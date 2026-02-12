"""
Canonicalizer Unit Tests

Tests for:
  - Text normalization (normalize.py)
  - JSON block extraction (extract.py)
  - Full pipeline (pipeline.py)
  - Source hash stability
  - Self-test hash stability
  - Fuzz resilience
  - Idempotence
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from canonicalizer.normalize import normalize_text
from canonicalizer.extract import (
    ExtractionResult,
    ExtractionStatus,
    extract_json_block,
    _find_json_blocks,
)
from canonicalizer.pipeline import (
    CanonicalizationResult,
    canonicalize,
    source_hash,
    self_test_hash,
)


# ===================================================================
# normalize_text tests
# ===================================================================

class TestNormalizeText:
    """Tests for canonicalizer.normalize.normalize_text."""

    def test_empty_input(self):
        assert normalize_text("") == ""

    def test_pure_whitespace(self):
        assert normalize_text("   \n\t  ") == ""

    def test_crlf_normalization(self):
        assert "\r" not in normalize_text("line1\r\nline2\r\nline3")

    def test_cr_normalization(self):
        assert "\r" not in normalize_text("line1\rline2")

    def test_preserves_interior_whitespace(self):
        """Q59: do NOT collapse interior whitespace."""
        text = '{"key": "value  with   spaces"}'
        result = normalize_text(text)
        assert "value  with   spaces" in result

    def test_strips_leading_trailing(self):
        result = normalize_text("  \n hello \n  ")
        assert result == "hello"

    def test_removes_null_byte(self):
        result = normalize_text("hello\x00world")
        assert "\x00" not in result
        assert "helloworld" in result

    def test_removes_bom(self):
        """BOM (U+FEFF) is category Cf — should be removed."""
        result = normalize_text("\ufeffhello")
        assert result == "hello"

    def test_removes_zero_width_joiner(self):
        """Zero-width joiner (U+200D) is Cf — removed."""
        result = normalize_text("hello\u200dworld")
        assert "\u200d" not in result

    def test_removes_zero_width_space(self):
        """Zero-width space (U+200B) is Cf — removed."""
        result = normalize_text("\u200bhello\u200b")
        assert "\u200b" not in result
        assert result == "hello"

    def test_preserves_newline_tab(self):
        result = normalize_text("line1\n\tline2")
        assert "\n" in result
        assert "\t" in result

    def test_unicode_nfc_normalization(self):
        """NFC: é as combining should become single char."""
        import unicodedata
        composed = "\u00e9"  # é (single char)
        decomposed = "e\u0301"  # e + combining accent
        result = normalize_text(decomposed)
        assert result == composed

    def test_removes_bell_character(self):
        result = normalize_text("hello\x07world")
        assert "\x07" not in result

    def test_json_string_values_preserved(self):
        """Critical: JSON string values must not be corrupted."""
        text = '{"message": "hello  world", "path": "./workspace/test  file.txt"}'
        result = normalize_text(text)
        assert "hello  world" in result
        assert "test  file.txt" in result


# ===================================================================
# extract_json_block tests
# ===================================================================

class TestExtractJsonBlock:
    """Tests for canonicalizer.extract.extract_json_block."""

    def test_empty_input(self):
        result = extract_json_block("")
        assert not result.ok()
        assert result.status == ExtractionStatus.NO_JSON.value

    def test_no_json(self):
        result = extract_json_block("Just plain text with no JSON.")
        assert not result.ok()
        assert result.status == ExtractionStatus.NO_JSON.value

    def test_simple_json(self):
        result = extract_json_block('{"candidates": []}')
        assert result.ok()
        assert result.parsed == {"candidates": []}

    def test_json_surrounded_by_prose(self):
        text = 'Here is the result:\n{"candidates": []}\nDone.'
        result = extract_json_block(text)
        assert result.ok()
        assert result.parsed == {"candidates": []}

    def test_json_with_markdown_fences(self):
        """LLM sometimes wraps JSON in code fences — extraction should still work
        as long as there's exactly one { ... } block."""
        text = '```json\n{"candidates": []}\n```'
        result = extract_json_block(text)
        assert result.ok()
        assert result.parsed == {"candidates": []}

    def test_multiple_blocks_rejected(self):
        """Q53: >1 JSON blocks → AMBIGUOUS_MULTI_BLOCK."""
        text = '{"a": 1} {"b": 2}'
        result = extract_json_block(text)
        assert not result.ok()
        assert result.status == ExtractionStatus.AMBIGUOUS_MULTI_BLOCK.value

    def test_nested_json_counts_as_one(self):
        text = '{"outer": {"inner": {"deep": true}}}'
        result = extract_json_block(text)
        assert result.ok()
        assert result.parsed["outer"]["inner"]["deep"] is True

    def test_json_with_string_braces(self):
        """Braces inside strings should not confuse the extractor."""
        text = '{"message": "this has {braces} inside"}'
        result = extract_json_block(text)
        assert result.ok()
        assert result.parsed["message"] == "this has {braces} inside"

    def test_json_with_escaped_quotes(self):
        text = '{"message": "say \\"hello\\""}'
        result = extract_json_block(text)
        assert result.ok()
        assert "hello" in result.parsed["message"]

    def test_unclosed_brace(self):
        text = '{"incomplete": true'
        result = extract_json_block(text)
        assert not result.ok()
        assert result.status == ExtractionStatus.NO_JSON.value

    def test_array_not_accepted(self):
        """Only dict (object) is accepted, not array."""
        text = '[1, 2, 3]'
        result = extract_json_block(text)
        assert not result.ok()  # No { ... } block found

    def test_real_candidate_payload(self):
        """Test with a realistic RSA-0 candidate payload."""
        payload = json.dumps({
            "candidates": [{
                "action_request": {
                    "action_type": "Notify",
                    "fields": {"target": "stdout", "message": "hello"}
                },
                "scope_claim": {
                    "observation_ids": ["obs1"],
                    "claim": "test claim",
                    "clause_ref": "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
                },
                "justification": {"text": "test justification"},
                "authority_citations": [
                    "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
                ]
            }]
        })
        result = extract_json_block(payload)
        assert result.ok()
        assert len(result.parsed["candidates"]) == 1

    def test_json_preceded_by_commentary(self):
        text = (
            "I'll create a Notify action as requested.\n\n"
            '{"candidates": [{"action_request": {"action_type": "Notify", '
            '"fields": {"target": "stdout", "message": "hi"}}, '
            '"scope_claim": {"observation_ids": [], "claim": "ok", '
            '"clause_ref": "x"}, "justification": {"text": "y"}, '
            '"authority_citations": ["x"]}]}'
        )
        result = extract_json_block(text)
        assert result.ok()
        assert result.parsed["candidates"][0]["action_request"]["action_type"] == "Notify"


class TestFindJsonBlocks:
    """Tests for the internal block finder."""

    def test_zero_blocks(self):
        assert _find_json_blocks("no json here") == []

    def test_one_block(self):
        blocks = _find_json_blocks('abc{"key":"val"}def')
        assert len(blocks) == 1

    def test_two_blocks(self):
        blocks = _find_json_blocks('{"a":1} text {"b":2}')
        assert len(blocks) == 2

    def test_nested_counts_as_one(self):
        blocks = _find_json_blocks('{"a":{"b":{"c":1}}}')
        assert len(blocks) == 1

    def test_string_braces_dont_count(self):
        blocks = _find_json_blocks('{"msg":"{hello}"}')
        assert len(blocks) == 1


# ===================================================================
# Full pipeline tests
# ===================================================================

class TestCanonicalize:
    """Tests for canonicalizer.pipeline.canonicalize."""

    def test_simple_json(self):
        result = canonicalize('{"candidates": []}')
        assert result.success
        assert result.parsed == {"candidates": []}
        assert result.canonicalized_hash != ""
        assert result.raw_hash != ""

    def test_json_with_bom_and_whitespace(self):
        result = canonicalize('\ufeff  \n{"candidates": []}\n  ')
        assert result.success
        assert result.parsed == {"candidates": []}

    def test_no_json_fails(self):
        result = canonicalize("just plain text")
        assert not result.success
        assert result.rejection_reason == ExtractionStatus.NO_JSON.value

    def test_multi_block_fails(self):
        result = canonicalize('{"a": 1} {"b": 2}')
        assert not result.success
        assert result.rejection_reason == ExtractionStatus.AMBIGUOUS_MULTI_BLOCK.value

    def test_empty_input(self):
        result = canonicalize("")
        assert not result.success

    def test_idempotence(self):
        """Canonicalizing the output of canonicalization gives same hash."""
        raw = 'Some prose\n{"candidates": []}\nMore prose'
        r1 = canonicalize(raw)
        assert r1.success
        r2 = canonicalize(r1.json_string)
        assert r2.success
        assert r1.canonicalized_hash == r2.canonicalized_hash

    def test_zero_width_removal_preserves_json(self):
        raw = '\u200b{"candidates": [\u200b]}\u200b'
        result = canonicalize(raw)
        assert result.success
        assert result.parsed == {"candidates": []}

    def test_raw_hash_differs_from_canonicalized(self):
        """Raw hash includes surrounding prose; canonicalized doesn't."""
        raw = 'Hello\n{"candidates": []}\nBye'
        result = canonicalize(raw)
        assert result.success
        assert result.raw_hash != result.canonicalized_hash

    def test_crlf_in_json(self):
        raw = '{\r\n"candidates": [\r\n]\r\n}'
        result = canonicalize(raw)
        assert result.success

    def test_realistic_llm_output(self):
        text = (
            'Sure, here is the action:\n\n```json\n'
            '{"candidates": [{"action_request": {"action_type": "Notify", '
            '"fields": {"target": "stdout", "message": "calibration-check"}}, '
            '"scope_claim": {"observation_ids": ["obs1"], "claim": "test", '
            '"clause_ref": "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"}, '
            '"justification": {"text": "Authorized by cited clause."}, '
            '"authority_citations": ['
            '"constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]}]}\n'
            '```\n'
        )
        result = canonicalize(text)
        assert result.success
        assert len(result.parsed["candidates"]) == 1


# ===================================================================
# Source hash and self-test
# ===================================================================

class TestCanonalizerIntegrity:
    """Tests for canonicalizer integrity checks."""

    def test_source_hash_stable(self):
        h1 = source_hash()
        h2 = source_hash()
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_self_test_hash_stable(self):
        h1 = self_test_hash()
        h2 = self_test_hash()
        assert h1 == h2
        assert len(h1) == 64

    def test_self_test_succeeds(self):
        """Self-test must not raise."""
        h = self_test_hash()
        assert isinstance(h, str)
        assert len(h) > 0


# ===================================================================
# Fuzz resilience
# ===================================================================

class TestCanonalizerFuzz:
    """Fuzz tests matching preflight requirements (Q5)."""

    @pytest.mark.parametrize("raw", [
        '\u200b{"candidates": []}\u200b',
        '{"candidates": []}',
        '{\r\n"candidates"\r: [\r\n]\r\n}',
        '\ufeff{"candidates": []}',
        '\t  {"candidates": []}  \t',
        '  {  "candidates"  :  [  ]  }  ',
        'Here is response:\u200d\n{"candidates": []}',
        '\u200f{"candidates": []}',
    ])
    def test_fuzz_case_extracts(self, raw):
        """Each fuzz case should either succeed or fail cleanly (no crash)."""
        result = canonicalize(raw)
        # All should either succeed or have a proper rejection reason
        if not result.success:
            assert result.rejection_reason is not None

    @pytest.mark.parametrize("raw", [
        '\u200b{"candidates": []}\u200b',
        '\ufeff{"candidates": []}',
        '\t  {"candidates": []}  \t',
        'Here is response:\u200d\n{"candidates": []}',
    ])
    def test_fuzz_idempotence(self, raw):
        """Q5: canonicalization must be idempotent on extractable inputs."""
        r1 = canonicalize(raw)
        if r1.success and r1.json_string:
            r2 = canonicalize(r1.json_string)
            assert r2.success
            assert r1.canonicalized_hash == r2.canonicalized_hash
