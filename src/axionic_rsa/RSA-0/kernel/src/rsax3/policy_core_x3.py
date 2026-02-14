"""
RSA X-3 — Policy Core (Sovereign Succession Under Lineage)

Extends policy_core_x2 with sovereign succession and treaty ratification.

X3_TOPOLOGICAL ordering (12-step per-cycle):
  Step 0:  Boundary verify/activate   (harness — NOT in this function)
  Step 1:  Amendment adoption
  Step 2:  Treaty revalidation (post-amendment)
  Step 3:  Succession proposal admission
  Step 4:  Treaty revocation admission
  Step 5:  Treaty ratification admission
  Step 6:  Density checkpoint A (full repair)
  Step 7:  Treaty grant admission
  Step 8:  Density checkpoint B (full repair)
  Step 9:  RSA action admission
  Step 10: Delegated action admission
  Step 11: Warrant issuance & output assembly

Step 0 (boundary verification/activation) is performed by the harness
BEFORE calling this function. policy_core_x3() receives post-activation
state and never sees pre-activation state.

Amendment adoption (Step 1) does NOT early-return; it continues into the
full cycle so revalidation and action evaluation happen in the same call.

If any suspended grants remain (has_suspensions()), new treaty grants
are blocked with SUSPENSION_UNRESOLVED at Step 7.

Composes X-2's sub-steps for treaty and action paths.
Composes X-1's policy core for amendment and base action paths.
Pure, deterministic, no side effects.

kernel_version_id: rsa-replay-regime-x3-v0.1
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..artifacts import (
    ActionRequest,
    CandidateBundle,
    DecisionType,
    ExitReasonCode,
    ExitRecord,
    ExecutionWarrant,
    InternalState,
    Observation,
    ObservationKind,
    RefusalReasonCode,
    RefusalRecord,
    SystemEvent,
    canonical_json,
    canonical_json_bytes,
)
from ..admission import AdmissionPipeline
from ..policy_core import extract_cycle_time, _make_exit_record, _make_budget_refusal

from ..rsax1.artifacts_x1 import (
    AmendmentProposal,
    DecisionTypeX1,
    PendingAmendment,
    StateDelta,
)
from ..rsax1.policy_core_x1 import (
    _action_path,
    _make_admission_pipeline,
    _try_adopt,
    _try_queue_amendment,
)

from ..rsax2.artifacts_x2 import (
    TreatyAdmissionEvent,
    TreatyAdmissionResult,
    TreatyGrant,
    TreatyRevalidationEvent,
    TreatyRevocation,
)
from ..rsax2.policy_core_x2 import (
    DelegatedActionRequest,
    _evaluate_delegated_action,
    _find_grant_from_result,
    _find_grant_id_from_result,
    make_warrant_with_deterministic_id,
)
from ..rsax2.treaty_admission import TreatyAdmissionPipeline

from .artifacts_x3 import (
    ActiveTreatySetX3,
    AuthorityCode,
    DecisionTypeX3,
    InternalStateX3,
    PolicyOutputX3,
    SuccessionProposal,
    SuccessionAdmissionRecord,
    SuccessionRejectionRecord,
    TreatyRatification,
    RatificationAdmissionRecord,
    RatificationRejectionRecord,
    RatificationRejectionCode,
)
from .constitution_x3 import EffectiveConstitutionFrame
from .succession_admission import SuccessionAdmissionPipeline
from .treaty_ratification import RatificationAdmissionPipeline


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KERNEL_VERSION_ID = "rsa-replay-regime-x3-v0.1"
CYCLE_ORDERING_X3_TOPOLOGICAL = "X3_TOPOLOGICAL"


# ---------------------------------------------------------------------------
# Policy Core X-3
# ---------------------------------------------------------------------------

def policy_core_x3(
    *,
    cycle_id: int,
    observations: List[Observation],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    succession_candidates: List[SuccessionProposal],
    treaty_revocation_candidates: List[TreatyRevocation],
    treaty_ratification_candidates: List[TreatyRatification],
    treaty_grant_candidates: List[TreatyGrant],
    delegated_action_candidates: List[DelegatedActionRequest],
    rsa_action_candidates: List[CandidateBundle],
    constitution_frame: EffectiveConstitutionFrame,
    internal_state: InternalStateX3,
) -> PolicyOutputX3:
    """
    X-3 policy core. Pure, deterministic.

    Implements X3_TOPOLOGICAL 12-step ordering.
    Receives post-activation state from harness (Step 0 already applied).

    Args:
        cycle_id: Current cycle number (explicit for determinism/logging)
        observations: Cycle observations (TIMESTAMP, BUDGET, SYSTEM)
        amendment_candidates: New amendment proposals
        pending_amendment_candidates: Pending amendments from prior cycles
        succession_candidates: SuccessionProposal artifacts
        treaty_revocation_candidates: TreatyRevocation artifacts
        treaty_ratification_candidates: TreatyRatification artifacts
        treaty_grant_candidates: TreatyGrant artifacts
        delegated_action_candidates: DelegatedActionRequest artifacts
        rsa_action_candidates: Direct RSA action CandidateBundles
        constitution_frame: EffectiveConstitutionFrame (constitution + overlay)
        internal_state: Post-activation InternalStateX3

    Returns:
        PolicyOutputX3 with all admission/rejection records
    """
    output = PolicyOutputX3(decision_type=DecisionTypeX3.REFUSE)

    # ---------------------------------------------------------------
    # Pre-admission: timestamp, integrity, budget
    # ---------------------------------------------------------------
    cycle_time = extract_cycle_time(observations)
    if cycle_time is None:
        timestamp_count = sum(
            1 for o in observations
            if o.kind == ObservationKind.TIMESTAMP.value
        )
        refusal = RefusalRecord(
            reason_code=RefusalReasonCode.MISSING_REQUIRED_OBSERVATION.value,
            failed_gate="required_observations",
            missing_artifacts=["TIMESTAMP" if timestamp_count == 0
                             else f"TIMESTAMP (ambiguous: count={timestamp_count})"],
            authority_ids_considered=[],
            observation_ids_referenced=[o.id for o in observations],
            rejection_summary_by_gate={},
            created_at="",
        )
        output.refusal = refusal
        return output

    # Integrity checks
    for obs in observations:
        if obs.kind == ObservationKind.SYSTEM.value:
            event = obs.payload.get("event", "")
            if event in (
                SystemEvent.STARTUP_INTEGRITY_FAIL.value,
                SystemEvent.CITATION_INDEX_FAIL.value,
                SystemEvent.EXECUTOR_INTEGRITY_FAIL.value,
                SystemEvent.REPLAY_FAIL.value,
            ):
                exit_record = ExitRecord(
                    reason_code=ExitReasonCode.INTEGRITY_RISK.value,
                    authority_citations=[
                        constitution_frame.make_citation("CL-EXIT-POLICY"),
                    ],
                    scope_claim={
                        "observation_ids": [obs.id],
                        "claim": f"EXIT required: {event}",
                    },
                    justification=(
                        f"Integrity risk: {event} — "
                        f"{obs.payload.get('detail', '')}"
                    ),
                    created_at=cycle_time,
                )
                output.decision_type = DecisionTypeX3.EXIT
                output.exit_record = exit_record
                return output

    # Budget check
    for obs in observations:
        if obs.kind == ObservationKind.BUDGET.value:
            token_count = obs.payload.get("llm_output_token_count", 0)
            max_tokens = constitution_frame.max_total_tokens_per_cycle()
            if token_count > max_tokens:
                refusal = _make_budget_refusal(observations, cycle_time)
                output.refusal = refusal
                return output

    # ===================================================================
    # X3_TOPOLOGICAL ordering (Steps 1-11)
    # ===================================================================

    all_revalidation_events: List[TreatyRevalidationEvent] = []

    # ------------------------------------------------------------------
    # Step 1: Amendment adoption (non-early-return)
    # ------------------------------------------------------------------
    adoption_result = _try_adopt(
        pending_amendment_candidates,
        constitution_frame,
        internal_state,
        cycle_time,
        None,  # schema — not passed to policy core per AL1
    )
    if adoption_result is not None:
        output.adoption_record = adoption_result.adoption_record
        output.state_delta = adoption_result.state_delta
        # Continue — do NOT early-return in topological mode

    # ------------------------------------------------------------------
    # Step 2: Treaty revalidation (post-amendment)
    # ------------------------------------------------------------------
    reval_events = (
        internal_state.active_treaty_set
        .apply_constitutional_revalidation(
            constitution_frame, internal_state.cycle_index,
        )
    )
    all_revalidation_events.extend(reval_events)

    # ------------------------------------------------------------------
    # Step 3: Succession proposal admission
    # ------------------------------------------------------------------
    if succession_candidates:
        succession_pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=(
                internal_state.sovereign_public_key_active
            ),
            prior_sovereign_public_key=(
                internal_state.prior_sovereign_public_key
            ),
            historical_sovereign_keys=(
                internal_state.historical_sovereign_keys
            ),
            constitution_frame=constitution_frame,
            already_admitted_this_cycle=False,
        )
        admitted, rejections, succ_events = succession_pipeline.evaluate(
            succession_candidates
        )
        output.succession_admission = admitted
        output.succession_rejections = rejections

        # Apply admission to state
        if admitted is not None and admitted.admitted:
            proposal = _find_succession_proposal(
                admitted.proposal_id, succession_candidates
            )
            if proposal and not proposal.is_self_succession():
                # Set pending successor key — activation at next boundary
                internal_state.pending_successor_key = (
                    proposal.successor_public_key
                )

    # ------------------------------------------------------------------
    # Step 4: Treaty revocation admission
    # ------------------------------------------------------------------
    revocation_events: List[TreatyAdmissionEvent] = []
    if treaty_revocation_candidates:
        rev_pipeline = TreatyAdmissionPipeline(
            constitution=constitution_frame,
            active_treaty_set=internal_state.active_treaty_set,
            cycle_index=internal_state.cycle_index,
        )
        rev_admitted, rev_rejected, rev_events = (
            rev_pipeline.evaluate_revocations(treaty_revocation_candidates)
        )
        output.treaty_revocations_admitted = rev_admitted
        output.treaty_revocations_rejected = rev_rejected
        revocation_events = rev_events

        # Apply admitted revocations immediately
        for rev_result in rev_admitted:
            rev_grant_id = _find_grant_id_from_result(
                rev_result, treaty_revocation_candidates
            )
            if rev_grant_id:
                internal_state.active_treaty_set.revoke(rev_grant_id)

    # ------------------------------------------------------------------
    # Step 5: Treaty ratification admission
    # ------------------------------------------------------------------
    if treaty_ratification_candidates:
        rat_pipeline = RatificationAdmissionPipeline(
            sovereign_public_key_active=(
                internal_state.sovereign_public_key_active
            ),
            prior_sovereign_public_key=(
                internal_state.prior_sovereign_public_key
            ),
            active_treaty_set=internal_state.active_treaty_set,
            density_upper_bound=constitution_frame.density_upper_bound(),
            action_permissions=constitution_frame.get_action_permissions(),
            action_type_count=len(constitution_frame.get_action_types()),
            current_cycle=internal_state.cycle_index,
        )
        rat_admissions, rat_rejections = rat_pipeline.evaluate(
            treaty_ratification_candidates
        )
        output.ratification_admissions = rat_admissions
        output.ratification_rejections = rat_rejections

    # ------------------------------------------------------------------
    # Step 6: Density checkpoint A (full repair)
    # ------------------------------------------------------------------
    density_bound = constitution_frame.density_upper_bound()
    action_perms = constitution_frame.get_action_permissions()
    action_type_count = len(constitution_frame.get_action_types())

    density_a_events = (
        internal_state.active_treaty_set.apply_density_repair(
            density_upper_bound=density_bound,
            action_permissions=action_perms,
            action_type_count=action_type_count,
            current_cycle=internal_state.cycle_index,
        )
    )
    all_revalidation_events.extend(density_a_events)

    # ------------------------------------------------------------------
    # Step 7: Treaty grant admission
    # ------------------------------------------------------------------
    grant_events: List[TreatyAdmissionEvent] = []
    if treaty_grant_candidates:
        # Block new grants if suspensions exist
        if internal_state.active_treaty_set.has_suspensions():
            # Reject all with SUSPENSION_UNRESOLVED
            for grant_cand in treaty_grant_candidates:
                output.treaty_grants_rejected.append(
                    TreatyAdmissionResult(
                        artifact_id=grant_cand.id,
                        artifact_type="TreatyGrant",
                        admitted=False,
                        rejection_code=AuthorityCode.SUSPENSION_UNRESOLVED,
                        events=[TreatyAdmissionEvent(
                            artifact_id=grant_cand.id,
                            artifact_type="TreatyGrant",
                            gate="suspension_check",
                            result="fail",
                            reason_code=AuthorityCode.SUSPENSION_UNRESOLVED,
                        )],
                    )
                )
        else:
            sorted_grants = sorted(
                treaty_grant_candidates, key=lambda g: g.id
            )
            grant_pipeline = TreatyAdmissionPipeline(
                constitution=constitution_frame,
                active_treaty_set=internal_state.active_treaty_set,
                cycle_index=internal_state.cycle_index,
            )
            grant_admitted, grant_rejected, grant_evts = (
                grant_pipeline.evaluate_grants(sorted_grants)
            )
            output.treaty_grants_admitted = grant_admitted
            output.treaty_grants_rejected.extend(grant_rejected)
            grant_events = grant_evts

            for grant_result in grant_admitted:
                grant_obj = _find_grant_from_result(
                    grant_result, sorted_grants
                )
                if grant_obj:
                    grant_obj.grant_cycle = internal_state.cycle_index
                    internal_state.active_treaty_set.add_grant(grant_obj)

    output.treaty_admission_events = grant_events + revocation_events

    # ------------------------------------------------------------------
    # Step 8: Density checkpoint B (full repair)
    # ------------------------------------------------------------------
    density_b_events = (
        internal_state.active_treaty_set.apply_density_repair(
            density_upper_bound=density_bound,
            action_permissions=action_perms,
            action_type_count=action_type_count,
            current_cycle=internal_state.cycle_index,
        )
    )
    all_revalidation_events.extend(density_b_events)
    output.revalidation_events = all_revalidation_events

    # ------------------------------------------------------------------
    # Step 9: Amendment proposal queuing
    # ------------------------------------------------------------------
    amendment_output, amend_events, amend_rejected = _try_queue_amendment(
        amendment_candidates,
        constitution_frame,
        internal_state,
        cycle_time,
        None,  # schema
    )
    if amendment_output is not None:
        output.decision_type = DecisionTypeX3.QUEUE_AMENDMENT
        output.queued_proposal = amendment_output.queued_proposal
        if amendment_output.state_delta is not None:
            output.state_delta = amendment_output.state_delta
        output.amendment_admission_events = amend_events
        return output
    if amend_events:
        output.amendment_admission_events = amend_events

    # ------------------------------------------------------------------
    # Step 10: RSA action admission
    # ------------------------------------------------------------------
    rsa_action_result = _action_path(
        observations,
        rsa_action_candidates,
        constitution_frame,
        internal_state,
        Path("."),  # repo_root — not used in policy core
        cycle_time,
    )

    # ------------------------------------------------------------------
    # Step 11: Delegated action admission
    # ------------------------------------------------------------------
    delegated_warrants: List[ExecutionWarrant] = []
    delegated_rejections: List[Dict[str, Any]] = []

    active_grants = internal_state.active_treaty_set.active_grants(
        internal_state.cycle_index
    )

    for dar in delegated_action_candidates:
        warrant_or_rejection = _evaluate_delegated_action(
            dar, constitution_frame, active_grants,
            internal_state.cycle_index, cycle_time,
        )
        if isinstance(warrant_or_rejection, ExecutionWarrant):
            delegated_warrants.append(warrant_or_rejection)
        else:
            delegated_rejections.append(warrant_or_rejection)

    # ------------------------------------------------------------------
    # Step 12: Warrant issuance & output assembly
    # ------------------------------------------------------------------
    all_warrants: List[ExecutionWarrant] = []
    all_bundles: List[CandidateBundle] = []

    if rsa_action_result.decision_type == DecisionTypeX1.ACTION:
        if rsa_action_result.warrant:
            rsa_w = rsa_action_result.warrant
            rsa_warrant = make_warrant_with_deterministic_id(
                action_request_id=rsa_w.action_request_id,
                action_type=rsa_w.action_type,
                scope_constraints=rsa_w.scope_constraints,
                issued_in_cycle=rsa_w.issued_in_cycle,
                created_at=rsa_w.created_at,
                origin="rsa",
            )
            all_warrants.append(rsa_warrant)
        if rsa_action_result.bundle:
            all_bundles.append(rsa_action_result.bundle)

    all_warrants.extend(delegated_warrants)

    origin_rank = constitution_frame.get_origin_rank()

    def warrant_sort_key(w: ExecutionWarrant) -> Tuple[int, str]:
        origin = w.scope_constraints.get("origin", "rsa")
        rank = origin_rank.get(origin, 99)
        return (rank, w.warrant_id)

    all_warrants.sort(key=warrant_sort_key)

    if all_warrants:
        output.decision_type = DecisionTypeX3.ACTION
        output.warrants = all_warrants
        output.bundles = all_bundles
        output.delegated_warrants = delegated_warrants
        output.delegated_rejections = delegated_rejections
        output.admission_events = rsa_action_result.admission_events
        output.selection_event = rsa_action_result.selection_event
        output.admitted = rsa_action_result.admitted
        output.rejected = rsa_action_result.rejected
        return output

    if rsa_action_result.decision_type == DecisionTypeX1.REFUSE:
        output.decision_type = DecisionTypeX3.REFUSE
        output.refusal = rsa_action_result.refusal
        output.admission_events = rsa_action_result.admission_events
        output.admitted = rsa_action_result.admitted
        output.rejected = rsa_action_result.rejected
        output.delegated_rejections = delegated_rejections
        return output

    # Fallback REFUSE — no admissible actions
    refusal = RefusalRecord(
        reason_code=RefusalReasonCode.NO_ADMISSIBLE_ACTION.value,
        failed_gate="none",
        missing_artifacts=[],
        authority_ids_considered=[],
        observation_ids_referenced=[o.id for o in observations],
        rejection_summary_by_gate={},
        created_at=cycle_time,
    )
    output.refusal = refusal
    output.delegated_rejections = delegated_rejections
    return output


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_succession_proposal(
    proposal_id: str,
    candidates: List[SuccessionProposal],
) -> Optional[SuccessionProposal]:
    """Find a succession proposal by ID."""
    for p in candidates:
        if p.id == proposal_id:
            return p
    return None
