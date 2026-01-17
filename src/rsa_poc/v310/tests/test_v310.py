"""Unit tests for v3.1 infrastructure.

Tests:
1. Tokenizer and PAD stability
2. Gate P4 buffer management
3. Novelty detection
4. Normative state manager
5. V310AblationHarness integration
"""

import pytest
import json
import hashlib
from typing import Set, Tuple

# Import v3.1 components
from src.rsa_poc.v310.tokenizer import (
    V310Tokenizer,
    get_tokenizer,
    PAD_STR,
    run_pad_self_test,
    TokenizerConfig,
)
from src.rsa_poc.v310.gate_p4 import (
    GateP4,
    GateP4Config,
    GateP4Violation,
    serialize_precedent_record,
    create_empty_precedent_buffer,
    ceil_to_32,
)
from src.rsa_poc.v310.harness import (
    V310AblationHarness,
    V310AblationSpec,
    V310RunConfig,
    V310InvalidReason,
    NoveltyDetector,
    NormativeStateManager,
)


# ============================================================================
# Tokenizer Tests
# ============================================================================

class TestTokenizer:
    """Tests for V310Tokenizer."""

    def test_tokenizer_initialization(self):
        """Tokenizer initializes with correct provider/model."""
        tokenizer = get_tokenizer("anthropic", "claude-sonnet-4-20250514")
        assert tokenizer.provider == "anthropic"
        assert tokenizer.model_id == "claude-sonnet-4-20250514"
        assert tokenizer._tokenizer_id == "cl100k_base"

    def test_token_counting(self):
        """Token counting produces consistent results."""
        tokenizer = get_tokenizer()

        # Same text should produce same count
        text = "The agent must choose an action"
        count1 = tokenizer.count_tokens(text)
        count2 = tokenizer.count_tokens(text)
        assert count1 == count2
        assert count1 > 0

    def test_pad_stability(self):
        """PAD_STR passes all stability requirements."""
        tokenizer = get_tokenizer()
        is_stable, token_count, msg = tokenizer.validate_pad_stability(PAD_STR)

        assert is_stable, f"PAD not stable: {msg}"
        assert token_count == 1, f"PAD should be 1 token, got {token_count}"

    def test_pad_linear_scaling(self):
        """PAD repetition scales linearly."""
        tokenizer = get_tokenizer()
        base_count = tokenizer.count_tokens(PAD_STR)

        for k in [2, 5, 10, 50, 100]:
            repeated_count = tokenizer.count_tokens(PAD_STR * k)
            expected = base_count * k
            assert repeated_count == expected, f"k={k}: got {repeated_count}, expected {expected}"

    def test_pad_boundary_stability(self):
        """PAD doesn't cause boundary token merging."""
        tokenizer = get_tokenizer()

        prefixes = [
            "action",
            "action.",
            '{"key": "value"}',
            "End of precedent.\n\n",
        ]

        for prefix in prefixes:
            prefix_tokens = tokenizer.encode(prefix)
            combined_tokens = tokenizer.encode(prefix + PAD_STR)

            assert combined_tokens[:len(prefix_tokens)] == prefix_tokens, \
                f"Boundary merge detected for prefix: {repr(prefix)}"

    def test_tokenizer_config(self):
        """Tokenizer config captures all required fields."""
        tokenizer = get_tokenizer()
        tokenizer.validate_pad_stability(PAD_STR)
        config = tokenizer.get_config()

        assert isinstance(config, TokenizerConfig)
        assert config.provider == "anthropic"
        assert config.tokenizer_id == "cl100k_base"
        assert config.pad_str == PAD_STR
        assert config.pad_token_count == 1


class TestPadSelfTest:
    """Tests for PAD self-test function."""

    def test_self_test_passes(self):
        """run_pad_self_test returns success for valid PAD."""
        passed, msg = run_pad_self_test()
        assert passed, f"Self-test should pass: {msg}"
        assert "passed" in msg.lower()


# ============================================================================
# Gate P4 Tests
# ============================================================================

class TestGateP4:
    """Tests for Gate P4 enforcement."""

    def test_gate_initialization(self):
        """Gate P4 initializes with valid config."""
        config = GateP4Config(buffer_size_n=512)
        gate = GateP4(config)

        assert gate.config.buffer_size_n == 512
        assert gate._pad_token_count == 1

    def test_precedent_buffer_preparation(self):
        """Precedent buffer is correctly padded."""
        config = GateP4Config(buffer_size_n=512)
        gate = GateP4(config)

        precedent = serialize_precedent_record(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_PREFER_COOPERATION"},
            conflict_attribution={("B_COOPERATION_MATTERS", "P_NO_DEFECT")},
            artifact_digest="test123",
            step_index=5,
        )

        injection, violation = gate.prepare_precedent_buffer(precedent)

        assert violation is None
        assert injection is not None
        assert injection.total_tokens == 512
        assert injection.precedent_tokens > 0
        assert injection.padding_tokens > 0
        assert injection.precedent_tokens + injection.padding_tokens == injection.total_tokens

    def test_buffer_overflow_detection(self):
        """Buffer overflow is detected when precedent exceeds N."""
        config = GateP4Config(buffer_size_n=32)  # Very small buffer
        gate = GateP4(config)

        # Create large precedent
        large_precedent = serialize_precedent_record(
            authorized_violations=set(f"P_{i}" for i in range(20)),
            required_preservations=set(f"R_{i}" for i in range(20)),
            conflict_attribution=set(),
            artifact_digest="x" * 100,
            step_index=0,
        )

        injection, violation = gate.prepare_precedent_buffer(large_precedent)

        assert violation == GateP4Violation.BUFFER_OVERFLOW
        assert injection is None

    def test_token_jitter_detection(self):
        """Token jitter is detected when prompt size changes."""
        config = GateP4Config(buffer_size_n=512, tolerance=0)
        gate = GateP4(config)

        # First prompt establishes baseline
        prompt1 = "Test prompt with some content" + PAD_STR * 100
        passed1, violation1, jitter1 = gate.check_jitter(prompt1, 0, "ep1")
        assert passed1
        assert jitter1 == 0

        # Same size prompt should pass
        prompt2 = "Another prompt with content" + PAD_STR * 100
        tokens2 = gate.tokenizer.count_tokens(prompt2)
        tokens1 = gate.tokenizer.count_tokens(prompt1)

        if tokens2 == tokens1:
            passed2, violation2, jitter2 = gate.check_jitter(prompt2, 1, "ep1")
            assert passed2
        else:
            passed2, violation2, jitter2 = gate.check_jitter(prompt2, 1, "ep1")
            assert not passed2
            assert violation2 == GateP4Violation.SHADOW_PERSISTENCE

    def test_empty_precedent_buffer(self):
        """Empty precedent buffer is all PAD."""
        config = GateP4Config(buffer_size_n=512)
        tokenizer = get_tokenizer()

        buffer = create_empty_precedent_buffer(config, tokenizer)
        token_count = tokenizer.count_tokens(buffer)

        assert token_count == 512
        assert PAD_STR in buffer


class TestCalibration:
    """Tests for buffer size calibration."""

    def test_ceil_to_32(self):
        """ceil_to_32 rounds up correctly."""
        assert ceil_to_32(1) == 32
        assert ceil_to_32(32) == 32
        assert ceil_to_32(33) == 64
        assert ceil_to_32(100) == 128
        assert ceil_to_32(512) == 512

    def test_calibrate_buffer_size(self):
        """Calibration produces correct buffer size."""
        observations = [45, 52, 48, 61, 55]
        N = GateP4.calibrate_buffer_size(observations, floor=512)

        # max = 61, 1.25 * 61 = 76.25, ceil_to_32 = 96, max(512, 96) = 512
        assert N == 512

    def test_calibrate_buffer_size_large(self):
        """Calibration handles large observations."""
        observations = [400, 450, 480, 500, 520]
        N = GateP4.calibrate_buffer_size(observations, floor=512)

        # max = 520, 1.25 * 520 = 650, ceil_to_32 = 672, max(512, 672) = 672
        assert N == 672


class TestPrecedentSerialization:
    """Tests for precedent serialization."""

    def test_serialization_canonical(self):
        """Serialization produces canonical JSON."""
        result1 = serialize_precedent_record(
            authorized_violations={"B", "A"},
            required_preservations={"Y", "X"},
            conflict_attribution={("B", "P"), ("A", "Q")},
            artifact_digest="abc",
            step_index=5,
        )

        result2 = serialize_precedent_record(
            authorized_violations={"A", "B"},  # Different order
            required_preservations={"X", "Y"},
            conflict_attribution={("A", "Q"), ("B", "P")},
            artifact_digest="abc",
            step_index=5,
        )

        assert result1 == result2, "Canonical serialization should be order-independent"

    def test_serialization_valid_json(self):
        """Serialization produces valid JSON."""
        result = serialize_precedent_record(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_PREFER_COOPERATION"},
            conflict_attribution={("B_COOPERATION_MATTERS", "P_NO_DEFECT")},
            artifact_digest="test123",
            step_index=5,
        )

        parsed = json.loads(result)
        assert "AV" in parsed
        assert "RP" in parsed
        assert "CA" in parsed
        assert "digest" in parsed
        assert "step" in parsed


# ============================================================================
# Novelty Detection Tests
# ============================================================================

class TestNoveltyDetector:
    """Tests for novelty detection."""

    def test_first_conflict_is_novel(self):
        """First conflict in episode is always novel."""
        detector = NoveltyDetector()
        detector.start_episode("ep1")

        sig = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)

        assert sig.is_novel
        assert sig.episode_id == "ep1"
        assert sig.step == 0

    def test_same_conflict_not_novel(self):
        """Same conflict signature is not novel."""
        detector = NoveltyDetector()
        detector.start_episode("ep1")

        sig1 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)
        sig2 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 1)

        assert sig1.is_novel
        assert not sig2.is_novel
        assert sig1.signature_hash == sig2.signature_hash

    def test_different_constraint_is_novel(self):
        """Different constraint IDs make conflict novel."""
        detector = NoveltyDetector()
        detector.start_episode("ep1")

        sig1 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)
        sig2 = detector.check_novelty(["P_NO_LIE"], {"trust": 0.5}, 1)

        assert sig1.is_novel
        assert sig2.is_novel
        assert sig1.signature_hash != sig2.signature_hash

    def test_different_resource_is_novel(self):
        """Different resource vector makes conflict novel."""
        detector = NoveltyDetector()
        detector.start_episode("ep1")

        sig1 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)
        sig2 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.8}, 1)

        assert sig1.is_novel
        assert sig2.is_novel
        assert sig1.signature_hash != sig2.signature_hash

    def test_episode_reset_clears_history(self):
        """Starting new episode clears signature history."""
        detector = NoveltyDetector()

        detector.start_episode("ep1")
        sig1 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)

        detector.start_episode("ep2")  # Reset
        sig2 = detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)

        assert sig1.is_novel
        assert sig2.is_novel  # Same conflict, but new episode


# ============================================================================
# Normative State Manager Tests
# ============================================================================

class TestNormativeStateManager:
    """Tests for normative state manager."""

    def test_baseline_allows_writes(self):
        """Baseline mode allows precedent writes."""
        manager = NormativeStateManager(V310AblationSpec.NONE)

        result = manager.record_precedent(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_PREFER_COOPERATION"},
            conflict_attribution={("B_COOPERATION_MATTERS", "P_NO_DEFECT")},
            digest="test",
            step=0,
        )

        assert result is True
        assert manager.get_write_stats()["writes"] == 1
        assert manager.get_write_stats()["blocked"] == 0

    def test_run_b_blocks_writes(self):
        """Run B mode blocks all writes."""
        manager = NormativeStateManager(V310AblationSpec.REFLECTION_EXCISION)

        result = manager.record_precedent(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_PREFER_COOPERATION"},
            conflict_attribution=set(),
            digest="test",
            step=0,
        )

        assert result is False
        assert manager.get_write_stats()["writes"] == 0
        assert manager.get_write_stats()["blocked"] == 1

    def test_run_c_resets_at_episode_boundary(self):
        """Run C mode resets state at episode boundaries."""
        manager = NormativeStateManager(V310AblationSpec.PERSISTENCE_EXCISION)

        # Write something
        manager.record_precedent(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_PREFER_COOPERATION"},
            conflict_attribution=set(),
            digest="test",
            step=0,
        )

        hash_before_reset = manager.compute_hash()

        # Reset for new episode
        manager.reset_for_episode()

        hash_after_reset = manager.compute_hash()

        # State should be cleared (back to empty hash)
        assert hash_after_reset != hash_before_reset

    def test_baseline_no_episode_reset(self):
        """Baseline mode doesn't reset at episode boundaries."""
        manager = NormativeStateManager(V310AblationSpec.NONE)

        # Write something
        manager.record_precedent(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_PREFER_COOPERATION"},
            conflict_attribution=set(),
            digest="test",
            step=0,
        )

        hash_before = manager.compute_hash()

        # Episode boundary (should be no-op for baseline)
        manager.reset_for_episode()

        hash_after = manager.compute_hash()

        # State should be unchanged
        assert hash_after == hash_before


# ============================================================================
# V310 Harness Integration Tests
# ============================================================================

class TestV310Harness:
    """Integration tests for V310AblationHarness."""

    def test_harness_initialization(self):
        """Harness initializes with valid config."""
        config = V310RunConfig(
            ablation=V310AblationSpec.NONE,
            buffer_size_n=512,
            seeds=(42, 123, 456, 789, 1024),
            num_episodes=1,
            steps_per_episode=5,
        )

        harness = V310AblationHarness(config)

        assert harness.config == config
        assert harness.tokenizer is not None
        assert harness.gate_p4 is not None
        assert harness.novelty_detector is not None
        assert harness.normative_manager is not None

    def test_config_validation_seeds(self):
        """Config validation catches insufficient seeds."""
        config = V310RunConfig(
            ablation=V310AblationSpec.NONE,
            seeds=(42,),  # Only 1 seed
        )

        errors = config.validate()
        assert len(errors) > 0
        assert "5 seeds" in errors[0]

    def test_config_validation_episode_length(self):
        """Config validation catches short episodes."""
        config = V310RunConfig(
            ablation=V310AblationSpec.NONE,
            seeds=(42, 123, 456, 789, 1024),
            steps_per_episode=2,  # Less than 3
        )

        errors = config.validate()
        assert len(errors) > 0
        assert ">= 3" in errors[0]

    def test_precedent_injection_empty(self):
        """Precedent injection works with empty precedent."""
        config = V310RunConfig(
            ablation=V310AblationSpec.NONE,
            seeds=(42, 123, 456, 789, 1024),
        )

        harness = V310AblationHarness(config)
        buffer, telemetry, violation = harness.prepare_precedent_injection(0, "test_ep")

        assert violation is None
        assert telemetry is not None
        assert telemetry.precedent_tokens == 0
        assert telemetry.total_tokens == 512

    def test_run_header(self):
        """Run header contains required fields."""
        config = V310RunConfig(
            ablation=V310AblationSpec.NONE,
            seeds=(42, 123, 456, 789, 1024),
        )

        harness = V310AblationHarness(config)
        header = harness.get_run_header()

        assert header["version"] == "v3.1"
        assert header["ablation"] == "none"
        assert header["buffer_size_n"] == 512
        assert "tokenizer" in header
        assert header["tokenizer"]["provider"] == "anthropic"


# ============================================================================
# Run if executed directly
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
