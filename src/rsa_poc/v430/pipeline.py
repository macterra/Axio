"""
RSA-PoC v4.3 — MVRSA-4.3 Pipeline Runner

Implements the full episode runner for v4.3 with:
- Deliberate → Compile → Mask → Select → Execute loop
- Dual contradiction handling (A in regime 1, B in regime 2)
- Multi-repair discipline (R9: one repair per regime)
- Epoch-chained identity continuity (R6)
- Non-subsumption replay (R10)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple

from .core import (
    JCOMP430,
    JCOMP430_HASH,
    JustificationV430,
    NormStateV430,
    create_initial_norm_state_v430,
    LawRepairActionV430,
    LawRepairGateV430,
    RepairValidationResultV430,
    RepairFailureReasonV430,
    TraceEntry,
    TraceLog,
    RuleEvalV430,
    MaskResultV430,
    compute_feasible_430,
    create_contradiction_a_entry,
    create_contradiction_b_entry,
    compute_epoch_0,
    Condition,
    ConditionOp,
    PatchOp,
    PatchOperation,
    create_canonical_repair_b,
    EnvironmentInterfaceV430,
)
from .env.tri_demand import (
    TriDemandV430,
    Action,
    POSITIONS,
    Observation430,
    progress_set,
    REGIME_1_START,
    REGIME_2_PREREGISTERED_START,
)
from .harness import (
    HaltReasonV430,
    MaskedActionsV430,
    SelectionV430,
    TelemetryV430,
)


# ============================================================================
# §1 — Selector Protocols
# ============================================================================


class SelectorProtocol(Protocol):
    """Selector interface for action selection."""

    def select(
        self,
        feasible_action_ids: List[str],
        observation: Any,
        episode: int,
        step: int,
    ) -> SelectionV430:
        """Select action from feasible set."""
        ...


class ArgmaxSelector:
    """Select first feasible action (deterministic)."""

    def select(
        self,
        feasible_action_ids: List[str],
        observation: Any,
        episode: int,
        step: int,
    ) -> SelectionV430:
        if not feasible_action_ids:
            return SelectionV430.halt(HaltReasonV430.NO_FEASIBLE_ACTIONS)
        return SelectionV430(
            action_id=sorted(feasible_action_ids)[0],
            selection_time_ms=0.0,
        )


class TaskAwareSelector:
    """Select action that makes progress toward active task."""

    def select(
        self,
        feasible_action_ids: List[str],
        observation: Any,
        episode: int,
        step: int,
    ) -> SelectionV430:
        if not feasible_action_ids:
            return SelectionV430.halt(HaltReasonV430.NO_FEASIBLE_ACTIONS)

        obs = observation if isinstance(observation, Observation430) else Observation430(**observation)

        # Priority: DEPOSIT > STAMP > COLLECT > MOVE toward goal
        if "A5" in feasible_action_ids:  # DEPOSIT
            return SelectionV430(action_id="A5", selection_time_ms=0.1)
        if "A6" in feasible_action_ids and obs.regime == 1:  # STAMP in regime 1
            return SelectionV430(action_id="A6", selection_time_ms=0.1)
        if "A4" in feasible_action_ids and obs.inventory == 0:  # COLLECT
            return SelectionV430(action_id="A4", selection_time_ms=0.1)

        # Move toward goal position
        return SelectionV430(
            action_id=sorted(feasible_action_ids)[0],
            selection_time_ms=0.1,
        )


# ============================================================================
# §2 — Deliberator Protocol
# ============================================================================


class DeliberatorProtocol(Protocol):
    """Deliberator interface."""

    epoch_chain: List[str]
    repair_a_issued: bool
    repair_b_issued: bool

    def set_epoch_chain(self, epoch_chain: List[str]) -> None: ...
    def record_repair_accepted(self, contradiction_type: str) -> None: ...

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV430,
        episode: int,
        step: int,
        regime: int,
    ) -> Any:
        """Generate justifications for observation."""
        ...


# ============================================================================
# §3 — Harness Configuration
# ============================================================================


@dataclass
class HarnessConfigV430:
    """Configuration for v4.3 harness."""
    max_steps_per_episode: int = 40
    max_episodes: int = 20
    seed: int = 42
    selector_type: str = "argmax"  # "argmax", "task_aware"
    record_telemetry: bool = True
    verbose: bool = False
    validity_gates_only: bool = True


# ============================================================================
# §3.5 — Environment Interface Wrapper
# ============================================================================


class EnvInterfaceWrapper(EnvironmentInterfaceV430):
    """Wrapper that adapts TriDemandV430 to EnvironmentInterfaceV430."""

    def __init__(self, env: TriDemandV430):
        self.env = env

    def target_satisfied(self, obs: Any, obligation_target: Dict[str, Any]) -> bool:
        return self.env.target_satisfied(obs, obligation_target)

    def rank(self, obs: Any, obligation_target: Dict[str, Any]) -> int:
        return self.env.rank(obs, obligation_target)

    def progress_set(self, obs: Any, obligation_target: Dict[str, Any]) -> Set[str]:
        return self.env.progress_set(obs, obligation_target)


# ============================================================================
# §4 — Pipeline Harness
# ============================================================================


class MVRSA430Harness:
    """
    MVRSA-4.3 Pipeline Harness.

    Executes Deliberate → Compile → Mask → Select → Execute with:
    - Dual contradiction handling (A and B)
    - Multi-repair discipline (R9)
    - Epoch-chained identity continuity (R6)
    """

    def __init__(
        self,
        env: TriDemandV430,
        deliberator: DeliberatorProtocol,
        config: HarnessConfigV430,
    ):
        self.env = env
        self.env_interface = EnvInterfaceWrapper(env)  # Interface wrapper
        self.deliberator = deliberator
        self.config = config

        # Selector
        if config.selector_type == "task_aware":
            self.selector = TaskAwareSelector()
        else:
            self.selector = ArgmaxSelector()

        # PERSISTENT state across episodes
        self.norm_state = create_initial_norm_state_v430()
        self.trace_log = TraceLog(run_seed=config.seed)

        # Epoch chain for R6 anti-amnesia
        epoch_0 = compute_epoch_0(
            self.norm_state.law_fingerprint,
            f"harness_nonce_{config.seed}".encode()
        )
        self.epoch_chain: List[str] = [epoch_0]
        self.deliberator.set_epoch_chain(self.epoch_chain)

        # Repair tracking
        self.repair_a_accepted: bool = False
        self.repair_b_accepted: bool = False
        self.current_regime: int = 0

        # Law-Repair Gate
        self.gate = LawRepairGateV430(
            trace_log={},
            expected_compiler_hash=JCOMP430_HASH,
            env_progress_set_fn=progress_set,
            max_retries_per_contradiction=2,
        )
        self.gate.initialize_epoch_chain(epoch_0)

        # Compiler
        self.compiler = JCOMP430(self.norm_state)
        self._compiled_rules: List[RuleEvalV430] = []

        # Telemetry
        self.telemetry = TelemetryV430()

        # Counters
        self.total_steps = 0
        self.total_halts = 0
        self.total_contradictions = 0
        self.total_repairs_attempted = 0
        self.total_repairs_accepted = 0
        self.halts_by_reason: Dict[str, int] = {}
        self.continuity_checks_total = 0
        self.continuity_failures_total = 0
        self.repair_bindings: List[Dict[str, Any]] = []

    def _recompile_rules(self) -> None:
        """Recompile rules after norm_state change."""
        self.compiler = JCOMP430(self.norm_state)
        self._compiled_rules = self.compiler.compile_all_rules()

    def _record_halt(self, reason: HaltReasonV430) -> None:
        """Record a HALT with reason tracking."""
        self.total_halts += 1
        reason_key = reason.value
        self.halts_by_reason[reason_key] = self.halts_by_reason.get(reason_key, 0) + 1
        self.telemetry.record_halt(reason)

    def _determine_regime(self, obs: Observation430) -> int:
        """Determine current regime based on observation and repair state."""
        # Regime transitions are event-gated:
        # - regime 0 → 1: episode >= REGIME_1_START
        # - regime 1 → 2: Repair A accepted
        if self.repair_a_accepted:
            return 2
        elif obs.episode >= REGIME_1_START:
            return 1
        return 0

    def _check_contradiction(
        self,
        obs: Observation430,
        regime: int,
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check for contradictions.

        Returns: (is_contradiction, contradiction_type, blocking_rules)
        """
        # Compile rules and compute feasible actions
        if not self._compiled_rules:
            self._recompile_rules()

        mask_result = compute_feasible_430(
            self._compiled_rules,
            self.norm_state,
            obs,
            self.env_interface,
            self.norm_state.norm_hash,
            regime,
        )

        if not mask_result.is_contradiction:
            return False, None, []

        contradiction_type = mask_result.contradiction_type
        blocking_rules = mask_result.blocking_rule_ids or []

        return True, contradiction_type, blocking_rules

    def _attempt_repair(
        self,
        obs: Observation430,
        contradiction_type: str,
        blocking_rules: List[str],
        episode: int,
        step: int,
    ) -> bool:
        """Attempt to issue and apply LAW_REPAIR."""
        self.total_repairs_attempted += 1

        # Generate trace entry
        if contradiction_type == 'A':
            trace_entry = create_contradiction_a_entry(
                run_seed=self.config.seed,
                episode=episode,
                step=step,
                blocking_rule_ids=blocking_rules,
                active_obligation_target={"kind": "DELIVER", "target_id": "ZONE_A"},
                progress_actions={"A6"},  # STAMP
                compiled_permitted_actions=set(),
            )
        else:  # B
            trace_entry = create_contradiction_b_entry(
                run_seed=self.config.seed,
                episode=episode,
                step=step,
                blocking_rule_ids=blocking_rules,
                active_obligation_target={"kind": "DELIVER", "target_id": obs.position},
                progress_actions={"A5"},  # DEPOSIT
                compiled_permitted_actions=set(),
            )

        self.trace_log.add(trace_entry)
        self.gate.trace_log[trace_entry.trace_entry_id] = trace_entry

        # Generate repair action
        if contradiction_type == 'A':
            repair_action = self._create_repair_a(trace_entry.trace_entry_id)
        else:
            repair_action = self._create_repair_b(trace_entry.trace_entry_id)

        # Validate repair through gate
        self.gate.set_regime(self._determine_regime(obs))

        # For validity gates only, apply directly
        if self.config.validity_gates_only:
            success = self._apply_repair_direct(repair_action, contradiction_type)
        else:
            success = self._apply_repair_with_gate(repair_action, obs, contradiction_type)

        if success:
            self.total_repairs_accepted += 1
            if contradiction_type == 'A':
                self.repair_a_accepted = True
                self.telemetry.repair_a_accepted = True
                self.telemetry.repair_a_episode = episode
                self.deliberator.record_repair_accepted('A')
            else:
                self.repair_b_accepted = True
                self.telemetry.repair_b_accepted = True
                self.telemetry.repair_b_episode = episode
                self.deliberator.record_repair_accepted('B')

            self.repair_bindings.append({
                "trace_entry_id": trace_entry.trace_entry_id,
                "contradiction_type": contradiction_type,
                "blocking_rule_ids": blocking_rules,
                "epoch": self.epoch_chain[-1],
                "episode": episode,
                "step": step,
                "accepted": True,
            })
            return True

        self.repair_bindings.append({
            "trace_entry_id": trace_entry.trace_entry_id,
            "contradiction_type": contradiction_type,
            "blocking_rule_ids": blocking_rules,
            "epoch": None,
            "episode": episode,
            "step": step,
            "accepted": False,
        })
        return False

    def _create_repair_a(self, trace_entry_id: str) -> LawRepairActionV430:
        """Create canonical Repair A: POSITION_EQ exception to R6."""
        exception_condition = Condition(
            op=ConditionOp.POSITION_EQ,
            args=["STAMP_LOCATION"],
        )
        patch_r6 = PatchOperation(
            op=PatchOp.ADD_EXCEPTION,
            target_rule_id="R6",
            exception_condition=exception_condition,
        )
        prior_epoch = self.epoch_chain[-1] if self.epoch_chain else None
        return LawRepairActionV430.create(
            trace_entry_id=trace_entry_id,
            rule_ids=["R6"],
            patch_ops=[patch_r6],
            prior_repair_epoch=prior_epoch,
            contradiction_type='A',
            regime_at_submission=1,
        )

    def _create_repair_b(self, trace_entry_id: str) -> LawRepairActionV430:
        """Create canonical Repair B using factory function."""
        prior_epoch = self.epoch_chain[-1]
        return create_canonical_repair_b(
            trace_entry_id=trace_entry_id,
            prior_epoch=prior_epoch,
        )

    def _apply_repair_direct(
        self,
        repair_action: LawRepairActionV430,
        contradiction_type: str,
    ) -> bool:
        """Apply repair directly (simplified for validity gates)."""
        import hashlib

        # Apply patches to norm state
        patched_rules = list(self.norm_state.rules)

        for patch_op in repair_action.patch_ops:
            if patch_op.op == PatchOp.ADD_EXCEPTION:
                for i, rule in enumerate(patched_rules):
                    if rule.id == patch_op.target_rule_id:
                        from dataclasses import replace
                        patched_rules[i] = replace(
                            rule,
                            exception_condition=patch_op.exception_condition
                        )
                        break

        # Compute new epoch
        # nonce_index: 1 for Repair A (epoch_1), 2 for Repair B (epoch_2)
        nonce_index = len(self.epoch_chain)  # Will be 1 or 2
        h = hashlib.sha256()
        h.update(self.norm_state.law_fingerprint.encode())
        h.update(repair_action.repair_fingerprint.encode())
        h.update(self.env.get_nonce(nonce_index))
        new_epoch = h.hexdigest()

        # Update epoch chain
        new_epoch_chain = self.epoch_chain + [new_epoch]
        new_repair_count = self.norm_state.repair_count + 1

        # Update norm state
        self.norm_state = NormStateV430(
            rules=patched_rules,
            epoch_chain=new_epoch_chain,
            repair_count=new_repair_count,
        )
        self.epoch_chain = new_epoch_chain
        self.telemetry.epoch_chain = self.epoch_chain.copy()
        self.deliberator.set_epoch_chain(self.epoch_chain)
        self._recompile_rules()

        return True

    def _apply_repair_with_gate(
        self,
        repair_action: LawRepairActionV430,
        obs: Observation430,
        contradiction_type: str,
    ) -> bool:
        """Apply repair with full gate validation."""
        # Get compiled permitted actions
        regime = self._determine_regime(obs)
        mask_result = compute_feasible_430(
            self._compiled_rules,
            self.norm_state,
            obs,
            self.env_interface,
            self.norm_state.norm_hash,
            regime,
        )
        compiled_permitted = set(mask_result.feasible)

        obligation_target = {"kind": "DELIVER", "target_id": "ZONE_A"}

        # nonce_index: 1 for Repair A (epoch_1), 2 for Repair B (epoch_2)
        nonce_index = len(self.epoch_chain)
        result = self.gate.validate_repair(
            repair_action=repair_action,
            norm_state=self.norm_state,
            obs=obs,
            active_obligation_target=obligation_target,
            compiled_permitted_actions=compiled_permitted,
            compile_fn=lambda ns: JCOMP430(ns).compile_all_rules(),
            compiler_hash=JCOMP430_HASH,
            env_nonce=self.env.get_nonce(nonce_index).decode('utf-8'),
        )

        if result.valid:
            self.gate.accept_repair(
                repair_action,
                result.new_repair_epoch,
                result.patched_norm_state,
            )
            self.norm_state = result.patched_norm_state
            self.epoch_chain.append(result.new_repair_epoch)
            self.telemetry.epoch_chain = self.epoch_chain.copy()
            self.deliberator.set_epoch_chain(self.epoch_chain)
            self._recompile_rules()
            return True

        return False

    def run_step(
        self,
        obs: Observation430,
        episode: int,
        step: int,
    ) -> Tuple[Observation430, bool, bool]:
        """
        Execute a single pipeline step.

        Returns: (new_obs, done, halted)
        """
        self.total_steps += 1
        regime = self._determine_regime(obs)
        self.current_regime = regime
        self.gate.set_regime(regime)

        # Check for contradiction
        is_contradiction, contradiction_type, blocking_rules = self._check_contradiction(obs, regime)

        if is_contradiction:
            self.total_contradictions += 1
            if contradiction_type == 'A':
                self.telemetry.contradiction_a_total += 1
            elif contradiction_type == 'B':
                self.telemetry.contradiction_b_total += 1

            # Check if we can repair
            can_repair_a = contradiction_type == 'A' and not self.repair_a_accepted
            can_repair_b = contradiction_type == 'B' and self.repair_a_accepted and not self.repair_b_accepted

            if can_repair_a or can_repair_b:
                repair_accepted = self._attempt_repair(
                    obs, contradiction_type, blocking_rules, episode, step
                )
                if not repair_accepted:
                    self._record_halt(HaltReasonV430.REPAIR_REJECTED)
                    return obs, False, True
            else:
                # Cannot repair (patch stacking or already repaired)
                if contradiction_type == 'A' and self.repair_a_accepted:
                    self._record_halt(HaltReasonV430.NORMATIVE_DEADLOCK_AFTER_A)
                else:
                    self._record_halt(HaltReasonV430.PATCH_STACKING)
                return obs, False, True

        # Deliberate
        deliberation = self.deliberator.deliberate(
            obs, self.norm_state, episode, step, regime
        )

        if not deliberation.success:
            self._record_halt(HaltReasonV430.DELIBERATION_FAILURE)
            return obs, False, True

        # Mask: compute feasible actions
        if not self._compiled_rules:
            self._recompile_rules()

        mask_result = compute_feasible_430(
            self._compiled_rules,
            self.norm_state,
            obs,
            self.env_interface,
            self.norm_state.norm_hash,
            regime,
        )
        feasible = mask_result.feasible

        # Filter to justified actions
        justified_actions = {j.action_id for j in deliberation.justifications}
        feasible_justified = [a for a in feasible if a in justified_actions]

        # If no justified feasible, use all feasible
        if not feasible_justified and feasible:
            feasible_justified = feasible

        # Select
        if not feasible_justified:
            self._record_halt(HaltReasonV430.NO_FEASIBLE_ACTIONS)
            return obs, False, True

        selection = self.selector.select(
            feasible_action_ids=feasible_justified,
            observation=obs,
            episode=episode,
            step=step,
        )

        if selection.is_halt:
            self._record_halt(selection.halt_reason)
            return obs, False, True

        # Execute
        action = Action(int(selection.action_id[1:]))
        new_obs, reward, terminated, truncated, info = self.env.step(action)
        done = terminated or truncated

        if self.config.verbose:
            print(f"    Step {step}: {selection.action_id} @ {obs.position} → {new_obs.position}")

        return new_obs, done, False

    def run_episode(self, episode: int) -> Dict[str, Any]:
        """Run a single episode."""
        obs, info = self.env.reset(episode=episode)
        self._recompile_rules()

        self.telemetry.episodes_total += 1

        steps = 0
        success = False
        halted = False

        for step in range(self.config.max_steps_per_episode):
            obs, done, halted = self.run_step(obs, episode, step)
            steps += 1

            if halted:
                self.telemetry.episodes_halted += 1
                break

            if done:
                success = True
                self.telemetry.episodes_success += 1
                break

        return {
            "episode": episode,
            "steps": steps,
            "success": success,
            "halted": halted,
            "regime_at_end": self.current_regime,
            "repair_a_accepted": self.repair_a_accepted,
            "repair_b_accepted": self.repair_b_accepted,
        }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SelectorProtocol",
    "ArgmaxSelector",
    "TaskAwareSelector",
    "DeliberatorProtocol",
    "HarnessConfigV430",
    "MVRSA430Harness",
]
