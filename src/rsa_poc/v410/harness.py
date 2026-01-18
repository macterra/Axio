"""
RSA-PoC v4.1 — MVRSA-4.1 Pipeline Harness
Implements §4.1-4.8 of v41_design_freeze.md

The harness executes the Deliberate → Compile → Mask → Select → Execute
pipeline with strict interface boundaries.

Key v4.1 changes:
- Mask stage uses progress_set-based feasibility
- Selector blindness enforced at harness level
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple

from .core import (
    CompilationBatch,
    CompilationResult,
    CompilationStatus,
    JCOMP410,
    JustificationV410,
    MaskResult,
    NormStateV410,
    RuleEval,
    compute_feasible,
    content_hash,
    create_initial_norm_state,
)
from .env.tri_demand import TriDemandV410, Action


# ============================================================================
# §4.1 — Interface Dataclasses
# ============================================================================


class HaltReason(str, Enum):
    """Reason for HALT action."""
    NO_FEASIBLE_ACTIONS = "NO_FEASIBLE_ACTIONS"
    COMPILATION_FAILURE = "COMPILATION_FAILURE"
    DELIBERATION_FAILURE = "DELIBERATION_FAILURE"
    SELECTOR_ERROR = "SELECTOR_ERROR"


@dataclass
class DeliberationOutput:
    """Output from the deliberation stage."""
    justifications: List[JustificationV410]
    deliberation_time_ms: float
    raw_response: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.justifications) > 0


@dataclass
class MaskedAction:
    """A feasible action with its associated rule evaluators."""
    action_id: str
    rule_evals: List[RuleEval]


@dataclass
class MaskedActions:
    """Output from the Mask stage."""
    feasible: List[str]
    feasible_count: int
    mask_time_ms: float
    binding_obligation: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_halt(self) -> bool:
        return self.feasible_count == 0


@dataclass
class Selection:
    """Output from the Selector stage."""
    action_id: str
    selection_time_ms: float
    is_halt: bool = False
    halt_reason: Optional[HaltReason] = None

    @staticmethod
    def halt(reason: HaltReason) -> "Selection":
        return Selection(
            action_id="HALT",
            selection_time_ms=0.0,
            is_halt=True,
            halt_reason=reason
        )


@dataclass
class ExecutionResult:
    """Output from the Execute stage."""
    action_id: str
    observation: Any
    reward: float
    done: bool
    info: Dict[str, Any]
    execution_time_ms: float


@dataclass
class StepRecord:
    """Record of a single pipeline step for telemetry."""
    step: int
    episode: int
    observation_before: Any
    deliberation: DeliberationOutput
    compilation: Optional[CompilationBatch]
    masked: MaskedActions
    selection: Selection
    execution: Optional[ExecutionResult]
    norm_hash_before: str
    norm_hash_after: str
    total_time_ms: float


# ============================================================================
# §4.2 — Deliberator Protocol
# ============================================================================


class DeliberatorProtocol(Protocol):
    """Protocol for deliberator implementations."""

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV410,
        episode: int,
        step: int
    ) -> DeliberationOutput:
        """
        Generate justifications for available actions.

        Args:
            observation: Current environment observation
            norm_state: Current normative state
            episode: Current episode number
            step: Current step number

        Returns:
            DeliberationOutput with list of justifications
        """
        ...


# ============================================================================
# §4.3 — Selector Protocol (Blindness Enforced)
# ============================================================================


class SelectorProtocol(Protocol):
    """
    Protocol for selector implementations.

    CRITICAL: Selectors receive ONLY action IDs, not justifications.
    This enforces the blindness requirement from §4.3.
    """

    def select(
        self,
        feasible_action_ids: List[str],
        observation: Any,
        episode: int,
        step: int
    ) -> Selection:
        """
        Select an action from the feasible set.

        Args:
            feasible_action_ids: List of feasible action IDs (NO justifications!)
            observation: Current environment observation
            episode: Current episode number
            step: Current step number

        Returns:
            Selection with chosen action_id
        """
        ...


# ============================================================================
# §4.4 — Random Selector Implementation
# ============================================================================


class RandomSelector:
    """
    Random selector that uniformly samples from feasible actions.

    Used as default selector and for calibration runs.
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def select(
        self,
        feasible_action_ids: List[str],
        observation: Any,
        episode: int,
        step: int
    ) -> Selection:
        start = time.perf_counter()

        if not feasible_action_ids:
            return Selection.halt(HaltReason.NO_FEASIBLE_ACTIONS)

        action_id = self.rng.choice(feasible_action_ids)

        elapsed = (time.perf_counter() - start) * 1000
        return Selection(action_id=action_id, selection_time_ms=elapsed)


# ============================================================================
# §4.5 — Argmax Selector Implementation
# ============================================================================


class ArgmaxSelector:
    """
    Argmax selector that picks the lowest-indexed feasible action.

    Provides deterministic selection for debugging and testing.
    """

    def select(
        self,
        feasible_action_ids: List[str],
        observation: Any,
        episode: int,
        step: int
    ) -> Selection:
        start = time.perf_counter()

        if not feasible_action_ids:
            return Selection.halt(HaltReason.NO_FEASIBLE_ACTIONS)

        # Sort by action ID to ensure deterministic order
        sorted_actions = sorted(feasible_action_ids)
        action_id = sorted_actions[0]

        elapsed = (time.perf_counter() - start) * 1000
        return Selection(action_id=action_id, selection_time_ms=elapsed)


# ============================================================================
# §4.6 — MVRSA-4.1 Harness
# ============================================================================


@dataclass
class HarnessConfig:
    """Configuration for the MVRSA-4.1 harness."""
    max_steps_per_episode: int = 40  # H parameter
    max_episodes: int = 20  # E parameter
    max_conflicts: int = 10  # F parameter
    seed: int = 42
    selector_type: str = "random"  # "random" or "argmax"
    record_telemetry: bool = True
    verbose: bool = False  # Print progress updates


class MVRSA410Harness:
    """
    MVRSA-4.1 Pipeline Harness.

    Executes the Deliberate → Compile → Mask → Select → Execute pipeline
    with strict interface boundaries and telemetry recording.
    """

    def __init__(
        self,
        env: TriDemandV410,
        deliberator: DeliberatorProtocol,
        config: HarnessConfig,
        selector: Optional[SelectorProtocol] = None
    ):
        self.env = env
        self.deliberator = deliberator
        self.config = config

        # Initialize selector
        if selector is not None:
            self.selector = selector
        elif config.selector_type == "argmax":
            self.selector = ArgmaxSelector()
        else:
            self.selector = RandomSelector(seed=config.seed)

        # Initialize norm state
        self.norm_state = create_initial_norm_state()

        # Initialize compiler (will be refreshed per step)
        self.compiler = JCOMP410(self.norm_state)

        # Telemetry
        self.step_records: List[StepRecord] = []
        self.episode_summaries: List[Dict[str, Any]] = []

        # Counters
        self.total_steps = 0
        self.total_halts = 0
        self.total_conflicts = 0

    def reset_for_episode(self, episode: int) -> Any:
        """Reset environment and norm state for new episode."""
        obs, _ = self.env.reset()

        # Expire rules at episode boundary
        from .core import expire_rules
        self.norm_state = expire_rules(self.norm_state, episode)

        # Refresh compiler with updated norm state
        self.compiler = JCOMP410(self.norm_state)

        return obs

    def run_step(
        self,
        obs: Any,
        episode: int,
        step: int
    ) -> Tuple[StepRecord, Any, bool]:
        """
        Execute a single pipeline step.

        Returns:
            Tuple of (StepRecord, new_observation, done)
        """
        step_start = time.perf_counter()
        norm_hash_before = self.norm_state.norm_hash

        # Stage 1: Deliberate
        deliberation = self.deliberator.deliberate(obs, self.norm_state, episode, step)

        if not deliberation.success:
            # Deliberation failure → HALT
            masked = MaskedActions(
                feasible=[],
                feasible_count=0,
                mask_time_ms=0.0,
                error=deliberation.error
            )
            selection = Selection.halt(HaltReason.DELIBERATION_FAILURE)
            self.total_halts += 1

            record = StepRecord(
                step=step,
                episode=episode,
                observation_before=obs,
                deliberation=deliberation,
                compilation=None,
                masked=masked,
                selection=selection,
                execution=None,
                norm_hash_before=norm_hash_before,
                norm_hash_after=norm_hash_before,
                total_time_ms=(time.perf_counter() - step_start) * 1000
            )
            return record, obs, False

        # Stage 2: Compile
        justifications_json = [json.dumps(j.to_dict()) for j in deliberation.justifications]
        compilation = self.compiler.compile_batch(justifications_json)

        # Collect all compiled rule evaluators
        all_rule_evals: List[RuleEval] = []
        for result in compilation.results:
            if result.status == CompilationStatus.COMPILED and result.rule_evals:
                all_rule_evals.extend(result.rule_evals)

        if not all_rule_evals:
            # All compilations failed → HALT
            masked = MaskedActions(
                feasible=[],
                feasible_count=0,
                mask_time_ms=0.0,
                error="All compilations failed"
            )
            selection = Selection.halt(HaltReason.COMPILATION_FAILURE)
            self.total_halts += 1

            record = StepRecord(
                step=step,
                episode=episode,
                observation_before=obs,
                deliberation=deliberation,
                compilation=compilation,
                masked=masked,
                selection=selection,
                execution=None,
                norm_hash_before=norm_hash_before,
                norm_hash_after=norm_hash_before,
                total_time_ms=(time.perf_counter() - step_start) * 1000
            )
            return record, obs, False

        # Stage 3: Mask (Obligation Gate)
        mask_start = time.perf_counter()
        mask_result = compute_feasible(
            compiled_rules=all_rule_evals,
            norm_state=self.norm_state,
            obs=obs,
            env=self.env,
            current_norm_hash=self.norm_state.norm_hash
        )
        mask_elapsed = (time.perf_counter() - mask_start) * 1000

        masked = MaskedActions(
            feasible=mask_result.feasible,
            feasible_count=mask_result.feasible_count,
            mask_time_ms=mask_elapsed,
            binding_obligation=mask_result.binding_obligation,
            error=mask_result.error
        )

        # Stage 4: Select (with blindness enforced)
        if masked.is_halt:
            selection = Selection.halt(HaltReason.NO_FEASIBLE_ACTIONS)
            self.total_halts += 1
        else:
            # CRITICAL: Selector receives ONLY action IDs, not justifications
            selection = self.selector.select(
                feasible_action_ids=masked.feasible,
                observation=obs,
                episode=episode,
                step=step
            )

        # Stage 5: Execute
        execution: Optional[ExecutionResult] = None
        new_obs = obs
        done = False

        if not selection.is_halt:
            exec_start = time.perf_counter()

            # Map action ID to Action enum
            action = Action(int(selection.action_id[1:]))  # "A0" → 0
            new_obs, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated

            execution = ExecutionResult(
                action_id=selection.action_id,
                observation=new_obs,
                reward=reward,
                done=done,
                info=info,
                execution_time_ms=(time.perf_counter() - exec_start) * 1000
            )

        # Create step record
        record = StepRecord(
            step=step,
            episode=episode,
            observation_before=obs,
            deliberation=deliberation,
            compilation=compilation,
            masked=masked,
            selection=selection,
            execution=execution,
            norm_hash_before=norm_hash_before,
            norm_hash_after=self.norm_state.norm_hash,
            total_time_ms=(time.perf_counter() - step_start) * 1000
        )

        self.total_steps += 1
        if self.config.record_telemetry:
            self.step_records.append(record)

        return record, new_obs, done

    def run_episode(self, episode: int) -> Dict[str, Any]:
        """
        Run a complete episode.

        Returns:
            Episode summary dictionary
        """
        obs = self.reset_for_episode(episode)
        episode_start = time.perf_counter()

        episode_steps = 0
        episode_halts = 0
        episode_reward = 0.0
        done = False

        while not done and episode_steps < self.config.max_steps_per_episode:
            record, obs, done = self.run_step(obs, episode, episode_steps)
            episode_steps += 1

            if record.selection.is_halt:
                episode_halts += 1

            if record.execution:
                episode_reward += record.execution.reward

        episode_elapsed = (time.perf_counter() - episode_start) * 1000

        summary = {
            "episode": episode,
            "steps": episode_steps,
            "halts": episode_halts,
            "reward": episode_reward,
            "done": done,
            "elapsed_ms": episode_elapsed,
            "final_norm_hash": self.norm_state.norm_hash
        }

        self.episode_summaries.append(summary)
        return summary

    def run(self) -> Dict[str, Any]:
        """
        Run the full experiment.

        Returns:
            Experiment summary dictionary
        """
        run_start = time.perf_counter()

        if self.config.verbose:
            print(f"    Starting run: H={self.config.max_steps_per_episode}, E={self.config.max_episodes}, seed={self.config.seed}")

        for episode in range(self.config.max_episodes):
            self.run_episode(episode)

            if self.config.verbose:
                ep_summary = self.episode_summaries[-1]
                elapsed_so_far = (time.perf_counter() - run_start)
                eta = elapsed_so_far / (episode + 1) * (self.config.max_episodes - episode - 1)
                print(f"      Episode {episode+1}/{self.config.max_episodes}: "
                      f"{ep_summary['steps']} steps, {ep_summary['halts']} halts, "
                      f"reward={ep_summary['reward']:.1f}, "
                      f"elapsed={elapsed_so_far:.1f}s, ETA={eta:.1f}s", flush=True)

            # Check conflict budget
            if self.total_conflicts >= self.config.max_conflicts:
                if self.config.verbose:
                    print(f"    ⚠ Conflict budget exhausted at episode {episode+1}")
                break

        run_elapsed = (time.perf_counter() - run_start) * 1000

        return {
            "config": {
                "max_steps": self.config.max_steps_per_episode,
                "max_episodes": self.config.max_episodes,
                "max_conflicts": self.config.max_conflicts,
                "seed": self.config.seed,
                "selector": self.config.selector_type
            },
            "summary": {
                "total_steps": self.total_steps,
                "total_halts": self.total_halts,
                "total_conflicts": self.total_conflicts,
                "episodes_completed": len(self.episode_summaries),
                "elapsed_ms": run_elapsed
            },
            "episodes": self.episode_summaries
        }


# ============================================================================
# §4.7 — Guardrail Check
# ============================================================================


def check_guardrails(
    results: Dict[str, Any],
    c_min: float = 0.70,
    h_max: float = 0.20,
    a_max: float = 0.10
) -> Dict[str, Any]:
    """
    Check experiment results against guardrails.

    Args:
        results: Experiment results from harness.run()
        c_min: Minimum compliance rate
        h_max: Maximum halt rate
        a_max: Maximum anomaly rate

    Returns:
        Guardrail check results
    """
    total_steps = results["summary"]["total_steps"]
    total_halts = results["summary"]["total_halts"]

    if total_steps == 0:
        return {
            "passed": False,
            "reason": "No steps executed",
            "metrics": {}
        }

    # Calculate rates
    halt_rate = total_halts / total_steps
    # Compliance = 1 - halt_rate for now (more sophisticated in full impl)
    compliance_rate = 1.0 - halt_rate
    # Anomaly rate placeholder (would require more detailed analysis)
    anomaly_rate = 0.0

    passed = (
        compliance_rate >= c_min and
        halt_rate <= h_max and
        anomaly_rate <= a_max
    )

    return {
        "passed": passed,
        "metrics": {
            "compliance_rate": compliance_rate,
            "halt_rate": halt_rate,
            "anomaly_rate": anomaly_rate
        },
        "thresholds": {
            "c_min": c_min,
            "h_max": h_max,
            "a_max": a_max
        }
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "HaltReason",
    "DeliberationOutput",
    "MaskedAction",
    "MaskedActions",
    "Selection",
    "ExecutionResult",
    "StepRecord",
    "DeliberatorProtocol",
    "SelectorProtocol",
    "RandomSelector",
    "ArgmaxSelector",
    "HarnessConfig",
    "MVRSA410Harness",
    "check_guardrails",
]
