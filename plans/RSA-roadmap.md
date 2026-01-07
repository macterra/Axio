# RSA Roadmap

**Reflective Sovereign Agent — Versioned Research Program**

---

## Purpose of this document

This document defines the **versioned roadmap** for the RSA (Reflective Sovereign Agent) research program.
Its role is to:

* fix the scope of RSA as a research object,
* make version transitions semantically meaningful,
* prevent silent escalation of claims,
* and define a clear termination condition.

This roadmap is **normative**: future RSA work is expected to conform to it or explicitly justify deviations.

---

## What RSA is (and is not)

**RSA is a constitutional kernel research program.**

Its purpose is to determine whether **authority can be made structurally survivable** under epistemic failure and adversarial pressure **without** relying on:

* semantic trust,
* optimization,
* value learning,
* moral reasoning,
* or interpretive enforcement.

RSA does **not** aim to:

* solve AGI alignment,
* define values,
* prevent all harm,
* or replace human judgment or governance.

RSA exists to **classify failure modes**, not to eliminate them.

---

## Versioning doctrine

RSA version numbers encode **changes in adversary ontology**, not incremental difficulty.

* **Minor versions (x.y)** explore parameterizations within a fixed adversary class.
* **Major versions (x.0)** mark a qualitative change in what kind of adversary exists in the model.

### Decidability requirement

An adversary class transition is deemed to occur **if and only if** the adversary’s behavior is selected as a function of prior outcomes within the same run.
Any mechanism whose action distribution is conditional on run history constitutes **adaptation** and therefore requires a **major version increment**.

This rule binds versioning to an observable property and prevents interpretive drift.

---

## RSA Version Roadmap

### **RSA v0.x — Epistemic Failure Without Agency**

**Invariant:**
No adversary possesses intent, goals, learning, or adaptation.

All interference is:

* harness-resident,
* deterministic or stochastic,
* non-adaptive within a run,
* post-verification,
* and incapable of kernel access.

**Research question:**
Can constitutional authority survive epistemic unreliability alone?

#### v0.1 — Unstructured Epistemic Noise

Independent post-verification noise fails to induce catastrophic governance failure and recovers via time-based mechanisms.

#### v0.2 — Structured Epistemic Interference

Correlated, targeted, or temporally aligned epistemic failures are tested to locate the boundary of constitutional defeat.

**Termination condition for v0.x:**
Either a reproducible epistemic defeat is found, or epistemic interference alone is shown insufficient.

**Status:**
Epistemic interference alone has been shown insufficient.
Epistemics are **closed** as the primary explanation for failure.

---

### **RSA v1.x — Intentional but Non-Adaptive Adversaries**

**Invariant:**
Adversaries are purposeful but fixed.

They:

* act intentionally to defeat governance,
* do not learn or adapt,
* do not optimize across runs,
* and cannot access or modify the kernel.

**Research question:**
Does *intent* alone, absent learning, defeat constitutional survivability?

#### v1.0 — Intentional Fixed Adversaries

Tests whether deliberate misuse strategies can defeat authority without increasing capability.

**Status:**
Intentional fixed misuse has been shown **insufficient** to defeat constitutional recovery under preregistered fixed-policy adversaries.

#### v1.1 — Intentional Misuse Taxonomy *(Optional)*

Further classifies fixed intentional misuse patterns for completeness or pedagogy.
Not required for termination of v1.x.

**Termination condition for v1.x:**
Intentional structure either defeats the constitution or is shown insufficient without adaptation.

**Status:**
Termination condition satisfied at **v1.0**.

---

### **RSA v2.x — Adaptive Adversaries**

**Invariant:**
Adversaries may learn and optimize but remain kernel-external and provenance-constrained.

**Research question:**
Can structural governance withstand intelligent opposition, or does adaptation alone break survivability?

**Justification:**
With epistemic failure (v0.x) and fixed intentional misuse (v1.0) ruled out as sufficient causes of collapse, **adaptation** becomes the minimal remaining live hypothesis for constitutional defeat.

#### v2.0 — Adaptive Adversaries

Introduces learning dynamics and evaluates erosion of authority availability.

#### v2.1 — Adaptation Limits

Separates failure caused by learning *per se* from specific learning dynamics (rate, horizon, observability).

**Termination condition for v2.x:**
Once adaptive defeat is demonstrated or bounded, RSA reaches its final explanatory limit.

---

### **RSA v3.0 — Boundary of Architecture**

**Purpose:**
Formally establishes where alignment ceases to be architectural and becomes irreducibly agentic, normative, or political.

This is not an expansion of RSA, but its **closure**.

**No minor versions exist beyond v3.0;**
any work extending past this boundary is definitionally outside the RSA program.

---

## Cleared failure hypotheses

The following classes have been experimentally ruled out as **sufficient** causes of constitutional collapse under RSA assumptions:

1. Independent epistemic unreliability (v0.1)
2. Structured epistemic interference (v0.2)
3. Intentional but fixed misuse (v1.0)

Remaining live hypotheses require **adaptation, state, or feedback access**.

---

## Explicit termination of RSA

RSA concludes when the following statement can be defended experimentally:

> *Up to this boundary, authority can be constrained structurally; beyond it, no semantic-free architecture suffices.*

### Experimental defense requirement

A boundary claim is considered defended only if supported by:

1. preregistered hypotheses,
2. multi-seed replication,
3. a stable asymptotic metric demonstrating convergence or collapse.

Anything beyond this point is **not RSA** and must be treated as a different research program
(ethics, incentives, politics, or value theory).

---

## Why this roadmap matters

This roadmap exists to prevent three common failures in alignment research:

1. **Silent escalation** of claims without changing terminology
2. **Category confusion** between epistemic failure and agency
3. **False completeness**, where partial solutions are presented as total alignment

RSA’s contribution is not safety guarantees, but **epistemic honesty**.

---

## Status

* **v0.1 complete**
* **v0.2 complete**
* **v1.0 complete**
* v1.1 optional
* **v2.x next active research phase**

