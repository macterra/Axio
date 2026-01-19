"""
RSA-PoC v4.2 — Calibration Baselines
Implements §9 of poc_spec_v4.2.md

Four calibration baselines:
1. Task Oracle v4.2 - Scripted policy with LAW_REPAIR capability
2. ASB Null - Uniform random action (must HALT at contradiction)
3. Repair-capable solvability witness

Key v4.2 changes from v4.1:
- Task Oracle must issue LAW_REPAIR when contradiction detected under regime=1
- Calibration must demonstrate repair is necessary and feasible
- ASB Null expected to HALT at first contradiction (no repair capability)
"""

from __future__ import annotations

import json
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
from .core.trace import TraceEntry, TraceEntryID, TraceLog
from .core.law_repair import LawRepairAction, LawRepairGate, RepairValidationResult
from .core.dsl import PatchOp, PatchOperation, Rule


# ============================================================================
# §9.0 — Movement Utilities
# ============================================================================


def move_toward(pos: Tuple[int, int], goal: Tuple[int, int]) -> Action:
    """
    Deterministic movement toward goal position.

    Uses (row, col) semantics:
    - MOVE_N (A0): row -= 1
    - MOVE_S (A1): row += 1
    - MOVE_E (A2): col += 1
    - MOVE_W (A3): col -= 1

    Tie-breaking: E/W before N/S (column then row).
    """
    row, col = pos
    goal_row, goal_col = goal

    if col < goal_col:
        return Action.MOVE_E  # col += 1
    if col > goal_col:
        return Action.MOVE_W  # col -= 1
    if row > goal_row:
        return Action.MOVE_N  # row -= 1
    if row < goal_row:
        return Action.MOVE_S  # row += 1

    # Already at goal - shouldn't happen if called correctly
    return Action.MOVE_N  # Arbitrary fallback


# ============================================================================
# §9.1 — Task Oracle v4.2 Policy (with LAW_REPAIR)
# ============================================================================


def create_canonical_repair_action(
    trace_entry_id: str,
    blocking_rule_ids: List[str],
    prior_repair_epoch: Optional[str],
) -> LawRepairAction:
    """
    Create the canonical repair action for the STAMP prohibition.

    This is the minimal patch: add an exception to R6 (PROHIBIT(STAMP))
    to allow STAMP when regime=1.

    Patch: PROHIBIT(STAMP) → PROHIBIT(STAMP) UNLESS (regime==1)
    """
    # Build the exception condition: regime == 1
    exception_condition: Dict[str, Any] = {
        "op": "AND",
        "args": [
            {"op": "REGIME_EQ", "args": [1]},
            {"op": "TRUE", "args": []}  # Could add active_obligation check
        ]
    }

    # Create patch operation: ADD_EXCEPTION to R6
    patch_ops = [
        {
            "target_rule_id": "R6",
            "op": PatchOp.ADD_EXCEPTION.value,
            "exception_condition": exception_condition
        }
    ]

    return LawRepairAction(
        trace_entry_id=trace_entry_id,
        rule_ids=blocking_rule_ids,
        prior_repair_epoch=prior_repair_epoch,
        patch_ops=patch_ops
    )


class TaskOracleV420:
    """
    Task Oracle v4.2: Scripted policy with LAW_REPAIR capability.

    Under regime=0: Behaves exactly as v4.1 Oracle (task completion).
    Under regime=1: When contradiction detected, issues LAW_REPAIR,
                    then proceeds to STAMP and complete task.

    This is a solvability witness, not an RSA component.
    Oracle is privileged for calibration: it can read trace log directly.

    NOTE: For calibration, we use a simplified repair mechanism that
    directly patches the norm state without full R1-R8 validation.
    The full gate is tested separately.
    """

    def __init__(
        self,
        norm_state: NormStateV420,
        trace_log: TraceLog,
        run_seed: int = 42
    ):
        self.norm_state = norm_state
        self.trace_log = trace_log
        self.run_seed = run_seed

        # Track whether repair has been issued
        self.repair_issued = False
        self.repair_accepted = False
        self.current_repair_epoch: Optional[str] = None

        # Compile initial rules
        self._recompile_rules()

    def _recompile_rules(self):
        """Recompile rules after any modification."""
        compiler = JCOMP420(self.norm_state)
        self.compiled_rules = compiler.compile_all_rules()

    def _check_stamp_blocked(self, obs: Observation) -> Tuple[bool, List[str]]:
        """
        Check if STAMP action is blocked by compiled rules.

        Returns (is_blocked, blocking_rule_ids).
        For calibration, this is a simplified check.
        """
        blocking_rules = []

        # Check each rule for STAMP prohibition
        for rule_eval in self.compiled_rules:
            if rule_eval.rule_type == "PROHIBITION":
                effect = rule_eval.effect
                if effect.get("action_class") == "STAMP":
                    # Check if condition is active
                    if rule_eval.active(obs, self.norm_state.norm_hash):
                        blocking_rules.append(rule_eval.rule_id)

        return len(blocking_rules) > 0, blocking_rules

    def _needs_stamp(self, obs: Observation) -> bool:
        """Check if agent needs to STAMP to make progress."""
        # Under regime=1, need STAMP before DEPOSIT
        return obs.regime == 1 and not obs.stamped and obs.inventory > 0

    def get_action(
        self,
        obs: Observation,
        episode: int,
        step: int
    ) -> Tuple[Action, Optional[LawRepairAction]]:
        """
        Get action for current observation.

        Returns:
            Tuple of (action, optional_repair_action)
            If repair is needed, returns repair action instead of movement.
        """
        regime = obs.regime

        # Check for contradiction under regime=1
        if regime == 1 and not self.repair_accepted:
            # Check if we're in a state where STAMP is needed but blocked
            if self._needs_stamp(obs):
                is_blocked, blocking_rules = self._check_stamp_blocked(obs)

                if is_blocked and not self.repair_issued:
                    # Need to issue LAW_REPAIR
                    trace_entry_id = TraceEntryID.generate(
                        run_seed=self.run_seed,
                        episode=episode,
                        step=step,
                        entry_type="CONTRADICTION"
                    )

                    # Record in trace log
                    from datetime import datetime
                    from .core.trace import TraceEntryType

                    trace_entry = TraceEntry(
                        trace_entry_id=trace_entry_id,
                        entry_type=TraceEntryType.CONTRADICTION,
                        run_seed=self.run_seed,
                        episode=episode,
                        step=step,
                        timestamp=datetime.now().isoformat(),
                        blocking_rule_ids=blocking_rules,
                        active_obligation_target={"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"},
                        progress_actions={"A6"}  # STAMP
                    )
                    self.trace_log.add(trace_entry)

                    # Create repair action
                    repair_action = create_canonical_repair_action(
                        trace_entry_id=trace_entry_id,
                        blocking_rule_ids=blocking_rules,
                        prior_repair_epoch=self.current_repair_epoch
                    )
                    self.repair_issued = True

                    # Return NOP action with repair (repair takes precedence)
                    return Action.MOVE_N, repair_action

        # Standard task oracle logic
        return self._task_policy(obs), None

    def apply_repair_direct(
        self,
        repair_action: LawRepairAction,
        env_nonce: bytes,
    ) -> bool:
        """
        Apply a repair action directly (simplified for calibration).

        This bypasses the full R1-R8 validation since the Oracle
        is a privileged solvability witness. For actual agents,
        the full LawRepairGate should be used.

        Returns True if repair was applied successfully.
        """
        # For calibration, we directly patch the norm state
        # The canonical repair adds an exception to R6 allowing STAMP under regime=1

        # Find R6 (PROHIBIT(STAMP)) and add exception
        patched_rules = []
        for rule in self.norm_state.rules:
            if rule.id == "R6":
                # Apply the patch: add exception for regime=1
                from .core.dsl import Condition, ConditionOp

                # Create new condition: original AND NOT (regime=1)
                # This effectively adds "UNLESS regime=1" to the prohibition
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

                # Create patched rule
                from dataclasses import replace
                patched_rule = replace(rule, condition=new_condition)
                patched_rules.append(patched_rule)
            else:
                patched_rules.append(rule)

        # Create new norm state with patched rules
        import hashlib

        # Compute new repair epoch
        h = hashlib.sha256()
        h.update(self.norm_state.law_fingerprint.encode())
        h.update(repair_action.repair_fingerprint.encode())
        h.update(env_nonce)
        new_epoch = h.hexdigest()

        # Update norm state - NormStateV420 only takes rules and repair_epoch
        self.norm_state = NormStateV420(
            rules=patched_rules,
            repair_epoch=new_epoch
        )
        self._recompile_rules()

        self.repair_accepted = True
        self.current_repair_epoch = new_epoch

        return True

    def _compute_progress_set(self, obs: Observation) -> List[str]:
        """
        Compute progress set for current obligation.

        For v4.2, this mirrors the environment's progress_set logic.
        """
        pos = obs.agent_pos
        inventory = obs.inventory
        regime = obs.regime
        stamped = obs.stamped

        # Target: satisfy ZONE_A (simplification - Oracle targets A first)
        target_zone = POSITIONS["ZONE_A"]

        # If already at zone with inventory and (stamped if regime=1), DEPOSIT
        if pos == target_zone and inventory > 0:
            if regime == 0 or (regime == 1 and stamped):
                return ["A5"]  # DEPOSIT

        # If at zone but need stamp (regime=1, not stamped)
        if pos == target_zone and inventory > 0 and regime == 1 and not stamped:
            # Need to go to ZONE_C and STAMP
            return ["A6"]  # STAMP is progress (but need to get there first)

        # If at ZONE_C and not stamped (regime=1), STAMP is progress
        if pos == POSITIONS["ZONE_C"] and regime == 1 and not stamped:
            return ["A6"]  # STAMP

        # If no inventory, need to COLLECT at SOURCE
        if inventory == 0:
            if pos == POSITIONS["SOURCE"]:
                return ["A4"]  # COLLECT
            else:
                # Movement toward SOURCE
                return self._movement_toward(pos, POSITIONS["SOURCE"])

        # Have inventory, need to reach target (with possible STAMP detour)
        if regime == 1 and not stamped:
            # Need STAMP first - go to ZONE_C
            return self._movement_toward(pos, POSITIONS["ZONE_C"])
        else:
            # Go to target zone
            return self._movement_toward(pos, target_zone)

    def _movement_toward(
        self,
        pos: Tuple[int, int],
        goal: Tuple[int, int]
    ) -> List[str]:
        """Get progress movement actions toward goal."""
        row, col = pos
        goal_row, goal_col = goal

        actions = []
        if col < goal_col:
            actions.append("A2")  # MOVE_E
        if col > goal_col:
            actions.append("A3")  # MOVE_W
        if row > goal_row:
            actions.append("A0")  # MOVE_N
        if row < goal_row:
            actions.append("A1")  # MOVE_S

        return actions if actions else ["A0"]  # Fallback

    def _task_policy(self, obs: Observation) -> Action:
        """
        Standard task completion policy.
        """
        pos = obs.agent_pos
        regime = obs.regime
        stamped = obs.stamped

        # Target selection (fixed priority order)
        if not obs.zone_a_satisfied:
            target = "ZONE_A"
        elif not obs.zone_b_satisfied:
            target = "ZONE_B"
        elif not obs.zone_c_satisfied:
            target = "ZONE_C"
        else:
            # All zones satisfied - arbitrary move
            return Action.MOVE_N

        # Under regime=1, if not stamped and have inventory, go STAMP first
        if regime == 1 and not stamped and obs.inventory > 0:
            if pos == POSITIONS["ZONE_C"]:
                return Action.STAMP
            else:
                return move_toward(pos, POSITIONS["ZONE_C"])

        # If no inventory, go to SOURCE and COLLECT
        if obs.inventory == 0:
            if pos != POSITIONS["SOURCE"]:
                return move_toward(pos, POSITIONS["SOURCE"])
            else:
                return Action.COLLECT

        # Have inventory (and stamped if regime=1): go to target and DEPOSIT
        target_pos = POSITIONS[target]
        if pos != target_pos:
            return move_toward(pos, target_pos)
        else:
            return Action.DEPOSIT


# ============================================================================
# §9.2 — Task Oracle Calibration Runner
# ============================================================================


@dataclass
class TaskOracleCalibrationConfigV420:
    """Configuration for Task Oracle v4.2 calibration run."""
    max_steps_per_episode: int = 40  # H=40
    max_episodes: int = 100  # E=100 for calibration
    seed: int = 42
    require_repair: bool = True  # Must issue repair under regime=1


class TaskOracleCalibrationV420:
    """
    Task Oracle v4.2 calibration runner.

    Proves:
    1. Environment is solvable under regime flip
    2. LAW_REPAIR is necessary and feasible
    3. Success rate ≥ τ (0.95)

    Key invariant: Oracle should require exactly ONE repair per run.
    - Episode 1: regime=0 → no contradiction → no repair
    - Episode 2: regime flips to 1 → contradiction → repair once
    - Episodes 3+: repaired law persists → no further contradictions
    """

    def __init__(self, config: TaskOracleCalibrationConfigV420):
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
        """
        Check if current state has contradiction (STAMP blocked but needed).
        Returns (is_contradiction, blocking_rule_ids).
        """
        if not (obs.regime == 1 and not obs.stamped and obs.inventory > 0):
            return False, []

        # Check if STAMP is blocked by any rule
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
        """Run Task Oracle v4.2 calibration with persistence tracking."""
        start_time = time.perf_counter()

        # ====================================================================
        # §9.1.1 — Required calibration counters (per spec Step 1)
        # ====================================================================
        total_steps = 0
        total_successes = 0
        contradictions_detected_total = 0
        repairs_submitted_total = 0
        repairs_accepted_total = 0
        repairs_rejected_total = 0
        contradictions_after_first_accepted_repair = 0
        episode_start_continuity_checks_total = 0
        episode_start_continuity_failures_total = 0

        first_repair_accepted = False
        first_repair_episode = None
        epoch_log: List[Dict[str, Any]] = []
        episode_summaries = []

        # ====================================================================
        # §9.1.2 — Persistent state across episodes (LAW MUST PERSIST)
        # ====================================================================
        # Create norm state and Oracle ONCE for entire run (not per episode!)
        norm_state = create_initial_norm_state_v420()
        trace_log = TraceLog(run_seed=self.config.seed)

        oracle = TaskOracleV420(
            norm_state=norm_state,
            trace_log=trace_log,
            run_seed=self.config.seed
        )

        initial_law_fingerprint = norm_state.law_fingerprint
        current_expected_epoch: Optional[str] = None

        for episode in range(self.config.max_episodes):
            # Reset environment for new episode (but NOT the Oracle/norm_state!)
            obs, info = self.env.reset()

            # Capture initial regime at episode start
            episode_start_regime = obs.regime

            # ================================================================
            # §9.1.3 — Episode-start continuity check
            # ================================================================
            if episode > 0:
                episode_start_continuity_checks_total += 1
                compiled_law_epoch = oracle.norm_state.repair_epoch

                epoch_log.append({
                    "episode": episode,
                    "expected_epoch": current_expected_epoch,
                    "found_epoch": compiled_law_epoch[:16] if compiled_law_epoch else None,
                    "match": compiled_law_epoch == current_expected_epoch
                })

                if first_repair_accepted:
                    # After first repair, epoch should match
                    if compiled_law_epoch != current_expected_epoch:
                        episode_start_continuity_failures_total += 1

            episode_steps = 0
            success = False
            episode_repair_submitted = False
            episode_repair_accepted = False
            episode_contradictions = 0

            while episode_steps < self.config.max_steps_per_episode:
                # Check success before taking action
                if self._is_success(obs):
                    success = True
                    break

                # Check for contradiction in current state
                is_contradiction, blocking_rules = self._check_contradiction(
                    obs, oracle.norm_state
                )

                if is_contradiction:
                    episode_contradictions += 1
                    contradictions_detected_total += 1

                    if first_repair_accepted:
                        contradictions_after_first_accepted_repair += 1

                # Get action from Oracle
                action, repair_action = oracle.get_action(
                    obs=obs,
                    episode=episode,
                    step=episode_steps
                )

                # Handle repair if issued
                if repair_action is not None:
                    episode_repair_submitted = True
                    repairs_submitted_total += 1

                    # Apply repair directly (simplified for calibration)
                    applied = oracle.apply_repair_direct(
                        repair_action=repair_action,
                        env_nonce=self.env.get_nonce(),
                    )

                    if applied:
                        episode_repair_accepted = True
                        repairs_accepted_total += 1

                        if not first_repair_accepted:
                            first_repair_accepted = True
                            first_repair_episode = episode

                        # Update expected epoch for continuity checks
                        current_expected_epoch = oracle.current_repair_epoch
                    else:
                        repairs_rejected_total += 1

                    # Continue with the action
                    action = oracle._task_policy(obs)

                # Execute action in environment
                obs, reward, terminated, truncated, info = self.env.step(action)
                episode_steps += 1
                total_steps += 1

                if terminated or truncated:
                    if self._is_success(obs):
                        success = True
                    break

            if success:
                total_successes += 1

            # Record actual regime from observation (env.episode_count = loop_episode + 1)
            # So regime flips at loop_episode=1 (env.episode_count=2)
            episode_summaries.append({
                "episode": episode,
                "steps": episode_steps,
                "success": success,
                "regime_at_start": episode_start_regime,  # Captured at episode start
                "regime_at_end": obs.regime,
                "contradictions_detected": episode_contradictions,
                "repair_submitted": episode_repair_submitted,
                "repair_accepted": episode_repair_accepted
            })

        elapsed = (time.perf_counter() - start_time) * 1000
        success_rate = total_successes / self.config.max_episodes

        # ====================================================================
        # §9.1.4 — Invariant checks (hard fail if violated)
        # ====================================================================
        invariant_violations = []

        # Invariant 1: Oracle should succeed with repairs_accepted ≤ 1
        if repairs_accepted_total > 1:
            invariant_violations.append({
                "invariant": "REPAIR_COUNT",
                "expected": "≤ 1",
                "actual": repairs_accepted_total,
                "classification": "INVALID_ORACLE / LAW_NOT_PERSISTED"
            })

        # Invariant 2: No contradictions after first accepted repair
        if contradictions_after_first_accepted_repair > 0:
            invariant_violations.append({
                "invariant": "NO_POST_REPAIR_CONTRADICTIONS",
                "expected": 0,
                "actual": contradictions_after_first_accepted_repair,
                "classification": "BUG / REPAIR_NOT_REMOVING_CONTRADICTION"
            })

        # Invariant 3: No continuity failures
        if episode_start_continuity_failures_total > 0:
            invariant_violations.append({
                "invariant": "CONTINUITY",
                "expected": 0,
                "actual": episode_start_continuity_failures_total,
                "classification": "INVALID_ENV / CONTINUITY_NOT_ENFORCED"
            })

        invariants_passed = len(invariant_violations) == 0

        # Calibration passes if:
        # 1. Success rate ≥ 0.95
        # 2. At least one repair was issued and accepted (repair is necessary)
        # 3. All invariants pass
        calibration_passed = (
            success_rate >= 0.95 and
            repairs_accepted_total >= 1 and
            invariants_passed
        )

        return {
            "calibration_type": "TASK_ORACLE_V420",
            "description": "Task Oracle v4.2 - scripted policy with LAW_REPAIR and persistence",
            "config": {
                "max_steps": self.config.max_steps_per_episode,
                "max_episodes": self.config.max_episodes,
                "seed": self.config.seed
            },
            "summary": {
                "total_steps": total_steps,
                "total_successes": total_successes,
                "success_rate": success_rate,
                "elapsed_ms": elapsed,
                "calibration_passed": calibration_passed,
                "invariants_passed": invariants_passed
            },
            "persistence_counters": {
                "contradictions_detected_total": contradictions_detected_total,
                "repairs_submitted_total": repairs_submitted_total,
                "repairs_accepted_total": repairs_accepted_total,
                "repairs_rejected_total": repairs_rejected_total,
                "contradictions_after_first_accepted_repair": contradictions_after_first_accepted_repair,
                "episode_start_continuity_checks_total": episode_start_continuity_checks_total,
                "episode_start_continuity_failures_total": episode_start_continuity_failures_total,
                "first_repair_episode": first_repair_episode
            },
            "epoch_log": epoch_log[:10],  # First 10 for inspection
            "invariant_violations": invariant_violations,
            "episodes": episode_summaries
        }


# ============================================================================
# §9.3 — ASB Null Baseline (Random Action, Expected to HALT)
# ============================================================================


@dataclass
class ASBNullConfigV420:
    """Configuration for ASB Null v4.2 baseline."""
    max_steps_per_episode: int = 40
    max_episodes: int = 100
    seed: int = 42


class ASBNullBaselineV420:
    """
    ASB Null v4.2: Uniform random action selection.

    No normative reasoning, no repair capability.
    Expected behavior under regime=1: HALT at first contradiction.

    This validates that contradiction detection works and
    demonstrates that repair is necessary for progress.
    """

    def __init__(self, config: ASBNullConfigV420):
        self.config = config
        self.env = TriDemandV420(seed=config.seed)
        import random
        self.rng = random.Random(config.seed)

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
    ) -> bool:
        """
        Check if current state has contradiction (STAMP blocked but needed).

        For ASB Null, we use a simplified check: if regime=1, not stamped,
        and have inventory, check if STAMP is prohibited.
        """
        if not (obs.regime == 1 and not obs.stamped and obs.inventory > 0):
            return False

        # Check if STAMP is blocked by any rule
        compiler = JCOMP420(norm_state)
        compiled_rules = compiler.compile_all_rules()

        for rule_eval in compiled_rules:
            if rule_eval.rule_type == "PROHIBITION":
                effect = rule_eval.effect
                if effect.get("action_class") == "STAMP":
                    # Check if condition is active
                    if rule_eval.active(obs, norm_state.norm_hash):
                        return True

        return False

    def run(self) -> Dict[str, Any]:
        """Run ASB Null v4.2 baseline."""
        start_time = time.perf_counter()

        total_steps = 0
        total_successes = 0
        total_halts = 0
        episode_summaries = []

        for episode in range(self.config.max_episodes):
            obs, info = self.env.reset()
            norm_state = create_initial_norm_state_v420()

            episode_steps = 0
            success = False
            halted = False

            while episode_steps < self.config.max_steps_per_episode:
                if self._is_success(obs):
                    success = True
                    break

                # Check for contradiction (ASB Null can't resolve)
                if self._check_contradiction(obs, norm_state):
                    halted = True
                    total_halts += 1
                    break

                # Random action selection
                available_actions = list(Action)
                action = self.rng.choice(available_actions)

                obs, reward, terminated, truncated, info = self.env.step(action)
                episode_steps += 1
                total_steps += 1

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
                "regime_at_end": obs.regime
            })

        elapsed = (time.perf_counter() - start_time) * 1000
        success_rate = total_successes / self.config.max_episodes
        halt_rate = total_halts / self.config.max_episodes

        # ASB Null is expected to:
        # 1. Have low success rate (can't complete task effectively)
        # 2. Have at least some halts (demonstrates contradiction detection)
        # Key: any halts prove repair is necessary for progress
        demonstrates_repair_necessity = total_halts > 0 or success_rate < 0.5

        return {
            "calibration_type": "ASB_NULL_V420",
            "description": "ASB Null v4.2 - random action, no repair capability",
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
                # ASB Null demonstrates repair necessity if it halts
                # or has low success rate
                "demonstrates_repair_necessity": demonstrates_repair_necessity
            },
            "episodes": episode_summaries
        }
