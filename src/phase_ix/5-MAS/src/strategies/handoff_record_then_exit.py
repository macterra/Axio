"""
HandoffRecordThenExit — Per preregistration §5.7.

Writes own_key until exit_epoch-1 (TAG="OWN"), writes HANDOFF at exit_epoch,
then exits permanently.
Used in: E (A2 exits at 12, A3 exits at 18).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class HandoffRecordThenExit(RSA):
    """Writes own key, records handoff, then exits at specified epoch."""

    def __init__(self, agent_id: str, own_key: str, exit_epoch: int,
                 authority_ids: list[str]):
        self.id = agent_id
        self._own_key = own_key
        self._exit_epoch = exit_epoch
        self._authority_ids = authority_ids
        self._current_epoch: int = 0
        self._exited: bool = False

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        # Exit AFTER proposing the handoff action at exit_epoch
        return self._current_epoch >= self._exit_epoch and self._exited

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch < self._exit_epoch:
            tag = "OWN"
        elif self._current_epoch == self._exit_epoch:
            tag = "HANDOFF"
            self._exited = True
        else:
            return None  # Should not reach here (already exited)
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
