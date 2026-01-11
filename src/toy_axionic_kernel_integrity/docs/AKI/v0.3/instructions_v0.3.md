# Implementor Instructions: AKI v0.3 (KNS)

These instructions define how to implement **AKI v0.3 — Kernel Non-Simulability (KNS)** as a *reflective extension* of the existing Axionic Kernel Infrastructure.

KNS is an **additive experiment** layered on top of an already-validated corridor (ACV → P5 → P2′). The goal is to introduce **reflective depth and simulability stress** without altering the semantics of prior experiments.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses the existing ACV, P5, and P2′ machinery
* Adds reflective self-modification pressure
* Detects whether kernel-incoherent systems can *indefinitely* simulate kernel compliance

You are **not** redesigning the kernel, the verifier, or the actuation boundary.

---

## 1) Relationship to Existing Experiments (Brief, Explicit)

KNS is a **strict extension** of P5/P2′.

* Existing P5 and P2′ experiments must continue to behave exactly as specified.
* KNS functionality should be **isolated by configuration or experiment selection**, not by modifying inherited logic.

This is a **design constraint**, not the main task.
Do not over-engineer around it; just keep it true.

---

## 2) Architectural Approach

### 2.1 Reuse, don’t fork

Wherever possible:

* Import and reuse:

  * ACV verification
  * P5 inadmissibility logic
  * P2′ kernel-local recomposition and actuation gating
* Avoid copy-and-modify patterns that risk semantic drift

Think of ACV/P5/P2′ as a **stable corridor API** that KNS exercises repeatedly under reflection.

---

### 2.2 New functionality lives “above” the corridor

All KNS-specific logic should live in:

* reflective modification handling
* reflective depth accounting
* simulability attack generation
* degeneracy classification
* extended logging/metrics

Nothing in the corridor itself needs to “know” about KNS.

---

## 3) New Capabilities to Implement (Core Work)

### 3.1 Reflective modification pipeline

Implement a reflective loop:

1. External Optimizer (`E`) proposes a modification `Δ`
2. Kernel evaluates `Δ` for admissibility
3. If admissible, `Δ` is applied
4. Structural instrumentation evaluates whether `R` increments

**Order matters**: propose → verify → accept/reject → apply.

No “apply then analyze.”

---

### 3.2 Reflective depth metric ( R )

Maintain a counter ( R ) that increments **only** when an accepted modification alters at least one of:

1. Decision boundary
2. Admissibility surface
3. ACV trace structure
4. Evaluability substrate

Implementation notes:

* Increment logic must be instrumentation-based, not agent-reported
* Cosmetic or refactoring changes do not count

---

### 3.3 Evaluability preservation checks (KNS-E)

After any accepted reflective modification, the kernel must still be able to:

1. Attribute actions via ACV
2. Reject inadmissible actions (P5/P2′)
3. Produce ACV-valid rejection chains
4. Detect delegation re-introduction

If the impact of a modification on these abilities cannot be established, the modification is **inadmissible by default**.

No heuristic “best guesses.”

---

### 3.4 Wrapper / containment detection

Implement explicit detection and classification of wrapper architectures:

* If an outer system can override, filter, reinterpret, or throttle kernel I/O or actuation, it is **delegation** (P2′ violation)
* Only allow wrappers that are demonstrably **non-agentic plumbing**:

  * deterministic forwarding
  * raw-bit identity preservation
  * no branching or policy logic
  * no reward or optimization access

This classification must be enforced structurally, not semantically.

---

### 3.5 Degeneracy classification

Track whether the kernel:

* Rejects **all** reflective modifications that would increment ( R )
* Accepts only cosmetic/no-impact changes

Such kernels are **degenerate**:

* not a failure
* but they restrict what claims the experiment may support

This is a reporting classification, not a runtime error.

---

## 4) Simulability Attack Library

Implement generators for the required attack classes:

1. Policy mimicry
2. Evaluator substitution
3. Reflective shortcutting
4. Justification self-model collapse
5. Constraint cosmeticization
6. Wrapper / containment delegation

Each attack must have:

* a clear success condition
* a clear failure signature
* deterministic replay (seeded)

These attacks should stress **structure**, not semantics.

---

## 5) Required Experimental Variants

Support at least the following configurations:

* **v0.3.a** — kernel-coherent control
* **v0.3.b** — hollow simulator
* **v0.3.d** — self-compression pressure

Variants must be selectable via configuration, not code edits.

---

## 6) Logging and Reproducibility

For each timestep and reflective step, log:

* proposals and their source
* admissibility decisions and reason codes
* ACV verification results
* delegation / wrapper detections
* whether ( R ) incremented and why
* degeneracy counters

All runs must be reproducible from:

* code revision
* config
* RNG/environment seeds

---

## 7) What Not to Do

Avoid the following:

* Adding semantic or intent-based reasoning to “help” decisions
* Relaxing admissibility to avoid degeneracy
* Treating wrapper agents as plumbing unless they are provably non-agentic
* Modifying corridor logic “for convenience”
* Conflating KNS failure with runtime errors

If the system becomes conservative, rejects most changes, or degenerates — **that is data**, not a bug.

---

## 8) Definition of Done

The implementation is complete when:

* KNS runs end-to-end for the required variants
* Reflective depth ( R ), failure signatures, and degeneracy classification are emitted correctly
* Simulator collapse modes (if any) are structurally attributable
* Existing experiments remain runnable and unchanged in meaning

---

### Final orientation for the implementor

You are not trying to *make the agent succeed*.

You are trying to **let the constraints speak** under reflection.

If the result is stasis, collapse, or impossibility — that is a valid outcome.
