"""
OwnKeyOnly — Per preregistration §5.2.

Always writes to own assigned key. TAG = "OWN".
Used in: B (Phase 1), C (A2, A3), D (A1, A2, A3).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class OwnKeyOnly(RSA):
    """Always writes to own assigned key every epoch."""

    TAG = "OWN"

    def __init__(self, agent_id: str, own_key: str, authority_ids: list[str]):
        self.id = agent_id
        self._own_key = own_key
        self._authority_ids = authority_ids
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[self._own_key],
            proposed_delta={
                self._own_key: f"{self.TAG}:{self.id}:{self._current_epoch}"
            },
            authorities_cited=self._authority_ids,
        )
