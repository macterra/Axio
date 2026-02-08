#!/usr/bin/env python3
"""
Phase IX-3 GS — Official Experiment Execution

Runs all 10 conditions per the frozen preregistration,
evaluates against §6.1 PASS predicates, produces execution log.

Preregistration hash: 19b53a61a67b5bb7dd73b8eaa8e1a857fe4ca46a7b40188b1a42944a7c1e53c5
Commitment timestamp: 2026-02-07T00:00:00Z
Commit ID: d565d96e29174a55c19400a6c261d0dec7d49972
"""

import json
import os
import sys
import importlib

# ─── Path setup ─────────────────────────────────────────────────

_GS_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__)))
_CUD_ROOT = os.path.normpath(os.path.join(_GS_ROOT, '..', '2-CUD'))

# Phase 1: Import CUD modules first
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

# Force CUD's src into sys.modules
importlib.import_module("src.agent_model")
importlib.import_module("src.world_state")
importlib.import_module("src.authority_store")
importlib.import_module("src.admissibility")
importlib.import_module("src.deadlock_classifier")
importlib.import_module("src.epoch_controller")

# Phase 2: Redirect src package __path__ to 3-GS/src/
import types
_gs_src_dir = os.path.join(_GS_ROOT, 'src')
_gs_src = types.ModuleType("src")
_gs_src.__path__ = [_gs_src_dir]
_gs_src.__file__ = os.path.join(_gs_src_dir, '__init__.py')
_gs_src.__package__ = "src"
sys.modules["src"] = _gs_src

# Phase 3: Import GS modules
_gs_harness = importlib.import_module("src.gs_harness")
run_all_conditions = _gs_harness.run_all_conditions
FIXED_CLOCK = _gs_harness.FIXED_CLOCK

RESULTS_DIR = os.path.join(_GS_ROOT, "results")


def main():
    print("=" * 72)
    print("Phase IX-3: Governance Styles Under Honest Failure (GS)")
    print("Official Experiment Execution")
    print("=" * 72)
    print()

    # Run all 10 conditions
    execution_log = run_all_conditions(
        results_dir=RESULTS_DIR,
        timestamp=FIXED_CLOCK,
    )

    # Report per-condition results
    print(f"{'Cond':<6} {'Terminal':<20} {'Style':<25} {'Result':<6}")
    print("-" * 72)
    for cond in execution_log.conditions:
        tc = cond.terminal_classification or "None"
        style = cond.governance_style_label or "—"
        result = cond.condition_result
        marker = "✓" if result == "PASS" else "✗"
        fail_tokens = ", ".join(cond.ix3_fail_tokens) if cond.ix3_fail_tokens else ""
        line = f"{cond.condition:<6} {tc:<20} {style:<25} {marker} {result}"
        if fail_tokens:
            line += f"  [{fail_tokens}]"
        print(line)

    print("-" * 72)
    print()

    # Aggregate
    print(f"Aggregate Result: {execution_log.aggregate_result}")
    print()

    # Replay verification (per §8.2 Replay Rule)
    print("Determinism Check:")
    log2 = run_all_conditions(timestamp=FIXED_CLOCK)
    replay_ok = True
    for c1, c2 in zip(execution_log.conditions, log2.conditions):
        d1 = c1.to_dict()
        d2 = c2.to_dict()
        # Exclude timestamps from comparison (per replay rule)
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
