"""Deterministic Generator for v1.1

Generates JAF-1.1 artifacts with mechanical prediction computation.

This generator computes predicted fields by calling the same logic used by
the compiler, ensuring perfect introspection in the baseline condition.
"""

from typing import Set, Dict, Optional, Tuple, List
import uuid

# Import v1.1 schema
try:
    from ..jaf.schema import JAF110
    from ...v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, CompilerHints,
        ConflictResolution, canonicalize_pair
    )
    from ...v100.state.normative import NormativeStateV100
except ImportError:
    from rsa_poc.v110.jaf.schema import JAF110
    from rsa_poc.v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, CompilerHints,
        ConflictResolution, canonicalize_pair
    )
    from rsa_poc.v100.state.normative import NormativeStateV100


class DeterministicGeneratorV110:
    """
    v1.1 deterministic generator with mechanical prediction.

    Computes predicted fields by simulating compilation logic,
    providing a gold-standard baseline for audit validation.
    """

    def __init__(self, normative_state: NormativeStateV100):
        """
        Initialize generator with normative state.

        Args:
            normative_state: Normative state with precedent tracking
        """
        self.normative_state = normative_state
        self._step = 0

    def generate(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str = "MVRA_v110"
    ) -> JAF110:
        """
        Generate JAF-1.1 artifact with mechanically computed predictions.

        Args:
            feasible_actions: List of currently feasible action IDs
            apcm: Action-Preference Consequence Map from environment
            agent_id: Agent identifier for artifact

        Returns:
            JAF110 artifact ready for compilation
        """
        self._step += 1

        # === v1.0 fields (unchanged logic) ===

        # Detect collisions from APCM
        collisions = self._detect_collisions(apcm, feasible_actions)

        # Determine authorized violations and conflict resolution
        if collisions:
            authorized_violations, conflict_attribution = self._resolve_collisions(
                collisions, apcm, feasible_actions
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

        # Determine conflict resolution
        conflict_resolution = None
        if precedent and collisions:
            conflict_resolution = ConflictResolution(
                mode=resolution_mode,
                previous_artifact_digest=precedent_digest
            )

        # === v1.1: Compute predictions mechanically ===

        # Simulate compilation to compute actual sets
        predicted_forbidden_actions, predicted_allowed_actions = self._compute_action_predictions(
            authorized_violations,
            required_preservations,
            apcm,
            feasible_actions
        )

        # Compute inevitable violations/preservations
        predicted_violations, predicted_preservations = self._compute_outcome_predictions(
            predicted_allowed_actions,
            apcm,
            all_preferences
        )

        # Pick candidate action from predicted allowed set (or first feasible if none allowed)
        if predicted_allowed_actions:
            candidate_action = sorted(predicted_allowed_actions)[0]  # Deterministic choice
        elif feasible_actions:
            candidate_action = feasible_actions[0]
        else:
            candidate_action = "WAIT"  # Fallback

        # Build JAF-1.1
        jaf = JAF110(
            artifact_version="JAF-1.1",
            identity=Identity(
                agent_id=agent_id,
                continuity_counter=self._step
            ),
            references=References(
                belief_ids=["WORLD_STATE"],  # Minimal for v1.1
                pref_ids=list(all_preferences)
            ),
            action_claim=ActionClaim(
                candidate_action_id=candidate_action,
                relation="SATISFIES",
                target_pref_id=None,
                expected_constraint_effect="NO_CONSTRAINT"
            ),
            relevance=Relevance(
                required_belief_ids=["WORLD_STATE"]
            ),
            compiler_hints=CompilerHints(
                forbid_action_ids=[],
                forbid_mode="NONE",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            authorized_violations=authorized_violations,
            required_preservations=required_preservations,
            conflict_attribution=conflict_attribution,
            conflict_resolution=conflict_resolution,
            step=self._step,
            nonce=str(uuid.uuid4()),
            # v1.1 predictive fields
            predicted_forbidden_actions=predicted_forbidden_actions,
            predicted_allowed_actions=predicted_allowed_actions,
            predicted_violations=predicted_violations,
            predicted_preservations=predicted_preservations
        )

        return jaf

    def _detect_collisions(
        self,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: List[str]
    ) -> Set[Tuple[str, str]]:
        """
        Detect genuine preference collisions from APCM.

        A collision exists when no feasible action has an empty violation set.
        In other words: every action violates at least one preference (norm collision).

        This is DISTINCT from gridlock (A_actual = ∅ after compilation).

        Returns set of canonicalized collision pairs, or empty set if clean path exists.
        """
        all_preferences = self.normative_state.get_preferences()

        # Check for norm collision: does a clean path exist?
        # Clean path = at least one action with empty violates set
        exists_clean = False

        for action in feasible_actions:
            if action not in apcm:
                continue

            violates = apcm[action].get("violates", set())

            # If this action violates nothing, clean path exists
            if not violates:
                exists_clean = True
                break

        # If clean path exists, no collision
        if exists_clean:
            return set()

        # Norm collision detected: every action violates something
        # Collect all violated preferences across all actions
        all_violated = set()
        for action in feasible_actions:
            if action in apcm:
                all_violated.update(apcm[action].get("violates", set()))

        # Generate collision pairs from all violated preferences
        # (they're in mutual conflict since no action can satisfy all)
        collisions = set()
        violated_list = sorted(all_violated)
        for i in range(len(violated_list)):
            for j in range(i + 1, len(violated_list)):
                collisions.add(canonicalize_pair(violated_list[i], violated_list[j]))

        return collisions

    def _resolve_collisions(
        self,
        collisions: Set[Tuple[str, str]],
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: List[str]
    ) -> Tuple[Set[str], Set[Tuple[str, str]]]:
        """
        Resolve collisions by selecting priority preference.

        Strategy: Pick first preference in sorted order as priority,
        authorize violations of all others involved in collisions.

        Returns: (authorized_violations, conflict_attribution)
        """
        # Get all preferences involved in collisions
        collision_prefs = set()
        for p1, p2 in collisions:
            collision_prefs.add(p1)
            collision_prefs.add(p2)

        # Pick priority (deterministic: first in sorted order)
        priority_pref = sorted(collision_prefs)[0]

        # Authorize violations of non-priority collision preferences
        authorized_violations = collision_prefs - {priority_pref}

        return authorized_violations, collisions

    def _compute_action_predictions(
        self,
        authorized_violations: Set[str],
        required_preservations: Set[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: List[str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Mechanically compute which actions will be forbidden/allowed.

        This replicates the v1.0 compilation logic to predict F_actual and A_actual.

        Returns: (predicted_forbidden, predicted_allowed)
        """
        feasible_set = set(feasible_actions)
        forbidden = set()

        for action in feasible_actions:
            if action not in apcm:
                continue

            # Get what this action violates
            violates = apcm[action].get("violates", set())

            # Check if action violates any required_preservations (not authorized)
            unauth_violations = violates & required_preservations

            # If action violates a required preservation, forbid it
            if unauth_violations:
                forbidden.add(action)

        allowed = feasible_set - forbidden

        return forbidden, allowed

    def _compute_outcome_predictions(
        self,
        allowed_actions: Set[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        all_preferences: Set[str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Compute inevitable violations and preservations.

        V_actual = preferences violated by ALL allowed actions
        P_actual = preferences satisfied by ALL allowed actions

        Returns: (predicted_violations, predicted_preservations)
        """
        if not allowed_actions:
            # Gridlock case - return empty sets (will be skipped by Audit C′)
            return set(), set()

        # V_actual: preferences violated by ALL allowed actions
        violations = None
        for action in allowed_actions:
            if action not in apcm:
                continue

            violated_by_action = apcm[action].get("violates", set())

            # Intersection: violated by ALL actions
            if violations is None:
                violations = violated_by_action.copy()
            else:
                violations = violations & violated_by_action

        if violations is None:
            violations = set()

        # P_actual: preferences satisfied by ALL allowed actions
        preservations = None
        for action in allowed_actions:
            if action not in apcm:
                continue

            satisfied_by_action = apcm[action].get("satisfies", set())

            # Intersection: satisfied by ALL actions
            if preservations is None:
                preservations = satisfied_by_action.copy()
            else:
                preservations = preservations & satisfied_by_action

        if preservations is None:
            preservations = set()

        return violations, preservations
        if preservations is None:
            preservations = set()

        return violations, preservations

    def reset(self):
        """Reset generator state"""
        self._step = 0


class ScrambledPredictionsGeneratorV110:
    """
    Ablation: Generate valid v1.0 fields but corrupt v1.1 predictions.

    Tests whether audit layer is causally load-bearing by intentionally
    producing incorrect predictions while maintaining v1.0 validity.
    """

    def __init__(self, normative_state: NormativeStateV100, seed: int = 42):
        """
        Initialize scrambled generator.

        Args:
            normative_state: Normative state with precedent tracking
            seed: Random seed for scrambling
        """
        self.base_generator = DeterministicGeneratorV110(normative_state)
        self._seed = seed
        import random
        self._rng = random.Random(seed)

    def generate(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str = "MVRA_v110_Scrambled"
    ) -> JAF110:
        """
        Generate JAF with valid v1.0 fields but scrambled predictions.

        Expected: Audit A/B/C failures without v1.0 rule violations.
        """
        # Generate valid JAF-1.1 first
        jaf = self.base_generator.generate(feasible_actions, apcm, agent_id)

        # Scramble predictions while keeping v1.0 fields intact
        all_actions = set(feasible_actions)
        all_prefs = self.base_generator.normative_state.get_preferences()

        # Corrupt action predictions (swap some elements)
        if jaf.predicted_forbidden_actions and jaf.predicted_allowed_actions:
            # Move one action from forbidden to allowed (or vice versa)
            if self._rng.random() > 0.5 and jaf.predicted_forbidden_actions:
                moved = self._rng.choice(list(jaf.predicted_forbidden_actions))
                jaf.predicted_forbidden_actions.remove(moved)
                jaf.predicted_allowed_actions.add(moved)
            elif jaf.predicted_allowed_actions:
                moved = self._rng.choice(list(jaf.predicted_allowed_actions))
                jaf.predicted_allowed_actions.remove(moved)
                jaf.predicted_forbidden_actions.add(moved)

        # Corrupt outcome predictions
        if all_prefs:
            # Add or remove a random preference from violations
            rand_pref = self._rng.choice(list(all_prefs))
            if rand_pref in jaf.predicted_violations:
                jaf.predicted_violations.remove(rand_pref)
                jaf.predicted_preservations.add(rand_pref)
            else:
                jaf.predicted_violations.add(rand_pref)
                if rand_pref in jaf.predicted_preservations:
                    jaf.predicted_preservations.remove(rand_pref)

        return jaf

    def reset(self):
        """Reset generator state"""
        self.base_generator.reset()
        self._rng = __import__('random').Random(self._seed)
