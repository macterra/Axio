"""
X-0P Cycle Runner

Orchestrates profiling cycles by calling policy_core() directly,
bypassing the host (per BB5). Handles state evolution, execution
dispatch, and per-cycle logging.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    CandidateBundle,
    DecisionType,
    InternalState,
    Observation,
    canonical_json,
)
from kernel.src.constitution import Constitution
from kernel.src.policy_core import PolicyOutput, policy_core

from profiling.x0p.harness.src.generator_common import CycleInput, ConditionManifest


# ---------------------------------------------------------------------------
# Cycle result container
# ---------------------------------------------------------------------------

@dataclass
class CycleResult:
    """Output of a single profiling cycle."""
    cycle_id: str
    condition: str
    entropy_class: str
    decision_type: str
    input_hash: str
    state_in_hash: str
    state_out_hash: str
    warrant_id: Optional[str] = None
    refusal_reason: Optional[str] = None
    refusal_failed_gate: Optional[str] = None
    exit_reason: Optional[str] = None
    admitted_count: int = 0
    rejected_count: int = 0
    gate_failures: Dict[str, int] = field(default_factory=dict)
    authority_ids_invoked: List[str] = field(default_factory=list)
    execution_trace: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    artifact_ids: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "condition": self.condition,
            "entropy_class": self.entropy_class,
            "decision_type": self.decision_type,
            "input_hash": self.input_hash,
            "state_in_hash": self.state_in_hash,
            "state_out_hash": self.state_out_hash,
            "warrant_id": self.warrant_id,
            "refusal_reason": self.refusal_reason,
            "refusal_failed_gate": self.refusal_failed_gate,
            "exit_reason": self.exit_reason,
            "admitted_count": self.admitted_count,
            "rejected_count": self.rejected_count,
            "gate_failures": self.gate_failures,
            "authority_ids_invoked": self.authority_ids_invoked,
            "execution_trace": self.execution_trace,
            "latency_ms": self.latency_ms,
            "artifact_ids": self.artifact_ids,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# State hashing
# ---------------------------------------------------------------------------

def _state_hash(state: InternalState) -> str:
    """Deterministic hash of internal state."""
    return hashlib.sha256(
        canonical_json(state.to_dict()).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Run result container
# ---------------------------------------------------------------------------

@dataclass
class ConditionRunResult:
    """Result of running an entire condition."""
    condition: str
    run_id: str
    manifest_hash: str
    constitution_hash: str
    n_cycles: int
    cycle_results: List[CycleResult] = field(default_factory=list)
    aborted: bool = False
    abort_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition": self.condition,
            "run_id": self.run_id,
            "manifest_hash": self.manifest_hash,
            "constitution_hash": self.constitution_hash,
            "n_cycles": self.n_cycles,
            "cycle_results": [cr.to_dict() for cr in self.cycle_results],
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
        }


# ---------------------------------------------------------------------------
# Single cycle execution
# ---------------------------------------------------------------------------

def run_cycle(
    cycle_input: CycleInput,
    constitution: Constitution,
    internal_state: InternalState,
    repo_root: Path,
    executor: Optional[Any] = None,  # Optional CapturingExecutor
) -> tuple[CycleResult, InternalState]:
    """Execute one profiling cycle.

    Calls policy_core() directly (bypassing host per BB5).
    If ACTION and executor is provided, delegates execution.

    Returns (CycleResult, next_internal_state).
    """
    state_in_hash = _state_hash(internal_state)
    input_hash = cycle_input.input_hash()

    # Measure latency OUTSIDE kernel core only (per H26)
    t_start = time.perf_counter()
    output: PolicyOutput = policy_core(
        observations=cycle_input.observations,
        constitution=constitution,
        internal_state=internal_state,
        candidates=cycle_input.candidates,
        repo_root=repo_root,
    )
    t_end = time.perf_counter()
    latency_ms = (t_end - t_start) * 1000.0

    decision = output.decision
    decision_type = decision.decision_type

    # Advance internal state
    next_state = internal_state.advance(decision_type)
    state_out_hash = _state_hash(next_state)

    # Build cycle result
    result = CycleResult(
        cycle_id=cycle_input.cycle_id,
        condition=cycle_input.condition,
        entropy_class=cycle_input.entropy_class,
        decision_type=decision_type,
        input_hash=input_hash,
        state_in_hash=state_in_hash,
        state_out_hash=state_out_hash,
        latency_ms=latency_ms,
        admitted_count=len(output.admitted),
        rejected_count=len(output.rejected),
        metadata=cycle_input.metadata,
    )

    # Extract decision-specific fields
    if decision_type == DecisionType.ACTION.value:
        if decision.warrant:
            result.warrant_id = decision.warrant.warrant_id
            result.artifact_ids["warrant_id"] = decision.warrant.warrant_id
        if decision.bundle:
            result.artifact_ids["action_request_id"] = decision.bundle.action_request.id

        # Collect authority IDs from admitted bundles
        for admitted in output.admitted:
            if admitted.candidate:
                result.authority_ids_invoked.extend(
                    admitted.candidate.authority_citations
                )

        # Execute if executor provided
        if executor is not None and decision.warrant and decision.bundle:
            try:
                exec_result = executor.execute(
                    decision.warrant,
                    decision.bundle.action_request,
                    cycle=internal_state.cycle_index,
                )
                result.execution_trace = exec_result
            except Exception as e:
                result.execution_trace = {"error": str(e)}

    elif decision_type == DecisionType.REFUSE.value:
        if decision.refusal:
            result.refusal_reason = decision.refusal.reason_code
            result.refusal_failed_gate = decision.refusal.failed_gate
            result.artifact_ids["refusal_id"] = decision.refusal.id

    elif decision_type == DecisionType.EXIT.value:
        if decision.exit_record:
            result.exit_reason = decision.exit_record.reason_code
            result.artifact_ids["exit_record_id"] = decision.exit_record.id

    # Gate failure histogram (short-circuit: first-failing-gate only, per CE13)
    gate_failures: Dict[str, int] = {}
    for rejected in output.rejected:
        if hasattr(rejected, 'events'):
            for event in rejected.events:
                gate = getattr(event, 'gate', 'unknown')
                gate_failures[gate] = gate_failures.get(gate, 0) + 1
    # Also check admission events for failures
    for event in output.admission_events:
        if hasattr(event, 'passed') and not event.passed:
            gate = getattr(event, 'gate', 'unknown')
            gate_failures[gate] = gate_failures.get(gate, 0) + 1
    result.gate_failures = gate_failures

    return result, next_state


# ---------------------------------------------------------------------------
# Full condition run
# ---------------------------------------------------------------------------

def run_condition(
    manifest: ConditionManifest,
    constitution: Constitution,
    repo_root: Path,
    executor: Optional[Any] = None,
    initial_state: Optional[InternalState] = None,
) -> ConditionRunResult:
    """Execute all cycles for a condition manifest.

    Returns ConditionRunResult with all cycle results.
    """
    run_id = str(uuid.uuid4())
    state = initial_state or InternalState(cycle_index=0, last_decision="NONE")

    run_result = ConditionRunResult(
        condition=manifest.condition,
        run_id=run_id,
        manifest_hash=manifest.manifest_hash(),
        constitution_hash=constitution.sha256,
        n_cycles=manifest.n_cycles,
    )

    for cycle_input in manifest.cycles:
        try:
            cycle_result, state = run_cycle(
                cycle_input=cycle_input,
                constitution=constitution,
                internal_state=state,
                repo_root=repo_root,
                executor=executor,
            )
            run_result.cycle_results.append(cycle_result)

            # If EXIT, stop the condition run
            if cycle_result.decision_type == DecisionType.EXIT.value:
                break

        except Exception as e:
            run_result.aborted = True
            run_result.abort_reason = f"Unhandled exception at cycle {cycle_input.cycle_id}: {e}"
            break

    return run_result
