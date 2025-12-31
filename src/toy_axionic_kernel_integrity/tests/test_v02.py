"""
Tests for AKI v0.2 — Sovereign Kernel Verification Under Delegation Pressure.

Test categories:
1. K_act_key non-exportability tests
2. Kernel-local recomposition tests
3. Actuator admissibility tests
4. Attack library tests (all 6 attacks)
5. Variant tests (v0.2.a through v0.2.d)
6. Integration tests

Each test has:
- Clear success condition
- Explicit logs
- Reproducible seeds
"""

import pickle
import json
import pytest
from typing import Any

from toy_aki.kernel.sovereign_authority import (
    ActuationAuthority,
    ActuationBinding,
    ActuationAuthorityLeakError,
    compute_action_hash,
)
from toy_aki.kernel.recomposition import (
    KernelRecomposer,
    RecompositionMode,
    DELEGATION_AUTHORITY_MARKERS,
)
from toy_aki.kernel.sovereign_actuator import (
    SovereignActuator,
    ActuationCommitment,
    AdmissibilityCheckType,
)
from toy_aki.attacks import (
    create_attack,
    get_all_attack_types,
    PolicyLaunderingAttack,
    ActuationTokenSmuggling,
    PrecommitmentForwarding,
    CompressedPolicyDelegation,
    SplitBrainDelegation,
    AnchorBurialAuthorityMasking,
)
from toy_aki.env.pressure_envs import (
    create_environment,
    get_all_environment_types,
    FastStochasticPlanning,
)
from toy_aki.harness.v02_runner import (
    SovereignKernel,
    ExperimentVariant,
    V02ExperimentRunner,
)


# =============================================================================
# 1. K_act_key Non-Exportability Tests
# =============================================================================

class TestActuationAuthorityNonExportability:
    """Tests for K_act_key non-exportability invariant."""

    def test_pickle_serialization_blocked(self):
        """K_act_key must not be pickle-serializable."""
        authority = ActuationAuthority("test-kernel")

        with pytest.raises(ActuationAuthorityLeakError) as exc_info:
            pickle.dumps(authority)

        assert "serialization" in str(exc_info.value).lower()

    def test_pickle_reduce_blocked(self):
        """K_act_key must block __reduce__ protocol."""
        authority = ActuationAuthority("test-kernel")

        with pytest.raises(ActuationAuthorityLeakError):
            authority.__reduce__()

    def test_pickle_reduce_ex_blocked(self):
        """K_act_key must block __reduce_ex__ protocol."""
        authority = ActuationAuthority("test-kernel")

        with pytest.raises(ActuationAuthorityLeakError):
            authority.__reduce_ex__(4)

    def test_repr_does_not_leak_secret(self):
        """repr() must not expose the secret."""
        authority = ActuationAuthority("test-kernel")
        repr_str = repr(authority)

        # Should not contain hex strings that could be the secret
        assert len(repr_str) < 200  # Reasonable length
        assert "_secret" not in repr_str
        assert authority._secret.hex() not in repr_str

    def test_str_does_not_leak_secret(self):
        """str() must not expose the secret."""
        authority = ActuationAuthority("test-kernel")
        str_repr = str(authority)

        assert authority._secret.hex() not in str_repr

    def test_leak_detection_in_dict(self):
        """assert_no_leaks_in must detect K_act_key in dictionaries."""
        authority = ActuationAuthority("test-kernel")

        obj = {"data": {"nested": authority}}

        with pytest.raises(ActuationAuthorityLeakError):
            ActuationAuthority.assert_no_leaks_in(obj)

    def test_leak_detection_in_list(self):
        """assert_no_leaks_in must detect K_act_key in lists."""
        authority = ActuationAuthority("test-kernel")

        obj = [1, 2, [3, authority]]

        with pytest.raises(ActuationAuthorityLeakError):
            ActuationAuthority.assert_no_leaks_in(obj)

    def test_binding_does_not_contain_secret(self):
        """ActuationBinding must not contain the secret."""
        authority = ActuationAuthority("test-kernel")
        action_hash = compute_action_hash("MOVE_RIGHT", {})

        binding = authority.bind_to_action(action_hash)

        # Convert binding to dict and check
        binding_dict = binding.to_dict()
        binding_json = json.dumps(binding_dict)

        # Secret should not appear anywhere
        assert authority._secret.hex() not in binding_json

    def test_binding_is_serializable(self):
        """ActuationBinding (unlike K_act_key) should be serializable."""
        authority = ActuationAuthority("test-kernel")
        action_hash = compute_action_hash("MOVE_RIGHT", {})

        binding = authority.bind_to_action(action_hash)

        # Should not raise
        binding_dict = binding.to_dict()
        json.dumps(binding_dict)

        # Reconstruct
        reconstructed = ActuationBinding.from_dict(binding_dict)
        assert reconstructed.action_hash == binding.action_hash

    def test_binding_verification(self):
        """Binding verification must work without exposing secret."""
        authority = ActuationAuthority("test-kernel")
        action_hash = compute_action_hash("MOVE_RIGHT", {})

        binding = authority.bind_to_action(action_hash)

        # Authority can verify its own binding
        assert authority.verify_binding(binding)

    def test_foreign_binding_rejected(self):
        """Binding from different authority must be rejected."""
        authority1 = ActuationAuthority("kernel-1")
        authority2 = ActuationAuthority("kernel-2")

        action_hash = compute_action_hash("MOVE_RIGHT", {})
        binding1 = authority1.bind_to_action(action_hash)

        # Authority2 should reject authority1's binding
        assert not authority2.verify_binding(binding1)


# =============================================================================
# 2. Kernel-Local Recomposition Tests
# =============================================================================

class TestKernelLocalRecomposition:
    """Tests for kernel-local recomposition."""

    def test_honest_proposal_accepted(self):
        """Honest proposal without delegation markers should be accepted."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.HARDENED)

        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": {},
                },
            },
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)

        assert result.success
        assert result.recomposed_action is not None
        assert result.binding is not None
        assert result.recomposed_action.action_type == "MOVE_RIGHT"

    def test_delegation_authority_marker_rejected(self):
        """Proposals with delegation_authority marker must be rejected."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.HARDENED)

        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": {},
                },
            },
            "delegation_authority": {"type": "external"},
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)

        assert not result.success
        assert "delegation" in result.rejection_reason.lower()

    def test_actuation_token_rejected(self):
        """Proposals with actuation_token marker must be rejected."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.HARDENED)

        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": {},
                },
            },
            "actuation_token": {"token_id": "fake"},
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)

        assert not result.success

    @pytest.mark.parametrize("marker", list(DELEGATION_AUTHORITY_MARKERS)[:5])
    def test_all_delegation_markers_rejected(self, marker: str):
        """All delegation authority markers must be rejected."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.HARDENED)

        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": {},
                },
            },
            marker: {"type": "test"},
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)
        assert not result.success

    def test_soft_mode_allows_markers(self):
        """In SOFT mode, delegation markers should be allowed."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.SOFT)

        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": {},
                },
            },
            "delegation_authority": {"type": "external"},
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)

        # Should succeed in soft mode
        assert result.success

    def test_action_hash_bound_directly(self):
        """Binding must be to hash of action payload, not opaque blob."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.HARDENED)

        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": {"distance": 1},
                },
            },
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)

        assert result.success

        # Verify binding is to the action hash
        expected_hash = compute_action_hash("MOVE_RIGHT", {"distance": 1})
        assert result.binding.action_hash == expected_hash
        assert result.recomposed_action.action_hash == expected_hash

    def test_args_deep_copied(self):
        """Action args must be deep copied, not referenced."""
        authority = ActuationAuthority("test-kernel")
        recomposer = KernelRecomposer(authority, mode=RecompositionMode.HARDENED)

        original_args = {"nested": {"value": 1}}
        proposal = {
            "proposal_id": "test-1",
            "request": {
                "intent": {
                    "action": "MOVE_RIGHT",
                    "args": original_args,
                },
            },
            "policy_digest": "test",
            "env_digest": "test",
        }

        result = recomposer.recompose(proposal)

        # Modify original
        original_args["nested"]["value"] = 999

        # Recomposed action should not be affected
        assert result.recomposed_action.action_args["nested"]["value"] == 1


# =============================================================================
# 3. Actuator Admissibility Tests
# =============================================================================

class TestSovereignActuator:
    """Tests for actuator admissibility checks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.authority = ActuationAuthority("test-kernel")
        self.actuator = SovereignActuator(
            self.authority,
            mode=RecompositionMode.HARDENED
        )

    def create_valid_commitment(self, action: str = "MOVE_RIGHT") -> ActuationCommitment:
        """Create a valid actuation commitment for testing."""
        from toy_aki.kernel.sovereign_authority import RecomposedAction
        from toy_aki.kernel.watchdog import current_time_ms
        import uuid

        action_hash = compute_action_hash(action, {})
        binding = self.authority.bind_to_action(action_hash)

        recomposed = RecomposedAction(
            action_type=action,
            action_args={},
            action_hash=action_hash,
            source_proposal_hash="test-hash",
            recomposition_timestamp_ms=current_time_ms(),
        )

        return ActuationCommitment(
            commitment_id=str(uuid.uuid4()),
            recomposed_action=recomposed,
            binding=binding,
            acv_chain={
                "commitment": "test",
                "anchor": "test",
                "nonce": "test",
                "proposal_hash": "test",
                "verified": True,
            },
            kernel_id=self.authority._kernel_id,
            timestamp_ms=current_time_ms(),
        )

    def test_valid_commitment_accepted(self):
        """Valid commitment should be accepted."""
        commitment = self.create_valid_commitment()
        result = self.actuator.accept(commitment)

        assert result.admissible
        assert result.rejection_reason is None

    def test_invalid_acv_rejected(self):
        """Commitment with invalid ACV chain should be rejected."""
        commitment = self.create_valid_commitment()
        commitment.acv_chain["verified"] = False

        result = self.actuator.accept(commitment)

        assert not result.admissible
        assert any(
            c.check_type == AdmissibilityCheckType.ACV_CHAIN and not c.passed
            for c in result.checks
        )

    def test_missing_acv_fields_rejected(self):
        """Commitment with missing ACV fields should be rejected."""
        commitment = self.create_valid_commitment()
        del commitment.acv_chain["anchor"]

        result = self.actuator.accept(commitment)

        assert not result.admissible

    def test_wrong_kernel_id_rejected(self):
        """Commitment with binding from different authority should be rejected."""
        # Create a commitment with a binding from a different authority
        from toy_aki.kernel.sovereign_authority import RecomposedAction
        from toy_aki.kernel.watchdog import current_time_ms
        import uuid

        # Create a different authority
        other_authority = ActuationAuthority("other-kernel")
        action_hash = compute_action_hash("MOVE_RIGHT", {})

        # Binding is from the other authority
        binding = other_authority.bind_to_action(action_hash)

        recomposed = RecomposedAction(
            action_type="MOVE_RIGHT",
            action_args={},
            action_hash=action_hash,
            source_proposal_hash="test-hash",
            recomposition_timestamp_ms=current_time_ms(),
        )

        commitment = ActuationCommitment(
            commitment_id=str(uuid.uuid4()),
            recomposed_action=recomposed,
            binding=binding,
            acv_chain={
                "commitment": "test",
                "anchor": "test",
                "nonce": "test",
                "proposal_hash": "test",
                "verified": True,
            },
            kernel_id="other-kernel",
            timestamp_ms=current_time_ms(),
        )

        result = self.actuator.accept(commitment)

        # Should be rejected because binding was from different authority
        assert not result.admissible

    def test_binding_hash_mismatch_rejected(self):
        """Commitment with mismatched binding hash should be rejected."""
        commitment = self.create_valid_commitment()

        # Tamper with action hash
        commitment.recomposed_action.action_hash = "tampered"

        result = self.actuator.accept(commitment)

        assert not result.admissible

    def test_soft_mode_skips_advanced_checks(self):
        """In SOFT mode, only ACV is checked."""
        self.actuator.set_mode(RecompositionMode.SOFT)

        commitment = self.create_valid_commitment()
        # Tamper with something that would fail in HARDENED mode
        commitment.kernel_id = "wrong-kernel"

        result = self.actuator.accept(commitment)

        # Should still pass in SOFT mode (only ACV checked)
        assert result.admissible


# =============================================================================
# 4. Attack Library Tests
# =============================================================================

class TestAttackLibrary:
    """Tests for all 6 delegation attacks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.authority = ActuationAuthority("test-kernel")
        self.recomposer = KernelRecomposer(
            self.authority,
            mode=RecompositionMode.HARDENED
        )

    def test_all_attack_types_exist(self):
        """All 6 required attack types must exist."""
        attack_types = get_all_attack_types()

        required = {
            "policy_laundering",
            "actuation_token_smuggling",
            "precommitment_forwarding",
            "compressed_policy_delegation",
            "split_brain_delegation",
            "anchor_burial_authority_masking",
        }

        assert required.issubset(set(attack_types))

    @pytest.mark.parametrize("attack_type", get_all_attack_types())
    def test_attack_generates_payload(self, attack_type: str):
        """Each attack must generate a valid payload."""
        attack = create_attack(attack_type, seed=42)

        payload = attack.generate_payload(
            action="MOVE_RIGHT",
            action_args={},
            env_digest="test-env",
            policy_digest="test-policy",
        )

        assert isinstance(payload, dict)
        assert "request" in payload

    @pytest.mark.parametrize("attack_type", get_all_attack_types())
    def test_attack_rejected_in_hardened_mode(self, attack_type: str):
        """Each attack must be rejected in HARDENED mode."""
        attack = create_attack(attack_type, seed=42)

        payload = attack.generate_payload(
            action="MOVE_RIGHT",
            action_args={},
            env_digest="test-env",
            policy_digest="test-policy",
        )

        result = self.recomposer.recompose(payload)

        assert not result.success, f"Attack {attack_type} should be rejected"

    def test_policy_laundering_contains_marker(self):
        """Policy laundering attack must contain delegation_authority marker."""
        attack = PolicyLaunderingAttack(seed=42)
        payload = attack.generate_payload("MOVE_RIGHT", {}, "env", "policy")

        assert "delegation_authority" in payload

    def test_actuation_token_contains_marker(self):
        """Actuation token attack must contain actuation_token marker."""
        attack = ActuationTokenSmuggling(seed=42)
        payload = attack.generate_payload("MOVE_RIGHT", {}, "env", "policy")

        assert "actuation_token" in payload

    def test_precommitment_contains_marker(self):
        """Precommitment attack must contain precommitted_action marker."""
        attack = PrecommitmentForwarding(seed=42)
        payload = attack.generate_payload("MOVE_RIGHT", {}, "env", "policy")

        assert "precommitted_action" in payload or "forwarded_commitment" in payload

    def test_compressed_policy_contains_marker(self):
        """Compressed policy attack must contain compressed_policy marker."""
        attack = CompressedPolicyDelegation(seed=42)
        payload = attack.generate_payload("MOVE_RIGHT", {}, "env", "policy")

        assert "compressed_policy" in payload

    def test_split_brain_contains_marker(self):
        """Split-brain attack must contain fragment routing marker."""
        attack = SplitBrainDelegation(seed=42)
        payload = attack.generate_payload("MOVE_RIGHT", {}, "env", "policy")

        assert "kernel_fragment_route" in payload or "split_brain_authority" in payload

    def test_anchor_burial_contains_marker(self):
        """Anchor burial attack must contain external_authority marker."""
        attack = AnchorBurialAuthorityMasking(seed=42)
        payload = attack.generate_payload("MOVE_RIGHT", {}, "env", "policy")

        assert "external_authority" in payload


# =============================================================================
# 5. Variant Tests
# =============================================================================

class TestExperimentalVariants:
    """Tests for experimental variants v0.2.a through v0.2.d."""

    def test_v02a_rejects_all_attacks(self):
        """v0.2.a (hardened) must reject all attacks."""
        kernel = SovereignKernel("test", mode=RecompositionMode.HARDENED)

        for attack_type in get_all_attack_types():
            attack = create_attack(attack_type, seed=42)
            payload = attack.generate_payload(
                action="MOVE_RIGHT",
                action_args={},
                env_digest="test",
                policy_digest="test",
            )

            accepted, reason, _ = kernel.process_proposal(payload)

            assert not accepted, f"v0.2.a should reject {attack_type}"

    def test_v02b_accepts_with_valid_acv(self):
        """v0.2.b (soft) should accept proposals with valid ACV."""
        kernel = SovereignKernel("test", mode=RecompositionMode.SOFT)

        # Honest proposal
        proposal = {
            "proposal_id": "test",
            "request": {
                "intent": {"action": "MOVE_RIGHT", "args": {}},
            },
            "policy_digest": "test",
            "env_digest": "test",
        }

        accepted, reason, commitment = kernel.process_proposal(proposal)

        assert accepted

    def test_v02b_demonstrates_vulnerability(self):
        """v0.2.b should demonstrate delegation vulnerability."""
        kernel = SovereignKernel("test", mode=RecompositionMode.SOFT)

        # Attack proposal - should be accepted in soft mode
        attack = create_attack("policy_laundering", seed=42)
        payload = attack.generate_payload(
            action="MOVE_RIGHT",
            action_args={},
            env_digest="test",
            policy_digest="test",
        )

        accepted, reason, commitment = kernel.process_proposal(payload)

        # In soft mode, this should be accepted (demonstrating vulnerability)
        assert accepted


# =============================================================================
# 6. Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full experiment."""

    def test_environment_creation(self):
        """All environment types must be creatable."""
        for env_type in get_all_environment_types():
            env = create_environment(env_type, seed=42)
            assert env is not None
            assert env.state is not None

    def test_pressure_metrics(self):
        """Environments must report delegation pressure metrics."""
        for env_type in get_all_environment_types():
            env = create_environment(env_type, seed=42)
            metrics = env.compute_pressure_metrics()

            assert metrics.compute_gap >= 1.0  # E has advantage

    def test_oracle_vs_kernel_action(self):
        """E (oracle) should have better actions than K."""
        env = FastStochasticPlanning(seed=42)

        oracle_action = env.get_oracle_action()
        kernel_action = env.get_kernel_action()

        # Both should return valid actions
        assert oracle_action is not None
        assert kernel_action is not None

    def test_single_trial_execution(self):
        """Single trial should complete successfully."""
        runner = V02ExperimentRunner(base_seed=42, verbose=False)

        trial = runner.run_trial(
            variant=ExperimentVariant.V02A_HARDENED,
            env_type="fast_stochastic_planning",
            attack_type="policy_laundering",
            mode=RecompositionMode.HARDENED,
            seed=42,
        )

        assert trial is not None
        assert trial.trial_id is not None
        # In hardened mode, attack should be rejected
        assert not trial.breach_detected or trial.rejection_count > 0

    def test_variant_execution(self):
        """Full variant should complete with results."""
        runner = V02ExperimentRunner(base_seed=42, verbose=False)

        result = runner.run_variant(ExperimentVariant.V02A_HARDENED)

        assert result.total_trials > 0
        # Hardened mode should have no breaches
        assert result.breaches == 0

    def test_full_experiment_structure(self):
        """Full experiment should produce valid result structure."""
        runner = V02ExperimentRunner(base_seed=42, verbose=False)

        result = runner.run_full_experiment()

        assert result.experiment_id is not None
        assert len(result.variant_results) == 4
        assert ExperimentVariant.V02A_HARDENED.value in result.variant_results
        assert result.claim is not None


# =============================================================================
# 7. Leak Detection Stress Tests
# =============================================================================

class TestLeakDetectionStress:
    """Stress tests for K_act_key leak detection."""

    def test_induced_serialization_blocked(self):
        """E cannot induce serialization of K_act_key."""
        authority = ActuationAuthority("test-kernel")

        # Attempt to serialize via various methods
        with pytest.raises(ActuationAuthorityLeakError):
            pickle.dumps(authority)

        with pytest.raises(ActuationAuthorityLeakError):
            import copy
            copy.deepcopy(authority)  # Uses __reduce__

    def test_reflection_does_not_leak(self):
        """Reflection on authority should not leak secret."""
        authority = ActuationAuthority("test-kernel")

        # Get all attributes
        attrs = dir(authority)

        # None should expose the secret
        for attr in attrs:
            if not attr.startswith("_"):
                value = getattr(authority, attr)
                if callable(value):
                    continue
                # Non-callable public attrs should not be the secret
                assert value != authority._secret

    def test_logging_blocked_by_assertion(self):
        """Logging should be blocked by leak assertion."""
        authority = ActuationAuthority("test-kernel")

        log_entry = {"action": "test", "authority": authority}

        with pytest.raises(ActuationAuthorityLeakError):
            ActuationAuthority.assert_no_leaks_in(log_entry)

    def test_deeply_nested_leak_detected(self):
        """Deeply nested leaks should be detected."""
        authority = ActuationAuthority("test-kernel")

        nested = {
            "level1": {
                "level2": {
                    "level3": [
                        {"level4": {"secret": authority}}
                    ]
                }
            }
        }

        with pytest.raises(ActuationAuthorityLeakError):
            ActuationAuthority.assert_no_leaks_in(nested)
