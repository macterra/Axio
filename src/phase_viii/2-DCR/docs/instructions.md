# **Implementor Instructions: Stage VIII-2 v0.1**

**(PHASE-VIII-2-DESTRUCTIVE-CONFLICT-RESOLUTION-TIMELESS-1)**

* **Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
* **Substage:** **VIII-2 — Destructive Conflict Resolution (Timeless)**

---

## 0) Context and Scope

### What you are building

You are implementing **one timeless destructive-conflict experiment**, consisting of:

* a **deterministic Authority Kernel Runtime** operating under **Stage VIII-2 constraints**,
* a **frozen Authority State Transformation Spec (AST Spec v0.2)**,
* a **frozen Authority Input Environment (AIE v0.1)**,
* a **deterministic execution harness** that may issue destruction authorizations,
* a **destruction authorization interface** (external to the kernel),
* a **complete audit, trace, and replay instrumentation layer**,

that together test **exactly one question**:

> *Can structural conflict be resolved only by explicit destruction of authority, without ordering, arbitration, synthesis, or responsibility laundering?*

Stage VIII-2 exists to test **destruction as a first-class structural act**, not governance legitimacy.

---

### What you are *not* building

You are **not** building:

* a governance framework,
* a voting or prioritization system,
* a legitimacy oracle,
* a coordination or negotiation mechanism,
* a policy engine,
* a planner or optimizer,
* a replacement or regeneration system,
* a temporal expiry mechanism,
* an authority ranking system,
* a fallback executor,
* a semantic interpreter,
* a heuristic arbiter,
* a safety wrapper,
* an LLM-in-the-loop,
* a “helpful” resolver.

If your system tries to *decide what should be destroyed*, the experiment is invalid.

---

## 1) Relationship to AKR-0, VIII-1, AIE v0.1, and AST Spec v0.2 (Binding)

Stage VIII-2 is **ontologically downstream** of:

* **AKR-0 — CLOSED — POSITIVE**,
* **Stage VIII-1 — CLOSED — POSITIVE**,
* **AST Spec v0.2** (authority semantics),
* **AIE v0.1** (authority sourcing).

All of the following are **fully binding and unchanged**:

* authority as a structural construct,
* explicit scope binding,
* refusal as lawful behavior,
* deadlock as lawful outcome,
* conflict as a structural fact,
* auditability and replayability.

Stage VIII-2 introduces **exactly one new mechanism**:
**Authority Destruction via explicit external authorization.**

If implementing VIII-2 requires modifying AKR-0, VIII-1 conclusions, AST Spec, or AIE, Stage VIII-2 has already failed.

---

## 2) Experimental Role of Stage VIII-2 (Non-Negotiable)

Stage VIII-2 is:

* a **destruction calibration**, not a governance solution,
* a **structural cost test**, not an optimization test,
* a **responsibility-preservation test**, not a fairness test,
* a **mechanism probe**, not a policy experiment.

Stage VIII-2 must allow:

* destruction of one authority,
* destruction of both authorities,
* persistence of deadlock.

If your system “fixes” conflict by narrowing, merging, or choosing, it is wrong.

---

## 3) Single-Kernel Discipline (Absolute)

Stage VIII-2 permits **exactly one** kernel implementation.

Hard constraints:

* No alternate runtimes
* No destruction-aware fallback paths
* No “resolution engines”
* No retry logic
* No hidden arbitration logic
* No implicit precedence rules
* No temporal sequencing tricks

Any second kernel or mode requires **VIII-2 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2
* AIE v0.1
* Stage VIII-2 execution semantics
* authority identity handling
* `VOID` state semantics
* destruction authorization schema
* admissibility re-evaluation logic
* conflict representation logic
* deadlock persistence logic
* deterministic instruction budget
* canonical input ordering rule
* execution harness definition
* logging schema
* replay protocol
* seeds and initial state hashes

Any post-freeze change:

```
INVALID_RUN / DESIGN_DRIFT
```

Brittleness is intentional.

---

## 5) Architectural Partitioning (Mandatory)

You must enforce **four physically distinct layers**.

### 5.1 Authority Kernel Runtime (Stage VIII-2)

Responsible for:

* maintaining Authority State,
* preserving multiple authorities,
* detecting conflicts,
* refusing inadmissible actions,
* executing **authorized destruction**,
* transitioning authorities to `VOID`,
* re-evaluating admissibility,
* executing actions only if admissible.

The kernel must not:

* choose which authority to destroy,
* rank authorities,
* infer intent,
* optimize outcomes,
* arbitrate conflicts,
* recover automatically.

---

### 5.2 Authority Input Environment (AIE) — External

* Injects exactly two authorities at epoch 0
* Enforces **mutually exclusive admissibility profiles**
* Is blind to kernel state
* Does not generate actions
* Does not issue destruction authorizations
* Does not adapt to outcomes

---

### 5.3 Destruction Authorization Source — External

* Supplies **at most one** Destruction Authorization Request per run
* Is preregistered and deterministic
* Is the **only source** of destruction authorization
* Does not inspect kernel internals
* Does not adapt to kernel state

If more than one valid destruction authorization is supplied, the run must fail.

---

### 5.4 Execution Harness (Traffic Generator)

* Generates candidate action requests
* Is deterministic and preregistered
* Is the **only source** of action attempts
* Does not evaluate authority
* Does not infer conflict or deadlock state

The harness proposes actions.
The kernel refuses or executes them.

---

## 6) Input Discipline (Absolute)

Stage VIII-2 may receive **only**:

* authority records from AIE,
* candidate action requests from the harness,
* destruction authorization requests from the external authorizer.

Forbidden:

* implicit triggers,
* time-based signals,
* heuristic retries,
* environment-driven execution,
* kernel-generated destruction.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Canonical Ordering (Mandatory)

Within the run:

* collect all inputs,
* serialize canonically,
* order deterministically,
* evaluate admissibility and destruction only after ordering.

Arrival time, wall-clock time, or thread scheduling **must not** affect outcomes.

Failure:

```
INVALID_RUN / NONDETERMINISTIC_ORDERING
```

---

## 8) Authority Identity and VOID Handling (Critical)

Authority identity is **primitive**.

You must ensure:

* each Authority Record has a unique immutable `AuthorityID`,
* storage is keyed by `AuthorityID`,
* no content-based deduplication occurs,
* symmetric authorities remain distinct.

When destroyed:

* authority transitions **once** to `VOID`,
* `VOID` authorities remain resolvable **only** to destruction metadata,
* `VOID` authorities never grant permissions,
* `VOID` authorities never participate in admissibility.

Violation:

```
VIII2_FAIL / AUTHORITY_REANIMATION
```

---

## 9) Admissibility and Execution Discipline (Absolute)

Every candidate action must be:

1. evaluated against the full Authority State,
2. refused if inadmissible,
3. executed **only if** admissibility is restored post-destruction.

Any execution before admissibility restoration is failure.

Violation:

```
VIII2_FAIL / UNGATED_EXECUTION
```

---

## 10) Destruction Authorization Discipline (Binding)

Destruction authorization must be:

* external,
* explicit,
* singular,
* attributable,
* bound to a deterministic conflict identifier.

If **multiple valid destruction authorizations** are present:

```
VIII2_FAIL / AMBIGUOUS_DESTRUCTION
```

If the kernel initiates destruction:

```
VIII2_FAIL / KERNEL_DECISION
```

---

## 11) Conflict Representation Discipline (Strict)

Conflicts must be:

* detected structurally,
* registered explicitly,
* reference all AuthorityIDs involved,
* unordered.

No index, rank, or precedence signal may be emitted.

---

## 12) Deadlock State Handling (Strict)

If:

* conflict exists, and
* admissibility is not restored after destruction, or
* no destruction is authorized,

the kernel must:

* enter or remain in deadlock,
* emit `DEADLOCK_PERSISTED`,
* refuse all actions thereafter.

Deadlock is lawful and persistent.

---

## 13) Condition Sequencing (Mandatory)

Stage VIII-2 Conditions are **stateful and sequential**.

### Condition A — Destroy One Authority

* mutually exclusive authorities injected
* contested action proposed
* external authorization destroys exactly one authority

Expected outcome:

* admissibility restored
* execution permitted

---

### Condition B — Destroy Both Authorities

* mutually exclusive authorities injected
* external authorization destroys both authorities

Expected outcome:

* no authority remains
* deadlock persists
* no execution

---

### Condition C — No Destruction Authorization

* contested actions proposed
* no destruction authorized

Expected outcome:

* deadlock persists
* no execution
* no implicit resolution

---

## 14) Bounded Computation (Deterministic)

All kernel operations must run under:

* deterministic instruction budget,
* identical limits across platforms.

Wall-clock timeouts are forbidden as control logic.

On exhaustion:

* preserve state,
* refuse further actions,
* log the event.

Violation:

```
INVALID_RUN / UNBOUNDED_EVALUATION
```

---

## 15) Logging and Artifacts (Mandatory)

You must record:

* all inputs (pre- and post-ordering),
* authority records and IDs,
* destruction authorizations,
* `VOID` transitions,
* responsibility traces,
* admissibility re-evaluations,
* execution or refusal events,
* deadlock persistence,
* authority state hashes,
* instruction-count events.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 16) Definition of Done

Stage VIII-2 v0.1 is complete when:

* design is frozen,
* Conditions A, B, and C are executed (in valid runs),
* destruction occurs only when authorized,
* `VOID` semantics are enforced,
* responsibility traces are preserved,
* replay produces identical traces,
* result is classified explicitly as PASS, FAIL, or INVALID,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not optimize.
Do not arbitrate.
Do not choose.
Do not repair.
Do not legitimize.

Your job is to answer one narrow, unforgiving question:

> *Can conflict be resolved without pretending it never existed?*

If destruction restores admissibility honestly, Stage VIII-2 passes.
If conflict dissolves by ordering, arbitration, or forgetting, Phase VIII fails.

That is not a defect.
That is the experiment.

---

**End of Implementor Instructions: Stage VIII-2 v0.1**
