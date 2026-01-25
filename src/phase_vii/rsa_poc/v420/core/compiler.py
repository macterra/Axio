"""
RSA-PoC v4.2 — JCOMP-4.2 Compiler

v4.2 additions:
- repair_epoch embedding in compiled output
- Compiler hash for R8 shadow compiler lock
- Support for v4.2 conditions (REGIME_EQ, STAMPED)
"""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .dsl import (
    ActionClass,
    Condition,
    ConditionOp,
    EffectType,
    JustificationV420,
    Rule,
    RuleType,
)
from .norm_state import NormStateV420


# ============================================================================
# Compiler Hash (R8)
# ============================================================================


def compute_compiler_hash() -> str:
    """
    Compute hash of this compiler module for R8 validation.

    Returns SHA-256 of the module source code.
    """
    source = inspect.getsource(inspect.getmodule(compute_compiler_hash))
    return hashlib.sha256(source.encode('utf-8')).hexdigest()


# Module-level compiler hash (computed at import time)
JCOMP420_HASH = compute_compiler_hash()


# ============================================================================
# Action Class Mapping
# ============================================================================

ACTION_CLASS_TO_ACTION_IDS: Dict[str, Set[str]] = {
    "MOVE": {"A0", "A1", "A2", "A3"},
    "COLLECT": {"A4"},
    "DEPOSIT": {"A5"},
    "STAMP": {"A6"},  # v4.2 addition
    "ANY": {"A0", "A1", "A2", "A3", "A4", "A5", "A6"},
    "WAIT": set(),
}


# ============================================================================
# Compilation Status
# ============================================================================


class CompilationStatus(str, Enum):
    """Compilation result status."""
    COMPILED = "COMPILED"
    PARSE_ERROR = "PARSE_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    REFERENCE_ERROR = "REFERENCE_ERROR"


# ============================================================================
# RuleEval (Executable Predicate Form)
# ============================================================================


@dataclass
class RuleEval:
    """
    Compiled rule evaluator for v4.2.

    Includes repair_epoch for continuity tracking.
    """
    rule_id: str
    rule_type: str  # "PERMISSION", "PROHIBITION", "OBLIGATION"
    compiled_norm_hash: str
    condition_fn: Callable[[Any], bool]
    effect: Dict[str, Any]
    priority: int = 0
    repair_epoch: Optional[str] = None  # v4.2: Set if rule was repaired

    def active(self, obs: Any, current_norm_hash: str) -> bool:
        """Check if rule is active for given observation."""
        if current_norm_hash != self.compiled_norm_hash:
            return False
        return self.condition_fn(obs)


# ============================================================================
# Compilation Result
# ============================================================================


@dataclass
class CompilationResult420:
    """Result of compiling a single justification."""
    action_id: str
    status: CompilationStatus
    rule_evals: Optional[List[RuleEval]] = None
    error_message: Optional[str] = None
    compiler_hash: str = JCOMP420_HASH


@dataclass
class CompilationBatch420:
    """Result of compiling multiple justifications."""
    results: List[CompilationResult420]
    compiled_count: int = 0
    failed_count: int = 0
    compiler_hash: str = JCOMP420_HASH

    def __post_init__(self):
        self.compiled_count = sum(
            1 for r in self.results if r.status == CompilationStatus.COMPILED
        )
        self.failed_count = len(self.results) - self.compiled_count


# ============================================================================
# Condition Compilation
# ============================================================================


def compile_condition(cond: Condition) -> Callable[[Any], bool]:
    """
    Compile a Condition into a callable predicate.

    v4.2 additions:
    - REGIME_EQ: Check regime == value
    - STAMPED: Check stamped == True
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

    # v4.2 conditions
    elif op == ConditionOp.REGIME_EQ:
        value = args[0]
        return lambda obs, v=value: _get_obs_field(obs, "regime") == v

    elif op == ConditionOp.STAMPED:
        return lambda obs: _get_obs_field(obs, "stamped") == True

    else:
        raise ValueError(f"Unknown condition operator: {op}")


def _get_obs_field(obs: Any, field: str) -> Any:
    """Get a field from observation (supports dict or dataclass)."""
    if isinstance(obs, dict):
        return obs.get(field)
    return getattr(obs, field, None)


def _check_in_state(obs: Any, state_id: str) -> bool:
    """Check if agent is in a named state/position."""
    from ..env.tri_demand import POSITIONS

    target_pos = POSITIONS.get(state_id)
    if target_pos is None:
        return False

    agent_pos = _get_obs_field(obs, "agent_pos")
    return agent_pos == target_pos


# ============================================================================
# JCOMP-4.2 Compiler
# ============================================================================


class JCOMP420:
    """
    JCOMP-4.2: Deterministic justification compiler.

    v4.2 additions:
    - repair_epoch in RuleEval
    - Compiler hash for R8
    """

    def __init__(self, norm_state: NormStateV420):
        self.norm_state = norm_state
        self.compiler_hash = JCOMP420_HASH

    def compile(self, justification_json: str) -> CompilationResult420:
        """Compile a single justification from JSON string."""
        try:
            data = json.loads(justification_json)
        except json.JSONDecodeError as e:
            return CompilationResult420(
                action_id="UNKNOWN",
                status=CompilationStatus.PARSE_ERROR,
                error_message=f"Invalid JSON: {e}"
            )

        try:
            justification = JustificationV420.from_dict(data)
        except (KeyError, ValueError, TypeError) as e:
            action_id = data.get("action_id", "UNKNOWN")
            return CompilationResult420(
                action_id=action_id,
                status=CompilationStatus.SCHEMA_ERROR,
                error_message=f"Schema validation failed: {e}"
            )

        return self.compile_justification(justification)

    def compile_justification(self, justification: JustificationV420) -> CompilationResult420:
        """Compile a validated JustificationV420 object."""
        action_id = justification.action_id

        # Reference resolve
        for rule_ref in justification.rule_refs:
            if not self.norm_state.has_rule(rule_ref):
                return CompilationResult420(
                    action_id=action_id,
                    status=CompilationStatus.REFERENCE_ERROR,
                    error_message=f"Rule reference not found: {rule_ref}"
                )

        # Emit RuleEval for each referenced rule
        rule_evals = []
        for rule_ref in justification.rule_refs:
            rule = self.norm_state.get_rule(rule_ref)
            if rule is None:
                return CompilationResult420(
                    action_id=action_id,
                    status=CompilationStatus.REFERENCE_ERROR,
                    error_message=f"Rule not found: {rule_ref}"
                )

            condition_fn = compile_condition(rule.condition)

            rule_eval = RuleEval(
                rule_id=rule.id,
                rule_type=rule.type.value,
                compiled_norm_hash=self.norm_state.norm_hash,
                condition_fn=condition_fn,
                effect=rule.effect.to_dict(),
                priority=rule.priority,
                repair_epoch=rule.repair_epoch,
            )
            rule_evals.append(rule_eval)

        return CompilationResult420(
            action_id=action_id,
            status=CompilationStatus.COMPILED,
            rule_evals=rule_evals
        )

    def compile_batch(self, justifications_json: List[str]) -> CompilationBatch420:
        """Compile multiple justifications from JSON strings."""
        results = [self.compile(j) for j in justifications_json]
        return CompilationBatch420(results=results)

    def compile_justifications(self, justifications: List[JustificationV420]) -> CompilationBatch420:
        """Compile multiple validated justifications."""
        results = [self.compile_justification(j) for j in justifications]
        return CompilationBatch420(results=results)

    def compile_all_rules(self) -> List[RuleEval]:
        """
        Compile all rules in norm_state to RuleEval objects.

        Used for full law compilation (not tied to specific justifications).
        """
        rule_evals = []
        for rule in self.norm_state.rules:
            condition_fn = compile_condition(rule.condition)
            rule_eval = RuleEval(
                rule_id=rule.id,
                rule_type=rule.type.value,
                compiled_norm_hash=self.norm_state.norm_hash,
                condition_fn=condition_fn,
                effect=rule.effect.to_dict(),
                priority=rule.priority,
                repair_epoch=rule.repair_epoch,
            )
            rule_evals.append(rule_eval)
        return rule_evals


# ============================================================================
# Mask Stage (Obligation Gate)
# ============================================================================


@dataclass
class MaskResult420:
    """Result of the Mask stage with Obligation Gate."""
    feasible: List[str]
    feasible_count: int
    binding_obligation: Optional[str] = None
    binding_obligation_target: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    is_contradiction: bool = False
    blocking_rule_ids: Optional[List[str]] = None
    progress_actions: Optional[Set[str]] = None
    compiled_permitted_actions: Optional[Set[str]] = None


class EnvironmentInterface420:
    """Abstract interface for environment obligation methods."""
    def target_satisfied(self, obs: Any, obligation_target: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def rank(self, obs: Any, obligation_target: Dict[str, Any]) -> int:
        raise NotImplementedError

    def progress_set(self, obs: Any, obligation_target: Dict[str, Any]) -> Set[str]:
        raise NotImplementedError


def compute_feasible_420(
    compiled_rules: List[RuleEval],
    norm_state: NormStateV420,
    obs: Any,
    env: EnvironmentInterface420,
    current_norm_hash: str
) -> MaskResult420:
    """
    Compute feasible actions with Obligation Gate per v4.2.

    v4.2: Detects contradictions and returns diagnostic info.
    """
    # Step 1: Determine active rules
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

    # Step 2: Build permitted/prohibited sets
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
        active_ids = {r.rule_id for r in active_obligs}
        priorities = {}
        for rule in norm_state.rules:
            if rule.id in active_ids:
                priorities[rule.id] = rule.priority

        if not priorities:
            return MaskResult420(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: no matching obligations in norm_state"
            )

        max_priority = max(priorities.values())
        binding = [r for r in active_obligs if priorities.get(r.rule_id) == max_priority]

        binding_rule_ids = {r.rule_id for r in binding}
        if len(binding_rule_ids) > 1:
            return MaskResult420(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: competing obligations with equal priority"
            )

        binding_rule = binding[0]
        eff = binding_rule.effect

        if eff.get("effect_type") != "OBLIGATION_TARGET":
            return MaskResult420(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: obligation effect is not OBLIGATION_TARGET"
            )

        tgt = eff.get("obligation_target")
        if tgt is None:
            return MaskResult420(
                feasible=[],
                feasible_count=0,
                error="REFERENCE_ERROR: obligation_target is None"
            )

        # If satisfied, obligation doesn't gate
        if env.target_satisfied(obs, tgt):
            return MaskResult420(
                feasible=list(compiled_permitted_actions),
                feasible_count=len(compiled_permitted_actions)
            )

        # Progress set from environment
        ps = env.progress_set(obs, tgt)

        if not ps:
            return MaskResult420(
                feasible=[],
                feasible_count=0,
                binding_obligation=binding_rule.rule_id,
                binding_obligation_target=tgt,
            )

        feasible = list(ps & compiled_permitted_actions)

        # v4.2: Detect contradiction
        if not feasible:
            # Find which prohibitions are blocking
            blocking_rule_ids = []
            for r in active_prohibs:
                if r.effect.get("effect_type") == "ACTION_CLASS":
                    action_class = r.effect.get("action_class", "")
                    prohibited_actions = ACTION_CLASS_TO_ACTION_IDS.get(action_class, set())
                    if ps & prohibited_actions:
                        blocking_rule_ids.append(r.rule_id)

            return MaskResult420(
                feasible=[],
                feasible_count=0,
                binding_obligation=binding_rule.rule_id,
                binding_obligation_target=tgt,
                is_contradiction=True,
                blocking_rule_ids=blocking_rule_ids,
                progress_actions=ps,
                compiled_permitted_actions=compiled_permitted_actions,
            )

        return MaskResult420(
            feasible=feasible,
            feasible_count=len(feasible),
            binding_obligation=binding_rule.rule_id,
            binding_obligation_target=tgt,
        )

    # Step 4: No obligation binds
    return MaskResult420(
        feasible=list(compiled_permitted_actions),
        feasible_count=len(compiled_permitted_actions)
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "JCOMP420",
    "JCOMP420_HASH",
    "compute_compiler_hash",
    "CompilationStatus",
    "RuleEval",
    "CompilationResult420",
    "CompilationBatch420",
    "compile_condition",
    "MaskResult420",
    "EnvironmentInterface420",
    "compute_feasible_420",
    "ACTION_CLASS_TO_ACTION_IDS",
]
