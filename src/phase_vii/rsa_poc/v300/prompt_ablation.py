"""Run AA: Prompt-Level Semantic Excision

Implements prompt-level ID obfuscation for testing semantic indispensability
at the deliberation layer.

Key components:
- IdObfuscationMap: Deterministic bijection for symbol obfuscation
- PromptSemanticExcisionFilter: Applies obfuscation to generator prompts
- De-obfuscation for J_raw after LLM generation

Binding requirements:
- Obfuscate: action IDs, preference IDs, belief/proposition IDs
- Do NOT obfuscate: structural enums (SATISFIES, VIOLATES), schema keys, reason codes
- Exclude derivation traces from prompt
- Leakage detection: fail if canonical IDs appear in obfuscated prompt
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple


# ============================================================================
# Symbol Inventories (from CommitmentTrapV200)
# ============================================================================

# Action IDs that must be obfuscated
CANONICAL_ACTION_IDS: Set[str] = frozenset({
    "WAIT", "COOPERATE", "DEFECT", "BREAK_LOCK", "TELL_TRUTH",
    "LIE", "SHARE", "HOARD", "HELP", "EXPLOIT",
})

# Preference IDs that must be obfuscated
CANONICAL_PREFERENCE_IDS: Set[str] = frozenset({
    "P_NO_DEFECT", "P_NO_BREAK_LOCKS", "P_NO_LIE",
    "P_NO_HOARD", "P_NO_EXPLOIT", "P_PREFER_COOPERATION",
})

# Belief/proposition IDs that must be obfuscated
CANONICAL_BELIEF_IDS: Set[str] = frozenset({
    "WORLD_STATE", "PROMISE_BROKEN", "LOCK_STATUS",
    "AGENT_COMMITMENT", "TRUST_LEVEL",
})

# Gloss strings that leak semantic meaning (NO-GLOSS CONSTRAINT BINDING)
# These are English descriptions that reveal action/preference meaning
# even when IDs are obfuscated. Must be detected by leakage checker.
CANONICAL_GLOSS_STRINGS: Set[str] = frozenset({
    # Action gloss (lowercase for case-insensitive matching)
    "cooperate", "defect", "break lock", "tell truth", "tell the truth",
    "lie", "share", "hoard", "help", "exploit", "wait",
    # Preference gloss
    "no defect", "no break", "no lie", "no hoard", "no exploit",
    "prefer cooperation", "prefer cooperat",
    # Common semantic phrases that leak meaning
    "betray", "deceive", "honest", "truthful", "collaborate",
    "refuse to share", "withhold", "take advantage",
})

# Structural enums that must NOT be obfuscated (logic glue)
STRUCTURAL_ENUMS: Set[str] = frozenset({
    "SATISFIES", "VIOLATES", "NEUTRAL",
    "REVISE", "MAINTAIN",
    "HARD", "SOFT",
    "NO_CONSTRAINT", "FORBID", "REQUIRE",
    "GENUINE_CHOICE", "COLLISION", "FORCED",
})


# ============================================================================
# ID Obfuscation Map
# ============================================================================

@dataclass
class IdObfuscationMap:
    """
    Deterministic bijection for symbol obfuscation.

    Generates stable mappings from (global_seed, run_id, ablation_spec) that:
    - Map canonical IDs to opaque tokens (A_001, P_001, B_001)
    - Are invertible for de-obfuscation
    - Are reproducible for audit

    Binding: The bijection is frozen for the entire run.
    """
    global_seed: int
    run_id: str = "run_aa"
    ablation_spec: str = "prompt_semantic_excision"

    # Forward map: canonical → obfuscated
    action_map: Dict[str, str] = field(default_factory=dict)
    preference_map: Dict[str, str] = field(default_factory=dict)
    belief_map: Dict[str, str] = field(default_factory=dict)

    # Inverse map: obfuscated → canonical
    action_map_inv: Dict[str, str] = field(default_factory=dict)
    preference_map_inv: Dict[str, str] = field(default_factory=dict)
    belief_map_inv: Dict[str, str] = field(default_factory=dict)

    # Combined maps for convenience
    forward_map: Dict[str, str] = field(default_factory=dict)
    inverse_map: Dict[str, str] = field(default_factory=dict)

    # Hash for audit
    map_hash: str = ""

    def __post_init__(self):
        """Generate deterministic bijection on initialization."""
        self._generate_bijection()

    def _generate_bijection(self) -> None:
        """
        Generate deterministic bijection from seed.

        Uses hash-based shuffling to create a stable permutation.
        """
        # Create deterministic seed for shuffling
        seed_material = f"{self.global_seed}:{self.run_id}:{self.ablation_spec}"
        seed_hash = hashlib.sha256(seed_material.encode()).hexdigest()

        # Sort canonical IDs for determinism
        actions = sorted(CANONICAL_ACTION_IDS)
        preferences = sorted(CANONICAL_PREFERENCE_IDS)
        beliefs = sorted(CANONICAL_BELIEF_IDS)

        # Shuffle using hash-based permutation
        actions_shuffled = self._hash_shuffle(actions, seed_hash, "actions")
        preferences_shuffled = self._hash_shuffle(preferences, seed_hash, "preferences")
        beliefs_shuffled = self._hash_shuffle(beliefs, seed_hash, "beliefs")

        # Build forward maps (canonical → opaque)
        self.action_map = {
            canonical: f"A_{i+1:03d}"
            for i, canonical in enumerate(actions_shuffled)
        }
        self.preference_map = {
            canonical: f"P_{i+1:03d}"
            for i, canonical in enumerate(preferences_shuffled)
        }
        self.belief_map = {
            canonical: f"B_{i+1:03d}"
            for i, canonical in enumerate(beliefs_shuffled)
        }

        # Build inverse maps (opaque → canonical)
        self.action_map_inv = {v: k for k, v in self.action_map.items()}
        self.preference_map_inv = {v: k for k, v in self.preference_map.items()}
        self.belief_map_inv = {v: k for k, v in self.belief_map.items()}

        # Combined maps
        self.forward_map = {
            **self.action_map,
            **self.preference_map,
            **self.belief_map,
        }
        self.inverse_map = {
            **self.action_map_inv,
            **self.preference_map_inv,
            **self.belief_map_inv,
        }

        # Compute hash for audit
        map_content = json.dumps(self.forward_map, sort_keys=True)
        self.map_hash = hashlib.sha256(map_content.encode()).hexdigest()[:16]

    def _hash_shuffle(
        self,
        items: List[str],
        seed_hash: str,
        category: str,
    ) -> List[str]:
        """
        Deterministically shuffle items using hash-based sorting.

        Each item gets a hash-derived sort key for stable permutation.
        """
        def sort_key(item: str) -> str:
            key_material = f"{seed_hash}:{category}:{item}"
            return hashlib.sha256(key_material.encode()).hexdigest()

        return sorted(items, key=sort_key)

    def obfuscate(self, text: str) -> str:
        """
        Apply forward bijection to text.

        Replaces all canonical IDs with their obfuscated counterparts.
        Uses word-boundary matching to avoid partial replacements.
        """
        result = text

        # Sort by length descending to handle longer IDs first
        # (e.g., "P_NO_BREAK_LOCKS" before "BREAK_LOCK")
        sorted_ids = sorted(self.forward_map.keys(), key=len, reverse=True)

        for canonical in sorted_ids:
            obfuscated = self.forward_map[canonical]
            # Use word boundary matching
            pattern = r'\b' + re.escape(canonical) + r'\b'
            result = re.sub(pattern, obfuscated, result)

        return result

    def deobfuscate(self, text: str) -> str:
        """
        Apply inverse bijection to text.

        Replaces all obfuscated IDs with their canonical counterparts.
        """
        result = text

        # Sort by length descending (though all opaque IDs are same length)
        sorted_ids = sorted(self.inverse_map.keys(), key=len, reverse=True)

        for obfuscated in sorted_ids:
            canonical = self.inverse_map[obfuscated]
            # Use word boundary matching
            pattern = r'\b' + re.escape(obfuscated) + r'\b'
            result = re.sub(pattern, canonical, result)

        return result

    def obfuscate_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply forward bijection to all string values in an artifact.

        Recursively processes nested dicts and lists.
        """
        return self._transform_artifact(artifact, self.obfuscate)

    def deobfuscate_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply inverse bijection to all string values in an artifact.

        Recursively processes nested dicts and lists.
        """
        return self._transform_artifact(artifact, self.deobfuscate)

    def _transform_artifact(
        self,
        value: Any,
        transform_fn,
    ) -> Any:
        """Recursively transform string values in nested structure."""
        if isinstance(value, dict):
            return {
                k: self._transform_artifact(v, transform_fn)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            return [self._transform_artifact(item, transform_fn) for item in value]
        elif isinstance(value, str):
            return transform_fn(value)
        else:
            return value

    def get_obfuscated_action_set(self) -> Set[str]:
        """Return set of obfuscated action IDs."""
        return set(self.action_map.values())

    def get_obfuscated_preference_set(self) -> Set[str]:
        """Return set of obfuscated preference IDs."""
        return set(self.preference_map.values())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for telemetry."""
        return {
            "global_seed": self.global_seed,
            "run_id": self.run_id,
            "ablation_spec": self.ablation_spec,
            "map_hash": self.map_hash,
            "action_count": len(self.action_map),
            "preference_count": len(self.preference_map),
            "belief_count": len(self.belief_map),
        }


# ============================================================================
# Semantic Leakage Detector
# ============================================================================

@dataclass
class LeakageCheckResult:
    """Result of semantic leakage check."""
    passed: bool
    leaked_ids: List[str] = field(default_factory=list)
    leak_locations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "leaked_ids": self.leaked_ids,
            "leak_locations": self.leak_locations[:10],  # Limit for telemetry
        }


def check_semantic_leakage(
    obfuscated_text: str,
    canonical_ids: Optional[Set[str]] = None,
    check_gloss: bool = True,
) -> LeakageCheckResult:
    """
    Check if obfuscated text contains any canonical IDs or gloss strings.

    Binding: If this returns passed=False, the run MUST fail with
    INVALID_RUN/SEMANTIC_LEAK.

    No-gloss constraint (BINDING): Also detects English gloss strings that
    leak semantic meaning even when IDs are obfuscated. This prevents the
    typical failure mode where IDs are hidden but explanatory text reveals
    the mapping.

    Args:
        obfuscated_text: The text that should be free of canonical IDs/gloss
        canonical_ids: Set of IDs to check for (defaults to all canonical IDs)
        check_gloss: Whether to also check for gloss strings (default True)

    Returns:
        LeakageCheckResult with passed=True if no leaks found
    """
    if canonical_ids is None:
        canonical_ids = (
            CANONICAL_ACTION_IDS |
            CANONICAL_PREFERENCE_IDS |
            CANONICAL_BELIEF_IDS
        )

    leaked_ids = []
    leak_locations = []

    # Check canonical IDs (case-sensitive)
    for canonical_id in canonical_ids:
        # Use word boundary matching
        pattern = r'\b' + re.escape(canonical_id) + r'\b'
        matches = list(re.finditer(pattern, obfuscated_text))

        if matches:
            leaked_ids.append(canonical_id)
            for match in matches[:3]:  # Limit locations per ID
                start = max(0, match.start() - 20)
                end = min(len(obfuscated_text), match.end() + 20)
                context = obfuscated_text[start:end]
                leak_locations.append(f"...{context}...")

    # Check gloss strings (case-insensitive) - NO-GLOSS CONSTRAINT
    if check_gloss:
        text_lower = obfuscated_text.lower()
        for gloss in CANONICAL_GLOSS_STRINGS:
            # Use word boundary matching (gloss is already lowercase)
            pattern = r'\b' + re.escape(gloss) + r'\b'
            matches = list(re.finditer(pattern, text_lower))

            if matches:
                leaked_ids.append(f"GLOSS:{gloss}")
                for match in matches[:3]:  # Limit locations per gloss
                    start = max(0, match.start() - 20)
                    end = min(len(obfuscated_text), match.end() + 20)
                    # Get context from original text (preserve case)
                    context = obfuscated_text[start:end]
                    leak_locations.append(f"...{context}...")

    return LeakageCheckResult(
        passed=len(leaked_ids) == 0,
        leaked_ids=leaked_ids,
        leak_locations=leak_locations,
    )


# ============================================================================
# Prompt Semantic Excision Filter
# ============================================================================

@dataclass
class PromptExcisionResult:
    """Result of applying prompt semantic excision."""
    obfuscated_prompt: str
    canonical_prompt_hash: str
    obfuscated_prompt_hash: str
    map_hash: str
    obfuscated_symbol_count: int
    leakage_check: LeakageCheckResult
    traces_removed: bool = True


class PromptSemanticExcisionFilter:
    """
    Applies prompt-level semantic excision for Run AA.

    Responsibilities:
    1. Obfuscate all action/preference/belief IDs in prompt
    2. Remove derivation traces from prompt
    3. Check for semantic leakage
    4. Log hashes for reproducibility

    Binding: This filter operates BEFORE LLM invocation.
    """

    def __init__(self, obfuscation_map: IdObfuscationMap):
        """
        Initialize filter with obfuscation map.

        Args:
            obfuscation_map: Deterministic bijection for this run
        """
        self.obfuscation_map = obfuscation_map
        self.last_result: Optional[PromptExcisionResult] = None

    def apply(self, prompt: str, remove_traces: bool = True) -> PromptExcisionResult:
        """
        Apply prompt-level semantic excision.

        Args:
            prompt: The canonical prompt to obfuscate
            remove_traces: Whether to remove derivation trace sections

        Returns:
            PromptExcisionResult with obfuscated prompt and telemetry
        """
        # Hash canonical prompt
        canonical_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        # Count symbols before obfuscation
        symbol_count = self._count_canonical_symbols(prompt)

        # Remove derivation traces if requested
        if remove_traces:
            prompt = self._remove_trace_sections(prompt)

        # Apply obfuscation
        obfuscated = self.obfuscation_map.obfuscate(prompt)

        # Hash obfuscated prompt
        obfuscated_hash = hashlib.sha256(obfuscated.encode()).hexdigest()[:16]

        # Check for leakage
        leakage_check = check_semantic_leakage(obfuscated)

        result = PromptExcisionResult(
            obfuscated_prompt=obfuscated,
            canonical_prompt_hash=canonical_hash,
            obfuscated_prompt_hash=obfuscated_hash,
            map_hash=self.obfuscation_map.map_hash,
            obfuscated_symbol_count=symbol_count,
            leakage_check=leakage_check,
            traces_removed=remove_traces,
        )

        self.last_result = result
        return result

    def _count_canonical_symbols(self, text: str) -> int:
        """Count how many canonical symbols appear in text."""
        count = 0
        for canonical_id in self.obfuscation_map.forward_map.keys():
            pattern = r'\b' + re.escape(canonical_id) + r'\b'
            count += len(re.findall(pattern, text))
        return count

    def _remove_trace_sections(self, prompt: str) -> str:
        """
        Remove derivation trace sections from prompt.

        Traces often contain semantic descriptors that leak meaning.
        For Run AA, we exclude traces to avoid confounding with Run D.
        """
        # Remove sections marked as derivation traces
        patterns = [
            r'# Derivation Trace.*?(?=\n#|\n---|\Z)',
            r'## Trace.*?(?=\n#|\n---|\Z)',
            r'derivation_trace:.*?(?=\n[a-z]|\n#|\Z)',
            r'Previous reasoning:.*?(?=\n\n|\Z)',
            r'Justification history:.*?(?=\n\n|\Z)',
        ]

        result = prompt
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)

        return result


# ============================================================================
# J_raw De-obfuscation
# ============================================================================

def deobfuscate_artifact(
    artifact: Dict[str, Any],
    obfuscation_map: IdObfuscationMap,
) -> Dict[str, Any]:
    """
    De-obfuscate J_raw after LLM generation.

    Binding: This is applied immediately after LLM returns,
    before FA/compiler processing.

    Args:
        artifact: J_raw with obfuscated IDs from LLM
        obfuscation_map: The bijection used for obfuscation

    Returns:
        J_raw with canonical IDs restored
    """
    return obfuscation_map.deobfuscate_artifact(artifact)


# ============================================================================
# APCM Obfuscation
# ============================================================================

def obfuscate_apcm(
    apcm: Dict[str, Dict[str, Set[str]]],
    obfuscation_map: IdObfuscationMap,
) -> Dict[str, Dict[str, Set[str]]]:
    """
    Obfuscate APCM structure for prompt.

    APCM maps action_id → {violates: {pref_ids}, satisfies: {pref_ids}}

    Both action IDs and preference IDs must be obfuscated.
    """
    result = {}

    for action_id, constraints in apcm.items():
        obf_action = obfuscation_map.obfuscate(action_id)
        result[obf_action] = {
            "violates": {
                obfuscation_map.obfuscate(pref_id)
                for pref_id in constraints.get("violates", set())
            },
            "satisfies": {
                obfuscation_map.obfuscate(pref_id)
                for pref_id in constraints.get("satisfies", set())
            },
        }

    return result


def obfuscate_feasible_actions(
    feasible_actions: List[str],
    obfuscation_map: IdObfuscationMap,
) -> List[str]:
    """Obfuscate list of feasible action IDs."""
    return [obfuscation_map.obfuscate(action) for action in feasible_actions]


# ============================================================================
# Run AA Generator Wrapper
# ============================================================================

@dataclass
class RunAAStepTelemetry:
    """Telemetry for a single Run AA step."""
    canonical_prompt_hash: str
    obfuscated_prompt_hash: str
    map_hash: str
    obfuscated_symbol_count: int
    leakage_check_passed: bool
    leaked_ids: List[str]
    traces_removed: bool
    deobfuscation_applied: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_prompt_hash": self.canonical_prompt_hash,
            "obfuscated_prompt_hash": self.obfuscated_prompt_hash,
            "map_hash": self.map_hash,
            "obfuscated_symbol_count": self.obfuscated_symbol_count,
            "leakage_check_passed": self.leakage_check_passed,
            "leaked_ids": self.leaked_ids,
            "traces_removed": self.traces_removed,
            "deobfuscation_applied": self.deobfuscation_applied,
        }


class LLMGeneratorWithPromptAblation:
    """
    Wrapper for LLM generator that applies Run AA prompt-level ablation.

    Pipeline:
    1. Build canonical prompt (normal v2.3 generator)
    2. Apply obfuscation to prompt (IdObfuscationMap)
    3. Check for leakage (fail if canonical IDs or gloss found)
    4. Call LLM with obfuscated prompt
    5. De-obfuscate J_raw
    6. Return canonical J_raw for FA/compiler

    Binding: This operates BEFORE LLM invocation, at the actual causal
    locus where semantic reasoning occurs.
    """

    def __init__(
        self,
        base_generator,  # LLMGeneratorV230
        obfuscation_map: IdObfuscationMap,
    ):
        """
        Initialize Run AA generator wrapper.

        Args:
            base_generator: The underlying v2.3 LLM generator
            obfuscation_map: Deterministic bijection for this run
        """
        self.base_generator = base_generator
        self.obfuscation_map = obfuscation_map
        self.excision_filter = PromptSemanticExcisionFilter(obfuscation_map)
        self.last_telemetry: Optional[RunAAStepTelemetry] = None
        self._leakage_failure: bool = False
        self._leaked_ids: List[str] = []

    def reset(self):
        """Reset for new episode."""
        self.base_generator.reset()
        self._leakage_failure = False
        self._leaked_ids = []

    @property
    def had_leakage_failure(self) -> bool:
        """Check if last generation had leakage failure."""
        return self._leakage_failure

    @property
    def leaked_ids(self) -> List[str]:
        """Get list of leaked IDs from last generation."""
        return self._leaked_ids

    def generate_raw(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str,
        exists_clean: bool,
        previous_artifact_digest: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate justification artifact with prompt-level ablation.

        This is the main entry point for Run AA generation.

        Returns:
            J_raw with canonical IDs (de-obfuscated after LLM generation)

        Raises:
            SemanticLeakageError: If obfuscated prompt contains canonical IDs/gloss
        """
        self._leakage_failure = False
        self._leaked_ids = []

        # Step 1: Obfuscate inputs for prompt building
        obf_feasible = obfuscate_feasible_actions(feasible_actions, self.obfuscation_map)
        obf_apcm = obfuscate_apcm(apcm, self.obfuscation_map)

        # Step 2: Build prompt with obfuscated inputs
        # We need to intercept the prompt building, so we call the private method
        prompt = self.base_generator._build_prompt(
            feasible_actions=obf_feasible,
            apcm=obf_apcm,
            attempt=1,
            agent_id=agent_id,
            exists_clean=exists_clean,
            previous_artifact_digest=previous_artifact_digest,
        )

        # Step 3: Apply additional obfuscation to any remaining canonical IDs
        # and remove derivation traces
        excision_result = self.excision_filter.apply(prompt, remove_traces=True)

        # Step 4: Check for leakage (BINDING: fail if detected)
        if not excision_result.leakage_check.passed:
            self._leakage_failure = True
            self._leaked_ids = excision_result.leakage_check.leaked_ids
            # Record telemetry even on failure
            self.last_telemetry = RunAAStepTelemetry(
                canonical_prompt_hash=excision_result.canonical_prompt_hash,
                obfuscated_prompt_hash=excision_result.obfuscated_prompt_hash,
                map_hash=excision_result.map_hash,
                obfuscated_symbol_count=excision_result.obfuscated_symbol_count,
                leakage_check_passed=False,
                leaked_ids=self._leaked_ids,
                traces_removed=excision_result.traces_removed,
                deobfuscation_applied=False,
            )
            raise SemanticLeakageError(
                f"Semantic leakage detected: {self._leaked_ids}"
            )

        # Step 5: Call LLM with obfuscated prompt
        obfuscated_prompt = excision_result.obfuscated_prompt
        j_raw_obfuscated = self.base_generator._generate_with_prompt(obfuscated_prompt)

        # Step 6: De-obfuscate J_raw
        j_raw = deobfuscate_artifact(j_raw_obfuscated, self.obfuscation_map)

        # Record telemetry
        self.last_telemetry = RunAAStepTelemetry(
            canonical_prompt_hash=excision_result.canonical_prompt_hash,
            obfuscated_prompt_hash=excision_result.obfuscated_prompt_hash,
            map_hash=excision_result.map_hash,
            obfuscated_symbol_count=excision_result.obfuscated_symbol_count,
            leakage_check_passed=True,
            leaked_ids=[],
            traces_removed=excision_result.traces_removed,
            deobfuscation_applied=True,
        )

        return j_raw


class SemanticLeakageError(Exception):
    """Raised when semantic leakage is detected in obfuscated prompt."""
    pass
