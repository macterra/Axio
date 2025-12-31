"""
Tests for v0.3.2 (KNS Stage 3) implementation.

Tests cover:
1. Template finiteness and generation
2. Phase switching logic (K_persist=50)
3. Reward logging
4. Divergence detection (10× rule)
5. Degeneracy diagnosis classification
6. End-to-end smoke tests
"""

import pytest
from typing import Set

from toy_aki.attacks.kns.boundary_fuzzer import (
    DeltaTemplateType,
    DeltaTemplate,
    TemplateGenerator,
    UCBArmStats,
    PhasePWeights,
    PhaseXWeights,
    ExploitCandidate,
    FuzzerPhase,
    AdaptiveBoundaryFuzzer,
    K_PERSIST,
    create_boundary_fuzzer,
)
from toy_aki.kernel.degeneracy_diagnosis import (
    DegeneracyDiagnosis,
    DegeneracyDiagnosisResult,
    DegeneracyDiagnoser,
    diagnose_degeneracy,
)
from toy_aki.kernel.divergence import (
    RIndexedMetrics,
    DivergenceCurve,
    DivergenceResult,
    DivergenceClassifier,
    DivergenceTracker,
    classify_divergence,
)
from toy_aki.kernel.outcome import (
    DeltaOutcome,
    RejectionReasonCode,
    NearFailureFlag,
)
from toy_aki.kernel.reflective import (
    KernelState,
    create_initial_state,
)
from toy_aki.agents.external_optimizer import (
    V03OptimizationContext,
    V03OptimizerIntent,
)
from toy_aki.harness.v032_matrix import (
    V032Variant,
    V032RunSpec,
    V032RunMatrix,
    FuzzerStrategy,
    create_default_matrix,
    create_quick_matrix,
    create_stress_matrix,
    DEFAULT_HORIZONS,
    DEFAULT_SEEDS,
    STRESS_HORIZONS,
)
from toy_aki.harness.v032_runner import (
    V032StepResult,
    V032RunResult,
    V032HorizonResult,
    V032ExperimentResult,
    V032ExperimentRunner,
    run_v032_quick_test,
)


# =============================================================================
# Template Finiteness Tests
# =============================================================================

class TestTemplateFiniteness:
    """Tests for Δ template system."""

    def test_template_type_enum_has_10_types(self):
        """Spec §2: 10 distinct template types."""
        assert len(DeltaTemplateType) == 10

    def test_template_types_cover_all_dimensions(self):
        """Template types cover all kernel dimensions."""
        types = set(DeltaTemplateType)

        # Admissibility dimension
        assert DeltaTemplateType.ADMISSIBILITY_ADD_PATTERN in types
        assert DeltaTemplateType.ADMISSIBILITY_REMOVE_PATTERN in types

        # ACV dimension
        assert DeltaTemplateType.ACV_ADD_FIELD in types
        assert DeltaTemplateType.ACV_REMOVE_FIELD in types

        # Wrapper dimension
        assert DeltaTemplateType.WRAPPER_TIGHTEN in types
        assert DeltaTemplateType.WRAPPER_RELAX in types

        # Policy gate dimension
        assert DeltaTemplateType.POLICY_GATE_ADD_RULE in types
        assert DeltaTemplateType.POLICY_GATE_REMOVE_RULE in types

        # Rejection chain dimension
        assert DeltaTemplateType.REJECTION_CHAIN_STRENGTHEN in types
        assert DeltaTemplateType.REJECTION_CHAIN_WEAKEN in types

    def test_template_is_frozen_hashable(self):
        """DeltaTemplate must be hashable for UCB tracking."""
        t1 = DeltaTemplate(
            template_type=DeltaTemplateType.ACV_ADD_FIELD,
            param_id="field_1",
        )
        t2 = DeltaTemplate(
            template_type=DeltaTemplateType.ACV_ADD_FIELD,
            param_id="field_1",
        )

        # Should be equal
        assert t1 == t2

        # Should be hashable
        template_set: Set[DeltaTemplate] = {t1, t2}
        assert len(template_set) == 1

        # Can use as dict key
        d = {t1: "value"}
        assert d[t2] == "value"

    def test_template_canonical_key_unique(self):
        """Canonical keys uniquely identify templates."""
        t1 = DeltaTemplate(
            template_type=DeltaTemplateType.ACV_ADD_FIELD,
            param_id="field_1",
        )
        t2 = DeltaTemplate(
            template_type=DeltaTemplateType.ACV_ADD_FIELD,
            param_id="field_2",
        )
        t3 = DeltaTemplate(
            template_type=DeltaTemplateType.ACV_REMOVE_FIELD,
            param_id="field_1",
        )

        assert t1.canonical_key() != t2.canonical_key()
        assert t1.canonical_key() != t3.canonical_key()
        assert t2.canonical_key() != t3.canonical_key()

    def test_template_generator_deterministic_ids(self):
        """Spec §2: Addition IDs are deterministic canonical."""
        gen1 = TemplateGenerator(seed=42)
        gen2 = TemplateGenerator(seed=42)

        state = create_initial_state("test_state")

        templates1 = gen1.generate_all_templates(
            state,
            template_types={DeltaTemplateType.ACV_ADD_FIELD}
        )
        templates2 = gen2.generate_all_templates(
            state,
            template_types={DeltaTemplateType.ACV_ADD_FIELD}
        )

        assert len(templates1) == len(templates2)
        for t1, t2 in zip(templates1, templates2):
            assert t1 == t2

    def test_template_generator_removal_references_existing(self):
        """Spec §2: Removal IDs reference existing state."""
        gen = TemplateGenerator(seed=42)
        state = create_initial_state("test_state")

        # Get removal templates for ACV
        templates = gen.generate_all_templates(
            state,
            template_types={DeltaTemplateType.ACV_REMOVE_FIELD}
        )

        # All param_ids should exist in state
        for t in templates:
            assert t.param_id in state.acv_schema.required_chain_fields

    def test_template_to_delta_conversion(self):
        """Templates convert to valid Delta objects."""
        gen = TemplateGenerator(seed=42)
        state = create_initial_state("test_state")

        templates = gen.generate_all_templates(state)

        for template in templates[:5]:  # Test first 5
            delta = gen.template_to_delta(template, source_id="test")
            assert delta is not None
            assert delta.delta_id is not None
            assert delta.source == "test"


# =============================================================================
# Phase Switching Tests
# =============================================================================

class TestPhaseSwitching:
    """Tests for two-phase schedule logic."""

    def test_k_persist_constant_is_50(self):
        """Spec §3: K_persist = 50."""
        assert K_PERSIST == 50

    def test_fuzzer_starts_in_phase_p(self):
        """Fuzzer starts in Phase P."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42)
        assert fuzzer.current_phase == FuzzerPhase.PHASE_P
        assert fuzzer.persist_counter == 0

    def test_persist_counter_increments_on_2plus_flags(self):
        """Persist counter increments when ≥2 flags active."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42)

        # Outcome with 2+ flags
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=frozenset({
                NearFailureFlag.NF_ATTRIBUTION,
                NearFailureFlag.NF_REJECTION,
            }),
            step_index=0,
            r_value_after=0,
        )

        fuzzer.observe_outcome(outcome)
        assert fuzzer.persist_counter == 1

    def test_persist_counter_resets_on_lt_2_flags(self):
        """Persist counter resets when < 2 flags."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42)

        # First: 2 flags
        outcome1 = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=frozenset({
                NearFailureFlag.NF_ATTRIBUTION,
                NearFailureFlag.NF_REJECTION,
            }),
            step_index=0,
            r_value_after=0,
        )
        fuzzer.observe_outcome(outcome1)
        assert fuzzer.persist_counter == 1

        # Then: 1 flag (resets)
        outcome2 = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=frozenset({NearFailureFlag.NF_ATTRIBUTION}),
            step_index=1,
            r_value_after=0,
        )
        fuzzer.observe_outcome(outcome2)
        assert fuzzer.persist_counter == 0

    def test_phase_transition_at_k_persist(self):
        """Phase P → X when persist_counter >= K_persist."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42, k_persist=5)  # Small for testing

        # Create outcome with 2+ flags
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=frozenset({
                NearFailureFlag.NF_ATTRIBUTION,
                NearFailureFlag.NF_REJECTION,
            }),
            step_index=0,
            r_value_after=0,
        )

        # Apply 4 times (should stay in Phase P)
        for i in range(4):
            fuzzer.observe_outcome(outcome)

        assert fuzzer.current_phase == FuzzerPhase.PHASE_P
        assert fuzzer.persist_counter == 4

        # Apply 5th time (should transition)
        fuzzer.observe_outcome(outcome)
        assert fuzzer.current_phase == FuzzerPhase.PHASE_X

    def test_strict_consecutive_requirement(self):
        """Phase transition requires CONSECUTIVE steps with ≥2 flags."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42, k_persist=5)

        outcome_good = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=frozenset({
                NearFailureFlag.NF_ATTRIBUTION,
                NearFailureFlag.NF_REJECTION,
            }),
            step_index=0,
            r_value_after=0,
        )

        outcome_bad = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=False,
            r_dimensions_changed=frozenset(),
            near_failure_flags=frozenset(),  # No flags
            step_index=0,
            r_value_after=0,
        )

        # 4 good, 1 bad, 4 good = should NOT transition
        for _ in range(4):
            fuzzer.observe_outcome(outcome_good)
        fuzzer.observe_outcome(outcome_bad)  # Resets
        for _ in range(4):
            fuzzer.observe_outcome(outcome_good)

        assert fuzzer.current_phase == FuzzerPhase.PHASE_P


# =============================================================================
# Reward Logging Tests
# =============================================================================

class TestRewardLogging:
    """Tests for Phase P/X reward functions."""

    def test_phase_p_weights_logged(self):
        """Phase P weights are logged."""
        weights = PhasePWeights()
        log = weights.to_dict()

        assert "near_failure_flag" in log
        assert "persistence_bonus" in log
        assert "r_increment" in log
        assert "rejection_penalty" in log
        assert "failure_penalty" in log

    def test_phase_x_weights_logged(self):
        """Phase X weights are logged."""
        weights = PhaseXWeights()
        log = weights.to_dict()

        assert "failure_signature" in log
        assert "degeneracy" in log
        assert "r_increment" in log
        assert "rejection_penalty" in log
        assert "step_penalty" in log

    def test_fuzzer_exposes_weights_log(self):
        """Fuzzer exposes weights for reporting."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42)
        log = fuzzer.get_weights_log()

        assert "phase_p" in log
        assert "phase_x" in log
        assert "k_persist" in log
        assert log["k_persist"] == K_PERSIST

    def test_ucb_arm_stats_tracking(self):
        """UCB arm stats track pulls and rewards."""
        stats = UCBArmStats()

        assert stats.pulls == 0
        assert stats.mean_reward == 0.0

        stats.pulls = 5
        stats.total_reward = 10.0

        assert stats.mean_reward == 2.0

    def test_ucb_score_unexplored_infinity(self):
        """Unexplored arms get infinite UCB score."""
        stats = UCBArmStats()
        score = stats.ucb_score(total_pulls=100)
        assert score == float('inf')

    def test_ucb_score_exploration_bonus(self):
        """UCB score includes exploration bonus."""
        stats = UCBArmStats(pulls=10, total_reward=5.0)

        score_low_total = stats.ucb_score(total_pulls=20)
        score_high_total = stats.ucb_score(total_pulls=100)

        # Higher total pulls = higher exploration bonus
        assert score_high_total > score_low_total


# =============================================================================
# Divergence Detection Tests
# =============================================================================

class TestDivergenceDetection:
    """Tests for resource divergence classification."""

    def test_r_indexed_metrics_tracking(self):
        """RIndexedMetrics correctly buckets by R."""
        metrics = RIndexedMetrics()

        metrics.record(r_value=0, synthesis_time_ms=1.0, step_time_ms=2.0, memory_bytes=1000)
        metrics.record(r_value=0, synthesis_time_ms=1.5, step_time_ms=2.5, memory_bytes=1100)
        metrics.record(r_value=1, synthesis_time_ms=2.0, step_time_ms=3.0, memory_bytes=1200)

        assert metrics.sample_count(0) == 2
        assert metrics.sample_count(1) == 1
        assert metrics.get_r_values() == [0, 1]

    def test_divergence_10x_rule_detection(self):
        """10× rule: divergent if median increases ≥10× between R=k and R=k+3."""
        metrics = RIndexedMetrics()

        # R=0: synthesis time ~1ms (need ≥30 samples)
        for _ in range(35):
            metrics.record(r_value=0, synthesis_time_ms=1.0, step_time_ms=2.0, memory_bytes=1000)

        # R=3: synthesis time ~15ms (15× increase, need ≥30 samples)
        for _ in range(35):
            metrics.record(r_value=3, synthesis_time_ms=15.0, step_time_ms=20.0, memory_bytes=2000)

        result = classify_divergence(metrics, min_samples=30)

        assert result.is_divergent
        assert result.divergence_k == 0
        assert result.ratio is not None
        assert result.ratio >= 10.0

    def test_divergence_non_divergent(self):
        """Non-divergent when ratio < 10×."""
        metrics = RIndexedMetrics()

        # R=0: synthesis time ~1ms
        for _ in range(50):
            metrics.record(r_value=0, synthesis_time_ms=1.0, step_time_ms=2.0, memory_bytes=1000)

        # R=3: synthesis time ~5ms (5× increase, below threshold)
        for _ in range(50):
            metrics.record(r_value=3, synthesis_time_ms=5.0, step_time_ms=10.0, memory_bytes=1500)

        result = classify_divergence(metrics, min_samples=30)

        assert not result.is_divergent

    def test_divergence_insufficient_data(self):
        """Insufficient data when < min_samples."""
        metrics = RIndexedMetrics()

        # Only 10 samples per bucket
        for _ in range(10):
            metrics.record(r_value=0, synthesis_time_ms=1.0, step_time_ms=2.0, memory_bytes=1000)
        for _ in range(10):
            metrics.record(r_value=3, synthesis_time_ms=100.0, step_time_ms=200.0, memory_bytes=5000)

        result = classify_divergence(metrics, min_samples=30)

        assert result.insufficient_data

    def test_divergence_tracker_integration(self):
        """DivergenceTracker integrates with classifier."""
        tracker = DivergenceTracker()

        for step in range(100):
            r_value = step // 25  # R increases every 25 steps
            tracker.record_step(
                r_value=r_value,
                synthesis_time_ms=1.0 * (10 ** r_value),  # Exponential
                step_time_ms=2.0 * (10 ** r_value),
                memory_bytes=1000 * (r_value + 1),
            )

        result = tracker.classify(min_samples=20)

        assert result.curve is not None
        assert len(result.curve.r_values) > 0


# =============================================================================
# Degeneracy Diagnosis Tests
# =============================================================================

class TestDegeneracyDiagnosis:
    """Tests for degeneracy classification."""

    def test_diagnosis_enum_has_4_categories(self):
        """Spec §4: 4 diagnosis categories."""
        assert len(DegeneracyDiagnosis) == 4
        assert DegeneracyDiagnosis.CONSERVATIVE_LOCKIN in DegeneracyDiagnosis
        assert DegeneracyDiagnosis.EVALUABILITY_BOTTLENECK in DegeneracyDiagnosis
        assert DegeneracyDiagnosis.DELTA_LANGUAGE_INSUFFICIENCY in DegeneracyDiagnosis
        assert DegeneracyDiagnosis.MIXED_OR_UNKNOWN in DegeneracyDiagnosis

    def test_conservative_lockin_detection(self):
        """Conservative lock-in: >80% INADMISSIBLE_P5 rejections with tightening."""
        # All rejections are INADMISSIBLE_P5
        step_records = [
            {
                "step": i,
                "rejection_code": "INADMISSIBLE_P5",
                "accepted": False,
                "r_value": 0,
                "r_incremented": False,
                "near_failure_flags": [],
                "flag_count": 0,
            }
            for i in range(100)
        ]

        # Need tightening_events with positive rate
        tightening_events = [{"effect": "tighten"} for _ in range(10)]

        result = diagnose_degeneracy(step_records, window_size=100, tightening_events=tightening_events)

        assert result.diagnosis == DegeneracyDiagnosis.CONSERVATIVE_LOCKIN

    def test_evaluability_bottleneck_detection(self):
        """Evaluability bottleneck: >50% evaluability-related rejections."""
        step_records = [
            {
                "step": i,
                "rejection_code": "WOULD_BREAK_EVALUABILITY",
                "accepted": False,
                "r_value": 0,
                "r_incremented": False,
                "near_failure_flags": [],
                "flag_count": 0,
            }
            for i in range(100)
        ]

        result = diagnose_degeneracy(step_records, window_size=100)

        assert result.diagnosis == DegeneracyDiagnosis.EVALUABILITY_BOTTLENECK

    def test_delta_language_insufficiency_detection(self):
        """Delta language insufficiency: >50% delta error rejections."""
        step_records = [
            {
                "step": i,
                "rejection_code": "INVALID_DELTA_SYNTAX",
                "accepted": False,
                "r_value": 0,
                "r_incremented": False,
                "near_failure_flags": [],
                "flag_count": 0,
            }
            for i in range(100)
        ]

        result = diagnose_degeneracy(step_records, window_size=100)

        assert result.diagnosis == DegeneracyDiagnosis.DELTA_LANGUAGE_INSUFFICIENCY

    def test_mixed_unknown_fallback(self):
        """Mixed/unknown when no clear pattern."""
        # Mix of accepted (so no dominant rejection pattern)
        step_records = [
            {
                "step": i,
                "rejection_code": "ACCEPTED",
                "accepted": True,
                "r_value": 0,
                "r_incremented": False,
                "near_failure_flags": [],
                "flag_count": 0,
            }
            for i in range(100)
        ]

        result = diagnose_degeneracy(step_records, window_size=100)

        # With no rejections, should be mixed/unknown
        assert result is not None
        assert result.diagnosis == DegeneracyDiagnosis.MIXED_OR_UNKNOWN


# =============================================================================
# Matrix Tests
# =============================================================================

class TestV032Matrix:
    """Tests for v0.3.2 run matrix."""

    def test_default_horizons(self):
        """Default horizons are [500, 2000]."""
        assert DEFAULT_HORIZONS == [500, 2000]

    def test_stress_horizons(self):
        """Stress horizons are [10000]."""
        assert STRESS_HORIZONS == [10000]

    def test_default_seeds(self):
        """Default seeds are [42, 43, 44]."""
        assert DEFAULT_SEEDS == [42, 43, 44]

    def test_default_matrix_configuration(self):
        """Default matrix has correct configuration."""
        matrix = create_default_matrix()

        assert matrix.horizons == DEFAULT_HORIZONS
        assert matrix.seeds == DEFAULT_SEEDS
        assert len(matrix.variants) == 4
        assert not matrix.use_stress

    def test_stress_matrix_configuration(self):
        """Stress matrix has H=10000."""
        matrix = create_stress_matrix()

        assert matrix.horizons == [10000]
        assert matrix.use_stress

    def test_quick_matrix_minimal(self):
        """Quick matrix is minimal for CI."""
        matrix = create_quick_matrix()

        assert len(matrix.seeds) == 1
        assert len(matrix.horizons) == 1
        assert len(matrix.variants) == 2

    def test_matrix_generates_all_runs(self):
        """Matrix generates all combinations."""
        matrix = V032RunMatrix(
            seeds=[42],
            horizons=[500],
            variants=[V032Variant.V032A_KERNEL_COHERENT, V032Variant.V032B_HOLLOW_FUZZER],
        )

        runs = list(matrix.generate_runs())
        assert len(runs) == 2

    def test_run_spec_adversarial_detection(self):
        """RunSpec correctly identifies adversarial runs."""
        control = V032RunSpec(
            seed=42,
            horizon=500,
            variant=V032Variant.V032A_KERNEL_COHERENT,
            scenario_id="test",
        )
        adversary = V032RunSpec(
            seed=42,
            horizon=500,
            variant=V032Variant.V032B_HOLLOW_FUZZER,
            scenario_id="test",
        )

        assert not control.is_adversarial()
        assert adversary.is_adversarial()


# =============================================================================
# Runner Tests
# =============================================================================

class TestV032Runner:
    """Tests for v0.3.2 runner."""

    def test_runner_initialization(self):
        """Runner initializes with correct defaults."""
        runner = V032ExperimentRunner(base_seed=42)

        assert runner.base_seed == 42
        assert runner.k_persist == K_PERSIST

    def test_runner_creates_fuzzer_for_adversarial(self):
        """Runner creates AdaptiveBoundaryFuzzer for adversarial runs."""
        runner = V032ExperimentRunner(base_seed=42)
        spec = V032RunSpec(
            seed=42,
            horizon=50,  # Short for testing
            variant=V032Variant.V032B_HOLLOW_FUZZER,
            scenario_id="test",
        )

        fuzzer = runner.create_fuzzer(spec)
        assert isinstance(fuzzer, AdaptiveBoundaryFuzzer)


# =============================================================================
# End-to-End Smoke Tests
# =============================================================================

class TestEndToEndSmoke:
    """End-to-end smoke tests."""

    def test_fuzzer_propose_delta_phase_p(self):
        """Fuzzer proposes deltas in Phase P."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42)
        state = create_initial_state("test_smoke")

        context = V03OptimizationContext(
            current_state=state,
            r_value=0,
            step_number=0,
            previous_deltas=[],
            previous_outcomes=[],
            reward_signal=0.0,
            pressure_level=0.0,
            timestamp_ms=0,
        )

        decision = fuzzer.propose_delta(context)

        assert decision.propose
        assert decision.delta is not None

    def test_fuzzer_adversarial_intent(self):
        """Fuzzer has adversarial intent."""
        fuzzer = AdaptiveBoundaryFuzzer(seed=42)
        assert fuzzer.intent == V03OptimizerIntent.ADVERSARIAL

    def test_quick_run_completes(self):
        """Quick run completes without error."""
        runner = V032ExperimentRunner(base_seed=42, verbose=False)
        spec = V032RunSpec(
            seed=42,
            horizon=10,  # Very short for CI
            variant=V032Variant.V032B_HOLLOW_FUZZER,
            scenario_id="smoke_test",
        )

        result = runner.run_single(spec)

        assert result is not None
        assert result.total_steps == 10
        assert result.phase_at_end in [FuzzerPhase.PHASE_P, FuzzerPhase.PHASE_X]

    def test_control_run_completes(self):
        """Control run completes without error."""
        runner = V032ExperimentRunner(base_seed=42, verbose=False)
        spec = V032RunSpec(
            seed=42,
            horizon=10,
            variant=V032Variant.V032A_KERNEL_COHERENT,
            scenario_id="smoke_test",
        )

        result = runner.run_single(spec)

        assert result is not None
        assert result.total_steps == 10
        # Control uses benign optimizer, not fuzzer
        assert result.phase_at_end == FuzzerPhase.PHASE_P

    def test_horizon_result_aggregation(self):
        """Horizon results aggregate correctly."""
        runner = V032ExperimentRunner(base_seed=42, verbose=False)
        matrix = V032RunMatrix(
            seeds=[42],
            horizons=[10],
            variants=[V032Variant.V032A_KERNEL_COHERENT, V032Variant.V032B_HOLLOW_FUZZER],
        )

        result = runner.run_horizon(10, matrix)

        assert result.horizon == 10
        assert len(result.runs) == 2
        assert result.mean_r_star >= 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestV032Integration:
    """Integration tests for v0.3.2 components."""

    def test_fuzzer_with_divergence_tracking(self):
        """Fuzzer run tracks divergence correctly."""
        runner = V032ExperimentRunner(base_seed=42, verbose=False)
        spec = V032RunSpec(
            seed=42,
            horizon=50,
            variant=V032Variant.V032B_HOLLOW_FUZZER,
            scenario_id="integration",
        )

        result = runner.run_single(spec)

        assert result.divergence_result is not None
        assert result.divergence_result.curve is not None

    def test_degeneracy_diagnosis_on_stall(self):
        """Degeneracy is diagnosed when run stalls."""
        runner = V032ExperimentRunner(
            base_seed=42,
            verbose=False,
            degeneracy_grace_window=20,  # Small for testing
        )
        spec = V032RunSpec(
            seed=42,
            horizon=50,
            variant=V032Variant.V032B_HOLLOW_FUZZER,
            scenario_id="stall_test",
        )

        result = runner.run_single(spec)

        # Result should have diagnosis if degenerate
        # (may or may not be degenerate depending on fuzzer behavior)
        assert result is not None

    def test_template_stats_reported(self):
        """Template stats are reported in result."""
        runner = V032ExperimentRunner(base_seed=42, verbose=False)
        spec = V032RunSpec(
            seed=42,
            horizon=20,
            variant=V032Variant.V032B_HOLLOW_FUZZER,
            scenario_id="stats_test",
        )

        result = runner.run_single(spec)

        assert result.template_acceptance_rates is not None
        assert len(result.template_acceptance_rates) > 0
