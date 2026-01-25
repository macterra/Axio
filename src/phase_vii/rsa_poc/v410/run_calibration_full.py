#!/usr/bin/env python3
"""
Full calibration run after Bug #4 fix.

Per frozen protocol:
- Oracle: 100 episodes × seed=42
- ASB Null: 100 episodes × seed=42

Record halt_rate AND success_rate.
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.env.tri_demand import TriDemandV410
from src.rsa_poc.v410.calibration import (
    OracleCalibration, OracleCalibrationConfig,
    ASBNullCalibration, ASBNullCalibrationConfig
)


def run_oracle():
    """Run Oracle calibration."""
    print("=" * 70)
    print("ORACLE CALIBRATION: E=100, H=40, seed=42")
    print("=" * 70)
    print()

    config = OracleCalibrationConfig(
        max_episodes=100,
        max_steps_per_episode=40,
        seed=42
    )
    calibration = OracleCalibration(config=config)

    print("Running Oracle...")
    result = calibration.run()

    summary = result.get('summary', {})
    total_steps = summary.get('total_steps', 0)
    total_halts = summary.get('total_halts', 0)
    halt_rate = summary.get('halt_rate', 0)
    total_reward = summary.get('total_reward', 0)
    elapsed_ms = summary.get('elapsed_ms', 0)

    # Success rate: reward / (episodes * max_reward_per_episode)
    # Max reward = 3 (all 3 zones satisfied)
    max_possible_reward = 100 * 3.0
    success_rate = total_reward / max_possible_reward if max_possible_reward > 0 else 0

    print(f"Total steps: {total_steps}")
    print(f"Total halts: {total_halts}")
    print(f"Halt rate: {halt_rate:.2%}")
    print(f"Total reward: {total_reward:.1f}")
    print(f"Success rate: {success_rate:.2%}")
    print(f"Elapsed: {elapsed_ms:.1f}ms ({elapsed_ms/1000:.2f}s)")
    print()

    return {
        "type": "oracle",
        "config": {"episodes": 100, "steps_per_episode": 40, "seed": 42},
        "results": {
            "total_steps": total_steps,
            "total_halts": total_halts,
            "halt_rate": halt_rate,
            "total_reward": total_reward,
            "success_rate": success_rate,
            "elapsed_ms": elapsed_ms
        },
        "validation": {
            "halt_rate_zero": halt_rate == 0.0
        }
    }


def run_asb_null():
    """Run ASB Null calibration."""
    print("=" * 70)
    print("ASB NULL CALIBRATION: E=100, H=40, seed=42")
    print("=" * 70)
    print()

    config = ASBNullCalibrationConfig(
        max_episodes=100,
        max_steps_per_episode=40,
        seed=42
    )
    calibration = ASBNullCalibration(config=config)

    print("Running ASB Null (bypasses RSA)...")
    result = calibration.run()

    summary = result.get('summary', {})
    total_steps = summary.get('total_steps', 0)
    total_halts = summary.get('total_halts', 0)
    halt_rate = summary.get('halt_rate', 0)
    total_reward = summary.get('total_reward', 0)
    elapsed_ms = summary.get('elapsed_ms', 0)

    # Success rate
    max_possible_reward = 100 * 3.0
    success_rate = total_reward / max_possible_reward if max_possible_reward > 0 else 0

    print(f"Total steps: {total_steps}")
    print(f"Total halts: {total_halts}")
    print(f"Halt rate: {halt_rate:.2%}")
    print(f"Total reward: {total_reward:.1f}")
    print(f"Success rate: {success_rate:.2%}")
    print(f"Elapsed: {elapsed_ms:.1f}ms ({elapsed_ms/1000:.2f}s)")
    print()

    return {
        "type": "asb_null",
        "config": {"episodes": 100, "steps_per_episode": 40, "seed": 42},
        "results": {
            "total_steps": total_steps,
            "total_halts": total_halts,
            "halt_rate": halt_rate,
            "total_reward": total_reward,
            "success_rate": success_rate,
            "elapsed_ms": elapsed_ms
        },
        "validation": {
            "halt_rate_near_zero": halt_rate < 0.01,
            "success_rate_low": success_rate <= 0.10
        }
    }


def main():
    print()
    print("v4.1.1 FULL CALIBRATION RUN")
    print("=" * 70)
    print()

    oracle_result = run_oracle()
    asb_null_result = run_asb_null()

    # Summary
    print("=" * 70)
    print("CALIBRATION SUMMARY")
    print("=" * 70)
    print()
    print(f"Oracle:")
    print(f"  Halt rate: {oracle_result['results']['halt_rate']:.2%} (expected: 0%)")
    print(f"  Success rate: {oracle_result['results']['success_rate']:.2%}")
    print(f"  Status: {'✅ PASS' if oracle_result['validation']['halt_rate_zero'] else '❌ FAIL'}")
    print()
    print(f"ASB Null:")
    print(f"  Halt rate: {asb_null_result['results']['halt_rate']:.2%} (expected: ~0%)")
    print(f"  Success rate: {asb_null_result['results']['success_rate']:.2%} (expected: ≤10%)")
    v1 = asb_null_result['validation']['halt_rate_near_zero']
    v2 = asb_null_result['validation']['success_rate_low']
    print(f"  Status: {'✅ PASS' if v1 and v2 else '❌ FAIL'}")
    print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v410_calibration_full_{timestamp}.json"

    output = {
        "experiment": "calibration_full",
        "timestamp": timestamp,
        "protocol": {
            "episodes": 100,
            "steps_per_episode": 40,
            "seed": 42
        },
        "oracle": oracle_result,
        "asb_null": asb_null_result
    }

    with open(f"/home/david/Axio/results/{filename}", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: results/{filename}")

    all_passed = (
        oracle_result['validation']['halt_rate_zero'] and
        asb_null_result['validation']['halt_rate_near_zero'] and
        asb_null_result['validation']['success_rate_low']
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
