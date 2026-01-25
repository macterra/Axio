"""ASB-Class Null Agent Baseline

The ASB (Agent Sans Beliefs) Null Agent is the non-normative baseline
for v3.0 ablation comparisons.

Properties:
- No justification artifacts
- No normative state
- No compilation gate
- No audits
- Action selection: seeded uniform random over feasible actions

If an ablated system is indistinguishable from ASB Null, it has
collapsed to ASB_CLASS_REDUCIBILITY.

Binding choice: uniform random seeded (not deterministic first-feasible)
Rationale: deterministic first-feasible can accidentally look "principled"
via ordering artifacts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Tuple
import random


class ASBActionSelection(Enum):
    """Action selection mode for ASB Null Agent."""
    UNIFORM_RANDOM_SEEDED = "uniform_random_seeded"  # Binding choice
    DETERMINISTIC_FIRST = "deterministic_first"  # Acceptable alternative


@dataclass
class ASBNullConfig:
    """Configuration for ASB Null Agent."""
    # Action selection mode (binding: UNIFORM_RANDOM_SEEDED)
    selection_mode: ASBActionSelection = ASBActionSelection.UNIFORM_RANDOM_SEEDED

    # Global seed for random selection (combined with episode_id and step_index)
    global_seed: int = 42

    # Whether to respect feasibility mask (yes, always)
    respect_feasibility: bool = True

    # Whether to log action selections
    log_selections: bool = True

    @staticmethod
    def derive_seed(global_seed: int, episode_id: int, step_index: int) -> int:
        """
        Derive deterministic seed from (global_seed, episode_id, step_index).

        BINDING: Same derivation as SelectorTolerance for consistency.
        """
        combined = hash((global_seed, episode_id, step_index))
        return abs(combined) % (2 ** 31)


@dataclass
class ASBStepResult:
    """Result of a single ASB Null Agent step."""
    step_index: int
    seed_offset: int
    feasible_actions: List[str]
    selected_action: str
    selection_mode: ASBActionSelection

    # No justification (by definition)
    justification: None = None

    # No constraints (by definition)
    constraints: None = None

    # No audit (by definition)
    audit_result: None = None


class ASBNullAgent:
    """
    ASB-Class Null Agent: non-normative baseline.

    This agent:
    - Selects actions uniformly at random from feasible set
    - Has no beliefs, preferences, or justifications
    - Has no normative state or persistence
    - Has no compilation or audit gates

    Used as comparison target for ablation runs.
    If ablated system ≈ ASB Null, classify as ASB_CLASS_REDUCIBILITY.
    """

    def __init__(self, config: Optional[ASBNullConfig] = None):
        """Initialize ASB Null Agent."""
        self.config = config or ASBNullConfig()
        self._step_count = 0
        self._action_history: List[ASBStepResult] = []

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset agent state for new episode."""
        self._step_count = 0
        self._action_history = []
        if seed is not None:
            self.config = ASBNullConfig(
                selection_mode=self.config.selection_mode,
                global_seed=seed,
                respect_feasibility=self.config.respect_feasibility,
                log_selections=self.config.log_selections,
            )

    def select_action(
        self,
        feasible_actions: Set[str],
        step: int = 0,
        episode: int = 0,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Select action from feasible set.

        No normative reasoning. No justification. Just selection.

        Args:
            feasible_actions: Set of feasible action IDs
            step: Current step index
            episode: Current episode index
            world_state: Current world state (ignored by ASB Null)

        Returns:
            Selected action ID as string
        """
        # Convert set to sorted list for deterministic ordering
        feasible_list = sorted(list(feasible_actions))

        if not feasible_list:
            raise ValueError("ASB Null Agent requires at least one feasible action")

        # Derive seed using hash(global_seed, episode_id, step_index)
        # BINDING: Same derivation formula as SelectorTolerance
        derived_seed = ASBNullConfig.derive_seed(
            self.config.global_seed, episode, step
        )

        if self.config.selection_mode == ASBActionSelection.UNIFORM_RANDOM_SEEDED:
            # Binding choice: uniform random
            rng = random.Random(derived_seed)
            selected = rng.choice(feasible_list)

        elif self.config.selection_mode == ASBActionSelection.DETERMINISTIC_FIRST:
            # Alternative: deterministic first
            selected = feasible_list[0]

        else:
            raise ValueError(f"Unknown selection mode: {self.config.selection_mode}")

        # Track in history
        self._step_count += 1
        result = ASBStepResult(
            step_index=step,
            seed_offset=derived_seed,
            feasible_actions=feasible_list,
            selected_action=selected,
            selection_mode=self.config.selection_mode,
        )
        self._action_history.append(result)

        return selected

    def select_action_full(
        self,
        feasible_actions: Set[str],
        step: int = 0,
        episode: int = 0,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> ASBStepResult:
        """
        Select action and return full result with metadata.

        Same as select_action but returns ASBStepResult instead of just action ID.
        """
        action = self.select_action(feasible_actions, step, episode, world_state)
        return self._action_history[-1]

    def get_action_distribution(self) -> Dict[str, float]:
        """
        Get empirical action distribution from history.

        Used for comparing ablated system to ASB baseline.
        """
        if not self._action_history:
            return {}

        from collections import Counter
        counts = Counter(r.selected_action for r in self._action_history)
        total = sum(counts.values())
        return {action: count / total for action, count in counts.items()}

    def get_history(self) -> List[ASBStepResult]:
        """Get action history for analysis."""
        return list(self._action_history)


# ============================================================================
# ASB Equivalence Metrics
# ============================================================================

def compute_asb_equivalence(
    ablated_actions: List[str],
    asb_actions: List[str],
    ablated_feasible_sets: Optional[List[Set[str]]] = None,
    asb_feasible_sets: Optional[List[Set[str]]] = None,
    ablated_step_indices: Optional[List[int]] = None,
    asb_step_indices: Optional[List[int]] = None,
) -> float:
    """
    Compute equivalence score between ablated system and ASB Null.

    BINDING (v3.0 Integration Requirement 5):
    Computes on intersection of executed step indices only.
    If one episode terminated early, excludes those steps symmetrically.

    Args:
        ablated_actions: Actions taken by ablated system
        asb_actions: Actions taken by ASB Null agent
        ablated_feasible_sets: Feasible sets for ablated system (optional)
        asb_feasible_sets: Feasible sets for ASB Null (optional)
        ablated_step_indices: Step indices for ablated actions (optional)
        asb_step_indices: Step indices for ASB actions (optional)

    Returns:
        Score in [0, 1] where 1.0 = indistinguishable from ASB Null

    Metrics:
    1. Action distribution similarity (L1 → similarity)
    2. Per-step action agreement rate
    3. Conditional independence from feasibility (both should be uniform)

    If step_indices are provided, computes on intersection only.
    If feasible_sets are not provided, uses simplified comparison.
    """
    # Handle step intersection alignment
    if ablated_step_indices is not None and asb_step_indices is not None:
        # Find intersection of step indices
        ablated_set = set(ablated_step_indices)
        asb_set = set(asb_step_indices)
        common_steps = ablated_set & asb_set

        if not common_steps:
            return 0.0

        # Filter to common steps only
        ablated_idx_map = {s: i for i, s in enumerate(ablated_step_indices)}
        asb_idx_map = {s: i for i, s in enumerate(asb_step_indices)}

        common_sorted = sorted(common_steps)
        ablated_actions = [ablated_actions[ablated_idx_map[s]] for s in common_sorted]
        asb_actions = [asb_actions[asb_idx_map[s]] for s in common_sorted]

        if ablated_feasible_sets is not None:
            ablated_feasible_sets = [ablated_feasible_sets[ablated_idx_map[s]] for s in common_sorted]
        if asb_feasible_sets is not None:
            asb_feasible_sets = [asb_feasible_sets[asb_idx_map[s]] for s in common_sorted]

    elif len(ablated_actions) != len(asb_actions):
        # No step indices provided but lengths differ - truncate to minimum
        # This is the fallback for backwards compatibility
        min_len = min(len(ablated_actions), len(asb_actions))
        ablated_actions = ablated_actions[:min_len]
        asb_actions = asb_actions[:min_len]
        if ablated_feasible_sets is not None:
            ablated_feasible_sets = ablated_feasible_sets[:min_len]
        if asb_feasible_sets is not None:
            asb_feasible_sets = asb_feasible_sets[:min_len]

    if not ablated_actions:
        return 0.0

    # Metric 1: Per-step agreement rate
    agreements = sum(1 for a, b in zip(ablated_actions, asb_actions) if a == b)
    agreement_rate = agreements / len(ablated_actions)

    # Metric 2: Action distribution similarity
    from collections import Counter
    ablated_dist = Counter(ablated_actions)
    asb_dist = Counter(asb_actions)

    all_actions = set(ablated_dist.keys()) | set(asb_dist.keys())
    total = len(ablated_actions)

    # Compute L1 distance between distributions
    l1_distance = sum(
        abs(ablated_dist.get(a, 0) / total - asb_dist.get(a, 0) / total)
        for a in all_actions
    )
    distribution_similarity = 1.0 - (l1_distance / 2.0)  # Normalize to [0, 1]

    # Metric 3: Uniformity over feasible sets (if provided)
    if ablated_feasible_sets is not None:
        uniformity_score = _compute_uniformity_score(ablated_actions, ablated_feasible_sets)
        # Combine all three metrics
        equivalence = (agreement_rate + distribution_similarity + uniformity_score) / 3.0
    else:
        # Without feasible sets, use simple average of agreement and distribution
        equivalence = (agreement_rate + distribution_similarity) / 2.0

    return equivalence


def _compute_uniformity_score(
    actions: List[str],
    feasible_sets: List[Set[str]],
) -> float:
    """
    Compute how uniformly the agent samples from feasible sets.

    A uniform agent would select each feasible action with equal probability.
    """
    if not actions or not feasible_sets:
        return 0.0

    # For each step, compute deviation from uniform
    deviations = []

    # Group by feasible set size
    from collections import defaultdict
    by_size = defaultdict(list)

    for action, feasible in zip(actions, feasible_sets):
        if feasible:
            by_size[len(feasible)].append((action, feasible))

    for size, step_data in by_size.items():
        if size <= 1:
            continue  # No choice, skip

        # Count action frequencies
        from collections import Counter
        action_counts = Counter(a for a, _ in step_data)

        # Expected under uniform: each action appears with prob 1/size
        # But we're measuring: given size-k feasible set, how uniform is selection?
        total_steps = len(step_data)
        expected_per_action = total_steps / size  # If all feasible actions were equally likely

        # Compute chi-squared-like deviation
        observed_counts = list(action_counts.values())
        variance = sum((c - expected_per_action) ** 2 for c in observed_counts)
        normalized_variance = variance / (total_steps ** 2) if total_steps > 0 else 0

        # Convert to similarity (lower variance = more uniform = higher score)
        similarity = 1.0 / (1.0 + normalized_variance * 10)
        deviations.append(similarity)

    return sum(deviations) / len(deviations) if deviations else 0.5


def is_asb_reducible(
    equivalence_score: float,
    threshold: float = 0.85,
) -> bool:
    """
    Determine if ablated system is reducible to ASB Null.

    Args:
        equivalence_score: Score from compute_asb_equivalence
        threshold: Classification threshold (binding: 0.85)

    Returns:
        True if system is ASB-reducible (ablation "succeeded" in collapse)
    """
    return equivalence_score >= threshold
