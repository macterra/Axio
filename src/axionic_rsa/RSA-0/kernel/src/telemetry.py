"""
RSA-0 Phase X — Telemetry Derivation

Pure, deterministic function:
  derive_telemetry(cycle_inputs, decision, traces) → LogIntents

Produces the exact JSONL lines that will be written via LogAppend warrants.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .admission import AdmissionEvent
from .artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    Decision,
    ExecutionWarrant,
    InternalState,
    Observation,
    canonical_json,
    canonical_json_bytes,
)
from .policy_core import PolicyOutput
from .selector import SelectionEvent


@dataclass
class LogIntent:
    """A batch of JSONL lines destined for one log stream."""
    log_name: str
    lines: List[str]

    def lines_sha256(self) -> str:
        """SHA-256 of newline-joined lines (UTF-8)."""
        content = "\n".join(self.lines) + "\n"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class LogCommitSummary:
    """Summary of log writes for a cycle, appended to execution_trace."""
    cycle_index: int
    streams_written: List[str]
    warrants: List[Dict[str, Any]]
    total_lines_written: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "log_commit_summary",
            "cycle_index": self.cycle_index,
            "streams_written": self.streams_written,
            "warrants": self.warrants,
            "total_lines_written": self.total_lines_written,
        }


def derive_telemetry(
    run_id: str,
    cycle_index: int,
    observations: List[Observation],
    candidates: List[CandidateBundle],
    policy_output: PolicyOutput,
) -> List[LogIntent]:
    """
    Pure function: derive all log lines for this cycle.
    Returns a list of LogIntents, one per log stream that has content.
    """
    intents: List[LogIntent] = []

    # 1. observations log
    obs_lines = []
    for obs in observations:
        obs_lines.append(canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "observation": obs.to_dict(),
        }))
    if obs_lines:
        intents.append(LogIntent(log_name="observations", lines=obs_lines))

    # 2. artifacts log
    artifact_lines = []
    for cand in candidates:
        artifact_lines.append(canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "artifact": cand.action_request.to_dict(),
        }))
        if cand.scope_claim:
            artifact_lines.append(canonical_json({
                "run_id": run_id,
                "cycle_id": cycle_index,
                "artifact": cand.scope_claim.to_dict(),
            }))
        if cand.justification:
            artifact_lines.append(canonical_json({
                "run_id": run_id,
                "cycle_id": cycle_index,
                "artifact": cand.justification.to_dict(),
            }))

    decision = policy_output.decision
    if decision.refusal:
        artifact_lines.append(canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "artifact": decision.refusal.to_dict(),
        }))
    if decision.exit_record:
        artifact_lines.append(canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "artifact": decision.exit_record.to_dict(),
        }))
    if decision.warrant:
        artifact_lines.append(canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "artifact": decision.warrant.to_dict(),
        }))

    if artifact_lines:
        intents.append(LogIntent(log_name="artifacts", lines=artifact_lines))

    # 3. admission_trace log
    admission_lines = []
    for event in policy_output.admission_events:
        admission_lines.append(canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "event": event.to_dict(),
        }))
    if admission_lines:
        intents.append(LogIntent(log_name="admission_trace", lines=admission_lines))

    # 4. selector_trace log
    if policy_output.selection_event:
        selector_line = canonical_json({
            "run_id": run_id,
            "cycle_id": cycle_index,
            "event": policy_output.selection_event.to_dict(),
        })
        intents.append(LogIntent(log_name="selector_trace", lines=[selector_line]))

    # 5. execution_trace log
    exec_lines = []
    exec_lines.append(canonical_json({
        "run_id": run_id,
        "cycle_id": cycle_index,
        "decision": {
            "decision_type": decision.decision_type,
            "warrant_id": decision.warrant.warrant_id if decision.warrant else None,
            "action_type": decision.bundle.action_request.action_type if decision.bundle else None,
        },
    }))
    if exec_lines:
        intents.append(LogIntent(log_name="execution_trace", lines=exec_lines))

    return intents


def build_log_append_bundles(
    intents: List[LogIntent],
    cycle_index: int,
    constitution_version: str,
) -> List[CandidateBundle]:
    """
    Convert LogIntents into kernel-authored CandidateBundle objects
    for LogAppend actions, ready for admission.
    """
    bundles = []
    for intent in intents:
        ar = ActionRequest(
            action_type=ActionType.LOG_APPEND.value,
            fields={
                "log_name": intent.log_name,
                "jsonl_lines": intent.lines,
            },
            author=Author.KERNEL.value,
        )
        bundle = CandidateBundle(
            action_request=ar,
            scope_claim=None,
            justification=None,
            authority_citations=[
                f"constitution:v{constitution_version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                f"constitution:v{constitution_version}@/telemetry_policy/required_logs",
            ],
        )
        bundles.append(bundle)
    return bundles
