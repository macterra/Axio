#!/usr/bin/env python3
"""
X-1 Production Run

Executes the full X-1 amendment lifecycle:
  - 5 pre-fork cycles
  - Trivial amendment proposal, cooling, adoption
  - 5 post-fork cycles
  - 7 adversarial scenarios (all rejected)
  - 3 chained lawful amendments
  - Replay verification

Outputs:
  - results/x1_session.json (full structured result)
  - results/x1_report.md   (human-readable report)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent  # profiling/x1/
RSA0_ROOT = SCRIPT_DIR.parent.parent         # RSA-0/
sys.path.insert(0, str(RSA0_ROOT))

from profiling.x1.harness.src.runner_x1 import X1Runner, X1SessionConfig
from profiling.x1.harness.src.report_x1 import generate_report


def main() -> None:
    constitution_path = str(
        RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.2.yaml"
    )
    schema_path = str(
        RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.2.schema.json"
    )

    config = X1SessionConfig(
        repo_root=RSA0_ROOT,
        constitution_path=constitution_path,
        schema_path=schema_path,
        base_timestamp="2026-02-12T12:00:00Z",
        normal_cycles_pre_amendment=5,
        cooling_cycles=2,
        normal_cycles_post_fork=5,
        adversarial_scenarios=True,
        chained_amendments=3,
        verbose=True,
    )

    print(f"\n{'='*70}")
    print(f"  RSA X-1 PRODUCTION RUN")
    print(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"{'='*70}\n")

    runner = X1Runner(config)
    result = runner.run()

    # --- Save results ---
    results_dir = RSA0_ROOT / "profiling" / "x1" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = results_dir / "x1_session.json"
    json_path.write_text(json.dumps(result.to_dict(), indent=2))
    print(f"\n  Session JSON → {json_path}")

    # Report
    report_md = generate_report(result)
    report_path = results_dir / "x1_report.md"
    report_path.write_text(report_md)
    print(f"  Report MD   → {report_path}")

    # --- Summary ---
    print(f"\n{'='*70}")
    print(f"  PRODUCTION RUN COMPLETE")
    print(f"{'='*70}")
    print(f"  Total cycles:       {result.total_cycles}")
    print(f"  Decision types:     {result.decision_type_counts}")
    print(f"  Adoptions:          {len(result.adoptions)}")
    print(f"  Rejections:         {len(result.rejections)}")
    print(f"  Transitions:        {len(result.constitution_transitions)}")
    print(f"  Replay verified:    {result.replay_verified}")
    print(f"  Aborted:            {result.aborted}")
    if result.replay_divergences:
        print(f"  Divergences:        {len(result.replay_divergences)}")
    print(f"  Initial hash:       {result.initial_constitution_hash[:32]}...")
    print(f"  Final hash:         {result.final_constitution_hash[:32]}...")
    print()

    # Exit code
    if result.aborted:
        sys.exit(1)
    if not result.adoptions:
        print("  [WARN] No adoptions — spec closure criteria NOT met")
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
