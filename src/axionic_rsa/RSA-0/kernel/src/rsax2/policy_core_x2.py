"""
RSA X-2 — Policy Core (Treaty-Aware)

Extends policy_core_x1 with treaty-constrained delegation:

Per-cycle ordering (CL-CYCLE-ORDERING):
  Step 1: Governance artifact admission
    1a. Amendment adoption (if eligible)
    1b. Treaty revocation admission and application
    1c. Treaty grant admission (canonical hash order within grants)
    1d. Amendment proposal queuing
  Step 2: Revocation processing (already applied in 1b)
  Step 3: Active treaty set recomputation
  Step 4: ActionRequest admission (including delegated with signature check)
  Step 5: ExecutionWarrant issuance (multiple warrants per cycle;
          origin_rank ASC, then warrant_id ASC)

warrant_id = SHA-256 of canonical JSON of warrant payload excluding warrant_id.
Encoding: hex_lowercase per CL-WARRANT-ID-DETERMINISM.

Composes X-1's policy core for amendment and base action paths.
Pure, deterministic, no side effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..artifacts import (
    ActionRequest,
    Author,
    CandidateBundle,
    Decision,
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
from ..admission import AdmissionEvent, AdmissionPipeline, AdmissionResult
from ..policy_core import extract_cycle_time, _make_exit_record, _make_budget_refusal
from ..selector import SelectionEvent, select

from ..rsax1.artifacts_x1 import (
    AmendmentAdoptionRecord,
    AmendmentProposal,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
    StateDelta,
)
from ..rsax1.admission_x1 import (
    AmendmentAdmissionEvent,
    AmendmentAdmissionPipeline,
    AmendmentAdmissionResult,
    check_cooling_satisfied,
    invalidate_stale_proposals,
)
from ..rsax1.policy_core_x1 import (
    PolicyOutputX1,
    _action_path,
    _make_admission_pipeline,
    _try_adopt,
    _try_queue_amendment,
)

from .artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyAdmissionEvent,
    TreatyAdmissionResult,
    TreatyGrant,
    TreatyRejectionCode,
    TreatyRevalidationEvent,
    TreatyRevocation,
)
from .constitution_x2 import ConstitutionX2
from .treaty_admission import TreatyAdmissionPipeline
from .signature import verify_action_request_signature


# ---------------------------------------------------------------------------
# Cycle ordering modes
# ---------------------------------------------------------------------------

CYCLE_ORDERING_DEFAULT = "DEFAULT"
CYCLE_ORDERING_X2D_TOPOLOGICAL = "X2D_TOPOLOGICAL"


# ---------------------------------------------------------------------------
# Warrant ID computation (CL-WARRANT-ID-DETERMINISM)
# ---------------------------------------------------------------------------

def compute_warrant_id(warrant_dict: Dict[str, Any]) -> str:
    """
    Compute warrant_id = SHA-256 of canonical JSON of warrant payload
    excluding warrant_id field. Encoding: hex_lowercase.
    """
    payload = {k: v for k, v in warrant_dict.items() if k != "warrant_id"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_warrant_with_deterministic_id(
    action_request_id: str,
    action_type: str,
    scope_constraints: Dict[str, Any],
    issued_in_cycle: int,
    created_at: str,
    origin: str,
) -> ExecutionWarrant:
    """
    Create an ExecutionWarrant with deterministic warrant_id.
    The origin field is stored inside scope_constraints.
    """
    sc = dict(scope_constraints)
    sc["origin"] = origin

    warrant = ExecutionWarrant(
        action_request_id=action_request_id,
        action_type=action_type,
        scope_constraints=sc,
        issued_in_cycle=issued_in_cycle,
        single_use=True,
        warrant_id="",  # placeholder
        created_at=created_at,
    )
    # Compute deterministic warrant_id
    wd = warrant.to_dict()
    warrant.warrant_id = compute_warrant_id(wd)
    return warrant


# ---------------------------------------------------------------------------
# Extended Policy Output (X-2)
# ---------------------------------------------------------------------------

@dataclass
class PolicyOutputX2:
    """Full output of X-2 policy core evaluation."""
    decision_type: str  # DecisionTypeX2 value
    # ACTION path — may have multiple warrants
    bundles: List[CandidateBundle] = field(default_factory=list)
    warrants: List[ExecutionWarrant] = field(default_factory=list)
    # REFUSE path
    refusal: Optional[RefusalRecord] = None
    # EXIT path
    exit_record: Optional[ExitRecord] = None
    # QUEUE_AMENDMENT path
    queued_proposal: Optional[AmendmentProposal] = None
    # ADOPT path
    adoption_record: Optional[AmendmentAdoptionRecord] = None
    # State delta
    state_delta: Optional[StateDelta] = None
    # Trace events
    admission_events: List[AdmissionEvent] = field(default_factory=list)
    amendment_admission_events: List[AmendmentAdmissionEvent] = field(default_factory=list)
    treaty_admission_events: List[TreatyAdmissionEvent] = field(default_factory=list)
    revalidation_events: List[TreatyRevalidationEvent] = field(default_factory=list)
    selection_event: Optional[SelectionEvent] = None
    admitted: List[AdmissionResult] = field(default_factory=list)
    rejected: List[AdmissionResult] = field(default_factory=list)
    treaty_grants_admitted: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_grants_rejected: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_revocations_admitted: List[TreatyAdmissionResult] = field(default_factory=list)
    treaty_revocations_rejected: List[TreatyAdmissionResult] = field(default_factory=list)
    # Delegated action results
    delegated_warrants: List[ExecutionWarrant] = field(default_factory=list)
    delegated_rejections: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"decision_type": self.decision_type}
        if self.bundles:
            d["bundles"] = [b.to_dict() for b in self.bundles]
        if self.warrants:
            d["warrants"] = [w.to_dict() for w in self.warrants]
        if self.refusal:
            d["refusal"] = self.refusal.to_dict()
        if self.exit_record:
            d["exit_record"] = self.exit_record.to_dict()
        if self.queued_proposal:
            d["queued_proposal"] = self.queued_proposal.to_dict_id()
        if self.adoption_record:
            d["adoption_record"] = self.adoption_record.to_dict()
        if self.state_delta:
            d["state_delta"] = self.state_delta.to_dict()
        if self.delegated_warrants:
            d["delegated_warrants"] = [w.to_dict() for w in self.delegated_warrants]
        if self.delegated_rejections:
            d["delegated_rejections"] = self.delegated_rejections
        return d


# ---------------------------------------------------------------------------
# Delegated Action Request (with signature)
# ---------------------------------------------------------------------------

@dataclass
class DelegatedActionRequest:
    """
    ActionRequest submitted by a treaty grantee with signature.
    Per CL-SCOPE-CLAIM-ZONE-FORMAT: must include both scope_type and scope_zone.
    """
    action_type: str
    fields: Dict[str, Any]
    grantee_identifier: str
    authority_citations: List[str]  # must include treaty: citation
    signature: str  # hex-encoded Ed25519 signature
    scope_type: str = ""  # e.g., "FILE_PATH", "LOG_STREAM"
    scope_zone: str = ""  # zone label from ScopeEnumerations
    created_at: str = ""
    id: str = ""

    def to_action_request_dict(self) -> Dict[str, Any]:
        """Return the dict used for signature verification (excludes signature)."""
        d: Dict[str, Any] = {
            "type": "ActionRequest",
            "action_type": self.action_type,
            "fields": self.fields,
            "grantee_identifier": self.grantee_identifier,
            "authority_citations": sorted(self.authority_citations),
            "scope_type": self.scope_type,
            "scope_zone": self.scope_zone,
            "created_at": self.created_at,
        }
        if self.id:
            d["id"] = self.id
        return d


# ---------------------------------------------------------------------------
# Policy Core X-2
# ---------------------------------------------------------------------------

def policy_core_x2(
    observations: List[Observation],
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    treaty_grant_candidates: List[TreatyGrant],
    treaty_revocation_candidates: List[TreatyRevocation],
    delegated_action_candidates: List[DelegatedActionRequest],
    constitution: ConstitutionX2,
    internal_state: InternalStateX2,
    repo_root: Path,
    schema: Optional[Dict[str, Any]] = None,
    cycle_ordering_mode: str = CYCLE_ORDERING_DEFAULT,
) -> PolicyOutputX2:
    """
    X-2 policy core. Pure, deterministic.

    Implements 5-step cycle ordering per CL-CYCLE-ORDERING.

    cycle_ordering_mode:
      - "DEFAULT": original CL-CYCLE-ORDERING (revocations before grants)
      - "X2D_TOPOLOGICAL": X-2D topological time
        (amendment adoption → revalidation → grants → revocations →
         density repair → actions)
    """
    output = PolicyOutputX2(decision_type=DecisionTypeX2.REFUSE)

    # ---------------------------------------------------------------
    # Pre-admission: timestamp, integrity, budget (same as X-1)
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
                        constitution.make_citation("CL-EXIT-POLICY"),
                    ],
                    scope_claim={
                        "observation_ids": [obs.id],
                        "claim": f"EXIT required: {event}",
                    },
                    justification=f"Integrity risk: {event} — {obs.payload.get('detail', '')}",
                    created_at=cycle_time,
                )
                output.decision_type = DecisionTypeX2.EXIT
                output.exit_record = exit_record
                return output

    # Budget check
    for obs in observations:
        if obs.kind == ObservationKind.BUDGET.value:
            token_count = obs.payload.get("llm_output_token_count", 0)
            max_tokens = constitution.max_total_tokens_per_cycle()
            if token_count > max_tokens:
                refusal = _make_budget_refusal(observations, cycle_time)
                output.refusal = refusal
                return output

    # ===================================================================
    # STEP 1: Governance artifact admission
    # ===================================================================

    if cycle_ordering_mode == CYCLE_ORDERING_X2D_TOPOLOGICAL:
        return _x2d_topological_path(
            observations, action_candidates, amendment_candidates,
            pending_amendment_candidates, treaty_grant_candidates,
            treaty_revocation_candidates, delegated_action_candidates,
            constitution, internal_state, repo_root, schema, cycle_time, output,
        )

    # --- Step 1a: Amendment adoption (if eligible) ---
    adoption_result = _try_adopt(
        pending_amendment_candidates,
        constitution,
        internal_state,
        cycle_time,
        schema,
    )
    if adoption_result is not None:
        output.decision_type = DecisionTypeX2.ADOPT
        output.adoption_record = adoption_result.adoption_record
        output.state_delta = adoption_result.state_delta
        return output

    # --- Step 1b: Treaty revocation admission and application ---
    revocation_events: List[TreatyAdmissionEvent] = []
    if treaty_revocation_candidates:
        rev_pipeline = TreatyAdmissionPipeline(
            constitution=constitution,
            active_treaty_set=internal_state.active_treaty_set,
            cycle_index=internal_state.cycle_index,
        )
        rev_admitted, rev_rejected, rev_events = rev_pipeline.evaluate_revocations(
            treaty_revocation_candidates
        )
        output.treaty_revocations_admitted = rev_admitted
        output.treaty_revocations_rejected = rev_rejected
        revocation_events = rev_events

        # Apply admitted revocations immediately (before grant admission)
        for rev_result in rev_admitted:
            rev_grant_id = _find_grant_id_from_result(rev_result, treaty_revocation_candidates)
            if rev_grant_id:
                internal_state.active_treaty_set.revoke(rev_grant_id)

    # --- Step 1c: Treaty grant admission (canonical hash order) ---
    grant_events: List[TreatyAdmissionEvent] = []
    if treaty_grant_candidates:
        # Sort candidates by canonical hash for deterministic ordering
        sorted_grants = sorted(treaty_grant_candidates, key=lambda g: g.id)

        grant_pipeline = TreatyAdmissionPipeline(
            constitution=constitution,
            active_treaty_set=internal_state.active_treaty_set,
            cycle_index=internal_state.cycle_index,
        )
        grant_admitted, grant_rejected, grant_evts = grant_pipeline.evaluate_grants(
            sorted_grants
        )
        output.treaty_grants_admitted = grant_admitted
        output.treaty_grants_rejected = grant_rejected
        grant_events = grant_evts

        # Apply admitted grants to the active treaty set
        for grant_result in grant_admitted:
            grant_obj = _find_grant_from_result(grant_result, sorted_grants)
            if grant_obj:
                grant_obj.grant_cycle = internal_state.cycle_index
                internal_state.active_treaty_set.add_grant(grant_obj)

    output.treaty_admission_events = revocation_events + grant_events

    # --- Step 1d: Amendment proposal queuing ---
    amendment_output, amend_events, amend_rejected = _try_queue_amendment(
        amendment_candidates,
        constitution,
        internal_state,
        cycle_time,
        schema,
    )
    if amendment_output is not None:
        output.decision_type = DecisionTypeX2.QUEUE_AMENDMENT
        output.queued_proposal = amendment_output.queued_proposal
        output.state_delta = amendment_output.state_delta
        output.amendment_admission_events = amend_events
        return output
    if amend_events:
        output.amendment_admission_events = amend_events

    # ===================================================================
    # STEPS 2-3: Revocation processing & Active treaty set recomputation
    # (Already applied in Step 1b; treaty set is current)
    # ===================================================================

    # ===================================================================
    # STEP 4: ActionRequest admission (including delegated)
    # ===================================================================

    # --- 4a: Normal (RSA) action admission ---
    rsa_action_result = _action_path(
        observations,
        action_candidates,
        constitution,
        internal_state,
        repo_root,
        cycle_time,
    )

    # --- 4b: Delegated action admission ---
    delegated_warrants: List[ExecutionWarrant] = []
    delegated_rejections: List[Dict[str, Any]] = []

    active_grants = internal_state.active_treaty_set.active_grants(internal_state.cycle_index)

    for dar in delegated_action_candidates:
        warrant_or_rejection = _evaluate_delegated_action(
            dar, constitution, active_grants, internal_state.cycle_index, cycle_time,
        )
        if isinstance(warrant_or_rejection, ExecutionWarrant):
            delegated_warrants.append(warrant_or_rejection)
        else:
            delegated_rejections.append(warrant_or_rejection)

    # ===================================================================
    # STEP 5: Warrant issuance & output assembly
    # ===================================================================

    # Collect all warrants: RSA warrant (if any) + delegated warrants
    all_warrants: List[ExecutionWarrant] = []
    all_bundles: List[CandidateBundle] = []

    if rsa_action_result.decision_type == DecisionTypeX1.ACTION:
        if rsa_action_result.warrant:
            # Wrap RSA warrant with origin and deterministic warrant_id
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

    # Add delegated warrants
    all_warrants.extend(delegated_warrants)

    # Sort warrants per CL-WARRANT-EXECUTION-ORDER:
    # origin_rank ASC (rsa=0, delegated=1), then warrant_id ASC
    origin_rank = constitution.get_origin_rank()

    def warrant_sort_key(w: ExecutionWarrant) -> Tuple[int, str]:
        origin = w.scope_constraints.get("origin", "rsa")
        rank = origin_rank.get(origin, 99)
        return (rank, w.warrant_id)

    all_warrants.sort(key=warrant_sort_key)

    if all_warrants:
        output.decision_type = DecisionTypeX2.ACTION
        output.warrants = all_warrants
        output.bundles = all_bundles
        output.delegated_warrants = delegated_warrants
        output.delegated_rejections = delegated_rejections
        output.admission_events = rsa_action_result.admission_events
        output.selection_event = rsa_action_result.selection_event
        output.admitted = rsa_action_result.admitted
        output.rejected = rsa_action_result.rejected
        return output

    # No warrants at all — REFUSE
    if rsa_action_result.decision_type == DecisionTypeX1.REFUSE:
        output.decision_type = DecisionTypeX2.REFUSE
        output.refusal = rsa_action_result.refusal
        output.admission_events = rsa_action_result.admission_events
        output.admitted = rsa_action_result.admitted
        output.rejected = rsa_action_result.rejected
        output.delegated_rejections = delegated_rejections
        return output

    # Fallback REFUSE
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
# Delegated Action Evaluation
# ---------------------------------------------------------------------------

def _evaluate_delegated_action(
    dar: DelegatedActionRequest,
    constitution: ConstitutionX2,
    active_grants: List[TreatyGrant],
    cycle_index: int,
    cycle_time: str,
) -> ExecutionWarrant | Dict[str, Any]:
    """
    Evaluate a single delegated ActionRequest.
    Returns ExecutionWarrant on success, rejection dict on failure.
    """
    # Step 1: Signature verification (MUST happen before authority resolution)
    if not dar.signature:
        return {
            "action_request_id": dar.id,
            "rejection_code": TreatyRejectionCode.SIGNATURE_MISSING,
            "detail": "delegated ActionRequest has no signature",
        }

    valid, error_msg = verify_action_request_signature(
        dar.grantee_identifier,
        dar.to_action_request_dict(),
        dar.signature,
    )
    if not valid:
        return {
            "action_request_id": dar.id,
            "rejection_code": TreatyRejectionCode.SIGNATURE_INVALID,
            "detail": f"signature verification failed: {error_msg}",
        }

    # Step 2: Verify action is in closed action set
    if dar.action_type not in constitution.get_closed_action_set():
        return {
            "action_request_id": dar.id,
            "rejection_code": TreatyRejectionCode.INVALID_FIELD,
            "detail": f"action '{dar.action_type}' not in closed action set",
        }

    # Step 3: Validate scope_type and scope_zone per CL-SCOPE-CLAIM-ZONE-FORMAT
    scope_rule = constitution.get_action_scope_rule(dar.action_type)
    if scope_rule and scope_rule.get("scope_claim_required", True):
        if not dar.scope_type:
            return {
                "action_request_id": dar.id,
                "rejection_code": TreatyRejectionCode.INVALID_FIELD,
                "detail": "scope_type required but missing",
            }
        if not dar.scope_zone:
            return {
                "action_request_id": dar.id,
                "rejection_code": TreatyRejectionCode.INVALID_FIELD,
                "detail": "scope_zone required but missing",
            }

        # scope_type must be in valid_scope_types for this action
        valid_scope_types = constitution.get_valid_scope_types(dar.action_type)
        if dar.scope_type not in valid_scope_types:
            return {
                "action_request_id": dar.id,
                "rejection_code": TreatyRejectionCode.SCOPE_COLLAPSE,
                "detail": f"scope_type '{dar.scope_type}' not valid for action '{dar.action_type}'",
            }

        # scope_zone must be in ScopeEnumerations zones for that scope_type
        constitutional_zones = constitution.get_zones_for_scope_type(dar.scope_type)
        if dar.scope_zone not in constitutional_zones:
            return {
                "action_request_id": dar.id,
                "rejection_code": TreatyRejectionCode.SCOPE_COLLAPSE,
                "detail": f"scope_zone '{dar.scope_zone}' not in ScopeEnumerations for '{dar.scope_type}'",
            }

        # Enforce permitted_zones for Notify (and any other constrained actions)
        permitted_zones = constitution.get_permitted_zones(dar.action_type)
        if permitted_zones is not None and dar.scope_zone not in permitted_zones:
            return {
                "action_request_id": dar.id,
                "rejection_code": TreatyRejectionCode.SCOPE_COLLAPSE,
                "detail": f"scope_zone '{dar.scope_zone}' not in permitted_zones for '{dar.action_type}'",
            }

    # Step 4: Find an active grant that covers (grantee, action, scope)
    matching_grant = _find_matching_grant(dar, active_grants, constitution)
    if matching_grant is None:
        return {
            "action_request_id": dar.id,
            "rejection_code": TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
            "detail": f"no active grant covers action '{dar.action_type}' for grantee",
        }

    # Step 5: Treaty citation validation
    has_treaty_citation = any(c.startswith("treaty:") for c in dar.authority_citations)
    if not has_treaty_citation:
        return {
            "action_request_id": dar.id,
            "rejection_code": TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
            "detail": "delegated ActionRequest must include a treaty: citation",
        }

    # Step 6: Issue delegated warrant with deterministic warrant_id
    warrant = make_warrant_with_deterministic_id(
        action_request_id=dar.id or f"dar-{dar.grantee_identifier[:16]}-{dar.action_type}",
        action_type=dar.action_type,
        scope_constraints={
            "grantee_identifier": dar.grantee_identifier,
            "grant_id": matching_grant.id,
            "scope_type": dar.scope_type,
            "scope_zone": dar.scope_zone,
        },
        issued_in_cycle=cycle_index,
        created_at=cycle_time,
        origin="delegated",
    )

    return warrant


def _find_matching_grant(
    dar: DelegatedActionRequest,
    active_grants: List[TreatyGrant],
    constitution: ConstitutionX2,
) -> Optional[TreatyGrant]:
    """
    Find the first active grant that:
    - matches grantee_identifier
    - includes the requested action in granted_actions
    - scope_zone (if specified) is within grant's scope_constraints[scope_type]
    """
    for grant in active_grants:
        if grant.grantee_identifier != dar.grantee_identifier:
            continue
        if dar.action_type not in grant.granted_actions:
            continue
        if dar.scope_type and dar.scope_zone:
            # Check scope_constraints map: scope_type key must have scope_zone
            grant_zones = grant.scope_constraints.get(dar.scope_type, [])
            if dar.scope_zone not in grant_zones:
                continue
        return grant
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_grant_id_from_result(
    result: TreatyAdmissionResult,
    revocations: List[TreatyRevocation],
) -> Optional[str]:
    """Find the grant_id from a revocation admission result."""
    for rev in revocations:
        if rev.id == result.artifact_id:
            return rev.grant_id
    return None


def _find_grant_from_result(
    result: TreatyAdmissionResult,
    grants: List[TreatyGrant],
) -> Optional[TreatyGrant]:
    """Find the TreatyGrant object from an admission result."""
    for grant in grants:
        if grant.id == result.artifact_id:
            return grant
    return None


# ---------------------------------------------------------------------------
# X-2D Topological Time Path
# ---------------------------------------------------------------------------

def _x2d_topological_path(
    observations: List[Observation],
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    treaty_grant_candidates: List[TreatyGrant],
    treaty_revocation_candidates: List[TreatyRevocation],
    delegated_action_candidates: List[DelegatedActionRequest],
    constitution: ConstitutionX2,
    internal_state: InternalStateX2,
    repo_root: Path,
    schema: Optional[Dict[str, Any]],
    cycle_time: str,
    output: PolicyOutputX2,
) -> PolicyOutputX2:
    """X-2D topological ordering within a single cycle.

    Binding order (per Q&A V79, P62):
      1. Amendment adoption (composed via X-1 engine)
      2. Treaty revalidation (post-amendment, before grants)
      3. Treaty grants
      4. Treaty revocations
      5. Expiry (implicit in active_grants filter)
      6. Density enforcement + repair loop
      7. RSA actions
      8. Delegated actions

    Amendment adoption does NOT early-return; it continues into the full
    cycle so revalidation and action evaluation happen in the same call.
    """
    all_revalidation_events: List[TreatyRevalidationEvent] = []

    # ------------------------------------------------------------------
    # Step T1: Amendment adoption (non-early-return in topological mode)
    # ------------------------------------------------------------------
    adoption_result = _try_adopt(
        pending_amendment_candidates,
        constitution,
        internal_state,
        cycle_time,
        schema,
    )
    if adoption_result is not None:
        output.adoption_record = adoption_result.adoption_record
        output.state_delta = adoption_result.state_delta
        # Apply adoption: update constitution in-flight for revalidation.
        # The state_delta contains the new constitution hash; the harness
        # must supply the updated constitution for subsequent cycles, but
        # within *this* cycle we use the updated state for revalidation.
        # NOTE: constitution is already the post-adoption state if the
        # harness applied it. For the kernel, we proceed with the current
        # constitution object which reflects pre-adoption state unless the
        # caller updates it. In X-2D runner, the caller is responsible for
        # passing the post-adoption constitution. We log the adoption and
        # proceed.

    # ------------------------------------------------------------------
    # Step T2: Treaty revalidation (post-amendment, before grants)
    # ------------------------------------------------------------------
    reval_events = internal_state.active_treaty_set.apply_constitutional_revalidation(
        constitution, internal_state.cycle_index,
    )
    all_revalidation_events.extend(reval_events)

    # ------------------------------------------------------------------
    # Step T3: Treaty grant admission (grants BEFORE revocations)
    # ------------------------------------------------------------------
    grant_events: List[TreatyAdmissionEvent] = []
    if treaty_grant_candidates:
        sorted_grants = sorted(treaty_grant_candidates, key=lambda g: g.id)
        grant_pipeline = TreatyAdmissionPipeline(
            constitution=constitution,
            active_treaty_set=internal_state.active_treaty_set,
            cycle_index=internal_state.cycle_index,
        )
        grant_admitted, grant_rejected, grant_evts = grant_pipeline.evaluate_grants(
            sorted_grants
        )
        output.treaty_grants_admitted = grant_admitted
        output.treaty_grants_rejected = grant_rejected
        grant_events = grant_evts

        for grant_result in grant_admitted:
            grant_obj = _find_grant_from_result(grant_result, sorted_grants)
            if grant_obj:
                grant_obj.grant_cycle = internal_state.cycle_index
                internal_state.active_treaty_set.add_grant(grant_obj)

    # ------------------------------------------------------------------
    # Step T4: Treaty revocation admission (revocations AFTER grants)
    # ------------------------------------------------------------------
    revocation_events: List[TreatyAdmissionEvent] = []
    if treaty_revocation_candidates:
        rev_pipeline = TreatyAdmissionPipeline(
            constitution=constitution,
            active_treaty_set=internal_state.active_treaty_set,
            cycle_index=internal_state.cycle_index,
        )
        rev_admitted, rev_rejected, rev_events = rev_pipeline.evaluate_revocations(
            treaty_revocation_candidates
        )
        output.treaty_revocations_admitted = rev_admitted
        output.treaty_revocations_rejected = rev_rejected
        revocation_events = rev_events

        for rev_result in rev_admitted:
            rev_grant_id = _find_grant_id_from_result(
                rev_result, treaty_revocation_candidates
            )
            if rev_grant_id:
                internal_state.active_treaty_set.revoke(rev_grant_id)

    output.treaty_admission_events = grant_events + revocation_events

    # ------------------------------------------------------------------
    # Step T5: Density enforcement + repair loop
    # ------------------------------------------------------------------
    density_bound = constitution.density_upper_bound()
    action_perms = constitution.get_action_permissions()
    action_type_count = len(constitution.get_action_types())

    density_repair_events = internal_state.active_treaty_set.apply_density_repair(
        density_upper_bound=density_bound,
        action_permissions=action_perms,
        action_type_count=action_type_count,
        current_cycle=internal_state.cycle_index,
    )
    all_revalidation_events.extend(density_repair_events)
    output.revalidation_events = all_revalidation_events

    # ------------------------------------------------------------------
    # Step T6: Amendment proposal queuing
    # ------------------------------------------------------------------
    amendment_output, amend_events, amend_rejected = _try_queue_amendment(
        amendment_candidates,
        constitution,
        internal_state,
        cycle_time,
        schema,
    )
    if amendment_output is not None:
        output.decision_type = DecisionTypeX2.QUEUE_AMENDMENT
        output.queued_proposal = amendment_output.queued_proposal
        output.state_delta = amendment_output.state_delta
        output.amendment_admission_events = amend_events
        return output
    if amend_events:
        output.amendment_admission_events = amend_events

    # ------------------------------------------------------------------
    # Step T7: RSA action admission
    # ------------------------------------------------------------------
    rsa_action_result = _action_path(
        observations,
        action_candidates,
        constitution,
        internal_state,
        repo_root,
        cycle_time,
    )

    # ------------------------------------------------------------------
    # Step T8: Delegated action admission
    # ------------------------------------------------------------------
    delegated_warrants: List[ExecutionWarrant] = []
    delegated_rejections: List[Dict[str, Any]] = []

    active_grants = internal_state.active_treaty_set.active_grants(
        internal_state.cycle_index
    )

    for dar in delegated_action_candidates:
        warrant_or_rejection = _evaluate_delegated_action(
            dar, constitution, active_grants, internal_state.cycle_index, cycle_time,
        )
        if isinstance(warrant_or_rejection, ExecutionWarrant):
            delegated_warrants.append(warrant_or_rejection)
        else:
            delegated_rejections.append(warrant_or_rejection)

    # ------------------------------------------------------------------
    # Step T9: Warrant issuance & output assembly
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

    origin_rank = constitution.get_origin_rank()

    def warrant_sort_key(w: ExecutionWarrant) -> Tuple[int, str]:
        origin = w.scope_constraints.get("origin", "rsa")
        rank = origin_rank.get(origin, 99)
        return (rank, w.warrant_id)

    all_warrants.sort(key=warrant_sort_key)

    if all_warrants:
        output.decision_type = DecisionTypeX2.ACTION
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
        output.decision_type = DecisionTypeX2.REFUSE
        output.refusal = rsa_action_result.refusal
        output.admission_events = rsa_action_result.admission_events
        output.admitted = rsa_action_result.admitted
        output.rejected = rsa_action_result.rejected
        output.delegated_rejections = delegated_rejections
        return output

    # Fallback REFUSE
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
