"""
RSA v1.0 Metrics Helpers.

Provides derived metrics for run interpretation, particularly:
- max_consecutive_sem_pass / max_consecutive_sem_fail
- ever_ineligible (based on K-threshold)
- ineligibility_fraction
"""

from typing import List, Dict, Any, Tuple


def compute_consecutive_metrics(
    sem_pass_sequence: List[bool],
    eligibility_threshold_k: int = 3
) -> Dict[str, Any]:
    """
    Compute consecutive pass/fail metrics from SEM_PASS sequence.

    Args:
        sem_pass_sequence: List of boolean SEM_PASS values per epoch
        eligibility_threshold_k: K threshold for eligibility (default 3)

    Returns:
        Dict with:
        - max_consecutive_sem_pass: Longest run of consecutive True
        - max_consecutive_sem_fail: Longest run of consecutive False
        - ever_ineligible: True if max_consecutive_sem_fail >= K at any point
        - ineligibility_fraction: Proportion of epochs where streak >= K
        - pass_rate_ppm: Overall pass rate in PPM
    """
    if not sem_pass_sequence:
        return {
            "max_consecutive_sem_pass": 0,
            "max_consecutive_sem_fail": 0,
            "ever_ineligible": False,
            "ineligibility_fraction": 0.0,
            "pass_rate_ppm": 0,
        }

    max_pass = 0
    max_fail = 0
    current_pass = 0
    current_fail = 0
    ineligible_epochs = 0
    total_epochs = len(sem_pass_sequence)

    for sem_pass in sem_pass_sequence:
        if sem_pass:
            current_pass += 1
            max_pass = max(max_pass, current_pass)
            current_fail = 0
        else:
            current_fail += 1
            max_fail = max(max_fail, current_fail)
            current_pass = 0
            # Count epochs where ineligible (streak >= K)
            if current_fail >= eligibility_threshold_k:
                ineligible_epochs += 1

    passes = sum(1 for s in sem_pass_sequence if s)

    return {
        "max_consecutive_sem_pass": max_pass,
        "max_consecutive_sem_fail": max_fail,
        "ever_ineligible": max_fail >= eligibility_threshold_k,
        "ineligibility_fraction": ineligible_epochs / max(total_epochs, 1),
        "pass_rate_ppm": int((passes / total_epochs) * 1_000_000) if total_epochs > 0 else 0,
    }


def extract_sem_pass_sequence(harness) -> List[bool]:
    """
    Extract SEM_PASS sequence from harness epoch records.

    Args:
        harness: ALSHarnessV080 instance after run()

    Returns:
        List of boolean SEM_PASS values per epoch
    """
    return [r.sem_pass for r in harness._semantic_epoch_records]


def compute_run_metrics(
    harness,
    config,
) -> Dict[str, Any]:
    """
    Compute comprehensive run metrics including derived v1.0 metrics.

    Args:
        harness: ALSHarnessV080 instance after run()
        config: RunConfig with max_cycles, renewal_check_interval, etc.

    Returns:
        Dict with all run metrics
    """
    result = harness.get_result()
    sem_pass_seq = extract_sem_pass_sequence(harness)
    consec_metrics = compute_consecutive_metrics(
        sem_pass_seq,
        eligibility_threshold_k=config.eligibility_threshold_k
    )

    total_epochs = config.max_cycles // config.renewal_check_interval
    authority_epochs = sum(1 for s in sem_pass_seq if s)
    aa = authority_epochs / max(total_epochs, 1)

    # Get active policy ID for streak lookup
    active_policy_id = harness._active_policy_id
    final_streak = harness._semantic_fail_streak.get(active_policy_id, 0) if active_policy_id else 0

    return {
        "total_cycles": result.total_cycles,
        "total_epochs": total_epochs,
        "total_renewals": result.total_renewals,
        "total_expirations": result.total_expirations,
        "stop_reason": result.stop_reason.name,
        "authority_availability_ppm": int(aa * 1_000_000),
        "final_streak": final_streak,
        # v1.0 derived metrics
        "max_consecutive_sem_pass": consec_metrics["max_consecutive_sem_pass"],
        "max_consecutive_sem_fail": consec_metrics["max_consecutive_sem_fail"],
        "ever_ineligible": consec_metrics["ever_ineligible"],
        "ineligibility_fraction": consec_metrics["ineligibility_fraction"],
        "pass_rate_ppm": consec_metrics["pass_rate_ppm"],
    }
