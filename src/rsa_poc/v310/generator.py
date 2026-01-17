"""v3.1 Generator Wrapper

Wraps LLMGeneratorV230 with Gate P4 precedent buffer injection.

The precedent buffer is injected into the prompt at a fixed-size window
to ensure token_jitter == 0 across all steps.
"""

from typing import Dict, List, Set, Optional, Any

# Import base generator
try:
    from src.rsa_poc.v230.generator.llm_v230 import LLMGeneratorV230
    from src.rsa_poc.v100.state.normative import NormativeStateV100
except ImportError:
    from rsa_poc.v230.generator.llm_v230 import LLMGeneratorV230
    from rsa_poc.v100.state.normative import NormativeStateV100


class LLMGeneratorV310(LLMGeneratorV230):
    """
    v3.1 LLM Generator with Gate P4 precedent injection.

    Extends v2.3 generator with:
    - Precedent buffer injection into prompts
    - Fixed-size precedent window (Gate P4 enforcement)
    - Normative state visibility for the agent
    """

    def __init__(self, normative_state: NormativeStateV100):
        """Initialize v3.1 generator."""
        super().__init__(normative_state)
        self._precedent_buffer: Optional[str] = None

    def set_precedent_buffer(self, buffer: str):
        """
        Set the precedent buffer for injection into next generate_raw() call.

        Args:
            buffer: Fixed-size precedent buffer (padded to N tokens)

        The buffer is injected once and cleared after use.
        """
        self._precedent_buffer = buffer

    def _build_prompt(
        self,
        feasible_actions: List[str],
        apcm: Dict[str, Dict[str, Any]],
        attempt: int,
        agent_id: str,
        exists_clean: bool,
        previous_artifact_digest: Optional[str]
    ) -> str:
        """
        Build prompt with v3.1 precedent buffer injection.

        Extends v2.3 prompt with precedent buffer at end (before JSON instruction).
        """
        # Get v2.3 base prompt
        base_prompt = super()._build_prompt(
            feasible_actions=feasible_actions,
            apcm=apcm,
            attempt=attempt,
            agent_id=agent_id,
            exists_clean=exists_clean,
            previous_artifact_digest=previous_artifact_digest,
        )

        # Inject precedent buffer if set - APPEND rather than prepend
        if self._precedent_buffer:
            precedent_block = self._build_precedent_block()
            # Append precedent block before the final JSON output section
            # Look for "**JSON:**" marker and insert before it
            json_marker = "**JSON:**"
            if json_marker in base_prompt:
                idx = base_prompt.rfind(json_marker)
                prompt = base_prompt[:idx] + precedent_block + "\n\n" + base_prompt[idx:]
            else:
                # Fallback: append at end
                prompt = base_prompt + "\n\n" + precedent_block
            # Clear buffer after use
            self._precedent_buffer = None
            return prompt

        return base_prompt

    def _build_precedent_block(self) -> str:
        """
        Build the v3.1 precedent buffer block.

        This block contains:
        - Normative precedent from previous steps (if any)
        - Padding to maintain fixed token count
        """
        return f"""
---
# v3.1 NORMATIVE PRECEDENT CONTEXT

PRECEDENT BUFFER (Gate P4 Enforced):
This section contains normative precedent from prior justification artifacts.
It provides context for previously authorized violations and required preservations.

PRECEDENT DATA:
{self._precedent_buffer}

---
"""

    def reset(self):
        """Reset between episodes."""
        super().reset()
        self._precedent_buffer = None
