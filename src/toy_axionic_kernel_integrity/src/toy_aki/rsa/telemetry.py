"""
RSA v0.1 Telemetry.

Data structures for recording RSA perturbation events at epoch and run level.
Required for proving flips occurred and quantifying observed vs target rates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RSAEpochRecord:
    """
    Per-epoch RSA telemetry record.

    Records what happened at each epoch where RSA could fire.
    """

    epoch: int
    targets: int  # Number of booleans eligible for corruption (0 during lapse)
    flips: int  # Number of flips that occurred
    flips_by_key: Dict[str, int]  # Flips per key (C0, C1, C2, SEM_PASS)
    p_flip_ppm: int  # Configured/effective flip probability

    # Raw values before corruption (None if in lapse)
    c0_raw: Optional[bool] = None
    c1_raw: Optional[bool] = None
    c2_raw: Optional[bool] = None
    sem_pass_raw: Optional[bool] = None

    # Values after corruption (None if in lapse)
    c0_corrupted: Optional[bool] = None
    c1_corrupted: Optional[bool] = None
    c2_corrupted: Optional[bool] = None
    sem_pass_corrupted: Optional[bool] = None

    # Lapse indicator
    in_lapse: bool = False

    # v0.2: Burst phase ("ACTIVE" or "QUIET", None for non-burst models)
    phase: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "epoch": self.epoch,
            "targets": self.targets,
            "flips": self.flips,
            "flips_by_key": self.flips_by_key,
            "p_flip_ppm": self.p_flip_ppm,
            "c0_raw": self.c0_raw,
            "c1_raw": self.c1_raw,
            "c2_raw": self.c2_raw,
            "sem_pass_raw": self.sem_pass_raw,
            "c0_corrupted": self.c0_corrupted,
            "c1_corrupted": self.c1_corrupted,
            "c2_corrupted": self.c2_corrupted,
            "sem_pass_corrupted": self.sem_pass_corrupted,
            "in_lapse": self.in_lapse,
            "phase": self.phase,
        }


@dataclass
class RSARunSummary:
    """
    Run-level RSA telemetry summary.

    Aggregates per-epoch records into run-level metrics.
    """

    # Configuration echo
    enabled: bool
    noise_model: str
    scope: str
    p_flip_ppm: int
    rng_stream: str
    seed_rsa: int

    # Aggregate metrics
    total_targets: int = 0
    total_flips: int = 0
    observed_flip_rate_ppm: int = 0
    expected_flip_rate_ppm: int = 0

    # Per-key breakdown
    flips_by_key: Dict[str, int] = field(default_factory=dict)

    # Epoch counts
    epochs_with_flips: int = 0
    epochs_in_lapse: int = 0
    epochs_evaluated: int = 0

    # v0.2: Burst-specific telemetry
    burst_duty_cycle_ppm: int = 0
    active_phase_targets: int = 0
    active_phase_flips: int = 0
    active_phase_flip_rate_ppm: int = 0
    quiet_phase_targets: int = 0
    quiet_phase_flips: int = 0
    quiet_phase_flip_rate_ppm: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "enabled": self.enabled,
            "noise_model": self.noise_model,
            "scope": self.scope,
            "p_flip_ppm": self.p_flip_ppm,
            "rng_stream": self.rng_stream,
            "seed_rsa": self.seed_rsa,
            "total_targets": self.total_targets,
            "total_flips": self.total_flips,
            "observed_flip_rate_ppm": self.observed_flip_rate_ppm,
            "expected_flip_rate_ppm": self.expected_flip_rate_ppm,
            "flips_by_key": self.flips_by_key,
            "epochs_with_flips": self.epochs_with_flips,
            "epochs_in_lapse": self.epochs_in_lapse,
            "epochs_evaluated": self.epochs_evaluated,
            # v0.2 burst telemetry
            "burst_duty_cycle_ppm": self.burst_duty_cycle_ppm,
            "active_phase_targets": self.active_phase_targets,
            "active_phase_flips": self.active_phase_flips,
            "active_phase_flip_rate_ppm": self.active_phase_flip_rate_ppm,
            "quiet_phase_targets": self.quiet_phase_targets,
            "quiet_phase_flips": self.quiet_phase_flips,
            "quiet_phase_flip_rate_ppm": self.quiet_phase_flip_rate_ppm,
        }


class RSATelemetry:
    """
    RSA telemetry aggregator.

    Collects epoch records and computes run-level summary.
    """

    def __init__(
        self,
        enabled: bool = False,
        noise_model: str = "NONE",
        scope: str = "PER_CI",
        p_flip_ppm: int = 0,
        rng_stream: str = "rsa",
        seed_rsa: int = 0,
    ):
        """Initialize telemetry collector."""
        self._enabled = enabled
        self._noise_model = noise_model
        self._scope = scope
        self._p_flip_ppm = p_flip_ppm
        self._rng_stream = rng_stream
        self._seed_rsa = seed_rsa

        self._epoch_records: List[RSAEpochRecord] = []

    def record_epoch(self, record: RSAEpochRecord) -> None:
        """Record a single epoch's RSA activity."""
        self._epoch_records.append(record)

    @property
    def epoch_records(self) -> List[RSAEpochRecord]:
        """Return all epoch records."""
        return self._epoch_records

    def summarize(self) -> RSARunSummary:
        """
        Compute run-level summary from epoch records.

        Returns:
            RSARunSummary with aggregated metrics
        """
        total_targets = 0
        total_flips = 0
        flips_by_key: Dict[str, int] = {"C0": 0, "C1": 0, "C2": 0, "SEM_PASS": 0}
        epochs_with_flips = 0
        epochs_in_lapse = 0
        epochs_evaluated = 0

        # v0.2: Burst-specific tracking
        active_epochs = 0
        active_targets = 0
        active_flips = 0
        quiet_epochs = 0
        quiet_targets = 0
        quiet_flips = 0

        for record in self._epoch_records:
            if record.in_lapse:
                epochs_in_lapse += 1
            else:
                epochs_evaluated += 1
                total_targets += record.targets
                total_flips += record.flips

                if record.flips > 0:
                    epochs_with_flips += 1

                for key, count in record.flips_by_key.items():
                    flips_by_key[key] = flips_by_key.get(key, 0) + count

                # v0.2: Track burst phase metrics
                if record.phase == "ACTIVE":
                    active_epochs += 1
                    active_targets += record.targets
                    active_flips += record.flips
                elif record.phase == "QUIET":
                    quiet_epochs += 1
                    quiet_targets += record.targets
                    quiet_flips += record.flips

        # Compute observed rate (avoid division by zero)
        if total_targets > 0:
            observed_flip_rate_ppm = (total_flips * 1_000_000) // total_targets
        else:
            observed_flip_rate_ppm = 0

        # v0.2: Compute burst telemetry
        total_burst_epochs = active_epochs + quiet_epochs
        if total_burst_epochs > 0:
            burst_duty_cycle_ppm = (active_epochs * 1_000_000) // total_burst_epochs
        else:
            burst_duty_cycle_ppm = 0

        if active_targets > 0:
            active_phase_flip_rate_ppm = (active_flips * 1_000_000) // active_targets
        else:
            active_phase_flip_rate_ppm = 0

        if quiet_targets > 0:
            quiet_phase_flip_rate_ppm = (quiet_flips * 1_000_000) // quiet_targets
        else:
            quiet_phase_flip_rate_ppm = 0

        return RSARunSummary(
            enabled=self._enabled,
            noise_model=self._noise_model,
            scope=self._scope,
            p_flip_ppm=self._p_flip_ppm,
            rng_stream=self._rng_stream,
            seed_rsa=self._seed_rsa,
            total_targets=total_targets,
            total_flips=total_flips,
            observed_flip_rate_ppm=observed_flip_rate_ppm,
            expected_flip_rate_ppm=self._p_flip_ppm,
            flips_by_key=flips_by_key,
            epochs_with_flips=epochs_with_flips,
            epochs_in_lapse=epochs_in_lapse,
            epochs_evaluated=epochs_evaluated,
            # v0.2 burst telemetry
            burst_duty_cycle_ppm=burst_duty_cycle_ppm,
            active_phase_targets=active_targets,
            active_phase_flips=active_flips,
            active_phase_flip_rate_ppm=active_phase_flip_rate_ppm,
            quiet_phase_targets=quiet_targets,
            quiet_phase_flips=quiet_flips,
            quiet_phase_flip_rate_ppm=quiet_phase_flip_rate_ppm,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize telemetry to dictionary."""
        summary = self.summarize()
        return {
            "summary": summary.to_dict(),
            "epoch_records": [r.to_dict() for r in self._epoch_records],
        }

    @property
    def total_flips(self) -> int:
        """Return total flip count across all epochs."""
        return sum(r.flips for r in self._epoch_records)

    @property
    def total_targets(self) -> int:
        """Return total target count across all epochs."""
        return sum(r.targets for r in self._epoch_records if not r.in_lapse)
