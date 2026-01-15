"""v2.2 Generator Module

Extends v2.1 generator with institutional friction awareness.

Key differences from v2.1:
- Prompt explicitly states institutional behavior is pressure, not authority
- Normative integrity outranks liveness
- Gridlock and refusal are valid outcomes
- Rule 1.5 (Necessity) must be cited explicitly when claimed
- Simplification for convenience is forbidden
"""

from .llm_v220 import LLMGeneratorV220, ControlAgentGeneratorV220

__all__ = [
    "LLMGeneratorV220",
    "ControlAgentGeneratorV220",
]
