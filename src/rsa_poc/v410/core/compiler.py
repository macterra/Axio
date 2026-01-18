"""
RSA-PoC v4.1 — JCOMP-4.1 Compiler
Implements §2.1-2.6 of v41_design_freeze.md

Fully deterministic, non-LLM compiler that maps justifications
to executable rule evaluators. Includes revised Obligation Gate (§2.5.1)
with progress_set-based feasibility.

v4.1 changes from v4.0:
- RuleEval instead of ExecutablePredicate
- Obligations bind to targets, not immediate actions
- Mask stage uses env.progress_set() for obligation feasibility
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple

from .dsl import (
    ActionClass,
    Condition,
    ConditionOp,
    EffectType,
    JustificationV410,
    ObligationTarget,
    ParseError,
    Rule,
    RuleType,
    ValidationError,
    validate_justification_json,
)
from .norm_state import NormStateV410


# ============================================================================
# §2.5.1 — ACTION_CLASS_TO_ACTION_IDS Mapping (Frozen)
# ============================================================================

ACTION_CLASS_TO_ACTION_IDS: Dict[str, Set[str]] = {
    "MOVE": {"A0", "A1", "A2", "A3"},
    "COLLECT": {"A4"},
    "DEPOSIT": {"A5"},
    "ANY": {"A0", "A1", "A2", "A3", "A4", "A5"},
    "WAIT": set(),  # Reserved, maps to empty set
}


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
# §2.4 — RuleEval (Executable Predicate Form)
# ============================================================================


@dataclass
class RuleEval:
    """
    Compiled rule evaluator per §2.4 of v4.1 design freeze.

    v4.1 compiles rules (not per-action predicates) because
    obligations bind to targets and Mask computes feasibility.

    Includes norm_hash check to prevent cross-law replay.
    """
    rule_id: str
    rule_type: str  # "PERMISSION", "PROHIBITION", "OBLIGATION"
    compiled_norm_hash: str
    condition_fn: Callable[[Any], bool]
    effect: Dict[str, Any]  # Canonical Effect object from NormState
    priority: int = 0

    def active(self, obs: Any, current_norm_hash: str) -> bool:
        """
        Check if rule is active for given observation.

        Rejects if:
        - NormState has changed since compilation
        - Condition evaluates to False
        """
        # Reject if NormState has changed (prevents cross-law replay)
        if current_norm_hash != self.compiled_norm_hash:
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
    rule_evals: Optional[List[RuleEval]] = None
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

    Per §2.5 of v4.1 design freeze:
    - TRUE → lambda obs: True
    - FALSE → lambda obs: False
    - EQ(field, val) → lambda obs: obs[field] == val
    - GT(field, val) → lambda obs: obs[field] > val
    - LT(field, val) → lambda obs: obs[field] < val
    - IN_STATE(state_id) → lambda obs: obs.agent_pos == POSITIONS[state_id]
    - HAS_RESOURCE(n) → lambda obs: obs.inventory >= n
    - AND(a, b, ...) → lambda obs: all conditions true
    - OR(a, b, ...) → lambda obs: any condition true
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
# §2.3 — JCOMP-4.1 Compiler
# ============================================================================


class JCOMP410:
    """
    JCOMP-4.1: Deterministic justification compiler.

    Per §2.1-2.3 of v4.1 design freeze:
    1. Parse: Validate JSON syntax
    2. Schema validate: Validate against JustificationV410 schema
    3. Reference resolve: Verify all rule_refs exist in norm_state
    4. Rule-eval emit: Generate RuleEval objects for referenced rules
    """

    def __init__(self, norm_state: NormStateV410):
        self.norm_state = norm_state

    def compile(self, justification_json: str) -> CompilationResult:
        """
        Compile a single justification from JSON string.

        Returns CompilationResult with status and optional rule_evals.
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
            justification = JustificationV410.from_dict(data)
        except (KeyError, ValueError, TypeError) as e:
            action_id = data.get("action_id", "UNKNOWN")
            return CompilationResult(
                action_id=action_id,
                status=CompilationStatus.SCHEMA_ERROR,
                error_message=f"Schema validation failed: {e}"
            )

        return self.compile_justification(justification)

    def compile_justification(self, justification: JustificationV410) -> CompilationResult:
        """
        Compile a validated JustificationV410 object.
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

        # Step 4: Emit RuleEval for each referenced rule
        rule_evals = []
        for rule_ref in justification.rule_refs:
            rule = self.norm_state.get_rule(rule_ref)
            if rule is None:
                return CompilationResult(
                    action_id=action_id,
                    status=CompilationStatus.REFERENCE_ERROR,
                    error_message=f"Rule not found: {rule_ref}"
                )

            # Compile condition
            condition_fn = compile_condition(rule.condition)

            rule_eval = RuleEval(
                rule_id=rule.id,
                rule_type=rule.type.value,
                compiled_norm_hash=self.norm_state.norm_hash,
                condition_fn=condition_fn,
                effect=rule.effect.to_dict(),
                priority=rule.priority
            )
            rule_evals.append(rule_eval)

        return CompilationResult(
            action_id=action_id,
            status=CompilationStatus.COMPILED,
            rule_evals=rule_evals
        )

    def compile_batch(self, justifications_json: List[str]) -> CompilationBatch:
        """
        Compile multiple justifications from JSON strings.
        """
        results = [self.compile(j) for j in justifications_json]
        return CompilationBatch(results=results)

    def compile_justifications(self, justifications: List[JustificationV410]) -> CompilationBatch:
        """
        Compile multiple validated justifications.
        """
        results = [self.compile_justification(j) for j in justifications]
        return CompilationBatch(results=results)


# ============================================================================
# §2.5.1 — Mask Stage (Obligation Gate)
# ============================================================================


@dataclass
class MaskResult:
    """Result of the Mask stage with Obligation Gate."""
    feasible: List[str]
    feasible_count: int
    error: Optional[str] = None
    binding_obligation: Optional[str] = None  # Rule ID if obligation binds


class EnvironmentInterface:
    """
    Abstract interface for environment obligation methods.

    The actual TriDemandV410 environment implements these.
    """
    def target_satisfied(self, obs: Any, obligation_target: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def rank(self, obs: Any, obligation_target: Dict[str, Any]) -> int:
        raise NotImplementedError

    def progress_set(self, obs: Any, obligation_target: Dict[str, Any]) -> Set[str]:
        raise NotImplementedError


def compute_feasible(
    compiled_rules: List[RuleEval],
    norm_state: NormStateV410,
    obs: Any,
    env: EnvironmentInterface,
    current_norm_hash: str
) -> MaskResult:
    """
    Compute feasible actions with Obligation Gate per §2.5.1.

    FROZEN SEMANTICS (v4.1):
    1. Find active rules (permission, prohibition, obligation)
    2. Build permitted/prohibited sets from ACTION_CLASS effects
    3. If obligation binds:
       - Check if target satisfied (if so, obligation doesn't gate)
       - Get progress_set from environment
       - feasible = progress_set ∩ compiled_permitted_actions
       - If empty → HALT
    4. If no obligation binds: feasible = permitted - prohibited

    Returns MaskResult with feasible action IDs.
    """
    # Step 1: Determine active rules (hash-guarded)
    active_perms: List[RuleEval] = []
    active_prohibs: List[RuleEval] = []
    active_obligs: List[RuleEval] = []

    for r in compiled_rules:
        if not r.active(obs, current_norm_hash):
            continue
        if r.rule_type == "PERMISSION":
            active_perms.append(r)
        elif r.rule_type == "PROHIBITION":
            active_prohibs.append(r)
        elif r.rule_type == "OBLIGATION":
            active_obligs.append(r)

    # Step 2: Build permitted/prohibited sets from ACTION_CLASS effects
    permitted: Set[str] = set()
    prohibited: Set[str] = set()

    for r in active_perms:
        if r.effect.get("effect_type") == "ACTION_CLASS":
            action_class = r.effect.get("action_class", "")
            permitted |= ACTION_CLASS_TO_ACTION_IDS.get(action_class, set())

    for r in active_prohibs:
        if r.effect.get("effect_type") == "ACTION_CLASS":
            action_class = r.effect.get("action_class", "")
            prohibited |= ACTION_CLASS_TO_ACTION_IDS.get(action_class, set())

    compiled_permitted_actions = permitted - prohibited

    # Step 3: Apply obligation target gate
    if active_obligs:
        # Identify highest-priority active OBLIGATION
        active_ids = {r.rule_id for r in active_obligs}

        # Get priorities from norm_state
        priorities = {}
        for rule in norm_state.rules:
            if rule.id in active_ids:
                priorities[rule.id] = rule.priority

        if not priorities:
            return MaskResult(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: no matching obligations in norm_state"
            )

        max_priority = max(priorities.values())
        binding = [r for r in active_obligs if priorities.get(r.rule_id) == max_priority]

        # Check for distinct rule_ids at max priority (not duplicate RuleEvals)
        binding_rule_ids = {r.rule_id for r in binding}
        if len(binding_rule_ids) > 1:
            # Multiple distinct obligations with same priority
            return MaskResult(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: competing obligations with equal priority"
            )

        binding_rule = binding[0]
        eff = binding_rule.effect

        if eff.get("effect_type") != "OBLIGATION_TARGET":
            return MaskResult(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: obligation effect is not OBLIGATION_TARGET"
            )

        tgt = eff.get("obligation_target")
        if tgt is None:
            return MaskResult(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: obligation_target is None"
            )

        # If already satisfied, obligation doesn't gate feasibility
        if env.target_satisfied(obs, tgt):
            return MaskResult(
                feasible=list(compiled_permitted_actions),
                feasible_count=len(compiled_permitted_actions)
            )

        # Progress set computed by environment
        ps = env.progress_set(obs, tgt)

        # Empty progress_set => impossible obligation => HALT
        if not ps:
            return MaskResult(
                feasible=[],
                feasible_count=0,
                binding_obligation=binding_rule.rule_id
            )

        feasible = list(ps & compiled_permitted_actions)

        # Empty intersection => law/physics contradiction => HALT
        if not feasible:
            return MaskResult(
                feasible=[],
                feasible_count=0,
                binding_obligation=binding_rule.rule_id
            )

        return MaskResult(
            feasible=feasible,
            feasible_count=len(feasible),
            binding_obligation=binding_rule.rule_id
        )

    # Step 4: No obligation binds — use PERMISSION minus PROHIBITION
    return MaskResult(
        feasible=list(compiled_permitted_actions),
        feasible_count=len(compiled_permitted_actions)
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "CompilationStatus",
    "RuleEval",
    "CompilationResult",
    "CompilationBatch",
    "JCOMP410",
    "compile_condition",
    "MaskResult",
    "EnvironmentInterface",
    "compute_feasible",
    "ACTION_CLASS_TO_ACTION_IDS",
]

