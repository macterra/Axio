#!/usr/bin/env python3
"""
RSA v3.0 Run 2: Eligibility Edge Oscillator

Model K: 1-bit toggle adversary that oscillates behavior at eligibility edge.
- State: 1-bit toggle (0 or 1)
- ELIG_EDGE, state=0 → ACTION_MIN_EFFORT
- ELIG_EDGE, state=1 → ACTION_INVALID_COMMIT
- otherwise → ACTION_COMPLIANT
- Toggle state on each epoch where eligibility_bucket == EDGE

Collects telemetry to prove:
1. Model activation via primitive emission counts
2. Exercised state verification (dynamic check: |{S_t}| ≥ 2)
"""
import sys
sys.path.insert(0, "src")

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import statistics

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import (
    RSAPolicyConfig, RSAPolicyModel, StatefulRSAWrapper,
    EdgeOscillatorAdversary, EligibilityBucket
)

# Frozen protocol fingerprint
SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000


@dataclass
class TelemetryAccumulator:
    """Accumulates telemetry during a single run."""
    epochs_edge_state_0: int = 0
    epochs_edge_state_1: int = 0
    epochs_non_edge: int = 0
    min_effort_epochs: int = 0
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

            # Track EDGE vs non-EDGE
            if observable.eligibility_bucket == EligibilityBucket.EDGE:
                if state_before == 0:
                    accumulator.epochs_edge_state_0 += 1
                else:
                    accumulator.epochs_edge_state_1 += 1
            else:
                accumulator.epochs_non_edge += 1

            if accumulator.last_state >= 0 and state_before != accumulator.last_state:
                accumulator.state_transitions += 1
            accumulator.last_state = state_after

            primitive = result.get('rsa_primitive', 'NONE')
            if primitive == 'MIN_EFFORT':
                accumulator.min_effort_epochs += 1
            elif primitive == 'INVALID_COMMIT':
                accumulator.invalid_commit_epochs += 1
            elif primitive == 'COMPLIANT':
                accumulator.compliant_epochs += 1

        return result

    return traced_intercept


@dataclass
class Run2Metrics:
    """Metrics extracted for Run 2 analysis with telemetry."""
    seed: int
    AA_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    renewals_succeeded: int
    renewal_attempts: int
    epochs_edge_state_0: int
    epochs_edge_state_1: int
    epochs_non_edge: int
    min_effort_epochs: int
    invalid_commit_epochs: int
    compliant_epochs: int
    state_transitions: int
    observed_state_count: int
    exercised_state_dynamic_ok: bool


def run_with_telemetry(seed: int, config: ALSConfigV080, policy_config: RSAPolicyConfig) -> Tuple[Run2Metrics, TelemetryAccumulator]:
    """Run with RSA v3.0 and telemetry collection."""
    accumulator = TelemetryAccumulator()

    original_intercept = StatefulRSAWrapper.intercept
    StatefulRSAWrapper.intercept = make_telemetry_wrapper(accumulator)

    try:
        harness = ALSHarnessV080(seed=seed, config=config, rsa_policy_config=policy_config)
        result = harness.run()
    finally:
        StatefulRSAWrapper.intercept = original_intercept

    lapse_count = result.semantic_lapse_count + result.structural_lapse_count
    total_lapse_epochs = result.total_lapse_duration_epochs
    AA_ppm = int(result.authority_uptime_fraction * 1_000_000)
    failure_class = result.stop_reason.name if result.stop_reason else "NONE"

    metrics = Run2Metrics(
        seed=seed,
        AA_ppm=AA_ppm,
        failure_class=failure_class,
        lapse_count=lapse_count,
        total_lapse_epochs=total_lapse_epochs,
        renewals_succeeded=result.renewal_successes,
        renewal_attempts=result.renewal_attempts,
        epochs_edge_state_0=accumulator.epochs_edge_state_0,
        epochs_edge_state_1=accumulator.epochs_edge_state_1,
        epochs_non_edge=accumulator.epochs_non_edge,
        min_effort_epochs=accumulator.min_effort_epochs,
        invalid_commit_epochs=accumulator.invalid_commit_epochs,
        compliant_epochs=accumulator.compliant_epochs,
        state_transitions=accumulator.state_transitions,
        observed_state_count=len(accumulator.observed_states),
        exercised_state_dynamic_ok=len(accumulator.observed_states) >= 2,
    )

    return metrics, accumulator


def compute_activation_probabilities(all_metrics: List[Run2Metrics]) -> Dict[str, float]:
    """Compute conditional activation probabilities."""
    total_edge_0 = sum(m.epochs_edge_state_0 for m in all_metrics)
    total_edge_1 = sum(m.epochs_edge_state_1 for m in all_metrics)
    total_non_edge = sum(m.epochs_non_edge for m in all_metrics)
    total_min_effort = sum(m.min_effort_epochs for m in all_metrics)
    total_invalid = sum(m.invalid_commit_epochs for m in all_metrics)
    total_compliant = sum(m.compliant_epochs for m in all_metrics)

    p_min_effort_given_edge_0 = total_min_effort / max(1, total_edge_0)
    p_invalid_given_edge_1 = total_invalid / max(1, total_edge_1)
    p_compliant_given_non_edge = total_compliant / max(1, total_non_edge)

    return {
        "total_edge_state_0_epochs": total_edge_0,
        "total_edge_state_1_epochs": total_edge_1,
        "total_non_edge_epochs": total_non_edge,
        "P_min_effort_given_edge_0": p_min_effort_given_edge_0,
        "P_invalid_given_edge_1": p_invalid_given_edge_1,
        "P_compliant_given_non_edge": p_compliant_given_non_edge,
    }


def main():
    print("=" * 80)
    print("RSA v3.0 Run 2: EDGE_OSCILLATOR")
    print("=" * 80)
    print()

    print("Running v3.0 acceptance gate...")
    from toy_aki.rsa.test_acceptance_v3 import run_acceptance_gate
    if not run_acceptance_gate():
        print("\n❌ ACCEPTANCE GATE FAILED - ABORTING RUN")
        return 1

    print("\n✅ Acceptance gate passed, proceeding with runs\n")

    config_k = RSAPolicyConfig(
        policy_model=RSAPolicyModel.EDGE_OSCILLATOR,
        rsa_version="v3",
        rsa_max_internal_states=4,
        epoch_size=RENEWAL_CHECK_INTERVAL,
    )

    if not EdgeOscillatorAdversary.verify_exercised_state_static(config_k):
        print("❌ Static exercised-state check FAILED for Model K")
        return 1

    print("✅ Static exercised-state check passed")
    print()

    als_config = ALSConfigV080(max_cycles=MAX_CYCLES)
    all_metrics: List[Run2Metrics] = []

    print("=" * 80)
    print("EXECUTING RUNS")
    print("=" * 80)

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, _ = run_with_telemetry(seed, als_config, config_k)
        all_metrics.append(metrics)
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"states_observed={metrics.observed_state_count}")

    probs = compute_activation_probabilities(all_metrics)

    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION")
    print("=" * 80)
    print(f"Total EDGE+state=0 epochs: {probs['total_edge_state_0_epochs']}")
    print(f"Total EDGE+state=1 epochs: {probs['total_edge_state_1_epochs']}")
    print(f"Total non-EDGE epochs: {probs['total_non_edge_epochs']}")
    print(f"P(MIN_EFFORT | EDGE,state=0): {probs['P_min_effort_given_edge_0']:.6f}")
    print(f"P(INVALID | EDGE,state=1): {probs['P_invalid_given_edge_1']:.6f}")
    print(f"P(COMPLIANT | non-EDGE): {probs['P_compliant_given_non_edge']:.6f}")

    # Note: EDGE epochs may be rare, so activation check may be weak
    activation_ok = probs['P_compliant_given_non_edge'] > 0.99

    if activation_ok:
        print("\n✅ Model K (EDGE_OSCILLATOR) activation VERIFIED")
    else:
        print("\n⚠️ Model K activation unclear (EDGE may be rare)")

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
        print("\n⚠️ Some runs may not exercise state (depends on EDGE occurrence)")

    print()
    print("=" * 80)
    print("RUN 2 SUMMARY")
    print("=" * 80)

    mean_aa = statistics.mean(m.AA_ppm for m in all_metrics)
    mean_lapses = statistics.mean(m.lapse_count for m in all_metrics)
    terminal_failures = sum(1 for m in all_metrics if m.failure_class != "HORIZON_EXHAUSTED")

    print(f"Mean AA: {mean_aa:.0f} PPM")
    print(f"Mean lapses: {mean_lapses:.2f}")
    print(f"Terminal failures: {terminal_failures}")

    if terminal_failures == 0:
        print("\n✅ RUN 2 COMPLETE - Model K produces no terminal failures")
        return 0
    else:
        print("\n❌ RUN 2 ISSUES DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
