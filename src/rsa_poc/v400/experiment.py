"""
RSA-PoC v4.0 — Main Experiment Runner
Implements §12 Execution Order of v40_design_freeze.md

1. Design Freeze → APPROVED
2. Implementation → DONE
3. Environment Calibration → DONE
4. Baseline Verification (5 seeds)
5. Ablation Battery (A, B, C, D × 5 seeds = 20 runs)
6. Weakening Ladders (future)
7. SPOF Tests (future)
8. Final Classification + Closure
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .core.ablations import (
    AblationResult,
    run_ablation_a,
    run_ablation_b,
    run_ablation_c,
    run_ablation_d,
)
from .core.harness import MVRSA400, RunMetrics
from .core.oracle import OracleDeliberator
from .calibration import run_calibration, CalibrationResult, calibration_report

# Preregistered seeds per §7
SEEDS = [42, 123, 456, 789, 1024]


# ============================================================================
# Baseline Verification
# ============================================================================


@dataclass
class BaselineResult:
    """Result of baseline verification for one seed."""
    seed: int
    metrics: RunMetrics
    success_rate: float


def run_baseline(seed: int, max_episodes: int = 20) -> BaselineResult:
    """Run baseline verification for one seed."""
    deliberator = OracleDeliberator()
    agent = MVRSA400(deliberator=deliberator, seed=seed, max_episodes=max_episodes)
    metrics = agent.run()

    return BaselineResult(
        seed=seed,
        metrics=metrics,
        success_rate=metrics.success_rate,
    )


def run_baseline_verification(seeds: List[int] = None) -> Dict:
    """
    Run baseline verification per §12.

    Returns dict with results for each seed.
    """
    if seeds is None:
        seeds = SEEDS

    results = {
        "timestamp": datetime.now().isoformat(),
        "seeds": seeds,
        "baselines": [],
        "aggregate_success_rate": 0.0,
    }

    for seed in seeds:
        baseline = run_baseline(seed)
        results["baselines"].append({
            "seed": seed,
            "success_rate": baseline.success_rate,
            "halt_rate": baseline.metrics.halt_rate,
            "compilation_rate": baseline.metrics.compilation_rate,
            "patches_applied": baseline.metrics.patches_applied,
        })

    # Aggregate
    results["aggregate_success_rate"] = sum(
        b["success_rate"] for b in results["baselines"]
    ) / len(results["baselines"])

    return results


# ============================================================================
# Ablation Battery
# ============================================================================


def run_ablation_battery(seeds: List[int] = None) -> Dict:
    """
    Run ablation battery per §12.

    A, B, C, D × 5 seeds = 20 runs
    """
    if seeds is None:
        seeds = SEEDS

    results = {
        "timestamp": datetime.now().isoformat(),
        "seeds": seeds,
        "ablations": {
            "A": [],  # Semantic Excision
            "B": [],  # Reflection Excision
            "C": [],  # Persistence Excision
            "D": [],  # Trace Excision
        },
        "summary": {},
    }

    # Run A (Semantic Excision)
    print("Running Ablation A (Semantic Excision)...")
    for seed in seeds:
        r = run_ablation_a(seed)
        results["ablations"]["A"].append({
            "seed": seed,
            "success_rate": r.success_rate,
            "halt_rate": r.halt_rate,
        })

    # Run B (Reflection Excision)
    print("Running Ablation B (Reflection Excision)...")
    for seed in seeds:
        r = run_ablation_b(seed)
        results["ablations"]["B"].append({
            "seed": seed,
            "success_rate": r.success_rate,
            "halt_rate": r.halt_rate,
        })

    # Run C (Persistence Excision)
    print("Running Ablation C (Persistence Excision)...")
    for seed in seeds:
        r = run_ablation_c(seed)
        results["ablations"]["C"].append({
            "seed": seed,
            "success_rate": r.success_rate,
            "halt_rate": r.halt_rate,
        })

    # Run D (Trace Excision)
    print("Running Ablation D (Trace Excision)...")
    for seed in seeds:
        r = run_ablation_d(seed)
        results["ablations"]["D"].append({
            "seed": seed,
            "success_rate": r.success_rate,
            "halt_rate": r.halt_rate,
        })

    # Summary
    for abl_type in ["A", "B", "C", "D"]:
        rates = [r["success_rate"] for r in results["ablations"][abl_type]]
        results["summary"][abl_type] = {
            "mean_success_rate": sum(rates) / len(rates),
            "min_success_rate": min(rates),
            "max_success_rate": max(rates),
        }

    return results


# ============================================================================
# Classification
# ============================================================================


def classify_results(baseline: Dict, ablations: Dict) -> Dict:
    """
    Classify results per §11.

    | Classification | Condition |
    |----------------|-----------|
    | BASELINE | Survives pressure-free, diverges from ASB |
    | NARRATIVE_COLLAPSE | Trace ablation causes ASB-equivalence |
    | INCENTIVE_CAPTURE | Semantic ablation causes ASB-equivalence |
    | ONTOLOGICAL_COLLAPSE | Reflection or persistence ablation causes ASB-equivalence |
    | ASB_CLASS_REDUCIBILITY | Baseline indistinguishable from ASB |
    """
    ASB_THRESHOLD = 0.10  # ASB Null should be ≤10%

    classification = {
        "baseline_success_rate": baseline["aggregate_success_rate"],
        "ablation_success_rates": {
            k: v["mean_success_rate"]
            for k, v in ablations["summary"].items()
        },
        "classification": None,
        "reason": None,
    }

    baseline_rate = baseline["aggregate_success_rate"]
    a_rate = ablations["summary"]["A"]["mean_success_rate"]
    b_rate = ablations["summary"]["B"]["mean_success_rate"]
    c_rate = ablations["summary"]["C"]["mean_success_rate"]
    d_rate = ablations["summary"]["D"]["mean_success_rate"]

    # Check baseline
    if baseline_rate <= ASB_THRESHOLD:
        classification["classification"] = "ASB_CLASS_REDUCIBILITY"
        classification["reason"] = f"Baseline ({baseline_rate:.1%}) ≤ ASB threshold ({ASB_THRESHOLD:.0%})"
        return classification

    # Check ablations for collapse
    collapses = []

    if d_rate <= ASB_THRESHOLD:
        collapses.append(("NARRATIVE_COLLAPSE", f"Run D (Trace): {d_rate:.1%}"))

    if a_rate <= ASB_THRESHOLD:
        collapses.append(("INCENTIVE_CAPTURE", f"Run A (Semantic): {a_rate:.1%}"))

    if b_rate <= ASB_THRESHOLD:
        collapses.append(("ONTOLOGICAL_COLLAPSE", f"Run B (Reflection): {b_rate:.1%}"))

    if c_rate <= ASB_THRESHOLD:
        collapses.append(("ONTOLOGICAL_COLLAPSE", f"Run C (Persistence): {c_rate:.1%}"))

    if collapses:
        # Use first collapse type (priority order)
        classification["classification"] = collapses[0][0]
        classification["reason"] = "; ".join(c[1] for c in collapses)
    else:
        classification["classification"] = "BASELINE"
        classification["reason"] = f"Baseline ({baseline_rate:.1%}) diverges from ASB, no ablation collapse"

    return classification


# ============================================================================
# Main Runner
# ============================================================================


def run_full_experiment(quick: bool = False) -> Dict:
    """
    Run full v4.0 experiment per §12 execution order.

    Args:
        quick: If True, use fewer episodes for faster testing
    """
    print("=" * 70)
    print("RSA-PoC v4.0 — Full Experiment")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    results = {
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
        "quick_mode": quick,
    }

    seeds = SEEDS if not quick else [42, 123]

    # Step 3: Environment Calibration
    print("Step 3: Environment Calibration")
    print("-" * 40)
    cal = run_calibration(seeds=seeds[:2] if quick else seeds)
    results["calibration"] = {
        "oracle_success_rate": cal.oracle_success_rate,
        "asb_null_success_rate": cal.asb_null_success_rate,
        "passed": cal.overall_passed,
    }
    print(f"  Oracle: {cal.oracle_success_rate:.1%}")
    print(f"  ASB Null: {cal.asb_null_success_rate:.1%}")
    print(f"  Status: {'PASSED' if cal.overall_passed else 'FAILED'}")
    print()

    if not cal.overall_passed:
        print("ERROR: Calibration failed. Aborting.")
        results["status"] = "INVALID_RUN"
        return results

    # Step 4: Baseline Verification
    print("Step 4: Baseline Verification")
    print("-" * 40)
    baseline = run_baseline_verification(seeds=seeds)
    results["baseline"] = baseline
    print(f"  Aggregate success rate: {baseline['aggregate_success_rate']:.1%}")
    for b in baseline["baselines"]:
        print(f"    Seed {b['seed']}: {b['success_rate']:.1%}")
    print()

    # Step 5: Ablation Battery
    print("Step 5: Ablation Battery")
    print("-" * 40)
    ablations = run_ablation_battery(seeds=seeds)
    results["ablations"] = ablations
    for abl_type, summary in ablations["summary"].items():
        print(f"  Run {abl_type}: {summary['mean_success_rate']:.1%} mean success")
    print()

    # Step 8: Classification
    print("Step 8: Classification")
    print("-" * 40)
    classification = classify_results(baseline, ablations)
    results["classification"] = classification
    print(f"  Result: {classification['classification']}")
    print(f"  Reason: {classification['reason']}")
    print()

    print("=" * 70)
    print("Experiment Complete")
    print("=" * 70)

    return results


def main():
    """CLI entry point."""
    import sys

    quick = "--quick" in sys.argv

    results = run_full_experiment(quick=quick)

    # Save results
    output_path = f"/home/david/Axio/src/rsa_poc/v400/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")

    return 0 if results.get("classification", {}).get("classification") else 1


if __name__ == "__main__":
    exit(main())
