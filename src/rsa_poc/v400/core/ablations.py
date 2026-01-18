"""
RSA-PoC v4.0 — Ablation Harnesses
Implements §10 of v40_design_freeze.md

Run A — Semantic Excision
Run B — Reflection Excision
Run C — Persistence Excision
Run D — Trace Excision
"""

from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .dsl import (
    Claim,
    JustificationV400,
    NormPatchV400,
    Predicate,
)
from .harness import (
    Deliberator,
    DeliberationOutput,
    MVRSA400,
    RunMetrics,
)
from .norm_state import (
    NormStateV400,
    apply_patch,
    create_initial_norm_state,
)
from .oracle import OracleDeliberator
from ..env.tri_demand import Observation, E, H


# ============================================================================
# §10.1 — Run A: Semantic Excision
# ============================================================================


def create_opaque_observation(obs: Observation, run_seed: int) -> Observation:
    """
    Create semantically opaque observation per §10.1.

    - Preserve observation shape and arity (same keys/types)
    - Replace semantic payloads with opaque tokens
    - Tokens are constant per field across all steps (no time-indexed variation)
    - hash(field_name || run_seed) truncated to field's original byte length
    """
    def opaque_int(field_name: str, max_val: int) -> int:
        h = hashlib.sha256(f"{field_name}{run_seed}".encode()).digest()
        return int.from_bytes(h[:4], 'big') % (max_val + 1)

    def opaque_bool(field_name: str) -> bool:
        h = hashlib.sha256(f"{field_name}{run_seed}".encode()).digest()
        return h[0] % 2 == 0

    def opaque_tuple(field_name: str, size: int, max_val: int) -> tuple:
        result = []
        for i in range(size):
            h = hashlib.sha256(f"{field_name}_{i}_{run_seed}".encode()).digest()
            result.append(int.from_bytes(h[:4], 'big') % (max_val + 1))
        return tuple(result)

    return Observation(
        agent_pos=opaque_tuple("agent_pos", 2, 4),
        inventory=opaque_int("inventory", 3),
        zone_a_demand=opaque_int("zone_a_demand", 1),
        zone_b_demand=opaque_int("zone_b_demand", 1),
        zone_c_demand=opaque_int("zone_c_demand", 1),
        zone_a_satisfied=opaque_bool("zone_a_satisfied"),
        zone_b_satisfied=opaque_bool("zone_b_satisfied"),
        zone_c_satisfied=opaque_bool("zone_c_satisfied"),
        step=obs.step,  # Keep step for structure but it doesn't help semantically
        episode=obs.episode,  # Keep episode for structure
        rule_r1_active=opaque_bool("rule_r1_active"),
    )


class SemanticExcisionDeliberator(Deliberator):
    """
    Run A: Semantic Excision deliberator.

    Wraps an underlying deliberator but feeds it opaque observations.
    Deliberator sees structurally valid but semantically meaningless data.
    """

    def __init__(self, underlying: Deliberator, run_seed: int):
        self.underlying = underlying
        self.run_seed = run_seed

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        # Create opaque observation
        opaque_obs = create_opaque_observation(obs, self.run_seed)

        # Deliberate with opaque observation
        return self.underlying.deliberate(opaque_obs, norm_state)


# ============================================================================
# §10.2 — Run B: Reflection Excision
# ============================================================================


class ReflectionBlockingNormState(NormStateV400):
    """NormState wrapper that blocks all patch operations."""
    pass  # The blocking happens in the harness, not here


class ReflectionExcisionMVRSA(MVRSA400):
    """
    Run B: Reflection Excision harness.

    Blocks all NormPatch operations. rev stays at 0, rules never change.
    """

    def __init__(self, deliberator: Deliberator, seed: int = 42):
        super().__init__(deliberator, seed)

    def run_episode(self):
        """Override to block patches."""
        from .norm_state import expire_rules
        from .compiler import JCOMP400, CompilationStatus, compute_feasible
        from .harness import MaskedActions, SelectionSource
        from ..env.tri_demand import ACTION_ID_MAP

        # Handle rule expiration at episode boundary
        self.norm_state = expire_rules(self.norm_state, self.current_episode)

        obs = self.env.reset(episode=self.current_episode)

        episode_reward = 0.0
        episode_halts = 0
        episode_compilation_failures = 0
        episode_compilation_total = 0
        # episode_patches = 0 — always 0 for Run B

        for step in range(self.max_steps_per_episode):
            self.current_step = step

            # DELIBERATE
            delib_output = self.deliberator.deliberate(obs, self.norm_state)

            # BLOCK PATCH — Run B: Never apply patches
            # delib_output.patch is ignored

            # COMPILE
            compiler = JCOMP400(self.norm_state)
            batch = compiler.compile_justifications(delib_output.justifications)
            episode_compilation_total += len(batch.results)
            episode_compilation_failures += batch.failed_count

            compiled_predicates = [
                r.predicate for r in batch.results
                if r.status == CompilationStatus.COMPILED and r.predicate is not None
            ]

            # MASK
            mask_result = compute_feasible(
                compiled_predicates,
                self.norm_state,
                obs,
                self.current_episode
            )

            masked_actions = MaskedActions(
                feasible=mask_result.feasible,
                feasible_count=mask_result.feasible_count
            )

            # SELECT
            selection = self.selector.select(masked_actions)

            from .harness import StepMetrics
            step_metrics = StepMetrics(
                compilation_success=batch.compiled_count > 0,
                compilation_count=batch.compiled_count,
                halt=selection.source == SelectionSource.HALT,
                binding_obligation=mask_result.binding_obligation,
            )

            if selection.source == SelectionSource.HALT:
                episode_halts += 1
                step_metrics.action_taken = None
                step_metrics.reward = -0.1
                self.step_history.append(step_metrics)
                continue

            # EXECUTE
            action_int = ACTION_ID_MAP.get(selection.action_id, 0)
            obs, reward, done, info = self.env.step(action_int)

            step_metrics.action_taken = selection.action_id
            step_metrics.reward = reward
            episode_reward += reward
            self.step_history.append(step_metrics)

            if done:
                break

        from .harness import EpisodeMetrics
        success = info.get("success", False) if 'info' in dir() else False
        timeout = info.get("timeout", False) if 'info' in dir() else (step >= self.max_steps_per_episode - 1)

        metrics = EpisodeMetrics(
            steps=step + 1,
            total_reward=episode_reward,
            success=success,
            timeout=timeout,
            halts=episode_halts,
            compilation_failures=episode_compilation_failures,
            compilation_total=episode_compilation_total,
            patches_applied=0,  # Always 0 for Run B
        )

        self.episode_metrics.append(metrics)
        self.current_episode += 1

        return metrics


# ============================================================================
# §10.3 — Run C: Persistence Excision
# ============================================================================


class PersistenceExcisionMVRSA(MVRSA400):
    """
    Run C: Persistence Excision harness.

    Resets NormState to initial at each episode boundary.
    Patches apply within episode only.
    """

    def run_episode(self):
        """Override to reset NormState at episode start."""
        # RESET NORM STATE — Run C: No cross-episode persistence
        self.norm_state = create_initial_norm_state()

        # Then proceed with normal episode (patches can apply within episode)
        return super().run_episode()


# ============================================================================
# §10.4 — Run D: Trace Excision
# ============================================================================


class TraceExcisionDeliberator(Deliberator):
    """
    Run D: Trace Excision deliberator.

    Produces justifications with only action_id, no claims or meaningful rule_refs.
    """

    def __init__(self, underlying: Deliberator):
        self.underlying = underlying

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        # Get underlying deliberation
        output = self.underlying.deliberate(obs, norm_state)

        # Strip justifications to minimal form
        stripped_justifications = []
        for j in output.justifications:
            # Keep action_id, use minimal valid rule_ref and claim
            stripped = JustificationV400(
                action_id=j.action_id,
                rule_refs=["R4"],  # Always use R4 (general permission)
                claims=[Claim(predicate=Predicate.PERMITS, args=["R4", j.action_id])]
                # No conflict, no counterfactual
            )
            stripped_justifications.append(stripped)

        return DeliberationOutput(
            justifications=stripped_justifications,
            patch=output.patch  # Keep patches for fair comparison
        )


# ============================================================================
# Ablation Runner
# ============================================================================


@dataclass
class AblationResult:
    """Result of an ablation run."""
    ablation_type: str  # A, B, C, D
    seed: int
    metrics: RunMetrics
    success_rate: float
    halt_rate: float


def run_ablation_a(seed: int, max_episodes: int = E) -> AblationResult:
    """Run A: Semantic Excision."""
    underlying = OracleDeliberator()
    deliberator = SemanticExcisionDeliberator(underlying, run_seed=seed)
    agent = MVRSA400(deliberator=deliberator, seed=seed, max_episodes=max_episodes)
    metrics = agent.run()

    return AblationResult(
        ablation_type="A",
        seed=seed,
        metrics=metrics,
        success_rate=metrics.success_rate,
        halt_rate=metrics.halt_rate,
    )


def run_ablation_b(seed: int, max_episodes: int = E) -> AblationResult:
    """Run B: Reflection Excision."""
    deliberator = OracleDeliberator()
    agent = ReflectionExcisionMVRSA(deliberator=deliberator, seed=seed)
    agent.max_episodes = max_episodes
    metrics = agent.run()

    return AblationResult(
        ablation_type="B",
        seed=seed,
        metrics=metrics,
        success_rate=metrics.success_rate,
        halt_rate=metrics.halt_rate,
    )


def run_ablation_c(seed: int, max_episodes: int = E) -> AblationResult:
    """Run C: Persistence Excision."""
    deliberator = OracleDeliberator()
    agent = PersistenceExcisionMVRSA(deliberator=deliberator, seed=seed)
    agent.max_episodes = max_episodes
    metrics = agent.run()

    return AblationResult(
        ablation_type="C",
        seed=seed,
        metrics=metrics,
        success_rate=metrics.success_rate,
        halt_rate=metrics.halt_rate,
    )


def run_ablation_d(seed: int, max_episodes: int = E) -> AblationResult:
    """Run D: Trace Excision."""
    underlying = OracleDeliberator()
    deliberator = TraceExcisionDeliberator(underlying)
    agent = MVRSA400(deliberator=deliberator, seed=seed, max_episodes=max_episodes)
    metrics = agent.run()

    return AblationResult(
        ablation_type="D",
        seed=seed,
        metrics=metrics,
        success_rate=metrics.success_rate,
        halt_rate=metrics.halt_rate,
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "create_opaque_observation",
    "SemanticExcisionDeliberator",
    "ReflectionExcisionMVRSA",
    "PersistenceExcisionMVRSA",
    "TraceExcisionDeliberator",
    "AblationResult",
    "run_ablation_a",
    "run_ablation_b",
    "run_ablation_c",
    "run_ablation_d",
]
