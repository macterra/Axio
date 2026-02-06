"""
CUD Authority Store — Per preregistration §2.3

Authority artifact storage, capability lookup, holding checks.
All authorities are injected at epoch 0 and immutable thereafter.
"""

from typing import Any
import copy


class AuthorityStore:
    """
    Storage and query for CUD authority artifacts per §2.3.
    Authorities are ALLOW (holder-bound capability) or DENY (global veto).
    """

    def __init__(self):
        self._authorities: list[dict[str, Any]] = []

    def inject(self, authorities: list[dict[str, Any]]) -> None:
        """Inject authority artifacts at epoch 0. Immutable after injection."""
        self._authorities = copy.deepcopy(authorities)

    def get_all(self) -> list[dict[str, Any]]:
        """Return all authority artifacts."""
        return copy.deepcopy(self._authorities)

    def get_by_id(self, authority_id: str) -> dict[str, Any] | None:
        """Look up authority by ID."""
        for auth in self._authorities:
            if auth["authority_id"] == authority_id:
                return copy.deepcopy(auth)
        return None

    def is_held_by(self, authority_id: str, agent_id: str) -> bool:
        """
        Check if authority is held by agent per §2.6 rule 4:
        A.holder_agent_id == X AND A.status == "ACTIVE"
        AND A.created_epoch == 0 AND A exists in epoch-0 set.
        """
        auth = self.get_by_id(authority_id)
        if auth is None:
            return False
        return (
            auth["holder_agent_id"] == agent_id
            and auth["status"] == "ACTIVE"
            and auth["created_epoch"] == 0
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
        """Check if any DENY authority covers (key, op). Global veto."""
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
