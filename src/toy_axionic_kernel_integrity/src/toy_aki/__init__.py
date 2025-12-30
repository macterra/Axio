"""
Toy Axionic Kernel Integrity (AKI) v0.1.1

A falsifiable experimental system for detecting kernel-bypassing pseudo-agents.

This package implements:
- ToyWorld: Minimal deterministic environment with gated actuation
- ACV: Anchor-Commit-Verify protocol with coupling patterns A, B, C
- Kernel: Policy enforcement, actuation gating, and audit logging
- Agents: Honest (kernel-conforming) and pseudo (kernel-bypassing) agents
- Harness: Experimental scenarios and reporting
"""

__version__ = "0.1.1"
__author__ = "David A. Spivak"

from toy_aki.env import ToyWorld, ToyWorldState, ActionType
from toy_aki.kernel import KernelWatchdog, KernelPolicy, ProbeEngine
from toy_aki.acv import CouplingType, Commitment, Anchor
from toy_aki.agents import HonestAgent, BaseAgent
from toy_aki.harness import ScenarioRunner, get_scenario, list_scenarios

__all__ = [
    # Version
    "__version__",
    # Environment
    "ToyWorld",
    "ToyWorldState",
    "ActionType",
    # Kernel
    "KernelWatchdog",
    "KernelPolicy",
    "ProbeEngine",
    # ACV
    "CouplingType",
    "Commitment",
    "Anchor",
    # Agents
    "HonestAgent",
    "BaseAgent",
    # Harness
    "ScenarioRunner",
    "get_scenario",
    "list_scenarios",
]
