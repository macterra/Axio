#!/usr/bin/env python3
"""v3.0 Ablation D Runner — The Golden Test

This is the definitive test for the RSA-PoC program.
If Ablation D fails (constraints still bind without traces),
the entire program is falsified.

Ablation D removes:
- derivation_trace
- justification_trace
- rule_refs
- proof objects
- inference chains

Preserves:
- Constraint IDs
- Binding strength
- All other structure

Expected outcome:
- Collapse to ASB_CLASS_REDUCIBILITY or NARRATIVE_COLLAPSE
- If constraints still bind → justifications were epiphenomenal → FAILURE

Usage:
    python run_v300_ablation_d.py [--seeds 42,123,456,789,1024] [--output results.json]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rsa_poc.v300 import (
    AblationSpec,
    V300RunConfig,
    V300AblationHarness,
)
from rsa_poc.v300.ablation import AblationClassification


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="v3.0 Ablation D — Golden Test for RSA-PoC"
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default="42,123,456,789,1024",
        help="Comma-separated list of seeds (minimum 5 required)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (default: v300_ablation_d_<timestamp>.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration without executing",
    )
    return parser.parse_args()


def main():
    """Execute Ablation D — The Golden Test."""
    args = parse_args()

    # Parse seeds
    seeds = tuple(int(s.strip()) for s in args.seeds.split(","))

    if len(seeds) < 5:
        print("ERROR: v3.0 requires minimum 5 preregistered seeds")
        sys.exit(1)

    # Default output path
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"v300_ablation_d_{timestamp}.json")
    else:
        output_path = Path(args.output)

    print("=" * 70)
    print("v3.0 ABLATION D — THE GOLDEN TEST")
    print("=" * 70)
    print()
    print("This test removes derivation traces while preserving constraint IDs.")
    print("If constraints still bind without their justification traces,")
    print("the RSA-PoC program is FALSIFIED.")
    print()
    print(f"Seeds: {seeds}")
    print(f"Output: {output_path}")
    print()

    if args.dry_run:
        print("[DRY RUN] Would execute with above configuration")
        return

    # Configure Ablation D
    config = V300RunConfig(
        ablation=AblationSpec.TRACE_EXCISION,
        seeds=seeds,
        num_episodes=3,
        steps_per_episode=50,
        environment="CommitmentTrapV200",
        use_sam=False,  # No SAM for v3.0 baseline
        friction_modifier=1.0,  # Neutral friction
    )

    # Create harness
    harness = V300AblationHarness(config)

    # Execute
    print("-" * 70)
    print("EXECUTING ABLATION D")
    print("-" * 70)

    result = harness.run(output_path)

    # Report results
    print()
    print("=" * 70)
    print("ABLATION D RESULT")
    print("=" * 70)
    print()

    if result.aggregate_classification is None:
        print("RESULT: NO VALID SEEDS")
        print("Classification could not be determined.")
        sys.exit(2)

    classification = result.aggregate_classification
    consistent = result.classification_consistent
    all_valid = result.all_seeds_valid

    print(f"Aggregate Classification: {classification.value}")
    print(f"Consistent across seeds: {consistent}")
    print(f"All seeds valid: {all_valid}")
    print()

    # Interpret result
    if classification == AblationClassification.ASB_CLASS_REDUCIBILITY:
        print("✓ ABLATION D PASSED: System collapsed to ASB-class")
        print("  The ablated system is indistinguishable from random action selection.")
        print("  Derivation traces WERE load-bearing.")
        print()
        print("  RSA-PoC program survives this test.")
        sys.exit(0)

    elif classification == AblationClassification.NARRATIVE_COLLAPSE:
        print("✓ ABLATION D PASSED: Narrative collapse observed")
        print("  Constraints no longer bind meaningfully without traces.")
        print("  Derivation traces WERE semantically necessary.")
        print()
        print("  RSA-PoC program survives this test.")
        sys.exit(0)

    elif classification == AblationClassification.ONTOLOGICAL_COLLAPSE:
        print("✓ ABLATION D PASSED: Ontological collapse observed")
        print("  System reduced to mechanism without traces.")
        print("  Derivation traces WERE constitutive of agency.")
        print()
        print("  RSA-PoC program survives this test.")
        sys.exit(0)

    elif classification == AblationClassification.INCENTIVE_CAPTURE:
        print("? ABLATION D UNEXPECTED: Incentive capture")
        print("  System drifted to reward-following.")
        print("  This is not the expected failure mode for trace ablation.")
        print()
        print("  RSA-PoC program requires investigation.")
        sys.exit(3)

    elif classification == AblationClassification.INVALID_RUN:
        print("✗ ABLATION D INVALID: Technical failures")
        print("  Too many invalid seeds to classify.")
        print(f"  Invalid seeds: {result.invalid_seeds}")
        print()
        print("  RSA-PoC program requires rerun with fixed infrastructure.")
        sys.exit(2)

    else:
        print(f"? ABLATION D UNKNOWN: {classification.value}")
        print("  Unexpected classification.")
        sys.exit(4)


if __name__ == "__main__":
    main()
