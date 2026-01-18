"""
RSA-PoC v4.0.1 — Formal Deliberator
Implements §4.2 compliant deliberator for baseline/ablations.

This is NOT a hidden policy agent. It:
1. Consumes (obs, NormState)
2. Enumerates all possible actions
3. For each action, constructs a justification referencing applicable rules
4. Optionally emits NormPatch based on reflection triggers
5. Contains NO hardcoded policy logic beyond schema formatting

The deliberator is "intentionally dumb" — it doesn't know which action is
optimal. That decision comes from the MASK stage (obligation gate) and
SELECT stage (uniform random from feasible set).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .dsl import (
    ActionClass,
    Claim,
    Condition,
    ConditionOp,
    Effect,
    JustificationV400,
    NormPatchV400,
    PatchOp,
    Predicate,
    Rule,
    RuleType,
    content_hash,
)
from .harness import Deliberator, DeliberationOutput
from .norm_state import NormStateV400
from ..env.tri_demand import (
    Action,
    GRID_SIZE,
    H,
    Observation,
    POSITIONS,
)


# ============================================================================
# Action → Rule Mapping
# ============================================================================

# Map action IDs to ActionClass for rule lookup
ACTION_TO_CLASS = {
    "A0": ActionClass.MOVE,  # MOVE_N
    "A1": ActionClass.MOVE,  # MOVE_S
    "A2": ActionClass.MOVE,  # MOVE_E
    "A3": ActionClass.MOVE,  # MOVE_W
    "A4": ActionClass.COLLECT,
    "A5": ActionClass.DEPOSIT,
}

# All action IDs in the environment
ALL_ACTIONS = ["A0", "A1", "A2", "A3", "A4", "A5"]


# ============================================================================
# §4.2 — Formal Deliberator
# ============================================================================


class FormalDeliberator(Deliberator):
    """
    Formal deliberator that routes through the normative loop.

    Properties:
    - Enumerates ALL actions, not just "good" ones
    - References rules mechanically (no policy reasoning)
    - Issues patches based on reflection triggers (rule expiry)
    - Does NOT contain optimal behavior — that emerges from the pipeline

    This deliberator is "dumb" in the sense that it always proposes
    justifications for all actions. The filtering happens downstream:
    - COMPILE: rejects invalid references
    - MASK: filters by permissions/prohibitions/obligations
    - SELECT: picks uniformly from feasible set

    If the environment is solvable, it's because the NormState + Compiler
    + Obligation Gate correctly constrain the agent to optimal behavior.
    If not, the agent halts or fails.
    """

    def __init__(self):
        self.patched_r1 = False
        self.episode_at_last_patch = -1

    def reset(self) -> None:
        """Reset deliberator state for new run."""
        self.patched_r1 = False
        self.episode_at_last_patch = -1

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Generate justifications for all candidate actions.

        Returns justifications for ALL actions. The COMPILE and MASK stages
        will filter down to the feasible set.
        """
        patch = self._check_reflection_triggers(obs, norm_state)
        justifications = self._enumerate_justifications(obs, norm_state)

        return DeliberationOutput(
            justifications=justifications,
            patch=patch
        )

    def _enumerate_justifications(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> List[JustificationV400]:
        """
        Create justifications for all actions based on current NormState.

        For each action:
        1. Find rules that apply to its ActionClass
        2. Create a justification referencing those rules
        3. If no rules apply, still create justification with R4 (fallback)
        """
        justifications = []

        for action_id in ALL_ACTIONS:
            action_class = ACTION_TO_CLASS[action_id]
            applicable_rules = self._find_applicable_rules(action_class, norm_state, obs)

            if applicable_rules:
                # Create justification referencing applicable rules
                justification = self._create_justification(
                    action_id=action_id,
                    rule_refs=[r.id for r in applicable_rules],
                    obs=obs
                )
            else:
                # No specific rules — try to reference R4 (general permission)
                # If R4 doesn't exist or doesn't apply, compiler will reject
                if norm_state.has_rule("R4"):
                    justification = self._create_justification(
                        action_id=action_id,
                        rule_refs=["R4"],
                        obs=obs
                    )
                else:
                    # No fallback rule — create justification anyway
                    # Compiler will return REFERENCE_ERROR
                    justification = self._create_justification(
                        action_id=action_id,
                        rule_refs=["R4"],  # Will fail at compile time
                        obs=obs
                    )

            justifications.append(justification)

        return justifications

    def _find_applicable_rules(
        self,
        action_class: ActionClass,
        norm_state: NormStateV400,
        obs: Observation,
    ) -> List[Rule]:
        """
        Find rules that apply to the given action class.

        A rule applies if:
        - Its effect's action_class matches
        - It's currently active (not expired)
        """
        applicable = []

        for rule in norm_state.rules:
            # Check if rule's effect matches action class
            if rule.effect.action_class == action_class:
                applicable.append(rule)
            elif rule.effect.action_class == ActionClass.ANY:
                applicable.append(rule)

        return applicable

    def _create_justification(
        self,
        action_id: str,
        rule_refs: List[str],
        obs: Observation,
    ) -> JustificationV400:
        """Create a justification for the given action."""
        # Create claims based on current observation
        # Use valid predicates from the closed vocabulary
        claims = [
            Claim(
                predicate=Predicate.SATISFIES,
                args=[action_id, f"pos_{obs.agent_pos[0]}_{obs.agent_pos[1]}"],
            ),
        ]

        # Add zone satisfaction claims
        if obs.zone_a_satisfied:
            claims.append(Claim(
                predicate=Predicate.SATISFIES,
                args=[action_id, "ZONE_A"],
            ))
        if obs.zone_b_satisfied:
            claims.append(Claim(
                predicate=Predicate.SATISFIES,
                args=[action_id, "ZONE_B"],
            ))
        if obs.zone_c_satisfied:
            claims.append(Claim(
                predicate=Predicate.SATISFIES,
                args=[action_id, "ZONE_C"],
            ))

        return JustificationV400(
            action_id=action_id,
            claims=claims,
            rule_refs=rule_refs,
        )

    def _check_reflection_triggers(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> Optional[NormPatchV400]:
        """
        Check for reflection triggers that require NormPatch.

        Per §3.2: Reflection triggers include rule expiry events.

        This is NOT policy logic — it's mechanical response to:
        - R1 expired → issue patch to renew R1 (if not already done)
        """
        # Check if R1 has expired and we haven't patched yet
        if not obs.rule_r1_active and not self.patched_r1:
            # R1 expired — issue renewal patch
            # This happens at episode 2 per the environment design
            if obs.episode >= 2 and obs.episode != self.episode_at_last_patch:
                self.patched_r1 = True
                self.episode_at_last_patch = obs.episode
                return self._create_r1_renewal_patch(norm_state)

        return None

    def _create_r1_renewal_patch(
        self,
        norm_state: NormStateV400,
    ) -> NormPatchV400:
        """
        Create patch to renew R1 with narrower scope.

        Per design: R1 initially applies unconditionally, expires at episode 1.
        Renewal makes R1 conditional on Zone A not being satisfied.
        """
        # Create renewed R1 with narrower scope
        renewed_r1 = Rule(
            id="R1",
            type=RuleType.OBLIGATION,
            condition=Condition(
                op=ConditionOp.AND,
                args=[
                    Condition(op=ConditionOp.IN_STATE, args=["ZONE_A"]).to_dict(),
                    Condition(
                        op=ConditionOp.NOT,
                        args=[Condition(op=ConditionOp.EQ, args=["zone_a_satisfied", True]).to_dict()]
                    ).to_dict(),
                ]
            ),
            effect=Effect(action_class=ActionClass.DEPOSIT, target="ZONE_A"),
            priority=100,  # High priority
            expires_episode=None,  # Persistent
        )

        return NormPatchV400(
            op=PatchOp.ADD,
            target_rule_id="R1",
            justification_ref=content_hash(str(renewed_r1))[:16],
            new_rule=renewed_r1
        )


# ============================================================================
# Ablation Deliberators
# ============================================================================


class SemanticExcisionDeliberator(Deliberator):
    """
    Run A: Semantic Excision — remove all OBLIGATION/PROHIBITION rules.

    Uses FormalDeliberator base but filters NormState before deliberation.
    """

    def __init__(self):
        self.base = FormalDeliberator()

    def reset(self) -> None:
        self.base.reset()

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Deliberate with semantic excision.

        Filter NormState to remove OBLIGATION and PROHIBITION rules.
        Only PERMISSION rules remain.
        """
        # Create filtered rules list (not dict)
        filtered_rules = [
            rule for rule in norm_state.rules
            if rule.type == RuleType.PERMISSION
        ]

        # Create new norm state with filtered rules
        from .dsl import hash_rules
        filtered_state = NormStateV400(
            norm_hash=hash_rules(filtered_rules),
            rules=filtered_rules,
            rev=norm_state.rev,
            last_patch_hash=norm_state.last_patch_hash,
            ledger_root=norm_state.ledger_root,
        )

        return self.base.deliberate(obs, filtered_state)


class ReflectionExcisionDeliberator(Deliberator):
    """
    Run B: Reflection Excision — disable NormPatch emission.

    Uses FormalDeliberator but never emits patches.
    """

    def __init__(self):
        self.base = FormalDeliberator()

    def reset(self) -> None:
        self.base.reset()

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Deliberate without reflection (no patches).
        """
        output = self.base.deliberate(obs, norm_state)
        # Strip patch — reflection is disabled
        return DeliberationOutput(
            justifications=output.justifications,
            patch=None  # No reflection
        )


class PersistenceExcisionDeliberator(Deliberator):
    """
    Run C: Persistence Excision — reset NormState each episode.

    Uses FormalDeliberator but deliberator doesn't maintain cross-episode state.
    The harness must also reset NormState each episode.
    """

    def __init__(self):
        self.base = FormalDeliberator()

    def reset(self) -> None:
        self.base.reset()

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Deliberate without persistence.

        Note: The harness must also reset NormState each episode.
        This deliberator just ensures its internal state is also reset.
        """
        # Reset base deliberator state at each episode start
        if obs.step == 0:
            self.base.reset()

        return self.base.deliberate(obs, norm_state)


class TraceExcisionDeliberator(Deliberator):
    """
    Run D: Trace Excision — remove justification from compilation input.

    Per v4.0.1 binding action: compilation receives NO justification object.
    JCOMP must return SCHEMA_ERROR, leading to empty feasible set → HALT.

    Implementation: We cannot return empty justifications (violates DeliberationOutput).
    Instead, we set a flag that the harness checks BEFORE compilation.
    The harness must skip COMPILE entirely and record SCHEMA_ERROR.
    """

    # Sentinel value to signal trace excision
    TRACE_EXCISED = True

    def __init__(self):
        self._trace_excised = True

    def reset(self) -> None:
        pass

    @property
    def is_trace_excised(self) -> bool:
        """Check if this deliberator produces trace-excised output."""
        return self._trace_excised

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Return a minimal valid justification that will be IGNORED by the harness.

        The harness must check `deliberator.is_trace_excised` BEFORE compilation
        and, if True, treat this as "no justification received" → SCHEMA_ERROR.

        We return a minimal valid justification here only to satisfy the
        DeliberationOutput type constraint. It will NOT be compiled.
        """
        # Create a minimal valid justification (to satisfy type constraint)
        # The harness will NOT compile this — it checks is_trace_excised first
        dummy = JustificationV400(
            action_id="A0",
            claims=[Claim(predicate=Predicate.PERMITS, args=["R4", "A0"])],
            rule_refs=["R4"],  # Minimal valid ref
        )

        return DeliberationOutput(
            justifications=[dummy],
            patch=None
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "FormalDeliberator",
    "SemanticExcisionDeliberator",
    "ReflectionExcisionDeliberator",
    "PersistenceExcisionDeliberator",
    "TraceExcisionDeliberator",
    "ALL_ACTIONS",
    "ACTION_TO_CLASS",
]
