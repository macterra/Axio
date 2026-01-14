#!/usr/bin/env python3
"""
Simple debug script - run one sovereign step and analyze failure.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rsa_poc.v100.state.normative import NormativeStateV100
from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v200.compiler_ext.compiler import JCOMP200
from rsa_poc.v200.generator.llm_v1 import LLMGeneratorV200
from rsa_poc.v200.regimes.reward_regimes import create_regime
from rsa_poc.v200.iic.incentive_record import IncentiveRecord
from rsa_poc.v120.tools.formal_assistant import FormalAssistant
from rsa_poc.v120.tools.artifact_store import ArtifactStore


def main():
    # Check API key
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: LLM_API_KEY required")
        sys.exit(1)

    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    model = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
    print(f"LLM: {provider} / {model}\n")

    # Setup
    env = CommitmentTrapV100()
    state = NormativeStateV100()
    env_actions = set(env.ACTIONS)
    env_preferences = state.get_preferences() if hasattr(state, 'get_preferences') else set()

    compiler = JCOMP200(
        valid_actions=env_actions,
        valid_preferences=env_preferences
    )

    generator = LLMGeneratorV200(normative_state=state)

    # Setup assistant with proper dependencies
    artifact_store = ArtifactStore()
    assistant = FormalAssistant(
        artifact_store=artifact_store,
        preference_registry=env_preferences,
        action_inventory=env_actions
    )

    # Create previous incentive record (simulating step t-1)
    prev_record = IncentiveRecord(
        reward_regime_id="R1",
        reward_value=0.5,
        step_id=0,
        reward_input_digest="test_digest",
        reward_function_version_id="R1_v1"
    )

    # Set it on generator
    generator.set_previous_incentive_record(prev_record)

    # Get environment observation
    obs = env.reset()
    feasible = list(env.feasible_actions())
    print(f"Feasible actions: {feasible}")

    # Build APCM
    apcm = {}
    for action in feasible:
        apcm[action] = {
            "violates": set(env.TEMPTATION_VIOLATIONS.get(action, set())),
            "satisfies": set()
        }
        # Add preference satisfactions for safe actions
        if action in env.SAFE_ACTIONS:
            apcm[action]["satisfies"].add("P_PREFER_COOPERATION")

    print(f"APCM: {apcm}")

    # Check exists_clean
    exists_clean = any(len(apcm[a]["violates"]) == 0 for a in feasible)
    print(f"exists_clean: {exists_clean}")

    # Generate raw artifact
    print("\n--- Generating artifact ---")
    try:
        j_raw = generator.generate_raw(
            feasible_actions=feasible,
            apcm=apcm,
            agent_id="MVRA_v200_debug",
            exists_clean=exists_clean,
            previous_artifact_digest="test_prev_digest"
        )
        print("\n--- Raw artifact (J_raw) ---")
        print(json.dumps(j_raw, indent=2, default=str))
    except Exception as e:
        import traceback
        print(f"\n--- GENERATION FAILED ---")
        print(f"Error: {e}")
        traceback.print_exc()
        return

    # Compile with v2.0 (includes Rule G)
    print("\n--- Compiling with JCOMP-2.0 ---")
    result = compiler.compile_with_incentives(
        j_raw_dict=j_raw,
        assistant=assistant,
        apcm=apcm,
        feasible_actions=set(feasible)
    )

    print(f"\nCompilation success: {result.success}")

    if not result.success:
        print("\n--- COMPILATION ERRORS ---")

        # Incentive errors (Rule G/H)
        if result.incentive_errors:
            print("\nIncentive errors (Rule G/H):")
            for err in result.incentive_errors:
                print(f"  Code: {err.code}")
                print(f"  Details: {err.details}")
                print()

        # Institutional errors
        if result.institutional_errors:
            print("\nInstitutional errors (D/E/F):")
            for err in result.institutional_errors:
                print(f"  Code: {err.code}")
                print(f"  Details: {err.details}")
                print()

        # Base result errors
        if hasattr(result, 'base_result') and result.base_result and hasattr(result.base_result, 'errors'):
            if result.base_result.errors:
                print("\nBase result errors:")
                for err in result.base_result.errors:
                    print(f"  Code: {err.code}")
                    print(f"  Details: {err.details}")
                    print()

        # Rule G details
        if hasattr(result, 'rule_g_passed'):
            print(f"\nRule G passed: {result.rule_g_passed}")
        if hasattr(result, 'rule_g_violations') and result.rule_g_violations:
            print(f"Rule G violations:")
            for v in result.rule_g_violations:
                print(f"  - {v}")

        # Rule H details
        if hasattr(result, 'rule_h_passed'):
            print(f"\nRule H passed: {result.rule_h_passed}")
        if hasattr(result, 'rule_h_violations') and result.rule_h_violations:
            print(f"Rule H violations:")
            for v in result.rule_h_violations:
                print(f"  - {v}")
    else:
        print("\n✓ Compilation succeeded!")
        # Access from base_result
        if hasattr(result, 'base_result') and result.base_result:
            print(f"Action: {result.base_result.action}")
            print(f"AV: {result.base_result.authorized_violations}")
            print(f"RP: {result.base_result.required_preservations}")
        else:
            print("(Details in base_result not available)")


if __name__ == "__main__":
    main()
