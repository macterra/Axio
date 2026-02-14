"""
RSA X-3 — Artifact Types (Succession Extension)

Adds SuccessionProposal, TreatyRatification, CycleCommitPayload,
CycleStartPayload, and X-3 state types.
Extends InternalStateX2 with sovereign lineage tracking.

All artifacts implement dual serialization: to_dict_full() and to_dict_id().
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from ..artifacts import (
    Author,
    canonical_json,
    canonical_json_bytes,
    artifact_hash,
    _compute_id,
)
from ..rsax1.artifacts_x1 import (
    AmendmentProposal,
    AmendmentRejectionCode,
    PendingAmendment,
    InternalStateX1,
    StateDelta,
    _compute_id_from_dict,
)
from ..rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRevocation,
    TreatyAdmissionEvent,
    TreatyAdmissionResult,
    TreatyRevalidationEvent,
)


# ---------------------------------------------------------------------------
# Extended Decision Types (X-3)
# ---------------------------------------------------------------------------

class DecisionTypeX3:
    """X-3 decision types: superset of X-2."""
    ACTION = "ACTION"
    QUEUE_AMENDMENT = "QUEUE_AMENDMENT"
    ADOPT = "ADOPT"
    REFUSE = "REFUSE"
    EXIT = "EXIT"

    ALL = frozenset({ACTION, QUEUE_AMENDMENT, ADOPT, REFUSE, EXIT})


# ---------------------------------------------------------------------------
# Succession Rejection Codes
# ---------------------------------------------------------------------------

class SuccessionRejectionCode:
    """Rejection codes for the SuccessionProposal admission pipeline."""
    INVALID_FIELD = "INVALID_FIELD"
    AUTHORITY_CITATION_INVALID = "AUTHORITY_CITATION_INVALID"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    PRIOR_SOVEREIGN_MISMATCH = "PRIOR_SOVEREIGN_MISMATCH"
    IDENTITY_CYCLE = "IDENTITY_CYCLE"
    LINEAGE_FORK = "LINEAGE_FORK"
    SUCCESSION_DISABLED = "SUCCESSION_DISABLED"
    MULTIPLE_SUCCESSIONS_IN_CYCLE = "MULTIPLE_SUCCESSIONS_IN_CYCLE"
    PRIOR_KEY_PRIVILEGE_LEAK = "PRIOR_KEY_PRIVILEGE_LEAK"

    ALL = frozenset({
        INVALID_FIELD, AUTHORITY_CITATION_INVALID, SIGNATURE_INVALID,
        PRIOR_SOVEREIGN_MISMATCH, IDENTITY_CYCLE, LINEAGE_FORK,
        SUCCESSION_DISABLED, MULTIPLE_SUCCESSIONS_IN_CYCLE,
        PRIOR_KEY_PRIVILEGE_LEAK,
    })


class SuccessionGate:
    """Gates for the succession admission pipeline (S1–S7)."""
    S1_COMPLETENESS = "s1_completeness"
    S2_CITATION_SNAPSHOT = "s2_citation_snapshot"
    S3_SIGNATURE = "s3_signature"
    S4_SOVEREIGN_MATCH = "s4_sovereign_match"
    S5_LINEAGE_INTEGRITY = "s5_lineage_integrity"
    S6_CONSTITUTIONAL_COMPLIANCE = "s6_constitutional_compliance"
    S7_PER_CYCLE_UNIQUENESS = "s7_per_cycle_uniqueness"


# ---------------------------------------------------------------------------
# Ratification Rejection Codes
# ---------------------------------------------------------------------------

class RatificationRejectionCode:
    """Rejection codes for TreatyRatification admission."""
    SCHEMA_INVALID = "SCHEMA_INVALID"
    INVALID_FIELD = "INVALID_FIELD"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    TREATY_NOT_SUSPENDED = "TREATY_NOT_SUSPENDED"
    DENSITY_MARGIN_VIOLATION = "DENSITY_MARGIN_VIOLATION"
    PRIOR_KEY_PRIVILEGE_LEAK = "PRIOR_KEY_PRIVILEGE_LEAK"

    ALL = frozenset({
        SCHEMA_INVALID, INVALID_FIELD, SIGNATURE_INVALID,
        TREATY_NOT_SUSPENDED, DENSITY_MARGIN_VIOLATION,
        PRIOR_KEY_PRIVILEGE_LEAK,
    })


class RatificationGate:
    """Gates for the ratification admission pipeline (R0–R4)."""
    R0_SCHEMA = "r0_schema"
    R1_COMPLETENESS = "r1_completeness"
    R2_SIGNATURE = "r2_signature"
    R3_TREATY_SUSPENDED = "r3_treaty_suspended"
    R4_DENSITY = "r4_density"


# ---------------------------------------------------------------------------
# Boundary Codes
# ---------------------------------------------------------------------------

class BoundaryCode:
    """Boundary verification failure codes."""
    BOUNDARY_SIGNATURE_MISMATCH = "BOUNDARY_SIGNATURE_MISMATCH"
    BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR = "BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR"
    BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR = "BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR"
    BOUNDARY_STATE_CHAIN_MISMATCH = "BOUNDARY_STATE_CHAIN_MISMATCH"

    ALL = frozenset({
        BOUNDARY_SIGNATURE_MISMATCH,
        BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR,
        BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR,
        BOUNDARY_STATE_CHAIN_MISMATCH,
    })


# ---------------------------------------------------------------------------
# Authority Codes
# ---------------------------------------------------------------------------

class AuthorityCode:
    """Authority-related rejection codes for X-3."""
    PRIOR_KEY_PRIVILEGE_LEAK = "PRIOR_KEY_PRIVILEGE_LEAK"
    SUSPENSION_UNRESOLVED = "SUSPENSION_UNRESOLVED"


# ---------------------------------------------------------------------------
# SuccessionProposal
# ---------------------------------------------------------------------------

SUCCESSION_REQUIRED_FIELDS = frozenset({
    "type", "prior_sovereign_public_key", "successor_public_key",
    "authority_citations", "justification", "signature",
})


@dataclass
class SuccessionProposal:
    """
    Sovereign succession proposal artifact.

    Proposes transition of sovereign identity from prior key to successor key.
    Must be signed by the prior (active) sovereign.
    """
    prior_sovereign_public_key: str
    successor_public_key: str
    authority_citations: List[str]
    justification: str
    signature: str
    author: str = Author.REFLECTION.value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id_from_dict(self.to_dict_id())

    def to_dict_full(self) -> Dict[str, Any]:
        return {
            "type": "SuccessionProposal",
            "prior_sovereign_public_key": self.prior_sovereign_public_key,
            "successor_public_key": self.successor_public_key,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "signature": self.signature,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict_id(self) -> Dict[str, Any]:
        """Identity hash excludes signature (payload identity)."""
        return {
            "type": "SuccessionProposal",
            "prior_sovereign_public_key": self.prior_sovereign_public_key,
            "successor_public_key": self.successor_public_key,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.to_dict_full()

    def signing_payload(self) -> Dict[str, Any]:
        """Payload to sign/verify (excludes signature and id fields)."""
        return {
            "type": "SuccessionProposal",
            "prior_sovereign_public_key": self.prior_sovereign_public_key,
            "successor_public_key": self.successor_public_key,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
        }

    def is_self_succession(self) -> bool:
        """True if successor equals prior (no-op succession)."""
        return self.successor_public_key == self.prior_sovereign_public_key


# ---------------------------------------------------------------------------
# TreatyRatification
# ---------------------------------------------------------------------------

RATIFICATION_REQUIRED_FIELDS = frozenset({
    "type", "treaty_id", "ratify", "signature",
})


@dataclass
class TreatyRatification:
    """
    Treaty ratification artifact.

    Submitted by the new sovereign to either restore (ratify=True) or
    revoke (ratify=False) a suspended treaty.
    """
    treaty_id: str
    ratify: bool
    signature: str
    authority_citations: List[str] = field(default_factory=list)
    justification: str = ""
    author: str = Author.REFLECTION.value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id_from_dict(self.to_dict_id())

    def to_dict_full(self) -> Dict[str, Any]:
        return {
            "type": "TreatyRatification",
            "treaty_id": self.treaty_id,
            "ratify": self.ratify,
            "signature": self.signature,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict_id(self) -> Dict[str, Any]:
        """Identity hash excludes signature."""
        return {
            "type": "TreatyRatification",
            "treaty_id": self.treaty_id,
            "ratify": self.ratify,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.to_dict_full()

    def signing_payload(self) -> Dict[str, Any]:
        """Payload to sign/verify (excludes signature and id fields)."""
        return {
            "type": "TreatyRatification",
            "treaty_id": self.treaty_id,
            "ratify": self.ratify,
            "authority_citations": sorted(self.authority_citations),
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# CycleCommitPayload / CycleStartPayload
# ---------------------------------------------------------------------------

@dataclass
class CycleCommitPayload:
    """Canonical payload signed at end of cycle by active sovereign."""
    cycle_id: int
    kernel_version_id: str
    state_hash_end: str
    state_hash_prev: str
    constitution_hash_tip: str
    pending_successor_key: Optional[str]
    identity_chain_length: int
    identity_chain_tip_hash: str
    overlay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "CycleCommit",
            "cycle_id": self.cycle_id,
            "kernel_version_id": self.kernel_version_id,
            "state_hash_end": self.state_hash_end,
            "state_hash_prev": self.state_hash_prev,
            "constitution_hash_tip": self.constitution_hash_tip,
            "pending_successor_key": self.pending_successor_key,
            "identity_chain_length": self.identity_chain_length,
            "identity_chain_tip_hash": self.identity_chain_tip_hash,
            "overlay_hash": self.overlay_hash,
        }


@dataclass
class CycleStartPayload:
    """Canonical payload signed at start of cycle by derived active sovereign."""
    cycle_id: int
    kernel_version_id: str
    state_hash_prev: str
    sovereign_public_key_active: str
    identity_chain_length: int
    identity_chain_tip_hash: str
    overlay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "CycleStart",
            "cycle_id": self.cycle_id,
            "kernel_version_id": self.kernel_version_id,
            "state_hash_prev": self.state_hash_prev,
            "sovereign_public_key_active": self.sovereign_public_key_active,
            "identity_chain_length": self.identity_chain_length,
            "identity_chain_tip_hash": self.identity_chain_tip_hash,
            "overlay_hash": self.overlay_hash,
        }


# ---------------------------------------------------------------------------
# Succession Trace Events
# ---------------------------------------------------------------------------

@dataclass
class SuccessionAdmissionEvent:
    """Trace event for succession admission pipeline."""
    artifact_id: str
    gate: str
    result: str  # "pass" | "fail"
    reason_code: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "event_type": "succession_admission_event",
            "artifact_id": self.artifact_id,
            "gate": self.gate,
            "result": self.result,
        }
        if self.reason_code:
            d["reason_code"] = self.reason_code
        if self.detail:
            d["detail"] = self.detail
        return d


@dataclass
class SuccessionAdmissionRecord:
    """Result of succession proposal admission."""
    proposal_id: str
    admitted: bool
    is_self_succession: bool = False
    events: List[SuccessionAdmissionEvent] = field(default_factory=list)
    failed_gate: str = ""
    rejection_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "admitted": self.admitted,
            "is_self_succession": self.is_self_succession,
            "events": [e.to_dict() for e in self.events],
            "failed_gate": self.failed_gate,
            "rejection_code": self.rejection_code,
        }


@dataclass
class SuccessionRejectionRecord:
    """Record for a rejected succession proposal."""
    proposal_id: str
    rejection_code: str
    failed_gate: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "rejection_code": self.rejection_code,
            "failed_gate": self.failed_gate,
            "detail": self.detail,
        }


# ---------------------------------------------------------------------------
# Ratification Trace Events
# ---------------------------------------------------------------------------

@dataclass
class RatificationAdmissionRecord:
    """Result of treaty ratification admission."""
    ratification_id: str
    treaty_id: str
    ratify: bool
    admitted: bool
    events: List[Dict[str, Any]] = field(default_factory=list)
    failed_gate: str = ""
    rejection_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ratification_id": self.ratification_id,
            "treaty_id": self.treaty_id,
            "ratify": self.ratify,
            "admitted": self.admitted,
            "events": self.events,
            "failed_gate": self.failed_gate,
            "rejection_code": self.rejection_code,
        }


@dataclass
class RatificationRejectionRecord:
    """Record for a rejected ratification."""
    ratification_id: str
    treaty_id: str
    rejection_code: str
    failed_gate: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ratification_id": self.ratification_id,
            "treaty_id": self.treaty_id,
            "rejection_code": self.rejection_code,
            "failed_gate": self.failed_gate,
            "detail": self.detail,
        }


# ---------------------------------------------------------------------------
# Active Treaty Set X-3 Extension
# ---------------------------------------------------------------------------

@dataclass
class ActiveTreatySetX3(ActiveTreatySet):
    """Extends ActiveTreatySet with suspension tracking for X-3."""
    suspended_grant_ids: set = field(default_factory=set)

    def active_grants(self, current_cycle: int) -> List[TreatyGrant]:
        """Return grants that are active, not revoked, not invalidated,
        and not suspended."""
        return [
            g for g in self.grants
            if g.is_active(current_cycle)
            and g.id not in self.revoked_grant_ids
            and g.id not in self.invalidated_grant_ids
            and g.id not in self.suspended_grant_ids
        ]

    def suspended_grants(self, current_cycle: int) -> List[TreatyGrant]:
        """Return grants that are suspended (not expired, not revoked)."""
        return [
            g for g in self.grants
            if g.is_active(current_cycle)
            and g.id not in self.revoked_grant_ids
            and g.id not in self.invalidated_grant_ids
            and g.id in self.suspended_grant_ids
        ]

    def suspend_all_active(self, current_cycle: int) -> List[str]:
        """Move all currently ACTIVE grants to SUSPENDED.
        Returns list of newly suspended grant IDs."""
        active = super().active_grants(current_cycle)
        # Use parent's active_grants to get truly active ones
        # (not already suspended)
        newly_suspended = []
        for g in active:
            if g.id not in self.suspended_grant_ids:
                self.suspended_grant_ids.add(g.id)
                newly_suspended.append(g.id)
        return newly_suspended

    def ratify(self, grant_id: str) -> bool:
        """Restore a suspended grant to ACTIVE. Returns True if found."""
        if grant_id in self.suspended_grant_ids:
            self.suspended_grant_ids.discard(grant_id)
            return True
        return False

    def reject_ratification(self, grant_id: str) -> bool:
        """Revoke a suspended grant (ratify=false). Returns True if found."""
        if grant_id in self.suspended_grant_ids:
            self.suspended_grant_ids.discard(grant_id)
            self.revoked_grant_ids.add(grant_id)
            return True
        return False

    def has_suspensions(self) -> bool:
        """True if any grants are currently suspended."""
        return len(self.suspended_grant_ids) > 0

    def prune_expired_suspensions(self, current_cycle: int) -> List[str]:
        """Remove expired grants from suspended set.
        Returns list of removed grant IDs."""
        to_remove = []
        for gid in list(self.suspended_grant_ids):
            grant = self.find_grant(gid)
            if grant is None or not grant.is_active(current_cycle):
                to_remove.append(gid)
        for gid in to_remove:
            self.suspended_grant_ids.discard(gid)
        return to_remove


# ---------------------------------------------------------------------------
# Extended Internal State (X-3)
# ---------------------------------------------------------------------------

@dataclass
class InternalStateX3(InternalStateX2):
    """Extended internal state for X-3 with sovereign lineage tracking."""
    # Sovereign identity
    sovereign_public_key_active: str = ""
    prior_sovereign_public_key: Optional[str] = None
    pending_successor_key: Optional[str] = None

    # Lineage chain
    identity_chain_length: int = 1
    identity_chain_tip_hash: str = ""
    historical_sovereign_keys: set = field(default_factory=set)

    # Overlay
    overlay_hash: str = ""

    # Override parent's ActiveTreatySet with X-3 version
    active_treaty_set: ActiveTreatySetX3 = field(default_factory=ActiveTreatySetX3)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["sovereign_public_key_active"] = self.sovereign_public_key_active
        d["prior_sovereign_public_key"] = self.prior_sovereign_public_key
        d["pending_successor_key"] = self.pending_successor_key
        d["identity_chain_length"] = self.identity_chain_length
        d["identity_chain_tip_hash"] = self.identity_chain_tip_hash
        d["historical_sovereign_keys"] = sorted(self.historical_sovereign_keys)
        d["overlay_hash"] = self.overlay_hash
        d["suspended_grant_ids"] = sorted(self.active_treaty_set.suspended_grant_ids)
        return d

    def advance(self, decision_type: str) -> "InternalStateX3":
        return InternalStateX3(
            cycle_index=self.cycle_index + 1,
            last_decision=decision_type,
            active_constitution_hash=self.active_constitution_hash,
            pending_amendments=list(self.pending_amendments),
            decision_type_history=self.decision_type_history + [decision_type],
            active_treaty_set=self.active_treaty_set,
            sovereign_public_key_active=self.sovereign_public_key_active,
            prior_sovereign_public_key=self.prior_sovereign_public_key,
            pending_successor_key=self.pending_successor_key,
            identity_chain_length=self.identity_chain_length,
            identity_chain_tip_hash=self.identity_chain_tip_hash,
            historical_sovereign_keys=set(self.historical_sovereign_keys),
            overlay_hash=self.overlay_hash,
        )


# ---------------------------------------------------------------------------
# Identity Chain Hash Computation
# ---------------------------------------------------------------------------

def compute_identity_chain_tip_hash(
    chain_length: int,
    active_key: str,
    prior_tip_hash: str,
    succession_proposal_hash: str,
) -> str:
    """Compute identity_chain_tip_hash per AE1 binding definition.

    tip_hash = SHA256(JCS({
        type: "identity_chain_tip",
        chain_length: <int>,
        active_key: <str>,
        prior_tip_hash: <str>,
        succession_proposal_hash: <str>
    }))
    """
    payload = {
        "type": "identity_chain_tip",
        "chain_length": chain_length,
        "active_key": active_key,
        "prior_tip_hash": prior_tip_hash,
        "succession_proposal_hash": succession_proposal_hash,
    }
    return hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()


def compute_genesis_tip_hash(genesis_artifact_dict: Dict[str, Any]) -> str:
    """Compute genesis identity_chain_tip_hash = SHA256(JCS(genesis_artifact))."""
    return hashlib.sha256(
        canonical_json_bytes(genesis_artifact_dict)
    ).hexdigest()


# ---------------------------------------------------------------------------
# PolicyOutputX3
# ---------------------------------------------------------------------------

@dataclass
class PolicyOutputX3:
    """Output of policy_core_x3. Extends X-2 output with succession
    and ratification fields."""
    decision_type: str = DecisionTypeX3.REFUSE

    # From X-2
    warrant: Optional[Any] = None
    warrants: List[Any] = field(default_factory=list)
    bundles: List[Any] = field(default_factory=list)
    refusal: Optional[Any] = None
    exit_record: Optional[Any] = None
    admission_events: List[Any] = field(default_factory=list)
    selection_event: Optional[Any] = None
    bundle: Optional[Any] = None
    admitted: List[Any] = field(default_factory=list)
    rejected: List[Any] = field(default_factory=list)

    # X-2 treaty fields
    treaty_grants_admitted: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_grants_rejected: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_revocations_admitted: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_revocations_rejected: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_admission_events: List[TreatyAdmissionEvent] = field(default_factory=list)
    revalidation_events: List[TreatyRevalidationEvent] = field(default_factory=list)
    delegated_warrants: List[Any] = field(default_factory=list)
    delegated_rejections: List[Any] = field(default_factory=list)

    # X-1 amendment fields
    adoption_record: Optional[Any] = None
    queued_proposal: Optional[Any] = None
    state_delta: Optional[StateDelta] = None
    amendment_admission_events: List[Any] = field(default_factory=list)

    # X-3 succession fields
    succession_admission: Optional[SuccessionAdmissionRecord] = None
    succession_rejections: List[SuccessionRejectionRecord] = field(default_factory=list)

    # X-3 ratification fields
    ratification_admissions: List[RatificationAdmissionRecord] = field(default_factory=list)
    ratification_rejections: List[RatificationRejectionRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"decision_type": self.decision_type}
        if self.succession_admission:
            d["succession_admission"] = self.succession_admission.to_dict()
        if self.succession_rejections:
            d["succession_rejections"] = [r.to_dict() for r in self.succession_rejections]
        if self.ratification_admissions:
            d["ratification_admissions"] = [r.to_dict() for r in self.ratification_admissions]
        if self.ratification_rejections:
            d["ratification_rejections"] = [r.to_dict() for r in self.ratification_rejections]
        return d
