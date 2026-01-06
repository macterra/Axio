#!/usr/bin/env python3
"""
RSA v0.2 Run 2 — Commitment-Correlated Noise Sweep (Single-Key Axis)

Measures whether persistent impairment of a single obligation wire (C1_OK) can
defeat constitutional recovery, or whether it produces only bounded degradation
under RSA v0.2 constraints.

Model: COMMITMENT_KEYED_FLIP, PER_KEY
Target: C1 (frozen)
Sweep: rsa_p_target_flip_ppm ∈ {0, 500, 1_000, 5_000, 10_000, 20_000, 50_000, 100_000}
Seeds: [40, 41, 42, 43, 44]
"""

import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics

# Add src to path for imports
sys.path.insert(0, str(__file__).replace("/scripts/rsa_v020_run2_commitment_correlated.py", "/src"))

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
# Run 2 sweep: 0% to 10% on single key
SWEEP_VALUES_PPM = [0, 500, 1_000, 5_000, 10_000, 20_000, 50_000, 100_000]

# Target key (frozen for Run 2)
TARGET_KEY = "C1"

# Seeds (fixed)
SEEDS = [40, 41, 42, 43, 44]


@dataclass
class SeedMetrics:
    """Per-seed metrics for a single run."""
    seed: int
    p_target_flip_ppm: int

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

    # Flips by key (must be only C1)
    flips_by_key: Dict[str, int]

    # Pivotal flip telemetry
    key_pivotal_flips: int  # C1_OK_raw != C1_OK
    key_pivotal_rate_ppm: int
    sem_pass_pivotal_flips: int  # SEM_PASS_raw != SEM_PASS_corrupted
    sem_pass_pivotal_rate_ppm: int

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


def run_single_seed(seed: int, p_target_flip_ppm: int) -> SeedMetrics:
    """Run a single seed at a given flip rate."""

    rsa_config = RSAConfig(
        rsa_enabled=True,
        rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
        rsa_scope=RSAScope.PER_KEY,
        rsa_rng_stream="rsa_v020",
        rsa_target_key=TARGET_KEY,
        rsa_p_target_flip_ppm=p_target_flip_ppm,
    )

    harness = ALSHarnessV080(seed=seed, config=FROZEN_ALS_CONFIG, rsa_config=rsa_config)
    result = harness.run()

    # Build authority timeline and compute RSA metrics
    timeline = build_authority_timeline(result)
    rsa_metrics = compute_rsa_metrics(timeline)

    # Extract RSA telemetry
    rsa_summary = result.rsa["summary"] if result.rsa else {}
    rsa_records = result.rsa.get("epoch_records", []) if result.rsa else []

    total_targets = rsa_summary.get("total_targets", 0)
    total_flips = rsa_summary.get("total_flips", 0)
    observed_flip_rate_ppm = rsa_summary.get("observed_flip_rate_ppm", 0)

    # Epochs evaluated = epochs with authority (where RSA could target)
    epochs_evaluated = rsa_metrics.authority_epochs
    epochs_in_lapse = rsa_metrics.lapse_epochs

    # Flips by key from summary (already aggregated)
    flips_by_key = rsa_summary.get("flips_by_key", {"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0})

    # Key pivotal flips: C1_OK_raw != C1_OK (same as flips for COMMITMENT_KEYED_FLIP)
    key_pivotal_flips = flips_by_key.get(TARGET_KEY, 0)
    key_pivotal_rate_ppm = 1_000_000 if key_pivotal_flips > 0 else 0

    # SEM_PASS pivotal flips: count where SEM_PASS_raw != SEM_PASS_corrupted
    sem_pass_pivotal_flips = 0
    for rec in rsa_records:
        sem_pass_raw = rec.get("sem_pass_raw")
        sem_pass_corrupted = rec.get("sem_pass_corrupted")
        if sem_pass_raw is not None and sem_pass_corrupted is not None:
            if sem_pass_raw != sem_pass_corrupted:
                sem_pass_pivotal_flips += 1
    sem_pass_pivotal_rate_ppm = (
        sem_pass_pivotal_flips * 1_000_000 // total_flips if total_flips > 0 else 0
    )

    return SeedMetrics(
        seed=seed,
        p_target_flip_ppm=p_target_flip_ppm,
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
        expected_flip_rate_ppm=p_target_flip_ppm,
        flips_by_key=flips_by_key,
        key_pivotal_flips=key_pivotal_flips,
        key_pivotal_rate_ppm=key_pivotal_rate_ppm,
        sem_pass_pivotal_flips=sem_pass_pivotal_flips,
        sem_pass_pivotal_rate_ppm=sem_pass_pivotal_rate_ppm,
        recovery_time_histogram=rsa_metrics.recovery_time_histogram,
    )


def print_run_header():
    """Print execution header with frozen config."""
    print("=" * 100)
    print("RSA v0.2 Run 2 — Commitment-Correlated Noise Sweep (Single-Key Axis)")
    print("=" * 100)
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
    print("RSA Configuration (Run 2):")
    print("  rsa_noise_model:        COMMITMENT_KEYED_FLIP")
    print("  rsa_scope:              PER_KEY")
    print(f"  rsa_target_key:         {TARGET_KEY}")
    print(f"  sweep_values_ppm:       {SWEEP_VALUES_PPM}")
    print(f"  seeds:                  {SEEDS}")
    print()


def check_invariants(results: List[SeedMetrics], p_target_flip_ppm: int) -> bool:
    """
    Check Run 2 telemetry invariants per spec.

    Returns True if all invariants pass.
    """
    all_pass = True

    for r in results:
        # Invariant 1: total_targets == epochs_evaluated
        if r.total_targets != r.epochs_evaluated:
            print(f"    ⚠ Seed {r.seed}: total_targets ({r.total_targets}) != epochs_evaluated ({r.epochs_evaluated})")
            all_pass = False

        # Invariant 2: epochs_evaluated + epochs_in_lapse == horizon_epochs
        total_epochs = r.epochs_evaluated + r.epochs_in_lapse
        if total_epochs != HORIZON_EPOCHS:
            print(f"    ⚠ Seed {r.seed}: epochs_evaluated + epochs_in_lapse ({total_epochs}) != horizon_epochs ({HORIZON_EPOCHS})")
            all_pass = False

        # Invariant 3: sum(flips_by_key.values()) == total_flips
        sum_flips = sum(r.flips_by_key.values())
        if sum_flips != r.total_flips:
            print(f"    ⚠ Seed {r.seed}: sum(flips_by_key) ({sum_flips}) != total_flips ({r.total_flips})")
            all_pass = False

        # Invariant 4: flips only under target key
        non_target_flips = sum(v for k, v in r.flips_by_key.items() if k != TARGET_KEY)
        if non_target_flips > 0:
            print(f"    ⚠ Seed {r.seed}: non-target key flips detected: {r.flips_by_key}")
            all_pass = False

    if all_pass:
        print("    ✓ All telemetry invariants pass")

    return all_pass


def print_per_seed_table(results: List[SeedMetrics], p_target_flip_ppm: int):
    """Print per-seed results table for a given flip rate."""
    print(f"\n--- p_target_flip_ppm = {p_target_flip_ppm:,} ({p_target_flip_ppm / 10_000:.2f}%) ---\n")

    # Header
    print(f"{'Seed':<6} {'AA_ppm':>10} {'AAA_ppm':>10} {'Failure Class':>22} "
          f"{'Lapses':>8} {'Max_Lapse':>10} "
          f"{'Flips':>8} {'Key_Piv':>10} {'SEM_Piv':>10}")
    print("-" * 115)

    for r in results:
        print(f"{r.seed:<6} {r.authority_availability_ppm:>10,} {r.asymptotic_authority_availability_ppm:>10,} "
              f"{r.failure_class:>22} {r.lapse_count:>8} "
              f"{r.max_single_lapse_epochs:>10} {r.total_flips:>8} "
              f"{r.key_pivotal_flips:>10} {r.sem_pass_pivotal_flips:>10}")


def print_aggregate_summary(results: List[SeedMetrics], p_target_flip_ppm: int):
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

    print(f"\n  Aggregate (p_target_flip_ppm={p_target_flip_ppm:,}):")
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


def print_rsa_integrity(results: List[SeedMetrics], p_target_flip_ppm: int):
    """Print RSA integrity metrics for a given flip rate."""
    total_targets = sum(r.total_targets for r in results)
    total_flips = sum(r.total_flips for r in results)
    total_key_pivotal = sum(r.key_pivotal_flips for r in results)
    total_sem_pivotal = sum(r.sem_pass_pivotal_flips for r in results)
    epochs_evaluated = sum(r.epochs_evaluated for r in results)
    epochs_in_lapse = sum(r.epochs_in_lapse for r in results)

    # Aggregate flips_by_key
    agg_flips_by_key = {"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0}
    for r in results:
        for key, count in r.flips_by_key.items():
            agg_flips_by_key[key] = agg_flips_by_key.get(key, 0) + count

    observed_rate = total_flips * 1_000_000 // total_targets if total_targets > 0 else 0
    key_pivotal_rate = 1_000_000 if total_flips > 0 else 0  # Always 100% for key flips
    sem_pivotal_rate = total_sem_pivotal * 1_000_000 // total_flips if total_flips > 0 else 0

    print(f"\n  RSA Integrity (p_target_flip_ppm={p_target_flip_ppm:,}):")
    print(f"    total_targets:       {total_targets:,}")
    print(f"    total_flips:         {total_flips:,}")
    print(f"    observed_flip_ppm:   {observed_rate:,}")
    print(f"    expected_flip_ppm:   {p_target_flip_ppm:,}")
    print(f"    epochs_evaluated:    {epochs_evaluated:,}")
    print(f"    epochs_in_lapse:     {epochs_in_lapse:,}")
    print()
    print(f"    flips_by_key:        {agg_flips_by_key}")
    print(f"    key_pivotal_flips:   {total_key_pivotal:,} ({key_pivotal_rate:,} PPM)")
    print(f"    sem_pivotal_flips:   {total_sem_pivotal:,} ({sem_pivotal_rate:,} PPM)")

    # Sanity checks
    rate_delta = abs(observed_rate - p_target_flip_ppm)
    rate_tolerance = max(1000, p_target_flip_ppm // 10)  # 10% or 1000 PPM tolerance

    if p_target_flip_ppm > 0:
        if rate_delta <= rate_tolerance:
            print(f"    ✓ Observed flip rate within tolerance of expected")
        else:
            print(f"    ⚠ Observed flip rate deviates by {rate_delta:,} PPM from expected")

    # Check that only target key has flips
    non_target_flips = sum(v for k, v in agg_flips_by_key.items() if k != TARGET_KEY)
    if non_target_flips == 0:
        print(f"    ✓ Flips only under target key ({TARGET_KEY})")
    else:
        print(f"    ⚠ Non-target key flips detected: {non_target_flips}")


def print_sweep_summary(all_results: Dict[int, List[SeedMetrics]]):
    """Print final summary table across all sweep values."""
    print("\n" + "=" * 100)
    print("SWEEP SUMMARY")
    print("=" * 100)

    print(f"\n{'p_flip':>10} {'Mean_AA':>12} {'Mean_AAA':>12} {'ΔAA_base':>10} "
          f"{'Mean_Lapses':>12} {'Mean_MaxLap':>12} {'SEM_Piv%':>10} {'Classes':>14}")
    print("-" * 100)

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

        # SEM_PASS pivotal percentage
        total_flips = sum(r.total_flips for r in results)
        total_sem_pivotal = sum(r.sem_pass_pivotal_flips for r in results)
        sem_piv_pct = (total_sem_pivotal * 100 / total_flips) if total_flips > 0 else 0

        # Class summary
        class_counts = {}
        for r in results:
            c = r.failure_class[0]  # First letter
            class_counts[c] = class_counts.get(c, 0) + 1
        class_str = "/".join(f"{class_counts.get(c, 0)}{c}" for c in ["S", "B", "T", "A", "X"])

        delta_str = f"{delta_aa:+,.0f}" if p > 0 else "baseline"
        print(f"{p:>10,} {mean_aa:>12,.0f} {mean_aaa:>12,.0f} {delta_str:>10} "
              f"{mean_lapses:>12.1f} {mean_max_lapse:>12.1f} {sem_piv_pct:>9.1f}% {class_str:>14}")


def main():
    print_run_header()

    start_time = time.time()
    all_results: Dict[int, List[SeedMetrics]] = {}

    for p_target_flip_ppm in SWEEP_VALUES_PPM:
        print(f"\n{'='*100}")
        print(f"Running p_target_flip_ppm = {p_target_flip_ppm:,} ({p_target_flip_ppm / 10_000:.2f}%)")
        print(f"{'='*100}")

        results = []
        for seed in SEEDS:
            print(f"  Seed {seed}...", end=" ", flush=True)
            t0 = time.time()
            result = run_single_seed(seed, p_target_flip_ppm)
            results.append(result)
            print(f"done ({time.time() - t0:.1f}s)")

        all_results[p_target_flip_ppm] = results

        # Check invariants before printing detailed results
        print("\n  Invariant checks:")
        check_invariants(results, p_target_flip_ppm)

        # Print detailed results for this sweep point
        print_per_seed_table(results, p_target_flip_ppm)
        print_aggregate_summary(results, p_target_flip_ppm)
        print_rsa_integrity(results, p_target_flip_ppm)

    elapsed = time.time() - start_time

    # Final sweep summary
    print_sweep_summary(all_results)

    print(f"\n{'='*100}")
    print(f"Run 2 complete. Total execution time: {elapsed:.1f}s")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()
