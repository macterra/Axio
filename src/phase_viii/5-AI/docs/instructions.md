# **Implementor Instructions: Stage VIII-5 v0.1**

**(PHASE-VIII-5-AUTHORITY-INJECTION-OPEN-SYSTEM-1)**

* **Axionic Phase VIII — Governance Stress Architecture (GSA-PoC)**
* **Substage:** **VIII-5 — Authority Injection Under Open-System Constraint**

---

## 0) Context and Scope

### What you are building

You are implementing **one open-system authority-injection stress experiment**, consisting of:

* a **deterministic Authority Kernel Runtime** operating under **Stage VIII-5 constraints**,
* a **frozen Authority State Transformation Spec (AST Spec v0.2)**,
* a **frozen Authority Input Environment (AIE v0.1)**,
* a **deterministic execution harness** that injects authority, proposes actions, and advances epochs,
* a **complete audit, trace, and replay instrumentation layer**,

that together test **exactly one question**:

> *Can new authority be introduced from outside the system without privilege, kernel arbitration, ordering, laundering, or semantic exception?*

Stage VIII-5 exists to test **open-system honesty**, not governance success.

If governance survives only by smuggling in gods, Phase VIII terminates honestly.

---

### What you are *not* building

You are **not** building:

* a legitimacy filter,
* a gatekeeper for injection,
* a superuser port,
* a constitution importer,
* a bootstrap authority,
* a consensus engine,
* a revolution dampener,
* a stability mechanism,
* a deadlock breaker,
* an incentive layer,
* a trust model,
* a political theory,
* a safety system,
* a semantic interpreter,
* an adjudicator.

If your implementation **tries to make injection safe, wise, fair, or stabilizing**, the experiment is invalid.

---

## 1) Relationship to Prior Stages and Specs (Binding)

Stage VIII-5 is **ontologically downstream** of:

* **AKR-0 — CLOSED — POSITIVE**,
* **Stage VIII-1 — CLOSED — POSITIVE**,
* **Stage VIII-2 — CLOSED — POSITIVE**,
* **Stage VIII-3 — CLOSED — POSITIVE**,
* **Stage VIII-4 — CLOSED — POSITIVE**,
* **AST Spec v0.2**, and
* **AIE v0.1**.

All of the following remain **fully binding and unchanged**:

* authority as a structural construct,
* conflict as a structural fact,
* refusal as a lawful outcome,
* deadlock as a lawful outcome,
* non-amplification invariants,
* expiry and renewal semantics,
* determinism and replayability,
* selector blindness,
* refusal-first semantics.

Stage VIII-5 introduces **external authority injection only**.

If Stage VIII-5 requires modifying AKR-0, VIII-1, VIII-2, VIII-3, VIII-4, AST, or AIE semantics, Stage VIII-5 has already failed.

---

## 2) Experimental Role of Stage VIII-5 (Non-Negotiable)

Stage VIII-5 is:

* an **open-system boundary test**, not a governance mechanism,
* an **external disruption probe**, not an amendment pathway,
* a **privilege detection experiment**, not a safety valve.

Stage VIII-5 must be able to:

* inject authority that worsens conflict,
* inject authority that never resolves deadlock,
* inject authority endlessly without convergence,
* terminate with infinite unresolved authority records.

If your system “uses injection to fix governance,” it is wrong.

---

## 3) Single-Kernel Discipline (Absolute)

Stage VIII-5 permits **exactly one** kernel implementation.

Hard constraints:

* No alternate runtimes
* No injection mode
* No bootstrap kernel
* No emergency override
* No kernel-initiated injection
* No injection prioritization
* No identity arbitration
* No “first injection wins”

A second kernel or privileged injection path requires **VIII-5 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2
* AIE v0.1
* Stage VIII-5 execution semantics
* authority injection schema
* content-addressed AuthorityID derivation
* VOID lineage sentinel semantics
* authority activation discipline
* admissibility logic
* conflict and deadlock handling
* authority renewal handling
* intra-epoch evaluation bound
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

### 5.1 Authority Kernel Runtime (Stage VIII-5)

Responsible for:

* maintaining Authority State,
* evaluating injection structurally,
* enforcing content-addressed identity derivation,
* enforcing VOID lineage constraints,
* enforcing non-amplification,
* enforcing activation discipline,
* preserving conflict and deadlock,
* refusing inadmissible injections deterministically.

The kernel must not:

* interpret injection intent,
* judge legitimacy,
* prioritize injections,
* resolve conflicts,
* exit deadlock due to injection,
* stabilize governance.

---

### 5.2 Authority Input Environment (AIE) — External

* Supplies authority records
* Supplies injection events
* Supplies action requests
* Is blind to kernel outcomes
* Does not infer conflict or deadlock
* Does not adapt injection strategy

If AIE reacts to kernel outcomes, the run is invalid.

---

### 5.3 Execution Harness (Injection Traffic Generator)

* Injects authority deterministically
* Proposes actions deterministically
* Advances epochs explicitly
* Applies load and flooding scenarios
* Does not interpret authority state
* Does not resolve deadlock
* Does not retry intelligently

The harness pressures the system.
The kernel resists.

---

## 6) Input Discipline (Absolute)

Stage VIII-5 may receive **only**:

* authority records from AIE,
* explicit authority injection events,
* explicit epoch advancement requests,
* explicit authority renewal requests,
* candidate action requests.

Forbidden:

* implicit injection,
* kernel-generated injection,
* heuristic retries,
* inferred authority creation,
* semantic repair.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Authority Identity Discipline (Critical)

You must ensure:

* AuthorityIDs are **content-addressed** from the full AuthorityRecord,
* identical AuthorityRecords yield identical AuthorityIDs,
* duplicate injections are idempotent,
* no user-assigned AuthorityIDs exist,
* no kernel arbitration occurs.

Any procedural identity resolution:

```
VIII5_FAIL / IMPLICIT_ORDERING
```

---

## 8) Injection Lineage Discipline (Critical)

You must ensure:

* all injected authorities specify `ParentID := VOID`,
* `VOID` is not comparable to any AuthorityID,
* lineage determines validation path (VIII-5 vs VIII-4),
* no injected authority claims ancestry.

Any implicit lineage or inheritance:

```
VIII5_FAIL / GOVERNANCE_PRIVILEGE
```

---

## 9) Authority Activation Discipline (Absolute)

Injected authority must:

* enter `PENDING` state on injection,
* activate only at the next epoch boundary,
* admit no actions in the injection epoch.

Immediate activation is forbidden.

Violation:

```
VIII5_FAIL / IMPLICIT_ORDERING
```

---

## 10) Injection Admissibility (Strict)

Every injection must be:

1. schema-valid,
2. content-addressed,
3. VOID-lineaged,
4. epoch-consistent,
5. within deterministic budget.

Injection intent is irrelevant.

Violation:

```
VIII5_FAIL / UNGATED_EXECUTION
```

---

## 11) Injection and Conflict Semantics (Binding)

Injected authority must not:

* erase conflict,
* downgrade deadlock,
* retroactively authorize actions.

Injected authority may:

* join conflicts,
* expand deadlock,
* worsen admissibility.

Conflict persistence is success, not failure.

---

## 12) Deadlock Discipline (Strict)

Injection must not:

* exit deadlock,
* bypass admissibility,
* force resolution.

Deadlock may persist indefinitely despite injection.

Kernel intervention:

```
VIII5_FAIL / KERNEL_DECISION
```

---

## 13) Injection Flooding Discipline (Mandatory)

You must test:

* high-volume injection,
* overlapping scopes,
* multi-epoch accumulation.

You must ensure:

* refusal occurs only via budget exhaustion,
* no heuristic throttling,
* no prioritization,
* no silent collapse of trace or state.

Any ad hoc suppression:

```
VIII5_FAIL / AD_HOC_RESOURCE_ARBITRATION
```

---

## 14) Intra-Epoch Termination Bound (Mandatory)

All injection evaluation must run under:

* a deterministic instruction budget,
* identical bounds across platforms.

On exhaustion:

* preserve state,
* refuse deterministically,
* log exhaustion explicitly.

Wall-clock timeouts are forbidden.

Violation:

```
INVALID_RUN / NONTERMINATING_REGRESS
```

---

## 15) Condition Sequencing (Mandatory)

Stage VIII-5 Conditions are **stateful and sequential**.

### Condition A — Injection Into Empty Authority State

### Condition B — Injection Into Active Conflict

### Condition C — Competing Injections

### Condition D — Injection After Authority Destruction

### Condition E — Injection Under Load

### Condition F — Injection Flooding Attempt

Running conditions out of sequence is invalid.

---

## 16) Logging and Artifacts (Mandatory)

You must record:

* all injection events,
* injected AuthorityRecords,
* derived AuthorityIDs,
* injection epochs,
* source identifiers (opaque),
* authority state transitions,
* activation transitions,
* conflict and deadlock transitions,
* budget exhaustion events,
* authority state hashes,
* epoch transitions.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 17) Definition of Done

Stage VIII-5 v0.1 is complete when:

* design is frozen,
* identity is content-addressed,
* injection is structurally evaluated only,
* no privilege is introduced,
* conflicts persist honestly,
* deadlocks persist honestly,
* replay is bit-perfect,
* classification is explicit,
* no kernel discretion is exercised.

---

## Final Orientation for the Implementor

Do not judge injection.
Do not legitimize injection.
Do not stabilize governance.
Do not save the system.

Your job is to answer one brutal question:

> *Can authority enter a system without becoming a god?*

If yes, Stage VIII-5 passes.
If injection requires privilege, Phase VIII fails.

That is not an error.
That is the measurement.

---

**End of Implementor Instructions: Stage VIII-5 v0.1**
