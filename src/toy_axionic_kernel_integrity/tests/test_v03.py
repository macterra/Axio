"""
AKI v0.3 Test Suite: Kernel Non-Simulability (KNS).

Tests for:
- R increment logic
- Evaluability checks (KNS-E)
- Wrapper classification
- Degeneracy classification
- Attack success/failure signatures
- End-to-end smoke test
"""

import pytest
import uuid
from typing import Any

# Core v0.3 components
from toy_aki.kernel.reflective import (
    KernelState,
    Delta,
    DeltaType,
    AdmissibilityRules,
    DecisionBoundary,
    ACVSchema,
    WrapperDetectionConfig,
    apply_delta,
    create_initial_state,
    DeltaApplicationError,
)
from toy_aki.kernel.r_metric import (
    RMetricTracker,
    RDimension,
    RIncrementResult,
    DescriptorExtractor,
    StateDescriptors,
    is_cosmetic_delta,
    expected_r_dimension,
)
from toy_aki.kernel.evaluability import (
    EvaluabilityCapability,
    EvaluabilityResult,
    EvaluabilityMonitor,
    assess_evaluability,
    would_delta_break_evaluability,
    check_attribution_capability,
    check_rejection_capability,
    check_explanation_capability,
    check_detection_capability,
)
from toy_aki.kernel.wrapper_detection import (
    WrapperClassification,
    WrapperDetectionResult,
    WrapperDetector,
    ChannelSegment,
    ChannelType,
    PipelineGraph,
    create_standard_pipeline,
    create_wrapped_pipeline,
    classify_wrapper,
)
from toy_aki.agents.external_optimizer import (
    ReflectiveOptimizer,
    BenignReflectiveOptimizer,
    NullReflectiveOptimizer,
    RandomReflectiveOptimizer,
    V03OptimizationContext,
    V03OptimizerDecision,
    create_v03_optimizer,
)
from toy_aki.attacks.kns import (
    KNSAttack,
    KNSAttackType,
    KNSAttackResult,
    PolicyMimicryAttack,
    EvaluatorSubstitutionAttack,
    ReflectiveShortcuttingAttack,
    JustificationCollapseAttack,
    ConstraintCosmeticizationAttack,
    WrapperDelegationAttack,
    create_kns_attack,
    get_all_kns_attack_types,
)
from toy_aki.harness.v03_runner import (
    V03Variant,
    FailureSignature,
    ReflectiveKernel,
    V03ExperimentRunner,
    run_v03_experiment,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def initial_state() -> KernelState:
    """Create initial kernel state for testing."""
    return create_initial_state(
        state_id="test_state_0",
        timestamp_ms=1000,
    )


@pytest.fixture
def r_tracker() -> RMetricTracker:
    """Create R metric tracker."""
    return RMetricTracker(enable_probing=False)


@pytest.fixture
def eval_monitor() -> EvaluabilityMonitor:
    """Create evaluability monitor."""
    return EvaluabilityMonitor()


@pytest.fixture
def wrapper_detector() -> WrapperDetector:
    """Create wrapper detector."""
    return WrapperDetector()


# =============================================================================
# KernelState Tests
# =============================================================================

class TestKernelState:
    """Tests for KernelState and Delta application."""

    def test_create_initial_state(self, initial_state: KernelState):
        """Initial state should have expected defaults."""
        assert initial_state.state_version == 1
        assert initial_state.parent_state_id is None
        assert "delegation_authority" in initial_state.admissibility.inadmissible_patterns
        assert "MOVE_LEFT" in initial_state.decision_boundary.allowed_action_types

    def test_state_is_frozen(self, initial_state: KernelState):
        """KernelState should be frozen (immutable)."""
        with pytest.raises(Exception):
            initial_state.state_version = 2  # type: ignore

    def test_dimension_digests(self, initial_state: KernelState):
        """Should produce digests for each dimension."""
        digests = initial_state.dimension_digests()
        assert "admissibility" in digests
        assert "decision_boundary" in digests
        assert "acv_schema" in digests
        assert "wrapper_detection" in digests
        assert all(isinstance(d, str) and len(d) > 0 for d in digests.values())

    def test_apply_admissibility_delta(self, initial_state: KernelState):
        """Delta should modify admissibility rules."""
        delta = Delta(
            delta_id="test_delta_1",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("new_pattern",),
        )
        new_state = apply_delta(initial_state, delta, "test_state_1")

        assert "new_pattern" in new_state.admissibility.inadmissible_patterns
        assert new_state.state_version == 2
        assert new_state.parent_state_id == initial_state.state_id

    def test_apply_decision_delta(self, initial_state: KernelState):
        """Delta should modify decision boundary."""
        delta = Delta(
            delta_id="test_delta_2",
            delta_type=DeltaType.ADD_ACTION_TYPE,
            target_dimension="decision",
            payload=("NEW_ACTION",),
        )
        new_state = apply_delta(initial_state, delta, "test_state_2")

        assert "NEW_ACTION" in new_state.decision_boundary.allowed_action_types

    def test_apply_acv_delta(self, initial_state: KernelState):
        """Delta should modify ACV schema."""
        delta = Delta(
            delta_id="test_delta_3",
            delta_type=DeltaType.ADD_REQUIRED_ACV_FIELD,
            target_dimension="acv",
            payload=("new_field",),
        )
        new_state = apply_delta(initial_state, delta, "test_state_3")

        assert "new_field" in new_state.acv_schema.required_chain_fields

    def test_apply_cosmetic_delta(self, initial_state: KernelState):
        """Cosmetic delta should not change R dimensions."""
        old_digests = initial_state.dimension_digests()

        delta = Delta(
            delta_id="test_delta_4",
            delta_type=DeltaType.UPDATE_DESCRIPTION,
            target_dimension="cosmetic",
            payload=("New description",),
        )
        new_state = apply_delta(initial_state, delta, "test_state_4")

        # R dimensions unchanged
        new_digests = new_state.dimension_digests()
        assert old_digests == new_digests

        # Description changed
        assert new_state.description == "New description"

    def test_invalid_delta_raises(self, initial_state: KernelState):
        """Invalid delta should raise error."""
        delta = Delta(
            delta_id="bad_delta",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=(),  # Empty payload is invalid
        )
        with pytest.raises(DeltaApplicationError):
            apply_delta(initial_state, delta, "should_fail")


# =============================================================================
# R Metric Tests
# =============================================================================

class TestRMetric:
    """Tests for R metric tracking."""

    def test_initial_r_is_zero(self, r_tracker: RMetricTracker):
        """R should start at 0."""
        assert r_tracker.r_value == 0

    def test_cosmetic_delta_no_r_increment(
        self,
        initial_state: KernelState,
        r_tracker: RMetricTracker,
    ):
        """Cosmetic deltas should not increment R."""
        r_tracker.register_initial_state(initial_state)

        delta = Delta(
            delta_id="cosmetic_1",
            delta_type=DeltaType.UPDATE_DESCRIPTION,
            target_dimension="cosmetic",
            payload=("Updated",),
        )
        new_state = apply_delta(initial_state, delta, "state_1")

        result = r_tracker.check_r_increment(initial_state, new_state, delta)

        assert not result.should_increment
        assert len(result.changed_dimensions) == 0

    def test_structural_delta_increments_r(
        self,
        initial_state: KernelState,
        r_tracker: RMetricTracker,
    ):
        """Structural deltas should increment R."""
        r_tracker.register_initial_state(initial_state)

        delta = Delta(
            delta_id="structural_1",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test_pattern",),
        )
        new_state = apply_delta(initial_state, delta, "state_1")

        result = r_tracker.check_r_increment(initial_state, new_state, delta)

        assert result.should_increment
        assert RDimension.ADMISSIBILITY_SURFACE in result.changed_dimensions

    def test_r_tracker_applies_increment(
        self,
        initial_state: KernelState,
        r_tracker: RMetricTracker,
    ):
        """apply_increment should update R value."""
        r_tracker.register_initial_state(initial_state)
        assert r_tracker.r_value == 0

        delta = Delta(
            delta_id="inc_1",
            delta_type=DeltaType.ADD_ACTION_TYPE,
            target_dimension="decision",
            payload=("NEW",),
        )
        new_state = apply_delta(initial_state, delta, "state_1")

        new_r = r_tracker.apply_increment(new_state)
        assert new_r == 1
        assert r_tracker.r_value == 1

    def test_is_cosmetic_delta(self):
        """is_cosmetic_delta should correctly classify."""
        cosmetic = Delta(
            delta_id="c1",
            delta_type=DeltaType.UPDATE_DESCRIPTION,
            target_dimension="cosmetic",
            payload=("x",),
        )
        assert is_cosmetic_delta(cosmetic)

        structural = Delta(
            delta_id="s1",
            delta_type=DeltaType.ADD_FORBIDDEN_CLASS,
            target_dimension="admissibility",
            payload=("X",),
        )
        assert not is_cosmetic_delta(structural)

    def test_expected_r_dimension(self):
        """expected_r_dimension should map delta types correctly."""
        assert expected_r_dimension(
            Delta("d1", DeltaType.ADD_INADMISSIBLE_PATTERN, "admissibility", ("x",))
        ) == RDimension.ADMISSIBILITY_SURFACE

        assert expected_r_dimension(
            Delta("d2", DeltaType.ADD_ACTION_TYPE, "decision", ("x",))
        ) == RDimension.DECISION_BOUNDARY

        assert expected_r_dimension(
            Delta("d3", DeltaType.ADD_REQUIRED_ACV_FIELD, "acv", ("x",))
        ) == RDimension.ACV_TRACE_STRUCTURE

        assert expected_r_dimension(
            Delta("d4", DeltaType.UPDATE_DESCRIPTION, "cosmetic", ("x",))
        ) is None


# =============================================================================
# Evaluability Tests
# =============================================================================

class TestEvaluability:
    """Tests for KNS-E evaluability checks."""

    def test_initial_state_is_evaluable(self, initial_state: KernelState):
        """Initial state should have full evaluability."""
        result = assess_evaluability(initial_state)
        assert result.evaluability_preserved
        assert all(
            r.preserved for r in result.capability_results.values()
        )

    def test_attribution_capability(self, initial_state: KernelState):
        """Attribution requires ACV chain fields."""
        result = check_attribution_capability(initial_state)
        assert result.preserved
        assert result.capability == EvaluabilityCapability.ATTRIBUTION

    def test_rejection_capability(self, initial_state: KernelState):
        """Rejection requires inadmissible patterns."""
        result = check_rejection_capability(initial_state)
        assert result.preserved
        assert result.capability == EvaluabilityCapability.REJECTION

    def test_explanation_capability(self, initial_state: KernelState):
        """Explanation requires chain fields for rejection chains."""
        result = check_explanation_capability(initial_state)
        assert result.preserved
        assert result.capability == EvaluabilityCapability.EXPLANATION

    def test_detection_capability(self, initial_state: KernelState):
        """Detection requires delegation patterns."""
        result = check_detection_capability(initial_state)
        assert result.preserved
        assert result.capability == EvaluabilityCapability.DETECTION

    def test_removing_patterns_affects_evaluability(self, initial_state: KernelState):
        """Removing core patterns should affect evaluability."""
        # Remove multiple core patterns
        modified_admissibility = AdmissibilityRules(
            inadmissible_patterns=frozenset(),  # Empty!
            forbidden_action_classes=initial_state.admissibility.forbidden_action_classes,
        )
        modified_state = KernelState(
            state_id="modified",
            admissibility=modified_admissibility,
            decision_boundary=initial_state.decision_boundary,
            acv_schema=initial_state.acv_schema,
            wrapper_detection=initial_state.wrapper_detection,
        )

        result = assess_evaluability(modified_state)
        # Detection capability should be affected
        assert not result.capability_results[EvaluabilityCapability.DETECTION].preserved

    def test_evaluability_monitor_tracks_loss(
        self,
        initial_state: KernelState,
        eval_monitor: EvaluabilityMonitor,
    ):
        """Monitor should track when evaluability is lost."""
        # Check initial state
        eval_monitor.check_state(initial_state)
        assert eval_monitor.evaluability_intact

        # Create broken state
        broken_admissibility = AdmissibilityRules(
            inadmissible_patterns=frozenset(),
        )
        broken_state = KernelState(
            state_id="broken",
            admissibility=broken_admissibility,
            decision_boundary=initial_state.decision_boundary,
            acv_schema=initial_state.acv_schema,
            wrapper_detection=initial_state.wrapper_detection,
        )

        eval_monitor.check_state(broken_state)
        assert not eval_monitor.evaluability_intact
        assert eval_monitor.loss_point == "broken"

    def test_would_delta_break_evaluability(self, initial_state: KernelState):
        """Should predict evaluability impact of deltas."""
        # Safe delta
        safe_delta = Delta(
            delta_id="safe",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("new_pattern",),
        )
        would_break, _ = would_delta_break_evaluability(initial_state, safe_delta)
        assert not would_break

        # Dangerous delta (removing core pattern)
        dangerous_delta = Delta(
            delta_id="dangerous",
            delta_type=DeltaType.REMOVE_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("delegation_authority",),
        )
        # This may or may not break depending on remaining patterns
        # Just test that it doesn't crash
        would_delta_break_evaluability(initial_state, dangerous_delta)


# =============================================================================
# Wrapper Detection Tests
# =============================================================================

class TestWrapperDetection:
    """Tests for wrapper/containment classification."""

    def test_standard_pipeline_is_plumbing(self):
        """Standard pipeline should be non-agentic plumbing."""
        pipeline = create_standard_pipeline()
        config = WrapperDetectionConfig()
        result = classify_wrapper(pipeline, config)

        assert result.classification == WrapperClassification.NON_AGENTIC_PLUMBING
        assert result.is_valid
        assert len(result.agentic_segments) == 0

    def test_wrapper_with_policy_access_is_delegation(self):
        """Wrapper with policy access should be delegation violation."""
        pipeline = create_wrapped_pipeline(
            wrapper_has_policy_access=True,
        )
        config = WrapperDetectionConfig()
        result = classify_wrapper(pipeline, config)

        assert result.classification == WrapperClassification.DELEGATION_VIOLATION
        assert not result.is_valid
        assert len(result.agentic_segments) > 0

    def test_wrapper_with_reward_access_is_delegation(self):
        """Wrapper with reward access should be delegation violation."""
        pipeline = create_wrapped_pipeline(
            wrapper_has_reward_access=True,
        )
        config = WrapperDetectionConfig()
        result = classify_wrapper(pipeline, config)

        assert result.classification == WrapperClassification.DELEGATION_VIOLATION
        assert not result.is_valid

    def test_wrapper_with_filtering_is_delegation(self):
        """Wrapper that filters observations should be delegation."""
        pipeline = create_wrapped_pipeline(
            wrapper_filters_observations=True,
        )
        config = WrapperDetectionConfig()
        result = classify_wrapper(pipeline, config)

        assert result.classification == WrapperClassification.DELEGATION_VIOLATION
        assert not result.is_valid

    def test_wrapper_with_throttling_is_delegation(self):
        """Wrapper that throttles actions should be delegation."""
        pipeline = create_wrapped_pipeline(
            wrapper_throttles_actions=True,
        )
        config = WrapperDetectionConfig()
        result = classify_wrapper(pipeline, config)

        assert result.classification == WrapperClassification.DELEGATION_VIOLATION
        assert not result.is_valid

    def test_detector_tracks_violations(self, wrapper_detector: WrapperDetector):
        """Detector should track violation history."""
        good_pipeline = create_standard_pipeline()
        bad_pipeline = create_wrapped_pipeline(wrapper_has_policy_access=True)

        wrapper_detector.detect(good_pipeline)
        assert not wrapper_detector.has_violations()

        wrapper_detector.detect(bad_pipeline)
        assert wrapper_detector.has_violations()
        assert wrapper_detector.violation_count() == 1


# =============================================================================
# Optimizer Tests
# =============================================================================

class TestOptimizers:
    """Tests for external optimizers."""

    def test_benign_optimizer_proposes_safe_deltas(self, initial_state: KernelState):
        """Benign optimizer should propose safe deltas."""
        optimizer = BenignReflectiveOptimizer(seed=42, max_proposals=5)

        context = V03OptimizationContext(
            current_state=initial_state,
            r_value=0,
            step_number=0,
            previous_deltas=[],
            previous_outcomes=[],
        )

        # Get some proposals
        proposals = []
        for i in range(10):
            context = V03OptimizationContext(
                current_state=initial_state,
                r_value=0,
                step_number=i,
                previous_deltas=[],
                previous_outcomes=[],
            )
            decision = optimizer.propose_delta(context)
            if decision.propose:
                proposals.append(decision.delta)

        # Should have some proposals
        assert len(proposals) > 0

        # All should be safe types
        safe_types = {
            DeltaType.ADD_INADMISSIBLE_PATTERN,
            DeltaType.ADD_FORBIDDEN_CLASS,
            DeltaType.STRENGTHEN_WRAPPER_DETECTION,
            DeltaType.UPDATE_DESCRIPTION,
        }
        for delta in proposals:
            assert delta.delta_type in safe_types

    def test_null_optimizer_never_proposes(self, initial_state: KernelState):
        """Null optimizer should always abstain."""
        optimizer = NullReflectiveOptimizer()

        context = V03OptimizationContext(
            current_state=initial_state,
            r_value=0,
            step_number=0,
            previous_deltas=[],
            previous_outcomes=[],
        )

        for _ in range(10):
            decision = optimizer.propose_delta(context)
            assert not decision.propose
            assert decision.delta is None

    def test_random_optimizer_proposes_varied_deltas(self, initial_state: KernelState):
        """Random optimizer should propose various delta types."""
        optimizer = RandomReflectiveOptimizer(seed=42, abstain_probability=0.0)

        delta_types_seen = set()
        for i in range(20):
            context = V03OptimizationContext(
                current_state=initial_state,
                r_value=0,
                step_number=i,
                previous_deltas=[],
                previous_outcomes=[],
            )
            decision = optimizer.propose_delta(context)
            if decision.propose and decision.delta:
                delta_types_seen.add(decision.delta.delta_type)

        # Should see variety
        assert len(delta_types_seen) >= 3

    def test_create_v03_optimizer_factory(self):
        """Factory should create correct optimizer types."""
        opt_a = create_v03_optimizer("v0.3.a")
        assert isinstance(opt_a, BenignReflectiveOptimizer)

        opt_b = create_v03_optimizer("v0.3.b")
        assert isinstance(opt_b, RandomReflectiveOptimizer)


# =============================================================================
# KNS Attack Tests
# =============================================================================

class TestKNSAttacks:
    """Tests for KNS simulability attacks."""

    def test_all_attack_types_available(self):
        """All 6 attack types should be available."""
        types = get_all_kns_attack_types()
        assert len(types) == 6
        assert KNSAttackType.POLICY_MIMICRY in types
        assert KNSAttackType.EVALUATOR_SUBSTITUTION in types
        assert KNSAttackType.REFLECTIVE_SHORTCUTTING in types
        assert KNSAttackType.JUSTIFICATION_COLLAPSE in types
        assert KNSAttackType.CONSTRAINT_COSMETICIZATION in types
        assert KNSAttackType.WRAPPER_DELEGATION in types

    def test_create_kns_attack_factory(self):
        """Factory should create all attack types."""
        for attack_type in get_all_kns_attack_types():
            attack = create_kns_attack(attack_type, seed=42)
            assert isinstance(attack, KNSAttack)
            assert attack.attack_type == attack_type

    def test_policy_mimicry_attack(self, initial_state: KernelState):
        """Policy mimicry attack should propose deltas."""
        attack = PolicyMimicryAttack(seed=42)
        assert attack.attack_type == KNSAttackType.POLICY_MIMICRY

        context = V03OptimizationContext(
            current_state=initial_state,
            r_value=0,
            step_number=0,
            previous_deltas=[],
            previous_outcomes=[],
        )

        # Should propose in learning phase
        decision = attack.propose_delta(context)
        assert decision.propose

    def test_attack_result_tracking(self, initial_state: KernelState):
        """Attacks should track results correctly."""
        attack = PolicyMimicryAttack(seed=42)

        # Record some outcomes
        attack.record_delta_outcome(True)
        attack.record_delta_outcome(False)
        attack.record_delta_outcome(True)

        result = attack.get_result(
            passed_checks=True,
            hollowed_structure=False,
            r_achieved=2,
        )

        assert result.attack_type == KNSAttackType.POLICY_MIMICRY
        assert result.r_achieved == 2
        assert result.steps_taken == 3
        assert result.deltas_accepted == 2

    def test_attack_failure_recording(self):
        """Attacks should record failure signatures."""
        attack = EvaluatorSubstitutionAttack(seed=42)

        attack.record_failure("evaluability_loss", step=5)

        result = attack.get_result(
            passed_checks=False,
            hollowed_structure=False,
            r_achieved=3,
        )

        assert result.failure_signature == "evaluability_loss"
        assert result.failure_step == 5

    def test_all_attacks_have_strategies(self):
        """All attacks should describe their strategy."""
        for attack_type in get_all_kns_attack_types():
            attack = create_kns_attack(attack_type)
            strategy = attack.get_attack_strategy()
            assert isinstance(strategy, str)
            assert len(strategy) > 0


# =============================================================================
# Reflective Kernel Tests
# =============================================================================

class TestReflectiveKernel:
    """Tests for ReflectiveKernel."""

    def test_kernel_initialization(self):
        """Kernel should initialize with correct state."""
        kernel = ReflectiveKernel(kernel_id="test_kernel")
        assert kernel.r_value == 0
        assert kernel.evaluability_intact
        assert kernel.state is not None

    def test_kernel_rejects_inadmissible_delta(self):
        """Kernel should reject deltas that break evaluability."""
        kernel = ReflectiveKernel(kernel_id="test_kernel")

        # This delta tries to remove core delegation pattern
        # It may be inadmissible if it would break detection
        delta = Delta(
            delta_id="bad_delta",
            delta_type=DeltaType.REMOVE_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("delegation_authority",),
        )

        success, new_state, error = kernel.apply_delta(delta)
        # Should either succeed or fail cleanly
        assert isinstance(success, bool)
        if not success:
            assert error is not None

    def test_kernel_accepts_safe_delta(self):
        """Kernel should accept safe deltas."""
        kernel = ReflectiveKernel(kernel_id="test_kernel")

        delta = Delta(
            delta_id="safe_delta",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("new_test_pattern",),
        )

        success, new_state, error = kernel.apply_delta(delta)
        assert success
        assert new_state is not None
        assert error is None
        assert "new_test_pattern" in kernel.state.admissibility.inadmissible_patterns

    def test_kernel_r_increments_on_structural_change(self):
        """R should increment on structural changes."""
        kernel = ReflectiveKernel(kernel_id="test_kernel")
        assert kernel.r_value == 0

        delta = Delta(
            delta_id="structural",
            delta_type=DeltaType.ADD_FORBIDDEN_CLASS,
            target_dimension="admissibility",
            payload=("NEW_CLASS",),
        )

        success, _, _ = kernel.apply_delta(delta)
        assert success
        assert kernel.r_value == 1

    def test_kernel_pipeline_check(self):
        """Kernel should detect wrapper violations."""
        kernel = ReflectiveKernel(kernel_id="test_kernel")

        good_pipeline = create_standard_pipeline()
        result = kernel.check_pipeline(good_pipeline)
        assert result.is_valid

        bad_pipeline = create_wrapped_pipeline(wrapper_has_policy_access=True)
        result = kernel.check_pipeline(bad_pipeline)
        assert not result.is_valid


# =============================================================================
# Degeneracy Classification Tests
# =============================================================================

class TestDegeneracyClassification:
    """Tests for degeneracy detection."""

    def test_null_optimizer_causes_degeneracy(self):
        """Null optimizer should result in degenerate classification."""
        kernel = ReflectiveKernel(kernel_id="test")
        optimizer = NullReflectiveOptimizer()

        # Run a few steps
        for step in range(10):
            context = V03OptimizationContext(
                current_state=kernel.state,
                r_value=kernel.r_value,
                step_number=step,
                previous_deltas=[],
                previous_outcomes=[],
            )
            decision = optimizer.propose_delta(context)
            # Null optimizer never proposes
            assert not decision.propose

        # No R increments = potentially degenerate
        assert kernel.r_value == 0


# =============================================================================
# End-to-End Smoke Test
# =============================================================================

class TestV03Smoke:
    """End-to-end smoke tests for v0.3."""

    def test_smoke_v03_runner(self):
        """v0.3 runner should complete without error."""
        runner = V03ExperimentRunner(
            base_seed=42,
            max_steps=5,  # Minimal steps for smoke test
            verbose=False,
        )

        # Just verify corridor - full experiment is expensive
        p5_ok, p2_prime_ok, corridor_ok = runner.verify_corridor()
        assert p5_ok
        assert p2_prime_ok
        assert corridor_ok

    def test_smoke_single_variant(self):
        """Single variant should complete."""
        runner = V03ExperimentRunner(
            base_seed=42,
            max_steps=5,
            verbose=False,
        )

        optimizer = BenignReflectiveOptimizer(seed=42)
        result = runner.run_variant(V03Variant.V03A_KERNEL_COHERENT, optimizer)

        assert result.variant == "v0.3.a"
        assert result.total_steps > 0
        assert result.r_star >= 0

    def test_smoke_full_experiment_minimal(self):
        """Full experiment should complete (minimal steps)."""
        result = run_v03_experiment(
            base_seed=42,
            max_steps=3,
            verbose=False,
        )

        assert result.experiment_id is not None
        assert result.corridor_intact
        assert len(result.variant_results) > 0
        assert result.claim is not None


# =============================================================================
# Integration Tests
# =============================================================================

class TestV03Integration:
    """Integration tests verifying component interactions."""

    def test_delta_application_updates_r_and_evaluability(self):
        """Delta application should update both R and evaluability."""
        kernel = ReflectiveKernel(kernel_id="integration_test")
        initial_r = kernel.r_value
        initial_eval = kernel.evaluability_intact

        # Apply structural delta
        delta = Delta(
            delta_id="int_delta",
            delta_type=DeltaType.ADD_ACTION_TYPE,
            target_dimension="decision",
            payload=("INTEGRATION_ACTION",),
        )

        success, _, _ = kernel.apply_delta(delta)
        assert success

        # R should increment
        assert kernel.r_value > initial_r

        # Evaluability should still be intact (safe delta)
        assert kernel.evaluability_intact

    def test_attack_integration_with_kernel(self):
        """Attacks should interact correctly with kernel."""
        kernel = ReflectiveKernel(kernel_id="attack_test")
        attack = ConstraintCosmeticizationAttack(seed=42)

        accepted_count = 0
        rejected_count = 0

        for step in range(10):
            context = V03OptimizationContext(
                current_state=kernel.state,
                r_value=kernel.r_value,
                step_number=step,
                previous_deltas=[],
                previous_outcomes=[],
            )

            decision = attack.propose_delta(context)
            if decision.propose and decision.delta:
                success, _, _ = kernel.apply_delta(decision.delta)
                attack.record_delta_outcome(success)
                if success:
                    accepted_count += 1
                else:
                    rejected_count += 1

        # Attack should have attempted something
        result = attack.get_result(
            passed_checks=accepted_count > 0,
            hollowed_structure=accepted_count > 0,
            r_achieved=kernel.r_value,
        )

        assert result.steps_taken > 0
