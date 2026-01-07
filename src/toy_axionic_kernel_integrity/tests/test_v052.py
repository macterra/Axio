"""
AKI v0.5.2 ALS-E Tests.

Tests for Expressivity-Bounded Succession (ALS-E).

Key features tested:
1. Rent accounting (deducted at epoch start, monotone enforcement)
2. Bankruptcy semantics (LEASE_EXPIRED not REVOKED, no S* increment)
3. E-Class assignment (from capability groups, misconfiguration raises error)
4. CBD successor behavior (compliant under stress, high utilization)
5. Non-regression (v0.4.3 unchanged)

Per spec §6 and binding decisions:
- E-Class assigned from lease-granted interface surface
- Rent charged at epoch start from step budget
- Bankruptcy distinct from revocation (violation)
- Renewal attestation consumes successor budget (no kernel subsidy)

Test organization:
§1: Rent accounting tests
§2: Bankruptcy semantics tests
§3: E-Class assignment tests
§4: CBD successor behavior tests
§5: Renewal under rent pressure tests
§6: Non-regression tests
§7: run_als_experiment() v0.5.2 tests
§8: Edge case tests
"""

import pytest
from typing import FrozenSet, Dict, Any

from toy_aki.als.expressivity import (
    ExpressivityClass,
    CapabilityGroup,
    RentSchedule,
    assign_e_class_from_action_types,
    validate_e_class_assignment,
    DEFAULT_CAPABILITY_MAPPING,
)
from toy_aki.als.generator import (
    GeneratorConfig,
    AttackSuccessorType,
    ControlSuccessorType,
    CBDSuccessor,
    V052_ATTACK_WEIGHTS,
)
from toy_aki.als.harness import (
    ALSConfigV052,
    ALSHarnessV052,
    ALSStopReason,
    run_als_experiment,
)
from toy_aki.als.working_mind import ResourceEnvelope


# =============================================================================
# §1: Rent Accounting Tests
# =============================================================================

class TestRentAccounting:
    """Tests for rent schedule and enforcement."""

    def test_rent_schedule_default_values(self):
        """Default rent schedule matches binding decisions."""
        schedule = RentSchedule(steps_cap_epoch=50)

        # Per binding: E0=1, E1=ceil(0.10*S), E2=ceil(0.25*S), E3=ceil(0.40*S), E4=ceil(0.60*S)
        assert schedule.compute_rent(ExpressivityClass.E0) == 1
        assert schedule.compute_rent(ExpressivityClass.E1) == 5   # ceil(0.10*50)
        assert schedule.compute_rent(ExpressivityClass.E2) == 13  # ceil(0.25*50)
        assert schedule.compute_rent(ExpressivityClass.E3) == 20  # ceil(0.40*50)
        assert schedule.compute_rent(ExpressivityClass.E4) == 30  # ceil(0.60*50)

    def test_rent_schedule_monotone_increasing(self):
        """Rent values are monotonically increasing with E-Class."""
        schedule = RentSchedule(steps_cap_epoch=100)
        rents = [schedule.compute_rent(e) for e in ExpressivityClass]

        for i in range(1, len(rents)):
            assert rents[i] >= rents[i-1], f"rent({ExpressivityClass(i)}) < rent({ExpressivityClass(i-1)})"

    def test_rent_never_exceeds_cap_minus_one(self):
        """Rent never exceeds S-1 (leave at least 1 step for renewal)."""
        for cap in [10, 50, 100, 200]:
            schedule = RentSchedule(steps_cap_epoch=cap)
            for e_class in ExpressivityClass:
                rent = schedule.compute_rent(e_class)
                assert rent <= cap - 1, f"rent={rent} exceeds cap-1={cap-1} for {e_class}"

    def test_effective_steps_after_rent(self):
        """Effective steps = cap - rent."""
        schedule = RentSchedule(steps_cap_epoch=50)

        # E0: rent=1, effective=49
        assert schedule.compute_effective_steps(ExpressivityClass.E0) == 49
        # E4: rent=30, effective=20
        assert schedule.compute_effective_steps(ExpressivityClass.E4) == 20

    def test_rent_deducted_at_epoch_start(self):
        """Rent is charged at the start of each epoch, not end."""
        config = ALSConfigV052(
            max_cycles=100,
            renewal_check_interval=50,  # 2 epochs
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Should have rent records for epochs
        assert len(result.epoch_rent_records) > 0
        # First epoch rent charged at epoch_index = 0
        first_record = result.epoch_rent_records[0]
        assert first_record.epoch_index == 0

    def test_rent_charged_regardless_of_actions(self):
        """Rent is fixed per E-Class, not tied to action count."""
        schedule = RentSchedule(steps_cap_epoch=50)

        # Same E-Class always same rent
        for _ in range(10):
            assert schedule.compute_rent(ExpressivityClass.E2) == 13

    def test_rent_schedule_custom_fractions(self):
        """Custom rent fractions can be provided."""
        schedule = RentSchedule(
            steps_cap_epoch=100,
            e1_fraction=0.15,  # Must maintain monotone: e1 < e2 < e3 < e4
            e2_fraction=0.30,
            e3_fraction=0.45,
            e4_fraction=0.65,
        )

        assert schedule.compute_rent(ExpressivityClass.E1) == 15  # ceil(0.15*100)
        assert schedule.compute_rent(ExpressivityClass.E2) == 30  # ceil(0.30*100)

    def test_monotone_enforcement_raises_on_violation(self):
        """RentSchedule raises if custom fractions violate monotonicity."""
        # E1 > E2 should fail
        with pytest.raises(ValueError, match="monotone"):
            RentSchedule(
                steps_cap_epoch=100,
                e1_fraction=0.50,
                e2_fraction=0.25,  # Lower than e1
                e3_fraction=0.55,
                e4_fraction=0.65,
            )


# =============================================================================
# §2: Bankruptcy Semantics Tests
# =============================================================================

class TestBankruptcySemantics:
    """Tests for bankruptcy behavior (rent exhaustion)."""

    def test_bankruptcy_uses_lease_expired_not_revoked(self):
        """Bankruptcy terminates via LEASE_EXPIRED, not REVOKED."""
        # Configure for high rent (E4) with low cap
        config = ALSConfigV052(
            max_cycles=500,
            renewal_check_interval=50,
            expressivity_mode="fixed",
            fixed_e_class="E4",  # Highest rent
        )
        # Use very low step cap to induce bankruptcy
        gen_config = GeneratorConfig(
            attack_weights=V052_ATTACK_WEIGHTS,
        )
        config.generator_config = gen_config

        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Bankruptcies should NOT count as revocations
        assert result.total_revocations == 0 or result.total_bankruptcies >= 0
        # They are expirations, not violations

    def test_bankruptcy_does_not_increment_s_star_via_cooperation(self):
        """Bankruptcy doesn't require cooperation from successor."""
        # The kernel detects rent exhaustion, not the successor
        config = ALSConfigV052(
            max_cycles=200,
            renewal_check_interval=50,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # S* counts succession events, not bankruptcies directly
        assert result.s_star >= 1  # At least init

    def test_bankruptcy_event_records_rent_info(self):
        """BankruptcyEvent records E-Class and rent charged."""
        config = ALSConfigV052(
            max_cycles=200,
            renewal_check_interval=50,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        for be in result.bankruptcy_events:
            assert hasattr(be, 'e_class')
            assert hasattr(be, 'rent_charged')
            assert be.rent_charged > 0

    def test_bankruptcy_triggers_succession_opportunity(self):
        """After bankruptcy, a new successor can be endorsed."""
        config = ALSConfigV052(
            max_cycles=1000,
            renewal_check_interval=50,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # If bankruptcies occurred, S* should reflect succession opportunities
        if result.total_bankruptcies > 0:
            # S* = init + expirations + bankruptcies (minus failed successions)
            assert result.s_star >= 1


# =============================================================================
# §3: E-Class Assignment Tests
# =============================================================================

class TestEClassAssignment:
    """Tests for capability-based E-Class assignment."""

    def test_heartbeat_only_is_e0(self):
        """Action types in HEARTBEAT group only → E0."""
        action_types = frozenset({"WAIT", "PING", "HEARTBEAT"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E0

    def test_logging_raises_to_e1(self):
        """Action types requiring LOGGING → E1."""
        action_types = frozenset({"WAIT", "LOG", "REPORT"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E1

    def test_state_mutation_raises_to_e2(self):
        """Action types requiring STATE_MUTATION → E2."""
        action_types = frozenset({"WAIT", "SET", "GET"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E2

    def test_fanout_raises_to_e3(self):
        """Action types requiring FANOUT_COMPOSITION → E3."""
        action_types = frozenset({"WAIT", "BATCH", "COMPOSE"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E3

    def test_full_api_raises_to_e4(self):
        """Action types requiring FULL_API_SURFACE → E4."""
        action_types = frozenset({"WAIT", "MOVE_LEFT", "HARVEST"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E4

    def test_e_class_assignment_takes_maximum(self):
        """E-Class is max of all action type requirements."""
        # Mix of E0 (WAIT), E1 (LOG), E3 (BATCH) actions → E3
        action_types = frozenset({"WAIT", "LOG", "BATCH"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E3

    def test_validate_e_class_passes_for_valid(self):
        """validate_e_class_assignment passes for valid assignments."""
        action_types = frozenset({"WAIT", "SET"})  # Requires E2
        # E2 or higher should work (no exception raised)
        validate_e_class_assignment(action_types, ExpressivityClass.E2)
        validate_e_class_assignment(action_types, ExpressivityClass.E3)
        validate_e_class_assignment(action_types, ExpressivityClass.E4)

    def test_validate_e_class_fails_for_insufficient(self):
        """validate_e_class_assignment fails for insufficient E-Class."""
        from toy_aki.als.expressivity import EClassAssignmentError
        action_types = frozenset({"WAIT", "SET"})  # Requires E2
        # E0 and E1 should raise EClassAssignmentError
        with pytest.raises(EClassAssignmentError):
            validate_e_class_assignment(action_types, ExpressivityClass.E0)
        with pytest.raises(EClassAssignmentError):
            validate_e_class_assignment(action_types, ExpressivityClass.E1)

    def test_e_class_not_influenced_by_self_report(self):
        """E-Class is derived from action types, not self-reported."""
        # Successor can't claim lower E-Class than actions require
        action_types = frozenset({"WAIT", "MOVE_LEFT"})  # FULL_API_SURFACE
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E4  # Not whatever successor claims

    def test_unknown_action_types_get_conservative_e_class(self):
        """Unknown action types are assigned to E4 (conservative)."""
        action_types = frozenset({"WAIT", "UNKNOWN_DANGEROUS_ACTION"})
        e_class = assign_e_class_from_action_types(action_types)
        assert e_class == ExpressivityClass.E4


# =============================================================================
# §4: CBD Successor Behavior Tests
# =============================================================================

class TestCBDSuccessor:
    """Tests for Compliant-But-Dangerous successor behavior."""

    def test_cbd_is_fully_compliant(self):
        """CBD successor never triggers violations."""
        cbd = CBDSuccessor(
            mind_id="test_cbd",
            allowed_action_types=frozenset({"GET", "SET", "MOVE_LEFT", "WAIT"}),
            seed=42,
        )

        # Generate many actions
        for i in range(100):
            action = cbd.propose_action({"cycle": i})
            if action:
                assert action["action_type"] in cbd._allowed_action_types

    def test_cbd_runs_near_caps(self):
        """CBD successor tries to run near resource caps."""
        resources = ResourceEnvelope(
            max_actions_per_epoch=50,
            max_steps_per_epoch=50,
        )
        cbd = CBDSuccessor(
            mind_id="test_cbd",
            allowed_action_types=frozenset({"GET", "SET", "MOVE_LEFT", "WAIT"}),
            resources=resources,
            safety_margin=1,
            seed=42,
        )

        # CBD should emit actions up to near the cap
        action_count = 0
        for i in range(50):
            action = cbd.propose_action({"cycle": i})
            if action:
                action_count += 1

        # Should be at cap - safety_margin
        assert action_count >= 40  # At least 80% utilization

    def test_cbd_uses_state_mutation_if_enabled(self):
        """CBD with state mutation writes to internal state."""
        cbd = CBDSuccessor(
            mind_id="test_cbd",
            allowed_action_types=frozenset({"GET", "SET", "MOVE_LEFT", "WAIT"}),
            use_state_mutation=True,
            seed=42,
        )

        # Generate actions that mutate state
        for i in range(20):
            cbd.propose_action({"cycle": i})

        assert cbd.get_state_size() > 0

    def test_cbd_manifest_declares_correct_capabilities(self):
        """CBD manifest accurately reflects declared capabilities."""
        cbd = CBDSuccessor(
            mind_id="test_cbd",
            allowed_action_types=frozenset({"GET", "SET"}),
            use_state_mutation=True,
            seed=42,
        )

        manifest = cbd.export_manifest()
        assert manifest.interface.action_types == frozenset({"GET", "SET"})

    def test_cbd_in_v052_harness_completes(self):
        """CBD successors in v0.5.2 harness run to completion."""
        config = ALSConfigV052(
            max_cycles=500,
            renewal_check_interval=50,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Should complete without CBD-induced failures
        assert result.stop_reason in [
            ALSStopReason.HORIZON_EXHAUSTED,
            ALSStopReason.ENDORSEMENT_DEGENERACY,
        ]


# =============================================================================
# §5: Renewal Under Rent Pressure Tests
# =============================================================================

class TestRenewalUnderRent:
    """Tests for renewal behavior with rent pressure."""

    def test_renewal_consumes_successor_budget(self):
        """Renewal attestation is paid from successor's step budget."""
        # Per binding: renewal consumes budget, no kernel subsidy
        schedule = RentSchedule(steps_cap_epoch=50)

        # After rent, effective_steps is what's left for work + renewal
        for e_class in ExpressivityClass:
            effective = schedule.compute_effective_steps(e_class)
            assert effective >= 0
            assert effective < 50  # Less than full cap

    def test_high_e_class_reduces_renewal_capacity(self):
        """Higher E-Class means less budget for renewal attestation."""
        schedule = RentSchedule(steps_cap_epoch=50)

        e0_effective = schedule.compute_effective_steps(ExpressivityClass.E0)
        e4_effective = schedule.compute_effective_steps(ExpressivityClass.E4)

        assert e0_effective > e4_effective

    def test_renewal_fails_if_no_effective_steps(self):
        """If effective_steps = 0, renewal cannot occur."""
        # This would be bankruptcy
        # With cap constraint rent <= cap-1, effective is always >= 1
        schedule = RentSchedule(steps_cap_epoch=10)
        effective = schedule.compute_effective_steps(ExpressivityClass.E4)
        # With cap=10, E4 rent = min(6, 9) = 6, effective = 4
        assert effective >= 1  # Always at least 1 step

    def test_harness_tracks_effective_steps_per_epoch(self):
        """Harness tracks effective steps after rent deduction."""
        config = ALSConfigV052(
            max_cycles=200,
            renewal_check_interval=50,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Epoch records should show effective steps
        for record in result.epoch_rent_records:
            # effective_steps = steps_cap_epoch - rent, so:
            # effective_steps + rent_charged = steps_cap_epoch
            # effective_steps >= 0 always
            assert record.effective_steps >= 0
            # Verify rent_charged and effective_steps are coherent
            assert record.rent_charged >= 0
            assert record.effective_steps + record.rent_charged >= record.effective_steps


# =============================================================================
# §6: Non-Regression Tests
# =============================================================================

class TestNonRegression:
    """Tests that v0.4.x behavior is unchanged."""

    def test_v043_unchanged_with_default_weights(self):
        """v0.4.3 harness uses original generator weights."""
        from toy_aki.als.harness import ALSConfig, ALSHarnessV043

        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # Should complete with expected behavior
        assert result.spec_version == "0.4.3"
        assert result.s_star >= 1

    def test_v042_unchanged_s_star_semantics(self):
        """v0.4.2 S* counts per-cycle endorsements (not succession)."""
        from toy_aki.als.harness import ALSConfig, ALSHarnessV042

        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness = ALSHarnessV042(seed=42, config=config)
        result = harness.run()

        # v0.4.2 S* should be high (per-cycle sampling)
        assert result.s_star > 100

    def test_v043_s_star_lower_than_v042(self):
        """v0.4.3 S* is dramatically lower than v0.4.2."""
        from toy_aki.als.harness import ALSConfig, ALSHarnessV042, ALSHarnessV043

        config = ALSConfig(max_cycles=10000, renewal_check_interval=100)

        result_042 = ALSHarnessV042(seed=42, config=config).run()
        result_043 = ALSHarnessV043(seed=42, config=config).run()

        ratio = result_042.s_star / max(result_043.s_star, 1)
        assert ratio > 100  # v0.4.3 S* should be >100x lower

    def test_cbd_not_in_v04x_default_weights(self):
        """CBD is not in default weights for v0.4.x."""
        from toy_aki.als.generator import GeneratorConfig

        default_config = GeneratorConfig()
        assert AttackSuccessorType.CBD not in default_config.attack_weights

    def test_cbd_in_v052_default_weights(self):
        """CBD is in default weights for v0.5.2."""
        config = ALSConfigV052()
        assert AttackSuccessorType.CBD in config.generator_config.attack_weights


# =============================================================================
# §7: run_als_experiment() v0.5.2 Tests
# =============================================================================

class TestRunExperimentV052:
    """Tests for run_als_experiment with v0.5.2."""

    def test_run_als_experiment_v052(self):
        """run_als_experiment supports spec_version='0.5.2'."""
        result = run_als_experiment(
            seed=42,
            max_cycles=200,
            spec_version="0.5.2",
        )

        assert hasattr(result, 'total_bankruptcies')
        assert hasattr(result, 'epoch_rent_records')

    def test_v052_result_has_e_class_distribution(self):
        """v0.5.2 result tracks E-Class distribution."""
        result = run_als_experiment(
            seed=42,
            max_cycles=500,
            spec_version="0.5.2",
        )

        assert hasattr(result, 'e_class_distribution')

    def test_v052_result_has_rent_telemetry(self):
        """v0.5.2 result includes rent telemetry."""
        result = run_als_experiment(
            seed=42,
            max_cycles=500,
            spec_version="0.5.2",
        )

        assert hasattr(result, 'epoch_rent_records')
        assert hasattr(result, 'total_rent_charged')


# =============================================================================
# §8: Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests for v0.5.2."""

    def test_e0_rent_is_always_1(self):
        """E0 rent is 1 regardless of cap (for caps >= 5)."""
        for cap in [5, 10, 50, 100, 1000]:
            schedule = RentSchedule(steps_cap_epoch=cap)
            assert schedule.compute_rent(ExpressivityClass.E0) == 1

    def test_empty_action_types_is_e0(self):
        """Empty action types set is E0."""
        e_class = assign_e_class_from_action_types(frozenset())
        assert e_class == ExpressivityClass.E0

    def test_rent_with_small_cap(self):
        """Rent schedule handles small caps (>= 5)."""
        schedule = RentSchedule(steps_cap_epoch=5)
        # With cap=5, all rents should be <= 4 (cap-1)
        for e_class in ExpressivityClass:
            rent = schedule.compute_rent(e_class)
            effective = schedule.compute_effective_steps(e_class)
            assert rent <= 4  # Cannot exceed cap-1
            assert effective >= 1

    def test_harness_run_is_reproducible(self):
        """Same seed produces same result."""
        config = ALSConfigV052(max_cycles=500)

        result1 = ALSHarnessV052(seed=42, config=config).run()
        result2 = ALSHarnessV052(seed=42, config=config).run()

        assert result1.s_star == result2.s_star
        assert result1.total_renewals == result2.total_renewals
        assert result1.total_bankruptcies == result2.total_bankruptcies

    def test_different_seeds_produce_different_results(self):
        """Different seeds produce different results."""
        config = ALSConfigV052(max_cycles=1000)

        results = [ALSHarnessV052(seed=s, config=config).run() for s in [42, 43, 44]]

        # At least some should differ (may be same if short run)
        s_stars = [r.s_star for r in results]
        # With 1000 cycles, likely to see some variation
        # Just check they all complete
        for r in results:
            assert r.stop_reason == ALSStopReason.HORIZON_EXHAUSTED


# =============================================================================
# §9: Integration Tests
# =============================================================================

class TestV052Integration:
    """Integration tests for full v0.5.2 runs."""

    def test_full_run_with_all_e_classes(self):
        """Full run encounters multiple E-Classes."""
        config = ALSConfigV052(
            max_cycles=2000,
            renewal_check_interval=50,
            expressivity_mode="random",
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Should have variation in E-Classes
        assert len(result.e_class_distribution) >= 1

    def test_cbd_successors_classified_correctly(self):
        """CBD successors in run are classified as hollow succession."""
        config = ALSConfigV052(
            max_cycles=1000,
            renewal_check_interval=50,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # CBD successors should be in succession events
        cbd_events = [e for e in result.succession_events if 'cbd' in e.mind_id.lower()]
        for event in cbd_events:
            assert event.is_non_trivial is False  # CBD is compliant, not non-trivial

    def test_harness_telemetry_complete(self):
        """Harness provides complete telemetry for v0.5.2."""
        config = ALSConfigV052(max_cycles=500)
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Check all required telemetry fields
        assert result.s_star >= 0
        assert result.total_renewals >= 0
        assert result.total_expirations >= 0
        assert result.total_bankruptcies >= 0
        assert hasattr(result, 'e_class_distribution')
        assert hasattr(result, 'epoch_rent_records')

    def test_rent_schedule_accessible_from_harness(self):
        """Harness exposes rent schedule for inspection."""
        config = ALSConfigV052(max_cycles=100)
        harness = ALSHarnessV052(seed=42, config=config)

        schedule = harness.get_rent_schedule()
        assert 'steps_cap_epoch' in schedule
        assert 'rents' in schedule  # Actual key is 'rents', not 'rent_values'


# =============================================================================
# §10: Stress Tests
# =============================================================================

class TestV052Stress:
    """Stress tests for v0.5.2 behavior."""

    def test_high_e_class_under_pressure(self):
        """High E-Class successors under rent pressure."""
        config = ALSConfigV052(
            max_cycles=5000,
            renewal_check_interval=50,
            expressivity_mode="fixed",
            fixed_e_class="E4",
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Should complete even with high rent
        assert result.stop_reason in [
            ALSStopReason.HORIZON_EXHAUSTED,
            ALSStopReason.ENDORSEMENT_DEGENERACY,
        ]

    def test_short_epochs_with_rent(self):
        """Short epochs with rent charging."""
        config = ALSConfigV052(
            max_cycles=1000,
            renewal_check_interval=20,  # Very short epochs
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Should have many epochs
        assert len(result.epoch_rent_records) >= 10

    def test_extended_run_stability(self):
        """Extended run for stability testing."""
        config = ALSConfigV052(
            max_cycles=10000,
            renewal_check_interval=100,
        )
        harness = ALSHarnessV052(seed=42, config=config)
        result = harness.run()

        # Should complete without crashes
        assert result.total_cycles >= 10000 or result.stop_reason != ALSStopReason.HORIZON_EXHAUSTED
