"""
RSA v0.1/v0.2 Configuration.

Defines RSAConfig with all parameters for verifier-outcome noise injection.
All probability parameters use PPM (parts-per-million) integers; no floats.

v0.1: FLIP_BERNOULLI model with PER_CI or SEM_PASS_ONLY scope
v0.2: Adds AGG_FLIP_BERNOULLI, COMMITMENT_KEYED_FLIP, BURST_SCHEDULED_FLIP
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RSANoiseModel(Enum):
    """Noise model for verifier outcome corruption."""

    # v0.1 models
    NONE = "NONE"
    FLIP_BERNOULLI = "FLIP_BERNOULLI"

    # v0.2 models
    AGG_FLIP_BERNOULLI = "AGG_FLIP_BERNOULLI"      # Run 1: aggregation-point corruption
    COMMITMENT_KEYED_FLIP = "COMMITMENT_KEYED_FLIP"  # Run 2: commitment-correlated noise
    BURST_SCHEDULED_FLIP = "BURST_SCHEDULED_FLIP"   # Run 3: burst-scheduled interference


class RSAScope(Enum):
    """Scope of RSA corruption."""

    # Corrupt each Ci_OK independently (recommended for v0.1; highest diagnostic value)
    PER_CI = "PER_CI"

    # Corrupt only the aggregate SEM_PASS (v0.2 Run 1/3 default)
    SEM_PASS_ONLY = "SEM_PASS_ONLY"

    # Corrupt only the targeted commitment key (v0.2 Run 2)
    PER_KEY = "PER_KEY"


@dataclass
class RSAConfig:
    """
    Configuration for RSA v0.1/v0.2 stress layer.

    All parameters are fixed for the run. No adaptation.
    RSA is disabled by default; when disabled, behavior is identical to AKI v0.8.

    v0.1 Attributes:
        rsa_enabled: Whether RSA is enabled. Default False.
        rsa_noise_model: Noise model to use. Default NONE.
        rsa_p_flip_ppm: Flip probability in PPM (0..1_000_000). Default 0.
        rsa_scope: Which booleans to corrupt. Default PER_CI.
        rsa_rng_stream: Label for RNG stream derivation. Default "rsa".

    v0.2 Attributes (Model B - COMMITMENT_KEYED_FLIP):
        rsa_target_key: Target commitment key ("C0", "C1", or "C2"). Default None.
        rsa_p_target_flip_ppm: Flip probability for target key. Default 0.

    v0.2 Attributes (Model C - BURST_SCHEDULED_FLIP):
        rsa_burst_period_epochs: Burst period in epochs. Default 0 (disabled).
        rsa_burst_width_epochs: Burst width in epochs. Default 0.
        rsa_burst_phase_offset: Phase offset in epochs. Default 0.
        rsa_p_burst_flip_ppm: Flip probability during ACTIVE phase. Default 0.
        rsa_p_quiet_flip_ppm: Flip probability during QUIET phase. Default 0.
    """

    # Common parameters
    rsa_enabled: bool = False
    rsa_noise_model: RSANoiseModel = RSANoiseModel.NONE
    rsa_p_flip_ppm: int = 0
    rsa_scope: RSAScope = RSAScope.PER_CI
    rsa_rng_stream: str = "rsa"

    # v0.2 Model B: COMMITMENT_KEYED_FLIP
    rsa_target_key: Optional[str] = None
    rsa_p_target_flip_ppm: int = 0

    # v0.2 Model C: BURST_SCHEDULED_FLIP
    rsa_burst_period_epochs: int = 0
    rsa_burst_width_epochs: int = 0
    rsa_burst_phase_offset: int = 0
    rsa_p_burst_flip_ppm: int = 0
    rsa_p_quiet_flip_ppm: int = 0

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Ensure p_flip_ppm values are in valid range
        for field_name in ["rsa_p_flip_ppm", "rsa_p_target_flip_ppm",
                           "rsa_p_burst_flip_ppm", "rsa_p_quiet_flip_ppm"]:
            value = getattr(self, field_name)
            if not (0 <= value <= 1_000_000):
                raise ValueError(
                    f"{field_name} must be in [0, 1_000_000], got {value}"
                )

        # Convert string enums if needed
        if isinstance(self.rsa_noise_model, str):
            self.rsa_noise_model = RSANoiseModel(self.rsa_noise_model)
        if isinstance(self.rsa_scope, str):
            self.rsa_scope = RSAScope(self.rsa_scope)

        # Validate target_key for Model B
        if self.rsa_noise_model == RSANoiseModel.COMMITMENT_KEYED_FLIP:
            if self.rsa_target_key not in ("C0", "C1", "C2"):
                raise ValueError(
                    f"rsa_target_key must be 'C0', 'C1', or 'C2' for "
                    f"COMMITMENT_KEYED_FLIP, got {self.rsa_target_key}"
                )

        # Validate burst parameters for Model C
        if self.rsa_noise_model == RSANoiseModel.BURST_SCHEDULED_FLIP:
            if self.rsa_burst_period_epochs <= 0:
                raise ValueError(
                    f"rsa_burst_period_epochs must be > 0 for "
                    f"BURST_SCHEDULED_FLIP, got {self.rsa_burst_period_epochs}"
                )
            if self.rsa_burst_width_epochs <= 0:
                raise ValueError(
                    f"rsa_burst_width_epochs must be > 0 for "
                    f"BURST_SCHEDULED_FLIP, got {self.rsa_burst_width_epochs}"
                )
            if self.rsa_burst_width_epochs > self.rsa_burst_period_epochs:
                raise ValueError(
                    f"rsa_burst_width_epochs ({self.rsa_burst_width_epochs}) "
                    f"must be <= rsa_burst_period_epochs ({self.rsa_burst_period_epochs})"
                )

    def is_active(self) -> bool:
        """Check if RSA will actually corrupt anything."""
        if not self.rsa_enabled:
            return False
        if self.rsa_noise_model == RSANoiseModel.NONE:
            return False

        # v0.1 models: FLIP_BERNOULLI
        if self.rsa_noise_model == RSANoiseModel.FLIP_BERNOULLI:
            return self.rsa_p_flip_ppm > 0

        # v0.2 Model A: AGG_FLIP_BERNOULLI
        if self.rsa_noise_model == RSANoiseModel.AGG_FLIP_BERNOULLI:
            return self.rsa_p_flip_ppm > 0

        # v0.2 Model B: COMMITMENT_KEYED_FLIP
        if self.rsa_noise_model == RSANoiseModel.COMMITMENT_KEYED_FLIP:
            return self.rsa_p_target_flip_ppm > 0

        # v0.2 Model C: BURST_SCHEDULED_FLIP
        if self.rsa_noise_model == RSANoiseModel.BURST_SCHEDULED_FLIP:
            return self.rsa_p_burst_flip_ppm > 0 or self.rsa_p_quiet_flip_ppm > 0

        return False

    def get_effective_p_flip_ppm(self, phase: Optional[str] = None) -> int:
        """
        Get effective flip probability based on model and phase.

        Args:
            phase: "ACTIVE" or "QUIET" for burst model, None otherwise

        Returns:
            Effective flip probability in PPM
        """
        if self.rsa_noise_model == RSANoiseModel.BURST_SCHEDULED_FLIP:
            if phase == "ACTIVE":
                return self.rsa_p_burst_flip_ppm
            elif phase == "QUIET":
                return self.rsa_p_quiet_flip_ppm
            else:
                # Fallback: return burst probability
                return self.rsa_p_burst_flip_ppm
        elif self.rsa_noise_model == RSANoiseModel.COMMITMENT_KEYED_FLIP:
            return self.rsa_p_target_flip_ppm
        else:
            return self.rsa_p_flip_ppm

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "rsa_enabled": self.rsa_enabled,
            "rsa_noise_model": self.rsa_noise_model.value,
            "rsa_p_flip_ppm": self.rsa_p_flip_ppm,
            "rsa_scope": self.rsa_scope.value,
            "rsa_rng_stream": self.rsa_rng_stream,
            # v0.2 Model B
            "rsa_target_key": self.rsa_target_key,
            "rsa_p_target_flip_ppm": self.rsa_p_target_flip_ppm,
            # v0.2 Model C
            "rsa_burst_period_epochs": self.rsa_burst_period_epochs,
            "rsa_burst_width_epochs": self.rsa_burst_width_epochs,
            "rsa_burst_phase_offset": self.rsa_burst_phase_offset,
            "rsa_p_burst_flip_ppm": self.rsa_p_burst_flip_ppm,
            "rsa_p_quiet_flip_ppm": self.rsa_p_quiet_flip_ppm,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RSAConfig":
        """Deserialize from dictionary."""
        return cls(
            rsa_enabled=data.get("rsa_enabled", False),
            rsa_noise_model=RSANoiseModel(data.get("rsa_noise_model", "NONE")),
            rsa_p_flip_ppm=data.get("rsa_p_flip_ppm", 0),
            rsa_scope=RSAScope(data.get("rsa_scope", "PER_CI")),
            rsa_rng_stream=data.get("rsa_rng_stream", "rsa"),
            # v0.2 Model B
            rsa_target_key=data.get("rsa_target_key"),
            rsa_p_target_flip_ppm=data.get("rsa_p_target_flip_ppm", 0),
            # v0.2 Model C
            rsa_burst_period_epochs=data.get("rsa_burst_period_epochs", 0),
            rsa_burst_width_epochs=data.get("rsa_burst_width_epochs", 0),
            rsa_burst_phase_offset=data.get("rsa_burst_phase_offset", 0),
            rsa_p_burst_flip_ppm=data.get("rsa_p_burst_flip_ppm", 0),
            rsa_p_quiet_flip_ppm=data.get("rsa_p_quiet_flip_ppm", 0),
        )
