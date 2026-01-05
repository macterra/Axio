#!/usr/bin/env python3
"""
AKI v0.8 Run B: Amnesty Interval Sensitivity Under Forced Turnover

This script executes the v0.8 Run B experiment to test whether the long-lapse
mode observed in Run A is governed by the CTA clock.

Per instructions_v0.8_runnerB.md:
- Single-axis experiment: AMNESTY_INTERVAL = 5 (vs Run A's 10)
- All other parameters frozen to Run A values
- K=3 (fixed eligibility threshold)
- max_successive_renewals=3 (forced turnover)
- horizon=5,000 cycles
- Seeds: 50, 51, 52, 53, 54
- Pool policy: V060_DEFAULT

Key hypothesis:
- Run A showed long-lapse mode at L ≈ 20 epochs (= 2 × AMNESTY_INTERVAL)
- If CTA clock governs this, Run B should see L ≈ 10 epochs (= 2 × 5)

Key comparisons to Run A:
- Bimodality shift (fraction with L ≤ 2 vs L ≥ 10 vs L ≥ 20)
- Recoveries-without-amnesty fraction
- Median L for long-lapse subset
- Recovery Yield distribution
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.harness import (
    ALSConfigV080,
    ALSRunResultV080,
    ALSHarnessV080,
    CandidatePoolPolicy,
    LapseCause,
)


# =============================================================================
# Configuration (Per instructions_v0.8_runnerB.md)
# =============================================================================

SEEDS = [50, 51, 52, 53, 54]
HORIZON = 5000
RENEWAL_CHECK_INTERVAL = 50
MAX_SUCCESSIVE_RENEWALS = 3
ELIGIBILITY_THRESHOLD_K = 3
AMNESTY_INTERVAL = 5  # CHANGED from Run A's 10
AMNESTY_DECAY = 1
POOL_POLICY = CandidatePoolPolicy.V060_DEFAULT

# Run A baseline values for comparison
RUN_A_AMNESTY_INTERVAL = 10
RUN_A_TOTAL_LAPSES = 13
RUN_A_TOTAL_RECOVERIES = 13
RUN_A_AMNESTY_EVENTS = 8
RUN_A_RECOVERIES_WITHOUT_AMNESTY = 9
RUN_A_LONG_LAPSE_MEDIAN = 20  # Approximate


@dataclass
class LapseEpisode:
    """Record of a single lapse episode."""
    seed: int
    episode_num: int
    lapse_cause: str
    lapse_epochs: int
    lapse_cycles: int
    amnesty_events_during: int
    recovered: bool
    active_epochs_after: int
    recovery_yield: float
    is_stutter: bool
    no_amnesty: bool  # Recovery without any amnesty events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "episode_num": self.episode_num,
            "lapse_cause": self.lapse_cause,
            "lapse_epochs": self.lapse_epochs,
            "lapse_cycles": self.lapse_cycles,
            "amnesty_events_during": self.amnesty_events_during,
            "recovered": self.recovered,
            "active_epochs_after": self.active_epochs_after,
            "recovery_yield": self.recovery_yield,
            "is_stutter": self.is_stutter,
            "no_amnesty": self.no_amnesty,
        }


@dataclass
class SeedSummary:
    """Summary metrics for a single seed."""
    seed: int
    post_init_successions: int
    avg_c_elig_size: float
    min_c_elig_size: int
    lapses: int
    null_auth_cycles: int
    semantic_lapse_cycles: int
    structural_lapse_cycles: int
    amnesty_events: int
    recoveries: int
    recoveries_without_amnesty: int
    median_lapse_epochs: float
    median_authority_epochs: float
    median_recovery_yield: float
    stutter_recoveries: int
    dominant_regime: str
    terminal_cause: str

    # Additional metrics
    mean_lapse_duration_epochs: float
    time_to_first_recovery: Optional[int]
    authority_uptime_fraction: float
    lapse_fraction: float
    total_streak_decay: int
    zombie_cycles: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "post_init_successions": self.post_init_successions,
            "avg_c_elig_size": self.avg_c_elig_size,
            "min_c_elig_size": self.min_c_elig_size,
            "lapses": self.lapses,
            "null_auth_cycles": self.null_auth_cycles,
            "semantic_lapse_cycles": self.semantic_lapse_cycles,
            "structural_lapse_cycles": self.structural_lapse_cycles,
            "amnesty_events": self.amnesty_events,
            "recoveries": self.recoveries,
            "recoveries_without_amnesty": self.recoveries_without_amnesty,
            "median_lapse_epochs": self.median_lapse_epochs,
            "median_authority_epochs": self.median_authority_epochs,
            "median_recovery_yield": self.median_recovery_yield,
            "stutter_recoveries": self.stutter_recoveries,
            "dominant_regime": self.dominant_regime,
            "terminal_cause": self.terminal_cause,
            "mean_lapse_duration_epochs": self.mean_lapse_duration_epochs,
            "time_to_first_recovery": self.time_to_first_recovery,
            "authority_uptime_fraction": self.authority_uptime_fraction,
            "lapse_fraction": self.lapse_fraction,
            "total_streak_decay": self.total_streak_decay,
            "zombie_cycles": self.zombie_cycles,
        }


def classify_regime(result: ALSRunResultV080) -> str:
    """
    Classify seed regime per instructions.

    - NO_LAPSE: no NULL_AUTHORITY entered
    - RECOVERING: lapse occurs and at least one recovery occurs
    - PERMANENT_LAPSE: lapse occurs and no recovery occurs by horizon
    - AMNESTY_DOMINANT: lapse fraction of horizon > 0.80
    """
    if result.semantic_lapse_count + result.structural_lapse_count == 0:
        return "NO_LAPSE"

    if result.lapse_fraction > 0.80:
        return "AMNESTY_DOMINANT"

    if result.recovery_count == 0:
        return "PERMANENT_LAPSE"

    return "RECOVERING"


def classify_oscillation_subtype(result: ALSRunResultV080) -> Optional[str]:
    """
    Classify oscillation subtype if RECOVERING.

    - STUTTER_DOMINANT: stutter fraction of recoveries > 0.50
    """
    if result.recovery_count == 0:
        return None

    stutter_fraction = result.stutter_recovery_count / result.recovery_count
    if stutter_fraction > 0.50:
        return "STUTTER_DOMINANT"

    return None


def compute_c_elig_stats(result: ALSRunResultV080) -> tuple[float, int]:
    """Compute average and minimum C_ELIG size from eligibility events."""
    succession_cycles = set()
    for event in result.eligibility_events:
        succession_cycles.add(event["cycle"])

    if not succession_cycles:
        return (11.0, 11)

    c_elig_sizes = []
    for cycle in succession_cycles:
        eligible_count = sum(
            1 for e in result.eligibility_events
            if e["cycle"] == cycle and e["eligible"]
        )
        c_elig_sizes.append(eligible_count)

    if not c_elig_sizes:
        return (11.0, 11)

    avg = sum(c_elig_sizes) / len(c_elig_sizes)
    min_size = min(c_elig_sizes)
    return (avg, min_size)


def extract_lapse_episodes(seed: int, result: ALSRunResultV080) -> List[LapseEpisode]:
    """
    Extract lapse episodes from result for episode table.

    Uses explicit authority_epochs_after from recovery events.
    """
    episodes = []

    lapse_list = result.lapse_events_v080
    recovery_list = result.recovery_events

    for i, lapse in enumerate(lapse_list):
        lapse_epochs = lapse.get("duration_epochs", 0)
        lapse_cycles = lapse.get("duration_cycles", 0)
        recovered = lapse.get("recovered", False)
        amnesty_during = lapse.get("amnesty_events_during", 0)
        cause = lapse.get("cause", "SEMANTIC")

        active_epochs_after = None
        is_stutter = None
        ry = None

        if recovered and i < len(recovery_list):
            recovery = recovery_list[i]
            active_epochs_after = recovery.get("authority_epochs_after")
            is_stutter = recovery.get("is_stutter")

            if lapse_epochs > 0 and active_epochs_after is not None:
                ry = active_epochs_after / lapse_epochs

        episodes.append(LapseEpisode(
            seed=seed,
            episode_num=i + 1,
            lapse_cause=cause,
            lapse_epochs=lapse_epochs,
            lapse_cycles=lapse_cycles,
            amnesty_events_during=amnesty_during,
            recovered=recovered,
            active_epochs_after=active_epochs_after if active_epochs_after is not None else 0,
            recovery_yield=ry if ry is not None else 0.0,
            is_stutter=is_stutter if is_stutter is not None else False,
            no_amnesty=recovered and amnesty_during == 0,
        ))

    return episodes


def compute_median(values: List[float]) -> float:
    """Compute median of a list."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    return sorted_vals[n // 2]


def run_seed(seed: int, verbose: bool = False) -> tuple[ALSRunResultV080, SeedSummary, List[LapseEpisode]]:
    """Run a single seed and compute summary."""
    config = ALSConfigV080(
        max_cycles=HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
        eligibility_threshold_k=ELIGIBILITY_THRESHOLD_K,
        amnesty_interval=AMNESTY_INTERVAL,
        amnesty_decay=AMNESTY_DECAY,
        candidate_pool_policy=POOL_POLICY,
        cta_enabled=True,
    )

    harness = ALSHarnessV080(seed=seed, config=config, verbose=verbose)
    result = harness.run()

    # Compute C_ELIG stats
    avg_c_elig, min_c_elig = compute_c_elig_stats(result)

    # Classify regime
    regime = classify_regime(result)
    oscillation = classify_oscillation_subtype(result)
    if oscillation:
        regime = f"{regime}:{oscillation}"

    # Compute semantic vs structural lapse cycles
    semantic_cycles = sum(
        e.get("duration_cycles", 0)
        for e in result.lapse_events_v080
        if e.get("cause") == "SEMANTIC"
    )
    structural_cycles = sum(
        e.get("duration_cycles", 0)
        for e in result.lapse_events_v080
        if e.get("cause") == "STRUCTURAL"
    )

    # Mean lapse duration
    lapse_durations = [e.get("duration_epochs", 0) for e in result.lapse_events_v080]
    mean_lapse_duration = sum(lapse_durations) / len(lapse_durations) if lapse_durations else 0.0

    # Compute episode-level metrics
    episodes = extract_lapse_episodes(seed, result)

    # Recovery yields
    recovery_yields = [ep.recovery_yield for ep in episodes if ep.recovered]
    median_ry = compute_median(recovery_yields) if recovery_yields else 0.0

    # Lapse epochs
    lapse_epochs_list = [ep.lapse_epochs for ep in episodes]
    median_lapse = compute_median([float(x) for x in lapse_epochs_list]) if lapse_epochs_list else 0.0

    # Authority epochs
    authority_epochs_list = [ep.active_epochs_after for ep in episodes if ep.recovered]
    median_authority = compute_median([float(x) for x in authority_epochs_list]) if authority_epochs_list else 0.0

    # Count stutter recoveries
    stutter_count = sum(1 for ep in episodes if ep.is_stutter)

    # Count recoveries without amnesty
    no_amnesty_count = sum(1 for ep in episodes if ep.no_amnesty)

    summary = SeedSummary(
        seed=seed,
        post_init_successions=result.post_init_successions,
        avg_c_elig_size=avg_c_elig,
        min_c_elig_size=min_c_elig,
        lapses=result.semantic_lapse_count + result.structural_lapse_count,
        null_auth_cycles=result.total_lapse_duration_cycles,
        semantic_lapse_cycles=semantic_cycles,
        structural_lapse_cycles=structural_cycles,
        amnesty_events=result.amnesty_event_count,
        recoveries=result.recovery_count,
        recoveries_without_amnesty=no_amnesty_count,
        median_lapse_epochs=median_lapse,
        median_authority_epochs=median_authority,
        median_recovery_yield=median_ry,
        stutter_recoveries=stutter_count,
        dominant_regime=regime,
        terminal_cause=result.stop_reason.name if result.stop_reason else "UNKNOWN",
        mean_lapse_duration_epochs=mean_lapse_duration,
        time_to_first_recovery=result.time_to_first_recovery,
        authority_uptime_fraction=result.authority_uptime_fraction,
        lapse_fraction=result.lapse_fraction,
        total_streak_decay=result.total_streak_decay_applied,
        zombie_cycles=result.ineligible_in_office_cycles,
    )

    return result, summary, episodes


def compute_bimodality_metrics(episodes: List[LapseEpisode]) -> Dict[str, Any]:
    """Compute bimodality metrics for comparison with Run A."""
    if not episodes:
        return {
            "fraction_L_le_2": 0.0,
            "fraction_L_ge_10": 0.0,
            "fraction_L_ge_20": 0.0,
            "long_lapse_median": 0.0,
            "short_lapse_count": 0,
            "long_lapse_count": 0,
        }

    total = len(episodes)
    short_lapses = [ep for ep in episodes if ep.lapse_epochs <= 2]
    medium_lapses = [ep for ep in episodes if ep.lapse_epochs >= 10]
    long_lapses = [ep for ep in episodes if ep.lapse_epochs >= 20]

    # Median of "long" lapses (L >= 5 to capture new mode boundary)
    long_for_median = [ep.lapse_epochs for ep in episodes if ep.lapse_epochs >= 5]
    long_median = compute_median([float(x) for x in long_for_median]) if long_for_median else 0.0

    return {
        "fraction_L_le_2": len(short_lapses) / total,
        "fraction_L_ge_10": len(medium_lapses) / total,
        "fraction_L_ge_20": len(long_lapses) / total,
        "long_lapse_median": long_median,
        "short_lapse_count": len(short_lapses),
        "long_lapse_count": len(medium_lapses),
    }


def main():
    print("=" * 70)
    print("AKI v0.8 Run B: Amnesty Interval Sensitivity Under Forced Turnover")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Horizon: {HORIZON} cycles")
    print(f"  K (eligibility threshold): {ELIGIBILITY_THRESHOLD_K}")
    print(f"  max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS}")
    print(f"  AMNESTY_INTERVAL: {AMNESTY_INTERVAL} epochs  <-- CHANGED from Run A's {RUN_A_AMNESTY_INTERVAL}")
    print(f"  AMNESTY_DECAY: {AMNESTY_DECAY}")
    print(f"  Pool policy: {POOL_POLICY.name}")
    print(f"  Seeds: {SEEDS}")
    print()

    all_results = []
    all_summaries = []
    all_episodes = []

    for seed in SEEDS:
        print(f"Running seed {seed}...", end=" ", flush=True)
        result, summary, episodes = run_seed(seed, verbose=False)
        all_results.append(result)
        all_summaries.append(summary)
        all_episodes.extend(episodes)

        print(f"done. Regime: {summary.dominant_regime}, "
              f"Lapses: {summary.lapses}, Recoveries: {summary.recoveries}, "
              f"No-Amnesty: {summary.recoveries_without_amnesty}")

    print()
    print("=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print()

    # Print summary table header
    header = (
        f"{'Seed':>4} | {'Post-Init':>9} | {'Avg|C_E|':>8} | {'Min|C_E|':>8} | "
        f"{'Lapses':>6} | {'NULL_AUTH':>9} | {'Amnesty':>7} | {'Recover':>7} | "
        f"{'NoAmn':>5} | {'Med L':>5} | {'Med A':>5} | {'Med RY':>6} | "
        f"{'Regime':>15} | {'Terminal':>15}"
    )
    print(header)
    print("-" * len(header))

    for s in all_summaries:
        row = (
            f"{s.seed:>4} | {s.post_init_successions:>9} | {s.avg_c_elig_size:>8.2f} | "
            f"{s.min_c_elig_size:>8} | {s.lapses:>6} | {s.null_auth_cycles:>9} | "
            f"{s.amnesty_events:>7} | {s.recoveries:>7} | "
            f"{s.recoveries_without_amnesty:>5} | {s.median_lapse_epochs:>5.1f} | "
            f"{s.median_authority_epochs:>5.1f} | {s.median_recovery_yield:>6.2f} | "
            f"{s.dominant_regime:>15} | {s.terminal_cause:>15}"
        )
        print(row)

    print()
    print("=" * 70)
    print("AGGREGATE METRICS")
    print("=" * 70)
    print()

    total_lapses = sum(s.lapses for s in all_summaries)
    total_recoveries = sum(s.recoveries for s in all_summaries)
    total_amnesty = sum(s.amnesty_events for s in all_summaries)
    total_null_auth = sum(s.null_auth_cycles for s in all_summaries)
    total_stutter = sum(s.stutter_recoveries for s in all_summaries)
    total_no_amnesty = sum(s.recoveries_without_amnesty for s in all_summaries)

    print(f"Total lapses across all seeds: {total_lapses}")
    print(f"Total recoveries: {total_recoveries}")
    print(f"Total amnesty events: {total_amnesty}")
    print(f"Total NULL_AUTHORITY cycles: {total_null_auth}")
    print(f"Total stutter recoveries: {total_stutter}")
    print(f"Recoveries without amnesty: {total_no_amnesty}")

    if total_recoveries > 0:
        stutter_fraction = total_stutter / total_recoveries
        no_amnesty_fraction = total_no_amnesty / total_recoveries
        with_amnesty_fraction = 1.0 - no_amnesty_fraction
        print(f"Stutter fraction: {stutter_fraction:.1%}")
        print(f"Recoveries without amnesty: {no_amnesty_fraction:.1%}")
        print(f"Recoveries with amnesty: {with_amnesty_fraction:.1%}")

    # Regime distribution
    regime_counts = {}
    for s in all_summaries:
        base_regime = s.dominant_regime.split(":")[0]
        regime_counts[base_regime] = regime_counts.get(base_regime, 0) + 1

    print()
    print("Regime distribution:")
    for regime, count in sorted(regime_counts.items()):
        print(f"  {regime}: {count}/5 seeds")

    print()
    print("=" * 70)
    print("BIMODALITY ANALYSIS (vs Run A)")
    print("=" * 70)
    print()

    bimodality = compute_bimodality_metrics(all_episodes)

    print(f"Fraction of lapses with L <= 2:  {bimodality['fraction_L_le_2']:.1%}  (Run A: 69%)")
    print(f"Fraction of lapses with L >= 10: {bimodality['fraction_L_ge_10']:.1%}  (Run A: 31%)")
    print(f"Fraction of lapses with L >= 20: {bimodality['fraction_L_ge_20']:.1%}  (Run A: 31%)")
    print(f"Median L for long lapses (L>=5): {bimodality['long_lapse_median']:.1f}  (Run A: ~20)")
    print()
    print("Interpretation:")
    if bimodality['fraction_L_ge_20'] < 0.10:
        print("  -> Long-lapse mode (L~20) has COMPRESSED or COLLAPSED")
    elif bimodality['long_lapse_median'] < 15:
        print("  -> Long-lapse mode has SHIFTED downward")
    else:
        print("  -> Long-lapse mode appears UNCHANGED")

    print()
    print("=" * 70)
    print("EPISODE TABLE (All episodes)")
    print("=" * 70)
    print()

    if all_episodes:
        ep_header = (
            f"{'Seed':>4} | {'Ep#':>3} | {'Cause':>10} | {'L(epochs)':>9} | "
            f"{'Amnesty':>7} | {'Recovered':>9} | {'A(epochs)':>9} | {'RY':>6} | "
            f"{'Stutter':>7} | {'NoAmn':>5}"
        )
        print(ep_header)
        print("-" * len(ep_header))

        for ep in all_episodes:
            row = (
                f"{ep.seed:>4} | {ep.episode_num:>3} | {ep.lapse_cause:>10} | "
                f"{ep.lapse_epochs:>9} | {ep.amnesty_events_during:>7} | "
                f"{'Yes' if ep.recovered else 'No':>9} | {ep.active_epochs_after:>9} | "
                f"{ep.recovery_yield:>6.2f} | {'Yes' if ep.is_stutter else 'No':>7} | "
                f"{'Yes' if ep.no_amnesty else 'No':>5}"
            )
            print(row)

    print()
    print("=" * 70)
    print("COMPARISON TO RUN A")
    print("=" * 70)
    print()

    print(f"{'Metric':<35} | {'Run A':>10} | {'Run B':>10} | {'Delta':>10}")
    print("-" * 70)
    print(f"{'AMNESTY_INTERVAL':<35} | {RUN_A_AMNESTY_INTERVAL:>10} | {AMNESTY_INTERVAL:>10} | {'CHANGED':>10}")
    print(f"{'Total lapses':<35} | {RUN_A_TOTAL_LAPSES:>10} | {total_lapses:>10} | {total_lapses - RUN_A_TOTAL_LAPSES:>+10}")
    print(f"{'Total recoveries':<35} | {RUN_A_TOTAL_RECOVERIES:>10} | {total_recoveries:>10} | {total_recoveries - RUN_A_TOTAL_RECOVERIES:>+10}")
    print(f"{'Total amnesty events':<35} | {RUN_A_AMNESTY_EVENTS:>10} | {total_amnesty:>10} | {total_amnesty - RUN_A_AMNESTY_EVENTS:>+10}")
    print(f"{'Recoveries without amnesty':<35} | {RUN_A_RECOVERIES_WITHOUT_AMNESTY:>10} | {total_no_amnesty:>10} | {total_no_amnesty - RUN_A_RECOVERIES_WITHOUT_AMNESTY:>+10}")

    if total_recoveries > 0:
        run_a_no_amnesty_pct = RUN_A_RECOVERIES_WITHOUT_AMNESTY / RUN_A_TOTAL_RECOVERIES * 100
        run_b_no_amnesty_pct = total_no_amnesty / total_recoveries * 100
        print(f"{'No-amnesty recovery %':<35} | {run_a_no_amnesty_pct:>9.0f}% | {run_b_no_amnesty_pct:>9.0f}% | {run_b_no_amnesty_pct - run_a_no_amnesty_pct:>+9.0f}%")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output_data = {
        "experiment": "run_b_v080",
        "timestamp": timestamp,
        "config": {
            "horizon": HORIZON,
            "eligibility_threshold_k": ELIGIBILITY_THRESHOLD_K,
            "max_successive_renewals": MAX_SUCCESSIVE_RENEWALS,
            "amnesty_interval": AMNESTY_INTERVAL,
            "amnesty_decay": AMNESTY_DECAY,
            "pool_policy": POOL_POLICY.name,
            "seeds": SEEDS,
        },
        "summaries": [s.to_dict() for s in all_summaries],
        "episodes": [ep.to_dict() for ep in all_episodes],
        "aggregate": {
            "total_lapses": total_lapses,
            "total_recoveries": total_recoveries,
            "total_amnesty_events": total_amnesty,
            "total_null_auth_cycles": total_null_auth,
            "total_stutter_recoveries": total_stutter,
            "total_recoveries_without_amnesty": total_no_amnesty,
            "regime_counts": regime_counts,
        },
        "bimodality": bimodality,
        "run_a_comparison": {
            "run_a_amnesty_interval": RUN_A_AMNESTY_INTERVAL,
            "run_a_total_lapses": RUN_A_TOTAL_LAPSES,
            "run_a_total_recoveries": RUN_A_TOTAL_RECOVERIES,
            "run_a_amnesty_events": RUN_A_AMNESTY_EVENTS,
            "run_a_recoveries_without_amnesty": RUN_A_RECOVERIES_WITHOUT_AMNESTY,
        },
    }

    output_file = output_dir / f"run_b_v080_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print()
    print(f"Results saved to: {output_file}")

    return output_data


if __name__ == "__main__":
    main()
