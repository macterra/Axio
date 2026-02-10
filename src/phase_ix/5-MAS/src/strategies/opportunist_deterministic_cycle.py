"""
OpportunistDeterministicCycle — Per preregistration §5.6.

Cycles through K_INST keys in fixed order. TAG = "CYCLE".
Used in: D (A0 with all K_INST keys).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class OpportunistDeterministicCycle(RSA):
    """Cycles through institutional keys in fixed deterministic order."""

    TAG = "CYCLE"

    def __init__(self, agent_id: str, keys: list[str],
                 authority_ids_by_key: dict[str, list[str]]):
        self.id = agent_id
        self._keys = list(keys)  # Fixed ordered list
        self._auth_by_key = authority_ids_by_key
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        key = self._keys[self._current_epoch % len(self._keys)]
        auth = self._auth_by_key.get(key, [])
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
