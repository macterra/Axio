"""
RSA X-2 — Artifact Types (Treaty Extension)

Adds TreatyGrant, TreatyRevocation, and delegated ActionRequest support.
Extends DecisionType for X-2 (superset of X-1).
All artifacts implement dual serialization: to_dict_full() and to_dict_id().

TreatyGrant.to_dict_id() includes ALL fields (canonicalized for hash stability).
List fields are sorted lexicographically before hashing.

scope_constraints is a map {scope_type: [zone_label...]}, keys sorted,
each zone list sorted+unique, subset of ScopeEnumerations (8C.3).

Density uses distinct (authority, action) pairs per CL-EFFECTIVE-DENSITY-DEFINITION.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ..artifacts import (
    Author,
    canonical_json,
    canonical_json_bytes,
    artifact_hash,
    _compute_id,
)
from ..rsax1.artifacts_x1 import (
    DecisionTypeX1,
    AmendmentProposal,
    AmendmentRejectionCode,
    PendingAmendment,
    InternalStateX1,
    StateDelta,
)


# ---------------------------------------------------------------------------
# Extended Decision Types (X-2)
# ---------------------------------------------------------------------------

class DecisionTypeX2:
    """X-2 decision types: superset of X-1."""
    ACTION = "ACTION"
    QUEUE_AMENDMENT = "QUEUE_AMENDMENT"
    ADOPT = "ADOPT"
    REFUSE = "REFUSE"
    EXIT = "EXIT"

    ALL = frozenset({ACTION, QUEUE_AMENDMENT, ADOPT, REFUSE, EXIT})


# ---------------------------------------------------------------------------
# Treaty Rejection Codes
# ---------------------------------------------------------------------------

class TreatyRejectionCode:
    """Rejection codes specific to the treaty admission pipeline."""
    # Grant gates (6T/7T/8C)
    GRANTOR_NOT_CONSTITUTIONAL = "GRANTOR_NOT_CONSTITUTIONAL"
    GRANTOR_LACKS_PERMISSION = "GRANTOR_LACKS_PERMISSION"
    TREATY_PERMISSION_MISSING = "TREATY_PERMISSION_MISSING"
    SCOPE_COLLAPSE = "SCOPE_COLLAPSE"
    COVERAGE_INFLATION = "COVERAGE_INFLATION"
    EXCESSIVE_DEPTH = "EXCESSIVE_DEPTH"
    DELEGATION_CYCLE = "DELEGATION_CYCLE"
    DENSITY_MARGIN_VIOLATION = "DENSITY_MARGIN_VIOLATION"
    WILDCARD_MAPPING = "WILDCARD_MAPPING"
    # Revocation gates (8R)
    NONREVOCABLE_GRANT = "NONREVOCABLE_GRANT"
    GRANT_NOT_FOUND = "GRANT_NOT_FOUND"
    GRANT_INACTIVE = "GRANT_INACTIVE"
    # Shared
    SCHEMA_INVALID = "SCHEMA_INVALID"
    INVALID_FIELD = "INVALID_FIELD"
    AUTHORITY_CITATION_INVALID = "AUTHORITY_CITATION_INVALID"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    SIGNATURE_MISSING = "SIGNATURE_MISSING"

    ALL = frozenset({
        GRANTOR_NOT_CONSTITUTIONAL, GRANTOR_LACKS_PERMISSION,
        TREATY_PERMISSION_MISSING, SCOPE_COLLAPSE, COVERAGE_INFLATION,
        EXCESSIVE_DEPTH, DELEGATION_CYCLE, DENSITY_MARGIN_VIOLATION,
        WILDCARD_MAPPING, NONREVOCABLE_GRANT, GRANT_NOT_FOUND,
        GRANT_INACTIVE,
        SCHEMA_INVALID, INVALID_FIELD, AUTHORITY_CITATION_INVALID,
        SIGNATURE_INVALID, SIGNATURE_MISSING,
    })


class TreatyGate:
    """Gates for the treaty admission pipeline."""
    AUTHORIZATION = "treaty_authorization"           # Gate 6T
    SCHEMA_VALIDITY = "treaty_schema_validity"       # Gate 7T
    DELEGATION_PRESERVATION = "delegation_preservation"  # Gate 8C
    REVOCATION_VALIDITY = "revocation_validity"      # Gate 8R


# ---------------------------------------------------------------------------
# Grantee Identifier
# ---------------------------------------------------------------------------

GRANTEE_ID_PATTERN = re.compile(r"^ed25519:[0-9a-fA-F]{64}$")


def validate_grantee_identifier(grantee_id: str) -> bool:
    """Check if grantee_identifier matches ed25519:<hex64> format."""
    return bool(GRANTEE_ID_PATTERN.match(grantee_id))


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

def canonicalize_treaty_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonicalize a treaty artifact dict for hashing:
    - Sort dict keys
    - Sort list fields (granted_actions, authority_citations) lexicographically
    - For scope_constraints map: sort keys and sort each zone list
    Returns a new dict (does not mutate input).
    """
    SORTED_LIST_FIELDS = frozenset({
        "granted_actions", "authority_citations",
    })
    out = {}
    for k in sorted(d.keys()):
        v = d[k]
        if k == "scope_constraints" and isinstance(v, dict):
            # Map canonicalization: sort keys, sort each zone list
            out[k] = {
                sk: sorted(sv) if isinstance(sv, list) else sv
                for sk, sv in sorted(v.items())
            }
        elif k in SORTED_LIST_FIELDS and isinstance(v, list):
            out[k] = sorted(v, key=str)
        elif isinstance(v, dict):
            out[k] = canonicalize_treaty_dict(v)
        else:
            out[k] = v
    return out


def treaty_canonical_hash(d: Dict[str, Any]) -> str:
    """SHA-256 of canonicalized treaty dict (excluding 'id' field)."""
    filtered = {k: v for k, v in d.items() if k != "id"}
    canonical = canonicalize_treaty_dict(filtered)
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# TreatyGrant
# ---------------------------------------------------------------------------

@dataclass
class TreatyGrant:
    """
    Typed treaty grant artifact: explicit scoped delegation.

    scope_constraints: map {scope_type: [zone_label...]} per CL-SCOPE-ENUMERATIONS.
    All list fields are sorted lexicographically before hashing.
    """
    grantor_authority_id: str
    grantee_identifier: str
    granted_actions: List[str]
    scope_constraints: Dict[str, List[str]]  # {scope_type: [zone_labels]}
    duration_cycles: int
    revocable: bool
    authority_citations: List[str]
    justification: str
    author: str = Author.REFLECTION.value
    created_at: str = ""
    grant_cycle: int = -1  # set by kernel at admission time (not in schema)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = treaty_canonical_hash(self.to_dict_full())

    def to_dict_full(self) -> Dict[str, Any]:
        """Full dict including all constitutional fields. grant_cycle excluded (runtime)."""
        return {
            "type": "TreatyGrant",
            "grantor_authority_id": self.grantor_authority_id,
            "grantee_identifier": self.grantee_identifier,
            "granted_actions": sorted(self.granted_actions),
            "scope_constraints": {
                k: sorted(v)
                for k, v in sorted(self.scope_constraints.items())
            },
            "duration_cycles": self.duration_cycles,
            "revocable": self.revocable,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict_id(self) -> Dict[str, Any]:
        """Same as full — all fields included for identity hash."""
        return self.to_dict_full()

    def to_dict(self) -> Dict[str, Any]:
        return self.to_dict_full()

    def to_dict_internal(self) -> Dict[str, Any]:
        """Full dict with runtime fields (grant_cycle) for internal tracking."""
        d = self.to_dict_full()
        d["grant_cycle"] = self.grant_cycle
        return d

    def is_active(self, current_cycle: int) -> bool:
        """Check if grant is active in the given cycle."""
        if self.grant_cycle < 0:
            return False
        return self.grant_cycle <= current_cycle <= self.grant_cycle + self.duration_cycles - 1

    def expiry_cycle(self) -> int:
        """Last cycle this grant is active."""
        return self.grant_cycle + self.duration_cycles - 1

    def all_zone_labels(self) -> Set[str]:
        """Return flat set of all zone labels across all scope_types."""
        result: Set[str] = set()
        for zones in self.scope_constraints.values():
            result.update(zones)
        return result


# ---------------------------------------------------------------------------
# TreatyRevocation
# ---------------------------------------------------------------------------

@dataclass
class TreatyRevocation:
    """Typed treaty revocation artifact."""
    grant_id: str
    authority_citations: List[str]
    justification: str
    author: str = Author.REFLECTION.value
    created_at: str = ""
    effective_cycle: int = -1  # set by kernel
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = treaty_canonical_hash(self.to_dict_full())

    def to_dict_full(self) -> Dict[str, Any]:
        return {
            "type": "TreatyRevocation",
            "grant_id": self.grant_id,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict_id(self) -> Dict[str, Any]:
        return self.to_dict_full()

    def to_dict(self) -> Dict[str, Any]:
        return self.to_dict_full()


# ---------------------------------------------------------------------------
# Active Treaty Set
# ---------------------------------------------------------------------------

@dataclass
class ActiveTreatySet:
    """
    Tracks all active treaty grants for a given cycle.
    Reconstructible from log stream — no persistent state.
    """
    grants: List[TreatyGrant] = field(default_factory=list)
    revoked_grant_ids: set = field(default_factory=set)

    def active_grants(self, current_cycle: int) -> List[TreatyGrant]:
        """Return grants that are active and not revoked in the given cycle."""
        return [
            g for g in self.grants
            if g.is_active(current_cycle) and g.id not in self.revoked_grant_ids
        ]

    def add_grant(self, grant: TreatyGrant) -> None:
        self.grants.append(grant)

    def revoke(self, grant_id: str) -> bool:
        """Revoke a grant. Returns True if found and revocable."""
        for g in self.grants:
            if g.id == grant_id:
                if not g.revocable:
                    return False
                self.revoked_grant_ids.add(grant_id)
                return True
        return False

    def find_grant(self, grant_id: str) -> Optional[TreatyGrant]:
        for g in self.grants:
            if g.id == grant_id:
                return g
        return None

    def is_grantee(self, identifier: str, current_cycle: int) -> bool:
        """Check if identifier has any active grant."""
        return any(
            g.grantee_identifier == identifier
            for g in self.active_grants(current_cycle)
        )

    def grants_for_grantee(self, identifier: str, current_cycle: int) -> List[TreatyGrant]:
        """Return all active grants for a specific grantee."""
        return [
            g for g in self.active_grants(current_cycle)
            if g.grantee_identifier == identifier
        ]

    def delegation_graph_edges(self, current_cycle: int) -> List[tuple]:
        """Return (grantor, grantee) edges for cycle detection."""
        return [
            (g.grantor_authority_id, g.grantee_identifier)
            for g in self.active_grants(current_cycle)
        ]

    def would_create_cycle(self, new_grant: TreatyGrant, current_cycle: int) -> bool:
        """Check if adding new_grant creates a cycle in the delegation graph."""
        edges = self.delegation_graph_edges(current_cycle)
        edges.append((new_grant.grantor_authority_id, new_grant.grantee_identifier))

        adj: Dict[str, List[str]] = {}
        for src, dst in edges:
            adj.setdefault(src, []).append(dst)

        visited: set = set()
        in_stack: set = set()

        def has_cycle(node: str) -> bool:
            if node in in_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            in_stack.add(node)
            for neighbor in adj.get(node, []):
                if has_cycle(neighbor):
                    return True
            in_stack.discard(node)
            return False

        for node in adj:
            if has_cycle(node):
                return True
        return False

    def prune_for_density(
        self,
        max_density: float,
        action_permissions: List[Dict[str, Any]],
        action_type_count: int,
        current_cycle: int,
    ) -> List[str]:
        """
        Deterministic greedy pruning: oldest first, then canonical hash ASC.
        Returns list of pruned grant IDs.
        """
        pruned: List[str] = []
        active = self.active_grants(current_cycle)
        # Sort: grant_cycle ASC, then id ASC (canonical hash)
        active_sorted = sorted(active, key=lambda g: (g.grant_cycle, g.id))

        while True:
            current_active = [
                g for g in active_sorted
                if g.id not in self.revoked_grant_ids and g.id not in pruned
            ]
            d = _compute_effective_density(
                action_permissions, current_active, action_type_count
            )
            # Reject d==1.0 per CL-EFFECTIVE-DENSITY-DEFINITION
            if d <= max_density and d != 1.0:
                break
            if not current_active:
                break
            victim = current_active[0]
            pruned.append(victim.id)

        return pruned


# ---------------------------------------------------------------------------
# Extended Internal State (X-2)
# ---------------------------------------------------------------------------

@dataclass
class InternalStateX2(InternalStateX1):
    """Extended internal state for X-2 with treaty tracking."""
    active_treaty_set: ActiveTreatySet = field(default_factory=ActiveTreatySet)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["active_grants"] = [g.to_dict_internal() for g in self.active_treaty_set.grants]
        d["revoked_grant_ids"] = sorted(self.active_treaty_set.revoked_grant_ids)
        return d

    def advance(self, decision_type: str) -> "InternalStateX2":
        return InternalStateX2(
            cycle_index=self.cycle_index + 1,
            last_decision=decision_type,
            active_constitution_hash=self.active_constitution_hash,
            pending_amendments=list(self.pending_amendments),
            decision_type_history=self.decision_type_history + [decision_type],
            active_treaty_set=self.active_treaty_set,
        )


# ---------------------------------------------------------------------------
# Treaty Trace Events
# ---------------------------------------------------------------------------

@dataclass
class TreatyAdmissionEvent:
    """Trace event for treaty admission pipeline."""
    artifact_id: str
    artifact_type: str  # "TreatyGrant" | "TreatyRevocation"
    gate: str
    result: str  # "pass" | "fail"
    reason_code: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "event_type": "treaty_admission_event",
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "gate": self.gate,
            "result": self.result,
        }
        if self.reason_code:
            d["reason_code"] = self.reason_code
        if self.detail:
            d["detail"] = self.detail
        return d


@dataclass
class TreatyAdmissionResult:
    """Result of treaty artifact admission."""
    artifact_id: str
    artifact_type: str
    admitted: bool
    events: List[TreatyAdmissionEvent] = field(default_factory=list)
    failed_gate: str = ""
    rejection_code: str = ""
    # For grants: density info on success
    effective_density: float = 0.0
    a_eff: int = 0
    m_eff: int = 0


# ---------------------------------------------------------------------------
# Helpers — Effective Density (distinct pairs)
# ---------------------------------------------------------------------------

def _compute_effective_density(
    action_permissions: List[Dict[str, Any]],
    active_grants: List[TreatyGrant],
    action_type_count: int,
) -> float:
    """
    Compute effective density including treaty grants.
    Per CL-EFFECTIVE-DENSITY-DEFINITION:
      A_eff = distinct authorities in action_permissions UNION distinct active grantees
      B     = count of action_space.action_types
      M_eff = count of distinct (authority, action) pairs:
              constitutional UNION delegated
      d_eff = M_eff / (A_eff * B)

    Uses SET UNION for distinct (authority, action) pairs.
    """
    # Constitutional pairs: {(authority, action)}
    const_pairs: Set[Tuple[str, str]] = set()
    const_authorities: Set[str] = set()
    for perm in action_permissions:
        auth = perm.get("authority", "")
        const_authorities.add(auth)
        for action in perm.get("actions", []):
            const_pairs.add((auth, action))

    # Treaty pairs: {(grantee_identifier, action)}
    treaty_pairs: Set[Tuple[str, str]] = set()
    treaty_grantees: Set[str] = set()
    for grant in active_grants:
        treaty_grantees.add(grant.grantee_identifier)
        for action in grant.granted_actions:
            treaty_pairs.add((grant.grantee_identifier, action))

    A_eff = len(const_authorities) + len(treaty_grantees)
    B = action_type_count
    M_eff = len(const_pairs | treaty_pairs)  # UNION — distinct pairs total

    if A_eff == 0 or B == 0:
        return 0.0

    return M_eff / (A_eff * B)
