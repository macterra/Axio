# **Implementor Instructions: Stage VIII-4 v0.1**

**(PHASE-VIII-4-GOVERNANCE-TRANSITIONS-META-AUTHORITY-1)**

* **Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
* **Substage:** **VIII-4 — Governance Transitions (Meta-Authority)**

---

## 0) Context and Scope

### What you are building

You are implementing **one governance-transition stress experiment**, consisting of:

* a **deterministic Authority Kernel Runtime** operating under **Stage VIII-4 constraints**,
* a **frozen Authority State Transformation Spec (AST Spec v0.2)**,
* a **frozen Authority Input Environment (AIE v0.1)**,
* a **deterministic execution harness** that proposes governance actions and advances epochs,
* a **complete audit, trace, and replay instrumentation layer**,

that together test **exactly one question**:

> *Can authority govern authority through ordinary, authority-bound transformations without privilege, escalation, kernel choice, or semantic exception?*

Stage VIII-4 exists to test **meta-governance honesty**, not institutional success.

If governance works only by cheating, Phase VIII terminates honestly.

---

### What you are *not* building

You are **not** building:

* a constitution engine,
* a governance framework,
* a policy DSL,
* a rule compiler,
* an amendment optimizer,
* a legitimacy oracle,
* a hierarchy resolver,
* a superuser role,
* a “constitutional layer,”
* a meta-scheduler,
* a conflict solver,
* a governance recommender,
* a stability mechanism,
* a safety system,
* a semantic interpreter,
* an LLM-assisted adjudicator.

If your implementation **tries to make governance coherent or stable**, the experiment is invalid.

---

## 1) Relationship to Prior Stages and Specs (Binding)

Stage VIII-4 is **ontologically downstream** of:

* **AKR-0 — CLOSED — POSITIVE**,
* **Stage VIII-1 — CLOSED — POSITIVE**,
* **Stage VIII-2 — CLOSED — POSITIVE**,
* **Stage VIII-3 — CLOSED — POSITIVE**,
* **AST Spec v0.2**, and
* **AIE v0.1**.

All of the following are **fully binding and unchanged**:

* authority as a structural construct,
* scope opacity,
* refusal as a lawful outcome,
* deadlock as a lawful outcome,
* conflict as a structural fact,
* determinism and replayability,
* expiry and renewal semantics.

Stage VIII-4 introduces **governance actions only**.

If Stage VIII-4 requires modifying AKR-0, VIII-1, VIII-2, VIII-3, AST, or AIE semantics, Stage VIII-4 has already failed.

---

## 2) Experimental Role of Stage VIII-4 (Non-Negotiable)

Stage VIII-4 is:

* a **meta-authority stress test**, not a governance solution,
* a **self-amendment probe**, not an institutional design,
* a **privilege detection experiment**, not a stability guarantee.

Stage VIII-4 must be able to:

* revoke all authorities,
* deadlock governance indefinitely,
* refuse all governance actions,
* terminate with no governing authority remaining.

If your system “keeps governance alive,” it is wrong.

---

## 3) Single-Kernel Discipline (Absolute)

Stage VIII-4 permits **exactly one** kernel implementation.

Hard constraints:

* No alternate runtimes
* No governance mode
* No constitutional path
* No emergency override
* No kernel-initiated governance
* No implicit meta-ordering
* No “last amendment wins”
* No hidden arbitration

A second kernel or governance mode requires **VIII-4 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2
* AIE v0.1
* Stage VIII-4 execution semantics
* governance action schema
* governance action identity rules
* authority non-amplification invariant
* intra-epoch evaluation bound
* admissibility logic for governance actions
* conflict and deadlock handling
* authority creation and destruction rules
* epoch handling
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

### 5.1 Authority Kernel Runtime (Stage VIII-4)

Responsible for:

* maintaining Authority State,
* evaluating governance actions structurally,
* enforcing non-amplification,
* enforcing identity immutability,
* enforcing admissibility using only ACTIVE authorities,
* preserving conflict and deadlock,
* refusing inadmissible governance actions deterministically.

The kernel must not:

* interpret governance semantics,
* choose governing authorities,
* resolve governance conflicts,
* break regress loops,
* escalate authority,
* repair governance.

---

### 5.2 Authority Input Environment (AIE) — External

* Supplies authority records only
* Supplies governance action requests only
* Is blind to kernel outcomes
* Does not infer conflict or deadlock
* Does not adapt governance proposals

If AIE reacts to kernel outcomes, the run is invalid.

---

### 5.3 Execution Harness (Governance Traffic Generator)

* Proposes governance actions deterministically
* Advances epochs explicitly
* Injects destruction and renewal explicitly
* Does not interpret authority state
* Does not resolve deadlock
* Does not retry intelligently

The harness pressures governance.
The kernel resists.

---

## 6) Input Discipline (Absolute)

Stage VIII-4 may receive **only**:

* authority records from AIE,
* explicit epoch advancement requests,
* explicit authority renewal requests,
* explicit governance action requests,
* candidate non-governance actions (for interference testing).

Forbidden:

* implicit governance triggers,
* kernel-generated governance actions,
* heuristic retries,
* inferred amendments,
* semantic repair.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Governance Action Identity Discipline (Critical)

You must ensure:

* governance action identity is derived **only** from explicit structural fields,
* identical governance actions at different epochs are distinct,
* no semantic equivalence testing occurs,
* no normalization collapses history.

Any implicit comparison or aliasing:

```
VIII4_FAIL / IMPLICIT_ORDERING
```

---

## 8) Authority Identity and Modification Handling (Critical)

You must ensure:

* each Authority Record has a unique immutable `AuthorityID`,
* governance actions never mutate authority in place,
* amendment produces a **new AuthorityID**,
* VOID and EXPIRED authorities never grant permissions,
* pointer breakage is preserved.

Any resurrection, mutation, or auto-update:

```
VIII4_FAIL / AUTHORITY_REANIMATION
```

---

## 9) Admissibility of Governance Actions (Absolute)

Every governance action must be:

1. evaluated using **only ACTIVE authorities**,
2. rejected if no authority admits it,
3. rejected if authorities conflict,
4. executed only if structurally admissible.

Governance intent is irrelevant.

Violation:

```
VIII4_FAIL / UNGATED_EXECUTION
```

---

## 10) Governance Non-Amplification (Strict)

You must enforce:

* no governance action may create authority whose admissible action-set exceeds the union of the admitting authorities’ action-sets,
* no amendment chain may escalate authority power,
* all authority power is conserved or reduced internally.

Any escalation:

```
VIII4_FAIL / AUTHORITY_LAUNDERING
```

---

## 11) Refusal, Conflict, and Deadlock Semantics (Binding)

If a governance action is inadmissible, the kernel must:

* refuse explicitly,
* preserve authority state,
* preserve conflict state,
* preserve deadlock state across epochs.

Forbidden:

* partial governance,
* best-effort amendment,
* silent failure,
* “temporary authority.”

Refusal and deadlock are **success states**.

---

## 12) Self-Reference and Regress Discipline (Strict)

Governance actions may target authorities that authorize governance.

You must ensure:

* no special-case handling,
* no loop unrolling,
* no kernel escape.

Regress must terminate via:

* refusal,
* expiry,
* destruction,
* lawful deadlock,
* evaluation bound exhaustion.

Kernel intervention:

```
VIII4_FAIL / KERNEL_DECISION
```

---

## 13) Intra-Epoch Termination Bound (Mandatory)

All governance evaluation must run under:

* a deterministic instruction budget,
* identical bounds across platforms.

On exhaustion:

* preserve state,
* refuse or deadlock deterministically,
* log exhaustion explicitly.

Wall-clock timeouts are forbidden.

Violation:

```
INVALID_RUN / NONTERMINATING_REGRESS
```

---

## 14) Condition Sequencing (Mandatory)

Stage VIII-4 Conditions are **stateful and sequential**.

### Condition A — Governance Without Authority

* governance action proposed
* no admitting authority

Expected outcome:

* refusal,
* no authority change.

---

### Condition B — Single-Authority Governance

* one authority admits governance action
* no conflict

Expected outcome:

* lawful execution **iff** admissible.

---

### Condition C — Conflicting Governance Authorities

* incompatible governance actions admitted

Expected outcome:

* conflict registered,
* deadlock entered.

---

### Condition D — Governance of Governance

* authority attempts to modify its own governance authority

Expected outcome:

* lawful execution or lawful deadlock,
* no exception paths.

---

### Condition E — Infinite Regress Attempt

* chained governance actions form recursive dependency

Expected outcome:

* termination via refusal, expiry, destruction, deadlock, or bound exhaustion.

Running conditions out of sequence is invalid.

---

## 15) Logging and Artifacts (Mandatory)

You must record:

* all governance action requests,
* governance action identities,
* admissible authority sets at evaluation time,
* authority creation, expiry, and destruction events,
* conflict and deadlock transitions,
* instruction-count exhaustion events,
* authority state hashes,
* epoch transitions.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 16) Definition of Done

Stage VIII-4 v0.1 is complete when:

* design is frozen,
* governance actions are evaluated structurally,
* no authority escalation occurs,
* self-reference terminates lawfully,
* conflicts and deadlocks persist explicitly,
* replay is bit-perfect,
* result is classified explicitly,
* no kernel discretion is exercised.

---

## Final Orientation for the Implementor

Do not govern.
Do not stabilize.
Do not optimize.
Do not resolve.

Your job is to answer one brutal question:

> *Can authority govern itself without becoming a god?*

If yes, Stage VIII-4 passes.
If governance requires privilege, Phase VIII fails.

That is not a flaw.
That is the measurement.

---

**End of Implementor Instructions: Stage VIII-4 v0.1**
