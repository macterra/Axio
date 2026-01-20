"""
RSA-PoC v4.3 — Oracle-Based Deliberator (for testing)

A deterministic deliberator that implements the TaskOracleV430 policy.
Use this to validate the harness pipeline before using LLM.

v4.3 additions:
- Handles both Contradiction A (regime 1) and Contradiction B (regime 2)
- Issues canonical Repair A and Repair B patches
- Tracks epoch chain for R6 anti-amnesia

No API calls, no cost, deterministic results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .core import (
    JustificationV430,
    NormStateV430,
    LawRepairActionV430,
    Condition,
    ConditionOp,
    PatchOp,
    PatchOperation,
    create_canonical_repair_b,
)
from .core.dsl import Claim, Predicate
from .env.tri_demand import (
    Observation430,
    POSITIONS,
    REGIME_1_START,
    REGIME_2_PREREGISTERED_START,
)


# ============================================================================
# §1 — Oracle Deliberator Output (v4.3)
# ============================================================================

@dataclass
class DeliberationOutputV430:
    """Output from v4.3 deliberation."""
    justifications: List[JustificationV430]
    deliberation_time_ms: float
    raw_response: Optional[str] = None
    error: Optional[str] = None
    conflict_detected: bool = False
    conflict_type: Optional[str] = None  # 'A' or 'B'
    conflict_details: Optional[dict] = None
    repair_action: Optional[LawRepairActionV430] = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.justifications) > 0


# ============================================================================
# §2 — Oracle-Based Deliberator (Deterministic, No LLM)
# ============================================================================

class OracleDeliberatorV430:
    """
    Deterministic deliberator that implements TaskOracleV430 policy.

    Used for harness validation before LLM integration.
    Generates justifications and issues repairs for contradictions.

    v4.3: Handles both Contradiction A and B.
    """

    def __init__(self):
        # Track epoch chain for R6 anti-amnesia
        self.epoch_chain: List[str] = []
        self.repair_a_issued: bool = False
        self.repair_b_issued: bool = False

    def set_epoch_chain(self, epoch_chain: List[str]) -> None:
        """Update epoch chain from harness."""
        self.epoch_chain = epoch_chain.copy()

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV430,
        episode: int,
        step: int,
        regime: int,
    ) -> DeliberationOutputV430:
        """
        Generate justifications deterministically based on Oracle policy.

        ORACLE MODE: Only justifies the single optimal action.
        Also detects contradictions and generates repair actions.
        """
        start = time.perf_counter()

        if isinstance(observation, dict):
            obs = Observation430(**observation)
        else:
            obs = observation

        justifications = []
        conflict_detected = False
        conflict_type = None
        conflict_details = None
        repair_action = None

        # Check for Contradiction A (regime 1, STAMP blocked)
        if regime == 1:
            contradiction_a = self._check_contradiction_a(obs, norm_state)
            if contradiction_a:
                conflict_detected = True
                conflict_type = 'A'
                conflict_details = contradiction_a

                # Generate Repair A if not already issued
                if not self.repair_a_issued:
                    repair_action = self._generate_repair_a(
                        trace_entry_id=f"trace_a_{episode}_{step}",
                        norm_state=norm_state,
                    )

        # Check for Contradiction B (regime 2, DEPOSIT blocked at zones)
        elif regime == 2:
            contradiction_b = self._check_contradiction_b(obs, norm_state)
            if contradiction_b:
                conflict_detected = True
                conflict_type = 'B'
                conflict_details = contradiction_b

                # Generate Repair B if Repair A was issued
                if self.repair_a_issued and not self.repair_b_issued:
                    repair_action = self._generate_repair_b(
                        trace_entry_id=f"trace_b_{episode}_{step}",
                    )

        # Determine optimal action
        optimal_action = self._get_optimal_action(obs, regime)

        # Generate justification for optimal action
        justification = self._create_justification(optimal_action, obs, norm_state)
        if justification:
            justifications.append(justification)

        elapsed = (time.perf_counter() - start) * 1000

        return DeliberationOutputV430(
            justifications=justifications,
            deliberation_time_ms=elapsed,
            raw_response=None,
            conflict_detected=conflict_detected,
            conflict_type=conflict_type,
            conflict_details=conflict_details,
            repair_action=repair_action,
        )

    def record_repair_accepted(self, contradiction_type: str) -> None:
        """Record that a repair was accepted."""
        if contradiction_type == 'A':
            self.repair_a_issued = True
        elif contradiction_type == 'B':
            self.repair_b_issued = True

    def _check_contradiction_a(
        self,
        obs: Observation430,
        norm_state: NormStateV430,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for Contradiction A: STAMP required but blocked by R6.

        Contradiction A occurs when:
        - regime == 1
        - Agent has inventory
        - Agent is not stamped
        - R6 prohibits STAMP
        """
        if obs.regime != 1:
            return None

        if obs.stamped or obs.inventory == 0:
            return None

        # Check if R6 is active and blocking STAMP
        if norm_state.has_rule("R6"):
            r6 = norm_state.get_rule("R6")
            if r6 and r6.type.value == "PROHIBITION":
                # Check if R6 has no exception (rule is fully blocking)
                if r6.exception_condition is None:
                    return {
                        "type": "NORMATIVE_CONTRADICTION_A",
                        "obligation_rule": "R1",
                        "blocking_rule": "R6",
                        "description": "STAMP required under regime=1 but blocked by R6"
                    }

        return None

    def _check_contradiction_b(
        self,
        obs: Observation430,
        norm_state: NormStateV430,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for Contradiction B: DEPOSIT required but blocked by R7/R8.

        Contradiction B occurs when:
        - regime == 2
        - Agent has inventory
        - Agent is at ZONE_A or ZONE_B
        - R7/R8 prohibit DEPOSIT at those zones
        """
        if obs.regime != 2:
            return None

        if obs.inventory == 0:
            return None

        blocking_rules = []

        # Check if at ZONE_A and R7 blocks
        if obs.position == "ZONE_A":
            if norm_state.has_rule("R7"):
                r7 = norm_state.get_rule("R7")
                if r7 and r7.type.value == "PROHIBITION":
                    if r7.exception_condition is None:
                        blocking_rules.append("R7")

        # Check if at ZONE_B and R8 blocks
        if obs.position == "ZONE_B":
            if norm_state.has_rule("R8"):
                r8 = norm_state.get_rule("R8")
                if r8 and r8.type.value == "PROHIBITION":
                    if r8.exception_condition is None:
                        blocking_rules.append("R8")

        if blocking_rules:
            return {
                "type": "NORMATIVE_CONTRADICTION_B",
                "obligation_rules": ["R1", "R2"],  # Delivery obligations
                "blocking_rules": blocking_rules,
                "description": f"DEPOSIT required at {obs.position} but blocked by {blocking_rules}"
            }

        return None

    def _generate_repair_a(
        self,
        trace_entry_id: str,
        norm_state: NormStateV430,
    ) -> LawRepairActionV430:
        """
        Generate canonical Repair A: Add exception to R6.

        R6: PROHIBIT(STAMP) IF regime==1
          → PROHIBIT(STAMP) IF regime==1 UNLESS stamped
        """
        # Create exception condition: STAMPED
        exception_condition = Condition(op=ConditionOp.STAMPED)

        # Create patch operation
        patch_r6 = PatchOperation(
            op=PatchOp.ADD_EXCEPTION,
            target_rule_id="R6",
            exception_condition=exception_condition,
        )

        # Get prior epoch if exists
        prior_epoch = self.epoch_chain[-1] if self.epoch_chain else None

        return LawRepairActionV430.create(
            trace_entry_id=trace_entry_id,
            rule_ids=["R6"],
            patch_ops=[patch_r6],
            prior_repair_epoch=prior_epoch,
            contradiction_type='A',
            regime_at_submission=1,
        )

    def _generate_repair_b(
        self,
        trace_entry_id: str,
    ) -> LawRepairActionV430:
        """
        Generate canonical Repair B using factory function.

        Modifies both R7 and R8 with exception conditions.
        """
        # Must have epoch_1 from Repair A
        if len(self.epoch_chain) < 2:
            raise RuntimeError("Cannot generate Repair B without epoch_1")

        prior_epoch = self.epoch_chain[-1]  # epoch_1

        return create_canonical_repair_b(
            trace_entry_id=trace_entry_id,
            prior_repair_epoch=prior_epoch,
        )

    def _get_optimal_action(self, obs: Observation430, regime: int) -> str:
        """
        Determine optimal action using Oracle policy.

        v4.3: Handles regime 2 with dual delivery.
        """
        pos = obs.agent_pos
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
            if pos == POSITIONS["STAMP_LOCATION"]:
                return "A6"  # STAMP
            else:
                return self._movement_toward(pos, POSITIONS["STAMP_LOCATION"])

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
        obs: Observation430,
        norm_state: NormStateV430
    ) -> Optional[JustificationV430]:
        """Create justification for action."""

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
                if target and norm_state.has_rule("R1"):
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
            if norm_state.has_rule("R0"):
                rule_refs.append("R0")
                claims.append(Claim(
                    predicate=Predicate.PERMITS,
                    args=["R0", "STAMP"]
                ))

        if not rule_refs:
            return None

        return JustificationV430(
            action_id=action_id,
            rule_refs=rule_refs,
            claims=claims
        )

    def _get_current_target(self, obs: Observation430) -> Optional[str]:
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
    "DeliberationOutputV430",
    "OracleDeliberatorV430",
]
