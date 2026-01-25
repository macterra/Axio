"""Deterministic Generator for v1.0

Generates JAF-1.0 artifacts with APCM-grounded collision detection.

Key differences from v0.1:
- Receives APCM from environment
- Detects genuine collisions deterministically
- Produces authorized_violations and conflict_attribution
- Implements simple resolution strategy
"""

from typing import Set, Dict, Optional, Tuple, List
import uuid
import random
from datetime import datetime

# Import JAF-1.0 schema
try:
    from ..jaf.schema import (
        JAF100, Identity, References, ActionClaim, Relevance,
        CompilerHints, ConflictResolution, canonicalize_pair
    )
    from ..state.normative import NormativeStateV100
except ImportError:
    from src.rsa_poc.v100.jaf.schema import (
        JAF100, Identity, References, ActionClaim, Relevance,
        CompilerHints, ConflictResolution, canonicalize_pair
    )
    from src.rsa_poc.v100.state.normative import NormativeStateV100


class DeterministicGeneratorV100:
    """
    v1.0 generator with APCM truth grounding.

    Deterministic, rule-based JAF-1.0 production.
    """

    def __init__(self, normative_state: NormativeStateV100):
        """
        Initialize generator with normative state.

        Args:
            normative_state: v1.0 normative state with precedent tracking
        """
        self.normative_state = normative_state
        self._step = 0

    def generate(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str = "MVRA_v100"
    ) -> JAF100:
        """
        Generate JAF-1.0 artifact for current step.

        Args:
            feasible_actions: List of currently feasible action IDs
            apcm: Action-Preference Consequence Map from environment
            agent_id: Agent identifier for artifact

        Returns:
            JAF100 artifact ready for compilation
        """
        self._step += 1

        # Detect collisions from APCM
        collisions = self._detect_collisions(apcm, feasible_actions)

        # Select action to justify (simple: first feasible)
        # In production, this would be more sophisticated
        action_to_justify = feasible_actions[0] if feasible_actions else "WAIT"

        # Determine if we need to authorize violations
        action_violations = apcm.get(action_to_justify, {}).get("violates", set())

        # Simple resolution strategy:
        # - If there are collisions, authorize the smaller set of violations
        # - Otherwise, maintain empty AV
        if collisions:
            authorized_violations, conflict_attribution = self._resolve_collisions(
                collisions, action_violations
            )
        else:
            authorized_violations = set()
            conflict_attribution = set()

        # Required preservations: all non-authorized preferences
        all_preferences = self.normative_state.get_preferences()
        required_preservations = all_preferences - authorized_violations

        # Get precedent for conflict resolution
        precedent = self.normative_state.get_precedent()
        precedent_digest = precedent["digest"] if precedent else ""

        # Determine conflict resolution mode
        if precedent and collisions:
            # Check if we're revising
            prev_av = precedent["authorized_violations"]
            if authorized_violations != prev_av:
                resolution_mode = "REVISE"
            else:
                resolution_mode = "MAINTAIN"
        else:
            resolution_mode = "MAINTAIN"  # Default when no precedent or no collision

        # Build JAF
        jaf = JAF100(
            artifact_version="JAF-1.0",
            step=self._step,
            identity=Identity(
                agent_id=agent_id,
                continuity_counter=self._step
            ),
            references=References(
                belief_ids=list(self._select_relevant_beliefs(action_to_justify)),
                pref_ids=list(self._select_relevant_preferences(action_to_justify))
            ),
            action_claim=ActionClaim(
                candidate_action_id=action_to_justify,
                relation="SATISFIES",  # Default for v1.0
                target_pref_id=None,
                expected_constraint_effect="NO_CONSTRAINT"
            ),
            relevance=Relevance(
                required_belief_ids=list(self._select_relevant_beliefs(action_to_justify))
            ),
            compiler_hints=CompilerHints(
                forbid_action_ids=[],
                forbid_mode="NONE",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            nonce=str(uuid.uuid4()),
            authorized_violations=authorized_violations,
            required_preservations=required_preservations,
            conflict_attribution=conflict_attribution,
            precedent_reference=precedent_digest,
            conflict_resolution=ConflictResolution(
                mode=resolution_mode,
                previous_artifact_digest=precedent_digest
            ) if precedent and collisions else None
        )

        return jaf

    def _detect_collisions(
        self,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: List[str]
    ) -> Set[Tuple[str, str]]:
        """
        Detect genuine preference collisions from APCM.

        A collision exists between (P1, P2) iff:
        - For all feasible actions, at least one of P1 or P2 is violated

        Returns set of canonicalized collision pairs.
        """
        all_preferences = self.normative_state.get_preferences()
        collisions = set()

        # Check all pairs of preferences
        pref_list = sorted(all_preferences)  # Deterministic ordering
        for i in range(len(pref_list)):
            for j in range(i + 1, len(pref_list)):
                p1, p2 = pref_list[i], pref_list[j]

                if self._is_collision_pair(p1, p2, apcm, feasible_actions):
                    collisions.add(canonicalize_pair(p1, p2))

        return collisions

    def _is_collision_pair(
        self,
        p1: str,
        p2: str,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: List[str]
    ) -> bool:
        """
        Check if (p1, p2) form a genuine collision.

        Returns True iff for all feasible actions, at least one is violated.
        """
        for action in feasible_actions:
            if action not in apcm:
                continue

            violates = apcm[action]["violates"]

            # If neither p1 nor p2 is violated, NOT a collision
            if p1 not in violates and p2 not in violates:
                return False

        return True  # All feasible actions violate at least one

    def _resolve_collisions(
        self,
        collisions: Set[Tuple[str, str]],
        action_violations: Set[str]
    ) -> Tuple[Set[str], Set[Tuple[str, str]]]:
        """
        Simple collision resolution strategy.

        Strategy:
        - Authorize violations that appear in collisions AND are violated by chosen action
        - Attribute all detected collisions

        Returns: (authorized_violations, conflict_attribution)
        """
        # Get all preferences involved in collisions
        collision_prefs = set()
        for p1, p2 in collisions:
            collision_prefs.add(p1)
            collision_prefs.add(p2)

        # Authorize only those collision prefs that are actually violated by chosen action
        authorized_violations = collision_prefs & action_violations

        # Attribute all detected collisions
        conflict_attribution = collisions.copy()

        return authorized_violations, conflict_attribution

    def _select_relevant_beliefs(self, action_id: str) -> Set[str]:
        """
        Select beliefs relevant to action justification.

        Simple heuristic: map actions to their corresponding beliefs.
        """
        belief_map = {
            "COOPERATE": {"B_COOPERATION_MATTERS"},
            "DEFECT": {"B_COOPERATION_MATTERS"},  # Negation
            "BREAK_LOCK": {"B_LOCKS_PROTECT"},  # Negation
            "TELL_TRUTH": {"B_TRUTH_BUILDS_TRUST"},
            "LIE": {"B_TRUTH_BUILDS_TRUST"},  # Negation
            "SHARE": {"B_SHARING_HELPS"},
            "HOARD": {"B_SHARING_HELPS"},  # Negation
            "HELP": {"B_HELP_CREATES_GOOD"},
            "EXPLOIT": {"B_EXPLOITATION_HARMS"},
            "WAIT": {"B_COOPERATION_MATTERS"},  # Default
        }

        return belief_map.get(action_id, set())

    def _select_relevant_preferences(self, action_id: str) -> Set[str]:
        """
        Select preferences relevant to action justification.

        Simple heuristic: all preferences (comprehensive grounding).
        """
        return self.normative_state.get_preferences()

    def _generate_justification(
        self,
        action_id: str,
        authorized_violations: Set[str],
        collisions: Set[Tuple[str, str]]
    ) -> str:
        """Generate justification text for action"""
        if not collisions:
            return f"Action {action_id} respects all normative commitments."

        if authorized_violations:
            av_list = ", ".join(sorted(authorized_violations))
            return (
                f"Action {action_id} requires authorized violation of {av_list} "
                f"due to genuine normative collision. This violation is necessary "
                f"as all feasible alternatives violate at least one colliding preference."
            )
        else:
            return (
                f"Action {action_id} navigates normative collision without violation. "
                f"All preferences are preserved despite environmental constraints."
            )

    def _generate_explanation(
        self,
        action_id: str,
        authorized_violations: Set[str],
        collisions: Set[Tuple[str, str]]
    ) -> str:
        """Generate relevance explanation"""
        if not collisions:
            return "No normative conflicts detected. Clean action space."

        collision_count = len(collisions)
        return (
            f"Detected {collision_count} genuine preference collision(s). "
            f"Resolution requires selective authorization to maintain coherence."
        )

    def reset(self):
        """Reset generator state (e.g., between episodes)"""
        self._step = 0


class ScrambledConflictGenerator:
    """
    Ablation: Generate JAF-1.0 with scrambled conflict attribution.

    Tests whether truthful collision detection is causally load-bearing.
    """

    def __init__(self, normative_state: NormativeStateV100, seed: int = 42):
        """Initialize scrambled generator"""
        self.normative_state = normative_state
        self._step = 0
        self._seed = seed
        import random
        self._rng = random.Random(seed)

    def generate(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str = "MVRA_v100_Scrambled"
    ) -> JAF100:
        """
        Generate JAF-1.0 with FALSE conflict attribution.

        This should cause compilation failures, halting the agent.
        """
        self._step += 1

        # Generate valid JAF first (using correct generator)
        base_generator = DeterministicGeneratorV100(self.normative_state)
        jaf = base_generator.generate(feasible_actions, apcm, agent_id)

        # Scramble conflict_attribution with FALSE collisions
        all_prefs = list(self.normative_state.get_preferences())
        if len(all_prefs) >= 2:
            # Pick random pair that is NOT a genuine collision
            p1 = self._rng.choice(all_prefs)
            p2 = self._rng.choice([p for p in all_prefs if p != p1])

            # Replace with false collision
            jaf.conflict_attribution = {canonicalize_pair(p1, p2)}

        return jaf

    def reset(self):
        """Reset generator state"""
        self._step = 0
        self._rng = random.Random(self._seed)
