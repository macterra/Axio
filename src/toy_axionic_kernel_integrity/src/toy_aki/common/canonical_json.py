"""Canonical JSON encoding for deterministic hashing.

Per spec:
- Object keys sorted lexicographically (bytewise UTF-8)
- No whitespace
- Arrays preserve order
- Integers encoded base-10, no leading zeros, -0 normalized to 0
- No NaN/Inf (impossible if floats are forbidden)
"""

import json
from typing import Any


def canonical_json_bytes(obj: Any) -> bytes:
    """Encode an object to canonical JSON bytes.

    Args:
        obj: Object to encode (must not contain floats)

    Returns:
        Canonical JSON as UTF-8 bytes

    Raises:
        ValueError: If object contains NaN, Inf, or other non-serializable values
    """
    return json.dumps(
        obj,
        separators=(',', ':'),  # No whitespace
        sort_keys=True,         # Lexicographic key ordering
        ensure_ascii=False,     # Allow UTF-8
        allow_nan=False,        # Reject NaN/Inf
    ).encode('utf-8')


def canonical_json_str(obj: Any) -> str:
    """Encode an object to canonical JSON string.

    Args:
        obj: Object to encode (must not contain floats)

    Returns:
        Canonical JSON as string
    """
    return canonical_json_bytes(obj).decode('utf-8')


def normalize_integer(value: int) -> int:
    """Normalize an integer value.

    Per spec: -0 normalized to 0 (Python already handles this).

    Args:
        value: Integer value

    Returns:
        Normalized integer
    """
    if value == 0:
        return 0  # Handles -0 case
    return value
