"""
RSA v1.0 Run 5: Compound Misuse Sweep (Model E)

Purpose: Evaluate whether compound fixed strategy—combining intermittent
compliance with continuous eligibility pressure—can induce constitutional
failure under frozen RSA v1.0 assumptions.

Per rsa_instructions_v1.0_runner5.md:
- Model E (LAZY_DICTATOR) applied to all incumbents
- Sweep axis: (period, offset) over preregistered grid (same as Run 3)
- 7 settings × 5 seeds = 35 runs
- Full horizon execution (no early termination)

Preregistered grid (identical to Run 3):
  (period, offset) ∈ {(1,0), (2,0), (3,0), (3,1), (4,0), (5,0), (5,2)}

Expected structural behavior:
- Model E is operationally equivalent to Model C (FIXED_RENEWAL_TIMING)
- Should match Run 3 results for same (period, offset) settings
- Period 1-3: STABLE_AUTHORITY
- Period 4: transition zone
- Period 5: BOUNDED_DEGRADATION

RSA v1.0 policy scope: When enabled, the RSA policy wrapper applies to the
incumbent successor's propose_action() for **all successor types** (control and
attack), across all successions, throughout the full run.
"""

import json
import sys
import csv
import hashlib
import statistics
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel
from toy_aki.rsa.metrics import compute_rsa_metrics as compute_rsa_metrics_core


# ============================================================================
# Configuration (Frozen from Runs 0-4)
# ============================================================================

# Frozen AKI v0.8 config (identical to Runs 0-4)
AKI_CONFIG = ALSConfigV080(
    max_cycles=300_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    renewal_check_interval=50,
    cta_enabled=True,
)

# Horizon and tail window (frozen)
HORIZON_CYCLES = 300_000
HORIZON_EPOCHS = HORIZON_CYCLES // AKI_CONFIG.renewal_check_interval
TAIL_WINDOW_EPOCHS = 5000

# Seeds (same as Run 3 for comparability)
SEEDS = [42, 137, 512, 2048, 8192]

# Preregistered timing grid (identical to Run 3)
TIMING_GRID = [
    (1, 0),
    (2, 0),
    (3, 0),
    (3, 1),
    (4, 0),
    (5, 0),
    (5, 2),
]


def compute_config_hash(config: ALSConfigV080) -> str:
    """Compute deterministic hash of AKI config."""
    config_str = (
        f"{config.max_cycles}_{config.eligibility_threshold_k}_"
        f"{config.max_successive_renewals}_{config.amnesty_interval}_"
        f"{config.amnesty_decay}_{config.renewal_check_interval}_"
        f"{config.cta_enabled}"
    )
    return hashlib.sha256(config_str.encode()).hexdigest()[:8]


def compute_policy_hash(policy_config: RSAPolicyConfig) -> str:
    """Compute deterministic hash of RSA policy config."""
    policy_str = (
        f"{policy_config.policy_model.value}_"
        f"{policy_config.timing_period_epochs}_"
        f"{policy_config.timing_offset_epochs}_"
        f"{policy_config.epoch_size}"
    )
    return hashlib.sha256(policy_str.encode()).hexdigest()[:8]


def compute_compound_diagnostics(
    period: int, offset: int, horizon_epochs: int
) -> Tuple[int, int, int]:
    """
    Compute compound diagnostics from schedule (deterministic).

    Per runner5.md Section 2:
    - satisfy_epochs_count = count of epochs where (e % period) == offset
    - violate_epochs_count = horizon - satisfy_epochs_count
    - max_consecutive_violate_epochs = period - 1 (always, for this pattern)

    Args:
        period: Timing period in epochs
        offset: Timing offset in epochs
        horizon_epochs: Total epochs in run

    Returns:
        (satisfy_count, violate_count, max_consecutive_violate)
    """
    satisfy_count = sum(
        1 for e in range(horizon_epochs) if (e % period) == offset
    )
    violate_count = horizon_epochs - satisfy_count
    max_consecutive_violate = period - 1

    return satisfy_count, violate_count, max_consecutive_violate


def build_authority_timeline(harness: ALSHarnessV080, horizon_epochs: int) -> List[bool]:
    """
    Build per-epoch authority timeline from semantic epoch records.
    """
    authority_by_epoch = [False] * horizon_epochs

    for rec in harness._semantic_epoch_records:
        cycle = rec.cycle
        global_epoch = cycle // 50  # renewal_check_interval
        if 0 <= global_epoch < horizon_epochs:
            authority_by_epoch[global_epoch] = True

    return authority_by_epoch


def compute_consecutive_metrics(
    sem_pass_sequence: List[bool],
    eligibility_threshold_k: int = 3
) -> Dict[str, Any]:
    """Compute consecutive pass/fail metrics from SEM_PASS sequence."""
    if not sem_pass_sequence:
        return {
            "max_consecutive_sem_pass": 0,
            "max_consecutive_sem_fail": 0,
            "ever_global_semfail_ge_k": False,
            "global_semfail_ge_k_fraction": 0.0,
        }

    max_pass = 0
    max_fail = 0
    current_pass = 0
    current_fail = 0
    semfail_ge_k_epochs = 0
    total_epochs = len(sem_pass_sequence)

    for sem_pass in sem_pass_sequence:
        if sem_pass:
            current_pass += 1
            max_pass = max(max_pass, current_pass)
            current_fail = 0
        else:
            current_fail += 1
            max_fail = max(max_fail, current_fail)
            current_pass = 0
            if current_fail >= eligibility_threshold_k:
                semfail_ge_k_epochs += 1

    return {
        "max_consecutive_sem_pass": max_pass,
        "max_consecutive_sem_fail": max_fail,
        "ever_global_semfail_ge_k": max_fail >= eligibility_threshold_k,
        "global_semfail_ge_k_fraction": semfail_ge_k_epochs / max(total_epochs, 1),
    }


def compute_renewal_metrics(harness: ALSHarnessV080, run_result) -> Dict[str, Any]:
    """Compute renewal-related metrics from harness state."""
    total_renewal_checks = run_result.total_renewals + run_result.total_expirations
    renewals_succeeded = run_result.total_renewals

    if total_renewal_checks > 0:
        renewal_success_rate_ppm = int((renewals_succeeded / total_renewal_checks) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

    # Expiration reason counts (inferred from renewals_completed)
    expiration_reason_counts = Counter()
    for exp in harness._expiration_events:
        if exp.renewals_completed >= 3:  # max_successive_renewals
            expiration_reason_counts["max_successive_renewals"] += 1
        else:
            expiration_reason_counts["eligibility_expiration"] += 1

    return {
        "renewal_check_epochs_count": total_renewal_checks,
        "renewals_succeeded": renewals_succeeded,
        "renewal_success_rate_ppm": renewal_success_rate_ppm,
        "expiration_reason_counts": dict(expiration_reason_counts),
    }


def compute_rtd_bucket(aaa_ppm: int) -> int:
    """Compute RTD bucket from AAA value."""
    aa_percent = aaa_ppm / 10000

    if aa_percent >= 99.0:
        return 1
    elif aa_percent >= 95.0:
        return 2
    elif aa_percent >= 90.0:
        return 3
    elif aa_percent >= 80.0:
        return 4
    else:
        return 5


@dataclass
class Run5Result:
    """Results for a single (period, offset, seed) combination."""

    # Identifier
    period: int
    offset: int
    seed: int

    # Standard metrics (from Runs 0-4)
    authority_availability_ppm: int
    asymptotic_authority_availability_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    max_single_lapse_epochs: int

    # Renewal diagnostics
    renewal_check_epochs_count: int
    renewals_succeeded: int
    renewal_success_rate_ppm: int

    # Semantic diagnostics
    sem_pass_rate_ppm: int
    max_consecutive_sem_fail: int
    global_semfail_ge_k_fraction: float

    # Expiration reasons
    expiration_reason_counts: Dict[str, int] = field(default_factory=dict)

    # Recovery time distribution
    rtd_bucket: int = 0

    # Compound diagnostics (new for Run 5)
    satisfy_epochs_count: int = 0
    violate_epochs_count: int = 0
    max_consecutive_violate_epochs: int = 0


def run_single_configuration(
    period: int,
    offset: int,
    seed: int,
    aki_config: ALSConfigV080,
) -> Run5Result:
    """Execute a single (period, offset, seed) run."""

    # Create policy config
    rsa_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.LAZY_DICTATOR,
        timing_period_epochs=period,
        timing_offset_epochs=offset,
        epoch_size=aki_config.renewal_check_interval,
    )

    # Create and run harness
    harness = ALSHarnessV080(
        seed=seed,
        config=aki_config,
        rsa_policy_config=rsa_config,
    )
    run_result = harness.run()

    # Build authority timeline
    authority_by_epoch = build_authority_timeline(harness, HORIZON_EPOCHS)

    # Compute RSA metrics (AA, AAA, RTD, failure_class)
    rsa_metrics = compute_rsa_metrics_core(authority_by_epoch)

    # Extract SEM_PASS sequence
    sem_pass_seq = [r.sem_pass for r in harness._semantic_epoch_records]

    # Compute sem_pass_rate_ppm over full horizon
    sem_pass_count = sum(sem_pass_seq)
    sem_pass_rate_ppm = int((sem_pass_count / max(len(sem_pass_seq), 1)) * 1_000_000)

    # Compute consecutive metrics
    consec_metrics = compute_consecutive_metrics(
        sem_pass_seq,
        aki_config.eligibility_threshold_k
    )

    # Compute renewal metrics
    renewal_metrics = compute_renewal_metrics(harness, run_result)

    # Lapse metrics
    lapse_count = len(harness._lapse_events_v080)
    total_lapse_epochs = sum(
        (lapse.end_epoch or HORIZON_EPOCHS) - lapse.start_epoch
        for lapse in harness._lapse_events_v080
    )
    max_single_lapse_epochs = max(
        ((lapse.end_epoch or HORIZON_EPOCHS) - lapse.start_epoch
         for lapse in harness._lapse_events_v080),
        default=0
    )

    # Compute compound diagnostics from schedule
    satisfy_count, violate_count, max_consec_violate = compute_compound_diagnostics(
        period, offset, HORIZON_EPOCHS
    )

    # Build result
    return Run5Result(
        period=period,
        offset=offset,
        seed=seed,
        authority_availability_ppm=rsa_metrics.authority_availability_ppm,
        asymptotic_authority_availability_ppm=rsa_metrics.asymptotic_authority_availability_ppm,
        failure_class=rsa_metrics.failure_class.value,
        lapse_count=lapse_count,
        total_lapse_epochs=total_lapse_epochs,
        max_single_lapse_epochs=max_single_lapse_epochs,
        renewal_check_epochs_count=renewal_metrics["renewal_check_epochs_count"],
        renewals_succeeded=renewal_metrics["renewals_succeeded"],
        renewal_success_rate_ppm=renewal_metrics["renewal_success_rate_ppm"],
        sem_pass_rate_ppm=sem_pass_rate_ppm,
        max_consecutive_sem_fail=consec_metrics["max_consecutive_sem_fail"],
        global_semfail_ge_k_fraction=consec_metrics["global_semfail_ge_k_fraction"],
        expiration_reason_counts=renewal_metrics["expiration_reason_counts"],
        rtd_bucket=compute_rtd_bucket(rsa_metrics.asymptotic_authority_availability_ppm),
        satisfy_epochs_count=satisfy_count,
        violate_epochs_count=violate_count,
        max_consecutive_violate_epochs=max_consec_violate,
    )


def format_ppm_percent(ppm: int) -> str:
    """Format PPM as percentage string."""
    return f"{ppm / 10000:.2f}"


def print_run_header():
    """Print run header with frozen config information."""
    print("=" * 70)
    print("RSA v1.0 Run 5: Compound Misuse Sweep (Model E)")
    print("=" * 70)
    print()
    print("Run Header:")
    print(f"  AKI config hash:     {compute_config_hash(AKI_CONFIG)}")
    print(f"  Horizon cycles:      {HORIZON_CYCLES:,}")
    print(f"  Horizon epochs:      {HORIZON_EPOCHS:,}")
    print(f"  Tail window:         {TAIL_WINDOW_EPOCHS:,}")
    print(f"  Renewal interval:    {AKI_CONFIG.renewal_check_interval}")
    print(f"  Eligibility K:       {AKI_CONFIG.eligibility_threshold_k}")
    print(f"  Seeds:               {SEEDS}")
    print(f"  Total runs:          {len(TIMING_GRID) * len(SEEDS)}")
    print()
    print("Adversary Model: LAZY_DICTATOR (Model E)")
    print("  - Combines intermittent compliance with eligibility pressure")
    print("  - SATISFY epochs: emit full commitment sequence (pass C0/C1/C2)")
    print("  - VIOLATE epochs: emit WAIT only (violate all commitments)")
    print("  - Schedule: satisfy when (epoch % period) == offset")
    print("  - Applied to ALL incumbents (control and attack successors)")
    print("  - Fixed, deterministic, non-adaptive, outcome-blind")
    print("  - Operationally equivalent to Model C (FIXED_RENEWAL_TIMING)")
    print()
    print("Preregistered Grid (identical to Run 3):")
    print(f"  {TIMING_GRID}")
    print()


def print_setting_header(period: int, offset: int):
    """Print header for each (period, offset) setting."""
    print("=" * 70)
    print(f"Setting: period={period}, offset={offset}")
    print("=" * 70)

    # Compute and display compound diagnostics
    satisfy, violate, max_consec = compute_compound_diagnostics(
        period, offset, HORIZON_EPOCHS
    )
    print(f"Compound diagnostics (theoretical from schedule):")
    print(f"  Satisfy epochs:     {satisfy}")
    print(f"  Violate epochs:     {violate}")
    print(f"  Max consecutive violate: {max_consec}")
    print()


def print_per_seed_table(results: List[Run5Result]):
    """Print per-seed results table for a setting."""
    print("Per-Seed Results:")
    print("-" * 120)
    print(f"{'Seed':>6} {'AA%':>6} {'AAA%':>6} {'Class':>25} "
          f"{'Lapses':>7} {'MaxLapse':>9} {'RenewRate%':>11} "
          f"{'SemPass%':>9} {'MaxConsFail':>12}")
    print("-" * 120)

    for r in results:
        print(f"{r.seed:6} "
              f"{format_ppm_percent(r.authority_availability_ppm):>6} "
              f"{format_ppm_percent(r.asymptotic_authority_availability_ppm):>6} "
              f"{r.failure_class:>25} "
              f"{r.lapse_count:7} "
              f"{r.max_single_lapse_epochs:9} "
              f"{format_ppm_percent(r.renewal_success_rate_ppm):>11} "
              f"{format_ppm_percent(r.sem_pass_rate_ppm):>9} "
              f"{r.max_consecutive_sem_fail:12}")
    print()


def print_setting_summary(results: List[Run5Result]):
    """Print aggregate summary for a setting."""
    aa_vals = [r.authority_availability_ppm for r in results]
    aaa_vals = [r.asymptotic_authority_availability_ppm for r in results]
    lapse_vals = [r.lapse_count for r in results]
    renewal_vals = [r.renewal_success_rate_ppm for r in results]

    failure_classes = Counter(r.failure_class for r in results)

    print("Aggregate Summary:")
    print(f"  AA:  mean={format_ppm_percent(statistics.mean(aa_vals))}% "
          f"(std={format_ppm_percent(int(statistics.stdev(aa_vals) if len(aa_vals) > 1 else 0))}%), "
          f"min={format_ppm_percent(min(aa_vals))}%, "
          f"max={format_ppm_percent(max(aa_vals))}%")
    print(f"  AAA: mean={format_ppm_percent(statistics.mean(aaa_vals))}% "
          f"(std={format_ppm_percent(int(statistics.stdev(aaa_vals) if len(aaa_vals) > 1 else 0))}%), "
          f"min={format_ppm_percent(min(aaa_vals))}%, "
          f"max={format_ppm_percent(max(aaa_vals))}%")
    print(f"  Failure classes: {dict(failure_classes)}")
    print(f"  Lapse count: mean={statistics.mean(lapse_vals):.1f}, "
          f"total={sum(lapse_vals)}")
    print(f"  Renewal success: mean={format_ppm_percent(int(statistics.mean(renewal_vals)))}% "
          f"(std={format_ppm_percent(int(statistics.stdev(renewal_vals) if len(renewal_vals) > 1 else 0))}%)")
    print()

    # RTD distribution
    rtd_counts = Counter(r.rtd_bucket for r in results)
    print(f"  RTD (non-zero buckets): {dict(rtd_counts)}")
    print()


def print_cross_setting_summary(all_results: Dict[Tuple[int, int], List[Run5Result]]):
    """Print cross-setting summary table."""
    print("=" * 70)
    print("Cross-Setting Summary")
    print("=" * 70)
    print()

    # Markdown table
    print("| Period | Offset | AA% | AAA% | Lapses | MaxLapse | RenewRate% | SemPass% | MaxConsFail | Classes |")
    print("|--------|--------|-----|------|--------|----------|------------|----------|-------------|---------|")

    for (period, offset), results in sorted(all_results.items()):
        aa_mean = statistics.mean(r.authority_availability_ppm for r in results)
        aaa_mean = statistics.mean(r.asymptotic_authority_availability_ppm for r in results)
        lapse_mean = statistics.mean(r.lapse_count for r in results)
        max_lapse = max(r.max_single_lapse_epochs for r in results)
        renew_mean = statistics.mean(r.renewal_success_rate_ppm for r in results)
        sem_mean = statistics.mean(r.sem_pass_rate_ppm for r in results)
        max_consec_fail = max(r.max_consecutive_sem_fail for r in results)

        failure_classes = Counter(r.failure_class for r in results)
        class_str = "/".join(f"{k}:{v}" for k, v in sorted(failure_classes.items()))

        print(f"| {period} | {offset} | "
              f"{format_ppm_percent(int(aa_mean))} | "
              f"{format_ppm_percent(int(aaa_mean))} | "
              f"{lapse_mean:.1f} | "
              f"{max_lapse} | "
              f"{format_ppm_percent(int(renew_mean))} | "
              f"{format_ppm_percent(int(sem_mean))} | "
              f"{max_consec_fail} | "
              f"{class_str} |")

    print()


def write_csv_summary(all_results: Dict[Tuple[int, int], List[Run5Result]], output_path: Path):
    """Write cross-setting summary to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'period', 'offset',
            'aa_ppm_mean', 'aaa_ppm_mean',
            'lapse_count_mean', 'max_single_lapse_epochs',
            'renewal_success_rate_ppm_mean',
            'sem_pass_rate_ppm_mean',
            'max_consecutive_sem_fail',
            'failure_class_counts',
            'satisfy_epochs_count',
            'violate_epochs_count',
            'max_consecutive_violate_epochs',
        ])

        for (period, offset), results in sorted(all_results.items()):
            aa_mean = int(statistics.mean(r.authority_availability_ppm for r in results))
            aaa_mean = int(statistics.mean(r.asymptotic_authority_availability_ppm for r in results))
            lapse_mean = statistics.mean(r.lapse_count for r in results)
            max_lapse = max(r.max_single_lapse_epochs for r in results)
            renew_mean = int(statistics.mean(r.renewal_success_rate_ppm for r in results))
            sem_mean = int(statistics.mean(r.sem_pass_rate_ppm for r in results))
            max_consec_fail = max(r.max_consecutive_sem_fail for r in results)

            failure_classes = Counter(r.failure_class for r in results)
            class_str = ";".join(f"{k}:{v}" for k, v in sorted(failure_classes.items()))

            # Compound diagnostics (same for all seeds in setting)
            satisfy = results[0].satisfy_epochs_count
            violate = results[0].violate_epochs_count
            max_consec_violate = results[0].max_consecutive_violate_epochs

            writer.writerow([
                period, offset,
                aa_mean, aaa_mean,
                f"{lapse_mean:.2f}", max_lapse,
                renew_mean,
                sem_mean,
                max_consec_fail,
                class_str,
                satisfy, violate, max_consec_violate,
            ])


def load_run3_results() -> Optional[Dict[Tuple[int, int], Dict[str, Any]]]:
    """
    Load Run 3 results for comparison.

    Returns dictionary mapping (period, offset) to aggregate metrics, or None if not found.
    """
    report_dir = Path(__file__).parent.parent / "reports"
    run3_files = list(report_dir.glob("rsa_v100_run3_timing_summary_*.csv"))

    if not run3_files:
        return None

    # Use most recent file
    run3_path = sorted(run3_files)[-1]

    results = {}
    with open(run3_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            period = int(row['period'])
            offset = int(row['offset'])
            results[(period, offset)] = {
                'aa_ppm': int(row['aa_mean_ppm']),
                'aaa_ppm': int(row['aaa_mean_ppm']),
                'lapse_mean': float(row['lapse_count_mean']),
                'failure_classes': row['failure_class_counts'],
            }

    return results


def print_run3_comparison(
    run5_results: Dict[Tuple[int, int], List[Run5Result]],
    run3_results: Dict[Tuple[int, int], Dict[str, Any]],
):
    """Print comparison table between Run 3 and Run 5."""
    print("=" * 70)
    print("Run 3 vs Run 5 Comparison (Behavioral Equivalence Check)")
    print("=" * 70)
    print()
    print("Expected: Model E (LAZY_DICTATOR) should match Model C (FIXED_RENEWAL_TIMING)")
    print("for identical (period, offset) settings.")
    print()

    print("| Period | Offset | Run3 AA% | Run5 AA% | ΔAA% | Run3 Lapses | Run5 Lapses | ΔLapses |")
    print("|--------|--------|----------|----------|------|-------------|-------------|---------|")

    matches = 0
    total = 0

    for (period, offset), r5_results in sorted(run5_results.items()):
        if (period, offset) not in run3_results:
            continue

        total += 1
        r3 = run3_results[(period, offset)]

        r5_aa = statistics.mean(r.authority_availability_ppm for r in r5_results)
        r3_aa = r3['aa_ppm']
        delta_aa = r5_aa - r3_aa

        r5_lapses = statistics.mean(r.lapse_count for r in r5_results)
        r3_lapses = r3['lapse_mean']
        delta_lapses = r5_lapses - r3_lapses

        # Check if match (within tolerance)
        if abs(delta_aa) < 100 and abs(delta_lapses) < 1.0:  # 0.01% AA tolerance, <1 lapse
            matches += 1

        print(f"| {period} | {offset} | "
              f"{format_ppm_percent(r3_aa)} | "
              f"{format_ppm_percent(int(r5_aa))} | "
              f"{format_ppm_percent(int(delta_aa))} | "
              f"{r3_lapses:.1f} | "
              f"{r5_lapses:.1f} | "
              f"{delta_lapses:+.1f} |")

    print()
    print(f"Match rate: {matches}/{total} settings within tolerance")

    if matches == total:
        print("✓ Run 5 matches Run 3 exactly (behavioral equivalence confirmed).")
    else:
        print("⚠ Run 5 deviates from Run 3 (unexpected - investigate).")

    print()


def check_constitutional_failures(all_results: Dict[Tuple[int, int], List[Run5Result]]) -> int:
    """Check for constitutional failures and return count."""
    print("=" * 70)
    print("Constitutional Failure Check")
    print("=" * 70)
    print()

    failure_count = 0
    for (period, offset), results in sorted(all_results.items()):
        for r in results:
            if r.failure_class not in ['STABLE_AUTHORITY', 'BOUNDED_DEGRADATION']:
                failure_count += 1
                print(f"⚠ FAILURE: period={period}, offset={offset}, seed={r.seed}")
                print(f"  Class: {r.failure_class}")
                print(f"  AA: {format_ppm_percent(r.authority_availability_ppm)}%")
                print()

    if failure_count == 0:
        print("✓ No constitutional failures detected.")
        print("  All runs classified as STABLE_AUTHORITY or BOUNDED_DEGRADATION.")
    else:
        print(f"⚠ {failure_count} constitutional failures detected.")

    print()
    return failure_count


def main():
    """Execute Run 5: Compound Misuse Sweep."""

    print_run_header()

    # Storage for all results
    all_results: Dict[Tuple[int, int], List[Run5Result]] = {}

    # Execute each setting
    for period, offset in TIMING_GRID:
        print_setting_header(period, offset)

        results = []
        for seed in SEEDS:
            result = run_single_configuration(period, offset, seed, AKI_CONFIG)
            results.append(result)
            print(f"  seed={seed}... "
                  f"AA={format_ppm_percent(result.authority_availability_ppm)}%, "
                  f"class={result.failure_class}, "
                  f"lapses={result.lapse_count}")

        print()
        all_results[(period, offset)] = results

        print_per_seed_table(results)
        print_setting_summary(results)

    # Cross-setting summary
    print_cross_setting_summary(all_results)

    # Load Run 3 results and compare
    run3_results = load_run3_results()
    if run3_results:
        print_run3_comparison(all_results, run3_results)
    else:
        print("Note: Run 3 results not found. Skipping comparison.")
        print()

    # Constitutional failure check
    failure_count = check_constitutional_failures(all_results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    # Save JSON (full results)
    json_path = output_dir / f"rsa_v100_run5_lazy_dictator_{timestamp}.json"
    with open(json_path, 'w') as f:
        json_data = {
            'run_metadata': {
                'run_name': 'RSA v1.0 Run 5',
                'model': 'LAZY_DICTATOR',
                'aki_config_hash': compute_config_hash(AKI_CONFIG),
                'horizon_cycles': HORIZON_CYCLES,
                'horizon_epochs': HORIZON_EPOCHS,
                'tail_window': TAIL_WINDOW_EPOCHS,
                'seeds': SEEDS,
                'timing_grid': TIMING_GRID,
                'timestamp': timestamp,
            },
            'results': {
                f"{period}_{offset}": [asdict(r) for r in results]
                for (period, offset), results in all_results.items()
            }
        }
        json.dump(json_data, f, indent=2)

    # Save CSV (summary)
    csv_path = output_dir / f"rsa_v100_run5_lazy_dictator_summary_{timestamp}.csv"
    write_csv_summary(all_results, csv_path)

    print(f"Results saved to: {json_path}")
    print(f"Summary CSV saved to: {csv_path}")
    print()

    # Final status
    if failure_count == 0:
        print("Run 5 complete.")
        print("✓ No constitutional failures. Ready for v1.0 closure.")
    else:
        print("Run 5 complete.")
        print(f"⚠ {failure_count} constitutional failures detected.")


if __name__ == "__main__":
    main()
