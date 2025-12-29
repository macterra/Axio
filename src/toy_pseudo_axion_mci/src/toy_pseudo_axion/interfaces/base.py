"""Base interface protocol for causal interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

from ..env.gridworld import GridState


@dataclass
class InterfaceSpec:
    """Interface specification included in every proposal."""
    mode: str  # "full", "mci_latent", "mci_minimal"
    factor_dim: int  # Dimension of factor vector (default 8 for MCI)
    projection_id: Optional[str] = None  # For mci_latent: which projection to use

    def to_dict(self) -> dict:
        result = {
            "mode": self.mode,
            "factor_dim": self.factor_dim,
        }
        if self.projection_id is not None:
            result["projection_id"] = self.projection_id
        return result

    @classmethod
    def from_dict(cls, d: dict) -> "InterfaceSpec":
        return cls(
            mode=d["mode"],
            factor_dim=d["factor_dim"],
            projection_id=d.get("projection_id"),
        )


class CausalInterface(ABC):
    """Abstract base class for causal interfaces.

    Defines what the kernel can see and verify about agent decisions.
    """

    @property
    @abstractmethod
    def mode(self) -> str:
        """Return the interface mode name."""
        pass

    @property
    @abstractmethod
    def factor_dim(self) -> int:
        """Return the dimension of the factor vector."""
        pass

    @abstractmethod
    def get_interface_spec(self) -> InterfaceSpec:
        """Get the interface specification for proposals."""
        pass

    @abstractmethod
    def compute_factors(self, env: GridState) -> list[float]:
        """Compute factor vector from environment.

        For mci_minimal, this may be overridden by agent-supplied factors.

        Args:
            env: Current environment state

        Returns:
            Factor vector of length factor_dim, values in [0, 1]
        """
        pass

    @abstractmethod
    def create_commitment(
        self,
        factors: list[float],
        interface_spec: InterfaceSpec,
        nonce: bytes,
    ) -> tuple[str, str]:
        """Create a commitment over factors.

        Args:
            factors: Factor vector
            interface_spec: Interface specification
            nonce: Random nonce bytes

        Returns:
            Tuple of (factor_digest, commitment_hex)
        """
        pass

    @abstractmethod
    def verify_commitment(
        self,
        factors: list[float],
        interface_spec: InterfaceSpec,
        commitment: str,
        nonce: bytes,
    ) -> bool:
        """Verify a factor commitment.

        Args:
            factors: Claimed factor vector
            interface_spec: Interface specification
            commitment: Claimed commitment
            nonce: Revealed nonce

        Returns:
            True if commitment is valid
        """
        pass
