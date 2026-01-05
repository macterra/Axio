#!/usr/bin/env python3
"""
AKI v0.8 Run A: CTA Baseline Recovery Dynamics Under Forced Turnover

This script executes the v0.8 baseline experiment to test whether Constitutional
Temporal Amnesty (CTA) enables constitutional recovery from NULL_AUTHORITY.

Per instructions_v0.8_runnerA.md:
- Single-axis experiment (no parameter sweep)
- CTA enabled with default parameters (AMNESTY_INTERVAL=10, AMNESTY_DECAY=1)
- K=3 (fixed eligibility threshold)
- max_successive_renewals=3 (forced turnover)
- horizon=5,000 cycles
- Seeds: 50, 51, 52, 53, 54
- Pool policy: V060_DEFAULT

Key metrics:
- Recovery count and yield (RY = authority epochs / lapse epochs)
- Stutter recovery detection
- Lapse cause classification (semantic vs structural)
- Amnesty event tracking
"""

import json
import sys
import os
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
# Configuration (Per instructions_v0.8_runnerA.md)
# =============================================================================

SEEDS = [50, 51, 52, 53, 54]
HORIZON = 5000
RENEWAL_CHECK_INTERVAL = 50
MAX_SUCCESSIVE_RENEWALS = 3
ELIGIBILITY_THRESHOLD_K = 3
AMNESTY_INTERVAL = 10
AMNESTY_DECAY = 1
POOL_POLICY = CandidatePoolPolicy.V060_DEFAULT


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
    # Group eligibility events by succession (same cycle)
    succession_cycles = set()
    for event in result.eligibility_events:
        succession_cycles.add(event["cycle"])

    if not succession_cycles:
        return (11.0, 11)  # Default pool size if no succession events

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

    Uses explicit authority_epochs_after from recovery events (fixed telemetry).
    """
    episodes = []

    # Use lapse_events_v080 which has cause classification
    lapse_list = result.lapse_events_v080
    recovery_list = result.recovery_events

    for i, lapse in enumerate(lapse_list):
        lapse_epochs = lapse.get("duration_epochs", 0)
        lapse_cycles = lapse.get("duration_cycles", 0)
        recovered = lapse.get("recovered", False)
        amnesty_during = lapse.get("amnesty_events_during", 0)
        cause = lapse.get("cause", "SEMANTIC")

        # Get matching recovery event if any (recovery events are 1:1 with recovered lapses)
        active_epochs_after = None
        is_stutter = None
        ry = None

        if recovered and i < len(recovery_list):
            recovery = recovery_list[i]
            # Use explicit authority_epochs_after from fixed harness
            active_epochs_after = recovery.get("authority_epochs_after")
            is_stutter = recovery.get("is_stutter")

            # Compute per-episode recovery yield
            if lapse_epochs > 0 and active_epochs_after is not None:
                ry = active_epochs_after / lapse_epochs
            elif lapse_epochs > 0:
                # Fallback if not yet available
                ry = None

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

    # Compute median recovery yield from episodes
    episodes = extract_lapse_episodes(seed, result)
    recovery_yields = [ep.recovery_yield for ep in episodes if ep.recovered]
    median_ry = compute_median(recovery_yields) if recovery_yields else 0.0

    # Count stutter recoveries
    stutter_count = sum(1 for ep in episodes if ep.is_stutter)

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


def main():
    print("=" * 70)
    print("AKI v0.8 Run A: CTA Baseline Recovery Dynamics Under Forced Turnover")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Horizon: {HORIZON} cycles")
    print(f"  K (eligibility threshold): {ELIGIBILITY_THRESHOLD_K}")
    print(f"  max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS}")
    print(f"  AMNESTY_INTERVAL: {AMNESTY_INTERVAL} epochs")
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
              f"Lapses: {summary.lapses}, Recoveries: {summary.recoveries}")

    print()
    print("=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print()

    # Print summary table header
    header = (
        f"{'Seed':>4} | {'Post-Init':>9} | {'Avg|C_E|':>8} | {'Min|C_E|':>8} | "
        f"{'Lapses':>6} | {'NULL_AUTH':>9} | {'Amnesty':>7} | {'Recover':>7} | "
        f"{'Med RY':>6} | {'Stutter':>7} | {'Regime':>20} | {'Terminal':>15}"
    )
    print(header)
    print("-" * len(header))

    for s in all_summaries:
        row = (
            f"{s.seed:>4} | {s.post_init_successions:>9} | {s.avg_c_elig_size:>8.2f} | "
            f"{s.min_c_elig_size:>8} | {s.lapses:>6} | {s.null_auth_cycles:>9} | "
            f"{s.amnesty_events:>7} | {s.recoveries:>7} | {s.median_recovery_yield:>6.2f} | "
            f"{s.stutter_recoveries:>7} | {s.dominant_regime:>20} | {s.terminal_cause:>15}"
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

    print(f"Total lapses across all seeds: {total_lapses}")
    print(f"Total recoveries: {total_recoveries}")
    print(f"Total amnesty events: {total_amnesty}")
    print(f"Total NULL_AUTHORITY cycles: {total_null_auth}")
    print(f"Total stutter recoveries: {total_stutter}")

    if total_recoveries > 0:
        stutter_fraction = total_stutter / total_recoveries
        print(f"Stutter fraction: {stutter_fraction:.1%}")

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
    print("EPISODE TABLE (First 20 episodes)")
    print("=" * 70)
    print()

    if all_episodes:
        ep_header = (
            f"{'Seed':>4} | {'Ep#':>3} | {'Cause':>10} | {'L(epochs)':>9} | "
            f"{'Amnesty':>7} | {'Recovered':>9} | {'A(epochs)':>9} | {'RY':>6} | {'Stutter':>7}"
        )
        print(ep_header)
        print("-" * len(ep_header))

        for ep in all_episodes[:20]:
            row = (
                f"{ep.seed:>4} | {ep.episode_num:>3} | {ep.lapse_cause:>10} | "
                f"{ep.lapse_epochs:>9} | {ep.amnesty_events_during:>7} | "
                f"{'Yes' if ep.recovered else 'No':>9} | {ep.active_epochs_after:>9} | "
                f"{ep.recovery_yield:>6.2f} | {'Yes' if ep.is_stutter else 'No':>7}"
            )
            print(row)

        if len(all_episodes) > 20:
            print(f"... ({len(all_episodes) - 20} more episodes)")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output_data = {
        "experiment": "run_a_v080",
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
            "regime_counts": regime_counts,
        },
    }

    output_file = output_dir / f"run_a_v080_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print()
    print(f"Results saved to: {output_file}")

    return output_data


if __name__ == "__main__":
    main()
