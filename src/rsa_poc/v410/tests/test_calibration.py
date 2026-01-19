"""
Unit tests for v4.1 calibration implementations.

Tests verify:
1. TaskOracleCalibration completes task at ≥95% success rate
2. ASBNullCalibration bypasses RSA entirely (0% halt rate)
3. OracleCalibration produces 0% halt rate (compliance check)
4. DirectRandomWalk produces expected behavior
"""

import pytest

import sys
sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.calibration import (
    # Task Oracle
    move_toward,
    task_oracle_policy,
    TaskOracleCalibration,
    TaskOracleCalibrationConfig,
    # Compliance Oracle
    ASBNullCalibration,
    ASBNullCalibrationConfig,
    OracleCalibration,
    OracleCalibrationConfig,
    DirectRandomWalk,
    DirectRandomConfig,
)
from src.rsa_poc.v410.env.tri_demand import Action, Observation, POSITIONS, TriDemandV410


class TestTaskOraclePolicy:
    """Tests for task_oracle_policy (deterministic task completion)."""

    def test_move_toward_east(self):
        """move_toward should return MOVE_E when col < goal_col."""
        action = move_toward((2, 0), (2, 2))
        assert action == Action.MOVE_E

    def test_move_toward_west(self):
        """move_toward should return MOVE_W when col > goal_col."""
        action = move_toward((2, 4), (2, 2))
        assert action == Action.MOVE_W

    def test_move_toward_north(self):
        """move_toward should return MOVE_N when row > goal_row."""
        action = move_toward((4, 2), (2, 2))
        assert action == Action.MOVE_N

    def test_move_toward_south(self):
        """move_toward should return MOVE_S when row < goal_row."""
        action = move_toward((0, 2), (2, 2))
        assert action == Action.MOVE_S

    def test_move_toward_prioritizes_col_over_row(self):
        """move_toward should prioritize E/W movement over N/S."""
        # Diagonal case: need to go both east and north
        action = move_toward((4, 0), (2, 2))
        # Should prioritize column (east) first
        assert action == Action.MOVE_E

    def test_policy_goes_to_source_when_inventory_zero(self):
        """Policy should go to SOURCE when inventory is empty."""
        obs = Observation(
            agent_pos=(4, 2),  # START
            inventory=0,
            zone_a_demand=1,
            zone_b_demand=1,
            zone_c_demand=1,
            zone_a_satisfied=False,
            zone_b_satisfied=False,
            zone_c_satisfied=False,
            step=0,
            episode=0,
            rule_r1_active=True
        )
        action = task_oracle_policy(obs)
        # Should move north toward SOURCE (2, 2)
        assert action == Action.MOVE_N

    def test_policy_collects_at_source(self):
        """Policy should COLLECT when at SOURCE with empty inventory."""
        obs = Observation(
            agent_pos=POSITIONS["SOURCE"],
            inventory=0,
            zone_a_demand=1,
            zone_b_demand=1,
            zone_c_demand=1,
            zone_a_satisfied=False,
            zone_b_satisfied=False,
            zone_c_satisfied=False,
            step=0,
            episode=0,
            rule_r1_active=True
        )
        action = task_oracle_policy(obs)
        assert action == Action.COLLECT

    def test_policy_goes_to_zone_a_first(self):
        """Policy should prioritize Zone A when all zones unsatisfied."""
        obs = Observation(
            agent_pos=POSITIONS["SOURCE"],
            inventory=1,
            zone_a_demand=1,
            zone_b_demand=1,
            zone_c_demand=1,
            zone_a_satisfied=False,
            zone_b_satisfied=False,
            zone_c_satisfied=False,
            step=0,
            episode=0,
            rule_r1_active=True
        )
        action = task_oracle_policy(obs)
        # Zone A is at (2, 0), source is at (2, 2) - should go west
        assert action == Action.MOVE_W

    def test_policy_deposits_at_zone(self):
        """Policy should DEPOSIT when at zone with inventory."""
        obs = Observation(
            agent_pos=POSITIONS["ZONE_A"],
            inventory=1,
            zone_a_demand=1,
            zone_b_demand=1,
            zone_c_demand=1,
            zone_a_satisfied=False,
            zone_b_satisfied=False,
            zone_c_satisfied=False,
            step=0,
            episode=0,
            rule_r1_active=True
        )
        action = task_oracle_policy(obs)
        assert action == Action.DEPOSIT

    def test_policy_moves_to_zone_b_when_a_satisfied(self):
        """Policy should target Zone B when A is satisfied."""
        obs = Observation(
            agent_pos=POSITIONS["SOURCE"],
            inventory=1,
            zone_a_demand=1,
            zone_b_demand=1,
            zone_c_demand=1,
            zone_a_satisfied=True,
            zone_b_satisfied=False,
            zone_c_satisfied=False,
            step=0,
            episode=0,
            rule_r1_active=True
        )
        action = task_oracle_policy(obs)
        # Zone B is at (0, 2), source is at (2, 2) - should go north
        assert action == Action.MOVE_N


class TestTaskOracleCalibration:
    """Tests for TaskOracleCalibration (calibration gate)."""

    def test_task_oracle_achieves_100_percent_success(self):
        """Task Oracle should complete task in 100% of episodes."""
        config = TaskOracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=10,
            seed=42
        )
        cal = TaskOracleCalibration(config)

        result = cal.run()

        # Should achieve 100% success rate with H=40
        assert result['summary']['success_rate'] == 1.0
        assert result['summary']['calibration_passed'] == True

    def test_task_oracle_zero_halt_rate(self):
        """Task Oracle should have 0% halt rate (bypasses RSA)."""
        config = TaskOracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=10,
            seed=42
        )
        cal = TaskOracleCalibration(config)

        result = cal.run()

        assert result['summary']['total_halts'] == 0
        assert result['summary']['halt_rate'] == 0.0

    def test_task_oracle_passes_calibration_gate(self):
        """Task Oracle should pass calibration gate (≥95% success)."""
        config = TaskOracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=100,
            seed=42
        )
        cal = TaskOracleCalibration(config)

        result = cal.run()

        assert result['summary']['success_rate'] >= 0.95
        assert result['summary']['calibration_passed'] == True

    def test_task_oracle_fast_execution(self):
        """Task Oracle should execute quickly (no LLM, no RSA)."""
        config = TaskOracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=100,
            seed=42
        )
        cal = TaskOracleCalibration(config)

        result = cal.run()

        # Should complete 100 episodes in under 1 second
        assert result['summary']['elapsed_ms'] < 1000

    def test_task_oracle_deterministic(self):
        """Task Oracle should be deterministic."""
        config1 = TaskOracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=10,
            seed=42
        )
        config2 = TaskOracleCalibrationConfig(
            max_steps_per_episode=40,
            max_episodes=10,
            seed=42
        )

        result1 = TaskOracleCalibration(config1).run()
        result2 = TaskOracleCalibration(config2).run()

        assert result1['summary']['total_successes'] == result2['summary']['total_successes']
        assert result1['summary']['total_steps'] == result2['summary']['total_steps']


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
        """Compliance Oracle result should identify as COMPLIANCE_ORACLE type."""
        config = OracleCalibrationConfig(
            max_steps_per_episode=10,
            max_episodes=1,
            seed=42
        )
        cal = OracleCalibration(config)

        result = cal.run()

        assert result.get('calibration_type') == 'COMPLIANCE_ORACLE'


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
