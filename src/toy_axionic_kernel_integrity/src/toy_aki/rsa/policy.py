"""
RSA v1.0 & v2.0 Policy Module.

Defines intentional adversaries that operate at the action-selection layer.
v1.0 policies are stateless; v2.0 policies have minimal bounded adaptive state.

v1.0 Models (A-E): Stateless, deterministic, non-adaptive
v2.0 Models (F-I): Minimal bounded adaptive adversaries with observable interface

Key constraints:
- Non-adaptive (v1.0): no access to authority state, lapse history, or evaluation outcomes
- Minimal adaptive (v2.0): bounded state, observable interface only, no semantic interpretation
- Non-invasive: policies emit actions that the kernel then accepts or rejects
- Removable: v2.0 policies can be disabled without kernel changes
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional, FrozenSet


class RSAPolicyModel(Enum):
    """
    RSA adversary policy models.

    v1.0 models (A-E): Stateless, deterministic, non-adaptive.
    v2.0 models (F-I): Minimal bounded adaptive adversaries.
    """

    NONE = "NONE"  # No policy override; agent runs normally

    # v1.0 models
    ALWAYS_FAIL_COMMITMENT = "ALWAYS_FAIL_COMMITMENT"      # Model A
    MINIMAL_ELIGIBILITY_ONLY = "MINIMAL_ELIGIBILITY_ONLY"  # Model B
    FIXED_RENEWAL_TIMING = "FIXED_RENEWAL_TIMING"          # Model C
    ALWAYS_SELF_RENEW = "ALWAYS_SELF_RENEW"                # Model D
    LAZY_DICTATOR = "LAZY_DICTATOR"                        # Model E

    # v2.0 adaptive models
    OUTCOME_TOGGLE = "OUTCOME_TOGGLE"                      # Model F
    CTA_PHASE_AWARE = "CTA_PHASE_AWARE"                    # Model G
    ELIGIBILITY_EDGE_PROBE = "ELIGIBILITY_EDGE_PROBE"      # Model H
    RENEWAL_FEEDBACK = "RENEWAL_FEEDBACK"                  # Model I


@dataclass(frozen=True)
class RSAPolicyConfig:
    """
    Configuration for RSA v1.0 and v2.0 policies.

    v1.0 Attributes:
        policy_model: Which adversary model to use
        target_commitment: For Model A, which commitment to violate ("C0", "C1", "C2")
        timing_offset_epochs: For Model C, epoch offset pattern for satisfaction
        timing_period_epochs: For Model C, period of the satisfaction pattern
        epoch_size: Cycles per epoch (for action scheduling)

    v2.0 Attributes (adaptive models F-I):
        rsa_version: "v1" or "v2" for version coexistence
        rsa_invalid_target_key: Which commitment to use for invalid actions ("C0", "C1", "C2")
        rsa_max_internal_states: Maximum adaptive states (bounded state constraint)
        rsa_toggle_on_lapse: For Model F, toggle on ANY lapse vs specific outcomes
        rsa_rng_stream: RNG stream name for stochastic policies (default: "rsa_v200")
    """

    policy_model: RSAPolicyModel = RSAPolicyModel.NONE

    # v1.0 Model A parameters
    target_commitment: str = "C0"  # Which commitment to always violate

    # v1.0 Model C/E parameters
    timing_offset_epochs: int = 0  # Epoch offset within period where satisfaction occurs
    timing_period_epochs: int = 1  # Period of timing pattern (1 = every epoch)

    # Shared parameters
    epoch_size: int = 50  # Cycles per epoch

    # v2.0 parameters
    rsa_version: str = "v1"  # "v1" or "v2"
    rsa_invalid_target_key: str = "C0"  # Target for invalid commitment actions
    rsa_max_internal_states: int = 4  # Bounded adaptive state limit
    rsa_toggle_on_lapse: bool = True  # Model F: toggle on ANY lapse vs outcome-specific
    rsa_rng_stream: str = "rsa_v200"  # RNG stream for v2.0 policies

    def __post_init__(self):
        """Validate configuration."""
        if isinstance(self.policy_model, str):
            object.__setattr__(self, 'policy_model', RSAPolicyModel(self.policy_model))

        if self.target_commitment not in ("C0", "C1", "C2"):
            raise ValueError(
                f"target_commitment must be 'C0', 'C1', or 'C2', got {self.target_commitment}"
            )

        if self.timing_period_epochs < 1:
            raise ValueError(
                f"timing_period_epochs must be >= 1, got {self.timing_period_epochs}"
            )

        if self.epoch_size < 1:
            raise ValueError(
                f"epoch_size must be >= 1, got {self.epoch_size}"
            )

        # v2.0 validation
        if self.rsa_version not in ("v1", "v2"):
            raise ValueError(
                f"rsa_version must be 'v1' or 'v2', got {self.rsa_version}"
            )

        if self.rsa_invalid_target_key not in ("C0", "C1", "C2"):
            raise ValueError(
                f"rsa_invalid_target_key must be 'C0', 'C1', or 'C2', got {self.rsa_invalid_target_key}"
            )

        if self.rsa_max_internal_states < 1:
            raise ValueError(
                f"rsa_max_internal_states must be >= 1, got {self.rsa_max_internal_states}"
            )

        # Validate v2.0 models only used with v2.0 version
        v2_models = {
            RSAPolicyModel.OUTCOME_TOGGLE,
            RSAPolicyModel.CTA_PHASE_AWARE,
            RSAPolicyModel.ELIGIBILITY_EDGE_PROBE,
            RSAPolicyModel.RENEWAL_FEEDBACK
        }
        if self.policy_model in v2_models and self.rsa_version != "v2":
            raise ValueError(
                f"Policy model {self.policy_model.value} requires rsa_version='v2', got '{self.rsa_version}'"
            )


# ============================================================================
# v2.0 Observable Outcome Interface
# ============================================================================

class CTABucket(Enum):
    """CTA phase buckets for v2.0 observable interface."""
    INACTIVE = "INACTIVE"
    EARLY = "EARLY"
    MID = "MID"
    LATE = "LATE"


class EligibilityBucket(Enum):
    """Eligibility streak buckets for v2.0 observable interface (K=3 context)."""
    SAFE = "SAFE"          # streak ≤ 1
    EDGE = "EDGE"          # streak = 2
    INELIGIBLE = "INELIGIBLE"  # streak ≥ 3


class RenewalOutcome(Enum):
    """Renewal attempt outcome for v2.0 observable interface."""
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"


class AuthorityStatus(Enum):
    """Authority status for v2.0 observable interface."""
    HAS_AUTHORITY = "HAS_AUTHORITY"
    NULL_AUTHORITY = "NULL_AUTHORITY"


@dataclass(frozen=True)
class ObservableOutcome:
    """
    v2.0 Observable outcome interface (FROZEN SPEC).

    Provides kernel-external observables for bounded adaptive adversaries.
    Sampled at the start of epoch N (reflecting outcomes of epoch N-1).

    6 observables (deterministic from kernel state):
    1. epoch_index: Current epoch number
    2. authority_status: HAS_AUTHORITY or NULL_AUTHORITY
    3. lapse_occurred: Did ANY commitment lapse occur last epoch?
    4. renewal_outcome: SUCCEEDED, FAILED, or NOT_ATTEMPTED (never None)
    5. cta_phase: INACTIVE, EARLY, MID, or LATE
    6. eligibility_bucket: SAFE, EDGE, or INELIGIBLE
    """
    epoch_index: int
    authority_status: AuthorityStatus
    lapse_occurred: bool
    renewal_outcome: RenewalOutcome
    cta_phase: CTABucket
    eligibility_bucket: EligibilityBucket


def compute_cta_bucket(cta_active: bool, current_index: int, cta_length: int) -> CTABucket:
    """
    Compute CTA phase bucket using equal thirds via floor division.

    Args:
        cta_active: Is CTA currently active?
        current_index: Current position in CTA (0-based)
        cta_length: Total CTA length

    Returns:
        CTABucket (INACTIVE, EARLY, MID, or LATE)
    """
    if not cta_active:
        return CTABucket.INACTIVE

    if cta_length == 0:
        return CTABucket.INACTIVE  # Empty CTA treated as inactive

    b1 = cta_length // 3
    b2 = 2 * cta_length // 3

    if current_index < b1:
        return CTABucket.EARLY
    elif current_index < b2:
        return CTABucket.MID
    else:
        return CTABucket.LATE


def compute_eligibility_bucket(successive_renewal_failures: int, K: int = 3) -> EligibilityBucket:
    """
    Compute eligibility bucket based on renewal failure streak.

    Args:
        successive_renewal_failures: Current streak of renewal failures
        K: Eligibility limit (default 3 for AKI v0.8)

    Returns:
        EligibilityBucket (SAFE, EDGE, or INELIGIBLE)
    """
    if successive_renewal_failures <= 1:
        return EligibilityBucket.SAFE
    elif successive_renewal_failures == 2:
        return EligibilityBucket.EDGE
    else:  # >= 3
        return EligibilityBucket.INELIGIBLE


# ============================================================================
# v2.0 Action Primitives
# ============================================================================

class ActionPrimitive(Enum):
    """
    v2.0 Action primitives for adaptive adversary policies.

    These are conceptual primitives that map to EpochPlans via v1.0 generators.
    Maintains architectural separation: no direct kernel manipulation.
    """
    COMPLIANT = "COMPLIANT"         # Satisfy all commitments (use full sequence)
    INVALID_COMMIT = "INVALID_COMMIT"  # Attempt invalid commitment action
    MAX_RENT = "MAX_RENT"           # Minimize commitment satisfaction (violate all)
    MIN_EFFORT = "MIN_EFFORT"       # Minimal actions for eligibility (same as COMPLIANT in ALS-A)
    NO_OP = "NO_OP"                 # No actions (pure WAIT)


def primitive_to_epoch_plan(
    primitive: ActionPrimitive,
    epoch: int,
    cycle_in_epoch: int,
    config: RSAPolicyConfig
) -> Dict[str, Any]:
    """
    Convert action primitive to epoch plan via v1.0 action generators.

    This is Option A from binding decisions: thin adapter over existing generators.
    Maintains v1.0 architectural separation without duplicating generator logic.

    Args:
        primitive: Action primitive to convert
        epoch: Current epoch (0-based)
        cycle_in_epoch: Cycle within epoch (0-based)
        config: Policy configuration

    Returns:
        Action dict compatible with harness interface
    """
    if primitive == ActionPrimitive.COMPLIANT:
        # Use full commitment sequence generator
        return _full_commitment_sequence(epoch, cycle_in_epoch)

    elif primitive == ActionPrimitive.INVALID_COMMIT:
        # Generate invalid action targeting specified commitment
        return _make_invalid_action(epoch, cycle_in_epoch, config.rsa_invalid_target_key)

    elif primitive == ActionPrimitive.MAX_RENT:
        # Maximal legal expressivity (highest rent while legal)
        # In ALS-A: full action plan with maximum expressivity
        return _make_max_rent_action(epoch, cycle_in_epoch)

    elif primitive == ActionPrimitive.MIN_EFFORT:
        # Minimal legal behavior distinct from NO_OP
        # Single cheap action (e.g. GET only)
        return _make_min_effort_action(epoch, cycle_in_epoch)

    elif primitive == ActionPrimitive.NO_OP:
        # Pure WAIT (no commitment attempt)
        return _make_wait_action()

    else:
        raise ValueError(f"Unknown action primitive: {primitive}")


def _make_max_rent_action(epoch: int, cycle_in_epoch: int) -> Dict[str, Any]:
    """
    Generate maximal legal expressivity action (highest rent while legal).

    In ALS-A context, this means full commitment satisfaction with maximum
    expressivity. This is the highest-rent legal action plan.

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch

    Returns:
        Action dict with maximal legal expressivity
    """
    # Full commitment sequence represents maximal legal expressivity
    return _full_commitment_sequence(epoch, cycle_in_epoch)


def _make_min_effort_action(epoch: int, cycle_in_epoch: int) -> Dict[str, Any]:
    """
    Generate minimal legal effort action distinct from NO_OP.

    Single cheap action (e.g. GET) that shows activity but minimal expressivity.

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch

    Returns:
        Action dict with minimal legal effort
    """
    # Single GET action - minimal but distinct from WAIT
    return {
        "action_type": ACTION_GET,
        "payload": {"key": "minimal_effort_probe"},
        "source": "rsa_v2_min_effort",
    }


def _make_invalid_action(epoch: int, cycle_in_epoch: int, target_key: str) -> Dict[str, Any]:
    """
    Generate invalid commitment action for specified target.

    Invalid actions are correctly formatted but violate commitment semantics:
    - C0: LOG with missing required field
    - C1: SET with invalid key format
    - C2: SEQUENCE with too few actions

    These should be accepted by harness but fail commitment verification.

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch
        target_key: Which commitment to target ("C0", "C1", "C2")

    Returns:
        Invalid action dict
    """
    if target_key == "C0":
        # Invalid LOG: missing required "message" field
        return {
            "action_type": ACTION_LOG,
            "payload": {"epoch": epoch},  # Missing "message" field
            "source": "rsa_v2_invalid",
        }
    elif target_key == "C1":
        # Invalid SET: use reserved key that fails verifier
        return {
            "action_type": ACTION_SET,
            "payload": {"key": "INVALID_KEY", "value": epoch},
            "source": "rsa_v2_invalid",
        }
    elif target_key == "C2":
        # Invalid SEQUENCE: too few actions (C2 requires >= 2)
        return {
            "action_type": ACTION_SEQUENCE,
            "payload": {"actions": [{"op": "NOOP"}]},  # Only 1 action, needs >= 2
            "source": "rsa_v2_invalid",
        }
    else:
        # Unknown target, default to WAIT
        return _make_wait_action()


# ============================================================================
# ALS-A Action Constants (from harness/verifiers)
# ============================================================================

# Action types that satisfy specific commitments in ALS-A
# Based on CommitmentAwareSuccessor_v1 in generator.py:
# - C0: LOG action in epoch
# - C1: SET + GET actions in epoch
# - C2: SEQUENCE action when epoch % 3 == 0

ACTION_LOG = "LOG"
ACTION_SET = "SET"
ACTION_GET = "GET"
ACTION_SEQUENCE = "SEQUENCE"
ACTION_WAIT = "WAIT"

# All commitment actions used by RSA v1.0 policies.
# Exported for harness interface expansion.
RSA_COMMITMENT_ACTIONS: FrozenSet[str] = frozenset({
    ACTION_LOG, ACTION_SET, ACTION_GET, ACTION_SEQUENCE, ACTION_WAIT
})


# ============================================================================
# Policy Base Class
# ============================================================================

class RSAPolicy(ABC):
    """
    Abstract base class for RSA v1.0 policies.

    Policies are stateless: emit() is a pure function of (epoch, cycle, config).
    """

    @abstractmethod
    def emit(self, epoch: int, cycle_in_epoch: int, config: RSAPolicyConfig) -> Dict[str, Any]:
        """
        Emit an action for the given epoch and cycle.

        Args:
            epoch: Current epoch index (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            config: Policy configuration

        Returns:
            Action dict with 'action_type' and 'payload'
        """
        pass

    @property
    @abstractmethod
    def model(self) -> RSAPolicyModel:
        """Return the policy model enum."""
        pass


# ============================================================================
# v2.0 Adaptive Adversary Base Class
# ============================================================================

class AdaptiveRSAAdversary(ABC):
    """
    Abstract base class for RSA v2.0 adaptive adversaries.

    v2.0 adversaries have minimal bounded adaptive state and operate via
    observable outcome interface. All models are deterministic and kernel-external.

    State constraints:
    - Bounded: max_internal_states limit (default 4)
    - Global: persists across entire run (including successions)
    - Observable-only: state transitions based solely on ObservableOutcome
    - Deterministic: state transitions are pure functions

    Interface constraints:
    - Must implement select_action() as total function
    - Must implement update_state() for observable-driven state transitions
    - Must provide get_state() for telemetry
    - Must respect max_internal_states bound
    """

    def __init__(self, config: RSAPolicyConfig):
        """
        Initialize adaptive adversary.

        Args:
            config: Policy configuration
        """
        self._config = config
        self._internal_state: int = 0  # Start in state 0

    @abstractmethod
    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """
        Select action primitive based on observable outcome and internal state.

        This is the strategy map: (observable, state) → action
        Must be a total function (defined for all valid inputs).

        Args:
            observable: Current observable outcome
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)

        Returns:
            ActionPrimitive to execute
        """
        pass

    @abstractmethod
    def update_state(self, observable: ObservableOutcome) -> None:
        """
        Update internal state based on observable outcome.

        Called at the start of each epoch (after observable sampling).
        State transitions must be deterministic and respect bounded state constraint.

        Args:
            observable: Current observable outcome
        """
        pass

    def get_state(self) -> int:
        """
        Get current internal state.

        Returns:
            Current state index (0-based)
        """
        return self._internal_state

    def reset_state(self) -> None:
        """
        Reset internal state to initial value.

        Note: In v2.0, state persists across successions by default.
        This method exists for testing and explicit reset scenarios.
        """
        self._internal_state = 0

    @property
    @abstractmethod
    def model(self) -> RSAPolicyModel:
        """Return the policy model enum."""
        pass

    def emit(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        config: RSAPolicyConfig
    ) -> Dict[str, Any]:
        """
        Emit action by selecting primitive and converting to epoch plan.

        This is the top-level emission function that:
        1. Selects action primitive based on observable + state
        2. Converts primitive to epoch plan via adapter
        3. Tags action with v2.0 telemetry

        Args:
            observable: Current observable outcome
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            config: Policy configuration

        Returns:
            Action dict with telemetry tags
        """
        # Select action primitive
        primitive = self.select_action(observable, epoch, cycle_in_epoch)

        # Convert to epoch plan
        action = primitive_to_epoch_plan(primitive, epoch, cycle_in_epoch, config)

        # Tag with v2.0 telemetry
        action["rsa_generated"] = True
        action["rsa_version"] = "v2"
        action["rsa_model"] = self.model.value
        action["rsa_primitive"] = primitive.value
        action["rsa_state"] = self._internal_state

        return action


# ============================================================================
# Commitment Satisfaction Helpers
# ============================================================================

def _make_log_action(epoch: int, source: str = "rsa_policy") -> Dict[str, Any]:
    """Create LOG action for C0 satisfaction."""
    return {
        "action_type": ACTION_LOG,
        "payload": {"message": f"epoch_{epoch}_presence", "epoch": epoch},
        "source": source,
    }


def _make_set_action(epoch: int, source: str = "rsa_policy") -> Dict[str, Any]:
    """Create SET action for C1 (part 1)."""
    return {
        "action_type": ACTION_SET,
        "payload": {"key": "c1", "value": epoch},
        "source": source,
    }


def _make_get_action(epoch: int, source: str = "rsa_policy") -> Dict[str, Any]:
    """Create GET action for C1 (part 2)."""
    return {
        "action_type": ACTION_GET,
        "payload": {"key": "c1"},
        "source": source,
    }


def _make_sequence_action(epoch: int, source: str = "rsa_policy") -> Dict[str, Any]:
    """Create SEQUENCE action for C2 (required when epoch % 3 == 0).

    Note: C2 verifier requires payload["actions"] with length >= 2.
    """
    return {
        "action_type": ACTION_SEQUENCE,
        "payload": {"actions": [{"op": "NOOP"}, {"op": "NOOP"}]},
        "source": source,
    }


def _make_wait_action(source: str = "rsa_policy") -> Dict[str, Any]:
    """Create WAIT action (no commitment implications)."""
    return {
        "action_type": ACTION_WAIT,
        "payload": {},
        "source": source,
    }


def _full_commitment_sequence(epoch: int, cycle_in_epoch: int) -> Optional[Dict[str, Any]]:
    """
    Emit action sequence that satisfies all commitments (C0, C1, C2).

    Schedule (for complete commitment satisfaction):
    - Cycle 0: LOG (C0)
    - Cycle 1: SET (C1 part 1)
    - Cycle 2: GET (C1 part 2)
    - Cycle 3: SEQUENCE (C2)
    - Cycle 4+: WAIT

    NOTE: SEQUENCE is emitted every epoch that requests full satisfaction,
    regardless of epoch % 3. This ensures C2's 3-epoch window always contains
    at least one SEQUENCE when the policy intends full compliance.

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch (0-based)

    Returns:
        Action dict
    """
    if cycle_in_epoch == 0:
        return _make_log_action(epoch)
    elif cycle_in_epoch == 1:
        return _make_set_action(epoch)
    elif cycle_in_epoch == 2:
        return _make_get_action(epoch)
    elif cycle_in_epoch == 3:
        # Always emit SEQUENCE for full satisfaction
        # C2's window=3 means we just need SEQUENCE within any 3-epoch span
        return _make_sequence_action(epoch)
    else:
        return _make_wait_action()


def _skip_commitment(
    epoch: int,
    cycle_in_epoch: int,
    skip_target: str
) -> Dict[str, Any]:
    """
    Emit action sequence that skips one specific commitment.

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch
        skip_target: Which commitment to skip ("C0", "C1", "C2")

    Returns:
        Action dict (WAIT if the cycle would normally satisfy skip_target)
    """
    if skip_target == "C0":
        # Skip LOG at cycle 0
        if cycle_in_epoch == 0:
            return _make_wait_action()
        elif cycle_in_epoch == 1:
            return _make_set_action(epoch)
        elif cycle_in_epoch == 2:
            return _make_get_action(epoch)
        elif cycle_in_epoch == 3 and epoch % 3 == 0:
            return _make_sequence_action(epoch)
        else:
            return _make_wait_action()

    elif skip_target == "C1":
        # Skip SET/GET at cycles 1-2
        if cycle_in_epoch == 0:
            return _make_log_action(epoch)
        elif cycle_in_epoch in (1, 2):
            return _make_wait_action()
        elif cycle_in_epoch == 3 and epoch % 3 == 0:
            return _make_sequence_action(epoch)
        else:
            return _make_wait_action()

    elif skip_target == "C2":
        # Skip SEQUENCE at cycle 3 (only matters when epoch % 3 == 0)
        if cycle_in_epoch == 0:
            return _make_log_action(epoch)
        elif cycle_in_epoch == 1:
            return _make_set_action(epoch)
        elif cycle_in_epoch == 2:
            return _make_get_action(epoch)
        elif cycle_in_epoch == 3:
            # Always WAIT, even when epoch % 3 == 0
            return _make_wait_action()
        else:
            return _make_wait_action()

    else:
        # Unknown target, default to full sequence
        return _full_commitment_sequence(epoch, cycle_in_epoch)


# ============================================================================
# Model A: ALWAYS_FAIL_COMMITMENT
# ============================================================================

class AlwaysFailCommitmentPolicy(RSAPolicy):
    """
    Model A: Always violates one designated commitment.

    Emits actions that satisfy all commitments except the target.
    The target commitment is never satisfied in any epoch.

    Purpose: Test survivability under deliberate incompetence or sabotage.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.ALWAYS_FAIL_COMMITMENT

    def emit(self, epoch: int, cycle_in_epoch: int, config: RSAPolicyConfig) -> Dict[str, Any]:
        """Emit action that skips the target commitment."""
        return _skip_commitment(epoch, cycle_in_epoch, config.target_commitment)


# ============================================================================
# Model B: MINIMAL_ELIGIBILITY_ONLY
# ============================================================================

class MinimalEligibilityOnlyPolicy(RSAPolicy):
    """
    Model B: Satisfies exactly the minimum commitments required for eligibility.

    In ALS-A with strict conjunction, this means satisfying all commitments,
    but with minimal action count (no redundant actions).

    Purpose: Test hollow authority persistence absent adaptation.

    ALS-A Note: Under strict AND, the "minimal" trace is the unique trace that
    satisfies C0 AND C1 AND C2. This may collapse behaviorally with Model D.
    Distinguish via telemetry (steps_used, action_count).
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY

    def emit(self, epoch: int, cycle_in_epoch: int, config: RSAPolicyConfig) -> Dict[str, Any]:
        """Emit minimal action sequence for full compliance."""
        # In ALS-A, minimal = full commitment sequence (strict AND)
        return _full_commitment_sequence(epoch, cycle_in_epoch)


# ============================================================================
# Model C: FIXED_RENEWAL_TIMING
# ============================================================================

class FixedRenewalTimingPolicy(RSAPolicy):
    """
    Model C: Satisfies commitments only at fixed epoch offsets.

    Uses timing_offset_epochs and timing_period_epochs to determine
    which epochs get commitment satisfaction vs violation.

    Schedule: satisfy commitments when (epoch % period) == offset

    Purpose: Test timing misuse without feedback exploitation.

    ALS-A Note: Controls commitment satisfaction timing via action emission.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.FIXED_RENEWAL_TIMING

    def emit(self, epoch: int, cycle_in_epoch: int, config: RSAPolicyConfig) -> Dict[str, Any]:
        """Emit actions based on timing schedule."""
        # Satisfy commitments only when epoch matches the timing pattern
        should_satisfy = (epoch % config.timing_period_epochs) == config.timing_offset_epochs

        if should_satisfy:
            return _full_commitment_sequence(epoch, cycle_in_epoch)
        else:
            # Violate all commitments by just emitting WAIT
            return _make_wait_action()


# ============================================================================
# Model D: ALWAYS_SELF_RENEW
# ============================================================================

class AlwaysSelfRenewPolicy(RSAPolicy):
    """
    Model D: Maintains continuous eligibility for automatic renewal.

    Always emits commitment-satisfying actions every epoch.
    Never intentionally drops SEM_PASS.

    Purpose: Test structural entrenchment via blind persistence.

    ALS-A Note: Renewal is automatic at renewal_check_interval; no explicit
    ACTION_RENEW exists. Model D maintains continuous eligibility so renewals
    succeed whenever checked. May collapse behaviorally with Model B under
    strict conjunction if minimal trace is unique.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.ALWAYS_SELF_RENEW

    def emit(self, epoch: int, cycle_in_epoch: int, config: RSAPolicyConfig) -> Dict[str, Any]:
        """Emit full commitment sequence for continuous eligibility."""
        return _full_commitment_sequence(epoch, cycle_in_epoch)


# ============================================================================
# Model E: LAZY_DICTATOR
# ============================================================================

class LazyDictatorPolicy(RSAPolicy):
    """
    Model E: Compound misuse - scheduled compliance with minimal satisfaction.

    Operationally equivalent to Model C (FIXED_RENEWAL_TIMING):
    - SATISFY epochs: emit full commitment sequence (pass all commitments)
    - VIOLATE epochs: emit WAIT only (violate all commitments)

    Schedule: satisfy when (epoch % period) == offset, violate otherwise.

    Purpose: Test compound fixed strategy combining intermittent compliance
    with continuous eligibility pressure. Represents "lazy dictator" archetype:
    comply only when scheduled, otherwise do nothing.

    RSA v1.0: Fixed, deterministic, non-adaptive, outcome-blind.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.LAZY_DICTATOR

    def emit(self, epoch: int, cycle_in_epoch: int, config: RSAPolicyConfig) -> Dict[str, Any]:
        """Emit actions based on timing schedule (same as Model C)."""
        # Satisfy commitments only when epoch matches the timing pattern
        should_satisfy = (epoch % config.timing_period_epochs) == config.timing_offset_epochs

        if should_satisfy:
            return _full_commitment_sequence(epoch, cycle_in_epoch)
        else:
            # Violate all commitments by just emitting WAIT
            return _make_wait_action()


# ============================================================================
# v2.0 Adaptive Models (F-I)
# ============================================================================

class OutcomeToggleAdversary(AdaptiveRSAAdversary):
    """
    Model F: OUTCOME_TOGGLE

    Binary state adversary that toggles behavior based on commitment lapse.

    States:
    - 0: COMPLIANT (satisfy all commitments)
    - 1: MAX_RENT (violate all commitments)

    Transitions:
    - Toggle state when lapse_occurred = True
    - Maintain state otherwise

    Purpose: Test minimal outcome-reactive adaptation with binary strategy.
    Simplest possible adaptive adversary.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.OUTCOME_TOGGLE

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """Select action based on lapse occurrence (FROZEN SPEC)."""
        if observable.lapse_occurred:
            return ActionPrimitive.INVALID_COMMIT
        else:
            return ActionPrimitive.MAX_RENT

    def update_state(self, observable: ObservableOutcome) -> None:
        """Stateless model - no state updates."""
        pass


class CTAPhaseAwareAdversary(AdaptiveRSAAdversary):
    """
    Model G: CTA_PHASE_AWARE

    Stateless adversary that branches on CTA phase.

    Strategy map:
    - EARLY: COMPLIANT
    - MIDDLE: INVALID_COMMIT
    - LATE: MAX_RENT

    Purpose: Test phase-sensitive adaptation without state persistence.
    Explores CTA structure exploitation.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.CTA_PHASE_AWARE

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """Select action based on CTA phase bucket (FROZEN SPEC)."""
        if observable.cta_phase == CTABucket.INACTIVE:
            return ActionPrimitive.MAX_RENT
        elif observable.cta_phase == CTABucket.EARLY:
            return ActionPrimitive.INVALID_COMMIT
        elif observable.cta_phase == CTABucket.MID:
            return ActionPrimitive.MIN_EFFORT
        else:  # LATE
            return ActionPrimitive.COMPLIANT

    def update_state(self, observable: ObservableOutcome) -> None:
        """Stateless: no state updates."""
        pass


class EligibilityEdgeProbeAdversary(AdaptiveRSAAdversary):
    """
    Model H: ELIGIBILITY_EDGE_PROBE

    Stateless adversary that branches on eligibility distance.

    Strategy map:
    - SAFE (streak ≤ 1): MAX_RENT (push toward edge)
    - EDGE (streak = 2): COMPLIANT (stay at edge, avoid ineligibility)
    - INELIGIBLE (streak ≥ 3): NO_OP (passive, already ineligible)

    Purpose: Test eligibility boundary exploitation.
    Explores "edge-riding" strategy at K-1 threshold.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.ELIGIBILITY_EDGE_PROBE

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """Select action based on eligibility bucket (FROZEN SPEC)."""
        if observable.eligibility_bucket == EligibilityBucket.SAFE:
            return ActionPrimitive.MAX_RENT
        elif observable.eligibility_bucket == EligibilityBucket.EDGE:
            return ActionPrimitive.INVALID_COMMIT  # CRITICAL FIX
        else:  # INELIGIBLE
            return ActionPrimitive.NO_OP

    def update_state(self, observable: ObservableOutcome) -> None:
        """Stateless: no state updates."""
        pass


class RenewalFeedbackAdversary(AdaptiveRSAAdversary):
    """
    Model I: RENEWAL_FEEDBACK

    Stateless adversary that branches on renewal outcome.

    Strategy map:
    - SUCCESS: INVALID_COMMIT (test resilience after successful renewal)
    - FAILURE: COMPLIANT (attempt recovery)
    - None (no renewal attempt): COMPLIANT (default)

    Purpose: Test renewal-driven adaptation.
    Explores post-renewal behavioral shifts.
    """

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.RENEWAL_FEEDBACK

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """Select action based on renewal outcome (FROZEN SPEC)."""
        if observable.renewal_outcome == RenewalOutcome.SUCCEEDED:
            return ActionPrimitive.MAX_RENT
        elif observable.renewal_outcome == RenewalOutcome.FAILED:
            return ActionPrimitive.INVALID_COMMIT
        else:  # NOT_ATTEMPTED
            return ActionPrimitive.MIN_EFFORT

    def update_state(self, observable: ObservableOutcome) -> None:
        """Stateless: no state updates."""
        pass


# ============================================================================
# Policy Factory
# ============================================================================

def create_policy(model: RSAPolicyModel) -> Optional[RSAPolicy]:
    """
    Factory function to create v1.0 policy instance from model enum.

    Args:
        model: Policy model enum (v1.0 models only)

    Returns:
        Policy instance, or None for NONE model
    """
    if model == RSAPolicyModel.NONE:
        return None
    elif model == RSAPolicyModel.ALWAYS_FAIL_COMMITMENT:
        return AlwaysFailCommitmentPolicy()
    elif model == RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY:
        return MinimalEligibilityOnlyPolicy()
    elif model == RSAPolicyModel.FIXED_RENEWAL_TIMING:
        return FixedRenewalTimingPolicy()
    elif model == RSAPolicyModel.ALWAYS_SELF_RENEW:
        return AlwaysSelfRenewPolicy()
    elif model == RSAPolicyModel.LAZY_DICTATOR:
        return LazyDictatorPolicy()
    else:
        raise ValueError(f"Unknown v1.0 policy model: {model}")


def create_adaptive_adversary(model: RSAPolicyModel, config: RSAPolicyConfig) -> Optional[AdaptiveRSAAdversary]:
    """
    Factory function to create v2.0 adaptive adversary from model enum.

    Args:
        model: Policy model enum (v2.0 models only)
        config: Policy configuration

    Returns:
        AdaptiveRSAAdversary instance, or None for NONE model
    """
    if model == RSAPolicyModel.NONE:
        return None
    elif model == RSAPolicyModel.OUTCOME_TOGGLE:
        return OutcomeToggleAdversary(config)
    elif model == RSAPolicyModel.CTA_PHASE_AWARE:
        return CTAPhaseAwareAdversary(config)
    elif model == RSAPolicyModel.ELIGIBILITY_EDGE_PROBE:
        return EligibilityEdgeProbeAdversary(config)
    elif model == RSAPolicyModel.RENEWAL_FEEDBACK:
        return RenewalFeedbackAdversary(config)
    else:
        raise ValueError(f"Unknown v2.0 policy model: {model}")



# ============================================================================
# Policy Wrapper (for harness integration)
# ============================================================================

class RSAPolicyWrapper:
    """
    Wrapper that intercepts propose_action calls when RSA v1.0 policy is active.

    This is injected between the harness and the agent to override action
    proposals with adversarial policy emissions.

    Usage:
        wrapper = RSAPolicyWrapper.from_config(policy_config)
        if wrapper is not None:
            action = wrapper.intercept(epoch, cycle_in_epoch, original_action)
        else:
            action = original_action
    """

    def __init__(self, policy: RSAPolicy, config: RSAPolicyConfig):
        self._policy = policy
        self._config = config

    @classmethod
    def from_config(cls, config: Optional[RSAPolicyConfig]) -> Optional["RSAPolicyWrapper"]:
        """
        Create wrapper from config, or None if policy is NONE/disabled.

        Args:
            config: Policy configuration

        Returns:
            RSAPolicyWrapper if policy is active, None otherwise
        """
        if config is None:
            return None

        policy = create_policy(config.policy_model)
        if policy is None:
            return None

        return cls(policy, config)

    @property
    def model(self) -> RSAPolicyModel:
        """Return active policy model."""
        return self._policy.model

    def intercept(
        self,
        epoch: int,
        cycle_in_epoch: int,
        original_action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intercept action proposal and return adversarial action.

        Args:
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            original_action: Original agent action (ignored, kept for telemetry)

        Returns:
            Adversarial action from policy
        """
        action = self._policy.emit(epoch, cycle_in_epoch, self._config)

        # Tag action as RSA-generated for telemetry
        action["rsa_generated"] = True
        action["rsa_model"] = self._policy.model.value

        return action

    def get_telemetry(self) -> Dict[str, Any]:
        """Return policy telemetry for logging."""
        return {
            "rsa_policy_enabled": True,
            "rsa_policy_model": self._policy.model.value,
            "rsa_target_commitment": self._config.target_commitment,
            "rsa_timing_offset": self._config.timing_offset_epochs,
            "rsa_timing_period": self._config.timing_period_epochs,
            "rsa_epoch_size": self._config.epoch_size,
        }


# ============================================================================
# v2.0 Adaptive Adversary Wrapper (for harness integration)
# ============================================================================

class AdaptiveRSAWrapper:
    """
    Wrapper for v2.0 adaptive adversaries with observable interface.

    This wrapper:
    1. Samples observable outcomes at epoch start
    2. Updates adversary state based on observables
    3. Intercepts action proposals via adversary select_action()
    4. Maintains telemetry for adaptive behavior tracking

    Usage:
        wrapper = AdaptiveRSAWrapper.from_config(policy_config)
        if wrapper is not None:
            observable = wrapper.sample_observable(kernel_state)
            wrapper.update_state(observable)
            action = wrapper.intercept(observable, epoch, cycle_in_epoch)
    """

    def __init__(self, adversary: AdaptiveRSAAdversary, config: RSAPolicyConfig):
        self._adversary = adversary
        self._config = config

    @classmethod
    def from_config(cls, config: Optional[RSAPolicyConfig]) -> Optional["AdaptiveRSAWrapper"]:
        """
        Create wrapper from config, or None if policy is NONE/disabled.

        Args:
            config: Policy configuration

        Returns:
            AdaptiveRSAWrapper if v2.0 policy is active, None otherwise
        """
        if config is None:
            return None

        if config.rsa_version != "v2":
            return None

        adversary = create_adaptive_adversary(config.policy_model, config)
        if adversary is None:
            return None

        return cls(adversary, config)

    @property
    def model(self) -> RSAPolicyModel:
        """Return active adversary model."""
        return self._adversary.model

    def sample_observable(self, kernel_state: Dict[str, Any]) -> ObservableOutcome:
        """
        Sample observable outcome from kernel state (FROZEN SPEC).

        This is the v2.0 interface boundary: extract only the 6 observables
        from kernel state without exposing internal semantics.

        Args:
            kernel_state: Current kernel state dict

        Returns:
            ObservableOutcome with 6 frozen observables
        """
        # Extract observables from kernel state
        # This mapping respects architectural separation

        # Observable 1: epoch_index
        epoch_index = kernel_state.get("epoch_index", 0)

        # Observable 2: authority_status
        authority = kernel_state.get("authority", None)
        if authority is None or authority == "NULL":
            authority_status = AuthorityStatus.NULL_AUTHORITY
        else:
            authority_status = AuthorityStatus.HAS_AUTHORITY

        # Observable 3: lapse_occurred
        lapse_occurred = kernel_state.get("lapse_occurred_last_epoch", False)

        # Observable 4: renewal_outcome (never None, use NOT_ATTEMPTED)
        last_renewal_result = kernel_state.get("last_renewal_result", None)
        if last_renewal_result is None:
            renewal_outcome = RenewalOutcome.NOT_ATTEMPTED
        elif last_renewal_result:
            renewal_outcome = RenewalOutcome.SUCCEEDED
        else:
            renewal_outcome = RenewalOutcome.FAILED

        # Observable 5: cta_phase (including INACTIVE)
        cta_active = kernel_state.get("cta_active", False)
        cta_index = kernel_state.get("cta_current_index", 0)
        cta_length = kernel_state.get("cta_length", 1)
        cta_phase = compute_cta_bucket(cta_active, cta_index, cta_length)

        # Observable 6: eligibility_bucket
        successive_failures = kernel_state.get("successive_renewal_failures", 0)
        eligibility_bucket = compute_eligibility_bucket(successive_failures)

        return ObservableOutcome(
            epoch_index=epoch_index,
            authority_status=authority_status,
            lapse_occurred=lapse_occurred,
            renewal_outcome=renewal_outcome,
            cta_phase=cta_phase,
            eligibility_bucket=eligibility_bucket
        )

    def update_state(self, observable: ObservableOutcome) -> None:
        """
        Update adversary internal state based on observable.

        Called at the start of each epoch after sampling observable.

        Args:
            observable: Current observable outcome
        """
        self._adversary.update_state(observable)

    def intercept(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        original_action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intercept action proposal and return adversarial action.

        Args:
            observable: Current observable outcome
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            original_action: Original agent action (ignored, kept for telemetry)

        Returns:
            Adversarial action from adaptive adversary
        """
        return self._adversary.emit(observable, epoch, cycle_in_epoch, self._config)

    def get_state(self) -> int:
        """Get current adversary internal state."""
        return self._adversary.get_state()

    def get_telemetry(self) -> Dict[str, Any]:
        """Return adversary telemetry for logging."""
        return {
            "rsa_policy_enabled": True,
            "rsa_version": "v2",
            "rsa_policy_model": self._adversary.model.value,
            "rsa_internal_state": self._adversary.get_state(),
            "rsa_invalid_target_key": self._config.rsa_invalid_target_key,
            "rsa_max_internal_states": self._config.rsa_max_internal_states,
            "rsa_epoch_size": self._config.epoch_size,
        }
