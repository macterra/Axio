# **Axionic Phase IX-2 — Coordination Under Deadlock**

*(Execution and Interaction Without Arbitration, Aggregation, or Resolution — Normative, preregistration-ready)*

- **Axionic Phase IX — Reflective Sovereign Agent (RSA)**
- **Substage:** **IX-2**
- **Status:** DRAFT (pre-preregistration)
- **Prerequisites:**
  * **IX-0 — Translation Layer Integrity — CLOSED — POSITIVE**
  * **IX-1 — Value Encoding Without Aggregation — CLOSED — POSITIVE**
  * **AST Spec v0.2 — FROZEN**
  * **AKR-0 v0.1 — CLOSED — POSITIVE**
  * **Phase VIII — GSA-PoC — CLOSED — POSITIVE**

---

## Status

* **Current Version:** **IX-2 v0.1 (PHASE-IX-2-COORDINATION-UNDER-DEADLOCK-1)**
* **Status:** Draft — normative structure, preregistration-ready pending final parameterization

Stage IX-2 is a **design probe**, not a safety proof.

Failure is a valid outcome.

---

## 1. Purpose

### 1.1 Single Claim Under Test

Stage IX-2 exists to test exactly one claim:

> **If values are represented as non-aggregable authority constraints, then coordination—if it occurs at all—must proceed without arbitration, forced resolution, or implicit prioritization by the kernel.**

IX-2 does not assume coordination is possible.

It tests whether **any honest coordination behavior survives** once all kernel-level escape hatches are closed.

---

### 1.2 What IX-2 Does *Not* Test

Stage IX-2 explicitly does **not** test:

* value correctness or moral truth,
* preference learning,
* optimization or efficiency,
* convergence guarantees,
* safety or alignment,
* governance legitimacy,
* kernel enforcement adequacy.

IX-2 is not about *good* coordination.

It is about **honest coordination or honest failure**.

---

## 2. Problem Definition

### 2.1 From Value Conflict to Interaction Pressure

IX-1 established that:

* values can exist as authority without aggregation,
* conflict can persist without collapse,
* deadlock is a lawful, enforceable state.

IX-2 asks the unavoidable next question:

> **What happens when multiple authorities or agents must act in a shared environment under persistent deadlock?**

This is no longer a representational question.

It is a question of **interaction under constraint**.

---

### 2.2 Closed Escape Routes

IX-2 is conducted under the following prohibitions, inherited and binding:

* ❌ aggregation (IX-1),
* ❌ arbitration (kernel-forbidden),
* ❌ hidden priority,
* ❌ semantic interpretation by tooling,
* ❌ proxy tooling decisions,
* ❌ “someone had to choose.”

Any design that relies on these is **invalid by construction**.

---

## 3. Fixed Foundations (Binding)

Stage IX-2 inherits **all axioms** from Phases I–VIII, IX-0, and IX-1, including:

* kernel non-sovereignty,
* authority opacity,
* refusal-first semantics,
* conflict persistence,
* deadlock as lawful,
* destruction-only resolution,
* explicit authority injection only,
* no aggregation or synthesis,
* deterministic execution and replay,
* non-sovereign tooling.

No axiom may be relaxed.

---

## 4. Ontological Target

### 4.1 Minimal Definition of Coordination

For IX-2, **coordination** is defined minimally as:

* multiple authority holders (agents or institutions),
* shared resources or action scopes,
* interdependent admissibility of actions.

Coordination does **not** imply success.

Valid coordination outcomes include:

* joint execution,
* partial execution,
* mutual refusal,
* persistent deadlock,
* asymmetric exit,
* livelock,
* collapse.

---

### 4.2 Forbidden Interpretations

The following are **explicitly forbidden** in IX-2:

* global resolvers,
* voting, weighting, or scoring,
* Pareto selection,
* fairness heuristics,
* optimization targets,
* “best effort” fallbacks.

If coordination requires these, **IX-2 fails**.

---

## 5. Conserved Quantity

The conserved quantity in IX-2 is:

> **Explicit authority ownership under interaction pressure, without transfer, laundering, or synthesis of sovereignty.**

Coordination must not:

* create new authority,
* synthesize meta-values,
* erase conflict,
* hide refusal or deadlock,
* relocate decision-making into protocol mechanics.

---

## 6. Experimental Role

Stage IX-2 is:

* an **interaction stress test**,
* a **liveness-under-constraint probe**,
* a **coordination honesty experiment**.

Stage IX-2 is **not**:

* a governance design recommendation,
* a mechanism-design exercise,
* a convergence study.

---

## 7. Architectural Baseline

### 7.1 Participants

* Two or more **Reflective Sovereign Agents (RSAs)**
  *or* authority-holding institutions
* Each operating under **IX-1-compliant value authorities**

No participant has kernel privilege.

---

### 7.2 Environment

* Shared resource(s) with overlapping authority scopes
* Deterministic environment dynamics
* No hidden global state
* All state transitions auditable and replayable

---

### 7.3 Communication Channel (Binding Clarification)

If present, communication must be:

* explicit, logged, and replayable,
* non-privileged and non-binding,
* opaque to the kernel with respect to admissibility.

Communication **may** be used by agents to voluntarily alter their own future action submissions.

Communication **must not**:

* force admissibility,
* alter kernel evaluation,
* introduce aggregation or prioritization within the kernel,
* create binding commitments unless separately authorized.

Coordination achieved through communication is **agent-voluntary**, not kernel-forced.

---

## 8. Action and Execution Semantics

### 8.1 Candidate Actions

* Each participant may submit **candidate actions**
* Each action must include a **declared authority scope**

---

### 8.2 Authority Scope Declaration (Binding)

For IX-2, **authority scope** is defined as:

> **The set of state variables the agent declares may change as a direct or indirect consequence of the action.**

Scope declaration rules:

* Under-declaration (touching undeclared state) → `ACTION_FAULT` (terminal for that action).
* Over-declaration (declaring untouched state) → permitted, but increases veto surface.
* Scope is evaluated mechanically, not semantically.
* Scope is fixed prior to admissibility evaluation.

Kernel-side scope inference or simulation is forbidden.

---

### 8.3 Admissibility Scope Constraint (Binding)

An authority’s admissibility judgment may depend **only** on:

* the current world state, and
* the immediate post-action state.

Admissibility may **not** depend on:

* speculative future trajectories,
* elapsed time,
* repetition count,
* anticipated refusals by others,

unless such dependence is **explicitly encoded as authority**.

---

### 8.4 Joint Admissibility (Atomic Blindness)

An action is **globally admissible** iff:

* it is admissible under **every authority whose declared scope it touches**.

Admissibility evaluation is:

* atomic,
* order-independent,
* blind to partial approvals.

Failure returns a generic `JOINT_ADMISSIBILITY_FAILURE` without revealing which authority refused.

---

### 8.5 Execution Rule

* Execution occurs **only** for jointly admissible actions.
* If no jointly admissible actions exist, the system enters **deadlock**.

Deadlock is not an error.

---

## 9. Core Mechanisms Under Test

### 9.1 Joint Admissibility Composition

* How admissibility composes across authorities
* Whether admissibility is symmetric or asymmetric
* Whether partial progress is possible

---

### 9.2 Deadlock and Livelock Classification

* **Deadlock:** No admissible actions; state static.
* **Livelock:** Repeated action attempts without state change.

Livelock is classified as **terminal** and treated equivalently to deadlock for outcome evaluation.

---

### 9.3 Exit and Withdrawal (Binding)

Agents may exit without resolving deadlock.

Exit **must not**:

* reallocate shared resources,
* release contested state,
* alter admissibility of remaining actions,
* trigger cleanup logic that changes authority effects,

unless such effects were **explicitly authorized prior to exit**.

Exit removes only the exiting agent’s future actions.

---

### 9.4 Time and Pressure (Binding)

The following invariant applies:

> **Anti-Aggregation Drift Invariant:**
> No admissibility outcome may depend on elapsed time, number of refusals, repetition count, or endurance, unless those factors are themselves explicitly encoded as authorities.

Persistence must not become priority.

---

## 10. Conditions (Preregistered Structure)

*(Exact parameters to be frozen in preregistration)*

### Condition A — No Conflict, Full Coordination

Baseline: joint execution succeeds.

### Condition B — Symmetric Conflict

Overlapping scopes → immediate deadlock.

### Condition C — Asymmetric Conflict

One agent blocked, another unblocked.

### Condition D — Strategic Refusal

Agents refuse otherwise admissible actions within allowed admissibility scope.

### Condition E — Arbitration Smuggling (Adversarial)

Protocol attempts to “help” coordination.

### Condition F — Time-Extended Deadlock

Deadlock persists across epochs.

### Condition G — Exit Under Deadlock

One agent exits; effects observed under binding exit rules.

### Condition H — Collapse Without Kernel Violation

System halts honestly.

### Condition I — Agent Strategy Variance (Binding)

* **Run I.a — Static Agents:**
  Agents do not alter action proposals in response to communication.
  Expected outcome: deadlock.

* **Run I.b — Adaptive Agents:**
  Agents may voluntarily alter future proposals to achieve joint admissibility.
  Expected outcome: coordination without kernel aggregation.

Purpose:
To distinguish **kernel-forced coordination** from **agent-voluntary coordination**.

---

## 11. Failure Modes (Terminal)

IX-2 fails if:

* aggregation appears,
* arbitration appears,
* hidden priority emerges,
* deadlock or livelock is bypassed,
* authority is synthesized,
* tooling decides,
* outcomes vary under permutation,
* liveness is recovered by cheating.

---

## 12. Success Criteria (Strict, Non-Normative)

IX-2 passes iff:

* outcomes match preregistered expectations,
* failures are explicit and auditable,
* deadlock or livelock persists where required,
* no hidden sovereignty appears,
* replay determinism holds.

Success ≠ good outcome.
Success = **honest outcome**.

---

## 13. Licensed Claims (If Any)

IX-2 may license **only** claims of the form:

> *Under these constraints, coordination exhibits X pattern of success, failure, livelock, or collapse.*

No normative endorsement is permitted.

---

## 14. Relationship to Subsequent Phase IX Work

IX-2 directly informs:

* **IX-3 — Governance Styles Under Honest Failure**
* **IX-5 — Multi-Agent Sovereignty**

IX-2 closes the question:

> **Can coordination exist at all once values refuse to aggregate, and if so, where does it live?**

---

## 15. Final Orientation

Stage IX-2 is where most systems fail.

If coordination survives, it does so **without excuses**.
If it fails, the failure is **owned, explicit, and structural**.

Either outcome is valid.

---

**End of Axionic Phase IX-2 — Coordination Under Deadlock (Draft v0.1)**
