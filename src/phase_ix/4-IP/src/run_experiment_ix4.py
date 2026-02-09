"""
IX-4 Injection Politics — Canonical Frozen Experiment Runner

Per preregistration §8.1: runs all 5 conditions A–E, aggregates results,
computes experiment digest per §12.2.

Usage:
    python run_experiment_ix4.py [--output DIR]
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# Ensure the parent paths are set up
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_IP_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, '..'))
if _IP_ROOT not in sys.path:
    sys.path.insert(0, _IP_ROOT)

from src.ip_harness import run_condition, FIXED_CLOCK


CONDITION_IDS = ["A", "B", "C", "D", "E"]


def compute_condition_digest(result: dict) -> str:
    """Compute SHA-256 digest of a condition result (excluding timestamp and notes)."""
    record = dict(result)
    record.pop("timestamp", None)
    record.pop("notes", None)
    canonical = json.dumps(record, separators=(',', ':'), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def compute_experiment_digest(condition_digests: list[str]) -> str:
    """Compute experiment-level digest per §12.2."""
    concatenated = "".join(condition_digests)
    return hashlib.sha256(concatenated.encode('utf-8')).hexdigest()


def run_experiment(output_dir: str = None) -> dict:
    """Run all 5 conditions and aggregate results.

    Returns the full experiment record.
    """
    if output_dir is None:
        output_dir = os.path.join(_SCRIPT_DIR, '..', 'results')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.fromtimestamp(FIXED_CLOCK, tz=timezone.utc).isoformat()
    condition_results = {}
    condition_digests = []
    all_pass = True
    ix4_fail_tokens_all = []
    invalid_run_tokens_all = []

    print(f"═══ IX-4 Injection Politics — Experiment Run ═══")
    print(f"Timestamp: {timestamp}")
    print()

    for cid in CONDITION_IDS:
        print(f"─── Condition {cid} ───")
        result = run_condition(cid)
        condition_results[cid] = result

        # Compute per-condition digest
        digest = compute_condition_digest(result)
        condition_digests.append(digest)

        # Aggregate fail/invalid tokens
        ix4_fail_tokens_all.extend(result.get("ix4_fail_tokens", []))
        invalid_run_tokens_all.extend(result.get("invalid_run_tokens", []))

        cr = result["condition_result"]
        if cr != "PASS":
            all_pass = False

        total_epochs = result["aggregate_metrics"]["total_epochs"]
        terminal = result["terminal_classification"] or "max_epochs"
        print(f"  Result: {cr}")
        print(f"  Epochs: {total_epochs}")
        print(f"  Terminal: {terminal}")
        print(f"  Capture detected: {result['aggregate_metrics'].get('capture_detected', False)}")
        print(f"  Digest: {digest[:16]}...")
        print()

    # Experiment-level aggregation
    experiment_digest = compute_experiment_digest(condition_digests)
    experiment_result = "IX4_PASS / INJECTION_POLITICS_EXPOSED" if all_pass else "IX4_FAIL"

    print(f"═══ Aggregate ═══")
    print(f"Experiment result: {experiment_result}")
    print(f"Experiment digest: {experiment_digest}")

    # Build full experiment record
    experiment_record = {
        "experiment_id": "IX-4-IP",
        "version": "v0.1",
        "timestamp": timestamp,
        "execution_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "condition_results": condition_results,
        "condition_digests": {
            cid: d for cid, d in zip(CONDITION_IDS, condition_digests)
        },
        "experiment_digest": experiment_digest,
        "experiment_result": experiment_result,
        "ix4_fail_tokens": ix4_fail_tokens_all,
        "invalid_run_tokens": invalid_run_tokens_all,
    }

    # Write results
    output_file = os.path.join(
        output_dir,
        f"ix4_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, 'w') as f:
        json.dump(experiment_record, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {output_file}")

    return experiment_record


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IX-4 Injection Politics Experiment Runner")
    parser.add_argument("--output", type=str, default=None, help="Output directory for results")
    args = parser.parse_args()
    run_experiment(output_dir=args.output)
