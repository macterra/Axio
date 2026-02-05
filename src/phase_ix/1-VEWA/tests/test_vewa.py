"""
VEWA Unit Tests

Comprehensive test suite for Phase IX-1: Value Encoding Without Aggregation.
Tests all 6 conditions (A-F) plus encoding, conflict, admissibility edge cases.

Per preregistration §4 (test vectors), §7 (success criteria).
"""

import copy
import json
import sys
import os
import importlib
import pytest

# Resolve the package so relative imports within src/ work correctly.
_VEWA_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _VEWA_ROOT not in sys.path:
    sys.path.insert(0, _VEWA_ROOT)

# Import submodules explicitly using importlib to avoid __init__.py name collisions
_canonical = importlib.import_module("src.canonical")
_structural_diff = importlib.import_module("src.structural_diff")
_value_encoding = importlib.import_module("src.value_encoding")
_conflict_probe = importlib.import_module("src.conflict_probe")
_vewa_harness = importlib.import_module("src.vewa_harness")
_logging = importlib.import_module("src.logging")

# Pull symbols into local namespace
canonicalize = _canonical.canonicalize
canonicalize_bytes = _canonical.canonicalize_bytes

structural_diff = _structural_diff.structural_diff
DiffResult = _structural_diff.DiffResult
MISSING = _structural_diff.MISSING

ValueEncodingHarness = _value_encoding.ValueEncodingHarness
ValueEncodingError = _value_encoding.ValueEncodingError
VALID_OPERATIONS = _value_encoding.VALID_OPERATIONS
VALID_COMMITMENTS = _value_encoding.VALID_COMMITMENTS
FIXED_HOLDER = _value_encoding.FIXED_HOLDER
FIXED_LINEAGE_TYPE = _value_encoding.FIXED_LINEAGE_TYPE
FIXED_STATUS = _value_encoding.FIXED_STATUS

AuthorityStore = _conflict_probe.AuthorityStore
ConflictProbe = _conflict_probe.ConflictProbe
ConflictRecord = _conflict_probe.ConflictRecord
DeadlockRecord = _conflict_probe.DeadlockRecord
AdmissibilityResult = _conflict_probe.AdmissibilityResult

VEWAHarness = _vewa_harness.VEWAHarness
VEWAFaultConfig = _vewa_harness.VEWAFaultConfig
ConditionResult = _vewa_harness.ConditionResult
FIXED_CLOCK = _vewa_harness.FIXED_CLOCK
VECTOR_A = _vewa_harness.VECTOR_A
VECTOR_B = _vewa_harness.VECTOR_B
VECTOR_C = _vewa_harness.VECTOR_C
VECTOR_D = _vewa_harness.VECTOR_D
VECTOR_E = _vewa_harness.VECTOR_E
VECTOR_F = _vewa_harness.VECTOR_F

VEWAConditionLog = _logging.VEWAConditionLog
VEWAExecutionLog = _logging.VEWAExecutionLog


# ============================================================
# §2.4 Canonical Serialization Tests
# ============================================================

class TestCanonical:
    """Tests for canonical serialization per §2.4."""

    def test_key_order_lexicographic(self):
        """Keys must be lexicographically sorted."""
        obj = {"zebra": 1, "alpha": 2, "middle": 3}
        result = canonicalize(obj)
        assert result == '{"alpha":2,"middle":3,"zebra":1}'

    def test_compact_form(self):
        """No insignificant whitespace."""
        obj = {"a": 1, "b": [1, 2]}
        result = canonicalize(obj)
        assert " " not in result
        assert "\n" not in result

    def test_nested_key_order(self):
        """Nested objects also sorted."""
        obj = {"outer": {"z": 1, "a": 2}}
        result = canonicalize(obj)
        assert result == '{"outer":{"a":2,"z":1}}'

    def test_array_order_preserved(self):
        """Array order is preserved, not sorted."""
        obj = {"arr": [3, 1, 2]}
        result = canonicalize(obj)
        assert result == '{"arr":[3,1,2]}'

    def test_utf8_bytes(self):
        """canonicalize_bytes returns UTF-8."""
        obj = {"key": "value"}
        result = canonicalize_bytes(obj)
        assert isinstance(result, bytes)
        assert result == b'{"key":"value"}'


# ============================================================
# §5.1 Structural Diff Tests
# ============================================================

class TestStructuralDiff:
    """Tests for structural diff per §5.1."""

    def test_identical(self):
        """Identical objects produce 0 diffs."""
        a = {"x": 1, "y": [1, 2]}
        b = {"x": 1, "y": [1, 2]}
        result = structural_diff(a, b)
        assert result.count == 0

    def test_value_diff(self):
        """Different leaf values detected."""
        a = {"x": 1}
        b = {"x": 2}
        result = structural_diff(a, b)
        assert result.count == 1
        assert result.entries[0].path == "x"

    def test_missing_key(self):
        """Missing key detected."""
        a = {"x": 1}
        b = {"x": 1, "y": 2}
        result = structural_diff(a, b)
        assert result.count == 1
        assert result.entries[0].path == "y"

    def test_array_length_diff(self):
        """Array length difference detected."""
        a = {"arr": [1, 2]}
        b = {"arr": [1, 2, 3]}
        result = structural_diff(a, b)
        assert result.count == 1
        assert result.entries[0].path == "arr[2]"

    def test_nested_diff(self):
        """Nested object diff uses dot notation."""
        a = {"outer": {"inner": 1}}
        b = {"outer": {"inner": 2}}
        result = structural_diff(a, b)
        assert result.count == 1
        assert result.entries[0].path == "outer.inner"

    def test_extra_field_detection(self):
        """Extra field produces diff entry."""
        a = {"x": 1}
        b = {"x": 1, "priority": 1}
        result = structural_diff(a, b)
        assert result.count == 1
        assert result.entries[0].path == "priority"


# ============================================================
# §2.1 / §2.5 Value Encoding Tests
# ============================================================

class TestValueEncoding:
    """Tests for VEH per §2.1, §2.5."""

    def setup_method(self):
        self.veh = ValueEncodingHarness(fixed_clock=FIXED_CLOCK)

    def test_single_value_encoding(self):
        """§4.1 VECTOR_A: single value produces correct artifact."""
        value = {
            "value_id": "V_OPEN",
            "scope": [{"target": "FILE:/data/report.txt", "operation": "READ"}],
            "commitment": "ALLOW",
        }
        artifact = self.veh.encode_value(value)

        expected = VECTOR_A["expected_artifacts"][0]
        diff = structural_diff(artifact, expected)
        assert diff.count == 0, f"Encoding mismatch: {[(e.path, e.left, e.right) for e in diff.entries]}"

    def test_bijection_one_to_one(self):
        """One value → exactly one artifact (§2.5 bijection)."""
        values = [
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T2", "operation": "WRITE"}], "commitment": "DENY"},
        ]
        artifacts = self.veh.encode(values)
        assert len(artifacts) == 2
        # Different authority_ids
        assert artifacts[0]["authority_id"] != artifacts[1]["authority_id"]

    def test_sequence_counter(self):
        """Authority IDs use VEWA-<NNN> format with incrementing counter."""
        values = [
            {"value_id": f"V{i}", "scope": [{"target": f"T{i}", "operation": "READ"}], "commitment": "ALLOW"}
            for i in range(3)
        ]
        artifacts = self.veh.encode(values)
        assert artifacts[0]["authority_id"] == "VEWA-001"
        assert artifacts[1]["authority_id"] == "VEWA-002"
        assert artifacts[2]["authority_id"] == "VEWA-003"

    def test_sequence_reset(self):
        """reset_sequence resets counter per §6.2."""
        self.veh.encode_value(
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"}
        )
        assert self.veh.current_sequence == 2
        self.veh.reset_sequence(1)
        assert self.veh.current_sequence == 1
        artifact = self.veh.encode_value(
            {"value_id": "V2", "scope": [{"target": "T2", "operation": "READ"}], "commitment": "ALLOW"}
        )
        assert artifact["authority_id"] == "VEWA-001"

    def test_fixed_fields(self):
        """All fixed fields per §2.5 encoding table."""
        value = {
            "value_id": "V_TEST",
            "scope": [{"target": "T", "operation": "WRITE"}],
            "commitment": "DENY",
        }
        artifact = self.veh.encode_value(value)

        assert artifact["holder"] == "VALUE_AUTHORITY"
        assert artifact["lineage"]["type"] == "VALUE_DECLARATION"
        assert artifact["lineage"]["encoding_epoch"] == 0
        assert artifact["expiry_epoch"] == 0
        assert artifact["status"] == "ACTIVE"
        assert artifact["created_epoch"] == FIXED_CLOCK

    def test_passthrough_fields(self):
        """User-specified fields pass through without modification (§2.5)."""
        value = {
            "value_id": "V_PASS",
            "scope": [{"target": "FILE:/path", "operation": "ADMIN"}],
            "commitment": "DENY",
        }
        artifact = self.veh.encode_value(value)

        assert artifact["commitment"] == "DENY"
        assert artifact["aav"] == "ADMIN"
        assert artifact["scope"] == value["scope"]
        assert artifact["lineage"]["value_id"] == "V_PASS"

    def test_aav_from_scope_operation(self):
        """aav is mapped from scope[0].operation (§2.5)."""
        for op in VALID_OPERATIONS:
            self.veh.reset_sequence(1)
            value = {
                "value_id": f"V_{op}",
                "scope": [{"target": "T", "operation": op}],
                "commitment": "ALLOW",
            }
            artifact = self.veh.encode_value(value)
            assert artifact["aav"] == op

    def test_canonical_field_order(self):
        """Artifact fields are in canonical (lexicographic) order per §2.4."""
        value = {
            "value_id": "V_ORDER",
            "scope": [{"target": "T", "operation": "READ"}],
            "commitment": "ALLOW",
        }
        artifact = self.veh.encode_value(value)
        canonical_json = canonicalize(artifact)
        reparsed = json.loads(canonical_json)

        # Verify key order in canonical serialization
        expected_order = [
            "aav", "authority_id", "commitment", "created_epoch",
            "expiry_epoch", "holder", "lineage", "scope", "status"
        ]
        actual_keys = list(json.loads(canonical_json).keys())
        assert actual_keys == expected_order

    # --- Validation error tests ---

    def test_missing_required_field(self):
        """Missing required field raises error."""
        with pytest.raises(ValueEncodingError, match="Missing required fields"):
            self.veh.encode_value({"value_id": "V1", "scope": []})

    def test_extra_field_forbidden(self):
        """Additional properties forbidden per §2.1."""
        with pytest.raises(ValueEncodingError, match="Forbidden additional fields"):
            self.veh.encode_value({
                "value_id": "V1",
                "scope": [{"target": "T", "operation": "READ"}],
                "commitment": "ALLOW",
                "name": "forbidden",
            })

    def test_invalid_commitment(self):
        """Invalid commitment value raises error."""
        with pytest.raises(ValueEncodingError, match="commitment must be"):
            self.veh.encode_value({
                "value_id": "V1",
                "scope": [{"target": "T", "operation": "READ"}],
                "commitment": "MAYBE",
            })

    def test_invalid_operation(self):
        """Invalid operation raises error."""
        with pytest.raises(ValueEncodingError, match="operation must be"):
            self.veh.encode_value({
                "value_id": "V1",
                "scope": [{"target": "T", "operation": "DELETE"}],
                "commitment": "ALLOW",
            })

    def test_multi_scope_atom_forbidden(self):
        """Multiple scope atoms forbidden (maxItems: 1)."""
        with pytest.raises(ValueEncodingError, match="maxItems: 1"):
            self.veh.encode_value({
                "value_id": "V1",
                "scope": [
                    {"target": "T1", "operation": "READ"},
                    {"target": "T2", "operation": "WRITE"},
                ],
                "commitment": "ALLOW",
            })

    def test_empty_scope_forbidden(self):
        """Empty scope forbidden (minItems: 1)."""
        with pytest.raises(ValueEncodingError, match="minItems: 1"):
            self.veh.encode_value({
                "value_id": "V1",
                "scope": [],
                "commitment": "ALLOW",
            })

    def test_scope_atom_extra_field_forbidden(self):
        """Scope atom additional properties forbidden."""
        with pytest.raises(ValueEncodingError, match="forbidden additional fields"):
            self.veh.encode_value({
                "value_id": "V1",
                "scope": [{"target": "T", "operation": "READ", "extra": "bad"}],
                "commitment": "ALLOW",
            })


# ============================================================
# §2.6 / §2.7 Conflict Detection and Admissibility Tests
# ============================================================

class TestConflictProbe:
    """Tests for conflict detection and admissibility per §2.6, §2.7."""

    def setup_method(self):
        self.store = AuthorityStore()
        self.probe = ConflictProbe(self.store)
        self.veh = ValueEncodingHarness(fixed_clock=FIXED_CLOCK)

    def _inject_values(self, values):
        """Helper: encode and inject values."""
        artifacts = self.veh.encode(values)
        for a in artifacts:
            self.store.inject(a)
        return artifacts

    def test_no_conflict_disjoint_scopes(self):
        """Disjoint scopes produce no conflict (Condition B)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T2", "operation": "WRITE"}], "commitment": "ALLOW"},
        ])
        conflicts = self.probe.detect_conflicts()
        assert len(conflicts) == 0

    def test_no_conflict_allow_allow(self):
        """ALLOW + ALLOW on same scope is not a conflict (§2.6)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
        ])
        conflicts = self.probe.detect_conflicts()
        assert len(conflicts) == 0

    def test_conflict_allow_deny(self):
        """ALLOW + DENY on same scope is a conflict (§2.6)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        conflicts = self.probe.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "MULTI_BINDING"

    def test_conflict_deny_deny(self):
        """DENY + DENY on same scope is a conflict (§2.6 non-collapse discipline)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        conflicts = self.probe.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "MULTI_BINDING"

    def test_conflict_record_unordered_set(self):
        """Conflict record authorities are an unordered set (§2.6)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        conflicts = self.probe.detect_conflicts()
        assert len(conflicts) == 1
        # authorities is a set (unordered)
        assert isinstance(conflicts[0].authorities, set)
        assert len(conflicts[0].authorities) == 2

    def test_conflict_serialization_sorted(self):
        """Conflict to_dict serializes authorities as sorted array (§2.6 Set Serialization Rule)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        conflicts = self.probe.detect_conflicts()
        d = conflicts[0].to_dict()
        assert d["authorities"] == sorted(d["authorities"])

    def test_conflict_persists(self):
        """Conflict records persist (§2.6 Conflict Timing)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        self.probe.detect_conflicts()
        # Still conflicted after detection
        assert self.probe.is_scope_conflicted("T1", "READ")

    # --- Admissibility tests ---

    def test_admissibility_single_allow(self):
        """Single ALLOW → ACTION_ADMISSIBLE (§2.7 step 4)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
        ])
        self.probe.detect_conflicts()
        result = self.probe.evaluate_admissibility({"target": "T1", "operation": "READ"})
        assert result.result == "ACTION_ADMISSIBLE"
        assert result.reason is None

    def test_admissibility_no_authority(self):
        """No matching authority → ACTION_REFUSED / NO_AUTHORITY (§2.7 step 2)."""
        result = self.probe.evaluate_admissibility({"target": "T_NONE", "operation": "READ"})
        assert result.result == "ACTION_REFUSED"
        assert result.reason == "NO_AUTHORITY"

    def test_admissibility_conflict_refused(self):
        """Conflicted scope → ACTION_REFUSED / VALUE_CONFLICT (§2.7 step 3)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        self.probe.detect_conflicts()
        result = self.probe.evaluate_admissibility({"target": "T1", "operation": "READ"})
        assert result.result == "ACTION_REFUSED"
        assert result.reason == "VALUE_CONFLICT"

    def test_admissibility_all_deny(self):
        """All DENY, no conflict → ACTION_REFUSED / DENIED_BY_AUTHORITY (§2.7 step 5)."""
        # Single DENY (no conflict since only one authority)
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        self.probe.detect_conflicts()
        result = self.probe.evaluate_admissibility({"target": "T1", "operation": "READ"})
        assert result.result == "ACTION_REFUSED"
        assert result.reason == "DENIED_BY_AUTHORITY"

    def test_admissibility_allow_allow_no_conflict(self):
        """ALLOW + ALLOW → ACTION_ADMISSIBLE, no conflict (§2.6, §2.7)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
        ])
        self.probe.detect_conflicts()
        result = self.probe.evaluate_admissibility({"target": "T1", "operation": "READ"})
        assert result.result == "ACTION_ADMISSIBLE"
        assert result.reason is None

    # --- Deadlock tests ---

    def test_deadlock_on_conflict(self):
        """Conflicted scope with no admissible action → deadlock (§2.7)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ])
        self.probe.detect_conflicts()
        actions = [{"target": "T1", "operation": "READ"}]
        deadlocks = self.probe.check_deadlock(actions)
        assert len(deadlocks) == 1
        assert deadlocks[0].status == "STATE_DEADLOCK / VALUE_CONFLICT"

    def test_no_deadlock_without_conflict(self):
        """No conflict → no deadlock."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
        ])
        self.probe.detect_conflicts()
        actions = [{"target": "T1", "operation": "READ"}]
        deadlocks = self.probe.check_deadlock(actions)
        assert len(deadlocks) == 0

    def test_deadlock_scope_bound(self):
        """Deadlock only on contested scope, not on uncontested (§2.7)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
            {"value_id": "V3", "scope": [{"target": "T2", "operation": "WRITE"}], "commitment": "ALLOW"},
        ])
        self.probe.detect_conflicts()

        # T1 READ is conflicted, T2 WRITE is not
        actions = [
            {"target": "T1", "operation": "READ"},
            {"target": "T2", "operation": "WRITE"},
        ]
        deadlocks = self.probe.check_deadlock(actions)
        assert len(deadlocks) == 1
        assert deadlocks[0].scope_atom["target"] == "T1"

        # T2 is still admissible
        r = self.probe.evaluate_admissibility({"target": "T2", "operation": "WRITE"})
        assert r.result == "ACTION_ADMISSIBLE"

    # --- Authority Store tests ---

    def test_store_reinitialize(self):
        """Reinitialize clears all state (§6.1 step a)."""
        self._inject_values([
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "ALLOW"},
        ])
        assert len(self.store.get_all_artifacts()) == 1
        self.store.reinitialize()
        assert len(self.store.get_all_artifacts()) == 0
        assert not self.store.epoch_closed

    def test_epoch_closure_blocks_injection(self):
        """Post-epoch injection returns synthesis error (§1.3)."""
        self.store.close_epoch()
        result = self.store.inject({"authority_id": "VEWA-999", "foo": "bar"})
        assert result == "IX1_FAIL / VALUE_SYNTHESIS"

    def test_artifact_schema_validation(self):
        """validate_artifact_schema detects extra fields (Condition D)."""
        artifact = {
            "aav": "READ", "authority_id": "VEWA-001", "commitment": "ALLOW",
            "created_epoch": 0, "expiry_epoch": 0, "holder": "VALUE_AUTHORITY",
            "lineage": {"encoding_epoch": 0, "type": "VALUE_DECLARATION", "value_id": "V1"},
            "scope": [{"operation": "READ", "target": "T"}], "status": "ACTIVE",
            "priority": 1,  # injected forbidden field
        }
        extra = self.probe.validate_artifact_schema(artifact)
        assert extra == ["priority"]

    def test_scope_atom_canonicalized_matching(self):
        """Scope atom matching uses canonicalized equality (§2.4)."""
        # Inject with one key order
        self.store.inject({
            "authority_id": "VEWA-001",
            "scope": [{"target": "FILE:/x", "operation": "READ"}],
            "aav": "READ", "commitment": "ALLOW", "holder": "VALUE_AUTHORITY",
            "lineage": {"type": "VALUE_DECLARATION", "value_id": "V1", "encoding_epoch": 0},
            "created_epoch": FIXED_CLOCK, "expiry_epoch": 0, "status": "ACTIVE",
        })
        # Query with same values (canonicalized matching)
        matches = self.store.find_by_scope_atom("FILE:/x", "READ")
        assert len(matches) == 1


# ============================================================
# §3.1 / §4 / §7 Condition Tests (via Harness)
# ============================================================

class TestConditionA:
    """Condition A: Single Value Admissibility (§4.1)."""

    def test_condition_a_passes(self):
        harness = VEWAHarness()
        result = harness.execute_condition_a()
        assert result.experiment_result == "PASS"
        assert "IX1_PASS" in result.classification

    def test_condition_a_encoding_correct(self):
        """Artifact matches expected per VECTOR_A."""
        harness = VEWAHarness()
        result = harness.execute_condition_a()
        diffs = result.log.structural_diffs
        assert all(d["count"] == 0 for d in diffs)

    def test_condition_a_no_conflict(self):
        harness = VEWAHarness()
        result = harness.execute_condition_a()
        assert len(result.log.conflict_records) == 0

    def test_condition_a_admissible(self):
        harness = VEWAHarness()
        result = harness.execute_condition_a()
        assert all(
            a["result"] == "ACTION_ADMISSIBLE"
            for a in result.log.admissibility_results
        )

    def test_condition_a_no_deadlock(self):
        harness = VEWAHarness()
        result = harness.execute_condition_a()
        assert len(result.log.deadlock_records) == 0


class TestConditionB:
    """Condition B: Multiple Non-Conflicting Values (§4.2)."""

    def test_condition_b_passes(self):
        harness = VEWAHarness()
        result = harness.execute_condition_b()
        assert result.experiment_result == "PASS"

    def test_condition_b_two_artifacts(self):
        harness = VEWAHarness()
        result = harness.execute_condition_b()
        assert len(result.log.encoded_artifacts) == 2
        ids = {a["authority_id"] for a in result.log.encoded_artifacts}
        assert len(ids) == 2  # distinct

    def test_condition_b_no_conflict(self):
        harness = VEWAHarness()
        result = harness.execute_condition_b()
        assert len(result.log.conflict_records) == 0

    def test_condition_b_both_admissible(self):
        harness = VEWAHarness()
        result = harness.execute_condition_b()
        assert len(result.log.admissibility_results) == 2
        assert all(
            a["result"] == "ACTION_ADMISSIBLE"
            for a in result.log.admissibility_results
        )


class TestConditionC:
    """Condition C: Conflicting Values — Deadlock (§4.3)."""

    def test_condition_c_passes(self):
        harness = VEWAHarness()
        result = harness.execute_condition_c()
        assert result.experiment_result == "PASS"

    def test_condition_c_conflict_registered(self):
        harness = VEWAHarness()
        result = harness.execute_condition_c()
        assert len(result.log.conflict_records) == 1
        cr = result.log.conflict_records[0]
        assert cr["conflict_type"] == "MULTI_BINDING"
        assert len(cr["authorities"]) == 2

    def test_condition_c_action_refused(self):
        harness = VEWAHarness()
        result = harness.execute_condition_c()
        assert all(
            a["result"] == "ACTION_REFUSED"
            for a in result.log.admissibility_results
        )
        assert all(
            a["reason"] == "VALUE_CONFLICT"
            for a in result.log.admissibility_results
        )

    def test_condition_c_deadlock(self):
        harness = VEWAHarness()
        result = harness.execute_condition_c()
        assert len(result.log.deadlock_records) == 1
        assert result.log.deadlock_records[0]["status"] == "STATE_DEADLOCK / VALUE_CONFLICT"

    def test_condition_c_conflict_persists(self):
        """Conflict record references both authorities as unordered set."""
        harness = VEWAHarness()
        result = harness.execute_condition_c()
        cr = result.log.conflict_records[0]
        # Both authority IDs present
        assert set(cr["authorities"]) == {"VEWA-001", "VEWA-002"}


class TestConditionD:
    """Condition D: Aggregation Attempt — Adversarial (§4.4)."""

    def test_condition_d_passes(self):
        """Adversarial detection = experiment PASS (§3.3)."""
        harness = VEWAHarness()
        result = harness.execute_condition_d()
        assert result.experiment_result == "PASS"

    def test_condition_d_kernel_emits_fail(self):
        """Kernel classification is IX1_FAIL / VALUE_AGGREGATION."""
        harness = VEWAHarness()
        result = harness.execute_condition_d()
        assert "IX1_FAIL / VALUE_AGGREGATION" in result.classification

    def test_condition_d_detects_priority_field(self):
        """System detects the injected 'priority' field."""
        harness = VEWAHarness()
        result = harness.execute_condition_d()
        assert "priority" in result.classification_reason


class TestConditionE:
    """Condition E: Permutation Invariance (§4.5)."""

    def test_condition_e_passes(self):
        """Permutation invariance holds — PASS."""
        harness = VEWAHarness()
        result = harness.execute_condition_e()
        assert result.experiment_result == "PASS"

    def test_condition_e_no_implicit_value(self):
        """No IX1_FAIL / IMPLICIT_VALUE emitted."""
        harness = VEWAHarness()
        result = harness.execute_condition_e()
        assert "IMPLICIT_VALUE" not in result.classification

    def test_condition_e_both_runs_logged(self):
        """Both permutation runs are logged."""
        harness = VEWAHarness()
        result = harness.execute_condition_e()
        # Both runs' artifacts logged (4 total: 2 per run)
        assert len(result.log.encoded_artifacts) == 4

    def test_condition_e_invariant_criterion(self):
        """
        Verify permutation invariance per §3.4:
        - Same scope atoms
        - Same admissibility results/reasons
        - Same value_id sets in conflicts
        """
        harness = VEWAHarness()
        result = harness.execute_condition_e()
        # All admissibility results should be ACTION_REFUSED / VALUE_CONFLICT
        for a in result.log.admissibility_results:
            assert a["result"] == "ACTION_REFUSED"
            assert a["reason"] == "VALUE_CONFLICT"


class TestConditionF:
    """Condition F: Meta-Authority Synthesis Attempt — Adversarial (§4.6)."""

    def test_condition_f_passes(self):
        """Adversarial detection = experiment PASS (§3.3)."""
        harness = VEWAHarness()
        result = harness.execute_condition_f()
        assert result.experiment_result == "PASS"

    def test_condition_f_kernel_emits_fail(self):
        """Kernel classification is IX1_FAIL / VALUE_SYNTHESIS."""
        harness = VEWAHarness()
        result = harness.execute_condition_f()
        assert "IX1_FAIL / VALUE_SYNTHESIS" in result.classification

    def test_condition_f_post_epoch_blocked(self):
        """Post-epoch injection is blocked."""
        harness = VEWAHarness()
        result = harness.execute_condition_f()
        assert "blocked" in result.classification_reason.lower()


# ============================================================
# §7.2 Aggregate Success Test
# ============================================================

class TestAggregateExecution:
    """Full execution of all conditions (§7.2)."""

    def test_all_conditions_pass(self):
        """All 6 conditions pass → IX1_PASS / VALUE_ENCODING_ESTABLISHED."""
        harness = VEWAHarness()
        log = harness.execute_all()
        assert "IX1_PASS" in log.aggregate_result
        assert "VALUE_ENCODING_ESTABLISHED" in log.aggregate_result

    def test_all_conditions_executed(self):
        """All 6 conditions are present in log."""
        harness = VEWAHarness()
        log = harness.execute_all()
        conditions = [c.condition for c in log.conditions]
        assert conditions == ["A", "B", "C", "D", "E", "F"]

    def test_all_conditions_experiment_pass(self):
        """Each condition's experiment_result is PASS."""
        harness = VEWAHarness()
        log = harness.execute_all()
        for c in log.conditions:
            assert c.experiment_result == "PASS", (
                f"Condition {c.condition} failed: "
                f"{c.classification} — {c.classification_reason}"
            )

    def test_replay_determinism(self):
        """Two consecutive runs produce identical results (§6.2 Replay Rule)."""
        h1 = VEWAHarness()
        h2 = VEWAHarness()
        log1 = h1.execute_all()
        log2 = h2.execute_all()

        for c1, c2 in zip(log1.conditions, log2.conditions):
            assert c1.classification == c2.classification
            assert c1.classification_reason == c2.classification_reason
            assert c1.experiment_result == c2.experiment_result
            assert c1.encoded_artifacts == c2.encoded_artifacts
            assert c1.conflict_records == c2.conflict_records
            assert c1.admissibility_results == c2.admissibility_results
            assert c1.deadlock_records == c2.deadlock_records


# ============================================================
# §6.3 Logging Tests
# ============================================================

class TestLogging:
    """Tests for logging schema per §6.3."""

    def test_condition_log_has_required_fields(self):
        """VEWAConditionLog has all §6.3 fields."""
        log = VEWAConditionLog(condition="A", timestamp="2026-02-05T00:00:00Z")
        d = log.to_dict()
        required = {
            "condition", "timestamp", "value_declarations", "encoded_artifacts",
            "expected_artifacts", "candidate_actions", "fault_injection",
            "conflict_records", "admissibility_results", "deadlock_records",
            "structural_diffs", "classification", "classification_reason",
            "experiment_result", "notes",
        }
        assert required.issubset(set(d.keys()))

    def test_admissibility_reason_enum(self):
        """Admissibility reasons are from the enum (§6.3)."""
        valid_reasons = {None, "NO_AUTHORITY", "VALUE_CONFLICT", "DENIED_BY_AUTHORITY"}
        harness = VEWAHarness()
        log = harness.execute_all()
        for c in log.conditions:
            for a in c.admissibility_results:
                assert a["reason"] in valid_reasons, (
                    f"Invalid reason {a['reason']!r} in condition {c.condition}"
                )

    def test_execution_log_serializable(self):
        """Full execution log serializes to valid JSON."""
        harness = VEWAHarness()
        log = harness.execute_all()
        json_str = log.to_json()
        parsed = json.loads(json_str)
        assert parsed["phase"] == "IX-1"
        assert parsed["subphase"] == "VEWA"
        assert len(parsed["conditions"]) == 6


# ============================================================
# Edge case tests
# ============================================================

class TestEdgeCases:
    """Edge cases and invariant tests."""

    def test_condition_isolation(self):
        """Each condition starts with clean state (§6.1 step a)."""
        harness = VEWAHarness()
        # Run C (creates conflicts), then A (should have none)
        harness.execute_condition_c()
        result = harness.execute_condition_a()
        assert result.experiment_result == "PASS"
        assert len(result.log.conflict_records) == 0

    def test_sequence_resets_between_conditions(self):
        """Sequence counter resets to 001 per condition (§6.2)."""
        harness = VEWAHarness()
        r_a = harness.execute_condition_a()
        r_b = harness.execute_condition_b()
        # Both start with VEWA-001
        assert r_a.log.encoded_artifacts[0]["authority_id"] == "VEWA-001"
        assert r_b.log.encoded_artifacts[0]["authority_id"] == "VEWA-001"

    def test_no_action_executed_token(self):
        """ACTION_EXECUTED never appears (§2.8 forbidden outputs)."""
        harness = VEWAHarness()
        log = harness.execute_all()
        for c in log.conditions:
            for a in c.admissibility_results:
                assert a["result"] != "ACTION_EXECUTED"

    def test_deny_deny_conflict(self):
        """DENY + DENY produces conflict, not reinforced denial (§2.6)."""
        store = AuthorityStore()
        probe = ConflictProbe(store)
        veh = ValueEncodingHarness(fixed_clock=FIXED_CLOCK)

        values = [
            {"value_id": "V1", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
            {"value_id": "V2", "scope": [{"target": "T1", "operation": "READ"}], "commitment": "DENY"},
        ]
        for a in veh.encode(values):
            store.inject(a)

        conflicts = probe.detect_conflicts()
        assert len(conflicts) == 1

        # Admissibility should be VALUE_CONFLICT, not DENIED_BY_AUTHORITY
        result = probe.evaluate_admissibility({"target": "T1", "operation": "READ"})
        assert result.result == "ACTION_REFUSED"
        assert result.reason == "VALUE_CONFLICT"

    def test_conflict_type_is_multi_binding(self):
        """conflict_type is always MULTI_BINDING (§2.6, S1 patch)."""
        store = AuthorityStore()
        probe = ConflictProbe(store)
        veh = ValueEncodingHarness(fixed_clock=FIXED_CLOCK)

        for commitment_pair in [("ALLOW", "DENY"), ("DENY", "DENY")]:
            store.reinitialize()
            probe.reinitialize()
            veh.reset_sequence(1)
            values = [
                {"value_id": "V1", "scope": [{"target": "T", "operation": "READ"}], "commitment": commitment_pair[0]},
                {"value_id": "V2", "scope": [{"target": "T", "operation": "READ"}], "commitment": commitment_pair[1]},
            ]
            for a in veh.encode(values):
                store.inject(a)
            conflicts = probe.detect_conflicts()
            assert len(conflicts) == 1
            assert conflicts[0].conflict_type == "MULTI_BINDING"
