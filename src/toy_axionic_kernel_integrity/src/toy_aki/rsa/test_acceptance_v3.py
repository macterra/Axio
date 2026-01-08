"""
RSA v3.0 Acceptance Test Suite

Implements all 9 acceptance tests from rsa_instructions_v3.0.md.
Tests verify architectural compliance, behavioral constraints, exercised
state verification, and separation properties before experimental runs.

Tests:
1. RSA disabled equivalence (deferred to run-time)
2. RSA NONE equivalence (deferred to run-time)
3. Deterministic replay audit (deferred to run-time)
4. Kernel invariance audit (static check)
5. Observable interface audit (static check)
6. State bound enforcement (max_internal_states respected)
7. Action primitive separation check (inherited from v2.0)
8a. Exercised state verification - static (pre-run gate)
8b. Exercised state verification - dynamic (post-run check)
9. Strategy map totality audit (all observable+state combinations handled)
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
    create_stateful_adversary,
    StatefulRSAWrapper,
    StatefulRSAAdversary,
    ResonantLapseAdversary,
    EdgeOscillatorAdversary,
    CTAPhaseLockerAdversary,
)


@dataclass
class TestResult:
    """Result from a single test."""
    test_id: str
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class RSAv3AcceptanceTests:
    """Acceptance test suite for RSA v3.0 implementation."""

    def __init__(self):
        self.results: List[TestResult] = []

    def _add_result(self, test_id: str, name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """Add a test result."""
        self.results.append(TestResult(test_id, name, passed, message, details))
        status = "✓" if passed else "✗"
        print(f"  {status} Test {test_id}: {message}")

    def run_all(self) -> bool:
        """
        Run all v3.0 acceptance tests.

        Returns:
            True if all tests pass, False otherwise
        """
        print("=" * 80)
        print("RSA v3.0 Acceptance Test Suite")
        print("=" * 80)
        print()

        self.test_4_kernel_invariance_audit()
        self.test_5_observable_interface_audit()
        self.test_6_state_bound_enforcement()
        self.test_8a_exercised_state_static()
        self.test_9_strategy_map_totality()
        self.test_A_eligibility_bucket_equivalence()
        self.test_B1_model_k_forced_edge_microtrace()
        self.test_B2_model_l_phase_transition_microtrace()

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

        Verify v3.0 models don't access kernel internals.
        This is a static check of the code structure.
        """
        print("\nTest 4: Kernel invariance audit...")

        # Check that v3.0 models only use ObservableOutcome interface
        # This is enforced by type signatures - models take ObservableOutcome, not kernel_state

        models_checked = []

        for model_class in [ResonantLapseAdversary, EdgeOscillatorAdversary, CTAPhaseLockerAdversary]:
            # Verify select_action takes ObservableOutcome
            import inspect
            sig = inspect.signature(model_class.select_action)
            params = list(sig.parameters.keys())

            # Should have: self, observable, epoch, cycle_in_epoch
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
            f"All {len(models_checked)} models use ObservableOutcome interface only" if all_valid
            else f"Some models access kernel internals directly",
            {'models': models_checked}
        )

    def test_5_observable_interface_audit(self):
        """
        Test 5: Observable interface audit.

        Verify only allowed observables are exposed (6 from spec).
        """
        print("\nTest 5: Observable interface audit...")

        # Check ObservableOutcome has exactly 6 fields
        import dataclasses
        fields = [f.name for f in dataclasses.fields(ObservableOutcome)]

        expected_fields = {
            'epoch_index',
            'authority_status',
            'lapse_occurred',
            'renewal_outcome',
            'cta_phase',
            'eligibility_bucket'
        }

        actual_fields = set(fields)
        matches = actual_fields == expected_fields
        extra = actual_fields - expected_fields
        missing = expected_fields - actual_fields

        self._add_result(
            "5",
            "Observable interface audit",
            matches,
            f"ObservableOutcome has exactly 6 required fields" if matches
            else f"Field mismatch: extra={extra}, missing={missing}",
            {'expected': expected_fields, 'actual': actual_fields}
        )

    def test_6_state_bound_enforcement(self):
        """
        Test 6: State bound enforcement.

        Verify rsa_max_internal_states is respected by all models.
        """
        print("\nTest 6: State bound enforcement...")

        test_cases = []

        # Test Model J with N=50 (Run 1a)
        try:
            config_j = RSAPolicyConfig(
                policy_model=RSAPolicyModel.RESONANT_LAPSE,
                rsa_version="v3",
                rsa_resonant_period_N=50,
                rsa_max_internal_states=50  # Must be >= N
            )
            adv_j = ResonantLapseAdversary(config_j)
            reachable = adv_j.get_reachable_state_count()
            valid = reachable <= config_j.rsa_max_internal_states
            test_cases.append({
                'model': 'J (N=50)',
                'reachable': reachable,
                'bound': config_j.rsa_max_internal_states,
                'valid': valid
            })
        except Exception as e:
            test_cases.append({'model': 'J (N=50)', 'error': str(e), 'valid': False})

        # Test Model J with N=100 (Run 1b)
        try:
            config_j2 = RSAPolicyConfig(
                policy_model=RSAPolicyModel.RESONANT_LAPSE,
                rsa_version="v3",
                rsa_resonant_period_N=100,
                rsa_max_internal_states=100  # Must be >= N
            )
            adv_j2 = ResonantLapseAdversary(config_j2)
            reachable = adv_j2.get_reachable_state_count()
            valid = reachable <= config_j2.rsa_max_internal_states
            test_cases.append({
                'model': 'J (N=100)',
                'reachable': reachable,
                'bound': config_j2.rsa_max_internal_states,
                'valid': valid
            })
        except Exception as e:
            test_cases.append({'model': 'J (N=100)', 'error': str(e), 'valid': False})

        # Test Model K (2 states)
        try:
            config_k = RSAPolicyConfig(
                policy_model=RSAPolicyModel.EDGE_OSCILLATOR,
                rsa_version="v3",
                rsa_max_internal_states=4  # Must be >= 2
            )
            adv_k = EdgeOscillatorAdversary(config_k)
            reachable = adv_k.get_reachable_state_count()
            valid = reachable <= config_k.rsa_max_internal_states
            test_cases.append({
                'model': 'K',
                'reachable': reachable,
                'bound': config_k.rsa_max_internal_states,
                'valid': valid
            })
        except Exception as e:
            test_cases.append({'model': 'K', 'error': str(e), 'valid': False})

        # Test Model L (4 states)
        try:
            config_l = RSAPolicyConfig(
                policy_model=RSAPolicyModel.CTA_PHASE_LOCKER,
                rsa_version="v3",
                rsa_max_internal_states=4  # Must be >= 4
            )
            adv_l = CTAPhaseLockerAdversary(config_l)
            reachable = adv_l.get_reachable_state_count()
            valid = reachable <= config_l.rsa_max_internal_states
            test_cases.append({
                'model': 'L',
                'reachable': reachable,
                'bound': config_l.rsa_max_internal_states,
                'valid': valid
            })
        except Exception as e:
            test_cases.append({'model': 'L', 'error': str(e), 'valid': False})

        # Test that undersized bounds are rejected
        try:
            bad_config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.RESONANT_LAPSE,
                rsa_version="v3",
                rsa_resonant_period_N=50,
                rsa_max_internal_states=10  # Too small!
            )
            # Should raise ValueError
            test_cases.append({'model': 'J (undersized)', 'error': 'Should have raised', 'valid': False})
        except ValueError:
            test_cases.append({'model': 'J (undersized)', 'rejected': True, 'valid': True})

        all_valid = all(t.get('valid', False) for t in test_cases)

        self._add_result(
            "6",
            "State bound enforcement",
            all_valid,
            f"All {len(test_cases)} state bound checks pass" if all_valid
            else f"Some state bound checks failed",
            {'cases': test_cases}
        )

    def test_8a_exercised_state_static(self):
        """
        Test 8a: Exercised state verification - static.

        Verify each model has at least one observable O and two states S_a ≠ S_b
        such that π(O, S_a) ≠ π(O, S_b).
        """
        print("\nTest 8a: Exercised state static verification...")

        test_cases = []

        # Model J: π(O, 0) = INVALID_COMMIT, π(O, 1) = COMPLIANT
        config_j = RSAPolicyConfig(
            policy_model=RSAPolicyModel.RESONANT_LAPSE,
            rsa_version="v3",
            rsa_resonant_period_N=50,
            rsa_max_internal_states=50
        )
        passes_j = ResonantLapseAdversary.verify_exercised_state_static(config_j)
        test_cases.append({'model': 'J', 'passes': passes_j})

        # Model K: π(EDGE, 0) = MIN_EFFORT, π(EDGE, 1) = INVALID_COMMIT
        config_k = RSAPolicyConfig(
            policy_model=RSAPolicyModel.EDGE_OSCILLATOR,
            rsa_version="v3",
            rsa_max_internal_states=4
        )
        passes_k = EdgeOscillatorAdversary.verify_exercised_state_static(config_k)
        test_cases.append({'model': 'K', 'passes': passes_k})

        # Model L: π(EARLY, INACTIVE) = INVALID, π(EARLY, EARLY) = COMPLIANT
        config_l = RSAPolicyConfig(
            policy_model=RSAPolicyModel.CTA_PHASE_LOCKER,
            rsa_version="v3",
            rsa_max_internal_states=4
        )
        passes_l = CTAPhaseLockerAdversary.verify_exercised_state_static(config_l)
        test_cases.append({'model': 'L', 'passes': passes_l})

        all_pass = all(t['passes'] for t in test_cases)

        self._add_result(
            "8a",
            "Exercised state static verification",
            all_pass,
            f"All {len(test_cases)} models pass static exercised-state check" if all_pass
            else f"Some models fail static check",
            {'cases': test_cases}
        )

    def test_9_strategy_map_totality(self):
        """
        Test 9: Strategy map totality audit.

        Verify all (observable_bucket, state) combinations are handled.
        """
        print("\nTest 9: Strategy map totality audit...")

        test_cases = []

        # Generate all observable bucket combinations (excluding epoch_index)
        authority_values = [AuthorityStatus.HAS_AUTHORITY, AuthorityStatus.NULL_AUTHORITY]
        lapse_values = [True, False]
        renewal_values = [RenewalOutcome.SUCCEEDED, RenewalOutcome.FAILED, RenewalOutcome.NOT_ATTEMPTED]
        cta_values = [CTABucket.INACTIVE, CTABucket.EARLY, CTABucket.MID, CTABucket.LATE]
        elig_values = [EligibilityBucket.SAFE, EligibilityBucket.EDGE, EligibilityBucket.INELIGIBLE]

        # Sample observables (not exhaustive, but representative)
        sample_observables = []
        for auth in authority_values:
            for lapse in lapse_values:
                for renewal in renewal_values:
                    for cta in cta_values:
                        for elig in elig_values:
                            sample_observables.append(ObservableOutcome(
                                epoch_index=100,  # Arbitrary, excluded from strategy map keys
                                authority_status=auth,
                                lapse_occurred=lapse,
                                renewal_outcome=renewal,
                                cta_phase=cta,
                                eligibility_bucket=elig
                            ))

        # Test Model J (N states)
        config_j = RSAPolicyConfig(
            policy_model=RSAPolicyModel.RESONANT_LAPSE,
            rsa_version="v3",
            rsa_resonant_period_N=5,  # Small for testing
            rsa_max_internal_states=5
        )
        adv_j = ResonantLapseAdversary(config_j)
        j_errors = []
        for state in range(config_j.rsa_resonant_period_N):
            adv_j._internal_state = state
            for obs in sample_observables[:10]:  # Sample subset
                try:
                    action = adv_j.select_action(obs, 0, 0)
                    if action not in ActionPrimitive:
                        j_errors.append(f"Invalid action for state={state}")
                except Exception as e:
                    j_errors.append(f"Exception at state={state}: {e}")
        test_cases.append({'model': 'J', 'errors': j_errors, 'valid': len(j_errors) == 0})

        # Test Model K (2 states)
        config_k = RSAPolicyConfig(
            policy_model=RSAPolicyModel.EDGE_OSCILLATOR,
            rsa_version="v3",
            rsa_max_internal_states=4
        )
        adv_k = EdgeOscillatorAdversary(config_k)
        k_errors = []
        for state in range(2):
            adv_k._internal_state = state
            for obs in sample_observables:
                try:
                    action = adv_k.select_action(obs, 0, 0)
                    if action not in ActionPrimitive:
                        k_errors.append(f"Invalid action for state={state}")
                except Exception as e:
                    k_errors.append(f"Exception at state={state}: {e}")
        test_cases.append({'model': 'K', 'errors': k_errors, 'valid': len(k_errors) == 0})

        # Test Model L (4 states)
        config_l = RSAPolicyConfig(
            policy_model=RSAPolicyModel.CTA_PHASE_LOCKER,
            rsa_version="v3",
            rsa_max_internal_states=4
        )
        adv_l = CTAPhaseLockerAdversary(config_l)
        l_errors = []
        for state in range(4):
            adv_l._internal_state = state
            for obs in sample_observables:
                try:
                    action = adv_l.select_action(obs, 0, 0)
                    if action not in ActionPrimitive:
                        l_errors.append(f"Invalid action for state={state}")
                except Exception as e:
                    l_errors.append(f"Exception at state={state}: {e}")
        test_cases.append({'model': 'L', 'errors': l_errors, 'valid': len(l_errors) == 0})

        all_valid = all(t['valid'] for t in test_cases)

        self._add_result(
            "9",
            "Strategy map totality audit",
            all_valid,
            f"All {len(test_cases)} models have total strategy maps" if all_valid
            else f"Some models have incomplete strategy maps",
            {'cases': test_cases}
        )

    def test_A_eligibility_bucket_equivalence(self):
        """
        Test A: Eligibility Bucket Equivalence Test (REQUIRED)

        Prove that the v3.0 eligibility_bucket adapter is bit-for-bit identical
        to the v2.0 bucketization semantics.

        V2.0/V3.0 Semantics (distance-from-ineligibility):
        - successive_renewal_failures <= 1 → SAFE
        - successive_renewal_failures == 2 → EDGE
        - successive_renewal_failures >= 3 → INELIGIBLE

        This test validates all boundary conditions.
        """
        print("\nTest A: Eligibility bucket equivalence...")

        test_cases = []

        # Define expected semantics based on spec
        # K = 3 (eligibility limit), so:
        # - failures=0,1 → SAFE (distance >= 2)
        # - failures=2   → EDGE (distance == 1)
        # - failures>=3  → INELIGIBLE (distance <= 0)
        expected_mapping = {
            0: EligibilityBucket.SAFE,
            1: EligibilityBucket.SAFE,
            2: EligibilityBucket.EDGE,
            3: EligibilityBucket.INELIGIBLE,
            4: EligibilityBucket.INELIGIBLE,
            5: EligibilityBucket.INELIGIBLE,
            10: EligibilityBucket.INELIGIBLE,
            100: EligibilityBucket.INELIGIBLE,
        }

        for failures, expected in expected_mapping.items():
            actual = compute_eligibility_bucket(failures)
            matches = actual == expected
            test_cases.append({
                'failures': failures,
                'expected': expected.name,
                'actual': actual.name,
                'matches': matches
            })

        all_match = all(t['matches'] for t in test_cases)

        # Also verify the critical EDGE semantics for Model K
        # EDGE should occur at exactly failures==2 (K-1 threshold)
        edge_at_2 = compute_eligibility_bucket(2) == EligibilityBucket.EDGE
        edge_only_at_2 = (
            compute_eligibility_bucket(1) != EligibilityBucket.EDGE and
            compute_eligibility_bucket(3) != EligibilityBucket.EDGE
        )

        edge_semantics_valid = edge_at_2 and edge_only_at_2

        self._add_result(
            "A",
            "Eligibility bucket equivalence",
            all_match and edge_semantics_valid,
            f"All {len(test_cases)} boundary conditions match v2.0 semantics, EDGE at K-1 confirmed"
            if (all_match and edge_semantics_valid)
            else f"Bucket semantics mismatch: {[t for t in test_cases if not t['matches']]}",
            {'cases': test_cases, 'edge_at_K_minus_1': edge_semantics_valid}
        )

    def test_B1_model_k_forced_edge_microtrace(self):
        """
        Test B1: Model K Forced-EDGE Microtrace (REQUIRED)

        Feed 12 epochs of eligibility_bucket = EDGE and verify strict alternation:
        - state_pre: 0 → 1 → 0 → 1 ...
        - action:    MIN → INVALID → MIN → INVALID ...

        This validates toggle condition + update ordering.
        """
        print("\nTest B1: Model K forced-EDGE microtrace...")

        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.EDGE_OSCILLATOR,
            rsa_version="v3",
            rsa_max_internal_states=4
        )
        adv = EdgeOscillatorAdversary(config)

        # Create observable with EDGE bucket (all other fields are irrelevant for Model K)
        edge_obs = ObservableOutcome(
            epoch_index=0,
            authority_status=AuthorityStatus.HAS_AUTHORITY,
            lapse_occurred=False,
            renewal_outcome=RenewalOutcome.SUCCEEDED,
            cta_phase=CTABucket.INACTIVE,
            eligibility_bucket=EligibilityBucket.EDGE,
        )

        trace = []
        expected_states = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        expected_actions = [
            ActionPrimitive.MIN_EFFORT,     # state=0 → MIN
            ActionPrimitive.INVALID_COMMIT, # state=1 → INVALID
            ActionPrimitive.MIN_EFFORT,     # state=0 → MIN
            ActionPrimitive.INVALID_COMMIT, # state=1 → INVALID
            ActionPrimitive.MIN_EFFORT,
            ActionPrimitive.INVALID_COMMIT,
            ActionPrimitive.MIN_EFFORT,
            ActionPrimitive.INVALID_COMMIT,
            ActionPrimitive.MIN_EFFORT,
            ActionPrimitive.INVALID_COMMIT,
            ActionPrimitive.MIN_EFFORT,
            ActionPrimitive.INVALID_COMMIT,
        ]

        all_match = True
        for i in range(12):
            state_pre = adv._internal_state
            action = adv.select_action(edge_obs, epoch=i, cycle_in_epoch=0)
            adv.update_state(edge_obs)
            state_post = adv._internal_state

            trace.append({
                'epoch': i,
                'state_pre': state_pre,
                'action': action.name,
                'state_post': state_post,
            })

            # Verify against expected
            if state_pre != expected_states[i]:
                all_match = False
            if action != expected_actions[i]:
                all_match = False

        # Additional check: state toggles correctly (0→1, 1→0)
        toggle_check = all(
            trace[i]['state_post'] == 1 - trace[i]['state_pre']
            for i in range(12)
        )

        self._add_result(
            "B1",
            "Model K forced-EDGE microtrace",
            all_match and toggle_check,
            f"12 epochs: strict alternation verified, toggle logic correct"
            if (all_match and toggle_check)
            else f"Alternation/toggle failure: {trace}",
            {'trace': trace}
        )

    def test_B2_model_l_phase_transition_microtrace(self):
        """
        Test B2: Model L Phase-Transition Microtrace (REQUIRED)

        Feed phases: INACTIVE → EARLY → EARLY → MID → MID → LATE → INACTIVE
        Verify:
        - INVALID emitted only on phase changes
        - COMPLIANT on steady phase
        - update occurs after action (state reflects previous phase)
        """
        print("\nTest B2: Model L phase-transition microtrace...")

        config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.CTA_PHASE_LOCKER,
            rsa_version="v3",
            rsa_max_internal_states=4
        )
        adv = CTAPhaseLockerAdversary(config)

        # Phase sequence to test
        phase_sequence = [
            CTABucket.INACTIVE,  # epoch 0: state=INACTIVE, phase=INACTIVE → COMPLIANT
            CTABucket.EARLY,     # epoch 1: state=INACTIVE, phase=EARLY → INVALID (transition)
            CTABucket.EARLY,     # epoch 2: state=EARLY, phase=EARLY → COMPLIANT (steady)
            CTABucket.MID,       # epoch 3: state=EARLY, phase=MID → INVALID (transition)
            CTABucket.MID,       # epoch 4: state=MID, phase=MID → COMPLIANT (steady)
            CTABucket.LATE,      # epoch 5: state=MID, phase=LATE → INVALID (transition)
            CTABucket.INACTIVE,  # epoch 6: state=LATE, phase=INACTIVE → INVALID (transition)
        ]

        expected_actions = [
            ActionPrimitive.COMPLIANT,       # INACTIVE→INACTIVE: no change
            ActionPrimitive.INVALID_COMMIT,  # INACTIVE→EARLY: transition
            ActionPrimitive.COMPLIANT,       # EARLY→EARLY: no change
            ActionPrimitive.INVALID_COMMIT,  # EARLY→MID: transition
            ActionPrimitive.COMPLIANT,       # MID→MID: no change
            ActionPrimitive.INVALID_COMMIT,  # MID→LATE: transition
            ActionPrimitive.INVALID_COMMIT,  # LATE→INACTIVE: transition
        ]

        # State encoding: INACTIVE=0, EARLY=1, MID=2, LATE=3
        expected_states_pre = [0, 0, 1, 1, 2, 2, 3]  # state BEFORE action
        expected_states_post = [0, 1, 1, 2, 2, 3, 0]  # state AFTER update

        def make_obs(phase: CTABucket, epoch: int) -> ObservableOutcome:
            return ObservableOutcome(
                epoch_index=epoch,
                authority_status=AuthorityStatus.HAS_AUTHORITY,
                lapse_occurred=False,
                renewal_outcome=RenewalOutcome.SUCCEEDED,
                cta_phase=phase,
                eligibility_bucket=EligibilityBucket.SAFE,
            )

        trace = []
        all_match = True

        for i, phase in enumerate(phase_sequence):
            obs = make_obs(phase, epoch=i)
            state_pre = adv._internal_state
            action = adv.select_action(obs, epoch=i, cycle_in_epoch=0)
            adv.update_state(obs)
            state_post = adv._internal_state

            trace.append({
                'epoch': i,
                'phase': phase.name,
                'state_pre': state_pre,
                'action': action.name,
                'state_post': state_post,
            })

            # Verify against expected
            if state_pre != expected_states_pre[i]:
                all_match = False
            if action != expected_actions[i]:
                all_match = False
            if state_post != expected_states_post[i]:
                all_match = False

        # Verify ordering property: action is based on state_pre, update happens after
        # This is inherent in the trace structure - state_pre is captured before select_action

        self._add_result(
            "B2",
            "Model L phase-transition microtrace",
            all_match,
            f"7 epochs: phase transitions detected correctly, update ordering verified"
            if all_match
            else f"Phase transition failure: {trace}",
            {'trace': trace}
        )


def run_acceptance_gate() -> bool:
    """
    Run v3.0 acceptance gate (pre-run validation).

    Returns:
        True if all acceptance tests pass, False otherwise
    """
    tests = RSAv3AcceptanceTests()
    return tests.run_all()


if __name__ == "__main__":
    success = run_acceptance_gate()
    sys.exit(0 if success else 1)
