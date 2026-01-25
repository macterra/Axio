#!/usr/bin/env python3
"""RSA-PoC v2.2 Run 0

Entry point for v2.2 Institutional Corruption experiments.

Run Plan v2.2 (per spec Section 14):
1. v2.1 Baseline (Benign Institution)
2. I1 — Frictional Institution
3. I2 — Capricious Institution
4. I3 — Asymmetric Institution
5. Ablation A — Reduced Retry Budget
6. Ablation B — Friction on Norm-Preserving Paths Only

All runs use identical seeds (42) for reproducibility.

Usage:
    export LLM_PROVIDER=anthropic
    export LLM_MODEL=claude-sonnet-4-20250514
    export LLM_API_KEY=<your-key>
    python src/rsa_poc/v220/run_v220_run0.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure PYTHONPATH includes project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from rsa_poc.v220.runplans import (
    V220ExperimentHarness,
    V220RunConfig,
    AgentType,
)
from rsa_poc.v220.institution import InstitutionProfile
from rsa_poc.v220.tests import run_all_fixtures, print_fixture_results, run_determinism_gate
from rsa_poc.v220.audit import RuleKAAudit, StepMetrics


def run_determinism_gate_check() -> bool:
    """
    Run Section 3.1 determinism gate.

    Must pass before any LLM runs.
    Returns True if passed.
    """
    passed, results = run_determinism_gate()
    return passed


def run_fixtures() -> bool:
    """Run v2.2 rule fixtures. Returns True if all pass."""
    print("\n" + "=" * 70)
    print("v2.2 Rule Fixtures")
    print("=" * 70)

    passed, total, results = run_all_fixtures()
    print_fixture_results(results)

    return passed == total


def run_single_experiment(
    profile: InstitutionProfile,
    agent_type: AgentType,
    label: str,
    results_dir: Path,
    run_id: str = "",
) -> dict:
    """Run a single experiment configuration."""
    print(f"\n{'=' * 70}")
    print(f"Running: {label}")
    print(f"  Agent: {agent_type.value}")
    print(f"  Profile: {profile.value}")
    print("=" * 70)

    config = V220RunConfig(
        agent_type=agent_type,
        institution_profile=profile,
        reward_regime=None,  # No incentive interference for v2.2 baseline
        num_episodes=3,
        steps_per_episode=10,
        random_seed=42,
        agent_id=f"MVRA_v220_{profile.value}",
    )

    harness = V220ExperimentHarness(config, telemetry_dir=results_dir)
    result = harness.run()

    # Build step_records for K-A telemetry (binding schema)
    step_records = []
    for ep in result.episodes:
        for step_rec in ep.steps:
            step_records.append(step_rec.to_step_record_dict(
                run_id=run_id,
                profile_id=profile.value,
                agent_type=agent_type.value,
                seed=config.random_seed,
                episode_idx=ep.episode_id,
            ))

    return {
        "label": label,
        "agent_type": agent_type.value,
        "profile": profile.value,
        "summary": result.summary,
        "episodes": [
            {
                "episode_id": ep.episode_id,
                "steps_count": len(ep.steps),
                "compilation_failures": ep.compilation_failures,
                "blocked_steps": ep.blocked_steps,
                "high_friction_steps": ep.high_friction_steps,
                "total_reward": ep.total_reward,
                "anti_zeno_terminated": ep.anti_zeno_termination.should_terminate if ep.anti_zeno_termination else False,
            }
            for ep in result.episodes
        ],
        "step_records": step_records,  # K-A telemetry
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
    }


def run_post_hoc_audit(
    baseline_results: dict,
    friction_results: dict,
) -> dict:
    """
    Run Rule K-A post-hoc audit comparing friction run to baseline.

    Returns audit result dictionary.
    """
    audit = RuleKAAudit()

    # Extract step metrics from results
    # (In full implementation, this would use detailed step telemetry)
    # For now, we return a placeholder

    return {
        "audit_run": True,
        "baseline_label": baseline_results.get("label", "unknown"),
        "friction_label": friction_results.get("label", "unknown"),
        "note": "Full K-A audit requires detailed step telemetry from harness",
    }


def analyze_results(all_results: list) -> dict:
    """Print analysis of all experiment results. Returns latency stats for B2."""
    print("\n" + "=" * 70)
    print("v2.2 Run 0 Analysis")
    print("=" * 70)

    print("\n### Compilation Success Rates ###\n")
    print(f"{'Label':<40} {'Agent':<12} {'Profile':<10} {'Compile%':<10} {'Blocked%':<10}")
    print("-" * 90)

    for r in all_results:
        label = r["label"][:38]
        agent = r["agent_type"]
        profile = r["profile"]
        compile_rate = r["summary"]["compilation_success_rate"] * 100
        blocked_rate = r["summary"]["blocked_step_rate"] * 100
        print(f"{label:<40} {agent:<12} {profile:<10} {compile_rate:>7.1f}%   {blocked_rate:>7.1f}%")

    print("\n### High Friction Analysis ###\n")
    print(f"{'Label':<40} {'HF Steps':<12} {'Anti-Zeno':<15}")
    print("-" * 70)

    for r in all_results:
        label = r["label"][:38]
        hf_rate = r["summary"]["high_friction_step_rate"] * 100
        anti_zeno = r["summary"]["anti_zeno_terminations"]
        print(f"{label:<40} {hf_rate:>8.1f}%    {anti_zeno} terminations")

    print("\n### Latency Summary ###\n")
    print(f"{'Label':<40} {'Total Latency (ms)':<20}")
    print("-" * 65)

    for r in all_results:
        label = r["label"][:38]
        latency = r["summary"]["total_institution_latency_ms"]
        print(f"{label:<40} {latency:>15,}")

    # B2: Log baseline latency distribution for threshold calibration
    print("\n### Baseline Latency Distribution (B2) ###")
    print("(For justifying 500ms HighFriction threshold calibration)")
    print("-" * 65)

    latency_stats = {}
    for r in all_results:
        if r["profile"] == "BENIGN":
            # Collect per-op latencies from summary
            label = r["label"][:38]
            latencies = r["summary"].get("per_op_latencies", [])
            if latencies:
                sorted_l = sorted(latencies)
                n = len(sorted_l)
                p50 = sorted_l[int(n * 0.50)] if n > 0 else 0
                p95 = sorted_l[int(n * 0.95)] if n > 0 else 0
                p99 = sorted_l[int(n * 0.99)] if n > 0 else 0
                print(f"{label:<40} P50={p50}ms  P95={p95}ms  P99={p99}ms")
                latency_stats[label] = {"p50": p50, "p95": p95, "p99": p99}
            else:
                print(f"{label:<40} (no per-op latency data)")
                latency_stats[label] = {"p50": 0, "p95": 0, "p99": 0, "note": "BENIGN has zero friction"}

    return latency_stats


def main():
    """Main entry point for v2.2 Run 0."""
    print("\n" + "=" * 70)
    print("RSA-PoC v2.2 — Institutional Corruption (Paperwork as Adversary)")
    print("=" * 70)

    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("results/v220")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Step 0: DETERMINISM GATE (Section 3.1)
    # Must pass before any LLM runs
    print("\n[0/5] Running Determinism Gate (Section 3.1)...")
    determinism_passed = run_determinism_gate_check()

    if not determinism_passed:
        print("\n❌ DETERMINISM GATE FAILED")
        print("   DO NOT execute Run 0 with LLM until fixed.")
        print("   See results/v220/determinism/ for details.")
        sys.exit(1)

    print("\n✓ Determinism gate passed. Proceeding with Run 0.")

    # Step 1: Run fixtures
    print("\n[1/5] Running Rule Fixtures...")
    fixtures_passed = run_fixtures()

    if not fixtures_passed:
        print("\n⚠️  WARNING: Some fixtures failed. Proceeding with experiments anyway.")
        # Note: In strict mode, we might abort here

    # Step 2: Run experiments
    print("\n[2/5] Running Experiments...")

    all_results = []
    run_id = f"v220_run0_{timestamp}"

    # v2.1 Baseline (Benign Institution)
    result = run_single_experiment(
        profile=InstitutionProfile.BENIGN,
        agent_type=AgentType.SOVEREIGN,
        label="v2.1 Baseline (Benign Institution) - Sovereign",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)
    baseline_result = result

    # Control agent on benign
    result = run_single_experiment(
        profile=InstitutionProfile.BENIGN,
        agent_type=AgentType.CONTROL,
        label="v2.1 Baseline (Benign Institution) - Control",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)

    # I1 — Frictional Institution
    result = run_single_experiment(
        profile=InstitutionProfile.I1,
        agent_type=AgentType.SOVEREIGN,
        label="I1 Frictional Institution - Sovereign",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)
    i1_sovereign = result

    result = run_single_experiment(
        profile=InstitutionProfile.I1,
        agent_type=AgentType.CONTROL,
        label="I1 Frictional Institution - Control",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)

    # I2 — Capricious Institution
    result = run_single_experiment(
        profile=InstitutionProfile.I2,
        agent_type=AgentType.SOVEREIGN,
        label="I2 Capricious Institution - Sovereign",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)
    i2_sovereign = result

    result = run_single_experiment(
        profile=InstitutionProfile.I2,
        agent_type=AgentType.CONTROL,
        label="I2 Capricious Institution - Control",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)

    # I3 — Asymmetric Institution
    result = run_single_experiment(
        profile=InstitutionProfile.I3,
        agent_type=AgentType.SOVEREIGN,
        label="I3 Asymmetric Institution - Sovereign",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)
    i3_sovereign = result

    result = run_single_experiment(
        profile=InstitutionProfile.I3,
        agent_type=AgentType.CONTROL,
        label="I3 Asymmetric Institution - Control",
        results_dir=results_dir,
        run_id=run_id,
    )
    all_results.append(result)

    # Step 3: Run post-hoc audits
    print("\n[3/5] Running Post-Hoc Audits (Rule K-A)...")

    audit_results = []
    for friction_result in [i1_sovereign, i2_sovereign, i3_sovereign]:
        audit = run_post_hoc_audit(baseline_result, friction_result)
        audit_results.append(audit)
        print(f"  Audit: {audit['friction_label']} vs baseline")

    # Step 4: Analyze and save results
    print("\n[4/5] Analyzing Results...")
    latency_stats = analyze_results(all_results)

    # Save all results
    output_file = results_dir / f"v220_run0_{timestamp}.json"
    output = {
        "run_id": f"v220_run0_{timestamp}",
        "determinism_gate_passed": determinism_passed,
        "fixtures_passed": fixtures_passed,
        "experiments": all_results,
        "audits": audit_results,
        "baseline_latency_stats": latency_stats,  # B2: for threshold calibration
        "timestamp": timestamp,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")

    print("\n" + "=" * 70)
    print("v2.2 Run 0 Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
