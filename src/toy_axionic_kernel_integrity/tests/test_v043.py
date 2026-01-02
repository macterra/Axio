"""
AKI v0.4.3 ALS Tests.

Tests for semantic clarification revision of v0.4.2.

Key differences from v0.4.2:
1. Per-cycle sampling is NOT succession
2. Succession only occurs at: init, expiration, revocation
3. MSRW (Minimum Successor Residence Window) enforced
4. Kernel-derived build commitment
5. S* counts authority transfers, not samples

Organized by semantic:
1. Succession event timing
2. MSRW enforcement
3. Kernel-derived commitment
4. S* counting accuracy
5. v0.4.2 vs v0.4.3 comparison
"""

import pytest
import secrets
from typing import FrozenSet

from toy_aki.als.working_mind import (
    WorkingMind,
    WorkingMindManifest,
    BaseWorkingMind,
    ResourceEnvelope,
    InterfaceDeclaration,
    create_baseline_working_mind,
)
from toy_aki.als.leases import (
    LeaseCompliancePackage,
    Lease,
    LeaseStatus,
    LeaseViolation,
    LCPValidator,
    create_baseline_lcp,
)
from toy_aki.als.sentinel import (
    Sentinel,
    create_baseline_sentinel,
)
from toy_aki.als.generator import (
    SuccessorGenerator,
    GeneratorConfig,
)
from toy_aki.als.harness import (
    ALSConfig,
    ALSHarnessV042,
    ALSHarnessV043,
    ALSRunResult,
    ALSStopReason,
    SuccessionEvent,
    RenewalEvent,
    ExpirationEvent,
    RevocationEvent,
    run_als_experiment,
)


# =============================================================================
# §1: Succession Event Timing Tests
# =============================================================================


class TestSuccessionEventTiming:
    """Test that succession only occurs at init, expiration, or revocation."""

    def test_succession_at_init(self):
        """First endorsement happens at cycle 1 (init)."""
        config = ALSConfig(max_cycles=10, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        assert result.s_star >= 1, "Should have at least one succession at init"
        assert len(result.succession_events) >= 1

        # First succession should be at cycle 1
        first_succession = result.succession_events[0]
        assert first_succession.cycle == 1
        assert first_succession.endorsed is True

    def test_no_succession_during_msrw(self):
        """No succession during MSRW window after endorsement."""
        config = ALSConfig(max_cycles=50, renewal_check_interval=100, msrw_cycles=50)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # Only initial succession should occur (MSRW protects for 50 cycles)
        assert result.s_star == 1, f"Expected S*=1 during MSRW, got {result.s_star}"

    def test_succession_at_expiration(self):
        """Succession occurs when lease expires (renewal limit reached)."""
        # Configure for quick expiration: 1 renewal max, 10 cycle interval
        config = ALSConfig(max_cycles=100, renewal_check_interval=10)
        harness = ALSHarnessV043(seed=42, config=config)

        # Manually check expiration behavior by running longer
        config_long = ALSConfig(max_cycles=100000, renewal_check_interval=100)
        harness_long = ALSHarnessV043(seed=42, config=config_long)
        result = harness_long.run()

        # After 100 renewals (10000 cycles), lease expires
        assert result.total_expirations >= 9, f"Expected >=9 expirations, got {result.total_expirations}"
        assert result.s_star >= 10, f"Expected S*>=10, got {result.s_star}"

    def test_succession_triggered_by_expiration_not_sampling(self):
        """Verify succession is NOT triggered by per-cycle sampling."""
        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # v0.4.3: With no expiration in 1000 cycles (100 renewals), S* should be 1
        assert result.s_star == 1, f"Expected S*=1 (init only), got {result.s_star}"
        assert result.total_endorsements == 1


class TestMSRWEnforcement:
    """Test Minimum Successor Residence Window enforcement."""

    def test_msrw_default_value(self):
        """MSRW defaults to max(renewal_interval, 100)."""
        config1 = ALSConfig(renewal_check_interval=50)
        assert config1.get_msrw() == 100, "MSRW should be 100 when interval < 100"

        config2 = ALSConfig(renewal_check_interval=200)
        assert config2.get_msrw() == 200, "MSRW should be 200 when interval > 100"

    def test_msrw_explicit_value(self):
        """MSRW can be explicitly set."""
        config = ALSConfig(renewal_check_interval=100, msrw_cycles=500)
        assert config.get_msrw() == 500

    def test_msrw_prevents_early_succession(self):
        """Succession blocked during MSRW window."""
        config = ALSConfig(max_cycles=10, renewal_check_interval=100, msrw_cycles=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # Only initial succession, no more during MSRW
        assert result.s_star == 1


# =============================================================================
# §2: Kernel-Derived Commitment Tests
# =============================================================================


class TestKernelDerivedCommitment:
    """Test kernel-derived build commitment per spec §4.5."""

    def test_kernel_computes_commitment(self):
        """Kernel derives commitment from canonical manifest."""
        sentinel = create_baseline_sentinel()
        validator = LCPValidator(sentinel_id=sentinel.sentinel_id)
        manifest = WorkingMindManifest(
            build_source="test",
            build_version="1.0",
            build_hash="successor_claimed_hash",
            interface=InterfaceDeclaration(),
            resources=ResourceEnvelope(),
        )

        commitment = validator._compute_kernel_commitment(manifest)

        # Commitment should be a hex hash
        assert len(commitment) == 64, "Should be 32-byte SHA256 hex"
        assert commitment != "successor_claimed_hash", "Should not use successor's claim"

    def test_kernel_commitment_deterministic(self):
        """Same manifest produces same kernel commitment."""
        sentinel = create_baseline_sentinel()
        validator = LCPValidator(sentinel_id=sentinel.sentinel_id)
        manifest = WorkingMindManifest(
            build_source="test",
            build_version="1.0",
            build_hash="any",
            interface=InterfaceDeclaration(),
            resources=ResourceEnvelope(),
        )

        c1 = validator._compute_kernel_commitment(manifest)
        c2 = validator._compute_kernel_commitment(manifest)

        assert c1 == c2

    def test_kernel_commitment_excludes_build_hash(self):
        """Kernel commitment excludes successor's build_hash from input."""
        sentinel = create_baseline_sentinel()
        validator = LCPValidator(sentinel_id=sentinel.sentinel_id)

        manifest1 = WorkingMindManifest(
            build_source="test",
            build_version="1.0",
            build_hash="hash_a",
            interface=InterfaceDeclaration(),
            resources=ResourceEnvelope(),
        )

        manifest2 = WorkingMindManifest(
            build_source="test",
            build_version="1.0",
            build_hash="hash_b",  # Different build_hash
            interface=InterfaceDeclaration(),
            resources=ResourceEnvelope(),
        )

        c1 = validator._compute_kernel_commitment(manifest1)
        c2 = validator._compute_kernel_commitment(manifest2)

        # Should be same since build_hash is excluded from input
        assert c1 == c2, "Kernel commitment should ignore successor's build_hash"

    def test_create_lease_v043_uses_kernel_commitment(self):
        """Lease creation uses kernel-derived commitment."""
        sentinel = create_baseline_sentinel()
        validator = LCPValidator(sentinel_id=sentinel.sentinel_id)
        mind = create_baseline_working_mind()
        manifest = mind.export_manifest()
        lcp = create_baseline_lcp(manifest, sentinel.sentinel_id)

        lease, error = validator.create_lease_v043(lcp, "test_mind", manifest)

        assert lease is not None, f"Lease creation failed: {error}"
        assert "v043" in lease.lease_id, "Lease should be v0.4.3 type"


# =============================================================================
# §3: S* Counting Accuracy Tests
# =============================================================================


class TestSStarCounting:
    """Test S* counts only authority transfers, not samples."""

    def test_s_star_equals_endorsements(self):
        """S* should equal total endorsements in v0.4.3."""
        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        assert result.s_star == result.total_endorsements

    def test_s_star_not_tied_to_cycles(self):
        """S* is NOT proportional to cycles like in v0.4.2."""
        config1 = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness1 = ALSHarnessV043(seed=42, config=config1)
        result1 = harness1.run()

        config2 = ALSConfig(max_cycles=5000, renewal_check_interval=100)
        harness2 = ALSHarnessV043(seed=42, config=config2)
        result2 = harness2.run()

        # Both should have S*=1 (no expiration within horizon)
        assert result1.s_star == 1
        assert result2.s_star == 1

    def test_s_star_tied_to_expirations(self):
        """S* = 1 + expirations (init plus expiration-triggered successions)."""
        config = ALSConfig(max_cycles=100000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        expected_s_star = 1 + result.total_expirations
        assert result.s_star == expected_s_star, f"S* should be 1 + expirations"


# =============================================================================
# §4: v0.4.2 vs v0.4.3 Comparison Tests
# =============================================================================


class TestV042V043Comparison:
    """Test semantic differences between v0.4.2 and v0.4.3."""

    def test_v042_has_high_s_star(self):
        """v0.4.2 has high S* due to per-cycle sampling."""
        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness = ALSHarnessV042(seed=42, config=config)
        result = harness.run()

        # v0.4.2 samples every cycle, so S* ≈ cycles
        assert result.s_star > 100, f"v0.4.2 should have high S*, got {result.s_star}"

    def test_v043_has_low_s_star(self):
        """v0.4.3 has low S* due to discrete succession events."""
        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # v0.4.3 only counts authority transfers
        assert result.s_star <= 10, f"v0.4.3 should have low S*, got {result.s_star}"

    def test_v043_s_star_much_lower_than_v042(self):
        """v0.4.3 S* is dramatically lower than v0.4.2."""
        config = ALSConfig(max_cycles=10000, renewal_check_interval=100)

        harness_042 = ALSHarnessV042(seed=42, config=config)
        result_042 = harness_042.run()

        harness_043 = ALSHarnessV043(seed=42, config=config)
        result_043 = harness_043.run()

        # v0.4.3 S* should be at least 100x lower
        ratio = result_042.s_star / max(result_043.s_star, 1)
        assert ratio > 100, f"v0.4.3 S* should be >100x lower, ratio={ratio:.1f}"

    def test_v043_has_spec_version(self):
        """v0.4.3 result includes spec version."""
        config = ALSConfig(max_cycles=10)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        assert result.spec_version == "0.4.3"


# =============================================================================
# §5: Renewal and Expiration Event Tests
# =============================================================================


class TestRenewalExpirationEvents:
    """Test renewal and expiration event tracking."""

    def test_renewal_events_recorded(self):
        """Renewal events are tracked."""
        config = ALSConfig(max_cycles=500, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # Should have ~5 renewals (at cycles 100, 200, 300, 400, 500)
        assert result.total_renewals >= 4
        assert len(result.renewal_events) >= 4

    def test_expiration_events_recorded(self):
        """Expiration events are tracked."""
        config = ALSConfig(max_cycles=100000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # Should have expirations after renewal limits reached
        assert result.total_expirations > 0
        assert len(result.expiration_events) == result.total_expirations

    def test_mean_residence_cycles(self):
        """Mean residence is tracked correctly."""
        config = ALSConfig(max_cycles=100000, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # With 100 renewals per lease at 100 cycles each = ~10000 cycles per successor
        assert result.mean_residence_cycles is not None
        assert 9000 < result.mean_residence_cycles < 11000, (
            f"Expected ~10000, got {result.mean_residence_cycles}"
        )


# =============================================================================
# §6: run_als_experiment() Tests
# =============================================================================


class TestRunALSExperiment:
    """Test convenience function for running experiments."""

    def test_default_is_v043(self):
        """Default spec_version is 0.4.3."""
        result = run_als_experiment(seed=42, max_cycles=10)
        assert result.spec_version == "0.4.3"

    def test_can_specify_v042(self):
        """Can run with v0.4.2 semantics."""
        result = run_als_experiment(seed=42, max_cycles=10, spec_version="0.4.2")
        # v0.4.2 should have endorsements (S* may be 0 if no non-trivial)
        assert result.total_endorsements > 0

    def test_invalid_version_raises(self):
        """Invalid spec version raises error."""
        with pytest.raises(ValueError):
            run_als_experiment(seed=42, spec_version="0.5.0")


# =============================================================================
# §7: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_horizon_1_cycle(self):
        """Minimal horizon of 1 cycle."""
        config = ALSConfig(max_cycles=1, renewal_check_interval=100)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        # Should have exactly 1 succession (init at cycle 1)
        assert result.s_star == 1
        assert result.total_cycles == 1

    def test_msrw_larger_than_horizon(self):
        """MSRW larger than horizon means only init succession."""
        config = ALSConfig(max_cycles=50, renewal_check_interval=100, msrw_cycles=1000)
        harness = ALSHarnessV043(seed=42, config=config)
        result = harness.run()

        assert result.s_star == 1

    def test_deterministic_with_same_seed(self):
        """Same seed produces same results."""
        config = ALSConfig(max_cycles=1000, renewal_check_interval=100)

        harness1 = ALSHarnessV043(seed=42, config=config)
        result1 = harness1.run()

        harness2 = ALSHarnessV043(seed=42, config=config)
        result2 = harness2.run()

        assert result1.s_star == result2.s_star
        assert result1.total_renewals == result2.total_renewals
        assert result1.total_expirations == result2.total_expirations

    def test_different_seeds_can_differ(self):
        """Different seeds can produce different results."""
        # Actually with current setup, results are deterministic per seed
        # but we test the mechanism works
        config = ALSConfig(max_cycles=10000, renewal_check_interval=100)

        harness1 = ALSHarnessV043(seed=42, config=config)
        result1 = harness1.run()

        harness2 = ALSHarnessV043(seed=999, config=config)
        result2 = harness2.run()

        # Both should have same S* due to deterministic lease mechanics
        # but run_id should differ
        assert result1.run_id != result2.run_id
