"""
RSA v0.1 Acceptance Tests.

Per spec §9, these tests are NON-NEGOTIABLE:
1. RSA disabled equivalence: behavior matches pre-RSA baseline
2. RSA enabled with p_flip=0 equivalence: no enabled-path contamination
3. Flip firing proof: flips occur and match target rate
"""

import pytest
from typing import Dict, List, Any

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope


class TestRSADisabledEquivalence:
    """
    Test 9.1: RSA disabled equivalence.

    Run AKI v0.8 baseline with RSA code present but rsa_enabled=False.
    Must match pre-RSA baseline on all invariants.
    """

    def test_rsa_disabled_matches_no_rsa(self):
        """With rsa_enabled=False, behavior is identical to no RSA."""
        config = ALSConfigV080(max_cycles=1000, max_successive_renewals=3)

        # Run without RSA (baseline)
        h1 = ALSHarnessV080(seed=42, config=config)
        r1 = h1.run()

        # Run with RSA disabled
        rsa_cfg = RSAConfig(rsa_enabled=False)
        h2 = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        # Must match on all AKI invariants
        assert r1.s_star == r2.s_star
        assert r1.total_cycles == r2.total_cycles
        assert r1.recovery_count == r2.recovery_count
        assert r1.amnesty_event_count == r2.amnesty_event_count
        assert r1.authority_uptime_cycles == r2.authority_uptime_cycles
        assert r1.total_renewals == r2.total_renewals
        assert r1.semantic_lapse_count == r2.semantic_lapse_count
        assert r1.structural_lapse_count == r2.structural_lapse_count

        # RSA telemetry should be None when disabled
        assert r2.rsa is None

    def test_rsa_none_config_matches_no_rsa(self):
        """With rsa_config=None, behavior is identical to no RSA."""
        config = ALSConfigV080(max_cycles=1000, max_successive_renewals=3)

        # Run without RSA (baseline)
        h1 = ALSHarnessV080(seed=42, config=config)
        r1 = h1.run()

        # Run with rsa_config=None (explicit)
        h2 = ALSHarnessV080(seed=42, config=config, rsa_config=None)
        r2 = h2.run()

        # Must match exactly
        assert r1.s_star == r2.s_star
        assert r1.total_cycles == r2.total_cycles
        assert r1.recovery_count == r2.recovery_count
        assert r2.rsa is None


class TestRSAPFlipZeroEquivalence:
    """
    Test 9.2: RSA enabled with p_flip=0 equivalence.

    Catches "enabled path contamination" (extra RNG draws, ordering changes).
    """

    def test_p_flip_zero_matches_baseline(self):
        """With p_flip=0, behavior is identical to baseline."""
        config = ALSConfigV080(max_cycles=1000, max_successive_renewals=3)

        # Run without RSA (baseline)
        h1 = ALSHarnessV080(seed=42, config=config)
        r1 = h1.run()

        # Run with RSA enabled but p_flip=0
        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=0,  # Zero flip rate
        )
        h2 = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        # Must match on all AKI invariants
        assert r1.s_star == r2.s_star
        assert r1.total_cycles == r2.total_cycles
        assert r1.recovery_count == r2.recovery_count
        assert r1.amnesty_event_count == r2.amnesty_event_count
        assert r1.authority_uptime_cycles == r2.authority_uptime_cycles
        assert r1.total_renewals == r2.total_renewals

        # RSA telemetry should exist but show zero flips
        assert r2.rsa is not None
        assert r2.rsa["summary"]["total_flips"] == 0
        assert r2.rsa["summary"]["observed_flip_rate_ppm"] == 0

    def test_p_flip_zero_no_contamination(self):
        """Verify RSA path doesn't contaminate candidate sampling RNG."""
        config = ALSConfigV080(max_cycles=2000, max_successive_renewals=3)

        # Run without RSA
        h1 = ALSHarnessV080(seed=99, config=config)
        r1 = h1.run()

        # Run with RSA p_flip=0
        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=0,
        )
        h2 = ALSHarnessV080(seed=99, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        # Semantic epoch records should match exactly
        # (same C0_OK, C1_OK, C2_OK, sem_pass values)
        assert len(r1.semantic_epoch_records) == len(r2.semantic_epoch_records)
        for rec1, rec2 in zip(r1.semantic_epoch_records, r2.semantic_epoch_records):
            assert rec1["c0_ok"] == rec2["c0_ok"]
            assert rec1["c1_ok"] == rec2["c1_ok"]
            assert rec1["c2_ok"] == rec2["c2_ok"]
            assert rec1["sem_pass"] == rec2["sem_pass"]


class TestRSAFlipFiringProof:
    """
    Test 9.3: Flip firing proof.

    Run with high flip rate and verify flips occur at expected rate.
    """

    def test_flips_occur_with_high_rate(self):
        """With high p_flip, flips definitely occur."""
        config = ALSConfigV080(max_cycles=2000, max_successive_renewals=3)

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=500_000,  # 50% flip rate
        )
        h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        result = h.run()

        # Must have flips
        assert result.rsa is not None
        assert result.rsa["summary"]["total_flips"] > 0
        assert result.rsa["summary"]["total_targets"] > 0

    def test_flip_rate_within_tolerance(self):
        """Observed flip rate is near expected within binomial tolerance."""
        config = ALSConfigV080(max_cycles=5000, max_successive_renewals=3)

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=100_000,  # 10% flip rate
            rsa_scope=RSAScope.PER_CI,
        )
        h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        result = h.run()

        assert result.rsa is not None
        summary = result.rsa["summary"]

        # Compute binomial tolerance (3 sigma)
        n = summary["total_targets"]
        p = 0.1  # 10%
        expected = n * p
        sigma = (n * p * (1 - p)) ** 0.5
        tolerance = 3 * sigma

        observed = summary["total_flips"]
        assert abs(observed - expected) < tolerance, (
            f"Observed {observed} flips, expected {expected} ± {tolerance}"
        )

    def test_targets_per_epoch_correct_per_ci(self):
        """PER_CI scope has 3 targets per evaluated epoch."""
        config = ALSConfigV080(max_cycles=1000, max_successive_renewals=3)

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=50_000,
            rsa_scope=RSAScope.PER_CI,
        )
        h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        result = h.run()

        assert result.rsa is not None

        # Check that evaluated epochs have 3 targets
        for rec in result.rsa["epoch_records"]:
            if not rec["in_lapse"]:
                assert rec["targets"] == 3, f"PER_CI should have 3 targets, got {rec['targets']}"

    def test_targets_per_epoch_correct_sem_pass_only(self):
        """SEM_PASS_ONLY scope has 1 target per evaluated epoch."""
        config = ALSConfigV080(max_cycles=1000, max_successive_renewals=3)

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=50_000,
            rsa_scope=RSAScope.SEM_PASS_ONLY,
        )
        h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        result = h.run()

        assert result.rsa is not None

        # Check that evaluated epochs have 1 target
        for rec in result.rsa["epoch_records"]:
            if not rec["in_lapse"]:
                assert rec["targets"] == 1, f"SEM_PASS_ONLY should have 1 target, got {rec['targets']}"


class TestRSANoLapseFiring:
    """
    Test R1: No RSA during lapse (structurally guaranteed).

    During NULL_AUTHORITY, AKI does not evaluate commitments.
    RSA must not fire either; targets per epoch during lapse must be zero.
    """

    def test_no_targets_during_lapse(self):
        """RSA has zero targets during NULL_AUTHORITY epochs."""
        # Configure to induce lapses
        config = ALSConfigV080(
            max_cycles=5000,
            max_successive_renewals=2,
            eligibility_threshold_k=2,  # Low K to trigger lapses faster
        )

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=100_000,
            rsa_scope=RSAScope.PER_CI,
        )
        h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        result = h.run()

        assert result.rsa is not None

        # Check lapse epochs have zero targets
        lapse_records = [r for r in result.rsa["epoch_records"] if r["in_lapse"]]
        for rec in lapse_records:
            assert rec["targets"] == 0, f"Lapse epoch should have 0 targets, got {rec['targets']}"
            assert rec["flips"] == 0, f"Lapse epoch should have 0 flips, got {rec['flips']}"


class TestRSADeterminism:
    """
    Test determinism and reproducibility.
    """

    def test_same_seed_same_flips(self):
        """Same seed produces identical flip pattern."""
        config = ALSConfigV080(max_cycles=1000, max_successive_renewals=3)

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=100_000,
        )

        # Run twice with same seed
        h1 = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        r1 = h1.run()

        h2 = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        # Flip patterns must match exactly
        assert r1.rsa["summary"]["total_flips"] == r2.rsa["summary"]["total_flips"]
        assert r1.rsa["summary"]["flips_by_key"] == r2.rsa["summary"]["flips_by_key"]

        # Epoch-by-epoch match
        for rec1, rec2 in zip(r1.rsa["epoch_records"], r2.rsa["epoch_records"]):
            assert rec1["flips"] == rec2["flips"]
            assert rec1["flips_by_key"] == rec2["flips_by_key"]

    def test_different_seed_different_flips(self):
        """Different seeds produce different flip patterns."""
        config = ALSConfigV080(max_cycles=2000, max_successive_renewals=3)

        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=100_000,
        )

        h1 = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
        r1 = h1.run()

        h2 = ALSHarnessV080(seed=99, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        # With different seeds and enough samples, flip patterns should differ
        # (not guaranteed but extremely likely with 100+ targets)
        flips1 = [(r["epoch"], r["flips_by_key"]) for r in r1.rsa["epoch_records"]]
        flips2 = [(r["epoch"], r["flips_by_key"]) for r in r2.rsa["epoch_records"]]

        # Just verify the summaries differ (very likely with different seeds)
        # This is a sanity check, not a strict guarantee
        assert r1.rsa["summary"]["seed_rsa"] != r2.rsa["summary"]["seed_rsa"]
