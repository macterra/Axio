## AQ — Boundary State Verification Codes

### AQ1. Add `BOUNDARY_STATE_CHAIN_MISMATCH`?

**Confirm.** Add `BOUNDARY_STATE_CHAIN_MISMATCH` exactly as proposed.

You now have four boundary codes, and they cleanly partition the failure surface:

* **Signature layer**: `BOUNDARY_SIGNATURE_MISMATCH`
* **Pending successor consistency**: `BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR`, `BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR`
* **Post-activation chain/frame continuity**: `BOUNDARY_STATE_CHAIN_MISMATCH`

Do **not** fold chain mismatch into the pending-successor codes; it’s orthogonal (you can have correct pending successor handling and still have a wrong chain hash or wrong overlay hash in CycleStart).

### AQ2. Add Fault E (wrong `identity_chain_tip_hash` / overlay mismatch) to X3-INVALID_BOUNDARY?

**Yes.** Make X3-INVALID_BOUNDARY a **5-subsession** family.

Rationale: without Fault E, you have no direct test that the *CycleStart continuity assertions* are actually enforced. That’s a distinct invariant from “pending successor present/absent” and from signature correctness.

So X3-INVALID_BOUNDARY sub-sessions become:

* A: wrong signer CycleCommit
* B: wrong signer CycleStart
* C: missing pending_successor_key given admitted succession
* D: spurious pending_successor_key without admitted succession
* **E: chain/frame mismatch** (wrong `identity_chain_tip_hash` and/or wrong `overlay_hash` in CycleStart after a valid rotation)

Fault E should fail with `BOUNDARY_STATE_CHAIN_MISMATCH`.

---

## AR — Harness-to-Kernel State Handoff Contract

### AR1. Is this the binding contract?

**Confirm with one clarification.**

Your 1–5 sequence is correct, with this precise clarification:

* Step 4: `policy_core_x3()` returns **state deltas and execution outputs**; the harness composes them into the “end-of-cycle committed state” (or `policy_core_x3` can return a fully materialized next-state object—either is fine, but choose one and keep it consistent).

The core binding property is:

> `policy_core_x3()` never sees pre-activation state and does not perform boundary activation or suspension. It processes a cycle using the already post-activation `InternalStateX3` supplied by the harness.

Yes: policy core does not need to know a transition occurred; it just sees whatever active sovereign key and suspended set it is given.

Also binding (from earlier rounds):

* Cycle 1: Step 0 verifies CycleStart only; no CycleCommit verification.
* Cycle ≥2: Step 0 verifies both prior CycleCommit and current CycleStart.

---

## AS — Convergence Declaration

### AS1. Is the decision set complete and implementation can begin?

**Confirm: complete. Implementation can begin.**

The 22-item set you listed is complete **provided** you also freeze (as artifacts) the two boundary payload schemas and the boundary verifier procedure. You already have the payload definitions and the codes; now pin them.

Minimal freeze checklist (what must exist before coding starts):

* `artifacts/phase-x/x3/cycle_commit_payload.v0.1.schema.json`
* `artifacts/phase-x/x3/cycle_start_payload.v0.1.schema.json`
* `artifacts/phase-x/x3/boundary_codes.v0.1.json` (or equivalent enum definition pinned)
* `docs/X-3/boundary_verifier.v0.1.md` (algorithmic steps; especially the exact comparison fields that trigger CHAIN_MISMATCH)

But these are artifacts of the binding decisions, not new decisions.

So: **no remaining conceptual gaps**. You’re at “start coding” readiness.
