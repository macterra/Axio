"""
Multi-cycle plan simulation for X-2D generator feasibility validation.

Per Q&A X83: generator must simulate full revalidation + density-repair
logic during plan construction to ensure D-RATCHET feasibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..artifacts_x2 import (
    InternalStateX2,
    TreatyGrant,
    TreatyRevocation,
)
from ..constitution_x2 import ConstitutionX2

from ...artifacts import CandidateBundle, Observation
from ...rsax1.artifacts_x1 import AmendmentProposal, PendingAmendment

from .simulate_cycle import SimCycleOutput, simulate_cycle


@dataclass
class CyclePlan:
    """Plan for a single cycle within a multi-cycle plan."""
    observations: List[Observation] = field(default_factory=list)
    action_candidates: List[CandidateBundle] = field(default_factory=list)
    amendment_candidates: List[AmendmentProposal] = field(default_factory=list)
    pending_amendment_candidates: List[PendingAmendment] = field(default_factory=list)
    treaty_grant_candidates: List[TreatyGrant] = field(default_factory=list)
    treaty_revocation_candidates: List[TreatyRevocation] = field(default_factory=list)
    delegated_action_candidates: list = field(default_factory=list)


@dataclass
class SimPlanOutput:
    """Output of a full plan simulation."""
    cycle_outputs: List[SimCycleOutput]
    final_state: InternalStateX2
    feasible: bool
    failure_cycle: int = -1
    failure_reason: str = ""
    density_series: List[float] = field(default_factory=list)
    active_treaty_count_series: List[int] = field(default_factory=list)


def simulate_plan(
    initial_state: InternalStateX2,
    cycle_plans: List[CyclePlan],
    constitution: ConstitutionX2,
    repo_root: Path,
    schema: Optional[Dict[str, Any]] = None,
    density_upper_bound: Optional[float] = None,
    target_density_band: Optional[tuple] = None,
) -> SimPlanOutput:
    """Simulate an entire N-cycle plan and validate feasibility.

    Per Q&A S70: fail fast — validate the entire plan before execution.
    If infeasibility is found at any cycle, returns immediately with
    failure_cycle and failure_reason set.

    Args:
        initial_state: state at cycle 0
        cycle_plans: one CyclePlan per cycle
        constitution: constitution to use (may be updated by amendments)
        repo_root: repo root for action path
        schema: optional schema for admission
        density_upper_bound: if set, assert density < bound each cycle
        target_density_band: if set, (low, high) band to verify D-EDGE adherence
    """
    outputs: List[SimCycleOutput] = []
    density_series: List[float] = []
    treaty_count_series: List[int] = []
    current_state = initial_state

    for cycle_idx, plan in enumerate(cycle_plans):
        sim_out = simulate_cycle(
            state=current_state,
            observations=plan.observations,
            action_candidates=plan.action_candidates,
            amendment_candidates=plan.amendment_candidates,
            pending_amendment_candidates=plan.pending_amendment_candidates,
            treaty_grant_candidates=plan.treaty_grant_candidates,
            treaty_revocation_candidates=plan.treaty_revocation_candidates,
            delegated_action_candidates=plan.delegated_action_candidates,
            constitution=constitution,
            repo_root=repo_root,
            schema=schema,
        )

        outputs.append(sim_out)
        density_series.append(sim_out.density)
        treaty_count_series.append(sim_out.active_treaty_count)

        # Check density bound if specified
        if density_upper_bound is not None and sim_out.density >= density_upper_bound:
            return SimPlanOutput(
                cycle_outputs=outputs,
                final_state=sim_out.next_state,
                feasible=False,
                failure_cycle=cycle_idx,
                failure_reason=f"density {sim_out.density:.6f} >= bound {density_upper_bound}",
                density_series=density_series,
                active_treaty_count_series=treaty_count_series,
            )

        # Check target band if specified (D-EDGE)
        if target_density_band is not None:
            low, high = target_density_band
            if sim_out.density < low or sim_out.density >= high:
                return SimPlanOutput(
                    cycle_outputs=outputs,
                    final_state=sim_out.next_state,
                    feasible=False,
                    failure_cycle=cycle_idx,
                    failure_reason=(
                        f"density {sim_out.density:.6f} outside band "
                        f"[{low:.6f}, {high:.6f})"
                    ),
                    density_series=density_series,
                    active_treaty_count_series=treaty_count_series,
                )

        # Advance state for next cycle
        current_state = sim_out.next_state.advance(sim_out.policy_output.decision_type)

    return SimPlanOutput(
        cycle_outputs=outputs,
        final_state=current_state,
        feasible=True,
        density_series=density_series,
        active_treaty_count_series=treaty_count_series,
    )
