"""
RSA v0.2 Burst Schedule Module.

Pure functions for computing burst phase from epoch index.
No runtime event anchoring; all schedules are deterministic
functions of (epoch_index, static_schedule_params).
"""

from enum import Enum
from typing import NamedTuple


class BurstPhase(Enum):
    """Burst schedule phase."""
    ACTIVE = "ACTIVE"
    QUIET = "QUIET"


class BurstScheduleParams(NamedTuple):
    """Parameters for periodic burst schedule."""
    period_epochs: int
    width_epochs: int
    phase_offset: int = 0

    def validate(self) -> None:
        """Validate schedule parameters."""
        if self.period_epochs <= 0:
            raise ValueError(f"period_epochs must be > 0, got {self.period_epochs}")
        if self.width_epochs <= 0:
            raise ValueError(f"width_epochs must be > 0, got {self.width_epochs}")
        if self.width_epochs > self.period_epochs:
            raise ValueError(
                f"width_epochs ({self.width_epochs}) must be <= period_epochs ({self.period_epochs})"
            )

    @property
    def duty_cycle_ppm(self) -> int:
        """Compute duty cycle in PPM."""
        return (self.width_epochs * 1_000_000) // self.period_epochs


def compute_burst_phase(
    epoch: int,
    period: int,
    width: int,
    phase_offset: int = 0,
) -> BurstPhase:
    """
    Compute burst phase for a given epoch.

    Pure function of (epoch, period, width, phase_offset).
    Does NOT reference any dynamic system events.

    Canonical periodic rule:
        x = (epoch + phase_offset) % period
        ACTIVE iff x < width

    Args:
        epoch: Current epoch index (global, not per-authority)
        period: Burst period in epochs
        width: Burst width in epochs (active phase duration)
        phase_offset: Phase offset in epochs (default 0)

    Returns:
        BurstPhase.ACTIVE or BurstPhase.QUIET
    """
    if period <= 0:
        raise ValueError(f"period must be > 0, got {period}")

    x = (epoch + phase_offset) % period
    return BurstPhase.ACTIVE if x < width else BurstPhase.QUIET


def compute_burst_phase_from_params(
    epoch: int,
    params: BurstScheduleParams,
) -> BurstPhase:
    """
    Compute burst phase using BurstScheduleParams.

    Args:
        epoch: Current epoch index
        params: Burst schedule parameters

    Returns:
        BurstPhase.ACTIVE or BurstPhase.QUIET
    """
    return compute_burst_phase(
        epoch=epoch,
        period=params.period_epochs,
        width=params.width_epochs,
        phase_offset=params.phase_offset,
    )
