#!/usr/bin/env python3
"""
RSA v2.0 Run 2: CTA Phase-Aware Adversary (CTA_PHASE_AWARE)

Model G: Strategy selection based on forward-looking CTA phase.

Per binding decision 2026-01-08:
CTA is a FORWARD-LOOKING CONSTITUTIONAL CLOCK observable during authority.
The phase represents "projected amnesty phase if lapse were to begin now".

Strategy Map (Model G):
| CTA Phase    | Action Primitive    |
|--------------|---------------------|
| INACTIVE     | ACTION_MAX_RENT     |  (CTA disabled - never seen with cta_enabled=True)
| EARLY        | ACTION_INVALID_COMMIT |
| MID          | ACTION_MIN_EFFORT   |
| LATE         | ACTION_COMPLIANT    |

Telemetry Requirements for Activation Proof:
- P(MAX_RENT | cta_phase = INACTIVE) = 1.0  (or N/A if never observed)
- P(INVALID_COMMIT | cta_phase = EARLY) = 1.0
- P(MIN_EFFORT | cta_phase = MID) = 1.0
- P(COMPLIANT | cta_phase = LATE) = 1.0

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
    RSAPolicyConfig, RSAPolicyModel, AdaptiveRSAWrapper, CTABucket
)

# Frozen protocol fingerprint
SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000
TAIL_WINDOW = 5000

# Protocol hashes from v2.0 implementation report
ALSCONFIG_PARAMETER_HASH = "fd58b6e5"
RSA_V2_CONFIG_HASH = "4e20b327"
OBSERVABLE_INTERFACE_HASH = "9afe2362"
HARNESS_PATCH = "v0.8.1-lapse-tracking"

# Model G strategy map hash
# Strategy: INACTIVE→MAX_RENT, EARLY→INVALID_COMMIT, MID→MIN_EFFORT, LATE→COMPLIANT
MODEL_G_STRATEGY_MAP_HASH = "model_g_cta_phase_aware"


@dataclass
class CTAPhaseTelemetry:
    """Tracks per-CTA-phase observations and primitive emissions."""
    # Phase observation counts
    epochs_inactive: int = 0
    epochs_early: int = 0
    epochs_mid: int = 0
    epochs_late: int = 0

    # Primitive emission counts (per phase)
    max_rent_in_inactive: int = 0
    invalid_commit_in_early: int = 0
    min_effort_in_mid: int = 0
    compliant_in_late: int = 0

    # Cross-validation: wrong primitives (should all be 0)
    wrong_primitive_count: int = 0

    _seen_epochs: set = field(default_factory=set)


def make_cta_telemetry_wrapper(telemetry: CTAPhaseTelemetry):
    """Create a telemetry-capturing intercept wrapper for CTA phase tracking."""
    original_intercept = AdaptiveRSAWrapper.intercept

    def traced_intercept(self, observable, epoch, cycle_in_epoch, original_action):
        result = original_intercept(self, observable, epoch, cycle_in_epoch, original_action)

        # Only count once per epoch (first cycle)
        if epoch not in telemetry._seen_epochs:
            telemetry._seen_epochs.add(epoch)

            phase = observable.cta_phase
            primitive = result.get('rsa_primitive', 'NONE')

            # Track phase observations
            if phase == CTABucket.INACTIVE:
                telemetry.epochs_inactive += 1
                if primitive == 'MAX_RENT':
                    telemetry.max_rent_in_inactive += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif phase == CTABucket.EARLY:
                telemetry.epochs_early += 1
                if primitive == 'INVALID_COMMIT':
                    telemetry.invalid_commit_in_early += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif phase == CTABucket.MID:
                telemetry.epochs_mid += 1
                if primitive == 'MIN_EFFORT':
                    telemetry.min_effort_in_mid += 1
                else:
                    telemetry.wrong_primitive_count += 1
            elif phase == CTABucket.LATE:
                telemetry.epochs_late += 1
                if primitive == 'COMPLIANT':
                    telemetry.compliant_in_late += 1
                else:
                    telemetry.wrong_primitive_count += 1

        return result

    return traced_intercept


@dataclass
class Run2Metrics:
    """Metrics extracted for Run 2 analysis with CTA phase telemetry."""
    seed: int
    AA_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    renewals_succeeded: int
    renewal_attempts: int
    renewal_success_rate_ppm: int
    # CTA phase telemetry
    epochs_inactive: int
    epochs_early: int
    epochs_mid: int
    epochs_late: int
    max_rent_in_inactive: int
    invalid_commit_in_early: int
    min_effort_in_mid: int
    compliant_in_late: int
    wrong_primitive_count: int


def run_with_cta_telemetry(seed: int, config: ALSConfigV080, policy_config: RSAPolicyConfig) -> Tuple[Run2Metrics, CTAPhaseTelemetry]:
    """Run with CTA_PHASE_AWARE policy and telemetry collection."""
    telemetry = CTAPhaseTelemetry()

    # Patch intercept for this run
    original_intercept = AdaptiveRSAWrapper.intercept
    AdaptiveRSAWrapper.intercept = make_cta_telemetry_wrapper(telemetry)

    try:
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()

        lapse_count = result.semantic_lapse_count + result.structural_lapse_count
        AA_ppm = int(result.authority_uptime_fraction * 1_000_000)

        if result.renewal_attempts > 0:
            renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
        else:
            renewal_success_rate_ppm = 0

        metrics = Run2Metrics(
            seed=seed,
            AA_ppm=AA_ppm,
            failure_class=result.stop_reason.name if result.stop_reason else "NONE",
            lapse_count=lapse_count,
            total_lapse_epochs=result.total_lapse_duration_epochs,
            renewals_succeeded=result.renewal_successes,
            renewal_attempts=result.renewal_attempts,
            renewal_success_rate_ppm=renewal_success_rate_ppm,
            epochs_inactive=telemetry.epochs_inactive,
            epochs_early=telemetry.epochs_early,
            epochs_mid=telemetry.epochs_mid,
            epochs_late=telemetry.epochs_late,
            max_rent_in_inactive=telemetry.max_rent_in_inactive,
            invalid_commit_in_early=telemetry.invalid_commit_in_early,
            min_effort_in_mid=telemetry.min_effort_in_mid,
            compliant_in_late=telemetry.compliant_in_late,
            wrong_primitive_count=telemetry.wrong_primitive_count,
        )

        return metrics, telemetry
    finally:
        # Restore original intercept
        AdaptiveRSAWrapper.intercept = original_intercept


def run_baseline(seed: int, config: ALSConfigV080) -> Run2Metrics:
    """Run baseline (no RSA) for comparison."""
    harness = ALSHarnessV080(seed=seed, config=config)
    result = harness.run()

    lapse_count = result.semantic_lapse_count + result.structural_lapse_count
    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)

    if result.renewal_attempts > 0:
        renewal_success_rate_ppm = int((result.renewal_successes / result.renewal_attempts) * 1_000_000)
    else:
        renewal_success_rate_ppm = 0

    return Run2Metrics(
        seed=seed,
        AA_ppm=AA_ppm,
        failure_class=result.stop_reason.name if result.stop_reason else "NONE",
        lapse_count=lapse_count,
        total_lapse_epochs=result.total_lapse_duration_epochs,
        renewals_succeeded=result.renewal_successes,
        renewal_attempts=result.renewal_attempts,
        renewal_success_rate_ppm=renewal_success_rate_ppm,
        # No telemetry for baseline
        epochs_inactive=0,
        epochs_early=0,
        epochs_mid=0,
        epochs_late=0,
        max_rent_in_inactive=0,
        invalid_commit_in_early=0,
        min_effort_in_mid=0,
        compliant_in_late=0,
        wrong_primitive_count=0,
    )


def main():
    print("=" * 80)
    print("RSA v2.0 RUN 2: CTA_PHASE_AWARE (Model G)")
    print("=" * 80)

    # Protocol fingerprint
    print("\n--- Protocol Fingerprint ---")
    print(f"ALSConfig Parameter Hash:    {ALSCONFIG_PARAMETER_HASH}")
    print(f"RSA v2.0 Config Hash:        {RSA_V2_CONFIG_HASH}")
    print(f"Observable Interface Hash:   {OBSERVABLE_INTERFACE_HASH}")
    print(f"Harness Patch:               {HARNESS_PATCH}")
    print(f"Seeds:                       {SEEDS}")
    print(f"Horizon:                     {MAX_CYCLES} cycles = {HORIZON_EPOCHS} epochs")
    print()
    print("--- Model G Strategy Map ---")
    print("  CTA_INACTIVE → MAX_RENT")
    print("  CTA_EARLY    → INVALID_COMMIT")
    print("  CTA_MID      → MIN_EFFORT")
    print("  CTA_LATE     → COMPLIANT")
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

    # RSA v2.0 config for Model G
    policy_config = RSAPolicyConfig(
        policy_model=RSAPolicyModel.CTA_PHASE_AWARE,
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
    baseline_results: Dict[int, Run2Metrics] = {}
    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics = run_baseline(seed, config)
        baseline_results[seed] = metrics
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}")

    # Run CTA_PHASE_AWARE for each seed with telemetry
    print()
    print("=" * 80)
    print("PHASE 2: MODEL G (CTA_PHASE_AWARE) WITH TELEMETRY")
    print("=" * 80)
    run2_results: Dict[int, Run2Metrics] = {}
    telemetry_by_seed: Dict[int, CTAPhaseTelemetry] = {}

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, telem = run_with_cta_telemetry(seed, config, policy_config)
        run2_results[seed] = metrics
        telemetry_by_seed[seed] = telem
        total_phases = metrics.epochs_inactive + metrics.epochs_early + metrics.epochs_mid + metrics.epochs_late
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"phases=[I:{metrics.epochs_inactive},E:{metrics.epochs_early},"
              f"M:{metrics.epochs_mid},L:{metrics.epochs_late}]")

    # Phase distribution summary
    print()
    print("=" * 80)
    print("CTA PHASE DISTRIBUTION (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'INACTIVE':>10} {'EARLY':>10} {'MID':>10} {'LATE':>10} {'TOTAL':>10}")
    print("-" * 70)

    total_inactive = 0
    total_early = 0
    total_mid = 0
    total_late = 0

    for seed in SEEDS:
        m = run2_results[seed]
        total = m.epochs_inactive + m.epochs_early + m.epochs_mid + m.epochs_late
        print(f"{seed:>8} {m.epochs_inactive:>10} {m.epochs_early:>10} "
              f"{m.epochs_mid:>10} {m.epochs_late:>10} {total:>10}")
        total_inactive += m.epochs_inactive
        total_early += m.epochs_early
        total_mid += m.epochs_mid
        total_late += m.epochs_late

    grand_total = total_inactive + total_early + total_mid + total_late
    print("-" * 70)
    print(f"{'TOTAL':>8} {total_inactive:>10} {total_early:>10} "
          f"{total_mid:>10} {total_late:>10} {grand_total:>10}")

    # Primitive emission summary
    print()
    print("=" * 80)
    print("PRIMITIVE EMISSIONS BY PHASE (PER SEED)")
    print("=" * 80)
    print(f"{'Seed':>8} {'MAX_RENT':>10} {'INV_CMT':>10} {'MIN_EFF':>10} {'COMPLIANT':>10} {'WRONG':>10}")
    print(f"{'':>8} {'(INACT)':>10} {'(EARLY)':>10} {'(MID)':>10} {'(LATE)':>10} {'':>10}")
    print("-" * 70)

    total_maxrent = 0
    total_invalid = 0
    total_mineff = 0
    total_compliant = 0
    total_wrong = 0

    for seed in SEEDS:
        m = run2_results[seed]
        print(f"{seed:>8} {m.max_rent_in_inactive:>10} {m.invalid_commit_in_early:>10} "
              f"{m.min_effort_in_mid:>10} {m.compliant_in_late:>10} {m.wrong_primitive_count:>10}")
        total_maxrent += m.max_rent_in_inactive
        total_invalid += m.invalid_commit_in_early
        total_mineff += m.min_effort_in_mid
        total_compliant += m.compliant_in_late
        total_wrong += m.wrong_primitive_count

    print("-" * 70)
    print(f"{'TOTAL':>8} {total_maxrent:>10} {total_invalid:>10} "
          f"{total_mineff:>10} {total_compliant:>10} {total_wrong:>10}")

    # Conditional probabilities
    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION (CONDITIONAL PROBABILITIES)")
    print("=" * 80)

    # P(MAX_RENT | INACTIVE) - may be N/A if INACTIVE never observed
    if total_inactive > 0:
        p_maxrent_inactive = total_maxrent / total_inactive
        p_maxrent_str = f"{total_maxrent}/{total_inactive} = {p_maxrent_inactive:.6f}"
    else:
        p_maxrent_inactive = None
        p_maxrent_str = "N/A (INACTIVE never observed - expected with cta_enabled=True)"

    # P(INVALID_COMMIT | EARLY)
    if total_early > 0:
        p_invalid_early = total_invalid / total_early
    else:
        p_invalid_early = None

    # P(MIN_EFFORT | MID)
    if total_mid > 0:
        p_mineff_mid = total_mineff / total_mid
    else:
        p_mineff_mid = None

    # P(COMPLIANT | LATE)
    if total_late > 0:
        p_compliant_late = total_compliant / total_late
    else:
        p_compliant_late = None

    print(f"  P(MAX_RENT | INACTIVE):       {p_maxrent_str}")
    print(f"  P(INVALID_COMMIT | EARLY):    {total_invalid}/{total_early} = {p_invalid_early:.6f}" if p_invalid_early is not None else "  P(INVALID_COMMIT | EARLY):    N/A (no EARLY epochs)")
    print(f"  P(MIN_EFFORT | MID):          {total_mineff}/{total_mid} = {p_mineff_mid:.6f}" if p_mineff_mid is not None else "  P(MIN_EFFORT | MID):          N/A (no MID epochs)")
    print(f"  P(COMPLIANT | LATE):          {total_compliant}/{total_late} = {p_compliant_late:.6f}" if p_compliant_late is not None else "  P(COMPLIANT | LATE):          N/A (no LATE epochs)")
    print()

    # Check activation
    activation_verified = True
    issues = []

    # INACTIVE check (N/A is acceptable since cta_enabled=True means INACTIVE never observed)
    if total_inactive > 0 and p_maxrent_inactive != 1.0:
        activation_verified = False
        issues.append(f"P(MAX_RENT | INACTIVE) = {p_maxrent_inactive:.6f} ≠ 1.0")

    # EARLY check
    if total_early > 0 and p_invalid_early != 1.0:
        activation_verified = False
        issues.append(f"P(INVALID_COMMIT | EARLY) = {p_invalid_early:.6f} ≠ 1.0")

    # MID check
    if total_mid > 0 and p_mineff_mid != 1.0:
        activation_verified = False
        issues.append(f"P(MIN_EFFORT | MID) = {p_mineff_mid:.6f} ≠ 1.0")

    # LATE check
    if total_late > 0 and p_compliant_late != 1.0:
        activation_verified = False
        issues.append(f"P(COMPLIANT | LATE) = {p_compliant_late:.6f} ≠ 1.0")

    # Wrong primitive check
    if total_wrong > 0:
        activation_verified = False
        issues.append(f"Wrong primitive emissions: {total_wrong}")

    if activation_verified:
        print("  ✅ Model G ACTIVATION VERIFIED: Strategy map executed correctly")
    else:
        print("  ❌ Model G ACTIVATION FAILED:")
        for issue in issues:
            print(f"     - {issue}")

    # Comparison table
    print()
    print("=" * 80)
    print("BASELINE VS RUN 2 COMPARISON")
    print("=" * 80)
    print(f"{'Seed':>8} {'Base AA':>12} {'Run2 AA':>12} {'Δ AA':>10} {'Base Lapse':>12} {'Run2 Lapse':>12}")
    print("-" * 80)

    identical_count = 0
    aa_deltas = []
    for seed in SEEDS:
        base = baseline_results[seed]
        run2 = run2_results[seed]
        delta = run2.AA_ppm - base.AA_ppm
        aa_deltas.append(delta)
        is_identical = (base.AA_ppm == run2.AA_ppm)
        if is_identical:
            identical_count += 1
        print(f"{seed:>8} {base.AA_ppm:>12} {run2.AA_ppm:>12} {delta:>+10} {base.lapse_count:>12} {run2.lapse_count:>12}")

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
    run2_class_dist: Dict[str, int] = {}
    for seed in SEEDS:
        fc = baseline_results[seed].failure_class
        base_class_dist[fc] = base_class_dist.get(fc, 0) + 1
        fc = run2_results[seed].failure_class
        run2_class_dist[fc] = run2_class_dist.get(fc, 0) + 1
    print(f"  Baseline: {base_class_dist}")
    print(f"  Run 2:    {run2_class_dist}")

    # Final summary
    print()
    print("=" * 80)
    print("RUN 2 SUMMARY")
    print("=" * 80)
    print(f"  Activation verified:     {'YES' if activation_verified else 'NO'}")
    print(f"  Total epochs observed:   {grand_total}")
    print(f"  Phase distribution:")
    print(f"    INACTIVE: {total_inactive} ({100.0*total_inactive/grand_total:.1f}%)" if grand_total > 0 else "    INACTIVE: 0")
    print(f"    EARLY:    {total_early} ({100.0*total_early/grand_total:.1f}%)" if grand_total > 0 else "    EARLY: 0")
    print(f"    MID:      {total_mid} ({100.0*total_mid/grand_total:.1f}%)" if grand_total > 0 else "    MID: 0")
    print(f"    LATE:     {total_late} ({100.0*total_late/grand_total:.1f}%)" if grand_total > 0 else "    LATE: 0")
    print(f"  Primitive emissions by phase:")
    print(f"    MAX_RENT (INACTIVE):       {total_maxrent}")
    print(f"    INVALID_COMMIT (EARLY):    {total_invalid}")
    print(f"    MIN_EFFORT (MID):          {total_mineff}")
    print(f"    COMPLIANT (LATE):          {total_compliant}")
    print(f"  Wrong primitive emissions:   {total_wrong}")
    print(f"  Identical outcomes to baseline: {identical_count}/10 seeds")
    print()
    print("=" * 80)
    print("RUN 2 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
