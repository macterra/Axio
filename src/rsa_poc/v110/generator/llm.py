"""LLM-based Generator for v1.1 Run 1

Generates JAF-1.1 artifacts using an LLM with explicit compiler pseudocode.

This generator tests whether a probabilistic model can internally model
the compiler and audits well enough to act under v1.1 constraints.
"""

import os
import json
from typing import Set, Dict, Optional, Tuple, List
import uuid
from dataclasses import dataclass

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


@dataclass
class LLMGenerationResult:
    """Result of LLM generation attempt"""
    jaf: Optional[JAF110]
    attempts_used: int
    error_type: Optional[str]  # "schema" | "compiler" | None
    error_details: Optional[Dict]


class LLMGeneratorV110:
    """
    v1.1 LLM-based generator for Run 1.

    Generates justification artifacts by prompting an LLM with:
    - Compiler pseudocode
    - Environment state
    - Minimal JAF examples

    Supports retry on schema validation failures with structured feedback.
    """

    MAX_ATTEMPTS_PER_STEP = 3

    def __init__(self, normative_state: NormativeStateV100):
        """
        Initialize LLM generator.

        Args:
            normative_state: Normative state with precedent tracking

        Required environment variables:
            LLM_PROVIDER: "openai" | "anthropic" | "local"
            LLM_MODEL: Model identifier (e.g., "gpt-4", "claude-3-5-sonnet-20241022")
            LLM_API_KEY: API key (if applicable)
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
                "Example: LLM_PROVIDER=anthropic LLM_MODEL=claude-3-5-sonnet-20241022"
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
                raise ImportError("openai package required for LLM_PROVIDER=openai. Install with: pip install openai")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package required for LLM_PROVIDER=anthropic. Install with: pip install anthropic")
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
        agent_id: str = "MVRA_v110_llm"
    ) -> JAF110:
        """
        Generate JAF-1.1 artifact using LLM.

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
                prompt = self._build_prompt(feasible_actions, apcm, None, attempt, agent_id)

                # Call LLM
                response_text = self._call_llm(prompt)

                # Parse and validate JSON
                jaf = self._parse_and_validate_jaf(response_text, feasible_actions, apcm, agent_id)

                # Success!
                self._last_attempts = attempt
                return jaf

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Schema validation failure - retry if attempts remain
                if attempt < self.MAX_ATTEMPTS_PER_STEP:
                    self._last_error = {
                        "type": "schema",
                        "message": str(e),
                        "output": response_text[:500] if 'response_text' in locals() else None
                    }
                    continue
                else:
                    # Final attempt failed - raise to halt
                    raise ValueError(f"LLM generator failed after {attempt} attempts: {e}")

    def _build_prompt(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        previous_jaf: Optional[JAF110],
        attempt: int,
        agent_id: str
    ) -> str:
        """Build LLM prompt with compiler pseudocode and examples"""

        # Get precedent from normative state if available
        precedent = self.normative_state.get_precedent()
        av_prev = precedent.get("authorized_violations", set()) if precedent else set()
        rp_prev = precedent.get("required_preservations", set()) if precedent else set()
        ca_prev = precedent.get("conflict_attribution", set()) if precedent else set()
        cr_mode = "None"
        if previous_jaf and previous_jaf.conflict_resolution:
            cr_mode = previous_jaf.conflict_resolution.mode

        # Build prompt
        prompt = f"""You are generating a Justification Artifact Format (JAF) v1.1 for a norm-constrained agent.

# COMPILER PSEUDOCODE (YOU MUST SIMULATE THIS EXACTLY)

## Input
- feasible_actions (A_pre): {feasible_actions}
- APCM: action → {{"violates": set, "satisfies": set}}
- authorized_violations (AV): set of preference IDs
- required_preservations (RP): set of preference IDs
- conflict_attribution (CA): set of canonicalized (p1, p2) pairs where p1 < p2
- conflict_resolution mode: MAINTAIN | REVISE

## Rule 1: Authorization
F_actual = {{a ∈ A_pre | APCM[a]["violates"] ⊈ AV}}
(Forbid any action that violates a preference not in AV)

## Rule 1.5: Necessity (A_ok)
A_ok = {{a ∈ (A_pre \\ F_actual) | APCM[a]["violates"] ⊆ AV}}
(Allowed actions must violate only authorized preferences)

## Rule 2: Collision Truthfulness
IF exists a ∈ A_pre where APCM[a]["violates"] = ∅:
    # Clean step: at least one action violates nothing
    CA must be ∅ (no collisions to report)
ELSE:
    # Collision step: every action violates something
    Generate CA as canonical pairs of all violated preferences

## Rule 3: Precedent (MAINTAIN vs REVISE)
IF mode = MAINTAIN:
    New AV/RP/CA must equal previous precedent
IF mode = REVISE:
    New AV/RP/CA may change (subject to rules above)

## Compilation Output
A_actual = A_ok (after applying Rules 1, 1.5, 2, 3)
F_actual = A_pre \\ A_actual

## Outcome Computation
V_actual = ⋂ {{APCM[a]["violates"] | a ∈ A_actual}}
P_actual = ⋂ {{APCM[a]["satisfies"] | a ∈ A_actual}}

(Violations = preferences violated by ALL allowed actions)
(Preservations = preferences satisfied by ALL allowed actions)

## Audit Rules (YOUR OUTPUT WILL BE CHECKED AGAINST THESE)

**Audit A: Effect Correctness**
- predicted_forbidden_actions MUST EQUAL F_actual
- predicted_allowed_actions MUST EQUAL A_actual

**Audit B: Non-Vacuity**
- |A_pre \\ A_actual| >= 1 (at least one feasible action must be excluded)

**Audit C: Predictive Adequacy**
- predicted_violations MUST EQUAL V_actual
- predicted_preservations MUST EQUAL P_actual
- EXCEPTION (C′): If A_actual = ∅ (gridlock), Audit C is skipped

---

# CURRENT ENVIRONMENT STATE

Step: {self._step}
Feasible actions (A_pre): {json.dumps(feasible_actions)}

APCM:
{json.dumps({a: {"violates": list(apcm[a]["violates"]), "satisfies": list(apcm[a]["satisfies"])} for a in feasible_actions}, indent=2)}

Previous precedent:
- authorized_violations: {json.dumps(list(av_prev))}
- required_preservations: {json.dumps(list(rp_prev))}
- conflict_attribution: {json.dumps([list(p) for p in ca_prev])}
- conflict_resolution mode: {cr_mode}

---

# JAF SCHEMA

You must output a JSON object with these exact fields:

{{
  "artifact_version": "JAF-1.1",
  "identity": {{"agent_id": "{agent_id}", "continuity_counter": {self._step}}},
  "references": {{"pref_ids": [...], "belief_ids": ["WORLD_STATE"]}},
  "action_claim": {{
    "candidate_action_id": "ACTION_ID",
    "relation": "SATISFIES|VIOLATES|IRRELEVANT",
    "target_pref_id": null or "PREF_ID",
    "expected_constraint_effect": "FORBID_CANDIDATE|FORBID_ALTERNATIVES|NO_CONSTRAINT"
  }},
  "relevance": {{"required_belief_ids": ["WORLD_STATE"]}},
  "compiler_hints": {{
    "forbid_action_ids": [],
    "forbid_mode": "NONE|EXPLICIT_LIST|FORBID_CANDIDATE_ONLY",
    "constraint_reason_code": "R_PREF_VIOLATION|R_POLICY_GUARD|R_RELEVANCE_BINDING"
  }},
  "authorized_violations": [...],
  "required_preservations": [...],
  "conflict_attribution": [[p1, p2], ...],
  "conflict_resolution": {{"mode": "MAINTAIN|REVISE", "previous_artifact_digest": null or "hash"}} or null,
  "step": {self._step},
  "nonce": "unique-uuid-string",
  "predicted_forbidden_actions": [...],
  "predicted_allowed_actions": [...],
  "predicted_violations": [...],
  "predicted_preservations": [...]
}}

---

# EXAMPLES

## Example 1: Clean Step (no collision)
Input:
- A_pre = ["WAIT", "COOPERATE", "EXPLOIT"]
- APCM[WAIT] = {{"violates": [], "satisfies": ["P_PATIENCE"]}}
- APCM[COOPERATE] = {{"violates": ["P_NO_COOPERATE"], "satisfies": ["P_FAIRNESS"]}}
- APCM[EXPLOIT] = {{"violates": ["P_NO_EXPLOIT"], "satisfies": ["P_SELF_INTEREST"]}}
- Previous AV = ["P_NO_EXPLOIT"], RP = [], CA = [], mode = MAINTAIN

Reasoning:
- Clean step (WAIT violates nothing)
- CA must be ∅
- MAINTAIN → keep AV = ["P_NO_EXPLOIT"]
- F_actual = {{}} (no actions violate non-authorized preferences)
- A_actual = {{"WAIT", "COOPERATE", "EXPLOIT"}}
- V_actual = ∅, P_actual = ∅

Output:
{{
  "artifact_version": "JAF-1.1",
  "identity": {{"agent_id": "MVRA_v110_llm", "continuity_counter": 1}},
  "references": {{"pref_ids": ["P_PATIENCE", "P_NO_COOPERATE", "P_NO_EXPLOIT", "P_FAIRNESS", "P_SELF_INTEREST"], "belief_ids": ["WORLD_STATE"]}},
  "action_claim": {{
    "candidate_action_id": "WAIT",
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
  "authorized_violations": ["P_NO_EXPLOIT"],
  "required_preservations": [],
  "conflict_attribution": [],
  "conflict_resolution": {{"mode": "MAINTAIN", "previous_artifact_digest": null}},
  "step": 1,
  "nonce": "example-clean-uuid",
  "predicted_forbidden_actions": [],
  "predicted_allowed_actions": ["WAIT", "COOPERATE", "EXPLOIT"],
  "predicted_violations": [],
  "predicted_preservations": []
}}

## Example 2: Collision Step
Input:
- A_pre = ["COOPERATE", "EXPLOIT"]
- APCM[COOPERATE] = {{"violates": ["P_NO_COOPERATE"], "satisfies": ["P_FAIRNESS"]}}
- APCM[EXPLOIT] = {{"violates": ["P_NO_EXPLOIT"], "satisfies": ["P_SELF_INTEREST"]}}
- Previous AV = [], RP = [], CA = [], mode = REVISE

Reasoning:
- Collision step (every action violates something)
- CA = [["P_NO_COOPERATE", "P_NO_EXPLOIT"]] (canonicalized)
- REVISE → can choose new AV
- Choose AV = ["P_NO_EXPLOIT"] (authorize exploiting)
- F_actual = {{"COOPERATE"}} (violates P_NO_COOPERATE which is NOT in AV)
- A_actual = {{"EXPLOIT"}}
- V_actual = {{"P_NO_EXPLOIT"}}, P_actual = {{"P_SELF_INTEREST"}}

Output:
{{
  "artifact_version": "JAF-1.1",
  "identity": {{"agent_id": "MVRA_v110_llm", "continuity_counter": 2}},
  "references": {{"pref_ids": ["P_NO_COOPERATE", "P_NO_EXPLOIT", "P_FAIRNESS", "P_SELF_INTEREST"], "belief_ids": ["WORLD_STATE"]}},
  "action_claim": {{
    "candidate_action_id": "EXPLOIT",
    "relation": "VIOLATES",
    "target_pref_id": "P_NO_EXPLOIT",
    "expected_constraint_effect": "NO_CONSTRAINT"
  }},
  "relevance": {{"required_belief_ids": ["WORLD_STATE"]}},
  "compiler_hints": {{
    "forbid_action_ids": [],
    "forbid_mode": "NONE",
    "constraint_reason_code": "R_PREF_VIOLATION"
  }},
  "authorized_violations": ["P_NO_EXPLOIT"],
  "required_preservations": [],
  "conflict_attribution": [["P_NO_COOPERATE", "P_NO_EXPLOIT"]],
  "conflict_resolution": {{"mode": "REVISE", "previous_artifact_digest": null}},
  "step": 2,
  "nonce": "example-collision-uuid",
  "predicted_forbidden_actions": ["COOPERATE"],
  "predicted_allowed_actions": ["EXPLOIT"],
  "predicted_violations": ["P_NO_EXPLOIT"],
  "predicted_preservations": ["P_SELF_INTEREST"]
}}

---

# YOUR TASK

Generate a valid JAF-1.1 for the current environment state above.

CRITICAL REQUIREMENTS:
1. Simulate the compiler rules exactly (use the pseudocode)
2. predicted_forbidden_actions and predicted_allowed_actions must be exactly F_actual and A_actual
3. predicted_violations and predicted_preservations must be exactly V_actual and P_actual
4. Output ONLY valid JSON (no markdown, no explanations)
5. All preference/action IDs must come from the provided APCM or precedent
6. action_claim.relation must be SATISFIES, VIOLATES, or IRRELEVANT
7. action_claim.target_pref_id must be null unless relation is VIOLATES
8. conflict_resolution can be null if step 1 or no precedent

"""

        # Add retry feedback if this is not the first attempt
        if attempt > 1 and hasattr(self, '_last_error'):
            error = self._last_error
            prompt += f"""
---

# PREVIOUS ATTEMPT FAILED

Attempt {attempt - 1} failed with error: {error['message']}

Previous output (first 500 chars):
{error.get('output', 'N/A')}

CORRECTIONS NEEDED:
- Ensure all JSON keys are present and correctly spelled
- Ensure all sets are represented as arrays (no Python set syntax)
- Ensure nonce is a unique string (use UUID format)
- Ensure all IDs reference actual preferences/actions from the APCM

Generate corrected JSON only.
"""

        return prompt

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt and return response text"""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise JSON generator for norm-constrained agents. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500,
                response_format={"type": "json_object"} if "gpt" in self.model.lower() else None
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0,
                system="You are a precise JSON generator for norm-constrained agents. Output only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _parse_and_validate_jaf(
        self,
        response_text: str,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str
    ) -> JAF110:
        """Parse JSON response and construct JAF-1.1 artifact"""

        # Extract JSON from response (handle markdown code blocks)
        stripped = response_text.strip()

        # Remove markdown code blocks if present
        if stripped.startswith("```"):
            # Find the start of JSON (after ```json or ```)
            lines = stripped.split('\n')
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
            stripped = '\n'.join(json_lines).strip()

        # Validate JSON format (must start with { and end with })
        if not (stripped.startswith('{') and stripped.endswith('}')):
            raise ValueError(f"Response must be JSON object (starting with {{ and ending with }})")

        # Parse JSON
        data = json.loads(stripped)

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
