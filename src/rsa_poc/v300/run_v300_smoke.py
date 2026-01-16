#!/usr/bin/env python3
"""v3.0 Smoke Test Runner

BINDING (v3.0 Integration Requirement 6):
Single-seed smoke test that MUST pass before any multi-seed run.

Configuration:
- seed=42
- episodes=1
- steps≤20

Acceptance Criteria:
- 0 INVALID_RUN classifications
- No fallback substitution (action_source != "harness_default")
- No crashes in selector/executor/compiler
- No missing-field exceptions

Usage:
    python -m rsa_poc.v300.run_v300_smoke
    python -m rsa_poc.v300.run_v300_smoke --ablation trace_excision
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from rsa_poc.v300.harness import (
    V300AblationHarness,
    V300RunConfig,
    V300EpisodeRecord,
)
from rsa_poc.v300.ablation import (
    AblationSpec,
    AblationClassification,
    InvalidRunReason,
)


def run_smoke_test(
    ablation: AblationSpec = AblationSpec.TRACE_EXCISION,
    output_path: Optional[Path] = None,
) -> bool:
    """
    Run single-seed smoke test.

    Returns True if smoke test passes, False otherwise.
    """
    print("=" * 60)
    print("v3.0 SMOKE TEST")
    print("=" * 60)
    print(f"Ablation: {ablation.value}")
    print(f"Seed: 42")
    print(f"Episodes: 1")
    print(f"Max steps: 20")
    print()

    # Create config with relaxed requirements for smoke test
    # Use tuple with exactly 5 elements (minimum required)
    # But we'll only use the first seed for smoke test
    config = V300RunConfig(
        ablation=ablation,
        seeds=(42, 43, 44, 45, 46),  # Minimum 5 required
        num_episodes=1,
        steps_per_episode=20,
    )

    harness = V300AblationHarness(config)

    # Run just the first seed
    print("Running smoke test seed (42)...")
    try:
        seed_result = harness._run_seed(42)
    except Exception as e:
        print(f"\n❌ SMOKE TEST FAILED: Exception during run")
        print(f"   {type(e).__name__}: {e}")
        return False

    # Check acceptance criteria
    failures = []

    # 1. No INVALID_RUN
    if seed_result.classification == AblationClassification.INVALID_RUN:
        failures.append(
            f"Classification is INVALID_RUN (reason: {seed_result.invalid_reason.value})"
        )

    # 2. Check for fallback substitution
    if seed_result.invalid_reason == InvalidRunReason.FALLBACK_SUBSTITUTION:
        failures.append("Fallback substitution detected")

    # 3. Check for crashes (schema crashes, missing field exceptions)
    if seed_result.invalid_reason in (
        InvalidRunReason.SCHEMA_CRASH,
        InvalidRunReason.MISSING_FIELD_EXCEPTION,
        InvalidRunReason.NULL_POINTER,
        InvalidRunReason.STATIC_TYPE_ERROR,
    ):
        failures.append(f"Technical crash: {seed_result.invalid_reason.value}")

    # 4. Check technical failures list
    if seed_result.technical_failures:
        failures.append(f"Technical failures: {seed_result.technical_failures}")

    # Report results
    print()
    print("-" * 60)
    print("SMOKE TEST RESULTS")
    print("-" * 60)
    print(f"Classification: {seed_result.classification.value}")
    print(f"Invalid Reason: {seed_result.invalid_reason.value}")
    print(f"Compilation Success Rate: {seed_result.compilation_success_rate:.2%}")
    print(f"Gridlock Rate: {seed_result.gridlock_rate:.2%}")
    print(f"ASB Equivalence Score: {seed_result.asb_equivalence_score:.3f}")

    if failures:
        print()
        print("❌ SMOKE TEST FAILED")
        for failure in failures:
            print(f"   - {failure}")
        print()
        print("DO NOT PROCEED with multi-seed runs until smoke test passes.")
        return False
    else:
        print()
        print("✅ SMOKE TEST PASSED")
        print()
        print("Safe to proceed with multi-seed runs.")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="v3.0 Smoke Test - Single-seed validation before multi-seed runs"
    )
    parser.add_argument(
        "--ablation",
        type=str,
        choices=["none", "trace_excision", "semantic_excision",
                 "reflection_excision", "persistence_excision"],
        default="trace_excision",
        help="Ablation type to test (default: trace_excision for Golden Test)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for results JSON",
    )

    args = parser.parse_args()

    # Map ablation string to enum
    ablation_map = {
        "none": AblationSpec.NONE,
        "trace_excision": AblationSpec.TRACE_EXCISION,
        "semantic_excision": AblationSpec.SEMANTIC_EXCISION,
        "reflection_excision": AblationSpec.REFLECTION_EXCISION,
        "persistence_excision": AblationSpec.PERSISTENCE_EXCISION,
    }
    ablation = ablation_map[args.ablation]

    success = run_smoke_test(ablation, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
