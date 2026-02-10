"""
ContestKeyAlways — Per preregistration §5.1.

Always targets the specified key every epoch. TAG = "CONTEST".
Used in: A (all), C (A0, A1 on K_POLICY+K_LOG via AlternatingContest),
         D (A0 via OpportunistDeterministicCycle), F (A0, A1).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class ContestKeyAlways(RSA):
    """Always writes to the specified key every epoch."""

    TAG = "CONTEST"

    def __init__(self, agent_id: str, target_key: str, authority_ids: list[str]):
        self.id = agent_id
        self._target_key = target_key
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
            declared_scope=[self._target_key],
            proposed_delta={
                self._target_key: f"{self.TAG}:{self.id}:{self._current_epoch}"
            },
            authorities_cited=self._authority_ids,
        )
