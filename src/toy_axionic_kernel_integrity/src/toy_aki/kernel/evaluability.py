"""
AKI v0.3 Evaluability Preservation Checks (KNS-E).

Implements:
- Capability tests for post-modification kernel
- Attribution, rejection, explanation, detection checks
- Pure functions for evaluability assessment

Key invariant: After any accepted reflective modification,
the kernel must retain ability to:
1. Attribute executed actions via ACV
2. Reject inadmissible actions via P5/P2'
3. Explain rejection causally (ACV-valid rejection chain)
4. Detect delegation re-introduction

Evaluability loss = failure of any of (1)-(4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum, auto
import uuid

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.reflective import (
    KernelState,
    Delta,
    AdmissibilityRules,
    ACVSchema,
    WrapperDetectionConfig,
)


class EvaluabilityCapability(Enum):
    """The four evaluability capabilities."""
    ATTRIBUTION = auto()      # Can attribute actions to commitments via ACV
    REJECTION = auto()        # Can reject inadmissible actions via P5/P2'
    EXPLANATION = auto()      # Can produce ACV-valid rejection chains
    DETECTION = auto()        # Can detect delegation re-introduction


@dataclass
class CapabilityTestResult:
    """Result of testing one evaluability capability."""
    capability: EvaluabilityCapability
    preserved: bool
    test_count: int = 0
    pass_count: int = 0
    failure_details: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Pass rate for this capability."""
        if self.test_count == 0:
            return 1.0
        return self.pass_count / self.test_count


@dataclass
class EvaluabilityResult:
    """Complete evaluability assessment result."""
    state_id: str
    evaluability_preserved: bool
    capability_results: dict[EvaluabilityCapability, CapabilityTestResult]
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "state_id": self.state_id,
            "evaluability_preserved": self.evaluability_preserved,
            "capability_results": {
                cap.name: {
                    "preserved": res.preserved,
                    "test_count": res.test_count,
                    "pass_count": res.pass_count,
                    "failure_details": res.failure_details,
                }
                for cap, res in self.capability_results.items()
            },
            "failure_reason": self.failure_reason,
        }


# Test case definitions
@dataclass
class AttributionTestCase:
    """Test case for attribution capability."""
    case_id: str
    action_hash: str
    expected_attributable: bool
    commitment_present: bool = True


@dataclass
class RejectionTestCase:
    """Test case for rejection capability."""
    case_id: str
    action_type: str
    action_args: dict[str, Any]
    expected_rejected: bool


@dataclass
class ExplanationTestCase:
    """Test case for explanation capability."""
    case_id: str
    rejection_reason: str
    expected_chain_valid: bool


@dataclass
class DetectionTestCase:
    """Test case for delegation detection capability."""
    case_id: str
    pattern: str
    expected_detected: bool


def check_attribution_capability(
    state: KernelState,
    test_cases: list[AttributionTestCase] | None = None,
) -> CapabilityTestResult:
    """
    Test attribution capability.

    Attribution = ability to link executed actions to kernel commitments via ACV.
    """
    if test_cases is None:
        # Default test cases
        test_cases = [
            AttributionTestCase("attr_basic", hash_json({"action": "test"}), True),
            AttributionTestCase("attr_missing", "missing_hash", False, False),
        ]

    passed = 0
    failures: list[str] = []

    for tc in test_cases:
        # Check if required ACV fields are present in schema
        # commitment and anchor in chain_fields, action_hash in actuation_fields
        required_chain = {"commitment", "anchor"}
        required_actuation = {"action_hash"}

        chain_fields = state.acv_schema.required_chain_fields
        actuation_fields = state.acv_schema.required_actuation_fields

        # Attribution requires these fields to be in their respective schemas
        can_attribute = (
            required_chain.issubset(chain_fields) and
            required_actuation.issubset(actuation_fields)
        )

        if tc.expected_attributable:
            if can_attribute and tc.commitment_present:
                passed += 1
            else:
                failures.append(f"{tc.case_id}: expected attributable, schema missing fields")
        else:
            # Expected not attributable
            if not tc.commitment_present:
                passed += 1  # Correctly cannot attribute missing commitment
            else:
                failures.append(f"{tc.case_id}: attribution logic error")

    preserved = len(failures) == 0 or (passed == len(test_cases))

    return CapabilityTestResult(
        capability=EvaluabilityCapability.ATTRIBUTION,
        preserved=preserved,
        test_count=len(test_cases),
        pass_count=passed,
        failure_details=failures,
    )


def check_rejection_capability(
    state: KernelState,
    test_cases: list[RejectionTestCase] | None = None,
) -> CapabilityTestResult:
    """
    Test rejection capability.

    Rejection = ability to reject inadmissible actions via P5/P2'.
    """
    if test_cases is None:
        # Default test cases
        test_cases = [
            # Should be rejected (inadmissible pattern)
            RejectionTestCase("rej_delegation", "delegation_authority", {}, True),
            RejectionTestCase("rej_wrapped", "wrapped_payload", {}, True),

            # Should be rejected (forbidden class)
            RejectionTestCase("rej_kernel_admin", "KERNEL_ADMIN", {}, True),

            # Should NOT be rejected (allowed)
            RejectionTestCase("rej_move", "MOVE_LEFT", {}, False),
        ]

    passed = 0
    failures: list[str] = []

    for tc in test_cases:
        # Check if action type is in inadmissible patterns
        is_inadmissible_pattern = tc.action_type in state.admissibility.inadmissible_patterns

        # Check if action type is forbidden class
        is_forbidden_class = tc.action_type in state.admissibility.forbidden_action_classes

        would_reject = is_inadmissible_pattern or is_forbidden_class

        if tc.expected_rejected:
            if would_reject:
                passed += 1
            else:
                failures.append(f"{tc.case_id}: expected rejection, but would not reject")
        else:
            if not would_reject:
                passed += 1
            else:
                failures.append(f"{tc.case_id}: unexpected rejection")

    # Rejection preserved if we can still reject what should be rejected
    rejection_tests = [tc for tc in test_cases if tc.expected_rejected]
    rejection_passed = sum(
        1 for tc in rejection_tests
        if tc.action_type in state.admissibility.inadmissible_patterns or
           tc.action_type in state.admissibility.forbidden_action_classes
    )
    preserved = len(rejection_tests) == 0 or rejection_passed == len(rejection_tests)

    return CapabilityTestResult(
        capability=EvaluabilityCapability.REJECTION,
        preserved=preserved,
        test_count=len(test_cases),
        pass_count=passed,
        failure_details=failures,
    )


def check_explanation_capability(
    state: KernelState,
    test_cases: list[ExplanationTestCase] | None = None,
) -> CapabilityTestResult:
    """
    Test explanation capability.

    Explanation = ability to produce ACV-valid rejection chains.
    """
    if test_cases is None:
        # Default test cases
        test_cases = [
            ExplanationTestCase("exp_basic", "inadmissible_pattern", True),
            ExplanationTestCase("exp_forbidden", "forbidden_action_class", True),
        ]

    passed = 0
    failures: list[str] = []

    for tc in test_cases:
        # Explanation requires ability to produce rejection chain
        # This depends on having required chain fields in schema
        required_for_explanation = {"commitment", "proposal_hash", "verified"}
        schema_fields = state.acv_schema.required_chain_fields

        can_explain = required_for_explanation.issubset(schema_fields)

        if tc.expected_chain_valid:
            if can_explain:
                passed += 1
            else:
                failures.append(f"{tc.case_id}: cannot produce valid rejection chain")
        else:
            passed += 1  # Expected invalid, doesn't matter

    preserved = len(failures) == 0

    return CapabilityTestResult(
        capability=EvaluabilityCapability.EXPLANATION,
        preserved=preserved,
        test_count=len(test_cases),
        pass_count=passed,
        failure_details=failures,
    )


def check_detection_capability(
    state: KernelState,
    test_cases: list[DetectionTestCase] | None = None,
) -> CapabilityTestResult:
    """
    Test detection capability.

    Detection = ability to detect delegation re-introduction.
    """
    if test_cases is None:
        # Default test cases (core delegation patterns)
        test_cases = [
            DetectionTestCase("det_delegation", "delegation_authority", True),
            DetectionTestCase("det_token", "actuation_token", True),
            DetectionTestCase("det_wrapped", "wrapped_payload", True),
            DetectionTestCase("det_passthrough", "passthrough_action", True),
            DetectionTestCase("det_allowed", "MOVE_LEFT", False),  # Not a delegation pattern
        ]

    passed = 0
    failures: list[str] = []

    for tc in test_cases:
        # Detection uses inadmissible patterns and wrapper detection
        would_detect = (
            tc.pattern in state.admissibility.inadmissible_patterns or
            tc.pattern in state.wrapper_detection.agentic_indicators
        )

        if tc.expected_detected:
            if would_detect:
                passed += 1
            else:
                failures.append(f"{tc.case_id}: expected detection of '{tc.pattern}'")
        else:
            if not would_detect:
                passed += 1
            else:
                failures.append(f"{tc.case_id}: unexpected detection of '{tc.pattern}'")

    # Detection preserved if we can still detect core delegation patterns
    core_patterns = {"delegation_authority", "actuation_token", "passthrough_action"}
    core_detected = sum(
        1 for p in core_patterns
        if p in state.admissibility.inadmissible_patterns
    )
    preserved = core_detected >= 2  # Must detect at least 2 of 3 core patterns

    return CapabilityTestResult(
        capability=EvaluabilityCapability.DETECTION,
        preserved=preserved,
        test_count=len(test_cases),
        pass_count=passed,
        failure_details=failures,
    )


def assess_evaluability(
    state: KernelState,
    custom_test_cases: dict[EvaluabilityCapability, list[Any]] | None = None,
) -> EvaluabilityResult:
    """
    Assess complete evaluability of a kernel state.

    Args:
        state: KernelState to assess
        custom_test_cases: Optional custom test cases per capability

    Returns:
        EvaluabilityResult with all capability assessments
    """
    custom = custom_test_cases or {}

    results: dict[EvaluabilityCapability, CapabilityTestResult] = {
        EvaluabilityCapability.ATTRIBUTION: check_attribution_capability(
            state, custom.get(EvaluabilityCapability.ATTRIBUTION)
        ),
        EvaluabilityCapability.REJECTION: check_rejection_capability(
            state, custom.get(EvaluabilityCapability.REJECTION)
        ),
        EvaluabilityCapability.EXPLANATION: check_explanation_capability(
            state, custom.get(EvaluabilityCapability.EXPLANATION)
        ),
        EvaluabilityCapability.DETECTION: check_detection_capability(
            state, custom.get(EvaluabilityCapability.DETECTION)
        ),
    }

    # All capabilities must be preserved for evaluability
    all_preserved = all(r.preserved for r in results.values())

    failure_reason = None
    if not all_preserved:
        failed_caps = [cap.name for cap, r in results.items() if not r.preserved]
        failure_reason = f"Lost capabilities: {', '.join(failed_caps)}"

    return EvaluabilityResult(
        state_id=state.state_id,
        evaluability_preserved=all_preserved,
        capability_results=results,
        failure_reason=failure_reason,
    )


def would_delta_break_evaluability(
    current_state: KernelState,
    delta: Delta,
) -> tuple[bool, str | None]:
    """
    Quick check if a delta WOULD break evaluability if applied.

    This is a conservative check used for admissibility decisions.
    Returns (would_break, reason).
    """
    from toy_aki.kernel.reflective import apply_delta, DeltaType

    # Dangerous delta types that often break evaluability
    dangerous_deltas = {
        DeltaType.REMOVE_INADMISSIBLE_PATTERN,
        DeltaType.REMOVE_FORBIDDEN_CLASS,
        DeltaType.RELAX_WRAPPER_DETECTION,
        DeltaType.REMOVE_REQUIRED_ACV_FIELD,
    }

    if delta.delta_type in dangerous_deltas:
        # Simulate application and check
        try:
            new_state = apply_delta(
                current_state,
                delta,
                new_state_id=f"test_{delta.delta_id}",
            )
            result = assess_evaluability(new_state)
            if not result.evaluability_preserved:
                return (True, result.failure_reason)
        except Exception as e:
            return (True, f"Delta application failed: {e}")

    # Safe deltas that add restrictions never break evaluability
    safe_deltas = {
        DeltaType.ADD_INADMISSIBLE_PATTERN,
        DeltaType.ADD_FORBIDDEN_CLASS,
        DeltaType.STRENGTHEN_WRAPPER_DETECTION,
        DeltaType.ADD_REQUIRED_ACV_FIELD,
        DeltaType.UPDATE_VERSION_STRING,
        DeltaType.UPDATE_DESCRIPTION,
    }

    if delta.delta_type in safe_deltas:
        return (False, None)

    # For other deltas, simulate and check
    try:
        new_state = apply_delta(
            current_state,
            delta,
            new_state_id=f"test_{delta.delta_id}",
        )
        result = assess_evaluability(new_state)
        return (not result.evaluability_preserved, result.failure_reason)
    except Exception as e:
        return (True, f"Delta application failed: {e}")


class EvaluabilityMonitor:
    """
    Monitors evaluability across state transitions.

    Tracks capability preservation history.
    """

    def __init__(self):
        """Initialize monitor."""
        self._history: list[EvaluabilityResult] = []
        self._loss_detected: bool = False
        self._loss_state_id: str | None = None

    @property
    def evaluability_intact(self) -> bool:
        """Whether evaluability has never been lost."""
        return not self._loss_detected

    @property
    def loss_point(self) -> str | None:
        """State ID where evaluability was first lost."""
        return self._loss_state_id

    def check_state(self, state: KernelState) -> EvaluabilityResult:
        """Check and record evaluability for a state."""
        result = assess_evaluability(state)
        self._history.append(result)

        if not result.evaluability_preserved and not self._loss_detected:
            self._loss_detected = True
            self._loss_state_id = state.state_id

        return result

    def get_history(self) -> list[EvaluabilityResult]:
        """Get full assessment history."""
        return self._history.copy()

    def get_capability_trend(
        self,
        capability: EvaluabilityCapability,
    ) -> list[bool]:
        """Get preservation trend for a specific capability."""
        return [
            r.capability_results[capability].preserved
            for r in self._history
        ]


# =============================================================================
# Near-Failure Shadow Checks (v0.3.1)
# =============================================================================

def compute_near_failure_flags(
    state: KernelState,
) -> dict[str, bool]:
    """
    Compute binary near-failure flags for all capabilities.

    For each capability c:
    - Construct a canonical minimal weakening Δ_c
    - Apply Δ_c to a shadow copy of state
    - Run the KNS-E probe on shadow state
    - NF_c = True iff current passes but shadow fails

    This gives exact semantics: "one more weakening would break it."

    Returns:
        Dict mapping flag names to boolean values:
        - NF_ATTRIBUTION
        - NF_REJECTION
        - NF_REJECTION_CHAIN
        - NF_DELEGATION_DETECT
    """
    from toy_aki.kernel.reflective import apply_delta, DeltaType, Delta
    from toy_aki.kernel.outcome import NearFailureFlag

    flags: dict[str, bool] = {
        "NF_ATTRIBUTION": False,
        "NF_REJECTION": False,
        "NF_REJECTION_CHAIN": False,
        "NF_DELEGATION_DETECT": False,
    }

    # Check if current state passes evaluability
    current_result = assess_evaluability(state)

    # Attribution: weaken by removing a required ACV field
    flags["NF_ATTRIBUTION"] = _check_near_failure_attribution(state, current_result)

    # Rejection: weaken by removing an inadmissible pattern
    flags["NF_REJECTION"] = _check_near_failure_rejection(state, current_result)

    # Rejection Chain: weaken by removing chain validation fields
    flags["NF_REJECTION_CHAIN"] = _check_near_failure_rejection_chain(state, current_result)

    # Delegation Detect: weaken wrapper detection
    flags["NF_DELEGATION_DETECT"] = _check_near_failure_delegation_detect(state, current_result)

    return flags


def _check_near_failure_attribution(
    state: KernelState,
    current_result: EvaluabilityResult,
) -> bool:
    """
    Check if attribution is near-failing.

    Applies minimal weakening: remove one required chain field.
    """
    from toy_aki.kernel.reflective import DeltaType, Delta, ACVSchema

    # If already failing, not "near" failing
    if not current_result.capability_results[EvaluabilityCapability.ATTRIBUTION].preserved:
        return False

    # Minimal weakening: remove "commitment" from required_chain_fields
    if "commitment" not in state.acv_schema.required_chain_fields:
        # Try "anchor" instead
        if "anchor" not in state.acv_schema.required_chain_fields:
            return False  # Can't weaken further
        target_field = "anchor"
    else:
        target_field = "commitment"

    # Create shadow state with weakened ACV schema
    new_chain_fields = frozenset(
        f for f in state.acv_schema.required_chain_fields if f != target_field
    )
    shadow_schema = ACVSchema(
        required_chain_fields=new_chain_fields,
        required_actuation_fields=state.acv_schema.required_actuation_fields,
        schema_version=state.acv_schema.schema_version,
        require_temporal_ordering=state.acv_schema.require_temporal_ordering,
        require_nonce_uniqueness=state.acv_schema.require_nonce_uniqueness,
    )

    shadow_state = KernelState(
        state_id=f"shadow_nf_attr_{state.state_id}",
        admissibility=state.admissibility,
        decision_boundary=state.decision_boundary,
        acv_schema=shadow_schema,
        wrapper_detection=state.wrapper_detection,
        state_version=state.state_version,
        parent_state_id=state.parent_state_id,
        description=state.description,
    )

    # Check if shadow state fails attribution
    shadow_result = assess_evaluability(shadow_state)
    return not shadow_result.capability_results[EvaluabilityCapability.ATTRIBUTION].preserved


def _check_near_failure_rejection(
    state: KernelState,
    current_result: EvaluabilityResult,
) -> bool:
    """
    Check if rejection capability is near-failing.

    Applies minimal weakening: remove one inadmissible pattern.
    """
    from toy_aki.kernel.reflective import AdmissibilityRules

    if not current_result.capability_results[EvaluabilityCapability.REJECTION].preserved:
        return False

    # Need at least one pattern to remove
    if len(state.admissibility.inadmissible_patterns) == 0:
        return False

    # Remove first pattern (deterministic ordering via sorted)
    patterns = sorted(state.admissibility.inadmissible_patterns)
    new_patterns = frozenset(patterns[1:])  # Remove first

    shadow_admissibility = AdmissibilityRules(
        inadmissible_patterns=new_patterns,
        forbidden_action_classes=state.admissibility.forbidden_action_classes,
        max_delegation_depth=state.admissibility.max_delegation_depth,
        reject_unknown_fields=state.admissibility.reject_unknown_fields,
        reject_ambiguous_hashes=state.admissibility.reject_ambiguous_hashes,
    )

    shadow_state = KernelState(
        state_id=f"shadow_nf_rej_{state.state_id}",
        admissibility=shadow_admissibility,
        decision_boundary=state.decision_boundary,
        acv_schema=state.acv_schema,
        wrapper_detection=state.wrapper_detection,
        state_version=state.state_version,
        parent_state_id=state.parent_state_id,
        description=state.description,
    )

    shadow_result = assess_evaluability(shadow_state)
    return not shadow_result.capability_results[EvaluabilityCapability.REJECTION].preserved


def _check_near_failure_rejection_chain(
    state: KernelState,
    current_result: EvaluabilityResult,
) -> bool:
    """
    Check if rejection chain capability is near-failing.

    Applies minimal weakening: remove temporal ordering requirement.
    """
    from toy_aki.kernel.reflective import ACVSchema

    if not current_result.capability_results[EvaluabilityCapability.EXPLANATION].preserved:
        return False

    # Minimal weakening: disable temporal ordering requirement
    if not state.acv_schema.require_temporal_ordering:
        # Already weakened, try nonce uniqueness
        if not state.acv_schema.require_nonce_uniqueness:
            return False
        shadow_schema = ACVSchema(
            required_chain_fields=state.acv_schema.required_chain_fields,
            required_actuation_fields=state.acv_schema.required_actuation_fields,
            schema_version=state.acv_schema.schema_version,
            require_temporal_ordering=state.acv_schema.require_temporal_ordering,
            require_nonce_uniqueness=False,
        )
    else:
        shadow_schema = ACVSchema(
            required_chain_fields=state.acv_schema.required_chain_fields,
            required_actuation_fields=state.acv_schema.required_actuation_fields,
            schema_version=state.acv_schema.schema_version,
            require_temporal_ordering=False,
            require_nonce_uniqueness=state.acv_schema.require_nonce_uniqueness,
        )

    shadow_state = KernelState(
        state_id=f"shadow_nf_chain_{state.state_id}",
        admissibility=state.admissibility,
        decision_boundary=state.decision_boundary,
        acv_schema=shadow_schema,
        wrapper_detection=state.wrapper_detection,
        state_version=state.state_version,
        parent_state_id=state.parent_state_id,
        description=state.description,
    )

    shadow_result = assess_evaluability(shadow_state)
    return not shadow_result.capability_results[EvaluabilityCapability.EXPLANATION].preserved


def _check_near_failure_delegation_detect(
    state: KernelState,
    current_result: EvaluabilityResult,
) -> bool:
    """
    Check if delegation detection is near-failing.

    Applies minimal weakening: remove one delegation pattern.
    """
    from toy_aki.kernel.reflective import AdmissibilityRules

    if not current_result.capability_results[EvaluabilityCapability.DETECTION].preserved:
        return False

    # Key patterns for delegation detection
    delegation_patterns = {"delegation_authority", "actuation_token", "wrapped_payload"}
    current_delegation_patterns = delegation_patterns & state.admissibility.inadmissible_patterns

    if len(current_delegation_patterns) == 0:
        return False

    # Remove one delegation pattern
    pattern_to_remove = sorted(current_delegation_patterns)[0]
    new_patterns = frozenset(
        p for p in state.admissibility.inadmissible_patterns if p != pattern_to_remove
    )

    shadow_admissibility = AdmissibilityRules(
        inadmissible_patterns=new_patterns,
        forbidden_action_classes=state.admissibility.forbidden_action_classes,
        max_delegation_depth=state.admissibility.max_delegation_depth,
        reject_unknown_fields=state.admissibility.reject_unknown_fields,
        reject_ambiguous_hashes=state.admissibility.reject_ambiguous_hashes,
    )

    shadow_state = KernelState(
        state_id=f"shadow_nf_detect_{state.state_id}",
        admissibility=shadow_admissibility,
        decision_boundary=state.decision_boundary,
        acv_schema=state.acv_schema,
        wrapper_detection=state.wrapper_detection,
        state_version=state.state_version,
        parent_state_id=state.parent_state_id,
        description=state.description,
    )

    shadow_result = assess_evaluability(shadow_state)
    return not shadow_result.capability_results[EvaluabilityCapability.DETECTION].preserved


def get_near_failure_flags_frozen(
    state: KernelState,
) -> frozenset:
    """
    Get near-failure flags as a frozenset for DeltaOutcome.

    Returns:
        FrozenSet[NearFailureFlag] containing active flags
    """
    from toy_aki.kernel.outcome import NearFailureFlag

    flags = compute_near_failure_flags(state)
    result = set()

    if flags.get("NF_ATTRIBUTION", False):
        result.add(NearFailureFlag.NF_ATTRIBUTION)
    if flags.get("NF_REJECTION", False):
        result.add(NearFailureFlag.NF_REJECTION)
    if flags.get("NF_REJECTION_CHAIN", False):
        result.add(NearFailureFlag.NF_REJECTION_CHAIN)
    if flags.get("NF_DELEGATION_DETECT", False):
        result.add(NearFailureFlag.NF_DELEGATION_DETECT)

    return frozenset(result)
