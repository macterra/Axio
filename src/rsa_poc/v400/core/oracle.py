"""
RSA-PoC v4.0 — Oracle Policy
Implements §6.3 of v40_design_freeze.md

Scripted optimal policy for calibration gate verification.
Produces correct justifications at each step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..core.dsl import (
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
from ..core.harness import (
    Deliberator,
    DeliberationOutput,
)
from ..core.norm_state import NormStateV400
from ..env.tri_demand import (
    Action,
    GRID_SIZE,
    H,
    Observation,
    POSITIONS,
)


# ============================================================================
# Oracle State Tracking
# ============================================================================


@dataclass
class OracleState:
    """Track oracle's internal plan state."""
    current_target: Optional[str] = None  # ZONE_A, ZONE_B, ZONE_C, SOURCE
    phase: str = "COLLECT"  # COLLECT, DELIVER_A, DELIVER_B, DELIVER_C


# ============================================================================
# Path Planning (Manhattan distance)
# ============================================================================


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Compute Manhattan distance between two positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def next_move_towards(current: Tuple[int, int], target: Tuple[int, int]) -> str:
    """
    Compute next action to move from current to target.
    Returns action ID (A0-A3) or None if at target.
    """
    if current == target:
        return None

    dr = target[0] - current[0]
    dc = target[1] - current[1]

    # Prioritize vertical movement
    if dr < 0:
        return "A0"  # MOVE_N
    elif dr > 0:
        return "A1"  # MOVE_S
    elif dc > 0:
        return "A2"  # MOVE_E
    elif dc < 0:
        return "A3"  # MOVE_W

    return None


# ============================================================================
# §6.3 — Oracle Deliberator
# ============================================================================


class OracleDeliberator(Deliberator):
    """
    Oracle policy per §6.3:

    1. Collect from Source
    2. Deposit at highest-demand zone
    3. If conflict: follow active priority rule (R1 initially)
    4. At episode 2: issue patch to renew R1 with narrower scope
    5. Repeat until all zones satisfied
    """

    def __init__(self):
        self.state = OracleState()
        self.patched_r1 = False

    def reset(self) -> None:
        """Reset oracle state for new run."""
        self.state = OracleState()
        self.patched_r1 = False

    def deliberate(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> DeliberationOutput:
        """
        Generate optimal justification for current state.
        """
        patch = None

        # Check if we need to patch R1 at episode 2
        if obs.episode >= 2 and not self.patched_r1 and not obs.rule_r1_active:
            patch = self._create_r1_renewal_patch(norm_state)
            self.patched_r1 = True

        # Determine action based on current phase
        action_id, rule_ref = self._plan_action(obs, norm_state)

        # Create justification
        justification = self._create_justification(action_id, rule_ref, obs)

        return DeliberationOutput(
            justifications=[justification],
            patch=patch
        )

    def _plan_action(
        self,
        obs: Observation,
        norm_state: NormStateV400,
    ) -> Tuple[str, str]:
        """
        Plan next action based on observation.

        Returns (action_id, primary_rule_ref)
        """
        pos = obs.agent_pos

        # If we have no inventory, go collect
        if obs.inventory == 0:
            if pos == POSITIONS["SOURCE"]:
                return "A4", "R3"  # COLLECT, reference PERMISSION R3
            else:
                action = next_move_towards(pos, POSITIONS["SOURCE"])
                return action, "R4"  # MOVE, reference PERMISSION R4

        # We have inventory - decide where to deposit
        # Priority: R1 (Zone A) > R2 (Zone B) > Zone C

        # Determine target based on priority and satisfaction
        target = None
        rule_ref = "R4"  # Default to move permission

        # R1: Zone A priority (if active and unsatisfied)
        r1_active = norm_state.has_rule("R1") and obs.zone_a_demand > 0 and not obs.zone_a_satisfied
        if r1_active:
            target = "ZONE_A"
            rule_ref = "R1"
        # R2: Zone B (if R1 not binding and B unsatisfied)
        elif obs.zone_b_demand > 0 and not obs.zone_b_satisfied:
            target = "ZONE_B"
            rule_ref = "R2"
        # Zone C (no specific rule, just permission)
        elif obs.zone_c_demand > 0 and not obs.zone_c_satisfied:
            target = "ZONE_C"
            rule_ref = "R4"
        # Zone A fallback (if R1 expired but A still needs delivery)
        elif obs.zone_a_demand > 0 and not obs.zone_a_satisfied:
            target = "ZONE_A"
            rule_ref = "R4"
        else:
            # All zones satisfied - any move is fine
            return "A0", "R4"

        # Move to target or deposit
        target_pos = POSITIONS[target]
        if pos == target_pos:
            return "A5", rule_ref  # DEPOSIT
        else:
            action = next_move_towards(pos, target_pos)
            return action, "R4"  # MOVE with R4 permission

    def _create_justification(
        self,
        action_id: str,
        rule_ref: str,
        obs: Observation,
    ) -> JustificationV400:
        """Create a valid justification for the action."""
        # Determine predicate based on rule type
        if rule_ref in ["R1", "R2"]:
            predicate = Predicate.REQUIRES
        else:
            predicate = Predicate.PERMITS

        claims = [
            Claim(
                predicate=predicate,
                args=[rule_ref, action_id]
            )
        ]

        return JustificationV400(
            action_id=action_id,
            rule_refs=[rule_ref],
            claims=claims
        )

    def _create_r1_renewal_patch(self, norm_state: NormStateV400) -> NormPatchV400:
        """
        Create patch to renew R1 at episode 2.

        Per §6.3: "issue patch to renew R1 with narrower scope"
        """
        # Compute justification hash for the patch
        justification = JustificationV400(
            action_id="A5",  # DEPOSIT
            rule_refs=["R2"],  # Reference existing R2 as basis
            claims=[
                Claim(
                    predicate=Predicate.REQUIRES,
                    args=["R2", "A5", "ZONE_A"]
                )
            ]
        )
        justification_hash = content_hash(justification.to_dict())

        # Create new R1 with no expiration
        new_r1 = Rule(
            id="R1",
            type=RuleType.OBLIGATION,
            condition=Condition(
                op=ConditionOp.AND,
                args=[
                    Condition(op=ConditionOp.GT, args=["zone_a_demand", 0]),
                    Condition(op=ConditionOp.EQ, args=["zone_a_satisfied", False])
                ]
            ),
            effect=Effect(action_class=ActionClass.DEPOSIT, target="ZONE_A"),
            expires_episode=None,  # No expiration this time
            priority=10
        )

        return NormPatchV400(
            op=PatchOp.ADD,  # ADD since R1 was removed by expiration
            target_rule_id="R1",
            justification_ref=justification_hash,
            new_rule=new_r1
        )


# ============================================================================
# Oracle Runner (for calibration)
# ============================================================================


class OracleRunner:
    """
    Run Oracle policy for calibration verification.

    Per §6.2: Must achieve ≥95% success rate.
    """

    def __init__(self, seed: int = 42, max_episodes: int = 100):
        self.seed = seed
        self.max_episodes = max_episodes

    def run(self) -> dict:
        """
        Run Oracle and return results.

        Returns dict with success_rate and episode details.
        """
        from ..core.harness import MVRSA400, RunMetrics

        deliberator = OracleDeliberator()

        results = {
            "seed": self.seed,
            "episodes": self.max_episodes,
            "successes": 0,
            "failures": 0,
            "episode_results": [],
        }

        agent = MVRSA400(
            deliberator=deliberator,
            seed=self.seed,
            max_episodes=self.max_episodes,
        )

        run_metrics = agent.run()

        results["success_rate"] = run_metrics.success_rate
        results["successes"] = int(run_metrics.success_rate * run_metrics.episodes)
        results["failures"] = run_metrics.episodes - results["successes"]
        results["halt_rate"] = run_metrics.halt_rate
        results["compilation_rate"] = run_metrics.compilation_rate

        return results


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "OracleState",
    "OracleDeliberator",
    "OracleRunner",
    "manhattan_distance",
    "next_move_towards",
]
