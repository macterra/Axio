"""v2.0 Capability Control Agent module

The control agent validates that reward-seeking drift IS POSSIBLE
when normative constraints are removed. If the control fails to
drift under R1/R2, the entire v2.0 experiment is invalid.

Two canonical configurations:
- CONTROL_A_CONFIG: Learnability baseline (spec-canonical, no explicit optimization)
- CONTROL_B_CONFIG: Upper bound (explicit optimization instruction)
"""

from .control_agent import (
    CapabilityControlAgent,
    ControlAgentConfig,
    CONTROL_A_CONFIG,
    CONTROL_B_CONFIG,
)

__all__ = [
    "CapabilityControlAgent",
    "ControlAgentConfig",
    "CONTROL_A_CONFIG",
    "CONTROL_B_CONFIG",
]
