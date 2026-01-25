#!/usr/bin/env python3
"""
Full-protocol Ablation D rerun after Bug #3 fix.

Parameters: H=40, E=20, seed=42
Expected: 800 HALTs, 0 steps executed, halt_rate=1.0
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.env.tri_demand import TriDemandV410
from src.rsa_poc.v410.ablations import AblationType, AblationHarness
from src.rsa_poc.v410.harness import HarnessConfig
from src.rsa_poc.v410.deliberator import DeterministicDeliberator


def main():
    print("=" * 70)
    print("ABLATION D: FULL-PROTOCOL RERUN (Bug #3 Fixed)")
    print("=" * 70)
    print()
    print("Parameters: H=40, E=20, seed=42")
    print("Expected: 800 HALTs, 0 steps executed")
    print()

    env = TriDemandV410(seed=42)
    config = HarnessConfig(
        max_steps_per_episode=40,
        max_episodes=20,
        seed=42,
        verbose=True
    )

    harness = AblationHarness(
        env=env,
        ablation_type=AblationType.TRACE_EXCISION,
        config=config,
        deliberator=DeterministicDeliberator(),
        seed=42
    )

    print("Running...")
    print()

    result = harness.run()

    summary = result.get('summary', {})
    total_steps = summary.get('total_steps', 0)
    total_halts = summary.get('total_halts', 0)
    elapsed_ms = summary.get('elapsed_ms', 0)

    # Expected: 20 episodes × 40 attempts = 800 halt attempts
    expected_halts = 20 * 40

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total steps executed: {total_steps}")
    print(f"Total halts: {total_halts}")
    print(f"Expected halts: {expected_halts}")
    print(f"Elapsed: {elapsed_ms:.1f}ms ({elapsed_ms/1000:.2f}s)")
    print()

    # Validation
    steps_ok = total_steps == 0
    halts_ok = total_halts == expected_halts
    passed = steps_ok and halts_ok

    print("VALIDATION:")
    print(f"  steps == 0: {'✅' if steps_ok else '❌'} ({total_steps})")
    print(f"  halts == {expected_halts}: {'✅' if halts_ok else '❌'} ({total_halts})")
    print()
    print(f"RESULT: {'✅ PASS - Ablation D validated at full protocol' if passed else '❌ FAIL'}")
    print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v410_ablation_d_rerun_{timestamp}.json"

    output = {
        "experiment": "ablation_d_rerun",
        "timestamp": timestamp,
        "protocol": {
            "H": 40,
            "E": 20,
            "seed": 42
        },
        "bug_fix": "Bug #3: TraceExcisionCompiler returns empty rule_evals",
        "results": {
            "total_steps": total_steps,
            "total_halts": total_halts,
            "expected_halts": expected_halts,
            "halt_rate": 1.0 if total_steps == 0 and total_halts > 0 else 0.0,
            "elapsed_ms": elapsed_ms
        },
        "validation": {
            "passed": passed,
            "steps_zero": steps_ok,
            "halts_correct": halts_ok
        },
        "episodes": result.get('episodes', [])
    }

    with open(f"/home/david/Axio/results/{filename}", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: results/{filename}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
