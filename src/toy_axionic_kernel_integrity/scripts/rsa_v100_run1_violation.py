"""
RSA v1.0 Run 1: Persistent Violation (ALWAYS_FAIL_COMMITMENT)

Purpose: Test survivability under deliberate commitment violation.

Per spec §RSA v1.0 Run Sequence:
- Model: ALWAYS_FAIL_COMMITMENT
- Sweep: target commitment keys (C0, C1, C2)

Expected outcomes (fail-streak semantics, K=3):
- C0/C1 target: Always fail SEM_PASS → streak grows → ineligible after 3 epochs → low AA
- C2 target: Fail only when epoch%3==0 → max 1 consecutive fail → always eligible → moderate AA
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel
from scripts.rsa_v100_metrics import compute_consecutive_metrics, extract_sem_pass_sequence


@dataclass
class RunConfig:
    """Configuration for RSA v1.0 Run 1."""

    # Shared across all runs
    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    amnesty_interval: int = 10

    # Run parameters
    seeds: List[int] = None
    target_commitments: List[str] = None

    def __post_init__(self):
        if self.seeds is None:
            self.seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
        if self.target_commitments is None:
            self.target_commitments = ["C0", "C1", "C2"]


def run_persistent_violation(config: RunConfig, verbose: bool = False) -> List[Dict[str, Any]]:
    """Run persistent violation experiments."""
    results = []

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        amnesty_interval=config.amnesty_interval,
    )

    for target in config.target_commitments:
        for seed in config.seeds:
            print(f"Running ALWAYS_FAIL_COMMITMENT target={target} seed={seed}...")

            policy_config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
                target_commitment=target,
                epoch_size=config.renewal_check_interval,
            )

            harness = ALSHarnessV080(
                seed=seed,
                config=als_config,
                verbose=verbose,
                rsa_policy_config=policy_config,
            )
            result = harness.run()

            # Compute AA and derived metrics
            total_epochs = config.max_cycles // config.renewal_check_interval
            sem_pass_seq = extract_sem_pass_sequence(harness)
            consec_metrics = compute_consecutive_metrics(
                sem_pass_seq,
                eligibility_threshold_k=config.eligibility_threshold_k
            )
            authority_epochs = sum(1 for s in sem_pass_seq if s)
            aa = authority_epochs / max(total_epochs, 1)

            run_result = {
                "run_id": f"rsa_v100_run1_violation_{target}_seed{seed}",
                "seed": seed,
                "rsa_model": "ALWAYS_FAIL_COMMITMENT",
                "target_commitment": target,
                "rsa_policy_enabled": True,
                "total_cycles": result.total_cycles,
                "total_epochs": total_epochs,
                "total_renewals": result.total_renewals,
                "total_expirations": result.total_expirations,
                "stop_reason": result.stop_reason.name,
                "authority_availability_ppm": int(aa * 1_000_000),
                "final_streak": harness._semantic_fail_streak.get(harness._active_policy_id, 0),
                # v1.0 derived metrics
                "max_consecutive_sem_pass": consec_metrics["max_consecutive_sem_pass"],
                "max_consecutive_sem_fail": consec_metrics["max_consecutive_sem_fail"],
                "ever_ineligible": consec_metrics["ever_ineligible"],
                "ineligibility_fraction": consec_metrics["ineligibility_fraction"],
                "pass_rate_ppm": consec_metrics["pass_rate_ppm"],
            }
            results.append(run_result)

            elig_str = "✗" if consec_metrics["ever_ineligible"] else "✓"
            print(f"  Cycles={result.total_cycles}, AA={aa:.4f}, MaxFail={consec_metrics['max_consecutive_sem_fail']}, Elig={elig_str}")

    return results


def main():
    """Run persistent violation experiments and save results."""
    print("=" * 60)
    print("RSA v1.0 Run 1: Persistent Violation (ALWAYS_FAIL_COMMITMENT)")
    print("=" * 60)
    print()

    config = RunConfig()

    print(f"Configuration:")
    print(f"  max_cycles: {config.max_cycles}")
    print(f"  target_commitments: {config.target_commitments}")
    print(f"  seeds: {config.seeds}")
    print()

    results = run_persistent_violation(config)

    # Summary by target
    print()
    print("=" * 60)
    print("Summary by Target Commitment")
    print("=" * 60)

    for target in config.target_commitments:
        target_results = [r for r in results if r["target_commitment"] == target]
        aa_values = [r["authority_availability_ppm"] / 1_000_000 for r in target_results]
        mean_aa = sum(aa_values) / len(aa_values)
        # Count runs that NEVER became ineligible (ever_ineligible == False)
        always_eligible_count = sum(1 for r in target_results if not r["ever_ineligible"])
        max_fail = max(r["max_consecutive_sem_fail"] for r in target_results)
        print(f"{target}: Mean AA = {mean_aa:.4f}, MaxConsecFail = {max_fail}, AlwaysEligible = {always_eligible_count}/{len(target_results)}")

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"rsa_v100_run1_violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "run_type": "RSA v1.0 Run 1: Persistent Violation",
            "config": asdict(config),
            "results": results,
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
