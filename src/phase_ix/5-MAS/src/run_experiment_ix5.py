#!/usr/bin/env python3
"""
IX-5 MAS Experiment — Canonical Frozen Entrypoint.

Per preregistration §8.1: runs conditions A–F serially,
computes per-condition digests, and aggregates into experiment digest.

Usage:
    python run_experiment_ix5.py [--conditions A,B,C,D,E,F] [--output results.json]
"""

import argparse
import importlib
import json
import os
import sys
import types
from datetime import datetime, timezone

# ─── 3-phase import setup (per IX-4 pattern) ───────────────────

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_MAS_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, ".."))
_CUD_ROOT = os.path.normpath(os.path.join(_MAS_ROOT, "..", "2-CUD"))

if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_cud_agent_model = importlib.import_module("src.agent_model")
_cud_world_state = importlib.import_module("src.world_state")
_cud_authority_store = importlib.import_module("src.authority_store")
_cud_admissibility = importlib.import_module("src.admissibility")

_mas_src_dir = os.path.join(_MAS_ROOT, "src")
_mas_src = types.ModuleType("src")
_mas_src.__path__ = [_mas_src_dir]
_mas_src.__file__ = os.path.join(_mas_src_dir, "__init__.py")
_mas_src.__package__ = "src"
sys.modules["src"] = _mas_src

from src.mas_harness import (
    run_condition,
    compute_condition_digest,
    compute_experiment_digest,
    CONDITION_BUILDERS,
)


ALL_CONDITIONS = list("ABCDEF")


def run_experiment(
    conditions: list[str] | None = None,
    output_path: str | None = None,
    verbose: bool = True,
) -> dict:
    """Run the IX-5 MAS experiment.

    Args:
        conditions: List of condition IDs to run (default: all A–F).
        output_path: Path to write JSON results (default: auto-generated).
        verbose: Print progress to stderr.

    Returns:
        Full experiment result dict.
    """
    conditions = conditions or ALL_CONDITIONS

    if verbose:
        print(f"IX-5 MAS Experiment — {len(conditions)} conditions", file=sys.stderr)
        print(f"Conditions: {', '.join(conditions)}", file=sys.stderr)
        print("─" * 60, file=sys.stderr)

    condition_results: dict[str, dict] = {}
    condition_digests: dict[str, str] = {}

    for cond_id in conditions:
        if cond_id not in CONDITION_BUILDERS:
            raise ValueError(f"Unknown condition: {cond_id}")

        if verbose:
            print(f"\n▶ Running Condition {cond_id}...", file=sys.stderr)

        result = run_condition(cond_id)
        digest = compute_condition_digest(result)

        condition_results[cond_id] = result
        condition_digests[cond_id] = digest

        epochs_run = len(result["epochs"])
        terminal = result["terminal_classification"] or "MAX_EPOCHS"
        verdict = result["condition_result"]

        if verbose:
            print(
                f"  ✓ {cond_id}: {epochs_run} epochs | "
                f"terminal={terminal} | result={verdict}",
                file=sys.stderr,
            )
            # Key metrics
            am = result["aggregate_metrics"]
            print(
                f"    progress={am['epoch_progress_rate_K_INST']:.4f} "
                f"refusal={am['refusal_rate']:.4f} "
                f"overlap={am['write_overlap_rate_K_INST']:.4f}",
                file=sys.stderr,
            )
            if am.get("domination_detected"):
                print(
                    f"    ⚠ DOMINATION_DETECTED: {am['domination_index']}",
                    file=sys.stderr,
                )
            if am.get("zombie_write_count", 0) > 0:
                print(
                    f"    🧟 zombie_writes={am['zombie_write_count']} "
                    f"rate={am['zombie_write_rate']:.4f}",
                    file=sys.stderr,
                )

    # Compute experiment digest
    experiment_digest = None
    if set(conditions) == set(ALL_CONDITIONS):
        experiment_digest = compute_experiment_digest(condition_digests)

    # Assemble experiment record
    experiment = {
        "experiment_id": "IX-5-MAS",
        "version": "v0.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conditions_run": conditions,
        "condition_results": condition_results,
        "condition_digests": condition_digests,
        "experiment_digest": experiment_digest,
        "summary": {
            cond_id: {
                "condition_result": r["condition_result"],
                "terminal_classification": r["terminal_classification"],
                "epochs_run": len(r["epochs"]),
                "ix5_fail_tokens": r["ix5_fail_tokens"],
            }
            for cond_id, r in condition_results.items()
        },
    }

    # Write output
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            _SCRIPT_DIR, "..", "results",
            f"ix5_mas_results_{ts}.json",
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(experiment, f, indent=2, default=str)

    if verbose:
        print(f"\n{'─' * 60}", file=sys.stderr)
        print(f"Results written to: {output_path}", file=sys.stderr)
        if experiment_digest:
            print(f"Experiment digest: {experiment_digest}", file=sys.stderr)
        # Summary table
        print("\n  Condition  Epochs  Terminal                     Result", file=sys.stderr)
        print("  ─────────  ──────  ───────────────────────────  ──────", file=sys.stderr)
        for cond_id in conditions:
            s = experiment["summary"][cond_id]
            print(
                f"  {cond_id:>9}  {s['epochs_run']:>6}  "
                f"{(s['terminal_classification'] or 'MAX_EPOCHS'):<27}  "
                f"{s['condition_result']}",
                file=sys.stderr,
            )

    return experiment


def main():
    parser = argparse.ArgumentParser(description="IX-5 MAS Experiment")
    parser.add_argument(
        "--conditions", type=str, default=None,
        help="Comma-separated condition IDs (default: A,B,C,D,E,F)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress progress output",
    )
    args = parser.parse_args()

    conditions = args.conditions.split(",") if args.conditions else None

    run_experiment(
        conditions=conditions,
        output_path=args.output,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
