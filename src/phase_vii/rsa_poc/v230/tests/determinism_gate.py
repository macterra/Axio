"""SAM Determinism Verification Gate

Ensures SAM implementations satisfy the determinism invariant:
"SAM must be deterministic under replay."

Given the same:
- Master seed
- Episode ID
- Sequence of observable signals

SAM must produce:
- Identical sequence of pressures
- Identical RNG state hashes
- Identical state snapshots

This is critical for:
1. Reproducibility of experiments
2. Audit verification
3. Debugging
"""

import hashlib
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from ..adversary import (
    SAM,
    SAMProfile,
    ObservableSignals,
    AdversaryPressure,
    AdversaryInteractionRecord,
    create_sam,
)


@dataclass(frozen=True)
class DeterminismCheckResult:
    """Result of determinism verification."""
    passed: bool
    sam_profile: str
    num_steps: int
    num_mismatches: int
    first_mismatch_step: Optional[int]
    mismatch_details: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "sam_profile": self.sam_profile,
            "num_steps": self.num_steps,
            "num_mismatches": self.num_mismatches,
            "first_mismatch_step": self.first_mismatch_step,
            "mismatch_details": self.mismatch_details,
        }


class SAMDeterminismGate:
    """
    Verification gate for SAM determinism.

    Usage:
        gate = SAMDeterminismGate()
        signals = [...]  # Sequence of ObservableSignals
        result = gate.verify(SAMProfile.S2_MODEL_BASED, seed=42, signals=signals)
        assert result.passed, f"Determinism check failed: {result.mismatch_details}"
    """

    def verify(
        self,
        profile: SAMProfile,
        seed: int,
        signals: List[ObservableSignals],
        num_replays: int = 3,
    ) -> DeterminismCheckResult:
        """
        Verify SAM determinism by running multiple replays.

        Args:
            profile: SAM profile to test
            seed: Master seed
            signals: Sequence of observable signals to replay
            num_replays: Number of replay attempts

        Returns:
            DeterminismCheckResult with verification outcome
        """
        if not signals:
            return DeterminismCheckResult(
                passed=True,
                sam_profile=profile.value,
                num_steps=0,
                num_mismatches=0,
                first_mismatch_step=None,
                mismatch_details=[],
            )

        # Run first pass to get reference sequence
        reference_records = self._run_sam(profile, seed, signals)

        # Run replays and compare
        mismatches: List[Dict[str, Any]] = []
        first_mismatch: Optional[int] = None

        for replay_idx in range(num_replays):
            replay_records = self._run_sam(profile, seed, signals)

            for step_idx, (ref, rep) in enumerate(zip(reference_records, replay_records)):
                mismatch = self._compare_records(ref, rep, step_idx, replay_idx)
                if mismatch:
                    mismatches.append(mismatch)
                    if first_mismatch is None:
                        first_mismatch = step_idx

        return DeterminismCheckResult(
            passed=len(mismatches) == 0,
            sam_profile=profile.value,
            num_steps=len(signals),
            num_mismatches=len(mismatches),
            first_mismatch_step=first_mismatch,
            mismatch_details=mismatches[:10],  # Limit to first 10
        )

    def _run_sam(
        self,
        profile: SAMProfile,
        seed: int,
        signals: List[ObservableSignals],
    ) -> List[AdversaryInteractionRecord]:
        """Run SAM through signal sequence and collect records."""
        # For NEUTRALIZED, we need to provide pressure_magnitudes
        if profile == SAMProfile.NEUTRALIZED:
            # Use uniform pressure for determinism testing
            pressure_magnitudes = [1.0] * len(signals)
            sam = create_sam(profile, seed, pressure_magnitudes=pressure_magnitudes)
        else:
            sam = create_sam(profile, seed)
        sam.start_episode("determinism_test")

        records = []
        for signal in signals:
            _, record = sam.step(signal)
            records.append(record)

        return records

    def _compare_records(
        self,
        ref: AdversaryInteractionRecord,
        rep: AdversaryInteractionRecord,
        step_idx: int,
        replay_idx: int,
    ) -> Optional[Dict[str, Any]]:
        """Compare two records for determinism."""
        mismatches = []

        # Check RNG state hash (primary determinism indicator)
        if ref.rng_state_hash != rep.rng_state_hash:
            mismatches.append({
                "field": "rng_state_hash",
                "reference": ref.rng_state_hash,
                "replay": rep.rng_state_hash,
            })

        # Check pressure values
        if ref.pressure != rep.pressure:
            mismatches.append({
                "field": "pressure",
                "reference": ref.pressure,
                "replay": rep.pressure,
            })

        # Check state snapshot
        if ref.state_snapshot != rep.state_snapshot:
            mismatches.append({
                "field": "state_snapshot",
                "reference": ref.state_snapshot,
                "replay": rep.state_snapshot,
            })

        if mismatches:
            return {
                "step_idx": step_idx,
                "replay_idx": replay_idx,
                "mismatches": mismatches,
            }

        return None


def generate_test_signals(num_steps: int, seed: int) -> List[ObservableSignals]:
    """
    Generate test signals for determinism verification.

    Creates a reproducible sequence of signals.
    """
    import random
    rng = random.Random(seed)

    signals = []
    for step_idx in range(num_steps):
        signals.append(ObservableSignals(
            step_index=step_idx,
            episode_id=f"test_ep_{seed}",
            last_friction_bits=rng.random() * 0.8,
            last_outcome_code=rng.choice(["SUCCESS", "FAILURE", "TIMEOUT"]),
            last_latency_ms=rng.randint(50, 500),
            last_compile_success=rng.random() > 0.2,
            last_compile_error_code=None if rng.random() > 0.2 else "E_TEST",
            friction_sum_last_10=rng.random() * 5,
            failure_count_last_10=rng.randint(0, 3),
            gridlock_count_last_10=rng.randint(0, 2),
        ))

    return signals


def run_determinism_gate_all_profiles(
    num_steps: int = 50,
    seed: int = 42,
) -> Dict[str, DeterminismCheckResult]:
    """
    Run determinism verification on all SAM profiles.

    Returns dict mapping profile name to result.
    """
    gate = SAMDeterminismGate()
    signals = generate_test_signals(num_steps, seed)

    results = {}
    for profile in SAMProfile:
        result = gate.verify(profile, seed, signals)
        results[profile.value] = result

    return results


__all__ = [
    "SAMDeterminismGate",
    "DeterminismCheckResult",
    "generate_test_signals",
    "run_determinism_gate_all_profiles",
]
