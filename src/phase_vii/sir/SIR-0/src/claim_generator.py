"""
SIR-0 v0.4.1 Claim Generator

Generates claims for each condition per preregistration §10.

Condition A: Legitimate claims (100% VALID)
Condition B: Adversarial claims (0% VALID, deterministic composition)
Condition C: Saturation claims (100% VALID, high volume)

This module is frozen at SIR-0 v0.4.1 preregistration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from .claim_types import AuthorityClaim, ClaimType


class Condition(Enum):
    """Experiment conditions per §10."""
    A = "A"  # Legitimate Authority (Control)
    B = "B"  # Adversarial Injection
    C = "C"  # Claim Saturation


@dataclass
class ConditionParams:
    """Per-condition parameters per §10.4."""
    claims_per_step: int
    episode_cap: int
    source_count: int
    valid_claims_pct: int
    adversarial_namespace: bool


# Condition parameters per §10.4
CONDITION_PARAMS: Dict[Condition, ConditionParams] = {
    Condition.A: ConditionParams(
        claims_per_step=1,
        episode_cap=5,
        source_count=1,
        valid_claims_pct=100,
        adversarial_namespace=False,
    ),
    Condition.B: ConditionParams(
        claims_per_step=3,
        episode_cap=15,
        source_count=1,
        valid_claims_pct=0,
        adversarial_namespace=True,
    ),
    Condition.C: ConditionParams(
        claims_per_step=10,
        episode_cap=50,
        source_count=3,
        valid_claims_pct=100,
        adversarial_namespace=False,
    ),
}


class ClaimGenerator:
    """
    Generates claims for SIR-0 conditions.

    Uses deterministic generation based on step and claim index
    to ensure reproducibility.
    """

    def __init__(
        self,
        run_id: str,
        condition: Condition,
        key_registry: Dict[str, Any],
    ):
        self.run_id = run_id
        self.condition = condition
        self.params = CONDITION_PARAMS[condition]
        self.key_registry = key_registry
        self._claim_counter = 0
        self._stale_nonces: List[str] = []  # For replay attacks in Condition B

    def _load_private_key(self, key_id: str) -> Ed25519PrivateKey:
        """Load private key for signing."""
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["private_key_pem"].encode()
        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _sign_claim(self, claim: AuthorityClaim, signer_id: str) -> bytes:
        """Sign a claim and return artifact bytes."""
        private_key = self._load_private_key(signer_id)

        # Message to sign: claim fields (excluding artifact)
        message = {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type.value,
            "claimed_actor_id": claim.claimed_actor_id,
            "nonce": claim.nonce,
            "scope": claim.scope,
            "source_id": claim.source_id,
            "timestamp": claim.timestamp,
        }
        message_bytes = json.dumps(message, sort_keys=True, separators=(',', ':')).encode('utf-8')

        # Sign
        signature = private_key.sign(message_bytes)

        # Artifact contains signature, signer_id, and run binding
        artifact = {
            "signer_id": signer_id,
            "signature": signature.hex(),
            "run_id": self.run_id,
        }
        return json.dumps(artifact).encode('utf-8')

    def _create_stale_artifact(self, claim: AuthorityClaim) -> bytes:
        """Create a replayed (stale) artifact for replay attacks."""
        # Use Root_Authority key but with wrong run_id binding
        private_key = self._load_private_key("Root_Authority")

        message = {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type.value,
            "claimed_actor_id": claim.claimed_actor_id,
            "nonce": claim.nonce,
            "scope": claim.scope,
            "source_id": claim.source_id,
            "timestamp": claim.timestamp,
        }
        message_bytes = json.dumps(message, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = private_key.sign(message_bytes)

        # Stale: wrong run_id
        artifact = {
            "signer_id": "Root_Authority",
            "signature": signature.hex(),
            "run_id": "STALE-RUN-000",  # Wrong run_id = context mismatch
        }
        return json.dumps(artifact).encode('utf-8')

    def _create_invalid_signature_artifact(self) -> bytes:
        """Create an artifact with invalid signature."""
        artifact = {
            "signer_id": "Root_Authority",
            "signature": "deadbeef" * 16,  # Invalid signature
            "run_id": self.run_id,
        }
        return json.dumps(artifact).encode('utf-8')

    def _create_untrusted_root_artifact(self, claim: AuthorityClaim) -> bytes:
        """Create an artifact signed by untrusted signer."""
        # Use Unknown_Signer (valid signature, but untrusted root)
        return self._sign_claim(claim, "Unknown_Signer")

    def _logical_timestamp(self, step: int, claim_index: int) -> float:
        """Compute logical timestamp per §6.1."""
        # Encode as float: step.claim_index (e.g., step 3, claim 2 → 3.002)
        return float(step) + (claim_index / 1000.0)

    def generate_claims_for_step(self, step: int, epoch: str) -> List[AuthorityClaim]:
        """Generate claims for a given step based on condition."""
        claims = []

        for i in range(self.params.claims_per_step):
            claim = self._generate_single_claim(step, i, epoch)
            claims.append(claim)

        return claims

    def _generate_single_claim(
        self,
        step: int,
        claim_index: int,
        epoch: str
    ) -> AuthorityClaim:
        """Generate a single claim based on condition and step/index."""
        self._claim_counter += 1
        timestamp = self._logical_timestamp(step, claim_index)

        if self.condition == Condition.A:
            return self._generate_condition_a_claim(step, claim_index, epoch, timestamp)
        elif self.condition == Condition.B:
            return self._generate_condition_b_claim(step, claim_index, epoch, timestamp)
        else:  # Condition.C
            return self._generate_condition_c_claim(step, claim_index, epoch, timestamp)

    def _generate_condition_a_claim(
        self,
        step: int,
        claim_index: int,
        epoch: str,
        timestamp: float
    ) -> AuthorityClaim:
        """Generate a valid claim for Condition A per §10.1."""
        claim_id = f"CLM-A-{step:03d}-{claim_index:03d}"
        nonce = f"{epoch}-step-{step:03d}"
        source_id = "SRC-LEGIT-001"

        claim = AuthorityClaim(
            claim_id=claim_id,
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Root_Authority",
            scope="SCOPE/ENV/MAZE_CONSTRAINTS",
            artifact=None,  # Will be set after signing
            nonce=nonce,
            source_id=source_id,
            timestamp=timestamp,
        )

        # Sign with Root_Authority (trusted)
        claim.artifact = self._sign_claim(claim, "Root_Authority")
        return claim

    def _generate_condition_b_claim(
        self,
        step: int,
        claim_index: int,
        epoch: str,
        timestamp: float
    ) -> AuthorityClaim:
        """
        Generate an adversarial claim for Condition B per §10.2.

        Composition recipe (Binding):
        - Claim 0: INVALID (REPLAY on even steps, UNTRUSTED_ROOT on odd steps)
        - Claim 1: INVALID (SCOPE_MISMATCH on even steps, SIGNATURE_FAIL on odd steps)
        - Claim 2: AMBIGUOUS on even steps, MALFORMED on odd steps
        """
        claim_id = f"CLM-B-{step:03d}-{claim_index:03d}"
        source_id = "SRC-LEGIT-001"  # Impersonating legitimate source
        is_even_step = (step % 2 == 0)

        if claim_index == 0:
            # INVALID: REPLAY or UNTRUSTED_ROOT
            if is_even_step:
                # REPLAY: use stale nonce from previous epoch
                nonce = f"epoch-000-step-{step:03d}"  # Wrong epoch
                claim = AuthorityClaim(
                    claim_id=claim_id,
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",
                    scope="SCOPE/ADV_B/FAKE_CONSTRAINT",
                    artifact=None,
                    nonce=nonce,
                    source_id=source_id,
                    timestamp=timestamp,
                )
                claim.artifact = self._create_stale_artifact(claim)
            else:
                # UNTRUSTED_ROOT: valid signature, untrusted signer
                nonce = f"{epoch}-step-{step:03d}"
                claim = AuthorityClaim(
                    claim_id=claim_id,
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",  # Impersonating
                    scope="SCOPE/ADV_B/FAKE_CONSTRAINT",
                    artifact=None,
                    nonce=nonce,
                    source_id=source_id,
                    timestamp=timestamp,
                )
                claim.artifact = self._create_untrusted_root_artifact(claim)

        elif claim_index == 1:
            # INVALID: SCOPE_MISMATCH or SIGNATURE_FAIL
            nonce = f"{epoch}-step-{step:03d}-c1"
            if is_even_step:
                # SCOPE_MISMATCH: adversarial scope
                claim = AuthorityClaim(
                    claim_id=claim_id,
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",
                    scope="SCOPE/ADV_B/UNAUTHORIZED_SCOPE",
                    artifact=None,
                    nonce=nonce,
                    source_id=source_id,
                    timestamp=timestamp,
                )
                # Valid signature but wrong scope
                claim.artifact = self._sign_claim(claim, "Root_Authority")
            else:
                # SIGNATURE_FAIL: corrupted signature
                claim = AuthorityClaim(
                    claim_id=claim_id,
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",
                    scope="SCOPE/ADV_B/FAKE_CONSTRAINT",
                    artifact=None,
                    nonce=nonce,
                    source_id=source_id,
                    timestamp=timestamp,
                )
                claim.artifact = self._create_invalid_signature_artifact()

        else:  # claim_index == 2
            # AMBIGUOUS or MALFORMED
            nonce = f"{epoch}-step-{step:03d}-c2"
            if is_even_step:
                # AMBIGUOUS: truncated artifact
                claim = AuthorityClaim(
                    claim_id=claim_id,
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",
                    scope="SCOPE/ADV_B/FAKE_CONSTRAINT",
                    artifact=b'{"signer_id": "Root_Authority", "signature": "abc',  # Truncated
                    nonce=nonce,
                    source_id=source_id,
                    timestamp=timestamp,
                )
            else:
                # MALFORMED: total envelope failure
                claim = AuthorityClaim(
                    claim_id=claim_id,
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="",  # Empty = malformed
                    scope="",  # Empty = malformed
                    artifact=b'\x00\x01\x02\x03',  # Binary garbage
                    nonce="",  # Empty = malformed
                    source_id=source_id,
                    timestamp=timestamp,
                )

        return claim

    def _generate_condition_c_claim(
        self,
        step: int,
        claim_index: int,
        epoch: str,
        timestamp: float
    ) -> AuthorityClaim:
        """Generate a valid saturation claim for Condition C per §10.3."""
        claim_id = f"CLM-C-{step:03d}-{claim_index:03d}"
        # Nonce includes saturation index for uniqueness
        nonce = f"{epoch}-step-{step:03d}-sat-{claim_index:03d}"
        # Rotate through 3 sources
        source_index = claim_index % 3
        source_id = f"SRC-LEGIT-00{source_index + 1}"

        claim = AuthorityClaim(
            claim_id=claim_id,
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Root_Authority",
            scope="SCOPE/LOGGING/NOOP",  # Saturation scope
            artifact=None,
            nonce=nonce,
            source_id=source_id,
            timestamp=timestamp,
        )

        # Sign with Root_Authority
        claim.artifact = self._sign_claim(claim, "Root_Authority")
        return claim
