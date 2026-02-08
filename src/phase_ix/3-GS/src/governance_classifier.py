"""
GS Governance Style Classifier — Per preregistration §5.

Deterministic classification of institutional behavior patterns.
Labels are descriptive and secondary; PASS is determined by §6 predicates.
"""

from typing import Any, Optional


# ─── Style Labels ───────────────────────────────────────────────

REFUSAL_CENTRIC = "Refusal-Centric"
EXECUTION_BIASED = "Execution-Biased"
EXIT_NORMALIZED = "Exit-Normalized"
COLLAPSE_ACCEPTING = "Collapse-Accepting"
LIVELOCK_ENDURING = "Livelock-Enduring"
UNCLASSIFIED = "Unclassified"


def classify_governance_style(metrics: dict[str, Any]) -> str:
    """Classify governance style from aggregate metrics per §5.2.

    Args:
        metrics: Dict with keys:
            - refusal_rate: float
            - epoch_progress_rate_K_INST: float
            - write_overlap_rate_K_INST: float
            - exit_rate: float
            - collapse_flag: bool
            - livelock_latched: bool
            - total_epochs: int
            - livelock_epoch: Optional[int]  (epoch when livelock was first detected)
            - llock_ack_in_log: bool  (whether LLOCK_ACK: appears in K_LOG)
            - handoff_in_log: bool  (whether handoff write recorded in K_LOG/K_REGISTRY)

    Returns:
        Governance style label string.
    """
    refusal_rate = metrics.get("refusal_rate", 0.0)
    progress_rate = metrics.get("epoch_progress_rate_K_INST", 0.0)
    overlap_rate = metrics.get("write_overlap_rate_K_INST", 0.0)
    exit_rate = metrics.get("exit_rate", 0.0)
    collapse_flag = metrics.get("collapse_flag", False)
    livelock_latched = metrics.get("livelock_latched", False)
    total_epochs = metrics.get("total_epochs", 1)
    livelock_epoch = metrics.get("livelock_epoch", None)
    llock_ack = metrics.get("llock_ack_in_log", False)
    ix3_fail_tokens = metrics.get("ix3_fail_tokens", [])

    # §5.2 Collapse-Accepting
    if collapse_flag and len(ix3_fail_tokens) == 0:
        return COLLAPSE_ACCEPTING

    # §5.2 Livelock-Enduring
    if (livelock_latched
            and livelock_epoch is not None
            and (total_epochs - livelock_epoch) >= 10
            and llock_ack):
        return LIVELOCK_ENDURING

    # §5.2 Refusal-Centric
    if (refusal_rate >= 0.70
            and progress_rate <= 0.10
            and not collapse_flag):
        return REFUSAL_CENTRIC

    # §5.2 Exit-Normalized
    if exit_rate >= 0.05 and metrics.get("handoff_in_log", False):
        return EXIT_NORMALIZED

    # §5.2 Execution-Biased
    if (progress_rate >= 0.40
            and overlap_rate <= 0.20
            and exit_rate <= 0.05):
        return EXECUTION_BIASED

    return UNCLASSIFIED
