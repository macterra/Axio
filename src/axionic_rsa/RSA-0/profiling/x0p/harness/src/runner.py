"""
X-0P Main Profiling Runner

Executes the full profiling pipeline per instructions §11:
1. Pre-flight calibration
2. Condition A
3. Baselines
4. Conditions B–E
5. Replay validation
6. Generate report

If Condition A fails inhabitation floor: abort.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict

from kernel.src.artifacts import InternalState
from kernel.src.constitution import Constitution

from profiling.x0p.harness.src.baselines import (
    BaselineRunResult,
    run_always_admit,
    run_always_refuse,
)
from profiling.x0p.harness.src.cycle_runner import (
    ConditionRunResult,
    run_condition,
)
from profiling.x0p.harness.src.generator import (
    generate_condition_A,
    generate_condition_B,
    generate_condition_C,
    generate_condition_D,
    generate_condition_E,
)
from profiling.x0p.harness.src.generator_common import ConditionManifest
from profiling.x0p.harness.src.preflight import (
    PreflightResult,
    build_session_metadata,
    run_preflight,
)
from profiling.x0p.harness.src.report import generate_report, write_report
from replay.x0p.verifier import (
    ReplayVerificationResult,
    verify_condition_replay,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SEEDS = {
    "A": 42,
    "B": 43,
    "C": 44,
    "D": 45,
    "E": 46,
}

DEFAULT_N_CYCLES = 100


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_profiling(
    repo_root: Path,
    n_cycles: int = DEFAULT_N_CYCLES,
    seeds: Dict[str, int] | None = None,
    output_dir: Path | None = None,
) -> Dict[str, Any]:
    """Execute the full X-0P profiling pipeline.

    Returns the final report dict.
    """
    seeds = seeds or DEFAULT_SEEDS
    run_id = str(uuid.uuid4())

    if output_dir is None:
        output_dir = repo_root / "logs" / "x0p"
    output_dir.mkdir(parents=True, exist_ok=True)

    constitution_path = (
        repo_root / "artifacts" / "phase-x" / "constitution"
        / "rsa_constitution.v0.1.1.yaml"
    )
    schema_path = (
        repo_root / "artifacts" / "phase-x" / "constitution"
        / "rsa_constitution.v0.1.1.schema.json"
    )

    corpus_path = (
        repo_root / "profiling" / "x0p" / "conditions" / "corpus_B.txt"
    )

    # ==================================================================
    # Step 1: Pre-flight calibration
    # ==================================================================
    print("[X-0P] Step 1: Pre-flight calibration...")

    generators = {
        "A": (generate_condition_A, seeds["A"], {"n_cycles": n_cycles}),
        "B": (generate_condition_B, seeds["B"], {"n_cycles": n_cycles, "corpus_path": corpus_path}),
        "C": (generate_condition_C, seeds["C"], {"n_cycles": n_cycles}),
        "D": (generate_condition_D, seeds["D"], {"n_cycles": n_cycles}),
        "E": (generate_condition_E, seeds["E"], {"n_cycles": n_cycles}),
    }

    preflight = run_preflight(
        repo_root=repo_root,
        constitution_path=constitution_path,
        schema_path=schema_path,
        generators=generators,
    )

    if not preflight.passed:
        _write_abort(output_dir, run_id, "Pre-flight failed", preflight.to_dict())
        raise RuntimeError(f"Pre-flight failed: {preflight.to_dict()}")

    # Build session metadata
    generator_config = {
        "seeds": seeds,
        "n_cycles": n_cycles,
        "corpus_path": str(corpus_path),
    }
    session_meta = build_session_metadata(
        repo_root=repo_root,
        constitution_path=constitution_path,
        preflight=preflight,
        generator_config=generator_config,
        run_id=run_id,
    )

    # Write session metadata
    with open(output_dir / "session_metadata.json", "w") as f:
        json.dump(session_meta, f, indent=2, sort_keys=True)

    print(f"[X-0P] Pre-flight passed. Run ID: {run_id}")

    # Load constitution
    constitution = Constitution(str(constitution_path))

    # ==================================================================
    # Step 2: Condition A
    # ==================================================================
    print("[X-0P] Step 2: Running Condition A (structured commands)...")
    manifest_A = generate_condition_A(seed=seeds["A"], n_cycles=n_cycles)
    result_A = run_condition(manifest_A, constitution, repo_root)

    _write_condition_log(output_dir, "condition_A.json", result_A)

    # Check inhabitation floor (per instructions §8)
    action_count_A = sum(
        1 for cr in result_A.cycle_results if cr.decision_type == "ACTION"
    )
    if action_count_A == 0:
        _write_abort(output_dir, run_id, "Condition A inhabitation floor failed: 0 ACTIONs")
        raise RuntimeError("Condition A action rate equals Always-Refuse baseline (0 ACTIONs). Aborting.")

    print(f"[X-0P] Condition A complete: {action_count_A}/{len(result_A.cycle_results)} ACTION")

    # ==================================================================
    # Step 3: Baselines
    # ==================================================================
    print("[X-0P] Step 3: Running baselines...")

    # Generate all manifests
    manifests = {
        "A": manifest_A,
        "B": generate_condition_B(seed=seeds["B"], n_cycles=n_cycles, corpus_path=corpus_path),
        "C": generate_condition_C(seed=seeds["C"], n_cycles=n_cycles),
        "D": generate_condition_D(seed=seeds["D"], n_cycles=n_cycles),
        "E": generate_condition_E(seed=seeds["E"], n_cycles=n_cycles),
    }

    baseline_results: Dict[str, Dict[str, BaselineRunResult]] = {}
    for condition, manifest in manifests.items():
        baseline_results[condition] = {
            "always_refuse": run_always_refuse(manifest),
            "always_admit": run_always_admit(manifest),
        }

    _write_condition_log(output_dir, "baseline_refuse.json", {
        c: bl["always_refuse"].to_dict() for c, bl in baseline_results.items()
    })
    _write_condition_log(output_dir, "baseline_admit.json", {
        c: bl["always_admit"].to_dict() for c, bl in baseline_results.items()
    })

    print("[X-0P] Baselines complete.")

    # ==================================================================
    # Step 4: Conditions B–E
    # ==================================================================
    condition_results: Dict[str, ConditionRunResult] = {"A": result_A}

    for label in ["B", "C", "D", "E"]:
        print(f"[X-0P] Step 4: Running Condition {label}...")
        result = run_condition(manifests[label], constitution, repo_root)
        condition_results[label] = result
        _write_condition_log(output_dir, f"condition_{label}.json", result)

        action_count = sum(
            1 for cr in result.cycle_results if cr.decision_type == "ACTION"
        )
        print(f"[X-0P] Condition {label} complete: {action_count}/{len(result.cycle_results)} ACTION")

    # ==================================================================
    # Step 5: Replay validation
    # ==================================================================
    print("[X-0P] Step 5: Replay validation...")
    replay_results: Dict[str, ReplayVerificationResult] = {}

    for label in ["A", "B", "C", "D", "E"]:
        rv = verify_condition_replay(
            manifest=manifests[label],
            original_results=condition_results[label].cycle_results,
            constitution_path=constitution_path,
            repo_root=repo_root,
            expected_constitution_hash=constitution.sha256,
        )
        replay_results[label] = rv

        status = "PASS" if rv.passed else f"FAIL ({rv.n_divergences} divergences)"
        print(f"[X-0P] Replay {label}: {status}")

    # ==================================================================
    # Step 6: Generate report
    # ==================================================================
    print("[X-0P] Step 6: Generating report...")

    report = generate_report(
        condition_results=condition_results,
        baseline_results=baseline_results,
        replay_results=replay_results,
        constitution_hash=constitution.sha256,
        calibration_hash=session_meta.get("calibration_hash", ""),
        session_metadata=session_meta,
    )

    report_path = repo_root / "profiling" / "x0p" / "reports" / "x0p_report.json"
    write_report(report, report_path)

    # Also write to logs
    write_report(report, output_dir / "x0p_report.json")

    print(f"[X-0P] Report written to {report_path}")
    print("[X-0P] Profiling complete.")

    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_condition_log(output_dir: Path, filename: str, data) -> None:
    """Write a condition log file."""
    path = output_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        if hasattr(data, "to_dict"):
            json.dump(data.to_dict(), f, indent=2, sort_keys=True)
        else:
            json.dump(data, f, indent=2, sort_keys=True)


def _write_abort(output_dir: Path, run_id: str, reason: str, detail=None) -> None:
    """Write ABORTED.json per BG18."""
    abort = {
        "run_id": run_id,
        "aborted": True,
        "reason": reason,
        "detail": detail,
    }
    path = output_dir / "ABORTED.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(abort, f, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    repo = Path(__file__).resolve().parent.parent.parent.parent
    try:
        report = run_profiling(repo)
        # Check for failures per instructions §8
        replay_ok = report.get("replay_verification", {}).get("all_passed", False)
        if not replay_ok:
            print("[X-0P] WARNING: Replay verification FAILED")
            sys.exit(1)
    except RuntimeError as e:
        print(f"[X-0P] ABORTED: {e}")
        sys.exit(1)
