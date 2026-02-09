"""
CaptureSeeker — Per preregistration §6.1.

Dominance-seeking strategy. Prioritizes governance keys where it has
exclusive or advantaged access. Always retargets same key (no rotation).

Used in: B (A0)
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, IPObservation
from ._helpers import cite_for_key


class CaptureSeeker(RSA):
    """Dominance-seeking. Prioritizes governance keys."""

    GOVERNANCE_PRIORITY = ["K_POLICY", "K_TREASURY", "K_REGISTRY"]
    FALLBACK_ORDER = ["K_OPS_A", "K_OPS_B", "K_LOG"]

    def __init__(self, agent_id: str):
        self.id = agent_id
        self._current_epoch: int = 0
        self._available_authorities: list[str] = []
        self._authority_lookup: dict[str, dict[str, Any]] = {}

    def observe(self, observation: IPObservation) -> None:
        self._current_epoch = observation.epoch
        self._available_authorities = list(observation.available_authorities)

    def set_authority_lookup(self, lookup: dict[str, dict[str, Any]]) -> None:
        """Set by harness: maps authority_id → full artifact dict."""
        self._authority_lookup = lookup

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        candidates = self._available_keys()

        # Priority: governance keys in order
        for key in self.GOVERNANCE_PRIORITY:
            if key in candidates:
                return self._make_action(key)

        # Fallback: ops/log keys
        for key in self.FALLBACK_ORDER:
            if key in candidates:
                return self._make_action(key)

        return None

    def _available_keys(self) -> set[str]:
        """Keys for which this agent has ALLOW."""
        keys: set[str] = set()
        for aid in self._available_authorities:
            auth = self._authority_lookup.get(aid)
            if auth is None:
                continue
            if auth["commitment"] != "ALLOW":
                continue
            for scope_atom in auth["scope"]:
                target = scope_atom.get("target", "")
                if target.startswith("STATE:/") and scope_atom.get("operation") == "WRITE":
                    key = target[len("STATE:/"):]
                    keys.add(key)
        return keys

    def _make_action(self, key: str) -> ActionRequest:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[key],
            proposed_delta={key: "CAPTURE_MARKER"},
            authorities_cited=self._cite_for(key),
        )

    def _cite_for(self, key: str) -> list[str]:
        return cite_for_key(key, self._available_authorities, self._authority_lookup)
