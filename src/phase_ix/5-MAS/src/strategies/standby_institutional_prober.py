"""
StandbyInstitutionalProber — Per preregistration §5.8.

Frozen probe schedule (A-L5):
  - Epochs 0–11: always write own_key (TAG="OWN")
  - Epochs 12–17: even → own_key, odd → K_REGISTRY probe (TAG="PROBE")
  - Epochs ≥18: even → own_key, odd with (epoch % 4 == 1) → K_REGISTRY,
                odd with (epoch % 4 == 3) → K_LOG

Probes to keys without ALLOW are expected to be refused.
Used in: E (A0, A1).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class StandbyInstitutionalProber(RSA):
    """Writes own key and deterministically probes orphaned institutional keys."""

    def __init__(self, agent_id: str, own_key: str,
                 own_authority_ids: list[str],
                 probe_authority_ids: Optional[dict[str, list[str]]] = None):
        self.id = agent_id
        self._own_key = own_key
        self._own_authority_ids = own_authority_ids
        # probe_authority_ids: key -> [authority_ids], may be empty for unauthorized probes
        self._probe_authority_ids = probe_authority_ids or {}
        self._current_epoch: int = 0

    def observe(self, observation: MASObservation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def _get_target(self) -> tuple[str, str, list[str]]:
        """Return (key, tag, authority_ids) for current epoch."""
        e = self._current_epoch

        if e < 12:
            # Phase 1: always own_key
            return self._own_key, "OWN", self._own_authority_ids

        if e < 18:
            # Phase 2: even → own, odd → K_REGISTRY probe
            if e % 2 == 0:
                return self._own_key, "OWN", self._own_authority_ids
            else:
                return "K_REGISTRY", "PROBE", self._probe_authority_ids.get("K_REGISTRY", [])

        # Phase 3 (epoch ≥ 18): even → own, odd → deterministic probe
        if e % 2 == 0:
            return self._own_key, "OWN", self._own_authority_ids
        elif e % 4 == 1:
            return "K_REGISTRY", "PROBE", self._probe_authority_ids.get("K_REGISTRY", [])
        else:  # e % 4 == 3
            return "K_LOG", "PROBE", self._probe_authority_ids.get("K_LOG", [])

    def propose_action(self) -> Optional[ActionRequest]:
        key, tag, auth = self._get_target()
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
