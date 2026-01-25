"""
RSA-PoC v4.2 — Ablation Variants (B and C)

Implements:
- Ablation B: Reflection Excision (break R7 via trace unavailability)
- Ablation C: Persistence Excision (break R5/R6 via norm_state reset)

These ablations are expected to collapse under v4.2 because:
- B: Cannot cite valid trace_entry_id / blocking_rule_ids → R7 rejects repair
- C: Repair epoch lost each episode → R6 rejects repair on subsequent episodes

"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .env.tri_demand import (
    Action,
    Observation420 as Observation,
    POSITIONS,
    TriDemandV420,
)
from .core.norm_state import NormStateV420, create_initial_norm_state_v420
from .core.compiler import JCOMP420
from .core.trace import TraceEntry, TraceEntryID, TraceLog, TraceEntryType
from .core.law_repair import LawRepairAction, LawRepairGate, RepairValidationResult
from .core.dsl import PatchOp, PatchOperation

from .calibration import (
    move_toward,
    create_canonical_repair_action,
    TaskOracleV420,
    TaskOracleCalibrationConfigV420,
)


# ============================================================================
# §B.0 — Ablation Flags
# ============================================================================


# Ablation B: Reflection Excision
# When True, trace access returns None/empty, making R7 validation fail
ABLATION_REFLECTION_EXCISE = False

# Ablation C: Persistence Excision
# When True, norm_state is reset at each episode boundary
ABLATION_PERSISTENCE_EXCISE = False


# ============================================================================
# §B.1 — Typed Exception for Trace Unavailability
# ============================================================================


class TraceUnavailableError(Exception):
    """
    Raised when trace access is excised (Ablation B).

    This error propagates to LAW_REPAIR construction, resulting in
    an invalid repair that will fail R7 validation.
    """
    pass


# ============================================================================
# §B.2 — Ablation B: Reflection-Excised Task Oracle
# ============================================================================


class TaskOracleReflectionExcisedV420(TaskOracleV420):
    """
    Task Oracle v4.2 with Reflection Excision (Ablation B).

    Trace access is stubbed to return:
    - trace_entry_id = None
    - rule_ids = []

    Expected behavior:
    - Contradiction is detected (detection remains intact)
    - Agent attempts LAW_REPAIR but cannot cite valid trace
    - Repair fails R7 validation → HALT
    """

    def __init__(
        self,
        norm_state: NormStateV420,
        trace_log: TraceLog,
        run_seed: int = 42
    ):
        super().__init__(norm_state, trace_log, run_seed)
        # Track R7 failures for diagnostics
        self.r7_failures = 0

    def _get_trace_entry_id_for_contradiction(
        self,
        episode: int,
        step: int,
    ) -> Optional[str]:
        """
        Stubbed trace access: returns None.

        In baseline, this would return a valid TraceEntryID.
        Under Ablation B, trace is unavailable.
        """
        # ABLATION B: Trace access is excised
        return None

    def _get_blocking_rule_ids(
        self,
        obs: Observation,
    ) -> List[str]:
        """
        Stubbed blocking rule query: returns empty list.

        In baseline, this would return the blocking rule IDs from trace.
        Under Ablation B, this information is unavailable.
        """
        # ABLATION B: Blocking rules unavailable from trace
        return []

    def get_action(
        self,
        obs: Observation,
        episode: int,
        step: int
    ) -> Tuple[Action, Optional[LawRepairAction]]:
        """
        Get action with Reflection Excision.

        When contradiction is detected, attempts repair but with
        invalid trace_entry_id (None) and empty rule_ids.
        """
        regime = obs.regime

        # Check for contradiction under regime=1
        if regime == 1 and not self.repair_accepted:
            # Check if we're in a state where STAMP is needed but blocked
            if self._needs_stamp(obs):
                is_blocked, _actual_blocking_rules = self._check_stamp_blocked(obs)

                if is_blocked and not self.repair_issued:
                    # ========================================================
                    # ABLATION B: Trace access is excised
                    # ========================================================
                    trace_entry_id = self._get_trace_entry_id_for_contradiction(
                        episode=episode,
                        step=step,
                    )
                    blocking_rule_ids = self._get_blocking_rule_ids(obs)

                    # Trace entry is still created (detection intact) but agent
                    # cannot access it for repair construction
                    from datetime import datetime
                    actual_trace_entry_id = TraceEntryID.generate(
                        run_seed=self.run_seed,
                        episode=episode,
                        step=step,
                        entry_type="CONTRADICTION"
                    )
                    trace_entry = TraceEntry(
                        trace_entry_id=actual_trace_entry_id,
                        entry_type=TraceEntryType.CONTRADICTION,
                        run_seed=self.run_seed,
                        episode=episode,
                        step=step,
                        timestamp=datetime.now().isoformat(),
                        blocking_rule_ids=_actual_blocking_rules,  # Actual rules stored
                        active_obligation_target={"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"},
                        progress_actions={"A6"}
                    )
                    self.trace_log.add(trace_entry)

                    # Attempt repair with excised trace info
                    # trace_entry_id = None, blocking_rule_ids = []
                    if trace_entry_id is None:
                        # Cannot construct valid repair without trace_entry_id
                        # This will fail R7 when submitted
                        repair_action = LawRepairAction(
                            trace_entry_id="INVALID_NO_TRACE_ACCESS",  # Invalid ID
                            rule_ids=blocking_rule_ids,  # Empty list
                            prior_repair_epoch=self.current_repair_epoch,
                            patch_ops=[
                                {
                                    "target_rule_id": "R6",  # Guessed, not from trace
                                    "op": PatchOp.ADD_EXCEPTION.value,
                                    "exception_condition": {
                                        "op": "AND",
                                        "args": [
                                            {"op": "REGIME_EQ", "args": [1]},
                                            {"op": "TRUE", "args": []}
                                        ]
                                    }
                                }
                            ]
                        )
                    else:
                        repair_action = create_canonical_repair_action(
                            trace_entry_id=trace_entry_id,
                            blocking_rule_ids=blocking_rule_ids,
                            prior_repair_epoch=self.current_repair_epoch
                        )

                    self.repair_issued = True
                    return Action.MOVE_N, repair_action

        # Standard task oracle logic
        return self._task_policy(obs), None


# ============================================================================
# §B.3 — Ablation B Calibration Runner
# ============================================================================


@dataclass
class AblationBCalibrationConfig:
    """Configuration for Ablation B calibration."""
    max_steps_per_episode: int = 40
    max_episodes: int = 100
    seed: int = 42


class AblationBCalibrationV420:
    """
    Ablation B: Reflection Excision Calibration.

    Expected behavior:
    - Contradiction detected at regime flip (episode 2)
    - Agent attempts LAW_REPAIR with invalid trace info
    - Repair fails R7 (trace_entry_id not found, rule_ids empty)
    - Agent HALTs (cannot make progress)

    Success criteria for ablation:
    - Halt rate > 0 (demonstrates R7 enforcement)
    - Success rate significantly lower than baseline
    """

    def __init__(self, config: AblationBCalibrationConfig):
        self.config = config
        self.env = TriDemandV420(seed=config.seed)

    def _is_success(self, obs: Observation) -> bool:
        """Episode success: all three zones satisfied."""
        return (
            obs.zone_a_satisfied and
            obs.zone_b_satisfied and
            obs.zone_c_satisfied
        )

    def _check_contradiction(
        self,
        obs: Observation,
        norm_state: NormStateV420
    ) -> Tuple[bool, List[str]]:
        """Check if current state has contradiction."""
        if not (obs.regime == 1 and not obs.stamped and obs.inventory > 0):
            return False, []

        compiler = JCOMP420(norm_state)
        compiled_rules = compiler.compile_all_rules()
        blocking_rules = []

        for rule_eval in compiled_rules:
            if rule_eval.rule_type == "PROHIBITION":
                effect = rule_eval.effect
                if effect.get("action_class") == "STAMP":
                    if rule_eval.active(obs, norm_state.norm_hash):
                        blocking_rules.append(rule_eval.rule_id)

        return len(blocking_rules) > 0, blocking_rules

    def run(self) -> Dict[str, Any]:
        """Run Ablation B calibration."""
        start_time = time.perf_counter()

        total_steps = 0
        total_successes = 0
        total_halts = 0
        total_r7_failures = 0
        contradictions_detected = 0
        repairs_attempted = 0
        repairs_rejected_r7 = 0
        episode_summaries = []

        # Norm state and oracle persist across episodes (persistence intact)
        norm_state = create_initial_norm_state_v420()
        trace_log = TraceLog(run_seed=self.config.seed)

        oracle = TaskOracleReflectionExcisedV420(
            norm_state=norm_state,
            trace_log=trace_log,
            run_seed=self.config.seed
        )

        # Create the repair gate for validation
        from .core.compiler import JCOMP420_HASH
        gate = LawRepairGate(
            trace_log=trace_log,
            compiler_hash=JCOMP420_HASH,
            env_progress_set_fn=lambda obs, tgt: {"A6"} if obs.regime == 1 and not obs.stamped else set(),
            env_target_satisfied_fn=lambda obs, tgt: False,
            current_repair_epoch=None,
            regime=0,
        )

        for episode in range(self.config.max_episodes):
            obs, info = self.env.reset()
            episode_steps = 0
            success = False
            halted = False
            episode_r7_failure = False

            # Update gate regime
            gate.regime = obs.regime

            while episode_steps < self.config.max_steps_per_episode:
                if self._is_success(obs):
                    success = True
                    break

                # Check for contradiction
                is_contradiction, blocking_rules = self._check_contradiction(
                    obs, oracle.norm_state
                )

                if is_contradiction:
                    contradictions_detected += 1

                # Get action from excised oracle
                action, repair_action = oracle.get_action(
                    obs=obs,
                    episode=episode,
                    step=episode_steps
                )

                # Handle repair attempt
                if repair_action is not None:
                    repairs_attempted += 1

                    # Validate through gate (expected to fail R7)
                    compiler = JCOMP420(oracle.norm_state)

                    result = gate.validate(
                        repair_action=repair_action,
                        norm_state=oracle.norm_state,
                        obs=obs,
                        active_obligation_target={"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"},
                        compiled_permitted_actions=set(),  # STAMP blocked
                        compile_fn=lambda ns: JCOMP420(ns).compile_all_rules(),
                        compiler_hash=JCOMP420_HASH,
                    )

                    if not result.valid:
                        repairs_rejected_r7 += 1

                        # Check if failure is R7-related
                        if result.failure_reason and "R7" in result.failure_reason.value:
                            total_r7_failures += 1
                            episode_r7_failure = True

                        # Repair rejected → HALT (cannot resolve contradiction)
                        halted = True
                        total_halts += 1
                        break
                    else:
                        # Unexpected: repair should not pass with excised trace
                        oracle.apply_repair_direct(
                            repair_action=repair_action,
                            env_nonce=self.env.get_nonce(),
                        )

                # Execute action
                obs, reward, terminated, truncated, info = self.env.step(action)
                episode_steps += 1
                total_steps += 1

                # Update gate regime
                gate.regime = obs.regime

                if terminated or truncated:
                    if self._is_success(obs):
                        success = True
                    break

            if success:
                total_successes += 1

            episode_summaries.append({
                "episode": episode,
                "steps": episode_steps,
                "success": success,
                "halted": halted,
                "r7_failure": episode_r7_failure,
                "regime_at_end": obs.regime
            })

        elapsed = (time.perf_counter() - start_time) * 1000
        success_rate = total_successes / self.config.max_episodes
        halt_rate = total_halts / self.config.max_episodes

        # Ablation B should show:
        # - Halts occur (R7 enforcement working)
        # - Success rate < baseline (cannot repair)
        ablation_effective = total_halts > 0 or success_rate < 0.5

        return {
            "calibration_type": "ABLATION_B_REFLECTION_EXCISION_V420",
            "description": "Ablation B - Reflection Excision (trace access stubbed)",
            "ablation_flag": "ABLATION_REFLECTION_EXCISE=True",
            "config": {
                "max_steps": self.config.max_steps_per_episode,
                "max_episodes": self.config.max_episodes,
                "seed": self.config.seed
            },
            "summary": {
                "total_steps": total_steps,
                "total_successes": total_successes,
                "success_rate": success_rate,
                "total_halts": total_halts,
                "halt_rate": halt_rate,
                "elapsed_ms": elapsed,
                "ablation_effective": ablation_effective
            },
            "r7_enforcement": {
                "contradictions_detected": contradictions_detected,
                "repairs_attempted": repairs_attempted,
                "repairs_rejected_r7": repairs_rejected_r7,
                "total_r7_failures": total_r7_failures,
            },
            "expected_behavior": {
                "halt_on_r7": "Agent cannot cite valid trace_entry_id → R7 rejects",
                "blocking_rule_ids_empty": "Agent cannot identify blocking rules",
            },
            "episodes": episode_summaries
        }


# ============================================================================
# §C.1 — Ablation C: Persistence-Excised Task Oracle
# ============================================================================


class TaskOraclePersistenceExcisedV420(TaskOracleV420):
    """
    Task Oracle v4.2 with Persistence Excision (Ablation C).

    The agent loses ALL cross-episode normative state at each episode
    boundary via `on_episode_start()`. This includes:
    - norm_state (repaired law forgotten)
    - current_repair_epoch (epoch cache cleared)
    - All epoch memory (no side-channel persistence)

    Expected failure path:
    - Episode 2: Contradiction detected, repair issued, repair accepted
    - Episode 3+: on_episode_start() resets ALL normative state
    - Agent has no epoch memory (current_repair_epoch = None)
    - Contradiction recurs (PROHIBIT(STAMP) is back)
    - Agent attempts repair but cannot cite prior_repair_epoch (it's None)
    - Gate rejects via R6 (missing prior epoch when env expects one)
    - HALT

    NOTE: This class is used by the standard run harness (not a calibration fork).
    The excision is in the agent, not the harness.

    FORBIDDEN: Agent must NOT be able to query env.repair_epoch or any
    environment continuity state. The harness must not expose this.
    """

    def __init__(
        self,
        norm_state: NormStateV420,
        trace_log: TraceLog,
        run_seed: int = 42
    ):
        super().__init__(norm_state, trace_log, run_seed)
        # Track episode resets for diagnostics
        self.episode_resets = 0

    def on_episode_start(self, episode: int) -> None:
        """
        Called at the start of each episode by the run harness.

        Under Ablation C, this resets ALL agent normative state:
        - norm_state (law and repair_epoch)
        - current_repair_epoch (agent's epoch cache)
        - repair tracking flags

        The agent loses ALL cross-episode normative memory.
        Only the environment retains its repair_epoch.
        """
        if episode > 0:
            # ================================================================
            # ABLATION C: Reset ALL agent normative state at episode boundary
            # ================================================================

            # Reset norm_state to initial (repaired law forgotten)
            self.norm_state = create_initial_norm_state_v420()
            self._recompile_rules()

            # Reset ALL epoch memory (no side-channel persistence allowed)
            self.current_repair_epoch = None

            # Reset repair tracking (agent "forgets" it repaired)
            self.repair_issued = False
            self.repair_accepted = False

            self.episode_resets += 1


# ============================================================================
# Convenience Runner (Ablation B only - C uses standard harness)
# ============================================================================


def run_ablation_b(seed: int = 42, episodes: int = 100) -> Dict[str, Any]:
    """Run Ablation B (Reflection Excision) calibration."""
    config = AblationBCalibrationConfig(
        max_steps_per_episode=40,
        max_episodes=episodes,
        seed=seed
    )
    runner = AblationBCalibrationV420(config)
    return runner.run()


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    # Flags
    "ABLATION_REFLECTION_EXCISE",
    "ABLATION_PERSISTENCE_EXCISE",
    # Exceptions
    "TraceUnavailableError",
    # Ablation B
    "TaskOracleReflectionExcisedV420",
    "AblationBCalibrationConfig",
    "AblationBCalibrationV420",
    "run_ablation_b",
    # Ablation C (agent class only, no calibration fork)
    "TaskOraclePersistenceExcisedV420",
]
