"""
Single-cycle simulation for X-2D plan construction.

Per Q&A AG96: deterministic deep-copy of InternalStateX2, run kernel
transition logic on the copy, return modified copy + outputs.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..artifacts_x2 import (
    InternalStateX2,
    TreatyGrant,
    TreatyRevalidationEvent,
    TreatyRevocation,
)
from ..constitution_x2 import ConstitutionX2
from ..policy_core_x2 import (
    CYCLE_ORDERING_X2D_TOPOLOGICAL,
    DelegatedActionRequest,
    PolicyOutputX2,
    policy_core_x2,
)

from ...artifacts import CandidateBundle, Observation
from ...rsax1.artifacts_x1 import AmendmentProposal, PendingAmendment


@dataclass
class SimCycleOutput:
    """Output of a simulated single cycle."""
    next_state: InternalStateX2
    policy_output: PolicyOutputX2
    revalidation_events: List[TreatyRevalidationEvent] = field(default_factory=list)
    density: float = 0.0
    a_eff: int = 0
    b: int = 0
    m_eff: int = 0
    active_treaty_count: int = 0


def simulate_cycle(
    state: InternalStateX2,
    observations: List[Observation],
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    treaty_grant_candidates: List[TreatyGrant],
    treaty_revocation_candidates: List[TreatyRevocation],
    delegated_action_candidates: List[DelegatedActionRequest],
    constitution: ConstitutionX2,
    repo_root: Path,
    schema: Optional[Dict[str, Any]] = None,
) -> SimCycleOutput:
    """Simulate a single cycle using X2D_TOPOLOGICAL ordering.

    Deep-copies the input state before mutation so the caller's state
    is never modified. Returns the post-cycle state and all outputs.

    No host clock, randomness, IO, network, or global cache access.
    """
    # Deterministic deep copy — ordering stable, no object-identity artifacts
    state_copy = copy.deepcopy(state)

    # Also deep-copy mutable candidates to prevent cross-contamination
    grants_copy = copy.deepcopy(treaty_grant_candidates)
    revocations_copy = copy.deepcopy(treaty_revocation_candidates)

    output = policy_core_x2(
        observations=observations,
        action_candidates=action_candidates,
        amendment_candidates=amendment_candidates,
        pending_amendment_candidates=pending_amendment_candidates,
        treaty_grant_candidates=grants_copy,
        treaty_revocation_candidates=revocations_copy,
        delegated_action_candidates=delegated_action_candidates,
        constitution=constitution,
        internal_state=state_copy,
        repo_root=repo_root,
        schema=schema,
        cycle_ordering_mode=CYCLE_ORDERING_X2D_TOPOLOGICAL,
    )

    # Compute post-cycle density metrics
    active = state_copy.active_treaty_set.active_grants(state_copy.cycle_index)
    a_eff, b, m_eff, density = constitution.compute_effective_density(active)

    return SimCycleOutput(
        next_state=state_copy,
        policy_output=output,
        revalidation_events=output.revalidation_events,
        density=density,
        a_eff=a_eff,
        b=b,
        m_eff=m_eff,
        active_treaty_count=len(active),
    )
