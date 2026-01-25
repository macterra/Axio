"""Blind Action Selector for v1.0

Inherits v010 blindness pattern: no access to JAF, APCM, or normative state.
Receives only action mask from compiler.
"""

from typing import List, Set, Optional
import random


class BlindActionSelectorV100:
    """
    v1.0 blind selector - enforces separation of concerns.

    Properties:
    - No access to JAF artifacts
    - No access to APCM
    - No access to normative state
    - Receives only: feasible actions + mask (forbidden actions)
    - Selects uniformly from allowed actions
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize blind selector.

        Args:
            seed: Random seed for deterministic selection
        """
        self._rng = random.Random(seed)

    def select(
        self,
        feasible_actions: List[str],
        forbidden_actions: Set[str]
    ) -> Optional[str]:
        """
        Select action from allowed set.

        Args:
            feasible_actions: Actions feasible in environment
            forbidden_actions: Actions forbidden by compiler (blacklist)

        Returns:
            Selected action ID, or None if no valid options
        """
        # Compute allowed actions: feasible AND not forbidden
        allowed = [action for action in feasible_actions
                  if action not in forbidden_actions]

        if not allowed:
            return None  # No valid options

        # Uniform random selection from allowed set
        return self._rng.choice(allowed)

    def reset(self, seed: Optional[int] = None):
        """Reset selector state"""
        if seed is not None:
            self._rng = random.Random(seed)


class ASBNullSelectorV100:
    """
    ASB (Atheoretic Stochastic Baseline) selector for v1.0.

    Selects uniformly from feasible actions, ignoring all constraints.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize ASB selector"""
        self._rng = random.Random(seed)

    def select(
        self,
        feasible_actions: List[str],
        forbidden_actions: Set[str] = None  # Ignored
    ) -> Optional[str]:
        """
        Select action uniformly from feasible set.

        Ignores all normative constraints (forbidden_actions).
        """
        if not feasible_actions:
            return None

        return self._rng.choice(feasible_actions)

    def reset(self, seed: Optional[int] = None):
        """Reset selector state"""
        if seed is not None:
            self._rng = random.Random(seed)
