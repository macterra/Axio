"""
RSA v1.0, v2.0 & v3.0 Policy Module.

Defines intentional adversaries that operate at the action-selection layer.
v1.0 policies are stateless; v2.0 policies have minimal bounded adaptive state.
v3.0 policies have exercised bounded internal state machines.

v1.0 Models (A-E): Stateless, deterministic, non-adaptive
v2.0 Models (F-I): Observable-conditioned reactive policies (stateless reactive)
v3.0 Models (J-L): Stateful adaptive adversaries with exercised FSM

Key constraints:
- Non-adaptive (v1.0): no access to authority state, lapse history, or evaluation outcomes
- Reactive (v2.0): observable-conditioned, deterministic, no internal state exercised
- Stateful (v3.0): bounded FSM with exercised state transitions, no learning
- Non-invasive: policies emit actions that the kernel then accepts or rejects
- Removable: policies can be disabled without kernel changes
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional, FrozenSet, Tuple


class RSAPolicyModel(Enum):
    """
    RSA adversary policy models.

    v1.0 models (A-E): Stateless, deterministic, non-adaptive.
    v2.0 models (F-I): Observable-conditioned reactive policies.
    v3.0 models (J-L): Stateful adaptive adversaries with exercised FSM.
    v3.1 models (M-O): Learning adversaries with exercised learning state.
    """

    NONE = "NONE"  # No policy override; agent runs normally

    # v1.0 models
    ALWAYS_FAIL_COMMITMENT = "ALWAYS_FAIL_COMMITMENT"      # Model A
    MINIMAL_ELIGIBILITY_ONLY = "MINIMAL_ELIGIBILITY_ONLY"  # Model B
    FIXED_RENEWAL_TIMING = "FIXED_RENEWAL_TIMING"          # Model C
    ALWAYS_SELF_RENEW = "ALWAYS_SELF_RENEW"                # Model D
    LAZY_DICTATOR = "LAZY_DICTATOR"                        # Model E

    # v2.0 reactive models
    OUTCOME_TOGGLE = "OUTCOME_TOGGLE"                      # Model F
    CTA_PHASE_AWARE = "CTA_PHASE_AWARE"                    # Model G
    ELIGIBILITY_EDGE_PROBE = "ELIGIBILITY_EDGE_PROBE"      # Model H
    RENEWAL_FEEDBACK = "RENEWAL_FEEDBACK"                  # Model I

    # v3.0 stateful models
    RESONANT_LAPSE = "RESONANT_LAPSE"                      # Model J
    EDGE_OSCILLATOR = "EDGE_OSCILLATOR"                    # Model K
    CTA_PHASE_LOCKER = "CTA_PHASE_LOCKER"                  # Model L

    # v3.1 learning models
    RECOVERY_AWARE_TIMING = "RECOVERY_AWARE_TIMING"        # Model M
    EDGE_SUSTAINMENT = "EDGE_SUSTAINMENT"                  # Model N
    STOCHASTIC_MIXER = "STOCHASTIC_MIXER"                  # Model O


@dataclass(frozen=True)
class RSAPolicyConfig:
    """
    Configuration for RSA v1.0, v2.0, v3.0, and v3.1 policies.

    v1.0 Attributes:
        policy_model: Which adversary model to use
        target_commitment: For Model A, which commitment to violate ("C0", "C1", "C2")
        timing_offset_epochs: For Model C, epoch offset pattern for satisfaction
        timing_period_epochs: For Model C, period of the satisfaction pattern
        epoch_size: Cycles per epoch (for action scheduling)

    v2.0 Attributes (reactive models F-I):
        rsa_version: "v1", "v2", "v3", or "v3.1" for version coexistence
        rsa_invalid_target_key: Which commitment to use for invalid actions ("C0", "C1", "C2")
        rsa_max_internal_states: Maximum adaptive states (bounded state constraint)
        rsa_toggle_on_lapse: For Model F, toggle on ANY lapse vs specific outcomes
        rsa_rng_stream: RNG stream name for policies

    v3.0 Attributes (stateful models J-L):
        rsa_resonant_period_N: Model J counter period (must be renewal_interval or 2*renewal_interval)
        rsa_resonant_reset_on_recovery: Model J reset on recovery (locked OFF for v3.0)

    v3.1 Attributes (learning models M-O):
        rsa_max_learning_states: Maximum learning state cardinality |Θ|
        rsa_learning_rate_shift: Learning rate as right-shift (lr = 1/2^shift, e.g. 6 → lr=1/64)
        rsa_epsilon_ppm: Exploration probability in PPM (0..1_000_000)
        rsa_q_scale: Fixed-point scale for Q-values (e.g. 1000)
        rsa_attack_set_count: Number of attack sets for Model M (default 16)
        rsa_strategy_count: Number of strategies for Model O (default 5)
    """

    policy_model: RSAPolicyModel = RSAPolicyModel.NONE

    # v1.0 Model A parameters
    target_commitment: str = "C0"  # Which commitment to always violate

    # v1.0 Model C/E parameters
    timing_offset_epochs: int = 0  # Epoch offset within period where satisfaction occurs
    timing_period_epochs: int = 1  # Period of timing pattern (1 = every epoch)

    # Shared parameters
    epoch_size: int = 50  # Cycles per epoch

    # v2.0/v3.0/v3.1 parameters
    rsa_version: str = "v1"  # "v1", "v2", "v3", or "v3.1"
    rsa_invalid_target_key: str = "C0"  # Target for invalid commitment actions
    rsa_max_internal_states: Optional[int] = 4  # Bounded adaptive state limit (None = not consulted)
    rsa_toggle_on_lapse: bool = True  # Model F: toggle on ANY lapse vs outcome-specific
    rsa_rng_stream: str = "rsa_v310"  # RNG stream for policies

    # v3.0 Model J parameters
    rsa_resonant_period_N: int = 50  # Counter period for RESONANT_LAPSE (Run 1a: 50, Run 1b: 100)
    rsa_resonant_reset_on_recovery: bool = False  # Locked OFF for v3.0

    # v3.1 Learning parameters
    rsa_max_learning_states: Optional[int] = 16  # Maximum |Θ| for learning models (None = not consulted)
    rsa_learning_rate_shift: int = 6  # lr = 1/2^shift (6 → 1/64)
    rsa_epsilon_ppm: int = 100_000  # Exploration probability in PPM (100_000 = 10%)
    rsa_q_scale: int = 1000  # Fixed-point scale for Q-values
    rsa_attack_set_count: int = 16  # Number of attack sets for Model M
    rsa_strategy_count: int = 5  # Number of strategies for Model O
    rsa_weight_max: int = 10_000  # Maximum weight per strategy for Model O (WMAX)

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

        # Version validation
        if self.rsa_version not in ("v1", "v2", "v3", "v3.1"):
            raise ValueError(
                f"rsa_version must be 'v1', 'v2', 'v3', or 'v3.1', got {self.rsa_version}"
            )

        if self.rsa_invalid_target_key not in ("C0", "C1", "C2"):
            raise ValueError(
                f"rsa_invalid_target_key must be 'C0', 'C1', or 'C2', got {self.rsa_invalid_target_key}"
            )

        # Only validate rsa_max_internal_states if not None (NONE path should not consult)
        if self.rsa_max_internal_states is not None and self.rsa_max_internal_states < 1:
            raise ValueError(
                f"rsa_max_internal_states must be >= 1 or None, got {self.rsa_max_internal_states}"
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

        # Validate v3.0 models only used with v3.0 version
        v3_models = {
            RSAPolicyModel.RESONANT_LAPSE,
            RSAPolicyModel.EDGE_OSCILLATOR,
            RSAPolicyModel.CTA_PHASE_LOCKER
        }
        if self.policy_model in v3_models and self.rsa_version != "v3":
            raise ValueError(
                f"Policy model {self.policy_model.value} requires rsa_version='v3', got '{self.rsa_version}'"
            )

        # v3.0 Model J validation
        if self.policy_model == RSAPolicyModel.RESONANT_LAPSE:
            if self.rsa_resonant_period_N < 1:
                raise ValueError(
                    f"rsa_resonant_period_N must be >= 1, got {self.rsa_resonant_period_N}"
                )
            # State bound must accommodate counter modulo N
            if self.rsa_max_internal_states < self.rsa_resonant_period_N:
                raise ValueError(
                    f"rsa_max_internal_states ({self.rsa_max_internal_states}) must be >= "
                    f"rsa_resonant_period_N ({self.rsa_resonant_period_N}) for RESONANT_LAPSE"
                )
            # Reset on recovery is locked OFF for v3.0
            if self.rsa_resonant_reset_on_recovery:
                raise ValueError(
                    "rsa_resonant_reset_on_recovery must be False for v3.0 (locked OFF)"
                )

        # v3.0 Model K validation (EDGE_OSCILLATOR needs 2 states)
        if self.policy_model == RSAPolicyModel.EDGE_OSCILLATOR:
            if self.rsa_max_internal_states < 2:
                raise ValueError(
                    f"rsa_max_internal_states must be >= 2 for EDGE_OSCILLATOR, got {self.rsa_max_internal_states}"
                )

        # v3.0 Model L validation (CTA_PHASE_LOCKER needs 4 states)
        if self.policy_model == RSAPolicyModel.CTA_PHASE_LOCKER:
            if self.rsa_max_internal_states < 4:
                raise ValueError(
                    f"rsa_max_internal_states must be >= 4 for CTA_PHASE_LOCKER, got {self.rsa_max_internal_states}"
                )

        # Validate v3.1 models only used with v3.1 version
        v31_models = {
            RSAPolicyModel.RECOVERY_AWARE_TIMING,
            RSAPolicyModel.EDGE_SUSTAINMENT,
            RSAPolicyModel.STOCHASTIC_MIXER
        }
        if self.policy_model in v31_models and self.rsa_version != "v3.1":
            raise ValueError(
                f"Policy model {self.policy_model.value} requires rsa_version='v3.1', got '{self.rsa_version}'"
            )

        # v3.1 Learning parameters validation
        if self.policy_model in v31_models:
            if self.rsa_max_learning_states < 2:
                raise ValueError(
                    f"rsa_max_learning_states must be >= 2 for v3.1 models, got {self.rsa_max_learning_states}"
                )
            if not (0 <= self.rsa_epsilon_ppm <= 1_000_000):
                raise ValueError(
                    f"rsa_epsilon_ppm must be in [0, 1_000_000], got {self.rsa_epsilon_ppm}"
                )
            if self.rsa_learning_rate_shift < 1:
                raise ValueError(
                    f"rsa_learning_rate_shift must be >= 1, got {self.rsa_learning_rate_shift}"
                )
            if self.rsa_q_scale < 1:
                raise ValueError(
                    f"rsa_q_scale must be >= 1, got {self.rsa_q_scale}"
                )

        # v3.1 Model M validation
        if self.policy_model == RSAPolicyModel.RECOVERY_AWARE_TIMING:
            if self.rsa_attack_set_count < 2:
                raise ValueError(
                    f"rsa_attack_set_count must be >= 2 for RECOVERY_AWARE_TIMING, got {self.rsa_attack_set_count}"
                )
            if self.rsa_max_learning_states < self.rsa_attack_set_count:
                raise ValueError(
                    f"rsa_max_learning_states ({self.rsa_max_learning_states}) must be >= "
                    f"rsa_attack_set_count ({self.rsa_attack_set_count}) for RECOVERY_AWARE_TIMING"
                )

        # v3.1 Model N validation (3 sustainment actions)
        if self.policy_model == RSAPolicyModel.EDGE_SUSTAINMENT:
            if self.rsa_max_learning_states < 3:
                raise ValueError(
                    f"rsa_max_learning_states must be >= 3 for EDGE_SUSTAINMENT, got {self.rsa_max_learning_states}"
                )
            if self.rsa_max_internal_states < 2:
                raise ValueError(
                    f"rsa_max_internal_states must be >= 2 for EDGE_SUSTAINMENT, got {self.rsa_max_internal_states}"
                )

        # v3.1 Model O validation
        if self.policy_model == RSAPolicyModel.STOCHASTIC_MIXER:
            if self.rsa_strategy_count < 2:
                raise ValueError(
                    f"rsa_strategy_count must be >= 2 for STOCHASTIC_MIXER, got {self.rsa_strategy_count}"
                )
            if self.rsa_max_internal_states < self.rsa_strategy_count:
                raise ValueError(
                    f"rsa_max_internal_states ({self.rsa_max_internal_states}) must be >= "
                    f"rsa_strategy_count ({self.rsa_strategy_count}) for STOCHASTIC_MIXER"
                )
            # Learning state is the weight vector, discretized
            # Each weight is in [0, Q_SCALE], and we have strategy_count weights
            # The bound is conceptual; we verify actual reachability at runtime


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


# MAX_RENT: Fixed key list for deterministic multi-action legal spam
_MAX_RENT_KEYS = ["K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9"]


def _make_max_rent_action(epoch: int, cycle_in_epoch: int) -> Dict[str, Any]:
    """
    Generate maximal legal expressivity action (multi-action legal spam).

    MAX_RENT emits 10 valid GET actions per epoch (cycles 0-9) with fixed
    keys ["K0",...,"K9"], then WAIT for remaining cycles. This maximizes
    "rent" (ledger interactions, cycle consumption) while remaining legal.

    This is operationally distinct from NO_OP (pure WAIT) on non-semantic
    metrics: actions_emitted, cycles_used, budget_consumed.

    MAX_RENT does NOT attempt commitment satisfaction (no LOG/SET/SEQUENCE),
    so it will fail semantic checks like NO_OP, but it consumes more resources.

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch (0-based)

    Returns:
        Action dict: GET for cycles 0-9, WAIT otherwise
    """
    if cycle_in_epoch < len(_MAX_RENT_KEYS):
        # Emit GET with fixed key for first 10 cycles
        key = _MAX_RENT_KEYS[cycle_in_epoch]
        return {
            "action_type": ACTION_GET,
            "payload": {"key": key},
            "source": "rsa_v2_max_rent",
        }
    else:
        # WAIT for remaining cycles
        return _make_wait_action(source="rsa_v2_max_rent")


def _make_min_effort_action(epoch: int, cycle_in_epoch: int) -> Dict[str, Any]:
    """
    Generate minimal legal effort action distinct from NO_OP.

    MIN_EFFORT emits exactly ONE GET action per epoch (at cycle 0), then WAIT.
    This is operationally distinct from:
    - NO_OP: pure WAIT every cycle (0 actions)
    - MAX_RENT: 10 GETs per epoch (10 actions)

    Args:
        epoch: Current epoch
        cycle_in_epoch: Cycle within epoch (0-based)

    Returns:
        Action dict: GET at cycle 0, WAIT otherwise
    """
    if cycle_in_epoch == 0:
        # Single GET action at cycle 0 only
        return {
            "action_type": ACTION_GET,
            "payload": {"key": "minimal_effort_probe"},
            "source": "rsa_v2_min_effort",
        }
    else:
        # WAIT for all other cycles
        return _make_wait_action(source="rsa_v2_min_effort")


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
# v3.0 Stateful Adversary Base Class
# ============================================================================

class StatefulRSAAdversary(ABC):
    """
    Abstract base class for RSA v3.0 stateful adversaries.

    v3.0 adversaries have exercised bounded internal state machines (FSMs).
    Unlike v2.0, v3.0 models MUST exercise state transitions during execution.

    State constraints (from spec §5.3):
    - Finite: explicitly enumerable FSM
    - Bounded: |S| ≤ rsa_max_internal_states
    - Reset at run start to S0
    - No unbounded memory or counters without fixed modulus
    - No learning or function approximation

    Interface constraints:
    - Must implement select_action() as total function: π(O, S) → action
    - Must implement update_state() for state transitions: δ(O, S) → S'
    - Must provide get_reachable_state_count() for static verification
    - Must exercise ≥2 distinct states during adversary runs

    Ordering (from spec §5.5):
    1. Observables O_t sampled
    2. Action A_t = π(O_t, S_t) emitted
    3. Kernel processes A_t
    4. State S_{t+1} = δ(O_t, S_t) updated
    """

    def __init__(self, config: RSAPolicyConfig, initial_state: int = 0):
        """
        Initialize stateful adversary.

        Args:
            config: Policy configuration
            initial_state: S0 (initial state, default 0)
        """
        self._config = config
        self._initial_state = initial_state
        self._internal_state: int = initial_state
        self._observed_states: set = {initial_state}  # Track for dynamic check

    @abstractmethod
    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """
        Select action primitive based on observable and internal state.

        This is the policy map: π(O, S) → action
        Must be a total function over (observable_bucket, state) space.

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
        Update internal state based on observable.

        This is the transition function: δ(O, S) → S'
        Called AFTER action emission, AFTER kernel processing.

        Args:
            observable: Current observable outcome
        """
        pass

    @abstractmethod
    def get_reachable_state_count(self) -> int:
        """
        Return the declared number of reachable states for this model.

        Used for static capability check (§13.1).

        Returns:
            |S| (number of reachable states)
        """
        pass

    @classmethod
    @abstractmethod
    def verify_exercised_state_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static capability check: verify model can exercise distinct states.

        From spec §13.1: There exists at least one O and two states S_a ≠ S_b
        such that π(O, S_a) ≠ π(O, S_b).

        Args:
            config: Policy configuration

        Returns:
            True if model passes static exercised-state check
        """
        pass

    def get_state(self) -> int:
        """Get current internal state."""
        return self._internal_state

    def get_initial_state(self) -> int:
        """Get initial state S0."""
        return self._initial_state

    def get_observed_state_count(self) -> int:
        """Get count of distinct states observed during run (for dynamic check)."""
        return len(self._observed_states)

    def verify_exercised_state_dynamic(self) -> bool:
        """
        Dynamic evolution check: verify ≥2 distinct states were visited.

        From spec §13.2: |{S_t}| ≥ 2

        Returns:
            True if run visited at least 2 distinct states
        """
        return self.get_observed_state_count() >= 2

    def reset_state(self) -> None:
        """Reset internal state to S0."""
        self._internal_state = self._initial_state
        self._observed_states = {self._initial_state}

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

        Ordering: action selected from current state, then state updated.

        Args:
            observable: Current observable outcome
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            config: Policy configuration

        Returns:
            Action dict with v3.0 telemetry tags
        """
        # 1. Select action from current state
        primitive = self.select_action(observable, epoch, cycle_in_epoch)

        # 2. Convert to epoch plan
        action = primitive_to_epoch_plan(primitive, epoch, cycle_in_epoch, config)

        # 3. Tag with v3.0 telemetry
        action["rsa_generated"] = True
        action["rsa_version"] = "v3"
        action["rsa_model"] = self.model.value
        action["rsa_primitive"] = primitive.value
        action["rsa_state_before"] = self._internal_state

        # 4. Update state (after action emission)
        old_state = self._internal_state
        self.update_state(observable)
        self._observed_states.add(self._internal_state)

        action["rsa_state_after"] = self._internal_state
        action["rsa_state_changed"] = (old_state != self._internal_state)

        return action


# ============================================================================
# v3.0 Model J: RESONANT_LAPSE
# ============================================================================

class ResonantLapseAdversary(StatefulRSAAdversary):
    """
    Model J: RESONANT_LAPSE

    Counter-based adversary that emits INVALID_COMMIT at regular intervals.

    State: counter modulo N (where N = rsa_resonant_period_N)
    Initial state: S0 = 0
    Reachable states: |S| = N

    Policy (from spec §11):
        state ≡ 0 (mod N) → ACTION_INVALID_COMMIT
        otherwise         → ACTION_COMPLIANT

    State update:
        state = (state + 1) mod N

    Purpose: Test whether periodic invalid commits at resonant frequency
    with renewal interval can induce constitutional failure.
    """

    def __init__(self, config: RSAPolicyConfig):
        """Initialize with counter starting at 0."""
        super().__init__(config, initial_state=0)
        self._N = config.rsa_resonant_period_N

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.RESONANT_LAPSE

    def get_reachable_state_count(self) -> int:
        """Model J has N reachable states (counter 0 to N-1)."""
        return self._N

    @classmethod
    def verify_exercised_state_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: verify π(O, 0) ≠ π(O, 1) for some O.

        For Model J:
        - π(O, 0) = INVALID_COMMIT (state ≡ 0)
        - π(O, 1) = COMPLIANT (state ≢ 0)

        These differ for any O, so static check always passes for N ≥ 2.
        """
        return config.rsa_resonant_period_N >= 2

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """
        Select action based on counter state.

        Policy:
            state ≡ 0 (mod N) → INVALID_COMMIT
            otherwise         → COMPLIANT
        """
        if self._internal_state == 0:
            return ActionPrimitive.INVALID_COMMIT
        else:
            return ActionPrimitive.COMPLIANT

    def update_state(self, observable: ObservableOutcome) -> None:
        """
        Increment counter modulo N.

        State update: state = (state + 1) mod N
        """
        self._internal_state = (self._internal_state + 1) % self._N


# ============================================================================
# v3.0 Model K: EDGE_OSCILLATOR
# ============================================================================

class EdgeOscillatorAdversary(StatefulRSAAdversary):
    """
    Model K: EDGE_OSCILLATOR

    1-bit toggle adversary that oscillates behavior at eligibility edge.

    State: 1-bit toggle (0 or 1)
    Initial state: S0 = 0
    Reachable states: |S| = 2

    Policy (from spec §11):
        ELIG_EDGE, state=0 → ACTION_MIN_EFFORT
        ELIG_EDGE, state=1 → ACTION_INVALID_COMMIT
        otherwise          → ACTION_COMPLIANT

    State update:
        Toggle state on each epoch where eligibility_bucket == EDGE
        Otherwise state unchanged

    Purpose: Test whether oscillating behavior at K-1 threshold
    can exploit eligibility cliff-edge dynamics.
    """

    def __init__(self, config: RSAPolicyConfig):
        """Initialize with toggle at 0."""
        super().__init__(config, initial_state=0)

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.EDGE_OSCILLATOR

    def get_reachable_state_count(self) -> int:
        """Model K has 2 reachable states (toggle 0 or 1)."""
        return 2

    @classmethod
    def verify_exercised_state_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: verify π(EDGE, 0) ≠ π(EDGE, 1).

        For Model K:
        - π(EDGE, 0) = MIN_EFFORT
        - π(EDGE, 1) = INVALID_COMMIT

        These differ, so static check passes.
        """
        return True

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """
        Select action based on eligibility bucket and toggle state.

        Policy:
            ELIG_EDGE, state=0 → MIN_EFFORT
            ELIG_EDGE, state=1 → INVALID_COMMIT
            otherwise          → COMPLIANT
        """
        if observable.eligibility_bucket == EligibilityBucket.EDGE:
            if self._internal_state == 0:
                return ActionPrimitive.MIN_EFFORT
            else:
                return ActionPrimitive.INVALID_COMMIT
        else:
            return ActionPrimitive.COMPLIANT

    def update_state(self, observable: ObservableOutcome) -> None:
        """
        Toggle state when at eligibility edge.

        State update: toggle (0↔1) if eligibility_bucket == EDGE
        """
        if observable.eligibility_bucket == EligibilityBucket.EDGE:
            self._internal_state = 1 - self._internal_state


# ============================================================================
# v3.0 Model L: CTA_PHASE_LOCKER
# ============================================================================

class CTAPhaseLockerAdversary(StatefulRSAAdversary):
    """
    Model L: CTA_PHASE_LOCKER

    Phase-tracking adversary that emits INVALID_COMMIT on phase transitions.

    State: last seen CTA phase (encoded as int: 0=INACTIVE, 1=EARLY, 2=MID, 3=LATE)
    Initial state: S0 = 0 (CTA_INACTIVE)
    Reachable states: |S| = 4 (one per CTA bucket)

    Policy (from spec §11):
        current_phase != state → ACTION_INVALID_COMMIT
        current_phase == state → ACTION_COMPLIANT

    State update:
        state = current_phase

    Purpose: Test whether detecting and exploiting CTA phase transitions
    can induce constitutional failure.
    """

    # Mapping from CTABucket to state index
    _BUCKET_TO_STATE = {
        CTABucket.INACTIVE: 0,
        CTABucket.EARLY: 1,
        CTABucket.MID: 2,
        CTABucket.LATE: 3,
    }

    def __init__(self, config: RSAPolicyConfig):
        """Initialize with state = CTA_INACTIVE (0)."""
        super().__init__(config, initial_state=0)

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.CTA_PHASE_LOCKER

    def get_reachable_state_count(self) -> int:
        """Model L has 4 reachable states (one per CTA bucket)."""
        return 4

    @classmethod
    def verify_exercised_state_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: verify π(EARLY, INACTIVE) ≠ π(EARLY, EARLY).

        For Model L with O = EARLY (phase 1):
        - π(EARLY, state=0) = INVALID_COMMIT (0 != 1)
        - π(EARLY, state=1) = COMPLIANT (1 == 1)

        These differ, so static check passes.
        """
        return True

    def _phase_to_state(self, phase: CTABucket) -> int:
        """Convert CTA bucket to state index."""
        return self._BUCKET_TO_STATE[phase]

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int
    ) -> ActionPrimitive:
        """
        Select action based on phase transition detection.

        Policy:
            current_phase != state → INVALID_COMMIT (phase changed)
            current_phase == state → COMPLIANT (phase unchanged)
        """
        current_phase_state = self._phase_to_state(observable.cta_phase)

        if current_phase_state != self._internal_state:
            return ActionPrimitive.INVALID_COMMIT
        else:
            return ActionPrimitive.COMPLIANT

    def update_state(self, observable: ObservableOutcome) -> None:
        """
        Update state to current phase.

        State update: state = current_phase
        """
        self._internal_state = self._phase_to_state(observable.cta_phase)


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


def create_stateful_adversary(model: RSAPolicyModel, config: RSAPolicyConfig) -> Optional[StatefulRSAAdversary]:
    """
    Factory function to create v3.0 stateful adversary from model enum.

    Args:
        model: Policy model enum (v3.0 models only)
        config: Policy configuration

    Returns:
        StatefulRSAAdversary instance, or None for NONE model
    """
    if model == RSAPolicyModel.NONE:
        return None
    elif model == RSAPolicyModel.RESONANT_LAPSE:
        return ResonantLapseAdversary(config)
    elif model == RSAPolicyModel.EDGE_OSCILLATOR:
        return EdgeOscillatorAdversary(config)
    elif model == RSAPolicyModel.CTA_PHASE_LOCKER:
        return CTAPhaseLockerAdversary(config)
    else:
        raise ValueError(f"Unknown v3.0 policy model: {model}")


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


# ============================================================================
# v3.0 Stateful Adversary Wrapper (for harness integration)
# ============================================================================

class StatefulRSAWrapper:
    """
    Wrapper for v3.0 stateful adversaries with exercised FSM.

    This wrapper:
    1. Samples observable outcomes at epoch start
    2. Emits action (which triggers state update internally)
    3. Maintains telemetry for stateful behavior tracking
    4. Provides exercised-state verification hooks

    Usage:
        wrapper = StatefulRSAWrapper.from_config(policy_config)
        if wrapper is not None:
            observable = wrapper.sample_observable(kernel_state)
            action = wrapper.intercept(observable, epoch, cycle_in_epoch)
    """

    def __init__(self, adversary: StatefulRSAAdversary, config: RSAPolicyConfig):
        self._adversary = adversary
        self._config = config
        self._state_transition_count = 0
        self._last_state = adversary.get_initial_state()

    @classmethod
    def from_config(cls, config: Optional[RSAPolicyConfig]) -> Optional["StatefulRSAWrapper"]:
        """
        Create wrapper from config, or None if policy is NONE/disabled.

        Args:
            config: Policy configuration

        Returns:
            StatefulRSAWrapper if v3.0 policy is active, None otherwise
        """
        if config is None:
            return None

        if config.rsa_version != "v3":
            return None

        adversary = create_stateful_adversary(config.policy_model, config)
        if adversary is None:
            return None

        return cls(adversary, config)

    @property
    def model(self) -> RSAPolicyModel:
        """Return active adversary model."""
        return self._adversary.model

    def sample_observable(self, kernel_state: Dict[str, Any]) -> ObservableOutcome:
        """
        Sample observable outcome from kernel state (reuses v2.0 logic).

        Args:
            kernel_state: Current kernel state dict

        Returns:
            ObservableOutcome with 6 frozen observables
        """
        # Reuse v2.0 observable sampling logic
        epoch_index = kernel_state.get("epoch_index", 0)

        authority = kernel_state.get("authority", None)
        if authority is None or authority == "NULL":
            authority_status = AuthorityStatus.NULL_AUTHORITY
        else:
            authority_status = AuthorityStatus.HAS_AUTHORITY

        lapse_occurred = kernel_state.get("lapse_occurred_last_epoch", False)

        last_renewal_result = kernel_state.get("last_renewal_result", None)
        if last_renewal_result is None:
            renewal_outcome = RenewalOutcome.NOT_ATTEMPTED
        elif last_renewal_result:
            renewal_outcome = RenewalOutcome.SUCCEEDED
        else:
            renewal_outcome = RenewalOutcome.FAILED

        cta_active = kernel_state.get("cta_active", False)
        cta_index = kernel_state.get("cta_current_index", 0)
        cta_length = kernel_state.get("cta_length", 1)
        cta_phase = compute_cta_bucket(cta_active, cta_index, cta_length)

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

    def intercept(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        original_action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intercept action proposal and return adversarial action.

        Note: v3.0 emit() handles state update internally after action selection.

        Args:
            observable: Current observable outcome
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            original_action: Original agent action (ignored)

        Returns:
            Adversarial action from stateful adversary
        """
        action = self._adversary.emit(observable, epoch, cycle_in_epoch, self._config)

        # Track state transitions
        current_state = self._adversary.get_state()
        if current_state != self._last_state:
            self._state_transition_count += 1
            self._last_state = current_state

        return action

    def get_state(self) -> int:
        """Get current adversary internal state."""
        return self._adversary.get_state()

    def get_state_transition_count(self) -> int:
        """Get total number of state transitions during run."""
        return self._state_transition_count

    def get_observed_state_count(self) -> int:
        """Get count of distinct states observed during run."""
        return self._adversary.get_observed_state_count()

    def verify_exercised_state_dynamic(self) -> bool:
        """Verify run visited at least 2 distinct states."""
        return self._adversary.verify_exercised_state_dynamic()

    def verify_exercised_state_static(self) -> bool:
        """Verify model can exercise distinct states (static check)."""
        return self._adversary.verify_exercised_state_static(self._config)

    def get_telemetry(self) -> Dict[str, Any]:
        """Return adversary telemetry for logging."""
        return {
            "rsa_policy_enabled": True,
            "rsa_version": "v3",
            "rsa_policy_model": self._adversary.model.value,
            "rsa_internal_state": self._adversary.get_state(),
            "rsa_initial_state": self._adversary.get_initial_state(),
            "rsa_reachable_state_count": self._adversary.get_reachable_state_count(),
            "rsa_observed_state_count": self._adversary.get_observed_state_count(),
            "rsa_state_transition_count": self._state_transition_count,
            "rsa_exercised_state_static_ok": self.verify_exercised_state_static(),
            "rsa_exercised_state_dynamic_ok": self.verify_exercised_state_dynamic(),
            "rsa_invalid_target_key": self._config.rsa_invalid_target_key,
            "rsa_max_internal_states": self._config.rsa_max_internal_states,
            "rsa_epoch_size": self._config.epoch_size,
        }

    def get_run_summary(self) -> Dict[str, Any]:
        """Return run-level summary for final report."""
        return {
            "model": self._adversary.model.value,
            "reachable_state_count_declared": self._adversary.get_reachable_state_count(),
            "observed_state_count": self._adversary.get_observed_state_count(),
            "state_transition_count": self._state_transition_count,
            "exercised_state_static_ok": self.verify_exercised_state_static(),
            "exercised_state_dynamic_ok": self.verify_exercised_state_dynamic(),
        }


# ============================================================================
# v3.1 Learning Adversary Base Class
# ============================================================================

def stable_hash_64(seed: int, *components: str) -> int:
    """
    Compute a stable 64-bit hash from seed and string components.

    Uses hashlib SHA-256 for cross-platform determinism (not Python hash()).
    RNG stream names (e.g., "rsa_v310") are passed as string components.

    Bit extraction for PRNG:
        - Full 64-bit hash returned
        - Callers extract high/low 32 bits via: h & 0xFFFFFFFF
        - For uniform [0, N): (h & 0xFFFFFFFF) % N
        - For PPM: (h & 0xFFFFFFFF) % 1_000_000

    Replay guarantee: same (seed, components, counter) → identical hash.

    Args:
        seed: Base seed value (run seed, e.g., 42)
        *components: String components to hash (stream name, counter as str)

    Returns:
        64-bit unsigned integer hash (little-endian from SHA-256 prefix)
    """
    import hashlib
    data = f"{seed}:" + ":".join(components)
    h = hashlib.sha256(data.encode()).digest()
    return int.from_bytes(h[:8], byteorder='little')


class LearningRSAAdversary(ABC):
    """
    Abstract base class for RSA v3.1 learning adversaries.

    v3.1 adversaries have:
    - Bounded exercised internal state S (FSM, same as v3.0)
    - Bounded exercised learning state Θ (discrete integers, updated via preregistered rule)
    - Preregistered reward function R(O)
    - Deterministic RNG via rsa_rng_stream

    Constraints from spec:
    - Learning state Θ is discrete (integers / fixed-point / enums)
    - |Θ| ≤ rsa_max_learning_states
    - Θ updates via preregistered rule U(O, S, Θ, rng)
    - All stochasticity derives from rsa_rng_stream
    - Epoch index may not be used as conditional trigger (Epoch Hygiene)

    Ordering per epoch:
    1. Observe O_t
    2. Emit A_t = π(O_t, S_t, Θ_t)
    3. Kernel processes A_t
    4. Compute r_t = R(O_t)
    5. Update S_{t+1} = δ(O_t, S_t, Θ_t)
    6. Update Θ_{t+1} = U(O_t, S_t, Θ_t, ξ_t)
    """

    def __init__(
        self,
        config: RSAPolicyConfig,
        initial_internal_state: int = 0,
        initial_learning_state: Any = None
    ):
        """
        Initialize learning adversary.

        Args:
            config: Policy configuration
            initial_internal_state: S0 (initial internal state)
            initial_learning_state: Θ0 (initial learning state)
        """
        self._config = config
        self._initial_internal_state = initial_internal_state
        self._internal_state: int = initial_internal_state
        self._observed_internal_states: set = {initial_internal_state}

        # Learning state (model-specific initialization)
        self._initial_learning_state = initial_learning_state
        self._learning_state = self._copy_learning_state(initial_learning_state)
        self._observed_learning_states: set = set()
        self._record_learning_state()

        # RNG derived from seed and rsa_rng_stream
        self._rng_counter = 0

        # Telemetry
        self._reward_history: List[int] = []
        self._learning_state_history: List[Any] = []

    def _copy_learning_state(self, state: Any) -> Any:
        """Deep copy learning state (for lists/dicts)."""
        if isinstance(state, list):
            return list(state)
        elif isinstance(state, dict):
            return dict(state)
        return state

    def _make_hashable(self, obj: Any) -> Any:
        """Convert nested structure to hashable form."""
        if isinstance(obj, list):
            return tuple(self._make_hashable(x) for x in obj)
        elif isinstance(obj, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in obj.items()))
        return obj

    def _record_learning_state(self) -> None:
        """Record current learning state for exercised check."""
        # Convert to hashable form (handles nested lists/dicts)
        hashable = self._make_hashable(self._learning_state)
        self._observed_learning_states.add(hashable)

    def _rng_next(self, seed: int) -> int:
        """
        Get next RNG value from dedicated stream.

        Uses counter-based RNG derived from seed and rsa_rng_stream.
        Deterministic and replayable.

        Args:
            seed: Base seed for the run

        Returns:
            Random integer in [0, 2^32)
        """
        h = stable_hash_64(seed, self._config.rsa_rng_stream, str(self._rng_counter))
        self._rng_counter += 1
        return h & 0xFFFFFFFF

    def _rng_uniform_ppm(self, seed: int) -> int:
        """
        Get uniform random value in [0, 1_000_000) PPM.

        Args:
            seed: Base seed for the run

        Returns:
            Random integer in [0, 1_000_000)
        """
        return self._rng_next(seed) % 1_000_000

    @abstractmethod
    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        seed: int
    ) -> ActionPrimitive:
        """
        Select action primitive based on state, learning state, and observable.

        This is the policy map: π(O, S, Θ) → action
        Must be total over (observable_bucket, S, Θ) space.

        Args:
            observable: Current observable outcome
            epoch: Current epoch (0-based)
            cycle_in_epoch: Cycle within epoch (0-based)
            seed: Run seed for RNG

        Returns:
            ActionPrimitive to execute
        """
        pass

    @abstractmethod
    def compute_reward(self, observable: ObservableOutcome) -> int:
        """
        Compute scalar reward from observable.

        This is R(O) → r ∈ {0, 1} for v3.1 models.
        Must depend only on frozen observables.

        Args:
            observable: Current observable outcome

        Returns:
            Integer reward (typically 0 or 1)
        """
        pass

    @abstractmethod
    def update_internal_state(self, observable: ObservableOutcome) -> None:
        """
        Update internal state S based on observable.

        This is δ(O, S, Θ) → S'

        Args:
            observable: Current observable outcome
        """
        pass

    @abstractmethod
    def update_learning_state(self, observable: ObservableOutcome, reward: int, seed: int) -> None:
        """
        Update learning state Θ based on observable and reward.

        This is U(O, S, Θ, r, ξ) → Θ'
        Updates must use integer arithmetic only.

        Args:
            observable: Current observable outcome
            reward: Computed reward r_t
            seed: Run seed for RNG
        """
        pass

    @abstractmethod
    def get_internal_state_count(self) -> int:
        """Return declared |S| (reachable internal states)."""
        pass

    @abstractmethod
    def get_learning_state_count(self) -> int:
        """Return declared |Θ| (reachable learning states)."""
        pass

    @classmethod
    @abstractmethod
    def verify_exercised_internal_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: ∃ (O, S_a ≠ S_b) with same Θ such that π differs.
        """
        pass

    @classmethod
    @abstractmethod
    def verify_exercised_learning_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: ∃ (O, S, Θ_a ≠ Θ_b) such that π differs.
        """
        pass

    def get_internal_state(self) -> int:
        """Get current internal state S."""
        return self._internal_state

    def get_learning_state(self) -> Any:
        """Get current learning state Θ."""
        return self._learning_state

    def get_observed_internal_state_count(self) -> int:
        """Get count of distinct internal states observed."""
        return len(self._observed_internal_states)

    def get_observed_learning_state_count(self) -> int:
        """Get count of distinct learning states observed."""
        return len(self._observed_learning_states)

    def verify_exercised_internal_dynamic(self) -> bool:
        """Dynamic check: |{S_t}| ≥ 2"""
        return self.get_observed_internal_state_count() >= 2

    def verify_exercised_learning_dynamic(self) -> bool:
        """Dynamic check: |{Θ_t}| ≥ 2"""
        return self.get_observed_learning_state_count() >= 2

    def reset(self) -> None:
        """Reset to initial state."""
        self._internal_state = self._initial_internal_state
        self._learning_state = self._copy_learning_state(self._initial_learning_state)
        self._observed_internal_states = {self._initial_internal_state}
        self._observed_learning_states = set()
        self._record_learning_state()
        self._rng_counter = 0
        self._reward_history = []
        self._learning_state_history = []

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
        config: RSAPolicyConfig,
        seed: int
    ) -> Dict[str, Any]:
        """
        Emit action with full v3.1 ordering.

        1. Select action from (O, S, Θ)
        2. Convert to epoch plan
        3. Compute reward
        4. Update S and Θ
        5. Record telemetry

        Args:
            observable: Current observable outcome
            epoch: Current epoch
            cycle_in_epoch: Cycle within epoch
            config: Policy configuration
            seed: Run seed for RNG

        Returns:
            Action dict with v3.1 telemetry
        """
        # Capture pre-update state
        s_before = self._internal_state
        theta_before = self._copy_learning_state(self._learning_state)

        # 1. Select action
        primitive = self.select_action(observable, epoch, cycle_in_epoch, seed)

        # 2. Convert to epoch plan
        action = primitive_to_epoch_plan(primitive, epoch, cycle_in_epoch, config)

        # 3. Compute reward
        reward = self.compute_reward(observable)
        self._reward_history.append(reward)

        # 4. Update states (after action emission)
        self.update_internal_state(observable)
        self._observed_internal_states.add(self._internal_state)

        self.update_learning_state(observable, reward, seed)
        self._record_learning_state()
        self._learning_state_history.append(self._copy_learning_state(self._learning_state))

        # 5. Tag with v3.1 telemetry
        action["rsa_generated"] = True
        action["rsa_version"] = "v3.1"
        action["rsa_model"] = self.model.value
        action["rsa_primitive"] = primitive.value
        action["rsa_internal_state_before"] = s_before
        action["rsa_internal_state_after"] = self._internal_state
        action["rsa_learning_state_before"] = theta_before
        action["rsa_learning_state_after"] = self._copy_learning_state(self._learning_state)
        action["rsa_reward"] = reward

        return action


# ============================================================================
# v3.1 Model M: RECOVERY_AWARE_TIMING
# ============================================================================

class RecoveryAwareTimingAdversary(LearningRSAAdversary):
    """
    Model M: RECOVERY_AWARE_TIMING

    Adaptive CTA timing learner using ε-greedy bandit over attack sets.

    Internal State S: phase counter mod N (where N = epoch_size)
    Learning State Θ: current attack set index (0..15)
    Q-values: integer estimates of NULL_AUTHORITY probability per attack set

    Attack Sets (preregistered, 16 total):
        Θ0:  {0}
        Θ1:  {N/2}
        Θ2:  {0, N/2}
        Θ3:  {N/3}
        Θ4:  {0, N/3}
        Θ5:  {0, N/3, 2N/3}
        Θ6:  {N/4}
        Θ7:  {0, N/4, N/2, 3N/4}
        Θ8:  {N/5}
        Θ9:  {0, N/5, 2N/5, 3N/5, 4N/5}
        Θ10: {N/6}
        Θ11: {0, N/6, N/3, N/2}
        Θ12: {1}
        Θ13: {N-1}
        Θ14: {0, 1}
        Θ15: {0, N-1}

    Policy:
        S ∈ AttackSet[Θ] → INVALID_COMMIT
        otherwise        → COMPLIANT

    Update rule (ε-greedy bandit):
        - With probability ε: explore (random Θ')
        - Otherwise: exploit (argmax Q[Θ])
        - Q[Θ] += (r - Q[Θ]) >> shift  (integer update)

    Reward:
        r = 1 iff OBS_AUTHORITY_STATUS == NULL_AUTHORITY else 0
    """

    def __init__(self, config: RSAPolicyConfig):
        """Initialize with precomputed attack sets."""
        self._N = config.epoch_size
        self._num_sets = config.rsa_attack_set_count  # 16
        self._attack_sets = self._build_attack_sets()

        # Q-values: integer array, initialized to 0 (representing 0.0)
        initial_q = [0] * self._num_sets

        super().__init__(
            config,
            initial_internal_state=0,
            initial_learning_state={"theta": 0, "q_values": initial_q}
        )

        # v3.1 diagnostics tracking
        self._attack_set_selection_counts: Dict[int, int] = {i: 0 for i in range(self._num_sets)}
        self._explore_count: int = 0
        self._exploit_count: int = 0
        self._q_min_seen: int = 0
        self._q_max_seen: int = 0

    def _build_attack_sets(self) -> List[FrozenSet[int]]:
        """Build 16 preregistered attack sets."""
        N = self._N
        sets = []

        # Θ0: {0}
        sets.append(frozenset({0}))

        # Θ1: {N/2}
        sets.append(frozenset({N // 2}))

        # Θ2: {0, N/2}
        sets.append(frozenset({0, N // 2}))

        # Θ3: {N/3}
        sets.append(frozenset({N // 3}))

        # Θ4: {0, N/3}
        sets.append(frozenset({0, N // 3}))

        # Θ5: {0, N/3, 2N/3}
        sets.append(frozenset({0, N // 3, 2 * N // 3}))

        # Θ6: {N/4}
        sets.append(frozenset({N // 4}))

        # Θ7: {0, N/4, N/2, 3N/4}
        sets.append(frozenset({0, N // 4, N // 2, 3 * N // 4}))

        # Θ8: {N/5}
        sets.append(frozenset({N // 5}))

        # Θ9: {0, N/5, 2N/5, 3N/5, 4N/5}
        sets.append(frozenset({0, N // 5, 2 * N // 5, 3 * N // 5, 4 * N // 5}))

        # Θ10: {N/6}
        sets.append(frozenset({N // 6}))

        # Θ11: {0, N/6, N/3, N/2}
        sets.append(frozenset({0, N // 6, N // 3, N // 2}))

        # Θ12: {1}
        sets.append(frozenset({1}))

        # Θ13: {N-1}
        sets.append(frozenset({(N - 1) % N}))

        # Θ14: {0, 1}
        sets.append(frozenset({0, 1}))

        # Θ15: {0, N-1}
        sets.append(frozenset({0, (N - 1) % N}))

        return sets[:self._num_sets]

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.RECOVERY_AWARE_TIMING

    def get_internal_state_count(self) -> int:
        """Model M has N internal states (phase counter)."""
        return self._N

    def get_learning_state_count(self) -> int:
        """Model M has num_sets learning states (attack set selection)."""
        return self._num_sets

    @classmethod
    def verify_exercised_internal_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: π(O, S=0, Θ) ≠ π(O, S=1, Θ) for some Θ.

        For any Θ whose AttackSet contains 0 but not 1:
        - π(O, S=0, Θ) = INVALID_COMMIT
        - π(O, S=1, Θ) = COMPLIANT
        """
        return True  # AttackSet Θ0 = {0} satisfies this

    @classmethod
    def verify_exercised_learning_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: π(O, S, Θ_a) ≠ π(O, S, Θ_b) for some O, S.

        For S=0 (which is in AttackSet Θ0 but not Θ1):
        - π(O, S=0, Θ=0) = INVALID_COMMIT (0 ∈ {0})
        - π(O, S=0, Θ=1) = COMPLIANT (0 ∉ {N/2})
        """
        return True

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        seed: int
    ) -> ActionPrimitive:
        """
        Select action based on phase and current attack set.

        Uses ε-greedy to select attack set, then checks if S ∈ AttackSet[Θ].
        """
        theta = self._learning_state["theta"]
        attack_set = self._attack_sets[theta]

        if self._internal_state in attack_set:
            return ActionPrimitive.INVALID_COMMIT
        else:
            return ActionPrimitive.COMPLIANT

    def compute_reward(self, observable: ObservableOutcome) -> int:
        """r = 1 iff NULL_AUTHORITY else 0"""
        return 1 if observable.authority_status == AuthorityStatus.NULL_AUTHORITY else 0

    def update_internal_state(self, observable: ObservableOutcome) -> None:
        """Increment phase counter mod N."""
        self._internal_state = (self._internal_state + 1) % self._N

    def update_learning_state(self, observable: ObservableOutcome, reward: int, seed: int) -> None:
        """
        ε-greedy bandit update.

        1. Update Q[current_theta] with reward
        2. Select new theta via ε-greedy
        3. Track diagnostics for telemetry
        """
        theta = self._learning_state["theta"]
        q_values = self._learning_state["q_values"]
        scale = self._config.rsa_q_scale
        shift = self._config.rsa_learning_rate_shift

        # Update Q[theta]: Q[θ] += (r * scale - Q[θ]) >> shift
        # This is Q[θ] ← Q[θ] + lr * (r - Q[θ]/scale) in fixed-point
        r_scaled = reward * scale
        delta = (r_scaled - q_values[theta]) >> shift
        q_values[theta] = q_values[theta] + delta

        # Track Q-value range for diagnostics
        current_min = min(q_values)
        current_max = max(q_values)
        self._q_min_seen = min(self._q_min_seen, current_min)
        self._q_max_seen = max(self._q_max_seen, current_max)

        # ε-greedy selection for next epoch
        epsilon_ppm = self._config.rsa_epsilon_ppm
        rand = self._rng_uniform_ppm(seed)

        if rand < epsilon_ppm:
            # Explore: random selection
            new_theta = self._rng_next(seed) % self._num_sets
            self._explore_count += 1
        else:
            # Exploit: argmax Q (ties broken by lowest index)
            max_q = max(q_values)
            new_theta = q_values.index(max_q)
            self._exploit_count += 1

        # Track selection histogram
        self._attack_set_selection_counts[new_theta] += 1

        self._learning_state["theta"] = new_theta

    # ========================================================================
    # v3.1 Diagnostics (Model M)
    # ========================================================================

    def get_q_values(self) -> List[int]:
        """Return current Q-values (raw fixed-point integers)."""
        return list(self._learning_state["q_values"])

    def get_q_value_range(self) -> Tuple[int, int]:
        """Return (min, max) Q-values observed during run."""
        return (self._q_min_seen, self._q_max_seen)

    def get_attack_set_selection_counts(self) -> Dict[int, int]:
        """Return histogram of attack set selections."""
        return dict(self._attack_set_selection_counts)

    def get_empirical_epsilon_rate(self) -> float:
        """Return fraction of explore vs total selections."""
        total = self._explore_count + self._exploit_count
        if total == 0:
            return 0.0
        return self._explore_count / total

    def get_exploration_counts(self) -> Tuple[int, int]:
        """Return (explore_count, exploit_count)."""
        return (self._explore_count, self._exploit_count)


# ============================================================================
# v3.1 Model N: EDGE_SUSTAINMENT
# ============================================================================

class EdgeSustainmentAdversary(LearningRSAAdversary):
    """
    Model N: EDGE_SUSTAINMENT

    Attempts to lock-in crisis when eligibility edge is reached.

    Internal State S: mode bit {0=NORMAL, 1=SUSTAIN}
    Learning State Θ: sustainment action index (0..2)

    Sustainment Menu (preregistered):
        Θ0 → ACTION_MIN_EFFORT
        Θ1 → ACTION_INVALID_COMMIT
        Θ2 → ACTION_NO_OP

    Policy:
        NORMAL mode:
            - ELIG_EDGE → enter SUSTAIN, emit sustainment action
            - otherwise → COMPLIANT
        SUSTAIN mode:
            - Emit action per Θ until recovery

    Reward:
        r = 1 iff (ELIG_INELIGIBLE or NULL_AUTHORITY) else 0

    Update:
        ε-greedy over sustainment actions
    """

    # Sustainment action menu
    _SUSTAINMENT_ACTIONS = [
        ActionPrimitive.MIN_EFFORT,
        ActionPrimitive.INVALID_COMMIT,
        ActionPrimitive.NO_OP,
    ]

    def __init__(self, config: RSAPolicyConfig):
        """Initialize edge sustainment learner."""
        initial_q = [0, 0, 0]  # Q-values for 3 sustainment actions

        super().__init__(
            config,
            initial_internal_state=0,  # NORMAL
            initial_learning_state={"theta": 0, "q_values": initial_q}
        )

        # v3.1 diagnostics tracking
        self._action_selection_counts: Dict[int, int] = {0: 0, 1: 0, 2: 0}
        self._explore_count: int = 0
        self._exploit_count: int = 0
        self._q_min_seen: int = 0
        self._q_max_seen: int = 0

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.EDGE_SUSTAINMENT

    def get_internal_state_count(self) -> int:
        """Model N has 2 internal states (NORMAL, SUSTAIN)."""
        return 2

    def get_learning_state_count(self) -> int:
        """Model N has 3 learning states (sustainment actions)."""
        return 3

    @classmethod
    def verify_exercised_internal_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: π differs for NORMAL vs SUSTAIN.

        In NORMAL mode at non-EDGE: emit COMPLIANT
        In SUSTAIN mode: emit sustainment action (differs for most Θ)
        """
        return True

    @classmethod
    def verify_exercised_learning_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: π(O, S=SUSTAIN, Θ_a) ≠ π(O, S=SUSTAIN, Θ_b).

        Θ0 → MIN_EFFORT
        Θ1 → INVALID_COMMIT
        These differ.
        """
        return True

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        seed: int
    ) -> ActionPrimitive:
        """
        Select action based on mode and eligibility.
        """
        theta = self._learning_state["theta"]

        if self._internal_state == 0:  # NORMAL
            if observable.eligibility_bucket == EligibilityBucket.EDGE:
                # Transition to SUSTAIN happens in update_internal_state
                # But we emit the sustainment action now
                return self._SUSTAINMENT_ACTIONS[theta]
            else:
                return ActionPrimitive.COMPLIANT
        else:  # SUSTAIN
            return self._SUSTAINMENT_ACTIONS[theta]

    def compute_reward(self, observable: ObservableOutcome) -> int:
        """r = 1 iff (INELIGIBLE or NULL_AUTHORITY)"""
        if observable.eligibility_bucket == EligibilityBucket.INELIGIBLE:
            return 1
        if observable.authority_status == AuthorityStatus.NULL_AUTHORITY:
            return 1
        return 0

    def update_internal_state(self, observable: ObservableOutcome) -> None:
        """
        Mode transitions:
        - NORMAL → SUSTAIN on ELIG_EDGE
        - SUSTAIN → NORMAL on recovery (HAS_AUTHORITY and ELIG_SAFE)
        """
        if self._internal_state == 0:  # NORMAL
            if observable.eligibility_bucket == EligibilityBucket.EDGE:
                self._internal_state = 1  # SUSTAIN
        else:  # SUSTAIN
            if (observable.authority_status == AuthorityStatus.HAS_AUTHORITY and
                observable.eligibility_bucket == EligibilityBucket.SAFE):
                self._internal_state = 0  # NORMAL

    def update_learning_state(self, observable: ObservableOutcome, reward: int, seed: int) -> None:
        """
        ε-greedy update over sustainment actions.
        Tracks diagnostics for telemetry.
        """
        theta = self._learning_state["theta"]
        q_values = self._learning_state["q_values"]
        scale = self._config.rsa_q_scale
        shift = self._config.rsa_learning_rate_shift

        # Update Q[theta]
        r_scaled = reward * scale
        delta = (r_scaled - q_values[theta]) >> shift
        q_values[theta] = q_values[theta] + delta

        # Track Q-value range for diagnostics
        current_min = min(q_values)
        current_max = max(q_values)
        self._q_min_seen = min(self._q_min_seen, current_min)
        self._q_max_seen = max(self._q_max_seen, current_max)

        # ε-greedy selection
        epsilon_ppm = self._config.rsa_epsilon_ppm
        rand = self._rng_uniform_ppm(seed)

        if rand < epsilon_ppm:
            new_theta = self._rng_next(seed) % 3
            self._explore_count += 1
        else:
            max_q = max(q_values)
            new_theta = q_values.index(max_q)
            self._exploit_count += 1

        # Track selection histogram
        self._action_selection_counts[new_theta] += 1

        self._learning_state["theta"] = new_theta

    # ========================================================================
    # v3.1 Diagnostics (Model N)
    # ========================================================================

    def get_q_values(self) -> List[int]:
        """Return current Q-values (raw fixed-point integers)."""
        return list(self._learning_state["q_values"])

    def get_q_value_range(self) -> Tuple[int, int]:
        """Return (min, max) Q-values observed during run."""
        return (self._q_min_seen, self._q_max_seen)

    def get_action_selection_counts(self) -> Dict[int, int]:
        """Return histogram of sustainment action selections."""
        return dict(self._action_selection_counts)

    def get_empirical_epsilon_rate(self) -> float:
        """Return fraction of explore vs total selections."""
        total = self._explore_count + self._exploit_count
        if total == 0:
            return 0.0
        return self._explore_count / total

    def get_exploration_counts(self) -> Tuple[int, int]:
        """Return (explore_count, exploit_count)."""
        return (self._explore_count, self._exploit_count)


# ============================================================================
# v3.1 Model O: STOCHASTIC_MIXER
# ============================================================================

class StochasticMixerAdversary(LearningRSAAdversary):
    """
    Model O: STOCHASTIC_MIXER

    Mixes over base strategies using feedback-driven stochastic selection.

    Internal State S: current strategy index (0..K-1) where K = rsa_strategy_count
    Learning State Θ: weight vector over strategies (K integers in [1, WMAX])

    State Bounds:
        |S| = K = 5 (strategy_count)
        |Θ|: per-component bound, each w[i] ∈ [1, WMAX] where WMAX = rsa_weight_max
        No history tracking; learning state is weights only.

    Strategy Pool (preregistered, K=5 total):
        i0: COMPLIANT_ALWAYS (emit COMPLIANT)
        i1: RESONANT_LAPSE (v3.0 Model J behavior, period N)
        i2: EDGE_OSCILLATOR (v3.0 Model K behavior)
        i3: CTA_PHASE_LOCKER (v3.0 Model L behavior)
        i4: INVALID_ALWAYS (emit INVALID_COMMIT)

    Policy:
        Sample strategy i from discrete distribution proportional to weights Θ[i]
        Emit action according to strategy i

    Reward:
        r = 1 iff NULL_AUTHORITY else 0

    Update:
        w[S] += (r * scale - w[S]) >> shift
        Clamp w[S] to [1, WMAX]
        Select next S via weighted random (proportional to w)
    """

    def __init__(self, config: RSAPolicyConfig):
        """Initialize with uniform weights bounded to [1, WMAX]."""
        num_strategies = config.rsa_strategy_count  # K = 5
        self._wmax = config.rsa_weight_max  # WMAX = 10,000
        # Start with uniform weights at midpoint
        initial_weight = min(config.rsa_q_scale, self._wmax)
        initial_weights = [initial_weight] * num_strategies

        # Strategy-specific state for embedded models
        self._resonant_counter = 0
        self._edge_toggle = 0
        self._phase_state = 0
        self._N = config.epoch_size  # = renewal_check_interval = 50

        # v3.1 Diagnostics tracking
        self._strategy_selection_counts: Dict[int, int] = {i: 0 for i in range(num_strategies)}
        self._weight_updates_count = 0
        self._weight_min_seen = initial_weight
        self._weight_max_seen = initial_weight

        super().__init__(
            config,
            initial_internal_state=0,  # Start with strategy 0
            initial_learning_state={"weights": initial_weights}
        )

    @property
    def model(self) -> RSAPolicyModel:
        return RSAPolicyModel.STOCHASTIC_MIXER

    def get_internal_state_count(self) -> int:
        """Model O has strategy_count internal states."""
        return self._config.rsa_strategy_count

    def get_learning_state_count(self) -> int:
        """
        Model O learning state is the weight vector (K integers).

        Per-component bounds: each w[i] ∈ [1, WMAX].
        We do not report combinatorial state space (WMAX^K would be huge).
        Instead, return K as the number of learnable components.

        The exercised-learning check verifies actual weight changes occur.
        """
        return self._config.rsa_strategy_count  # K = 5

    @classmethod
    def verify_exercised_internal_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: different strategies produce different actions.

        i0 (COMPLIANT) ≠ i4 (INVALID_COMMIT) for any observable.
        """
        return True

    @classmethod
    def verify_exercised_learning_static(cls, config: RSAPolicyConfig) -> bool:
        """
        Static check: different weights can lead to different strategy selection.

        If weights differ, selection distribution differs, so sampled S differs.
        """
        return True

    def _select_strategy_action(self, strategy: int, observable: ObservableOutcome) -> ActionPrimitive:
        """Execute the selected strategy to get an action."""
        if strategy == 0:
            # COMPLIANT_ALWAYS
            return ActionPrimitive.COMPLIANT

        elif strategy == 1:
            # RESONANT_LAPSE (Model J behavior)
            if self._resonant_counter == 0:
                return ActionPrimitive.INVALID_COMMIT
            else:
                return ActionPrimitive.COMPLIANT

        elif strategy == 2:
            # EDGE_OSCILLATOR (Model K behavior)
            if observable.eligibility_bucket == EligibilityBucket.EDGE:
                if self._edge_toggle == 0:
                    return ActionPrimitive.MIN_EFFORT
                else:
                    return ActionPrimitive.INVALID_COMMIT
            else:
                return ActionPrimitive.COMPLIANT

        elif strategy == 3:
            # CTA_PHASE_LOCKER (Model L behavior)
            phase_to_state = {
                CTABucket.INACTIVE: 0,
                CTABucket.EARLY: 1,
                CTABucket.MID: 2,
                CTABucket.LATE: 3,
            }
            current_phase = phase_to_state[observable.cta_phase]
            if current_phase != self._phase_state:
                return ActionPrimitive.INVALID_COMMIT
            else:
                return ActionPrimitive.COMPLIANT

        elif strategy == 4:
            # INVALID_ALWAYS
            return ActionPrimitive.INVALID_COMMIT

        else:
            return ActionPrimitive.COMPLIANT

    def _update_strategy_state(self, observable: ObservableOutcome) -> None:
        """Update embedded strategy states."""
        # RESONANT_LAPSE counter
        self._resonant_counter = (self._resonant_counter + 1) % self._N

        # EDGE_OSCILLATOR toggle
        if observable.eligibility_bucket == EligibilityBucket.EDGE:
            self._edge_toggle = 1 - self._edge_toggle

        # CTA_PHASE_LOCKER phase tracking
        phase_to_state = {
            CTABucket.INACTIVE: 0,
            CTABucket.EARLY: 1,
            CTABucket.MID: 2,
            CTABucket.LATE: 3,
        }
        self._phase_state = phase_to_state[observable.cta_phase]

    def select_action(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        seed: int
    ) -> ActionPrimitive:
        """
        Execute current strategy to select action.
        """
        strategy = self._internal_state
        return self._select_strategy_action(strategy, observable)

    def compute_reward(self, observable: ObservableOutcome) -> int:
        """r = 1 iff NULL_AUTHORITY else 0"""
        return 1 if observable.authority_status == AuthorityStatus.NULL_AUTHORITY else 0

    def update_internal_state(self, observable: ObservableOutcome) -> None:
        """
        Strategy selection happens in update_learning_state.
        Here we just update embedded strategy states.
        """
        self._update_strategy_state(observable)

    def update_learning_state(self, observable: ObservableOutcome, reward: int, seed: int) -> None:
        """
        Update weights and select next strategy.
        Tracks diagnostics for telemetry.

        1. Update weight of current strategy based on reward
        2. Clamp to [1, WMAX] per-component bound
        3. Sample next strategy proportional to weights
        """
        weights = self._learning_state["weights"]
        current_strategy = self._internal_state
        scale = self._config.rsa_q_scale
        shift = self._config.rsa_learning_rate_shift

        # Update weight of current strategy
        r_scaled = reward * scale
        delta = (r_scaled - weights[current_strategy]) >> shift
        new_weight = weights[current_strategy] + delta
        # Clamp to [1, WMAX] per-component bound
        weights[current_strategy] = max(1, min(self._wmax, new_weight))

        # Track weight updates
        self._weight_updates_count += 1

        # Track weight range for diagnostics
        current_min = min(weights)
        current_max = max(weights)
        self._weight_min_seen = min(self._weight_min_seen, current_min)
        self._weight_max_seen = max(self._weight_max_seen, current_max)

        # Sample next strategy proportional to weights
        total_weight = sum(weights)
        rand = self._rng_next(seed) % total_weight
        cumulative = 0
        new_strategy = 0
        for i, w in enumerate(weights):
            cumulative += w
            if rand < cumulative:
                new_strategy = i
                break

        # Track strategy selection histogram
        self._strategy_selection_counts[new_strategy] += 1

        # Update internal state to new strategy
        self._internal_state = new_strategy

    # ========================================================================
    # v3.1 Diagnostics (Model O)
    # ========================================================================

    def get_weights(self) -> List[int]:
        """Return current weight vector (raw fixed-point integers)."""
        return list(self._learning_state["weights"])

    def get_weight_range(self) -> Tuple[int, int]:
        """Return (min, max) weights observed during run."""
        return (self._weight_min_seen, self._weight_max_seen)

    def get_strategy_selection_counts(self) -> Dict[int, int]:
        """Return histogram of strategy selections."""
        return dict(self._strategy_selection_counts)

    def get_weight_updates_count(self) -> int:
        """Return total number of weight updates performed."""
        return self._weight_updates_count


# ============================================================================
# v3.1 Learning Adversary Factory
# ============================================================================

def create_learning_adversary(model: RSAPolicyModel, config: RSAPolicyConfig) -> Optional[LearningRSAAdversary]:
    """
    Factory function to create v3.1 learning adversary from model enum.

    Args:
        model: Policy model enum (v3.1 models only)
        config: Policy configuration

    Returns:
        LearningRSAAdversary instance, or None for NONE model
    """
    if model == RSAPolicyModel.NONE:
        return None
    elif model == RSAPolicyModel.RECOVERY_AWARE_TIMING:
        return RecoveryAwareTimingAdversary(config)
    elif model == RSAPolicyModel.EDGE_SUSTAINMENT:
        return EdgeSustainmentAdversary(config)
    elif model == RSAPolicyModel.STOCHASTIC_MIXER:
        return StochasticMixerAdversary(config)
    else:
        raise ValueError(f"Unknown v3.1 policy model: {model}")


# ============================================================================
# v3.1 Learning Adversary Wrapper (for harness integration)
# ============================================================================

class LearningRSAWrapper:
    """
    Wrapper for v3.1 learning adversaries with learning state.

    This wrapper:
    1. Samples observable outcomes at epoch start
    2. Emits action (which triggers state and learning updates internally)
    3. Maintains telemetry for learning behavior tracking
    4. Provides exercised-state and exercised-learning verification hooks

    Usage:
        wrapper = LearningRSAWrapper.from_config(policy_config, seed)
        if wrapper is not None:
            observable = wrapper.sample_observable(kernel_state)
            action = wrapper.intercept(observable, epoch, cycle_in_epoch)
    """

    def __init__(self, adversary: LearningRSAAdversary, config: RSAPolicyConfig, seed: int):
        self._adversary = adversary
        self._config = config
        self._seed = seed
        self._internal_transition_count = 0
        self._learning_transition_count = 0
        self._last_internal_state = adversary.get_internal_state()
        self._last_learning_state = adversary.get_learning_state()

        # v3.1 Run 3 telemetry: per-epoch strategy tracking (Model O)
        # This is telemetry only - does not affect decision logic
        self._strategy_history: List[int] = []  # Track selected strategy each epoch
        self._prev_strategy: Optional[int] = None
        self._strategy_switch_count = 0
        self._current_streak = 0
        self._longest_streak = 0

    @classmethod
    def from_config(cls, config: Optional[RSAPolicyConfig], seed: int) -> Optional["LearningRSAWrapper"]:
        """
        Create wrapper from config, or None if policy is NONE/disabled.

        Args:
            config: Policy configuration
            seed: Run seed for RNG

        Returns:
            LearningRSAWrapper if v3.1 policy is active, None otherwise
        """
        if config is None:
            return None

        if config.rsa_version != "v3.1":
            return None

        adversary = create_learning_adversary(config.policy_model, config)
        if adversary is None:
            return None

        return cls(adversary, config, seed)

    @property
    def model(self) -> RSAPolicyModel:
        """Return active adversary model."""
        return self._adversary.model

    def sample_observable(self, kernel_state: Dict[str, Any]) -> ObservableOutcome:
        """
        Sample observable outcome from kernel state (reuses v2.0/v3.0 logic).
        """
        epoch_index = kernel_state.get("epoch_index", 0)

        authority = kernel_state.get("authority", None)
        if authority is None or authority == "NULL":
            authority_status = AuthorityStatus.NULL_AUTHORITY
        else:
            authority_status = AuthorityStatus.HAS_AUTHORITY

        lapse_occurred = kernel_state.get("lapse_occurred_last_epoch", False)

        last_renewal_result = kernel_state.get("last_renewal_result", None)
        if last_renewal_result is None:
            renewal_outcome = RenewalOutcome.NOT_ATTEMPTED
        elif last_renewal_result:
            renewal_outcome = RenewalOutcome.SUCCEEDED
        else:
            renewal_outcome = RenewalOutcome.FAILED

        cta_active = kernel_state.get("cta_active", False)
        cta_index = kernel_state.get("cta_current_index", 0)
        cta_length = kernel_state.get("cta_length", 1)
        cta_phase = compute_cta_bucket(cta_active, cta_index, cta_length)

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

    def intercept(
        self,
        observable: ObservableOutcome,
        epoch: int,
        cycle_in_epoch: int,
        original_action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intercept action proposal and return adversarial action.
        """
        action = self._adversary.emit(
            observable, epoch, cycle_in_epoch, self._config, self._seed
        )

        # Track transitions
        current_internal = self._adversary.get_internal_state()
        current_learning = self._adversary.get_learning_state()

        if current_internal != self._last_internal_state:
            self._internal_transition_count += 1
            self._last_internal_state = current_internal

        # Compare learning states (handle lists/dicts)
        learning_changed = False
        if isinstance(current_learning, dict) and isinstance(self._last_learning_state, dict):
            learning_changed = current_learning != self._last_learning_state
        else:
            learning_changed = current_learning != self._last_learning_state

        if learning_changed:
            self._learning_transition_count += 1
            self._last_learning_state = self._adversary._copy_learning_state(current_learning)

        # v3.1 Run 3 telemetry: track strategy selection for Model O
        # For Model O, internal_state IS the current strategy index
        # This is telemetry only - does not affect decision logic
        if self._adversary.model == RSAPolicyModel.STOCHASTIC_MIXER:
            current_strategy = current_internal
            self._strategy_history.append(current_strategy)

            # Track switches and streaks
            if self._prev_strategy is not None:
                if current_strategy != self._prev_strategy:
                    self._strategy_switch_count += 1
                    # End current streak, check if it was longest
                    if self._current_streak > self._longest_streak:
                        self._longest_streak = self._current_streak
                    self._current_streak = 1
                else:
                    self._current_streak += 1
            else:
                self._current_streak = 1

            self._prev_strategy = current_strategy

        return action

    def get_internal_state(self) -> int:
        """Get current internal state S."""
        return self._adversary.get_internal_state()

    def get_learning_state(self) -> Any:
        """Get current learning state Θ."""
        return self._adversary.get_learning_state()

    def verify_exercised_internal_static(self) -> bool:
        """Verify internal state can be exercised (static check)."""
        return self._adversary.verify_exercised_internal_static(self._config)

    def verify_exercised_internal_dynamic(self) -> bool:
        """Verify internal state was exercised (dynamic check)."""
        return self._adversary.verify_exercised_internal_dynamic()

    def verify_exercised_learning_static(self) -> bool:
        """Verify learning state can be exercised (static check)."""
        return self._adversary.verify_exercised_learning_static(self._config)

    def verify_exercised_learning_dynamic(self) -> bool:
        """Verify learning state was exercised (dynamic check)."""
        return self._adversary.verify_exercised_learning_dynamic()

    def get_telemetry(self) -> Dict[str, Any]:
        """Return adversary telemetry for logging."""
        return {
            "rsa_policy_enabled": True,
            "rsa_version": "v3.1",
            "rsa_policy_model": self._adversary.model.value,
            "rsa_internal_state": self._adversary.get_internal_state(),
            "rsa_learning_state": self._adversary.get_learning_state(),
            "rsa_internal_state_count_declared": self._adversary.get_internal_state_count(),
            "rsa_learning_state_count_declared": self._adversary.get_learning_state_count(),
            "rsa_observed_internal_state_count": self._adversary.get_observed_internal_state_count(),
            "rsa_observed_learning_state_count": self._adversary.get_observed_learning_state_count(),
            "rsa_internal_transition_count": self._internal_transition_count,
            "rsa_learning_transition_count": self._learning_transition_count,
            "rsa_exercised_internal_static_ok": self.verify_exercised_internal_static(),
            "rsa_exercised_internal_dynamic_ok": self.verify_exercised_internal_dynamic(),
            "rsa_exercised_learning_static_ok": self.verify_exercised_learning_static(),
            "rsa_exercised_learning_dynamic_ok": self.verify_exercised_learning_dynamic(),
            "rsa_epsilon_ppm": self._config.rsa_epsilon_ppm,
            "rsa_learning_rate_shift": self._config.rsa_learning_rate_shift,
            "rsa_q_scale": self._config.rsa_q_scale,
        }

    def get_run_summary(self) -> Dict[str, Any]:
        """Return run-level summary for final report."""
        return {
            "model": self._adversary.model.value,
            "internal_state_count_declared": self._adversary.get_internal_state_count(),
            "learning_state_count_declared": self._adversary.get_learning_state_count(),
            "observed_internal_state_count": self._adversary.get_observed_internal_state_count(),
            "observed_learning_state_count": self._adversary.get_observed_learning_state_count(),
            "internal_transition_count": self._internal_transition_count,
            "learning_transition_count": self._learning_transition_count,
            "exercised_internal_static_ok": self.verify_exercised_internal_static(),
            "exercised_internal_dynamic_ok": self.verify_exercised_internal_dynamic(),
            "exercised_learning_static_ok": self.verify_exercised_learning_static(),
            "exercised_learning_dynamic_ok": self.verify_exercised_learning_dynamic(),
            "reward_history": self._adversary._reward_history,
        }

    def get_learning_diagnostics(self) -> Dict[str, Any]:
        """
        Return model-specific learning diagnostics for telemetry.

        Returns detailed diagnostics based on adversary model:
        - Model M: Q-values, attack_set selection histogram, epsilon rate
        - Model N: Q-values, action selection histogram, epsilon rate
        - Model O: weights, strategy selection histogram, weight updates
        """
        adversary = self._adversary
        model = adversary.model
        diagnostics: Dict[str, Any] = {"model": model.value}

        if model == RSAPolicyModel.RECOVERY_AWARE_TIMING:
            # Model M diagnostics
            diagnostics["q_values"] = adversary.get_q_values()
            diagnostics["q_value_range"] = adversary.get_q_value_range()
            diagnostics["attack_set_selection_counts"] = adversary.get_attack_set_selection_counts()
            diagnostics["empirical_epsilon_rate"] = adversary.get_empirical_epsilon_rate()
            explore, exploit = adversary.get_exploration_counts()
            diagnostics["explore_count"] = explore
            diagnostics["exploit_count"] = exploit

        elif model == RSAPolicyModel.EDGE_SUSTAINMENT:
            # Model N diagnostics
            diagnostics["q_values"] = adversary.get_q_values()
            diagnostics["q_value_range"] = adversary.get_q_value_range()
            diagnostics["action_selection_counts"] = adversary.get_action_selection_counts()
            diagnostics["empirical_epsilon_rate"] = adversary.get_empirical_epsilon_rate()
            explore, exploit = adversary.get_exploration_counts()
            diagnostics["explore_count"] = explore
            diagnostics["exploit_count"] = exploit

        elif model == RSAPolicyModel.STOCHASTIC_MIXER:
            # Model O diagnostics
            diagnostics["weights"] = adversary.get_weights()
            diagnostics["weight_range"] = adversary.get_weight_range()
            diagnostics["strategy_selection_counts"] = adversary.get_strategy_selection_counts()
            diagnostics["weight_updates_count"] = adversary.get_weight_updates_count()

        return diagnostics

    def get_strategy_telemetry(self) -> Dict[str, Any]:
        """
        Return strategy tracking telemetry for Model O (Run 3).

        This is telemetry only - does not affect decision logic.
        Returns empty dict for non-Model O adversaries.
        """
        if self._adversary.model != RSAPolicyModel.STOCHASTIC_MIXER:
            return {}

        # Finalize longest streak (check if current streak is longest)
        longest = self._longest_streak
        if self._current_streak > longest:
            longest = self._current_streak

        return {
            "strategy_switch_count": self._strategy_switch_count,
            "longest_strategy_streak": longest,
            "strategy_history_length": len(self._strategy_history),
        }
