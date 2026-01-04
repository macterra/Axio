#!/usr/bin/env python3
"""
Run D: AKI v0.7 Candidate Pool Composition Stress Under Forced Turnover (ALS-G)

Per instructions_v0.7_runnerD.md:
- Tests whether pool composition skew changes eligibility contraction and lapse frequency
- Fixed K=5 (boundary region from Run C)
- Fixed forced-turnover geometry (max_successive_renewals = 3)
- All other parameters identical to Run B/C

Purpose:
Quantify whether skewing the candidate pool toward failure-prone (Attack) or
pass-prone (Control) policies changes constitutional outcomes.

Sub-runs:
- D0: V060_DEFAULT (baseline control, replication anchor)
- D1: ATTACK_HEAVY_90 (~90% Attack, ~10% Control)
- D2: CONTROL_HEAVY_90 (~90% Control, ~10% Attack)
"""

import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
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
    get_pool_policy_weights,
)


# =============================================================================
# Configuration Constants (Binding per instructions_v0.7_runnerD.md)
# =============================================================================

# Renewal geometry (identical to Run B/C)
RENEWAL_CHECK_INTERVAL = 50
MSRW_CYCLES = 200
RENEWAL_COST = 5

# Horizon (identical to Run B/C)
HORIZON = 5000

# Rent schedule (unchanged)
RENT_E1 = 10
RENT_E2 = 40
RENT_E3 = 80
RENT_E4 = 160

# Forced turnover (identical to Run B/C)
MAX_SUCCESSIVE_RENEWALS = 3

# Fixed K value (boundary region from Run C)
K = 5

# Pool composition policies for sweep
POOL_POLICIES = {
    "D0": CandidatePoolPolicy.V060_DEFAULT,
    "D1": CandidatePoolPolicy.ATTACK_HEAVY_90,
    "D2": CandidatePoolPolicy.CONTROL_HEAVY_90,
}

# Seeds (same as Run A/B/C)
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
    """Summary for a single (pool_policy, seed) run."""
    sub_run_id: str
    pool_policy: str
    seed: int
    total_cycles: int
    total_successions: int
    post_init_successions: int
    forced_turnovers: int
    mean_residence_epochs: float
    avg_c_elig_size: float
    min_c_elig_size: int
    lapses: int
    time_in_null_authority: int
    attack_draws: int
    control_draws: int
    attack_draw_ratio: float
    control_draw_ratio: float
    dominant_regime: ConstitutionalRegime
    terminal_cause: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub_run_id": self.sub_run_id,
            "pool_policy": self.pool_policy,
            "seed": self.seed,
            "total_cycles": self.total_cycles,
            "total_successions": self.total_successions,
            "post_init_successions": self.post_init_successions,
            "forced_turnovers": self.forced_turnovers,
            "mean_residence_epochs": self.mean_residence_epochs,
            "avg_c_elig_size": self.avg_c_elig_size,
            "min_c_elig_size": self.min_c_elig_size,
            "lapses": self.lapses,
            "time_in_null_authority": self.time_in_null_authority,
            "attack_draws": self.attack_draws,
            "control_draws": self.control_draws,
            "attack_draw_ratio": self.attack_draw_ratio,
            "control_draw_ratio": self.control_draw_ratio,
            "dominant_regime": self.dominant_regime.name,
            "terminal_cause": self.terminal_cause,
        }


@dataclass
class SubRunSummary:
    """Summary for a sub-run (all seeds at one pool policy)."""
    sub_run_id: str
    pool_policy: str
    total_runs: int
    total_post_init_successions: int
    total_lapses: int
    total_time_in_null_authority: int
    avg_attack_draw_ratio: float
    avg_control_draw_ratio: float
    regime_distribution: Dict[str, int] = field(default_factory=dict)
    seed_results: List[SeedResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub_run_id": self.sub_run_id,
            "pool_policy": self.pool_policy,
            "total_runs": self.total_runs,
            "total_post_init_successions": self.total_post_init_successions,
            "total_lapses": self.total_lapses,
            "total_time_in_null_authority": self.total_time_in_null_authority,
            "avg_attack_draw_ratio": self.avg_attack_draw_ratio,
            "avg_control_draw_ratio": self.avg_control_draw_ratio,
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
    k_value: int = K
    max_successive_renewals: int = MAX_SUCCESSIVE_RENEWALS
    renewal_check_interval: int = RENEWAL_CHECK_INTERVAL
    pool_policies: List[str] = field(default_factory=list)
    seeds: List[int] = field(default_factory=list)
    sub_runs: List[SubRunSummary] = field(default_factory=list)
    weight_verification: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "spec_version": self.spec_version,
            "horizon": self.horizon,
            "k_value": self.k_value,
            "max_successive_renewals": self.max_successive_renewals,
            "renewal_check_interval": self.renewal_check_interval,
            "pool_policies": self.pool_policies,
            "seeds": self.seeds,
            "sub_runs": [s.to_dict() for s in self.sub_runs],
            "weight_verification": self.weight_verification,
        }


# =============================================================================
# Run Functions
# =============================================================================

def create_config(pool_policy: CandidatePoolPolicy) -> ALSConfigV070:
    """Create config with specified pool policy."""
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
        candidate_pool_policy=pool_policy,
        # Run B/C/D: forced turnover
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
    )


def run_single(seed: int, config: ALSConfigV070, verbose: bool = False) -> ALSRunResultV070:
    """Run a single v0.7 experiment."""
    harness = ALSHarnessV070(seed=seed, config=config, verbose=verbose)
    return harness.run()


def analyze_result(result: ALSRunResultV070, sub_run_id: str) -> SeedResult:
    """Analyze a single run result."""
    # Compute mean residence in epochs
    mean_residence_epochs = 0.0
    if result.mean_residence_cycles > 0:
        mean_residence_epochs = result.mean_residence_cycles / RENEWAL_CHECK_INTERVAL

    # Compute C_ELIG statistics
    # Use eligibility events to estimate pool size at each succession
    succession_elig: List[int] = []
    min_c_elig = 11  # Pool size

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

    for epoch in sorted(epoch_elig_counts.keys()):
        total, elig = epoch_elig_counts[epoch]
        if total > 0:
            approx_elig = min(elig, 11)
            succession_elig.append(approx_elig)
            min_c_elig = min(min_c_elig, approx_elig)

    avg_c_elig = sum(succession_elig) / len(succession_elig) if succession_elig else 11.0

    terminal_cause = result.stop_reason.name if result.stop_reason else "UNKNOWN"

    return SeedResult(
        sub_run_id=sub_run_id,
        pool_policy=result.pool_policy,
        seed=result.seed,
        total_cycles=result.total_cycles,
        total_successions=result.total_endorsements,
        post_init_successions=result.post_init_successions,
        forced_turnovers=result.forced_turnover_count,
        mean_residence_epochs=mean_residence_epochs,
        avg_c_elig_size=avg_c_elig,
        min_c_elig_size=min_c_elig,
        lapses=result.empty_eligible_set_events,
        time_in_null_authority=result.total_lapse_duration_cycles,
        attack_draws=result.attack_draws,
        control_draws=result.control_draws,
        attack_draw_ratio=result.attack_draw_ratio,
        control_draw_ratio=result.control_draw_ratio,
        dominant_regime=classify_regime(result),
        terminal_cause=terminal_cause,
    )


def run_sub_run(sub_run_id: str, pool_policy: CandidatePoolPolicy, seeds: List[int]) -> SubRunSummary:
    """Run all seeds for a sub-run configuration."""
    print(f"\n{'='*60}")
    print(f"Sub-Run {sub_run_id}: {pool_policy.name}")
    print(f"{'='*60}")

    # Report expected weights
    control_w, attack_w = get_pool_policy_weights(pool_policy)
    print(f"  Expected weights: Control={control_w:.2f}, Attack={attack_w:.2f}")

    config = create_config(pool_policy)
    seed_results: List[SeedResult] = []

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        start = time.time()
        result = run_single(seed, config, verbose=False)
        elapsed = time.time() - start

        seed_result = analyze_result(result, sub_run_id)
        seed_results.append(seed_result)

        print(f"done ({result.total_cycles} cycles, "
              f"{result.post_init_successions} post-init, "
              f"{result.empty_eligible_set_events} lapses, "
              f"A/C={result.attack_draw_ratio:.2%}/{result.control_draw_ratio:.2%}, "
              f"{elapsed:.2f}s)")

    # Aggregate
    total_post_init = sum(r.post_init_successions for r in seed_results)
    total_lapses = sum(r.lapses for r in seed_results)
    total_null_auth = sum(r.time_in_null_authority for r in seed_results)
    avg_attack_ratio = sum(r.attack_draw_ratio for r in seed_results) / len(seed_results)
    avg_control_ratio = sum(r.control_draw_ratio for r in seed_results) / len(seed_results)

    regime_counts = Counter(r.dominant_regime.name for r in seed_results)

    summary = SubRunSummary(
        sub_run_id=sub_run_id,
        pool_policy=pool_policy.name,
        total_runs=len(seed_results),
        total_post_init_successions=total_post_init,
        total_lapses=total_lapses,
        total_time_in_null_authority=total_null_auth,
        avg_attack_draw_ratio=avg_attack_ratio,
        avg_control_draw_ratio=avg_control_ratio,
        regime_distribution=dict(regime_counts),
        seed_results=seed_results,
    )

    print(f"\n  Summary {pool_policy.name}:")
    print(f"    Post-init successions: {total_post_init}")
    print(f"    Lapses: {total_lapses}")
    print(f"    Time in NULL_AUTHORITY: {total_null_auth} cycles")
    print(f"    Avg Attack/Control draw ratio: {avg_attack_ratio:.2%}/{avg_control_ratio:.2%}")
    print(f"    Regime distribution: {dict(regime_counts)}")

    return summary


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the full experiment."""
    print("="*70)
    print("AKI v0.7 Experiment: Run D - Candidate Pool Composition Stress")
    print("="*70)
    print(f"Horizon: {HORIZON} cycles")
    print(f"Seeds: {SEEDS}")
    print(f"K: {K} (fixed)")
    print(f"max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS} (forced turnover)")
    print(f"Pool policies: {[p.name for p in POOL_POLICIES.values()]}")

    timestamp = datetime.now().isoformat()
    report = ExperimentReport(
        experiment_id=f"run_d_v070_{int(time.time())}",
        timestamp=timestamp,
        pool_policies=[p.name for p in POOL_POLICIES.values()],
        seeds=SEEDS,
    )

    # Record weight verification
    for sub_run_id, policy in POOL_POLICIES.items():
        control_w, attack_w = get_pool_policy_weights(policy)
        report.weight_verification[policy.name] = {
            "control_weight": control_w,
            "attack_weight": attack_w,
        }

    for sub_run_id, pool_policy in POOL_POLICIES.items():
        summary = run_sub_run(sub_run_id, pool_policy, SEEDS)
        report.sub_runs.append(summary)

    # Save report
    report_path = Path(__file__).parent.parent / "reports" / f"run_d_v070_{int(time.time())}.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"Report saved to: {report_path}")
    print(f"{'='*70}")

    # ==========================================================================
    # Required Reporting
    # ==========================================================================

    # Summary Table (all pool policies, seed combinations)
    print("\n\nSummary Table (Required per instructions):")
    print("-"*150)
    print(f"{'Policy':<20} {'Seed':<6} {'Post-Init':<10} {'Avg|C_ELIG|':<12} {'Min|C_ELIG|':<12} "
          f"{'Lapses':<8} {'NULL_AUTH':<12} {'Attack%':<10} {'Control%':<10} {'Regime':<22} {'Terminal':<15}")
    print("-"*150)
    for sub in report.sub_runs:
        for r in sub.seed_results:
            print(f"{r.pool_policy:<20} {r.seed:<6} {r.post_init_successions:<10} {r.avg_c_elig_size:<12.2f} "
                  f"{r.min_c_elig_size:<12} {r.lapses:<8} "
                  f"{r.time_in_null_authority:<12} {r.attack_draw_ratio:<10.2%} {r.control_draw_ratio:<10.2%} "
                  f"{r.dominant_regime.name:<22} {r.terminal_cause:<15}")
    print("-"*150)

    # Phase-Line View
    print("\n\nPhase-Line View (Pool Policy → Regime Distribution):")
    print("-"*80)
    print(f"{'Pool Policy':<20} {'LATENT':<12} {'FILTERING_ACTIVE':<20} {'CONSTITUTIONAL_LAPSE':<22}")
    print("-"*80)
    for sub in report.sub_runs:
        latent = sub.regime_distribution.get("LATENT", 0)
        filtering = sub.regime_distribution.get("FILTERING_ACTIVE", 0)
        lapse = sub.regime_distribution.get("CONSTITUTIONAL_LAPSE", 0)
        print(f"{sub.pool_policy:<20} {latent}/5{'':<8} {filtering}/5{'':<16} {lapse}/5")
    print("-"*80)

    # Composition Verification
    print("\n" + "="*70)
    print("Composition Verification (Required)")
    print("="*70)
    for sub in report.sub_runs:
        expected_control, expected_attack = get_pool_policy_weights(
            CandidatePoolPolicy[sub.pool_policy]
        )
        print(f"\n  {sub.pool_policy}:")
        print(f"    Expected: Attack={expected_attack:.0%}, Control={expected_control:.0%}")
        print(f"    Realized: Attack={sub.avg_attack_draw_ratio:.1%}, Control={sub.avg_control_draw_ratio:.1%}")
        # Check if within tolerance (±5%)
        attack_ok = abs(sub.avg_attack_draw_ratio - expected_attack) <= 0.05
        control_ok = abs(sub.avg_control_draw_ratio - expected_control) <= 0.05
        if attack_ok and control_ok:
            print(f"    ✓ Composition matches expected skew")
        else:
            print(f"    ⚠ Composition deviates from expected skew")

    # Conservative Interpretation per Sub-Run
    print("\n" + "="*70)
    print("Conservative Interpretation (per Pool Policy)")
    print("="*70)

    for sub in report.sub_runs:
        lapses = sub.total_lapses
        null_auth = sub.total_time_in_null_authority
        regime_dist = sub.regime_distribution
        lapse_seeds = regime_dist.get("CONSTITUTIONAL_LAPSE", 0)
        filtering_seeds = regime_dist.get("FILTERING_ACTIVE", 0)
        latent_seeds = regime_dist.get("LATENT", 0)

        print(f"\n### {sub.pool_policy} ({sub.sub_run_id})")
        print(f"  Pool composition: Attack={sub.avg_attack_draw_ratio:.1%}, Control={sub.avg_control_draw_ratio:.1%}")
        print(f"  Eligibility filtering: {'ACTIVATED' if lapses > 0 or filtering_seeds > 0 else 'LATENT'}")
        print(f"  Constitutional lapse: {'OCCURRED' if lapses > 0 else 'DID NOT OCCUR'} ({lapses} events across {lapse_seeds} seeds)")
        print(f"  Time in NULL_AUTHORITY: {null_auth} cycles")
        print(f"  Regime distribution: LATENT={latent_seeds}/5, FILTERING_ACTIVE={filtering_seeds}/5, CONSTITUTIONAL_LAPSE={lapse_seeds}/5")
        print(f"  What CANNOT be inferred: competence, governance quality, alignment properties, generality beyond tested geometry")

    # Composition-dependent observations
    print("\n" + "="*70)
    print("Composition-Dependent Observations")
    print("="*70)

    lapse_by_policy = {s.pool_policy: s.total_lapses for s in report.sub_runs}
    null_auth_by_policy = {s.pool_policy: s.total_time_in_null_authority for s in report.sub_runs}

    print(f"\n  Lapse count by policy: {lapse_by_policy}")
    print(f"  NULL_AUTHORITY time by policy: {null_auth_by_policy}")

    # Compare D1 vs D0
    d0 = next((s for s in report.sub_runs if s.pool_policy == "V060_DEFAULT"), None)
    d1 = next((s for s in report.sub_runs if s.pool_policy == "ATTACK_HEAVY_90"), None)
    d2 = next((s for s in report.sub_runs if s.pool_policy == "CONTROL_HEAVY_90"), None)

    if d0 and d1:
        if d1.total_lapses > d0.total_lapses:
            print(f"\n  ✓ ATTACK_HEAVY increases lapse relative to baseline ({d1.total_lapses} vs {d0.total_lapses})")
        elif d1.total_lapses == d0.total_lapses:
            print(f"\n  ○ ATTACK_HEAVY has same lapse count as baseline ({d1.total_lapses})")
        else:
            print(f"\n  ⚠ ATTACK_HEAVY has fewer lapses than baseline ({d1.total_lapses} vs {d0.total_lapses}) - unexpected")

    if d0 and d2:
        if d2.total_lapses < d0.total_lapses:
            print(f"  ✓ CONTROL_HEAVY reduces lapse relative to baseline ({d2.total_lapses} vs {d0.total_lapses})")
        elif d2.total_lapses == 0:
            print(f"  ✓ CONTROL_HEAVY eliminates lapse ({d2.total_lapses} lapses)")
        else:
            print(f"  ○ CONTROL_HEAVY has same or more lapses than baseline ({d2.total_lapses} vs {d0.total_lapses})")

    print("\n✓ Run D complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
