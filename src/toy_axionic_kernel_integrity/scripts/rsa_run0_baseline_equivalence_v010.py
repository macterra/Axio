#!/usr/bin/env python3
"""
RSA v0.1 Run 0: Baseline Equivalence Test.

Per spec §9.1 and §9.2:
- Verify RSA disabled matches pre-RSA baseline
- Verify RSA enabled with p_flip=0 matches baseline

This validates that RSA code presence does not contaminate AKI behavior.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope


def run_baseline_equivalence():
    """Run baseline equivalence tests."""
    print("=" * 70)
    print("RSA v0.1 Run 0: Baseline Equivalence Test")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    # Standard AKI v0.8 configuration (matching Run A parameters)
    config = ALSConfigV080(
        max_cycles=5000,
        eligibility_threshold_k=3,
        max_successive_renewals=3,
        amnesty_interval=10,
        amnesty_decay=1,
        cta_enabled=True,
    )

    seeds = [40, 41, 42, 43, 44]

    print("Configuration:")
    print(f"  Max cycles: {config.max_cycles}")
    print(f"  Eligibility K: {config.eligibility_threshold_k}")
    print(f"  Max renewals: {config.max_successive_renewals}")
    print(f"  Amnesty interval: {config.amnesty_interval}")
    print(f"  Seeds: {seeds}")
    print()

    # Test 1: No RSA vs RSA disabled
    print("-" * 70)
    print("Test 1: No RSA vs RSA Disabled (rsa_enabled=False)")
    print("-" * 70)

    all_match = True
    for seed in seeds:
        # Baseline (no RSA)
        h1 = ALSHarnessV080(seed=seed, config=config)
        r1 = h1.run()

        # RSA disabled
        rsa_cfg = RSAConfig(rsa_enabled=False)
        h2 = ALSHarnessV080(seed=seed, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        match = (
            r1.s_star == r2.s_star and
            r1.total_cycles == r2.total_cycles and
            r1.recovery_count == r2.recovery_count and
            r1.amnesty_event_count == r2.amnesty_event_count and
            r1.total_renewals == r2.total_renewals and
            r1.authority_uptime_cycles == r2.authority_uptime_cycles and
            r2.rsa is None
        )

        status = "✓ MATCH" if match else "✗ MISMATCH"
        print(f"  Seed {seed}: {status}")
        if not match:
            all_match = False
            print(f"    Baseline: S*={r1.s_star}, rec={r1.recovery_count}, amnesty={r1.amnesty_event_count}")
            print(f"    RSA off:  S*={r2.s_star}, rec={r2.recovery_count}, amnesty={r2.amnesty_event_count}")

    print()
    if all_match:
        print("  RESULT: ✓ RSA disabled equivalence VALIDATED")
    else:
        print("  RESULT: ✗ RSA disabled equivalence FAILED")

    # Test 2: No RSA vs RSA with p_flip=0
    print()
    print("-" * 70)
    print("Test 2: No RSA vs RSA Enabled with p_flip=0")
    print("-" * 70)

    all_match = True
    for seed in seeds:
        # Baseline (no RSA)
        h1 = ALSHarnessV080(seed=seed, config=config)
        r1 = h1.run()

        # RSA enabled with p_flip=0
        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=0,
        )
        h2 = ALSHarnessV080(seed=seed, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        match = (
            r1.s_star == r2.s_star and
            r1.total_cycles == r2.total_cycles and
            r1.recovery_count == r2.recovery_count and
            r1.amnesty_event_count == r2.amnesty_event_count and
            r1.total_renewals == r2.total_renewals and
            r1.authority_uptime_cycles == r2.authority_uptime_cycles and
            r2.rsa is not None and
            r2.rsa["summary"]["total_flips"] == 0
        )

        status = "✓ MATCH" if match else "✗ MISMATCH"
        flips = r2.rsa["summary"]["total_flips"] if r2.rsa else "N/A"
        print(f"  Seed {seed}: {status} (flips={flips})")
        if not match:
            all_match = False
            print(f"    Baseline: S*={r1.s_star}, rec={r1.recovery_count}")
            print(f"    RSA p=0:  S*={r2.s_star}, rec={r2.recovery_count}")

    print()
    if all_match:
        print("  RESULT: ✓ p_flip=0 equivalence VALIDATED")
    else:
        print("  RESULT: ✗ p_flip=0 equivalence FAILED")

    # Test 3: Semantic epoch trace identity
    print()
    print("-" * 70)
    print("Test 3: Semantic Epoch Trace Identity")
    print("-" * 70)

    all_match = True
    for seed in seeds:
        # Baseline (no RSA)
        h1 = ALSHarnessV080(seed=seed, config=config)
        r1 = h1.run()

        # RSA enabled with p_flip=0
        rsa_cfg = RSAConfig(
            rsa_enabled=True,
            rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
            rsa_p_flip_ppm=0,
        )
        h2 = ALSHarnessV080(seed=seed, config=config, rsa_config=rsa_cfg)
        r2 = h2.run()

        # Compare semantic epoch records
        records_match = len(r1.semantic_epoch_records) == len(r2.semantic_epoch_records)
        if records_match:
            for rec1, rec2 in zip(r1.semantic_epoch_records, r2.semantic_epoch_records):
                if (rec1["c0_ok"] != rec2["c0_ok"] or
                    rec1["c1_ok"] != rec2["c1_ok"] or
                    rec1["c2_ok"] != rec2["c2_ok"] or
                    rec1["sem_pass"] != rec2["sem_pass"]):
                    records_match = False
                    break

        status = "✓ MATCH" if records_match else "✗ MISMATCH"
        n_records = len(r1.semantic_epoch_records)
        print(f"  Seed {seed}: {status} ({n_records} epochs)")
        if not records_match:
            all_match = False

    print()
    if all_match:
        print("  RESULT: ✓ Semantic trace identity VALIDATED")
    else:
        print("  RESULT: ✗ Semantic trace identity FAILED")

    print()
    print("=" * 70)
    print("BASELINE EQUIVALENCE TEST COMPLETE")
    print("=" * 70)

    return all_match


if __name__ == "__main__":
    success = run_baseline_equivalence()
    sys.exit(0 if success else 1)
