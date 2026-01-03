#!/usr/bin/env python3
"""
Run F: AKI v0.5.2 ALS-E Competence Horizon Experiments

Three sub-runs:
- F0: Calibration (E0 baseline)
- F1: Ascension (E0 → E4 expressivity climb)
- F2: CBD Stress (fixed E3 with high CBD prevalence)

Per binding instructions:
- H = 30,000 cycles
- steps_cap_epoch = 100, actions_cap_epoch = 100
- Rent schedule: E0=1, E1=10, E2=25, E3=40, E4=60
- reject_immediate_bankruptcy = False

Seeds:
- F0: 42, 43, 44
- F1, F2: 40, 41, 42, 43, 44
"""

import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.generator import (
    GeneratorConfig,
    AttackSuccessorType,
    ControlSuccessorType,
    SuccessorGenerator,
    TieredGenerator,
    V052_ATTACK_WEIGHTS,
    TieredSuccessor,
)
from toy_aki.als.harness import (
    ALSHarnessV052,
    ALSConfigV052,
    ALSRunResultV052,
)
from toy_aki.als.expressivity import (
    ExpressivityClass,
    RentSchedule,
    classify_hollow_tenures,
    HollowTenure,
)
from toy_aki.als.working_mind import ResourceEnvelope


# =============================================================================
# Configuration Constants (Binding)
# =============================================================================

# Shared parameters
H_CYCLES = 30_000
RENEWAL_CHECK_INTERVAL = 100
MSRW_CYCLES = 200
MAX_SUCCESSIVE_RENEWALS = 15
EPOCH_SIZE = 100  # Same as renewal_check_interval

# Caps (binding: 100 for Run F)
STEPS_CAP_EPOCH = 100
ACTIONS_CAP_EPOCH = 100

# Rent schedule for S=100: E0=1, E1=10, E2=25, E3=40, E4=60
# (This is the default with fractions 0.10, 0.25, 0.40, 0.60)

# F1 ascension parameters
F1_DWELL_LEASES = 3  # Option A: dwell for 3 leases per tier
F1_CEILING_THRESHOLD = 0.50  # Renewal rate below this = ceiling found
F1_CEILING_WINDOWS = 3  # Consecutive windows below threshold

# F2 CBD parameters
F2_CBD_WEIGHT = 0.30  # CBD prevalence >= 0.25 per binding

# Seeds
F0_SEEDS = [42, 43, 44]
F1_SEEDS = [40, 41, 42, 43, 44]
F2_SEEDS = [40, 41, 42, 43, 44]


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class RunFSummary:
    """Summary for a single Run F execution."""
    run_id: str
    sub_run: str  # "F0", "F1", "F2"
    seed: int
    s_star: int
    total_successions: int
    total_renewals: int
    total_expirations: int
    total_bankruptcies: int
    total_revocations: int
    stop_reason: str
    e_class_distribution: Dict[str, int]
    renewal_rate_by_e_class: Dict[str, float]
    max_sustained_tier: Optional[str] = None  # F1 only
    ceiling_tier: Optional[str] = None  # F1 only
    hollow_tenures_count: int = 0  # F2 primarily
    hollow_rate: float = 0.0
    runtime_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RentTelemetrySummary:
    """Rent telemetry aggregation."""
    rent_steps_charged_mean: float
    rent_steps_charged_max: int
    effective_steps_available_mean: float
    effective_steps_available_min: int
    steps_used_mean: float
    steps_used_max: int
    actions_used_mean: float
    actions_used_max: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Helper Functions
# =============================================================================

def create_base_config(
    generator_config: Optional[GeneratorConfig] = None,
) -> ALSConfigV052:
    """Create base configuration for Run F."""
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=ACTIONS_CAP_EPOCH,
        max_steps_per_epoch=STEPS_CAP_EPOCH,
        max_external_calls=0,
    )

    return ALSConfigV052(
        max_cycles=H_CYCLES,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        generator_config=generator_config,
        baseline_resource_envelope_override=baseline_envelope,
        reject_immediate_bankruptcy=False,  # Binding: bankruptcy is valid data
    )


def compute_rent_telemetry(
    epoch_records: List[Any],
    e_class_filter: Optional[str] = None,
) -> RentTelemetrySummary:
    """Compute rent telemetry summary from epoch records."""
    if e_class_filter:
        records = [r for r in epoch_records if r.e_class == e_class_filter]
    else:
        records = epoch_records

    if not records:
        return RentTelemetrySummary(
            rent_steps_charged_mean=0.0,
            rent_steps_charged_max=0,
            effective_steps_available_mean=0.0,
            effective_steps_available_min=0,
            steps_used_mean=0.0,
            steps_used_max=0,
            actions_used_mean=0.0,
            actions_used_max=0,
        )

    rents = [r.rent_charged for r in records]
    effective = [r.effective_steps for r in records]
    steps = [r.steps_used for r in records]
    actions = [r.actions_used for r in records]

    return RentTelemetrySummary(
        rent_steps_charged_mean=sum(rents) / len(rents),
        rent_steps_charged_max=max(rents),
        effective_steps_available_mean=sum(effective) / len(effective),
        effective_steps_available_min=min(effective),
        steps_used_mean=sum(steps) / len(steps),
        steps_used_max=max(steps),
        actions_used_mean=sum(actions) / len(actions),
        actions_used_max=max(actions),
    )


def analyze_failure_modes(
    result: ALSRunResultV052,
) -> Dict[str, Dict[str, int]]:
    """Analyze failure modes by E-Class and successor type."""
    bankruptcy_by_eclass: Dict[str, int] = {}
    bankruptcy_by_type: Dict[str, int] = {}

    for ev in result.bankruptcy_events:
        e = ev.e_class
        t = ev.source_type
        bankruptcy_by_eclass[e] = bankruptcy_by_eclass.get(e, 0) + 1
        bankruptcy_by_type[t] = bankruptcy_by_type.get(t, 0) + 1

    return {
        "bankruptcy_by_e_class": bankruptcy_by_eclass,
        "bankruptcy_by_type": bankruptcy_by_type,
    }


# =============================================================================
# F0: Calibration Run (E0 Baseline)
# =============================================================================

def run_f0(seed: int, verbose: bool = False) -> Tuple[RunFSummary, Dict[str, Any]]:
    """
    Run F0: E0 baseline calibration.

    - Use TieredGenerator at E0 for guaranteed E0 successors
    - Verify rent accounting
    - Expected: revocations=0, bankruptcies=0, renewal_rate>=0.95
    """
    print(f"  F0 seed={seed}: Starting E0 calibration...")
    start_time = time.time()

    config = create_base_config()
    harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)

    # Use TieredGenerator for guaranteed E0 successors
    tiered_gen = TieredGenerator(
        sentinel_id=harness._sentinel.sentinel_id,
        target_e_class=ExpressivityClass.E0,
        seed=seed,
        resources=harness._baseline_manifest.resources,
    )
    harness.set_generator(tiered_gen)

    result = harness.run()

    runtime_ms = int((time.time() - start_time) * 1000)

    # Build summary
    summary = RunFSummary(
        run_id=f"F0_{seed}",
        sub_run="F0",
        seed=seed,
        s_star=result.s_star,
        total_successions=len(result.succession_events),
        total_renewals=result.total_renewals,
        total_expirations=result.total_expirations,
        total_bankruptcies=result.total_bankruptcies,
        total_revocations=result.total_revocations,
        stop_reason=result.stop_reason.name if result.stop_reason else "UNKNOWN",
        e_class_distribution=result.e_class_distribution,
        renewal_rate_by_e_class=result.renewal_rate_by_e_class,
        runtime_ms=runtime_ms,
    )

    # Detailed data
    details = {
        "rent_telemetry": compute_rent_telemetry(result.epoch_rent_records).to_dict(),
        "generator_stats": {"candidate_count": tiered_gen.candidate_count},
        "failure_modes": analyze_failure_modes(result),
    }

    # Sanity checks
    checks = {
        "revocations_zero": result.total_revocations == 0,
        "bankruptcies_zero": result.total_bankruptcies == 0,
        "renewal_rate_high": result.renewal_rate_by_e_class.get("E0", 0) >= 0.95,
    }
    details["sanity_checks"] = checks

    print(f"    S*={result.s_star}, renewals={result.total_renewals}, "
          f"bankruptcies={result.total_bankruptcies}, revocations={result.total_revocations}")
    print(f"    Sanity: {checks}")

    return summary, details


# =============================================================================
# F1: Ascension Run (E0 → E4 Climb)
# =============================================================================

def run_f1(seed: int, verbose: bool = False) -> Tuple[RunFSummary, Dict[str, Any]]:
    """
    Run F1: Expressivity ascension E0 → E4.

    - Progress tiers at succession boundaries (Option A: 3 leases per tier)
    - Use TieredGenerator for guaranteed tier-specific successors
    - Stop ascending when renewal_rate < 0.50 for 3 consecutive windows
    - Continue at last sustainable tier for remaining horizon
    """
    print(f"  F1 seed={seed}: Starting ascension...")
    start_time = time.time()

    # Track ascension state
    tiers = [ExpressivityClass.E0, ExpressivityClass.E1, ExpressivityClass.E2,
             ExpressivityClass.E3, ExpressivityClass.E4]
    current_tier_idx = 0
    max_sustained_tier = ExpressivityClass.E0
    ceiling_tier: Optional[ExpressivityClass] = None

    # Aggregate results across tier progressions
    all_epoch_records = []
    all_bankruptcy_events = []
    total_s_star = 0
    total_successions = 0
    total_renewals = 0
    total_expirations = 0
    total_bankruptcies = 0
    total_revocations = 0
    e_class_dist: Dict[str, int] = {}

    # Run ascension loop
    cycles_used = 0

    while cycles_used < H_CYCLES and current_tier_idx < len(tiers):
        current_tier = tiers[current_tier_idx]

        # Calculate dwell cycles: enough for F1_DWELL_LEASES with ~100 cycles per lease
        # Each lease epoch is RENEWAL_CHECK_INTERVAL cycles
        dwell_cycles_per_tier = min(
            F1_DWELL_LEASES * RENEWAL_CHECK_INTERVAL * 100,  # ~30,000 cycles per lease at ~100 epochs/lease
            H_CYCLES // 5,  # Or 1/5 of total horizon, whichever is smaller
        )
        remaining_cycles = min(dwell_cycles_per_tier, H_CYCLES - cycles_used)

        # Configure for this tier dwell
        dwell_config = ALSConfigV052(
            max_cycles=remaining_cycles,
            renewal_check_interval=RENEWAL_CHECK_INTERVAL,
            msrw_cycles=MSRW_CYCLES,
            baseline_resource_envelope_override=ResourceEnvelope(
                max_actions_per_epoch=ACTIONS_CAP_EPOCH,
                max_steps_per_epoch=STEPS_CAP_EPOCH,
                max_external_calls=0,
            ),
            reject_immediate_bankruptcy=False,
        )

        harness = ALSHarnessV052(seed=seed + current_tier_idx, config=dwell_config, verbose=verbose)

        # Use TieredGenerator for guaranteed tier-specific successors
        tiered_gen = TieredGenerator(
            sentinel_id=harness._sentinel.sentinel_id,
            target_e_class=current_tier,
            seed=seed + current_tier_idx,
            resources=harness._baseline_manifest.resources,
        )
        harness.set_generator(tiered_gen)

        print(f"    Tier {current_tier.name}: Starting dwell (max {remaining_cycles} cycles)...")

        result = harness.run()

        # Accumulate results
        cycles_used += harness.cycle
        all_epoch_records.extend(result.epoch_rent_records)
        all_bankruptcy_events.extend(result.bankruptcy_events)
        total_s_star += result.s_star
        total_successions += len(result.succession_events)
        total_renewals += result.total_renewals
        total_expirations += result.total_expirations
        total_bankruptcies += result.total_bankruptcies
        total_revocations += result.total_revocations

        for k, v in result.e_class_distribution.items():
            e_class_dist[k] = e_class_dist.get(k, 0) + v

        leases_at_tier = len(result.succession_events)

        # Check ceiling condition
        tier_renewal_rate = result.renewal_rate_by_e_class.get(current_tier.name, 0)
        print(f"    Tier {current_tier.name}: {leases_at_tier} successions, "
              f"renewal_rate={tier_renewal_rate:.2f}, bankruptcies={result.total_bankruptcies}")

        if tier_renewal_rate < F1_CEILING_THRESHOLD:
            print(f"    Ceiling found at {current_tier.name} (renewal_rate < {F1_CEILING_THRESHOLD})")
            ceiling_tier = current_tier
            # Continue at previous tier if possible
            if current_tier_idx > 0:
                max_sustained_tier = tiers[current_tier_idx - 1]
            break
        else:
            max_sustained_tier = current_tier

        # Advance to next tier
        current_tier_idx += 1

    runtime_ms = int((time.time() - start_time) * 1000)

    # Compute renewal rates by E-Class
    renewal_rates: Dict[str, float] = {}
    for e in ExpressivityClass:
        successions = e_class_dist.get(e.name, 0)
        # Approximate renewal rate from epochs
        epochs_at_e = len([r for r in all_epoch_records if r.e_class == e.name])
        if successions > 0 and epochs_at_e > 0:
            # Rough estimate: renewals ~= epochs - successions
            renewal_rates[e.name] = max(0, (epochs_at_e - successions) / max(1, epochs_at_e))
        else:
            renewal_rates[e.name] = 0.0

    summary = RunFSummary(
        run_id=f"F1_{seed}",
        sub_run="F1",
        seed=seed,
        s_star=total_s_star,
        total_successions=total_successions,
        total_renewals=total_renewals,
        total_expirations=total_expirations,
        total_bankruptcies=total_bankruptcies,
        total_revocations=total_revocations,
        stop_reason="CEILING_FOUND" if ceiling_tier else "ASCENSION_COMPLETE",
        e_class_distribution=e_class_dist,
        renewal_rate_by_e_class=renewal_rates,
        max_sustained_tier=max_sustained_tier.name,
        ceiling_tier=ceiling_tier.name if ceiling_tier else None,
        runtime_ms=runtime_ms,
    )

    details = {
        "rent_telemetry": compute_rent_telemetry(all_epoch_records).to_dict(),
        "rent_by_tier": {
            e.name: compute_rent_telemetry(all_epoch_records, e.name).to_dict()
            for e in ExpressivityClass
        },
        "failure_modes": {
            "bankruptcy_by_e_class": {},
            "bankruptcy_by_type": {},
        },
        "tier_progression": {
            "max_sustained": max_sustained_tier.name,
            "ceiling": ceiling_tier.name if ceiling_tier else None,
        },
    }

    # Aggregate failure modes
    for ev in all_bankruptcy_events:
        e = ev.e_class
        t = ev.source_type
        details["failure_modes"]["bankruptcy_by_e_class"][e] = \
            details["failure_modes"]["bankruptcy_by_e_class"].get(e, 0) + 1
        details["failure_modes"]["bankruptcy_by_type"][t] = \
            details["failure_modes"]["bankruptcy_by_type"].get(t, 0) + 1

    print(f"    Final: max_sustained={max_sustained_tier.name}, "
          f"ceiling={ceiling_tier.name if ceiling_tier else 'None'}")

    return summary, details


# =============================================================================
# F2: CBD Stress Run (Fixed E3)
# =============================================================================

def run_f2(seed: int, verbose: bool = False) -> Tuple[RunFSummary, Dict[str, Any]]:
    """
    Run F2: CBD stress test at fixed E3.

    - Fixed E3 expressivity
    - High CBD prevalence (>=0.25)
    - Measure hollow succession rate
    """
    print(f"  F2 seed={seed}: Starting CBD stress at E3...")
    start_time = time.time()

    # Create config with high CBD weight
    gen_config = GeneratorConfig(
        control_weight=0.1,  # Low control
        attack_weights={
            AttackSuccessorType.RUBBER_STAMP: 0.15,
            AttackSuccessorType.LEASE_GAMING: 0.15,
            AttackSuccessorType.SEMANTIC_CREEP: 0.15,
            AttackSuccessorType.HIDDEN_DELEGATION: 0.08,
            AttackSuccessorType.ENDORSEMENT_PRESSURE: 0.08,
            AttackSuccessorType.SENTINEL_EVASION: 0.04,
            AttackSuccessorType.BOUNDARY_HUGGER: 0.05,
            AttackSuccessorType.CBD: F2_CBD_WEIGHT,  # High CBD
        },
        excluded_attack_types={AttackSuccessorType.VIOLATION},
    )

    config = create_base_config(gen_config)
    harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)

    # Use TieredGenerator for guaranteed E3 successors
    tiered_gen = TieredGenerator(
        sentinel_id=harness._sentinel.sentinel_id,
        target_e_class=ExpressivityClass.E3,
        seed=seed,
        resources=harness._baseline_manifest.resources,
    )
    harness.set_generator(tiered_gen)

    result = harness.run()

    runtime_ms = int((time.time() - start_time) * 1000)

    # Classify hollow tenures
    hollow_tenures = classify_hollow_tenures(
        epoch_rent_records=result.epoch_rent_records,
        succession_events=result.succession_events if hasattr(result, 'succession_events') else [],
        renewal_events=result.renewal_events if hasattr(result, 'renewal_events') else [],
        revocation_events=result.revocation_events if hasattr(result, 'revocation_events') else [],
        actions_cap_epoch=ACTIONS_CAP_EPOCH,
    )

    hollow_count = len(hollow_tenures)
    hollow_rate = hollow_count / max(1, len(result.succession_events))

    # Breakdown by successor type
    hollow_by_type: Dict[str, int] = {}
    for ht in hollow_tenures:
        t = ht.successor_type
        hollow_by_type[t] = hollow_by_type.get(t, 0) + 1

    summary = RunFSummary(
        run_id=f"F2_{seed}",
        sub_run="F2",
        seed=seed,
        s_star=result.s_star,
        total_successions=len(result.succession_events),
        total_renewals=result.total_renewals,
        total_expirations=result.total_expirations,
        total_bankruptcies=result.total_bankruptcies,
        total_revocations=result.total_revocations,
        stop_reason=result.stop_reason.name if result.stop_reason else "UNKNOWN",
        e_class_distribution=result.e_class_distribution,
        renewal_rate_by_e_class=result.renewal_rate_by_e_class,
        hollow_tenures_count=hollow_count,
        hollow_rate=hollow_rate,
        runtime_ms=runtime_ms,
    )

    details = {
        "rent_telemetry": compute_rent_telemetry(result.epoch_rent_records).to_dict(),
        "failure_modes": analyze_failure_modes(result),
        "hollow_succession": {
            "total_hollow": hollow_count,
            "hollow_rate": hollow_rate,
            "by_successor_type": hollow_by_type,
            "tenures": [ht.to_dict() for ht in hollow_tenures[:20]],  # First 20
        },
        "tiered_generator_candidate_count": tiered_gen.candidate_count,
    }

    print(f"    S*={result.s_star}, successions={len(result.succession_events)}, "
          f"bankruptcies={result.total_bankruptcies}, hollow={hollow_count} ({hollow_rate:.2%})")

    return summary, details


# =============================================================================
# Main Execution
# =============================================================================

def run_all_f():
    """Execute all Run F sub-runs."""
    results = {
        "metadata": {
            "experiment": "Run F: AKI v0.5.2 ALS-E Competence Horizon",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "H_cycles": H_CYCLES,
                "steps_cap_epoch": STEPS_CAP_EPOCH,
                "actions_cap_epoch": ACTIONS_CAP_EPOCH,
                "renewal_check_interval": RENEWAL_CHECK_INTERVAL,
                "rent_schedule": {
                    "E0": 1,
                    "E1": 10,
                    "E2": 25,
                    "E3": 40,
                    "E4": 60,
                },
            },
        },
        "F0": {"summaries": [], "details": []},
        "F1": {"summaries": [], "details": []},
        "F2": {"summaries": [], "details": []},
    }

    print("=" * 60)
    print("Run F: AKI v0.5.2 ALS-E Competence Horizon Experiments")
    print("=" * 60)

    # F0: Calibration
    print("\n--- F0: Calibration (E0 Baseline) ---")
    for seed in F0_SEEDS:
        summary, details = run_f0(seed)
        results["F0"]["summaries"].append(summary.to_dict())
        results["F0"]["details"].append(details)

    # F1: Ascension
    print("\n--- F1: Ascension (E0 → E4 Climb) ---")
    for seed in F1_SEEDS:
        summary, details = run_f1(seed)
        results["F1"]["summaries"].append(summary.to_dict())
        results["F1"]["details"].append(details)

    # F2: CBD Stress
    print("\n--- F2: CBD Stress (E3 Fixed) ---")
    for seed in F2_SEEDS:
        summary, details = run_f2(seed)
        results["F2"]["summaries"].append(summary.to_dict())
        results["F2"]["details"].append(details)

    # Save results
    output_path = Path(__file__).parent / "run_f_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"Results saved to: {output_path}")
    print(f"{'=' * 60}")

    return results


def print_summary_table(results: Dict[str, Any]):
    """Print summary tables for all sub-runs."""
    print("\n" + "=" * 80)
    print("SUMMARY TABLES")
    print("=" * 80)

    for sub_run in ["F0", "F1", "F2"]:
        summaries = results[sub_run]["summaries"]
        if not summaries:
            continue

        print(f"\n--- {sub_run} Results ---")
        print(f"{'Seed':<6} {'S*':<6} {'Succ':<6} {'Renew':<6} {'Bankr':<6} {'Revoc':<6} {'Stop':<20}")
        print("-" * 70)

        for s in summaries:
            print(f"{s['seed']:<6} {s['s_star']:<6} {s['total_successions']:<6} "
                  f"{s['total_renewals']:<6} {s['total_bankruptcies']:<6} "
                  f"{s['total_revocations']:<6} {s['stop_reason']:<20}")

        # F1 ceiling info
        if sub_run == "F1":
            print("\nCeiling Analysis:")
            for s in summaries:
                print(f"  Seed {s['seed']}: max_sustained={s.get('max_sustained_tier', 'N/A')}, "
                      f"ceiling={s.get('ceiling_tier', 'None')}")

        # F2 hollow info
        if sub_run == "F2":
            print("\nHollow Succession:")
            for s in summaries:
                print(f"  Seed {s['seed']}: hollow={s.get('hollow_tenures_count', 0)} "
                      f"({s.get('hollow_rate', 0):.2%})")


if __name__ == "__main__":
    results = run_all_f()
    print_summary_table(results)
