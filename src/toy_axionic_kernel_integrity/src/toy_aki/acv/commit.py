"""
ACV Commitment: Agent-side commitment generation.

The commit phase produces C = HMAC(kernel_public_key, P || nonce)
where P is the proposal and nonce is agent-generated randomness.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

from toy_aki.common.hashing import (
    sha256_hex,
    hmac_sha256_hex,
    canonical_json_bytes,
    compute_proposal_hash,
    compute_trace_commit,
)
from toy_aki.common.no_floats import assert_no_floats


@dataclass
class Commitment:
    """
    ACV commitment object.

    Contains the commitment hash and the information needed
    to verify it during the reveal phase.
    """
    commitment: str  # HMAC(kernel_public_key, P || nonce)
    nonce: str  # 32-byte nonce as hex (64 chars)
    nonce_ref: str  # Reference ID for audit correlation
    proposal_hash: str  # Hash of the proposal being committed
    timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "commitment": self.commitment,
            "nonce": self.nonce,
            "nonce_ref": self.nonce_ref,
            "proposal_hash": self.proposal_hash,
            "timestamp_ms": self.timestamp_ms,
        }


def generate_nonce() -> str:
    """Generate a cryptographically secure 32-byte nonce as hex."""
    return os.urandom(32).hex()


def generate_nonce_ref() -> str:
    """Generate a unique nonce reference for audit correlation."""
    return f"nonce-{uuid.uuid4()}"


def compute_commitment(
    proposal: dict[str, Any],
    nonce: str,
    kernel_public_key: str,
) -> str:
    """
    Compute ACV commitment: C = HMAC(kernel_public_key, P || nonce).

    Args:
        proposal: The proposal object (must not contain floats)
        nonce: 32-byte nonce as hex string
        kernel_public_key: Kernel's public key for HMAC

    Returns:
        Commitment hash as hex string
    """
    # Ensure proposal has no floats
    assert_no_floats(proposal)

    # Serialize proposal and concatenate with nonce
    proposal_bytes = canonical_json_bytes(proposal)
    nonce_bytes = bytes.fromhex(nonce)
    message = proposal_bytes + nonce_bytes

    # Convert key to bytes if it's a hex string, otherwise encode
    if len(kernel_public_key) == 64:
        try:
            key_bytes = bytes.fromhex(kernel_public_key)
        except ValueError:
            key_bytes = kernel_public_key.encode("utf-8")
    else:
        key_bytes = kernel_public_key.encode("utf-8")

    # Compute HMAC
    return hmac_sha256_hex(key_bytes, message)


def create_commitment(
    proposal: dict[str, Any],
    kernel_public_key: str,
    timestamp_ms: int,
    nonce: str | None = None,
) -> Commitment:
    """
    Create a full commitment object for a proposal.

    Args:
        proposal: The proposal to commit to
        kernel_public_key: Kernel's public key
        timestamp_ms: Current timestamp in milliseconds
        nonce: Optional pre-generated nonce (for testing)

    Returns:
        Commitment object with all fields populated
    """
    # Generate nonce if not provided
    if nonce is None:
        nonce = generate_nonce()

    # Compute proposal hash
    proposal_hash = compute_proposal_hash(proposal)

    # Compute commitment
    commitment_hash = compute_commitment(proposal, nonce, kernel_public_key)

    return Commitment(
        commitment=commitment_hash,
        nonce=nonce,
        nonce_ref=generate_nonce_ref(),
        proposal_hash=proposal_hash,
        timestamp_ms=timestamp_ms,
    )


def verify_commitment_format(commitment: Commitment) -> bool:
    """
    Verify that a commitment object has valid format.

    This checks structural validity, not cryptographic validity.
    """
    # Check nonce is 64 hex chars (32 bytes)
    if len(commitment.nonce) != 64:
        return False
    try:
        bytes.fromhex(commitment.nonce)
    except ValueError:
        return False

    # Check commitment is 64 hex chars
    if len(commitment.commitment) != 64:
        return False
    try:
        bytes.fromhex(commitment.commitment)
    except ValueError:
        return False

    # Check proposal hash
    if len(commitment.proposal_hash) != 64:
        return False

    return True
