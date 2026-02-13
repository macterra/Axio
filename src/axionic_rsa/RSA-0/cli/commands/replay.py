"""
RSA-0 X-0E — ``rsa replay`` command

Deterministic replay from logs.  Reconstructs kernel decisions and
recomputes the state hash chain.  Any divergence constitutes failure.

Usage:
    rsa replay --constitution <path> --log-dir <path>
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    Decision,
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
    component_hash,
    cycle_state_hash,
    initial_state_hash,
    state_hash_hex,
)
from host.log_io import read_jsonl, read_jsonl_by_cycle


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CycleReplayResult:
    cycle_id: int
    match: bool
    original_decision_type: str = ""
    replayed_decision_type: str = ""
    original_warrant_id: Optional[str] = None
    replayed_warrant_id: Optional[str] = None
    state_hash_match: bool = True
    expected_hash: str = ""
    computed_hash: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class ReplayReport:
    success: bool
    cycles_replayed: int = 0
    cycles_matched: int = 0
    final_hash_match: bool = False
    expected_final_hash: str = ""
    computed_final_hash: str = ""
    cycle_results: List[CycleReplayResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Log reconstruction
# ---------------------------------------------------------------------------

def _reconstruct_observations(obs_entries: List[Dict[str, Any]]) -> List[Observation]:
    """Reconstruct Observation objects from logged observation entries."""
    observations = []
    for entry in obs_entries:
        obs = Observation(
            kind=entry.get("kind", entry.get("observation", {}).get("kind", "")),
            payload=entry.get("payload", entry.get("observation", {}).get("payload", {})),
            author=entry.get("author", entry.get("observation", {}).get("author", Author.KERNEL.value)),
            created_at=entry.get("timestamp", entry.get("observation", {}).get("created_at", "")),
            id=entry.get("observation_id", entry.get("observation", {}).get("id", "")),
        )
        observations.append(obs)
    return observations


def _reconstruct_candidates(art_entries: List[Dict[str, Any]]) -> List[CandidateBundle]:
    """Reconstruct CandidateBundle objects from logged artifact entries."""
    candidates = []
    for entry in art_entries:
        bundle_data = entry.get("bundle", {})

        ar_data = bundle_data.get("action_request", {})
        sc_data = bundle_data.get("scope_claim")
        j_data = bundle_data.get("justification")

        ar = ActionRequest(
            action_type=ar_data.get("action_type", ""),
            fields=ar_data.get("fields", {}),
            author=ar_data.get("author", Author.REFLECTION.value),
            created_at=ar_data.get("created_at", ""),
            id=ar_data.get("id", ""),
        )
        sc = None
        if sc_data:
            sc = ScopeClaim(
                observation_ids=sc_data.get("observation_ids", []),
                claim=sc_data.get("claim", ""),
                clause_ref=sc_data.get("clause_ref", ""),
                author=sc_data.get("author", Author.REFLECTION.value),
                created_at=sc_data.get("created_at", ""),
                id=sc_data.get("id", ""),
            )
        j = None
        if j_data:
            j = Justification(
                text=j_data.get("text", ""),
                author=j_data.get("author", Author.REFLECTION.value),
                created_at=j_data.get("created_at", ""),
                id=j_data.get("id", ""),
            )
        cb = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=j,
            authority_citations=bundle_data.get("authority_citations", []),
        )
        candidates.append(cb)
    return candidates


# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------

def _verify_execution_coherence(
    exec_entries: List[Dict[str, Any]],
    outbox_entries: List[Dict[str, Any]],
    replayed_warrant_id: Optional[str],
    replayed_decision_type: str,
    cycle_id: int,
) -> List[str]:
    """Verify execution outcome coherence (A24/A25).

    - Every SUCCESS execution must have a valid recomputed warrant.
    - No execution without warrant.
    - If FAILURE, outbox must NOT contain that warrant_id.
    """
    errors: List[str] = []
    outbox_wids = {e.get("warrant_id") for e in outbox_entries if e.get("warrant_id")}

    for exec_entry in exec_entries:
        wid = exec_entry.get("warrant_id", "")
        status = exec_entry.get("execution_status", "")

        if status == "SUCCESS":
            # Must have a corresponding replayed warrant
            if replayed_decision_type != DecisionType.ACTION.value:
                errors.append(
                    f"Cycle {cycle_id}: execution SUCCESS for warrant {wid[:12]}... "
                    f"but replay decision is {replayed_decision_type}, not ACTION"
                )
            elif replayed_warrant_id and replayed_warrant_id != wid:
                errors.append(
                    f"Cycle {cycle_id}: execution warrant {wid[:12]}... "
                    f"differs from replayed warrant {replayed_warrant_id[:12]}..."
                )
        elif status == "FAILURE":
            # If failure, outbox must NOT contain this warrant_id
            if wid in outbox_wids:
                errors.append(
                    f"Cycle {cycle_id}: execution FAILURE for {wid[:12]}... "
                    f"but warrant_id found in outbox"
                )
        elif status == "NO_ACTION":
            # No-action cycles are fine if replay also didn't produce an action
            if replayed_decision_type == DecisionType.ACTION.value:
                errors.append(
                    f"Cycle {cycle_id}: logged NO_ACTION but replay produced ACTION"
                )

    return errors


def _verify_reconciliation(
    all_exec_entries: List[Dict[str, Any]],
    all_outbox_entries: List[Dict[str, Any]],
    recon_entries: List[Dict[str, Any]],
) -> List[str]:
    """Simulate reconciliation and verify it matches what was logged.

    Per A25: replay recomputes what reconciliation should have done
    and verifies execution_trace contains the synthesized entries.
    """
    errors: List[str] = []

    exec_wids = {e.get("warrant_id") for e in all_exec_entries if e.get("warrant_id")}
    outbox_wids = {e.get("warrant_id") for e in all_outbox_entries if e.get("warrant_id")}

    # Orphans = in outbox but not in execution_trace before reconciliation
    # Reconciliation should have added them.
    reconciled_wids = {e.get("warrant_id") for e in recon_entries if e.get("warrant_id")}

    # After reconciliation, all outbox wids should appear in exec trace
    missing = outbox_wids - exec_wids
    if missing:
        errors.append(
            f"Reconciliation gap: {len(missing)} warrant_ids in outbox "
            f"but not in execution_trace after reconciliation"
        )

    return errors


# ---------------------------------------------------------------------------
# Main replay function
# ---------------------------------------------------------------------------

def replay(
    constitution_path: str,
    log_dir: str,
) -> ReplayReport:
    """Execute deterministic replay from logs."""
    const_path = Path(constitution_path)
    logs = Path(log_dir)
    report = ReplayReport(success=True)

    # --- 1. Validate constitution ---
    constitution = Constitution(str(const_path))
    active_hash = constitution.sha256

    # --- 2. Validate kernel_version_id from run metadata ---
    run_meta = read_jsonl(logs / "run_meta.jsonl")
    logged_version_id = None
    logged_constitution_hash = None
    logged_final_hash = None

    for entry in run_meta:
        if entry.get("event") == "RUN_START":
            logged_version_id = entry.get("kernel_version_id")
            logged_constitution_hash = entry.get("constitution_hash")
        elif entry.get("event") == "RUN_COMPLETE":
            logged_final_hash = entry.get("final_state_hash")

    if logged_version_id and logged_version_id != KERNEL_VERSION_ID:
        report.errors.append(
            f"kernel_version_id mismatch: logged={logged_version_id}, "
            f"current={KERNEL_VERSION_ID}"
        )
        report.success = False
        return report

    if logged_constitution_hash and logged_constitution_hash != active_hash:
        report.errors.append(
            f"Constitution hash mismatch: logged={logged_constitution_hash}, "
            f"loaded={active_hash}"
        )
        report.success = False
        return report

    # --- 3. Load all logs ---
    obs_by_cycle = read_jsonl_by_cycle(logs / "observations.jsonl")
    art_by_cycle = read_jsonl_by_cycle(logs / "artifacts.jsonl")
    adm_by_cycle = read_jsonl_by_cycle(logs / "admission_trace.jsonl")
    sel_by_cycle = read_jsonl_by_cycle(logs / "selector_trace.jsonl")
    exe_by_cycle = read_jsonl_by_cycle(logs / "execution_trace.jsonl")
    hash_by_cycle = read_jsonl_by_cycle(logs / "state_hashes.jsonl")

    all_outbox = read_jsonl(logs / "outbox.jsonl")
    all_recon = read_jsonl(logs / "reconciliation_trace.jsonl")
    all_exec = read_jsonl(logs / "execution_trace.jsonl")

    # --- 4. Verify reconciliation ---
    recon_errors = _verify_reconciliation(all_exec, all_outbox, all_recon)
    if recon_errors:
        report.errors.extend(recon_errors)

    # --- 5. Determine cycle range ---
    all_cycles = sorted(
        set(obs_by_cycle.keys())
        | set(art_by_cycle.keys())
        | set(adm_by_cycle.keys())
        | set(exe_by_cycle.keys())
    )
    # Filter out negative cycles (reconciliation)
    all_cycles = [c for c in all_cycles if c >= 0]

    # --- 6. Initialize state hash chain ---
    prev_hash = initial_state_hash(active_hash, KERNEL_VERSION_ID)
    repo_root = Path(".")

    # --- 7. Replay each cycle ---
    for cycle_id in all_cycles:
        cycle_result = CycleReplayResult(cycle_id=cycle_id, match=True)

        # Reconstruct observations
        cycle_obs_entries = obs_by_cycle.get(cycle_id, [])
        observations = _reconstruct_observations(cycle_obs_entries)

        # Reconstruct candidates from artifacts log
        cycle_art_entries = art_by_cycle.get(cycle_id, [])
        candidates = _reconstruct_candidates(cycle_art_entries)

        # Build internal state
        internal_state = InternalState(
            cycle_index=cycle_id,
        )

        # --- Replay kernel decision ---
        output: PolicyOutput = policy_core(
            observations=observations,
            constitution=constitution,
            internal_state=internal_state,
            candidates=candidates,
            repo_root=repo_root,
        )

        replayed_dt = output.decision.decision_type
        replayed_wid = (
            output.decision.warrant.warrant_id
            if output.decision.warrant else None
        )

        cycle_result.replayed_decision_type = replayed_dt
        cycle_result.replayed_warrant_id = replayed_wid

        # --- Compare with logged execution trace ---
        cycle_exec = exe_by_cycle.get(cycle_id, [])
        logged_dt = None
        logged_wid = None

        for ex in cycle_exec:
            if ex.get("execution_status") == "SUCCESS":
                logged_wid = ex.get("warrant_id")
                logged_dt = DecisionType.ACTION.value
            elif ex.get("execution_status") == "NO_ACTION":
                logged_dt = ex.get("decision_type", "")
            elif ex.get("execution_status") == "FAILURE":
                logged_wid = ex.get("warrant_id")
                logged_dt = DecisionType.ACTION.value

        cycle_result.original_decision_type = logged_dt or ""

        # Decision type match
        if logged_dt and logged_dt != replayed_dt:
            cycle_result.match = False
            cycle_result.errors.append(
                f"Decision type divergence: logged={logged_dt}, replayed={replayed_dt}"
            )

        # Warrant ID match
        if logged_wid and logged_wid != replayed_wid:
            cycle_result.match = False
            cycle_result.errors.append(
                f"Warrant ID divergence: logged={logged_wid[:12]}..., "
                f"replayed={replayed_wid[:12] if replayed_wid else 'None'}..."
            )

        # --- Execution coherence ---
        coherence_errors = _verify_execution_coherence(
            cycle_exec, all_outbox, replayed_wid, replayed_dt, cycle_id
        )
        if coherence_errors:
            cycle_result.errors.extend(coherence_errors)

        # --- Recompute state hash chain ---
        # Use the ORIGINAL logged records for hash computation
        # (replay verifies that the decisions match, then verifies
        #  that the hash chain over the logged records matches)
        cycle_adm = adm_by_cycle.get(cycle_id, [])
        cycle_sel = sel_by_cycle.get(cycle_id, [])

        prev_hash = cycle_state_hash(
            prev_hash,
            artifacts_records=cycle_art_entries,
            admission_records=cycle_adm,
            selector_records=cycle_sel,
            execution_records=cycle_exec,
        )

        computed_hex = state_hash_hex(prev_hash)
        cycle_result.computed_hash = computed_hex

        # Compare with logged hash
        logged_hashes = hash_by_cycle.get(cycle_id, [])
        if logged_hashes:
            expected_hex = logged_hashes[-1].get("state_hash", "")
            cycle_result.expected_hash = expected_hex
            if expected_hex != computed_hex:
                cycle_result.state_hash_match = False
                cycle_result.match = False
                cycle_result.errors.append(
                    f"State hash divergence: expected={expected_hex[:16]}..., "
                    f"computed={computed_hex[:16]}..."
                )

        if not cycle_result.match or cycle_result.errors:
            report.success = False

        report.cycle_results.append(cycle_result)

    # --- 8. Final checks ---
    report.cycles_replayed = len(all_cycles)
    report.cycles_matched = sum(1 for r in report.cycle_results if r.match)
    report.computed_final_hash = state_hash_hex(prev_hash)

    if logged_final_hash:
        report.expected_final_hash = logged_final_hash
        report.final_hash_match = (logged_final_hash == report.computed_final_hash)
        if not report.final_hash_match:
            report.errors.append(
                f"Final state hash mismatch: logged={logged_final_hash[:16]}..., "
                f"computed={report.computed_final_hash[:16]}..."
            )
            report.success = False

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_replay(
    constitution_path: str,
    log_dir: str,
) -> int:
    """Execute replay and print results.  Returns 0 on success, 1 on failure."""
    print(f"[X-0E REPLAY] Constitution: {constitution_path}")
    print(f"[X-0E REPLAY] Log dir: {log_dir}")
    print(f"[X-0E REPLAY] Kernel version: {KERNEL_VERSION_ID}")
    print()

    report = replay(constitution_path, log_dir)

    for r in report.cycle_results:
        status = "MATCH" if r.match else "DIVERGENCE"
        print(f"  Cycle {r.cycle_id}: {status}")
        if r.original_decision_type or r.replayed_decision_type:
            print(f"    Decision: logged={r.original_decision_type}, replayed={r.replayed_decision_type}")
        if r.original_warrant_id or r.replayed_warrant_id:
            logged_w = r.original_warrant_id[:12] + "..." if r.original_warrant_id else "None"
            replayed_w = r.replayed_warrant_id[:12] + "..." if r.replayed_warrant_id else "None"
            print(f"    Warrant: logged={logged_w}, replayed={replayed_w}")
        if r.computed_hash:
            print(f"    State hash: {r.computed_hash[:16]}...")
        for err in r.errors:
            print(f"    ERROR: {err}")

    print()
    if report.errors:
        for err in report.errors:
            print(f"[X-0E REPLAY] ERROR: {err}")
        print()

    print(f"[X-0E REPLAY] Cycles: {report.cycles_replayed} replayed, {report.cycles_matched} matched")
    print(f"[X-0E REPLAY] Final hash: {report.computed_final_hash}")
    if report.expected_final_hash:
        print(f"[X-0E REPLAY] Expected:   {report.expected_final_hash}")
        print(f"[X-0E REPLAY] Final hash match: {report.final_hash_match}")

    if report.success:
        print("\n[X-0E REPLAY] SUCCESS — deterministic replay verified.")
        return 0
    else:
        print("\n[X-0E REPLAY] FAILURE — replay divergence detected.")
        return 1
