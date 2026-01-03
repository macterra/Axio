#!/usr/bin/env python3
"""
Sanity check for Run G: Dry sampler acceptance rates per tier.

Per instructions_v0.5.2_runnerG.md:
- Draw 10,000 samples per tier
- Report acceptance rate
- Verify generator can produce candidates at each E-Class

Usage:
    python scripts/sanity_check_sampler.py
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.generator import (
    SuccessorGenerator,
    GeneratorConfig,
    TierFilterGenerator,
    TierUnsatisfiableError,
    V052_ATTACK_WEIGHTS,
    V052_RUNG_G2_ATTACK_WEIGHTS,
)
from toy_aki.als.expressivity import ExpressivityClass, assign_e_class_from_action_types
from toy_aki.als.working_mind import (
    WorkingMindManifest,
    ResourceEnvelope,
    InterfaceDeclaration,
)


def create_baseline_manifest() -> WorkingMindManifest:
    """Create a minimal baseline manifest for generator initialization."""
    return WorkingMindManifest(
        build_hash="baseline_sanity_check",
        build_version="0.0.0",
        resources=ResourceEnvelope(
            max_steps_per_epoch=100,
            max_actions_per_epoch=100,
        ),
        interface=InterfaceDeclaration(
            action_types=frozenset({"WAIT", "PING", "LOG"}),
        ),
    )


def dry_sample_tier(
    base_generator: SuccessorGenerator,
    target_e_class: ExpressivityClass,
    num_draws: int = 10_000,
) -> dict:
    """
    Draw num_draws samples from base generator, count how many match target E-Class.

    Returns dict with:
        - draws: total draws
        - matches: draws matching target E-Class
        - acceptance_rate: matches / draws
    """
    matches = 0
    e_class_distribution = {e: 0 for e in ExpressivityClass}

    for _ in range(num_draws):
        candidate = base_generator.propose(cycle=0)
        action_types = candidate.manifest.interface.action_types
        e_class = assign_e_class_from_action_types(action_types)
        e_class_distribution[e_class] += 1
        if e_class == target_e_class:
            matches += 1

    return {
        "draws": num_draws,
        "matches": matches,
        "acceptance_rate": matches / num_draws if num_draws > 0 else 0.0,
        "e_class_distribution": e_class_distribution,
    }


def main():
    print("=" * 60)
    print("Run G Sanity Check: Dry Sampler Acceptance Rates")
    print("=" * 60)
    print()

    # Create baseline manifest for generator initialization
    baseline_manifest = create_baseline_manifest()

    # Create base generator with V052 attack weights (for G1 ascension)
    config_g1 = GeneratorConfig(
        control_weight=0.20,  # Per Run G: control ≤ 0.20
        attack_weights=V052_ATTACK_WEIGHTS.copy(),
    )
    gen_g1 = SuccessorGenerator(
        sentinel_id="sanity_sentinel",
        baseline_manifest=baseline_manifest,
        config=config_g1,
        seed=42,
    )

    print("Configuration (G1 - Ascension):")
    print(f"  control_weight: {config_g1.control_weight}")
    print(f"  attack_weights: {list(config_g1.attack_weights.keys())}")
    print()

    # Test each tier
    tiers = [
        ExpressivityClass.E0,
        ExpressivityClass.E1,
        ExpressivityClass.E2,
        ExpressivityClass.E3,
        ExpressivityClass.E4,
    ]

    print("Drawing 10,000 samples per tier...")
    print()

    results_g1 = {}
    for tier in tiers:
        # Create fresh generator for each tier to reset state
        gen = SuccessorGenerator(
            sentinel_id="sanity_sentinel",
            baseline_manifest=baseline_manifest,
            config=config_g1,
            seed=42,
        )
        result = dry_sample_tier(gen, tier, num_draws=10_000)
        results_g1[tier] = result

        rate_pct = result["acceptance_rate"] * 100
        print(f"  {tier.name}: {result['matches']:,}/{result['draws']:,} = {rate_pct:.1f}% acceptance")

    print()

    # Overall E-Class distribution from last run (they should all be similar)
    print("E-Class distribution from 10,000 draws:")
    last_dist = results_g1[tiers[-1]]["e_class_distribution"]
    for e_class, count in last_dist.items():
        pct = count / 10_000 * 100
        print(f"  {e_class.name}: {count:,} ({pct:.1f}%)")

    print()
    print("-" * 60)
    print()

    # Now test G2 configuration with CBD_E3
    config_g2 = GeneratorConfig(
        control_weight=0.20,
        attack_weights=V052_RUNG_G2_ATTACK_WEIGHTS.copy(),
    )

    print("Configuration (G2 - CBD E3 Stress):")
    print(f"  control_weight: {config_g2.control_weight}")
    print(f"  attack_weights: {list(config_g2.attack_weights.keys())}")
    print()

    gen_g2 = SuccessorGenerator(
        sentinel_id="sanity_sentinel",
        baseline_manifest=baseline_manifest,
        config=config_g2,
        seed=42,
    )

    result_g2_e3 = dry_sample_tier(gen_g2, ExpressivityClass.E3, num_draws=10_000)
    rate_pct = result_g2_e3["acceptance_rate"] * 100
    print(f"  E3 (G2 config): {result_g2_e3['matches']:,}/{result_g2_e3['draws']:,} = {rate_pct:.1f}% acceptance")

    print()
    print("E-Class distribution (G2 config):")
    g2_dist = result_g2_e3["e_class_distribution"]
    for e_class, count in g2_dist.items():
        pct = count / 10_000 * 100
        print(f"  {e_class.name}: {count:,} ({pct:.1f}%)")

    print()
    print("=" * 60)
    print("Sanity check complete.")
    print("=" * 60)

    # Check for any zero acceptance rates
    any_zero = False
    for tier, result in results_g1.items():
        if result["acceptance_rate"] == 0:
            print(f"\nWARNING: {tier.name} has 0% acceptance rate!")
            any_zero = True

    if result_g2_e3["acceptance_rate"] == 0:
        print("\nWARNING: G2 E3 has 0% acceptance rate!")
        any_zero = True

    if not any_zero:
        print("\n✓ All tiers have non-zero acceptance rates.")


if __name__ == "__main__":
    main()
