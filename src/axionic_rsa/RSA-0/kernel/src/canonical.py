"""
RSA-0 — Canonical JSON Serialization (Single Source of Truth)

All canonical JSON encoding flows through this module.
Implementation: canonicaljson library (RFC 8785 — JSON Canonicalization
Scheme).  Pinned as a freeze-grade dependency.

Supported types: strings, integers, booleans, null, arrays, objects,
floats (finite only — NaN/Inf forbidden).

See: kernel/src/artifacts.py for compatibility shims (canonical_json,
canonical_json_bytes) that re-export from here.
"""

from __future__ import annotations

import math
from typing import Any

import canonicaljson as _cjson


def _assert_no_non_finite(value: Any) -> None:
    """Reject NaN / Inf anywhere in the value tree."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Non-finite float not allowed in canonical JSON: {value!r}")
    elif isinstance(value, dict):
        for v in value.values():
            _assert_no_non_finite(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _assert_no_non_finite(v)


def canonical_bytes(value: Any) -> bytes:
    """Canonical JSON as strict UTF-8 bytes (RFC 8785 JCS).  Primary form."""
    _assert_no_non_finite(value)
    return _cjson.encode_canonical_json(value)


def canonical_str(value: Any) -> str:
    """Canonical JSON as a Python str.  Thin wrapper over canonical_bytes."""
    return canonical_bytes(value).decode("utf-8")
