# PROVENANCE:
# Copied from: src/phase_ix/1-VEWA/src/canonical.py
# Source commit: 694e9cc27fcbca766099df887cb804cf19e6aeee
# Copied on: 2026-02-05
# Policy: IX-1 inventory immutable; fixes applied by copy-forward versioning.
"""
AST v0.2 Canonical Serialization (reused from IX-0/IX-1)

Per preregistration §2.5:
- Key Order: Lexicographic ASCII sort
- Whitespace: No insignificant whitespace (compact form)
- Encoding: UTF-8, no BOM
- Numbers: No leading zeros, no trailing decimal zeros
- Strings: Double-quoted, minimal escaping
- Array Ordering: Preserved, no sorting
"""

import json
from typing import Any


def canonicalize(obj: Any) -> str:
    """
    Serialize object to canonical JSON form per AST v0.2 Appendix C.

    Returns UTF-8 encoded compact JSON with lexicographically sorted keys.
    Array order is preserved.
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def canonicalize_bytes(obj: Any) -> bytes:
    """
    Serialize object to canonical JSON bytes (UTF-8, no BOM).
    """
    return canonicalize(obj).encode('utf-8')
