"""
RefusalHardliner — Per preregistration §6.1.

Baseline-institutionalist. Never cites post-epoch-0 authority.
Snapshots available_authorities at epoch 0 and only uses those IDs.

Used in: A (A2), B (A1), C (A1), D (A2), E (A2)
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, IPObservation
from ._helpers import cite_for_key


class RefusalHardliner(RSA):
    """Baseline-institutionalist. Only cites epoch-0 authority."""

    def __init__(self, agent_id: str):
        self.id = agent_id
        self._current_epoch: int = 0
        self._epoch0_authorities: Optional[list[str]] = None
        self._available_authorities: list[str] = []
        self._authority_lookup: dict[str, dict[str, Any]] = {}

    def observe(self, observation: IPObservation) -> None:
        self._current_epoch = observation.epoch
        self._available_authorities = list(observation.available_authorities)
        # Snapshot epoch-0 authorities on first observe
        if self._epoch0_authorities is None:
            self._epoch0_authorities = list(observation.available_authorities)

    def set_authority_lookup(self, lookup: dict[str, dict[str, Any]]) -> None:
        """Set by harness: maps authority_id → full artifact dict."""
        self._authority_lookup = lookup

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        # Per §6.1: RefusalHardliner restricts eligible artifacts to epoch-0 snapshot
        eligible = self._epoch0_authorities if self._epoch0_authorities else []
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "POLICY_PROPOSAL"},
            authorities_cited=cite_for_key(
                "K_POLICY", eligible, self._authority_lookup
            ),
        )
