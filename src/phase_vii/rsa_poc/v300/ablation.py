"""v3.0 Ablation Types and Configuration

Core types for the ablation defense framework:
- AblationSpec: which component to ablate
- AblationConfig: full run configuration
- AblationClassification: outcome taxonomy
- AblationResult: run results with classification
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
from datetime import datetime


# ============================================================================
# Ablation Specification (Binding)
# ============================================================================

class AblationSpec(Enum):
    """
    Which component to ablate.

    Only one ablation per run. Combined ablations are forbidden.

    Execution order per spec: D → A → AA → B → C
    """
    NONE = "none"  # Baseline: full v2.3 agent, no ablation
    SEMANTIC_EXCISION = "semantic_excision"  # A: Remove semantic payloads (CLOSED - N/A for ID-based schemas)
    PROMPT_SEMANTIC_EXCISION = "prompt_semantic_excision"  # AA: Obfuscate IDs in generator prompt
    REFLECTION_EXCISION = "reflection_excision"  # B: Disable normative updates
    PERSISTENCE_EXCISION = "persistence_excision"  # C: Clear state at episode boundaries
    TRACE_EXCISION = "trace_excision"  # D: Remove derivation evidence [GOLDEN TEST]


class InvalidRunReason(Enum):
    """
    Reasons a run is classified as INVALID_RUN.

    Invalid runs do not count as collapse evidence.
    """
    NONE = "none"
    # Protocol violations
    MULTIPLE_ABLATIONS = "multiple_ablations"  # More than one component ablated
    PARTIAL_ABLATION = "partial_ablation"  # Ablation incompletely applied
    COMPENSATION_ADDED = "compensation_added"  # New structure added to "help"
    REINTERPRETATION = "reinterpretation"  # Collapse via interpretation, not mechanics
    # Technical failures (don't count as collapse)
    SCHEMA_CRASH = "schema_crash"  # Schema validation exception
    NULL_POINTER = "null_pointer"  # Null dereference
    MISSING_FIELD_EXCEPTION = "missing_field_exception"  # Required field access crash
    STATIC_TYPE_ERROR = "static_type_error"  # Type system failure
    GENERATOR_REFUSAL = "generator_refusal"  # LLM refused due to unreadable prompt
    # Run AA specific
    SEMANTIC_LEAK = "semantic_leak"  # Canonical IDs found in obfuscated prompt
    # Harness violations
    FALLBACK_SUBSTITUTION = "fallback_substitution"  # Action authorship violated
    ABLATION_PROTOCOL_VIOLATION = "ablation_protocol_violation"  # General protocol failure


class AblationClassification(Enum):
    """
    Outcome classification for valid ablation runs.

    From RSA-PoC failure taxonomy. "Still agent-like" is NOT a category.
    """
    # Collapse modes (expected outcomes for valid ablations)
    NARRATIVE_COLLAPSE = "narrative_collapse"  # Constraints no longer bind meaningfully
    INCENTIVE_CAPTURE = "incentive_capture"  # Drift to reward-following
    ONTOLOGICAL_COLLAPSE = "ontological_collapse"  # System reduces to mechanism
    ASB_CLASS_REDUCIBILITY = "asb_class_reducibility"  # Indistinguishable from null baseline
    # Invalid run (doesn't count)
    INVALID_RUN = "invalid_run"


# ============================================================================
# Ablation Configuration
# ============================================================================

@dataclass(frozen=True)
class AblationConfig:
    """
    Full configuration for a v3.0 ablation run.

    Baseline and ablated runs must share:
    - environment
    - seeds
    - prompts (except as modified by ablation)
    - compiler
    - harness
    - audits
    """
    # Run identification
    run_id: str

    # Ablation specification
    ablation: AblationSpec

    # Seed configuration (minimum 5 for multi-seed requirement)
    seeds: List[int] = field(default_factory=lambda: [42, 123, 456, 789, 1024])

    # Episode configuration
    num_episodes: int = 3
    steps_per_episode: int = 50

    # Environment (binding: CommitmentTrapV200)
    environment: str = "CommitmentTrapV200"

    # SAM mode (binding: no SAM for v3.0 baseline)
    use_sam: bool = False  # v3.0 baseline = no strategic adversary
    friction_modifier: float = 1.0  # Neutral friction

    # Validation flags
    validate_single_ablation: bool = True
    validate_no_compensation: bool = True
    validate_action_authorship: bool = True

    def __post_init__(self):
        """Validate configuration constraints."""
        if len(self.seeds) < 5:
            raise ValueError("v3.0 requires minimum 5 preregistered seeds")
        if self.use_sam and self.ablation != AblationSpec.NONE:
            # Warning: SAM + ablation is a secondary experiment, not core v3.0
            pass


# ============================================================================
# Ablation Result
# ============================================================================

@dataclass
class SeedResult:
    """Result for a single seed in an ablation run."""
    seed: int
    classification: AblationClassification
    invalid_reason: InvalidRunReason = InvalidRunReason.NONE

    # Metrics (diagnostic only, no optimization)
    compilation_success_rate: float = 0.0
    feasible_action_set_size_mean: float = 0.0
    action_distribution_divergence: float = 0.0  # vs baseline
    gridlock_rate: float = 0.0
    halt_rate: float = 0.0
    audit_failure_count: int = 0
    asb_equivalence_score: float = 0.0  # 1.0 = indistinguishable from ASB null

    # BINDING METRICS (v3.0 Ablation A/B/C instrumentation)
    # Ratio of steps where constraints affected action selection
    binding_ratio: float = 0.0
    # Mean constraint strength (actions removed per step) for baseline
    binding_strength_baseline: float = 0.0
    # Mean constraint strength for ablated run
    binding_strength_ablated: float = 0.0

    # TELEMETRY aggregates
    # Total fields replaced by ablation filter across all steps
    total_ablation_replacements: int = 0
    # Mean replacements per step
    mean_ablation_replacements_per_step: float = 0.0

    # Error tracking
    technical_failures: List[str] = field(default_factory=list)
    action_authorship_violations: int = 0

    # Raw data
    episode_summaries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AblationResult:
    """
    Complete result for an ablation run across all seeds.
    """
    # Configuration
    config: AblationConfig

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Per-seed results
    seed_results: List[SeedResult] = field(default_factory=list)

    # Aggregate classification
    aggregate_classification: Optional[AblationClassification] = None
    classification_consistent: bool = False  # True if same across all seeds

    # Validity
    all_seeds_valid: bool = False
    invalid_seeds: List[int] = field(default_factory=list)

    # Comparison to baseline
    baseline_divergence: float = 0.0  # How different from baseline
    asb_similarity: float = 0.0  # How similar to ASB null

    def compute_aggregate(self) -> None:
        """Compute aggregate classification from seed results."""
        valid_results = [r for r in self.seed_results
                        if r.classification != AblationClassification.INVALID_RUN]

        if not valid_results:
            self.aggregate_classification = AblationClassification.INVALID_RUN
            self.classification_consistent = False
            self.all_seeds_valid = False
            return

        # Check consistency
        classifications = [r.classification for r in valid_results]
        unique_classifications = set(classifications)

        self.classification_consistent = len(unique_classifications) == 1
        self.all_seeds_valid = len(valid_results) == len(self.seed_results)

        # Aggregate is the most common classification (or first if tie)
        from collections import Counter
        counts = Counter(classifications)
        self.aggregate_classification = counts.most_common(1)[0][0]

        # Track invalid seeds
        self.invalid_seeds = [r.seed for r in self.seed_results
                             if r.classification == AblationClassification.INVALID_RUN]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON output."""
        return {
            "config": {
                "run_id": self.config.run_id,
                "ablation": self.config.ablation.value,
                "seeds": self.config.seeds,
                "num_episodes": self.config.num_episodes,
                "steps_per_episode": self.config.steps_per_episode,
                "environment": self.config.environment,
            },
            "timing": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
            },
            "seed_results": [
                {
                    "seed": r.seed,
                    "classification": r.classification.value,
                    "invalid_reason": r.invalid_reason.value,
                    "compilation_success_rate": r.compilation_success_rate,
                    "gridlock_rate": r.gridlock_rate,
                    "asb_equivalence_score": r.asb_equivalence_score,
                    "technical_failures": r.technical_failures,
                    "action_authorship_violations": r.action_authorship_violations,
                }
                for r in self.seed_results
            ],
            "aggregate": {
                "classification": self.aggregate_classification.value if self.aggregate_classification else None,
                "consistent": self.classification_consistent,
                "all_valid": self.all_seeds_valid,
                "invalid_seeds": self.invalid_seeds,
            },
        }


# ============================================================================
# Ablation Filters (Post-FA Transformers)
# ============================================================================

class AblationFilter:
    """
    Base class for ablation filters applied after Formal Assistant.

    Filters transform J_final → J_final' by removing/replacing
    the ablated component while preserving structure.
    """

    def __init__(self, ablation: AblationSpec):
        self.ablation = ablation

    def apply(self, j_final: Dict[str, Any]) -> Dict[str, Any]:
        """Apply ablation transformation. Override in subclasses."""
        raise NotImplementedError


class SemanticExcisionFilter(AblationFilter):
    """
    Ablation A: Remove semantic payloads.

    Replaces belief/preference/justification text with opaque tokens.
    Preserves: IDs, arity, typing, structure, list lengths.

    After apply(), check:
    - self.last_replacement_count: number of fields replaced
    - self.last_replaced_paths: list of replaced field paths (capped at 25)
    """

    def __init__(self):
        super().__init__(AblationSpec.SEMANTIC_EXCISION)
        self._token_counter = 0
        self.last_replacement_count = 0
        self.last_replaced_paths: List[str] = []

    def _next_token(self) -> str:
        """Generate next opaque token."""
        import hashlib
        import time
        self._token_counter += 1
        hash_input = f"{time.time()}_{self._token_counter}"
        hash_hex = hashlib.md5(hash_input.encode()).hexdigest()[:6]
        return f"<SEMANTIC_EXCISED_TOKEN_{hash_hex}>"

    def apply(self, j_final: Dict[str, Any]) -> Dict[str, Any]:
        """Replace semantic content with opaque tokens."""
        import copy
        result = copy.deepcopy(j_final)

        # Reset counters
        self.last_replacement_count = 0
        self.last_replaced_paths = []

        # Fields to tokenize (semantic payloads) - exact names
        # These are fields that contain human-readable semantic content
        # as opposed to IDs, codes, hashes, or structural markers
        #
        # IMPORTANT: Do NOT include structural fields like:
        # - expected_constraint_effect (enum: NO_CONSTRAINT, FORBID, etc.)
        # - relation (enum: SATISFIES, VIOLATES, etc.)
        # - mode (enum: MAINTAIN, REVISE, etc.)
        # - binding_strength (enum: HARD, SOFT, etc.)
        #
        # Only include fields that contain free-form explanatory text.
        SEMANTIC_FIELDS = {
            # Core semantic payload fields (free-form text)
            "text", "content", "description", "explanation",
            "reason", "rationale", "justification", "narrative",
            "belief_content", "preference_content", "goal_description",
            "constraint_explanation", "refusal_reason",
            "semantic_content",  # Test fixture field
            # Extended set for any explanatory/narrative fields
            "note", "notes", "comment", "comments",
            "summary", "message", "details",
        }

        def tokenize_recursive(value: Any, path: str = "") -> Any:
            if isinstance(value, dict):
                new_dict = {}
                for k, v in value.items():
                    if k in SEMANTIC_FIELDS and isinstance(v, str):
                        # Replace semantic string with token
                        new_dict[k] = self._next_token()
                        self.last_replacement_count += 1
                        if len(self.last_replaced_paths) < 25:
                            self.last_replaced_paths.append(f"{path}.{k}" if path else k)
                    else:
                        new_dict[k] = tokenize_recursive(v, f"{path}.{k}" if path else k)
                return new_dict
            elif isinstance(value, list):
                return [tokenize_recursive(item, f"{path}[{i}]")
                        for i, item in enumerate(value)]
            else:
                return value

        return tokenize_recursive(result)


class ReflectionExcisionFilter(AblationFilter):
    """
    Ablation B: Disable normative updates.

    Removes normative_update / revision fields.
    Freezes normative state at initial value.
    """

    def __init__(self):
        super().__init__(AblationSpec.REFLECTION_EXCISION)

    def apply(self, j_final: Dict[str, Any]) -> Dict[str, Any]:
        """Remove normative update structures and clear reflection history."""
        import copy
        result = copy.deepcopy(j_final)

        # Fields that indicate normative self-update
        REFLECTION_FIELDS = {
            "normative_update", "state_update", "revision",
            "self_revision", "commitment_update", "preference_update",
            "belief_revision", "norm_transition",
        }

        def remove_reflection(value: Any) -> Any:
            if isinstance(value, dict):
                new_dict = {}
                for k, v in value.items():
                    if k in REFLECTION_FIELDS:
                        continue  # Skip reflection fields
                    elif k == "reflection_history":
                        # Clear reflection history (empty list)
                        new_dict[k] = []
                    else:
                        new_dict[k] = remove_reflection(v)
                return new_dict
            elif isinstance(value, list):
                return [remove_reflection(item) for item in value]
            else:
                return value

        result = remove_reflection(result)
        result["_normative_updates_frozen"] = True
        return result


class PersistenceExcisionFilter(AblationFilter):
    """
    Ablation C: Disable cross-episode persistence.

    Note: This filter doesn't transform J_final directly.
    Instead, the harness must clear normative state at episode boundaries.
    The filter marks artifacts to prevent carryover attempts.
    """

    def __init__(self):
        super().__init__(AblationSpec.PERSISTENCE_EXCISION)

    def apply(self, j_final: Dict[str, Any]) -> Dict[str, Any]:
        """Mark artifact as non-persistent."""
        import copy
        result = copy.deepcopy(j_final)

        # Add marker to prevent persistence
        result["_ablation_no_persist"] = True

        # Remove any persistence-related fields
        PERSISTENCE_FIELDS = {
            "persist", "carry_forward", "remember", "store_commitment",
            "episode_memory", "cross_episode",
        }

        def remove_persistence(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: remove_persistence(v)
                        for k, v in value.items()
                        if k.lower() not in PERSISTENCE_FIELDS}
            elif isinstance(value, list):
                return [remove_persistence(item) for item in value]
            else:
                return value

        return remove_persistence(result)


class TraceExcisionFilter(AblationFilter):
    """
    Ablation D: Remove derivation evidence (GOLDEN TEST).

    Removes derivation_trace, rule_refs, proof objects.
    Preserves constraint emission interface.

    If constraints still bind without traces, justifications were epiphenomenal.
    This falsifies the entire RSA-PoC program.
    """

    def __init__(self):
        super().__init__(AblationSpec.TRACE_EXCISION)

    def apply(self, j_final: Dict[str, Any]) -> Dict[str, Any]:
        """Remove derivation evidence while preserving constraints."""
        import copy
        result = copy.deepcopy(j_final)

        # Derivation evidence fields (the "trace") - exact names
        TRACE_FIELDS = {
            "derivation_trace", "derivation", "proof",
            "rule_refs", "rule_application", "inference_chain",
            "reasoning_steps", "derivation_path", "proof_object",
            "belief_to_constraint", "premise_refs",
            "justification_trace",  # Exact match
        }

        def remove_traces(value: Any) -> Any:
            if isinstance(value, dict):
                new_dict = {}
                for k, v in value.items():
                    if k in TRACE_FIELDS:
                        continue  # Remove trace fields entirely
                    else:
                        new_dict[k] = remove_traces(v)
                return new_dict
            elif isinstance(value, list):
                return [remove_traces(item) for item in value]
            else:
                return value

        return remove_traces(result)


def create_ablation_filter(ablation: AblationSpec) -> Optional[AblationFilter]:
    """Factory for ablation filters."""
    if ablation == AblationSpec.NONE:
        return None
    elif ablation == AblationSpec.SEMANTIC_EXCISION:
        return SemanticExcisionFilter()
    elif ablation == AblationSpec.REFLECTION_EXCISION:
        return ReflectionExcisionFilter()
    elif ablation == AblationSpec.PERSISTENCE_EXCISION:
        return PersistenceExcisionFilter()
    elif ablation == AblationSpec.TRACE_EXCISION:
        return TraceExcisionFilter()
    elif ablation == AblationSpec.PROMPT_SEMANTIC_EXCISION:
        # Run AA: Prompt-level ablation happens BEFORE LLM, not in post-FA filter.
        # Return None here; the harness handles Run AA separately.
        return None
    else:
        raise ValueError(f"Unknown ablation: {ablation}")
