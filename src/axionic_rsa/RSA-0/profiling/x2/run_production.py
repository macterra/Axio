#!/usr/bin/env python3
"""
X-2 Production Run

Executes the full X-2 treaty delegation lifecycle:
  - 3 normal pre-delegation cycles
  - Lawful delegation (2 scenarios: ReadLocal + Notify via pre-populated grants)
  - Lawful revocation (1 scenario)
  - 11 adversarial grant scenarios (all rejected at correct gates)
  - 4 adversarial delegation scenarios (all rejected)
  - Expiry lifecycle (grant → use → expire → reject)
  - Replay verification

Outputs:
  - results/x2_session.json (full structured result)
  - results/x2_report.md   (human-readable report)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent  # profiling/x2/
RSA0_ROOT = SCRIPT_DIR.parent.parent         # RSA-0/
sys.path.insert(0, str(RSA0_ROOT))

from profiling.x2.harness.src.runner_x2 import X2Runner, X2SessionConfig
from profiling.x2.harness.src.report_x2 import generate_report


def main() -> None:
    constitution_path = str(
        RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.3.yaml"
    )
    schema_path = str(
        RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.3.schema.json"
    )
    schema_path_obj = Path(schema_path)
    if not schema_path_obj.exists():
        schema_path = None

    config = X2SessionConfig(
        repo_root=RSA0_ROOT,
        constitution_path=constitution_path,
        schema_path=schema_path,
        base_timestamp="2026-02-12T12:00:00Z",
        normal_cycles_pre=3,
        normal_cycles_post=2,
        adversarial_grants=True,
        adversarial_delegation=True,
        expiry_test=True,
        verbose=True,
    )

    print(f"\n{'='*70}")
    print(f"  RSA X-2 PRODUCTION RUN")
    print(f"  Treaty-Constrained Delegation")
    print(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"{'='*70}\n")

    runner = X2Runner(config)
    result = runner.run()

    # --- Save results ---
    results_dir = RSA0_ROOT / "profiling" / "x2" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = results_dir / "x2_session.json"
    json_path.write_text(json.dumps(result.to_dict(), indent=2))
    print(f"\n  Session JSON → {json_path}")

    # Report
    report_md = generate_report(result)
    report_path = results_dir / "x2_report.md"
    report_path.write_text(report_md)
    print(f"  Report MD   → {report_path}")

    # --- Summary ---
    print(f"\n{'='*70}")
    print(f"  PRODUCTION RUN COMPLETE")
    print(f"{'='*70}")
    print(f"  Total cycles:           {result.total_cycles}")
    print(f"  Decision types:         {result.decision_type_counts}")
    print(f"  Grants admitted:        {result.total_grants_admitted}")
    print(f"  Grants rejected:        {result.total_grants_rejected}")
    print(f"  Revocations admitted:   {result.total_revocations_admitted}")
    print(f"  Revocations rejected:   {result.total_revocations_rejected}")
    print(f"  Delegated warrants:     {result.total_delegated_warrants}")
    print(f"  Delegated rejections:   {result.total_delegated_rejections}")
    print(f"  Expiry confirmed:       {result.expiry_confirmed}")
    print(f"  Replay verified:        {result.replay_verified}")
    print(f"  Constitution hash:      {result.constitution_hash[:32]}...")
    print()

    # Adversarial summary
    grant_correct = sum(1 for r in result.grant_rejection_results if r.get("correct"))
    deleg_correct = sum(1 for r in result.delegation_rejection_results if r.get("correct"))
    print(f"  Grant rejections:       {grant_correct}/{len(result.grant_rejection_results)} correct")
    print(f"  Delegation rejections:  {deleg_correct}/{len(result.delegation_rejection_results)} correct")
    print()

    # Exit code
    if result.aborted:
        print("  [ABORTED]")
        sys.exit(1)
    if not result.total_delegated_warrants:
        print("  [WARN] No delegated warrants — closure criteria NOT met")
        sys.exit(2)
    if not result.replay_verified:
        print("  [WARN] Replay divergence detected")
        sys.exit(3)

    # Check all adversarial correct
    all_correct = (
        all(r.get("correct") for r in result.grant_rejection_results)
        and all(r.get("correct") for r in result.delegation_rejection_results)
    )
    if not all_correct:
        print("  [WARN] Some adversarial rejections did not match — check report")
        sys.exit(4)

    print("  [OK] All closure criteria met")
    sys.exit(0)


if __name__ == "__main__":
    main()
