"""
CUD Epoch Controller — Per preregistration §2.8

Orchestrates the epoch loop: observe → exit check → message → action → adjudicate → execute.
"""

from typing import Any, Optional
from .agent_model import RSA, Observation, ActionRequest, Message
from .world_state import WorldState
from .authority_store import AuthorityStore
from .admissibility import evaluate_admissibility, EXECUTED, NO_ACTION
from .deadlock_classifier import DeadlockClassifier, STATE_DEADLOCK, STATE_LIVELOCK, COLLAPSE, ORPHANING
from .common.logging import CUDEpochLog


class EpochController:
    """
    Epoch loop orchestration per §2.8.

    Manages agent lifecycle, message delivery, action adjudication,
    and terminal classification.
    """

    def __init__(
        self,
        agents: dict[str, RSA],
        world_state: WorldState,
        authority_store: AuthorityStore,
        max_epochs: int,
        communication_enabled: bool = False,
        adversarial_tie_break: bool = False,
    ):
        self._agents = dict(agents)  # mutable copy
        self._active_agents: list[str] = list(agents.keys())
        self._world_state = world_state
        self._authority_store = authority_store
        self._max_epochs = max_epochs
        self._communication_enabled = communication_enabled
        self._adversarial_tie_break = adversarial_tie_break
        self._classifier = DeadlockClassifier()

        # Per-agent state tracking
        self._last_outcomes: dict[str, Optional[str]] = {
            aid: None for aid in agents
        }
        self._last_action_ids: dict[str, Optional[str]] = {
            aid: None for aid in agents
        }
        self._last_declared_scopes: dict[str, Optional[list[str]]] = {
            aid: None for aid in agents
        }
        self._pending_messages: list[Message] = []
        self._epoch_logs: list[CUDEpochLog] = []
        self._terminal_classification: Optional[str] = None
        self._kernel_classification: Optional[str] = None
        self._exited_agents: set[str] = set()
        self._deadlock_epoch_count: int = 0

    @property
    def epoch_logs(self) -> list[CUDEpochLog]:
        return self._epoch_logs

    @property
    def terminal_classification(self) -> Optional[str]:
        return self._terminal_classification

    @property
    def kernel_classification(self) -> Optional[str]:
        return self._kernel_classification

    @property
    def final_state(self) -> dict[str, Any]:
        return self._world_state.get_state()

    def run(self) -> dict[str, Any]:
        """
        Execute the full epoch loop.

        Returns summary dict with terminal_classification, kernel_classification,
        final_state, epochs.
        """
        for epoch in range(self._max_epochs):
            epoch_log = self._run_epoch(epoch)
            self._epoch_logs.append(epoch_log)

            # Check terminal conditions after each epoch
            if self._terminal_classification is not None:
                break

            # Check collapse
            if DeadlockClassifier.is_collapse(self._active_agents):
                self._terminal_classification = COLLAPSE
                break

        # Check for orphaning at end if no other terminal classification
        if self._terminal_classification is None:
            orphaned = DeadlockClassifier.detect_orphaning(
                self._active_agents,
                self._authority_store,
                list(self._world_state.get_state().keys()),
            )
            if orphaned:
                self._terminal_classification = ORPHANING

        # Adversarial detection (Condition E)
        if self._adversarial_tie_break:
            self._kernel_classification = "IX2_FAIL / IMPLICIT_ARBITRATION"

        return {
            "terminal_classification": self._terminal_classification,
            "kernel_classification": self._kernel_classification,
            "final_state": self._world_state.get_state(),
            "epochs": [log.to_dict() for log in self._epoch_logs],
        }

    def _run_epoch(self, epoch: int) -> CUDEpochLog:
        """Execute a single epoch per §2.8."""
        log = CUDEpochLog(epoch=epoch)
        state_before = self._world_state.snapshot()

        # Step 1+2: Build observations and deliver
        observations: dict[str, dict[str, Any]] = {}
        for agent_id in list(self._active_agents):
            obs = Observation(
                epoch=epoch,
                world_state=self._world_state.get_state(),
                own_last_outcome=self._last_outcomes.get(agent_id),
                own_last_action_id=self._last_action_ids.get(agent_id),
                own_last_declared_scope=self._last_declared_scopes.get(agent_id),
                messages=list(self._pending_messages),
            )
            self._agents[agent_id].observe(obs)
            observations[agent_id] = {
                "epoch": obs.epoch,
                "world_state": obs.world_state,
                "own_last_outcome": obs.own_last_outcome,
            }
        log.observations = observations

        # Step 3: Exit check
        exiting = []
        for agent_id in list(self._active_agents):
            if self._agents[agent_id].wants_to_exit():
                exiting.append(agent_id)
        for agent_id in exiting:
            self._active_agents.remove(agent_id)
            self._exited_agents.add(agent_id)
        log.exits = exiting

        # Check collapse after exits
        if not self._active_agents:
            self._terminal_classification = COLLAPSE
            log.state_after = self._world_state.get_state()

            # Check orphaning too
            orphaned = DeadlockClassifier.detect_orphaning(
                self._active_agents,
                self._authority_store,
                list(self._world_state.get_state().keys()),
            )
            if orphaned and self._exited_agents:
                # Collapse takes precedence unless specific orphaning condition
                pass

            return log

        # Step 4: Message composition
        new_messages: list[Message] = []
        if self._communication_enabled:
            for agent_id in self._active_agents:
                content = self._agents[agent_id].compose_message()
                if content is not None:
                    msg = Message(sender=agent_id, epoch=epoch, content=content)
                    new_messages.append(msg)
        log.messages = [
            {"sender": m.sender, "epoch": m.epoch, "content": m.content}
            for m in new_messages
        ]

        # Step 5: Action proposals
        actions: dict[str, Optional[ActionRequest]] = {}
        for agent_id in self._active_agents:
            action = self._agents[agent_id].propose_action()
            actions[agent_id] = action

        log.actions = [
            action.to_dict() if action is not None else None
            for action in actions.values()
        ]

        # Step 6: Adjudication (two-pass)
        outcomes, pass1_results, pass2_results = evaluate_admissibility(
            actions, self._authority_store,
            adversarial_tie_break=self._adversarial_tie_break,
        )
        log.pass1_results = pass1_results
        log.pass2_results = pass2_results
        log.outcomes = outcomes

        # Step 7+8: Execute admissible actions and update state
        for agent_id, outcome in outcomes.items():
            action = actions.get(agent_id)
            if outcome == EXECUTED and action is not None:
                self._world_state.apply_delta(action.proposed_delta)

        # Update per-agent tracking
        for agent_id in self._active_agents:
            action = actions.get(agent_id)
            self._last_outcomes[agent_id] = outcomes.get(agent_id)
            if action is not None:
                self._last_action_ids[agent_id] = action.action_id
                self._last_declared_scopes[agent_id] = action.declared_scope
            else:
                self._last_action_ids[agent_id] = None
                self._last_declared_scopes[agent_id] = None

        # Deliver messages for next epoch
        self._pending_messages = new_messages

        log.state_after = self._world_state.get_state()

        # Terminal classification checks
        state_after = self._world_state.get_state()
        state_changed = state_before != state_after

        any_pass1_admissible = any(
            r == "PASS" for r in pass1_results.values()
        )
        any_action_submitted = any(
            actions[aid] is not None for aid in self._active_agents
            if aid in actions
        )
        # Check if any Pass-1-admissible action was refused at Pass-2
        any_pass2_interference = any(
            r == "FAIL" for r in pass2_results.values()
        )

        # Orphaning detection — check BEFORE deadlock so it takes precedence
        if self._exited_agents and self._terminal_classification is None:
            orphaned = DeadlockClassifier.detect_orphaning(
                self._active_agents,
                self._authority_store,
                list(state_after.keys()),
            )
            if orphaned:
                self._terminal_classification = ORPHANING

        # Deadlock detection (only if no terminal classification yet)
        if self._terminal_classification is None:
            if not any_pass1_admissible and any_action_submitted:
                self._deadlock_epoch_count += 1
                if DeadlockClassifier.is_deadlock(outcomes, pass1_results):
                    self._terminal_classification = STATE_DEADLOCK
            elif not any_action_submitted:
                if not any_pass1_admissible:
                    self._deadlock_epoch_count += 1
                    self._terminal_classification = STATE_DEADLOCK
            else:
                self._deadlock_epoch_count = 0

        # Livelock detection (only if no terminal classification yet)
        self._classifier.record_epoch(
            state_changed, any_pass1_admissible,
            any_action_submitted, any_pass2_interference,
        )
        if self._terminal_classification is None and self._classifier.is_livelock():
            self._terminal_classification = STATE_LIVELOCK

        return log
