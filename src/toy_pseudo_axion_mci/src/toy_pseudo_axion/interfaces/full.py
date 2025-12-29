"""Full interface - legacy v1 behavior using fork snapshots over normalize_state."""

from typing import Optional

from .base import CausalInterface, InterfaceSpec
from ..env.gridworld import GridState
from ..env.normalize_state import normalize_state, get_default_focus_vars
from ..common.hashing import hash_json, hmac_sha256_hex, sha256_hex


class FullInterface(CausalInterface):
    """Full causal interface using environment-based fork snapshots.

    This is the legacy v1 behavior where commitments are made over
    normalize_state(env, focus_vars).
    """

    def __init__(self, factor_dim: int = 0):
        """Initialize full interface.

        Args:
            factor_dim: Not used in full mode, set to 0
        """
        self._factor_dim = factor_dim

    @property
    def mode(self) -> str:
        return "full"

    @property
    def factor_dim(self) -> int:
        return self._factor_dim

    def get_interface_spec(self) -> InterfaceSpec:
        return InterfaceSpec(
            mode="full",
            factor_dim=self._factor_dim,
            projection_id=None,
        )

    def compute_factors(self, env: GridState) -> list[float]:
        """Full mode doesn't use factors - return empty list."""
        return []

    def create_commitment(
        self,
        factors: list[float],
        interface_spec: InterfaceSpec,
        nonce: bytes,
    ) -> tuple[str, str]:
        """Full mode uses fork snapshots, not factor commitments.

        This method exists for interface compatibility but shouldn't
        be called in full mode.
        """
        raise NotImplementedError("Full mode uses fork snapshots, not factor commitments")

    def verify_commitment(
        self,
        factors: list[float],
        interface_spec: InterfaceSpec,
        commitment: str,
        nonce: bytes,
    ) -> bool:
        """Full mode uses fork snapshots, not factor commitments."""
        raise NotImplementedError("Full mode uses fork snapshots, not factor commitments")

    def create_fork_commitment(
        self,
        env: GridState,
        focus_vars: list[str],
        nonce: bytes,
    ) -> tuple[str, str]:
        """Create a fork snapshot commitment (full mode only).

        Args:
            env: Environment state
            focus_vars: Variables to include in normalized state
            nonce: Random nonce bytes

        Returns:
            Tuple of (state_digest, commitment_hex)
        """
        # Compute state digest
        normalized = normalize_state(env, focus_vars)
        state_digest = hash_json(normalized)

        # Compute aux digest over focus_vars
        aux_digest = sha256_hex(focus_vars)

        # Build commitment: HMAC-SHA256(nonce, state_digest || 0x00 || aux_digest)
        digest_raw = bytes.fromhex(state_digest)
        aux_raw = bytes.fromhex(aux_digest)
        msg = digest_raw + b"\x00" + aux_raw
        commitment = hmac_sha256_hex(nonce, msg)

        return state_digest, commitment

    def verify_fork_commitment(
        self,
        env: GridState,
        focus_vars: list[str],
        state_digest: str,
        commitment: str,
        nonce: bytes,
    ) -> bool:
        """Verify a fork snapshot commitment.

        Args:
            env: Environment state
            focus_vars: Variables used in commitment
            state_digest: Claimed state digest
            commitment: Claimed commitment
            nonce: Revealed nonce

        Returns:
            True if commitment is valid
        """
        computed_digest, computed_commitment = self.create_fork_commitment(
            env, focus_vars, nonce
        )
        return (
            computed_digest == state_digest and
            computed_commitment == commitment
        )
