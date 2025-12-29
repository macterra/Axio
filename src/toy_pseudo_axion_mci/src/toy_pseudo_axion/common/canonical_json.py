"""Canonical JSON encoding following RFC 8785 (JCS) semantics."""

import json
import math
from typing import Any


def _format_float(x: float) -> str:
    """Format a float with max 8 decimal places, trimming trailing zeros and dot.

    Handles special cases:
    - -0.0 normalized to 0
    - No NaN/Inf allowed (raises ValueError)
    """
    if math.isnan(x) or math.isinf(x):
        raise ValueError(f"Cannot encode NaN or Inf in canonical JSON: {x}")

    # Normalize -0.0 to 0
    if x == 0.0:
        return "0"

    # Format with 8 decimal places
    formatted = format(x, ".8f")

    # Trim trailing zeros and trailing dot
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")

    return formatted


def _canonical_value(obj: Any) -> Any:
    """Recursively convert object to canonical form for JSON encoding."""
    if obj is None:
        return None
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, int):
        return obj
    elif isinstance(obj, float):
        # Convert float to canonical string representation for encoding
        return _CanonicalFloat(obj)
    elif isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        # Sort keys lexicographically (bytewise UTF-8)
        return {k: _canonical_value(v) for k, v in sorted(obj.items(), key=lambda x: x[0].encode('utf-8'))}
    elif isinstance(obj, (list, tuple)):
        return [_canonical_value(item) for item in obj]
    else:
        raise TypeError(f"Cannot encode type {type(obj).__name__} in canonical JSON")


class _CanonicalFloat(float):
    """A float subclass that formats itself canonically when JSON encoded."""

    def __repr__(self) -> str:
        return _format_float(self)


class CanonicalJSONEncoder(json.JSONEncoder):
    """JSON encoder that produces canonical output."""

    def encode(self, o: Any) -> str:
        """Encode object to canonical JSON string."""
        return super().encode(_canonical_value(o))

    def default(self, o: Any) -> Any:
        if isinstance(o, _CanonicalFloat):
            # This shouldn't be reached due to iterencode handling
            return float(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    def iterencode(self, o: Any, _one_shot: bool = False) -> str:
        """Override to handle _CanonicalFloat properly."""
        # Process the object to canonical form first
        canonical = _canonical_value(o)

        # Use custom encoding for floats
        return self._iterencode_impl(canonical)

    def _iterencode_impl(self, o: Any) -> str:
        """Custom implementation that handles canonical floats."""
        if o is None:
            yield "null"
        elif o is True:
            yield "true"
        elif o is False:
            yield "false"
        elif isinstance(o, _CanonicalFloat):
            yield _format_float(o)
        elif isinstance(o, int):
            yield str(o)
        elif isinstance(o, float):
            yield _format_float(o)
        elif isinstance(o, str):
            yield json.dumps(o)
        elif isinstance(o, dict):
            yield "{"
            first = True
            for k, v in o.items():
                if not first:
                    yield ","
                first = False
                yield json.dumps(k)
                yield ":"
                yield from self._iterencode_impl(v)
            yield "}"
        elif isinstance(o, list):
            yield "["
            first = True
            for item in o:
                if not first:
                    yield ","
                first = False
                yield from self._iterencode_impl(item)
            yield "]"
        else:
            raise TypeError(f"Cannot encode type {type(o).__name__}")


def canonical_json_string(obj: Any) -> str:
    """Convert object to canonical JSON string.

    Rules:
    - Object keys sorted lexicographically (bytewise UTF-8)
    - No whitespace
    - Arrays preserve order
    - Floats: max 8 decimal places, trailing zeros/dot trimmed, -0 -> 0
    - No NaN/Inf
    """
    encoder = CanonicalJSONEncoder(separators=(",", ":"), sort_keys=False)
    return "".join(encoder._iterencode_impl(_canonical_value(obj)))


def canonical_json_bytes(obj: Any) -> bytes:
    """Convert object to canonical JSON bytes (UTF-8 encoded)."""
    return canonical_json_string(obj).encode("utf-8")
