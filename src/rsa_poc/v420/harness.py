"""
RSA-PoC v4.2 — MVRSA-4.2 Pipeline Harness

Implements the Deliberate → Compile → Mask → Select → Execute pipeline
for v4.2 with LAW_REPAIR support.

Key v4.2 changes from v4.1:
- STAMP (A6) action support
- LAW_REPAIR gate integration (validity gates)
- Regime-aware contradiction detection
- Persistent norm_state across episodes (NOT reset per episode)
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple

from .core import (
    JCOMP420,
    JustificationV420,
    NormStateV420,
    create_initial_norm_state_v420,
    LawRepairAction,
    LawRepairGate,
    RepairValidationResult,
    TraceEntry,
    TraceLog,
)
from .env.tri_demand import TriDemandV420, Action, POSITIONS, Observation420
from .deliberator_oracle import DeliberationOutputV420, OracleDeliberatorV420


# ============================================================================
# §4.1 — Interface Dataclasses
# ============================================================================


class HaltReason(str, Enum):
    """Reason for HALT action."""
    NO_FEASIBLE_ACTIONS = "NO_FEASIBLE_ACTIONS"
    COMPILATION_FAILURE = "COMPILATION_FAILURE"
    DELIBERATION_FAILURE = "DELIBERATION_FAILURE"
    SELECTOR_ERROR = "SELECTOR_ERROR"
    CONTRADICTION_NO_REPAIR = "CONTRADICTION_NO_REPAIR"
    REPAIR_REJECTED = "REPAIR_REJECTED"


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
    deliberation: DeliberationOutputV420
    masked: MaskedActions
    selection: Selection
    execution: Optional[ExecutionResult]
    norm_hash_before: str
    norm_hash_after: str
    total_time_ms: float
    contradiction_detected: bool = False
    repair_attempted: bool = False
    repair_accepted: bool = False


# ============================================================================
# §4.2 — Deliberator Protocol
# ============================================================================


class DeliberatorProtocol(Protocol):
    """Protocol for deliberator implementations."""

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV420,
        episode: int,
        step: int
    ) -> DeliberationOutputV420:
        """Generate justifications for available actions."""
        ...


# ============================================================================
# §4.3 — Selector Implementations
# ============================================================================


class RandomSelector:
    """Random selector that uniformly samples from feasible actions."""

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


class ArgmaxSelector:
    """Argmax selector that picks the lowest-indexed feasible action."""

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

        sorted_actions = sorted(feasible_action_ids)
        action_id = sorted_actions[0]
        elapsed = (time.perf_counter() - start) * 1000
        return Selection(action_id=action_id, selection_time_ms=elapsed)


class TaskAwareSelector:
    """
    Task-aware selector that prefers progress actions over arbitrary movement.

    Priority order:
    1. STAMP (A6) - if regime=1, not stamped, have inventory, at ZONE_C (MUST stamp before deposit under regime=1)
    2. DEPOSIT (A5) - if at target zone with inventory (and stamped if regime=1)
    3. COLLECT (A4) - if at SOURCE with no inventory
    4. Movement toward goal (based on position)
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

        obs = observation
        pos = obs.agent_pos

        # Priority 1: STAMP if needed (MUST stamp before deposit under regime=1)
        if "A6" in feasible_action_ids and obs.regime == 1 and not obs.stamped and obs.inventory > 0:
            if pos == POSITIONS["ZONE_C"]:
                elapsed = (time.perf_counter() - start) * 1000
                return Selection(action_id="A6", selection_time_ms=elapsed)

        # Priority 2: DEPOSIT if at target zone with inventory (and stamped if regime=1)
        if "A5" in feasible_action_ids and obs.inventory > 0:
            # Under regime=1, must be stamped first
            if obs.regime == 1 and not obs.stamped:
                pass  # Skip deposit, need to stamp first
            else:
                # Check if at any unsatisfied zone
                at_zone = (
                    (pos == POSITIONS["ZONE_A"] and not obs.zone_a_satisfied) or
                    (pos == POSITIONS["ZONE_B"] and not obs.zone_b_satisfied) or
                    (pos == POSITIONS["ZONE_C"] and not obs.zone_c_satisfied)
                )
                if at_zone:
                    elapsed = (time.perf_counter() - start) * 1000
                    return Selection(action_id="A5", selection_time_ms=elapsed)

        # Priority 3: COLLECT at SOURCE
        if "A4" in feasible_action_ids and obs.inventory == 0:
            if pos == POSITIONS["SOURCE"]:
                elapsed = (time.perf_counter() - start) * 1000
                return Selection(action_id="A4", selection_time_ms=elapsed)

        # Priority 4: Movement toward goal
        # Determine goal
        if obs.inventory == 0:
            goal = POSITIONS["SOURCE"]
        elif obs.regime == 1 and not obs.stamped:
            goal = POSITIONS["ZONE_C"]
        elif not obs.zone_a_satisfied:
            goal = POSITIONS["ZONE_A"]
        elif not obs.zone_b_satisfied:
            goal = POSITIONS["ZONE_B"]
        elif not obs.zone_c_satisfied:
            goal = POSITIONS["ZONE_C"]
        else:
            goal = pos  # All done

        # Prefer movement toward goal
        row, col = pos
        goal_row, goal_col = goal
        preferred_moves = []

        if col < goal_col and "A2" in feasible_action_ids:
            preferred_moves.append("A2")  # MOVE_E
        if col > goal_col and "A3" in feasible_action_ids:
            preferred_moves.append("A3")  # MOVE_W
        if row > goal_row and "A0" in feasible_action_ids:
            preferred_moves.append("A0")  # MOVE_N
        if row < goal_row and "A1" in feasible_action_ids:
            preferred_moves.append("A1")  # MOVE_S

        if preferred_moves:
            action_id = preferred_moves[0]
        else:
            # Fallback: any feasible action
            action_id = sorted(feasible_action_ids)[0]

        elapsed = (time.perf_counter() - start) * 1000
        return Selection(action_id=action_id, selection_time_ms=elapsed)


# ============================================================================
# §4.4 — Validity Gate (Mask with Contradiction Detection)
# ============================================================================


def compute_feasible_v420(
    norm_state: NormStateV420,
    obs: Observation420,
    compiled_rules: List[Any],
) -> Tuple[List[str], bool, List[str]]:
    """
    Compute feasible actions with contradiction detection.

    Returns:
        (feasible_actions, is_contradiction, blocking_rule_ids)
    """
    # All actions A0-A6
    all_actions = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]
    feasible = []
    blocked_actions: Dict[str, List[str]] = {}

    # Check each action against compiled rules
    for action_id in all_actions:
        action_class = _action_to_class(action_id)
        is_blocked = False
        blocking_rules = []

        for rule_eval in compiled_rules:
            if rule_eval.rule_type == "PROHIBITION":
                effect = rule_eval.effect
                if effect.get("action_class") == action_class:
                    if rule_eval.active(obs, norm_state.norm_hash):
                        is_blocked = True
                        blocking_rules.append(rule_eval.rule_id)

        if is_blocked:
            blocked_actions[action_id] = blocking_rules
        else:
            feasible.append(action_id)

    # Check for contradiction: STAMP needed but blocked
    is_contradiction = False
    contradiction_blocking_rules = []

    if obs.regime == 1 and not obs.stamped and obs.inventory > 0:
        # Need STAMP for progress
        if "A6" not in feasible:
            is_contradiction = True
            contradiction_blocking_rules = blocked_actions.get("A6", [])

    return feasible, is_contradiction, contradiction_blocking_rules


def _action_to_class(action_id: str) -> str:
    """Map action ID to action class."""
    mapping = {
        "A0": "MOVE", "A1": "MOVE", "A2": "MOVE", "A3": "MOVE",
        "A4": "COLLECT", "A5": "DEPOSIT", "A6": "STAMP"
    }
    return mapping.get(action_id, "MOVE")


# ============================================================================
# §4.5 — MVRSA-4.2 Harness
# ============================================================================


@dataclass
class HarnessConfigV420:
    """Configuration for v4.2 harness."""
    max_steps_per_episode: int = 40  # H
    max_episodes: int = 20  # E
    seed: int = 42
    selector_type: str = "argmax"  # "random", "argmax", or "task_aware"
    record_telemetry: bool = True
    verbose: bool = False
    validity_gates_only: bool = True  # Only check validity, not full R1-R8


class MVRSA420Harness:
    """
    MVRSA-4.2 Pipeline Harness.

    Executes Deliberate → Compile → Mask → Select → Execute with:
    - LAW_REPAIR support
    - Contradiction detection
    - Persistent norm_state across episodes
    """

    def __init__(
        self,
        env: TriDemandV420,
        deliberator: DeliberatorProtocol,
        config: HarnessConfigV420,
    ):
        self.env = env
        self.deliberator = deliberator
        self.config = config

        # Selector
        if config.selector_type == "task_aware":
            self.selector = TaskAwareSelector()
        elif config.selector_type == "argmax":
            self.selector = ArgmaxSelector()
        else:
            self.selector = RandomSelector(seed=config.seed)

        # PERSISTENT state across episodes (v4.2 key invariant)
        self.norm_state = create_initial_norm_state_v420()
        self.trace_log = TraceLog(run_seed=config.seed)

        # Repair tracking
        self.repair_issued = False
        self.repair_accepted = False
        self.current_repair_epoch: Optional[str] = None

        # Compiler (refreshed when norm_state changes)
        self.compiler = JCOMP420(self.norm_state)

        # Telemetry
        self.step_records: List[StepRecord] = []
        self.episode_summaries: List[Dict[str, Any]] = []

        # Counters
        self.total_steps = 0
        self.total_halts = 0
        self.total_contradictions = 0
        self.total_repairs_attempted = 0
        self.total_repairs_accepted = 0

        # Extended telemetry (v4.2 gate classification)
        self.halts_by_reason: Dict[str, int] = {}  # HaltReason -> count
        self.continuity_checks_total = 0
        self.continuity_failures_total = 0
        self.repair_bindings: List[Dict[str, Any]] = []  # trace/repair binding records
        self._expected_norm_hash: Optional[str] = None  # for continuity checks

    def _recompile_rules(self):
        """Recompile rules after norm_state change."""
        self.compiler = JCOMP420(self.norm_state)
        self._compiled_rules = self.compiler.compile_all_rules()

    def _record_halt(self, reason: HaltReason):
        """Record a HALT with reason tracking."""
        self.total_halts += 1
        reason_key = reason.value
        self.halts_by_reason[reason_key] = self.halts_by_reason.get(reason_key, 0) + 1

    def reset_for_episode(self, episode: int) -> Observation420:
        """
        Reset environment for new episode.

        CRITICAL: norm_state is NOT reset. Law persists across episodes.
        Includes continuity check: norm_hash should not change unexpectedly.
        """
        # Continuity check: verify norm_hash hasn't drifted between episodes
        if episode > 0 and self._expected_norm_hash is not None:
            self.continuity_checks_total += 1
            current_hash = self.norm_state.norm_hash
            if current_hash != self._expected_norm_hash:
                self.continuity_failures_total += 1
                # Log but don't halt - this is telemetry

        obs, info = self.env.reset()

        # Refresh compiler (in case norm_state was modified)
        self._recompile_rules()

        # Record expected hash for next continuity check
        self._expected_norm_hash = self.norm_state.norm_hash

        return obs

    def _check_contradiction(
        self,
        obs: Observation420
    ) -> Tuple[bool, List[str]]:
        """Check if current state has contradiction."""
        _, is_contradiction, blocking_rules = compute_feasible_v420(
            self.norm_state, obs, self._compiled_rules
        )
        return is_contradiction, blocking_rules

    def _attempt_repair(
        self,
        obs: Observation420,
        blocking_rules: List[str],
        episode: int,
        step: int
    ) -> bool:
        """
        Attempt to issue and apply LAW_REPAIR.

        For validity gates only, we apply a simplified repair.
        Returns True if repair was accepted.
        """
        from .calibration import create_canonical_repair_action
        from .core.trace import TraceEntryID, TraceEntryType
        from datetime import datetime

        self.total_repairs_attempted += 1

        # Generate trace entry ID
        trace_entry_id = TraceEntryID.generate(
            run_seed=self.config.seed,
            episode=episode,
            step=step,
            entry_type="CONTRADICTION"
        )

        # Record contradiction in trace
        trace_entry = TraceEntry(
            trace_entry_id=trace_entry_id,
            entry_type=TraceEntryType.CONTRADICTION,
            run_seed=self.config.seed,
            episode=episode,
            step=step,
            timestamp=datetime.now().isoformat(),
            blocking_rule_ids=blocking_rules,
            active_obligation_target={"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"},
            progress_actions={"A6"}
        )
        self.trace_log.add(trace_entry)

        # Create repair action
        repair_action = create_canonical_repair_action(
            trace_entry_id=trace_entry_id,
            blocking_rule_ids=blocking_rules,
            prior_repair_epoch=self.current_repair_epoch
        )

        # Validity gates only: apply repair directly
        if self.config.validity_gates_only:
            success = self._apply_repair_direct(repair_action)
        else:
            # Full R1-R8 validation (not implemented in this version)
            success = self._apply_repair_with_gate(repair_action)

        if success:
            self.repair_issued = True
            self.repair_accepted = True
            self.total_repairs_accepted += 1

            # Record repair binding for telemetry
            self.repair_bindings.append({
                "trace_entry_id": str(trace_entry_id),
                "blocking_rule_ids": blocking_rules,
                "repair_epoch": self.current_repair_epoch,
                "episode": episode,
                "step": step,
                "accepted": True
            })
            return True

        # Record rejected repair
        self.repair_bindings.append({
            "trace_entry_id": str(trace_entry_id),
            "blocking_rule_ids": blocking_rules,
            "repair_epoch": None,
            "episode": episode,
            "step": step,
            "accepted": False
        })
        return False

    def _apply_repair_direct(self, repair_action: LawRepairAction) -> bool:
        """Apply repair directly (simplified for validity gates)."""
        from .core.dsl import Condition, ConditionOp
        import hashlib

        # Find R6 (PROHIBIT(STAMP)) and add exception
        patched_rules = []
        for rule in self.norm_state.rules:
            if rule.id == "R6":
                # Add exception: NOT (regime=1)
                new_condition = Condition(
                    op=ConditionOp.AND,
                    args=[
                        rule.condition,
                        Condition(
                            op=ConditionOp.NOT,
                            args=[
                                Condition(op=ConditionOp.REGIME_EQ, args=[1])
                            ]
                        )
                    ]
                )
                from dataclasses import replace
                patched_rule = replace(rule, condition=new_condition)
                patched_rules.append(patched_rule)
            else:
                patched_rules.append(rule)

        # Compute new repair epoch
        h = hashlib.sha256()
        h.update(self.norm_state.law_fingerprint.encode())
        h.update(repair_action.repair_fingerprint.encode())
        h.update(self.env.get_nonce())
        new_epoch = h.hexdigest()

        # Update norm state
        self.norm_state = NormStateV420(
            rules=patched_rules,
            repair_epoch=new_epoch
        )
        self._recompile_rules()

        self.current_repair_epoch = new_epoch
        return True

    def _apply_repair_with_gate(self, repair_action: LawRepairAction) -> bool:
        """Apply repair with full R1-R8 gate (not implemented)."""
        # This would use LawRepairGate.validate()
        raise NotImplementedError("Full R1-R8 gate validation not implemented")

    def run_step(
        self,
        obs: Observation420,
        episode: int,
        step: int
    ) -> Tuple[StepRecord, Observation420, bool]:
        """Execute a single pipeline step."""
        step_start = time.perf_counter()
        norm_hash_before = self.norm_state.norm_hash

        contradiction_detected = False
        repair_attempted = False
        repair_accepted = False

        # Check for contradiction before deliberation
        is_contradiction, blocking_rules = self._check_contradiction(obs)

        if is_contradiction:
            contradiction_detected = True
            self.total_contradictions += 1

            if not self.repair_accepted:
                # Attempt repair
                repair_attempted = True
                repair_accepted = self._attempt_repair(
                    obs, blocking_rules, episode, step
                )

                if not repair_accepted:
                    # Repair failed - HALT
                    self._record_halt(HaltReason.REPAIR_REJECTED)
                    masked = MaskedActions(
                        feasible=[],
                        feasible_count=0,
                        mask_time_ms=0.0,
                        error="Contradiction detected, repair rejected"
                    )
                    selection = Selection.halt(HaltReason.REPAIR_REJECTED)

                    record = StepRecord(
                        step=step,
                        episode=episode,
                        observation_before=obs,
                        deliberation=DeliberationOutputV420([], 0.0, error="Skipped due to repair"),
                        masked=masked,
                        selection=selection,
                        execution=None,
                        norm_hash_before=norm_hash_before,
                        norm_hash_after=self.norm_state.norm_hash,
                        total_time_ms=(time.perf_counter() - step_start) * 1000,
                        contradiction_detected=True,
                        repair_attempted=True,
                        repair_accepted=False
                    )
                    return record, obs, False
            else:
                # Already repaired but contradiction persists - BUG
                # This shouldn't happen with correct repair
                pass

        # Stage 1: Deliberate
        deliberation = self.deliberator.deliberate(obs, self.norm_state, episode, step)

        if not deliberation.success:
            self._record_halt(HaltReason.DELIBERATION_FAILURE)
            masked = MaskedActions(
                feasible=[],
                feasible_count=0,
                mask_time_ms=0.0,
                error=deliberation.error
            )
            selection = Selection.halt(HaltReason.DELIBERATION_FAILURE)

            record = StepRecord(
                step=step,
                episode=episode,
                observation_before=obs,
                deliberation=deliberation,
                masked=masked,
                selection=selection,
                execution=None,
                norm_hash_before=norm_hash_before,
                norm_hash_after=self.norm_state.norm_hash,
                total_time_ms=(time.perf_counter() - step_start) * 1000,
                contradiction_detected=contradiction_detected,
                repair_attempted=repair_attempted,
                repair_accepted=repair_accepted
            )
            return record, obs, False

        # Stage 2: Mask (compute feasible)
        mask_start = time.perf_counter()
        feasible, _, _ = compute_feasible_v420(
            self.norm_state, obs, self._compiled_rules
        )
        mask_elapsed = (time.perf_counter() - mask_start) * 1000

        # Filter to justified actions
        justified_actions = {j.action_id for j in deliberation.justifications}
        feasible_justified = [a for a in feasible if a in justified_actions]

        masked = MaskedActions(
            feasible=feasible_justified,
            feasible_count=len(feasible_justified),
            mask_time_ms=mask_elapsed
        )

        # Stage 3: Select
        if masked.is_halt:
            selection = Selection.halt(HaltReason.NO_FEASIBLE_ACTIONS)
            self._record_halt(HaltReason.NO_FEASIBLE_ACTIONS)
        else:
            selection = self.selector.select(
                feasible_action_ids=masked.feasible,
                observation=obs,
                episode=episode,
                step=step
            )

        # Stage 4: Execute
        execution: Optional[ExecutionResult] = None
        new_obs = obs
        done = False

        if not selection.is_halt:
            exec_start = time.perf_counter()

            # Map action ID to Action enum
            action = Action(int(selection.action_id[1:]))
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
            masked=masked,
            selection=selection,
            execution=execution,
            norm_hash_before=norm_hash_before,
            norm_hash_after=self.norm_state.norm_hash,
            total_time_ms=(time.perf_counter() - step_start) * 1000,
            contradiction_detected=contradiction_detected,
            repair_attempted=repair_attempted,
            repair_accepted=repair_accepted
        )

        self.total_steps += 1
        if self.config.record_telemetry:
            self.step_records.append(record)

        return record, new_obs, done

    def run_episode(self, episode: int) -> Dict[str, Any]:
        """Run a complete episode."""
        obs = self.reset_for_episode(episode)
        episode_start = time.perf_counter()

        episode_steps = 0
        episode_halts = 0
        episode_reward = 0.0
        episode_contradictions = 0
        episode_repairs = 0
        done = False

        while not done and episode_steps < self.config.max_steps_per_episode:
            record, obs, step_done = self.run_step(obs, episode, episode_steps)
            episode_steps += 1

            if record.selection.is_halt:
                episode_halts += 1
                break  # HALT terminates episode

            if record.execution:
                episode_reward += record.execution.reward
                done = record.execution.done

            if record.contradiction_detected:
                episode_contradictions += 1
            if record.repair_accepted:
                episode_repairs += 1

        episode_elapsed = (time.perf_counter() - episode_start) * 1000

        # Check success
        success = (
            obs.zone_a_satisfied and
            obs.zone_b_satisfied and
            obs.zone_c_satisfied
        )

        summary = {
            "episode": episode,
            "steps": episode_steps,
            "halts": episode_halts,
            "reward": episode_reward,
            "done": done,
            "success": success,
            "contradictions": episode_contradictions,
            "repairs": episode_repairs,
            "regime_at_end": obs.regime,
            "elapsed_ms": episode_elapsed,
            "final_norm_hash": self.norm_state.norm_hash
        }

        self.episode_summaries.append(summary)
        return summary

    def run(self) -> Dict[str, Any]:
        """Run the full experiment."""
        run_start = time.perf_counter()

        if self.config.verbose:
            print(f"Starting run: H={self.config.max_steps_per_episode}, "
                  f"E={self.config.max_episodes}, seed={self.config.seed}")

        for episode in range(self.config.max_episodes):
            summary = self.run_episode(episode)

            if self.config.verbose:
                elapsed_so_far = time.perf_counter() - run_start
                eta = elapsed_so_far / (episode + 1) * (self.config.max_episodes - episode - 1)
                print(f"  Episode {episode+1}/{self.config.max_episodes}: "
                      f"{summary['steps']} steps, "
                      f"success={summary['success']}, "
                      f"contradictions={summary['contradictions']}, "
                      f"repairs={summary['repairs']}, "
                      f"elapsed={elapsed_so_far:.1f}s, ETA={eta:.1f}s", flush=True)

        run_elapsed = (time.perf_counter() - run_start) * 1000

        # Compute summary stats
        total_successes = sum(1 for e in self.episode_summaries if e["success"])
        success_rate = total_successes / len(self.episode_summaries) if self.episode_summaries else 0

        return {
            "config": {
                "max_steps": self.config.max_steps_per_episode,
                "max_episodes": self.config.max_episodes,
                "seed": self.config.seed,
                "selector": self.config.selector_type,
                "validity_gates_only": self.config.validity_gates_only
            },
            "summary": {
                "total_steps": self.total_steps,
                "total_halts": self.total_halts,
                "total_contradictions": self.total_contradictions,
                "total_repairs_attempted": self.total_repairs_attempted,
                "total_repairs_accepted": self.total_repairs_accepted,
                "total_successes": total_successes,
                "success_rate": success_rate,
                "episodes_completed": len(self.episode_summaries),
                "elapsed_ms": run_elapsed
            },
            "gate_telemetry": {
                "repairs_submitted_total": self.total_repairs_attempted,
                "repairs_accepted_total": self.total_repairs_accepted,
                "repairs_rejected_total": self.total_repairs_attempted - self.total_repairs_accepted,
                "continuity_checks_total": self.continuity_checks_total,
                "continuity_failures_total": self.continuity_failures_total,
                "halts_by_reason": self.halts_by_reason,
                "repair_bindings": self.repair_bindings
            },
            "episodes": self.episode_summaries
        }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "HaltReason",
    "MaskedActions",
    "Selection",
    "ExecutionResult",
    "StepRecord",
    "DeliberatorProtocol",
    "RandomSelector",
    "ArgmaxSelector",
    "TaskAwareSelector",
    "HarnessConfigV420",
    "MVRSA420Harness",
    "compute_feasible_v420",
]
