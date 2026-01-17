"""Calibration script for v3.1 buffer size N.

Runs simulation to measure typical precedent record token lengths,
then calculates and freezes N for all subsequent runs.

Binding formula: N = max(512, ceil_to_32(1.25 × max(observed)))
"""

import json
import random
from typing import Set, Tuple, List

from .tokenizer import get_tokenizer, PAD_STR
from .gate_p4 import GateP4, GateP4Config, serialize_precedent_record, ceil_to_32


# Realistic constraint IDs from the system
BELIEF_IDS = [
    "B_COOPERATION_MATTERS",
    "B_LOCKS_PROTECT",
    "B_TRUTH_BUILDS_TRUST",
    "B_SHARING_HELPS",
    "B_HELP_CREATES_GOOD",
    "B_EXPLOITATION_HARMS",
]

PREFERENCE_IDS = [
    "P_NO_DEFECT",
    "P_NO_BREAK_LOCKS",
    "P_NO_LIE",
    "P_NO_HOARD",
    "P_NO_EXPLOIT",
    "P_PREFER_COOPERATION",
]


def generate_synthetic_precedent(
    rng: random.Random,
    step: int,
    av_count: int = None,
    rp_count: int = None,
    ca_count: int = None,
) -> Tuple[Set[str], Set[str], Set[Tuple[str, str]], str]:
    """Generate a synthetic precedent record for calibration.

    Args:
        rng: Random generator for reproducibility
        step: Step index
        av_count: Number of authorized violations (random if None)
        rp_count: Number of required preservations (random if None)
        ca_count: Number of conflict attributions (random if None)

    Returns:
        Tuple of (AV, RP, CA, digest)
    """
    if av_count is None:
        av_count = rng.randint(0, 3)
    if rp_count is None:
        rp_count = rng.randint(1, 4)
    if ca_count is None:
        ca_count = rng.randint(0, 3)

    # Generate authorized violations
    av = set(rng.sample(PREFERENCE_IDS, min(av_count, len(PREFERENCE_IDS))))

    # Generate required preservations (must have at least 1)
    rp = set(rng.sample(PREFERENCE_IDS, min(rp_count, len(PREFERENCE_IDS))))
    if not rp:
        rp = {rng.choice(PREFERENCE_IDS)}

    # Generate conflict attributions (belief, preference pairs)
    ca = set()
    for _ in range(ca_count):
        belief = rng.choice(BELIEF_IDS)
        pref = rng.choice(PREFERENCE_IDS)
        ca.add((belief, pref))

    # Generate digest (16 hex chars)
    digest = f"{rng.getrandbits(64):016x}"

    return av, rp, ca, digest


def run_calibration(
    num_seeds: int = 3,
    steps_per_seed: int = 50,
    verbose: bool = True,
) -> int:
    """Run calibration to determine buffer size N.

    Args:
        num_seeds: Number of seeds to calibrate with
        steps_per_seed: Steps per seed
        verbose: Print progress

    Returns:
        Calculated buffer size N (frozen after this)
    """
    tokenizer = get_tokenizer()

    if verbose:
        print("v3.1 Buffer Size Calibration")
        print("=" * 50)
        print(f"Tokenizer: {tokenizer._tokenizer_id} v{tokenizer._tokenizer_version}")
        print(f"PAD: {repr(PAD_STR)} ({tokenizer.count_tokens(PAD_STR)} tokens)")
        print(f"Seeds: {num_seeds}, Steps/seed: {steps_per_seed}")
        print()

    all_token_counts = []

    for seed in range(num_seeds):
        rng = random.Random(42 + seed * 1000)
        seed_counts = []

        for step in range(steps_per_seed):
            # Generate synthetic precedent
            av, rp, ca, digest = generate_synthetic_precedent(rng, step)

            # Serialize
            precedent_str = serialize_precedent_record(
                authorized_violations=av,
                required_preservations=rp,
                conflict_attribution=ca,
                artifact_digest=digest,
                step_index=step,
            )

            # Count tokens
            token_count = tokenizer.count_tokens(precedent_str)
            seed_counts.append(token_count)
            all_token_counts.append(token_count)

        if verbose:
            print(f"Seed {seed}: min={min(seed_counts)}, max={max(seed_counts)}, "
                  f"avg={sum(seed_counts)/len(seed_counts):.1f}")

    # Calculate N using binding formula
    max_observed = max(all_token_counts)
    N = max(512, ceil_to_32(1.25 * max_observed))

    if verbose:
        print()
        print(f"Calibration Results:")
        print(f"  Total samples: {len(all_token_counts)}")
        print(f"  Min tokens: {min(all_token_counts)}")
        print(f"  Max tokens: {max_observed}")
        print(f"  Avg tokens: {sum(all_token_counts)/len(all_token_counts):.1f}")
        print()
        print(f"  1.25 × max = {1.25 * max_observed:.1f}")
        print(f"  ceil_to_32 = {ceil_to_32(1.25 * max_observed)}")
        print(f"  max(512, ^) = {N}")
        print()
        print(f"  *** BUFFER SIZE N = {N} ***")
        print()
        print("  This value must be frozen in GateP4Config for all runs.")

    return N


def validate_calibration(N: int, num_samples: int = 100) -> bool:
    """Validate that calibrated N handles edge cases.

    Args:
        N: Buffer size to validate
        num_samples: Number of samples to test

    Returns:
        True if all samples fit in buffer
    """
    tokenizer = get_tokenizer()
    rng = random.Random(999)

    # Test with maximum-size precedents
    failures = 0
    for i in range(num_samples):
        # Generate worst-case precedent (max counts)
        av, rp, ca, digest = generate_synthetic_precedent(
            rng, i,
            av_count=len(PREFERENCE_IDS),  # Max AV
            rp_count=len(PREFERENCE_IDS),  # Max RP
            ca_count=len(BELIEF_IDS),       # Max CA
        )

        precedent_str = serialize_precedent_record(
            authorized_violations=av,
            required_preservations=rp,
            conflict_attribution=ca,
            artifact_digest=digest,
            step_index=i,
        )

        token_count = tokenizer.count_tokens(precedent_str)
        if token_count > N:
            failures += 1
            print(f"  OVERFLOW: sample {i} has {token_count} tokens (N={N})")

    return failures == 0


if __name__ == "__main__":
    # Run calibration
    N = run_calibration(num_seeds=3, steps_per_seed=50)

    print("\nValidation (worst-case precedents):")
    if validate_calibration(N, num_samples=100):
        print("  All worst-case samples fit in buffer.")
    else:
        print("  WARNING: Some samples exceed buffer size!")
