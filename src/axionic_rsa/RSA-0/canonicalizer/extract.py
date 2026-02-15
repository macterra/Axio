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


def _repair_brace_balance(text: str) -> str:
    """Repair unbalanced braces caused by LLMs dropping closing braces.

    LLMs commonly drop a closing `}` when generating deeply nested JSON,
    especially for WriteLocal actions where the content string is long.
    The typical failure: `{"action_request": {"fields": {...}},` — the
    model closes `fields` but forgets to close `action_request`.

    Strategy: count the brace imbalance, then try inserting the missing
    `}` after each existing `}` (outside strings) until json.loads
    succeeds. This brute-force approach is safe because the search space
    is small (typically <10 `}` positions) and the text is short.
    """
    # Find all } positions outside strings
    close_positions: list[int] = []
    in_string = False
    escaped = False
    opens = 0
    closes = 0

    for i, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == "\\" and in_string:
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch == "{":
                opens += 1
            elif ch == "}":
                closes += 1
                close_positions.append(i)

    missing = opens - closes
    if missing <= 0:
        return text  # Already balanced (or has excess closes)

    # Try inserting `missing` closing braces after each existing `}`
    # position, from earliest to latest. The earliest valid position
    # is typically correct (it's where the LLM dropped the brace).
    for pos in close_positions:
        candidate = text[: pos + 1] + "}" * missing + text[pos + 1 :]
        try:
            json.loads(candidate)
            return candidate
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

    # No position worked — return original unchanged
    return text


def _repair_json_strings(text: str) -> str:
    """Repair literal control characters inside JSON string values.

    LLMs commonly emit literal newlines and tabs inside JSON strings
    instead of the escaped forms (\\n, \\t). This scans the text and
    replaces literal control characters only when inside a double-quoted
    string, preserving structural whitespace between keys.
    """
    out: list[str] = []
    in_string = False
    escaped = False

    for ch in text:
        if escaped:
            out.append(ch)
            escaped = False
            continue

        if ch == "\\":
            out.append(ch)
            if in_string:
                escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue

        if in_string:
            if ch == "\n":
                out.append("\\n")
            elif ch == "\r":
                out.append("\\r")
            elif ch == "\t":
                out.append("\\t")
            else:
                out.append(ch)
        else:
            out.append(ch)

    return "".join(out)


def _try_parse(json_str: str) -> Optional[dict]:
    """Try to parse JSON string, applying repairs if needed.

    Returns parsed dict on success, None on failure.
    """
    # 1. Try raw parse
    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            return parsed
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    # 2. Repair literal control chars in strings
    repaired = _repair_json_strings(json_str)
    try:
        parsed = json.loads(repaired)
        if isinstance(parsed, dict):
            return parsed
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    # 3. Repair brace balance (LLM dropped a closing brace)
    repaired = _repair_brace_balance(repaired)
    try:
        parsed = json.loads(repaired)
        if isinstance(parsed, dict):
            return parsed
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    return None


def extract_json_block(text: str) -> ExtractionResult:
    """Extract exactly one top-level JSON object from text.

    Per Q53: reject if 0 or >1 blocks found.
    Falls back to greedy extraction (first { to last }) when strict
    block-finding fails, to recover from LLM brace-counting errors.
    """
    if not text or not text.strip():
        return ExtractionResult(
            status=ExtractionStatus.NO_JSON.value,
            error="Empty input text",
        )

    blocks = _find_json_blocks(text)

    if len(blocks) == 1:
        start, end = blocks[0]
        json_str = text[start:end]
        parsed = _try_parse(json_str)
        if parsed is not None:
            return ExtractionResult(
                status=ExtractionStatus.OK.value,
                json_string=json_str,
                parsed=parsed,
            )
        # Block found but unparseable — fall through to greedy

    if len(blocks) > 1:
        return ExtractionResult(
            status=ExtractionStatus.AMBIGUOUS_MULTI_BLOCK.value,
            error=f"Found {len(blocks)} JSON blocks; expected exactly 1",
        )

    # Greedy fallback: first { to last }. Handles the common case where
    # the LLM drops a closing brace, making _find_json_blocks see the
    # outer {"candidates":...} as unclosed (0 blocks) or a misaligned
    # inner block (1 block, unparseable).
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace < 0 or last_brace <= first_brace:
        return ExtractionResult(
            status=ExtractionStatus.NO_JSON.value,
            error="No JSON object found in text",
        )

    greedy_str = text[first_brace:last_brace + 1]
    parsed = _try_parse(greedy_str)
    if parsed is not None:
        # Re-serialize through _repair steps to get the clean string
        clean = _repair_json_strings(greedy_str)
        clean = _repair_brace_balance(clean)
        return ExtractionResult(
            status=ExtractionStatus.OK.value,
            json_string=clean,
            parsed=parsed,
        )

    return ExtractionResult(
        status=ExtractionStatus.PARSE_ERROR.value,
        error="Extracted block is not valid JSON after repair attempts",
    )
