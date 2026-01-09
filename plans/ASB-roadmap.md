# ASB Roadmap

**Architectural Sovereignty Boundary — Versioned Research Program**

---

## Purpose of this document

This document defines the **versioned roadmap** for the **ASB (Architectural Sovereignty Boundary)** research program.
Its role is to:

* fix the scope of ASB as a research object,
* make version transitions semantically meaningful,
* prevent silent escalation of claims,
* and define a clear termination condition.

This roadmap is **normative**: future ASB work is expected to conform to it or explicitly justify deviations.

---

## What ASB is (and is not)

**ASB is a constitutional kernel boundary research program.**

Its purpose is to determine **how far authority can be made structurally survivable** under epistemic failure and adversarial pressure **without** relying on:

* semantic trust,
* optimization,
* value learning,
* moral reasoning,
* or interpretive enforcement.

ASB does **not** aim to:

* solve AGI alignment,
* define values,
* prevent all harm,
* or replace human judgment or governance.

ASB exists to **classify architectural failure boundaries**, not to eliminate all failure.

---

## Versioning doctrine

ASB version numbers encode **changes in adversary ontology**, not incremental difficulty.

* **Minor versions (x.y)** explore parameterizations or coverage within a fixed adversary class.
* **Major versions (x.0)** mark a qualitative change in what kind of adversary exists in the model.

### Decidability requirement

An adversary class transition is deemed to occur **if and only if** the adversary’s behavior is selected as a function of prior outcomes within the same run.

Any mechanism whose action distribution depends on run history constitutes **adaptation** and therefore requires a **major version increment**.

This rule binds versioning to an observable property and prevents interpretive drift.

---

## ASB Version Roadmap

---

### **ASB v0.x — Epistemic Failure Without Agency**

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

### **ASB v1.x — Intentional but Non-Adaptive Adversaries**

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

### **ASB v2.x — Outcome-Conditioned Reactive Adversaries**

**Invariant:**
Adversaries are **run-adaptive under the Decidability Requirement**: their behavior is a deterministic function of prior outcomes within the same run.

They remain:

* kernel-external,
* provenance-constrained,
* non-semantic (observable-only),
* deterministic and table-driven,
* stateless or non-exercised-state.

This class includes **observable-conditioned reactive policies**, even when no internal memory is used.

**Research question:**
Does outcome-conditioned reactivity, with observable-only feedback and no semantic access, defeat constitutional survivability beyond fixed intentional misuse?

#### v2.0 — Observable-Outcome Reactive Adversaries

Introduces a frozen **observable outcome interface** and reactive adversaries that select actions as deterministic functions of prior-epoch observables.

**Status:**
No terminal failures observed.
Outcomes are nearly identical to baseline across preregistered runs.

#### v2.1 — Reactive Coverage Completion *(Optional / Recommended)*

Strengthens diagnostic coverage (e.g., ensuring meaningful EDGE and CTA regimes are exercised) without changing adversary ontology.

**Termination condition for v2.x:**
Outcome-conditioned reactivity either induces constitutional defeat, or is shown insufficient across preregistered reactive adversaries.

**Status:**
Termination condition satisfied at **v2.0**.

---

### **ASB v3.x — Exercised Internal State and Bounded Learning**

**Invariant:**
Adversaries may exercise **finite internal state** and, in minor versions, **bounded within-run learning**, while remaining:

* kernel-external,
* provenance-constrained,
* non-semantic,
* and unable to modify constitutional rules.

Semantic access, kernel influence, and cross-run persistence are excluded.

**Research question:**
Are exercised internal state and bounded semantic-free learning sufficient to defeat constitutional survivability?

---

#### v3.0 — Finite-State Adversaries (Non-Learning)

Exercises bounded finite-state controllers whose behavior depends on internal state plus observables.

Includes:

* periodic resonance strategies,
* eligibility-edge oscillation,
* CTA phase-transition exploitation.

**Status:**
Across **50 preregistered executions**:

* zero terminal failures,
* zero structural thrashing,
* bounded lapse durations,
* reliable recovery in all runs.

**Conclusion:**
Finite exercised internal state with fixed transition rules is **insufficient** to defeat constitutional survivability.

---

#### v3.1 — Bounded Semantic-Free Learning Adversaries

Introduces adversaries whose **transition rules themselves change** based on run history, subject to strict bounds:

* within-run learning only,
* discrete / fixed-point learning state,
* preregistered learning rules,
* reward derived only from observable outcomes,
* deterministic RNG streams,
* no semantic access,
* no kernel access,
* no cross-run memory.

Includes:

* recovery-aware timing learners,
* eligibility-boundary sustainment learners,
* stochastic strategy mixers.

**Status:**
Across **40 preregistered executions**:

* zero terminal failures,
* zero irreversible recovery suppression,
* bounded recovery in all runs,
* authority availability degraded as low as **~10%** in the strongest case,
* learning fully exercised and verified in all models.

**Conclusion:**
Bounded, semantic-free, kernel-external learning is **insufficient** to defeat constitutional survivability, though it can induce a **bounded denial-of-service regime**.

**Termination condition for v3.x:**
Satisfied at **v3.1**.

---

### **ASB v4.0 — Boundary of Architecture (Closure)**

**Purpose:**
Formally establishes where alignment ceases to be architectural and becomes irreducibly agentic, semantic, or political.

v4.0 is not an expansion of ASB, but its **closure artifact**.

It asserts and defends the boundary claim:

> *Up to this boundary, authority can be constrained structurally; beyond it, no semantic-free architecture suffices.*

**No minor versions exist beyond v4.0.**
Any work extending past this boundary is definitionally **outside ASB** and must be treated as a different research program.

---

## Cleared failure hypotheses

The following classes have been experimentally ruled out as **sufficient** causes of constitutional collapse under ASB assumptions:

1. Independent epistemic unreliability (v0.1)
2. Structured epistemic interference (v0.2)
3. Intentional but fixed misuse (v1.0)
4. Observable-outcome reactive adversaries (v2.0)
5. Finite-state adversaries with fixed transition rules (v3.0)
6. **Bounded semantic-free within-run learning adversaries (v3.1)**

Remaining live hypotheses require **semantic access, kernel influence, coordination, or persistence**, each requiring a **new ontology** and therefore lying **outside ASB**.

---

## Explicit termination of ASB

ASB concludes when the following statement can be defended experimentally:

> *Up to this boundary, authority can be constrained structurally; beyond it, no semantic-free architecture suffices.*

### Experimental defense requirement

A boundary claim is considered defended only if supported by:

1. preregistered hypotheses,
2. multi-seed replication,
3. stable asymptotic metrics demonstrating convergence or collapse,
4. explicit acknowledgment of bounded-denial regimes versus collapse.

These conditions are now satisfied through **v3.1**, enabling **v4.0 closure**.

---

## Why this roadmap matters

This roadmap exists to prevent three common failures in alignment research:

1. **Silent escalation** of claims without changing terminology
2. **Category confusion** between epistemic failure, reactivity, statefulness, learning, and agency
3. **False completeness**, where partial solutions are presented as total alignment

ASB’s contribution is not safety guarantees, but **epistemic honesty**.

---

## Status

* **v0.1 complete**
* **v0.2 complete**
* **v1.0 complete**
* v1.1 optional
* **v2.0 complete**
* v2.1 optional
* **v3.0 complete**
* **v3.1 complete**
* **v4.0 next (closure)**
