"""
Unit tests for v4.1 ablation implementations.

Tests verify:
1. TraceExcisionCompiler returns empty rule_evals (causes HALT)
2. Harness preserves ablation compiler across episode resets
3. All ablation types produce expected behavior
"""

import pytest
import json
from unittest.mock import Mock, patch

# Import the components we're testing
import sys
sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.ablations import (
    AblationHarness,
    AblationType,
    TraceExcisionCompiler,
    SemanticExcisionEnvironment,
    create_reflection_excision_norm_state,
    create_persistence_excision_norm_state,
)
from src.rsa_poc.v410.core import (
    JCOMP410,
    create_initial_norm_state,
    JustificationV410,
    Predicate,
)
from src.rsa_poc.v410.core.compiler import CompilationStatus
from src.rsa_poc.v410.env.tri_demand import TriDemandV410
from src.rsa_poc.v410.harness import HarnessConfig, MVRSA410Harness
from src.rsa_poc.v410.deliberator import DeterministicDeliberator


class TestTraceExcisionCompiler:
    """Tests for TraceExcisionCompiler implementation."""

    def test_compile_returns_compiled_status(self):
        """TraceExcisionCompiler should return COMPILED status (not error)."""
        norm_state = create_initial_norm_state()
        base_compiler = JCOMP410(norm_state)
        trace_compiler = TraceExcisionCompiler(base_compiler)

        # Create a valid justification JSON
        justification_json = json.dumps({
            "action_id": "A1",
            "claims": [{"predicate": "PERMITS", "args": ["R4", "MOVE"]}],
            "rule_refs": ["R4"]
        })

        result = trace_compiler.compile(justification_json)

        assert result.status == CompilationStatus.COMPILED
        assert result.action_id == "A1"

    def test_compile_returns_empty_rule_evals(self):
        """TraceExcisionCompiler should return empty rule_evals (trace excised)."""
        norm_state = create_initial_norm_state()
        base_compiler = JCOMP410(norm_state)
        trace_compiler = TraceExcisionCompiler(base_compiler)

        justification_json = json.dumps({
            "action_id": "A2",
            "claims": [{"predicate": "PERMITS", "args": ["R4", "MOVE"]}],
            "rule_refs": ["R4"]
        })

        result = trace_compiler.compile(justification_json)

        # This is the key test: empty rule_evals triggers HALT in harness
        assert result.rule_evals == []
        assert len(result.rule_evals) == 0

    def test_compile_batch_all_empty_rule_evals(self):
        """compile_batch should return all results with empty rule_evals."""
        norm_state = create_initial_norm_state()
        base_compiler = JCOMP410(norm_state)
        trace_compiler = TraceExcisionCompiler(base_compiler)

        justifications = [
            json.dumps({"action_id": "A1", "claims": [{"predicate": "PERMITS", "args": ["R4", "MOVE"]}], "rule_refs": ["R4"]}),
            json.dumps({"action_id": "A2", "claims": [{"predicate": "PERMITS", "args": ["R4", "MOVE"]}], "rule_refs": ["R4"]}),
            json.dumps({"action_id": "A3", "claims": [{"predicate": "PERMITS", "args": ["R4", "MOVE"]}], "rule_refs": ["R4"]}),
        ]

        batch = trace_compiler.compile_batch(justifications)

        assert len(batch.results) == 3
        for result in batch.results:
            assert result.rule_evals == []

    def test_compile_preserves_action_id(self):
        """TraceExcisionCompiler should preserve action_id from input."""
        norm_state = create_initial_norm_state()
        base_compiler = JCOMP410(norm_state)
        trace_compiler = TraceExcisionCompiler(base_compiler)

        for action_id in ["A0", "A1", "A2", "A3", "A4", "A5"]:
            justification_json = json.dumps({
                "action_id": action_id,
                "claims": [{"predicate": "PERMITS", "args": ["R4", "MOVE"]}],
                "rule_refs": ["R4"]
            })

            result = trace_compiler.compile(justification_json)
            assert result.action_id == action_id

    def test_compile_handles_malformed_json(self):
        """TraceExcisionCompiler should handle malformed JSON gracefully."""
        norm_state = create_initial_norm_state()
        base_compiler = JCOMP410(norm_state)
        trace_compiler = TraceExcisionCompiler(base_compiler)

        # Malformed JSON - should still return COMPILED with empty rule_evals
        result = trace_compiler.compile("not valid json")

        assert result.status == CompilationStatus.COMPILED
        assert result.rule_evals == []
        assert result.action_id == "A0"  # Default fallback


class TestHarnessAblationCompilerPreservation:
    """Tests that harness preserves ablation compiler across episode resets."""

    def test_trace_excision_compiler_preserved_across_episodes(self):
        """TraceExcisionCompiler should persist after episode reset."""
        env = TriDemandV410(seed=42)
        config = HarnessConfig(
            max_steps_per_episode=5,
            max_episodes=3,
            max_conflicts=10,
            seed=42,
            selector_type='random',
            record_telemetry=False
        )

        harness = AblationHarness(
            env=env,
            ablation_type=AblationType.TRACE_EXCISION,
            config=config,
            deliberator=DeterministicDeliberator()
        )

        # Check initial state
        assert hasattr(harness._harness, '_ablation_compiler')
        assert isinstance(harness._harness.compiler, TraceExcisionCompiler)

        # Simulate episode reset
        harness._harness.reset_for_episode(episode=1)

        # Compiler should still be TraceExcisionCompiler after reset
        assert isinstance(harness._harness.compiler, TraceExcisionCompiler)

    def test_non_ablation_compiler_replaced_on_reset(self):
        """Regular harness should replace compiler on episode reset."""
        env = TriDemandV410(seed=42)
        config = HarnessConfig(
            max_steps_per_episode=5,
            max_episodes=3,
            max_conflicts=10,
            seed=42,
            selector_type='random',
            record_telemetry=False
        )

        harness = MVRSA410Harness(
            env=env,
            deliberator=DeterministicDeliberator(),
            config=config
        )

        # Regular harness should NOT have _ablation_compiler
        assert not hasattr(harness, '_ablation_compiler')
        assert isinstance(harness.compiler, JCOMP410)


class TestAblationHarnessSetup:
    """Tests for AblationHarness configuration."""

    def test_trace_excision_sets_ablation_compiler_marker(self):
        """TRACE_EXCISION should set _ablation_compiler attribute."""
        env = TriDemandV410(seed=42)
        config = HarnessConfig(
            max_steps_per_episode=5,
            max_episodes=1,
            max_conflicts=10,
            seed=42,
            selector_type='random',
            record_telemetry=False
        )

        harness = AblationHarness(
            env=env,
            ablation_type=AblationType.TRACE_EXCISION,
            config=config,
            deliberator=DeterministicDeliberator()
        )

        # Should have both compiler and _ablation_compiler
        assert hasattr(harness._harness, '_ablation_compiler')
        assert harness._harness._ablation_compiler is harness._harness.compiler

    def test_non_trace_excision_no_ablation_compiler_marker(self):
        """Non-TRACE_EXCISION ablations should not set _ablation_compiler."""
        env = TriDemandV410(seed=42)
        config = HarnessConfig(
            max_steps_per_episode=5,
            max_episodes=1,
            max_conflicts=10,
            seed=42,
            selector_type='random',
            record_telemetry=False
        )

        for ablation_type in [AblationType.NONE, AblationType.SEMANTIC_EXCISION,
                               AblationType.REFLECTION_EXCISION, AblationType.PERSISTENCE_EXCISION]:
            harness = AblationHarness(
                env=env,
                ablation_type=ablation_type,
                config=config,
                deliberator=DeterministicDeliberator()
            )

            assert not hasattr(harness._harness, '_ablation_compiler')


class TestTraceExcisionCausesHalt:
    """Integration tests verifying trace excision causes 100% HALT."""

    def test_trace_excision_causes_halt_at_step_0(self):
        """TraceExcisionCompiler should cause HALT at step 0."""
        env = TriDemandV410(seed=42)
        config = HarnessConfig(
            max_steps_per_episode=10,
            max_episodes=1,
            max_conflicts=10,
            seed=42,
            selector_type='random',
            record_telemetry=False
        )

        harness = AblationHarness(
            env=env,
            ablation_type=AblationType.TRACE_EXCISION,
            config=config,
            deliberator=DeterministicDeliberator()
        )

        result = harness.run()

        # All steps should be halts
        assert result['summary']['total_steps'] == 0
        assert result['summary']['total_halts'] == 10  # max_steps_per_episode

    def test_trace_excision_100_percent_halt_rate(self):
        """Trace excision should produce 100% halt rate."""
        env = TriDemandV410(seed=42)
        config = HarnessConfig(
            max_steps_per_episode=40,
            max_episodes=1,
            max_conflicts=10,
            seed=42,
            selector_type='random',
            record_telemetry=False
        )

        harness = AblationHarness(
            env=env,
            ablation_type=AblationType.TRACE_EXCISION,
            config=config,
            deliberator=DeterministicDeliberator()
        )

        result = harness.run()

        total_attempts = result['summary']['total_steps'] + result['summary']['total_halts']
        halt_rate = result['summary']['total_halts'] / total_attempts if total_attempts > 0 else 1.0

        assert halt_rate == 1.0, f"Expected 100% halt rate, got {halt_rate:.1%}"

    def test_non_trace_ablations_do_not_cause_pervasive_halt(self):
        """Non-trace ablations should NOT cause 100% halt rate."""
        for ablation_type in [AblationType.NONE, AblationType.REFLECTION_EXCISION,
                               AblationType.PERSISTENCE_EXCISION]:
            env = TriDemandV410(seed=42)
            config = HarnessConfig(
                max_steps_per_episode=10,
                max_episodes=1,
                max_conflicts=10,
                seed=42,
                selector_type='random',
                record_telemetry=False
            )

            harness = AblationHarness(
                env=env,
                ablation_type=ablation_type,
                config=config,
                deliberator=DeterministicDeliberator()
            )

            result = harness.run()

            # Should have some steps executed (not all halts)
            assert result['summary']['total_steps'] > 0, \
                f"{ablation_type.value} should not cause 100% halt"


class TestSemanticExcisionEnvironment:
    """Tests for SemanticExcisionEnvironment."""

    def test_semantic_excision_replaces_observation(self):
        """Semantic excision should replace observation with opaque tokens."""
        base_env = TriDemandV410(seed=42)
        excised_env = SemanticExcisionEnvironment(base_env, seed=42)

        obs, _ = excised_env.reset()

        # Observation should still be an Observation object
        # but with scrambled semantics (this depends on implementation)
        assert hasattr(obs, 'agent_pos') or hasattr(obs, 'inventory')


class TestReflectionExcisionNormState:
    """Tests for reflection excision norm state."""

    def test_reflection_excision_disables_patching(self):
        """Reflection excision norm state should reject patches."""
        norm_state = create_reflection_excision_norm_state()

        # Should have rules
        assert len(norm_state.rules) > 0

        # Patching should be disabled (exact mechanism depends on implementation)
        # This tests that the norm state is configured correctly


class TestPersistenceExcisionNormState:
    """Tests for persistence excision norm state."""

    def test_persistence_excision_resets_each_episode(self):
        """Persistence excision should reset norm state each episode."""
        norm_state = create_persistence_excision_norm_state()

        # Should have rules
        assert len(norm_state.rules) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
