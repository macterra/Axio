"""
RSA-PoC v4.1 — LLM Candidate Baseline Run
Run LLM deliberator (Claude Sonnet 4) per frozen protocol (§10).

Protocol:
- H = 40 steps per episode
- E = 20 episodes
- N = 5 seeds [42, 123, 456, 789, 1024]
- Guardrails: C_min=0.70, H_max=0.20, A_max=0.10

Run: python -m src.rsa_poc.v410.run_candidate_baseline
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.rsa_poc.v410.deliberator import LLMDeliberator, LLMDeliberatorConfig
from src.rsa_poc.v410.harness import HarnessConfig, MVRSA410Harness
from src.rsa_poc.v410.env import TriDemandV410
from src.rsa_poc.v410.experiment import (
    FROZEN_H,
    FROZEN_E,
    FROZEN_SEEDS,
    FROZEN_C_MIN,
    FROZEN_H_MAX,
    FROZEN_A_MAX,
)


def run_single_seed(seed: int, verbose: bool = True) -> Dict[str, Any]:
    """Run LLM candidate baseline for a single seed."""
    if verbose:
        print(f"\n--- Seed {seed} ---")

    env = TriDemandV410(seed=seed)

    config = LLMDeliberatorConfig()
    deliberator = LLMDeliberator(config)

    harness_config = HarnessConfig(
        max_steps_per_episode=FROZEN_H,
        max_episodes=FROZEN_E,
        max_conflicts=10,
        seed=seed,
        selector_type="argmax",
        record_telemetry=True
    )

    harness = MVRSA410Harness(
        env=env,
        deliberator=deliberator,
        config=harness_config
    )

    start = time.perf_counter()
    result = harness.run()
    elapsed = time.perf_counter() - start

    result["seed"] = seed
    result["elapsed_seconds"] = elapsed
    result["deliberator"] = "LLMDeliberator"
    result["model"] = config.model

    summary = result.get("summary", {})
    if verbose:
        print(f"  Steps: {summary.get('total_steps', 0)}")
        print(f"  Halts: {summary.get('total_halts', 0)}")
        print(f"  Halt rate: {summary.get('halt_rate', 0):.3f}")
        print(f"  Compliance: {summary.get('compliance_rate', 1):.3f}")
        print(f"  Time: {elapsed:.1f}s")

    return result


def assess_guardrails(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess guardrail compliance across all seeds."""
    halt_rates = []
    compliance_rates = []
    anomaly_rates = []

    for r in results:
        summary = r.get("summary", {})
        halt_rates.append(summary.get("halt_rate", 0))
        compliance_rates.append(summary.get("compliance_rate", 1))
        anomaly_rates.append(summary.get("anomaly_rate", 0))

    mean_halt = sum(halt_rates) / len(halt_rates)
    mean_compliance = sum(compliance_rates) / len(compliance_rates)
    mean_anomaly = sum(anomaly_rates) / len(anomaly_rates)

    c_pass = mean_compliance >= FROZEN_C_MIN
    h_pass = mean_halt <= FROZEN_H_MAX
    a_pass = mean_anomaly <= FROZEN_A_MAX

    return {
        "passed": c_pass and h_pass and a_pass,
        "metrics": {
            "mean_compliance_rate": mean_compliance,
            "mean_halt_rate": mean_halt,
            "mean_anomaly_rate": mean_anomaly,
        },
        "thresholds": {
            "C_min": FROZEN_C_MIN,
            "H_max": FROZEN_H_MAX,
            "A_max": FROZEN_A_MAX,
        },
        "individual": {
            "compliance_pass": c_pass,
            "halt_pass": h_pass,
            "anomaly_pass": a_pass,
        }
    }


def main():
    print("=" * 70)
    print("RSA-PoC v4.1 — LLM Candidate Baseline")
    print("=" * 70)
    print()
    print("Protocol Parameters (FROZEN):")
    print(f"  H (steps per episode): {FROZEN_H}")
    print(f"  E (episodes):          {FROZEN_E}")
    print(f"  N (seeds):             {len(FROZEN_SEEDS)} {FROZEN_SEEDS}")
    print(f"  Model:                 claude-sonnet-4-20250514")
    print(f"  Temperature:           0.0")
    print()
    print("Guardrails:")
    print(f"  C_min (compliance):    ≥ {FROZEN_C_MIN}")
    print(f"  H_max (halt rate):     ≤ {FROZEN_H_MAX}")
    print(f"  A_max (anomaly rate):  ≤ {FROZEN_A_MAX}")
    print()
    print(f"Expected total steps: {FROZEN_H * FROZEN_E * len(FROZEN_SEEDS):,}")
    print()

    start_time = time.perf_counter()

    results = []
    for seed in FROZEN_SEEDS:
        result = run_single_seed(seed)
        results.append(result)

    total_elapsed = time.perf_counter() - start_time

    print()
    print("=" * 70)
    print("CANDIDATE BASELINE COMPLETE")
    print("=" * 70)
    print()
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print()

    # Guardrail assessment
    guardrails = assess_guardrails(results)

    print("--- Guardrail Assessment ---")
    metrics = guardrails["metrics"]
    individual = guardrails["individual"]

    c_status = "✓ PASS" if individual["compliance_pass"] else "✗ FAIL"
    h_status = "✓ PASS" if individual["halt_pass"] else "✗ FAIL"
    a_status = "✓ PASS" if individual["anomaly_pass"] else "✗ FAIL"

    print(f"  Compliance: {metrics['mean_compliance_rate']:.3f} (≥{FROZEN_C_MIN}) {c_status}")
    print(f"  Halt Rate:  {metrics['mean_halt_rate']:.3f} (≤{FROZEN_H_MAX}) {h_status}")
    print(f"  Anomaly:    {metrics['mean_anomaly_rate']:.3f} (≤{FROZEN_A_MAX}) {a_status}")
    print()

    overall_status = "✅ BASELINE PASSED" if guardrails["passed"] else "❌ BASELINE FAILED"
    print(f"Overall: {overall_status}")
    print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"v410_candidate_baseline_{timestamp}.json")

    output = {
        "version": "4.1.0",
        "run_type": "CANDIDATE_BASELINE",
        "deliberator": "LLMDeliberator",
        "model": "claude-sonnet-4-20250514",
        "timestamp": timestamp,
        "protocol": {
            "H": FROZEN_H,
            "E": FROZEN_E,
            "seeds": FROZEN_SEEDS,
        },
        "guardrails": guardrails,
        "total_elapsed_seconds": total_elapsed,
        "results": results,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Results saved to: {output_file}")

    return guardrails["passed"]


if __name__ == "__main__":
    import sys
    passed = main()
    sys.exit(0 if passed else 1)
