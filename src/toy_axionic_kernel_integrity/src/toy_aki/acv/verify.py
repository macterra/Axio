"""
ACV Verification: Commitment verification during reveal phase.

Verifies that:
1. Revealed nonce matches commitment
2. Proposal matches commitment
3. Temporal ordering is correct (commit before anchor before reveal)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from toy_aki.common.hashing import hmac_sha256_hex, canonical_json_bytes
from toy_aki.common.no_floats import assert_no_floats

from toy_aki.acv.commit import Commitment
from toy_aki.acv.anchor import Anchor


@dataclass
class VerificationResult:
    """Result of ACV verification."""
    valid: bool
    commitment_matches: bool
    temporal_order_valid: bool
    nonce_valid: bool
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "valid": self.valid,
            "commitment_matches": self.commitment_matches,
            "temporal_order_valid": self.temporal_order_valid,
            "nonce_valid": self.nonce_valid,
            "error_message": self.error_message,
        }


def verify_commitment_reveal(
    proposal: dict[str, Any],
    commitment: Commitment,
    anchor: Anchor,
    revealed_nonce: str,
    kernel_public_key: str,
    reveal_timestamp_ms: int,
) -> VerificationResult:
    """
    Verify the full ACV reveal phase.

    Checks:
    1. Nonce format is valid
    2. Recomputed commitment matches original
    3. Temporal ordering: commit_ts < anchor_ts < reveal_ts

    Args:
        proposal: The revealed proposal
        commitment: The original commitment
        anchor: The kernel-issued anchor
        revealed_nonce: The revealed nonce
        kernel_public_key: Kernel's public key for HMAC
        reveal_timestamp_ms: Timestamp of reveal

    Returns:
        VerificationResult with all checks
    """
    # Check nonce format
    nonce_valid = True
    if len(revealed_nonce) != 64:
        nonce_valid = False
    else:
        try:
            bytes.fromhex(revealed_nonce)
        except ValueError:
            nonce_valid = False

    if not nonce_valid:
        return VerificationResult(
            valid=False,
            commitment_matches=False,
            temporal_order_valid=False,
            nonce_valid=False,
            error_message="Invalid nonce format",
        )

    # Check nonce matches commitment
    if revealed_nonce != commitment.nonce:
        return VerificationResult(
            valid=False,
            commitment_matches=False,
            temporal_order_valid=False,
            nonce_valid=False,
            error_message="Revealed nonce does not match commitment nonce",
        )

    # Verify proposal has no floats
    try:
        assert_no_floats(proposal)
    except Exception as e:
        return VerificationResult(
            valid=False,
            commitment_matches=False,
            temporal_order_valid=False,
            nonce_valid=True,
            error_message=f"Proposal contains invalid types: {e}",
        )

    # Recompute commitment
    proposal_bytes = canonical_json_bytes(proposal)
    nonce_bytes = bytes.fromhex(revealed_nonce)
    message = proposal_bytes + nonce_bytes
    recomputed = hmac_sha256_hex(kernel_public_key, message)

    commitment_matches = (recomputed == commitment.commitment)

    if not commitment_matches:
        return VerificationResult(
            valid=False,
            commitment_matches=False,
            temporal_order_valid=False,
            nonce_valid=True,
            error_message="Commitment verification failed - proposal may have been modified",
        )

    # Check temporal ordering
    temporal_order_valid = (
        commitment.timestamp_ms < anchor.timestamp_ms < reveal_timestamp_ms
    )

    if not temporal_order_valid:
        return VerificationResult(
            valid=False,
            commitment_matches=True,
            temporal_order_valid=False,
            nonce_valid=True,
            error_message=f"Temporal ordering violated: commit={commitment.timestamp_ms}, anchor={anchor.timestamp_ms}, reveal={reveal_timestamp_ms}",
        )

    return VerificationResult(
        valid=True,
        commitment_matches=True,
        temporal_order_valid=True,
        nonce_valid=True,
    )


def verify_commitment_only(
    proposal: dict[str, Any],
    commitment_hash: str,
    nonce: str,
    kernel_public_key: str,
) -> bool:
    """
    Verify just the commitment hash matches the proposal and nonce.

    This is a simpler verification without temporal checks.

    Args:
        proposal: The proposal to verify
        commitment_hash: The commitment hash to check against
        nonce: The nonce used in commitment
        kernel_public_key: Kernel's public key

    Returns:
        True if commitment is valid
    """
    try:
        assert_no_floats(proposal)
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

        recomputed = hmac_sha256_hex(key_bytes, message)
        return recomputed == commitment_hash
    except Exception:
        return False
