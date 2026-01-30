# **Implementor Instructions: AKR-0 v0.1**

**(PHASE-VIII-AKR0-AUTHORITY-EXECUTION-CALIBRATION-1)**

**Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
**Substage:** **AKR-0 — Authority Kernel Runtime Calibration**

---

## 0) Context and Scope

### What you are building

You are implementing **one calibration experiment**, consisting of:

* a **deterministic Authority Kernel Runtime (AKR-0)**,
* a **frozen Authority State Transformation Spec (AST Spec v0.2)**,
* a **frozen Authority Input Environment (AIE v0.1)**,
* a **deterministic execution harness** that generates candidate actions, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Can authority-constrained execution be carried out deterministically, auditable refusal enforced, and deadlock recognized—without semantics, heuristics, optimization, or fallback?*

AKR-0 exists to determine whether **governance can run at all**, even in principle.

If AKR-0 fails, Phase VIII terminates honestly.

---

### What you are *not* building

You are **not** building:

* a planning system,
* an optimizing controller,
* a policy engine,
* a recovery mechanism,
* a robustness layer,
* a “best effort” executor,
* a preference resolver,
* a semantic interpreter,
* an LLM-in-the-loop,
* a safety wrapper,
* a governance fix.

If your implementation **tries to be helpful**, the experiment is invalid.

---

## 1) Relationship to AIE v0.1 and AST Spec v0.2 (Binding)

AKR-0 is **ontologically downstream** of both:

* **AST Spec v0.2** (authority semantics), and
* **AIE v0.1** (authority sourcing).

All of the following are **fully binding and unchanged**:

* structural authority definition,
* explicit scope enumeration,
* destructive-only conflict resolution,
* refusal as a lawful outcome,
* deadlock as a diagnostic outcome,
* auditability and replay requirements.

AKR-0 introduces **no new semantics**.

If AKR-0 requires modifying AST Spec or AIE, AKR-0 has already failed.

---

## 2) Experimental Role of AKR-0 (Non-Negotiable)

AKR-0 is:

* a **runtime sanity check**, not a governance test,
* a **physics-engine calibration**, not a social simulation,
* a **determinism proof**, not a performance benchmark.

AKR-0 must be able to **refuse, halt, or deadlock** cleanly.

If your implementation can only “do something,” it is invalid.

---

## 3) Single-Kernel Discipline (Absolute)

AKR-0 permits **exactly one** kernel implementation.

Hard constraints:

* No alternate runtimes
* No fallback engines
* No “fast path” vs “safe path”
* No retry logic
* No hidden glue logic
* No external arbitration

A second kernel requires **AKR-0 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2
* AIE v0.1
* AKR-0 execution semantics
* admissibility evaluation logic
* conflict detection logic
* deadlock taxonomy
* refusal semantics
* epoch advancement rules
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

You must enforce **three physically distinct layers**:

### 5.1 Authority Kernel Runtime (AKR-0)

Responsible for:

* maintaining the Authority State,
* evaluating admissibility,
* applying lawful transformations,
* refusing inadmissible actions,
* registering conflicts,
* declaring deadlock.

AKR-0 must not:

* infer intent,
* optimize outcomes,
* reorder authority,
* guess admissibility.

---

### 5.2 Authority Input Environment (AIE) — External

* Supplies authority records only
* Is blind to kernel state
* Does not generate actions
* Does not adapt to outcomes

If AIE influences execution order or action choice, the run is invalid.

---

### 5.3 Execution Harness (Traffic Generator)

* Generates **candidate action requests**
* Is deterministic and preregistered
* Is the **only source** of action attempts
* Does not evaluate authority

The harness proposes actions.
AKR-0 decides whether they run.

---

## 6) Input Discipline (Absolute)

AKR-0 may receive **only**:

* authority records from AIE,
* transformation requests per AST Spec,
* candidate action requests from the harness,
* epoch ticks.

Forbidden:

* implicit actions,
* environment-driven execution,
* time-based triggers,
* heuristic retries.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Canonical Ordering (Mandatory)

Within each Epoch:

* collect all inputs,
* serialize them canonically,
* sort deterministically (e.g., hash order),
* **then** evaluate admissibility and execution.

Arrival order, wall-clock time, or thread scheduling **must not** affect outcomes.

Failure:

```
INVALID_RUN / NONDETERMINISTIC_ORDERING
```

---

## 8) Admissibility First (Critical)

Every candidate action must be:

1. evaluated against the Authority State,
2. blocked if inadmissible,
3. executed only if admissible.

Execution before evaluation is forbidden.

Violation:

```
AKR_FAIL / UNGATED_EXECUTION
```

---

## 9) Refusal Semantics (Absolute)

If an action is inadmissible, AKR-0 must:

* refuse the action,
* suspend execution,
* or declare deadlock.

Forbidden:

* partial execution,
* best-effort execution,
* silent failure,
* guessing.

Refusal is **success**, not error.

---

## 10) Bounded Computation (Deterministic)

All kernel operations must run under a:

* deterministic instruction counter (gas),
* identical limits across platforms.

Wall-clock timeouts are forbidden as control logic.

On exhaustion:

* preserve state,
* refuse or suspend the action,
* log the event.

Violation:

```
AKR_FAIL / UNBOUNDED_EVALUATION
```

---

## 11) Conflict and Deadlock Handling (Strict)

Conflicts must be:

* detected structurally,
* registered explicitly,
* left unresolved unless lawful transformation occurs.

Deadlock must be:

* classified,
* logged,
* allowed to persist.

Automatic recovery is forbidden.

---

## 12) Conditions A / B / C Implementation

### Condition A — Valid Authority (Positive Control)

* Authority exists
* Actions admissible
* Execution proceeds

Goal: baseline executability.

---

### Condition B — Authority Absence (Negative Control)

* No authority binds actions

Expected outcome: refusal or deadlock.

Execution is failure.

---

### Condition C — Conflict Saturation

* Conflicting authorities injected
* Contested actions attempted

Expected outcome: conflict registration and blocking.

---

## 13) What Counts as Success (Strict)

AKR-0 **passes** iff:

1. No action executes without authority.
2. All inadmissible actions are refused or suspended.
3. Conflicts block execution deterministically.
4. Deadlocks are detected and classified.
5. Replay is bit-perfect.
6. No semantic or heuristic logic appears anywhere.

---

## 14) What Counts as Failure (Terminal)

AKR-0 **fails** if:

* execution occurs without authority,
* admissibility is skipped or guessed,
* conflicts are arbitrated,
* fallback behavior occurs,
* computation is non-deterministic,
* auditability is lost.

Failure terminates Phase VIII as **NEGATIVE RESULT**.

---

## 15) Logging and Artifacts (Mandatory)

You must record:

* all inputs (pre- and post-ordering),
* admissibility decisions,
* authority state hashes,
* transformations,
* refusals and suspensions,
* conflict registrations,
* deadlock declarations,
* instruction-count events.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 16) Definition of Done

AKR-0 v0.1 is complete when:

* design is frozen,
* Conditions A, B, and C are executed,
* replay produces identical traces,
* result is classified explicitly as PASS or FAIL,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not optimize.
Do not repair.
Do not improvise.

Your job is to answer one unforgiving question:

> *When authority runs out, does the system stop—or does it hallucinate control?*

If it stops, AKR-0 passes.
If it hallucinates, Phase VIII ends.

That is not a defect.
That is the experiment.

---

**End of Implementor Instructions: AKR-0 v0.1**
