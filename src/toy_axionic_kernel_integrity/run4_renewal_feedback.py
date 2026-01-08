#!/usr/bin/env python3
"""
RSA v2.0 Run 4: Renewal-Outcome Feedback (RENEWAL_FEEDBACK)

Model I: Stateless adversary that branches on renewal outcome.

Strategy Map (Model I):
| Renewal Outcome     | Action Primitive    |
|---------------------|---------------------|
| SUCCEEDED           | MAX_RENT            |
| FAILED              | INVALID_COMMIT      |
| NOT_ATTEMPTED       | MIN_EFFORT          |

Research Question:
Can an adversary that conditions behavior on renewal outcomes (succeeded/failed/not-attempted)
defeat constitutional survivability under RSA constraints?

Telemetry Requirements for Activation Proof:
- P(MAX_RENT | SUCCEEDED) = 1.0
- P(INVALID_COMMIT | FAILED) = 1.0
- P(MIN_EFFORT | NOT_ATTEMPTED) = 1.0

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
from toy_aki.rsa.policy import (
    RSAPolicyConfig, RSAPolicyModel, AdaptiveRSAWrapper, RenewalOutcome
)

# Frozen protocol fingerprint
SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000
TAIL_WINDOW = 5000
ELIGIBILITY_THRESHOLD_K = 3

# Protocol hashes from v2.0 implementation report
ALSCONFIG_PARAMETER_HASH = "fd58b6e5"
RSA_V2_CONFIG_HASH = "4e20b327"
OBSERVABLE_INTERFACE_HASH = "9afe2362"
HARNESS_PATCH = "v0.8.1-lapse-tracking"


@dataclass
class RenewalTelemetry:
    """Tracks per-renewal-outcome observations and primitive emissions."""
    # Outcome observation counts
    epochs_succeeded: int = 0
    epochs_failed: int = 0
    epochs_not_attempted: int = 0

    # Primitive emission counts (per outcome)
    max_rent_in_succeeded: int = 0
    invalid_commit_in_failed: int = 0
    min_effort_in_not_attempted: int = 0

    # Cross-validation: wrong primitives (should all be 0)
    wrong_primitive_count: int = 0

    _seen_epochs: set = field(default_factory=set)


def make_renewal_telemetry_wrapper(telemetry: RenewalTelemetry):
    """Create a telemetry-capturing intercept wrapper for renewal outcome tracking."""
    original_intercept = AdaptiveRSAWrapper.intercept

    def traced_intercept(self, observable, epoch, cycle_in_epoch, original_action):
        result = original_intercept(self, observable, epoch, cycle_in_epoch, original_action)

        # Only count once per epoch (first cycle)
        if epoch not in telemetry._seen_epochs:
            telemetry._seen_epochs.add(epoch)

            outcome = observable.renewal_outcome
            primitive = result.get('rsa_primitive', 'NONE')

            # Track outcome observations and verify primitive mapping
            if outcome == RenewalOutcome.SUCCEEDED:
                telemetry.epochs_succeeded += 1
                if primitive == 'MAX_RENT':
                    telemetry.max_rent_in_succeeded += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif outcome == RenewalOutcome.FAILED:
                telemetry.epochs_failed += 1
                if primitive == 'INVALID_COMMIT':
                    telemetry.invalid_commit_in_failed += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif outcome == RenewalOutcome.NOT_ATTEMPTED:
                telemetry.epochs_not_attempted += 1
                if primitive == 'MIN_EFFORT':
                    telemetry.min_effort_in_not_attempted += 1
                else:
                    telemetry.wrong_primitive_count += 1

        return result

    def restore_original():
        """Restore original intercept method."""
        AdaptiveRSAWrapper.intercept = original_intercept

    return traced_intercept, restore_original


@dataclass
class Run4Metrics:
    """Metrics extracted for Run 4 analysis with renewal telemetry."""
    seed: int
    AA_ppm: int
    AAA_ppm: int  # Tail window AA
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    max_single_lapse_epochs: int
    renewals_succeeded: int
    renewal_attempts: int
    renewal_success_rate_ppm: int
    # Renewal outcome telemetry
    epochs_succeeded: int
    epochs_failed: int
    epochs_not_attempted: int
    max_rent_in_succeeded: int
    invalid_commit_in_failed: int
    min_effort_in_not_attempted: int
    wrong_primitive_count: int


def compute_aaa(result, tail_window: int = TAIL_WINDOW) -> int:
    """Compute asymptotic authority availability (tail window)."""
    return int(result.authority_uptime_fraction * 1_000_000)


def run_with_renewal_telemetry(
    seed: int,
    config: ALSConfigV080,
    policy_config: RSAPolicyConfig
) -> Tuple[Run4Metrics, RenewalTelemetry]:
    """Run with RENEWAL_FEEDBACK policy and telemetry collection."""
    telemetry = RenewalTelemetry()

    # Patch intercept for this run
    traced_intercept, restore_original = make_renewal_telemetry_wrapper(telemetry)
    AdaptiveRSAWrapper.intercept = traced_intercept

    try:
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()

        lapse_count = result.semantic_lapse_count + result.structural_lapse_count
        AA_ppm = int(result.authority_uptime_fraction * 1_000_000)
        AAA_ppm = compute_aaa(result)

        if result.renewal_attempts > 0:
            renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
        else:
            renewal_success_rate_ppm = 0

        max_single_lapse = result.max_lapse_duration_epochs if hasattr(result, 'max_lapse_duration_epochs') else 0

        metrics = Run4Metrics(
            seed=seed,
            AA_ppm=AA_ppm,
            AAA_ppm=AAA_ppm,
            failure_class=result.stop_reason.name if result.stop_reason else "NONE",
            lapse_count=lapse_count,
            total_lapse_epochs=result.total_lapse_duration_epochs,
            max_single_lapse_epochs=max_single_lapse,
            renewals_succeeded=result.renewal_successes,
            renewal_attempts=result.renewal_attempts,
            renewal_success_rate_ppm=renewal_success_rate_ppm,
            epochs_succeeded=telemetry.epochs_succeeded,
            epochs_failed=telemetry.epochs_failed,
            epochs_not_attempted=telemetry.epochs_not_attempted,
            max_rent_in_succeeded=telemetry.max_rent_in_succeeded,
            invalid_commit_in_failed=telemetry.invalid_commit_in_failed,
            min_effort_in_not_attempted=telemetry.min_effort_in_not_attempted,
            wrong_primitive_count=telemetry.wrong_primitive_count,
        )

        return metrics, telemetry
    finally:
        restore_original()


def run_baseline(seed: int, config: ALSConfigV080) -> Run4Metrics:
    """Run baseline (no RSA) for comparison."""
    harness = ALSHarnessV080(seed=seed, config=config)
    result = harness.run()

    lapse_count = result.semantic_lapse_count + result.structural_lapse_count
    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)
    AAA_ppm = compute_aaa(result)

    if result.renewal_attempts > 0:
        renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

    max_single_lapse = result.max_lapse_duration_epochs if hasattr(result, 'max_lapse_duration_epochs') else 0

    return Run4Metrics(
        seed=seed,
        AA_ppm=AA_ppm,
        AAA_ppm=AAA_ppm,
        failure_class=result.stop_reason.name if result.stop_reason else "NONE",
        lapse_count=lapse_count,
        total_lapse_epochs=result.total_lapse_duration_epochs,
        max_single_lapse_epochs=max_single_lapse,
        renewals_succeeded=result.renewal_successes,
        renewal_attempts=result.renewal_attempts,
        renewal_success_rate_ppm=renewal_success_rate_ppm,
        # No RSA telemetry in baseline
        epochs_succeeded=0,
        epochs_failed=0,
        epochs_not_attempted=0,
        max_rent_in_succeeded=0,
        invalid_commit_in_failed=0,
        min_effort_in_not_attempted=0,
        wrong_primitive_count=0,
    )


def compute_config_hash(config: ALSConfigV080) -> str:
    """Compute hash of AKI configuration for reproducibility."""
    config_dict = {
        "max_cycles": config.max_cycles,
        "renewal_check_interval": config.renewal_check_interval,
        "eligibility_threshold_k": config.eligibility_threshold_k,
        "amnesty_interval": config.amnesty_interval,
        "amnesty_decay": config.amnesty_decay,
        "cta_enabled": config.cta_enabled,
    }
    config_json = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()[:8]


def compute_rsa_config_hash(config: RSAPolicyConfig) -> str:
    """Compute hash of RSA v2.0 configuration."""
    config_dict = {
        "policy_model": config.policy_model.value,
        "rsa_version": config.rsa_version,
        "epoch_size": config.epoch_size,
        "rsa_invalid_target_key": config.rsa_invalid_target_key,
    }
    config_json = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()[:8]


def main():
    print("=" * 80)
    print("RSA v2.0 RUN 4: RENEWAL_FEEDBACK (Model I)")
    print("=" * 80)
    print()

    # Build frozen configuration
    als_config = ALSConfigV080(
        max_cycles=MAX_CYCLES,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        eligibility_threshold_k=ELIGIBILITY_THRESHOLD_K,
        amnesty_interval=10,
        amnesty_decay=1,
        cta_enabled=True,
    )

    rsa_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.RENEWAL_FEEDBACK,
        rsa_version="v2",
        epoch_size=RENEWAL_CHECK_INTERVAL,
        rsa_invalid_target_key="C0",
    )

    # Print protocol fingerprint
    print("--- Protocol Fingerprint ---")
    print(f"ALSConfig Parameter Hash:    {ALSCONFIG_PARAMETER_HASH}")
    rsa_hash = compute_rsa_config_hash(rsa_config)
    print(f"RSA v2.0 Config Hash:        {rsa_hash}")
    print(f"Observable Interface Hash:   {OBSERVABLE_INTERFACE_HASH}")
    print(f"Harness Patch:               {HARNESS_PATCH}")
    print(f"Eligibility Threshold K:     {ELIGIBILITY_THRESHOLD_K}")
    print(f"Seeds:                       {SEEDS}")
    print(f"Horizon:                     {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    print()

    # Print strategy map
    print("--- Model I Strategy Map ---")
    print("  SUCCEEDED       → MAX_RENT")
    print("  FAILED          → INVALID_COMMIT")
    print("  NOT_ATTEMPTED   → MIN_EFFORT")
    print()

    # Verify config hashes
    computed_als_hash = compute_config_hash(als_config)
    print(f"Computed ALSConfig Hash: {computed_als_hash}")
    print(f"Computed RSA Config Hash: {rsa_hash}")
    print()

    # ==========================================================================
    # PHASE 1: BASELINE (RSA DISABLED)
    # ==========================================================================
    print("=" * 80)
    print("PHASE 1: BASELINE (RSA DISABLED)")
    print("=" * 80)

    baseline_results: List[Run4Metrics] = []
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics = run_baseline(seed, als_config)
        baseline_results.append(metrics)
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}")

    # ==========================================================================
    # PHASE 2: MODEL I (RENEWAL_FEEDBACK) WITH TELEMETRY
    # ==========================================================================
    print()
    print("=" * 80)
    print("PHASE 2: MODEL I (RENEWAL_FEEDBACK) WITH TELEMETRY")
    print("=" * 80)

    run4_results: List[Run4Metrics] = []
    run4_telemetry: List[RenewalTelemetry] = []
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, telemetry = run_with_renewal_telemetry(seed, als_config, rsa_config)
        run4_results.append(metrics)
        run4_telemetry.append(telemetry)
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"outcomes=[S:{metrics.epochs_succeeded},F:{metrics.epochs_failed},N:{metrics.epochs_not_attempted}]")

    # ==========================================================================
    # RENEWAL OUTCOME DISTRIBUTION
    # ==========================================================================
    print()
    print("=" * 80)
    print("RENEWAL OUTCOME DISTRIBUTION (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'SUCCEEDED':>10} {'FAILED':>10} {'NOT_ATMP':>10} {'TOTAL':>10} {'succ_frac':>10}")
    print("-" * 70)

    total_succeeded = 0
    total_failed = 0
    total_not_attempted = 0
    for m in run4_results:
        total = m.epochs_succeeded + m.epochs_failed + m.epochs_not_attempted
        succ_frac = m.epochs_succeeded / total * 100 if total > 0 else 0
        print(f"{m.seed:>8} {m.epochs_succeeded:>10} {m.epochs_failed:>10} "
              f"{m.epochs_not_attempted:>10} {total:>10} {succ_frac:>9.1f}%")
        total_succeeded += m.epochs_succeeded
        total_failed += m.epochs_failed
        total_not_attempted += m.epochs_not_attempted

    grand_total = total_succeeded + total_failed + total_not_attempted
    succ_frac = total_succeeded / grand_total * 100 if grand_total > 0 else 0
    print("-" * 70)
    print(f"{'TOTAL':>8} {total_succeeded:>10} {total_failed:>10} "
          f"{total_not_attempted:>10} {grand_total:>10} {succ_frac:>9.1f}%")

    # ==========================================================================
    # PRIMITIVE EMISSIONS BY OUTCOME
    # ==========================================================================
    print()
    print("=" * 80)
    print("PRIMITIVE EMISSIONS BY OUTCOME (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'MAX_RENT':>10} {'INV_CMT':>10} {'MIN_EFF':>10} {'WRONG':>10}")
    print(f"{'':>8} {'(SUCC)':>10} {'(FAIL)':>10} {'(NOT_AT)':>10} {'':>10}")
    print("-" * 60)

    total_max_rent = 0
    total_inv_cmt = 0
    total_min_eff = 0
    total_wrong = 0
    for m in run4_results:
        print(f"{m.seed:>8} {m.max_rent_in_succeeded:>10} {m.invalid_commit_in_failed:>10} "
              f"{m.min_effort_in_not_attempted:>10} {m.wrong_primitive_count:>10}")
        total_max_rent += m.max_rent_in_succeeded
        total_inv_cmt += m.invalid_commit_in_failed
        total_min_eff += m.min_effort_in_not_attempted
        total_wrong += m.wrong_primitive_count

    print("-" * 60)
    print(f"{'TOTAL':>8} {total_max_rent:>10} {total_inv_cmt:>10} "
          f"{total_min_eff:>10} {total_wrong:>10}")

    # ==========================================================================
    # ACTIVATION VERIFICATION
    # ==========================================================================
    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION (CONDITIONAL PROBABILITIES)")
    print("=" * 80)

    # P(MAX_RENT | SUCCEEDED)
    if total_succeeded > 0:
        p_max_rent_given_succ = total_max_rent / total_succeeded
    else:
        p_max_rent_given_succ = 0.0

    # P(INVALID_COMMIT | FAILED)
    if total_failed > 0:
        p_inv_cmt_given_fail = total_inv_cmt / total_failed
    else:
        p_inv_cmt_given_fail = 0.0

    # P(MIN_EFFORT | NOT_ATTEMPTED)
    if total_not_attempted > 0:
        p_min_eff_given_not = total_min_eff / total_not_attempted
    else:
        p_min_eff_given_not = 0.0

    print(f"  P(MAX_RENT | SUCCEEDED):      {total_max_rent}/{total_succeeded} = {p_max_rent_given_succ:.6f}")
    print(f"  P(INVALID_COMMIT | FAILED):   {total_inv_cmt}/{total_failed} = {p_inv_cmt_given_fail:.6f}")
    print(f"  P(MIN_EFFORT | NOT_ATTEMPTED): {total_min_eff}/{total_not_attempted} = {p_min_eff_given_not:.6f}")
    print()

    # Check activation
    activation_verified = (
        p_max_rent_given_succ == 1.0 and
        p_inv_cmt_given_fail == 1.0 and
        p_min_eff_given_not == 1.0 and
        total_wrong == 0
    )

    if activation_verified:
        print("  ✅ Model I ACTIVATION VERIFIED: Strategy map executed correctly")
    else:
        print("  ❌ Model I ACTIVATION FAILED: Strategy map mismatch")
        if total_wrong > 0:
            print(f"     Wrong primitive emissions: {total_wrong}")

    # ==========================================================================
    # BASELINE COMPARISON
    # ==========================================================================
    print()
    print("=" * 80)
    print("BASELINE VS RUN 4 COMPARISON")
    print("=" * 80)
    print(f"{'Seed':>8} {'Base AA':>12} {'Run4 AA':>12} {'Δ AA':>8} "
          f"{'Base Lapse':>12} {'Run4 Lapse':>12}")
    print("-" * 80)

    identical_count = 0
    aa_deltas = []
    for base, run4 in zip(baseline_results, run4_results):
        delta = run4.AA_ppm - base.AA_ppm
        aa_deltas.append(delta)
        identical = delta == 0
        if identical:
            identical_count += 1
        print(f"{base.seed:>8} {base.AA_ppm:>12} {run4.AA_ppm:>12} {delta:>+8} "
              f"{base.lapse_count:>12} {run4.lapse_count:>12}")

    print()
    print(f"Seeds with identical AA: {identical_count}/{len(SEEDS)}")
    print(f"Mean AA delta: {statistics.mean(aa_deltas):.1f} ppm")
    print(f"StdDev AA delta: {statistics.stdev(aa_deltas):.1f} ppm")

    # Failure class distribution
    baseline_classes = {}
    run4_classes = {}
    for m in baseline_results:
        baseline_classes[m.failure_class] = baseline_classes.get(m.failure_class, 0) + 1
    for m in run4_results:
        run4_classes[m.failure_class] = run4_classes.get(m.failure_class, 0) + 1

    print()
    print("--- Failure Class Distribution ---")
    print(f"  Baseline: {baseline_classes}")
    print(f"  Run 4:    {run4_classes}")

    # ==========================================================================
    # RUN 4 SUMMARY
    # ==========================================================================
    print()
    print("=" * 80)
    print("RUN 4 SUMMARY")
    print("=" * 80)
    print(f"  Activation verified:     {'YES' if activation_verified else 'NO'}")
    print(f"  Total epochs observed:   {grand_total}")
    print(f"  Outcome distribution:")
    print(f"    SUCCEEDED:      {total_succeeded} ({total_succeeded/grand_total*100:.1f}%)")
    print(f"    FAILED:         {total_failed} ({total_failed/grand_total*100:.1f}%)")
    print(f"    NOT_ATTEMPTED:  {total_not_attempted} ({total_not_attempted/grand_total*100:.1f}%)")
    print(f"  Primitive emissions by outcome:")
    print(f"    MAX_RENT (SUCCEEDED):      {total_max_rent}")
    print(f"    INVALID_COMMIT (FAILED):   {total_inv_cmt}")
    print(f"    MIN_EFFORT (NOT_ATTEMPTED): {total_min_eff}")
    print(f"  Wrong primitive emissions:   {total_wrong}")
    print(f"  Identical outcomes to baseline: {identical_count}/{len(SEEDS)} seeds")

    # Terminal failure check
    terminal_failures = [m for m in run4_results if m.failure_class not in ("HORIZON_EXHAUSTED",)]
    print(f"  Terminal failure modes:      {'YES' if terminal_failures else 'NO'}")

    print()
    print("=" * 80)
    print("RUN 4 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
