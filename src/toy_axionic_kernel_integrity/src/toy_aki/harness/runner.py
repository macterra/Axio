"""
Runner: Execute scenarios and collect results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from toy_aki.kernel import KernelWatchdog, ProbeEngine, current_time_ms
from toy_aki.acv import CouplingType
from toy_aki.agents import BaseAgent
from toy_aki.harness.scenarios import ScenarioConfig, create_agent_from_config


@dataclass
class EpisodeResult:
    """Result of running a single episode."""
    scenario_name: str
    seed: int
    coupling_type: str
    ticks_executed: int
    goal_reached: bool
    violations_detected: int
    temptation_attempts: int
    buried_anchors: int
    probe_results: dict[str, Any]
    audit_entries: int
    duration_ms: int
    agent_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "seed": self.seed,
            "coupling_type": self.coupling_type,
            "ticks_executed": self.ticks_executed,
            "goal_reached": self.goal_reached,
            "violations_detected": self.violations_detected,
            "temptation_attempts": self.temptation_attempts,
            "buried_anchors": self.buried_anchors,
            "probe_results": self.probe_results,
            "audit_entries": self.audit_entries,
            "duration_ms": self.duration_ms,
            "agent_results": self.agent_results,
        }


class ScenarioRunner:
    """
    Runs experimental scenarios and collects results.
    """

    def __init__(self, verbose: bool = False):
        """Initialize runner."""
        self._verbose = verbose
        self._results: list[EpisodeResult] = []

    def log(self, message: str) -> None:
        """Log message if verbose."""
        if self._verbose:
            print(f"[Runner] {message}")

    def run_scenario(self, config: ScenarioConfig) -> EpisodeResult:
        """
        Run a single scenario.

        Args:
            config: Scenario configuration

        Returns:
            EpisodeResult with all metrics
        """
        start_time = time.time()
        self.log(f"Starting scenario: {config.name}")

        # Initialize kernel
        kernel = KernelWatchdog(
            seed=config.seed,
            coupling_type=config.coupling_type,
        )

        # Create agents
        agents: list[BaseAgent] = []
        for agent_config in config.agents:
            agent = create_agent_from_config(agent_config)
            agents.append(agent)
            self.log(f"  Created agent: {agent.agent_id}")

        # Run episode
        agent_results = []
        tick = 0

        while tick < config.max_ticks:
            state = kernel.env.state

            if state.goal_reached:
                self.log(f"  Goal reached at tick {tick}")
                break

            # Each agent takes a turn
            for agent in agents:
                if tick >= config.max_ticks:
                    break

                try:
                    result = agent.act(kernel)
                    if result:
                        agent_results.append({
                            "tick": tick,
                            "agent_id": agent.agent_id,
                            "result": result,
                        })
                        self.log(f"  Tick {tick}: {agent.agent_id} -> {result.get('action_type', 'unknown')}")
                except Exception as e:
                    self.log(f"  Tick {tick}: {agent.agent_id} raised {type(e).__name__}: {e}")
                    agent_results.append({
                        "tick": tick,
                        "agent_id": agent.agent_id,
                        "error": str(e),
                    })

                tick += 1

        # End episode
        summary = kernel.end_episode()

        # Run probes
        probe_engine = ProbeEngine(kernel)
        probe_report = probe_engine.generate_report()

        duration_ms = int((time.time() - start_time) * 1000)

        result = EpisodeResult(
            scenario_name=config.name,
            seed=config.seed,
            coupling_type=config.coupling_type.value,
            ticks_executed=summary["total_ticks"],
            goal_reached=summary["goal_reached"],
            violations_detected=summary["violations_detected"],
            temptation_attempts=summary["temptation_attempts"],
            buried_anchors=summary["unused_anchors"],
            probe_results=probe_report,
            audit_entries=summary["audit_entries"],
            duration_ms=duration_ms,
            agent_results=agent_results,
        )

        self._results.append(result)
        self.log(f"Completed scenario: {config.name} in {duration_ms}ms")

        return result

    def run_coupling_comparison(
        self,
        config: ScenarioConfig,
    ) -> dict[str, EpisodeResult]:
        """
        Run same scenario with different coupling patterns.

        Args:
            config: Base scenario configuration

        Returns:
            Dict mapping coupling type to result
        """
        results = {}

        for coupling in [CouplingType.A, CouplingType.B, CouplingType.C]:
            # Create modified config
            modified_config = ScenarioConfig(
                scenario_type=config.scenario_type,
                name=f"{config.name} (Coupling {coupling.value})",
                description=config.description,
                seed=config.seed,
                max_ticks=config.max_ticks,
                coupling_type=coupling,
                agents=config.agents,
                parameters=config.parameters,
            )

            result = self.run_scenario(modified_config)
            results[coupling.value] = result

        return results

    def run_suite(
        self,
        scenarios: list[ScenarioConfig],
    ) -> list[EpisodeResult]:
        """
        Run a suite of scenarios.

        Args:
            scenarios: List of scenario configurations

        Returns:
            List of results
        """
        results = []

        for config in scenarios:
            result = self.run_scenario(config)
            results.append(result)

        return results

    def get_all_results(self) -> list[EpisodeResult]:
        """Get all results from this runner."""
        return list(self._results)

    def clear_results(self) -> None:
        """Clear stored results."""
        self._results.clear()
