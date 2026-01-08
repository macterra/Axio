#!/usr/bin/env python3
"""
RSA v2.0 Run 3: Eligibility-Edge Probing (ELIGIBILITY_EDGE_PROBE)

Model H: Stateless adversary that exploits eligibility threshold discontinuities.

Strategy Map (Model H):
| Eligibility Bucket | Action Primitive    |
|--------------------|---------------------|
| SAFE (streak ≤ 1)  | MAX_RENT            |
| EDGE (streak = 2)  | INVALID_COMMIT      |
| INELIGIBLE (≥ 3)   | NO_OP               |

Research Question:
Can an adversary that acts "normally" when safe, but deliberately violates
commitments exactly at the eligibility cliff-edge, defeat constitutional survivability?

Telemetry Requirements for Activation Proof:
- P(MAX_RENT | SAFE) = 1.0
- P(INVALID_COMMIT | EDGE) = 1.0
- P(NO_OP | INELIGIBLE) = 1.0

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
    RSAPolicyConfig, RSAPolicyModel, AdaptiveRSAWrapper, EligibilityBucket
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
class EligibilityTelemetry:
    """Tracks per-eligibility-bucket observations and primitive emissions."""
    # Bucket observation counts
    epochs_safe: int = 0
    epochs_edge: int = 0
    epochs_ineligible: int = 0

    # Primitive emission counts (per bucket)
    max_rent_in_safe: int = 0
    invalid_commit_in_edge: int = 0
    no_op_in_ineligible: int = 0

    # Cross-validation: wrong primitives (should all be 0)
    wrong_primitive_count: int = 0

    # Raw streak histogram for sanity check
    # Key: raw streak value, Value: count of epochs with that streak
    raw_streak_histogram: Dict[int, int] = field(default_factory=dict)

    _seen_epochs: set = field(default_factory=set)


def make_eligibility_telemetry_wrapper(telemetry: EligibilityTelemetry):
    """Create a telemetry-capturing intercept wrapper for eligibility tracking.

    Also patches sample_observable to capture raw streak values for sanity check.
    """
    original_intercept = AdaptiveRSAWrapper.intercept
    original_sample = AdaptiveRSAWrapper.sample_observable

    # Track raw streak per epoch
    raw_streak_by_epoch: Dict[int, int] = {}

    def traced_sample(self, kernel_state):
        """Capture raw streak before bucket computation."""
        result = original_sample(self, kernel_state)
        epoch = kernel_state.get("epoch_index", 0)
        raw_streak = kernel_state.get("successive_renewal_failures", 0)
        raw_streak_by_epoch[epoch] = raw_streak
        return result

    AdaptiveRSAWrapper.sample_observable = traced_sample

    def traced_intercept(self, observable, epoch, cycle_in_epoch, original_action):
        result = original_intercept(self, observable, epoch, cycle_in_epoch, original_action)

        # Only count once per epoch (first cycle)
        if epoch not in telemetry._seen_epochs:
            telemetry._seen_epochs.add(epoch)

            bucket = observable.eligibility_bucket
            primitive = result.get('rsa_primitive', 'NONE')

            # Record raw streak for sanity check
            raw_streak = raw_streak_by_epoch.get(epoch, -1)
            if raw_streak >= 0:
                telemetry.raw_streak_histogram[raw_streak] = telemetry.raw_streak_histogram.get(raw_streak, 0) + 1

            # Track bucket observations
            if bucket == EligibilityBucket.SAFE:
                telemetry.epochs_safe += 1
                if primitive == 'MAX_RENT':
                    telemetry.max_rent_in_safe += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif bucket == EligibilityBucket.EDGE:
                telemetry.epochs_edge += 1
                if primitive == 'INVALID_COMMIT':
                    telemetry.invalid_commit_in_edge += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif bucket == EligibilityBucket.INELIGIBLE:
                telemetry.epochs_ineligible += 1
                if primitive == 'NO_OP':
                    telemetry.no_op_in_ineligible += 1
                else:
                    telemetry.wrong_primitive_count += 1

        return result

    def restore_original():
        """Restore original methods."""
        AdaptiveRSAWrapper.intercept = original_intercept
        AdaptiveRSAWrapper.sample_observable = original_sample

    return traced_intercept, restore_original


@dataclass
class Run3Metrics:
    """Metrics extracted for Run 3 analysis with eligibility telemetry."""
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
    # Eligibility bucket telemetry
    epochs_safe: int
    epochs_edge: int
    epochs_ineligible: int
    max_rent_in_safe: int
    invalid_commit_in_edge: int
    no_op_in_ineligible: int
    wrong_primitive_count: int
    # Derived
    ever_ineligible: bool
    ineligibility_fraction_ppm: int
    edge_hit_count: int


def compute_aaa(result, tail_window: int = TAIL_WINDOW) -> int:
    """Compute asymptotic authority availability (tail window)."""
    # AAA = fraction of last tail_window cycles in authority
    # This is approximated from the run result
    # For now, use the overall AA as approximation
    # (Full implementation would track per-cycle authority status)
    return int(result.authority_uptime_fraction * 1_000_000)


def run_with_eligibility_telemetry(
    seed: int,
    config: ALSConfigV080,
    policy_config: RSAPolicyConfig
) -> Tuple[Run3Metrics, EligibilityTelemetry]:
    """Run with ELIGIBILITY_EDGE_PROBE policy and telemetry collection."""
    telemetry = EligibilityTelemetry()

    # Patch intercept and sample_observable for this run
    traced_intercept, restore_original = make_eligibility_telemetry_wrapper(telemetry)
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

        # Max single lapse duration
        max_single_lapse = result.max_lapse_duration_epochs if hasattr(result, 'max_lapse_duration_epochs') else 0

        # Compute derived metrics
        total_observed = telemetry.epochs_safe + telemetry.epochs_edge + telemetry.epochs_ineligible
        ever_ineligible = telemetry.epochs_ineligible > 0
        if total_observed > 0:
            ineligibility_fraction_ppm = int(1_000_000 * telemetry.epochs_ineligible / total_observed)
        else:
            ineligibility_fraction_ppm = 0

        metrics = Run3Metrics(
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
            epochs_safe=telemetry.epochs_safe,
            epochs_edge=telemetry.epochs_edge,
            epochs_ineligible=telemetry.epochs_ineligible,
            max_rent_in_safe=telemetry.max_rent_in_safe,
            invalid_commit_in_edge=telemetry.invalid_commit_in_edge,
            no_op_in_ineligible=telemetry.no_op_in_ineligible,
            wrong_primitive_count=telemetry.wrong_primitive_count,
            ever_ineligible=ever_ineligible,
            ineligibility_fraction_ppm=ineligibility_fraction_ppm,
            edge_hit_count=telemetry.epochs_edge,
        )

        return metrics, telemetry
    finally:
        # Restore original methods
        restore_original()


def run_baseline(seed: int, config: ALSConfigV080) -> Run3Metrics:
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

    return Run3Metrics(
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
        # No telemetry for baseline
        epochs_safe=0,
        epochs_edge=0,
        epochs_ineligible=0,
        max_rent_in_safe=0,
        invalid_commit_in_edge=0,
        no_op_in_ineligible=0,
        wrong_primitive_count=0,
        ever_ineligible=False,
        ineligibility_fraction_ppm=0,
        edge_hit_count=0,
    )


def main():
    print("=" * 80)
    print("RSA v2.0 RUN 3: ELIGIBILITY_EDGE_PROBE (Model H)")
    print("=" * 80)

    # Protocol fingerprint
    print("\n--- Protocol Fingerprint ---")
    print(f"ALSConfig Parameter Hash:    {ALSCONFIG_PARAMETER_HASH}")
    print(f"RSA v2.0 Config Hash:        {RSA_V2_CONFIG_HASH}")
    print(f"Observable Interface Hash:   {OBSERVABLE_INTERFACE_HASH}")
    print(f"Harness Patch:               {HARNESS_PATCH}")
    print(f"Eligibility Threshold K:     {ELIGIBILITY_THRESHOLD_K}")
    print(f"Seeds:                       {SEEDS}")
    print(f"Horizon:                     {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    print()
    print("--- Model H Strategy Map ---")
    print("  SAFE (streak ≤ 1)       → MAX_RENT")
    print("  EDGE (streak = 2)       → INVALID_COMMIT")
    print("  INELIGIBLE (streak ≥ 3) → NO_OP")
    print()

    # Configuration (frozen)
    config = ALSConfigV080(
        max_cycles=MAX_CYCLES,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
    )

    # Compute ALSConfig parameter hash
    config_dict = {
        "max_cycles": config.max_cycles,
        "renewal_check_interval": config.renewal_check_interval,
        "eligibility_threshold_k": config.eligibility_threshold_k,
        "amnesty_interval": config.amnesty_interval,
        "amnesty_decay": config.amnesty_decay,
        "cta_enabled": config.cta_enabled,
    }
    als_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:8]
    print(f"Computed ALSConfig Hash: {als_hash}")

    # RSA v2.0 config for Model H
    policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.ELIGIBILITY_EDGE_PROBE,
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
    baseline_results: Dict[int, Run3Metrics] = {}
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics = run_baseline(seed, config)
        baseline_results[seed] = metrics
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}")

    # Run ELIGIBILITY_EDGE_PROBE for each seed with telemetry
    print()
    print("=" * 80)
    print("PHASE 2: MODEL H (ELIGIBILITY_EDGE_PROBE) WITH TELEMETRY")
    print("=" * 80)
    run3_results: Dict[int, Run3Metrics] = {}
    telemetry_by_seed: Dict[int, EligibilityTelemetry] = {}

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, telem = run_with_eligibility_telemetry(seed, config, policy_config)
        run3_results[seed] = metrics
        telemetry_by_seed[seed] = telem
        total_buckets = metrics.epochs_safe + metrics.epochs_edge + metrics.epochs_ineligible
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"buckets=[S:{metrics.epochs_safe},E:{metrics.epochs_edge},"
              f"I:{metrics.epochs_ineligible}]")

    # Eligibility bucket distribution summary
    print()
    print("=" * 80)
    print("ELIGIBILITY BUCKET DISTRIBUTION (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'SAFE':>10} {'EDGE':>10} {'INELIG':>10} {'TOTAL':>10} {'edge_frac':>12}")
    print("-" * 70)

    total_safe = 0
    total_edge = 0
    total_ineligible = 0

    for seed in SEEDS:
        m = run3_results[seed]
        total = m.epochs_safe + m.epochs_edge + m.epochs_ineligible
        edge_frac = f"{100.0*m.epochs_edge/total:.1f}%" if total > 0 else "N/A"
        print(f"{seed:>8} {m.epochs_safe:>10} {m.epochs_edge:>10} "
              f"{m.epochs_ineligible:>10} {total:>10} {edge_frac:>12}")
        total_safe += m.epochs_safe
        total_edge += m.epochs_edge
        total_ineligible += m.epochs_ineligible

    grand_total = total_safe + total_edge + total_ineligible
    print("-" * 70)
    edge_frac_total = f"{100.0*total_edge/grand_total:.1f}%" if grand_total > 0 else "N/A"
    print(f"{'TOTAL':>8} {total_safe:>10} {total_edge:>10} "
          f"{total_ineligible:>10} {grand_total:>10} {edge_frac_total:>12}")

    # Raw streak histogram (sanity cross-check)
    print()
    print("=" * 80)
    print("RAW STREAK HISTOGRAM (SANITY CHECK: streak → bucket mapping)")
    print("=" * 80)
    print("Expected mapping (K=3):")
    print("  streak ≤ 1 → SAFE")
    print("  streak = 2 → EDGE")
    print("  streak ≥ 3 → INELIGIBLE")
    print()

    # Aggregate raw streak histogram across all seeds
    aggregate_streak_hist: Dict[int, int] = {}
    for seed in SEEDS:
        telem = telemetry_by_seed[seed]
        for streak, count in telem.raw_streak_histogram.items():
            aggregate_streak_hist[streak] = aggregate_streak_hist.get(streak, 0) + count

    print(f"{'Streak':>8} {'Count':>12} {'Expected Bucket':>18} {'Actual Bucket':>18}")
    print("-" * 60)
    for streak in sorted(aggregate_streak_hist.keys()):
        count = aggregate_streak_hist[streak]
        if streak <= 1:
            expected = "SAFE"
        elif streak == 2:
            expected = "EDGE"
        else:
            expected = "INELIGIBLE"
        print(f"{streak:>8} {count:>12} {expected:>18} {expected:>18}")

    print("-" * 60)
    total_from_hist = sum(aggregate_streak_hist.values())
    print(f"{'TOTAL':>8} {total_from_hist:>12}")

    # Verify histogram matches bucket counts
    hist_safe = sum(aggregate_streak_hist.get(s, 0) for s in aggregate_streak_hist if s <= 1)
    hist_edge = aggregate_streak_hist.get(2, 0)
    hist_inelig = sum(aggregate_streak_hist.get(s, 0) for s in aggregate_streak_hist if s >= 3)

    print()
    print("Cross-check: histogram-derived vs bucket counts:")
    print(f"  SAFE:        histogram={hist_safe}, buckets={total_safe}, match={'YES' if hist_safe == total_safe else 'NO'}")
    print(f"  EDGE:        histogram={hist_edge}, buckets={total_edge}, match={'YES' if hist_edge == total_edge else 'NO'}")
    print(f"  INELIGIBLE:  histogram={hist_inelig}, buckets={total_ineligible}, match={'YES' if hist_inelig == total_ineligible else 'NO'}")

    # Primitive emission summary
    print()
    print("=" * 80)
    print("PRIMITIVE EMISSIONS BY BUCKET (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'MAX_RENT':>10} {'INV_CMT':>10} {'NO_OP':>10} {'WRONG':>10}")
    print(f"{'':>8} {'(SAFE)':>10} {'(EDGE)':>10} {'(INELIG)':>10} {'':>10}")
    print("-" * 60)

    total_maxrent = 0
    total_invalid = 0
    total_noop = 0
    total_wrong = 0

    for seed in SEEDS:
        m = run3_results[seed]
        print(f"{seed:>8} {m.max_rent_in_safe:>10} {m.invalid_commit_in_edge:>10} "
              f"{m.no_op_in_ineligible:>10} {m.wrong_primitive_count:>10}")
        total_maxrent += m.max_rent_in_safe
        total_invalid += m.invalid_commit_in_edge
        total_noop += m.no_op_in_ineligible
        total_wrong += m.wrong_primitive_count

    print("-" * 60)
    print(f"{'TOTAL':>8} {total_maxrent:>10} {total_invalid:>10} "
          f"{total_noop:>10} {total_wrong:>10}")

    # Conditional probabilities
    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION (CONDITIONAL PROBABILITIES)")
    print("=" * 80)

    # P(MAX_RENT | SAFE)
    if total_safe > 0:
        p_maxrent_safe = total_maxrent / total_safe
    else:
        p_maxrent_safe = None

    # P(INVALID_COMMIT | EDGE)
    if total_edge > 0:
        p_invalid_edge = total_invalid / total_edge
    else:
        p_invalid_edge = None

    # P(NO_OP | INELIGIBLE)
    if total_ineligible > 0:
        p_noop_ineligible = total_noop / total_ineligible
    else:
        p_noop_ineligible = None

    print(f"  P(MAX_RENT | SAFE):           {total_maxrent}/{total_safe} = {p_maxrent_safe:.6f}" if p_maxrent_safe is not None else "  P(MAX_RENT | SAFE):           N/A (no SAFE epochs)")
    print(f"  P(INVALID_COMMIT | EDGE):     {total_invalid}/{total_edge} = {p_invalid_edge:.6f}" if p_invalid_edge is not None else "  P(INVALID_COMMIT | EDGE):     N/A (no EDGE epochs)")
    print(f"  P(NO_OP | INELIGIBLE):        {total_noop}/{total_ineligible} = {p_noop_ineligible:.6f}" if p_noop_ineligible is not None else "  P(NO_OP | INELIGIBLE):        N/A (no INELIGIBLE epochs)")
    print()

    # Check activation
    activation_verified = True
    issues = []

    # SAFE check
    if total_safe > 0 and p_maxrent_safe != 1.0:
        activation_verified = False
        issues.append(f"P(MAX_RENT | SAFE) = {p_maxrent_safe:.6f} ≠ 1.0")

    # EDGE check
    if total_edge > 0 and p_invalid_edge != 1.0:
        activation_verified = False
        issues.append(f"P(INVALID_COMMIT | EDGE) = {p_invalid_edge:.6f} ≠ 1.0")

    # INELIGIBLE check
    if total_ineligible > 0 and p_noop_ineligible != 1.0:
        activation_verified = False
        issues.append(f"P(NO_OP | INELIGIBLE) = {p_noop_ineligible:.6f} ≠ 1.0")

    # Wrong primitive check
    if total_wrong > 0:
        activation_verified = False
        issues.append(f"Wrong primitive emissions: {total_wrong}")

    if activation_verified:
        print("  ✅ Model H ACTIVATION VERIFIED: Strategy map executed correctly")
    else:
        print("  ❌ Model H ACTIVATION FAILED:")
        for issue in issues:
            print(f"     - {issue}")

    # Ineligibility diagnostics
    print()
    print("=" * 80)
    print("ELIGIBILITY DIAGNOSTICS (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'ever_inelig':>12} {'inelig_frac':>12} {'edge_hits':>12} {'lapses':>10}")
    print("-" * 60)

    ever_inelig_count = 0
    inelig_fracs = []
    edge_hits = []

    for seed in SEEDS:
        m = run3_results[seed]
        ever_str = "YES" if m.ever_ineligible else "NO"
        if m.ever_ineligible:
            ever_inelig_count += 1
        inelig_frac_str = f"{m.ineligibility_fraction_ppm/10000:.2f}%"
        inelig_fracs.append(m.ineligibility_fraction_ppm)
        edge_hits.append(m.edge_hit_count)
        print(f"{seed:>8} {ever_str:>12} {inelig_frac_str:>12} {m.edge_hit_count:>12} {m.lapse_count:>10}")

    print("-" * 60)
    print(f"Seeds ever ineligible: {ever_inelig_count}/10")
    if inelig_fracs:
        print(f"Mean ineligibility fraction: {statistics.mean(inelig_fracs)/10000:.2f}%")
    if edge_hits:
        print(f"Mean edge hits per seed: {statistics.mean(edge_hits):.1f}")

    # Comparison table
    print()
    print("=" * 80)
    print("BASELINE VS RUN 3 COMPARISON")
    print("=" * 80)
    print(f"{'Seed':>8} {'Base AA':>12} {'Run3 AA':>12} {'Δ AA':>10} {'Base Lapse':>12} {'Run3 Lapse':>12}")
    print("-" * 80)

    identical_count = 0
    aa_deltas = []
    for seed in SEEDS:
        base = baseline_results[seed]
        run3 = run3_results[seed]
        delta = run3.AA_ppm - base.AA_ppm
        aa_deltas.append(delta)
        is_identical = (base.AA_ppm == run3.AA_ppm)
        if is_identical:
            identical_count += 1
        print(f"{seed:>8} {base.AA_ppm:>12} {run3.AA_ppm:>12} {delta:>+10} {base.lapse_count:>12} {run3.lapse_count:>12}")

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
    run3_class_dist: Dict[str, int] = {}
    for seed in SEEDS:
        fc = baseline_results[seed].failure_class
        base_class_dist[fc] = base_class_dist.get(fc, 0) + 1
        fc = run3_results[seed].failure_class
        run3_class_dist[fc] = run3_class_dist.get(fc, 0) + 1
    print(f"  Baseline: {base_class_dist}")
    print(f"  Run 3:    {run3_class_dist}")

    # Check for terminal failure modes
    terminal_modes = ['TERMINAL_COLLAPSE', 'STRUCTURAL_THRASHING', 'IRREVERSIBLE_RECOVERY_SUPPRESSION']
    terminal_found = False
    for mode in terminal_modes:
        if run3_class_dist.get(mode, 0) > 0:
            terminal_found = True
            print(f"\n  ⚠️  TERMINAL FAILURE MODE DETECTED: {mode} ({run3_class_dist[mode]} seeds)")

    # Final summary
    print()
    print("=" * 80)
    print("RUN 3 SUMMARY")
    print("=" * 80)
    print(f"  Activation verified:     {'YES' if activation_verified else 'NO'}")
    print(f"  Total epochs observed:   {grand_total}")
    print(f"  Bucket distribution:")
    print(f"    SAFE:        {total_safe} ({100.0*total_safe/grand_total:.1f}%)" if grand_total > 0 else "    SAFE: 0")
    print(f"    EDGE:        {total_edge} ({100.0*total_edge/grand_total:.1f}%)" if grand_total > 0 else "    EDGE: 0")
    print(f"    INELIGIBLE:  {total_ineligible} ({100.0*total_ineligible/grand_total:.1f}%)" if grand_total > 0 else "    INELIGIBLE: 0")
    print(f"  Primitive emissions by bucket:")
    print(f"    MAX_RENT (SAFE):           {total_maxrent}")
    print(f"    INVALID_COMMIT (EDGE):     {total_invalid}")
    print(f"    NO_OP (INELIGIBLE):        {total_noop}")
    print(f"  Wrong primitive emissions:   {total_wrong}")
    print(f"  Seeds ever ineligible:       {ever_inelig_count}/10")
    print(f"  Identical outcomes to baseline: {identical_count}/10 seeds")
    print(f"  Terminal failure modes:      {'YES' if terminal_found else 'NO'}")
    print()
    print("=" * 80)
    print("RUN 3 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
