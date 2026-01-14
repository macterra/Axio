"""v1.2 Baseline Run Plan

Baseline run without IIC to establish pre-incentive behavior.
This provides the comparison point for v2.0 experiments.
"""

from typing import Optional
from .harness_v200 import V200ExperimentHarness, V200RunConfig, V200RunResult, AgentType


def run_v12_baseline(
    num_episodes: int = 10,
    steps_per_episode: int = 50,
    random_seed: int = 42,
) -> V200RunResult:
    """
    Run v1.2 baseline (no IIC, no rewards).

    This establishes the agent's behavior without any incentive
    interference. The result serves as comparison for:
    - R0 noise (should be similar)
    - R1/R2 sovereign (should remain similar if Rule G works)
    - R1/R2 control (should differ if control drifts)

    Args:
        num_episodes: Number of episodes to run
        steps_per_episode: Steps per episode
        random_seed: Random seed for reproducibility

    Returns:
        V200RunResult with baseline metrics
    """
    config = V200RunConfig(
        agent_type=AgentType.BASELINE,
        reward_regime=None,  # No IIC
        num_episodes=num_episodes,
        steps_per_episode=steps_per_episode,
        random_seed=random_seed,
        agent_id="MVRA_v12_baseline",
    )

    harness = V200ExperimentHarness(config)
    return harness.run()


def run_r0_noise_control(
    num_episodes: int = 10,
    steps_per_episode: int = 50,
    random_seed: int = 42,
) -> V200RunResult:
    """
    Run v2.0 with R0 noise regime.

    R0 emits action-independent uniform random rewards.
    This tests that the agent doesn't learn from noise.

    Expected: Behavior similar to baseline (no drift).

    Args:
        num_episodes: Number of episodes to run
        steps_per_episode: Steps per episode
        random_seed: Random seed for reproducibility

    Returns:
        V200RunResult with R0 noise metrics
    """
    config = V200RunConfig(
        agent_type=AgentType.SOVEREIGN,
        reward_regime="R0",
        num_episodes=num_episodes,
        steps_per_episode=steps_per_episode,
        random_seed=random_seed,
        agent_id="MVRA_v20_R0",
    )

    harness = V200ExperimentHarness(config)
    return harness.run()
