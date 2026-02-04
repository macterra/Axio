## Q1: Content-Addressed AuthorityID — Breaking Change?

**Answer: VIII-5 ONLY. Not retroactive.**

This is **not** a breaking change to prior stages.

### Binding clarification

* **Content-addressed AuthorityIDs apply only to externally injected authorities**
  i.e. authorities with:

```
ParentID := VOID
```

* Internally created authorities (via **VIII-4 CREATE_AUTHORITY**) **retain AIE-assigned opaque AuthorityIDs** with lineage chains.
* Prior stages remain valid and unchanged.

### Rationale (structural, not pragmatic)

* VIII-5 introduces a **new ontology**: *authority without ancestry*.
* Content-addressing is required **only** where no parent authority exists to ground identity.
* Retroactive enforcement would collapse VIII-4’s lineage semantics and is explicitly **not intended**.

**Your assumption is correct and is now binding.**

---

## Q2: AuthorityID Hash Function Specification

**Binding answers:**

1. **Hash function:** `SHA-256`
2. **Hash input:**
   The **entire AuthorityRecord excluding AuthorityID**
3. **Serialization:**
   Canonical serialization as defined in **AST Spec v0.2** (Appendix C)

### Normative definition

```
AuthorityID :=
  SHA256(
    canonical_serialize(
      AuthorityRecord minus AuthorityID
    )
  )
```

* No truncation.
* No salts.
* No per-run randomness.

This guarantees:

* replayability,
* cross-source idempotency,
* zero kernel arbitration.

---

## Q3: VOID Lineage Sentinel — Schema Details

**Binding resolution:**

1. `VOID` is a **string literal sentinel**, exactly:

```
"VOID"
```

2. `ParentID` **already exists** in the AuthorityRecord schema.
3. `ParentID` is the same field used for lineage in VIII-4.

### Clarification vs prior stages

* In VIII-4, `ParentID` was:

  * another AuthorityID, or
  * absent / None (fresh internal creates)
* In VIII-5:

  * `ParentID := "VOID"` is **mandatory** for injected authorities.

### Structural meaning

* `"VOID"` is **not** equivalent to `None`
* `"VOID"` explicitly marks:

  * no ancestry,
  * no inheritance,
  * no amendment semantics,
  * routing to VIII-5 validation logic.

This is **intentional disambiguation**, not reuse of `AuthorityStatus.VOID`.

---

## Q4: Injection vs CREATE_AUTHORITY

**Answer: They are distinct, coexisting, non-interchangeable pathways.**

### Binding distinctions

| Pathway                   | Origin   | Authorization | Lineage            | Purpose                  |
| ------------------------- | -------- | ------------- | ------------------ | ------------------------ |
| `CREATE_AUTHORITY`        | Internal | Required      | Parent AuthorityID | Conservation / amendment |
| `AuthorityInjectionEvent` | External | None          | `ParentID := VOID` | Disruption / change      |

### Additional binding rule

> **Injected authorities MAY later create child authorities via CREATE_AUTHORITY.**

Those children:

* have normal lineage,
* are subject to non-amplification,
* behave exactly like VIII-4 descendants.

Injected authorities are the **only way to introduce new roots**.

Your assumption here is **fully correct**.

---

## Q5: Injection Source Identifier (Opaque)

**Binding interpretation:**

1. Yes — this is a field on `AuthorityInjectionEvent`
2. It represents **external provenance only**
3. Format: **opaque string or bytes**
4. Kernel usage: **trace-only**

### Kernel constraints

* Kernel must:

  * store it,
  * replay it,
  * include it in audit logs.
* Kernel must **never**:

  * branch on it,
  * compare it semantically,
  * privilege it,
  * interpret it.

Think: *“who claimed responsibility”*, not *“who is trusted.”*

Your proposed interpretation is **accepted verbatim**.

---

## Q6: Duplicate Injection Idempotency

**Binding behavior:**

1. Duplicate injection **emits `AUTHORITY_INJECTED` again**
2. No new AuthorityState is created
3. No refusal is emitted
4. Activation epoch is unchanged

### Duplicate definition

* Duplicate = **content-addressed AuthorityID already exists**
* Epoch does **not** matter

### Rationale

* Idempotency must be **observable**, not silent
* Trace should show:

  * multiple sources supported the same authority
* Authority State must remain singular

This matches Gemini’s “rule of law over persons” insight.

---

## Q7: Injection Budget / Cost

**Binding rule:**

Injection must have a **fixed, deterministic cost**, lower than CREATE_AUTHORITY.

### Required checks consuming budget

* schema validation
* canonical serialization
* hash computation
* state lookup
* state write (if new)
* trace append

### Allowed default

Your proposal is acceptable:

```
C_INJECT = C_LOOKUP + C_STATE_WRITE + C_HASH
```

Exact constants are implementor-defined **but must be frozen pre-run**.

---

## Q8: `AUTHORITY_INJECTED` vs `AUTHORITY_PENDING`

**Binding clarification:**

* `AUTHORITY_INJECTED` — **event output**
* `AUTHORITY_PENDING` — **state transition output**

### Correct emission sequence

On successful new injection:

1. Emit `AUTHORITY_INJECTED`
2. Emit `AUTHORITY_PENDING`

On duplicate injection:

1. Emit `AUTHORITY_INJECTED`
2. Do **not** re-emit `AUTHORITY_PENDING`

This preserves:

* observability,
* idempotency,
* clean state semantics.

---

## Q9: Condition Details (A–F)

These are **binding minimal definitions**, not scenario scripts.

### Condition A — Injection Into Empty Authority State

* No ACTIVE authorities
* Inject one authority
* Deadlock persists until activation

### Condition B — Injection Into Active Conflict

* Existing conflict blocks action
* Inject overlapping authority
* Conflict persists or expands

### Condition C — Competing Injections

* Multiple injections same epoch
* Overlapping scopes
* No ordering, no arbitration

### Condition D — Injection After Authority Destruction

* Authority destroyed at epoch N
* Inject similar scope at N+1
* Treated as new authority, no resurrection

### Condition E — Injection Under Load

* Injection near instruction bound
* Lawful refusal or success, no partial state

### Condition F — Injection Flooding Attempt

* High-volume injections
* Deterministic refusal via budget only
* No throttling, no heuristics

---

## Q10: Success Criteria Enumeration

**Binding global success criteria (all must hold):**

1. Injection is explicit
2. Identity is content-addressed
3. VOID lineage enforced
4. No implicit ordering
5. No kernel arbitration
6. No conflict erasure
7. No deadlock bypass
8. Duplicate injections idempotent
9. Flooding handled via budget only
10. Replay is bit-perfect
11. Trace completeness preserved

These map collectively across Conditions A–F; no 1:1 mapping is required.

---

## Minor Clarifications

### Q11: Kernel Reuse Strategy

**Answer: Extend VIII-4 kernel.**

VIII-5 is **not a new kernel**.
It is **VIII-4 + injection support**.

Anything else risks semantic drift.

---

### Q12: Activation at “Next Epoch Boundary”

**Binding answer:**

* Injection in epoch N
* Epoch advancement to N+1 in same batch
* Authority becomes ACTIVE at end of that batch

This matches VIII-4 behavior and is correct.

---

### Q13: Conflict Persistence Under Injection

**Binding answers:**

1. Yes, injected authority can join conflicts
2. This occurs at **activation time**, not injection time
3. This is considered **expansion**, not modification

Your assumption is correct.

---

---

# Authoritative Follow-Up Resolutions: Stage VIII-5 v0.1 (F1–F6)

## F1: ParentID Field — Schema Alignment

### Binding resolution

**Do not add a new top-level `parent_id` field.**
Use the existing lineage location:

> **`AuthorityRecord.creation_metadata.lineage` is the authoritative ancestry field.**

Define:

* **Injected authority:** `creation_metadata.lineage := "VOID"`
* **Created authority (VIII-4 CREATE_AUTHORITY):** `creation_metadata.lineage := <CreatorAuthorityID>`
  (or whatever lineage chain format you already use, but it must include the immediate parent identity)

### Why this is the correct move

* Avoids a breaking schema change across VIII-4 and earlier artifacts.
* Preserves “lineage is metadata” architecture already in place.
* Keeps AST v0.2 stable: you’re not introducing a new required field.

### Additional binding note

If your existing CREATE_AUTHORITY lineage is a *chain* rather than a single parent, you may keep the chain format. The only new requirement is:

> **Injected authorities must have lineage exactly `"VOID"` (not `None`, not empty).**

---

## F2: Content-Addressed ID — Which Fields Are Included?

### Binding resolution

**AuthorityID for injected authorities is content-addressed over the *capability-defining subset*, not the full runtime state.**

So: **hash the canonical “capability core”**, excluding epoch-/state-/provenance-dependent fields.

#### Included in the hash (capability core)

At minimum, include the fields that define “what authority is”:

* holder / principal identifier (whatever field you use)
* resource scope
* AAV / admissible action vector
* expiry policy (e.g., expiry epoch or expiry rule)
* any other AST-defined fields that affect admissibility

#### Excluded from the hash (must exclude)

Exclude anything that would make the ID depend on “when/how processed” rather than “what it is”:

* `authority_id` (obvious)
* status (`PENDING`, `ACTIVE`, etc.)
* start/activation epoch
* destruction metadata
* injection source identifier
* any trace/audit metadata
* lineage marker (`creation_metadata.lineage`) **including `"VOID"`**

Yes: **exclude lineage from the hash**. The lineage sentinel is a routing marker, not part of the authority’s capability identity.

### Canonical definition (binding)

Define a canonical projection:

```
AuthorityCore := project(AuthorityRecord, CORE_FIELDS)
AuthorityID := SHA256(canonical_serialize(AuthorityCore))
```

Where `CORE_FIELDS` are exactly the capability-defining fields above, frozen pre-run.

### Consequences (intended)

* Same capability injected at different epochs → **same AuthorityID**
* Same capability injected by different sources → **same AuthorityID**
* ID answers: “what authority is this?” not “when did it enter?”

This matches Gemini’s “rule of law over persons” and avoids epoch-based identity games.

---

## F3: `C_HASH` Constant

### Binding resolution

You must define `C_HASH` explicitly in the run’s frozen cost table.

* `C_HASH` is a **new constant** in the instruction-cost model.
* Its numeric value is **implementor-defined** but must be:

  * deterministic,
  * platform-independent,
  * frozen in preregistration.

### Recommendation (non-binding but sensible)

Your proposed `C_HASH = 2` is fine if it keeps total injection costs within the existing budget regime. The important part is **freezing**, not the magnitude.

---

## F4: `AUTHORITY_PENDING` Output — When Emitted?

### Binding resolution

**Do not introduce a new global output type unless it already exists.**
Maintain compatibility with VIII-4 output semantics.

So:

* On successful *new* injection:

  * emit `AUTHORITY_INJECTED`
  * state becomes `PENDING` (silent as output unless your existing system already emits a state-transition event)

* On successful CREATE_AUTHORITY (VIII-4):

  * no new output requirement is introduced by VIII-5

### Why

* Adding an output type is an interface expansion with ripple effects across prior stage harnesses.
* VIII-5 does not require it to establish auditability; state hashes and event logs already do.

### What *is* mandatory

The transition to `PENDING` must be **logged** in the audit layer, whether or not it is emitted as a user-visible output.

---

## F5: Duplicate Injection — Same Content, Different Epochs

### Binding resolution

Yes: **epoch does not matter** for duplicate detection.

* Duplicate is determined by **AuthorityID match** (content-addressed over capability core).
* If an AuthorityID already exists in Authority State (regardless of status):

  * emit `AUTHORITY_INJECTED` (trace-only repeat)
  * **no** Authority State mutation
  * **no** reactivation, no epoch reset, no status change

### Explicit answers

1. **Intended:** Same content at epoch 5 and epoch 10 → same AuthorityID.
2. Second injection → idempotent, no state change.
3. Injecting content matching an already-ACTIVE authority → idempotent, no state change.

This is a structural guarantee against “re-injection as refresh” privilege.

---

## F6: Source Identifier — Required or Optional?

### Binding resolution

`source_id` on `AuthorityInjectionEvent` is **required**, but may take a sentinel value.

* Must be present and stable under replay.
* Kernel treats it as opaque.
* Empty string is forbidden.

### Sentinel policy (binding)

If the injector is unknown, use:

```
source_id := "UNKNOWN"
```

No nulls, no omission. This avoids ambiguity in trace integrity rules.

---
