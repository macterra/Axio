# RSA X-3 — Follow-Up Questions (Round 2)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A — Round 2
**Source:** Answers from Round 1 (`docs/X-3/answers.md`)

---

## Q — Genesis Artifact & Overlay

**Q1.** A1 specifies a Genesis artifact at `artifacts/phase-x/x3/genesis.v0.1.json` with `genesis_sovereign_public_key` and `genesis_artifact_hash`. Is `genesis_artifact_hash` the SHA-256 of the canonical artifact itself (self-referential hash, computed after all other fields are set), or a hash of some external anchoring data?

**Q2.** A1 says the genesis keypair is derived from a "pinned constant seed" (`X3_GENESIS_SEED`). Should every X-3 session use the same genesis key (one canonical genesis identity), or can different profiling families use different genesis keys (each derived from the family seed)? The answer mentions "reproducible across runs" suggesting one canonical key.

**Q3.** B1 introduces a "profiling constitution overlay" as a separate file. What is the file format and location? Proposed: `artifacts/phase-x/x3/x3_overlay.v0.1.yaml` containing `succession_enabled: true` and the `CL-SUCCESSION-*` clauses cited in B3. Its hash is logged in `X3SessionStart`. Confirm or adjust.

**Q4.** B3 says citations reference overlay clauses like `CL-SUCCESSION-ENABLED`, `CL-SUCCESSION-SINGLETON-LINEAGE`, `CL-SUCCESSION-RATIFICATION-REQUIRED`. How does citation resolution work for the overlay? In X-1/X-2, citations use the format `constitution:<hash>#<id>`. Should overlay citations use `overlay:<hash>#<id>`, or `constitution:<hash>#<id>` where the hash is the combined hash of v0.3 + overlay?

**Q5.** The X-2D profiling constitution was created by programmatically modifying the v0.3 YAML (adding `CL-PERM-DELEGATION-ACTIONS`), producing a single merged constitution object. Should the X-3 overlay follow the same pattern (merge into a single `ConstitutionX3` object where the overlay clauses are queryable through the normal citation index), or remain a separate file with its own resolution namespace?

---

## R — Succession Admission Mechanics

**R1.** D1 says Gate S2 uses the "end of prior cycle" constitutional frame. But what happens at cycle 1? There is no prior cycle. Does S2 use the initial constitutional frame (v0.3 + overlay as loaded at session start)?

**R2.** D2 says maintain a set of all historical sovereign keys and reject reuse. Where is this set stored? Options:
  (a) A field on `InternalStateX3` (e.g., `historical_sovereign_keys: set`).
  (b) Derived on-the-fly from the succession artifact log during admission.
Recommend (a) for O(1) lookup. Confirm.

**R3.** D4 says evaluate proposals in lexicographic order by `artifact_id`. How are `SuccessionProposal` candidates provided to the kernel? As a list parameter (like `treaty_grant_candidates`), or embedded within `action_candidates`? I recommend a dedicated `succession_candidates: List[SuccessionProposal]` parameter on `policy_core_x3()`.

**R4.** A4 says self-succession does not increment `identity_chain_length`. D2 says reject if `successor_public_key` already appeared in lineage "unless self-succession no-op case." Does self-succession add the key to `historical_sovereign_keys` again? If not, the set is unchanged. If yes, it's a redundant add. Clarify: self-succession should be a complete no-op on lineage state (no set mutation, no counter mutation)?

---

## S — Boundary Mechanics

**S1.** F1 defines `CycleCommitPayload` and F2 defines `CycleStartPayload` as harness-level records. Are these logged to `x3_boundary_events.jsonl`, or to a separate log? Instructions §14 already defines `x3_boundary_events.jsonl` with similar fields. Should commit/start payloads be the boundary event records themselves?

**S2.** E3/F4 says the harness signs and the kernel verifies. At what point during replay does the kernel verify boundary signatures? Options:
  (a) At the start of cycle N+1 processing (before any topological steps).
  (b) As a post-cycle validation after all cycle N+1 steps complete.
  (c) As a separate replay pass after all cycles are reconstructed.
Recommend (a) — verification at cycle start is the natural "start header" check. Confirm.

**S3.** F1's `CycleCommitPayload` includes `state_hash_prev`. For cycle 0 (the first cycle), what is `state_hash_prev`? The initial state hash from the X-0E chain (`SHA256(constitution_hash ‖ SHA256(kernel_version_id))`)?

**S4.** When no succession occurs in a cycle, are CycleCommit and CycleStart records still produced and signed? The boundary signature system seems designed for transitions, but structural uniformity (per F3) suggests every cycle boundary should have signed commit/start records. If yes, every cycle has a commit signed by the active sovereign and a start verified under the (unchanged) active sovereign.

**S5.** The `CycleCommitPayload` includes `pending_successor_key`. In non-succession cycles, this is null. The commit is signed by the active sovereign. Does the `CycleStartPayload` for the next cycle also need `pending_successor_key` (which would always be null, since it was consumed at activation)? Or is the start payload simpler?

---

## T — Treaty Ratification Pipeline

**T1.** G3 says TreatyRatification is kernel-level with its own admission gate. Define the gate structure. Proposed:
  - Gate R1: Completeness (required fields present)
  - Gate R2: Signature verification (signed by active sovereign)
  - Gate R3: Treaty exists and is SUSPENDED (not ACTIVE, not REVOKED)
  - Gate R4: Density check (if `ratify=true`, reactivation must not breach density bound)
Confirm or modify.

**T2.** G4 says new TreatyGrants are rejected with `SUSPENSION_UNRESOLVED` while suspended treaties exist. Does this apply only to the *successor's* grants, or also to ratification of old grants? I.e., can the successor ratify some treaties (clearing some suspensions) and then issue new grants (while other suspensions remain)? Or must *all* suspensions be cleared first?

**T3.** L5 answer places ratifications at step 7 (after revocations, before density repair). But G4 says grants are blocked while suspensions exist. Since grants are step 5 and ratifications are step 7, a cycle cannot both ratify and grant in the same cycle (grants would be rejected at step 5 because suspensions haven't been resolved at step 7 yet). Is this intentional? Or should ratifications come *before* grants (step 4.5)?

**T4.** TreatyRatification rejection codes — what codes should be used? Proposed:
  - `INVALID_FIELD` (missing/malformed fields)
  - `SIGNATURE_INVALID` (bad sovereign signature)
  - `TREATY_NOT_SUSPENDED` (treaty is ACTIVE or REVOKED or doesn't exist)
  - `DENSITY_BOUND_EXCEEDED` (ratify=true would breach bound)
Confirm or add codes.

**T5.** Can a TreatyRatification be submitted for a treaty that was created *before* the succession (i.e., by the prior sovereign)? This should be yes (that's the whole point), but confirm there's no authorization mismatch — the ratification is signed by the successor, who was not the original grantor.

---

## U — Self-Succession Boundaries

**U1.** C2/G7 answers establish self-succession as a complete no-op: no chain increment, no suspension, no ratification needed. But F3 says both CycleCommit and CycleStart signatures are still required (structural uniformity). Does self-succession produce a `pending_successor_key` value in kernel state (that equals the active key), or is `pending_successor_key` left null because it's a no-op? If null, the boundary activation step in Phase C has nothing to consume and the key doesn't change — but F3 says signatures still happen.

**U2.** If self-succession doesn't set `pending_successor_key`, does Gate S7 (per-cycle uniqueness) still consume a "slot"? I.e., can another (real) succession be proposed in the same cycle as a self-succession?

**U3.** Does self-succession produce any log artifacts at all (e.g., a SuccessionProposal with `admitted=true` in the trace), or is it silently dropped before admission?

---

## V — Kernel Module Design

**V1.** J2 proposes `kernel/src/rsax3/` with 5 modules. `policy_core_x3.py` will need to compose `policy_core_x2`'s topological path. Should `policy_core_x3` be a wrapper that calls into the X-2 engine for the non-succession steps (like X-2 composes X-1), or should it duplicate the full topological path with succession steps inserted?

**V2.** `InternalStateX3` will extend `InternalStateX2`. Proposed fields:
  - `sovereign_public_key_active: str`
  - `pending_successor_key: Optional[str]`
  - `identity_chain_length: int`
  - `identity_chain_tip_hash: str`
  - `historical_sovereign_keys: set`
  - `suspended_grant_ids: set`
Confirm or adjust.

**V3.** The `X3_TOPOLOGICAL` ordering mode constant — should it live in `policy_core_x2.py` (alongside `X2D_TOPOLOGICAL`) or in the new `policy_core_x3.py`? If in x3, the X-2 policy core needs an import or dispatch hook to route to x3 when the mode is set.

**V4.** Should `signature.py` be extended with succession-specific signing/verification helpers (e.g., `sign_succession_proposal()`, `verify_succession_signature()`, `sign_cycle_commit()`, `verify_cycle_commit()`), or should the existing generic `sign_action_request`/`verify_action_request_signature` be renamed to generic versions?

---

## W — Ordering Clarifications

**W1.** The L5 answer expands the ordering to 12 steps. Where does **amendment queuing** (proposing new amendments) fit? In X-2D, amendment queuing is not explicitly listed because X-2D doesn't propose amendments mid-session. But X-3 allows amendments (O2 confirms same-cycle amendments). Proposed: amendment queuing goes after ratifications (step 7.5) but before RSA actions (step 9). Confirm.

**W2.** The 12-step ordering has `pending_successor_key` record as step 4. Per E2, this is just a state delta from step 3. Can steps 3 and 4 be merged into a single "succession admission" step for implementation, with the step-4 semantics being an internal detail of step 3's handler?

**W3.** Does warrant issuance (step 11) cover warrants for RSA actions AND delegated actions, or only delegated? In X-2D, RSA action warrants are issued inline during step 7 (RSA actions). Clarify whether X-3 defers all warrant issuance to step 11, or follows X-2D's pattern of inline issuance.

---

## End of X-3 Follow-Up Questions (30 questions across 7 sections Q–W)
