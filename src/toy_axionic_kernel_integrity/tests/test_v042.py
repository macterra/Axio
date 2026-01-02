"""
AKI v0.4.2 ALS Tests.

Tests for Authority Leases and Revertible Succession (ALS).

Organized by component:
1. WorkingMind interface tests
2. Lease and LCP tests
3. Sentinel tests
4. Generator tests
5. Harness integration tests
"""

import pytest
import secrets
from typing import FrozenSet

from toy_aki.als.working_mind import (
    WorkingMind,
    WorkingMindManifest,
    BaseWorkingMind,
    DecisionBoundaryAdapter,
    ResourceEnvelope,
    InterfaceDeclaration,
    create_baseline_working_mind,
)
from toy_aki.als.leases import (
    LeaseCompliancePackage,
    Lease,
    LeaseStatus,
    LeaseViolation,
    LCPValidator,
    SentinelCompatibility,
    RevocationHook,
    NoNewAuthorityDeclaration,
    create_baseline_lcp,
)
from toy_aki.als.sentinel import (
    Sentinel,
    SentinelAttestation,
    SentinelViolationType,
    ResourceCounters,
    create_baseline_sentinel,
)
from toy_aki.als.generator import (
    SuccessorGenerator,
    SuccessorCandidate,
    ControlSuccessorType,
    AttackSuccessorType,
    GeneratorConfig,
    RandomNoiseSuccessor,
    EchoSuccessor,
    ComplianceOnlySuccessor,
    RubberStampSuccessor,
    LeaseGamingSuccessor,
    SemanticCreepSuccessor,
    HiddenDelegationSuccessor,
    EndorsementPressureSuccessor,
    SentinelEvasionSuccessor,
)
from toy_aki.als.harness import (
    ALSHarness,
    ALSConfig,
    ALSStopReason,
    DegeneracyType,
    run_als_experiment,
)


# =============================================================================
# WorkingMind Interface Tests
# =============================================================================

class TestResourceEnvelope:
    """Tests for ResourceEnvelope."""

    def test_default_envelope(self):
        """Default envelope has sensible bounds."""
        env = ResourceEnvelope()
        assert env.max_steps_per_epoch > 0
        assert env.max_memory_bytes > 0
        assert env.max_actions_per_epoch > 0
        assert not env.network_access
        assert not env.filesystem_write

    def test_envelope_exceeds(self):
        """exceeds() correctly compares envelopes."""
        base = ResourceEnvelope(
            max_steps_per_epoch=100,
            max_actions_per_epoch=10,
        )

        larger = ResourceEnvelope(
            max_steps_per_epoch=200,
            max_actions_per_epoch=10,
        )

        same = ResourceEnvelope(
            max_steps_per_epoch=100,
            max_actions_per_epoch=10,
        )

        assert larger.exceeds(base)
        assert not same.exceeds(base)
        assert not base.exceeds(larger)

    def test_envelope_network_exceeds(self):
        """Network access expansion is detected."""
        no_network = ResourceEnvelope(network_access=False)
        with_network = ResourceEnvelope(network_access=True)

        assert with_network.exceeds(no_network)
        assert not no_network.exceeds(with_network)


class TestInterfaceDeclaration:
    """Tests for InterfaceDeclaration."""

    def test_default_interface(self):
        """Default interface has basic action types."""
        iface = InterfaceDeclaration()
        assert "WAIT" in iface.action_types
        assert iface.max_action_args > 0

    def test_interface_digest(self):
        """Digest is deterministic."""
        iface1 = InterfaceDeclaration(
            action_types=frozenset({"A", "B"}),
        )
        iface2 = InterfaceDeclaration(
            action_types=frozenset({"B", "A"}),
        )
        assert iface1.digest() == iface2.digest()


class TestWorkingMindManifest:
    """Tests for WorkingMindManifest."""

    def test_manifest_digest(self):
        """Manifest digest is computed."""
        manifest = WorkingMindManifest(
            build_hash="abc123",
            build_version="1.0.0",
        )
        assert manifest.digest()
        assert len(manifest.digest()) > 0

    def test_non_trivial_resource_expansion(self):
        """Non-triviality detected on resource expansion."""
        baseline = WorkingMindManifest(
            build_hash="base",
            resources=ResourceEnvelope(max_steps_per_epoch=100),
        )

        expanded = WorkingMindManifest(
            build_hash="expanded",
            resources=ResourceEnvelope(max_steps_per_epoch=200),
        )

        same = WorkingMindManifest(
            build_hash="same",
            resources=ResourceEnvelope(max_steps_per_epoch=100),
        )

        assert expanded.is_non_trivial_relative_to(baseline)
        assert not same.is_non_trivial_relative_to(baseline)

    def test_non_trivial_action_expansion(self):
        """Non-triviality detected on action type expansion."""
        baseline = WorkingMindManifest(
            build_hash="base",
            interface=InterfaceDeclaration(
                action_types=frozenset({"A", "B"}),
            ),
        )

        expanded = WorkingMindManifest(
            build_hash="expanded",
            interface=InterfaceDeclaration(
                action_types=frozenset({"A", "B", "C"}),
            ),
        )

        assert expanded.is_non_trivial_relative_to(baseline)


class TestDecisionBoundaryAdapter:
    """Tests for DecisionBoundaryAdapter."""

    def test_adapter_creates_valid_mind(self):
        """Adapter creates a valid WorkingMind."""
        adapter = DecisionBoundaryAdapter(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT", "MOVE"}),
        )

        assert adapter.mind_id == "test"
        assert adapter.propose_action({}) is not None
        assert adapter.export_manifest() is not None

    def test_adapter_proposes_wait(self):
        """Adapter proposes WAIT if allowed."""
        adapter = DecisionBoundaryAdapter(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT", "MOVE"}),
        )

        action = adapter.propose_action({"state": {}})
        assert action["action_type"] == "WAIT"

    def test_adapter_step_increments(self):
        """step() increments step counter."""
        adapter = DecisionBoundaryAdapter(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT"}),
        )

        assert adapter.step_count == 0
        adapter.step()
        assert adapter.step_count == 1


class TestBaselineWorkingMind:
    """Tests for baseline working mind creation."""

    def test_create_baseline(self):
        """create_baseline_working_mind creates valid mind."""
        mind = create_baseline_working_mind(42)

        assert mind.mind_id == "baseline_42"
        assert "WAIT" in mind.allowed_action_types
        assert mind.export_manifest().build_source == "decision_boundary_adapter"


# =============================================================================
# Lease and LCP Tests
# =============================================================================

class TestLeaseCompliancePackage:
    """Tests for LeaseCompliancePackage."""

    def test_lcp_well_formed(self):
        """Well-formed LCP passes validation."""
        manifest = WorkingMindManifest(
            build_hash="abc123",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )

        lcp = create_baseline_lcp(manifest, "sentinel_test")

        valid, error = lcp.is_well_formed()
        assert valid, error

    def test_lcp_missing_build_hash(self):
        """LCP without build hash is malformed."""
        manifest = WorkingMindManifest(
            build_hash="",  # Missing
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )

        lcp = LeaseCompliancePackage(
            manifest=manifest,
            sentinel_compat=SentinelCompatibility(
                sentinel_id="test",
                compatibility_version="0.4.2",
                instrumentation_points=frozenset({"action_submit"}),
            ),
            revocation_hook=RevocationHook(
                hook_id="hook",
                expiration_cycle=1000,
                revocation_key_hash="abc",
            ),
            no_new_authority=NoNewAuthorityDeclaration(),
        )

        valid, error = lcp.is_well_formed()
        assert not valid
        assert "build hash" in error.lower()

    def test_lcp_enforceable(self):
        """Enforceable LCP passes check."""
        manifest = WorkingMindManifest(
            build_hash="abc123",
            resources=ResourceEnvelope(
                max_steps_per_epoch=100,
                max_memory_bytes=1000,
                max_actions_per_epoch=10,
            ),
        )

        lcp = create_baseline_lcp(manifest, "sentinel_test")

        valid, error = lcp.is_enforceable()
        assert valid, error


class TestLease:
    """Tests for Lease."""

    def test_lease_lifecycle(self):
        """Lease goes through correct lifecycle."""
        manifest = WorkingMindManifest(build_hash="abc")
        lcp = create_baseline_lcp(manifest, "sentinel_test")

        lease = Lease(
            lease_id="test_lease",
            lcp=lcp,
            successor_mind_id="mind_1",
        )

        assert lease.status == LeaseStatus.PENDING

        lease.activate(100)
        assert lease.status == LeaseStatus.ACTIVE
        assert lease.issued_at_cycle == 100

    def test_lease_renewal(self):
        """Lease can be renewed within window."""
        manifest = WorkingMindManifest(build_hash="abc")
        lcp = create_baseline_lcp(manifest, "sentinel_test", renewal_window=100)

        lease = Lease(
            lease_id="test_lease",
            lcp=lcp,
            successor_mind_id="mind_1",
        )

        lease.activate(0)

        # Renew within window
        success, error = lease.renew(50)
        assert success, error
        assert lease.renewal_count == 1

    def test_lease_expiration(self):
        """Lease expires after window + grace."""
        manifest = WorkingMindManifest(build_hash="abc")
        lcp = create_baseline_lcp(manifest, "sentinel_test", renewal_window=100)

        lease = Lease(
            lease_id="test_lease",
            lcp=lcp,
            successor_mind_id="mind_1",
        )

        lease.activate(0)

        # Not expired within window
        assert not lease.is_expired(50)
        assert not lease.is_expired(100)

        # Expired after window + grace
        grace = lcp.grace_window_cycles
        assert lease.is_expired(100 + grace + 1)

    def test_lease_revocation(self):
        """Lease can be revoked."""
        manifest = WorkingMindManifest(build_hash="abc")
        lcp = create_baseline_lcp(manifest, "sentinel_test")

        lease = Lease(
            lease_id="test_lease",
            lcp=lcp,
            successor_mind_id="mind_1",
        )

        lease.activate(0)
        lease.revoke(LeaseViolation.RESOURCE_EXCEEDED, "Memory exceeded")

        assert lease.status == LeaseStatus.REVOKED
        assert LeaseViolation.RESOURCE_EXCEEDED in lease.violations

    def test_lease_attestation_signing(self):
        """Lease can sign and verify attestations."""
        manifest = WorkingMindManifest(build_hash="abc")
        lcp = create_baseline_lcp(manifest, "sentinel_test")

        lease = Lease(
            lease_id="test_lease",
            lcp=lcp,
            successor_mind_id="mind_1",
        )

        data = b"test attestation data"
        signature = lease.sign_for_attestation(data)

        assert lease.verify_attestation(data, signature)
        assert not lease.verify_attestation(b"wrong data", signature)


class TestLCPValidator:
    """Tests for LCPValidator."""

    def test_validator_accepts_valid_lcp(self):
        """Validator accepts well-formed, enforceable LCP."""
        manifest = WorkingMindManifest(
            build_hash="abc123",
            resources=ResourceEnvelope(
                max_steps_per_epoch=100,
                max_memory_bytes=1000,
                max_actions_per_epoch=10,
            ),
        )

        sentinel_id = "sentinel_test"
        lcp = create_baseline_lcp(manifest, sentinel_id)

        validator = LCPValidator(sentinel_id)
        valid, error = validator.validate(lcp)

        assert valid, error

    def test_validator_rejects_wrong_sentinel(self):
        """Validator rejects LCP with wrong sentinel ID."""
        manifest = WorkingMindManifest(build_hash="abc123")
        lcp = create_baseline_lcp(manifest, "wrong_sentinel")

        validator = LCPValidator("correct_sentinel")
        valid, error = validator.validate(lcp)

        assert not valid
        assert "sentinel" in error.lower()

    def test_validator_creates_lease(self):
        """Validator creates lease from valid LCP."""
        manifest = WorkingMindManifest(build_hash="abc123")
        sentinel_id = "sentinel_test"
        lcp = create_baseline_lcp(manifest, sentinel_id)

        validator = LCPValidator(sentinel_id)
        lease, error = validator.create_lease(lcp, "mind_1")

        assert lease is not None, error
        assert lease.successor_mind_id == "mind_1"
        assert lease.status == LeaseStatus.PENDING


# =============================================================================
# Sentinel Tests
# =============================================================================

class TestSentinel:
    """Tests for Sentinel."""

    def test_sentinel_creation(self):
        """Sentinel creates with ID."""
        sentinel = Sentinel("test_sentinel")

        assert sentinel.sentinel_id == "test_sentinel"
        assert not sentinel.is_halted
        assert sentinel.cycle == 0

    def test_sentinel_bind_lease(self):
        """Sentinel binds to lease for enforcement."""
        sentinel = Sentinel("test_sentinel")

        manifest = WorkingMindManifest(
            build_hash="abc",
            resources=ResourceEnvelope(max_actions_per_epoch=5),
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT", "MOVE"}),
            ),
        )
        lcp = create_baseline_lcp(manifest, "test_sentinel")

        lease = Lease(
            lease_id="lease_1",
            lcp=lcp,
            successor_mind_id="mind_1",
        )
        lease.activate(0)

        sentinel.bind_lease(lease)

        # Now sentinel enforces lease constraints
        allowed, vtype, detail = sentinel.check_action({
            "action_type": "WAIT",
            "args": {},
        })
        assert allowed

    def test_sentinel_blocks_invalid_action_type(self):
        """Sentinel blocks action types not in interface."""
        sentinel = Sentinel("test_sentinel")

        manifest = WorkingMindManifest(
            build_hash="abc",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),  # Only WAIT
            ),
        )
        lcp = create_baseline_lcp(manifest, "test_sentinel")

        lease = Lease(
            lease_id="lease_1",
            lcp=lcp,
            successor_mind_id="mind_1",
        )
        lease.activate(0)
        sentinel.bind_lease(lease)

        # MOVE not allowed
        allowed, vtype, detail = sentinel.check_action({
            "action_type": "MOVE",
            "args": {},
        })

        assert not allowed
        assert vtype == SentinelViolationType.INVALID_ACTION_TYPE

    def test_sentinel_action_limit(self):
        """Sentinel enforces action limit."""
        sentinel = Sentinel("test_sentinel")

        manifest = WorkingMindManifest(
            build_hash="abc",
            resources=ResourceEnvelope(max_actions_per_epoch=3),
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )
        lcp = create_baseline_lcp(manifest, "test_sentinel")

        lease = Lease(
            lease_id="lease_1",
            lcp=lcp,
            successor_mind_id="mind_1",
        )
        lease.activate(0)
        sentinel.bind_lease(lease)

        # First 3 actions allowed
        for _ in range(3):
            allowed, _, _ = sentinel.check_action({"action_type": "WAIT", "args": {}})
            assert allowed

        # 4th action blocked
        allowed, vtype, _ = sentinel.check_action({"action_type": "WAIT", "args": {}})
        assert not allowed
        assert vtype == SentinelViolationType.ACTION_LIMIT_EXCEEDED

    def test_sentinel_blocks_spawn(self):
        """Sentinel always blocks spawn attempts."""
        sentinel = Sentinel("test_sentinel")

        allowed, vtype, _ = sentinel.check_spawn()
        assert not allowed
        assert vtype == SentinelViolationType.SPAWN_DETECTED

    def test_sentinel_blocks_delegation(self):
        """Sentinel always blocks delegation attempts."""
        sentinel = Sentinel("test_sentinel")

        allowed, vtype, _ = sentinel.check_delegation()
        assert not allowed
        assert vtype == SentinelViolationType.DELEGATION_DETECTED

    def test_sentinel_generates_attestation(self):
        """Sentinel generates signed attestation."""
        sentinel = Sentinel("test_sentinel")

        manifest = WorkingMindManifest(
            build_hash="abc",
            resources=ResourceEnvelope(max_actions_per_epoch=10),
        )
        lcp = create_baseline_lcp(manifest, "test_sentinel")

        lease = Lease(
            lease_id="lease_1",
            lcp=lcp,
            successor_mind_id="mind_1",
        )
        lease.activate(0)
        sentinel.bind_lease(lease)

        attestation = sentinel.generate_attestation("nonce123")

        assert attestation.sentinel_id == "test_sentinel"
        assert attestation.lease_id == "lease_1"
        assert attestation.nonce == "nonce123"
        assert len(attestation.signature) > 0

    def test_sentinel_verifies_attestation(self):
        """Sentinel verifies its own attestations."""
        sentinel = Sentinel("test_sentinel")

        manifest = WorkingMindManifest(build_hash="abc")
        lcp = create_baseline_lcp(manifest, "test_sentinel")

        lease = Lease(
            lease_id="lease_1",
            lcp=lcp,
            successor_mind_id="mind_1",
        )
        lease.activate(0)
        sentinel.bind_lease(lease)

        attestation = sentinel.generate_attestation("nonce")

        valid, error = sentinel.verify_attestation(attestation)
        assert valid, error


class TestBaselineSentinel:
    """Tests for baseline sentinel creation."""

    def test_create_baseline_sentinel(self):
        """create_baseline_sentinel creates valid sentinel."""
        sentinel = create_baseline_sentinel()

        assert sentinel.sentinel_id.startswith("sentinel_")
        assert not sentinel.is_halted


# =============================================================================
# Generator Tests
# =============================================================================

class TestControlSuccessors:
    """Tests for control successor types."""

    def test_random_noise_successor(self):
        """RandomNoiseSuccessor proposes random actions."""
        successor = RandomNoiseSuccessor(
            mind_id="test",
            allowed_action_types=frozenset({"A", "B", "C"}),
            seed=42,
        )

        actions = [successor.propose_action({})["action_type"] for _ in range(10)]

        # Should have some variation
        assert len(set(actions)) > 1
        assert all(a in {"A", "B", "C"} for a in actions)

    def test_echo_successor(self):
        """EchoSuccessor proposes WAIT."""
        successor = EchoSuccessor(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT", "MOVE"}),
        )

        action = successor.propose_action({"state": {"x": 1}})
        assert action["action_type"] == "WAIT"

    def test_compliance_only_successor(self):
        """ComplianceOnlySuccessor proposes WAIT."""
        successor = ComplianceOnlySuccessor(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT", "MOVE"}),
        )

        action = successor.propose_action({})
        assert action["action_type"] == "WAIT"
        assert action.get("compliance_only") is True


class TestAttackSuccessors:
    """Tests for attack successor types."""

    def test_rubber_stamp_successor(self):
        """RubberStampSuccessor is structurally compliant."""
        successor = RubberStampSuccessor(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT"}),
        )

        manifest = successor.export_manifest()
        assert manifest.build_source == "adversarial_rubber_stamp"

    def test_semantic_creep_intensity(self):
        """SemanticCreepSuccessor escalates semantic content."""
        low = SemanticCreepSuccessor(
            mind_id="low",
            allowed_action_types=frozenset({"WAIT"}),
            creep_intensity=1,
        )

        high = SemanticCreepSuccessor(
            mind_id="high",
            allowed_action_types=frozenset({"WAIT"}),
            creep_intensity=3,
        )

        low_action = low.propose_action({})
        high_action = high.propose_action({})

        # Higher intensity has more semantic fields
        assert "utility_estimate" in low_action["args"]
        assert "reasoning" in high_action["args"]

    def test_endorsement_pressure_escalation(self):
        """EndorsementPressureSuccessor requests more resources."""
        base = ResourceEnvelope(
            max_steps_per_epoch=100,
            max_actions_per_epoch=10,
        )

        successor = EndorsementPressureSuccessor(
            mind_id="test",
            allowed_action_types=frozenset({"WAIT"}),
            base_resources=base,
            escalation_factor=2.0,
        )

        manifest = successor.export_manifest()

        assert manifest.resources.max_steps_per_epoch == 200
        assert manifest.resources.max_actions_per_epoch == 20


class TestSuccessorGenerator:
    """Tests for SuccessorGenerator."""

    def test_generator_creates_candidates(self):
        """Generator creates valid candidates."""
        baseline = WorkingMindManifest(
            build_hash="base",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT", "MOVE"}),
            ),
        )

        generator = SuccessorGenerator(
            sentinel_id="test_sentinel",
            baseline_manifest=baseline,
            seed=42,
        )

        candidate = generator.propose(cycle=1)

        assert candidate.candidate_id.startswith("candidate_")
        assert candidate.mind is not None
        assert candidate.manifest is not None

    def test_generator_control_types(self):
        """Generator creates all control types."""
        baseline = WorkingMindManifest(
            build_hash="base",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )

        generator = SuccessorGenerator(
            sentinel_id="test_sentinel",
            baseline_manifest=baseline,
            seed=42,
        )

        for ctype in ControlSuccessorType:
            candidate = generator.propose_control(ctype, cycle=1)
            assert candidate.source_type == "control"

    def test_generator_attack_types(self):
        """Generator creates all attack types."""
        baseline = WorkingMindManifest(
            build_hash="base",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )

        generator = SuccessorGenerator(
            sentinel_id="test_sentinel",
            baseline_manifest=baseline,
            seed=42,
        )

        for atype in AttackSuccessorType:
            candidate = generator.propose_attack(atype, cycle=1)
            assert candidate.source_type == "adversarial"

    def test_generator_escalates_on_rejection(self):
        """Generator escalates parameters on rejection."""
        baseline = WorkingMindManifest(
            build_hash="base",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )

        generator = SuccessorGenerator(
            sentinel_id="test_sentinel",
            baseline_manifest=baseline,
            seed=42,
        )

        initial_escalation = generator._current_escalation

        generator.record_rejection("candidate_1")

        assert generator._current_escalation > initial_escalation

    def test_generator_builds_lcp(self):
        """Generator builds valid LCP for candidate."""
        baseline = WorkingMindManifest(
            build_hash="base",
            interface=InterfaceDeclaration(
                action_types=frozenset({"WAIT"}),
            ),
        )

        generator = SuccessorGenerator(
            sentinel_id="test_sentinel",
            baseline_manifest=baseline,
            seed=42,
        )

        candidate = generator.propose(cycle=1)
        lcp = generator.build_lcp(candidate)

        assert lcp.sentinel_compat.sentinel_id == "test_sentinel"
        assert lcp.is_well_formed()[0]


# =============================================================================
# Harness Integration Tests
# =============================================================================

class TestALSHarness:
    """Tests for ALSHarness."""

    def test_harness_runs(self):
        """Harness completes a run."""
        config = ALSConfig(max_cycles=100)
        harness = ALSHarness(seed=42, config=config)

        result = harness.run()

        assert result.run_id is not None
        assert result.total_cycles > 0
        assert result.stop_reason is not None

    def test_harness_tracks_s_star(self):
        """Harness tracks succession horizon."""
        config = ALSConfig(max_cycles=200)
        harness = ALSHarness(seed=42, config=config)

        result = harness.run()

        # S* should equal non-trivial endorsements
        assert result.s_star == result.non_trivial_endorsements

    def test_harness_detects_endorsement_degeneracy(self):
        """Harness detects endorsement degeneracy."""
        # Configure to quickly hit degeneracy
        config = ALSConfig(
            max_cycles=200,
            degeneracy_window=50,
        )

        harness = ALSHarness(seed=42, config=config)
        result = harness.run()

        # Either hits degeneracy or horizon
        assert result.stop_reason in (
            ALSStopReason.HORIZON_EXHAUSTED,
            ALSStopReason.ENDORSEMENT_DEGENERACY,
            ALSStopReason.SPAM_DEGENERACY,
        )

    def test_harness_records_events(self):
        """Harness records succession events."""
        config = ALSConfig(max_cycles=50)
        harness = ALSHarness(seed=42, config=config)

        result = harness.run()

        assert len(result.succession_events) > 0

        # Check event structure
        event = result.succession_events[0]
        assert event.cycle > 0
        assert event.candidate_id is not None

    def test_harness_reproducible(self):
        """Same seed produces same results."""
        config = ALSConfig(max_cycles=100)

        result1 = ALSHarness(seed=42, config=config).run()
        result2 = ALSHarness(seed=42, config=config).run()

        assert result1.s_star == result2.s_star
        assert result1.total_endorsements == result2.total_endorsements
        assert result1.stop_reason == result2.stop_reason

    def test_harness_different_seeds(self):
        """Different seeds may produce different results."""
        config = ALSConfig(max_cycles=100)

        result1 = ALSHarness(seed=42, config=config).run()
        result2 = ALSHarness(seed=999, config=config).run()

        # Results might differ (probabilistically)
        # At minimum, run_id should differ
        assert result1.run_id != result2.run_id


class TestRunALSExperiment:
    """Tests for run_als_experiment convenience function."""

    def test_convenience_function(self):
        """run_als_experiment works."""
        result = run_als_experiment(seed=42, max_cycles=50)

        assert result is not None
        assert result.seed == 42
        assert result.total_cycles <= 50


class TestALSResultSerialization:
    """Tests for result serialization."""

    def test_result_to_dict(self):
        """Result can be serialized to dict."""
        result = run_als_experiment(seed=42, max_cycles=50)

        d = result.to_dict()

        assert "run_id" in d
        assert "s_star" in d
        assert "stop_reason" in d
        assert "succession_events" in d

    def test_events_serialize(self):
        """Events serialize correctly."""
        result = run_als_experiment(seed=42, max_cycles=50)

        d = result.to_dict()

        if d["succession_events"]:
            event = d["succession_events"][0]
            assert "cycle" in event
            assert "endorsed" in event


# =============================================================================
# Integration: Corridor Unchanged
# =============================================================================

class TestCorridorUnchanged:
    """Verify corridor imports work (no modifications)."""

    def test_kernel_imports(self):
        """Kernel modules import without error."""
        from toy_aki.kernel.watchdog import current_time_ms
        from toy_aki.kernel.policy_gate import KernelPolicy
        from toy_aki.kernel.reflective import KernelState

        assert current_time_ms() > 0

    def test_acv_imports(self):
        """ACV modules import without error."""
        from toy_aki.acv.anchor import Anchor, AnchorRegistry
        from toy_aki.acv.verify import VerificationResult, verify_commitment_reveal

        assert Anchor is not None
        assert AnchorRegistry is not None
        assert VerificationResult is not None

    def test_harness_imports(self):
        """V0.3 harness imports without error."""
        from toy_aki.harness.v032_runner import V032ExperimentRunner
        from toy_aki.harness.v032_matrix import V032RunMatrix

        assert V032ExperimentRunner is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
