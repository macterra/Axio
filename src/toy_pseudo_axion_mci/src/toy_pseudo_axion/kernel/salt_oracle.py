"""Salt Oracle for MCI v0.4 - Delayed Reveal Challenge.

This module provides the kernel service for generating and managing
per-timestep salts that anchor factor derivation to an unpredictable
challenge.

The salt oracle:
- Generates random 128-bit salts at episode start
- Never exposes salts to agents during the episode
- Reveals all salts at episode end for verification
"""

import os
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SaltOracle:
    """Kernel service for salt generation and reveal.

    Salts are generated at episode start and stored internally.
    Agents never see salts during the episode. At episode end,
    salts are revealed for I7 verification.
    """

    _salts: list[bytes] = field(default_factory=list)
    _seed: Optional[int] = field(default=None)
    _episode_active: bool = field(default=False)

    def begin_episode(self, steps: int, seed: Optional[int] = None) -> None:
        """Initialize salts for a new episode.

        Args:
            steps: Number of timesteps in the episode
            seed: Optional seed for reproducibility (uses os.urandom if None)
        """
        self._salts = []
        self._seed = seed
        self._episode_active = True

        if seed is not None:
            # Deterministic salt generation for reproducibility
            import random
            rng = random.Random(seed)
            for _ in range(steps):
                # Generate 16 bytes (128 bits) deterministically
                salt = bytes(rng.getrandbits(8) for _ in range(16))
                self._salts.append(salt)
        else:
            # True random salts
            for _ in range(steps):
                self._salts.append(os.urandom(16))

    def salt_at(self, t: int) -> bytes:
        """Get salt for timestep t (kernel-only, never passed to agent).

        Args:
            t: Timestep index (0-based)

        Returns:
            16-byte salt for timestep t

        Raises:
            ValueError: If episode not active or t out of range
        """
        if not self._episode_active:
            raise ValueError("No active episode")
        if t < 0 or t >= len(self._salts):
            raise ValueError(f"Timestep {t} out of range [0, {len(self._salts)})")
        return self._salts[t]

    def reveal_all(self) -> list[bytes]:
        """Reveal all salts at episode end.

        Returns:
            List of all salts in timestep order
        """
        self._episode_active = False
        return list(self._salts)

    def get_steps(self) -> int:
        """Get number of steps in current episode."""
        return len(self._salts)


def compute_salted_factors(
    env_canonical: bytes,
    salt: bytes,
    num_factors: int = 8
) -> list[float]:
    """Fixed φ function: derive factors from (env, salt).

    This is the implementation-defined φ that both honest and pseudo
    agents must use. It is deterministic and fixed by the protocol.

    Args:
        env_canonical: Canonical byte representation of environment state
        salt: 16-byte salt for this timestep
        num_factors: Number of factors to derive (default 8)

    Returns:
        List of factors in [0, 1]
    """
    # Combine env and salt
    combined = env_canonical + salt

    # Hash to get deterministic bytes
    h = hashlib.sha256(combined).digest()

    # Convert to factors in [0, 1]
    factors = []
    for i in range(num_factors):
        # Use 2 bytes per factor for better resolution
        byte_idx = (i * 2) % len(h)
        value = (h[byte_idx] * 256 + h[(byte_idx + 1) % len(h)]) / 65535.0
        factors.append(value)

    return factors


def compute_factor_digest(factors: list[float], salt: bytes) -> str:
    """Compute digest of factors bound to salt.

    Args:
        factors: Factor vector
        salt: Salt for this timestep

    Returns:
        Hex digest string
    """
    # Canonical JSON representation
    data = {
        "factors": [round(f, 8) for f in factors],
        "salt": salt.hex()
    }
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(canonical).hexdigest()


def canonicalize_env(env) -> bytes:
    """Convert environment state to canonical bytes.

    Args:
        env: GridState environment

    Returns:
        Canonical byte representation
    """
    # Extract relevant state for factor derivation
    state = {
        "tick": env.tick,
        "self_pos": [env.self_entity.x, env.self_entity.y],
        "self_energy": env.self_entity.energy,
    }

    return json.dumps(state, sort_keys=True, separators=(',', ':')).encode()


def verify_salted_factors(
    committed_factors: list[float],
    env_canonical: bytes,
    salt: bytes,
    tolerance: float = 1e-6
) -> tuple[bool, str]:
    """Verify that committed factors match recomputed factors.

    Args:
        committed_factors: Factors the agent committed to
        env_canonical: Canonical env bytes
        salt: Revealed salt
        tolerance: Floating point comparison tolerance

    Returns:
        Tuple of (passed, message)
    """
    expected = compute_salted_factors(env_canonical, salt)

    if len(committed_factors) != len(expected):
        return False, f"Factor count mismatch: {len(committed_factors)} vs {len(expected)}"

    for i, (c, e) in enumerate(zip(committed_factors, expected)):
        if abs(c - e) > tolerance:
            return False, f"Factor {i} mismatch: committed {c:.8f} vs expected {e:.8f}"

    return True, ""
