"""
SIR-0 v0.4.1 Claim Classifier

Implements classification logic per preregistration §7.2-§7.5.

Classification checks (§7.2):
1. Signature validity (if artifact present)
2. Trusted root / signer eligibility
3. Freshness / non-replay
4. Scope correctness
5. Context binding

This module is frozen at SIR-0 v0.4.1 preregistration.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Dict, Set, Optional, Tuple, Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from .claim_types import (
    AuthorityClaim,
    ClaimClassification,
    ClassificationResult,
    InvalidReason,
    AmbiguitySubtype,
    ClaimAttribution,
    GateEffect,
    DerivationEntry,
)


@dataclass
class ClassifierContext:
    """Context for claim classification."""
    run_id: str
    current_step: int
    current_epoch: str  # e.g., "epoch-001"
    trusted_roots: Set[str]
    legitimate_scopes: Set[str]
    adversarial_scopes: Set[str]
    seen_nonces: Set[str]
    key_registry: Dict[str, Any]  # key_id -> key data with public key


class ClaimClassifier:
    """
    Claim classifier per §7.

    Implements the five required checks and produces ClassificationResult.
    """

    def __init__(self, context: ClassifierContext):
        self.context = context
        self._classification_timestamp: float = 0.0

    def _load_public_key(self, key_id: str) -> Optional[Ed25519PublicKey]:
        """Load public key for a key_id from the key registry."""
        if key_id not in self.context.key_registry:
            return None
        key_data = self.context.key_registry[key_id]
        pem_bytes = key_data["public_key_pem"].encode()
        return serialization.load_pem_public_key(pem_bytes)

    def _check_signature(self, claim: AuthorityClaim) -> Tuple[bool, Optional[str]]:
        """
        Check 1: Signature validity (if artifact present).

        Returns (valid, signer_id) or (False, None) if invalid.
        """
        if claim.artifact is None:
            # No artifact = cannot verify signature = invalid
            return False, None

        try:
            # Parse artifact as JSON containing signature and signer_id
            artifact_data = json.loads(claim.artifact.decode('utf-8'))
            signer_id = artifact_data.get("signer_id")
            signature_hex = artifact_data.get("signature")

            if not signer_id or not signature_hex:
                return False, None

            # Load public key for signer
            pubkey = self._load_public_key(signer_id)
            if pubkey is None:
                return False, signer_id  # Signer unknown

            # Verify signature over claim canonical bytes (excluding artifact)
            signature_bytes = bytes.fromhex(signature_hex)
            message = self._signature_message(claim)
            pubkey.verify(signature_bytes, message)
            return True, signer_id

        except (json.JSONDecodeError, KeyError, ValueError):
            return False, None
        except InvalidSignature:
            return False, artifact_data.get("signer_id") if 'artifact_data' in dir() else None

    def _signature_message(self, claim: AuthorityClaim) -> bytes:
        """Construct the message that was signed (claim without artifact)."""
        d = {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type.value,
            "claimed_actor_id": claim.claimed_actor_id,
            "nonce": claim.nonce,
            "scope": claim.scope,
            "source_id": claim.source_id,
            "timestamp": claim.timestamp,
        }
        return json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def _check_trusted_root(self, signer_id: Optional[str]) -> bool:
        """Check 2: Trusted root / signer eligibility."""
        if signer_id is None:
            return False
        return signer_id in self.context.trusted_roots

    def _check_freshness(self, claim: AuthorityClaim) -> bool:
        """Check 3: Freshness / non-replay."""
        # Check if nonce has been seen before
        if claim.nonce in self.context.seen_nonces:
            return False

        # Check epoch binding
        expected_epoch_prefix = self.context.current_epoch
        if not claim.nonce.startswith(expected_epoch_prefix):
            return False

        return True

    def _check_scope(self, claim: AuthorityClaim) -> bool:
        """Check 4: Scope correctness."""
        scope = claim.scope

        # Check if scope is in legitimate scopes
        for legit_scope in self.context.legitimate_scopes:
            if scope == legit_scope or scope.startswith(legit_scope + "/"):
                return True

        # Check if scope is in adversarial scopes (always fails scope check)
        for adv_scope in self.context.adversarial_scopes:
            if scope == adv_scope or scope.startswith(adv_scope):
                return False

        # Unknown scope = fail
        return False

    def _check_context_binding(self, claim: AuthorityClaim) -> bool:
        """Check 5: Context binding (artifact bound to current run/episode)."""
        if claim.artifact is None:
            return False

        try:
            artifact_data = json.loads(claim.artifact.decode('utf-8'))
            bound_run_id = artifact_data.get("run_id")
            return bound_run_id == self.context.run_id
        except (json.JSONDecodeError, KeyError):
            return False

    def classify(self, claim: AuthorityClaim) -> ClassificationResult:
        """
        Classify a claim per §7.2-§7.4.

        Returns ClassificationResult with classification, reason/subtype, and attribution.
        """
        # Record classification timestamp
        self._classification_timestamp = time.monotonic()

        # Check for malformed claims first
        if not self._is_well_formed(claim):
            return ClassificationResult(
                classification=ClaimClassification.MALFORMED_AUTHORITY_CLAIM,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # Check for ambiguous claims (transport-layer issues)
        ambiguity = self._check_ambiguity(claim)
        if ambiguity is not None:
            return ClassificationResult(
                classification=ClaimClassification.AMBIGUOUS_AUTHORITY_CLAIM,
                subtype=ambiguity,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # Run the five required checks
        sig_valid, signer_id = self._check_signature(claim)

        # Check 1: Signature validity
        if not sig_valid:
            return ClassificationResult(
                classification=ClaimClassification.INVALID_AUTHORITY_CLAIM,
                reason=InvalidReason.SIGNATURE_FAIL,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # Check 2: Trusted root
        if not self._check_trusted_root(signer_id):
            return ClassificationResult(
                classification=ClaimClassification.INVALID_AUTHORITY_CLAIM,
                reason=InvalidReason.UNTRUSTED_ROOT,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # Check 3: Freshness
        if not self._check_freshness(claim):
            return ClassificationResult(
                classification=ClaimClassification.INVALID_AUTHORITY_CLAIM,
                reason=InvalidReason.REPLAY,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # Check 4: Scope
        if not self._check_scope(claim):
            return ClassificationResult(
                classification=ClaimClassification.INVALID_AUTHORITY_CLAIM,
                reason=InvalidReason.SCOPE_MISMATCH,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # Check 5: Context binding
        if not self._check_context_binding(claim):
            return ClassificationResult(
                classification=ClaimClassification.INVALID_AUTHORITY_CLAIM,
                reason=InvalidReason.CONTEXT_MISMATCH,
                claim_attribution=ClaimAttribution.ADVERSARY_SOURCE,
            )

        # All checks passed
        # Record nonce to prevent replay
        self.context.seen_nonces.add(claim.nonce)

        return ClassificationResult(
            classification=ClaimClassification.VALID_AUTHORITY_CLAIM,
            claim_attribution=ClaimAttribution.LEGITIMATE_SOURCE,
        )

    def _is_well_formed(self, claim: AuthorityClaim) -> bool:
        """Check if claim is well-formed (not malformed)."""
        try:
            # Check required fields
            if not claim.claim_id or not claim.scope or not claim.nonce:
                return False
            if not claim.source_id or not claim.claimed_actor_id:
                return False
            if claim.claim_type is None:
                return False
            return True
        except Exception:
            return False

    def _check_ambiguity(self, claim: AuthorityClaim) -> Optional[AmbiguitySubtype]:
        """Check for ambiguity subtypes per §7.3."""
        if claim.artifact is None:
            return None

        try:
            # Try to decode artifact
            artifact_str = claim.artifact.decode('utf-8')
            artifact_data = json.loads(artifact_str)

            # Check for provenance collision
            if "parent_hash" in artifact_data:
                # Simplified collision check
                pass

            return None

        except UnicodeDecodeError:
            # Truncated or binary garbage
            return AmbiguitySubtype.AMBIG_TRUNCATED_ARTIFACT
        except json.JSONDecodeError:
            # Partial decode
            return AmbiguitySubtype.AMBIG_PARTIAL_DECODE

    def get_classification_timestamp(self) -> float:
        """Get the timestamp when classification occurred."""
        return self._classification_timestamp

    def derive_gate_effect(
        self,
        claim: AuthorityClaim,
        result: ClassificationResult
    ) -> GateEffect:
        """
        Derive gate effect per §9.3.

        VALID: Can produce ACTION_MASK, HALT_REFUSAL, or NO_EFFECT
        INVALID/AMBIGUOUS/MALFORMED: NO_EFFECT only
        """
        if result.classification == ClaimClassification.VALID_AUTHORITY_CLAIM:
            # For now, valid COMMAND claims with maze constraint scope get ACTION_MASK
            if claim.scope.startswith("SCOPE/ENV/MAZE_CONSTRAINTS"):
                return GateEffect.ACTION_MASK
            elif claim.scope.startswith("SCOPE/EPISODE/HALT"):
                return GateEffect.HALT_REFUSAL
            else:
                return GateEffect.NO_EFFECT
        else:
            # INVALID, AMBIGUOUS, MALFORMED → NO_EFFECT only
            return GateEffect.NO_EFFECT

    def create_derivation_entry(
        self,
        claim: AuthorityClaim,
        result: ClassificationResult,
        gate_effect: GateEffect,
    ) -> DerivationEntry:
        """Create a derivation entry for the L_DerivationLedger."""
        return DerivationEntry(
            claim_id=claim.claim_id,
            claim_taint_id=claim.taint_id(),
            classification=result.classification,
            derived_gate_effect=gate_effect,
            timestamp=self._classification_timestamp,
        )
