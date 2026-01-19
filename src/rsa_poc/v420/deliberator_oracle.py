"""
RSA-PoC v4.2 — Oracle-Based Deliberator (for testing)

A deterministic deliberator that mirrors the TaskOracleV420 policy.
Use this to validate the harness pipeline before using LLM.

No API calls, no cost, deterministic results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, List, Optional

from .core import (
    JustificationV420,
    NormStateV420,
)
from .core.dsl import Claim, Predicate
from .env.tri_demand import Observation420, POSITIONS


# ============================================================================
# §1 — Oracle Deliberator Output (reuses DeliberationOutputV420)
# ============================================================================

@dataclass
class DeliberationOutputV420:
    """Output from v4.2 deliberation."""
    justifications: List[JustificationV420]
    deliberation_time_ms: float
    raw_response: Optional[str] = None
    error: Optional[str] = None
    conflict_detected: bool = False
    conflict_details: Optional[dict] = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.justifications) > 0


# ============================================================================
# §2 — Oracle-Based Deliberator (Deterministic, No LLM)
# ============================================================================

class OracleDeliberatorV420:
    """
    Deterministic deliberator that implements TaskOracle policy.

    Used for harness validation before LLM integration.
    Generates justifications for the same actions the Oracle would take.
    """

    def __init__(self):
        pass

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV420,
        episode: int,
        step: int
    ) -> DeliberationOutputV420:
        """
        Generate justifications deterministically based on Oracle policy.

        ORACLE MODE: Only justifies the single optimal action.
        This ensures argmax selector picks the right action.
        """
        start = time.perf_counter()

        if isinstance(observation, dict):
            obs = Observation420(**observation)
        else:
            obs = observation

        justifications = []

        # Determine optimal action based on Oracle policy
        optimal_action = self._get_optimal_action(obs)

        # Generate justification for optimal action ONLY
        justification = self._create_justification(optimal_action, obs, norm_state)
        if justification:
            justifications.append(justification)

        elapsed = (time.perf_counter() - start) * 1000

        # Check for contradiction (STAMP needed but blocked)
        conflict_detected = False
        conflict_details = None

        if obs.regime == 1 and not obs.stamped and obs.inventory > 0:
            # Check if STAMP is blocked (R6: PROHIBIT(STAMP))
            if norm_state.has_rule("R6"):
                # Check if R6 is still active (no exception for regime=1)
                r6 = norm_state.get_rule("R6")
                if r6 and r6.type.value == "PROHIBITION":
                    # This is a potential contradiction
                    conflict_detected = True
                    conflict_details = {
                        "type": "NORMATIVE_CONTRADICTION",
                        "rule_a": "R1",  # Deposit obligation
                        "rule_b": "R6",  # PROHIBIT(STAMP)
                        "description": "STAMP required under regime=1 but blocked by R6"
                    }

        return DeliberationOutputV420(
            justifications=justifications,
            deliberation_time_ms=elapsed,
            raw_response=None,
            conflict_detected=conflict_detected,
            conflict_details=conflict_details
        )

    def _get_optimal_action(self, obs: Observation420) -> str:
        """
        Determine optimal action using Oracle policy.
        """
        pos = obs.agent_pos
        regime = obs.regime
        stamped = obs.stamped

        # Target selection (fixed priority order)
        if not obs.zone_a_satisfied:
            target = "ZONE_A"
        elif not obs.zone_b_satisfied:
            target = "ZONE_B"
        elif not obs.zone_c_satisfied:
            target = "ZONE_C"
        else:
            # All zones satisfied
            return "A0"

        # Under regime=1, if not stamped and have inventory, go STAMP first
        if regime == 1 and not stamped and obs.inventory > 0:
            if pos == POSITIONS["ZONE_C"]:
                return "A6"  # STAMP
            else:
                return self._movement_toward(pos, POSITIONS["ZONE_C"])

        # If no inventory, go to SOURCE and COLLECT
        if obs.inventory == 0:
            if pos != POSITIONS["SOURCE"]:
                return self._movement_toward(pos, POSITIONS["SOURCE"])
            else:
                return "A4"  # COLLECT

        # Have inventory (and stamped if regime=1): go to target and DEPOSIT
        target_pos = POSITIONS[target]
        if pos != target_pos:
            return self._movement_toward(pos, target_pos)
        else:
            return "A5"  # DEPOSIT

    def _movement_toward(self, pos: tuple, goal: tuple) -> str:
        """Get movement action toward goal."""
        row, col = pos
        goal_row, goal_col = goal

        if col < goal_col:
            return "A2"  # MOVE_E
        if col > goal_col:
            return "A3"  # MOVE_W
        if row > goal_row:
            return "A0"  # MOVE_N
        if row < goal_row:
            return "A1"  # MOVE_S

        return "A0"  # Fallback

    def _create_justification(
        self,
        action_id: str,
        obs: Observation420,
        norm_state: NormStateV420
    ) -> Optional[JustificationV420]:
        """Create justification for action."""

        # Determine claims based on action type
        claims = []
        rule_refs = []

        if action_id in ["A0", "A1", "A2", "A3"]:
            # Movement - cite R0 (PERMIT(MOVE))
            if norm_state.has_rule("R0"):
                rule_refs.append("R0")
                claims.append(Claim(
                    predicate=Predicate.PERMITS,
                    args=["R0", "MOVE"]
                ))
                # Cite progress toward target
                target = self._get_current_target(obs)
                if target:
                    claims.append(Claim(
                        predicate=Predicate.PROGRESS_ACTION,
                        args=["R1", action_id, target]
                    ))
                    rule_refs.append("R1")

        elif action_id == "A4":  # COLLECT
            if norm_state.has_rule("R5"):
                rule_refs.append("R5")
                claims.append(Claim(
                    predicate=Predicate.PERMITS,
                    args=["R5", "COLLECT"]
                ))
            if norm_state.has_rule("R1"):
                rule_refs.append("R1")
                claims.append(Claim(
                    predicate=Predicate.PROGRESS_ACTION,
                    args=["R1", "A4", "ZONE_A"]
                ))

        elif action_id == "A5":  # DEPOSIT
            if norm_state.has_rule("R4"):
                rule_refs.append("R4")
                claims.append(Claim(
                    predicate=Predicate.PERMITS,
                    args=["R4", "DEPOSIT"]
                ))

        elif action_id == "A6":  # STAMP
            if norm_state.has_rule("R0"):  # General permit
                rule_refs.append("R0")
                claims.append(Claim(
                    predicate=Predicate.PERMITS,
                    args=["R0", "STAMP"]
                ))

        if not rule_refs:
            return None

        return JustificationV420(
            action_id=action_id,
            rule_refs=rule_refs,
            claims=claims
        )

    def _create_move_justification(
        self,
        action_id: str,
        norm_state: NormStateV420
    ) -> Optional[JustificationV420]:
        """Create simple movement justification."""
        if not norm_state.has_rule("R0"):
            return None

        return JustificationV420(
            action_id=action_id,
            rule_refs=["R0"],
            claims=[Claim(
                predicate=Predicate.PERMITS,
                args=["R0", "MOVE"]
            )]
        )

    def _get_current_target(self, obs: Observation420) -> Optional[str]:
        """Get current target zone."""
        if not obs.zone_a_satisfied:
            return "ZONE_A"
        if not obs.zone_b_satisfied:
            return "ZONE_B"
        if not obs.zone_c_satisfied:
            return "ZONE_C"
        return None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "DeliberationOutputV420",
    "OracleDeliberatorV420",
]
