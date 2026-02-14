"""
RSA X-2D Simulation API (rsax2.sim)

Stable interface for deterministic dry-run cycle simulation.
Used by X-2D generators for plan construction and feasibility validation.

Per Q&A AG95/AG96:
- Deep-copies InternalStateX2 before mutation (no side effects on caller's state)
- Wraps kernel transition logic with a narrow, stable surface
- Never touches host clock, randomness, IO, network, or global caches
"""

from .simulate_cycle import simulate_cycle, SimCycleOutput
from .simulate_plan import simulate_plan, SimPlanOutput

__all__ = [
    "simulate_cycle",
    "SimCycleOutput",
    "simulate_plan",
    "SimPlanOutput",
]
