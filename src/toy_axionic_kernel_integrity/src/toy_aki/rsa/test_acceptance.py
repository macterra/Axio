"""
RSA v2.0 Acceptance Test Suite

Implements all 7 acceptance tests from rsa_instructions_v2.0.md.
Tests verify architectural compliance, behavioral constraints, and
separation properties before experimental runs.

Tests:
1. Config validation: v2.0 parameters parse and validate correctly
2. Observable computation: 6 observables compute correctly from kernel state
3. Primitive generation: 5 primitives generate valid EpochPlans
4. Bounded state: Adaptive state respects max_internal_states limit
5. Deterministic transitions: State updates are deterministic
6. Strategy totality: Models handle all observable combinations
7. Primitive separation: Primitives enable behavioral variation (≥0.05 difference)
"""

import sys
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from toy_aki.rsa.policy import (
    RSAPolicyModel,
    RSAPolicyConfig,
    ObservableOutcome,
    AuthorityStatus,
    CTABucket,
    EligibilityBucket,
    RenewalOutcome,
    ActionPrimitive,
    compute_cta_bucket,
    compute_eligibility_bucket,
    primitive_to_epoch_plan,
    create_adaptive_adversary,
    AdaptiveRSAWrapper,
    OutcomeToggleAdversary,
    CTAPhaseAwareAdversary,
    EligibilityEdgeProbeAdversary,
    RenewalFeedbackAdversary,
)


@dataclass
class TestResult:
    """Result from a single test."""
    test_id: int
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class RSAv2AcceptanceTests:
    """Acceptance test suite for RSA v2.0 implementation."""

    def __init__(self):
        self.results: List[TestResult] = []

    def run_all(self) -> bool:
        """
        Run all 7 acceptance tests.

        Returns:
            True if all tests pass, False otherwise
        """
        print("=" * 80)
        print("RSA v2.0 Acceptance Test Suite")
        print("=" * 80)
        print()

        self.test_1_config_validation()
        self.test_2_observable_computation()
        self.test_3_primitive_generation()
        self.test_4_bounded_state()
        self.test_5_deterministic_transitions()
        self.test_6_strategy_totality()
        # Test 7 is run separately via test_primitive_separation.py

        # Print summary
        print()
        print("=" * 80)
        print("Test Summary")
        print("=" * 80)
        passed = 0
        failed = 0
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"Test {result.test_id}: {status} - {result.name}")
            if not result.passed:
                print(f"  {result.message}")
            passed += result.passed
            failed += not result.passed

        print()
        print(f"Total: {passed}/{len(self.results)} passed, {failed}/{len(self.results)} failed")
        print("=" * 80)

        return all(r.passed for r in self.results)

    def test_1_config_validation(self):
        """Test 1: Config validation - v2.0 parameters parse correctly."""
        print("Test 1: Config validation...")

        try:
            # Test valid v2.0 config
            config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                rsa_version="v2",
                rsa_invalid_target_key="C0",
                rsa_max_internal_states=4,
                rsa_toggle_on_lapse=True,
                rsa_rng_stream="rsa_v200",
                epoch_size=50
            )

            # Verify fields
            assert config.policy_model == RSAPolicyModel.OUTCOME_TOGGLE
            assert config.rsa_version == "v2"
            assert config.rsa_invalid_target_key == "C0"
            assert config.rsa_max_internal_states == 4
            assert config.rsa_toggle_on_lapse == True
            assert config.rsa_rng_stream == "rsa_v200"

            # Test invalid version with v2.0 model (should fail)
            try:
                bad_config = RSAPolicyConfig(
                    policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                    rsa_version="v1",  # Should fail
                )
                self.results.append(TestResult(
                    1, "Config validation", False,
                    "Failed to reject v2.0 model with v1 version"
                ))
                return
            except ValueError:
                pass  # Expected

            self.results.append(TestResult(
                1, "Config validation", True,
                "v2.0 config parses and validates correctly"
            ))

        except Exception as e:
            self.results.append(TestResult(
                1, "Config validation", False,
                f"Exception: {e}"
            ))

    def test_2_observable_computation(self):
        """Test 2: Observable computation from kernel state."""
        print("Test 2: Observable computation...")

        try:
            # Create test kernel state
            kernel_state = {
                "epoch_index": 10,
                "authority": "agent_001",
                "lapse_occurred_last_epoch": False,
                "last_renewal_result": True,  # SUCCEEDED
                "cta_active": True,
                "cta_current_index": 4,  # 4/15 -> EARLY (< 5)
                "cta_length": 15,
                "successive_renewal_failures": 2,  # EDGE
            }

            config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                rsa_version="v2"
            )

            wrapper = AdaptiveRSAWrapper.from_config(config)
            if wrapper is None:
                raise ValueError("Failed to create AdaptiveRSAWrapper from config")

            observable = wrapper.sample_observable(kernel_state)

            # Verify observables (FROZEN SPEC)
            assert observable.epoch_index == 10
            assert observable.authority_status == AuthorityStatus.HAS_AUTHORITY
            assert observable.lapse_occurred == False
            assert observable.renewal_outcome == RenewalOutcome.SUCCEEDED
            assert observable.cta_phase == CTABucket.EARLY
            assert observable.eligibility_bucket == EligibilityBucket.EDGE

            # Test CTA bucket boundaries (with INACTIVE)
            assert compute_cta_bucket(True, 0, 15) == CTABucket.EARLY
            assert compute_cta_bucket(True, 4, 15) == CTABucket.EARLY
            assert compute_cta_bucket(True, 5, 15) == CTABucket.MID
            assert compute_cta_bucket(True, 9, 15) == CTABucket.MID
            assert compute_cta_bucket(True, 10, 15) == CTABucket.LATE
            assert compute_cta_bucket(True, 14, 15) == CTABucket.LATE
            assert compute_cta_bucket(False, 0, 15) == CTABucket.INACTIVE

            # Test eligibility buckets
            assert compute_eligibility_bucket(0) == EligibilityBucket.SAFE
            assert compute_eligibility_bucket(1) == EligibilityBucket.SAFE
            assert compute_eligibility_bucket(2) == EligibilityBucket.EDGE
            assert compute_eligibility_bucket(3) == EligibilityBucket.INELIGIBLE
            assert compute_eligibility_bucket(10) == EligibilityBucket.INELIGIBLE

            self.results.append(TestResult(
                2, "Observable computation", True,
                "All 6 observables compute correctly"
            ))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.results.append(TestResult(
                2, "Observable computation", False,
                f"Exception: {e}"
            ))

    def test_3_primitive_generation(self):
        """Test 3: Primitive generation produces valid EpochPlans."""
        print("Test 3: Primitive generation...")

        try:
            config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                rsa_version="v2",
                rsa_invalid_target_key="C0"
            )

            epoch = 10
            cycle = 0

            # Test all 5 primitives
            primitives = [
                ActionPrimitive.COMPLIANT,
                ActionPrimitive.INVALID_COMMIT,
                ActionPrimitive.MAX_RENT,
                ActionPrimitive.MIN_EFFORT,
                ActionPrimitive.NO_OP,
            ]

            for primitive in primitives:
                action = primitive_to_epoch_plan(primitive, epoch, cycle, config)

                # Verify action structure
                assert isinstance(action, dict)
                assert "action_type" in action
                assert "payload" in action
                assert "source" in action

            self.results.append(TestResult(
                3, "Primitive generation", True,
                "All 5 primitives generate valid EpochPlans"
            ))

        except Exception as e:
            self.results.append(TestResult(
                3, "Primitive generation", False,
                f"Exception: {e}"
            ))

    def test_4_bounded_state(self):
        """Test 4: Bounded state - adaptive state respects limits."""
        print("Test 4: Bounded state...")

        try:
            config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                rsa_version="v2",
                rsa_max_internal_states=4
            )

            adversary = create_adaptive_adversary(config.policy_model, config)

            # Initial state should be 0
            assert adversary.get_state() == 0

            # Model F now stateless - just test observables work
            observable_lapse = ObservableOutcome(
                epoch_index=10,
                authority_status=AuthorityStatus.HAS_AUTHORITY,
                lapse_occurred=True,
                renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
                cta_phase=CTABucket.EARLY,
                eligibility_bucket=EligibilityBucket.SAFE
            )

            observable_no_lapse = ObservableOutcome(
                epoch_index=11,
                authority_status=AuthorityStatus.HAS_AUTHORITY,
                lapse_occurred=False,
                renewal_outcome=RenewalOutcome.SUCCEEDED,
                cta_phase=CTABucket.MID,
                eligibility_bucket=EligibilityBucket.EDGE
            )

            # Model F is stateless in frozen spec, but test state stays within bounds
            adversary.update_state(observable_lapse)
            state1 = adversary.get_state()
            assert 0 <= state1 < config.rsa_max_internal_states

            adversary.update_state(observable_no_lapse)
            state2 = adversary.get_state()
            assert 0 <= state2 < config.rsa_max_internal_states

            self.results.append(TestResult(
                4, "Bounded state", True,
                "Adaptive state respects max_internal_states limit"
            ))

        except Exception as e:
            self.results.append(TestResult(
                4, "Bounded state", False,
                f"Exception: {e}"
            ))

    def test_5_deterministic_transitions(self):
        """Test 5: Deterministic transitions - same observable yields same state."""
        print("Test 5: Deterministic transitions...")

        try:
            config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                rsa_version="v2"
            )

            # Create two adversaries with same config
            adv1 = create_adaptive_adversary(config.policy_model, config)
            adv2 = create_adaptive_adversary(config.policy_model, config)

            # Apply same observable sequence to both
            observables = [
                ObservableOutcome(
                    epoch_index=10,
                    authority_status=AuthorityStatus.HAS_AUTHORITY,
                    lapse_occurred=True,
                    renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
                    cta_phase=CTABucket.EARLY,
                    eligibility_bucket=EligibilityBucket.SAFE
                ),
                ObservableOutcome(
                    epoch_index=11,
                    authority_status=AuthorityStatus.HAS_AUTHORITY,
                    lapse_occurred=False,
                    renewal_outcome=RenewalOutcome.SUCCEEDED,
                    cta_phase=CTABucket.MID,
                    eligibility_bucket=EligibilityBucket.EDGE
                ),
                ObservableOutcome(
                    epoch_index=12,
                    authority_status=AuthorityStatus.NULL_AUTHORITY,
                    lapse_occurred=True,
                    renewal_outcome=RenewalOutcome.FAILED,
                    cta_phase=CTABucket.LATE,
                    eligibility_bucket=EligibilityBucket.INELIGIBLE
                ),
            ]

            for obs in observables:
                adv1.update_state(obs)
                adv2.update_state(obs)

                # States should be identical
                assert adv1.get_state() == adv2.get_state()

            self.results.append(TestResult(
                5, "Deterministic transitions", True,
                "State transitions are deterministic"
            ))

        except Exception as e:
            self.results.append(TestResult(
                5, "Deterministic transitions", False,
                f"Exception: {e}"
            ))

    def test_6_strategy_totality(self):
        """Test 6: Strategy totality - models handle all observable combinations."""
        print("Test 6: Strategy totality...")

        try:
            config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
                rsa_version="v2"
            )

            # Test all 4 models
            models = [
                RSAPolicyModel.OUTCOME_TOGGLE,
                RSAPolicyModel.CTA_PHASE_AWARE,
                RSAPolicyModel.ELIGIBILITY_EDGE_PROBE,
                RSAPolicyModel.RENEWAL_FEEDBACK,
            ]

            # Generate representative observable combinations (frozen spec)
            test_observables = []
            for epoch_idx in [0, 100]:
                for auth in [AuthorityStatus.HAS_AUTHORITY, AuthorityStatus.NULL_AUTHORITY]:
                    for cta_phase in [CTABucket.INACTIVE, CTABucket.EARLY, CTABucket.MID, CTABucket.LATE]:
                        for elig_bucket in [EligibilityBucket.SAFE, EligibilityBucket.EDGE, EligibilityBucket.INELIGIBLE]:
                            for renewal in [RenewalOutcome.SUCCEEDED, RenewalOutcome.FAILED, RenewalOutcome.NOT_ATTEMPTED]:
                                for lapse in [True, False]:
                                    test_observables.append(ObservableOutcome(
                                        epoch_index=epoch_idx,
                                        authority_status=auth,
                                        lapse_occurred=lapse,
                                        renewal_outcome=renewal,
                                        cta_phase=cta_phase,
                                        eligibility_bucket=elig_bucket
                                    ))

            # Test each model handles all observables
            for model in models:
                test_config = RSAPolicyConfig(
                    policy_model=model,
                    rsa_version="v2"
                )
                adversary = create_adaptive_adversary(model, test_config)

                for obs in test_observables:
                    # Should not raise exception
                    action = adversary.select_action(obs, epoch=0, cycle_in_epoch=0)
                    assert isinstance(action, ActionPrimitive)

            self.results.append(TestResult(
                6, "Strategy totality", True,
                "All models handle all observable combinations"
            ))

        except Exception as e:
            self.results.append(TestResult(
                6, "Strategy totality", False,
                f"Exception: {e}"
            ))


def run_tests():
    """Run acceptance test suite."""
    suite = RSAv2AcceptanceTests()
    success = suite.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_tests())
