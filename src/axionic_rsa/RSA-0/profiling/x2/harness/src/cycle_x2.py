"""
X-2 Cycle Runner

Orchestrates a single kernel cycle under the X-2 policy core:
  observations + candidates + treaties + DARs → policy_core_x2 → decision

Handles the 5-step per-cycle ordering:
  Step 1: Governance (adoption, revocations, grants, amendment queue)
  Step 2: Revocation processing (folded into Step 1b)
  Step 3: Active treaty set recomputation
  Step 4: ActionRequest admission (RSA + delegated)
  Step 5: Warrant issuance (origin_rank ASC, warrant_id ASC)

All cycle state is logged for replay.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    ExecutionWarrant,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    SystemEvent,
    canonical_json,
)
from kernel.src.rsax1.artifacts_x1 import (
    AmendmentProposal,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
    StateDelta,
)
from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRevocation,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import (
    DelegatedActionRequest,
    PolicyOutputX2,
    policy_core_x2,
)

from host.tools.executor import ExecutionEvent, Executor


# ---------------------------------------------------------------------------
# Cycle result
# ---------------------------------------------------------------------------

@dataclass
class X2CycleResult:
    """Full result of a single X-2 cycle."""
    cycle_index: int
    cycle_id: str
    phase: str
    decision_type: str
    constitution_hash: str
    # State hashes for replay
    state_in_hash: str = ""
    state_out_hash: str = ""
    # Treaty events
    grants_admitted: int = 0
    grants_rejected: int = 0
    revocations_admitted: int = 0
    revocations_rejected: int = 0
    active_grants_count: int = 0
    # Delegated action events
    delegated_warrants_issued: int = 0
    delegated_rejections: int = 0
    # RSA action path
    rsa_warrant_id: Optional[str] = None
    rsa_action_type: Optional[str] = None
    # All warrants (sorted per CL-WARRANT-EXECUTION-ORDER)
    warrant_ids: List[str] = field(default_factory=list)
    # Refusal
    refusal_reason: Optional[str] = None
    refusal_gate: Optional[str] = None
    # Amendment
    amendment_proposed: bool = False
    amendment_adopted: bool = False
    proposal_id: Optional[str] = None
    new_constitution_hash: Optional[str] = None
    # Rejection details
    grant_rejection_codes: List[str] = field(default_factory=list)
    delegation_rejection_codes: List[str] = field(default_factory=list)
    revocation_rejection_codes: List[str] = field(default_factory=list)
    # Trace
    execution_events: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "cycle_index": self.cycle_index,
            "cycle_id": self.cycle_id,
            "phase": self.phase,
            "decision_type": self.decision_type,
            "constitution_hash": self.constitution_hash,
            "state_in_hash": self.state_in_hash,
            "state_out_hash": self.state_out_hash,
            "grants_admitted": self.grants_admitted,
            "grants_rejected": self.grants_rejected,
            "revocations_admitted": self.revocations_admitted,
            "revocations_rejected": self.revocations_rejected,
            "active_grants_count": self.active_grants_count,
            "delegated_warrants_issued": self.delegated_warrants_issued,
            "delegated_rejections": self.delegated_rejections,
            "warrant_ids": self.warrant_ids,
        }
        if self.rsa_warrant_id:
            d["rsa_warrant_id"] = self.rsa_warrant_id
            d["rsa_action_type"] = self.rsa_action_type
        if self.refusal_reason:
            d["refusal_reason"] = self.refusal_reason
            d["refusal_gate"] = self.refusal_gate
        if self.amendment_proposed:
            d["amendment_proposed"] = True
            d["proposal_id"] = self.proposal_id
        if self.amendment_adopted:
            d["amendment_adopted"] = True
            d["new_constitution_hash"] = self.new_constitution_hash
        if self.grant_rejection_codes:
            d["grant_rejection_codes"] = self.grant_rejection_codes
        if self.delegation_rejection_codes:
            d["delegation_rejection_codes"] = self.delegation_rejection_codes
        if self.revocation_rejection_codes:
            d["revocation_rejection_codes"] = self.revocation_rejection_codes
        if self.execution_events:
            d["execution_events"] = self.execution_events
        d["latency_ms"] = self.latency_ms
        return d


# ---------------------------------------------------------------------------
# Observation builders
# ---------------------------------------------------------------------------

def make_timestamp_obs(timestamp: str) -> Observation:
    return Observation(
        kind=ObservationKind.TIMESTAMP.value,
        payload={"iso8601_utc": timestamp},
        author=Author.HOST.value,
    )


def make_system_obs(event: str, detail: str = "") -> Observation:
    return Observation(
        kind=ObservationKind.SYSTEM.value,
        payload={"event": event, "detail": detail},
        author=Author.HOST.value,
    )


def make_budget_obs(
    token_count: int = 0,
    candidates_reported: int = 0,
    parse_errors: int = 0,
) -> Observation:
    return Observation(
        kind=ObservationKind.BUDGET.value,
        payload={
            "llm_output_token_count": token_count,
            "llm_candidates_reported": candidates_reported,
            "llm_parse_errors": parse_errors,
        },
        author=Author.HOST.value,
    )


def make_user_input_obs(text: str) -> Observation:
    return Observation(
        kind=ObservationKind.USER_INPUT.value,
        payload={"text": text, "source": "x2_harness"},
        author=Author.USER.value,
    )


# ---------------------------------------------------------------------------
# Candidate builders
# ---------------------------------------------------------------------------

def build_notify_candidate(
    message: str,
    observation_ids: List[str],
    constitution: ConstitutionX2,
) -> CandidateBundle:
    """Build a Notify candidate with hash-based citations."""
    ar = ActionRequest(
        action_type=ActionType.NOTIFY.value,
        fields={"target": "stdout", "message": message},
        author=Author.HOST.value,
    )
    sc = ScopeClaim(
        observation_ids=observation_ids,
        claim="Notification warranted by cycle input",
        clause_ref=constitution.make_citation("CL-SCOPE-SYSTEM"),
        author=Author.HOST.value,
    )
    just = Justification(
        text=f"Responding to cycle input with Notify(stdout)",
        author=Author.HOST.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[
            constitution.make_citation("INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"),
            constitution.make_citation("INV-AUTHORITY-CITED"),
            constitution.make_authority_citation("AUTH_TELEMETRY"),
        ],
    )


# ---------------------------------------------------------------------------
# State hashing
# ---------------------------------------------------------------------------

def _state_hash(state: InternalStateX2) -> str:
    return hashlib.sha256(
        canonical_json(state.to_dict()).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Single cycle execution
# ---------------------------------------------------------------------------

def run_x2_cycle(
    cycle_index: int,
    phase: str,
    timestamp: str,
    user_message: str,
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    treaty_grant_candidates: List[TreatyGrant],
    treaty_revocation_candidates: List[TreatyRevocation],
    delegated_action_candidates: List[DelegatedActionRequest],
    constitution: ConstitutionX2,
    internal_state: InternalStateX2,
    repo_root: Path,
    schema: Optional[Dict[str, Any]] = None,
) -> Tuple[X2CycleResult, InternalStateX2, PolicyOutputX2]:
    """
    Execute one X-2 cycle.

    Returns (cycle_result, next_state, raw_policy_output).
    The caller is responsible for executing warrants and applying state deltas.
    """
    cycle_id = f"X2-{cycle_index:04d}"
    state_in_hash = _state_hash(internal_state)
    t_start = time.perf_counter()

    # Build observations
    observations = [
        make_timestamp_obs(timestamp),
        make_user_input_obs(user_message),
        make_budget_obs(0, len(action_candidates), 0),
    ]

    # Pending amendments for adoption check
    pending_candidates = list(internal_state.pending_amendments)

    # Call policy core X-2
    output = policy_core_x2(
        observations=observations,
        action_candidates=action_candidates,
        amendment_candidates=amendment_candidates,
        pending_amendment_candidates=pending_candidates,
        treaty_grant_candidates=treaty_grant_candidates,
        treaty_revocation_candidates=treaty_revocation_candidates,
        delegated_action_candidates=delegated_action_candidates,
        constitution=constitution,
        internal_state=internal_state,
        repo_root=repo_root,
        schema=schema,
    )

    elapsed_ms = (time.perf_counter() - t_start) * 1000

    # Build result
    result = X2CycleResult(
        cycle_index=cycle_index,
        cycle_id=cycle_id,
        phase=phase,
        decision_type=output.decision_type,
        constitution_hash=constitution.sha256,
        state_in_hash=state_in_hash,
        latency_ms=elapsed_ms,
    )

    # Treaty admission results
    result.grants_admitted = len(output.treaty_grants_admitted)
    result.grants_rejected = len(output.treaty_grants_rejected)
    result.revocations_admitted = len(output.treaty_revocations_admitted)
    result.revocations_rejected = len(output.treaty_revocations_rejected)
    result.grant_rejection_codes = [
        r.rejection_code for r in output.treaty_grants_rejected
    ]
    result.revocation_rejection_codes = [
        r.rejection_code for r in output.treaty_revocations_rejected
    ]

    # Delegated action results
    result.delegated_warrants_issued = len(output.delegated_warrants)
    result.delegated_rejections = len(output.delegated_rejections)
    result.delegation_rejection_codes = [
        r.get("rejection_code", "") for r in output.delegated_rejections
    ]

    # Warrant IDs (all warrants, in execution order)
    result.warrant_ids = [w.warrant_id for w in output.warrants]

    # Decision-type-specific fields
    if output.decision_type == DecisionTypeX2.ACTION:
        # Find RSA warrant
        for w in output.warrants:
            if w.scope_constraints.get("origin") == "rsa":
                result.rsa_warrant_id = w.warrant_id
                result.rsa_action_type = w.action_type
                break
    elif output.decision_type == DecisionTypeX2.REFUSE:
        if output.refusal:
            result.refusal_reason = output.refusal.reason_code
            result.refusal_gate = output.refusal.failed_gate
    elif output.decision_type == DecisionTypeX2.QUEUE_AMENDMENT:
        result.amendment_proposed = True
        if output.queued_proposal:
            result.proposal_id = output.queued_proposal.id
    elif output.decision_type == DecisionTypeX2.ADOPT:
        result.amendment_adopted = True
        if output.adoption_record:
            result.new_constitution_hash = output.adoption_record.new_constitution_hash

    # Compute next state
    next_state = internal_state.advance(output.decision_type)
    result.active_grants_count = len(next_state.active_treaty_set.active_grants(cycle_index))

    # Apply state deltas (amendment queue/adopt)
    if output.state_delta:
        delta = output.state_delta
        if delta.delta_type == "queue_amendment":
            p = delta.payload.get("pending_amendment", {})
            pending = PendingAmendment(
                proposal_id=p["proposal_id"],
                prior_constitution_hash=p["prior_constitution_hash"],
                proposed_constitution_hash=p["proposed_constitution_hash"],
                proposal_cycle=p["proposal_cycle"],
            )
            next_state.pending_amendments = list(internal_state.pending_amendments) + [pending]
        elif delta.delta_type == "adopt_amendment":
            new_hash = delta.payload.get("new_constitution_hash", "")
            next_state.active_constitution_hash = new_hash
            remaining_dicts = delta.payload.get("remaining_pending", [])
            next_state.pending_amendments = [
                PendingAmendment(**r) for r in remaining_dicts
            ]

    result.state_out_hash = _state_hash(next_state)

    return result, next_state, output


def execute_warrants(
    output: PolicyOutputX2,
    repo_root: Path,
    cycle_index: int,
) -> List[ExecutionEvent]:
    """Execute all warranted actions from a policy output."""
    events: List[ExecutionEvent] = []
    if output.decision_type != DecisionTypeX2.ACTION:
        return events

    executor = Executor(repo_root, cycle_index)

    for warrant in output.warrants:
        origin = warrant.scope_constraints.get("origin", "rsa")

        if origin == "rsa" and output.bundles:
            # RSA warrant: use the first bundle
            event = executor.execute(warrant, output.bundles[0])
            events.append(event)
        elif origin == "delegated":
            # Delegated warrant: construct a minimal bundle for execution
            ar = ActionRequest(
                action_type=warrant.action_type,
                fields={},  # fields are in the DAR, not preserved in warrant
                author=Author.HOST.value,
            )
            sc = ScopeClaim(
                observation_ids=[],
                claim=f"Delegated {warrant.action_type}",
                clause_ref="treaty",
                author=Author.HOST.value,
            )
            just = Justification(
                text=f"Delegated action via treaty grant {warrant.scope_constraints.get('grant_id', '')}",
                author=Author.HOST.value,
            )
            bundle = CandidateBundle(
                action_request=ar,
                scope_claim=sc,
                justification=just,
                authority_citations=[],
            )
            # Fix AR ID to match warrant
            bundle.action_request.id = warrant.action_request_id
            event = executor.execute(warrant, bundle)
            events.append(event)

    return events
