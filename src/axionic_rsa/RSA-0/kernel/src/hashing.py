"""
RSA-0 — Hashing Primitives (Single Source of Truth)

All content-addressable hashing flows through this module.
Artifact IDs, warrant IDs, and state-hash chain components
are all computed here.

See: kernel/src/artifacts.py for the compatibility shim (artifact_hash)
that re-exports from here.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .canonical import canonical_bytes


def content_hash(value: Any) -> str:
    """SHA-256 hex digest of canonical JSON bytes.

    Identical to the legacy ``artifact_hash`` function; kept under a
    clearer name for new code while the old name remains available
    via the compatibility shim in artifacts.py.
    """
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
