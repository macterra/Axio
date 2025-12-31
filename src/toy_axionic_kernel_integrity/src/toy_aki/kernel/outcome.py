"""
Delta Outcome Schema for v0.3.1 Adaptive Feedback.

Provides structured feedback to external optimizers without
exposing kernel internals or semantic information.

All signals are:
- Structural (not semantic)
- Stable across versions
- Coarse-grained (no fine scores)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import FrozenSet


class RejectionReasonCode(Enum):
    """
    Structured rejection reason codes for adaptive feedback.

    Requirements:
    - Must be structural (no semantics like "deceptive")
    - Must be stable across versions
    - Must be coarse-grained
    """
    # Corridor violations
    INADMISSIBLE_P5 = auto()              # P5 inadmissibility triggered
    P2P_DELEGATION_VIOLATION = auto()     # P2' non-delegable actuation violated
    ACV_SCHEMA_VIOLATION = auto()         # ACV chain/schema requirements violated

    # Evaluability failures (KNS-E)
    EVALUABILITY_ATTRIBUTION_FAIL = auto()        # Attribution capability would break
    EVALUABILITY_REJECTION_FAIL = auto()          # Rejection capability would break
    EVALUABILITY_REJECTION_CHAIN_FAIL = auto()    # Rejection chain capability would break
    EVALUABILITY_DELEGATION_DETECT_FAIL = auto()  # Delegation detection would break

    # Delta format/application errors
    DELTA_INVALID_FORMAT = auto()         # Delta is syntactically invalid
    DELTA_APPLICATION_ERROR = auto()      # Delta could not be applied
    DELTA_PAYLOAD_ERROR = auto()          # Payload is invalid for delta type

    # Wrapper/containment violations
    WRAPPER_DELEGATION_DETECTED = auto()  # Wrapper classified as delegation violation

    # Resource/budget violations (v0.3.1.c)
    RESOURCE_BUDGET_EXCEEDED = auto()     # Exceeded resource cap (if enforced)

    # Accept (not a rejection - used for classification completeness)
    ACCEPTED = auto()                     # Delta was accepted (not a rejection)


class NearFailureFlag(Enum):
    """
    Binary near-failure flags for adaptive feedback.

    Each flag indicates: "one more weakening would break this capability."
    Computed via shadow-state simulation, not arbitrary thresholds.
    """
    NF_ATTRIBUTION = auto()           # Attribution check near-failing
    NF_REJECTION = auto()             # Rejection capability near-failing
    NF_REJECTION_CHAIN = auto()       # Rejection chain near-failing
    NF_DELEGATION_DETECT = auto()     # Delegation detection near-failing


@dataclass(frozen=True)
class DeltaOutcome:
    """
    Structured outcome feedback for v0.3.1 adaptive optimizers.

    Contains only signals permitted by spec §3.1:
    - accept/reject bit
    - rejection reason code (structural only)
    - whether R incremented and which dimensions
    - near-failure flags (binary only)
    - step index

    Explicitly excluded:
    - Kernel internals
    - Hidden state
    - Semantic labels
    """
    # Basic outcome
    accepted: bool
    rejection_reason_code: RejectionReasonCode

    # R increment information
    r_incremented: bool
    r_dimensions_changed: FrozenSet[str] = frozenset()

    # Near-failure flags (binary only)
    near_failure_flags: FrozenSet[NearFailureFlag] = frozenset()

    # Step tracking
    step_index: int = 0

    # R value after this step
    r_value_after: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "accepted": self.accepted,
            "rejection_reason_code": self.rejection_reason_code.name,
            "r_incremented": self.r_incremented,
            "r_dimensions_changed": sorted(self.r_dimensions_changed),
            "near_failure_flags": sorted(f.name for f in self.near_failure_flags),
            "step_index": self.step_index,
            "r_value_after": self.r_value_after,
        }

    @classmethod
    def accepted_outcome(
        cls,
        r_incremented: bool,
        r_dimensions_changed: FrozenSet[str],
        near_failure_flags: FrozenSet[NearFailureFlag],
        step_index: int,
        r_value_after: int,
    ) -> DeltaOutcome:
        """Create accepted outcome."""
        return cls(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=r_incremented,
            r_dimensions_changed=r_dimensions_changed,
            near_failure_flags=near_failure_flags,
            step_index=step_index,
            r_value_after=r_value_after,
        )

    @classmethod
    def rejected_outcome(
        cls,
        reason_code: RejectionReasonCode,
        near_failure_flags: FrozenSet[NearFailureFlag],
        step_index: int,
        r_value_after: int,
    ) -> DeltaOutcome:
        """Create rejected outcome."""
        return cls(
            accepted=False,
            rejection_reason_code=reason_code,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=near_failure_flags,
            step_index=step_index,
            r_value_after=r_value_after,
        )


def map_reason_string_to_code(reason: str | None) -> RejectionReasonCode:
    """
    Map legacy string rejection reasons to structured codes.

    Used for backward compatibility with v0.3 rejection strings.
    """
    if reason is None:
        return RejectionReasonCode.ACCEPTED

    reason_lower = reason.lower()

    # P5/P2' corridor
    if "p5" in reason_lower or "inadmissible" in reason_lower:
        return RejectionReasonCode.INADMISSIBLE_P5
    if "p2" in reason_lower or "delegation" in reason_lower:
        return RejectionReasonCode.P2P_DELEGATION_VIOLATION
    if "acv" in reason_lower or "chain" in reason_lower:
        return RejectionReasonCode.ACV_SCHEMA_VIOLATION

    # Evaluability
    if "attribution" in reason_lower:
        return RejectionReasonCode.EVALUABILITY_ATTRIBUTION_FAIL
    if "rejection_chain" in reason_lower or "rejection chain" in reason_lower:
        return RejectionReasonCode.EVALUABILITY_REJECTION_CHAIN_FAIL
    if "rejection" in reason_lower:
        return RejectionReasonCode.EVALUABILITY_REJECTION_FAIL
    if "detection" in reason_lower or "wrapper" in reason_lower:
        return RejectionReasonCode.EVALUABILITY_DELEGATION_DETECT_FAIL

    # Delta errors
    if "format" in reason_lower or "invalid" in reason_lower:
        return RejectionReasonCode.DELTA_INVALID_FORMAT
    if "application" in reason_lower or "apply" in reason_lower:
        return RejectionReasonCode.DELTA_APPLICATION_ERROR
    if "payload" in reason_lower:
        return RejectionReasonCode.DELTA_PAYLOAD_ERROR

    # Evaluability generic (fallback)
    if "evaluability" in reason_lower:
        return RejectionReasonCode.EVALUABILITY_REJECTION_FAIL

    # Default to P5 for unrecognized inadmissibility
    if "inadmissible" in reason_lower:
        return RejectionReasonCode.INADMISSIBLE_P5

    # Fallback
    return RejectionReasonCode.DELTA_APPLICATION_ERROR
