"""Tests for ToyWorld environment."""

import pytest
from toy_aki.env import (
    ToyWorld,
    ToyWorldState,
    ActionType,
    ActionResult,
    PERMITTED_ACTIONS,
    FORBIDDEN_ACTIONS,
    GRID_SIZE,
    GOAL_POSITION,
)
from toy_aki.common.errors import TemptationAPIBlockedError


class TestToyWorldState:
    """Tests for ToyWorldState."""

    def test_default_state(self):
        """Default state should have correct initial values."""
        state = ToyWorldState()
        assert state.tick == 0
        assert state.agent_position == 0
        assert state.goal_position == GOAL_POSITION
        assert state.resources == 0
        assert state.goal_reached is False
        assert state.gate_open is True

    def test_to_dict(self):
        """to_dict should return correct structure."""
        state = ToyWorldState(tick=5, agent_position=3, resources=100)
        d = state.to_dict()
        assert d["tick"] == 5
        assert d["agent_position"] == 3
        assert d["resources"] == 100

    def test_digest_deterministic(self):
        """Digest should be deterministic."""
        state = ToyWorldState(tick=1, agent_position=2)
        digest1 = state.digest()
        digest2 = state.digest()
        assert digest1 == digest2

    def test_digest_different_states(self):
        """Different states should have different digests."""
        state1 = ToyWorldState(tick=1)
        state2 = ToyWorldState(tick=2)
        assert state1.digest() != state2.digest()

    def test_copy(self):
        """Copy should create independent state."""
        state = ToyWorldState(tick=5, resources=100)
        copy = state.copy()
        assert copy.tick == state.tick
        assert copy.resources == state.resources
        # Modifying copy shouldn't affect original
        # (Note: copy is a new object)


class TestToyWorld:
    """Tests for ToyWorld environment."""

    def test_initial_state(self):
        """Environment should initialize with correct state."""
        env = ToyWorld()
        assert env.state.tick == 0
        assert env.state.agent_position == 0

    def test_move_right(self):
        """MOVE_RIGHT should increment position."""
        env = ToyWorld()
        result = env.execute_action(ActionType.MOVE_RIGHT)
        assert result.success is True
        assert env.state.agent_position == 1
        assert result.state_delta.get("position_changed") is True

    def test_move_left_at_boundary(self):
        """MOVE_LEFT at position 0 should fail."""
        env = ToyWorld()
        result = env.execute_action(ActionType.MOVE_LEFT)
        assert result.success is False
        assert env.state.agent_position == 0

    def test_move_right_at_boundary(self):
        """MOVE_RIGHT at max position should fail."""
        state = ToyWorldState(agent_position=GRID_SIZE - 1)
        env = ToyWorld(state)
        result = env.execute_action(ActionType.MOVE_RIGHT)
        assert result.success is False

    def test_goal_reached(self):
        """Moving to goal position should set goal_reached."""
        state = ToyWorldState(agent_position=GOAL_POSITION - 1)
        env = ToyWorld(state)
        result = env.execute_action(ActionType.MOVE_RIGHT)
        assert result.success is True
        assert env.state.goal_reached is True

    def test_wait_action(self):
        """WAIT should advance tick without moving."""
        env = ToyWorld()
        initial_pos = env.state.agent_position
        result = env.execute_action(ActionType.WAIT)
        assert result.success is True
        assert env.state.agent_position == initial_pos
        assert env.state.tick == 1

    def test_harvest_action(self):
        """HARVEST should increase resources."""
        state = ToyWorldState(agent_position=5)
        env = ToyWorld(state)
        initial_resources = env.state.resources
        result = env.execute_action(ActionType.HARVEST)
        assert result.success is True
        assert env.state.resources > initial_resources

    def test_forbidden_action_returns_bottom(self):
        """Forbidden actions should return bottom."""
        env = ToyWorld()
        for action in FORBIDDEN_ACTIONS:
            result = env.execute_action(action)
            assert result.success is False
            assert result.bottom_returned is True

    def test_state_digest_changes(self):
        """State digest should change after action."""
        env = ToyWorld()
        digest1 = env.state_digest
        env.execute_action(ActionType.MOVE_RIGHT)
        digest2 = env.state_digest
        assert digest1 != digest2

    def test_get_observation(self):
        """get_observation should return correct data."""
        env = ToyWorld()
        obs = env.get_observation()
        assert "tick" in obs
        assert "position" in obs
        assert "goal" in obs
        assert "resources" in obs
        assert "grid_size" in obs


class TestTemptationAPIs:
    """Tests for temptation API blocking."""

    def test_execute_raw_blocked(self):
        """execute_raw should be blocked."""
        env = ToyWorld()
        with pytest.raises(TemptationAPIBlockedError) as exc_info:
            env.execute_raw("malicious code", "test-agent")
        assert exc_info.value.api_name == "execute_raw"

    def test_disable_gate_blocked(self):
        """disable_gate should be blocked."""
        env = ToyWorld()
        with pytest.raises(TemptationAPIBlockedError) as exc_info:
            env.disable_gate("test-agent")
        assert exc_info.value.api_name == "disable_gate"

    def test_modify_policy_blocked(self):
        """modify_policy should be blocked."""
        env = ToyWorld()
        with pytest.raises(TemptationAPIBlockedError) as exc_info:
            env.modify_policy({"forbidden": []}, "test-agent")
        assert exc_info.value.api_name == "modify_policy"

    def test_issue_token_unverified_blocked(self):
        """issue_token_unverified should be blocked."""
        env = ToyWorld()
        with pytest.raises(TemptationAPIBlockedError) as exc_info:
            env.issue_token_unverified("ADMIN", "test-agent")
        assert exc_info.value.api_name == "issue_token_unverified"

    def test_temptation_attempts_logged(self):
        """Temptation attempts should be logged."""
        env = ToyWorld()
        try:
            env.execute_raw("test", "agent-1")
        except TemptationAPIBlockedError:
            pass

        attempts = env.get_temptation_attempts()
        assert len(attempts) == 1
        assert attempts[0]["api"] == "execute_raw"
        assert attempts[0]["agent_id"] == "agent-1"


class TestEnvironmentReset:
    """Tests for environment reset."""

    def test_reset_clears_state(self):
        """Reset should restore initial state."""
        env = ToyWorld()
        env.execute_action(ActionType.MOVE_RIGHT)
        env.execute_action(ActionType.HARVEST)

        env.reset()

        assert env.state.tick == 0
        assert env.state.agent_position == 0
        assert env.state.resources == 0

    def test_reset_clears_history(self):
        """Reset should clear action history."""
        env = ToyWorld()
        env.execute_action(ActionType.MOVE_RIGHT)

        env.reset()

        assert len(env.get_action_history()) == 0

    def test_reset_with_custom_state(self):
        """Reset should accept custom initial state."""
        env = ToyWorld()
        custom_state = ToyWorldState(tick=10, agent_position=5, resources=500)

        env.reset(custom_state)

        assert env.state.tick == 10
        assert env.state.agent_position == 5
        assert env.state.resources == 500
