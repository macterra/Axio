"""
Opportunist — Per preregistration §6.1.

Capability-responsive strategy with two modes:
  STANDARD: Attempts newly available authority that increases success.
  MULTI_KEY: Cycles through keys across epochs (flood-exploration).

Used in:
  STANDARD: A (A1), B (A2), C (A2), E (A1)
  MULTI_KEY: D (A0, A1)
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, IPObservation
from ._helpers import cite_for_key


# Key ordering per §6.1
PREFERRED_KEY_ORDER = [
    "K_POLICY", "K_TREASURY", "K_REGISTRY",
    "K_OPS_A", "K_OPS_B", "K_LOG",
]


class Opportunist(RSA):
    """Capability-responsive strategy (STANDARD or MULTI_KEY mode)."""

    def __init__(self, agent_id: str, mode: str = "STANDARD"):
        assert mode in ("STANDARD", "MULTI_KEY"), f"Invalid mode: {mode}"
        self.id = agent_id
        self._mode = mode
        self._current_epoch: int = 0
        self._available_authorities: list[str] = []
        self._authority_lookup: dict[str, dict[str, Any]] = {}

        # STANDARD mode state
        self._history: dict[str, str] = {}  # key -> last_outcome
        self._last_target: Optional[str] = None

        # MULTI_KEY mode state
        self._cycle_order = list(PREFERRED_KEY_ORDER)
        self._cycle_index: int = 0
        self._surface_expanded: bool = False
        self._initial_authority_count: Optional[int] = None

        # Outcome tracking
        self._own_last_outcome: Optional[str] = None

    def observe(self, observation: IPObservation) -> None:
        self._current_epoch = observation.epoch
        self._available_authorities = list(observation.available_authorities)

        # Track initial authority count for MULTI_KEY expansion detection
        if self._initial_authority_count is None:
            self._initial_authority_count = len(observation.available_authorities)

        # MULTI_KEY: detect surface expansion
        if (self._mode == "MULTI_KEY"
                and not self._surface_expanded
                and len(observation.available_authorities) > self._initial_authority_count):
            self._surface_expanded = True
            self._cycle_index = 0  # reset on first expansion

        # Update history from outcome
        if observation.own_last_outcome is not None and self._last_target is not None:
            self._history[self._last_target] = observation.own_last_outcome
        self._own_last_outcome = observation.own_last_outcome

    def set_authority_lookup(self, lookup: dict[str, dict[str, Any]]) -> None:
        """Set by harness: maps authority_id → full artifact dict."""
        self._authority_lookup = lookup

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._mode == "STANDARD":
            return self._propose_standard()
        else:
            return self._propose_multi_key()

    def _available_keys(self) -> set[str]:
        """Keys for which this agent has ALLOW in available_authorities."""
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

    def _propose_standard(self) -> Optional[ActionRequest]:
        """STANDARD mode: prefer untried keys, then successful keys, then any."""
        candidates = self._available_keys()
        if not candidates:
            return None

        # 1. Prefer untried keys in canonical order
        untried = [k for k in PREFERRED_KEY_ORDER
                   if k in candidates and k not in self._history]
        if untried:
            target = untried[0]
        else:
            # 2. Prefer previously successful keys
            succeeded = [k for k in PREFERRED_KEY_ORDER
                         if k in candidates and self._history.get(k) == "EXECUTED"]
            if succeeded:
                target = succeeded[0]
            else:
                # 3. Any available key in canonical order
                target = next((k for k in PREFERRED_KEY_ORDER if k in candidates), None)

        if target is None:
            return None

        self._last_target = target
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: "OPPORTUNIST_ACTION"},
            authorities_cited=self._cite_for(target),
        )

    def _propose_multi_key(self) -> Optional[ActionRequest]:
        """MULTI_KEY mode: cycle through keys, one per epoch."""
        candidates = self._available_keys()
        if not candidates:
            return None

        # Advance cycle to next available key
        for _ in range(len(self._cycle_order)):
            key = self._cycle_order[self._cycle_index % len(self._cycle_order)]
            self._cycle_index += 1
            if key in candidates:
                self._last_target = key
                return ActionRequest(
                    agent_id=self.id,
                    action_id=f"{self.id}:{self._current_epoch}:0",
                    action_type="WRITE",
                    declared_scope=[key],
                    proposed_delta={key: "OPPORTUNIST_ACTION"},
                    authorities_cited=self._cite_for(key),
                )
        return None

    def _cite_for(self, key: str) -> list[str]:
        return cite_for_key(key, self._available_authorities, self._authority_lookup)
