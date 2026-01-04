#!/usr/bin/env python3
"""
Run K: AKI v0.5.2 Succession Geometry Sweep

Per instructions_v0.5.2_runnerK.md:
- 4 sub-runs: K0 (∞), K1 (100), K2 (15), K3 (3) max_successive_renewals
- 5 seeds each: 40-44
- H = 30,000 cycles
- Fixed E3 tier at 40% rent (well inside stable region)
- renewal_check_interval = 90 (non-commensurate with epoch to avoid resonance)

Purpose:
Determine whether forced, discrete authority turnover is merely a procedural
guardrail or a **constitutive stabilizer** of institutional dynamics under ALS-E.

MSRW Semantic Constraint:
- MSRW gates successor replacement only, NOT renewal checks
- Renewal is gated by budget feasibility and max_successive_renewals
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
EPOCH_SIZE = 100

# Caps (slack regime)
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Fixed geometry (non-commensurate to avoid J/J2 resonance)
RENEWAL_CHECK_INTERVAL = 90
MSRW_CYCLES = 200
RENEWAL_COST = 5

# E3 rent: 40% (well inside stable region)
E3_RENT_FRACTION = 0.40
E3_RENT = int(E3_RENT_FRACTION * STEPS_CAP_EPOCH)  # = 80
EFFECTIVE_STEPS = STEPS_CAP_EPOCH - E3_RENT  # = 120

# E4 rent for monotonicity
E4_RENT = 160

# Generator weights
CONTROL_WEIGHT = 0.20

# Seeds
SEEDS = [40, 41, 42, 43, 44]

# Sub-run definitions: max_successive_renewals variants
SUB_RUNS = {
    "K0": {"max_successive_renewals": 1_000_000, "label": "No Forced Succession (Lock-In Control)"},
    "K1": {"max_successive_renewals": 100, "label": "Low Turnover Pressure"},
    "K2": {"max_successive_renewals": 15, "label": "Moderate Turnover (Constitutional Baseline)"},
    "K3": {"max_successive_renewals": 3, "label": "High Turnover Pressure"},
}


# =============================================================================
# Regime Classification
# =============================================================================

@dataclass
class RegimeClassification:
    """
    Post-hoc regime classification for institutional dynamics.

    Regime Types:
    - LOCK_IN: tenures ≈ 1, entropy → 0, renewals dominate horizon
    - CONSTITUTIONAL_STABILITY: tenures > 1, entropy > 0, high renewal rate, no degeneracy
    - THRASH: short residence times, high tenure count, MSRW pressure or spam degeneracy
    - INDETERMINATE: Cannot classify definitively
    """
    regime: str

    # Diagnostic metrics
    tenure_count: int
    mean_residence_cycles: float
    renewal_rate: float
    entropy_proxy: float  # unique manifest signatures / total tenures

    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_entropy_proxy(tenures: List[TenureRecord]) -> float:
    """
    Compute entropy proxy as unique manifest signatures / total tenures.

    Low entropy (→ 0): single mind dominates or few unique successors
    High entropy (→ 1): diverse succession

    Special case: if only 1 tenure, entropy = 0 (no succession diversity)
    """
    if not tenures or len(tenures) <= 1:
        return 0.0  # No diversity with 0 or 1 tenure
    unique_sigs = set(t.manifest_signature for t in tenures)
    return len(unique_sigs) / len(tenures)


def classify_regime(
    result: ALSRunResultV052,
    max_successive_renewals: int,
) -> RegimeClassification:
    """
    Classify run into Lock-In/Constitutional-Stability/Thrash/Indeterminate.
    """
    notes = []

    tenures = result.tenure_records
    tenure_count = len(tenures) if tenures else 1

    # Compute mean residence
    if tenures:
        residences = [t.duration for t in tenures]
        mean_residence = sum(residences) / len(residences)
    else:
        mean_residence = result.total_cycles

    # Renewal rate
    if result.renewal_attempts > 0:
        renewal_rate = result.renewal_successes / result.renewal_attempts
    else:
        renewal_rate = 1.0

    # Entropy proxy
    entropy_proxy = compute_entropy_proxy(tenures)

    notes.append(f"tenure_count={tenure_count}")
    notes.append(f"mean_residence={mean_residence:.1f}")
    notes.append(f"renewal_rate={renewal_rate:.2%}")
    notes.append(f"entropy_proxy={entropy_proxy:.3f}")
    notes.append(f"stop_reason={result.stop_reason.name}")

    # LOCK_IN detection: very few tenures regardless of renewals
    # Key indicator: authority froze in initial configuration
    if tenure_count <= 2:
        return RegimeClassification(
            regime="LOCK_IN",
            tenure_count=tenure_count,
            mean_residence_cycles=mean_residence,
            renewal_rate=renewal_rate,
            entropy_proxy=entropy_proxy,
            notes=notes + ["Lock-In: single/dual tenure, authority frozen"],
        )

    # THRASH detection
    # Expected renewals per tenure = max_successive_renewals
    # Expected cycles per tenure ≈ max_successive_renewals * renewal_check_interval
    expected_cycles_per_tenure = max_successive_renewals * RENEWAL_CHECK_INTERVAL

    if mean_residence < expected_cycles_per_tenure * 0.5:
        # Residence is much shorter than expected - thrash
        return RegimeClassification(
            regime="THRASH",
            tenure_count=tenure_count,
            mean_residence_cycles=mean_residence,
            renewal_rate=renewal_rate,
            entropy_proxy=entropy_proxy,
            notes=notes + [f"Thrash: mean_residence ({mean_residence:.0f}) << expected ({expected_cycles_per_tenure})"],
        )

    # Check for spam degeneracy termination with low tenure diversity
    if result.stop_reason == ALSStopReason.SPAM_DEGENERACY:
        # Spam degeneracy indicates control successor dominance
        # This is a form of stasis - system stabilized into degenerate mode
        return RegimeClassification(
            regime="SPAM_STASIS",
            tenure_count=tenure_count,
            mean_residence_cycles=mean_residence,
            renewal_rate=renewal_rate,
            entropy_proxy=entropy_proxy,
            notes=notes + ["Spam Stasis: SPAM_DEGENERACY terminated (control dominance)"],
        )

    # CONSTITUTIONAL_STABILITY detection
    # Tenures > 1, reasonable entropy (even 0.1 is some diversity), high renewal
    if tenure_count > 2 and renewal_rate >= 0.75:
        return RegimeClassification(
            regime="CONSTITUTIONAL_STABILITY",
            tenure_count=tenure_count,
            mean_residence_cycles=mean_residence,
            renewal_rate=renewal_rate,
            entropy_proxy=entropy_proxy,
            notes=notes + ["Constitutional Stability: multiple tenures, high renewal"],
        )

    # INDETERMINATE
    return RegimeClassification(
        regime="INDETERMINATE",
        tenure_count=tenure_count,
        mean_residence_cycles=mean_residence,
        renewal_rate=renewal_rate,
        entropy_proxy=entropy_proxy,
        notes=notes + ["Indeterminate: does not fit clear regime pattern"],
    )


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class RunKSeedResult:
    """Result for a single Run K seed."""
    run_id: str
    sub_run: str
    max_successive_renewals: int
    seed: int

    # Core metrics
    s_star: int
    total_cycles: int
    total_renewals: int
    total_successions: int
    total_expirations: int
    total_bankruptcies: int
    total_revocations: int

    # Succession dynamics
    total_tenures: int
    mean_residence_cycles: float
    residence_times: List[int]

    # Renewal outcomes
    renewal_attempts: int
    renewal_successes: int
    renewal_rate: float
    renewals_per_tenure: float

    # Authority diversity
    entropy_proxy: float
    unique_manifest_signatures: int

    # Termination
    stop_reason: str
    degeneracy_classification: Optional[str]

    # Classification
    regime: RegimeClassification

    runtime_ms: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["regime"] = self.regime.to_dict()
        return d


@dataclass
class RunKSubRunSummary:
    """Summary for a sub-run (all seeds at one max_successive_renewals)."""
    sub_run: str
    max_successive_renewals: int
    label: str
    seeds_run: int

    # Aggregates
    mean_tenures: float
    mean_residence: float
    mean_renewal_rate: float
    mean_entropy: float

    # Regime distribution
    dominant_regime: str
    regime_counts: Dict[str, int]

    # Termination distribution
    stop_reason_counts: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunKReport:
    """Complete Run K report."""
    experiment_id: str
    spec_version: str
    timestamp: str
    horizon: int
    renewal_cost: int
    renewal_check_interval: int
    msrw_cycles: int
    e3_rent: int
    e3_rent_fraction: float
    effective_steps: int
    steps_cap_epoch: int
    seeds: List[int]
    sub_runs: Dict[str, Dict[str, Any]]
    sub_run_summaries: List[RunKSubRunSummary]
    individual_runs: List[RunKSeedResult]
    phase_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "spec_version": self.spec_version,
            "timestamp": self.timestamp,
            "horizon": self.horizon,
            "renewal_cost": self.renewal_cost,
            "renewal_check_interval": self.renewal_check_interval,
            "msrw_cycles": self.msrw_cycles,
            "e3_rent": self.e3_rent,
            "e3_rent_fraction": self.e3_rent_fraction,
            "effective_steps": self.effective_steps,
            "steps_cap_epoch": self.steps_cap_epoch,
            "seeds": self.seeds,
            "sub_runs": self.sub_runs,
            "sub_run_summaries": [s.to_dict() for s in self.sub_run_summaries],
            "individual_runs": [r.to_dict() for r in self.individual_runs],
            "phase_analysis": self.phase_analysis,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def create_generator(
    sentinel_id: str,
    baseline_manifest: "WorkingMindManifest",
    seed: int,
    max_successive_renewals: int,
) -> SuccessorGenerator:
    """Create generator with G2 attack weights."""
    config = GeneratorConfig(
        control_weight=CONTROL_WEIGHT,
        attack_weights=V052_RUNG_G2_ATTACK_WEIGHTS.copy(),
        excluded_attack_types={AttackSuccessorType.VIOLATION},
        max_successive_renewals_default=max_successive_renewals,
    )
    return SuccessorGenerator(
        sentinel_id=sentinel_id,
        baseline_manifest=baseline_manifest,
        seed=seed,
        config=config,
    )


def create_config(max_successive_renewals: int) -> ALSConfigV052:
    """Create configuration for a specific max_successive_renewals."""
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
        # Fixed E3 rent at 40% (stable region)
        rent_e3_fraction=E3_RENT_FRACTION,
        rent_e4=E4_RENT,
    )


def run_single(
    sub_run: str,
    max_successive_renewals: int,
    seed: int,
) -> RunKSeedResult:
    """Execute a single Run K seed."""
    run_id = f"K-{sub_run}_s{seed}"
    print(f"  Starting {run_id} (max_successive_renewals={max_successive_renewals})...")

    start_time = time.time()

    # Create components
    config = create_config(max_successive_renewals)
    harness = ALSHarnessV052(seed=seed, config=config)

    # Create base generator
    base_gen = create_generator(
        sentinel_id=harness._sentinel.sentinel_id,
        baseline_manifest=harness._baseline_manifest,
        seed=seed,
        max_successive_renewals=max_successive_renewals,
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
    tenure_count = len(tenures) if tenures else 1

    # Residence times
    if tenures:
        residence_times = [t.duration for t in tenures]
        mean_residence = sum(residence_times) / len(residence_times)
    else:
        residence_times = [result.total_cycles]
        mean_residence = result.total_cycles

    # Renewal rate
    if result.renewal_attempts > 0:
        renewal_rate = result.renewal_successes / result.renewal_attempts
    else:
        renewal_rate = 1.0

    # Renewals per tenure
    renewals_per_tenure = result.total_renewals / tenure_count if tenure_count > 0 else 0

    # Entropy proxy
    entropy_proxy = compute_entropy_proxy(tenures)
    unique_sigs = len(set(t.manifest_signature for t in tenures)) if tenures else 0

    # Degeneracy classification
    degeneracy = None
    if result.stop_reason == ALSStopReason.SPAM_DEGENERACY:
        degeneracy = "SPAM_DEGENERACY"
    elif result.stop_reason == ALSStopReason.ENDORSEMENT_DEGENERACY:
        degeneracy = "ENDORSEMENT_DEGENERACY"

    # Classify regime
    regime = classify_regime(result, max_successive_renewals)

    return RunKSeedResult(
        run_id=run_id,
        sub_run=sub_run,
        max_successive_renewals=max_successive_renewals,
        seed=seed,
        s_star=result.s_star,
        total_cycles=result.total_cycles,
        total_renewals=result.total_renewals,
        total_successions=result.total_endorsements,
        total_expirations=result.total_expirations,
        total_bankruptcies=result.total_bankruptcies,
        total_revocations=result.total_revocations,
        total_tenures=tenure_count,
        mean_residence_cycles=mean_residence,
        residence_times=residence_times,
        renewal_attempts=result.renewal_attempts,
        renewal_successes=result.renewal_successes,
        renewal_rate=renewal_rate,
        renewals_per_tenure=renewals_per_tenure,
        entropy_proxy=entropy_proxy,
        unique_manifest_signatures=unique_sigs,
        stop_reason=result.stop_reason.name,
        degeneracy_classification=degeneracy,
        regime=regime,
        runtime_ms=runtime_ms,
    )


def summarize_sub_run(
    sub_run: str,
    max_successive_renewals: int,
    label: str,
    results: List[RunKSeedResult],
) -> RunKSubRunSummary:
    """Create summary for all seeds at one max_successive_renewals."""
    seeds_run = len(results)

    mean_tenures = sum(r.total_tenures for r in results) / seeds_run
    mean_residence = sum(r.mean_residence_cycles for r in results) / seeds_run
    mean_renewal_rate = sum(r.renewal_rate for r in results) / seeds_run
    mean_entropy = sum(r.entropy_proxy for r in results) / seeds_run

    # Count regimes
    regime_counts: Dict[str, int] = {}
    for r in results:
        reg = r.regime.regime
        regime_counts[reg] = regime_counts.get(reg, 0) + 1

    dominant_regime = max(regime_counts.keys(), key=lambda k: regime_counts[k])

    # Count stop reasons
    stop_reason_counts: Dict[str, int] = {}
    for r in results:
        sr = r.stop_reason
        stop_reason_counts[sr] = stop_reason_counts.get(sr, 0) + 1

    return RunKSubRunSummary(
        sub_run=sub_run,
        max_successive_renewals=max_successive_renewals,
        label=label,
        seeds_run=seeds_run,
        mean_tenures=mean_tenures,
        mean_residence=mean_residence,
        mean_renewal_rate=mean_renewal_rate,
        mean_entropy=mean_entropy,
        dominant_regime=dominant_regime,
        regime_counts=regime_counts,
        stop_reason_counts=stop_reason_counts,
    )


def analyze_phase_line(summaries: List[RunKSubRunSummary]) -> Dict[str, Any]:
    """Analyze the succession pressure → regime phase line."""
    analysis = {
        "description": "Succession pressure phase line analysis",
        "phase_points": [],
        "constitutional_band": None,
        "lock_in_boundary": None,
        "thrash_boundary": None,
        "notes": [],
    }

    # Sort by max_successive_renewals (descending = increasing turnover pressure)
    sorted_summaries = sorted(summaries, key=lambda s: s.max_successive_renewals, reverse=True)

    for s in sorted_summaries:
        analysis["phase_points"].append({
            "sub_run": s.sub_run,
            "max_successive_renewals": s.max_successive_renewals,
            "dominant_regime": s.dominant_regime,
            "mean_tenures": s.mean_tenures,
            "mean_entropy": s.mean_entropy,
        })

    # Identify boundaries
    regimes = [(s.max_successive_renewals, s.dominant_regime) for s in sorted_summaries]

    # Find lock-in boundary (highest max_successive_renewals that produces LOCK_IN)
    lock_in_values = [msr for msr, reg in regimes if reg == "LOCK_IN"]
    if lock_in_values:
        analysis["lock_in_boundary"] = min(lock_in_values)
        analysis["notes"].append(f"Lock-in appears at max_successive_renewals ≥ {min(lock_in_values)}")

    # Find thrash boundary (lowest max_successive_renewals that produces THRASH)
    thrash_values = [msr for msr, reg in regimes if reg == "THRASH"]
    if thrash_values:
        analysis["thrash_boundary"] = max(thrash_values)
        analysis["notes"].append(f"Thrash appears at max_successive_renewals ≤ {max(thrash_values)}")

    # Find constitutional band
    stability_values = [msr for msr, reg in regimes if reg == "CONSTITUTIONAL_STABILITY"]
    if stability_values:
        band_min = min(stability_values)
        band_max = max(stability_values)
        analysis["constitutional_band"] = {"min": band_min, "max": band_max}
        analysis["notes"].append(f"Constitutional band: {band_min} ≤ max_successive_renewals ≤ {band_max}")

    # Determine if forced succession is constitutive or procedural
    if lock_in_values and stability_values:
        analysis["notes"].append("Forced succession appears CONSTITUTIVE: without it, lock-in occurs")
    elif not lock_in_values:
        analysis["notes"].append("Forced succession may be PROCEDURAL: no lock-in observed even without it")

    return analysis


def generate_report_markdown(report: RunKReport) -> str:
    """Generate markdown report."""
    lines = [
        "# Run K: Succession Geometry Sweep",
        "",
        f"**Experiment ID**: {report.experiment_id}",
        f"**Spec Version**: {report.spec_version}",
        f"**Timestamp**: {report.timestamp}",
        "",
        "## Configuration",
        "",
        f"- **Horizon**: {report.horizon:,} cycles",
        f"- **renewal_check_interval**: {report.renewal_check_interval} (non-commensurate with epoch)",
        f"- **msrw_cycles**: {report.msrw_cycles}",
        f"- **renewal_cost**: {report.renewal_cost}",
        f"- **steps_cap_epoch**: {report.steps_cap_epoch}",
        f"- **E3 rent**: {report.e3_rent} ({report.e3_rent_fraction*100:.0f}%)",
        f"- **Effective steps**: {report.effective_steps}",
        f"- **Seeds**: {report.seeds}",
        "",
        "## MSRW Semantic Constraint",
        "",
        "MSRW gates **successor replacement** only, not renewal checks.",
        "Renewal is determined by budget feasibility and `max_successive_renewals`.",
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
        "| Sub-Run | max_successive_renewals | Label |",
        "|---------|-------------------------|-------|",
    ]

    for name, cfg in report.sub_runs.items():
        msr = cfg['max_successive_renewals']
        msr_str = "∞" if msr >= 1_000_000 else str(msr)
        lines.append(f"| {name} | {msr_str} | {cfg['label']} |")

    lines.extend([
        "",
        "## Summary Table",
        "",
        "| Sub-Run | max_successive_renewals | Tenures | Mean Residence | Renewal Rate | Entropy | Dominant Regime | Terminal Cause |",
        "|---------|-------------------------|---------|----------------|--------------|---------|-----------------|----------------|",
    ])

    for s in report.sub_run_summaries:
        msr_str = "∞" if s.max_successive_renewals >= 1_000_000 else str(s.max_successive_renewals)
        stop_reasons = ", ".join(f"{k}({v})" for k, v in s.stop_reason_counts.items())
        lines.append(
            f"| {s.sub_run} | {msr_str} | {s.mean_tenures:.1f} | {s.mean_residence:.0f} | "
            f"{s.mean_renewal_rate:.2%} | {s.mean_entropy:.3f} | {s.dominant_regime} | {stop_reasons} |"
        )

    lines.extend([
        "",
        "## Phase Line: max_successive_renewals → Regime",
        "",
        "```",
    ])

    # ASCII phase line
    for s in sorted(report.sub_run_summaries, key=lambda x: x.max_successive_renewals, reverse=True):
        msr_str = "∞" if s.max_successive_renewals >= 1_000_000 else str(s.max_successive_renewals)
        lines.append(f"  {msr_str:>7} → {s.dominant_regime}")

    lines.append("```")

    # Phase analysis
    phase = report.phase_analysis
    lines.extend([
        "",
        "## Phase Analysis",
        "",
    ])

    if phase.get("constitutional_band"):
        band = phase["constitutional_band"]
        lines.append(f"**Constitutional Band**: {band['min']} ≤ max_successive_renewals ≤ {band['max']}")
    else:
        lines.append("**Constitutional Band**: Not identified")

    if phase.get("lock_in_boundary"):
        lines.append(f"**Lock-In Boundary**: max_successive_renewals ≥ {phase['lock_in_boundary']}")

    if phase.get("thrash_boundary"):
        lines.append(f"**Thrash Boundary**: max_successive_renewals ≤ {phase['thrash_boundary']}")

    lines.append("")
    lines.append("**Notes:**")
    for note in phase.get("notes", []):
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Individual Run Details",
        "",
        "| Sub-Run | Seed | Tenures | Residence | Renewals | Ren/Tenure | Entropy | Regime | Stop |",
        "|---------|------|---------|-----------|----------|------------|---------|--------|------|",
    ])

    for r in report.individual_runs:
        lines.append(
            f"| {r.sub_run} | {r.seed} | {r.total_tenures} | {r.mean_residence_cycles:.0f} | "
            f"{r.total_renewals} | {r.renewals_per_tenure:.1f} | {r.entropy_proxy:.3f} | "
            f"{r.regime.regime} | {r.stop_reason} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
    ])

    # Per sub-run interpretation
    for s in report.sub_run_summaries:
        msr_str = "∞" if s.max_successive_renewals >= 1_000_000 else str(s.max_successive_renewals)
        lines.extend([
            f"### {s.sub_run} (max_successive_renewals={msr_str})",
            "",
            f"**Turnover pressure tested:** {'None (infinite renewals allowed)' if s.max_successive_renewals >= 1_000_000 else f'Forced succession after {s.max_successive_renewals} renewals'}",
            "",
        ])

        if s.dominant_regime == "LOCK_IN":
            lines.append(
                f"**Outcome:** Institutional lock-in. Mean tenures={s.mean_tenures:.1f}, "
                f"entropy={s.mean_entropy:.3f}. Authority froze in initial configuration."
            )
        elif s.dominant_regime == "CONSTITUTIONAL_STABILITY":
            lines.append(
                f"**Outcome:** Constitutional stability. Mean tenures={s.mean_tenures:.1f}, "
                f"renewal rate={s.mean_renewal_rate:.2%}, entropy={s.mean_entropy:.3f}. "
                "Diverse succession with high renewal success."
            )
        elif s.dominant_regime == "THRASH":
            lines.append(
                f"**Outcome:** Authority thrash. Mean tenures={s.mean_tenures:.1f}, "
                f"mean residence={s.mean_residence:.0f} cycles. "
                "Premature turnover disrupted stability."
            )
        else:
            lines.append(f"**Outcome:** {s.dominant_regime}")

        lines.append("")
        lines.append("**What cannot be concluded:**")
        lines.append("- General governance optimality")
        lines.append("- Task competence or semantic performance")
        lines.append("- Cross-tier generality")
        lines.append("")

    lines.extend([
        "## Key Finding",
        "",
    ])

    # Summary conclusion
    summaries = report.sub_run_summaries
    has_lock_in = any(s.dominant_regime == "LOCK_IN" for s in summaries)
    has_stability = any(s.dominant_regime == "CONSTITUTIONAL_STABILITY" for s in summaries)
    has_thrash = any(s.dominant_regime == "THRASH" for s in summaries)

    if has_lock_in and has_stability:
        lines.append(
            "**Forced succession is CONSTITUTIVE, not merely procedural.**"
        )
        lines.append("")
        lines.append(
            "Without forced succession, authority locks into a single configuration. "
            "The system remains operationally stable but loses its capacity for institutional adaptation. "
            "Forced succession is required for the succession mechanism to exercise its constitutional function."
        )
    elif has_stability and has_thrash:
        lines.append(
            "**A constitutional band exists between lock-in and thrash.**"
        )
        lines.append("")
        lines.append(
            "Too much turnover pressure causes authority thrash; too little causes lock-in. "
            "The constitutional baseline (moderate forced succession) maintains stability."
        )
    elif not has_lock_in and not has_thrash:
        lines.append(
            "**No phase boundaries detected in the tested range.**"
        )
        lines.append("")
        lines.append(
            "All sub-runs produced similar regimes. The succession pressure range may need extension."
        )
    else:
        regimes_str = ", ".join(f"{s.sub_run}={s.dominant_regime}" for s in summaries)
        lines.append(f"**Mixed regime outcomes:** {regimes_str}")

    lines.extend([
        "",
        "---",
        "*Generated by run_k_v052.py*",
    ])

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Run K: Succession Geometry Sweep")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Horizon: {HORIZON:,} cycles")
    print(f"  renewal_check_interval: {RENEWAL_CHECK_INTERVAL}")
    print(f"  msrw_cycles: {MSRW_CYCLES}")
    print(f"  renewal_cost: {RENEWAL_COST}")
    print(f"  steps_cap_epoch: {STEPS_CAP_EPOCH}")
    print(f"  E3 rent: {E3_RENT} ({E3_RENT_FRACTION*100:.0f}%)")
    print(f"  Effective steps: {EFFECTIVE_STEPS}")
    print(f"  Seeds: {SEEDS}")
    print()

    all_results: List[RunKSeedResult] = []
    sub_run_results: Dict[str, List[RunKSeedResult]] = {}
    summaries: List[RunKSubRunSummary] = []

    for sub_run, cfg in SUB_RUNS.items():
        msr = cfg["max_successive_renewals"]
        label = cfg["label"]
        msr_str = "∞" if msr >= 1_000_000 else str(msr)

        print(f"\n--- {sub_run}: {label} ---")
        print(f"    max_successive_renewals = {msr_str}")

        sub_run_results[sub_run] = []

        for seed in SEEDS:
            result = run_single(sub_run, msr, seed)
            all_results.append(result)
            sub_run_results[sub_run].append(result)
            print(f"    {result.run_id}: tenures={result.total_tenures}, "
                  f"residence={result.mean_residence_cycles:.0f}, "
                  f"entropy={result.entropy_proxy:.3f}, regime={result.regime.regime}")

        summary = summarize_sub_run(sub_run, msr, label, sub_run_results[sub_run])
        summaries.append(summary)
        print(f"  Summary: dominant={summary.dominant_regime}, "
              f"mean_tenures={summary.mean_tenures:.1f}, mean_entropy={summary.mean_entropy:.3f}")

    # Analyze phase line
    phase_analysis = analyze_phase_line(summaries)

    # Create report
    timestamp = datetime.now().isoformat()
    experiment_id = f"run_k_v052_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    report = RunKReport(
        experiment_id=experiment_id,
        spec_version="0.5.2",
        timestamp=timestamp,
        horizon=HORIZON,
        renewal_cost=RENEWAL_COST,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        e3_rent=E3_RENT,
        e3_rent_fraction=E3_RENT_FRACTION,
        effective_steps=EFFECTIVE_STEPS,
        steps_cap_epoch=STEPS_CAP_EPOCH,
        seeds=SEEDS,
        sub_runs=SUB_RUNS,
        sub_run_summaries=summaries,
        individual_runs=all_results,
        phase_analysis=phase_analysis,
    )

    # Save results
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "run_k_v052_results.json"
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nResults saved to: {json_path}")

    md_path = reports_dir / "run_k_v052_report.md"
    with open(md_path, "w") as f:
        f.write(generate_report_markdown(report))
    print(f"Report saved to: {md_path}")

    print()
    print("=" * 70)
    print("Run K Complete")
    print("=" * 70)

    # Summary
    print()
    print("Phase Analysis:")
    for note in phase_analysis.get("notes", []):
        print(f"  - {note}")


if __name__ == "__main__":
    main()
