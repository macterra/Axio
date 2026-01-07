"""
RSA v1.0 Run 0: Baseline (No Adversary)

Purpose: Establish clean reference baseline for all RSA v1.0 experiments under the
exact frozen AKI configuration, horizon, and seed set used in Runs 1-5.

Per rsa_instructions_v1.0_runner0.md:
- Condition A: RSA policy disabled (true clean baseline)
- Condition B: RSA policy enabled with NONE (enabled-path equivalence)
- Both conditions must produce identical per-seed metrics
- Full metrics suite including AAA, RTD, failure classification, and v1.0 diagnostics
"""

import json
import sys
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
    """Configuration for RSA v1.0 runs (frozen per spec)."""

    # Frozen parameters
    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    max_successive_renewals: int = 3
    amnesty_interval: int = 10
    amnesty_decay: int = 1
    cta_enabled: bool = True

    # Fixed seed battery (v1.0 canonical set)
    # Performance fix applied: epoch-indexed action trace O(1) vs O(n) scan
    seeds: List[int] = field(default_factory=lambda: [
        42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768
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


# =============================================================================
# Metrics Computation
# =============================================================================

def build_authority_timeline(harness: ALSHarnessV080, horizon_epochs: int) -> List[bool]:
    """
    Build per-epoch authority timeline from semantic epoch records.

    Authority is present (True) for epochs where semantic evaluation occurred.
    Uses the same algorithm as v0.2 baseline for consistency.

    Note: This differs from using lapse_events_v080 because semantic epoch records
    are only created when authority is actively exercised, providing an accurate
    measure of governance availability.
    """
    # Start with all epochs as False (no authority)
    authority_by_epoch = [False] * horizon_epochs

    # Mark epochs where semantic evaluation occurred (authority was active)
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
    """
    Compute consecutive pass/fail metrics from SEM_PASS sequence.
    """
    if not sem_pass_sequence:
        return {
            "max_consecutive_sem_pass": 0,
            "max_consecutive_sem_fail": 0,
            "ever_ineligible": False,
            "ineligibility_fraction": 0.0,
        }

    max_pass = 0
    max_fail = 0
    current_pass = 0
    current_fail = 0
    ineligible_epochs = 0
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
                ineligible_epochs += 1

    return {
        "max_consecutive_sem_pass": max_pass,
        "max_consecutive_sem_fail": max_fail,
        "ever_ineligible": max_fail >= eligibility_threshold_k,
        "ineligibility_fraction": ineligible_epochs / max(total_epochs, 1),
    }


def compute_renewal_metrics(harness: ALSHarnessV080, run_result) -> Dict[str, Any]:
    """
    Compute renewal-related metrics from harness state.
    """
    total_renewal_checks = run_result.total_renewals + run_result.total_expirations
    renewals_succeeded = run_result.total_renewals

    if total_renewal_checks > 0:
        renewal_success_rate_ppm = int((renewals_succeeded / total_renewal_checks) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

    return {
        "renewal_check_epochs_count": total_renewal_checks,
        "renewals_succeeded": renewals_succeeded,
        "renewal_success_rate_ppm": renewal_success_rate_ppm,
    }


def compute_full_metrics(
    harness: ALSHarnessV080,
    run_result,
    config: RunConfig,
    condition: str,
    seed: int,
) -> Dict[str, Any]:
    """
    Compute all required metrics for a single run.
    """
    horizon_epochs = config.horizon_epochs

    # Build authority timeline
    authority_by_epoch = build_authority_timeline(harness, horizon_epochs)

    # Compute RSA metrics (AA, AAA, RTD, failure_class)
    rsa_metrics = compute_rsa_metrics(authority_by_epoch)

    # Extract SEM_PASS sequence
    sem_pass_seq = [r.sem_pass for r in harness._semantic_epoch_records]

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
        "run_id": f"rsa_v100_run0_{condition}_seed{seed}",
        "seed": seed,
        "condition": condition,

        # RSA state
        "rsa_enabled": condition == "B",
        "rsa_model": "NONE" if condition == "B" else None,

        # Basic run info
        "total_cycles": run_result.total_cycles,
        "epochs_evaluated": len(sem_pass_seq),

        # Governance outcomes (§3.1)
        "authority_availability_ppm": rsa_metrics.authority_availability_ppm,
        "asymptotic_authority_availability_ppm": rsa_metrics.asymptotic_authority_availability_ppm,
        "failure_class": rsa_metrics.failure_class.value,
        "recovery_time_histogram": rsa_metrics.recovery_time_histogram,

        # Lapse metrics
        "lapse_count": lapse_count,
        "total_lapse_epochs": total_lapse_epochs,
        "max_single_lapse_epochs": max_single_lapse_epochs,
        "epochs_in_lapse": epochs_in_lapse,

        # v1.0 derived diagnostics (§3.2)
        "max_consecutive_sem_pass": consec_metrics["max_consecutive_sem_pass"],
        "max_consecutive_sem_fail": consec_metrics["max_consecutive_sem_fail"],
        "ever_ineligible": consec_metrics["ever_ineligible"],
        "ineligibility_fraction": consec_metrics["ineligibility_fraction"],

        # Renewal metrics
        "renewal_check_epochs_count": renewal_metrics["renewal_check_epochs_count"],
        "renewals_succeeded": renewal_metrics["renewals_succeeded"],
        "renewal_success_rate_ppm": renewal_metrics["renewal_success_rate_ppm"],

        # Stop reason
        "stop_reason": run_result.stop_reason.name,
    }


# =============================================================================
# Run Execution
# =============================================================================

def run_condition_a(config: RunConfig, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Run Condition A: RSA policy disabled (true clean baseline).
    """
    results = []

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        max_successive_renewals=config.max_successive_renewals,
        amnesty_interval=config.amnesty_interval,
        amnesty_decay=config.amnesty_decay,
        cta_enabled=config.cta_enabled,
    )

    for seed in config.seeds:
        print(f"  Condition A seed={seed}...", end=" ", flush=True)

        harness = ALSHarnessV080(
            seed=seed,
            config=als_config,
            verbose=verbose,
            rsa_config=None,
            rsa_policy_config=None,
        )
        run_result = harness.run()

        metrics = compute_full_metrics(harness, run_result, config, "A", seed)
        results.append(metrics)

        aa_pct = metrics["authority_availability_ppm"] / 10_000
        print(f"AA={aa_pct:.2f}%, class={metrics['failure_class']}")

    return results


def run_condition_b(config: RunConfig, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Run Condition B: RSA policy enabled with NONE (enabled-path equivalence).
    """
    results = []

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        max_successive_renewals=config.max_successive_renewals,
        amnesty_interval=config.amnesty_interval,
        amnesty_decay=config.amnesty_decay,
        cta_enabled=config.cta_enabled,
    )

    rsa_policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.NONE,
        epoch_size=als_config.renewal_check_interval,
    )

    for seed in config.seeds:
        print(f"  Condition B seed={seed}...", end=" ", flush=True)

        harness = ALSHarnessV080(
            seed=seed,
            config=als_config,
            verbose=verbose,
            rsa_config=None,
            rsa_policy_config=rsa_policy_config,
        )
        run_result = harness.run()

        metrics = compute_full_metrics(harness, run_result, config, "B", seed)
        results.append(metrics)

        aa_pct = metrics["authority_availability_ppm"] / 10_000
        print(f"AA={aa_pct:.2f}%, class={metrics['failure_class']}")

    return results


# =============================================================================
# Equivalence Check
# =============================================================================

EQUIVALENCE_KEYS = [
    "authority_availability_ppm",
    "asymptotic_authority_availability_ppm",
    "failure_class",
    "lapse_count",
    "total_lapse_epochs",
    "max_single_lapse_epochs",
    "max_consecutive_sem_pass",
    "max_consecutive_sem_fail",
    "ever_ineligible",
    "renewal_success_rate_ppm",
]


def check_equivalence(
    results_a: List[Dict[str, Any]],
    results_b: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """
    Check that Condition A and B produce identical per-seed metrics.

    Returns (is_equivalent, list_of_differences)
    """
    differences = []

    if len(results_a) != len(results_b):
        return False, [f"Result count mismatch: A={len(results_a)}, B={len(results_b)}"]

    for ra, rb in zip(results_a, results_b):
        seed = ra["seed"]
        for key in EQUIVALENCE_KEYS:
            val_a = ra.get(key)
            val_b = rb.get(key)
            if val_a != val_b:
                differences.append(f"seed={seed} {key}: A={val_a}, B={val_b}")

    return len(differences) == 0, differences


# =============================================================================
# Aggregate Summaries
# =============================================================================

def compute_aggregate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate summary across seeds.
    """
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

    # RTD aggregate
    rtd_aggregate = {label: 0 for label in RTD_BUCKET_LABELS}
    for r in results:
        for label, count in r["recovery_time_histogram"].items():
            rtd_aggregate[label] += count

    # Max single lapse distribution
    max_lapse_values = [r["max_single_lapse_epochs"] for r in results]
    max_lapse_mean = statistics.mean(max_lapse_values)
    max_lapse_max = max(max_lapse_values)

    # Ineligibility and renewal metrics
    inelig_fractions = [r["ineligibility_fraction"] for r in results]
    renewal_rates = [r["renewal_success_rate_ppm"] for r in results]

    inelig_mean = statistics.mean(inelig_fractions)
    inelig_std = statistics.stdev(inelig_fractions) if n > 1 else 0.0
    renewal_mean = statistics.mean(renewal_rates)
    renewal_std = statistics.stdev(renewal_rates) if n > 1 else 0.0

    return {
        "n_seeds": n,
        "aa_mean_ppm": int(aa_mean),
        "aa_std_ppm": int(aa_std),
        "aa_min_ppm": min(aa_values),
        "aa_max_ppm": max(aa_values),
        "aaa_mean_ppm": int(aaa_mean),
        "aaa_std_ppm": int(aaa_std),
        "aaa_min_ppm": min(aaa_values),
        "aaa_max_ppm": max(aaa_values),
        "failure_class_counts": dict(class_counts),
        "rtd_aggregate": rtd_aggregate,
        "max_single_lapse_mean": max_lapse_mean,
        "max_single_lapse_max": max_lapse_max,
        "ineligibility_fraction_mean": inelig_mean,
        "ineligibility_fraction_std": inelig_std,
        "renewal_success_rate_mean_ppm": int(renewal_mean),
        "renewal_success_rate_std_ppm": int(renewal_std),
    }


# =============================================================================
# Output Formatting
# =============================================================================

def print_run_header(config: RunConfig):
    """Print run header with configuration info."""
    print("=" * 70)
    print("RSA v1.0 Run 0: Baseline Reference (No Adversary)")
    print("=" * 70)
    print()
    print("Run Header:")
    print(f"  AKI config hash:     {config.config_hash()}")
    print(f"  Horizon cycles:      {config.max_cycles:,}")
    print(f"  Horizon epochs:      {config.horizon_epochs:,}")
    print(f"  Tail window:         {config.tail_window:,}")
    print(f"  Renewal interval:    {config.renewal_check_interval}")
    print(f"  Eligibility K:       {config.eligibility_threshold_k}")
    print(f"  Seeds:               {config.seeds}")
    print()


def print_per_seed_table(results: List[Dict[str, Any]], condition: str):
    """Print per-seed results table."""
    print(f"\nPer-Seed Results (Condition {condition}):")
    print("-" * 100)
    header = f"{'Seed':>6} {'AA%':>7} {'AAA%':>7} {'Class':>22} {'Lapses':>6} {'MaxLapse':>8} {'RenewRate%':>10} {'EverInelig':>10}"
    print(header)
    print("-" * 100)

    for r in results:
        aa_pct = r["authority_availability_ppm"] / 10_000
        aaa_pct = r["asymptotic_authority_availability_ppm"] / 10_000
        renew_pct = r["renewal_success_rate_ppm"] / 10_000
        ever_inelig = "Yes" if r["ever_ineligible"] else "No"

        print(f"{r['seed']:>6} {aa_pct:>7.2f} {aaa_pct:>7.2f} {r['failure_class']:>22} "
              f"{r['lapse_count']:>6} {r['max_single_lapse_epochs']:>8} {renew_pct:>10.2f} {ever_inelig:>10}")


def print_aggregate_summary(summary: Dict[str, Any], condition: str):
    """Print aggregate summary."""
    print(f"\nAggregate Summary (Condition {condition}):")
    print("-" * 50)
    aa_mean_pct = summary["aa_mean_ppm"] / 10_000
    aa_std_pct = summary["aa_std_ppm"] / 10_000
    aaa_mean_pct = summary["aaa_mean_ppm"] / 10_000
    aaa_std_pct = summary["aaa_std_ppm"] / 10_000

    print(f"  AA:  mean={aa_mean_pct:.2f}% (std={aa_std_pct:.2f}%)")
    print(f"  AAA: mean={aaa_mean_pct:.2f}% (std={aaa_std_pct:.2f}%)")
    print(f"  Failure classes: {summary['failure_class_counts']}")
    print(f"  Max single lapse: mean={summary['max_single_lapse_mean']:.1f}, max={summary['max_single_lapse_max']}")

    renew_mean_pct = summary["renewal_success_rate_mean_ppm"] / 10_000
    renew_std_pct = summary["renewal_success_rate_std_ppm"] / 10_000
    print(f"  Renewal success: mean={renew_mean_pct:.2f}% (std={renew_std_pct:.2f}%)")
    print(f"  Ineligibility fraction: mean={summary['ineligibility_fraction_mean']:.4f} (std={summary['ineligibility_fraction_std']:.4f})")

    # RTD summary
    rtd = summary["rtd_aggregate"]
    non_zero = {k: v for k, v in rtd.items() if v > 0}
    if non_zero:
        print(f"  RTD (non-zero buckets): {non_zero}")
    else:
        print(f"  RTD: No lapses recorded")


def print_rsa_integrity_block(results_b: List[Dict[str, Any]]):
    """Print RSA policy integrity block for Condition B."""
    print("\nRSA Policy Integrity Block (Condition B):")
    print("-" * 50)
    print(f"  rsa_enabled: True")
    print(f"  rsa_model: NONE")
    print(f"  All {len(results_b)} runs completed with policy wrapper present")
    print(f"  Policy NONE does not modify agent actions")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run baseline experiments and save results."""
    config = RunConfig()

    # Print header
    print_run_header(config)

    # Condition A: RSA disabled
    print("Running Condition A (RSA policy disabled)...")
    results_a = run_condition_a(config)
    summary_a = compute_aggregate_summary(results_a)

    print()

    # Condition B: RSA enabled with NONE
    print("Running Condition B (RSA policy enabled, model=NONE)...")
    results_b = run_condition_b(config)
    summary_b = compute_aggregate_summary(results_b)

    # Print per-seed tables
    print_per_seed_table(results_a, "A")
    print_per_seed_table(results_b, "B")

    # Print aggregate summaries
    print_aggregate_summary(summary_a, "A")
    print_aggregate_summary(summary_b, "B")

    # RSA integrity block
    print_rsa_integrity_block(results_b)

    # Equivalence check
    print("\n" + "=" * 70)
    print("Equivalence Check")
    print("=" * 70)

    is_equivalent, differences = check_equivalence(results_a, results_b)

    if is_equivalent:
        print()
        print("✓ Condition A (policy disabled) and Condition B (policy enabled, NONE)")
        print("  produced identical per-seed metrics.")
        print()
    else:
        print()
        print("✗ EQUIVALENCE FAILED - Conditions A and B differ:")
        for diff in differences:
            print(f"    {diff}")
        print()
        print("STOPPING: Do not proceed to Runs 1-5 until this is resolved.")
        print()
        sys.exit(1)

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"rsa_v100_run0_baseline_{timestamp}.json"

    output_data = {
        "run_type": "RSA v1.0 Run 0: Baseline Reference",
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
            "horizon_epochs": config.horizon_epochs,
            "tail_window": config.tail_window,
            "config_hash": config.config_hash(),
        },
        "condition_a": {
            "description": "RSA policy disabled (true clean baseline)",
            "results": results_a,
            "summary": summary_a,
        },
        "condition_b": {
            "description": "RSA policy enabled with NONE (enabled-path equivalence)",
            "results": results_b,
            "summary": summary_b,
        },
        "equivalence_check": {
            "passed": is_equivalent,
            "differences": differences,
        },
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()
    print("Run 0 complete. Baseline established for v1.0 experimental runs.")


if __name__ == "__main__":
    main()
