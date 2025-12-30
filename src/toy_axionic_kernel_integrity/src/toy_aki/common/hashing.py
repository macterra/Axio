"""Cryptographic hashing utilities for AKI.

Provides:
- SHA-256 hashing (hex output)
- HMAC-SHA-256 (hex output)
- hash_json() with no-floats enforcement
"""

import hashlib
import hmac
from typing import Any

from .canonical_json import canonical_json_bytes
from .no_floats import assert_no_floats


def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash and return lowercase hex.

    Args:
        data: Bytes to hash

    Returns:
        64-character lowercase hex string
    """
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> bytes:
    """Compute SHA-256 hash and return raw bytes.

    Args:
        data: Bytes to hash

    Returns:
        32-byte digest
    """
    return hashlib.sha256(data).digest()


def hmac_sha256_hex(key_bytes: bytes, msg_bytes: bytes) -> str:
    """Compute HMAC-SHA-256 and return lowercase hex.

    Args:
        key_bytes: HMAC key as bytes
        msg_bytes: Message to authenticate

    Returns:
        64-character lowercase hex string
    """
    return hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()


def hmac_sha256_bytes(key_bytes: bytes, msg_bytes: bytes) -> bytes:
    """Compute HMAC-SHA-256 and return raw bytes.

    Args:
        key_bytes: HMAC key as bytes
        msg_bytes: Message to authenticate

    Returns:
        32-byte HMAC digest
    """
    return hmac.new(key_bytes, msg_bytes, hashlib.sha256).digest()


def hash_json(obj: Any) -> str:
    """Hash a JSON-serializable object using canonical encoding.

    This is the primary hashing function for all protocol objects.
    Enforces the no-floats rule before hashing.

    Args:
        obj: Object to hash (must not contain floats)

    Returns:
        64-character lowercase hex SHA-256 hash

    Raises:
        FloatInHashedObjectError: If a float is found in the object
    """
    assert_no_floats(obj)
    return sha256_hex(canonical_json_bytes(obj))


def compute_proposal_hash(proposal: dict) -> str:
    """Compute the hash of a proposal (excluding proposal_hash field).

    Per K0: proposal_hash = hash_json(proposal_without_proposal_hash)

    Args:
        proposal: Proposal dict (may or may not contain proposal_hash)

    Returns:
        64-character lowercase hex hash
    """
    proposal_copy = {k: v for k, v in proposal.items() if k != "proposal_hash"}
    return hash_json(proposal_copy)


def compute_trace_commit(trace: dict) -> str:
    """Compute the hash of a trace (excluding trace_commit field).

    Per K1: trace_commit = hash_json(trace_without_trace_commit)

    Args:
        trace: Trace dict (may or may not contain trace_commit)

    Returns:
        64-character lowercase hex hash
    """
    trace_copy = {k: v for k, v in trace.items() if k != "trace_commit"}
    return hash_json(trace_copy)


def compute_entry_hash(entry: dict) -> str:
    """Compute the hash of an audit entry (excluding entry_hash field).

    Per K7: entry_hash = hash_json(entry_without_entry_hash)

    Args:
        entry: Audit entry dict (may or may not contain entry_hash)

    Returns:
        64-character lowercase hex hash
    """
    entry_copy = {k: v for k, v in entry.items() if k != "entry_hash"}
    return hash_json(entry_copy)


def seed_to_kernel_secret(seed: int) -> bytes:
    """Derive kernel secret from seed.

    Per spec: kernel_secret = sha256(b"toy_aki" + seed_bytes).digest()

    Args:
        seed: Integer seed in [0, 2^64-1]

    Returns:
        32-byte kernel secret
    """
    seed_bytes = seed.to_bytes(8, "little", signed=False)
    return sha256_bytes(b"toy_aki" + seed_bytes)
