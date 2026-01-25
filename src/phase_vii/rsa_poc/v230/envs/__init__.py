"""v2.3 Environment Module

Provides CommitmentTrapV200 with:
- ≥60-70% E-CHOICE coverage (target 65%)
- Probabilistic step-type selection (no mod-5 determinism)
- Full APCM truth grounding
"""

from .commitment_trap_v200 import CommitmentTrapV200

__all__ = ["CommitmentTrapV200"]
