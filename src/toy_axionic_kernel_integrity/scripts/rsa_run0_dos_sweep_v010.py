#!/usr/bin/env python3
"""
RSA v0.1 Run 0: Governance DoS Sweep.

Per spec §10:
Measure how AKI v0.8's constitutional recovery behaves when semantic
verification is noisy, causing eligibility exhaustion and increased
time in NULL_AUTHORITY.

Sweep rsa_p_flip_ppm over: 0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000
"""

import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Add src to path for development
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope


@dataclass
class SweepResult:
    """Result for a single p_flip value across seeds."""
    p_flip_ppm: int
    p_flip_pct: float

    # Aggregate metrics across seeds
    mean_lapse_count: float = 0.0
    mean_lapse_epochs: float = 0.0
    mean_lapse_duration: float = 0.0
    mean_recovery_count: float = 0.0
    mean_recovery_rate: float = 0.0
    mean_stutter_count: float = 0.0
    mean_recovery_yield: float = 0.0
    mean_authority_uptime: float = 0.0
    mean_lapse_fraction: float = 0.0

    # RSA metrics
    mean_total_flips: float = 0.0
    mean_observed_rate_ppm: float = 0.0

    # Regime classification
    robust_count: int = 0
    degraded_count: int = 0
    dos_count: int = 0

    # Per-seed details
    seed_results: List[Dict[str, Any]] = field(default_factory=list)


def classify_regime(result, amnesty_interval: int) -> str:
    """
    Classify run regime per spec §10.5.

    - ROBUST: recoveries remain high, lapse durations modest
    - DEGRADED: recoveries occur, but long-lapse mode expands / RY collapses
    - DOS_REGIME: prolonged NULL_AUTHORITY dominance
    """
    # DoS threshold: continuous lapse > 5 * amnesty_interval epochs
    dos_threshold_epochs = 5 * amnesty_interval

    # Check for DoS regime
    max_lapse_epochs = 0
    for lapse in result.lapse_events_v080:
        lapse_duration = lapse.get("duration_epochs", 0)
        if lapse_duration > max_lapse_epochs:
            max_lapse_epochs = lapse_duration

    if max_lapse_epochs > dos_threshold_epochs:
        return "DOS_REGIME"

    # Check for degraded regime (low recovery yield or high lapse fraction)
    if result.recovery_yield < 0.5 or result.lapse_fraction > 0.5:
        return "DEGRADED"

    return "ROBUST"


def run_dos_sweep():
    """Run the DoS sweep experiment."""
    print("=" * 70)
    print("RSA v0.1 Run 0: Governance DoS Sweep")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    # Standard AKI v0.8 configuration
    config = ALSConfigV080(
        max_cycles=10_000,
        eligibility_threshold_k=3,
        max_successive_renewals=3,
        amnesty_interval=10,
        amnesty_decay=1,
        cta_enabled=True,
    )

    seeds = [40, 41, 42, 43, 44]

    # Sweep values per spec §10.2
    p_flip_values = [0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000]

    print("Configuration:")
    print(f"  Max cycles: {config.max_cycles}")
    print(f"  Eligibility K: {config.eligibility_threshold_k}")
    print(f"  Max renewals: {config.max_successive_renewals}")
    print(f"  Amnesty interval: {config.amnesty_interval}")
    print(f"  Seeds: {seeds}")
    print(f"  p_flip sweep: {p_flip_values} PPM")
    print()

    results: List[SweepResult] = []

    for p_flip_ppm in p_flip_values:
        p_flip_pct = p_flip_ppm / 10_000  # Convert to percentage
        print(f"\n{'='*70}")
        print(f"p_flip = {p_flip_ppm} PPM ({p_flip_pct:.2f}%)")
        print("=" * 70)

        sweep_result = SweepResult(
            p_flip_ppm=p_flip_ppm,
            p_flip_pct=p_flip_pct,
        )

        # Accumulators for averaging
        lapse_counts = []
        lapse_epochs_list = []
        lapse_durations = []
        recovery_counts = []
        recovery_rates = []
        stutter_counts = []
        recovery_yields = []
        authority_uptimes = []
        lapse_fractions = []
        total_flips_list = []
        observed_rates = []

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
            lapse_count = len(result.lapse_events_v080)
            total_lapse_epochs = result.total_lapse_duration_epochs
            mean_lapse_dur = total_lapse_epochs / lapse_count if lapse_count > 0 else 0
            recovery_count = result.recovery_count
            recovery_rate = recovery_count / lapse_count if lapse_count > 0 else 1.0
            stutter_count = result.stutter_recovery_count
            recovery_yield = result.recovery_yield
            authority_uptime = result.authority_uptime_fraction
            lapse_frac = result.lapse_fraction

            # RSA metrics
            if result.rsa:
                total_flips = result.rsa["summary"]["total_flips"]
                observed_rate = result.rsa["summary"]["observed_flip_rate_ppm"]
            else:
                total_flips = 0
                observed_rate = 0

            # Classify regime
            regime = classify_regime(result, config.amnesty_interval)

            # Update counts
            if regime == "ROBUST":
                sweep_result.robust_count += 1
            elif regime == "DEGRADED":
                sweep_result.degraded_count += 1
            else:
                sweep_result.dos_count += 1

            # Store per-seed result
            seed_result = {
                "seed": seed,
                "lapse_count": lapse_count,
                "lapse_epochs": total_lapse_epochs,
                "mean_lapse_duration": mean_lapse_dur,
                "recovery_count": recovery_count,
                "recovery_rate": recovery_rate,
                "stutter_count": stutter_count,
                "recovery_yield": recovery_yield,
                "authority_uptime": authority_uptime,
                "lapse_fraction": lapse_frac,
                "total_flips": total_flips,
                "observed_rate_ppm": observed_rate,
                "regime": regime,
            }
            sweep_result.seed_results.append(seed_result)

            # Accumulate for averaging
            lapse_counts.append(lapse_count)
            lapse_epochs_list.append(total_lapse_epochs)
            lapse_durations.append(mean_lapse_dur)
            recovery_counts.append(recovery_count)
            recovery_rates.append(recovery_rate)
            stutter_counts.append(stutter_count)
            recovery_yields.append(recovery_yield)
            authority_uptimes.append(authority_uptime)
            lapse_fractions.append(lapse_frac)
            total_flips_list.append(total_flips)
            observed_rates.append(observed_rate)

            print(f"  Seed {seed}: lapses={lapse_count}, rec={recovery_count}, "
                  f"RY={recovery_yield:.2f}, uptime={authority_uptime:.1%}, "
                  f"flips={total_flips}, regime={regime}")

        # Compute averages
        n = len(seeds)
        sweep_result.mean_lapse_count = sum(lapse_counts) / n
        sweep_result.mean_lapse_epochs = sum(lapse_epochs_list) / n
        sweep_result.mean_lapse_duration = sum(lapse_durations) / n
        sweep_result.mean_recovery_count = sum(recovery_counts) / n
        sweep_result.mean_recovery_rate = sum(recovery_rates) / n
        sweep_result.mean_stutter_count = sum(stutter_counts) / n
        sweep_result.mean_recovery_yield = sum(recovery_yields) / n
        sweep_result.mean_authority_uptime = sum(authority_uptimes) / n
        sweep_result.mean_lapse_fraction = sum(lapse_fractions) / n
        sweep_result.mean_total_flips = sum(total_flips_list) / n
        sweep_result.mean_observed_rate_ppm = sum(observed_rates) / n

        results.append(sweep_result)

        print(f"\n  Summary: mean_lapses={sweep_result.mean_lapse_count:.1f}, "
              f"mean_rec={sweep_result.mean_recovery_count:.1f}, "
              f"mean_RY={sweep_result.mean_recovery_yield:.2f}, "
              f"mean_uptime={sweep_result.mean_authority_uptime:.1%}")
        print(f"  Regimes: ROBUST={sweep_result.robust_count}, "
              f"DEGRADED={sweep_result.degraded_count}, "
              f"DOS={sweep_result.dos_count}")

    # Print summary table
    print("\n" + "=" * 70)
    print("SWEEP SUMMARY")
    print("=" * 70)
    print()
    print("| p_flip (PPM) | p_flip (%) | Lapses | Recoveries | RY    | Uptime  | Flips | ROBUST | DEGRADED | DOS |")
    print("|--------------|------------|--------|------------|-------|---------|-------|--------|----------|-----|")

    for r in results:
        print(f"| {r.p_flip_ppm:>12} | {r.p_flip_pct:>10.2f} | "
              f"{r.mean_lapse_count:>6.1f} | {r.mean_recovery_count:>10.1f} | "
              f"{r.mean_recovery_yield:>5.2f} | {r.mean_authority_uptime:>6.1%} | "
              f"{r.mean_total_flips:>5.0f} | {r.robust_count:>6} | "
              f"{r.degraded_count:>8} | {r.dos_count:>3} |")

    print()
    print("=" * 70)
    print("DOS SWEEP COMPLETE")
    print("=" * 70)

    return results


if __name__ == "__main__":
    results = run_dos_sweep()
