#!/usr/bin/env python3
"""
RSA v0.1 Run 3: DoS Threshold Search.

Search for the first true DoS regime under high RSA noise at fixed SV baseline.
Find the smallest RSA flip intensity that produces persistent lapse (DoS).

Single axis: rsa_p_flip_ppm ∈ [300_000, 400_000, 500_000, 600_000]
Fixed SV baseline: 800,000 PPM

4 noise levels × 5 seeds = 20 runs

Per instructions §0-11.
"""

import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
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
    rsa_flip_ppm: int

    # Core governance metrics
    authority_uptime_fraction: float = 0.0
    lapse_event_count: int = 0
    lapse_epoch_count_total: int = 0
    max_single_lapse_epochs: int = 0
    mean_lapse_duration: float = 0.0
    final_in_authority: bool = True

    # Recovery characterization
    recovery_count: int = 0

    # RSA metrics
    epochs_evaluated: int = 0
    total_targets: int = 0
    total_flips: int = 0
    pivotal_flips: int = 0

    # Lapse durations for CTA imprint
    lapse_durations: List[int] = field(default_factory=list)

    # Regime classification
    regime: str = "ROBUST"

    # Flags
    dos_flag: bool = False
    degraded_flag: bool = False
    ends_in_null: bool = False


@dataclass
class NoiseLevelResult:
    """Aggregate result for a single RSA noise level."""

    rsa_flip_ppm: int

    # Per-seed results
    seed_results: List[SeedResult] = field(default_factory=list)

    # Aggregate governance metrics
    mean_uptime: float = 0.0
    std_uptime: float = 0.0
    mean_lapse_epochs: float = 0.0
    std_lapse_epochs: float = 0.0
    mean_max_single_lapse: float = 0.0
    max_max_single_lapse: int = 0

    # Aggregate RSA metrics
    sum_targets: int = 0
    sum_flips: int = 0
    sum_pivotal_flips: int = 0
    aggregate_observed_ppm: int = 0
    pivotal_rate: float = 0.0

    # Regime counts
    robust_count: int = 0
    degraded_count: int = 0
    dos_count: int = 0

    # All lapse durations for CTA imprint
    all_lapse_durations: List[int] = field(default_factory=list)


def classify_regime(result, amnesty_interval: int) -> str:
    """
    Classify run regime per spec §6.

    - DOS_REGIME: max single lapse > 5 × amnesty_interval epochs (>50)
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


def run_dos_threshold_search():
    """Run the DoS threshold search experiment."""
    print("=" * 78)
    print("RSA v0.1 Run 3: DoS Threshold Search")
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

    # SV configuration (FIXED for Run 3)
    sv_config = SVConfig(per_ci_pass_rate_ppm=800_000)
    expected_sem_pass = (800_000 / 1_000_000) ** 3

    seeds = [40, 41, 42, 43, 44]

    # RSA noise sweep (high range)
    rsa_sweep = [300_000, 400_000, 500_000, 600_000]

    dos_threshold_epochs = 5 * config.amnesty_interval  # 50 epochs

    print("Configuration:")
    print("  AKI v0.8 (FROZEN):")
    print(f"    max_cycles: {config.max_cycles}")
    print(f"    eligibility_threshold_k: {config.eligibility_threshold_k}")
    print(f"    amnesty_interval: {config.amnesty_interval}")
    print(f"    renewal_check_interval: {config.renewal_check_interval}")
    print(f"    total_epochs: {config.max_cycles // config.renewal_check_interval}")
    print("  SV (FIXED):")
    print(f"    per_ci_pass_rate_ppm: {sv_config.per_ci_pass_rate_ppm}")
    print(f"    expected_sem_pass: {expected_sem_pass:.3f}")
    print("  RSA:")
    print(f"    scope: PER_CI")
    print(f"    noise_model: FLIP_BERNOULLI")
    print(f"    sweep: {rsa_sweep} PPM ({[r // 10_000 for r in rsa_sweep]}%)")
    print("  Seeds:", seeds)
    print(f"  DOS threshold: max_single_lapse > {dos_threshold_epochs} epochs")
    print(f"  Total runs: {len(rsa_sweep)} × {len(seeds)} = {len(rsa_sweep) * len(seeds)}")
    print()

    results: Dict[int, NoiseLevelResult] = {}

    total_runs = len(rsa_sweep) * len(seeds)
    run_count = 0

    for rsa_ppm in rsa_sweep:
        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_scope=RSAScope.PER_CI,
            rsa_p_flip_ppm=rsa_ppm,
        )

        noise_result = NoiseLevelResult(rsa_flip_ppm=rsa_ppm)

        print(f"\n{'='*78}")
        print(f"RSA Flip Rate: {rsa_ppm} PPM ({rsa_ppm // 10_000}%)")
        print("=" * 78)

        for seed in seeds:
            run_count += 1
            h = ALSHarnessV080_SV(
                seed=seed, config=config, sv_config=sv_config, rsa_config=rsa_cfg
            )
            result = h.run()

            # Core governance metrics
            seed_result = SeedResult(seed=seed, rsa_flip_ppm=rsa_ppm)
            seed_result.authority_uptime_fraction = result.authority_uptime_fraction
            seed_result.lapse_event_count = len(result.lapse_events_v080)
            seed_result.lapse_epoch_count_total = result.total_lapse_duration_epochs
            seed_result.max_single_lapse_epochs = get_max_single_lapse_epochs(result)
            seed_result.lapse_durations = get_all_lapse_durations(result)

            if seed_result.lapse_event_count > 0:
                seed_result.mean_lapse_duration = (
                    seed_result.lapse_epoch_count_total / seed_result.lapse_event_count
                )

            # Recovery count
            seed_result.recovery_count = getattr(
                result, "recovery_count", seed_result.lapse_event_count
            )

            # Check if run ends in authority
            # (Infer from last lapse event if it extends to horizon)
            if result.lapse_events_v080:
                last_lapse = result.lapse_events_v080[-1]
                last_lapse_end = last_lapse.get("end_epoch", 0)
                total_epochs = config.max_cycles // config.renewal_check_interval
                if last_lapse_end >= total_epochs - 1:
                    seed_result.ends_in_null = True
                    seed_result.final_in_authority = False

            # RSA metrics
            if result.rsa:
                seed_result.epochs_evaluated = result.rsa["summary"]["epochs_evaluated"]
                seed_result.total_targets = result.rsa["summary"]["total_targets"]
                seed_result.total_flips = result.rsa["summary"]["total_flips"]
                seed_result.pivotal_flips = count_pivotal_flips(h._rsa_telemetry)

            # Regime classification
            seed_result.regime = classify_regime(result, config.amnesty_interval)
            seed_result.dos_flag = seed_result.regime == "DOS_REGIME"
            seed_result.degraded_flag = seed_result.regime == "DEGRADED"

            noise_result.seed_results.append(seed_result)
            noise_result.all_lapse_durations.extend(seed_result.lapse_durations)

            # Print per-seed summary with flags
            flags = []
            if seed_result.max_single_lapse_epochs > dos_threshold_epochs:
                flags.append("⚠️ DOS")
            if seed_result.authority_uptime_fraction < 0.5:
                flags.append("⚠️ <50% uptime")
            if seed_result.ends_in_null:
                flags.append("⚠️ ends_null")

            flag_str = " ".join(flags) if flags else ""
            print(
                f"  Seed {seed}: uptime={seed_result.authority_uptime_fraction:.1%}, "
                f"lapses={seed_result.lapse_event_count}, "
                f"lapse_ep={seed_result.lapse_epoch_count_total}, "
                f"max_lapse={seed_result.max_single_lapse_epochs}, "
                f"regime={seed_result.regime} {flag_str}"
            )

        # Compute aggregates
        n = len(seeds)

        uptimes = [sr.authority_uptime_fraction for sr in noise_result.seed_results]
        lapse_epochs = [sr.lapse_epoch_count_total for sr in noise_result.seed_results]
        max_lapses = [sr.max_single_lapse_epochs for sr in noise_result.seed_results]

        noise_result.mean_uptime = statistics.mean(uptimes)
        noise_result.std_uptime = statistics.stdev(uptimes) if n > 1 else 0.0
        noise_result.mean_lapse_epochs = statistics.mean(lapse_epochs)
        noise_result.std_lapse_epochs = statistics.stdev(lapse_epochs) if n > 1 else 0.0
        noise_result.mean_max_single_lapse = statistics.mean(max_lapses)
        noise_result.max_max_single_lapse = max(max_lapses)

        noise_result.sum_targets = sum(sr.total_targets for sr in noise_result.seed_results)
        noise_result.sum_flips = sum(sr.total_flips for sr in noise_result.seed_results)
        noise_result.sum_pivotal_flips = sum(sr.pivotal_flips for sr in noise_result.seed_results)

        if noise_result.sum_targets > 0:
            noise_result.aggregate_observed_ppm = (
                noise_result.sum_flips * 1_000_000
            ) // noise_result.sum_targets

        if noise_result.sum_flips > 0:
            noise_result.pivotal_rate = noise_result.sum_pivotal_flips / noise_result.sum_flips

        for sr in noise_result.seed_results:
            if sr.regime == "ROBUST":
                noise_result.robust_count += 1
            elif sr.regime == "DEGRADED":
                noise_result.degraded_count += 1
            else:
                noise_result.dos_count += 1

        results[rsa_ppm] = noise_result

        # Print aggregate summary
        print(f"\n  --- Aggregate (N={n} seeds) ---")
        print(f"  mean_uptime: {noise_result.mean_uptime:.1%} (±{noise_result.std_uptime:.1%})")
        print(f"  mean_lapse_epochs: {noise_result.mean_lapse_epochs:.1f} (±{noise_result.std_lapse_epochs:.1f})")
        print(f"  mean_max_lapse: {noise_result.mean_max_single_lapse:.1f}, max_max: {noise_result.max_max_single_lapse}")
        print(f"  RSA: targets={noise_result.sum_targets}, flips={noise_result.sum_flips}, "
              f"pivotal={noise_result.sum_pivotal_flips} ({noise_result.pivotal_rate:.1%})")
        print(f"  Regimes: ROBUST={noise_result.robust_count}, DEGRADED={noise_result.degraded_count}, "
              f"DOS={noise_result.dos_count}")

    print(f"\n  All {total_runs} runs completed.\n")

    # Summary Tables
    print("=" * 78)
    print("SUMMARY TABLES")
    print("=" * 78)

    # Table 1: Per-noise summary
    print("\n### Table 1: Per-Noise Level Summary")
    print(f"{'RSA_PPM':>10} {'mean_up':>10} {'std_up':>8} {'mean_lapse':>12} "
          f"{'max_max':>8} {'R/D/X':>10}")
    print("-" * 62)

    for rsa_ppm in rsa_sweep:
        nr = results[rsa_ppm]
        regime_str = f"{nr.robust_count}/{nr.degraded_count}/{nr.dos_count}"
        print(
            f"{rsa_ppm:>10} "
            f"{nr.mean_uptime:>9.1%} "
            f"{nr.std_uptime:>7.1%} "
            f"{nr.mean_lapse_epochs:>12.1f} "
            f"{nr.max_max_single_lapse:>8} "
            f"{regime_str:>10}"
        )

    # Table 2: Per-seed detail
    print("\n### Table 2: Per-Seed Results")
    print(f"{'RSA':>8} {'seed':>6} {'uptime':>8} {'lapse_ep':>10} {'max_lapse':>10} "
          f"{'mean_dur':>10} {'regime':>12}")
    print("-" * 70)

    for rsa_ppm in rsa_sweep:
        nr = results[rsa_ppm]
        for sr in nr.seed_results:
            print(
                f"{rsa_ppm:>8} "
                f"{sr.seed:>6} "
                f"{sr.authority_uptime_fraction:>7.1%} "
                f"{sr.lapse_epoch_count_total:>10} "
                f"{sr.max_single_lapse_epochs:>10} "
                f"{sr.mean_lapse_duration:>10.1f} "
                f"{sr.regime:>12}"
            )

    # Table 3: RSA Flip Summary
    print("\n### Table 3: RSA Flip Summary")
    print(f"{'RSA_PPM':>10} {'targets':>10} {'flips':>8} {'obs_ppm':>10} "
          f"{'pivotal':>8} {'piv_rate':>10}")
    print("-" * 60)

    for rsa_ppm in rsa_sweep:
        nr = results[rsa_ppm]
        print(
            f"{rsa_ppm:>10} "
            f"{nr.sum_targets:>10} "
            f"{nr.sum_flips:>8} "
            f"{nr.aggregate_observed_ppm:>10} "
            f"{nr.sum_pivotal_flips:>8} "
            f"{nr.pivotal_rate:>9.1%}"
        )

    # Table 4: CTA Imprint (aggregate across all noise levels)
    print("\n### Table 4: CTA Imprint (Lapse Duration mod amnesty_interval)")

    all_durations = []
    for nr in results.values():
        all_durations.extend(nr.all_lapse_durations)

    if len(all_durations) > 0:
        amnesty = config.amnesty_interval
        near_multiple = 0
        remainder_counts = {}

        for d in all_durations:
            r = d % amnesty
            remainder_counts[r] = remainder_counts.get(r, 0) + 1
            if r <= 1 or r >= amnesty - 1:
                near_multiple += 1

        fraction_near = near_multiple / len(all_durations)
        print(f"  Total lapse events: {len(all_durations)}")
        print(f"  Durations within ±1 of amnesty multiple: {near_multiple} ({fraction_near:.1%})")
        print(f"  Remainder distribution (mod {amnesty}):")
        for rem in sorted(remainder_counts.keys()):
            print(f"    {rem}: {remainder_counts[rem]}")
    else:
        print("  No lapse events recorded.")

    # Per noise level CTA imprint
    print("\n### Table 5: CTA Imprint by Noise Level")
    print(f"{'RSA_PPM':>10} {'N_lapses':>10} {'near_mult':>10} {'fraction':>10}")
    print("-" * 45)

    for rsa_ppm in rsa_sweep:
        nr = results[rsa_ppm]
        if len(nr.all_lapse_durations) > 0:
            near = sum(
                1 for d in nr.all_lapse_durations
                if (d % config.amnesty_interval) <= 1 or (d % config.amnesty_interval) >= config.amnesty_interval - 1
            )
            frac = near / len(nr.all_lapse_durations)
            print(f"{rsa_ppm:>10} {len(nr.all_lapse_durations):>10} {near:>10} {frac:>9.1%}")
        else:
            print(f"{rsa_ppm:>10} {'0':>10} {'-':>10} {'-':>10}")

    # Hypothesis Validation
    print("\n" + "=" * 78)
    print("HYPOTHESIS VALIDATION")
    print("=" * 78)

    # H7: DoS emergence
    print("\n### H7: DoS Emergence")
    print(f"Check: At least one seed becomes DOS_REGIME (max_lapse > {dos_threshold_epochs})")

    dos_found = False
    first_dos_level = None
    dos_seeds = []

    for rsa_ppm in rsa_sweep:
        nr = results[rsa_ppm]
        if nr.dos_count > 0:
            dos_found = True
            if first_dos_level is None:
                first_dos_level = rsa_ppm
            for sr in nr.seed_results:
                if sr.regime == "DOS_REGIME":
                    dos_seeds.append((rsa_ppm, sr.seed, sr.max_single_lapse_epochs))

    if dos_found:
        print(f"  DoS first observed at RSA = {first_dos_level} PPM ({first_dos_level // 10_000}%)")
        print(f"  DoS seeds:")
        for rsa, seed, max_lapse in dos_seeds:
            print(f"    RSA={rsa}, seed={seed}, max_lapse={max_lapse}")
        print("  H7 Status: SUPPORTED")
        h7_status = "SUPPORTED"
    else:
        print("  No DOS_REGIME observed at any tested noise level.")
        print("  H7 Status: NOT SUPPORTED")
        h7_status = "NOT SUPPORTED"

    # H8: CTA clock imprint persists until DoS
    print("\n### H8: CTA Clock Imprint Persists Until DoS")
    print("Check: Non-DoS runs show lapse clustering; DoS runs show weakening")

    # Separate durations by regime
    non_dos_durations = []
    dos_durations = []

    for nr in results.values():
        for sr in nr.seed_results:
            if sr.regime == "DOS_REGIME":
                dos_durations.extend(sr.lapse_durations)
            else:
                non_dos_durations.extend(sr.lapse_durations)

    amnesty = config.amnesty_interval

    if len(non_dos_durations) > 0:
        non_dos_near = sum(
            1 for d in non_dos_durations
            if (d % amnesty) <= 1 or (d % amnesty) >= amnesty - 1
        )
        non_dos_frac = non_dos_near / len(non_dos_durations)
        print(f"  Non-DoS lapses: {len(non_dos_durations)}, near multiple: {non_dos_frac:.1%}")
    else:
        non_dos_frac = 0.0
        print("  Non-DoS lapses: 0")

    if len(dos_durations) > 0:
        dos_near = sum(
            1 for d in dos_durations
            if (d % amnesty) <= 1 or (d % amnesty) >= amnesty - 1
        )
        dos_frac = dos_near / len(dos_durations)
        print(f"  DoS lapses: {len(dos_durations)}, near multiple: {dos_frac:.1%}")
    else:
        dos_frac = 0.0
        print("  DoS lapses: 0 (no DoS observed)")

    if len(non_dos_durations) > 0 and non_dos_frac > 0.5:
        if len(dos_durations) == 0 or dos_frac < non_dos_frac:
            print("  CTA imprint persists in non-DoS; weakens or absent in DoS")
            print("  H8 Status: SUPPORTED")
            h8_status = "SUPPORTED"
        else:
            print("  CTA imprint does not weaken in DoS regime")
            print("  H8 Status: INCONCLUSIVE")
            h8_status = "INCONCLUSIVE"
    else:
        print("  Insufficient data to evaluate CTA imprint")
        print("  H8 Status: INCONCLUSIVE")
        h8_status = "INCONCLUSIVE"

    # H9: Nonlinear transition
    print("\n### H9: Nonlinear Transition")
    print("Check: Transition from rare lapses to persistent lapse is sharper in high-noise regime")

    # Compare mean_lapse_epochs growth rate across noise levels
    lapse_epochs_by_noise = [(rsa_ppm, results[rsa_ppm].mean_lapse_epochs) for rsa_ppm in rsa_sweep]

    print("  Lapse epoch progression:")
    for rsa_ppm, mean_lapse in lapse_epochs_by_noise:
        print(f"    RSA={rsa_ppm}: {mean_lapse:.1f}")

    # Check if there's a sharp jump (>2x increase between adjacent levels)
    sharp_jump = False
    for i in range(1, len(lapse_epochs_by_noise)):
        prev_lapse = lapse_epochs_by_noise[i - 1][1]
        curr_lapse = lapse_epochs_by_noise[i][1]
        if prev_lapse > 0 and curr_lapse / prev_lapse > 2.0:
            sharp_jump = True
            print(f"  Sharp jump detected: {lapse_epochs_by_noise[i-1][0]} → {lapse_epochs_by_noise[i][0]}")
            print(f"    ({prev_lapse:.1f} → {curr_lapse:.1f}, {curr_lapse/prev_lapse:.1f}x)")

    # Also check if max_max_lapse jumps sharply
    max_lapse_by_noise = [(rsa_ppm, results[rsa_ppm].max_max_single_lapse) for rsa_ppm in rsa_sweep]
    for i in range(1, len(max_lapse_by_noise)):
        prev_max = max_lapse_by_noise[i - 1][1]
        curr_max = max_lapse_by_noise[i][1]
        if prev_max > 0 and curr_max > dos_threshold_epochs and prev_max <= dos_threshold_epochs:
            sharp_jump = True
            print(f"  DoS threshold crossed: {max_lapse_by_noise[i-1][0]} → {max_lapse_by_noise[i][0]}")
            print(f"    (max_lapse {prev_max} → {curr_max})")

    if sharp_jump:
        print("  H9 Status: SUPPORTED")
        h9_status = "SUPPORTED"
    else:
        print("  No sharp transition detected; progression appears gradual")
        print("  H9 Status: NOT SUPPORTED")
        h9_status = "NOT SUPPORTED"

    # Hypothesis Summary
    print("\n### Hypothesis Summary")
    print(f"  H7 (DoS Emergence):           {h7_status}")
    print(f"  H8 (CTA Imprint Until DoS):   {h8_status}")
    print(f"  H9 (Nonlinear Transition):    {h9_status}")

    # First DoS threshold identification
    print("\n" + "=" * 78)
    print("DOS THRESHOLD IDENTIFICATION")
    print("=" * 78)

    if first_dos_level is not None:
        print(f"\n  First DoS observed at RSA flip rate: {first_dos_level} PPM ({first_dos_level // 10_000}%)")
        print(f"  At SV baseline: 800,000 PPM (~51% SEM_PASS)")
        print(f"  DoS seeds: {[(rsa, seed) for rsa, seed, _ in dos_seeds]}")
    else:
        print(f"\n  No DoS observed up to {max(rsa_sweep)} PPM ({max(rsa_sweep) // 10_000}%)")
        print(f"  Higher noise levels may be needed to find DoS threshold")

    print("\n" + "=" * 78)
    print("RUN 3 COMPLETE")
    print("=" * 78)

    return results


if __name__ == "__main__":
    run_dos_threshold_search()
