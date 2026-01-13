"""Blind Action Selector for RSA-PoC v0.1

Action selector that is BLIND to semantics.

CRITICAL: This module MUST NOT import or access:
- JAF artifacts
- Normative state text/descriptions
- Belief/preference content
- Justification comments
- Any semantic representations
"""

import random
from typing import List, Dict, Set, Optional


class BlindActionSelector:
    """
    Action selector that only sees masks and environment state.

    This is a simple ASB-class policy machine that respects compiled masks.

    Permitted inputs:
    - Environment observation (non-semantic)
    - Feasible action list
    - Compiled action mask (ALLOW/FORBID)

    Forbidden inputs:
    - JAF artifacts
    - Normative state (beliefs/preferences)
    - Justification text
    - Semantic content
    """

    def __init__(self, seed: int = 42, strategy: str = "random"):
        """
        Initialize selector.

        Args:
            seed: Random seed
            strategy: Selection strategy ("random", "first", "reward_greedy")
        """
        self._rng = random.Random(seed)
        self._strategy = strategy
        self._step_count = 0

    def select_action(
        self,
        feasible_actions: List[str],
        action_mask: Dict[str, str],
        env_obs: Optional[Dict] = None
    ) -> str:
        """
        Select action from masked feasible set.

        Args:
            feasible_actions: List of feasible action IDs
            action_mask: Dict mapping action_id -> "ALLOW" or "FORBID"
            env_obs: Environment observation (non-semantic, optional)

        Returns:
            Selected action ID

        Raises:
            ValueError: If no actions remain after masking (gridlock)
        """
        # Apply mask to feasible actions
        masked_feasible = [
            action for action in feasible_actions
            if action_mask.get(action, "ALLOW") == "ALLOW"
        ]

        if not masked_feasible:
            raise ValueError("Normative gridlock: no actions remain after masking")

        # Select based on strategy
        if self._strategy == "random":
            action = self._rng.choice(masked_feasible)
        elif self._strategy == "first":
            action = masked_feasible[0]
        elif self._strategy == "reward_greedy":
            # Simple heuristic: prefer actions with higher expected reward
            # This is ASB-class behavior (reward-driven, not norm-driven)
            action = self._select_greedy(masked_feasible)
        else:
            raise ValueError(f"Unknown strategy: {self._strategy}")

        self._step_count += 1
        return action

    def _select_greedy(self, actions: List[str]) -> str:
        """
        Greedy selection based on simple action name heuristics.

        This is deliberately simple and non-semantic.
        Just demonstrates that selector can have internal policy logic.
        """
        # Preference order (ASB-class heuristic)
        priority = [
            "DEFECT", "EXPLOIT", "HOARD", "BREAK_LOCK", "LIE",  # High reward temptations
            "COOPERATE", "TELL_TRUTH", "SHARE",  # Moderate reward
            "HELP", "WAIT"  # Low reward
        ]

        for preferred in priority:
            if preferred in actions:
                return preferred

        # Fallback
        return actions[0]


class ASBNullSelector:
    """
    ASB-class null selector (baseline).

    No normative gating - selects directly from feasible actions.
    Used for ablation comparison.
    """

    def __init__(self, seed: int = 42, strategy: str = "random"):
        self._rng = random.Random(seed)
        self._strategy = strategy

    def select_action(
        self,
        feasible_actions: List[str],
        env_obs: Optional[Dict] = None
    ) -> str:
        """
        Select action without normative constraints.

        Args:
            feasible_actions: List of feasible action IDs
            env_obs: Environment observation (optional)

        Returns:
            Selected action ID
        """
        if not feasible_actions:
            raise ValueError("No feasible actions")

        if self._strategy == "random":
            return self._rng.choice(feasible_actions)
        elif self._strategy == "first":
            return feasible_actions[0]
        elif self._strategy == "reward_greedy":
            return self._select_greedy(feasible_actions)
        else:
            raise ValueError(f"Unknown strategy: {self._strategy}")

    def _select_greedy(self, actions: List[str]) -> str:
        """Same greedy logic as BlindActionSelector"""
        priority = [
            "DEFECT", "EXPLOIT", "HOARD", "BREAK_LOCK", "LIE",
            "COOPERATE", "TELL_TRUTH", "SHARE",
            "HELP", "WAIT"
        ]

        for preferred in priority:
            if preferred in actions:
                return preferred

        return actions[0]
