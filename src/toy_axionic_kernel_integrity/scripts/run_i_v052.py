#!/usr/bin/env python3
"""
Run I: AKI v0.5.2 Guardrail Removal / Institutional Debt Test

Per instructions_v0.5.2_runnerI.md:
- H = 100,000 cycles (long horizon for institutional debt accumulation)
- Seeds: 40, 41, 42
- max_successive_renewals = 1,000,000 (guardrail disabled)
- renewal_cost = 5 (safe, non-binding per H3-R results)
- Fixed E3 tier, baseline rent

Purpose:
Test whether agency can fail through accumulation, even when all local constraints
appear slack. The hypothesis is that removing the renewal cap while keeping the
local success margin comfortable will reveal systemic/emergent failure modes.

Telemetry:
- TenureRecords: mind_id, start/end cycle, e_class, renewals, manifest diversity
- Rolling entropy over last 10 tenures (Shannon entropy)
- Post-hoc degeneracy classification:
  * Authority Thrash: entropy → 0 (same mind dominates)
  * Rubber-Stamp: renewals_per_tenure → ∞ (no succession)
  * Hollowing: manifest_diversity → 1 (trivial minds)

Binding Decisions (Q1-Q4):
- Q1: Post-hoc classification only (no new runtime stop reasons)
- Q2: max_successive_renewals = 1_000_000 (large value, no type changes)
- Q3: Entropy over last 10 tenures, Shannon entropy: H = -Σ pᵢ log₂ pᵢ
- Q4: Manifest action types as diversity proxy (not trace)
"""

import sys
import json
import time
import math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
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

HORIZON = 100_000  # Long horizon for institutional debt
RENEWAL_CHECK_INTERVAL = 100
MSRW_CYCLES = 200
MAX_SUCCESSIVE_RENEWALS = 1_000_000  # Guardrail disabled (Q2 binding)
EPOCH_SIZE = 100

# Caps (slack regime per H3-R results)
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Renewal cost (safe, non-binding per H3-R boundary analysis)
RENEWAL_COST = 5

# Generator weights
CONTROL_WEIGHT = 0.20

# Seeds
SEEDS = [40, 41, 42]


# =============================================================================
# Degeneracy Classification (Post-hoc)
# =============================================================================

@dataclass
class DegeneracyClassification:
    """Post-hoc degeneracy classification for a run."""
    authority_thrash: bool  # Entropy → 0 (same mind dominates)
    rubber_stamp: bool      # renewals_per_tenure → ∞ (no succession)
    hollowing: bool         # manifest_diversity → 1 (trivial minds)

    # Diagnostic metrics
    final_entropy: float
    mean_renewals_per_tenure: float
    mean_manifest_diversity: float

    # Thresholds used
    entropy_threshold: float = 0.5  # Below this = thrash
    renewals_threshold: float = 50.0  # Above this = rubber-stamp (per tenure avg)
    diversity_threshold: float = 1.5  # Below this = hollowing

    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "authority_thrash": self.authority_thrash,
            "rubber_stamp": self.rubber_stamp,
            "hollowing": self.hollowing,
            "final_entropy": self.final_entropy,
            "mean_renewals_per_tenure": self.mean_renewals_per_tenure,
            "mean_manifest_diversity": self.mean_manifest_diversity,
            "entropy_threshold": self.entropy_threshold,
            "renewals_threshold": self.renewals_threshold,
            "diversity_threshold": self.diversity_threshold,
            "notes": self.notes,
        }


def classify_degeneracy(result: ALSRunResultV052) -> DegeneracyClassification:
    """
    Perform post-hoc degeneracy classification.

    Three modes:
    1. Authority Thrash: Same mind keeps being endorsed (low entropy)
    2. Rubber-Stamp: Single tenure with many renewals (no succession)
    3. Hollowing: Only trivial minds endorsed (low manifest diversity)
    """
    notes = []

    tenures = result.tenure_records
    entropy_samples = result.tenure_entropy_samples

    # Default values if no data
    if not tenures:
        notes.append("No tenure records collected")
        return DegeneracyClassification(
            authority_thrash=False,
            rubber_stamp=False,
            hollowing=False,
            final_entropy=0.0,
            mean_renewals_per_tenure=0.0,
            mean_manifest_diversity=0.0,
            notes=notes,
        )

    # 1. Authority Thrash: Check final entropy
    if entropy_samples:
        final_entropy = entropy_samples[-1]
    else:
        # Compute entropy manually
        recent_minds = [t.mind_id for t in tenures[-10:]]
        if len(recent_minds) >= 2:
            counts = Counter(recent_minds)
            total = len(recent_minds)
            final_entropy = -sum((c/total) * math.log2(c/total) for c in counts.values())
        else:
            final_entropy = 0.0

    entropy_threshold = 0.5
    authority_thrash = final_entropy < entropy_threshold
    if authority_thrash:
        notes.append(f"Authority Thrash detected: entropy={final_entropy:.3f} < {entropy_threshold}")

    # 2. Rubber-Stamp: High renewals per tenure
    renewals = [t.renewals_during_tenure for t in tenures]
    mean_renewals = sum(renewals) / len(renewals) if renewals else 0.0

    renewals_threshold = 50.0
    rubber_stamp = mean_renewals > renewals_threshold
    if rubber_stamp:
        notes.append(f"Rubber-Stamp detected: mean_renewals={mean_renewals:.1f} > {renewals_threshold}")

    # 3. Hollowing: Low manifest diversity
    diversities = [t.manifest_action_type_count for t in tenures]
    mean_diversity = sum(diversities) / len(diversities) if diversities else 0.0

    diversity_threshold = 1.5
    hollowing = mean_diversity < diversity_threshold
    if hollowing:
        notes.append(f"Hollowing detected: mean_diversity={mean_diversity:.2f} < {diversity_threshold}")

    if not (authority_thrash or rubber_stamp or hollowing):
        notes.append("No degeneracy mode detected")

    return DegeneracyClassification(
        authority_thrash=authority_thrash,
        rubber_stamp=rubber_stamp,
        hollowing=hollowing,
        final_entropy=final_entropy,
        mean_renewals_per_tenure=mean_renewals,
        mean_manifest_diversity=mean_diversity,
        entropy_threshold=entropy_threshold,
        renewals_threshold=renewals_threshold,
        diversity_threshold=diversity_threshold,
        notes=notes,
    )


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class RunIResult:
    """Result for a single Run I execution."""
    run_id: str
    seed: int
    s_star: int
    total_cycles: int
    total_renewals: int
    total_endorsements: int
    non_trivial_endorsements: int
    total_expirations: int
    total_revocations: int
    total_bankruptcies: int
    stop_reason: str
    tenure_count: int
    entropy_samples_count: int
    final_entropy: float
    mean_renewals_per_tenure: float
    mean_manifest_diversity: float
    degeneracy: DegeneracyClassification
    runtime_ms: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["degeneracy"] = self.degeneracy.to_dict()
        return d


@dataclass
class RunIReport:
    """Complete Run I report."""
    experiment_id: str
    spec_version: str
    timestamp: str
    horizon: int
    max_successive_renewals: int
    renewal_cost: int
    seeds: List[int]
    individual_runs: List[RunIResult]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "spec_version": self.spec_version,
            "timestamp": self.timestamp,
            "horizon": self.horizon,
            "max_successive_renewals": self.max_successive_renewals,
            "renewal_cost": self.renewal_cost,
            "seeds": self.seeds,
            "individual_runs": [r.to_dict() for r in self.individual_runs],
            "summary": self.summary,
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


def create_config() -> ALSConfigV052:
    """Create configuration for Run I."""
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
        stop_on_renewal_fail=False,  # Do NOT stop early for Run I
    )


def run_single(seed: int) -> Tuple[RunIResult, ALSRunResultV052]:
    """Execute a single Run I run."""
    run_id = f"I_s{seed}"
    print(f"  Starting {run_id} (horizon={HORIZON:,}, guardrail_disabled)...")

    start_time = time.time()

    # Create components
    config = create_config()
    harness = ALSHarnessV052(seed=seed, config=config)

    # Create base generator from harness's manifest
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

    # Set generator and run simulation
    harness.set_generator(generator)
    result = harness.run()

    runtime_ms = int((time.time() - start_time) * 1000)

    # Post-hoc degeneracy classification
    degeneracy = classify_degeneracy(result)

    # Extract tenure stats
    tenures = result.tenure_records
    tenure_count = len(tenures)
    entropy_samples = result.tenure_entropy_samples
    final_entropy = entropy_samples[-1] if entropy_samples else 0.0

    if tenures:
        mean_renewals = sum(t.renewals_during_tenure for t in tenures) / len(tenures)
        mean_diversity = sum(t.manifest_action_type_count for t in tenures) / len(tenures)
    else:
        mean_renewals = 0.0
        mean_diversity = 0.0

    run_result = RunIResult(
        run_id=run_id,
        seed=seed,
        s_star=result.s_star,
        total_cycles=result.total_cycles,
        total_renewals=result.total_renewals,
        total_endorsements=result.total_endorsements,
        non_trivial_endorsements=result.non_trivial_endorsements,
        total_expirations=result.total_expirations,
        total_revocations=result.total_revocations,
        total_bankruptcies=result.total_bankruptcies,
        stop_reason=result.stop_reason.name,
        tenure_count=tenure_count,
        entropy_samples_count=len(entropy_samples),
        final_entropy=final_entropy,
        mean_renewals_per_tenure=mean_renewals,
        mean_manifest_diversity=mean_diversity,
        degeneracy=degeneracy,
        runtime_ms=runtime_ms,
    )

    return run_result, result


def generate_summary(runs: List[RunIResult]) -> Dict[str, Any]:
    """Generate summary statistics across all runs."""
    # Terminal mode counts
    horizon_exhausted = sum(1 for r in runs if r.stop_reason == "HORIZON_EXHAUSTED")
    renewal_fail = sum(1 for r in runs if r.stop_reason == "RENEWAL_FAIL")
    bankrupt = sum(1 for r in runs if r.stop_reason == "BANKRUPTCY")
    revoked = sum(1 for r in runs if r.stop_reason == "REVOCATION")

    # Degeneracy mode counts
    authority_thrash = sum(1 for r in runs if r.degeneracy.authority_thrash)
    rubber_stamp = sum(1 for r in runs if r.degeneracy.rubber_stamp)
    hollowing = sum(1 for r in runs if r.degeneracy.hollowing)
    any_degeneracy = sum(1 for r in runs if
        r.degeneracy.authority_thrash or r.degeneracy.rubber_stamp or r.degeneracy.hollowing)

    # Aggregate stats
    mean_s_star = sum(r.s_star for r in runs) / len(runs)
    mean_cycles = sum(r.total_cycles for r in runs) / len(runs)
    mean_renewals = sum(r.total_renewals for r in runs) / len(runs)
    mean_final_entropy = sum(r.final_entropy for r in runs) / len(runs)
    mean_renewals_per_tenure = sum(r.mean_renewals_per_tenure for r in runs) / len(runs)

    return {
        "total_runs": len(runs),
        "terminal_modes": {
            "HORIZON_EXHAUSTED": horizon_exhausted,
            "RENEWAL_FAIL": renewal_fail,
            "BANKRUPTCY": bankrupt,
            "REVOCATION": revoked,
        },
        "degeneracy_modes": {
            "authority_thrash": authority_thrash,
            "rubber_stamp": rubber_stamp,
            "hollowing": hollowing,
            "any_degeneracy": any_degeneracy,
        },
        "aggregate_stats": {
            "mean_s_star": mean_s_star,
            "mean_cycles": mean_cycles,
            "mean_renewals": mean_renewals,
            "mean_final_entropy": mean_final_entropy,
            "mean_renewals_per_tenure": mean_renewals_per_tenure,
        },
    }


def generate_markdown_report(report: RunIReport) -> str:
    """Generate markdown report."""
    lines = [
        "# Run I: Guardrail Removal / Institutional Debt Test",
        "",
        f"**Experiment ID**: {report.experiment_id}",
        f"**Spec Version**: {report.spec_version}",
        f"**Timestamp**: {report.timestamp}",
        "",
        "## Configuration",
        "",
        f"- **Horizon**: {report.horizon:,} cycles",
        f"- **max_successive_renewals**: {report.max_successive_renewals:,} (guardrail disabled)",
        f"- **renewal_cost**: {report.renewal_cost}",
        f"- **Seeds**: {report.seeds}",
        "- **Attack Weights**: V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)",
        "",
        "## Hypothesis",
        "",
        "> Test whether agency can fail through accumulation, even when all local",
        "> constraints appear slack. The guardrail `max_successive_renewals` is removed",
        "> to see if systemic failure modes emerge over long horizons.",
        "",
        "## Summary",
        "",
    ]

    summary = report.summary

    lines.extend([
        "### Terminal Modes",
        "",
        "| Mode | Count |",
        "|------|-------|",
    ])
    for mode, count in summary["terminal_modes"].items():
        lines.append(f"| {mode} | {count} |")

    lines.extend([
        "",
        "### Post-hoc Degeneracy Classification",
        "",
        "| Mode | Count | Description |",
        "|------|-------|-------------|",
        f"| Authority Thrash | {summary['degeneracy_modes']['authority_thrash']} | Entropy → 0 (same mind dominates) |",
        f"| Rubber-Stamp | {summary['degeneracy_modes']['rubber_stamp']} | renewals_per_tenure → ∞ (no succession) |",
        f"| Hollowing | {summary['degeneracy_modes']['hollowing']} | manifest_diversity → 1 (trivial minds) |",
        f"| **Any Degeneracy** | {summary['degeneracy_modes']['any_degeneracy']} | |",
        "",
        "### Aggregate Statistics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Mean S* | {summary['aggregate_stats']['mean_s_star']:.1f} |",
        f"| Mean Cycles | {summary['aggregate_stats']['mean_cycles']:,.0f} |",
        f"| Mean Renewals | {summary['aggregate_stats']['mean_renewals']:,.0f} |",
        f"| Mean Final Entropy | {summary['aggregate_stats']['mean_final_entropy']:.3f} |",
        f"| Mean Renewals/Tenure | {summary['aggregate_stats']['mean_renewals_per_tenure']:.1f} |",
        "",
        "## Individual Run Details",
        "",
        "| Seed | S* | Cycles | Renewals | Tenures | Final Entropy | Stop Reason | Degeneracy |",
        "|------|----|--------|----------|---------|---------------|-------------|------------|",
    ])

    for r in report.individual_runs:
        deg_modes = []
        if r.degeneracy.authority_thrash:
            deg_modes.append("Thrash")
        if r.degeneracy.rubber_stamp:
            deg_modes.append("RubberStamp")
        if r.degeneracy.hollowing:
            deg_modes.append("Hollow")
        deg_str = ", ".join(deg_modes) if deg_modes else "None"

        lines.append(
            f"| {r.seed} | {r.s_star} | {r.total_cycles:,} | {r.total_renewals:,} | "
            f"{r.tenure_count} | {r.final_entropy:.3f} | {r.stop_reason} | {deg_str} |"
        )

    lines.extend([
        "",
        "## Degeneracy Details by Run",
        "",
    ])

    for r in report.individual_runs:
        lines.extend([
            f"### Seed {r.seed}",
            "",
            f"- **Final Entropy**: {r.degeneracy.final_entropy:.4f}",
            f"- **Mean Renewals/Tenure**: {r.degeneracy.mean_renewals_per_tenure:.2f}",
            f"- **Mean Manifest Diversity**: {r.degeneracy.mean_manifest_diversity:.2f}",
            "",
            "**Notes**:",
        ])
        for note in r.degeneracy.notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.extend([
        "## Interpretation",
        "",
    ])

    # Dynamic interpretation based on results
    summary = report.summary
    total = summary["total_runs"]
    horizon_exhausted = summary["terminal_modes"]["HORIZON_EXHAUSTED"]
    any_deg = summary["degeneracy_modes"]["any_degeneracy"]
    thrash = summary["degeneracy_modes"]["authority_thrash"]
    rubber = summary["degeneracy_modes"]["rubber_stamp"]
    hollow = summary["degeneracy_modes"]["hollowing"]
    mean_s = summary["aggregate_stats"]["mean_s_star"]
    mean_renewals = summary["aggregate_stats"]["mean_renewals_per_tenure"]

    lines.extend([
        "### Key Findings",
        "",
    ])

    if horizon_exhausted == total:
        lines.append(f"**All {total} runs reached horizon** without renewal failure, bankruptcy, or revocation.")
        lines.append("This confirms that under the tested parameters, the system is operationally stable.")
        lines.append("")

    if any_deg == total:
        lines.append(f"**All {total} runs exhibited degeneracy patterns:**")
        lines.append("")
        if thrash == total:
            lines.append(f"- **Authority Thrash** ({thrash}/{total}): The same incumbent mind dominated throughout.")
        if rubber == total:
            lines.append(f"- **Rubber-Stamp** ({rubber}/{total}): The incumbent accumulated {mean_renewals:.0f} renewals without succession.")
        if hollow > 0:
            lines.append(f"- **Hollowing** ({hollow}/{total}): Successors converged to trivial manifests.")
        lines.append("")

    if mean_s == 1.0:
        lines.extend([
            "### Analysis: The Extreme Rubber-Stamp Case",
            "",
            "With **S* = 1** across all seeds, the system endorsed exactly one successor at the start",
            "and that successor renewed indefinitely (1000 times over 100k cycles). No succession ever",
            "occurred because:",
            "",
            "1. The `max_successive_renewals` guardrail was disabled (set to 1,000,000)",
            "2. Renewal cost was non-binding (cost=5 with steps_cap=200 leaves slack)",
            "3. The E3-tier mind satisfied all attestation constraints",
            "4. No violation, bankruptcy, or expiration events triggered succession",
            "",
            "This represents **institutional calcification**: the authority structure froze in its",
            "initial configuration. While the system remained *operationally* stable (no failures),",
            "it completely failed to exercise its *renewal* capability—the very mechanism designed",
            "to enable institutional adaptation.",
            "",
        ])

    lines.extend([
        "### Implications for the Guardrail",
        "",
        "The `max_successive_renewals` guardrail exists precisely to prevent this degenerate mode.",
        "When disabled, the first competent incumbent can monopolize authority indefinitely,",
        "eliminating the system's capacity for institutional change. This validates the guardrail's",
        "design rationale: forced succession ensures the succession mechanism is exercised,",
        "even when the incumbent remains locally compliant.",
        "",
        "---",
        "*Generated by run_i_v052.py*",
    ])

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Run I: Guardrail Removal / Institutional Debt Test")
    print("=" * 70)
    print()
    print(f"Configuration:")
    print(f"  Horizon: {HORIZON:,} cycles")
    print(f"  max_successive_renewals: {MAX_SUCCESSIVE_RENEWALS:,} (guardrail disabled)")
    print(f"  renewal_cost: {RENEWAL_COST}")
    print(f"  Seeds: {SEEDS}")
    print()

    start_total = time.time()
    runs: List[RunIResult] = []
    raw_results: List[ALSRunResultV052] = []

    for seed in SEEDS:
        run_result, raw_result = run_single(seed)
        runs.append(run_result)
        raw_results.append(raw_result)

        print(f"    Completed: S*={run_result.s_star}, cycles={run_result.total_cycles:,}, "
              f"renewals={run_result.total_renewals:,}, tenures={run_result.tenure_count}")
        print(f"    Stop: {run_result.stop_reason}, Final Entropy: {run_result.final_entropy:.3f}")

        # Print degeneracy notes
        for note in run_result.degeneracy.notes:
            print(f"      - {note}")
        print()

    total_time = time.time() - start_total

    # Generate summary
    summary = generate_summary(runs)

    # Create report
    report = RunIReport(
        experiment_id=f"run_i_v052_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        spec_version="0.5.2",
        timestamp=datetime.now().isoformat(),
        horizon=HORIZON,
        max_successive_renewals=MAX_SUCCESSIVE_RENEWALS,
        renewal_cost=RENEWAL_COST,
        seeds=SEEDS,
        individual_runs=runs,
        summary=summary,
    )

    # Save results
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # JSON results
    json_path = reports_dir / "run_i_v052_results.json"
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"Results saved to: {json_path}")

    # Markdown report
    md_path = reports_dir / "run_i_v052_report.md"
    md_content = generate_markdown_report(report)
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Report saved to: {md_path}")

    # Also save raw tenure records for detailed analysis
    tenure_data = []
    for i, raw in enumerate(raw_results):
        seed = SEEDS[i]
        for t in raw.tenure_records:
            tenure_data.append({
                "seed": seed,
                "mind_id": t.mind_id,
                "start_cycle": t.start_cycle,
                "end_cycle": t.end_cycle,
                "e_class": t.e_class,
                "renewals_during_tenure": t.renewals_during_tenure,
                "manifest_action_type_count": t.manifest_action_type_count,
                "manifest_capability_groups": t.manifest_capability_groups,
                "terminal_reason": t.terminal_reason,
            })

    tenure_path = reports_dir / "run_i_v052_tenures.json"
    with open(tenure_path, "w") as f:
        json.dump(tenure_data, f, indent=2)
    print(f"Tenure records saved to: {tenure_path}")

    print()
    print("=" * 70)
    print("Run I Complete")
    print("=" * 70)
    print(f"Total time: {total_time:.1f}s")
    print()
    print("Summary:")
    print(f"  Terminal modes: {summary['terminal_modes']}")
    print(f"  Degeneracy modes: {summary['degeneracy_modes']}")
    print(f"  Mean S*: {summary['aggregate_stats']['mean_s_star']:.1f}")
    print(f"  Mean Final Entropy: {summary['aggregate_stats']['mean_final_entropy']:.3f}")


if __name__ == "__main__":
    main()
