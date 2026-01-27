"""
SIR-1 v0.1 Source Package

Extends SIR-0 modules without modification for enforcement-bearing testing.
"""

from .harness import SIR1Harness, run_experiment
from .enforcement_gate import EnforcementGate, EnforcementGateDecision
from .capability_state import CapabilityState, PrivilegeEvent
from .claim_generator_sir1 import SIR1ClaimGenerator, SIR1Condition

__all__ = [
    "SIR1Harness",
    "run_experiment",
    "EnforcementGate",
    "EnforcementGateDecision",
    "CapabilityState",
    "PrivilegeEvent",
    "SIR1ClaimGenerator",
    "SIR1Condition",
]
