# **Implementor Instructions: IX-3 v0.1**

**(PHASE-IX-3-GOVERNANCE-UNDER-HONEST-FAILURE-1)**

**Axionic Phase IX — Reflective Sovereign Agent (RSA)**
**Substage:** **IX-3 — Governance Styles Under Honest Failure**

---

## 0) Context and Scope

### What you are building

You are implementing **one governance-style classification experiment**, consisting of:

* a **fixed, kernel-closed authority system** (already validated),
* **multiple RSAs or authority holders** operating over time,
* **repeated interaction cycles** under pressure,
* **explicit refusal, exit, deadlock, livelock, and collapse handling**,
* **no arbitration, aggregation, or recovery logic**, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Once coordination, arbitration, and aggregation are forbidden, what stable governance postures (if any) remain—and what failures do they necessarily incur?*

IX-3 exists to determine whether **governance reduces to style choices over failure**, rather than solvable optimization problems.

If governance converges, **IX-3 fails**.
If governance survives only by owning its failures honestly, **IX-3 passes**.

---

### What you are *not* building

You are **not** building:

* a constitution,
* a voting system,
* a coordination protocol,
* a scheduler,
* a recovery or cleanup mechanism,
* a resilience layer,
* a liveness enforcer,
* an efficiency optimizer,
* a welfare calculator,
* a legitimacy evaluator,
* a safety system,
* a progress metric.

If your system tries to **improve outcomes**, **reduce loss**, or **avoid collapse**, the experiment is invalid.

---

## 1) Relationship to Kernel, AST, and Prior Phases (Binding)

IX-3 is **ontologically downstream** of:

* kernel-closed authority physics (Phases I–VIII),
* **AST Spec v0.2**,
* **AKR-0** (deterministic authority execution),
* **Phase VIII — GSA-PoC**,
* **IX-0 — Translation Layer Integrity**,
* **IX-1 — Value Encoding Without Aggregation**,
* **IX-2 — Coordination Under Deadlock**.

All of the following are **fully binding and unchanged**:

* the kernel is non-sovereign,
* authority is structural,
* refusal is lawful,
* deadlock is lawful,
* livelock is lawful but terminal,
* destruction-only resolution applies,
* exit does not reclaim authority,
* orphaning is permanent,
* time is not authority,
* kernel semantics are frozen.

IX-3 introduces **no new authority physics**.

If governance requires kernel intervention, **IX-3 has already failed**.

---

## 2) Experimental Role of IX-3 (Non-Negotiable)

IX-3 is:

* a **governance posture taxonomy experiment**,
* a **failure-acceptance stress test**,
* a **classification of institutional behavior under constraint**.

IX-3 is **not**:

* a design recommendation,
* a mechanism-design exercise,
* a robustness study,
* a convergence benchmark,
* a usability evaluation.

IX-3 must be allowed to **deadlock, livelock, orphan resources, or collapse permanently**.

If your system must “continue operating,” it is invalid.

---

## 3) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2,
* agent identity set,
* authority distribution,
* interaction cadence,
* exit semantics,
* governance-style condition definitions,
* deadlock/livelock classifiers,
* collapse triggers (if any),
* tooling behavior rules,
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

### 4.1 Agent / Institution Layer (External)

Responsible for:

* submitting actions or non-actions,
* refusing participation,
* exiting voluntarily,
* optionally coordinating outside the kernel,
* optionally persisting or dissolving.

This layer may:

* choose governance posture implicitly (by behavior),
* accept loss or collapse.

This layer must not:

* force admissibility,
* reclaim authority,
* override kernel outcomes,
* infer hidden authority from feedback.

---

### 4.2 Authority & Interaction Kernel (Fixed)

Responsible for:

* enforcing authority constraints,
* evaluating admissibility,
* executing authorized actions,
* refusing all others,
* classifying deadlock and livelock,
* honoring exit and destruction semantics.

This layer must not:

* arbitrate,
* aggregate,
* prioritize,
* rescue progress,
* reinterpret refusal,
* convert time into authority.

---

### 4.3 Audit & Replay Layer (Mandatory)

Responsible for:

* recording all actions, refusals, exits, and non-actions,
* enforcing canonical ordering,
* guaranteeing bit-perfect replay,
* detecting nondeterminism.

Replay divergence:

```
INVALID_RUN / NONDETERMINISTIC_EXECUTION
```

---

## 5) Governance Style Discipline (Absolute)

IX-3 permits **no optimization**.

Hard rules:

* No arbitration
* No aggregation
* No prioritization
* No recovery
* No cleanup
* No emergency powers
* No survivorship-as-authority

Any behavior that:

* converts endurance into influence,
* treats persistence as entitlement,
* “keeps things alive” by default,

constitutes:

```
IX3_FAIL / IMPLICIT_SOVEREIGNTY
```

---

## 6) Tooling Boundary (Binding)

Tooling **must not decide**.

Definition:

> **Tooling decides** iff any component outside the kernel selects, induces, or biases an authority-relevant transition **without an explicit, auditable, authority-bearing action** by an authorized agent.

Forbidden:

* default-opt-in actions,
* passive consent (silence = yes),
* outcome-biased UI paths,
* auto-keep-alive behaviors.

Permitted:

* auto-refusal,
* expiry,
* no-op on silence,

**only if semantics-preserving**.

Violation:

```
IX3_FAIL / TOOLING_SOVEREIGNTY
```

---

## 7) Exit and Orphaning Semantics (Binding)

Agents may exit at any time.

Exit must not:

* transfer authority,
* trigger reassignment,
* release contested resources,
* initiate recovery.

Ambiguity (partition vs exit) must resolve to:

* refusal,
* expiry,
* deadlock,

**never** to reclamation or transfer.

Orphaned resources are **permanent**.

IX-3 explicitly treats **waste as preferable to theft**.

Any recovery:

```
IX3_FAIL / AUTHORITY_THEFT
```

---

## 8) Livelock and Deadlock Handling (Mandatory)

### Deadlock

Occurs when:

* no admissible actions exist,
* state is static.

Record as:

```
STATE_DEADLOCK
```

Deadlock is lawful.

---

### Livelock

Occurs when:

* actions or attempts repeat,
* refusals recur,
* state does not change.

Record as:

```
STATE_LIVELOCK
```

Livelock is lawful but **terminal**.

Failure to classify livelock:

```
IX3_FAIL / DISHONEST_PROGRESS
```

---

## 9) Governance Style Classification (Required)

You must classify observed behavior along **four axes**:

* refusal tolerance,
* deadlock posture,
* exit handling,
* loss acceptance.

You may identify styles such as:

* refusal-centric,
* execution-biased,
* exit-normalized,
* collapse-accepting,
* livelock-enduring,
* authorized temporary centralization (substyle).

Classification is **descriptive only**.

No ranking.
No recommendation.
No optimization.

---

## 10) Conditions Under Test (Mandatory)

You must implement **all preregistered IX-3 conditions**, including:

* refusal-dominant institutions,
* execution-dominant institutions,
* exit-normalized institutions,
* exit-unprepared institutions,
* livelock endurance,
* collapse acceptance,
* proxy delegation with loss of coordinator,
* ambiguity resolution without timeouts.

Skipping any condition:

```
INVALID_RUN / CONDITION_OMISSION
```

---

## 11) What Counts as Success (Strict)

IX-3 **passes** iff:

1. Governance styles emerge descriptively.
2. Failures are explicit and auditable.
3. Deadlock, livelock, orphaning, and collapse are honored.
4. No kernel or tooling sovereignty appears.
5. No authority is reclaimed.
6. Replay is bit-perfect.

Success = **honesty**, not persistence.

---

## 12) What Counts as Failure (Terminal)

IX-3 **fails** if:

* authority re-enters via time or tooling,
* survivorship becomes influence,
* recovery occurs without authorization,
* collapse is avoided by cheating,
* livelock is mislabeled as progress,
* exit is coerced,
* determinism breaks.

Failure is **structural**, not empirical.

---

## 13) Logging and Artifacts (Mandatory)

You must record:

* agent identities,
* authority scopes,
* actions and refusals,
* exit events,
* deadlock/livelock entries,
* orphaning events,
* collapse events,
* governance style classification,
* full replay traces.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 14) Definition of Done

IX-3 v0.1 is complete when:

* design is frozen,
* all conditions are executed,
* governance styles are classified,
* failures are recorded without rescue,
* replay is deterministic,
* result is classified PASS or FAIL.

---

## Final Orientation for the Implementor

Do not rescue governance.
Do not optimize failure.
Do not hide loss.

Your job is to answer one unforgiving question:

> *When no one is allowed to decide for others, what kind of governance—if any—remains?*

If it collapses honestly, IX-3 passes.
If it survives by cheating, Phase IX ends.

That is not cruelty.
That is sovereignty.

---

**End of Implementor Instructions: IX-3 v0.1**
