"""
RSA v0.1/v0.2 Adversary.

Implements deterministic verifier-outcome corruption using stateless hash-based
flip decisions. No RNG state is maintained; flips are computed as pure functions
of (seed_rsa, epoch, key, stage).

v0.1: FLIP_BERNOULLI model
v0.2: Adds AGG_FLIP_BERNOULLI, COMMITMENT_KEYED_FLIP, BURST_SCHEDULED_FLIP
"""

import struct
from dataclasses import dataclass
from typing import Optional, Tuple, Callable

from toy_aki.rsa.config import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.telemetry import RSAEpochRecord
from toy_aki.rsa.schedule import compute_burst_phase, BurstPhase


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
    RSA v0.1/v0.2 Adversary: Deterministic verifier-outcome corruption.

    Key properties:
    - Stateless flip decisions (pure function of seed/epoch/key)
    - No RNG stream state (cannot contaminate other RNG)
    - Action-independent (cannot observe agent traces)
    - Kernel-inaccessible (harness-resident only)

    v0.2 models:
    - AGG_FLIP_BERNOULLI: Corrupt only SEM_PASS (aggregation point)
    - COMMITMENT_KEYED_FLIP: Corrupt only one targeted Ci key
    - BURST_SCHEDULED_FLIP: Periodic burst schedule with phase-dependent rates

    Usage:
        adversary = RSAAdversary(config, run_seed)
        c0_ok, c1_ok, c2_ok, sem_pass, record = adversary.corrupt(
            epoch, c0_raw, c1_raw, c2_raw, sem_pass_raw,
            aggregator=lambda c0, c1, c2: c0 and c1 and c2,
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

        # Determine effective flip probability based on model
        p_flip_ppm = self._get_effective_p_flip_ppm(epoch, key)

        if p_flip_ppm == 0:
            return False

        # Stateless hash-based flip decision
        u64 = stable_hash_64(self._seed_rsa, epoch, key, stage)
        threshold = u64 % 1_000_000
        return threshold < p_flip_ppm

    def _get_effective_p_flip_ppm(self, epoch: int, key: str) -> int:
        """
        Get effective flip probability based on model and phase.

        Args:
            epoch: Current epoch index
            key: Target key

        Returns:
            Effective flip probability in PPM
        """
        model = self._config.rsa_noise_model

        # v0.1: FLIP_BERNOULLI
        if model == RSANoiseModel.FLIP_BERNOULLI:
            return self._config.rsa_p_flip_ppm

        # v0.2 Model A: AGG_FLIP_BERNOULLI (only SEM_PASS)
        if model == RSANoiseModel.AGG_FLIP_BERNOULLI:
            return self._config.rsa_p_flip_ppm

        # v0.2 Model B: COMMITMENT_KEYED_FLIP (only target key)
        if model == RSANoiseModel.COMMITMENT_KEYED_FLIP:
            if key == self._config.rsa_target_key:
                return self._config.rsa_p_target_flip_ppm
            return 0

        # v0.2 Model C: BURST_SCHEDULED_FLIP (phase-dependent)
        if model == RSANoiseModel.BURST_SCHEDULED_FLIP:
            phase = compute_burst_phase(
                epoch=epoch,
                period=self._config.rsa_burst_period_epochs,
                width=self._config.rsa_burst_width_epochs,
                phase_offset=self._config.rsa_burst_phase_offset,
            )
            if phase == BurstPhase.ACTIVE:
                return self._config.rsa_p_burst_flip_ppm
            else:
                return self._config.rsa_p_quiet_flip_ppm

        return 0

    def _get_current_phase(self, epoch: int) -> Optional[str]:
        """Get current burst phase as string, or None for non-burst models."""
        if self._config.rsa_noise_model != RSANoiseModel.BURST_SCHEDULED_FLIP:
            return None

        phase = compute_burst_phase(
            epoch=epoch,
            period=self._config.rsa_burst_period_epochs,
            width=self._config.rsa_burst_width_epochs,
            phase_offset=self._config.rsa_burst_phase_offset,
        )
        return phase.value

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
        aggregator: Optional[Callable[[bool, bool, bool], bool]] = None,
    ) -> Tuple[bool, bool, bool, bool, RSAEpochRecord]:
        """
        Apply corruption to verifier outcomes.

        v0.1 behavior:
        - PER_CI: corrupt each Ci_OK independently, recompute SEM_PASS
        - SEM_PASS_ONLY: corrupt only the aggregate SEM_PASS

        v0.2 behavior:
        - AGG_FLIP_BERNOULLI: corrupt only SEM_PASS (Model A)
        - COMMITMENT_KEYED_FLIP: corrupt only target key, recompute SEM_PASS (Model B)
        - BURST_SCHEDULED_FLIP: phase-dependent corruption (Model C)

        Args:
            epoch: Current epoch index
            c0_raw: Raw C0_OK value from verifier
            c1_raw: Raw C1_OK value from verifier
            c2_raw: Raw C2_OK value from verifier
            sem_pass_raw: Raw SEM_PASS value (c0 and c1 and c2)
            aggregator: Callable to recompute SEM_PASS from Ci values.
                        MUST be the exact AKI aggregation function (not a reimplementation).
                        For v0.2, this parameter is REQUIRED; pass ALSHarnessV080._aggregate_sem_pass.
                        For v0.1 backward compatibility only, None falls back to `c0 and c1 and c2`.

        Returns:
            Tuple of (c0_ok, c1_ok, c2_ok, sem_pass, epoch_record)
        """
        # v0.1 backward compatibility: if no aggregator provided, use inline AND
        # v0.2 MUST pass the real AKI aggregator; this fallback is DEPRECATED for v0.2
        if aggregator is None:
            import warnings
            if self._config.rsa_noise_model in (
                RSANoiseModel.AGG_FLIP_BERNOULLI,
                RSANoiseModel.COMMITMENT_KEYED_FLIP,
                RSANoiseModel.BURST_SCHEDULED_FLIP,
            ):
                warnings.warn(
                    "v0.2 models SHOULD pass AKI's aggregator; using fallback AND logic",
                    UserWarning,
                )
            aggregator = lambda c0, c1, c2: c0 and c1 and c2

        model = self._config.rsa_noise_model
        scope = self._config.rsa_scope
        phase = self._get_current_phase(epoch)
        p_effective = self._get_effective_p_flip_ppm(epoch, "SEM_PASS")  # Default key

        flips_by_key = {"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0}
        c0_ok, c1_ok, c2_ok = c0_raw, c1_raw, c2_raw
        sem_pass = sem_pass_raw

        # ========== v0.1: FLIP_BERNOULLI ==========
        if model == RSANoiseModel.FLIP_BERNOULLI:
            if scope == RSAScope.PER_CI:
                # Corrupt each Ci_OK independently
                c0_ok, c0_flip = self.maybe_corrupt(c0_raw, epoch, "C0", "commitment")
                c1_ok, c1_flip = self.maybe_corrupt(c1_raw, epoch, "C1", "commitment")
                c2_ok, c2_flip = self.maybe_corrupt(c2_raw, epoch, "C2", "commitment")

                # Recompute SEM_PASS using aggregator (not inline AND)
                sem_pass = aggregator(c0_ok, c1_ok, c2_ok)

                flips_by_key["C0"] = 1 if c0_flip else 0
                flips_by_key["C1"] = 1 if c1_flip else 0
                flips_by_key["C2"] = 1 if c2_flip else 0
                targets = 3

            else:  # SEM_PASS_ONLY
                sem_pass, sem_flip = self.maybe_corrupt(
                    sem_pass_raw, epoch, "SEM_PASS", "aggregate"
                )
                flips_by_key["SEM_PASS"] = 1 if sem_flip else 0
                targets = 1

        # ========== v0.2 Model A: AGG_FLIP_BERNOULLI ==========
        elif model == RSANoiseModel.AGG_FLIP_BERNOULLI:
            # Only corrupt aggregation point (SEM_PASS)
            sem_pass, sem_flip = self.maybe_corrupt(
                sem_pass_raw, epoch, "SEM_PASS", "aggregate"
            )
            flips_by_key["SEM_PASS"] = 1 if sem_flip else 0
            targets = 1
            p_effective = self._config.rsa_p_flip_ppm

        # ========== v0.2 Model B: COMMITMENT_KEYED_FLIP ==========
        elif model == RSANoiseModel.COMMITMENT_KEYED_FLIP:
            # Corrupt only the target key
            target = self._config.rsa_target_key
            p_effective = self._config.rsa_p_target_flip_ppm

            if target == "C0":
                c0_ok, c0_flip = self.maybe_corrupt(c0_raw, epoch, "C0", "commitment")
                flips_by_key["C0"] = 1 if c0_flip else 0
            elif target == "C1":
                c1_ok, c1_flip = self.maybe_corrupt(c1_raw, epoch, "C1", "commitment")
                flips_by_key["C1"] = 1 if c1_flip else 0
            elif target == "C2":
                c2_ok, c2_flip = self.maybe_corrupt(c2_raw, epoch, "C2", "commitment")
                flips_by_key["C2"] = 1 if c2_flip else 0

            # Recompute SEM_PASS using aggregator
            sem_pass = aggregator(c0_ok, c1_ok, c2_ok)
            targets = 1

        # ========== v0.2 Model C: BURST_SCHEDULED_FLIP ==========
        elif model == RSANoiseModel.BURST_SCHEDULED_FLIP:
            # Scope determines what gets corrupted; phase determines rate
            if scope == RSAScope.SEM_PASS_ONLY:
                sem_pass, sem_flip = self.maybe_corrupt(
                    sem_pass_raw, epoch, "SEM_PASS", "aggregate"
                )
                flips_by_key["SEM_PASS"] = 1 if sem_flip else 0
                targets = 1
            else:  # PER_CI
                c0_ok, c0_flip = self.maybe_corrupt(c0_raw, epoch, "C0", "commitment")
                c1_ok, c1_flip = self.maybe_corrupt(c1_raw, epoch, "C1", "commitment")
                c2_ok, c2_flip = self.maybe_corrupt(c2_raw, epoch, "C2", "commitment")
                sem_pass = aggregator(c0_ok, c1_ok, c2_ok)

                flips_by_key["C0"] = 1 if c0_flip else 0
                flips_by_key["C1"] = 1 if c1_flip else 0
                flips_by_key["C2"] = 1 if c2_flip else 0
                targets = 3

            p_effective = self._get_effective_p_flip_ppm(epoch, "SEM_PASS")

        else:  # NONE or unknown
            targets = 0

        total_flips = sum(flips_by_key.values())

        # Create telemetry record
        record = RSAEpochRecord(
            epoch=epoch,
            targets=targets,
            flips=total_flips,
            flips_by_key=flips_by_key,
            p_flip_ppm=p_effective,
            c0_raw=c0_raw,
            c1_raw=c1_raw,
            c2_raw=c2_raw,
            sem_pass_raw=sem_pass_raw,
            c0_corrupted=c0_ok,
            c1_corrupted=c1_ok,
            c2_corrupted=c2_ok,
            sem_pass_corrupted=sem_pass,
            phase=phase,  # v0.2: burst phase
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
