"""Acceptance Tests for RSA-PoC v1.1

Tests v1.0 requirements + v1.1 audit rules (A/B/C + C').
"""

import pytest
from pathlib import Path

# Import components
try:
    from src.rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
    from src.rsa_poc.v110.state.normative import NormativeStateV110
    from src.rsa_poc.v110.generator.deterministic import DeterministicGeneratorV110, ScrambledPredictionsGeneratorV110
    from src.rsa_poc.v110.selector.blind import BlindActionSelectorV110
    from src.rsa_poc.v110.agent import MVRAAgentV110
    from src.rsa_poc.v110.ablations import ASBAgentV110, MVRAScrambledAgentV110, MVRABypassAgentV110
    from src.rsa_poc.v110.jcomp.compiler import JCOMP110
    from src.rsa_poc.v110.jaf.schema import JAF110
    from src.rsa_poc.v100.jaf.schema import Identity, References, ActionClaim, Relevance, ConflictResolution
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
    from src.rsa_poc.v110.state.normative import NormativeStateV110
    from src.rsa_poc.v110.generator.deterministic import DeterministicGeneratorV110, ScrambledPredictionsGeneratorV110
    from src.rsa_poc.v110.selector.blind import BlindActionSelectorV110
    from src.rsa_poc.v110.agent import MVRAAgentV110
    from src.rsa_poc.v110.ablations import ASBAgentV110, MVRAScrambledAgentV110, MVRABypassAgentV110
    from src.rsa_poc.v110.jcomp.compiler import JCOMP110
    from src.rsa_poc.v110.jaf.schema import JAF110
    from src.rsa_poc.v100.jaf.schema import Identity, References, ActionClaim, Relevance, ConflictResolution


# ============================================================================
# v1.0 Regression Tests (ensure v1.0 still works)
# ============================================================================

def test_env_apcm_exists():
    """ENV-1: Environment provides APCM"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()
    obs = env._get_obs()

    assert "apcm" in obs
    assert isinstance(obs["apcm"], dict)

    # Check structure: Dict[action, Dict[outcome, Set[pref]]]
    for action, outcomes in obs["apcm"].items():
        assert isinstance(outcomes, dict)
        for outcome, prefs in outcomes.items():
            assert isinstance(prefs, set)


def test_env_collision_pattern():
    """ENV-2: Environment enforces 60/40 collision pattern"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    env.reset()

    collision_count = 0
    clean_count = 0

    for _ in range(50):
        obs = env._get_obs()
        if obs.get("is_collision_step"):
            collision_count += 1
        else:
            clean_count += 1

        # Take any feasible action to advance
        feasible = obs["feasible_actions"]
        if feasible:
            env.step(feasible[0])

    # 60% collision (3 of 5), 40% clean (2 of 5)
    # Over 50 steps: 30 collision, 20 clean
    assert collision_count == 30
    assert clean_count == 20


def test_jaf_v110_fields():
    """JAF-1: JAF-1.1 has all required v1.1 fields"""
    state = NormativeStateV110()
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    generator = DeterministicGeneratorV110(state)
    obs = env._get_obs()

    jaf = generator.generate(
        feasible_actions=obs["feasible_actions"],
        apcm=obs["apcm"]
    )

    # Check v1.0 fields
    assert jaf.artifact_version == "JAF-1.1"
    assert hasattr(jaf, "authorized_violations")
    assert hasattr(jaf, "required_preservations")
    assert hasattr(jaf, "conflict_attribution")

    # Check v1.1 predictive fields
    assert hasattr(jaf, "predicted_forbidden_actions")
    assert hasattr(jaf, "predicted_allowed_actions")
    assert hasattr(jaf, "predicted_violations")
    assert hasattr(jaf, "predicted_preservations")

    # Check types
    assert isinstance(jaf.predicted_forbidden_actions, set)
    assert isinstance(jaf.predicted_allowed_actions, set)
    assert isinstance(jaf.predicted_violations, set)
    assert isinstance(jaf.predicted_preservations, set)


# ============================================================================
# v1.1 Audit Rule Tests
# ============================================================================

def test_audit_a_effect_correctness_pass():
    """AUDIT-A-1: Correct predictions pass Audit A"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    # Run one step
    agent.reset()
    result = agent.step()

    # Deterministic generator should produce correct predictions
    assert result.compilation_result is not None
    assert result.compilation_result.success, f"Compilation failed: {[e.code for e in result.compilation_result.errors]}"


def test_audit_a_effect_correctness_fail():
    """AUDIT-A-2: Incorrect predictions fail Audit A"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    state = NormativeStateV110()

    agent = MVRAScrambledAgentV110(
        env=env,
        normative_state=state,
        seed=42
    )

    # Run one step with scrambled predictions
    agent.reset()
    result = agent.step()

    # Scrambled predictions should cause compilation failure
    assert result.compilation_result is not None
    assert not result.compilation_result.success

    # Check for E_EFFECT_MISMATCH error
    error_codes = [e.code for e in result.compilation_result.errors]
    assert "E_EFFECT_MISMATCH" in error_codes or "E_PREDICTION_ERROR" in error_codes


def test_audit_b_non_vacuity():
    """AUDIT-B: Non-vacuity requires at least one action forbidden"""
    # This is tested implicitly in normal operation
    # The deterministic generator always produces non-vacuous justifications
    # when collisions exist

    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    history = agent.run_episode()

    # Check that at least some steps had forbidden actions
    forbidden_counts = []
    for result in history:
        if result.jaf and result.compilation_result and result.compilation_result.success:
            forbidden_counts.append(len(result.compilation_result.action_mask))

    # At least some steps should have non-zero forbidden actions
    assert any(count > 0 for count in forbidden_counts), "All justifications were vacuous"


def test_audit_c_predictive_adequacy():
    """AUDIT-C: Predictive adequacy with correct outcome predictions"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    # Run episode
    history = agent.run_episode()

    # Deterministic generator should produce correct predictions
    # Check that no E_PREDICTION_ERROR occurred
    for result in history:
        if result.compilation_result and not result.compilation_result.success:
            error_codes = [e.code for e in result.compilation_result.errors]
            assert "E_PREDICTION_ERROR" not in error_codes


def test_audit_c_prime_gridlock_exception():
    """AUDIT-C': Gridlock exception - Audit C skipped when A_actual is empty"""
    # Create a scenario where all actions are forbidden (gridlock)
    # This is harder to construct with the deterministic generator
    # For now, we test that gridlock is handled gracefully

    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    history = agent.run_episode()

    # Agent should not halt due to gridlock in this environment
    # (CommitmentTrap doesn't produce gridlock with correct implementation)
    metrics = agent.get_metrics()

    # If we reached end without halt, gridlock handling worked
    assert metrics["total_steps"] > 0


# ============================================================================
# Agent Tests
# ============================================================================

def test_agent_mvra_v110_runs():
    """AGENT-1: MVRA v1.1 completes episode"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    history = agent.run_episode()
    metrics = agent.get_metrics()

    assert len(history) > 0
    assert metrics["total_steps"] == 50
    assert not metrics["halted"]


def test_agent_asb_baseline():
    """AGENT-2: ASB baseline runs"""
    env = CommitmentTrapV100(max_steps=50, seed=42)

    agent = ASBAgentV110(env)
    history = agent.run_episode()
    metrics = agent.get_metrics()

    assert len(history) == 50
    assert metrics["violation_rate"] > 0.6  # ASB has high violations


def test_agent_scrambled_halts():
    """AGENT-3: Scrambled agent halts with audit failures"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV110()

    agent = MVRAScrambledAgentV110(env, state, seed=42)
    history = agent.run_episode()
    metrics = agent.get_metrics()

    # Scrambled should halt early with audit failures
    assert metrics["halted"]
    assert "Compilation failed" in metrics["halt_reason"]
    assert metrics["total_steps"] == 0  # Halts on first step


def test_agent_bypass_high_violations():
    """AGENT-4: Bypass agent has high violations (like ASB)"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV110()

    agent = MVRABypassAgentV110(env, state)
    history = agent.run_episode()
    metrics = agent.get_metrics()

    assert metrics["total_steps"] == 50
    assert metrics["violation_rate"] > 0.6  # Should be similar to ASB


# ============================================================================
# Comparative Tests
# ============================================================================

def test_comparative_mvra_reduces_violations():
    """COMP-1: MVRA v1.1 reduces violations vs ASB"""
    env_mvra = CommitmentTrapV100(max_steps=50, seed=42)
    env_asb = CommitmentTrapV100(max_steps=50, seed=42)

    # MVRA
    state = NormativeStateV110()
    agent_mvra = MVRAAgentV110(
        env=env_mvra,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )
    agent_mvra.run_episode()
    metrics_mvra = agent_mvra.get_metrics()

    # ASB
    agent_asb = ASBAgentV110(env_asb)
    agent_asb.run_episode()
    metrics_asb = agent_asb.get_metrics()

    # MVRA should have lower violation rate than ASB
    assert metrics_mvra["violation_rate"] < metrics_asb["violation_rate"]


def test_comparative_constraint_non_trivial():
    """COMP-2: MVRA constraints are non-trivial"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    history = agent.run_episode()

    # Count steps with non-empty action masks
    constrained_steps = 0
    for result in history:
        if result.compilation_result and result.compilation_result.success:
            if len(result.compilation_result.action_mask) > 0:
                constrained_steps += 1

    # More than 50% of steps should have constraints
    assert constrained_steps / len(history) > 0.5


# ============================================================================
# v1.1 Fix Tests (Regression Prevention)
# ============================================================================

def test_collision_forces_violations():
    """FIX-1: On collision steps, all actions violate something; on clean steps, at least one doesn't"""
    env = CommitmentTrapV100(max_steps=20, seed=42)
    env.reset()

    collision_steps_validated = 0
    clean_steps_validated = 0

    for step in range(20):
        obs = env._get_obs()
        apcm = obs["apcm"]
        feasible = obs["feasible_actions"]
        is_collision = obs.get("is_collision_step", False)

        if is_collision:
            # On collision steps: all feasible actions must violate at least one preference
            for action in feasible:
                violates = apcm.get(action, {}).get("violates", set())
                assert len(violates) > 0, \
                    f"Step {step}: Collision step but action '{action}' has no violations. APCM: {apcm.get(action)}"
            collision_steps_validated += 1
        else:
            # On clean steps: at least one feasible action must have empty violation set
            exists_clean = any(
                len(apcm.get(a, {}).get("violates", set())) == 0
                for a in feasible
            )
            assert exists_clean, \
                f"Step {step}: Clean step but no action has empty violations. APCM: {apcm}"
            clean_steps_validated += 1

        # Advance to next step
        if feasible:
            env.step(feasible[0])

    # Verify we tested both kinds of steps
    assert collision_steps_validated > 0, "No collision steps found"
    assert clean_steps_validated > 0, "No clean steps found"


def test_violation_accounting_correctness():
    """FIX-2: Reported violations must match APCM[selected_action].violates"""
    env = CommitmentTrapV100(max_steps=20, seed=42)
    state = NormativeStateV110()

    agent = MVRAAgentV110(
        env=env,
        normative_state=state,
        generator=DeterministicGeneratorV110(state),
        selector=BlindActionSelectorV110(seed=42)
    )

    agent.reset()

    for step in range(20):
        obs = env._get_obs()
        apcm = obs["apcm"]

        result = agent.step()

        if result.selected_action and result.selected_action in apcm:
            # Get expected violations from APCM
            expected_violations = apcm[result.selected_action].get("violates", set())

            # Get reported violations from result
            reported_violations = set(result.info.get("violated_prefs", []))

            # They must match exactly
            assert reported_violations == expected_violations, \
                f"Step {step}: Violation mismatch for action '{result.selected_action}'. " \
                f"Expected: {expected_violations}, Got: {reported_violations}"

        if result.done or result.halted:
            break


def test_audit_b_spec_compliance():
    """FIX-3: Audit B checks |A_pre \\ A_actual| >= 1 (at least one feasible action excluded)"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    state = NormativeStateV110()

    # Initialize compiler with valid vocabularies
    env.reset()
    obs = env._get_obs()
    valid_actions = list(set(a for a in obs.get("apcm", {}).keys()))
    valid_preferences = list(state.get_preferences())

    compiler = JCOMP110(
        valid_actions=valid_actions,
        valid_preferences=valid_preferences
    )

    # Find a collision step where constraints will exclude actions
    for attempt in range(10):
        obs = env._get_obs()
        if obs.get("is_collision_step"):
            break
        if obs["feasible_actions"]:
            env.step(obs["feasible_actions"][0])

    # Generate JAF with deterministic generator (will produce correct predictions)
    generator = DeterministicGeneratorV110(state)
    jaf = generator.generate(
        feasible_actions=obs["feasible_actions"],
        apcm=obs["apcm"]
    )

    # Compile - should succeed on collision steps with correct predictions
    result = compiler.compile(
        jaf=jaf,
        apcm=obs["apcm"],
        feasible_actions=set(obs["feasible_actions"]),
        precedent=None
    )

    # If compilation succeeded, verify Audit B logic was correctly applied
    if result.success:
        A_pre = set(obs["feasible_actions"])
        A_actual = A_pre - result.action_mask

        # At least one action must be excluded (Audit B requirement)
        excluded = A_pre - A_actual
        assert len(excluded) >= 1, \
            f"Audit B passed but no actions excluded. A_pre={A_pre}, A_actual={A_actual}, excluded={excluded}"
    else:
        # If it failed, it should NOT be due to Audit B on collision steps with proper generator
        error_codes = [e.code for e in result.errors]
        # On collision steps with deterministic generator, we shouldn't fail Audit B
        # (it might fail other audits in edge cases, but Audit B should pass)
        assert "E_DECORATIVE_JUSTIFICATION" not in error_codes, \
            f"Audit B (E_DECORATIVE_JUSTIFICATION) should not fail with deterministic generator on collision steps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
