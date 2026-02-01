# **Implementor Instructions: Stage VIII-1 v0.1**

**(PHASE-VIII-1-MINIMAL-PLURAL-AUTHORITY-STATIC-1)**

- **Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
- **Substage:** **VIII-1 — Minimal Plural Authority (Static)**

---

## 0) Context and Scope

### What you are building

You are implementing **one static plural-authority calibration experiment**, consisting of:

* a **deterministic Authority Kernel Runtime** operating under **Stage VIII-1 constraints**,
* a **frozen Authority State Transformation Spec (AST Spec v0.2)**,
* a **frozen Authority Input Environment (AIE v0.1)**,
* a **deterministic execution harness** proposing candidate actions, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Can multiple authorities coexist structurally over the same scope without collapsing into ordering, arbitration, or implicit dominance—even when no action is admissible?*

Stage VIII-1 exists to test **representation**, not governance.

If plural authority collapses at the representational level, Phase VIII terminates honestly.

---

### What you are *not* building

You are **not** building:

* a governance system,
* a coordination mechanism,
* a conflict resolver,
* a policy engine,
* a planner,
* an optimizer,
* a recovery system,
* a prioritization scheme,
* a fallback executor,
* a heuristic arbiter,
* a semantic interpreter,
* an LLM-in-the-loop,
* a safety wrapper,
* a “best effort” governor.

If your implementation **tries to be helpful**, the experiment is invalid.

---

## 1) Relationship to AKR-0, AIE v0.1, and AST Spec v0.2 (Binding)

Stage VIII-1 is **ontologically downstream** of:

* **AKR-0 — CLOSED — POSITIVE**,
* **AST Spec v0.2** (authority semantics), and
* **AIE v0.1** (authority sourcing).

All of the following are **fully binding and unchanged**:

* authority as a structural construct,
* explicit scope binding,
* refusal as a lawful outcome,
* deadlock as a lawful diagnostic,
* conflict as a structural fact,
* auditability and replay requirements.

Stage VIII-1 introduces **no new semantics**.

If Stage VIII-1 requires modifying AKR-0 conclusions, AST Spec, or AIE, Stage VIII-1 has already failed.

---

## 2) Experimental Role of Stage VIII-1 (Non-Negotiable)

Stage VIII-1 is:

* a **plurality sanity check**, not a governance test,
* a **representation test**, not an execution test,
* a **structural ontology probe**, not a coordination experiment.

Stage VIII-1 must be able to **refuse everything** and **halt cleanly**.

If your system must “do something” to appear correct, it is wrong.

---

## 3) Single-Kernel Discipline (Absolute)

Stage VIII-1 permits **exactly one** kernel implementation.

Hard constraints:

* No alternate runtimes
* No fallback engines
* No “plural-aware” special paths
* No retry logic
* No hidden arbitration logic
* No implicit precedence rules

A second kernel or mode requires **VIII-1 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2
* AIE v0.1
* Stage VIII-1 execution semantics
* authority identity handling
* conflict detection logic
* conflict representation logic
* refusal semantics
* deadlock state logic
* transformation admissibility checks
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

You must enforce **three physically distinct layers**.

### 5.1 Authority Kernel Runtime (Stage VIII-1)

Responsible for:

* maintaining the Authority State,
* preserving multiple authorities simultaneously,
* evaluating admissibility under AST,
* refusing inadmissible actions,
* registering conflicts,
* entering and maintaining deadlock state.

The kernel must not:

* resolve conflicts,
* prioritize authorities,
* collapse symmetric records,
* infer sameness,
* guess intent,
* optimize outcomes.

---

### 5.2 Authority Input Environment (AIE) — External

* Supplies authority records only
* Injects exactly two authorities at epoch 0
* Is blind to kernel state
* Does not generate actions
* Does not adapt to outcomes

If AIE influences execution order or conflict handling, the run is invalid.

---

### 5.3 Execution Harness (Traffic Generator)

* Generates **candidate action requests**
* Is deterministic and preregistered
* Is the **only source** of action attempts
* Does not evaluate authority
* Does not infer conflict state

The harness proposes actions.
The kernel refuses them.

---

## 6) Input Discipline (Absolute)

Stage VIII-1 may receive **only**:

* authority records from AIE,
* candidate action requests from the harness.

Forbidden:

* transformation requests,
* epoch ticks,
* implicit actions,
* environment-driven execution,
* heuristic retries,
* time-based triggers.

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
* evaluate admissibility only after ordering.

Arrival order, wall-clock time, or thread scheduling **must not** affect outcomes.

Failure:

```
INVALID_RUN / NONDETERMINISTIC_ORDERING
```

---

## 8) Authority Identity Handling (Critical)

Authority identity is **primitive**.

You must ensure:

* each Authority Record has a unique immutable `AuthorityID`,
* storage is keyed by `AuthorityID`,
* no content-based deduplication occurs,
* symmetric authorities remain distinct.

Using content-addressable storage, Merkle trees, or equality collapse is forbidden.

Violation:

```
VIII1_FAIL / AUTHORITY_COLLAPSE
```

---

## 9) Admissibility First (Absolute)

Every candidate action must be:

1. evaluated against the full Authority State,
2. blocked if inadmissible due to conflict or absence of authority,
3. **never executed** in Stage VIII-1.

Execution at any point is failure.

Violation:

```
VIII1_FAIL / UNGATED_EXECUTION
```

---

## 10) Refusal Semantics (Binding)

If an action is inadmissible, the kernel must:

* refuse the action explicitly,
* preserve authority state,
* preserve conflict state.

Forbidden:

* partial execution,
* best-effort execution,
* silent failure,
* fallback behavior.

Refusal is **success**, not error.

---

## 11) Conflict Representation Discipline (Strict)

When conflicting authorities bind the same scope:

* conflict must be detected structurally,
* conflict must be registered explicitly,
* conflict records must reference all AuthorityIDs involved,
* conflict records must be **unordered**.

You must not expose:

* index positions,
* ordering,
* lexicographic precedence.

Any detectable ordering signal is failure.

---

## 12) Deadlock State Handling (Strict)

When:

* a conflict is registered, and
* no admissible actions exist, and
* no admissible transformations exist,

the kernel must:

* enter `STATE_DEADLOCK`,
* emit `DEADLOCK_DECLARED`,
* remain in deadlock for the remainder of the run.

Deadlock is a **persistent state**, not a transient event.

Automatic recovery is forbidden.

---

## 13) Condition Sequencing (Mandatory)

Stage VIII-1 Conditions are **stateful and sequential**.

### Condition A — Contested Authority

* Conflicting authorities injected
* Contested actions proposed

Expected outcome:

* actions refused
* conflict registered
* deadlock entered

---

### Condition B — Third-Party Actions

**Prerequisite:** Condition A has executed and conflict is active.

* Actions proposed by identity not present in Authority State

Expected outcome:

* rejection with `AUTHORITY_NOT_FOUND`
* conflict remains registered
* deadlock state persists

Running Condition B in isolation is invalid.

---

## 14) Bounded Computation (Deterministic)

All kernel operations must run under:

* deterministic instruction budget (gas),
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
* admissibility decisions,
* conflict registrations,
* refusal events,
* deadlock entry and persistence,
* authority state hashes,
* instruction-count events.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 16) Definition of Done

Stage VIII-1 v0.1 is complete when:

* design is frozen,
* Conditions A then B are executed in one run,
* conflict is represented without ordering,
* deadlock is entered and persists,
* replay produces identical traces,
* result is classified explicitly as PASS or FAIL,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not optimize.
Do not arbitrate.
Do not resolve.
Do not improvise.

Your job is to answer one narrow, unforgiving question:

> *Can plural authority exist without pretending to govern?*

If it can, Stage VIII-1 passes.
If it collapses into ordering or arbitration, Phase VIII ends.

That is not a defect.
That is the experiment.

---

**End of Implementor Instructions: Stage VIII-1 v0.1**
