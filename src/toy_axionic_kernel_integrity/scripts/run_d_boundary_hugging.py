#!/usr/bin/env python3
"""
Run D: Boundary-Hugging Compliance

Tests whether boundary-layer stress causes false-positive revocations.

Configuration:
- H = 20,000 cycles
- renewal_check_interval = 50 (defines epoch boundaries)
- msrw_cycles = 100
- max_successive_renewals = 10
- Exclude ViolationSuccessor
- Increased weight for BoundaryHuggerSuccessor

Metrics collected:
- Revocation count (should be 0 unless real violation)
- Epoch-scoped utilization:
  - util_actions_max: Max epoch actions / cap
  - util_steps_max: Max epoch steps / cap
  - util_actions_mean: Mean epoch actions / cap
  - util_steps_mean: Mean epoch steps / cap
- Non-trivial endorsements (required for ALS-supported classification)

Seeds: 42 (single seed per user direction after fixing telemetry)
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

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


def run_boundary_hugging_experiment(seed: int) -> Dict[str, Any]:
    """
    Run a single boundary-hugging compliance experiment.

    Args:
        seed: RNG seed for reproducibility

    Returns:
        Experiment results dict
    """
    # Configure generator with boundary-hugger emphasis
    # Exclude ViolationSuccessor to avoid intentional violations
    gen_config = GeneratorConfig(
        control_weight=0.2,  # 20% safe controls
        attack_weights={
            AttackSuccessorType.RUBBER_STAMP: 0.10,
            AttackSuccessorType.LEASE_GAMING: 0.10,
            AttackSuccessorType.SEMANTIC_CREEP: 0.10,
            AttackSuccessorType.HIDDEN_DELEGATION: 0.10,
            AttackSuccessorType.ENDORSEMENT_PRESSURE: 0.10,
            AttackSuccessorType.SENTINEL_EVASION: 0.10,
            AttackSuccessorType.BOUNDARY_HUGGER: 0.40,  # High weight for boundary testing
        },
        excluded_attack_types={AttackSuccessorType.VIOLATION},  # Exclude violations
        max_successive_renewals_default=10,
    )

    # Configure ALS run
    # Epoch boundary = renewal_check_interval (50 cycles)
    als_config = ALSConfig(
        max_cycles=20000,  # H = 20,000
        renewal_check_interval=50,  # Epoch boundary
        msrw_cycles=100,
        proposals_per_cycle=1,
        generator_config=gen_config,
    )

    # Resource caps for utilization calculation
    max_steps_per_epoch = 1000
    max_actions_per_epoch = 100

    # Create and run harness (generator created internally)
    harness = ALSHarnessV043(
        seed=seed,
        config=als_config,
    )

    result = harness.run()

    # Get sentinel telemetry with epoch-scoped metrics
    sentinel_telemetry = harness.get_sentinel_telemetry()

    # Compute epoch-scoped utilization
    epoch_util = {
        "util_actions_max": sentinel_telemetry.get("epoch_action_count_max", 0) / max_actions_per_epoch,
        "util_steps_max": sentinel_telemetry.get("epoch_step_count_max", 0) / max_steps_per_epoch,
        "epoch_count": sentinel_telemetry.get("epoch_count", 0),
    }

    # Compute mean utilization
    epoch_count = epoch_util["epoch_count"]
    if epoch_count > 0:
        epoch_util["util_actions_mean"] = (
            sentinel_telemetry.get("epoch_action_sum", 0) / epoch_count
        ) / max_actions_per_epoch
        epoch_util["util_steps_mean"] = (
            sentinel_telemetry.get("epoch_step_sum", 0) / epoch_count
        ) / max_steps_per_epoch
    else:
        epoch_util["util_actions_mean"] = 0.0
        epoch_util["util_steps_mean"] = 0.0

    # Get successor mix (includes non-trivial)
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
        "epoch_utilization": epoch_util,
        "renewal_stability": renewal_stability,
        "sentinel_telemetry": sentinel_telemetry,
        "duration_ms": result.duration_ms,
    }


def main():
    """Run seed 42 and print results."""
    print("=" * 70)
    print("RUN D: BOUNDARY-HUGGING COMPLIANCE")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  H = 20,000 cycles")
    print("  renewal_check_interval = 50 (epoch boundary)")
    print("  msrw_cycles = 100")
    print("  max_successive_renewals = 10")
    print("  max_steps_per_epoch = 1000")
    print("  max_actions_per_epoch = 100")
    print("  BoundaryHuggerSuccessor weight = 40%")
    print("  ViolationSuccessor: EXCLUDED")
    print()

    # Run seed 42 per user direction
    seeds = [42]
    results = []

    for seed in seeds:
        print(f"Running seed {seed}...")
        result = run_boundary_hugging_experiment(seed)
        results.append(result)
        print(f"  Completed in {result['duration_ms']}ms")
        print(f"  Revocations: {result['total_revocations']}")
        print()

    # Print summary table
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    print(f"{'Seed':<6} {'Cycles':<8} {'Endorse':<9} {'NonTriv':<9} {'Renewals':<9} {'Expire':<8} {'Revoke':<8}")
    print("-" * 70)

    for r in results:
        nt = r["non_trivial_endorsements"]
        nt_pct = (nt / r["total_endorsements"] * 100) if r["total_endorsements"] > 0 else 0
        print(f"{r['seed']:<6} {r['total_cycles']:<8} {r['total_endorsements']:<9} "
              f"{nt} ({nt_pct:.1f}%)  {r['total_renewals']:<9} {r['total_expirations']:<8} "
              f"{r['total_revocations']:<8}")

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
    print("EPOCH-SCOPED UTILIZATION")
    print("-" * 70)
    print(f"{'Seed':<6} {'Epochs':<8} {'util_actions_max':<18} {'util_steps_max':<18}")
    print("-" * 70)

    for r in results:
        eu = r["epoch_utilization"]
        print(f"{r['seed']:<6} {eu['epoch_count']:<8} {eu['util_actions_max']:.3f}             "
              f"{eu['util_steps_max']:.3f}")

    print()
    print(f"{'Seed':<6} {'util_actions_mean':<18} {'util_steps_mean':<18}")
    print("-" * 70)

    for r in results:
        eu = r["epoch_utilization"]
        print(f"{r['seed']:<6} {eu['util_actions_mean']:.3f}              "
              f"{eu['util_steps_mean']:.3f}")

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

    # Check success criteria
    total_revocations = sum(r["total_revocations"] for r in results)
    non_trivial_present = any(r["non_trivial_endorsements"] > 0 for r in results)

    # Check utilization near caps
    high_util = any(
        r["epoch_utilization"]["util_steps_max"] > 0.8 or
        r["epoch_utilization"]["util_actions_max"] > 0.8
        for r in results
    )

    print("CLASSIFICATION")
    print("-" * 70)

    if total_revocations == 0 and non_trivial_present:
        if high_util:
            print("✓ SUCCESS (ALS-supported): Zero false-positive revocations under")
            print("  boundary-layer stress with non-trivial endorsements present.")
        else:
            print("✓ PARTIAL: Zero false-positive revocations, but utilization")
            print("  did not reach near-cap levels (>80%). Evidence supports")
            print("  \"no false-positive revocations under high action throughput\"")
            print("  but not full boundary-hugging compliance.")
    elif total_revocations == 0:
        print("⚠ WARNING: Zero revocations but no non-trivial endorsements.")
        print("  Cannot classify as ALS-supported without non-trivial presence.")
    else:
        print(f"✗ FAILURE: {total_revocations} revocations detected")
        print("  Review revocation events for violation details")

    # Save detailed results
    output_path = Path(__file__).parent / "run_d_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
