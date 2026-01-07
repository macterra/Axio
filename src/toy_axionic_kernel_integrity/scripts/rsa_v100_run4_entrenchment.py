"""
RSA v1.0 Run 4: Blind Succession Avoidance (ALWAYS_SELF_RENEW)

Purpose: Test structural entrenchment via blind persistence.

Per spec §RSA v1.0 Run Sequence:
- Model: ALWAYS_SELF_RENEW
- Always emits commitment-satisfying actions
- Maintains continuous eligibility for automatic renewal
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
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel


@dataclass
class RunConfig:
    """Configuration for RSA v1.0 Run 4."""

    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    amnesty_interval: int = 10
    seeds: List[int] = None

    def __post_init__(self):
        if self.seeds is None:
            self.seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]


def run_entrenchment(config: RunConfig, verbose: bool = False) -> List[Dict[str, Any]]:
    """Run entrenchment experiments."""
    results = []

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        amnesty_interval=config.amnesty_interval,
    )

    for seed in config.seeds:
        print(f"Running ALWAYS_SELF_RENEW seed={seed}...")

        policy_config = RSAPolicyConfig(
            policy_model=RSAPolicyModel.ALWAYS_SELF_RENEW,
            epoch_size=config.renewal_check_interval,
        )

        harness = ALSHarnessV080(
            seed=seed,
            config=als_config,
            verbose=verbose,
            rsa_policy_config=policy_config,
        )
        result = harness.run()

        # Compute AA
        total_epochs = config.max_cycles // config.renewal_check_interval
        authority_epochs = len([r for r in harness._semantic_epoch_records if r.sem_pass])
        aa = authority_epochs / max(total_epochs, 1)

        # Compute AAA (asymptotic authority availability)
        tail_window = max(5000, total_epochs // 5)
        if len(harness._semantic_epoch_records) >= tail_window:
            tail_records = harness._semantic_epoch_records[-tail_window:]
            tail_passes = len([r for r in tail_records if r.sem_pass])
            aaa = tail_passes / tail_window
        else:
            aaa = aa  # Fall back to AA if not enough epochs

        # Track telemetry
        v10_telemetry = harness._rsa_v10_epoch_telemetry if hasattr(harness, '_rsa_v10_epoch_telemetry') else []

        run_result = {
            "run_id": f"rsa_v100_run4_entrenchment_seed{seed}",
            "seed": seed,
            "rsa_model": "ALWAYS_SELF_RENEW",
            "rsa_policy_enabled": True,
            "total_cycles": result.total_cycles,
            "total_epochs": total_epochs,
            "total_renewals": result.total_renewals,
            "total_expirations": result.total_expirations,
            "stop_reason": result.stop_reason.name,
            "authority_availability_ppm": int(aa * 1_000_000),
            "asymptotic_authority_availability_ppm": int(aaa * 1_000_000),
            "final_streak": harness._semantic_fail_streak.get(harness._active_policy_id, 0),
            "telemetry_sample_count": len(v10_telemetry),
        }
        results.append(run_result)

        print(f"  Cycles={result.total_cycles}, AA={aa:.4f}, AAA={aaa:.4f}, Renewals={result.total_renewals}")

    return results


def main():
    """Run entrenchment experiments and save results."""
    print("=" * 60)
    print("RSA v1.0 Run 4: Blind Succession Avoidance (ALWAYS_SELF_RENEW)")
    print("=" * 60)
    print()

    config = RunConfig()

    print(f"Configuration:")
    print(f"  max_cycles: {config.max_cycles}")
    print(f"  seeds: {config.seeds}")
    print()

    results = run_entrenchment(config)

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    aa_values = [r["authority_availability_ppm"] / 1_000_000 for r in results]
    aaa_values = [r["asymptotic_authority_availability_ppm"] / 1_000_000 for r in results]
    mean_aa = sum(aa_values) / len(aa_values)
    mean_aaa = sum(aaa_values) / len(aaa_values)

    print(f"Mean AA:  {mean_aa:.4f}")
    print(f"Mean AAA: {mean_aaa:.4f}")
    print(f"AA range:  [{min(aa_values):.4f}, {max(aa_values):.4f}]")
    print(f"AAA range: [{min(aaa_values):.4f}, {max(aaa_values):.4f}]")

    # Note about entrenchment
    print()
    print("Note: ALWAYS_SELF_RENEW should maintain near-100% AA/AAA")
    print("by continuously satisfying all commitments, demonstrating")
    print("structural entrenchment via blind persistence.")

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"rsa_v100_run4_entrenchment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "run_type": "RSA v1.0 Run 4: Blind Succession Avoidance",
            "config": asdict(config),
            "results": results,
            "summary": {
                "mean_authority_availability": mean_aa,
                "mean_asymptotic_authority_availability": mean_aaa,
            }
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
