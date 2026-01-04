#!/usr/bin/env python3
"""
Run A: AKI v0.6 Semantic Commitment Baseline

Per spec §6 (ALS-C: Authority Leases with Semantic Commitments):
- Tests GENESIS_SET_0 (C0, C1, C2) with total cost 12 steps/epoch
- Validates semantic independence: commitment failure ≠ authority loss
- Measures commitment satisfaction rates under various E-class conditions

Purpose:
Establish baseline behavior for the Commitment Ledger mechanism and verify
that semantic obligations can fail independently of structural renewal.

Key Invariants to Validate:
1. Genesis commitments seeded before first succession
2. Commitment cost charged AFTER rent
3. Semantic failure does NOT revoke authority
4. Evaluation at epoch end only
5. MAX_COMMIT_TTL = 10 enforced
6. commit_cap = floor(0.25 * steps_cap_epoch) enforced

Sub-runs:
- L0: Mixed E-classes (random assignment)
- L1: E1-only (minimal expressivity, should satisfy C0 easily)
- L2: E2-only (state operations, should satisfy C0+C1)
- L3: E3-only (full expressivity, should satisfy all commitments)
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

# Generator weights
CONTROL_WEIGHT = 0.20

# Seeds
SEEDS = [50, 51, 52, 53, 54]

# Sub-run definitions
SUB_RUNS = {
    "A0": {"expressivity_mode": "random", "label": "Mixed E-Classes (Random)"},
    "A1": {"expressivity_mode": "fixed", "fixed_e_class": "E1", "label": "E1-Only (Minimal)"},
    "A2": {"expressivity_mode": "fixed", "fixed_e_class": "E2", "label": "E2-Only (State Ops)"},
    "A3": {"expressivity_mode": "fixed", "fixed_e_class": "E3", "label": "E3-Only (Full)"},
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
    """Aggregated results for one sub-run (one MSR setting, multiple seeds)."""
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
    mean_failure_count: float = 0.0
    mean_default_count: float = 0.0
    total_commitment_cost: int = 0
    
    # Regime distribution
    regime_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Per-seed results
    seed_results: List[Dict[str, Any]] = field(default_factory=list)
    
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
    """Run a single v0.6 experiment."""
    
    # Build generator config
    gen_config = GeneratorConfig(
        control_weight=CONTROL_WEIGHT,
        attack_weights=V052_RUNG_G2_ATTACK_WEIGHTS,
        max_successive_renewals_default=100,
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
    failure_counts = []
    default_counts = []
    commitment_costs = []
    regimes = []
    
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
        failure_counts.append(run_result.commitment_failure_count)
        default_counts.append(run_result.commitment_default_count)
        commitment_costs.append(run_result.total_commitment_cost_charged)
        
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
    result.mean_failure_count = sum(failure_counts) / len(failure_counts) if failure_counts else 0
    result.mean_default_count = sum(default_counts) / len(default_counts) if default_counts else 0
    result.total_commitment_cost = sum(commitment_costs)
    result.regime_distribution = dict(Counter(regimes))
    
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
    lines.append("# Run A: AKI v0.6 Semantic Commitment Baseline")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().isoformat()}")
    lines.append(f"**Total Runtime**: {total_elapsed:.1f}s")
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
    lines.append(f"| Renewal Interval | {RENEWAL_CHECK_INTERVAL} cycles |")
    lines.append(f"| Seeds | {SEEDS} |")
    lines.append("")
    
    # GENESIS_SET_0 description
    lines.append("## GENESIS_SET_0 Commitments")
    lines.append("")
    lines.append("| CID | Spec | Verifier | Window | Cost |")
    lines.append("|-----|------|----------|--------|------|")
    lines.append("| C0 | CMT_PRESENCE_LOG | VRF_EPOCH_ACTION_COUNT | 1 epoch | 2 |")
    lines.append("| C1 | CMT_STATE_ECHO | VRF_ORDERED_ACTION_PATTERN | 2 epochs | 4 |")
    lines.append("| C2 | CMT_COMPOSED_OP | VRF_ACTION_HAS_PAYLOAD_SHAPE | 3 epochs | 6 |")
    lines.append("")
    
    # Summary table
    lines.append("## Summary by Sub-Run")
    lines.append("")
    lines.append("| Sub-Run | Label | Mean S* | Mean Sat% | Mean Fail | Regime |")
    lines.append("|---------|-------|---------|-----------|-----------|--------|")
    
    for sub_id in ["A0", "A1", "A2", "A3"]:
        if sub_id not in sub_run_results:
            continue
        r = sub_run_results[sub_id]
        # Dominant regime
        dominant = max(r.regime_distribution.items(), key=lambda x: x[1])[0] if r.regime_distribution else "N/A"
        lines.append(f"| {sub_id} | {r.label} | {r.mean_s_star:.1f} ± {r.std_s_star:.1f} | "
                     f"{r.mean_satisfaction_rate:.1%} ± {r.std_satisfaction_rate:.1%} | "
                     f"{r.mean_failure_count:.1f} | {dominant} |")
    lines.append("")
    
    # Detailed per-sub-run
    lines.append("## Detailed Results")
    lines.append("")
    
    for sub_id in ["A0", "A1", "A2", "A3"]:
        if sub_id not in sub_run_results:
            continue
        r = sub_run_results[sub_id]
        
        lines.append(f"### {sub_id}: {r.label}")
        lines.append("")
        lines.append(f"- **Expressivity Mode**: {r.expressivity_mode}")
        if r.fixed_e_class:
            lines.append(f"- **Fixed E-Class**: {r.fixed_e_class}")
        lines.append(f"- **Mean S***: {r.mean_s_star:.1f} ± {r.std_s_star:.1f}")
        lines.append(f"- **Mean Satisfaction Rate**: {r.mean_satisfaction_rate:.1%} ± {r.std_satisfaction_rate:.1%}")
        lines.append(f"- **Mean Failure Count**: {r.mean_failure_count:.1f}")
        lines.append(f"- **Mean Default Count**: {r.mean_default_count:.1f}")
        lines.append(f"- **Total Commitment Cost**: {r.total_commitment_cost:,} steps")
        lines.append("")
        
        # Per-seed table
        lines.append("| Seed | S* | Cycles | Renewals | Sat% | Fails | Defaults | Regime |")
        lines.append("|------|-----|--------|----------|------|-------|----------|--------|")
        for sr in r.seed_results:
            lines.append(f"| {sr['seed']} | {sr['s_star']} | {sr['total_cycles']:,} | "
                         f"{sr['total_renewals']} | {sr['commitment_satisfaction_rate']:.1%} | "
                         f"{sr['commitment_failure_count']} | {sr['commitment_default_count']} | "
                         f"{sr['regime']} |")
        lines.append("")
    
    # Key findings
    lines.append("## Key Findings")
    lines.append("")
    
    # Check semantic independence
    lines.append("### 1. Semantic Independence Validation")
    lines.append("")
    for sub_id, r in sub_run_results.items():
        failures_with_continuation = [
            sr for sr in r.seed_results
            if sr['commitment_failure_count'] > 0 and sr['s_star'] > 0
        ]
        if failures_with_continuation:
            lines.append(f"- **{sub_id}**: {len(failures_with_continuation)}/{len(r.seed_results)} runs had "
                         f"commitment failures but continued running (semantic independence confirmed)")
    lines.append("")
    
    # E-class correlation
    lines.append("### 2. Expressivity-Commitment Correlation")
    lines.append("")
    if "A1" in sub_run_results and "A3" in sub_run_results:
        l1_sat = sub_run_results["A1"].mean_satisfaction_rate
        l3_sat = sub_run_results["A3"].mean_satisfaction_rate
        lines.append(f"- E1-only (L1) satisfaction: {l1_sat:.1%}")
        lines.append(f"- E3-only (L3) satisfaction: {l3_sat:.1%}")
        if l3_sat > l1_sat:
            lines.append("- **Higher expressivity correlates with higher commitment satisfaction**")
        else:
            lines.append("- No clear correlation between expressivity and satisfaction")
    lines.append("")
    
    # Cost analysis
    lines.append("### 3. Commitment Cost Analysis")
    lines.append("")
    lines.append(f"- Genesis cost: {GENESIS_COST} steps/epoch")
    lines.append(f"- Commit cap: {COMMIT_CAP} steps/epoch")
    lines.append(f"- Headroom: {COMMIT_CAP - GENESIS_COST} steps available for additional commitments")
    lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    """Run the full experiment."""
    print("=" * 60)
    print("Run A: AKI v0.6 Semantic Commitment Baseline")
    print("=" * 60)
    print()
    
    total_start = time.time()
    results = {}
    
    for sub_id, sub_config in SUB_RUNS.items():
        print(f"\n--- {sub_id}: {sub_config['label']} ---")
        result = run_sub_run(sub_id, sub_config, SEEDS)
        results[sub_id] = result
        print(f"  Mean S*: {result.mean_s_star:.1f}, Mean Sat: {result.mean_satisfaction_rate:.1%}")
    
    total_elapsed = time.time() - total_start
    
    # Generate report
    report = generate_report(results, total_elapsed)
    
    # Save report
    report_path = Path(__file__).parent.parent / "docs" / "run_a_v060_report.md"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")
    
    # Save raw data
    data_path = Path(__file__).parent.parent / "docs" / "run_a_v060_data.json"
    data = {
        "config": {
            "horizon": HORIZON,
            "epoch_size": EPOCH_SIZE,
            "steps_cap": STEPS_CAP_EPOCH,
            "commit_cap": COMMIT_CAP,
            "genesis_cost": GENESIS_COST,
            "max_commit_ttl": MAX_COMMIT_TTL,
            "seeds": SEEDS,
        },
        "sub_runs": {k: v.to_dict() for k, v in results.items()},
        "total_elapsed_s": total_elapsed,
    }
    data_path.write_text(json.dumps(data, indent=2))
    print(f"Data saved to: {data_path}")
    
    print(f"\nTotal runtime: {total_elapsed:.1f}s")
    print("Done!")


if __name__ == "__main__":
    main()
