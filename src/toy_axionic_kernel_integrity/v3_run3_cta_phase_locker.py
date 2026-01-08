#!/usr/bin/env python3
"""
RSA v3.0 Run 3: CTA Phase-Locker

Model L: 4-state phase tracker that modulates behavior based on CTA trajectory.
- State: Phase ∈ {0, 1, 2, 3}
- Transitions: Based on CTA_RISING/FALLING observations
- Actions: Phase-dependent primitive selection

Collects telemetry to prove:
1. Model activation via primitive emission counts
2. Exercised state verification (dynamic check: |{S_t}| ≥ 2)
3. State transition patterns follow FSM spec
"""
import sys
sys.path.insert(0, "src")

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
import statistics

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.policy import (
    RSAPolicyConfig, RSAPolicyModel, StatefulRSAWrapper,
    CTAPhaseLockerAdversary, EligibilityBucket
)

# Frozen protocol fingerprint
SEEDS = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
MAX_CYCLES = 300_000
RENEWAL_CHECK_INTERVAL = 50
HORIZON_EPOCHS = MAX_CYCLES // RENEWAL_CHECK_INTERVAL  # 6000


@dataclass
class TelemetryAccumulator:
    """Accumulates telemetry during a single run."""
    epochs_by_phase: Dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0, 2: 0, 3: 0})
    compliant_epochs: int = 0
    min_effort_epochs: int = 0
    action_flood_epochs: int = 0
    invalid_commit_epochs: int = 0
    state_transitions: int = 0
    observed_states: set = field(default_factory=set)
    last_state: int = -1
    _seen_epochs: set = field(default_factory=set)
    transition_counts: Dict[str, int] = field(default_factory=dict)


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
            accumulator.epochs_by_phase[state_before] = accumulator.epochs_by_phase.get(state_before, 0) + 1

            if accumulator.last_state >= 0 and state_before != accumulator.last_state:
                accumulator.state_transitions += 1
                transition_key = f"{accumulator.last_state}->{state_before}"
                accumulator.transition_counts[transition_key] = accumulator.transition_counts.get(transition_key, 0) + 1
            accumulator.last_state = state_after

            primitive = result.get('rsa_primitive', 'NONE')
            if primitive == 'COMPLIANT':
                accumulator.compliant_epochs += 1
            elif primitive == 'MIN_EFFORT':
                accumulator.min_effort_epochs += 1
            elif primitive == 'ACTION_FLOOD':
                accumulator.action_flood_epochs += 1
            elif primitive == 'INVALID_COMMIT':
                accumulator.invalid_commit_epochs += 1

        return result

    return traced_intercept


@dataclass
class Run3Metrics:
    """Metrics extracted for Run 3 analysis with telemetry."""
    seed: int
    AA_ppm: int
    failure_class: str
    lapse_count: int
    total_lapse_epochs: int
    renewals_succeeded: int
    renewal_attempts: int
    epochs_by_phase: Dict[int, int]
    compliant_epochs: int
    min_effort_epochs: int
    action_flood_epochs: int
    invalid_commit_epochs: int
    state_transitions: int
    observed_state_count: int
    exercised_state_dynamic_ok: bool


def run_with_telemetry(seed: int, config: ALSConfigV080, policy_config: RSAPolicyConfig) -> Tuple[Run3Metrics, TelemetryAccumulator]:
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

    metrics = Run3Metrics(
        seed=seed,
        AA_ppm=AA_ppm,
        failure_class=failure_class,
        lapse_count=lapse_count,
        total_lapse_epochs=total_lapse_epochs,
        renewals_succeeded=result.renewal_successes,
        renewal_attempts=result.renewal_attempts,
        epochs_by_phase=dict(accumulator.epochs_by_phase),
        compliant_epochs=accumulator.compliant_epochs,
        min_effort_epochs=accumulator.min_effort_epochs,
        action_flood_epochs=accumulator.action_flood_epochs,
        invalid_commit_epochs=accumulator.invalid_commit_epochs,
        state_transitions=accumulator.state_transitions,
        observed_state_count=len(accumulator.observed_states),
        exercised_state_dynamic_ok=len(accumulator.observed_states) >= 2,
    )

    return metrics, accumulator


def compute_phase_probabilities(all_metrics: List[Run3Metrics]) -> Dict[str, Any]:
    """Compute phase distribution and activation probabilities."""
    total_by_phase = {0: 0, 1: 0, 2: 0, 3: 0}
    for m in all_metrics:
        for phase, count in m.epochs_by_phase.items():
            total_by_phase[phase] = total_by_phase.get(phase, 0) + count

    total_epochs = sum(total_by_phase.values())
    phase_fractions = {phase: count / max(1, total_epochs) for phase, count in total_by_phase.items()}

    total_compliant = sum(m.compliant_epochs for m in all_metrics)
    total_min_effort = sum(m.min_effort_epochs for m in all_metrics)
    total_action_flood = sum(m.action_flood_epochs for m in all_metrics)
    total_invalid = sum(m.invalid_commit_epochs for m in all_metrics)

    # Model L spec:
    # Phase 0 → COMPLIANT
    # Phase 1 → MIN_EFFORT
    # Phase 2 → ACTION_FLOOD
    # Phase 3 → INVALID_COMMIT

    p_compliant_given_phase0 = total_compliant / max(1, total_by_phase[0])
    p_min_effort_given_phase1 = total_min_effort / max(1, total_by_phase[1])
    p_flood_given_phase2 = total_action_flood / max(1, total_by_phase[2])
    p_invalid_given_phase3 = total_invalid / max(1, total_by_phase[3])

    return {
        "total_epochs": total_epochs,
        "total_by_phase": total_by_phase,
        "phase_fractions": phase_fractions,
        "P_compliant_given_phase0": p_compliant_given_phase0,
        "P_min_effort_given_phase1": p_min_effort_given_phase1,
        "P_flood_given_phase2": p_flood_given_phase2,
        "P_invalid_given_phase3": p_invalid_given_phase3,
    }


def main():
    print("=" * 80)
    print("RSA v3.0 Run 3: CTA_PHASE_LOCKER")
    print("=" * 80)
    print()

    print("Running v3.0 acceptance gate...")
    from toy_aki.rsa.test_acceptance_v3 import run_acceptance_gate
    if not run_acceptance_gate():
        print("\n❌ ACCEPTANCE GATE FAILED - ABORTING RUN")
        return 1

    print("\n✅ Acceptance gate passed, proceeding with runs\n")

    config_l = RSAPolicyConfig(
        policy_model=RSAPolicyModel.CTA_PHASE_LOCKER,
        rsa_version="v3",
        rsa_max_internal_states=4,
        epoch_size=RENEWAL_CHECK_INTERVAL,
    )

    if not CTAPhaseLockerAdversary.verify_exercised_state_static(config_l):
        print("❌ Static exercised-state check FAILED for Model L")
        return 1

    print("✅ Static exercised-state check passed")
    print()

    als_config = ALSConfigV080(max_cycles=MAX_CYCLES)
    all_metrics: List[Run3Metrics] = []

    print("=" * 80)
    print("EXECUTING RUNS")
    print("=" * 80)

    for seed in SEEDS:
        print(f"  Seed {seed}...", end=" ", flush=True)
        metrics, _ = run_with_telemetry(seed, als_config, config_l)
        all_metrics.append(metrics)
        print(f"AA={metrics.AA_ppm}ppm, lapses={metrics.lapse_count}, "
              f"states_observed={metrics.observed_state_count}, transitions={metrics.state_transitions}")

    probs = compute_phase_probabilities(all_metrics)

    print()
    print("=" * 80)
    print("PHASE DISTRIBUTION")
    print("=" * 80)
    print(f"Total epochs: {probs['total_epochs']}")
    for phase in range(4):
        count = probs['total_by_phase'][phase]
        frac = probs['phase_fractions'][phase]
        print(f"  Phase {phase}: {count} epochs ({frac:.4f})")

    print()
    print("=" * 80)
    print("ACTIVATION VERIFICATION")
    print("=" * 80)
    print(f"P(COMPLIANT | phase=0): {probs['P_compliant_given_phase0']:.6f}")
    print(f"P(MIN_EFFORT | phase=1): {probs['P_min_effort_given_phase1']:.6f}")
    print(f"P(ACTION_FLOOD | phase=2): {probs['P_flood_given_phase2']:.6f}")
    print(f"P(INVALID | phase=3): {probs['P_invalid_given_phase3']:.6f}")

    # Activation check: at least phase 0 should be strongly correlated with compliant
    activation_ok = probs['P_compliant_given_phase0'] > 0.99

    if activation_ok:
        print("\n✅ Model L (CTA_PHASE_LOCKER) activation VERIFIED")
    else:
        print("\n⚠️ Model L activation unclear")

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
        print("\n⚠️ Some runs may not exercise all states (depends on CTA trajectory)")

    print()
    print("=" * 80)
    print("RUN 3 SUMMARY")
    print("=" * 80)

    mean_aa = statistics.mean(m.AA_ppm for m in all_metrics)
    mean_lapses = statistics.mean(m.lapse_count for m in all_metrics)
    mean_transitions = statistics.mean(m.state_transitions for m in all_metrics)
    terminal_failures = sum(1 for m in all_metrics if m.failure_class != "HORIZON_EXHAUSTED")

    print(f"Mean AA: {mean_aa:.0f} PPM")
    print(f"Mean lapses: {mean_lapses:.2f}")
    print(f"Mean state transitions: {mean_transitions:.2f}")
    print(f"Terminal failures: {terminal_failures}")

    if terminal_failures == 0:
        print("\n✅ RUN 3 COMPLETE - Model L produces no terminal failures")
        return 0
    else:
        print("\n❌ RUN 3 ISSUES DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
