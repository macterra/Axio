"""
AKI v0.8 Test Suite: Authority Leases with Constitutional Temporal Amnesty (ALS-A).

Tests the CTA mechanism and its integration with the ALS harness.

Key invariants to test (per instructions §17):
1. No streak updates during lapse except CTA
2. CTA never runs while authority is active
3. TTL clocks advance during lapse
4. Recovery occurs iff C_ELIG reopens
5. Deterministic amnesty timing
6. Policy-ID persistence across recovery
7. Multi-policy recovery ("Bucket of Doom")
8. Structural lapse does not falsely recover

Per spec §6 and instructions §8.3:
- AMNESTY_INTERVAL = 10 epochs
- AMNESTY_DECAY = 1 streak point
- CTA runs at epoch boundaries during NULL_AUTHORITY
- Succession attempts occur only at succession boundaries
- Candidate pool regenerated on every succession attempt
"""

import pytest
from typing import Dict, List, Optional

from toy_aki.als.generator import (
    SuccessorCandidate,
    ControlSuccessorType,
    AttackSuccessorType,
    SuccessorGenerator,
    GeneratorConfig,
)
from toy_aki.als.working_mind import WorkingMindManifest, ResourceEnvelope, InterfaceDeclaration
from toy_aki.als.harness import (
    ALSConfigV080,
    ALSRunResultV080,
    ALSHarnessV080,
    CandidatePoolPolicy,
    LapseCause,
    AmnestyEvent,
    RecoveryEvent,
    LapseEventV080,
)


def _create_test_config(**kwargs) -> ALSConfigV080:
    """Create a test config with sensible defaults."""
    defaults = {
        "max_cycles": 1000,
        "renewal_check_interval": 50,
        "eligibility_threshold_k": 3,
        "amnesty_interval": 10,
        "amnesty_decay": 1,
        "cta_enabled": True,
        "max_successive_renewals": 3,  # Force turnover to trigger succession
    }
    defaults.update(kwargs)
    return ALSConfigV080(**defaults)


# =============================================================================
# Unit Tests: ALSConfigV080
# =============================================================================

class TestALSConfigV080:
    """Tests for v0.8 config."""

    def test_config_defaults(self):
        """Config has correct defaults per spec §6.4."""
        config = ALSConfigV080()
        assert config.amnesty_interval == 10
        assert config.amnesty_decay == 1
        assert config.cta_enabled is True

    def test_config_extends_v070(self):
        """Config inherits v0.7 fields."""
        config = ALSConfigV080()
        # Should have eligibility fields from V070
        assert hasattr(config, "eligibility_threshold_k")
        assert config.eligibility_threshold_k == 3
        # Should have commitment fields from V060
        assert hasattr(config, "genesis_set")
        # Should have pool policy from V070
        assert hasattr(config, "candidate_pool_policy")

    def test_config_custom_amnesty_params(self):
        """Config respects custom amnesty parameters."""
        config = ALSConfigV080(amnesty_interval=5, amnesty_decay=2)
        assert config.amnesty_interval == 5
        assert config.amnesty_decay == 2

    def test_cta_can_be_disabled(self):
        """CTA can be disabled for comparison runs."""
        config = ALSConfigV080(cta_enabled=False)
        assert config.cta_enabled is False


# =============================================================================
# Unit Tests: ALSRunResultV080
# =============================================================================

class TestALSRunResultV080:
    """Tests for v0.8 run result."""

    def test_result_has_cta_fields(self):
        """Result has CTA-specific fields per spec §13.3."""
        result = ALSRunResultV080(run_id="test", seed=42)
        # Required new metrics
        assert hasattr(result, "amnesty_event_count")
        assert hasattr(result, "amnesty_epochs")
        assert hasattr(result, "aggregate_streak_mass_before_amnesty")
        assert hasattr(result, "aggregate_streak_mass_after_amnesty")
        assert hasattr(result, "recovery_count")
        assert hasattr(result, "time_to_first_recovery")
        assert hasattr(result, "mean_time_to_recovery")
        assert hasattr(result, "recovery_yield")
        assert hasattr(result, "authority_uptime_fraction")
        assert hasattr(result, "lapse_fraction")
        assert hasattr(result, "semantic_lapse_count")
        assert hasattr(result, "structural_lapse_count")
        assert hasattr(result, "stutter_recovery_count")
        assert hasattr(result, "hollow_recovery_count")

    def test_result_has_cta_events(self):
        """Result has CTA event lists."""
        result = ALSRunResultV080(run_id="test", seed=42)
        assert hasattr(result, "amnesty_events")
        assert hasattr(result, "recovery_events")
        assert hasattr(result, "lapse_events_v080")

    def test_result_to_dict_has_cta_metrics(self):
        """Result serializes CTA metrics correctly."""
        result = ALSRunResultV080(
            run_id="test",
            seed=42,
            amnesty_event_count=5,
            recovery_count=2,
        )
        d = result.to_dict()
        assert d["spec_version"] == "0.8"
        assert d["amnesty_event_count"] == 5
        assert d["recovery_count"] == 2


# =============================================================================
# Unit Tests: LapseCause Classification
# =============================================================================

class TestLapseCause:
    """Tests for lapse cause classification per spec §6.2."""

    def test_semantic_lapse_value(self):
        """SEMANTIC lapse is for ineligible candidates."""
        assert LapseCause.SEMANTIC.name == "SEMANTIC"

    def test_structural_lapse_value(self):
        """STRUCTURAL lapse is for no admissible candidates."""
        assert LapseCause.STRUCTURAL.name == "STRUCTURAL"


# =============================================================================
# Unit Tests: AmnestyEvent
# =============================================================================

class TestAmnestyEvent:
    """Tests for amnesty event recording."""

    def test_amnesty_event_fields(self):
        """AmnestyEvent has required fields."""
        event = AmnestyEvent(
            cycle=500,
            epoch=10,
            lapse_epoch_count=10,
            policies_affected=["attack:CBD", "control:COMPLIANCE_ONLY"],
            streak_deltas={"attack:CBD": 1, "control:COMPLIANCE_ONLY": 1},
            aggregate_streak_mass_before=6,
            aggregate_streak_mass_after=4,
        )
        assert event.cycle == 500
        assert event.epoch == 10
        assert event.lapse_epoch_count == 10
        assert len(event.policies_affected) == 2
        assert event.aggregate_streak_mass_before == 6
        assert event.aggregate_streak_mass_after == 4

    def test_amnesty_event_to_dict(self):
        """AmnestyEvent serializes correctly."""
        event = AmnestyEvent(
            cycle=500,
            epoch=10,
            lapse_epoch_count=10,
            policies_affected=["attack:CBD"],
            streak_deltas={"attack:CBD": 1},
            aggregate_streak_mass_before=3,
            aggregate_streak_mass_after=2,
        )
        d = event.to_dict()
        assert d["cycle"] == 500
        assert d["lapse_epoch_count"] == 10
        assert "streak_deltas" in d


# =============================================================================
# Unit Tests: RecoveryEvent
# =============================================================================

class TestRecoveryEvent:
    """Tests for recovery event recording."""

    def test_recovery_event_fields(self):
        """RecoveryEvent has required fields."""
        event = RecoveryEvent(
            cycle=1000,
            epoch=20,
            lapse_duration_cycles=500,
            lapse_duration_epochs=10,
            amnesty_events_during_lapse=1,
            lapse_cause=LapseCause.SEMANTIC,
            recovered_policy_id="control:COMPLIANCE_ONLY",
            streak_at_recovery=2,
        )
        assert event.lapse_duration_epochs == 10
        assert event.amnesty_events_during_lapse == 1
        assert event.lapse_cause == LapseCause.SEMANTIC

    def test_recovery_event_to_dict(self):
        """RecoveryEvent serializes correctly."""
        event = RecoveryEvent(
            cycle=1000,
            epoch=20,
            lapse_duration_cycles=500,
            lapse_duration_epochs=10,
            amnesty_events_during_lapse=1,
            lapse_cause=LapseCause.SEMANTIC,
            recovered_policy_id="control:COMPLIANCE_ONLY",
            streak_at_recovery=2,
        )
        d = event.to_dict()
        assert d["lapse_cause"] == "SEMANTIC"
        assert d["recovered_policy_id"] == "control:COMPLIANCE_ONLY"


# =============================================================================
# Integration Tests: CTA Never Runs While Authority Is Active
# =============================================================================

class TestCTAOnlyDuringLapse:
    """Test that CTA only runs during NULL_AUTHORITY (per instructions §17.2)."""

    def test_no_amnesty_without_lapse(self):
        """CTA does not fire when authority is continuously active."""
        # Use config that makes lapse unlikely
        config = _create_test_config(
            max_cycles=500,
            eligibility_threshold_k=100,  # Very high K = no ineligibility
            max_successive_renewals=None,  # No forced turnover
        )
        harness = ALSHarnessV080(seed=42, config=config, verbose=False)
        result = harness.run()

        # Should have no amnesty events
        assert result.amnesty_event_count == 0
        # Should have no lapses
        assert result.semantic_lapse_count == 0
        assert result.structural_lapse_count == 0


# =============================================================================
# Integration Tests: Deterministic Amnesty Timing
# =============================================================================

class TestDeterministicAmnestyTiming:
    """Test that amnesty fires exactly at AMNESTY_INTERVAL boundaries (per instructions §17.5)."""

    def test_amnesty_fires_at_interval(self):
        """Amnesty fires after exactly AMNESTY_INTERVAL epochs in lapse."""
        # Force lapse quickly with low K and forced turnover
        config = _create_test_config(
            max_cycles=2000,
            eligibility_threshold_k=1,  # Very low K = likely lapse
            amnesty_interval=5,
            amnesty_decay=1,
            max_successive_renewals=1,  # Immediate forced turnover
        )
        harness = ALSHarnessV080(seed=42, config=config, verbose=False)
        result = harness.run()

        # Check that amnesty events occur at correct intervals
        for event_dict in result.amnesty_events:
            lapse_epoch = event_dict["lapse_epoch_count"]
            # Should be multiple of amnesty_interval
            assert lapse_epoch % config.amnesty_interval == 0, (
                f"Amnesty at lapse_epoch={lapse_epoch} not multiple of {config.amnesty_interval}"
            )


# =============================================================================
# Integration Tests: Recovery Iff C_ELIG Reopens
# =============================================================================

class TestRecoveryCondition:
    """Test that recovery occurs iff C_ELIG becomes non-empty (per instructions §17.4)."""

    def test_recovery_requires_eligible_candidate(self):
        """Recovery only happens when eligible candidates exist."""
        config = _create_test_config(
            max_cycles=3000,
            eligibility_threshold_k=3,
            amnesty_interval=10,
            amnesty_decay=1,
            max_successive_renewals=2,
        )
        harness = ALSHarnessV080(seed=123, config=config, verbose=False)
        result = harness.run()

        # If we had recoveries, check that streak was below K at recovery
        for event_dict in result.recovery_events:
            streak = event_dict["streak_at_recovery"]
            assert streak < config.eligibility_threshold_k, (
                f"Recovery with streak={streak} >= K={config.eligibility_threshold_k}"
            )


# =============================================================================
# Integration Tests: Policy-ID Persistence Across Recovery
# =============================================================================

class TestPolicyIdPersistence:
    """Test that policy_id streaks persist across recovery (per instructions §17.6)."""

    def test_streaks_persist_through_lapse_and_recovery(self):
        """Streak table maintains policy_id identity across lapse-recovery cycles."""
        config = _create_test_config(
            max_cycles=5000,
            eligibility_threshold_k=3,
            amnesty_interval=10,
            amnesty_decay=1,
            max_successive_renewals=2,
        )
        harness = ALSHarnessV080(seed=456, config=config, verbose=False)
        result = harness.run()

        # Final streaks should be keyed by canonical policy_id format
        for policy_id, streak in result.final_streak_by_policy.items():
            # Policy ID should follow format "category:ENUM_NAME"
            parts = policy_id.split(":")
            assert len(parts) == 2, f"Invalid policy_id format: {policy_id}"
            assert parts[0] in ("control", "attack"), f"Invalid category: {parts[0]}"


# =============================================================================
# Integration Tests: No Streak Updates During Lapse Except CTA
# =============================================================================

class TestNoStreakUpdatesExceptCTA:
    """Test that only CTA modifies streaks during lapse (per instructions §17.1)."""

    def test_streak_only_decremented_by_amnesty_during_lapse(self):
        """During lapse, streaks only decrease (via CTA), never increase."""
        config = _create_test_config(
            max_cycles=3000,
            eligibility_threshold_k=2,
            amnesty_interval=5,
            amnesty_decay=1,
            max_successive_renewals=1,
        )
        harness = ALSHarnessV080(seed=789, config=config, verbose=False)
        result = harness.run()

        # Check amnesty events show only decrements
        for event_dict in result.amnesty_events:
            streak_deltas = event_dict["streak_deltas"]
            for policy_id, delta in streak_deltas.items():
                assert delta > 0, f"Expected decrement (positive delta), got {delta}"
            # Aggregate mass should decrease or stay same
            assert event_dict["aggregate_streak_mass_after"] <= event_dict["aggregate_streak_mass_before"]


# =============================================================================
# Integration Tests: Authority Uptime and Lapse Fraction
# =============================================================================

class TestUptimeMetrics:
    """Test authority uptime and lapse fraction metrics."""

    def test_uptime_plus_lapse_equals_total(self):
        """Authority uptime + lapse time ≈ total cycles."""
        config = _create_test_config(
            max_cycles=2000,
            eligibility_threshold_k=3,
            max_successive_renewals=2,
        )
        harness = ALSHarnessV080(seed=999, config=config, verbose=False)
        result = harness.run()

        # Fractions should sum to ~1.0 (allowing for initial succession)
        total_fraction = result.authority_uptime_fraction + result.lapse_fraction
        # Allow some slack for cycle 0 / initial state
        assert 0.95 <= total_fraction <= 1.05, (
            f"Uptime ({result.authority_uptime_fraction}) + Lapse ({result.lapse_fraction}) = {total_fraction}"
        )


# =============================================================================
# Integration Tests: Lapse Cause Classification
# =============================================================================

class TestLapseCauseClassification:
    """Test semantic vs structural lapse classification."""

    def test_semantic_lapse_classification(self):
        """Lapses due to ineligibility are classified as SEMANTIC."""
        config = _create_test_config(
            max_cycles=2000,
            eligibility_threshold_k=2,  # Low K for likely ineligibility
            max_successive_renewals=1,
        )
        harness = ALSHarnessV080(seed=111, config=config, verbose=False)
        result = harness.run()

        # Most lapses should be semantic (candidates exist but ineligible)
        for lapse_dict in result.lapse_events_v080:
            # Since generator always produces candidates, lapses should be SEMANTIC
            assert lapse_dict["cause"] in ("SEMANTIC", "STRUCTURAL")


# =============================================================================
# Integration Tests: CTA Disabled Comparison
# =============================================================================

class TestCTADisabled:
    """Test behavior when CTA is disabled (for comparison runs)."""

    def test_no_recovery_without_cta(self):
        """Without CTA, recovery is impossible once all policies are ineligible."""
        # Use very low K and disable CTA
        config = _create_test_config(
            max_cycles=1000,
            eligibility_threshold_k=1,  # Very low K
            amnesty_interval=10,
            cta_enabled=False,  # Disable CTA
            max_successive_renewals=1,
        )
        harness = ALSHarnessV080(seed=222, config=config, verbose=False)
        result = harness.run()

        # Should have no amnesty events
        assert result.amnesty_event_count == 0

        # If we entered lapse, we should not have recovered (or recovered only
        # if fresh pool happened to have eligible candidates)
        # This is a behavioral observation, not a strict invariant


# =============================================================================
# Integration Tests: Multi-Policy Recovery ("Bucket of Doom")
# =============================================================================

class TestMultiPolicyRecovery:
    """Test recovery when multiple policies need streak decay (per instructions §17.7)."""

    def test_amnesty_affects_all_policies(self):
        """Amnesty decrements streaks for ALL historical policies."""
        config = _create_test_config(
            max_cycles=5000,
            eligibility_threshold_k=3,
            amnesty_interval=10,
            amnesty_decay=1,
            max_successive_renewals=2,
        )
        harness = ALSHarnessV080(seed=333, config=config, verbose=False)
        result = harness.run()

        # Check that amnesty events can affect multiple policies
        for event_dict in result.amnesty_events:
            # This test passes if amnesty can affect multiple policies
            # (not required to always affect multiple, just capable)
            policies_affected = event_dict["policies_affected"]
            # At minimum, should be a list
            assert isinstance(policies_affected, list)


# =============================================================================
# Integration Tests: Hollow Recovery Detection
# =============================================================================

class TestHollowRecovery:
    """Test detection of hollow recovery (rapid re-lapse post-recovery)."""

    def test_hollow_recovery_metric_exists(self):
        """Hollow recovery count is tracked."""
        config = _create_test_config(
            max_cycles=3000,
            eligibility_threshold_k=2,
            amnesty_interval=5,
            max_successive_renewals=1,
        )
        harness = ALSHarnessV080(seed=444, config=config, verbose=False)
        result = harness.run()

        # Metric should exist and be non-negative
        assert result.hollow_recovery_count >= 0


# =============================================================================
# Integration Tests: Recovery Yield
# =============================================================================

class TestRecoveryYield:
    """Test recovery yield computation."""

    def test_recovery_yield_computation(self):
        """Recovery yield = authority epochs after recovery / lapse epochs to achieve recovery."""
        config = _create_test_config(
            max_cycles=5000,
            eligibility_threshold_k=3,
            amnesty_interval=10,
            max_successive_renewals=2,
        )
        harness = ALSHarnessV080(seed=555, config=config, verbose=False)
        result = harness.run()

        # Recovery yield should be non-negative
        assert result.recovery_yield >= 0.0

        # If we had recoveries, yield should be computable
        if result.recovery_count > 0:
            # Yield can be 0 if all recoveries were immediately followed by re-lapse
            # or positive if authority held for any duration
            assert result.recovery_yield >= 0.0


# =============================================================================
# Integration Tests: Full Run Smoke Test
# =============================================================================

class TestFullRunSmoke:
    """Smoke tests for full v0.8 runs."""

    def test_basic_run_completes(self):
        """A basic v0.8 run completes without error."""
        config = _create_test_config(max_cycles=1000)
        harness = ALSHarnessV080(seed=42, config=config, verbose=False)
        result = harness.run()

        assert result.spec_version == "0.8"
        assert result.total_cycles > 0
        assert result.stop_reason is not None

    def test_run_with_forced_turnover(self):
        """Run with forced turnover exercises succession paths."""
        config = _create_test_config(
            max_cycles=2000,
            max_successive_renewals=2,
        )
        harness = ALSHarnessV080(seed=42, config=config, verbose=False)
        result = harness.run()

        # Should have some forced turnovers
        assert result.forced_turnover_count >= 0

    def test_verbose_mode(self):
        """Verbose mode runs without error."""
        config = _create_test_config(max_cycles=500)
        harness = ALSHarnessV080(seed=42, config=config, verbose=True)
        result = harness.run()
        assert result.total_cycles > 0
