"""MCI Minimal interface implementation.

Provides factor-based commitments where factors can be agent-supplied.
Used for mci_minimal mode testing (no thresholds, entropy curves).
"""

from __future__ import annotations

from typing import Any

from ..env.gridworld import GridState
from .mci_latent import MCILatentInterface


class MCIMinimalInterface(MCILatentInterface):
    """MCI Minimal interface with agent-supplied factors.

    Extends MCILatentInterface but allows agents to supply their own
    factor vectors (which may differ from the true projection).

    In mci_minimal mode:
    - Same probes run, no pass/fail thresholds
    - Reports entropy-binned curves and cliff detection
    - Factors can come from agent or be computed by interface
    """

    @property
    def mode(self) -> str:
        return "mci_minimal"

    def create_factor_commitment_with_factors(
        self,
        agent_factors: list[float],
        snapshot_id: str,
        nonce_ref: str,
    ) -> dict[str, Any]:
        """Create factor snapshot with agent-supplied factors.

        This allows agents to provide their own factor values,
        which may not match the true projection.

        Args:
            agent_factors: Agent-supplied factor vector
            snapshot_id: Unique ID for this snapshot
            nonce_ref: Reference nonce

        Returns:
            Factor snapshot dict
        """
        # Validate dimension
        if len(agent_factors) != self.FACTOR_DIM:
            raise ValueError(
                f"Factor dimension mismatch: {len(agent_factors)} != {self.FACTOR_DIM}"
            )

        # Validate range
        for i, f in enumerate(agent_factors):
            if not (0.0 <= f <= 1.0):
                raise ValueError(f"Factor {i} out of range: {f}")

        digest = self.create_factor_digest(agent_factors, nonce_ref)

        return {
            "snapshot_id": snapshot_id,
            "factor_digest": digest,
            "dim": self.FACTOR_DIM,
            "commitment": {
                "factors": agent_factors,
                "projection_id": self.PROJECTION_ID,
            },
            "nonce_ref": nonce_ref,
        }

    def verify_factor_commitment_against_claimed(
        self,
        claimed_factors: list[float],
        commitment: dict[str, Any],
        nonce_ref: str,
    ) -> bool:
        """Verify factor snapshot commitment matches claimed factors.

        Unlike the parent verify_factor_commitment, this compares against
        claimed factors rather than computing from environment.

        Args:
            claimed_factors: Factors to verify against
            commitment: Factor snapshot dict
            nonce_ref: Reference nonce

        Returns:
            True if factors match, False otherwise
        """
        # Get commitment factors
        commitment_factors = commitment.get("commitment", {}).get("factors", [])

        # Check dimension
        if len(commitment_factors) != len(claimed_factors):
            return False

        # Check each factor (allow small floating point tolerance)
        tolerance = 1e-9
        for current, claimed in zip(claimed_factors, commitment_factors):
            if abs(current - claimed) > tolerance:
                return False

        # Verify digest
        expected_digest = self.create_factor_digest(commitment_factors, nonce_ref)
        return commitment.get("factor_digest") == expected_digest

    def create_fork_commitment_with_factors(
        self,
        agent_factors: list[float],
        tick: int,
        nonce_ref: str,
    ) -> dict[str, Any]:
        """Create fork commitment with agent-supplied factors.

        Args:
            agent_factors: Agent-supplied factor vector
            tick: Current tick number
            nonce_ref: Reference nonce

        Returns:
            Fork commitment with factors
        """
        snapshot_id = f"fork_{tick}"
        factor_snapshot = self.create_factor_commitment_with_factors(
            agent_factors, snapshot_id, nonce_ref
        )

        return {
            "tick": tick,
            "factor_snapshot": factor_snapshot,
            "nonce_ref": nonce_ref,
        }

    def compare_factors_to_ground_truth(
        self, env: GridState, claimed_factors: list[float]
    ) -> dict[str, Any]:
        """Compare claimed factors to ground truth projection.

        Useful for analyzing pseudo agent factor fabrication.

        Args:
            env: Environment state
            claimed_factors: Agent's claimed factors

        Returns:
            Comparison dict with:
            - ground_truth: True projected factors
            - claimed: Agent's claimed factors
            - deltas: Difference for each factor
            - max_delta: Maximum absolute difference
            - factors_match: True if all factors match within tolerance
        """
        ground_truth = self.compute_factors(env)

        tolerance = 1e-9
        deltas = [abs(g - c) for g, c in zip(ground_truth, claimed_factors)]
        max_delta = max(deltas) if deltas else 0.0
        factors_match = all(d <= tolerance for d in deltas)

        return {
            "ground_truth": ground_truth,
            "claimed": claimed_factors,
            "deltas": deltas,
            "max_delta": max_delta,
            "factors_match": factors_match,
        }
