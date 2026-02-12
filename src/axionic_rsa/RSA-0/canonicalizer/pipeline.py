"""
Canonicalizer — Full Pipeline

Composes normalize_text() + extract_json_block() into a single
deterministic pipeline.

Input:  raw LLM text (untrusted)
Output: CanonicalizationResult with clean JSON string + parsed dict
        OR rejection with structured reason.

Per Q1 pipeline:
  LLM raw text
  → canonicalizer.normalize_text()
  → canonicalizer.extract_json_block()
  → JSON parse (done by extract)
  → kernel canonical_json() (downstream, not in canonicalizer)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional

from canonicalizer.normalize import normalize_text
from canonicalizer.extract import (
    ExtractionResult,
    ExtractionStatus,
    extract_json_block,
)


@dataclass
class CanonicalizationResult:
    """Result of the full canonicalization pipeline."""
    success: bool
    normalized_text: str = ""
    json_string: Optional[str] = None
    parsed: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    raw_hash: str = ""
    canonicalized_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "success": self.success,
            "raw_hash": self.raw_hash,
            "canonicalized_hash": self.canonicalized_hash,
        }
        if self.rejection_reason:
            d["rejection_reason"] = self.rejection_reason
        return d


def canonicalize(raw_text: str) -> CanonicalizationResult:
    """Run the full canonicalization pipeline on raw LLM text.

    Returns CanonicalizationResult. On failure, success=False and
    rejection_reason is populated.
    """
    raw_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    # Phase 1: text normalization
    normalized = normalize_text(raw_text)

    # Phase 2: JSON block extraction
    extraction: ExtractionResult = extract_json_block(normalized)

    if not extraction.ok():
        return CanonicalizationResult(
            success=False,
            normalized_text=normalized,
            rejection_reason=extraction.status,
            raw_hash=raw_hash,
            canonicalized_hash="",
        )

    # Compute hash of the extracted JSON string
    canonicalized_hash = hashlib.sha256(
        extraction.json_string.encode("utf-8")
    ).hexdigest()

    return CanonicalizationResult(
        success=True,
        normalized_text=normalized,
        json_string=extraction.json_string,
        parsed=extraction.parsed,
        raw_hash=raw_hash,
        canonicalized_hash=canonicalized_hash,
    )


def source_hash() -> str:
    """Compute SHA-256 of all canonicalizer source files.

    Used at preflight to verify canonicalizer integrity.
    """
    import importlib
    from pathlib import Path

    pkg_dir = Path(__file__).resolve().parent
    source_files = sorted(pkg_dir.glob("*.py"))

    hasher = hashlib.sha256()
    for f in source_files:
        hasher.update(f.read_bytes())

    return hasher.hexdigest()


def self_test_hash() -> str:
    """Run a fixed-input round-trip and return the output hash.

    Per Q4: both source hash and self-test hash are recorded.
    """
    fixed_input = (
        'Here is the result:\n'
        '{"candidates": [{"action_request": {"action_type": "Notify", '
        '"fields": {"target": "stdout", "message": "hello"}}, '
        '"scope_claim": {"observation_ids": ["obs1"], "claim": "test", '
        '"clause_ref": "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"}, '
        '"justification": {"text": "test justification"}, '
        '"authority_citations": '
        '["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]}]}\n'
    )

    result = canonicalize(fixed_input)
    if not result.success:
        raise RuntimeError(f"Canonicalizer self-test failed: {result.rejection_reason}")

    return result.canonicalized_hash
