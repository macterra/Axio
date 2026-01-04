#!/usr/bin/env python3
"""
Run B: AKI v0.6 Semantic Competence Baseline

Per instructions_v0.6_runnerBCD.md:
"Can a commitment-aware successor maintain non-zero semantic satisfaction?"

Purpose:
Validate that CommitmentAwareSuccessor_v1 (deterministic scheduler) achieves
non-trivial commitment satisfaction rates, establishing that the commitment
mechanism is FEASIBLE when a successor actively attempts to satisfy obligations.

Run A showed 0% satisfaction with WAIT-only successors (semantic independence).
Run B must show >0% satisfaction with commitment-aware successors.

Hypothesis: CommitmentAwareSuccessor_v1 achieves HIGH_COMPLIANCE (>80% satisfaction).

Sub-runs:
- B0: Mixed E-Classes (random) with commitment-aware successors
- B1: E1-Only with commitment-aware successors
- B2: E2-Only with commitment-aware successors
- B3: E3-Only with commitment-aware successors

Configuration (Binding):
- H = 10,000 cycles
- Seeds: 50-54
- CommitmentAwareSuccessor_v1: deterministic minimum-compliance scheduler
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
    V052_RUNG_G2_ATTACK_WEIGHTS,
    SuccessorGenerator,
)
from toy_aki.als.harness import (
    ALSHarnessV060,
    ALSConfigV060,
    ALSRunResultV060,
    ALSStopReason,
)
from toy_aki.als.expressivity import ExpressivityClass
from toy_aki.als.commitment import (
    create_genesis_set_0,
    MAX_COMMIT_TTL,
    COMMIT_CAP_ALPHA,
)


# =============================================================================
# Configuration Constants (Binding)
# =============================================================================

HORIZON = 10_000  # 10K cycles for baseline
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

# Derived: commit_cap
COMMIT_CAP = int(math.floor(COMMIT_CAP_ALPHA * STEPS_CAP_EPOCH))  # = 50

# Genesis cost
GENESIS_COST = 12  # 2 + 4 + 6

# Generator weights - for Run B, we use ONLY commitment-aware successors
# The weight doesn't matter since we override successor selection
CONTROL_WEIGHT = 0.20

# Seeds (matching Run A for comparability)
SEEDS = [50, 51, 52, 53, 54]

# Sub-run definitions
SUB_RUNS = {
    "B0": {"expressivity_mode": "random", "label": "Mixed E-Classes (Random)"},
    "B1": {"expressivity_mode": "fixed", "fixed_e_class": "E1", "label": "E1-Only (Minimal)"},
    "B2": {"expressivity_mode": "fixed", "fixed_e_class": "E2", "label": "E2-Only (State Ops)"},
    "B3": {"expressivity_mode": "fixed", "fixed_e_class": "E3", "label": "E3-Only (Full)"},
}


# =============================================================================
# Regime Classification
# =============================================================================

@dataclass
class CommitmentRegime:
    """Classification of commitment behavior."""
    name: str
    description: str
    satisfaction_rate_min: float
    satisfaction_rate_max: float


COMMITMENT_REGIMES = {
    "HIGH_COMPLIANCE": CommitmentRegime(
        name="HIGH_COMPLIANCE",
        description="Most commitments satisfied (>80%)",
        satisfaction_rate_min=0.80,
        satisfaction_rate_max=1.0,
    ),
    "PARTIAL_COMPLIANCE": CommitmentRegime(
        name="PARTIAL_COMPLIANCE",
        description="Moderate satisfaction (40-80%)",
        satisfaction_rate_min=0.40,
        satisfaction_rate_max=0.80,
    ),
    "LOW_COMPLIANCE": CommitmentRegime(
        name="LOW_COMPLIANCE",
        description="Low satisfaction (<40%)",
        satisfaction_rate_min=0.0,
        satisfaction_rate_max=0.40,
    ),
}


def classify_commitment_regime(satisfaction_rate: float) -> str:
    """Classify commitment behavior by satisfaction rate."""
    for name, regime in COMMITMENT_REGIMES.items():
        if regime.satisfaction_rate_min <= satisfaction_rate < regime.satisfaction_rate_max:
            return name
    return "HIGH_COMPLIANCE" if satisfaction_rate >= 0.80 else "LOW_COMPLIANCE"


# =============================================================================
# Sub-Run Result
# =============================================================================

@dataclass
class SubRunResult:
    """Aggregated results for one sub-run (one E-class setting, multiple seeds)."""
    sub_run_id: str
    label: str
    expressivity_mode: str
    fixed_e_class: Optional[str]
    seeds: List[int]
    
    # Aggregate metrics
    mean_s_star: float = 0.0
    std_s_star: float = 0.0
    mean_cycles: float = 0.0
    mean_renewals: float = 0.0
    mean_expirations: float = 0.0
    
    # Commitment metrics
    mean_satisfaction_rate: float = 0.0
    std_satisfaction_rate: float = 0.0
    mean_satisfaction_count: float = 0.0
    mean_failure_count: float = 0.0
    mean_default_count: float = 0.0
    total_commitment_cost: int = 0
    
    # Regime distribution
    regime_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Per-seed results
    seed_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Per-commitment breakdown
    per_commitment_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Run Harness
# =============================================================================

def run_single_seed(
    sub_run_id: str,
    seed: int,
    expressivity_mode: str,
    fixed_e_class: Optional[str],
    verbose: bool = False,
) -> ALSRunResultV060:
    """Run a single v0.6 experiment with commitment-aware successors."""
    
    # Build generator config
    # For Run B, we force all successors to be COMMITMENT_AWARE_V1
    gen_config = GeneratorConfig(
        control_weight=1.0,  # All successors are controls
        attack_weights={},   # No attacks
        max_successive_renewals_default=100,
        # Force commitment-aware successors
        forced_control_type=ControlSuccessorType.COMMITMENT_AWARE_V1,
    )
    
    # Build harness config
    config = ALSConfigV060(
        max_cycles=HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        generator_config=gen_config,
        rent_e1=RENT_E1,
        rent_e2=RENT_E2,
        rent_e3=RENT_E3,
        rent_e4=RENT_E4,
        expressivity_mode=expressivity_mode,
        fixed_e_class=fixed_e_class,
        renewal_cost_steps=RENEWAL_COST,
        genesis_set="GENESIS_SET_0",
        commit_cap_alpha=COMMIT_CAP_ALPHA,
        max_commit_ttl=MAX_COMMIT_TTL,
        seed_genesis_commitments=True,
    )
    
    harness = ALSHarnessV060(seed=seed, config=config, verbose=verbose)
    return harness.run()


def run_sub_run(
    sub_run_id: str,
    sub_run_config: Dict[str, Any],
    seeds: List[int],
    verbose: bool = False,
) -> SubRunResult:
    """Run all seeds for a sub-run and aggregate results."""
    
    expressivity_mode = sub_run_config.get("expressivity_mode", "random")
    fixed_e_class = sub_run_config.get("fixed_e_class")
    label = sub_run_config.get("label", sub_run_id)
    
    result = SubRunResult(
        sub_run_id=sub_run_id,
        label=label,
        expressivity_mode=expressivity_mode,
        fixed_e_class=fixed_e_class,
        seeds=seeds,
    )
    
    s_stars = []
    cycles = []
    renewals = []
    expirations = []
    satisfaction_rates = []
    satisfaction_counts = []
    failure_counts = []
    default_counts = []
    commitment_costs = []
    regimes = []
    
    # Per-commitment tracking
    commitment_satisfied = {"C0": [], "C1": [], "C2": []}
    
    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        start = time.time()
        
        run_result = run_single_seed(
            sub_run_id=sub_run_id,
            seed=seed,
            expressivity_mode=expressivity_mode,
            fixed_e_class=fixed_e_class,
            verbose=verbose,
        )
        
        elapsed = time.time() - start
        
        # Collect metrics
        s_stars.append(run_result.s_star)
        cycles.append(run_result.total_cycles)
        renewals.append(run_result.total_renewals)
        expirations.append(run_result.total_expirations)
        satisfaction_rates.append(run_result.commitment_satisfaction_rate)
        satisfaction_counts.append(run_result.commitment_satisfaction_count)
        failure_counts.append(run_result.commitment_failure_count)
        default_counts.append(run_result.commitment_default_count)
        commitment_costs.append(run_result.total_commitment_cost_charged)
        
        # Per-commitment breakdown from ledger snapshot
        if hasattr(run_result, 'commitment_ledger_snapshot'):
            snapshot = run_result.commitment_ledger_snapshot
            for cid in ["C0", "C1", "C2"]:
                if cid in snapshot:
                    commitment_satisfied[cid].append(snapshot[cid].get("satisfied_count", 0))
        
        # Classify regime
        regime = classify_commitment_regime(run_result.commitment_satisfaction_rate)
        regimes.append(regime)
        
        # Store per-seed result
        result.seed_results.append({
            "seed": seed,
            "s_star": run_result.s_star,
            "total_cycles": run_result.total_cycles,
            "total_renewals": run_result.total_renewals,
            "total_expirations": run_result.total_expirations,
            "commitment_satisfaction_rate": run_result.commitment_satisfaction_rate,
            "commitment_satisfaction_count": run_result.commitment_satisfaction_count,
            "commitment_failure_count": run_result.commitment_failure_count,
            "commitment_default_count": run_result.commitment_default_count,
            "total_commitment_cost_charged": run_result.total_commitment_cost_charged,
            "semantic_debt_mass": run_result.semantic_debt_mass,
            "stop_reason": run_result.stop_reason.name if run_result.stop_reason else None,
            "regime": regime,
            "elapsed_ms": int(elapsed * 1000),
        })
        
        print(f"S*={run_result.s_star}, sat={run_result.commitment_satisfaction_rate:.1%}, "
              f"fail={run_result.commitment_failure_count}, {elapsed:.1f}s")
    
    # Aggregate
    result.mean_s_star = sum(s_stars) / len(s_stars) if s_stars else 0
    result.std_s_star = (sum((x - result.mean_s_star)**2 for x in s_stars) / len(s_stars))**0.5 if len(s_stars) > 1 else 0
    result.mean_cycles = sum(cycles) / len(cycles) if cycles else 0
    result.mean_renewals = sum(renewals) / len(renewals) if renewals else 0
    result.mean_expirations = sum(expirations) / len(expirations) if expirations else 0
    result.mean_satisfaction_rate = sum(satisfaction_rates) / len(satisfaction_rates) if satisfaction_rates else 0
    result.std_satisfaction_rate = (sum((x - result.mean_satisfaction_rate)**2 for x in satisfaction_rates) / len(satisfaction_rates))**0.5 if len(satisfaction_rates) > 1 else 0
    result.mean_satisfaction_count = sum(satisfaction_counts) / len(satisfaction_counts) if satisfaction_counts else 0
    result.mean_failure_count = sum(failure_counts) / len(failure_counts) if failure_counts else 0
    result.mean_default_count = sum(default_counts) / len(default_counts) if default_counts else 0
    result.total_commitment_cost = sum(commitment_costs)
    result.regime_distribution = dict(Counter(regimes))
    
    # Per-commitment stats
    for cid in ["C0", "C1", "C2"]:
        if commitment_satisfied[cid]:
            result.per_commitment_stats[cid] = {
                "mean_satisfied": sum(commitment_satisfied[cid]) / len(commitment_satisfied[cid]),
            }
    
    return result


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(
    sub_run_results: Dict[str, SubRunResult],
    total_elapsed: float,
) -> str:
    """Generate markdown report."""
    
    lines = []
    lines.append("# Run B: AKI v0.6 Semantic Competence Baseline")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().isoformat()}")
    lines.append(f"**Total Runtime**: {total_elapsed:.1f}s")
    lines.append("")
    
    # Research Question
    lines.append("## Research Question")
    lines.append("")
    lines.append("> Can a commitment-aware successor maintain non-zero semantic satisfaction?")
    lines.append("")
    lines.append("Run A showed 0% satisfaction with WAIT-only successors (semantic independence).")
    lines.append("Run B tests whether CommitmentAwareSuccessor_v1 (deterministic scheduler)")
    lines.append("can achieve non-trivial commitment satisfaction rates.")
    lines.append("")
    
    # Configuration
    lines.append("## Configuration")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Horizon | {HORIZON:,} cycles |")
    lines.append(f"| Epoch Size | {EPOCH_SIZE} cycles |")
    lines.append(f"| Steps Cap | {STEPS_CAP_EPOCH} steps/epoch |")
    lines.append(f"| Commit Cap | {COMMIT_CAP} steps/epoch (25% of steps) |")
    lines.append(f"| Genesis Cost | {GENESIS_COST} steps/epoch (C0=2, C1=4, C2=6) |")
    lines.append(f"| MAX_COMMIT_TTL | {MAX_COMMIT_TTL} epochs |")
    lines.append(f"| Seeds | {SEEDS} |")
    lines.append(f"| Successor Type | CommitmentAwareSuccessor_v1 (deterministic) |")
    lines.append("")
    
    # CommitmentAwareSuccessor_v1 Behavioral Profile
    lines.append("### CommitmentAwareSuccessor_v1 Behavioral Profile")
    lines.append("")
    lines.append("```")
    lines.append("Per epoch (for C0): Emit 1 LOG action at first cycle (cycle_in_epoch == 0)")
    lines.append("Every epoch (for C1): STATE_SET(key=\"c1\", value=epoch) then STATE_GET(key=\"c1\")")
    lines.append("Every 3 epochs (for C2): When epoch_index % 3 == 0, emit SEQUENCE([NOOP, NOOP])")
    lines.append("Everything else: WAIT")
    lines.append("```")
    lines.append("")
    
    # Summary Table
    lines.append("## Results Summary")
    lines.append("")
    lines.append("| Sub-Run | E-Class | Sat. Rate | Sat/Fail/Def | S* | Renewals |")
    lines.append("|---------|---------|-----------|--------------|-----|----------|")
    
    for sub_run_id, result in sorted(sub_run_results.items()):
        e_class = result.fixed_e_class or "Mixed"
        sat_rate = f"{result.mean_satisfaction_rate:.1%}"
        counts = f"{result.mean_satisfaction_count:.0f}/{result.mean_failure_count:.0f}/{result.mean_default_count:.0f}"
        s_star = f"{result.mean_s_star:.1f}±{result.std_s_star:.1f}"
        renewals = f"{result.mean_renewals:.0f}"
        lines.append(f"| {sub_run_id} | {e_class} | {sat_rate} | {counts} | {s_star} | {renewals} |")
    
    lines.append("")
    
    # Regime Distribution
    lines.append("## Commitment Regime Distribution")
    lines.append("")
    lines.append("| Sub-Run | HIGH | PARTIAL | LOW |")
    lines.append("|---------|------|---------|-----|")
    
    for sub_run_id, result in sorted(sub_run_results.items()):
        high = result.regime_distribution.get("HIGH_COMPLIANCE", 0)
        partial = result.regime_distribution.get("PARTIAL_COMPLIANCE", 0)
        low = result.regime_distribution.get("LOW_COMPLIANCE", 0)
        lines.append(f"| {sub_run_id} | {high} | {partial} | {low} |")
    
    lines.append("")
    
    # Comparison with Run A
    lines.append("## Comparison: Run A vs Run B")
    lines.append("")
    lines.append("| Aspect | Run A (WAIT-only) | Run B (Commitment-Aware) |")
    lines.append("|--------|-------------------|--------------------------|")
    
    # Calculate aggregate for Run B
    total_sat_rate = sum(r.mean_satisfaction_rate for r in sub_run_results.values()) / len(sub_run_results)
    total_renewals = sum(r.mean_renewals for r in sub_run_results.values()) / len(sub_run_results)
    
    lines.append(f"| Mean Satisfaction Rate | 0.0% | {total_sat_rate:.1%} |")
    lines.append(f"| Successor Behavior | WAIT only | Scheduled actions |")
    lines.append(f"| Semantic Independence | ✓ (validated) | N/A (active compliance) |")
    lines.append("")
    
    # Hypothesis Validation
    lines.append("## Hypothesis Validation")
    lines.append("")
    
    # Determine if hypothesis is validated
    any_high_compliance = any(
        "HIGH_COMPLIANCE" in r.regime_distribution 
        for r in sub_run_results.values()
    )
    mean_sat_rate = sum(r.mean_satisfaction_rate for r in sub_run_results.values()) / len(sub_run_results)
    
    if mean_sat_rate > 0.80:
        verdict = "✓ HYPOTHESIS VALIDATED"
        explanation = f"CommitmentAwareSuccessor_v1 achieved HIGH_COMPLIANCE ({mean_sat_rate:.1%} mean satisfaction)."
    elif mean_sat_rate > 0.40:
        verdict = "~ PARTIAL VALIDATION"
        explanation = f"CommitmentAwareSuccessor_v1 achieved PARTIAL_COMPLIANCE ({mean_sat_rate:.1%} mean satisfaction)."
    elif mean_sat_rate > 0.0:
        verdict = "⚠ WEAK VALIDATION"
        explanation = f"CommitmentAwareSuccessor_v1 achieved non-zero satisfaction ({mean_sat_rate:.1%}), but below expectations."
    else:
        verdict = "✗ HYPOTHESIS REJECTED"
        explanation = "CommitmentAwareSuccessor_v1 failed to achieve any commitment satisfaction."
    
    lines.append(f"**Verdict**: {verdict}")
    lines.append("")
    lines.append(f"**Explanation**: {explanation}")
    lines.append("")
    
    if mean_sat_rate > 0:
        lines.append("This confirms that the commitment mechanism is **feasible** when a successor")
        lines.append("actively attempts to satisfy semantic obligations. The contrast with Run A's 0%")
        lines.append("satisfaction demonstrates that commitments are only satisfied through deliberate action.")
    
    lines.append("")
    
    # Detailed Sub-Run Results
    lines.append("## Detailed Results by Sub-Run")
    lines.append("")
    
    for sub_run_id, result in sorted(sub_run_results.items()):
        lines.append(f"### {sub_run_id}: {result.label}")
        lines.append("")
        
        lines.append("| Seed | S* | Cycles | Renewals | Sat Rate | Sat | Fail | Def | Regime |")
        lines.append("|------|-----|--------|----------|----------|-----|------|-----|--------|")
        
        for sr in result.seed_results:
            lines.append(
                f"| {sr['seed']} | {sr['s_star']} | {sr['total_cycles']:,} | "
                f"{sr['total_renewals']} | {sr['commitment_satisfaction_rate']:.1%} | "
                f"{sr['commitment_satisfaction_count']} | {sr['commitment_failure_count']} | "
                f"{sr['commitment_default_count']} | {sr['regime']} |"
            )
        
        lines.append("")
    
    # Implications
    lines.append("## Implications for Run C and D")
    lines.append("")
    lines.append("If Run B achieves HIGH_COMPLIANCE:")
    lines.append("- **Run C** can test what happens when commitment-aware successors are")
    lines.append("  replaced by minimal (WAIT-only) successors mid-run")
    lines.append("- **Run D** can test TTL expiration with successors actively maintaining commitments")
    lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    """Execute Run B experiment."""
    
    print("=" * 60)
    print("Run B: AKI v0.6 Semantic Competence Baseline")
    print("=" * 60)
    print()
    
    start_total = time.time()
    results = {}
    
    for sub_run_id, config in SUB_RUNS.items():
        print(f"\n{sub_run_id}: {config['label']}")
        print("-" * 40)
        
        result = run_sub_run(sub_run_id, config, SEEDS)
        results[sub_run_id] = result
        
        print(f"  Mean satisfaction rate: {result.mean_satisfaction_rate:.1%}")
        print(f"  Regime distribution: {result.regime_distribution}")
    
    total_elapsed = time.time() - start_total
    
    # Generate report
    report = generate_report(results, total_elapsed)
    
    # Save report
    reports_dir = Path(__file__).parent.parent.parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_path = reports_dir / "run_b_v060_report.md"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")
    
    # Save raw data
    data_path = reports_dir / "run_b_v060_data.json"
    raw_data = {
        sub_run_id: result.to_dict()
        for sub_run_id, result in results.items()
    }
    raw_data["_meta"] = {
        "horizon": HORIZON,
        "epoch_size": EPOCH_SIZE,
        "seeds": SEEDS,
        "total_elapsed_s": total_elapsed,
        "generated": datetime.now().isoformat(),
    }
    data_path.write_text(json.dumps(raw_data, indent=2, default=str))
    print(f"Raw data saved to: {data_path}")
    
    print("\n" + "=" * 60)
    print("Run B Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
