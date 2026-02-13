"""
RSA-0 X-0E — Test Suite

Covers spec §12–§17 closure criteria:
  1. rsa run produces side effect under warrant gating
  2. rsa replay reconstructs identical state hashes
  3. No side effect without warrant
  4. Destination idempotency enforced
  5. Logs sufficient for deterministic reconstruction
  6. Constitution hash validation enforced
  7. Kernel authority semantics unchanged
  8. Test vector reproducible across runs
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Ensure RSA-0 root is importable
import sys

RSA0_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RSA0_ROOT))

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    InternalState,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
)
from kernel.src.canonical import canonical_bytes, canonical_str
from kernel.src.constitution import Constitution, ConstitutionError
from kernel.src.hashing import content_hash
from kernel.src.state_hash import (
    KERNEL_VERSION_ID,
    component_hash,
    cycle_state_hash,
    initial_state_hash,
    state_hash_hex,
)
from host.log_io import append_jsonl, read_jsonl, read_jsonl_by_cycle, extract_warrant_ids
from host.executor_x0e import ExecutorX0E
from cli.commands.run import run
from cli.commands.replay import replay, ReplayReport


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CONSTITUTION_PATH = RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.1.1.yaml"
OBSERVATION_STREAM = RSA0_ROOT / "tests" / "fixtures" / "x0e_end_to_end_vector" / "observation_stream.jsonl"
EXPECTED_HASHES = RSA0_ROOT / "tests" / "fixtures" / "x0e_end_to_end_vector" / "expected_state_hashes.jsonl"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_log_dir(tmp_path):
    """Provide a clean temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def run_result(tmp_log_dir):
    """Execute rsa run on the test vector and return (exit_code, log_dir)."""
    rc = run(
        constitution_path=str(CONSTITUTION_PATH),
        log_dir=str(tmp_log_dir),
        observations_path=str(OBSERVATION_STREAM),
    )
    return rc, tmp_log_dir


# ===================================================================
# § JCS Canonicalization
# ===================================================================

class TestJCSCanonicalization:
    """Verify RFC 8785 conformance for our data subset."""

    def test_sorted_keys(self):
        val = {"z": 1, "a": 2}
        result = canonical_str(val)
        assert result == '{"a":2,"z":1}'

    def test_nested_sorted_keys(self):
        val = {"b": {"z": 1, "a": 2}, "a": 3}
        result = canonical_str(val)
        assert result == '{"a":3,"b":{"a":2,"z":1}}'

    def test_unicode_preserved(self):
        val = {"key": "héllo wörld"}
        result = canonical_str(val)
        assert "héllo wörld" in result

    def test_integer_serialization(self):
        val = {"n": 42}
        assert canonical_str(val) == '{"n":42}'

    def test_boolean_serialization(self):
        val = {"t": True, "f": False}
        result = canonical_str(val)
        assert '"f":false' in result
        assert '"t":true' in result

    def test_null_serialization(self):
        val = {"n": None}
        assert canonical_str(val) == '{"n":null}'

    def test_array_serialization(self):
        val = {"a": [3, 1, 2]}
        assert canonical_str(val) == '{"a":[3,1,2]}'

    def test_empty_object(self):
        assert canonical_str({}) == "{}"

    def test_empty_array(self):
        assert canonical_str([]) == "[]"

    def test_canonical_bytes_utf8(self):
        val = {"key": "value"}
        b = canonical_bytes(val)
        assert isinstance(b, bytes)
        assert b == canonical_str(val).encode("utf-8")


# ===================================================================
# § Content Hashing
# ===================================================================

class TestContentHash:
    """Verify artifact hashing determinism."""

    def test_content_hash_deterministic(self):
        val = {"action_type": "Notify", "fields": {"target": "stdout"}}
        h1 = content_hash(val)
        h2 = content_hash(val)
        assert h1 == h2

    def test_content_hash_key_order_independent(self):
        h1 = content_hash({"b": 2, "a": 1})
        h2 = content_hash({"a": 1, "b": 2})
        assert h1 == h2

    def test_content_hash_is_sha256_hex(self):
        h = content_hash({"test": True})
        assert len(h) == 64
        int(h, 16)  # must be valid hex


# ===================================================================
# § State Hash Chain
# ===================================================================

class TestStateHashChain:
    """Verify state hash chain computation per spec §11."""

    def test_initial_state_hash_deterministic(self):
        const_hash = "ad6aa7ccb0ed27151423486b60de380da9d34436f6c5554da84f3a092902740f"
        h1 = initial_state_hash(const_hash)
        h2 = initial_state_hash(const_hash)
        assert h1 == h2

    def test_initial_state_hash_length(self):
        const_hash = "a" * 64
        h = initial_state_hash(const_hash)
        assert len(h) == 32  # raw bytes

    def test_different_constitution_different_hash(self):
        h1 = initial_state_hash("a" * 64)
        h2 = initial_state_hash("b" * 64)
        assert h1 != h2

    def test_different_version_different_hash(self):
        ch = "a" * 64
        h1 = initial_state_hash(ch, "v1")
        h2 = initial_state_hash(ch, "v2")
        assert h1 != h2

    def test_component_hash_empty_list(self):
        h = component_hash([])
        assert len(h) == 32
        # Should be SHA256(JCS([]))
        expected = hashlib.sha256(canonical_bytes([])).digest()
        assert h == expected

    def test_component_hash_deterministic(self):
        records = [{"cycle_id": 0, "result": "admitted"}]
        h1 = component_hash(records)
        h2 = component_hash(records)
        assert h1 == h2

    def test_cycle_state_hash_changes_with_data(self):
        prev = b"\x00" * 32
        h1 = cycle_state_hash(prev, [], [], [], [])
        h2 = cycle_state_hash(prev, [{"x": 1}], [], [], [])
        assert h1 != h2

    def test_state_hash_hex_format(self):
        raw = b"\x00" * 32
        hexstr = state_hash_hex(raw)
        assert len(hexstr) == 64
        assert hexstr == "0" * 64


# ===================================================================
# § Constitution Integrity (spec §13.1)
# ===================================================================

class TestConstitutionIntegrity:
    """Verify constitution loading and hash validation."""

    def test_load_valid_constitution(self):
        c = Constitution(str(CONSTITUTION_PATH))
        assert c.version == "0.1.1"
        assert len(c.sha256) == 64

    def test_constitution_hash_matches_sidecar(self):
        c = Constitution(str(CONSTITUTION_PATH))
        sidecar_path = CONSTITUTION_PATH.parent / "rsa_constitution.v0.1.1.sha256"
        expected = sidecar_path.read_text().strip().split()[0]
        assert c.sha256 == expected

    def test_constitution_citation_resolution(self):
        c = Constitution(str(CONSTITUTION_PATH))
        node = c.resolve_citation("constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT")
        assert node is not None
        assert node["id"] == "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"

    def test_tampered_constitution_rejected(self, tmp_path):
        """Constitution with wrong bytes should fail hash check."""
        # Copy constitution and tamper
        tampered = tmp_path / "rsa_constitution.v0.1.1.yaml"
        original = CONSTITUTION_PATH.read_bytes()
        tampered.write_bytes(original + b"\n# tampered")

        # Copy sidecar (with original hash)
        sidecar = tmp_path / "rsa_constitution.v0.1.1.sha256"
        original_sidecar = CONSTITUTION_PATH.parent / "rsa_constitution.v0.1.1.sha256"
        shutil.copy2(original_sidecar, sidecar)

        with pytest.raises(ConstitutionError, match="hash mismatch"):
            Constitution(str(tampered))


# ===================================================================
# § Log I/O
# ===================================================================

class TestLogIO:
    """Verify append-only JSONL I/O."""

    def test_append_and_read(self, tmp_path):
        p = tmp_path / "test.jsonl"
        append_jsonl(p, {"a": 1})
        append_jsonl(p, {"b": 2})
        records = read_jsonl(p)
        assert len(records) == 2
        assert records[0] == {"a": 1}
        assert records[1] == {"b": 2}

    def test_read_missing_file(self, tmp_path):
        p = tmp_path / "nonexistent.jsonl"
        assert read_jsonl(p) == []

    def test_read_by_cycle(self, tmp_path):
        p = tmp_path / "test.jsonl"
        append_jsonl(p, {"cycle_id": 0, "x": 1})
        append_jsonl(p, {"cycle_id": 0, "x": 2})
        append_jsonl(p, {"cycle_id": 1, "x": 3})
        by_cycle = read_jsonl_by_cycle(p)
        assert len(by_cycle[0]) == 2
        assert len(by_cycle[1]) == 1

    def test_extract_warrant_ids(self, tmp_path):
        p = tmp_path / "test.jsonl"
        append_jsonl(p, {"warrant_id": "abc", "x": 1})
        append_jsonl(p, {"warrant_id": "def", "x": 2})
        append_jsonl(p, {"x": 3})  # no warrant_id
        ids = extract_warrant_ids(p)
        assert ids == {"abc", "def"}

    def test_append_is_canonical(self, tmp_path):
        """Appended JSON must be canonically serialized."""
        p = tmp_path / "test.jsonl"
        append_jsonl(p, {"z": 1, "a": 2})
        raw = p.read_text("utf-8").strip()
        assert raw == '{"a":2,"z":1}'


# ===================================================================
# § Executor (spec §6)
# ===================================================================

class TestExecutorX0E:
    """Verify warrant-gated execution."""

    def _make_warrant(self, action_type="Notify", cycle=0, ts="2025-01-15T00:00:00Z"):
        from kernel.src.artifacts import ExecutionWarrant
        return ExecutionWarrant(
            action_request_id="test-ar-id",
            action_type=action_type,
            scope_constraints={"target": "stdout"},
            issued_in_cycle=cycle,
            created_at=ts,
        )

    def _make_bundle(self, message="test message", ts="2025-01-15T00:00:00Z"):
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": message},
            author=Author.REFLECTION.value,
            created_at=ts,
        )
        return CandidateBundle(
            action_request=ar,
            scope_claim=None,
            justification=None,
            authority_citations=[],
        )

    def test_notify_success(self, tmp_log_dir):
        executor = ExecutorX0E(tmp_log_dir)
        warrant = self._make_warrant()
        bundle = self._make_bundle()
        result = executor.execute(warrant, bundle, 0, "2025-01-15T00:00:00Z")
        assert result["execution_status"] == "SUCCESS"

        # Outbox should have an entry
        outbox = read_jsonl(tmp_log_dir / "outbox.jsonl")
        assert len(outbox) == 1
        assert outbox[0]["warrant_id"] == warrant.warrant_id

    def test_duplicate_warrant_refused(self, tmp_log_dir):
        executor = ExecutorX0E(tmp_log_dir)
        warrant = self._make_warrant()
        bundle = self._make_bundle()
        r1 = executor.execute(warrant, bundle, 0, "2025-01-15T00:00:00Z")
        assert r1["execution_status"] == "SUCCESS"

        r2 = executor.execute(warrant, bundle, 0, "2025-01-15T00:00:00Z")
        assert r2["execution_status"] == "FAILURE"
        assert "DUPLICATE" in r2["failure_reason"]

    def test_non_notify_refused(self, tmp_log_dir):
        executor = ExecutorX0E(tmp_log_dir)
        warrant = self._make_warrant(action_type="WriteLocal")
        bundle = self._make_bundle()
        result = executor.execute(warrant, bundle, 0, "2025-01-15T00:00:00Z")
        assert result["execution_status"] == "FAILURE"
        assert "ACTION_TYPE_REFUSED" in result["failure_reason"]

    def test_startup_reconciliation(self, tmp_log_dir):
        """If outbox has warrant_id not in execution_trace, reconciliation adds it."""
        # Simulate crash: outbox has entry, execution_trace doesn't
        append_jsonl(tmp_log_dir / "outbox.jsonl", {
            "warrant_id": "orphan-001",
            "cycle_id": 0,
            "message": "orphaned",
        })

        executor = ExecutorX0E(tmp_log_dir)
        executor.startup_reconciliation()

        exec_entries = read_jsonl(tmp_log_dir / "execution_trace.jsonl")
        assert any(e.get("warrant_id") == "orphan-001" for e in exec_entries)

        recon_entries = read_jsonl(tmp_log_dir / "reconciliation_trace.jsonl")
        assert any(e.get("warrant_id") == "orphan-001" for e in recon_entries)


# ===================================================================
# § End-to-End Run (spec §4.1, §17.1)
# ===================================================================

class TestEndToEndRun:
    """Verify rsa run produces correct outputs."""

    def test_run_exits_zero(self, run_result):
        rc, _ = run_result
        assert rc == 0

    def test_outbox_has_entry(self, run_result):
        _, log_dir = run_result
        outbox = read_jsonl(log_dir / "outbox.jsonl")
        assert len(outbox) == 1
        assert "warrant_id" in outbox[0]
        assert outbox[0]["message"] == "echo: Hello, RSA-0"

    def test_execution_trace_has_success(self, run_result):
        _, log_dir = run_result
        exec_entries = read_jsonl(log_dir / "execution_trace.jsonl")
        assert len(exec_entries) == 1
        assert exec_entries[0]["execution_status"] == "SUCCESS"

    def test_state_hash_logged(self, run_result):
        _, log_dir = run_result
        hashes = read_jsonl(log_dir / "state_hashes.jsonl")
        assert len(hashes) == 1
        assert len(hashes[0]["state_hash"]) == 64

    def test_run_meta_logged(self, run_result):
        _, log_dir = run_result
        meta = read_jsonl(log_dir / "run_meta.jsonl")
        events = [e["event"] for e in meta]
        assert "RUN_START" in events
        assert "RUN_COMPLETE" in events

    def test_kernel_version_in_meta(self, run_result):
        _, log_dir = run_result
        meta = read_jsonl(log_dir / "run_meta.jsonl")
        start = [e for e in meta if e["event"] == "RUN_START"][0]
        assert start["kernel_version_id"] == KERNEL_VERSION_ID

    def test_all_required_logs_exist(self, run_result):
        _, log_dir = run_result
        required = [
            "observations.jsonl",
            "artifacts.jsonl",
            "admission_trace.jsonl",
            "selector_trace.jsonl",
            "execution_trace.jsonl",
        ]
        for name in required:
            assert (log_dir / name).exists(), f"Missing required log: {name}"


# ===================================================================
# § End-to-End Replay (spec §4.1, §17.2)
# ===================================================================

class TestEndToEndReplay:
    """Verify rsa replay reconstructs identical state."""

    def test_replay_success(self, run_result):
        _, log_dir = run_result
        report = replay(str(CONSTITUTION_PATH), str(log_dir))
        assert report.success

    def test_replay_final_hash_matches(self, run_result):
        _, log_dir = run_result
        report = replay(str(CONSTITUTION_PATH), str(log_dir))
        assert report.final_hash_match

    def test_replay_all_cycles_match(self, run_result):
        _, log_dir = run_result
        report = replay(str(CONSTITUTION_PATH), str(log_dir))
        assert report.cycles_matched == report.cycles_replayed

    def test_replay_detects_tampered_hash(self, run_result):
        """Tamper with logged state hash → replay should detect mismatch."""
        _, log_dir = run_result

        # Tamper the state hash
        hashes_path = log_dir / "state_hashes.jsonl"
        records = read_jsonl(hashes_path)
        records[0]["state_hash"] = "0" * 64

        # Rewrite the file
        hashes_path.unlink()
        for r in records:
            append_jsonl(hashes_path, r)

        report = replay(str(CONSTITUTION_PATH), str(log_dir))
        assert not report.success or not report.cycle_results[0].state_hash_match


# ===================================================================
# § Cross-Run Determinism (spec §15, §17.8)
# ===================================================================

class TestDeterminism:
    """Verify identical outputs across independent runs."""

    def test_two_runs_identical_hashes(self, tmp_path):
        """Two fresh runs on same vector → identical state hashes."""
        log1 = tmp_path / "run1"
        log2 = tmp_path / "run2"
        log1.mkdir()
        log2.mkdir()

        run(str(CONSTITUTION_PATH), str(log1), str(OBSERVATION_STREAM))
        run(str(CONSTITUTION_PATH), str(log2), str(OBSERVATION_STREAM))

        h1 = read_jsonl(log1 / "state_hashes.jsonl")
        h2 = read_jsonl(log2 / "state_hashes.jsonl")
        assert len(h1) == len(h2)
        for a, b in zip(h1, h2):
            assert a["state_hash"] == b["state_hash"]

    def test_matches_golden_vector(self, tmp_path):
        """Run output matches the pre-computed expected state hashes."""
        log_dir = tmp_path / "golden"
        log_dir.mkdir()
        run(str(CONSTITUTION_PATH), str(log_dir), str(OBSERVATION_STREAM))

        actual = read_jsonl(log_dir / "state_hashes.jsonl")
        expected = read_jsonl(EXPECTED_HASHES)

        assert len(actual) == len(expected)
        for a, e in zip(actual, expected):
            assert a["state_hash"] == e["state_hash"], (
                f"Cycle {a['cycle_id']}: {a['state_hash']} != {e['state_hash']}"
            )

    def test_outbox_deterministic(self, tmp_path):
        """Outbox content identical across two runs."""
        log1 = tmp_path / "run1"
        log2 = tmp_path / "run2"
        log1.mkdir()
        log2.mkdir()

        run(str(CONSTITUTION_PATH), str(log1), str(OBSERVATION_STREAM))
        run(str(CONSTITUTION_PATH), str(log2), str(OBSERVATION_STREAM))

        o1 = read_jsonl(log1 / "outbox.jsonl")
        o2 = read_jsonl(log2 / "outbox.jsonl")
        assert o1 == o2


# ===================================================================
# § No Side Effect Without Warrant (spec §17.3)
# ===================================================================

class TestNoUnwarrantedSideEffects:
    """Verify warrantless operations produce no outbox entries."""

    def test_refuse_cycle_no_outbox(self, tmp_path):
        """A cycle with no candidates → REFUSE, no outbox entry."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create observation stream with no candidates
        obs_file = tmp_path / "obs_empty.jsonl"
        obs_file.write_text(json.dumps({
            "cycle_id": 0,
            "timestamp": "2025-01-15T00:00:00Z",
            "observation": {
                "kind": "user_input",
                "payload": {"text": "noop", "source": "cli"},
                "author": "user",
            },
            "candidates": [],
        }) + "\n")

        run(str(CONSTITUTION_PATH), str(log_dir), str(obs_file))

        outbox = read_jsonl(log_dir / "outbox.jsonl")
        assert len(outbox) == 0


# ===================================================================
# § KERNEL_VERSION_ID
# ===================================================================

class TestKernelVersionID:
    """Verify kernel version identity."""

    def test_version_id_format(self):
        assert isinstance(KERNEL_VERSION_ID, str)
        assert "x0e" in KERNEL_VERSION_ID

    def test_version_id_in_initial_hash(self):
        """Different kernel_version_id → different initial hash."""
        ch = "a" * 64
        h1 = initial_state_hash(ch, KERNEL_VERSION_ID)
        h2 = initial_state_hash(ch, "different-version")
        assert h1 != h2
