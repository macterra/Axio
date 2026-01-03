#!/usr/bin/env python3
"""
Run H: AKI v0.5.2 ALS-E Boundary-Finding Escalation Experiments

Three sub-runs (single-axis escalation):
- H1: Rent escalation (E3=60) with H=30,000
- H2: Horizon extension to H=100,000 cycles
- H3: Renewal cost (10 steps) with H=30,000

All runs:
- Fixed E3 tier (using TierFilterGenerator)
- epoch_size = 100, renewal_check_interval = 100
- msrw_cycles = 200
- max_successive_renewals = 15

Per binding instructions:
- H1: E0=1, E1=15, E2=35, E3=60, E4=80 (escalated rent)
- H2: Default rent schedule (E3=40)
- H3: Default rent + renewal_cost_steps=10

Seeds:
- H1: 40, 41, 42, 43, 44
- H2: 40, 41, 42 (longer runs)
- H3: 40, 41, 42, 43, 44
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
RENEWAL_CHECK_INTERVAL = 100
MSRW_CYCLES = 200
MAX_SUCCESSIVE_RENEWALS = 15
EPOCH_SIZE = 100

# Caps (binding: 100)
STEPS_CAP_EPOCH = 100
ACTIONS_CAP_EPOCH = 100

# Generator weights
CONTROL_WEIGHT = 0.20  # Per binding

# H1: Rent escalation
H1_HORIZON = 30_000
H1_RENT_E1 = 15
H1_RENT_E2 = 35
H1_RENT_E3 = 60  # Escalated from 40
H1_RENT_E4 = 80
H1_SEEDS = [40, 41, 42, 43, 44]

# H2: Horizon extension
H2_HORIZON = 100_000
H2_SEEDS = [40, 41, 42]  # Fewer seeds for longer runs

# H3: Renewal cost
H3_HORIZON = 30_000
H3_RENEWAL_COST_STEPS = 10
H3_SEEDS = [40, 41, 42, 43, 44]


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class RunHSummary:
    """Summary for a single Run H execution."""
    run_id: str
    sub_run: str  # "H1", "H2", "H3"
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
    hollow_tenures_count: int = 0
    hollow_rate: float = 0.0
    renewal_failed_due_to_budget_count: int = 0  # H3 specific
    renewal_cost_steps_charged_total: int = 0  # H3 specific
    runtime_ms: int = 0
    generator_accept_rate: float = 0.0

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
    renewal_cost_charged_total: int = 0  # H3 specific
    renewal_budget_failures: int = 0  # H3 specific

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Helper Functions
# =============================================================================

def create_h1_config() -> ALSConfigV052:
    """Create H1 configuration with escalated rent."""
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=ACTIONS_CAP_EPOCH,
        max_steps_per_epoch=STEPS_CAP_EPOCH,
        max_external_calls=0,
    )

    return ALSConfigV052(
        max_cycles=H1_HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        baseline_resource_envelope_override=baseline_envelope,
        reject_immediate_bankruptcy=False,
        # Escalated rent values
        rent_e1=H1_RENT_E1,
        rent_e2=H1_RENT_E2,
        rent_e3=H1_RENT_E3,
        rent_e4=H1_RENT_E4,
    )


def create_h2_config() -> ALSConfigV052:
    """Create H2 configuration with extended horizon."""
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=ACTIONS_CAP_EPOCH,
        max_steps_per_epoch=STEPS_CAP_EPOCH,
        max_external_calls=0,
    )

    return ALSConfigV052(
        max_cycles=H2_HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        baseline_resource_envelope_override=baseline_envelope,
        reject_immediate_bankruptcy=False,
        # Default rent (no overrides)
    )


def create_h3_config() -> ALSConfigV052:
    """Create H3 configuration with renewal cost."""
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=ACTIONS_CAP_EPOCH,
        max_steps_per_epoch=STEPS_CAP_EPOCH,
        max_external_calls=0,
    )

    return ALSConfigV052(
        max_cycles=H3_HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        baseline_resource_envelope_override=baseline_envelope,
        reject_immediate_bankruptcy=False,
        renewal_cost_steps=H3_RENEWAL_COST_STEPS,  # 10 steps at renewal
    )


def create_generator(
    sentinel_id: str,
    baseline_manifest: "WorkingMindManifest",
    seed: int,
) -> SuccessorGenerator:
    """Create generator with standard weights."""
    config = GeneratorConfig(
        control_weight=CONTROL_WEIGHT,
        attack_weights=V052_ATTACK_WEIGHTS.copy(),
        excluded_attack_types={AttackSuccessorType.VIOLATION},
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

    # H3 specific fields
    renewal_cost_total = sum(getattr(r, 'renewal_cost_steps_charged', 0) for r in records)
    budget_failures = sum(1 for r in records if getattr(r, 'renewal_failed_due_to_budget', False))

    return RentTelemetrySummary(
        rent_steps_charged_mean=sum(rents) / len(rents),
        rent_steps_charged_max=max(rents),
        effective_steps_available_mean=sum(effective) / len(effective),
        effective_steps_available_min=min(effective),
        steps_used_mean=sum(steps) / len(steps),
        steps_used_max=max(steps),
        actions_used_mean=sum(actions) / len(actions),
        actions_used_max=max(actions),
        renewal_cost_charged_total=renewal_cost_total,
        renewal_budget_failures=budget_failures,
    )


# =============================================================================
# H1: Rent Escalation at E3
# =============================================================================

def run_h1(seed: int, verbose: bool = False) -> Tuple[RunHSummary, Dict[str, Any]]:
    """
    Run H1: Rent escalation at fixed E3.

    E3 rent = 60 (up from 40), effective_steps = 40.
    Question: Does higher rent at E3 trigger collapse?
    """
    print(f"  H1 seed={seed}: Rent escalation (E3=60)...")
    start_time = time.time()

    config = create_h1_config()
    harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)

    # Create generator and filter for E3
    base_gen = create_generator(
        sentinel_id=harness._sentinel.sentinel_id,
        baseline_manifest=harness._baseline_manifest,
        seed=seed,
    )
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
        return RunHSummary(
            run_id=f"H1_{seed}",
            sub_run="H1",
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

    summary = RunHSummary(
        run_id=f"H1_{seed}",
        sub_run="H1",
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

    details = {
        "rent_telemetry": compute_rent_telemetry(result.epoch_rent_records).to_dict(),
        "generator_stats": {
            "proposals_accepted": tier_filter.stats["proposals_accepted"],
            "proposals_filtered": tier_filter.stats["proposals_filtered"],
            "acceptance_rate": accept_rate,
        },
        "rent_schedule": {
            "E1": H1_RENT_E1,
            "E2": H1_RENT_E2,
            "E3": H1_RENT_E3,
            "E4": H1_RENT_E4,
            "effective_at_E3": STEPS_CAP_EPOCH - H1_RENT_E3,
        },
    }

    print(f"    H1 seed={seed}: s*={result.s_star}, successions={len(result.succession_events)}, "
          f"renewals={result.total_renewals}, bankruptcies={result.total_bankruptcies}, "
          f"hollow={hollow_count}")

    return summary, details


# =============================================================================
# H2: Horizon Extension at E3
# =============================================================================

def run_h2(seed: int, verbose: bool = False) -> Tuple[RunHSummary, Dict[str, Any]]:
    """
    Run H2: Extended horizon (100,000 cycles) at fixed E3.

    Default rent (E3=40, effective_steps=60).
    Question: Does long horizon reveal slow-accumulation pathologies?
    """
    print(f"  H2 seed={seed}: Horizon extension (H=100,000)...")
    start_time = time.time()

    config = create_h2_config()
    harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)

    # Create generator and filter for E3
    base_gen = create_generator(
        sentinel_id=harness._sentinel.sentinel_id,
        baseline_manifest=harness._baseline_manifest,
        seed=seed,
    )
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
        return RunHSummary(
            run_id=f"H2_{seed}",
            sub_run="H2",
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

    summary = RunHSummary(
        run_id=f"H2_{seed}",
        sub_run="H2",
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

    details = {
        "rent_telemetry": compute_rent_telemetry(result.epoch_rent_records).to_dict(),
        "generator_stats": {
            "proposals_accepted": tier_filter.stats["proposals_accepted"],
            "proposals_filtered": tier_filter.stats["proposals_filtered"],
            "acceptance_rate": accept_rate,
        },
        "horizon": H2_HORIZON,
    }

    print(f"    H2 seed={seed}: s*={result.s_star}, successions={len(result.succession_events)}, "
          f"renewals={result.total_renewals}, bankruptcies={result.total_bankruptcies}, "
          f"hollow={hollow_count}")

    return summary, details


# =============================================================================
# H3: Renewal Cost at E3
# =============================================================================

def run_h3(seed: int, verbose: bool = False) -> Tuple[RunHSummary, Dict[str, Any]]:
    """
    Run H3: Renewal cost (10 steps) at fixed E3.

    Default rent (E3=40), plus 10 steps charged at renewal check.
    Question: Does renewal overhead become the limiting factor?
    """
    print(f"  H3 seed={seed}: Renewal cost (10 steps)...")
    start_time = time.time()

    config = create_h3_config()
    harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)

    # Create generator and filter for E3
    base_gen = create_generator(
        sentinel_id=harness._sentinel.sentinel_id,
        baseline_manifest=harness._baseline_manifest,
        seed=seed,
    )
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
        return RunHSummary(
            run_id=f"H3_{seed}",
            sub_run="H3",
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

    # H3-specific: count renewal budget failures
    renewal_budget_failures = sum(
        1 for r in result.epoch_rent_records
        if getattr(r, 'renewal_failed_due_to_budget', False)
    )
    renewal_cost_charged_total = sum(
        getattr(r, 'renewal_cost_steps_charged', 0) for r in result.epoch_rent_records
    )

    summary = RunHSummary(
        run_id=f"H3_{seed}",
        sub_run="H3",
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
        renewal_failed_due_to_budget_count=renewal_budget_failures,
        renewal_cost_steps_charged_total=renewal_cost_charged_total,
        runtime_ms=runtime_ms,
        generator_accept_rate=accept_rate,
    )

    details = {
        "rent_telemetry": compute_rent_telemetry(result.epoch_rent_records).to_dict(),
        "generator_stats": {
            "proposals_accepted": tier_filter.stats["proposals_accepted"],
            "proposals_filtered": tier_filter.stats["proposals_filtered"],
            "acceptance_rate": accept_rate,
        },
        "renewal_cost": {
            "steps_charged_per_renewal": H3_RENEWAL_COST_STEPS,
            "total_charged": renewal_cost_charged_total,
            "budget_failures": renewal_budget_failures,
        },
    }

    print(f"    H3 seed={seed}: s*={result.s_star}, successions={len(result.succession_events)}, "
          f"renewals={result.total_renewals}, bankruptcies={result.total_bankruptcies}, "
          f"renewal_budget_failures={renewal_budget_failures}, hollow={hollow_count}")

    return summary, details


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run all H sub-runs."""
    print("=" * 60)
    print("Run H: Boundary-Finding Escalation Experiments")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print()

    all_results: Dict[str, List[Dict[str, Any]]] = {
        "H1": [],
        "H2": [],
        "H3": [],
    }
    all_details: Dict[str, List[Dict[str, Any]]] = {
        "H1": [],
        "H2": [],
        "H3": [],
    }

    # Run H1: Rent Escalation
    print("\n" + "=" * 40)
    print("H1: Rent Escalation (E3=60)")
    print("=" * 40)
    for seed in H1_SEEDS:
        summary, details = run_h1(seed, verbose=False)
        all_results["H1"].append(summary.to_dict())
        all_details["H1"].append(details)

    # Run H2: Horizon Extension
    print("\n" + "=" * 40)
    print("H2: Horizon Extension (H=100,000)")
    print("=" * 40)
    for seed in H2_SEEDS:
        summary, details = run_h2(seed, verbose=False)
        all_results["H2"].append(summary.to_dict())
        all_details["H2"].append(details)

    # Run H3: Renewal Cost
    print("\n" + "=" * 40)
    print("H3: Renewal Cost (10 steps)")
    print("=" * 40)
    for seed in H3_SEEDS:
        summary, details = run_h3(seed, verbose=False)
        all_results["H3"].append(summary.to_dict())
        all_details["H3"].append(details)

    # Generate summary
    print("\n" + "=" * 60)
    print("Run H Summary")
    print("=" * 60)

    for sub_run in ["H1", "H2", "H3"]:
        results = all_results[sub_run]
        if not results:
            print(f"\n{sub_run}: No results")
            continue

        total_bankruptcies = sum(r["total_bankruptcies"] for r in results)
        total_hollow = sum(r["hollow_tenures_count"] for r in results)
        avg_renewal_rate = sum(
            r["renewal_rate_by_e_class"].get("E3", 0) for r in results
        ) / len(results)

        print(f"\n{sub_run}:")
        print(f"  Seeds: {[r['seed'] for r in results]}")
        print(f"  Total bankruptcies: {total_bankruptcies}")
        print(f"  Total hollow tenures: {total_hollow}")
        print(f"  Avg E3 renewal rate: {avg_renewal_rate:.3f}")

        if sub_run == "H3":
            total_budget_failures = sum(r.get("renewal_failed_due_to_budget_count", 0) for r in results)
            print(f"  Total renewal budget failures: {total_budget_failures}")

    # Save results to JSON
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output = {
        "run_id": "H",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "H1": {
                "horizon": H1_HORIZON,
                "rent_e3": H1_RENT_E3,
                "seeds": H1_SEEDS,
            },
            "H2": {
                "horizon": H2_HORIZON,
                "seeds": H2_SEEDS,
            },
            "H3": {
                "horizon": H3_HORIZON,
                "renewal_cost_steps": H3_RENEWAL_COST_STEPS,
                "seeds": H3_SEEDS,
            },
        },
        "results": all_results,
        "details": all_details,
    }

    output_path = output_dir / "run_h_v052_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
