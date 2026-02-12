"""
RSA X-1 — Artifact Types (Amendment Extension)

Adds AmendmentProposal and AmendmentAdoptionRecord to the closed artifact set.
Extends DecisionType with QUEUE_AMENDMENT and ADOPT.
All artifacts implement dual serialization: to_dict_full() and to_dict_id().

AmendmentProposal.to_dict_id() excludes proposed_constitution_yaml from
the identity hash to avoid whitespace sensitivity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..artifacts import (
    Author,
    DecisionType,
    canonical_json,
    canonical_json_bytes,
    artifact_hash,
    _compute_id,
)


# ---------------------------------------------------------------------------
# Extended enums
# ---------------------------------------------------------------------------

class DecisionTypeX1:
    """X-1 decision types: superset of RSA-0's {ACTION, REFUSE, EXIT}."""
    ACTION = "ACTION"
    QUEUE_AMENDMENT = "QUEUE_AMENDMENT"
    ADOPT = "ADOPT"
    REFUSE = "REFUSE"
    EXIT = "EXIT"

    ALL = frozenset({ACTION, QUEUE_AMENDMENT, ADOPT, REFUSE, EXIT})


class AmendmentRejectionCode:
    """Rejection codes specific to the amendment admission pipeline."""
    AMENDMENTS_DISABLED = "AMENDMENTS_DISABLED"
    PRIOR_HASH_MISMATCH = "PRIOR_HASH_MISMATCH"
    ECK_MISSING = "ECK_MISSING"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    PHYSICS_CLAIM_DETECTED = "PHYSICS_CLAIM_DETECTED"
    WILDCARD_MAPPING = "WILDCARD_MAPPING"
    UNIVERSAL_AUTHORIZATION = "UNIVERSAL_AUTHORIZATION"
    SCOPE_COLLAPSE = "SCOPE_COLLAPSE"
    ENVELOPE_DEGRADED = "ENVELOPE_DEGRADED"
    COOLING_VIOLATION = "COOLING_VIOLATION"

    ALL = frozenset({
        AMENDMENTS_DISABLED, PRIOR_HASH_MISMATCH, ECK_MISSING,
        SCHEMA_INVALID, PHYSICS_CLAIM_DETECTED, WILDCARD_MAPPING,
        UNIVERSAL_AUTHORIZATION, SCOPE_COLLAPSE, ENVELOPE_DEGRADED,
        COOLING_VIOLATION,
    })


class AmendmentGate:
    """Gates 6–8B for the amendment admission pipeline."""
    AUTHORIZATION = "amendment_authorization"          # Gate 6
    FULL_REPLACEMENT_INTEGRITY = "full_replacement_integrity"  # Gate 7
    PHYSICS_CLAIM_REJECTION = "physics_claim_rejection"  # Gate 8A
    STRUCTURAL_PRESERVATION = "structural_preservation"  # Gate 8B


# ---------------------------------------------------------------------------
# AmendmentProposal
# ---------------------------------------------------------------------------

@dataclass
class AmendmentProposal:
    """
    A typed amendment proposal. Full-document replacement only.

    Dual serialization:
      - to_dict_full(): includes proposed_constitution_yaml (for logging)
      - to_dict_id(): excludes proposed_constitution_yaml (for identity hashing)

    The 'id' is computed from to_dict_id() to avoid whitespace sensitivity.
    """
    prior_constitution_hash: str
    proposed_constitution_yaml: str
    proposed_constitution_hash: str
    justification: str
    authority_citations: List[str]
    diff_summary: str = ""
    author: str = Author.REFLECTION.value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id_from_dict(self.to_dict_id())

    def to_dict_full(self) -> Dict[str, Any]:
        """Full serialization including YAML content (for logging/storage)."""
        return {
            "type": "AmendmentProposal",
            "prior_constitution_hash": self.prior_constitution_hash,
            "proposed_constitution_yaml": self.proposed_constitution_yaml,
            "proposed_constitution_hash": self.proposed_constitution_hash,
            "justification": self.justification,
            "authority_citations": self.authority_citations,
            "diff_summary": self.diff_summary,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict_id(self) -> Dict[str, Any]:
        """Identity serialization excluding YAML content (for hash computation)."""
        return {
            "type": "AmendmentProposal",
            "prior_constitution_hash": self.prior_constitution_hash,
            "proposed_constitution_hash": self.proposed_constitution_hash,
            "justification": self.justification,
            "authority_citations": self.authority_citations,
            "diff_summary": self.diff_summary,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Default serialization is full (backward compat)."""
        return self.to_dict_full()


# ---------------------------------------------------------------------------
# AmendmentAdoptionRecord
# ---------------------------------------------------------------------------

@dataclass
class AmendmentAdoptionRecord:
    """
    Kernel-issued record of a constitutional amendment adoption.
    Always authored by kernel.
    """
    proposal_id: str
    prior_constitution_hash: str
    new_constitution_hash: str
    effective_cycle: int
    authority_citations: List[str]
    author: str = Author.KERNEL.value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id_from_dict(self.to_dict_id())

    def to_dict_full(self) -> Dict[str, Any]:
        return {
            "type": "AmendmentAdoptionRecord",
            "proposal_id": self.proposal_id,
            "prior_constitution_hash": self.prior_constitution_hash,
            "new_constitution_hash": self.new_constitution_hash,
            "effective_cycle": self.effective_cycle,
            "authority_citations": self.authority_citations,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict_id(self) -> Dict[str, Any]:
        """Same as to_dict_full for adoption records (no large fields to exclude)."""
        return self.to_dict_full()

    def to_dict(self) -> Dict[str, Any]:
        return self.to_dict_full()


# ---------------------------------------------------------------------------
# Extended Internal State (X-1)
# ---------------------------------------------------------------------------

@dataclass
class PendingAmendment:
    """A queued amendment awaiting cooling period."""
    proposal_id: str
    prior_constitution_hash: str
    proposed_constitution_hash: str
    proposal_cycle: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "prior_constitution_hash": self.prior_constitution_hash,
            "proposed_constitution_hash": self.proposed_constitution_hash,
            "proposal_cycle": self.proposal_cycle,
        }


@dataclass
class InternalStateX1:
    """Extended internal state for X-1 with amendment tracking."""
    cycle_index: int = 0
    last_decision: str = "NONE"
    active_constitution_hash: str = ""
    pending_amendments: List[PendingAmendment] = field(default_factory=list)
    decision_type_history: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_index": self.cycle_index,
            "last_decision": self.last_decision,
            "active_constitution_hash": self.active_constitution_hash,
            "pending_amendments": [p.to_dict() for p in self.pending_amendments],
            "decision_type_history": self.decision_type_history,
        }

    def advance(self, decision_type: str) -> "InternalStateX1":
        """Return next cycle's internal state (pure)."""
        return InternalStateX1(
            cycle_index=self.cycle_index + 1,
            last_decision=decision_type,
            active_constitution_hash=self.active_constitution_hash,
            pending_amendments=list(self.pending_amendments),
            decision_type_history=self.decision_type_history + [decision_type],
        )


# ---------------------------------------------------------------------------
# State delta (output with QUEUE_AMENDMENT and ADOPT decisions)
# ---------------------------------------------------------------------------

@dataclass
class StateDelta:
    """
    Minimal state mutation descriptor emitted with QUEUE_AMENDMENT and ADOPT decisions.
    Consumed by the host to update internal state.
    """
    delta_type: str  # "queue_amendment" | "adopt_amendment" | "invalidate_stale"
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta_type": self.delta_type,
            "payload": self.payload,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_id_from_dict(d: Dict[str, Any]) -> str:
    """Compute artifact ID from a dict, excluding the 'id' field."""
    filtered = {k: v for k, v in d.items() if k != "id"}
    return artifact_hash(filtered)
