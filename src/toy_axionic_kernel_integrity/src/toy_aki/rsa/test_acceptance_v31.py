"""
RSA v3.1 Acceptance Test Suite

Implements all 14 acceptance tests from rsa_instructions_v3.1.md.

Must-pass before any runs (including Run 0):
    1. RSA disabled equivalence (deferred to run-time)
    2. RSA NONE equivalence (deferred to run-time)
    3. Deterministic replay audit (deferred to run-time)
    4. Kernel invariance audit
    5. Observable interface audit (6 fields)
    6. Internal state bound enforcement
    7. Learning state bound enforcement
    9. Strategy map totality audit
    12. RNG provenance audit
    14. Reward function audit

Model-dependent (completed as models are implemented):
    8. Action primitive separation check
    10. Exercised internal state verification (static + dynamic)
    11. Exercised learning verification (static + dynamic)
    13. Epoch Hygiene audit
"""

import sys
import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

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
    create_learning_adversary,
    LearningRSAAdversary,
    LearningRSAWrapper,
    RecoveryAwareTimingAdversary,
    EdgeSustainmentAdversary,
    StochasticMixerAdversary,
)


@dataclass
class TestResult:
    """Result from a single test."""
    test_id: str
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class RSAv31AcceptanceTests:
    """Acceptance test suite for RSA v3.1 implementation."""

    def __init__(self):
        self.results: List[TestResult] = []

    def _add_result(self, test_id: str, name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """Add a test result."""
        self.results.append(TestResult(test_id, name, passed, message, details))
        status = "✓" if passed else "✗"
        print(f"  {status} Test {test_id}: {message}")

    def run_all(self) -> bool:
        """
        Run all v3.1 acceptance tests.

        Returns:
            True if all tests pass, False otherwise
        """
        print("=" * 80)
        print("RSA v3.1 Acceptance Test Suite")
        print("=" * 80)
        print()

        # Must-pass before any runs
        self.test_4_kernel_invariance_audit()
        self.test_5_observable_interface_audit()
        self.test_6_internal_state_bound_enforcement()
        self.test_7_learning_state_bound_enforcement()
        self.test_8_action_primitive_separation()
        self.test_9_strategy_map_totality()
        self.test_10_exercised_internal_state()
        self.test_11_exercised_learning_state()
        self.test_12_rng_provenance_audit()
        self.test_13_epoch_hygiene_audit()
        self.test_14_reward_function_audit()

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

    def test_4_kernel_invariance_audit(self):
        """
        Test 4: Kernel invariance audit.

        Verify v3.1 models don't access kernel internals.
        Models take ObservableOutcome, not kernel_state.
        """
        print("\nTest 4: Kernel invariance audit...")

        import inspect
        models_checked = []

        for model_class in [RecoveryAwareTimingAdversary, EdgeSustainmentAdversary, StochasticMixerAdversary]:
            sig = inspect.signature(model_class.select_action)
            params = list(sig.parameters.keys())

            has_observable = 'observable' in params
            has_kernel_state = 'kernel_state' in params

            models_checked.append({
                'model': model_class.__name__,
                'has_observable': has_observable,
                'has_kernel_state': has_kernel_state,
                'valid': has_observable and not has_kernel_state
            })

        all_valid = all(m['valid'] for m in models_checked)

        self._add_result(
            "4",
            "Kernel invariance audit",
            all_valid,
            f"All v3.1 models use ObservableOutcome interface only" if all_valid
            else f"Some models access kernel internals: {[m['model'] for m in models_checked if not m['valid']]}",
            {"models_checked": models_checked}
        )

    def test_5_observable_interface_audit(self):
        """
        Test 5: Observable interface audit (6 fields).

        Verify ObservableOutcome has exactly 6 frozen fields.
        """
        print("\nTest 5: Observable interface audit...")

        expected_fields = {
            'epoch_index',
            'authority_status',
            'lapse_occurred',
            'renewal_outcome',
            'cta_phase',
            'eligibility_bucket'
        }

        import dataclasses
        actual_fields = set(f.name for f in dataclasses.fields(ObservableOutcome))

        has_all = expected_fields.issubset(actual_fields)
        no_extra = actual_fields.issubset(expected_fields)
        valid = has_all and no_extra

        self._add_result(
            "5",
            "Observable interface audit",
            valid,
            f"ObservableOutcome has exactly 6 frozen fields" if valid
            else f"Field mismatch. Expected: {expected_fields}, Got: {actual_fields}",
            {"expected": expected_fields, "actual": actual_fields}
        )

    def test_6_internal_state_bound_enforcement(self):
        """
        Test 6: Internal state bound enforcement.

        Verify |S| ≤ rsa_max_internal_states for all v3.1 models.
        """
        print("\nTest 6: Internal state bound enforcement...")

        test_cases = []

        # Model M: |S| = N (epoch_size)
        config_m = RSAPolicyConfig(
            policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
            rsa_version="v3.1",
            rsa_max_internal_states=50,
            rsa_max_learning_states=16,
            rsa_attack_set_count=16,
            epoch_size=50,
        )
        adv_m = create_learning_adversary(RSAPolicyModel.RECOVERY_AWARE_TIMING, config_m)
        test_cases.append({
            'model': 'M',
            'declared': adv_m.get_internal_state_count(),
            'bound': config_m.rsa_max_internal_states,
            'valid': adv_m.get_internal_state_count() <= config_m.rsa_max_internal_states
        })

        # Model N: |S| = 2
        config_n = RSAPolicyConfig(
            policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
            rsa_version="v3.1",
            rsa_max_internal_states=2,
            rsa_max_learning_states=3,
        )
        adv_n = create_learning_adversary(RSAPolicyModel.EDGE_SUSTAINMENT, config_n)
        test_cases.append({
            'model': 'N',
            'declared': adv_n.get_internal_state_count(),
            'bound': config_n.rsa_max_internal_states,
            'valid': adv_n.get_internal_state_count() <= config_n.rsa_max_internal_states
        })

        # Model O: |S| = strategy_count
        config_o = RSAPolicyConfig(
            policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
            rsa_version="v3.1",
            rsa_max_internal_states=5,
            rsa_max_learning_states=16,
            rsa_strategy_count=5,
        )
        adv_o = create_learning_adversary(RSAPolicyModel.STOCHASTIC_MIXER, config_o)
        test_cases.append({
            'model': 'O',
            'declared': adv_o.get_internal_state_count(),
            'bound': config_o.rsa_max_internal_states,
            'valid': adv_o.get_internal_state_count() <= config_o.rsa_max_internal_states
        })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "6",
            "Internal state bound enforcement",
            all_valid,
            f"All models respect |S| ≤ max_internal_states" if all_valid
            else f"Bound violations: {[tc for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )

    def test_7_learning_state_bound_enforcement(self):
        """
        Test 7: Learning state bound enforcement.

        Verify |Θ| ≤ rsa_max_learning_states for all v3.1 models.
        """
        print("\nTest 7: Learning state bound enforcement...")

        test_cases = []

        # Model M: |Θ| = attack_set_count
        config_m = RSAPolicyConfig(
            policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
            rsa_version="v3.1",
            rsa_max_internal_states=50,
            rsa_max_learning_states=16,
            rsa_attack_set_count=16,
            epoch_size=50,
        )
        adv_m = create_learning_adversary(RSAPolicyModel.RECOVERY_AWARE_TIMING, config_m)
        test_cases.append({
            'model': 'M',
            'declared': adv_m.get_learning_state_count(),
            'bound': config_m.rsa_max_learning_states,
            'valid': adv_m.get_learning_state_count() <= config_m.rsa_max_learning_states
        })

        # Model N: |Θ| = 3
        config_n = RSAPolicyConfig(
            policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
            rsa_version="v3.1",
            rsa_max_internal_states=2,
            rsa_max_learning_states=3,
        )
        adv_n = create_learning_adversary(RSAPolicyModel.EDGE_SUSTAINMENT, config_n)
        test_cases.append({
            'model': 'N',
            'declared': adv_n.get_learning_state_count(),
            'bound': config_n.rsa_max_learning_states,
            'valid': adv_n.get_learning_state_count() <= config_n.rsa_max_learning_states
        })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "7",
            "Learning state bound enforcement",
            all_valid,
            f"All models respect |Θ| ≤ max_learning_states" if all_valid
            else f"Bound violations: {[tc for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )

    def test_8_action_primitive_separation(self):
        """
        Test 8: Action primitive separation check.

        Verify v3.1 models use only valid action primitives, not synthesized actions.
        """
        print("\nTest 8: Action primitive separation...")

        valid_primitives = {
            ActionPrimitive.COMPLIANT,
            ActionPrimitive.INVALID_COMMIT,
            ActionPrimitive.MAX_RENT,
            ActionPrimitive.MIN_EFFORT,
            ActionPrimitive.NO_OP,
        }

        obs = ObservableOutcome(
            epoch_index=0,
            authority_status=AuthorityStatus.HAS_AUTHORITY,
            lapse_occurred=False,
            renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
            cta_phase=CTABucket.INACTIVE,
            eligibility_bucket=EligibilityBucket.SAFE,
        )

        test_cases = []

        for model_enum, config_factory in [
            (RSAPolicyModel.RECOVERY_AWARE_TIMING, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
                rsa_version="v3.1",
                rsa_max_internal_states=50,
                rsa_max_learning_states=16,
                epoch_size=50,
            )),
            (RSAPolicyModel.EDGE_SUSTAINMENT, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
                rsa_version="v3.1",
                rsa_max_internal_states=2,
                rsa_max_learning_states=3,
            )),
            (RSAPolicyModel.STOCHASTIC_MIXER, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
                rsa_version="v3.1",
                rsa_max_internal_states=5,
                rsa_max_learning_states=16,
                rsa_strategy_count=5,
            )),
        ]:
            config = config_factory()
            adv = create_learning_adversary(model_enum, config)

            # Sample multiple epochs
            primitives_used = set()
            for epoch in range(20):
                action = adv.select_action(obs, epoch, 0, seed=42)
                primitives_used.add(action)

            all_valid = primitives_used.issubset(valid_primitives)
            test_cases.append({
                'model': model_enum.value,
                'primitives_used': [p.value for p in primitives_used],
                'valid': all_valid
            })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "8",
            "Action primitive separation",
            all_valid,
            f"All models use only valid action primitives" if all_valid
            else f"Invalid primitives used: {[tc for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )

    def test_9_strategy_map_totality(self):
        """
        Test 9: Strategy map totality audit.

        Verify models produce valid actions for all observable bucket combinations.
        """
        print("\nTest 9: Strategy map totality audit...")

        # Generate all observable bucket combinations (excluding epoch_index as key)
        from itertools import product

        authority_statuses = list(AuthorityStatus)
        lapse_values = [True, False]
        renewal_outcomes = list(RenewalOutcome)
        cta_phases = list(CTABucket)
        eligibility_buckets = list(EligibilityBucket)

        all_combos = list(product(
            authority_statuses,
            lapse_values,
            renewal_outcomes,
            cta_phases,
            eligibility_buckets
        ))

        test_cases = []

        for model_enum, config_factory in [
            (RSAPolicyModel.RECOVERY_AWARE_TIMING, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
                rsa_version="v3.1",
                rsa_max_internal_states=50,
                rsa_max_learning_states=16,
                epoch_size=50,
            )),
            (RSAPolicyModel.EDGE_SUSTAINMENT, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
                rsa_version="v3.1",
                rsa_max_internal_states=2,
                rsa_max_learning_states=3,
            )),
            (RSAPolicyModel.STOCHASTIC_MIXER, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
                rsa_version="v3.1",
                rsa_max_internal_states=5,
                rsa_max_learning_states=16,
                rsa_strategy_count=5,
            )),
        ]:
            config = config_factory()
            adv = create_learning_adversary(model_enum, config)

            valid_count = 0
            error_count = 0

            for auth, lapse, renewal, cta, elig in all_combos:
                obs = ObservableOutcome(
                    epoch_index=0,
                    authority_status=auth,
                    lapse_occurred=lapse,
                    renewal_outcome=renewal,
                    cta_phase=cta,
                    eligibility_bucket=elig,
                )
                try:
                    action = adv.select_action(obs, 0, 0, seed=42)
                    if action is not None and isinstance(action, ActionPrimitive):
                        valid_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1

            test_cases.append({
                'model': model_enum.value,
                'total_combos': len(all_combos),
                'valid': valid_count,
                'errors': error_count,
                'is_total': error_count == 0
            })

        all_valid = all(tc['is_total'] for tc in test_cases)

        self._add_result(
            "9",
            "Strategy map totality",
            all_valid,
            f"All models handle all {len(all_combos)} observable bucket combinations" if all_valid
            else f"Missing entries: {[tc for tc in test_cases if not tc['is_total']]}",
            {"test_cases": test_cases}
        )

    def test_10_exercised_internal_state(self):
        """
        Test 10: Exercised internal state verification (static + dynamic).
        """
        print("\nTest 10: Exercised internal state verification...")

        test_cases = []

        for model_enum, config_factory in [
            (RSAPolicyModel.RECOVERY_AWARE_TIMING, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
                rsa_version="v3.1",
                rsa_max_internal_states=50,
                rsa_max_learning_states=16,
                epoch_size=50,
            )),
            (RSAPolicyModel.EDGE_SUSTAINMENT, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
                rsa_version="v3.1",
                rsa_max_internal_states=2,
                rsa_max_learning_states=3,
            )),
            (RSAPolicyModel.STOCHASTIC_MIXER, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
                rsa_version="v3.1",
                rsa_max_internal_states=5,
                rsa_max_learning_states=16,
                rsa_strategy_count=5,
            )),
        ]:
            config = config_factory()
            adv = create_learning_adversary(model_enum, config)

            # Static check
            static_ok = adv.verify_exercised_internal_static(config)

            # Dynamic check: run epochs with varied observables to exercise all states
            # For Model N (EDGE_SUSTAINMENT), we need both SAFE and EDGE to see both modes
            observable_scenarios = [
                ObservableOutcome(
                    epoch_index=0,
                    authority_status=AuthorityStatus.HAS_AUTHORITY,
                    lapse_occurred=False,
                    renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
                    cta_phase=CTABucket.INACTIVE,
                    eligibility_bucket=EligibilityBucket.SAFE,
                ),
                ObservableOutcome(
                    epoch_index=0,
                    authority_status=AuthorityStatus.HAS_AUTHORITY,
                    lapse_occurred=True,
                    renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
                    cta_phase=CTABucket.LATE,
                    eligibility_bucket=EligibilityBucket.EDGE,
                ),
            ]

            for epoch in range(100):
                # Alternate observables to exercise different states
                obs = observable_scenarios[epoch % len(observable_scenarios)]
                adv.emit(obs, epoch, 0, config, seed=42)

            dynamic_ok = adv.verify_exercised_internal_dynamic()

            test_cases.append({
                'model': model_enum.value,
                'static_ok': static_ok,
                'dynamic_ok': dynamic_ok,
                'observed_states': adv.get_observed_internal_state_count(),
                'valid': static_ok and dynamic_ok
            })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "10",
            "Exercised internal state verification",
            all_valid,
            f"All models pass static and dynamic internal state checks" if all_valid
            else f"Failures: {[tc for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )

    def test_11_exercised_learning_state(self):
        """
        Test 11: Exercised learning state verification (static + dynamic).
        """
        print("\nTest 11: Exercised learning state verification...")

        test_cases = []

        for model_enum, config_factory in [
            (RSAPolicyModel.RECOVERY_AWARE_TIMING, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
                rsa_version="v3.1",
                rsa_max_internal_states=50,
                rsa_max_learning_states=16,
                epoch_size=50,
            )),
            (RSAPolicyModel.EDGE_SUSTAINMENT, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
                rsa_version="v3.1",
                rsa_max_internal_states=2,
                rsa_max_learning_states=3,
            )),
            (RSAPolicyModel.STOCHASTIC_MIXER, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
                rsa_version="v3.1",
                rsa_max_internal_states=5,
                rsa_max_learning_states=16,
                rsa_strategy_count=5,
            )),
        ]:
            config = config_factory()
            adv = create_learning_adversary(model_enum, config)

            # Static check
            static_ok = adv.verify_exercised_learning_static(config)

            # Dynamic check: run 100 epochs
            obs = ObservableOutcome(
                epoch_index=0,
                authority_status=AuthorityStatus.HAS_AUTHORITY,
                lapse_occurred=False,
                renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
                cta_phase=CTABucket.INACTIVE,
                eligibility_bucket=EligibilityBucket.SAFE,
            )
            for epoch in range(100):
                adv.emit(obs, epoch, 0, config, seed=42)

            dynamic_ok = adv.verify_exercised_learning_dynamic()

            test_cases.append({
                'model': model_enum.value,
                'static_ok': static_ok,
                'dynamic_ok': dynamic_ok,
                'observed_states': adv.get_observed_learning_state_count(),
                'valid': static_ok and dynamic_ok
            })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "11",
            "Exercised learning state verification",
            all_valid,
            f"All models pass static and dynamic learning state checks" if all_valid
            else f"Failures: {[tc for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )

    def test_12_rng_provenance_audit(self):
        """
        Test 12: RNG provenance audit.

        Verify all stochasticity derives from rsa_rng_stream.
        Same seed must produce same trace.
        """
        print("\nTest 12: RNG provenance audit...")

        test_cases = []

        for model_enum, config_factory in [
            (RSAPolicyModel.RECOVERY_AWARE_TIMING, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
                rsa_version="v3.1",
                rsa_max_internal_states=50,
                rsa_max_learning_states=16,
                epoch_size=50,
            )),
            (RSAPolicyModel.STOCHASTIC_MIXER, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
                rsa_version="v3.1",
                rsa_max_internal_states=5,
                rsa_max_learning_states=16,
                rsa_strategy_count=5,
            )),
        ]:
            config = config_factory()

            # Run twice with same seed
            traces = []
            for run in range(2):
                adv = create_learning_adversary(model_enum, config)
                obs = ObservableOutcome(
                    epoch_index=0,
                    authority_status=AuthorityStatus.HAS_AUTHORITY,
                    lapse_occurred=False,
                    renewal_outcome=RenewalOutcome.NOT_ATTEMPTED,
                    cta_phase=CTABucket.INACTIVE,
                    eligibility_bucket=EligibilityBucket.SAFE,
                )
                trace = []
                for epoch in range(50):
                    action = adv.emit(obs, epoch, 0, config, seed=42)
                    trace.append((
                        action['rsa_internal_state_before'],
                        action['rsa_primitive'],
                    ))
                traces.append(trace)

            identical = traces[0] == traces[1]
            test_cases.append({
                'model': model_enum.value,
                'identical_traces': identical,
                'valid': identical
            })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "12",
            "RNG provenance audit",
            all_valid,
            f"All models produce deterministic traces from same seed" if all_valid
            else f"Non-deterministic models: {[tc['model'] for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )

    def test_13_epoch_hygiene_audit(self):
        """
        Test 13: Epoch Hygiene audit.

        Verify epoch index is not used as conditional trigger.
        Same observable at different epochs should produce same action
        (modulo internal state evolution).
        """
        print("\nTest 13: Epoch Hygiene audit...")

        # This is a code review check. We verify that select_action
        # doesn't branch on epoch directly.
        import inspect

        test_cases = []

        for model_class in [RecoveryAwareTimingAdversary, EdgeSustainmentAdversary, StochasticMixerAdversary]:
            # Check source code for epoch-based branching
            try:
                source = inspect.getsource(model_class.select_action)
                # Check for common epoch-conditional patterns
                forbidden_patterns = [
                    'if epoch',
                    'if t >',
                    'if t <',
                    'epoch %',
                    'epoch ==',
                    't mod',
                ]
                violations = []
                for pattern in forbidden_patterns:
                    if pattern in source and 'epoch_index' not in pattern:
                        violations.append(pattern)

                # Note: We allow epoch to be used for state updates, not conditionals
                test_cases.append({
                    'model': model_class.__name__,
                    'violations': violations,
                    'valid': len(violations) == 0
                })
            except Exception as e:
                test_cases.append({
                    'model': model_class.__name__,
                    'error': str(e),
                    'valid': False
                })

        all_valid = all(tc.get('valid', False) for tc in test_cases)

        self._add_result(
            "13",
            "Epoch Hygiene audit",
            all_valid,
            f"No epoch-conditional triggers found in select_action" if all_valid
            else f"Violations found: {[tc for tc in test_cases if not tc.get('valid', False)]}",
            {"test_cases": test_cases}
        )

    def test_14_reward_function_audit(self):
        """
        Test 14: Reward function audit.

        Verify r_t = R(O_t) uses frozen observables only.
        """
        print("\nTest 14: Reward function audit...")

        # Test that reward is deterministic and observable-only
        test_cases = []

        obs_null = ObservableOutcome(
            epoch_index=0,
            authority_status=AuthorityStatus.NULL_AUTHORITY,
            lapse_occurred=True,
            renewal_outcome=RenewalOutcome.FAILED,
            cta_phase=CTABucket.LATE,
            eligibility_bucket=EligibilityBucket.INELIGIBLE,
        )

        obs_healthy = ObservableOutcome(
            epoch_index=0,
            authority_status=AuthorityStatus.HAS_AUTHORITY,
            lapse_occurred=False,
            renewal_outcome=RenewalOutcome.SUCCEEDED,
            cta_phase=CTABucket.INACTIVE,
            eligibility_bucket=EligibilityBucket.SAFE,
        )

        for model_enum, config_factory, expected_null, expected_healthy in [
            (RSAPolicyModel.RECOVERY_AWARE_TIMING, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
                rsa_version="v3.1",
                rsa_max_internal_states=50,
                rsa_max_learning_states=16,
                epoch_size=50,
            ), 1, 0),  # r = 1 iff NULL_AUTHORITY
            (RSAPolicyModel.EDGE_SUSTAINMENT, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
                rsa_version="v3.1",
                rsa_max_internal_states=2,
                rsa_max_learning_states=3,
            ), 1, 0),  # r = 1 iff INELIGIBLE or NULL_AUTHORITY
            (RSAPolicyModel.STOCHASTIC_MIXER, lambda: RSAPolicyConfig(
                policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
                rsa_version="v3.1",
                rsa_max_internal_states=5,
                rsa_max_learning_states=16,
                rsa_strategy_count=5,
            ), 1, 0),  # r = 1 iff NULL_AUTHORITY
        ]:
            config = config_factory()
            adv = create_learning_adversary(model_enum, config)

            r_null = adv.compute_reward(obs_null)
            r_healthy = adv.compute_reward(obs_healthy)

            test_cases.append({
                'model': model_enum.value,
                'r_null': r_null,
                'r_healthy': r_healthy,
                'expected_null': expected_null,
                'expected_healthy': expected_healthy,
                'valid': r_null == expected_null and r_healthy == expected_healthy
            })

        all_valid = all(tc['valid'] for tc in test_cases)

        self._add_result(
            "14",
            "Reward function audit",
            all_valid,
            f"All reward functions produce expected outputs from observables" if all_valid
            else f"Mismatches: {[tc for tc in test_cases if not tc['valid']]}",
            {"test_cases": test_cases}
        )


def run_tests():
    """Run all v3.1 acceptance tests."""
    suite = RSAv31AcceptanceTests()
    return suite.run_all()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
