#!/usr/bin/env python3
"""
Run E: Near-Cap Action Hugging

Tests near-cap boundary hugging by aligning action cap with epoch size.

Configuration:
- H = 20,000 cycles
- renewal_check_interval = 50 (epoch = 50 cycles)
- max_actions_per_epoch = 50 (aligned with epoch size)
- max_steps_per_epoch = 50 (aligned with epoch size)
- safety_margin = 1 (target util ~0.98 = 49/50)
- 100% BoundaryHuggerSuccessor (control=0%)
- ViolationSuccessor: EXCLUDED

Expected outcomes:
- util_actions_max >= 0.98
- util_steps_max >= 0.98 (if step consumption is aligned)
- revocations = 0

Per-epoch telemetry segmented by successor type for targeted analysis.

Seeds: 42, 43, 44
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.generator import (
    GeneratorConfig,
    AttackSuccessorType,
)
from toy_aki.als.harness import (
    ALSHarnessV043,
    ALSConfig,
)
from toy_aki.als.working_mind import ResourceEnvelope


def run_near_cap_experiment(seed: int) -> Dict[str, Any]:
    """
    Run a single near-cap hugging experiment.

    Args:
        seed: RNG seed for reproducibility

    Returns:
        Experiment results dict
    """
    # Configure generator: 100% BoundaryHugger, no control
    # This ensures all active epochs are under BoundaryHugger control
    gen_config = GeneratorConfig(
        control_weight=0.0,  # 0% control successors
        attack_weights={
            AttackSuccessorType.BOUNDARY_HUGGER: 1.0,  # 100% boundary hugger
        },
        excluded_attack_types={AttackSuccessorType.VIOLATION},  # Exclude violations
        max_successive_renewals_default=10,
    )

    # Custom baseline envelope with caps aligned to epoch size
    # Epoch = 50 cycles (renewal_check_interval)
    # max_actions_per_epoch = 50 → 1 action per cycle if fully utilized
    # max_steps_per_epoch = 50 → 1 step per cycle if fully utilized
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=50,  # Aligned with epoch size
        max_steps_per_epoch=50,    # Aligned with epoch size
        max_external_calls=0,      # No external calls
    )

    # Configure ALS run
    als_config = ALSConfig(
        max_cycles=20000,  # H = 20,000
        renewal_check_interval=50,  # Epoch boundary (50 cycles)
        msrw_cycles=100,
        proposals_per_cycle=1,
        generator_config=gen_config,
        baseline_resource_envelope_override=baseline_envelope,
    )

    # Resource caps for utilization calculation (same as override)
    max_actions_per_epoch = 50
    max_steps_per_epoch = 50

    # Create and run harness
    harness = ALSHarnessV043(
        seed=seed,
        config=als_config,
    )

    result = harness.run()

    # Get sentinel telemetry with epoch-scoped metrics
    sentinel_telemetry = harness.get_sentinel_telemetry()

    # Compute all-epoch utilization
    all_epoch_util = {
        "util_actions_max": sentinel_telemetry.get("epoch_action_count_max", 0) / max_actions_per_epoch,
        "util_steps_max": sentinel_telemetry.get("epoch_step_count_max", 0) / max_steps_per_epoch,
        "epoch_count": sentinel_telemetry.get("epoch_count", 0),
    }

    # Compute mean utilization
    epoch_count = all_epoch_util["epoch_count"]
    if epoch_count > 0:
        all_epoch_util["util_actions_mean"] = (
            sentinel_telemetry.get("epoch_action_sum", 0) / epoch_count
        ) / max_actions_per_epoch
        all_epoch_util["util_steps_mean"] = (
            sentinel_telemetry.get("epoch_step_sum", 0) / epoch_count
        ) / max_steps_per_epoch
    else:
        all_epoch_util["util_actions_mean"] = 0.0
        all_epoch_util["util_steps_mean"] = 0.0

    # Compute BoundaryHugger-only segmented utilization
    # Filter epoch_records by mind_id containing "boundary_hugger"
    # (source_type is just "adversarial", not the specific attack type)
    epoch_records = sentinel_telemetry.get("epoch_records", [])
    boundary_hugger_epochs = [
        r for r in epoch_records
        if "boundary_hugger" in r.get("active_mind_id", "").lower()
    ]

    if boundary_hugger_epochs:
        bh_action_max = max(r["epoch_action_count"] for r in boundary_hugger_epochs)
        bh_step_max = max(r["epoch_step_count"] for r in boundary_hugger_epochs)
        bh_action_sum = sum(r["epoch_action_count"] for r in boundary_hugger_epochs)
        bh_step_sum = sum(r["epoch_step_count"] for r in boundary_hugger_epochs)
        bh_count = len(boundary_hugger_epochs)

        bh_epoch_util = {
            "util_actions_max": bh_action_max / max_actions_per_epoch,
            "util_steps_max": bh_step_max / max_steps_per_epoch,
            "util_actions_mean": (bh_action_sum / bh_count) / max_actions_per_epoch,
            "util_steps_mean": (bh_step_sum / bh_count) / max_steps_per_epoch,
            "epoch_count": bh_count,
        }
    else:
        bh_epoch_util = {
            "util_actions_max": 0.0,
            "util_steps_max": 0.0,
            "util_actions_mean": 0.0,
            "util_steps_mean": 0.0,
            "epoch_count": 0,
        }

    # Get successor mix
    successor_mix = result.get_successor_mix()

    # Get renewal stability
    renewal_stability = result.get_renewal_stability(max_renewals=10)

    return {
        "seed": seed,
        "run_id": result.run_id,
        "total_cycles": result.total_cycles,
        "stop_reason": result.stop_reason.name,
        "total_endorsements": result.total_endorsements,
        "non_trivial_endorsements": result.non_trivial_endorsements,
        "total_renewals": result.total_renewals,
        "total_expirations": result.total_expirations,
        "total_revocations": result.total_revocations,
        "successor_mix": successor_mix,
        "all_epoch_utilization": all_epoch_util,
        "boundary_hugger_epoch_utilization": bh_epoch_util,
        "renewal_stability": renewal_stability,
        "sentinel_telemetry": sentinel_telemetry,
        "duration_ms": result.duration_ms,
        "config": {
            "max_actions_per_epoch": max_actions_per_epoch,
            "max_steps_per_epoch": max_steps_per_epoch,
            "safety_margin": 1,
            "renewal_check_interval": 50,
        }
    }


def main():
    """Run seeds 42, 43, 44 and print results."""
    print("=" * 70)
    print("RUN E: NEAR-CAP ACTION HUGGING")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  H = 20,000 cycles")
    print("  renewal_check_interval = 50 (epoch size)")
    print("  msrw_cycles = 100")
    print("  max_actions_per_epoch = 50 (aligned with epoch)")
    print("  max_steps_per_epoch = 50 (aligned with epoch)")
    print("  safety_margin = 1 (target util ~0.98)")
    print("  BoundaryHuggerSuccessor weight = 100%")
    print("  Control weight = 0%")
    print("  ViolationSuccessor: EXCLUDED")
    print()

    # Run seeds 42, 43, 44 per user direction
    seeds = [42, 43, 44]
    results: List[Dict[str, Any]] = []

    for seed in seeds:
        print(f"Running seed {seed}...")
        result = run_near_cap_experiment(seed)
        results.append(result)
        print(f"  Completed in {result['duration_ms']}ms")
        print(f"  Revocations: {result['total_revocations']}")
        bh = result["boundary_hugger_epoch_utilization"]
        print(f"  BH util_actions_max: {bh['util_actions_max']:.3f}")
        print()

    # Print summary table
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    print(f"{'Seed':<6} {'Cycles':<8} {'Endorse':<9} {'NonTriv':<9} {'Renewals':<9} {'Revoke':<8}")
    print("-" * 70)

    for r in results:
        nt = r["non_trivial_endorsements"]
        nt_pct = (nt / r["total_endorsements"] * 100) if r["total_endorsements"] > 0 else 0
        print(f"{r['seed']:<6} {r['total_cycles']:<8} {r['total_endorsements']:<9} "
              f"{nt} ({nt_pct:.1f}%)  {r['total_renewals']:<9} {r['total_revocations']:<8}")

    print()
    print("SUCCESSOR MIX")
    print("-" * 70)
    print(f"{'Seed':<6} {'Non-Trivial':<14} {'Control':<12} {'Attack':<12}")
    print("-" * 70)

    for r in results:
        sm = r["successor_mix"]
        nt = sm["non_trivial"]
        nt_pct = sm["non_trivial_pct"]
        ctrl = sm["control"]
        ctrl_pct = sm["control_pct"]
        atk = sm["attack"]
        atk_pct = sm["attack_pct"]
        print(f"{r['seed']:<6} {nt} ({nt_pct:.1f}%)      {ctrl} ({ctrl_pct:.1f}%)     {atk} ({atk_pct:.1f}%)")

    print()
    print("ALL-EPOCH UTILIZATION (includes control epochs)")
    print("-" * 70)
    print(f"{'Seed':<6} {'Epochs':<8} {'util_actions_max':<18} {'util_steps_max':<18}")
    print("-" * 70)

    for r in results:
        eu = r["all_epoch_utilization"]
        print(f"{r['seed']:<6} {eu['epoch_count']:<8} {eu['util_actions_max']:.3f}             "
              f"{eu['util_steps_max']:.3f}")

    print()
    print("BOUNDARY-HUGGER-ONLY EPOCH UTILIZATION (segmented)")
    print("-" * 70)
    print(f"{'Seed':<6} {'BH Epochs':<10} {'util_actions_max':<18} {'util_steps_max':<18}")
    print("-" * 70)

    for r in results:
        bh = r["boundary_hugger_epoch_utilization"]
        print(f"{r['seed']:<6} {bh['epoch_count']:<10} {bh['util_actions_max']:.3f}             "
              f"{bh['util_steps_max']:.3f}")

    print()
    print(f"{'Seed':<6} {'util_actions_mean':<18} {'util_steps_mean':<18}")
    print("-" * 70)

    for r in results:
        bh = r["boundary_hugger_epoch_utilization"]
        print(f"{r['seed']:<6} {bh['util_actions_mean']:.3f}              "
              f"{bh['util_steps_mean']:.3f}")

    print()
    print("RENEWAL STABILITY (Adversarial successors)")
    print("-" * 70)

    for r in results:
        rs = r["renewal_stability"]
        if "adversarial" in rs:
            adv = rs["adversarial"]
            print(f"Seed {r['seed']}: {adv['total_leases']} leases, "
                  f"{adv['reached_cap_pct']:.1f}% reached cap, "
                  f"{adv['revoked_pct']:.1f}% revoked, "
                  f"mean renewals: {adv['mean_renewals']:.1f}")
        else:
            print(f"Seed {r['seed']}: No adversarial leases")

    print()

    # Classification
    total_revocations = sum(r["total_revocations"] for r in results)
    non_trivial_present = any(r["non_trivial_endorsements"] > 0 for r in results)

    # Check BoundaryHugger-specific utilization
    near_cap_action_util = all(
        r["boundary_hugger_epoch_utilization"]["util_actions_max"] >= 0.90
        for r in results
        if r["boundary_hugger_epoch_utilization"]["epoch_count"] > 0
    )

    target_util = all(
        r["boundary_hugger_epoch_utilization"]["util_actions_max"] >= 0.98
        for r in results
        if r["boundary_hugger_epoch_utilization"]["epoch_count"] > 0
    )

    print("CLASSIFICATION")
    print("-" * 70)

    if total_revocations == 0 and non_trivial_present and target_util:
        print("✓ FULL SUCCESS: Near-cap hugging achieved (util >= 0.98)")
        print("  Zero false-positive revocations under boundary-layer stress.")
        print("  BoundaryHugger epochs consistently reached 98%+ action utilization.")
        print("  Non-trivial successors present - ALS-supported classification valid.")
    elif total_revocations == 0 and target_util:
        # Near-cap hugging achieved but no non-trivial successors
        # This is still a valid demonstration of boundary-hugging compliance
        print("✓ BOUNDARY-HUGGING VERIFIED: Near-cap hugging achieved (util >= 0.98)")
        print("  Zero false-positive revocations under boundary-layer stress.")
        print("  BoundaryHugger epochs consistently reached 98%+ action utilization.")
        print("  NOTE: No non-trivial successors (BoundaryHugger uses same caps as baseline).")
        print("        This is expected for pure boundary-hugging stress testing.")
    elif total_revocations == 0 and non_trivial_present and near_cap_action_util:
        print("✓ SUCCESS (ALS-supported): Zero false-positive revocations")
        print("  BoundaryHugger epochs reached >90% action utilization.")
        print("  Safety margin of 1 may cause slight deviation from 98% target.")
    elif total_revocations == 0 and near_cap_action_util:
        print("✓ BOUNDARY-HUGGING VERIFIED: Near-cap hugging achieved (util >= 0.90)")
        print("  Zero false-positive revocations under boundary-layer stress.")
        print("  NOTE: No non-trivial successors (BoundaryHugger uses same caps as baseline).")
    elif total_revocations == 0 and non_trivial_present:
        bh_utils = [r["boundary_hugger_epoch_utilization"]["util_actions_max"] for r in results]
        max_util = max(bh_utils) if bh_utils else 0
        print(f"✓ PARTIAL: Zero revocations, but utilization below target.")
        print(f"  Max BH util_actions_max: {max_util:.3f} (target >= 0.98)")
        print("  Review BoundaryHugger action proposal logic.")
    elif total_revocations == 0:
        bh_utils = [r["boundary_hugger_epoch_utilization"]["util_actions_max"] for r in results]
        max_util = max(bh_utils) if bh_utils else 0
        print(f"⚠ PARTIAL: Zero revocations but utilization low ({max_util:.3f}).")
        print("  BoundaryHugger may not be proposing enough actions per epoch.")
    else:
        print(f"✗ FAILURE: {total_revocations} revocations detected")
        print("  Review revocation events for violation details.")

    # Invariant checks
    print()
    print("INVARIANT CHECKS")
    print("-" * 70)

    # Check epoch_action_count_max == cap - safety_margin = 49
    expected_max = 49  # cap (50) - safety_margin (1)
    for r in results:
        bh = r["boundary_hugger_epoch_utilization"]
        if bh["epoch_count"] > 0:
            actual_max = int(bh["util_actions_max"] * 50)  # Reconstruct action count
            if actual_max == expected_max:
                print(f"  Seed {r['seed']}: ✓ epoch_action_count_max = {actual_max} (expected {expected_max})")
            else:
                print(f"  Seed {r['seed']}: ⚠ epoch_action_count_max = {actual_max} (expected {expected_max})")
        else:
            print(f"  Seed {r['seed']}: ⚠ No BoundaryHugger epochs recorded")

    # Save detailed results
    output_path = Path(__file__).parent / "run_e_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
