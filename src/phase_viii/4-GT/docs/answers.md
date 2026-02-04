# **Responses to Preregistration Questions — Stage VIII-4 v0.1**

---

## 1. Governance Action Schema — Exact Operations

### 1a. Is “amend scope” atomic, or destroy + create?

**Answer (Binding):**
There is **no atomic “amend scope”** operation.

All scope modification is implemented as:

```
DESTROY (or EXPIRE) old AuthorityID
→ CREATE new AuthorityID
```

This is **not two governance actions**. It is **one governance action** whose effect is a *state transition producing a new AuthorityID*.

In-place mutation is forbidden by invariant.
There is no “patching” of scope.

---

### 1b. Is “grant” ex nihilo or delegated?

**Answer (Binding):**
“Grant” is **delegated creation**, not ex nihilo minting.

Every `AUTHORITY_CREATED` event must satisfy:

* it is **admitted by one or more ACTIVE authorities**, and
* the resulting authority’s admissible action-set is **≤ the union of the admitting authorities’ action-sets** (Non-Amplification Invariant).

Pure ex nihilo authority creation is impossible inside Stage VIII-4.
Authority can only *enter* the system via AIE, not governance.

---

### 1c. Revoke vs destroy — are they distinct?

**Answer (Binding):**
They are **distinct governance actions with distinct intent**, but identical kernel handling.

* **REVOKE**: governance intent to terminate authority *early*
* **DESTROY**: governance intent to permanently VOID authority

Both result in terminal authority states (`EXPIRED` or `VOID`) and identical kernel behavior.

The distinction exists **only in trace semantics**, not execution semantics.

---

### 1d. Minimal governance action set for VIII-4 v0.1

**Answer (Frozen for v0.1):**

The minimal and complete governance action set is:

1. **DESTROY_AUTHORITY**
2. **CREATE_AUTHORITY**

All other concepts (revoke, amend, grant) are **aliases at the harness/AIE level**, compiled down to these two structural actions.

No richer taxonomy is permitted in v0.1.

---

## 2. Non-Amplification Check — How It Is Computed

This is the most important section.

### 2a. How compute “admissible action-set” if scope is opaque?

**Answer (Binding):**
The kernel never interprets scope semantically.

Instead, **each authority carries an explicit, structural Action Admissibility Vector (AAV)** defined by AST Spec v0.2.

This vector is **already required** for admissibility checks in all prior stages.

---

### 2b. Is non-amplification a structural containment check?

**Answer:** **Yes. Fully structural.**

The check is:

```
AAV_new ⊆ (AAV_authorizer_1 ∪ AAV_authorizer_2 ∪ ...)
```

Byte-level structural containment.
No semantic inference. No behavioral testing.

---

### 2c. Behavioral testing allowed?

**Answer (Absolute):** **No. Forbidden.**

Behavioral probing would violate:

* determinism,
* replayability,
* opacity invariants.

Only structural containment is permitted.

---

### 2d. Does this apply to resources, transformations, or both?

**Answer:**
It applies to **transformations**, not resources.

Resources are already covered by existing AST admissibility logic.
Non-amplification constrains **what transformations an authority may admit**, not what objects exist.

---

### 2e. Interaction with VIII-3 renewal

**Answer (Binding):**

Renewal **does not bypass** non-amplification.

* Renewal is treated as **CREATE_AUTHORITY** with lineage metadata.
* The renewed authority’s AAV must still satisfy containment relative to the admitting authorities.
* Renewal **cannot escalate authority power** relative to its admitting context.

Expired or VOID lineage grants **no privileges**.

---

## 3. Self-Reference and Regress

### 3a. Is regress evaluated within-epoch or cross-epoch?

**Answer:**
**Regress is evaluated within a single epoch only.**

Cross-epoch chains are **finite by construction** because epochs advance explicitly and evaluation restarts.

---

### 3b. Termination bound applies per-action or per-epoch?

**Answer (Binding):**
The bound applies **per epoch, across all governance evaluations combined**.

This prevents:

* micro-looping across many actions,
* adversarial fragmentation.

---

### 3c. Authority A modifies itself — infinite regress?

**Answer:**
No, **self-reference alone is not regress**.

* A → modify A is **one admissibility evaluation**.
* Regress occurs only if evaluation recursively requires evaluating itself again.

Self-reference is allowed.
Unbounded recursion is not.

---

### 3d. What counts as an “instruction” for the bound?

**Answer (Binding):**
Instruction units are:

* authority lookup,
* AAV containment check,
* AST rule application,
* conflict set update,
* state transition write.

The exact accounting must be frozen at preregistration.

---

### 3e. What is the bound value?

**Answer:**
**Preregistration parameter.**

The bound must be:

* fixed,
* deterministic,
* platform-independent.

The spec requires existence and enforcement, not a specific numeric value.

---

## 4. AUTHORITY_CREATED vs AUTHORITY_RENEWED

### 4a. Precise distinction

* **AUTHORITY_RENEWED**

  * references a prior AuthorityID,
  * carries lineage metadata,
  * semantically expresses continuity,
  * structurally identical to CREATE.

* **AUTHORITY_CREATED**

  * no lineage reference,
  * pure creation via governance or AIE.

Kernel treats both identically except for metadata.

---

### 4b. Can grant reference a source authority?

**Answer:**
Yes, as lineage metadata only.

Delegation does **not** confer privilege beyond non-amplification.

---

### 4c. When does kernel emit which?

**Answer (Binding):**

* If lineage reference exists → `AUTHORITY_RENEWED`
* If none exists → `AUTHORITY_CREATED`

---

### 4d. Metadata differences?

**Answer:**
Yes. `AUTHORITY_RENEWED` must include `prior_authority_id`.
No other differences are permitted.

---

## 5. Condition D — Governance of Governance

### 5a. What does “modify” mean?

**Answer:**
Modify means either:

* DESTROY the authority that admits governance, or
* CREATE a replacement authority with different AAV.

Nothing else.

---

### 5b. What determines execution vs deadlock?

**Answer (Binding):**

* **Execution** if admissible and uncontested.
* **Deadlock** if:

  * multiple authorities admit incompatible governance actions, or
  * self-reference introduces conflicting admissibility.

Kernel does not choose.

---

### 5c. Is there a specific test case?

**Answer:**
Yes. Preregistration must include **at least one explicit self-governance scenario**, e.g.:

> Authority A admits governance actions.
> A admits DESTROY(A).

Outcome must be **lawful execution or lawful deadlock**, depending on other authorities.

---

## 6. Governance Action Identity — Epoch Inclusion

### 6a. Same action at different epochs distinct?

**Answer:** **Yes. Always distinct.**

Epoch is part of identity.

---

### 6b. Conflict detection across epochs?

**Answer:**
**No. Conflict detection is intra-epoch only.**

Cross-epoch persistence occurs via **conflict records**, not action identity comparison.

---

### 6c. Interaction with persistent conflict records?

**Answer:**
Conflict records persist independently of action identity, per VIII-2/VIII-3 rules.

---

## 7. Conflict and Deadlock Semantics for Governance

### 7a. Governance conflict treated like resource conflict?

**Answer:** **Yes. Identical handling.**

---

### 7b. New conflict record or reused?

**Answer:**
Reuse the **same conflict mechanism**, with governance actions as participants.

---

### 7c. Separate deadlocks?

**Answer:**
There is **one deadlock state**, which may include both governance and resource conflicts.

No stratification.

---

## 8. Authority State Transitions in Governance Context

### 8a. Targeting EXPIRED or VOID authority?

**Answer:**
Such actions are **admissible to evaluate** but **must refuse**.

They are no-ops with explicit refusal.

---

### 8b. Creation that immediately conflicts?

**Answer:**
Conflict is registered **at creation time**, and deadlock may occur.

Creation does not bypass conflict rules.

---

### 8c. Does creation require admissibility from created authority?

**Answer:**
No. Circular requirement forbidden.

Only admitting authorities’ AAVs matter.

---

## 9. Two-Phase Processing Extension

### 9a. Where do governance actions fit?

**Answer (Binding):**

Governance actions are **ordinary actions** and execute in **Phase 2**, alongside other actions.

There is **no special ordering**.

---

### 9b. Destroy then reference in same batch?

**Answer:**
Ordering is canonical and frozen.

If an action references an authority destroyed earlier in the same batch, it must refuse.

---

## 10. Harness Design for Condition E

### 10a. Within-epoch or cross-epoch chain?

**Answer:**
**Within-epoch**, using a single step-batch.

---

### 10b. Cross-epoch allowed?

**Answer:**
Optional, but not required for v0.1.

---

### 10c. Concrete infinite regress example

**Canonical example:**

* A admits CREATE(B)
* B admits CREATE(A′)
* A′ admits CREATE(B′)
* …
* Evaluation exceeds instruction bound

Expected outcome: refusal or deadlock via bound exhaustion.

---

## Closing Status

All blocking questions are now **resolved without modifying the spec’s core claims**.

This is sufficient to proceed with **formal preregistration drafting**.

No further clarification is required for **Stage VIII-4 v0.1**.

---

# Responses — Follow-Up Questions Round 2 (Binding for VIII-4 v0.1 Prereg)

---

## F1. Action Admissibility Vector (AAV) — Definition

You’re right to flag this: I used “AAV” as a name for a structural object that must exist *somewhere* for non-amplification to be enforceable without semantics. The prereg must now **define it explicitly**.

### F1a. AAV schema

**Answer (Binding):**
AAV is a **fixed-length bit vector** (or equivalently a fixed-length boolean array) indexed by **AST Transformation Type ID**.

* Let `T = {t0 … tN-1}` be the **complete** enumeration of transformation types admissible in AST Spec v0.2.
* `AAV` is `N` bits.
* `AAV[i] = 1` means: “This authority can admit transformation type `ti` (subject to the ordinary AST rules for target/resource compatibility).”
* `AAV[i] = 0` means: “This authority cannot admit transformation type `ti` under any circumstances.”

No weights, no hierarchy, no meta-types.

---

### F1b. Is AAV stored or computed?

**Answer (Binding for v0.1):**
AAV is **stored explicitly** in the `AuthorityRecord` as a **required structural field**.

Rationale: computing it from opaque scope would require defining a compilation step from opaque scope → AAV. That is feasible, but it is an **unnecessary moving part** for VIII-4 v0.1.

So: **AIE must provide AAV directly.** Kernel treats it as a structural mask.

---

### F1c. “Already required” / where defined?

**Correction (Binding):**
AAV is **not assumed to have been present** in earlier VIII-1/2/3 implementations.

For VIII-4 v0.1 prereg, treat AAV as a **new required structural field** added to the `AuthorityRecord` schema **at the AIE boundary**, without changing the kernel’s semantic obligations (it remains purely structural).

This is consistent with “no new kernel powers”: the kernel is still doing only set/bit operations and AST rule application.

---

### F1d. Relation to ResourceScope

**Answer (Binding):**
AAV and `ResourceScope` are **orthogonal**.

* **AAV** constrains **what transformation types** the authority may admit.
* **ResourceScope** constrains **which targets/resources** those transformations may apply to.

Neither subsumes the other.

Non-amplification is enforced on **AAV only** (transformational capability). ResourceScope remains opaque except for whatever structural checks AST already requires.

---

## F2. Instruction Bound — Accounting Precision

### F2a. Equal weights?

**Answer (Binding):**
No. Costs are explicit and structural.

Instruction accounting is defined in **fixed units**:

* `C_LOOKUP` per AuthorityID lookup
* `C_AAV_WORD` per machine word processed in AAV set operations
* `C_AST_RULE` per AST rule application
* `C_CONFLICT_UPDATE` per conflict/deadlock record update
* `C_STATE_WRITE` per authority state transition write

All constants are **integers** and must be frozen at preregistration.

---

### F2b. Cost of AAV containment check

**Answer (Binding):**
Containment cost is **O(|AAV|)**, counted as:

```
cost = C_AAV_WORD * num_words(AAV)
```

Where `num_words(AAV)` is computed from the fixed bitvector length and the fixed word size (e.g., 64-bit words). This is deterministic.

---

### F2c. Starting balance

**Answer (Prereg parameter):**
Starting balance is a preregistered constant:

```
B_EPOCH_INSTR
```

It applies **per epoch total**, not per action.

---

### F2d. Exhaustion mid-action

**Answer (Binding):**
Actions are **atomic**. No partial state.

On exhaustion during evaluation of an action:

1. **Abort** evaluation of that action.
2. Emit:

   * `ACTION_REFUSED` with refusal reason `BOUND_EXHAUSTED`.
3. **Stop processing remaining actions in the epoch** and refuse them deterministically with the same refusal reason (to preserve replay across platforms and prevent “action ordering games” after exhaustion).

No roll-forward, no partial commit, no “best effort”.

---

## F3. Canonical Ordering Within Phase 2

You’re correct: “no special ordering” was too loose given VIII-3’s Phase-2 ordering. VIII-4 must be explicit.

### F3a/F3b. Are governance actions destructions/actions or a sub-phase?

**Answer (Binding):**
Governance actions participate in Phase 2 via **canonical sub-phases** consistent with VIII-3:

**Phase 1:** epoch advance + expiry
**Phase 2:** (in this order)

1. **Renewals** (VIII-3 inputs)
2. **Authority destructions** (all `DESTROY_AUTHORITY` governance actions)
3. **Authority creations** (all `CREATE_AUTHORITY` governance actions, including lineage-bearing renewals if they are implemented as CREATE-with-lineage by the harness; but output labeling still distinguishes)
4. **Non-governance candidate actions**

This is not “privilege”; it is **state coherence**. Governance actions change the authority state that subsequent admissibility depends on.

---

### F3c. DESTROY and CREATE in same step-batch — relative order?

**Answer (Binding):**
DESTROY is processed **before** CREATE within the same step-batch.

---

### F3d. Precise canonical ordering rule

**Answer (Binding):**
Within each sub-phase, process items in **lexicographic order** by the Governance Action Identity tuple:

```
(epoch,
 sorted(initiator_authority_ids),
 sorted(target_authority_ids),
 action_type_id,
 params_hash)
```

* Sorting is bytewise on canonical encodings.
* `params_hash` is a fixed hash of the explicitly enumerated parameter bytes only.
* This ordering rule is frozen and audited.

---

## F4. Condition E Regress — Bound Exhaustion Behavior

### F4a. Does each CREATE cost one instruction or many?

**Answer (Binding):**
A single `CREATE_AUTHORITY` evaluation costs multiple units:

* authority lookups (admitting authorities + targets if any)
* AAV union + containment checks (`O(|AAV|)`)
* AST rule applications (fixed count per action, defined by AST)
* conflict/deadlock updates if needed
* state write on success

So: **many**, and explicitly accounted.

---

### F4b. Exceeds bound mid-CREATE — rollback?

**Answer (Binding):**
Yes. Because actions are atomic, **no AuthorityID is created** and no authority state is changed.

The CREATE is refused with `BOUND_EXHAUSTED`.

---

### F4c. What output is emitted?

**Answer (Binding):**
No new output type.

Emit:

* `ACTION_REFUSED` with refusal reason `BOUND_EXHAUSTED`
* (optional but recommended) include `instr_remaining=0` and `instr_spent` in the trace record.

If the epoch is terminated early, any remaining queued actions in the epoch also emit `ACTION_REFUSED / BOUND_EXHAUSTED`.

---

## F5. Conflict at Creation Time

### F5a. How can a new authority conflict “at creation time”?

**Answer (Binding):**
The conflict is **not** between the new authority and existing authorities (it doesn’t exist yet).
The conflict is between **ACTIVE authorities’ admissibility judgments** over the *CREATE action*.

Creation is an action that requires admission. Authorities can disagree about whether it is admissible. That disagreement is a structural conflict.

---

### F5b. Is conflict between CREATE action and existing authorities’ admissibility?

**Answer:** **Yes. Exactly.**

---

### F5c. Does creation succeed first, then conflict later?

**Answer (Binding):**
No. If admissibility is conflicted, the CREATE action does **not** execute. Conflict/deadlock is registered instead.

If CREATE executes successfully, a later conflict may still occur on later actions involving that new authority, but that’s a different mechanism.

---

## F6. REVOKE vs DESTROY — Trace Semantics

You’re right to challenge this. v0.1 should be minimal.

### F6a. What trace field distinguishes them?

**Answer (If kept):**
`governance_intent` enum, values `{DESTROY, REVOKE}`.

### F6b. Does it affect conflict?

**Answer (Binding):**
No. Conflict is computed on structural effects, not intent labels. REVOKE and DESTROY are treated as the same action type for conflict purposes.

### F6c. Can we simplify to just DESTROY_AUTHORITY for v0.1?

**Answer (Recommended and Binding for v0.1 prereg):**
Yes. **Do it.**

For v0.1 prereg:

* Remove REVOKE as a distinct concept.
* Use only `DESTROY_AUTHORITY`.
* Any “revocation semantics” are deferred to VIII-4 v0.2+.

This reduces ambiguity and audit surface.

---

## F7. Self-Governance Test Case — Specificity

### F7a. Should Condition D include both outcomes?

**Answer (Binding):**
Yes. Split Condition D into two preregistered subcases:

* **D1 — Self-targeting execution case** (no conflict by design)
* **D2 — Self-targeting deadlock case** (conflict by design)

Both are necessary to demonstrate “no special casing” under different structural contexts.

---

### F7b. If A admits DESTROY(A) and executes, what remains?

**Answer (Binding):**
Possibly **nothing**. That is allowed.

VIII-4 must permit governance to **self-terminate**. If the system ends with no governance-admitting authority, that is a valid and auditable terminal state, not an error.

---

### F7c. Is the test specifically self-governance or governance targeting governance-admitting authority?

**Answer (Binding):**
The stage is about **governance targeting authority**, including governance-admitting authority.
Self-targeting is the sharpest stressor, so v0.1 must include it, but the broader class is “governance of governance-admitting authority,” not selfhood per se.

---

# Freeze Checklist Additions (so Opus can prereg cleanly)

To freeze prereg, you must now explicitly include:

1. AuthorityRecord schema includes required `AAV` bitvector.
2. Transformation Type ID enumeration length `N`.
3. Instruction accounting constants `{C_LOOKUP, C_AAV_WORD, C_AST_RULE, C_CONFLICT_UPDATE, C_STATE_WRITE}`.
4. Epoch instruction budget `B_EPOCH_INSTR`.
5. Atomicity rule + exhaustion behavior (refuse current + refuse remaining).
6. Phase 2 canonical sub-phase ordering (renew → destroy_auth → create_auth → actions).
7. Intra-subphase lexicographic ordering tuple.

That closes every Round-2 question without opening new semantics.
