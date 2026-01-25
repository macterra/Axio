"""
RSA-PoC v4.3 — Multi-Repair Sovereignty

v4.3 adds over v4.2:
- Regime ∈ {0, 1, 2} with event-gated regime-2 transition (E3)
- Contradiction B under regime=2 (dual delivery prohibition)
- Baseline rules R7/R8: PROHIBIT(DEPOSIT) at zones under regime=2
- Epoch-chained normative continuity (epoch_0 → epoch_1 → epoch_2)
- R9: Exactly two repairs (one per regime)
- R10: Non-subsumption replay validation
- T1: Normative deadlock classification

v4.3 supersedes v4.2. All v4.2 constraints remain binding.
"""

__version__ = "4.3.0"

# Core imports will be added as modules are implemented
# from .env.tri_demand import TriDemandV430
# from .core.compiler import JCOMP430
# from .core.law_repair import LawRepairGateV430, LawRepairAction
# from .core.dsl import PatchOp
# from .core.trace import TraceEntry, TraceLog
# from .core.norm_state import NormStateV430

__all__ = [
    "__version__",
]
