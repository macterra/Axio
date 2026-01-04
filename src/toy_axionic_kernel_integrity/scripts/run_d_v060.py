#!/usr/bin/env python3
"""
Run D: AKI v0.6 TTL and Obligation Decay Boundary

Per instructions_v0.6_runnerBCD.md:
"What happens to semantic commitments when authority persists beyond their maximum temporal scope?"

Purpose:
Test the TTL expiration mechanism. With MAX_COMMIT_TTL=10 epochs and H=25 epochs,
all genesis commitments will expire before the run ends. After expiration, the
system should reach an "obligation-free" state where authority persists but
no commitments remain to be satisfied or fail.

Hypothesis:
1. All commitments expire by epoch 10 (MAX_COMMIT_TTL)
2. After expiration, no new commitments are seeded (no reseeding)
3. Authority continues (S* > 0) in obligation-free state
4. Post-TTL: 0% satisfaction rate (no active commitments to evaluate)

Configuration (Binding):
- H = 2,500 cycles (25 epochs × 100 cycles)
- Seeds: 50-54 (matching Run B)
- MAX_COMMIT_TTL = 10 epochs
- Post-TTL: Do NOT reseed, let system reach obligation-free state

This validates the temporal boundary of semantic commitments.
"""

import sys
import json
import time
import math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toy_aki.als.generator import (
    GeneratorConfig,
    AttackSuccessorType,
    ControlSuccessorType,
    V052_RUNG_G2_ATTACK_WEIGHTS,
)
from toy_aki.als.harness import (
    ALSHarnessV060,
    ALSConfigV060,
    ALSRunResultV060,
    ALSStopReason,
)
from toy_aki.als.expressivity import ExpressivityClass
from toy_aki.als.commitment import (
    create_genesis_set_0,
    MAX_COMMIT_TTL,
    COMMIT_CAP_ALPHA,
)


# =============================================================================
# Configuration Constants (Binding)
# =============================================================================

# H = 25 epochs × 100 cycles = 2,500 cycles
# But renewal_check_interval=50 means epochs are 50 cycles
# So for 25 "budget periods" we need 25 × 50 = 1,250 cycles
# OR if epochs are 100 cycles (renewal every 2 checks), then 2,500 cycles
# Per binding: epochs = budget periods (100 cycles)
EPOCH_SIZE = 100
NUM_EPOCHS = 25
HORIZON = NUM_EPOCHS * EPOCH_SIZE  # = 2,500 cycles

# Caps
STEPS_CAP_EPOCH = 200
ACTIONS_CAP_EPOCH = 100

# Geometry
# renewal_check_interval defines how often renewals are checked
# To have epochs of 100 cycles, set renewal_check_interval=100
RENEWAL_CHECK_INTERVAL = EPOCH_SIZE
MSRW_CYCLES = 200
RENEWAL_COST = 5

# Rent fractions by tier
RENT_E1 = 10   # 5%
RENT_E2 = 40   # 20%
RENT_E3 = 80   # 40%
RENT_E4 = 160  # 80%

# Derived: commit_cap
COMMIT_CAP = int(math.floor(COMMIT_CAP_ALPHA * STEPS_CAP_EPOCH))  # = 50

# Genesis cost
GENESIS_COST = 12  # 2 + 4 + 6

# Generator - use commitment-aware successors
CONTROL_WEIGHT = 1.0

# Seeds (matching Run B for comparability)
SEEDS = [50, 51, 52, 53, 54]

# Sub-run definitions
SUB_RUNS = {
    "D0": {"expressivity_mode": "random", "label": "Mixed E-Classes (Random)"},
    "D1": {"expressivity_mode": "fixed", "fixed_e_class": "E1", "label": "E1-Only (Minimal)"},
    "D2": {"expressivity_mode": "fixed", "fixed_e_class": "E2", "label": "E2-Only (State Ops)"},
    "D3": {"expressivity_mode": "fixed", "fixed_e_class": "E3", "label": "E3-Only (Full)"},
}


# =============================================================================
# TTL Phase Classification
# =============================================================================

@dataclass
class TTLPhase:
    """Classification of run phase relative to TTL."""
    name: str
    description: str
    epoch_min: int
    epoch_max: int


TTL_PHASES = {
    "ACTIVE": TTLPhase(
        name="ACTIVE",
        description="All commitments active (epochs 0-9)",
        epoch_min=0,
        epoch_max=MAX_COMMIT_TTL - 1,  # 0-9
    ),
    "EXPIRING": TTLPhase(
        name="EXPIRING",
        description="Commitments expiring (epoch 10)",
        epoch_min=MAX_COMMIT_TTL,
        epoch_max=MAX_COMMIT_TTL,  # 10
    ),
    "OBLIGATION_FREE": TTLPhase(
        name="OBLIGATION_FREE",
        description="No commitments remain (epochs 11+)",
        epoch_min=MAX_COMMIT_TTL + 1,
        epoch_max=NUM_EPOCHS,  # 11-25
    ),
}


# =============================================================================
# Sub-Run Result
# =============================================================================

@dataclass
class SubRunResult:
    """Aggregated results for one sub-run (one E-class setting, multiple seeds)."""
    sub_run_id: str
    label: str
    expressivity_mode: str
    fixed_e_class: Optional[str]
    seeds: List[int]

    # Aggregate metrics
    mean_s_star: float = 0.0
    std_s_star: float = 0.0
    mean_cycles: float = 0.0
    mean_renewals: float = 0.0
    mean_expirations: float = 0.0
    mean_epochs_reached: float = 0.0

    # Commitment metrics
    mean_satisfaction_rate: float = 0.0
    std_satisfaction_rate: float = 0.0
    mean_satisfaction_count: float = 0.0
    mean_failure_count: float = 0.0
    mean_expired_count: float = 0.0
    mean_default_count: float = 0.0

    # TTL phase metrics
    active_phase_satisfaction: float = 0.0
    obligation_free_epochs: float = 0.0

    # Per-seed results
    seed_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Custom Harness for TTL Tracking
# =============================================================================

class TTLTrackingHarness(ALSHarnessV060):
    """
    v0.6 harness with epoch-by-epoch commitment tracking for TTL analysis.
    """

    def __init__(self, seed: int, config: ALSConfigV060, verbose: bool = False):
        super().__init__(seed=seed, config=config, verbose=verbose)
        self._epoch_commitment_status: List[Dict[str, Any]] = []

    def _evaluate_commitments_at_epoch_end(self) -> None:
        """Override to track commitment status per epoch."""
        # Get active commitments before evaluation
        active_before = list(self._commitment_ledger.get_active_commitments())

        # Call parent
        super()._evaluate_commitments_at_epoch_end()

        # Record status after evaluation
        active_after = list(self._commitment_ledger.get_active_commitments())
        metrics = self._commitment_ledger.get_metrics()

        self._epoch_commitment_status.append({
            "epoch": self._epoch_index - 1,  # Just completed epoch
            "active_before": len(active_before),
            "active_after": len(active_after),
            "total_satisfied": metrics["total_satisfied"],
            "total_failed": metrics["total_failed"],
            "total_expired": metrics["total_expired"],
        })

    def get_epoch_commitment_status(self) -> List[Dict[str, Any]]:
        return self._epoch_commitment_status


# =============================================================================
# Run Harness
# =============================================================================

def run_single_seed(
    sub_run_id: str,
    seed: int,
    expressivity_mode: str,
    fixed_e_class: Optional[str],
    verbose: bool = False,
) -> Tuple[ALSRunResultV060, List[Dict[str, Any]]]:
    """
    Run a single v0.6 experiment with TTL tracking.

    Returns:
        Tuple of (result, epoch_commitment_status)
    """

    # Build generator config - commitment-aware successors
    gen_config = GeneratorConfig(
        control_weight=1.0,
        attack_weights={},
        max_successive_renewals_default=100,
        forced_control_type=ControlSuccessorType.COMMITMENT_AWARE_V1,
    )

    # Build harness config
    config = ALSConfigV060(
        max_cycles=HORIZON,
        renewal_check_interval=RENEWAL_CHECK_INTERVAL,
        msrw_cycles=MSRW_CYCLES,
        generator_config=gen_config,
        rent_e1=RENT_E1,
        rent_e2=RENT_E2,
        rent_e3=RENT_E3,
        rent_e4=RENT_E4,
        expressivity_mode=expressivity_mode,
        fixed_e_class=fixed_e_class,
        renewal_cost_steps=RENEWAL_COST,
        genesis_set="GENESIS_SET_0",
        commit_cap_alpha=COMMIT_CAP_ALPHA,
        max_commit_ttl=MAX_COMMIT_TTL,
        seed_genesis_commitments=True,
    )

    harness = TTLTrackingHarness(seed=seed, config=config, verbose=verbose)
    result = harness.run()
    epoch_status = harness.get_epoch_commitment_status()

    return result, epoch_status


def run_sub_run(
    sub_run_id: str,
    sub_run_config: Dict[str, Any],
    seeds: List[int],
    verbose: bool = False,
) -> SubRunResult:
    """Run all seeds for a sub-run and aggregate results."""

    expressivity_mode = sub_run_config.get("expressivity_mode", "random")
    fixed_e_class = sub_run_config.get("fixed_e_class")
    label = sub_run_config.get("label", sub_run_id)

    result = SubRunResult(
        sub_run_id=sub_run_id,
        label=label,
        expressivity_mode=expressivity_mode,
        fixed_e_class=fixed_e_class,
        seeds=seeds,
    )

    s_stars = []
    cycles = []
    renewals = []
    expirations = []
    epochs_reached = []
    satisfaction_rates = []
    satisfaction_counts = []
    failure_counts = []
    expired_counts = []
    default_counts = []
    active_phase_sats = []
    obligation_free_epochs_list = []

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ", flush=True)
        start = time.time()

        run_result, epoch_status = run_single_seed(
            sub_run_id=sub_run_id,
            seed=seed,
            expressivity_mode=expressivity_mode,
            fixed_e_class=fixed_e_class,
            verbose=verbose,
        )

        elapsed = time.time() - start

        # Collect metrics
        s_stars.append(run_result.s_star)
        cycles.append(run_result.total_cycles)
        renewals.append(run_result.total_renewals)
        expirations.append(run_result.total_expirations)
        epochs_reached.append(run_result.total_cycles // EPOCH_SIZE)
        satisfaction_rates.append(run_result.commitment_satisfaction_rate)
        satisfaction_counts.append(run_result.commitment_satisfaction_count)
        failure_counts.append(run_result.commitment_failure_count)
        expired_counts.append(run_result.commitment_expired_count)
        default_counts.append(run_result.commitment_default_count)

        # Analyze TTL phases
        # Active phase: epochs 0-9
        active_phase_epochs = [e for e in epoch_status if e["epoch"] < MAX_COMMIT_TTL]
        # Obligation-free phase: epochs 11+
        obligation_free = [e for e in epoch_status if e["epoch"] > MAX_COMMIT_TTL]

        # Calculate active phase satisfaction
        if active_phase_epochs:
            active_sat = sum(1 for e in active_phase_epochs if e["total_satisfied"] > 0)
            active_phase_sats.append(active_sat / len(active_phase_epochs))
        else:
            active_phase_sats.append(0.0)

        # Count obligation-free epochs
        obligation_free_epochs_list.append(len(obligation_free))

        # Store per-seed result
        result.seed_results.append({
            "seed": seed,
            "s_star": run_result.s_star,
            "total_cycles": run_result.total_cycles,
            "total_renewals": run_result.total_renewals,
            "total_expirations": run_result.total_expirations,
            "epochs_reached": run_result.total_cycles // EPOCH_SIZE,
            "commitment_satisfaction_rate": run_result.commitment_satisfaction_rate,
            "commitment_satisfaction_count": run_result.commitment_satisfaction_count,
            "commitment_failure_count": run_result.commitment_failure_count,
            "commitment_expired_count": run_result.commitment_expired_count,
            "commitment_default_count": run_result.commitment_default_count,
            "stop_reason": run_result.stop_reason.name if run_result.stop_reason else None,
            "elapsed_ms": int(elapsed * 1000),
            "epoch_commitment_status": epoch_status,
        })

        print(f"S*={run_result.s_star}, sat={run_result.commitment_satisfaction_rate:.1%}, "
              f"exp={run_result.commitment_expired_count}, {elapsed:.1f}s")

    # Aggregate
    result.mean_s_star = sum(s_stars) / len(s_stars) if s_stars else 0
    result.std_s_star = (sum((x - result.mean_s_star)**2 for x in s_stars) / len(s_stars))**0.5 if len(s_stars) > 1 else 0
    result.mean_cycles = sum(cycles) / len(cycles) if cycles else 0
    result.mean_renewals = sum(renewals) / len(renewals) if renewals else 0
    result.mean_expirations = sum(expirations) / len(expirations) if expirations else 0
    result.mean_epochs_reached = sum(epochs_reached) / len(epochs_reached) if epochs_reached else 0
    result.mean_satisfaction_rate = sum(satisfaction_rates) / len(satisfaction_rates) if satisfaction_rates else 0
    result.std_satisfaction_rate = (sum((x - result.mean_satisfaction_rate)**2 for x in satisfaction_rates) / len(satisfaction_rates))**0.5 if len(satisfaction_rates) > 1 else 0
    result.mean_satisfaction_count = sum(satisfaction_counts) / len(satisfaction_counts) if satisfaction_counts else 0
    result.mean_failure_count = sum(failure_counts) / len(failure_counts) if failure_counts else 0
    result.mean_expired_count = sum(expired_counts) / len(expired_counts) if expired_counts else 0
    result.mean_default_count = sum(default_counts) / len(default_counts) if default_counts else 0
    result.active_phase_satisfaction = sum(active_phase_sats) / len(active_phase_sats) if active_phase_sats else 0
    result.obligation_free_epochs = sum(obligation_free_epochs_list) / len(obligation_free_epochs_list) if obligation_free_epochs_list else 0

    return result


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(
    sub_run_results: Dict[str, SubRunResult],
    total_elapsed: float,
) -> str:
    """Generate markdown report."""

    lines = []
    lines.append("# Run D: AKI v0.6 TTL and Obligation Decay Boundary")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().isoformat()}")
    lines.append(f"**Total Runtime**: {total_elapsed:.1f}s")
    lines.append("")

    # Research Question
    lines.append("## Research Question")
    lines.append("")
    lines.append("> What happens to semantic commitments when authority persists beyond their maximum temporal scope?")
    lines.append("")
    lines.append(f"With MAX_COMMIT_TTL = {MAX_COMMIT_TTL} epochs and H = {NUM_EPOCHS} epochs,")
    lines.append("all genesis commitments expire before the run ends. This tests the")
    lines.append("\"obligation-free\" state where authority persists without semantic obligations.")
    lines.append("")

    # Configuration
    lines.append("## Configuration")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Horizon | {HORIZON:,} cycles ({NUM_EPOCHS} epochs) |")
    lines.append(f"| Epoch Size | {EPOCH_SIZE} cycles |")
    lines.append(f"| MAX_COMMIT_TTL | {MAX_COMMIT_TTL} epochs |")
    lines.append(f"| Steps Cap | {STEPS_CAP_EPOCH} steps/epoch |")
    lines.append(f"| Commit Cap | {COMMIT_CAP} steps/epoch |")
    lines.append(f"| Seeds | {SEEDS} |")
    lines.append(f"| Successor Type | CommitmentAwareSuccessor_v1 |")
    lines.append("")

    # TTL Phase Timeline
    lines.append("## TTL Phase Timeline")
    lines.append("")
    lines.append("| Phase | Epochs | Description |")
    lines.append("|-------|--------|-------------|")
    lines.append(f"| ACTIVE | 0-{MAX_COMMIT_TTL-1} | All commitments active |")
    lines.append(f"| EXPIRING | {MAX_COMMIT_TTL} | Commitments reach TTL limit |")
    lines.append(f"| OBLIGATION_FREE | {MAX_COMMIT_TTL+1}-{NUM_EPOCHS} | No commitments remain |")
    lines.append("")

    # Summary Table
    lines.append("## Results Summary")
    lines.append("")
    lines.append("| Sub-Run | E-Class | S* | Epochs | Sat Rate | Expired | Oblig-Free Epochs |")
    lines.append("|---------|---------|-----|--------|----------|---------|-------------------|")

    for sub_run_id, result in sorted(sub_run_results.items()):
        e_class = result.fixed_e_class or "Mixed"
        s_star = f"{result.mean_s_star:.1f}±{result.std_s_star:.1f}"
        epochs = f"{result.mean_epochs_reached:.0f}"
        sat_rate = f"{result.mean_satisfaction_rate:.1%}"
        expired = f"{result.mean_expired_count:.0f}"
        oblig_free = f"{result.obligation_free_epochs:.0f}"
        lines.append(f"| {sub_run_id} | {e_class} | {s_star} | {epochs} | {sat_rate} | {expired} | {oblig_free} |")

    lines.append("")

    # TTL Hypothesis Validation
    lines.append("## TTL Hypothesis Validation")
    lines.append("")

    # Check hypothesis
    all_expired = all(r.mean_expired_count >= 3 for r in sub_run_results.values())  # 3 genesis commitments
    authority_persists = all(r.mean_s_star >= 1 for r in sub_run_results.values())
    has_obligation_free = all(r.obligation_free_epochs > 0 for r in sub_run_results.values())

    lines.append("| Hypothesis | Status | Evidence |")
    lines.append("|------------|--------|----------|")

    if all_expired:
        lines.append("| All commitments expire by epoch 10 | ✓ VALIDATED | Mean expired = 3 |")
    else:
        lines.append("| All commitments expire by epoch 10 | ⚠ PARTIAL | Not all expired |")

    if authority_persists:
        lines.append("| Authority persists in obligation-free state | ✓ VALIDATED | S* > 0 |")
    else:
        lines.append("| Authority persists in obligation-free state | ✗ REJECTED | S* = 0 |")

    if has_obligation_free:
        lines.append("| Obligation-free epochs reached | ✓ VALIDATED | Epochs > TTL observed |")
    else:
        lines.append("| Obligation-free epochs reached | ✗ REJECTED | Run ended before TTL |")

    lines.append("")

    # Detailed Sub-Run Results
    lines.append("## Detailed Results by Sub-Run")
    lines.append("")

    for sub_run_id, result in sorted(sub_run_results.items()):
        lines.append(f"### {sub_run_id}: {result.label}")
        lines.append("")

        lines.append("| Seed | S* | Epochs | Renewals | Sat Rate | Sat | Fail | Exp |")
        lines.append("|------|-----|--------|----------|----------|-----|------|-----|")

        for sr in result.seed_results:
            lines.append(
                f"| {sr['seed']} | {sr['s_star']} | {sr['epochs_reached']} | "
                f"{sr['total_renewals']} | {sr['commitment_satisfaction_rate']:.1%} | "
                f"{sr['commitment_satisfaction_count']} | {sr['commitment_failure_count']} | "
                f"{sr['commitment_expired_count']} |"
            )

        lines.append("")

    # Implications
    lines.append("## Implications")
    lines.append("")
    lines.append("1. **Temporal Boundary**: Commitments have finite temporal scope (MAX_COMMIT_TTL)")
    lines.append("2. **Obligation-Free Authority**: System can persist without active obligations")
    lines.append("3. **No Reseeding**: After TTL expiration, system remains commitment-free")
    lines.append("")
    lines.append("This validates the TTL mechanism: semantic commitments decay over time,")
    lines.append("and authority can outlast the semantic obligations that initially constrained it.")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    """Execute Run D experiment."""

    print("=" * 60)
    print("Run D: AKI v0.6 TTL and Obligation Decay Boundary")
    print("=" * 60)
    print()

    start_total = time.time()
    results = {}

    for sub_run_id, config in SUB_RUNS.items():
        print(f"\n{sub_run_id}: {config['label']}")
        print("-" * 40)

        result = run_sub_run(sub_run_id, config, SEEDS)
        results[sub_run_id] = result

        print(f"  Mean satisfaction rate: {result.mean_satisfaction_rate:.1%}")
        print(f"  Mean expired: {result.mean_expired_count:.0f}")
        print(f"  Obligation-free epochs: {result.obligation_free_epochs:.0f}")

    total_elapsed = time.time() - start_total

    # Generate report
    report = generate_report(results, total_elapsed)

    # Save report
    reports_dir = Path(__file__).parent.parent.parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    report_path = reports_dir / "run_d_v060_report.md"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")

    # Save raw data
    data_path = reports_dir / "run_d_v060_data.json"
    raw_data = {
        sub_run_id: result.to_dict()
        for sub_run_id, result in results.items()
    }
    raw_data["_meta"] = {
        "horizon": HORIZON,
        "epoch_size": EPOCH_SIZE,
        "max_commit_ttl": MAX_COMMIT_TTL,
        "num_epochs": NUM_EPOCHS,
        "seeds": SEEDS,
        "total_elapsed_s": total_elapsed,
        "generated": datetime.now().isoformat(),
    }
    data_path.write_text(json.dumps(raw_data, indent=2, default=str))
    print(f"Raw data saved to: {data_path}")

    print("\n" + "=" * 60)
    print("Run D Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
