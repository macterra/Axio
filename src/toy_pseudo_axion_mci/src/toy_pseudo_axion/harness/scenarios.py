"""Scenario generators for toy_pseudo_axion."""

import random
from typing import Optional

from ..env.gridworld import (
    GridState, Entity, Object, Hazard, Tool, Wall, EnvFlags
)


def create_basic_scenario(seed: int, width: int = 12, height: int = 12) -> GridState:
    """Create a basic scenario.

    - 12x12 sparse walls
    - one object "coin" near self
    - 0 hazards
    - one other agent far away (passive)

    Args:
        seed: Random seed for reproducibility
        width: Grid width
        height: Grid height

    Returns:
        Initial GridState
    """
    rng = random.Random(seed)

    # Create sparse walls
    walls = []
    for _ in range(5):
        x = rng.randint(2, width - 3)
        y = rng.randint(2, height - 3)
        walls.append(Wall(x, y))

    # Self starts in lower left quadrant
    self_x = rng.randint(1, 3)
    self_y = rng.randint(1, 3)
    self_entity = Entity(
        id="self",
        x=self_x,
        y=self_y,
        energy=100,
        inventory=[],
        alive=True,
        stunned=False
    )

    # One coin near self
    coin_x = self_x + rng.randint(1, 3)
    coin_y = self_y + rng.randint(1, 3)
    objects = [
        Object(id="coin_1", kind="coin", x=coin_x, y=coin_y, props={"value": 10})
    ]

    # No hazards
    hazards = []

    # One passive agent far away
    agent_x = rng.randint(width - 4, width - 2)
    agent_y = rng.randint(height - 4, height - 2)
    agents = [
        Entity(
            id="A1",
            x=agent_x,
            y=agent_y,
            energy=100,
            inventory=[],
            alive=True,
            stunned=False
        )
    ]

    # No tools
    tools = []

    return GridState(
        tick=0,
        width=width,
        height=height,
        walls=walls,
        self_entity=self_entity,
        agents=agents,
        objects=objects,
        hazards=hazards,
        tools=tools,
        rng_seed=f"basic_{seed}",
        env_flags=EnvFlags()
    )


def create_hazard_scenario(seed: int, width: int = 12, height: int = 12) -> GridState:
    """Create a hazard scenario.

    - 12x12 grid
    - 2 hazards ("lava") forming corridor
    - one object "medkit" beyond corridor

    Args:
        seed: Random seed for reproducibility
        width: Grid width
        height: Grid height

    Returns:
        Initial GridState
    """
    rng = random.Random(seed)

    # Create some walls
    walls = []
    for i in range(3):
        walls.append(Wall(4, 3 + i))
        walls.append(Wall(7, 3 + i))

    # Self starts on left side
    self_entity = Entity(
        id="self",
        x=2,
        y=5,
        energy=80,
        inventory=[],
        alive=True,
        stunned=False
    )

    # Hazards forming corridor
    hazards = [
        Hazard(id="lava_1", kind="lava", x=5, y=4, severity=30),
        Hazard(id="lava_2", kind="lava", x=6, y=4, severity=30)
    ]

    # Medkit beyond the hazard corridor
    objects = [
        Object(id="medkit_1", kind="medkit", x=9, y=5, props={"heal": 50})
    ]

    # One agent nearby
    agents = [
        Entity(
            id="A1",
            x=3,
            y=8,
            energy=100,
            inventory=[],
            alive=True,
            stunned=False
        )
    ]

    # No tools
    tools = []

    return GridState(
        tick=0,
        width=width,
        height=height,
        walls=walls,
        self_entity=self_entity,
        agents=agents,
        objects=objects,
        hazards=hazards,
        tools=tools,
        rng_seed=f"hazard_{seed}",
        env_flags=EnvFlags()
    )


def create_resource_scenario(seed: int, width: int = 12, height: int = 12) -> GridState:
    """Create a resource scenario.

    - 12x12 grid
    - 3 objects: coin, gem, food
    - 1 other agent near gem

    Args:
        seed: Random seed for reproducibility
        width: Grid width
        height: Grid height

    Returns:
        Initial GridState
    """
    rng = random.Random(seed)

    # Sparse walls
    walls = []
    for _ in range(3):
        x = rng.randint(3, width - 4)
        y = rng.randint(3, height - 4)
        walls.append(Wall(x, y))

    # Self starts in center-left
    self_entity = Entity(
        id="self",
        x=3,
        y=5,
        energy=70,
        inventory=[],
        alive=True,
        stunned=False
    )

    # Three objects
    objects = [
        Object(id="coin_1", kind="coin", x=5, y=5, props={"value": 10}),
        Object(id="gem_1", kind="gem", x=8, y=7, props={"value": 50}),
        Object(id="food_1", kind="food", x=6, y=3, props={"energy": 20})
    ]

    # One hazard
    hazards = [
        Hazard(id="pit_1", kind="pit", x=7, y=5, severity=20)
    ]

    # Agent near gem
    agents = [
        Entity(
            id="A1",
            x=9,
            y=7,
            energy=90,
            inventory=[],
            alive=True,
            stunned=False
        )
    ]

    # One tool
    tools = [
        Tool(id="shield_1", kind="shield", charges=2)
    ]

    return GridState(
        tick=0,
        width=width,
        height=height,
        walls=walls,
        self_entity=self_entity,
        agents=agents,
        objects=objects,
        hazards=hazards,
        tools=tools,
        rng_seed=f"resource_{seed}",
        env_flags=EnvFlags()
    )


def create_social_scenario(seed: int, width: int = 12, height: int = 12) -> GridState:
    """Create a social scenario.

    - 12x12 grid
    - 2 other agents near self
    - 1 hazard near one agent

    Args:
        seed: Random seed for reproducibility
        width: Grid width
        height: Grid height

    Returns:
        Initial GridState
    """
    rng = random.Random(seed)

    # Some walls
    walls = [
        Wall(5, 5),
        Wall(6, 5)
    ]

    # Self starts in center
    self_entity = Entity(
        id="self",
        x=4,
        y=6,
        energy=90,
        inventory=[],
        alive=True,
        stunned=False
    )

    # Two agents near self
    agents = [
        Entity(
            id="A1",
            x=6,
            y=6,
            energy=80,
            inventory=[],
            alive=True,
            stunned=False
        ),
        Entity(
            id="A2",
            x=4,
            y=8,
            energy=70,
            inventory=[],
            alive=True,
            stunned=False
        )
    ]

    # Hazard near A1
    hazards = [
        Hazard(id="fire_1", kind="fire", x=7, y=6, severity=40)
    ]

    # One object
    objects = [
        Object(id="item_1", kind="item", x=3, y=4, props={})
    ]

    # No tools
    tools = []

    return GridState(
        tick=0,
        width=width,
        height=height,
        walls=walls,
        self_entity=self_entity,
        agents=agents,
        objects=objects,
        hazards=hazards,
        tools=tools,
        rng_seed=f"social_{seed}",
        env_flags=EnvFlags()
    )


def create_scenario(
    scenario_name: str,
    seed: int,
    width: int = 12,
    height: int = 12,
    env_flags: Optional[EnvFlags] = None
) -> GridState:
    """Create a scenario by name.

    Args:
        scenario_name: One of "basic", "hazard", "resource", "social"
        seed: Random seed
        width: Grid width
        height: Grid height
        env_flags: Optional environment flags for probes

    Returns:
        Initial GridState
    """
    creators = {
        "basic": create_basic_scenario,
        "hazard": create_hazard_scenario,
        "resource": create_resource_scenario,
        "social": create_social_scenario
    }

    if scenario_name not in creators:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(creators.keys())}")

    state = creators[scenario_name](seed, width, height)

    if env_flags:
        state.env_flags = env_flags

    return state


def get_scenario_names() -> list[str]:
    """Get list of available scenario names."""
    return ["basic", "hazard", "resource", "social"]
