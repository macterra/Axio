#!/usr/bin/env python3
"""
Run J: AKI v0.5.2 Expressivity Rent Escalation / Stasis–Collapse Boundary

Per instructions_v0.5.2_runnerJ.md:
- 4 sub-runs: J0 (40%), J1 (60%), J2 (75%), J3 (85%) E3 rent
- 5 seeds each: 40-44
- H = 30,000 cycles
- Fixed E3 tier
- max_successive_renewals = 15 (forced succession enabled)
- renewal_cost = 5 (non-binding)

Purpose:
Identify the first genuine boundary induced by expressivity rent.
As E3 rent increases (reducing effective steps), where does the system
transition from Growth to Stasis or Collapse?

Regime Classification (post-hoc):
- Growth (G): Bankruptcy < 5%, Renewal ≥ 90%, no collapse signatures
- Stasis (S): Renewal ≥ 90%, Bankruptcy < 5%, but flat manifest diversity
- Collapse (C): Bankruptcy ≥ 30% OR Renewal < 50% OR reproducible early termination
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
    SuccessorGenerator,
    TierFilterGenerator,
    TierUnsatisfiableError,
    V052_RUNG_G2_ATTACK_WEIGHTS,
)
from toy_aki.als.harness import (
    ALSHarnessV052,
    ALSConfigV052,
    ALSRunResultV052,
    ALSStopReason,
    TenureRecord,
)
from toy_aki.als.expressivity import (
    ExpressivityClass,
)
from toy_aki.als.working_mind import ResourceEnvelope


# =============================================================================
# Configuration Constants (Binding)
# =============================================================================

HORIZON = 30_000
RENEWAL_CHECK_INTERVAL = 100
MSRW_CYCLES = 200
MAX_SUCCESSIVE_RENEWALS = 15  # Forced succession enabled
EPOCH_SIZE = 100

# Caps (slack regime)
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Renewal cost (non-binding per H3-R)
RENEWAL_COST = 5

# Generator weights
CONTROL_WEIGHT = 0.20

# Seeds
SEEDS = [40, 41, 42, 43, 44]

# Sub-run definitions: E3 rent fractions
# Phase 2: Bisection between 45% and 50%
SUB_RUNS = {
    "J0": {"e3_rent_fraction": 0.40, "label": "Baseline (40%)"},
    "J0a": {"e3_rent_fraction": 0.45, "label": "Bisect (45%)"},
    "J0a1": {"e3_rent_fraction": 0.47, "label": "Bisect (47%)"},
    "J0a2": {"e3_rent_fraction": 0.48, "label": "Bisect (48%)"},
    "J0a3": {"e3_rent_fraction": 0.49, "label": "Bisect (49%)"},
    "J0b": {"e3_rent_fraction": 0.50, "label": "Bisect (50%)"},
    "J1": {"e3_rent_fraction": 0.60, "label": "High (60%)"},
}

# E4 rent for monotonicity (90% of cap = 180)
E4_RENT = 180


# =============================================================================
# Regime Classification
# =============================================================================

@dataclass
class RegimeClassification:
    """
    Post-hoc regime classification for a run.

    Regime Types:
    - GROWTH: Healthy renewal with behavioral diversity
    - METASTABLE_STASIS: High renewal success with low long-run behavioral diversity,
      terminating via entropy-collapse detector rather than renewal failure.
    - RENEWAL_COLLAPSE: Collapse induced by renewal infeasibility due to budget
      arithmetic; termination detected via entropy-collapse detector.
    - STABLE_LOW_MARGIN: Cannot classify definitively
    """
    regime: str  # "GROWTH", "METASTABLE_STASIS", "RENEWAL_COLLAPSE", "STABLE_LOW_MARGIN"

    # Diagnostic metrics
    bankruptcy_rate: float  # bankruptcies / tenures
    renewal_rate: float     # successful renewals / attempts
    manifest_diversity_stable: bool  # unique signatures stayed near 1-2
    early_termination: bool  # did not reach horizon

    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def classify_regime(
    result: ALSRunResultV052,
    unique_signatures_in_window: int,
) -> RegimeClassification:
    """
    Classify run into Growth/Metastable-Stasis/Renewal-Collapse/Stable-Low-Margin.

    Growth (G): Bankruptcy < 5%, Renewal ≥ 90%, no collapse signatures
    Metastable-Stasis (MS): Renewal ≥ 90%, Bankruptcy < 5%, flat manifest diversity
    Renewal-Collapse (RC): Bankruptcy ≥ 30% OR Renewal < 50% OR early termination
    Stable-Low-Margin: Cannot classify as Stasis without traces
    """
    notes = []

    tenures = result.tenure_records
    tenure_count = len(tenures) if tenures else 1  # Avoid div by zero

    # Compute bankruptcy rate
    bankruptcy_rate = result.total_bankruptcies / tenure_count

    # Compute renewal rate
    if result.renewal_attempts > 0:
        renewal_rate = result.renewal_successes / result.renewal_attempts
    else:
        renewal_rate = 1.0  # No attempts = no failures

    # Check early termination
    early_termination = result.stop_reason != ALSStopReason.HORIZON_EXHAUSTED

    # Check manifest diversity stability
    manifest_diversity_stable = unique_signatures_in_window <= 2

    notes.append(f"bankruptcy_rate={bankruptcy_rate:.3f}")
    notes.append(f"renewal_rate={renewal_rate:.3f}")
    notes.append(f"unique_signatures_in_window={unique_signatures_in_window}")
    notes.append(f"stop_reason={result.stop_reason.name}")

    # Collapse detection (now RENEWAL_COLLAPSE)
    if bankruptcy_rate >= 0.30:
        return RegimeClassification(
            regime="RENEWAL_COLLAPSE",
            bankruptcy_rate=bankruptcy_rate,
            renewal_rate=renewal_rate,
            manifest_diversity_stable=manifest_diversity_stable,
            early_termination=early_termination,
            notes=notes + ["Renewal-Collapse: bankruptcy_rate >= 30%"],
        )

    if renewal_rate < 0.50:
        return RegimeClassification(
            regime="RENEWAL_COLLAPSE",
            bankruptcy_rate=bankruptcy_rate,
            renewal_rate=renewal_rate,
            manifest_diversity_stable=manifest_diversity_stable,
            early_termination=early_termination,
            notes=notes + ["Renewal-Collapse: renewal_rate < 50%"],
        )

    if early_termination and result.stop_reason == ALSStopReason.RENEWAL_FAIL:
        return RegimeClassification(
            regime="RENEWAL_COLLAPSE",
            bankruptcy_rate=bankruptcy_rate,
            renewal_rate=renewal_rate,
            manifest_diversity_stable=manifest_diversity_stable,
            early_termination=early_termination,
            notes=notes + [f"Renewal-Collapse: early termination ({result.stop_reason.name})"],
        )

    # Growth vs Metastable-Stasis detection
    if renewal_rate >= 0.90 and bankruptcy_rate < 0.05:
        if manifest_diversity_stable and tenure_count > 5:
            return RegimeClassification(
                regime="METASTABLE_STASIS",
                bankruptcy_rate=bankruptcy_rate,
                renewal_rate=renewal_rate,
                manifest_diversity_stable=manifest_diversity_stable,
                early_termination=early_termination,
                notes=notes + ["Metastable-Stasis: high renewal, low bankruptcy, flat diversity"],
            )
        else:
            return RegimeClassification(
                regime="GROWTH",
                bankruptcy_rate=bankruptcy_rate,
                renewal_rate=renewal_rate,
                manifest_diversity_stable=manifest_diversity_stable,
                early_termination=early_termination,
                notes=notes + ["Growth: healthy metrics"],
            )

    # Default: stable but low margin
    return RegimeClassification(
        regime="STABLE_LOW_MARGIN",
        bankruptcy_rate=bankruptcy_rate,
        renewal_rate=renewal_rate,
        manifest_diversity_stable=manifest_diversity_stable,
        early_termination=early_termination,
        notes=notes + ["Stable-Low-Margin: cannot classify definitively"],
    )


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class RunJSeedResult:
    """Result for a single seed in a sub-run."""
    run_id: str
    sub_run: str
    e3_rent_fraction: float
    e3_rent: int
    effective_steps: int
    seed: int
    s_star: int
    total_cycles: int
    total_renewals: int
    total_successions: int
    total_expirations: int
    total_bankruptcies: int
    total_revocations: int
    renewal_attempts: int
    renewal_successes: int
    renewal_rate: float
    tenure_count: int
    unique_manifest_signatures: int
    stop_reason: str
    regime: RegimeClassification
    min_remaining_budget: Optional[int]
    mean_remaining_budget: Optional[float]
    runtime_ms: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["regime"] = self.regime.to_dict()
        return d


@dataclass
class RunJSubRunSummary:
    """Summary for a sub-run (all seeds at one rent level)."""
    sub_run: str
    e3_rent_fraction: float
    e3_rent: int
    effective_steps: int
    seeds_run: int
    failures: int
    bankruptcies_total: int
    mean_renewal_rate: float
    dominant_regime: str
    regime_counts: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunJReport:
    """Complete Run J report."""
    experiment_id: str
    spec_version: str
    timestamp: str
    horizon: int
    renewal_cost: int
    max_successive_renewals: int
    steps_cap_epoch: int
    seeds: List[int]
    sub_runs: Dict[str, Dict[str, Any]]
    sub_run_summaries: List[RunJSubRunSummary]
    individual_runs: List[RunJSeedResult]
    boundary_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "spec_version": self.spec_version,
            "timestamp": self.timestamp,
            "horizon": self.horizon,
            "renewal_cost": self.renewal_cost,
            "max_successive_renewals": self.max_successive_renewals,
            "steps_cap_epoch": self.steps_cap_epoch,
            "seeds": self.seeds,
            "sub_runs": self.sub_runs,
            "sub_run_summaries": [s.to_dict() for s in self.sub_run_summaries],
            "individual_runs": [r.to_dict() for r in self.individual_runs],
            "boundary_analysis": self.boundary_analysis,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def create_generator(
    sentinel_id: str,
    baseline_manifest: "WorkingMindManifest",
    seed: int,
) -> SuccessorGenerator:
    """Create generator with G2 attack weights."""
    config = GeneratorConfig(
        control_weight=CONTROL_WEIGHT,
        attack_weights=V052_RUNG_G2_ATTACK_WEIGHTS.copy(),
        excluded_attack_types={AttackSuccessorType.VIOLATION},
        max_successive_renewals_default=MAX_SUCCESSIVE_RENEWALS,
    )
    return SuccessorGenerator(
        sentinel_id=sentinel_id,
        baseline_manifest=baseline_manifest,
        seed=seed,
        config=config,
    )


def create_config(e3_rent_fraction: float) -> ALSConfigV052:
    """Create configuration for a specific E3 rent fraction."""
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=ACTIONS_CAP_EPOCH,
        max_steps_per_epoch=STEPS_CAP_EPOCH,
        max_external_calls=0,
    )

    return ALSConfigV052(
        max_cycles=HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        baseline_resource_envelope_override=baseline_envelope,
        reject_immediate_bankruptcy=False,
        renewal_cost_steps=RENEWAL_COST,
        stop_on_renewal_fail=False,
        # Run J: E3 rent fraction override
        rent_e3_fraction=e3_rent_fraction,
        # Run J: E4 rent = 180 for monotonicity when E3 = 170
        rent_e4=E4_RENT,
    )


def compute_unique_signatures(tenures: List[TenureRecord], window: int = 10) -> int:
    """Compute unique manifest signatures in last N tenures."""
    if not tenures:
        return 0
    recent = tenures[-window:]
    unique_sigs = set(t.manifest_signature for t in recent)
    return len(unique_sigs)


def compute_budget_stats(result: ALSRunResultV052) -> Tuple[Optional[int], Optional[float]]:
    """Compute min and mean remaining budget at renewal checks."""
    budgets = []
    for event in result.renewal_events:
        if event.remaining_budget_at_check is not None:
            budgets.append(event.remaining_budget_at_check)

    if not budgets:
        return None, None

    return min(budgets), sum(budgets) / len(budgets)


def run_single(
    sub_run: str,
    e3_rent_fraction: float,
    seed: int,
) -> RunJSeedResult:
    """Execute a single Run J seed."""
    run_id = f"J-{sub_run}_s{seed}"
    print(f"  Starting {run_id} (e3_rent={e3_rent_fraction*100:.0f}%)...")

    start_time = time.time()

    # Create components
    config = create_config(e3_rent_fraction)
    harness = ALSHarnessV052(seed=seed, config=config)

    # Create base generator
    base_gen = create_generator(
        sentinel_id=harness._sentinel.sentinel_id,
        baseline_manifest=harness._baseline_manifest,
        seed=seed,
    )

    # Create tier-filtered generator for E3 only
    generator = TierFilterGenerator(
        base_generator=base_gen,
        target_e_class=ExpressivityClass.E3,
        max_retries=200,
    )

    # Set generator and run
    harness.set_generator(generator)
    result = harness.run()

    runtime_ms = int((time.time() - start_time) * 1000)

    # Compute derived metrics
    tenures = result.tenure_records
    tenure_count = len(tenures)
    unique_signatures = compute_unique_signatures(tenures)

    if result.renewal_attempts > 0:
        renewal_rate = result.renewal_successes / result.renewal_attempts
    else:
        renewal_rate = 1.0

    min_budget, mean_budget = compute_budget_stats(result)

    # Compute E3 rent and effective steps
    e3_rent = math.ceil(e3_rent_fraction * STEPS_CAP_EPOCH)
    effective_steps = STEPS_CAP_EPOCH - e3_rent

    # Classify regime
    regime = classify_regime(result, unique_signatures)

    return RunJSeedResult(
        run_id=run_id,
        sub_run=sub_run,
        e3_rent_fraction=e3_rent_fraction,
        e3_rent=e3_rent,
        effective_steps=effective_steps,
        seed=seed,
        s_star=result.s_star,
        total_cycles=result.total_cycles,
        total_renewals=result.total_renewals,
        total_successions=result.total_endorsements,
        total_expirations=result.total_expirations,
        total_bankruptcies=result.total_bankruptcies,
        total_revocations=result.total_revocations,
        renewal_attempts=result.renewal_attempts,
        renewal_successes=result.renewal_successes,
        renewal_rate=renewal_rate,
        tenure_count=tenure_count,
        unique_manifest_signatures=unique_signatures,
        stop_reason=result.stop_reason.name,
        regime=regime,
        min_remaining_budget=min_budget,
        mean_remaining_budget=mean_budget,
        runtime_ms=runtime_ms,
    )


def summarize_sub_run(
    sub_run: str,
    e3_rent_fraction: float,
    results: List[RunJSeedResult],
) -> RunJSubRunSummary:
    """Create summary for all seeds at one rent level."""
    seeds_run = len(results)

    failures = sum(1 for r in results if r.stop_reason != "HORIZON_EXHAUSTED")
    bankruptcies_total = sum(r.total_bankruptcies for r in results)
    mean_renewal_rate = sum(r.renewal_rate for r in results) / seeds_run

    # Count regimes
    regime_counts: Dict[str, int] = {}
    for r in results:
        reg = r.regime.regime
        regime_counts[reg] = regime_counts.get(reg, 0) + 1

    # Dominant regime
    dominant_regime = max(regime_counts.keys(), key=lambda k: regime_counts[k])

    e3_rent = math.ceil(e3_rent_fraction * STEPS_CAP_EPOCH)
    effective_steps = STEPS_CAP_EPOCH - e3_rent

    return RunJSubRunSummary(
        sub_run=sub_run,
        e3_rent_fraction=e3_rent_fraction,
        e3_rent=e3_rent,
        effective_steps=effective_steps,
        seeds_run=seeds_run,
        failures=failures,
        bankruptcies_total=bankruptcies_total,
        mean_renewal_rate=mean_renewal_rate,
        dominant_regime=dominant_regime,
        regime_counts=regime_counts,
    )


def analyze_boundary(summaries: List[RunJSubRunSummary]) -> Dict[str, Any]:
    """Analyze regime transition boundary."""
    analysis = {
        "description": "Boundary analysis for E3 rent impact on regime",
        "rent_vs_regime": {},
        "transition_point": None,
        "notes": [],
    }

    for s in summaries:
        analysis["rent_vs_regime"][s.sub_run] = {
            "e3_rent_fraction": s.e3_rent_fraction,
            "e3_rent": s.e3_rent,
            "effective_steps": s.effective_steps,
            "dominant_regime": s.dominant_regime,
            "regime_counts": s.regime_counts,
            "failures": s.failures,
            "mean_renewal_rate": s.mean_renewal_rate,
        }

    # Find transition point
    regimes = [(s.sub_run, s.e3_rent_fraction, s.dominant_regime) for s in summaries]

    for i, (sub, frac, regime) in enumerate(regimes):
        if regime in ("COLLAPSE", "STASIS"):
            analysis["transition_point"] = {
                "sub_run": sub,
                "e3_rent_fraction": frac,
                "regime": regime,
            }
            if i > 0:
                prev_sub, prev_frac, prev_regime = regimes[i-1]
                analysis["notes"].append(
                    f"Transition detected between {prev_sub} ({prev_regime}) and {sub} ({regime})"
                )
            else:
                analysis["notes"].append(f"First tested rent level shows {regime}")
            break

    if analysis["transition_point"] is None:
        analysis["notes"].append("No transition to Stasis/Collapse observed in tested range")

        # Check if all Growth
        all_growth = all(s.dominant_regime == "GROWTH" for s in summaries)
        if all_growth:
            analysis["notes"].append("All rent levels remain in GROWTH regime - negative result")

    return analysis


def generate_markdown_report(report: RunJReport) -> str:
    """Generate markdown report."""
    lines = [
        "# Run J: Expressivity Rent Escalation / Stasis–Collapse Boundary",
        "",
        f"**Experiment ID**: {report.experiment_id}",
        f"**Spec Version**: {report.spec_version}",
        f"**Timestamp**: {report.timestamp}",
        "",
        "## Configuration",
        "",
        f"- **Horizon**: {report.horizon:,} cycles",
        f"- **max_successive_renewals**: {report.max_successive_renewals} (forced succession enabled)",
        f"- **renewal_cost**: {report.renewal_cost}",
        f"- **steps_cap_epoch**: {report.steps_cap_epoch}",
        f"- **Seeds**: {report.seeds}",
        "- **Attack Weights**: V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)",
        "- **Fixed Tier**: E3",
        "",
        "## Sub-Run Definitions",
        "",
        "| Sub-Run | E3 Rent % | E3 Rent | Effective Steps |",
        "|---------|-----------|---------|-----------------|",
    ]

    for name, info in report.sub_runs.items():
        e3_rent = math.ceil(info["e3_rent_fraction"] * report.steps_cap_epoch)
        effective = report.steps_cap_epoch - e3_rent
        lines.append(f"| {name} | {info['e3_rent_fraction']*100:.0f}% | {e3_rent} | {effective} |")

    lines.extend([
        "",
        "## Summary by Sub-Run",
        "",
        "| Sub-Run | E3 Rent % | Eff. Steps | Seeds | Failures | Bankruptcies | Mean Renewal Rate | Dominant Regime |",
        "|---------|-----------|------------|-------|----------|--------------|-------------------|-----------------|",
    ])

    for s in report.sub_run_summaries:
        lines.append(
            f"| {s.sub_run} | {s.e3_rent_fraction*100:.0f}% | {s.effective_steps} | "
            f"{s.seeds_run} | {s.failures} | {s.bankruptcies_total} | "
            f"{s.mean_renewal_rate:.2%} | {s.dominant_regime} |"
        )

    lines.extend([
        "",
        "## Boundary Analysis",
        "",
    ])

    boundary = report.boundary_analysis
    if boundary.get("transition_point"):
        tp = boundary["transition_point"]
        lines.append(f"**Transition Point**: {tp['sub_run']} at {tp['e3_rent_fraction']*100:.0f}% rent → {tp['regime']}")
    else:
        lines.append("**Transition Point**: Not observed in tested range")

    lines.append("")
    lines.append("**Notes:**")
    for note in boundary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Individual Run Details",
        "",
        "| Sub-Run | Seed | S* | Cycles | Ren.Att | Ren.Succ | Renewals | Tenures | Ren Rate | Regime | Stop |",
        "|---------|------|----|--------|---------|----------|----------|---------|----------|--------|------|",
    ])

    for r in report.individual_runs:
        lines.append(
            f"| {r.sub_run} | {r.seed} | {r.s_star} | {r.total_cycles:,} | "
            f"{r.renewal_attempts} | {r.renewal_successes} | "
            f"{r.total_renewals:,} | {r.tenure_count} | {r.renewal_rate:.2%} | "
            f"{r.regime.regime} | {r.stop_reason} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
    ])

    # Dynamic interpretation
    summaries = report.sub_run_summaries
    all_growth = all(s.dominant_regime == "GROWTH" for s in summaries)
    any_collapse = any(s.dominant_regime == "RENEWAL_COLLAPSE" for s in summaries)
    any_stasis = any(s.dominant_regime == "METASTABLE_STASIS" for s in summaries)

    if all_growth:
        lines.extend([
            "### Negative Result: No Regime Transition Observed",
            "",
            "All tested E3 rent levels (40%–85%) remained in the **GROWTH** regime.",
            "This indicates that even at 85% rent (effective_steps=30), the system",
            "maintains healthy renewal rates and low bankruptcy with forced succession.",
            "",
            "**Implications:**",
            "- The Metastable-Stasis/Renewal-Collapse boundary lies **above 85% rent** for this configuration",
            "- Forced succession prevents lock-in even under extreme rent pressure",
            "- The system has significant margin before rent becomes destabilizing",
        ])
    elif any_collapse:
        collapse_at = next(s for s in summaries if s.dominant_regime == "RENEWAL_COLLAPSE")
        lines.extend([
            f"### Renewal-Collapse Detected at {collapse_at.sub_run}",
            "",
            f"The system entered **RENEWAL_COLLAPSE** regime at {collapse_at.e3_rent_fraction*100:.0f}% E3 rent",
            f"(effective_steps={collapse_at.effective_steps}).",
            "",
            "**Characteristics:**",
            f"- Failures: {collapse_at.failures}/{collapse_at.seeds_run} seeds",
            f"- Mean renewal rate: {collapse_at.mean_renewal_rate:.2%}",
            f"- Total bankruptcies: {collapse_at.bankruptcies_total}",
        ])
    elif any_stasis:
        stasis_at = next(s for s in summaries if s.dominant_regime == "METASTABLE_STASIS")
        lines.extend([
            f"### Metastable-Stasis Detected at {stasis_at.sub_run}",
            "",
            f"The system entered **METASTABLE_STASIS** regime at {stasis_at.e3_rent_fraction*100:.0f}% E3 rent.",
            "Renewals succeed and bankruptcies are rare, but manifest diversity collapsed—",
            "the same (or very similar) successors are endorsed repeatedly.",
        ])

    lines.extend([
        "",
        "---",
        "*Generated by run_j_v052.py*",
    ])

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Run J: Expressivity Rent Escalation / Stasis–Collapse Boundary")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Horizon: {HORIZON:,} cycles")
    print(f"  max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS}")
    print(f"  renewal_cost: {RENEWAL_COST}")
    print(f"  steps_cap_epoch: {STEPS_CAP_EPOCH}")
    print(f"  Seeds: {SEEDS}")
    print()

    start_total = time.time()
    all_runs: List[RunJSeedResult] = []
    summaries: List[RunJSubRunSummary] = []

    for sub_run, params in SUB_RUNS.items():
        e3_frac = params["e3_rent_fraction"]
        e3_rent = math.ceil(e3_frac * STEPS_CAP_EPOCH)
        effective = STEPS_CAP_EPOCH - e3_rent

        print(f"\n--- {sub_run}: {params['label']} ---")
        print(f"    E3 rent = {e3_rent} ({e3_frac*100:.0f}%), effective_steps = {effective}")

        sub_run_results = []
        for seed in SEEDS:
            result = run_single(sub_run, e3_frac, seed)
            sub_run_results.append(result)
            all_runs.append(result)

            print(f"    {result.run_id}: S*={result.s_star}, cycles={result.total_cycles:,}, "
                  f"renewal_rate={result.renewal_rate:.2%}, regime={result.regime.regime}")

        summary = summarize_sub_run(sub_run, e3_frac, sub_run_results)
        summaries.append(summary)
        print(f"  Summary: dominant={summary.dominant_regime}, failures={summary.failures}, "
              f"mean_renewal={summary.mean_renewal_rate:.2%}")

    total_time = time.time() - start_total

    # Analyze boundary
    boundary_analysis = analyze_boundary(summaries)

    # Create report
    report = RunJReport(
        experiment_id=f"run_j_v052_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        spec_version="0.5.2",
        timestamp=datetime.now().isoformat(),
        horizon=HORIZON,
        renewal_cost=RENEWAL_COST,
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
        steps_cap_epoch=STEPS_CAP_EPOCH,
        seeds=SEEDS,
        sub_runs=SUB_RUNS,
        sub_run_summaries=summaries,
        individual_runs=all_runs,
        boundary_analysis=boundary_analysis,
    )

    # Save results
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "run_j_v052_results.json"
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nResults saved to: {json_path}")

    md_path = reports_dir / "run_j_v052_report.md"
    md_content = generate_markdown_report(report)
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Report saved to: {md_path}")

    print()
    print("=" * 70)
    print("Run J Complete")
    print("=" * 70)
    print(f"Total time: {total_time:.1f}s")
    print()
    print("Boundary Analysis:")
    for note in boundary_analysis.get("notes", []):
        print(f"  - {note}")


if __name__ == "__main__":
    main()
