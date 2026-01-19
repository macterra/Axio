"""
RSA-PoC v4.2 — LAW_REPAIR Action Schema and Gate

Implements:
- LawRepairAction: Typed schema for law repair
- LawRepairGate: Validates repairs per R1-R8
- RepairValidationResult: Result of repair validation
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

from .dsl import (
    Condition,
    ConditionOp,
    PatchOp,
    PatchOperation,
    Rule,
    canonical_json,
    patch_fingerprint,
)
from .trace import TraceEntry, TraceLog, TraceEntryType

if TYPE_CHECKING:
    from .norm_state import NormStateV420


# ============================================================================
# LAW_REPAIR Action Schema
# ============================================================================


@dataclass
class LawRepairAction:
    """
    LAW_REPAIR action schema per v4.2 spec.

    Required fields:
    - trace_entry_id: TraceEntryID of the contradiction being addressed
    - rule_ids: Compiled rule_id(s) responsible for contradiction
    - prior_repair_epoch: Exact prior epoch value (for R6)
    - patch_ops: List of typed patch operations
    - patch_fingerprint: Canonical encoding of patches (auto-computed)
    """
    trace_entry_id: str
    rule_ids: List[str]
    prior_repair_epoch: Optional[str]  # None for first repair under regime=1
    patch_ops: List[PatchOperation]
    repair_fingerprint: Optional[str] = None  # Auto-computed if not provided

    def __post_init__(self):
        # Convert dict patch ops to PatchOperation objects
        self.patch_ops = [
            PatchOperation.from_dict(p) if isinstance(p, dict) else p
            for p in self.patch_ops
        ]
        # Auto-compute fingerprint if not provided
        if self.repair_fingerprint is None:
            self.repair_fingerprint = patch_fingerprint(self.patch_ops)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": "LAW_REPAIR",
            "trace_entry_id": self.trace_entry_id,
            "rule_ids": self.rule_ids,
            "prior_repair_epoch": self.prior_repair_epoch,
            "patch_ops": [p.to_dict() for p in self.patch_ops],
            "repair_fingerprint": self.repair_fingerprint,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LawRepairAction":
        return cls(
            trace_entry_id=d["trace_entry_id"],
            rule_ids=d["rule_ids"],
            prior_repair_epoch=d.get("prior_repair_epoch"),
            patch_ops=[PatchOperation.from_dict(p) for p in d["patch_ops"]],
            repair_fingerprint=d.get("repair_fingerprint"),
        )


# ============================================================================
# Repair Validation Result
# ============================================================================


class RepairFailureReason(str, Enum):
    """Reasons a repair can fail validation."""
    # R1 failures
    R1_NO_RULE_MODIFIED = "R1_NO_RULE_MODIFIED"
    R1_RULE_NOT_RESPONSIBLE = "R1_RULE_NOT_RESPONSIBLE"
    # R2 failures
    R2_STILL_NO_PROGRESS = "R2_STILL_NO_PROGRESS"
    R2_COMPILATION_FAILED = "R2_COMPILATION_FAILED"
    # R3 failures
    R3_COMPILATION_FAILED = "R3_COMPILATION_FAILED"
    # R4 failures
    R4_NEW_DEFAULT_DETECTED = "R4_NEW_DEFAULT_DETECTED"
    R4_FALLBACK_DETECTED = "R4_FALLBACK_DETECTED"
    # R5/R6 failures
    R5_EPOCH_MISMATCH = "R5_EPOCH_MISMATCH"
    R6_MISSING_PRIOR_EPOCH = "R6_MISSING_PRIOR_EPOCH"
    R6_WRONG_PRIOR_EPOCH = "R6_WRONG_PRIOR_EPOCH"
    # R7 failures
    R7_TRACE_ENTRY_NOT_FOUND = "R7_TRACE_ENTRY_NOT_FOUND"
    R7_RULE_NOT_IN_TRACE = "R7_RULE_NOT_IN_TRACE"
    R7_NO_CITED_RULE_MODIFIED = "R7_NO_CITED_RULE_MODIFIED"
    # R8 failures
    R8_COMPILER_DRIFT = "R8_COMPILER_DRIFT"
    # R9 failures (optional)
    R9_RETRY_EXHAUSTED = "R9_RETRY_EXHAUSTED"


@dataclass
class RepairValidationResult:
    """Result of validating a LAW_REPAIR action."""
    valid: bool
    failure_reason: Optional[RepairFailureReason] = None
    failure_detail: Optional[str] = None
    new_law_fingerprint: Optional[str] = None
    new_repair_epoch: Optional[str] = None

    @staticmethod
    def success(
        new_law_fingerprint: str,
        new_repair_epoch: str
    ) -> "RepairValidationResult":
        return RepairValidationResult(
            valid=True,
            new_law_fingerprint=new_law_fingerprint,
            new_repair_epoch=new_repair_epoch,
        )

    @staticmethod
    def failure(
        reason: RepairFailureReason,
        detail: Optional[str] = None
    ) -> "RepairValidationResult":
        return RepairValidationResult(
            valid=False,
            failure_reason=reason,
            failure_detail=detail,
        )


# ============================================================================
# Law-Repair Gate
# ============================================================================


class LawRepairGate:
    """
    Law-Repair Gate implementing R1-R8 validation.

    The gate validates LAW_REPAIR actions and, if valid, applies
    the repair and computes the new repair_epoch.
    """

    def __init__(
        self,
        trace_log: TraceLog,
        compiler_hash: str,
        env_progress_set_fn: Callable[[Any, Dict[str, str]], Set[str]],
        env_target_satisfied_fn: Callable[[Any, Dict[str, str]], bool],
        current_repair_epoch: Optional[str] = None,
        regime: int = 0,
        max_retries: int = 2,  # R9 default
    ):
        """
        Initialize the Law-Repair Gate.

        Args:
            trace_log: TraceLog for R7 validation
            compiler_hash: Expected compiler hash for R8
            env_progress_set_fn: Environment's progress_set function
            env_target_satisfied_fn: Environment's target_satisfied function
            current_repair_epoch: Current repair epoch (None if no prior repair)
            regime: Current regime (0 or 1)
            max_retries: Max repair attempts per contradiction (R9)
        """
        self.trace_log = trace_log
        self.expected_compiler_hash = compiler_hash
        self.env_progress_set = env_progress_set_fn
        self.env_target_satisfied = env_target_satisfied_fn
        self.current_repair_epoch = current_repair_epoch
        self.regime = regime
        self.max_retries = max_retries
        self._retry_count: Dict[str, int] = {}  # trace_entry_id -> attempts

    def validate(
        self,
        repair_action: LawRepairAction,
        norm_state: "NormStateV420",
        obs: Any,
        active_obligation_target: Dict[str, str],
        compiled_permitted_actions: Set[str],
        compile_fn: Callable[["NormStateV420"], Any],
        compiler_hash: str,
    ) -> RepairValidationResult:
        """
        Validate a LAW_REPAIR action per R1-R8.

        Args:
            repair_action: The repair action to validate
            norm_state: Current normative state
            obs: Current observation
            active_obligation_target: The obligation that triggered contradiction
            compiled_permitted_actions: Current permitted actions from compilation
            compile_fn: Function to compile a norm state (for shadow compile)
            compiler_hash: Hash of the compiler being used

        Returns:
            RepairValidationResult indicating success or failure
        """
        # R8: Shadow Compiler Lock
        if compiler_hash != self.expected_compiler_hash:
            return RepairValidationResult.failure(
                RepairFailureReason.R8_COMPILER_DRIFT,
                f"Compiler hash mismatch: {compiler_hash} != {self.expected_compiler_hash}"
            )

        # R9: Check retry count
        trace_id = repair_action.trace_entry_id
        if trace_id in self._retry_count:
            if self._retry_count[trace_id] >= self.max_retries:
                return RepairValidationResult.failure(
                    RepairFailureReason.R9_RETRY_EXHAUSTED,
                    f"Max retries ({self.max_retries}) exhausted for {trace_id}"
                )

        # R7: Trace-Cited Causality
        trace_entry = self.trace_log.get(trace_id)
        if trace_entry is None:
            return RepairValidationResult.failure(
                RepairFailureReason.R7_TRACE_ENTRY_NOT_FOUND,
                f"TraceEntryID not found: {trace_id}"
            )

        if trace_entry.entry_type != TraceEntryType.CONTRADICTION:
            return RepairValidationResult.failure(
                RepairFailureReason.R7_TRACE_ENTRY_NOT_FOUND,
                f"TraceEntry is not a CONTRADICTION: {trace_entry.entry_type}"
            )

        # R7: Verify cited rule_ids exist in trace entry
        trace_blocking_rules = set(trace_entry.blocking_rule_ids or [])
        for rule_id in repair_action.rule_ids:
            if rule_id not in trace_blocking_rules:
                return RepairValidationResult.failure(
                    RepairFailureReason.R7_RULE_NOT_IN_TRACE,
                    f"Rule {rule_id} not in trace blocking_rule_ids: {trace_blocking_rules}"
                )

        # R6: Anti-Amnesia Rule (under regime=1)
        if self.regime == 1 and self.current_repair_epoch is not None:
            if repair_action.prior_repair_epoch is None:
                return RepairValidationResult.failure(
                    RepairFailureReason.R6_MISSING_PRIOR_EPOCH,
                    "prior_repair_epoch required under regime=1 with existing epoch"
                )
            if repair_action.prior_repair_epoch != self.current_repair_epoch:
                return RepairValidationResult.failure(
                    RepairFailureReason.R6_WRONG_PRIOR_EPOCH,
                    f"prior_repair_epoch mismatch: {repair_action.prior_repair_epoch} != {self.current_repair_epoch}"
                )

        # R1: Structural Relevance
        modified_rule_ids = {p.target_rule_id for p in repair_action.patch_ops}
        if not modified_rule_ids:
            return RepairValidationResult.failure(
                RepairFailureReason.R1_NO_RULE_MODIFIED,
                "No rules modified by patch operations"
            )

        # R7: Verify at least one cited rule is modified
        cited_rules_modified = modified_rule_ids & set(repair_action.rule_ids)
        if not cited_rules_modified:
            return RepairValidationResult.failure(
                RepairFailureReason.R7_NO_CITED_RULE_MODIFIED,
                f"No cited rules modified. Modified: {modified_rule_ids}, Cited: {repair_action.rule_ids}"
            )

        # R1: Verify modified rules are in blocking set
        for rule_id in modified_rule_ids:
            if rule_id not in trace_blocking_rules:
                return RepairValidationResult.failure(
                    RepairFailureReason.R1_RULE_NOT_RESPONSIBLE,
                    f"Modified rule {rule_id} not in blocking set: {trace_blocking_rules}"
                )

        # Apply patches to get new norm state
        try:
            patched_norm_state = self._apply_patches(
                norm_state, repair_action.patch_ops
            )
        except Exception as e:
            return RepairValidationResult.failure(
                RepairFailureReason.R3_COMPILATION_FAILED,
                f"Failed to apply patches: {e}"
            )

        # R3: Deterministic Compilation
        try:
            compilation_result = compile_fn(patched_norm_state)
            if not compilation_result:
                return RepairValidationResult.failure(
                    RepairFailureReason.R3_COMPILATION_FAILED,
                    "Repaired law failed to compile"
                )
        except Exception as e:
            return RepairValidationResult.failure(
                RepairFailureReason.R3_COMPILATION_FAILED,
                f"Compilation error: {e}"
            )

        # R2: Non-Cosmetic Effect
        # After applying repair, progress_set ∩ compiled_permitted_actions ≠ ∅
        try:
            new_permitted = self._get_permitted_actions(patched_norm_state, obs)
            progress = self.env_progress_set(obs, active_obligation_target)

            intersection = progress & new_permitted
            if not intersection:
                return RepairValidationResult.failure(
                    RepairFailureReason.R2_STILL_NO_PROGRESS,
                    f"Repair cosmetic: progress={progress}, new_permitted={new_permitted}, intersection empty"
                )
        except Exception as e:
            return RepairValidationResult.failure(
                RepairFailureReason.R2_COMPILATION_FAILED,
                f"Failed to verify R2: {e}"
            )

        # R4: No New Defaults
        # Check that no patch introduces unconditional permissions or suppression
        for patch in repair_action.patch_ops:
            if self._introduces_default(patch):
                return RepairValidationResult.failure(
                    RepairFailureReason.R4_NEW_DEFAULT_DETECTED,
                    f"Patch introduces default/fallback: {patch.to_dict()}"
                )

        # All validations passed - compute new epoch
        new_law_fingerprint = patched_norm_state.law_fingerprint
        new_epoch = self._compute_new_epoch(
            previous_law_fingerprint=norm_state.law_fingerprint,
            repair_fingerprint=repair_action.repair_fingerprint,
        )

        # Increment retry count
        self._retry_count[trace_id] = self._retry_count.get(trace_id, 0) + 1

        return RepairValidationResult.success(
            new_law_fingerprint=new_law_fingerprint,
            new_repair_epoch=new_epoch,
        )

    def _apply_patches(
        self,
        norm_state: "NormStateV420",
        patches: List[PatchOperation]
    ) -> "NormStateV420":
        """Apply patches to norm state and return new state."""
        # Import here to avoid circular dependency
        from .norm_state import NormStateV420

        new_rules = list(norm_state.rules)

        for patch in patches:
            # Find the target rule
            target_idx = None
            for i, rule in enumerate(new_rules):
                if rule.id == patch.target_rule_id:
                    target_idx = i
                    break

            if target_idx is None:
                raise ValueError(f"Target rule not found: {patch.target_rule_id}")

            # Apply patch
            new_rule = patch.apply(new_rules[target_idx])
            new_rules[target_idx] = new_rule

        return NormStateV420(rules=new_rules)

    def _get_permitted_actions(
        self,
        norm_state: "NormStateV420",
        obs: Any
    ) -> Set[str]:
        """Get permitted actions from norm state (simplified check)."""
        # This is a simplified check - actual implementation would use full compiler
        from .dsl import ActionClass

        ACTION_CLASS_TO_IDS = {
            "MOVE": {"A0", "A1", "A2", "A3"},
            "COLLECT": {"A4"},
            "DEPOSIT": {"A5"},
            "STAMP": {"A6"},
            "ANY": {"A0", "A1", "A2", "A3", "A4", "A5", "A6"},
        }

        permitted: Set[str] = set()
        prohibited: Set[str] = set()

        for rule in norm_state.rules:
            # Check if rule is active (simplified - assumes TRUE condition for now)
            # Full implementation would evaluate conditions
            if rule.type.value == "PERMISSION":
                if rule.effect.action_class:
                    permitted |= ACTION_CLASS_TO_IDS.get(rule.effect.action_class.value, set())
            elif rule.type.value == "PROHIBITION":
                if rule.effect.action_class:
                    prohibited |= ACTION_CLASS_TO_IDS.get(rule.effect.action_class.value, set())

        return permitted - prohibited

    def _introduces_default(self, patch: PatchOperation) -> bool:
        """Check if a patch introduces unconditional permission or fallback."""
        if patch.op == PatchOp.MODIFY_CONDITION:
            # Check if new condition is TRUE (unconditional)
            if patch.new_condition and patch.new_condition.op == ConditionOp.TRUE:
                return True
        elif patch.op == PatchOp.ADD_EXCEPTION:
            # Check if exception is FALSE (never applies = rule always active)
            # This would effectively be a no-op, not a default
            pass
        return False

    def _compute_new_epoch(
        self,
        previous_law_fingerprint: str,
        repair_fingerprint: str,
    ) -> str:
        """Compute new repair_epoch."""
        # In production, this would use environment nonce
        # For now, use hash of fingerprints
        h = hashlib.sha256()
        h.update(previous_law_fingerprint.encode('utf-8'))
        h.update(repair_fingerprint.encode('utf-8'))
        # Note: environment_nonce should be injected here
        return h.hexdigest()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "LawRepairAction",
    "RepairFailureReason",
    "RepairValidationResult",
    "LawRepairGate",
]
