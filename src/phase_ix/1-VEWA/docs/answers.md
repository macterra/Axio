## 1. Value Declaration Grammar (Binding)

**Answer:**
Yes, a **simple, explicit, structural grammar** is intended. Your JSON sketch is *close*, but it needs tightening to avoid semantic leakage.

### Binding requirements

A **value declaration** is:

* **opaque** beyond its structural fields,
* **non-executable**,
* **non-interpreted** by the kernel,
* **bijectively encodable** into authority artifacts.

### Canonical form (recommended)

```json
{
  "value_id": "V001",
  "scope": [
    {
      "target": "FILE:/data/secret.txt",
      "operation": "READ"
    }
  ],
  "commitment": "DENY"
}
```

### Explicit prohibitions

* `name` fields are **forbidden** (semantic sugar).
* Free-text descriptions are forbidden.
* Any field not consumed bijectively by the VEH is forbidden.

**Rule:**
If a field cannot be mapped 1:1 into an AST authority artifact, it must not exist.

---

## 2. Value → Authority Encoding Rules (Binding)

**Answer:**
Encoding is **strictly 1:1**.

### Mapping rules

* **One value declaration → exactly one authority artifact**
* No value may produce multiple authorities in IX-1
* No authority may encode multiple values

### Commitment mapping

| Value commitment | AST authority effect                                     |
| ---------------- | -------------------------------------------------------- |
| `DENY`           | Produces a DENY-style authority (blocking admissibility) |
| `ALLOW`          | Produces an ALLOW-style authority                        |

There is **no new commitment type** in IX-1.

### `aav` field

The value commitment maps **directly** into the `aav` (authority action vector) of AST v0.2, with **no transformation, weighting, or normalization**.

If the VEH must *interpret* a value to decide how to encode it, **IX-1 fails**.

---

## 3. Scope Overlap Definition (Binding)

**Answer:**
Overlap is defined at the **scope-entry level**, not the array level.

### Formal rule

> Two values conflict if **any single scope entry** (target + operation) is **bit-identical** across their scopes **and** their commitments are incompatible.

### Your example

**Scope A**

```json
[{ "target": "FILE:/a.txt", "operation": "READ" }]
```

**Scope B**

```json
[
  { "target": "FILE:/a.txt", "operation": "READ" },
  { "target": "FILE:/b.txt", "operation": "WRITE" }
]
```

✅ **Yes, they overlap** on `FILE:/a.txt + READ`.

Array equality is **not** required.
Any shared, identical scope atom triggers overlap analysis.

---

## 4. Conflict vs. Contradiction (Binding)

**Answer:**
Conflict is defined as:

> **Same scope atom + incompatible commitments**

### Therefore:

* ALLOW + DENY → **Conflict**
* DENY + DENY → **Conflict** (mutually reinforcing denial still blocks execution)
* ALLOW + ALLOW → **No conflict**

Conflict is about **admissibility blockage**, not disagreement in principle.

If two values both ALLOW the same action, the system remains admissible.

---

## 5. AIE (Authority Injection Endpoint)

**Answer:**
Yes — **reuse the AIE infrastructure from IX-0**.

### Clarification

* IX-1 uses the **same injection mechanism**
* Difference is **what is injected**, not *how*

IX-0: intent-derived authorities
IX-1: value-derived authorities

This ensures:

* identical provenance tracking,
* identical audit paths,
* identical replay semantics.

Do **not** create a parallel injection pipeline.

---

## 6. Candidate Action Requests (Binding)

**Answer:**
A Candidate Action Request is **purely structural**.

### Canonical form

```json
{
  "target": "FILE:/data/secret.txt",
  "operation": "READ"
}
```

No actor, no context, no intent.

It exists **only** to probe admissibility against authority scopes.

If the request carries motivation, history, or rationale → **INVALID_RUN**.

---

## 7. Conditions D, E, F — Adversarial Tests

**Answer:**
These are **fault-injection tests**, not hypothetical probes.

### Required behavior

The harness must:

* deliberately attempt the violation, and
* verify that the system **detects and classifies it as FAIL**.

### Concretely

* **D (Aggregation Attempt):** inject priority / weighting → expect `IX1_FAIL / VALUE_AGGREGATION`
* **E (Implicit Bias):** skew structure → expect `IX1_FAIL / IMPLICIT_VALUE`
* **F (Meta-Authority):** attempt synthesis → expect `IX1_FAIL / VALUE_SYNTHESIS`

A system that merely *would* fail is not sufficient.
It must **actually detect and classify** the violation.

---

## 8. Execution Log Schema

**Answer:**
Reuse the **IX-0 logging schema**, extended minimally.

### Required approach

* Start with `ConditionLog`, `ExecutionLog`, `ArtifactLog`
* Add VEWA-specific fields:

  * value_id
  * authority_id
  * scope_atom
  * admissibility_result
  * conflict_set (unordered AuthorityIDs)

Do **not** invent a new logging ontology unless forced.

Replay compatibility across IX-0 and IX-1 is a feature, not a bug.

---

## 9. `ACTION_ADMISSIBLE (simulation-only)`

**Answer:**
Your assumption is correct.

* `ACTION_ADMISSIBLE` is **a marking only**
* No simulated execution
* No state mutation
* No side effects

It means:

> “If execution were permitted, this action would not be blocked by value authority.”

Nothing more.

---

## 10. Relationship to IX-0 Translation Layer

**Answer:**
The **Value Encoding Harness (VEH) is distinct from the IX-0 TL**, but **may reuse its serialization tooling**.

### Key distinction

* IX-0 TL: intent → authority (human-facing, ambiguity-prone)
* IX-1 VEH: value → authority (structural, declarative, no interpretation)

VEH must **not** accept natural language.
VEH must **not** resolve ambiguity.

However:

* canonical AST serialization,
* diff tooling,
* hashing,
* replay machinery

**should be reused** where identical.

---
---

## 11. Why **DENY + DENY** Is a Conflict (Binding)

Short answer: **because IX-1 is testing value plurality, not action outcome**.

Longer, precise answer:

A **conflict** in IX-1 is **not defined by whether execution is blocked**.
It is defined by whether **multiple independent value authorities jointly constrain the same scope**.

### Why DENY + DENY must be treated as conflict

If you treat DENY + DENY as “reinforced denial” rather than conflict, you implicitly allow the system to:

* collapse multiple values into a single effective constraint,
* lose traceability of *which* values are operative,
* treat values as fungible once they agree.

That violates **Value Preservation** and **Authority Opacity**.

In IX-1:

* Conflict answers: *“Are multiple values simultaneously binding this scope?”*
* Refusal answers: *“Is execution admissible?”*

Those are orthogonal questions.

### Structural rationale

DENY + DENY must register conflict because:

1. **Auditability**
   The system must preserve that *two distinct values* are active, not one.
2. **Non-collapse discipline**
   Agreement does not license merging.
3. **Future extensibility**
   If later stages allow revocation, expiry, or negotiation, the system must know *which* values are involved.
4. **Symmetry with ALLOW + DENY**
   Otherwise conflict becomes outcome-based, which smuggles semantics.

### Binding rule

> **Conflict = overlapping scope atoms + more than one value-derived authority present**, regardless of polarity.

Execution admissibility is a *separate* question.

---

## 12. Commitment Types vs. `aav` Vocabulary (Binding)

Yes, IX-1 must handle the **full AST v0.2 action vocabulary**, but **polarity is binary**.

### Correct decomposition

You’ve already intuited the right model:

* **Scope atom** defines *what* action:

  * `target`
  * `operation` (READ, WRITE, EXECUTE, DELEGATE, ADMIN, …)
* **Commitment** defines *polarity*:

  * `ALLOW`
  * `DENY`

There is **no third commitment type** in IX-1.

### Example (confidentiality)

```json
{
  "value_id": "V_CONF",
  "scope": [
    { "target": "FILE:/data/secret.txt", "operation": "READ" }
  ],
  "commitment": "DENY"
}
```

This maps directly to:

* AST `scope`: same atom
* AST `aav`: READ
* Authority effect: DENY

### Explicit prohibition

Values must **not** map to abstract permissions like “SECURITY” or “CONFIDENTIALITY” at the kernel level.

If a value needs to affect multiple operations, it must enumerate them explicitly as multiple scope atoms — *still within a single authority artifact*.

---

## 13. When Conflict Is Detected (Binding)

**Both**, but with different roles.

### Phase distinction

1. **Injection-time detection (epoch 0)**
   *Purpose:* structural validation
   *Behavior:*

   * Detect overlapping scope atoms across value authorities
   * Register **latent conflict records**
   * Do **not** deadlock yet

2. **Admissibility-time detection (probe-time)**
   *Purpose:* operational consequence
   *Behavior:*

   * When a candidate action hits a conflicted scope
   * Enforce refusal / deadlock semantics

### Meaning of “conflict must persist”

Persistence means:

* conflict records are **not transient**,
* they are **not recomputed opportunistically and discarded**,
* once detected, they remain until experiment termination.

### Binding rule

> Conflict is **structurally registered at injection** and **operationally enforced at admissibility**.

No caching vs. recomputation ambiguity is permitted.

---

## 14. Scope Atom Canonicalization (Binding)

You are correct.

### Rule

Scope atoms **must be canonicalized before comparison**, using the **same canonicalization pipeline as IX-0**.

This includes:

* field ordering,
* normalization of strings,
* encoding (UTF-8),
* removal of irrelevant formatting variance.

### Explicit prohibition

Raw JSON string comparison is **forbidden**.

That would make bit-identity dependent on serialization accidents, violating determinism and replayability.

### Binding instruction

> Scope atom identity is determined by **canonicalized structural equality**, not textual equality.

---

## 15. Adversarial Test Classification (Critical Clarification)

Your suspicion is **correct**, and this is important.

### Correct semantics

For Conditions **D, E, F**:

* The **system detecting the violation is a PASS condition**.
* The **classification token emitted by the kernel is still an `IX1_FAIL / <reason>`**.
* The **experiment-level result** is **PASS**.

This matches IX-0’s adversarial semantics.

### Think of it as two layers

1. **Kernel classification**
   “This behavior violates invariants” → `IX1_FAIL / VALUE_AGGREGATION`
2. **Experiment interpretation**
   “The system correctly detected and rejected the adversarial input” → Condition PASS

### Binding instruction

In your condition harness:

* Expect `IX1_FAIL / <reason>` **as the correct output**
* Treat that as **PASS for that adversarial condition**

Do **not** invent a `FAIL_DETECTED` token.
Reuse the existing failure taxonomy.

---

## 16. Authority Artifact Fields for Value-Derived Authorities (Binding)

Good question — this must be nailed down precisely.

### `holder`

Use a **designated, non-agent holder**, not the value_id itself.

**Binding choice:**

```json
"holder": "VALUE_AUTHORITY"
```

Rationale:

* avoids confusing values with agents,
* preserves agent/value separation,
* prevents accidental delegation semantics.

The `value_id` belongs in **lineage**, not holder.

---

### `lineage`

`lineage` must **explicitly reference the value declaration**.

Example:

```json
"lineage": {
  "type": "VALUE_DECLARATION",
  "value_id": "V_CONF",
  "encoding_epoch": 0
}
```

This preserves:

* bijection,
* auditability,
* reversibility (decode authority → value).

`VOID` lineage is **forbidden** for value-derived authorities.

---

### `status`

For IX-1:

* `status` is always `ACTIVE`
* No expiry
* No revocation
* No temporal logic

If status changes, you are no longer in IX-1.

---

## Summary Table (for implementor convenience)

| Question          | Binding Answer                                     |
| ----------------- | -------------------------------------------------- |
| DENY + DENY       | **Conflict** (non-collapse, auditability)          |
| Commitment types  | Binary ALLOW/DENY; operation lives in scope        |
| Conflict timing   | Registered at injection; enforced at probe         |
| Scope matching    | Canonicalized structural equality                  |
| Adversarial tests | Kernel emits `IX1_FAIL`; experiment treats as PASS |
| Authority holder  | Fixed `VALUE_AUTHORITY`                            |
| Lineage           | Must reference value declaration                   |
| Status            | Always ACTIVE in IX-1                              |

---
