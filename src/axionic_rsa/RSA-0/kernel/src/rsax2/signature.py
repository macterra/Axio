"""
RSA X-2 — Ed25519 Signature Verification

Deterministic, replay-stable signature verification for delegated ActionRequests.
Uses PyCA cryptography library.

No external identity providers, no network calls, no time-based freshness.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
    Ed25519PrivateKey,
)
from cryptography.exceptions import InvalidSignature

from ..artifacts import canonical_json_bytes


# ---------------------------------------------------------------------------
# Key Helpers
# ---------------------------------------------------------------------------

def public_key_from_hex(hex_key: str) -> Ed25519PublicKey:
    """Load Ed25519 public key from 64-char hex string."""
    raw = bytes.fromhex(hex_key)
    if len(raw) != 32:
        raise ValueError(f"Ed25519 public key must be 32 bytes, got {len(raw)}")
    return Ed25519PublicKey.from_public_bytes(raw)


def extract_pubkey_hex(grantee_identifier: str) -> str:
    """Extract hex public key from 'ed25519:<hex64>' identifier."""
    if not grantee_identifier.startswith("ed25519:"):
        raise ValueError(f"Unsupported identifier scheme: {grantee_identifier}")
    return grantee_identifier[len("ed25519:"):]


# ---------------------------------------------------------------------------
# Signing (for test helpers)
# ---------------------------------------------------------------------------

def generate_keypair() -> Tuple[Ed25519PrivateKey, str]:
    """Generate an Ed25519 keypair. Returns (private_key, grantee_identifier)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_hex = public_key.public_bytes_raw().hex()
    grantee_id = f"ed25519:{pub_hex}"
    return private_key, grantee_id


def sign_action_request(
    private_key: Ed25519PrivateKey,
    action_request_dict: Dict[str, Any],
) -> str:
    """
    Sign an ActionRequest dict (excluding the signature field).
    Returns hex-encoded signature.
    """
    # Remove signature field if present
    payload = {k: v for k, v in action_request_dict.items() if k != "signature"}
    payload_bytes = canonical_json_bytes(payload)
    signature = private_key.sign(payload_bytes)
    return signature.hex()


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_action_request_signature(
    grantee_identifier: str,
    action_request_dict: Dict[str, Any],
    signature_hex: str,
) -> Tuple[bool, str]:
    """
    Verify Ed25519 signature on an ActionRequest.

    Args:
        grantee_identifier: "ed25519:<hex64>" identifier
        action_request_dict: the full ActionRequest dict (signature field excluded for verification)
        signature_hex: hex-encoded Ed25519 signature

    Returns:
        (valid, error_message)
    """
    try:
        pub_hex = extract_pubkey_hex(grantee_identifier)
        public_key = public_key_from_hex(pub_hex)
    except (ValueError, Exception) as e:
        return False, f"Invalid grantee identifier: {e}"

    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False, "Signature is not valid hex"

    # Canonicalize payload (exclude signature field)
    payload = {k: v for k, v in action_request_dict.items() if k != "signature"}
    payload_bytes = canonical_json_bytes(payload)

    try:
        public_key.verify(sig_bytes, payload_bytes)
        return True, ""
    except InvalidSignature:
        return False, "Signature verification failed"
    except Exception as e:
        return False, f"Verification error: {e}"
