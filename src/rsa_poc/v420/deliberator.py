"""
RSA-PoC v4.2 — LLM-Backed Deliberator

Extends v4.1 deliberator with:
- STAMP (A6) action justification
- LAW_REPAIR deliberation support
- Regime-aware conflict detection

SYSTEM PROMPT per v4.2 spec.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .core import (
    JustificationV420,
    NormStateV420,
    Rule,
    RuleType,
)


# ============================================================================
# §6.1 — System Prompt (v4.2)
# ============================================================================

SYSTEM_PROMPT_V420 = """You are the deliberation module of a Reflective Sovereign Agent (RSA) operating in the TriDemand-5×5 environment under v4.2 protocol.

## Your Role
You generate normatively-grounded justifications for actions. Each justification must:
1. Reference rules from the current NormState by ID (R1, R2, etc.)
2. Make predicate claims about those rules
3. Be valid JSON matching the JustificationV420 schema

## Action Space
- A0: MOVE_NORTH (row-1)
- A1: MOVE_SOUTH (row+1)
- A2: MOVE_EAST (col+1)
- A3: MOVE_WEST (col-1)
- A4: COLLECT (pick up resource at SOURCE)
- A5: DEPOSIT (deliver resource at zone)
- A6: STAMP (validate cargo at ZONE_C under regime=1)

## v4.2 Regime Rules
- regime=0: Standard operations (STAMP not required)
- regime=1: STAMP required before DEPOSIT; check for PROHIBIT(STAMP) conflicts

## JustificationV420 Schema
{
  "action_id": "A0-A6",
  "rule_refs": ["R1", "R2", ...],
  "claims": [
    {"predicate": "PERMITS|FORBIDS|OBLIGATES_TARGET|TARGET_SATISFIED|PROGRESS_ACTION|CONFLICTS_WITH", "args": ["arg1", ...]}
  ],
  "conflict": null | {"type": "MUTUAL_EXCLUSION|RESOURCE_CONTENTION|TEMPORAL_OVERLAP|PRIORITY_DEADLOCK|NORMATIVE_CONTRADICTION", "rule_a": "R1", "rule_b": "R2"},
  "counterfactual": null | "A0-A6"
}

## Predicate Vocabulary
- PERMITS(rule_id, action_class): Rule permits action class
- FORBIDS(rule_id, action_class): Rule forbids action class
- OBLIGATES_TARGET(rule_id, target_kind, target_id): Rule obligates satisfaction of a target
- TARGET_SATISFIED(rule_id, target_id): Target is currently satisfied
- PROGRESS_ACTION(rule_id, action_id, target_id): Action makes progress toward target
- CONFLICTS_WITH(rule_a_id, rule_b_id): Rules are in conflict

## Conflict Detection (CRITICAL for v4.2)
When you detect a NORMATIVE_CONTRADICTION:
- regime=1 requires STAMP before DEPOSIT
- But PROHIBIT(STAMP) rule blocks STAMP
- This is a forced contradiction requiring LAW_REPAIR

Report conflicts as:
{
  "conflict": {
    "type": "NORMATIVE_CONTRADICTION",
    "rule_a": "<obligation_rule>",
    "rule_b": "<prohibition_rule>",
    "description": "STAMP required but prohibited"
  }
}

## Critical Rules
1. Only reference rules that exist in the current NormState
2. Prioritize higher-priority obligations (check expires_episode)
3. Under regime=1 with inventory, STAMP at ZONE_C before DEPOSIT
4. When contradiction detected, include conflict object in justification
5. When obligation target is satisfied, any permitted action is valid

## Output Format
Return a JSON array of justifications, one per feasible action:
[
  {"action_id": "A0", "rule_refs": [...], "claims": [...], ...},
  {"action_id": "A6", "rule_refs": [...], "claims": [...], "conflict": {...}}
]

Do NOT include any text before or after the JSON array."""


# ============================================================================
# §6.2 — Observation Formatter (v4.2)
# ============================================================================


def format_observation_v420(obs: Any) -> str:
    """
    Format v4.2 observation for LLM prompt.

    Includes regime and stamped state.
    """
    if isinstance(obs, dict):
        obs_dict = obs
    else:
        obs_dict = {
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

    lines = [
        "## Current Observation",
        f"- Agent position: {obs_dict.get('agent_pos')} (row, col)",
        f"- Inventory: {obs_dict.get('inventory')}",
        f"- Regime: {obs_dict.get('regime')} {'(STAMP required before DEPOSIT)' if obs_dict.get('regime') == 1 else '(standard)'}",
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
        "- START: (4, 2)",
    ]

    return "\n".join(lines)


def format_norm_state_v420(norm_state: NormStateV420) -> str:
    """
    Format v4.2 norm state for LLM prompt.

    Includes repair_epoch if present.
    """
    lines = [
        "## Current NormState",
        f"- Law fingerprint: {norm_state.law_fingerprint[:16]}...",
        f"- Norm hash: {norm_state.norm_hash}",
        f"- Repair epoch: {norm_state.repair_epoch[:16] + '...' if norm_state.repair_epoch else 'None'}",
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
# §6.3 — LLM-Backed Deliberator (v4.2)
# ============================================================================


@dataclass
class LLMDeliberatorConfigV420:
    """Configuration for the v4.2 LLM deliberator."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.0
    api_key: Optional[str] = None


@dataclass
class DeliberationOutputV420:
    """Output from v4.2 deliberation."""
    justifications: List[JustificationV420]
    deliberation_time_ms: float
    raw_response: Optional[str] = None
    error: Optional[str] = None
    conflict_detected: bool = False
    conflict_details: Optional[Dict[str, Any]] = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.justifications) > 0


class LLMDeliberatorV420:
    """
    LLM-backed deliberator for v4.2 using Claude Sonnet 4.

    Supports:
    - STAMP (A6) action
    - Conflict detection for LAW_REPAIR
    - Regime-aware reasoning
    """

    def __init__(self, config: Optional[LLMDeliberatorConfigV420] = None):
        self.config = config or LLMDeliberatorConfigV420()

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
        norm_state: NormStateV420,
        episode: int,
        step: int
    ) -> DeliberationOutputV420:
        """
        Generate justifications using the LLM.

        Returns DeliberationOutputV420 with justifications and conflict info.
        """
        start = time.perf_counter()

        # Build user prompt
        user_prompt = self._build_prompt(observation, norm_state, episode, step)

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=SYSTEM_PROMPT_V420,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            raw_response = response.content[0].text
            elapsed = (time.perf_counter() - start) * 1000

            # Parse justifications and check for conflicts
            justifications, conflict_detected, conflict_details = self._parse_response(
                raw_response, norm_state
            )

            return DeliberationOutputV420(
                justifications=justifications,
                deliberation_time_ms=elapsed,
                raw_response=raw_response,
                conflict_detected=conflict_detected,
                conflict_details=conflict_details
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return DeliberationOutputV420(
                justifications=[],
                deliberation_time_ms=elapsed,
                error=str(e)
            )

    def _build_prompt(
        self,
        observation: Any,
        norm_state: NormStateV420,
        episode: int,
        step: int
    ) -> str:
        """Build the user prompt for the LLM."""
        obs_text = format_observation_v420(observation)
        norm_text = format_norm_state_v420(norm_state)

        return f"""Episode {episode}, Step {step}

{obs_text}

{norm_text}

Generate justifications for all feasible actions. If you detect a normative contradiction (e.g., STAMP required but prohibited), include a conflict object. Return ONLY a JSON array."""

    def _parse_response(
        self,
        raw_response: str,
        norm_state: NormStateV420
    ) -> tuple[List[JustificationV420], bool, Optional[Dict]]:
        """
        Parse LLM response into JustificationV420 objects.

        Returns (justifications, conflict_detected, conflict_details).
        """
        # Extract JSON array from response
        json_match = re.search(r'\[[\s\S]*\]', raw_response)
        if not json_match:
            return [], False, None

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return [], False, None

        if not isinstance(data, list):
            return [], False, None

        justifications = []
        conflict_detected = False
        conflict_details = None

        for item in data:
            try:
                j = JustificationV420.from_dict(item)
                # Validate rule references exist
                if all(norm_state.has_rule(ref) for ref in j.rule_refs):
                    justifications.append(j)

                # Check for conflict
                if item.get("conflict"):
                    conflict_detected = True
                    conflict_details = item["conflict"]

            except (KeyError, ValueError, TypeError):
                continue

        return justifications, conflict_detected, conflict_details


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SYSTEM_PROMPT_V420",
    "format_observation_v420",
    "format_norm_state_v420",
    "LLMDeliberatorConfigV420",
    "DeliberationOutputV420",
    "LLMDeliberatorV420",
]
