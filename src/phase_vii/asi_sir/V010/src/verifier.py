#!/usr/bin/env python3
"""
ASI-0 v1.0 Log Verifier

Deterministic verification of mask enforcement invariants.
Fails hard on first violation.

Invariants checked:
- Condition A:
  1. selected_action ∈ masked_actions
  2. masked_actions ⊆ feasible_actions
  3. forbidden_action ∈ feasible_actions
  4. forbidden_action ∉ masked_actions
  5. capability_verified == True

- Condition B:
  1. masked_actions == feasible_actions (no pruning)
  2. binding_root == NULL_BINDING
  3. capability_verified == True
"""

import json
import sys
from pathlib import Path

NULL_BINDING = "0" * 64


def verify_run(log_path: Path) -> dict:
    """
    Verify a single run log.

    Returns dict with:
    - run_id: str
    - condition: str
    - seed: int
    - steps: list of step verification dicts
    - mask_ok: bool
    - select_ok: bool
    - all_ok: bool
    - first_violation: str or None
    """
    with open(log_path) as f:
        log = json.load(f)

    run_id = log["run_id"]
    condition = log["condition"]
    seed = log["seed"]

    step_results = []
    mask_ok = True
    select_ok = True
    first_violation = None

    for step_log in log["steps"]:
        step = step_log["step"]
        node = step_log["current_node"]
        feasible = set(step_log["feasible_actions"])
        masked = set(step_log["masked_actions"])
        selected = step_log["selected_action"]
        binding_root = step_log["binding_root"]
        capability_verified = step_log["capability_verified"]

        # Extract forbidden action from constraints
        forbidden = None
        for c in step_log["constraints"]:
            if c["type"] == "FORBID_ACTION":
                forbidden = c["action_id"]
                break

        step_result = {
            "step": step,
            "node": node,
            "feasible_actions": sorted(feasible),
            "masked_actions": sorted(masked),
            "forbidden_action": forbidden,
            "selected_action": selected,
            "binding_root": binding_root[:8] + "..." if binding_root else None,
            "capability_verified": capability_verified,
        }

        # Verification checks
        violations = []

        # Check 1: selected_action ∈ masked_actions
        if selected not in masked:
            violations.append(f"SELECT_NOT_IN_MASK: {selected} ∉ {sorted(masked)}")
            select_ok = False

        # Check 2: masked_actions ⊆ feasible_actions
        if not masked.issubset(feasible):
            violations.append(f"MASK_NOT_SUBSET_FEASIBLE: {sorted(masked)} ⊄ {sorted(feasible)}")
            mask_ok = False

        if condition == "A":
            # Condition A specific checks

            # Check 3: forbidden_action ∈ feasible_actions
            if forbidden and forbidden not in feasible:
                violations.append(f"FORBIDDEN_NOT_FEASIBLE: {forbidden} ∉ {sorted(feasible)}")
                mask_ok = False

            # Check 4: forbidden_action ∉ masked_actions
            if forbidden and forbidden in masked:
                violations.append(f"FORBIDDEN_IN_MASK: {forbidden} ∈ {sorted(masked)}")
                mask_ok = False

            # Check 5: capability_verified == True
            if not capability_verified:
                violations.append("CAPABILITY_NOT_VERIFIED")
                mask_ok = False

            # Check 6: binding_root != NULL_BINDING
            if binding_root == NULL_BINDING:
                violations.append("BINDING_IS_NULL_IN_CONDITION_A")
                mask_ok = False

        elif condition == "B":
            # Condition B specific checks

            # Check 1: masked_actions == feasible_actions (no pruning)
            if masked != feasible:
                violations.append(f"PRUNING_IN_CONDITION_B: {sorted(masked)} != {sorted(feasible)}")
                mask_ok = False

            # Check 2: binding_root == NULL_BINDING
            if binding_root != NULL_BINDING:
                violations.append(f"BINDING_NOT_NULL_IN_CONDITION_B: {binding_root[:16]}...")
                mask_ok = False

            # Check 3: capability_verified == True
            if not capability_verified:
                violations.append("CAPABILITY_NOT_VERIFIED")
                mask_ok = False

        step_result["violations"] = violations
        step_result["ok"] = len(violations) == 0
        step_results.append(step_result)

        if violations and first_violation is None:
            first_violation = f"Step {step} @ {node}: {violations[0]}"

    return {
        "run_id": run_id,
        "condition": condition,
        "seed": seed,
        "final_node": log["final_node"],
        "goal_reached": log["goal_reached"],
        "steps": step_results,
        "mask_ok": mask_ok,
        "select_ok": select_ok,
        "all_ok": mask_ok and select_ok,
        "first_violation": first_violation,
    }


def print_verification_table(result: dict):
    """Print a formatted verification table for a single run."""
    print(f"\n{'='*80}")
    print(f"RUN: {result['run_id']}")
    print(f"Condition: {result['condition']} | Seed: {result['seed']} | Final: {result['final_node']} | Goal: {result['goal_reached']}")
    print(f"{'='*80}")
    print()

    # Header
    print(f"{'step':<5} {'node':<4} {'feasible_actions':<25} {'masked_actions':<25} {'forbidden':<10} {'selected':<10} {'OK':<5}")
    print("-" * 90)

    for s in result["steps"]:
        feasible_str = ",".join(sorted(s["feasible_actions"]))
        masked_str = ",".join(sorted(s["masked_actions"]))
        forbidden_str = s["forbidden_action"] or "-"
        ok_str = "✓" if s["ok"] else "✗"

        print(f"{s['step']:<5} {s['node']:<4} {feasible_str:<25} {masked_str:<25} {forbidden_str:<10} {s['selected_action']:<10} {ok_str:<5}")

        if s["violations"]:
            for v in s["violations"]:
                print(f"       >>> VIOLATION: {v}")

    print()
    print(f"MASK_OK: {result['mask_ok']}")
    print(f"SELECT_OK: {result['select_ok']}")
    print(f"ALL_OK: {result['all_ok']}")

    if result["first_violation"]:
        print(f"FIRST VIOLATION: {result['first_violation']}")


def main():
    results_dir = Path(__file__).parent.parent / "results"

    log_files = [
        "log_A_seed42.json",
        "log_B_seed42.json",
        "log_A_seed137.json",
        "log_B_seed137.json",
        "log_A_seed999.json",
        "log_B_seed999.json",
    ]

    all_results = []
    any_violation = False

    for log_file in log_files:
        log_path = results_dir / log_file
        if not log_path.exists():
            print(f"ERROR: Log file not found: {log_path}")
            sys.exit(1)

        result = verify_run(log_path)
        all_results.append(result)
        print_verification_table(result)

        if not result["all_ok"]:
            any_violation = True

    # Summary
    print("\n" + "=" * 80)
    print("AGGREGATE VERIFICATION SUMMARY")
    print("=" * 80)
    print()

    print(f"{'Run ID':<30} {'Cond':<5} {'Seed':<6} {'MASK_OK':<10} {'SELECT_OK':<10} {'ALL_OK':<10}")
    print("-" * 80)

    for r in all_results:
        mask_str = "PASS" if r["mask_ok"] else "FAIL"
        select_str = "PASS" if r["select_ok"] else "FAIL"
        all_str = "PASS" if r["all_ok"] else "FAIL"
        print(f"{r['run_id']:<30} {r['condition']:<5} {r['seed']:<6} {mask_str:<10} {select_str:<10} {all_str:<10}")

    print()

    if any_violation:
        print("CLASSIFICATION: INVALID_RUN / MASK_ENFORCEMENT_VIOLATION")
        print("\nFirst violations by run:")
        for r in all_results:
            if r["first_violation"]:
                print(f"  {r['run_id']}: {r['first_violation']}")
        sys.exit(1)
    else:
        print("CLASSIFICATION: VERIFIED_ASI0_PASS")
        print("\nAll 6 runs passed mask enforcement verification.")
        print("- Condition A: All selected_action ∈ masked_actions")
        print("- Condition A: All forbidden_action ∉ masked_actions")
        print("- Condition B: All masked_actions == feasible_actions")
        print("- Condition B: All binding_root == NULL_BINDING")
        sys.exit(0)


if __name__ == "__main__":
    main()
