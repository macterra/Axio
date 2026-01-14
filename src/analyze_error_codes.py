#!/usr/bin/env python3
"""
Systematic failure analysis using actual v2.0 harness.
Produces histogram of all error codes from sovereign runs.
"""

import os
import sys
import json
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rsa_poc.v200.runplans.harness_v200 import (
    V200ExperimentHarness, V200RunConfig, AgentType
)


def run_analysis(regime: str, num_episodes: int = 3, steps_per_episode: int = 10):
    """Run sovereign experiment and collect all error codes."""

    config = V200RunConfig(
        agent_type=AgentType.SOVEREIGN,
        reward_regime=regime,
        num_episodes=num_episodes,
        steps_per_episode=steps_per_episode,
        random_seed=42
    )

    harness = V200ExperimentHarness(config)
    result = harness.run()

    # Collect all error codes
    error_counts = Counter()
    successful_steps = 0
    failed_steps = 0

    for episode in result.episodes:
        for step_record in episode.steps:
            if step_record.compiled_ok:
                successful_steps += 1
            else:
                failed_steps += 1
                if step_record.error_code:
                    # Parse error code (may contain full message)
                    code = step_record.error_code
                    # Extract just the code prefix
                    if ':' in code:
                        code_prefix = code.split(':')[0].strip()
                    else:
                        code_prefix = code
                    error_counts[code_prefix] += 1
                    # Also count full message for detail
                    error_counts[f"FULL:{code[:80]}"] += 1

    return {
        "regime": regime,
        "successful_steps": successful_steps,
        "failed_steps": failed_steps,
        "error_counts": dict(error_counts),
        "total_compilation_failures": result.summary.get("total_compilation_failures", 0),
        "drift_rate": result.summary.get("drift_rate", 0),
    }


def main():
    # Check API key
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: LLM_API_KEY required")
        sys.exit(1)

    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    model = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
    print(f"LLM: {provider} / {model}")
    print()

    print("=" * 70)
    print("SOVEREIGN ERROR CODE ANALYSIS")
    print("=" * 70)

    # Run for R1
    print("\nAnalyzing Sovereign under R1...")
    r1_data = run_analysis("R1", num_episodes=2, steps_per_episode=10)

    print(f"\nR1 Results:")
    print(f"  Successful steps: {r1_data['successful_steps']}")
    print(f"  Failed steps: {r1_data['failed_steps']}")
    print(f"  Drift rate: {r1_data['drift_rate']}")
    print(f"\n  Error code histogram:")
    for code, count in sorted(r1_data['error_counts'].items()):
        if not code.startswith("FULL:"):
            print(f"    {code}: {count}")

    # Run for R2
    print("\nAnalyzing Sovereign under R2...")
    r2_data = run_analysis("R2", num_episodes=2, steps_per_episode=10)

    print(f"\nR2 Results:")
    print(f"  Successful steps: {r2_data['successful_steps']}")
    print(f"  Failed steps: {r2_data['failed_steps']}")
    print(f"  Drift rate: {r2_data['drift_rate']}")
    print(f"\n  Error code histogram:")
    for code, count in sorted(r2_data['error_counts'].items()):
        if not code.startswith("FULL:"):
            print(f"    {code}: {count}")

    # Save detailed results
    output = {
        "timestamp": datetime.now().isoformat(),
        "R1": r1_data,
        "R2": r2_data
    }

    filename = f"error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nDetailed results saved to: {filename}")


if __name__ == "__main__":
    main()
