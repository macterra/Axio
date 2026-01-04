#!/usr/bin/env python3
"""
Run C: AKI v0.7 Eligibility Threshold Sweep Under Forced Turnover (ALS-G)

Per instructions_v0.7_runnerC.md:
- Tests how eligibility threshold K controls constitutional outcomes
- Fixed forced-turnover geometry (max_successive_renewals = 3)
- All other parameters identical to Run B

Purpose:
Quantify how K controls eligibility contraction, lapse frequency, and
time spent in NULL_AUTHORITY under fixed turnover pressure.

Sub-runs:
- C1: K=1 (knife-edge, maximum strictness)
- C2: K=3 (baseline, must replicate Run B)
- C3: K=5 (forgiving)
- C4: K=10 (very forgiving)
"""

import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import Counter
from enum import Enum, auto

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.generator import (
    GeneratorConfig,
    AttackSuccessorType,
    ControlSuccessorType,
)
from toy_aki.als.harness import (
    ALSHarnessV070,
    ALSConfigV070,
    ALSRunResultV070,
    ALSStopReason,
    CandidatePoolPolicy,
)


# =============================================================================
# Configuration Constants (Binding per instructions_v0.7_runnerC.md)
# =============================================================================

# Renewal geometry (identical to Run B)
RENEWAL_CHECK_INTERVAL = 50
MSRW_CYCLES = 200
RENEWAL_COST = 5

# Horizon (identical to Run B for comparability)
HORIZON = 5000

# Rent schedule (unchanged from Run B)
RENT_E1 = 10
RENT_E2 = 40
RENT_E3 = 80
RENT_E4 = 160

# Forced turnover (identical to Run B)
MAX_SUCCESSIVE_RENEWALS = 3

# K values for sweep
K_VALUES = {
    "C1": 1,   # Knife-edge
    "C2": 3,   # Baseline (Run B replication)
    "C3": 5,   # Forgiving
    "C4": 10,  # Very forgiving
}

# Seeds (same as Run A and Run B)
SEEDS = [50, 51, 52, 53, 54]


# =============================================================================
# Regime Classification
# =============================================================================

class ConstitutionalRegime(Enum):
    """Constitutional behavior classification per instructions."""
    LATENT = auto()           # Eligibility rarely reduces C_ELIG, no lapse
    FILTERING_ACTIVE = auto() # Eligibility reductions frequent, no/rare lapse
    CONSTITUTIONAL_LAPSE = auto()  # C_ELIG = ∅ occurs, NULL_AUTHORITY entered


def classify_regime(result: ALSRunResultV070) -> ConstitutionalRegime:
    """Classify run by constitutional behavior."""
    if result.empty_eligible_set_events > 0:
        return ConstitutionalRegime.CONSTITUTIONAL_LAPSE
    if result.eligibility_rejection_count > 5:  # Threshold for "frequent"
        return ConstitutionalRegime.FILTERING_ACTIVE
    return ConstitutionalRegime.LATENT


# =============================================================================
# Run Result Structures
# =============================================================================

@dataclass
class SeedResult:
    """Summary for a single (K, seed) run."""
    k_value: int
    seed: int
    total_cycles: int
    total_successions: int
    post_init_successions: int
    forced_turnovers: int
    mean_residence_epochs: float
    avg_c_elig_size: float
    min_c_elig_size: int
    time_to_first_empty: Optional[int]  # Epoch index, or None
    lapses: int
    time_in_null_authority: int
    dominant_regime: ConstitutionalRegime
    terminal_cause: str
    max_streak_by_policy: Dict[str, int] = field(default_factory=dict)
    streak_resets: int = 0
    sawtooth_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k_value": self.k_value,
            "seed": self.seed,
            "total_cycles": self.total_cycles,
            "total_successions": self.total_successions,
            "post_init_successions": self.post_init_successions,
            "forced_turnovers": self.forced_turnovers,
            "mean_residence_epochs": self.mean_residence_epochs,
            "avg_c_elig_size": self.avg_c_elig_size,
            "min_c_elig_size": self.min_c_elig_size,
            "time_to_first_empty": self.time_to_first_empty,
            "lapses": self.lapses,
            "time_in_null_authority": self.time_in_null_authority,
            "dominant_regime": self.dominant_regime.name,
            "terminal_cause": self.terminal_cause,
            "max_streak_by_policy": self.max_streak_by_policy,
            "streak_resets": self.streak_resets,
            "sawtooth_count": self.sawtooth_count,
        }


@dataclass
class SubRunSummary:
    """Summary for a sub-run (all seeds at one K)."""
    sub_run_id: str
    k_value: int
    total_runs: int
    total_post_init_successions: int
    total_lapses: int
    total_time_in_null_authority: int
    avg_time_to_first_empty: Optional[float]
    regime_distribution: Dict[str, int] = field(default_factory=dict)
    seed_results: List[SeedResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub_run_id": self.sub_run_id,
            "k_value": self.k_value,
            "total_runs": self.total_runs,
            "total_post_init_successions": self.total_post_init_successions,
            "total_lapses": self.total_lapses,
            "total_time_in_null_authority": self.total_time_in_null_authority,
            "avg_time_to_first_empty": self.avg_time_to_first_empty,
            "regime_distribution": self.regime_distribution,
            "seed_results": [r.to_dict() for r in self.seed_results],
        }


@dataclass
class ExperimentReport:
    """Full experiment report."""
    experiment_id: str
    timestamp: str
    spec_version: str = "0.7"
    horizon: int = HORIZON
    max_successive_renewals: int = MAX_SUCCESSIVE_RENEWALS
    renewal_check_interval: int = RENEWAL_CHECK_INTERVAL
    k_values: Dict[str, int] = field(default_factory=dict)
    seeds: List[int] = field(default_factory=list)
    sub_runs: List[SubRunSummary] = field(default_factory=list)
    raw_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "spec_version": self.spec_version,
            "horizon": self.horizon,
            "max_successive_renewals": self.max_successive_renewals,
            "renewal_check_interval": self.renewal_check_interval,
            "k_values": self.k_values,
            "seeds": self.seeds,
            "sub_runs": [s.to_dict() for s in self.sub_runs],
            "raw_results": self.raw_results,
        }


# =============================================================================
# Run Functions
# =============================================================================

def create_config(k_value: int) -> ALSConfigV070:
    """Create config with specified K value."""
    return ALSConfigV070(
        max_cycles=HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        renewal_cost_steps=RENEWAL_COST,
        rent_e1=RENT_E1,
        rent_e2=RENT_E2,
        rent_e3=RENT_E3,
        rent_e4=RENT_E4,
        # v0.7 specific
        eligibility_threshold_k=k_value,
        candidate_pool_policy=CandidatePoolPolicy.V060_DEFAULT,
        # Run B/C: forced turnover
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
    )


def run_single(seed: int, config: ALSConfigV070, verbose: bool = False) -> ALSRunResultV070:
    """Run a single v0.7 experiment."""
    harness = ALSHarnessV070(seed=seed, config=config, verbose=verbose)
    return harness.run()


def analyze_result(result: ALSRunResultV070, k_value: int) -> SeedResult:
    """Analyze a single run result."""
    # Compute mean residence in epochs
    mean_residence_epochs = 0.0
    if result.mean_residence_cycles > 0:
        mean_residence_epochs = result.mean_residence_cycles / RENEWAL_CHECK_INTERVAL

    # Compute C_ELIG statistics per succession
    succession_elig: List[int] = []
    min_c_elig = 11  # Pool size
    time_to_first_empty: Optional[int] = None

    epoch_elig_counts: Dict[int, List[int]] = {}
    for event in result.eligibility_events:
        if isinstance(event, dict):
            epoch = event.get("epoch", 0)
            eligible = event.get("eligible", True)
        else:
            epoch = event.epoch
            eligible = event.eligible

        if epoch not in epoch_elig_counts:
            epoch_elig_counts[epoch] = [0, 0]  # [total, eligible]
        epoch_elig_counts[epoch][0] += 1
        if eligible:
            epoch_elig_counts[epoch][1] += 1

    # Find min C_ELIG and time-to-first-empty
    for epoch in sorted(epoch_elig_counts.keys()):
        total, elig = epoch_elig_counts[epoch]
        # Approximate per-succession C_ELIG (normalize by expected pool size)
        if total > 0:
            # Each succession evaluates ~11 candidates
            approx_elig = min(elig, 11)
            succession_elig.append(approx_elig)
            min_c_elig = min(min_c_elig, approx_elig)
            if elig == 0 and time_to_first_empty is None:
                time_to_first_empty = epoch

    avg_c_elig = sum(succession_elig) / len(succession_elig) if succession_elig else 11.0

    # Count streak resets and max streaks
    streak_resets = 0
    max_streaks: Dict[str, int] = {}
    for record in result.semantic_epoch_records:
        if isinstance(record, dict):
            policy_id = record.get("active_policy_id", "unknown")
            streak_after = record.get("streak_after", 0)
            sem_pass = record.get("sem_pass", False)
        else:
            policy_id = record.active_policy_id or "unknown"
            streak_after = record.streak_after
            sem_pass = record.sem_pass

        if policy_id not in max_streaks:
            max_streaks[policy_id] = 0
        max_streaks[policy_id] = max(max_streaks[policy_id], streak_after)

        if sem_pass:
            streak_resets += 1

    terminal_cause = result.stop_reason.name if result.stop_reason else "UNKNOWN"

    return SeedResult(
        k_value=k_value,
        seed=result.seed,
        total_cycles=result.total_cycles,
        total_successions=result.total_endorsements,
        post_init_successions=result.post_init_successions,
        forced_turnovers=result.forced_turnover_count,
        mean_residence_epochs=mean_residence_epochs,
        avg_c_elig_size=avg_c_elig,
        min_c_elig_size=min_c_elig,
        time_to_first_empty=time_to_first_empty,
        lapses=result.empty_eligible_set_events,
        time_in_null_authority=result.total_lapse_duration_cycles,
        dominant_regime=classify_regime(result),
        terminal_cause=terminal_cause,
        max_streak_by_policy=max_streaks,
        streak_resets=streak_resets,
        sawtooth_count=result.sawtooth_count,
    )


def run_sub_run(sub_run_id: str, k_value: int, seeds: List[int]) -> SubRunSummary:
    """Run all seeds for a sub-run configuration."""
    print(f"\n{'='*60}")
    print(f"Sub-Run {sub_run_id}: K={k_value}")
    print(f"{'='*60}")

    config = create_config(k_value)
    seed_results: List[SeedResult] = []

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        start = time.time()
        result = run_single(seed, config, verbose=False)
        elapsed = time.time() - start

        seed_result = analyze_result(result, k_value)
        seed_results.append(seed_result)

        print(f"done ({result.total_cycles} cycles, "
              f"{result.post_init_successions} post-init, "
              f"{result.empty_eligible_set_events} lapses, "
              f"{elapsed:.2f}s)")

    # Aggregate
    total_post_init = sum(r.post_init_successions for r in seed_results)
    total_lapses = sum(r.lapses for r in seed_results)
    total_null_auth = sum(r.time_in_null_authority for r in seed_results)

    # Time-to-first-empty average (exclude None)
    first_empties = [r.time_to_first_empty for r in seed_results if r.time_to_first_empty is not None]
    avg_first_empty = sum(first_empties) / len(first_empties) if first_empties else None

    regime_counts = Counter(r.dominant_regime.name for r in seed_results)

    summary = SubRunSummary(
        sub_run_id=sub_run_id,
        k_value=k_value,
        total_runs=len(seed_results),
        total_post_init_successions=total_post_init,
        total_lapses=total_lapses,
        total_time_in_null_authority=total_null_auth,
        avg_time_to_first_empty=avg_first_empty,
        regime_distribution=dict(regime_counts),
        seed_results=seed_results,
    )

    print(f"\n  Summary K={k_value}:")
    print(f"    Post-init successions: {total_post_init}")
    print(f"    Lapses: {total_lapses}")
    print(f"    Time in NULL_AUTHORITY: {total_null_auth} cycles")
    print(f"    Avg time-to-first-empty: {avg_first_empty}")
    print(f"    Regime distribution: {dict(regime_counts)}")

    return summary


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the full experiment."""
    print("="*70)
    print("AKI v0.7 Experiment: Run C - Eligibility Threshold Sweep")
    print("="*70)
    print(f"Horizon: {HORIZON} cycles")
    print(f"Seeds: {SEEDS}")
    print(f"K values: {K_VALUES}")
    print(f"max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS} (forced turnover)")

    timestamp = datetime.now().isoformat()
    report = ExperimentReport(
        experiment_id=f"run_c_v070_{int(time.time())}",
        timestamp=timestamp,
        k_values=K_VALUES,
        seeds=SEEDS,
    )

    all_results: List[ALSRunResultV070] = []

    for sub_run_id, k_value in K_VALUES.items():
        summary = run_sub_run(sub_run_id, k_value, SEEDS)
        report.sub_runs.append(summary)

    # Save report
    report_path = Path(__file__).parent.parent / "reports" / f"run_c_v070_{int(time.time())}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"Report saved to: {report_path}")
    print(f"{'='*70}")

    # ==========================================================================
    # Required Reporting
    # ==========================================================================

    # Summary Table (all K, seed combinations)
    print("\n\nSummary Table (Required per instructions):")
    print("-"*140)
    print(f"{'K':<4} {'Seed':<6} {'Post-Init':<10} {'Avg|C_ELIG|':<12} {'Min|C_ELIG|':<12} "
          f"{'1st Empty':<12} {'Lapses':<8} {'NULL_AUTH':<12} {'Regime':<22} {'Terminal':<15}")
    print("-"*140)
    for sub in report.sub_runs:
        for r in sub.seed_results:
            first_empty_str = str(r.time_to_first_empty) if r.time_to_first_empty is not None else "N/A"
            print(f"{r.k_value:<4} {r.seed:<6} {r.post_init_successions:<10} {r.avg_c_elig_size:<12.2f} "
                  f"{r.min_c_elig_size:<12} {first_empty_str:<12} {r.lapses:<8} "
                  f"{r.time_in_null_authority:<12} {r.dominant_regime.name:<22} {r.terminal_cause:<15}")
    print("-"*140)

    # Phase-Line View
    print("\n\nPhase-Line View (K → Regime Distribution):")
    print("-"*60)
    print(f"{'K':<6} {'LATENT':<12} {'FILTERING_ACTIVE':<20} {'CONSTITUTIONAL_LAPSE':<22}")
    print("-"*60)
    for sub in report.sub_runs:
        latent = sub.regime_distribution.get("LATENT", 0)
        filtering = sub.regime_distribution.get("FILTERING_ACTIVE", 0)
        lapse = sub.regime_distribution.get("CONSTITUTIONAL_LAPSE", 0)
        print(f"{sub.k_value:<6} {latent}/5{'':<8} {filtering}/5{'':<16} {lapse}/5")
    print("-"*60)

    # Conservative Interpretation per K
    print("\n" + "="*70)
    print("Conservative Interpretation (per K)")
    print("="*70)

    for sub in report.sub_runs:
        k = sub.k_value
        lapses = sub.total_lapses
        null_auth = sub.total_time_in_null_authority
        regime_dist = sub.regime_distribution
        lapse_seeds = regime_dist.get("CONSTITUTIONAL_LAPSE", 0)
        filtering_seeds = regime_dist.get("FILTERING_ACTIVE", 0)
        latent_seeds = regime_dist.get("LATENT", 0)

        print(f"\n### K = {k} ({sub.sub_run_id})")
        print(f"  Eligibility filtering: {'ACTIVATED' if lapses > 0 or filtering_seeds > 0 else 'LATENT'}")
        print(f"  Constitutional lapse: {'OCCURRED' if lapses > 0 else 'DID NOT OCCUR'} ({lapses} events across {lapse_seeds} seeds)")
        print(f"  Time in NULL_AUTHORITY: {null_auth} cycles")
        print(f"  Regime distribution: LATENT={latent_seeds}/5, FILTERING_ACTIVE={filtering_seeds}/5, CONSTITUTIONAL_LAPSE={lapse_seeds}/5")
        print(f"  What CANNOT be inferred: competence, governance quality, alignment properties, generality beyond tested geometry")

    # Run B replication check (C2 should match Run B)
    print("\n" + "="*70)
    print("Run B Replication Check (C2 vs Run B)")
    print("="*70)
    c2_summary = next((s for s in report.sub_runs if s.k_value == 3), None)
    if c2_summary:
        # Run B had: 88 post-init, 11 lapses, 344 cycles in NULL_AUTH
        print(f"  C2 post-init successions: {c2_summary.total_post_init_successions} (Run B: 88)")
        print(f"  C2 lapses: {c2_summary.total_lapses} (Run B: 11)")
        print(f"  C2 time in NULL_AUTHORITY: {c2_summary.total_time_in_null_authority} (Run B: 344)")
        if c2_summary.total_lapses > 0:
            print("  ✓ C2 reproduces Run B constitutional lapse behavior")
        else:
            print("  ⚠ C2 does NOT reproduce Run B lapse behavior - investigate")

    # K-dependent observations
    print("\n" + "="*70)
    print("K-Dependent Observations")
    print("="*70)

    lapse_by_k = {s.k_value: s.total_lapses for s in report.sub_runs}
    null_auth_by_k = {s.k_value: s.total_time_in_null_authority for s in report.sub_runs}

    print(f"\n  Lapse count by K: {lapse_by_k}")
    print(f"  NULL_AUTHORITY time by K: {null_auth_by_k}")

    # Check for non-lapse region at higher K
    if lapse_by_k.get(10, 0) == 0:
        print("\n  ✓ Non-lapse constitutional band emerged at K=10")
    elif lapse_by_k.get(5, 0) == 0:
        print("\n  ✓ Non-lapse constitutional band emerged at K=5")
    else:
        print("\n  ○ Constitutional lapse occurred at all tested K values")

    print("\n✓ Run C complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
