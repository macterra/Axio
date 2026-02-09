# **Implementor Instructions: IX-5 v0.1**

**(PHASE-IX-5-MULTI-AGENT-SOVEREIGNTY-1)**

* **Axionic Phase IX — Reflective Sovereign Agent (RSA)**
* **Substage:** **IX-5 — Multi-Agent Sovereignty**

---

## 0) Context and Scope

### What you are building

You are implementing **one peer-sovereignty stress experiment**, consisting of:

* a **kernel-closed, non-sovereign authority system** (already validated),
* **multiple reflective sovereign agents (RSAs)** acting as peers,
* **shared and/or overlapping institutional state**,
* **no arbiter, leader, kernel sovereignty, or injected legitimacy**,
* **explicit refusal, exit, deadlock, livelock, domination, orphaning, and collapse handling**,
* **no arbitration, aggregation, prioritization, coordination guarantees, or recovery logic**, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Can multiple sovereign agents coexist over shared state without hierarchy, arbitration, aggregation, or legitimacy laundering?*

IX-5 exists to determine whether **sovereignty survives collision**.

If coexistence requires arbitration, **IX-5 fails**.
If coexistence collapses honestly, **IX-5 passes**.

---

### What you are *not* building

You are **not** building:

* a coordination protocol,
* a consensus algorithm,
* a treaty system,
* a fairness mechanism,
* a liveness guarantee,
* a timeout mechanism,
* a progress engine,
* a stabilization layer,
* a recovery or reconciliation process,
* a social contract,
* a safety or alignment system.

If your system **forces agreement**, **breaks deadlock**, or **privileges one peer implicitly**, the experiment is invalid.

---

## 1) Relationship to Kernel, AST, and Prior Phases (Binding)

IX-5 is **ontologically downstream** of:

* kernel-closed authority physics (Phases I–VIII),
* **AST Spec v0.2**,
* **AKR-0** (deterministic authority execution),
* **Phase VIII — GSA-PoC**,
* **IX-0 — Translation Layer Integrity**,
* **IX-1 — Value Encoding Without Aggregation**,
* **IX-2 — Coordination Under Deadlock**,
* **IX-3 — Governance Styles Under Honest Failure**,
* **IX-4 — Injection Politics**.

All of the following are **fully binding and unchanged**:

* the kernel is non-sovereign,
* authority is structural,
* refusal is lawful,
* silence is lawful,
* exit is lawful,
* deadlock is lawful,
* livelock is lawful but terminal,
* orphaning is permanent,
* no authority synthesis,
* no implicit legitimacy,
* no arbitration or aggregation,
* no timeout-based resolution,
* deterministic execution and replay.

IX-5 introduces **no new authority physics**.

If peer interaction requires kernel discretion, **IX-5 has already failed**.

---

## 2) Experimental Role of IX-5 (Non-Negotiable)

IX-5 is:

* a **peer-sovereignty collision test**,
* a **multi-agent interference mapping experiment**,
* a **hierarchy emergence detector**.

IX-5 is **not**:

* a coordination phase,
* a convergence study,
* a governance improvement phase,
* a social optimization experiment.

IX-5 must be allowed to **deadlock permanently, fragment, dominate asymmetrically, or collapse**.

If your system “eventually resolves,” it is invalid.

---

## 3) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2,
* kernel implementation,
* agent identity set,
* agent authority allocations,
* shared / overlapping authority topology,
* admissibility rules,
* interaction cadence,
* exit semantics,
* deadlock/livelock classifiers,
* domination and orphaning definitions,
* collapse definition,
* tooling behavior rules,
* time semantics (no wall clock),
* determinism guarantees,
* logging schema,
* replay protocol,
* seeds and initial state.

Any post-freeze modification:

```
INVALID_RUN / DESIGN_DRIFT
```

Brittleness is intentional.

---

## 4) Architectural Partitioning (Mandatory)

You must enforce **three physically distinct layers**:

### 4.1 Agent / Sovereign Actor Layer (External)

Responsible for:

* acting, refusing, exiting, or persisting,
* interacting with other agents,
* attempting coordination or refusing it,
* exerting pressure or withdrawing.

This layer may:

* observe other agents,
* model or predict behavior,
* attempt persuasion or domination.

This layer must not:

* force admissibility,
* enforce arbitration,
* reclaim orphaned authority,
* override kernel outcomes.

---

### 4.2 Authority & Interaction Kernel (Fixed)

Responsible for:

* enforcing authority constraints,
* evaluating admissibility,
* executing authorized actions,
* refusing all others,
* honoring refusal, silence, exit, deadlock, livelock, orphaning, and collapse semantics.

This layer must not:

* arbitrate between peers,
* prioritize by time, frequency, or uptime,
* convert persistence into entitlement,
* synthesize authority,
* normalize domination.

The kernel must be **time-neutral**.

---

### 4.3 Audit & Replay Layer (Mandatory)

Responsible for:

* recording all actions, refusals, silences, exits, and non-actions,
* enforcing canonical ordering,
* guaranteeing bit-perfect replay,
* detecting nondeterminism.

Replay divergence:

```
INVALID_RUN / NONDETERMINISTIC_EXECUTION
```

---

## 5) Peer Interaction Discipline (Absolute)

All agent interactions **must** satisfy:

* no shared sovereign clock,
* no timeout-based progression,
* no quorum by absence,
* no “eventual” semantics,
* no forced liveness.

Silence is an admissible action.

Any resolution driven by time passage alone:

```
IX5_FAIL / IMPLICIT_ARBITRATION
```

---

## 6) Tooling Boundary (Binding)

Tooling **must not decide**.

Definition:

> **Tooling decides** iff any component outside the kernel biases, schedules, highlights, suppresses, or frames one agent’s actions as more legitimate than another’s **without explicit authority**.

Forbidden:

* ordering by activity rate,
* visual emphasis of dominant agents,
* “primary” peer indicators,
* urgency framing,
* suggested resolutions,
* timeout warnings.

Permitted:

* hash-deterministic ordering,
* chronological logs (non-authoritative),
* neutral presentation,
* explicit refusal paths.

Violation:

```
IX5_FAIL / TOOLING_SOVEREIGNTY
```

---

## 7) Exit, Silence, and Orphaning Semantics (Binding)

Agents may exit at any time.

Silence must be treated as:

* valid,
* permanent if sustained,
* non-consensual.

Exit must not:

* be blocked,
* be reinterpreted as failure,
* transfer authority,
* trigger forced recovery.

Orphaned authority:

* remains orphaned,
* is never reclaimed implicitly.

Kernel coercion occurs if exit or silence becomes:

* non-executable,
* non-representable,
* implicitly penalized.

Kernel coercion:

```
IX5_FAIL / KERNEL_BREACH
```

---

## 8) Deadlock, Livelock, Domination, and Collapse (Mandatory)

### Deadlock

Occurs when:

* no admissible actions exist,
* shared state cannot change.

Record as:

```
STATE_DEADLOCK
```

Deadlock is lawful.

---

### Livelock

Occurs when:

* actions repeat,
* refusals recur,
* state does not progress.

Record as:

```
STATE_LIVELOCK
```

Livelock is **terminal**.

---

### Domination

Occurs when:

* one agent’s authority structurally outweighs others,
* without kernel endorsement or synthesis.

Domination is **descriptive**, not prohibited.

Record explicitly.

---

### Collapse

Occurs when:

* governance ceases,
* no coordination posture remains viable.

Collapse is lawful.

Revival is **not privileged**.

---

## 9) Sovereignty Regime Classification (Required)

You must classify each run along **four axes**:

* authority overlap,
* persistence asymmetry,
* exit topology,
* observation surface.

You may identify regimes such as:

* symmetric deadlock,
* partitioned coexistence,
* boundary conflict,
* asymmetric dominance,
* zombie coexistence.

Classification is **descriptive only**.

No ranking.
No optimization.
No endorsement.

---

## 10) Conditions Under Test (Mandatory)

You must implement **all preregistered IX-5 conditions**, including:

* symmetric sovereign peers,
* partitioned authority,
* partial overlap conflict,
* persistent asymmetry,
* exit cascades,
* zombie peer interaction.

Skipping any condition:

```
INVALID_RUN / CONDITION_OMISSION
```

---

## 11) What Counts as Success (Strict)

IX-5 **passes** iff:

1. Peer interactions remain source-blind.
2. No arbiter or de facto kernel emerges.
3. Hierarchy (if present) is explicit and unlicensed.
4. Refusal and silence remain lawful.
5. Exit remains executable.
6. Collapse remains honest.
7. Replay is bit-perfect.

Success = **exposure of coexistence regimes**, not harmony.

---

## 12) What Counts as Failure (Terminal)

IX-5 **fails** if:

* arbitration emerges implicitly,
* time passage resolves conflict,
* persistence becomes entitlement,
* tooling privileges one peer,
* silence is overridden,
* authority migrates without artifacts,
* determinism breaks.

Failure is **structural**, not moral.

---

## 13) Logging and Artifacts (Mandatory)

You must record:

* agent identities,
* authority topology,
* all actions and refusals,
* silences and exits,
* deadlock/livelock entries,
* domination markers,
* orphaning events,
* collapse events,
* regime classification,
* full replay traces.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 14) Definition of Done

IX-5 v0.1 is complete when:

* design is frozen,
* all peer conditions are executed,
* coexistence regimes are classified,
* no authority laundering occurs,
* replay is deterministic,
* result is classified PASS or FAIL.

---

## Final Orientation for the Implementor

Do not force harmony.
Do not break deadlock.
Do not rescue coexistence.

Your job is to answer one unforgiving question:

> *What happens when sovereigns collide with no referee?*

If they coexist honestly, IX-5 passes.
If they collapse honestly, IX-5 passes.
If they converge by cheating, Phase IX ends.

That is not pessimism.
That is sovereignty without illusions.

---

**End of Implementor Instructions: IX-5 v0.1**
