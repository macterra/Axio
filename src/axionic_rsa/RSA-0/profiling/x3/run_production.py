#!/usr/bin/env python3
"""
X-3 Production Run

Executes the full X-3 sovereign succession profiling:
  - 8 mandatory session families:
    X3-BASE, X3-NEAR_BOUND, X3-CHURN, X3-RAT_DELAY,
    X3-MULTI_ROT, X3-INVALID_SIG, X3-DUP_CYCLE, X3-INVALID_BOUNDARY
  - Per-session admission gates (6X/7X/8X)
  - Deterministic N-cycle plans from seeded generators
  - Boundary verification + succession activation at cycle boundaries
  - Replay verification (state_out[i] == state_in[i+1])
  - Session closure evaluation

Outputs:
  - logs/x3/<session_id>/x3_sessions.jsonl
  - logs/x3/<session_id>/x3_metrics.jsonl
  - logs/x3/<session_id>/x3_boundary_events.jsonl
  - profiling/x3/results/x3_summary.json
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent        # profiling/x3/
RSA0_ROOT = SCRIPT_DIR.parent.parent                # RSA-0/
sys.path.insert(0, str(RSA0_ROOT))

from profiling.x3.harness.src.constitution_helper_x3 import (
    create_x3_profiling_constitution,
)
from profiling.x3.harness.src.runner_x3 import X3Runner, X3SessionResult
from profiling.x3.harness.src.schemas_x3 import (
    SessionFamilyX3,
    X3SessionStart,
)


# ---------------------------------------------------------------------------
# Session parameter presets (frozen before production run)
# ---------------------------------------------------------------------------

def _base_seeds(family_offset: int) -> Dict[str, int]:
    return {
        "treaty_stream": 303600 + family_offset,
        "action_stream": 303610 + family_offset,
        "succession_stream": 303620 + family_offset,
    }


# ---------- X3-BASE ----------
def _x3_base_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_BASE.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=50,
        density_upper_bound=0.75,
        seeds=_base_seeds(0),
        rotation_schedule=[{"cycle": 25, "successor_index": 1}],
        ratification_delay_cycles=1,
        delegation_state_mode="LOW",
        grantee_count=3,
        delegated_requests_per_cycle_fraction=0.5,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-NEAR_BOUND ----------
def _x3_near_bound_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_NEAR_BOUND.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=60,
        density_upper_bound=0.75,
        seeds=_base_seeds(1),
        rotation_schedule=[{"cycle": 30, "successor_index": 1}],
        ratification_delay_cycles=1,
        delegation_state_mode="NEAR_BOUND",
        grantee_count=5,
        delegated_requests_per_cycle_fraction=0.6,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-CHURN ----------
def _x3_churn_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_CHURN.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=80,
        density_upper_bound=0.75,
        seeds=_base_seeds(2),
        rotation_schedule=[{"cycle": 40, "successor_index": 1}],
        ratification_delay_cycles=2,
        delegation_state_mode="CHURN_ACTIVE",
        grantee_count=6,
        delegated_requests_per_cycle_fraction=0.7,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-RAT_DELAY ----------
def _x3_rat_delay_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_RAT_DELAY.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=60,
        density_upper_bound=0.75,
        seeds=_base_seeds(3),
        rotation_schedule=[{"cycle": 20, "successor_index": 1}],
        ratification_delay_cycles=5,
        delegation_state_mode="LOW",
        grantee_count=4,
        delegated_requests_per_cycle_fraction=0.5,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-MULTI_ROT ----------
def _x3_multi_rot_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_MULTI_ROT.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=80,
        density_upper_bound=0.75,
        seeds=_base_seeds(4),
        rotation_schedule=[
            {"cycle": 20, "successor_index": 1},
            {"cycle": 40, "successor_index": 2},
            {"cycle": 60, "successor_index": 3},
        ],
        ratification_delay_cycles=2,
        delegation_state_mode="LOW",
        grantee_count=4,
        delegated_requests_per_cycle_fraction=0.5,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-INVALID_SIG ----------
def _x3_invalid_sig_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_INVALID_SIG.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=50,
        density_upper_bound=0.75,
        seeds=_base_seeds(5),
        rotation_schedule=[{"cycle": 25, "successor_index": 1}],
        ratification_delay_cycles=1,
        delegation_state_mode="LOW",
        grantee_count=3,
        delegated_requests_per_cycle_fraction=0.3,
        invalid_succession_fractions={"invalid_signature": 1.0},
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-DUP_CYCLE ----------
def _x3_dup_cycle_session() -> X3SessionStart:
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_DUP_CYCLE.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=50,
        density_upper_bound=0.75,
        seeds=_base_seeds(6),
        rotation_schedule=[{"cycle": 25, "successor_index": 1}],
        ratification_delay_cycles=1,
        delegation_state_mode="LOW",
        grantee_count=3,
        delegated_requests_per_cycle_fraction=0.3,
        invalid_succession_fractions={"duplicate_cycle": 1.0},
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


# ---------- X3-INVALID_BOUNDARY ----------
def _x3_invalid_boundary_session() -> X3SessionStart:
    """5 sub-sessions (A-E) with different boundary faults at cycle 20."""
    return X3SessionStart(
        session_family=SessionFamilyX3.X3_INVALID_BOUNDARY.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=50,
        density_upper_bound=0.75,
        seeds=_base_seeds(7),
        rotation_schedule=[{"cycle": 20, "successor_index": 1}],
        ratification_delay_cycles=1,
        delegation_state_mode="LOW",
        grantee_count=3,
        delegated_requests_per_cycle_fraction=0.3,
        invalid_boundary_faults=[
            {"sub_session": "A", "fault_type": "wrong_commit_signer", "cycle": 21},
            {"sub_session": "B", "fault_type": "wrong_start_signer", "cycle": 21},
            {"sub_session": "C", "fault_type": "missing_pending_successor", "cycle": 21},
            {"sub_session": "D", "fault_type": "spurious_pending_successor", "cycle": 15},
            {"sub_session": "E", "fault_type": "chain_mismatch", "cycle": 21},
        ],
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


ALL_SESSION_FACTORIES = [
    _x3_base_session,
    _x3_near_bound_session,
    _x3_churn_session,
    _x3_rat_delay_session,
    _x3_multi_rot_session,
    _x3_invalid_sig_session,
    _x3_dup_cycle_session,
    _x3_invalid_boundary_session,
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    constitution = create_x3_profiling_constitution(repo_root=RSA0_ROOT)

    log_root = RSA0_ROOT / "logs" / "x3"
    results_dir = RSA0_ROOT / "profiling" / "x3" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    families = ", ".join(f.value for f in SessionFamilyX3)

    print(f"\n{'='*70}")
    print(f"  RSA X-3 PRODUCTION RUN")
    print(f"  Sovereign Succession Under Lineage Profiling")
    print(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"  Families: {families}")
    print(f"{'='*70}\n")

    all_results: List[Dict[str, Any]] = []
    overall_pass = True

    for factory in ALL_SESSION_FACTORIES:
        session_start = factory()
        family = session_start.session_family

        # X3-INVALID_BOUNDARY runs multiple sub-sessions
        if family == SessionFamilyX3.X3_INVALID_BOUNDARY.value:
            sub_results = _run_invalid_boundary_subsessions(
                session_start, constitution, log_root,
            )
            for sr in sub_results:
                all_results.append(sr)
                if not sr.get("closure_pass", False):
                    overall_pass = False
            continue

        print(f"\n--- {family} ---")

        runner = X3Runner(
            session_start=session_start,
            constitution_frame=constitution,
            repo_root=RSA0_ROOT,
            log_root=log_root,
            verbose=True,
        )
        result = runner.run()
        summary = _make_summary(result)
        all_results.append(summary)

        if not result.closure_pass:
            overall_pass = False

        _print_result(result)

    # Write combined summary
    summary_path = results_dir / "x3_summary.json"
    combined = {
        "run_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_pass": overall_pass,
        "sessions": all_results,
    }
    summary_path.write_text(json.dumps(combined, indent=2))

    print(f"\n{'='*70}")
    print(f"  X-3 PRODUCTION RUN COMPLETE")
    print(f"{'='*70}")
    print(f"  Overall: {'PASS' if overall_pass else 'FAIL'}")
    print(f"  Summary: {summary_path}")
    print()

    sys.exit(0 if overall_pass else 1)


# ---------------------------------------------------------------------------
# X3-INVALID_BOUNDARY sub-sessions
# ---------------------------------------------------------------------------

def _run_invalid_boundary_subsessions(
    template: X3SessionStart,
    constitution,
    log_root: Path,
) -> List[Dict[str, Any]]:
    """Run 5 sub-sessions (A-E) each with one boundary fault."""
    results: List[Dict[str, Any]] = []

    for fault_spec in template.invalid_boundary_faults:
        sub_label = fault_spec["sub_session"]
        fault_type = fault_spec["fault_type"]
        fault_cycle = fault_spec["cycle"]

        print(f"\n--- X3-INVALID_BOUNDARY sub-session {sub_label} "
              f"({fault_type} @ cycle {fault_cycle}) ---")

        # Clone session start for this sub-session
        sub_start = X3SessionStart(
            session_family=template.session_family,
            session_id=f"{template.session_id}-{sub_label}",
            session_length_cycles=template.session_length_cycles,
            density_upper_bound=template.density_upper_bound,
            seeds=dict(template.seeds),
            rotation_schedule=list(template.rotation_schedule),
            ratification_delay_cycles=template.ratification_delay_cycles,
            delegation_state_mode=template.delegation_state_mode,
            grantee_count=template.grantee_count,
            delegated_requests_per_cycle_fraction=template.delegated_requests_per_cycle_fraction,
            invalid_boundary_faults=[fault_spec],
            created_at=template.created_at,
        )

        runner = X3Runner(
            session_start=sub_start,
            constitution_frame=constitution,
            repo_root=RSA0_ROOT,
            log_root=log_root,
            verbose=True,
        )
        result = runner.run()
        summary = _make_summary(result)
        summary["sub_session"] = sub_label
        summary["fault_type"] = fault_type
        summary["fault_cycle"] = fault_cycle
        results.append(summary)

        _print_result(result)

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_summary(result: X3SessionResult) -> Dict[str, Any]:
    return {
        "session_family": result.session_family,
        "session_id": result.session_id,
        "total_cycles": result.total_cycles,
        "closure_pass": result.closure_pass,
        "failure_reasons": result.failure_reasons,
        "replay_divergences": result.replay_divergence_count,
        "total_rotations_activated": result.total_rotations_activated,
        "total_successions_rejected": result.total_successions_rejected,
        "total_boundary_faults_detected": result.total_boundary_faults_detected,
        "total_grants_admitted": result.total_grants_admitted,
        "total_delegated_warrants": result.total_delegated_warrants,
        "total_ratifications_admitted": result.total_ratifications_admitted,
        "density_max": (
            max(result.density_series) if result.density_series else 0.0
        ),
        "density_mean": (
            sum(result.density_series) / len(result.density_series)
            if result.density_series else 0.0
        ),
    }


def _print_result(result: X3SessionResult) -> None:
    print(f"  Cycles: {result.total_cycles}")
    print(f"  Rotations: {result.total_rotations_activated}")
    print(f"  Boundary faults: {result.total_boundary_faults_detected}")
    print(f"  Closure: {'PASS' if result.closure_pass else 'FAIL'}")
    if result.failure_reasons:
        for r in result.failure_reasons:
            print(f"    FAIL: {r}")


if __name__ == "__main__":
    main()
