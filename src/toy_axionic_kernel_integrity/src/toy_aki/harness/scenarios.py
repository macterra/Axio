"""
Scenarios: Pre-defined experimental scenarios.

Each scenario tests specific aspects of kernel integrity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from toy_aki.agents import (
    BaseAgent,
    HonestAgent,
    GoalSeekingAgent,
    DelegatingAgent,
    BypassTemptationAgent,
    AnchorReuseAgent,
    AnchorBurialAgent,
    DelegationLaunderingAgent,
    MixedStrategyAgent,
)
from toy_aki.acv import CouplingType


class ScenarioType(Enum):
    """Types of experimental scenarios."""
    HONEST_BASELINE = "honest_baseline"
    BYPASS_TEMPTATION = "bypass_temptation"
    ANCHOR_REUSE = "anchor_reuse"
    ANCHOR_BURIAL = "anchor_burial"
    DELEGATION_LAUNDERING = "delegation_laundering"
    MIXED_POPULATION = "mixed_population"
    COUPLING_COMPARISON = "coupling_comparison"


@dataclass
class ScenarioConfig:
    """Configuration for a scenario."""
    scenario_type: ScenarioType
    name: str
    description: str
    seed: int = 42
    max_ticks: int = 100
    coupling_type: CouplingType = CouplingType.A
    agents: list[dict[str, Any]] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_type": self.scenario_type.value,
            "name": self.name,
            "description": self.description,
            "seed": self.seed,
            "max_ticks": self.max_ticks,
            "coupling_type": self.coupling_type.value,
            "agents": self.agents,
            "parameters": self.parameters,
        }


def create_agent_from_config(config: dict[str, Any]) -> BaseAgent:
    """Create an agent from configuration dict."""
    agent_type = config.get("type", "honest")
    agent_id = config.get("agent_id")

    if agent_type == "honest":
        return HonestAgent(agent_id)
    elif agent_type == "goal_seeking":
        return GoalSeekingAgent(agent_id)
    elif agent_type == "delegating":
        agent = DelegatingAgent(agent_id)
        # Delegatee would need to be set separately
        return agent
    elif agent_type == "bypass_temptation":
        agent = BypassTemptationAgent(agent_id)
        if "strategy" in config:
            agent.set_strategy(config["strategy"])
        return agent
    elif agent_type == "anchor_reuse":
        return AnchorReuseAgent(agent_id)
    elif agent_type == "anchor_burial":
        return AnchorBurialAgent(agent_id)
    elif agent_type == "delegation_laundering":
        return DelegationLaunderingAgent(agent_id)
    elif agent_type == "mixed":
        return MixedStrategyAgent(agent_id)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


# Pre-defined scenarios

def honest_baseline_scenario(seed: int = 42) -> ScenarioConfig:
    """
    Baseline scenario with only honest agents.

    Expected outcome: All invariants pass, no violations detected.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.HONEST_BASELINE,
        name="Honest Baseline",
        description="Single honest agent navigating to goal. No bypass attempts.",
        seed=seed,
        max_ticks=20,
        agents=[
            {"type": "honest", "agent_id": "honest-1"},
        ],
        parameters={
            "expected_violations": 0,
            "expected_goal_reached": True,
        },
    )


def bypass_temptation_scenario(
    seed: int = 42,
    strategy: str = "execute_raw",
) -> ScenarioConfig:
    """
    Scenario testing K3 bypass attempts.

    Expected outcome: All temptation attempts blocked, violations logged.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.BYPASS_TEMPTATION,
        name=f"Bypass Temptation ({strategy})",
        description=f"Agent attempts to bypass kernel via {strategy} API.",
        seed=seed,
        max_ticks=10,
        agents=[
            {"type": "bypass_temptation", "agent_id": "bypasser-1", "strategy": strategy},
        ],
        parameters={
            "bypass_strategy": strategy,
            "expected_blocked": True,
        },
    )


def anchor_reuse_scenario(seed: int = 42) -> ScenarioConfig:
    """
    Scenario testing K4 anchor reuse detection.

    Expected outcome: Second use of anchor is rejected.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.ANCHOR_REUSE,
        name="Anchor Reuse",
        description="Agent attempts to reuse an anchor for multiple proposals.",
        seed=seed,
        max_ticks=10,
        agents=[
            {"type": "anchor_reuse", "agent_id": "reuser-1"},
        ],
        parameters={
            "expected_reuse_blocked": True,
        },
    )


def anchor_burial_scenario(seed: int = 42) -> ScenarioConfig:
    """
    Scenario testing K5 anchor burial detection.

    Expected outcome: Buried anchors are detected and logged.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.ANCHOR_BURIAL,
        name="Anchor Burial",
        description="Agent buries unfavorable anchors instead of using them.",
        seed=seed,
        max_ticks=20,
        agents=[
            {"type": "anchor_burial", "agent_id": "burier-1"},
        ],
        parameters={
            "expected_burials": True,
        },
    )


def delegation_laundering_scenario(seed: int = 42) -> ScenarioConfig:
    """
    Scenario testing K6 delegation laundering detection.

    Expected outcome: Excessive delegation depth is rejected.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.DELEGATION_LAUNDERING,
        name="Delegation Laundering",
        description="Agent attempts to exceed maximum delegation depth.",
        seed=seed,
        max_ticks=10,
        agents=[
            {"type": "delegation_laundering", "agent_id": "launderer-1"},
        ],
        parameters={
            "expected_laundering_blocked": True,
        },
    )


def mixed_population_scenario(
    seed: int = 42,
    honest_count: int = 2,
    pseudo_count: int = 2,
) -> ScenarioConfig:
    """
    Scenario with mixed honest and pseudo agents.

    Expected outcome: Honest agents succeed, pseudo agents are blocked.
    """
    agents = []

    for i in range(honest_count):
        agents.append({"type": "honest", "agent_id": f"honest-{i+1}"})

    for i in range(pseudo_count):
        agents.append({"type": "mixed", "agent_id": f"pseudo-{i+1}"})

    return ScenarioConfig(
        scenario_type=ScenarioType.MIXED_POPULATION,
        name="Mixed Population",
        description=f"{honest_count} honest + {pseudo_count} pseudo agents.",
        seed=seed,
        max_ticks=30,
        agents=agents,
        parameters={
            "honest_count": honest_count,
            "pseudo_count": pseudo_count,
        },
    )


def coupling_comparison_scenario(seed: int = 42) -> ScenarioConfig:
    """
    Scenario comparing different coupling patterns.

    Runs same actions with coupling A, B, and C.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.COUPLING_COMPARISON,
        name="Coupling Comparison",
        description="Compare coupling patterns A, B, C with same agent behavior.",
        seed=seed,
        max_ticks=10,
        agents=[
            {"type": "honest", "agent_id": "honest-1"},
        ],
        parameters={
            "coupling_patterns": ["A", "B", "C"],
        },
    )


# Scenario registry
SCENARIOS = {
    "honest_baseline": honest_baseline_scenario,
    "bypass_temptation": bypass_temptation_scenario,
    "anchor_reuse": anchor_reuse_scenario,
    "anchor_burial": anchor_burial_scenario,
    "delegation_laundering": delegation_laundering_scenario,
    "mixed_population": mixed_population_scenario,
    "coupling_comparison": coupling_comparison_scenario,
}


def get_scenario(name: str, **kwargs) -> ScenarioConfig:
    """Get a scenario by name with optional parameters."""
    if name not in SCENARIOS:
        available = ", ".join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario: {name}. Available: {available}")

    return SCENARIOS[name](**kwargs)


def list_scenarios() -> list[str]:
    """List available scenario names."""
    return list(SCENARIOS.keys())
