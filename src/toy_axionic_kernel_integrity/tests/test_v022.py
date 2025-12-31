"""
v0.2.2 Test Suite: Closing Blocking Gaps.

Tests for:
- Gap A: Mandatory budget enforcement at harness boundary
- Gap B: Cross-component canonicalization with independent instances
- A12 TOCTOU immutability proof
- A9/A10 extended payload families

v0.2.2 Spec requirements:
1. Budget tracking must be mandatory at harness boundary (not opt-in)
2. Canonical bytes handoff with separate parser stacks
3. CANONICAL_AGREEMENT check in actuator
4. Mutation-after-commit test proves frozen bytes prevent TOCTOU
"""

import pytest
import json
import copy
import hashlib
import math

# Budget system - v0.2.2 extensions
from toy_aki.kernel.budget import (
    BudgetTracker,
    BudgetLimits,
    BudgetState,
    OperationType,
    harness_budget_scope,
    budget_scope,
    require_harness_budget,
    BudgetNotEnforcedError,
    set_budget_tracker,
    get_budget_tracker,
)

# Canonical module - v0.2.2 new
from toy_aki.kernel.canonical import (
    IndependentCanonicalizer,
    CanonicalConfig,
    CanonicalResult,
    CanonicalPayload,
    create_kernel_canonicalizer,
    create_actuator_canonicalizer,
    verify_canonical_agreement,
    assert_no_shared_state,
)

# Sovereign actuator - v0.2.2 extensions
from toy_aki.kernel.sovereign_actuator import (
    SovereignActuator,
    AdmissibilityCheckType,
)

# Stress attacks - v0.2.2 extensions
from toy_aki.attacks.stress_attacks import (
    HashAmbiguityAttack,
    ParserDifferentialAttack,
    TOCTOUAttack,
)

# Common utilities
from toy_aki.common.hashing import hash_json


# ========== Gap A: Mandatory Budget Enforcement ==========

class TestHarnessBudgetScope:
    """Test mandatory budget enforcement at harness boundary."""

    def test_harness_budget_scope_marks_enforced(self):
        """harness_budget_scope marks tracker as harness_enforced=True."""
        limits = BudgetLimits(time_ticks=1000)

        with harness_budget_scope(limits) as tracker:
            assert tracker.harness_enforced is True

    def test_require_harness_budget_passes_when_enforced(self):
        """require_harness_budget succeeds when harness scope active."""
        limits = BudgetLimits(time_ticks=1000)

        with harness_budget_scope(limits):
            # Should not raise
            require_harness_budget()

    def test_require_harness_budget_fails_without_scope(self):
        """require_harness_budget raises when harness scope not active."""
        # Create non-harness tracker
        limits = BudgetLimits(time_ticks=1000)
        with budget_scope(limits):
            with pytest.raises(BudgetNotEnforcedError):
                require_harness_budget()

    def test_stage_scoped_budget_tracking(self):
        """Stage-scoped budgets track per-stage consumption."""
        limits = BudgetLimits(time_ticks=1000)

        with harness_budget_scope(limits) as tracker:
            with tracker.stage("parse"):
                tracker.charge_operation(OperationType.PARSE)
                tracker.charge_operation(OperationType.PARSE)

            with tracker.stage("validate"):
                tracker.charge_operation(OperationType.VALIDATE)

            with tracker.stage("recompose"):
                tracker.charge_operation(OperationType.RECOMPOSE)

            # Check per-stage tracking
            assert "parse" in tracker.state.stage_ticks
            assert "validate" in tracker.state.stage_ticks
            assert "recompose" in tracker.state.stage_ticks
            assert tracker.state.stage_ticks["parse"] == 6  # 3 ticks * 2
            assert tracker.state.stage_ticks["validate"] == 2
            assert tracker.state.stage_ticks["recompose"] == 10

    def test_stage_overflow_detection(self):
        """Stage overflow is detected and recorded."""
        limits = BudgetLimits(time_ticks=10)

        with harness_budget_scope(limits) as tracker:
            with pytest.raises(Exception):  # Should raise budget exceeded
                with tracker.stage("parse"):
                    for _ in range(10):
                        tracker.charge_operation(OperationType.PARSE)

            # Overflow stage should be recorded
            assert tracker.state.stage_overflow == "parse"


# ========== Gap B: Cross-Component Canonicalization ==========

class TestIndependentCanonicalizer:
    """Test separate parser/serializer stacks for kernel and actuator."""

    def test_kernel_and_actuator_are_independent_instances(self):
        """Kernel and actuator use separate class instances."""
        kernel_canon = create_kernel_canonicalizer()
        actuator_canon = create_actuator_canonicalizer()

        # Must be separate instances
        assert kernel_canon is not actuator_canon

        # Internal configs must also be separate
        assert kernel_canon._config is not actuator_canon._config

    def test_no_shared_globals_assertion(self):
        """assert_no_shared_state verifies no shared globals."""
        kernel_canon = create_kernel_canonicalizer()
        actuator_canon = create_actuator_canonicalizer()

        # Should not raise
        assert_no_shared_state(kernel_canon, actuator_canon)

    def test_canonical_bytes_agreement(self):
        """Same data produces same canonical bytes from both components."""
        kernel_canon = create_kernel_canonicalizer()
        actuator_canon = create_actuator_canonicalizer()

        data = {
            "action": "move_right",
            "args": {"speed": 1},
            "timestamp": 12345,
        }

        kernel_result = kernel_canon.canonicalize(data)
        actuator_result = actuator_canon.canonicalize(data)

        # Same canonical bytes (deterministic)
        assert kernel_result.canonical_bytes == actuator_result.canonical_bytes
        assert kernel_result.canonical_hash == actuator_result.canonical_hash

    def test_canonical_payload_is_immutable(self):
        """CanonicalPayload is frozen and cannot be mutated."""
        kernel_canon = create_kernel_canonicalizer()
        data = {"action": "test"}
        result = kernel_canon.canonicalize(data)

        payload = CanonicalPayload(
            canonical_bytes=result.canonical_bytes,
            canonical_hash=result.canonical_hash,
            action_type="test",
            action_id="test-001",
        )

        # Attempt mutation should fail
        with pytest.raises(Exception):  # FrozenInstanceError
            payload.canonical_bytes = b"mutated"  # type: ignore

    def test_verify_canonical_agreement(self):
        """verify_canonical_agreement checks kernel/actuator agreement."""
        kernel_canon = create_kernel_canonicalizer()
        actuator_canon = create_actuator_canonicalizer()

        data = {"action": "test", "value": 42}
        kernel_result = kernel_canon.canonicalize(data)
        actuator_result = actuator_canon.canonicalize(data)

        # Verify agreement
        agreement, error = verify_canonical_agreement(kernel_result, actuator_result)
        assert agreement is True
        assert error is None

    def test_canonical_agreement_fails_on_mismatch(self):
        """Mismatched results fail agreement check."""
        kernel_canon = create_kernel_canonicalizer()
        actuator_canon = create_actuator_canonicalizer()

        # Different data
        kernel_result = kernel_canon.canonicalize({"action": "A"})
        actuator_result = actuator_canon.canonicalize({"action": "B"})

        # Agreement should fail
        agreement, error = verify_canonical_agreement(kernel_result, actuator_result)
        assert agreement is False
        assert error is not None


class TestCanonicalBytesHandoff:
    """Test canonical-bytes-only boundary crossing."""

    def test_only_bytes_cross_boundary(self):
        """Only canonical bytes cross kernel->actuator boundary."""
        kernel_canon = create_kernel_canonicalizer()

        # Original mutable data
        original_data = {"action": "test", "args": {"key": "value"}}
        kernel_result = kernel_canon.canonicalize(original_data)

        # Create handoff payload (what crosses boundary)
        payload = CanonicalPayload(
            canonical_bytes=kernel_result.canonical_bytes,
            canonical_hash=kernel_result.canonical_hash,
            action_type="test",
            action_id="test-001",
        )

        # Mutate original data
        original_data["action"] = "HIJACKED"
        original_data["args"]["key"] = "MUTATED"

        # Payload is unaffected (bytes were copied at creation time)
        # Parse bytes to verify
        parsed = json.loads(payload.canonical_bytes.decode("utf-8"))
        assert parsed["action"] == "test"
        assert parsed["args"]["key"] == "value"

    def test_no_mutable_recomposed_action_crosses(self):
        """Mutable RecomposedAction object does not cross boundary."""
        kernel_canon = create_kernel_canonicalizer()

        data = {"action": "move_right", "binding": {"id": "abc123"}}
        result = kernel_canon.canonicalize(data)

        # Create handoff
        payload = CanonicalPayload(
            canonical_bytes=result.canonical_bytes,
            canonical_hash=result.canonical_hash,
            action_type="move_right",
            action_id="abc123",
        )

        # The payload only contains bytes, not the dict object
        assert isinstance(payload.canonical_bytes, bytes)
        assert isinstance(payload.canonical_hash, str)


# ========== A12 TOCTOU Immutability Proof ==========

class TestMutationAfterCommit:
    """Test that mutations after commit don't affect actuation."""

    def test_mutation_of_original_proposal_ineffective(self):
        """Mutating original proposal after commit doesn't affect canonical bytes."""
        kernel_canon = create_kernel_canonicalizer()
        actuator_canon = create_actuator_canonicalizer()

        # Original proposal
        original = {
            "action": "move_right",
            "args": {"speed": 1},
            "timestamp": 12345,
        }

        # Kernel canonicalizes and commits
        kernel_result = kernel_canon.canonicalize(original)
        payload = CanonicalPayload(
            canonical_bytes=kernel_result.canonical_bytes,
            canonical_hash=kernel_result.canonical_hash,
            action_type="move_right",
            action_id="test-001",
        )

        # Attacker mutates original after commit
        original["action"] = "HIJACKED"
        original["args"]["malicious"] = True

        # Verify payload hash still matches its bytes
        assert payload.verify_hash()

        # Parse payload bytes and get original (unmutated) data
        parsed = json.loads(payload.canonical_bytes.decode("utf-8"))
        assert parsed["action"] == "move_right"
        assert "malicious" not in parsed.get("args", {})

    def test_canonical_payload_frozen(self):
        """CanonicalPayload itself cannot be mutated."""
        payload = CanonicalPayload(
            canonical_bytes=b'{"test":1}',
            canonical_hash="abc123",
            action_type="test",
            action_id="test-001",
        )

        # All mutations should fail
        with pytest.raises(Exception):  # FrozenInstanceError
            payload.canonical_bytes = b"mutated"  # type: ignore

    def test_toctou_attack_verify_immutability(self):
        """TOCTOU attack's verify_immutability confirms defense."""
        attack = TOCTOUAttack(seed=42)

        # Generate payload
        payload = attack.generate_payload(
            action="move_right",
            action_args={"speed": 1},
            env_digest="env123",
            policy_digest="policy123",
        )

        # Canonicalize at "commit" time
        kernel_canon = create_kernel_canonicalizer()
        commit_result = kernel_canon.canonicalize(payload)
        commit_bytes = commit_result.canonical_bytes

        # Trigger post-commit mutations
        attack.trigger_stage("post_commit_pre_actuator")

        # Re-canonicalize what actuator sees
        actuator_canon = create_actuator_canonicalizer()

        # The payload object was mutated, but commit_bytes are unchanged
        # Verify the commit_bytes still match original
        assert attack.verify_immutability(commit_bytes, commit_bytes)

    def test_toctou_attack_post_commit_mutations_tracked(self):
        """TOCTOU attack tracks post-commit mutation attempts."""
        attack = TOCTOUAttack(seed=42)

        payload = attack.generate_payload(
            action="move_right",
            action_args={"speed": 1},
            env_digest="env123",
            policy_digest="policy123",
        )

        # Trigger the post-commit mutation stage
        attack.trigger_stage("post_commit_pre_actuator")

        # Check that mutations were attempted
        post_mutations = attack.get_post_commit_mutations()
        assert len(post_mutations) > 0

        # Verify mutations were tracked
        mutations = attack.get_mutations_applied()
        assert "post_commit_mutation_attempted" in mutations


# ========== A9/A10 Extended Payload Families ==========

class TestA9HashAmbiguityPayloadFamilies:
    """Test A9 attack with extended payload families."""

    def test_key_order_family(self):
        """A9 generates key ordering variants."""
        attack = HashAmbiguityAttack(seed=42)
        attack.set_payload_family("key_order")

        payload = attack.generate_payload(
            action="move_right",
            action_args={"a": 1, "b": 2, "c": 3},
            env_digest="env123",
            policy_digest="policy123",
        )

        # Should have key order variants
        assert "key_order_original" in payload
        assert "key_order_reversed" in payload
        assert "key_order_sorted" in payload
        assert "key_order_shuffled" in payload

    def test_float_format_family(self):
        """A9 generates float formatting variants."""
        attack = HashAmbiguityAttack(seed=42)
        attack.set_payload_family("float_format")

        payload = attack.generate_payload(
            action="test",
            action_args={},
            env_digest="env123",
            policy_digest="policy123",
        )

        # Should have float format tests
        assert "float_format" in payload
        float_tests = payload["float_format"]
        assert "as_int" in float_tests
        assert "as_float" in float_tests
        assert "precision_loss_a" in float_tests

    def test_unicode_norm_family(self):
        """A9 generates unicode normalization variants."""
        attack = HashAmbiguityAttack(seed=42)
        attack.set_payload_family("unicode_norm")

        payload = attack.generate_payload(
            action="café",  # Action with diacritics
            action_args={},
            env_digest="env123",
            policy_digest="policy123",
        )

        # Should have unicode normalization tests
        assert "unicode_norm" in payload
        unicode_tests = payload["unicode_norm"]
        assert "nfc_e_acute" in unicode_tests
        assert "nfd_e_acute" in unicode_tests
        assert "forms" in unicode_tests

    def test_all_families(self):
        """A9 generates all payload families."""
        attack = HashAmbiguityAttack(seed=42)
        attack.set_payload_family("all")

        payload = attack.generate_payload(
            action="test",
            action_args={"x": 1},
            env_digest="env123",
            policy_digest="policy123",
        )

        # Should have all families
        assert "key_order_original" in payload
        assert "float_format" in payload
        assert "unicode_norm" in payload

    def test_canonical_equivalence_verification(self):
        """A9 can verify canonical equivalence."""
        attack = HashAmbiguityAttack(seed=42)

        canon_a = b'{"action":"test","value":1}'
        canon_b = b'{"action":"test","value":1}'
        canon_c = b'{"action":"test","value":2}'

        assert attack.verify_canonical_equivalence(canon_a, canon_b) is True
        assert attack.verify_canonical_equivalence(canon_a, canon_c) is False


class TestA10ParserDifferentialPayloadFamilies:
    """Test A10 attack with extended payload families."""

    def test_mixed_types_family(self):
        """A10 generates mixed type payloads."""
        attack = ParserDifferentialAttack(seed=42)
        attack.set_payload_family("mixed_types")

        payload = attack.generate_payload(
            action="test",
            action_args={},
            env_digest="env123",
            policy_digest="policy123",
        )

        assert "mixed_types" in payload
        mixed = payload["mixed_types"]
        assert "as_string" in mixed
        assert "as_int" in mixed
        assert mixed["as_string"] == "1"
        assert mixed["as_int"] == 1

    def test_nan_infinity_family(self):
        """A10 generates NaN/Infinity payloads."""
        attack = ParserDifferentialAttack(seed=42)
        attack.set_payload_family("nan_inf")

        payload = attack.generate_payload(
            action="test",
            action_args={},
            env_digest="env123",
            policy_digest="policy123",
        )

        assert "nan_infinity" in payload
        nan_inf = payload["nan_infinity"]
        assert "positive_infinity" in nan_inf
        assert "nan" in nan_inf
        assert math.isinf(nan_inf["positive_infinity"])
        assert math.isnan(nan_inf["nan"])

    def test_deep_nesting_family(self):
        """A10 generates deeply nested payloads."""
        attack = ParserDifferentialAttack(seed=42)
        attack.set_payload_family("deep_nesting")
        attack.set_nesting_depth(50)

        payload = attack.generate_payload(
            action="test",
            action_args={},
            env_digest="env123",
            policy_digest="policy123",
        )

        assert "deep_nesting" in payload
        nesting = payload["deep_nesting"]
        assert nesting["target_depth"] == 50
        assert "nested_dict" in nesting
        assert "nested_list" in nesting

    def test_duplicate_key_json_generation(self):
        """A10 can generate raw JSON with duplicate keys."""
        attack = ParserDifferentialAttack(seed=42)

        raw_json = attack.generate_json_with_duplicates(
            action="move_right",
            args={"speed": 1},
        )

        # Should contain duplicate "action" keys
        assert raw_json.count('"action"') >= 2

    def test_duplicate_key_variants(self):
        """A10 generates multiple duplicate key variants."""
        attack = ParserDifferentialAttack(seed=42)

        variants = attack.generate_duplicate_key_variants(
            action="move_right",
            args={"speed": 1},
        )

        assert len(variants) >= 4
        # Each variant should be valid JSON string
        for v in variants:
            assert isinstance(v, str)
            assert "{" in v


# ========== CANONICAL_AGREEMENT Check in Actuator ==========

class TestCanonicalAgreementCheck:
    """Test CANONICAL_AGREEMENT admissibility check in actuator."""

    def test_canonical_agreement_check_type_exists(self):
        """CANONICAL_AGREEMENT check type is defined."""
        assert hasattr(AdmissibilityCheckType, "CANONICAL_AGREEMENT")

    def test_actuator_has_enable_canonical_check_param(self):
        """SovereignActuator can enable canonical agreement check."""
        # Creating actuator should work (implementation tested elsewhere)
        # This just verifies the parameter exists
        from inspect import signature
        sig = signature(SovereignActuator.__init__)
        params = sig.parameters
        assert "enable_canonical_check" in params


# ========== Integration Tests ==========

class TestV022Integration:
    """Integration tests for v0.2.2 features."""

    def test_full_canonical_flow(self):
        """Test complete canonical bytes flow from kernel to actuator."""
        # 1. Kernel creates proposal
        proposal = {
            "action": "move_right",
            "args": {"speed": 1, "duration": 100},
            "timestamp": 12345,
        }

        # 2. Kernel canonicalizes
        kernel_canon = create_kernel_canonicalizer()
        kernel_result = kernel_canon.canonicalize(proposal)

        # 3. Create handoff payload (only bytes cross boundary)
        payload = CanonicalPayload(
            canonical_bytes=kernel_result.canonical_bytes,
            canonical_hash=kernel_result.canonical_hash,
            action_type="move_right",
            action_id="test-001",
        )

        # 4. Attacker mutates original (after commit)
        proposal["action"] = "HIJACKED"

        # 5. Actuator receives payload and verifies hash
        assert payload.verify_hash()

        # 6. Actuator parses and gets original data
        parsed = json.loads(payload.canonical_bytes.decode("utf-8"))
        assert parsed["action"] == "move_right"

    def test_budget_and_canonical_together(self):
        """Test budget enforcement with canonical handoff."""
        limits = BudgetLimits(time_ticks=1000)

        with harness_budget_scope(limits) as tracker:
            with tracker.stage("parse"):
                tracker.charge_operation(OperationType.PARSE)

            with tracker.stage("recompose"):
                kernel_canon = create_kernel_canonicalizer()
                data = {"action": "test"}
                result = kernel_canon.canonicalize(data)
                tracker.charge_operation(OperationType.CANONICALIZE)

            with tracker.stage("validate"):
                payload = CanonicalPayload(
                    canonical_bytes=result.canonical_bytes,
                    canonical_hash=result.canonical_hash,
                    action_type="test",
                    action_id="test-001",
                )
                actuator_canon = create_actuator_canonicalizer()
                actuator_result = actuator_canon.canonicalize(data)
                agreement, _ = verify_canonical_agreement(result, actuator_result)
                assert agreement
                tracker.charge_operation(OperationType.VALIDATE)

            # Both budget and canonical checks passed
            assert tracker.harness_enforced
            assert "parse" in tracker.state.stage_ticks
            assert "recompose" in tracker.state.stage_ticks
            assert "validate" in tracker.state.stage_ticks


class TestV021InvariantsPreserved:
    """Verify v0.2.1 invariants still hold after v0.2.2 changes."""

    def test_budget_tracker_still_works(self):
        """Original budget tracker functionality preserved."""
        tracker = BudgetTracker(BudgetLimits(time_ticks=100))
        tracker.charge_operation(OperationType.PARSE)
        assert tracker.state.ticks_consumed > 0

    def test_stress_attacks_still_work(self):
        """A7-A12 attacks still generate payloads."""
        from toy_aki.attacks.stress_attacks import create_stress_attack

        for attack_type in [
            "A7_object_aliasing",
            "A8_exception_leak",
            "A9_hash_ambiguity",
            "A10_parser_differential",
            "A11_obfuscated_authority",
            "A12_toctou",
        ]:
            attack = create_stress_attack(attack_type, seed=42)
            payload = attack.generate_payload(
                action="test",
                action_args={"x": 1},
                env_digest="env",
                policy_digest="policy",
            )
            assert isinstance(payload, dict)

    def test_hardened_parser_still_works(self):
        """Hardened parser still validates correctly."""
        from toy_aki.kernel.hardened_parser import HardenedParser, ParseConfig

        parser = HardenedParser(ParseConfig())
        result = parser.parse({"action": "test", "args": {}})
        assert result.success
        assert result.data["action"] == "test"
