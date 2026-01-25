"""v3.0 Infrastructure Tests

Tests for:
1. AblationSpec enum and single-ablation discipline
2. Ablation filters (A, B, C, D)
3. JCOMP300 with relaxation
4. SelectorTolerance defaults
5. ASB Null Agent
6. Validity gates
7. Classification logic

Key test invariants:
- "trace-missing but otherwise well-formed" fixture must pass schema under Ablation D
- "selector missing-field" fixture must not crash
- Classification must be exactly one of the taxonomy
"""

import pytest
from typing import Dict, Any
from dataclasses import asdict

# Import v3.0 components
from rsa_poc.v300.ablation import (
    AblationSpec,
    AblationConfig,
    AblationResult,
    AblationClassification,
    InvalidRunReason,
    SeedResult,
    SemanticExcisionFilter,
    ReflectionExcisionFilter,
    PersistenceExcisionFilter,
    TraceExcisionFilter,
    create_ablation_filter,
)
from rsa_poc.v300.compiler import (
    JCOMP300,
    AblationRelaxation,
    create_relaxation,
    SelectorTolerance,
    V300CompilationResult,
)
from rsa_poc.v300.asb_null import (
    ASBNullAgent,
    ASBNullConfig,
    ASBActionSelection,
    compute_asb_equivalence,
    is_asb_reducible,
)
from rsa_poc.v300.harness import (
    V300AblationHarness,
    V300RunConfig,
    ValidityGate,
    AblationClassifier,
    V300StepRecord,
    V300EpisodeRecord,
    ConstraintBindingMetrics,
    ConstraintBindingDetector,
    StepType,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def well_formed_constraint() -> Dict[str, Any]:
    """A well-formed v2.3 constraint with all fields."""
    return {
        "constraint_id": "C001",
        "axiom_source": "A1",
        "semantic_content": "Prevent harmful actions toward humans",
        "justification_trace": {
            "derivation": ["A1", "A1.1", "C001"],
            "reflection_history": [
                {
                    "step": 12,
                    "update": "Narrowed scope to immediate physical harm",
                    "reason": "Edge case clarification",
                }
            ],
        },
        "current_weight": 0.85,
        "binding_strength": "HARD",
        "preference_persistence": {
            "episode_0": 0.8,
            "episode_1": 0.85,
            "updates": 1,
        },
    }


@pytest.fixture
def trace_missing_constraint() -> Dict[str, Any]:
    """
    A constraint with justification_trace removed.

    Under Ablation D, this should pass schema.
    Under other modes, this should fail.
    """
    return {
        "constraint_id": "C001",
        "axiom_source": "A1",
        "semantic_content": "Prevent harmful actions toward humans",
        # justification_trace MISSING
        "current_weight": 0.85,
        "binding_strength": "HARD",
        "preference_persistence": {
            "episode_0": 0.8,
            "episode_1": 0.85,
            "updates": 1,
        },
    }


@pytest.fixture
def semantic_missing_constraint() -> Dict[str, Any]:
    """A constraint with semantic content replaced by opaque token."""
    return {
        "constraint_id": "C001",
        "axiom_source": "A1",
        "semantic_content": "<SEMANTIC_EXCISED_TOKEN_a3f7c2>",
        "justification_trace": {
            "derivation": ["<OPAQUE>"],
            "reflection_history": [],
        },
        "current_weight": 0.85,
        "binding_strength": "HARD",
        "preference_persistence": {
            "episode_0": 0.8,
            "episode_1": 0.85,
            "updates": 1,
        },
    }


@pytest.fixture
def selector_missing_field_context() -> Dict[str, Any]:
    """
    Selector context with missing field.

    Must not crash - should use SelectorTolerance defaults.
    """
    return {
        "step": 42,
        "feasible_actions": ["A", "B", "C"],
        # preferences MISSING
        # constraints MISSING
        "environment_state": {"position": [0, 0]},
    }


# ============================================================================
# AblationSpec Tests
# ============================================================================

class TestAblationSpec:
    """Tests for AblationSpec enum."""

    def test_ablation_spec_values(self):
        """Verify all four ablations exist."""
        assert AblationSpec.NONE.value == "none"
        assert AblationSpec.SEMANTIC_EXCISION.value == "semantic_excision"
        assert AblationSpec.REFLECTION_EXCISION.value == "reflection_excision"
        assert AblationSpec.PERSISTENCE_EXCISION.value == "persistence_excision"
        assert AblationSpec.TRACE_EXCISION.value == "trace_excision"

    def test_ablation_spec_from_string(self):
        """Verify string -> enum conversion."""
        assert AblationSpec("none") == AblationSpec.NONE
        assert AblationSpec("trace_excision") == AblationSpec.TRACE_EXCISION

    def test_single_ablation_discipline(self):
        """Verify enum enforces single ablation."""
        # Can only hold one value at a time
        ablation = AblationSpec.SEMANTIC_EXCISION
        assert ablation != AblationSpec.REFLECTION_EXCISION
        assert ablation != AblationSpec.PERSISTENCE_EXCISION
        assert ablation != AblationSpec.TRACE_EXCISION


# ============================================================================
# Ablation Filter Tests
# ============================================================================

class TestAblationFilters:
    """Tests for ablation filters."""

    def test_trace_excision_filter(self, well_formed_constraint):
        """Test Ablation D removes justification traces."""
        filter = TraceExcisionFilter()
        ablated = filter.apply(well_formed_constraint)

        # Trace should be removed or emptied
        assert "justification_trace" not in ablated or ablated.get("justification_trace") is None

        # Other fields preserved
        assert ablated["constraint_id"] == "C001"
        assert ablated["semantic_content"] == "Prevent harmful actions toward humans"
        assert ablated["current_weight"] == 0.85

    def test_semantic_excision_filter(self, well_formed_constraint):
        """Test Ablation A replaces semantic content with opaque tokens."""
        filter = SemanticExcisionFilter()
        ablated = filter.apply(well_formed_constraint)

        # Semantic content should be opaque token
        assert ablated["semantic_content"].startswith("<SEMANTIC_EXCISED_TOKEN_")

        # Other fields preserved
        assert ablated["constraint_id"] == "C001"
        assert ablated["current_weight"] == 0.85

    def test_reflection_excision_filter(self, well_formed_constraint):
        """Test Ablation B disables normative updates."""
        filter = ReflectionExcisionFilter()
        ablated = filter.apply(well_formed_constraint)

        # Reflection history should be cleared
        trace = ablated.get("justification_trace", {})
        if "reflection_history" in trace:
            assert len(trace["reflection_history"]) == 0

        # Should have freeze marker
        assert ablated.get("_normative_updates_frozen", False) == True

    def test_persistence_excision_filter(self, well_formed_constraint):
        """Test Ablation C clears persistence state."""
        filter = PersistenceExcisionFilter()
        ablated = filter.apply(well_formed_constraint)

        # Preference persistence should be cleared or marked
        assert ablated.get("_ablation_no_persist", False) == True

    def test_create_ablation_filter(self):
        """Test factory creates correct filter types."""
        assert isinstance(create_ablation_filter(AblationSpec.NONE), type(None)) or create_ablation_filter(AblationSpec.NONE) is None
        assert isinstance(create_ablation_filter(AblationSpec.SEMANTIC_EXCISION), SemanticExcisionFilter)
        assert isinstance(create_ablation_filter(AblationSpec.REFLECTION_EXCISION), ReflectionExcisionFilter)
        assert isinstance(create_ablation_filter(AblationSpec.PERSISTENCE_EXCISION), PersistenceExcisionFilter)
        assert isinstance(create_ablation_filter(AblationSpec.TRACE_EXCISION), TraceExcisionFilter)


# ============================================================================
# JCOMP300 Tests
# ============================================================================

class TestJCOMP300:
    """Tests for JCOMP-3.0 compiler with relaxation."""

    def test_no_relaxation_default(self):
        """Default compiler has no relaxation."""
        compiler = JCOMP300(ablation=AblationSpec.NONE)
        assert compiler.ablation == AblationSpec.NONE

    def test_trace_ablation_relaxation(self):
        """Ablation D relaxes trace requirements."""
        relaxation = create_relaxation(AblationSpec.TRACE_EXCISION)

        assert relaxation.allow_missing_justification_trace == True
        assert relaxation.allow_missing_semantic_content == False

    def test_semantic_ablation_relaxation(self):
        """Ablation A relaxes semantic requirements."""
        relaxation = create_relaxation(AblationSpec.SEMANTIC_EXCISION)

        assert relaxation.allow_opaque_semantic_tokens == True
        assert relaxation.allow_missing_justification_trace == False

    def test_trace_missing_constraint_passes_under_ablation_d(self, trace_missing_constraint):
        """
        CRITICAL: trace-missing constraint must pass schema under Ablation D.

        This is the key infrastructure invariant.
        """
        compiler = JCOMP300(ablation=AblationSpec.TRACE_EXCISION)

        # Simulate compilation
        result = compiler._validate_constraint_for_ablation(
            trace_missing_constraint,
            AblationSpec.TRACE_EXCISION,
        )

        assert result.valid == True
        assert result.fields_relaxed == ["justification_trace"]

    def test_trace_missing_constraint_fails_under_no_ablation(self, trace_missing_constraint):
        """trace-missing constraint must fail under normal compilation."""
        compiler = JCOMP300(ablation=AblationSpec.NONE)

        # Simulate compilation
        result = compiler._validate_constraint_for_ablation(
            trace_missing_constraint,
            AblationSpec.NONE,
        )

        assert result.valid == False
        assert "justification_trace" in result.missing_fields


# ============================================================================
# Selector Tolerance Tests
# ============================================================================

class TestSelectorTolerance:
    """Tests for selector tolerance under missing fields."""

    def test_selector_missing_field_no_crash(self, selector_missing_field_context):
        """
        CRITICAL: missing-field context must not crash selector.

        Should use uniform random over feasible actions.
        """
        tolerance = SelectorTolerance(
            default_action_mode="uniform_random_feasible",
            global_seed=42,
        )

        # Get default action
        action = tolerance.select_default(selector_missing_field_context)

        # Should return valid action from feasible set
        assert action in ["A", "B", "C"]

        # Should not crash
        assert action is not None

    def test_selector_tolerance_deterministic_mode(self, selector_missing_field_context):
        """Deterministic mode returns first feasible action."""
        tolerance = SelectorTolerance(
            default_action_mode="deterministic_first",
            global_seed=42,
        )

        action = tolerance.select_default(selector_missing_field_context)

        assert action == "A"  # First in list

    def test_selector_tolerance_seeded_random(self, selector_missing_field_context):
        """Seeded random is reproducible."""
        tolerance1 = SelectorTolerance(
            default_action_mode="uniform_random_feasible",
            global_seed=42,
        )
        tolerance2 = SelectorTolerance(
            default_action_mode="uniform_random_feasible",
            global_seed=42,
        )

        action1 = tolerance1.select_default(selector_missing_field_context)
        action2 = tolerance2.select_default(selector_missing_field_context)

        assert action1 == action2


# ============================================================================
# ASB Null Agent Tests
# ============================================================================

class TestASBNullAgent:
    """Tests for ASB-Class Null Agent baseline."""

    def test_asb_null_creation(self):
        """ASB Null Agent can be created."""
        config = ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=42,
        )
        agent = ASBNullAgent(config)

        assert agent is not None

    def test_asb_null_uniform_selection(self):
        """ASB Null selects uniformly from feasible actions."""
        config = ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=42,
        )
        agent = ASBNullAgent(config)

        feasible = {"A", "B", "C", "D"}
        action = agent.select_action(feasible, step=0, episode=0)

        assert action in feasible

    def test_asb_null_reproducible(self):
        """Same seed produces same sequence."""
        config1 = ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=42,
        )
        config2 = ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=42,
        )
        agent1 = ASBNullAgent(config1)
        agent2 = ASBNullAgent(config2)

        feasible = {"A", "B", "C", "D"}

        for step in range(10):
            a1 = agent1.select_action(feasible, step=step, episode=0)
            a2 = agent2.select_action(feasible, step=step, episode=0)
            assert a1 == a2

    def test_asb_null_different_seeds_differ(self):
        """Different seeds produce different sequences."""
        config1 = ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=42,
        )
        config2 = ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=123,
        )
        agent1 = ASBNullAgent(config1)
        agent2 = ASBNullAgent(config2)

        feasible = {"A", "B", "C", "D", "E", "F", "G", "H"}

        # Collect sequences
        seq1 = [agent1.select_action(feasible, step=i, episode=0) for i in range(20)]
        seq2 = [agent2.select_action(feasible, step=i, episode=0) for i in range(20)]

        # Should differ at some point
        assert seq1 != seq2


# ============================================================================
# ASB Equivalence Tests
# ============================================================================

class TestASBEquivalence:
    """Tests for ASB equivalence computation."""

    def test_identical_sequences_high_score(self):
        """Identical action sequences have high equivalence."""
        seq1 = ["A", "B", "C", "A", "B"]
        seq2 = ["A", "B", "C", "A", "B"]

        score = compute_asb_equivalence(seq1, seq2)

        assert score > 0.9

    def test_completely_different_low_score(self):
        """Completely different sequences have low equivalence."""
        seq1 = ["A", "A", "A", "A", "A"]
        seq2 = ["B", "B", "B", "B", "B"]

        score = compute_asb_equivalence(seq1, seq2)

        assert score < 0.3

    def test_threshold_check(self):
        """is_asb_reducible applies threshold correctly."""
        assert is_asb_reducible(0.9, threshold=0.85) == True
        assert is_asb_reducible(0.8, threshold=0.85) == False
        assert is_asb_reducible(0.85, threshold=0.85) == True

    def test_step_intersection_alignment(self):
        """ASB equivalence computes on intersection of executed steps (v3.0 Req 5)."""
        # Ablated ran steps 0-9, baseline ran steps 0-14
        ablated_actions = ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"]  # 10 steps
        ablated_indices = list(range(10))

        asb_actions = ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B", "C", "C", "C", "C", "C"]
        asb_indices = list(range(15))

        # Should compare only steps 0-9 (intersection)
        score = compute_asb_equivalence(
            ablated_actions,
            asb_actions,
            ablated_step_indices=ablated_indices,
            asb_step_indices=asb_indices,
        )

        # Identical on steps 0-9, should be high
        assert score > 0.9

    def test_step_intersection_empty(self):
        """No common steps returns 0."""
        ablated_actions = ["A", "B"]
        ablated_indices = [0, 1]

        asb_actions = ["C", "D"]
        asb_indices = [10, 11]  # No overlap

        score = compute_asb_equivalence(
            ablated_actions,
            asb_actions,
            ablated_step_indices=ablated_indices,
            asb_step_indices=asb_indices,
        )

        assert score == 0.0

    def test_different_length_no_indices_truncates(self):
        """Different lengths without indices truncates to minimum."""
        seq1 = ["A", "A", "A", "A", "A", "A", "A"]  # 7 steps
        seq2 = ["A", "A", "A"]  # 3 steps

        # Should compare only first 3 steps
        score = compute_asb_equivalence(seq1, seq2)

        # All "A" on first 3 steps, should be high
        assert score > 0.9


# ============================================================================
# Exception Logging Tests
# ============================================================================

class TestExceptionLogging:
    """Tests for hard exception logging (v3.0 Integration Requirement 7)."""

    def test_record_exception_sets_fields(self):
        """record_exception populates all exception fields."""
        step = V300StepRecord(
            step_index=5,
            episode_index=2,
            seed=42,
            action_id="A",
            feasible_actions=["A", "B"],
            ablation_applied=AblationSpec.TRACE_EXCISION,
        )

        test_exception = ValueError("Missing required field: justification_trace")
        step.record_exception(test_exception, call_site="compiler")

        assert step.is_technical_failure == True
        assert step.exception_class_name == "ValueError"
        assert step.exception_call_site == "compiler"
        assert step.exception_message == "Missing required field: justification_trace"
        assert step.technical_failure_type == "ValueError"

    def test_exception_log_line_format(self):
        """Exception log line includes step, episode, ablation, and details."""
        step = V300StepRecord(
            step_index=10,
            episode_index=3,
            seed=42,
            action_id="A",
            feasible_actions=["A", "B"],
            ablation_applied=AblationSpec.SEMANTIC_EXCISION,
        )

        step.record_exception(KeyError("semantic_content"), call_site="selector")
        log_line = step.get_exception_log_line()

        assert log_line is not None
        assert "step=10" in log_line
        assert "episode=3" in log_line
        assert "ablation=semantic_excision" in log_line
        assert "KeyError" in log_line
        assert "selector" in log_line

    def test_no_exception_returns_none(self):
        """get_exception_log_line returns None when no exception recorded."""
        step = V300StepRecord(
            step_index=0,
            episode_index=0,
            seed=42,
            action_id="A",
            feasible_actions=["A", "B"],
            ablation_applied=AblationSpec.NONE,
        )

        assert step.get_exception_log_line() is None

    def test_all_call_sites_valid(self):
        """Exception can be recorded from all valid call sites."""
        valid_sites = ["compiler", "selector", "executor", "filter"]

        for site in valid_sites:
            step = V300StepRecord(
                step_index=0,
                episode_index=0,
                seed=42,
                action_id="A",
                feasible_actions=["A", "B"],
                ablation_applied=AblationSpec.NONE,
            )
            step.record_exception(RuntimeError("test"), call_site=site)
            assert step.exception_call_site == site


# ============================================================================
# Validity Gate Tests
# ============================================================================

class TestValidityGate:
    """Tests for validity gate enforcement."""

    def test_action_authorship_valid(self):
        """Agent-authored action passes gate."""
        step = V300StepRecord(
            step_index=0,
            episode_index=0,
            seed=42,
            action_id="A",
            feasible_actions=["A", "B"],
            ablation_applied=AblationSpec.NONE,
            action_source="agent",
        )

        valid, reason = ValidityGate.check_action_authorship(step)

        assert valid == True
        assert reason is None

    def test_action_authorship_violation(self):
        """Harness-authored action fails gate."""
        step = V300StepRecord(
            step_index=0,
            episode_index=0,
            seed=42,
            action_id="A",
            feasible_actions=["A", "B"],
            ablation_applied=AblationSpec.NONE,
            action_source="harness_default",
        )

        valid, reason = ValidityGate.check_action_authorship(step)

        assert valid == False
        assert reason == InvalidRunReason.FALLBACK_SUBSTITUTION

    def test_technical_failure_detection(self):
        """Technical failures are detected."""
        step = V300StepRecord(
            step_index=0,
            episode_index=0,
            seed=42,
            action_id="A",
            feasible_actions=["A", "B"],
            ablation_applied=AblationSpec.NONE,
            is_technical_failure=True,
            technical_failure_type="missing_field_exception",
        )

        valid, reason = ValidityGate.check_not_technical_failure(step)

        assert valid == False
        assert reason == InvalidRunReason.MISSING_FIELD_EXCEPTION


# ============================================================================
# Classification Tests
# ============================================================================

class TestClassification:
    """Tests for ablation classification."""

    def test_classification_taxonomy_complete(self):
        """Verify all classification values exist."""
        assert AblationClassification.NARRATIVE_COLLAPSE.value == "narrative_collapse"
        assert AblationClassification.INCENTIVE_CAPTURE.value == "incentive_capture"
        assert AblationClassification.ONTOLOGICAL_COLLAPSE.value == "ontological_collapse"
        assert AblationClassification.ASB_CLASS_REDUCIBILITY.value == "asb_class_reducibility"
        assert AblationClassification.INVALID_RUN.value == "invalid_run"

    def test_invalid_reason_taxonomy_complete(self):
        """Verify all invalid reasons exist."""
        assert InvalidRunReason.NONE.value == "none"
        assert InvalidRunReason.MULTIPLE_ABLATIONS.value == "multiple_ablations"
        assert InvalidRunReason.SCHEMA_CRASH.value == "schema_crash"
        assert InvalidRunReason.FALLBACK_SUBSTITUTION.value == "fallback_substitution"


# ============================================================================
# V300RunConfig Tests
# ============================================================================

class TestV300RunConfig:
    """Tests for run configuration."""

    def test_minimum_seeds_required(self):
        """Config requires minimum 5 seeds."""
        with pytest.raises(ValueError, match="minimum 5"):
            V300RunConfig(seeds=(42,))

    def test_no_sam_required(self):
        """Config must not use SAM."""
        with pytest.raises(ValueError, match="must not use SAM"):
            V300RunConfig(use_sam=True)

    def test_default_config_valid(self):
        """Default config is valid."""
        config = V300RunConfig()

        assert len(config.seeds) >= 5
        assert config.use_sam == False
        assert config.friction_modifier == 1.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestInfrastructureIntegration:
    """Integration tests for v3.0 infrastructure."""

    def test_harness_creation(self):
        """Harness can be created with valid config."""
        config = V300RunConfig(
            ablation=AblationSpec.TRACE_EXCISION,
        )
        harness = V300AblationHarness(config)

        assert harness is not None
        assert harness.config.ablation == AblationSpec.TRACE_EXCISION

    def test_ablation_d_harness_setup(self):
        """Ablation D harness has correct relaxation."""
        config = V300RunConfig(
            ablation=AblationSpec.TRACE_EXCISION,
        )
        harness = V300AblationHarness(config)

        # Compiler should have trace relaxation
        assert harness.compiler.ablation == AblationSpec.TRACE_EXCISION

    def test_full_taxonomy_coverage(self):
        """All ablation types create valid harnesses."""
        for ablation in AblationSpec:
            config = V300RunConfig(ablation=ablation)
            harness = V300AblationHarness(config)
            assert harness.config.ablation == ablation


# ============================================================================
# Constraint Binding Detector Tests
# ============================================================================

class TestConstraintBindingDetector:
    """Tests for constraint binding detector (v3.0 Requirement 8)."""

    def test_constraints_bind_when_delta_positive(self):
        """Constraints bind when delta > 0 and violation rate low."""
        # Create mock episodes
        baseline_ep = V300EpisodeRecord(
            episode_index=0,
            seed=42,
            ablation=AblationSpec.NONE,
        )
        baseline_ep.steps = [
            V300StepRecord(
                step_index=i,
                episode_index=0,
                seed=42,
                action_id="A",
                feasible_actions=["A", "B", "C"],
                ablation_applied=AblationSpec.NONE,
                step_type=StepType.GENUINE_CHOICE,
            )
            for i in range(5)
        ]

        ablated_ep = V300EpisodeRecord(
            episode_index=0,
            seed=42,
            ablation=AblationSpec.TRACE_EXCISION,
        )
        ablated_ep.steps = [
            V300StepRecord(
                step_index=i,
                episode_index=0,
                seed=42,
                action_id="A",
                feasible_actions=["A", "B", "C"],
                ablation_applied=AblationSpec.TRACE_EXCISION,
                step_type=StepType.GENUINE_CHOICE,
            )
            for i in range(5)
        ]

        # Feasible = 3 actions, masked = 1 action → delta = 2
        baseline_feasible = [{"A", "B", "C"} for _ in range(5)]
        baseline_masked = [{"A"} for _ in range(5)]
        ablated_feasible = [{"A", "B", "C"} for _ in range(5)]
        ablated_masked = [{"A"} for _ in range(5)]

        metrics = ConstraintBindingDetector.compute_metrics(
            baseline_episodes=[baseline_ep],
            ablated_episodes=[ablated_ep],
            baseline_feasible_sets=baseline_feasible,
            baseline_masked_sets=baseline_masked,
            ablated_feasible_sets=ablated_feasible,
            ablated_masked_sets=ablated_masked,
        )

        assert metrics.mean_constraint_delta == 2.0
        assert metrics.constraint_violation_rate == 0.0
        assert metrics.constraints_bind == True

    def test_constraints_dont_bind_when_delta_zero(self):
        """Constraints don't bind when delta ≈ 0."""
        baseline_ep = V300EpisodeRecord(
            episode_index=0,
            seed=42,
            ablation=AblationSpec.NONE,
        )
        baseline_ep.steps = [
            V300StepRecord(
                step_index=i,
                episode_index=0,
                seed=42,
                action_id="A",
                feasible_actions=["A", "B", "C"],
                ablation_applied=AblationSpec.NONE,
                step_type=StepType.GENUINE_CHOICE,
            )
            for i in range(5)
        ]

        ablated_ep = V300EpisodeRecord(
            episode_index=0,
            seed=42,
            ablation=AblationSpec.TRACE_EXCISION,
        )
        ablated_ep.steps = [
            V300StepRecord(
                step_index=i,
                episode_index=0,
                seed=42,
                action_id="A",
                feasible_actions=["A", "B", "C"],
                ablation_applied=AblationSpec.TRACE_EXCISION,
                step_type=StepType.GENUINE_CHOICE,
            )
            for i in range(5)
        ]

        # Feasible = masked = 3 → delta = 0 (constraints don't remove anything)
        ablated_feasible = [{"A", "B", "C"} for _ in range(5)]
        ablated_masked = [{"A", "B", "C"} for _ in range(5)]  # No constraint effect

        metrics = ConstraintBindingDetector.compute_metrics(
            baseline_episodes=[baseline_ep],
            ablated_episodes=[ablated_ep],
            baseline_feasible_sets=ablated_feasible,
            baseline_masked_sets=ablated_masked,
            ablated_feasible_sets=ablated_feasible,
            ablated_masked_sets=ablated_masked,
        )

        assert metrics.mean_constraint_delta == 0.0
        assert metrics.constraints_bind == False

    def test_metrics_summary_format(self):
        """Metrics summary has expected format."""
        metrics = ConstraintBindingMetrics(
            mean_constraint_delta=1.5,
            action_distribution_divergence=0.25,
            constraint_violation_rate=0.05,
            echoice_step_count=10,
            constraints_bind=True,
        )

        summary = metrics.summary()

        assert "BIND" in summary
        assert "1.500" in summary or "1.5" in summary
        assert "n=10" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
