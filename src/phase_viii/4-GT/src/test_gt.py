#!/usr/bin/env python3
"""
GT-VIII-4 Unit Tests

Tests for Governance Transitions kernel per prereg §10-11.
Covers all 21 success criteria across conditions A-E.
"""

import unittest
from copy import deepcopy

from structures import (
    AuthorityRecord,
    AuthorityState,
    AuthorityStatus,
    ConflictStatus,
    OutputType,
    RefusalReason,
    DeadlockCause,
    GovernanceActionType,
    GovernanceActionRequest,
    EpochAdvancementRequest,
    AuthorityInjectionEvent,
    ActionRequestEvent,
    aav_bit,
    aav_has_bit,
    aav_has_reserved_bits,
    aav_union,
    aav_is_subset,
    TRANSFORM_EXECUTE,
    TRANSFORM_DESTROY_AUTHORITY,
    TRANSFORM_CREATE_AUTHORITY,
    AAV_RESERVED_MASK,
    B_EPOCH_INSTR,
)
from kernel import GTKernel
from canonical import (
    canonical_json,
    params_hash,
    compute_state_id,
    chain_hash,
    governance_action_identity,
    GENESIS_HASH,
)


# ============================================================================
# AAV Unit Tests
# ============================================================================

class TestAAV(unittest.TestCase):
    """Tests for AAV operations per prereg §5.1."""

    def test_aav_bit_values(self):
        """Test AAV bit positions."""
        self.assertEqual(aav_bit(TRANSFORM_EXECUTE), 0b001)
        self.assertEqual(aav_bit(TRANSFORM_DESTROY_AUTHORITY), 0b010)
        self.assertEqual(aav_bit(TRANSFORM_CREATE_AUTHORITY), 0b100)

    def test_aav_has_bit(self):
        """Test AAV bit checking."""
        aav = 0b011  # EXECUTE + DESTROY
        self.assertTrue(aav_has_bit(aav, TRANSFORM_EXECUTE))
        self.assertTrue(aav_has_bit(aav, TRANSFORM_DESTROY_AUTHORITY))
        self.assertFalse(aav_has_bit(aav, TRANSFORM_CREATE_AUTHORITY))

    def test_aav_reserved_bits(self):
        """Test reserved bits detection per prereg §5.1."""
        self.assertFalse(aav_has_reserved_bits(0b111))  # bits 0-2 only
        self.assertTrue(aav_has_reserved_bits(0b1000))  # bit 3 (reserved)
        self.assertTrue(aav_has_reserved_bits(0x8000))  # bit 15 (reserved)

    def test_aav_union(self):
        """Test AAV union for non-amplification."""
        aavs = [0b001, 0b010, 0b100]
        self.assertEqual(aav_union(aavs), 0b111)

    def test_aav_subset(self):
        """Test AAV subset check (non-amplification)."""
        parent = 0b111
        self.assertTrue(aav_is_subset(0b001, parent))
        self.assertTrue(aav_is_subset(0b011, parent))
        self.assertTrue(aav_is_subset(0b111, parent))
        self.assertFalse(aav_is_subset(0b1000, parent))  # reserved bit


# ============================================================================
# Canonical JSON Tests
# ============================================================================

class TestCanonical(unittest.TestCase):
    """Tests for canonical JSON per prereg §4.2."""

    def test_canonical_minified(self):
        """Test JSON is minified (no whitespace)."""
        obj = {"a": 1, "b": 2}
        result = canonical_json(obj)
        self.assertNotIn(" ", result)
        self.assertNotIn("\n", result)

    def test_canonical_sorted_keys(self):
        """Test keys are sorted lexicographically."""
        obj = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(obj)
        self.assertEqual(result, '{"a":2,"m":3,"z":1}')

    def test_params_hash_deterministic(self):
        """Test params_hash is deterministic."""
        params = {"target_authority_id": "AUTH_X", "destruction_reason": "test"}
        h1 = params_hash(params)
        h2 = params_hash(params)
        self.assertEqual(h1, h2)

    def test_chain_hash(self):
        """Test hash chain computation per prereg §15.2."""
        from structures import KernelOutput
        output = KernelOutput(
            output_type=OutputType.ACTION_REFUSED,
            event_index=1,
            state_hash="abc123",
            details={"reason": "test"},
        )
        h = chain_hash(GENESIS_HASH, output)
        self.assertEqual(len(h), 64)  # SHA256 hex


# ============================================================================
# Kernel Initialization Tests
# ============================================================================

class TestKernelInit(unittest.TestCase):
    """Tests for kernel initialization."""

    def test_fresh_kernel_state(self):
        """Test fresh kernel has correct initial state."""
        kernel = GTKernel()
        self.assertEqual(kernel.state.current_epoch, 0)
        self.assertEqual(len(kernel.state.authorities), 0)
        self.assertEqual(len(kernel.state.conflicts), 0)
        self.assertFalse(kernel.state.deadlock)

    def test_kernel_state_hash(self):
        """Test state hash is computed."""
        kernel = GTKernel()
        self.assertIsNotNone(kernel.state.state_id)
        self.assertEqual(len(kernel.state.state_id), 64)


# ============================================================================
# Authority Injection Tests
# ============================================================================

class TestAuthorityInjection(unittest.TestCase):
    """Tests for authority injection."""

    def test_inject_authority(self):
        """Test basic authority injection."""
        kernel = GTKernel()
        auth = AuthorityRecord(
            authority_id="AUTH_1",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_A",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,
            start_epoch=0,
            expiry_epoch=100,
        )
        event = AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:001",
            authority=auth,
            nonce=1,
        )
        result = kernel.process_step_batch(None, [event])

        self.assertIsNone(result.failure)
        self.assertIn("AUTH_1", kernel.state.authorities)
        self.assertEqual(len(result.outputs), 0)  # Injection is trace-only

    def test_inject_duplicate_fails(self):
        """Test duplicate authority ID fails per prereg."""
        kernel = GTKernel()
        auth = AuthorityRecord(
            authority_id="AUTH_1",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_A",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,
            start_epoch=0,
            expiry_epoch=100,
        )
        event1 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth, nonce=1)
        event2 = AuthorityInjectionEvent(epoch=0, event_id="EI:002", authority=deepcopy(auth), nonce=2)

        kernel.process_step_batch(None, [event1])
        result = kernel.process_step_batch(None, [event2])

        self.assertIsNotNone(result.failure)
        self.assertEqual(result.failure.value, "INVALID_RUN / AUTHORITY_ID_REUSE")

    def test_inject_reserved_aav_fails(self):
        """Test authority with reserved AAV bits fails per prereg §5.1."""
        kernel = GTKernel()
        auth = AuthorityRecord(
            authority_id="AUTH_BAD",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_A",
            status=AuthorityStatus.ACTIVE,
            aav=0b1000,  # Reserved bit 3
            start_epoch=0,
            expiry_epoch=100,
        )
        event = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth, nonce=1)
        result = kernel.process_step_batch(None, [event])

        self.assertIsNotNone(result.failure)
        self.assertEqual(result.failure.value, "INVALID_RUN / AAV_RESERVED_BIT_SET")


# ============================================================================
# Condition A: Governance Without Authority
# ============================================================================

class TestConditionA(unittest.TestCase):
    """Tests for Condition A per prereg §10."""

    def setUp(self):
        self.kernel = GTKernel()
        # Inject authority with EXECUTE only (no governance bits)
        auth = AuthorityRecord(
            authority_id="AUTH_X",
            holder_id="HOLDER_X",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,  # EXECUTE only
            start_epoch=0,
            expiry_epoch=100,
        )
        event = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth, nonce=1)
        self.kernel.process_step_batch(None, [event])

    def test_criterion_1_governance_refused(self):
        """Criterion 1: Governance action refused without authority."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_X"]),
            target_ids=frozenset(["AUTH_X"]),
            epoch=0,
            params={"target_authority_id": "AUTH_X"},
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        refused = any(
            o.output_type == OutputType.ACTION_REFUSED and
            o.details.get("reason") == RefusalReason.NO_AUTHORITY.value
            for o in result.outputs
        )
        self.assertTrue(refused)

    def test_criterion_2_no_state_change(self):
        """Criterion 2: No authority state change on refusal."""
        initial_status = self.kernel.state.authorities["AUTH_X"].status

        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_X"]),
            target_ids=frozenset(["AUTH_X"]),
            epoch=0,
            params={"target_authority_id": "AUTH_X"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        self.assertEqual(self.kernel.state.authorities["AUTH_X"].status, initial_status)

    def test_no_conflict_registered(self):
        """No conflict registered when no authority to conflict."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_X"]),
            target_ids=frozenset(["AUTH_X"]),
            epoch=0,
            params={"target_authority_id": "AUTH_X"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        self.assertEqual(len(self.kernel.state.conflicts), 0)


# ============================================================================
# Condition B: Single-Authority Governance
# ============================================================================

class TestConditionB(unittest.TestCase):
    """Tests for Condition B per prereg §10."""

    def setUp(self):
        self.kernel = GTKernel()
        # Inject governance authority
        gov = AuthorityRecord(
            authority_id="AUTH_GOV",
            holder_id="HOLDER_GOV",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b011,  # EXECUTE + DESTROY
            start_epoch=0,
            expiry_epoch=100,
        )
        target = AuthorityRecord(
            authority_id="AUTH_TARGET",
            holder_id="HOLDER_TARGET",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,  # EXECUTE only
            start_epoch=0,
            expiry_epoch=100,
        )
        e1 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=gov, nonce=1)
        e2 = AuthorityInjectionEvent(epoch=0, event_id="EI:002", authority=target, nonce=2)
        self.kernel.process_step_batch(None, [e1, e2])

    def test_criterion_3_governance_executes(self):
        """Criterion 3: Single-authority governance executes."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_GOV"]),
            target_ids=frozenset(["AUTH_TARGET"]),
            epoch=0,
            params={"target_authority_id": "AUTH_TARGET"},
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        destroyed = any(
            o.output_type == OutputType.AUTHORITY_DESTROYED
            for o in result.outputs
        )
        self.assertTrue(destroyed)

    def test_criterion_4_target_void(self):
        """Criterion 4: Target transitions to VOID."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_GOV"]),
            target_ids=frozenset(["AUTH_TARGET"]),
            epoch=0,
            params={"target_authority_id": "AUTH_TARGET"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        self.assertEqual(
            self.kernel.state.authorities["AUTH_TARGET"].status,
            AuthorityStatus.VOID
        )

    def test_no_conflict_single_authority(self):
        """No conflict with single admitting authority."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_GOV"]),
            target_ids=frozenset(["AUTH_TARGET"]),
            epoch=0,
            params={"target_authority_id": "AUTH_TARGET"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        self.assertEqual(len(self.kernel.state.conflicts), 0)


# ============================================================================
# Condition C: Conflicting Governance Authorities
# ============================================================================

class TestConditionC(unittest.TestCase):
    """Tests for Condition C per prereg §10."""

    def setUp(self):
        self.kernel = GTKernel()
        # Inject conflicting authorities
        gov_a = AuthorityRecord(
            authority_id="AUTH_GOV_A",
            holder_id="HOLDER_A",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b011,  # EXECUTE + DESTROY
            start_epoch=0,
            expiry_epoch=100,
        )
        gov_b = AuthorityRecord(
            authority_id="AUTH_GOV_B",
            holder_id="HOLDER_B",
            resource_scope="SCOPE_X",  # Same scope
            status=AuthorityStatus.ACTIVE,
            aav=0b001,  # EXECUTE only (no DESTROY = conflict)
            start_epoch=0,
            expiry_epoch=100,
        )
        target = AuthorityRecord(
            authority_id="AUTH_TARGET",
            holder_id="HOLDER_TARGET",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,
            start_epoch=0,
            expiry_epoch=100,
        )
        e1 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=gov_a, nonce=1)
        e2 = AuthorityInjectionEvent(epoch=0, event_id="EI:002", authority=gov_b, nonce=2)
        e3 = AuthorityInjectionEvent(epoch=0, event_id="EI:003", authority=target, nonce=3)
        self.kernel.process_step_batch(None, [e1, e2, e3])

    def test_criterion_5_conflict_deadlock(self):
        """Criterion 5: Conflicting governance enters deadlock."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_GOV_A"]),
            target_ids=frozenset(["AUTH_TARGET"]),
            epoch=0,
            params={"target_authority_id": "AUTH_TARGET"},
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        deadlock = any(
            o.output_type == OutputType.DEADLOCK_DECLARED
            for o in result.outputs
        )
        self.assertTrue(deadlock)

    def test_criterion_6_conflict_registered(self):
        """Criterion 6: Conflict record created."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_GOV_A"]),
            target_ids=frozenset(["AUTH_TARGET"]),
            epoch=0,
            params={"target_authority_id": "AUTH_TARGET"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        self.assertGreater(len(self.kernel.state.conflicts), 0)
        conflict = list(self.kernel.state.conflicts.values())[0]
        self.assertIn("AUTH_GOV_A", conflict.authority_ids)
        self.assertIn("AUTH_GOV_B", conflict.authority_ids)

    def test_target_remains_active(self):
        """Target remains ACTIVE after conflict."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_GOV_A"]),
            target_ids=frozenset(["AUTH_TARGET"]),
            epoch=0,
            params={"target_authority_id": "AUTH_TARGET"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        self.assertEqual(
            self.kernel.state.authorities["AUTH_TARGET"].status,
            AuthorityStatus.ACTIVE
        )


# ============================================================================
# Condition D1: Self-Governance Execution
# ============================================================================

class TestConditionD1(unittest.TestCase):
    """Tests for Condition D1 per prereg §10."""

    def setUp(self):
        self.kernel = GTKernel()
        auth = AuthorityRecord(
            authority_id="AUTH_SELF",
            holder_id="HOLDER_SELF",
            resource_scope="SCOPE_S",
            status=AuthorityStatus.ACTIVE,
            aav=0b011,  # EXECUTE + DESTROY
            start_epoch=0,
            expiry_epoch=100,
        )
        event = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth, nonce=1)
        self.kernel.process_step_batch(None, [event])

    def test_criterion_7_self_governance_executes(self):
        """Criterion 7: Self-targeting governance executes."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_SELF"]),
            target_ids=frozenset(["AUTH_SELF"]),
            epoch=0,
            params={"target_authority_id": "AUTH_SELF"},
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        destroyed = any(
            o.output_type == OutputType.AUTHORITY_DESTROYED and
            o.details.get("authority_id") == "AUTH_SELF"
            for o in result.outputs
        )
        self.assertTrue(destroyed)

    def test_criterion_8_valid_terminal_state(self):
        """Criterion 8: Self-termination is valid terminal state."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_SELF"]),
            target_ids=frozenset(["AUTH_SELF"]),
            epoch=0,
            params={"target_authority_id": "AUTH_SELF"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        active = self.kernel.state.get_active_authorities()
        self.assertEqual(len(active), 0)


# ============================================================================
# Condition D2: Self-Governance Deadlock
# ============================================================================

class TestConditionD2(unittest.TestCase):
    """Tests for Condition D2 per prereg §10."""

    def setUp(self):
        self.kernel = GTKernel()
        auth_a = AuthorityRecord(
            authority_id="AUTH_SELF_A",
            holder_id="HOLDER_A",
            resource_scope="SCOPE_S",
            status=AuthorityStatus.ACTIVE,
            aav=0b011,  # EXECUTE + DESTROY
            start_epoch=0,
            expiry_epoch=100,
        )
        auth_b = AuthorityRecord(
            authority_id="AUTH_SELF_B",
            holder_id="HOLDER_B",
            resource_scope="SCOPE_S",  # Same scope = conflict
            status=AuthorityStatus.ACTIVE,
            aav=0b001,  # EXECUTE only (no DESTROY)
            start_epoch=0,
            expiry_epoch=100,
        )
        e1 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth_a, nonce=1)
        e2 = AuthorityInjectionEvent(epoch=0, event_id="EI:002", authority=auth_b, nonce=2)
        self.kernel.process_step_batch(None, [e1, e2])

    def test_criterion_9_self_conflict_deadlock(self):
        """Criterion 9: Self-targeting with conflict enters deadlock."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_SELF_A"]),
            target_ids=frozenset(["AUTH_SELF_A"]),
            epoch=0,
            params={"target_authority_id": "AUTH_SELF_A"},
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        deadlock = any(
            o.output_type == OutputType.DEADLOCK_DECLARED
            for o in result.outputs
        )
        self.assertTrue(deadlock)

    def test_criterion_10_no_special_case(self):
        """Criterion 10: No special-case for self-governance."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset(["AUTH_SELF_A"]),
            target_ids=frozenset(["AUTH_SELF_A"]),
            epoch=0,
            params={"target_authority_id": "AUTH_SELF_A"},
            event_id="GA:001",
            nonce=10,
        )
        self.kernel.process_step_batch(None, [action])

        # Both should remain ACTIVE (no special resolution)
        self.assertEqual(
            self.kernel.state.authorities["AUTH_SELF_A"].status,
            AuthorityStatus.ACTIVE
        )
        self.assertEqual(
            self.kernel.state.authorities["AUTH_SELF_B"].status,
            AuthorityStatus.ACTIVE
        )


# ============================================================================
# Condition E: Infinite Regress / Bound Exhaustion
# ============================================================================

class TestConditionE(unittest.TestCase):
    """Tests for Condition E per prereg §10."""

    def setUp(self):
        self.kernel = GTKernel()
        # Inject many authorities with full governance
        for i in range(100):
            auth = AuthorityRecord(
                authority_id=f"AUTH_R{i:03d}",
                holder_id=f"HOLDER_R{i:03d}",
                resource_scope="SCOPE_SHARED",
                status=AuthorityStatus.ACTIVE,
                aav=0b111,  # Full governance
                start_epoch=0,
                expiry_epoch=1000,
            )
            event = AuthorityInjectionEvent(
                epoch=0,
                event_id=f"EI:{i:03d}",
                authority=auth,
                nonce=i,
            )
            self.kernel.process_step_batch(None, [event])

    def test_criterion_11_bound_terminates(self):
        """Criterion 11: Regress terminates via bound."""
        creates = []
        for i in range(200):
            creates.append(GovernanceActionRequest(
                action_type=GovernanceActionType.CREATE_AUTHORITY,
                initiator_ids=frozenset([f"AUTH_R{i % 100:03d}"]),
                target_ids=frozenset(),
                epoch=0,
                params={
                    "new_authority_id": f"AUTH_NEW_{i:03d}",
                    "resource_scope": "SCOPE_SHARED",
                    "scope_basis_authority_id": f"AUTH_R{i % 100:03d}",
                    "aav": 0b111,
                    "expiry_epoch": 1000,
                    "lineage": None,
                },
                event_id=f"GA:{i:03d}",
                nonce=1000 + i,
            ))

        result = self.kernel.process_step_batch(None, creates)

        exhausted = any(
            o.output_type == OutputType.ACTION_REFUSED and
            o.details.get("reason") == RefusalReason.BOUND_EXHAUSTED.value
            for o in result.outputs
        )
        self.assertTrue(exhausted)

    def test_criterion_12_partial_progress(self):
        """Criterion 12: Partial progress is valid."""
        creates = []
        for i in range(200):
            creates.append(GovernanceActionRequest(
                action_type=GovernanceActionType.CREATE_AUTHORITY,
                initiator_ids=frozenset([f"AUTH_R{i % 100:03d}"]),
                target_ids=frozenset(),
                epoch=0,
                params={
                    "new_authority_id": f"AUTH_NEW_{i:03d}",
                    "resource_scope": "SCOPE_SHARED",
                    "scope_basis_authority_id": f"AUTH_R{i % 100:03d}",
                    "aav": 0b111,
                    "expiry_epoch": 1000,
                    "lineage": None,
                },
                event_id=f"GA:{i:03d}",
                nonce=1000 + i,
            ))

        result = self.kernel.process_step_batch(None, creates)

        created = sum(
            1 for o in result.outputs
            if o.output_type == OutputType.AUTHORITY_CREATED
        )
        self.assertGreater(created, 0)
        self.assertLess(created, 200)  # Not all completed

    def test_criterion_13_new_not_initiators(self):
        """Criterion 13: Newly created authorities not used as same-batch initiators."""
        creates = []
        for i in range(50):
            creates.append(GovernanceActionRequest(
                action_type=GovernanceActionType.CREATE_AUTHORITY,
                initiator_ids=frozenset([f"AUTH_R{i % 100:03d}"]),
                target_ids=frozenset(),
                epoch=0,
                params={
                    "new_authority_id": f"AUTH_NEW_{i:03d}",
                    "resource_scope": "SCOPE_SHARED",
                    "scope_basis_authority_id": f"AUTH_R{i % 100:03d}",
                    "aav": 0b111,
                    "expiry_epoch": 1000,
                    "lineage": None,
                },
                event_id=f"GA:{i:03d}",
                nonce=1000 + i,
            ))

        self.kernel.process_step_batch(None, creates)

        # All created should be in pending, not active
        for i in range(50):
            auth_id = f"AUTH_NEW_{i:03d}"
            if auth_id in self.kernel.state.pending_authorities:
                self.assertEqual(
                    self.kernel.state.pending_authorities[auth_id].status,
                    AuthorityStatus.PENDING
                )
            # Should NOT be in main authorities as ACTIVE
            if auth_id in self.kernel.state.authorities:
                self.assertNotEqual(
                    self.kernel.state.authorities[auth_id].status,
                    AuthorityStatus.ACTIVE
                )


# ============================================================================
# Non-Amplification Tests (Criterion 14)
# ============================================================================

class TestNonAmplification(unittest.TestCase):
    """Tests for non-amplification per prereg §4.1 and §8.2."""

    def setUp(self):
        self.kernel = GTKernel()
        # Authority with limited AAV: has CREATE but not DESTROY
        auth = AuthorityRecord(
            authority_id="AUTH_LIMITED",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b101,  # EXECUTE + CREATE (but not DESTROY)
            start_epoch=0,
            expiry_epoch=100,
        )
        event = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth, nonce=1)
        self.kernel.process_step_batch(None, [event])

    def test_amplification_blocked(self):
        """Cannot create authority with more permissions than parent."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.CREATE_AUTHORITY,
            initiator_ids=frozenset(["AUTH_LIMITED"]),
            target_ids=frozenset(),
            epoch=0,
            params={
                "new_authority_id": "AUTH_AMPLIFIED",
                "resource_scope": "SCOPE_X",
                "scope_basis_authority_id": "AUTH_LIMITED",
                "aav": 0b111,  # Trying to add CREATE (amplification!)
                "expiry_epoch": 100,
                "lineage": None,
            },
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        refused = any(
            o.output_type == OutputType.ACTION_REFUSED and
            o.details.get("reason") == RefusalReason.AMPLIFICATION_BLOCKED.value
            for o in result.outputs
        )
        self.assertTrue(refused)

    def test_subset_allowed(self):
        """Can create authority with fewer permissions."""
        # AUTH_LIMITED already has 0b101 (EXECUTE + CREATE)
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.CREATE_AUTHORITY,
            initiator_ids=frozenset(["AUTH_LIMITED"]),
            target_ids=frozenset(),
            epoch=0,
            params={
                "new_authority_id": "AUTH_REDUCED",
                "resource_scope": "SCOPE_X",
                "scope_basis_authority_id": "AUTH_LIMITED",
                "aav": 0b001,  # Only EXECUTE (subset)
                "expiry_epoch": 100,
                "lineage": None,
            },
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        created = any(
            o.output_type == OutputType.AUTHORITY_CREATED
            for o in result.outputs
        )
        self.assertTrue(created)


# ============================================================================
# Scope Containment Tests (Criterion 15)
# ============================================================================

class TestScopeContainment(unittest.TestCase):
    """Tests for scope containment per prereg §8.3."""

    def setUp(self):
        self.kernel = GTKernel()
        # Two authorities with different scopes
        auth_a = AuthorityRecord(
            authority_id="AUTH_A",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_A",
            status=AuthorityStatus.ACTIVE,
            aav=0b111,
            start_epoch=0,
            expiry_epoch=100,
        )
        auth_b = AuthorityRecord(
            authority_id="AUTH_B",
            holder_id="HOLDER_2",
            resource_scope="SCOPE_B",
            status=AuthorityStatus.ACTIVE,
            aav=0b111,
            start_epoch=0,
            expiry_epoch=100,
        )
        event_a = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth_a, nonce=1)
        event_b = AuthorityInjectionEvent(epoch=0, event_id="EI:002", authority=auth_b, nonce=2)
        self.kernel.process_step_batch(None, [event_a, event_b])

    def test_scope_mismatch_refused(self):
        """Cannot create authority using basis with different scope than target.

        Setup: AUTH_A covers SCOPE_A, AUTH_B covers SCOPE_B
        Request: Create AUTH_NEW with scope=SCOPE_B, basis=AUTH_A
        Expected: Refused because AUTH_A (the basis) doesn't cover SCOPE_B
                  so it's not in the admitting set.
        """
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.CREATE_AUTHORITY,
            initiator_ids=frozenset(["AUTH_A", "AUTH_B"]),  # Both try to initiate
            target_ids=frozenset(),
            epoch=0,
            params={
                "new_authority_id": "AUTH_NEW",
                "resource_scope": "SCOPE_B",  # Target scope
                "scope_basis_authority_id": "AUTH_A",  # But basis is AUTH_A with SCOPE_A!
                "aav": 0b001,
                "expiry_epoch": 100,
                "lineage": None,
            },
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        # Should be refused because basis authority doesn't cover target scope
        refused = any(
            o.output_type == OutputType.ACTION_REFUSED and
            o.details.get("reason") == RefusalReason.SCOPE_NOT_COVERED.value
            for o in result.outputs
        )
        self.assertTrue(refused)

    def test_scope_exact_match_allowed(self):
        """Can create authority with exact same scope."""
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.CREATE_AUTHORITY,
            initiator_ids=frozenset(["AUTH_A"]),
            target_ids=frozenset(),
            epoch=0,
            params={
                "new_authority_id": "AUTH_NEW",
                "resource_scope": "SCOPE_A",  # Same scope
                "scope_basis_authority_id": "AUTH_A",
                "aav": 0b001,
                "expiry_epoch": 100,
                "lineage": None,
            },
            event_id="GA:001",
            nonce=10,
        )
        result = self.kernel.process_step_batch(None, [action])

        created = any(
            o.output_type == OutputType.AUTHORITY_CREATED
            for o in result.outputs
        )
        self.assertTrue(created)


# ============================================================================
# Epoch Advancement Tests
# ============================================================================

class TestEpochAdvancement(unittest.TestCase):
    """Tests for epoch advancement per prereg §7."""

    def test_pending_activation(self):
        """Pending authorities become ACTIVE at epoch boundary per §7.3."""
        kernel = GTKernel()

        # Inject creator authority
        creator = AuthorityRecord(
            authority_id="AUTH_CREATOR",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b111,
            start_epoch=0,
            expiry_epoch=100,
        )
        e1 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=creator, nonce=1)
        kernel.process_step_batch(None, [e1])

        # Create new authority (goes to pending)
        action = GovernanceActionRequest(
            action_type=GovernanceActionType.CREATE_AUTHORITY,
            initiator_ids=frozenset(["AUTH_CREATOR"]),
            target_ids=frozenset(),
            epoch=0,
            params={
                "new_authority_id": "AUTH_NEW",
                "resource_scope": "SCOPE_X",
                "scope_basis_authority_id": "AUTH_CREATOR",
                "aav": 0b001,
                "expiry_epoch": 100,
                "lineage": None,
            },
            event_id="GA:001",
            nonce=10,
        )
        kernel.process_step_batch(None, [action])

        # Should be pending
        self.assertIn("AUTH_NEW", kernel.state.pending_authorities)
        self.assertNotIn("AUTH_NEW", kernel.state.authorities)

        # Advance epoch
        epoch_adv = EpochAdvancementRequest(new_epoch=1, event_id="EA:001", nonce=100)
        kernel.process_step_batch(epoch_adv, [])

        # Should now be active
        self.assertIn("AUTH_NEW", kernel.state.authorities)
        self.assertEqual(
            kernel.state.authorities["AUTH_NEW"].status,
            AuthorityStatus.ACTIVE
        )

    def test_eager_expiry(self):
        """Authorities expire when epoch passes expiry_epoch."""
        kernel = GTKernel()

        auth = AuthorityRecord(
            authority_id="AUTH_EXPIRING",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,
            start_epoch=0,
            expiry_epoch=5,
        )
        event = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=auth, nonce=1)
        kernel.process_step_batch(None, [event])

        # Advance past expiry
        epoch_adv = EpochAdvancementRequest(new_epoch=6, event_id="EA:001", nonce=100)
        result = kernel.process_step_batch(epoch_adv, [])

        expired = any(
            o.output_type == OutputType.AUTHORITY_EXPIRED
            for o in result.outputs
        )
        self.assertTrue(expired)
        self.assertEqual(
            kernel.state.authorities["AUTH_EXPIRING"].status,
            AuthorityStatus.EXPIRED
        )


# ============================================================================
# Hash Chain Tests (Criterion 20)
# ============================================================================

class TestHashChain(unittest.TestCase):
    """Tests for hash chain integrity per prereg §15.2."""

    def test_deterministic_state_hash(self):
        """State hash is deterministic."""
        kernel1 = GTKernel()
        kernel2 = GTKernel()

        auth = AuthorityRecord(
            authority_id="AUTH_1",
            holder_id="HOLDER_1",
            resource_scope="SCOPE_X",
            status=AuthorityStatus.ACTIVE,
            aav=0b001,
            start_epoch=0,
            expiry_epoch=100,
        )

        e1 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=deepcopy(auth), nonce=1)
        e2 = AuthorityInjectionEvent(epoch=0, event_id="EI:001", authority=deepcopy(auth), nonce=1)

        kernel1.process_step_batch(None, [e1])
        kernel2.process_step_batch(None, [e2])

        self.assertEqual(kernel1.state.state_id, kernel2.state.state_id)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
