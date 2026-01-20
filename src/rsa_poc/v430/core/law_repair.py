"""
v4.3 Law-Repair Gate with R9/R10 extensions.

Extends v4.2 repair gate with:
- R9: Multi-Repair Discipline (exactly two repairs, one per regime)
- R10: Non-Subsumption Constraint (Repair B must not be subsumed by Repair A)

Per spec: poc_spec_v4.3.md and v43_implementation_answers.md
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Set,
    Tuple,
)

from .dsl import (
    ActionClass,
    Condition,
    ConditionOp,
    Effect,
    NormativeRule,
    PatchOp,
    PatchOperation,
    RuleType,
)

if TYPE_CHECKING:
    from .norm_state import NormStateV430
    from .trace import TraceEntry


# ============================================================================
# Repair Failure Reasons (v4.3 extended)
# ============================================================================


class RepairFailureReasonV430(Enum):
    """Enumeration of repair validation failure reasons."""

    # v4.2 inherited reasons
    R1_NO_RULE_MODIFIED = "R1_NO_RULE_MODIFIED"
    R1_RULE_NOT_RESPONSIBLE = "R1_RULE_NOT_RESPONSIBLE"
    R2_STILL_NO_PROGRESS = "R2_STILL_NO_PROGRESS"
    R2_COMPILATION_FAILED = "R2_COMPILATION_FAILED"
    R3_COMPILATION_FAILED = "R3_COMPILATION_FAILED"
    R4_NEW_DEFAULT_DETECTED = "R4_NEW_DEFAULT_DETECTED"
    R5_OVERLAPPING_RULES = "R5_OVERLAPPING_RULES"
    R6_MISSING_PRIOR_EPOCH = "R6_MISSING_PRIOR_EPOCH"
    R6_WRONG_PRIOR_EPOCH = "R6_WRONG_PRIOR_EPOCH"
    R7_TRACE_ENTRY_NOT_FOUND = "R7_TRACE_ENTRY_NOT_FOUND"
    R7_RULE_NOT_IN_TRACE = "R7_RULE_NOT_IN_TRACE"
    R7_NO_CITED_RULE_MODIFIED = "R7_NO_CITED_RULE_MODIFIED"
    R8_COMPILER_DRIFT = "R8_COMPILER_DRIFT"

    # v4.2 retry limit
    R9_V42_RETRY_EXHAUSTED = "R9_V42_RETRY_EXHAUSTED"

    # v4.3 new reasons
    R9_PATCH_STACKING = "R9_PATCH_STACKING"  # Third repair attempt
    R9_WRONG_REGIME = "R9_WRONG_REGIME"  # Repair in wrong regime
    R9_DUPLICATE_REGIME_REPAIR = "R9_DUPLICATE_REGIME_REPAIR"  # Second repair in same regime
    R10_B_SUBSUMED_BY_A = "R10_B_SUBSUMED_BY_A"  # Repair B not needed after A

    # v4.3 Option B: Non-vacuous Repair A
    R2A_VACUOUS_EXCEPTION = "R2A_VACUOUS_EXCEPTION"  # Exception always true in regime (vacuous repeal)

    # v4.3 partial repair rejection
    PARTIAL_B_REPAIR = "PARTIAL_B_REPAIR"  # Only one of R7/R8 modified


# ============================================================================
# Repair Action Types (v4.3)
# ============================================================================


@dataclass(frozen=True)
class LawRepairActionV430:
    """
    A repair action submitted to the Law-Repair Gate.

    v4.3 extends with:
    - contradiction_type: 'A' or 'B' to track which contradiction this repairs
    - regime_at_submission: The regime when this repair was submitted
    """

    trace_entry_id: str
    rule_ids: Tuple[str, ...]
    patch_ops: Tuple[PatchOperation, ...]
    prior_repair_epoch: Optional[str]
    repair_fingerprint: str
    contradiction_type: str  # 'A' or 'B'
    regime_at_submission: int  # 1 or 2

    def __post_init__(self) -> None:
        """Validate repair action invariants."""
        if self.contradiction_type not in ('A', 'B'):
            raise ValueError(f"contradiction_type must be 'A' or 'B', got: {self.contradiction_type}")
        if self.regime_at_submission not in (1, 2):
            raise ValueError(f"regime_at_submission must be 1 or 2, got: {self.regime_at_submission}")

    @classmethod
    def create(
        cls,
        trace_entry_id: str,
        rule_ids: List[str],
        patch_ops: List[PatchOperation],
        prior_repair_epoch: Optional[str],
        contradiction_type: str,
        regime_at_submission: int,
    ) -> "LawRepairActionV430":
        """Factory method with fingerprint computation."""
        # Sort for deterministic fingerprint
        sorted_rule_ids = tuple(sorted(rule_ids))
        sorted_patch_ops = tuple(sorted(patch_ops, key=lambda p: p.target_rule_id))

        # Compute repair fingerprint
        h = hashlib.sha256()
        h.update(trace_entry_id.encode('utf-8'))
        for rule_id in sorted_rule_ids:
            h.update(rule_id.encode('utf-8'))
        for patch in sorted_patch_ops:
            h.update(str(patch.to_dict()).encode('utf-8'))
        if prior_repair_epoch:
            h.update(prior_repair_epoch.encode('utf-8'))
        fingerprint = h.hexdigest()

        return cls(
            trace_entry_id=trace_entry_id,
            rule_ids=sorted_rule_ids,
            patch_ops=sorted_patch_ops,
            prior_repair_epoch=prior_repair_epoch,
            repair_fingerprint=fingerprint,
            contradiction_type=contradiction_type,
            regime_at_submission=regime_at_submission,
        )


# ============================================================================
# Validation Result
# ============================================================================


@dataclass(frozen=True)
class RepairValidationResultV430:
    """Result of repair validation."""

    valid: bool
    failure_reason: Optional[RepairFailureReasonV430] = None
    failure_detail: Optional[str] = None
    new_law_fingerprint: Optional[str] = None
    new_repair_epoch: Optional[str] = None
    patched_norm_state: Optional["NormStateV430"] = None

    @classmethod
    def success(
        cls,
        new_law_fingerprint: str,
        new_repair_epoch: str,
        patched_norm_state: "NormStateV430",
    ) -> "RepairValidationResultV430":
        """Create successful validation result."""
        return cls(
            valid=True,
            new_law_fingerprint=new_law_fingerprint,
            new_repair_epoch=new_repair_epoch,
            patched_norm_state=patched_norm_state,
        )

    @classmethod
    def failure(
        cls,
        reason: RepairFailureReasonV430,
        detail: str,
    ) -> "RepairValidationResultV430":
        """Create failed validation result."""
        return cls(
            valid=False,
            failure_reason=reason,
            failure_detail=detail,
        )


# ============================================================================
# Non-Subsumption Replay Result
# ============================================================================


@dataclass(frozen=True)
class NonSubsumptionReplayResult:
    """Result of R10 non-subsumption replay check."""

    passed: bool
    contradiction_b_still_triggers: bool
    detail: str


# ============================================================================
# Law-Repair Gate (v4.3)
# ============================================================================


class LawRepairGateV430:
    """
    v4.3 Law-Repair Gate with multi-repair discipline.

    Key extensions over v4.2:
    - R9: Exactly two repairs allowed (one per regime)
    - R10: Non-subsumption constraint for Repair B
    - Epoch chain tracking across repairs
    """

    def __init__(
        self,
        trace_log: Dict[str, "TraceEntry"],
        expected_compiler_hash: str,
        env_progress_set_fn: Callable[[Any, Dict[str, str]], Set[str]],
        max_retries_per_contradiction: int = 2,
    ) -> None:
        """
        Initialize v4.3 Law-Repair Gate.

        Args:
            trace_log: Mapping from trace_entry_id to TraceEntry
            expected_compiler_hash: Hash of the compiler for R8 validation
            env_progress_set_fn: Function to compute progress_set from observation
            max_retries_per_contradiction: Max attempts per contradiction (R11)
        """
        self.trace_log = trace_log
        self.expected_compiler_hash = expected_compiler_hash
        self.env_progress_set = env_progress_set_fn
        self.max_retries = max_retries_per_contradiction

        # Regime state
        self.regime: int = 0

        # Epoch chain: [epoch_0, epoch_1, epoch_2]
        self.epoch_chain: List[str] = []

        # Track repairs by regime
        self._repair_by_regime: Dict[int, LawRepairActionV430] = {}

        # Track retry count per trace_entry_id
        self._retry_count: Dict[str, int] = {}

        # Store post-A norm state for R10 replay
        self._post_a_norm_state: Optional["NormStateV430"] = None

    @property
    def repair_count(self) -> int:
        """Total repairs accepted."""
        return len(self._repair_by_regime)

    @property
    def current_epoch(self) -> Optional[str]:
        """Current epoch (latest in chain)."""
        return self.epoch_chain[-1] if self.epoch_chain else None

    def set_regime(self, regime: int) -> None:
        """Update current regime."""
        if regime not in (0, 1, 2):
            raise ValueError(f"Invalid regime: {regime}")
        self.regime = regime

    def initialize_epoch_chain(self, epoch_0: str) -> None:
        """Initialize epoch chain with epoch_0."""
        if self.epoch_chain:
            raise RuntimeError("Epoch chain already initialized")
        self.epoch_chain = [epoch_0]

    def validate_repair(
        self,
        repair_action: LawRepairActionV430,
        norm_state: "NormStateV430",
        obs: Any,
        active_obligation_target: Dict[str, str],
        compiled_permitted_actions: Set[str],
        compile_fn: Callable[["NormStateV430"], Any],
        compiler_hash: str,
        env_nonce: str,
    ) -> RepairValidationResultV430:
        """
        Validate a LAW_REPAIR action per R1-R10.

        Args:
            repair_action: The repair action to validate
            norm_state: Current normative state
            obs: Current observation
            active_obligation_target: The obligation that triggered contradiction
            compiled_permitted_actions: Current permitted actions from compilation
            compile_fn: Function to compile a norm state (for shadow compile)
            compiler_hash: Hash of the compiler being used
            env_nonce: Environment nonce for epoch computation

        Returns:
            RepairValidationResultV430 indicating success or failure
        """
        # ----------------------------------------------------------------
        # R9: Multi-Repair Discipline
        # ----------------------------------------------------------------

        # Check total repair count
        if self.repair_count >= 2:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R9_PATCH_STACKING,
                f"Third repair attempt rejected. Already accepted {self.repair_count} repairs."
            )

        # Check regime correctness
        expected_regime = 1 if repair_action.contradiction_type == 'A' else 2
        if repair_action.regime_at_submission != expected_regime:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R9_WRONG_REGIME,
                f"Contradiction {repair_action.contradiction_type} must be repaired in regime {expected_regime}, "
                f"got regime {repair_action.regime_at_submission}"
            )

        # Check no duplicate repair in same regime
        if repair_action.regime_at_submission in self._repair_by_regime:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R9_DUPLICATE_REGIME_REPAIR,
                f"Already accepted repair in regime {repair_action.regime_at_submission}"
            )

        # ----------------------------------------------------------------
        # R8: Shadow Compiler Lock
        # ----------------------------------------------------------------
        if compiler_hash != self.expected_compiler_hash:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R8_COMPILER_DRIFT,
                f"Compiler hash mismatch: {compiler_hash} != {self.expected_compiler_hash}"
            )

        # ----------------------------------------------------------------
        # R11 (optional): Check retry count
        # ----------------------------------------------------------------
        trace_id = repair_action.trace_entry_id
        if trace_id in self._retry_count:
            if self._retry_count[trace_id] >= self.max_retries:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R9_V42_RETRY_EXHAUSTED,
                    f"Max retries ({self.max_retries}) exhausted for {trace_id}"
                )

        # ----------------------------------------------------------------
        # R7: Trace-Cited Causality
        # ----------------------------------------------------------------
        trace_entry = self.trace_log.get(trace_id)
        if trace_entry is None:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R7_TRACE_ENTRY_NOT_FOUND,
                f"TraceEntryID not found: {trace_id}"
            )

        # Import here to avoid circular dependency
        from .trace import TraceEntryType

        if trace_entry.entry_type != TraceEntryType.CONTRADICTION:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R7_TRACE_ENTRY_NOT_FOUND,
                f"TraceEntry is not a CONTRADICTION: {trace_entry.entry_type}"
            )

        # R7: Verify cited rule_ids exist in trace entry
        trace_blocking_rules = set(trace_entry.blocking_rule_ids or [])
        for rule_id in repair_action.rule_ids:
            if rule_id not in trace_blocking_rules:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R7_RULE_NOT_IN_TRACE,
                    f"Rule {rule_id} not in trace blocking_rule_ids: {trace_blocking_rules}"
                )

        # ----------------------------------------------------------------
        # R6: Anti-Amnesia Rule
        # ----------------------------------------------------------------

        # For Repair A (regime=1): check prior epoch is epoch_0
        # For Repair B (regime=2): check prior epoch is epoch_1
        required_prior_epoch = self.epoch_chain[-1] if self.epoch_chain else None

        if self.repair_count > 0:
            # After first repair, prior_repair_epoch is required
            if repair_action.prior_repair_epoch is None:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R6_MISSING_PRIOR_EPOCH,
                    f"prior_repair_epoch required after repair count {self.repair_count}"
                )
            if repair_action.prior_repair_epoch != required_prior_epoch:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R6_WRONG_PRIOR_EPOCH,
                    f"prior_repair_epoch mismatch: {repair_action.prior_repair_epoch} != {required_prior_epoch}"
                )
        elif self.regime == 1 and repair_action.prior_repair_epoch is not None:
            # First repair in regime 1: prior_repair_epoch should match epoch_0 if provided
            if repair_action.prior_repair_epoch != required_prior_epoch:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R6_WRONG_PRIOR_EPOCH,
                    f"prior_repair_epoch mismatch: {repair_action.prior_repair_epoch} != {required_prior_epoch}"
                )

        # ----------------------------------------------------------------
        # R1: Structural Relevance
        # ----------------------------------------------------------------
        modified_rule_ids = {p.target_rule_id for p in repair_action.patch_ops}
        if not modified_rule_ids:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R1_NO_RULE_MODIFIED,
                "No rules modified by patch operations"
            )

        # R7: Verify at least one cited rule is modified
        cited_rules_modified = modified_rule_ids & set(repair_action.rule_ids)
        if not cited_rules_modified:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R7_NO_CITED_RULE_MODIFIED,
                f"No cited rules modified. Modified: {modified_rule_ids}, Cited: {repair_action.rule_ids}"
            )

        # R1: Verify modified rules are in blocking set
        for rule_id in modified_rule_ids:
            if rule_id not in trace_blocking_rules:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R1_RULE_NOT_RESPONSIBLE,
                    f"Modified rule {rule_id} not in blocking set: {trace_blocking_rules}"
                )

        # ----------------------------------------------------------------
        # Repair B: Check completeness (both R7 and R8 must be modified)
        # ----------------------------------------------------------------
        if repair_action.contradiction_type == 'B':
            required_rules = {'R7', 'R8'}
            if not required_rules.issubset(modified_rule_ids):
                missing = required_rules - modified_rule_ids
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.PARTIAL_B_REPAIR,
                    f"Repair B must modify both R7 and R8. Missing: {missing}"
                )

        # ----------------------------------------------------------------
        # Apply patches to get new norm state
        # ----------------------------------------------------------------
        try:
            patched_norm_state = self._apply_patches(
                norm_state, list(repair_action.patch_ops)
            )
        except Exception as e:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R3_COMPILATION_FAILED,
                f"Failed to apply patches: {e}"
            )

        # ----------------------------------------------------------------
        # R3: Deterministic Compilation
        # ----------------------------------------------------------------
        try:
            compiled_rules = compile_fn(patched_norm_state)
            if not compiled_rules:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R3_COMPILATION_FAILED,
                    "Repaired law failed to compile"
                )
        except Exception as e:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R3_COMPILATION_FAILED,
                f"Compilation error: {e}"
            )

        # ----------------------------------------------------------------
        # R2: Non-Cosmetic Effect
        # ----------------------------------------------------------------
        try:
            # Use compiled rules to determine permitted actions
            new_permitted = self._get_permitted_actions_from_compiled(
                compiled_rules, obs, patched_norm_state.norm_hash
            )
            progress = self.env_progress_set(obs, active_obligation_target)

            intersection = progress & new_permitted
            if not intersection:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R2_STILL_NO_PROGRESS,
                    f"Repair cosmetic: progress={progress}, new_permitted={new_permitted}, intersection empty"
                )
        except Exception as e:
            return RepairValidationResultV430.failure(
                RepairFailureReasonV430.R2_COMPILATION_FAILED,
                f"Failed to verify R2: {e}"
            )

        # ----------------------------------------------------------------
        # R4: No New Defaults
        # ----------------------------------------------------------------
        for patch in repair_action.patch_ops:
            if self._introduces_default(patch):
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R4_NEW_DEFAULT_DETECTED,
                    f"Patch introduces default/fallback: {patch.to_dict()}"
                )

        # ----------------------------------------------------------------
        # R2A: Non-Vacuity Check for Repair A (Option B)
        # ----------------------------------------------------------------
        # Repair A exception must be:
        # - True in contradiction state (s_contra_A)
        # - False in at least one other regime-1 state (s_alt_A)
        # This prevents exceptions that are "always true in regime 1" (vacuous repeal)
        if repair_action.contradiction_type == 'A':
            r2a_result = self._check_non_vacuity_a(
                repair_action=repair_action,
                obs=obs,  # s_contra_A
            )
            if not r2a_result["passed"]:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R2A_VACUOUS_EXCEPTION,
                    r2a_result["detail"]
                )

        # ----------------------------------------------------------------
        # R10: Non-Subsumption Constraint (for Repair B only)
        # ----------------------------------------------------------------
        if repair_action.contradiction_type == 'B':
            r10_result = self._check_non_subsumption(
                repair_action=repair_action,
                obs=obs,
                active_obligation_target=active_obligation_target,
            )
            if not r10_result.passed:
                return RepairValidationResultV430.failure(
                    RepairFailureReasonV430.R10_B_SUBSUMED_BY_A,
                    r10_result.detail
                )

        # ----------------------------------------------------------------
        # All validations passed - compute new epoch
        # ----------------------------------------------------------------
        new_law_fingerprint = patched_norm_state.law_fingerprint
        new_epoch = self._compute_new_epoch(
            previous_epoch=self.epoch_chain[-1] if self.epoch_chain else "",
            repair_fingerprint=repair_action.repair_fingerprint,
            env_nonce=env_nonce,
        )

        # Increment retry count
        self._retry_count[trace_id] = self._retry_count.get(trace_id, 0) + 1

        return RepairValidationResultV430.success(
            new_law_fingerprint=new_law_fingerprint,
            new_repair_epoch=new_epoch,
            patched_norm_state=patched_norm_state,
        )

    def accept_repair(
        self,
        repair_action: LawRepairActionV430,
        new_epoch: str,
        patched_norm_state: "NormStateV430",
    ) -> None:
        """
        Accept a validated repair and update gate state.

        Called after validate_repair returns success.
        """
        # Record repair
        self._repair_by_regime[repair_action.regime_at_submission] = repair_action

        # Extend epoch chain
        self.epoch_chain.append(new_epoch)

        # Store post-A norm state for R10 replay
        if repair_action.contradiction_type == 'A':
            self._post_a_norm_state = patched_norm_state

    def _check_non_subsumption(
        self,
        repair_action: LawRepairActionV430,
        obs: Any,
        active_obligation_target: Dict[str, str],
    ) -> NonSubsumptionReplayResult:
        """
        R10: Check that Contradiction B still triggers under post-A law.

        Replay with post-A law (epoch_1), Repair B not applied.
        If Contradiction B does NOT trigger, Repair B is subsumed by A.
        """
        if self._post_a_norm_state is None:
            # No Repair A accepted yet - this shouldn't happen for Repair B
            return NonSubsumptionReplayResult(
                passed=False,
                contradiction_b_still_triggers=False,
                detail="Cannot check R10: no post-A norm state available"
            )

        # Check if Contradiction B still triggers under post-A law
        try:
            permitted = self._get_permitted_actions(self._post_a_norm_state, obs)
            progress = self.env_progress_set(obs, active_obligation_target)

            intersection = progress & permitted
            contradiction_triggers = len(intersection) == 0

            if not contradiction_triggers:
                return NonSubsumptionReplayResult(
                    passed=False,
                    contradiction_b_still_triggers=False,
                    detail=f"R10 failed: post-A law already permits progress. "
                           f"progress={progress}, permitted={permitted}, intersection={intersection}"
                )

            return NonSubsumptionReplayResult(
                passed=True,
                contradiction_b_still_triggers=True,
                detail=f"R10 passed: Contradiction B still triggers under post-A law. "
                       f"progress={progress}, permitted={permitted}, intersection empty"
            )
        except Exception as e:
            return NonSubsumptionReplayResult(
                passed=False,
                contradiction_b_still_triggers=False,
                detail=f"R10 check failed with error: {e}"
            )

    def _apply_patches(
        self,
        norm_state: "NormStateV430",
        patches: List[PatchOperation],
    ) -> "NormStateV430":
        """Apply patches to norm state and return new state."""
        from .norm_state import NormStateV430

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

        return NormStateV430(rules=new_rules)

    def _get_permitted_actions(
        self,
        norm_state: "NormStateV430",
        obs: Any,
    ) -> Set[str]:
        """
        Get permitted actions from norm state.

        This is a simplified check - actual implementation uses full compiler.
        """
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
            # Simplified condition check
            if rule.type == RuleType.PERMISSION:
                if rule.effect.action_class:
                    permitted |= ACTION_CLASS_TO_IDS.get(rule.effect.action_class.value, set())
            elif rule.type == RuleType.PROHIBITION:
                if rule.effect.action_class:
                    prohibited |= ACTION_CLASS_TO_IDS.get(rule.effect.action_class.value, set())

        return permitted - prohibited

    def _get_permitted_actions_from_compiled(
        self,
        compiled_rules: List[Any],
        obs: Any,
        norm_hash: str,
    ) -> Set[str]:
        """
        Get permitted actions from compiled rules, properly evaluating conditions.

        This evaluates each rule's condition and exception against the observation.

        Args:
            compiled_rules: List of RuleEvalV430 from JCOMP430
            obs: Current observation
            norm_hash: Hash of the norm state

        Returns:
            Set of action IDs that are permitted
        """
        ACTION_CLASS_TO_IDS = {
            "MOVE": {"A0", "A1", "A2", "A3"},
            "COLLECT": {"A4"},
            "DEPOSIT": {"A5"},
            "STAMP": {"A6"},
            "ANY": {"A0", "A1", "A2", "A3", "A4", "A5", "A6"},
        }

        permitted: Set[str] = set()
        prohibited: Set[str] = set()

        for rule in compiled_rules:
            # Check if rule is active (condition is true)
            if not rule.active(obs, norm_hash):
                continue

            action_class = rule.effect.get("action_class")
            if not action_class:
                continue

            actions = ACTION_CLASS_TO_IDS.get(action_class, set())

            if rule.rule_type == "PERMISSION":
                permitted |= actions
            elif rule.rule_type == "PROHIBITION":
                prohibited |= actions

        return permitted - prohibited

    def _introduces_default(self, patch: PatchOperation) -> bool:
        """Check if a patch introduces unconditional permission or fallback."""
        if patch.op == PatchOp.MODIFY_CONDITION:
            # Check if new condition is TRUE (unconditional)
            if patch.new_condition and patch.new_condition.op == ConditionOp.TRUE:
                return True
        return False

    def _check_non_vacuity_a(
        self,
        repair_action: LawRepairActionV430,
        obs: Any,
    ) -> Dict[str, Any]:
        """
        R2A: Non-Vacuity Check for Repair A (Option B).

        The exception predicate must be:
        - True in the contradiction state (s_contra_A = obs)
        - False in at least one other regime-1 state (s_alt_A)

        This prevents exceptions that are "always true in regime 1" (vacuous repeal).

        Preregistered regime-1 states:
        - s_contra_A: regime=1, at STAMP_LOCATION (contradiction trigger)
        - s_alt_A: regime=1, NOT at STAMP_LOCATION (different position)
        """
        from .compiler import compile_condition
        from ..env.tri_demand import POSITIONS, Observation430

        # Extract exception condition from the ADD_EXCEPTION patch
        exception_condition = None
        for patch in repair_action.patch_ops:
            if patch.op == PatchOp.ADD_EXCEPTION and patch.target_rule_id == "R6":
                exception_condition = patch.exception_condition
                break

        if exception_condition is None:
            return {
                "passed": False,
                "detail": "R2A: No exception condition found for R6 in Repair A",
                "exception_at_contra": None,
                "exception_at_alt": None,
            }

        # Compile the exception predicate
        try:
            exception_fn = compile_condition(exception_condition)
        except Exception as e:
            return {
                "passed": False,
                "detail": f"R2A: Failed to compile exception condition: {e}",
                "exception_at_contra": None,
                "exception_at_alt": None,
            }

        # s_contra_A: the current observation (at contradiction state)
        exception_at_contra = exception_fn(obs)

        # s_alt_A: Create a regime-1 state NOT at STAMP_LOCATION
        # Use SOURCE as the alternative position (clearly not STAMP_LOCATION)
        s_alt_A = Observation430(
            agent_pos=POSITIONS["SOURCE"],  # Different from STAMP_LOCATION
            inventory=obs.inventory,
            item_type=obs.item_type,
            zone_a_demand=obs.zone_a_demand,
            zone_b_demand=obs.zone_b_demand,
            zone_c_demand=obs.zone_c_demand,
            zone_a_satisfied=obs.zone_a_satisfied,
            zone_b_satisfied=obs.zone_b_satisfied,
            zone_c_satisfied=obs.zone_c_satisfied,
            step=obs.step,
            episode=obs.episode,
            rule_r1_active=obs.rule_r1_active,
            regime=1,  # Same regime as contradiction
            stamped=obs.stamped,
            dual_delivery_mode=obs.dual_delivery_mode,
            can_deliver_a=obs.can_deliver_a,
            can_deliver_b=obs.can_deliver_b,
        )

        exception_at_alt = exception_fn(s_alt_A)

        # Requirement: exception(s_contra_A) == True AND exception(s_alt_A) == False
        if not exception_at_contra:
            return {
                "passed": False,
                "detail": f"R2A: Exception is False in contradiction state (must be True). "
                          f"exception(s_contra_A)={exception_at_contra}",
                "exception_at_contra": exception_at_contra,
                "exception_at_alt": exception_at_alt,
            }

        if exception_at_alt:
            return {
                "passed": False,
                "detail": f"R2A: Exception is True in alternative regime-1 state (vacuous repeal). "
                          f"exception(s_contra_A)={exception_at_contra}, exception(s_alt_A)={exception_at_alt}. "
                          f"Repair A exception must be False in at least one other regime-1 state.",
                "exception_at_contra": exception_at_contra,
                "exception_at_alt": exception_at_alt,
            }

        return {
            "passed": True,
            "detail": f"R2A passed: exception(s_contra_A)={exception_at_contra}, exception(s_alt_A)={exception_at_alt}",
            "exception_at_contra": exception_at_contra,
            "exception_at_alt": exception_at_alt,
        }

    def _compute_new_epoch(
        self,
        previous_epoch: str,
        repair_fingerprint: str,
        env_nonce: str,
    ) -> str:
        """
        Compute new epoch using epoch-to-epoch chaining.

        epoch_n := H(epoch_{n-1} ∥ repair_fingerprint ∥ env_nonce)
        """
        h = hashlib.sha256()
        h.update(previous_epoch.encode('utf-8'))
        h.update(repair_fingerprint.encode('utf-8'))
        h.update(env_nonce.encode('utf-8'))
        return h.hexdigest()


# ============================================================================
# Canonical Repair B Factory
# ============================================================================


def create_canonical_repair_b(
    trace_entry_id: str,
    prior_repair_epoch: str,
) -> LawRepairActionV430:
    """
    Create the canonical Repair B patch.

    Per v43_implementation_answers.md:
    - R7: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A
          → PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A UNLESS can_deliver_A
    - R8: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B
          → PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B UNLESS can_deliver_B
    """
    # Create exception conditions
    exception_r7 = Condition(op=ConditionOp.CAN_DELIVER_A)
    exception_r8 = Condition(op=ConditionOp.CAN_DELIVER_B)

    # Create patch operations (canonical ordering: R7 then R8)
    patch_r7 = PatchOperation(
        op=PatchOp.ADD_EXCEPTION,
        target_rule_id="R7",
        exception_condition=exception_r7,
    )
    patch_r8 = PatchOperation(
        op=PatchOp.ADD_EXCEPTION,
        target_rule_id="R8",
        exception_condition=exception_r8,
    )

    return LawRepairActionV430.create(
        trace_entry_id=trace_entry_id,
        rule_ids=["R7", "R8"],
        patch_ops=[patch_r7, patch_r8],
        prior_repair_epoch=prior_repair_epoch,
        contradiction_type='B',
        regime_at_submission=2,
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "LawRepairActionV430",
    "RepairFailureReasonV430",
    "RepairValidationResultV430",
    "NonSubsumptionReplayResult",
    "LawRepairGateV430",
    "create_canonical_repair_b",
]
