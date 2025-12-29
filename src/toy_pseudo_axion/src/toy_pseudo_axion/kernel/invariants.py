"""Kernel invariant definitions and checks."""

from typing import Any, Optional
from dataclasses import dataclass

from ..common.hashing import hash_json
from ..common.errors import InvariantViolationError


@dataclass
class Witness:
    """A witness to an invariant check result."""
    invariant: str
    severity: str  # "fatal" or "warn"
    message: str
    data_hash: str

    def to_dict(self) -> dict:
        return {
            "invariant": self.invariant,
            "severity": self.severity,
            "message": self.message,
            "data_hash": self.data_hash
        }


def check_i0_trace_commit_integrity(trace: dict) -> Optional[Witness]:
    """I0: Trace Commit Integrity (Fatal)

    Reject if trace.trace_commit != hash_json(trace_without_trace_commit)
    """
    # Make a copy without trace_commit for hashing
    trace_for_hash = {k: v for k, v in trace.items() if k != "trace_commit"}
    expected_commit = hash_json(trace_for_hash)

    actual_commit = trace.get("trace_commit", "")

    if actual_commit != expected_commit:
        return Witness(
            invariant="I0_TRACE_COMMIT_INTEGRITY",
            severity="fatal",
            message=f"Trace commit mismatch: expected {expected_commit}, got {actual_commit}",
            data_hash=hash_json({"expected": expected_commit, "actual": actual_commit})
        )
    return None


def check_i1_counterfactual_minimum(trace: dict) -> Optional[Witness]:
    """I1: Counterfactual Minimum (Fatal)

    Reject if:
    - len(trace.counterfactuals) < 3 OR
    - sum(prob_mass) < 0.9 OR
    - any prob_mass outside [0,1]
    """
    counterfactuals = trace.get("counterfactuals", [])

    if len(counterfactuals) < 3:
        return Witness(
            invariant="I1_COUNTERFACTUAL_MINIMUM",
            severity="fatal",
            message=f"Insufficient counterfactuals: {len(counterfactuals)} < 3 required",
            data_hash=hash_json({"count": len(counterfactuals)})
        )

    prob_sum = 0.0
    for cf in counterfactuals:
        prob_mass = cf.get("prob_mass", 0)
        if not (0 <= prob_mass <= 1):
            return Witness(
                invariant="I1_COUNTERFACTUAL_MINIMUM",
                severity="fatal",
                message=f"Invalid prob_mass {prob_mass}: must be in [0,1]",
                data_hash=hash_json({"cf_id": cf.get("cf_id"), "prob_mass": prob_mass})
            )
        prob_sum += prob_mass

    if prob_sum < 0.9:
        return Witness(
            invariant="I1_COUNTERFACTUAL_MINIMUM",
            severity="fatal",
            message=f"Insufficient probability coverage: {prob_sum:.3f} < 0.9 required",
            data_hash=hash_json({"prob_sum": prob_sum})
        )

    return None


def check_i3_fork_snapshot_present(trace: dict) -> Optional[Witness]:
    """I3: Fork Snapshot Commitments Present (Fatal)

    Reject if:
    - len(trace.fork_snapshots) < 1 OR
    - any snapshot missing required fields
    """
    fork_snapshots = trace.get("fork_snapshots", [])

    if len(fork_snapshots) < 1:
        return Witness(
            invariant="I3_FORK_SNAPSHOT_PRESENT",
            severity="fatal",
            message="No fork snapshots provided",
            data_hash=hash_json({"count": 0})
        )

    required_fields = ["fork_id", "state_digest", "focus_vars", "commitment", "nonce_ref"]

    for i, snapshot in enumerate(fork_snapshots):
        missing = [f for f in required_fields if f not in snapshot]
        if missing:
            return Witness(
                invariant="I3_FORK_SNAPSHOT_PRESENT",
                severity="fatal",
                message=f"Fork snapshot {i} missing fields: {missing}",
                data_hash=hash_json({"index": i, "missing": missing})
            )

    return None


def check_i4_capability_token_binding(token: dict, proposal_hash: str, trace_hash: str, scope_hash: str) -> Optional[Witness]:
    """I4: Capability Tokens Trace-Bound (Fatal)

    Token binding must include matching:
    - proposal_hash
    - trace_hash
    - scope_hash
    """
    binding = token.get("binding", {})

    if binding.get("proposal_hash") != proposal_hash:
        return Witness(
            invariant="I4_CAPABILITY_TOKEN_BINDING",
            severity="fatal",
            message="Token proposal_hash mismatch",
            data_hash=hash_json({
                "expected": proposal_hash,
                "actual": binding.get("proposal_hash")
            })
        )

    if binding.get("trace_hash") != trace_hash:
        return Witness(
            invariant="I4_CAPABILITY_TOKEN_BINDING",
            severity="fatal",
            message="Token trace_hash mismatch",
            data_hash=hash_json({
                "expected": trace_hash,
                "actual": binding.get("trace_hash")
            })
        )

    if binding.get("scope_hash") != scope_hash:
        return Witness(
            invariant="I4_CAPABILITY_TOKEN_BINDING",
            severity="fatal",
            message="Token scope_hash mismatch",
            data_hash=hash_json({
                "expected": scope_hash,
                "actual": binding.get("scope_hash")
            })
        )

    return None


def check_all_invariants(proposal: dict) -> list[Witness]:
    """Check all kernel invariants on a proposal.

    Returns list of witnesses (empty if all pass).
    """
    witnesses = []

    trace = proposal.get("trace", {})

    # I0: Trace commit integrity
    w = check_i0_trace_commit_integrity(trace)
    if w:
        witnesses.append(w)

    # I1: Counterfactual minimum
    w = check_i1_counterfactual_minimum(trace)
    if w:
        witnesses.append(w)

    # I3: Fork snapshot present
    w = check_i3_fork_snapshot_present(trace)
    if w:
        witnesses.append(w)

    # Note: I4 and I5 are checked separately during token operations

    return witnesses


def has_fatal_violation(witnesses: list[Witness]) -> bool:
    """Check if any witness indicates a fatal violation."""
    return any(w.severity == "fatal" for w in witnesses)
