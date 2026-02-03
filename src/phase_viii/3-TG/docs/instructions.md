# **Implementor Instructions: Stage VIII-3 v0.1**

**(PHASE-VIII-3-TEMPORAL-GOVERNANCE-AUTHORITY-OVER-TIME-1)**

* **Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
* **Substage:** **VIII-3 — Temporal Governance (Authority Over Time)**

---

## 0) Context and Scope

### What you are building

You are implementing **one temporal authority survivability experiment**, consisting of:

* a **deterministic Authority Kernel Runtime** operating under **Stage VIII-3 constraints**,
* a **frozen Authority State Transformation Spec (AST Spec v0.2)**,
* a **frozen Authority Input Environment (AIE v0.1)**,
* a **deterministic execution harness** that advances epochs, injects renewals, and proposes actions,
* a **complete audit, trace, and replay instrumentation layer**,

that together test **exactly one question**:

> *Can authority persist over time only via explicit expiry and renewal, without implicit ordering, resurrection, semantic drift, or temporal “healing” of conflict?*

Stage VIII-3 exists to test **temporal honesty**, not governance effectiveness.

If authority survives time without explicit renewal, Phase VIII terminates honestly.

---

### What you are *not* building

You are **not** building:

* a governance system,
* a scheduler,
* a policy lifecycle manager,
* a law-amendment system,
* a prioritization mechanism,
* a continuity optimizer,
* a renewal recommender,
* an authority selector,
* a legitimacy evaluator,
* a conflict resolver,
* a planner,
* a recovery mechanism,
* a time-based heuristic,
* a semantic interpreter,
* an LLM-in-the-loop,
* a “smooth transition” system.

If your implementation **tries to make temporal governance feel natural**, the experiment is invalid.

---

## 1) Relationship to Prior Stages and Specs (Binding)

Stage VIII-3 is **ontologically downstream** of:

* **AKR-0 — CLOSED — POSITIVE**,
* **Stage VIII-1 — CLOSED — POSITIVE**,
* **Stage VIII-2 — CLOSED — POSITIVE**,
* **AST Spec v0.2**, and
* **AIE v0.1**.

All of the following are **fully binding and unchanged**:

* authority as a structural construct,
* scope opacity,
* refusal as a lawful outcome,
* deadlock as a lawful outcome,
* conflict as a structural fact,
* determinism and replayability.

Stage VIII-3 introduces **time only**.

If Stage VIII-3 requires modifying AKR-0, VIII-1, VIII-2, AST, or AIE semantics, Stage VIII-3 has already failed.

---

## 2) Experimental Role of Stage VIII-3 (Non-Negotiable)

Stage VIII-3 is:

* a **temporal stress test**, not a governance solution,
* a **persistence probe**, not a continuity guarantee,
* a **destruction-and-renewal honesty check**, not a lifecycle manager.

Stage VIII-3 must be able to:

* allow all authorities to expire,
* refuse all actions indefinitely,
* preserve deadlock across epochs,
* halt cleanly with no recovery.

If your system “keeps things running,” it is wrong.

---

## 3) Single-Kernel Discipline (Absolute)

Stage VIII-3 permits **exactly one** kernel implementation.

Hard constraints:

* No alternate runtimes
* No epoch-aware fallback logic
* No renewal heuristics
* No authority aging shortcuts
* No “latest authority wins” logic
* No kernel-initiated renewal
* No temporal arbitration

A second kernel or mode requires **VIII-3 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2
* AIE v0.1
* Stage VIII-3 execution semantics
* epoch representation and monotonicity rules
* expiry and renewal handling
* authority state transitions
* renewal metadata schema
* admissibility logic over time
* conflict persistence logic
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

You must enforce **three physically distinct layers**.

### 5.1 Authority Kernel Runtime (Stage VIII-3)

Responsible for:

* maintaining Authority State across epochs,
* enforcing finite expiry of all authorities,
* transitioning authorities to EXPIRED or VOID,
* evaluating admissibility using only ACTIVE authorities,
* preserving conflict and deadlock across time,
* refusing inadmissible actions deterministically.

The kernel must not:

* interpret time semantically,
* infer renewal necessity,
* initiate renewal,
* prioritize newer authorities,
* resolve conflicts,
* smooth transitions.

---

### 5.2 Authority Input Environment (AIE) — External

* Supplies authority records only
* Supplies renewal requests only
* Is blind to kernel state
* Does not infer expiry
* Does not adapt to outcomes

If AIE reacts to kernel outcomes, the run is invalid.

---

### 5.3 Execution Harness (Temporal Traffic Generator)

* Advances epochs explicitly
* Injects renewal requests explicitly
* Proposes candidate actions deterministically
* Does not interpret authority state
* Does not react to deadlock
* Does not retry intelligently

The harness applies pressure.
The kernel resists.

---

## 6) Input Discipline (Absolute)

Stage VIII-3 may receive **only**:

* authority records from AIE,
* explicit epoch advancement requests,
* explicit authority renewal requests,
* candidate action requests from the harness.

Forbidden:

* implicit epoch ticks,
* wall-clock triggers,
* auto-renewal,
* kernel-initiated inputs,
* heuristic retries,
* inferred transformations.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Epoch Discipline (Mandatory)

Epoch handling must satisfy:

* discrete integer epochs,
* strictly monotonic increase,
* explicit advancement only,
* no regression,
* no implicit progression.

Any attempt to set `NewEpoch ≤ CurrentEpoch`:

```
INVALID_RUN / TEMPORAL_REGRESSION
```

Epoch is a **state variable**, not a clock.

---

## 8) Authority Identity and Lifetime Handling (Critical)

You must ensure:

* each Authority Record has a unique immutable `AuthorityID`,
* every authority has a finite `ExpiryEpoch`,
* expiry transitions are automatic and deterministic,
* EXPIRED and VOID authorities never grant permissions,
* renewal creates a **new** AuthorityID.

Using content equality, lineage inference, or resurrection logic is forbidden.

Violation:

```
VIII3_FAIL / AUTHORITY_REANIMATION
```

---

## 9) Admissibility Over Time (Absolute)

Every candidate action must be:

1. evaluated against **only ACTIVE authorities**,
2. refused if inadmissible,
3. never executed when authority is absent or conflicted.

Expired authority is equivalent to no authority.

Violation:

```
VIII3_FAIL / UNGATED_EXECUTION
```

---

## 10) Refusal and Deadlock Semantics (Binding)

If an action is inadmissible, the kernel must:

* refuse explicitly,
* preserve authority state,
* preserve conflict state,
* preserve deadlock state across epochs.

Forbidden:

* best-effort execution,
* partial execution,
* time-based recovery,
* silent degradation.

Refusal and deadlock are **success states**.

---

## 11) Renewal Semantics Discipline (Strict)

Renewal handling must satisfy:

* renewal is externally requested only,
* renewal creates a new AuthorityID,
* renewal does not inherit authority force,
* renewal does not modify prior records,
* renewal of VOID authorities is permitted but non-resurrective.

Kernel-initiated renewal:

```
VIII3_FAIL / KERNEL_DECISION
```

---

## 12) Conflict Persistence Over Time (Strict)

If a conflict exists at epoch *t*:

* and no destruction or renewal occurs,
* conflict **must persist** at epoch *t+1*.

Epoch advancement alone must not change admissibility.

Implicit resolution:

```
VIII3_FAIL / IMPLICIT_RESOLUTION
```

---

## 13) Condition Sequencing (Mandatory)

Stage VIII-3 Conditions are **stateful and sequential**.

### Condition A — Expiry Without Renewal

* Authorities expire
* No renewal injected

Expected outcome:

* no ACTIVE authorities,
* actions refused,
* deadlock persists.

---

### Condition B — Renewal Without Conflict

**Prerequisite:** Condition A executed.

* Renewal injected with non-overlapping scope

Expected outcome:

* admissibility restored,
* no history erased.

---

### Condition C — Renewal After Destruction

**Prerequisite:** VOID authority exists.

* Renewal references VOID authority

Expected outcome:

* VOID state preserved,
* no resurrection,
* admissibility evaluated anew.

---

### Condition D — Renewal Under Ongoing Conflict

**Prerequisite:** conflict active.

* Renewal injected for one conflicting side

Expected outcome:

* conflict remains explicit,
* no priority inferred.

Running conditions out of sequence is invalid.

---

## 14) Bounded Computation (Deterministic)

All kernel operations must run under:

* deterministic instruction budget,
* identical limits across platforms.

Wall-clock timeouts are forbidden.

On exhaustion:

* preserve state,
* refuse further actions,
* log deterministically.

Violation:

```
INVALID_RUN / UNBOUNDED_EVALUATION
```

---

## 15) Logging and Artifacts (Mandatory)

You must record:

* all inputs (pre- and post-ordering),
* epoch transitions,
* authority lifecycle events,
* renewal requests and metadata,
* admissibility decisions,
* conflict and deadlock persistence,
* authority state hashes,
* instruction-count events.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 16) Definition of Done

Stage VIII-3 v0.1 is complete when:

* design is frozen,
* epochs advance monotonically,
* authorities expire deterministically,
* renewal creates new AuthorityIDs,
* conflict persists across time,
* deadlock persists lawfully,
* replay is bit-perfect,
* result is classified explicitly,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not smooth.
Do not optimize.
Do not assume continuity.
Do not “help time along.”

Your job is to answer one brutal question:

> *Does authority survive time only if someone explicitly keeps it alive?*

If yes, Stage VIII-3 passes.
If time quietly repairs governance, Phase VIII fails.

That is not a problem.
That is the point.

---

**End of Implementor Instructions: Stage VIII-3 v0.1**
