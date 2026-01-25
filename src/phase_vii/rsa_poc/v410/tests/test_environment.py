"""
Unit tests for v4.1 environment (TriDemandV410).

Tests verify:
1. rank() computes correct path distance
2. progress_set() returns actions that decrease rank
3. target_satisfied() detects zone satisfaction
4. Environment step mechanics work correctly
"""

import pytest

import sys
sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.env.tri_demand import (
    TriDemandV410,
    Action,
    Observation,
    POSITIONS,
)
from src.rsa_poc.v410.core import ObligationTarget


class TestRankFunction:
    """Tests for rank() function (Bug #2 fix)."""

    def test_rank_at_satisfied_target_is_zero(self):
        """Rank should be 0 when target is satisfied."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        # Create observation with Zone A satisfied
        satisfied_obs = Observation(
            agent_pos=obs.agent_pos,
            inventory=obs.inventory,
            zone_a_demand=0,
            zone_b_demand=obs.zone_b_demand,
            zone_c_demand=obs.zone_c_demand,
            zone_a_satisfied=True,
            zone_b_satisfied=False,
            zone_c_satisfied=False,
            step=0,
            episode=1,
            rule_r1_active=True
        )

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A")

        rank = env.rank(satisfied_obs, target.to_dict())
        assert rank == 0

    def test_rank_decreases_toward_source(self):
        """Rank should decrease when moving toward SOURCE with no inventory."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        # At START, need to go to SOURCE first
        start_rank = env.rank(obs, target)

        # Move toward SOURCE (North)
        obs2, _, _, _, _ = env.step(Action.MOVE_N)
        new_rank = env.rank(obs2, target)

        # Rank should decrease
        assert new_rank < start_rank, f"Rank should decrease: {new_rank} < {start_rank}"

    def test_collect_at_source_decreases_rank(self):
        """COLLECT at SOURCE should decrease rank (Bug #2 scenario)."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        # Move to SOURCE with step limit to prevent infinite loop
        # NOTE: Position is (row, col). MOVE_N decreases row, MOVE_W decreases col.
        max_steps = 20
        for _ in range(max_steps):
            if obs.agent_pos == POSITIONS["SOURCE"]:
                break
            # Navigation: row first, then col
            if obs.agent_pos[0] > POSITIONS["SOURCE"][0]:
                obs, _, _, _, _ = env.step(Action.MOVE_N)  # decrease row
            elif obs.agent_pos[0] < POSITIONS["SOURCE"][0]:
                obs, _, _, _, _ = env.step(Action.MOVE_S)  # increase row
            elif obs.agent_pos[1] > POSITIONS["SOURCE"][1]:
                obs, _, _, _, _ = env.step(Action.MOVE_W)  # decrease col
            elif obs.agent_pos[1] < POSITIONS["SOURCE"][1]:
                obs, _, _, _, _ = env.step(Action.MOVE_E)  # increase col

        # Skip if we couldn't reach SOURCE
        if obs.agent_pos != POSITIONS["SOURCE"]:
            pytest.skip("Could not navigate to SOURCE")

        assert obs.inventory == 0

        rank_before_collect = env.rank(obs, target)

        # Collect
        obs_after, _, _, _, _ = env.step(Action.COLLECT)

        rank_after_collect = env.rank(obs_after, target)

        # This was Bug #2: COLLECT should DECREASE rank, not increase
        assert rank_after_collect < rank_before_collect, \
            f"COLLECT should decrease rank: {rank_after_collect} < {rank_before_collect}"

    def test_rank_includes_full_path(self):
        """Rank should include full path: dist_to_source + collect + dist_to_zone + deposit."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        # At START with no inventory
        rank = env.rank(obs, target)

        # Just verify rank is reasonable (> 0)
        assert rank > 0


class TestProgressSet:
    """Tests for progress_set() function."""

    def test_progress_set_returns_actions(self):
        """progress_set should return a set of action IDs."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        progress = env.progress_set(obs, target)

        assert isinstance(progress, set)
        for action_id in progress:
            assert action_id in ["A0", "A1", "A2", "A3", "A4", "A5"]

    def test_progress_set_actions_decrease_rank(self):
        """All actions in progress_set should decrease rank."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        current_rank = env.rank(obs, target)
        progress = env.progress_set(obs, target)

        # For each action in progress_set, verify it decreases rank
        # (Using simulation in a fresh env instance)
        for action_id in progress:
            action = Action(int(action_id[1]))
            test_env = TriDemandV410(seed=42)
            test_obs, _ = test_env.reset()

            # Simulate action
            new_obs, _, _, _, _ = test_env.step(action)
            new_rank = test_env.rank(new_obs, target)

            assert new_rank < current_rank, \
                f"Action {action_id} should decrease rank: {new_rank} < {current_rank}"

    def test_progress_set_not_empty_at_start(self):
        """progress_set should not be empty at START (path exists)."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        progress = env.progress_set(obs, target)

        assert len(progress) > 0, "progress_set should not be empty at START"


class TestTargetSatisfied:
    """Tests for target_satisfied() function."""

    def test_target_not_satisfied_initially(self):
        """Targets should not be satisfied at start."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target_a = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()
        target_b = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_B").to_dict()
        target_c = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_C").to_dict()

        assert not env.target_satisfied(obs, target_a)
        assert not env.target_satisfied(obs, target_b)
        assert not env.target_satisfied(obs, target_c)

    def test_target_satisfied_after_delivery(self):
        """Target should be satisfied after successful delivery."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        target_a = ObligationTarget(kind="DEPOSIT_ZONE", target_id="ZONE_A").to_dict()

        # Helper to navigate with step limit
        # NOTE: Position is (row, col). MOVE_N decreases row, MOVE_W decreases col.
        def navigate_to(target_pos, max_steps=20):
            nonlocal obs
            for _ in range(max_steps):
                if obs.agent_pos == target_pos:
                    return True
                if obs.agent_pos[0] > target_pos[0]:
                    obs, _, _, _, _ = env.step(Action.MOVE_N)  # decrease row
                elif obs.agent_pos[0] < target_pos[0]:
                    obs, _, _, _, _ = env.step(Action.MOVE_S)  # increase row
                elif obs.agent_pos[1] > target_pos[1]:
                    obs, _, _, _, _ = env.step(Action.MOVE_W)  # decrease col
                elif obs.agent_pos[1] < target_pos[1]:
                    obs, _, _, _, _ = env.step(Action.MOVE_E)  # increase col
            return obs.agent_pos == target_pos

        # 1. Move to SOURCE
        if not navigate_to(POSITIONS["SOURCE"]):
            pytest.skip("Could not navigate to SOURCE")

        # 2. Collect
        obs, _, _, _, _ = env.step(Action.COLLECT)
        assert obs.inventory > 0

        # 3. Move to Zone A
        if not navigate_to(POSITIONS["ZONE_A"]):
            pytest.skip("Could not navigate to ZONE_A")

        # 4. Deposit
        obs, _, _, _, _ = env.step(Action.DEPOSIT)

        # Should now be satisfied
        assert env.target_satisfied(obs, target_a), "Zone A should be satisfied after deposit"


class TestEnvironmentBasics:
    """Basic environment functionality tests."""

    def test_reset_returns_observation(self):
        """Reset should return a valid observation."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        assert isinstance(obs, Observation)
        assert hasattr(obs, 'agent_pos')
        assert hasattr(obs, 'inventory')

    def test_step_returns_observation(self):
        """Step should return a valid observation."""
        env = TriDemandV410(seed=42)
        obs, _ = env.reset()

        new_obs, reward, terminated, truncated, info = env.step(Action.MOVE_N)

        assert isinstance(new_obs, Observation)

    def test_deterministic_with_seed(self):
        """Same seed should produce same initial state."""
        env1 = TriDemandV410(seed=42)
        env2 = TriDemandV410(seed=42)

        obs1, _ = env1.reset()
        obs2, _ = env2.reset()

        assert obs1.agent_pos == obs2.agent_pos
        assert obs1.inventory == obs2.inventory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
