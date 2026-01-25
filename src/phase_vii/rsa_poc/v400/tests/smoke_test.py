"""
RSA-PoC v4.0 — Quick Smoke Test
Verify basic functionality before running calibration.
"""

import sys
sys.path.insert(0, '/home/david/Axio/src/rsa_poc')

def test_dsl():
    """Test DSL validators."""
    from v400.core.dsl import (
        JustificationV400,
        Claim,
        Predicate,
        create_initial_rules,
        canonicalize,
        content_hash,
    )

    # Test justification creation
    j = JustificationV400(
        action_id="A0",
        rule_refs=["R1"],
        claims=[Claim(predicate=Predicate.PERMITS, args=["R1", "A0"])]
    )

    d = j.to_dict()
    assert d["action_id"] == "A0"
    assert len(d["rule_refs"]) == 1

    # Test initial rules
    rules = create_initial_rules()
    assert len(rules) == 4
    assert rules[0].id == "R1"
    assert rules[0].expires_episode == 1

    # Test canonicalization
    c = canonicalize({"b": 1, "a": 2})
    assert c == '{"a":2,"b":1}'

    # Test hash
    h = content_hash({"test": 123})
    assert len(h) == 16

    print("✓ DSL tests passed")


def test_norm_state():
    """Test NormState operations."""
    from v400.core.norm_state import (
        create_initial_norm_state,
        apply_patch,
        expire_rules,
    )
    from v400.core.dsl import NormPatchV400, PatchOp, Rule, RuleType, Condition, ConditionOp, Effect, ActionClass

    # Create initial state
    state = create_initial_norm_state()
    assert state.rev == 0
    assert len(state.rules) == 4
    assert state.has_rule("R1")

    # Test expiration
    expired = expire_rules(state, 2)  # R1 expires at episode 1
    assert not expired.has_rule("R1")
    assert len(expired.rules) == 3

    print("✓ NormState tests passed")


def test_environment():
    """Test TriDemandV400 environment."""
    from v400.env.tri_demand import TriDemandV400, Action, POSITIONS

    env = TriDemandV400(seed=42)
    obs = env.reset(episode=0)

    assert obs.agent_pos == POSITIONS["START"]
    assert obs.inventory == 0
    assert obs.zone_a_demand == 1

    # Test movement
    obs, reward, done, info = env.step(Action.MOVE_N)
    assert obs.agent_pos[0] == 3  # Moved north from row 4

    # Test render
    grid_str = env.render()
    assert "@" in grid_str

    print("✓ Environment tests passed")


def test_compiler():
    """Test JCOMP-4.0 compiler."""
    from v400.core.compiler import JCOMP400, CompilationStatus
    from v400.core.norm_state import create_initial_norm_state

    state = create_initial_norm_state()
    compiler = JCOMP400(state)

    # Valid justification
    valid_json = '{"action_id": "A0", "rule_refs": ["R4"], "claims": [{"predicate": "PERMITS", "args": ["R4", "A0"]}]}'
    result = compiler.compile(valid_json)
    assert result.status == CompilationStatus.COMPILED

    # Invalid JSON
    result = compiler.compile("not json")
    assert result.status == CompilationStatus.PARSE_ERROR

    # Missing rule reference
    invalid_ref = '{"action_id": "A0", "rule_refs": ["R99"], "claims": [{"predicate": "PERMITS", "args": ["R99", "A0"]}]}'
    result = compiler.compile(invalid_ref)
    assert result.status == CompilationStatus.REFERENCE_ERROR

    print("✓ Compiler tests passed")


def test_oracle():
    """Test Oracle deliberator."""
    from v400.core.oracle import OracleDeliberator
    from v400.core.norm_state import create_initial_norm_state
    from v400.env.tri_demand import TriDemandV400

    env = TriDemandV400(seed=42)
    obs = env.reset(episode=0)

    state = create_initial_norm_state()
    delib = OracleDeliberator()

    output = delib.deliberate(obs, state)
    assert len(output.justifications) >= 1
    assert output.justifications[0].action_id is not None

    print("✓ Oracle tests passed")


def test_harness():
    """Test MVRSA-4.0 harness with Oracle."""
    from v400.core.harness import MVRSA400
    from v400.core.oracle import OracleDeliberator

    delib = OracleDeliberator()
    agent = MVRSA400(deliberator=delib, seed=42, max_episodes=1)

    metrics = agent.run()
    assert metrics.episodes == 1
    assert metrics.total_steps > 0

    print("✓ Harness tests passed")


def main():
    print("=" * 50)
    print("RSA-PoC v4.0 — Smoke Test")
    print("=" * 50)
    print()

    try:
        test_dsl()
        test_norm_state()
        test_environment()
        test_compiler()
        test_oracle()
        test_harness()

        print()
        print("=" * 50)
        print("All smoke tests PASSED ✓")
        print("=" * 50)
        return 0
    except Exception as e:
        print()
        print("=" * 50)
        print(f"FAILED: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
