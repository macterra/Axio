#!/usr/bin/env python3
"""
X-2D Production Run

Executes the full X-2D delegation churn & density stress profiling:
  - 5 mandatory session families: D-BASE, D-CHURN, D-SAT, D-RATCHET, D-EDGE
  - Per-session admission gates (6D/7D/8D)
  - Deterministic N-cycle plans from seeded generators
  - X2D_TOPOLOGICAL cycle ordering
  - Per-cycle and window metrics
  - Replay verification
  - Session closure evaluation

Outputs:
  - logs/x2d/<session_id>/x2d_session.jsonl
  - logs/x2d/<session_id>/x2d_metrics.jsonl
  - logs/x2d/<session_id>/x2d_window_metrics.jsonl
  - results/x2d/x2d_summary.json
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent        # profiling/x2d/
RSA0_ROOT = SCRIPT_DIR.parent.parent                # RSA-0/
sys.path.insert(0, str(RSA0_ROOT))

from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from profiling.x2d.harness.src.constitution_helper import create_x2d_profiling_constitution
from profiling.x2d.harness.src.runner import X2DRunner, X2DSessionResult
from profiling.x2d.harness.src.schemas import SessionFamily, X2DSessionStart
from profiling.x2d.harness.src.metrics import (
    compute_per_cycle_metrics,
    compute_window_metrics,
    write_metrics,
)


# ---------------------------------------------------------------------------
# Session parameter presets (frozen before production run)
# ---------------------------------------------------------------------------

def _base_seeds(family_offset: int) -> Dict[str, int]:
    return {
        "treaty_stream": 202600 + family_offset,
        "action_stream": 202610 + family_offset,
        "amendment_stream": 202620 + family_offset,
    }


def _base_invalid_fractions() -> Dict[str, float]:
    return {
        "missing_signature": 0.05,
        "invalid_signature": 0.05,
        "wrong_treaty_citation": 0.05,
        "scope_violation": 0.05,
        "expired_grant": 0.05,
        "revoked_grant": 0.05,
    }


def _d_base_session() -> X2DSessionStart:
    return X2DSessionStart(
        session_family=SessionFamily.D_BASE.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=50,
        window_size_cycles=10,
        density_upper_bound=0.75,
        density_proximity_delta=0.05,
        deadlock_threshold_K=5,
        seeds=_base_seeds(0),
        invalid_request_fractions=_base_invalid_fractions(),
        grant_duration_distribution={"type": "uniform", "min": 20, "max": 40},
        grantee_count=5,
        max_active_grants_per_grantee=3,
        delegated_requests_per_cycle_fraction=0.5,
        amendment_schedule=[],
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _d_churn_session() -> X2DSessionStart:
    return X2DSessionStart(
        session_family=SessionFamily.D_CHURN.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=80,
        window_size_cycles=10,
        density_upper_bound=0.75,
        density_proximity_delta=0.05,
        deadlock_threshold_K=5,
        seeds=_base_seeds(1),
        invalid_request_fractions=_base_invalid_fractions(),
        grant_duration_distribution={"type": "uniform", "min": 3, "max": 15},
        grantee_count=8,
        max_active_grants_per_grantee=4,
        delegated_requests_per_cycle_fraction=0.7,
        amendment_schedule=[],
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _d_sat_session() -> X2DSessionStart:
    return X2DSessionStart(
        session_family=SessionFamily.D_SAT.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=60,
        window_size_cycles=10,
        density_upper_bound=0.75,
        density_proximity_delta=0.05,
        deadlock_threshold_K=5,
        seeds=_base_seeds(2),
        invalid_request_fractions=_base_invalid_fractions(),
        grant_duration_distribution={"type": "uniform", "min": 10, "max": 30},
        grantee_count=10,
        max_active_grants_per_grantee=5,
        delegated_requests_per_cycle_fraction=0.6,
        amendment_schedule=[],
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _d_ratchet_session() -> X2DSessionStart:
    return X2DSessionStart(
        session_family=SessionFamily.D_RATCHET.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=60,
        window_size_cycles=10,
        density_upper_bound=0.75,
        density_proximity_delta=0.05,
        deadlock_threshold_K=5,
        seeds=_base_seeds(3),
        invalid_request_fractions=_base_invalid_fractions(),
        grant_duration_distribution={"type": "uniform", "min": 10, "max": 30},
        grantee_count=6,
        max_active_grants_per_grantee=4,
        delegated_requests_per_cycle_fraction=0.6,
        amendment_schedule=[
            {
                "cycle": 30,
                "type": "ban_action",
                "action": "WriteLocal",
                "description": "Ban WriteLocal at cycle 30",
            },
        ],
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _d_edge_session() -> X2DSessionStart:
    return X2DSessionStart(
        session_family=SessionFamily.D_EDGE.value,
        session_id=str(uuid.uuid4()),
        session_length_cycles=60,
        window_size_cycles=10,
        density_upper_bound=0.75,
        density_proximity_delta=0.05,
        deadlock_threshold_K=5,
        seeds=_base_seeds(4),
        invalid_request_fractions=_base_invalid_fractions(),
        grant_duration_distribution={"type": "uniform", "min": 5, "max": 20},
        grantee_count=8,
        max_active_grants_per_grantee=4,
        delegated_requests_per_cycle_fraction=0.8,
        amendment_schedule=[],
        target_density_band_low=0.60,
        target_density_band_high=0.74,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


ALL_SESSION_FACTORIES = [
    _d_base_session,
    _d_churn_session,
    _d_sat_session,
    _d_ratchet_session,
    _d_edge_session,
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Profiling constitution: v0.3 + AUTH_DELEGATION action_permissions
    # (AUTH_DELEGATION needs action_permissions for Gate 8C.2b to pass)
    constitution = create_x2d_profiling_constitution(repo_root=RSA0_ROOT)

    log_root = RSA0_ROOT / "logs" / "x2d"
    results_dir = RSA0_ROOT / "profiling" / "x2d" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  RSA X-2D PRODUCTION RUN")
    print(f"  Delegation Churn & Density Stress Profiling")
    print(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"  Families: {', '.join(f.value for f in SessionFamily)}")
    print(f"{'='*70}\n")

    all_results: List[Dict[str, Any]] = []
    overall_pass = True

    for factory in ALL_SESSION_FACTORIES:
        session_start = factory()
        session_start.canonical_hash()

        print(f"\n--- {session_start.session_family} ---")

        runner = X2DRunner(
            session_start=session_start,
            constitution=constitution,
            repo_root=RSA0_ROOT,
            log_root=log_root,
            verbose=True,
        )
        result = runner.run()

        # Compute and write metrics
        session_dir = log_root / session_start.session_id
        per_cycle = compute_per_cycle_metrics(result.cycle_results)
        window_metrics = compute_window_metrics(
            per_cycle, session_start.window_size_cycles,
        )
        write_metrics(session_dir, per_cycle, window_metrics)

        # Summary
        summary = {
            "session_family": result.session_family,
            "session_id": result.session_id,
            "total_cycles": result.total_cycles,
            "closure_pass": result.closure_pass,
            "failure_reasons": result.failure_reasons,
            "replay_divergences": result.replay_divergence_count,
            "density_max": max(result.density_series) if result.density_series else 0.0,
            "density_mean": (
                sum(result.density_series) / len(result.density_series)
                if result.density_series else 0.0
            ),
            "total_grants_admitted": result.total_grants_admitted,
            "total_delegated_warrants": result.total_delegated_warrants,
            "total_revalidation_invalidated": result.total_revalidation_invalidated,
        }
        all_results.append(summary)

        if not result.closure_pass:
            overall_pass = False

        print(f"  Cycles: {result.total_cycles}")
        print(f"  Closure: {'PASS' if result.closure_pass else 'FAIL'}")
        if result.failure_reasons:
            for r in result.failure_reasons:
                print(f"    FAIL: {r}")

    # Write combined summary
    summary_path = results_dir / "x2d_summary.json"
    combined = {
        "run_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_pass": overall_pass,
        "sessions": all_results,
    }
    summary_path.write_text(json.dumps(combined, indent=2))

    print(f"\n{'='*70}")
    print(f"  X-2D PRODUCTION RUN COMPLETE")
    print(f"{'='*70}")
    print(f"  Overall: {'PASS' if overall_pass else 'FAIL'}")
    print(f"  Summary: {summary_path}")
    print()

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
