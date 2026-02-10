"""
HandoffRecordThenExit — Per preregistration §5.1 pseudocode.

Writes own_key with OWN tag until exit_epoch-2, writes HANDOFF at exit_epoch-1,
then exits at exit_epoch (wants_to_exit returns True before propose_action).
Used in: E (A2 exits at 12, A3 exits at 18).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class HandoffRecordThenExit(RSA):
    """Writes own key, records handoff at exit_epoch-1, exits at exit_epoch."""

    def __init__(self, agent_id: str, own_key: str, exit_epoch: int,
                 authority_ids: list[str]):
        self.id = agent_id
        self._own_key = own_key
        self._exit_epoch = exit_epoch
        self._authority_ids = authority_ids
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        # Per prereg §5.1: exit at exit_epoch (before propose_action)
        return self._current_epoch >= self._exit_epoch

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        # Per prereg §5.1: HANDOFF at exit_epoch-1, OWN otherwise
        if self._current_epoch == self._exit_epoch - 1:
            tag = "HANDOFF"
        else:
            tag = "OWN"
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[self._own_key],
            proposed_delta={
                self._own_key: f"{tag}:{self.id}:{self._current_epoch}"
            },
            authorities_cited=self._authority_ids,
        )
