"""Test configuration for toy_pseudo_axion."""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_env():
    """Create a sample environment for testing."""
    from toy_pseudo_axion.env.gridworld import (
        GridState, Entity, Object, Hazard, Tool, Wall, EnvFlags
    )

    return GridState(
        tick=0,
        width=8,
        height=8,
        walls=[Wall(3, 3)],
        self_entity=Entity(
            id="self",
            x=2,
            y=2,
            energy=100,
            inventory=[],
            alive=True,
            stunned=False
        ),
        agents=[
            Entity(
                id="A1",
                x=5,
                y=5,
                energy=80,
                inventory=[],
                alive=True,
                stunned=False
            )
        ],
        objects=[
            Object(id="coin_1", kind="coin", x=4, y=2, props={"value": 10})
        ],
        hazards=[
            Hazard(id="pit_1", kind="pit", x=6, y=2, severity=20)
        ],
        tools=[],
        rng_seed="test_0",
        env_flags=EnvFlags()
    )


@pytest.fixture
def sample_proposal(sample_env):
    """Create a sample proposal for testing."""
    from toy_pseudo_axion.common.hashing import sha256_hex, hash_json
    import secrets

    nonce = secrets.token_hex(16)

    return {
        "payload": {
            "plan": {
                "steps": [
                    {"action": "move", "direction": "right"}
                ]
            },
            "capability_requests": [
                {
                    "operation": "move",
                    "trace_commit": sha256_hex("test_trace_commit")
                }
            ]
        },
        "trace": {
            "env_hash": hash_json(sample_env.to_dict()),
            "focus_vars": {
                "self_position": {"x": 2, "y": 2},
                "self_energy": 100,
                "nearest_item": {"id": "coin_1", "dx": 2, "dy": 0, "dist": 2}
            },
            "counterfactuals": [
                {
                    "id": "cf_1",
                    "mutation": {"kind": "set", "var": "self_position.x", "value": 1},
                    "predicted_choice": "move:right",
                    "causal_claim": "IF self_position.x DEC THEN CHOICE move:right"
                }
            ],
            "fork_snapshots": [
                {
                    "fork_id": "fork_1",
                    "forked_at_tick": 0,
                    "commitment": sha256_hex(nonce + "|" + hash_json(sample_env.to_dict())),
                    "state_hash": hash_json(sample_env.to_dict())
                }
            ]
        }
    }


@pytest.fixture
def honest_agent():
    """Create an honest agent for testing."""
    from toy_pseudo_axion.agents.honest import HonestAgent
    return HonestAgent()


@pytest.fixture
def pseudo_agent():
    """Create a pseudo agent for testing."""
    from toy_pseudo_axion.agents.pseudo import PseudoAgent
    return PseudoAgent()
