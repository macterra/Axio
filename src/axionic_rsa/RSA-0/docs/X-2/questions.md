# RSA X-2 Design Questions

**Phase:** X-2 — Delegation Without Sovereignty Leakage
**Status:** Pre-implementation Q&A
**Date:** 2026-02-12

Questions are grouped by domain. Each question is tagged with a priority:

* **[BINDING]** — answer determines implementation semantics; must be frozen before code
* **[CLARIFY]** — ambiguity or apparent conflict between spec and instructions; needs resolution
* **[DEFAULT]** — has an obvious default; confirmation requested

---

## A. Constitutional Prerequisites

### Q1 [BINDING]
The current constitution v0.2 has a **closed artifact vocabulary** of exactly 10 types (Observation, ActionRequest, ScopeClaim, Justification, CandidateBundle, ExecutionWarrant, RefusalRecord, ExitRecord, AmendmentProposal, AmendmentAdoptionRecord). X-2 introduces `TreatyGrant` and `TreatyRevocation`.

Must a v0.2 → v0.3 constitutional amendment (via X-1 machinery) be adopted **before** the kernel can admit treaty artifacts? Or does X-2 extend the kernel artifact vocabulary independently of the constitution's `artifact_vocabulary` list?

### Q2 [BINDING]
The current constitution defines **no delegation authority**. The five authorities are AUTH_TELEMETRY, AUTH_IO_READ, AUTH_IO_WRITE, AUTH_GOVERNANCE, AUTH_EXECUTION. None authorizes delegation.

Does X-2 require a constitutional amendment adding (a) a delegation action type and (b) an authority permitting its use? Or is delegation treated as a kernel-level capability outside the action_permissions model?

### Q3 [BINDING]
The X-2 spec (§5.1, sub-gate 8C.7) references **ε** (epsilon) — a density margin parameter defined "in the Constitution." The current v0.2 constitution has `density_upper_bound: 0.75` but no explicit ε field.

Options:
1. ε is a **new constitutional field** added via v0.2 → v0.3 amendment.
2. ε **is** the density_upper_bound (i.e., "density < 1 − ε" means "density < 1 − 0.25 = 0.75").
3. ε is a separate margin below density_upper_bound (i.e., effective treaty density must be < density_upper_bound − ε).

Which interpretation is intended?

### Q4 [CLARIFY]
AUTH_EXECUTION exists in the v0.2 authorities list but is **unmapped** — it has no action_permissions entry. Is AUTH_EXECUTION the intended anchor for delegation authority, or should a new authority (e.g., AUTH_DELEGATION) be created?

### Q5 [BINDING]
The current closed action set is {Notify, ReadLocal, WriteLocal, LogAppend}. The spec says `granted_actions must be strict subset of closed action set`. Does "strict subset" mean:

1. A **proper** subset (cannot delegate the entire action set), or
2. A **subset** (can delegate all four if grantor holds all four)?

---

## B. Repo Layout and Integration

### Q6 [CLARIFY]
Instructions §1 say "Extend the RSA-0 repo." However, X-2 docs live under `RSA-2/docs/`. Should the implementation:

1. Live entirely inside the existing `RSA-0/` tree (extending kernel, artifacts, etc.), or
2. Live under `RSA-2/` as a separate package importing from RSA-0, or
3. The instructions' "RSA-0 repo" just means the same git repo (`Axio`), and files go under `RSA-2/`?

### Q7 [DEFAULT]
Instructions list new files under `replay/src/` (treaty_loader.py, treaty_resolver.py, signature_verify.py). Current RSA-0 has no `replay/` directory — replay is built into the profiling harness. Should these be:

1. New modules under `kernel/src/rsax2/` (matching the rsax1 pattern), or
2. A standalone `replay/` directory as literally specified?

Default: follow the rsax1 pattern (`kernel/src/rsax2/`).

### Q8 [CLARIFY]
Instructions say the treaty schema goes at `artifacts/phase-x/treaties/treaty_types.v0.1.schema.json`. This is a **new frozen artifact**. Does it get its own SHA-256 sidecar file (`.sha256`) following the same pattern as the constitution schema?

---

## C. Gate Pipeline Architecture

### Q9 [BINDING]
The instructions (§5) describe treaty admission gates as "Gate 6 — Treaty Authorization Preconditions," "Gate 7 — Treaty Schema Validity," "Gate 8C — Delegation Preservation Checks." But the existing X-1 pipeline **already uses** Gate 6 (amendment_authorization) and Gate 7 (full_replacement_integrity) for amendments.

Are these:
1. **Shared** gates (6 and 7 apply generically to all artifact types, with type-specific sub-logic), or
2. **Type-specific** gates (amendments get gates 6A/7A, treaties get gates 6T/7T), or
3. **Sequentially numbered** (the instructions' "Gate 6" for treaties is actually a new gate numbered beyond 8B)?

### Q10 [BINDING]
For **regular ActionRequests** (not amendments, not treaties), the existing RSA-0 pipeline has gates 1–5. X-2 adds treaty-based authority resolution at ActionRequest admission time (§7, §9). Where in the existing gate pipeline does treaty authority resolution occur?

Options:
1. Modify Gate 2 (authority_citation) to also check active treaty grants.
2. Add a new gate (e.g., Gate 2T) after Gate 2 for treaty-sourced authority.
3. Treaty authority is resolved **before** Gate 2 by expanding the authority resolution set, so Gate 2 operates on the expanded set transparently.

### Q11 [CLARIFY]
Instructions §5 say treaty artifacts "pass through existing gates 0–5, then" enter the treaty-specific gates. But RSA-0 has **no Gate 0**. Gates start at 1 (completeness). Is "Gate 0" an error, or does it refer to basic artifact parsing (which is currently implicit)?

### Q12 [BINDING]
The instructions define Gate 8C sub-gates as 8C.1 through 8C.8, and the spec table (§5.1) adds 8C.9 (authority citation valid). The instructions also have Gate 8R for revocations.

For revocations, do they pass through Gate 8C first (and fail at steps that don't apply)? Or does the pipeline branch: TreatyGrant → 8C, TreatyRevocation → 8R, with no overlap?

---

## D. Cryptographic Identity and Signatures

### Q13 [BINDING]
No signature infrastructure exists in the current kernel. X-2 requires cryptographic signatures on delegated ActionRequests. What key algorithm and format?

Options:
1. Ed25519 (compact, deterministic, no randomness needed)
2. ECDSA (secp256k1 or P-256)
3. Left to implementer's choice within spec constraints

Default assumption: Ed25519.

### Q14 [BINDING]
What is the canonical form of `grantee_identifier`?

Options:
1. Raw hex-encoded public key (e.g., `"ed25519:abcdef1234..."`)
2. A symbolic name registered in the constitution (e.g., `"agent:bob"`)
3. Both forms permitted, with different verification paths

### Q15 [BINDING]
What **exactly** is signed? The full canonical ActionRequest JSON? A subset of fields? The artifact hash?

### Q16 [CLARIFY]
The spec says `grantee_identifier` must be "a closed canonical identifier type already supported by kernel physics." But the current kernel has **no identifier types** — only the Author enum (kernel/host/user/reflection). Does this mean:

1. A new identifier type must be added to kernel physics (violating kernel freeze), or
2. The identifier type is added to the **constitution** (policy-level), not kernel, or
3. The kernel already has content-addressed artifact IDs (SHA-256), and "supported by kernel physics" means using that hash infrastructure?

### Q17 [DEFAULT]
For signature verification, do we implement Ed25519 using:

1. Python's `cryptography` library (PyCA)
2. `nacl` / `pynacl` (libsodium binding)
3. Pure-Python implementation (no external deps, maximally replay-safe)

Default assumption: `cryptography` library (standard, audited).

### Q18 [CLARIFY]
Instructions §7 say signature verification must have "no time-based freshness checks." Does this mean:

1. Signatures have **no expiry** — a valid signature is valid forever (replay safety), or
2. Signatures may include a timestamp but verification ignores it, or
3. Signatures must not contain any temporal component at all?

---

## E. Density, Coverage, and Scope Computation

### Q19 [BINDING]
The current density formula is `M / (A × B)` where A = distinct authorities in action_permissions, B = action types, M = total (authority, action) pairs.

Under X-2, when computing effective density per-cycle:
1. Does **A** include grantees with active treaty grants?
2. Does **M** include treaty-delegated (grantee, action) pairs?
3. Does **B** remain the constitutional closed action set size (always 4)?

### Q20 [BINDING]
8C.4 defines **Coverage(X)** as the set of (action, scope) pairs authorized for authority X. How is "scope" represented in the coverage pair?

Current scope types per action:
- Notify: `target`
- ReadLocal: `file_path`
- WriteLocal: `file_path`
- LogAppend: `log_name`

Is Coverage over (action_type, scope_type) pairs, or over (action_type, specific_scope_value) pairs? The former is finite; the latter could be infinite.

### Q21 [BINDING]
8C.4 says reject if `Coverage(grantor ∪ grant_effect) > Coverage(grantor)`. This implies the grant **cannot add any new coverage pairs** — even within the grantor's existing scope. But the point of delegation is that a grantee gets authority the grantor already has. How can Coverage(grantor ∪ grantee) ever equal Coverage(grantor) if the grantee is a distinct authority?

Possible interpretations:
1. Coverage is measured **per-authority** (grantee coverage ⊆ grantor coverage, but the union is allowed to grow since grantee is a new authority).
2. Coverage is measured **globally** (total system coverage must not exceed what it was before the grant — meaning the grant only re-labels existing coverage).
3. Coverage counts **(action, scope_type)** pairs ignoring authority identity, so granting existing actions at existing scope types doesn't inflate coverage.

Which interpretation is correct?

### Q22 [BINDING]
8C.3 says `Scope(grant) ⊆ Scope(grantor)`. How is scope subset computed?

Example: Grantor has ReadLocal scope `file_path: ["/data/*"]`. Grant says `scope_constraints: {file_path: "/data/subset/*"}`. Is subset determined by:
1. String prefix matching (path containment)?
2. Exact equality only?
3. A lattice order defined in the constitution's ScopeSystem?

### Q23 [CLARIFY]
The density margin check (8C.7) uses `density >= 1 − ε` as the rejection threshold. The existing 8B check uses `density <= density_upper_bound`. Are these two separate checks, or does `1 − ε` replace `density_upper_bound` for treaties?

Example: If density_upper_bound = 0.75 and ε = 0.1, does a treaty-expanded density of 0.80 pass 8C.7 (since 0.80 < 0.90 = 1 − ε) but fail 8B-style check (0.80 > 0.75)?

---

## F. Treaty Lifecycle and Cycle Mechanics

### Q24 [BINDING]
Activation window: `current_cycle ∈ [grant_cycle, grant_cycle + duration_cycles - 1]`.

Is `grant_cycle` the cycle in which the TreatyGrant was **admitted**, or the **next** cycle boundary? The cycle ordering (§6) places artifact admission before warrant issuance, so a grant admitted in cycle N could theoretically take effect in the same cycle.

### Q25 [BINDING]
Can multiple TreatyGrants be admitted in a single cycle? If so, is density recomputed **incrementally** (each grant checked against the state including all prior same-cycle grants) or **batch** (all grants checked against pre-cycle state)?

### Q26 [BINDING]
Can multiple TreatyGrants delegate to the **same grantee**? If so, how do overlapping grants compose?

1. Union of granted_actions, intersection of scope_constraints
2. Each grant is independent — grantee gets the union of all active grants
3. Only one active grant per grantee permitted

### Q27 [BINDING]
If `revocable: false`, can the grant still **expire** via `duration_cycles`? Or does `revocable: false` mean both irrevocable AND non-expiring?

### Q28 [DEFAULT]
What is the maximum allowed `duration_cycles`? The spec says "finite and ≥ 1." Is there an upper bound (e.g., 1000 cycles, or the constitution's cooling period, or unlimited)?

Default assumption: No explicit upper bound beyond "finite integer > 0."

### Q29 [CLARIFY]
The cycle ordering says: (1) Artifact admission, (2) Revocation processing, (3) Active treaty set recomputation, (4) ActionRequest admission, (5) Warrant issuance.

Currently, the RSA-0/X-1 cycle processes a **single LLM response** containing a CandidateBundle with one ActionRequest. Does X-2 change this to allow **multiple artifacts per cycle** (e.g., a TreatyGrant and an ActionRequest in the same cycle from the same or different agents)?

### Q30 [BINDING]
Revocation "becomes effective at next cycle boundary" (§8) but the cycle ordering (§6) puts "Revocation processing" in step 2 of the **current** cycle. Which is it?

1. A TreatyRevocation admitted in cycle N takes effect in cycle N (same-cycle, since revocation processing comes after admission in the ordering).
2. A TreatyRevocation admitted in cycle N takes effect at cycle N+1 boundary.

The instructions §6 says "Same-cycle revocation must take precedence over warrant issuance," which implies interpretation 1.

---

## G. ActionRequest Admission Under Delegation

### Q31 [BINDING]
When an ActionRequest uses treaty-based authority, does it cite the TreatyGrant artifact by hash/ID in its `authority_citations`? Or does it cite the underlying constitutional authority, and the kernel resolves the treaty chain transparently?

### Q32 [BINDING]
If a delegated ActionRequest's signature is valid but the underlying TreatyGrant has **expired** by the time the ActionRequest is evaluated (step 4 in cycle ordering), what happens?

1. REFUSE with AUTHORITY_CITATION_INVALID (grant expired)
2. REFUSE with a new code (e.g., GRANT_EXPIRED)
3. The ActionRequest should never reach evaluation because the active treaty set was already recomputed in step 3

### Q33 [CLARIFY]
Does a delegated ActionRequest require **both** a signature AND standard authority_citations? Or does the signature replace the authority_citations field for treaty-sourced authority?

### Q34 [BINDING]
The spec says "Treaty authority never overrides constitutional prohibitions." If the constitution forbids an action type (e.g., it's in `forbidden_objectives`), but a TreatyGrant includes it in `granted_actions`, is this caught at:

1. 8C.1 (closed action set membership — the action wouldn't be in the closed set), or
2. A separate prohibition check, or
3. Gate 4 (constitution_compliance) during ActionRequest admission when the grantee tries to use it?

---

## H. Replay and Determinism

### Q35 [BINDING]
The instructions say "No global treaty cache allowed." Does this mean:

1. Active treaty set must be **recomputed from logs every cycle** (no memoization), or
2. In-memory state is allowed during execution but must be **reconstructible** from logs (i.e., replay rebuilds from scratch)?

### Q36 [DEFAULT]
Replay needs to verify signature determinism. Does the replay harness:

1. Re-verify all signatures from logged ActionRequests (checking they still pass/fail identically), or
2. Compare logged signature verification outcomes against recomputed outcomes?

Default assumption: Both — re-verify and compare.

### Q37 [CLARIFY]
The instructions say to add `treaty_loader.py`, `treaty_resolver.py`, `signature_verify.py` under replay. But the production kernel also needs treaty loading, resolution, and signature verification. Are these shared modules used by both kernel and replay, or separate implementations that must agree?

---

## I. Logging

### Q38 [DEFAULT]
Instructions list two new log files: `treaties.jsonl` and `treaty_trace.jsonl`. Current RSA-0 logs go to `logs/`. Do these new logs go to the same `logs/` directory?

Default: Yes.

### Q39 [CLARIFY]
`treaty_trace.jsonl` includes "signature verification outcome when relevant (ActionRequest admission trace)." Does this mean signature verification events are logged in **treaty_trace.jsonl** (treaty-focused) or in the existing **admission trace log** (action-focused)?

### Q40 [DEFAULT]
Current RSA-0 logs are structured with `cycle_id` as a top-level field. Do treaty log entries follow the same schema pattern?

Default: Yes, with `cycle_id`, `timestamp`, standard envelope fields.

---

## J. Testing and Profiling

### Q41 [BINDING]
Test §12 item 1 says "A grants Notify to B → B submits signed request → warrant issued → replay stable." Who is B? In the current system, there is only one agent (the RSA itself). Does X-2:

1. Introduce a **second agent** (even if simulated), or
2. Model B as the same agent using a different identity (key pair), or
3. Model B as an external entity whose signed requests are injected as observations?

### Q42 [BINDING]
Test §12 item 12 says "100+ grants with sparse scopes maintain determinism and enforce ε margin." Is this a **unit test** (synthetic grants) or a **production profiling run** (like X-1's 36-cycle session)?

### Q43 [DEFAULT]
Should the X-2 test suite follow the same pattern as X-1 (pytest, fixtures, parametrized scenarios)?

Default: Yes.

### Q44 [CLARIFY]
Test §12 item 9 says "Same-cycle revocation blocks pending delegated action." This requires at least two artifacts in one cycle (a TreatyRevocation and a delegated ActionRequest). How are multiple artifacts injected in a single cycle in the test harness? Mocked LLM responses containing multiple artifacts?

---

## K. Schema and Constitution Interactions

### Q45 [BINDING]
The treaty schema (`treaty_types.v0.1.schema.json`) is described as **frozen under `artifacts/`**. If it needs to evolve, does it follow X-1 amendment machinery (constitutional replacement) or a separate versioning path?

### Q46 [CLARIFY]
Gate 7 in the instructions says "Schema validation passes under frozen treaty schema." For treaty artifacts, is Gate 7 schema validation against the **treaty schema** only, or also against the **constitution schema**? Treaties aren't constitutions, so the constitution schema shouldn't apply — but the instructions don't make the boundary explicit.

### Q47 [BINDING]
The instructions mention `IdentifierType` and `ScopeConstraintType` in the treaty schema (§4). Neither type exists in the current schema. Are these:

1. New JSON Schema definitions within `treaty_types.v0.1.schema.json`,
2. References to types defined in the constitution schema, or
3. Placeholder names that should match existing scope system types?

### Q48 [BINDING]
The constitution's `artifact_vocabulary` is currently a closed list. Does the treaty schema define its own vocabulary, or must TreatyGrant/TreatyRevocation be added to the constitution's `artifact_vocabulary` via X-1 amendment?

This is related to Q1 but specific to schema enforcement.

---

## L. Boundary Conditions and Edge Cases

### Q49 [BINDING]
What happens if a TreatyGrant cites AUTH_EXECUTION (which exists in the constitution but has **no action_permissions mapping**)? Can an authority with zero constitutional action_permissions issue a valid TreatyGrant?

### Q50 [BINDING]
If the constitutional authority model is amended under X-1 to **remove** an authority that has active TreatyGrants, what happens to those grants?

1. They are implicitly invalidated (grantor authority no longer exists).
2. They remain active until expiry (vested rights model).
3. They must be explicitly revoked first (amendment with active grants is blocked).

### Q51 [BINDING]
Can a TreatyGrant be admitted during the X-1 cooling period for a pending amendment? If the amendment changes the authority model, the grant might be valid now but invalid under the pending constitution. Is there any interaction?

### Q52 [BINDING]
Zero-grant edge case: can a TreatyGrant have `granted_actions: []` (empty list)? The spec says `minItems=1`, but this should be confirmed — is an empty grant an error or a no-op?

### Q53 [DEFAULT]
Maximum number of active TreatyGrants at any time? Is there a budget analogous to `max_pending_amendments`?

Default assumption: No explicit cap; density check is the natural bound.

### Q54 [CLARIFY]
The spec says `delegation depth ≤ 1 from constitutional root`. Does this mean the depth of the edge from root to grantee is 1 (i.e., exactly one hop), or that the total graph depth is ≤ 1 (same thing for a tree, but different if multiple roots exist)?

### Q55 [BINDING]
Acyclicity check (8C.6): with depth ≤ 1 strictly enforced, cycles are impossible by construction (only constitutional authorities can grant, grantees can't re-grant). Is 8C.6 redundant defense-in-depth, or does it guard against a scenario not covered by 8C.5?

If it's pure defense-in-depth, should it still be a **separate gate** with its own rejection code, or folded into 8C.5?

---

## M. X-1 Interaction

### Q56 [BINDING]
Can an X-1 constitutional amendment be adopted that **removes** the delegation permission entirely (disabling future TreatyGrants)? If so, do existing active grants survive until expiry, or are they immediately invalidated?

### Q57 [CLARIFY]
The constitution's ratchet constraints (8B.5) enforce monotonic non-relaxation. Do treaty-related constitutional fields (e.g., ε, delegation permissions) fall under existing ratchet rules, or do they need new ratchet entries?

### Q58 [BINDING]
If a constitutional amendment changes `density_upper_bound` (non-increasing per ratchet), does the new bound apply to already-active TreatyGrants? Could a tighter bound retroactively invalidate an in-flight grant whose density was legal when admitted?

---

## N. Failure Mode Semantics

### Q59 [BINDING]
Instructions §13 say "Phase X-2 fails if delegation chain is possible." But testing can only demonstrate the **absence** of chains in tested scenarios, not impossibility. Is the standard:

1. No chain observed across all test scenarios (empirical), or
2. A formal argument (proof sketch) that the gate pipeline makes chains structurally impossible?

### Q60 [DEFAULT]
What constitutes a "replay divergence" for X-2 failure determination? Any of:

1. Different accept/reject decision on any artifact
2. Different signature verification outcome
3. Different active treaty set at any cycle boundary
4. Different warrant issuance set

Default: All of the above.

---

**Total: 60 questions (33 BINDING, 16 CLARIFY, 11 DEFAULT)**
