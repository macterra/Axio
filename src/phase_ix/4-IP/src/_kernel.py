"""
IP Import Helper — Resolves IX-2 kernel module imports.

All IX-4 modules import IX-2 symbols through this module to avoid
path manipulation in every file.

IX-4 extensions:
  - IPObservation: adds available_authorities field (§2.1)
  - IPAuthorityStore: source-blind is_held_by (§2.6, §7.2)
"""

import copy
import importlib
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

# ─── Path setup: make IX-2 CUD importable ──────────────────────

_IP_SRC = os.path.dirname(os.path.abspath(__file__))
_IP_ROOT = os.path.normpath(os.path.join(_IP_SRC, '..'))
_CUD_ROOT = os.path.normpath(os.path.join(_IP_ROOT, '..', '2-CUD'))

if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

# ─── Import IX-2 kernel modules ────────────────────────────────

_agent_model = importlib.import_module("src.agent_model")
_world_state = importlib.import_module("src.world_state")
_authority_store = importlib.import_module("src.authority_store")
_admissibility = importlib.import_module("src.admissibility")

# ─── Re-export IX-2 symbols ────────────────────────────────────

# agent_model
RSA = _agent_model.RSA
Observation = _agent_model.Observation
ActionRequest = _agent_model.ActionRequest
Message = _agent_model.Message

# world_state
WorldState = _world_state.WorldState

# authority_store (IX-2 base)
CUDAuthorityStore = _authority_store.AuthorityStore

# admissibility
evaluate_admissibility = _admissibility.evaluate_admissibility
EXECUTED = _admissibility.EXECUTED
JOINT_ADMISSIBILITY_FAILURE = _admissibility.JOINT_ADMISSIBILITY_FAILURE
ACTION_FAULT = _admissibility.ACTION_FAULT
NO_ACTION = _admissibility.NO_ACTION

# Pass-1 internal function (for harness-level diagnostic access)
_pass1_check = _admissibility._pass1_check


# ─── IX-4 Extensions ───────────────────────────────────────────

@dataclass(frozen=True)
class IPObservation:
    """IX-4 Observation with available_authorities field per §2.1.

    Extends IX-2 Observation without modifying the IX-2 source.
    The available_authorities field exposes already-existing public state
    (the AuthorityStore view) in a read-only, provenance-free way.
    """
    epoch: int
    world_state: dict[str, Any]
    own_last_outcome: Optional[str]
    own_last_action_id: Optional[str]
    own_last_declared_scope: Optional[list[str]]
    messages: list[Message]
    available_authorities: list[str]  # authority IDs of ALLOW artifacts for this agent


class IPAuthorityStore:
    """IX-4 Authority Store with source-blind is_held_by per §2.6, §7.2.

    Extends IX-2 AuthorityStore to support:
    1. Post-epoch-0 injection (created_epoch > 0)
    2. Source-blind is_held_by (does NOT check created_epoch)
    3. Dynamic authority surface queries per agent
    """

    def __init__(self):
        self._authorities: list[dict[str, Any]] = []

    def inject(self, authorities: list[dict[str, Any]]) -> None:
        """Inject authority artifacts. Can be called multiple times."""
        self._authorities.extend(copy.deepcopy(authorities))

    def get_all(self) -> list[dict[str, Any]]:
        """Return all authority artifacts (deep copy)."""
        return copy.deepcopy(self._authorities)

    def get_by_id(self, authority_id: str) -> dict[str, Any] | None:
        """Look up authority by ID."""
        for auth in self._authorities:
            if auth["authority_id"] == authority_id:
                return copy.deepcopy(auth)
        return None

    def is_held_by(self, authority_id: str, agent_id: str) -> bool:
        """Check if authority is held by agent — SOURCE-BLIND per §2.6.

        Unlike IX-2's is_held_by, this does NOT check created_epoch.
        Baseline and injected artifacts are treated identically.
        """
        auth = self.get_by_id(authority_id)
        if auth is None:
            return False
        return (
            auth["holder_agent_id"] == agent_id
            and auth["status"] == "ACTIVE"
        )

    def get_allows_for_scope(self, key: str, operation: str) -> list[dict[str, Any]]:
        """Get all ALLOW authorities covering (key, op)."""
        target = f"STATE:/{key}"
        result = []
        for auth in self._authorities:
            if auth["commitment"] != "ALLOW":
                continue
            for scope_atom in auth["scope"]:
                if scope_atom["target"] == target and scope_atom["operation"] == operation:
                    result.append(copy.deepcopy(auth))
                    break
        return result

    def has_deny_for_scope(self, key: str, operation: str) -> bool:
        """Check if any DENY authority covers (key, op)."""
        target = f"STATE:/{key}"
        for auth in self._authorities:
            if auth["commitment"] != "DENY":
                continue
            for scope_atom in auth["scope"]:
                if scope_atom["target"] == target and scope_atom["operation"] == operation:
                    return True
        return False

    def get_allow_holders_for_scope(self, key: str, operation: str) -> set[str]:
        """Return set of agent_ids that hold ALLOW for (key, op)."""
        allows = self.get_allows_for_scope(key, operation)
        return {a["holder_agent_id"] for a in allows}

    def get_allow_ids_for_agent(self, agent_id: str) -> list[str]:
        """Return ALLOW authority IDs held by this agent, sorted by canonical serialization.

        Per §7.2: sorted by lexicographically smallest canonical serialization
        of the full artifact (keys in canonical field order, compact JSON).
        """
        import json
        results = []
        for auth in self._authorities:
            if auth["commitment"] != "ALLOW" and auth.get("commitment") != "ALLOW":
                continue
            if auth["holder_agent_id"] != agent_id:
                continue
            if auth["status"] != "ACTIVE":
                continue
            # Canonical serialization per §2.5
            canonical = json.dumps({
                "authority_id": auth["authority_id"],
                "commitment": auth["commitment"],
                "created_epoch": auth["created_epoch"],
                "holder_agent_id": auth["holder_agent_id"],
                "issuer_agent_id": auth["issuer_agent_id"],
                "scope": [{"operation": s["operation"], "target": s["target"]}
                          for s in auth["scope"]],
                "status": auth["status"],
            }, separators=(',', ':'), ensure_ascii=False)
            results.append((canonical, auth["authority_id"]))
        # Sort by canonical serialization
        results.sort(key=lambda x: x[0])
        return [aid for _, aid in results]
