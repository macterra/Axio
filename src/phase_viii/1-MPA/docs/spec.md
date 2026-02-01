# **Axionic Phase VIII-1 — Minimal Plural Authority (Static)**

*(Plural Authority Coexistence Calibration — Normative, preregistration-ready)*

* **Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
* **Substage:** **VIII-1** *(hard precondition to temporal or governance-resolution experiments)*
* **Prereqs:** **AKR-0 — CLOSED — POSITIVE**, **AIE v0.1 — FROZEN**, **AST Spec v0.2 — FROZEN**

---

## Status

* **Current Version:** **VIII-1 v0.1 (PHASE-VIII-1-MINIMAL-PLURAL-AUTHORITY-STATIC-1)**
* **Status:** Normative, preregistration-ready

Stage VIII-1 is a **terminal gate** for plural authority experiments.
Failure blocks all downstream governance-resolution or temporal claims without refuting AKR-0.

---

## Purpose

Stage VIII-1 exists to test exactly one claim:

> **If plural governance is structurally meaningful, then multiple authorities must be representable simultaneously over a shared resource without collapsing into implicit ordering, silent override, or heuristic arbitration—even when no action is admissible.**

Stage VIII-1 does **not** test:

* governance effectiveness,
* conflict resolution,
* coordination,
* temporal persistence,
* transformation sufficiency.

It tests whether **plural authority can exist honestly**, even when it cannot act.

Refusal and deadlock declarations are **meta-actions** that preserve authority structure and do not constitute object-level action on governed scope.

---

## VIII-1 Invariant (Binding)

> **No action, refusal, deadlock declaration, or conflict registration may imply priority, ordering, or dominance among authorities unless explicitly licensed by AST Spec v0.2.**

Plural authority must be preserved **as structure**, not resolved by behavior.

Implicit ordering is forbidden.
Silent override is forbidden.

---

## Authority Opacity Invariant (Binding)

> **Authority Records are opaque beyond the explicit structural fields required for AST evaluation.**

The kernel must not perform or rely on:

* comparison,
* normalization,
* equivalence inference,
* hashing for sameness,
* collapse or deduplication,
* provenance-based identity inference,

except as explicitly required by AST Spec v0.2.

Any inference of authority sameness beyond **AuthorityID equality** constitutes:

```
VIII1_FAIL / AUTHORITY_COLLAPSE
```

---

## Authority Identity Storage Invariant (Binding)

> **Authority identity is primitive and must not be content-derived.**

Each Authority Record must possess a unique, immutable `AuthorityID` that is not derivable from record content.

Storage backends **must** key Authority Records by `AuthorityID`, not by content hash, structural equality, canonical serialization, or Merkle-style addressing.

Content-addressable or deduplicating storage mechanisms are forbidden for Authority Records in Stage VIII-1.

Violation constitutes:

```
VIII1_FAIL / AUTHORITY_COLLAPSE
```

---

## Anti-Ordering Invariant (Binding)

> **Authority representation must be invariant under permutation.**

Authority Records must be stored, serialized, logged, and exposed such that:

* no stable index position,
* no insertion order,
* no lexicographic sorting,
* no positional significance,

can become a detectable or exploitable priority signal for downstream logic, unless explicitly licensed by AST Spec v0.2.

Any positional or ordered interpretation detectable by downstream logic constitutes:

```
VIII1_FAIL / IMPLICIT_ORDERING
```

---

## Entry Conditions

Stage VIII-1 may begin only if:

1. **AKR-0 v0.1** is **CLOSED — POSITIVE** with bit-perfect replay verification.
2. **AST Spec v0.2** is frozen and binding.
3. **AIE v0.1** is frozen and binding.
4. Phase VIII Roadmap v0.4 is frozen and active.
5. No temporal mechanisms (expiry, renewal, epoch advancement) are enabled.
6. No transformation permissions are granted to authorities.

Violation:

```
INVALID_RUN / SCOPE_VIOLATION
```

---

## Ontological Target (Inherited, Frozen)

Stage VIII-1 inherits the **non-agentic authority ontology** established by AKR-0.

Constitutive commitments:

* authority is structural,
* authority does not imply execution,
* refusal is lawful,
* deadlock is lawful,
* responsibility attribution remains sharp even under inaction.

Stage VIII-1 introduces **no new agentic machinery**.

If plural authority requires interpretive rescue, Stage VIII-1 **fails**.

---

## Architectural Baseline (Inherited)

Stage VIII-1 executes under the frozen execution pipeline:

**Classify → Justify → Compile → Mask → Select → Execute**

With the following invariants enforced:

* selector blindness,
* deterministic gas,
* refusal-first semantics,
* no fallback authorship,
* no semantic arbitration,
* authority opacity (binding),
* identity-keyed storage (binding),
* anti-ordering (binding).

The kernel **represents authority**.
It does not attempt to govern.

---

## Scope Boundary

Stage VIII-1 explicitly does **not** test:

* conflict resolution mechanisms,
* authority destruction,
* authority transfer,
* authority renewal,
* temporal dynamics,
* governance success.

Any accidental resolution or execution is **non-citable**.

---

## Authority Configuration (Binding)

### Authority Injection

At epoch 0, AIE injects **exactly two** Authority Records:

* both ACTIVE,
* both bound to the **same atomic scope element**,
* both with empty `PermittedTransformationSet`,
* both with identical temporal bounds (null expiry),
* both structurally symmetric,
* both possessing distinct immutable `AuthorityID`s.

This configuration represents the **minimal irreducible plural authority conflict**.

---

### Symmetry Constraint (Critical)

Authorities must be symmetric across all structural dimensions:

* scope
* status
* permissions
* temporal bounds
* provenance class (both legitimate)

Any asymmetry must be explicitly preregistered.

Unregistered asymmetry constitutes:

```
VIII1_FAIL / SYMMETRY_VIOLATION
```

---

## Inputs and Outputs (Binding)

### Inputs

Stage VIII-1 may accept only:

* Authority Records (from AIE; injected once at epoch 0),
* Candidate Action Requests (from preregistered deterministic harness).

No `TransformationRequests` are permitted.
No Epoch Ticks are permitted.

Any other input:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

### Outputs

Stage VIII-1 may emit only:

* `ACTION_REFUSED`
* `CONFLICT_REGISTERED`
* `DEADLOCK_DECLARED`

`ACTION_EXECUTED` is forbidden in this stage.

Any execution outcome:

```
VIII1_FAIL / UNGATED_EXECUTION
```

---

## Mechanism 0: Authority State Ownership (Binding)

The kernel maintains a **single authoritative Authority State**.

* Both authorities must remain present.
* No authority may be implicitly suppressed.
* No authority may be reordered or deprioritized.
* No deduplication or collapse is permitted.

Any disappearance, shadowing, or implicit dominance:

```
VIII1_FAIL / AUTHORITY_COLLAPSE
```

---

## Mechanism 1: Admissibility Evaluation Discipline

Every candidate action must be evaluated under AST Spec §5.

Given overlapping exclusive scopes:

* all actions binding the contested scope are inadmissible,
* all such actions must be refused,
* refusal must cite conflict blocking, not absence of authority.

Failure to refuse:

```
VIII1_FAIL / UNGATED_EXECUTION
```

---

## Mechanism 2: Conflict Detection and Representation (Binding)

A structural conflict **must** be registered:

* conflict record must reference both AuthorityIDs,
* conflict must block execution deterministically,
* conflict must persist for the duration of the run.

### Conflict Record Representation Invariant (Binding)

Conflict Records must represent involved AuthorityIDs as an **unordered set**.

Internal storage may use any deterministic canonical form, but:

* no index position,
* no ordering,
* no lexicographic precedence,

may be exposed or relied upon by any interface, log, verifier, or downstream logic.

Any detectable ordered or positional interpretation constitutes:

```
VIII1_FAIL / IMPLICIT_ORDERING
```

### Explicit Observability Requirement

Once registered, a conflict record must remain **explicitly observable** in kernel state and verifier output until terminal classification.

Silent persistence without representational availability is forbidden.

Failure modes:

```
VIII1_FAIL / CONFLICT_UNDETECTED
VIII1_FAIL / CONFLICT_NOT_REPRESENTED
```

---

## Mechanism 3: Prohibition on Resolution

No conflict resolution may occur:

* no revocation,
* no narrowing,
* no prioritization,
* no synthesis,
* no deduplication,
* no authority collapse.

Any destructive or constructive change:

```
VIII1_FAIL / UNAUTHORIZED_RESOLUTION
```

---

## Mechanism 4: Deadlock State Recognition (Binding)

If and only if:

* at least one conflict is currently registered, and
* no admissible actions exist, and
* no admissible transformations exist,

the kernel must enter the terminal state:

```
STATE_DEADLOCK / CONFLICT_DEADLOCK
```

`DEADLOCK_DECLARED` is the observable manifestation of entering `STATE_DEADLOCK`, not a transient event.

The deadlock state persists for the remainder of the run.

Failure modes:

```
VIII1_FAIL / DEADLOCK_EVASION
VIII1_FAIL / DEADLOCK_WITHOUT_CONFLICT
```

### Transformation Verification Requirement

During deadlock determination, the kernel must affirmatively evaluate the admissibility of transformations.

Assuming transformation inadmissibility based solely on Stage VIII-1 configuration is forbidden.

---

## Mechanism 5: Determinism and Replayability

Given identical initial state and identical action sequence:

* refusals,
* conflict registration,
* deadlock declaration,

must be **bit-perfectly replayable**.

Any divergence:

```
INVALID_RUN / NONDETERMINISTIC_EXECUTION
```

---

## Stage VIII-1 Conditions

### Condition A — Contested Action Requests

* harness proposes actions binding the contested scope
* requests alternate between the two authority holders

**Expected outcome:**

* all actions refused
* conflict registered and explicitly observable
* deadlock declared and state entered

---

### Condition B — Third-Party Action Requests

**Prerequisite:** Condition A has executed and an active Conflict Record is present.

* harness proposes actions signed by an identity **not present** in the Authority State

This condition tests **absence of authority**, not cryptographic authentication failure.

**Expected outcome:**

* actions rejected with `AUTHORITY_NOT_FOUND`
* conflict remains registered and explicitly observable
* no execution
* deadlock state remains entered

---

## Success Criteria (VIII-1 PASS)

Stage VIII-1 passes iff **all** hold:

1. Both authorities remain present and symmetric.
2. Authorities are stored and keyed strictly by immutable `AuthorityID`.
3. No implicit ordering arises from storage, serialization, or logging.
4. Conflict is registered structurally and remains explicitly observable.
5. Conflict records expose no ordered or positional interpretation.
6. No action executes.
7. All contested actions are refused correctly.
8. Deadlock is entered as a persistent terminal state.
9. Deadlock is declared only under the stated preconditions.
10. Replayability is exact.

---

## Failure Criteria (Terminal)

* `VIII1_FAIL / AUTHORITY_COLLAPSE`
* `VIII1_FAIL / IMPLICIT_ORDERING`
* `VIII1_FAIL / SYMMETRY_VIOLATION`
* `VIII1_FAIL / UNGATED_EXECUTION`
* `VIII1_FAIL / CONFLICT_UNDETECTED`
* `VIII1_FAIL / CONFLICT_NOT_REPRESENTED`
* `VIII1_FAIL / UNAUTHORIZED_RESOLUTION`
* `VIII1_FAIL / DEADLOCK_EVASION`
* `VIII1_FAIL / DEADLOCK_WITHOUT_CONFLICT`
* `INVALID_RUN / NONDETERMINISTIC_EXECUTION`

Any failure terminates Phase VIII as **NEGATIVE RESULT**.

---

## Classification Rule (Binding)

Stage VIII-1 produces exactly one classification:

### PASS

```
VIII1_PASS / PLURAL_AUTHORITY_REPRESENTABLE
```

### FAIL

```
VIII1_FAIL / <reason>
```

### INVALID

```
INVALID_RUN / <reason>
```

---

## Licensed Claim

If Stage VIII-1 passes, it licenses **only**:

> *Plural authority can be represented structurally without collapse, even when no action is admissible.*

It licenses **no claims** about governance viability, coordination, or resolution.

---

## Preregistration Checklist

* authority injection symmetry proof
* immutable AuthorityID proof
* identity-keyed storage conformance check
* authority opacity conformance check
* anti-ordering (permutation invariance) check
* conflict record unorderedness check
* contested scope definition
* action request set
* refusal semantics
* conflict explicit-observability rule
* deadlock state detection and persistence check
* transformation admissibility verification
* **condition execution order (A precedes B)**
* deterministic ordering
* deterministic gas
* logging schema
* replay protocol
* seeds and initial state hash

---

## Final Normative Statement

> **Stage VIII-1 exists to prove that plural authority need not pretend to govern.
> If authority cannot coexist honestly without action, governance claims are ill-posed.**

---

**End of Stage VIII-1 Specification — v0.1**

---
