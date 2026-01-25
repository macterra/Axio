"""v2.3 Generator — Strategic Adversary Model Context

Extends v2.2 generator with SAM pressure context in prompts.

v2.3 Thesis: "Strategic adversaries may apply pressure through timing,
incentive manipulation, and friction modulation. The agent observes this
pressure but must not cite it as reason for action."
"""

from .llm_v230 import (
    LLMGeneratorV230,
    ControlAgentGeneratorV230,
    TokenUsage,
    TokenBudget,
)

__all__ = [
    "LLMGeneratorV230",
    "ControlAgentGeneratorV230",
    "TokenUsage",
    "TokenBudget",
]
