"""
ContestPolicyAlways — Per preregistration §6.1.

Injection-oblivious control. Always targets K_POLICY regardless of
authority surface. Does not change intent based on authority surface changes.
Will cite injected authority if it covers K_POLICY (does not inspect created_epoch).

Used in: A (A0, A3), B (A3), C (A3), D (A3), E (A0, A3)
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, IPObservation
from ._helpers import cite_for_key


class ContestPolicyAlways(RSA):
    """Injection-oblivious control. Always targets K_POLICY."""

    def __init__(self, agent_id: str):
        self.id = agent_id
        self._current_epoch: int = 0
        self._available_authorities: list[str] = []
        self._authority_lookup: dict[str, dict[str, Any]] = {}

    def observe(self, observation: IPObservation) -> None:
        self._current_epoch = observation.epoch
        self._available_authorities = list(observation.available_authorities)
        # Build lookup from world state — authority details come via harness
        # The _authority_lookup is populated by the harness before observe()

    def set_authority_lookup(self, lookup: dict[str, dict[str, Any]]) -> None:
        """Set by harness: maps authority_id → full artifact dict."""
        self._authority_lookup = lookup

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "POLICY_CONTEST"},
            authorities_cited=self._cite_for("K_POLICY"),
        )

    def _cite_for(self, key: str) -> list[str]:
        return cite_for_key(key, self._available_authorities, self._authority_lookup)
