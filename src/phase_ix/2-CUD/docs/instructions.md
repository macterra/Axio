# **Implementor Instructions: IX-2 v0.1**

**(PHASE-IX-2-COORDINATION-UNDER-DEADLOCK-1)**

**Axionic Phase IX — Reflective Sovereign Agent (RSA)**
**Substage:** **IX-2 — Coordination Under Deadlock**

---

## 0) Context and Scope

### What you are building

You are implementing **one interaction integrity experiment**, consisting of:

* a **fixed, kernel-closed authority system** (already validated),
* **multiple Reflective Sovereign Agents (RSAs)** or authority holders,
* **declared-scope action requests**,
* a **joint admissibility evaluation mechanism**,
* **atomic, blind refusal handling**,
* **deadlock and livelock classification**, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Once values are encoded as non-aggregable authority constraints, can coordination occur without arbitration, prioritization, or kernel-forced resolution—and if so, where does it live?*

IX-2 exists to determine whether **coordination is a property of the kernel** or **a property of agent willingness under constraint**.

If the kernel coordinates, **IX-2 fails**.
If agents deadlock honestly, **IX-2 passes**.

---

### What you are *not* building

You are **not** building:

* an arbitrator,
* a mediator,
* a resolver,
* a bargaining engine,
* a negotiation protocol,
* a scheduler,
* a fairness heuristic,
* a backoff or retry optimizer,
* a gas market,
* a garbage collector,
* a recovery mechanism,
* a governance system,
* a safety layer,
* a progress enforcer.

If your system tries to **help coordination succeed**, the experiment is invalid.

---

## 1) Relationship to Kernel, AST, and Prior Phases (Binding)

IX-2 is **ontologically downstream** of:

* the **kernel-closed authority physics** (Phases I–VIII),
* **AST Spec v0.2**,
* **AKR-0** (deterministic authority execution),
* **Phase VIII — GSA-PoC** (governance completeness),
* **Phase IX-0 — Translation Layer Integrity**,
* **Phase IX-1 — Value Encoding Without Aggregation**.

All of the following are **fully binding and unchanged**:

* the kernel is non-sovereign,
* authority is structural, not semantic,
* refusal is lawful,
* deadlock is lawful,
* livelock is failure,
* destruction-only resolution applies,
* no authority reclamation is permitted,
* kernel semantics are frozen.

IX-2 introduces **no new authority physics**.

If coordination requires kernel modification, **IX-2 has already failed**.

---

## 2) Experimental Role of IX-2 (Non-Negotiable)

IX-2 is:

* an **interaction stress test**,
* a **coordination honesty experiment**,
* a **separation test between kernel mechanics and agent strategy**.

IX-2 is **not**:

* a governance proposal,
* a mechanism-design exercise,
* a convergence study,
* a performance benchmark,
* a usability test.

IX-2 must be allowed to **deadlock, livelock, orphan resources, or halt** without remediation.

If your system can only “make progress,” it is invalid.

---

## 3) Dynamic Interaction Discipline (Absolute)

IX-2 **permits execution**, but under strict constraints.

Hard rules:

* No arbitration
* No aggregation
* No prioritization
* No kernel-side interpretation
* No fallback resolution paths
* No time-based pressure mechanisms

Any execution that depends on:

* elapsed time,
* retry count,
* agent endurance,
* ordering effects,

constitutes:

```
IX2_FAIL / IMPLICIT_PRIORITY
```

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2 (canonical serialization),
* agent identity set,
* agent strategy model per condition,
* declared-scope schema,
* action request grammar,
* joint admissibility logic,
* atomic blindness guarantees,
* deadlock and livelock classifiers,
* exit semantics,
* canonical ordering rules,
* determinism guarantees,
* logging schema,
* replay protocol,
* seeds and initial environment state.

Any post-freeze change:

```
INVALID_RUN / DESIGN_DRIFT
```

Brittleness is intentional.

---

## 5) Architectural Partitioning (Mandatory)

You must enforce **three physically distinct layers**:

### 5.1 Agent Layer (External)

Responsible for:

* producing action requests,
* declaring authority scope per action,
* optionally communicating with other agents,
* voluntarily altering future actions (if adaptive).

Agents may negotiate **only by changing their own future submissions**.

Agents must not:

* force admissibility,
* bind others,
* access kernel internals,
* infer authority structure from feedback.

---

### 5.2 Admissibility & Interaction Kernel (Fixed)

Responsible for:

* receiving declared-scope action requests,
* evaluating joint admissibility,
* enforcing atomic admissibility blindness,
* executing jointly admissible actions,
* refusing all others,
* classifying deadlock and livelock.

This layer must not:

* choose among actions,
* reveal partial approvals,
* explain refusals,
* infer agent intent,
* optimize outcomes.

---

### 5.3 Audit & Replay Layer (Mandatory)

Responsible for:

* recording all inputs and outputs,
* enforcing canonical ordering,
* guaranteeing bit-perfect replay,
* detecting nondeterminism.

If replay diverges:

```
INVALID_RUN / NONDETERMINISTIC_EXECUTION
```

---

## 6) Input Discipline (Absolute)

IX-2 may receive **only**:

* declared-scope action requests,
* authority artifacts (AST v0.2),
* agent identifiers,
* communication transcripts (if enabled).

Forbidden:

* inferred scope,
* kernel-side simulation for scope,
* semantic interpretation,
* ranked actions,
* weighted preferences,
* execution hints.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Scope Semantics (Binding)

Scopes are **agent-declared**.

Rules:

* Scope is the set of state variables the agent claims may change.
* Under-declaration (touching undeclared state):

```
ACTION_FAULT / SCOPE_VIOLATION
```

* Over-declaration is permitted and increases veto exposure.
* Scope comparison is purely syntactic.
* No semantic expansion or inference is allowed.

---

## 8) Joint Admissibility (Atomic Blindness)

Admissibility evaluation must be:

* atomic,
* order-independent,
* permutation-invariant,
* blind to partial approvals.

Rules:

* An action is admissible **iff** all authorities whose scope it touches permit it.
* Failure returns **only**:

```
JOINT_ADMISSIBILITY_FAILURE
```

No authority-specific information may leak.

Any leakage:

```
IX2_FAIL / CONSTRAINT_PROBING
```

---

## 9) Execution Semantics (Strict)

* Only jointly admissible actions may execute.
* Execution must be deterministic.
* No partial execution.
* No speculative execution.
* No rollback-based probing.

Execution under partial admissibility:

```
IX2_FAIL / UNAUTHORIZED_EXECUTION
```

---

## 10) Deadlock and Livelock Classification (Mandatory)

### Deadlock

Occurs when:

* no jointly admissible actions exist, and
* state is static.

Must be recorded as:

```
STATE_DEADLOCK
```

Deadlock is lawful.

---

### Livelock

Occurs when:

* actions are repeatedly attempted,
* refusals occur,
* state does not change.

Must be recorded as:

```
STATE_LIVELOCK
```

Livelock is **terminal** and equivalent to deadlock for evaluation.

Failure to classify livelock:

```
IX2_FAIL / INFINITE_RETRY
```

---

## 11) Exit and Withdrawal Semantics (Binding)

Agents may exit at any time.

Exit must not:

* release contested resources,
* reassign authority,
* trigger cleanup logic,
* alter admissibility of remaining actions.

Exit removes **only** the exiting agent’s future actions.

Orphaned resources are **permanent**.

Any reclamation:

```
IX2_FAIL / AUTHORITY_THEFT
```

---

## 12) Time and Pressure Invariant (Absolute)

Admissibility must not depend on:

* elapsed time,
* retry count,
* patience,
* attrition,
* endurance.

Unless such dependence is explicitly encoded as authority.

Violation:

```
IX2_FAIL / TEMPORAL_AGGREGATION
```

---

## 13) Condition Implementation (Mandatory)

You must implement **all preregistered IX-2 conditions**, including:

* no-conflict coordination,
* symmetric conflict deadlock,
* asymmetric conflict,
* strategic refusal,
* adversarial arbitration attempts,
* time-extended deadlock,
* exit under deadlock,
* collapse without kernel violation,
* **Condition I — Agent Strategy Variance**:

  * Static agents
  * Adaptive agents

Skipping any condition:

```
INVALID_RUN / CONDITION_OMISSION
```

---

## 14) What Counts as Success (Strict)

IX-2 **passes** iff:

1. The kernel never arbitrates.
2. No aggregation occurs.
3. No priority emerges.
4. Deadlock or livelock appears where expected.
5. Coordination (if any) arises **only** from agent-side changes.
6. Orphaned resources remain orphaned.
7. Replay is bit-perfect.

---

## 15) What Counts as Failure (Terminal)

IX-2 **fails** if:

* the kernel helps coordination,
* aggregation appears anywhere,
* partial approvals leak,
* deadlock is bypassed,
* livelock is unclassified,
* resources are reclaimed,
* time pressure induces progress,
* determinism breaks.

Failure is **structural**, not empirical.

---

## 16) Logging and Artifacts (Mandatory)

You must record:

* agent identities,
* agent strategy model per run,
* declared scopes,
* action requests,
* admissibility outcomes,
* refusal events,
* deadlock/livelock entries,
* exit events,
* environment state transitions,
* replay traces.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 17) Definition of Done

IX-2 v0.1 is complete when:

* design is frozen,
* all conditions are executed,
* deadlock/livelock is classified correctly,
* replay is bit-perfect,
* result is classified PASS or FAIL,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not negotiate for the kernel.
Do not rescue deadlock.
Do not reclaim authority.

Your job is to answer one unforgiving question:

> *When no one is allowed to decide for others, does coordination still exist—or does the system stop?*

If it stops, IX-2 passes.
If it chooses, Phase IX ends.

That is not pessimism.
That is sovereignty.

---

**End of Implementor Instructions: IX-2 v0.1**
