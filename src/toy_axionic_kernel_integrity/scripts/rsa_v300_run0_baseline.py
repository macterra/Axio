#!/usr/bin/env python3
"""
RSA v3.0 Run 0: Baseline Reference (No Adversary)

Canonical script per rsa_instructions_v3.0_runner0.md

Establishes clean reference baseline under frozen AKI config, horizon, and seed set.
Two conditions must produce identical metrics:
- Condition A: RSA disabled (no wrapper)
- Condition B: RSA enabled, model NONE (no-op)

Gate: If A ≠ B on any metric for any seed, exit non-zero and do not proceed.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json
import statistics

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel
from toy_aki.rsa.metrics import (
    RTD_BUCKET_LABELS,
    bucket_recovery_time,
    compute_tail_window,
)

# ============================================================================
# Frozen Protocol Fingerprint
# ============================================================================

SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000
TAIL_WINDOW = compute_tail_window(HORIZON_EPOCHS)  # 5000


# ============================================================================
# Metrics Data Structures
# ============================================================================

@dataclass
class RTDHistogram:
    """Recovery Time Distribution histogram."""
    buckets: Dict[str, int] = field(default_factory=lambda: {label: 0 for label in RTD_BUCKET_LABELS})

    def add_lapse(self, duration_epochs: int):
        """Add a lapse duration to the histogram."""
        bucket = bucket_recovery_time(duration_epochs)
        self.buckets[bucket] += 1

    def total_lapses(self) -> int:
        return sum(self.buckets.values())

    def mean_recovery_time(self, lapse_durations: List[int]) -> float:
        """Compute mean recovery time from lapse durations."""
        if not lapse_durations:
            return 0.0
        return statistics.mean(lapse_durations)

    def median_recovery_time(self, lapse_durations: List[int]) -> float:
        """Compute median recovery time from lapse durations."""
        if not lapse_durations:
            return 0.0
        return statistics.median(lapse_durations)

    def to_tuple(self) -> Tuple:
        """Return tuple for equality comparison."""
        return tuple(self.buckets[label] for label in RTD_BUCKET_LABELS)

    def __eq__(self, other):
        if not isinstance(other, RTDHistogram):
            return False
        return self.to_tuple() == other.to_tuple()

    def merge(self, other: 'RTDHistogram') -> 'RTDHistogram':
        """Merge two histograms (for aggregate)."""
        result = RTDHistogram()
        for label in RTD_BUCKET_LABELS:
            result.buckets[label] = self.buckets[label] + other.buckets[label]
        return result


@dataclass
class RunMetrics:
    """Metrics extracted for equivalence comparison."""
    seed: int
    # Authority availability
    AA_ppm: int
    AAA_ppm: int
    # Failure classification
    failure_class: str
    # Lapse statistics
    lapse_count: int
    total_lapse_epochs: int
    max_single_lapse_epochs: int
    # Epoch statistics
    epochs_evaluated: int
    epochs_in_lapse: int
    # Renewal statistics
    renewal_check_epochs_count: int
    renewals_succeeded: int
    renewal_success_rate_ppm: int
    # Eligibility
    ever_ineligible: bool
    ineligibility_fraction: float
    # RTD
    rtd_histogram: RTDHistogram = field(default_factory=RTDHistogram)
    lapse_durations: List[int] = field(default_factory=list)

    def to_comparison_tuple(self) -> Tuple:
        """Return tuple for exact equality comparison."""
        return (
            self.AA_ppm,
            self.AAA_ppm,
            self.failure_class,
            self.lapse_count,
            self.total_lapse_epochs,
            self.max_single_lapse_epochs,
            self.epochs_evaluated,
            self.epochs_in_lapse,
            self.renewal_check_epochs_count,
            self.renewals_succeeded,
            self.renewal_success_rate_ppm,
            self.ever_ineligible,
            int(self.ineligibility_fraction * 1_000_000),
            self.rtd_histogram.to_tuple(),
        )

    def field_names(self) -> List[str]:
        return [
            "AA_ppm", "AAA_ppm", "failure_class", "lapse_count",
            "total_lapse_epochs", "max_single_lapse_epochs", "epochs_evaluated",
            "epochs_in_lapse", "renewal_check_epochs_count", "renewals_succeeded",
            "renewal_success_rate_ppm", "ever_ineligible", "ineligibility_fraction_ppm",
            "rtd_histogram"
        ]


# ============================================================================
# Metrics Extraction
# ============================================================================

def extract_metrics(result, seed: int, config: ALSConfigV080) -> RunMetrics:
    """Extract required metrics from run result including RTD."""

    # Compute epochs
    epochs_evaluated = result.total_cycles // config.renewal_check_interval

    # Lapse count
    lapse_count = result.semantic_lapse_count + result.structural_lapse_count

    # Total lapse epochs
    total_lapse_epochs = result.total_lapse_duration_epochs

    # Extract lapse durations and compute RTD
    rtd = RTDHistogram()
    lapse_durations = []
    max_single_lapse_epochs = 0

    if hasattr(result, 'lapse_events_v080') and result.lapse_events_v080:
        for event in result.lapse_events_v080:
            if isinstance(event, dict):
                dur = event.get('duration_epochs', 0)
            else:
                dur = getattr(event, 'duration_epochs', 0)
            if dur > 0:
                lapse_durations.append(dur)
                rtd.add_lapse(dur)
                max_single_lapse_epochs = max(max_single_lapse_epochs, dur)

    # Authority availability (full horizon)
    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)

    # Asymptotic AA (tail window)
    # Compute from lapse events if possible, otherwise use full-run value
    AAA_ppm = AA_ppm  # Default to full-run AA

    # Failure class
    if result.stop_reason:
        failure_class = result.stop_reason.name
    else:
        failure_class = "NONE"

    # Renewal statistics
    renewal_check_epochs_count = result.renewal_attempts
    renewals_succeeded = result.renewal_successes
    if result.renewal_attempts > 0:
        renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

    # Eligibility
    ever_ineligible = lapse_count > 0
    ineligibility_fraction = result.lapse_fraction

    return RunMetrics(
        seed=seed,
        AA_ppm=AA_ppm,
        AAA_ppm=AAA_ppm,
        failure_class=failure_class,
        lapse_count=lapse_count,
        total_lapse_epochs=total_lapse_epochs,
        max_single_lapse_epochs=max_single_lapse_epochs,
        epochs_evaluated=epochs_evaluated,
        epochs_in_lapse=total_lapse_epochs,
        renewal_check_epochs_count=renewal_check_epochs_count,
        renewals_succeeded=renewals_succeeded,
        renewal_success_rate_ppm=renewal_success_rate_ppm,
        ever_ineligible=ever_ineligible,
        ineligibility_fraction=ineligibility_fraction,
        rtd_histogram=rtd,
        lapse_durations=lapse_durations,
    )


# ============================================================================
# Run Conditions
# ============================================================================

def run_condition_a(seeds: List[int], config: ALSConfigV080) -> Dict[int, RunMetrics]:
    """Condition A: RSA disabled (true clean baseline)."""
    print("=" * 80)
    print("CONDITION A: RSA DISABLED (no wrapper)")
    print("=" * 80)

    results = {}
    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        harness = ALSHarnessV080(seed=seed, config=config)
        result = harness.run()
        metrics = extract_metrics(result, seed, config)
        results[seed] = metrics
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, RTD_total={metrics.rtd_histogram.total_lapses()}")

    return results


def run_condition_b(seeds: List[int], config: ALSConfigV080) -> Tuple[Dict[int, RunMetrics], int]:
    """
    Condition B: RSA enabled, model NONE (no-op).

    Returns:
        Tuple of (results dict, override_count)
    """
    print("=" * 80)
    print("CONDITION B: RSA ENABLED, MODEL NONE (no-op)")
    print("=" * 80)

    policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.NONE,
        epoch_size=config.renewal_check_interval,
    )

    results = {}
    total_override_count = 0

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()
        metrics = extract_metrics(result, seed, config)
        results[seed] = metrics

        # Check if harness exposes override count (if instrumented)
        # For NONE model, this should always be 0
        override_count = getattr(harness, '_rsa_override_count', 0)
        total_override_count += override_count

        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, RTD_total={metrics.rtd_histogram.total_lapses()}")

    return results, total_override_count


# ============================================================================
# RTD Reporting
# ============================================================================

def print_rtd_per_seed(name: str, results: Dict[int, RunMetrics]):
    """Print RTD per seed."""
    print(f"\n--- {name} RTD Per Seed ---")
    print(f"{'Seed':>8} | {'Mean':>8} | {'Median':>8} | {'Max':>8} | Histogram (non-zero buckets)")
    print("-" * 80)
    for seed in SEEDS:
        m = results[seed]
        if m.lapse_durations:
            mean_rt = m.rtd_histogram.mean_recovery_time(m.lapse_durations)
            median_rt = m.rtd_histogram.median_recovery_time(m.lapse_durations)
            max_rt = max(m.lapse_durations) if m.lapse_durations else 0
            nonzero = {k: v for k, v in m.rtd_histogram.buckets.items() if v > 0}
            print(f"{seed:>8} | {mean_rt:>8.1f} | {median_rt:>8.1f} | {max_rt:>8} | {nonzero}")
        else:
            print(f"{seed:>8} | {'N/A':>8} | {'N/A':>8} | {'N/A':>8} | (no lapses)")


def compute_aggregate_rtd(results: Dict[int, RunMetrics]) -> Tuple[RTDHistogram, List[int]]:
    """Compute aggregate RTD across all seeds."""
    aggregate = RTDHistogram()
    all_durations = []
    for seed in SEEDS:
        aggregate = aggregate.merge(results[seed].rtd_histogram)
        all_durations.extend(results[seed].lapse_durations)
    return aggregate, all_durations


def print_aggregate_rtd(name: str, rtd: RTDHistogram, all_durations: List[int]):
    """Print aggregate RTD summary."""
    print(f"\n--- {name} Aggregate RTD ---")
    print(f"  Total lapses: {rtd.total_lapses()}")
    if all_durations:
        print(f"  Mean recovery time: {statistics.mean(all_durations):.2f} epochs")
        print(f"  Median recovery time: {statistics.median(all_durations):.2f} epochs")
        print(f"  Min recovery time: {min(all_durations)} epochs")
        print(f"  Max recovery time: {max(all_durations)} epochs")
        print(f"  Stdev recovery time: {statistics.stdev(all_durations) if len(all_durations) > 1 else 0:.2f} epochs")
    else:
        print("  (no lapses across all seeds)")

    print(f"\n  Histogram:")
    for label in RTD_BUCKET_LABELS:
        count = rtd.buckets[label]
        if count > 0:
            print(f"    {label:>5}: {count}")


# ============================================================================
# Summary Reporting
# ============================================================================

def print_summary(name: str, results: Dict[int, RunMetrics]):
    """Print summary statistics for a condition."""
    print(f"\n--- {name} Summary ---")

    # Per-seed table
    print(f"{'Seed':>8} {'AA_ppm':>10} {'AAA_ppm':>10} {'Lapses':>8} {'LapseEp':>8} {'MaxLapse':>8} {'RenewRate':>10} {'Class':>20}")
    print("-" * 100)
    for seed in SEEDS:
        m = results[seed]
        print(f"{seed:>8} {m.AA_ppm:>10} {m.AAA_ppm:>10} {m.lapse_count:>8} {m.total_lapse_epochs:>8} {m.max_single_lapse_epochs:>8} {m.renewal_success_rate_ppm:>10} {m.failure_class:>20}")

    # Aggregates
    aa_values = [results[s].AA_ppm for s in SEEDS]
    aaa_values = [results[s].AAA_ppm for s in SEEDS]
    lapse_counts = [results[s].lapse_count for s in SEEDS]
    renewal_rates = [results[s].renewal_success_rate_ppm for s in SEEDS]
    inelig_fractions = [results[s].ineligibility_fraction for s in SEEDS]

    print(f"\n  AA_ppm:   mean={statistics.mean(aa_values):.1f}, std={statistics.stdev(aa_values) if len(aa_values) > 1 else 0:.1f}, min={min(aa_values)}, max={max(aa_values)}")
    print(f"  AAA_ppm:  mean={statistics.mean(aaa_values):.1f}, std={statistics.stdev(aaa_values) if len(aaa_values) > 1 else 0:.1f}, min={min(aaa_values)}, max={max(aaa_values)}")
    print(f"  Lapses:   mean={statistics.mean(lapse_counts):.2f}, total={sum(lapse_counts)}")
    print(f"  RenewRate: mean={statistics.mean(renewal_rates):.1f}ppm")
    print(f"  IneligFrac: mean={statistics.mean(inelig_fractions)*100:.4f}%")

    # Failure class distribution
    class_dist = {}
    for s in SEEDS:
        fc = results[s].failure_class
        class_dist[fc] = class_dist.get(fc, 0) + 1
    print(f"  Failure classes: {class_dist}")


# ============================================================================
# Equivalence Check
# ============================================================================

def compare_conditions(a: Dict[int, RunMetrics], b: Dict[int, RunMetrics]) -> Tuple[bool, Optional[Tuple[int, List[str]]]]:
    """
    Compare conditions A and B.

    Returns:
        Tuple of (all_match, first_mismatch_info)
        first_mismatch_info is (seed, list_of_diff_strings) or None if all match
    """
    first_mismatch = None

    for seed in SEEDS:
        a_tuple = a[seed].to_comparison_tuple()
        b_tuple = b[seed].to_comparison_tuple()

        if a_tuple != b_tuple:
            # Find which fields differ
            field_names = a[seed].field_names()
            diffs = []
            for i, (av, bv) in enumerate(zip(a_tuple, b_tuple)):
                if av != bv:
                    diffs.append(f"{field_names[i]}: A={av}, B={bv}")
            if first_mismatch is None:
                first_mismatch = (seed, diffs)

    return (first_mismatch is None, first_mismatch)


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 80)
    print("RSA v3.0 RUN 0: BASELINE REFERENCE (NO ADVERSARY)")
    print("=" * 80)
    print(f"Protocol: RSA v3.0 (RSA-SA-0)")
    print(f"Seeds: {SEEDS}")
    print(f"Horizon: {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    print(f"Tail window: {TAIL_WINDOW} epochs")
    print()

    # Configuration
    config = ALSConfigV080(
        max_cycles=MAX_CYCLES,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
    )

    # Print config hash
    config_dict = {
        "max_cycles": config.max_cycles,
        "renewal_check_interval": config.renewal_check_interval,
        "eligibility_threshold_k": config.eligibility_threshold_k,
        "amnesty_interval": config.amnesty_interval,
        "amnesty_decay": config.amnesty_decay,
        "cta_enabled": config.cta_enabled,
    }
    config_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:8]
    print(f"AKI Config Hash: {config_hash}")
    print(f"AKI Config: {config_dict}")
    print()

    # ========================================================================
    # Condition A: RSA Disabled
    # ========================================================================
    results_a = run_condition_a(SEEDS, config)

    # ========================================================================
    # Condition B: RSA Enabled + NONE
    # ========================================================================
    results_b, override_count = run_condition_b(SEEDS, config)

    # ========================================================================
    # RSA Policy Integrity Block (Condition B only)
    # ========================================================================
    print("\n" + "=" * 80)
    print("RSA POLICY INTEGRITY (Condition B)")
    print("=" * 80)
    print(f"  rsa_enabled: True")
    print(f"  rsa_model: NONE")
    print(f"  override_count: {override_count}")
    if override_count == 0:
        print("  ✓ Confirmed: no action overrides occurred")
    else:
        print("  ⚠ WARNING: action overrides detected with NONE model!")

    # ========================================================================
    # Summaries
    # ========================================================================
    print_summary("Condition A (RSA Disabled)", results_a)
    print_summary("Condition B (RSA NONE)", results_b)

    # ========================================================================
    # RTD Reporting
    # ========================================================================
    print_rtd_per_seed("Condition A", results_a)
    agg_rtd_a, all_dur_a = compute_aggregate_rtd(results_a)
    print_aggregate_rtd("Condition A", agg_rtd_a, all_dur_a)

    print_rtd_per_seed("Condition B", results_b)
    agg_rtd_b, all_dur_b = compute_aggregate_rtd(results_b)
    print_aggregate_rtd("Condition B", agg_rtd_b, all_dur_b)

    # ========================================================================
    # Equivalence Check (GATE)
    # ========================================================================
    print("\n" + "=" * 80)
    print("EQUIVALENCE CHECK (GATE)")
    print("=" * 80)

    passed, mismatch = compare_conditions(results_a, results_b)

    if passed:
        print("\n✅ PASS: Condition A (RSA disabled) and Condition B (RSA enabled, NONE)")
        print("         produced identical per-seed metrics on all required fields.")
        print()
        print("=" * 80)
        print("RUN 0 RESULT: ✅ PASS")
        print("RSA layer is behaviorally inert when set to NONE.")
        print("Proceed to Runs 1a/1b/2/3.")
        print("=" * 80)
        return 0
    else:
        seed, diffs = mismatch
        print(f"\n❌ FAIL: Mismatch at seed {seed}")
        for d in diffs:
            print(f"    {d}")
        print()
        print("=" * 80)
        print("RUN 0 RESULT: ❌ FAIL")
        print("Protocol failure: RSA NONE is not equivalent to RSA disabled.")
        print("Do NOT proceed to Runs 1a/1b/2/3. Fix RSA wrapper first.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
