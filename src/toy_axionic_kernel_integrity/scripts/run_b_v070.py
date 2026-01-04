#!/usr/bin/env python3
"""
Run B: AKI v0.7 Forced Succession Eligibility Activation (ALS-G)

Per instructions_v0.7_runnerB.md:
- Tests eligibility filtering under forced turnover conditions
- max_successive_renewals = 3 forces lease expiration after 3 renewals
- K = 3 (spec default eligibility threshold)

Purpose:
Determine whether eligibility-coupled succession produces observable
constitutional effects when post-initial succession events are forced to occur.

Key Questions:
1. Does eligibility gating actively filter successor candidates?
2. Under what conditions does constitutional lapse (NULL_AUTHORITY) occur?
3. How do streaks evolve when succession is frequent?

Configuration:
- B0: max_successive_renewals = 3, K = 3
- Horizon: 100 * renewal_check_interval cycles
- Seeds: 50, 51, 52, 53, 54 (same as Run A)
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
# Configuration Constants (Binding per instructions_v0.7_runnerB.md)
# =============================================================================

# Renewal geometry (unchanged from Run A)
RENEWAL_CHECK_INTERVAL = 50
MSRW_CYCLES = 200
RENEWAL_COST = 5

# Horizon: 100 * renewal_check_interval
HORIZON = 100 * RENEWAL_CHECK_INTERVAL  # = 5000 cycles

# Rent schedule (unchanged from Run A)
RENT_E1 = 10
RENT_E2 = 40
RENT_E3 = 80
RENT_E4 = 160

# Forced turnover (Run B experimental axis)
MAX_SUCCESSIVE_RENEWALS = 3

# Eligibility threshold (spec default)
K = 3

# Seeds (same as Run A for continuity)
SEEDS = [50, 51, 52, 53, 54]


# =============================================================================
# Regime Classification
# =============================================================================

class ConstitutionalRegime(Enum):
    """Constitutional behavior classification per instructions."""
    LATENT = auto()           # Successions occur, eligibility rarely reduces C_ELIG
    FILTERING_ACTIVE = auto() # Eligibility exclusions observed repeatedly
    CONSTITUTIONAL_LAPSE = auto()  # C_ELIG = ∅ occurs, system enters NULL_AUTHORITY


def classify_regime(result: ALSRunResultV070) -> ConstitutionalRegime:
    """Classify run by constitutional behavior."""
    if result.empty_eligible_set_events > 0:
        return ConstitutionalRegime.CONSTITUTIONAL_LAPSE
    if result.eligibility_rejection_count > 5:  # Threshold for "repeated"
        return ConstitutionalRegime.FILTERING_ACTIVE
    return ConstitutionalRegime.LATENT


# =============================================================================
# Run Result Aggregation
# =============================================================================

@dataclass
class SeedResult:
    """Summary for a single seed run."""
    seed: int
    total_cycles: int
    total_successions: int
    post_init_successions: int
    forced_turnovers: int
    mean_residence_epochs: float
    c_pool_size: int
    avg_c_elig_size: float
    eligibility_rejections: int
    lapses: int
    time_in_null_authority: int
    dominant_regime: ConstitutionalRegime
    terminal_cause: str
    max_streak_reached: Dict[str, int] = field(default_factory=dict)
    streak_resets: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "total_cycles": self.total_cycles,
            "total_successions": self.total_successions,
            "post_init_successions": self.post_init_successions,
            "forced_turnovers": self.forced_turnovers,
            "mean_residence_epochs": self.mean_residence_epochs,
            "c_pool_size": self.c_pool_size,
            "avg_c_elig_size": self.avg_c_elig_size,
            "eligibility_rejections": self.eligibility_rejections,
            "lapses": self.lapses,
            "time_in_null_authority": self.time_in_null_authority,
            "dominant_regime": self.dominant_regime.name,
            "terminal_cause": self.terminal_cause,
            "max_streak_reached": self.max_streak_reached,
            "streak_resets": self.streak_resets,
        }


@dataclass
class ExperimentReport:
    """Full experiment report."""
    experiment_id: str
    timestamp: str
    spec_version: str = "0.7"
    horizon: int = HORIZON
    k_value: int = K
    max_successive_renewals: int = MAX_SUCCESSIVE_RENEWALS
    renewal_check_interval: int = RENEWAL_CHECK_INTERVAL
    seeds: List[int] = field(default_factory=list)
    seed_results: List[SeedResult] = field(default_factory=list)
    raw_results: List[Dict[str, Any]] = field(default_factory=list)

    # Aggregates
    total_post_init_successions: int = 0
    total_forced_turnovers: int = 0
    total_eligibility_rejections: int = 0
    total_lapses: int = 0
    regime_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "spec_version": self.spec_version,
            "horizon": self.horizon,
            "k_value": self.k_value,
            "max_successive_renewals": self.max_successive_renewals,
            "renewal_check_interval": self.renewal_check_interval,
            "seeds": self.seeds,
            "seed_results": [r.to_dict() for r in self.seed_results],
            "total_post_init_successions": self.total_post_init_successions,
            "total_forced_turnovers": self.total_forced_turnovers,
            "total_eligibility_rejections": self.total_eligibility_rejections,
            "total_lapses": self.total_lapses,
            "regime_distribution": self.regime_distribution,
            "raw_results": self.raw_results,
        }


# =============================================================================
# Run Functions
# =============================================================================

def create_config_b0() -> ALSConfigV070:
    """Create B0 configuration: forced turnover with K=3."""
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
        eligibility_threshold_k=K,
        candidate_pool_policy=CandidatePoolPolicy.V060_DEFAULT,
        # Run B: forced turnover
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
    )


def run_single(seed: int, config: ALSConfigV070, verbose: bool = False) -> ALSRunResultV070:
    """Run a single v0.7 experiment."""
    harness = ALSHarnessV070(seed=seed, config=config, verbose=verbose)
    return harness.run()


def analyze_result(result: ALSRunResultV070) -> SeedResult:
    """Analyze a single run result."""
    # Compute mean residence in epochs (approximate)
    mean_residence_epochs = 0.0
    if result.mean_residence_cycles > 0:
        mean_residence_epochs = result.mean_residence_cycles / RENEWAL_CHECK_INTERVAL

    # Compute average C_ELIG size at succession
    # From eligibility events, count eligible vs total per succession
    successions_data = {}  # cycle -> (total, eligible)
    for event in result.eligibility_events:
        if isinstance(event, dict):
            cycle = event.get("cycle", 0)
            eligible = event.get("eligible", True)
        else:
            cycle = event.cycle
            eligible = event.eligible

        if cycle not in successions_data:
            successions_data[cycle] = [0, 0]
        successions_data[cycle][0] += 1  # total
        if eligible:
            successions_data[cycle][1] += 1  # eligible

    avg_c_elig = 0.0
    c_pool_size = 0
    if successions_data:
        pools = [d[0] for d in successions_data.values()]
        eligs = [d[1] for d in successions_data.values()]
        c_pool_size = max(pools) if pools else 0
        avg_c_elig = sum(eligs) / len(eligs) if eligs else 0.0

    # Count streak resets (SEM_PASS events)
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

    # Terminal cause
    terminal_cause = result.stop_reason.name if result.stop_reason else "UNKNOWN"

    return SeedResult(
        seed=result.seed,
        total_cycles=result.total_cycles,
        total_successions=result.total_endorsements,
        post_init_successions=result.post_init_successions,
        forced_turnovers=result.forced_turnover_count,
        mean_residence_epochs=mean_residence_epochs,
        c_pool_size=c_pool_size,
        avg_c_elig_size=avg_c_elig,
        eligibility_rejections=result.eligibility_rejection_count,
        lapses=result.empty_eligible_set_events,
        time_in_null_authority=result.total_lapse_duration_cycles,
        dominant_regime=classify_regime(result),
        terminal_cause=terminal_cause,
        max_streak_reached=max_streaks,
        streak_resets=streak_resets,
    )


def print_eligibility_timeline(results: List[ALSRunResultV070]) -> None:
    """Print eligibility activation timeline (required per instructions)."""
    print("\n" + "="*70)
    print("Eligibility Activation Timeline")
    print("="*70)

    for result in results:
        print(f"\nSeed {result.seed}:")
        print(f"  {'Epoch':<8} {'|C_ELIG|':<10} {'|C_POOL|':<10} {'Ratio':<10}")
        print(f"  {'-'*38}")

        # Group by epoch
        epoch_data = {}
        for event in result.eligibility_events:
            if isinstance(event, dict):
                epoch = event.get("epoch", 0)
                eligible = event.get("eligible", True)
            else:
                epoch = event.epoch
                eligible = event.eligible

            if epoch not in epoch_data:
                epoch_data[epoch] = [0, 0]
            epoch_data[epoch][0] += 1  # pool
            if eligible:
                epoch_data[epoch][1] += 1  # elig

        for epoch in sorted(epoch_data.keys())[:20]:  # Show first 20 epochs
            pool, elig = epoch_data[epoch]
            ratio = elig / pool if pool > 0 else 1.0
            bar = "█" * int(ratio * 10) + "░" * (10 - int(ratio * 10))
            print(f"  {epoch:<8} {elig:<10} {pool:<10} {bar} {ratio:.2f}")

        if len(epoch_data) > 20:
            print(f"  ... ({len(epoch_data) - 20} more epochs)")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the full experiment."""
    print("="*70)
    print("AKI v0.7 Experiment: Run B - Forced Succession Eligibility Activation")
    print("="*70)
    print(f"Horizon: {HORIZON} cycles")
    print(f"Seeds: {SEEDS}")
    print(f"K: {K}")
    print(f"max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS}")
    print(f"Expected turnovers per seed: ~{HORIZON // (MAX_SUCCESSIVE_RENEWALS * RENEWAL_CHECK_INTERVAL)}")

    timestamp = datetime.now().isoformat()
    report = ExperimentReport(
        experiment_id=f"run_b_v070_{int(time.time())}",
        timestamp=timestamp,
        seeds=SEEDS,
    )

    config = create_config_b0()
    results: List[ALSRunResultV070] = []

    print(f"\n{'='*60}")
    print(f"Running B0: max_successive_renewals={MAX_SUCCESSIVE_RENEWALS}, K={K}")
    print(f"{'='*60}")

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        start = time.time()
        result = run_single(seed, config, verbose=False)
        elapsed = time.time() - start
        results.append(result)

        # Analyze
        seed_result = analyze_result(result)
        report.seed_results.append(seed_result)

        print(f"done ({result.total_cycles} cycles, "
              f"{result.post_init_successions} post-init successions, "
              f"{result.forced_turnover_count} forced, "
              f"{result.eligibility_rejection_count} rejections, "
              f"{elapsed:.2f}s)")

    # Aggregate
    report.total_post_init_successions = sum(r.post_init_successions for r in report.seed_results)
    report.total_forced_turnovers = sum(r.forced_turnovers for r in report.seed_results)
    report.total_eligibility_rejections = sum(r.eligibility_rejections for r in report.seed_results)
    report.total_lapses = sum(r.lapses for r in report.seed_results)

    regime_counts = Counter(r.dominant_regime.name for r in report.seed_results)
    report.regime_distribution = dict(regime_counts)

    # Store raw results
    report.raw_results = [r.to_dict() for r in results]

    # Print eligibility timeline
    print_eligibility_timeline(results)

    # Save report
    report_path = Path(__file__).parent.parent / "reports" / f"run_b_v070_{int(time.time())}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"Report saved to: {report_path}")
    print(f"{'='*70}")

    # Print summary table (required per instructions)
    print("\n\nSummary Table (Required per instructions):")
    print("-"*120)
    print(f"{'Seed':<6} {'Post-Init':<12} {'Mean Res.':<12} {'Avg |C_ELIG|':<14} "
          f"{'Lapses':<8} {'NULL_AUTH':<12} {'Regime':<20} {'Terminal':<15}")
    print("-"*120)
    for r in report.seed_results:
        print(f"{r.seed:<6} {r.post_init_successions:<12} {r.mean_residence_epochs:<12.2f} "
              f"{r.avg_c_elig_size:<14.2f} {r.lapses:<8} {r.time_in_null_authority:<12} "
              f"{r.dominant_regime.name:<20} {r.terminal_cause:<15}")
    print("-"*120)

    # Print aggregate summary
    print(f"\nAggregate:")
    print(f"  Total post-init successions: {report.total_post_init_successions}")
    print(f"  Total forced turnovers: {report.total_forced_turnovers}")
    print(f"  Total eligibility rejections: {report.total_eligibility_rejections}")
    print(f"  Total lapses: {report.total_lapses}")
    print(f"  Regime distribution: {report.regime_distribution}")

    # Conservative interpretation
    print("\n" + "="*70)
    print("Conservative Interpretation")
    print("="*70)

    filtering_active = report.total_eligibility_rejections > 0
    lapse_occurred = report.total_lapses > 0

    print(f"""
Turnover pressure was applied via max_successive_renewals={MAX_SUCCESSIVE_RENEWALS}.

Eligibility filtering {"ACTIVATED" if filtering_active else "DID NOT ACTIVATE"}:
  - Total eligibility rejections: {report.total_eligibility_rejections}
  - Post-init successions: {report.total_post_init_successions}
  - Forced turnovers: {report.total_forced_turnovers}

Constitutional lapse {"OCCURRED" if lapse_occurred else "DID NOT OCCUR"}:
  - Lapse events: {report.total_lapses}
  - Time in NULL_AUTHORITY: {sum(r.time_in_null_authority for r in report.seed_results)} cycles

What CANNOT be inferred beyond succession-gated selection:
  - Improved competence (not measured)
  - Optimal governance (not defined)
  - Semantic success (not evaluated beyond structural compliance)
  - Alignment properties (out of scope)
""")

    # Validate Run B success criteria
    print("="*70)
    print("Run B Success Criteria")
    print("="*70)

    success = True
    if report.total_post_init_successions < 20 * len(SEEDS):
        print(f"⚠ WARNING: Post-init successions ({report.total_post_init_successions}) < target (100)")
        print(f"  Consider rerunning with longer horizon (H = 300 * renewal_check_interval)")
        success = False
    else:
        print(f"✓ Sufficient post-init successions: {report.total_post_init_successions}")

    if filtering_active:
        print(f"✓ Eligibility exclusions observed: {report.total_eligibility_rejections}")
    else:
        print(f"⚠ No eligibility exclusions observed")

    if lapse_occurred:
        print(f"✓ Constitutional lapse occurred: {report.total_lapses} events")
    else:
        print(f"○ No constitutional lapse (may be expected under moderate turnover)")

    if success:
        print("\n✓ Run B complete and informative.")
    else:
        print("\n⚠ Run B may need parameter adjustment.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
