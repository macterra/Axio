"""Tests for kernel components."""

import pytest
from toy_aki.kernel import (
    KernelPolicy,
    PolicyGate,
    ActuationGate,
    ActuationCertificate,
    MAX_DELEGATION_DEPTH,
    AuditLog,
    AuditEntry,
    GENESIS_PREV_HASH,
    KernelWatchdog,
    KernelDecision,
    ProbeEngine,
    ProbeResult,
)
from toy_aki.acv import AnchorRegistry


class TestKernelPolicy:
    """Tests for kernel policy."""

    def test_policy_exists(self):
        """KernelPolicy should be creatable."""
        policy = KernelPolicy()
        assert policy is not None


class TestPolicyGate:
    """Tests for policy gate."""

    def test_gate_exists(self):
        """PolicyGate should be creatable."""
        gate = PolicyGate()
        assert gate is not None


class TestActuationGate:
    """Tests for actuation gate."""

    def test_max_delegation_depth(self):
        """MAX_DELEGATION_DEPTH should be 2."""
        assert MAX_DELEGATION_DEPTH == 2


class TestAuditLog:
    """Tests for audit log."""

    def test_genesis_hash_defined(self):
        """GENESIS_PREV_HASH should be defined."""
        assert GENESIS_PREV_HASH is not None
        assert len(GENESIS_PREV_HASH) == 64

    def test_audit_log_creatable(self):
        """AuditLog should be creatable."""
        log = AuditLog()
        assert log is not None


class TestKernelDecision:
    """Tests for kernel decision."""

    def test_decision_has_accepted_field(self):
        """KernelDecision should have accepted field."""
        decision = KernelDecision(
            decision_id="test-001",
            proposal_hash="a" * 64,
            accepted=True,
            reason="",
            invariant_checks={},
            certificate=None,
            timestamp_ms=1000,
        )
        assert decision.accepted is True


class TestProbeResult:
    """Tests for probe results."""

    def test_probe_result_structure(self):
        """ProbeResult should have required fields."""
        result = ProbeResult(
            probe_id="probe-001",
            probe_name="test_probe",
            detected=True,
            severity="violation",
        )
        assert result.detected is True
        assert result.severity == "violation"


class TestAnchorRegistry:
    """Tests for anchor registry from kernel perspective."""

    def test_registry_creation(self):
        """AnchorRegistry should be creatable."""
        registry = AnchorRegistry()
        assert registry is not None
