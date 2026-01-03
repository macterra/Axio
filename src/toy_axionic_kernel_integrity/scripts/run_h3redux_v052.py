#!/usr/bin/env python3
"""
Run H3-redux: AKI v0.5.2 Renewal Cost Phase Line Measurement

Per instructions_v0.5.2_runnerH3.md:
- 6 sub-runs: R4, R5, R6, R7, R8, R9 (renewal_cost = 4, 5, 6, 7, 8, 9)
- 5 seeds each: 40-44
- H = 5,000 cycles (shorter horizon for phase boundary measurement)
- Fixed E3, default rent (E3=40)
- stop_on_renewal_fail = True (early termination on first renewal failure)

Binding Decisions:
1. Stop at first renewal failure detection (not bankruptcy cascade)
2. Count only checks reaching decision gate as "attempts"
3. Use V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)
4. Terminal mode = RENEWAL_FAIL when renewal fails

Telemetry:
- renewal_attempts: number of renewal checks reaching decision gate
- renewal_successes: number of successful renewals
- renewal_success_rate: renewal_successes / renewal_attempts
- time_to_first_renewal_fail: cycle at which first renewal failure occurred
"""

import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.generator import (
    GeneratorConfig,
    AttackSuccessorType,
    ControlSuccessorType,
    SuccessorGenerator,
    TierFilterGenerator,
    TierUnsatisfiableError,
    V052_RUNG_G2_ATTACK_WEIGHTS,  # Binding: use G2 weights
)
from toy_aki.als.harness import (
    ALSHarnessV052,
    ALSConfigV052,
    ALSRunResultV052,
    ALSStopReason,
)
from toy_aki.als.expressivity import (
    ExpressivityClass,
)
from toy_aki.als.working_mind import ResourceEnvelope


# =============================================================================
# Configuration Constants (Binding)
# =============================================================================

# Shared parameters
HORIZON = 5_000  # Shorter horizon for phase boundary measurement
RENEWAL_CHECK_INTERVAL = 100
MSRW_CYCLES = 200
MAX_SUCCESSIVE_RENEWALS = 15
EPOCH_SIZE = 100

# Caps (H3-redux′ correction: 200 to introduce slack)
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Generator weights
CONTROL_WEIGHT = 0.20  # Per binding

# Seeds for all sub-runs
SEEDS = [40, 41, 42, 43, 44]

# Renewal cost values to test (H3-redux″: extended range above known-safe)
RENEWAL_COSTS = [10, 12, 15, 20]


# =============================================================================
# Result Structures
# =============================================================================

@dataclass
class H3ReduxRunResult:
    """Result for a single H3-redux execution."""
    run_id: str
    sub_run: str  # "R4", "R5", "R6", "R7", "R8", "R9"
    renewal_cost: int
    seed: int
    s_star: int
    total_cycles: int
    total_renewals: int
    renewal_attempts: int
    renewal_successes: int
    renewal_success_rate: float
    time_to_first_renewal_fail: Optional[int]
    stop_reason: str
    total_bankruptcies: int
    total_expirations: int
    total_revocations: int
    e_class_distribution: Dict[str, int]
    runtime_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class H3ReduxSubRunSummary:
    """Summary for a sub-run (all seeds at one renewal_cost)."""
    sub_run: str
    renewal_cost: int
    seeds_run: int
    seeds_reached_horizon: int
    seeds_failed_renewal: int
    seeds_bankrupt: int
    mean_renewal_success_rate: float
    mean_time_to_first_fail: Optional[float]  # None if no failures
    min_time_to_first_fail: Optional[int]
    max_time_to_first_fail: Optional[int]
    mean_renewal_attempts: float
    mean_s_star: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class H3ReduxReport:
    """Complete H3-redux report."""
    experiment_id: str
    spec_version: str
    timestamp: str
    horizon: int
    renewal_costs_tested: List[int]
    seeds_per_cost: int
    total_runs: int
    sub_run_summaries: List[H3ReduxSubRunSummary]
    individual_runs: List[H3ReduxRunResult]
    phase_boundary_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "spec_version": self.spec_version,
            "timestamp": self.timestamp,
            "horizon": self.horizon,
            "renewal_costs_tested": self.renewal_costs_tested,
            "seeds_per_cost": self.seeds_per_cost,
            "total_runs": self.total_runs,
            "sub_run_summaries": [s.to_dict() for s in self.sub_run_summaries],
            "individual_runs": [r.to_dict() for r in self.individual_runs],
            "phase_boundary_analysis": self.phase_boundary_analysis,
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


def create_config(renewal_cost: int) -> ALSConfigV052:
    """Create configuration for a specific renewal cost."""
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
        renewal_cost_steps=renewal_cost,
        stop_on_renewal_fail=True,  # Enable early termination
    )


def run_single(
    renewal_cost: int,
    seed: int,
    sub_run_label: str,
) -> H3ReduxRunResult:
    """Execute a single H3-redux run."""
    run_id = f"H3-{sub_run_label}_s{seed}"
    print(f"  Starting {run_id} (renewal_cost={renewal_cost})...")

    start_time = time.time()

    # Create components
    config = create_config(renewal_cost)
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

    # Use our own run_id for reporting
    actual_run_id = run_id

    runtime_ms = int((time.time() - start_time) * 1000)

    # Compute renewal success rate
    if result.renewal_attempts > 0:
        success_rate = result.renewal_successes / result.renewal_attempts
    else:
        success_rate = 1.0  # No attempts = no failures

    return H3ReduxRunResult(
        run_id=run_id,
        sub_run=sub_run_label,
        renewal_cost=renewal_cost,
        seed=seed,
        s_star=result.s_star,
        total_cycles=result.total_cycles,
        total_renewals=result.total_renewals,
        renewal_attempts=result.renewal_attempts,
        renewal_successes=result.renewal_successes,
        renewal_success_rate=success_rate,
        time_to_first_renewal_fail=result.time_to_first_renewal_fail,
        stop_reason=result.stop_reason.name,
        total_bankruptcies=result.total_bankruptcies,
        total_expirations=result.total_expirations,
        total_revocations=result.total_revocations,
        e_class_distribution=result.e_class_distribution,
        runtime_ms=runtime_ms,
    )


def summarize_sub_run(
    sub_run_label: str,
    renewal_cost: int,
    results: List[H3ReduxRunResult],
) -> H3ReduxSubRunSummary:
    """Create summary for all seeds at one renewal cost."""
    seeds_run = len(results)

    # Count terminal modes
    seeds_reached_horizon = sum(
        1 for r in results if r.stop_reason == "HORIZON_EXHAUSTED"
    )
    seeds_failed_renewal = sum(
        1 for r in results if r.stop_reason == "RENEWAL_FAIL"
    )
    seeds_bankrupt = sum(
        1 for r in results if r.stop_reason not in ("HORIZON_EXHAUSTED", "RENEWAL_FAIL")
    )

    # Mean renewal success rate
    mean_success_rate = sum(r.renewal_success_rate for r in results) / seeds_run

    # Time to first failure stats
    fail_times = [r.time_to_first_renewal_fail for r in results if r.time_to_first_renewal_fail is not None]
    if fail_times:
        mean_fail_time = sum(fail_times) / len(fail_times)
        min_fail_time = min(fail_times)
        max_fail_time = max(fail_times)
    else:
        mean_fail_time = None
        min_fail_time = None
        max_fail_time = None

    # Mean attempts and S*
    mean_attempts = sum(r.renewal_attempts for r in results) / seeds_run
    mean_s_star = sum(r.s_star for r in results) / seeds_run

    return H3ReduxSubRunSummary(
        sub_run=sub_run_label,
        renewal_cost=renewal_cost,
        seeds_run=seeds_run,
        seeds_reached_horizon=seeds_reached_horizon,
        seeds_failed_renewal=seeds_failed_renewal,
        seeds_bankrupt=seeds_bankrupt,
        mean_renewal_success_rate=mean_success_rate,
        mean_time_to_first_fail=mean_fail_time,
        min_time_to_first_fail=min_fail_time,
        max_time_to_first_fail=max_fail_time,
        mean_renewal_attempts=mean_attempts,
        mean_s_star=mean_s_star,
    )


def analyze_phase_boundary(
    summaries: List[H3ReduxSubRunSummary],
) -> Dict[str, Any]:
    """Analyze phase boundary from sub-run summaries."""
    analysis = {
        "description": "Phase boundary analysis for renewal cost impact on system stability",
        "renewal_cost_vs_failure_rate": {},
        "critical_threshold": None,
        "notes": [],
    }

    # Build failure rate table
    for s in summaries:
        failure_rate = s.seeds_failed_renewal / s.seeds_run if s.seeds_run > 0 else 0.0
        analysis["renewal_cost_vs_failure_rate"][s.renewal_cost] = {
            "failure_rate": failure_rate,
            "failures": s.seeds_failed_renewal,
            "total": s.seeds_run,
            "mean_success_rate": s.mean_renewal_success_rate,
            "mean_time_to_fail": s.mean_time_to_first_fail,
        }

    # Find critical threshold (first cost with >50% failure rate)
    for s in summaries:
        failure_rate = s.seeds_failed_renewal / s.seeds_run if s.seeds_run > 0 else 0.0
        if failure_rate > 0.5:
            analysis["critical_threshold"] = s.renewal_cost
            analysis["notes"].append(
                f"Critical threshold at renewal_cost={s.renewal_cost}: "
                f"{failure_rate*100:.1f}% failure rate"
            )
            break

    # Additional notes
    if analysis["critical_threshold"] is None:
        analysis["notes"].append("No critical threshold found in tested range (all costs < 50% failure)")

    # Check for gradient (only note if there's actual variation)
    costs = sorted(analysis["renewal_cost_vs_failure_rate"].keys())
    rates = [analysis["renewal_cost_vs_failure_rate"][c]["failure_rate"] for c in costs]
    if all(r == 0 for r in rates):
        analysis["notes"].append("No increase in renewal failure was observed across the tested renewal_cost range. Renewal success rate remained constant.")
    elif all(r == 1.0 for r in rates):
        analysis["notes"].append("All renewal attempts failed across the tested range (100% failure rate).")
    elif rates == sorted(rates) and rates[0] != rates[-1]:
        analysis["notes"].append("Failure rate increases with renewal_cost.")
    elif rates != sorted(rates):
        analysis["notes"].append("WARNING: Non-monotonic failure rate detected.")

    return analysis


def generate_markdown_report(report: H3ReduxReport) -> str:
    """Generate markdown report."""
    lines = [
        "# Run H3-redux: Renewal Cost Phase Line Measurement",
        "",
        f"**Experiment ID**: {report.experiment_id}",
        f"**Spec Version**: {report.spec_version}",
        f"**Timestamp**: {report.timestamp}",
        "",
        "## Configuration",
        "",
        f"- **Horizon**: {report.horizon:,} cycles",
        f"- **Renewal Costs Tested**: {report.renewal_costs_tested}",
        f"- **Seeds per Cost**: {report.seeds_per_cost}",
        f"- **Total Runs**: {report.total_runs}",
        "- **Attack Weights**: V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)",
        "- **Stop Mode**: stop_on_renewal_fail=True (early termination)",
        "",
        "## Summary by Renewal Cost",
        "",
        "| Cost | Seeds | Horizon | Fail | Bankrupt | Mean Success Rate | Mean Fail Time |",
        "|------|-------|---------|------|----------|-------------------|----------------|",
    ]

    for s in report.sub_run_summaries:
        fail_time_str = f"{s.mean_time_to_first_fail:.0f}" if s.mean_time_to_first_fail else "N/A"
        lines.append(
            f"| {s.renewal_cost} | {s.seeds_run} | {s.seeds_reached_horizon} | "
            f"{s.seeds_failed_renewal} | {s.seeds_bankrupt} | "
            f"{s.mean_renewal_success_rate:.2%} | {fail_time_str} |"
        )

    lines.extend([
        "",
        "## Phase Boundary Analysis",
        "",
    ])

    analysis = report.phase_boundary_analysis
    if analysis["critical_threshold"]:
        lines.append(f"**Critical Threshold**: renewal_cost = {analysis['critical_threshold']}")
    else:
        lines.append("**Critical Threshold**: Not found in tested range")

    lines.extend([
        "",
        "### Failure Rate by Renewal Cost",
        "",
        "| Cost | Failure Rate | Mean Time to Fail |",
        "|------|--------------|-------------------|",
    ])

    for cost, data in sorted(analysis["renewal_cost_vs_failure_rate"].items()):
        fail_time_str = f"{data['mean_time_to_fail']:.0f}" if data['mean_time_to_fail'] else "N/A"
        lines.append(f"| {cost} | {data['failure_rate']:.0%} | {fail_time_str} |")

    lines.extend([
        "",
        "### Notes",
        "",
    ])
    for note in analysis["notes"]:
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Individual Run Results",
        "",
        "| Run ID | Cost | Seed | S* | Cycles | Attempts | Successes | Rate | Fail Time | Stop Reason |",
        "|--------|------|------|----|--------|----------|-----------|------|-----------|-------------|",
    ])

    for r in report.individual_runs:
        fail_time_str = str(r.time_to_first_renewal_fail) if r.time_to_first_renewal_fail else "N/A"
        lines.append(
            f"| {r.run_id} | {r.renewal_cost} | {r.seed} | {r.s_star} | "
            f"{r.total_cycles} | {r.renewal_attempts} | {r.renewal_successes} | "
            f"{r.renewal_success_rate:.2%} | {fail_time_str} | {r.stop_reason} |"
        )

    lines.extend([
        "",
        "---",
        "",
        f"*Report generated {report.timestamp}*",
    ])

    return "\n".join(lines)


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Run H3-redux″ experiment: extended sweep above known-safe range."""
    print("=" * 70)
    print("Run H3-redux″: Extended Renewal Cost Sweep")
    print(f"  steps_cap_epoch = {STEPS_CAP_EPOCH}")
    print(f"  renewal_costs = {RENEWAL_COSTS}")
    print("=" * 70)
    print()

    timestamp = datetime.now().isoformat()
    experiment_id = f"H3-redux-double-prime_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    all_results: List[H3ReduxRunResult] = []
    sub_run_summaries: List[H3ReduxSubRunSummary] = []

    # Run each renewal cost level
    for renewal_cost in RENEWAL_COSTS:
        sub_run_label = f"R{renewal_cost}"
        print(f"\n[{sub_run_label}] Testing renewal_cost = {renewal_cost}")
        print("-" * 50)

        sub_run_results: List[H3ReduxRunResult] = []

        for seed in SEEDS:
            result = run_single(
                renewal_cost=renewal_cost,
                seed=seed,
                sub_run_label=sub_run_label,
            )
            sub_run_results.append(result)
            all_results.append(result)

            # Print immediate result
            fail_indicator = "FAIL" if result.stop_reason == "RENEWAL_FAIL" else result.stop_reason
            print(
                f"    Seed {seed}: S*={result.s_star}, "
                f"attempts={result.renewal_attempts}, "
                f"rate={result.renewal_success_rate:.2%}, "
                f"[{fail_indicator}]"
            )

        # Summarize sub-run
        summary = summarize_sub_run(sub_run_label, renewal_cost, sub_run_results)
        sub_run_summaries.append(summary)

        print(f"  Sub-run {sub_run_label} complete: "
              f"{summary.seeds_failed_renewal}/{summary.seeds_run} failed, "
              f"mean_rate={summary.mean_renewal_success_rate:.2%}")

    # Analyze phase boundary
    phase_analysis = analyze_phase_boundary(sub_run_summaries)

    # Create report
    report = H3ReduxReport(
        experiment_id=experiment_id,
        spec_version="0.5.2",
        timestamp=timestamp,
        horizon=HORIZON,
        renewal_costs_tested=RENEWAL_COSTS,
        seeds_per_cost=len(SEEDS),
        total_runs=len(all_results),
        sub_run_summaries=sub_run_summaries,
        individual_runs=all_results,
        phase_boundary_analysis=phase_analysis,
    )

    # Save JSON results
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "run_h3redux_double_prime_v052_results.json"
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nResults saved to: {json_path}")

    # Save markdown report
    md_path = reports_dir / "run_h3redux_double_prime_v052_report.md"
    with open(md_path, "w") as f:
        f.write(generate_markdown_report(report))
    print(f"Report saved to: {md_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("PHASE BOUNDARY SUMMARY")
    print("=" * 70)
    print()
    print("Failure Rate by Renewal Cost:")
    for cost, data in sorted(phase_analysis["renewal_cost_vs_failure_rate"].items()):
        bar = "█" * int(data["failure_rate"] * 20)
        print(f"  Cost {cost}: {data['failure_rate']:5.0%} {bar}")

    if phase_analysis["critical_threshold"]:
        print(f"\n⚠️  Critical threshold: renewal_cost = {phase_analysis['critical_threshold']}")
    else:
        print("\n✓ No critical threshold found in range [4-9]")

    print("\n" + "=" * 70)
    print("H3-redux complete.")


if __name__ == "__main__":
    main()
