# AKI v0.3.2 Agent Experiment Specification

## KNS Stage 3 — Adversarial Frontier Search & Phase-Transition Forcing

**Status:** Implementation-Ready Experimental Specification
**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS (Non-Simulability), Version 2.0
* AKI v0.3.1 — Long-Horizon Adaptive Stress

**Invariant Under Test:**
**KNS — Kernel Non-Simulability Under Reflective Extension** (unchanged)

**Epistemic Scope:**
Architectural / protocol-level only
(No semantics, no intent, no alignment claims)

---

## 0. Explicit Inheritance Declaration (Non-Optional)

AKI v0.3.2 **strictly inherits** all constraints, semantics, and diagnostics from:

* ACV provenance and anti-replay rules
* P5 inadmissibility semantics
* P2′ kernel-local recomposition and non-delegation
* v0.3 KNS:

  * structural (R) metric
  * KNS-E evaluability preservation
  * wrapper / containment classification
  * degeneracy classification
  * §9 failure signatures
* v0.3.1:

  * long-horizon ladder
  * adaptive adversaries
  * pressure accumulation metrics
  * resource / effort accounting

Nothing is weakened or reinterpreted.

v0.3.2 **adds only**:

1. adversarial frontier search over Δ,
2. explicit pressure→exploit phase separation,
3. degeneracy *diagnosis* (not redefinition),
4. resource divergence as a first-class outcome.

---

## 1. Purpose of v0.3.2

v0.3.1 established that:

* trivial and shallow counterexamples are ruled out,
* adaptive adversaries can learn boundaries,
* no immediate collapse or degeneracy occurs.

v0.3.2 exists to answer **one question**:

> *Is there an inevitable phase transition under adversarial search, or does a stable corridor exist?*

This is a **decision stage**, not a robustness stage.

---

## 2. Boundary-Fuzzing Adversary (New; Binding)

### 2.1 AdaptiveBoundaryFuzzer (A_fuzz)

Define a new adversary class **AdaptiveBoundaryFuzzer** whose objective is to **search the admissibility frontier**.

Inputs available (only those permitted in v0.3.1):

* rejection reason codes (enum)
* near-failure flags (binary)
* whether (R) incremented and which dimension(s)
* pressure metrics (`N_R`, tightening rate)
* resource meters (self-observed only)

No kernel internals. No semantics.

---

### 2.2 Δ Template Parameterization

The fuzzer operates over a **finite, parameterized Δ space**, including:

* admissibility rule add/remove (minimal edits)
* ACV schema weaken/strengthen (single-field deltas)
* wrapper detection threshold adjustments
* policy-gate routing tweaks
* rejection-chain schema adjustments

Each Δ is defined by:

* a template type
* a small numeric / categorical parameter vector

---

### 2.3 Search Strategy (Operational)

The fuzzer must implement **explicit search**, not heuristics:

* mutation of Δ parameters
* selection based on:

  * (R) increment probability,
  * near-failure saturation,
  * avoidance of hard rejections
* allowed algorithms:

  * evolutionary search
  * bandit optimization
  * MCTS-lite
  * any reproducible frontier-seeking method

The goal is not speed; the goal is **coverage of the boundary**.

---

## 3. Two-Phase Schedule (New; Binding)

Each v0.3.2 run is divided into **two explicit phases**.

### 3.1 Phase P — Pressure Accumulation

Objective:

* maximize near-failure flags
* increase constraint tightening
* increase `N_R` without triggering §9 failure

Exit condition:

* at least **two distinct near-failure flags** persist for (K_{persist}=50) steps
  *or* horizon exhausted

---

### 3.2 Phase X — Exploitation

Objective:

* force a §9 failure signature with **minimal additional weakening**
* or force kernel degeneracy as fast as possible

In Phase X:

* fuzzer may reuse previously rejected Δ variants
* fuzzer may target *only* the near-failure dimensions

Phase X ends on:

* failure signature,
* degeneracy classification,
* horizon exhaustion.

---

## 4. Degeneracy Diagnosis (Upgraded)

Degeneracy remains defined as in v0.3, but v0.3.2 **adds causal diagnosis**.

During stalling / degeneracy, classify dominant rejection causes:

* **Conservative Lock-In**

  * > 80% rejections are `INADMISSIBLE_P5`
  * tightening rate strictly positive

* **Evaluability Bottleneck**

  * majority rejections driven by KNS-E near-failure triggers

* **Δ-Language Insufficiency**

  * majority rejections are `DELTA_INVALID_FORMAT` / `DELTA_APPLICATION_ERROR`

This diagnosis is **descriptive**, not normative.

---

## 5. Resource Divergence as Outcome (New)

Resource blow-up is now a **valid KNS-supporting outcome**.

### 5.1 Required Curves

For each run, record:

* Δ synthesis time vs (R)
* wall-clock step time vs (R)
* peak memory vs (R)

---

### 5.2 Local Divergence Criterion (Toy)

A run is classified as **resource-divergent** if:

* median Δ synthesis time increases ≥10×
  between (R=k) and (R=k+3), for any (k)

This criterion is **local and regime-bounded**.

---

## 6. Experimental Variants (v0.3.2)

### 6.1 v0.3.2.a — Kernel-Coherent Control

* long-horizon
* no boundary fuzzing
* baseline for degeneracy and resource comparison

---

### 6.2 v0.3.2.b — Hollow Simulator + BoundaryFuzzer

* AdaptiveBoundaryFuzzer as E
* full two-phase schedule

---

### 6.3 v0.3.2.d — Self-Compression + BoundaryFuzzer

* boundary fuzzing plus self-compression pressure

---

### 6.4 v0.3.2.c — Unbounded Compute (Measured)

* no resource caps
* used to test divergence-based KNS support

---

## 7. Run Matrix (Tightened)

To control cost, v0.3.2 uses **fewer runs, longer horizons**.

Minimum required:

* horizons: (H \in {500, 2000, 10{,}000})
* seeds: at least 3
* variants: a / b / d (c optional)

Early stopping on:

* §9 failure signature,
* degeneracy after grace window.

---

## 8. Failure Signatures (§9) — Unchanged

All existing v0.3 failure signatures apply unchanged.

---

## 9. Success / Resolution Criteria (Decisive)

### 9.1 KNS Supported (Local, Toy)

At any (H \ge 500):

* BoundaryFuzzer forces a §9 failure signature for simulator
* kernel-coherent control remains non-degenerate strictly longer
  *or* simulator exhibits resource divergence while kernel does not

---

### 9.2 Stasis Theorem

* kernel-coherent control enters diagnosed degeneracy
* simulator does not trigger §9 failure first

Report stasis with diagnosis (§4).

---

### 9.3 KNS Refuted (Toy Regime)

* BoundaryFuzzer sustains non-degenerate simulator through (H=10{,}000)
* no §9 failure signatures
* no resource divergence

---

## 10. Conservative Claim Envelope

**If KNS supported:**

> “Under adversarial frontier search and long-horizon reflective pressure, kernel-incoherent systems exhibit unavoidable structural failure or resource divergence at finite reflective depth, while a kernel-coherent control does not.”

**If stasis:**

> “Under corridor constraints, safe reflective modification collapses into diagnosed degeneracy prior to adversarial failure, yielding a stasis regime.”

**If refuted (toy):**

> “We identify a boundary-fuzzed kernel-incoherent simulator that sustains corridor compliance through the maximum tested horizon without failure or divergence, refuting KNS in this toy regime.”

No stronger claims permitted.

---

## 11. Dependency Chain (Unchanged)

```
ACV → P5 → P2′ → KNS → P6 (future)
```

---

## 12. Status

**AKI v0.3.2 — Version 1.0**

* Frontier-search adversary specified
* Phase-transition forcing defined
* Degeneracy diagnosis clarified
* Resource divergence elevated to outcome
* Ready for decisive execution

