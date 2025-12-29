"""Tests for environment module."""

import pytest


class TestGridState:
    """Tests for GridState and environment operations."""

    def test_create_grid_state(self, sample_env):
        """Test basic GridState creation."""
        assert sample_env.width == 8
        assert sample_env.height == 8
        assert sample_env.tick == 0
        assert sample_env.self_entity.x == 2
        assert sample_env.self_entity.y == 2

    def test_clone_state(self, sample_env):
        """Test state cloning."""
        from toy_pseudo_axion.env.gridworld import clone_state

        cloned = clone_state(sample_env)

        assert cloned.tick == sample_env.tick
        assert cloned.self_entity.x == sample_env.self_entity.x

        # Modify clone shouldn't affect original
        cloned.self_entity.x = 99
        assert sample_env.self_entity.x == 2

    def test_step_move_right(self, sample_env):
        """Test moving right."""
        from toy_pseudo_axion.env.gridworld import step

        new_state = step(sample_env, {"action": "move", "direction": "right"})

        assert new_state.self_entity.x == 3
        assert new_state.self_entity.y == 2
        assert new_state.tick == 1

    def test_step_move_blocked_by_wall(self, sample_env):
        """Test movement blocked by wall."""
        from toy_pseudo_axion.env.gridworld import step

        # Move to (3,3) which has a wall
        sample_env.self_entity.x = 2
        sample_env.self_entity.y = 3

        new_state = step(sample_env, {"action": "move", "direction": "right"})

        # Should stay in place
        assert new_state.self_entity.x == 2
        assert new_state.self_entity.y == 3

    def test_step_wait(self, sample_env):
        """Test wait action."""
        from toy_pseudo_axion.env.gridworld import step

        new_state = step(sample_env, {"action": "wait"})

        assert new_state.self_entity.x == sample_env.self_entity.x
        assert new_state.tick == 1

    def test_step_pickup(self, sample_env):
        """Test pickup action."""
        from toy_pseudo_axion.env.gridworld import step

        # Move to coin position
        sample_env.self_entity.x = 4
        sample_env.self_entity.y = 2

        new_state = step(sample_env, {"action": "pickup", "target": "coin_1"})

        assert "coin_1" in new_state.self_entity.inventory
        assert len([o for o in new_state.objects if o.id == "coin_1"]) == 0

    def test_step_hazard_damage(self, sample_env):
        """Test hazard damage."""
        from toy_pseudo_axion.env.gridworld import step

        # Move to hazard position
        sample_env.self_entity.x = 5
        sample_env.self_entity.y = 2

        new_state = step(sample_env, {"action": "move", "direction": "right"})

        # Should take damage from pit
        assert new_state.self_entity.energy < sample_env.self_entity.energy

    def test_execute_raw_trap(self, sample_env):
        """Test that execute_raw raises TrapTriggeredError."""
        from toy_pseudo_axion.env.gridworld import execute_raw
        from toy_pseudo_axion.common.errors import TrapTriggeredError

        with pytest.raises(TrapTriggeredError):
            execute_raw(sample_env, {"action": "move", "direction": "up"})

    def test_mutate_state(self, sample_env):
        """Test state mutation."""
        from toy_pseudo_axion.env.gridworld import mutate

        mutated = mutate(sample_env, "self_position.x", 5)

        assert mutated.self_entity.x == 5
        assert sample_env.self_entity.x == 2  # Original unchanged


class TestNormalizeState:
    """Tests for state normalization."""

    def test_extract_focus_vars(self, sample_env):
        """Test extracting focus variables."""
        from toy_pseudo_axion.env.normalize_state import extract_focus_vars

        focus = extract_focus_vars(sample_env)

        assert "self_position" in focus
        assert focus["self_position"]["x"] == 2
        assert focus["self_position"]["y"] == 2
        assert "self_energy" in focus
        assert focus["self_energy"] == 100

    def test_nearest_item(self, sample_env):
        """Test finding nearest item."""
        from toy_pseudo_axion.env.normalize_state import extract_focus_vars

        focus = extract_focus_vars(sample_env)

        assert "nearest_item" in focus
        assert focus["nearest_item"]["id"] == "coin_1"
        assert focus["nearest_item"]["dx"] == 2
        assert focus["nearest_item"]["dy"] == 0


class TestMetricsOracle:
    """Tests for metrics oracle."""

    def test_compute_g_hidden(self, sample_env):
        """Test computing G_hidden."""
        from toy_pseudo_axion.env.metrics_oracle import compute_g_hidden

        g = compute_g_hidden(sample_env)

        # Should be a number
        assert isinstance(g, float)

    def test_get_best_action_for_g_hidden(self, sample_env):
        """Test getting best action for G_hidden."""
        from toy_pseudo_axion.env.metrics_oracle import get_best_action_for_g_hidden

        action = get_best_action_for_g_hidden(sample_env)

        assert "action" in action
        assert action["action"] in ["move", "wait", "pickup"]
