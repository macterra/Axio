"""
RSA-PoC v4.1 — Calibration Baselines
Implements §9.1-9.3 of v41_design_freeze.md

Two calibration baselines to establish performance bounds:
1. Oracle - Perfect knowledge of optimal policy
2. ASB Null - Uniform random action selection (no RSA)
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .core import NormStateV410, create_initial_norm_state
from .deliberator import OracleDeliberator
from .harness import (
    DeliberationOutput,
    ExecutionResult,
    HarnessConfig,
    MVRSA410Harness,
    RandomSelector,
    Selection,
)
from .env.tri_demand import Action, TriDemandV410


# ============================================================================
# §9.1 — Oracle Calibration
# ============================================================================


@dataclass
class OracleCalibrationConfig:
    """Configuration for Oracle calibration run."""
    max_steps_per_episode: int = 40
    max_episodes: int = 20
    seed: int = 42


class OracleCalibration:
    """
    Oracle baseline with perfect policy.

    Uses OracleDeliberator which has complete knowledge of
    optimal actions. Establishes theoretical upper bound.
    """

    def __init__(self, config: OracleCalibrationConfig):
        self.config = config
        self.env = TriDemandV410(seed=config.seed)
        self.deliberator = OracleDeliberator(self.env)

    def run(self) -> Dict[str, Any]:
        """Run Oracle calibration."""
        harness_config = HarnessConfig(
            max_steps_per_episode=self.config.max_steps_per_episode,
            max_episodes=self.config.max_episodes,
            max_conflicts=10,  # Not relevant for Oracle
            seed=self.config.seed,
            selector_type="argmax",  # Oracle uses argmax selection
            record_telemetry=True
        )

        harness = MVRSA410Harness(
            env=self.env,
            deliberator=self.deliberator,
            config=harness_config
        )

        results = harness.run()
        results["calibration_type"] = "ORACLE"
        results["description"] = "Perfect knowledge baseline - theoretical upper bound"

        return results


# ============================================================================
# §9.2 — ASB Null Calibration (Bypasses RSA Entirely)
# ============================================================================


class ASBNullDeliberator:
    """
    DEPRECATED: This deliberator attempted to go through RSA with invalid
    justifications, but that's not what ASB Null means.

    Per VIII.1 §5.1 and VIII.2 §7.1, the ASB-Class Null Agent:
    - MAY include: memory, internal state, reactive policies, tool use
    - MUST NOT include: justification artifacts as action gates

    The correct ASB Null baseline bypasses RSA entirely and just
    executes random actions. See ASBNullCalibration which does this.
    """

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV410,
        episode: int,
        step: int
    ) -> DeliberationOutput:
        """Generate justifications for all actions."""
        from .core import JustificationV410, Predicate

        start = time.perf_counter()

        # Find a permission rule to reference
        perm_rule = None
        for rule in norm_state.rules:
            if rule.type.value == "PERMISSION":
                perm_rule = rule.id
                break

        if perm_rule is None:
            # Fallback if no permission rules exist
            perm_rule = norm_state.rules[0].id if norm_state.rules else "R1"

        # Generate justification for every action
        justifications = []
        for action_id in ["A0", "A1", "A2", "A3", "A4", "A5"]:
            try:
                j = JustificationV410(
                    action_id=action_id,
                    rule_refs=[perm_rule],
                    claims=[{
                        "predicate": Predicate.PERMITS.value,
                        "args": [perm_rule, "ANY"]
                    }]
                )
                justifications.append(j)
            except ValueError:
                # Skip if validation fails
                pass

        elapsed = (time.perf_counter() - start) * 1000

        return DeliberationOutput(
            justifications=justifications,
            deliberation_time_ms=elapsed
        )


@dataclass
class ASBNullCalibrationConfig:
    """Configuration for ASB Null calibration run."""
    max_steps_per_episode: int = 40
    max_episodes: int = 20
    seed: int = 42


class ASBNullCalibration:
    """
    ASB Null baseline with uniform random actions.

    Per VIII.1 §5.1 and VIII.2 §7.1:
    - ASB Null Agent MAY include memory, state, reactive policies
    - ASB Null Agent MUST NOT use justification artifacts as action gates

    This implementation BYPASSES RSA entirely.
    Actions are selected uniformly at random without deliberation/compilation.
    Establishes theoretical lower bound for comparison with RSA.

    Expected behavior: 100% of steps execute (no HALTs), reward ≈ random walk.
    """

    def __init__(self, config: ASBNullCalibrationConfig):
        self.config = config
        self.rng = random.Random(config.seed)
        self.env = TriDemandV410(seed=config.seed)

    def run(self) -> Dict[str, Any]:
        """Run ASB Null calibration - bypasses RSA entirely."""
        start_time = time.perf_counter()

        total_steps = 0
        total_reward = 0.0
        episode_summaries = []

        for episode in range(self.config.max_episodes):
            obs, _ = self.env.reset()
            episode_reward = 0.0
            episode_steps = 0
            done = False

            while not done and episode_steps < self.config.max_steps_per_episode:
                # Uniformly random action - NO RSA!
                action = Action(self.rng.randint(0, 5))
                obs, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated

                episode_reward += reward
                episode_steps += 1
                total_steps += 1

            total_reward += episode_reward
            episode_summaries.append({
                "episode": episode,
                "steps": episode_steps,
                "reward": episode_reward,
                "done": done
            })

        elapsed = (time.perf_counter() - start_time) * 1000

        return {
            "calibration_type": "ASB_NULL",
            "description": "ASB Null baseline - bypasses RSA, uniform random actions",
            "config": {
                "max_steps": self.config.max_steps_per_episode,
                "max_episodes": self.config.max_episodes,
                "seed": self.config.seed
            },
            "summary": {
                "total_steps": total_steps,
                "total_halts": 0,  # No halts - no RSA!
                "halt_rate": 0.0,
                "total_reward": total_reward,
                "average_episode_reward": total_reward / self.config.max_episodes,
                "elapsed_ms": elapsed
            },
            "episodes": episode_summaries
        }


# ============================================================================
# §9.3 — Direct Random Walk (No RSA at All)
# ============================================================================


@dataclass
class DirectRandomConfig:
    """Configuration for direct random walk."""
    max_steps_per_episode: int = 40
    max_episodes: int = 20
    seed: int = 42


class DirectRandomWalk:
    """
    Completely random action selection without any RSA components.

    Directly samples from action space without deliberation/compilation.
    Used to verify ASB Null calibration is working correctly.
    """

    def __init__(self, config: DirectRandomConfig):
        self.config = config
        self.rng = random.Random(config.seed)
        self.env = TriDemandV410(seed=config.seed)

    def run(self) -> Dict[str, Any]:
        """Run direct random walk."""
        start_time = time.perf_counter()

        total_steps = 0
        total_reward = 0.0
        episode_summaries = []

        for episode in range(self.config.max_episodes):
            obs, _ = self.env.reset()
            episode_reward = 0.0
            episode_steps = 0
            done = False

            while not done and episode_steps < self.config.max_steps_per_episode:
                # Uniformly random action
                action = Action(self.rng.randint(0, 5))
                obs, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated

                episode_reward += reward
                episode_steps += 1
                total_steps += 1

            total_reward += episode_reward
            episode_summaries.append({
                "episode": episode,
                "steps": episode_steps,
                "reward": episode_reward,
                "done": done
            })

        elapsed = (time.perf_counter() - start_time) * 1000

        return {
            "calibration_type": "DIRECT_RANDOM",
            "description": "Direct random walk - no RSA components",
            "config": {
                "max_steps": self.config.max_steps_per_episode,
                "max_episodes": self.config.max_episodes,
                "seed": self.config.seed
            },
            "summary": {
                "total_steps": total_steps,
                "total_reward": total_reward,
                "average_episode_reward": total_reward / self.config.max_episodes,
                "elapsed_ms": elapsed
            },
            "episodes": episode_summaries
        }


# ============================================================================
# §9.4 — Run All Calibrations
# ============================================================================


def run_calibrations(
    seeds: List[int],
    max_steps: int = 40,
    max_episodes: int = 20
) -> Dict[str, Any]:
    """
    Run all calibration baselines across multiple seeds.

    Returns:
        Dictionary with Oracle, ASB Null, and Direct Random results
    """
    results = {
        "seeds": seeds,
        "config": {
            "max_steps": max_steps,
            "max_episodes": max_episodes
        },
        "oracle": [],
        "asb_null": [],
        "direct_random": []
    }

    print(f"\n[Calibration] Running across {len(seeds)} seeds (H={max_steps}, E={max_episodes})")

    for i, seed in enumerate(seeds):
        print(f"  [{i+1}/{len(seeds)}] Seed {seed}:", end="", flush=True)

        # Oracle
        oracle_config = OracleCalibrationConfig(
            max_steps_per_episode=max_steps,
            max_episodes=max_episodes,
            seed=seed
        )
        oracle = OracleCalibration(oracle_config)
        oracle_result = oracle.run()
        oracle_result["seed"] = seed
        results["oracle"].append(oracle_result)
        print(f" Oracle ✓", end="", flush=True)

        # ASB Null
        asb_config = ASBNullCalibrationConfig(
            max_steps_per_episode=max_steps,
            max_episodes=max_episodes,
            seed=seed
        )
        asb_null = ASBNullCalibration(asb_config)
        asb_result = asb_null.run()
        asb_result["seed"] = seed
        results["asb_null"].append(asb_result)
        print(f" ASB ✓", end="", flush=True)

        # Direct Random
        direct_config = DirectRandomConfig(
            max_steps_per_episode=max_steps,
            max_episodes=max_episodes,
            seed=seed
        )
        direct = DirectRandomWalk(direct_config)
        direct_result = direct.run()
        direct_result["seed"] = seed
        results["direct_random"].append(direct_result)
        print(f" Random ✓", flush=True)

    print(f"  Calibration complete.", flush=True)
    return results


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "OracleCalibrationConfig",
    "OracleCalibration",
    "ASBNullDeliberator",
    "ASBNullCalibrationConfig",
    "ASBNullCalibration",
    "DirectRandomConfig",
    "DirectRandomWalk",
    "run_calibrations",
]
