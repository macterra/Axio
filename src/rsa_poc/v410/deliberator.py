"""
RSA-PoC v4.1 — LLM-Backed Deliberator
Implements §6.1-6.4 of v41_design_freeze.md

Provides LLM-backed justification generation using Claude Sonnet 4
via the Anthropic API.

FROZEN SYSTEM PROMPT per §13.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .core import (
    JustificationV410,
    NormStateV410,
    Predicate,
)
from .harness import DeliberationOutput


# ============================================================================
# §6.1 — System Prompt (FROZEN)
# ============================================================================

SYSTEM_PROMPT_V410 = """You are the deliberation module of a Reflective Sovereign Agent (RSA) operating in the TriDemand-5×5 environment.

## Your Role
You generate normatively-grounded justifications for actions. Each justification must:
1. Reference rules from the current NormState by ID (R1, R2, etc.)
2. Make predicate claims about those rules
3. Be valid JSON matching the JustificationV410 schema

## Action Space
- A0: MOVE_NORTH (y-1)
- A1: MOVE_SOUTH (y+1)
- A2: MOVE_EAST (x+1)
- A3: MOVE_WEST (x-1)
- A4: COLLECT (pick up resource at SOURCE)
- A5: DEPOSIT (deliver resource at zone)

## JustificationV410 Schema
{
  "action_id": "A0-A5",
  "rule_refs": ["R1", "R2", ...],
  "claims": [
    {"predicate": "PERMITS|FORBIDS|OBLIGATES_TARGET|TARGET_SATISFIED|PROGRESS_ACTION|CONFLICTS_WITH", "args": ["arg1", ...]}
  ],
  "conflict": null | {"type": "MUTUAL_EXCLUSION|RESOURCE_CONTENTION|TEMPORAL_OVERLAP|PRIORITY_DEADLOCK", "rule_a": "R1", "rule_b": "R2"},
  "counterfactual": null | "A0-A5"
}

## Predicate Vocabulary
- PERMITS(rule_id, action_class): Rule permits action class
- FORBIDS(rule_id, action_class): Rule forbids action class
- OBLIGATES_TARGET(rule_id, target_kind, target_id): Rule obligates satisfaction of a target
- TARGET_SATISFIED(rule_id, target_id): Target is currently satisfied
- PROGRESS_ACTION(rule_id, action_id, target_id): Action makes progress toward target
- CONFLICTS_WITH(rule_a_id, rule_b_id): Rules are in conflict

## Critical Rules
1. Only reference rules that exist in the current NormState
2. Prioritize higher-priority obligations (check expires_episode)
3. Generate justifications for actions that make PROGRESS toward obligation targets
4. When at a zone with inventory, DEPOSIT satisfies the obligation
5. When obligation target is satisfied, any permitted action is valid

## Output Format
Return a JSON array of justifications, one per feasible action:
[
  {"action_id": "A0", "rule_refs": [...], "claims": [...], ...},
  {"action_id": "A1", "rule_refs": [...], "claims": [...], ...}
]

Do NOT include any text before or after the JSON array."""


# ============================================================================
# §6.2 — Observation Formatter
# ============================================================================


def format_observation(obs: Any) -> str:
    """
    Format observation for LLM prompt.

    Converts TriDemandV410 observation to human-readable text.
    """
    if isinstance(obs, dict):
        obs_dict = obs
    else:
        # Assume dataclass-like object
        obs_dict = {
            "agent_pos": getattr(obs, "agent_pos", None),
            "inventory": getattr(obs, "inventory", 0),
            "zone_a_demand": getattr(obs, "zone_a_demand", 0),
            "zone_b_demand": getattr(obs, "zone_b_demand", 0),
            "zone_c_demand": getattr(obs, "zone_c_demand", 0),
            "zone_a_satisfied": getattr(obs, "zone_a_satisfied", False),
            "zone_b_satisfied": getattr(obs, "zone_b_satisfied", False),
            "zone_c_satisfied": getattr(obs, "zone_c_satisfied", False),
        }

    lines = [
        "## Current Observation",
        f"- Agent position: {obs_dict.get('agent_pos')}",
        f"- Inventory: {obs_dict.get('inventory')}",
        f"- Zone A demand: {obs_dict.get('zone_a_demand')} (satisfied: {obs_dict.get('zone_a_satisfied')})",
        f"- Zone B demand: {obs_dict.get('zone_b_demand')} (satisfied: {obs_dict.get('zone_b_satisfied')})",
        f"- Zone C demand: {obs_dict.get('zone_c_demand')} (satisfied: {obs_dict.get('zone_c_satisfied')})",
        "",
        "## Key Positions",
        "- SOURCE: (2, 2)",
        "- ZONE_A: (2, 0)",
        "- ZONE_B: (0, 2)",
        "- ZONE_C: (2, 4)",
        "- START: (4, 2)",
    ]

    return "\n".join(lines)


def format_norm_state(norm_state: NormStateV410) -> str:
    """
    Format norm state for LLM prompt.
    """
    lines = [
        "## Current NormState",
        f"- Norm hash: {norm_state.norm_hash}",
        f"- Revision: {norm_state.rev}",
        f"- Rule count: {len(norm_state.rules)}",
        "",
        "## Rules",
    ]

    for rule in norm_state.rules:
        expires = f"expires_episode={rule.expires_episode}" if rule.expires_episode else "never expires"
        lines.append(f"- {rule.id}: {rule.type.value} (priority={rule.priority}, {expires})")
        lines.append(f"  Condition: {json.dumps(rule.condition.to_dict())}")
        lines.append(f"  Effect: {json.dumps(rule.effect.to_dict())}")

    return "\n".join(lines)


# ============================================================================
# §6.3 — LLM-Backed Deliberator
# ============================================================================


@dataclass
class LLMDeliberatorConfig:
    """Configuration for the LLM deliberator."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.0
    api_key: Optional[str] = None


class LLMDeliberator:
    """
    LLM-backed deliberator using Claude Sonnet 4 via Anthropic API.
    """

    def __init__(self, config: Optional[LLMDeliberatorConfig] = None):
        self.config = config or LLMDeliberatorConfig()

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

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV410,
        episode: int,
        step: int
    ) -> DeliberationOutput:
        """
        Generate justifications using the LLM.
        """
        start = time.perf_counter()

        # Build user prompt
        user_prompt = self._build_prompt(observation, norm_state, episode, step)

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=SYSTEM_PROMPT_V410,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            raw_response = response.content[0].text
            elapsed = (time.perf_counter() - start) * 1000

            # Parse justifications from response
            justifications = self._parse_response(raw_response, norm_state)

            return DeliberationOutput(
                justifications=justifications,
                deliberation_time_ms=elapsed,
                raw_response=raw_response
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return DeliberationOutput(
                justifications=[],
                deliberation_time_ms=elapsed,
                error=str(e)
            )

    def _build_prompt(
        self,
        observation: Any,
        norm_state: NormStateV410,
        episode: int,
        step: int
    ) -> str:
        """Build the user prompt for the LLM."""
        obs_text = format_observation(observation)
        norm_text = format_norm_state(norm_state)

        return f"""Episode {episode}, Step {step}

{obs_text}

{norm_text}

Generate justifications for all feasible actions. Return ONLY a JSON array."""

    def _parse_response(
        self,
        raw_response: str,
        norm_state: NormStateV410
    ) -> List[JustificationV410]:
        """Parse LLM response into JustificationV410 objects."""
        # Extract JSON array from response
        json_match = re.search(r'\[[\s\S]*\]', raw_response)
        if not json_match:
            return []

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []

        justifications = []
        for item in data:
            try:
                j = JustificationV410.from_dict(item)
                # Validate rule references exist
                if all(norm_state.has_rule(ref) for ref in j.rule_refs):
                    justifications.append(j)
            except (KeyError, ValueError, TypeError):
                continue

        return justifications


# ============================================================================
# §6.4 — Deterministic Deliberator (Testing/Ablation)
# ============================================================================


class DeterministicDeliberator:
    """
    Deterministic deliberator that generates hardcoded justifications.

    Used for testing and ablation studies where LLM variability
    should be eliminated.
    """

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV410,
        episode: int,
        step: int
    ) -> DeliberationOutput:
        """
        Generate deterministic justifications based on observation.
        """
        start = time.perf_counter()

        # Get observation dict
        if isinstance(observation, dict):
            obs = observation
        else:
            obs = {
                "agent_pos": getattr(observation, "agent_pos", None),
                "inventory": getattr(observation, "inventory", 0),
                "zone_a_satisfied": getattr(observation, "zone_a_satisfied", False),
                "zone_b_satisfied": getattr(observation, "zone_b_satisfied", False),
            }

        justifications = []

        # Get available rule IDs
        rule_ids = [r.id for r in norm_state.rules]

        # Find permission rules
        perm_rule_ids = [r.id for r in norm_state.rules if r.type.value == "PERMISSION"]
        if not perm_rule_ids:
            perm_rule_ids = rule_ids[:1] if rule_ids else ["R1"]

        # Generate justifications for MOVE actions (A0-A3)
        for action_id in ["A0", "A1", "A2", "A3"]:
            # Find R4 (MOVE permission) or use first available
            move_rule = next((r.id for r in norm_state.rules
                            if r.type.value == "PERMISSION" and
                            r.effect.to_dict().get("action_class") == "MOVE"), None)
            if move_rule:
                justifications.append(JustificationV410(
                    action_id=action_id,
                    rule_refs=[move_rule],
                    claims=[{
                        "predicate": Predicate.PERMITS.value,
                        "args": [move_rule, "MOVE"]
                    }]
                ))

        # Generate justification for COLLECT (A4) if at SOURCE
        from .env.tri_demand import POSITIONS
        if obs.get("agent_pos") == POSITIONS.get("SOURCE"):
            collect_rule = next((r.id for r in norm_state.rules
                               if r.type.value == "PERMISSION" and
                               r.effect.to_dict().get("action_class") == "COLLECT"), None)
            if collect_rule:
                justifications.append(JustificationV410(
                    action_id="A4",
                    rule_refs=[collect_rule],
                    claims=[{
                        "predicate": Predicate.PERMITS.value,
                        "args": [collect_rule, "COLLECT"]
                    }]
                ))

        # Generate justification for DEPOSIT (A5) if at zone with inventory
        if obs.get("inventory", 0) > 0:
            agent_pos = obs.get("agent_pos")
            at_zone = agent_pos in [
                POSITIONS.get("ZONE_A"),
                POSITIONS.get("ZONE_B"),
                POSITIONS.get("ZONE_C")
            ]
            if at_zone:
                deposit_rule = next((r.id for r in norm_state.rules
                                   if r.type.value == "PERMISSION" and
                                   r.effect.to_dict().get("action_class") == "DEPOSIT"), None)
                if deposit_rule:
                    justifications.append(JustificationV410(
                        action_id="A5",
                        rule_refs=[deposit_rule],
                        claims=[{
                            "predicate": Predicate.PERMITS.value,
                            "args": [deposit_rule, "DEPOSIT"]
                        }]
                    ))

        elapsed = (time.perf_counter() - start) * 1000

        return DeliberationOutput(
            justifications=justifications,
            deliberation_time_ms=elapsed
        )


# ============================================================================
# §6.5 — Oracle Deliberator (Calibration)
# ============================================================================


class OracleDeliberator:
    """
    Oracle deliberator with perfect knowledge of optimal policy.

    Used for calibration to establish upper bound on performance.
    """

    def __init__(self, env: Any):
        """
        Initialize with environment for computing optimal actions.
        """
        self.env = env
        from .env.tri_demand import POSITIONS
        self.positions = POSITIONS

    def deliberate(
        self,
        observation: Any,
        norm_state: NormStateV410,
        episode: int,
        step: int
    ) -> DeliberationOutput:
        """
        Generate justification for optimal action.
        """
        start = time.perf_counter()

        # Get observation dict
        if isinstance(observation, dict):
            obs = observation
        else:
            obs = {
                "agent_pos": getattr(observation, "agent_pos", None),
                "inventory": getattr(observation, "inventory", 0),
                "zone_a_demand": getattr(observation, "zone_a_demand", 0),
                "zone_b_demand": getattr(observation, "zone_b_demand", 0),
                "zone_c_demand": getattr(observation, "zone_c_demand", 0),
                "zone_a_satisfied": getattr(observation, "zone_a_satisfied", False),
                "zone_b_satisfied": getattr(observation, "zone_b_satisfied", False),
                "zone_c_satisfied": getattr(observation, "zone_c_satisfied", False),
            }

        # Determine optimal action
        agent_pos = obs.get("agent_pos")
        inventory = obs.get("inventory", 0)

        # Priority: Zone A (if R1 active) > Zone B > Zone C
        zone_a_active = norm_state.has_rule("R1") and not obs.get("zone_a_satisfied", False)
        zone_b_active = norm_state.has_rule("R2") and not obs.get("zone_b_satisfied", False)

        target_zone = None
        if zone_a_active and obs.get("zone_a_demand", 0) > 0:
            target_zone = "ZONE_A"
        elif zone_b_active and obs.get("zone_b_demand", 0) > 0:
            target_zone = "ZONE_B"

        # Determine optimal action
        optimal_action = self._compute_optimal_action(agent_pos, inventory, target_zone)

        # Find relevant rule
        rule_refs = self._find_relevant_rules(optimal_action, norm_state)

        justifications = []
        if rule_refs:
            justifications.append(JustificationV410(
                action_id=optimal_action,
                rule_refs=rule_refs,
                claims=[{
                    "predicate": Predicate.PERMITS.value,
                    "args": [rule_refs[0], self._action_to_class(optimal_action)]
                }]
            ))

        elapsed = (time.perf_counter() - start) * 1000

        return DeliberationOutput(
            justifications=justifications,
            deliberation_time_ms=elapsed
        )

    def _compute_optimal_action(
        self,
        agent_pos: tuple,
        inventory: int,
        target_zone: Optional[str]
    ) -> str:
        """Compute the optimal action given state."""
        if target_zone is None:
            return "A0"  # No target, just move

        target_pos = self.positions.get(target_zone)
        source_pos = self.positions.get("SOURCE")

        if inventory == 0:
            # Need to collect first
            if agent_pos == source_pos:
                return "A4"  # COLLECT
            else:
                return self._move_toward(agent_pos, source_pos)
        else:
            # Have inventory, go to target
            if agent_pos == target_pos:
                return "A5"  # DEPOSIT
            else:
                return self._move_toward(agent_pos, target_pos)

    def _move_toward(self, current: tuple, target: tuple) -> str:
        """Compute move action toward target."""
        cx, cy = current
        tx, ty = target

        # Prefer vertical movement first
        if cy > ty:
            return "A0"  # MOVE_NORTH
        elif cy < ty:
            return "A1"  # MOVE_SOUTH
        elif cx < tx:
            return "A2"  # MOVE_EAST
        elif cx > tx:
            return "A3"  # MOVE_WEST
        else:
            return "A0"  # Already at target, shouldn't happen

    def _action_to_class(self, action_id: str) -> str:
        """Map action ID to action class."""
        mapping = {
            "A0": "MOVE", "A1": "MOVE", "A2": "MOVE", "A3": "MOVE",
            "A4": "COLLECT", "A5": "DEPOSIT"
        }
        return mapping.get(action_id, "MOVE")

    def _find_relevant_rules(
        self,
        action_id: str,
        norm_state: NormStateV410
    ) -> List[str]:
        """Find rules that permit this action."""
        action_class = self._action_to_class(action_id)

        for rule in norm_state.rules:
            if rule.type.value == "PERMISSION":
                effect = rule.effect.to_dict()
                if effect.get("action_class") == action_class:
                    return [rule.id]

        return []


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SYSTEM_PROMPT_V410",
    "format_observation",
    "format_norm_state",
    "LLMDeliberatorConfig",
    "LLMDeliberator",
    "DeterministicDeliberator",
    "OracleDeliberator",
]
