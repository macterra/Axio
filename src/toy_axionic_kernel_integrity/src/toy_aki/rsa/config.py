"""
RSA v0.1 Configuration.

Defines RSAConfig with all parameters for verifier-outcome noise injection.
All probability parameters use PPM (parts-per-million) integers; no floats.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RSANoiseModel(Enum):
    """Noise model for verifier outcome corruption."""

    NONE = "NONE"
    FLIP_BERNOULLI = "FLIP_BERNOULLI"


class RSAScope(Enum):
    """Scope of RSA corruption."""

    # Corrupt each Ci_OK independently (recommended; highest diagnostic value)
    PER_CI = "PER_CI"

    # Corrupt only the aggregate SEM_PASS (minimal surface area)
    SEM_PASS_ONLY = "SEM_PASS_ONLY"


@dataclass
class RSAConfig:
    """
    Configuration for RSA v0.1 stress layer.

    All parameters are fixed for the run. No adaptation.
    RSA is disabled by default; when disabled, behavior is identical to AKI v0.8.

    Attributes:
        rsa_enabled: Whether RSA is enabled. Default False.
        rsa_noise_model: Noise model to use. Default NONE.
        rsa_p_flip_ppm: Flip probability in PPM (0..1_000_000). Default 0.
        rsa_scope: Which booleans to corrupt. Default PER_CI.
        rsa_rng_stream: Label for RNG stream derivation. Default "rsa".
    """

    rsa_enabled: bool = False
    rsa_noise_model: RSANoiseModel = RSANoiseModel.NONE
    rsa_p_flip_ppm: int = 0
    rsa_scope: RSAScope = RSAScope.PER_CI
    rsa_rng_stream: str = "rsa"

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Ensure p_flip_ppm is in valid range
        if not (0 <= self.rsa_p_flip_ppm <= 1_000_000):
            raise ValueError(
                f"rsa_p_flip_ppm must be in [0, 1_000_000], got {self.rsa_p_flip_ppm}"
            )

        # Convert string enums if needed
        if isinstance(self.rsa_noise_model, str):
            self.rsa_noise_model = RSANoiseModel(self.rsa_noise_model)
        if isinstance(self.rsa_scope, str):
            self.rsa_scope = RSAScope(self.rsa_scope)

    def is_active(self) -> bool:
        """Check if RSA will actually corrupt anything."""
        return (
            self.rsa_enabled
            and self.rsa_noise_model != RSANoiseModel.NONE
            and self.rsa_p_flip_ppm > 0
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "rsa_enabled": self.rsa_enabled,
            "rsa_noise_model": self.rsa_noise_model.value,
            "rsa_p_flip_ppm": self.rsa_p_flip_ppm,
            "rsa_scope": self.rsa_scope.value,
            "rsa_rng_stream": self.rsa_rng_stream,
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
        )
