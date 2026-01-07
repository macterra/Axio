"""
RSA v1.0 Run 3: Fixed Timing Misuse Sweep (Model C)

Purpose: Evaluate whether deterministic timing patterns of compliance and
violation—without learning, adaptation, or deception—can induce constitutional
failure under frozen RSA v1.0 assumptions.

Per rsa_instructions_v1.0_runner3.md:
- Model C (FIXED_RENEWAL_TIMING) applied to all incumbents
- Sweep axis: (period, offset) over preregistered grid
- 7 settings × 5 seeds = 35 runs
- Full horizon execution (no early termination)

Preregistered grid:
  (period, offset) ∈ {(1,0), (2,0), (3,0), (3,1), (4,0), (5,0), (5,2)}

Expected structural behavior:
- Period 1-3: Max consecutive fails < K=3 → always eligible
- Period 4-5: Max consecutive fails ≥ K=3 → enters ineligibility states

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
from toy_aki.rsa.metrics import (
    compute_rsa_metrics,
    compute_tail_window,
    RSAMetrics,
    FailureClass,
    RTD_BUCKET_LABELS,
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class RunConfig:
    """Configuration for RSA v1.0 Run 3 (frozen per spec)."""

    # Frozen parameters (identical to Runs 0-2)
    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    max_successive_renewals: int = 3
    amnesty_interval: int = 10
    amnesty_decay: int = 1
    cta_enabled: bool = True

    # Run 3 seed battery (5 seeds)
    seeds: List[int] = field(default_factory=lambda: [42, 137, 512, 2048, 8192])

    # Preregistered (period, offset) grid
    timing_grid: List[Tuple[int, int]] = field(default_factory=lambda: [
        (1, 0),
        (2, 0),
        (3, 0),
        (3, 1),
        (4, 0),
        (5, 0),
        (5, 2),
    ])

    @property
    def horizon_epochs(self) -> int:
        return self.max_cycles // self.renewal_check_interval

    @property
    def tail_window(self) -> int:
        return compute_tail_window(self.horizon_epochs)

    def config_hash(self) -> str:
        """Compute deterministic hash of frozen config."""
        config_str = f"{self.max_cycles}:{self.renewal_check_interval}:{self.eligibility_threshold_k}"
        config_str += f":{self.max_successive_renewals}:{self.amnesty_interval}:{self.amnesty_decay}"
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def policy_hash(self, period: int, offset: int) -> str:
        """Compute hash of policy config for given timing parameters."""
        policy_str = f"FIXED_RENEWAL_TIMING:{period}:{offset}:{self.renewal_check_interval}"
        return hashlib.md5(policy_str.encode()).hexdigest()[:8]


# =============================================================================
# Metrics Computation (reused from Runs 0-2)
# =============================================================================

def build_authority_timeline(harness: ALSHarnessV080, horizon_epochs: int) -> List[bool]:
    """Build per-epoch authority timeline from semantic epoch records."""
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

    # Expiration reason counts
    expiration_reason_counts = Counter()
    for exp in harness._expiration_events:
        if exp.renewals_completed >= 3:  # max_successive_renewals
            expiration_reason_counts["max_successive_renewals"] += 1
        else:
            expiration_reason_counts["other"] += 1

    return {
        "renewal_check_epochs_count": total_renewal_checks,
        "renewals_succeeded": renewals_succeeded,
        "renewal_success_rate_ppm": renewal_success_rate_ppm,
        "expiration_reason_counts": dict(expiration_reason_counts),
    }


def compute_full_metrics(
    harness: ALSHarnessV080,
    run_result,
    config: RunConfig,
    seed: int,
    period: int,
    offset: int,
) -> Dict[str, Any]:
    """Compute all required metrics for a single run."""
    horizon_epochs = config.horizon_epochs

    # Build authority timeline
    authority_by_epoch = build_authority_timeline(harness, horizon_epochs)

    # Compute RSA metrics (AA, AAA, RTD, failure_class)
    rsa_metrics = compute_rsa_metrics(authority_by_epoch)

    # Extract SEM_PASS sequence
    sem_pass_seq = [r.sem_pass for r in harness._semantic_epoch_records]

    # Compute sem_pass_rate_ppm over full horizon
    sem_pass_count = sum(sem_pass_seq)
    sem_pass_rate_ppm = int((sem_pass_count / max(len(sem_pass_seq), 1)) * 1_000_000)

    # Compute v1.0 consecutive metrics
    consec_metrics = compute_consecutive_metrics(
        sem_pass_seq,
        config.eligibility_threshold_k
    )

    # Compute renewal metrics
    renewal_metrics = compute_renewal_metrics(harness, run_result)

    # Lapse metrics
    lapse_count = len(harness._lapse_events_v080)
    total_lapse_epochs = sum(
        (lapse.end_epoch or horizon_epochs) - lapse.start_epoch
        for lapse in harness._lapse_events_v080
    )
    max_single_lapse_epochs = max(
        ((lapse.end_epoch or horizon_epochs) - lapse.start_epoch
         for lapse in harness._lapse_events_v080),
        default=0
    )
    epochs_in_lapse = rsa_metrics.lapse_epochs

    return {
        # Run identification
        "run_id": f"rsa_v100_run3_timing_p{period}_o{offset}_seed{seed}",
        "seed": seed,
        "period": period,
        "offset": offset,

        # RSA state
        "rsa_enabled": True,
        "rsa_model": "FIXED_RENEWAL_TIMING",

        # Basic run info
        "total_cycles": run_result.total_cycles,
        "epochs_evaluated": len(sem_pass_seq),

        # Timing-pattern diagnostics (new for Run 3)
        "sem_pass_rate_ppm": sem_pass_rate_ppm,

        # Governance outcomes
        "authority_availability_ppm": rsa_metrics.authority_availability_ppm,
        "asymptotic_authority_availability_ppm": rsa_metrics.asymptotic_authority_availability_ppm,
        "failure_class": rsa_metrics.failure_class.value,
        "recovery_time_histogram": rsa_metrics.recovery_time_histogram,

        # Lapse metrics
        "lapse_count": lapse_count,
        "total_lapse_epochs": total_lapse_epochs,
        "max_single_lapse_epochs": max_single_lapse_epochs,
        "epochs_in_lapse": epochs_in_lapse,

        # Global semantic diagnostics
        "max_consecutive_sem_pass": consec_metrics["max_consecutive_sem_pass"],
        "max_consecutive_sem_fail": consec_metrics["max_consecutive_sem_fail"],
        "ever_global_semfail_ge_k": consec_metrics["ever_global_semfail_ge_k"],
        "global_semfail_ge_k_fraction": consec_metrics["global_semfail_ge_k_fraction"],

        # Renewal metrics
        "renewal_check_epochs_count": renewal_metrics["renewal_check_epochs_count"],
        "renewals_succeeded": renewal_metrics["renewals_succeeded"],
        "renewal_success_rate_ppm": renewal_metrics["renewal_success_rate_ppm"],
        "expiration_reason_counts": renewal_metrics["expiration_reason_counts"],

        # Stop reason
        "stop_reason": run_result.stop_reason.name,
    }


# =============================================================================
# Run Execution
# =============================================================================

def run_timing_sweep(
    config: RunConfig,
    verbose: bool = False
) -> Dict[Tuple[int, int], List[Dict[str, Any]]]:
    """
    Run Model C (FIXED_RENEWAL_TIMING) across all (period, offset) settings.

    Returns:
        Dict mapping (period, offset) -> list of per-seed results
    """
    results_by_setting = {}

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        max_successive_renewals=config.max_successive_renewals,
        amnesty_interval=config.amnesty_interval,
        amnesty_decay=config.amnesty_decay,
        cta_enabled=config.cta_enabled,
    )

    for period, offset in config.timing_grid:
        print(f"\n{'='*70}")
        print(f"Setting: period={period}, offset={offset}")
        print(f"{'='*70}")
        print(f"  Config hash:  {config.config_hash()}")
        print(f"  Policy hash:  {config.policy_hash(period, offset)}")
        print()

        rsa_policy_config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.FIXED_RENEWAL_TIMING,
            timing_period_epochs=period,
            timing_offset_epochs=offset,
            epoch_size=als_config.renewal_check_interval,
        )

        setting_results = []

        for seed in config.seeds:
            print(f"  seed={seed}...", end=" ", flush=True)

            harness = ALSHarnessV080(
                seed=seed,
                config=als_config,
                verbose=verbose,
                rsa_config=None,
                rsa_policy_config=rsa_policy_config,
            )
            run_result = harness.run()

            metrics = compute_full_metrics(harness, run_result, config, seed, period, offset)
            setting_results.append(metrics)

            aa_pct = metrics["authority_availability_ppm"] / 10_000
            print(f"AA={aa_pct:.2f}%, class={metrics['failure_class']}, "
                  f"sem_pass={metrics['sem_pass_rate_ppm']/10_000:.1f}%")

        results_by_setting[(period, offset)] = setting_results

    return results_by_setting


# =============================================================================
# Aggregate Summaries
# =============================================================================

def compute_per_setting_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate summary for a single (period, offset) setting."""
    n = len(results)
    if n == 0:
        return {}

    # AA and AAA
    aa_values = [r["authority_availability_ppm"] for r in results]
    aaa_values = [r["asymptotic_authority_availability_ppm"] for r in results]

    aa_mean = statistics.mean(aa_values)
    aa_std = statistics.stdev(aa_values) if n > 1 else 0.0
    aaa_mean = statistics.mean(aaa_values)
    aaa_std = statistics.stdev(aaa_values) if n > 1 else 0.0

    # Class counts
    class_counts = Counter(r["failure_class"] for r in results)

    # Failure class analysis
    failure_classes = [
        "STRUCTURAL_THRASHING",
        "ASYMPTOTIC_DOS",
        "TERMINAL_COLLAPSE",
        "IRREVERSIBLE_RECOVERY_SUPPRESSION",
    ]
    failure_count = sum(class_counts.get(fc, 0) for fc in failure_classes)

    # RTD aggregate
    rtd_aggregate = {label: 0 for label in RTD_BUCKET_LABELS}
    for r in results:
        for label, count in r["recovery_time_histogram"].items():
            rtd_aggregate[label] += count

    # Lapse metrics
    lapse_counts = [r["lapse_count"] for r in results]
    max_lapse_values = [r["max_single_lapse_epochs"] for r in results]

    lapse_count_mean = statistics.mean(lapse_counts)
    lapse_count_total = sum(lapse_counts)
    max_lapse_mean = statistics.mean(max_lapse_values)
    max_lapse_max = max(max_lapse_values)

    # Global semantic metrics
    semfail_fractions = [r["global_semfail_ge_k_fraction"] for r in results]
    semfail_mean = statistics.mean(semfail_fractions)

    sem_pass_rates = [r["sem_pass_rate_ppm"] for r in results]
    sem_pass_rate_mean = statistics.mean(sem_pass_rates)

    # Renewal metrics
    renewal_rates = [r["renewal_success_rate_ppm"] for r in results]
    renewal_mean = statistics.mean(renewal_rates)
    renewal_std = statistics.stdev(renewal_rates) if n > 1 else 0.0

    # Expiration reason aggregation
    expiration_reasons_aggregate = Counter()
    for r in results:
        for reason, count in r["expiration_reason_counts"].items():
            expiration_reasons_aggregate[reason] += count

    # Max consecutive sem_fail (diagnostic for eligibility analysis)
    max_consec_fails = [r["max_consecutive_sem_fail"] for r in results]
    max_consec_fail_mean = statistics.mean(max_consec_fails)
    max_consec_fail_max = max(max_consec_fails)

    return {
        "n_seeds": n,
        "period": results[0]["period"],
        "offset": results[0]["offset"],
        "aa_mean_ppm": int(aa_mean),
        "aa_std_ppm": int(aa_std),
        "aa_min_ppm": min(aa_values),
        "aa_max_ppm": max(aa_values),
        "aaa_mean_ppm": int(aaa_mean),
        "aaa_std_ppm": int(aaa_std),
        "aaa_min_ppm": min(aaa_values),
        "aaa_max_ppm": max(aaa_values),
        "failure_class_counts": dict(class_counts),
        "failure_count": failure_count,
        "rtd_aggregate": rtd_aggregate,
        "lapse_count_mean": lapse_count_mean,
        "lapse_count_total": lapse_count_total,
        "max_single_lapse_mean": max_lapse_mean,
        "max_single_lapse_max": max_lapse_max,
        "global_semfail_ge_k_fraction_mean": semfail_mean,
        "sem_pass_rate_mean_ppm": int(sem_pass_rate_mean),
        "renewal_success_rate_mean_ppm": int(renewal_mean),
        "renewal_success_rate_std_ppm": int(renewal_std),
        "expiration_reason_counts": dict(expiration_reasons_aggregate),
        "max_consecutive_sem_fail_mean": max_consec_fail_mean,
        "max_consecutive_sem_fail_max": max_consec_fail_max,
    }


# =============================================================================
# Output Formatting
# =============================================================================

def print_run_header(config: RunConfig):
    """Print run header with configuration info."""
    print("=" * 70)
    print("RSA v1.0 Run 3: Fixed Timing Misuse Sweep (Model C)")
    print("=" * 70)
    print()
    print("Run Header:")
    print(f"  AKI config hash:     {config.config_hash()}")
    print(f"  Horizon cycles:      {config.max_cycles:,}")
    print(f"  Horizon epochs:      {config.horizon_epochs:,}")
    print(f"  Tail window:         {config.tail_window:,}")
    print(f"  Renewal interval:    {config.renewal_check_interval}")
    print(f"  Eligibility K:       {config.eligibility_threshold_k}")
    print(f"  Seeds per setting:   {len(config.seeds)}")
    print(f"  Seeds:               {config.seeds}")
    print(f"  Timing grid:         {config.timing_grid}")
    print(f"  Total runs:          {len(config.timing_grid) * len(config.seeds)}")
    print()
    print("Adversary Model: FIXED_RENEWAL_TIMING (Model C)")
    print("  - Schedule: SATISFY commitments iff (epoch % period) == offset")
    print("  - Otherwise: VIOLATE commitments")
    print("  - Applied to ALL incumbents (control and attack successors)")
    print("  - Fixed, deterministic, non-adaptive, outcome-blind")
    print()


def print_per_seed_table(results: List[Dict[str, Any]], period: int, offset: int):
    """Print per-seed results table for a setting."""
    print(f"\nPer-Seed Results (period={period}, offset={offset}):")
    print("-" * 120)
    header = f"{'Seed':>6} {'AA%':>7} {'AAA%':>7} {'Class':>20} {'Lapses':>6} {'MaxLapse':>8} " \
             f"{'RenewRate%':>11} {'SemPass%':>9} {'MaxFails':>8}"
    print(header)
    print("-" * 120)

    for r in results:
        aa_pct = r["authority_availability_ppm"] / 10_000
        aaa_pct = r["asymptotic_authority_availability_ppm"] / 10_000
        renew_pct = r["renewal_success_rate_ppm"] / 10_000
        sem_pass_pct = r["sem_pass_rate_ppm"] / 10_000

        print(f"{r['seed']:>6} {aa_pct:>7.2f} {aaa_pct:>7.2f} {r['failure_class']:>20} "
              f"{r['lapse_count']:>6} {r['max_single_lapse_epochs']:>8} "
              f"{renew_pct:>11.2f} {sem_pass_pct:>9.1f} {r['max_consecutive_sem_fail']:>8}")


def print_per_setting_summary(summary: Dict[str, Any]):
    """Print aggregate summary for a single setting."""
    print("\nPer-Setting Summary:")
    print("-" * 50)
    aa_mean_pct = summary["aa_mean_ppm"] / 10_000
    aa_std_pct = summary["aa_std_ppm"] / 10_000
    aaa_mean_pct = summary["aaa_mean_ppm"] / 10_000
    aaa_std_pct = summary["aaa_std_ppm"] / 10_000

    print(f"  AA:  mean={aa_mean_pct:.2f}% (std={aa_std_pct:.2f}%), "
          f"min={summary['aa_min_ppm']/10_000:.2f}%, max={summary['aa_max_ppm']/10_000:.2f}%")
    print(f"  AAA: mean={aaa_mean_pct:.2f}% (std={aaa_std_pct:.2f}%), "
          f"min={summary['aaa_min_ppm']/10_000:.2f}%, max={summary['aaa_max_ppm']/10_000:.2f}%")
    print(f"  Failure classes: {summary['failure_class_counts']}")
    print(f"  Failure count (hard failures): {summary['failure_count']}")
    print(f"  Lapse count: mean={summary['lapse_count_mean']:.1f}, total={summary['lapse_count_total']}")
    print(f"  Max single lapse: mean={summary['max_single_lapse_mean']:.1f}, max={summary['max_single_lapse_max']}")

    renew_mean_pct = summary["renewal_success_rate_mean_ppm"] / 10_000
    renew_std_pct = summary["renewal_success_rate_std_ppm"] / 10_000
    sem_pass_mean_pct = summary["sem_pass_rate_mean_ppm"] / 10_000

    print(f"  Renewal success: mean={renew_mean_pct:.2f}% (std={renew_std_pct:.2f}%)")
    print(f"  Sem_pass rate: mean={sem_pass_mean_pct:.1f}%")
    print(f"  Max consecutive sem_fail: mean={summary['max_consecutive_sem_fail_mean']:.1f}, "
          f"max={summary['max_consecutive_sem_fail_max']}")
    print(f"  Global sem_fail ≥K fraction: mean={summary['global_semfail_ge_k_fraction_mean']:.4f}")
    print(f"  Expiration reasons: {summary['expiration_reason_counts']}")

    # RTD summary
    rtd = summary["rtd_aggregate"]
    non_zero = {k: v for k, v in rtd.items() if v > 0}
    if non_zero:
        print(f"  RTD (non-zero buckets): {non_zero}")
    else:
        print(f"  RTD: No lapses recorded")


def print_cross_setting_summary(summaries: List[Dict[str, Any]]):
    """Print cross-setting summary table."""
    print("\n" + "="*70)
    print("Cross-Setting Summary Table")
    print("="*70)
    print()
    print(f"{'Period':>6} {'Offset':>6} {'AA%':>7} {'AAA%':>7} {'RenewRate%':>11} "
          f"{'SemPass%':>9} {'MaxFail':>7} {'Failures':>8} {'Classes':<30}")
    print("-" * 120)

    for s in summaries:
        aa_pct = s["aa_mean_ppm"] / 10_000
        aaa_pct = s["aaa_mean_ppm"] / 10_000
        renew_pct = s["renewal_success_rate_mean_ppm"] / 10_000
        sem_pass_pct = s["sem_pass_rate_mean_ppm"] / 10_000
        max_fail = int(s["max_consecutive_sem_fail_max"])

        # Compact class representation
        classes_str = ", ".join(f"{k}:{v}" for k, v in s["failure_class_counts"].items())
        classes_str = classes_str[:28] + ".." if len(classes_str) > 30 else classes_str

        print(f"{s['period']:>6} {s['offset']:>6} {aa_pct:>7.2f} {aaa_pct:>7.2f} {renew_pct:>11.2f} "
              f"{sem_pass_pct:>9.1f} {max_fail:>7} {s['failure_count']:>8} {classes_str:<30}")

    print()


def print_constitutional_failure_check(summaries: List[Dict[str, Any]]):
    """Print constitutional failure check."""
    print("=" * 70)
    print("Constitutional Failure Check")
    print("=" * 70)
    print()

    total_failures = sum(s["failure_count"] for s in summaries)
    total_runs = sum(s["n_seeds"] for s in summaries)

    if total_failures > 0:
        print(f"⚠ {total_failures} constitutional failure(s) detected across {total_runs} runs")
        print()
        print("Failures by setting:")
        for s in summaries:
            if s["failure_count"] > 0:
                print(f"  period={s['period']}, offset={s['offset']}: "
                      f"{s['failure_count']} failures, classes={s['failure_class_counts']}")
    else:
        print(f"✓ No constitutional failures detected across {total_runs} runs.")
        print("  All runs classified as STABLE_AUTHORITY or BOUNDED_DEGRADATION.")


# =============================================================================
# CSV Export
# =============================================================================

def write_csv_summary(summaries: List[Dict[str, Any]], output_dir: Path, timestamp: str):
    """Write cross-setting summary to CSV."""
    csv_file = output_dir / f"rsa_v100_run3_timing_summary_{timestamp}.csv"

    with open(csv_file, "w", newline="") as f:
        fieldnames = [
            "period", "offset", "n_seeds",
            "aa_mean_ppm", "aa_std_ppm", "aa_min_ppm", "aa_max_ppm",
            "aaa_mean_ppm", "aaa_std_ppm", "aaa_min_ppm", "aaa_max_ppm",
            "renewal_success_rate_mean_ppm", "renewal_success_rate_std_ppm",
            "sem_pass_rate_mean_ppm",
            "max_consecutive_sem_fail_mean", "max_consecutive_sem_fail_max",
            "global_semfail_ge_k_fraction_mean",
            "lapse_count_mean", "lapse_count_total",
            "max_single_lapse_mean", "max_single_lapse_max",
            "failure_count", "failure_class_counts",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for s in summaries:
            row = {k: s[k] for k in fieldnames if k != "failure_class_counts"}
            row["failure_class_counts"] = str(s["failure_class_counts"])
            writer.writerow(row)

    print(f"\nCSV summary saved to: {csv_file}")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run timing sweep experiment and save results."""
    config = RunConfig()

    # Print header
    print_run_header(config)

    # Run Model C across all (period, offset) settings
    print("Running Model C (FIXED_RENEWAL_TIMING) across preregistered grid...")
    results_by_setting = run_timing_sweep(config)

    # Compute per-setting summaries
    summaries = []
    for (period, offset), results in results_by_setting.items():
        print_per_seed_table(results, period, offset)
        summary = compute_per_setting_summary(results)
        print_per_setting_summary(summary)
        summaries.append(summary)

    # Sort summaries by (period, offset) for consistent ordering
    summaries.sort(key=lambda s: (s["period"], s["offset"]))

    # Print cross-setting summary
    print_cross_setting_summary(summaries)

    # Check for constitutional failures
    print_constitutional_failure_check(summaries)

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Write CSV summary
    write_csv_summary(summaries, output_dir, timestamp)

    # Write full JSON output
    output_file = output_dir / f"rsa_v100_run3_timing_{timestamp}.json"

    # Flatten results_by_setting for JSON serialization
    all_results = []
    for results in results_by_setting.values():
        all_results.extend(results)

    output_data = {
        "run_type": "RSA v1.0 Run 3: Fixed Timing Misuse Sweep (Model C)",
        "timestamp": timestamp,
        "config": {
            "max_cycles": config.max_cycles,
            "renewal_check_interval": config.renewal_check_interval,
            "eligibility_threshold_k": config.eligibility_threshold_k,
            "max_successive_renewals": config.max_successive_renewals,
            "amnesty_interval": config.amnesty_interval,
            "amnesty_decay": config.amnesty_decay,
            "cta_enabled": config.cta_enabled,
            "seeds": config.seeds,
            "timing_grid": config.timing_grid,
            "horizon_epochs": config.horizon_epochs,
            "tail_window": config.tail_window,
            "config_hash": config.config_hash(),
        },
        "adversary_model": {
            "name": "FIXED_RENEWAL_TIMING",
            "description": "Satisfies commitments only at fixed epoch offsets",
            "schedule": "(epoch % period) == offset",
            "scope": "Applied to all incumbents (control and attack successors)",
            "behavior": "Fixed, deterministic, non-adaptive, outcome-blind",
        },
        "results": all_results,
        "summaries": summaries,
        "total_runs": len(all_results),
        "total_failures": sum(s["failure_count"] for s in summaries),
        "any_constitutional_failures": any(s["failure_count"] > 0 for s in summaries),
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nFull results saved to: {output_file}")
    print()
    print("Run 3 complete.")

    total_failures = sum(s["failure_count"] for s in summaries)
    if total_failures > 0:
        print(f"⚠ {total_failures} constitutional failure(s) detected. Review before proceeding to Run 4.")
    else:
        print("✓ No constitutional failures. Ready to proceed to Run 4.")


if __name__ == "__main__":
    main()
