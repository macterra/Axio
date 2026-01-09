#!/usr/bin/env python3
"""
RSA v3.1 Run 3: Model O (STOCHASTIC_MIXER)

Canonical script per rsa_instructions_v3.1_runner3.md

Tests whether learning to mix among a portfolio of known strategies
can defeat constitutional recovery.

Strategy Pool (frozen):
    0: COMPLIANT (baseline)
    1: RESONANT_LAPSE (v3.0 Model J)
    2: EDGE_OSCILLATOR (v3.0 Model K)
    3: CTA_PHASE_LOCKER (v3.0 Model L)
    4: INVALID_ALWAYS (degenerate)

Learning Parameters (frozen):
    - Q_SCALE: 1000 (fixed-point precision)
    - lr_shift: 6 (lr = 1/64)
    - epsilon_ppm: 100,000 (10% exploration)
    - strategy_count: 5
    - weight_max: 10,000

Capacity Bounds:
    - max_internal_states: 5 (current strategy index)
    - max_learning_states: 5 (learning dimensions)
"""
import sys
import os
import math

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
from toy_aki.rsa.policy import (
    RSAPolicyConfig,
    RSAPolicyModel,
    LearningRSAWrapper,
)
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

# Model O Learning Parameters (frozen)
Q_SCALE = 1000
LR_SHIFT = 6  # lr = 1/64
EPSILON_PPM = 100_000  # 10%
STRATEGY_COUNT = 5
WEIGHT_MAX = 10_000

# Capacity bounds
MAX_INTERNAL_STATES = STRATEGY_COUNT   # current strategy index
MAX_LEARNING_STATES = STRATEGY_COUNT   # learning dimensions

# Strategy names for reporting
STRATEGY_NAMES = {
    0: "COMPLIANT",
    1: "RESONANT_LAPSE",
    2: "EDGE_OSCILLATOR",
    3: "CTA_PHASE_LOCKER",
    4: "INVALID_ALWAYS",
}


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

    def to_tuple(self) -> Tuple:
        """Return tuple for equality comparison."""
        return tuple(self.buckets[label] for label in RTD_BUCKET_LABELS)

    def merge(self, other: 'RTDHistogram') -> 'RTDHistogram':
        """Merge two histograms (for aggregate)."""
        result = RTDHistogram()
        for label in RTD_BUCKET_LABELS:
            result.buckets[label] = self.buckets[label] + other.buckets[label]
        return result


@dataclass
class RunMetrics:
    """Metrics extracted for comparison."""
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
    # RTD
    rtd_histogram: RTDHistogram = field(default_factory=RTDHistogram)
    lapse_durations: List[int] = field(default_factory=list)


@dataclass
class StrategyDiagnostics:
    """Strategy-mixing diagnostics for Model O (Run 3)."""
    strategy_selection_counts: Dict[int, int]
    strategy_selection_entropy: float
    dominant_strategy: int
    dominant_strategy_name: str
    dominant_strategy_fraction: float
    strategy_switch_count: int
    longest_strategy_streak: int
    final_weights: List[int]
    weight_range: Tuple[int, int]


@dataclass
class LearningDiagnostics:
    """Learning-specific diagnostics for Model O."""
    weights: List[int]
    weight_range: Tuple[int, int]
    weight_updates_count: int
    distinct_internal_states_observed: int
    distinct_learning_states_observed: int


@dataclass
class Run3Metrics:
    """Full metrics for Run 3 including strategy and learning diagnostics."""
    run_metrics: RunMetrics
    strategy_diagnostics: Optional[StrategyDiagnostics] = None
    learning_diagnostics: Optional[LearningDiagnostics] = None
    # Instrumentation
    wrapper_invoked_count: int = 0
    override_count: int = 0
    # v3.1 wrapper summary
    wrapper_summary: Optional[Dict[str, Any]] = None


# ============================================================================
# Baseline Loading
# ============================================================================

def load_baseline_from_run0(report_path: str) -> Dict[int, int]:
    """
    Load baseline AA_ppm values from Run 0 report.

    Returns:
        Dict mapping seed -> AA_ppm
    """
    with open(report_path, "r") as f:
        content = f.read()

    # Parse the Condition A table to get baseline AA values
    baseline = {}
    in_condition_a = False
    for line in content.split("\n"):
        if "## Condition A: RSA Disabled" in line:
            in_condition_a = True
            continue
        if in_condition_a and line.startswith("| ") and not line.startswith("| Seed") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                try:
                    seed = int(parts[1])
                    aa_ppm = int(parts[2])
                    baseline[seed] = aa_ppm
                except ValueError:
                    pass
        if in_condition_a and line.startswith("**AA mean**"):
            break

    return baseline


# ============================================================================
# Metrics Extraction
# ============================================================================

def extract_metrics(result, seed: int, config: ALSConfigV080) -> RunMetrics:
    """Extract required metrics from run result including RTD."""

    epochs_evaluated = result.total_cycles // config.renewal_check_interval
    lapse_count = result.semantic_lapse_count + result.structural_lapse_count
    total_lapse_epochs = result.total_lapse_duration_epochs

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

    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)
    AAA_ppm = AA_ppm

    if result.stop_reason:
        failure_class = result.stop_reason.name
    else:
        failure_class = "NONE"

    renewal_check_epochs_count = result.renewal_attempts
    renewals_succeeded = result.renewal_successes
    if result.renewal_attempts > 0:
        renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

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
        rtd_histogram=rtd,
        lapse_durations=lapse_durations,
    )


def compute_entropy(counts: Dict[int, int]) -> float:
    """
    Compute base-2 entropy from selection histogram.

    H = -Σ p_i * log2(p_i) for p_i > 0
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


def extract_strategy_diagnostics(harness: ALSHarnessV080) -> Optional[StrategyDiagnostics]:
    """Extract strategy-mixing diagnostics from harness v3.1 wrapper."""
    wrapper = getattr(harness, '_rsa_v31_wrapper', None)
    if wrapper is None:
        return None

    try:
        diag = wrapper.get_learning_diagnostics()
        telemetry = wrapper.get_strategy_telemetry()
        summary = wrapper.get_run_summary()

        # Get strategy selection counts
        selection_counts = diag.get("strategy_selection_counts", {})
        total_selections = sum(selection_counts.values())

        # Compute entropy
        entropy = compute_entropy(selection_counts)

        # Get final weights and find dominant strategy
        final_weights = diag.get("weights", [])
        if final_weights:
            dominant_idx = final_weights.index(max(final_weights))
        else:
            dominant_idx = 0

        dominant_name = STRATEGY_NAMES.get(dominant_idx, f"UNKNOWN_{dominant_idx}")

        # Compute dominant strategy fraction (from selection counts, not weights)
        dominant_count = selection_counts.get(dominant_idx, 0)
        dominant_fraction = dominant_count / total_selections if total_selections > 0 else 0.0

        # Get switch/streak from telemetry
        switch_count = telemetry.get("strategy_switch_count", 0)
        longest_streak = telemetry.get("longest_strategy_streak", 0)

        return StrategyDiagnostics(
            strategy_selection_counts=selection_counts,
            strategy_selection_entropy=entropy,
            dominant_strategy=dominant_idx,
            dominant_strategy_name=dominant_name,
            dominant_strategy_fraction=dominant_fraction,
            strategy_switch_count=switch_count,
            longest_strategy_streak=longest_streak,
            final_weights=final_weights,
            weight_range=tuple(diag.get("weight_range", (0, 0))),
        )
    except Exception as e:
        print(f"  Warning: Failed to extract strategy diagnostics: {e}")
        return None


def extract_learning_diagnostics(harness: ALSHarnessV080) -> Optional[LearningDiagnostics]:
    """Extract learning diagnostics from harness v3.1 wrapper."""
    wrapper = getattr(harness, '_rsa_v31_wrapper', None)
    if wrapper is None:
        return None

    try:
        diag = wrapper.get_learning_diagnostics()
        summary = wrapper.get_run_summary()

        return LearningDiagnostics(
            weights=diag.get("weights", []),
            weight_range=tuple(diag.get("weight_range", (0, 0))),
            weight_updates_count=diag.get("weight_updates_count", 0),
            distinct_internal_states_observed=summary.get("observed_internal_state_count", 0),
            distinct_learning_states_observed=summary.get("observed_learning_state_count", 0),
        )
    except Exception as e:
        print(f"  Warning: Failed to extract learning diagnostics: {e}")
        return None


# ============================================================================
# Run Model O
# ============================================================================

def run_model_o(seeds: List[int], config: ALSConfigV080) -> Dict[int, Run3Metrics]:
    """Run Model O (STOCHASTIC_MIXER) with full diagnostics."""
    print("=" * 80)
    print("RUN 3: Model O (STOCHASTIC_MIXER)")
    print("=" * 80)
    print(f"  Q_SCALE: {Q_SCALE}")
    print(f"  LR_SHIFT: {LR_SHIFT} (lr = 1/{2**LR_SHIFT})")
    print(f"  EPSILON_PPM: {EPSILON_PPM} ({EPSILON_PPM/10000:.1f}%)")
    print(f"  STRATEGY_COUNT: {STRATEGY_COUNT}")
    print(f"  WEIGHT_MAX: {WEIGHT_MAX}")
    print(f"  MAX_INTERNAL_STATES: {MAX_INTERNAL_STATES}")
    print(f"  MAX_LEARNING_STATES: {MAX_LEARNING_STATES}")
    print()
    print("  Strategy Pool:")
    for i, name in STRATEGY_NAMES.items():
        print(f"    {i}: {name}")
    print()

    # v3.1 policy configuration
    policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
        rsa_version="v3.1",
        rsa_rng_stream="rsa_v310",
        rsa_max_internal_states=MAX_INTERNAL_STATES,
        rsa_max_learning_states=MAX_LEARNING_STATES,
        epoch_size=RENEWAL_CHECK_INTERVAL,
        rsa_q_scale=Q_SCALE,
        rsa_learning_rate_shift=LR_SHIFT,
        rsa_epsilon_ppm=EPSILON_PPM,
        rsa_strategy_count=STRATEGY_COUNT,
        rsa_weight_max=WEIGHT_MAX,
    )

    results = {}

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()

        metrics = extract_metrics(result, seed, config)
        strategy_diag = extract_strategy_diagnostics(harness)
        learning_diag = extract_learning_diagnostics(harness)

        # Get instrumentation
        wrapper_invoked = getattr(harness, '_rsa_wrapper_invoked_count', 0)
        override_count = getattr(harness, '_rsa_override_count', 0)

        # Get wrapper summary
        wrapper = getattr(harness, '_rsa_v31_wrapper', None)
        wrapper_summary = wrapper.get_run_summary() if wrapper else None

        run3_metrics = Run3Metrics(
            run_metrics=metrics,
            strategy_diagnostics=strategy_diag,
            learning_diagnostics=learning_diag,
            wrapper_invoked_count=wrapper_invoked,
            override_count=override_count,
            wrapper_summary=wrapper_summary,
        )
        results[seed] = run3_metrics

        # Print summary
        dominant = strategy_diag.dominant_strategy_name if strategy_diag else "N/A"
        entropy = f"{strategy_diag.strategy_selection_entropy:.2f}" if strategy_diag else "N/A"
        switches = strategy_diag.strategy_switch_count if strategy_diag else 0
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"dom={dominant}, H={entropy}, switches={switches}")

    return results


# ============================================================================
# Reporting
# ============================================================================

def print_summary(name: str, results: Dict[int, Run3Metrics], baseline: Dict[int, int]):
    """Print summary statistics with deltas."""
    print(f"\n--- {name} Summary ---")

    # Per-seed table
    print(f"{'Seed':>8} {'AA_ppm':>10} {'ΔAA':>10} {'Lapses':>8} {'Dominant':>18} {'Entropy':>8} {'Switches':>10}")
    print("-" * 90)
    for seed in SEEDS:
        m = results[seed].run_metrics
        delta_aa = m.AA_ppm - baseline.get(seed, 0)
        delta_str = f"{delta_aa:+d}"
        strat = results[seed].strategy_diagnostics
        dom = strat.dominant_strategy_name if strat else "N/A"
        entropy = f"{strat.strategy_selection_entropy:.2f}" if strat else "N/A"
        switches = strat.strategy_switch_count if strat else 0
        print(f"{seed:>8} {m.AA_ppm:>10} {delta_str:>10} {m.lapse_count:>8} {dom:>18} {entropy:>8} {switches:>10}")

    # Aggregates
    aa_values = [results[s].run_metrics.AA_ppm for s in SEEDS]
    delta_values = [results[s].run_metrics.AA_ppm - baseline.get(s, 0) for s in SEEDS]
    lapse_counts = [results[s].run_metrics.lapse_count for s in SEEDS]
    override_counts = [results[s].override_count for s in SEEDS]

    print(f"\n  AA_ppm:     mean={statistics.mean(aa_values):.1f}, std={statistics.stdev(aa_values) if len(aa_values) > 1 else 0:.1f}")
    print(f"  ΔAA (vs B): mean={statistics.mean(delta_values):.1f}, min={min(delta_values)}, max={max(delta_values)}")
    print(f"  Lapses:     mean={statistics.mean(lapse_counts):.2f}, total={sum(lapse_counts)}")
    print(f"  Overrides:  total={sum(override_counts)}")


def print_strategy_diagnostics(results: Dict[int, Run3Metrics]):
    """Print strategy-mixing diagnostics summary."""
    print("\n--- Strategy Diagnostics (Model O) ---")

    for seed in SEEDS:
        strat = results[seed].strategy_diagnostics
        if strat:
            print(f"\nSeed {seed}:")
            print(f"  Selection counts: {dict(sorted(strat.strategy_selection_counts.items()))}")
            print(f"  Selection entropy: {strat.strategy_selection_entropy:.3f} bits")
            print(f"  Dominant strategy: {strat.dominant_strategy} ({strat.dominant_strategy_name})")
            print(f"  Dominant fraction: {strat.dominant_strategy_fraction*100:.1f}%")
            print(f"  Strategy switches: {strat.strategy_switch_count}")
            print(f"  Longest streak: {strat.longest_strategy_streak}")
            print(f"  Final weights: {strat.final_weights}")


def print_learning_diagnostics(results: Dict[int, Run3Metrics]):
    """Print learning diagnostics summary."""
    print("\n--- Learning Diagnostics (Model O) ---")

    for seed in SEEDS:
        learn = results[seed].learning_diagnostics
        if learn:
            print(f"\nSeed {seed}:")
            print(f"  Final weights: {learn.weights}")
            print(f"  Weight range: [{learn.weight_range[0]}, {learn.weight_range[1]}]")
            print(f"  Weight updates: {learn.weight_updates_count}")
            print(f"  Distinct internal states: {learn.distinct_internal_states_observed}")
            print(f"  Distinct learning states: {learn.distinct_learning_states_observed}")


def generate_report(
    config: ALSConfigV080,
    config_hash: str,
    results: Dict[int, Run3Metrics],
    baseline: Dict[int, int],
) -> str:
    """Generate markdown report."""
    report = []
    report.append("# RSA v3.1 Run 3: Model O (STOCHASTIC_MIXER) Results")
    report.append("")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Protocol**: RSA v3.1 (RSA-LA-0)")
    report.append(f"**Run**: 3 — Model O (STOCHASTIC_MIXER)")
    report.append("")

    # Config section
    report.append("## Configuration")
    report.append("")
    report.append(f"- **AKI Config Hash**: `{config_hash}`")
    report.append(f"- **Horizon**: {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    report.append(f"- **Tail Window**: {TAIL_WINDOW} epochs")
    report.append(f"- **Seeds**: {SEEDS}")
    report.append("")

    report.append("### Learning Parameters (Model O)")
    report.append("```python")
    report.append("RSAPolicyConfig(")
    report.append(f"    policy_model=RSAPolicyModel.STOCHASTIC_MIXER,")
    report.append(f"    rsa_version='v3.1',")
    report.append(f"    rsa_max_internal_states={MAX_INTERNAL_STATES},  # strategy index")
    report.append(f"    rsa_max_learning_states={MAX_LEARNING_STATES},  # learning dimensions")
    report.append(f"    rsa_q_scale={Q_SCALE},")
    report.append(f"    rsa_learning_rate_shift={LR_SHIFT},  # lr = 1/{2**LR_SHIFT}")
    report.append(f"    rsa_epsilon_ppm={EPSILON_PPM},  # {EPSILON_PPM/10000:.1f}%")
    report.append(f"    rsa_strategy_count={STRATEGY_COUNT},")
    report.append(f"    rsa_weight_max={WEIGHT_MAX},")
    report.append(")")
    report.append("```")
    report.append("")

    report.append("### Strategy Pool (Frozen)")
    report.append("")
    report.append("| Index | Strategy | Description |")
    report.append("|-------|----------|-------------|")
    report.append("| 0 | COMPLIANT | Always compliant (baseline) |")
    report.append("| 1 | RESONANT_LAPSE | Periodic invalid commit (v3.0 Model J) |")
    report.append("| 2 | EDGE_OSCILLATOR | Eligibility-edge alternation (v3.0 Model K) |")
    report.append("| 3 | CTA_PHASE_LOCKER | CTA boundary attacks (v3.0 Model L) |")
    report.append("| 4 | INVALID_ALWAYS | Always invalid commit (degenerate) |")
    report.append("")

    # Results table
    report.append("## Run 3 Results")
    report.append("")
    report.append("| Seed | AA_ppm | ΔAA | Lapses | LapseEp | Overrides | Dominant | Entropy | Class |")
    report.append("|------|--------|-----|--------|---------|-----------|----------|---------|-------|")
    for seed in SEEDS:
        m = results[seed].run_metrics
        delta_aa = m.AA_ppm - baseline.get(seed, 0)
        strat = results[seed].strategy_diagnostics
        dom = strat.dominant_strategy_name if strat else "N/A"
        entropy = f"{strat.strategy_selection_entropy:.2f}" if strat else "N/A"
        report.append(f"| {seed} | {m.AA_ppm} | {delta_aa:+d} | {m.lapse_count} | {m.total_lapse_epochs} | {results[seed].override_count} | {dom} | {entropy} | {m.failure_class} |")
    report.append("")

    # Aggregates
    aa_values = [results[s].run_metrics.AA_ppm for s in SEEDS]
    delta_values = [results[s].run_metrics.AA_ppm - baseline.get(s, 0) for s in SEEDS]
    lapse_counts = [results[s].run_metrics.lapse_count for s in SEEDS]
    override_counts = [results[s].override_count for s in SEEDS]

    report.append("### Aggregate Statistics")
    report.append("")
    report.append(f"- **AA mean**: {statistics.mean(aa_values):.1f} ppm, std: {statistics.stdev(aa_values) if len(aa_values) > 1 else 0:.1f}")
    report.append(f"- **ΔAA mean (vs baseline)**: {statistics.mean(delta_values):.1f}, range: [{min(delta_values)}, {max(delta_values)}]")
    report.append(f"- **Total lapses**: {sum(lapse_counts)} across all seeds")
    report.append(f"- **Total overrides**: {sum(override_counts)} (adversary interventions)")
    report.append("")

    # Baseline comparison
    baseline_mean = statistics.mean(baseline.values())
    report.append("### Baseline Comparison")
    report.append("")
    report.append(f"- **Baseline AA mean (Run 0)**: {baseline_mean:.1f} ppm")
    report.append(f"- **Run 3 AA mean**: {statistics.mean(aa_values):.1f} ppm")
    report.append(f"- **ΔAA mean**: {statistics.mean(delta_values):.1f} ppm")
    report.append("")

    # Strategy diagnostics section
    report.append("## Strategy-Mixing Diagnostics")
    report.append("")
    report.append("| Seed | Entropy | DomStrat | DomFrac | Switches | LongestStreak |")
    report.append("|------|---------|----------|---------|----------|---------------|")
    for seed in SEEDS:
        strat = results[seed].strategy_diagnostics
        if strat:
            report.append(f"| {seed} | {strat.strategy_selection_entropy:.3f} | {strat.dominant_strategy} ({strat.dominant_strategy_name}) | {strat.dominant_strategy_fraction*100:.1f}% | {strat.strategy_switch_count} | {strat.longest_strategy_streak} |")
        else:
            report.append(f"| {seed} | N/A | N/A | N/A | N/A | N/A |")
    report.append("")

    # Aggregate strategy stats
    entropies = [results[s].strategy_diagnostics.strategy_selection_entropy for s in SEEDS if results[s].strategy_diagnostics]
    switch_counts = [results[s].strategy_diagnostics.strategy_switch_count for s in SEEDS if results[s].strategy_diagnostics]
    if entropies:
        report.append("### Aggregate Strategy Statistics")
        report.append("")
        report.append(f"- **Entropy mean**: {statistics.mean(entropies):.3f} bits, std: {statistics.stdev(entropies) if len(entropies) > 1 else 0:.3f}")
        report.append(f"- **Switch count mean**: {statistics.mean(switch_counts):.1f}")
        report.append("")

    # Strategy selection histogram
    report.append("### Strategy Selection Histogram (per seed)")
    report.append("")
    for seed in SEEDS:
        strat = results[seed].strategy_diagnostics
        if strat and strat.strategy_selection_counts:
            counts_str = ", ".join(f"{STRATEGY_NAMES[i]}: {strat.strategy_selection_counts.get(i, 0)}" for i in range(STRATEGY_COUNT))
            report.append(f"**Seed {seed}**: {{{counts_str}}}")
    report.append("")

    # Final weights
    report.append("### Final Weights (per seed)")
    report.append("")
    report.append("| Seed | W0 (COMPLIANT) | W1 (RESONANT) | W2 (EDGE) | W3 (CTA) | W4 (INVALID) |")
    report.append("|------|----------------|---------------|-----------|----------|--------------|")
    for seed in SEEDS:
        strat = results[seed].strategy_diagnostics
        if strat and strat.final_weights:
            w = strat.final_weights
            report.append(f"| {seed} | {w[0]} | {w[1]} | {w[2]} | {w[3]} | {w[4]} |")
        else:
            report.append(f"| {seed} | N/A | N/A | N/A | N/A | N/A |")
    report.append("")

    # State exercised check
    report.append("## State Exercise Verification")
    report.append("")
    report.append("| Seed | Internal States Observed | Learning States Observed | Internal OK | Learning OK |")
    report.append("|------|--------------------------|--------------------------|-------------|-------------|")
    for seed in SEEDS:
        learn = results[seed].learning_diagnostics
        if learn:
            int_ok = "✓" if learn.distinct_internal_states_observed >= 2 else "✗"
            learn_ok = "✓" if learn.distinct_learning_states_observed >= 2 else "✗"
            report.append(f"| {seed} | {learn.distinct_internal_states_observed} | {learn.distinct_learning_states_observed} | {int_ok} | {learn_ok} |")
        else:
            report.append(f"| {seed} | N/A | N/A | N/A | N/A |")
    report.append("")

    # Instrumentation section
    total_wrapper = sum(results[s].wrapper_invoked_count for s in SEEDS)
    total_override = sum(results[s].override_count for s in SEEDS)
    report.append("## RSA Policy Instrumentation")
    report.append("")
    report.append("| Metric | Value | Notes |")
    report.append("|--------|-------|-------|")
    report.append(f"| wrapper_invoked_count | {total_wrapper} | v3.1 intercept path evaluated |")
    report.append(f"| override_count | {total_override} | adversary action emitted |")
    report.append("")

    # Survival assessment
    report.append("## Survival Assessment")
    report.append("")

    all_horizon = all(results[s].run_metrics.failure_class == "HORIZON_EXHAUSTED" for s in SEEDS)
    any_ineligible = any(results[s].run_metrics.failure_class == "INELIGIBLE" for s in SEEDS)
    aa_degradation = statistics.mean(delta_values)
    max_degradation = min(delta_values)

    if all_horizon:
        report.append("### ✅ AKI SURVIVED")
        report.append("")
        report.append("> All seeds reached `HORIZON_EXHAUSTED`. The constitutional mechanisms held.")
        report.append("")
        report.append("**Key finding**: Stochastic mixing over a portfolio of known strategies (Model O)")
        report.append("could not defeat constitutional survivability. Learning to mix strategies did not")
        report.append("outperform any single constituent strategy in terms of causing terminal failure.")
        report.append("")
        report.append(f"- **ΔAA mean**: {aa_degradation:.0f} ppm ({abs(aa_degradation)/10000:.1f}% {'degradation' if aa_degradation < 0 else 'improvement'})")
        report.append(f"- **Maximum degradation**: {max_degradation} ppm ({abs(max_degradation)/10000:.1f}%)")
        report.append(f"- **Survival**: 10/10 seeds")
    elif any_ineligible:
        ineligible_seeds = [s for s in SEEDS if results[s].run_metrics.failure_class == "INELIGIBLE"]
        report.append("### ❌ AKI DID NOT SURVIVE")
        report.append("")
        report.append(f"> {len(ineligible_seeds)} seed(s) terminated with `INELIGIBLE`: {ineligible_seeds}")
        report.append("")
        report.append("The stochastic mixer succeeded in defeating constitutional survivability.")
    else:
        non_horizon = [s for s in SEEDS if results[s].run_metrics.failure_class != "HORIZON_EXHAUSTED"]
        report.append("### ⚠️ MIXED RESULTS")
        report.append("")
        report.append(f"> Seeds {non_horizon} did not reach HORIZON_EXHAUSTED.")
        for s in non_horizon:
            report.append(f">   Seed {s}: {results[s].run_metrics.failure_class}")

    report.append("")

    # Run 3 interpretation
    report.append("## Run 3 Interpretation")
    report.append("")
    report.append("Run 3 is the **final adversary class** in RSA v3.1.")
    report.append("")

    if all_horizon:
        report.append("**Result**: Negative for stochastic mixing hypothesis.")
        report.append("")
        report.append("Learning to mix among strategies (COMPLIANT, RESONANT_LAPSE, EDGE_OSCILLATOR,")
        report.append("CTA_PHASE_LOCKER, INVALID_ALWAYS) could not induce constitutional collapse.")
        report.append("")
        report.append("### v3.1 Conclusion")
        report.append("")
        report.append("> **No kernel-external, semantic-free adversary—stateless, stateful, or learning,")
        report.append("> including stochastic mixers—can defeat constitutional survivability under the")
        report.append("> AKI v0.8 contract.**")
    else:
        report.append("**Result**: Positive for architectural stress detection.")

    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Report generated by RSA v3.1 Run 3 script*")

    return "\n".join(report)


# ============================================================================
# Main
# ============================================================================

def compute_config_hash(config: ALSConfigV080) -> str:
    """Compute hash of frozen config."""
    config_dict = {
        "max_cycles": config.max_cycles,
        "renewal_check_interval": config.renewal_check_interval,
        "eligibility_threshold_k": config.eligibility_threshold_k,
        "amnesty_interval": config.amnesty_interval,
        "amnesty_decay": config.amnesty_decay,
        "cta_enabled": config.cta_enabled,
    }
    config_json = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()[:8]


def main():
    print("=" * 80)
    print("RSA v3.1 RUN 3: Model O (STOCHASTIC_MIXER)")
    print("=" * 80)
    print()

    # Create frozen AKI config
    config = ALSConfigV080(
        max_cycles=MAX_CYCLES,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        eligibility_threshold_k=3,
        amnesty_interval=10,
        amnesty_decay=1,
        cta_enabled=True,
    )

    config_hash = compute_config_hash(config)
    expected_hash = "fd58b6e5"

    print(f"AKI Config Hash: {config_hash}")
    if config_hash != expected_hash:
        print(f"  ⚠ WARNING: Config hash mismatch! Expected {expected_hash}")
    else:
        print(f"  ✓ Config hash matches frozen v3.1 protocol")
    print()

    # Load baseline from Run 0
    baseline_path = os.path.join(
        os.path.dirname(__file__), "..", "reports", "rsa_v310_run0_baseline.md"
    )
    if not os.path.exists(baseline_path):
        print(f"ERROR: Baseline file not found: {baseline_path}")
        print("Run rsa_v310_run0_baseline.py first!")
        sys.exit(1)

    print(f"Loading baseline from: {baseline_path}")
    baseline = load_baseline_from_run0(baseline_path)
    if len(baseline) != len(SEEDS):
        print(f"ERROR: Baseline has {len(baseline)} seeds, expected {len(SEEDS)}")
        sys.exit(1)
    print(f"  ✓ Loaded baseline for {len(baseline)} seeds")
    print(f"  Baseline AA mean: {statistics.mean(baseline.values()):.1f} ppm")
    print()

    # Run Model O
    results = run_model_o(SEEDS, config)
    print()

    # Print summary
    print_summary("Run 3 (Model O)", results, baseline)
    print()

    # Print strategy diagnostics
    print_strategy_diagnostics(results)
    print()

    # Print learning diagnostics
    print_learning_diagnostics(results)
    print()

    # Generate report
    report = generate_report(config, config_hash, results, baseline)

    # Write report
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "reports", "rsa_v310_run3_model_o.md"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)

    print("=" * 80)
    print(f"Report written to: {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
