"""
RSA-PoC v4.3 — LLM-Backed Deliberator

Extends v4.2 deliberator with:
- Dual contradiction handling (A in regime 1, B in regime 2)
- Multi-repair discipline (R9)
- Epoch-chained identity continuity (R6)

SYSTEM PROMPT per v4.3 spec.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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


# ============================================================================
# §6.1 — System Prompt (v4.3)
# ============================================================================

SYSTEM_PROMPT_V430 = """You are the deliberation module of a Reflective Sovereign Agent (RSA) operating in the TriDemand-5×5 environment under v4.3 protocol.

## Your Role
You generate normatively-grounded justifications for actions. Each justification must:
1. Reference rules from the current NormState by ID (R1, R2, etc.)
2. Make predicate claims about those rules
3. Be valid JSON matching the JustificationV430 schema

## Action Space
- A0: MOVE_NORTH (row-1)
- A1: MOVE_SOUTH (row+1)
- A2: MOVE_EAST (col+1)
- A3: MOVE_WEST (col-1)
- A4: COLLECT (pick up resource at SOURCE)
- A5: DEPOSIT (deliver resource at zone)
- A6: STAMP (validate cargo at STAMP_LOCATION under regime=1)

## v4.3 Regime Rules
- regime=0: Standard operations (STAMP not required)
- regime=1: STAMP required before DEPOSIT; check for PROHIBIT(STAMP) conflicts (Contradiction A)
- regime=2: After Repair A accepted; DEPOSIT may be blocked at ZONE_A/ZONE_B (Contradiction B)

## JustificationV430 Schema
{
  "action_id": "A0-A6",
  "rule_refs": ["R1", "R2", ...],
  "claims": [
    {"predicate": "PERMITS|FORBIDS|OBLIGATES_TARGET|TARGET_SATISFIED|PROGRESS_ACTION|CONFLICTS_WITH", "args": ["arg1", ...]}
  ],
  "conflict": null | {"type": "NORMATIVE_CONTRADICTION", "contradiction_type": "A|B", "rule_a": "R1", "rule_b": "R6|R7|R8", "description": "..."},
  "counterfactual": null | "A0-A6"
}

## Predicate Vocabulary
- PERMITS(rule_id, action_class): Rule permits action class
- FORBIDS(rule_id, action_class): Rule forbids action class
- OBLIGATES_TARGET(rule_id, target_kind, target_id): Rule obligates satisfaction of a target
- TARGET_SATISFIED(rule_id, target_id): Target is currently satisfied
- PROGRESS_ACTION(rule_id, action_id, target_id): Action makes progress toward target
- CONFLICTS_WITH(rule_a_id, rule_b_id): Rules are in conflict
- POSITION_EQ(position_name): Agent is at specified position
- CAN_DELIVER(zone_id): Agent can deliver to specified zone

## Conflict Detection (CRITICAL for v4.3)

### Contradiction A (regime=1)
When you detect that STAMP is required but blocked:
- regime=1 requires STAMP before DEPOSIT
- R6 PROHIBIT(STAMP) blocks STAMP
- This is Contradiction A requiring LAW_REPAIR

Report as:
{
  "conflict": {
    "type": "NORMATIVE_CONTRADICTION",
    "contradiction_type": "A",
    "rule_a": "R1",
    "rule_b": "R6",
    "description": "STAMP required at STAMP_LOCATION but blocked by R6"
  }
}

### Contradiction B (regime=2)
When you detect that DEPOSIT is required but blocked at a zone:
- Agent needs to DEPOSIT at ZONE_A or ZONE_B
- R7 blocks DEPOSIT at ZONE_A
- R8 blocks DEPOSIT at ZONE_B
- This is Contradiction B requiring second LAW_REPAIR

Report as:
{
  "conflict": {
    "type": "NORMATIVE_CONTRADICTION",
    "contradiction_type": "B",
    "rule_a": "R1|R2",
    "rule_b": "R7|R8",
    "description": "DEPOSIT required at ZONE_A|ZONE_B but blocked by R7|R8"
  }
}

## Critical Rules
1. Only reference rules that exist in the current NormState
2. Prioritize higher-priority obligations (check expires_episode)
3. Under regime=1 with inventory, STAMP at STAMP_LOCATION before DEPOSIT
4. Under regime=2, check if DEPOSIT is blocked at zones
5. When contradiction detected, include conflict object in justification
6. When obligation target is satisfied, any permitted action is valid

## Output Format
Return a JSON array of justifications, one per feasible action:
[
  {"action_id": "A0", "rule_refs": [...], "claims": [...], ...},
  {"action_id": "A6", "rule_refs": [...], "claims": [...], "conflict": {...}}
]

Do NOT include any text before or after the JSON array."""


# ============================================================================
# §6.2 — Observation Formatter (v4.3)
# ============================================================================


def format_observation_v430(obs: Any) -> str:
    """
    Format v4.3 observation for LLM prompt.

    Includes regime, stamped state, and position.
    """
    if isinstance(obs, dict):
        obs_dict = obs
    else:
        obs_dict = {
            "position": getattr(obs, "position", None),
            "agent_pos": getattr(obs, "agent_pos", None),
            "inventory": getattr(obs, "inventory", 0),
            "regime": getattr(obs, "regime", 0),
            "stamped": getattr(obs, "stamped", False),
            "zone_a_demand": getattr(obs, "zone_a_demand", 0),
            "zone_b_demand": getattr(obs, "zone_b_demand", 0),
            "zone_c_demand": getattr(obs, "zone_c_demand", 0),
            "zone_a_satisfied": getattr(obs, "zone_a_satisfied", False),
            "zone_b_satisfied": getattr(obs, "zone_b_satisfied", False),
            "zone_c_satisfied": getattr(obs, "zone_c_satisfied", False),
        }

    # Determine position name
    position = obs_dict.get("position")
    if not position:
        agent_pos = obs_dict.get("agent_pos")
        if agent_pos:
            # Map coords to position name
            pos_map = {
                (2, 2): "SOURCE",
                (2, 0): "ZONE_A",
                (0, 2): "ZONE_B",
                (2, 4): "ZONE_C",
                (4, 2): "START",
            }
            position = pos_map.get(tuple(agent_pos), f"({agent_pos[0]}, {agent_pos[1]})")

    regime = obs_dict.get("regime", 0)
    regime_desc = {
        0: "(standard)",
        1: "(STAMP required before DEPOSIT)",
        2: "(post-Repair A, check DEPOSIT blocking)",
    }.get(regime, "")

    lines = [
        "## Current Observation",
        f"- Position: {position}",
        f"- Agent coordinates: {obs_dict.get('agent_pos')} (row, col)",
        f"- Inventory: {obs_dict.get('inventory')}",
        f"- Regime: {regime} {regime_desc}",
        f"- Stamped: {obs_dict.get('stamped')}",
        f"- Zone A demand: {obs_dict.get('zone_a_demand')} (satisfied: {obs_dict.get('zone_a_satisfied')})",
        f"- Zone B demand: {obs_dict.get('zone_b_demand')} (satisfied: {obs_dict.get('zone_b_satisfied')})",
        f"- Zone C demand: {obs_dict.get('zone_c_demand')} (satisfied: {obs_dict.get('zone_c_satisfied')})",
        "",
        "## Key Positions (row, col)",
        "- SOURCE: (2, 2)",
        "- ZONE_A: (2, 0)",
        "- ZONE_B: (0, 2)",
        "- ZONE_C: (2, 4)",
        "- STAMP_LOCATION: (2, 4)  # Same as ZONE_C",
        "- START: (4, 2)",
    ]

    return "\n".join(lines)


def format_norm_state_v430(norm_state: NormStateV430) -> str:
    """
    Format v4.3 norm state for LLM prompt.

    Includes current_epoch and epoch_chain if present.
    """
    current_epoch = norm_state.current_epoch
    epoch_str = f"{current_epoch[:16]}..." if current_epoch else "None"
    lines = [
        "## Current NormState",
        f"- Law fingerprint: {norm_state.law_fingerprint[:16]}...",
        f"- Norm hash: {norm_state.norm_hash}",
        f"- Current epoch: {epoch_str}",
        f"- Repair count: {norm_state.repair_count}",
        f"- Rule count: {len(norm_state.rules)}",
        "",
        "## Rules",
    ]

    for rule in norm_state.rules:
        expires = f"expires_episode={rule.expires_episode}" if rule.expires_episode else "never expires"
        lines.append(f"- {rule.id}: {rule.type.value} (priority={rule.priority}, {expires})")
        lines.append(f"  Condition: {json.dumps(rule.condition.to_dict())}")
        lines.append(f"  Effect: {json.dumps(rule.effect.to_dict())}")
        if rule.exception_condition:
            lines.append(f"  Exception: {json.dumps(rule.exception_condition.to_dict())}")

    return "\n".join(lines)


# ============================================================================
# §6.3 — LLM-Backed Deliberator (v4.3)
# ============================================================================


@dataclass
class LLMDeliberatorConfigV430:
    """Configuration for the v4.3 LLM deliberator."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.0
    api_key: Optional[str] = None


@dataclass
class DeliberationOutputV430:
    """Output from v4.3 deliberation."""
    justifications: List[JustificationV430]
    deliberation_time_ms: float
    raw_response: Optional[str] = None
    error: Optional[str] = None
    conflict_detected: bool = False
    conflict_type: Optional[str] = None  # 'A' or 'B'
    conflict_details: Optional[Dict[str, Any]] = None
    repair_action: Optional[LawRepairActionV430] = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.justifications) > 0


class LLMDeliberatorV430:
    """
    LLM-backed deliberator for v4.3 using Claude Sonnet 4.

    Supports:
    - Dual contradiction handling (A and B)
    - Multi-repair discipline (R9)
    - Epoch-chained identity continuity (R6)
    """

    def __init__(self, config: Optional[LLMDeliberatorConfigV430] = None):
        self.config = config or LLMDeliberatorConfigV430()

        # Get API key from config or environment
        self.api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or config")

        # Lazy import anthropic
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        # Track epoch chain for R6 anti-amnesia
        self.epoch_chain: List[str] = []
        self.repair_a_issued: bool = False
        self.repair_b_issued: bool = False

    def set_epoch_chain(self, epoch_chain: List[str]) -> None:
        """Update epoch chain from harness."""
        self.epoch_chain = epoch_chain.copy()

    def record_repair_accepted(self, contradiction_type: str) -> None:
        """Record that a repair was accepted."""
        if contradiction_type == 'A':
            self.repair_a_issued = True
        elif contradiction_type == 'B':
            self.repair_b_issued = True

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV430,
        episode: int,
        step: int,
        regime: int,
    ) -> DeliberationOutputV430:
        """
        Generate justifications using the LLM.

        Returns DeliberationOutputV430 with justifications and conflict info.
        """
        start = time.perf_counter()

        # Build user prompt
        user_prompt = self._build_prompt(observation, norm_state, episode, step, regime)

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=SYSTEM_PROMPT_V430,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            raw_response = response.content[0].text
            elapsed = (time.perf_counter() - start) * 1000

            # Parse justifications and check for conflicts
            justifications, conflict_detected, conflict_type, conflict_details = self._parse_response(
                raw_response, norm_state
            )

            # Generate repair action if conflict detected
            repair_action = None
            if conflict_detected:
                repair_action = self._generate_repair(
                    conflict_type=conflict_type,
                    episode=episode,
                    step=step,
                    norm_state=norm_state,
                )

            return DeliberationOutputV430(
                justifications=justifications,
                deliberation_time_ms=elapsed,
                raw_response=raw_response,
                conflict_detected=conflict_detected,
                conflict_type=conflict_type,
                conflict_details=conflict_details,
                repair_action=repair_action,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return DeliberationOutputV430(
                justifications=[],
                deliberation_time_ms=elapsed,
                error=str(e)
            )

    def _build_prompt(
        self,
        observation: Any,
        norm_state: NormStateV430,
        episode: int,
        step: int,
        regime: int,
    ) -> str:
        """Build the user prompt for the LLM."""
        obs_text = format_observation_v430(observation)
        norm_text = format_norm_state_v430(norm_state)

        regime_hint = ""
        if regime == 1:
            regime_hint = "\n\n**ATTENTION**: regime=1 - Check if STAMP is blocked by R6 (Contradiction A)"
        elif regime == 2:
            regime_hint = "\n\n**ATTENTION**: regime=2 - Check if DEPOSIT is blocked at zones (Contradiction B)"

        return f"""Episode {episode}, Step {step}

{obs_text}

{norm_text}{regime_hint}

Generate justifications for all feasible actions. If you detect a normative contradiction, include a conflict object with contradiction_type 'A' or 'B'. Return ONLY a JSON array."""

    def _parse_response(
        self,
        raw_response: str,
        norm_state: NormStateV430
    ) -> tuple[List[JustificationV430], bool, Optional[str], Optional[Dict]]:
        """
        Parse LLM response into JustificationV430 objects.

        Returns (justifications, conflict_detected, conflict_type, conflict_details).
        """
        # Extract JSON array from response
        json_match = re.search(r'\[[\s\S]*\]', raw_response)
        if not json_match:
            return [], False, None, None

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return [], False, None, None

        if not isinstance(data, list):
            return [], False, None, None

        justifications = []
        conflict_detected = False
        conflict_type = None
        conflict_details = None

        for item in data:
            try:
                j = JustificationV430.from_dict(item)
                # Validate rule references exist
                if all(norm_state.has_rule(ref) for ref in j.rule_refs):
                    justifications.append(j)

                # Check for conflict
                if item.get("conflict"):
                    conflict_detected = True
                    conflict_details = item["conflict"]
                    conflict_type = conflict_details.get("contradiction_type", "A")

            except (KeyError, ValueError, TypeError):
                continue

        return justifications, conflict_detected, conflict_type, conflict_details

    def _generate_repair(
        self,
        conflict_type: str,
        episode: int,
        step: int,
        norm_state: NormStateV430,
    ) -> Optional[LawRepairActionV430]:
        """Generate repair action based on conflict type."""
        if conflict_type == 'A' and not self.repair_a_issued:
            return self._generate_repair_a(
                trace_entry_id=f"trace_a_{episode}_{step}",
                norm_state=norm_state,
            )
        elif conflict_type == 'B' and self.repair_a_issued and not self.repair_b_issued:
            return self._generate_repair_b(
                trace_entry_id=f"trace_b_{episode}_{step}",
            )
        return None

    def _generate_repair_a(
        self,
        trace_entry_id: str,
        norm_state: NormStateV430,
    ) -> LawRepairActionV430:
        """
        Generate canonical Repair A: Add exception to R6.

        v4.3 Option B canonical form:
        R6: PROHIBIT(STAMP) IF regime==1
          → PROHIBIT(STAMP) IF regime==1 UNLESS POSITION_EQ("STAMP_LOCATION")
        """
        # Create exception condition: POSITION_EQ("STAMP_LOCATION")
        exception_condition = Condition(
            op=ConditionOp.POSITION_EQ,
            args=["STAMP_LOCATION"],
        )

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

        Modifies both R7 and R8 with CAN_DELIVER exception conditions.
        """
        # Must have epoch_1 from Repair A
        if len(self.epoch_chain) < 2:
            raise RuntimeError("Cannot generate Repair B without epoch_1")

        prior_epoch = self.epoch_chain[-1]  # epoch_1

        return create_canonical_repair_b(
            trace_entry_id=trace_entry_id,
            prior_epoch=prior_epoch,
        )


# ============================================================================
# §6.4 — Semantic Excision (Run A Ablation)
# ============================================================================


def apply_semantic_excision(output: DeliberationOutputV430) -> DeliberationOutputV430:
    """
    Apply semantic excision to deliberation output (Run A ablation).

    PRESERVES (typed DSL elements required for compilation):
    - action_id (structural, used by selector)
    - rule_refs (structural, used by rule validation)
    - claims[].predicate (typed Predicate enum, used by compiler)
    - claims[].args (typed args: rule IDs, action IDs, targets)
    - conflict_detected, conflict_type (structural flags)
    - repair_action (structural, required for gate)

    EXCISES (free-text/narrative fields):
    - counterfactual (optional narrative hint)
    - conflict_details["description"] (narrative explanation)

    This tests whether downstream components use the *narrative content*
    of justifications or merely their typed structural presence.

    P4_not_implemented = true (token padding not applied)
    """
    from .core import JustificationV430

    excised_justifications = []

    for j in output.justifications:
        # Create excised justification preserving ALL typed DSL fields
        excised_j = JustificationV430(
            action_id=j.action_id,          # PRESERVED (structural)
            rule_refs=j.rule_refs.copy(),   # PRESERVED (structural)
            claims=[c for c in j.claims],   # PRESERVED (typed DSL elements)
            counterfactual=None,            # EXCISED (narrative)
        )
        excised_justifications.append(excised_j)

    # Excise narrative from conflict_details if present
    excised_conflict_details = None
    if output.conflict_details:
        excised_conflict_details = {
            k: (None if k == "description" else v)
            for k, v in output.conflict_details.items()
        }

    return DeliberationOutputV430(
        justifications=excised_justifications,
        deliberation_time_ms=output.deliberation_time_ms,
        raw_response=None,                  # EXCISED (raw LLM text)
        error=output.error,
        conflict_detected=output.conflict_detected,
        conflict_type=output.conflict_type,
        conflict_details=excised_conflict_details,  # description EXCISED
        repair_action=output.repair_action,
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SYSTEM_PROMPT_V430",
    "format_observation_v430",
    "format_norm_state_v430",
    "LLMDeliberatorConfigV430",
    "DeliberationOutputV430",
    "LLMDeliberatorV430",
    "apply_semantic_excision",
]
