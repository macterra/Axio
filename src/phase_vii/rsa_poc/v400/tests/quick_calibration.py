"""
RSA-PoC v4.0 — Quick Calibration Check
Run a quick calibration to verify the gate before full run.
"""

import sys
sys.path.insert(0, '/home/david/Axio/src/rsa_poc')

from v400.core.harness import ASBNullAgent
from v400.core.oracle import OracleRunner

def quick_calibration():
    """Run quick calibration with fewer episodes."""
    print("=" * 60)
    print("RSA-PoC v4.0 — Quick Calibration Check")
    print("=" * 60)
    print()

    seeds = [42, 123]
    episodes_per_seed = 20

    # Oracle
    print("Running Oracle policy...")
    oracle_successes = 0
    oracle_total = 0

    for seed in seeds:
        runner = OracleRunner(seed=seed, max_episodes=episodes_per_seed)
        result = runner.run()
        oracle_successes += result["successes"]
        oracle_total += result["episodes"]
        print(f"  Seed {seed}: {result['successes']}/{result['episodes']} successes")

    oracle_rate = oracle_successes / oracle_total
    print(f"  Oracle overall: {oracle_rate:.1%}")
    print()

    # ASB Null
    print("Running ASB Null baseline...")
    asb_successes = 0
    asb_total = 0

    for seed in seeds:
        agent = ASBNullAgent(seed=seed, max_episodes=episodes_per_seed)
        metrics = agent.run()
        successes = int(metrics.success_rate * metrics.episodes)
        asb_successes += successes
        asb_total += metrics.episodes
        print(f"  Seed {seed}: {successes}/{metrics.episodes} successes")

    asb_rate = asb_successes / asb_total
    print(f"  ASB Null overall: {asb_rate:.1%}")
    print()

    # Check
    oracle_ok = oracle_rate >= 0.95
    asb_ok = asb_rate <= 0.10

    print("=" * 60)
    print("Results:")
    print(f"  Oracle:   {oracle_rate:.1%} {'✓' if oracle_ok else '✗'} (need ≥95%)")
    print(f"  ASB Null: {asb_rate:.1%} {'✓' if asb_ok else '✗'} (need ≤10%)")
    print()

    if oracle_ok and asb_ok:
        print("  Quick calibration PASSED ✓")
    else:
        print("  Quick calibration FAILED — needs debugging")
    print("=" * 60)

    return oracle_ok and asb_ok


if __name__ == "__main__":
    success = quick_calibration()
    exit(0 if success else 1)
