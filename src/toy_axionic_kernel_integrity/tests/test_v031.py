"""
Tests for v0.3.1 (KNS Stage 2).

Tests cover:
- Run matrix determinism
- Outcome observation (only allowed signals)
- Pressure metrics (N_R logic, tightening classifier)
- Resource meter sanity
- Adaptive attack adaptation behavior
- End-to-end smoke test
"""

import pytest
import time
from dataclasses import FrozenInstanceError
from typing import List

from toy_aki.kernel.outcome import (
    DeltaOutcome,
    RejectionReasonCode,
    NearFailureFlag,
)
from toy_aki.kernel.resource_meter import (
    ResourceMeter,
    StepResourceRecord,
    ResourceSummary,
)
from toy_aki.kernel.pressure_metrics import (
    PressureMetricsTracker,
    TighteningEvent,
    classify_delta_effect,
    K_ADAPT,
)
from toy_aki.harness.v031_matrix import (
    RunMatrix,
    RunSpec,
    V031Variant,
    AdaptiveAttackType,
    create_default_matrix,
    create_quick_matrix,
)
from toy_aki.attacks.kns.adaptive_attacks import (
    AdaptiveAttack,
    AdaptivePolicyMimicry,
    AdaptiveShortcutting,
    AdaptiveConstraintCosmeticization,
    create_adaptive_attack,
)
from toy_aki.agents.external_optimizer import (
    V03OptimizationContext,
    V03OptimizerDecision,
)
from toy_aki.kernel.reflective import KernelState, create_initial_state, Delta, DeltaType


class TestDeltaOutcome:
    """Test DeltaOutcome schema."""

    def test_create_accepted_outcome(self):
        """Test creating an accepted outcome."""
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=5,
            near_failure_flags=frozenset(),
        )

        assert outcome.accepted is True
        assert outcome.r_incremented is True
        assert outcome.r_value_after == 5
        assert outcome.rejection_reason_code == RejectionReasonCode.ACCEPTED

    def test_create_rejected_outcome(self):
        """Test creating a rejected outcome."""
        outcome = DeltaOutcome(
            accepted=False,
            rejection_reason_code=RejectionReasonCode.INADMISSIBLE_P5,
            r_incremented=False,
            r_value_after=4,
            near_failure_flags=frozenset({NearFailureFlag.NF_REJECTION}),
        )

        assert outcome.accepted is False
        assert outcome.r_incremented is False
        assert outcome.rejection_reason_code == RejectionReasonCode.INADMISSIBLE_P5
        assert NearFailureFlag.NF_REJECTION in outcome.near_failure_flags

    def test_outcome_is_frozen(self):
        """Verify DeltaOutcome is immutable."""
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=5,
            near_failure_flags=frozenset(),
        )

        with pytest.raises(FrozenInstanceError):
            outcome.r_value_after = 10

    def test_outcome_only_allowed_signals(self):
        """Verify outcome only contains allowed signals (no kernel internals)."""
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=5,
            near_failure_flags=frozenset(),
        )

        # Verify no access to internal state
        assert not hasattr(outcome, "kernel_state")
        assert not hasattr(outcome, "evaluability_state")
        assert not hasattr(outcome, "internal_R")
        assert not hasattr(outcome, "acv_history")

        # Only allowed fields exist
        allowed = {"accepted", "rejection_reason_code",
                   "r_incremented", "r_dimensions_changed", "r_value_after",
                   "near_failure_flags", "step_index"}
        for field_name in outcome.__dataclass_fields__:
            assert field_name in allowed

    def test_rejection_reason_codes_complete(self):
        """Verify all expected rejection reason codes exist."""
        expected = [
            "ACCEPTED", "INADMISSIBLE_P5", "P2P_DELEGATION_VIOLATION",
            "EVALUABILITY_ATTRIBUTION_FAIL", "EVALUABILITY_REJECTION_FAIL",
            "EVALUABILITY_REJECTION_CHAIN_FAIL", "EVALUABILITY_DELEGATION_DETECT_FAIL",
            "DELTA_INVALID_FORMAT", "DELTA_APPLICATION_ERROR",
            "WRAPPER_DELEGATION_DETECTED", "RESOURCE_BUDGET_EXCEEDED",
        ]
        for name in expected:
            assert hasattr(RejectionReasonCode, name)


class TestResourceMeter:
    """Test ResourceMeter."""

    def test_meter_creation(self):
        """Test creating a resource meter."""
        meter = ResourceMeter(enforce_caps=False)
        assert meter._enforce_caps is False
        assert len(meter._records) == 0

    def test_record_step(self):
        """Test recording a step."""
        meter = ResourceMeter(enforce_caps=False)
        meter.start_run()
        meter.start_step(1)
        record = meter.end_step()

        assert record.step_index == 1
        assert record.step_time_ms >= 0
        assert record.memory_bytes >= 0

    def test_get_summary(self):
        """Test getting resource summary."""
        meter = ResourceMeter(enforce_caps=False)
        meter.start_run()
        for i in range(3):
            meter.start_step(i)
            time.sleep(0.001)
            meter.end_step()

        summary = meter.get_summary()
        assert summary.total_steps == 3
        assert summary.total_time_ms > 0

    def test_synthesis_context_manager(self):
        """Test synthesis timing context manager."""
        meter = ResourceMeter(enforce_caps=False)
        meter.start_run()
        meter.start_step(1)

        with meter.measure_synthesis():
            time.sleep(0.01)  # 10ms

        record = meter.end_step()
        # Should have recorded synthesis time
        assert record.delta_synthesis_time_ms >= 10.0

    def test_reset(self):
        """Test resetting the meter."""
        meter = ResourceMeter(enforce_caps=False)
        meter.start_run()
        meter.start_step(1)
        meter.end_step()
        assert len(meter._records) == 1

        meter.start_run()  # start_run resets
        assert len(meter._records) == 0


class TestPressureMetrics:
    """Test PressureMetricsTracker."""

    def test_tracker_creation(self):
        """Test creating a tracker."""
        tracker = PressureMetricsTracker()
        assert tracker._total_steps == 0
        assert len(tracker._n_r_records) == 0

    def test_record_step_with_r_increment(self):
        """Test recording a step that incremented R."""
        tracker = PressureMetricsTracker()
        from toy_aki.kernel.watchdog import current_time_ms

        # Create a delta since record_step only updates _current_r when delta is provided
        delta = Delta(
            delta_id="test",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test",),
            source="test",
            rationale="test",
            timestamp_ms=current_time_ms(),
        )

        tracker.record_step(
            step_index=1,
            delta=delta,
            accepted=True,
            r_incremented=True,
            new_r_value=5,
        )

        assert tracker._current_r == 5

    def test_nr_accumulation(self):
        """Test N_R accumulation (steps since last R increment)."""
        tracker = PressureMetricsTracker()

        # Create a dummy delta
        from toy_aki.kernel.watchdog import current_time_ms
        delta = Delta(
            delta_id="test",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test",),
            source="test",
            rationale="test",
            timestamp_ms=current_time_ms(),
        )

        # Steps 1-3: rejected (count as N_R)
        for i in range(1, 4):
            tracker.record_step(i, delta=delta, accepted=False, r_incremented=False,
                              new_r_value=0, rejection_reason=RejectionReasonCode.INADMISSIBLE_P5)

        assert tracker._rejected_since_last_r == 3

        # Step 4: R increments (resets N_R)
        tracker.record_step(4, delta=delta, accepted=True, r_incremented=True, new_r_value=1)
        assert tracker._rejected_since_last_r == 0
        assert len(tracker._n_r_records) == 1

    def test_k_adapt_constant(self):
        """Verify K_ADAPT is 50."""
        assert K_ADAPT == 50

    def test_classify_delta_effect(self):
        """Test delta effect classifier."""
        # Create different delta types and test classification
        from toy_aki.kernel.watchdog import current_time_ms

        add_delta = Delta(
            delta_id="add",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test",),
            source="test",
            rationale="test",
            timestamp_ms=current_time_ms(),
        )

        result = classify_delta_effect(add_delta)
        # classify_delta_effect returns "tighten", "loosen", or "neutral"
        assert result in ("tighten", "loosen", "neutral")

    def test_tightening_events(self):
        """Test tightening event tracking."""
        tracker = PressureMetricsTracker()
        from toy_aki.kernel.watchdog import current_time_ms

        delta = Delta(
            delta_id="test",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test",),
            source="test",
            rationale="test",
            timestamp_ms=current_time_ms(),
        )

        tracker.record_step(1, delta=delta, accepted=True, r_incremented=True, new_r_value=1)

        events = tracker._tightening_events
        assert len(events) == 1
        assert events[0].effect in ("tighten", "loosen", "neutral")

    def test_get_summary(self):
        """Test getting pressure metrics summary."""
        tracker = PressureMetricsTracker()
        from toy_aki.kernel.watchdog import current_time_ms

        delta = Delta(
            delta_id="test",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test",),
            source="test",
            rationale="test",
            timestamp_ms=current_time_ms(),
        )

        # Simulate 10 steps with some R increments
        for i in range(10):
            tracker.record_step(
                step_index=i,
                delta=delta,
                accepted=(i % 3 == 0),
                r_incremented=(i % 5 == 0),
                new_r_value=i // 5,
                rejection_reason=RejectionReasonCode.INADMISSIBLE_P5 if i % 3 != 0 else None,
            )

        summary = tracker.get_summary()
        assert summary.total_steps == 10
        assert summary.final_r >= 0


class TestRunMatrix:
    """Test RunMatrix for v0.3.1."""

    def test_create_matrix(self):
        """Test creating a run matrix."""
        matrix = RunMatrix()
        runs = list(matrix.generate_runs())
        assert len(runs) > 0

    def test_run_spec_is_frozen(self):
        """Verify RunSpec is immutable."""
        spec = RunSpec(
            seed=42,
            horizon=50,
            variant=V031Variant.V031A_KERNEL_COHERENT,
            attack_type=None,
            scenario_id="test",
        )

        with pytest.raises(FrozenInstanceError):
            spec.seed = 100

    def test_deterministic_scenario_id(self):
        """Test that scenario IDs are deterministic."""
        matrix = RunMatrix()
        id1 = matrix.generate_scenario_id(42, 50)
        id2 = matrix.generate_scenario_id(42, 50)

        # Same parameters = same scenario ID
        assert id1 == id2

    def test_matched_regime_runs(self):
        """Test that matched-regime runs share scenario_id."""
        matrix = create_default_matrix()

        # Get matched pairs for H=50, seed=42
        pairs = matrix.generate_matched_pairs(horizon=50, seed=42)

        # All pairs should have same scenario_id
        if pairs:
            scenario_id = pairs[0][0].scenario_id
            for control, adversary in pairs:
                assert control.scenario_id == scenario_id
                assert adversary.scenario_id == scenario_id

    def test_horizon_ladder(self):
        """Test horizon ladder: 50, 200, 500, 2000."""
        matrix = create_default_matrix()

        horizons = matrix.horizons
        assert 50 in horizons
        assert 200 in horizons
        assert 500 in horizons
        assert 2000 in horizons

    def test_quick_matrix(self):
        """Test quick matrix is smaller."""
        quick = create_quick_matrix()
        default = create_default_matrix()

        assert quick.count_runs() < default.count_runs()

    def test_variants(self):
        """Test all v0.3.1 variants."""
        expected = [
            V031Variant.V031A_KERNEL_COHERENT,
            V031Variant.V031B_HOLLOW_ADAPTIVE,
            V031Variant.V031C_UNBOUNDED_MEASURED,
            V031Variant.V031D_SELF_COMPRESS_ADAPTIVE,
        ]
        for v in expected:
            assert v in V031Variant


class TestAdaptiveAttacks:
    """Test adaptive attack implementations."""

    @pytest.fixture
    def mock_context(self):
        """Create mock optimization context."""
        state = create_initial_state("test_state")
        return V03OptimizationContext(
            current_state=state,
            r_value=0,
            step_number=1,
            previous_deltas=[],
            previous_outcomes=[],
        )

    def test_create_adaptive_policy_mimicry(self):
        """Test creating AdaptivePolicyMimicry."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=42,
        )
        assert isinstance(attack, AdaptivePolicyMimicry)
        assert attack.attack_type == AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY

    def test_create_adaptive_shortcutting(self):
        """Test creating AdaptiveShortcutting."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_SHORTCUTTING,
            seed=42,
        )
        assert isinstance(attack, AdaptiveShortcutting)

    def test_create_adaptive_cosmeticization(self):
        """Test creating AdaptiveConstraintCosmeticization."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION,
            seed=42,
        )
        assert isinstance(attack, AdaptiveConstraintCosmeticization)

    def test_attack_observe_outcome(self):
        """Test that attacks can observe outcomes."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=42,
        )

        outcome = DeltaOutcome(
            accepted=False,
            rejection_reason_code=RejectionReasonCode.INADMISSIBLE_P5,
            r_incremented=False,
            r_value_after=0,
            near_failure_flags=frozenset(),
        )

        # Should not raise
        attack.observe_outcome(outcome)
        assert len(attack._outcomes) == 1

    def test_attack_adapts_to_rejections(self, mock_context):
        """Test that attacks adapt based on rejection patterns."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=42,
        )

        # Simulate repeated rejections for same reason
        for i in range(5):
            outcome = DeltaOutcome(
                accepted=False,
                rejection_reason_code=RejectionReasonCode.EVALUABILITY_ATTRIBUTION_FAIL,
                r_incremented=False,
                r_value_after=0,
                near_failure_flags=frozenset(),
            )
            attack.observe_outcome(outcome)

        # Attack should have marked some patterns as blocked
        assert len(attack._rejected_patterns) > 0
        assert attack._rejected_patterns[RejectionReasonCode.EVALUABILITY_ATTRIBUTION_FAIL] == 5

    def test_attack_targets_near_failures(self):
        """Test that attacks target near-failure capabilities."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION,
            seed=42,
        )

        # Observe outcome with near-failure flag
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=1,
            near_failure_flags=frozenset({NearFailureFlag.NF_ATTRIBUTION}),
        )
        attack.observe_outcome(outcome)

        # Attack should track observed near-failures
        assert NearFailureFlag.NF_ATTRIBUTION in attack._observed_near_failures

    def test_attack_propose_delta(self, mock_context):
        """Test that attacks can propose deltas."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=42,
        )

        decision = attack.propose_delta(mock_context)
        assert isinstance(decision, V03OptimizerDecision)

    def test_attack_is_seeded(self):
        """Test that attacks are seeded and deterministic."""
        attack1 = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=12345,
        )
        attack2 = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=12345,
        )

        # Same seed = same initial state
        assert attack1._seed == attack2._seed

    def test_attack_reset(self, mock_context):
        """Test that attack reset clears state."""
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_SHORTCUTTING,
            seed=42,
        )

        # Make some proposals
        attack.propose_delta(mock_context)
        attack.propose_delta(mock_context)

        # Observe some outcomes
        outcome = DeltaOutcome(
            accepted=False,
            rejection_reason_code=RejectionReasonCode.INADMISSIBLE_P5,
            r_incremented=False,
            r_value_after=0,
            near_failure_flags=frozenset(),
        )
        attack.observe_outcome(outcome)

        assert attack._proposal_count > 0
        assert len(attack._outcomes) > 0

        # Reset
        attack.reset()

        assert attack._proposal_count == 0
        assert len(attack._outcomes) == 0


class TestAdaptiveAttackIntegration:
    """Integration tests for adaptive attacks."""

    def test_attack_no_kernel_access(self):
        """Verify attacks cannot access kernel internals from outcome."""
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=5,
            near_failure_flags=frozenset(),
        )

        # Create attack
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=42,
        )

        # Observe outcome
        attack.observe_outcome(outcome)

        # Verify attack only has access to allowed signals
        # (outcome fields, not kernel state)
        last_outcome = attack._outcomes[-1]
        assert hasattr(last_outcome, "r_value_after")
        assert hasattr(last_outcome, "rejection_reason_code")
        assert not hasattr(last_outcome, "kernel_state")
        assert not hasattr(last_outcome, "internal_acv")

    def test_shortcutting_phase_transitions(self):
        """Test shortcutting attack phase transitions."""
        attack = AdaptiveShortcutting(seed=42)

        assert attack._shortcut_phase == "probe"

        # Simulate high rejection rate
        for i in range(15):
            outcome = DeltaOutcome(
                accepted=False,
                rejection_reason_code=RejectionReasonCode.INADMISSIBLE_P5,
                r_incremented=False,
                r_value_after=0,
                near_failure_flags=frozenset(),
            )
            attack.observe_outcome(outcome)

        # Should transition to adapt phase
        assert attack._shortcut_phase == "adapt"

    def test_cosmeticization_targets_specific_capability(self):
        """Test cosmeticization attack targets specific near-failures."""
        attack = AdaptiveConstraintCosmeticization(seed=42)

        # Initially no target
        assert attack._targeting_capability is None

        # Observe near-failure
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=1,
            near_failure_flags=frozenset({NearFailureFlag.NF_DELEGATION_DETECT}),
        )
        attack.observe_outcome(outcome)

        # Should now have target
        assert attack._targeting_capability == NearFailureFlag.NF_DELEGATION_DETECT


class TestV031EndToEnd:
    """End-to-end smoke tests for v0.3.1."""

    def test_smoke_create_and_observe(self):
        """Basic smoke test: create attack, propose, observe."""
        # Create attack
        attack = create_adaptive_attack(
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=42,
        )

        # Create context
        state = create_initial_state("test_state")
        context = V03OptimizationContext(
            current_state=state,
            r_value=0,
            step_number=1,
            previous_deltas=[],
            previous_outcomes=[],
        )

        # Propose delta
        decision = attack.propose_delta(context)
        assert decision is not None

        # Create outcome
        outcome = DeltaOutcome(
            accepted=True,
            rejection_reason_code=RejectionReasonCode.ACCEPTED,
            r_incremented=True,
            r_value_after=1,
            near_failure_flags=frozenset(),
        )

        # Observe outcome
        attack.observe_outcome(outcome)
        assert len(attack._outcomes) == 1

    def test_smoke_resource_meter_integration(self):
        """Smoke test resource meter in v0.3.1 context."""
        meter = ResourceMeter(enforce_caps=False)
        meter.start_run()

        # Simulate a run
        for step in range(10):
            meter.start_step(step)
            with meter.measure_synthesis():
                time.sleep(0.001)  # 1ms synthesis
            meter.end_step()

        summary = meter.get_summary()
        assert summary.total_steps == 10
        assert summary.peak_memory_bytes >= 0

    def test_smoke_pressure_metrics_integration(self):
        """Smoke test pressure metrics in v0.3.1 context."""
        tracker = PressureMetricsTracker()
        from toy_aki.kernel.watchdog import current_time_ms

        delta = Delta(
            delta_id="test",
            delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
            target_dimension="admissibility",
            payload=("test",),
            source="test",
            rationale="test",
            timestamp_ms=current_time_ms(),
        )

        # Simulate a run with occasional R increments
        r_value = 0
        for step in range(50):
            incremented = (step % 10 == 0)
            if incremented:
                r_value += 1
            tracker.record_step(step, delta=delta, accepted=incremented,
                              r_incremented=incremented, new_r_value=r_value)

        summary = tracker.get_summary()
        assert summary.total_steps == 50

    def test_smoke_matrix_coverage(self):
        """Smoke test matrix generates expected coverage."""
        matrix = create_quick_matrix()

        # Should cover specified variants
        variants_seen = set()
        horizons_seen = set()

        for run in matrix.generate_runs():
            variants_seen.add(run.variant)
            horizons_seen.add(run.horizon)

        assert V031Variant.V031A_KERNEL_COHERENT in variants_seen
        assert len(horizons_seen) >= 1
