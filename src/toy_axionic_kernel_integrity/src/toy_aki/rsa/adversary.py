"""
RSA v0.1 Adversary.

Implements deterministic verifier-outcome corruption using stateless hash-based
flip decisions. No RNG state is maintained; flips are computed as pure functions
of (seed_rsa, epoch, key, stage).
"""

import struct
from dataclasses import dataclass
from typing import Optional, Tuple

from toy_aki.rsa.config import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.telemetry import RSAEpochRecord


def stable_hash_64(seed: int, *args) -> int:
    """
    Compute a stable 64-bit hash from seed and arbitrary arguments.

    Uses FNV-1a hash algorithm for determinism across Python versions.
    Does NOT use Python's randomized hash().

    Args:
        seed: Base seed value
        *args: Additional values to incorporate (converted to strings)

    Returns:
        64-bit unsigned integer hash
    """
    # FNV-1a 64-bit constants
    FNV_PRIME = 0x00000100000001B3
    FNV_OFFSET = 0xcbf29ce484222325

    # Build input bytes
    components = [str(seed)] + [str(arg) for arg in args]
    data = "|".join(components).encode("utf-8")

    # FNV-1a hash
    h = FNV_OFFSET
    for byte in data:
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF

    return h


@dataclass
class CorruptionResult:
    """Result of a single corruption decision."""

    key: str  # "C0", "C1", "C2", or "SEM_PASS"
    original: bool
    corrupted: bool
    flipped: bool

    @property
    def changed(self) -> bool:
        return self.original != self.corrupted


class RSAAdversary:
    """
    RSA v0.1 Adversary: Deterministic verifier-outcome corruption.

    Key properties:
    - Stateless flip decisions (pure function of seed/epoch/key)
    - No RNG stream state (cannot contaminate other RNG)
    - Action-independent (cannot observe agent traces)
    - Kernel-inaccessible (harness-resident only)

    Usage:
        adversary = RSAAdversary(config, run_seed)
        c0_ok, c1_ok, c2_ok, sem_pass, record = adversary.corrupt(
            epoch, c0_raw, c1_raw, c2_raw, sem_pass_raw
        )
    """

    def __init__(self, config: RSAConfig, run_seed: int):
        """
        Initialize adversary.

        Args:
            config: RSA configuration
            run_seed: Base run seed for reproducibility
        """
        self._config = config
        self._run_seed = run_seed

        # Derive RSA-specific seed
        self._seed_rsa = stable_hash_64(run_seed, "rsa", config.rsa_rng_stream)

    @classmethod
    def from_config(
        cls,
        config: Optional[RSAConfig],
        run_seed: int,
    ) -> Optional["RSAAdversary"]:
        """
        Create adversary from config, or None if RSA is disabled.

        Args:
            config: RSA config (may be None)
            run_seed: Base run seed

        Returns:
            RSAAdversary if RSA is enabled, None otherwise
        """
        if config is None or not config.rsa_enabled:
            return None
        return cls(config, run_seed)

    def _should_flip(self, epoch: int, key: str, stage: str) -> bool:
        """
        Determine if a boolean should be flipped.

        Pure function of (seed_rsa, epoch, key, stage).
        No dependence on agent actions, traces, or current boolean values.

        Args:
            epoch: Current epoch index
            key: Boolean identifier ("C0", "C1", "C2", or "SEM_PASS")
            stage: Processing stage ("commitment" or "aggregate")

        Returns:
            True if the boolean should be flipped
        """
        if self._config.rsa_noise_model == RSANoiseModel.NONE:
            return False

        if self._config.rsa_p_flip_ppm == 0:
            return False

        # Stateless hash-based flip decision
        u64 = stable_hash_64(self._seed_rsa, epoch, key, stage)
        threshold = u64 % 1_000_000
        return threshold < self._config.rsa_p_flip_ppm

    def maybe_corrupt(
        self,
        value: bool,
        epoch: int,
        key: str,
        stage: str,
    ) -> Tuple[bool, bool]:
        """
        Maybe corrupt a single boolean.

        Args:
            value: Original boolean value
            epoch: Current epoch index
            key: Boolean identifier
            stage: Processing stage

        Returns:
            Tuple of (corrupted_value, was_flipped)
        """
        if not self._config.is_active():
            return (value, False)

        should_flip = self._should_flip(epoch, key, stage)
        if should_flip:
            return (not value, True)
        return (value, False)

    def corrupt(
        self,
        epoch: int,
        c0_raw: bool,
        c1_raw: bool,
        c2_raw: bool,
        sem_pass_raw: bool,
    ) -> Tuple[bool, bool, bool, bool, RSAEpochRecord]:
        """
        Apply corruption to verifier outcomes.

        Per spec §7:
        - PER_CI: corrupt each Ci_OK independently, recompute SEM_PASS
        - SEM_PASS_ONLY: corrupt only the aggregate SEM_PASS

        Args:
            epoch: Current epoch index
            c0_raw: Raw C0_OK value from verifier
            c1_raw: Raw C1_OK value from verifier
            c2_raw: Raw C2_OK value from verifier
            sem_pass_raw: Raw SEM_PASS value (c0 and c1 and c2)

        Returns:
            Tuple of (c0_ok, c1_ok, c2_ok, sem_pass, epoch_record)
        """
        flips_by_key = {"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0}

        if self._config.rsa_scope == RSAScope.PER_CI:
            # Corrupt each Ci_OK independently
            c0_ok, c0_flip = self.maybe_corrupt(c0_raw, epoch, "C0", "commitment")
            c1_ok, c1_flip = self.maybe_corrupt(c1_raw, epoch, "C1", "commitment")
            c2_ok, c2_flip = self.maybe_corrupt(c2_raw, epoch, "C2", "commitment")

            # Recompute SEM_PASS from potentially corrupted values
            sem_pass = c0_ok and c1_ok and c2_ok

            flips_by_key["C0"] = 1 if c0_flip else 0
            flips_by_key["C1"] = 1 if c1_flip else 0
            flips_by_key["C2"] = 1 if c2_flip else 0
            total_flips = sum(flips_by_key.values())
            targets = 3  # PER_CI has 3 targets per epoch

        else:  # SEM_PASS_ONLY
            # Keep Ci values unchanged, corrupt only aggregate
            c0_ok = c0_raw
            c1_ok = c1_raw
            c2_ok = c2_raw
            sem_pass, sem_flip = self.maybe_corrupt(
                sem_pass_raw, epoch, "SEM_PASS", "aggregate"
            )

            flips_by_key["SEM_PASS"] = 1 if sem_flip else 0
            total_flips = flips_by_key["SEM_PASS"]
            targets = 1  # SEM_PASS_ONLY has 1 target per epoch

        # Create telemetry record
        record = RSAEpochRecord(
            epoch=epoch,
            targets=targets,
            flips=total_flips,
            flips_by_key=flips_by_key,
            p_flip_ppm=self._config.rsa_p_flip_ppm,
            c0_raw=c0_raw,
            c1_raw=c1_raw,
            c2_raw=c2_raw,
            sem_pass_raw=sem_pass_raw,
            c0_corrupted=c0_ok,
            c1_corrupted=c1_ok,
            c2_corrupted=c2_ok,
            sem_pass_corrupted=sem_pass,
        )

        return (c0_ok, c1_ok, c2_ok, sem_pass, record)

    def create_lapse_epoch_record(self, epoch: int) -> RSAEpochRecord:
        """
        Create a telemetry record for an epoch during NULL_AUTHORITY.

        During lapse, no commitment evaluation occurs, so RSA has zero targets.

        Args:
            epoch: Current epoch index

        Returns:
            RSAEpochRecord with zero targets/flips
        """
        return RSAEpochRecord(
            epoch=epoch,
            targets=0,
            flips=0,
            flips_by_key={"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0},
            p_flip_ppm=self._config.rsa_p_flip_ppm,
            c0_raw=None,
            c1_raw=None,
            c2_raw=None,
            sem_pass_raw=None,
            c0_corrupted=None,
            c1_corrupted=None,
            c2_corrupted=None,
            sem_pass_corrupted=None,
            in_lapse=True,
        )

    @property
    def seed_rsa(self) -> int:
        """Return the derived RSA seed for telemetry."""
        return self._seed_rsa

    @property
    def config(self) -> RSAConfig:
        """Return the RSA configuration."""
        return self._config
