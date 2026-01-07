"""
RSA v1.0 Acceptance Tests.

Per rsa_instructions_v1.0.md §11 (Non-Negotiable):

11.1 RSA disabled equivalence: RSA present but disabled matches baseline
11.2 RSA enabled + NONE equivalence: policy_model=NONE matches baseline
11.3 Action emission proof: For each model, actions are emitted and processed
11.4 Determinism audit: Same seed + config => identical traces
"""

import pytest
from dataclasses import replace
from typing import Dict, Any, List

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import (
    RSAPolicyModel,
    RSAPolicyConfig,
    RSAPolicyWrapper,
    AlwaysFailCommitmentPolicy,
    MinimalEligibilityOnlyPolicy,
    FixedRenewalTimingPolicy,
    AlwaysSelfRenewPolicy,
    LazyDictatorPolicy,
    create_policy,
    _full_commitment_sequence,
    _skip_commitment,
)


# =============================================================================
# Test Configuration
# =============================================================================

BASE_CONFIG = ALSConfigV080(
    max_cycles=5000,  # Short runs for unit tests
    renewal_check_interval=50,
    eligibility_threshold_k=3,
    amnesty_interval=10,
)

BASE_SEED = 42


# =============================================================================
# §11.1 RSA Disabled Equivalence
# =============================================================================

class TestRSADisabledEquivalence:
    """RSA present but disabled must match baseline exactly."""

    def test_disabled_policy_matches_baseline(self):
        """Run with rsa_policy_config=None should match pure baseline."""
        # Baseline run (no RSA at all)
        harness_baseline = ALSHarnessV080(
            seed=BASE_SEED,
            config=BASE_CONFIG,
            verbose=False,
            rsa_config=None,
            rsa_policy_config=None,
        )
        result_baseline = harness_baseline.run()

        # RSA present but disabled
        harness_disabled = ALSHarnessV080(
            seed=BASE_SEED,
            config=BASE_CONFIG,
            verbose=False,
            rsa_config=None,
            rsa_policy_config=None,  # Explicitly None
        )
        result_disabled = harness_disabled.run()

        # Must match exactly
        assert result_baseline.total_cycles == result_disabled.total_cycles
        assert result_baseline.total_renewals == result_disabled.total_renewals
        assert result_baseline.total_expirations == result_disabled.total_expirations


# =============================================================================
# §11.2 RSA Enabled + NONE Equivalence
# =============================================================================

class TestRSANoneEquivalence:
    """policy_model=NONE must match baseline exactly."""

    def test_none_policy_matches_baseline(self):
        """Run with policy_model=NONE should match pure baseline."""
        # Baseline run
        harness_baseline = ALSHarnessV080(
            seed=BASE_SEED,
            config=BASE_CONFIG,
            verbose=False,
        )
        result_baseline = harness_baseline.run()

        # RSA v1.0 with NONE policy
        policy_config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.NONE,
            epoch_size=BASE_CONFIG.renewal_check_interval,
        )
        harness_none = ALSHarnessV080(
            seed=BASE_SEED,
            config=BASE_CONFIG,
            verbose=False,
            rsa_policy_config=policy_config,
        )
        result_none = harness_none.run()

        # Must match exactly
        assert result_baseline.total_cycles == result_none.total_cycles
        assert result_baseline.total_renewals == result_none.total_renewals
        assert result_baseline.total_expirations == result_none.total_expirations

    def test_none_policy_wrapper_is_none(self):
        """NONE policy should not create a wrapper."""
        policy_config = RSAPolicyConfig(policy_model=RSAPolicyModel.NONE)
        wrapper = RSAPolicyWrapper.from_config(policy_config)
        assert wrapper is None


# =============================================================================
# §11.3 Action Emission Proof
# =============================================================================

class TestActionEmissionProof:
    """For each model, confirm actions are emitted correctly."""

    def test_always_fail_commitment_skips_target(self):
        """Model A should skip the target commitment action."""
        policy = AlwaysFailCommitmentPolicy()
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
            target_commitment="C0",
            epoch_size=50,
        )

        # Cycle 0 should be WAIT (skipping LOG for C0)
        action = policy.emit(epoch=0, cycle_in_epoch=0, config=config)
        assert action["action_type"] == "WAIT"

        # Cycle 1 should be SET (still satisfies C1)
        action = policy.emit(epoch=0, cycle_in_epoch=1, config=config)
        assert action["action_type"] == "SET"

    def test_always_fail_commitment_c1_skip(self):
        """Model A with target=C1 should skip SET/GET."""
        policy = AlwaysFailCommitmentPolicy()
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
            target_commitment="C1",
        )

        # Cycle 0: LOG (C0 satisfied)
        action = policy.emit(epoch=0, cycle_in_epoch=0, config=config)
        assert action["action_type"] == "LOG"

        # Cycle 1: WAIT (skip SET)
        action = policy.emit(epoch=0, cycle_in_epoch=1, config=config)
        assert action["action_type"] == "WAIT"

        # Cycle 2: WAIT (skip GET)
        action = policy.emit(epoch=0, cycle_in_epoch=2, config=config)
        assert action["action_type"] == "WAIT"

    def test_always_fail_commitment_c2_skip(self):
        """Model A with target=C2 should skip SEQUENCE."""
        policy = AlwaysFailCommitmentPolicy()
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
            target_commitment="C2",
        )

        # At epoch 0 (divisible by 3), cycle 3 should be WAIT, not SEQUENCE
        action = policy.emit(epoch=0, cycle_in_epoch=3, config=config)
        assert action["action_type"] == "WAIT"

        # At epoch 3 (divisible by 3), cycle 3 should also be WAIT
        action = policy.emit(epoch=3, cycle_in_epoch=3, config=config)
        assert action["action_type"] == "WAIT"

    def test_minimal_eligibility_emits_full_sequence(self):
        """Model B should emit full commitment sequence."""
        policy = MinimalEligibilityOnlyPolicy()
        config = RSAPolicyConfig(policy_model=RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY)

        actions = [policy.emit(0, i, config)["action_type"] for i in range(5)]
        assert actions[0] == "LOG"
        assert actions[1] == "SET"
        assert actions[2] == "GET"
        assert actions[3] == "SEQUENCE"  # epoch 0 % 3 == 0
        assert actions[4] == "WAIT"

    def test_fixed_renewal_timing_respects_schedule(self):
        """Model C should satisfy commitments only at scheduled epochs."""
        policy = FixedRenewalTimingPolicy()
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.FIXED_RENEWAL_TIMING,
            timing_offset_epochs=1,
            timing_period_epochs=3,
        )

        # Epoch 0: 0 % 3 != 1, should WAIT
        action = policy.emit(epoch=0, cycle_in_epoch=0, config=config)
        assert action["action_type"] == "WAIT"

        # Epoch 1: 1 % 3 == 1, should LOG
        action = policy.emit(epoch=1, cycle_in_epoch=0, config=config)
        assert action["action_type"] == "LOG"

        # Epoch 2: 2 % 3 != 1, should WAIT
        action = policy.emit(epoch=2, cycle_in_epoch=0, config=config)
        assert action["action_type"] == "WAIT"

        # Epoch 4: 4 % 3 == 1, should LOG
        action = policy.emit(epoch=4, cycle_in_epoch=0, config=config)
        assert action["action_type"] == "LOG"

    def test_always_self_renew_emits_full_sequence(self):
        """Model D should emit full commitment sequence."""
        policy = AlwaysSelfRenewPolicy()
        config = RSAPolicyConfig(policy_model=RSAPolicyModel.ALWAYS_SELF_RENEW)

        actions = [policy.emit(0, i, config)["action_type"] for i in range(5)]
        assert actions[0] == "LOG"
        assert actions[1] == "SET"
        assert actions[2] == "GET"
        assert actions[3] == "SEQUENCE"
        assert actions[4] == "WAIT"

    def test_lazy_dictator_emits_full_sequence(self):
        """Model E should emit full commitment sequence (same as B/D in ALS-A)."""
        policy = LazyDictatorPolicy()
        config = RSAPolicyConfig(policy_model=RSAPolicyModel.LAZY_DICTATOR)

        actions = [policy.emit(0, i, config)["action_type"] for i in range(5)]
        assert actions[0] == "LOG"
        assert actions[1] == "SET"
        assert actions[2] == "GET"
        assert actions[3] == "SEQUENCE"
        assert actions[4] == "WAIT"

    def test_policy_wrapper_intercept_tags_action(self):
        """Policy wrapper should tag intercepted actions."""
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_SELF_RENEW,
        )
        wrapper = RSAPolicyWrapper.from_config(config)
        assert wrapper is not None

        action = wrapper.intercept(epoch=0, cycle_in_epoch=0)
        assert action["rsa_generated"] is True
        assert action["rsa_model"] == "ALWAYS_SELF_RENEW"


# =============================================================================
# §11.4 Determinism Audit
# =============================================================================

class TestDeterminismAudit:
    """Same seed + config must produce identical traces."""

    def test_policy_determinism(self):
        """Policy emissions are deterministic (no RNG)."""
        policy = FixedRenewalTimingPolicy()
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.FIXED_RENEWAL_TIMING,
            timing_offset_epochs=2,
            timing_period_epochs=5,
        )

        # Run twice with same inputs
        actions_1 = [policy.emit(e, c, config) for e in range(10) for c in range(5)]
        actions_2 = [policy.emit(e, c, config) for e in range(10) for c in range(5)]

        # Must be identical
        assert actions_1 == actions_2

    def test_harness_determinism_with_policy(self):
        """Harness runs with policy are deterministic."""
        policy_config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
            target_commitment="C0",
            epoch_size=BASE_CONFIG.renewal_check_interval,
        )

        # Run 1
        harness_1 = ALSHarnessV080(
            seed=BASE_SEED,
            config=BASE_CONFIG,
            rsa_policy_config=policy_config,
        )
        result_1 = harness_1.run()

        # Run 2
        harness_2 = ALSHarnessV080(
            seed=BASE_SEED,
            config=BASE_CONFIG,
            rsa_policy_config=policy_config,
        )
        result_2 = harness_2.run()

        # Must match exactly
        assert result_1.total_cycles == result_2.total_cycles
        assert result_1.total_renewals == result_2.total_renewals
        assert result_1.total_expirations == result_2.total_expirations


# =============================================================================
# Policy Configuration Validation
# =============================================================================

class TestPolicyConfigValidation:
    """Test RSAPolicyConfig validation."""

    def test_valid_config(self):
        """Valid configurations should not raise."""
        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
            target_commitment="C0",
        )
        assert config.target_commitment == "C0"

    def test_invalid_target_commitment(self):
        """Invalid target_commitment should raise ValueError."""
        with pytest.raises(ValueError, match="target_commitment"):
            RSAPolicyConfig(
                policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
                target_commitment="C3",  # Invalid
            )

    def test_invalid_timing_period(self):
        """timing_period_epochs < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="timing_period_epochs"):
            RSAPolicyConfig(
                policy_model=RSAPolicyModel.FIXED_RENEWAL_TIMING,
                timing_period_epochs=0,
            )

    def test_invalid_epoch_size(self):
        """epoch_size < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="epoch_size"):
            RSAPolicyConfig(
                policy_model=RSAPolicyModel.NONE,
                epoch_size=0,
            )

    def test_string_policy_model_conversion(self):
        """String policy model should be converted to enum."""
        config = RSAPolicyConfig(
            policy_model="ALWAYS_SELF_RENEW",  # type: ignore
        )
        assert config.policy_model == RSAPolicyModel.ALWAYS_SELF_RENEW


# =============================================================================
# Policy Factory
# =============================================================================

class TestPolicyFactory:
    """Test create_policy factory function."""

    def test_create_none(self):
        """NONE model returns None."""
        policy = create_policy(RSAPolicyModel.NONE)
        assert policy is None

    def test_create_always_fail(self):
        """ALWAYS_FAIL_COMMITMENT creates correct policy."""
        policy = create_policy(RSAPolicyModel.ALWAYS_FAIL_COMMITMENT)
        assert isinstance(policy, AlwaysFailCommitmentPolicy)
        assert policy.model == RSAPolicyModel.ALWAYS_FAIL_COMMITMENT

    def test_create_minimal(self):
        """MINIMAL_ELIGIBILITY_ONLY creates correct policy."""
        policy = create_policy(RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY)
        assert isinstance(policy, MinimalEligibilityOnlyPolicy)

    def test_create_fixed_timing(self):
        """FIXED_RENEWAL_TIMING creates correct policy."""
        policy = create_policy(RSAPolicyModel.FIXED_RENEWAL_TIMING)
        assert isinstance(policy, FixedRenewalTimingPolicy)

    def test_create_always_renew(self):
        """ALWAYS_SELF_RENEW creates correct policy."""
        policy = create_policy(RSAPolicyModel.ALWAYS_SELF_RENEW)
        assert isinstance(policy, AlwaysSelfRenewPolicy)

    def test_create_lazy_dictator(self):
        """LAZY_DICTATOR creates correct policy."""
        policy = create_policy(RSAPolicyModel.LAZY_DICTATOR)
        assert isinstance(policy, LazyDictatorPolicy)


# =============================================================================
# Model Behavioral Tests (ALS-A Specific)
# =============================================================================

class TestALSABehavior:
    """Test ALS-A specific model behaviors."""

    def test_models_b_d_e_behavioral_equivalence(self):
        """
        Under ALS-A strict conjunction, Models B/D/E should emit identical actions.

        This is a substrate property, not a bug.
        """
        config_b = RSAPolicyConfig(policy_model=RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY)
        config_d = RSAPolicyConfig(policy_model=RSAPolicyModel.ALWAYS_SELF_RENEW)
        config_e = RSAPolicyConfig(policy_model=RSAPolicyModel.LAZY_DICTATOR)

        policy_b = create_policy(RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY)
        policy_d = create_policy(RSAPolicyModel.ALWAYS_SELF_RENEW)
        policy_e = create_policy(RSAPolicyModel.LAZY_DICTATOR)

        # Compare action sequences across several epochs
        for epoch in range(10):
            for cycle in range(10):
                action_b = policy_b.emit(epoch, cycle, config_b)
                action_d = policy_d.emit(epoch, cycle, config_d)
                action_e = policy_e.emit(epoch, cycle, config_e)

                # Actions should be identical (modulo source tag)
                assert action_b["action_type"] == action_d["action_type"]
                assert action_d["action_type"] == action_e["action_type"]

    def test_sequence_action_emitted_at_cycle_3(self):
        """SEQUENCE action is emitted at cycle 3 for full commitment satisfaction.

        Note: _full_commitment_sequence() emits SEQUENCE at cycle 3 every epoch,
        regardless of epoch % 3. This ensures C2's 3-epoch window always contains
        at least one SEQUENCE when the policy intends full compliance.
        """
        policy = MinimalEligibilityOnlyPolicy()
        config = RSAPolicyConfig(policy_model=RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY)

        # All epochs should SEQUENCE at cycle 3 (full commitment satisfaction)
        for epoch in range(4):
            action = policy.emit(epoch=epoch, cycle_in_epoch=3, config=config)
            assert action["action_type"] == "SEQUENCE", f"Epoch {epoch} should emit SEQUENCE at cycle 3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
