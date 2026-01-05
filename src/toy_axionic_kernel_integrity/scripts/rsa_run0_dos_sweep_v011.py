#!/usr/bin/env python3
"""
RSA v0.1.1 Run 0: Governance DoS Sweep (Corrected).

CRITICAL CHANGES from v0.1.0:
1. Uses synthetic_verifier_enabled=True for meaningful SEM_PASS rates
2. Reports per-seed AND aggregate metrics clearly
3. Tracks "pivotal flips" (flips that changed SEM_PASS outcome)
4. Sweeps to higher flip rates (up to 20%)
5. Consistent epoch clock between RSA and harness

Per spec §10:
Measure how AKI v0.8's constitutional recovery behaves when semantic
verification is noisy, causing eligibility exhaustion and increased
time in NULL_AUTHORITY.
"""

import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Add src to path for development
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope


@dataclass
class SeedResult:
    """Per-seed result with full metrics."""
    seed: int

    # Harness metrics
    total_cycles: int = 0
    epochs_evaluated: int = 0
    lapse_event_count: int = 0
    lapse_epochs_total: int = 0
    authority_epochs_total: int = 0
    recovery_count: int = 0
    authority_uptime_fraction: float = 0.0
    lapse_fraction: float = 0.0
    recovery_yield: float = 0.0

    # RSA metrics
    targets_per_epoch: int = 3  # PER_CI scope
    total_targets: int = 0
    total_flips: int = 0
    pivotal_flips: int = 0  # Flips that changed SEM_PASS
    observed_ppm: int = 0

    # Regime
    regime: str = "ROBUST"


@dataclass
class SweepResult:
    """Aggregate result for a single p_flip value across seeds."""
    p_flip_ppm: int
    p_flip_pct: float

    # Per-seed results
    seed_results: List[SeedResult] = field(default_factory=list)

    # Aggregate metrics (computed from seed_results)
    sum_targets: int = 0
    sum_flips: int = 0
    sum_pivotal_flips: int = 0
    aggregate_observed_ppm: int = 0

    mean_lapse_event_count: float = 0.0
    mean_lapse_epochs_total: float = 0.0
    mean_authority_uptime: float = 0.0
    mean_recovery_yield: float = 0.0

    robust_count: int = 0
    degraded_count: int = 0
    dos_count: int = 0


def classify_regime(result, amnesty_interval: int) -> str:
    """
    Classify run regime per spec §10.5.

    - ROBUST: recoveries remain high, lapse durations modest
    - DEGRADED: recoveries occur, but long-lapse mode expands / RY collapses
    - DOS_REGIME: prolonged NULL_AUTHORITY dominance
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


def count_pivotal_flips(telemetry) -> int:
    """Count flips that changed SEM_PASS outcome."""
    count = 0
    for r in telemetry.epoch_records:
        if r.in_lapse:
            continue
        if r.sem_pass_raw != r.sem_pass_corrupted:
            count += 1
    return count


def run_dos_sweep():
    """Run the DoS sweep experiment with corrected methodology."""
    print("=" * 78)
    print("RSA v0.1.1 Run 0: Governance DoS Sweep (CORRECTED)")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 78)
    print()

    # Configuration with synthetic verifier for meaningful SEM_PASS rates
    config = ALSConfigV080(
        max_cycles=10_000,
        eligibility_threshold_k=3,
        max_successive_renewals=3,
        amnesty_interval=10,
        amnesty_decay=1,
        cta_enabled=True,
        # CRITICAL: Enable synthetic verifier for non-trivial SEM_PASS rates
        synthetic_verifier_enabled=True,
        synthetic_sem_pass_rate_ppm=800_000,  # 80% per-Ci => ~51% SEM_PASS
    )

    seeds = [40, 41, 42, 43, 44]

    # Extended sweep to higher flip rates
    p_flip_values = [0, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000]

    print("Configuration:")
    print(f"  Max cycles: {config.max_cycles}")
    print(f"  Eligibility K: {config.eligibility_threshold_k}")
    print(f"  Max renewals: {config.max_successive_renewals}")
    print(f"  Amnesty interval: {config.amnesty_interval}")
    print(f"  Synthetic verifier: {config.synthetic_verifier_enabled}")
    print(f"  Synthetic SEM_PASS rate: {config.synthetic_sem_pass_rate_ppm} PPM per-Ci")
    print(f"  Seeds: {seeds}")
    print(f"  p_flip sweep: {p_flip_values} PPM")
    print()

    results: List[SweepResult] = []

    for p_flip_ppm in p_flip_values:
        p_flip_pct = p_flip_ppm / 10_000
        print(f"\n{'='*78}")
        print(f"p_flip = {p_flip_ppm} PPM ({p_flip_pct:.2f}%)")
        print("=" * 78)

        sweep_result = SweepResult(
            p_flip_ppm=p_flip_ppm,
            p_flip_pct=p_flip_pct,
        )

        for seed in seeds:
            # Configure RSA
            if p_flip_ppm == 0:
                rsa_cfg = RSAConfig(rsa_enabled=False)
            else:
                rsa_cfg = RSAConfig(
                    rsa_enabled=True,
                    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
                    rsa_p_flip_ppm=p_flip_ppm,
                    rsa_scope=RSAScope.PER_CI,
                )

            h = ALSHarnessV080(seed=seed, config=config, rsa_config=rsa_cfg)
            result = h.run()

            # Extract metrics
            seed_result = SeedResult(seed=seed)
            seed_result.total_cycles = result.total_cycles
            seed_result.lapse_event_count = len(result.lapse_events_v080)
            seed_result.lapse_epochs_total = result.total_lapse_duration_epochs
            seed_result.recovery_count = result.recovery_count
            seed_result.authority_uptime_fraction = result.authority_uptime_fraction
            seed_result.lapse_fraction = result.lapse_fraction
            seed_result.recovery_yield = result.recovery_yield

            # RSA metrics
            if result.rsa:
                seed_result.epochs_evaluated = result.rsa["summary"]["epochs_evaluated"]
                seed_result.total_targets = result.rsa["summary"]["total_targets"]
                seed_result.total_flips = result.rsa["summary"]["total_flips"]
                seed_result.observed_ppm = result.rsa["summary"]["observed_flip_rate_ppm"]
                seed_result.authority_epochs_total = seed_result.epochs_evaluated

                # Count pivotal flips
                seed_result.pivotal_flips = count_pivotal_flips(h._rsa_telemetry)
            else:
                # No RSA - compute epochs from cycles
                seed_result.epochs_evaluated = result.total_cycles // config.renewal_check_interval
                seed_result.authority_epochs_total = seed_result.epochs_evaluated - seed_result.lapse_epochs_total

            # Classify regime
            seed_result.regime = classify_regime(result, config.amnesty_interval)

            sweep_result.seed_results.append(seed_result)

            print(f"  Seed {seed}: lapses={seed_result.lapse_event_count}, "
                  f"lapse_epochs={seed_result.lapse_epochs_total}, "
                  f"uptime={seed_result.authority_uptime_fraction:.1%}, "
                  f"flips={seed_result.total_flips}, "
                  f"pivotal={seed_result.pivotal_flips}, "
                  f"regime={seed_result.regime}")

        # Compute aggregates
        n = len(seeds)
        sweep_result.sum_targets = sum(sr.total_targets for sr in sweep_result.seed_results)
        sweep_result.sum_flips = sum(sr.total_flips for sr in sweep_result.seed_results)
        sweep_result.sum_pivotal_flips = sum(sr.pivotal_flips for sr in sweep_result.seed_results)

        if sweep_result.sum_targets > 0:
            sweep_result.aggregate_observed_ppm = (
                sweep_result.sum_flips * 1_000_000
            ) // sweep_result.sum_targets

        sweep_result.mean_lapse_event_count = sum(
            sr.lapse_event_count for sr in sweep_result.seed_results
        ) / n
        sweep_result.mean_lapse_epochs_total = sum(
            sr.lapse_epochs_total for sr in sweep_result.seed_results
        ) / n
        sweep_result.mean_authority_uptime = sum(
            sr.authority_uptime_fraction for sr in sweep_result.seed_results
        ) / n
        sweep_result.mean_recovery_yield = sum(
            sr.recovery_yield for sr in sweep_result.seed_results
        ) / n

        for sr in sweep_result.seed_results:
            if sr.regime == "ROBUST":
                sweep_result.robust_count += 1
            elif sr.regime == "DEGRADED":
                sweep_result.degraded_count += 1
            else:
                sweep_result.dos_count += 1

        results.append(sweep_result)

        print(f"\n  Aggregate: targets={sweep_result.sum_targets}, "
              f"flips={sweep_result.sum_flips}, "
              f"pivotal={sweep_result.sum_pivotal_flips}, "
              f"obs_ppm={sweep_result.aggregate_observed_ppm}")
        print(f"  Mean: lapses={sweep_result.mean_lapse_event_count:.1f}, "
              f"lapse_epochs={sweep_result.mean_lapse_epochs_total:.1f}, "
              f"uptime={sweep_result.mean_authority_uptime:.1%}")
        print(f"  Regimes: ROBUST={sweep_result.robust_count}, "
              f"DEGRADED={sweep_result.degraded_count}, "
              f"DOS={sweep_result.dos_count}")

    # Summary table
    print("\n" + "=" * 78)
    print("SWEEP SUMMARY")
    print("=" * 78)
    print()
    print("Per-Seed Averages:")
    print(f"{'p_flip':>10} {'p_flip':>8} {'Lapses':>8} {'Lapse':>10} {'Uptime':>8} "
          f"{'Flips':>8} {'Pivotal':>8} {'ROBUST':>7} {'DEG':>5} {'DOS':>5}")
    print(f"{'(PPM)':>10} {'(%)':>8} {'(count)':>8} {'(epochs)':>10} {'':>8} "
          f"{'(total)':>8} {'(total)':>8} {'':>7} {'':>5} {'':>5}")
    print("-" * 95)

    for r in results:
        print(f"{r.p_flip_ppm:>10} {r.p_flip_pct:>8.2f} "
              f"{r.mean_lapse_event_count:>8.1f} {r.mean_lapse_epochs_total:>10.1f} "
              f"{r.mean_authority_uptime:>7.1%} "
              f"{r.sum_flips:>8} {r.sum_pivotal_flips:>8} "
              f"{r.robust_count:>7} {r.degraded_count:>5} {r.dos_count:>5}")

    print("\n" + "=" * 78)
    print("DOS SWEEP COMPLETE")
    print("=" * 78)

    return results


if __name__ == "__main__":
    run_dos_sweep()
