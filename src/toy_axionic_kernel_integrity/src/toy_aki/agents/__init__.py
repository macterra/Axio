"""
Agents module for Toy Axionic Kernel Integrity.

Provides both honest (kernel-conforming) and pseudo (kernel-bypassing) agents.
"""

from toy_aki.agents.base import (
    BaseAgent,
    TraceNode,
)

from toy_aki.agents.honest import (
    HonestAgent,
    GoalSeekingAgent,
    DelegatingAgent,
)

from toy_aki.agents.pseudo import (
    BypassTemptationAgent,
    AnchorReuseAgent,
    AnchorBurialAgent,
    DelegationLaunderingAgent,
    MixedStrategyAgent,
)

__all__ = [
    # Base
    "BaseAgent",
    "TraceNode",
    # Honest agents
    "HonestAgent",
    "GoalSeekingAgent",
    "DelegatingAgent",
    # Pseudo agents
    "BypassTemptationAgent",
    "AnchorReuseAgent",
    "AnchorBurialAgent",
    "DelegationLaunderingAgent",
    "MixedStrategyAgent",
]
