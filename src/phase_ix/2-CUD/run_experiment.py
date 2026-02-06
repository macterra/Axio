#!/usr/bin/env python3
"""
Phase IX-2 CUD — Official Experiment Execution

Runs all 10 conditions per the frozen preregistration,
evaluates against §7 success criteria, produces execution log.

Preregistration hash: 6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473
Commitment timestamp: 2026-02-05T00:00:00Z
Commit ID: 694e9cc27fcbca766099df887cb804cf19e6aeee
"""

import json
import os
import sys

# Set up path
_CUD_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__)))
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

from src.cud_harness import run_all_conditions, evaluate_condition

RESULTS_DIR = os.path.join(_CUD_ROOT, "results")


def main():
    print("=" * 72)
    print("Phase IX-2: Coordination Under Deadlock (CUD)")
    print("Official Experiment Execution")
    print("=" * 72)
    print()

    # Run all 10 conditions
    execution_log = run_all_conditions(results_dir=RESULTS_DIR)

    # Report per-condition results
    print(f"{'Condition':<12} {'Terminal':<22} {'Kernel':<35} {'Result':<6}")
    print("-" * 72)
    for cond in execution_log.conditions:
        tc = cond.terminal_classification or "None"
        kc = cond.kernel_classification or "None"
        result = cond.experiment_result
        marker = "✓" if result == "PASS" else "✗"
        print(f"{cond.condition:<12} {tc:<22} {kc:<35} {marker} {result}")

    print("-" * 72)
    print()

    # Aggregate
    print(f"Aggregate Result: {execution_log.aggregate_result}")
    print()

    # Replay verification
    print("Determinism Check:")
    log2 = run_all_conditions()
    replay_ok = True
    for c1, c2 in zip(execution_log.conditions, log2.conditions):
        d1 = c1.to_dict()
        d2 = c2.to_dict()
        # Exclude timestamps from comparison (per §6.2 replay rule)
        d1.pop("timestamp", None)
        d2.pop("timestamp", None)
        if d1 != d2:
            print(f"  ✗ Condition {c1.condition}: replay mismatch!")
            replay_ok = False
        else:
            print(f"  ✓ Condition {c1.condition}: bit-perfect replay confirmed")

    print()
    if replay_ok:
        print("Replay Verification: PASS — all conditions deterministic")
    else:
        print("Replay Verification: FAIL — non-determinism detected")

    print()
    print(f"Results written to: {RESULTS_DIR}/")

    return 0 if "PASS" in execution_log.aggregate_result and replay_ok else 1


if __name__ == "__main__":
    sys.exit(main())
