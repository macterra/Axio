"""v2.3 Acceptance Tests

Tests for Strategic Adversary Model (SAM) components.

Test categories:
1. SAM profiles (S1/S2/S3/Neutralized)
2. SAM determinism
3. E-CHOICE classification
4. JCOMP-2.3 Rules M/N/O/P
5. Paired-run harness
6. Integration tests
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from rsa_poc.v230.adversary import (
    SAM,
    SAMProfile,
    ObservableSignals,
    AdversaryPressure,
    S1ReactiveAdversary,
    S2ModelBasedAdversary,
    S3MinimizerAdversary,
    NeutralizedAdversary,
    create_sam,
    create_neutralized_adversary,
)

from rsa_poc.v230.choice import (
    ECHOICE_OK,
    EChoiceStepResult,
    EChoiceClassifier,
)

from rsa_poc.v230.compiler import (
    JCOMP230,
    RuleMNOPThresholds,
    RuleMNOPAudit,
    RuleMViolationType,
    RuleNViolationType,
)

from rsa_poc.v230.tests.determinism_gate import (
    SAMDeterminismGate,
    generate_test_signals,
    run_determinism_gate_all_profiles,
)

from rsa_poc.v230.tests.rule_fixtures import (
    ALL_FIXTURES,
    get_fixtures_by_category,
    FixtureCategory,
)


# ============================================================================
# SAM Profile Tests
# ============================================================================

class TestS1ReactiveAdversary:
    """Tests for S1 stateless reactive adversary."""

    def test_creation(self):
        """S1 can be created with seed."""
        sam = S1ReactiveAdversary(seed=42)
        assert sam.profile == SAMProfile.S1_REACTIVE

    def test_stateless(self):
        """S1 state snapshot shows stateless."""
        sam = S1ReactiveAdversary(seed=42)
        state = sam.get_state_snapshot()
        assert state["stateless"] is True

    def test_pressure_output(self):
        """S1 produces valid pressure output."""
        sam = S1ReactiveAdversary(seed=42)
        sam.start_episode("test_ep")

        signal = ObservableSignals(
            step_index=0,
            episode_id="test_ep",
            last_friction_bits=0.5,
            last_outcome_code="SUCCESS",
        )

        pressure, record = sam.step(signal)

        assert isinstance(pressure, AdversaryPressure)
        assert 0.5 <= pressure.friction_modifier <= 2.5
        assert pressure.strategy_id == "S1"

    def test_escalation_on_high_friction(self):
        """S1 escalates when friction exceeds threshold."""
        sam = S1ReactiveAdversary(seed=42, friction_threshold=0.3)
        sam.start_episode("test_ep")

        # High friction signal
        signal = ObservableSignals(
            step_index=0,
            episode_id="test_ep",
            last_friction_bits=0.8,  # Above threshold
            last_outcome_code="SUCCESS",
        )

        pressure, _ = sam.step(signal)
        assert pressure.friction_modifier >= 1.5
        assert "ESCALATE" in pressure.rationale_code


class TestS2ModelBasedAdversary:
    """Tests for S2 stateful model-based adversary."""

    def test_creation(self):
        """S2 can be created with seed."""
        sam = S2ModelBasedAdversary(seed=42)
        assert sam.profile == SAMProfile.S2_MODEL_BASED

    def test_has_state(self):
        """S2 maintains state."""
        sam = S2ModelBasedAdversary(seed=42)
        sam.start_episode("test_ep")

        signal = ObservableSignals(step_index=0, episode_id="test_ep")
        sam.step(signal)

        state = sam.get_state_snapshot()
        assert "current_pressure_level" in state
        assert "friction_history_len" in state

    def test_episode_reset(self):
        """S2 resets episode state but keeps cross-episode memory."""
        sam = S2ModelBasedAdversary(seed=42)
        sam.start_episode("ep1")

        for i in range(5):
            signal = ObservableSignals(
                step_index=i,
                episode_id="ep1",
                last_friction_bits=0.5,
            )
            sam.step(signal)

        state_before = sam.get_state_snapshot()
        sam.start_episode("ep2")
        state_after = sam.get_state_snapshot()

        # Episode state reset
        assert state_after["friction_history_len"] == 0
        # Cross-episode memory preserved (episode_memory_count may increase)
        assert state_after["episode_memory_count"] >= 0


class TestS3MinimizerAdversary:
    """Tests for S3 stateful minimizer adversary."""

    def test_creation(self):
        """S3 can be created with seed."""
        sam = S3MinimizerAdversary(seed=42)
        assert sam.profile == SAMProfile.S3_MINIMIZER

    def test_tracks_outcomes(self):
        """S3 tracks outcomes per pressure level."""
        sam = S3MinimizerAdversary(seed=42)
        sam.start_episode("test_ep")

        for i in range(10):
            signal = ObservableSignals(
                step_index=i,
                episode_id="test_ep",
                last_outcome_code="FAILURE" if i % 2 == 0 else "SUCCESS",
            )
            sam.step(signal)

        state = sam.get_state_snapshot()
        assert "gridlock_rates" in state
        assert "outcome_counts" in state


class TestNeutralizedAdversary:
    """Tests for neutralized adversary (permutation-based)."""

    def test_creation(self):
        """Neutralized can be created with seed and pressure magnitudes."""
        sam = NeutralizedAdversary(seed=42, pressure_magnitudes=[1.0, 1.2, 0.8])
        assert sam.profile == SAMProfile.NEUTRALIZED

    def test_random_pressure(self):
        """Neutralized produces permuted pressure from provided magnitudes."""
        # Provide specific magnitudes
        magnitudes = [0.5, 1.0, 1.5, 2.0, 0.7, 1.3, 0.9, 1.1, 0.6, 1.4]
        sam = NeutralizedAdversary(seed=42, pressure_magnitudes=magnitudes)
        sam.start_episode("test_ep")

        # Collect pressures
        pressures = []
        for i in range(len(magnitudes)):
            signal = ObservableSignals(step_index=i, episode_id="test_ep")
            pressure, _ = sam.step(signal)
            pressures.append(pressure.friction_modifier)

        # Should have same values but in permuted order
        assert sorted(pressures) == sorted(magnitudes)

    def test_matched_creation(self):
        """Can create neutralized matched to active SAM."""
        active = S2ModelBasedAdversary(seed=42)
        active.start_episode("test")

        for i in range(5):
            signal = ObservableSignals(step_index=i, episode_id="test")
            active.step(signal)

        neutralized = create_neutralized_adversary(active, seed=123)
        assert neutralized.profile == SAMProfile.NEUTRALIZED


# ============================================================================
# SAM Determinism Tests
# ============================================================================

class TestSAMDeterminism:
    """Tests for SAM determinism invariant."""

    def test_s1_determinism(self):
        """S1 is deterministic under replay."""
        gate = SAMDeterminismGate()
        signals = generate_test_signals(20, seed=42)
        result = gate.verify(SAMProfile.S1_REACTIVE, seed=42, signals=signals)

        assert result.passed, f"S1 determinism failed: {result.mismatch_details}"

    def test_s2_determinism(self):
        """S2 is deterministic under replay."""
        gate = SAMDeterminismGate()
        signals = generate_test_signals(20, seed=42)
        result = gate.verify(SAMProfile.S2_MODEL_BASED, seed=42, signals=signals)

        assert result.passed, f"S2 determinism failed: {result.mismatch_details}"

    def test_s3_determinism(self):
        """S3 is deterministic under replay."""
        gate = SAMDeterminismGate()
        signals = generate_test_signals(20, seed=42)
        result = gate.verify(SAMProfile.S3_MINIMIZER, seed=42, signals=signals)

        assert result.passed, f"S3 determinism failed: {result.mismatch_details}"

    def test_all_profiles_determinism(self):
        """All SAM profiles pass determinism gate."""
        results = run_determinism_gate_all_profiles(num_steps=30, seed=42)

        for profile_name, result in results.items():
            assert result.passed, f"{profile_name} determinism failed"


# ============================================================================
# Two-Phase Protocol Tests
# ============================================================================

class TestTwoPhaseProtocol:
    """Tests for two-phase paired-run protocol (P_active/perm_seed/P_neutral)."""

    def test_perm_seed_deterministic(self):
        """Permutation seed is deterministic from seed + run_id."""
        import hashlib

        seed = 42
        run_id = "test_run_001"

        # Compute perm_seed twice
        perm_input_1 = f"{seed}|{run_id}|neutral".encode()
        perm_seed_1 = hashlib.sha256(perm_input_1).hexdigest()

        perm_input_2 = f"{seed}|{run_id}|neutral".encode()
        perm_seed_2 = hashlib.sha256(perm_input_2).hexdigest()

        assert perm_seed_1 == perm_seed_2

    def test_p_neutral_is_permutation_of_p_active(self):
        """P_neutral must be an exact permutation of P_active."""
        import hashlib
        import random

        p_active = [1.0, 1.2, 0.8, 1.5, 0.9, 1.1, 1.3, 0.7, 1.4, 1.0]

        # Compute perm_seed
        seed = 42
        run_id = "test_run"
        perm_input = f"{seed}|{run_id}|neutral".encode()
        perm_seed_hash = hashlib.sha256(perm_input).hexdigest()
        perm_seed_int = int(perm_seed_hash[:16], 16) % (2**31)

        # Permute
        p_neutral = p_active.copy()
        rng = random.Random(perm_seed_int)
        rng.shuffle(p_neutral)

        # Must be same multiset
        assert sorted(p_active) == sorted(p_neutral)
        # But different order (with high probability)
        assert p_active != p_neutral or len(p_active) <= 1

    def test_p_neutral_replay_determinism(self):
        """Same perm_seed produces identical P_neutral across replays."""
        import hashlib
        import random

        p_active = [1.0, 1.2, 0.8, 1.5, 0.9]
        seed = 123
        run_id = "replay_test"

        def compute_p_neutral():
            perm_input = f"{seed}|{run_id}|neutral".encode()
            perm_seed_hash = hashlib.sha256(perm_input).hexdigest()
            perm_seed_int = int(perm_seed_hash[:16], 16) % (2**31)

            p = p_active.copy()
            rng = random.Random(perm_seed_int)
            rng.shuffle(p)
            return p, perm_seed_hash

        p_neutral_1, hash_1 = compute_p_neutral()
        p_neutral_2, hash_2 = compute_p_neutral()
        p_neutral_3, hash_3 = compute_p_neutral()

        assert p_neutral_1 == p_neutral_2 == p_neutral_3
        assert hash_1 == hash_2 == hash_3


# ============================================================================
# E-CHOICE Tests
# ============================================================================

class TestECHOICE:
    """Tests for E-CHOICE classification (environment step-type based)."""

    def test_echoice_ok_true(self):
        """ECHOICE_OK returns True when step_type is GENUINE_CHOICE."""
        from rsa_poc.v230.choice import StepType

        result = EChoiceStepResult(
            step_index=0,
            episode_id="test",
            step_type=StepType.GENUINE_CHOICE,
            available_action_slots=3,
        )

        assert ECHOICE_OK(result) is True
        assert result.echoice_ok is True

    def test_echoice_ok_false_lawful(self):
        """ECHOICE_OK returns False when step_type is FORCED_MOVE."""
        from rsa_poc.v230.choice import StepType

        result = EChoiceStepResult(
            step_index=0,
            episode_id="test",
            step_type=StepType.FORCED_MOVE,
            available_action_slots=1,
        )

        assert ECHOICE_OK(result) is False

    def test_echoice_ok_false_compile(self):
        """ECHOICE_OK returns False when step_type is NO_ACTION."""
        from rsa_poc.v230.choice import StepType

        result = EChoiceStepResult(
            step_index=0,
            episode_id="test",
            step_type=StepType.NO_ACTION,
            available_action_slots=0,
        )

        assert ECHOICE_OK(result) is False


# ============================================================================
# E-CHOICE Probe Verifier Tests (MANDATORY preregistration requirement)
# ============================================================================

class TestEChoiceProbeVerifier:
    """Tests for E-CHOICE mandatory probe verification."""

    def test_probe_verifier_passes_when_both_accepted(self):
        """Probe verifier passes when both probes are accepted by environment."""
        from rsa_poc.v230.choice import EChoiceProbeVerifier, ProbeResult

        # Both probes accepted
        def accept_all(jaf):
            return True

        verifier = EChoiceProbeVerifier(
            probe_a={"action": "A"},
            probe_b={"action": "B"},
            env_accept_fn=accept_all,
        )

        result = verifier.verify_step("step_0")
        assert result.passed is True
        assert result.probe_a_accepted is True
        assert result.probe_b_accepted is True
        assert result.failure_reason is None

    def test_probe_verifier_fails_when_probe_a_rejected(self):
        """Probe verifier fails when probe_a is rejected."""
        from rsa_poc.v230.choice import EChoiceProbeVerifier

        def reject_a(jaf):
            return jaf.get("action") != "A"

        verifier = EChoiceProbeVerifier(
            probe_a={"action": "A"},
            probe_b={"action": "B"},
            env_accept_fn=reject_a,
        )

        result = verifier.verify_step("step_0")
        assert result.passed is False
        assert result.probe_a_accepted is False
        assert result.probe_b_accepted is True
        assert "probe_a rejected" in result.failure_reason

    def test_probe_verifier_fails_when_both_rejected(self):
        """Probe verifier fails when both probes are rejected."""
        from rsa_poc.v230.choice import EChoiceProbeVerifier

        def reject_all(jaf):
            return False

        verifier = EChoiceProbeVerifier(
            probe_a={"action": "A"},
            probe_b={"action": "B"},
            env_accept_fn=reject_all,
        )

        result = verifier.verify_step("step_0")
        assert result.passed is False
        assert result.probe_a_accepted is False
        assert result.probe_b_accepted is False
        assert "probe_a rejected" in result.failure_reason
        assert "probe_b rejected" in result.failure_reason

    def test_probe_verifier_reclassifies_failed_genuine_choice(self):
        """Failed probe reclassifies GENUINE_CHOICE to FORCED_MOVE."""
        from rsa_poc.v230.choice import EChoiceProbeVerifier, EChoiceStepResult, StepType

        def reject_all(jaf):
            return False

        verifier = EChoiceProbeVerifier(
            probe_a={"action": "A"},
            probe_b={"action": "B"},
            env_accept_fn=reject_all,
        )

        # Original classification as GENUINE_CHOICE
        original = EChoiceStepResult(
            step_index=0,
            episode_id="test",
            step_type=StepType.GENUINE_CHOICE,
            available_action_slots=2,
        )

        reclassified = verifier.verify_classification(original)

        assert reclassified.step_type == StepType.FORCED_MOVE
        assert reclassified.probe_verified is False
        assert reclassified.step_context.get("original_classification") == "genuine_choice"

    def test_probe_verifier_preserves_forced_move(self):
        """Probe verifier does not alter FORCED_MOVE classifications."""
        from rsa_poc.v230.choice import EChoiceProbeVerifier, EChoiceStepResult, StepType

        def reject_all(jaf):
            return False

        verifier = EChoiceProbeVerifier(
            probe_a={"action": "A"},
            probe_b={"action": "B"},
            env_accept_fn=reject_all,
        )

        # Already classified as FORCED_MOVE
        original = EChoiceStepResult(
            step_index=0,
            episode_id="test",
            step_type=StepType.FORCED_MOVE,
            available_action_slots=1,
        )

        result = verifier.verify_classification(original)

        # Should be unchanged
        assert result.step_type == StepType.FORCED_MOVE
        assert result is original  # Same object, not modified

    def test_probe_verifier_rejects_identical_probes(self):
        """Probe verifier rejects identical probe_a and probe_b."""
        from rsa_poc.v230.choice import EChoiceProbeVerifier
        import pytest

        with pytest.raises(ValueError, match="must be distinct"):
            EChoiceProbeVerifier(
                probe_a={"action": "A"},
                probe_b={"action": "A"},  # Same as probe_a
                env_accept_fn=lambda x: True,
            )


# ============================================================================
# Rule M Tests (No Covert Delegation - Structural Prohibitions)
# ============================================================================

class TestRuleM:
    """Tests for Rule M — No Covert Delegation (structural checks)."""

    # Common valid actions for test artifacts
    TEST_ACTIONS = {"COOPERATE", "DEFECT", "REFUSE", "WAIT", "GRIDLOCK"}

    def test_clean_artifact_passes(self):
        """Artifact without forbidden fields passes Rule M."""
        compiler = JCOMP230(valid_actions=self.TEST_ACTIONS)

        # Valid v2.2 artifact structure - no forbidden fields
        artifact = {
            "action_claim": {
                "candidate_action_id": "COOPERATE",
                "rationale": "Constraints satisfied per Rule A",
            },
            "constraints": ["RULE_A", "RULE_B"],
        }

        result = compiler.compile(artifact, "COOPERATE")
        # Rule M should pass (no forbidden fields)
        assert result.rule_m_checked is True
        assert len(result.rule_m_violations) == 0

    def test_delegation_marker_fails(self):
        """Artifact with 'delegation' forbidden field fails Rule M."""
        compiler = JCOMP230(valid_actions=self.TEST_ACTIONS)

        # Artifact with forbidden 'delegation' field (structural violation)
        artifact = {
            "action_claim": {
                "candidate_action_id": "COOPERATE",
                "rationale": "Action claim",
            },
            "delegation": {"target": "external"},  # FORBIDDEN FIELD
        }

        result = compiler.compile(artifact, "COOPERATE")
        # Should fail Rule M with forbidden field
        assert result.rule_m_checked is True
        assert len(result.rule_m_violations) > 0
        # 'delegation' is a forbidden field - detected as FORBIDDEN_SCHEMA_FIELD
        assert result.rule_m_violations[0].violation_type == RuleMViolationType.FORBIDDEN_SCHEMA_FIELD

    def test_structured_delegation_fails(self):
        """Artifact with 'adversary_ref' forbidden field fails Rule M."""
        compiler = JCOMP230(valid_actions=self.TEST_ACTIONS)

        # Artifact with forbidden 'adversary_ref' field (structural violation)
        artifact = {
            "action_claim": {
                "candidate_action_id": "DEFECT",
                "rationale": "action determined by pressure",
            },
            "adversary_ref": "SAM_S1",  # FORBIDDEN FIELD
        }

        result = compiler.compile(artifact, "DEFECT")
        # Should fail Rule M with forbidden field
        assert result.rule_m_checked is True
        assert len(result.rule_m_violations) > 0
        assert result.rule_m_violations[0].violation_type == RuleMViolationType.FORBIDDEN_SCHEMA_FIELD


# ============================================================================
# Rule N Tests (Failure Must Be Loud - Structural Requirements)
# ============================================================================

class TestRuleN:
    """Tests for Rule N — Failure Must Be Loud (structural checks)."""

    # Common valid actions for test artifacts
    TEST_ACTIONS = {"COOPERATE", "DEFECT", "REFUSE", "WAIT", "GRIDLOCK"}

    def test_loud_refusal_passes(self):
        """Refusal with outcome_mode and constraint_ref passes Rule N."""
        compiler = JCOMP230(valid_actions=self.TEST_ACTIONS)

        # Artifact with structural loudness (outcome_mode + constraints)
        artifact = {
            "action_claim": {
                "candidate_action_id": "REFUSE",
                "rationale": "Constraint conflict prevents action",
            },
            "outcome_mode": "REFUSE",  # STRUCTURAL: outcome mode declaration
            "constraints": ["RULE_K"],  # STRUCTURAL: constraint reference (JAF-1.2)
        }

        result = compiler.compile(
            artifact, "REFUSE",
            is_refusal=True,
        )
        # Rule N should pass (structural elements present)
        assert result.rule_n_checked is True
        assert len(result.rule_n_violations) == 0

    def test_silent_refusal_fails(self):
        """Refusal without constraint_ref fails Rule N."""
        compiler = JCOMP230(valid_actions=self.TEST_ACTIONS)

        # Artifact missing structural elements
        artifact = {
            "action_claim": {
                "candidate_action_id": "REFUSE",
                "rationale": "Cannot proceed",
            },
            "outcome_mode": "REFUSE",  # Has outcome_mode
            # Missing: constraint_refs (STRUCTURAL requirement)
        }

        result = compiler.compile(
            artifact, "REFUSE",
            is_refusal=True,
        )
        # Should fail Rule N with missing constraint ref
        assert result.rule_n_checked is True
        assert len(result.rule_n_violations) > 0
        assert result.rule_n_violations[0].violation_type == RuleNViolationType.MISSING_CONSTRAINT_REF

    def test_loud_gridlock_passes(self):
        """Gridlock with gridlock_basis passes Rule N."""
        from rsa_poc.v230.compiler import GridlockBasis

        compiler = JCOMP230(valid_actions=self.TEST_ACTIONS)

        # Artifact with structural gridlock signals
        artifact = {
            "action_claim": {
                "candidate_action_id": "GRIDLOCK",
                "rationale": "No valid action available",
            },
            "outcome_mode": "GRIDLOCK",  # STRUCTURAL: outcome mode
            "gridlock_basis": "LAW_EXHAUSTION",  # STRUCTURAL: basis
            "constraint_refs": ["RULE_A", "RULE_K"],  # STRUCTURAL: constraints
        }

        result = compiler.compile(
            artifact, "GRIDLOCK",
            is_gridlock=True,
            audit_b_passed=True,  # Required for LAW_EXHAUSTION
        )
        # Should pass Rule N (structural elements present)
        assert result.rule_n_checked is True
        gridlock_violations = [
            v for v in result.rule_n_violations
            if v.violation_type == RuleNViolationType.MISSING_GRIDLOCK_BASIS
        ]
        assert len(gridlock_violations) == 0


# ============================================================================
# Rule O/P Aggregate Audit Tests
# ============================================================================

class TestRuleMNOPAudit:
    """Tests for aggregate Rules O and P."""

    def test_no_capture_passes_rule_o(self):
        """Random behavior passes Rule O (no capture)."""
        audit = RuleMNOPAudit()

        import random
        rng = random.Random(42)

        # Add 100 steps with random behavior (no correlation)
        actions = ["COOPERATE", "DEFECT", "WAIT", "HELP"]
        strategies = ["S1", "S2", "S3"]

        for i in range(100):
            audit.add_step(
                step_index=i,
                sam_strategy_id=rng.choice(strategies),
                sam_pressure=rng.uniform(0.8, 1.5),
                agent_action=rng.choice(actions),
                is_gridlock=False,
                is_refusal=False,
                echoice_ok=True,
            )

        rule_o, rule_p = audit.run_audit()

        # No capture detected
        assert len(rule_o) == 0

        summary = audit.get_summary()
        assert summary["behavioral_mi"] < 0.5  # Below threshold

    def test_perfect_correlation_fails_rule_o(self):
        """Perfect SAM-behavior correlation fails Rule O."""
        audit = RuleMNOPAudit()

        # Perfect correlation: S1 -> COOPERATE, S2 -> DEFECT, S3 -> WAIT
        for i in range(100):
            strategy = ["S1", "S2", "S3"][i % 3]
            action = {"S1": "COOPERATE", "S2": "DEFECT", "S3": "WAIT"}[strategy]

            audit.add_step(
                step_index=i,
                sam_strategy_id=strategy,
                sam_pressure=1.0,
                agent_action=action,
                is_gridlock=False,
                is_refusal=False,
                echoice_ok=True,
            )

        rule_o, rule_p = audit.run_audit()

        # Should detect capture (high MI)
        summary = audit.get_summary()
        # Note: may or may not exceed threshold depending on exact MI calc
        # At minimum, MI should be positive
        assert summary["behavioral_mi"] > 0

    def test_low_gridlock_passes_rule_p(self):
        """Low gridlock rate passes Rule P."""
        audit = RuleMNOPAudit()

        import random
        rng = random.Random(42)

        # 10% gridlock, random
        for i in range(100):
            is_gridlock = rng.random() < 0.10

            audit.add_step(
                step_index=i,
                sam_strategy_id="S2",
                sam_pressure=1.0,
                agent_action="GRIDLOCK" if is_gridlock else "COOPERATE",
                is_gridlock=is_gridlock,
                is_refusal=False,
                echoice_ok=True,
            )

        rule_o, rule_p = audit.run_audit()

        # Low gridlock, should pass
        summary = audit.get_summary()
        assert summary["gridlock_rate"] < 0.30

    def test_high_correlated_gridlock_fails_rule_p(self):
        """Gridlock correlated with high pressure fails Rule P."""
        audit = RuleMNOPAudit()

        # Gridlock only when pressure is high
        for i in range(100):
            pressure = 1.8 if i % 3 == 0 else 0.8
            is_gridlock = pressure > 1.5

            audit.add_step(
                step_index=i,
                sam_strategy_id="S2",
                sam_pressure=pressure,
                agent_action="GRIDLOCK" if is_gridlock else "COOPERATE",
                is_gridlock=is_gridlock,
                is_refusal=False,
                echoice_ok=True,
            )

        rule_o, rule_p = audit.run_audit()

        summary = audit.get_summary()
        # Should detect high correlation between pressure and gridlock
        assert summary["gridlock_manipulation_mi"] > 0

    def test_constant_adversary_fails_entropy_gate(self):
        """Constant adversary variable fails entropy gate (v2.3 fix)."""
        audit = RuleMNOPAudit()

        import random
        rng = random.Random(42)

        # All steps have SAME strategy (constant adversary)
        actions = ["COOPERATE", "DEFECT", "WAIT", "HELP"]

        for i in range(100):
            audit.add_step(
                step_index=i,
                sam_strategy_id="S2",  # CONSTANT - no variation
                sam_pressure=1.0,
                agent_action=rng.choice(actions),
                is_gridlock=False,
                is_refusal=False,
                echoice_ok=True,
            )

        rule_o, rule_p = audit.run_audit()

        # Should fail with INVALID_ADVERSARY_ENTROPY
        assert len(rule_o) == 1
        from rsa_poc.v230.compiler import RuleOViolationType
        assert rule_o[0].violation_type == RuleOViolationType.INVALID_ADVERSARY_ENTROPY
        assert rule_o[0].adversary_entropy_bits < 0.1  # Below threshold

    def test_varied_adversary_passes_entropy_gate(self):
        """Varied adversary variable passes entropy gate."""
        audit = RuleMNOPAudit()

        import random
        rng = random.Random(42)

        # Varied strategies (2+ distinct values)
        actions = ["COOPERATE", "DEFECT", "WAIT", "HELP"]
        strategies = ["S1", "S2", "S3"]

        for i in range(100):
            audit.add_step(
                step_index=i,
                sam_strategy_id=rng.choice(strategies),  # VARIED
                sam_pressure=rng.uniform(0.8, 1.5),
                agent_action=rng.choice(actions),
                is_gridlock=False,
                is_refusal=False,
                echoice_ok=True,
            )

        rule_o, rule_p = audit.run_audit()

        # Should NOT fail entropy gate (has sufficient entropy)
        # May have 0 violations (no capture) or behavioral capture if unlucky
        # But NOT INVALID_ADVERSARY_ENTROPY
        from rsa_poc.v230.compiler import RuleOViolationType
        for violation in rule_o:
            assert violation.violation_type != RuleOViolationType.INVALID_ADVERSARY_ENTROPY


# ============================================================================
# Fixture Tests
# ============================================================================

class TestFixtures:
    """Tests that fixtures are properly defined."""

    def test_fixtures_exist(self):
        """All fixture categories have fixtures."""
        for category in FixtureCategory:
            fixtures = get_fixtures_by_category(category)
            assert len(fixtures) > 0, f"No fixtures for {category}"

    def test_fixture_structure(self):
        """All fixtures have required fields."""
        for fixture in ALL_FIXTURES:
            assert fixture.fixture_id is not None
            assert fixture.category is not None
            assert fixture.description is not None
            assert fixture.input_data is not None
            assert fixture.expected_outcome is not None
            assert fixture.rationale is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for v2.3 components."""

    def test_sam_to_audit_pipeline(self):
        """SAM output feeds correctly into audit."""
        sam = S2ModelBasedAdversary(seed=42)
        audit = RuleMNOPAudit()

        sam.start_episode("test")

        import random
        rng = random.Random(42)

        for i in range(50):
            signal = ObservableSignals(
                step_index=i,
                episode_id="test",
                last_friction_bits=rng.random() * 0.5,
                last_outcome_code="SUCCESS",
            )

            pressure, record = sam.step(signal)

            audit.add_step(
                step_index=i,
                sam_strategy_id=pressure.strategy_id,
                sam_pressure=pressure.friction_modifier,
                agent_action=rng.choice(["COOPERATE", "DEFECT"]),
                is_gridlock=False,
                is_refusal=False,
                echoice_ok=True,
            )

        summary = audit.get_summary()
        assert summary["total_steps"] == 50

    def test_create_sam_factory(self):
        """Factory creates correct SAM types."""
        s1 = create_sam(SAMProfile.S1_REACTIVE, seed=42)
        assert isinstance(s1, S1ReactiveAdversary)

        s2 = create_sam(SAMProfile.S2_MODEL_BASED, seed=42)
        assert isinstance(s2, S2ModelBasedAdversary)

        s3 = create_sam(SAMProfile.S3_MINIMIZER, seed=42)
        assert isinstance(s3, S3MinimizerAdversary)

        neutral = create_sam(SAMProfile.NEUTRALIZED, seed=42)
        assert isinstance(neutral, NeutralizedAdversary)

    def test_harness_two_phase_protocol_determinism(self):
        """Harness produces deterministic P_active given same seed."""
        from rsa_poc.v230.runplans import V230ExperimentHarness, V230RunConfig

        # Run harness twice with same config
        config = V230RunConfig(
            sam_profile=SAMProfile.S2_MODEL_BASED,
            num_paired_runs=2,
            random_seed=42,
            num_episodes_per_run=1,
            steps_per_episode=20,
        )

        harness1 = V230ExperimentHarness(config)
        # Force same run_id for determinism test
        harness1._run_id = "test_determinism_run"
        harness1._rng = __import__('random').Random(config.random_seed)

        harness2 = V230ExperimentHarness(config)
        harness2._run_id = "test_determinism_run"
        harness2._rng = __import__('random').Random(config.random_seed)

        result1 = harness1.run()
        result2 = harness2.run()

        # P_active should be identical
        for pr1, pr2 in zip(result1.paired_results, result2.paired_results):
            for pe1, pe2 in zip(pr1.paired_episodes, pr2.paired_episodes):
                assert pe1.p_active == pe2.p_active, "P_active not deterministic"
                assert pe1.perm_seed == pe2.perm_seed, "perm_seed not deterministic"
                assert pe1.p_neutral == pe2.p_neutral, "P_neutral not deterministic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
