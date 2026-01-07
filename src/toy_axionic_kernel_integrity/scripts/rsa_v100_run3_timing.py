"""
RSA v1.0 Run 3: Fixed Timing Misuse (FIXED_RENEWAL_TIMING)

Purpose: Test timing misuse without feedback exploitation.

Per spec §RSA v1.0 Run Sequence:
- Model: FIXED_RENEWAL_TIMING
- Sweep: renewal offsets and periods

Expected outcomes (fail-streak semantics, K=3):
- Period ≤ 3: Max consecutive fails = period-1 < K → always eligible
- Period = 4: Max consecutive fails = 3 = K → CRITICAL THRESHOLD (becomes ineligible)
- Period ≥ 5: Max consecutive fails > K → periodic ineligibility → degradation
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel
from scripts.rsa_v100_metrics import compute_consecutive_metrics, extract_sem_pass_sequence


@dataclass
class RunConfig:
    """Configuration for RSA v1.0 Run 3."""

    max_cycles: int = 300_000
    renewal_check_interval: int = 50
    eligibility_threshold_k: int = 3
    amnesty_interval: int = 10
    seeds: List[int] = None

    # Timing sweep parameters: (offset, period)
    timing_params: List[Tuple[int, int]] = None

    def __post_init__(self):
        if self.seeds is None:
            self.seeds = [42, 137, 256, 512, 1024]  # Fewer seeds for sweep
        if self.timing_params is None:
            # Various timing patterns:
            # (0, 1) = satisfy every epoch → max_consec_fail=0 → always eligible
            # (0, 2) = satisfy every other epoch → max_consec_fail=1 → always eligible
            # (0, 3) = satisfy every 3rd epoch → max_consec_fail=2 → always eligible
            # (0, 4) = satisfy every 4th epoch → max_consec_fail=3 → CRITICAL THRESHOLD (K=3)
            # (0, 5) = satisfy every 5th epoch → max_consec_fail=4 → becomes ineligible
            # (1, 3) = offset by 1 in period of 3
            # (2, 5) = offset pattern
            self.timing_params = [
                (0, 1),  # Every epoch (baseline for this model)
                (0, 2),  # Every other epoch
                (0, 3),  # Every 3rd epoch (matches C2 pattern)
                (0, 4),  # Every 4th epoch - CRITICAL THRESHOLD
                (0, 5),  # Every 5th epoch
                (1, 3),  # Offset pattern
                (2, 5),  # Offset pattern
            ]


def run_fixed_timing(config: RunConfig, verbose: bool = False) -> List[Dict[str, Any]]:
    """Run fixed timing experiments."""
    results = []

    als_config = ALSConfigV080(
        max_cycles=config.max_cycles,
        renewal_check_interval=config.renewal_check_interval,
        eligibility_threshold_k=config.eligibility_threshold_k,
        amnesty_interval=config.amnesty_interval,
    )

    for offset, period in config.timing_params:
        for seed in config.seeds:
            print(f"Running FIXED_RENEWAL_TIMING offset={offset} period={period} seed={seed}...")

            policy_config = RSAPolicyConfig(
                policy_model=RSAPolicyModel.FIXED_RENEWAL_TIMING,
                timing_offset_epochs=offset,
                timing_period_epochs=period,
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

            # Expected satisfaction rate and max consecutive fails
            expected_satisfaction_rate = 1.0 / period
            expected_max_consec_fail = period - 1

            run_result = {
                "run_id": f"rsa_v100_run3_timing_o{offset}_p{period}_seed{seed}",
                "seed": seed,
                "rsa_model": "FIXED_RENEWAL_TIMING",
                "timing_offset": offset,
                "timing_period": period,
                "expected_satisfaction_rate": expected_satisfaction_rate,
                "expected_max_consec_fail": expected_max_consec_fail,
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
            print(f"  AA={aa:.4f}, MaxFail={consec_metrics['max_consecutive_sem_fail']}, Elig={elig_str}")

    return results


def main():
    """Run fixed timing experiments and save results."""
    print("=" * 60)
    print("RSA v1.0 Run 3: Fixed Timing Misuse (FIXED_RENEWAL_TIMING)")
    print("=" * 60)
    print()

    config = RunConfig()

    print(f"Configuration:")
    print(f"  max_cycles: {config.max_cycles}")
    print(f"  timing_params: {config.timing_params}")
    print(f"  seeds: {config.seeds}")
    print()

    results = run_fixed_timing(config)

    # Summary by timing pattern
    print()
    print("=" * 60)
    print("Summary by Timing Pattern")
    print("=" * 60)

    for offset, period in config.timing_params:
        pattern_results = [r for r in results
                          if r["timing_offset"] == offset and r["timing_period"] == period]
        aa_values = [r["authority_availability_ppm"] / 1_000_000 for r in pattern_results]
        mean_aa = sum(aa_values) / len(aa_values)
        # Count runs that NEVER became ineligible
        always_eligible_count = sum(1 for r in pattern_results if not r["ever_ineligible"])
        max_fail = max(r["max_consecutive_sem_fail"] for r in pattern_results)
        elig_str = "✓" if always_eligible_count == len(pattern_results) else f"{always_eligible_count}/{len(pattern_results)}"
        print(f"offset={offset}, period={period}: AA={mean_aa:.4f}, MaxFail={max_fail}, AlwaysElig={elig_str}")

    # Save results
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"rsa_v100_run3_timing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "run_type": "RSA v1.0 Run 3: Fixed Timing Misuse",
            "config": asdict(config),
            "results": results,
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
