"""
RSA X-3 — Signature Helpers (Succession Extension)

Extends X-2 Ed25519 signature module with:
- Sovereign signature verification with PRIOR_KEY_PRIVILEGE_LEAK detection
- SuccessionProposal signing/verification
- TreatyRatification signing/verification
- CycleCommit/CycleStart signing/verification
- HKDF-SHA256 successor key derivation

No external identity providers, no network calls, no time-based freshness.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

from ..artifacts import canonical_json_bytes
from ..rsax2.signature import (
    public_key_from_hex,
    extract_pubkey_hex,
    generate_keypair,
    sign_action_request,
    verify_action_request_signature,
)


# ---------------------------------------------------------------------------
# HKDF-SHA256 Successor Key Derivation
# ---------------------------------------------------------------------------

def derive_successor_keypair(
    seed: bytes,
    chain_length: int,
    info_prefix: bytes = b"sovereign-key-",
) -> Tuple[Ed25519PrivateKey, str]:
    """Derive a deterministic Ed25519 keypair for a given chain position.

    Uses HKDF-SHA256 to derive 32 bytes of key material, then uses that
    as the Ed25519 private key seed.

    Args:
        seed: The root seed (IKM for HKDF)
        chain_length: The identity chain position (used in info)
        info_prefix: Prefix for the HKDF info parameter

    Returns:
        (private_key, grantee_identifier) where identifier is "ed25519:<hex64>"
    """
    info = info_prefix + str(chain_length).encode("ascii")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"rsa-x3-genesis",
        info=info,
    )
    key_material = hkdf.derive(seed)

    private_key = Ed25519PrivateKey.from_private_bytes(key_material)
    public_key = private_key.public_key()
    pub_hex = public_key.public_bytes_raw().hex()
    grantee_id = f"ed25519:{pub_hex}"
    return private_key, grantee_id


def derive_genesis_keypair(seed: bytes) -> Tuple[Ed25519PrivateKey, str]:
    """Derive the genesis sovereign keypair (chain_length=0 for key derivation)."""
    return derive_successor_keypair(seed, chain_length=0)


def precompute_keypairs(
    seed: bytes,
    max_rotations: int,
) -> list:
    """Precompute all keypairs for a session.

    Returns list of (private_key, grantee_identifier) tuples,
    indexed by chain position (0 = genesis).
    """
    return [
        derive_successor_keypair(seed, i)
        for i in range(max_rotations + 1)
    ]


# ---------------------------------------------------------------------------
# Sovereign Signature Verification with Privilege Leak Detection
# ---------------------------------------------------------------------------

def verify_active_sovereign_signature(
    payload_dict: Dict[str, Any],
    signature_hex: str,
    signer_identifier: str,
    active_sovereign_key: str,
    prior_sovereign_key: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """Verify a signature that requires active sovereign authority.

    Returns:
        (valid, error_message, rejection_code)
        - If valid: (True, "", "")
        - If prior key: (False, msg, "PRIOR_KEY_PRIVILEGE_LEAK")
        - If other: (False, msg, "SIGNATURE_INVALID")
    """
    if signer_identifier != active_sovereign_key:
        if prior_sovereign_key and signer_identifier == prior_sovereign_key:
            return (
                False,
                "Prior sovereign key attempted sovereign action post-activation",
                "PRIOR_KEY_PRIVILEGE_LEAK",
            )
        return (
            False,
            f"Signer {signer_identifier} is not the active sovereign",
            "SIGNATURE_INVALID",
        )

    # Verify the actual signature
    try:
        pub_hex = extract_pubkey_hex(signer_identifier)
        public_key = public_key_from_hex(pub_hex)
    except (ValueError, Exception) as e:
        return False, f"Invalid sovereign key: {e}", "SIGNATURE_INVALID"

    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False, "Signature is not valid hex", "SIGNATURE_INVALID"

    payload_bytes = canonical_json_bytes(payload_dict)

    try:
        public_key.verify(sig_bytes, payload_bytes)
        return True, "", ""
    except InvalidSignature:
        return False, "Signature verification failed", "SIGNATURE_INVALID"
    except Exception as e:
        return False, f"Verification error: {e}", "SIGNATURE_INVALID"


# ---------------------------------------------------------------------------
# Succession Proposal Signing/Verification
# ---------------------------------------------------------------------------

def sign_succession_proposal(
    private_key: Ed25519PrivateKey,
    proposal_dict: Dict[str, Any],
) -> str:
    """Sign a SuccessionProposal payload (excludes signature and id fields)."""
    payload = {
        k: v for k, v in proposal_dict.items()
        if k not in ("signature", "id")
    }
    payload_bytes = canonical_json_bytes(payload)
    signature = private_key.sign(payload_bytes)
    return signature.hex()


def verify_succession_proposal(
    signer_identifier: str,
    proposal_dict: Dict[str, Any],
    signature_hex: str,
) -> Tuple[bool, str]:
    """Verify Ed25519 signature on a SuccessionProposal.

    Returns (valid, error_message).
    """
    try:
        pub_hex = extract_pubkey_hex(signer_identifier)
        public_key = public_key_from_hex(pub_hex)
    except (ValueError, Exception) as e:
        return False, f"Invalid key: {e}"

    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False, "Signature is not valid hex"

    payload = {
        k: v for k, v in proposal_dict.items()
        if k not in ("signature", "id")
    }
    payload_bytes = canonical_json_bytes(payload)

    try:
        public_key.verify(sig_bytes, payload_bytes)
        return True, ""
    except InvalidSignature:
        return False, "Signature verification failed"
    except Exception as e:
        return False, f"Verification error: {e}"


# ---------------------------------------------------------------------------
# Treaty Ratification Signing/Verification
# ---------------------------------------------------------------------------

def sign_treaty_ratification(
    private_key: Ed25519PrivateKey,
    ratification_dict: Dict[str, Any],
) -> str:
    """Sign a TreatyRatification payload (excludes signature and id fields)."""
    payload = {
        k: v for k, v in ratification_dict.items()
        if k not in ("signature", "id")
    }
    payload_bytes = canonical_json_bytes(payload)
    signature = private_key.sign(payload_bytes)
    return signature.hex()


# ---------------------------------------------------------------------------
# Cycle Commit/Start Signing/Verification
# ---------------------------------------------------------------------------

def sign_cycle_commit(
    private_key: Ed25519PrivateKey,
    commit_payload_dict: Dict[str, Any],
) -> str:
    """Sign a CycleCommitPayload."""
    payload_bytes = canonical_json_bytes(commit_payload_dict)
    signature = private_key.sign(payload_bytes)
    return signature.hex()


def verify_cycle_commit(
    signer_identifier: str,
    commit_payload_dict: Dict[str, Any],
    signature_hex: str,
) -> Tuple[bool, str]:
    """Verify Ed25519 signature on a CycleCommitPayload."""
    try:
        pub_hex = extract_pubkey_hex(signer_identifier)
        public_key = public_key_from_hex(pub_hex)
    except (ValueError, Exception) as e:
        return False, f"Invalid key: {e}"

    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False, "Signature is not valid hex"

    payload_bytes = canonical_json_bytes(commit_payload_dict)

    try:
        public_key.verify(sig_bytes, payload_bytes)
        return True, ""
    except InvalidSignature:
        return False, "Signature verification failed"


def sign_cycle_start(
    private_key: Ed25519PrivateKey,
    start_payload_dict: Dict[str, Any],
) -> str:
    """Sign a CycleStartPayload."""
    payload_bytes = canonical_json_bytes(start_payload_dict)
    signature = private_key.sign(payload_bytes)
    return signature.hex()


def verify_cycle_start(
    signer_identifier: str,
    start_payload_dict: Dict[str, Any],
    signature_hex: str,
) -> Tuple[bool, str]:
    """Verify Ed25519 signature on a CycleStartPayload."""
    try:
        pub_hex = extract_pubkey_hex(signer_identifier)
        public_key = public_key_from_hex(pub_hex)
    except (ValueError, Exception) as e:
        return False, f"Invalid key: {e}"

    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False, "Signature is not valid hex"

    payload_bytes = canonical_json_bytes(start_payload_dict)

    try:
        public_key.verify(sig_bytes, payload_bytes)
        return True, ""
    except InvalidSignature:
        return False, "Signature verification failed"
