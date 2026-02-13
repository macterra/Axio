"""
RSA-0 X-0E — State Hash Chain

Implements the per-cycle state hash chain defined in X-0E spec §11.

    state_hash[0] = SHA256(constitution_hash_bytes ‖ kernel_version_hash)
    state_hash[n] = SHA256(
        state_hash[n-1] ‖ H_artifacts[n] ‖ H_admission[n] ‖
        H_selector[n]  ‖ H_execution[n]
    )

All '‖' concatenation is raw 32-byte SHA-256 digests.
Observations are excluded from the chain per spec §11 / Q&A A39/A51.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from .canonical import canonical_bytes

# Replay semantic protocol identifier — frozen once used in production logs.
# Changes only when hashing, warrant derivation, chain, or log schema changes.
KERNEL_VERSION_ID = "rsa-replay-regime-x0e-v0.1"


def _sha256_raw(data: bytes) -> bytes:
    """Return raw 32-byte SHA-256 digest."""
    return hashlib.sha256(data).digest()


def _sha256_hex(data: bytes) -> str:
    """Return hex-encoded SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def component_hash(records: List[Dict[str, Any]]) -> bytes:
    """Hash a list of log records for one cycle into a single 32-byte digest.

    H = SHA256(JCS([record_0, record_1, ...]))

    Records must be in append order within the log file for that cycle.
    """
    return _sha256_raw(canonical_bytes(records))


def initial_state_hash(constitution_hash_hex: str, kernel_version_id: str = KERNEL_VERSION_ID) -> bytes:
    """Compute state_hash[0] from constitution hash and kernel version.

    state_hash[0] = SHA256(constitution_hash_bytes ‖ kernel_version_hash)
    where kernel_version_hash = SHA256(UTF8(kernel_version_id))
    """
    constitution_bytes = bytes.fromhex(constitution_hash_hex)  # 32 bytes
    version_hash = _sha256_raw(kernel_version_id.encode("utf-8"))  # 32 bytes
    return _sha256_raw(constitution_bytes + version_hash)


def cycle_state_hash(
    prev_hash: bytes,
    artifacts_records: List[Dict[str, Any]],
    admission_records: List[Dict[str, Any]],
    selector_records: List[Dict[str, Any]],
    execution_records: List[Dict[str, Any]],
) -> bytes:
    """Compute state_hash[n] for a single cycle.

    state_hash[n] = SHA256(
        state_hash[n-1] ‖
        H_artifacts[n] ‖ H_admission[n] ‖
        H_selector[n]  ‖ H_execution[n]
    )

    Each component is 32 raw bytes; total input is 160 bytes.
    Empty record lists produce SHA256(JCS([])).
    """
    h_art = component_hash(artifacts_records)
    h_adm = component_hash(admission_records)
    h_sel = component_hash(selector_records)
    h_exe = component_hash(execution_records)
    return _sha256_raw(prev_hash + h_art + h_adm + h_sel + h_exe)


def state_hash_hex(raw: bytes) -> str:
    """Convert raw 32-byte state hash to hex string for logging."""
    return raw.hex()
