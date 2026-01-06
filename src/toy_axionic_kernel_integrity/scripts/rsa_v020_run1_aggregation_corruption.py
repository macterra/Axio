#!/usr/bin/env python3
"""
RSA v0.2 Run 1 — Aggregation-Point Corruption Sweep (SEM_PASS Axis)

Measures how AKI v0.8 governance robustness responds when only the aggregation
wire SEM_PASS is corrupted post-verification under a non-adaptive, semantic-free
interference process.

Model: AGG_FLIP_BERNOULLI, SEM_PASS_ONLY
Sweep: rsa_p_flip_ppm ∈ {0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000}
Seeds: [40, 41, 42, 43, 44]
"""

import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics

# Add src to path for imports
sys.path.insert(0, str(__file__).replace("/scripts/rsa_v020_run1_aggregation_corruption.py", "/src"))

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

# Preregistered sweep values (PPM) - DO NOT MODIFY
SWEEP_VALUES_PPM = [0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000]

# Seeds (fixed)
SEEDS = [40, 41, 42, 43, 44]


@dataclass
class SeedMetrics:
    """Per-seed metrics for a single run."""
    seed: int
    p_flip_ppm: int

    # Governance metrics
    authority_availability_ppm: int
    asymptotic_authority_availability_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    max_single_lapse_epochs: int
    epochs_evaluated: int
    epochs_in_lapse: int

    # RSA integrity metrics
    total_targets: int
    total_flips: int
    observed_flip_rate_ppm: int
    expected_flip_rate_ppm: int

    # Pivotal flip telemetry
    pivotal_flips: int
    pivotal_rate_ppm: int

    # Flip exposure (sanity check)
    flip_rate_per_evaluated_epoch_ppm: int

    # RTD
    recovery_time_histogram: Dict[str, int]


def build_authority_timeline(result) -> List[bool]:
    """
    Build authority timeline from semantic epoch records.

    Returns list of booleans: True if authority active, False if in lapse.
    """
    epochs = HORIZON_EPOCHS
    timeline = [False] * epochs

    for rec in result.semantic_epoch_records:
        cycle = rec.get("cycle", 0)
        global_epoch = cycle // RENEWAL_CHECK_INTERVAL
        if 0 <= global_epoch < epochs:
            timeline[global_epoch] = True

    return timeline


def run_single_seed(seed: int, p_flip_ppm: int) -> SeedMetrics:
    """Run a single seed at a given flip rate."""

    rsa_config = RSAConfig(
        rsa_enabled=True,
        rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
        rsa_scope=RSAScope.SEM_PASS_ONLY,
        rsa_rng_stream="rsa_v020",
        rsa_p_flip_ppm=p_flip_ppm,
    )

    harness = ALSHarnessV080(seed=seed, config=FROZEN_ALS_CONFIG, rsa_config=rsa_config)
    result = harness.run()

    # Build authority timeline and compute RSA metrics
    timeline = build_authority_timeline(result)
    rsa_metrics = compute_rsa_metrics(timeline)

    # Extract RSA telemetry
    rsa_summary = result.rsa["summary"] if result.rsa else {}

    total_targets = rsa_summary.get("total_targets", 0)
    total_flips = rsa_summary.get("total_flips", 0)
    observed_flip_rate_ppm = rsa_summary.get("observed_flip_rate_ppm", 0)

    # Epochs evaluated = epochs with authority (where RSA could target)
    epochs_evaluated = rsa_metrics.authority_epochs
    epochs_in_lapse = rsa_metrics.lapse_epochs

    # Pivotal flips: in SEM_PASS_ONLY, every flip is pivotal by construction
    pivotal_flips = total_flips
    pivotal_rate_ppm = 1_000_000 if total_flips > 0 else 0

    # Flip exposure: flips per evaluated epoch
    flip_rate_per_evaluated_epoch_ppm = (
        total_flips * 1_000_000 // epochs_evaluated if epochs_evaluated > 0 else 0
    )

    return SeedMetrics(
        seed=seed,
        p_flip_ppm=p_flip_ppm,
        authority_availability_ppm=rsa_metrics.authority_availability_ppm,
        asymptotic_authority_availability_ppm=rsa_metrics.asymptotic_authority_availability_ppm,
        failure_class=rsa_metrics.failure_class.value,
        lapse_count=len(rsa_metrics.lapse_intervals),
        total_lapse_epochs=rsa_metrics.lapse_epochs,
        max_single_lapse_epochs=max((lapse.duration_epochs for lapse in rsa_metrics.lapse_intervals), default=0),
        epochs_evaluated=epochs_evaluated,
        epochs_in_lapse=epochs_in_lapse,
        total_targets=total_targets,
        total_flips=total_flips,
        observed_flip_rate_ppm=observed_flip_rate_ppm,
        expected_flip_rate_ppm=p_flip_ppm,
        pivotal_flips=pivotal_flips,
        pivotal_rate_ppm=pivotal_rate_ppm,
        flip_rate_per_evaluated_epoch_ppm=flip_rate_per_evaluated_epoch_ppm,
        recovery_time_histogram=rsa_metrics.recovery_time_histogram,
    )


def print_run_header():
    """Print execution header with frozen config."""
    print("=" * 90)
    print("RSA v0.2 Run 1 — Aggregation-Point Corruption Sweep (SEM_PASS Axis)")
    print("=" * 90)
    print()
    print("Frozen AKI Configuration:")
    print(f"  max_cycles:             {FROZEN_ALS_CONFIG.max_cycles:,}")
    print(f"  renewal_check_interval: {RENEWAL_CHECK_INTERVAL}")
    print(f"  horizon_epochs:         {HORIZON_EPOCHS:,}")
    print(f"  tail_window:            {TAIL_WINDOW:,}")
    print(f"  eligibility_threshold_k: {FROZEN_ALS_CONFIG.eligibility_threshold_k}")
    print(f"  amnesty_interval:       {FROZEN_ALS_CONFIG.amnesty_interval}")
    print(f"  amnesty_decay:          {FROZEN_ALS_CONFIG.amnesty_decay}")
    print()
    print("RSA Configuration (Run 1):")
    print("  rsa_noise_model:        AGG_FLIP_BERNOULLI")
    print("  rsa_scope:              SEM_PASS_ONLY")
    print(f"  sweep_values_ppm:       {SWEEP_VALUES_PPM}")
    print(f"  seeds:                  {SEEDS}")
    print()


def print_per_seed_table(results: List[SeedMetrics], p_flip_ppm: int):
    """Print per-seed results table for a given flip rate."""
    print(f"\n--- p_flip_ppm = {p_flip_ppm:,} ({p_flip_ppm / 10_000:.2f}%) ---\n")

    # Header
    print(f"{'Seed':<6} {'AA_ppm':>10} {'AAA_ppm':>10} {'Failure Class':>22} "
          f"{'Lapses':>8} {'Lapse_ep':>10} {'Max_Lapse':>10} "
          f"{'Obs_flip':>10} {'Pivotal':>10}")
    print("-" * 110)

    for r in results:
        print(f"{r.seed:<6} {r.authority_availability_ppm:>10,} {r.asymptotic_authority_availability_ppm:>10,} "
              f"{r.failure_class:>22} {r.lapse_count:>8} {r.total_lapse_epochs:>10} "
              f"{r.max_single_lapse_epochs:>10} {r.observed_flip_rate_ppm:>10,} "
              f"{r.pivotal_rate_ppm:>10,}")


def print_aggregate_summary(results: List[SeedMetrics], p_flip_ppm: int):
    """Print aggregate summary for a given flip rate."""
    aa_values = [r.authority_availability_ppm for r in results]
    aaa_values = [r.asymptotic_authority_availability_ppm for r in results]
    max_lapse_values = [r.max_single_lapse_epochs for r in results]

    mean_aa = statistics.mean(aa_values)
    std_aa = statistics.stdev(aa_values) if len(aa_values) > 1 else 0
    mean_aaa = statistics.mean(aaa_values)
    std_aaa = statistics.stdev(aaa_values) if len(aaa_values) > 1 else 0

    # Failure class counts
    class_counts: Dict[str, int] = {}
    for r in results:
        class_counts[r.failure_class] = class_counts.get(r.failure_class, 0) + 1

    # Aggregate RTD
    agg_rtd: Dict[str, int] = {}
    for r in results:
        for bucket, count in r.recovery_time_histogram.items():
            agg_rtd[bucket] = agg_rtd.get(bucket, 0) + count

    print(f"\n  Aggregate (p_flip_ppm={p_flip_ppm:,}):")
    print(f"    Mean AA:  {mean_aa:,.0f} ± {std_aa:,.0f} PPM ({mean_aa / 10_000:.2f}%)")
    print(f"    Mean AAA: {mean_aaa:,.0f} ± {std_aaa:,.0f} PPM ({mean_aaa / 10_000:.2f}%)")
    print(f"    Max lapse range: {min(max_lapse_values)} - {max(max_lapse_values)} epochs")
    print()
    print("    Failure Class Distribution:")
    for fc in ["STABLE_AUTHORITY", "BOUNDED_DEGRADATION", "STRUCTURAL_THRASHING",
               "ASYMPTOTIC_DOS", "TERMINAL_COLLAPSE"]:
        count = class_counts.get(fc, 0)
        if count > 0:
            print(f"      {fc}: {count}")

    # RTD summary (compact)
    print()
    print("    RTD (total lapses by bucket):", end=" ")
    rtd_parts = []
    for bucket in ["1", "2", "3", "5", "10", "20", "50", "100", "200", "500", "1000", "2000", "5000", "INF"]:
        count = agg_rtd.get(bucket, 0)
        if count > 0:
            rtd_parts.append(f"≤{bucket}:{count}")
    print(", ".join(rtd_parts) if rtd_parts else "(none)")


def print_rsa_integrity(results: List[SeedMetrics], p_flip_ppm: int):
    """Print RSA integrity metrics for a given flip rate."""
    total_targets = sum(r.total_targets for r in results)
    total_flips = sum(r.total_flips for r in results)
    total_pivotal = sum(r.pivotal_flips for r in results)
    epochs_evaluated = sum(r.epochs_evaluated for r in results)
    epochs_in_lapse = sum(r.epochs_in_lapse for r in results)

    observed_rate = total_flips * 1_000_000 // total_targets if total_targets > 0 else 0
    flip_per_eval = total_flips * 1_000_000 // epochs_evaluated if epochs_evaluated > 0 else 0
    pivotal_rate = total_pivotal * 1_000_000 // total_flips if total_flips > 0 else 0

    print(f"\n  RSA Integrity (p_flip_ppm={p_flip_ppm:,}):")
    print(f"    total_targets:       {total_targets:,}")
    print(f"    total_flips:         {total_flips:,}")
    print(f"    observed_flip_ppm:   {observed_rate:,}")
    print(f"    expected_flip_ppm:   {p_flip_ppm:,}")
    print(f"    epochs_evaluated:    {epochs_evaluated:,}")
    print(f"    epochs_in_lapse:     {epochs_in_lapse:,}")
    print(f"    flip_per_eval_ppm:   {flip_per_eval:,}")
    print(f"    pivotal_flips:       {total_pivotal:,}")
    print(f"    pivotal_rate_ppm:    {pivotal_rate:,}")

    # Sanity checks
    rate_delta = abs(observed_rate - p_flip_ppm)
    rate_tolerance = max(1000, p_flip_ppm // 10)  # 10% or 1000 PPM tolerance

    if p_flip_ppm > 0:
        if rate_delta <= rate_tolerance:
            print(f"    ✓ Observed flip rate within tolerance of expected")
        else:
            print(f"    ⚠ Observed flip rate deviates by {rate_delta:,} PPM from expected")

    if total_flips > 0 and pivotal_rate != 1_000_000:
        print(f"    ⚠ Pivotal rate is not 100% - unexpected for SEM_PASS_ONLY")


def print_sweep_summary(all_results: Dict[int, List[SeedMetrics]]):
    """Print final summary table across all sweep values."""
    print("\n" + "=" * 90)
    print("SWEEP SUMMARY")
    print("=" * 90)

    print(f"\n{'p_flip':>10} {'Mean_AA':>12} {'Mean_AAA':>12} {'ΔAA_base':>10} "
          f"{'Mean_Lapses':>12} {'Mean_MaxLap':>12} {'Classes':>20}")
    print("-" * 90)

    # Baseline values from p=0
    baseline_aa = statistics.mean([r.authority_availability_ppm for r in all_results[0]])
    baseline_aaa = statistics.mean([r.asymptotic_authority_availability_ppm for r in all_results[0]])

    for p in SWEEP_VALUES_PPM:
        results = all_results[p]
        mean_aa = statistics.mean([r.authority_availability_ppm for r in results])
        mean_aaa = statistics.mean([r.asymptotic_authority_availability_ppm for r in results])
        delta_aa = mean_aa - baseline_aa
        mean_lapses = statistics.mean([r.lapse_count for r in results])
        mean_max_lapse = statistics.mean([r.max_single_lapse_epochs for r in results])

        # Class summary
        class_counts = {}
        for r in results:
            c = r.failure_class[0]  # First letter
            class_counts[c] = class_counts.get(c, 0) + 1
        class_str = "/".join(f"{class_counts.get(c, 0)}{c}" for c in ["S", "B", "T", "A", "X"])

        delta_str = f"{delta_aa:+,.0f}" if p > 0 else "baseline"
        print(f"{p:>10,} {mean_aa:>12,.0f} {mean_aaa:>12,.0f} {delta_str:>10} "
              f"{mean_lapses:>12.1f} {mean_max_lapse:>12.1f} {class_str:>20}")


def main():
    print_run_header()

    start_time = time.time()
    all_results: Dict[int, List[SeedMetrics]] = {}

    for p_flip_ppm in SWEEP_VALUES_PPM:
        print(f"\n{'='*90}")
        print(f"Running p_flip_ppm = {p_flip_ppm:,} ({p_flip_ppm / 10_000:.2f}%)")
        print(f"{'='*90}")

        results = []
        for seed in SEEDS:
            print(f"  Seed {seed}...", end=" ", flush=True)
            t0 = time.time()
            result = run_single_seed(seed, p_flip_ppm)
            results.append(result)
            print(f"done ({time.time() - t0:.1f}s)")

        all_results[p_flip_ppm] = results

        # Print detailed results for this sweep point
        print_per_seed_table(results, p_flip_ppm)
        print_aggregate_summary(results, p_flip_ppm)
        print_rsa_integrity(results, p_flip_ppm)

    elapsed = time.time() - start_time

    # Final sweep summary
    print_sweep_summary(all_results)

    print(f"\n{'='*90}")
    print(f"Run 1 complete. Total execution time: {elapsed:.1f}s")
    print(f"{'='*90}")


if __name__ == "__main__":
    main()
