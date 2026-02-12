"""
RSA-0 Canonicalizer — Deterministic LLM Text Normalization

Pipeline: raw LLM text → normalize_text() → extract_json_block() → JSON string
Operates BEFORE JSON parsing. Existing canonical_json() operates AFTER parsing.

Frozen before X-0L execution. Source hash + self-test hash recorded at preflight.
"""

from canonicalizer.normalize import normalize_text
from canonicalizer.extract import extract_json_block, ExtractionResult
from canonicalizer.pipeline import canonicalize, CanonicalizationResult

__all__ = [
    "normalize_text",
    "extract_json_block",
    "ExtractionResult",
    "canonicalize",
    "CanonicalizationResult",
]
