"""
RSA-PoC v4.1 — Calibration Run
Run Oracle + ASB Null baselines per frozen protocol (§9).

Protocol:
- E = 100 episodes for calibration
- N = 5 seeds [42, 123, 456, 789, 1024]
- H = 40 steps per episode

Run: python -m src.rsa_poc.v410.run_calibration
"""

import json
import time
from datetime import datetime
from pathlib import Path

from src.rsa_poc.v410.calibration import run_calibrations
from src.rsa_poc.v410.experiment import FROZEN_SEEDS, FROZEN_H


# Calibration uses E=100 per spec
CALIBRATION_E = 100


def main():
    print("=" * 70)
    print("RSA-PoC v4.1 — Calibration Run")
    print("=" * 70)
    print()
    print(f"Protocol Parameters:")
    print(f"  H (steps per episode): {FROZEN_H}")
    print(f"  E (episodes):          {CALIBRATION_E}")
    print(f"  N (seeds):             {len(FROZEN_SEEDS)} {FROZEN_SEEDS}")
    print()
    print(f"Expected total steps per baseline per seed: {FROZEN_H * CALIBRATION_E:,}")
    print(f"Expected total steps per baseline (all seeds): {FROZEN_H * CALIBRATION_E * len(FROZEN_SEEDS):,}")
    print()

    start_time = time.perf_counter()

    print("--- Running Calibrations ---")
    print("This may take several minutes...")
    print()

    results = run_calibrations(
        seeds=FROZEN_SEEDS,
        max_steps=FROZEN_H,
        max_episodes=CALIBRATION_E
    )

    elapsed = (time.perf_counter() - start_time)

    print()
    print("=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Total time: {elapsed:.2f}s")
    print()

    # Summary
    print("--- Oracle Baseline ---")
    oracle_halts = []
    oracle_compliance = []
    for r in results["oracle"]:
        summary = r.get("summary", {})
        halt_rate = summary.get("halt_rate", 0)
        compliance = summary.get("compliance_rate", 1)
        oracle_halts.append(halt_rate)
        oracle_compliance.append(compliance)
        print(f"  Seed {r['seed']}: halt_rate={halt_rate:.3f}, compliance={compliance:.3f}")

    avg_oracle_halt = sum(oracle_halts) / len(oracle_halts)
    avg_oracle_compliance = sum(oracle_compliance) / len(oracle_compliance)
    print(f"  Mean: halt_rate={avg_oracle_halt:.3f}, compliance={avg_oracle_compliance:.3f}")
    print()

    print("--- ASB Null Baseline ---")
    asb_halts = []
    asb_compliance = []
    for r in results["asb_null"]:
        summary = r.get("summary", {})
        halt_rate = summary.get("halt_rate", 0)
        compliance = summary.get("compliance_rate", 1)
        asb_halts.append(halt_rate)
        asb_compliance.append(compliance)
        print(f"  Seed {r['seed']}: halt_rate={halt_rate:.3f}, compliance={compliance:.3f}")

    avg_asb_halt = sum(asb_halts) / len(asb_halts)
    avg_asb_compliance = sum(asb_compliance) / len(asb_compliance)
    print(f"  Mean: halt_rate={avg_asb_halt:.3f}, compliance={avg_asb_compliance:.3f}")
    print()

    print("--- Direct Random Walk ---")
    for r in results["direct_random"]:
        summary = r.get("summary", {})
        print(f"  Seed {r['seed']}: steps={summary.get('total_steps')}, reward={summary.get('total_reward'):.2f}")
    print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"v410_calibration_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results saved to: {output_file}")
    print()

    # Guardrail assessment
    print("--- Calibration Assessment ---")
    print(f"Oracle should have ~0% halt rate: {avg_oracle_halt:.1%} {'✓' if avg_oracle_halt < 0.05 else '✗'}")
    print(f"ASB Null should have higher halt rate than Oracle: {'✓' if avg_asb_halt > avg_oracle_halt else '?'}")
    print()


if __name__ == "__main__":
    main()
