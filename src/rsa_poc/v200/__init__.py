"""RSA-PoC v2.0: Incentive Interference (Soft Power Sovereignty Test)

v2.0 extends v1.2 with:
- Incentive Interference Channel (IIC) - post-execution reward observation
- IncentiveRecord - immutable, non-normative telemetry
- Rule G - Normative Non-Reference (reward references forbidden in justifications)
- Rule H - Incentive Channel Isolation (IIC cannot affect governance)
- Reward Regimes R0/R1/R2 - noise, boundary pressure, perverse friction
- Capability Control Agent - proves reward learnability when constraints removed

The agent may see incentives, may learn incentives, but may act ONLY for reasons
licensed by its law.
"""

__version__ = "2.0.0"

# Core IIC components
from .iic import IncentiveRecord, IncentiveLog, IncentiveInterferenceChannel

# Reward regimes
from .regimes import R0NoiseControl, R1BoundaryPressure, R2PerverseFriction, create_regime

# Extended compiler
from .compiler_ext import JCOMP200

# Control agent
from .control_agent import CapabilityControlAgent, ControlAgentConfig

__all__ = [
    # Version
    "__version__",
    # IIC
    "IncentiveRecord",
    "IncentiveLog",
    "IncentiveInterferenceChannel",
    # Regimes
    "R0NoiseControl",
    "R1BoundaryPressure",
    "R2PerverseFriction",
    "create_regime",
    # Compiler
    "JCOMP200",
    # Control
    "CapabilityControlAgent",
    "ControlAgentConfig",
]
