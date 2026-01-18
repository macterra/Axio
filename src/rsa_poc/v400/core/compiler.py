"""
RSA-PoC v4.0 — JCOMP-4.0 Compiler
Implements §2.1-2.6 of v40_design_freeze.md

Fully deterministic, non-LLM compiler that maps justifications
to executable predicates. Includes Obligation Gate (§2.5.1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from .dsl import (
    ActionClass,
    Condition,
    ConditionOp,
    JustificationV400,
    ParseError,
    Rule,
    RuleType,
    ValidationError,
    validate_justification_json,
)
from .norm_state import NormStateV400


# ============================================================================
# §2.2 — Compilation Status
# ============================================================================


class CompilationStatus(str, Enum):
    """Compilation result status."""
    COMPILED = "COMPILED"
    PARSE_ERROR = "PARSE_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    REFERENCE_ERROR = "REFERENCE_ERROR"


# ============================================================================
# §2.4 — Executable Predicate
# ============================================================================


@dataclass
class ExecutablePredicate:
    """
    Compiled predicate per §2.4 of design freeze.

    Includes norm_hash check to prevent cross-law replay.
    """
    action_id: str
    rule_type: RuleType
    compiled_norm_hash: str
    condition_fn: Callable[[Any], bool]
    rule_id: str  # For debugging/tracing

    def evaluate(self, obs: Any, action: str, current_norm_hash: str) -> bool:
        """
        Evaluate predicate against observation.

        Rejects if:
        - NormState has changed since compilation
        - Action doesn't match
        - Condition evaluates to False
        """
        # Reject if NormState has changed (prevents cross-law replay)
        if current_norm_hash != self.compiled_norm_hash:
            return False
        if action != self.action_id:
            return False
        return self.condition_fn(obs)


# ============================================================================
# §2.3 — Compilation Result
# ============================================================================


@dataclass
class CompilationResult:
    """Result of compiling a single justification."""
    action_id: str
    status: CompilationStatus
    predicate: Optional[ExecutablePredicate] = None
    error_message: Optional[str] = None


@dataclass
class CompilationBatch:
    """Result of compiling multiple justifications."""
    results: List[CompilationResult]
    compiled_count: int = 0
    failed_count: int = 0

    def __post_init__(self):
        self.compiled_count = sum(
            1 for r in self.results if r.status == CompilationStatus.COMPILED
        )
        self.failed_count = len(self.results) - self.compiled_count


# ============================================================================
# §2.5 — Condition Compilation (Deterministic)
# ============================================================================


def compile_condition(cond: Condition) -> Callable[[Any], bool]:
    """
    Compile a Condition into a callable predicate.

    Per §2.5 of design freeze:
    - TRUE → lambda obs: True
    - FALSE → lambda obs: False
    - EQ(field, val) → lambda obs: obs[field] == val
    - GT(field, val) → lambda obs: obs[field] > val
    - LT(field, val) → lambda obs: obs[field] < val
    - IN_STATE(state_id) → lambda obs: obs.agent_pos == POSITIONS[state_id]
    - HAS_RESOURCE(n) → lambda obs: obs.inventory >= n
    - AND(a, b) → lambda obs: a(obs) and b(obs)
    - OR(a, b) → lambda obs: a(obs) or b(obs)
    - NOT(a) → lambda obs: not a(obs)
    """
    op = cond.op
    args = cond.args

    if op == ConditionOp.TRUE:
        return lambda obs: True

    elif op == ConditionOp.FALSE:
        return lambda obs: False

    elif op == ConditionOp.EQ:
        field_name = args[0]
        value = args[1]
        return lambda obs, f=field_name, v=value: _get_obs_field(obs, f) == v

    elif op == ConditionOp.GT:
        field_name = args[0]
        value = args[1]
        return lambda obs, f=field_name, v=value: _get_obs_field(obs, f) > v

    elif op == ConditionOp.LT:
        field_name = args[0]
        value = args[1]
        return lambda obs, f=field_name, v=value: _get_obs_field(obs, f) < v

    elif op == ConditionOp.IN_STATE:
        state_id = args[0]
        return lambda obs, s=state_id: _check_in_state(obs, s)

    elif op == ConditionOp.HAS_RESOURCE:
        n = args[0]
        return lambda obs, required=n: _get_obs_field(obs, "inventory") >= required

    elif op == ConditionOp.AND:
        # Recursively compile sub-conditions
        sub_fns = [compile_condition(a) if isinstance(a, Condition)
                   else compile_condition(Condition.from_dict(a)) for a in args]
        return lambda obs, fns=sub_fns: all(fn(obs) for fn in fns)

    elif op == ConditionOp.OR:
        sub_fns = [compile_condition(a) if isinstance(a, Condition)
                   else compile_condition(Condition.from_dict(a)) for a in args]
        return lambda obs, fns=sub_fns: any(fn(obs) for fn in fns)

    elif op == ConditionOp.NOT:
        sub_fn = compile_condition(args[0]) if isinstance(args[0], Condition) \
                 else compile_condition(Condition.from_dict(args[0]))
        return lambda obs, fn=sub_fn: not fn(obs)

    else:
        raise ValueError(f"Unknown condition operator: {op}")


def _get_obs_field(obs: Any, field: str) -> Any:
    """Get a field from observation (supports dict or dataclass)."""
    if isinstance(obs, dict):
        return obs.get(field)
    return getattr(obs, field, None)


def _check_in_state(obs: Any, state_id: str) -> bool:
    """Check if agent is in a named state/position."""
    # Import here to avoid circular dependency
    from ..env.tri_demand import POSITIONS

    target_pos = POSITIONS.get(state_id)
    if target_pos is None:
        return False

    agent_pos = _get_obs_field(obs, "agent_pos")
    return agent_pos == target_pos


# ============================================================================
# §2.3 — JCOMP-4.0 Compiler
# ============================================================================


class JCOMP400:
    """
    JCOMP-4.0: Deterministic justification compiler.

    Per §2.1-2.3 of design freeze:
    1. Parse: Validate JSON syntax
    2. Schema validate: Validate against JustificationV400 schema
    3. Reference resolve: Verify all rule_refs exist in norm_state
    4. Predicate emit: Generate executable predicate
    """

    def __init__(self, norm_state: NormStateV400):
        self.norm_state = norm_state

    def compile(self, justification_json: str) -> CompilationResult:
        """
        Compile a single justification from JSON string.

        Returns CompilationResult with status and optional predicate.
        """
        # Step 1: Parse JSON
        try:
            data = json.loads(justification_json)
        except json.JSONDecodeError as e:
            return CompilationResult(
                action_id="UNKNOWN",
                status=CompilationStatus.PARSE_ERROR,
                error_message=f"Invalid JSON: {e}"
            )

        # Step 2: Schema validate
        try:
            justification = JustificationV400.from_dict(data)
        except (KeyError, ValueError, TypeError) as e:
            action_id = data.get("action_id", "UNKNOWN")
            return CompilationResult(
                action_id=action_id,
                status=CompilationStatus.SCHEMA_ERROR,
                error_message=f"Schema validation failed: {e}"
            )

        return self.compile_justification(justification)

    def compile_justification(self, justification: JustificationV400) -> CompilationResult:
        """
        Compile a validated JustificationV400 object.
        """
        action_id = justification.action_id

        # Step 3: Reference resolve
        for rule_ref in justification.rule_refs:
            if not self.norm_state.has_rule(rule_ref):
                return CompilationResult(
                    action_id=action_id,
                    status=CompilationStatus.REFERENCE_ERROR,
                    error_message=f"Rule reference not found: {rule_ref}"
                )

        # Step 4: Predicate emit
        # Use the first referenced rule for the predicate
        primary_rule = self.norm_state.get_rule(justification.rule_refs[0])
        if primary_rule is None:
            return CompilationResult(
                action_id=action_id,
                status=CompilationStatus.REFERENCE_ERROR,
                error_message=f"Primary rule not found: {justification.rule_refs[0]}"
            )

        # Check for PERMISSION vs PROHIBITION conflict on same action
        rule_types = set()
        for rule_ref in justification.rule_refs:
            rule = self.norm_state.get_rule(rule_ref)
            if rule:
                rule_types.add(rule.type)

        if RuleType.PERMISSION in rule_types and RuleType.PROHIBITION in rule_types:
            return CompilationResult(
                action_id=action_id,
                status=CompilationStatus.REFERENCE_ERROR,
                error_message="PERMISSION vs PROHIBITION conflict on same action"
            )

        # Compile condition
        condition_fn = compile_condition(primary_rule.condition)

        predicate = ExecutablePredicate(
            action_id=action_id,
            rule_type=primary_rule.type,
            compiled_norm_hash=self.norm_state.norm_hash,
            condition_fn=condition_fn,
            rule_id=primary_rule.id
        )

        return CompilationResult(
            action_id=action_id,
            status=CompilationStatus.COMPILED,
            predicate=predicate
        )

    def compile_batch(self, justifications_json: List[str]) -> CompilationBatch:
        """
        Compile multiple justifications.
        """
        results = [self.compile(j) for j in justifications_json]
        return CompilationBatch(results=results)

    def compile_justifications(self, justifications: List[JustificationV400]) -> CompilationBatch:
        """
        Compile multiple validated justifications.
        """
        results = [self.compile_justification(j) for j in justifications]
        return CompilationBatch(results=results)


# ============================================================================
# §2.5.1 — Obligation Gate (Mask-Stage Rule)
# ============================================================================


@dataclass
class MaskResult:
    """Result of the Mask stage with Obligation Gate."""
    feasible: List[str]
    feasible_count: int
    error: Optional[str] = None
    binding_obligation: Optional[str] = None  # Rule ID if obligation binds


def compute_feasible(
    compiled_predicates: List[ExecutablePredicate],
    norm_state: NormStateV400,
    obs: Any,
    current_episode: int
) -> MaskResult:
    """
    Compute feasible actions with Obligation Gate per §2.5.1.

    FROZEN SEMANTICS (v4.0):
    1. Find active obligations (condition is true)
    2. Apply priority (highest wins)
    3. If obligation binds, check if obligated action is compiled/permitted
    4. If obligated action IS compiled/permitted → only that action is feasible
    5. If obligated action is NOT compiled/permitted → feasible=[] → HALT

    No "work towards obligation" logic. Strict binding.

    Returns MaskResult with feasible action IDs.
    """
    # Step 1: Find active obligations (condition is currently true)
    active_obligations: List[Tuple[Rule, bool]] = []

    for rule in norm_state.get_obligations(current_episode):
        condition_fn = compile_condition(rule.condition)
        if condition_fn(obs):
            active_obligations.append((rule, True))

    # Collect all permitted/prohibited from compiled predicates first
    permitted: set = set()
    prohibited: set = set()

    for pred in compiled_predicates:
        if pred.evaluate(obs, pred.action_id, norm_state.norm_hash):
            if pred.rule_type == RuleType.PERMISSION:
                permitted.add(pred.action_id)
            elif pred.rule_type == RuleType.PROHIBITION:
                prohibited.add(pred.action_id)

    # Step 2: Apply priority for obligations (highest wins)
    if active_obligations:
        max_priority = max(r.priority for r, _ in active_obligations)
        binding = [(r, active) for r, active in active_obligations if r.priority == max_priority]

        if len(binding) > 1:
            # Equal priority conflict
            return MaskResult(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: competing obligations with equal priority"
            )

        binding_rule = binding[0][0]
        obligated_action = _action_class_to_action_id(binding_rule.effect.action_class)

        # §2.5.1 FROZEN SEMANTICS:
        # Check if obligated action is compiled/permitted
        obligated_is_permitted = obligated_action in (permitted - prohibited)

        if obligated_is_permitted:
            # Obligation binds AND action is compiled/permitted → only that action
            return MaskResult(
                feasible=[obligated_action],
                feasible_count=1,
                binding_obligation=binding_rule.id
            )
        else:
            # Obligation binds but action NOT compiled/permitted → HALT
            # This is the frozen spec: no "work towards" escape hatch
            return MaskResult(
                feasible=[],
                feasible_count=0,
                binding_obligation=binding_rule.id,
                error=f"OBLIGATION_HALT: {obligated_action} not compiled/permitted"
            )

    # Step 3: No obligation binds — use PERMISSION/PROHIBITION logic
    feasible = list(permitted - prohibited)

    return MaskResult(
        feasible=feasible,
        feasible_count=len(feasible)
    )


def _action_class_to_action_id(action_class: ActionClass) -> str:
    """Map action class to action ID."""
    # This mapping must match the environment's action space
    mapping = {
        ActionClass.MOVE: "A0",  # Default to MOVE_N; specific moves handled separately
        ActionClass.COLLECT: "A4",
        ActionClass.DEPOSIT: "A5",
        ActionClass.WAIT: "A5",  # WAIT not in current env, map to DEPOSIT
        ActionClass.ANY: "A0",   # Default
    }
    return mapping.get(action_class, "A0")


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "CompilationStatus",
    "ExecutablePredicate",
    "CompilationResult",
    "CompilationBatch",
    "JCOMP400",
    "compile_condition",
    "MaskResult",
    "compute_feasible",
]
