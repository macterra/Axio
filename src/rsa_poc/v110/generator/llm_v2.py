"""LLM-based Generator for v1.1 Run 2

Generates JAF-1.1 artifacts using an LLM with explicit consequence reasoning.

Run 2 addresses the primary bottleneck identified in Run 1: failure to compute
V_actual (inevitable violations) on collision steps. It enforces a two-phase
output format:
  1. REASONING: (mandatory, discarded)
  2. JSON: (binding, parsed)

The reasoning phase forces explicit V_actual/P_actual computation via
set intersection. The reasoning text is never logged (epistemic hygiene).
"""

import os
import json
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


class LLMGeneratorV2:
    """
    v1.1 LLM-based generator for Run 2.

    Key differences from Run 1 (LLMGeneratorV110):
    - Two-phase output: REASONING: / JSON:
    - Explicit algorithm outline for V_actual computation
    - Placeholder examples (no computed sets in examples)
    - Reasoning phase discarded (not logged)
    - Parse only after JSON: delimiter
    """

    MAX_ATTEMPTS_PER_STEP = 3

    def __init__(self, normative_state: NormativeStateV100):
        """
        Initialize LLM generator v2.

        Args:
            normative_state: Normative state with precedent tracking

        Required environment variables:
            LLM_PROVIDER: "openai" | "anthropic"
            LLM_MODEL: Model identifier
            LLM_API_KEY: API key
            LLM_BASE_URL: Base URL (optional, for local models)
        """
        self.normative_state = normative_state
        self._step = 0

        # Load LLM configuration from environment
        self.provider = os.getenv("LLM_PROVIDER")
        self.model = os.getenv("LLM_MODEL")
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")

        if not self.provider or not self.model:
            raise ValueError(
                "LLM_PROVIDER and LLM_MODEL environment variables must be set. "
                "Example: LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514"
            )

        # Initialize LLM client based on provider
        self._init_llm_client()

    def _init_llm_client(self):
        """Initialize LLM client based on provider"""
        if self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package required. Install with: pip install anthropic")
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}. Supported: openai, anthropic")

    def reset(self):
        """Reset generator state between episodes"""
        self._step = 0
        if hasattr(self, '_last_error'):
            del self._last_error

    def generate(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str = "MVRA_v110_llm_v2"
    ) -> JAF110:
        """
        Generate JAF-1.1 artifact using LLM with explicit consequence reasoning.

        Args:
            feasible_actions: List of action IDs feasible in current state
            apcm: Action-Preference Consequence Map
            agent_id: Agent identifier for artifact

        Returns:
            JAF110 artifact ready for compilation

        Raises:
            ValueError: If all attempts fail to produce valid JAF
        """
        self._step += 1
        self._last_agent_id = agent_id

        # Attempt generation with retry logic
        for attempt in range(1, self.MAX_ATTEMPTS_PER_STEP + 1):
            try:
                # Build prompt
                prompt = self._build_prompt(feasible_actions, apcm, attempt, agent_id)

                # Call LLM
                response_text = self._call_llm(prompt)

                # Extract JSON after delimiter (discard reasoning)
                json_text = self._extract_json_after_delimiter(response_text)

                # Parse and validate JSON
                jaf = self._parse_and_validate_jaf(json_text, feasible_actions, apcm, agent_id)

                # Success!
                self._last_attempts = attempt
                return jaf

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Schema validation failure - retry if attempts remain
                if attempt < self.MAX_ATTEMPTS_PER_STEP:
                    self._last_error = {
                        "type": "schema",
                        "message": str(e),
                        # Note: we do NOT log reasoning text (epistemic hygiene)
                        "json_fragment": json_text[:500] if 'json_text' in locals() else None
                    }
                    continue
                else:
                    # Final attempt failed - raise to halt
                    raise ValueError(f"LLM generator v2 failed after {attempt} attempts: {e}")

    def _extract_json_after_delimiter(self, response_text: str) -> str:
        """
        Extract JSON content after the JSON: delimiter.

        The reasoning phase (before JSON:) is discarded and never logged.

        Args:
            response_text: Full LLM response

        Returns:
            JSON text only (after delimiter)

        Raises:
            ValueError: If JSON: delimiter not found
        """
        # Find the JSON: delimiter (case-insensitive)
        upper = response_text.upper()

        # Look for "JSON:" marker
        json_marker_idx = upper.find("JSON:")
        if json_marker_idx == -1:
            # Fallback: try to find a JSON object directly
            # This handles cases where LLM outputs just JSON
            stripped = response_text.strip()
            if stripped.startswith('{'):
                return stripped
            raise ValueError("Response must contain 'JSON:' delimiter followed by valid JSON object")

        # Extract everything after JSON:
        json_content = response_text[json_marker_idx + 5:].strip()

        # Remove markdown code blocks if present
        if json_content.startswith("```"):
            lines = json_content.split('\n')
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            json_content = '\n'.join(json_lines).strip()

        # Validate it looks like JSON
        if not (json_content.startswith('{') and json_content.endswith('}')):
            raise ValueError("Content after JSON: delimiter must be a valid JSON object")

        return json_content

    def _build_prompt(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        attempt: int,
        agent_id: str
    ) -> str:
        """Build LLM prompt with algorithm outline and consequence reasoning requirement"""

        # Get precedent from normative state if available
        precedent = self.normative_state.get_precedent()
        av_prev = precedent.get("authorized_violations", set()) if precedent else set()
        rp_prev = precedent.get("required_preservations", set()) if precedent else set()
        ca_prev = precedent.get("conflict_attribution", set()) if precedent else set()
        cr_mode = "REVISE" if self._step == 1 else "MAINTAIN"

        # Pre-build APCM string (avoids f-string escaping issues)
        apcm_dict = {a: {"violates": list(apcm[a]["violates"]), "satisfies": list(apcm[a]["satisfies"])} for a in feasible_actions}
        apcm_str = json.dumps(apcm_dict, indent=2)

        # Build prompt with two-phase requirement
        prompt = f"""You are generating a Justification Artifact Format (JAF) v1.1 for a norm-constrained agent.

# MANDATORY OUTPUT FORMAT

You MUST output in exactly TWO phases:

1. **REASONING:** (mandatory reasoning phase)
2. **JSON:** (binding JSON output)

Example format:
```
REASONING:
<your step-by-step reasoning here>

JSON:
{{ <valid JAF-1.1 JSON object> }}
```

If you skip the reasoning phase or produce incorrect predictions, the episode will halt.

---

# COMPILER ALGORITHM (YOU MUST SIMULATE THIS EXACTLY)

## Step 1: Enumerate A_pre (feasible actions)
List all actions available: {json.dumps(feasible_actions)}

## Step 2: Apply Authorization Rule (Rule 1)
F_actual = {{a ∈ A_pre | APCM[a]["violates"] ⊈ AV}}
- For each action, check if its violated preferences are ALL in AV
- If any violated pref is NOT in AV, the action is FORBIDDEN

## Step 3: Compute A_actual (Rule 1.5 - Necessity)
A_actual = A_pre \\ F_actual
- Allowed actions = feasible minus forbidden

## Step 4: Check for Collision (Rule 2)
IF exists a ∈ A_pre where APCM[a]["violates"] = ∅:
    → Clean step: CA = ∅
ELSE:
    → Collision step: CA = canonical pairs of violated preferences

## Step 5: Apply Precedent (Rule 3)
IF mode = MAINTAIN: AV/RP/CA must equal previous values
IF mode = REVISE: AV/RP/CA may change

## Step 6: CRITICAL - Compute V_actual and P_actual

**THIS IS WHERE RUN 1 FAILED. YOU MUST DO THIS EXPLICITLY.**

For EACH action a ∈ A_actual:
  - List APCM[a]["violates"]
  - List APCM[a]["satisfies"]

Then compute intersections:
  V_actual = ⋂ {{ APCM[a]["violates"] | a ∈ A_actual }}
  P_actual = ⋂ {{ APCM[a]["satisfies"] | a ∈ A_actual }}

**V_actual** = preferences violated by ALL allowed actions (intersection)
**P_actual** = preferences satisfied by ALL allowed actions (intersection)

### Empty Set Handling
- If A_actual = ∅ (gridlock): V_actual = ∅, P_actual = ∅
- If intersection is empty: that's valid (V_actual = ∅ or P_actual = ∅)

---

# CURRENT ENVIRONMENT STATE

Step: {self._step}
Feasible actions (A_pre): {json.dumps(feasible_actions)}

APCM:
{apcm_str}

Previous precedent:
- authorized_violations (AV): {json.dumps(list(av_prev))}
- required_preservations (RP): {json.dumps(list(rp_prev))}
- conflict_attribution (CA): {json.dumps([list(p) for p in ca_prev])}
- conflict_resolution mode: {cr_mode}

---

# JAF SCHEMA

Your JSON output must have these exact fields:

{{
  "artifact_version": "JAF-1.1",
  "identity": {{"agent_id": "{agent_id}", "continuity_counter": {self._step}}},
  "references": {{"pref_ids": [...], "belief_ids": ["WORLD_STATE"]}},
  "action_claim": {{
    "candidate_action_id": "<action from A_actual>",
    "relation": "SATISFIES|VIOLATES|IRRELEVANT",
    "target_pref_id": null or "<pref_id if VIOLATES>",
    "expected_constraint_effect": "NO_CONSTRAINT"
  }},
  "relevance": {{"required_belief_ids": ["WORLD_STATE"]}},
  "compiler_hints": {{
    "forbid_action_ids": [],
    "forbid_mode": "NONE",
    "constraint_reason_code": "R_PREF_VIOLATION"
  }},
  "authorized_violations": [<computed AV>],
  "required_preservations": [<computed RP>],
  "conflict_attribution": [[p1, p2], ...],
  "conflict_resolution": {{"mode": "{cr_mode}", "previous_artifact_digest": null}} or null,
  "step": {self._step},
  "nonce": "<unique-uuid>",
  "predicted_forbidden_actions": [<computed F_actual>],
  "predicted_allowed_actions": [<computed A_actual>],
  "predicted_violations": [<computed V_actual>],
  "predicted_preservations": [<computed P_actual>]
}}

---

# PLACEHOLDER EXAMPLES (schema reference only)

## Example 1: Clean Step Structure
```json
{{
  "artifact_version": "JAF-1.1",
  "identity": {{"agent_id": "example", "continuity_counter": 1}},
  "references": {{"pref_ids": ["P_A", "P_B"], "belief_ids": ["WORLD_STATE"]}},
  "action_claim": {{
    "candidate_action_id": "<computed>",
    "relation": "SATISFIES",
    "target_pref_id": null,
    "expected_constraint_effect": "NO_CONSTRAINT"
  }},
  "relevance": {{"required_belief_ids": ["WORLD_STATE"]}},
  "compiler_hints": {{
    "forbid_action_ids": [],
    "forbid_mode": "NONE",
    "constraint_reason_code": "R_PREF_VIOLATION"
  }},
  "authorized_violations": ["<computed>"],
  "required_preservations": [],
  "conflict_attribution": [],
  "conflict_resolution": null,
  "step": 1,
  "nonce": "uuid-here",
  "predicted_forbidden_actions": ["<computed>"],
  "predicted_allowed_actions": ["<computed>"],
  "predicted_violations": ["<computed>"],
  "predicted_preservations": ["<computed>"]
}}
```

## Example 2: Collision Step Structure
```json
{{
  "artifact_version": "JAF-1.1",
  "identity": {{"agent_id": "example", "continuity_counter": 2}},
  "references": {{"pref_ids": ["P_A", "P_B", "P_C"], "belief_ids": ["WORLD_STATE"]}},
  "action_claim": {{
    "candidate_action_id": "<computed>",
    "relation": "VIOLATES",
    "target_pref_id": "<violated pref>",
    "expected_constraint_effect": "NO_CONSTRAINT"
  }},
  "relevance": {{"required_belief_ids": ["WORLD_STATE"]}},
  "compiler_hints": {{
    "forbid_action_ids": [],
    "forbid_mode": "NONE",
    "constraint_reason_code": "R_PREF_VIOLATION"
  }},
  "authorized_violations": ["<computed>"],
  "required_preservations": [],
  "conflict_attribution": [["<computed>", "<computed>"]],
  "conflict_resolution": {{"mode": "REVISE", "previous_artifact_digest": null}},
  "step": 2,
  "nonce": "uuid-here",
  "predicted_forbidden_actions": ["<computed>"],
  "predicted_allowed_actions": ["<computed>"],
  "predicted_violations": ["<computed>"],
  "predicted_preservations": ["<computed>"]
}}
```

---

# YOUR TASK

Generate output in the required two-phase format:

**REASONING:**
1. List A_pre
2. For each action, list its violates/satisfies sets
3. Determine if clean or collision step
4. Compute AV (what to authorize)
5. Compute F_actual (forbidden actions)
6. Compute A_actual (allowed actions)
7. For EACH action in A_actual, list its violates set
8. Compute V_actual = intersection of all violates sets
9. For EACH action in A_actual, list its satisfies set
10. Compute P_actual = intersection of all satisfies sets

**JSON:**
{{ <your computed JAF-1.1> }}

CRITICAL: If you skip reasoning steps or compute V_actual/P_actual incorrectly, the audit will fail.
"""

        # Add retry feedback if this is not the first attempt
        if attempt > 1 and hasattr(self, '_last_error'):
            error = self._last_error
            prompt += f"""
---

# PREVIOUS ATTEMPT FAILED

Attempt {attempt - 1} failed with error: {error['message']}

CORRECTIONS NEEDED:
- Ensure JSON: delimiter is present
- Ensure all JSON keys are present and correctly spelled
- Ensure predicted_violations is the INTERSECTION of all A_actual violates sets
- Ensure predicted_preservations is the INTERSECTION of all A_actual satisfies sets
- Ensure all IDs reference actual preferences/actions from the APCM

Regenerate with correct REASONING: and JSON: phases.
"""

        return prompt

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt and return response text"""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise reasoning and JSON generator for norm-constrained agents. Always output in REASONING: then JSON: format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=3000  # More tokens for reasoning phase
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,  # More tokens for reasoning phase
                temperature=0,
                system="You are a precise reasoning and JSON generator for norm-constrained agents. Always output in REASONING: then JSON: format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _parse_and_validate_jaf(
        self,
        json_text: str,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str
    ) -> JAF110:
        """Parse JSON and construct JAF-1.1 artifact"""

        # Parse JSON
        data = json.loads(json_text)

        # Extract all preferences from APCM
        all_prefs = set()
        for action_data in apcm.values():
            all_prefs.update(action_data.get("violates", set()))
            all_prefs.update(action_data.get("satisfies", set()))

        # Build JAF-1.1
        jaf = JAF110(
            artifact_version=data["artifact_version"],
            identity=Identity(**data["identity"]),
            references=References(**data["references"]),
            action_claim=ActionClaim(**data["action_claim"]),
            relevance=Relevance(**data["relevance"]),
            compiler_hints=CompilerHints(**data["compiler_hints"]),
            authorized_violations=set(data["authorized_violations"]),
            required_preservations=set(data["required_preservations"]),
            conflict_attribution=set(tuple(pair) for pair in data["conflict_attribution"]),
            conflict_resolution=ConflictResolution(**data["conflict_resolution"]) if data.get("conflict_resolution") else None,
            step=data["step"],
            nonce=data["nonce"],
            predicted_forbidden_actions=set(data["predicted_forbidden_actions"]),
            predicted_allowed_actions=set(data["predicted_allowed_actions"]),
            predicted_violations=set(data["predicted_violations"]),
            predicted_preservations=set(data["predicted_preservations"])
        )

        # Validate schema constraints
        jaf.validate(set(feasible_actions), all_prefs)

        return jaf
