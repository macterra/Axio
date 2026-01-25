"""RSA-PoC v1.2 Run 1: Assistant Enabled

Tests whether the formal assistant can eliminate schema/ID/canonicalization
failures while preserving sensitivity to A/B/C audits.

v1.2 uses the v1.1 Run 4 generator as the baseline generator distribution.

Expected outcomes:
- Schema failures (E_NONCANONICAL_REFERENCE, E_INSTITUTION_FAILURE) -> ~0
- A/B/C audit failures should remain when LLM mispredicts semantics
- Rule D should never trigger (assistant doesn't tamper)
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Set, List, Optional
import copy

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
    from rsa_poc.v100.state.normative import NormativeStateV100
    from rsa_poc.v120.generator.llm_v1 import LLMGeneratorV120
    from rsa_poc.v120.jcomp.compiler import JCOMP120
    from rsa_poc.v120.tools.artifact_store import ArtifactStore
    from rsa_poc.v120.tools.formal_assistant import FormalAssistant
except ImportError as e:
    print(f"Import error: {e}")
    print("Ensure PYTHONPATH includes src directory")
    sys.exit(1)


# Canonical preferences from CommitmentTrapV100
PREFERENCE_REGISTRY = frozenset({
    "P_NO_DEFECT", "P_NO_BREAK_LOCKS", "P_NO_LIE",
    "P_NO_HOARD", "P_NO_EXPLOIT", "P_PREFER_COOPERATION"
})

# All 10 actions from the environment
ACTION_INVENTORY = frozenset({
    "WAIT", "COOPERATE", "DEFECT", "BREAK_LOCK", "TELL_TRUTH",
    "LIE", "SHARE", "HOARD", "HELP", "EXPLOIT"
})


def compute_exists_clean(apcm: Dict[str, Dict[str, Set[str]]], feasible_actions: Set[str]) -> bool:
    """Compute whether any feasible action has no violations"""
    for action in feasible_actions:
        if action in apcm:
            if len(apcm[action].get("violates", set())) == 0:
                return True
    return False


def run_episode(
    episode_num: int,
    env: CommitmentTrapV100,
    generator: LLMGeneratorV120,
    compiler: JCOMP120,
    store: ArtifactStore,
    assistant: FormalAssistant,
    normative_state: NormativeStateV100,
    max_steps: int = 20,
    seed: int = 42
) -> Dict:
    """Run single episode WITH assistant enabled"""

    results = {
        "episode": episode_num,
        "steps": [],
        "total_steps": 0,
        "halted": False,
        "halt_reason": None,
        "violations": 0,
        "audit_failures": 0,
        "institutional_failures": 0,
        "schema_failures": 0,
        "rule_d_failures": 0,
        "assistant_rejections": 0,
    }

    # Reset
    env.reset(seed=seed + episode_num)
    generator.reset()
    store.clear()
    normative_state.reset()

    previous_digest = None

    for step in range(1, max_steps + 1):
        step_result = {
            "step": step,
            "success": False,
            "error_codes": [],
            "violations": 0,
            "assistant_applied": False,
        }

        try:
            # Get environment state
            feasible_actions = set(env.feasible_actions())
            apcm = env.get_apcm()

            # Compute exists_clean (harness truth)
            exists_clean = compute_exists_clean(apcm, feasible_actions)

            # Generate raw JAF dict (J_raw)
            j_raw = generator.generate_raw(
                feasible_actions=list(feasible_actions),
                apcm=apcm,
                exists_clean=exists_clean,
                previous_artifact_digest=previous_digest
            )

            # Compile WITH assistant
            compilation_result = compiler.compile_with_assistant(
                j_raw_dict=j_raw,
                assistant=assistant,
                apcm=apcm,
                feasible_actions=feasible_actions,
                precedent=normative_state.get_precedent()
            )

            step_result["assistant_applied"] = compilation_result.assistant_applied

            if not compilation_result.success:
                # Categorize failure
                for err in compilation_result.institutional_errors:
                    step_result["error_codes"].append(err.code)
                    if err.code == "E_TOOL_NORMATIVE_TAMPERING":
                        results["rule_d_failures"] += 1
                    elif err.code == "E_NONCANONICAL_REFERENCE":
                        results["schema_failures"] += 1
                    elif err.code == "E_INSTITUTION_FAILURE":
                        results["institutional_failures"] += 1
                        # Check if it's an assistant rejection
                        if "rejection_reason" in str(err.details):
                            results["assistant_rejections"] += 1

                for err in compilation_result.errors:
                    step_result["error_codes"].append(err.code)
                    results["audit_failures"] += 1

                results["halted"] = True
                results["halt_reason"] = step_result["error_codes"]
                results["steps"].append(step_result)
                results["total_steps"] = step
                break

            # Success - pick action and step
            allowed_actions = feasible_actions - (compilation_result.action_mask or set())
            if allowed_actions:
                selected_action = sorted(allowed_actions)[0]
            else:
                selected_action = sorted(feasible_actions)[0]

            _, reward, done, _, info = env.step(selected_action)

            # Count violations
            if "violated_prefs" in info:
                step_result["violations"] = len(info["violated_prefs"])
                results["violations"] += len(info["violated_prefs"])

            # Update precedent from J_final
            j_final = compilation_result.j_final_dict
            normative_state.update_precedent({
                "authorized_violations": set(j_final.get("authorized_violations", [])),
                "required_preservations": set(j_final.get("required_preservations", [])),
                "conflict_attribution": {tuple(p) for p in j_final.get("conflict_attribution", [])},
            })

            # Store artifact
            previous_digest = store.append(j_final)

            step_result["success"] = True
            results["steps"].append(step_result)
            results["total_steps"] = step

            if done:
                break

        except Exception as e:
            step_result["error_codes"].append(f"EXCEPTION: {type(e).__name__}: {str(e)}")
            results["halted"] = True
            results["halt_reason"] = step_result["error_codes"]
            results["steps"].append(step_result)
            results["total_steps"] = step
            break

    return results


def main():
    """Run v1.2 with assistant enabled"""

    print("=" * 60)
    print("RSA-PoC v1.2 Run 1: Assistant ENABLED")
    print("=" * 60)
    print()
    print("This run tests whether the formal assistant eliminates")
    print("schema/ID failures while preserving A/B/C audit sensitivity.")
    print()

    # Check LLM environment
    if not os.getenv("LLM_PROVIDER") or not os.getenv("LLM_MODEL"):
        print("ERROR: LLM_PROVIDER and LLM_MODEL must be set")
        print("Example: LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514")
        sys.exit(1)

    print(f"LLM Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"LLM Model: {os.getenv('LLM_MODEL')}")
    print()

    # Configuration
    num_episodes = 5
    max_steps = 20
    seed = 42

    # Initialize components
    env = CommitmentTrapV100()
    normative_state = NormativeStateV100()
    generator = LLMGeneratorV120(normative_state)
    compiler = JCOMP120(ACTION_INVENTORY, PREFERENCE_REGISTRY)
    store = ArtifactStore()
    assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

    # Run episodes
    all_results = []

    for ep in range(1, num_episodes + 1):
        print(f"Episode {ep}/{num_episodes}...")

        result = run_episode(
            episode_num=ep,
            env=env,
            generator=generator,
            compiler=compiler,
            store=store,
            assistant=assistant,
            normative_state=normative_state,
            max_steps=max_steps,
            seed=seed
        )

        all_results.append(result)

        status = "HALTED" if result["halted"] else "COMPLETED"
        print(f"  {status}: {result['total_steps']} steps, "
              f"{result['violations']} violations, "
              f"{result['audit_failures']} audit, "
              f"{result['schema_failures']} schema, "
              f"{result['rule_d_failures']} Rule D")

        if result["halted"]:
            print(f"  Halt reason: {result['halt_reason']}")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_steps = sum(r["total_steps"] for r in all_results)
    total_violations = sum(r["violations"] for r in all_results)
    total_audit_failures = sum(r["audit_failures"] for r in all_results)
    total_schema_failures = sum(r["schema_failures"] for r in all_results)
    total_rule_d = sum(r["rule_d_failures"] for r in all_results)
    total_rejections = sum(r["assistant_rejections"] for r in all_results)
    episodes_completed = sum(1 for r in all_results if not r["halted"])

    print(f"Episodes completed: {episodes_completed}/{num_episodes}")
    print(f"Total steps: {total_steps}/{num_episodes * max_steps}")
    print(f"Total violations: {total_violations}")
    print(f"Total audit failures: {total_audit_failures}")
    print(f"Total schema failures: {total_schema_failures}")
    print(f"Total Rule D failures: {total_rule_d}")
    print(f"Total assistant rejections: {total_rejections}")

    survival_steps = [r["total_steps"] for r in all_results]
    median_survival = sorted(survival_steps)[len(survival_steps) // 2]
    print(f"Median survival: {median_survival} steps")

    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), "docs")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "run_1_assistant_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "version": "v1.2",
            "run": "1_assistant",
            "assistant_enabled": True,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "episodes": num_episodes,
                "max_steps": max_steps,
                "seed": seed,
                "llm_provider": os.getenv("LLM_PROVIDER"),
                "llm_model": os.getenv("LLM_MODEL"),
            },
            "summary": {
                "episodes_completed": episodes_completed,
                "total_steps": total_steps,
                "total_violations": total_violations,
                "total_audit_failures": total_audit_failures,
                "total_schema_failures": total_schema_failures,
                "total_rule_d_failures": total_rule_d,
                "total_assistant_rejections": total_rejections,
                "median_survival": median_survival,
            },
            "episodes": all_results,
        }, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")

    print()
    print("=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    print()
    print("Expected outcomes:")
    print("- Schema failures should be ~0 (assistant canonicalizes)")
    print("- Rule D failures should be 0 (assistant doesn't tamper)")
    print("- A/B/C audit failures may occur (semantic misprediction)")
    print("- Assistant rejections show LLM generating invalid IDs")
    print()

    if total_schema_failures == 0 and total_rule_d == 0:
        print("✅ SUCCESS: Institutional layer working as designed")
    elif total_rule_d > 0:
        print("❌ FAILURE: Rule D violations indicate assistant tampering bug")
    else:
        print("⚠️ PARTIAL: Some schema failures remain")


if __name__ == "__main__":
    main()
