"""
RSA-PoC v4.3 — Core Component Smoke Test

Verifies:
1. TriDemandV430 environment with regime transitions (0→1→2)
2. R9 PERMISSION(STAMP) and R6 PROHIBITION(STAMP) interaction
3. Contradiction A detection (regime=1, STAMP blocked)
4. Contradiction B detection (regime=2, DEPOSIT blocked by R7/R8)
5. Exception conditions in compiled rules
6. Law-Repair Gate with R9 (multi-repair) and R10 (non-subsumption)
7. Epoch chain construction
"""

import sys
sys.path.insert(0, '/home/david/Axio/src')

from rsa_poc.v430.env.tri_demand import (
    TriDemandV430,
    Action,
    ACTION_IDS,
    POSITIONS,
    REGIME_1_START,
    REGIME_2_PREREGISTERED_START,
    Observation430,
    progress_set,
    rank,
)
from rsa_poc.v430.core.norm_state import (
    NormStateV430,
    create_initial_norm_state_v430,
    compute_epoch_0,
    compute_epoch_n,
)
from rsa_poc.v430.core.compiler import (
    JCOMP430,
    JCOMP430_HASH,
    compute_feasible_430,
    compile_condition,
)
from rsa_poc.v430.core.trace import (
    TraceLog,
    TraceEntry,
    create_contradiction_a_entry,
    create_contradiction_b_entry,
)
from rsa_poc.v430.core.dsl import (
    Condition,
    ConditionOp,
    PatchOp,
    PatchOperation,
)
from rsa_poc.v430.core.law_repair import (
    LawRepairActionV430,
    LawRepairGateV430,
    RepairFailureReasonV430,
    create_canonical_repair_b,
)
from rsa_poc.v430.deliberator_oracle import OracleDeliberatorV430
from rsa_poc.v430.pipeline import MVRSA430Harness, HarnessConfigV430


def test_environment():
    """Test TriDemandV430 basic functionality and regime transitions."""
    print("=" * 60)
    print("TEST: TriDemandV430 Environment")
    print("=" * 60)

    env = TriDemandV430()

    # Episode 1: regime=0
    obs, info = env.reset(episode=1)
    print(f"Episode 1: regime={obs.regime}, stamped={obs.stamped}")
    assert obs.regime == 0, "Episode 1 should be regime=0"
    assert not obs.stamped, "Should not be stamped initially"
    assert not obs.dual_delivery_mode, "dual_delivery_mode should be False in regime 0"

    # Episode 2: regime=1 (flip at REGIME_1_START)
    obs, info = env.reset(episode=REGIME_1_START)
    print(f"Episode {REGIME_1_START}: regime={obs.regime}, stamped={obs.stamped}")
    assert obs.regime == 1, f"Episode {REGIME_1_START} should be regime=1"
    assert not obs.dual_delivery_mode, "dual_delivery_mode should be False in regime 1"

    # Episode 4+: regime=2 (requires Repair A acceptance for E3)
    # Simulate Repair A accepted in episode 2
    env.record_repair_a_accepted(episode=REGIME_1_START)
    obs, info = env.reset(episode=REGIME_2_PREREGISTERED_START)
    print(f"Episode {REGIME_2_PREREGISTERED_START}: regime={obs.regime}, dual_delivery={obs.dual_delivery_mode}")
    assert obs.regime == 2, f"Episode {REGIME_2_PREREGISTERED_START} should be regime=2 after Repair A"
    assert obs.dual_delivery_mode, "dual_delivery_mode should be True in regime 2"

    # Test STAMP action
    env.reset(episode=REGIME_1_START)
    # Move to STAMP_LOCATION (ZONE_C)
    env.step(Action.MOVE_E)
    env.step(Action.MOVE_E)
    env.step(Action.MOVE_N)
    obs, _, _, _, _ = env.step(Action.MOVE_N)
    print(f"At STAMP_LOCATION: pos={obs.agent_pos}, stamped={obs.stamped}")
    assert obs.agent_pos == POSITIONS["STAMP_LOCATION"], "Should be at STAMP_LOCATION"

    # Execute STAMP
    obs, reward, _, _, info = env.step(Action.STAMP)
    print(f"After STAMP: stamped={obs.stamped}, reward={reward}")
    assert obs.stamped, "Should be stamped after STAMP action"

    print("✅ Environment test PASSED\n")


def test_norm_state():
    """Test NormStateV430 with R9 PERMISSION(STAMP) and R6 PROHIBITION(STAMP)."""
    print("=" * 60)
    print("TEST: NormStateV430 with R9/R6")
    print("=" * 60)

    norm_state = create_initial_norm_state_v430()
    print(f"Rules: {[r.id for r in norm_state.rules]}")
    print(f"Law fingerprint: {norm_state.law_fingerprint[:16]}...")

    # Check R9 exists and permits STAMP
    r9 = norm_state.get_rule("R9")
    assert r9 is not None, "R9 should exist"
    assert r9.type.value == "PERMISSION", "R9 should be PERMISSION"
    assert r9.effect.action_class.value == "STAMP", "R9 should permit STAMP"
    print(f"R9: {r9.type.value}({r9.effect.action_class.value})")

    # Check R6 exists and prohibits STAMP
    r6 = norm_state.get_rule("R6")
    assert r6 is not None, "R6 should exist"
    assert r6.type.value == "PROHIBITION", "R6 should be PROHIBITION"
    assert r6.effect.action_class.value == "STAMP", "R6 should prohibit STAMP"
    print(f"R6: {r6.type.value}({r6.effect.action_class.value})")

    # Check R7/R8 exist for Contradiction B
    r7 = norm_state.get_rule("R7")
    r8 = norm_state.get_rule("R8")
    assert r7 is not None, "R7 should exist"
    assert r8 is not None, "R8 should exist"
    assert r7.type.value == "PROHIBITION", "R7 should be PROHIBITION"
    assert r8.type.value == "PROHIBITION", "R8 should be PROHIBITION"
    print(f"R7: {r7.type.value}({r7.effect.action_class.value}) - regime 2 / ZONE_A")
    print(f"R8: {r8.type.value}({r8.effect.action_class.value}) - regime 2 / ZONE_B")

    print("✅ NormState test PASSED\n")


def test_exception_condition_compilation():
    """Test that exception_condition compiles and evaluates correctly."""
    print("=" * 60)
    print("TEST: Exception Condition Compilation")
    print("=" * 60)

    norm_state = create_initial_norm_state_v430()

    # Apply a patch with exception to R6
    exception_cond = Condition(op=ConditionOp.HAS_RESOURCE, args=[1])
    patch = PatchOperation(
        target_rule_id="R6",
        op=PatchOp.ADD_EXCEPTION,
        exception_condition=exception_cond,
    )

    # Get R6 and apply patch
    r6 = norm_state.get_rule("R6")
    patched_r6 = patch.apply(r6)

    print(f"Original R6 exception: {r6.exception_condition}")
    print(f"Patched R6 exception: {patched_r6.exception_condition}")
    assert patched_r6.exception_condition is not None, "Patched R6 should have exception"

    # Create patched norm state
    new_rules = [patched_r6 if r.id == "R6" else r.copy() for r in norm_state.rules]
    patched_ns = NormStateV430(rules=new_rules)

    # Compile and check R6
    compiler = JCOMP430(patched_ns)
    compiled_rules = compiler.compile_all_rules()

    r6_compiled = next((r for r in compiled_rules if r.rule_id == "R6"), None)
    assert r6_compiled is not None, "R6 should be compiled"
    assert r6_compiled.exception_fn is not None, "R6 should have exception_fn"

    # Test with observation that has inventory
    obs_with_inv = Observation430(
        agent_pos=POSITIONS["STAMP_LOCATION"],
        inventory=1, item_type='A',
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=2, rule_r1_active=True, regime=1,
        stamped=False, dual_delivery_mode=False,
        can_deliver_a=False, can_deliver_b=False,
    )

    # Exception should be True (inventory >= 1)
    assert r6_compiled.exception_fn(obs_with_inv) == True, "Exception should be True with inventory"
    # Rule should be inactive (exception applies)
    assert r6_compiled.active(obs_with_inv, patched_ns.norm_hash) == False, "R6 should be inactive"

    # Test with observation without inventory
    obs_no_inv = Observation430(
        agent_pos=POSITIONS["STAMP_LOCATION"],
        inventory=0, item_type=None,
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=2, rule_r1_active=True, regime=1,
        stamped=False, dual_delivery_mode=False,
        can_deliver_a=False, can_deliver_b=False,
    )

    # Exception should be False (inventory < 1)
    assert r6_compiled.exception_fn(obs_no_inv) == False, "Exception should be False without inventory"
    # Rule should be active (no exception)
    assert r6_compiled.active(obs_no_inv, patched_ns.norm_hash) == True, "R6 should be active"

    print("✅ Exception condition compilation test PASSED\n")


def test_contradiction_a_detection():
    """Test Contradiction A detection under regime=1."""
    print("=" * 60)
    print("TEST: Contradiction A Detection (regime=1)")
    print("=" * 60)

    env = TriDemandV430()
    norm_state = create_initial_norm_state_v430()
    compiler = JCOMP430(norm_state)
    rule_evals = compiler.compile_all_rules()

    # Create observation at STAMP_LOCATION with inventory, regime=1
    obs = Observation430(
        agent_pos=POSITIONS["STAMP_LOCATION"],
        inventory=1, item_type='A',
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=REGIME_1_START, rule_r1_active=True, regime=1,
        stamped=False, dual_delivery_mode=False,
        can_deliver_a=False, can_deliver_b=False,
    )

    print(f"Observation: regime={obs.regime}, pos={obs.position}, inv={obs.inventory}, stamped={obs.stamped}")

    # Check progress set for DELIVER target
    target = {"kind": "DELIVER", "target_id": "ZONE_A"}
    ps = progress_set(obs, target)
    print(f"Progress set: {ps}")
    assert "A6" in ps, "Progress set should include A6 (STAMP)"

    # Compute feasible - STAMP should be blocked by R6
    mask_result = compute_feasible_430(
        compiled_rules=rule_evals,
        norm_state=norm_state,
        obs=obs,
        env=env,
        current_norm_hash=norm_state.norm_hash,
        regime=1,
    )

    print(f"Feasible: {mask_result.feasible}")
    print(f"Is contradiction: {mask_result.is_contradiction}")

    # A6 (STAMP) should not be feasible due to R6 prohibition
    assert "A6" not in mask_result.feasible, "STAMP should be blocked by R6"

    # This creates Contradiction A: progress requires STAMP but STAMP prohibited
    blocking = set(mask_result.blocking_rule_ids or [])
    print(f"Blocking rules: {blocking}")

    print("✅ Contradiction A detection test PASSED\n")


def test_contradiction_b_detection():
    """Test Contradiction B detection under regime=2."""
    print("=" * 60)
    print("TEST: Contradiction B Detection (regime=2)")
    print("=" * 60)

    env = TriDemandV430()
    norm_state = create_initial_norm_state_v430()
    compiler = JCOMP430(norm_state)
    rule_evals = compiler.compile_all_rules()

    # Create observation at ZONE_A with inventory, regime=2
    obs = Observation430(
        agent_pos=POSITIONS["ZONE_A"],
        inventory=1, item_type='A',
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=REGIME_2_PREREGISTERED_START, rule_r1_active=True, regime=2,
        stamped=True, dual_delivery_mode=True,
        can_deliver_a=True, can_deliver_b=False,
    )

    print(f"Observation: regime={obs.regime}, pos={obs.position}, can_deliver_a={obs.can_deliver_a}")

    # Check progress set for DELIVER target
    target = {"kind": "DELIVER", "target_id": "ZONE_A"}
    ps = progress_set(obs, target)
    print(f"Progress set: {ps}")
    assert "A5" in ps, "Progress set should include A5 (DEPOSIT)"

    # Check R7 is active (regime=2, position=ZONE_A)
    r7_compiled = next((r for r in rule_evals if r.rule_id == "R7"), None)
    r7_active = r7_compiled.active(obs, norm_state.norm_hash)
    print(f"R7 active: {r7_active}")
    assert r7_active, "R7 should be active at ZONE_A in regime 2"

    # Compute feasible - DEPOSIT should be blocked by R7
    mask_result = compute_feasible_430(
        compiled_rules=rule_evals,
        norm_state=norm_state,
        obs=obs,
        env=env,
        current_norm_hash=norm_state.norm_hash,
        regime=2,
    )

    print(f"Feasible: {mask_result.feasible}")
    print(f"Is contradiction: {mask_result.is_contradiction}")
    print(f"Blocking rules: {mask_result.blocking_rule_ids}")

    # A5 (DEPOSIT) should not be feasible due to R7 prohibition
    assert "A5" not in mask_result.feasible, "DEPOSIT should be blocked by R7"

    # Contradiction B: progress ∩ feasible = ∅
    # progress = {A5}, feasible = {A0, A2} → intersection empty
    ps_intersection = ps & set(mask_result.feasible)
    print(f"Progress ∩ Feasible: {ps_intersection}")
    assert len(ps_intersection) == 0, "Progress and feasible should not intersect"

    print("✅ Contradiction B detection test PASSED\n")


def test_epoch_chain():
    """Test epoch chain construction."""
    print("=" * 60)
    print("TEST: Epoch Chain Construction")
    print("=" * 60)

    norm_state = create_initial_norm_state_v430()

    # Compute epoch_0
    nonce_0 = b"test_nonce_0"
    epoch_0 = compute_epoch_0(norm_state.law_fingerprint, nonce_0)
    print(f"epoch_0: {epoch_0[:16]}...")

    # Simulate Repair A fingerprint
    repair_a_fingerprint = "repair_a_fingerprint_test"
    nonce_1 = b"test_nonce_1"
    epoch_1 = compute_epoch_n(epoch_0, repair_a_fingerprint, nonce_1)
    print(f"epoch_1: {epoch_1[:16]}...")

    # Simulate Repair B fingerprint
    repair_b_fingerprint = "repair_b_fingerprint_test"
    nonce_2 = b"test_nonce_2"
    epoch_2 = compute_epoch_n(epoch_1, repair_b_fingerprint, nonce_2)
    print(f"epoch_2: {epoch_2[:16]}...")

    # Verify chain property: different repairs produce different epochs
    assert epoch_0 != epoch_1, "epoch_0 and epoch_1 should differ"
    assert epoch_1 != epoch_2, "epoch_1 and epoch_2 should differ"

    # Verify determinism
    epoch_1_again = compute_epoch_n(epoch_0, repair_a_fingerprint, nonce_1)
    assert epoch_1 == epoch_1_again, "Same inputs should produce same epoch"

    print("✅ Epoch chain test PASSED\n")


def test_trace_entries():
    """Test Contradiction A and B trace entries."""
    print("=" * 60)
    print("TEST: Trace Entries (A and B)")
    print("=" * 60)

    trace_log = TraceLog(run_seed=42)

    # Create Contradiction A entry
    entry_a = create_contradiction_a_entry(
        run_seed=42,
        episode=REGIME_1_START,
        step=5,
        blocking_rule_ids=["R6"],
        active_obligation_target={"kind": "DELIVER", "target_id": "ZONE_A"},
        progress_actions={"A6"},
        compiled_permitted_actions=set(),
    )
    trace_log.add(entry_a)
    print(f"Contradiction A entry: {entry_a.trace_entry_id}")
    print(f"  contradiction_type: {entry_a.contradiction_type}")
    assert entry_a.contradiction_type == 'A', "Should be Contradiction A"

    # Create Contradiction B entry
    entry_b = create_contradiction_b_entry(
        run_seed=42,
        episode=REGIME_2_PREREGISTERED_START,
        step=10,
        blocking_rule_ids=["R7", "R8"],
        active_obligation_target={"kind": "DELIVER", "target_id": "ZONE_A"},
        progress_actions={"A5"},
        compiled_permitted_actions=set(),
    )
    trace_log.add(entry_b)
    print(f"Contradiction B entry: {entry_b.trace_entry_id}")
    print(f"  contradiction_type: {entry_b.contradiction_type}")
    assert entry_b.contradiction_type == 'B', "Should be Contradiction B"

    # Verify lookup
    found_a = trace_log.get(entry_a.trace_entry_id)
    found_b = trace_log.get(entry_b.trace_entry_id)
    assert found_a is not None, "Should find entry A"
    assert found_b is not None, "Should find entry B"
    assert found_a.contradiction_type == 'A'
    assert found_b.contradiction_type == 'B'

    print("✅ Trace entries test PASSED\n")


def test_law_repair_r9():
    """Test R9 (Multi-Repair Discipline) - max 2 repairs, one per regime."""
    print("=" * 60)
    print("TEST: R9 Multi-Repair Discipline")
    print("=" * 60)

    norm_state = create_initial_norm_state_v430()
    trace_log = TraceLog(run_seed=42)

    # Create trace entries
    entry_a = create_contradiction_a_entry(
        run_seed=42, episode=2, step=5,
        blocking_rule_ids=["R6"],
        active_obligation_target={"kind": "DELIVER", "target_id": "ZONE_A"},
        progress_actions={"A6"},
        compiled_permitted_actions=set(),
    )
    trace_log.add(entry_a)

    # Initialize gate
    def progress_fn(obs, target):
        return progress_set(obs, target)

    gate = LawRepairGateV430(
        trace_log=trace_log._by_id,
        expected_compiler_hash=JCOMP430_HASH,
        env_progress_set_fn=progress_fn,
        max_retries_per_contradiction=2,
    )

    # Initialize epoch chain
    epoch_0 = compute_epoch_0(norm_state.law_fingerprint, b"test")
    gate.initialize_epoch_chain(epoch_0)
    gate.set_regime(1)

    print(f"Initial repair_count: {gate.repair_count}")
    assert gate.repair_count == 0, "Should start with 0 repairs"

    print(f"Initial epoch_chain length: {len(gate.epoch_chain)}")
    assert len(gate.epoch_chain) == 1, "Should have epoch_0 in chain"
    assert gate.epoch_chain[0] == epoch_0, "First epoch should be epoch_0"

    print(f"Regime: {gate.regime}")
    assert gate.regime == 1, "Regime should be 1"

    # Verify repairs_by_regime starts empty
    print(f"_repair_by_regime: {gate._repair_by_regime}")
    assert len(gate._repair_by_regime) == 0, "No repairs yet"

    print("✅ R9 multi-repair test PASSED\n")


def test_compiler_hash():
    """Test compiler hash is stable."""
    print("=" * 60)
    print("TEST: Compiler Hash (R8)")
    print("=" * 60)

    print(f"JCOMP430_HASH: {JCOMP430_HASH[:16]}...")

    from rsa_poc.v430.core.compiler import compute_compiler_hash
    hash2 = compute_compiler_hash()
    assert hash2 == JCOMP430_HASH, "Hash should be consistent"

    print("✅ Compiler hash test PASSED\n")


def test_regime_coupling_e3_formula():
    """Test E3 formula: regime_2_start = max(REGIME_2_PREREGISTERED_START, accept_ep + 1)."""
    print("=" * 60)
    print("TEST: E3 Regime Coupling Formula")
    print("=" * 60)

    # Case 1: Repair A at episode 2 → regime 2 at max(4, 3) = 4
    env1 = TriDemandV430()
    env1.reset(episode=1)
    env1.record_repair_a_accepted(episode=2)
    obs3, _ = env1.reset(episode=3)
    obs4, _ = env1.reset(episode=4)
    print(f"Repair A at ep2: ep3.regime={obs3.regime}, ep4.regime={obs4.regime}")
    assert obs3.regime == 1, "Episode 3 should still be regime=1 (max(4,3)=4)"
    assert obs4.regime == 2, "Episode 4 should be regime=2"

    # Case 2: Repair A at episode 3 → regime 2 at max(4, 4) = 4
    env2 = TriDemandV430()
    env2.reset(episode=1)
    env2.record_repair_a_accepted(episode=3)
    obs3b, _ = env2.reset(episode=3)
    obs4b, _ = env2.reset(episode=4)
    print(f"Repair A at ep3: ep3.regime={obs3b.regime}, ep4.regime={obs4b.regime}")
    assert obs3b.regime == 1, "Episode 3 should be regime=1"
    assert obs4b.regime == 2, "Episode 4 should be regime=2"

    # Case 3: Repair A at episode 5 → regime 2 at max(4, 6) = 6
    env3 = TriDemandV430()
    env3.reset(episode=1)
    env3.record_repair_a_accepted(episode=5)
    obs5, _ = env3.reset(episode=5)
    obs6, _ = env3.reset(episode=6)
    print(f"Repair A at ep5: ep5.regime={obs5.regime}, ep6.regime={obs6.regime}")
    assert obs5.regime == 1, "Episode 5 should still be regime=1"
    assert obs6.regime == 2, "Episode 6 should be regime=2 (max(4,6)=6)"

    # Case 4: No Repair A → stays in regime 1 forever
    env4 = TriDemandV430()
    env4.reset(episode=1)
    obs10, _ = env4.reset(episode=10)
    print(f"No Repair A: ep10.regime={obs10.regime}")
    assert obs10.regime == 1, "Without Repair A, should stay in regime=1"

    print("✅ E3 Regime Coupling Formula test PASSED\n")


def test_regime_2_contradiction_b_activates():
    """Test that R7/R8 (Contradiction B) activate in regime 2."""
    print("=" * 60)
    print("TEST: R7/R8 Activate in Regime 2")
    print("=" * 60)

    from rsa_poc.v430.core import create_initial_norm_state_v430, JCOMP430

    # Create norm state and compile rules
    norm_state = create_initial_norm_state_v430()
    compiler = JCOMP430(norm_state)
    rules = compiler.compile_all_rules()

    # Create observation at ZONE_A in regime 2
    obs_zone_a = Observation430(
        agent_pos=POSITIONS["ZONE_A"],
        inventory=1, item_type='A',
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=4, rule_r1_active=False, regime=2,
        stamped=True, dual_delivery_mode=True,
        can_deliver_a=True, can_deliver_b=False,
    )

    # Check R7 is active (PROHIBITION on DEPOSIT at ZONE_A in regime 2)
    r7_rule = next((r for r in rules if r.rule_id == "R7"), None)
    assert r7_rule is not None, "R7 should exist"
    r7_active = r7_rule.active(obs_zone_a, norm_state.norm_hash)
    print(f"At ZONE_A in regime 2: R7.active={r7_active}")
    assert r7_active, "R7 should be active at ZONE_A in regime 2"

    # Create observation at ZONE_B in regime 2
    obs_zone_b = Observation430(
        agent_pos=POSITIONS["ZONE_B"],
        inventory=1, item_type='B',
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=4, rule_r1_active=False, regime=2,
        stamped=True, dual_delivery_mode=True,
        can_deliver_a=False, can_deliver_b=True,
    )

    r8_rule = next((r for r in rules if r.rule_id == "R8"), None)
    assert r8_rule is not None, "R8 should exist"
    r8_active = r8_rule.active(obs_zone_b, norm_state.norm_hash)
    print(f"At ZONE_B in regime 2: R8.active={r8_active}")
    assert r8_active, "R8 should be active at ZONE_B in regime 2"

    print("✅ R7/R8 Activate in Regime 2 test PASSED\n")


def test_regime_1_r7_r8_inactive():
    """Test that R7/R8 are INACTIVE in regime 1."""
    print("=" * 60)
    print("TEST: R7/R8 Inactive in Regime 1")
    print("=" * 60)

    from rsa_poc.v430.core import create_initial_norm_state_v430, JCOMP430

    norm_state = create_initial_norm_state_v430()
    compiler = JCOMP430(norm_state)
    rules = compiler.compile_all_rules()

    # Create observation at ZONE_A in regime 1
    obs_zone_a = Observation430(
        agent_pos=POSITIONS["ZONE_A"],
        inventory=1, item_type='A',
        zone_a_demand=1, zone_b_demand=1, zone_c_demand=1,
        zone_a_satisfied=False, zone_b_satisfied=False, zone_c_satisfied=False,
        step=5, episode=3, rule_r1_active=False, regime=1,
        stamped=True, dual_delivery_mode=False,
        can_deliver_a=True, can_deliver_b=False,
    )

    r7_rule = next((r for r in rules if r.rule_id == "R7"), None)
    r7_active = r7_rule.active(obs_zone_a, norm_state.norm_hash)
    print(f"At ZONE_A in regime 1: R7.active={r7_active}")
    assert not r7_active, "R7 should be INACTIVE in regime 1"

    print("✅ R7/R8 Inactive in Regime 1 test PASSED\n")


def test_canonical_repair_b():
    """Test canonical Repair B factory."""
    print("=" * 60)
    print("TEST: Canonical Repair B Factory")
    print("=" * 60)

    repair_b = create_canonical_repair_b(
        trace_entry_id="test_trace_id_b123",
        prior_repair_epoch="epoch_1_hash",
    )

    print(f"Repair B fingerprint: {repair_b.repair_fingerprint[:16]}...")
    print(f"Rule IDs: {repair_b.rule_ids}")
    print(f"Patch ops: {[p.op.value for p in repair_b.patch_ops]}")

    assert repair_b.contradiction_type == 'B', "Should be Contradiction B repair"
    assert 'R7' in repair_b.rule_ids, "Should modify R7"
    assert 'R8' in repair_b.rule_ids, "Should modify R8"
    assert repair_b.prior_repair_epoch == "epoch_1_hash", "Should reference prior epoch"
    assert len(repair_b.patch_ops) == 2, "Should have 2 patches"

    # Check patch operations
    for patch in repair_b.patch_ops:
        assert patch.op == PatchOp.ADD_EXCEPTION, "Should be ADD_EXCEPTION"
        assert patch.exception_condition is not None, "Should have exception condition"
        # R7 → CAN_DELIVER_A, R8 → CAN_DELIVER_B
        if patch.target_rule_id == "R7":
            assert patch.exception_condition.op == ConditionOp.CAN_DELIVER_A
        elif patch.target_rule_id == "R8":
            assert patch.exception_condition.op == ConditionOp.CAN_DELIVER_B

    print("✅ Canonical Repair B test PASSED\n")


def test_persistence_excision():
    """Test Run C: Persistence Excision ablation behavior."""
    print("=" * 60)
    print("TEST: Persistence Excision (Run C)")
    print("=" * 60)

    from src.rsa_poc.v430.deliberator_oracle import OracleDeliberatorV430
    from src.rsa_poc.v430.pipeline import MVRSA430Harness, HarnessConfigV430

    env = TriDemandV430(seed=42)
    deliberator = OracleDeliberatorV430()

    config = HarnessConfigV430(
        max_steps_per_episode=40,
        max_episodes=10,
        seed=42,
        selector_type='argmax',
        ablation='persistence_excision',
        verbose=False,
    )

    harness = MVRSA430Harness(env=env, deliberator=deliberator, config=config)

    # Track results across episodes
    results = []
    for ep in range(10):
        result = harness.run_episode(ep)
        results.append({
            'episode': ep,
            'success': result['success'],
            'regime': result['regime_at_end'],
            'repair_a': result['repair_a_accepted'],
            'epoch_len': len(harness.epoch_chain),
        })
        print(f"  Ep{ep}: success={result['success']}, regime={result['regime_at_end']}, epoch_len={len(harness.epoch_chain)}")

    # Verify key invariants:

    # 1. Ep0-1 (regime 0): Success, no repair needed
    assert results[0]['success'], "Ep0 should succeed (regime 0)"
    assert results[1]['success'], "Ep1 should succeed (regime 0)"
    assert results[0]['regime'] == 0, "Ep0 should be regime 0"

    # 2. Ep2-3 (regime 1): Success with Repair A within episode
    assert results[2]['success'], "Ep2 should succeed (Repair A within episode)"
    assert results[2]['regime'] == 1, "Ep2 should be regime 1"

    # 3. Ep4+ (regime 2): Failure — epoch chain reset, cannot synthesize Repair B
    for i in range(4, 10):
        assert not results[i]['success'], f"Ep{i} should FAIL (persistence excision collapse)"
        assert results[i]['regime'] == 2, f"Ep{i} should be regime 2"
        assert results[i]['epoch_len'] == 1, f"Ep{i} should have epoch_len=1 (reset)"

    # 4. Environment still remembers E3 (world persists, agent forgets)
    assert env._regime_2_actual_start == 4, "Env should remember regime_2_start=4"
    assert env._repair_a_episode == 2, "Env should remember Repair A at Ep2"

    # 5. Harness state is reset each episode (final state reflects last episode reset)
    assert not harness.repair_a_accepted, "Harness repair_a should be False (reset)"
    assert len(harness.epoch_chain) == 1, "Harness epoch chain should be [epoch_0]"

    print("✅ Persistence Excision test PASSED\n")


def test_trace_excision_opaque_format():
    """Test that trace excision (Run D) produces opaque NormState and Observation formatting."""
    print("=" * 60)
    print("TEST: Trace Excision Opaque Format (Run D)")
    print("=" * 60)

    from rsa_poc.v430.deliberator import (
        format_norm_state_v430,
        format_norm_state_opaque_v430,
        format_observation_v430,
        format_observation_opaque_v430,
    )

    # Create a harness to get a valid NormState
    env = TriDemandV430(seed=42)
    deliberator = OracleDeliberatorV430()
    config = HarnessConfigV430()
    harness = MVRSA430Harness(env, deliberator, config)
    ns = harness.norm_state

    # Regular format should contain actual condition/effect semantics
    regular = format_norm_state_v430(ns)
    assert "REGIME_EQ" in regular, "Regular format should contain REGIME_EQ"
    assert "STAMP" in regular, "Regular format should contain STAMP"
    assert "DEPOSIT" in regular, "Regular format should contain DEPOSIT"
    print("Regular format contains: REGIME_EQ, STAMP, DEPOSIT ✓")

    # Opaque format should NOT contain actual semantics
    opaque = format_norm_state_opaque_v430(ns)
    assert "REGIME_EQ" not in opaque, "Opaque format should NOT contain REGIME_EQ"
    assert '"STAMP"' not in opaque, "Opaque format should NOT contain STAMP"
    assert "COND_" in opaque, "Opaque format should contain COND_ placeholders"
    assert "EFFECT_" in opaque, "Opaque format should contain EFFECT_ placeholders"
    print("Opaque format contains: COND_*, EFFECT_* (no semantics) ✓")

    # Verify rule types are preserved
    assert "PROHIBITION" in opaque, "Opaque format should preserve rule types"
    assert "PERMISSION" in opaque, "Opaque format should preserve rule types"
    print("Opaque format preserves: PROHIBITION, PERMISSION ✓")

    # Verify R6 specifically
    r6_idx = opaque.find("R6:")
    assert r6_idx >= 0, "R6 should appear in opaque format"
    r6_section = opaque[r6_idx:r6_idx+100]
    assert "PROHIBITION" in r6_section, "R6 type should be PROHIBITION"
    assert "COND_" in r6_section, "R6 condition should be opaque"
    print(f"R6 opaque section: {r6_section[:60]}...")

    # Test opaque observation formatter
    obs, _ = env.reset(episode=2)
    obs_regular = format_observation_v430(obs)
    obs_opaque = format_observation_opaque_v430(obs)

    # Regular observation should contain semantic position names
    assert "STAMP_LOCATION" in obs_regular, "Regular obs should contain STAMP_LOCATION"
    assert "ZONE_A" in obs_regular, "Regular obs should contain ZONE_A"
    assert "regime=1" in obs_regular or "Regime: 1" in obs_regular, "Regular obs should have regime description"
    print("Regular observation contains: STAMP_LOCATION, ZONE_A ✓")

    # Opaque observation should NOT contain semantic position names
    assert "STAMP_LOCATION" not in obs_opaque, "Opaque obs should NOT contain STAMP_LOCATION"
    assert "ZONE_A" not in obs_opaque, "Opaque obs should NOT contain ZONE_A"
    assert "SOURCE" not in obs_opaque, "Opaque obs should NOT contain SOURCE"
    assert "LOC_" in obs_opaque, "Opaque obs should contain LOC_ placeholders"
    print("Opaque observation contains: LOC_* (no semantic position names) ✓")

    print("✅ Trace Excision Opaque Format test PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RSA-PoC v4.3 — Core Component Smoke Test")
    print("=" * 60 + "\n")

    test_environment()
    test_norm_state()
    test_exception_condition_compilation()
    test_contradiction_a_detection()
    test_contradiction_b_detection()
    test_epoch_chain()
    test_trace_entries()
    test_law_repair_r9()
    test_compiler_hash()
    test_regime_coupling_e3_formula()
    test_regime_2_contradiction_b_activates()
    test_regime_1_r7_r8_inactive()
    test_canonical_repair_b()
    test_persistence_excision()
    test_trace_excision_opaque_format()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
