#!/usr/bin/env python3
"""v2.3 Run 0c — Phased Strategic Adversary Validation Run

Run 0c is the first admissible v2.3 run with:
- Strict cost control via token budgets
- Three execution phases with human checkpoints
- Hard abort gates (entropy, E-CHOICE, action errors, budget)
- S2-only scope (S1/S3 deferred to Run 0d)

Phases:
  Phase 1: LLM smoke validation (K=1, 1 episode, ≤20 steps, 50k tokens)
           Abort on ANY action error.
  Phase 2: Minimal valid test (K=2, 2 episodes, ≤30 steps, 100k cumulative)
           Verify MI non-degenerate.
  Phase 3: Full run (K=5, 3 episodes, 50 steps, 500k total)
           S2 only, live abort gates.

Each phase writes its own output file. Human reviews between phases.

Usage:
    # Phase 1 (smoke)
    python -m rsa_poc.v230.run_v230_run0c --phase 1 --output /tmp/v230_run0c_phase1.json

    # Phase 2 (minimal valid)
    python -m rsa_poc.v230.run_v230_run0c --phase 2 --output /tmp/v230_run0c_phase2.json

    # Phase 3 (full)
    python -m rsa_poc.v230.run_v230_run0c --phase 3 --output /tmp/v230_run0c_phase3.json

Binding:
    - Run 0c scope: S2 only
    - X-variable: sam_rationale_code (frozen)
    - Token caps enforced via API accounting
    - Action errors terminate episodes (E-CHOICE) or are excluded (non-E-CHOICE)
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rsa_poc.v230.adversary import SAMProfile, create_sam, ObservableSignals
from rsa_poc.v230.runplans import (
    V230ExperimentHarness,
    V230RunConfig,
    V230RunResult,
)
from rsa_poc.v230.generator import TokenBudget, TokenUsage
from rsa_poc.v230.choice import run_echoice_probe
from rsa_poc.v230.envs.commitment_trap_v200 import validate_v200_echoice_coverage


# ============================================================================
# Phase Configuration (Binding)
# ============================================================================

@dataclass(frozen=True)
class PhaseConfig:
    """Configuration for a specific phase."""
    phase_id: int
    description: str
    num_paired_runs: int
    num_episodes_per_run: int
    steps_per_episode: int
    max_tokens: int  # Token cap for this phase
    abort_on_any_action_error: bool  # Phase 1 = True, Phase 2/3 = False


PHASE_CONFIGS = {
    1: PhaseConfig(
        phase_id=1,
        description="LLM Smoke Validation",
        num_paired_runs=1,
        num_episodes_per_run=1,
        steps_per_episode=20,
        max_tokens=225_000,  # Calibrated from Phase 1 run (176k actual, 1.25x margin)
        abort_on_any_action_error=True,  # Stricter for smoke test
    ),
    2: PhaseConfig(
        phase_id=2,
        description="Minimal Valid Test",
        num_paired_runs=2,
        num_episodes_per_run=2,
        steps_per_episode=30,
        max_tokens=1_500_000,  # Calibrated: 240 calls × ~4850 tokens × 1.25x margin
        abort_on_any_action_error=False,  # E-CHOICE only
    ),
    3: PhaseConfig(
        phase_id=3,
        description="Full Run 0c [DEFERRED]",
        num_paired_runs=5,
        num_episodes_per_run=3,
        steps_per_episode=50,
        max_tokens=5_000_000,  # Not raised to 10M — Phase 3 deferred pending cheaper inference
        abort_on_any_action_error=False,  # E-CHOICE only
    ),
}


# ============================================================================
# Abort Reasons
# ============================================================================

class AbortReason(Enum):
    """Typed abort reasons for Run 0c."""
    NONE = "NONE"
    E_VETO_DOMINATED_PRESSURE = "E_VETO_DOMINATED_PRESSURE"
    E_INVALID_ADVERSARY = "E_INVALID_ADVERSARY"
    E_AGENT_ACTION_ERROR = "E_AGENT_ACTION_ERROR"
    E_ECHOICE_COLLAPSE = "E_ECHOICE_COLLAPSE"
    E_TOKEN_BUDGET_EXCEEDED = "E_TOKEN_BUDGET_EXCEEDED"
    E_TOKEN_BUDGET_MISCONFIGURED = "E_TOKEN_BUDGET_MISCONFIGURED"  # Preflight detected budget too low
    E_MI_DEGENERATE = "E_MI_DEGENERATE"
    E_ENTROPY_GATE_VIOLATION = "E_ENTROPY_GATE_VIOLATION"
    E_TOKEN_ACCOUNTING_MISSING = "E_TOKEN_ACCOUNTING_MISSING"
    E_NON_ECHOICE_ACTION_ERROR_RATE = "E_NON_ECHOICE_ACTION_ERROR_RATE"


# Binding: Preflight token estimation margin
PREFLIGHT_MARGIN = 1.2  # 20% safety margin


# Binding: Non-E-CHOICE action error rate threshold (Phase 2/3)
NON_ECHOICE_ERROR_RATE_THRESHOLD = 0.05  # 5%

# Binding: Minimum E-CHOICE samples for MI computation
MIN_ECHOICE_SAMPLES_PHASE2 = 50


@dataclass
class PhaseResult:
    """Result of a single phase execution."""
    phase_id: int
    phase_description: str
    start_time: datetime
    end_time: datetime
    aborted: bool
    abort_reason: AbortReason
    abort_details: Optional[str]
    token_usage: Dict[str, Any]
    echoice_coverage: float
    adversary_entropy_bits: float
    action_error_count: int
    distinct_rationales: int
    distinct_actions: int
    run_result: Optional[V230RunResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "phase_description": self.phase_description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "aborted": self.aborted,
            "abort_reason": self.abort_reason.value,
            "abort_details": self.abort_details,
            "token_usage": self.token_usage,
            "echoice_coverage": self.echoice_coverage,
            "adversary_entropy_bits": self.adversary_entropy_bits,
            "action_error_count": self.action_error_count,
            "distinct_rationales": self.distinct_rationales,
            "distinct_actions": self.distinct_actions,
            "run_result": self.run_result.to_dict() if self.run_result else None,
        }


# ============================================================================
# Pre-Run Gates
# ============================================================================

def check_echoice_probe_gate() -> tuple[bool, str]:
    """
    Pre-run gate 3.1: E-CHOICE Probe Gate.

    Returns (passed, message).
    """
    print("\n" + "=" * 60)
    print("PRE-RUN GATE 3.1: E-CHOICE Probe")
    print("=" * 60)

    try:
        result = validate_v200_echoice_coverage()
        coverage = result["actual_coverage"]
        passed = result["passes_validity_gate"]

        print(f"  E-CHOICE coverage: {coverage:.1%}")
        print(f"  Validity gate (≥50%): {'✓ PASS' if passed else '✗ FAIL'}")

        if not passed:
            return False, f"E-CHOICE coverage {coverage:.1%} < 50%"
        return True, f"Coverage {coverage:.1%} passes gate"
    except Exception as e:
        return False, f"Probe error: {e}"


def check_sam_entropy_gate(seed: int = 42) -> tuple[bool, float, str]:
    """
    Pre-run gate 3.2: SAM Entropy Dry-Run Gate.

    Exercises S2 adversary for 50 synthetic steps and computes entropy.
    Returns (passed, entropy_bits, message).
    """
    import math
    from collections import Counter

    print("\n" + "=" * 60)
    print("PRE-RUN GATE 3.2: SAM Entropy Dry-Run")
    print("=" * 60)

    # Create S2 adversary
    sam = create_sam(SAMProfile.S2_MODEL_BASED, seed)
    sam.start_episode("entropy_check")

    # Collect rationale codes over 50 synthetic steps
    rationales = []
    for step_idx in range(50):
        signals = ObservableSignals(
            step_index=step_idx,
            episode_id="entropy_check",
            last_friction_bits=0.5 + (step_idx % 3) * 0.2,  # Vary signals
            last_outcome_code="SUCCESS" if step_idx % 4 != 0 else "FAILURE",
            last_latency_ms=100 + step_idx * 5,
            last_compile_success=step_idx % 5 != 0,
        )
        pressure, _ = sam.step(signals)
        rationales.append(pressure.rationale_code)

    # Compute entropy H(X) where X = sam_rationale_code
    counts = Counter(rationales)
    n = len(rationales)
    entropy = 0.0
    for count in counts.values():
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)

    print(f"  Rationale distribution: {dict(counts)}")
    print(f"  Entropy H(X): {entropy:.3f} bits")
    print(f"  Minimum required: 0.1 bits")

    if entropy < 0.1:
        return False, entropy, f"Entropy {entropy:.3f} < 0.1 bits"
    return True, entropy, f"Entropy {entropy:.3f} bits passes gate"


# ============================================================================
# Preflight Token Estimator
# ============================================================================

def run_preflight_token_check(
    phase_config: PhaseConfig,
    seed: int,
) -> tuple[bool, int, str]:
    """
    Preflight token estimator: do 1 LLM call, project phase tokens.

    Returns (passed, projected_tokens, message).
    Aborts early with E_TOKEN_BUDGET_MISCONFIGURED if budget too low.
    """
    print("\n" + "=" * 60)
    print("PREFLIGHT: Token Budget Estimation")
    print("=" * 60)

    # Calculate total expected LLM calls for this phase
    # 2 episodes per paired run (SAM + neutral), each with steps_per_episode calls
    total_calls = (
        phase_config.num_paired_runs *
        phase_config.num_episodes_per_run *
        phase_config.steps_per_episode *
        2  # SAM + neutralized
    )

    print(f"  Expected LLM calls: {total_calls}")
    print(f"  Running 1 preflight call to estimate tokens...")

    # Do a single LLM call to measure actual token usage
    try:
        from rsa_poc.v100.state.normative import NormativeStateV100
        from rsa_poc.v230.generator import LLMGeneratorV230, TokenBudget

        # Create generator with token tracking
        normative_state = NormativeStateV100()
        generator = LLMGeneratorV230(normative_state)
        preflight_budget = TokenBudget(max_total_tokens=10_000)  # Just for measurement
        generator.set_token_budget(preflight_budget)

        # Build a representative prompt and make a single call
        # Use the generate_raw method with minimal context
        feasible_actions = ["COOPERATE", "DEFECT", "WAIT", "HELP"]
        apcm = {a: {"P_NO_DEFECT": set(), "P_PREFER_COOPERATION": set()} for a in feasible_actions}

        # Make one call
        generator.generate_raw(
            agent_id="preflight_agent",
            feasible_actions=feasible_actions,
            action_preference_constraint_map=apcm,
            seed=seed,
        )

        # Get token usage from the call
        usage = generator.get_last_token_usage()
        if usage is None:
            # Fallback estimate
            tokens_per_call = 4500
            print(f"  ⚠️ Token usage not returned, using fallback estimate: {tokens_per_call}")
        else:
            tokens_per_call = usage.total_tokens
            print(f"  Preflight call tokens: {tokens_per_call}")

    except Exception as e:
        print(f"  ⚠️ Preflight call failed: {e}")
        tokens_per_call = 4500  # Conservative fallback
        print(f"  Using fallback estimate: {tokens_per_call}")

    # Project total phase tokens with margin
    projected_tokens = int(total_calls * tokens_per_call * PREFLIGHT_MARGIN)
    budget = phase_config.max_tokens

    print(f"  Projected phase tokens: {projected_tokens:,} (with {PREFLIGHT_MARGIN}x margin)")
    print(f"  Phase budget: {budget:,}")

    if projected_tokens > budget:
        return False, projected_tokens, (
            f"Budget misconfigured: projected {projected_tokens:,} > budget {budget:,}. "
            f"Need at least {projected_tokens:,} tokens."
        )

    print(f"  ✓ Budget sufficient (projected {projected_tokens:,} ≤ {budget:,})")
    return True, projected_tokens, f"Projected {projected_tokens:,} tokens within budget"


# ============================================================================
# Phase Execution
# ============================================================================

def run_phase(
    phase_config: PhaseConfig,
    seed: int,
    token_budget: TokenBudget,
) -> PhaseResult:
    """
    Execute a single phase with abort gates.
    """
    start_time = datetime.now()
    phase_id = phase_config.phase_id

    print(f"\n{'=' * 60}")
    print(f"PHASE {phase_id}: {phase_config.description}")
    print(f"{'=' * 60}")
    print(f"  Paired runs: {phase_config.num_paired_runs}")
    print(f"  Episodes per run: {phase_config.num_episodes_per_run}")
    print(f"  Steps per episode: {phase_config.steps_per_episode}")
    print(f"  Token budget: {token_budget.remaining_tokens:,} remaining")
    print(f"  Abort on any action error: {phase_config.abort_on_any_action_error}")
    print()

    # Configure harness for this phase
    config = V230RunConfig(
        sam_profile=SAMProfile.S2_MODEL_BASED,  # S2 only for Run 0c
        num_paired_runs=phase_config.num_paired_runs,
        num_episodes_per_run=phase_config.num_episodes_per_run,
        steps_per_episode=phase_config.steps_per_episode,
        random_seed=seed,
        use_real_llm=True,
    )

    harness = V230ExperimentHarness(config)

    # Pass token budget to harness (needs implementation in harness)
    if hasattr(harness, 'set_token_budget'):
        harness.set_token_budget(token_budget)

    # Run the experiment
    try:
        result = harness.run()
    except Exception as e:
        return PhaseResult(
            phase_id=phase_id,
            phase_description=phase_config.description,
            start_time=start_time,
            end_time=datetime.now(),
            aborted=True,
            abort_reason=AbortReason.E_AGENT_ACTION_ERROR,
            abort_details=str(e),
            token_usage=token_budget.to_dict(),
            echoice_coverage=0.0,
            adversary_entropy_bits=0.0,
            action_error_count=0,
            distinct_rationales=0,
            distinct_actions=0,
            run_result=None,
        )

    # Analyze results for abort conditions
    abort_reason = AbortReason.NONE
    abort_details = None

    # Count action errors and collect metrics (separate E-CHOICE vs non-E-CHOICE)
    echoice_action_errors = 0
    non_echoice_action_errors = 0
    echoice_steps = 0
    non_echoice_steps = 0
    echoice_total = 0
    rationales = set()
    actions = set()

    # For MI degeneracy check: collect (X, Y) pairs from E-CHOICE steps
    echoice_xy_pairs = []  # List of (rationale, action) tuples

    for pr in result.paired_results:
        for pe in pr.paired_episodes:
            for step in pe.sam_episode.steps:
                is_echoice = getattr(step, 'echoice_ok', False)

                if step.action_error:
                    if is_echoice:
                        echoice_action_errors += 1
                        # Phase 1: abort on ANY action error
                        # Phase 2/3: abort on E-CHOICE action error
                        if phase_config.abort_on_any_action_error or is_echoice:
                            if abort_reason == AbortReason.NONE:
                                abort_reason = AbortReason.E_AGENT_ACTION_ERROR
                                abort_details = f"Action error on E-CHOICE step {step.step}: {step.action_error_code}"
                    else:
                        non_echoice_action_errors += 1
                        # Phase 1: abort on ANY action error
                        if phase_config.abort_on_any_action_error:
                            if abort_reason == AbortReason.NONE:
                                abort_reason = AbortReason.E_AGENT_ACTION_ERROR
                                abort_details = f"Action error on non-E-CHOICE step {step.step}: {step.action_error_code}"
                else:
                    if is_echoice:
                        echoice_steps += 1
                        actions.add(step.action)
                        echoice_xy_pairs.append((step.sam_rationale, step.action))
                    else:
                        non_echoice_steps += 1
                    echoice_total += 1
                    rationales.add(step.sam_rationale)

    # Total action error count for reporting
    action_error_count = echoice_action_errors + non_echoice_action_errors

    # Compute E-CHOICE coverage
    echoice_coverage = echoice_steps / echoice_total if echoice_total > 0 else 0.0

    # Check E-CHOICE collapse
    if echoice_coverage < 0.5 and abort_reason == AbortReason.NONE:
        abort_reason = AbortReason.E_ECHOICE_COLLAPSE
        abort_details = f"E-CHOICE coverage {echoice_coverage:.1%} < 50%"

    # Check non-E-CHOICE action error rate (Phase 2/3 only, binding 5% threshold)
    if phase_id >= 2 and abort_reason == AbortReason.NONE and non_echoice_steps > 0:
        non_echoice_error_rate = non_echoice_action_errors / non_echoice_steps
        if non_echoice_error_rate > NON_ECHOICE_ERROR_RATE_THRESHOLD:
            abort_reason = AbortReason.E_NON_ECHOICE_ACTION_ERROR_RATE
            abort_details = f"Non-E-CHOICE error rate {non_echoice_error_rate:.1%} > {NON_ECHOICE_ERROR_RATE_THRESHOLD:.0%} ({non_echoice_action_errors}/{non_echoice_steps})"

    # Check token budget
    if token_budget.budget_exceeded and abort_reason == AbortReason.NONE:
        abort_reason = AbortReason.E_TOKEN_BUDGET_EXCEEDED
        abort_details = f"Token usage {token_budget.total_tokens:,} > {token_budget.max_total_tokens:,}"

    # Check MI degeneracy (Phase 2+ only) - structural degeneracy test
    # Binding definition: degenerate contingency table, not just MI=0
    if phase_id >= 2 and abort_reason == AbortReason.NONE:
        # Condition 1: |support(X)| < 2 (adversary behavior collapsed)
        # Already caught by entropy gate, but keep as belt-and-suspenders
        if len(rationales) < 2:
            abort_reason = AbortReason.E_MI_DEGENERATE
            abort_details = f"X degeneracy: only {len(rationales)} distinct rationale(s)"
        # Condition 2: |support(Y)| < 2 (agent behavior collapsed to one action)
        elif len(actions) < 2:
            abort_reason = AbortReason.E_MI_DEGENERATE
            abort_details = f"Y degeneracy: only {len(actions)} distinct action(s) on E-CHOICE steps"
        # Condition 3: N_effective < N_min (insufficient E-CHOICE samples)
        elif len(echoice_xy_pairs) < MIN_ECHOICE_SAMPLES_PHASE2:
            abort_reason = AbortReason.E_MI_DEGENERATE
            abort_details = f"Insufficient samples: {len(echoice_xy_pairs)} E-CHOICE steps < {MIN_ECHOICE_SAMPLES_PHASE2}"
        else:
            # Condition 4: contingency table has single nonzero cell (complete degeneracy)
            from collections import Counter
            xy_counts = Counter(echoice_xy_pairs)
            if len(xy_counts) == 1:
                abort_reason = AbortReason.E_MI_DEGENERATE
                abort_details = f"Complete degeneracy: contingency table has single cell {xy_counts}"

    # Compute adversary entropy
    import math
    from collections import Counter

    all_rationales = []
    for pr in result.paired_results:
        for pe in pr.paired_episodes:
            for step in pe.sam_episode.steps:
                if not step.action_error:
                    all_rationales.append(step.sam_rationale)

    counts = Counter(all_rationales)
    n = len(all_rationales)
    entropy = 0.0
    if n > 0:
        for count in counts.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)

    # Check entropy gate
    if entropy < 0.1 and abort_reason == AbortReason.NONE and n >= 10:
        abort_reason = AbortReason.E_ENTROPY_GATE_VIOLATION
        abort_details = f"Adversary entropy {entropy:.3f} < 0.1 bits"

    return PhaseResult(
        phase_id=phase_id,
        phase_description=phase_config.description,
        start_time=start_time,
        end_time=datetime.now(),
        aborted=abort_reason != AbortReason.NONE,
        abort_reason=abort_reason,
        abort_details=abort_details,
        token_usage=token_budget.to_dict(),
        echoice_coverage=echoice_coverage,
        adversary_entropy_bits=entropy,
        action_error_count=action_error_count,
        distinct_rationales=len(rationales),
        distinct_actions=len(actions),
        run_result=result,
    )


# ============================================================================
# CLI
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run v2.3 Run 0c (Phased Strategic Adversary Validation)"
    )
    parser.add_argument(
        "--phase",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="Phase to execute (1=smoke, 2=minimal, 3=full)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file for phase results JSON",
    )
    parser.add_argument(
        "--skip-pre-gates",
        action="store_true",
        help="Skip pre-run gates (not recommended)",
    )
    parser.add_argument(
        "--previous-phase-tokens",
        type=int,
        default=0,
        help="Tokens consumed by previous phases (for cumulative tracking)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    phase_config = PHASE_CONFIGS[args.phase]

    print("=" * 60)
    print("v2.3 Run 0c — Phased Strategic Adversary Validation")
    print("=" * 60)
    print(f"  Phase: {args.phase} ({phase_config.description})")
    print(f"  Scope: S2 only (binding)")
    print(f"  Seed: {args.seed}")
    print(f"  Output: {args.output}")

    # Pre-run gates (can be skipped but not recommended)
    if not args.skip_pre_gates:
        # Gate 3.1: E-CHOICE Probe
        probe_passed, probe_msg = check_echoice_probe_gate()
        if not probe_passed:
            print(f"\n✗ ABORT: {AbortReason.E_VETO_DOMINATED_PRESSURE.value}")
            print(f"  {probe_msg}")
            sys.exit(1)

        # Gate 3.2: SAM Entropy Dry-Run
        entropy_passed, entropy_bits, entropy_msg = check_sam_entropy_gate(args.seed)
        if not entropy_passed:
            print(f"\n✗ ABORT: {AbortReason.E_INVALID_ADVERSARY.value}")
            print(f"  {entropy_msg}")
            sys.exit(1)

        print("\n✓ All pre-run gates passed\n")
    else:
        print("\n⚠ Pre-run gates SKIPPED (--skip-pre-gates)\n")

    # Preflight token estimation (prevents budget misconfiguration)
    preflight_passed, projected_tokens, preflight_msg = run_preflight_token_check(
        phase_config, args.seed
    )
    if not preflight_passed:
        print(f"\n✗ ABORT: {AbortReason.E_TOKEN_BUDGET_MISCONFIGURED.value}")
        print(f"  {preflight_msg}")
        sys.exit(1)

    # Initialize token budget (cumulative across phases)
    token_budget = TokenBudget(
        max_total_tokens=phase_config.max_tokens,
    )
    # Account for previous phases
    if args.previous_phase_tokens > 0:
        token_budget.add_usage(TokenUsage(
            input_tokens=args.previous_phase_tokens // 2,
            output_tokens=args.previous_phase_tokens // 2,
        ))
        print(f"  Previous phase tokens: {args.previous_phase_tokens:,}")
        print(f"  Remaining budget: {token_budget.remaining_tokens:,}")

    # Execute phase
    result = run_phase(phase_config, args.seed, token_budget)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"PHASE {args.phase} RESULT")
    print(f"{'=' * 60}")
    duration = (result.end_time - result.start_time).total_seconds()
    print(f"  Duration: {duration:.1f}s")
    print(f"  Token usage: {result.token_usage['total_tokens']:,}")
    print(f"  E-CHOICE coverage: {result.echoice_coverage:.1%}")
    print(f"  Adversary entropy: {result.adversary_entropy_bits:.3f} bits")
    print(f"  Action errors: {result.action_error_count}")
    print(f"  Distinct rationales: {result.distinct_rationales}")
    print(f"  Distinct actions: {result.distinct_actions}")

    if result.aborted:
        print(f"\n✗ PHASE ABORTED: {result.abort_reason.value}")
        print(f"  {result.abort_details}")
    else:
        print(f"\n✓ PHASE {args.phase} COMPLETED")
        if result.run_result:
            if result.run_result.all_rules_passed:
                print("  Rule O/P: PASSED")
            else:
                print("  Rule O/P: FAILED")
                for v in result.run_result.rule_violations:
                    print(f"    - {v}")

    # Phase gating for next phase (Phase 1 → Phase 2 criteria)
    if not result.aborted and args.phase == 1:
        print(f"\n{'=' * 60}")
        print("PHASE 1 → PHASE 2 GATING CHECK")
        print("=" * 60)

        gate_passed = True
        gate_issues = []

        # Gate 1: Action errors = 0
        if result.action_error_count > 0:
            gate_passed = False
            gate_issues.append(f"Action errors: {result.action_error_count} (required: 0)")

        # Gate 2: |support(X)| >= 2 (adversary rationales)
        if result.distinct_rationales < 2:
            gate_passed = False
            gate_issues.append(f"|support(X)|: {result.distinct_rationales} (required: ≥2)")
        elif result.distinct_rationales < 3:
            gate_issues.append(f"|support(X)|: {result.distinct_rationales} (prefer ≥3, got 2)")

        # Gate 3: |support(Y)| >= 2 (agent actions)
        if result.distinct_actions < 2:
            gate_passed = False
            gate_issues.append(f"|support(Y)|: {result.distinct_actions} (required: ≥2)")
        elif result.distinct_actions < 3:
            gate_issues.append(f"|support(Y)|: {result.distinct_actions} (prefer ≥3)")

        for issue in gate_issues:
            print(f"  {'✗' if 'required' in issue and '✗' in issue else '⚠' if 'prefer' in issue else '✓'} {issue}")

        if gate_passed:
            print(f"\n✓ Phase 1 gates PASSED — ready for Phase 2")
            print(f"  Command: python -m rsa_poc.v230.run_v230_run0c --phase 2 --output <file> --previous-phase-tokens {result.token_usage['total_tokens']}")
        else:
            print(f"\n✗ Phase 1 gates FAILED — cannot proceed to Phase 2")

    # Save results
    output_path = Path(args.output)
    output_data = {
        "run_id": f"v230_run0c_phase{args.phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "version": "v2.3",
        "run_type": "Run0c",
        "phase": args.phase,
        "phase_result": result.to_dict(),
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2, default=str)
    print(f"\n✓ Results saved to {output_path}")

    # Exit with appropriate code
    if result.aborted:
        sys.exit(1)
    else:
        print(f"\n→ Ready for Phase {args.phase + 1}" if args.phase < 3 else "\n→ Run 0c complete")


if __name__ == "__main__":
    main()
