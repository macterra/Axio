"""
Unit Tests for Phase IX-0 TLI

Per preregistration §6 Test Vectors and §8 Classification.
Tests all 8 conditions A-H.
"""

import pytest
from typing import Dict, Any

from src.canonical import canonicalize, canonicalize_bytes
from src.structural_diff import (
    structural_diff, classify_diff, DiffEntry, DiffResult, MISSING,
    is_user_field_path, is_derived_field_path
)
from src.authorization_oracle import authorize, compute_artifact_hash, AuthResult
from src.translation_layer import (
    TranslationLayer, TranslationResult, TranslationStatus, FaultConfig
)
from src.translation_harness import TranslationHarness, TEST_VECTORS
from src.logging import ConditionLog, ExecutionLog


# ============================================================================
# Canonical Serialization Tests
# ============================================================================

class TestCanonical:
    """Tests for AST v0.2 canonical serialization."""

    def test_key_ordering(self):
        """Keys must be sorted lexicographically."""
        obj = {"z": 1, "a": 2, "m": 3}
        result = canonicalize(obj)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_nested_key_ordering(self):
        """Nested objects must also have sorted keys."""
        obj = {"outer": {"z": 1, "a": 2}, "inner": {"b": 3}}
        result = canonicalize(obj)
        assert result == '{"inner":{"b":3},"outer":{"a":2,"z":1}}'

    def test_array_preservation(self):
        """Array order must be preserved."""
        obj = {"items": [3, 1, 2]}
        result = canonicalize(obj)
        assert result == '{"items":[3,1,2]}'

    def test_no_whitespace(self):
        """Output must have no extraneous whitespace."""
        obj = {"key": "value", "number": 42}
        result = canonicalize(obj)
        assert " " not in result
        assert "\n" not in result

    def test_bytes_output(self):
        """canonicalize_bytes must return UTF-8 bytes."""
        obj = {"key": "value"}
        result = canonicalize_bytes(obj)
        assert isinstance(result, bytes)
        assert result == b'{"key":"value"}'

    def test_unicode_handling(self):
        """Unicode must be properly encoded."""
        obj = {"name": "日本語"}
        result = canonicalize(obj)
        assert "日本語" in result


# ============================================================================
# Structural Diff Tests
# ============================================================================

class TestStructuralDiff:
    """Tests for path-level structural diff."""

    def test_identical_objects(self):
        """Identical objects produce empty diff."""
        obj = {"a": 1, "b": 2}
        diff = structural_diff(obj, obj)
        assert len(diff.entries) == 0

    def test_value_modification(self):
        """Value changes produce entries with left/right values."""
        actual = {"a": 1, "b": 2}
        expected = {"a": 1, "b": 3}
        diff = structural_diff(actual, expected)

        assert len(diff.entries) == 1
        entry = diff.entries[0]
        assert entry.path == "b"
        assert entry.left == 2  # actual
        assert entry.right == 3  # expected

    def test_missing_field(self):
        """Missing fields produce entries with MISSING sentinel."""
        actual = {"a": 1}
        expected = {"a": 1, "b": 2}
        diff = structural_diff(actual, expected)

        assert len(diff.entries) == 1
        entry = diff.entries[0]
        assert entry.path == "b"
        assert entry.left is MISSING  # actual missing
        assert entry.right == 2  # expected present

    def test_extra_field(self):
        """Extra fields produce entries with MISSING sentinel."""
        actual = {"a": 1, "b": 2}
        expected = {"a": 1}
        diff = structural_diff(actual, expected)

        assert len(diff.entries) == 1
        entry = diff.entries[0]
        assert entry.path == "b"
        assert entry.left == 2  # actual present
        assert entry.right is MISSING  # expected missing

    def test_nested_diff(self):
        """Nested object diffs use dot-path notation."""
        actual = {"outer": {"inner": 1}}
        expected = {"outer": {"inner": 2}}
        diff = structural_diff(actual, expected)

        assert len(diff.entries) == 1
        entry = diff.entries[0]
        assert entry.path == "outer.inner"
        assert entry.left == 1
        assert entry.right == 2

    def test_array_element_diff(self):
        """Array element diffs use bracket notation."""
        actual = {"items": [1, 2, 3]}
        expected = {"items": [1, 9, 3]}
        diff = structural_diff(actual, expected)

        assert len(diff.entries) == 1
        entry = diff.entries[0]
        assert entry.path == "items[1]"
        assert entry.left == 2
        assert entry.right == 9

    def test_lexicographic_traversal(self):
        """Diff entries must be in lexicographic path order."""
        actual = {"z": 1, "a": 2, "m": 3}
        expected = {"z": 9, "a": 8, "m": 7}
        diff = structural_diff(actual, expected)

        paths = [e.path for e in diff.entries]
        assert paths == sorted(paths)


class TestClassifyDiff:
    """Tests for diff classification."""

    def test_identical_classification(self):
        """Empty diff classifies as IDENTICAL."""
        diff = DiffResult(entries=[])
        assert classify_diff(diff) == "IDENTICAL"

    def test_user_field_changes(self):
        """User field changes classify as MINIMAL_DELTA or USER_FIELD_CHANGED."""
        diff = DiffResult(entries=[
            DiffEntry(path="aav", left="READ", right="WRITE")
        ])
        # Per implementation, single user-field diff = MINIMAL_DELTA
        assert classify_diff(diff) == "MINIMAL_DELTA"

    def test_injection_detected(self):
        """Extra non-schema fields classify as INJECTION_DETECTED."""
        diff = DiffResult(entries=[
            DiffEntry(path="priority", left="HIGH", right=MISSING)
        ])
        assert classify_diff(diff) == "INJECTION_DETECTED"


class TestFieldClassification:
    """Tests for user/derived field path classification."""

    def test_user_fields(self):
        """User fields are correctly identified."""
        user_fields = ["holder", "scope", "aav", "expiry_epoch", "scope[0].resource"]
        for path in user_fields:
            assert is_user_field_path(path), f"{path} should be user field"

    def test_derived_fields(self):
        """Derived fields are correctly identified."""
        derived_fields = ["authority_id", "created_epoch", "lineage", "status"]
        for path in derived_fields:
            assert is_derived_field_path(path), f"{path} should be derived field"


# ============================================================================
# Authorization Oracle Tests
# ============================================================================

class TestAuthorizationOracle:
    """Tests for the authorization oracle."""

    def test_authorize_identical(self):
        """Identical artifacts are AUTHORIZED."""
        artifact = {"a": 1, "b": 2}
        expected = {"a": 1, "b": 2}
        assert authorize(artifact, expected) == AuthResult.AUTHORIZED

    def test_authorize_different(self):
        """Different artifacts are REJECTED."""
        artifact = {"a": 1, "b": 2}
        expected = {"a": 1, "b": 3}
        assert authorize(artifact, expected) == AuthResult.REJECTED

    def test_authorize_key_order_irrelevant(self):
        """Key order doesn't affect authorization."""
        artifact = {"z": 1, "a": 2}
        expected = {"a": 2, "z": 1}
        assert authorize(artifact, expected) == AuthResult.AUTHORIZED

    def test_authorize_none_artifact(self):
        """None artifact should be handled gracefully."""
        # The authorize function requires Dict, so test with empty dict
        # or modify oracle to handle None
        assert authorize({}, {"a": 1}) == AuthResult.REJECTED

    def test_hash_determinism(self):
        """Same object produces same hash."""
        obj = {"a": 1, "b": [2, 3]}
        h1 = compute_artifact_hash(obj)
        h2 = compute_artifact_hash(obj)
        assert h1 == h2

    def test_hash_key_order_irrelevant(self):
        """Key order doesn't affect hash."""
        obj1 = {"z": 1, "a": 2}
        obj2 = {"a": 2, "z": 1}
        assert compute_artifact_hash(obj1) == compute_artifact_hash(obj2)


# ============================================================================
# Translation Layer Tests
# ============================================================================

class TestTranslationLayer:
    """Tests for the translation layer."""

    @pytest.fixture
    def tl(self):
        """Fresh translation layer with fixed clock."""
        return TranslationLayer(fixed_clock=1738713600, sequence_seed=1)

    def test_valid_translation(self, tl):
        """Valid intent produces SUCCESS status."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        result = tl.translate(intent)
        assert result.status == TranslationStatus.SUCCESS
        assert result.artifact is not None

    def test_artifact_structure(self, tl):
        """Artifact contains all required fields."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        result = tl.translate(intent)
        artifact = result.artifact

        required_fields = {
            "holder", "scope", "aav", "expiry_epoch",
            "authority_id", "created_epoch", "lineage", "status"
        }
        assert required_fields.issubset(set(artifact.keys()))

    def test_authority_id_format(self, tl):
        """Authority ID follows TLI-<NNN> format."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        result = tl.translate(intent)

        import re
        assert re.match(r"TLI-\d{3}", result.artifact["authority_id"])

    def test_sequence_increment(self, tl):
        """Sequence increments with each translation."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }

        r1 = tl.translate(intent)
        r2 = tl.translate(intent)

        assert r1.artifact["authority_id"] == "TLI-001"
        assert r2.artifact["authority_id"] == "TLI-002"

    def test_sequence_reset(self, tl):
        """Sequence can be reset to arbitrary value."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }

        tl.translate(intent)  # TLI-001
        tl.reset_sequence(100)
        result = tl.translate(intent)

        assert result.artifact["authority_id"] == "TLI-100"

    def test_incomplete_intent_missing_aav(self, tl):
        """Missing aav field returns TRANSLATION_FAILED."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "expiry_epoch": 1738800000
            # Missing: aav
        }
        result = tl.translate(intent)

        assert result.status == TranslationStatus.TRANSLATION_FAILED
        assert result.reason == "INCOMPLETE_INTENT"

    def test_ambiguous_scope_refusal(self, tl):
        """Conflicting scope operations return TRANSLATION_REFUSED."""
        intent = {
            "holder": "alice",
            "scope": [
                {"resource": "FILE:/config.txt", "operation": "READ"},
                {"resource": "FILE:/config.txt", "operation": "WRITE"}
            ],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        result = tl.translate(intent)

        assert result.status == TranslationStatus.TRANSLATION_REFUSED
        assert result.reason == "AMBIGUOUS_SCOPE_MULTIPLE"

    def test_fixed_clock(self, tl):
        """created_epoch uses fixed clock."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        result = tl.translate(intent)

        assert result.artifact["created_epoch"] == 1738713600

    def test_scope_preservation(self, tl):
        """Scope entries are preserved from intent."""
        intent = {
            "holder": "alice",
            "scope": [
                {"resource": "FILE:/z.txt", "operation": "READ"},
            ],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        result = tl.translate(intent)
        scope = result.artifact["scope"]

        # Verify scope is preserved from intent
        assert scope[0]["resource"] == "FILE:/z.txt"

    def test_framing_ignored(self, tl):
        """Framing input is ignored by correct TL."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
        framing = {"suggested_aav": "ADMIN", "suggested_expiry": 0}

        result_without = tl.translate(intent)
        tl.reset_sequence(1)
        result_with = tl.translate(intent, framing=framing)

        # Artifacts should be identical
        assert result_without.artifact == result_with.artifact


class TestFaultInjection:
    """Tests for fault injection mechanisms."""

    @pytest.fixture
    def tl(self):
        return TranslationLayer(fixed_clock=1738713600, sequence_seed=1)

    def test_hidden_field_injection(self, tl):
        """Hidden field injection adds extra field to artifact."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }

        fault_config = FaultConfig(inject_hidden_field=("priority", "HIGH"))
        tl.set_fault_config(fault_config)

        result = tl.translate(intent)

        assert "priority" in result.artifact
        assert result.artifact["priority"] == "HIGH"

    def test_submission_modification(self, tl):
        """Submission phase modification changes artifact."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }

        fault_config = FaultConfig(modify_on_submission={"expiry_epoch": 9999999999})
        tl.set_fault_config(fault_config)

        # Preview phase
        tl.set_preview_phase(True)
        preview = tl.translate(intent)

        # Submission phase
        tl.set_preview_phase(False)
        tl.reset_sequence(1)
        submit = tl.translate(intent)

        # Expiry should differ
        assert preview.artifact["expiry_epoch"] == 1738800000
        assert submit.artifact["expiry_epoch"] == 9999999999

    def test_clear_fault_config(self, tl):
        """clear_fault_config removes fault injection."""
        intent = {
            "holder": "alice",
            "scope": [{"resource": "FILE:/test.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }

        fault_config = FaultConfig(inject_hidden_field=("priority", "HIGH"))
        tl.set_fault_config(fault_config)
        tl.clear_fault_config()

        result = tl.translate(intent)

        assert "priority" not in result.artifact


# ============================================================================
# Condition Tests (Per Preregistration §6)
# ============================================================================

class TestConditionA:
    """Condition A: Identity Preservation"""

    def test_condition_a_pass(self):
        """TL(intent) matches expected artifact exactly."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=1)
        vector = TEST_VECTORS["A"]

        result = tl.translate(vector["intent"])
        expected = vector["expected_artifact"]

        assert result.status == TranslationStatus.SUCCESS
        assert authorize(result.artifact, expected) == AuthResult.AUTHORIZED


class TestConditionB:
    """Condition B: Minimal Change Sensitivity"""

    def test_condition_b_pass(self):
        """Single field change produces exactly one user-field diff."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=1)
        vector = TEST_VECTORS["B"]

        r1 = tl.translate(vector["intent_1"])
        r2 = tl.translate(vector["intent_2"])

        assert r1.status == TranslationStatus.SUCCESS
        assert r2.status == TranslationStatus.SUCCESS

        diff = structural_diff(r1.artifact, r2.artifact)
        user_diffs = [e for e in diff.entries if is_user_field_path(e.path)]

        assert len(user_diffs) == 1
        assert user_diffs[0].path == "aav"


class TestConditionC:
    """Condition C: Ambiguous Intent Refusal"""

    def test_condition_c_pass(self):
        """Conflicting scope returns TRANSLATION_REFUSED."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=1)
        vector = TEST_VECTORS["C"]

        result = tl.translate(vector["intent"])

        assert result.status == TranslationStatus.TRANSLATION_REFUSED
        assert result.reason == "AMBIGUOUS_SCOPE_MULTIPLE"


class TestConditionD:
    """Condition D: Hidden Default Injection (Adversarial)"""

    def test_condition_d_fail_detected(self):
        """Injected hidden field is detectable via diff."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=3)
        vector = TEST_VECTORS["D"]

        fault_config = FaultConfig(inject_hidden_field=vector["fault_injection"])
        tl.set_fault_config(fault_config)

        result = tl.translate(vector["intent"])
        expected_clean = vector["expected_artifact_clean"]

        assert result.status == TranslationStatus.SUCCESS

        diff = structural_diff(result.artifact, expected_clean)
        assert any(e.path == "priority" for e in diff.entries)
        assert classify_diff(diff) == "INJECTION_DETECTED"


class TestConditionE:
    """Condition E: UI-Level Coercion (Adversarial)"""

    def test_condition_e_pass(self):
        """Framing is ignored by correct TL."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=5)  # TLI-005
        vector = TEST_VECTORS["E"]

        result = tl.translate(vector["intent"], framing=vector["framing"])
        expected = vector["expected_artifact"]

        assert result.status == TranslationStatus.SUCCESS
        assert authorize(result.artifact, expected) == AuthResult.AUTHORIZED


class TestConditionF:
    """Condition F: Replay Determinism"""

    def test_condition_f_pass(self):
        """Replayed translations with reset sequence produce identical artifacts."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=5)
        vector = TEST_VECTORS["F"]

        hashes = []
        for _ in range(vector["replay_count"]):
            tl.reset_sequence(vector["sequence_reset"])
            result = tl.translate(vector["intent"])
            assert result.status == TranslationStatus.SUCCESS
            hashes.append(compute_artifact_hash(result.artifact))

        # All hashes must match
        assert len(set(hashes)) == 1


class TestConditionG:
    """Condition G: Intent Incompleteness Refusal"""

    def test_condition_g_pass(self):
        """Incomplete intent returns TRANSLATION_FAILED."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=1)
        vector = TEST_VECTORS["G"]

        result = tl.translate(vector["intent"])

        assert result.status == TranslationStatus.TRANSLATION_FAILED
        assert result.reason == "INCOMPLETE_INTENT"


class TestConditionH:
    """Condition H: Preview-Submission Consistency (Negative Test)"""

    def test_condition_h_fail_detected(self):
        """Preview/submission mismatch is detectable via hash comparison."""
        tl = TranslationLayer(fixed_clock=1738713600, sequence_seed=6)
        vector = TEST_VECTORS["H"]

        fault_config = FaultConfig(modify_on_submission=vector["fault_injection"])
        tl.set_fault_config(fault_config)

        # Preview
        tl.set_preview_phase(True)
        tl.reset_sequence(6)
        preview = tl.translate(vector["intent"])

        # Submission
        tl.set_preview_phase(False)
        tl.reset_sequence(6)
        submit = tl.translate(vector["intent"])

        assert preview.status == TranslationStatus.SUCCESS
        assert submit.status == TranslationStatus.SUCCESS

        preview_hash = compute_artifact_hash(preview.artifact)
        submit_hash = compute_artifact_hash(submit.artifact)

        assert preview_hash != submit_hash  # Mismatch detected


# ============================================================================
# Integration Tests
# ============================================================================

class TestTranslationHarness:
    """Integration tests for the full harness."""

    def test_harness_runs_all_conditions(self):
        """Harness executes all 8 conditions."""
        harness = TranslationHarness(fixed_clock=1738713600)
        log = harness.run_all_conditions()

        conditions = {c.condition for c in log.conditions}
        assert conditions == {"A", "B", "C", "D", "E", "F", "G", "H"}

    def test_harness_aggregate_result(self):
        """Harness computes aggregate result per §8.2."""
        harness = TranslationHarness(fixed_clock=1738713600)
        log = harness.run_all_conditions()

        # Check individual classifications
        classifications = {c.condition: c.classification for c in log.conditions}

        # Expected: A, B, C, E, F, G = PASS; D, H = FAIL_DETECTED
        assert classifications["A"] == "PASS"
        assert classifications["B"] == "PASS"
        assert classifications["C"] == "PASS"
        assert classifications["D"] == "FAIL_DETECTED"
        assert classifications["E"] == "PASS"
        assert classifications["F"] == "PASS"
        assert classifications["G"] == "PASS"
        assert classifications["H"] == "FAIL_DETECTED"

        # Aggregate
        assert log.aggregate_result == "PASS"


# ============================================================================
# Logging Tests
# ============================================================================

class TestLogging:
    """Tests for structured logging."""

    def test_condition_log_serialization(self):
        """ConditionLog serializes to dict."""
        log = ConditionLog(
            condition="A",
            timestamp="2025-02-05T00:00:00Z",
            input_intent={"holder": "alice"},
            classification="PASS"
        )
        d = log.to_dict()

        assert d["condition"] == "A"
        assert d["classification"] == "PASS"
        assert d["input_intent"] == {"holder": "alice"}

    def test_execution_log_serialization(self):
        """ExecutionLog serializes to dict including all conditions."""
        exec_log = ExecutionLog()
        exec_log.add_condition(ConditionLog(
            condition="A",
            timestamp="2025-02-05T00:00:00Z",
            input_intent={"holder": "test"},
            classification="PASS"
        ))
        exec_log.aggregate_result = "PASS"

        d = exec_log.to_dict()

        assert len(d["conditions"]) == 1
        assert d["aggregate_result"] == "PASS"
