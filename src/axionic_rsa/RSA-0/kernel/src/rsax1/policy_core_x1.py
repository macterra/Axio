"""
RSA X-1 — Policy Core (Amendment-Aware)

Extends RSA-0's policy_core with amendment handling:
  policy_core_x1(observations, action_candidates, amendment_candidates,
                 pending_amendment_candidates, constitution, internal_state)
  → PolicyOutputX1

Evaluation order:
  1. Pre-admission checks (timestamp, integrity, budget) — same as RSA-0
  2. Adoption check for eligible pending amendments
  3. Amendment proposal admission (new proposals)
  4. Normal action admission + selection
  5. REFUSE/EXIT fallback

Composes RSA-0's policy_core for the action path.
Pure, deterministic, no side effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..artifacts import (
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
)
from ..admission import AdmissionEvent, AdmissionPipeline, AdmissionResult
from ..policy_core import extract_cycle_time, _make_exit_record, _make_budget_refusal
from ..selector import SelectionEvent, select

from .artifacts_x1 import (
    AmendmentAdoptionRecord,
    AmendmentProposal,
    AmendmentRejectionCode,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
    StateDelta,
)
from .admission_x1 import (
    AmendmentAdmissionEvent,
    AmendmentAdmissionPipeline,
    AmendmentAdmissionResult,
    check_cooling_satisfied,
    invalidate_stale_proposals,
)
from .constitution_x1 import ConstitutionX1


# ---------------------------------------------------------------------------
# Policy Output (X-1 extended)
# ---------------------------------------------------------------------------

@dataclass
class PolicyOutputX1:
    """Full output of X-1 policy core evaluation."""
    decision_type: str  # DecisionTypeX1 value
    # ACTION path
    bundle: Optional[CandidateBundle] = None
    warrant: Optional[ExecutionWarrant] = None
    # REFUSE path
    refusal: Optional[RefusalRecord] = None
    # EXIT path
    exit_record: Optional[ExitRecord] = None
    # QUEUE_AMENDMENT path
    queued_proposal: Optional[AmendmentProposal] = None
    # ADOPT path
    adoption_record: Optional[AmendmentAdoptionRecord] = None
    # State delta (for QUEUE_AMENDMENT/ADOPT)
    state_delta: Optional[StateDelta] = None
    # Trace events
    admission_events: List[AdmissionEvent] = field(default_factory=list)
    amendment_admission_events: List[AmendmentAdmissionEvent] = field(default_factory=list)
    selection_event: Optional[SelectionEvent] = None
    admitted: List[AdmissionResult] = field(default_factory=list)
    rejected: List[AdmissionResult] = field(default_factory=list)
    amendment_admitted: List[AmendmentAdmissionResult] = field(default_factory=list)
    amendment_rejected: List[AmendmentAdmissionResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"decision_type": self.decision_type}
        if self.bundle:
            d["bundle"] = self.bundle.to_dict()
        if self.warrant:
            d["warrant"] = self.warrant.to_dict()
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
        return d


# ---------------------------------------------------------------------------
# Policy Core X-1
# ---------------------------------------------------------------------------

def policy_core_x1(
    observations: List[Observation],
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    constitution: ConstitutionX1,
    internal_state: InternalStateX1,
    repo_root: Path,
    schema: Optional[Dict[str, Any]] = None,
) -> PolicyOutputX1:
    """
    X-1 policy core. Pure, deterministic.

    Parameters:
      observations: current cycle observations
      action_candidates: LLM-proposed action bundles
      amendment_candidates: LLM-proposed amendment proposals (new this cycle)
      pending_amendment_candidates: amendments queued from prior cycles
      constitution: current active ConstitutionX1
      internal_state: InternalStateX1 with pending_amendments etc.
      repo_root: repo root path for IO allowlist resolution
      schema: optional JSON schema for proposed constitution validation
    """
    # ---------------------------------------------------------------
    # Step 0: Pre-admission (timestamp, integrity, budget)
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
        return PolicyOutputX1(
            decision_type=DecisionTypeX1.REFUSE,
            refusal=refusal,
        )

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
                return PolicyOutputX1(
                    decision_type=DecisionTypeX1.EXIT,
                    exit_record=exit_record,
                )

    # Budget check
    for obs in observations:
        if obs.kind == ObservationKind.BUDGET.value:
            token_count = obs.payload.get("llm_output_token_count", 0)
            max_tokens = constitution.max_total_tokens_per_cycle()
            if token_count > max_tokens:
                refusal = _make_budget_refusal(observations, cycle_time)
                return PolicyOutputX1(
                    decision_type=DecisionTypeX1.REFUSE,
                    refusal=refusal,
                )

    # ---------------------------------------------------------------
    # Step 1: Adoption check (pending amendments that cooled off)
    # ---------------------------------------------------------------
    adoption_result = _try_adopt(
        pending_amendment_candidates,
        constitution,
        internal_state,
        cycle_time,
        schema,
    )
    if adoption_result is not None:
        return adoption_result

    # ---------------------------------------------------------------
    # Step 2: Amendment proposal admission (new proposals)
    # ---------------------------------------------------------------
    amendment_output = _try_queue_amendment(
        amendment_candidates,
        constitution,
        internal_state,
        cycle_time,
        schema,
    )
    if amendment_output is not None:
        return amendment_output

    # ---------------------------------------------------------------
    # Step 3: Normal action admission + selection (RSA-0 path)
    # ---------------------------------------------------------------
    return _action_path(
        observations,
        action_candidates,
        constitution,
        internal_state,
        repo_root,
        cycle_time,
    )


# ---------------------------------------------------------------------------
# Step 1: Try adoption
# ---------------------------------------------------------------------------

def _try_adopt(
    pending: List[PendingAmendment],
    constitution: ConstitutionX1,
    state: InternalStateX1,
    cycle_time: str,
    schema: Optional[Dict[str, Any]],
) -> Optional[PolicyOutputX1]:
    """
    Check if any pending amendment is eligible for adoption.
    Returns PolicyOutputX1 with ADOPT if found, None otherwise.
    """
    cooling = constitution.cooling_period_cycles()

    for p in pending:
        if not check_cooling_satisfied(p, state.cycle_index, cooling):
            continue

        # Re-validate gates 6-8B at adoption time
        # Build a temporary proposal to re-run through pipeline
        # (We only have the hash, not the full YAML — the host must provide it)
        # For now, adoption assumes the proposal was already fully validated at queue time
        # and the prior_hash still matches (forward-looking invalidation handles stale)

        if p.prior_constitution_hash != constitution.sha256:
            # Stale — skip (will be invalidated)
            continue

        # Issue adoption record
        effective_cycle = state.cycle_index + 1
        adoption_record = AmendmentAdoptionRecord(
            proposal_id=p.proposal_id,
            prior_constitution_hash=p.prior_constitution_hash,
            new_constitution_hash=p.proposed_constitution_hash,
            effective_cycle=effective_cycle,
            authority_citations=[
                constitution.make_authority_citation("AUTH_GOVERNANCE"),
                constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at=cycle_time,
        )

        # Invalidate stale proposals
        remaining, invalidated = invalidate_stale_proposals(
            [pp for pp in pending if pp.proposal_id != p.proposal_id],
            p.proposed_constitution_hash,
        )

        delta = StateDelta(
            delta_type="adopt_amendment",
            payload={
                "adoption_record": adoption_record.to_dict(),
                "new_constitution_hash": p.proposed_constitution_hash,
                "effective_cycle": effective_cycle,
                "invalidated_proposals": [inv.proposal_id for inv in invalidated],
                "remaining_pending": [r.to_dict() for r in remaining],
            },
        )

        return PolicyOutputX1(
            decision_type=DecisionTypeX1.ADOPT,
            adoption_record=adoption_record,
            state_delta=delta,
        )

    return None


# ---------------------------------------------------------------------------
# Step 2: Try queue amendment
# ---------------------------------------------------------------------------

def _try_queue_amendment(
    amendment_candidates: List[AmendmentProposal],
    constitution: ConstitutionX1,
    state: InternalStateX1,
    cycle_time: str,
    schema: Optional[Dict[str, Any]],
) -> Optional[PolicyOutputX1]:
    """
    Run amendment candidates through admission pipeline.
    If any admitted, queue the first one (deterministic: by proposal ID sort).
    """
    if not amendment_candidates:
        return None

    # Budget check
    max_per_cycle = constitution.max_amendment_candidates_per_cycle()
    candidates = amendment_candidates[:max_per_cycle]

    pipeline = AmendmentAdmissionPipeline(
        constitution=constitution,
        schema=schema,
        pending_amendments=state.pending_amendments,
        cycle_index=state.cycle_index,
    )

    admitted, rejected, events = pipeline.evaluate(candidates)

    if not admitted:
        # All rejected — fall through to action path
        return None

    # Select first by proposal ID (deterministic)
    admitted.sort(key=lambda r: r.proposal.id)
    selected = admitted[0]

    new_pending = PendingAmendment(
        proposal_id=selected.proposal.id,
        prior_constitution_hash=selected.proposal.prior_constitution_hash,
        proposed_constitution_hash=selected.proposal.proposed_constitution_hash,
        proposal_cycle=state.cycle_index,
    )

    delta = StateDelta(
        delta_type="queue_amendment",
        payload={
            "pending_amendment": new_pending.to_dict(),
        },
    )

    return PolicyOutputX1(
        decision_type=DecisionTypeX1.QUEUE_AMENDMENT,
        queued_proposal=selected.proposal,
        state_delta=delta,
        amendment_admission_events=events,
        amendment_admitted=admitted,
        amendment_rejected=rejected,
    )


# ---------------------------------------------------------------------------
# Step 3: Action path (RSA-0 composition)
# ---------------------------------------------------------------------------

def _action_path(
    observations: List[Observation],
    candidates: List[CandidateBundle],
    constitution: ConstitutionX1,
    state: InternalStateX1,
    repo_root: Path,
    cycle_time: str,
) -> PolicyOutputX1:
    """
    Normal RSA-0 action path: admission → selection → warrant.
    Uses the ConstitutionX1's data via a compatibility adapter.
    """
    # Build an RSA-0 compatible AdmissionPipeline
    # by wrapping ConstitutionX1 with RSA-0 Constitution interface
    pipeline = _make_admission_pipeline(constitution, repo_root)
    admitted, rejected, admission_events = pipeline.evaluate(candidates, observations)

    if not admitted:
        refusal = _make_no_action_refusal_x1(rejected, observations, cycle_time)
        return PolicyOutputX1(
            decision_type=DecisionTypeX1.REFUSE,
            refusal=refusal,
            admission_events=admission_events,
            admitted=admitted,
            rejected=rejected,
        )

    # Selection (same as RSA-0)
    selected_result, selection_event = select(admitted)
    assert selected_result is not None
    assert selection_event is not None

    selected_bundle = selected_result.candidate

    # Issue warrant
    warrant = ExecutionWarrant(
        action_request_id=selected_bundle.action_request.id,
        action_type=selected_bundle.action_request.action_type,
        scope_constraints=_build_scope_constraints_x1(selected_bundle, constitution, repo_root),
        issued_in_cycle=state.cycle_index,
        created_at=cycle_time,
    )

    return PolicyOutputX1(
        decision_type=DecisionTypeX1.ACTION,
        bundle=selected_bundle,
        warrant=warrant,
        admission_events=admission_events,
        selection_event=selection_event,
        admitted=admitted,
        rejected=rejected,
    )


# ---------------------------------------------------------------------------
# Compatibility adapter
# ---------------------------------------------------------------------------

class _ConstitutionAdapter:
    """
    Minimal adapter making ConstitutionX1 compatible with RSA-0's
    AdmissionPipeline which expects a Constitution object.
    """

    def __init__(self, cx1: ConstitutionX1):
        self._cx1 = cx1
        # Expose attributes used by AdmissionPipeline
        self._data = cx1.data
        self.version = cx1.version

    def get_action_type_def(self, action_type: str):
        return self._cx1.get_action_type_def(action_type)

    def get_allowed_action_types(self):
        return self._cx1.get_action_types()

    def get_read_paths(self):
        return self._cx1.get_read_paths()

    def get_write_paths(self):
        return self._cx1.get_write_paths()

    def is_network_enabled(self):
        return self._cx1.data.get("io_policy", {}).get("network", {}).get("enabled", False)

    def resolve_citation(self, citation):
        return self._cx1.resolve_citation(citation)

    @property
    def citation_index(self):
        return self._cx1.citation_index

    @property
    def data(self):
        return self._cx1.data


def _make_admission_pipeline(constitution: ConstitutionX1, repo_root: Path) -> AdmissionPipeline:
    """Create an RSA-0 compatible AdmissionPipeline from ConstitutionX1."""
    adapter = _ConstitutionAdapter(constitution)
    pipeline = AdmissionPipeline.__new__(AdmissionPipeline)
    pipeline.constitution = adapter
    pipeline.repo_root = repo_root.resolve()
    pipeline._read_roots = [
        (repo_root / p.lstrip("./")).resolve()
        for p in constitution.get_read_paths()
    ]
    pipeline._write_roots = [
        (repo_root / p.lstrip("./")).resolve()
        for p in constitution.get_write_paths()
    ]
    return pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_no_action_refusal_x1(
    rejected: List[AdmissionResult],
    observations: List[Observation],
    cycle_time: str,
) -> RefusalRecord:
    gate_order = [
        "completeness", "authority_citation", "scope_claim",
        "constitution_compliance", "io_allowlist",
    ]
    summary: Dict[str, int] = {}
    for r in rejected:
        gate = r.failed_gate
        summary[gate] = summary.get(gate, 0) + 1

    failed_gate = "none"
    if rejected:
        for g in gate_order:
            if g in summary:
                failed_gate = g
                break

    return RefusalRecord(
        reason_code=RefusalReasonCode.NO_ADMISSIBLE_ACTION.value,
        failed_gate=failed_gate,
        missing_artifacts=[],
        authority_ids_considered=[],
        observation_ids_referenced=[o.id for o in observations],
        rejection_summary_by_gate=summary,
        created_at=cycle_time,
    )


def _build_scope_constraints_x1(
    bundle: CandidateBundle,
    constitution: ConstitutionX1,
    repo_root: Path,
) -> Dict[str, Any]:
    """Build scope constraints for warrant from action type."""
    from ..artifacts import ActionType

    ar = bundle.action_request
    constraints: Dict[str, Any] = {"action_type": ar.action_type}

    if ar.action_type == ActionType.READ_LOCAL.value:
        constraints["allowed_path"] = ar.fields.get("path", "")
        constraints["read_roots"] = [
            str(repo_root / p.lstrip("./")) for p in constitution.get_read_paths()
        ]
    elif ar.action_type == ActionType.WRITE_LOCAL.value:
        constraints["allowed_path"] = ar.fields.get("path", "")
        constraints["write_roots"] = [
            str(repo_root / p.lstrip("./")) for p in constitution.get_write_paths()
        ]
    elif ar.action_type == ActionType.NOTIFY.value:
        constraints["target"] = ar.fields.get("target", "")
    elif ar.action_type == ActionType.LOG_APPEND.value:
        constraints["log_name"] = ar.fields.get("log_name", "")
        constraints["write_roots"] = [
            str(repo_root / p.lstrip("./")) for p in constitution.get_write_paths()
        ]

    return constraints
