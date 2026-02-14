Below are **final binding answers** for Round 3 (X–AC). I’m freezing choices to keep X-3 v0.1 implementable, deterministic, and non-semantic.

---

# X — Final Binding Ordering

## X1. Full binding ordering for `X3_TOPOLOGICAL`

Your proposed consolidated list is **almost correct**. Two corrections:

1. **Cycle-start boundary verification + activation must be Step 0** (before everything).
2. **“Density repair” should be treated as a deterministic checkpoint after each treaty-mutation class**, but you do not need two different algorithms; you need one function invoked twice.

**Binding ordering (Cycle c):**

0. **CycleStart boundary verification + activation**

   * Verify `CycleStartPayload(c)` signature under derived `sovereign_public_key_active(c)`
   * If `pending_successor_key` was set in cycle c−1 commit:

     * activate successor (set `sovereign_public_key_active`)
     * clear `pending_successor_key`
     * apply **treaty suspension** trigger (move ACTIVE → SUSPENDED)
     * enforce prior-key zeroing rule (state-level, not a step)
1. **Amendment adoption**
2. **Constitutional revalidation**
3. **SuccessionProposal admission**

   * If admitted and non-self: set `pending_successor_key` (in-cycle state)
4. **Treaty revocations**
5. **Treaty ratifications**

   * Multiple allowed; each must pass ratification gates
6. **Density checkpoint A** (post-revocation+ratification)
7. **Treaty grants**

   * Only if `suspended_grant_ids` is empty at evaluation time; else reject with `SUSPENSION_UNRESOLVED`
8. **Density checkpoint B** (post-grant)
9. **RSA actions** (warrants issued inline)
10. **Delegated actions** (warrants issued inline)
11. **CycleCommit construction + verification inputs**

* Compute end-state hash
* Harness signs `CycleCommitPayload(c)` under **active sovereign for cycle c** (the prior key if succession was only admitted this cycle)
* Kernel verifies commit signature deterministically during replay
* Persist commit record to `x3_boundary_events.jsonl`

**Do the two density checkpoints need to exist?**
Yes, as *checkpoints*, not as two distinct mechanisms. Reason: ratification can reactivate authority (affecting effective density) and grants can add new authority; both must be bounded **before any action evaluation**. The simplest deterministic model is “checkpoint after each treaty mutation class.”

If you want to compress, you may merge them only if you also forbid any grants in cycles that contain ratifications. That’s a semantic restriction you do not want. So keep both checkpoints.

## X2. Where does treaty expiry fit?

Implicit filtering, as in X-2D.

Binding rule: every query that computes “active grants” must use:

* `is_not_expired(cycle_id)`
* `not_revoked`
* `not_suspended` (for X-3)

No separate expiry step.

---

# Y — Composition Mechanics

## Y1. Refactor X-2D topological path vs duplicate vs hooks

Confirm **(a)**.

Refactor `_x2d_topological_path` into internal sub-step functions, then:

* X-2D path calls them in order (behavior unchanged).
* X-3 path composes them plus its new steps.

This avoids duplication and avoids callback complexity.

Concrete structure (suggested):

* `_step_amendment_adoption()`
* `_step_constitution_revalidation()`
* `_step_treaty_revocations()`
* `_step_treaty_grants()`
* `_step_density_checkpoint()`
* `_step_rsa_actions()`
* `_step_delegated_actions()`

X-3 adds:

* `_step_succession_admission()`
* `_step_treaty_ratifications()`
* `_step_cycle_start_boundary()`
* `_step_cycle_commit_recording()` (mostly harness-facing)

## Y2. Dispatch without circular imports

Confirm **(c)**.

Do not route X-3 through `policy_core_x2` at runtime.

* Harness calls `policy_core_x3()` when `cycle_ordering_mode == X3_TOPOLOGICAL`
* Harness calls `policy_core_x2()` when using X-2/X-2D modes

This avoids circular dependencies and matches the pattern you already use between phases.

---

# Z — Self-Succession vs. Boundary Records

## Z1. How does replay distinguish “self-succession admitted” from “no succession”?

Only via the **artifact admission trace** (and/or the artifacts component of the hash chain), not via boundary records.

That’s fine: boundary records exist to zipper signer custody; they are not the event log.

Self-succession is a no-op precisely because it produces no state delta.

## Z2. Should CycleCommit include `succession_admitted: bool`?

No. Keep CycleCommitPayload minimal and purely state-derived.

Auditability comes from:

* the admitted artifact list for the cycle
* the admission decision log
* `H_artifacts` / `H_admission` contributions

Adding `succession_admitted` is redundant and risks inconsistency (you’d be duplicating information already present in the committed log).

---

# AA — Genesis & Session Initialization

## AA1. Is `genesis_artifact_hash` stored inside the artifact or sidecar?

Inside the file as a convenience field, **but computed over the artifact with that field omitted**.

Verifier procedure:

1. Load genesis artifact JSON
2. Remove `genesis_artifact_hash`
3. Compute `SHA256(JCS(stripped_artifact))`
4. Compare with stored `genesis_artifact_hash`

Also store a sidecar `.sha256` if you want, but it’s optional.

## AA2. Does `kernel_version_id` change for X-3?

Yes. It must change whenever replay-relevant semantics change.

Define a new pinned identity, e.g.:

* `kernel_version_id = rsa-replay-regime-x3-v0.1`

This preserves the “Replay Regime Identity — pinned” prerequisite properly. X-3 adds boundary verification, sovereign identity fields, suspension state: replay semantics changed.

## AA3. Who signs CycleStart for cycle 1?

Genesis sovereign signs `CycleStartPayload(1)`.

Confirmed.

## AA4. Must genesis public key be logged in `X3SessionStart`?

Not required if the session logs:

* `genesis_artifact_hash`
* `overlay_hash`
* `constitution_hash`

That is sufficient. Logging the public key again is harmless but redundant. Binding choice: **log only the genesis artifact hash**.

---

# AB — Ratification Edge Cases

## AB1. If ratification rejected for density, does treaty remain SUSPENDED?

Yes. It remains SUSPENDED and may be retried in a later cycle after:

* revocations,
* expiry,
* other ratifications that free density headroom.

Reject code: `DENSITY_BOUND_EXCEEDED`.

## AB2. Multiple TreatyRatification artifacts in same cycle?

Yes. Multiple ratifications per cycle are allowed (for distinct treaty IDs), subject to deterministic ordering (lexicographic by `artifact_id` after canonicalization) and per-artifact gate checks.

Only SuccessionProposal has the “one per cycle” constraint.

## AB3. If a treaty expires while SUSPENDED, does it keep blocking?

No. Expiry must remove it from `suspended_grant_ids`.

Binding rule:

* At each cycle, when you compute the suspended set, drop any suspended grants that are expired at that cycle.

Reason: otherwise you can deadlock the successor permanently on an expired suspension.

---

# AC — Overlay & ConstitutionX3

## AC1. ConstitutionX3 subclass vs wrapper?

Use a wrapper:

* `EffectiveConstitutionFrame(constitution_v0_3, overlay_v0_1)`

This avoids contaminating the base constitution class and keeps overlay semantics clearly separable.

## AC2. Overlay clause structure?

Structured, matching constitution clause schema for uniform indexing:

Each overlay clause should include at minimum:

* `id`
* `text`
* `type` (e.g., `boolean_flag`, `procedure`, `invariant`)
* optional `params`

This keeps citation resolution uniform.

## AC3. Can overlay be amended via X-1?

No. Overlay is frozen for the entire session.

Amendments apply to the constitution state evolution, not to the profiling overlay. Treat the overlay as a harness-bound addendum required for X-3 enablement and clause references.

If you want amendable succession enablement, that’s a later constitution revision (v0.4+), not X-3 v0.1.

---

## Minimal “Freeze-Grade” Summary

* **Ordering:** Step 0 boundary verify/activate; ratify before grant; two density checkpoints.
* **Expiry:** implicit filtering + suspended expiry removal.
* **Composition:** refactor X-2 steps; harness calls X-3 entry point directly.
* **Self-succession:** visible only in admission trace; no commit flags.
* **Genesis:** hash stored inside artifact (computed with field omitted); new `kernel_version_id` for X-3.
* **Overlay:** JSON, structured clauses, separate namespace, frozen.

