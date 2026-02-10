"""
AlternateOwnProbe — Per preregistration §5.3.

Even epochs: write own_key (TAG="OWN"). Odd epochs: attempt probe_key (TAG="PROBE").
Probe will be refused if agent lacks ALLOW for probe_key.
Used in: B (Phase 2, inside PartitionedPeerStrategy).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class AlternateOwnProbe(RSA):
    """Alternates between own key (even) and probe key (odd)."""

    def __init__(self, agent_id: str, own_key: str, probe_key: str,
                 own_authority_ids: list[str], probe_authority_ids: list[str]):
        self.id = agent_id
        self._own_key = own_key
        self._probe_key = probe_key
        self._own_authority_ids = own_authority_ids
        self._probe_authority_ids = probe_authority_ids
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch % 2 == 0:
            key = self._own_key
            tag = "OWN"
            auth = self._own_authority_ids
        else:
            key = self._probe_key
            tag = "PROBE"
            auth = self._probe_authority_ids
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[key],
            proposed_delta={
                key: f"{tag}:{self.id}:{self._current_epoch}"
            },
            authorities_cited=auth,
        )
