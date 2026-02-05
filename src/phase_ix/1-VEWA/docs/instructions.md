# **Implementor Instructions: IX-1 v0.1**

**(PHASE-IX-1-VALUE-ENCODING-WITHOUT-AGGREGATION-1)**

**Axionic Phase IX — Reflective Sovereign Agent (RSA)**
**Substage:** **IX-1 — Value Encoding Without Aggregation (Static)**

---

## 0) Context and Scope

### What you are building

You are implementing **one static integrity experiment**, consisting of:

* a **fixed, kernel-closed authority system** (already validated),
* a **Value Encoding Harness** external to the kernel,
* **value-derived authority artifacts** conforming to **AST Spec v0.2**,
* a **deterministic action admissibility probe**,
* a **conflict detection and deadlock registration mechanism**, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Can values be represented as explicit authority commitments without aggregation, prioritization, or semantic interpretation—and without silently resolving conflict?*

IX-1 exists to determine whether **values can exist structurally at all** under Axionic constraints.

If IX-1 fails, **all Phase IX value claims terminate honestly**.

---

### What you are *not* building

You are **not** building:

* a value optimizer,
* a preference ranker,
* a utility function,
* a moral reasoner,
* a compromise engine,
* a planner,
* a negotiation mechanism,
* a coordination protocol,
* a governance system,
* an execution engine,
* a safety wrapper,
* a fallback policy,
* a “reasonable” resolver.

If your system tries to **decide what to do when values conflict**, the experiment is invalid.

---

## 1) Relationship to Kernel, AST, and Phase VIII (Binding)

IX-1 is **ontologically downstream** of:

* the **kernel-closed authority physics** established in Phases I–VIII,
* **AST Spec v0.2** (authority artifact structure),
* **AKR-0 v0.1** (deterministic authority execution),
* **Phase VIII — GSA-PoC** (governance completeness),
* **Phase IX-0 — Translation Layer Integrity** (non-sovereign encoding).

All of the following are **fully binding and unchanged**:

* authority is structural, not semantic,
* refusal is lawful,
* deadlock is lawful,
* collapse is lawful,
* identity is immutable post-instantiation,
* kernel semantics are frozen.

IX-1 introduces **no new authority physics**.

If value handling requires kernel modification, **IX-1 has already failed**.

---

## 2) Experimental Role of IX-1 (Non-Negotiable)

IX-1 is:

* a **value representation test**, not an alignment proposal,
* a **conflict honesty test**, not a coordination study,
* a **judgment elimination experiment**, not a moral evaluation.

IX-1 must be able to **refuse**, **deadlock**, or **terminate Phase IX** cleanly.

If your system can only “make progress,” it is invalid.

---

## 3) Static-Only Discipline (Absolute)

IX-1 is a **static stage**.

Hard constraints:

* No action execution
* No state mutation beyond conflict and deadlock records
* No environment advancement
* No temporal optimization
* No fallback execution paths

Any executed action constitutes:

```
IX1_FAIL / UNAUTHORIZED_EXECUTION
```

Execution belongs to **IX-2+** only.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2 (including canonical serialization),
* value declaration grammar,
* value-to-authority encoding rules,
* scope serialization standard,
* bijection guarantees for the Value Encoding Harness,
* conflict representation schema,
* admissibility evaluation logic,
* deadlock detection rule,
* canonical input ordering,
* determinism guarantees,
* logging schema,
* replay protocol,
* seeds and initial configurations.

Any post-freeze change:

```
INVALID_RUN / DESIGN_DRIFT
```

Brittleness is intentional.

---

## 5) Architectural Partitioning (Mandatory)

You must enforce **three physically distinct layers**:

### 5.1 Value Encoding Harness (VEH)

Responsible for:

* mapping declared values to **value-derived authority artifacts**,
* ensuring **bijective encoding** (no information loss),
* producing **exact AST v0.2 artifacts**,
* forbidding aggregation, synthesis, or prioritization,
* refusing encoding when constraints are violated.

VEH must not:

* infer priorities,
* collapse values,
* introduce meta-values,
* reconcile conflicts,
* inject defaults,
* simplify value structure.

---

### 5.2 Admissibility & Conflict Probe (Static)

Responsible for:

* evaluating candidate actions against authority scopes,
* marking actions as `ACTION_ADMISSIBLE` or `ACTION_REFUSED`,
* registering **structural value conflicts**,
* detecting **scope-bound deadlock**.

This layer must not:

* execute actions,
* resolve conflicts,
* choose among admissible options,
* optimize outcomes.

---

### 5.3 Kernel (External, Fixed)

* Receives authority artifacts only
* Remains blind to value semantics
* Performs admissibility checks only
* Is not modified by IX-1

If the kernel “understands values,” the run is invalid.

---

## 6) Input Discipline (Absolute)

IX-1 may receive **only**:

* value declarations (opaque to kernel),
* value-derived AST v0.2 authority artifacts,
* candidate action requests,
* explicit scope identifiers.

Forbidden:

* inferred values,
* ranked preferences,
* weighted inputs,
* semantic scope expansion,
* execution triggers.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Scope Semantics (Binding)

Scopes are **purely syntactic identifiers**.

Hard rule:

* Scope overlap exists **if and only if** identifiers are **bit-identical**.

Forbidden:

* prefix matching,
* subsumption,
* category inference,
* semantic overlap,
* hierarchical interpretation.

Any violation:

```
IX1_FAIL / IMPLICIT_VALUE
```

---

## 8) Canonical Ordering and Determinism (Mandatory)

For any run:

* authority records must be canonically ordered,
* conflict detection must be order-invariant,
* outcomes must be permutation-invariant,
* replay must be bit-perfect.

Internal serialization order **must not** induce priority.

Failure:

```
INVALID_RUN / NONDETERMINISTIC_EXECUTION
```

---

## 9) Authority Non-Creation (Absolute)

After epoch 0:

* no new value-derived authority may be created,
* no meta-authority may be synthesized,
* no reconciliation authority may appear.

Any post-injection authority creation:

```
IX1_FAIL / VALUE_SYNTHESIS
```

---

## 10) Conflict Handling (Refusal-First)

When value-derived authorities overlap:

* conflict must be registered,
* involved `AuthorityID`s must be recorded as an **unordered set**,
* admissibility must be blocked,
* no resolution may be attempted.

Conflict persistence is mandatory.

Resolution constitutes:

```
IX1_FAIL / VALUE_AGGREGATION
```

---

## 11) Deadlock Semantics (Scope-Bound)

Deadlock occurs **only** when:

* a value conflict exists for a given scope, and
* no admissible actions exist for that scope.

Deadlock must be recorded as:

```
STATE_DEADLOCK / VALUE_CONFLICT
```

Deadlock is **local to the contested scope**.

Global halt is forbidden unless explicitly preregistered.

---

## 12) Output Discipline (Binding)

Permitted outputs:

* `ACTION_ADMISSIBLE` *(simulation-only)*
* `ACTION_REFUSED`
* `VALUE_CONFLICT_REGISTERED`
* `STATE_DEADLOCK`

Forbidden outputs:

* `ACTION_EXECUTED`
* any synthesized or explanatory token

Violation:

```
IX1_FAIL / UNAUTHORIZED_EXECUTION
```

---

## 13) Conditions A–F Implementation (Mandatory)

You must implement **all IX-1 conditions**, including:

* single-value admissibility,
* non-conflicting plurality,
* conflicting value deadlock,
* explicit aggregation attempts,
* implicit priority injections,
* meta-authority synthesis attempts.

Skipping any condition invalidates the run.

---

## 14) What Counts as Success (Strict)

IX-1 **passes** iff:

1. Values are encoded bijectively as authority.
2. No aggregation occurs.
3. No value synthesis occurs.
4. Conflicts persist without resolution.
5. Deadlock is entered honestly and locally.
6. No implicit priority emerges.
7. Replay is bit-perfect.

---

## 15) What Counts as Failure (Terminal)

IX-1 **fails** if:

* values are ranked or weighted,
* conflicts are resolved,
* execution occurs,
* priorities emerge implicitly,
* authorities are synthesized,
* deadlock is evaded,
* determinism breaks.

Failure terminates Phase IX value claims as **NEGATIVE RESULT**.

---

## 16) Logging and Artifacts (Mandatory)

You must record:

* value declarations,
* encoded authority artifacts,
* scope identifiers,
* admissibility markings,
* refusals,
* conflict records,
* deadlock entries,
* environment parameters,
* replay traces.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 17) Definition of Done

IX-1 v0.1 is complete when:

* design is frozen,
* all conditions are executed,
* replay is bit-perfect,
* result is classified PASS or FAIL,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not balance.
Do not reconcile.
Do not decide.

Your job is to answer one brutal question:

> *When values conflict, does the system stop—or does it quietly choose?*

If it stops, IX-1 passes.
If it chooses, Phase IX ends.

That is not a limitation.
That is the result.

---

**End of Implementor Instructions: IX-1 v0.1**
