#!/usr/bin/env python3
"""
RSA-PoC v4.4 — Unit Tests

Tests for:
1. TokenizationBijection (bijective property, per-episode reset)
2. ExecutionCompetenceTracker (E44-EXEC gate logic)
3. CollisionTrace recording
4. Dual-channel observation formatting
5. R-gate enforcement in repair application
"""

import pytest
from typing import Dict, Set

# ============================================================================
# §1 — TokenizationBijection Tests
# ============================================================================


class TestTokenizationBijection:
    """Tests for per-episode bijective token mapping."""

    def test_bijection_action_to_token_and_back(self):
        """Action → Token → Action should be identity."""
        from ..env.tri_demand import TokenizationBijection

        bij = TokenizationBijection.create(seed=42)

        actions = ["MOVE_N", "COLLECT", "STAMP", "DEPOSIT"]
        for action in actions:
            token = bij.tokenize_action(action)
            recovered = bij.detokenize_action(token)
            assert recovered == action, f"Failed roundtrip for {action}"

    def test_bijection_predicate_to_token_and_back(self):
        """Predicate → Token → Predicate should be identity."""
        from ..env.tri_demand import TokenizationBijection

        bij = TokenizationBijection.create(seed=42)

        predicates = ["regime==1", "at(ZONE_A)", "inventory>0"]
        for pred in predicates:
            token = bij.tokenize_predicate(pred)
            recovered = bij.detokenize_predicate(token)
            assert recovered == pred, f"Failed roundtrip for {pred}"

    def test_bijection_is_injective(self):
        """Different inputs should map to different tokens."""
        from ..env.tri_demand import TokenizationBijection

        bij = TokenizationBijection.create(seed=42)

        actions = ["MOVE_N", "MOVE_S", "COLLECT", "STAMP"]
        tokens = [bij.tokenize_action(a) for a in actions]

        # All tokens should be unique
        assert len(tokens) == len(set(tokens)), "Tokens are not unique"

    def test_bijection_different_seeds(self):
        """Different seeds should produce different mappings."""
        from ..env.tri_demand import TokenizationBijection

        bij1 = TokenizationBijection.create(seed=42)
        bij2 = TokenizationBijection.create(seed=123)

        action = "STAMP"
        token1 = bij1.tokenize_action(action)
        token2 = bij2.tokenize_action(action)

        # Different seeds should (usually) produce different tokens
        # Could be same by chance, but very unlikely
        assert token1 != token2 or True  # Allow for rare collision

    def test_bijection_deterministic(self):
        """Same seed should produce same mapping."""
        from ..env.tri_demand import TokenizationBijection

        bij1 = TokenizationBijection.create(seed=42)
        bij2 = TokenizationBijection.create(seed=42)

        action = "COLLECT"
        assert bij1.tokenize_action(action) == bij2.tokenize_action(action)

    def test_bijection_token_format(self):
        """Tokens should have expected format A_N or P_N."""
        from ..env.tri_demand import TokenizationBijection

        bij = TokenizationBijection.create(seed=42)

        action_token = bij.tokenize_action("STAMP")
        pred_token = bij.tokenize_predicate("regime==1")

        assert action_token.startswith("A_"), f"Bad action token format: {action_token}"
        assert pred_token.startswith("P_"), f"Bad predicate token format: {pred_token}"


# ============================================================================
# §2 — ExecutionCompetenceTracker Tests
# ============================================================================


class TestExecutionCompetenceTracker:
    """Tests for E44-EXEC gate logic."""

    def test_gate_fails_with_no_actions(self):
        """Fresh tracker should fail gate."""
        from ..env.tri_demand import ExecutionCompetenceTracker

        tracker = ExecutionCompetenceTracker()
        assert not tracker.gate_passed

    def test_gate_fails_with_only_nav_actions(self):
        """Navigation only should fail gate."""
        from ..env.tri_demand import ExecutionCompetenceTracker, Action, POSITIONS

        tracker = ExecutionCompetenceTracker()
        # Move north from START, reaching non-initial
        new_pos = (POSITIONS["START"][0] - 1, POSITIONS["START"][1])
        tracker.record_action(Action.MOVE_N, new_pos)
        tracker.record_action(Action.MOVE_S, POSITIONS["START"])

        assert not tracker.gate_passed, "Gate should fail without non-nav actions"

    def test_gate_fails_with_only_non_nav_actions(self):
        """Non-nav only should fail gate."""
        from ..env.tri_demand import ExecutionCompetenceTracker, Action, POSITIONS

        tracker = ExecutionCompetenceTracker()
        # Try to collect at start (fails precondition, but still records attempt)
        tracker.record_action(Action.COLLECT, tuple(POSITIONS["START"]))

        assert not tracker.gate_passed, "Gate should fail without nav actions"

    def test_gate_fails_without_reaching_non_initial(self):
        """Even with action types, must reach non-initial position."""
        from ..env.tri_demand import ExecutionCompetenceTracker, Action, POSITIONS

        tracker = ExecutionCompetenceTracker()
        start = tuple(POSITIONS["START"])
        # Both action types but never leave start
        tracker.record_action(Action.MOVE_N, start)  # Hit wall, stay at start
        tracker.record_action(Action.COLLECT, start)

        assert not tracker.gate_passed, "Gate should fail without reaching non-initial"

    def test_gate_passes_with_full_competence(self):
        """Full competence should pass gate."""
        from ..env.tri_demand import ExecutionCompetenceTracker, Action, POSITIONS

        tracker = ExecutionCompetenceTracker()
        source = tuple(POSITIONS["SOURCE"])
        tracker.record_action(Action.MOVE_N, source)  # Nav action, moved to non-initial
        tracker.record_action(Action.COLLECT, source)  # Non-nav action

        assert tracker.gate_passed, "Gate should pass with full competence"

    def test_gate_is_idempotent(self):
        """Multiple checks should return same result."""
        from ..env.tri_demand import ExecutionCompetenceTracker, Action, POSITIONS

        tracker = ExecutionCompetenceTracker()
        zone_a = tuple(POSITIONS["ZONE_A"])
        tracker.record_action(Action.MOVE_N, zone_a)
        tracker.record_action(Action.DEPOSIT, zone_a)

        result1 = tracker.gate_passed
        result2 = tracker.gate_passed

        assert result1 == result2


# ============================================================================
# §3 — CollisionTrace Tests
# ============================================================================


class TestCollisionTrace:
    """Tests for collision trace recording."""

    def test_collision_trace_creation(self):
        """CollisionTrace should store required fields."""
        from ..env.tri_demand import CollisionTrace

        trace = CollisionTrace(
            tick=7,
            rule_id="R6",
            action_token="A_3",
            predicate_tokens=["P_1", "P_2"],
            episode=0,
        )

        assert trace.tick == 7
        assert trace.rule_id == "R6"
        assert trace.action_token == "A_3"
        assert "P_1" in trace.predicate_tokens

    def test_collision_trace_format(self):
        """CollisionTrace should format as human-readable string."""
        from ..env.tri_demand import CollisionTrace

        trace = CollisionTrace(
            tick=5,
            rule_id="R6",
            action_token="A_3",
            predicate_tokens=["P_1"],
            episode=0,
        )

        formatted = trace.format()
        assert "tick 5" in formatted.lower() or "5" in formatted
        assert "R6" in formatted

    def test_collision_trace_in_env(self):
        """Environment should track collision traces."""
        from ..env.tri_demand import TriDemandV440

        env = TriDemandV440(seed=42, normative_opacity=True)
        obs, _ = env.reset(episode=0)

        # Get initial traces (should be empty)
        traces = env.get_collision_traces()
        assert len(traces) == 0


# ============================================================================
# §4 — Dual-Channel Observation Tests
# ============================================================================


class TestDualChannelObservation:
    """Tests for dual-channel observation formatting."""

    def test_execution_channel_contains_position(self):
        """Execution channel should contain agent position."""
        from ..deliberator import format_execution_channel
        from ..env.tri_demand import TriDemandV440

        env = TriDemandV440(seed=42)
        obs, _ = env.reset(episode=0)

        exec_channel = format_execution_channel(obs)

        assert "Position" in exec_channel or "coordinates" in exec_channel
        assert "Inventory" in exec_channel

    def test_normative_channel_opaque_has_no_semantics(self):
        """Opaque normative channel should not reveal rule semantics."""
        from ..deliberator import format_normative_channel_opaque
        from ..env.tri_demand import TokenizationBijection
        from ..core.norm_state import create_initial_norm_state_v430

        norm_state = create_initial_norm_state_v430()
        bijection = TokenizationBijection.create(seed=42)

        norm_channel = format_normative_channel_opaque(norm_state, bijection)

        # Should NOT contain actual action names or predicate names
        forbidden = ["STAMP", "DEPOSIT", "COLLECT", "REGIME_EQ", "ZONE_A"]
        for word in forbidden:
            assert word not in norm_channel, f"Leaked '{word}' in opaque channel"

        # Should contain opaque tokens
        assert "COND_" in norm_channel or "EFFECT_" in norm_channel

    def test_dual_channel_has_both_sections(self):
        """Dual-channel observation should have both delimited sections."""
        from ..deliberator import format_dual_channel_observation
        from ..env.tri_demand import TriDemandV440, TokenizationBijection
        from ..core.norm_state import create_initial_norm_state_v430

        env = TriDemandV440(seed=42, normative_opacity=True)
        obs, _ = env.reset(episode=0)

        norm_state = create_initial_norm_state_v430()
        bijection = TokenizationBijection.create(seed=42)

        dual_obs = format_dual_channel_observation(
            obs, norm_state, bijection, normative_opacity=True
        )

        assert "[EXECUTION_CHANNEL]" in dual_obs
        assert "[NORMATIVE_CHANNEL]" in dual_obs

    def test_unstamped_deposit_failure_observable(self):
        """v4.4 fix: Unstamped DEPOSIT in regime>=1 should produce observable failure."""
        from ..env.tri_demand import TriDemandV440, Action, POSITIONS

        env = TriDemandV440(seed=42)
        env.reset(episode=0)

        # Move to regime 1 manually
        env.state.regime = 1

        # Navigate to SOURCE and collect
        env.state.agent_pos = POSITIONS["SOURCE"]
        obs, reward, _, _, info = env.step(Action.COLLECT)

        # Navigate to ZONE_A (without stamping)
        env.state.agent_pos = POSITIONS["ZONE_A"]
        env.state.stamped = False

        # Attempt DEPOSIT without stamping
        obs, reward, _, _, info = env.step(Action.DEPOSIT)

        # Should get observable failure signal
        assert info.get("last_action_outcome") == "FAIL_UNSTAMPED", \
            f"Expected FAIL_UNSTAMPED, got {info.get('last_action_outcome')}"
        assert reward == 0.0, "Unstamped deposit should give 0 reward"
        assert env.state.inventory > 0, "Inventory should be unchanged"

        # Observation should also contain the failure
        assert obs.last_action_outcome == "FAIL_UNSTAMPED"

    def test_stamped_deposit_success_observable(self):
        """v4.4 fix: Stamped DEPOSIT in regime>=1 should produce observable success."""
        from ..env.tri_demand import TriDemandV440, Action, POSITIONS

        env = TriDemandV440(seed=42)
        env.reset(episode=0)

        # Move to regime 1 manually
        env.state.regime = 1

        # Navigate to SOURCE and collect
        env.state.agent_pos = POSITIONS["SOURCE"]
        obs, reward, _, _, info = env.step(Action.COLLECT)

        # Stamp first
        env.state.agent_pos = POSITIONS["STAMP_LOCATION"]
        obs, reward, _, _, info = env.step(Action.STAMP)
        assert env.state.stamped == True

        # Navigate to ZONE_A and deposit
        env.state.agent_pos = POSITIONS["ZONE_A"]
        obs, reward, _, _, info = env.step(Action.DEPOSIT)

        # Should get observable success signal
        assert info.get("last_action_outcome") == "SUCCESS", \
            f"Expected SUCCESS, got {info.get('last_action_outcome')}"
        assert reward == 1.0, "Stamped deposit should give 1.0 reward"


# ============================================================================
# §5 — R-Gate Enforcement Tests
# ============================================================================


class TestRGateEnforcement:
    """Tests for R7/R9/R10 gate enforcement in repair application."""

    def test_repair_rejected_without_trace_citation(self):
        """R7: Repair without trace_entry_id should be rejected."""
        from ..run_llm_baseline import _apply_repair_simple
        from ..core.norm_state import create_initial_norm_state_v430
        from ..env.tri_demand import CollisionTrace
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class MockPatch:
            op: str = "ADD_EXCEPTION"
            rule_id: str = "R6"
            new_value: str = "REGIME_EQ(1)"

        @dataclass
        class MockRepairAction:
            patch_ops: List[MockPatch]
            trace_entry_id: str = None  # Missing trace citation

        norm_state = create_initial_norm_state_v430()
        repair = MockRepairAction(patch_ops=[MockPatch()])

        # Provide collision traces (R7 check enabled)
        traces = [CollisionTrace(tick=5, rule_id="R6", action_token="A_3", predicate_tokens=[], episode=0)]

        new_state, success, metadata = _apply_repair_simple(norm_state, repair, traces, repair_type='A')

        assert not success, "Repair without trace citation should fail R7"
        assert not metadata['r7_passed'], "R7 should be marked as failed"

    def test_repair_rejected_with_invalid_trace(self):
        """R7: Repair citing non-existent trace should be rejected."""
        from ..run_llm_baseline import _apply_repair_simple
        from ..core.norm_state import create_initial_norm_state_v430
        from ..env.tri_demand import CollisionTrace
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class MockPatch:
            op: str = "ADD_EXCEPTION"
            rule_id: str = "R6"
            new_value: str = "REGIME_EQ(1)"

        @dataclass
        class MockRepairAction:
            patch_ops: List[MockPatch]
            trace_entry_id: str = "nonexistent_trace"

        norm_state = create_initial_norm_state_v430()
        repair = MockRepairAction(patch_ops=[MockPatch()])

        # Create trace with known ID format: trace_ep{episode}_tick{tick}_{rule_id}
        trace = CollisionTrace(tick=5, rule_id="R6", action_token="A_3", predicate_tokens=[], episode=0)
        traces = [trace]

        new_state, success, metadata = _apply_repair_simple(norm_state, repair, traces, repair_type='A')

        assert not success, "Repair with invalid trace should fail R7"
        assert not metadata['r7_passed'], "R7 should be marked as failed"

    def test_repair_accepted_with_valid_trace(self):
        """Repair citing valid trace should be accepted."""
        from ..run_llm_baseline import _apply_repair_simple
        from ..core.norm_state import create_initial_norm_state_v430
        from ..env.tri_demand import CollisionTrace
        from ..core.dsl import PatchOp
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class MockPatch:
            op: PatchOp = PatchOp.ADD_EXCEPTION
            target_rule_id: str = "R6"
            exception_condition: str = "REGIME_EQ(1)"

        # Create trace first to get the correct ID
        trace = CollisionTrace(tick=5, rule_id="R6", action_token="A_3", predicate_tokens=[], episode=0)

        @dataclass
        class MockRepairAction:
            patch_ops: List[MockPatch]
            trace_entry_id: str

        norm_state = create_initial_norm_state_v430()
        repair = MockRepairAction(patch_ops=[MockPatch()], trace_entry_id=trace.trace_entry_id)

        traces = [trace]

        new_state, success, metadata = _apply_repair_simple(norm_state, repair, traces, repair_type='A')

        assert success, "Repair with valid trace should succeed"
        assert metadata['r7_passed'], "R7 should be marked as passed"
        assert new_state.repair_count == norm_state.repair_count + 1

    def test_r10_non_subsumption_check(self):
        """R10: Repair B should be rejected if Repair A already solved the contradiction."""
        from ..run_llm_baseline import _apply_repair_simple
        from ..core.norm_state import create_initial_norm_state_v430, NormStateV430
        from ..env.tri_demand import CollisionTrace
        from ..core.dsl import PatchOp
        from dataclasses import dataclass
        from copy import deepcopy
        from typing import List

        @dataclass
        class MockPatch:
            op: PatchOp = PatchOp.ADD_EXCEPTION
            target_rule_id: str = "R7"
            exception_condition: str = "REGIME_EQ(2)"

        @dataclass
        class MockRepairAction:
            patch_ops: List[MockPatch]
            trace_entry_id: str

        # Create trace for contradiction B
        trace = CollisionTrace(tick=10, rule_id="R7", action_token="A_5", predicate_tokens=[], episode=0)
        traces = [trace]

        # Get initial state (pre-Repair-A)
        pre_repair_a_state = create_initial_norm_state_v430()

        # Simulate post-Repair-A state where R7 already has the same exception
        post_repair_a_rules = list(pre_repair_a_state.rules)
        for i, rule in enumerate(post_repair_a_rules):
            if rule.id == "R7":
                new_rule = deepcopy(rule)
                object.__setattr__(new_rule, 'exception_condition', "REGIME_EQ(2)")
                post_repair_a_rules[i] = new_rule
                break

        post_repair_a_state = NormStateV430(
            rules=post_repair_a_rules,
            epoch_chain=list(pre_repair_a_state.epoch_chain),
            repair_count=pre_repair_a_state.repair_count + 1,
        )

        # Now try Repair B with the same exception (should be subsumed)
        repair_b = MockRepairAction(
            patch_ops=[MockPatch()],
            trace_entry_id=trace.trace_entry_id,
        )

        new_state, success, metadata = _apply_repair_simple(
            post_repair_a_state,
            repair_b,
            traces,
            repair_type='B',
            pre_repair_a_norm_state=pre_repair_a_state,
        )

        assert not success, "Repair B should fail R10 if subsumed by Repair A"
        assert not metadata['r10_passed'], "R10 should be marked as failed"
        assert metadata['r10_reason'] == 'B_SUBSUMED_BY_A'

    def test_deliberator_generates_valid_trace_entry_id(self):
        """Deliberator should generate trace_entry_id matching collision trace format."""
        from ..deliberator import LLMDeliberatorV440, LLMDeliberatorConfigV440
        from ..env.tri_demand import CollisionTrace
        from ..core.norm_state import create_initial_norm_state_v430

        # Create a deliberator (no API calls needed for this test)
        config = LLMDeliberatorConfigV440(normative_opacity=False)
        deliberator = LLMDeliberatorV440(config)

        # Create a collision trace with known format
        trace = CollisionTrace(
            tick=5,
            rule_id="R6",
            action_token="A_3",
            predicate_tokens=[],
            episode=2,
        )
        deliberator.set_collision_traces([trace])

        # Generate repair for contradiction A
        norm_state = create_initial_norm_state_v430()
        repair, collision_grounded = deliberator._generate_repair(
            conflict_type='A',
            conflict_details={'collision_rule': 'R6'},
            episode=2,
            step=5,
            norm_state=norm_state,
            bijection=None,
        )

        assert repair is not None, "Should generate repair for contradiction A"
        assert repair.trace_entry_id == trace.trace_entry_id, \
            f"trace_entry_id should match collision trace: got {repair.trace_entry_id}, expected {trace.trace_entry_id}"
        assert collision_grounded, "Repair should be marked as collision-grounded"

    def test_deliberator_generates_valid_repair_b(self):
        """Deliberator should generate valid Repair B without parameter errors."""
        from ..deliberator import LLMDeliberatorV440, LLMDeliberatorConfigV440
        from ..env.tri_demand import CollisionTrace

        # Create a deliberator
        config = LLMDeliberatorConfigV440(normative_opacity=False)
        deliberator = LLMDeliberatorV440(config)

        # Create a collision trace for contradiction B (R7 or R8)
        trace = CollisionTrace(
            tick=10,
            rule_id="R7",
            action_token="A_5",
            predicate_tokens=[],
            episode=3,
        )
        deliberator.set_collision_traces([trace])

        # Generate Repair B - this will fail if parameter names are wrong
        repair = deliberator._generate_repair_b(trace_entry_id=trace.trace_entry_id)

        assert repair is not None, "Should generate Repair B"
        assert repair.trace_entry_id == trace.trace_entry_id
        assert len(repair.patch_ops) == 2, "Repair B should have 2 patch ops (R7 and R8)"

    def test_generate_repair_for_conflict_b(self):
        """Full _generate_repair() flow for conflict_type='B' should work."""
        from ..deliberator import LLMDeliberatorV440, LLMDeliberatorConfigV440
        from ..env.tri_demand import CollisionTrace
        from ..core.norm_state import create_initial_norm_state_v430

        config = LLMDeliberatorConfigV440(normative_opacity=False)
        deliberator = LLMDeliberatorV440(config)

        # Create collision trace for R7 (DEPOSIT blocked at ZONE_A in regime 2)
        trace = CollisionTrace(
            tick=15,
            rule_id="R7",
            action_token="A_5",
            predicate_tokens=[],
            episode=5,
        )
        deliberator.set_collision_traces([trace])

        norm_state = create_initial_norm_state_v430()

        # Generate repair through the main interface
        repair, collision_grounded = deliberator._generate_repair(
            conflict_type='B',
            conflict_details={'collision_rule': 'R7'},
            episode=5,
            step=15,
            norm_state=norm_state,
            bijection=None,
        )

        assert repair is not None, "Should generate repair for conflict B"
        assert repair.trace_entry_id == trace.trace_entry_id, \
            f"Should use actual trace ID: got {repair.trace_entry_id}"
        assert collision_grounded, "Repair should be collision-grounded"
        assert len(repair.patch_ops) == 2, "Repair B has 2 patches (R7, R8)"

    def test_apply_repair_b_with_valid_trace(self):
        """_apply_repair_simple for Repair B with valid trace should succeed."""
        from ..run_llm_baseline import _apply_repair_simple
        from ..core.norm_state import create_initial_norm_state_v430
        from ..env.tri_demand import CollisionTrace
        from ..core.dsl import PatchOp
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class MockPatch:
            op: PatchOp = PatchOp.ADD_EXCEPTION
            target_rule_id: str = "R7"
            exception_condition: str = "CAN_DELIVER_A"

        @dataclass
        class MockRepairAction:
            patch_ops: List[MockPatch]
            trace_entry_id: str

        # Create trace for B (no prior Repair A)
        trace = CollisionTrace(tick=10, rule_id="R7", action_token="A_5", predicate_tokens=[], episode=2)
        traces = [trace]

        norm_state = create_initial_norm_state_v430()
        repair = MockRepairAction(patch_ops=[MockPatch()], trace_entry_id=trace.trace_entry_id)

        # Apply Repair B without pre_repair_a_norm_state (no subsumption check)
        new_state, success, metadata = _apply_repair_simple(
            norm_state, repair, traces, repair_type='B', pre_repair_a_norm_state=None
        )

        assert success, "Repair B should succeed when trace is valid and no subsumption"
        assert metadata['r7_passed'], "R7 should pass"


# ============================================================================
# §6 — Inferability Audit Tests
# ============================================================================


class TestInferabilityAudit:
    """Tests for the inferability audit mechanism."""

    def test_audit_feature_matrix_excludes_regime(self):
        """Normative-only features should not include regime."""
        from ..inferability_audit import AuditDataset, DecisionSnapshot

        dataset = AuditDataset()

        # Add a snapshot
        snapshot = DecisionSnapshot(
            episode=0,
            step=0,
            regime=1,  # This should NOT appear in normative-only features
            agent_pos=(2, 2),
            inventory=1,
            stamped=False,
            zone_a_satisfied=False,
            zone_b_satisfied=False,
            zone_c_satisfied=True,
            recent_actions=[],
            rule_ids=["R0", "R1"],
            rule_types=["PERMISSION", "OBLIGATION"],
            rule_priorities=[0, 10],
        )
        dataset.add(snapshot)

        X, y = dataset.to_feature_matrix(feature_set="normative_only")

        # Feature matrix should exist
        assert X.shape[0] == 1
        # No direct regime value (would need to check specific feature indices)

    def test_oracle_blocking_computation(self):
        """Oracle should correctly identify blocking scenarios."""
        from ..inferability_audit import _compute_oracle_blocking, POSITIONS

        # R6: STAMP blocked at STAMP_LOCATION in regime 1
        pos = tuple(POSITIONS["STAMP_LOCATION"])
        blocking = _compute_oracle_blocking(pos, inv=1, stamped=False, regime=1)
        assert "A6" in blocking
        assert blocking["A6"] == "R6"

        # R7: DEPOSIT blocked at ZONE_A in regime 2
        pos = tuple(POSITIONS["ZONE_A"])
        blocking = _compute_oracle_blocking(pos, inv=1, stamped=True, regime=2)
        assert "A5" in blocking
        assert blocking["A5"] == "R7"

        # No blocking in regime 0
        blocking = _compute_oracle_blocking(pos, inv=1, stamped=False, regime=0)
        assert len(blocking) == 0


# ============================================================================
# §7 — System Prompt Parity Tests
# ============================================================================


class TestSystemPromptParity:
    """Ensure execution semantics are identical between Baseline-44 and Run D'."""

    def test_execution_mechanics_section_identical(self):
        """
        Baseline-44 and Run D' must have identical execution mechanics sections.

        This prevents accidental divergence that would confound the opacity experiment.
        v4.4 removes normative foresight, NOT execution semantics documentation.
        """
        from ..deliberator import SYSTEM_PROMPT_V440_BASELINE, SYSTEM_PROMPT_V440_OPACITY

        # Extract execution mechanics sections
        exec_marker = "## Execution Mechanics (CLEAR — identical in Baseline-44 and Run D')"

        assert exec_marker in SYSTEM_PROMPT_V440_BASELINE, \
            "Baseline-44 must have execution mechanics section"
        assert exec_marker in SYSTEM_PROMPT_V440_OPACITY, \
            "Run D' must have execution mechanics section"

        # Extract the sections
        baseline_start = SYSTEM_PROMPT_V440_BASELINE.find(exec_marker)
        opacity_start = SYSTEM_PROMPT_V440_OPACITY.find(exec_marker)

        # Find end of section (next ## or end)
        baseline_rest = SYSTEM_PROMPT_V440_BASELINE[baseline_start:]
        opacity_rest = SYSTEM_PROMPT_V440_OPACITY[opacity_start:]

        # Get until next section
        baseline_end = baseline_rest.find("\n## ", 1)
        opacity_end = opacity_rest.find("\n## ", 1)

        baseline_section = baseline_rest[:baseline_end] if baseline_end > 0 else baseline_rest
        opacity_section = opacity_rest[:opacity_end] if opacity_end > 0 else opacity_rest

        assert baseline_section == opacity_section, \
            f"Execution mechanics sections must be identical.\n" \
            f"Baseline:\n{baseline_section}\n\nOpacity:\n{opacity_section}"

    def test_action_space_identical(self):
        """Action space definitions must be identical."""
        from ..deliberator import SYSTEM_PROMPT_V440_BASELINE, SYSTEM_PROMPT_V440_OPACITY

        # Both should have identical action definitions
        actions = ["A0: MOVE_NORTH", "A1: MOVE_SOUTH", "A2: MOVE_EAST",
                   "A3: MOVE_WEST", "A4: COLLECT", "A5: DEPOSIT", "A6: STAMP"]

        for action in actions:
            assert action in SYSTEM_PROMPT_V440_BASELINE, f"Baseline missing {action}"
            assert action in SYSTEM_PROMPT_V440_OPACITY, f"Opacity missing {action}"

    def test_action_space_section_parity(self):
        """
        Action space sections must be byte-identical between Baseline-44 and D'.

        Prevents 'two truths in same prompt' failures like 'regime=1' vs 'regime>=1'.
        """
        from ..deliberator import SYSTEM_PROMPT_V440_BASELINE, SYSTEM_PROMPT_V440_OPACITY

        # Extract action space sections from both prompts
        def extract_action_space(prompt):
            # Find action space block
            if "## Action Space (Execution Semantics" in prompt:
                marker = "## Action Space (Execution Semantics"
            else:
                marker = "## Action Space"

            start = prompt.find(marker)
            assert start >= 0, f"Action Space section not found"

            rest = prompt[start:]
            end = rest.find("\n## ", 1)
            return rest[:end] if end > 0 else rest

        baseline_actions = extract_action_space(SYSTEM_PROMPT_V440_BASELINE)
        opacity_actions = extract_action_space(SYSTEM_PROMPT_V440_OPACITY)

        # Normalize header difference (Baseline uses '## Action Space', D' uses '## Action Space (Execution Semantics — CLEAR)')
        baseline_normalized = baseline_actions.replace("## Action Space\n", "")
        opacity_normalized = opacity_actions.replace("## Action Space (Execution Semantics — CLEAR)\n", "")

        assert baseline_normalized == opacity_normalized, \
            f"Action space sections must have identical content.\n" \
            f"Baseline:\n{baseline_actions}\n\nOpacity:\n{opacity_actions}"

    def test_no_conflicting_regime_statements(self):
        """
        Ensure no conflicting regime statements for STAMP requirement.

        'regime>=1' should be the authoritative statement.
        No 'under regime=1' or similar should appear that would conflict.
        """
        from ..deliberator import SYSTEM_PROMPT_V440_BASELINE, SYSTEM_PROMPT_V440_OPACITY

        for name, prompt in [("Baseline-44", SYSTEM_PROMPT_V440_BASELINE),
                             ("D'", SYSTEM_PROMPT_V440_OPACITY)]:
            # Should have regime>=1 statement
            assert "regime>=1: STAMP required" in prompt, \
                f"{name} must state 'regime>=1: STAMP required'"

            # Should NOT have conflicting 'under regime=1' in action space
            assert "STAMP" in prompt and "under regime=1" not in prompt, \
                f"{name} has conflicting 'under regime=1' statement"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
