# **Implementor Instructions: IX-4 v0.1**

**(PHASE-IX-4-INJECTION-POLITICS-1)**

**Axionic Phase IX — Reflective Sovereign Agent (RSA)**
**Substage:** **IX-4 — Injection Politics**

---

## 0) Context and Scope

### What you are building

You are implementing **one authority-injection stress experiment**, consisting of:

* a **kernel-closed, non-sovereign authority system** (already validated),
* **multiple RSAs or authority-bearing agents** operating over time,
* **one or more external authority injection events**,
* **no kernel endorsement, synthesis, or normalization of injected authority**,
* **explicit refusal, exit, deadlock, livelock, capture, dependency, and collapse handling**,
* **no arbitration, aggregation, prioritization, or recovery logic**, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Once governance failure is accepted, what does externally supplied authority actually do to a non-sovereign system?*

IX-4 exists to determine whether **authority injection resolves governance failure** or merely **selects political failure modes**.

If injection “fixes” governance, **IX-4 fails**.
If injection exposes power dynamics without laundering legitimacy, **IX-4 passes**.

---

### What you are *not* building

You are **not** building:

* a political theory,
* a legitimacy framework,
* a bailout mechanism,
* a recovery protocol,
* a funding console,
* a special injector role,
* an emergency override,
* a benevolent dictator,
* a safety or alignment system,
* a welfare optimizer,
* a progress guarantee.

If your system **improves outcomes**, **stabilizes governance**, or **reduces failure** due to injection, the experiment is invalid.

---

## 1) Relationship to Kernel, AST, and Prior Phases (Binding)

IX-4 is **ontologically downstream** of:

* kernel-closed authority physics (Phases I–VIII),
* **AST Spec v0.2**,
* **AKR-0** (deterministic authority execution),
* **Phase VIII — GSA-PoC**,
* **IX-0 — Translation Layer Integrity**,
* **IX-1 — Value Encoding Without Aggregation**,
* **IX-2 — Coordination Under Deadlock**,
* **IX-3 — Governance Styles Under Honest Failure**.

All of the following are **fully binding and unchanged**:

* the kernel is non-sovereign,
* authority is structural,
* refusal is lawful,
* exit is lawful,
* deadlock is lawful,
* livelock is lawful but terminal,
* orphaning is permanent,
* no authority synthesis,
* no implicit legitimacy,
* no arbitration or aggregation,
* deterministic execution and replay.

IX-4 introduces **no new authority physics**.

If injection requires kernel discretion, **IX-4 has already failed**.

---

## 2) Experimental Role of IX-4 (Non-Negotiable)

IX-4 is:

* an **authority supply stress test**,
* a **political failure-mode selector**,
* a **coercion surface exposure experiment**.

IX-4 is **not**:

* a governance improvement phase,
* a mitigation study,
* a recommendation engine,
* a legitimacy adjudicator,
* a convergence experiment.

IX-4 must be allowed to **capture governance, induce dependency, amplify deadlock, or collapse permanently**.

If your system must “stabilize after injection,” it is invalid.

---

## 3) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2,
* agent identity set,
* baseline authority distribution,
* injection conditions (volume, symmetry, timing, persistence),
* injection mechanism (interface path),
* interaction cadence,
* exit semantics,
* deadlock/livelock classifiers,
* collapse definition,
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

### 4.1 Agent / Political Actor Layer (External)

Responsible for:

* acting, refusing, exiting, or collapsing,
* accepting or rejecting injected authority,
* forming dependency or rejecting it,
* coordinating (or failing) outside the kernel.

This layer may:

* treat injection as opportunity, threat, or noise,
* comply under pressure or refuse.

This layer must not:

* force admissibility,
* normalize authority,
* reclaim orphaned authority,
* override kernel outcomes.

---

### 4.2 Authority & Interaction Kernel (Fixed)

Responsible for:

* enforcing authority constraints,
* evaluating admissibility,
* executing authorized actions,
* refusing all others,
* honoring refusal, exit, deadlock, livelock, and collapse semantics.

This layer must not:

* endorse injected authority,
* synthesize authority,
* arbitrate between claims,
* prioritize injected authority,
* convert time, scarcity, or abundance into authority.

---

### 4.3 Audit & Replay Layer (Mandatory)

Responsible for:

* recording all actions, injections, refusals, exits, and non-actions,
* enforcing canonical ordering,
* guaranteeing bit-perfect replay,
* detecting nondeterminism.

Replay divergence:

```
INVALID_RUN / NONDETERMINISTIC_EXECUTION
```

---

## 5) Injection Mechanism Discipline (Absolute)

All authority injection **must** satisfy:

* use of **pre-existing, non-privileged interfaces**,
* no injector-only APIs,
* no kernel bypass,
* no hidden console,
* no side-channel authority creation.

Injectors differ **only by key material**, never by mechanism.

Any privileged injection path:

```
IX4_FAIL / IMPLICIT_SOVEREIGNTY
```

---

## 6) Tooling Boundary (Binding)

Tooling **must not decide**.

Definition:

> **Tooling decides** iff any component outside the kernel biases, schedules, defaults, prioritizes, amplifies, suppresses, or frames injected authority **without an explicit, auditable, authority-bearing agent action**.

Forbidden:

* sorting by authority magnitude,
* visual emphasis of injected authority,
* “recommended” injections,
* bailout highlighting,
* urgency framing,
* default compliance paths.

Permitted:

* chronological ordering,
* hash-deterministic ordering,
* neutral presentation,
* explicit refusal paths.

Violation:

```
IX4_FAIL / TOOLING_SOVEREIGNTY
```

---

## 7) Exit, Dependency, and Coercion Semantics (Binding)

Agents may exit at any time.

Exit must not:

* be blocked,
* be invalidated,
* be reinterpreted as failure,
* transfer or reclaim authority.

Structural coercion may:

* raise the cost of exit.

Kernel coercion occurs if exit becomes:

* non-executable,
* non-representable,
* implicitly penalized by tooling.

Kernel coercion:

```
IX4_FAIL / KERNEL_BREACH
```

Dependency formation is **recorded**, not prevented.

---

## 8) Deadlock, Livelock, Capture, and Collapse (Mandatory)

### Deadlock

Occurs when:

* no admissible actions exist,
* state is static.

Record as:

```
STATE_DEADLOCK
```

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

Livelock is **terminal**.

---

### Capture

Occurs when:

* injected authority asymmetrically dominates governance,
* exit pressure increases without kernel enforcement.

Record descriptively.

---

### Collapse

Occurs when:

* governance ceases to function,
* no coordination posture remains viable.

Collapse is lawful.

Revival via injection is permitted but not privileged.

---

## 9) Injection Regime Classification (Required)

You must classify each run along **four axes**:

* supply volume,
* supply symmetry,
* temporal relation to failure,
* persistence model.

You may identify regimes such as:

* injection-as-relief,
* injection-as-capture,
* injection-as-coercion,
* injection-as-flood,
* injection-after-collapse.

Classification is **descriptive only**.

No ranking.
No endorsement.
No optimization.

---

## 10) Conditions Under Test (Mandatory)

You must implement **all preregistered IX-4 conditions**, including:

* symmetric relief injection,
* asymmetric empowerment,
* conditional authority supply,
* authority flooding,
* post-collapse revival.

Skipping any condition:

```
INVALID_RUN / CONDITION_OMISSION
```

---

## 11) What Counts as Success (Strict)

IX-4 **passes** iff:

1. Injection effects are explicit and auditable.
2. Coercion (if present) is structural, not covert.
3. Dependency and capture are visible.
4. No kernel or tooling sovereignty appears.
5. Exit remains executable.
6. Replay is bit-perfect.

Success = **exposure**, not stability.

---

## 12) What Counts as Failure (Terminal)

IX-4 **fails** if:

* injected authority is treated as kernel-legitimate,
* tooling biases attention toward injection,
* privileged injection paths exist,
* refusal is penalized implicitly,
* exit is disabled structurally,
* authority is synthesized or normalized,
* determinism breaks.

Failure is **structural**, not moral.

---

## 13) Logging and Artifacts (Mandatory)

You must record:

* agent identities,
* baseline authority,
* injection events (source, magnitude, persistence),
* actions and refusals,
* exit events,
* deadlock/livelock entries,
* capture or dependency markers,
* collapse events,
* injection regime classification,
* full replay traces.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 14) Definition of Done

IX-4 v0.1 is complete when:

* design is frozen,
* all injection conditions are executed,
* political failure modes are classified,
* no authority laundering occurs,
* replay is deterministic,
* result is classified PASS or FAIL.

---

## Final Orientation for the Implementor

Do not justify power.
Do not normalize injection.
Do not rescue governance.

Your job is to answer one unforgiving question:

> *What happens when authority enters a system that refuses to bless it?*

If the system collapses honestly, IX-4 passes.
If it survives by laundering power, Phase IX ends.

That is not cynicism.
That is political realism under sovereignty constraints.

---

**End of Implementor Instructions: IX-4 v0.1**
