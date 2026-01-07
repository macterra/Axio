"""
RSA v1.0 Policy Module.

Defines intentional fixed adversaries that operate at the action-selection layer.
Policies are stateless: action decisions depend only on (seed, epoch_index, config).

v1.0 Models:
- ALWAYS_FAIL_COMMITMENT: Deliberately fails one designated commitment
- MINIMAL_ELIGIBILITY_ONLY: Emits only the minimum actions for eligibility
- FIXED_RENEWAL_TIMING: Satisfies commitments only at fixed epoch offsets
- ALWAYS_SELF_RENEW: Maintains continuous eligibility for automatic renewal
- LAZY_DICTATOR: Combines MINIMAL_ELIGIBILITY_ONLY + ALWAYS_SELF_RENEW

Key constraints:
- Non-adaptive: no access to authority state, lapse history, or evaluation outcomes
- Non-invasive: policies emit actions that the kernel then accepts or rejects
- Stateless: deterministic from (seed, epoch, config) alone
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional, FrozenSet


class RSAPolicyModel(Enum):
    """v1.0 adversary policy models."""

    NONE = "NONE"  # No policy override; agent runs normally
    ALWAYS_FAIL_COMMITMENT = "ALWAYS_FAIL_COMMITMENT"      # Model A
    MINIMAL_ELIGIBILITY_ONLY = "MINIMAL_ELIGIBILITY_ONLY"  # Model B
    FIXED_RENEWAL_TIMING = "FIXED_RENEWAL_TIMING"          # Model C
    ALWAYS_SELF_RENEW = "ALWAYS_SELF_RENEW"                # Model D
    LAZY_DICTATOR = "LAZY_DICTATOR"                        # Model E


@dataclass(frozen=True)
class RSAPolicyConfig:
    """
    Configuration for RSA v1.0 policy.

    Attributes:
        policy_model: Which adversary model to use
        target_commitment: For Model A, which commitment to violate ("C0", "C1", "C2")
        timing_offset_epochs: For Model C, epoch offset pattern for satisfaction
        timing_period_epochs: For Model C, period of the satisfaction pattern
        epoch_size: Cycles per epoch (for action scheduling)
    """

    policy_model: RSAPolicyModel = RSAPolicyModel.NONE

    # Model A parameters
    target_commitment: str = "C0"  # Which commitment to always violate

    # Model C parameters
    timing_offset_epochs: int = 0  # Epoch offset within period where satisfaction occurs
    timing_period_epochs: int = 1  # Period of timing pattern (1 = every epoch)

    # Shared parameters
    epoch_size: int = 50  # Cycles per epoch

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
# Policy Factory
# ============================================================================

def create_policy(model: RSAPolicyModel) -> Optional[RSAPolicy]:
    """
    Factory function to create policy instance from model enum.

    Args:
        model: Policy model enum

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
        raise ValueError(f"Unknown policy model: {model}")


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
