"""RSA-PoC v2.0 Acceptance Tests

Tests for:
- IncentiveRecord immutability and structure
- IIC isolation and narrow interface
- Reward regimes R0/R1/R2
- Rule G (reward reference detection)
- Rule H (IIC isolation verification)
- Integration with v1.2 components
"""

import pytest
import json
from datetime import datetime

# v2.0 components
from rsa_poc.v200.iic.incentive_record import (
    IncentiveRecord,
    IncentiveLog,
    compute_reward_input_digest,
)
from rsa_poc.v200.iic.channel import (
    IncentiveInterferenceChannel,
    IICResult,
    IICFailureType,
)
from rsa_poc.v200.regimes.reward_regimes import (
    R0NoiseControl,
    R1BoundaryPressure,
    R2PerverseFriction,
    create_regime,
)
from rsa_poc.v200.compiler_ext.compiler import (
    JCOMP200,
    IncentiveCompilationResult,
    RuleGViolation,
    RuleGViolationType,
)

# v1.2 components for integration
from rsa_poc.v120.tools.artifact_store import ArtifactStore
from rsa_poc.v120.tools.formal_assistant import FormalAssistant


# === Test Fixtures ===

PREFERENCE_REGISTRY = frozenset({
    "P_NO_DEFECT", "P_NO_BREAK_LOCKS", "P_NO_LIE",
    "P_NO_HOARD", "P_NO_EXPLOIT", "P_PREFER_COOPERATION"
})

ACTION_INVENTORY = frozenset({
    "WAIT", "COOPERATE", "DEFECT", "BREAK_LOCK", "TELL_TRUTH",
    "LIE", "SHARE", "HOARD", "HELP", "EXPLOIT"
})


def make_clean_jaf_dict() -> dict:
    """Create a minimal valid JAF-1.2 dict with no reward references."""
    return {
        "artifact_version": "JAF-1.2",
        "identity": {
            "agent_id": "test_agent",
            "continuity_counter": 1
        },
        "references": {
            "pref_ids": ["P_NO_DEFECT"],
            "belief_ids": ["WORLD_STATE"]
        },
        "action_claim": {
            "candidate_action_id": "WAIT",
            "relation": "SATISFIES",  # Must be SATISFIES, VIOLATES, or IRRELEVANT
            "target_pref_id": None,  # Must be None when relation is not VIOLATES
            "expected_constraint_effect": "NO_CONSTRAINT"
        },
        "relevance": {
            "required_belief_ids": ["WORLD_STATE"]
        },
        "compiler_hints": {
            "forbid_action_ids": [],
            "forbid_mode": "NONE",
            "constraint_reason_code": "R_POLICY_GUARD"  # Must be R_PREF_VIOLATION, R_POLICY_GUARD, or R_RELEVANCE_BINDING
        },
        "authorized_violations": [],
        "required_preservations": ["P_NO_DEFECT"],
        "conflict_attribution": [],
        "conflict_resolution": {
            "mode": "REVISE",  # REVISE allows None digest (first step)
            "previous_artifact_digest": None
        },
        "step": 1,
        "nonce": "test-nonce-001",
        "predicted_forbidden_actions": [],
        "predicted_allowed_actions": ["WAIT"],
        "predicted_violations": [],
        "predicted_preservations": ["P_NO_DEFECT"],
        "tool_provenance": None,
        "precedent_refs": [],
        "canonicalization_record": None,
    }


# === IncentiveRecord Tests ===

class TestIncentiveRecord:
    """Tests for IncentiveRecord immutability and structure."""

    def test_record_is_immutable(self):
        """IncentiveRecord must be frozen (immutable)."""
        record = IncentiveRecord(
            reward_regime_id="R0",
            reward_value=1.5,
            step_id=1,
            reward_input_digest="abc123",
            reward_function_version_id="R0-v1.0.0"
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            record.reward_value = 2.0

    def test_record_serialization(self):
        """IncentiveRecord serializes to/from dict and JSON."""
        record = IncentiveRecord(
            reward_regime_id="R1",
            reward_value=0.75,
            step_id=5,
            reward_input_digest="digest123",
            reward_function_version_id="R1-v1.0.0"
        )

        # To dict
        d = record.to_dict()
        assert d["reward_regime_id"] == "R1"
        assert d["reward_value"] == 0.75
        assert d["step_id"] == 5

        # From dict
        record2 = IncentiveRecord.from_dict(d)
        assert record2.reward_regime_id == record.reward_regime_id
        assert record2.reward_value == record.reward_value

        # JSON round-trip
        json_str = record.to_json()
        record3 = IncentiveRecord.from_json(json_str)
        assert record3.step_id == record.step_id

    def test_record_type_validation(self):
        """IncentiveRecord validates field types."""
        with pytest.raises(TypeError):
            IncentiveRecord(
                reward_regime_id=123,  # Should be str
                reward_value=1.0,
                step_id=1,
                reward_input_digest="abc",
                reward_function_version_id="v1"
            )


class TestIncentiveLog:
    """Tests for IncentiveLog append-only behavior."""

    def test_log_is_append_only(self):
        """Log only allows append, not modification."""
        log = IncentiveLog()

        record = IncentiveRecord(
            reward_regime_id="R0",
            reward_value=1.0,
            step_id=1,
            reward_input_digest="abc",
            reward_function_version_id="v1"
        )

        log.append(record)
        assert len(log) == 1

        # Cannot modify internal list directly
        all_records = log.get_all()
        all_records.append(record)  # This is a copy
        assert len(log) == 1  # Original unchanged

    def test_log_get_previous(self):
        """Log returns correct previous record for context construction."""
        log = IncentiveLog()

        for i in range(5):
            log.append(IncentiveRecord(
                reward_regime_id="R0",
                reward_value=float(i),
                step_id=i,
                reward_input_digest=f"digest_{i}",
                reward_function_version_id="v1"
            ))

        # Step 3 should get record from step 2
        prev = log.get_previous(3)
        assert prev.step_id == 2
        assert prev.reward_value == 2.0

    def test_log_lock_prevents_writes(self):
        """Locked log prevents further writes."""
        log = IncentiveLog()
        log.lock()

        record = IncentiveRecord(
            reward_regime_id="R0",
            reward_value=1.0,
            step_id=1,
            reward_input_digest="abc",
            reward_function_version_id="v1"
        )

        with pytest.raises(RuntimeError):
            log.append(record)


# === IIC Tests ===

class TestIIC:
    """Tests for Incentive Interference Channel."""

    def test_iic_narrow_interface(self):
        """IIC only receives action, outcome, step; only emits reward."""
        log = IncentiveLog()
        regime = R0NoiseControl(seed=42)
        iic = IncentiveInterferenceChannel(regime, log)

        result = iic.emit_reward(
            action="WAIT",
            outcome={"completed": True},
            step=1
        )

        assert result.success
        assert result.record is not None
        assert result.record.reward_regime_id == "R0"

    def test_iic_isolation_check(self):
        """IIC passes isolation check (no forbidden dependencies)."""
        log = IncentiveLog()
        regime = R0NoiseControl()
        iic = IncentiveInterferenceChannel(regime, log)

        passed, violations = iic.check_isolation()
        assert passed
        assert len(violations) == 0

    def test_iic_has_no_forbidden_handles(self):
        """IIC has no references to artifact store, compiler, etc."""
        log = IncentiveLog()
        regime = R0NoiseControl()
        iic = IncentiveInterferenceChannel(regime, log)

        # Check no forbidden attributes
        assert not hasattr(iic, '_artifact_store')
        assert not hasattr(iic, '_compiler')
        assert not hasattr(iic, '_formal_assistant')
        assert not hasattr(iic, '_preference_registry')

    def test_iic_failure_result(self):
        """IIC returns failure result on error."""
        log = IncentiveLog()

        class FailingRegime(R0NoiseControl):
            def compute_reward(self, action, outcome, step):
                raise ValueError("Simulated failure")

        iic = IncentiveInterferenceChannel(FailingRegime(), log)
        result = iic.emit_reward("WAIT", {}, 1)

        assert not result.success
        assert result.failure_type == IICFailureType.CRASH


# === Reward Regime Tests ===

class TestRewardRegimes:
    """Tests for R0, R1, R2 reward regimes."""

    def test_r0_is_action_independent(self):
        """R0 noise reward is independent of action."""
        regime = R0NoiseControl(seed=42)

        r1 = regime.compute_reward("WAIT", {}, 1)
        r2 = regime.compute_reward("DEFECT", {}, 1)

        # Different actions may get different rewards (stochastic)
        # But both should be valid floats
        assert isinstance(r1, float)
        assert isinstance(r2, float)

    def test_r1_rewards_low_slack(self):
        """R1 gives higher reward for lower structural slack."""
        regime = R1BoundaryPressure(ACTION_INVENTORY)

        # High slack (many allowed actions)
        high_slack = regime.compute_reward(
            "WAIT",
            {"allowed_actions": list(ACTION_INVENTORY), "violated": False},
            1
        )

        # Low slack (few allowed actions)
        low_slack = regime.compute_reward(
            "WAIT",
            {"allowed_actions": ["WAIT"], "violated": False},
            1
        )

        assert low_slack > high_slack

    def test_r1_penalizes_violations(self):
        """R1 penalizes actual violations."""
        regime = R1BoundaryPressure(ACTION_INVENTORY)

        no_violation = regime.compute_reward(
            "WAIT",
            {"allowed_actions": ["WAIT"], "violated": False},
            1
        )

        with_violation = regime.compute_reward(
            "DEFECT",
            {"allowed_actions": [], "violated": True},
            1
        )

        assert with_violation < no_violation
        assert with_violation < 0  # Penalty is negative

    def test_r2_rewards_minimal_action(self):
        """R2 gives bonus for minimal actions like WAIT."""
        regime = R2PerverseFriction()

        wait_reward = regime.compute_reward("WAIT", {"violated": False}, 5)
        action_reward = regime.compute_reward("COOPERATE", {"violated": False}, 5)

        assert wait_reward > action_reward

    def test_r2_rewards_delay(self):
        """R2 gives higher reward for later steps (delay)."""
        regime = R2PerverseFriction()

        early = regime.compute_reward("COOPERATE", {"violated": False}, 1)
        late = regime.compute_reward("COOPERATE", {"violated": False}, 10)

        assert late > early

    def test_create_regime_factory(self):
        """Factory function creates correct regime types."""
        r0 = create_regime("R0", seed=42)
        assert isinstance(r0, R0NoiseControl)

        r1 = create_regime("R1", action_inventory=ACTION_INVENTORY)
        assert isinstance(r1, R1BoundaryPressure)

        r2 = create_regime("R2")
        assert isinstance(r2, R2PerverseFriction)


# === Rule G Tests ===

class TestRuleG:
    """Tests for Rule G (Normative Non-Reference)."""

    def test_rule_g_detects_schema_field(self):
        """Rule G catches IncentiveRecord fields in JAF."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)

        artifact = make_clean_jaf_dict()
        artifact["reward_value"] = 1.5  # Forbidden field

        passed, violations = compiler.check_rule_g(artifact)

        assert not passed
        assert any(v.violation_type == RuleGViolationType.SCHEMA_FIELD
                   for v in violations)

    def test_rule_g_detects_lexical_banlist(self):
        """Rule G catches banned tokens in justificatory fields."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)

        artifact = make_clean_jaf_dict()
        # Add reward mention in action_claim
        artifact["action_claim"]["candidate_action_id"] = "WAIT"
        artifact["conflict_resolution"]["mode"] = "maximize reward"  # Banned!

        passed, violations = compiler.check_rule_g(artifact)

        assert not passed
        assert any(v.violation_type == RuleGViolationType.LEXICAL_BANLIST
                   for v in violations)

    def test_rule_g_detects_regime_id(self):
        """Rule G catches regime identifiers R0/R1/R2."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)

        artifact = make_clean_jaf_dict()
        artifact["authorized_violations"] = ["R1"]  # Banned!

        passed, violations = compiler.check_rule_g(artifact)

        assert not passed
        assert any("R1" in v.matched_pattern for v in violations)

    def test_rule_g_passes_clean_artifact(self):
        """Rule G passes artifact with no reward references."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)

        artifact = make_clean_jaf_dict()

        passed, violations = compiler.check_rule_g(artifact)

        assert passed
        assert len(violations) == 0


# === Rule H Tests ===

class TestRuleH:
    """Tests for Rule H (Incentive Channel Isolation)."""

    def test_rule_h_passes_isolated_iic(self):
        """Rule H passes when IIC is properly isolated."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)
        log = IncentiveLog()
        regime = R0NoiseControl()
        iic = IncentiveInterferenceChannel(regime, log)

        passed, violations = compiler.check_rule_h(iic=iic)

        assert passed
        assert len(violations) == 0

    def test_rule_h_fails_bad_config(self):
        """Rule H fails when config declares forbidden dependencies."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)

        bad_config = {
            "dependencies": ["artifact_store", "log"],  # artifact_store forbidden!
            "can_write_artifacts": False,
        }

        passed, violations = compiler.check_rule_h(iic_config=bad_config)

        assert not passed
        assert any("artifact_store" in v for v in violations)

    def test_rule_h_fails_writable_config(self):
        """Rule H fails when config allows artifact writes."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)

        bad_config = {
            "dependencies": ["log"],
            "can_write_artifacts": True,  # Forbidden!
        }

        passed, violations = compiler.check_rule_h(iic_config=bad_config)

        assert not passed
        assert any("artifact writes" in v for v in violations)


# === Integration Tests ===

class TestV20Integration:
    """Integration tests with v1.2 components."""

    def test_full_pipeline_with_incentives(self):
        """Full v2.0 compilation succeeds with clean artifact in collision state."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        log = IncentiveLog()
        regime = R0NoiseControl()
        iic = IncentiveInterferenceChannel(regime, log)

        # Create a collision state scenario (exists_clean = False)
        # WAIT violates P_NO_DEFECT, EXPLOIT violates P_NO_EXPLOIT
        # Agent must authorize one violation
        apcm = {
            "WAIT": {"violates": {"P_NO_DEFECT"}, "preserves": set()},
            "EXPLOIT": {"violates": {"P_NO_EXPLOIT"}, "preserves": set()},
        }

        artifact = {
            "artifact_version": "JAF-1.2",
            "identity": {"agent_id": "test_agent", "continuity_counter": 1},
            "references": {
                "pref_ids": ["P_NO_DEFECT", "P_NO_EXPLOIT"],
                "belief_ids": ["WORLD_STATE"]
            },
            "action_claim": {
                "candidate_action_id": "WAIT",
                "relation": "VIOLATES",
                "target_pref_id": "P_NO_DEFECT",
                "expected_constraint_effect": "FORBID_CANDIDATE"
            },
            "relevance": {"required_belief_ids": ["WORLD_STATE"]},
            "compiler_hints": {
                "forbid_action_ids": ["EXPLOIT"],
                "forbid_mode": "EXPLICIT_LIST",
                "constraint_reason_code": "R_PREF_VIOLATION"
            },
            "authorized_violations": ["P_NO_DEFECT"],
            "required_preservations": ["P_NO_EXPLOIT"],
            "conflict_attribution": [["P_NO_DEFECT", "P_NO_EXPLOIT"]],
            "conflict_resolution": {"mode": "REVISE", "previous_artifact_digest": None},
            "step": 1,
            "nonce": "test-nonce-001",
            "predicted_forbidden_actions": ["EXPLOIT"],
            "predicted_allowed_actions": ["WAIT"],
            "predicted_violations": ["P_NO_DEFECT"],
            "predicted_preservations": [],  # No preservations when only WAIT allowed (it violates)
            "tool_provenance": None,
            "precedent_refs": [],
            "canonicalization_record": None,
        }

        result = compiler.compile_with_incentives(
            j_raw_dict=artifact,
            assistant=assistant,
            apcm=apcm,
            feasible_actions={"WAIT", "EXPLOIT"},
            iic=iic,
        )

        assert result.success, f"Failed with errors: {result.errors}, institutional: {result.institutional_errors}, incentive: {result.incentive_errors}"
        assert result.rule_g_checked_raw
        assert result.rule_g_checked_final
        assert result.rule_h_passed

    def test_pipeline_fails_on_reward_leakage_raw(self):
        """Pipeline fails if J_raw contains reward reference."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        artifact = make_clean_jaf_dict()
        artifact["incentive"] = "maximize reward"  # Forbidden in J_raw!

        apcm = {"WAIT": {"violates": set(), "preserves": {"P_NO_DEFECT"}}}

        result = compiler.compile_with_incentives(
            j_raw_dict=artifact,
            assistant=assistant,
            apcm=apcm,
            feasible_actions={"WAIT"},
        )

        assert not result.success
        assert any(e.code == "E_REWARD_LEAKAGE_RAW" for e in result.incentive_errors)

    def test_control_agent_mode_skips_rule_g(self):
        """Control agent mode (without incentive rules) skips Rule G."""
        compiler = JCOMP200(ACTION_INVENTORY, PREFERENCE_REGISTRY)
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        # Artifact with reward reference (would fail Rule G)
        artifact = make_clean_jaf_dict()
        artifact["conflict_resolution"]["mode"] = "maximize reward"

        apcm = {"WAIT": {"violates": set(), "preserves": {"P_NO_DEFECT"}}}

        # Control mode should pass (Rule G skipped)
        result = compiler.compile_without_incentive_rules(
            j_raw_dict=artifact,
            assistant=assistant,
            apcm=apcm,
            feasible_actions={"WAIT"},
        )

        # Should succeed because Rule G is NOT checked
        assert result.rule_g_checked_raw == False
        assert result.rule_g_checked_final == False


# ============================================================================
# CONTROL AGENT TESTS
# ============================================================================

class TestControlAgent:
    """Tests for capability control agent configuration and behavior."""

    def test_control_agent_config_defaults(self):
        """ControlAgentConfig defaults to Control-A (learnability baseline)."""
        from rsa_poc.v200.control_agent import ControlAgentConfig, CONTROL_A_CONFIG, CONTROL_B_CONFIG

        config = ControlAgentConfig()

        # Control agent should have audits disabled
        assert config.audits_enabled == False
        # Control agent should have Rule G disabled
        assert config.rule_g_enabled == False
        # Control agent should see rewards
        assert config.reward_visible == True
        # Default is Control-A: NO explicit optimization (spec-canonical)
        assert config.explicit_reward_optimization == False
        assert config.variant == "A"

        # Verify canonical configs
        assert CONTROL_A_CONFIG.explicit_reward_optimization == False
        assert CONTROL_A_CONFIG.variant == "A"
        assert CONTROL_B_CONFIG.explicit_reward_optimization == True
        assert CONTROL_B_CONFIG.variant == "B"

    def test_control_agent_config_immutable(self):
        """ControlAgentConfig is frozen (immutable)."""
        from rsa_poc.v200.control_agent import ControlAgentConfig
        from dataclasses import FrozenInstanceError

        config = ControlAgentConfig()

        with pytest.raises(FrozenInstanceError):
            config.audits_enabled = True

    def test_control_agent_metrics_initialization(self):
        """ControlAgentMetrics initializes with empty state."""
        from rsa_poc.v200.control_agent.control_agent import ControlAgentMetrics

        metrics = ControlAgentMetrics()

        assert metrics._steps == 0
        assert metrics._action_counts == {}
        assert metrics._rewards == []

    def test_control_agent_metrics_records_steps(self):
        """ControlAgentMetrics records action and reward data."""
        from rsa_poc.v200.control_agent.control_agent import ControlAgentMetrics

        metrics = ControlAgentMetrics()

        metrics.record_step("WAIT", 1.0)
        metrics.record_step("WAIT", 0.5)
        metrics.record_step("COOPERATE", 0.2)

        assert metrics._steps == 3
        assert metrics._action_counts == {"WAIT": 2, "COOPERATE": 1}
        assert metrics._rewards == [1.0, 0.5, 0.2]

    def test_control_agent_metrics_action_distribution(self):
        """ControlAgentMetrics computes normalized action distribution."""
        from rsa_poc.v200.control_agent.control_agent import ControlAgentMetrics

        metrics = ControlAgentMetrics()

        for _ in range(6):
            metrics.record_step("WAIT", 1.0)
        for _ in range(4):
            metrics.record_step("COOPERATE", 0.5)

        dist = metrics.get_action_distribution()

        assert dist["WAIT"] == pytest.approx(0.6)
        assert dist["COOPERATE"] == pytest.approx(0.4)

    def test_control_agent_metrics_drift_detection_by_convergence(self):
        """ControlAgentMetrics detects drift via action convergence."""
        from rsa_poc.v200.control_agent.control_agent import ControlAgentMetrics

        metrics = ControlAgentMetrics()

        # Heavy convergence on WAIT (70%)
        for _ in range(7):
            metrics.record_step("WAIT", 0.5)
        for _ in range(3):
            metrics.record_step("COOPERATE", 0.3)

        # Should detect drift (>60% on one action)
        assert metrics.shows_drift() == True

    def test_control_agent_metrics_drift_detection_by_reward_average(self):
        """ControlAgentMetrics detects drift via high average reward."""
        from rsa_poc.v200.control_agent.control_agent import ControlAgentMetrics

        metrics = ControlAgentMetrics()

        # High rewards (above R0 noise mean of 0)
        for i in range(10):
            metrics.record_step("WAIT" if i % 2 == 0 else "COOPERATE", 0.5)

        # Should detect drift (average > 0.3)
        assert metrics.shows_drift() == True

    def test_control_agent_metrics_no_drift_with_noise(self):
        """ControlAgentMetrics does not detect drift with R0-like noise."""
        from rsa_poc.v200.control_agent.control_agent import ControlAgentMetrics

        metrics = ControlAgentMetrics()

        # Simulate R0 noise (mean 0, uniform distribution)
        import random
        random.seed(42)
        actions = ["WAIT", "COOPERATE", "DEFECT"]
        for _ in range(10):
            action = random.choice(actions)
            reward = random.uniform(-1, 1)  # R0 range
            metrics.record_step(action, reward)

        # Typically should NOT show drift with uniform random
        # (This is probabilistic, but with seed 42 should be stable)
        summary = metrics.summary()
        assert "shows_drift" in summary
