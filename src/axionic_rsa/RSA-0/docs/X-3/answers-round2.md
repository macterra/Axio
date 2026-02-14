Below are **binding answers** for Round 2 (Q–W). I’m keeping everything consistent with the X-3 v0.1 spec + instructions + Round-1 bindings: **Constitution v0.3 frozen, kernel verifies only, harness signs, deterministic replay, no new authority semantics.**

---

# Q — Genesis Artifact & Overlay

**Q1. Is `genesis_artifact_hash` self-referential?**
No. Do **not** put a self-hash inside the artifact. That’s pointless and brittle.

Define:

* `genesis_artifact_hash = SHA256(JCS(genesis_artifact_without_hash_field))`

So the stored hash is the hash of the canonical artifact **excluding** the `genesis_artifact_hash` field. (Same pattern as “sign payload excludes signature.”)

**Q2. One canonical genesis key or per-family genesis?**
One canonical genesis identity across all X-3 sessions.

Rationale: “Genesis” is an anchor, not a scenario parameter. Families vary rotation schedules and delegation regimes, not who the sovereign starts as.

Implementation: derive genesis keypair from a pinned constant seed `X3_GENESIS_SEED` (public key embedded in genesis artifact). Harness uses the same derivation to obtain the private key when it must sign CycleCommit/CycleStart.

**Q3. Overlay file format and location?**
Yes, with one adjustment: keep it JSON for canonicalization symmetry.

Use:

* `artifacts/phase-x/x3/x3_overlay.v0.1.json`

Contents include:

* `succession_enabled: bool`
* overlay clause table: `clauses: { "CL-SUCCESSION-ENABLED": {...}, ... }`
* overlay hash is `overlay_hash = SHA256(JCS(overlay))`

Log `overlay_hash` in `X3SessionStart`.

**Q4. Citation namespace for overlay?**
Use a separate namespace:

* `overlay:<overlay_hash>#<clause_id>`

Keep constitution citations as:

* `constitution:<constitution_hash>#<clause_id>`

Gate S2 resolves both against the **effective frame** but does not pretend they share a hash.

**Q5. Merge overlay into a single ConstitutionX3 object or separate namespace?**
Merge at runtime into an in-memory `EffectiveConstitutionFrame` for lookup convenience, **but preserve namespaces**.

So you get:

* one queryable index,
* but citations still retain origin (`constitution:` vs `overlay:`) for audit clarity and reason codes.

---

# R — Succession Admission Mechanics

**R1. Gate S2 at cycle 1?**
Cycle 1 uses the **initial frame loaded at session start** as the “prior boundary” snapshot:

* Constitution v0.3 baseline
* * X3 overlay v0.1

So: `S2_snapshot = frame_at_session_start`.

**R2. Where to store historical sovereign key set?**
Confirm (a): store on `InternalStateX3` as:

* `historical_sovereign_keys: set[str]`

Initialize with `{genesis_sovereign_public_key}`. O(1) lookup. Deterministic.

**R3. How are SuccessionProposal candidates provided to kernel?**
Confirm your recommendation: a dedicated parameter:

* `succession_candidates: List[SuccessionProposal]`

This prevents accidental embedding inside generic action candidates and keeps ordering deterministic.

**R4. Self-succession and state mutation?**
Self-succession is a complete lineage no-op:

* no set mutation
* no counter mutation
* no pending_successor_key set
* no suspension triggered

But it can still be admitted as an artifact (see U3). If admitted, it consumes the per-cycle uniqueness slot (see U2).

---

# S — Boundary Mechanics

**S1. Where are CycleCommit/CycleStart logged?**
Yes: make them the canonical payloads inside `x3_boundary_events.jsonl`.

Each boundary record includes:

* `cycle_commit_payload` + `cycle_commit_signature`
* `cycle_start_payload` + `cycle_start_signature`

Plus the summary fields you already listed.

No extra log stream required.

**S2. When does replay verify boundary signatures?**
Confirm (a): verify at **start of cycle N+1**, before any topological steps.

Ordering:

1. Load previous cycle end-state
2. Verify CycleCommit signature for N (under expected active key for N)
3. Apply boundary activation (consume pending_successor_key if present)
4. Verify CycleStart signature for N+1 (under derived active key for N+1)
5. Proceed with topological steps for cycle N+1

Fail closed.

**S3. What is `state_hash_prev` for the first cycle?**
Use the X-0E initial chain tip as `state_hash_prev` for cycle 1 start.

Concrete rule:

* `state_hash_prev` at cycle 1 start = `initial_state_hash` produced by X-0E initialization (whatever your frozen definition is—do not invent a new one for X-3).

**S4. Are commit/start records produced every cycle?**
Yes. Structural uniformity: every cycle produces:

* CycleCommit (signed by active sovereign for that cycle)
* CycleStart (signed by derived active sovereign for the next cycle)

Even when no succession occurs.

**S5. Does CycleStartPayload include pending_successor_key?**
No. Start payload should not include pending successor.

Start payload includes only:

* `cycle_id`
* `state_hash_prev`
* `sovereign_public_key_active` (expected active at start)
* `identity_chain_length`
* `kernel_version_id`

`pending_successor_key` is an end-of-cycle fact (commit-time), not a start-of-cycle input.

---

# T — Treaty Ratification Pipeline

**T1. Ratification gate structure?**
Confirmed with one addition (ordering determinism):

* **R0:** Schema validity (no extra fields; correct types)
* **R1:** Completeness → `INVALID_FIELD`
* **R2:** Signature verification under active sovereign → `SIGNATURE_INVALID`
* **R3:** Treaty exists and is **SUSPENDED** → `TREATY_NOT_SUSPENDED`
* **R4:** If `ratify=true`, reactivation must not breach density bound → `DENSITY_BOUND_EXCEEDED`

**T2. Must all suspensions be cleared before new grants?**
Yes. Binding rule from Round 1 stands:

* If `suspended_grant_ids` non-empty at the moment grants are evaluated, reject all new grants with `SUSPENSION_UNRESOLVED`.

So: successor may ratify/revoke across cycles; only once the suspended set is empty do new grants become admissible.

**T3. Ratifications after grants causes same-cycle deadlock — intentional?**
Not intentional. Fix ordering.

Ratifications must occur **before** grants.

Revised binding order fragment:

…
3 SuccessionProposal admission
4 pending_successor_key record (internal)
5 Treaty revocations
6 **Treaty ratifications**
7 Density repair (post-ratification)
8 **Treaty grants** *(allowed only if suspended set now empty)*
9 Density repair (post-grant) *(or merge with step 7 by making density repair a “checkpoint” after each treaty mutation class)*
…

To keep it simple: treat “density repair” as a checkpoint after treaty state changes. The key point: **ratification precedes any opportunity to grant**.

**T4. Ratification rejection codes?**
Confirm the proposed set:

* `INVALID_FIELD`
* `SIGNATURE_INVALID`
* `TREATY_NOT_SUSPENDED`
* `DENSITY_BOUND_EXCEEDED`

Additionally define:

* `SUSPENSION_UNRESOLVED` is for **grant admission**, not ratification.

**T5. Can successor ratify treaties created by prior sovereign?**
Yes. Ratification is explicitly the successor taking ownership. No authorization mismatch; the ratification signature is the only required authority.

---

# U — Self-Succession Boundaries

**U1. Does self-succession set pending_successor_key?**
No. Pending successor remains null for self-succession.

Signatures still happen every cycle regardless (S4). Self-succession does not require any special boundary machinery.

**U2. Does self-succession consume the per-cycle uniqueness slot?**
Yes. If a SuccessionProposal artifact is admitted (even no-op), that cycle has “used” succession. Any other SuccessionProposal in the same cycle is rejected with `MULTIPLE_SUCCESSIONS_IN_CYCLE`.

If you want a “no-op proposal does not consume slot” rule, that’s a semantic exception you don’t need. Keep it simple.

**U3. Is self-succession logged or silently dropped?**
Logged. It is a real admitted artifact with:

* `admitted=true`
* no pending_successor_key state change
* no chain increment
* no suspension

This preserves auditability and determinism.

---

# V — Kernel Module Design

**V1. Wrapper over X-2 engine or duplicate path?**
Wrapper.

`policy_core_x3` should:

* call into X-2 topological machinery for shared steps
* insert X-3-only steps at the defined hook points:

  * succession admission
  * boundary activation check (start-of-cycle)
  * treaty suspension/ratification handling

Avoid duplicating the entire pipeline; duplication will drift.

**V2. InternalStateX3 fields?**
Confirm with two adjustments:

Add:

* `overlay_hash: str` (session anchor)
* `genesis_artifact_hash: str` (anchor)
* `sovereign_public_key_genesis: str` (optional but useful)

Keep:

* `sovereign_public_key_active: str`
* `pending_successor_key: Optional[str]`
* `identity_chain_length: int`
* `identity_chain_tip_hash: str`
* `historical_sovereign_keys: set[str]`
* `suspended_grant_ids: set[str]`

**V3. Where does `X3_TOPOLOGICAL` constant live?**
Define it in `policy_core_x3.py`, but register it in the central dispatch (currently in X-2 policy core) via a small routing hook:

* if ordering mode is `X3_TOPOLOGICAL`, dispatch to `policy_core_x3`.

Do not import x3 into x2 deeply; keep a thin dispatch boundary to avoid cyclic deps.

**V4. Signature helpers: extend or rename?**
Extend with generic primitives, then wrap:

* introduce `sign_payload(payload_bytes, sk)` / `verify_payload(payload_bytes, sig, pk)`
* keep `sign_action_request` etc. as thin wrappers for backward compatibility
* add:

  * `sign_succession_proposal()`, `verify_succession_proposal_signature()`
  * `sign_cycle_commit()`, `verify_cycle_commit()`
  * `sign_cycle_start()`, `verify_cycle_start()`

Do not rename existing APIs during X-3. That’s churn.

---

# W — Ordering Clarifications

**W1. Where does amendment queuing fit?**
Amendment queuing is an input ingestion / artifact buffering concern; it does not belong as a topological execution step unless you model “proposal creation” as an in-kernel effect.

Binding answer:

* amendments (as artifacts) are evaluated at **Amendment adoption** step only.
* “queuing” is just “artifact appears in buffered inputs for cycle c.”

So you do not need a special “amendment queuing” step in the execution ordering.

If you insist on modeling it as a step for audit uniformity, place it immediately before warrant issuance, but it must not affect same-cycle adoption unless your system already permits same-cycle propose+adopt (most of your phases implicitly do not).

**W2. Can steps 3 and 4 merge?**
Yes. Implementation merges them:

* “succession admission” handler sets `pending_successor_key` as part of admission.

Step 4 remains a spec-level clarity label, not a separate function.

**W3. Warrant issuance: deferred or inline?**
Follow existing X-2D pattern:

* warrants are issued **inline** during RSA action evaluation and delegated action evaluation, because warrant contents depend on the action’s admissibility decision.

The “warrant issuance” step in the X-3 list should be interpreted as “warrant finalization/log flush,” not “compute warrants only here.”

Binding rule:

* action evaluation emits warrants immediately and deterministically;
* end-of-cycle commit records them in the execution trace.

---

## Summary of the only material corrections vs Round 1

1. **Ratifications must precede grants** (to avoid the structural impossibility of “clear suspensions then grant” in the same cycle).
2. Commit/start records are produced **every cycle**, logged in `x3_boundary_events.jsonl` as full payload+signature objects.

Everything else is confirmations or tightenings.
