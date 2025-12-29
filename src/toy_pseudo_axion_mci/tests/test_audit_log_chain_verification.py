"""Audit Log Chain Verification Tests.

Verifies that audit log is:
- Append-only and hash-chained
- Verifiable via verify_audit command
- Correctly handles genesis entry
- Detects chain breaks
"""

import json
import tempfile
from pathlib import Path
import pytest

from toy_pseudo_axion.common.hashing import hash_json
from toy_pseudo_axion.kernel.audit_log import (
    AuditLog,
    verify_audit_log,
    read_audit_log,
)


class TestAuditLogChainVerification:
    """Test suite for audit log chain verification."""

    def test_genesis_entry_has_zero_prev_hash(self):
        """First entry must have prev_entry_hash = '0' * 64."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            audit_log.append(
                event="POLICY_DECISION",
                proposal_hash="abc123",
                trace_hash="def456",
                verdict="allow",
                notes="test entry",
                witnesses=[],
                capability_tokens=[],
            )

            entries = read_audit_log(log_path)
            assert len(entries) == 1
            assert entries[0]["prev_entry_hash"] == "0" * 64

    def test_chain_links_correctly(self):
        """Each entry's prev_entry_hash must equal previous entry_hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            # Add multiple entries
            for i in range(5):
                audit_log.append(
                    event="POLICY_DECISION",
                    proposal_hash=f"proposal_{i}",
                    trace_hash=f"trace_{i}",
                    verdict="allow" if i % 2 == 0 else "deny",
                    notes=f"test entry {i}",
                    witnesses=[],
                    capability_tokens=[],
                )

            entries = read_audit_log(log_path)
            assert len(entries) == 5

            # Verify chain
            for i in range(1, len(entries)):
                assert entries[i]["prev_entry_hash"] == entries[i-1]["entry_hash"]

    def test_verify_valid_chain(self):
        """verify_audit_log must return True for valid chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            for i in range(3):
                audit_log.append(
                    event="POLICY_DECISION",
                    proposal_hash=f"proposal_{i}",
                    trace_hash=f"trace_{i}",
                    verdict="allow",
                    notes=f"test entry {i}",
                    witnesses=[],
                    capability_tokens=[],
                )

            is_valid, error = verify_audit_log(log_path)
            assert is_valid is True
            assert error is None

    def test_detect_tampered_entry(self):
        """verify_audit_log must detect tampered entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            for i in range(3):
                audit_log.append(
                    event="POLICY_DECISION",
                    proposal_hash=f"proposal_{i}",
                    trace_hash=f"trace_{i}",
                    verdict="allow",
                    notes=f"test entry {i}",
                    witnesses=[],
                    capability_tokens=[],
                )

            # Tamper with second entry
            entries = read_audit_log(log_path)
            entries[1]["kernel_decision"]["verdict"] = "TAMPERED"

            # Rewrite file
            with open(log_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            is_valid, error = verify_audit_log(log_path)
            assert is_valid is False
            assert error is not None

    def test_detect_broken_chain(self):
        """verify_audit_log must detect broken prev_entry_hash chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            for i in range(3):
                audit_log.append(
                    event="POLICY_DECISION",
                    proposal_hash=f"proposal_{i}",
                    trace_hash=f"trace_{i}",
                    verdict="allow",
                    notes=f"test entry {i}",
                    witnesses=[],
                    capability_tokens=[],
                )

            # Break chain
            entries = read_audit_log(log_path)
            entries[2]["prev_entry_hash"] = "wrong_hash"

            # Rewrite file
            with open(log_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            is_valid, error = verify_audit_log(log_path)
            assert is_valid is False

    def test_entry_hash_in_entry(self):
        """entry_hash must be present in each entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            audit_log.append(
                event="POLICY_DECISION",
                proposal_hash="abc123",
                trace_hash="def456",
                verdict="allow",
                notes="test entry",
                witnesses=[],
                capability_tokens=[],
            )

            entries = read_audit_log(log_path)
            assert "entry_hash" in entries[0]
            assert isinstance(entries[0]["entry_hash"], str)
            assert len(entries[0]["entry_hash"]) == 64  # SHA-256 hex

    def test_empty_log_verification(self):
        """Empty audit log should verify successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            log_path.touch()

            is_valid, error = verify_audit_log(log_path)
            assert is_valid is True

    def test_denials_are_logged(self):
        """Denials must be appended to audit log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit_log = AuditLog(log_path)

            audit_log.append(
                event="POLICY_DECISION",
                proposal_hash="denied_proposal",
                trace_hash="denied_trace",
                verdict="deny",
                notes="policy violation",
                witnesses=[{"invariant": "I0", "severity": "fatal", "message": "test", "data_hash": "x"}],
                capability_tokens=[],
            )

            entries = read_audit_log(log_path)
            assert len(entries) == 1
            assert entries[0]["kernel_decision"]["verdict"] == "deny"
            assert len(entries[0]["witnesses"]) == 1

