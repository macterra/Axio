"""
Canonicalizer — Text Normalization (Phase 1)

Non-destructive text sanitation applied to raw LLM output BEFORE
JSON block extraction.

Per Q59: normalize outer whitespace and line endings only.
Do NOT collapse interior whitespace (would corrupt JSON string values).

Operations:
  1. Normalize line endings (\\r\\n → \\n, \\r → \\n)
  2. Strip leading/trailing whitespace on full text
  3. Unicode NFC normalization
  4. Remove non-printing control characters (except \\n, \\t)
"""

from __future__ import annotations

import unicodedata


def normalize_text(raw: str) -> str:
    """Normalize raw LLM text for downstream JSON extraction.

    Non-destructive: preserves interior whitespace and JSON string values.
    Returns normalized text string.
    """
    if not raw:
        return ""

    text = raw

    # 1. Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 3. Remove non-printing control characters (keep \n, \t)
    #    Control chars: categories Cc, Cf (except common whitespace)
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == "Cc":
            # Keep newline, tab, carriage return (already normalized)
            if ch in ("\n", "\t"):
                cleaned.append(ch)
            # Drop all other control characters (NUL, BEL, etc.)
        elif cat == "Cf":
            # Drop format characters: zero-width joiners, BOM, etc.
            pass
        else:
            cleaned.append(ch)
    text = "".join(cleaned)

    # 4. Strip leading/trailing whitespace
    text = text.strip()

    return text
