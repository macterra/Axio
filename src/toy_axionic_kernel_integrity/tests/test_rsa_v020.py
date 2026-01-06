"""
RSA v0.2 Acceptance Tests.

Tests for Structured Epistemic Interference (RSA-SEI-0).
All acceptance tests from spec §11 must pass before any sweeps.
"""

import pytest
from typing import List

from toy_aki.rsa.config import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.adversary import RSAAdversary, stable_hash_64
from toy_aki.rsa.schedule import (
    compute_burst_phase,
    BurstPhase,
    BurstScheduleParams,
)
from toy_aki.rsa.metrics import (
    compute_rsa_metrics,
    extract_lapse_intervals,
    compute_rtd_histogram,
    bucket_recovery_time,
    compute_tail_window,
    classify_failure,
    FailureClass,
    RTD_BUCKET_LABELS,
)
from toy_aki.rsa.telemetry import RSAEpochRecord, RSATelemetry


# ==============================================================================
# §11.1: RSA Disabled Equivalence
# ==============================================================================

class TestRSADisabledEquivalence:
    """RSA disabled must not change any behavior."""

    def test_disabled_config_is_inactive(self):
        """Disabled RSA should report inactive."""
        config = RSAConfig(rsa_enabled=False)
        assert not config.is_active()

    def test_disabled_adversary_is_none(self):
        """RSAAdversary.from_config returns None when disabled."""
        config = RSAConfig(rsa_enabled=False)
        adversary = RSAAdversary.from_config(config, run_seed=42)
        assert adversary is None

    def test_none_model_is_inactive(self):
        """NONE model should be inactive even if enabled=True."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.NONE,
        )
        assert not config.is_active()


# ==============================================================================
# §11.2: RSA Enabled + Zero Probability Equivalence
# ==============================================================================

class TestZeroProbabilityEquivalence:
    """RSA enabled with zero probability must not corrupt anything."""

    def test_agg_flip_zero_no_flips(self):
        """AGG_FLIP_BERNOULLI with p=0 produces no flips."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
            rsa_p_flip_ppm=0,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
        )
        adversary = RSAAdversary(config, run_seed=42)

        # Run 100 epochs
        for epoch in range(100):
            c0, c1, c2, sem, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            assert c0 is True
            assert c1 is True
            assert c2 is True
            assert sem is True
            assert record.flips == 0

    def test_commitment_keyed_zero_no_flips(self):
        """COMMITMENT_KEYED_FLIP with p=0 produces no flips."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
            rsa_target_key="C1",
            rsa_p_target_flip_ppm=0,
        )
        adversary = RSAAdversary(config, run_seed=42)

        for epoch in range(100):
            c0, c1, c2, sem, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            assert record.flips == 0

    def test_burst_zero_no_flips(self):
        """BURST_SCHEDULED_FLIP with p_burst=0 and p_quiet=0 produces no flips."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
            rsa_burst_period_epochs=10,
            rsa_burst_width_epochs=3,
            rsa_p_burst_flip_ppm=0,
            rsa_p_quiet_flip_ppm=0,
        )
        adversary = RSAAdversary(config, run_seed=42)

        for epoch in range(100):
            c0, c1, c2, sem, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            assert record.flips == 0


# ==============================================================================
# §11.3: Flip Firing Proof (per model)
# ==============================================================================

class TestFlipFiringProof:
    """Verify each model actually produces flips at elevated rates."""

    def test_agg_flip_fires(self):
        """AGG_FLIP_BERNOULLI at 50% should produce ~50% flips."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
            rsa_p_flip_ppm=500_000,  # 50%
            rsa_scope=RSAScope.SEM_PASS_ONLY,
        )
        adversary = RSAAdversary(config, run_seed=42)

        flips = 0
        epochs = 1000
        for epoch in range(epochs):
            _, _, _, _, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            flips += record.flips

        # Should be ~500 flips ± tolerance
        observed_rate = flips / epochs
        assert 0.40 < observed_rate < 0.60, f"Expected ~50%, got {observed_rate:.1%}"

    def test_commitment_keyed_fires(self):
        """COMMITMENT_KEYED_FLIP at 50% should produce ~50% flips on target key."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
            rsa_target_key="C1",
            rsa_p_target_flip_ppm=500_000,  # 50%
        )
        adversary = RSAAdversary(config, run_seed=42)

        flips = 0
        epochs = 1000
        for epoch in range(epochs):
            _, _, _, _, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            flips += record.flips_by_key["C1"]

        observed_rate = flips / epochs
        assert 0.40 < observed_rate < 0.60, f"Expected ~50%, got {observed_rate:.1%}"

    def test_burst_fires_in_active_phase(self):
        """BURST_SCHEDULED_FLIP at 100% burst should flip during ACTIVE."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
            rsa_burst_period_epochs=10,
            rsa_burst_width_epochs=3,
            rsa_p_burst_flip_ppm=1_000_000,  # 100%
            rsa_p_quiet_flip_ppm=0,
        )
        adversary = RSAAdversary(config, run_seed=42)

        active_flips = 0
        quiet_flips = 0
        for epoch in range(100):
            _, _, _, _, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            if record.phase == "ACTIVE":
                active_flips += record.flips
            else:
                quiet_flips += record.flips

        # 100 epochs with period 10, width 3 → 30 active epochs
        assert active_flips == 30, f"Expected 30 active flips, got {active_flips}"
        assert quiet_flips == 0, f"Expected 0 quiet flips, got {quiet_flips}"

    def test_commitment_keyed_only_targets_specified_key(self):
        """COMMITMENT_KEYED_FLIP should only flip the target key."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
            rsa_target_key="C0",
            rsa_p_target_flip_ppm=1_000_000,  # 100%
        )
        adversary = RSAAdversary(config, run_seed=42)

        for epoch in range(100):
            _, _, _, _, record = adversary.corrupt(
                epoch=epoch,
                c0_raw=True, c1_raw=True, c2_raw=True,
                sem_pass_raw=True,
            )
            # Only C0 should be flipped
            assert record.flips_by_key["C0"] == 1
            assert record.flips_by_key["C1"] == 0
            assert record.flips_by_key["C2"] == 0
            assert record.flips_by_key["SEM_PASS"] == 0


# ==============================================================================
# §11.4: Burst Schedule Determinism
# ==============================================================================

class TestBurstScheduleDeterminism:
    """Same seed + config must produce identical flip patterns."""

    def test_burst_phase_deterministic(self):
        """Burst phase is deterministic function of epoch and params."""
        params = BurstScheduleParams(
            period_epochs=10,
            width_epochs=3,
            phase_offset=2,
        )

        phases1 = [compute_burst_phase(e, 10, 3, 2) for e in range(100)]
        phases2 = [compute_burst_phase(e, 10, 3, 2) for e in range(100)]

        assert phases1 == phases2

    def test_flip_pattern_deterministic(self):
        """Same seed produces identical flip locations."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
            rsa_burst_period_epochs=10,
            rsa_burst_width_epochs=3,
            rsa_p_burst_flip_ppm=500_000,
            rsa_p_quiet_flip_ppm=100_000,
        )

        adv1 = RSAAdversary(config, run_seed=42)
        adv2 = RSAAdversary(config, run_seed=42)

        for epoch in range(100):
            _, _, _, _, r1 = adv1.corrupt(epoch, True, True, True, True)
            _, _, _, _, r2 = adv2.corrupt(epoch, True, True, True, True)
            assert r1.flips == r2.flips
            assert r1.phase == r2.phase

    def test_different_seeds_produce_different_flips(self):
        """Different seeds should produce different flip patterns."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
            rsa_burst_period_epochs=10,
            rsa_burst_width_epochs=3,
            rsa_p_burst_flip_ppm=500_000,
            rsa_p_quiet_flip_ppm=100_000,
        )

        adv1 = RSAAdversary(config, run_seed=42)
        adv2 = RSAAdversary(config, run_seed=99)

        flips1 = []
        flips2 = []
        for epoch in range(100):
            _, _, _, _, r1 = adv1.corrupt(epoch, True, True, True, True)
            _, _, _, _, r2 = adv2.corrupt(epoch, True, True, True, True)
            flips1.append(r1.flips)
            flips2.append(r2.flips)

        # Patterns should differ (not identical)
        assert flips1 != flips2


# ==============================================================================
# Schedule Module Tests
# ==============================================================================

class TestBurstSchedule:
    """Test burst schedule pure functions."""

    def test_periodic_schedule_basic(self):
        """Basic periodic schedule: period=10, width=3."""
        # Epochs 0,1,2 -> ACTIVE; 3-9 -> QUIET
        for epoch in range(10):
            phase = compute_burst_phase(epoch, period=10, width=3, phase_offset=0)
            if epoch < 3:
                assert phase == BurstPhase.ACTIVE
            else:
                assert phase == BurstPhase.QUIET

    def test_periodic_schedule_with_offset(self):
        """Phase offset shifts the active window."""
        # With offset=5: epochs 5,6,7 are active (mapped from 0,1,2)
        # Actually: x = (epoch + 5) % 10, ACTIVE if x < 3
        # epoch=0: x=5, QUIET
        # epoch=5: x=0, ACTIVE
        for epoch in range(10):
            phase = compute_burst_phase(epoch, period=10, width=3, phase_offset=5)
            x = (epoch + 5) % 10
            expected = BurstPhase.ACTIVE if x < 3 else BurstPhase.QUIET
            assert phase == expected

    def test_schedule_params_validation(self):
        """BurstScheduleParams validates constraints."""
        params = BurstScheduleParams(period_epochs=10, width_epochs=3)
        params.validate()  # Should not raise

        with pytest.raises(ValueError):
            BurstScheduleParams(period_epochs=0, width_epochs=3).validate()

        with pytest.raises(ValueError):
            BurstScheduleParams(period_epochs=10, width_epochs=0).validate()

        with pytest.raises(ValueError):
            BurstScheduleParams(period_epochs=10, width_epochs=15).validate()

    def test_duty_cycle_computation(self):
        """Duty cycle PPM is correctly computed."""
        params = BurstScheduleParams(period_epochs=10, width_epochs=3)
        assert params.duty_cycle_ppm == 300_000  # 30%


# ==============================================================================
# Metrics Module Tests
# ==============================================================================

class TestMetrics:
    """Test AA/AAA/RTD computation."""

    def test_aa_computation(self):
        """Authority Availability computed correctly."""
        # 80% uptime
        authority = [True] * 80 + [False] * 20
        metrics = compute_rsa_metrics(authority)
        assert metrics.authority_availability_ppm == 800_000

    def test_aaa_computation(self):
        """Asymptotic Authority Availability uses tail window."""
        # First 100 epochs: 50% uptime
        # Last 100 epochs: 100% uptime
        # Tail window = max(5000, 200 // 5) = 5000 → but horizon < 5000,
        # so tail is whole run for this test
        authority = [i % 2 == 0 for i in range(100)] + [True] * 100
        metrics = compute_rsa_metrics(authority)
        # Tail window = max(5000, 200//5) = 5000 > 200, so uses full run
        # Full run: 50 + 100 = 150 / 200 = 75%
        assert metrics.asymptotic_authority_availability_ppm == 750_000

    def test_rtd_bucketing(self):
        """Recovery time correctly bucketed."""
        assert bucket_recovery_time(1) == "1"
        assert bucket_recovery_time(2) == "2"
        assert bucket_recovery_time(3) == "3"
        assert bucket_recovery_time(4) == "5"
        assert bucket_recovery_time(5) == "5"
        assert bucket_recovery_time(10) == "10"
        assert bucket_recovery_time(11) == "20"
        assert bucket_recovery_time(100) == "100"
        assert bucket_recovery_time(101) == "200"
        assert bucket_recovery_time(10000) == "INF"

    def test_lapse_interval_extraction(self):
        """Lapse intervals correctly extracted."""
        # Pattern: AUTH, AUTH, LAPSE, LAPSE, AUTH, LAPSE
        authority = [True, True, False, False, True, False]
        intervals = extract_lapse_intervals(authority)
        assert len(intervals) == 2
        assert intervals[0].start_epoch == 2
        assert intervals[0].end_epoch == 4
        assert intervals[0].duration_epochs == 2
        assert intervals[1].start_epoch == 5
        assert intervals[1].end_epoch == 6
        assert intervals[1].duration_epochs == 1

    def test_tail_window_computation(self):
        """Tail window is max(5000, horizon//5)."""
        assert compute_tail_window(10000) == 5000
        assert compute_tail_window(30000) == 6000
        assert compute_tail_window(1000) == 5000

    def test_failure_classification_stable(self):
        """High AAA with no lapses → STABLE_AUTHORITY."""
        authority = [True] * 10000
        metrics = compute_rsa_metrics(authority)
        assert metrics.failure_class == FailureClass.STABLE_AUTHORITY

    def test_failure_classification_terminal_collapse(self):
        """All lapses from midpoint → TERMINAL_COLLAPSE."""
        authority = [True] * 1000 + [False] * 9000
        metrics = compute_rsa_metrics(authority)
        assert metrics.failure_class == FailureClass.TERMINAL_COLLAPSE


# ==============================================================================
# Aggregator Binding Tests
# ==============================================================================

class TestAggregatorBinding:
    """Verify aggregator is called correctly in PER_KEY mode."""

    def test_aggregator_called_for_commitment_keyed(self):
        """COMMITMENT_KEYED_FLIP calls aggregator after corrupting target."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
            rsa_target_key="C1",
            rsa_p_target_flip_ppm=1_000_000,  # 100%
        )
        adversary = RSAAdversary(config, run_seed=42)

        # Custom aggregator that we can verify was called
        aggregator_calls = []
        def tracking_aggregator(c0, c1, c2):
            aggregator_calls.append((c0, c1, c2))
            return c0 and c1 and c2

        c0, c1, c2, sem, _ = adversary.corrupt(
            epoch=0,
            c0_raw=True, c1_raw=True, c2_raw=True,
            sem_pass_raw=True,
            aggregator=tracking_aggregator,
        )

        # Aggregator should be called with C1 flipped
        assert len(aggregator_calls) == 1
        assert aggregator_calls[0] == (True, False, True)  # C1 flipped
        assert sem is False  # AND(True, False, True) = False

    def test_aggregator_not_called_for_agg_flip(self):
        """AGG_FLIP_BERNOULLI does not call aggregator (corrupts SEM_PASS directly)."""
        config = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
            rsa_p_flip_ppm=1_000_000,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
        )
        adversary = RSAAdversary(config, run_seed=42)

        aggregator_calls = []
        def tracking_aggregator(c0, c1, c2):
            aggregator_calls.append((c0, c1, c2))
            return c0 and c1 and c2

        c0, c1, c2, sem, _ = adversary.corrupt(
            epoch=0,
            c0_raw=True, c1_raw=True, c2_raw=True,
            sem_pass_raw=True,
            aggregator=tracking_aggregator,
        )

        # Aggregator should NOT be called for AGG_FLIP_BERNOULLI
        assert len(aggregator_calls) == 0
        # But SEM_PASS should be flipped
        assert sem is False


# ==============================================================================
# Telemetry Tests
# ==============================================================================

class TestTelemetry:
    """Test telemetry aggregation for v0.2."""

    def test_burst_telemetry_aggregation(self):
        """Burst-specific telemetry is correctly aggregated."""
        telemetry = RSATelemetry(
            enabled=True,
            noise_model="BURST_SCHEDULED_FLIP",
            scope="SEM_PASS_ONLY",
            p_flip_ppm=500_000,
        )

        # Simulate 10 epochs: 3 active with flips, 7 quiet without
        for epoch in range(10):
            phase = "ACTIVE" if epoch < 3 else "QUIET"
            flips = 1 if phase == "ACTIVE" else 0
            record = RSAEpochRecord(
                epoch=epoch,
                targets=1,
                flips=flips,
                flips_by_key={"SEM_PASS": flips},
                p_flip_ppm=500_000 if phase == "ACTIVE" else 0,
                phase=phase,
            )
            telemetry.record_epoch(record)

        summary = telemetry.summarize()
        assert summary.active_phase_targets == 3
        assert summary.active_phase_flips == 3
        assert summary.quiet_phase_targets == 7
        assert summary.quiet_phase_flips == 0
        assert summary.burst_duty_cycle_ppm == 300_000  # 3/10 = 30%

    def test_lapse_epoch_invariant(self):
        """Lapse epochs MUST have targets=0, flips=0, and phase is None or QUIET."""
        telemetry = RSATelemetry(
            enabled=True,
            noise_model="BURST_SCHEDULED_FLIP",
            scope="SEM_PASS_ONLY",
            p_flip_ppm=500_000,
        )

        # Record a lapse epoch
        lapse_record = RSAEpochRecord(
            epoch=0,
            targets=0,
            flips=0,
            flips_by_key={"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0},
            p_flip_ppm=0,
            in_lapse=True,
            phase=None,
        )
        telemetry.record_epoch(lapse_record)

        # Verify invariants for lapse epoch
        assert lapse_record.in_lapse is True
        assert lapse_record.targets == 0
        assert lapse_record.flips == 0
        assert lapse_record.phase is None or lapse_record.phase == "QUIET"

        # Verify summary counts lapse correctly
        summary = telemetry.summarize()
        assert summary.epochs_in_lapse == 1
        assert summary.total_flips == 0


# ==============================================================================
# Config Validation Tests
# ==============================================================================

class TestConfigValidation:
    """Test RSAConfig validation for v0.2 parameters."""

    def test_commitment_keyed_requires_target_key(self):
        """COMMITMENT_KEYED_FLIP requires valid target_key."""
        with pytest.raises(ValueError):
            RSAConfig(
                rsa_enabled=True,
                rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
                rsa_target_key=None,
            )

        with pytest.raises(ValueError):
            RSAConfig(
                rsa_enabled=True,
                rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
                rsa_target_key="C3",  # Invalid
            )

    def test_burst_requires_valid_schedule(self):
        """BURST_SCHEDULED_FLIP requires valid period/width."""
        with pytest.raises(ValueError):
            RSAConfig(
                rsa_enabled=True,
                rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
                rsa_burst_period_epochs=0,
                rsa_burst_width_epochs=3,
            )

        with pytest.raises(ValueError):
            RSAConfig(
                rsa_enabled=True,
                rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
                rsa_burst_period_epochs=10,
                rsa_burst_width_epochs=0,
            )

        with pytest.raises(ValueError):
            RSAConfig(
                rsa_enabled=True,
                rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
                rsa_burst_period_epochs=10,
                rsa_burst_width_epochs=15,  # width > period
            )

    def test_ppm_range_validation(self):
        """PPM values must be in [0, 1_000_000]."""
        with pytest.raises(ValueError):
            RSAConfig(rsa_p_flip_ppm=-1)

        with pytest.raises(ValueError):
            RSAConfig(rsa_p_flip_ppm=1_000_001)

        with pytest.raises(ValueError):
            RSAConfig(
                rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
                rsa_target_key="C0",
                rsa_p_target_flip_ppm=2_000_000,
            )
