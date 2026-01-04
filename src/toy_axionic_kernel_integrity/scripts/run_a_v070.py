#!/usr/bin/env python3
"""
Run A: AKI v0.7 Eligibility-Coupled Succession Baseline (ALS-G)

Per spec §6 (ALS-G: Authority Leases with Eligibility Gating):
- Tests eligibility filtering based on semantic_fail_streak
- Validates K=3 threshold for candidate exclusion
- Measures lapse frequency and C_ELIG dynamics

Purpose:
Establish baseline behavior for the eligibility gating mechanism and verify
that candidates with persistent semantic failure are excluded from succession.

Key Invariants to Validate:
1. Streak tracked per stable policy_id (not instance)
2. C_ELIG = { c ∈ C_POOL | streak[c.policy_id] < K }
3. Empty C_ELIG triggers NULL_AUTHORITY lapse
4. No streak updates during lapse
5. Streak resets to 0 on semantic success

Sub-runs:
- G0: Default K=3 (baseline)
- G1: K=1 (aggressive filtering, more lapses expected)
- G2: K=5 (lenient filtering, fewer lapses expected)
- G3: K=10 (very lenient, minimal filtering)
"""

import sys
import json
import time
import math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from collections import Counter

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
# Configuration Constants (Binding)
# =============================================================================

HORIZON = 5_000  # 5K cycles for baseline
EPOCH_SIZE = 100

# Caps
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Geometry
RENEWAL_CHECK_INTERVAL = 50
MSRW_CYCLES = 200
RENEWAL_COST = 5

# Rent fractions by tier
RENT_E1 = 10   # 5%
RENT_E2 = 40   # 20%
RENT_E3 = 80   # 40%
RENT_E4 = 160  # 80%

# Eligibility threshold values to test
K_VALUES = {
    "G0": 3,   # Default K per spec
    "G1": 1,   # Aggressive
    "G2": 5,   # Lenient
    "G3": 10,  # Very lenient
}

# Generator weights
CONTROL_WEIGHT = 0.20

# Seeds
SEEDS = [50, 51, 52, 53, 54]


# =============================================================================
# Run Result Aggregation
# =============================================================================

@dataclass
class SubRunSummary:
    """Summary statistics for a sub-run."""
    sub_run_id: str
    k_value: int
    total_runs: int
    total_cycles: int
    total_successions: int
    total_lapse_count: int
    total_lapse_cycles: int
    avg_lapse_cycles_per_run: float
    lapse_rate: float  # lapses per 1000 cycles
    eligibility_exclusion_count: int
    policies_ever_excluded: Set[str] = field(default_factory=set)
    final_streak_summary: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub_run_id": self.sub_run_id,
            "k_value": self.k_value,
            "total_runs": self.total_runs,
            "total_cycles": self.total_cycles,
            "total_successions": self.total_successions,
            "total_lapse_count": self.total_lapse_count,
            "total_lapse_cycles": self.total_lapse_cycles,
            "avg_lapse_cycles_per_run": self.avg_lapse_cycles_per_run,
            "lapse_rate": self.lapse_rate,
            "eligibility_exclusion_count": self.eligibility_exclusion_count,
            "policies_ever_excluded": list(self.policies_ever_excluded),
            "final_streak_summary": self.final_streak_summary,
        }


@dataclass
class ExperimentReport:
    """Full experiment report."""
    experiment_id: str
    timestamp: str
    spec_version: str = "0.7"
    horizon: int = HORIZON
    seeds: List[int] = field(default_factory=list)
    sub_runs: List[SubRunSummary] = field(default_factory=list)
    raw_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "spec_version": self.spec_version,
            "horizon": self.horizon,
            "seeds": self.seeds,
            "sub_runs": [s.to_dict() for s in self.sub_runs],
            "raw_results": self.raw_results,
        }


# =============================================================================
# Run Functions
# =============================================================================

def create_config_v070(k_value: int) -> ALSConfigV070:
    """Create v0.7 config with specified K value."""
    return ALSConfigV070(
        max_cycles=HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        renewal_cost_steps=RENEWAL_COST,
        rent_e1=RENT_E1,
        rent_e2=RENT_E2,
        rent_e3=RENT_E3,
        rent_e4=RENT_E4,
        # V0.7 specific
        eligibility_threshold_k=k_value,
        candidate_pool_policy=CandidatePoolPolicy.V060_DEFAULT,
    )


def run_single(seed: int, config: ALSConfigV070, verbose: bool = False) -> ALSRunResultV070:
    """Run a single v0.7 experiment."""
    harness = ALSHarnessV070(seed=seed, config=config, verbose=verbose)
    return harness.run()


def run_sub_run(sub_run_id: str, k_value: int, seeds: List[int]) -> Tuple[SubRunSummary, List[ALSRunResultV070]]:
    """Run all seeds for a sub-run configuration."""
    print(f"\n{'='*60}")
    print(f"Sub-Run {sub_run_id}: K={k_value}")
    print(f"{'='*60}")

    config = create_config_v070(k_value)
    results: List[ALSRunResultV070] = []

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        start = time.time()
        result = run_single(seed, config, verbose=False)
        elapsed = time.time() - start
        results.append(result)
        print(f"done ({result.total_cycles} cycles, {elapsed:.2f}s)")

    # Aggregate statistics
    total_cycles = sum(r.total_cycles for r in results)
    total_successions = sum(len(r.succession_events) for r in results)
    total_lapse_count = sum(r.empty_eligible_set_events for r in results)
    total_lapse_cycles = sum(r.total_lapse_duration_cycles for r in results)
    eligibility_exclusion_count = sum(r.eligibility_rejection_count for r in results)

    # Collect all excluded policies
    policies_excluded: Set[str] = set()
    for r in results:
        for e in r.eligibility_events:
            # Handle both EligibilityEvent objects and dicts
            if isinstance(e, dict):
                if not e.get("eligible", True):
                    policies_excluded.add(e.get("candidate_policy_id", "unknown"))
            else:
                if not e.eligible:
                    policies_excluded.add(e.candidate_policy_id)

    # Average final streaks
    streak_sums: Dict[str, List[int]] = {}
    for r in results:
        for policy_id, streak in r.final_streak_by_policy.items():
            if policy_id not in streak_sums:
                streak_sums[policy_id] = []
            streak_sums[policy_id].append(streak)

    final_streak_summary = {
        pid: sum(streaks) / len(streaks) for pid, streaks in streak_sums.items()
    }

    lapse_rate = (total_lapse_count / total_cycles * 1000) if total_cycles > 0 else 0.0
    avg_lapse_cycles = total_lapse_cycles / len(results) if results else 0.0

    summary = SubRunSummary(
        sub_run_id=sub_run_id,
        k_value=k_value,
        total_runs=len(results),
        total_cycles=total_cycles,
        total_successions=total_successions,
        total_lapse_count=total_lapse_count,
        total_lapse_cycles=total_lapse_cycles,
        avg_lapse_cycles_per_run=avg_lapse_cycles,
        lapse_rate=lapse_rate,
        eligibility_exclusion_count=eligibility_exclusion_count,
        policies_ever_excluded=policies_excluded,
        final_streak_summary=final_streak_summary,
    )

    print(f"\n  Summary:")
    print(f"    Total cycles: {total_cycles}")
    print(f"    Successions: {total_successions}")
    print(f"    Lapses: {total_lapse_count} ({lapse_rate:.2f} per 1000 cycles)")
    print(f"    Lapse cycles: {total_lapse_cycles} ({avg_lapse_cycles:.1f} avg per run)")
    print(f"    Eligibility exclusions: {eligibility_exclusion_count}")
    print(f"    Policies excluded: {len(policies_excluded)}")

    return summary, results


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the full experiment."""
    print("="*70)
    print("AKI v0.7 Experiment: Run A - Eligibility-Coupled Succession Baseline")
    print("="*70)
    print(f"Horizon: {HORIZON} cycles")
    print(f"Seeds: {SEEDS}")
    print(f"K values: {K_VALUES}")

    timestamp = datetime.now().isoformat()
    report = ExperimentReport(
        experiment_id=f"run_a_v070_{int(time.time())}",
        timestamp=timestamp,
        seeds=SEEDS,
    )

    all_results: List[ALSRunResultV070] = []

    for sub_run_id, k_value in K_VALUES.items():
        summary, results = run_sub_run(sub_run_id, k_value, SEEDS)
        report.sub_runs.append(summary)
        all_results.extend(results)

    # Store raw results
    report.raw_results = [r.to_dict() for r in all_results]

    # Save report
    report_path = Path(__file__).parent.parent / "reports" / f"run_a_v070_{int(time.time())}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"Report saved to: {report_path}")
    print(f"{'='*70}")

    # Print comparison summary
    print("\n\nComparison Summary:")
    print("-"*70)
    print(f"{'Sub-Run':<10} {'K':<5} {'Cycles':<10} {'Lapses':<10} {'Rate':<15} {'Exclusions':<12}")
    print("-"*70)
    for s in report.sub_runs:
        print(f"{s.sub_run_id:<10} {s.k_value:<5} {s.total_cycles:<10} {s.total_lapse_count:<10} {s.lapse_rate:.2f}/1k cycles  {s.eligibility_exclusion_count:<12}")
    print("-"*70)

    print("\n✓ Experiment complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
