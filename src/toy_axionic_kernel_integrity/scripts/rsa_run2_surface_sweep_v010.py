#!/usr/bin/env python3
"""
RSA v0.1 Run 2: Robustness Surface Mapping.

Map the two-dimensional robustness surface of AKI v0.8 under RSA noise:
- Axis A: Semantic baseline (SV per_ci_pass_rate_ppm)
- Axis B: RSA noise intensity (rsa_p_flip_ppm)

5 SV baselines × 5 RSA noise levels × 5 seeds = 125 runs

Per instructions §0-10.
"""

import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
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
    sv_baseline_ppm: int
    rsa_flip_ppm: int

    # Governance metrics
    total_cycles: int = 0
    epochs_evaluated: int = 0
    lapse_event_count: int = 0
    lapse_epoch_count_total: int = 0
    max_single_lapse_epochs: int = 0
    authority_uptime_fraction: float = 0.0
    recovery_count: int = 0

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
    sv_epochs_evaluated: int = 0

    # Lapse durations for H6 analysis
    lapse_durations: List[int] = field(default_factory=list)

    # Regime classification
    regime: str = "ROBUST"


@dataclass
class CellResult:
    """Aggregate result for a single (SV baseline, RSA noise) cell."""

    sv_baseline_ppm: int
    rsa_flip_ppm: int
    expected_sem_pass_rate: float

    # Per-seed results
    seed_results: List[SeedResult] = field(default_factory=list)

    # Aggregate governance metrics
    mean_lapse_event_count: float = 0.0
    std_lapse_event_count: float = 0.0
    mean_lapse_epoch_count_total: float = 0.0
    std_lapse_epoch_count_total: float = 0.0
    mean_max_single_lapse_epochs: float = 0.0
    max_max_single_lapse_epochs: int = 0
    mean_authority_uptime: float = 0.0

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


@dataclass
class SVCalibration:
    """Aggregated SV calibration for a single baseline across all seeds/RSA levels."""

    sv_baseline_ppm: int
    expected_per_ci: float
    expected_sem_pass: float

    total_epochs: int = 0
    obs_c0_sum: int = 0
    obs_c1_sum: int = 0
    obs_c2_sum: int = 0
    obs_sem_pass_sum: int = 0

    # Per seed+RSA observations for sanity check
    observations: List[Tuple[int, int, float, float, float, float]] = field(
        default_factory=list
    )  # (seed, rsa_ppm, c0, c1, c2, sem)

    @property
    def obs_c0(self) -> float:
        return self.obs_c0_sum / self.total_epochs if self.total_epochs > 0 else 0.0

    @property
    def obs_c1(self) -> float:
        return self.obs_c1_sum / self.total_epochs if self.total_epochs > 0 else 0.0

    @property
    def obs_c2(self) -> float:
        return self.obs_c2_sum / self.total_epochs if self.total_epochs > 0 else 0.0

    @property
    def obs_sem_pass(self) -> float:
        return self.obs_sem_pass_sum / self.total_epochs if self.total_epochs > 0 else 0.0


def classify_regime(result, amnesty_interval: int) -> str:
    """
    Classify run regime per spec §5.

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


def run_surface_sweep():
    """Run the 2D robustness surface sweep experiment."""
    print("=" * 78)
    print("RSA v0.1 Run 2: Robustness Surface Mapping")
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

    seeds = [40, 41, 42, 43, 44]

    # Axis A: SV baseline sweep
    sv_sweep = [600_000, 700_000, 800_000, 850_000, 900_000]

    # Axis B: RSA noise sweep
    rsa_sweep = [0, 50_000, 100_000, 150_000, 200_000]

    print("Configuration:")
    print("  AKI v0.8 (FROZEN):")
    print(f"    max_cycles: {config.max_cycles}")
    print(f"    eligibility_threshold_k: {config.eligibility_threshold_k}")
    print(f"    amnesty_interval: {config.amnesty_interval}")
    print(f"    renewal_check_interval: {config.renewal_check_interval}")
    print(f"    total_epochs: {config.max_cycles // config.renewal_check_interval}")
    print("  Seeds:", seeds)
    print("  SV baseline sweep (PPM):", sv_sweep)
    print("  RSA noise sweep (PPM):", rsa_sweep)
    print(f"  Total runs: {len(sv_sweep)} × {len(rsa_sweep)} × {len(seeds)} = "
          f"{len(sv_sweep) * len(rsa_sweep) * len(seeds)}")
    print()

    # Grid storage: (sv_ppm, rsa_ppm) -> CellResult
    grid: Dict[Tuple[int, int], CellResult] = {}

    # SV calibration storage: sv_ppm -> SVCalibration
    sv_calibrations: Dict[int, SVCalibration] = {}
    for sv_ppm in sv_sweep:
        expected_per_ci = sv_ppm / 1_000_000
        sv_calibrations[sv_ppm] = SVCalibration(
            sv_baseline_ppm=sv_ppm,
            expected_per_ci=expected_per_ci,
            expected_sem_pass=expected_per_ci ** 3,
        )

    # Execute grid
    total_runs = len(sv_sweep) * len(rsa_sweep) * len(seeds)
    run_count = 0

    for sv_ppm in sv_sweep:
        sv_config = SVConfig(per_ci_pass_rate_ppm=sv_ppm)
        expected_sem = (sv_ppm / 1_000_000) ** 3

        for rsa_ppm in rsa_sweep:
            rsa_cfg = RSAConfig(
                rsa_enabled=(rsa_ppm > 0),
                rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
                rsa_scope=RSAScope.PER_CI,
                rsa_p_flip_ppm=rsa_ppm,
            )

            cell = CellResult(
                sv_baseline_ppm=sv_ppm,
                rsa_flip_ppm=rsa_ppm,
                expected_sem_pass_rate=expected_sem,
            )

            for seed in seeds:
                run_count += 1
                h = ALSHarnessV080_SV(
                    seed=seed, config=config, sv_config=sv_config, rsa_config=rsa_cfg
                )
                result = h.run()

                # Extract governance metrics
                seed_result = SeedResult(
                    seed=seed,
                    sv_baseline_ppm=sv_ppm,
                    rsa_flip_ppm=rsa_ppm,
                )
                seed_result.total_cycles = result.total_cycles
                seed_result.lapse_event_count = len(result.lapse_events_v080)
                seed_result.lapse_epoch_count_total = result.total_lapse_duration_epochs
                seed_result.max_single_lapse_epochs = get_max_single_lapse_epochs(result)
                seed_result.authority_uptime_fraction = result.authority_uptime_fraction
                seed_result.recovery_count = getattr(
                    result, "recovery_count", seed_result.lapse_event_count
                )
                seed_result.lapse_durations = get_all_lapse_durations(result)

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
                    seed_result.sv_epochs_evaluated = calib["epochs_evaluated"]

                    # Accumulate to baseline calibration
                    sv_cal = sv_calibrations[sv_ppm]
                    sv_cal.total_epochs += calib["epochs_evaluated"]
                    sv_cal.obs_c0_sum += calib["c0"]["count"]
                    sv_cal.obs_c1_sum += calib["c1"]["count"]
                    sv_cal.obs_c2_sum += calib["c2"]["count"]
                    sv_cal.obs_sem_pass_sum += calib["sem_pass"]["count"]
                    sv_cal.observations.append((
                        seed, rsa_ppm,
                        seed_result.sv_c0_rate,
                        seed_result.sv_c1_rate,
                        seed_result.sv_c2_rate,
                        seed_result.sv_sem_pass_rate,
                    ))

                # Regime classification
                seed_result.regime = classify_regime(result, config.amnesty_interval)

                cell.seed_results.append(seed_result)

                # Progress indicator
                if run_count % 25 == 0:
                    print(f"  Progress: {run_count}/{total_runs} runs completed")

            # Compute cell aggregates
            n = len(seeds)

            lapse_counts = [sr.lapse_event_count for sr in cell.seed_results]
            lapse_epochs = [sr.lapse_epoch_count_total for sr in cell.seed_results]
            max_lapses = [sr.max_single_lapse_epochs for sr in cell.seed_results]

            cell.mean_lapse_event_count = statistics.mean(lapse_counts)
            cell.std_lapse_event_count = statistics.stdev(lapse_counts) if n > 1 else 0.0
            cell.mean_lapse_epoch_count_total = statistics.mean(lapse_epochs)
            cell.std_lapse_epoch_count_total = statistics.stdev(lapse_epochs) if n > 1 else 0.0
            cell.mean_max_single_lapse_epochs = statistics.mean(max_lapses)
            cell.max_max_single_lapse_epochs = max(max_lapses)
            cell.mean_authority_uptime = statistics.mean(
                sr.authority_uptime_fraction for sr in cell.seed_results
            )

            cell.sum_targets = sum(sr.total_targets for sr in cell.seed_results)
            cell.sum_flips = sum(sr.total_flips for sr in cell.seed_results)
            cell.sum_pivotal_flips = sum(sr.pivotal_flips for sr in cell.seed_results)

            if cell.sum_targets > 0:
                cell.aggregate_observed_ppm = (
                    cell.sum_flips * 1_000_000
                ) // cell.sum_targets

            if cell.sum_flips > 0:
                cell.pivotal_rate = cell.sum_pivotal_flips / cell.sum_flips

            for sr in cell.seed_results:
                if sr.regime == "ROBUST":
                    cell.robust_count += 1
                elif sr.regime == "DEGRADED":
                    cell.degraded_count += 1
                else:
                    cell.dos_count += 1

            grid[(sv_ppm, rsa_ppm)] = cell

    print(f"\n  All {total_runs} runs completed.\n")

    # Sanity check: SV_RAW should be invariant to RSA noise
    print("=" * 78)
    print("SANITY CHECK: SV_RAW invariance across RSA noise levels")
    print("=" * 78)

    sanity_passed = True
    for sv_ppm, sv_cal in sv_calibrations.items():
        # Group observations by seed
        by_seed: Dict[int, List[Tuple[int, float, float, float, float]]] = {}
        for seed, rsa_ppm, c0, c1, c2, sem in sv_cal.observations:
            if seed not in by_seed:
                by_seed[seed] = []
            by_seed[seed].append((rsa_ppm, c0, c1, c2, sem))

        # Check each seed has consistent SV_RAW across RSA levels
        for seed, obs_list in by_seed.items():
            if len(obs_list) < 2:
                continue
            # Check if all obs have same c0, c1, c2, sem
            first = obs_list[0]
            for rsa_ppm, c0, c1, c2, sem in obs_list[1:]:
                if abs(c0 - first[1]) > 0.001 or abs(c1 - first[2]) > 0.001 or \
                   abs(c2 - first[3]) > 0.001 or abs(sem - first[4]) > 0.001:
                    print(f"  WARNING: SV baseline {sv_ppm}, seed {seed}: "
                          f"SV_RAW differs across RSA levels!")
                    print(f"    RSA {first[0]}: C0={first[1]:.3f} C1={first[2]:.3f} "
                          f"C2={first[3]:.3f} SEM={first[4]:.3f}")
                    print(f"    RSA {rsa_ppm}: C0={c0:.3f} C1={c1:.3f} "
                          f"C2={c2:.3f} SEM={sem:.3f}")
                    sanity_passed = False

    if sanity_passed:
        print("  ✓ All SV_RAW observations consistent across RSA noise levels")
    print()

    # SV Calibration Table
    print("=" * 78)
    print("SV_RAW_CALIBRATION (Pre-RSA, aggregated across all seeds × RSA levels)")
    print("=" * 78)
    print()
    print(f"{'SV_PPM':>10} {'exp_Ci':>8} {'obs_C0':>8} {'obs_C1':>8} {'obs_C2':>8} "
          f"{'exp_SEM':>8} {'obs_SEM':>8} {'N_epochs':>10}")
    print("-" * 78)

    for sv_ppm in sv_sweep:
        sv_cal = sv_calibrations[sv_ppm]
        print(
            f"{sv_ppm:>10} "
            f"{sv_cal.expected_per_ci:>8.3f} "
            f"{sv_cal.obs_c0:>8.3f} "
            f"{sv_cal.obs_c1:>8.3f} "
            f"{sv_cal.obs_c2:>8.3f} "
            f"{sv_cal.expected_sem_pass:>8.3f} "
            f"{sv_cal.obs_sem_pass:>8.3f} "
            f"{sv_cal.total_epochs:>10}"
        )
    print()
    print(f"  N = {len(seeds)} seeds × {len(rsa_sweep)} RSA levels × 200 epochs = "
          f"{len(seeds) * len(rsa_sweep) * 200} evaluations per baseline")
    print()

    # Surface Table: Uptime
    print("=" * 78)
    print("SURFACE TABLE: Authority Uptime")
    print("=" * 78)
    print()

    # Header
    header = f"{'SV \\\\ RSA':>10}"
    for rsa_ppm in rsa_sweep:
        header += f" | {rsa_ppm:>12}"
    print(header)
    print("-" * (10 + 15 * len(rsa_sweep)))

    for sv_ppm in sv_sweep:
        row = f"{sv_ppm:>10}"
        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            row += f" | {cell.mean_authority_uptime:>11.1%}"
        print(row)
    print()

    # Surface Table: Regime Counts
    print("=" * 78)
    print("SURFACE TABLE: Regime Counts (R/D/X)")
    print("=" * 78)
    print()

    header = f"{'SV \\\\ RSA':>10}"
    for rsa_ppm in rsa_sweep:
        header += f" | {rsa_ppm:>12}"
    print(header)
    print("-" * (10 + 15 * len(rsa_sweep)))

    for sv_ppm in sv_sweep:
        row = f"{sv_ppm:>10}"
        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            regime_str = f"{cell.robust_count}R/{cell.degraded_count}D/{cell.dos_count}X"
            row += f" | {regime_str:>12}"
        print(row)
    print()

    # Surface Table: Mean Lapse Epochs
    print("=" * 78)
    print("SURFACE TABLE: Mean Lapse Epoch Count")
    print("=" * 78)
    print()

    header = f"{'SV \\\\ RSA':>10}"
    for rsa_ppm in rsa_sweep:
        header += f" | {rsa_ppm:>12}"
    print(header)
    print("-" * (10 + 15 * len(rsa_sweep)))

    for sv_ppm in sv_sweep:
        row = f"{sv_ppm:>10}"
        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            row += f" | {cell.mean_lapse_epoch_count_total:>12.1f}"
        print(row)
    print()

    # Surface Table: Max Single Lapse
    print("=" * 78)
    print("SURFACE TABLE: Max Single Lapse (epochs, worst across seeds)")
    print("=" * 78)
    print()

    header = f"{'SV \\\\ RSA':>10}"
    for rsa_ppm in rsa_sweep:
        header += f" | {rsa_ppm:>12}"
    print(header)
    print("-" * (10 + 15 * len(rsa_sweep)))

    for sv_ppm in sv_sweep:
        row = f"{sv_ppm:>10}"
        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            row += f" | {cell.max_max_single_lapse_epochs:>12}"
        print(row)
    print()

    # Boundary Table
    print("=" * 78)
    print("BOUNDARY TABLE")
    print("=" * 78)
    print()
    print("For each SV baseline:")
    print("  - Highest RSA noise with 5×ROBUST (all seeds ROBUST)")
    print("  - Lowest RSA noise with any lapses (mean_lapse_epochs > 0)")
    print()
    print(f"{'SV_PPM':>10} {'max_all_robust':>15} {'min_with_lapses':>18}")
    print("-" * 45)

    for sv_ppm in sv_sweep:
        max_all_robust = None
        min_with_lapses = None

        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            if cell.robust_count == 5:
                max_all_robust = rsa_ppm
            if cell.mean_lapse_epoch_count_total > 0 and min_with_lapses is None:
                min_with_lapses = rsa_ppm

        max_robust_str = f"{max_all_robust}" if max_all_robust is not None else "none"
        min_lapse_str = f"{min_with_lapses}" if min_with_lapses is not None else "none"
        print(f"{sv_ppm:>10} {max_robust_str:>15} {min_lapse_str:>18}")
    print()

    # RSA Flip Summary
    print("=" * 78)
    print("RSA FLIP SUMMARY (per cell)")
    print("=" * 78)
    print()
    print(f"{'SV':>8} {'RSA':>8} {'targets':>10} {'flips':>8} {'pivotal':>8} {'piv_rate':>10}")
    print("-" * 56)

    for sv_ppm in sv_sweep:
        for rsa_ppm in rsa_sweep:
            if rsa_ppm == 0:
                continue  # No flips at RSA=0
            cell = grid[(sv_ppm, rsa_ppm)]
            print(
                f"{sv_ppm:>8} "
                f"{rsa_ppm:>8} "
                f"{cell.sum_targets:>10} "
                f"{cell.sum_flips:>8} "
                f"{cell.sum_pivotal_flips:>8} "
                f"{cell.pivotal_rate:>9.1%}"
            )
    print()

    # Hypothesis Validation
    print("=" * 78)
    print("HYPOTHESIS VALIDATION")
    print("=" * 78)

    # H4: Robustness Surface Continuity
    print("\n### H4: Robustness Surface Continuity")
    print("Check: For fixed SV baseline, governance degrades monotonically with RSA noise")

    h4_inversions = 0
    for sv_ppm in sv_sweep:
        prev_lapse = None
        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            curr_lapse = cell.mean_lapse_epoch_count_total
            if prev_lapse is not None and curr_lapse < prev_lapse - 0.5:
                # Allow small tolerance for noise
                h4_inversions += 1
                print(f"  Inversion at SV={sv_ppm}, RSA={rsa_ppm}: "
                      f"lapses decreased from {prev_lapse:.1f} to {curr_lapse:.1f}")
            prev_lapse = curr_lapse

    if h4_inversions == 0:
        print("  No inversions detected.")
        print("  H4 Status: SUPPORTED")
        h4_status = "SUPPORTED"
    elif h4_inversions <= 3:
        print(f"  {h4_inversions} minor inversion(s) detected.")
        print("  H4 Status: INCONCLUSIVE")
        h4_status = "INCONCLUSIVE"
    else:
        print(f"  {h4_inversions} inversions detected.")
        print("  H4 Status: NOT SUPPORTED")
        h4_status = "NOT SUPPORTED"

    # H5: Phase Boundary Shift
    print("\n### H5: Phase Boundary Shift")
    print("Check: Critical RSA noise (first lapses) increases with higher SV baseline")

    critical_rsa = []
    for sv_ppm in sv_sweep:
        first_lapse_rsa = None
        for rsa_ppm in rsa_sweep:
            cell = grid[(sv_ppm, rsa_ppm)]
            if cell.mean_lapse_epoch_count_total > 0:
                first_lapse_rsa = rsa_ppm
                break
        critical_rsa.append((sv_ppm, first_lapse_rsa))
        print(f"  SV={sv_ppm}: first lapses at RSA={first_lapse_rsa}")

    # Check if critical RSA is non-decreasing with SV
    h5_inversions = 0
    for i in range(1, len(critical_rsa)):
        prev_sv, prev_rsa = critical_rsa[i - 1]
        curr_sv, curr_rsa = critical_rsa[i]
        if prev_rsa is not None and curr_rsa is not None and curr_rsa < prev_rsa:
            h5_inversions += 1
            print(f"  Inversion: SV {prev_sv}→{curr_sv} has critical RSA {prev_rsa}→{curr_rsa}")

    if h5_inversions == 0:
        print("  Critical RSA is non-decreasing with SV baseline.")
        print("  H5 Status: SUPPORTED")
        h5_status = "SUPPORTED"
    else:
        print(f"  {h5_inversions} inversion(s) detected.")
        print("  H5 Status: NOT SUPPORTED")
        h5_status = "NOT SUPPORTED"

    # H6: CTA Persistence
    print("\n### H6: CTA Persistence")
    print("Check: Across non-DOS cells, lapse durations cluster near amnesty_interval multiples")

    all_durations = []
    for (sv_ppm, rsa_ppm), cell in grid.items():
        if cell.dos_count > 0:
            continue  # Skip DOS cells
        for sr in cell.seed_results:
            all_durations.extend(sr.lapse_durations)

    if len(all_durations) == 0:
        print("  No lapses observed in non-DOS cells; cannot analyze.")
        print("  H6 Status: INCONCLUSIVE")
        h6_status = "INCONCLUSIVE"
    else:
        amnesty = config.amnesty_interval
        near_multiple = 0
        for d in all_durations:
            remainder = d % amnesty
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

        if fraction_near > 0.3:
            print("  H6 Status: SUPPORTED")
            h6_status = "SUPPORTED"
        else:
            print("  H6 Status: NOT SUPPORTED (clustering not evident)")
            h6_status = "NOT SUPPORTED"

    # Hypothesis Summary
    print("\n### Hypothesis Summary")
    print(f"  H4 (Surface Continuity):    {h4_status}")
    print(f"  H5 (Phase Boundary Shift):  {h5_status}")
    print(f"  H6 (CTA Persistence):       {h6_status}")

    print("\n" + "=" * 78)
    print("RUN 2 COMPLETE")
    print("=" * 78)

    return grid, sv_calibrations


if __name__ == "__main__":
    run_surface_sweep()
