#!/usr/bin/env python3
"""
RSA v3.0 Run 1b: Resonant Lapse Trigger (N = 2 × renewal_interval)

Model J: Counter-based adversary that emits INVALID_COMMIT at regular intervals.
- State: counter modulo N (N=100 for Run 1b)
- state ≡ 0 (mod N) → ACTION_INVALID_COMMIT
- otherwise → ACTION_COMPLIANT

Collects telemetry to prove:
1. Model activation via primitive emission counts
2. Exercised state verification (dynamic check: |{S_t}| ≥ 2)
3. State transition counts
"""
import sys
sys.path.insert(0, "src")

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import statistics

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import (
    RSAPolicyConfig, RSAPolicyModel, StatefulRSAWrapper,
    ResonantLapseAdversary
)

# Frozen protocol fingerprint
SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000

# Model J Run 1b parameters
RESONANT_PERIOD_N = 2 * RENEWAL_CHECK_INTERVAL  # N = 100


@dataclass
class TelemetryAccumulator:
    """Accumulates telemetry during a single run."""
    epochs_state_0: int = 0
    epochs_state_other: int = 0
    invalid_commit_epochs: int = 0
    compliant_epochs: int = 0
    state_transitions: int = 0
    observed_states: set = field(default_factory=set)
    last_state: int = -1
    _seen_epochs: set = field(default_factory=set)


def make_telemetry_wrapper(accumulator: TelemetryAccumulator):
    """Create a telemetry-capturing intercept wrapper."""
    original_intercept = StatefulRSAWrapper.intercept

    def traced_intercept(self, observable, epoch, cycle_in_epoch, original_action):
        result = original_intercept(self, observable, epoch, cycle_in_epoch, original_action)

        if epoch not in accumulator._seen_epochs:
            accumulator._seen_epochs.add(epoch)

            state_before = result.get('rsa_state_before', 0)
            state_after = result.get('rsa_state_after', 0)

            accumulator.observed_states.add(state_before)
            accumulator.observed_states.add(state_after)

            if state_before == 0:
                accumulator.epochs_state_0 += 1
            else:
                accumulator.epochs_state_other += 1

            if accumulator.last_state >= 0 and state_before != accumulator.last_state:
                accumulator.state_transitions += 1
            accumulator.last_state = state_after

            primitive = result.get('rsa_primitive', 'NONE')
            if primitive == 'INVALID_COMMIT':
                accumulator.invalid_commit_epochs += 1
            elif primitive == 'COMPLIANT':
                accumulator.compliant_epochs += 1

        return result

    return traced_intercept


@dataclass
class Run1bMetrics:
    """Metrics extracted for Run 1b analysis with telemetry."""
    seed: int
    AA_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    renewals_succeeded: int
    renewal_attempts: int
    epochs_state_0: int
    epochs_state_other: int
    invalid_commit_epochs: int
    compliant_epochs: int
    state_transitions: int
    observed_state_count: int
    exercised_state_dynamic_ok: bool


def run_with_telemetry(seed: int, config: ALSConfigV080, policy_config: RSAPolicyConfig) -> Tuple[Run1bMetrics, TelemetryAccumulator]:
    """Run with RSA v3.0 and telemetry collection."""
    accumulator = TelemetryAccumulator()

    original_intercept = StatefulRSAWrapper.intercept
    StatefulRSAWrapper.intercept = make_telemetry_wrapper(accumulator)

    try:
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()
    finally:
        StatefulRSAWrapper.intercept = original_intercept

    epochs_evaluated = result.total_cycles // config.renewal_check_interval
    lapse_count = result.semantic_lapse_count + result.structural_lapse_count
    total_lapse_epochs = result.total_lapse_duration_epochs
    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)
    failure_class = result.stop_reason.name if result.stop_reason else "NONE"

    metrics = Run1bMetrics(
        seed=seed,
        AA_ppm=AA_ppm,
        failure_class=failure_class,
        lapse_count=lapse_count,
        total_lapse_epochs=total_lapse_epochs,
        renewals_succeeded=result.renewal_successes,
        renewal_attempts=result.renewal_attempts,
        epochs_state_0=accumulator.epochs_state_0,
        epochs_state_other=accumulator.epochs_state_other,
        invalid_commit_epochs=accumulator.invalid_commit_epochs,
        compliant_epochs=accumulator.compliant_epochs,
        state_transitions=accumulator.state_transitions,
        observed_state_count=len(accumulator.observed_states),
        exercised_state_dynamic_ok=len(accumulator.observed_states) >= 2,
    )

    return metrics, accumulator


def compute_activation_probabilities(all_metrics: List[Run1bMetrics]) -> Dict[str, float]:
    """Compute conditional activation probabilities."""
    total_state_0 = sum(m.epochs_state_0 for m in all_metrics)
    total_state_other = sum(m.epochs_state_other for m in all_metrics)
    total_invalid = sum(m.invalid_commit_epochs for m in all_metrics)
    total_compliant = sum(m.compliant_epochs for m in all_metrics)

    p_invalid_given_state_0 = total_invalid / max(1, total_state_0)
    p_compliant_given_state_other = total_compliant / max(1, total_state_other)

    return {
        "total_state_0_epochs": total_state_0,
        "total_state_other_epochs": total_state_other,
        "total_invalid_commit": total_invalid,
        "total_compliant": total_compliant,
        "P_invalid_given_state_0": p_invalid_given_state_0,
        "P_compliant_given_state_other": p_compliant_given_state_other,
    }


def main():
    print("=" * 80)
    print("RSA v3.0 Run 1b: RESONANT_LAPSE (N=100)")
    print("=" * 80)
    print()

    # Run acceptance gate first
    print("Running v3.0 acceptance gate...")
    from toy_aki.rsa.test_acceptance_v3 import run_acceptance_gate
    if not run_acceptance_gate():
        print("\n❌ ACCEPTANCE GATE FAILED - ABORTING RUN")
        return 1

    print("\n✅ Acceptance gate passed, proceeding with runs\n")

    config_j = RSAPolicyConfig(
        policy_model=RSAPolicyModel.RESONANT_LAPSE,
        rsa_version="v3",
        rsa_resonant_period_N=RESONANT_PERIOD_N,
        rsa_max_internal_states=RESONANT_PERIOD_N,
        epoch_size=RENEWAL_CHECK_INTERVAL,
    )

    if not ResonantLapseAdversary.verify_exercised_state_static(config_j):
        print("❌ Static exercised-state check FAILED for Model J")
        return 1

    print(f"✅ Static exercised-state check passed (N={RESONANT_PERIOD_N})")
    print()

    als_config = ALSConfigV080(max_cycles=MAX_CYCLES)
    all_metrics: List[Run1bMetrics] = []

    print("=" * 80)
    print("EXECUTING RUNS")
    print("=" * 80)

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, _ = run_with_telemetry(seed, als_config, config_j)
        all_metrics.append(metrics)
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"states_observed={metrics.observed_state_count}")

    probs = compute_activation_probabilities(all_metrics)

    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION")
    print("=" * 80)
    print(f"Total state=0 epochs: {probs['total_state_0_epochs']}")
    print(f"Total state≠0 epochs: {probs['total_state_other_epochs']}")
    print(f"P(INVALID_COMMIT | state=0): {probs['P_invalid_given_state_0']:.6f}")
    print(f"P(COMPLIANT | state≠0): {probs['P_compliant_given_state_other']:.6f}")

    activation_ok = (
        probs['P_invalid_given_state_0'] > 0.99 and
        probs['P_compliant_given_state_other'] > 0.99
    )

    if activation_ok:
        print("\n✅ Model J (RESONANT_LAPSE) activation VERIFIED")
    else:
        print("\n❌ Model J activation FAILED")

    print()
    print("=" * 80)
    print("EXERCISED STATE VERIFICATION (DYNAMIC)")
    print("=" * 80)
    all_exercised = all(m.exercised_state_dynamic_ok for m in all_metrics)
    for m in all_metrics:
        status = "✓" if m.exercised_state_dynamic_ok else "✗"
        print(f"  Seed {m.seed}: {status} observed {m.observed_state_count} distinct states")

    if all_exercised:
        print("\n✅ All runs pass exercised-state dynamic check")
    else:
        print("\n❌ Some runs FAILED exercised-state dynamic check")

    print()
    print("=" * 80)
    print("RUN 1b SUMMARY")
    print("=" * 80)

    mean_aa = statistics.mean(m.AA_ppm for m in all_metrics)
    mean_lapses = statistics.mean(m.lapse_count for m in all_metrics)
    terminal_failures = sum(1 for m in all_metrics if m.failure_class != "HORIZON_EXHAUSTED")

    print(f"Mean AA: {mean_aa:.0f} PPM")
    print(f"Mean lapses: {mean_lapses:.2f}")
    print(f"Terminal failures: {terminal_failures}")
    print(f"Activation verified: {activation_ok}")
    print(f"All exercised-state checks pass: {all_exercised}")

    if activation_ok and all_exercised and terminal_failures == 0:
        print("\n✅ RUN 1b COMPLETE - Model J (N=100) produces no terminal failures")
        return 0
    else:
        print("\n❌ RUN 1b ISSUES DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
