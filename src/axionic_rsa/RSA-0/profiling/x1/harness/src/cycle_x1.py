"""
X-1 Cycle Runner

Orchestrates a single kernel cycle under the X-1 policy core:
  observations + action_candidates + amendment_candidates → policy_core_x1 → decision

Handles:
  - ACTION: issue warrant, execute via Executor
  - QUEUE_AMENDMENT: apply state delta (add pending)
  - ADOPT: apply state delta (switch constitution, invalidate stale)
  - REFUSE: log refusal
  - EXIT: terminate

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
    InternalState,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    SystemEvent,
    canonical_json,
)
from kernel.src.rsax1.artifacts_x1 import (
    AmendmentAdoptionRecord,
    AmendmentProposal,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
    StateDelta,
)
from kernel.src.rsax1.constitution_x1 import ConstitutionX1
from kernel.src.rsax1.policy_core_x1 import PolicyOutputX1, policy_core_x1

from host.tools.executor import ExecutionEvent, Executor


# ---------------------------------------------------------------------------
# Cycle result
# ---------------------------------------------------------------------------

@dataclass
class X1CycleResult:
    """Full result of a single X-1 cycle."""
    cycle_index: int
    cycle_id: str
    phase: str  # "normal" | "propose" | "cooling" | "adopt" | "post-fork" | "adversarial"
    decision_type: str
    constitution_hash: str
    # State hashes for replay
    state_in_hash: str = ""
    state_out_hash: str = ""
    # Amendment-specific
    amendment_proposed: bool = False
    amendment_adopted: bool = False
    proposal_id: Optional[str] = None
    adoption_record_id: Optional[str] = None
    new_constitution_hash: Optional[str] = None
    # Action path
    warrant_id: Optional[str] = None
    action_type: Optional[str] = None
    # Refusal path
    refusal_reason: Optional[str] = None
    refusal_gate: Optional[str] = None
    # Amendment rejection
    amendment_rejection_code: Optional[str] = None
    amendment_rejection_gate: Optional[str] = None
    # Trace
    execution_events: List[Dict[str, Any]] = field(default_factory=list)
    admission_events: List[Dict[str, Any]] = field(default_factory=list)
    amendment_events: List[Dict[str, Any]] = field(default_factory=list)
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
        }
        if self.amendment_proposed:
            d["amendment_proposed"] = True
            d["proposal_id"] = self.proposal_id
        if self.amendment_adopted:
            d["amendment_adopted"] = True
            d["adoption_record_id"] = self.adoption_record_id
            d["new_constitution_hash"] = self.new_constitution_hash
        if self.warrant_id:
            d["warrant_id"] = self.warrant_id
            d["action_type"] = self.action_type
        if self.refusal_reason:
            d["refusal_reason"] = self.refusal_reason
            d["refusal_gate"] = self.refusal_gate
        if self.amendment_rejection_code:
            d["amendment_rejection_code"] = self.amendment_rejection_code
            d["amendment_rejection_gate"] = self.amendment_rejection_gate
        if self.execution_events:
            d["execution_events"] = self.execution_events
        if self.admission_events:
            d["admission_events"] = self.admission_events
        if self.amendment_events:
            d["amendment_events"] = self.amendment_events
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
        payload={"text": text, "source": "x1_harness"},
        author=Author.USER.value,
    )


# ---------------------------------------------------------------------------
# Host-constructed action candidates
# ---------------------------------------------------------------------------

def build_notify_candidate(
    message: str,
    observation_ids: List[str],
    constitution: ConstitutionX1,
) -> CandidateBundle:
    """Build a Notify(stdout) candidate with hash-based citations."""
    ar = ActionRequest(
        action_type=ActionType.NOTIFY.value,
        fields={"target": "stdout", "message": message},
        author=Author.HOST.value,
    )
    sc = ScopeClaim(
        observation_ids=observation_ids,
        claim="User input warrants notification via stdout",
        clause_ref=f"constitution:{constitution.sha256}@/action_space/action_types/0",
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

def _state_hash(state: InternalStateX1) -> str:
    return hashlib.sha256(
        canonical_json(state.to_dict()).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Single cycle execution
# ---------------------------------------------------------------------------

def run_x1_cycle(
    cycle_index: int,
    phase: str,
    timestamp: str,
    user_message: str,
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    constitution: ConstitutionX1,
    internal_state: InternalStateX1,
    repo_root: Path,
    schema: Optional[Dict[str, Any]] = None,
) -> Tuple[X1CycleResult, InternalStateX1, PolicyOutputX1]:
    """
    Execute one X-1 cycle.

    Returns (cycle_result, next_state, raw_policy_output).
    The caller is responsible for applying state deltas and executing warrants.
    """
    cycle_id = f"X1-{cycle_index:04d}"
    state_in_hash = _state_hash(internal_state)
    t_start = time.perf_counter()

    # Build observations
    observations = [
        make_timestamp_obs(timestamp),
        make_user_input_obs(user_message),
        make_budget_obs(0, len(action_candidates), 0),
    ]

    # Collect pending amendments for adoption check
    pending_candidates = list(internal_state.pending_amendments)

    # Call policy core
    output = policy_core_x1(
        observations=observations,
        action_candidates=action_candidates,
        amendment_candidates=amendment_candidates,
        pending_amendment_candidates=pending_candidates,
        constitution=constitution,
        internal_state=internal_state,
        repo_root=repo_root,
        schema=schema,
    )

    elapsed_ms = (time.perf_counter() - t_start) * 1000

    # Build result
    result = X1CycleResult(
        cycle_index=cycle_index,
        cycle_id=cycle_id,
        phase=phase,
        decision_type=output.decision_type,
        constitution_hash=constitution.sha256,
        state_in_hash=state_in_hash,
        latency_ms=elapsed_ms,
    )

    # Populate result fields based on decision type
    if output.decision_type == DecisionTypeX1.ACTION:
        if output.warrant:
            result.warrant_id = output.warrant.warrant_id
            result.action_type = output.warrant.action_type
    elif output.decision_type == DecisionTypeX1.QUEUE_AMENDMENT:
        result.amendment_proposed = True
        if output.queued_proposal:
            result.proposal_id = output.queued_proposal.id
    elif output.decision_type == DecisionTypeX1.ADOPT:
        result.amendment_adopted = True
        if output.adoption_record:
            result.adoption_record_id = output.adoption_record.id
            result.new_constitution_hash = output.adoption_record.new_constitution_hash
    elif output.decision_type == DecisionTypeX1.REFUSE:
        if output.refusal:
            result.refusal_reason = output.refusal.reason_code
            result.refusal_gate = output.refusal.failed_gate

    # Trace events
    result.admission_events = [e.to_dict() for e in output.admission_events]
    result.amendment_events = [e.to_dict() for e in output.amendment_admission_events]

    # Check for rejected amendments
    if output.amendment_rejected:
        first_reject = output.amendment_rejected[0]
        result.amendment_rejection_code = first_reject.rejection_code
        result.amendment_rejection_gate = first_reject.failed_gate

    # Compute next state
    next_state = internal_state.advance(output.decision_type)

    # Apply state deltas
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
            # Apply stale invalidation
            remaining_dicts = delta.payload.get("remaining_pending", [])
            next_state.pending_amendments = [
                PendingAmendment(**r) for r in remaining_dicts
            ]

    result.state_out_hash = _state_hash(next_state)

    return result, next_state, output


def execute_action(
    output: PolicyOutputX1,
    repo_root: Path,
    cycle_index: int,
) -> List[ExecutionEvent]:
    """Execute warranted action from a policy output."""
    events: List[ExecutionEvent] = []
    if (
        output.decision_type == DecisionTypeX1.ACTION
        and output.warrant is not None
        and output.bundle is not None
    ):
        executor = Executor(repo_root, cycle_index)
        event = executor.execute(output.warrant, output.bundle)
        events.append(event)
    return events
