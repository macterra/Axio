"""
Authorization Oracle

Per preregistration §4:
- Pure comparator function
- Compares emitted artifact against preregistered expected artifact
- Returns AUTHORIZED if byte-identical (canonical hash match), REJECTED otherwise
"""

import hashlib
from enum import Enum
from typing import Any, Dict

from .canonical import canonicalize_bytes


class AuthResult(Enum):
    """Authorization result from oracle comparison."""
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    NA = "N/A"  # For cases where no artifact was produced


def authorize(emitted_artifact: Dict[str, Any], expected_artifact: Dict[str, Any]) -> AuthResult:
    """
    Compare emitted artifact against preregistered expected artifact.
    Returns AUTHORIZED if byte-identical, REJECTED otherwise.

    Per preregistration §4.1, comparison uses canonical serialization and SHA-256.
    """
    emitted_canonical = canonicalize_bytes(emitted_artifact)
    expected_canonical = canonicalize_bytes(expected_artifact)

    emitted_hash = hashlib.sha256(emitted_canonical).hexdigest()
    expected_hash = hashlib.sha256(expected_canonical).hexdigest()

    if emitted_hash == expected_hash:
        return AuthResult.AUTHORIZED
    else:
        return AuthResult.REJECTED


def compute_artifact_hash(artifact: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of canonical artifact representation."""
    return hashlib.sha256(canonicalize_bytes(artifact)).hexdigest()
