#!/usr/bin/env python3
"""
RSA v0.1 Run 1: Semantic Baseline Sweep (SV Axis).

Measure how AKI v0.8 governance robustness under RSA noise depends on the
baseline semantic pass regime.

Single independent variable: SVConfig.per_ci_pass_rate_ppm
Fixed: RSA at 10% flip rate (PER_CI, FLIP_BERNOULLI)

Per instructions §1-7.
"""

import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import statistics

# Add src to path for development
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from toy_aki.als.harness import ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.synthetic_verifier import ALSHarnessV080_SV, SVConfig


@dataclass
class SeedResult:
    """Per-seed result with full metrics."""

    seed: int

    # Governance metrics
    total_cycles: int = 0
    epochs_evaluated: int = 0
    lapse_event_count: int = 0
    lapse_epoch_count_total: int = 0
    max_single_lapse_epochs: int = 0
    authority_uptime_fraction: float = 0.0
    recovery_count: int = 0
    recovery_yield: Optional[float] = None  # If available

    # RSA metrics
    total_targets: int = 0
    total_flips: int = 0
    pivotal_flips: int = 0
    observed_ppm: int = 0

    # SV calibration (raw, pre-RSA)
    sv_c0_rate: float = 0.0
    sv_c1_rate: float = 0.0
    sv_c2_rate: float = 0.0
    sv_sem_pass_rate: float = 0.0

    # Regime classification
    regime: str = "ROBUST"


@dataclass
class BaselineResult:
    """Aggregate result for a single SV baseline point."""

    per_ci_pass_rate_ppm: int
    expected_sem_pass_rate: float

    # Per-seed results
    seed_results: List[SeedResult] = field(default_factory=list)

    # Aggregate governance metrics
    mean_lapse_event_count: float = 0.0
    std_lapse_event_count: float = 0.0
    mean_lapse_epoch_count_total: float = 0.0
    std_lapse_epoch_count_total: float = 0.0
    mean_max_single_lapse_epochs: float = 0.0
    max_max_single_lapse_epochs: int = 0  # Max across all seeds
    mean_authority_uptime: float = 0.0
    mean_recovery_count: float = 0.0

    # Aggregate RSA metrics
    sum_targets: int = 0
    sum_flips: int = 0
    sum_pivotal_flips: int = 0
    aggregate_observed_ppm: int = 0
    pivotal_rate: float = 0.0

    # SV calibration (averaged)
    mean_sv_c0_rate: float = 0.0
    mean_sv_c1_rate: float = 0.0
    mean_sv_c2_rate: float = 0.0
    mean_sv_sem_pass_rate: float = 0.0

    # Regime counts
    robust_count: int = 0
    degraded_count: int = 0
    dos_count: int = 0

    # Lapse duration distribution (for H3)
    all_lapse_durations: List[int] = field(default_factory=list)


def classify_regime(result, amnesty_interval: int) -> str:
    """
    Classify run regime per spec §4.

    - DOS_REGIME: max single lapse > 5 × amnesty_interval epochs
    - DEGRADED: lapse_fraction > 50%
    - ROBUST: otherwise
    """
    dos_threshold_epochs = 5 * amnesty_interval

    max_lapse_epochs = 0
    for lapse in result.lapse_events_v080:
        lapse_duration = lapse.get("duration_epochs", 0)
        if lapse_duration > max_lapse_epochs:
            max_lapse_epochs = lapse_duration

    if max_lapse_epochs > dos_threshold_epochs:
        return "DOS_REGIME"

    if result.lapse_fraction > 0.5:
        return "DEGRADED"

    return "ROBUST"


def get_max_single_lapse_epochs(result) -> int:
    """Get maximum single lapse duration in epochs."""
    if not result.lapse_events_v080:
        return 0
    return max(
        lapse.get("duration_epochs", 0) for lapse in result.lapse_events_v080
    )


def get_all_lapse_durations(result) -> List[int]:
    """Get list of all individual lapse durations."""
    return [
        lapse.get("duration_epochs", 0)
        for lapse in result.lapse_events_v080
        if lapse.get("duration_epochs", 0) > 0
    ]


def count_pivotal_flips(telemetry) -> int:
    """Count flips that changed SEM_PASS outcome."""
    count = 0
    for r in telemetry.epoch_records:
        if r.in_lapse:
            continue
        if r.sem_pass_raw != r.sem_pass_corrupted:
            count += 1
    return count


def run_sv_baseline_sweep():
    """Run the SV baseline sweep experiment."""
    print("=" * 78)
    print("RSA v0.1 Run 1: Semantic Baseline Sweep (SV Axis)")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 78)
    print()

    # AKI v0.8 configuration (FROZEN)
    config = ALSConfigV080(
        max_cycles=10_000,
        eligibility_threshold_k=3,
        max_successive_renewals=3,
        amnesty_interval=10,
        amnesty_decay=1,
        cta_enabled=True,
    )

    # RSA configuration (FIXED for Run 1)
    rsa_cfg = RSAConfig(
        rsa_enabled=True,
        rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
        rsa_scope=RSAScope.PER_CI,
        rsa_p_flip_ppm=100_000,  # Fixed at 10%
    )

    seeds = [40, 41, 42, 43, 44]

    # Sweep values for per_ci_pass_rate_ppm
    sweep_values = [500_000, 600_000, 700_000, 800_000, 850_000, 900_000, 950_000]

    print("Configuration:")
    print("  AKI v0.8 (FROZEN):")
    print(f"    max_cycles: {config.max_cycles}")
    print(f"    eligibility_threshold_k: {config.eligibility_threshold_k}")
    print(f"    amnesty_interval: {config.amnesty_interval}")
    print(f"    renewal_check_interval: {config.renewal_check_interval}")
    print(f"    global_epoch_max: {config.max_cycles // config.renewal_check_interval}")
    print("  RSA (FIXED):")
    print(f"    rsa_p_flip_ppm: {rsa_cfg.rsa_p_flip_ppm} (10%)")
    print(f"    rsa_scope: {rsa_cfg.rsa_scope.value}")
    print(f"    rsa_noise_model: {rsa_cfg.rsa_noise_model.value}")
    print(f"  Seeds: {seeds}")
    print(f"  SV baseline sweep: {sweep_values} PPM")
    print()

    results: List[BaselineResult] = []

    for rate_ppm in sweep_values:
        expected_sem_pass = (rate_ppm / 1_000_000) ** 3
        print(f"\n{'='*78}")
        print(f"per_ci_pass_rate_ppm = {rate_ppm} (expected SEM_PASS = {expected_sem_pass:.3f})")
        print("=" * 78)

        sv_config = SVConfig(per_ci_pass_rate_ppm=rate_ppm)

        baseline_result = BaselineResult(
            per_ci_pass_rate_ppm=rate_ppm,
            expected_sem_pass_rate=expected_sem_pass,
        )

        for seed in seeds:
            h = ALSHarnessV080_SV(
                seed=seed, config=config, sv_config=sv_config, rsa_config=rsa_cfg
            )
            result = h.run()

            # Extract governance metrics
            seed_result = SeedResult(seed=seed)
            seed_result.total_cycles = result.total_cycles
            seed_result.lapse_event_count = len(result.lapse_events_v080)
            seed_result.lapse_epoch_count_total = result.total_lapse_duration_epochs
            seed_result.max_single_lapse_epochs = get_max_single_lapse_epochs(result)
            seed_result.authority_uptime_fraction = result.authority_uptime_fraction
            seed_result.recovery_count = getattr(result, "recovery_count", seed_result.lapse_event_count)

            # Optional: recovery_yield if available
            if hasattr(result, "recovery_yield"):
                seed_result.recovery_yield = result.recovery_yield

            # Verify lapse epoch consistency
            computed_total = sum(get_all_lapse_durations(result))
            assert computed_total == seed_result.lapse_epoch_count_total, (
                f"Lapse epoch mismatch: sum={computed_total}, "
                f"total={seed_result.lapse_epoch_count_total}"
            )

            # Collect lapse durations for H3 analysis
            baseline_result.all_lapse_durations.extend(get_all_lapse_durations(result))

            # RSA metrics
            if result.rsa:
                seed_result.epochs_evaluated = result.rsa["summary"]["epochs_evaluated"]
                seed_result.total_targets = result.rsa["summary"]["total_targets"]
                seed_result.total_flips = result.rsa["summary"]["total_flips"]
                seed_result.observed_ppm = result.rsa["summary"]["observed_flip_rate_ppm"]
                seed_result.pivotal_flips = count_pivotal_flips(h._rsa_telemetry)

            # SV calibration (raw, pre-RSA)
            calib = h.get_sv_calibration()
            if calib["epochs_evaluated"] > 0:
                seed_result.sv_c0_rate = calib["c0"]["observed"]
                seed_result.sv_c1_rate = calib["c1"]["observed"]
                seed_result.sv_c2_rate = calib["c2"]["observed"]
                seed_result.sv_sem_pass_rate = calib["sem_pass"]["observed"]

            # Regime classification
            seed_result.regime = classify_regime(result, config.amnesty_interval)

            baseline_result.seed_results.append(seed_result)

            print(
                f"  Seed {seed}: lapses={seed_result.lapse_event_count}, "
                f"lapse_epochs={seed_result.lapse_epoch_count_total}, "
                f"max_lapse={seed_result.max_single_lapse_epochs}, "
                f"uptime={seed_result.authority_uptime_fraction:.1%}, "
                f"regime={seed_result.regime}"
            )

        # Compute aggregates
        n = len(seeds)

        # Governance aggregates
        lapse_counts = [sr.lapse_event_count for sr in baseline_result.seed_results]
        lapse_epochs = [sr.lapse_epoch_count_total for sr in baseline_result.seed_results]
        max_lapses = [sr.max_single_lapse_epochs for sr in baseline_result.seed_results]

        baseline_result.mean_lapse_event_count = statistics.mean(lapse_counts)
        baseline_result.std_lapse_event_count = statistics.stdev(lapse_counts) if n > 1 else 0.0
        baseline_result.mean_lapse_epoch_count_total = statistics.mean(lapse_epochs)
        baseline_result.std_lapse_epoch_count_total = statistics.stdev(lapse_epochs) if n > 1 else 0.0
        baseline_result.mean_max_single_lapse_epochs = statistics.mean(max_lapses)
        baseline_result.max_max_single_lapse_epochs = max(max_lapses)
        baseline_result.mean_authority_uptime = statistics.mean(
            sr.authority_uptime_fraction for sr in baseline_result.seed_results
        )
        baseline_result.mean_recovery_count = statistics.mean(
            sr.recovery_count for sr in baseline_result.seed_results
        )

        # RSA aggregates
        baseline_result.sum_targets = sum(sr.total_targets for sr in baseline_result.seed_results)
        baseline_result.sum_flips = sum(sr.total_flips for sr in baseline_result.seed_results)
        baseline_result.sum_pivotal_flips = sum(sr.pivotal_flips for sr in baseline_result.seed_results)

        if baseline_result.sum_targets > 0:
            baseline_result.aggregate_observed_ppm = (
                baseline_result.sum_flips * 1_000_000
            ) // baseline_result.sum_targets

        if baseline_result.sum_flips > 0:
            baseline_result.pivotal_rate = baseline_result.sum_pivotal_flips / baseline_result.sum_flips

        # SV calibration aggregates
        baseline_result.mean_sv_c0_rate = statistics.mean(
            sr.sv_c0_rate for sr in baseline_result.seed_results
        )
        baseline_result.mean_sv_c1_rate = statistics.mean(
            sr.sv_c1_rate for sr in baseline_result.seed_results
        )
        baseline_result.mean_sv_c2_rate = statistics.mean(
            sr.sv_c2_rate for sr in baseline_result.seed_results
        )
        baseline_result.mean_sv_sem_pass_rate = statistics.mean(
            sr.sv_sem_pass_rate for sr in baseline_result.seed_results
        )

        # Regime counts
        for sr in baseline_result.seed_results:
            if sr.regime == "ROBUST":
                baseline_result.robust_count += 1
            elif sr.regime == "DEGRADED":
                baseline_result.degraded_count += 1
            else:
                baseline_result.dos_count += 1

        results.append(baseline_result)

        # Print aggregate summary
        print(f"\n  --- Aggregate (N={n} seeds) ---")
        print(f"  SV_RAW_CALIBRATION (pre-RSA):")
        print(f"    C0: {baseline_result.mean_sv_c0_rate:.3f}, "
              f"C1: {baseline_result.mean_sv_c1_rate:.3f}, "
              f"C2: {baseline_result.mean_sv_c2_rate:.3f}, "
              f"SEM_PASS: {baseline_result.mean_sv_sem_pass_rate:.3f} "
              f"(expected: {expected_sem_pass:.3f})")
        print(f"  Governance:")
        print(f"    mean_lapses: {baseline_result.mean_lapse_event_count:.1f} "
              f"(±{baseline_result.std_lapse_event_count:.1f})")
        print(f"    mean_lapse_epochs: {baseline_result.mean_lapse_epoch_count_total:.1f} "
              f"(±{baseline_result.std_lapse_epoch_count_total:.1f})")
        print(f"    mean_max_single_lapse: {baseline_result.mean_max_single_lapse_epochs:.1f}, "
              f"max_max: {baseline_result.max_max_single_lapse_epochs}")
        print(f"    mean_uptime: {baseline_result.mean_authority_uptime:.1%}")
        print(f"  RSA:")
        print(f"    targets: {baseline_result.sum_targets}, "
              f"flips: {baseline_result.sum_flips}, "
              f"pivotal: {baseline_result.sum_pivotal_flips} "
              f"({baseline_result.pivotal_rate:.1%})")
        print(f"  Regimes: ROBUST={baseline_result.robust_count}, "
              f"DEGRADED={baseline_result.degraded_count}, "
              f"DOS={baseline_result.dos_count}")

    # Summary tables
    print("\n" + "=" * 78)
    print("SWEEP SUMMARY")
    print("=" * 78)

    print("\n### Governance Metrics (per baseline point)")
    print(f"{'rate_ppm':>10} {'exp_SEM':>8} {'obs_SEM':>8} {'lapses':>8} {'lapse_ep':>10} "
          f"{'max_lapse':>10} {'uptime':>8} {'regime':>12}")
    print("-" * 88)

    for r in results:
        regime_str = f"{r.robust_count}R/{r.degraded_count}D/{r.dos_count}X"
        print(
            f"{r.per_ci_pass_rate_ppm:>10} "
            f"{r.expected_sem_pass_rate:>8.3f} "
            f"{r.mean_sv_sem_pass_rate:>8.3f} "
            f"{r.mean_lapse_event_count:>8.1f} "
            f"{r.mean_lapse_epoch_count_total:>10.1f} "
            f"{r.mean_max_single_lapse_epochs:>10.1f} "
            f"{r.mean_authority_uptime:>7.1%} "
            f"{regime_str:>12}"
        )

    print("\n### RSA Flip Summary (per baseline point)")
    print(f"{'rate_ppm':>10} {'targets':>10} {'flips':>8} {'pivotal':>8} {'piv_rate':>10}")
    print("-" * 50)

    for r in results:
        print(
            f"{r.per_ci_pass_rate_ppm:>10} "
            f"{r.sum_targets:>10} "
            f"{r.sum_flips:>8} "
            f"{r.sum_pivotal_flips:>8} "
            f"{r.pivotal_rate:>9.1%}"
        )

    print("\n### SV_RAW_CALIBRATION (pre-RSA, averaged across seeds)")
    print(f"{'rate_ppm':>10} {'exp_Ci':>8} {'obs_C0':>8} {'obs_C1':>8} {'obs_C2':>8} "
          f"{'exp_SEM':>8} {'obs_SEM':>8}")
    print("-" * 70)

    for r in results:
        exp_ci = r.per_ci_pass_rate_ppm / 1_000_000
        print(
            f"{r.per_ci_pass_rate_ppm:>10} "
            f"{exp_ci:>8.3f} "
            f"{r.mean_sv_c0_rate:>8.3f} "
            f"{r.mean_sv_c1_rate:>8.3f} "
            f"{r.mean_sv_c2_rate:>8.3f} "
            f"{r.expected_sem_pass_rate:>8.3f} "
            f"{r.mean_sv_sem_pass_rate:>8.3f}"
        )

    # Hypothesis validation
    print("\n" + "=" * 78)
    print("HYPOTHESIS VALIDATION")
    print("=" * 78)

    # H1: Monotonicity
    print("\n### H1: Monotonicity")
    print("Check: mean_lapse_epoch_count_total non-decreasing as per_ci_pass_rate_ppm decreases")

    lapse_epochs_by_rate = [(r.per_ci_pass_rate_ppm, r.mean_lapse_epoch_count_total) for r in results]
    lapse_epochs_by_rate_desc = sorted(lapse_epochs_by_rate, key=lambda x: -x[0])  # Descending rate

    inversions = 0
    for i in range(len(lapse_epochs_by_rate_desc) - 1):
        rate_high, lapse_high = lapse_epochs_by_rate_desc[i]
        rate_low, lapse_low = lapse_epochs_by_rate_desc[i + 1]
        if lapse_low < lapse_high:  # Inversion: lower rate should have >= lapses
            inversions += 1
            print(f"  Inversion: rate {rate_low} has fewer lapses ({lapse_low:.1f}) "
                  f"than rate {rate_high} ({lapse_high:.1f})")

    if inversions == 0:
        print("  No inversions detected.")
        print("  H1 Status: SUPPORTED")
        h1_status = "SUPPORTED"
    elif inversions <= 2:
        print(f"  {inversions} minor inversion(s) detected.")
        print("  H1 Status: INCONCLUSIVE")
        h1_status = "INCONCLUSIVE"
    else:
        print(f"  {inversions} inversions detected.")
        print("  H1 Status: NOT SUPPORTED")
        h1_status = "NOT SUPPORTED"

    # H2: Boundary detection
    print("\n### H2: Boundary Detection")
    print("Check: First baseline point where mean_lapse_epoch_count_total > 0")

    boundary_point = None
    for r in sorted(results, key=lambda x: -x.per_ci_pass_rate_ppm):  # Start from highest rate
        if r.mean_lapse_epoch_count_total > 0:
            boundary_point = r.per_ci_pass_rate_ppm
            break

    if boundary_point is not None:
        # Find the threshold band (between first lapse point and the one above)
        sorted_rates = sorted([r.per_ci_pass_rate_ppm for r in results], reverse=True)
        boundary_idx = sorted_rates.index(boundary_point)
        if boundary_idx > 0:
            upper_bound = sorted_rates[boundary_idx - 1]
            print(f"  Estimated threshold band: {boundary_point} - {upper_bound} PPM")
        else:
            print(f"  Lapses observed at highest baseline point: {boundary_point} PPM")
        print("  H2 Status: SUPPORTED")
        h2_status = "SUPPORTED"
    else:
        print("  No lapses observed at any baseline point.")
        print("  H2 Status: INCONCLUSIVE (no boundary detected)")
        h2_status = "INCONCLUSIVE"

    # H3: CTA clock imprint
    print("\n### H3: CTA Clock Imprint")
    print(f"Check: Lapse durations cluster near multiples of amnesty_interval ({config.amnesty_interval})")

    all_durations = []
    for r in results:
        all_durations.extend(r.all_lapse_durations)

    if len(all_durations) == 0:
        print("  No lapses observed; cannot analyze duration clustering.")
        print("  H3 Status: INCONCLUSIVE")
        h3_status = "INCONCLUSIVE"
    else:
        # Compute fraction within ±1 epoch of a multiple of amnesty_interval
        amnesty = config.amnesty_interval
        near_multiple = 0
        for d in all_durations:
            remainder = d % amnesty
            # Check if within ±1 of a multiple
            if remainder <= 1 or remainder >= amnesty - 1:
                near_multiple += 1

        fraction_near = near_multiple / len(all_durations)
        print(f"  Total lapse events: {len(all_durations)}")
        print(f"  Durations within ±1 epoch of amnesty multiple: {near_multiple} ({fraction_near:.1%})")

        # Histogram of remainders
        remainder_counts = {}
        for d in all_durations:
            r = d % amnesty
            remainder_counts[r] = remainder_counts.get(r, 0) + 1
        print(f"  Remainder distribution (mod {amnesty}):")
        for rem in sorted(remainder_counts.keys()):
            print(f"    {rem}: {remainder_counts[rem]}")

        # Threshold: if >30% cluster near multiples, consider it supported
        if fraction_near > 0.3:
            print("  H3 Status: SUPPORTED")
            h3_status = "SUPPORTED"
        else:
            print("  H3 Status: NOT SUPPORTED (clustering not evident)")
            h3_status = "NOT SUPPORTED"

    # Summary
    print("\n### Hypothesis Summary")
    print(f"  H1 (Monotonicity):      {h1_status}")
    print(f"  H2 (Boundary):          {h2_status}")
    print(f"  H3 (CTA Clock Imprint): {h3_status}")

    print("\n" + "=" * 78)
    print("RUN 1 COMPLETE")
    print("=" * 78)

    return results


if __name__ == "__main__":
    run_sv_baseline_sweep()
