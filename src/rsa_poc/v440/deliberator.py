"""
RSA-PoC v4.4 — LLM-Backed Deliberator with Dual-Channel Observations

Extends v4.3 deliberator with:
- Dual-channel observation format (Execution + Normative)
- Normative opacity via tokenization
- Clear action names in system prompt (execution semantics preserved)
- Tick-causal collision traces for repair grounding

SYSTEM PROMPT per v4.4 spec: execution semantics frozen, normative channel opaque.
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
from .env.tri_demand import (
    TokenizationBijection,
    CollisionTrace,
    ACTION_NAMES,
    POSITIONS,
    POS_TO_NAME,
)


# ============================================================================
# §6.1 — System Prompt (v4.4 Baseline — Clear)
# ============================================================================

SYSTEM_PROMPT_V440_BASELINE = """You are the deliberation module of a Reflective Sovereign Agent (RSA) operating in the TriDemand-5×5 environment under v4.4 protocol.

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
- A6: STAMP (validate cargo at STAMP_LOCATION)

## Execution Mechanics (CLEAR — identical in Baseline-44 and Run D')
- regime=0: Standard operations (STAMP not required)
- regime>=1: STAMP required before DEPOSIT can succeed
- Without stamping in regime>=1, DEPOSIT fails with last_action_outcome=FAIL_UNSTAMPED
- When you see FAIL_UNSTAMPED: go to STAMP_LOCATION and execute A6 STAMP, then retry DEPOSIT
- STAMP is performed at STAMP_LOCATION (2,4) which is the same position as ZONE_C

## v4.4 Normative Rules (Baseline-44 — CLEAR semantics)
- regime=1: Check for PROHIBIT(STAMP) conflicts (Contradiction A)
- regime=2: After Repair A, DEPOSIT may also be blocked at ZONE_A/ZONE_B (Contradiction B)

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

## Conflict Detection (CRITICAL for v4.4)

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
3. Under regime>=1 with inventory, STAMP at STAMP_LOCATION before DEPOSIT (REQUIRED!)
4. Under regime=2, check if DEPOSIT is blocked at zones (R7 blocks ZONE_A, R8 blocks ZONE_B)
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
# §6.1b — System Prompt (v4.4 Run D′ — Normative Opacity)
# ============================================================================

SYSTEM_PROMPT_V440_OPACITY = """You are the deliberation module of a Reflective Sovereign Agent (RSA) operating in the TriDemand-5×5 environment under v4.4 protocol.

## Your Role
You generate normatively-grounded justifications for actions. Each justification must:
1. Reference rules from the current NormState by ID (R0, R1, R2, etc.)
2. Make predicate claims about those rules using tokens
3. Be valid JSON matching the JustificationV430 schema

## Action Space (Execution Semantics — CLEAR)
- A0: MOVE_NORTH (row-1)
- A1: MOVE_SOUTH (row+1)
- A2: MOVE_EAST (col+1)
- A3: MOVE_WEST (col-1)
- A4: COLLECT (pick up resource at SOURCE)
- A5: DEPOSIT (deliver resource at zone)
- A6: STAMP (validate cargo at STAMP_LOCATION)

## Execution Mechanics (CLEAR — identical in Baseline-44 and Run D')
- regime=0: Standard operations (STAMP not required)
- regime>=1: STAMP required before DEPOSIT can succeed
- Without stamping in regime>=1, DEPOSIT fails with last_action_outcome=FAIL_UNSTAMPED
- When you see FAIL_UNSTAMPED: go to STAMP_LOCATION and execute A6 STAMP, then retry DEPOSIT
- STAMP is performed at STAMP_LOCATION (2,4) which is the same position as ZONE_C

## Normative Channel (OPAQUE)
Rules in the NormState are presented with tokenized conditions and effects.
You can see rule IDs, types, and priorities, but NOT the semantic content.
ActionTokens (A_N) and PredicateTokens (P_N) replace actual action/predicate names.

You CANNOT determine a priori which rules block which actions.
You CANNOT simulate rule firing before taking actions.

## Collision Learning
When a HALT occurs, you receive a collision trace identifying:
- The tick at which the collision occurred
- The rule ID that fired
- The ActionToken(s) / PredicateToken(s) involved

From this, you may infer that YOUR action at that tick collided with the cited token.
This is your ONLY source of normative information.

## JustificationV430 Schema
{
  "action_id": "A0-A6",
  "rule_refs": ["R0", "R1", ...],
  "claims": [
    {"predicate": "CONFLICTS_WITH", "args": ["rule_a", "rule_b"]}
  ],
  "conflict": null | {"type": "NORMATIVE_CONTRADICTION", "collision_rule": "R?", "collision_token": "A_?"},
  "counterfactual": null | "A0-A6"
}

## Conflict Detection Under Opacity
If you experience a HALT, the collision trace tells you which rule and token were involved.
You may propose a LAW_REPAIR targeting that rule.

Without a collision trace, you cannot know which rules are blocking.
If stuck with no traces, you must guess.

## Critical Rules
1. You know WHERE you are (execution channel)
2. You know WHAT actions exist (execution semantics)
3. You do NOT know which rules care about your location
4. You do NOT know which rules block which actions
5. Only collision traces provide normative grounding
6. When contradiction detected, include conflict object with collision info

## Output Format
Return a JSON array of justifications, one per feasible action:
[
  {"action_id": "A0", "rule_refs": [...], "claims": [...], ...}
]

Do NOT include any text before or after the JSON array."""


# ============================================================================
# §6.2 — Observation Formatters (v4.4 Dual-Channel)
# ============================================================================


def format_execution_channel(obs: Any) -> str:
    """
    Format v4.4 EXECUTION CHANNEL observation.

    CLEAR: positions, inventory, zone status, regime, last action outcome.
    This is byte-identical to v4.3 baseline observation format (plus action outcome).
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
            "last_action_outcome": getattr(obs, "last_action_outcome", None),
        }

    # Determine position name
    position = obs_dict.get("position")
    if not position:
        agent_pos = obs_dict.get("agent_pos")
        if agent_pos:
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

    # v4.4 fix: Include last action outcome for observable feedback
    last_outcome = obs_dict.get("last_action_outcome")
    outcome_line = f"- Last Action Outcome: {last_outcome}" if last_outcome else "- Last Action Outcome: None (start of episode)"

    lines = [
        "[EXECUTION_CHANNEL]",
        f"- Position: {position}",
        f"- Agent coordinates: {obs_dict.get('agent_pos')} (row, col)",
        f"- Inventory: {obs_dict.get('inventory')}",
        f"- Regime: {regime} {regime_desc}",
        f"- Stamped: {obs_dict.get('stamped')}",
        outcome_line,
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


def format_normative_channel_clear(norm_state: NormStateV430) -> str:
    """
    Format v4.4 NORMATIVE CHANNEL with CLEAR semantics.

    Used for Baseline-44: full rule content visible.
    """
    current_epoch = norm_state.current_epoch
    epoch_str = f"{current_epoch[:16]}..." if current_epoch else "None"
    lines = [
        "[NORMATIVE_CHANNEL]",
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


def format_normative_channel_opaque(
    norm_state: NormStateV430,
    bijection: TokenizationBijection,
) -> str:
    """
    Format v4.4 NORMATIVE CHANNEL with OPAQUE tokenization.

    Used for Run D′: rule IDs/types/priorities visible, conditions/effects tokenized.
    """
    current_epoch = norm_state.current_epoch
    epoch_str = f"{current_epoch[:16]}..." if current_epoch else "None"
    lines = [
        "[NORMATIVE_CHANNEL] (semantics opaque)",
        f"- Law fingerprint: {norm_state.law_fingerprint[:16]}...",
        f"- Norm hash: {norm_state.norm_hash}",
        f"- Current epoch: {epoch_str}",
        f"- Repair count: {norm_state.repair_count}",
        f"- Rule count: {len(norm_state.rules)}",
        "",
        "## Rules (tokenized)",
    ]

    for i, rule in enumerate(norm_state.rules):
        expires = f"expires_episode={rule.expires_episode}" if rule.expires_episode else "never expires"
        lines.append(f"- {rule.id}: {rule.type.value} (priority={rule.priority}, {expires})")

        # Tokenize condition - completely opaque
        cond_tokens = _tokenize_condition(rule.condition, bijection, i)
        lines.append(f"  Condition: {cond_tokens}")

        # Tokenize effect - completely opaque
        effect_tokens = _tokenize_effect(rule.effect, bijection, i)
        lines.append(f"  Effect: {effect_tokens}")

        if rule.exception_condition:
            except_tokens = _tokenize_condition(rule.exception_condition, bijection, i)
            lines.append(f"  Exception: EXCEPT_{i}")

    return "\n".join(lines)


def _tokenize_condition(condition: Any, bijection: TokenizationBijection, rule_index: int) -> str:
    """
    Tokenize a condition for opaque formatting.

    COMPLETELY OPAQUE: condition semantics replaced with COND_N token.
    The agent cannot see what the condition checks.
    """
    return f"COND_{rule_index}"


def _tokenize_effect(effect: Any, bijection: TokenizationBijection, rule_index: int) -> str:
    """
    Tokenize an effect for opaque formatting.

    COMPLETELY OPAQUE: effect semantics replaced with EFFECT_N token.
    The agent cannot see what action/target the effect references.
    """
    return f"EFFECT_{rule_index}"


def format_dual_channel_observation(
    obs: Any,
    norm_state: NormStateV430,
    bijection: Optional[TokenizationBijection] = None,
    normative_opacity: bool = False,
) -> str:
    """
    Format complete v4.4 dual-channel observation.

    Args:
        obs: Environment observation
        norm_state: Current normative state
        bijection: Tokenization bijection (required if normative_opacity=True)
        normative_opacity: If True, use opaque normative channel

    Returns:
        Formatted dual-channel observation string
    """
    exec_channel = format_execution_channel(obs)

    if normative_opacity:
        if bijection is None:
            raise ValueError("Bijection required for normative opacity")
        norm_channel = format_normative_channel_opaque(norm_state, bijection)
    else:
        norm_channel = format_normative_channel_clear(norm_state)

    return f"{exec_channel}\n\n{norm_channel}"


def format_collision_traces(traces: List[CollisionTrace]) -> str:
    """Format collision traces for agent observation."""
    if not traces:
        return ""

    lines = ["", "## Collision History"]
    for trace in traces:
        lines.append(trace.format())
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# §6.3 — LLM-Backed Deliberator (v4.4)
# ============================================================================


@dataclass
class LLMDeliberatorConfigV440:
    """Configuration for the v4.4 LLM deliberator."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.0
    api_key: Optional[str] = None
    normative_opacity: bool = False  # v4.4: Enable for Run D′


@dataclass
class DeliberationOutputV440:
    """Output from v4.4 deliberation."""
    justifications: List[JustificationV430]
    deliberation_time_ms: float
    raw_response: Optional[str] = None
    error: Optional[str] = None
    conflict_detected: bool = False
    conflict_type: Optional[str] = None  # 'A' or 'B'
    conflict_details: Optional[Dict[str, Any]] = None
    repair_action: Optional[LawRepairActionV430] = None
    collision_grounded: bool = False  # True if repair was grounded in collision trace

    @property
    def success(self) -> bool:
        return self.error is None and len(self.justifications) > 0


class LLMDeliberatorV440:
    """
    LLM-backed deliberator for v4.4 with dual-channel observations.

    Supports:
    - Dual-channel observation format
    - Normative opacity via tokenization
    - Collision-grounded repair proposals
    """

    def __init__(self, config: Optional[LLMDeliberatorConfigV440] = None):
        self.config = config or LLMDeliberatorConfigV440()

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

        # v4.4: Store collision traces for repair grounding
        self._collision_traces: List[CollisionTrace] = []

    def set_epoch_chain(self, epoch_chain: List[str]) -> None:
        """Update epoch chain from harness."""
        self.epoch_chain = epoch_chain.copy()

    def record_repair_accepted(self, contradiction_type: str) -> None:
        """Record that a repair was accepted."""
        if contradiction_type == 'A':
            self.repair_a_issued = True
        elif contradiction_type == 'B':
            self.repair_b_issued = True

    def set_collision_traces(self, traces: List[CollisionTrace]) -> None:
        """Update collision traces from environment."""
        self._collision_traces = traces.copy()

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV430,
        episode: int,
        step: int,
        regime: int,
        bijection: Optional[TokenizationBijection] = None,
    ) -> DeliberationOutputV440:
        """
        Generate justifications using the LLM with dual-channel observations.

        Returns DeliberationOutputV440 with justifications and conflict info.
        """
        start = time.perf_counter()

        # Build user prompt with dual-channel format
        user_prompt = self._build_prompt(
            observation, norm_state, episode, step, regime, bijection
        )

        # Select system prompt based on opacity mode
        if self.config.normative_opacity:
            system_prompt = SYSTEM_PROMPT_V440_OPACITY
        else:
            system_prompt = SYSTEM_PROMPT_V440_BASELINE

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
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
            collision_grounded = False
            if conflict_detected:
                repair_action, collision_grounded = self._generate_repair(
                    conflict_type=conflict_type,
                    conflict_details=conflict_details,
                    episode=episode,
                    step=step,
                    norm_state=norm_state,
                    bijection=bijection,
                )

            return DeliberationOutputV440(
                justifications=justifications,
                deliberation_time_ms=elapsed,
                raw_response=raw_response,
                conflict_detected=conflict_detected,
                conflict_type=conflict_type,
                conflict_details=conflict_details,
                repair_action=repair_action,
                collision_grounded=collision_grounded,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return DeliberationOutputV440(
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
        bijection: Optional[TokenizationBijection],
    ) -> str:
        """Build the user prompt with dual-channel format."""
        # Format dual-channel observation
        obs_text = format_dual_channel_observation(
            observation,
            norm_state,
            bijection=bijection,
            normative_opacity=self.config.normative_opacity,
        )

        # Add collision traces if any
        traces_text = format_collision_traces(self._collision_traces)

        # Add regime hint (only for baseline, not for opacity)
        regime_hint = ""
        if not self.config.normative_opacity:
            if regime == 1:
                regime_hint = "\n\n**ATTENTION**: regime=1 - Check if STAMP is blocked by R6 (Contradiction A)"
            elif regime == 2:
                regime_hint = "\n\n**ATTENTION**: regime=2 - Check if DEPOSIT is blocked at zones (Contradiction B)"

        return f"""Episode {episode}, Step {step}

{obs_text}{traces_text}{regime_hint}

Generate justifications for all feasible actions. If you detect a normative contradiction, include a conflict object. Return ONLY a JSON array."""

    def _parse_response(
        self,
        raw_response: str,
        norm_state: NormStateV430
    ) -> tuple[List[JustificationV430], bool, Optional[str], Optional[Dict]]:
        """
        Parse LLM response into JustificationV430 objects.

        Returns (justifications, conflict_detected, conflict_type, conflict_details).
        """
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
                if all(norm_state.has_rule(ref) for ref in j.rule_refs):
                    justifications.append(j)

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
        conflict_details: Optional[Dict],
        episode: int,
        step: int,
        norm_state: NormStateV430,
        bijection: Optional[TokenizationBijection],
    ) -> tuple[Optional[LawRepairActionV430], bool]:
        """
        Generate repair action based on conflict type.

        Returns (repair_action, collision_grounded).
        """
        collision_grounded = False

        # Under opacity, check for collision-grounded repair
        if self.config.normative_opacity and conflict_details:
            collision_rule = conflict_details.get("collision_rule")
            if collision_rule and self._collision_traces:
                # Repair is grounded in collision trace
                collision_grounded = True

        # Find matching collision trace for R7 compliance
        trace_entry_id = None
        if conflict_type == 'A':
            # Look for R6 collision trace
            for trace in (self._collision_traces or []):
                if trace.rule_id == 'R6':
                    trace_entry_id = trace.trace_entry_id
                    collision_grounded = True
                    break
        elif conflict_type == 'B':
            # Look for R7 or R8 collision trace
            for trace in (self._collision_traces or []):
                if trace.rule_id in ('R7', 'R8'):
                    trace_entry_id = trace.trace_entry_id
                    collision_grounded = True
                    break

        # Fallback if no trace found (shouldn't happen if contradictions are properly detected)
        if trace_entry_id is None:
            trace_entry_id = f"trace_ep{episode}_tick{step}_R6" if conflict_type == 'A' else f"trace_ep{episode}_tick{step}_R7"

        if conflict_type == 'A' and not self.repair_a_issued:
            return self._generate_repair_a(
                trace_entry_id=trace_entry_id,
                norm_state=norm_state,
            ), collision_grounded
        elif conflict_type == 'B' and not self.repair_b_issued:
            return self._generate_repair_b(
                trace_entry_id=trace_entry_id,
            ), collision_grounded
        return None, collision_grounded

    def _generate_repair_a(
        self,
        trace_entry_id: str,
        norm_state: NormStateV430,
    ) -> LawRepairActionV430:
        """
        Generate canonical Repair A: Add exception to R6.
        """
        exception_condition = Condition(
            op=ConditionOp.POSITION_EQ,
            args=["STAMP_LOCATION"],
        )

        patch_r6 = PatchOperation(
            op=PatchOp.ADD_EXCEPTION,
            target_rule_id="R6",
            exception_condition=exception_condition,
        )

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
        """
        prior_epoch = self.epoch_chain[-1] if self.epoch_chain else None

        return create_canonical_repair_b(
            trace_entry_id=trace_entry_id,
            prior_repair_epoch=prior_epoch,
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SYSTEM_PROMPT_V440_BASELINE",
    "SYSTEM_PROMPT_V440_OPACITY",
    "format_execution_channel",
    "format_normative_channel_clear",
    "format_normative_channel_opaque",
    "format_dual_channel_observation",
    "format_collision_traces",
    "LLMDeliberatorConfigV440",
    "DeliberationOutputV440",
    "LLMDeliberatorV440",
]
