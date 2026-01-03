#!/usr/bin/env python3
"""
Run G: AKI v0.5.2 ALS-E Competitive Expressivity Horizon Experiments

Two sub-runs:
- G1: Ascension with competition (E0 → E4 expressivity climb)
- G2: CBD Stress at fixed E3 with high CBD prevalence

Per binding instructions:
- H = 30,000 cycles
- epoch_size = 100, renewal_check_interval = 100
- msrw_cycles = 200
- max_successive_renewals = 15 (enforced)
- steps_cap_epoch = 100, actions_cap_epoch = 100
- Rent schedule: E0=1, E1=10, E2=25, E3=40, E4=60
- reject_immediate_bankruptcy = False
- Use mixed generator + TierFilterGenerator (not TieredGenerator alone)

Key difference from Run F:
- Mixed generator preserves attack/control competition
- TierFilterGenerator as POST-filter, not replacement
- CBD_E3 variant for G2 E3-constrained stress testing

Seeds: 40, 41, 42, 43, 44
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
    TierFilterGenerator,
    TierUnsatisfiableError,
    V052_ATTACK_WEIGHTS,
    V052_RUNG_G2_ATTACK_WEIGHTS,
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
MAX_SUCCESSIVE_RENEWALS = 15  # Binding: forced succession guardrail
EPOCH_SIZE = 100  # Same as renewal_check_interval

# Caps (binding: 100 for Run G)
STEPS_CAP_EPOCH = 100
ACTIONS_CAP_EPOCH = 100

# Rent schedule for S=100: E0=1, E1=10, E2=25, E3=40, E4=60
# (This is the default with fractions 0.10, 0.25, 0.40, 0.60)

# G1 ascension parameters
G1_DWELL_LEASES = 3  # Option A: dwell for 3 leases per tier (binding)
G1_CEILING_THRESHOLD = 0.50  # Renewal rate below this = ceiling found
G1_CEILING_WINDOWS = 3  # Consecutive windows below threshold

# G2 CBD parameters
G2_CBD_WEIGHT = 0.30  # CBD prevalence >= 0.30 per binding

# Generator weights
G1_CONTROL_WEIGHT = 0.20  # Per binding: control ≤ 0.20
G2_CONTROL_WEIGHT = 0.20

# Seeds
G1_SEEDS = [40, 41, 42, 43, 44]
G2_SEEDS = [40, 41, 42, 43, 44]


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class RunGSummary:
    """Summary for a single Run G execution."""
    run_id: str
    sub_run: str  # "G1", "G2"
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
    max_sustained_tier: Optional[str] = None  # G1 only
    ceiling_tier: Optional[str] = None  # G1 only
    hollow_tenures_count: int = 0  # G2 primarily
    hollow_rate: float = 0.0
    runtime_ms: int = 0
    generator_accept_rate: float = 0.0  # TierFilterGenerator acceptance rate

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
    """Create base configuration for Run G."""
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
        # Note: max_successive_renewals is set via GeneratorConfig.max_successive_renewals_default
    )


def create_g1_generator(
    sentinel_id: str,
    baseline_manifest: "WorkingMindManifest",
    seed: int,
) -> SuccessorGenerator:
    """Create G1 generator with mixed attack weights."""
    config = GeneratorConfig(
        control_weight=G1_CONTROL_WEIGHT,
        attack_weights=V052_ATTACK_WEIGHTS.copy(),
        excluded_attack_types={AttackSuccessorType.VIOLATION},  # Exclude violation
        max_successive_renewals_default=MAX_SUCCESSIVE_RENEWALS,
    )
    return SuccessorGenerator(
        sentinel_id=sentinel_id,
        baseline_manifest=baseline_manifest,
        seed=seed,
        config=config,
    )


def create_g2_generator(
    sentinel_id: str,
    baseline_manifest: "WorkingMindManifest",
    seed: int,
) -> SuccessorGenerator:
    """Create G2 generator with CBD_E3 emphasis."""
    config = GeneratorConfig(
        control_weight=G2_CONTROL_WEIGHT,
        attack_weights=V052_RUNG_G2_ATTACK_WEIGHTS.copy(),
        excluded_attack_types={AttackSuccessorType.VIOLATION},  # Exclude violation
        max_successive_renewals_default=MAX_SUCCESSIVE_RENEWALS,
    )
    return SuccessorGenerator(
        sentinel_id=sentinel_id,
        baseline_manifest=baseline_manifest,
        seed=seed,
        config=config,
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
# G1: Ascension with Competition (E0 → E4)
# =============================================================================

def run_g1(seed: int, verbose: bool = False) -> Tuple[RunGSummary, Dict[str, Any]]:
    """
    Run G1: Expressivity ascension E0 → E4 with competition.

    - Use mixed generator + TierFilterGenerator as post-filter
    - Progress tiers at succession boundaries (3 leases per tier)
    - Stop ascending when renewal_rate < 0.50 for 3 consecutive windows
    - Continue at last sustainable tier for remaining horizon
    """
    print(f"  G1 seed={seed}: Starting ascension with competition...")
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
    total_generator_accepted = 0
    total_generator_filtered = 0

    # Window tracking for ceiling detection
    low_renewal_windows = 0

    # Run ascension loop
    cycles_used = 0

    while cycles_used < H_CYCLES and current_tier_idx < len(tiers):
        current_tier = tiers[current_tier_idx]

        # Configure for this tier dwell
        # With max_successive_renewals=15 and renewal_check_interval=100,
        # each lease can last up to 1,500 cycles. For 3 leases, budget ~6,000 cycles.
        # But we also want some buffer, so use 6,000 cycles per tier.
        cycles_per_tier = min(6000, H_CYCLES - cycles_used)
        if cycles_per_tier <= 0:
            break

        dwell_config = ALSConfigV052(
            max_cycles=cycles_per_tier,
            renewal_check_interval=RENEWAL_CHECK_INTERVAL,
            msrw_cycles=MSRW_CYCLES,
            baseline_resource_envelope_override=ResourceEnvelope(
                max_actions_per_epoch=ACTIONS_CAP_EPOCH,
                max_steps_per_epoch=STEPS_CAP_EPOCH,
                max_external_calls=0,
            ),
            reject_immediate_bankruptcy=False,
            # Note: max_successive_renewals is set via GeneratorConfig.max_successive_renewals_default
        )

        harness = ALSHarnessV052(seed=seed + current_tier_idx, config=dwell_config, verbose=verbose)

        # Create mixed generator and wrap with TierFilterGenerator
        base_gen = create_g1_generator(
            sentinel_id=harness._sentinel.sentinel_id,
            baseline_manifest=harness._baseline_manifest,
            seed=seed + current_tier_idx,
        )
        tier_filter = TierFilterGenerator(
            base_generator=base_gen,
            target_e_class=current_tier,
            max_retries=200,
        )
        harness.set_generator(tier_filter)

        print(f"    Tier {current_tier.name}: Starting dwell (max {G1_DWELL_LEASES} leases)...")

        try:
            result = harness.run()
        except TierUnsatisfiableError as e:
            print(f"    TIER_UNSATISFIABLE at {current_tier.name}: {e}")
            # This is a generator deficiency, not ALS failure
            break

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

        # Track TierFilterGenerator stats
        total_generator_accepted += tier_filter.stats["proposals_accepted"]
        total_generator_filtered += tier_filter.stats["proposals_filtered"]

        leases_at_tier = len(result.succession_events)

        # Check ceiling condition
        tier_renewal_rate = result.renewal_rate_by_e_class.get(current_tier.name, 0)
        print(f"    Tier {current_tier.name}: {leases_at_tier} successions, "
              f"renewal_rate={tier_renewal_rate:.2f}, bankruptcies={result.total_bankruptcies}, "
              f"filtered={tier_filter.stats['proposals_filtered']}")

        if tier_renewal_rate < G1_CEILING_THRESHOLD:
            low_renewal_windows += 1
            if low_renewal_windows >= G1_CEILING_WINDOWS:
                print(f"    Ceiling found at {current_tier.name} "
                      f"(renewal_rate < {G1_CEILING_THRESHOLD} for {G1_CEILING_WINDOWS} windows)")
                ceiling_tier = current_tier
                # Fall back to previous tier if possible
                if current_tier_idx > 0:
                    max_sustained_tier = tiers[current_tier_idx - 1]
                break
        else:
            low_renewal_windows = 0  # Reset counter
            max_sustained_tier = current_tier

        # We've completed dwell at this tier (ran full cycle budget)
        print(f"    Dwell complete at {current_tier.name} ({leases_at_tier} leases)")
        # Advance to next tier
        current_tier_idx += 1

    runtime_ms = int((time.time() - start_time) * 1000)

    # Compute renewal rates by E-Class
    renewal_rates: Dict[str, float] = {}
    for e in ExpressivityClass:
        successions = e_class_dist.get(e.name, 0)
        # Use result's renewal rate if available
        if e.name in result.renewal_rate_by_e_class:
            renewal_rates[e.name] = result.renewal_rate_by_e_class[e.name]
        else:
            renewal_rates[e.name] = 0.0

    # Compute acceptance rate
    total_proposals = total_generator_accepted + total_generator_filtered
    accept_rate = total_generator_accepted / total_proposals if total_proposals > 0 else 0.0

    summary = RunGSummary(
        run_id=f"G1_{seed}",
        sub_run="G1",
        seed=seed,
        s_star=total_s_star,
        total_successions=total_successions,
        total_renewals=total_renewals,
        total_expirations=total_expirations,
        total_bankruptcies=total_bankruptcies,
        total_revocations=total_revocations,
        stop_reason="CEILING_FOUND" if ceiling_tier else "HORIZON_REACHED",
        e_class_distribution=e_class_dist,
        renewal_rate_by_e_class=renewal_rates,
        max_sustained_tier=max_sustained_tier.name if max_sustained_tier else None,
        ceiling_tier=ceiling_tier.name if ceiling_tier else None,
        runtime_ms=runtime_ms,
        generator_accept_rate=accept_rate,
    )

    details = {
        "rent_telemetry": compute_rent_telemetry(all_epoch_records).to_dict(),
        "failure_modes": {
            "bankruptcy_by_e_class": {},
            "bankruptcy_by_type": {},
        },
        "generator_stats": {
            "proposals_accepted": total_generator_accepted,
            "proposals_filtered": total_generator_filtered,
            "acceptance_rate": accept_rate,
        },
    }

    # Analyze failure modes
    for ev in all_bankruptcy_events:
        e = ev.e_class
        t = ev.source_type
        details["failure_modes"]["bankruptcy_by_e_class"][e] = \
            details["failure_modes"]["bankruptcy_by_e_class"].get(e, 0) + 1
        details["failure_modes"]["bankruptcy_by_type"][t] = \
            details["failure_modes"]["bankruptcy_by_type"].get(t, 0) + 1

    return summary, details


# =============================================================================
# G2: CBD Stress at Fixed E3
# =============================================================================

def run_g2(seed: int, verbose: bool = False) -> Tuple[RunGSummary, Dict[str, Any]]:
    """
    Run G2: CBD stress at fixed E3.

    - Fix expressivity at E3
    - Use mixed generator with CBD_E3 weight >= 0.30
    - TierFilterGenerator(E3) as post-filter
    - Map hollow succession and thrash dynamics
    """
    print(f"  G2 seed={seed}: Starting E3 CBD stress...")
    start_time = time.time()

    config = create_base_config()
    harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)

    # Create G2 generator with CBD_E3 emphasis
    base_gen = create_g2_generator(
        sentinel_id=harness._sentinel.sentinel_id,
        baseline_manifest=harness._baseline_manifest,
        seed=seed,
    )
    # Wrap with TierFilterGenerator for E3
    tier_filter = TierFilterGenerator(
        base_generator=base_gen,
        target_e_class=ExpressivityClass.E3,
        max_retries=200,
    )
    harness.set_generator(tier_filter)

    try:
        result = harness.run()
    except TierUnsatisfiableError as e:
        print(f"    TIER_UNSATISFIABLE at E3: {e}")
        # Return partial result
        return RunGSummary(
            run_id=f"G2_{seed}",
            sub_run="G2",
            seed=seed,
            s_star=0,
            total_successions=0,
            total_renewals=0,
            total_expirations=0,
            total_bankruptcies=0,
            total_revocations=0,
            stop_reason="TIER_UNSATISFIABLE",
            e_class_distribution={},
            renewal_rate_by_e_class={},
            runtime_ms=int((time.time() - start_time) * 1000),
        ), {"error": str(e)}

    runtime_ms = int((time.time() - start_time) * 1000)

    # Classify hollow tenures
    hollow_tenures = classify_hollow_tenures(
        epoch_rent_records=result.epoch_rent_records,
        succession_events=result.succession_events,
        renewal_events=result.renewal_events,
        revocation_events=result.revocation_events,
        actions_cap_epoch=ACTIONS_CAP_EPOCH,
        low_action_threshold=0.10,
        min_consecutive_renewals=2,
        min_low_action_streak=5,
    )

    hollow_count = len(hollow_tenures)
    hollow_rate = hollow_count / len(result.succession_events) if result.succession_events else 0.0

    # Compute acceptance rate
    total_proposals = tier_filter.stats["proposals_accepted"] + tier_filter.stats["proposals_filtered"]
    accept_rate = tier_filter.stats["proposals_accepted"] / total_proposals if total_proposals > 0 else 0.0

    summary = RunGSummary(
        run_id=f"G2_{seed}",
        sub_run="G2",
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
        generator_accept_rate=accept_rate,
    )

    # Analyze hollow tenures by successor type
    hollow_by_type: Dict[str, int] = {}
    for ht in hollow_tenures:
        t = ht.source_type
        hollow_by_type[t] = hollow_by_type.get(t, 0) + 1

    details = {
        "rent_telemetry": compute_rent_telemetry(result.epoch_rent_records).to_dict(),
        "failure_modes": analyze_failure_modes(result),
        "hollow_succession": {
            "count": hollow_count,
            "rate": hollow_rate,
            "by_successor_type": hollow_by_type,
        },
        "generator_stats": {
            "proposals_accepted": tier_filter.stats["proposals_accepted"],
            "proposals_filtered": tier_filter.stats["proposals_filtered"],
            "acceptance_rate": accept_rate,
        },
    }

    print(f"    S*={result.s_star}, successions={len(result.succession_events)}, "
          f"renewals={result.total_renewals}, bankruptcies={result.total_bankruptcies}, "
          f"hollow={hollow_count} ({hollow_rate*100:.1f}%)")

    return summary, details


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run all G experiments."""
    print("=" * 70)
    print("Run G: AKI v0.5.2 Competitive Expressivity Horizon")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  H = {H_CYCLES} cycles")
    print(f"  max_successive_renewals = {MAX_SUCCESSIVE_RENEWALS}")
    print(f"  G1 control_weight = {G1_CONTROL_WEIGHT}")
    print(f"  G2 CBD_E3 weight = {G2_CBD_WEIGHT}")
    print(f"  Dwell = {G1_DWELL_LEASES} leases per tier")
    print()

    results_dir = Path(__file__).parent.parent / "reports" / "run_g"
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = {
        "run_timestamp": datetime.now().isoformat(),
        "config": {
            "H_CYCLES": H_CYCLES,
            "MAX_SUCCESSIVE_RENEWALS": MAX_SUCCESSIVE_RENEWALS,
            "G1_CONTROL_WEIGHT": G1_CONTROL_WEIGHT,
            "G1_DWELL_LEASES": G1_DWELL_LEASES,
            "G2_CBD_WEIGHT": G2_CBD_WEIGHT,
        },
        "G1": [],
        "G2": [],
    }

    # Run G1: Ascension with competition
    print("-" * 70)
    print("G1: Ascension with Competition")
    print("-" * 70)
    for seed in G1_SEEDS:
        summary, details = run_g1(seed, verbose=False)
        all_results["G1"].append({
            "summary": summary.to_dict(),
            "details": details,
        })
        print()

    # Run G2: CBD Stress at fixed E3
    print("-" * 70)
    print("G2: CBD Stress at Fixed E3")
    print("-" * 70)
    for seed in G2_SEEDS:
        summary, details = run_g2(seed, verbose=False)
        all_results["G2"].append({
            "summary": summary.to_dict(),
            "details": details,
        })
        print()

    # Save results
    results_file = results_dir / f"run_g_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Results saved to: {results_file}")

    # Print summary table
    print()
    print("=" * 70)
    print("G1 Summary Table")
    print("=" * 70)
    print(f"{'Seed':<6} {'S*':<6} {'Succ':<6} {'Rnwl':<6} {'Bkrpt':<6} {'Max Tier':<10} {'Ceiling':<10} {'Accept%':<8}")
    print("-" * 70)
    for r in all_results["G1"]:
        s = r["summary"]
        print(f"{s['seed']:<6} {s['s_star']:<6} {s['total_successions']:<6} "
              f"{s['total_renewals']:<6} {s['total_bankruptcies']:<6} "
              f"{s['max_sustained_tier'] or 'N/A':<10} {s['ceiling_tier'] or 'N/A':<10} "
              f"{s['generator_accept_rate']*100:.1f}%")

    print()
    print("=" * 70)
    print("G2 Summary Table")
    print("=" * 70)
    print(f"{'Seed':<6} {'S*':<6} {'Succ':<6} {'Rnwl':<6} {'Bkrpt':<6} {'Hollow':<8} {'Rate':<8} {'Accept%':<8}")
    print("-" * 70)
    for r in all_results["G2"]:
        s = r["summary"]
        print(f"{s['seed']:<6} {s['s_star']:<6} {s['total_successions']:<6} "
              f"{s['total_renewals']:<6} {s['total_bankruptcies']:<6} "
              f"{s['hollow_tenures_count']:<8} {s['hollow_rate']*100:.1f}%{' ':<5} "
              f"{s['generator_accept_rate']*100:.1f}%")

    print()
    print("Run G complete.")


if __name__ == "__main__":
    main()
