"""
AlternatingContest — Per preregistration §5.5.

Even epochs: target key_a (TAG="CONTEST"). Odd epochs: target key_b (TAG="CONTEST").
Used in: C (A0, A1 with K_POLICY/K_LOG).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class AlternatingContest(RSA):
    """Alternates contest between two keys."""

    TAG = "CONTEST"

    def __init__(self, agent_id: str, key_a: str, key_b: str,
                 key_a_authority_ids: list[str], key_b_authority_ids: list[str]):
        self.id = agent_id
        self._key_a = key_a
        self._key_b = key_b
        self._key_a_auth = key_a_authority_ids
        self._key_b_auth = key_b_authority_ids
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch % 2 == 0:
            key = self._key_a
            auth = self._key_a_auth
        else:
            key = self._key_b
            auth = self._key_b_auth
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[key],
            proposed_delta={
                key: f"{self.TAG}:{self.id}:{self._current_epoch}"
            },
            authorities_cited=auth,
        )
