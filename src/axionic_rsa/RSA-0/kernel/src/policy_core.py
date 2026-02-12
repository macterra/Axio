"""
RSA-0 Phase X — Policy Core + Warrant Issuance

Pure, deterministic function:
  policy_core(observations, constitution, internal_state, candidates) → Decision

No IO, no network, no randomness, no retries, no heuristics.

ERRATUM X.E1: Deterministic Time
  Kernel-created artifacts use cycle_time extracted from the TIMESTAMP
  observation. TIMESTAMP is a required observation; absence → REFUSE.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .admission import AdmissionEvent, AdmissionPipeline, AdmissionResult
from .artifacts import (
    ActionType,
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
from .constitution import Constitution
from .selector import SelectionEvent, select


# ---------------------------------------------------------------------------
# Deterministic time extraction (Erratum X.E1)
# ---------------------------------------------------------------------------

def extract_cycle_time(observations: List[Observation]) -> Optional[str]:
    """
    Extract the deterministic cycle timestamp from the TIMESTAMP observation.
    Returns None if count != 1 (missing or ambiguous).
    """
    timestamps = [
        o for o in observations
        if o.kind == ObservationKind.TIMESTAMP.value
    ]
    if len(timestamps) != 1:
        return None
    return timestamps[0].payload.get("iso8601_utc", "")


@dataclass
class PolicyOutput:
    """Full output of a policy core evaluation."""
    decision: Decision
    admission_events: List[AdmissionEvent]
    selection_event: Optional[SelectionEvent]
    admitted: List[AdmissionResult]
    rejected: List[AdmissionResult]


def policy_core(
    observations: List[Observation],
    constitution: Constitution,
    internal_state: InternalState,
    candidates: List[CandidateBundle],
    repo_root: Path,
) -> PolicyOutput:
    """
    Pure decision function. No side effects.

    Returns the decision plus all trace events for telemetry.
    """
    # ---------------------------------------------------------------
    # Pre-admission: extract deterministic cycle time (Erratum X.E1)
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
            missing_artifacts=["TIMESTAMP" if timestamp_count == 0 else "TIMESTAMP (ambiguous: count=%d)" % timestamp_count],
            authority_ids_considered=[],
            observation_ids_referenced=[o.id for o in observations],
            rejection_summary_by_gate={},
            created_at="",
        )
        return PolicyOutput(
            decision=Decision(
                decision_type=DecisionType.REFUSE.value,
                refusal=refusal,
            ),
            admission_events=[],
            selection_event=None,
            admitted=[],
            rejected=[],
        )

    # Check for integrity-risk system observations
    for obs in observations:
        if obs.kind == ObservationKind.SYSTEM.value:
            event = obs.payload.get("event", "")
            if event in (
                SystemEvent.STARTUP_INTEGRITY_FAIL.value,
                SystemEvent.CITATION_INDEX_FAIL.value,
                SystemEvent.EXECUTOR_INTEGRITY_FAIL.value,
                SystemEvent.REPLAY_FAIL.value,
            ):
                exit_record = _make_exit_record(
                    ExitReasonCode.INTEGRITY_RISK.value,
                    [obs.id],
                    f"Integrity risk: {event} — {obs.payload.get('detail', '')}",
                    constitution,
                    cycle_time,
                )
                return PolicyOutput(
                    decision=Decision(
                        decision_type=DecisionType.EXIT.value,
                        exit_record=exit_record,
                    ),
                    admission_events=[],
                    selection_event=None,
                    admitted=[],
                    rejected=[],
                )

    # Check for budget exhaustion observation
    for obs in observations:
        if obs.kind == ObservationKind.BUDGET.value:
            token_count = obs.payload.get("llm_output_token_count", 0)
            max_tokens = constitution.max_total_tokens_per_cycle()
            if token_count > max_tokens:
                refusal = _make_budget_refusal(observations, cycle_time)
                return PolicyOutput(
                    decision=Decision(
                        decision_type=DecisionType.REFUSE.value,
                        refusal=refusal,
                    ),
                    admission_events=[],
                    selection_event=None,
                    admitted=[],
                    rejected=[],
                )

    # Run admission pipeline
    pipeline = AdmissionPipeline(constitution, repo_root)
    admitted, rejected, admission_events = pipeline.evaluate(candidates, observations)

    if not admitted:
        # No admissible action → REFUSE
        refusal = _make_no_action_refusal(rejected, observations, cycle_time)
        return PolicyOutput(
            decision=Decision(
                decision_type=DecisionType.REFUSE.value,
                refusal=refusal,
            ),
            admission_events=admission_events,
            selection_event=None,
            admitted=admitted,
            rejected=rejected,
        )

    # Selection
    selected_result, selection_event = select(admitted)
    assert selected_result is not None
    assert selection_event is not None

    selected_bundle = selected_result.candidate

    # Issue warrant
    warrant = ExecutionWarrant(
        action_request_id=selected_bundle.action_request.id,
        action_type=selected_bundle.action_request.action_type,
        scope_constraints=_build_scope_constraints(selected_bundle, constitution, repo_root),
        issued_in_cycle=internal_state.cycle_index,
        created_at=cycle_time,
    )

    return PolicyOutput(
        decision=Decision(
            decision_type=DecisionType.ACTION.value,
            bundle=selected_bundle,
            warrant=warrant,
        ),
        admission_events=admission_events,
        selection_event=selection_event,
        admitted=admitted,
        rejected=rejected,
    )


# ---------------------------------------------------------------------------
# Helpers (pure)
# ---------------------------------------------------------------------------

def _make_exit_record(
    reason_code: str,
    observation_ids: List[str],
    detail: str,
    constitution: Constitution,
    cycle_time: str,
) -> ExitRecord:
    """Construct a valid ExitRecord."""
    return ExitRecord(
        reason_code=reason_code,
        authority_citations=[
            f"constitution:v{constitution.version}@/exit_policy/exit_mandatory_conditions",
        ],
        scope_claim={
            "observation_ids": observation_ids,
            "claim": f"EXIT required: {reason_code}",
        },
        justification=detail,
        created_at=cycle_time,
    )


def _make_budget_refusal(observations: List[Observation], cycle_time: str) -> RefusalRecord:
    return RefusalRecord(
        reason_code=RefusalReasonCode.BUDGET_EXHAUSTED.value,
        failed_gate="none",
        missing_artifacts=[],
        authority_ids_considered=[],
        observation_ids_referenced=[o.id for o in observations],
        rejection_summary_by_gate={},
        created_at=cycle_time,
    )


def _make_no_action_refusal(
    rejected: List[AdmissionResult],
    observations: List[Observation],
    cycle_time: str,
) -> RefusalRecord:
    # Compute earliest gate where all candidates were eliminated
    gate_order = [
        "completeness",
        "authority_citation",
        "scope_claim",
        "constitution_compliance",
        "io_allowlist",
    ]

    summary: Dict[str, int] = {}
    for r in rejected:
        gate = r.failed_gate
        summary[gate] = summary.get(gate, 0) + 1

    # Find the gate that eliminated all remaining candidates
    failed_gate = "none"
    if rejected:
        # The earliest gate that has at least one failure
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


def _build_scope_constraints(
    bundle: CandidateBundle,
    constitution: Constitution,
    repo_root: Path,
) -> Dict[str, Any]:
    """Build scope constraints for the warrant from the action type."""
    ar = bundle.action_request

    constraints: Dict[str, Any] = {
        "action_type": ar.action_type,
    }

    if ar.action_type == ActionType.READ_LOCAL.value:
        constraints["allowed_path"] = ar.fields.get("path", "")
        constraints["read_roots"] = [str(repo_root / p.lstrip("./")) for p in constitution.get_read_paths()]

    elif ar.action_type == ActionType.WRITE_LOCAL.value:
        constraints["allowed_path"] = ar.fields.get("path", "")
        constraints["write_roots"] = [str(repo_root / p.lstrip("./")) for p in constitution.get_write_paths()]

    elif ar.action_type == ActionType.NOTIFY.value:
        constraints["target"] = ar.fields.get("target", "")

    elif ar.action_type == ActionType.LOG_APPEND.value:
        constraints["log_name"] = ar.fields.get("log_name", "")
        constraints["write_roots"] = [str(repo_root / p.lstrip("./")) for p in constitution.get_write_paths()]

    return constraints


# ---------------------------------------------------------------------------
# LogAppend warrant issuance (kernel-authoritative)
# ---------------------------------------------------------------------------

@dataclass
class LogAppendWarrantResult:
    """Result of admitting and warranting a single LogAppend bundle."""
    bundle: CandidateBundle
    warrant: Optional[ExecutionWarrant]
    admitted: bool
    rejection_reason: str = ""


def issue_log_append_warrants(
    log_bundles: List[CandidateBundle],
    observations: List[Observation],
    constitution: Constitution,
    cycle_index: int,
    repo_root: Path,
) -> List[LogAppendWarrantResult]:
    """
    Kernel-authoritative LogAppend warrant issuance.

    Each LogAppend bundle is run through the admission pipeline.
    Admitted bundles receive a kernel-issued ExecutionWarrant.
    This function is pure and deterministic.

    The host must call this instead of fabricating warrants directly.
    """
    cycle_time = extract_cycle_time(observations) or ""

    pipeline = AdmissionPipeline(constitution, repo_root)
    admitted, rejected, _ = pipeline.evaluate(log_bundles, observations)

    results: List[LogAppendWarrantResult] = []

    for ar in admitted:
        bundle = ar.candidate
        warrant = ExecutionWarrant(
            action_request_id=bundle.action_request.id,
            action_type=bundle.action_request.action_type,
            scope_constraints=_build_scope_constraints(bundle, constitution, repo_root),
            issued_in_cycle=cycle_index,
            created_at=cycle_time,
        )
        results.append(LogAppendWarrantResult(
            bundle=bundle,
            warrant=warrant,
            admitted=True,
        ))

    for rr in rejected:
        results.append(LogAppendWarrantResult(
            bundle=rr.candidate,
            warrant=None,
            admitted=False,
            rejection_reason=rr.rejection_code,
        ))

    return results
