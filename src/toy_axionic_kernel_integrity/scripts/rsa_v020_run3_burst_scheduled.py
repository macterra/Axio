#!/usr/bin/env python3
"""
RSA v0.2 Run 3 — Burst-Scheduled Interference Sweep (Temporal Concentration Axis)

Measures whether temporally concentrated, non-adaptive post-verification interference
can induce asymptotic governance failure even when the average corruption rate is modest.

Model: BURST_SCHEDULED_FLIP, SEM_PASS_ONLY
Grid: period × width × p_burst = 4 × 3 × 3 = 36 settings
Seeds: [40, 41, 42, 43, 44]
Total runs: 180
"""

import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple
import statistics

# Add src to path for imports
sys.path.insert(0, str(__file__).replace("/scripts/rsa_v020_run3_burst_scheduled.py", "/src"))

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

# Preregistered grid values - DO NOT MODIFY
PERIODS = [10, 50, 100, 200]
WIDTHS = [1, 5, 10]
P_BURSTS_PPM = [50_000, 100_000, 200_000]  # 5%, 10%, 20%
PHASE_OFFSET = 0  # frozen
P_QUIET_PPM = 0   # frozen

# Seeds (fixed)
SEEDS = [40, 41, 42, 43, 44]


@dataclass
class SeedMetrics:
    """Per-seed metrics for a single run."""
    seed: int
    period: int
    width: int
    p_burst_ppm: int

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

    # Burst telemetry
    active_epochs: int
    active_targets: int
    active_flips: int
    quiet_epochs: int
    quiet_targets: int
    quiet_flips: int
    active_phase_flip_rate_ppm: int
    quiet_phase_flip_rate_ppm: int

    # Duty cycles
    duty_cycle_scheduled_ppm: int  # over horizon_epochs (canonical)
    duty_cycle_evaluated_ppm: int  # over epochs_evaluated (exposure diagnostic)

    # Pivotal flip telemetry
    pivotal_flips: int
    pivotal_rate_ppm: int

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


def compute_scheduled_duty_cycle(period: int, width: int) -> int:
    """
    Compute theoretical duty cycle based on schedule parameters.

    Returns duty cycle in PPM (parts per million).
    """
    # Count active epochs in horizon based on schedule
    active_count = 0
    for epoch in range(HORIZON_EPOCHS):
        x = (epoch + PHASE_OFFSET) % period
        if x < width:
            active_count += 1
    return active_count * 1_000_000 // HORIZON_EPOCHS


def run_single_seed(seed: int, period: int, width: int, p_burst_ppm: int) -> SeedMetrics:
    """Run a single seed with given burst schedule parameters."""

    rsa_config = RSAConfig(
        rsa_enabled=True,
        rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
        rsa_scope=RSAScope.SEM_PASS_ONLY,
        rsa_rng_stream="rsa_v020",
        rsa_burst_period_epochs=period,
        rsa_burst_width_epochs=width,
        rsa_burst_phase_offset=PHASE_OFFSET,
        rsa_p_burst_flip_ppm=p_burst_ppm,
        rsa_p_quiet_flip_ppm=P_QUIET_PPM,
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

    # Epochs evaluated = epochs with authority
    epochs_evaluated = rsa_metrics.authority_epochs
    epochs_in_lapse = rsa_metrics.lapse_epochs

    # Burst telemetry from summary
    active_targets = rsa_summary.get("active_phase_targets", 0)
    active_flips = rsa_summary.get("active_phase_flips", 0)
    active_phase_flip_rate_ppm = rsa_summary.get("active_phase_flip_rate_ppm", 0)
    quiet_targets = rsa_summary.get("quiet_phase_targets", 0)
    quiet_flips = rsa_summary.get("quiet_phase_flips", 0)
    quiet_phase_flip_rate_ppm = rsa_summary.get("quiet_phase_flip_rate_ppm", 0)

    # Count active/quiet epochs from records
    active_epochs = 0
    quiet_epochs = 0
    active_epochs_evaluated = 0
    for rec in rsa_records:
        phase = rec.get("phase")
        in_lapse = rec.get("in_lapse", False)
        if phase == "ACTIVE":
            active_epochs += 1
            if not in_lapse:
                active_epochs_evaluated += 1
        elif phase == "QUIET":
            quiet_epochs += 1

    # Duty cycles
    duty_cycle_scheduled_ppm = compute_scheduled_duty_cycle(period, width)
    duty_cycle_evaluated_ppm = (
        active_epochs_evaluated * 1_000_000 // epochs_evaluated
        if epochs_evaluated > 0 else 0
    )

    # Pivotal flips: in SEM_PASS_ONLY, every flip is pivotal
    pivotal_flips = total_flips
    pivotal_rate_ppm = 1_000_000 if total_flips > 0 else 0

    return SeedMetrics(
        seed=seed,
        period=period,
        width=width,
        p_burst_ppm=p_burst_ppm,
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
        active_epochs=active_epochs,
        active_targets=active_targets,
        active_flips=active_flips,
        quiet_epochs=quiet_epochs,
        quiet_targets=quiet_targets,
        quiet_flips=quiet_flips,
        active_phase_flip_rate_ppm=active_phase_flip_rate_ppm,
        quiet_phase_flip_rate_ppm=quiet_phase_flip_rate_ppm,
        duty_cycle_scheduled_ppm=duty_cycle_scheduled_ppm,
        duty_cycle_evaluated_ppm=duty_cycle_evaluated_ppm,
        pivotal_flips=pivotal_flips,
        pivotal_rate_ppm=pivotal_rate_ppm,
        recovery_time_histogram=rsa_metrics.recovery_time_histogram,
    )


def print_run_header():
    """Print execution header with frozen config."""
    print("=" * 110)
    print("RSA v0.2 Run 3 — Burst-Scheduled Interference Sweep (Temporal Concentration Axis)")
    print("=" * 110)
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
    print("RSA Configuration (Run 3):")
    print("  rsa_noise_model:        BURST_SCHEDULED_FLIP")
    print("  rsa_scope:              SEM_PASS_ONLY")
    print(f"  periods:                {PERIODS}")
    print(f"  widths:                 {WIDTHS}")
    print(f"  p_bursts_ppm:           {P_BURSTS_PPM}")
    print(f"  phase_offset:           {PHASE_OFFSET} (frozen)")
    print(f"  p_quiet_ppm:            {P_QUIET_PPM} (frozen)")
    print(f"  seeds:                  {SEEDS}")
    print(f"  total_settings:         {len(PERIODS) * len(WIDTHS) * len(P_BURSTS_PPM)}")
    print(f"  total_runs:             {len(PERIODS) * len(WIDTHS) * len(P_BURSTS_PPM) * len(SEEDS)}")
    print()


def print_setting_header(period: int, width: int, p_burst_ppm: int, setting_num: int, total_settings: int):
    """Print header for a grid setting."""
    duty_theoretical = width * 1_000_000 // period
    print(f"\n{'='*110}")
    print(f"Setting {setting_num}/{total_settings}: period={period}, width={width}, p_burst={p_burst_ppm:,} PPM ({p_burst_ppm/10_000:.0f}%)")
    print(f"  Theoretical duty cycle: {duty_theoretical:,} PPM ({duty_theoretical/10_000:.1f}%)")
    print(f"  Theoretical avg rate:   {p_burst_ppm * duty_theoretical // 1_000_000:,} PPM")
    print(f"{'='*110}")


def print_per_seed_table(results: List[SeedMetrics]):
    """Print per-seed results table for a given setting."""
    print(f"\n{'Seed':<6} {'AA_ppm':>10} {'AAA_ppm':>10} {'Failure Class':>22} "
          f"{'Lapses':>8} {'Max_Lap':>8} {'Flips':>8} {'Act_Rate':>10} {'DC_Sched':>10} {'DC_Eval':>10}")
    print("-" * 120)

    for r in results:
        print(f"{r.seed:<6} {r.authority_availability_ppm:>10,} {r.asymptotic_authority_availability_ppm:>10,} "
              f"{r.failure_class:>22} {r.lapse_count:>8} "
              f"{r.max_single_lapse_epochs:>8} {r.total_flips:>8} "
              f"{r.active_phase_flip_rate_ppm:>10,} "
              f"{r.duty_cycle_scheduled_ppm:>10,} {r.duty_cycle_evaluated_ppm:>10,}")


def print_aggregate_summary(results: List[SeedMetrics]):
    """Print aggregate summary for a given setting."""
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

    print(f"\n  Aggregate Summary:")
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


def print_burst_telemetry(results: List[SeedMetrics]):
    """Print burst telemetry for a given setting."""
    total_targets = sum(r.total_targets for r in results)
    total_flips = sum(r.total_flips for r in results)
    total_active_targets = sum(r.active_targets for r in results)
    total_active_flips = sum(r.active_flips for r in results)
    total_quiet_targets = sum(r.quiet_targets for r in results)
    total_quiet_flips = sum(r.quiet_flips for r in results)
    epochs_evaluated = sum(r.epochs_evaluated for r in results)
    epochs_in_lapse = sum(r.epochs_in_lapse for r in results)

    # Use first result for scheduled duty cycle (same for all seeds)
    duty_cycle_scheduled = results[0].duty_cycle_scheduled_ppm
    p_burst = results[0].p_burst_ppm

    # Aggregate evaluated duty cycle
    total_active_epochs_evaluated = sum(
        r.active_targets for r in results  # active_targets ≈ active epochs evaluated
    )
    duty_cycle_evaluated = (
        total_active_epochs_evaluated * 1_000_000 // epochs_evaluated
        if epochs_evaluated > 0 else 0
    )

    # Flip rates
    active_flip_rate = total_active_flips * 1_000_000 // total_active_targets if total_active_targets > 0 else 0
    quiet_flip_rate = total_quiet_flips * 1_000_000 // total_quiet_targets if total_quiet_targets > 0 else 0
    global_flip_rate = total_flips * 1_000_000 // total_targets if total_targets > 0 else 0

    # Average rates
    scheduled_avg_rate = p_burst * duty_cycle_scheduled // 1_000_000
    effective_avg_rate = active_flip_rate * duty_cycle_evaluated // 1_000_000

    print(f"\n  Burst Telemetry:")
    print(f"    duty_cycle_scheduled_ppm:  {duty_cycle_scheduled:,} (over horizon)")
    print(f"    duty_cycle_evaluated_ppm:  {duty_cycle_evaluated:,} (over evaluated epochs)")
    print(f"    active_phase_flip_rate:    {active_flip_rate:,} PPM")
    print(f"    quiet_phase_flip_rate:     {quiet_flip_rate:,} PPM (should be 0)")
    print(f"    global_observed_rate:      {global_flip_rate:,} PPM")
    print()
    print(f"    scheduled_avg_rate:        {scheduled_avg_rate:,} PPM (p_burst × duty_scheduled)")
    print(f"    effective_avg_rate:        {effective_avg_rate:,} PPM (active_rate × duty_evaluated)")
    print()
    print(f"    total_targets:             {total_targets:,}")
    print(f"    total_flips:               {total_flips:,}")
    print(f"    active_targets:            {total_active_targets:,}")
    print(f"    active_flips:              {total_active_flips:,}")
    print(f"    epochs_evaluated:          {epochs_evaluated:,}")
    print(f"    epochs_in_lapse:           {epochs_in_lapse:,}")


def print_grid_summary(all_results: Dict[Tuple[int, int, int], List[SeedMetrics]]):
    """Print final summary table across all grid settings."""
    print("\n" + "=" * 130)
    print("GRID SUMMARY")
    print("=" * 130)

    # Get baseline from p=0 equivalent (period=10, width=1, p_burst=50000 at lowest)
    # Actually, use the first setting as reference since we don't have p=0

    print(f"\n{'Period':>8} {'Width':>6} {'p_burst':>10} {'DC_Sched':>10} {'Mean_AA':>12} {'Mean_AAA':>12} "
          f"{'Mean_Lap':>10} {'Mean_Max':>10} {'Eff_Rate':>10} {'Classes':>14}")
    print("-" * 130)

    for period in PERIODS:
        for width in WIDTHS:
            for p_burst in P_BURSTS_PPM:
                key = (period, width, p_burst)
                results = all_results[key]

                mean_aa = statistics.mean([r.authority_availability_ppm for r in results])
                mean_aaa = statistics.mean([r.asymptotic_authority_availability_ppm for r in results])
                mean_lapses = statistics.mean([r.lapse_count for r in results])
                mean_max_lapse = statistics.mean([r.max_single_lapse_epochs for r in results])
                duty_sched = results[0].duty_cycle_scheduled_ppm

                # Effective average rate
                total_active_flips = sum(r.active_flips for r in results)
                total_active_targets = sum(r.active_targets for r in results)
                active_rate = total_active_flips * 1_000_000 // total_active_targets if total_active_targets > 0 else 0
                eff_rate = active_rate * duty_sched // 1_000_000

                # Class summary
                class_counts = {}
                for r in results:
                    c = r.failure_class[0]  # First letter
                    class_counts[c] = class_counts.get(c, 0) + 1
                class_str = "/".join(f"{class_counts.get(c, 0)}{c}" for c in ["S", "B", "T", "A", "X"])

                print(f"{period:>8} {width:>6} {p_burst:>10,} {duty_sched:>10,} "
                      f"{mean_aa:>12,.0f} {mean_aaa:>12,.0f} {mean_lapses:>10.1f} "
                      f"{mean_max_lapse:>10.1f} {eff_rate:>10,} {class_str:>14}")


def main():
    print_run_header()

    start_time = time.time()
    all_results: Dict[Tuple[int, int, int], List[SeedMetrics]] = {}

    total_settings = len(PERIODS) * len(WIDTHS) * len(P_BURSTS_PPM)
    setting_num = 0

    for period in PERIODS:
        for width in WIDTHS:
            for p_burst in P_BURSTS_PPM:
                setting_num += 1
                print_setting_header(period, width, p_burst, setting_num, total_settings)

                results = []
                for seed in SEEDS:
                    print(f"  Seed {seed}...", end=" ", flush=True)
                    t0 = time.time()
                    result = run_single_seed(seed, period, width, p_burst)
                    results.append(result)
                    print(f"done ({time.time() - t0:.1f}s)")

                key = (period, width, p_burst)
                all_results[key] = results

                # Print detailed results for this setting
                print_per_seed_table(results)
                print_aggregate_summary(results)
                print_burst_telemetry(results)

    elapsed = time.time() - start_time

    # Final grid summary
    print_grid_summary(all_results)

    print(f"\n{'='*110}")
    print(f"Run 3 complete. Total execution time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"Settings: {total_settings}, Seeds: {len(SEEDS)}, Total runs: {total_settings * len(SEEDS)}")
    print(f"{'='*110}")


if __name__ == "__main__":
    main()
