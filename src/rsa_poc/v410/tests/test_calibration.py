"""
Unit tests for v4.1 calibration implementations.

Tests verify:
1. ASBNullCalibration bypasses RSA entirely (0% halt rate)
2. OracleCalibration produces 0% halt rate
3. DirectRandomWalk produces expected behavior
"""

import pytest

import sys
sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.calibration import (
    ASBNullCalibration,
    ASBNullCalibrationConfig,
    OracleCalibration,
    OracleCalibrationConfig,
    DirectRandomWalk,
    DirectRandomConfig,
)


class TestASBNullCalibration:
    """Tests for ASBNullCalibration (bypass RSA, uniform random)."""

    def test_asb_null_bypasses_rsa(self):
        """ASB Null should bypass RSA entirely - no deliberation, no compilation."""
        config = ASBNullCalibrationConfig(
            max_steps_per_episode=10,
            max_episodes=2,
            seed=42
        )
        cal = ASBNullCalibration(config)

        result = cal.run()

        # Should have zero halts - RSA is bypassed
        assert result['summary']['total_halts'] == 0
        assert result['summary']['halt_rate'] == 0.0

    def test_asb_null_executes_all_steps(self):
        """ASB Null should execute all steps (no halts)."""
        config = ASBNullCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=20,
            seed=42
        )
        cal = ASBNullCalibration(config)

        result = cal.run()

        # Should execute all 800 steps
        assert result['summary']['total_steps'] == 800
        assert result['summary']['total_halts'] == 0

    def test_asb_null_produces_random_walk_reward(self):
        """ASB Null should produce typical random walk reward."""
        config = ASBNullCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=20,
            seed=42
        )
        cal = ASBNullCalibration(config)

        result = cal.run()

        # Random walk should produce some reward (not zero, not maximal)
        # Exact value depends on seed but should be > 0 and << 800
        assert result['summary']['total_reward'] >= 0
        # Very low expected reward for random walk in delivery task
        assert result['summary']['total_reward'] < 100

    def test_asb_null_fast_execution(self):
        """ASB Null should execute quickly (no LLM calls)."""
        config = ASBNullCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=20,
            seed=42
        )
        cal = ASBNullCalibration(config)

        result = cal.run()

        # Should complete in under 1 second (no LLM, no compilation)
        assert result['summary']['elapsed_ms'] < 1000

    def test_asb_null_returns_expected_keys(self):
        """ASB Null result should have expected structure."""
        config = ASBNullCalibrationConfig(
            max_steps_per_episode=10,
            max_episodes=2,
            seed=42
        )
        cal = ASBNullCalibration(config)

        result = cal.run()

        assert 'calibration_type' in result
        assert result['calibration_type'] == 'ASB_NULL'
        assert 'summary' in result
        assert 'total_steps' in result['summary']
        assert 'total_halts' in result['summary']
        assert 'halt_rate' in result['summary']
        assert 'total_reward' in result['summary']
        assert 'elapsed_ms' in result['summary']

    def test_asb_null_deterministic_with_seed(self):
        """ASB Null should be deterministic given same seed."""
        config1 = ASBNullCalibrationConfig(
            max_steps_per_episode=10,
            max_episodes=5,
            seed=42
        )
        config2 = ASBNullCalibrationConfig(
            max_steps_per_episode=10,
            max_episodes=5,
            seed=42
        )

        result1 = ASBNullCalibration(config1).run()
        result2 = ASBNullCalibration(config2).run()

        # Same seed should produce same reward
        assert result1['summary']['total_reward'] == result2['summary']['total_reward']


class TestOracleCalibration:
    """Tests for OracleCalibration (perfect policy, 0% halt)."""

    def test_oracle_zero_halt_rate(self):
        """Oracle should produce 0% halt rate."""
        config = OracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=1,
            seed=42
        )
        cal = OracleCalibration(config)

        result = cal.run()

        total_attempts = result['summary'].get('total_steps', 0) + result['summary'].get('total_halts', 0)
        halt_rate = result['summary'].get('total_halts', 0) / total_attempts if total_attempts > 0 else 0

        assert halt_rate == 0.0

    def test_oracle_executes_all_steps(self):
        """Oracle should execute all steps."""
        config = OracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=1,
            seed=42
        )
        cal = OracleCalibration(config)

        result = cal.run()

        assert result['summary']['total_steps'] == 40

    def test_oracle_returns_calibration_type(self):
        """Oracle result should identify as ORACLE type."""
        config = OracleCalibrationConfig(
            max_steps_per_episode=10,
            max_episodes=1,
            seed=42
        )
        cal = OracleCalibration(config)

        result = cal.run()

        assert result.get('calibration_type') == 'ORACLE'


class TestDirectRandomWalk:
    """Tests for DirectRandomWalk (no RSA at all)."""

    def test_direct_random_executes_all_steps(self):
        """Direct random walk should execute all steps."""
        config = DirectRandomConfig(
            max_steps_per_episode=40,
            max_episodes=20,
            seed=42
        )
        walk = DirectRandomWalk(config)

        result = walk.run()

        assert result['summary']['total_steps'] == 800

    def test_direct_random_fast(self):
        """Direct random walk should be very fast."""
        config = DirectRandomConfig(
            max_steps_per_episode=40,
            max_episodes=20,
            seed=42
        )
        walk = DirectRandomWalk(config)

        result = walk.run()

        # Should complete in under 100ms
        assert result['summary']['elapsed_ms'] < 100

    def test_direct_random_type(self):
        """Direct random result should identify type."""
        config = DirectRandomConfig(
            max_steps_per_episode=10,
            max_episodes=1,
            seed=42
        )
        walk = DirectRandomWalk(config)

        result = walk.run()

        assert result.get('calibration_type') == 'DIRECT_RANDOM'


class TestASBNullVsOldBehavior:
    """Tests to verify ASB Null no longer produces 100% halts."""

    def test_asb_null_not_100_percent_halt(self):
        """ASB Null must NOT produce 100% halt rate (old broken behavior)."""
        config = ASBNullCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=20,
            seed=42
        )
        cal = ASBNullCalibration(config)

        result = cal.run()

        # The OLD broken behavior was 100% halts
        # The NEW correct behavior is 0% halts
        assert result['summary']['halt_rate'] != 1.0, \
            "ASB Null should NOT produce 100% halt rate - that was the broken behavior"
        assert result['summary']['halt_rate'] == 0.0, \
            "ASB Null should produce 0% halt rate (bypasses RSA)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
