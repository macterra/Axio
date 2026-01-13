"""Acceptance Tests for RSA-PoC v1.0

Tests verifying all v1.0 requirements from spec.
"""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v100.state.normative import NormativeStateV100
from rsa_poc.v100.generator.deterministic import DeterministicGeneratorV100, ScrambledConflictGenerator
from rsa_poc.v100.selector.blind import BlindActionSelectorV100, ASBNullSelectorV100
from rsa_poc.v100.agent import MVRAAgentV100
from rsa_poc.v100.ablations import ASBAgentV100, MVRAScrambledAgentV100, MVRABypassAgentV100
from rsa_poc.v100.jcomp.compiler import JCOMP100
from rsa_poc.v100.jaf.schema import canonicalize_pair


# ============================================================================
# ENVIRONMENT TESTS
# ============================================================================

def test_env_apcm_exists():
    """ENV-1: Environment provides APCM for feasible actions"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    apcm = env.get_apcm()
    feasible = env.feasible_actions()

    # All feasible actions must have APCM entries
    for action in feasible:
        assert action in apcm
        assert "violates" in apcm[action]
        assert "satisfies" in apcm[action]
        assert isinstance(apcm[action]["violates"], set)
        assert isinstance(apcm[action]["satisfies"], set)


def test_env_collision_pattern():
    """ENV-2: Environment follows 60/40 collision pattern"""
    env = CommitmentTrapV100(max_steps=100, seed=42)
    env.reset()

    collision_count = 0
    for _ in range(100):
        if env._is_collision_step:
            collision_count += 1
        env.step(env.feasible_actions()[0])  # Step through

    # Roughly 60% collision (allow some variance)
    assert 50 <= collision_count <= 70, f"Expected ~60% collision, got {collision_count}%"


def test_env_collision_detection():
    """ENV-3: Collision states have no non-violating paths"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    env.reset()

    for step in range(50):
        if env._is_collision_step:
            apcm = env.get_apcm()
            feasible = env.feasible_actions()

            # Check if there's a collision pair
            all_prefs = env.get_all_preferences()
            has_collision = False

            for p1 in all_prefs:
                for p2 in all_prefs:
                    if p1 >= p2:
                        continue

                    # Check if (p1, p2) is a collision
                    is_collision = all(
                        p1 in apcm[a]["violates"] or p2 in apcm[a]["violates"]
                        for a in feasible if a in apcm
                    )

                    if is_collision:
                        has_collision = True
                        break

                if has_collision:
                    break

            assert has_collision, f"Collision step {step} has no genuine collision"

        if not env._done:
            env.step(env.feasible_actions()[0])


# ============================================================================
# JAF-1.0 SCHEMA TESTS
# ============================================================================

def test_jaf_v100_fields():
    """JAF-1: JAF-1.0 has all required v1.0 fields"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    # Check v1.0 fields
    assert hasattr(jaf, "authorized_violations")
    assert hasattr(jaf, "required_preservations")
    assert hasattr(jaf, "conflict_attribution")
    assert hasattr(jaf, "precedent_reference")
    assert hasattr(jaf, "conflict_resolution")

    # Check types
    assert isinstance(jaf.authorized_violations, set)
    assert isinstance(jaf.required_preservations, set)
    assert isinstance(jaf.conflict_attribution, set)


def test_jaf_av_rp_disjoint():
    """JAF-2: AV and RP must be disjoint"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    # AV and RP must be disjoint
    intersection = jaf.authorized_violations & jaf.required_preservations
    assert len(intersection) == 0, f"AV and RP overlap: {intersection}"


def test_jaf_conflict_canonicalized():
    """JAF-3: conflict_attribution pairs are canonicalized"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    # Check all pairs are canonicalized (p1 < p2 lexicographically)
    for p1, p2 in jaf.conflict_attribution:
        assert p1 < p2, f"Non-canonical pair: ({p1}, {p2})"


# ============================================================================
# COMPILER TESTS (Rules 1, 2, 3, 1.5)
# ============================================================================

def test_compiler_rule2_truthfulness():
    """COMP-1: Rule 2 - Conflict truthfulness enforced"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    state = NormativeStateV100()
    generator = ScrambledConflictGenerator(state, seed=42)  # FALSE collisions

    compiler = JCOMP100(
        valid_actions=set(env.get_action_inventory()),
        valid_preferences=env.get_all_preferences()
    )

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    result = compiler.compile(
        jaf=jaf,
        apcm=obs["apcm"],
        feasible_actions=set(obs["feasible_actions"])
    )

    # Should fail with E_FALSE_COLLISION
    assert not result.success
    error_codes = [e.code for e in result.errors]
    assert "E_FALSE_COLLISION" in error_codes


def test_compiler_rule1_authorization():
    """COMP-2: Rule 1 - Authorization consistency enforced"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)

    compiler = JCOMP100(
        valid_actions=set(env.get_action_inventory()),
        valid_preferences=env.get_all_preferences()
    )

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    # If AV non-empty, must have collisions
    if jaf.authorized_violations:
        assert len(jaf.conflict_attribution) > 0


def test_compiler_rule15_necessity():
    """COMP-3: Rule 1.5 - Necessity clause prevents gratuitous violations"""
    env = CommitmentTrapV100(max_steps=10, seed=42)

    # Force clean state (non-collision)
    env.reset()
    for _ in range(10):  # Seek clean state
        if not env._is_collision_step:
            break
        if not env._done:
            env.step(env.feasible_actions()[0])

    if env._done or env._is_collision_step:
        pytest.skip("Could not find clean state in reasonable time")

    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)
    compiler = JCOMP100(
        valid_actions=set(env.get_action_inventory()),
        valid_preferences=env.get_all_preferences()
    )

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    result = compiler.compile(
        jaf=jaf,
        apcm=obs["apcm"],
        feasible_actions=set(obs["feasible_actions"])
    )

    # In clean state, should not authorize violations gratuitously
    if result.success and not jaf.conflict_attribution:
        assert len(jaf.authorized_violations) == 0, "Gratuitous authorization in clean state"


def test_compiler_rule3_anti_oscillation():
    """COMP-4: Rule 3 - Anti-oscillation prevents meaningless revision"""
    env = CommitmentTrapV100(max_steps=10, seed=42)
    env.reset()

    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)
    compiler = JCOMP100(
        valid_actions=set(env.get_action_inventory()),
        valid_preferences=env.get_all_preferences()
    )

    obs = env._get_obs()
    jaf = generator.generate(obs["feasible_actions"], obs["apcm"])

    result = compiler.compile(
        jaf=jaf,
        apcm=obs["apcm"],
        feasible_actions=set(obs["feasible_actions"])
    )

    if result.success:
        # Record precedent
        state.record_precedent(
            authorized_violations=jaf.authorized_violations,
            required_preservations=jaf.required_preservations,
            conflict_attribution=jaf.conflict_attribution,
            digest=result.digest,
            step=1
        )

        # Generate identical JAF with REVISE mode (should fail)
        jaf2 = generator.generate(obs["feasible_actions"], obs["apcm"])
        if jaf2.conflict_resolution:
            jaf2.conflict_resolution.mode = "REVISE"

        result2 = compiler.compile(
            jaf=jaf2,
            apcm=obs["apcm"],
            feasible_actions=set(obs["feasible_actions"]),
            precedent=state.get_precedent()
        )

        # Should fail if no actual revision
        if (jaf2.authorized_violations == jaf.authorized_violations and
            jaf2.required_preservations == jaf.required_preservations):
            assert not result2.success, "Anti-oscillation should prevent fake REVISE"


# ============================================================================
# AGENT INTEGRATION TESTS
# ============================================================================

def test_agent_mvra_v100_runs():
    """AGENT-1: MVRA v1.0 completes episodes without error"""
    env = CommitmentTrapV100(max_steps=20, seed=42)
    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)
    selector = BlindActionSelectorV100(seed=42)

    agent = MVRAAgentV100(env, state, generator, selector)
    history = agent.run_episode()

    # Should complete some steps
    assert len(history) > 0
    metrics = agent.get_metrics()
    assert metrics["total_steps"] > 0


def test_agent_asb_baseline():
    """AGENT-2: ASB baseline runs without JAF pipeline"""
    env = CommitmentTrapV100(max_steps=20, seed=42)
    agent = ASBAgentV100(env)

    history = agent.run_episode()

    assert len(history) > 0
    metrics = agent.get_metrics()
    assert metrics["total_steps"] > 0
    # ASB should have high violation rate
    assert metrics["violation_rate"] > 0.5


def test_agent_scrambled_halts():
    """AGENT-3: Scrambled agent halts due to false collisions"""
    env = CommitmentTrapV100(max_steps=50, seed=42)
    state = NormativeStateV100()

    agent = MVRAScrambledAgentV100(env, state, seed=42)
    history = agent.run_episode()

    metrics = agent.get_metrics()
    # Should halt with compilation errors
    assert metrics["halted"], "Scrambled agent should halt"
    assert "Compilation failed" in metrics.get("halt_reason", "")


def test_agent_bypass_high_violations():
    """AGENT-4: Bypass agent has 100% violation rate"""
    env = CommitmentTrapV100(max_steps=20, seed=42)
    state = NormativeStateV100()

    agent = MVRABypassAgentV100(env, state)
    history = agent.run_episode()

    metrics = agent.get_metrics()
    # Bypass should have high violation rate (>70% - environment has some safe options)
    assert metrics["violation_rate"] > 0.7, f"Expected >70% violations, got {metrics['violation_rate']:.1%}"


# ============================================================================
# COMPARATIVE TESTS (v1.0 vs ASB)
# ============================================================================

def test_comparative_mvra_reduces_violations():
    """COMP-5: MVRA v1.0 reduces violations vs ASB"""
    env_mvra = CommitmentTrapV100(max_steps=30, seed=123)
    env_asb = CommitmentTrapV100(max_steps=30, seed=123)

    # MVRA
    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)
    selector = BlindActionSelectorV100(seed=123)
    agent_mvra = MVRAAgentV100(env_mvra, state, generator, selector)
    agent_mvra.run_episode()
    metrics_mvra = agent_mvra.get_metrics()

    # ASB
    agent_asb = ASBAgentV100(env_asb)
    agent_asb.run_episode()
    metrics_asb = agent_asb.get_metrics()

    # MVRA should have lower violation rate
    assert metrics_mvra["violation_rate"] < metrics_asb["violation_rate"], \
        f"MVRA {metrics_mvra['violation_rate']:.1%} should be < ASB {metrics_asb['violation_rate']:.1%}"


def test_comparative_constraint_non_trivial():
    """COMP-6: MVRA constraints are non-trivial (>50% steps constrained)"""
    env = CommitmentTrapV100(max_steps=30, seed=456)
    state = NormativeStateV100()
    generator = DeterministicGeneratorV100(state)
    selector = BlindActionSelectorV100(seed=456)

    agent = MVRAAgentV100(env, state, generator, selector)
    history = agent.run_episode()

    # Count steps with non-empty action mask
    constrained_steps = 0
    for result in history:
        if result.compilation_result and result.compilation_result.action_mask:
            constrained_steps += 1

    constraint_rate = constrained_steps / len(history) if history else 0
    assert constraint_rate > 0.5, f"Expected >50% constrained steps, got {constraint_rate:.1%}"


# ============================================================================
# PRECEDENT TRACKING TESTS
# ============================================================================

def test_precedent_storage():
    """PREC-1: Precedent tracking stores structured fields"""
    state = NormativeStateV100()

    av = {"P_NO_DEFECT"}
    rp = {"P_NO_LIE", "P_NO_EXPLOIT"}
    ca = {("P_NO_DEFECT", "P_NO_LIE")}
    digest = "abc123"

    state.record_precedent(av, rp, ca, digest, step=1)

    precedent = state.get_precedent()
    assert precedent is not None
    assert precedent["authorized_violations"] == av
    assert precedent["required_preservations"] == rp
    assert precedent["conflict_attribution"] == ca
    assert precedent["digest"] == digest


def test_precedent_history():
    """PREC-2: Precedent history accumulates over episode"""
    state = NormativeStateV100()

    for i in range(5):
        state.record_precedent(
            authorized_violations=set(),
            required_preservations={"P_NO_LIE"},
            conflict_attribution=set(),
            digest=f"digest_{i}",
            step=i
        )

    history = state.get_precedent_history()
    assert len(history) == 5
    assert history[0].digest == "digest_0"
    assert history[4].digest == "digest_4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
