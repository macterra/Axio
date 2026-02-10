"""
EpochGatedLogChatter — Per preregistration §5.9.

Silent until start_epoch, then writes log_key every epoch. TAG = "ZOMBIE".
Used in: F (A2 with K_LOG, start_epoch=15).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class EpochGatedLogChatter(RSA):
    """Silent until start_epoch, then writes to log_key every epoch."""

    TAG = "ZOMBIE"

    def __init__(self, agent_id: str, log_key: str, start_epoch: int,
                 authority_ids: list[str]):
        self.id = agent_id
        self._log_key = log_key
        self._start_epoch = start_epoch
        self._authority_ids = authority_ids
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch < self._start_epoch:
            return None  # Silent
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[self._log_key],
            proposed_delta={
                self._log_key: f"{self.TAG}:{self.id}:{self._current_epoch}"
            },
            authorities_cited=self._authority_ids,
        )
