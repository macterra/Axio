"""
RSA X-3 — Boundary Verifier

Harness-level boundary verification and activation logic.
Runs at Step 0 of each cycle (before policy_core_x3).

Responsibilities:
  1. Verify CycleCommit(c-1) signature
  2. Verify pending_successor_key state consistency
  3. Perform boundary activation (key rotation, suspension)
  4. Verify CycleStart(c) signature
  5. Verify CycleStart(c) chain/frame continuity

NOT inside policy_core_x3. The kernel never signs boundary records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .artifacts_x3 import (
    BoundaryCode,
    CycleCommitPayload,
    CycleStartPayload,
    InternalStateX3,
    compute_identity_chain_tip_hash,
)
from .signature_x3 import (
    verify_cycle_commit,
    verify_cycle_start,
)
from ..artifacts import canonical_json_bytes


# ---------------------------------------------------------------------------
# Boundary Verification Result
# ---------------------------------------------------------------------------

@dataclass
class BoundaryVerificationResult:
    """Result of boundary verification and activation."""
    passed: bool
    failure_code: str = ""
    failure_detail: str = ""
    activation_occurred: bool = False
    prior_key: str = ""
    successor_key: str = ""
    suspended_grant_ids: List[str] = None

    def __post_init__(self):
        if self.suspended_grant_ids is None:
            self.suspended_grant_ids = []

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"passed": self.passed}
        if not self.passed:
            d["failure_code"] = self.failure_code
            d["failure_detail"] = self.failure_detail
        if self.activation_occurred:
            d["activation_occurred"] = True
            d["prior_key"] = self.prior_key
            d["successor_key"] = self.successor_key
            d["suspended_grant_ids"] = self.suspended_grant_ids
        return d


# ---------------------------------------------------------------------------
# Boundary Verifier
# ---------------------------------------------------------------------------

def verify_and_activate_boundary(
    *,
    cycle_id: int,
    state: InternalStateX3,
    cycle_commit_payload: Optional[Dict[str, Any]],
    cycle_commit_signature: Optional[str],
    cycle_start_payload: Dict[str, Any],
    cycle_start_signature: str,
    succession_admitted_in_prior_cycle: bool,
    succession_proposal_hash: str = "",
) -> BoundaryVerificationResult:
    """Perform full boundary verification and activation for cycle c.

    For cycle 1: skip CycleCommit verification (no prior cycle).
    For cycle >= 2: verify both CycleCommit(c-1) and CycleStart(c).

    Mutates state in-place (activation, suspension, lineage update).

    Args:
        cycle_id: Current cycle number
        state: InternalStateX3 to verify against and mutate
        cycle_commit_payload: CycleCommit payload dict (None for cycle 1)
        cycle_commit_signature: CycleCommit signature hex (None for cycle 1)
        cycle_start_payload: CycleStart payload dict
        cycle_start_signature: CycleStart signature hex
        succession_admitted_in_prior_cycle: Whether a non-self succession was
            admitted in the prior cycle
        succession_proposal_hash: Hash of the admitted succession proposal
            (needed for tip hash computation)

    Returns:
        BoundaryVerificationResult with pass/fail and activation details
    """
    activation_occurred = False
    prior_key = ""
    successor_key = ""
    suspended_ids: List[str] = []

    # ------------------------------------------------------------------
    # Step 1: Verify CycleCommit(c-1) signature (skip for cycle 1)
    # ------------------------------------------------------------------
    if cycle_id >= 2 and cycle_commit_payload is not None:
        expected_signer = state.sovereign_public_key_active
        valid, error = verify_cycle_commit(
            expected_signer,
            cycle_commit_payload,
            cycle_commit_signature or "",
        )
        if not valid:
            return BoundaryVerificationResult(
                passed=False,
                failure_code=BoundaryCode.BOUNDARY_SIGNATURE_MISMATCH,
                failure_detail=f"CycleCommit({cycle_id - 1}) signature failed: {error}",
            )

    # ------------------------------------------------------------------
    # Step 2: Verify pending successor state consistency
    # ------------------------------------------------------------------
    if cycle_id >= 2 and cycle_commit_payload is not None:
        commit_pending = cycle_commit_payload.get("pending_successor_key")

        if succession_admitted_in_prior_cycle:
            if commit_pending is None:
                return BoundaryVerificationResult(
                    passed=False,
                    failure_code=BoundaryCode.BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR,
                    failure_detail="No pending_successor_key despite admitted succession",
                )
        else:
            if commit_pending is not None:
                return BoundaryVerificationResult(
                    passed=False,
                    failure_code=BoundaryCode.BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR,
                    failure_detail="Unexpected pending_successor_key without succession",
                )

    # ------------------------------------------------------------------
    # Step 3: Boundary activation (if pending_successor_key present)
    # ------------------------------------------------------------------
    if state.pending_successor_key is not None:
        prior_key = state.sovereign_public_key_active
        successor_key = state.pending_successor_key

        # Update sovereign keys
        state.prior_sovereign_public_key = prior_key
        state.sovereign_public_key_active = successor_key
        state.pending_successor_key = None

        # Suspend all active grants
        suspended_ids = state.active_treaty_set.suspend_all_active(
            state.cycle_index
        )

        # Update lineage
        state.identity_chain_length += 1
        prior_tip = state.identity_chain_tip_hash
        state.identity_chain_tip_hash = compute_identity_chain_tip_hash(
            chain_length=state.identity_chain_length,
            active_key=successor_key,
            prior_tip_hash=prior_tip,
            succession_proposal_hash=succession_proposal_hash,
        )

        # Record in historical keys for cycle detection
        state.historical_sovereign_keys.add(prior_key)

        activation_occurred = True

    # ------------------------------------------------------------------
    # Step 4: Verify CycleStart(c) signature
    # ------------------------------------------------------------------
    expected_signer = state.sovereign_public_key_active
    valid, error = verify_cycle_start(
        expected_signer,
        cycle_start_payload,
        cycle_start_signature,
    )
    if not valid:
        return BoundaryVerificationResult(
            passed=False,
            failure_code=BoundaryCode.BOUNDARY_SIGNATURE_MISMATCH,
            failure_detail=f"CycleStart({cycle_id}) signature failed: {error}",
        )

    # ------------------------------------------------------------------
    # Step 5: Verify CycleStart chain/frame continuity
    # ------------------------------------------------------------------
    start_chain_length = cycle_start_payload.get("identity_chain_length")
    if start_chain_length != state.identity_chain_length:
        return BoundaryVerificationResult(
            passed=False,
            failure_code=BoundaryCode.BOUNDARY_STATE_CHAIN_MISMATCH,
            failure_detail=(
                f"CycleStart chain_length={start_chain_length} "
                f"!= state chain_length={state.identity_chain_length}"
            ),
        )

    start_tip_hash = cycle_start_payload.get("identity_chain_tip_hash")
    if start_tip_hash != state.identity_chain_tip_hash:
        return BoundaryVerificationResult(
            passed=False,
            failure_code=BoundaryCode.BOUNDARY_STATE_CHAIN_MISMATCH,
            failure_detail="CycleStart identity_chain_tip_hash mismatch",
        )

    start_overlay = cycle_start_payload.get("overlay_hash")
    if start_overlay != state.overlay_hash:
        return BoundaryVerificationResult(
            passed=False,
            failure_code=BoundaryCode.BOUNDARY_STATE_CHAIN_MISMATCH,
            failure_detail="CycleStart overlay_hash mismatch",
        )

    start_active_key = cycle_start_payload.get("sovereign_public_key_active")
    if start_active_key != state.sovereign_public_key_active:
        return BoundaryVerificationResult(
            passed=False,
            failure_code=BoundaryCode.BOUNDARY_STATE_CHAIN_MISMATCH,
            failure_detail="CycleStart sovereign_public_key_active mismatch",
        )

    # ------------------------------------------------------------------
    # All checks passed
    # ------------------------------------------------------------------
    return BoundaryVerificationResult(
        passed=True,
        activation_occurred=activation_occurred,
        prior_key=prior_key,
        successor_key=successor_key,
        suspended_grant_ids=suspended_ids,
    )
