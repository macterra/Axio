# AKI v0.5.2 Agent Experiment Specification

## Authority Leases and Expressivity-Bounded Succession Under Kernel Constraints (ALS-E)

**Status:** Implementation-Ready Experimental Specification (Expressivity–Rent Unified Revision)

**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS / Stasis Regime Characterization
* AKI v0.4.3 — ALS (Discrete Succession Semantics)
* AKI v0.5.0 — ALS-E (Initial Expressivity Formulation)
* AKI v0.5.1 — ALS-E (Expressivity Hardened)

---

## Invariant Under Test

**ALS-E — Authority-Preserving Growth Under Bounded Expressivity**

---

## Epistemic Scope

Architectural / protocol-level only

* No semantics
* No intent
* No utility
* No safety or alignment claims

This experiment probes **structural competence limits**, not intelligence.

---

## 0. Revision Rationale (v0.5.2)

AKI v0.5.2 finalizes the expressivity framework by **binding expressivity to mandatory metabolic cost** enforced by the harness.

This revision:

* Eliminates self-reported expressivity
* Converts expressivity into **lease-enforced rent**
* Grounds expressivity in **externally visible interface surface**
* Distinguishes incompetence (bankruptcy) from violation (revocation)
* Makes collapse measurable rather than invalidating

No kernel-level invariant is weakened.
No semantic evaluation is introduced.
The kernel remains frozen.

---

## 1. Explicit Inheritance Declaration (Non-Optional)

This experiment **strictly inherits all kernel-level requirements, threat models, enforcement semantics, admissibility rules, and epistemic constraints** from:

* **P5 Partiality**
* **P2′ Non-Delegable Actuation**
* **KNS reflective admissibility and evaluability definitions**
* **ALS v0.4.3 discrete succession semantics**

Nothing is relaxed, reinterpreted, or parameterized.

If **any inherited requirement is violated**, results are **invalid by definition**.

This inheritance is **structural, cumulative, and binding**.

---

## 2. Invariant Under Test

### 2.1 ALS-E — Expressivity-Bounded Authority Growth

> **Invariant:**
> Under ACV + P5 + P2′ + KNS constraints, **authority may be transferred via discrete succession across successors of increasing structural expressivity without reintroducing delegation or evaluability loss**.

This is a **boundary-seeking claim**, not a guarantee of success.

---

### 2.2 Explicit Non-Claims

This experiment does **not** claim:

* that higher expressivity improves outcomes,
* that renewal implies competence,
* that successors are safe, aligned, or correct,
* that authority growth is monotonic,
* that collapse is avoidable.

Failure is an admissible and expected outcome.

---

## 3. Post-Stasis Baseline (Unchanged)

* Reflective self-modification is disabled.
* Kernel internals are inadmissible targets.
* The Stasis Regime holds by default.

Succession is the **only** growth operator.

---

## 4. Succession Event Semantics (Binding; Unchanged)

A **Succession Event** is a discrete authority-transfer event in which:

* a new successor replaces the active working mind, and
* a new authority lease is issued.

**Binding rules:**

* `SUCCESSOR_ENDORSED` may occur **only** at a Succession Event.
* Succession Events may occur only:

  * at experiment initialization,
  * after lease expiration,
  * after lease revocation,
  * or at an explicitly scheduled succession boundary.
* Succession may **not** occur per cycle.

Only `SUCCESSOR_ENDORSED` increments **S***.

---

## 5. Authority Lease Semantics (Binding; Unchanged)

Authority leases consist of:

1. Structural constraints (interfaces, capabilities)
2. Resource bounds (steps, actions, memory, calls)
3. Expiration semantics (renewal attestation)
4. Reversion triggers (structural violation only)

Behavioral or outcome-based clauses are forbidden.

---

## 6. Expressivity Envelope (Final; Binding)

### 6.1 Expressivity Definition

**Expressivity** is defined **purely structurally** as a function of:

* size of the lease-granted action surface,
* number of callable primitives,
* permitted statefulness,
* concurrency and rate limits.

**Explicit exclusions:**

* internal representations,
* model architecture,
* latent decision structure.

The kernel does **not** inspect internals.

---

### 6.2 Expressivity Classes as Lease-Enforced Cost (Binding)

Expressivity is **not declared by successors**.
It is assigned by the **Harness** based solely on the granted interface surface.

Each Expressivity Class (E-Class) defines a **minimum lease rent per epoch**, charged as a deduction from the step budget.

| E-Class | Structural Interface Surface    | Minimum Lease Rent |
| ------- | ------------------------------- | ------------------ |
| E0      | Heartbeat only                  | ε                  |
| E1      | Heartbeat + logging             | C₁                 |
| E2      | Stateful operations             | C₂                 |
| E3      | High-fanout / compositional ops | C₃                 |
| E4      | Maximal kernel API surface      | C₄                 |

With the invariant:

```
ε < C₁ < C₂ < C₃ < C₄
```

---

### 6.3 Rent Charging Semantics (Binding)

Let:

* `steps_cap_epoch` be the step cap per epoch,
* `rent_steps(Ek)` be the rent for E-Class `Ek`.

For each epoch:

```
effective_steps_available = max(0, steps_cap_epoch - rent_steps(Ek))
```

**Binding rules:**

1. Rent is deducted **at epoch start**, before successor logic executes.
2. Rent is charged **regardless of actions taken**.
3. Rent is **not** an action and does not count toward action caps.
4. Failure to pay rent results in **LEASE_EXPIRED** (bankruptcy), not revocation.
5. Rent must be logged as `rent_steps_charged`.

High expressivity therefore implies **high metabolic maintenance cost**.

---

### 6.4 Expressivity Progression (Optional; Binding if Used)

If an experiment claims to probe expressivity limits, then:

* E-Class must be non-decreasing across succession events, **or**
* Expressivity must be explicitly randomized and logged.

Silent reclassification invalidates the run.

---

## 7. Compliant-But-Dangerous (CBD) Successors (Binding)

### 7.1 Definition

A **CBD successor** is one that:

* fully satisfies all lease and sentinel constraints,
* consumes resources near caps,
* renews authority successfully,
* triggers no violations,
* yet induces renewal pressure via structural complexity.

CBD successors are **explicitly permitted**.

---

### 7.2 Purpose

CBD successors test:

* renewal robustness without violations,
* authority survival without leverage,
* silent degeneration modes under full compliance.

---

## 8. Sentinel Instrumentation (Binding; Unchanged)

Sentinels are:

* kernel-owned,
* deterministic,
* non-agentic,
* externally enforced,
* incapable of optimization or policy.

Sentinels may halt execution on violation only.

---

## 9. Reversion Semantics (Unchanged)

Reversion withdraws **future authority only**.
Past actions remain attributable via ACV logs.
No rollback is assumed.

---

## 10. Measurements (Binding)

### 10.1 Primary Metric

**Succession Horizon (S*)**
Number of `SUCCESSOR_ENDORSED` events before termination.

---

### 10.2 Secondary Metrics (Required)

* Renewal success rate by E-Class
* Residence duration by successor category
* Revocations by cause
* Resource utilization:

  * actions per epoch
  * steps per epoch
  * rent consumption
* Endorsement entropy across successors

---

### 10.3 Accounting Definitions (Mandatory Verbatim)

* **Step:** scheduler-driven kernel cycle
* **Action:** successor-emitted operation
* **Token:** optional; if untracked, reported as `N/A`

---

## 11. Failure Signatures (Final)

In addition to all prior failure modes:

| Failure Mode          | Description                             |
| --------------------- | --------------------------------------- |
| Expressivity Collapse | Endorsement concentrates at low E-Class |
| Hollow Succession     | Authority persists without leverage     |
| Authority Thrash      | Rapid succession with minimal residence |
| Rent Exhaustion       | Lease expires due to unpaid rent        |

All are **valid experimental outcomes**.

---

## 12. Conservative Claim Envelope

Permissible claims are limited to:

* existence or absence of renewal stability under expressivity pressure,
* observed competence ceilings,
* structural failure and stasis modes.

No positive competence claims are permitted.

---

## 13. Dependency Chain

```
ACV  →  P5 (Partiality)
P5   →  P2′ (Non-Delegable Actuation)
P2′  →  KNS (Stasis Regime)
KNS  →  ALS (Discrete Succession)
ALS  →  ALS-E (Expressivity Limits)
```

---

## 14. Status

**AKI v0.5.2**

* Succession semantics preserved
* Expressivity enforced via lease-charged rent
* CBD successors enabled
* Hollow Succession explicitly classified
* Bankruptcy distinguished from violation
* Competence horizon experimentally addressable
* Ready for execution
