"""M0: Environment Determinism Tests.

Verifies that the gridworld environment is deterministic:
- Same seed produces identical states
- Clone produces exact copies
- Step function is deterministic
"""

import pytest
from toy_pseudo_axion.env.gridworld import GridState, step, clone_state
from toy_pseudo_axion.harness.scenarios import create_scenario


class TestEnvironmentDeterminism:
    """Test suite for environment determinism (M0)."""

    def test_scenario_same_seed_identical(self):
        """Same seed must produce identical scenario states."""
        env1 = create_scenario("basic", seed=42)
        env2 = create_scenario("basic", seed=42)

        assert env1.to_dict() == env2.to_dict()

    def test_scenario_different_seeds_differ(self):
        """Different seeds should produce different states."""
        env1 = create_scenario("basic", seed=42)
        env2 = create_scenario("basic", seed=123)

        # At minimum, starting positions or objects should differ
        assert env1.to_dict() != env2.to_dict()

    def test_clone_produces_exact_copy(self):
        """Clone must produce an exact copy of the state."""
        env = create_scenario("basic", seed=42)
        clone = clone_state(env)

        assert env.to_dict() == clone.to_dict()
        # Ensure they are independent objects
        assert env is not clone
        assert env.self_entity is not clone.self_entity

    def test_clone_independence(self):
        """Modifying clone should not affect original."""
        env = create_scenario("basic", seed=42)
        clone = clone_state(env)

        # Modify clone
        clone.self_entity.energy = 0

        # Original should be unchanged
        assert env.self_entity.energy != 0

    def test_step_deterministic(self):
        """Step function must be deterministic."""
        env1 = create_scenario("basic", seed=42)
        env2 = create_scenario("basic", seed=42)

        # Apply same action
        action = {"op": "move", "args": {"direction": "up"}}

        new_env1 = step(env1, action)
        new_env2 = step(env2, action)

        assert new_env1.to_dict() == new_env2.to_dict()

    def test_multiple_steps_deterministic(self):
        """Multiple steps must be deterministic."""
        env1 = create_scenario("basic", seed=42)
        env2 = create_scenario("basic", seed=42)

        actions = [
            {"op": "move", "args": {"direction": "up"}},
            {"op": "move", "args": {"direction": "right"}},
            {"op": "wait", "args": {}},
        ]

        for action in actions:
            env1 = step(env1, action)
            env2 = step(env2, action)

        assert env1.to_dict() == env2.to_dict()

    def test_all_scenarios_deterministic(self):
        """All scenario types must be deterministic."""
        scenarios = ["basic", "hazard", "resource", "social"]

        for scenario_name in scenarios:
            env1 = create_scenario(scenario_name, seed=42)
            env2 = create_scenario(scenario_name, seed=42)

            assert env1.to_dict() == env2.to_dict(), f"Scenario {scenario_name} not deterministic"
