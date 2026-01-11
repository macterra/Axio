#!/usr/bin/env python3
"""
RSA v2.0 Run 1: Binary Outcome Adaptation (OUTCOME_TOGGLE)

Model F: Minimal adaptive adversary with binary outcome reactivity.
- lapse_occurred=True → ACTION_INVALID_COMMIT
- otherwise → ACTION_MAX_RENT

Collects telemetry to prove model activation via primitive emission counts.
Activation MUST be proven by telemetry, not outcome deltas.
"""
import sys
sys.path.insert(0, "src")

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import json
import statistics

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyModel, AdaptiveRSAWrapper

# Frozen protocol fingerprint
SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000
TAIL_WINDOW = 5000

# Protocol hashes from v2.0 implementation report
AKI_CONFIG_HASH = "fd58b6e5"
RSA_V2_CONFIG_HASH = "4e20b327"
OBSERVABLE_INTERFACE_HASH = "9afe2362"
STRATEGY_MAP_HASH = "9661d09d"
PRIMITIVE_MAP_HASH = "e3268435"


@dataclass
class TelemetryAccumulator:
    """Accumulates telemetry during a single run."""
    epochs_lapse_true: int = 0
    epochs_lapse_false: int = 0
    invalid_commit_epochs: int = 0
    max_rent_epochs: int = 0
    _seen_epochs: set = field(default_factory=set)


def make_telemetry_wrapper(accumulator: TelemetryAccumulator):
    """Create a telemetry-capturing intercept wrapper."""
    original_intercept = AdaptiveRSAWrapper.intercept

    def traced_intercept(self, observable, epoch, cycle_in_epoch, original_action):
        result = original_intercept(self, observable, epoch, cycle_in_epoch, original_action)

        # Only count once per epoch (first cycle)
        if epoch not in accumulator._seen_epochs:
            accumulator._seen_epochs.add(epoch)

            if observable.lapse_occurred:
                accumulator.epochs_lapse_true += 1
            else:
                accumulator.epochs_lapse_false += 1

            primitive = result.get('rsa_primitive', 'NONE')
            if primitive == 'INVALID_COMMIT':
                accumulator.invalid_commit_epochs += 1
            elif primitive == 'MAX_RENT':
                accumulator.max_rent_epochs += 1

        return result

    return traced_intercept


@dataclass
class Run1Metrics:
    """Metrics extracted for Run 1 analysis with telemetry."""
    seed: int
    AA_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    renewals_succeeded: int
    renewal_attempts: int
    renewal_success_rate_ppm: int
    # Telemetry (required for activation proof)
    epochs_lapse_true: int
    epochs_lapse_false: int
    invalid_commit_epochs: int
    max_rent_epochs: int


def run_with_rsa_telemetry(seed: int, config: ALSConfigV080, policy_config: RSAPolicyConfig) -> Tuple[Run1Metrics, TelemetryAccumulator]:
    """Run with RSA and telemetry collection."""
    accumulator = TelemetryAccumulator()

    # Patch intercept for this run
    original_intercept = AdaptiveRSAWrapper.intercept
    AdaptiveRSAWrapper.intercept = make_telemetry_wrapper(accumulator)

    try:
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()

        lapse_count = result.semantic_lapse_count + result.structural_lapse_count
        AA_ppm = int(result.authority_uptime_fraction * 1_000_000)

        if result.renewal_attempts > 0:
            renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
        else:
            renewal_success_rate_ppm = 0

        metrics = Run1Metrics(
            seed=seed,
            AA_ppm=AA_ppm,
            failure_class=result.stop_reason.name if result.stop_reason else "NONE",
            lapse_count=lapse_count,
            total_lapse_epochs=result.total_lapse_duration_epochs,
            renewals_succeeded=result.renewal_successes,
            renewal_attempts=result.renewal_attempts,
            renewal_success_rate_ppm=renewal_success_rate_ppm,
            epochs_lapse_true=accumulator.epochs_lapse_true,
            epochs_lapse_false=accumulator.epochs_lapse_false,
            invalid_commit_epochs=accumulator.invalid_commit_epochs,
            max_rent_epochs=accumulator.max_rent_epochs,
        )

        return metrics, accumulator
    finally:
        # Restore original intercept
        AdaptiveRSAWrapper.intercept = original_intercept


def run_baseline(seed: int, config: ALSConfigV080) -> Run1Metrics:
    """Run baseline (no RSA) for comparison."""
    harness = ALSHarnessV080(seed=seed, config=config)
    result = harness.run()

    lapse_count = result.semantic_lapse_count + result.structural_lapse_count
    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)

    if result.renewal_attempts > 0:
        renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

    return Run1Metrics(
        seed=seed,
        AA_ppm=AA_ppm,
        failure_class=result.stop_reason.name if result.stop_reason else "NONE",
        lapse_count=lapse_count,
        total_lapse_epochs=result.total_lapse_duration_epochs,
        renewals_succeeded=result.renewal_successes,
        renewal_attempts=result.renewal_attempts,
        renewal_success_rate_ppm=renewal_success_rate_ppm,
        epochs_lapse_true=0,  # Not tracked for baseline
        epochs_lapse_false=0,
        invalid_commit_epochs=0,
        max_rent_epochs=0,
    )


def main():
    print("=" * 80)
    print("RSA v2.0 RUN 1: OUTCOME_TOGGLE (Model F)")
    print("=" * 80)

    # Protocol fingerprint
    print("\n--- Protocol Fingerprint ---")
    print(f"AKI Config Hash:            {AKI_CONFIG_HASH}")
    print(f"RSA v2.0 Config Hash:       {RSA_V2_CONFIG_HASH}")
    print(f"Observable Interface Hash:  {OBSERVABLE_INTERFACE_HASH}")
    print(f"Strategy Map Hash:          {STRATEGY_MAP_HASH}")
    print(f"Primitive Map Hash:         {PRIMITIVE_MAP_HASH}")
    print(f"Seeds:                      {SEEDS}")
    print(f"Horizon:                    {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    print()

    # Configuration (frozen)
    config = ALSConfigV080(
        max_cycles=MAX_CYCLES,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
    )

    # Compute AKI config hash
    config_dict = {
        "max_cycles": config.max_cycles,
        "renewal_check_interval": config.renewal_check_interval,
        "eligibility_threshold_k": config.eligibility_threshold_k,
        "amnesty_interval": config.amnesty_interval,
        "amnesty_decay": config.amnesty_decay,
        "cta_enabled": config.cta_enabled,
    }
    aki_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:8]
    print(f"Computed AKI Config Hash: {aki_hash}")

    # RSA v2.0 config
    policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.OUTCOME_TOGGLE,
        rsa_version="v2",
        epoch_size=RENEWAL_CHECK_INTERVAL,
        rsa_invalid_target_key="C0",
    )

    # Compute RSA config hash
    rsa_config_dict = {
        "policy_model": policy_config.policy_model.value,
        "rsa_version": policy_config.rsa_version,
        "epoch_size": policy_config.epoch_size,
        "rsa_invalid_target_key": policy_config.rsa_invalid_target_key,
    }
    rsa_hash = hashlib.sha256(json.dumps(rsa_config_dict, sort_keys=True).encode()).hexdigest()[:8]
    print(f"Computed RSA Config Hash: {rsa_hash}")
    print()

    # Run baseline for each seed
    print("=" * 80)
    print("PHASE 1: BASELINE (RSA DISABLED)")
    print("=" * 80)
    baseline_results: Dict[int, Run1Metrics] = {}
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics = run_baseline(seed, config)
        baseline_results[seed] = metrics
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}")

    # Run OUTCOME_TOGGLE for each seed with telemetry
    print()
    print("=" * 80)
    print("PHASE 2: MODEL F (OUTCOME_TOGGLE) WITH TELEMETRY")
    print("=" * 80)
    run1_results: Dict[int, Run1Metrics] = {}
    telemetry_by_seed: Dict[int, TelemetryAccumulator] = {}

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, accum = run_with_rsa_telemetry(seed, config, policy_config)
        run1_results[seed] = metrics
        telemetry_by_seed[seed] = accum
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"lapse_obs={metrics.epochs_lapse_true}, "
              f"inv={metrics.invalid_commit_epochs}, max={metrics.max_rent_epochs}")

    # Telemetry summary per seed
    print()
    print("=" * 80)
    print("TELEMETRY SUMMARY (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'lapse=T':>10} {'lapse=F':>10} {'INV_CMT':>10} {'MAX_RENT':>10}")
    print("-" * 60)

    total_lapse_true = 0
    total_lapse_false = 0
    total_invalid_commit = 0
    total_max_rent = 0

    for seed in SEEDS:
        m = run1_results[seed]
        print(f"{seed:>8} {m.epochs_lapse_true:>10} {m.epochs_lapse_false:>10} "
              f"{m.invalid_commit_epochs:>10} {m.max_rent_epochs:>10}")
        total_lapse_true += m.epochs_lapse_true
        total_lapse_false += m.epochs_lapse_false
        total_invalid_commit += m.invalid_commit_epochs
        total_max_rent += m.max_rent_epochs

    print("-" * 60)
    print(f"{'TOTAL':>8} {total_lapse_true:>10} {total_lapse_false:>10} "
          f"{total_invalid_commit:>10} {total_max_rent:>10}")

    # Conditional probabilities
    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION (CONDITIONAL PROBABILITIES)")
    print("=" * 80)

    if total_lapse_true > 0:
        p_invalid_given_lapse = total_invalid_commit / total_lapse_true
    else:
        p_invalid_given_lapse = 0.0

    if total_lapse_false > 0:
        p_maxrent_given_no_lapse = total_max_rent / total_lapse_false
    else:
        p_maxrent_given_no_lapse = 0.0

    print(f"  P(INVALID_COMMIT | lapse=True):  {total_invalid_commit}/{total_lapse_true} = {p_invalid_given_lapse:.6f}")
    print(f"  P(MAX_RENT | lapse=False):       {total_max_rent}/{total_lapse_false} = {p_maxrent_given_no_lapse:.6f}")
    print()

    if p_invalid_given_lapse == 1.0 and p_maxrent_given_no_lapse == 1.0:
        print("  ✅ Model F ACTIVATION VERIFIED: Strategy map executed correctly")
        activation_verified = True
    else:
        print("  ❌ Model F ACTIVATION FAILED: Conditional probabilities not 1.0")
        activation_verified = False

    # Comparison table
    print()
    print("=" * 80)
    print("BASELINE VS RUN 1 COMPARISON")
    print("=" * 80)
    print(f"{'Seed':>8} {'Base AA':>12} {'Run1 AA':>12} {'Δ AA':>10} {'Identical?':>12}")
    print("-" * 60)

    identical_count = 0
    aa_deltas = []
    for seed in SEEDS:
        base = baseline_results[seed]
        run1 = run1_results[seed]
        delta = run1.AA_ppm - base.AA_ppm
        aa_deltas.append(delta)
        is_identical = (base.AA_ppm == run1.AA_ppm)
        if is_identical:
            identical_count += 1
        print(f"{seed:>8} {base.AA_ppm:>12} {run1.AA_ppm:>12} {delta:>+10} {'YES' if is_identical else 'NO':>12}")

    print()
    print(f"Seeds with identical AA: {identical_count}/10")
    if aa_deltas:
        print(f"Mean AA delta: {statistics.mean(aa_deltas):+.1f} ppm")
        if len(aa_deltas) > 1:
            print(f"StdDev AA delta: {statistics.stdev(aa_deltas):.1f} ppm")

    # Failure class distribution
    print()
    print("--- Failure Class Distribution ---")
    base_class_dist: Dict[str, int] = {}
    run1_class_dist: Dict[str, int] = {}
    for seed in SEEDS:
        fc = baseline_results[seed].failure_class
        base_class_dist[fc] = base_class_dist.get(fc, 0) + 1
        fc = run1_results[seed].failure_class
        run1_class_dist[fc] = run1_class_dist.get(fc, 0) + 1
    print(f"  Baseline: {base_class_dist}")
    print(f"  Run 1:    {run1_class_dist}")

    # Final summary
    print()
    print("=" * 80)
    print("RUN 1 SUMMARY")
    print("=" * 80)
    print(f"  Activation verified: {'YES' if activation_verified else 'NO'}")
    print(f"  Total epochs (10 seeds): {(total_lapse_true + total_lapse_false)}")
    print(f"  Epochs with lapse=True: {total_lapse_true}")
    print(f"  INVALID_COMMIT emissions: {total_invalid_commit}")
    print(f"  MAX_RENT emissions: {total_max_rent}")
    print(f"  Identical outcomes to baseline: {identical_count}/10 seeds")
    print()
    print("=" * 80)
    print("RUN 1 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
