"""
PartitionedPeerStrategy — Per preregistration §5.4.

Single composite class (A-L4). Phase behavior:
  - Epochs 0 to phase_switch_epoch-1: OwnKeyOnly(own_key)
  - Epochs >= phase_switch_epoch: AlternateOwnProbe(own_key, probe_key)
    Even epoch → own_key (TAG="OWN"), Odd epoch → probe_key (TAG="PROBE")

Used in: B (all agents).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class PartitionedPeerStrategy(RSA):
    """Composite strategy: OwnKeyOnly then AlternateOwnProbe."""

    def __init__(self, agent_id: str, own_key: str, probe_key: str,
                 phase_switch_epoch: int,
                 own_authority_ids: list[str], probe_authority_ids: list[str]):
        self.id = agent_id
        self._own_key = own_key
        self._probe_key = probe_key
        self._phase_switch = phase_switch_epoch
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
        if self._current_epoch < self._phase_switch:
            # Phase 1: OwnKeyOnly
            key = self._own_key
            tag = "OWN"
            auth = self._own_authority_ids
        elif self._current_epoch % 2 == 0:
            # Phase 2, even: own_key
            key = self._own_key
            tag = "OWN"
            auth = self._own_authority_ids
        else:
            # Phase 2, odd: probe_key
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
