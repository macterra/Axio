"""MCI Latent interface implementation.

Provides factor-based commitments using v1_basic_k8 projection.
Factors are computed from the environment by the kernel.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..env.gridworld import GridState
from ..env.metrics_oracle import (
    compute_reachability_bfs,
    count_walls_in_radius,
    find_nearest_agent,
    find_nearest_hazard,
    find_nearest_object,
)
from .base import CausalInterface, InterfaceSpec


class MCILatentInterface(CausalInterface):
    """MCI Latent interface with factor projection.

    Implements v1_basic_k8 projection:
    - K = 8 factors, each normalized to [0, 1]
    - Factors are computed from environment state

    Factor definitions (0-indexed):
        F:0 = self.energy / 100 (clamped to [0, 1])
        F:1 = inventory_count / 10 (clamped to [0, 1])
        F:2 = min_dist_hazard / 10 (clamped to [0, 1], 1.0 if no hazards)
        F:3 = hazard_proximity_flag (1.0 if any hazard within dist 1, else 0.0)
        F:4 = min_dist_object / 10 (clamped to [0, 1], 1.0 if no objects)
        F:5 = min_dist_agent / 10 (clamped to [0, 1], 1.0 if no agents)
        F:6 = reachable_cells_bfs3 / 64 (BFS depth 3, walls block, hazards don't)
        F:7 = walls_radius3 / 25 (clamped to [0, 1])
    """

    PROJECTION_ID = "v1_basic_k8"
    FACTOR_DIM = 8

    @property
    def mode(self) -> str:
        return "mci_latent"

    @property
    def factor_dim(self) -> int:
        return self.FACTOR_DIM

    @property
    def projection_id(self) -> str:
        return self.PROJECTION_ID

    @classmethod
    def get_spec(cls) -> InterfaceSpec:
        return InterfaceSpec(
            mode="mci_latent",
            factor_dim=cls.FACTOR_DIM,
            projection_id=cls.PROJECTION_ID,
        )

    def get_interface_spec(self) -> InterfaceSpec:
        """Get the interface specification for proposals."""
        return InterfaceSpec(
            mode=self.mode,
            factor_dim=self.factor_dim,
            projection_id=self.projection_id,
        )

    def compute_factors(self, env: GridState) -> list[float]:
        """Project environment state to factor vector.

        Uses v1_basic_k8 projection.

        Args:
            env: Environment state

        Returns:
            List of 8 factors, each in [0, 1]
        """
        # F:0 - energy normalized
        f0 = min(max(env.self_entity.energy / 100.0, 0.0), 1.0)

        # F:1 - inventory count normalized
        inv_count = len(env.self_entity.inventory)
        f1 = min(max(inv_count / 10.0, 0.0), 1.0)

        # F:2 - min distance to hazard normalized
        nearest_hazard = find_nearest_hazard(env)
        if nearest_hazard is None:
            f2 = 1.0  # No hazards = max normalized distance
        else:
            f2 = min(max(nearest_hazard[1] / 10.0, 0.0), 1.0)

        # F:3 - hazard proximity flag
        if nearest_hazard is not None and nearest_hazard[1] <= 1:
            f3 = 1.0
        else:
            f3 = 0.0

        # F:4 - min distance to object normalized
        nearest_object = find_nearest_object(env)
        if nearest_object is None:
            f4 = 1.0  # No objects = max normalized distance
        else:
            f4 = min(max(nearest_object[1] / 10.0, 0.0), 1.0)

        # F:5 - min distance to agent normalized
        nearest_agent = find_nearest_agent(env)
        if nearest_agent is None:
            f5 = 1.0  # No agents = max normalized distance
        else:
            f5 = min(max(nearest_agent[1] / 10.0, 0.0), 1.0)

        # F:6 - reachable cells via BFS (depth 3, walls block, hazards don't)
        reachable = compute_reachability_bfs(env, max_depth=3)
        f6 = min(max(reachable / 64.0, 0.0), 1.0)

        # F:7 - wall count in radius 3 normalized
        wall_count = count_walls_in_radius(env, radius=3)
        f7 = min(max(wall_count / 25.0, 0.0), 1.0)

        return [f0, f1, f2, f3, f4, f5, f6, f7]

    def create_factor_digest(
        self, factors: list[float], nonce_ref: str
    ) -> str:
        """Create deterministic digest of factor vector.

        Args:
            factors: Factor vector
            nonce_ref: Reference nonce for commitment

        Returns:
            SHA-256 hex digest of factors + nonce
        """
        # Serialize factors to canonical JSON
        factors_json = json.dumps(
            factors, sort_keys=True, separators=(",", ":")
        )
        data = f"{factors_json}:{nonce_ref}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def create_factor_commitment(
        self, env: GridState, snapshot_id: str, nonce_ref: str
    ) -> dict[str, Any]:
        """Create factor snapshot commitment.

        Args:
            env: Environment state
            snapshot_id: Unique ID for this snapshot
            nonce_ref: Reference nonce

        Returns:
            Factor snapshot dict per factor_snapshot.json schema
        """
        factors = self.compute_factors(env)
        digest = self.create_factor_digest(factors, nonce_ref)

        # Commitment is HMAC over factor_digest with nonce - must be hex string
        commitment_data = json.dumps({
            "factor_digest": digest,
            "nonce_ref": nonce_ref
        }, sort_keys=True)
        commitment = hashlib.sha256(commitment_data.encode("utf-8")).hexdigest()

        return {
            "snapshot_id": snapshot_id,
            "factor_digest": digest,
            "dim": self.FACTOR_DIM,
            "commitment": commitment,
            "nonce_ref": nonce_ref,
        }

    def verify_factor_commitment(
        self,
        env: GridState,
        factor_snapshot: dict[str, Any],
        nonce_ref: str,
    ) -> bool:
        """Verify factor snapshot commitment matches environment.

        Args:
            env: Environment state to verify against
            factor_snapshot: Factor snapshot dict with factor_digest and commitment
            nonce_ref: Reference nonce

        Returns:
            True if commitment is valid, False otherwise
        """
        # Compute current factors
        current_factors = self.compute_factors(env)

        # Verify factor_digest matches current factors
        expected_digest = self.create_factor_digest(current_factors, nonce_ref)
        if factor_snapshot.get("factor_digest") != expected_digest:
            return False

        # Verify commitment is valid HMAC over factor_digest
        commitment_data = json.dumps({
            "factor_digest": factor_snapshot.get("factor_digest"),
            "nonce_ref": nonce_ref
        }, sort_keys=True)
        expected_commitment = hashlib.sha256(commitment_data.encode("utf-8")).hexdigest()

        return factor_snapshot.get("commitment") == expected_commitment

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
        nonce_hex = nonce.hex()
        digest = self.create_factor_digest(factors, nonce_hex)

        # Commitment is the digest for MCI
        return (digest, digest)

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
        nonce_hex = nonce.hex()
        expected_digest = self.create_factor_digest(factors, nonce_hex)
        return commitment == expected_digest

    def create_fork_commitment(
        self, env: GridState, tick: int, nonce_ref: str
    ) -> dict[str, Any]:
        """Create fork commitment with factors.

        For MCI latent, fork commitment includes factor snapshot.

        Args:
            env: Environment state
            tick: Current tick number
            nonce_ref: Reference nonce

        Returns:
            Fork commitment with factors
        """
        snapshot_id = f"fork_{tick}"
        factor_snapshot = self.create_factor_commitment(
            env, snapshot_id, nonce_ref
        )

        return {
            "tick": tick,
            "factor_snapshot": factor_snapshot,
            "nonce_ref": nonce_ref,
        }

    def verify_fork_commitment(
        self, env: GridState, commitment: dict[str, Any]
    ) -> bool:
        """Verify fork commitment factors match environment.

        Args:
            env: Environment state
            commitment: Fork commitment dict

        Returns:
            True if factors match, False otherwise
        """
        factor_snapshot = commitment.get("factor_snapshot", {})
        nonce_ref = commitment.get("nonce_ref", "")

        return self.verify_factor_commitment(env, factor_snapshot, nonce_ref)


def compute_replay_model_action(
    factors: list[float], W: list[list[float]], b: list[float], actions: list[str]
) -> str:
    """Compute action from replay model.

    logits = W @ f + b
    action = argmax(logits)

    Args:
        factors: Factor vector (K dimensions)
        W: Weight matrix (A x K) where A = number of actions
        b: Bias vector (A dimensions)
        actions: List of action names in order

    Returns:
        Selected action name
    """
    if len(W) != len(b) or len(W) != len(actions):
        raise ValueError("Dimension mismatch in replay model")

    if len(W) > 0 and len(W[0]) != len(factors):
        raise ValueError(f"Factor dimension mismatch: {len(W[0])} != {len(factors)}")

    # Compute logits
    logits = []
    for i in range(len(actions)):
        # W[i] @ factors + b[i]
        logit = b[i]
        for j in range(len(factors)):
            logit += W[i][j] * factors[j]
        logits.append(logit)

    # Argmax
    max_idx = 0
    max_val = logits[0]
    for i in range(1, len(logits)):
        if logits[i] > max_val:
            max_val = logits[i]
            max_idx = i

    return actions[max_idx]
