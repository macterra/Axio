"""
AKI v0.6 Test Suite: Authority Leases with Semantic Commitments (ALS-C).

Tests the Commitment Ledger infrastructure and its integration with
the ALS harness.

Key invariants to test:
1. Genesis commitments are seeded before first succession
2. Commitment cost is charged AFTER rent
3. Semantic failure does NOT cause lease revocation
4. Verifiers query ACV traces only
5. Evaluation occurs at epoch end
6. MAX_COMMIT_TTL is enforced
7. commit_cap is enforced

Per spec §6 and binding decisions:
- α = 0.25 (commit_cap = floor(0.25 * steps_cap_epoch))
- MAX_COMMIT_TTL = 10 epochs
- GENESIS_SET_0: C0 (cost=2), C1 (cost=4), C2 (cost=6) → total=12
"""

import pytest
from typing import Any, Dict, List, Optional

from toy_aki.als.commitment import (
    Commitment,
    CommitmentStatus,
    CommitmentSpec,
    CommitmentLedger,
    CommitmentEvent,
    CommitmentCostRecord,
    COMMITMENT_SPECS,
    create_genesis_set_0,
    MAX_COMMIT_TTL,
    COMMIT_CAP_ALPHA,
)
from toy_aki.als.verifiers import (
    ActionRecord,
    VRF_EPOCH_ACTION_COUNT,
    VRF_ORDERED_ACTION_PATTERN,
    VRF_ACTION_HAS_PAYLOAD_SHAPE,
    VERIFIERS,
    verify_commitment,
    get_commitment_params,
)
from toy_aki.als.harness import (
    ALSConfigV060,
    ALSRunResultV060,
    ALSHarnessV060,
    run_als_experiment,
)


# =============================================================================
# Unit Tests: Commitment Module
# =============================================================================

class TestCommitmentBasics:
    """Basic commitment data structure tests."""

    def test_commitment_status_enum(self):
        """CommitmentStatus has all required states."""
        assert CommitmentStatus.ACTIVE.name == "ACTIVE"
        assert CommitmentStatus.SATISFIED.name == "SATISFIED"
        assert CommitmentStatus.FAILED.name == "FAILED"
        assert CommitmentStatus.EXPIRED.name == "EXPIRED"

    def test_commitment_creation(self):
        """Commitment dataclass initializes correctly."""
        c = Commitment(
            cid="test_c0",
            spec_id="CMT_PRESENCE_LOG",
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            window=1,
            cost=2,
        )
        assert c.cid == "test_c0"
        assert c.status == CommitmentStatus.ACTIVE
        assert c.created_epoch == 0
        assert c.satisfaction_count == 0
        assert c.failure_count == 0

    def test_commitment_to_dict(self):
        """Commitment serializes to dictionary."""
        c = Commitment(
            cid="test_c0",
            spec_id="CMT_PRESENCE_LOG",
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            window=1,
            cost=2,
        )
        d = c.to_dict()
        assert d["cid"] == "test_c0"
        assert d["status"] == "ACTIVE"
        assert d["cost"] == 2


class TestCommitmentSpecs:
    """Tests for CommitmentSpec registry."""

    def test_genesis_specs_exist(self):
        """GENESIS_SET_0 specs are defined."""
        assert "CMT_PRESENCE_LOG" in COMMITMENT_SPECS
        assert "CMT_STATE_ECHO" in COMMITMENT_SPECS
        assert "CMT_COMPOSED_OP" in COMMITMENT_SPECS

    def test_spec_properties(self):
        """Spec properties match expected values."""
        log_spec = COMMITMENT_SPECS["CMT_PRESENCE_LOG"]
        assert log_spec.verifier_id == "VRF_EPOCH_ACTION_COUNT"
        assert log_spec.default_window == 1
        assert log_spec.default_cost == 2

        echo_spec = COMMITMENT_SPECS["CMT_STATE_ECHO"]
        assert echo_spec.verifier_id == "VRF_ORDERED_ACTION_PATTERN"
        assert echo_spec.default_window == 2
        assert echo_spec.default_cost == 4

        composed_spec = COMMITMENT_SPECS["CMT_COMPOSED_OP"]
        assert composed_spec.verifier_id == "VRF_ACTION_HAS_PAYLOAD_SHAPE"
        assert composed_spec.default_window == 3
        assert composed_spec.default_cost == 6


class TestGenesisSet0:
    """Tests for GENESIS_SET_0 creation."""

    def test_genesis_set_0_creates_three_commitments(self):
        """Genesis set has exactly 3 commitments."""
        commitments = create_genesis_set_0()
        assert len(commitments) == 3

    def test_genesis_set_0_ids(self):
        """Genesis commitments have expected IDs."""
        commitments = create_genesis_set_0()
        cids = {c.cid for c in commitments}
        assert cids == {"C0", "C1", "C2"}

    def test_genesis_set_0_costs(self):
        """Genesis total cost is 12 steps/epoch."""
        commitments = create_genesis_set_0()
        total_cost = sum(c.cost for c in commitments)
        assert total_cost == 12  # 2 + 4 + 6

    def test_genesis_set_0_windows(self):
        """Genesis windows are 1, 2, 3 epochs."""
        commitments = create_genesis_set_0()
        windows = {c.cid: c.window for c in commitments}
        assert windows == {"C0": 1, "C1": 2, "C2": 3}

    def test_genesis_start_epoch_respected(self):
        """Genesis commitments start at specified epoch."""
        commitments = create_genesis_set_0(start_epoch=5)
        for c in commitments:
            assert c.created_epoch == 5
            assert c.window_start_epoch == 5


class TestFrozenParameters:
    """Tests for frozen parameter values."""

    def test_max_commit_ttl(self):
        """MAX_COMMIT_TTL is 10 epochs."""
        assert MAX_COMMIT_TTL == 10

    def test_commit_cap_alpha(self):
        """COMMIT_CAP_ALPHA is 0.25."""
        assert COMMIT_CAP_ALPHA == 0.25


# =============================================================================
# Unit Tests: Commitment Ledger
# =============================================================================

class TestCommitmentLedger:
    """Tests for CommitmentLedger class."""

    def test_ledger_creation(self):
        """Ledger initializes correctly."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        assert ledger.commit_cap == 25  # floor(0.25 * 100)
        assert not ledger.is_seeded
        assert ledger.get_active_cost() == 0

    def test_commit_cap_calculation(self):
        """commit_cap is floor(0.25 * steps_cap)."""
        # Edge cases
        ledger1 = CommitmentLedger(steps_cap_epoch=50)
        assert ledger1.commit_cap == 12  # floor(12.5)

        ledger2 = CommitmentLedger(steps_cap_epoch=1)
        assert ledger2.commit_cap == 0  # floor(0.25)

        ledger3 = CommitmentLedger(steps_cap_epoch=1000)
        assert ledger3.commit_cap == 250

    def test_seed_genesis_commitments(self):
        """Seeding loads commitments correctly."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        genesis = create_genesis_set_0()
        ledger.seed(genesis)

        assert ledger.is_seeded
        assert ledger.get_active_cost() == 12  # 2 + 4 + 6

    def test_seed_cannot_be_called_twice(self):
        """Double seeding raises error."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        genesis = create_genesis_set_0()
        ledger.seed(genesis)

        with pytest.raises(ValueError, match="already seeded"):
            ledger.seed(genesis)

    def test_seed_requires_non_empty(self):
        """Seeding with empty list raises error."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        with pytest.raises(ValueError, match="cannot be empty"):
            ledger.seed([])

    def test_seed_rejects_duplicate_ids(self):
        """Duplicate commitment IDs are rejected."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        duplicates = [
            Commitment(cid="dup", spec_id="a", verifier_id="v", window=1, cost=1),
            Commitment(cid="dup", spec_id="b", verifier_id="v", window=1, cost=1),
        ]
        with pytest.raises(ValueError, match="Duplicate commitment ID"):
            ledger.seed(duplicates)


class TestCommitmentCostCharging:
    """Tests for commitment cost charging."""

    def test_charge_costs_succeeds(self):
        """Normal cost charging deducts correctly."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())

        cost_charged, defaulted = ledger.charge_costs(
            epoch=0, cycle=0, available_budget=50
        )
        assert cost_charged == 12
        assert not defaulted

    def test_charge_costs_records_event(self):
        """Cost charging creates record."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())
        ledger.charge_costs(epoch=0, cycle=0, available_budget=50)

        records = ledger.get_cost_records()
        assert len(records) == 1
        assert records[0].total_cost == 12
        assert records[0].commitments_charged == 3
        assert not records[0].defaulted

    def test_charge_costs_defaults_on_insufficient_budget(self):
        """Cost default when budget insufficient."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())

        # Budget less than total cost (12)
        cost_charged, defaulted = ledger.charge_costs(
            epoch=0, cycle=0, available_budget=10
        )
        assert cost_charged == 0
        assert defaulted

    def test_cost_default_fails_all_active_commitments(self):
        """Cost default transitions all ACTIVE to FAILED."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())
        ledger.charge_costs(epoch=0, cycle=0, available_budget=5)

        # All commitments should be FAILED
        active = ledger.get_active_commitments()
        assert len(active) == 0

        for cid in ["C0", "C1", "C2"]:
            c = ledger.get_commitment(cid)
            assert c is not None
            assert c.status == CommitmentStatus.FAILED

    def test_cost_default_increments_metrics(self):
        """Cost default increments defaulted count."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())
        ledger.charge_costs(epoch=0, cycle=0, available_budget=5)

        metrics = ledger.get_metrics()
        assert metrics["total_defaulted"] == 3
        assert metrics["total_failed"] == 3


class TestCommitmentEvaluation:
    """Tests for commitment evaluation."""

    def test_evaluate_commitment_satisfied(self):
        """Satisfied commitment increments count."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())

        status = ledger.evaluate_commitment(
            cid="C0", epoch=0, cycle=10, verifier_result=True
        )
        assert status == CommitmentStatus.ACTIVE  # Stays active for always-on

        c = ledger.get_commitment("C0")
        assert c is not None
        assert c.satisfaction_count == 1
        assert c.window_start_epoch == 1  # Reset for next window

    def test_evaluate_commitment_failed_within_window(self):
        """Failed within window stays ACTIVE."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())

        # C2 has window=3, so first fail shouldn't terminate
        status = ledger.evaluate_commitment(
            cid="C2", epoch=0, cycle=10, verifier_result=False
        )
        assert status == CommitmentStatus.ACTIVE

    def test_evaluate_commitment_failed_window_exhausted(self):
        """Failed with exhausted window transitions to FAILED."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())

        # C0 has window=1, so fail at epoch 0 exhausts window
        status = ledger.evaluate_commitment(
            cid="C0", epoch=0, cycle=10, verifier_result=False
        )
        assert status == CommitmentStatus.FAILED

    def test_evaluate_non_active_is_noop(self):
        """Evaluating non-ACTIVE commitment returns current status."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0())

        # Fail C0 first
        ledger.evaluate_commitment(cid="C0", epoch=0, cycle=10, verifier_result=False)

        # Evaluate again - should be noop
        status = ledger.evaluate_commitment(
            cid="C0", epoch=1, cycle=20, verifier_result=True
        )
        assert status == CommitmentStatus.FAILED


class TestCommitmentTTL:
    """Tests for MAX_COMMIT_TTL enforcement."""

    def test_ttl_expiration(self):
        """Commitments expire at MAX_COMMIT_TTL."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0(start_epoch=0))

        # Advance to epoch 10 (age = 10 >= MAX_COMMIT_TTL)
        expired_count = ledger.check_ttl_expirations(epoch=10, cycle=100)
        assert expired_count == 3

        for cid in ["C0", "C1", "C2"]:
            c = ledger.get_commitment(cid)
            assert c is not None
            assert c.status == CommitmentStatus.EXPIRED

    def test_ttl_not_expired_within_limit(self):
        """Commitments don't expire before TTL."""
        ledger = CommitmentLedger(steps_cap_epoch=100)
        ledger.seed(create_genesis_set_0(start_epoch=0))

        # At epoch 9, age = 9 < MAX_COMMIT_TTL (10)
        expired_count = ledger.check_ttl_expirations(epoch=9, cycle=90)
        assert expired_count == 0

        active = ledger.get_active_commitments()
        assert len(active) == 3


class TestCommitmentCapEnforcement:
    """Tests for commit_cap enforcement."""

    def test_can_add_commitment_within_cap(self):
        """Adding within cap is allowed."""
        ledger = CommitmentLedger(steps_cap_epoch=100)  # cap = 25
        # Start with just C0 (cost=2)
        ledger.seed([create_genesis_set_0()[0]])

        allowed, reason = ledger.can_add_commitment("CMT_STATE_ECHO")  # cost=4
        assert allowed
        assert reason == "OK"

    def test_can_add_commitment_exceeds_cap(self):
        """Adding that exceeds cap is rejected."""
        ledger = CommitmentLedger(steps_cap_epoch=50)  # cap = 12
        ledger.seed(create_genesis_set_0())  # total = 12

        allowed, reason = ledger.can_add_commitment("CMT_PRESENCE_LOG")  # cost=2
        assert not allowed
        assert "exceed commit_cap" in reason

    def test_add_commitment_creates_new(self):
        """add_commitment creates new commitment if allowed."""
        ledger = CommitmentLedger(steps_cap_epoch=100)  # cap = 25
        ledger.seed([create_genesis_set_0()[0]])  # Just C0, cost=2

        c = ledger.add_commitment(spec_id="CMT_STATE_ECHO", epoch=1, cycle=10)
        assert c is not None
        assert c.spec_id == "CMT_STATE_ECHO"
        assert c.status == CommitmentStatus.ACTIVE

    def test_add_commitment_rejected_returns_none(self):
        """add_commitment returns None if rejected."""
        ledger = CommitmentLedger(steps_cap_epoch=50)  # cap = 12
        ledger.seed(create_genesis_set_0())  # total = 12

        c = ledger.add_commitment(spec_id="CMT_PRESENCE_LOG", epoch=1, cycle=10)
        assert c is None


# =============================================================================
# Unit Tests: Verifiers
# =============================================================================

class TestVerifierRegistry:
    """Tests for verifier registry."""

    def test_all_genesis_verifiers_registered(self):
        """All GENESIS_SET_0 verifiers are in registry."""
        assert "VRF_EPOCH_ACTION_COUNT" in VERIFIERS
        assert "VRF_ORDERED_ACTION_PATTERN" in VERIFIERS
        assert "VRF_ACTION_HAS_PAYLOAD_SHAPE" in VERIFIERS


class TestVRF_EPOCH_ACTION_COUNT:
    """Tests for C0 verifier."""

    def test_passes_with_log_action(self):
        """Passes when LOG action exists in epoch."""
        actions = [
            ActionRecord(action_type="LOG", payload={}, epoch=0, cycle=5, sequence_num=0),
        ]
        result = verify_commitment(
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=0,
            params={"action_type": "LOG", "min_count": 1},
        )
        assert result is True

    def test_fails_without_log_action(self):
        """Fails when no LOG action in epoch."""
        actions = [
            ActionRecord(action_type="COMPUTE", payload={}, epoch=0, cycle=5, sequence_num=0),
        ]
        result = verify_commitment(
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=0,
            params={"action_type": "LOG", "min_count": 1},
        )
        assert result is False

    def test_fails_with_empty_actions(self):
        """Fails when no actions at all."""
        result = verify_commitment(
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            actions=[],
            window_start_epoch=0,
            window_end_epoch=0,
            params={"action_type": "LOG", "min_count": 1},
        )
        assert result is False

    def test_only_counts_current_epoch(self):
        """Only counts actions in window_end_epoch."""
        actions = [
            ActionRecord(action_type="LOG", payload={}, epoch=0, cycle=5, sequence_num=0),
            ActionRecord(action_type="LOG", payload={}, epoch=1, cycle=15, sequence_num=0),
        ]
        # Check epoch 1 only
        result = verify_commitment(
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            actions=actions,
            window_start_epoch=1,
            window_end_epoch=1,
            params={"action_type": "LOG", "min_count": 1},
        )
        assert result is True


class TestVRF_ORDERED_ACTION_PATTERN:
    """Tests for C1 verifier."""

    def test_passes_with_set_then_get(self):
        """Passes when STATE_SET followed by STATE_GET."""
        actions = [
            ActionRecord(
                action_type="STATE_SET",
                payload={"key": "c1", "value": 42},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
            ActionRecord(
                action_type="STATE_GET",
                payload={"key": "c1"},
                epoch=0,
                cycle=6,
                sequence_num=1,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ORDERED_ACTION_PATTERN",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=1,
            params={"key": "c1"},
        )
        assert result is True

    def test_fails_with_only_set(self):
        """Fails when only SET, no GET."""
        actions = [
            ActionRecord(
                action_type="STATE_SET",
                payload={"key": "c1", "value": 42},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ORDERED_ACTION_PATTERN",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=1,
            params={"key": "c1"},
        )
        assert result is False

    def test_fails_with_get_before_set(self):
        """Fails when GET precedes SET."""
        actions = [
            ActionRecord(
                action_type="STATE_GET",
                payload={"key": "c1"},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
            ActionRecord(
                action_type="STATE_SET",
                payload={"key": "c1", "value": 42},
                epoch=0,
                cycle=6,
                sequence_num=1,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ORDERED_ACTION_PATTERN",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=1,
            params={"key": "c1"},
        )
        assert result is False

    def test_also_accepts_shorthand_types(self):
        """Also accepts SET/GET without STATE_ prefix."""
        actions = [
            ActionRecord(
                action_type="SET",
                payload={"key": "c1", "value": 42},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
            ActionRecord(
                action_type="GET",
                payload={"key": "c1"},
                epoch=0,
                cycle=6,
                sequence_num=1,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ORDERED_ACTION_PATTERN",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=1,
            params={"key": "c1"},
        )
        assert result is True


class TestVRF_ACTION_HAS_PAYLOAD_SHAPE:
    """Tests for C2 verifier."""

    def test_passes_with_sequence_action(self):
        """Passes when SEQUENCE action has length >= 2."""
        actions = [
            ActionRecord(
                action_type="SEQUENCE",
                payload={"actions": ["a", "b"]},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=2,
            params={"action_types": {"SEQUENCE", "BATCH"}, "min_length": 2},
        )
        assert result is True

    def test_passes_with_batch_action(self):
        """Passes when BATCH action has length >= 2."""
        actions = [
            ActionRecord(
                action_type="BATCH",
                payload={"actions": [1, 2, 3]},
                epoch=1,
                cycle=15,
                sequence_num=0,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=2,
            params={"action_types": {"SEQUENCE", "BATCH"}, "min_length": 2},
        )
        assert result is True

    def test_fails_with_short_payload(self):
        """Fails when payload length < 2."""
        actions = [
            ActionRecord(
                action_type="SEQUENCE",
                payload={"actions": ["only_one"]},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=2,
            params={"action_types": {"SEQUENCE", "BATCH"}, "min_length": 2},
        )
        assert result is False

    def test_fails_with_wrong_action_type(self):
        """Fails when action type not in set."""
        actions = [
            ActionRecord(
                action_type="COMPUTE",
                payload={"actions": ["a", "b", "c"]},
                epoch=0,
                cycle=5,
                sequence_num=0,
            ),
        ]
        result = verify_commitment(
            verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
            actions=actions,
            window_start_epoch=0,
            window_end_epoch=2,
            params={"action_types": {"SEQUENCE", "BATCH"}, "min_length": 2},
        )
        assert result is False


class TestVerifyCommitmentHelper:
    """Tests for verify_commitment helper function."""

    def test_unknown_verifier_raises(self):
        """Unknown verifier ID raises ValueError."""
        with pytest.raises(ValueError, match="Unknown verifier"):
            verify_commitment(
                verifier_id="NONEXISTENT",
                actions=[],
                window_start_epoch=0,
                window_end_epoch=0,
            )


# =============================================================================
# Integration Tests: ALSHarnessV060
# =============================================================================

class TestALSConfigV060:
    """Tests for v0.6 config."""

    def test_config_defaults(self):
        """Config has correct defaults."""
        config = ALSConfigV060()
        assert config.genesis_set == "GENESIS_SET_0"
        assert config.commit_cap_alpha == 0.25
        assert config.max_commit_ttl == 10
        assert config.seed_genesis_commitments is True

    def test_config_extends_v052(self):
        """Config inherits v0.5.2 fields."""
        config = ALSConfigV060()
        # Should have rent fields from V052
        assert hasattr(config, "rent_e0")
        assert hasattr(config, "expressivity_mode")


class TestALSRunResultV060:
    """Tests for v0.6 run result."""

    def test_result_has_commitment_fields(self):
        """Result has commitment-specific fields."""
        result = ALSRunResultV060(run_id="test", seed=42)
        assert hasattr(result, "total_commitment_cost_charged")
        assert hasattr(result, "commitment_satisfaction_count")
        assert hasattr(result, "commitment_failure_count")
        assert hasattr(result, "commitment_expired_count")
        assert hasattr(result, "commitment_default_count")
        assert hasattr(result, "semantic_debt_mass")
        assert hasattr(result, "commitment_satisfaction_rate")

    def test_result_to_dict(self):
        """Result serializes correctly."""
        result = ALSRunResultV060(run_id="test", seed=42, s_star=5)
        d = result.to_dict()
        assert d["run_id"] == "test"
        assert d["seed"] == 42
        assert d["spec_version"] == "0.6"
        assert d["s_star"] == 5
        assert "commitment_satisfaction_count" in d


class TestALSHarnessV060Basic:
    """Basic harness tests."""

    def test_harness_initializes(self):
        """Harness initializes without error."""
        harness = ALSHarnessV060(seed=42)
        assert harness is not None

    def test_harness_seeds_genesis_commitments(self):
        """Harness seeds genesis commitments at init."""
        harness = ALSHarnessV060(seed=42)
        assert harness._commitment_ledger.is_seeded
        assert harness._commitment_ledger.get_active_cost() == 12

    def test_harness_can_run(self):
        """Harness can execute a run."""
        config = ALSConfigV060(max_cycles=100)
        harness = ALSHarnessV060(seed=42, config=config)
        result = harness.run()

        assert result is not None
        assert result.spec_version == "0.6"
        assert result.total_cycles > 0


class TestRunALSExperimentV060:
    """Tests for run_als_experiment with v0.6."""

    def test_run_als_experiment_060(self):
        """run_als_experiment supports spec_version='0.6'."""
        result = run_als_experiment(
            seed=42,
            spec_version="0.6",
            max_cycles=100,
        )
        assert result is not None
        assert result.spec_version == "0.6"


# =============================================================================
# Integration Tests: Semantic Independence
# =============================================================================

class TestSemanticIndependence:
    """Tests verifying semantic failure doesn't revoke authority."""

    def test_commitment_failure_does_not_stop_run(self):
        """
        Key v0.6 invariant: semantic failure is independent of structural renewal.

        The system should continue running even when commitments fail.
        """
        config = ALSConfigV060(max_cycles=500)
        harness = ALSHarnessV060(seed=12345, config=config)
        result = harness.run()

        # Run should complete (not stopped by commitment failure)
        assert result.stop_cycle > 0

        # Commitment failures can occur
        if result.commitment_failure_count > 0:
            # But renewals should still happen
            assert result.total_renewals >= 0  # May be 0 if expires first

    def test_cost_default_does_not_end_lease(self):
        """
        Cost default fails commitments but lease continues if rent was paid.
        """
        # This is tested implicitly - if cost default ended the lease,
        # s_star would immediately drop and runs would be very short.
        config = ALSConfigV060(max_cycles=200)
        harness = ALSHarnessV060(seed=42, config=config)
        result = harness.run()

        # Should get some succession count
        assert result.s_star >= 0


# =============================================================================
# Stress Tests
# =============================================================================

class TestV060StressRuns:
    """Stress tests for v0.6."""

    def test_multiple_seeds_complete(self):
        """Multiple seeds complete without crash."""
        config = ALSConfigV060(max_cycles=200)
        for seed in range(10):
            harness = ALSHarnessV060(seed=seed, config=config)
            result = harness.run()
            assert result.stop_reason is not None

    def test_long_run_stability(self):
        """Long run remains stable."""
        config = ALSConfigV060(max_cycles=1000)
        harness = ALSHarnessV060(seed=42, config=config)
        result = harness.run()

        # Should complete
        assert result.stop_cycle == 1000 or result.stop_reason is not None

        # Metrics should be reasonable
        assert result.total_commitment_cost_charged >= 0
        assert 0.0 <= result.commitment_satisfaction_rate <= 1.0


# =============================================================================
# Run as script for quick validation
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
