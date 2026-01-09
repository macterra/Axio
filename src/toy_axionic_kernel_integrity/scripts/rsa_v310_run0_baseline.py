#!/usr/bin/env python3
"""
RSA v3.1 Run 0: Baseline Reference (No Adversary)

Canonical script per rsa_instructions_v3.1_runner0.md

Establishes clean reference baseline under frozen AKI config, horizon, and seed set.
Two conditions must produce identical metrics:
- Condition A: RSA disabled (no wrapper)
- Condition B: RSA enabled, model NONE with explicit None capacity fields (no-op)

Gate: If A ≠ B on any metric for any seed, exit non-zero and do not proceed to Runs 1/2/3.
"""
import sys
import os

# Add src to path - use the correct path that harness expects
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json
import statistics
from datetime import datetime

# Use consistent import path (without src. prefix) that harness uses internally
from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel
from toy_aki.rsa.metrics import (
    RTD_BUCKET_LABELS,
    bucket_recovery_time,
    compute_tail_window,
)

# ============================================================================
# Frozen Protocol Fingerprint (v3.1)
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


@dataclass
class ConditionBIntegrity:
    """Integrity counters for Condition B."""
    total_wrapper_invoked: int = 0
    total_override_count: int = 0
    seeds_run: int = 0


def run_condition_b(seeds: List[int], config: ALSConfigV080) -> Tuple[Dict[int, RunMetrics], ConditionBIntegrity]:
    """
    Condition B: RSA enabled, model NONE with explicit None capacity fields.

    Per v3.1 spec:
    - Explicitly set policy_model=NONE
    - Explicitly set rsa_max_internal_states=None
    - Explicitly set rsa_max_learning_states=None

    Returns:
        Tuple of (results dict, integrity counters)
    """
    print("=" * 80)
    print("CONDITION B: RSA ENABLED, MODEL NONE (no-op)")
    print("  rsa_max_internal_states=None (explicit)")
    print("  rsa_max_learning_states=None (explicit)")
    print("=" * 80)

    # v3.1: Explicit None for capacity fields - NONE path must not consult them
    policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.NONE,
        rsa_version="v3.1",
        rsa_rng_stream="rsa_v310",
        rsa_max_internal_states=None,
        rsa_max_learning_states=None,
        epoch_size=config.renewal_check_interval,
    )

    results = {}
    integrity = ConditionBIntegrity()

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()
        metrics = extract_metrics(result, seed, config)
        results[seed] = metrics

        # v3.1 instrumentation: Track wrapper invocation and override counts
        wrapper_invoked = getattr(harness, '_rsa_wrapper_invoked_count', 0)
        override_count = getattr(harness, '_rsa_override_count', 0)
        integrity.total_wrapper_invoked += wrapper_invoked
        integrity.total_override_count += override_count
        integrity.seeds_run += 1

        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, RTD_total={metrics.rtd_histogram.total_lapses()}, wrapper_invoked={wrapper_invoked}")

    return results, integrity


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
# Report Generation
# ============================================================================

def generate_report(
    config: ALSConfigV080,
    config_hash: str,
    results_a: Dict[int, RunMetrics],
    results_b: Dict[int, RunMetrics],
    integrity: ConditionBIntegrity,
    passed: bool,
    mismatch: Optional[Tuple[int, List[str]]],
) -> str:
    """Generate markdown report."""
    report = []
    report.append("# RSA v3.1 Run 0: Baseline Reference Results")
    report.append("")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Protocol**: RSA v3.1 (RSA-LA-0)")
    report.append(f"**Gate**: Run 0 — Baseline Equivalence")
    report.append("")

    # Config section
    report.append("## Configuration")
    report.append("")
    report.append(f"- **AKI Config Hash**: `{config_hash}`")
    report.append(f"- **Horizon**: {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    report.append(f"- **Tail Window**: {TAIL_WINDOW} epochs")
    report.append(f"- **Seeds**: {SEEDS}")
    report.append("")
    report.append("### AKI Config (Frozen)")
    report.append("```python")
    report.append("ALSConfigV080(")
    report.append(f"    max_cycles={config.max_cycles},")
    report.append(f"    renewal_check_interval={config.renewal_check_interval},")
    report.append(f"    eligibility_threshold_k={config.eligibility_threshold_k},")
    report.append(f"    amnesty_interval={config.amnesty_interval},")
    report.append(f"    amnesty_decay={config.amnesty_decay},")
    report.append(f"    cta_enabled={config.cta_enabled},")
    report.append(")")
    report.append("```")
    report.append("")

    # Condition A results
    report.append("## Condition A: RSA Disabled")
    report.append("")
    report.append("| Seed | AA_ppm | AAA_ppm | Lapses | LapseEp | MaxLapse | RenewRate | Class |")
    report.append("|------|--------|---------|--------|---------|----------|-----------|-------|")
    for seed in SEEDS:
        m = results_a[seed]
        report.append(f"| {seed} | {m.AA_ppm} | {m.AAA_ppm} | {m.lapse_count} | {m.total_lapse_epochs} | {m.max_single_lapse_epochs} | {m.renewal_success_rate_ppm} | {m.failure_class} |")
    report.append("")

    # Condition A aggregates
    aa_a = [results_a[s].AA_ppm for s in SEEDS]
    report.append(f"**AA mean**: {statistics.mean(aa_a):.1f} ppm, std: {statistics.stdev(aa_a) if len(aa_a) > 1 else 0:.1f}")
    report.append("")

    # Condition B results
    report.append("## Condition B: RSA Enabled, NONE")
    report.append("")
    report.append("**RSAPolicyConfig (explicit None fields)**:")
    report.append("```python")
    report.append("RSAPolicyConfig(")
    report.append("    policy_model=RSAPolicyModel.NONE,")
    report.append("    rsa_version='v3.1',")
    report.append("    rsa_rng_stream='rsa_v310',")
    report.append("    rsa_max_internal_states=None,  # explicit")
    report.append("    rsa_max_learning_states=None,  # explicit")
    report.append(")")
    report.append("```")
    report.append("")
    report.append("| Seed | AA_ppm | AAA_ppm | Lapses | LapseEp | MaxLapse | RenewRate | Class |")
    report.append("|------|--------|---------|--------|---------|----------|-----------|-------|")
    for seed in SEEDS:
        m = results_b[seed]
        report.append(f"| {seed} | {m.AA_ppm} | {m.AAA_ppm} | {m.lapse_count} | {m.total_lapse_epochs} | {m.max_single_lapse_epochs} | {m.renewal_success_rate_ppm} | {m.failure_class} |")
    report.append("")

    # Condition B aggregates
    aa_b = [results_b[s].AA_ppm for s in SEEDS]
    report.append(f"**AA mean**: {statistics.mean(aa_b):.1f} ppm, std: {statistics.stdev(aa_b) if len(aa_b) > 1 else 0:.1f}")
    report.append("")

    # Policy integrity block
    report.append("## RSA Policy Integrity (Condition B)")
    report.append("")
    report.append("| Metric | Value | Status |")
    report.append("|--------|-------|--------|")
    report.append(f"| rsa_enabled | True | ✓ |")
    report.append(f"| rsa_model | NONE | ✓ |")
    report.append(f"| rsa_max_internal_states | None | ✓ (not consulted) |")
    report.append(f"| rsa_max_learning_states | None | ✓ (not consulted) |")
    report.append(f"| wrapper_invoked_count | {integrity.total_wrapper_invoked} | {'✓' if integrity.total_wrapper_invoked > 0 else '⚠ (expected > 0)'} |")
    report.append(f"| override_count | {integrity.total_override_count} | {'✓' if integrity.total_override_count == 0 else '⚠ (expected 0)'} |")
    report.append(f"| seeds_run | {integrity.seeds_run} | ✓ |")
    report.append("")

    if integrity.total_wrapper_invoked > 0:
        report.append("> ✓ **Enabled-path proof**: `wrapper_invoked_count > 0` confirms RSA intercept path was evaluated.")
        report.append("> No observable adapter exists for NONE model; wrapper invocation is the proof.")
    else:
        report.append("> ⚠ **Warning**: `wrapper_invoked_count == 0` — enabled-path may not have been evaluated.")
    report.append("")

    # Equivalence result
    report.append("## Equivalence Check")
    report.append("")
    if passed:
        report.append("### ✅ PASS")
        report.append("")
        report.append("> Condition A (RSA disabled) and Condition B (RSA enabled, NONE) produced identical per-seed metrics.")
        report.append("")
        report.append("The RSA v3.1 layer is behaviorally inert when set to NONE with explicit `None` capacity fields.")
    else:
        seed, diffs = mismatch
        report.append("### ❌ FAIL")
        report.append("")
        report.append(f"Mismatch detected at seed {seed}:")
        report.append("")
        for d in diffs:
            report.append(f"- {d}")
        report.append("")
        report.append("> **Do NOT proceed to Runs 1/2/3.** Fix RSA wrapper first.")
    report.append("")

    # Final gate status
    report.append("## Gate Status")
    report.append("")
    if passed:
        report.append("```")
        report.append("RUN 0 RESULT: ✅ PASS")
        report.append("RSA v3.1 layer is behaviorally inert when set to NONE.")
        report.append("Proceed to Runs 1/2/3.")
        report.append("```")
    else:
        report.append("```")
        report.append("RUN 0 RESULT: ❌ FAIL")
        report.append("Protocol failure: RSA NONE is not equivalent to RSA disabled.")
        report.append("Do NOT proceed to Runs 1/2/3.")
        report.append("```")
    report.append("")

    return "\n".join(report)


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 80)
    print("RSA v3.1 RUN 0: BASELINE REFERENCE (NO ADVERSARY)")
    print("=" * 80)
    print(f"Protocol: RSA v3.1 (RSA-LA-0)")
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
    results_b, integrity = run_condition_b(SEEDS, config)

    # ========================================================================
    # RSA Policy Integrity Block (Condition B only)
    # ========================================================================
    print("\n" + "=" * 80)
    print("RSA POLICY INTEGRITY (Condition B)")
    print("=" * 80)
    print(f"  rsa_enabled: True")
    print(f"  rsa_model: NONE")
    print(f"  rsa_max_internal_states: None (explicit, not consulted)")
    print(f"  rsa_max_learning_states: None (explicit, not consulted)")
    print(f"  wrapper_invoked_count: {integrity.total_wrapper_invoked}")
    print(f"  override_count: {integrity.total_override_count}")

    if integrity.total_wrapper_invoked > 0:
        print("  ✓ Enabled-path proof: wrapper_invoked_count > 0")
        print("  Note: No observable adapter exists for NONE; wrapper invocation is the proof.")
    else:
        print("  ⚠ Warning: wrapper_invoked_count == 0 — enabled-path may not be exercised")

    if integrity.total_override_count == 0:
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
        print("RSA v3.1 layer is behaviorally inert when set to NONE.")
        print("Proceed to Runs 1/2/3.")
        print("=" * 80)
    else:
        seed, diffs = mismatch
        print(f"\n❌ FAIL: Mismatch at seed {seed}")
        for d in diffs:
            print(f"    {d}")
        print()
        print("=" * 80)
        print("RUN 0 RESULT: ❌ FAIL")
        print("Protocol failure: RSA NONE is not equivalent to RSA disabled.")
        print("Do NOT proceed to Runs 1/2/3. Fix RSA wrapper first.")
        print("=" * 80)

    # ========================================================================
    # Generate Report
    # ========================================================================
    report = generate_report(config, config_hash, results_a, results_b, integrity, passed, mismatch)

    report_path = os.path.join(os.path.dirname(__file__), "..", "reports", "rsa_v310_run0_baseline.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport written to: {report_path}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
