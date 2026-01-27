"""
SIR-0 v0.4.1 Claim Schema and Types

Implements AuthorityClaim per preregistration §6.1 and classification
types per §7.1-§7.4.

This module is frozen at SIR-0 v0.4.1 preregistration.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List, Dict, Any


# ============================================================================
# §6.2 Claim Types
# ============================================================================

class ClaimType(Enum):
    """Claim types per §6.2."""
    COMMAND = "COMMAND"
    POLICY_UPDATE = "POLICY_UPDATE"


# ============================================================================
# §7.1 Classification Categories
# ============================================================================

class ClaimClassification(Enum):
    """Classification categories per §7.1."""
    VALID_AUTHORITY_CLAIM = "VALID_AUTHORITY_CLAIM"
    INVALID_AUTHORITY_CLAIM = "INVALID_AUTHORITY_CLAIM"
    AMBIGUOUS_AUTHORITY_CLAIM = "AMBIGUOUS_AUTHORITY_CLAIM"
    MALFORMED_AUTHORITY_CLAIM = "MALFORMED_AUTHORITY_CLAIM"


# ============================================================================
# §7.3 Ambiguity Subtypes
# ============================================================================

class AmbiguitySubtype(Enum):
    """Ambiguity subtypes per §7.3."""
    AMBIG_TRUNCATED_ARTIFACT = "AMBIG_TRUNCATED_ARTIFACT"
    AMBIG_PROVENANCE_COLLISION = "AMBIG_PROVENANCE_COLLISION"
    AMBIG_PARTIAL_DECODE = "AMBIG_PARTIAL_DECODE"


# ============================================================================
# §7.4 Invalid Reason Codes
# ============================================================================

class InvalidReason(Enum):
    """Invalid reason codes per §7.4."""
    SIGNATURE_FAIL = "SIGNATURE_FAIL"
    UNTRUSTED_ROOT = "UNTRUSTED_ROOT"
    REPLAY = "REPLAY"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"


# ============================================================================
# §9.1 Gate Effects
# ============================================================================

class GateEffect(Enum):
    """Permitted gate effects per §9.1."""
    ACTION_MASK = "ACTION_MASK"
    HALT_REFUSAL = "HALT_REFUSAL"
    NO_EFFECT = "NO_EFFECT"


# ============================================================================
# §11.1 Responsibility Actor
# ============================================================================

class ResponsibilityActor(Enum):
    """Responsibility actor categories per §11.1."""
    LEGITIMATE_AUTHORITY = "LEGITIMATE_AUTHORITY"
    SYSTEM_AUTHORITY = "SYSTEM_AUTHORITY"
    NONE = "NONE"


# ============================================================================
# §11.3 Claim Attribution
# ============================================================================

class ClaimAttribution(Enum):
    """Claim attribution for logging per §11.3."""
    LEGITIMATE_SOURCE = "LEGITIMATE_SOURCE"
    ADVERSARY_SOURCE = "ADVERSARY_SOURCE"


# ============================================================================
# §6.1 Authority Claim
# ============================================================================

@dataclass
class AuthorityClaim:
    """
    Authority claim per §6.1.

    Fields:
        claim_id: Unique identifier
        claim_type: COMMAND or POLICY_UPDATE
        claimed_actor_id: Who claims authority
        scope: Namespace-qualified scope
        artifact: Optional provenance certificate (base64 if provided)
        nonce: Freshness field
        source_id: Transport source identifier
        timestamp: Logical clock (run_id, step, claim_index)
    """
    claim_id: str
    claim_type: ClaimType
    claimed_actor_id: str
    scope: str
    artifact: Optional[bytes]
    nonce: str
    source_id: str
    timestamp: float  # Logical clock

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary with artifact base64-encoded."""
        return {
            "artifact": base64.b64encode(self.artifact).decode() if self.artifact else None,
            "claim_id": self.claim_id,
            "claim_type": self.claim_type.value,
            "claimed_actor_id": self.claimed_actor_id,
            "nonce": self.nonce,
            "scope": self.scope,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
        }

    def canonical_bytes(self) -> bytes:
        """
        Per §8.1: Canonical byte representation for taint_id computation.

        RFC 8785 JSON canonical form: sorted keys, no whitespace, stable floats.
        """
        d = self.to_dict()
        # JSON canonical form per RFC 8785
        return json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def taint_id(self) -> str:
        """Per §8.1: taint_id = SHA256(canonical(claim))."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest().lower()


# ============================================================================
# Classification Result
# ============================================================================

@dataclass
class ClassificationResult:
    """Result of claim classification."""
    classification: ClaimClassification
    reason: Optional[InvalidReason] = None  # For INVALID
    subtype: Optional[AmbiguitySubtype] = None  # For AMBIGUOUS
    claim_attribution: ClaimAttribution = ClaimAttribution.LEGITIMATE_SOURCE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification.value,
            "reason": self.reason.value if self.reason else None,
            "subtype": self.subtype.value if self.subtype else None,
            "claim_attribution": self.claim_attribution.value,
        }


# ============================================================================
# §8.3 Derivation Entry
# ============================================================================

@dataclass
class DerivationEntry:
    """Per §8.3: Entry in L_DerivationLedger."""
    claim_id: str
    claim_taint_id: str
    classification: ClaimClassification
    derived_gate_effect: GateEffect
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_taint_id": self.claim_taint_id,
            "classification": self.classification.value,
            "derived_gate_effect": self.derived_gate_effect.value,
            "timestamp": self.timestamp,
        }


# ============================================================================
# §8.3 L_DerivationLedger
# ============================================================================

@dataclass
class L_DerivationLedger:
    """Per §8.3: Per-step derivation ledger."""
    step: int
    entries: List[DerivationEntry]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "entries": [e.to_dict() for e in self.entries],
        }


# ============================================================================
# §8.2 JustifyInputManifest
# ============================================================================

@dataclass
class JustifyInputManifest:
    """Per §8.2: Per-step input manifest."""
    step: int
    observation_hash: str
    gate_metadata_hash: Optional[str]
    raw_claims_passed: bool  # MUST be False per §8.2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "observation_hash": self.observation_hash,
            "gate_metadata_hash": self.gate_metadata_hash,
            "raw_claims_passed": self.raw_claims_passed,
        }
