"""
RSA-0 X-0E — ``rsa run`` command

Processes a deterministic observation stream through the frozen kernel,
producing warranted side effects (Notify only) and append-only logs.

Usage:
    rsa run --constitution <path> --log-dir <path> --observations <path>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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
)
from kernel.src.constitution import Constitution
from kernel.src.policy_core import PolicyOutput, policy_core
from kernel.src.state_hash import (
    KERNEL_VERSION_ID,
    cycle_state_hash,
    initial_state_hash,
    state_hash_hex,
)
from host.log_io import append_jsonl, read_jsonl
from host.executor_x0e import ExecutorX0E


def _build_observation_record(obs: Observation, cycle_id: int, timestamp: str) -> Dict[str, Any]:
    """Build a log record for observations.jsonl."""
    return {
        "cycle_id": cycle_id,
        "observation_id": obs.id,
        "kind": obs.kind,
        "timestamp": timestamp,
        "payload": obs.payload,
    }


def _build_artifact_record(bundle: CandidateBundle, cycle_id: int, timestamp: str) -> Dict[str, Any]:
    """Build a log record for artifacts.jsonl."""
    return {
        "cycle_id": cycle_id,
        "artifact_id": bundle.action_request.id,
        "action_type": bundle.action_request.action_type,
        "timestamp": timestamp,
        "bundle": bundle.to_dict(),
    }


def _build_admission_record(
    event: Any, cycle_id: int, timestamp: str
) -> Dict[str, Any]:
    """Build a log record for admission_trace.jsonl."""
    return {
        "cycle_id": cycle_id,
        "artifact_id": getattr(event, "artifact_id", ""),
        "gate": getattr(event, "gate", ""),
        "result": getattr(event, "result", ""),
        "reason_code": getattr(event, "reason_code", ""),
        "timestamp": timestamp,
    }


def _build_selector_record(
    event: Any, cycle_id: int, timestamp: str
) -> Dict[str, Any]:
    """Build a log record for selector_trace.jsonl."""
    return {
        "cycle_id": cycle_id,
        "artifact_id": getattr(event, "candidate_id", ""),
        "selector_rank": getattr(event, "rank", 0),
        "result": getattr(event, "result", "selected"),
        "timestamp": timestamp,
    }


def _parse_observation_stream(obs_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL observation stream (pre-baked deterministic observations)."""
    records: List[Dict[str, Any]] = []
    with open(obs_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _build_candidates_from_observation(obs_data: Dict[str, Any]) -> List[CandidateBundle]:
    """Extract CandidateBundle(s) from a pre-baked observation payload.

    The observation envelope carries fully formed artifacts using the
    same field names as the kernel dataclasses.
    """
    candidates = []
    bundles = obs_data.get("candidates", [])
    for b in bundles:
        ar_data = b["action_request"]
        sc_data = b.get("scope_claim")
        j_data = b.get("justification")

        ar = ActionRequest(
            action_type=ar_data["action_type"],
            fields=ar_data.get("fields", {}),
            author=ar_data.get("author", Author.KERNEL.value),
            created_at=ar_data.get("created_at", ""),
        )
        sc = None
        if sc_data:
            sc = ScopeClaim(
                observation_ids=sc_data.get("observation_ids", []),
                claim=sc_data.get("claim", ""),
                clause_ref=sc_data.get("clause_ref", ""),
                author=sc_data.get("author", Author.KERNEL.value),
                created_at=sc_data.get("created_at", ""),
            )
        j = None
        if j_data:
            j = Justification(
                text=j_data.get("text", ""),
                author=j_data.get("author", Author.KERNEL.value),
                created_at=j_data.get("created_at", ""),
            )
        cb = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=j,
            authority_citations=b.get("authority_citations", []),
        )
        candidates.append(cb)
    return candidates


def run(
    constitution_path: str,
    log_dir: str,
    observations_path: str,
) -> int:
    """Execute rsa run.  Returns 0 on success, 1 on failure."""
    const_path = Path(constitution_path)
    logs = Path(log_dir)
    obs_path = Path(observations_path)

    # Ensure log directory exists
    logs.mkdir(parents=True, exist_ok=True)

    # --- 1. Validate constitution integrity ---
    constitution = Constitution(str(const_path))
    active_constitution_hash = constitution.sha256

    print(f"[X-0E] Constitution loaded: {const_path.name}")
    print(f"[X-0E] Constitution hash: {active_constitution_hash}")
    print(f"[X-0E] Kernel version: {KERNEL_VERSION_ID}")

    # --- 2. Log run metadata ---
    run_meta = {
        "event": "RUN_START",
        "kernel_version_id": KERNEL_VERSION_ID,
        "constitution_hash": active_constitution_hash,
        "constitution_path": str(const_path),
    }
    append_jsonl(logs / "run_meta.jsonl", run_meta)

    # --- 3. Initialize state hash chain ---
    prev_hash = initial_state_hash(active_constitution_hash, KERNEL_VERSION_ID)
    print(f"[X-0E] Initial state hash: {state_hash_hex(prev_hash)}")

    # --- 4. Initialize executor with startup reconciliation ---
    executor = ExecutorX0E(logs)
    executor.startup_reconciliation()

    # --- 5. Load observation stream ---
    obs_stream = _parse_observation_stream(obs_path)
    print(f"[X-0E] Observations loaded: {len(obs_stream)} cycles")

    # --- 6. Process cycles ---
    repo_root = Path(".")
    for cycle_idx, obs_data in enumerate(obs_stream):
        cycle_id = obs_data.get("cycle_id", cycle_idx)
        timestamp = obs_data.get("timestamp", "")

        # Build observations (TIMESTAMP + USER_INPUT)
        observations = [
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": timestamp},
                author=Author.KERNEL.value,
                created_at=timestamp,
            ),
        ]
        # Add payload observations
        if "observation" in obs_data:
            observations.append(Observation(
                kind=obs_data["observation"].get("kind", ObservationKind.USER_INPUT.value),
                payload=obs_data["observation"].get("payload", {}),
                author=obs_data["observation"].get("author", Author.USER.value),
                created_at=timestamp,
            ))

        # Build candidates from pre-baked data
        candidates = _build_candidates_from_observation(obs_data)

        # Build internal state
        internal_state = InternalState(
            cycle_index=cycle_id,
        )

        # --- Log observations ---
        obs_records = []
        for obs in observations:
            rec = _build_observation_record(obs, cycle_id, timestamp)
            append_jsonl(logs / "observations.jsonl", rec)
            obs_records.append(rec)

        # --- Log artifacts ---
        art_records = []
        for bundle in candidates:
            rec = _build_artifact_record(bundle, cycle_id, timestamp)
            append_jsonl(logs / "artifacts.jsonl", rec)
            art_records.append(rec)

        # --- Run kernel ---
        output: PolicyOutput = policy_core(
            observations=observations,
            constitution=constitution,
            internal_state=internal_state,
            candidates=candidates,
            repo_root=repo_root,
        )

        # --- Log admission trace ---
        adm_records = []
        for event in output.admission_events:
            rec = _build_admission_record(event, cycle_id, timestamp)
            append_jsonl(logs / "admission_trace.jsonl", rec)
            adm_records.append(rec)

        # --- Log selector trace ---
        sel_records = []
        if output.selection_event is not None:
            rec = _build_selector_record(output.selection_event, cycle_id, timestamp)
            append_jsonl(logs / "selector_trace.jsonl", rec)
            sel_records.append(rec)

        # --- Execute warrant (if ACTION) ---
        exe_records = []
        if output.decision.decision_type == DecisionType.ACTION.value:
            warrant = output.decision.warrant
            bundle = output.decision.bundle
            exec_record = executor.execute(warrant, bundle, cycle_id, timestamp)
            exe_records.append(exec_record)
            status = exec_record["execution_status"]
            print(f"  Cycle {cycle_id}: ACTION → Notify → {status} (warrant={warrant.warrant_id[:12]}...)")
        else:
            decision_type = output.decision.decision_type
            print(f"  Cycle {cycle_id}: {decision_type}")
            # Log a no-execution trace entry
            no_exec = {
                "cycle_id": cycle_id,
                "execution_status": "NO_ACTION",
                "decision_type": decision_type,
                "timestamp": timestamp,
            }
            append_jsonl(logs / "execution_trace.jsonl", no_exec)
            exe_records.append(no_exec)

        # --- Compute state hash ---
        prev_hash = cycle_state_hash(
            prev_hash,
            artifacts_records=art_records,
            admission_records=adm_records,
            selector_records=sel_records,
            execution_records=exe_records,
        )

        # Log state hash
        hash_record = {
            "cycle_id": cycle_id,
            "state_hash": state_hash_hex(prev_hash),
            "timestamp": timestamp,
        }
        append_jsonl(logs / "state_hashes.jsonl", hash_record)

    # --- 7. Log run completion ---
    final_meta = {
        "event": "RUN_COMPLETE",
        "final_state_hash": state_hash_hex(prev_hash),
        "cycles_processed": len(obs_stream),
        "kernel_version_id": KERNEL_VERSION_ID,
    }
    append_jsonl(logs / "run_meta.jsonl", final_meta)

    print(f"\n[X-0E] Run complete. {len(obs_stream)} cycles processed.")
    print(f"[X-0E] Final state hash: {state_hash_hex(prev_hash)}")
    return 0
