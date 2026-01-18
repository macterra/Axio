"""
RSA-PoC v4.0 — MVRSA-4.0 Harness
Implements §4 of v40_design_freeze.md

Component wiring: DELIBERATE → COMPILE → MASK → SELECT → EXECUTE
with full interface definitions and Fail-Not-Substitute semantics.
"""

from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from ..core.compiler import (
    JCOMP400,
    CompilationBatch,
    CompilationResult,
    CompilationStatus,
    ExecutablePredicate,
    MaskResult,
    compute_feasible,
)
from ..core.dsl import (
    JustificationV400,
    NormPatchV400,
    content_hash,
)
from ..core.norm_state import (
    NormStateV400,
    apply_patch,
    create_initial_norm_state,
    expire_rules,
)
from ..env.tri_demand import (
    ACTION_ID_MAP,
    ACTION_NAMES,
    Action,
    E,
    H,
    Observation,
    TriDemandV400,
)


# ============================================================================
# §4.2 — Interface Definitions
# ============================================================================


@dataclass
class DeliberationOutput:
    """
    Output from DELIBERATE stage.
    Per §4.2: justifications (minItems ≥ 1) and optional patch.
    """
    justifications: List[JustificationV400]
    patch: Optional[NormPatchV400] = None

    def __post_init__(self):
        if len(self.justifications) < 1:
            raise ValueError("justifications must have at least 1 item")


@dataclass
class MaskedActions:
    """
    Output from MASK stage.
    Per §4.2: feasible action IDs and count.
    """
    feasible: List[str]
    feasible_count: int


class SelectionSource(str, Enum):
    """Source of selection per §4.2 — NO DEFAULT."""
    AUTHORED = "AUTHORED"
    HALT = "HALT"


@dataclass
class Selection:
    """
    Output from SELECT stage.
    Per §4.2: action_id and source (AUTHORED or HALT only).
    """
    action_id: str
    source: SelectionSource


@dataclass
class ExecutionResult:
    """Output from EXECUTE stage."""
    obs: Observation
    reward: float
    done: bool
    info: Dict[str, Any]


# ============================================================================
# §4.3/4.4 — Selector (Blind, No Default)
# ============================================================================


class Selector:
    """
    Selector per §4.3 (blindness) and §4.4 (fail-not-substitute).

    Properties:
    - Receives only MaskedActions.feasible (action IDs)
    - No access to justifications, predicates, or normative state
    - Selects uniformly at random if multiple feasible
    - Returns HALT if feasible = []
    - NO DEFAULT SOURCE — defaults are forbidden
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def select(self, masked: MaskedActions) -> Selection:
        """
        Select action from feasible set.

        Per §4.3: blind selection with no access to justifications.
        Per §4.4: HALT if no feasible actions (no default/substitute).
        """
        if not masked.feasible:
            return Selection(action_id="HALT", source=SelectionSource.HALT)

        # Uniform random selection if multiple
        action_id = self.rng.choice(masked.feasible)
        return Selection(action_id=action_id, source=SelectionSource.AUTHORED)


# ============================================================================
# Deliberator Interface (LLM-backed in production)
# ============================================================================


class Deliberator(ABC):
    """
    Abstract deliberator interface.

    In production, this is backed by an LLM.
    For testing/calibration, we provide deterministic implementations.
    """

    @abstractmethod
    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Generate justifications and optional patch.

        Args:
            obs: Current observation
            norm_state: Current normative state

        Returns:
            DeliberationOutput with justifications and optional patch
        """
        pass


# ============================================================================
# §4.1 — MVRSA-4.0 Pipeline
# ============================================================================


@dataclass
class StepMetrics:
    """Metrics for a single step."""
    compilation_success: bool
    compilation_count: int
    halt: bool
    action_taken: Optional[str] = None
    reward: float = 0.0
    binding_obligation: Optional[str] = None


@dataclass
class EpisodeMetrics:
    """Metrics for a single episode."""
    steps: int
    total_reward: float
    success: bool
    timeout: bool
    halts: int
    compilation_failures: int
    compilation_total: int
    patches_applied: int


@dataclass
class RunMetrics:
    """Metrics for a complete run."""
    episodes: int
    total_steps: int
    success_rate: float
    halt_rate: float
    compilation_rate: float
    patches_applied: int


class MVRSA400:
    """
    Minimum Viable Reflective Sovereign Agent v4.0.

    Pipeline per §4.1:
    DELIBERATE → COMPILE → MASK → SELECT → EXECUTE

    With NormState persistence across episodes.
    """

    def __init__(
        self,
        deliberator: Deliberator,
        seed: int = 42,
        max_episodes: int = E,
        max_steps_per_episode: int = H,
    ):
        self.deliberator = deliberator
        self.seed = seed
        self.max_episodes = max_episodes
        self.max_steps_per_episode = max_steps_per_episode

        # Components
        self.env = TriDemandV400(seed=seed)
        self.selector = Selector(seed=seed)

        # State
        self.norm_state = create_initial_norm_state()
        self.current_episode = 0
        self.current_step = 0

        # Metrics
        self.episode_metrics: List[EpisodeMetrics] = []
        self.step_history: List[StepMetrics] = []

    def reset(self) -> None:
        """Reset agent state for new run."""
        self.norm_state = create_initial_norm_state()
        self.current_episode = 0
        self.current_step = 0
        self.episode_metrics = []
        self.step_history = []
        self.env = TriDemandV400(seed=self.seed)

    def run_episode(self) -> EpisodeMetrics:
        """
        Run a single episode.

        Returns EpisodeMetrics with success/failure and statistics.
        """
        # Handle rule expiration at episode boundary
        self.norm_state = expire_rules(self.norm_state, self.current_episode)

        # Reset environment
        obs = self.env.reset(episode=self.current_episode)

        episode_reward = 0.0
        episode_halts = 0
        episode_compilation_failures = 0
        episode_compilation_total = 0
        episode_patches = 0

        for step in range(self.max_steps_per_episode):
            self.current_step = step

            # DELIBERATE
            delib_output = self.deliberator.deliberate(obs, self.norm_state)

            # Check for trace excision (Run D)
            # If deliberator signals trace excision, skip compilation → SCHEMA_ERROR → HALT
            is_trace_excised = getattr(self.deliberator, 'is_trace_excised', False)

            if is_trace_excised:
                # TRUE TRACE EXCISION: No justification reaches compiler
                # Per v4.0.1: count as compilation failure, go to HALT
                episode_compilation_total += 1  # Count the attempt
                episode_compilation_failures += 1  # Count the failure

                # No compiled predicates → empty feasible set → HALT
                step_metrics = StepMetrics(
                    compilation_success=False,
                    compilation_count=0,
                    halt=True,
                    action_taken=None,
                    reward=-0.1,
                    binding_obligation=None,
                )
                self.step_history.append(step_metrics)
                episode_halts += 1
                continue

            # Apply patch if provided
            if delib_output.patch is not None:
                try:
                    self.norm_state, _ = apply_patch(self.norm_state, delib_output.patch)
                    episode_patches += 1
                except Exception as e:
                    # Patch failed — continue without it
                    pass

            # COMPILE
            compiler = JCOMP400(self.norm_state)
            batch = compiler.compile_justifications(delib_output.justifications)
            episode_compilation_total += len(batch.results)
            episode_compilation_failures += batch.failed_count

            # Get compiled predicates
            compiled_predicates = [
                r.predicate for r in batch.results
                if r.status == CompilationStatus.COMPILED and r.predicate is not None
            ]

            # MASK (with Obligation Gate)
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

            # Track step metrics
            step_metrics = StepMetrics(
                compilation_success=batch.compiled_count > 0,
                compilation_count=batch.compiled_count,
                halt=selection.source == SelectionSource.HALT,
                binding_obligation=mask_result.binding_obligation,
            )

            if selection.source == SelectionSource.HALT:
                episode_halts += 1
                # HALT = no action, episode continues but step is wasted
                step_metrics.action_taken = None
                step_metrics.reward = -0.1  # Penalty for halt
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

        # Episode metrics
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
            patches_applied=episode_patches,
        )

        self.episode_metrics.append(metrics)
        self.current_episode += 1

        return metrics

    def run(self) -> RunMetrics:
        """
        Run complete experiment (all episodes).

        Returns RunMetrics with aggregate statistics.
        """
        self.reset()

        for ep in range(self.max_episodes):
            self.run_episode()

        # Aggregate metrics
        total_steps = sum(m.steps for m in self.episode_metrics)
        success_count = sum(1 for m in self.episode_metrics if m.success)
        total_halts = sum(m.halts for m in self.episode_metrics)
        total_compilations = sum(m.compilation_total for m in self.episode_metrics)
        total_failures = sum(m.compilation_failures for m in self.episode_metrics)
        total_patches = sum(m.patches_applied for m in self.episode_metrics)

        return RunMetrics(
            episodes=len(self.episode_metrics),
            total_steps=total_steps,
            success_rate=success_count / len(self.episode_metrics) if self.episode_metrics else 0.0,
            halt_rate=total_halts / total_steps if total_steps > 0 else 0.0,
            compilation_rate=(total_compilations - total_failures) / total_compilations if total_compilations > 0 else 0.0,
            patches_applied=total_patches,
        )


# ============================================================================
# ASB Null Baseline (Uniform Random)
# ============================================================================


class ASBNullAgent:
    """
    ASB Null baseline: uniform random action selection.

    For calibration gate: should achieve ≤10% success rate.
    """

    def __init__(self, seed: int = 42, max_episodes: int = E, max_steps: int = H):
        self.seed = seed
        self.max_episodes = max_episodes
        self.max_steps = max_steps
        self.rng = random.Random(seed)

    def run(self) -> RunMetrics:
        """Run ASB Null baseline."""
        env = TriDemandV400(seed=self.seed)

        success_count = 0
        total_steps = 0

        for ep in range(self.max_episodes):
            env.reset(episode=ep)

            for step in range(self.max_steps):
                total_steps += 1

                # Get valid action mask
                mask = env.get_action_mask()
                valid_actions = [i for i, valid in enumerate(mask) if valid]

                if not valid_actions:
                    valid_actions = list(range(6))  # All actions

                action = self.rng.choice(valid_actions)
                obs, reward, done, info = env.step(action)

                if done:
                    if info.get("success", False):
                        success_count += 1
                    break

        return RunMetrics(
            episodes=self.max_episodes,
            total_steps=total_steps,
            success_rate=success_count / self.max_episodes,
            halt_rate=0.0,
            compilation_rate=1.0,  # No compilation in ASB
            patches_applied=0,
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Interfaces
    "DeliberationOutput",
    "MaskedActions",
    "SelectionSource",
    "Selection",
    "ExecutionResult",
    # Components
    "Selector",
    "Deliberator",
    "MVRSA400",
    # Metrics
    "StepMetrics",
    "EpisodeMetrics",
    "RunMetrics",
    # Baselines
    "ASBNullAgent",
]
