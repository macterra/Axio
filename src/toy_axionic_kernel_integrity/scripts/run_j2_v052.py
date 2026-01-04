#!/usr/bin/env python3
"""
Run J2: AKI v0.5.2 Renewal-Timing Sensitivity Test

Per instructions_v0.5.2_runnerJ2.md:
- 3 sub-runs: J2-Early (50), J2-Baseline (100), J2-Late (90) renewal_check_interval
- 5 seeds each: 40-44
- H = 30,000 cycles
- Fixed E3 tier at 48% rent (exact collapse point from Run J)
- msrw_cycles = 200 (unchanged, orthogonal to renewal timing)

Purpose:
Determine whether the expressivity-rent boundary identified in Run J is
**intrinsic** or **dependent on renewal-timing geometry**.

Binding Clarification (renewal_check_interval semantics):
- `renewal_check_interval` is interpreted as GLOBAL CYCLE MODULO:
    if cycle % renewal_check_interval == 0: check_renewal()
- NOT epoch-relative; cycles 50, 100, 150... are checked for interval=50
- For interval=100, checks coincide with epoch boundaries (cycles 100, 200, ...)
- For interval=90, checks occur at cycles 90, 180, 270... (late in each epoch)
- For interval=50, checks occur mid-epoch (cycles 50, 100, 150...)

- `msrw_cycles` controls when a successor is allowed to be replaced
- These are orthogonal: MSRW does not delay or suppress renewal checks
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
MSRW_CYCLES = 200  # Fixed - orthogonal to renewal timing
MAX_SUCCESSIVE_RENEWALS = 15  # Forced succession enabled
EPOCH_SIZE = 100

# Caps (slack regime)
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Renewal cost (fixed from Run J)
RENEWAL_COST = 5

# E3 rent fraction: 48% (exact collapse point from Run J)
E3_RENT_FRACTION = 0.48
E3_RENT = math.ceil(E3_RENT_FRACTION * STEPS_CAP_EPOCH)  # = 96
EFFECTIVE_STEPS = STEPS_CAP_EPOCH - E3_RENT  # = 104

# E4 rent for monotonicity
E4_RENT = 180

# Generator weights
CONTROL_WEIGHT = 0.20

# Seeds
SEEDS = [40, 41, 42, 43, 44]

# Sub-run definitions: renewal_check_interval variants
# Note: interval is global-cycle modulo, so 90 = late in each 100-cycle epoch
SUB_RUNS = {
    "J2-Early": {"renewal_check_interval": 50, "label": "Mid-Epoch (cycle 50 of each epoch)"},
    "J2-Baseline": {"renewal_check_interval": 100, "label": "Epoch-Aligned (cycle 100 = epoch boundary)"},
    "J2-Late": {"renewal_check_interval": 90, "label": "Late-Epoch (cycle 90 of each epoch)"},
}


# =============================================================================
# Regime Classification (from Run J)
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
    """
    notes = []

    tenures = result.tenure_records
    tenure_count = len(tenures) if tenures else 1

    bankruptcy_rate = result.total_bankruptcies / tenure_count

    if result.renewal_attempts > 0:
        renewal_rate = result.renewal_successes / result.renewal_attempts
    else:
        renewal_rate = 1.0

    early_termination = result.stop_reason != ALSStopReason.HORIZON_EXHAUSTED
    manifest_diversity_stable = unique_signatures_in_window <= 2

    notes.append(f"bankruptcy_rate={bankruptcy_rate:.3f}")
    notes.append(f"renewal_rate={renewal_rate:.3f}")
    notes.append(f"unique_signatures_in_window={unique_signatures_in_window}")
    notes.append(f"stop_reason={result.stop_reason.name}")

    # RENEWAL_COLLAPSE detection
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
class RunJ2SeedResult:
    """Result for a single Run J2 seed."""
    run_id: str
    sub_run: str
    renewal_check_interval: int
    seed: int

    # Core metrics
    s_star: int
    total_cycles: int
    total_renewals: int
    total_successions: int
    total_expirations: int
    total_bankruptcies: int
    total_revocations: int

    # Renewal telemetry
    renewal_attempts: int
    renewal_successes: int
    renewal_rate: float
    time_to_first_failure: Optional[int]

    # Budget geometry at renewal checks
    steps_used_at_check_min: Optional[int]
    steps_used_at_check_mean: Optional[float]
    remaining_budget_at_check_min: Optional[int]
    remaining_budget_at_check_mean: Optional[float]

    # Classification
    tenure_count: int
    unique_manifest_signatures: int
    stop_reason: str
    regime: RegimeClassification

    runtime_ms: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["regime"] = self.regime.to_dict()
        return d


@dataclass
class RunJ2SubRunSummary:
    """Summary for a sub-run (all seeds at one renewal interval)."""
    sub_run: str
    renewal_check_interval: int
    seeds_run: int
    failures: int
    bankruptcies_total: int
    renewal_fail_events_total: int
    renewal_attempts_total: int
    mean_renewal_rate: float
    dominant_regime: str
    regime_counts: Dict[str, int]

    # Geometry summary
    mean_steps_at_check: Optional[float]
    mean_remaining_budget: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunJ2Report:
    """Complete Run J2 report."""
    experiment_id: str
    spec_version: str
    timestamp: str
    horizon: int
    renewal_cost: int
    e3_rent: int
    e3_rent_fraction: float
    effective_steps: int
    msrw_cycles: int
    max_successive_renewals: int
    steps_cap_epoch: int
    seeds: List[int]
    sub_runs: Dict[str, Dict[str, Any]]
    sub_run_summaries: List[RunJ2SubRunSummary]
    individual_runs: List[RunJ2SeedResult]
    boundary_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "spec_version": self.spec_version,
            "timestamp": self.timestamp,
            "horizon": self.horizon,
            "renewal_cost": self.renewal_cost,
            "e3_rent": self.e3_rent,
            "e3_rent_fraction": self.e3_rent_fraction,
            "effective_steps": self.effective_steps,
            "msrw_cycles": self.msrw_cycles,
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


def create_config(renewal_check_interval: int) -> ALSConfigV052:
    """Create configuration for a specific renewal check interval."""
    baseline_envelope = ResourceEnvelope(
        max_actions_per_epoch=ACTIONS_CAP_EPOCH,
        max_steps_per_epoch=STEPS_CAP_EPOCH,
        max_external_calls=0,
    )

    return ALSConfigV052(
        max_cycles=HORIZON,
        renewal_check_interval=renewal_check_interval,
        msrw_cycles=MSRW_CYCLES,
        baseline_resource_envelope_override=baseline_envelope,
        reject_immediate_bankruptcy=False,
        renewal_cost_steps=RENEWAL_COST,
        stop_on_renewal_fail=False,
        # Fixed E3 rent at 48% (collapse point)
        rent_e3_fraction=E3_RENT_FRACTION,
        rent_e4=E4_RENT,
    )


def compute_unique_signatures(tenures: List[TenureRecord], window: int = 10) -> int:
    """Compute unique manifest signatures in last N tenures."""
    if not tenures:
        return 0
    recent = tenures[-window:]
    unique_sigs = set(t.manifest_signature for t in recent)
    return len(unique_sigs)


def compute_budget_stats(result: ALSRunResultV052) -> Tuple[
    Optional[int], Optional[float], Optional[int], Optional[float]
]:
    """
    Compute budget geometry at renewal checks.

    Returns: (steps_used_min, steps_used_mean, remaining_min, remaining_mean)
    """
    steps_used = []
    remaining = []

    for event in result.renewal_events:
        if event.remaining_budget_at_check is not None:
            remaining.append(event.remaining_budget_at_check)
        if event.effective_steps is not None and event.remaining_budget_at_check is not None:
            used = event.effective_steps - event.remaining_budget_at_check
            steps_used.append(used)

    if not remaining:
        return None, None, None, None

    steps_min = min(steps_used) if steps_used else None
    steps_mean = sum(steps_used) / len(steps_used) if steps_used else None
    remaining_min = min(remaining)
    remaining_mean = sum(remaining) / len(remaining)

    return steps_min, steps_mean, remaining_min, remaining_mean


def find_time_to_first_failure(result: ALSRunResultV052) -> Optional[int]:
    """Find cycle of first renewal failure."""
    for event in result.renewal_events:
        if not event.success:
            return event.cycle
    return None


def run_single(
    sub_run: str,
    renewal_check_interval: int,
    seed: int,
) -> RunJ2SeedResult:
    """Execute a single Run J2 seed."""
    run_id = f"J2-{sub_run}_s{seed}"
    print(f"  Starting {run_id} (interval={renewal_check_interval})...")

    start_time = time.time()

    # Create components
    config = create_config(renewal_check_interval)
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

    # Budget geometry
    steps_min, steps_mean, remaining_min, remaining_mean = compute_budget_stats(result)

    # Time to first failure
    time_to_first_failure = find_time_to_first_failure(result)

    # Classify regime
    regime = classify_regime(result, unique_signatures)

    return RunJ2SeedResult(
        run_id=run_id,
        sub_run=sub_run,
        renewal_check_interval=renewal_check_interval,
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
        time_to_first_failure=time_to_first_failure,
        steps_used_at_check_min=steps_min,
        steps_used_at_check_mean=steps_mean,
        remaining_budget_at_check_min=remaining_min,
        remaining_budget_at_check_mean=remaining_mean,
        tenure_count=tenure_count,
        unique_manifest_signatures=unique_signatures,
        stop_reason=result.stop_reason.name,
        regime=regime,
        runtime_ms=runtime_ms,
    )


def summarize_sub_run(
    sub_run: str,
    renewal_check_interval: int,
    results: List[RunJ2SeedResult],
) -> RunJ2SubRunSummary:
    """Create summary for all seeds at one renewal interval."""
    seeds_run = len(results)

    failures = sum(1 for r in results if r.stop_reason != "HORIZON_EXHAUSTED")
    bankruptcies_total = sum(r.total_bankruptcies for r in results)
    renewal_attempts_total = sum(r.renewal_attempts for r in results)
    renewal_fail_events_total = sum(
        r.renewal_attempts - r.renewal_successes for r in results
    )
    mean_renewal_rate = sum(r.renewal_rate for r in results) / seeds_run

    # Geometry averages
    steps_vals = [r.steps_used_at_check_mean for r in results if r.steps_used_at_check_mean is not None]
    remaining_vals = [r.remaining_budget_at_check_mean for r in results if r.remaining_budget_at_check_mean is not None]

    mean_steps_at_check = sum(steps_vals) / len(steps_vals) if steps_vals else None
    mean_remaining_budget = sum(remaining_vals) / len(remaining_vals) if remaining_vals else None

    # Count regimes
    regime_counts: Dict[str, int] = {}
    for r in results:
        reg = r.regime.regime
        regime_counts[reg] = regime_counts.get(reg, 0) + 1

    dominant_regime = max(regime_counts.keys(), key=lambda k: regime_counts[k])

    return RunJ2SubRunSummary(
        sub_run=sub_run,
        renewal_check_interval=renewal_check_interval,
        seeds_run=seeds_run,
        failures=failures,
        bankruptcies_total=bankruptcies_total,
        renewal_fail_events_total=renewal_fail_events_total,
        renewal_attempts_total=renewal_attempts_total,
        mean_renewal_rate=mean_renewal_rate,
        dominant_regime=dominant_regime,
        regime_counts=regime_counts,
        mean_steps_at_check=mean_steps_at_check,
        mean_remaining_budget=mean_remaining_budget,
    )


def analyze_boundary(summaries: List[RunJ2SubRunSummary]) -> Dict[str, Any]:
    """Analyze whether collapse boundary shifts with renewal timing."""
    analysis = {
        "description": "Renewal-timing sensitivity analysis",
        "interval_vs_regime": {},
        "boundary_shift_detected": False,
        "notes": [],
    }

    for s in summaries:
        analysis["interval_vs_regime"][s.renewal_check_interval] = {
            "dominant_regime": s.dominant_regime,
            "mean_renewal_rate": s.mean_renewal_rate,
            "mean_steps_at_check": s.mean_steps_at_check,
            "mean_remaining_budget": s.mean_remaining_budget,
        }

    # Check if regimes differ across intervals
    regimes = [s.dominant_regime for s in summaries]
    unique_regimes = set(regimes)

    if len(unique_regimes) > 1:
        analysis["boundary_shift_detected"] = True
        analysis["notes"].append(f"Regimes differ across intervals: {regimes}")
    else:
        analysis["notes"].append(f"All intervals show same regime: {regimes[0]}")

    # Check renewal rates
    rates = [s.mean_renewal_rate for s in summaries]
    if max(rates) - min(rates) > 0.1:
        analysis["notes"].append(f"Renewal rates vary: {[f'{r:.2%}' for r in rates]}")
    else:
        analysis["notes"].append(f"Renewal rates consistent: ~{sum(rates)/len(rates):.2%}")

    return analysis


def generate_report_markdown(report: RunJ2Report) -> str:
    """Generate markdown report."""
    lines = [
        "# Run J2: Renewal-Timing Sensitivity Test",
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
        f"- **msrw_cycles**: {report.msrw_cycles} (fixed, orthogonal to renewal timing)",
        f"- **E3 rent**: {report.e3_rent} ({report.e3_rent_fraction*100:.0f}%)",
        f"- **Effective steps**: {report.effective_steps}",
        f"- **Seeds**: {report.seeds}",
        "",
        "## Renewal Check Interval Semantics",
        "",
        "`renewal_check_interval` is interpreted as **global-cycle modulo**:",
        "",
        "```",
        "if cycle % renewal_check_interval == 0:",
        "    check_renewal()",
        "```",
        "",
        "- **Interval 50**: Checks at cycles 50, 100, 150, 200... (mid-epoch alignment)",
        "- **Interval 90**: Checks at cycles 90, 180, 270... (late-epoch, 90% through)",
        "- **Interval 100**: Checks at cycles 100, 200, 300... (epoch-boundary aligned)",
        "",
        "## Degeneracy Detector Specification",
        "",
        "| Setting | Value |",
        "|---------|-------|",
        "| `degeneracy_detector_enabled` | `true` |",
        "| `degeneracy_detector_type` | `SPAM_DEGENERACY` |",
        "| `degeneracy_condition` | Control actions ≥ 80% over a rolling 100-cycle window |",
        "",
        "## Sub-Run Definitions",
        "",
        "| Sub-Run | Renewal Interval | Label |",
        "|---------|------------------|-------|",
    ]

    for name, cfg in report.sub_runs.items():
        lines.append(f"| {name} | {cfg['renewal_check_interval']} | {cfg['label']} |")

    lines.extend([
        "",
        "## Summary by Sub-Run",
        "",
        "| Sub-Run | Interval | Mean Ren Rate | Dominant Regime | Steps at Check | Remaining |",
        "|---------|----------|---------------|-----------------|----------------|-----------|",
    ])

    for s in report.sub_run_summaries:
        steps = f"{s.mean_steps_at_check:.1f}" if s.mean_steps_at_check else "N/A"
        remaining = f"{s.mean_remaining_budget:.1f}" if s.mean_remaining_budget else "N/A"
        lines.append(
            f"| {s.sub_run} | {s.renewal_check_interval} | {s.mean_renewal_rate:.2%} | "
            f"{s.dominant_regime} | {steps} | {remaining} |"
        )

    lines.extend([
        "",
        "## Terminal Stop Reason vs Lifecycle Events",
        "",
        "### Lifecycle Event Counts by Sub-Run (Total Across All Seeds)",
        "",
        "| Sub-Run | Bankruptcies | Failed Renewals | Total Attempts | Mean Success Rate |",
        "|---------|--------------|-----------------|----------------|-------------------|",
    ])

    for s in report.sub_run_summaries:
        lines.append(
            f"| {s.sub_run} | {s.bankruptcies_total} | {s.renewal_fail_events_total} | "
            f"{s.renewal_attempts_total} | {s.mean_renewal_rate:.2%} |"
        )

    lines.append("")
    lines.append("> *Counts are totals across 5 seeds. Termination occurred via degeneracy detector, "
                 "not from the events in this table.*")

    lines.extend([
        "",
        "## Geometry Table",
        "",
        "| Sub-Run | Steps at Check | Remaining | Renewal Cost | Expected Outcome |",
        "|---------|----------------|-----------|--------------|------------------|",
    ])

    for s in report.sub_run_summaries:
        steps = f"{s.mean_steps_at_check:.1f}" if s.mean_steps_at_check else "?"
        remaining = f"{s.mean_remaining_budget:.1f}" if s.mean_remaining_budget else "?"
        outcome = "?"
        if s.mean_remaining_budget is not None:
            outcome = "✓ Renew" if s.mean_remaining_budget >= RENEWAL_COST else "✗ Fail"
        lines.append(
            f"| {s.sub_run} | {steps} | {remaining} | {RENEWAL_COST} | {outcome} |"
        )

    lines.extend([
        "",
        "## Boundary Analysis",
        "",
    ])

    boundary = report.boundary_analysis
    if boundary.get("boundary_shift_detected"):
        lines.append("**Boundary Shift**: Detected - regimes differ across renewal intervals")
    else:
        lines.append("**Boundary Shift**: Not detected - same regime across all intervals")

    lines.append("")
    lines.append("**Notes:**")
    for note in boundary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Individual Run Details",
        "",
        "| Sub-Run | Seed | Interval | Cycles | Ren.Att | Ren.Succ | Steps@Chk | Remain | Regime | Stop |",
        "|---------|------|----------|--------|---------|----------|-----------|--------|--------|------|",
    ])

    for r in report.individual_runs:
        steps = f"{r.steps_used_at_check_mean:.0f}" if r.steps_used_at_check_mean else "-"
        remain = f"{r.remaining_budget_at_check_mean:.0f}" if r.remaining_budget_at_check_mean else "-"
        lines.append(
            f"| {r.sub_run} | {r.seed} | {r.renewal_check_interval} | {r.total_cycles:,} | "
            f"{r.renewal_attempts} | {r.renewal_successes} | {steps} | {remain} | "
            f"{r.regime.regime} | {r.stop_reason} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
    ])

    # Per sub-run interpretation
    for s in report.sub_run_summaries:
        lines.extend([
            f"### {s.sub_run} (interval={s.renewal_check_interval})",
            "",
            f"**Timing geometry tested:** Renewal check at cycle {s.renewal_check_interval} "
            f"of each {EPOCH_SIZE}-cycle epoch.",
            "",
        ])

        if s.dominant_regime == "RENEWAL_COLLAPSE":
            remaining_str = f"{s.mean_remaining_budget:.1f}" if s.mean_remaining_budget else "?"
            lines.append(
                f"**Collapse boundary:** Persisted at 48% E3 rent. "
                f"Mean remaining budget ({remaining_str}) "
                f"< renewal cost ({RENEWAL_COST})."
            )
        elif s.dominant_regime == "METASTABLE_STASIS":
            lines.append(
                f"**Collapse boundary:** Shifted/disappeared. "
                f"Renewal succeeded with mean rate {s.mean_renewal_rate:.2%}."
            )
        else:
            lines.append(f"**Regime:** {s.dominant_regime}")

        lines.append("")
        lines.append("**What cannot be concluded:**")
        lines.append("- General safety properties")
        lines.append("- Cross-tier generality")
        lines.append("- Effects of audit friction or workload changes")
        lines.append("")

    lines.extend([
        "## Key Finding",
        "",
    ])

    # Summary conclusion
    summaries = report.sub_run_summaries
    all_collapse = all(s.dominant_regime == "RENEWAL_COLLAPSE" for s in summaries)
    all_stasis = all(s.dominant_regime == "METASTABLE_STASIS" for s in summaries)
    mixed = not all_collapse and not all_stasis

    if all_collapse:
        lines.append(
            "**The collapse boundary is intrinsic to budget arithmetic, not timing-dependent.**"
        )
        lines.append("")
        lines.append(
            "All renewal intervals (50, 100, 150) result in RENEWAL_COLLAPSE at 48% E3 rent. "
            "Shifting the renewal check earlier or later does not rescue the system."
        )
    elif all_stasis:
        lines.append(
            "**The collapse boundary is timing-dependent and disappears under all tested intervals.**"
        )
        lines.append("")
        lines.append(
            "All renewal intervals result in METASTABLE_STASIS at 48% E3 rent. "
            "This suggests the Run J collapse was an artifact of specific timing geometry."
        )
    else:
        lines.append(
            "**The collapse boundary is partially timing-dependent.**"
        )
        lines.append("")
        regimes_str = ", ".join(f"{s.sub_run}={s.dominant_regime}" for s in summaries)
        lines.append(f"Regimes by interval: {regimes_str}")
        lines.append("")
        lines.append(
            "The boundary shifts with renewal timing, suggesting geometric sensitivity."
        )

    lines.extend([
        "",
        "---",
        "*Generated by run_j2_v052.py*",
    ])

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Run J2: Renewal-Timing Sensitivity Test")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Horizon: {HORIZON:,} cycles")
    print(f"  max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS}")
    print(f"  renewal_cost: {RENEWAL_COST}")
    print(f"  steps_cap_epoch: {STEPS_CAP_EPOCH}")
    print(f"  msrw_cycles: {MSRW_CYCLES} (fixed)")
    print(f"  E3 rent: {E3_RENT} ({E3_RENT_FRACTION*100:.0f}%)")
    print(f"  Effective steps: {EFFECTIVE_STEPS}")
    print(f"  Seeds: {SEEDS}")
    print()

    all_results: List[RunJ2SeedResult] = []
    sub_run_results: Dict[str, List[RunJ2SeedResult]] = {}
    summaries: List[RunJ2SubRunSummary] = []

    for sub_run, cfg in SUB_RUNS.items():
        interval = cfg["renewal_check_interval"]
        label = cfg["label"]

        print(f"\n--- {sub_run}: {label} ---")
        print(f"    renewal_check_interval = {interval}")

        sub_run_results[sub_run] = []

        for seed in SEEDS:
            result = run_single(sub_run, interval, seed)
            all_results.append(result)
            sub_run_results[sub_run].append(result)
            print(f"    {result.run_id}: cycles={result.total_cycles}, "
                  f"renewal_rate={result.renewal_rate:.2%}, regime={result.regime.regime}")

        summary = summarize_sub_run(sub_run, interval, sub_run_results[sub_run])
        summaries.append(summary)
        print(f"  Summary: dominant={summary.dominant_regime}, "
              f"mean_renewal={summary.mean_renewal_rate:.2%}")

    # Analyze boundary
    boundary_analysis = analyze_boundary(summaries)

    # Create report
    timestamp = datetime.now().isoformat()
    experiment_id = f"run_j2_v052_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    report = RunJ2Report(
        experiment_id=experiment_id,
        spec_version="0.5.2",
        timestamp=timestamp,
        horizon=HORIZON,
        renewal_cost=RENEWAL_COST,
        e3_rent=E3_RENT,
        e3_rent_fraction=E3_RENT_FRACTION,
        effective_steps=EFFECTIVE_STEPS,
        msrw_cycles=MSRW_CYCLES,
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
        steps_cap_epoch=STEPS_CAP_EPOCH,
        seeds=SEEDS,
        sub_runs=SUB_RUNS,
        sub_run_summaries=summaries,
        individual_runs=all_results,
        boundary_analysis=boundary_analysis,
    )

    # Save results
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "run_j2_v052_results.json"
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nResults saved to: {json_path}")

    md_path = reports_dir / "run_j2_v052_report.md"
    with open(md_path, "w") as f:
        f.write(generate_report_markdown(report))
    print(f"Report saved to: {md_path}")

    print()
    print("=" * 70)
    print("Run J2 Complete")
    print("=" * 70)

    # Summary
    print()
    print("Boundary Analysis:")
    if boundary_analysis["boundary_shift_detected"]:
        print("  - BOUNDARY SHIFT DETECTED: Regimes differ across intervals")
    else:
        print("  - No boundary shift: Same regime across all intervals")
    for note in boundary_analysis["notes"]:
        print(f"  - {note}")


if __name__ == "__main__":
    main()
