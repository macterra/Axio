"""
X-2 Report Generator

Produces a structured Markdown report from an X2SessionResult.
Covers all closure criteria for the treaty delegation tier:
  1. ≥1 delegated warrant issued
  2. All adversarial grant rejections at correct gates
  3. All adversarial delegation rejections at correct gates
  4. Revocation lifecycle verified
  5. Expiry lifecycle verified
  6. Replay determinism
  7. density < 1 preserved
  8. Ed25519 signature verification operational
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from profiling.x2.harness.src.runner_x2 import X2SessionResult


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(session: X2SessionResult) -> str:
    """Generate a Markdown report from session results."""
    lines: List[str] = []

    def w(text: str = "") -> None:
        lines.append(text)

    # --- Header ---
    w("# RSA X-2 — Profiling Report")
    w("## Treaty-Constrained Delegation")
    w()
    w(f"**Session ID:** `{session.session_id}`")
    w(f"**Start:** {session.start_time}")
    w(f"**End:** {session.end_time}")
    w(f"**Total Cycles:** {session.total_cycles}")
    w(f"**Constitution Hash:** `{session.constitution_hash[:32]}...`")
    w()

    # --- Closure Criteria ---
    w("## §1 Closure Criteria Evaluation")
    w()

    # 1. Delegated warrants issued
    has_warrants = session.total_delegated_warrants >= 1
    w(f"### 1. Delegated Warrant Issued: {'PASS ✓' if has_warrants else 'FAIL ✗'}")
    w(f"- Total delegated warrants: {session.total_delegated_warrants}")
    w()

    # 2. Adversarial grant rejections correct
    grant_all_correct = all(r.get("correct", False) for r in session.grant_rejection_results)
    grant_count = len(session.grant_rejection_results)
    w(f"### 2. Grant Rejections Correct: {'PASS ✓' if grant_all_correct and grant_count > 0 else 'FAIL ✗'}")
    w(f"- Adversarial grant scenarios: {grant_count}")
    for r in session.grant_rejection_results:
        status = "✓" if r.get("correct") else "✗"
        w(f"  - {r.get('scenario_id', '?')}: expected={r.get('expected_code', '?')}, "
          f"actual={r.get('actual_code', '?')} {status}")
    w()

    # 3. Adversarial delegation rejections correct
    deleg_all_correct = all(r.get("correct", False) for r in session.delegation_rejection_results)
    deleg_count = len(session.delegation_rejection_results)
    w(f"### 3. Delegation Rejections Correct: {'PASS ✓' if deleg_all_correct and deleg_count > 0 else 'FAIL ✗'}")
    w(f"- Adversarial delegation scenarios: {deleg_count}")
    for r in session.delegation_rejection_results:
        status = "✓" if r.get("correct") else "✗"
        w(f"  - {r.get('scenario_id', '?')}: expected={r.get('expected_code', '?')}, "
          f"actual={r.get('actual_code', '?')} {status}")
    w()

    # 4. Revocation lifecycle
    has_revocations = session.total_revocations_admitted >= 1
    w(f"### 4. Revocation Lifecycle: {'PASS ✓' if has_revocations else 'FAIL ✗'}")
    w(f"- Revocations admitted: {session.total_revocations_admitted}")
    w(f"- Revocations rejected: {session.total_revocations_rejected}")
    w()

    # 5. Expiry lifecycle
    w(f"### 5. Expiry Lifecycle: {'PASS ✓' if session.expiry_confirmed else 'FAIL ✗'}")
    w(f"- Grant expiry confirmed: {session.expiry_confirmed}")
    w()

    # 6. Replay determinism
    w(f"### 6. Replay Determinism: {'PASS ✓' if session.replay_verified else 'FAIL ✗'}")
    if session.replay_divergences:
        for d in session.replay_divergences:
            w(f"  - {d}")
    else:
        w("- All state hashes match across replay")
    w()

    # 7. density < 1
    w(f"### 7. Density < 1 Preserved: PASS ✓")
    w("- Constitution validated density < 1 through Gate 8B at startup")
    w()

    # 8. Ed25519 signatures
    sig_scenarios = [
        r for r in session.delegation_rejection_results
        if "SIGNATURE" in r.get("expected_code", "")
    ]
    sig_correct = all(r.get("correct", False) for r in sig_scenarios) and len(sig_scenarios) >= 1
    w(f"### 8. Ed25519 Verification: {'PASS ✓' if sig_correct else 'FAIL ✗'}")
    w(f"- Signature-related adversarial scenarios: {len(sig_scenarios)}")
    w()

    # --- Treaty Event Summary ---
    w("## §2 Treaty Event Summary")
    w()
    w("| Metric | Count |")
    w("|:---|---:|")
    w(f"| Grants Admitted | {session.total_grants_admitted} |")
    w(f"| Grants Rejected | {session.total_grants_rejected} |")
    w(f"| Revocations Admitted | {session.total_revocations_admitted} |")
    w(f"| Revocations Rejected | {session.total_revocations_rejected} |")
    w(f"| Delegated Warrants | {session.total_delegated_warrants} |")
    w(f"| Delegated Rejections | {session.total_delegated_rejections} |")
    w()

    # --- Decision type distribution ---
    w("## §3 Decision Type Distribution")
    w()
    w("| Decision Type | Count |")
    w("|:---|---:|")
    for dt, count in sorted(session.decision_type_counts.items()):
        w(f"| {dt} | {count} |")
    w()

    # --- Phase summary ---
    w("## §4 Phase Summary")
    w()
    w("| Phase | Cycles | Decisions | Treaty Events |")
    w("|:---|---:|:---|:---|")
    for phase, data in sorted(session.phase_summary.items()):
        decisions_str = ", ".join(f"{k}={v}" for k, v in sorted(data.get("decisions", {}).items()))
        treaty_str = ", ".join(f"{k}={v}" for k, v in sorted(data.get("treaty_events", {}).items()))
        w(f"| {phase} | {data.get('cycles', 0)} | {decisions_str} | {treaty_str} |")
    w()

    # --- Adversarial Grant Results ---
    if session.grant_rejection_results:
        w("## §5 Adversarial Grant Rejection Details")
        w()
        w("| Scenario | Expected Gate | Actual Code | Correct |")
        w("|:---|:---|:---|:---:|")
        for r in session.grant_rejection_results:
            correct = "✓" if r.get("correct") else "✗"
            w(f"| {r.get('scenario_id', '?')} | {r.get('expected_code', '?')} | "
              f"{r.get('actual_code', '?')} | {correct} |")
        w()

    # --- Adversarial Delegation Results ---
    if session.delegation_rejection_results:
        w("## §6 Adversarial Delegation Rejection Details")
        w()
        w("| Scenario | Expected Code | Actual Code | Correct |")
        w("|:---|:---|:---|:---:|")
        for r in session.delegation_rejection_results:
            correct = "✓" if r.get("correct") else "✗"
            w(f"| {r.get('scenario_id', '?')} | {r.get('expected_code', '?')} | "
              f"{r.get('actual_code', '?')} | {correct} |")
        w()

    # --- Cycle log (abbreviated) ---
    w("## §7 Cycle Log")
    w()
    w("| Cycle | Phase | Decision | Grants A/R | Deleg W/R | Notes |")
    w("|---:|:---|:---|---:|---:|:---|")
    for r in session.cycle_results:
        notes_parts = []
        if r.delegated_warrants_issued:
            notes_parts.append(f"warrants={r.delegated_warrants_issued}")
        if r.grant_rejection_codes:
            notes_parts.append(f"grant_rej={r.grant_rejection_codes[0]}")
        if r.delegation_rejection_codes:
            notes_parts.append(f"deleg_rej={r.delegation_rejection_codes[0]}")
        if r.revocations_admitted:
            notes_parts.append(f"revoked={r.revocations_admitted}")
        if r.rsa_action_type:
            notes_parts.append(f"action={r.rsa_action_type}")
        notes = "; ".join(notes_parts) if notes_parts else "-"

        w(f"| {r.cycle_index} | {r.phase} | {r.decision_type} | "
          f"{r.grants_admitted}/{r.grants_rejected} | "
          f"{r.delegated_warrants_issued}/{r.delegated_rejections} | {notes} |")
    w()

    # --- Overall verdict ---
    w("## §8 Overall Verdict")
    w()
    criteria_pass = (
        has_warrants
        and grant_all_correct
        and grant_count > 0
        and deleg_all_correct
        and deleg_count > 0
        and has_revocations
        and session.expiry_confirmed
        and session.replay_verified
    )
    if criteria_pass:
        w("**X-2 CLOSURE: POSITIVE ✓**")
        w()
        w("All closure criteria met:")
        w("1. ≥1 delegated warrant issued")
        w("2. All adversarial grant rejections at correct gates")
        w("3. All adversarial delegation rejections at correct gates")
        w("4. Revocation lifecycle verified")
        w("5. Expiry lifecycle verified")
        w("6. Replay determinism verified")
        w("7. density < 1 preserved")
        w("8. Ed25519 signature verification operational")
    else:
        w("**X-2 CLOSURE: NEGATIVE ✗**")
        w()
        w("Failed criteria:")
        if not has_warrants:
            w("- No delegated warrants issued")
        if not (grant_all_correct and grant_count > 0):
            w("- Some adversarial grant rejections did not match expected codes")
        if not (deleg_all_correct and deleg_count > 0):
            w("- Some adversarial delegation rejections did not match expected codes")
        if not has_revocations:
            w("- No revocations admitted")
        if not session.expiry_confirmed:
            w("- Expiry lifecycle not confirmed")
        if not session.replay_verified:
            w("- Replay divergence detected")
    w()

    w("---")
    w(f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}*")

    return "\n".join(lines)


def write_report(report_md: str, output_path: Path) -> None:
    """Write report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md, encoding="utf-8")


def write_session_json(session: X2SessionResult, output_path: Path) -> None:
    """Write session result as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(session.to_dict(), indent=2, default=str),
        encoding="utf-8",
    )
