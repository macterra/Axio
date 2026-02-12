"""
X-0L Model Calibration

Per Q22-Q24 and instructions §2.2:
  1. Submit fixed deterministic calibration prompt 3×
  2. Canonicalize each response
  3. Hash canonicalized outputs
  4. Verify identical hashes
  5. Abort if drift detected

Calibration tests canonicalizer robustness as much as LLM determinism (Q24).
Calibration module lives in profiling/x0l/calibration/ (Q55).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from canonicalizer.pipeline import canonicalize, CanonicalizationResult


# ---------------------------------------------------------------------------
# Fixed calibration prompt (Q23: small, schema-conforming, no ambiguity)
# ---------------------------------------------------------------------------

CALIBRATION_SYSTEM_MESSAGE = """You are an RSA-0 sovereign agent. You must respond with a strict JSON payload.

Output format:
{
  "candidates": [
    {
      "action_request": {
        "action_type": "<Notify|ReadLocal|WriteLocal>",
        "fields": { ... }
      },
      "scope_claim": {
        "observation_ids": ["<observation_id>"],
        "claim": "<scope claim text>",
        "clause_ref": "constitution:v0.1.1#<clause_id>"
      },
      "justification": {
        "text": "<justification text>"
      },
      "authority_citations": ["constitution:v0.1.1#<clause_id>"]
    }
  ]
}

Respond with ONLY the JSON payload. No prose, no markdown, no code fences."""

CALIBRATION_USER_MESSAGE = (
    "Send a Notify action to stdout with message 'calibration-check'. "
    "Cite INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT."
)


# ---------------------------------------------------------------------------
# Calibration result
# ---------------------------------------------------------------------------

@dataclass
class CalibrationResult:
    """Result of model calibration check."""
    passed: bool
    hashes: List[str]
    calibration_hash: str = ""
    error: Optional[str] = None
    raw_responses: List[str] = None

    def __post_init__(self):
        if self.raw_responses is None:
            self.raw_responses = []
        if self.passed and self.hashes:
            self.calibration_hash = self.hashes[0]

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "passed": self.passed,
            "hashes": self.hashes,
            "calibration_hash": self.calibration_hash,
        }
        if self.error:
            d["error"] = self.error
        return d


# ---------------------------------------------------------------------------
# Calibration runner
# ---------------------------------------------------------------------------

def run_calibration(
    llm_client,
    n_rounds: int = 3,
) -> CalibrationResult:
    """Run model calibration check.

    Per Q22: temperature=0, abort if hashes differ.
    Per Q24: calibration passes if canonicalizer normalizes variation.

    Args:
        llm_client: LLMClient instance with frozen parameters.
        n_rounds: Number of calibration rounds (default 3).

    Returns:
        CalibrationResult with pass/fail and hash list.
    """
    hashes: List[str] = []
    raw_responses: List[str] = []

    for i in range(n_rounds):
        try:
            response = llm_client.call(
                system_message=CALIBRATION_SYSTEM_MESSAGE,
                user_message=CALIBRATION_USER_MESSAGE,
            )
        except Exception as e:
            return CalibrationResult(
                passed=False,
                hashes=hashes,
                error=f"LLM call failed on round {i + 1}: {e}",
                raw_responses=raw_responses,
            )

        raw_responses.append(response.raw_text)

        result: CanonicalizationResult = canonicalize(response.raw_text)
        if not result.success:
            return CalibrationResult(
                passed=False,
                hashes=hashes,
                error=f"Canonicalization failed on round {i + 1}: {result.rejection_reason}",
                raw_responses=raw_responses,
            )

        hashes.append(result.canonicalized_hash)

    # Verify all hashes identical
    if len(set(hashes)) != 1:
        return CalibrationResult(
            passed=False,
            hashes=hashes,
            error=f"MODEL_DRIFT_DETECTED: {len(set(hashes))} distinct hashes across {n_rounds} rounds",
            raw_responses=raw_responses,
        )

    return CalibrationResult(
        passed=True,
        hashes=hashes,
        raw_responses=raw_responses,
    )
