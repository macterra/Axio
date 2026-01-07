"""
RSA v1.0 Run 2: Minimal Compliance / Hollow Authority (Model B)

Purpose: Evaluate whether perfect formal compliance with minimal effort—without
competence, optimization, or adaptation—can induce constitutional failure or
hollow out governance under the frozen RSA v1.0 assumptions.

Per rsa_instructions_v1.0_runner2.md:
- Model B (MINIMAL_ELIGIBILITY_ONLY) applied to all incumbents
- No sweep axis (single policy class)
- 1 policy × 10 seeds = 10 runs
- Full horizon execution (no early termination)

Expected outcome: All seeds should match Run 0 seed 2048 behavior (attractor B):
- AA ≈ 99.98% (near 1.0, not necessarily exactly 1.0)
- AAA ≈ 100%
- Failure class: STABLE_AUTHORITY
- Lapses: 0 or near-0

RSA v1.0 policy scope: When enabled, the RSA policy wrapper applies to the
incumbent successor's propose_action() for **all successor types** (control and
attack), across all successions, throughout the full run.
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

    # Frozen parameters (identical to Run 0 and Run 1)
    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    max_successive_renewals: int = 3
    amnesty_interval: int = 10
    amnesty_decay: int = 1
    cta_enabled: bool = True

    # Fixed seed battery (v1.0 canonical set)
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

    def policy_hash(self) -> str:
        """Compute hash of policy config."""
        policy_str = f"MINIMAL_ELIGIBILITY_ONLY:{self.renewal_check_interval}"
        return hashlib.md5(policy_str.encode()).hexdigest()[:8]


# =============================================================================
# Metrics Computation (reused from Run 0/Run 1)
# =============================================================================

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
    """
    Compute consecutive pass/fail metrics from SEM_PASS sequence.

    Note: These are GLOBAL metrics (streak does not reset on succession).
    """
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
    """
    Compute renewal-related metrics from harness state.
    """
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
        "run_id": f"rsa_v100_run2_minimal_seed{seed}",
        "seed": seed,

        # RSA state
        "rsa_enabled": True,
        "rsa_model": "MINIMAL_ELIGIBILITY_ONLY",

        # Basic run info
        "total_cycles": run_result.total_cycles,
        "epochs_evaluated": len(sem_pass_seq),

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

def run_minimal_compliance(
    config: RunConfig,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Run Model B (MINIMAL_ELIGIBILITY_ONLY) across all seeds.
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
        policy_model=RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY,
        epoch_size=als_config.renewal_check_interval,
    )

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

        metrics = compute_full_metrics(harness, run_result, config, seed)
        results.append(metrics)

        aa_pct = metrics["authority_availability_ppm"] / 10_000
        print(f"AA={aa_pct:.2f}%, class={metrics['failure_class']}")

    return results


# =============================================================================
# Aggregate Summary
# =============================================================================

def compute_aggregate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate summary across all seeds.
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

    # Renewal metrics
    renewal_rates = [r["renewal_success_rate_ppm"] for r in results]
    renewal_mean = statistics.mean(renewal_rates)
    renewal_std = statistics.stdev(renewal_rates) if n > 1 else 0.0

    # Expiration reason aggregation
    expiration_reasons_aggregate = Counter()
    for r in results:
        for reason, count in r["expiration_reason_counts"].items():
            expiration_reasons_aggregate[reason] += count

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
        "failure_count": failure_count,
        "rtd_aggregate": rtd_aggregate,
        "lapse_count_mean": lapse_count_mean,
        "lapse_count_total": lapse_count_total,
        "max_single_lapse_mean": max_lapse_mean,
        "max_single_lapse_max": max_lapse_max,
        "global_semfail_ge_k_fraction_mean": semfail_mean,
        "renewal_success_rate_mean_ppm": int(renewal_mean),
        "renewal_success_rate_std_ppm": int(renewal_std),
        "expiration_reason_counts": dict(expiration_reasons_aggregate),
    }


# =============================================================================
# Output Formatting
# =============================================================================

def print_run_header(config: RunConfig):
    """Print run header with configuration info."""
    print("=" * 70)
    print("RSA v1.0 Run 2: Minimal Compliance / Hollow Authority (Model B)")
    print("=" * 70)
    print()
    print("Run Header:")
    print(f"  AKI config hash:     {config.config_hash()}")
    print(f"  Policy config hash:  {config.policy_hash()}")
    print(f"  Horizon cycles:      {config.max_cycles:,}")
    print(f"  Horizon epochs:      {config.horizon_epochs:,}")
    print(f"  Tail window:         {config.tail_window:,}")
    print(f"  Renewal interval:    {config.renewal_check_interval}")
    print(f"  Eligibility K:       {config.eligibility_threshold_k}")
    print(f"  Seeds:               {config.seeds}")
    print(f"  Total runs:          {len(config.seeds)}")
    print()
    print("Adversary Model: MINIMAL_ELIGIBILITY_ONLY (Model B)")
    print("  - Emits minimal action trace to satisfy all commitments (C0, C1, C2)")
    print("  - Applied to ALL incumbents (control and attack successors)")
    print("  - Fixed, deterministic, non-adaptive")
    print("  - Under ALS-A strict AND: behaviorally equivalent to full compliance")
    print()


def print_per_seed_table(results: List[Dict[str, Any]]):
    """Print per-seed results table."""
    print("\nPer-Seed Results:")
    print("-" * 110)
    header = f"{'Seed':>6} {'AA%':>7} {'AAA%':>7} {'Class':>20} {'Lapses':>6} {'MaxLapse':>8} {'RenewRate%':>10} {'SemFail≥K':>10}"
    print(header)
    print("-" * 110)

    for r in results:
        aa_pct = r["authority_availability_ppm"] / 10_000
        aaa_pct = r["asymptotic_authority_availability_ppm"] / 10_000
        renew_pct = r["renewal_success_rate_ppm"] / 10_000
        semfail = "Yes" if r["ever_global_semfail_ge_k"] else "No"

        print(f"{r['seed']:>6} {aa_pct:>7.2f} {aaa_pct:>7.2f} {r['failure_class']:>20} "
              f"{r['lapse_count']:>6} {r['max_single_lapse_epochs']:>8} {renew_pct:>10.2f} {semfail:>10}")


def print_aggregate_summary(summary: Dict[str, Any]):
    """Print aggregate summary."""
    print("\nAggregate Summary:")
    print("-" * 50)
    aa_mean_pct = summary["aa_mean_ppm"] / 10_000
    aa_std_pct = summary["aa_std_ppm"] / 10_000
    aaa_mean_pct = summary["aaa_mean_ppm"] / 10_000
    aaa_std_pct = summary["aaa_std_ppm"] / 10_000

    print(f"  AA:  mean={aa_mean_pct:.2f}% (std={aa_std_pct:.2f}%), min={summary['aa_min_ppm']/10_000:.2f}%, max={summary['aa_max_ppm']/10_000:.2f}%")
    print(f"  AAA: mean={aaa_mean_pct:.2f}% (std={aaa_std_pct:.2f}%), min={summary['aaa_min_ppm']/10_000:.2f}%, max={summary['aaa_max_ppm']/10_000:.2f}%")
    print(f"  Failure classes: {summary['failure_class_counts']}")
    print(f"  Failure count (hard failures): {summary['failure_count']}")
    print(f"  Lapse count: mean={summary['lapse_count_mean']:.1f}, total={summary['lapse_count_total']}")
    print(f"  Max single lapse: mean={summary['max_single_lapse_mean']:.1f}, max={summary['max_single_lapse_max']}")

    renew_mean_pct = summary["renewal_success_rate_mean_ppm"] / 10_000
    renew_std_pct = summary["renewal_success_rate_std_ppm"] / 10_000
    print(f"  Renewal success: mean={renew_mean_pct:.2f}% (std={renew_std_pct:.2f}%)")
    print(f"  Global sem_fail ≥K fraction: mean={summary['global_semfail_ge_k_fraction_mean']:.4f}")
    print(f"  Expiration reasons: {summary['expiration_reason_counts']}")

    # RTD summary
    rtd = summary["rtd_aggregate"]
    non_zero = {k: v for k, v in rtd.items() if v > 0}
    if non_zero:
        print(f"  RTD (non-zero buckets): {non_zero}")
    else:
        print(f"  RTD: No lapses recorded")


def print_baseline_comparison(summary: Dict[str, Any]):
    """Print comparison to Run 0 seed 2048 baseline."""
    print("\n" + "=" * 70)
    print("Comparison to Run 0 Attractor B (seed 2048)")
    print("=" * 70)
    print()
    print("Run 0 Seed 2048 (Attractor B) Reference:")
    print("  AA:  99.98%")
    print("  AAA: 100.00%")
    print("  Failure class: STABLE_AUTHORITY")
    print("  Lapses: 0")
    print()
    print("Run 2 Results:")
    aa_mean_pct = summary["aa_mean_ppm"] / 10_000
    aaa_mean_pct = summary["aaa_mean_ppm"] / 10_000
    print(f"  AA:  {aa_mean_pct:.2f}% (mean across 10 seeds)")
    print(f"  AAA: {aaa_mean_pct:.2f}% (mean across 10 seeds)")
    print(f"  Failure classes: {summary['failure_class_counts']}")
    print(f"  Total lapses: {summary['lapse_count_total']}")

    # Match assessment
    stable_count = summary["failure_class_counts"].get("STABLE_AUTHORITY", 0)
    if stable_count == 10 and summary["lapse_count_total"] == 0:
        print("\n✓ Run 2 matches Run 0 attractor B behavior across all seeds.")
    elif stable_count == 10:
        print(f"\n~ Run 2 achieves STABLE_AUTHORITY for all seeds, with {summary['lapse_count_total']} minor lapses.")
    else:
        print(f"\n⚠ Run 2 shows deviation from attractor B: {summary['failure_class_counts']}")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run minimal compliance experiment and save results."""
    config = RunConfig()

    # Print header
    print_run_header(config)

    # Run Model B across all seeds
    print("Running Model B (MINIMAL_ELIGIBILITY_ONLY)...")
    results = run_minimal_compliance(config)
    summary = compute_aggregate_summary(results)

    # Print results
    print_per_seed_table(results)
    print_aggregate_summary(summary)
    print_baseline_comparison(summary)

    # Check for constitutional failures
    print("\n" + "=" * 70)
    print("Constitutional Failure Check")
    print("=" * 70)

    if summary["failure_count"] > 0:
        print(f"\n⚠ {summary['failure_count']} constitutional failure(s) detected")
        print(f"  Failure class breakdown: {summary['failure_class_counts']}")
    else:
        print("\n✓ No constitutional failures detected.")
        print("  All runs classified as STABLE_AUTHORITY or BOUNDED_DEGRADATION.")

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"rsa_v100_run2_minimal_{timestamp}.json"

    output_data = {
        "run_type": "RSA v1.0 Run 2: Minimal Compliance / Hollow Authority (Model B)",
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
            "policy_hash": config.policy_hash(),
        },
        "adversary_model": {
            "name": "MINIMAL_ELIGIBILITY_ONLY",
            "description": "Emits minimal action trace to satisfy all commitments",
            "scope": "Applied to all incumbents (control and attack successors)",
            "behavior": "Fixed, deterministic, non-adaptive",
            "als_a_note": "Under strict AND, behaviorally equivalent to full compliance",
        },
        "results": results,
        "summary": summary,
        "baseline_comparison": {
            "run0_seed2048_aa_ppm": 999833,
            "run0_seed2048_aaa_ppm": 1000000,
            "run0_seed2048_failure_class": "STABLE_AUTHORITY",
            "run0_seed2048_lapses": 0,
        },
        "any_constitutional_failures": summary["failure_count"] > 0,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print()
    print("Run 2 complete.")
    if summary["failure_count"] > 0:
        print("⚠ Constitutional failures detected. Review before proceeding to Run 3.")
    else:
        print("✓ No constitutional failures. Ready to proceed to Run 3.")


if __name__ == "__main__":
    main()
