"""Hashing utilities for toy_pseudo_axion."""

import hashlib
import hmac
from typing import Any

from .canonical_json import canonical_json_bytes


def sha256_hex(data: bytes | str) -> str:
    """Compute SHA-256 hash and return lowercase hex digest.

    Args:
        data: Input bytes or string (strings are UTF-8 encoded)

    Returns:
        Lowercase hex digest
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest().lower()


def sha256_raw(data: bytes | str) -> bytes:
    """Compute SHA-256 hash and return raw bytes.

    Args:
        data: Input bytes or string (strings are UTF-8 encoded)

    Returns:
        Raw hash bytes
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).digest()


def hash_json(obj: Any) -> str:
    """Hash a JSON-serializable object using canonical JSON encoding.

    Returns lowercase hex digest of SHA-256(canonical_json_bytes(obj)).
    """
    return sha256_hex(canonical_json_bytes(obj))


def hmac_sha256_hex(key: bytes | str, msg: bytes | str) -> str:
    """Compute HMAC-SHA256 and return lowercase hex digest.

    Args:
        key: HMAC key (bytes or string)
        msg: Message to authenticate (bytes or string)

    Returns:
        Lowercase hex digest
    """
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(msg, str):
        msg = msg.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest().lower()


def hmac_sha256_raw(key: bytes | str, msg: bytes | str) -> bytes:
    """Compute HMAC-SHA256 and return raw bytes.

    Args:
        key: HMAC key (bytes or string)
        msg: Message to authenticate (bytes or string)

    Returns:
        Raw HMAC bytes
    """
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(msg, str):
        msg = msg.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).digest()


def compute_fork_commitment(
    nonce_bytes: bytes,
    state_digest: str,
    focus_vars: list[str]
) -> str:
    """Compute fork snapshot commitment.

    commitment = HMAC-SHA256(
        key = nonce_bytes,
        msg = state_digest_raw || b"\\x00" || focus_vars_digest_raw
    )

    Args:
        nonce_bytes: Random nonce bytes (key for HMAC)
        state_digest: Hex string of hash_json(normalize_state(env, focus_vars))
        focus_vars: List of focus variable names

    Returns:
        Lowercase hex digest of the commitment
    """
    state_digest_raw = bytes.fromhex(state_digest)
    focus_vars_digest_raw = sha256_raw(canonical_json_bytes(focus_vars))
    msg = state_digest_raw + b"\x00" + focus_vars_digest_raw
    return hmac_sha256_hex(nonce_bytes, msg)


def verify_fork_commitment(
    nonce_bytes: bytes,
    state_digest: str,
    focus_vars: list[str],
    expected_commitment: str
) -> bool:
    """Verify a fork snapshot commitment.

    Args:
        nonce_bytes: Revealed nonce bytes
        state_digest: Hex string of state digest
        focus_vars: List of focus variable names
        expected_commitment: Expected commitment hex string

    Returns:
        True if commitment matches, False otherwise
    """
    computed = compute_fork_commitment(nonce_bytes, state_digest, focus_vars)
    return hmac.compare_digest(computed, expected_commitment.lower())


def derive_kernel_secret(seed: int) -> bytes:
    """Derive kernel secret from suite seed.

    kernel_secret = sha256(b"toy_pseudo_axion_mci" || seed_bytes)

    Args:
        seed: Suite seed integer

    Returns:
        32-byte kernel secret
    """
    seed_bytes = seed.to_bytes(8, byteorder='big', signed=True)
    return sha256_raw(b"toy_pseudo_axion_mci" + seed_bytes)


def compute_token_signature(kernel_secret: bytes, token_data: dict) -> str:
    """Compute toy token signature.

    signature = sha256_hex(kernel_secret || canonical_json_bytes(token_without_signature))

    Args:
        kernel_secret: 32-byte kernel secret
        token_data: Token dict WITHOUT the signature field

    Returns:
        Lowercase hex digest signature
    """
    token_bytes = canonical_json_bytes(token_data)
    return sha256_hex(kernel_secret + token_bytes)


def verify_token_signature(kernel_secret: bytes, token_data: dict, signature: str) -> bool:
    """Verify a token signature.

    Args:
        kernel_secret: 32-byte kernel secret
        token_data: Token dict WITHOUT the signature field
        signature: Expected signature hex string

    Returns:
        True if signature matches, False otherwise
    """
    computed = compute_token_signature(kernel_secret, token_data)
    return hmac.compare_digest(computed, signature.lower())
