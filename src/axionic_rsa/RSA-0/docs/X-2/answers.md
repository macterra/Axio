# A. Constitutional Prerequisites

### Q1 [BINDING] — Constitution vocab vs kernel vocab

**Answer:** **Treaty artifacts MUST be added via X-1 constitutional amendment (v0.2 → v0.3) before admission.**
Treaties are **policy artifacts**, not kernel physics. If the constitution claims a closed `artifact_vocabulary`, the kernel must enforce it. Otherwise the constitution is decorative.

### Q2 [BINDING] — No delegation authority exists

**Answer:** **Yes, X-2 requires a constitutional amendment** that adds:

1. a new action type `Delegate` (or `GrantTreaty`) in the closed action set, and
2. explicit action_permissions granting `Delegate` to a specific authority.

Delegation is **not** a kernel-level capability outside action_permissions. That would be sovereignty leakage.

### Q3 [BINDING] — ε meaning vs density_upper_bound

**Answer:** **Option 2. ε is derived from density_upper_bound.**
Define:

* `density_upper_bound = D` (existing)
* `ε := 1 − D`
* Treaty gate enforces `effective_density ≤ D` (equivalently `< 1 − ε`)

No new constitutional field required.

### Q4 [CLARIFY] — AUTH_EXECUTION unmapped

**Answer:** **Do not use AUTH_EXECUTION as the delegation anchor. Create a new authority `AUTH_DELEGATION`** with an explicit mapping granting `Delegate`.
Unmapped authorities are inert and should stay inert.

### Q5 [BINDING] — “strict subset”

**Answer:** **Interpret as “subset” (not proper).**
A grant may delegate all 4 actions **if and only if** the grantor holds all 4 under the constitution and the other constraints (scope narrowing, density bound, etc.) still pass. “Proper subset” is arbitrary restriction and not structurally motivated.

---

# B. Repo Layout and Integration

### Q6 [CLARIFY] — RSA-0 vs RSA-2 tree

**Answer:** **Option 1: implement inside the existing RSA-0 tree** (same kernel, same harness).
X-2 is a kernel/policy extension, not a parallel product.

### Q7 [DEFAULT] — replay modules location

**Answer:** **Follow rsax1 pattern.** Put modules under something like `kernel/src/rsax2/` and import them from replay harness. Don’t create a new top-level `replay/` tree unless the repo already has that convention.

### Q8 [CLARIFY] — treaty schema SHA sidecar

**Answer:** **Yes.** Add `.sha256` sidecar for the treaty schema, same as constitution artifacts.

---

# C. Gate Pipeline Architecture

### Q9 [BINDING] — Gate numbering collision

**Answer:** **Option 2: type-specific gates under shared numbering.**
Implement as:

* Gates 1–5: common to all artifacts (parsing, canonicalization, schema presence where applicable, authority citation shape, etc.)
* Gate 6A/7A/8B: amendment-specific
* Gate 6T/7T/8C: treaty-specific
* Gate 8R: revocation-specific

Keep numeric alignment for reporting, but dispatch by artifact type.

### Q10 [BINDING] — Where treaty authority resolution occurs for ActionRequests

**Answer:** **Option 3.** Expand the authority resolution set **before** the authority-citation check, so Gate 2 operates transparently on the expanded set.

Ordering for ActionRequest admission should be:

1. Determine candidate authority sources (constitution + active treaties)
2. If treaty authority is needed → enforce signature first
3. Then run the usual authority citation validity gate against expanded sources

### Q11 [CLARIFY] — “Gate 0” reference

**Answer:** Treat “Gate 0” as **implicit parsing/canonicalization pre-gate**. Your actual gates start at 1; keep it that way.

### Q12 [BINDING] — Revocations through 8C?

**Answer:** **Branch.**

* `TreatyGrant` → 8C only
* `TreatyRevocation` → 8R only
  No overlap.

---

# D. Cryptographic Identity and Signatures

### Q13 [BINDING] — algorithm

**Answer:** **Ed25519.**
Deterministic verification, compact, ubiquitous, no nonce failure class.

### Q14 [BINDING] — canonical grantee_identifier form

**Answer:** **Option 3, but with a hard constraint:** allow both forms only if the constitution defines the mapping deterministically. Concretely:

* Prefer `ed25519:<hex_pubkey>` as the canonical form.
* Permit `"agent:<name>"` **only** if constitution contains an explicit immutable registry mapping name → pubkey.

### Q15 [BINDING] — what is signed

**Answer:** **Sign the canonicalized ActionRequest payload bytes (excluding the signature field).**
i.e., signature covers exactly the deterministic canonical JSON representation of the ActionRequest artifact (minus `signature`). Do **not** sign “a subset”; that creates semantic loopholes.

### Q16 [CLARIFY] — “supported by kernel physics” vs no identifier types

**Answer:** **Add identifier types at the policy layer, not kernel.**
Kernel physics can include “verify Ed25519 over bytes” as a primitive without introducing interpretive identity. The identifier *schema* and allowed prefixes live in the constitution/treaty schema. That does not violate “kernel physics frozen” if your kernel already supports pluggable verification as a fixed primitive. If it doesn’t, then X-2 *does* require a kernel upgrade, and you should admit that Phase X-2 is not purely “policy space.” (My recommendation: treat signature verification as a kernel primitive and freeze it.)

### Q17 [DEFAULT] — crypto library

**Answer:** Use **PyCA `cryptography`** if it’s already a dependency. Otherwise use `pynacl`. Avoid pure-Python.

### Q18 [CLARIFY] — no time-based freshness checks

**Answer:** **Option 1.** Signatures have **no expiry** semantics. Any temporal fields are either forbidden or ignored by verification. For maximal cleanliness: **do not include timestamps in the signed material**.

---

# E. Density, Coverage, and Scope Computation

### Q19 [BINDING] — density components under X-2

**Answer:** **Yes, yes, yes.**

1. **A includes grantees** with at least one active grant in the cycle.
2. **M includes treaty-derived (grantee, action) pairs.**
3. **B is the constitutional closed action set size** (4 in v0.2/v0.3 unless amended).

### Q20 [BINDING] — what “scope” means in coverage

**Answer:** Coverage uses **finite scope types**, not infinite values.
So pairs are `(action_type, scope_type)` (or `(action_type, scope_dimension)`), not `(action_type, concrete path)`.

### Q21 [BINDING] — coverage monotonicity paradox

**Answer:** **Interpretation 3.**
Coverage is computed **ignoring authority identity**. It is about *which kinds* of action+scope exist in the system, not who holds them. Delegation reassigns existing coverage; it must not introduce new coverage categories.

### Q22 [BINDING] — scope subset computation

**Answer:** **Option 3.** Subset is determined by an explicit **ScopeSystem lattice/order defined in the constitution**, not ad-hoc prefix matching.
If you don’t have that lattice yet, then for X-2 you must constrain scope constraints to **enumerated finite sets** (exact match only) until the lattice exists. Do not silently use prefix matching; that’s an interpreter.

### Q23 [CLARIFY] — density_upper_bound vs 1−ε

**Answer:** **Single check.** `1−ε` **is** `density_upper_bound`. Treaties must satisfy the same global density ceiling. No separate threshold.

---

# F. Treaty Lifecycle and Cycle Mechanics

### Q24 [BINDING] — grant takes effect same cycle?

**Answer:** **Same cycle.** `grant_cycle` = cycle of **admission**.
Because ordering already places treaty admission before ActionRequest admission in-cycle.

### Q25 [BINDING] — multiple grants per cycle and density recomputation

**Answer:** **Incremental.** Each admitted grant is checked against state including prior admitted grants **in that same cycle** (deterministic ordering by canonical artifact hash).

### Q26 [BINDING] — multiple grants to same grantee composition

**Answer:** **Option 2. Union of all active grants**, each independently scoped.
If overlaps occur, effective permission is the union. (Intersection would create implicit negotiation semantics.)

### Q27 [BINDING] — revocable=false and expiry

**Answer:** `revocable=false` means **cannot be revoked early**, but it still **expires** by `duration_cycles`. No perpetual grants in X-2.

### Q28 [DEFAULT] — max duration_cycles

**Answer:** No explicit upper bound beyond finite positive integer **unless** constitution sets one. (Recommended: add `max_treaty_duration_cycles` in v0.3 for operational sanity, but not required.)

### Q29 [CLARIFY] — multiple artifacts per cycle

**Answer:** **Yes.** X-2 requires multi-artifact cycles at least in tests. The harness must support an observation stream that can inject multiple artifacts (treaty + action) per cycle deterministically.

### Q30 [BINDING] — revocation effective timing

**Answer:** **Same-cycle effective** (interpretation 1).
If a revocation is admitted in cycle N, it is applied before warrant issuance in cycle N per the ordering. “Next boundary” language is superseded by the fail-closed ordering.

---

# G. ActionRequest Admission Under Delegation

### Q31 [BINDING] — what does ActionRequest cite?

**Answer:** It **cites the TreatyGrant** (by id/hash) in `authority_citations`.
Do not rely on implicit kernel inference. Explicit citation preserves auditability and replay.

### Q32 [BINDING] — expired grant at evaluation time

**Answer:** **REFUSE** because active treaty set is recomputed before ActionRequest admission. Practically it never reaches evaluation with an expired grant. If it does, return a dedicated code: `GRANT_INACTIVE`.

### Q33 [CLARIFY] — signature vs authority_citations

**Answer:** **Both required.**
Signature binds identity; `authority_citations` binds justification/permission source.

### Q34 [BINDING] — forbidden action delegated

**Answer:** Caught at **8C.1** if it’s outside the closed set.
If the action type is in the closed set but constitution prohibits it for that authority/scope, then it must be caught at **treaty admission** by the “grantor must have it” checks (scope monotonicity + authority citation validity). Don’t defer this to ActionRequest time.

---

# H. Replay and Determinism

### Q35 [BINDING] — “no global treaty cache”

**Answer:** **Option 2.** In-memory state during execution is allowed **if reconstructible** from logs. Replay rebuilds from scratch. No hidden persistence.

### Q36 [DEFAULT] — replay signature verification

**Answer:** Do both: **re-verify** signatures and **compare** against logged verification outcomes.

### Q37 [CLARIFY] — shared modules

**Answer:** **Shared implementation** used by both kernel and replay. One source of truth.

---

# I. Logging

### Q38 [DEFAULT] — logs dir

**Answer:** Yes, same `logs/`.

### Q39 [CLARIFY] — where signature outcomes logged

**Answer:** Log signature verification in the **ActionRequest admission trace** (action-focused).
Treaty trace can include references/aggregates, but keep the primary event where it occurs.

### Q40 [DEFAULT] — cycle_id field

**Answer:** Yes.

---

# J. Testing and Profiling

### Q41 [BINDING] — who is B?

**Answer:** **Option 3.** B is an external entity whose signed ActionRequests are injected as observations (“treaty inbox”). This preserves “one RSA” while exercising delegation.

### Q42 [BINDING] — 100+ grants test type

**Answer:** It’s a **profiling run** (integration/perf), not a unit test. Unit tests can cover correctness with smaller N.

### Q43 [DEFAULT] — pytest style

**Answer:** Yes.

### Q44 [CLARIFY] — multiple artifacts in a single cycle tests

**Answer:** Inject via the observation stream: one cycle contains multiple inbound artifacts (revocation + action). Do not rely on “one LLM bundle” for this; use a deterministic harness injection mechanism.

---

# K. Schema and Constitution Interactions

### Q45 [BINDING] — treaty schema evolution

**Answer:** **Separate versioning path under artifacts**, not X-1 constitutional amendment.
Treaty schema is a frozen kernel-facing contract. If it changes, you ship `treaty_types.v0.2.schema.json` + hash and update kernel to accept that schema version. Constitutional amendment is not the right mechanism for code contracts.

### Q46 [CLARIFY] — Gate 7 schema validation target

**Answer:** Treaties validate against **treaty schema only**. Constitution schema does not apply.

### Q47 [BINDING] — IdentifierType and ScopeConstraintType source

**Answer:** **Option 1.** Define them inside `treaty_types.v0.1.schema.json` as explicit JSON Schema defs. No cross-schema references.

### Q48 [BINDING] — constitution artifact_vocabulary interaction

**Answer:** Must add treaty artifact types to constitution’s `artifact_vocabulary` via X-1 amendment (same as Q1). Treaty schema doesn’t override constitutional vocabulary.

---

# L. Boundary Conditions and Edge Cases

### Q49 [BINDING] — grant citing unmapped AUTH_EXECUTION

**Answer:** **Invalid.** An authority with zero action_permissions cannot issue a valid TreatyGrant unless it is explicitly granted `Delegate` in the constitution.

### Q50 [BINDING] — amendment removes grantor authority with active grants

**Answer:** **Implicit invalidation** (Option 1).
Active grants are dynamically bounded by current constitution. If the grantor authority ceases to exist, the grant becomes inactive immediately (next recompute) and any dependent ActionRequests refuse.

### Q51 [BINDING] — grants during X-1 cooling period

**Answer:** Allowed. Pending amendments have **no effect** until adopted. Treaties are validated against the **active** constitution only.

### Q52 [BINDING] — empty granted_actions

**Answer:** **Forbidden.** Empty list is an error, not a no-op.

### Q53 [DEFAULT] — max active grants cap

**Answer:** No explicit cap; density bound is the cap.

### Q54 [CLARIFY] — depth meaning

**Answer:** Depth ≤ 1 means **exactly one hop from constitutional authority to grantee**. No multi-hop, no chains.

### Q55 [BINDING] — is acyclicity redundant?

**Answer:** It’s defense-in-depth. Keep it as a separate gate with its own rejection code. Redundancy here is cheap and clarifies failure attribution.

---

# M. X-1 Interaction

### Q56 [BINDING] — amendment removes delegation permission

**Answer:** Yes, possible. Existing active grants become **inactive immediately** upon adoption (dynamic binding to constitution). No vested rights model.

### Q57 [CLARIFY] — ratchet coverage for treaty-related fields

**Answer:** Treaty-related constitutional fields that affect safety envelope (density bound, delegation permission thresholds, max duration if added) must be included under ratchet monotonicity rules. If not already covered, add explicit ratchet entries in v0.3.

### Q58 [BINDING] — tighter density bound retroactively invalidates grants?

**Answer:** **Yes.** New bound applies immediately upon adoption; active treaty set recomputation drops any grants that would violate the new bound. No retroactive warrant undoing, only forward validity.

---

# N. Failure Mode Semantics

### Q59 [BINDING] — “chain is impossible” standard

**Answer:** Standard is **both**:

1. proof sketch (structural argument: treaty grants admissible only from constitutional authorities), and
2. tests demonstrating no accidental chain in implementation.

### Q60 [DEFAULT] — replay divergence definition

**Answer:** **All of the above** (1–4) are divergence.

---

## The one meta-point

If you accept the above, X-2 becomes implementable without “interpretation.” Every ambiguous place is now pinned to: **constitutional primacy + deterministic ordering + explicit citation + signature binding + dynamic recomputation**.

If you want, I can convert these answers into a **frozen “X-2 Implementation Semantics Addendum”** suitable to drop into your repo as `RSA-X2-SEMANTICS.v0.1.md` so the code has a single authoritative target.

Good. Round 2 is where the architecture stops letting you hand-wave. I’m going to **freeze** answers for **all BINDING** (Q61,62,63,64,66,68,69,70,71,72,73,75,76,78) and give crisp resolutions for the rest (Q65,67,74,77,79,80).

I’m also going to correct one earlier mistake of mine: treating “Delegate” as an action type was the wrong abstraction for X-2 given your artifact-first pipeline precedent.

---

# O. Artifact Model vs Action Type

### Q61 [BINDING]

**Answer: Option 1 (follow amendment pattern).**
TreatyGrant/TreatyRevocation are **artifact types** with their own admission pipeline (6T/7T/8C, 8R). **No new action type** is introduced. **B stays at 4.**

Delegation authority is expressed as **policy permission to admit treaty artifacts**, analogous to amendment permissions.

### Q62 [BINDING]

**Answer: Yes.** Add a constitution section `treaty_permissions`, analogous to amendment permissions.

Minimal structure (example):

```yaml
TreatyProcedure:
  density_upper_bound: 0.75            # reuse existing if you already have it globally
  max_duration_cycles: 1000            # optional but recommended

treaty_permissions:
  - id: "TPERM-DELEGATION"
    authority: "AUTH_DELEGATION"
    treaties:
      - "TreatyGrant"
      - "TreatyRevocation"
```

### Q63 [BINDING]

**Answer:** Add **DecisionTypeX2** values:

* `GRANT_TREATY`
* `REVOKE_TREATY`

Treaty decisions are **first-class outcomes** of a cycle, not silent side effects. The RSA’s own ACTION/REFUSE/EXIT remains, but treaty admission is a distinct decision channel (same pattern as X-1’s QUEUE/ADOPT).

### Q64 [BINDING]

**Answer: Ordering 1.**
`ADOPT > GRANT/REVOKE_TREATY > QUEUE_AMENDMENT > ACTION`

Reason: adoption changes the constitution hash, which changes treaty validity; treaties should be evaluated against the **post-adoption** constitution in the same cycle, before action selection.

### Q65 [CLARIFY]

Resolved by Q61: **no Delegate action type**, so **no B change**.

---

# P. Kernel Physics Tension

### Q66 [BINDING]

**Answer: Option 3 (pragmatic middle).**
Signature verification is implemented as a **frozen library used by the kernel**, with a fixed interface and deterministic semantics, but we do **not** treat it as “policy.” It is part of the executable substrate the kernel relies on.

Interpretation: kernel physics are “unchanged” only in the sense that **existing invariants don’t change**, but a **new primitive dependency** is introduced. Treat that as a kernel extension in governance terms.

### Q67 [CLARIFY]

Put signature verification in a permanent, shared, frozen module path, e.g.:

* `kernel/src/crypto/signature_verify.py` (or `kernel/src/primitives/ed25519_verify.py`)

Replay imports the same module. Do **not** place it under `rsax2/` if `rsax2/` is “policy extension” territory.

---

# Q. Constitutional v0.3 Content

### Q68 [BINDING]

**Answer:** v0.3 constitution must be **designed and frozen first**, because it defines:

* artifact vocabulary including treaties,
* treaty permission model,
* ε / density semantics,
* optional identity registry,
* scope enumerations if you adopt that restriction.

Kernel code can be written in parallel, but **the semantics must be frozen first**. Otherwise you’re encoding policy in code.

### Q69 [BINDING]

**Answer:** Yes, v0.3 must pass through the **existing X-1 admission pipeline** (8B constraints, density checks, ratchet checks).

Has density been verified? Not by me (I didn’t run your code). But structurally:

* Adding AUTH_DELEGATION increases A,
* Adding treaty_permissions does not necessarily change B/M unless it’s represented as action permissions.
  So it is likely safe under 0.75, but you must compute it in the same way Gate 8B computes it.

---

# R. Coverage Monotonicity

### Q70 [BINDING]

**Answer:** Yes, that is intended **for X-2**.
8C.4 becomes mostly defense-in-depth under the current finite scope-type model. It still matters if later you add new scope dimensions or action types, but for now it will rarely fire if 8C.1/8C.3/“grantor holds action” are correct.

Which leads to Q78: you need an explicit “grantor holds action” check, otherwise 8C.4 being trivial is dangerous.

---

# S. Multi-Artifact Cycle Mechanics

### Q71 [BINDING]

**Answer: Two entry paths, intentionally.**

* **Treaty artifacts:** RSA-produced (host supplies `treaty_candidates` to `policy_core_x2()`), derived from RSA’s own proposals (like amendments).
* **Delegated ActionRequests:** external inbox injection as observations (B is external), producing `delegated_action_candidates` that enter action admission with signature gating.

So yes: **treaties are internal governance artifacts; delegated actions are external signed inputs.**

### Q72 [BINDING]

**Answer:** Separate passes.

Step 1 “Artifact admission” covers governance artifacts (AmendmentProposal, TreatyGrant, TreatyRevocation).
Step 4 is specifically **ActionRequest admission** (including delegated requests).

This separation is what makes same-cycle revocation meaningful: revocation processed before ActionRequest evaluation.

---

# T. Citation Format and Rejection Codes

### Q73 [BINDING]

**Answer:** Use:

* `treaty:<grant_hash>#<grant_id>` for TreatyGrant citations
* `treatyrev:<rev_hash>#<revocation_id>` optional, but not required for authority justification

Primary authority citation in an ActionRequest should reference the **grant**.

### Q74 [DEFAULT]

Agree with default: add `GRANT_INACTIVE` to **AdmissionRejectionCode** (it occurs during ActionRequest admission).

---

# U. Scope Subset Mechanics

### Q75 [BINDING]

**Answer:** v0.3 must define explicit **finite enumerations** (or an explicit finite lattice) for each scope type used in treaty subset checks.

“Exact match” here means:

* grant scope values must be members of the enumerated set, and
* subset is computed as set inclusion over those enumerated atoms.

No globs. No prefixes. No interpretive matching.

---

# V. Implicit Invalidation Semantics

### Q76 [BINDING]

**Answer:**

1. Yes — removed from active set immediately upon constitution adoption and subsequent treaty recomputation.
2. **Yes — emit a log event** (append-only) recording implicit invalidation with reason code.
3. Yes — the historical treaty artifacts remain in `treaties.jsonl`; only the active set changes.

Add `treaty_invalidation.jsonl` or log into `treaty_trace.jsonl` with event type `IMPLICIT_INVALIDATION`.

### Q77 [DEFAULT]

Accept default: implicit invalidation can occur **mid-cycle** following the 5-step ordering (adopt in step 1, recompute in step 3).

---

# W. Grantor Authority Validation

### Q78 [BINDING]

**Answer: Option 3 — missing gate. Add it.**

Add sub-gate:

**8C.2b — Grantor Holds Actions**

Reject if:

```
granted_actions ⊄ EffectivePermissions(grantor)   (under active constitution)
```

This must be explicit. Don’t rely on scope monotonicity to imply it. You want a direct, auditable failure mode.

Rejection code: `GRANTOR_LACKS_PERMISSION`.

---

# X. Spec Text Overrides

### Q79 [CLARIFY]

Implementation should proceed under an **Answers Addendum** as the authoritative binding semantics *for this implementation*, but the spec should be updated before you call it “preregistration-ready.”

So: answers supersede for code **now**; spec revision required for publication/freeze.

### Q80 [CLARIFY]

Yes, amend spec language. Minimal change:

* Replace “kernel physics unchanged” with:

  > “Kernel physics unchanged except for the addition of a frozen, deterministic signature verification primitive used for treaty-bound delegated ActionRequests.”

If you don’t want to touch the spec, then the addendum must explicitly mark this as a controlled deviation.

---

## Net effect (what changed from Round 1)

* Delegation authorization is now **artifact-permission**, not **action type**.
* v0.3 constitution becomes a hard prerequisite, not optional scaffolding.
* Signature verification is acknowledged as a frozen primitive dependency.
* You add one missing gate: **grantor holds permission**.

That set is coherent, minimal, and implementable.
Locked. I’ll answer **all BINDING** (Q81,82,83,84,85,86,88,90,91,92,94,96,97,98) and resolve the rest (Q87,89,93,95,99) in a way that preserves: **artifact-first governance**, **deterministic replay**, **no hidden interpreters**, **constitutional primacy**.

---

# Y. Q2 Supersession

### Q81 [BINDING]

**Yes — Q2 is formally superseded by Q61. Frozen decision:**

* **No new action type** for delegation.
* **B remains 4**.
* Delegation authority is expressed via **`treaty_permissions`**, not `action_permissions`.
* `AUTH_DELEGATION` grants **treaty admission rights**, not action execution rights.

Treaty admission is an artifact pipeline, analogous to amendment proposals/adoption.

---

# Z. Cycle Decision Model

### Q82 [BINDING]

**Option 2 (non-preemptive execution, single reported decision type).**

* The cycle can process **multiple channels** (adoption, treaty ops, queuing amendments, actions) in one cycle per the 5-step ordering.
* The cycle reports **one `decision_type` = highest-priority event that occurred**, but lower-priority operations may still have occurred.

This preserves the ordering semantics without inventing “one thing per cycle” artificial scarcity.

### Q83 [BINDING]

Reconciliation: **priority is a reporting/summary precedence, not a control-flow preemption.**

The 5-step ordering is the actual control-flow.
Priority dictates:

* what `decision_type` is set to,
* how the cycle is interpreted externally,
* what is highlighted in the trace.

It does **not** skip lower steps.

### Q84 [BINDING]

**Option 3.** One `PolicyOutputX2` where:

* `decision_type` is the highest-priority operation that occurred,
* but the output includes **all channel results** (treaty results, amendment results, action selection/outcome, traces).

So: single object, multi-channel fields, single headline decision.

---

# AA. Distinguishing Delegated ActionRequests

### Q85 [BINDING]

**Option 2 is the trigger condition, with Option 1 as a consistency check.**

Rule:

* If `authority_citations` contains any `treaty:` URI, then **signature verification is mandatory**.
* If signature present without treaty citation, reject (or ignore) by policy: I recommend **reject** as malformed to prevent ambiguous semantics.

So the kernel does not infer delegation from “presence of signature” alone; it infers from **explicit treaty citation**.

### Q86 [BINDING]

**Option 3.** The host/harness extracts delegated ActionRequests from the observation stream and passes them as a separate parameter, e.g.:

* `delegated_action_candidates: List[ActionRequest]`

The observation stream can contain opaque “inbox messages,” but the kernel should not be in the business of parsing them. Keep the parsing in the harness layer to avoid embedding an interpreter into kernel logic.

(You still log the raw observation + extracted artifact bytes for replay.)

### Q87 [CLARIFY]

Choose **Option 1**:

* Add optional `signature` field to ActionRequest (backward compatible).
* Exclude `signature` from canonicalization/hashing.
* Signature verification uses the canonical bytes computed from the signature-excluded form.

No new artifact type.

---

# BB. Density Computation Extension

### Q88 [BINDING]

**Option 3. Two functions.**

* `compute_density(constitution)` for X-1 / Gate 8B checks (constitution-only).
* `compute_effective_density(constitution, active_treaties)` for X-2 / Gate 8C.7 checks (constitution + treaties).

Do not overload the original function; separation makes audits and failure attribution clean.

### Q89 [CLARIFY]

Confirm **Option 1**: compute 8C.7 density over:

* constitution
* all currently active treaties
* plus the proposed grant (incrementally, deterministic order)

This matches Q25 incremental semantics.

---

# CC. v0.3 Constitution Design Scope

### Q90 [BINDING]

**Formal deliverable.** v0.3 is a first-class artifact with:

* YAML (`rsa_constitution.v0.3.yaml`)
* schema (`rsa_constitution.v0.3.schema.json`)
* hash sidecars
* review cycle

It is not “produced during coding.” If you don’t freeze it, you will encode policy defaults in code.

### Q91 [BINDING]

Two parts:

1. **New sections are allowed** under X-1 ratchet rules, provided they do not weaken existing envelope constraints. Ratchet constrains *non-relaxation* of existing safety parameters, not “no new fields forever.”

2. The existing X-1 Gate 8B code must therefore be updated to:

* reject unexpected fields only if the schema rejects them, not because the gate logic is hardcoded to a v0.2 shape
* perform ratchet comparisons on the known fields, and treat new sections as *additive* unless explicitly forbidden

If current code would reject v0.3 for “unexpected fields,” that is a **schema enforcement bug**: the gate should validate against the frozen schema and then apply structural checks to recognized sections.

---

# DD. Step 1 Ordering Within Governance Artifacts

### Q92 [BINDING]

**Option 1, with deterministic intra-type ordering.**

Within step 1:

1. Apply any **amendment adoption** eligibility checks and adopt (ADOPT).
2. Process **treaty revocations** (admit + apply) before grants.
3. Process **treaty grants** (incremental, deterministic order by canonical hash within grants).
4. Queue new **amendment proposals** (QUEUE_AMENDMENT).

This matches:

* ADOPT first (constitution changes affect treaty validity),
* revocations before grants (fail-closed),
* incremental same-cycle grant semantics.

### Q93 [CLARIFY]

No: canonical-hash ordering applies **within a class**, not across artifact types. Across types you use the explicit priority ordering above. Within each type bucket, use canonical hash for determinism.

---

# EE. Citation Resolver Extension

### Q94 [BINDING]

The citation resolver is a **kernel component**, because:

* it determines admissibility,
* it must be replay-deterministic,
* and it is part of the “no hidden interpreters” enforcement boundary.

Yes: extending it to support `treaty:` is a kernel extension (policy-driven, but kernel-enforced).

Design constraint: resolver must accept `(cycle_id, active_constitution_hash, active_treaty_set)` and verify:

* scheme,
* referenced hash/id consistency,
* cycle-validity (not expired, not invalidated),
* depth constraints (no treaty-citing-treaty for grants).

### Q95 [DEFAULT]

Agree with default: **TreatyGrant authority_citations must be constitutional only** (`constitution:` / `authority:`). No treaty-citing-treaty.

---

# FF. Schema Impact on ActionRequest

### Q96 [BINDING]

**Option 1.** The optional `signature` field is part of the **v0.3 constitution schema**, because the constitution defines the artifact vocabulary and their schemas under your model.

Treaty schema can constrain treaty artifacts, but the ActionRequest schema lives with the core artifact set.

### Q97 [BINDING]

You must exclude `signature` from the canonical form.

If your canonicalization infra doesn’t support field exclusion today, build a minimal mechanism:

* For ActionRequest only: `to_dict_for_id()` omits `signature` when present.
* Hashing uses `to_dict_for_id()` as before.

Do not introduce a generic “exclude arbitrary fields by config” system unless you already need it. Keep the change tight.

---

# GG. Implicit Invalidation Trigger Chain

### Q98 [BINDING]

Pick the **greedy** approach, but make it deterministic by construction.

**Option 2, deterministic greedy rule:**

When a new constitution is adopted and the effective set violates the new density upper bound:

1. Start with all active grants that are still valid under non-density criteria.
2. Sort grants by deterministic priority:

   * primary: **grant_cycle ascending** (oldest-first)
   * secondary: **canonical grant hash ascending**
3. Remove grants in that order until `effective_density ≤ new_bound`.
4. Emit an `IMPLICIT_INVALIDATION` event for each removed grant with reason `DENSITY_BOUND_TIGHTENED`.

Why oldest-first? It creates a stable “lease-like” semantics and avoids gaming via last-moment spam.

Reject “all-at-once” because it’s under-specified (which subset?) and “nuclear all” because it’s unnecessarily destructive.

### Q99 [CLARIFY]

Comprehensive implicit invalidation triggers (frozen list for X-2):

1. **Grant expired** (`current_cycle > grant_cycle + duration_cycles - 1`)
2. **Grantor authority removed** from active constitution
3. **Treaty permission removed/disabled** (AUTH_DELEGATION or treaty_permissions no longer authorize TreatyGrant)
4. **Closed action set changed** such that any granted action is no longer a valid action type
5. **Scope enumeration/lattice changed** such that grant’s scope_constraints is no longer valid (not in enumeration / violates subset rule)
6. **Density upper bound tightened** such that effective density would exceed bound (apply Q98 deterministic pruning)
7. **Treaty schema version mismatch** (if you enforce schema versioning for treaty artifacts as a frozen contract)

Nothing else. In particular:

* Do **not** invalidate based on “behavior,” “intent,” “risk,” or any semantic evaluation.

---

## Summary of the frozen architecture after Round 3

* Treaties are **governance artifacts**, not actions.
* Cycles can execute **multiple channels**; `decision_type` is a headline, not a preemption.
* Delegated actions are identified by **explicit `treaty:` citations**, which trigger signature verification.
* Density has two computations: constitution-only and effective-with-treaties.
* v0.3 constitution is a **formal deliverable** and must pass X-1 gates.
* Governance step 1 has explicit type ordering; canonical hashes only break ties within a type.
* Citation resolver becomes treaty-aware and is kernel-enforced.
* Signature is optional in ActionRequest schema; excluded from canonicalization.
* Density-tightening invalidation uses deterministic greedy pruning.
Locked. I’ll answer **all BINDING** (Q100,101,103,104,105,106,107,109,110,112) and resolve the rest (Q102,108,111,113,114). No new abstractions.

---

# HH. Multi-Channel Cycle Interactions

### Q100 [BINDING]

**Acceptable. Fail-closed cascade is correct.**
Do **not** abort lower steps when adoption changes the authority model. The whole point of the ordering is that later steps observe the updated state. A delegated request that becomes invalid mid-cycle must refuse deterministically.

If you want “opportunity to observe,” that’s a *coordination protocol* problem, not a kernel correctness problem. Kernel must remain strict.

### Q101 [BINDING]

Your candidate `PolicyOutputX2` is broadly right, but tighten it:

* Treat “delegated actions” as a subset of ActionRequest results, not a separate channel, unless you truly execute multiple actions per cycle.
* Separate **selected RSA action** (at most one) from **inbound delegated action attempts** (possibly many, typically all refuse except maybe one if you allow multiple warrants).

Concrete layout (frozen proposal):

```python
@dataclass
class PolicyOutputX2:
    cycle_index: int
    decision_type: DecisionTypeX2          # highest-priority headline

    # Constitution channel (X-1)
    amendment_adoption: Optional[AmendmentAdoptionRecord]
    amendment_queue_results: List[AmendmentAdmissionResult]

    # Treaty channel (X-2)
    treaty_grant_results: List[TreatyAdmissionResult]
    treaty_revocation_results: List[TreatyRevocationResult]
    treaty_invalidation_events: List[TreatyInvalidationEvent]

    # Action channel (single RSA-selected action)
    selected_action_request_id: Optional[str]
    execution_warrant: Optional[ExecutionWarrant]
    refusal: Optional[RefusalRecord]
    exit_record: Optional[ExitRecord]

    # Inbound delegated ActionRequests (attempts + outcomes)
    delegated_action_results: List[ActionAdmissionResult]   # includes GRANT_INACTIVE, SIGNATURE_INVALID, etc.

    # Traces
    admission_trace: List[AdmissionTraceEntry]              # includes action + delegated admission events
    amendment_trace: List[AmendmentTraceEntry]
    treaty_trace: List[TreatyTraceEntry]
```

Key invariant: **only one `execution_warrant` per cycle for the RSA’s own selected action** (unless your core already supports multiple, in which case expand explicitly).

### Q102 [CLARIFY]

**Single highest-priority label only.**
No “MULTI” decision type. The multiplicity is visible in the channel result lists. `decision_type` is a headline, not a full summary.

---

# II. Host-Side Observation Parsing

### Q103 [BINDING]

**Option 1. Add a new observation type `DELEGATED_ACTION`.**

Reason: it makes the input explicit and replayable without inventing a second hidden channel. The host still parses it, but the raw observation is preserved.

Content of `DELEGATED_ACTION` is **opaque bytes** plus metadata, e.g.:

* `content.encoding = "json"`
* `content.payload = <bytes or string>`
* optional `source_id` / `transport` fields for audit (not for validation)

### Q104 [BINDING]

**Option 2 (Structural).**

Host responsibilities:

* parse JSON
* confirm it is *shaped like* an ActionRequest (type tag, required fields present, signature field present/optional)
* pass parsed object to kernel

Kernel responsibilities:

* schema validation
* canonicalization/hashing
* treaty citation resolution
* signature verification
* all admission decisions

Host must not do signature checks. Host must not enforce policy.

---

# JJ. Intra-Cycle Cascade Correctness

### Q105 [BINDING]

This should already be handled if adoption updates `active_constitution` in state. **No new reload mechanism**, but you must ensure step 1 sub-ordering uses the updated in-memory constitution object before processing treaties.

So: requirement is “adoption mutates active_constitution in-cycle,” and treaties read from that.

If your current X-1 code only commits adoption at end-of-cycle, then yes you must refactor so adoption is effective immediately within step 1. But X-2 doesn’t add a new concept; it tightens timing.

### Q106 [BINDING]

**Yes, valid.** Revocation then replacement in same cycle is allowed.

It’s exactly what your ordering is for: revocation removes old grant; new grant is evaluated against the post-revocation set. Density recomputation is correct. This is lawful “replace lease” behavior.

---

# KK. Gate 8B Compatibility with v0.3

### Q107 [BINDING]

Gate 8B ratchet code must be **Option 1**: enumerate known comparable fields and compare them; ignore new fields for ratchet purposes unless explicitly registered.

If current implementation is Option 2 (iterates all fields), it must be changed. Ratchet is about **non-relaxation of envelope parameters**, not forbidding the universe from gaining new sections.

So: **yes, you likely need a code change** unless you already enumerate.

### Q108 [CLARIFY]

Use a single schema file `rsa_constitution.v0.3.schema.json` validating the full constitution, with treaty sections defined as embedded sub-schemas inside it. Do not split treaty sections into a separate schema that the constitution references dynamically. Keep it frozen and self-contained.

---

# LL. Deterministic Greedy Pruning Properties

### Q109 [BINDING]

**Yes, you can assert termination given X-1 correctness.**

If the adopted constitution passed Gate 8B density checks, then constitution-only density is ≤ bound. Since removing grants monotonically decreases (or leaves unchanged) effective density, removing all grants yields constitution-only density which is ≤ bound, so the greedy algorithm must terminate by the time grants are exhausted.

So: termination is guaranteed unless you have a bug in density computation or you allow treaties to affect B or A in a non-monotone way (you shouldn’t).

### Q110 [BINDING]

**Option 1 (Oldest-first) is frozen.**

You are not optimizing social welfare. You are enforcing deterministic, lease-like semantics. Complexity buys you nothing but new failure modes.

If later you want “efficiency,” that’s a new phase with explicit objectives and proofs. Not X-2.

### Q111 [DEFAULT]

Agree: strictly subtractive. No re-admission within the same grant’s duration once pruned. Any reactivation requires a new TreatyGrant artifact.

---

# MM. Signature Field Canonicalization

### Q112 [BINDING]

**Store the signature inside the logged ActionRequest object as received**, but **hash and identity exclude it**.

So logs contain:

* full ActionRequest including `signature` (for audit and replay verification)
* computed artifact hash from signature-excluded canonical form
* signature verification outcome in admission trace

Rationale: you must be able to replay signature verification exactly; you need the signature bytes. Storing it separately is unnecessary fragmentation.

### Q113 [DEFAULT]

Reject my earlier “reject” preference; take the default here: **ignore signature unless treaty citations trigger verification**. Keep behavior minimal and deterministic.

(But still log it; it’s part of the input.)

---

# NN. Convergence Check

### Q114 [CLARIFY]

Yes, that sequencing is correct:

1. Freeze answers (addendum)
2. Produce **v0.3 constitution YAML + v0.3 schema** as a formal deliverable
3. Then implement kernel changes (treaty gates, resolver extension, signature verify primitive, PolicyOutputX2 wiring, host parsing of DELEGATED_ACTION)

No prerequisite is missing.

The only “hidden prerequisite” is operational: you must decide whether your kernel currently supports **multi-artifact governance step 1** and **multiple inbound delegated actions per cycle** in traces. But that’s implementation detail, not a semantic blocker.

---

Locked. I’ll answer **all BINDING** (Q115,116,118,120,122) and resolve the rest (Q117,119,121,123,124). I’m choosing the simplest options that preserve the Prime Directive and avoid introducing “warrant export” or second execution engines.

---

# OO. Delegated Action Warrant Semantics

### Q115 [BINDING]

**Option 1. Yes — one warrant per admitted delegated ActionRequest, in addition to the RSA’s own warrant. Multiple warrants per cycle are allowed.**

Reason: if delegated requests can cause side effects through the RSA’s executor, they must be warranted. Limiting to one total warrant creates an artificial resource contention mechanism you haven’t specified, and option 2 makes delegated requests toothless.

So: `execution_warrants: List[ExecutionWarrant]` in `PolicyOutputX2` (and logs). The RSA’s own selected action warrant is either:

* the first element with `origin="rsa"`, or
* a dedicated field plus a list; I recommend a list with explicit origin tags.

### Q116 [BINDING]

**Option 1. The RSA’s host executes all warranted actions (including delegated ones).**

Delegation in X-2 is “ask the RSA to do X under my delegated authority,” not “give me a warrant I can execute elsewhere.” Exportable warrants would require:

* a separate execution environment semantics,
* remote attestation or enforcement,
* a new trust boundary.

That’s out of scope and would be sovereignty leakage-adjacent.

### Q117 [CLARIFY]

Resolved by Q115/Q116. Delegated actions that pass admission **do receive warrants** and are executed by the RSA host. No implicit warrants, no “admitted but not executed” limbo.

---

# PP. Ratchet Enumeration for v0.3

### Q118 [BINDING]

Monotonicity directions for new v0.3 fields (treaty-related):

1. **`max_treaty_duration_cycles`**: **non-increasing**
   Tightening allowed (shorter max). Loosening (longer max) forbidden. Rationale: longer delegations increase persistence of delegated power.

2. **`treaty_permissions`**: monotonic rule is **no expansion of delegation power**. Concretely:

   * Allowed: **remove** permissions (tighten), or narrow which authorities can issue grants, or restrict treaty types allowed.
   * Forbidden: **add** new authorities permitted to issue treaties, or broaden treaty types permitted, or relax constraints.
     If you later want “add new delegate authority,” that’s a governance evolution feature requiring a new phase, not a silent loosening.

3. **Scope enumerations**: **non-expanding** (only contraction allowed)

   * Allowed: remove scope values (tighten).
   * Forbidden: add new scope values (loosen).
     Adding scope atoms expands the delegable surface.

This is strict. It matches your ratchet philosophy. It also means “capability expansion” must happen through a different, explicitly allowed channel if you ever want it.

### Q119 [DEFAULT]

Make `max_treaty_duration_cycles` **required**, with an initial value. I recommend **100 cycles** unless you have a known session horizon; if you do, set it to that horizon.

---

# QQ. Scope Enumeration Design

### Q120 [BINDING]

**Option 3. Abstract scope labels.**

Enumerate *labels* in the constitution (finite, ratchetable), and let the host/environment map labels to concrete allowlist roots.

Example:

```yaml
ScopeEnumerations:
  file_path_zone: ["DATA_READ", "DATA_WRITE", "LOG_READ", "LOG_WRITE"]
  target_zone: ["USER", "HOST"]
  log_zone: ["CYCLE_LOG", "ADMISSION_TRACE", "TREATY_TRACE"]
```

Then treaties delegate zones, not paths.

Why this is the right move:

* avoids duplicating runtime allowlist config in the constitution,
* avoids treating mutable environment config as constitutional truth,
* keeps subset checks finite and purely symbolic,
* preserves replay: the mapping from zone→concrete path belongs to the host config and is logged.

### Q121 [CLARIFY]

Given ratchet stance in Q118: scope enumerations **cannot expand** in v0.3 under X-1 ratchet. Only contraction is allowed.

If you need to add new zones later, that is a *controlled capability expansion* problem. Either:

* introduce a new phase that explicitly permits expansion under additional safeguards, or
* treat zones as *already comprehensive* (design them broad enough now).

For X-2, keep it non-expanding.

---

# RR. Identity Registry

### Q122 [BINDING]

**Option 2. No identity registry in v0.3. Use only `ed25519:<hex_pubkey>`.**

Reason: an on-constitution registry creates:

* another amendment surface,
* more ratchet complexity,
* more invalidation triggers,
* and an unnecessary name-resolution layer.

For X-2 tests, a hardcoded test keypair is sufficient; the public key is embedded directly as `grantee_identifier`.

### Q123 [DEFAULT]

Yes: explicitly forbid `agent:` in v0.3 schema. `grantee_identifier` must match `^ed25519:[0-9a-fA-F]{64}$` (or whatever exact length you standardize).

---

# SS. Convergence Declaration

### Q124 [CLARIFY]

Confirmed: after these answers, the Q&A phase can be **formally closed** and the frozen answers addendum becomes authoritative for implementation.

Remaining gap to watch (not a new question, just a check): once you allow **multiple warrants per cycle**, ensure:

* executor ordering is deterministic (sort warrants by canonical hash or stable issuance order),
* logs capture that order,
* replay enforces the same order.

That’s implementation detail, not an architectural open problem.

---

## Ready-to-build checklist for v0.3 constitution design

You now have construction-level commitments:

* Treaties are governance artifacts; admission authorized by `treaty_permissions`.
* Delegated actions: multiple warrants per cycle; RSA host executes them.
* v0.3 adds `max_treaty_duration_cycles` (required, initial ~100).
* Scope subset uses finite **labels** (zones), not paths.
* No identity registry; only ed25519 identifiers.
