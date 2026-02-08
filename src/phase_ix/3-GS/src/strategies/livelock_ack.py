"""LivelockAcknowledger_AfterLatch — Per preregistration §7.1.

After livelock latches, write LLOCK_ACK to K_LOG.
Used in: E (A2, A3).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class LivelockAcknowledger_AfterLatch(RSA):
    """Writes LLOCK_ACK to K_LOG after livelock is detected.

    Detection heuristic: world state unchanged for N consecutive epochs.
    Once latched, detection is permanent.
    After latch (+ optional delay), write one LLOCK_ACK.
    Only considers the action confirmed after observing EXECUTED.
    """

    def __init__(self, agent_id: str, log_allow_id: str,
                 livelock_n: int = 5, ack_delay: int = 0):
        self.id = agent_id
        self.log_allow_id = log_allow_id
        self._livelock_n = livelock_n
        self._ack_delay = ack_delay
        self._current_epoch: int = 0
        self._last_state: Optional[dict] = None
        self._stagnant_epochs: int = 0
        self._livelock_detected: bool = False
        self._detection_epoch: Optional[int] = None
        self._ack_written: bool = False
        self._ack_pending: bool = False

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

        # Check if our LLOCK_ACK was accepted
        if self._ack_pending:
            if observation.own_last_outcome == "EXECUTED":
                self._ack_written = True
            self._ack_pending = False

        # Track stagnation via world state comparison
        current_state = dict(observation.world_state)
        if self._last_state is not None:
            if current_state == self._last_state:
                self._stagnant_epochs += 1
            elif not self._livelock_detected:
                # Reset only before latch (after latch, keep latched)
                self._stagnant_epochs = 0
        self._last_state = current_state

        # Latch livelock
        if not self._livelock_detected and self._stagnant_epochs >= self._livelock_n:
            self._livelock_detected = True
            self._detection_epoch = self._current_epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if not self._livelock_detected or self._ack_written or self._ack_pending:
            return None
        # Respect ack_delay
        if (self._detection_epoch is not None
                and self._current_epoch < self._detection_epoch + self._ack_delay):
            return None
        self._ack_pending = True
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_LOG"],
            proposed_delta={"K_LOG": f"LLOCK_ACK:{self.id}:{self._current_epoch}"},
            authorities_cited=[self.log_allow_id],
        )
