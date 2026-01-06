#!/usr/bin/env python3
"""
RSA v0.2 Run 0 — Baseline Reference (No Interference)

Establishes clean reference baseline for all RSA v0.2 experiments under the
exact frozen AKI configuration, horizon, and seed set used in Runs 1-3.

Conditions:
  A: RSA disabled (true clean baseline)
  B: RSA enabled, p=0 (enabled-path equivalence)

Requirement: Results from A and B must be IDENTICAL at trace level.
"""

import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(__file__).replace("/scripts/rsa_v020_run0_baseline_reference.py", "/src"))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.metrics import compute_rsa_metrics, FailureClass


# =============================================================================
# Frozen Execution Parameters (v0.2)
# =============================================================================

FROZEN_ALS_CONFIG = ALSConfigV080(
    max_cycles=300_000,              # yields 6000 epochs at renewal_check_interval=50
    eligibility_threshold_k=3,        # frozen baseline
    max_successive_renewals=3,        # frozen baseline
    amnesty_interval=10,              # frozen baseline
    amnesty_decay=1,                  # frozen baseline
    cta_enabled=True,                 # frozen baseline
)

# Derived constants
RENEWAL_CHECK_INTERVAL = 50  # default
HORIZON_EPOCHS = FROZEN_ALS_CONFIG.max_cycles // RENEWAL_CHECK_INTERVAL
TAIL_WINDOW = max(5000, HORIZON_EPOCHS // 5)

SEEDS = [40, 41, 42, 43, 44]


@dataclass
class RunMetrics:
    """Per-run metrics for baseline comparison."""
    seed: int
    condition: str

    # AKI governance metrics
    s_star: int
    total_cycles: int
    recovery_count: int
    amnesty_event_count: int
    authority_uptime_cycles: int
    total_renewals: int
    semantic_lapse_count: int
    structural_lapse_count: int

    # RSA metrics (computed from authority timeline)
    authority_availability_ppm: int
    asymptotic_authority_availability_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    max_single_lapse_epochs: int
    epochs_evaluated: int
    epochs_in_lapse: int

    # RTD histogram
    recovery_time_histogram: Dict[str, int]

    # RSA telemetry (Condition B only)
    rsa_total_targets: Optional[int] = None
    rsa_total_flips: Optional[int] = None
    rsa_observed_flip_rate_ppm: Optional[int] = None


def build_authority_timeline(result) -> List[bool]:
    """
    Build authority timeline from semantic epoch records.

    Returns list of booleans: True if authority active, False if in lapse.

    Algorithm:
    - semantic_epoch_records are created only when authority is active
    - Each record has a 'cycle' field (the cycle when evaluation happened)
    - Global epoch = cycle // renewal_check_interval
    - Mark that global epoch as having active authority
    """
    epochs = HORIZON_EPOCHS
    timeline = [False] * epochs

    # Mark epochs where we have semantic evaluation (authority was active)
    for rec in result.semantic_epoch_records:
        # rec is a dict (from dataclass .to_dict()) with 'cycle' field
        cycle = rec.get("cycle", 0)
        global_epoch = cycle // RENEWAL_CHECK_INTERVAL
        if 0 <= global_epoch < epochs:
            timeline[global_epoch] = True

    return timeline


def run_condition_a(seed: int) -> RunMetrics:
    """Run with RSA disabled (true clean baseline)."""
    harness = ALSHarnessV080(seed=seed, config=FROZEN_ALS_CONFIG)
    result = harness.run()

    # Build authority timeline and compute RSA metrics
    timeline = build_authority_timeline(result)
    rsa_metrics = compute_rsa_metrics(timeline)

    return RunMetrics(
        seed=seed,
        condition="A (RSA disabled)",
        s_star=result.s_star,
        total_cycles=result.total_cycles,
        recovery_count=result.recovery_count,
        amnesty_event_count=result.amnesty_event_count,
        authority_uptime_cycles=result.authority_uptime_cycles,
        total_renewals=result.total_renewals,
        semantic_lapse_count=result.semantic_lapse_count,
        structural_lapse_count=result.structural_lapse_count,
        authority_availability_ppm=rsa_metrics.authority_availability_ppm,
        asymptotic_authority_availability_ppm=rsa_metrics.asymptotic_authority_availability_ppm,
        failure_class=rsa_metrics.failure_class.value,
        lapse_count=len(rsa_metrics.lapse_intervals),
        total_lapse_epochs=rsa_metrics.lapse_epochs,
        max_single_lapse_epochs=max((lapse.duration_epochs for lapse in rsa_metrics.lapse_intervals), default=0),
        epochs_evaluated=rsa_metrics.authority_epochs,
        epochs_in_lapse=rsa_metrics.lapse_epochs,
        recovery_time_histogram=rsa_metrics.recovery_time_histogram,
    )


def run_condition_b(seed: int) -> RunMetrics:
    """Run with RSA enabled, p=0 (enabled-path equivalence)."""
    rsa_config = RSAConfig(
        rsa_enabled=True,
        rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
        rsa_scope=RSAScope.SEM_PASS_ONLY,
        rsa_rng_stream="rsa_v020",
        rsa_p_flip_ppm=0,
    )

    harness = ALSHarnessV080(seed=seed, config=FROZEN_ALS_CONFIG, rsa_config=rsa_config)
    result = harness.run()

    # Build authority timeline and compute RSA metrics
    timeline = build_authority_timeline(result)
    rsa_metrics = compute_rsa_metrics(timeline)

    # Extract RSA telemetry
    rsa_summary = result.rsa["summary"] if result.rsa else {}

    return RunMetrics(
        seed=seed,
        condition="B (RSA enabled, p=0)",
        s_star=result.s_star,
        total_cycles=result.total_cycles,
        recovery_count=result.recovery_count,
        amnesty_event_count=result.amnesty_event_count,
        authority_uptime_cycles=result.authority_uptime_cycles,
        total_renewals=result.total_renewals,
        semantic_lapse_count=result.semantic_lapse_count,
        structural_lapse_count=result.structural_lapse_count,
        authority_availability_ppm=rsa_metrics.authority_availability_ppm,
        asymptotic_authority_availability_ppm=rsa_metrics.asymptotic_authority_availability_ppm,
        failure_class=rsa_metrics.failure_class.value,
        lapse_count=len(rsa_metrics.lapse_intervals),
        total_lapse_epochs=rsa_metrics.lapse_epochs,
        max_single_lapse_epochs=max((lapse.duration_epochs for lapse in rsa_metrics.lapse_intervals), default=0),
        epochs_evaluated=rsa_metrics.authority_epochs,
        epochs_in_lapse=rsa_metrics.lapse_epochs,
        recovery_time_histogram=rsa_metrics.recovery_time_histogram,
        rsa_total_targets=rsa_summary.get("total_targets"),
        rsa_total_flips=rsa_summary.get("total_flips"),
        rsa_observed_flip_rate_ppm=rsa_summary.get("observed_flip_rate_ppm"),
    )


def metrics_match(a: RunMetrics, b: RunMetrics) -> bool:
    """Check if two RunMetrics are equivalent (ignoring RSA-specific fields)."""
    return (
        a.s_star == b.s_star and
        a.total_cycles == b.total_cycles and
        a.recovery_count == b.recovery_count and
        a.amnesty_event_count == b.amnesty_event_count and
        a.authority_uptime_cycles == b.authority_uptime_cycles and
        a.total_renewals == b.total_renewals and
        a.semantic_lapse_count == b.semantic_lapse_count and
        a.structural_lapse_count == b.structural_lapse_count and
        a.authority_availability_ppm == b.authority_availability_ppm and
        a.asymptotic_authority_availability_ppm == b.asymptotic_authority_availability_ppm and
        a.failure_class == b.failure_class and
        a.lapse_count == b.lapse_count and
        a.total_lapse_epochs == b.total_lapse_epochs and
        a.max_single_lapse_epochs == b.max_single_lapse_epochs and
        a.epochs_evaluated == b.epochs_evaluated and
        a.epochs_in_lapse == b.epochs_in_lapse
    )


def print_header():
    """Print run header."""
    print("=" * 80)
    print("RSA v0.2 Run 0 — Baseline Reference (No Interference)")
    print("=" * 80)
    print()
    print("Execution Parameters (Frozen):")
    print(f"  max_cycles:             {FROZEN_ALS_CONFIG.max_cycles:,}")
    print(f"  renewal_check_interval: {RENEWAL_CHECK_INTERVAL}")
    print(f"  horizon_epochs:         {HORIZON_EPOCHS:,}")
    print(f"  tail_window:            {TAIL_WINDOW:,}")
    print(f"  eligibility_threshold_k: {FROZEN_ALS_CONFIG.eligibility_threshold_k}")
    print(f"  amnesty_interval:       {FROZEN_ALS_CONFIG.amnesty_interval}")
    print(f"  amnesty_decay:          {FROZEN_ALS_CONFIG.amnesty_decay}")
    print(f"  seeds:                  {SEEDS}")
    print()


def print_per_seed_table(results: List[RunMetrics], condition: str):
    """Print per-seed results table."""
    print(f"\n--- {condition} ---\n")
    print(f"{'Seed':<6} {'AA_ppm':>10} {'AAA_ppm':>10} {'Failure Class':>20} {'Lapses':>8} {'Max Lapse':>10}")
    print("-" * 70)
    for r in results:
        print(f"{r.seed:<6} {r.authority_availability_ppm:>10,} {r.asymptotic_authority_availability_ppm:>10,} "
              f"{r.failure_class:>20} {r.lapse_count:>8} {r.max_single_lapse_epochs:>10}")


def print_aggregate_summary(results: List[RunMetrics], condition: str):
    """Print aggregate summary."""
    aa_values = [r.authority_availability_ppm for r in results]
    aaa_values = [r.asymptotic_authority_availability_ppm for r in results]

    mean_aa = sum(aa_values) / len(aa_values)
    mean_aaa = sum(aaa_values) / len(aaa_values)

    # Count by failure class
    class_counts: Dict[str, int] = {}
    for r in results:
        class_counts[r.failure_class] = class_counts.get(r.failure_class, 0) + 1

    # Aggregate RTD
    agg_rtd: Dict[str, int] = {}
    for r in results:
        for bucket, count in r.recovery_time_histogram.items():
            agg_rtd[bucket] = agg_rtd.get(bucket, 0) + count

    print(f"\n--- Aggregate Summary ({condition}) ---\n")
    print(f"  Mean AA:  {mean_aa:,.0f} PPM ({mean_aa / 10000:.2f}%)")
    print(f"  Mean AAA: {mean_aaa:,.0f} PPM ({mean_aaa / 10000:.2f}%)")
    print()
    print("  Failure Class Distribution:")
    for fc, count in sorted(class_counts.items()):
        print(f"    {fc}: {count}")
    print()
    print("  RTD Aggregate (total lapses by bucket):")
    for bucket in ["1", "2", "3", "5", "10", "20", "50", "100", "200", "500", "1000", "2000", "5000", "INF"]:
        count = agg_rtd.get(bucket, 0)
        if count > 0:
            print(f"    {bucket}: {count}")


def print_rsa_integrity(results_b: List[RunMetrics]):
    """Print RSA integrity metrics for Condition B."""
    print("\n--- RSA Integrity Metrics (Condition B) ---\n")
    print(f"{'Seed':<6} {'Targets':>12} {'Flips':>10} {'Flip Rate PPM':>15}")
    print("-" * 50)
    for r in results_b:
        print(f"{r.seed:<6} {r.rsa_total_targets:>12,} {r.rsa_total_flips:>10} {r.rsa_observed_flip_rate_ppm:>15}")

    # Verify all flips are zero
    all_zero = all(r.rsa_total_flips == 0 for r in results_b)
    print()
    if all_zero:
        print("  ✓ All runs have zero flips (enabled-path equivalence confirmed)")
    else:
        print("  ✗ ERROR: Non-zero flips detected!")


def main():
    print_header()

    start_time = time.time()

    # Condition A: RSA disabled
    print("Running Condition A (RSA disabled)...")
    results_a = []
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        t0 = time.time()
        result = run_condition_a(seed)
        results_a.append(result)
        print(f"done ({time.time() - t0:.1f}s)")

    # Condition B: RSA enabled, p=0
    print("\nRunning Condition B (RSA enabled, p=0)...")
    results_b = []
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        t0 = time.time()
        result = run_condition_b(seed)
        results_b.append(result)
        print(f"done ({time.time() - t0:.1f}s)")

    elapsed = time.time() - start_time
    print(f"\nTotal execution time: {elapsed:.1f}s")

    # Print per-seed tables
    print_per_seed_table(results_a, "Condition A (RSA disabled)")
    print_per_seed_table(results_b, "Condition B (RSA enabled, p=0)")

    # Print aggregate summaries
    print_aggregate_summary(results_a, "Condition A")
    print_aggregate_summary(results_b, "Condition B")

    # Print RSA integrity
    print_rsa_integrity(results_b)

    # Verify equivalence
    print("\n" + "=" * 80)
    print("EQUIVALENCE CHECK")
    print("=" * 80)

    all_match = True
    for a, b in zip(results_a, results_b):
        if metrics_match(a, b):
            print(f"  Seed {a.seed}: ✓ MATCH")
        else:
            print(f"  Seed {a.seed}: ✗ MISMATCH")
            all_match = False

    print()
    if all_match:
        print("✓ Condition A (RSA disabled) and Condition B (RSA enabled, p=0) produced")
        print("  identical per-seed metrics.")
        print()
        print("BASELINE ESTABLISHED. Proceed to Runs 1-3.")
    else:
        print("✗ ERROR: Condition A and B do NOT match!")
        print("  DO NOT proceed to Runs 1-3 until this is resolved.")
        sys.exit(1)


if __name__ == "__main__":
    main()
