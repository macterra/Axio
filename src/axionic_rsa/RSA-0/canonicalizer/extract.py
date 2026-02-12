"""
Canonicalizer — JSON Block Extraction (Phase 2)

Deterministic extraction of exactly one top-level JSON object from
normalized text.

Per Q53:
  - Exactly 1 valid top-level JSON object → accept
  - 0 objects → reject (NO_JSON)
  - >1 objects → reject (AMBIGUOUS_MULTI_BLOCK)

Extraction uses brace-depth counting (not regex) for robustness
with nested structures.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ExtractionStatus(str, Enum):
    OK = "OK"
    NO_JSON = "NO_JSON"
    AMBIGUOUS_MULTI_BLOCK = "AMBIGUOUS_MULTI_BLOCK"
    PARSE_ERROR = "PARSE_ERROR"


@dataclass
class ExtractionResult:
    """Result of JSON block extraction."""
    status: str  # ExtractionStatus value
    json_string: Optional[str] = None
    parsed: Optional[Any] = None
    error: Optional[str] = None

    def ok(self) -> bool:
        return self.status == ExtractionStatus.OK.value


def _find_json_blocks(text: str) -> list[tuple[int, int]]:
    """Find all top-level { ... } blocks using brace-depth counting.

    Returns list of (start, end) index pairs.
    Handles strings (double-quoted) and escapes.
    """
    blocks: list[tuple[int, int]] = []
    i = 0
    n = len(text)

    while i < n:
        if text[i] == "{":
            # Start of a potential JSON block
            start = i
            depth = 0
            in_string = False
            escaped = False
            j = i

            while j < n:
                ch = text[j]

                if escaped:
                    escaped = False
                    j += 1
                    continue

                if ch == "\\":
                    if in_string:
                        escaped = True
                    j += 1
                    continue

                if ch == '"':
                    in_string = not in_string
                elif not in_string:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            blocks.append((start, j + 1))
                            i = j + 1
                            break

                j += 1
            else:
                # Unclosed brace — skip this opening brace
                i += 1
        else:
            i += 1

    return blocks


def extract_json_block(text: str) -> ExtractionResult:
    """Extract exactly one top-level JSON object from text.

    Per Q53: reject if 0 or >1 blocks found.
    """
    if not text or not text.strip():
        return ExtractionResult(
            status=ExtractionStatus.NO_JSON.value,
            error="Empty input text",
        )

    blocks = _find_json_blocks(text)

    if len(blocks) == 0:
        return ExtractionResult(
            status=ExtractionStatus.NO_JSON.value,
            error="No JSON object found in text",
        )

    if len(blocks) > 1:
        return ExtractionResult(
            status=ExtractionStatus.AMBIGUOUS_MULTI_BLOCK.value,
            error=f"Found {len(blocks)} JSON blocks; expected exactly 1",
        )

    start, end = blocks[0]
    json_str = text[start:end]

    # Validate it actually parses
    try:
        parsed = json.loads(json_str)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return ExtractionResult(
            status=ExtractionStatus.PARSE_ERROR.value,
            error=f"Extracted block is not valid JSON: {e}",
        )

    if not isinstance(parsed, dict):
        return ExtractionResult(
            status=ExtractionStatus.PARSE_ERROR.value,
            error=f"Extracted block is {type(parsed).__name__}, expected dict",
        )

    return ExtractionResult(
        status=ExtractionStatus.OK.value,
        json_string=json_str,
        parsed=parsed,
    )
