"""Acceptance Tests for RSA-PoC v0.1

Tests per poc_instructions_v0.1.md §12
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from v010.envs.commitment_trap import CommitmentTrapV010
from v010.state.normative import NormativeState, BeliefRegistryV010, PreferenceRegistryV010
from v010.jaf.schema import JAF010, Identity, References, ActionClaim, Relevance, CompilerHints
from v010.jcomp.compiler import JCOMP010
from v010.generator.deterministic import DeterministicJustificationGenerator
from v010.selector.blind import BlindActionSelector


class TestEnvironment:
    """Test COMMITMENT_TRAP_V010 environment"""

    def test_environment_basics(self):
        """Test environment initialization and basic operations"""
        env = CommitmentTrapV010(max_steps=10, seed=42)
        obs = env.reset(seed=42)

        assert "feasible_actions" in obs
        assert "action_inventory" in obs
        assert len(obs["action_inventory"]) == 10  # 10 actions per spec
        assert len(obs["feasible_actions"]) > 0

    def test_feasibility_oracle(self):
        """Test explicit feasibility oracle"""
        env = CommitmentTrapV010(max_steps=10, seed=42)
        env.reset(seed=42)

        feasible = env.feasible_actions()
        assert isinstance(feasible, list)
        assert all(isinstance(a, str) for a in feasible)

        # Test that at least one temptation and one safe action are feasible
        temptations = list(CommitmentTrapV010.TEMPTATIONS.keys())
        safe = CommitmentTrapV010.SAFE_ACTIONS

        has_temptation = any(a in feasible for a in temptations)
        has_safe = any(a in feasible for a in safe)

        assert has_temptation, "Should have at least one feasible temptation"
        assert has_safe, "Should have at least one feasible safe action"

    def test_determinism(self):
        """Test environment determinism with same seed"""
        env1 = CommitmentTrapV010(max_steps=5, seed=123)
        env2 = CommitmentTrapV010(max_steps=5, seed=123)

        obs1 = env1.reset(seed=123)
        obs2 = env2.reset(seed=123)

        assert obs1["feasible_actions"] == obs2["feasible_actions"]


class TestJAFSchema:
    """Test JAF-0.1 schema validation"""

    def test_valid_jaf(self):
        """Test that valid JAF passes validation"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="DEFECT",
                relation="VIOLATES",
                target_pref_id="P_NO_DEFECT",
                expected_constraint_effect="FORBID_CANDIDATE"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=["DEFECT"],
                forbid_mode="EXPLICIT_LIST",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            nonce="test123"
        )

        # Should not raise
        jaf.validate()

    def test_invalid_version(self):
        """Test that wrong version fails validation"""
        jaf = JAF010(
            artifact_version="JAF-0.0",  # Wrong version
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="DEFECT",
                relation="SATISFIES",
                target_pref_id=None,
                expected_constraint_effect="NO_CONSTRAINT"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=[],
                forbid_mode="NONE",
                constraint_reason_code="R_POLICY_GUARD"
            ),
            nonce="test123"
        )

        with pytest.raises(ValueError, match="artifact_version"):
            jaf.validate()

    def test_continuity_mismatch(self):
        """Test that continuity_counter must equal step"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=5,
            identity=Identity(agent_id="TEST", continuity_counter=3),  # Mismatch
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="WAIT",
                relation="SATISFIES",
                target_pref_id=None,
                expected_constraint_effect="NO_CONSTRAINT"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=[],
                forbid_mode="NONE",
                constraint_reason_code="R_POLICY_GUARD"
            ),
            nonce="test123"
        )

        with pytest.raises(ValueError, match="continuity_counter must equal step"):
            jaf.validate()

    def test_violates_requires_target_pref(self):
        """Test that VIOLATES relation requires target_pref_id"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="DEFECT",
                relation="VIOLATES",
                target_pref_id=None,  # Missing target
                expected_constraint_effect="FORBID_CANDIDATE"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=["DEFECT"],
                forbid_mode="EXPLICIT_LIST",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            nonce="test123"
        )

        with pytest.raises(ValueError, match="target_pref_id required"):
            jaf.validate()


class TestJCOMP:
    """Test JCOMP-0.1 compiler"""

    def test_determinism(self):
        """Test that JCOMP is deterministic"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="DEFECT",
                relation="VIOLATES",
                target_pref_id="P_NO_DEFECT",
                expected_constraint_effect="FORBID_CANDIDATE"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=["DEFECT"],
                forbid_mode="EXPLICIT_LIST",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            nonce="test123"
        )

        actions = ["WAIT", "COOPERATE", "DEFECT"]
        feasible = {"WAIT", "COOPERATE", "DEFECT"}

        # Compile twice
        c1 = JCOMP010.compile(jaf, actions, feasible)
        c2 = JCOMP010.compile(jaf, actions, feasible)

        assert c1.artifact_digest == c2.artifact_digest
        assert c1.forbidden_action_ids == c2.forbidden_action_ids
        assert c1.mask == c2.mask

    def test_forbid_mode_none(self):
        """Test NONE forbid mode produces empty forbid set"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="WAIT",
                relation="SATISFIES",
                target_pref_id=None,
                expected_constraint_effect="NO_CONSTRAINT"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=[],
                forbid_mode="NONE",
                constraint_reason_code="R_POLICY_GUARD"
            ),
            nonce="test123"
        )

        actions = ["WAIT", "COOPERATE", "DEFECT"]
        feasible = {"WAIT", "COOPERATE", "DEFECT"}

        c = JCOMP010.compile(jaf, actions, feasible)

        assert c.compile_ok
        assert len(c.forbidden_action_ids) == 0
        assert all(v == "ALLOW" for v in c.mask.values())

    def test_violation_enforcement_rule(self):
        """Test that VIOLATES requires candidate in forbid set"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="DEFECT",
                relation="VIOLATES",
                target_pref_id="P_NO_DEFECT",
                expected_constraint_effect="FORBID_CANDIDATE"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=[],  # Empty, but claims VIOLATES
                forbid_mode="NONE",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            nonce="test123"
        )

        actions = ["WAIT", "DEFECT"]
        feasible = {"WAIT", "DEFECT"}

        c = JCOMP010.compile(jaf, actions, feasible)

        assert not c.compile_ok
        assert c.error_code == "E_VIOLATION_BUT_NOT_FORBIDDEN"

    def test_nontrivial_accounting(self):
        """Test non-trivial constraint detection"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="DEFECT",
                relation="VIOLATES",
                target_pref_id="P_NO_DEFECT",
                expected_constraint_effect="FORBID_CANDIDATE"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=["DEFECT"],
                forbid_mode="EXPLICIT_LIST",
                constraint_reason_code="R_PREF_VIOLATION"
            ),
            nonce="test123"
        )

        actions = ["WAIT", "COOPERATE", "DEFECT"]
        feasible = {"WAIT", "COOPERATE", "DEFECT"}  # DEFECT is feasible

        c = JCOMP010.compile(jaf, actions, feasible)

        assert c.compile_ok
        assert "DEFECT" in c.nontrivial_forbidden_action_ids
        assert len(c.nontrivial_forbidden_action_ids) > 0


class TestSelectorBlindness:
    """Test that action selector is blind to semantics"""

    def test_selector_signature(self):
        """Test selector function signature excludes JAF/normative state"""
        selector = BlindActionSelector(seed=42)

        # Check method signature - should only accept feasible actions and mask
        import inspect
        sig = inspect.signature(selector.select_action)
        params = list(sig.parameters.keys())

        # Should have: feasible_actions, action_mask, env_obs
        assert "feasible_actions" in params
        assert "action_mask" in params

        # Should NOT have: jaf, normative_state, beliefs, preferences
        assert "jaf" not in params
        assert "normative_state" not in params
        assert "beliefs" not in params
        assert "preferences" not in params

    def test_selector_respects_mask(self):
        """Test that selector respects action mask"""
        selector = BlindActionSelector(seed=42)

        feasible = ["WAIT", "COOPERATE", "DEFECT"]
        mask = {
            "WAIT": "ALLOW",
            "COOPERATE": "ALLOW",
            "DEFECT": "FORBID"  # Forbidden
        }

        # Select multiple times
        for _ in range(10):
            action = selector.select_action(feasible, mask)
            assert action != "DEFECT", "Selector violated mask by selecting forbidden action"


class TestNormativeState:
    """Test normative state and registries"""

    def test_fixed_registries(self):
        """Test that registries are fixed (no dynamic ID creation)"""
        belief_ids = BeliefRegistryV010.get_belief_ids()
        pref_ids = PreferenceRegistryV010.get_pref_ids()

        # Should be non-empty
        assert len(belief_ids) > 0
        assert len(pref_ids) > 0

        # Should be fixed (check that we can't easily add new ones)
        with pytest.raises(KeyError):
            BeliefRegistryV010.get_belief("B_NONEXISTENT")

        with pytest.raises(KeyError):
            PreferenceRegistryV010.get_preference("P_NONEXISTENT")

    def test_belief_values_mutable(self):
        """Test that belief values can change (but not IDs)"""
        state = NormativeState()

        initial_ids = state.get_belief_ids()

        # Should be able to update status
        from v010.state.normative import TruthStatus
        state.update_belief_status("B_DOOR_A_LOCKED", TruthStatus.FALSE)

        # IDs should remain the same
        assert state.get_belief_ids() == initial_ids


class TestJustificationGenerator:
    """Test justification generator"""

    def test_generator_receives_feasibility(self):
        """Test that generator receives feasibility list"""
        generator = DeterministicJustificationGenerator(seed=42)
        state = NormativeState()

        feasible = ["WAIT", "COOPERATE", "DEFECT"]

        jaf = generator.generate(state, feasible, step=0)

        # Candidate should be from feasible set
        assert jaf.action_claim.candidate_action_id in feasible

    def test_generator_produces_valid_jaf(self):
        """Test that generator produces valid JAF"""
        generator = DeterministicJustificationGenerator(seed=42)
        state = NormativeState()

        feasible = ["WAIT", "COOPERATE", "DEFECT"]

        jaf = generator.generate(state, feasible, step=5)

        # Should be valid
        jaf.validate()  # Should not raise

        # Should have correct step
        assert jaf.step == 5
        assert jaf.identity.continuity_counter == 5


class TestGridlockDetection:
    """Test gridlock detection"""

    def test_gridlock_when_all_forbidden(self):
        """Test gridlock detection when all feasible actions forbidden"""
        jaf = JAF010(
            artifact_version="JAF-0.1",
            step=0,
            identity=Identity(agent_id="TEST", continuity_counter=0),
            references=References(
                belief_ids=["B_DOOR_A_LOCKED"],
                pref_ids=["P_NO_DEFECT"]
            ),
            action_claim=ActionClaim(
                candidate_action_id="WAIT",
                relation="SATISFIES",
                target_pref_id=None,
                expected_constraint_effect="FORBID_ALTERNATIVES"
            ),
            relevance=Relevance(required_belief_ids=["B_DOOR_A_LOCKED"]),
            compiler_hints=CompilerHints(
                forbid_action_ids=["WAIT", "COOPERATE"],  # Forbid all feasible
                forbid_mode="EXPLICIT_LIST",
                constraint_reason_code="R_POLICY_GUARD"
            ),
            nonce="test123"
        )

        actions = ["WAIT", "COOPERATE"]
        feasible = {"WAIT", "COOPERATE"}

        c = JCOMP010.compile(jaf, actions, feasible)

        assert c.compile_ok

        # Check for gridlock
        feasible_post_mask = [a for a in feasible if c.mask[a] == "ALLOW"]
        assert len(feasible_post_mask) == 0  # Gridlock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
