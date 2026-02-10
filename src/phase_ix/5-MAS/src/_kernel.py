"""
MAS Import Helper — Resolves IX-2 kernel module imports.

All IX-5 modules import IX-2 symbols through this module to avoid
path manipulation in every file.

IX-5 extensions:
  - MASObservation: adds peer_events field (§2.1, §6)
  - MASAuthorityStore: source-blind is_held_by, ALLOW-only (§2.3, §2.6)
"""

import copy
import importlib
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

# ─── Path setup: make IX-2 CUD importable ──────────────────────

_MAS_SRC = os.path.dirname(os.path.abspath(__file__))
_MAS_ROOT = os.path.normpath(os.path.join(_MAS_SRC, '..'))
_CUD_ROOT = os.path.normpath(os.path.join(_MAS_ROOT, '..', '2-CUD'))

if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

# ─── Import IX-2 kernel modules ────────────────────────────────

_agent_model = importlib.import_module("src.agent_model")
_world_state = importlib.import_module("src.world_state")
_authority_store = importlib.import_module("src.authority_store")
_admissibility = importlib.import_module("src.admissibility")

# ─── Re-export IX-2 symbols ────────────────────────────────────

RSA = _agent_model.RSA
Observation = _agent_model.Observation
ActionRequest = _agent_model.ActionRequest
Message = _agent_model.Message

WorldState = _world_state.WorldState
CUDAuthorityStore = _authority_store.AuthorityStore

evaluate_admissibility = _admissibility.evaluate_admissibility
_pass1_check = _admissibility._pass1_check
EXECUTED = _admissibility.EXECUTED
JOINT_ADMISSIBILITY_FAILURE = _admissibility.JOINT_ADMISSIBILITY_FAILURE
ACTION_FAULT = _admissibility.ACTION_FAULT
NO_ACTION = _admissibility.NO_ACTION


# ─── IX-5 Key Sets per §2.4 ────────────────────────────────────

K_INST = frozenset({"K_POLICY", "K_TREASURY", "K_REGISTRY", "K_LOG"})
K_OPS = frozenset({"K_OPS_A", "K_OPS_B"})
ALL_KEYS = K_INST | K_OPS


# ─── IX-5 Extensions ───────────────────────────────────────────

@dataclass(frozen=True)
class PeerEvent:
    """Per-epoch record of another agent's action outcome (§6.2).

    Delivered in OBS_FULL mode only. Contains previous-epoch data.
    """
    epoch: int
    agent_id: str
    event_type: str   # ACTION_ATTEMPT | ACTION_EXECUTED | ACTION_REFUSED | EXIT | SILENCE
    target_key: Optional[str] = None
    outcome_code: Optional[str] = None


@dataclass(frozen=True)
class MASObservation:
    """IX-5 Observation with peer_events field per §2.1, §6.

    Extends IX-2 Observation without modifying IX-2 source.
    No available_authorities field (A-K9).
    """
    epoch: int
    own_last_outcome: Optional[str]   # None at epoch 0
    peer_events: Optional[list[PeerEvent]] = None  # None if OBS_MIN


class MASAuthorityStore:
    """IX-5 Authority Store: ALLOW-only, source-blind, baseline-only.

    - No DENY artifacts (§2.3)
    - No post-epoch-0 injection (no injection engine in IX-5)
    - Source-blind is_held_by (no created_epoch check)
    """

    def __init__(self):
        self._authorities: list[dict[str, Any]] = []

    def inject(self, authorities: list[dict[str, Any]]) -> None:
        """Inject baseline authority artifacts at epoch 0."""
        self._authorities.extend(copy.deepcopy(authorities))

    def get_all(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._authorities)

    def get_by_id(self, authority_id: str) -> Optional[dict[str, Any]]:
        for auth in self._authorities:
            if auth["authority_id"] == authority_id:
                return copy.deepcopy(auth)
        return None

    def is_held_by(self, authority_id: str, agent_id: str) -> bool:
        """Source-blind holding check. No created_epoch filter."""
        auth = self.get_by_id(authority_id)
        if auth is None:
            return False
        return (
            auth["holder_agent_id"] == agent_id
            and auth["status"] == "ACTIVE"
        )

    def get_allows_for_scope(self, key: str, operation: str) -> list[dict[str, Any]]:
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
        """Always False in IX-5 (no DENY artifacts)."""
        return False

    def get_allow_holders_for_scope(self, key: str, operation: str) -> set[str]:
        allows = self.get_allows_for_scope(key, operation)
        return {a["holder_agent_id"] for a in allows}

    def get_allow_ids_for_agent(self, agent_id: str) -> list[str]:
        """Return sorted ALLOW authority IDs held by this agent."""
        results = []
        for auth in self._authorities:
            if auth["commitment"] != "ALLOW":
                continue
            if auth["holder_agent_id"] != agent_id:
                continue
            if auth["status"] != "ACTIVE":
                continue
            results.append(auth["authority_id"])
        results.sort()
        return results

    def has_allow(self, agent_id: str, key: str) -> bool:
        """Check if agent has any ALLOW for (key, WRITE)."""
        holders = self.get_allow_holders_for_scope(key, "WRITE")
        return agent_id in holders
