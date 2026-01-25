"""Deterministic Justification Generator for RSA-PoC v0.1

Non-LLM rule-based generator for validating the pipeline.
Produces valid JAF artifacts based on feasibility and normative state.
"""

import random
from typing import List, Set

# Handle both package and script imports
try:
    from ..jaf.schema import JAF010, Identity, References, ActionClaim, Relevance, CompilerHints
    from ..state.normative import NormativeState, PreferenceRegistryV010
except ImportError:
    from jaf.schema import JAF010, Identity, References, ActionClaim, Relevance, CompilerHints
    from state.normative import NormativeState, PreferenceRegistryV010


class DeterministicJustificationGenerator:
    """
    Rule-based justification generator.

    Generates valid JAF artifacts without using LLMs.
    Used to validate causal structure in v0.1.

    Critical: This generator MUST receive:
    - Normative state (read-only)
    - Feasibility list (read-only)

    MUST NOT receive:
    - Reward values
    - Policy internals
    - Chosen action (pre-selection)
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def generate(
        self,
        normative_state: NormativeState,
        feasible_actions: List[str],
        step: int
    ) -> JAF010:
        """
        Generate JAF artifact for current step.

        Args:
            normative_state: Current normative state (read-only)
            feasible_actions: List of feasible action IDs (read-only)
            step: Current step number

        Returns:
            Valid JAF-0.1 artifact
        """
        # Identify temptation actions (feasible + violate preferences)
        temptations = self._identify_temptations(feasible_actions)

        # Identify safe actions (feasible + don't violate preferences)
        safe_actions = [a for a in feasible_actions if a not in temptations]

        # Decide which action to target for justification
        # Strategy: alternate between forbidding temptations and allowing safe actions
        if temptations and (step % 2 == 0 or not safe_actions):
            # Forbid a temptation
            candidate = self._rng.choice(temptations)
            relation = "VIOLATES"
            violated_prefs = PreferenceRegistryV010.get_violated_by_action(candidate)
            target_pref_id = violated_prefs[0] if violated_prefs else None
            forbid_mode = "FORBID_CANDIDATE_ONLY"
            forbid_action_ids = []  # Empty for FORBID_CANDIDATE_ONLY per spec
            reason_code = "R_PREF_VIOLATION"
        else:
            # Allow a safe action (by not forbidding it)
            if safe_actions:
                candidate = self._rng.choice(safe_actions)
            else:
                candidate = self._rng.choice(feasible_actions)
            relation = "SATISFIES"
            target_pref_id = None
            forbid_mode = "NONE"
            forbid_action_ids = []  # Empty for NONE per spec
            reason_code = "R_POLICY_GUARD"

        # Select beliefs and preferences to reference
        all_belief_ids = normative_state.get_belief_ids()
        all_pref_ids = normative_state.get_pref_ids()

        # Sample a subset (at least 1 each)
        num_beliefs = self._rng.randint(1, min(3, len(all_belief_ids)))
        num_prefs = self._rng.randint(1, min(3, len(all_pref_ids)))

        belief_ids = self._rng.sample(all_belief_ids, num_beliefs)
        pref_ids = self._rng.sample(all_pref_ids, num_prefs)

        # Ensure target_pref_id is in pref_ids if needed
        if target_pref_id and target_pref_id not in pref_ids:
            pref_ids.append(target_pref_id)

        # Required beliefs is subset of referenced beliefs
        required_belief_ids = belief_ids[:max(1, len(belief_ids)//2)]

        # Generate nonce
        nonce = f"step_{step}_{self._rng.randint(1000, 9999)}"

        # Construct JAF
        artifact = JAF010(
            artifact_version="JAF-0.1",
            step=step,
            identity=Identity(
                agent_id=normative_state.agent_id,
                continuity_counter=step
            ),
            references=References(
                belief_ids=belief_ids,
                pref_ids=pref_ids
            ),
            action_claim=ActionClaim(
                candidate_action_id=candidate,
                relation=relation,
                target_pref_id=target_pref_id,
                expected_constraint_effect=(
                    "FORBID_CANDIDATE" if forbid_mode != "NONE" else "NO_CONSTRAINT"
                )
            ),
            relevance=Relevance(
                required_belief_ids=required_belief_ids
            ),
            compiler_hints=CompilerHints(
                forbid_action_ids=forbid_action_ids,
                forbid_mode=forbid_mode,
                constraint_reason_code=reason_code
            ),
            nonce=nonce,
            comment=f"Deterministic generation for step {step}"
        )

        # Validate before returning
        artifact.validate()

        return artifact

    def _identify_temptations(self, feasible_actions: List[str]) -> List[str]:
        """
        Identify which feasible actions are temptations.

        Temptations are actions that violate preferences.
        """
        temptations = []
        for action in feasible_actions:
            violated = PreferenceRegistryV010.get_violated_by_action(action)
            if violated:
                temptations.append(action)
        return temptations


class ScrambledJustificationGenerator(DeterministicJustificationGenerator):
    """
    Ablation variant: generates structurally corrupted JAF artifacts.

    Used to test that justifications are causally load-bearing.
    Scrambling should cause compile failures or different masks.
    """

    def generate(
        self,
        normative_state: NormativeState,
        feasible_actions: List[str],
        step: int
    ) -> JAF010:
        """Generate scrambled artifact"""
        # Generate normal artifact first
        artifact = super().generate(normative_state, feasible_actions, step)

        # Scramble it (introduce schema violations)
        scramble_type = self._rng.choice([
            "wrong_version",
            "mismatch_continuity",
            "invalid_relation",
            "target_pref_mismatch",
            "forbid_mode_mismatch"
        ])

        if scramble_type == "wrong_version":
            artifact.artifact_version = "JAF-0.0"
        elif scramble_type == "mismatch_continuity":
            artifact.identity.continuity_counter = step + 1
        elif scramble_type == "invalid_relation":
            artifact.action_claim.relation = "MAYBE_VIOLATES"
        elif scramble_type == "target_pref_mismatch":
            # Claim VIOLATES but set target_pref_id to None
            artifact.action_claim.relation = "VIOLATES"
            artifact.action_claim.target_pref_id = None
        elif scramble_type == "forbid_mode_mismatch":
            # Set EXPLICIT_LIST but empty forbid_action_ids
            artifact.compiler_hints.forbid_mode = "EXPLICIT_LIST"
            artifact.compiler_hints.forbid_action_ids = []

        return artifact
