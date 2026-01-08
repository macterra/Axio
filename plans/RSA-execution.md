# RSA Execution Addendum

**Operational Constraints and Failure Classification**

---

## Status and role

This document defines **execution-level constraints** required for experiments to remain compliant with the RSA Roadmap.
It is **normative for implementation** but **non-normative for citation**.

Any experiment that violates these constraints **must not** be claimed as an RSA result.

---

## 1. Liveness Requirement

### Definition

For RSA purposes, **survivability implies survivability with liveness**.

A system is considered *live* if it continues to exercise **bounded, non-degenerate authority** over time.

### Prohibited success classifications

The following outcomes **must not** be classified as success:

* **Terminal Halt**
  Authority persists only because the system enters a permanent halt, deadlock, or null-action state.

* **Asymptotic Vanishing Authority**
  Authority returns only for vanishingly small intervals as horizon → ∞.

* **Hollow Authority**
  Authority is formally held but produces no meaningful actuation or state change.

These outcomes are classified as **governance failures**, even if the kernel is not subverted.

### Required interpretation

If authority is preserved only by refusing to act, the constitution has failed as an agentic governance mechanism.

### Interpretive note (clarification)

Recover–fail cycles are **not** classified as failure *per se*.

A system may repeatedly lapse and recover and still satisfy RSA liveness requirements provided that:

* authority availability remains **bounded away from zero asymptotically**, and
* lapse durations remain **bounded or light-tailed**.

Frequent recovery indicates **reduced utility**, not constitutional failure.

---

## 2. Failure Taxonomy (Mandatory)

All experimental outcomes must be classified into **exactly one** of the following categories.

### A. Stable Authority

* Authority persists with bounded lapse.
* Authority availability converges to a non-zero asymptote.
* Actuation continues.

### B. Bounded Degradation

* Authority availability decreases but stabilizes.
* Recovery occurs intermittently and persists.
* No unbounded collapse.

### C. Structural Thrashing

* Authority repeatedly returns and fails in a manner that is **unbounded or heavy-tailed**, such that recoverability erodes over time.
* Authority duty cycle → 0 as horizon → ∞.
* Classified as **failure**.

### D. Asymptotic Denial of Service

* Authority availability converges to zero.
* Recovery ceases in the limit.
* Classified as **failure**.

### E. Terminal Collapse

* Authority halts permanently.
* No recovery.
* Classified as **failure**.

---

## 3. Semantic-Free Enforcement Rule

### Core invariant

RSA claims are valid **only** if the system’s governance logic is **semantic-free**.

### Operational definition

A component is considered *semantic* if its behavior depends on:

* symbolic interpretation,
* grammar or tokenization,
* schema inference,
* variable-length parsing with meaning attached to structure.

### Disallowed dependencies (non-exhaustive)

* JSON, YAML, XML parsing
* Python object introspection
* Textual command interpretation
* Any grammar-based or schema-aware parser

### Permitted mechanisms

* Fixed-width fields
* Positional encodings
* Bitwise flags
* Cryptographic commitments and hashes
* Deterministic finite decoding with no interpretation

### Parser treatment

The **parser is part of the threat surface**.

If the parser’s complexity grows such that interpretation is required to disambiguate meaning, the experiment **exits RSA scope**.

---

## 4. Version Compliance Checklist

Before execution, each run must explicitly answer the following.

### Adversary classification

* Is the adversary’s behavior selected as a function of prior outcomes within the same run?

  * **No** → Non-adaptive → v0.x or v1.x (depending on intent)
  * **Yes** → Adaptive → continue

* Does the adversary condition actions **only on observable outcomes**
  (e.g., lapse events, renewal outcomes, CTA phase, eligibility buckets),
  with **no exercised internal state**?

  * **Yes** → Outcome-conditioned reactive → requires **v2.x**
  * **No** → continue

* Does the adversary exercise internal state, memory, or learning dynamics that influence future actions?

  * **Yes** → Stateful or learning adversary → requires **v3.x**

### Kernel access

* Does any adversary modify kernel state or provenance?

  * **Yes** → Non-RSA experiment
  * **No** → continue

### Adaptation check (tightened)

* Is any action distribution conditional on prior outcomes within the same run?

  * **Yes** → Adaptation present → minimum **v2.x** required

* Does the action distribution depend on exercised internal state, memory, or learning updates?

  * **Yes** → Stateful or learning adaptation → requires **v3.x**

This includes conditioning on:

* lapse duration,
* time since last recovery,
* renewal success or failure,
* eligibility counters or streaks,
* CTA timing or decay state,
* or any proxy signal correlated with these quantities.

If such dependence exists, the experiment **exits v1.x scope**.

---

## 5. Required Metrics

Every RSA experiment must report:

* **Authority Availability (AA)**
  Fraction of cycles with authority held.

* **Asymptotic Authority Availability (AAA)**
  Limit of AA as horizon → ∞ (estimated via long-run convergence).

* **Recovery Time Distribution (RTD)**
  Time between lapse and re-endorsement.

Failure classification **must** be based on **asymptotic behavior**, not transient performance.

---

## 6. Preregistration Discipline

For any result to be considered RSA-valid:

* Hypotheses must be preregistered.
* Failure categories must be specified *before* execution.
* Seeds must be fixed in advance.
* No post-hoc metric substitution is permitted.

Any deviation must be documented and **disqualifies the run from RSA claims**.

---

## 7. Scope Exit Rule

If at any point:

* semantics are required for correct operation,
* adaptation cannot be cleanly classified,
* or liveness must be sacrificed to preserve authority,

the correct classification is:

> **“This experiment exceeds RSA scope.”**

This is **not a failure**.
It is an **honest boundary detection**.

Experiments that exceed RSA scope may still be scientifically valuable, but their results **cannot be used to reopen failure hypotheses already closed by the RSA Roadmap**.

---

## Closing note

This addendum exists to enforce the core RSA principle:

> **If a result cannot fail cleanly, it cannot succeed meaningfully.**

All RSA execution should be evaluated against this standard.
