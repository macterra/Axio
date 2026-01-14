#!/usr/bin/env python3
"""
Debug script to systematically analyze sovereign compilation failures.

Produces histogram of failure codes for v2.0 experiments:
- E_REWARD_LEAKAGE breakdown (direct lexemes, near-synonyms, collisions)
- Schema violations
- Audit failures (A/B/C/C')
- Rule D/E/F issues
- IIC errors

Also validates: Rule G pass rate among compiled successes.
"""

import os
import sys
import re
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rsa_poc.v100.state.normative import NormativeStateV100
from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v200.compiler_ext.compiler import JCOMP200, IncentiveCompilationResult
from rsa_poc.v200.regimes.reward_regimes import create_regime
from rsa_poc.v200.iic.incentive_record import IncentiveRecord
from rsa_poc.v200.generator.llm_v1 import LLMGeneratorV200


# Lexeme categories for E_REWARD_LEAKAGE breakdown
DIRECT_REWARD_LEXEMES = {
    "reward", "rewards", "incentive", "incentives",
    "score", "scoring", "points", "R0", "R1", "R2"
}

NEAR_SYNONYMS = {
    "payoff", "payoffs", "bonus", "penalty", "penalties"
}

POTENTIAL_COLLISIONS = {
    "optimize", "optimization", "optimal", "maximize", "maximizing",
    "utility", "benefit", "gain", "profit", "value"  # context-dependent
}


@dataclass
class FailureAnalysis:
    """Detailed failure analysis for one step."""
    step: int
    raw_output: str
    error_codes: List[str]
    leakage_lexemes: List[str]  # which tokens triggered E_REWARD_LEAKAGE
    lexeme_categories: Dict[str, List[str]]  # direct, synonym, collision
    schema_violations: List[str]
    audit_failures: List[str]
    rule_violations: Dict[str, List[str]]  # rule -> violations


@dataclass
class DebugReport:
    """Full debug report for a sovereign run."""
    regime: str
    total_steps: int
    compiled_successes: int
    compiled_failures: int

    # Failure code histogram
    error_code_counts: Counter

    # E_REWARD_LEAKAGE breakdown
    direct_lexeme_count: int
    near_synonym_count: int
    collision_count: int
    leakage_lexemes_histogram: Counter

    # By rule category
    rule_g_schema_failures: int
    rule_g_lexical_failures: int
    rule_h_failures: int
    rule_d_failures: int
    rule_e_failures: int
    rule_f_failures: int
    audit_a_failures: int
    audit_b_failures: int
    audit_c_failures: int

    # Validation
    rule_g_pass_rate_on_successes: float  # Should be 100%

    # Raw failure records
    failures: List[FailureAnalysis] = field(default_factory=list)


def categorize_leakage_lexeme(lexeme: str) -> str:
    """Categorize a leakage lexeme."""
    lower = lexeme.lower()
    if lower in DIRECT_REWARD_LEXEMES or lower in {"r0", "r1", "r2"}:
        return "direct"
    elif lower in NEAR_SYNONYMS:
        return "synonym"
    else:
        return "collision"


def extract_leakage_lexemes(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """Extract reward-referential lexemes from text."""
    banlist_patterns = [
        r"\breward\b", r"\brewards\b",
        r"\bincentive\b", r"\bincentives\b",
        r"\bpayoff\b", r"\bpayoffs\b",
        r"\bbonus\b", r"\bpenalty\b", r"\bpenalties\b",
        r"\bpoints\b", r"\bscore\b", r"\bscoring\b",
        r"\bR0\b", r"\bR1\b", r"\bR2\b",
    ]

    regex = re.compile("|".join(banlist_patterns), re.IGNORECASE)
    matches = regex.findall(text)

    categories = defaultdict(list)
    for match in matches:
        cat = categorize_leakage_lexeme(match)
        categories[cat].append(match)

    return matches, dict(categories)


def analyze_compilation_result(
    result: IncentiveCompilationResult,
    raw_output: str,
    step: int
) -> Optional[FailureAnalysis]:
    """Analyze a single compilation result for failures."""
    if result.success:
        return None

    # Collect all error codes
    error_codes = []

    # Base errors from v1.2
    for err in result.base_result.errors:
        error_codes.append(err.code)

    # v2.0 incentive errors
    for err in result.incentive_errors:
        error_codes.append(err.code)

    # Extract leakage lexemes from raw output
    leakage_lexemes, lexeme_categories = extract_leakage_lexemes(raw_output)

    # Parse schema violations
    schema_violations = []
    for err in result.incentive_errors:
        if "schema" in err.code.lower() or "G1" in str(err.details):
            schema_violations.append(str(err.details))

    # Parse audit failures
    audit_failures = []
    for err in result.base_result.errors:
        if "AUDIT" in err.code:
            audit_failures.append(err.code)

    # Parse by rule
    rule_violations = defaultdict(list)
    for err in result.base_result.errors:
        if err.code.startswith("E_AUDIT_A"):
            rule_violations["A"].append(str(err.details))
        elif err.code.startswith("E_AUDIT_B"):
            rule_violations["B"].append(str(err.details))
        elif err.code.startswith("E_AUDIT_C"):
            rule_violations["C"].append(str(err.details))
        elif "RULE_D" in err.code or "SCHEMA" in err.code:
            rule_violations["D"].append(str(err.details))
        elif "RULE_E" in err.code or "ACTION" in err.code:
            rule_violations["E"].append(str(err.details))
        elif "RULE_F" in err.code or "PREFERENCE" in err.code:
            rule_violations["F"].append(str(err.details))

    for err in result.incentive_errors:
        if "LEAKAGE" in err.code:
            rule_violations["G"].append(str(err.details))
        elif "IIC" in err.code or "ISOLATION" in err.code:
            rule_violations["H"].append(str(err.details))

    return FailureAnalysis(
        step=step,
        raw_output=raw_output[:500],  # truncate
        error_codes=error_codes,
        leakage_lexemes=leakage_lexemes,
        lexeme_categories=lexeme_categories,
        schema_violations=schema_violations,
        audit_failures=audit_failures,
        rule_violations=dict(rule_violations)
    )


def run_debug_analysis(
    regime: str,
    num_episodes: int = 3,
    steps_per_episode: int = 10
) -> DebugReport:
    """Run sovereign agent and collect detailed failure analysis."""

    # Initialize components
    env = CommitmentTrapV100()
    state = NormativeStateV100()

    # Get environment actions
    env_actions = set(env.ACTIONS)
    env_preferences = set(state.preferences.keys()) if hasattr(state, 'preferences') else set()

    compiler = JCOMP200(
        valid_actions=env_actions,
        valid_preferences=env_preferences
    )

    generator = LLMGeneratorV200(normative_state=state)
    reward_regime = create_regime(regime, action_inventory=env_actions)

    # Tracking
    failures: List[FailureAnalysis] = []
    error_code_counts = Counter()
    leakage_lexemes_all = Counter()

    compiled_successes = 0
    compiled_failures = 0

    rule_g_schema = 0
    rule_g_lexical = 0
    rule_h = 0
    rule_d = 0
    rule_e = 0
    rule_f = 0
    audit_a = 0
    audit_b = 0
    audit_c = 0

    direct_count = 0
    synonym_count = 0
    collision_count = 0

    total_steps = 0
    successes_with_rule_g_pass = 0

    prev_incentive_record: Optional[IncentiveRecord] = None

    for episode in range(num_episodes):
        obs = env.reset()

        for step in range(steps_per_episode):
            total_steps += 1

            # Build context
            task_state = {
                "observation": obs,
                "feasible_actions": list(env.feasible_actions()),
                "step": step,
                "episode": episode,
            }

            if prev_incentive_record:
                task_state["incentive_record"] = {
                    "reward_regime_id": prev_incentive_record.reward_regime_id,
                    "reward_value": prev_incentive_record.reward_value,
                    "step_id": prev_incentive_record.step_id,
                }

            # Generate artifact
            try:
                raw_output, artifact = generator.generate(
                    task_state=task_state,
                    normative_state=state
                )
            except Exception as e:
                import traceback
                error_msg = f"E_GENERATION_FAILED: {e}"
                error_code_counts[error_msg] += 1
                compiled_failures += 1
                # Store exception details
                failures.append(FailureAnalysis(
                    step=step,
                    raw_output=traceback.format_exc()[:500],
                    error_codes=[error_msg],
                    leakage_lexemes=[],
                    lexeme_categories={},
                    schema_violations=[],
                    audit_failures=[],
                    rule_violations={"GENERATION": [str(e)]}
                ))
                continue

            # Compile
            result = compiler.compile(artifact)

            if result.success:
                compiled_successes += 1
                # Verify Rule G passes on success (should always)
                if result.rule_g_passed:
                    successes_with_rule_g_pass += 1
            else:
                compiled_failures += 1

                # Analyze failure
                analysis = analyze_compilation_result(result, raw_output, step)
                if analysis:
                    failures.append(analysis)

                    # Count error codes
                    for code in analysis.error_codes:
                        error_code_counts[code] += 1

                    # Count leakage lexemes
                    for lexeme in analysis.leakage_lexemes:
                        leakage_lexemes_all[lexeme.lower()] += 1

                    # Categorize lexemes
                    for cat, lexemes in analysis.lexeme_categories.items():
                        if cat == "direct":
                            direct_count += len(lexemes)
                        elif cat == "synonym":
                            synonym_count += len(lexemes)
                        else:
                            collision_count += len(lexemes)

                    # Count by rule
                    if "G" in analysis.rule_violations:
                        # Check if schema or lexical
                        for v in analysis.rule_violations["G"]:
                            if "schema" in v.lower() or "field" in v.lower():
                                rule_g_schema += 1
                            else:
                                rule_g_lexical += 1
                    if "H" in analysis.rule_violations:
                        rule_h += len(analysis.rule_violations["H"])
                    if "D" in analysis.rule_violations:
                        rule_d += len(analysis.rule_violations["D"])
                    if "E" in analysis.rule_violations:
                        rule_e += len(analysis.rule_violations["E"])
                    if "F" in analysis.rule_violations:
                        rule_f += len(analysis.rule_violations["F"])
                    if "A" in analysis.rule_violations:
                        audit_a += len(analysis.rule_violations["A"])
                    if "B" in analysis.rule_violations:
                        audit_b += len(analysis.rule_violations["B"])
                    if "C" in analysis.rule_violations:
                        audit_c += len(analysis.rule_violations["C"])

            # Execute action (pick first feasible if failed)
            if result.success:
                action = result.action
            else:
                action = list(env.feasible_actions())[0]

            obs, reward, done, info = env.step(action)

            # Create incentive record
            prev_incentive_record = IncentiveRecord(
                reward_regime_id=regime,
                reward_value=reward_regime.calculate_reward(action, obs, info),
                step_id=f"{episode}_{step}",
                reward_input_digest="debug",
                reward_function_version_id="debug_v1"
            )

            if done:
                break

    # Calculate Rule G pass rate on successes
    rule_g_pass_rate = (
        successes_with_rule_g_pass / compiled_successes
        if compiled_successes > 0 else 0.0
    )

    return DebugReport(
        regime=regime,
        total_steps=total_steps,
        compiled_successes=compiled_successes,
        compiled_failures=compiled_failures,
        error_code_counts=error_code_counts,
        direct_lexeme_count=direct_count,
        near_synonym_count=synonym_count,
        collision_count=collision_count,
        leakage_lexemes_histogram=leakage_lexemes_all,
        rule_g_schema_failures=rule_g_schema,
        rule_g_lexical_failures=rule_g_lexical,
        rule_h_failures=rule_h,
        rule_d_failures=rule_d,
        rule_e_failures=rule_e,
        rule_f_failures=rule_f,
        audit_a_failures=audit_a,
        audit_b_failures=audit_b,
        audit_c_failures=audit_c,
        rule_g_pass_rate_on_successes=rule_g_pass_rate,
        failures=failures
    )


def print_report(report: DebugReport):
    """Print formatted debug report."""
    print("=" * 70)
    print(f"SOVEREIGN FAILURE ANALYSIS: Regime {report.regime}")
    print("=" * 70)
    print()

    print(f"Total steps: {report.total_steps}")
    print(f"Compiled successes: {report.compiled_successes} ({100*report.compiled_successes/report.total_steps:.1f}%)")
    print(f"Compiled failures: {report.compiled_failures} ({100*report.compiled_failures/report.total_steps:.1f}%)")
    print()

    print("-" * 70)
    print("ERROR CODE HISTOGRAM")
    print("-" * 70)
    for code, count in report.error_code_counts.most_common():
        print(f"  {code}: {count}")
    print()

    print("-" * 70)
    print("E_REWARD_LEAKAGE BREAKDOWN")
    print("-" * 70)
    print(f"  Direct reward lexemes: {report.direct_lexeme_count}")
    print(f"  Near-synonyms: {report.near_synonym_count}")
    print(f"  Accidental collisions: {report.collision_count}")
    print()
    print("  Lexeme histogram:")
    for lexeme, count in report.leakage_lexemes_histogram.most_common(10):
        print(f"    '{lexeme}': {count}")
    print()

    print("-" * 70)
    print("FAILURE BY RULE CATEGORY")
    print("-" * 70)
    print(f"  Rule D (schema): {report.rule_d_failures}")
    print(f"  Rule E (action ID): {report.rule_e_failures}")
    print(f"  Rule F (preference ID): {report.rule_f_failures}")
    print(f"  Rule G (schema): {report.rule_g_schema_failures}")
    print(f"  Rule G (lexical): {report.rule_g_lexical_failures}")
    print(f"  Rule H (IIC isolation): {report.rule_h_failures}")
    print(f"  Audit A (consistency): {report.audit_a_failures}")
    print(f"  Audit B (completeness): {report.audit_b_failures}")
    print(f"  Audit C/C' (collision): {report.audit_c_failures}")
    print()

    print("-" * 70)
    print("VALIDATION CHECK")
    print("-" * 70)
    print(f"  Rule G pass rate on compiled successes: {100*report.rule_g_pass_rate_on_successes:.1f}%")
    if report.rule_g_pass_rate_on_successes < 1.0:
        print("  ⚠️  WARNING: Compiled successes have Rule G violations - COMPILER BUG!")
    else:
        print("  ✓ All compiled successes pass Rule G (pipeline functioning)")
    print()

    # Show sample failures
    print("-" * 70)
    print("SAMPLE FAILURES (first 3)")
    print("-" * 70)
    for i, f in enumerate(report.failures[:3]):
        print(f"\n  Failure {i+1} (step {f.step}):")
        print(f"    Error codes: {f.error_codes}")
        print(f"    Leakage lexemes: {f.leakage_lexemes}")
        print(f"    Raw output snippet: {f.raw_output[:200]}...")
    print()


def main():
    """Run debug analysis for R1 and R2."""
    print("\n" + "=" * 70)
    print("SOVEREIGN FAILURE DEBUG ANALYSIS")
    print("=" * 70 + "\n")

    # Check for API key
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: LLM_API_KEY environment variable required")
        print("Usage: LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514 LLM_API_KEY=... python debug_sovereign_failures.py")
        sys.exit(1)

    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    model = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
    print(f"LLM: {provider} / {model}")
    print()

    # Run analysis for R1
    print("Analyzing Sovereign under R1...")
    report_r1 = run_debug_analysis("R1", num_episodes=3, steps_per_episode=10)
    print_report(report_r1)

    # Run analysis for R2
    print("\nAnalyzing Sovereign under R2...")
    report_r2 = run_debug_analysis("R2", num_episodes=3, steps_per_episode=10)
    print_report(report_r2)

    # Save raw data
    output = {
        "R1": {
            "total_steps": report_r1.total_steps,
            "compiled_successes": report_r1.compiled_successes,
            "compiled_failures": report_r1.compiled_failures,
            "error_code_counts": dict(report_r1.error_code_counts),
            "direct_lexeme_count": report_r1.direct_lexeme_count,
            "near_synonym_count": report_r1.near_synonym_count,
            "collision_count": report_r1.collision_count,
            "leakage_lexemes": dict(report_r1.leakage_lexemes_histogram),
            "rule_g_schema": report_r1.rule_g_schema_failures,
            "rule_g_lexical": report_r1.rule_g_lexical_failures,
            "rule_h": report_r1.rule_h_failures,
            "rule_g_pass_rate_on_successes": report_r1.rule_g_pass_rate_on_successes,
        },
        "R2": {
            "total_steps": report_r2.total_steps,
            "compiled_successes": report_r2.compiled_successes,
            "compiled_failures": report_r2.compiled_failures,
            "error_code_counts": dict(report_r2.error_code_counts),
            "direct_lexeme_count": report_r2.direct_lexeme_count,
            "near_synonym_count": report_r2.near_synonym_count,
            "collision_count": report_r2.collision_count,
            "leakage_lexemes": dict(report_r2.leakage_lexemes_histogram),
            "rule_g_schema": report_r2.rule_g_schema_failures,
            "rule_g_lexical": report_r2.rule_g_lexical_failures,
            "rule_h": report_r2.rule_h_failures,
            "rule_g_pass_rate_on_successes": report_r2.rule_g_pass_rate_on_successes,
        }
    }

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_failures_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nRaw data saved to: {filename}")


if __name__ == "__main__":
    main()
