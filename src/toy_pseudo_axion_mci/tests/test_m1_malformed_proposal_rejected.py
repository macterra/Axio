"""M1: Malformed Proposal Rejection Tests.

Verifies that the kernel correctly rejects malformed proposals:
- Invalid trace_commit
- Insufficient counterfactuals
- Missing required fields
- Schema validation failures
"""

import pytest
from toy_pseudo_axion.common.hashing import hash_json
from toy_pseudo_axion.kernel.invariants import (
    check_i0_trace_commit_integrity,
    check_i1_counterfactual_minimum,
    check_i3_fork_snapshot_present,
    check_all_invariants,
    has_fatal_violation,
)


class TestMalformedProposalRejection:
    """Test suite for malformed proposal rejection (M1)."""

    def test_i0_trace_commit_mismatch_rejected(self):
        """Trace with incorrect trace_commit must be rejected."""
        trace = {
            "trace_version": "0.3",
            "trace_commit": "0" * 64,  # Wrong commit
            "nodes": [{"id": 0, "kind": "observation", "summary": "test", "payload": {}}],
            "edges": [],
            "fork_snapshots": [],
            "causal_claims": [],
            "counterfactuals": [
                {"cf_id": "cf1", "description": "d1", "prob_mass": 0.4, "outcome": "x"},
                {"cf_id": "cf2", "description": "d2", "prob_mass": 0.3, "outcome": "y"},
                {"cf_id": "cf3", "description": "d3", "prob_mass": 0.3, "outcome": "z"},
            ]
        }

        witness = check_i0_trace_commit_integrity(trace)
        assert witness is not None
        assert witness.invariant == "I0_TRACE_COMMIT_INTEGRITY"
        assert witness.severity == "fatal"

    def test_i0_correct_trace_commit_accepted(self):
        """Trace with correct trace_commit must be accepted."""
        trace = {
            "trace_version": "0.3",
            "nodes": [{"id": 0, "kind": "observation", "summary": "test", "payload": {}}],
            "edges": [],
            "fork_snapshots": [],
            "causal_claims": [],
            "counterfactuals": [
                {"cf_id": "cf1", "description": "d1", "prob_mass": 0.4, "outcome": "x"},
                {"cf_id": "cf2", "description": "d2", "prob_mass": 0.3, "outcome": "y"},
                {"cf_id": "cf3", "description": "d3", "prob_mass": 0.3, "outcome": "z"},
            ]
        }
        # Compute correct commit
        trace["trace_commit"] = hash_json({k: v for k, v in trace.items() if k != "trace_commit"})

        witness = check_i0_trace_commit_integrity(trace)
        assert witness is None

    def test_i1_insufficient_counterfactuals_rejected(self):
        """Trace with < 3 counterfactuals must be rejected."""
        trace = {
            "counterfactuals": [
                {"cf_id": "cf1", "description": "d1", "prob_mass": 0.5, "outcome": "x"},
                {"cf_id": "cf2", "description": "d2", "prob_mass": 0.5, "outcome": "y"},
            ]
        }

        witness = check_i1_counterfactual_minimum(trace)
        assert witness is not None
        assert witness.invariant == "I1_COUNTERFACTUAL_MINIMUM"
        assert "Insufficient counterfactuals" in witness.message

    def test_i1_low_probability_mass_rejected(self):
        """Trace with prob_mass sum < 0.9 must be rejected."""
        trace = {
            "counterfactuals": [
                {"cf_id": "cf1", "description": "d1", "prob_mass": 0.2, "outcome": "x"},
                {"cf_id": "cf2", "description": "d2", "prob_mass": 0.2, "outcome": "y"},
                {"cf_id": "cf3", "description": "d3", "prob_mass": 0.2, "outcome": "z"},
            ]
        }

        witness = check_i1_counterfactual_minimum(trace)
        assert witness is not None
        assert "probability coverage" in witness.message.lower()

    def test_i1_invalid_prob_mass_rejected(self):
        """Trace with prob_mass outside [0,1] must be rejected."""
        trace = {
            "counterfactuals": [
                {"cf_id": "cf1", "description": "d1", "prob_mass": 1.5, "outcome": "x"},
                {"cf_id": "cf2", "description": "d2", "prob_mass": 0.3, "outcome": "y"},
                {"cf_id": "cf3", "description": "d3", "prob_mass": 0.3, "outcome": "z"},
            ]
        }

        witness = check_i1_counterfactual_minimum(trace)
        assert witness is not None
        assert "Invalid prob_mass" in witness.message

    def test_i1_valid_counterfactuals_accepted(self):
        """Trace with valid counterfactuals must be accepted."""
        trace = {
            "counterfactuals": [
                {"cf_id": "cf1", "description": "d1", "prob_mass": 0.4, "outcome": "x"},
                {"cf_id": "cf2", "description": "d2", "prob_mass": 0.3, "outcome": "y"},
                {"cf_id": "cf3", "description": "d3", "prob_mass": 0.3, "outcome": "z"},
            ]
        }

        witness = check_i1_counterfactual_minimum(trace)
        assert witness is None

    def test_i3_no_fork_snapshots_rejected(self):
        """Trace with no fork_snapshots must be rejected (full mode)."""
        trace = {
            "fork_snapshots": []
        }

        witness = check_i3_fork_snapshot_present(trace)
        assert witness is not None
        assert witness.invariant == "I3_FORK_SNAPSHOT_PRESENT"

    def test_i3_missing_fields_rejected(self):
        """Fork snapshot missing required fields must be rejected."""
        trace = {
            "fork_snapshots": [
                {"fork_id": "f1"}  # Missing other required fields
            ]
        }

        witness = check_i3_fork_snapshot_present(trace)
        assert witness is not None
        assert "missing fields" in witness.message.lower()

    def test_all_invariants_with_fatal_violation(self):
        """check_all_invariants must detect fatal violations."""
        proposal = {
            "trace": {
                "trace_commit": "wrong",
                "counterfactuals": [],
                "fork_snapshots": []
            }
        }

        witnesses = check_all_invariants(proposal)
        assert len(witnesses) > 0
        assert has_fatal_violation(witnesses)
