# RSA X-3 — Follow-Up Questions (Round 7)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A — Round 7
**Source:** Answers from Round 6 (`docs/X-3/answers-round6.md`)

---

## AQ — Boundary State Verification Codes

AN2 adds a new failure class: CycleStart's `identity_chain_*` and `overlay_hash` fields don't match replay-reconstructed state after activation. This is neither a signature mismatch nor one of the two `pending_successor_key` state codes from Round 5.

**AQ1.** Proposed: add `BOUNDARY_STATE_CHAIN_MISMATCH` for when CycleStart's `identity_chain_length`, `identity_chain_tip_hash`, or `overlay_hash` disagree with the harness-reconstructed post-activation state. This gives 4 boundary codes total:

| Code | Trigger |
|------|---------|
| `BOUNDARY_SIGNATURE_MISMATCH` | CycleCommit or CycleStart signature fails |
| `BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR` | No `pending_successor_key` in commit despite admitted succession |
| `BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR` | Non-null `pending_successor_key` without admitted succession |
| `BOUNDARY_STATE_CHAIN_MISMATCH` | CycleStart identity/overlay fields don't match reconstructed state |

Confirm, or fold the chain mismatch into one of the existing codes.

**AQ2.** This adds a 5th fault sub-session to X3-INVALID_BOUNDARY (Fault E: CycleStart with wrong `identity_chain_tip_hash` after a valid rotation). Should the family include this 5th sub-session, or is 4 sufficient?

---

## AR — Harness-to-Kernel State Handoff Contract

**AR1.** AO1 confirms Step 0 boundary activation runs at the harness level but modifies `InternalStateX3`. To confirm the handoff contract explicitly:

1. Harness loads `InternalStateX3` from prior cycle's committed state
2. Harness performs boundary verification + activation (Step 0): mutates `sovereign_public_key_active`, `prior_sovereign_public_key`, `pending_successor_key`, `suspended_grant_ids`, `identity_chain_length`, `identity_chain_tip_hash`
3. Harness passes the **post-activation** `InternalStateX3` to `policy_core_x3()`
4. `policy_core_x3()` returns `PolicyOutputX3` containing the **end-of-cycle** state
5. Harness signs CycleCommit over the end-of-cycle state, then signs CycleStart for next cycle

Is this the binding contract? If so, `policy_core_x3()` never sees pre-activation state and never needs to know a boundary transition occurred — it just processes a cycle with whatever sovereign key and suspension set it receives.

---

## AS — Convergence Declaration

**AS1.** With AN/AO/AP confirmed and the above two small items resolved, the binding decision set is:

1–14: As listed in Round 5 AM1
15: Boundary codes (4 total, per AQ1 if confirmed)
16: Frozen CycleCommitPayload v0.1 (with `overlay_hash`, per AN1)
17: Frozen CycleStartPayload v0.1 (with `overlay_hash` + `identity_chain_tip_hash`, per AN2)
18: `prior_sovereign_public_key` in InternalStateX3 for `PRIOR_KEY_PRIVILEGE_LEAK` detection (AJ1)
19: `verify_active_sovereign_signature()` shared helper (AJ2)
20: X3-INVALID_BOUNDARY uses separate sessions per fault (AK1)
21: One-cycle-delayed suspension at harness-level Step 0 (AO1)
22: Final `policy_core_x3()` signature with `pending_amendment_candidates` (AP1)

Confirm this is complete and implementation can begin, or flag any remaining gaps.

---

## End of X-3 Follow-Up Questions Round 7 (4 questions across 3 sections AQ–AS)
