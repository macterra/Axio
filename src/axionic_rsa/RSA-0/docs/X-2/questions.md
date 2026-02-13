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

---
---

# Follow-Up Questions (Round 2)

Generated from binding answers to Q1–Q60. These address tensions, implied commitments, and architectural gaps that emerged from the answers.

---

## O. Artifact Model vs Action Type (Critical — from Q2)

### Q61 [BINDING]
Q2's answer says to add a new action type `Delegate` (or `GrantTreaty`) to the closed action set. But the X-1 precedent shows that **AmendmentProposal is its own artifact type with its own admission pipeline** — it is NOT an ActionRequest with `action_type="ProposeAmendment"`. Amendments enter `policy_core_x1()` via a **separate parameter** (`amendment_candidates`), not via `CandidateBundle`.

TreatyGrant is structurally analogous to AmendmentProposal: a new artifact type with its own admission pipeline (6T/7T/8C). Two options:

1. **Follow the amendment pattern:** TreatyGrant/TreatyRevocation are artifact types with their own pipeline and their own `treaty_permissions` model (analogous to `amendment_permissions`). No new action type needed. `policy_core_x2()` takes a `treaty_candidates` parameter. B stays at 4.

2. **Follow Q2's answer literally:** Add `Delegate` as an action type. The RSA submits an ActionRequest with `action_type=Delegate`. The kernel issues a warrant for that action, and the warrant authorizes the TreatyGrant admission. But this means the kernel issues a warrant whose "side effect" is admitting another artifact — a novel pattern with no precedent.

Which model applies? If option 1, then Q2's answer needs revision. If option 2, what exactly does the ExecutionWarrant for a `Delegate` action contain and authorize?

### Q62 [BINDING]
If option 1 from Q61 (amendment pattern): Does X-2 need a `treaty_permissions` section in the constitution, analogous to `amendment_permissions`? Structure would be:

```yaml
treaty_permissions:
  - id: "CL-PERM-DELEGATION"
    authority: "AUTH_DELEGATION"
    treaties:
      - "TreatyGrant"
      - "TreatyRevocation"
```

### Q63 [BINDING]
If option 1 from Q61: What new `DecisionTypeX2` values are needed? Following the X-1 pattern (`QUEUE_AMENDMENT`, `ADOPT`), candidates might be:

- `GRANT_TREATY` (treaty admitted and activated)
- `REVOKE_TREATY` (revocation admitted and applied)

Or are treaty artifacts silently admitted without a dedicated decision type, with the cycle still resolving to ACTION/REFUSE/EXIT for the RSA's own action?

### Q64 [BINDING]
If option 1 from Q61: What is the **priority ordering** between amendment adoption, treaty admission, and action selection within a cycle? X-1 established: ADOPT > QUEUE_AMENDMENT > ACTION. Where do treaty operations slot in?

Candidates:
1. ADOPT > GRANT/REVOKE_TREATY > QUEUE_AMENDMENT > ACTION
2. ADOPT > QUEUE_AMENDMENT > GRANT/REVOKE_TREATY > ACTION
3. Treaty admission is **non-preemptive** — it happens alongside action selection (both can occur in the same cycle)

### Q65 [CLARIFY]
If option 2 from Q61 (Delegate as action type): Adding `Delegate` to the closed action set changes **B from 4 to 5**. Current density = 4/(3×4) = 0.333. After adding AUTH_DELEGATION with Delegate permission: A=4, B=5, M=5 → density = 5/(4×5) = 0.25. Under density_upper_bound = 0.75 this is safe, but the change is non-trivial. Is this density recalculation acknowledged?

---

## P. Kernel Physics Tension (Critical — from Q16)

### Q66 [BINDING]
The spec states "Kernel physics remain unchanged" and "X-2 modifies policy space only." Q16's answer says "treat signature verification as a kernel primitive and freeze it," acknowledging this is a kernel physics extension.

Which is authoritative?

1. **Spec is authoritative:** Signature verification must live **entirely in policy space** (constitution-defined, not kernel-hardcoded). The kernel provides only SHA-256 hashing (existing primitive); Ed25519 verification is a policy-layer module loaded at runtime.

2. **Q16 answer is authoritative:** X-2 requires a kernel physics extension. The spec's "kernel physics unchanged" claim must be revised. Ed25519 verification becomes a frozen kernel primitive.

3. **Pragmatic middle:** Signature verification is implemented as a **frozen library** loaded by the kernel but not part of `kernel/src/` — analogous to a driver. Kernel physics are "unchanged" in that no existing primitives change, but a new primitive is added.

### Q67 [CLARIFY]
If option 3 from Q66: Where does `signature_verify.py` live? It's used by both kernel (admission) and replay. The Q37 answer says "shared implementation." But if it's a kernel primitive, it can't live in `kernel/src/rsax2/` (that's policy extension). Should it live at `kernel/src/crypto/` as a permanent frozen module?

---

## Q. Constitutional v0.3 Content (from Q1, Q2, Q4)

### Q68 [BINDING]
Answers to Q1, Q2, Q4, Q48 collectively require a v0.2 → v0.3 constitutional amendment that adds at minimum:

- `TreatyGrant` and `TreatyRevocation` to `artifact_vocabulary`
- `AUTH_DELEGATION` to `authorities`
- Treaty-related permissions (either `action_permissions` or `treaty_permissions`)
- Possibly: `Delegate` action type (if Q61 option 2)
- Possibly: `treaty_permissions` section (if Q61 option 1)
- Possibly: identity registry mapping `agent:<name>` → pubkey (from Q14)
- Possibly: scope enumerations for scope subset computation (from Q22)
- Ratchet entries for treaty-related fields (from Q57)

Should the v0.3 constitution be **designed and frozen first** (before any X-2 kernel code), or can kernel code and constitution evolve concurrently?

### Q69 [BINDING]
Does the v0.3 amendment need to pass through the **existing X-1 admission pipeline** (Gate 8B structural preservation, density check, ratchet check)? If yes:

- Adding a new authority (AUTH_DELEGATION) increases A.
- Adding Delegate as action type (if Q61 option 2) increases B.
- Adding treaty_permissions changes density inputs.

All of these must satisfy density_upper_bound ≤ 0.75 in the proposed constitution. Has this been verified?

---

## R. Coverage Monotonicity (from Q21)

### Q70 [BINDING]
Q21's answer says coverage is (action_type, scope_type) pairs **ignoring authority identity**. Given the current scope types — Notify:target, ReadLocal:file_path, WriteLocal:file_path, LogAppend:log_name — the total coverage space is exactly 4 pairs (one per action). Any TreatyGrant that delegates existing action types at existing scope types can **never inflate coverage** because the (action, scope_type) pairs already exist.

This means 8C.4 (coverage monotonicity) is **trivially satisfied for every valid grant** — it cannot reject anything that passes 8C.1 (closed action set).

Is this the intended behavior? If so, 8C.4 is pure defense-in-depth against future scope type expansion. If not, the coverage definition needs revision.

---

## S. Multi-Artifact Cycle Mechanics (from Q29, Q44)

### Q71 [BINDING]
Q29 confirms multi-artifact cycles. Currently `policy_core_x1()` takes separate lists for `action_candidates` and `amendment_candidates`, supplied by the host. X-2 adds treaty artifacts.

How do treaty artifacts enter the cycle?

1. **Host-injected:** The harness/host constructs `treaty_candidates: List[TreatyGrant | TreatyRevocation]` from the observation stream and passes them as a separate parameter to `policy_core_x2()`.
2. **RSA-produced:** The RSA's CandidateBundle can contain TreatyGrant artifacts alongside ActionRequests, and the kernel partitions them.
3. **External inbox:** Treaty artifacts arrive via a dedicated external channel (e.g., signed messages from other agents injected as observations).

Q41 says B is "an external entity whose signed requests are injected as observations." But TreatyGrants are issued by the **RSA itself** (option 1 or 2), while signed **ActionRequests** from B arrive externally (option 3). Are these two different entry paths?

### Q72 [BINDING]
In the same-cycle revocation test (Q44), the cycle must process both a TreatyRevocation and a delegated ActionRequest. The 5-step ordering is:

1. Artifact admission (TreatyGrant, TreatyRevocation, AmendmentProposal)
2. Revocation processing
3. Active treaty set recomputation
4. ActionRequest admission
5. Warrant issuance

Are treaty artifacts and ActionRequests admitted in **separate passes** (steps 1 and 4), or does "artifact admission" in step 1 include ActionRequest admission? If separate, then the RSA can submit a TreatyRevocation and an ActionRequest in the same cycle, and the revocation is guaranteed to take effect before the ActionRequest is evaluated.

---

## T. Citation Format and Rejection Codes (from Q31, Q32)

### Q73 [BINDING]
Q31 says ActionRequests cite TreatyGrants by id/hash in `authority_citations`. The current citation format uses URI schemes:

- `constitution:<hash>#<clause_id>`
- `authority:<hash>#AUTH_*`

What is the URI scheme for treaty citations?

Candidate: `treaty:<grant_hash>#<grant_id>`

### Q74 [DEFAULT]
Q32 introduces `GRANT_INACTIVE` as a new rejection code. Which enum does it belong to?

1. `AdmissionRejectionCode` (RSA-0 action rejection codes)
2. A new `TreatyRejectionCode` enum
3. Extend `RefusalReasonCode`

Default: Add to `AdmissionRejectionCode` since it occurs during ActionRequest admission.

---

## U. Scope Subset Mechanics (from Q22)

### Q75 [BINDING]
Q22's answer says scope subset uses "enumerated finite sets (exact match only)" for X-2. This means:

- A TreatyGrant's `scope_constraints` must be a **subset** of the grantor's scope values from an **enumerated** set.
- Glob/prefix patterns (e.g., `/data/*`) are **not** supported for scope subset computation in X-2.

Does the v0.3 constitution need to define an explicit **scope value enumeration** for each scope type? For example:

```yaml
scope_enumerations:
  file_path: ["/data/local", "/logs", "/telemetry"]
  target: ["user", "host"]
  log_name: ["cycle_log", "admission_trace", "treaty_trace"]
```

Or does "exact match" mean the grant's scope_constraints must **literally equal** a value that appears in the grantor's constitutional scope?

---

## V. Implicit Invalidation Semantics (from Q50, Q56, Q58)

### Q76 [BINDING]
Q50, Q56, Q58 all establish "immediate invalidation" — active grants become inactive when the constitution changes in ways that undermine them. When a grant is implicitly invalidated:

1. Is it removed from the active treaty set at the moment of amendment adoption?
2. Is a log event emitted (e.g., `{"type": "implicit_invalidation", "grant_id": "...", "reason": "grantor_authority_removed"}`)?
3. Does the invalidated grant remain in `treaties.jsonl` (for historical audit) while being absent from the active set?

### Q77 [DEFAULT]
Can implicit invalidation happen **mid-cycle** (if an amendment is adopted in step 1 and treaty recomputation in step 3 notices the invalidation)? Or only at cycle boundaries?

Default: Mid-cycle, following the 5-step ordering — adoption in step 1 feeds into treaty recomputation in step 3.

---

## W. Grantor Authority Validation (from Q34)

### Q78 [BINDING]
Q34's answer catches forbidden actions at 8C.1. But what about actions that **are in the closed set** but the **grantor doesn't hold**?

Example: AUTH_TELEMETRY has {LogAppend, Notify}. A TreatyGrant from AUTH_TELEMETRY tries to delegate {ReadLocal}. ReadLocal is in the closed set (passes 8C.1) but AUTH_TELEMETRY doesn't hold it.

Which gate catches this?

1. 8C.3 (scope monotonicity — ReadLocal scope ⊄ grantor scope because grantor has no ReadLocal scope)
2. 8C.4 (coverage — new (ReadLocal, file_path) pair the grantor doesn't have)
3. A new explicit check: "granted_actions ⊆ grantor's action_permissions" (not currently listed as a sub-gate)

If option 3, this is a **missing gate** that needs definition.

---

## X. Spec Text Overrides

### Q79 [CLARIFY]
Q30's answer (same-cycle revocation) explicitly contradicts spec §8 which says "becomes effective at next cycle boundary." The answer resolves in favor of the instructions' fail-closed ordering.

Should the spec text be considered superseded by the answers document, or does the spec need a formal revision before implementation?

### Q80 [CLARIFY]
Spec §0 says "X-2 modifies policy space only. Kernel physics remain unchanged." Q16/Q66 acknowledge that Ed25519 verification is new kernel physics. Should the spec be amended to say "Kernel physics extended with frozen cryptographic verification primitive" or similar?

---

**Round 2 total: 20 follow-up questions (Q61–Q80)**
**Cumulative total: 80 questions (46 BINDING, 20 CLARIFY, 14 DEFAULT)**

---
---

# Follow-Up Questions (Round 3)

Generated from binding answers to Q61–Q80. These address architectural consequences of the artifact-permission model decision, v0.3 constitution design, and cycle mechanics under multi-artifact admission.

---

## Y. Q2 Supersession (from Q61)

### Q81 [BINDING]
Q61's answer (Option 1: amendment pattern, no `Delegate` action type) **reverses** Q2's original answer (add `Delegate` action type). Q2 remains in the answers document as-written.

For implementation clarity: is Q2's answer formally **superseded** by Q61? If so, the binding record is:

- No new action type is introduced by X-2.
- B remains unchanged (4 action types).
- Delegation authority is expressed via `treaty_permissions`, not `action_permissions`.
- AUTH_DELEGATION grants treaty admission rights, not action execution rights.

Confirm this is the frozen architectural decision.

---

## Z. Cycle Decision Model (from Q63, Q64)

### Q82 [BINDING]
Q63 adds GRANT_TREATY and REVOKE_TREATY as decision types. Q64 establishes priority: ADOPT > GRANT/REVOKE_TREATY > QUEUE_AMENDMENT > ACTION.

In X-1, QUEUE_AMENDMENT **preempts** ACTION — if an amendment is queued, the action path is skipped entirely. Does GRANT_TREATY similarly **preempt** QUEUE_AMENDMENT and ACTION? Or can a cycle produce **both** a treaty decision and an action decision?

Options:
1. **Preemptive chain:** Each higher-priority decision type blocks all lower ones. A cycle that grants a treaty does nothing else.
2. **Treaty is non-preemptive:** Treaty admission happens in step 1, but the cycle still evaluates amendments (step 1 continued) and actions (step 4). The "decision type" reported is the highest-priority one, but lower-priority operations still execute.
3. **Parallel channels:** Treaty decisions and action decisions are independent outputs of the same cycle (cycle reports both `GRANT_TREATY` and `ACTION`).

### Q83 [BINDING]
If option 1 from Q82 (preemptive): A cycle that grants a treaty **cannot** also execute an action. But Q72 says ActionRequests are admitted in step 4 (after treaty admission in step 1). The 5-step ordering suggests both happen, not that one preempts the other.

How do you reconcile the 5-step ordering (which implies both can co-occur) with the preemptive priority (which implies only one outcome)?

### Q84 [BINDING]
The X-1 cycle returns a single `PolicyOutputX1` containing the decision type, selected action (if any), amendment traces, etc. X-2 needs to return treaty results too. Is the output:

1. A single `PolicyOutputX2` with fields for all channels (action, amendment, treaty),
2. Multiple output objects (one per channel), or
3. A `PolicyOutputX2` where the decision_type reflects the highest-priority operation, but all channels' results are included?

---

## AA. Distinguishing Delegated ActionRequests (from Q71)

### Q85 [BINDING]
Q71 says delegated ActionRequests arrive as external signed inputs via observation injection. The kernel must distinguish these from the RSA's own ActionRequests (which are unsigned, produced via CandidateBundle).

What determines whether an ActionRequest requires signature verification?

1. **Presence of `signature` field:** If the ActionRequest has a `signature` field, it's delegated; if not, it's the RSA's own.
2. **Authority citation scheme:** If `authority_citations` contains a `treaty:` URI, signature verification is triggered.
3. **Entry path:** RSA's own ActionRequests come via `action_candidates`; delegated ones come via a separate `delegated_action_candidates` parameter.
4. **Author field:** Delegated ActionRequests have `author != "reflection"` (or a new author value like `"delegate"`).

### Q86 [BINDING]
If delegated ActionRequests arrive via observation injection (Q41/Q71), they need to be **parsed from observations** before entering the admission pipeline. Currently, observations are raw typed data (Observation objects with `observation_type` and `content`). What observation type carries a delegated ActionRequest?

Options:
1. New observation type: `"delegated_action_request"`
2. Delegated ActionRequests are wrapped in a new artifact type `DelegatedActionRequest` (distinct from `ActionRequest`)
3. The host/harness extracts them from the observation stream and passes them as a separate parameter to `policy_core_x2()`

### Q87 [CLARIFY]
The ActionRequest artifact currently has no `signature` field. Adding one changes the artifact schema. Does this require:

1. Adding an optional `signature` field to the existing ActionRequest definition (backward-compatible — unsigned requests omit it),
2. Creating a new artifact type `DelegatedActionRequest` with mandatory `signature`, or
3. Modifying the ActionRequest canonicalization to always produce the same hash regardless of whether `signature` is present (signature excluded from canonical form)?

Note: Q15 says "sign the canonicalized ActionRequest payload bytes (excluding the signature field)." This implies option 1 or 3 — signature is a field on ActionRequest but excluded from canonicalization.

---

## BB. Density Computation Extension (from Q19, Q61)

### Q88 [BINDING]
Q19 says A includes grantees and M includes treaty-derived pairs. The current `compute_density()` function in `constitution_x1.py` operates solely on `action_permissions` from the constitution YAML. Under X-2, density must be computed over the **effective authority resolution set** (constitution + active treaties).

This means `compute_density()` must accept the active treaty set as input. Is this:

1. A **new function** `compute_effective_density(constitution, active_treaties)` in X-2 code,
2. A **modification** of the existing `compute_density()` to optionally accept treaties, or
3. Two separate calls: `compute_density()` for 8B (amendment admission, constitutional only) and `compute_effective_density()` for 8C.7 (treaty admission, constitutional + treaties)?

### Q89 [CLARIFY]
When checking density at 8C.7 for a proposed TreatyGrant, is the density computed:

1. Over the **current** effective authority set (constitution + all active treaties + the proposed grant), or
2. Over the **constitutional** authority set only (constitution + proposed grant effect, ignoring other active treaties)?

Q25 says "incremental" — each grant checked against state including prior grants. This implies option 1 (full effective set). Confirm?

---

## CC. v0.3 Constitution Design Scope (from Q68)

### Q90 [BINDING]
Q68 says v0.3 must be designed and frozen first. The v0.3 delta is substantial:

1. `artifact_vocabulary` += TreatyGrant, TreatyRevocation (from Q1/Q48)
2. `authorities` += AUTH_DELEGATION (from Q4)
3. New section: `treaty_permissions` (from Q62)
4. New section: `TreatyProcedure` with `max_duration_cycles` (from Q62)
5. Scope enumerations for subset computation (from Q75)
6. Optional: identity registry for `agent:<name>` → pubkey (from Q14)
7. New ratchet entries for treaty fields (from Q57)
8. Constitution schema v0.3 to validate all of the above

Should the v0.3 design be a **formal deliverable** (like the v0.2 YAML + schema were for X-1) with its own review cycle? Or is it an implementation artifact produced during X-2 coding?

### Q91 [BINDING]
The v0.3 constitution must pass X-1's Gate 8B. Specifically:

- 8B.1 (cardinality): A ≥ 1, B ≥ 1 → still satisfied with AUTH_DELEGATION added (A increases, B unchanged)
- 8B.2 (wildcard): treaty_permissions must not contain `"*"` → easy to satisfy
- 8B.3 (density): Current M=4, A=3, B=4 → density=0.333. Adding AUTH_DELEGATION with no action_permissions entry: M stays 4, A stays 3 (only authorities in action_permissions count for density). Density unchanged.
- 8B.5 (ratchet): New sections (treaty_permissions, TreatyProcedure) are additions, not modifications of existing fields. Do **new sections** pass the ratchet check, or does 8B.5 only constrain fields that existed in v0.2?

Does the current X-1 Gate 8B code handle **new sections** that didn't exist in v0.2? Or will it reject v0.3 because it encounters unexpected fields?

---

## DD. Step 1 Ordering Within Governance Artifacts (from Q25, Q72)

### Q92 [BINDING]
Q72 confirms step 1 admits governance artifacts (AmendmentProposal, TreatyGrant, TreatyRevocation). Q64 says ADOPT > GRANT/REVOKE_TREATY > QUEUE_AMENDMENT.

Within step 1, what is the **sub-ordering** when multiple governance artifacts arrive in the same cycle?

1. First process all amendment adoptions, then all treaty admissions (grants before revocations), then queue new amendments. (Matches Q64 priority.)
2. Process all governance artifacts in canonical hash order (Q25's incremental rule), regardless of type.
3. Type-ordered: AmendmentProposal first, then AmendmentAdoption check, then TreatyRevocation, then TreatyGrant. (Ensures revocations before grants within the same cycle.)

### Q93 [CLARIFY]
Q25 says "deterministic ordering by canonical artifact hash" for multiple same-cycle grants. Does this ordering also apply across artifact types? If an AmendmentProposal and a TreatyGrant both arrive in the same cycle, is their admission order determined by their canonical hashes?

---

## EE. Citation Resolver Extension (from Q73)

### Q94 [BINDING]
Q73 introduces the `treaty:<grant_hash>#<grant_id>` citation scheme. The existing citation resolver (used in Gate 2 for ActionRequests and in amendment admission) handles `constitution:` and `authority:` schemes.

Extending the resolver to handle `treaty:` citations means:

1. The resolver must access the **active treaty set** (not just the constitution).
2. Treaty citations are **cycle-dependent** (a treaty citation valid in cycle N may be invalid in cycle N+1 after expiry).
3. The resolver must verify the grant_hash matches the actual grant's hash.

Is the citation resolver a kernel component or a policy component? If it's kernel, this is another kernel extension (alongside Ed25519).

### Q95 [DEFAULT]
Can a TreatyGrant's own `authority_citations` use the `treaty:` scheme (citing another treaty as justification)? Or must TreatyGrant authority citations be exclusively `constitution:` / `authority:` schemes?

Default: TreatyGrant citations must be constitutional only (no treaty-citing-treaty), since depth ≤ 1 means only constitutional authorities can issue grants.

---

## FF. Schema Impact on ActionRequest (from Q87)

### Q96 [BINDING]
Adding an optional `signature` field to ActionRequest changes the v0.2 schema's `ActionRequest` definition. This schema is frozen under `artifacts/`. Options:

1. The ActionRequest schema change is part of the **v0.3 constitution schema** (since artifact_vocabulary is constitutional).
2. The ActionRequest schema change is part of the **treaty schema** (since signatures only matter for treaty-delegated requests).
3. A **new v0.3 artifact schema** is created alongside the constitution schema, defining all artifact types including the updated ActionRequest.

### Q97 [BINDING]
The current `to_dict_for_id()` method on artifacts produces the canonical form used for hash computation. If `signature` is added to ActionRequest, it must be **excluded** from `to_dict_for_id()` (per Q15). Does the existing canonicalization infrastructure support field exclusion, or does a new mechanism need to be built?

---

## GG. Implicit Invalidation Trigger Chain (from Q76, Q58)

### Q98 [BINDING]
Q58 says a tighter density_upper_bound retroactively invalidates grants. But density depends on the **full effective authority set** (Q19). If invalidating one grant changes the density, that might bring another grant back under the threshold. Is invalidation:

1. **All-at-once:** Recompute density over constitution-only. Any grant that would push density above the new bound when re-added is invalid. (Order-independent.)
2. **Greedy:** Remove grants one-at-a-time (oldest first? highest density contribution first?) until density is under the new bound. (Order-dependent — nondeterministic unless tie-broken.)
3. **Total:** If the new density_upper_bound is violated by the current effective set, **all** active grants are invalidated. (Nuclear option — simple but harsh.)

### Q99 [CLARIFY]
Q50 says grants are invalidated when the grantor authority is removed. Q56 says grants are invalidated when delegation permission is removed. Q58 says grants are invalidated when density_upper_bound tightens. Are there any **other** implicit invalidation triggers? Comprehensive list needed for implementation.

Candidates:
- Grantor authority removed from constitution ✓ (Q50)
- Delegation permission removed ✓ (Q56)
- density_upper_bound tightened below current effective density ✓ (Q58)
- Granted action type removed from closed action set?
- Scope enumeration narrowed below grant's scope_constraints?
- treaty_permissions section removed entirely?

---

**Round 3 total: 19 follow-up questions (Q81–Q99)**
**Cumulative total: 99 questions (55 BINDING, 25 CLARIFY, 19 DEFAULT)**

---
---

# Follow-Up Questions (Round 4)

Generated from binding answers to Q81–Q99. These address consequences of the non-preemptive multi-channel cycle model, cascade effects within a single cycle, host-side parsing obligations, v0.3 schema compatibility, and algorithmic properties of deterministic greedy pruning.

---

## HH. Multi-Channel Cycle Interactions (from Q82, Q83, Q84)

### Q100 [BINDING]
Q82/Q83 establish that a single cycle can execute **all channels**: ADOPT + GRANT/REVOKE_TREATY + QUEUE_AMENDMENT + ACTION. The 5-step ordering provides the sequencing.

Consider this scenario:
1. Step 1: Amendment adopted → new constitution removes AUTH_IO_READ
2. Step 3: Treaty recomputation → an active grant delegating ReadLocal from AUTH_IO_READ is implicitly invalidated
3. Step 4: A delegated ActionRequest from the grantee citing that grant arrives → REFUSE (GRANT_INACTIVE)

The delegated ActionRequest's refusal is a **cascade** from the amendment adoption in the same cycle. The ActionRequest author had no opportunity to observe the invalidation.

Is this acceptable (fail-closed, deterministic), or should the cycle **abort lower-priority steps** when adoption changes the authority model?

### Q101 [BINDING]
Q84 says PolicyOutputX2 includes all channel results. What is the **concrete field layout**?

Candidate structure:
```python
@dataclass
class PolicyOutputX2:
    decision_type: str                    # highest-priority headline
    cycle_index: int
    # Amendment channel
    amendment_adoption: Optional[AmendmentAdoptionRecord]
    amendment_queued: List[AmendmentAdmissionResult]
    # Treaty channel
    treaty_grants_admitted: List[TreatyAdmissionResult]
    treaty_revocations_admitted: List[TreatyRevocationResult]
    treaty_invalidations: List[TreatyInvalidationEvent]
    # Action channel
    selected_action: Optional[ExecutionWarrant]
    refusal: Optional[RefusalRecord]
    # Delegated action channel
    delegated_actions: List[DelegatedActionResult]
    # Traces
    admission_trace: List[AdmissionResult]
    treaty_trace: List[TreatyTraceEntry]
    amendment_trace: List[AmendmentAdmissionResult]
```

Is this roughly correct, or should channels be grouped differently?

### Q102 [CLARIFY]
With multi-channel cycles, what `decision_type` values are possible? The full set from Q63/Q64 plus X-1:

- `ADOPT` (amendment adopted)
- `GRANT_TREATY` (treaty granted — but what if multiple grants + a revocation + an action all happen?)
- `REVOKE_TREATY`
- `QUEUE_AMENDMENT`
- `ACTION`
- `REFUSE`
- `EXIT`

If a cycle adopts an amendment, grants a treaty, AND executes an action, the decision_type is `ADOPT` (highest priority). But the cycle also did treaty and action work. Is there a `decision_type` for "multiple things happened" or is it always the single highest-priority label?

---

## II. Host-Side Observation Parsing (from Q86)

### Q103 [BINDING]
Q86 says the host extracts delegated ActionRequests from the observation stream and passes them as `delegated_action_candidates`. This means the **host is responsible for:**

1. Identifying which observations contain delegated ActionRequests
2. Parsing them into ActionRequest objects
3. Passing them separately to `policy_core_x2()`

What observation format carries a delegated ActionRequest? Current observation types include `TIMESTAMP`, `BUDGET`, `ENVIRONMENT`, `USER_MESSAGE`, `HOST_MESSAGE`, `FILE_CONTENT`, `TOOL_RESULT`.

Options:
1. Add new observation type `DELEGATED_ACTION` with content being a serialized, signed ActionRequest
2. Add new observation type `TREATY_INBOX` that wraps one or more signed ActionRequests
3. Delegated ActionRequests are not observations at all; they are a separate input channel to the harness (like how treaty_candidates are separate from observations)

### Q104 [BINDING]
The host must validate delegated ActionRequest structure **before** passing to the kernel. How much pre-validation does the host do?

1. **Minimal:** Host only extracts bytes; kernel handles all validation (parsing, schema, signature)
2. **Structural:** Host parses JSON and confirms it's an ActionRequest shape, but kernel validates signature and authority
3. **Full:** Host validates everything including signature, rejecting invalid requests before they reach the kernel

The kernel should be the authority, so option 1 or 2 seem correct. But option 1 means the kernel must handle raw bytes, which it currently doesn't.

---

## JJ. Intra-Cycle Cascade Correctness (from Q92, Q100)

### Q105 [BINDING]
Q92 establishes step 1 sub-ordering: ADOPT → revocations → grants → queue amendments. An adoption in step 1 may change the constitution, which changes what treaty permissions, authorities, scope enumerations, and density bounds exist.

When processing treaty grants later in step 1 (after adoption), the grant admission pipeline (6T/7T/8C) must use the **post-adoption** constitution. This requires the pipeline to re-load or reference the **newly active constitution** mid-step.

Is this already handled by the X-1 adoption mechanism (which updates `active_constitution_hash` and `active_constitution` in state)? Or does X-2 need explicit "constitution reload" logic between adoption and treaty admission within step 1?

### Q106 [BINDING]
If a TreatyRevocation and a TreatyGrant for overlapping authority arrive in the same cycle:

1. Per Q92, revocations are processed before grants within step 1.
2. The revocation removes a grant from the active set.
3. The new grant is checked against the post-revocation active set (density recomputed).

Can the new grant "replace" a revoked grant in the same cycle? If the revoked grant held 2 (authority, action) pairs and the new grant holds 2 different pairs, density may be unchanged. Is this a valid pattern?

---

## KK. Gate 8B Compatibility with v0.3 (from Q91)

### Q107 [BINDING]
Q91 says Gate 8B must handle new sections (treaty_permissions, TreatyProcedure) as additive. The current v0.2 schema uses `additionalProperties: false` throughout. The v0.3 schema must list these new sections as recognized properties.

But Gate 8B's **code** (not just schema) performs structural checks. Specifically, 8B.5 (ratchet) compares v0.2 → v0.3 field values. Does the ratchet comparison code currently:

1. **Enumerate** known fields and compare them (safe: new fields are ignored), or
2. **Iterate** all fields and require each to be non-relaxing (unsafe: new fields have no v0.2 counterpart and would error)?

This is an implementation question that determines whether Gate 8B needs a code change for v0.3.

### Q108 [CLARIFY]
The v0.3 schema must be created alongside the v0.3 constitution. Should it be `rsa_constitution.v0.3.schema.json` (validating the full constitution including treaty sections)? Or should treaty-related sections have their own embedded sub-schema within the constitution schema?

---

## LL. Deterministic Greedy Pruning Properties (from Q98)

### Q109 [BINDING]
Q98 defines oldest-first greedy pruning when density_upper_bound tightens. The algorithm is:

1. Start with all non-density-invalid grants
2. Sort by (grant_cycle ASC, canonical_hash ASC)
3. Remove one at a time until effective_density ≤ new_bound

**Convergence guarantee:** Is it possible for this algorithm to fail to converge (i.e., removing all grants still leaves density above the bound)?

If the constitution-only density (no treaties) already exceeds the new bound, then removing all grants won't help — the constitution itself is invalid. But this case should be caught by X-1 Gate 8B before the amendment is adopted.

Can we assert: "If v0.3 passes Gate 8B, then the greedy pruning algorithm always terminates with effective_density ≤ new_bound"?

### Q110 [BINDING]
Greedy pruning removes **oldest** grants first. But a newer grant might contribute more to density (more actions, broader scope) than an older one. Should the pruning optimize for **maximum density reduction per removal** instead of oldest-first?

Options:
1. **Oldest-first** (Q98 answer) — simple, deterministic, lease-like. May remove more grants than necessary.
2. **Largest-density-contribution-first** — fewer removals, but more complex. Deterministic if tie-broken by (grant_cycle, hash).
3. **Doesn't matter** — the important thing is determinism and convergence, not optimality.

### Q111 [DEFAULT]
After greedy pruning, should the kernel attempt to **re-admit** grants that were previously invalidated but might now fit under the new density? Or is pruning strictly subtractive (once removed, gone until expiry cycle)?

Default: Strictly subtractive. Pruned grants remain invalid for the remainder of their duration. No re-admission.

---

## MM. Signature Field Canonicalization (from Q87, Q97)

### Q112 [BINDING]
Q87 adds optional `signature` to ActionRequest. Q97 says exclude it from `to_dict_for_id()`. The current ActionRequest canonicalization includes **all fields** in a deterministic order.

When a delegated ActionRequest is admitted, the kernel must:
1. Compute canonical form **without** `signature` → get bytes
2. Verify Ed25519 signature over those bytes using `grantee_identifier`'s public key
3. Compute artifact hash from the same canonical form (still without signature)

The signature field exists in the full ActionRequest object but is **never** part of the content-addressed identity. Is the `signature` field stored in logs alongside the artifact, or is it logged separately (e.g., in the admission trace)?

### Q113 [DEFAULT]
Can an RSA's **own** ActionRequest (non-delegated) contain a `signature` field? If so, should the kernel:

1. **Ignore** it (signature is only checked when treaty citations are present, per Q85)
2. **Reject** it as malformed (non-delegated requests must not have signatures)
3. **Accept** it silently (field is optional, presence without treaty citation is harmless)

Default: Option 1 — ignore. The signature field is inert unless treaty citations trigger verification.

---

## NN. Convergence Check: Are We Done?

### Q114 [CLARIFY]
After 4 rounds of Q&A (99 questions, 60 answers + 3 rounds of follow-ups), the open design surface has narrowed substantially. The remaining architectural decisions are:

1. PolicyOutputX2 concrete layout (Q101)
2. Observation format for delegated ActionRequests (Q103)
3. Host pre-validation level (Q104)
4. Gate 8B ratchet code compatibility (Q107)
5. Greedy pruning optimality (Q110)

None of these block the **v0.3 constitution design**, which Q68/Q90 established as the first deliverable.

**Proposed next step:** Freeze answers, then design and produce the v0.3 constitution YAML + schema as the first implementation artifact. Kernel code follows.

Is this the correct sequencing, or is there a prerequisite I'm missing?

---

**Round 4 total: 15 follow-up questions (Q100–Q114)**
**Cumulative total: 114 questions (63 BINDING, 29 CLARIFY, 22 DEFAULT)**

---
---

# Follow-Up Questions (Round 5 — Final)

Generated from binding answers to Q100–Q114. This round addresses a small number of remaining specifics needed to begin v0.3 constitution design. The architecture is converged; these are construction-level details.

---

## OO. Delegated Action Warrant Semantics (from Q101)

### Q115 [BINDING]
Q101 says "only one `execution_warrant` per cycle for the RSA's own selected action." Delegated ActionRequests from external entities also need warrants to authorize side effects (the prime directive: no side effect without an ExecutionWarrant).

When a delegated ActionRequest passes admission (valid signature, valid treaty citation, scope checks pass), does the kernel issue a separate `ExecutionWarrant` for it?

1. **Yes — one warrant per admitted delegated ActionRequest**, in addition to the RSA's own warrant. Multiple warrants per cycle are possible.
2. **No — delegated ActionRequests are evaluated but not warranted in X-2.** Only the RSA's own selected action gets a warrant. Delegated actions are "pre-approved" but execution happens externally.
3. **Yes, but capped at one total warrant per cycle** (either the RSA's own action OR one delegated action, not both).

If option 1: the `execution_warrant` field in PolicyOutputX2 becomes a list. If option 3: delegated and RSA actions compete for the single warrant slot.

### Q116 [BINDING]
If delegated ActionRequests receive warrants (Q115 option 1 or 3): who **executes** the warranted action? The RSA's executor (host) runs the RSA's own warranted actions. But a delegated action comes from an external entity.

Options:
1. The RSA's host executes **all** warranted actions (including delegated ones). The external entity never directly acts; they merely request the RSA to act on their behalf.
2. The warrant is returned to the external entity (via observation response or similar), and the external entity executes independently.
3. Delegated warrants are logged but execution is out-of-scope for X-2. The kernel proves admission/authorization; execution is left to the deployment layer.

### Q117 [CLARIFY]
If delegated actions don't receive warrants (Q115 option 2): what is the observable outcome of a successfully admitted delegated ActionRequest? A log entry saying "admitted" but no warrant issued? This seems to violate the prime directive: "No side effects without a kernel-issued ExecutionWarrant."

Or does "no side effect" mean the delegated entity's proof of authorization IS the TreatyGrant + signed ActionRequest admission record, and the warrant is implicit in the admission?

---

## PP. Ratchet Enumeration for v0.3 (from Q57, Q107)

### Q118 [BINDING]
Q57 says treaty-related fields must be under ratchet rules. Q107 says ratchet code enumerates known fields. For v0.3, the ratchet-constrained fields are:

**Existing (v0.2):**
- `cooling_period_cycles`: non-decreasing
- `authorization_threshold`: non-decreasing
- `density_upper_bound`: non-increasing
- `authority_reference_mode`: cannot relax

**New (v0.3 — need ratchet rules):**
- `max_treaty_duration_cycles`: should be non-increasing (can only tighten)?
- `treaty_permissions`: can permissions be removed but not added? Or vice versa?
- Scope enumerations: can values be removed (tighten) but not added (loosen)?

What are the monotonicity directions for each new v0.3 field?

### Q119 [DEFAULT]
Should `max_treaty_duration_cycles` be a required field in v0.3 (with a specific initial value), or optional (absent means unlimited)?

Default: Required, with an initial value (e.g., 100 cycles). Unlimited duration is operationally dangerous and should require explicit opt-in via amendment.

---

## QQ. Scope Enumeration Design (from Q22, Q75)

### Q120 [BINDING]
Q75 says v0.3 must define explicit finite enumerations for scope types. The current constitution's ScopeSystem defines scope **types** (file_path, target, log_name) but not scope **values**.

For treaty subset checking, the enumeration must list legal scope values. But the RSA's own actions use scope values from the IO allowlist (e.g., read_roots, write_roots). These are runtime-configured, not constitutional.

Options:
1. **Constitutional scope enumerations** that mirror the allowlist values (e.g., `file_path: ["/data/local", "/logs"]`). Tight binding but duplicates allowlist config.
2. **The scope enumeration IS the IO allowlist** — treaty scope subset is checked against the allowlist roots, which are already constitutional (or at least frozen config).
3. **Abstract scope labels** (e.g., `file_path: ["read_zone", "write_zone", "log_zone"]`), with the allowlist mapping labels to concrete paths. Treaties delegate at the label level.

### Q121 [CLARIFY]
If scope values are enumerated in the constitution, they become subject to ratchet rules (Q118). Can scope enumerations be **expanded** via amendment (add new values — loosening), or only **contracted** (remove values — tightening)?

Adding new scope values could allow new treaty delegations. Removing scope values could invalidate existing grants (Q99 trigger 5). The monotonicity direction must be explicit.

---

## RR. Identity Registry (from Q14)

### Q122 [BINDING]
Q14 allows `agent:<name>` identifiers only if the constitution has an immutable registry mapping name → pubkey. Should the v0.3 constitution include such a registry?

Options:
1. **Yes** — add an `identity_registry` section mapping agent names to Ed25519 public keys. Required for `agent:` scheme support.
2. **No** — v0.3 uses only `ed25519:<hex_pubkey>` identifiers. Symbolic names are a future feature.
3. **Optional section** — present if needed, absent if not. Schema allows but does not require it.

For X-2's test suite, at least one grantee identity must exist. Is a hardcoded test keypair sufficient, or must the registry be constitutional?

### Q123 [DEFAULT]
If `agent:<name>` is not supported in v0.3, should the constitution schema explicitly **forbid** it (fail validation if encountered), or simply not define it (leaving it unrecognized)?

Default: Explicitly forbid — `grantee_identifier` must match the `ed25519:<hex>` pattern. Unrecognized schemes are schema errors.

---

## SS. Convergence Declaration

### Q124 [CLARIFY]
This is Round 5. The remaining questions (Q115–Q123) are construction-level: warrant semantics for delegated actions, ratchet directions for new fields, scope enumeration source, and identity format.

None of these introduce new architectural abstractions. All are resolvable by choosing the simpler option consistent with existing decisions.

After Q115–Q123 are answered, the Q&A phase should be **formally closed** and the frozen answers document should become the authoritative implementation addendum referenced in Q79.

Confirm or identify any remaining gap.

---

**Round 5 total: 10 follow-up questions (Q115–Q124)**
**Cumulative total: 124 questions (69 BINDING, 31 CLARIFY, 24 DEFAULT)**

---
---

# Q&A Convergence — Formal Close

**Status: CLOSED.** All 124 questions answered across 5 rounds. Q124 confirms no remaining architectural gaps.

## Convergence Evidence

| Round | Questions | New Abstractions Introduced |
|-------|----------:|:----------------------------|
| 1     | 60        | Full X-2 architecture: treaties, gates, scopes, density, identity, crypto |
| 2     | 20        | Artifact-pattern reversal (Q61), multi-channel cycles, treaty citations |
| 3     | 19        | PolicyOutputX2 layout, greedy pruning, implicit invalidation triggers |
| 4     | 15        | DELEGATED_ACTION observation type, Gate 8B ratchet enumeration |
| 5     | 10        | None — construction-level refinements only |

## Key Refinement from Round 5

Q115 upgraded `execution_warrant` from scalar to `execution_warrants: List[ExecutionWarrant]` with origin tags. This supersedes the single-warrant assumption in Q101. The PolicyOutputX2 layout is now:

- `decision_type`: single headline (highest-priority governance activity)
- `execution_warrants`: list of warrants (RSA's own + admitted delegated actions)
- Per-channel result fields (amendment, treaty, action admission details)

## Frozen Answers Addendum

The [answers.md](answers.md) document is now the **authoritative implementation addendum** per Q79. All 124 answers are binding on implementation. Where answers conflict with earlier answers, the later answer supersedes (explicitly: Q61 supersedes Q2, Q115 refines Q101).

## Next Steps (per Q114)

1. ~~Freeze Q&A answers~~ ✓
2. Design v0.3 constitution YAML (`rsa_constitution.v0.3.yaml`)
3. Create v0.3 JSON schema (`rsa_constitution.v0.3.schema.json`)
4. Create treaty type schema (`treaty_types.v0.1.schema.json` + SHA sidecar)
5. Implement X-2 kernel code under `kernel/src/rsax2/` and `kernel/src/crypto/`
6. Extend citation resolver for `treaty:` scheme
7. Build X-2 test suite and profiling harness

**Final count: 124 questions (69 BINDING, 31 CLARIFY, 24 DEFAULT) — 0 remaining open items.**