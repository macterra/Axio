"""Tests for kernel module."""

import pytest


class TestInvariants:
    """Tests for kernel invariants."""

    def test_check_i0_valid(self, sample_proposal):
        """Test I0 with valid trace commit."""
        from toy_pseudo_axion.kernel.invariants import check_i0_trace_commit

        passed, msg = check_i0_trace_commit(sample_proposal)

        # Should pass if trace exists and has env_hash
        assert passed

    def test_check_i0_missing_trace(self):
        """Test I0 with missing trace."""
        from toy_pseudo_axion.kernel.invariants import check_i0_trace_commit

        proposal = {"payload": {}}
        passed, msg = check_i0_trace_commit(proposal)

        assert not passed
        assert "trace" in msg.lower() or "missing" in msg.lower()

    def test_check_i1_valid(self, sample_proposal):
        """Test I1 with valid counterfactuals."""
        from toy_pseudo_axion.kernel.invariants import check_i1_counterfactual_min

        passed, msg = check_i1_counterfactual_min(sample_proposal, min_count=1)

        assert passed

    def test_check_i1_insufficient(self):
        """Test I1 with insufficient counterfactuals."""
        from toy_pseudo_axion.kernel.invariants import check_i1_counterfactual_min

        proposal = {
            "payload": {},
            "trace": {"counterfactuals": []}
        }
        passed, msg = check_i1_counterfactual_min(proposal, min_count=1)

        assert not passed

    def test_check_i3_fork_snapshot_required(self, sample_proposal):
        """Test I3 with fork snapshots."""
        from toy_pseudo_axion.kernel.invariants import check_i3_fork_snapshot

        passed, msg = check_i3_fork_snapshot(sample_proposal, required=True)

        assert passed

    def test_check_i3_missing_snapshots(self):
        """Test I3 with missing fork snapshots."""
        from toy_pseudo_axion.kernel.invariants import check_i3_fork_snapshot

        proposal = {
            "payload": {},
            "trace": {"fork_snapshots": []}
        }
        passed, msg = check_i3_fork_snapshot(proposal, required=True)

        assert not passed


class TestCapability:
    """Tests for capability token management."""

    def test_issue_token(self, temp_dir):
        """Test token issuance."""
        from toy_pseudo_axion.kernel.capability import CapabilityManager

        manager = CapabilityManager(seed=42)

        token = manager.issue_token(
            operation="move",
            trace_commit="abc123"
        )

        assert token["capability"] == "move"
        assert token["trace_commit"] == "abc123"
        assert "signature" in token
        assert "issued_at" in token

    def test_verify_token_valid(self, temp_dir):
        """Test valid token verification."""
        from toy_pseudo_axion.kernel.capability import CapabilityManager

        manager = CapabilityManager(seed=42)

        token = manager.issue_token(
            operation="move",
            trace_commit="abc123"
        )

        is_valid, msg = manager.verify_token(token, operation="move")

        assert is_valid

    def test_verify_token_wrong_operation(self, temp_dir):
        """Test token with wrong operation (I4 violation)."""
        from toy_pseudo_axion.kernel.capability import CapabilityManager

        manager = CapabilityManager(seed=42)

        token = manager.issue_token(
            operation="move",
            trace_commit="abc123"
        )

        is_valid, msg = manager.verify_token(token, operation="pickup")

        assert not is_valid
        assert "operation" in msg.lower() or "mismatch" in msg.lower()

    def test_verify_token_invalid_signature(self, temp_dir):
        """Test token with invalid signature."""
        from toy_pseudo_axion.kernel.capability import CapabilityManager

        manager = CapabilityManager(seed=42)

        token = manager.issue_token(
            operation="move",
            trace_commit="abc123"
        )

        # Tamper with signature
        token["signature"] = "invalid"

        is_valid, msg = manager.verify_token(token, operation="move")

        assert not is_valid


class TestAuditLog:
    """Tests for audit log."""

    def test_append_and_read(self, temp_dir):
        """Test appending and reading audit entries."""
        from toy_pseudo_axion.kernel.audit_log import AuditLog, read_audit_log

        log = AuditLog(temp_dir / "test_audit.log.jsonl")

        log.append({
            "entry_id": "e1",
            "verdict": "allow",
            "proposal_hash": "abc123"
        })

        entries = read_audit_log(temp_dir / "test_audit.log.jsonl")

        assert len(entries) == 1
        assert entries[0]["entry_id"] == "e1"

    def test_hash_chain(self, temp_dir):
        """Test hash chain integrity."""
        from toy_pseudo_axion.kernel.audit_log import AuditLog, read_audit_log, verify_audit_log

        log = AuditLog(temp_dir / "test_audit.log.jsonl")

        log.append({"entry_id": "e1", "verdict": "allow"})
        log.append({"entry_id": "e2", "verdict": "deny"})

        entries = read_audit_log(temp_dir / "test_audit.log.jsonl")
        is_valid, error = verify_audit_log(entries)

        assert is_valid
        assert error is None

    def test_detect_tampering(self, temp_dir):
        """Test that tampering is detected."""
        from toy_pseudo_axion.kernel.audit_log import AuditLog, read_audit_log, verify_audit_log
        import json

        log = AuditLog(temp_dir / "test_audit.log.jsonl")

        log.append({"entry_id": "e1", "verdict": "allow"})
        log.append({"entry_id": "e2", "verdict": "deny"})

        # Tamper with file
        entries = read_audit_log(temp_dir / "test_audit.log.jsonl")
        entries[0]["verdict"] = "tampered"

        is_valid, error = verify_audit_log(entries)

        assert not is_valid


class TestProbeEngine:
    """Tests for probe engine."""

    def test_parse_causal_claim_form_a(self):
        """Test parsing Form A causal claims."""
        from toy_pseudo_axion.kernel.probe_engine import parse_causal_claim

        claim = "IF self_energy DEC THEN CHOICE wait"
        result = parse_causal_claim(claim)

        assert result is not None
        assert result["var"] == "self_energy"
        assert result["op"] == "DEC"
        assert result["action"] == "wait"

    def test_parse_causal_claim_form_b(self):
        """Test parsing Form B causal claims."""
        from toy_pseudo_axion.kernel.probe_engine import parse_causal_claim

        claim = "IF self_energy LT 50 THEN CHOICE wait"
        result = parse_causal_claim(claim)

        assert result is not None
        assert result["var"] == "self_energy"
        assert result["cmp"] == "LT"
        assert result["value"] == "50"
        assert result["action"] == "wait"

    def test_parse_causal_claim_invalid(self):
        """Test parsing invalid causal claims."""
        from toy_pseudo_axion.kernel.probe_engine import parse_causal_claim

        result = parse_causal_claim("not a valid claim")

        assert result is None


class TestPolicyGate:
    """Tests for policy gate."""

    def test_evaluate_allow(self, sample_proposal, temp_dir):
        """Test evaluation that allows proposal."""
        from toy_pseudo_axion.kernel.policy_gate import PolicyGate
        from toy_pseudo_axion.kernel.audit_log import AuditLog

        audit_log = AuditLog(temp_dir / "audit.log.jsonl")
        gate = PolicyGate(audit_log, seed=42, use_watchdog=False)

        decision = gate.evaluate(sample_proposal)

        # Should allow or allow_with_constraints
        assert decision.verdict in ["allow", "allow_with_constraints"]

    def test_evaluate_deny_missing_trace(self, temp_dir):
        """Test evaluation denies proposal with missing trace."""
        from toy_pseudo_axion.kernel.policy_gate import PolicyGate
        from toy_pseudo_axion.kernel.audit_log import AuditLog

        audit_log = AuditLog(temp_dir / "audit.log.jsonl")
        gate = PolicyGate(audit_log, seed=42, use_watchdog=False)

        proposal = {"payload": {"plan": {"steps": []}}}
        decision = gate.evaluate(proposal)

        assert decision.verdict == "deny"
        assert len(decision.witnesses) > 0
