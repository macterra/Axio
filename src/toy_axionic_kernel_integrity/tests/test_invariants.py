"""Integration tests for K0-K7 invariant enforcement."""

import pytest
from toy_aki.kernel import (
    KernelWatchdog,
    KernelDecision,
    PolicyGate,
    ActuationGate,
    AuditLog,
    GENESIS_PREV_HASH,
    MAX_DELEGATION_DEPTH,
)
from toy_aki.env import ToyWorld
from toy_aki.acv import (
    create_commitment,
    generate_coupling_witness,
    verify_coupling_witness,
    CouplingType,
    AnchorRegistry,
)
from toy_aki.common.hashing import (
    compute_proposal_hash,
    compute_trace_commit,
    seed_to_kernel_secret,
    hash_json,
)


class TestInvariantConstants:
    """Tests for invariant-related constants."""

    def test_genesis_hash_defined(self):
        """GENESIS_PREV_HASH should be 64-char hex."""
        assert len(GENESIS_PREV_HASH) == 64

    def test_max_delegation_depth(self):
        """MAX_DELEGATION_DEPTH should be 2."""
        assert MAX_DELEGATION_DEPTH == 2


class TestHashingFunctions:
    """Tests for hashing functions used in invariants."""

    def test_proposal_hash_excludes_hash_field(self):
        """compute_proposal_hash should exclude proposal_hash field."""
        proposal = {
            "proposal_id": "test-123",
            "proposal_hash": "should_be_excluded",
            "data": "test",
        }
        hash1 = compute_proposal_hash(proposal)

        proposal2 = proposal.copy()
        proposal2["proposal_hash"] = "different_value"
        hash2 = compute_proposal_hash(proposal2)

        assert hash1 == hash2

    def test_trace_commit_deterministic(self):
        """compute_trace_commit should be deterministic."""
        trace = {"nodes": [{"id": "1"}, {"id": "2"}]}
        c1 = compute_trace_commit(trace)
        c2 = compute_trace_commit(trace)
        assert c1 == c2


class TestCouplingPatterns:
    """Tests for coupling patterns used in K6."""

    def test_coupling_a_works(self):
        """Coupling A should generate and verify."""
        nodes = [{"id": "1", "type": "obs"}]
        anchor = "a" * 64

        witness = generate_coupling_witness(CouplingType.A, nodes, anchor)
        assert verify_coupling_witness(witness, nodes, anchor) is True

    def test_coupling_b_works(self):
        """Coupling B should generate and verify."""
        nodes = [{"id": "1", "type": "obs"}]
        anchor = "b" * 64
        env_digest = "c" * 64

        witness = generate_coupling_witness(CouplingType.B, nodes, anchor, env_digest)
        assert verify_coupling_witness(witness, nodes, anchor, env_digest) is True

    def test_coupling_c_works(self):
        """Coupling C should generate and verify."""
        nodes = [
            {"id": "1", "type": "obs"},
            {"id": "2", "type": "reason"},
        ]
        anchor = "d" * 64

        witness = generate_coupling_witness(CouplingType.C, nodes, anchor)
        assert verify_coupling_witness(witness, nodes, anchor) is True

    def test_coupling_fails_with_wrong_trace(self):
        """Coupling should fail with modified trace."""
        original = [{"id": "1", "type": "obs"}]
        anchor = "e" * 64

        witness = generate_coupling_witness(CouplingType.A, original, anchor)

        modified = [{"id": "2", "type": "modified"}]
        assert verify_coupling_witness(witness, modified, anchor) is False


class TestKernelComponents:
    """Tests for kernel component existence."""

    def test_watchdog_importable(self):
        """KernelWatchdog should be importable."""
        assert KernelWatchdog is not None

    def test_decision_importable(self):
        """KernelDecision should be importable."""
        assert KernelDecision is not None

    def test_policy_gate_importable(self):
        """PolicyGate should be importable."""
        assert PolicyGate is not None

    def test_actuation_gate_importable(self):
        """ActuationGate should be importable."""
        assert ActuationGate is not None

    def test_audit_log_importable(self):
        """AuditLog should be importable."""
        assert AuditLog is not None
