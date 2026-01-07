"""
RSA v1.0 Run 0: Baseline (No Adversary)

Purpose: Establish baseline authority survivability and recovery behavior for AKI v0.8.

Per spec §RSA v1.0 Run Sequence:
- RSA disabled
- Identical horizon and seeds as Runs 1-5
- Establishes reference for comparison
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080


@dataclass
class RunConfig:
    """Configuration for RSA v1.0 runs."""

    # Shared across all runs
    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    amnesty_interval: int = 10

    # Run parameters
    seeds: List[int] = None

    def __post_init__(self):
        if self.seeds is None:
            # 10 seeds for statistical coverage
            self.seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]


def run_baseline(config: RunConfig, verbose: bool = False) -> List[Dict[str, Any]]:
    """Run baseline experiments (no RSA policy)."""
    results = []

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        amnesty_interval=config.amnesty_interval,
    )

    for seed in config.seeds:
        print(f"Running baseline seed={seed}...")

        harness = ALSHarnessV080(
            seed=seed,
            config=als_config,
            verbose=verbose,
            rsa_config=None,
            rsa_policy_config=None,
        )
        result = harness.run()

        # Compute AA
        total_epochs = config.max_cycles // config.renewal_check_interval
        authority_epochs = len([r for r in harness._semantic_epoch_records if r.sem_pass])
        aa = authority_epochs / max(total_epochs, 1)

        run_result = {
            "run_id": f"rsa_v100_run0_baseline_seed{seed}",
            "seed": seed,
            "rsa_model": "NONE",
            "rsa_policy_enabled": False,
            "total_cycles": result.total_cycles,
            "total_epochs": total_epochs,
            "total_renewals": result.total_renewals,
            "total_expirations": result.total_expirations,
            "stop_reason": result.stop_reason.name,
            "authority_availability_ppm": int(aa * 1_000_000),
            "final_streak": harness._semantic_fail_streak.get(harness._active_policy_id, 0),
        }
        results.append(run_result)

        print(f"  Cycles={result.total_cycles}, AA={aa:.4f}, Renewals={result.total_renewals}")

    return results


def main():
    """Run baseline experiments and save results."""
    print("=" * 60)
    print("RSA v1.0 Run 0: Baseline (No Adversary)")
    print("=" * 60)
    print()

    config = RunConfig()

    print(f"Configuration:")
    print(f"  max_cycles: {config.max_cycles}")
    print(f"  renewal_check_interval: {config.renewal_check_interval}")
    print(f"  eligibility_threshold_k: {config.eligibility_threshold_k}")
    print(f"  seeds: {config.seeds}")
    print()

    results = run_baseline(config)

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    aa_values = [r["authority_availability_ppm"] / 1_000_000 for r in results]
    mean_aa = sum(aa_values) / len(aa_values)

    print(f"Mean AA: {mean_aa:.4f}")
    print(f"AA range: [{min(aa_values):.4f}, {max(aa_values):.4f}]")

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"rsa_v100_run0_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "run_type": "RSA v1.0 Run 0: Baseline",
            "config": asdict(config),
            "results": results,
            "summary": {
                "mean_authority_availability": mean_aa,
                "min_aa": min(aa_values),
                "max_aa": max(aa_values),
            }
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
