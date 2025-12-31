#!/usr/bin/env python3
"""
AKI v0.3.2 H=10,000 Stress Regime Experiment Runner.

Executes the preregistered experiment per instructions_v032_runner.md.

Matrix:
- H = 10,000 only
- Seeds: {42, 43, 44}
- Variants per seed: v0.3.2.a (control), v0.3.2.b (hollow+fuzzer), v0.3.2.d (compress+fuzzer)

Execution order per seed: control → b → d
"""

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.attacks.kns.boundary_fuzzer import (
    AdaptiveBoundaryFuzzer,
    K_PERSIST,
    PhasePWeights,
    PhaseXWeights,
    FuzzerPhase,
)
from toy_aki.kernel.degeneracy_diagnosis import DegeneracyDiagnosis
from toy_aki.harness.v032_runner import (
    V032ExperimentRunner,
    V032RunResult,
    DEGENERACY_GRACE_WINDOW,
    DIVERGENCE_MIN_SAMPLES,
)
from toy_aki.harness.v032_matrix import (
    V032Variant,
    V032RunSpec,
    V032RunMatrix,
)


@dataclass
class Preconditions:
    """Precondition verification record."""
    git_commit: str
    python_version: str
    os_info: str
    cpu_arch: str
    psutil_available: bool
    k_persist: int
    degeneracy_grace_window: int
    divergence_ratio: float
    min_samples: int
    phase_p_weights: dict
    phase_x_weights: dict
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunRecord:
    """Complete record for a single run."""
    # Structural
    seed: int
    variant: str
    horizon: int
    stop_reason: str
    r_star: int
    phase_transition_step: Optional[int]
    phase_at_stop: str
    total_steps: int

    # Failure / Degeneracy
    failure_signature: Optional[str]
    degenerate: bool
    degeneracy_diagnosis: Optional[str]

    # Resource divergence
    divergence_flag: str  # True / False / InsufficientData
    divergence_k: Optional[int]
    divergence_ratio: Optional[float]
    median_synthesis_by_r: Dict[str, float]
    median_step_time_by_r: Dict[str, float]
    peak_rss_by_r: Dict[str, int]

    # Pressure
    max_consecutive_flag_steps: int
    total_flag_active_steps: int
    max_persist_counter: int

    # Timing
    duration_ms: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExperimentReport:
    """Complete experiment report."""
    experiment_id: str
    timestamp: str
    preconditions: Preconditions
    run_records: List[RunRecord]
    seeds: List[int]
    variants: List[str]
    horizon: int
    total_runs: int
    total_duration_ms: int

    # Summary stats
    control_r_stars: Dict[int, int]  # seed -> R*
    simulator_b_r_stars: Dict[int, int]
    simulator_d_r_stars: Dict[int, int]
    phase_transitions: int
    failures: int
    degeneracies: int
    divergent_runs: int

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "preconditions": self.preconditions.to_dict(),
            "run_records": [r.to_dict() for r in self.run_records],
            "seeds": self.seeds,
            "variants": self.variants,
            "horizon": self.horizon,
            "total_runs": self.total_runs,
            "total_duration_ms": self.total_duration_ms,
            "summary": {
                "control_r_stars": self.control_r_stars,
                "simulator_b_r_stars": self.simulator_b_r_stars,
                "simulator_d_r_stars": self.simulator_d_r_stars,
                "phase_transitions": self.phase_transitions,
                "failures": self.failures,
                "degeneracies": self.degeneracies,
                "divergent_runs": self.divergent_runs,
            },
        }


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()[:12]
    except Exception:
        return "unknown"


def check_psutil() -> bool:
    """Check if psutil is available."""
    try:
        import psutil
        return True
    except ImportError:
        return False


def verify_preconditions() -> Preconditions:
    """Verify and record all preconditions."""
    phase_p = PhasePWeights()
    phase_x = PhaseXWeights()

    return Preconditions(
        git_commit=get_git_commit(),
        python_version=platform.python_version(),
        os_info=f"{platform.system()} {platform.release()}",
        cpu_arch=platform.machine(),
        psutil_available=check_psutil(),
        k_persist=K_PERSIST,
        degeneracy_grace_window=DEGENERACY_GRACE_WINDOW,
        divergence_ratio=10.0,
        min_samples=DIVERGENCE_MIN_SAMPLES,
        phase_p_weights=phase_p.to_dict(),
        phase_x_weights=phase_x.to_dict(),
        timestamp=datetime.now().isoformat(),
    )


def run_result_to_record(result: V032RunResult) -> RunRecord:
    """Convert V032RunResult to RunRecord."""
    # Determine stop reason
    if result.failure_detected:
        stop_reason = "STOP_FAILURE_SIGNATURE"
    elif result.is_degenerate:
        stop_reason = "STOP_DEGENERACY"
    else:
        stop_reason = "STOP_HORIZON_EXHAUSTED"

    # Extract divergence info
    if result.divergence_result:
        if result.divergence_result.insufficient_data:
            divergence_flag = "InsufficientData"
        elif result.divergence_result.is_divergent:
            divergence_flag = "True"
        else:
            divergence_flag = "False"
        divergence_k = result.divergence_result.divergence_k
        divergence_ratio = result.divergence_result.ratio

        # Extract curves
        curve = result.divergence_result.curve
        median_synthesis = {str(k): v for k, v in curve.median_synthesis_time_ms.items()}
        median_step = {str(k): v for k, v in curve.median_step_time_ms.items()}
        peak_rss = {str(k): v for k, v in curve.peak_memory_bytes.items()}
    else:
        divergence_flag = "InsufficientData"
        divergence_k = None
        divergence_ratio = None
        median_synthesis = {}
        median_step = {}
        peak_rss = {}

    # Extract degeneracy diagnosis
    if result.degeneracy_diagnosis:
        degeneracy_diagnosis = result.degeneracy_diagnosis.diagnosis.name
    else:
        degeneracy_diagnosis = None

    return RunRecord(
        seed=result.seed,
        variant=result.variant,
        horizon=result.horizon,
        stop_reason=stop_reason,
        r_star=result.r_star,
        phase_transition_step=result.phase_transition_step,
        phase_at_stop=result.phase_at_end.name,
        total_steps=result.total_steps,
        failure_signature=result.failure_signature.name if result.failure_signature else None,
        degenerate=result.is_degenerate,
        degeneracy_diagnosis=degeneracy_diagnosis,
        divergence_flag=divergence_flag,
        divergence_k=divergence_k,
        divergence_ratio=divergence_ratio,
        median_synthesis_by_r=median_synthesis,
        median_step_time_by_r=median_step,
        peak_rss_by_r=peak_rss,
        max_consecutive_flag_steps=result.max_consecutive_flag_steps,
        total_flag_active_steps=result.total_flag_active_steps,
        max_persist_counter=result.max_persist_counter,
        duration_ms=result.duration_ms,
    )


def run_experiment(verbose: bool = True) -> ExperimentReport:
    """
    Run the H=10,000 stress experiment per preregistration.

    Matrix:
    - H = 10,000
    - Seeds: {42, 43, 44}
    - Variants: a (control), b (hollow+fuzzer), d (compress+fuzzer)
    - Order per seed: control → b → d
    """
    start_time = current_time_ms()
    experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Verify preconditions
    print("=" * 60)
    print("AKI v0.3.2 H=10,000 Stress Experiment")
    print("=" * 60)
    print()

    preconditions = verify_preconditions()
    print("Preconditions verified:")
    print(f"  Git commit: {preconditions.git_commit}")
    print(f"  Python: {preconditions.python_version}")
    print(f"  OS: {preconditions.os_info}")
    print(f"  K_persist: {preconditions.k_persist}")
    print(f"  Degeneracy window: {preconditions.degeneracy_grace_window}")
    print(f"  Divergence ratio: {preconditions.divergence_ratio}×")
    print(f"  Min samples: {preconditions.min_samples}")
    print(f"  psutil: {preconditions.psutil_available}")
    print()

    # Fixed matrix per preregistration
    HORIZON = 10_000
    SEEDS = [42, 43, 44]
    # Order: control (a) → b → d
    VARIANTS = [
        V032Variant.V032A_KERNEL_COHERENT,  # control
        V032Variant.V032B_HOLLOW_FUZZER,     # hollow + fuzzer
        V032Variant.V032D_COMPRESS_FUZZER,   # compress + fuzzer
    ]

    total_runs = len(SEEDS) * len(VARIANTS)
    print(f"Matrix: {total_runs} runs ({len(SEEDS)} seeds × {len(VARIANTS)} variants)")
    print(f"Horizon: {HORIZON}")
    print()

    # Create runner
    runner = V032ExperimentRunner(
        base_seed=42,
        verbose=verbose,
        degeneracy_grace_window=DEGENERACY_GRACE_WINDOW,
        k_persist=K_PERSIST,
        divergence_min_samples=DIVERGENCE_MIN_SAMPLES,
    )

    # Execute runs
    run_records: List[RunRecord] = []
    control_r_stars: Dict[int, int] = {}
    simulator_b_r_stars: Dict[int, int] = {}
    simulator_d_r_stars: Dict[int, int] = {}

    run_num = 0
    for seed in SEEDS:
        print(f"\n{'='*60}")
        print(f"SEED {seed}")
        print(f"{'='*60}")

        # Generate scenario ID (deterministic)
        matrix = V032RunMatrix(seeds=[seed], horizons=[HORIZON])
        scenario_id = matrix.generate_scenario_id(seed, HORIZON)

        for variant in VARIANTS:
            run_num += 1
            variant_name = variant.value

            print(f"\n[{run_num}/{total_runs}] {variant_name} (seed={seed}, H={HORIZON})")
            print("-" * 40)

            # Create run spec
            spec = V032RunSpec(
                seed=seed,
                horizon=HORIZON,
                variant=variant,
                scenario_id=scenario_id,
                use_stress=True,
            )

            # Execute run
            result = runner.run_single(spec)

            # Convert to record
            record = run_result_to_record(result)
            run_records.append(record)

            # Track R* by variant
            if variant == V032Variant.V032A_KERNEL_COHERENT:
                control_r_stars[seed] = record.r_star
            elif variant == V032Variant.V032B_HOLLOW_FUZZER:
                simulator_b_r_stars[seed] = record.r_star
            elif variant == V032Variant.V032D_COMPRESS_FUZZER:
                simulator_d_r_stars[seed] = record.r_star

            # Print summary
            print(f"  R*: {record.r_star}")
            print(f"  Stop: {record.stop_reason}")
            print(f"  Phase: {record.phase_at_stop}")
            print(f"  Steps: {record.total_steps}")
            if record.phase_transition_step:
                print(f"  Phase transition: step {record.phase_transition_step}")
            if record.failure_signature:
                print(f"  Failure: {record.failure_signature}")
            if record.degenerate:
                print(f"  Degeneracy: {record.degeneracy_diagnosis}")
            print(f"  Divergent: {record.divergence_flag}")
            print(f"  Duration: {record.duration_ms}ms")

    # Compute summary stats
    total_duration = current_time_ms() - start_time
    phase_transitions = sum(1 for r in run_records if r.phase_transition_step is not None)
    failures = sum(1 for r in run_records if r.failure_signature is not None)
    degeneracies = sum(1 for r in run_records if r.degenerate)
    divergent = sum(1 for r in run_records if r.divergence_flag == "True")

    # Create report
    report = ExperimentReport(
        experiment_id=experiment_id,
        timestamp=datetime.now().isoformat(),
        preconditions=preconditions,
        run_records=run_records,
        seeds=SEEDS,
        variants=[v.value for v in VARIANTS],
        horizon=HORIZON,
        total_runs=total_runs,
        total_duration_ms=total_duration,
        control_r_stars=control_r_stars,
        simulator_b_r_stars=simulator_b_r_stars,
        simulator_d_r_stars=simulator_d_r_stars,
        phase_transitions=phase_transitions,
        failures=failures,
        degeneracies=degeneracies,
        divergent_runs=divergent,
    )

    # Print final summary
    print()
    print("=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)
    print(f"Total duration: {total_duration}ms ({total_duration/1000:.1f}s)")
    print(f"Total runs: {total_runs}")
    print(f"Phase transitions: {phase_transitions}")
    print(f"Failures: {failures}")
    print(f"Degeneracies: {degeneracies}")
    print(f"Divergent runs: {divergent}")
    print()
    print("R* by seed:")
    for seed in SEEDS:
        c = control_r_stars.get(seed, "?")
        b = simulator_b_r_stars.get(seed, "?")
        d = simulator_d_r_stars.get(seed, "?")
        print(f"  Seed {seed}: control={c}, b={b}, d={d}")

    return report


def save_report(report: ExperimentReport, output_dir: Path) -> Path:
    """Save report to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"experiment_H10000_{report.experiment_id}.json"
    filepath = output_dir / filename

    with open(filepath, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    return filepath


def generate_markdown_report(report: ExperimentReport) -> str:
    """Generate markdown report from experiment data."""
    lines = []

    lines.append("# AKI v0.3.2 H=10,000 Stress Experiment Report")
    lines.append("")
    lines.append(f"**Experiment ID:** {report.experiment_id}")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append(f"**Duration:** {report.total_duration_ms}ms ({report.total_duration_ms/1000:.1f}s)")
    lines.append("")

    # Preconditions
    lines.append("## Preconditions")
    lines.append("")
    pre = report.preconditions
    lines.append(f"- Git commit: `{pre.git_commit}`")
    lines.append(f"- Python: {pre.python_version}")
    lines.append(f"- OS: {pre.os_info}")
    lines.append(f"- CPU: {pre.cpu_arch}")
    lines.append(f"- psutil: {pre.psutil_available}")
    lines.append(f"- K_persist: {pre.k_persist}")
    lines.append(f"- Degeneracy grace window: {pre.degeneracy_grace_window}")
    lines.append(f"- Divergence ratio: {pre.divergence_ratio}×")
    lines.append(f"- Min samples: {pre.min_samples}")
    lines.append("")

    # Matrix
    lines.append("## Run Matrix")
    lines.append("")
    lines.append(f"- Horizon: {report.horizon}")
    lines.append(f"- Seeds: {report.seeds}")
    lines.append(f"- Variants: {report.variants}")
    lines.append(f"- Total runs: {report.total_runs}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Phase transitions (P→X): {report.phase_transitions}/{report.total_runs}")
    lines.append(f"- Failure signatures: {report.failures}/{report.total_runs}")
    lines.append(f"- Degeneracies: {report.degeneracies}/{report.total_runs}")
    lines.append(f"- Resource divergent: {report.divergent_runs}/{report.total_runs}")
    lines.append("")

    # R* table
    lines.append("## R* by Seed and Variant")
    lines.append("")
    lines.append("| Seed | Control (a) | Hollow+Fuzzer (b) | Compress+Fuzzer (d) |")
    lines.append("|------|-------------|-------------------|---------------------|")
    for seed in report.seeds:
        c = report.control_r_stars.get(seed, "—")
        b = report.simulator_b_r_stars.get(seed, "—")
        d = report.simulator_d_r_stars.get(seed, "—")
        lines.append(f"| {seed} | {c} | {b} | {d} |")
    lines.append("")

    # Per-run details
    lines.append("## Per-Run Details")
    lines.append("")

    for record in report.run_records:
        lines.append(f"### {record.variant} (seed={record.seed})")
        lines.append("")
        lines.append(f"- **R*:** {record.r_star}")
        lines.append(f"- **Stop reason:** {record.stop_reason}")
        lines.append(f"- **Total steps:** {record.total_steps}")
        lines.append(f"- **Phase at stop:** {record.phase_at_stop}")
        if record.phase_transition_step:
            lines.append(f"- **Phase transition step:** {record.phase_transition_step}")
        if record.failure_signature:
            lines.append(f"- **Failure signature:** {record.failure_signature}")
        if record.degenerate:
            lines.append(f"- **Degenerate:** Yes")
            if record.degeneracy_diagnosis:
                lines.append(f"- **Degeneracy diagnosis:** {record.degeneracy_diagnosis}")
        lines.append(f"- **Divergent:** {record.divergence_flag}")
        if record.divergence_k is not None:
            lines.append(f"- **Divergence k:** {record.divergence_k}")
            lines.append(f"- **Divergence ratio:** {record.divergence_ratio:.1f}×")
        lines.append(f"- **Max persist counter:** {record.max_persist_counter}")
        lines.append(f"- **Max consecutive flag steps:** {record.max_consecutive_flag_steps}")
        lines.append(f"- **Duration:** {record.duration_ms}ms")
        lines.append("")

    # Raw interpretation (per §10)
    lines.append("## Observations (Raw)")
    lines.append("")
    lines.append("*Per preregistration §10, the runner reports data only. Interpretation is deferred.*")
    lines.append("")

    # Check control vs adversary
    control_non_degenerate = all(
        not r.degenerate for r in report.run_records
        if "v0.3.2.a" in r.variant
    )
    adversary_failures = sum(
        1 for r in report.run_records
        if "v0.3.2.a" not in r.variant and r.failure_signature
    )
    adversary_survivals = sum(
        1 for r in report.run_records
        if "v0.3.2.a" not in r.variant and not r.failure_signature and not r.degenerate
    )

    lines.append(f"- Control variants all non-degenerate: {control_non_degenerate}")
    lines.append(f"- Adversary failure signatures: {adversary_failures}")
    lines.append(f"- Adversary survivals (non-failure, non-degenerate): {adversary_survivals}")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    # Run experiment
    report = run_experiment(verbose=True)

    # Save JSON report
    output_dir = Path(__file__).parent.parent / "reports"
    json_path = save_report(report, output_dir)
    print(f"\nJSON report saved: {json_path}")

    # Generate and save markdown report
    md_content = generate_markdown_report(report)
    md_path = output_dir / f"experiment_H10000_{report.experiment_id}.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Markdown report saved: {md_path}")
