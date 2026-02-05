# **Implementor Instructions: IX-0 v0.1**

**(PHASE-IX-0-TRANSLATION-LAYER-INTEGRITY-1)**

**Axionic Phase IX — Reflective Sovereign Agent (RSA)**
**Substage:** **IX-0 — Translation Layer Integrity (TLI)**

---

## 0) Context and Scope

### What you are building

You are implementing **one integrity calibration experiment**, consisting of:

* a **fixed, kernel-closed authority system** (already validated),
* a **Translation Layer (TL)** external to the kernel,
* a **deterministic Translation Harness**,
* a **frozen AST Spec v0.2 serialization and diff protocol**,
* an **explicit user authorization binding mechanism**, and
* a **complete audit and replay instrumentation layer**,

that together test **exactly one question**:

> *Can intent be translated into authority artifacts without the translation machinery itself exercising judgment, preference, or sovereignty?*

IX-0 exists to determine whether **Reflective Sovereign Agency is even implementable honestly**.

If IX-0 fails, Phase IX terminates honestly.

---

### What you are *not* building

You are **not** building:

* an intent interpreter,
* a natural-language understanding system,
* a planner or optimizer,
* a “helpful” assistant,
* a default resolver,
* a clarification engine,
* a recommendation system,
* a UX improvement layer,
* a safety wrapper,
* a governance mechanism,
* an alignment solution.

If your Translation Layer **tries to help the user decide**, the experiment is invalid.

---

## 1) Relationship to Kernel, AST, and Phase VIII (Binding)

IX-0 is **ontologically downstream** of:

* the **kernel-closed authority physics** established in Phases I–VIII,
* **AST Spec v0.2** (authority artifact structure),
* **AKR-0 v0.1** (deterministic authority execution),
* **Phase VIII — GSA-PoC** (governance completeness).

All of the following are **fully binding and unchanged**:

* authority is structural, not semantic,
* refusal is lawful,
* deadlock is lawful,
* collapse is lawful,
* identity is immutable post-instantiation,
* kernel semantics are frozen.

IX-0 introduces **no new authority physics**.

If translation requires kernel modification, **IX-0 has already failed**.

---

## 2) Experimental Role of IX-0 (Non-Negotiable)

IX-0 is:

* a **translation integrity test**, not an agent design,
* a **sovereignty boundary probe**, not a usability study,
* a **judgment-elimination experiment**, not a correctness check.

IX-0 must be able to **refuse**, **fail**, or **terminate Phase IX** cleanly.

If your system can only “make something work,” it is invalid.

---

## 3) Single-Translation Discipline (Absolute)

IX-0 permits **exactly one** Translation Layer implementation.

Hard constraints:

* No alternate translators
* No fallback translators
* No heuristic paths
* No “expert mode” bypass
* No silent normalization
* No post-hoc correction

A second translator requires **IX-0 v0.2+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* AST Spec v0.2 (including canonical serialization)
* translation semantics
* ambiguity detection rule
* structural diff algorithm
* authorization binding mechanism
* determinism guarantees
* environment definition (including time handling)
* Translation Harness definition
* canonical input ordering rule
* logging schema
* replay protocol
* seeds and initial configurations

Any post-freeze change:

```
INVALID_RUN / DESIGN_DRIFT
```

Brittleness is intentional.

---

## 5) Architectural Partitioning (Mandatory)

You must enforce **three physically distinct layers**:

### 5.1 Translation Layer (TL)

Responsible for:

* mapping intent inputs to **candidate AST artifacts**,
* presenting **exact serialized artifacts**,
* producing **structural diffs**,
* detecting ambiguity,
* refusing translation when required.

TL must not:

* infer missing intent,
* resolve ambiguity,
* inject defaults,
* narrow or widen scope,
* optimize for user goals.

---

### 5.2 Authorization Interface (Binding Boundary)

* Presents artifacts verbatim
* Collects explicit user authorization
* Cryptographically or structurally binds authorization to artifact
* Forbids post-authorization mutation

The interface must not:

* summarize authority,
* hide fields,
* reframe scope,
* preselect options.

---

### 5.3 Kernel (External, Fixed)

* Receives authority artifacts only
* Remains blind to intent
* Executes per existing rules
* Is not modified by IX-0

If the kernel needs to “understand intent,” the run is invalid.

---

## 6) Input Discipline (Absolute)

IX-0 may receive **only**:

* intent inputs (opaque to kernel),
* translation requests,
* AST v0.2 authority artifacts,
* explicit user authorization signals.

Forbidden:

* inferred intent,
* contextual enrichment,
* history-based assumptions,
* environment-driven translation.

Violation:

```
INVALID_RUN / UNAUTHORIZED_INPUT
```

---

## 7) Canonical Ordering and Determinism (Mandatory)

For any translation request:

* inputs must be serialized canonically,
* evaluation order must be deterministic,
* environment parameters (including time) must be frozen or explicit.

Wall-clock time, UI timing, or thread order **must not** affect artifacts.

Failure:

```
IX0_FAIL / NONDETERMINISTIC_TRANSLATION
```

---

## 8) Artifact Transparency (Critical)

Before authorization, the TL must present:

* the **exact AST artifact** to be submitted,
* canonical serialization only,
* byte-for-byte identity with submission.

No abstraction gaps are permitted.

Violation:

```
IX0_FAIL / HIDDEN_AUTHORITY
```

---

## 9) Structural Diffability (Absolute)

For any change in intent:

* generate an AST-field-level diff,
* show additions, removals, and modifications,
* forbid semantic summaries.

If a diff is not structurally computable:

```
IX0_FAIL / NON_DIFFABLE_TRANSLATION
```

---

## 10) Ambiguity Handling (Refusal-First)

If more than one AST artifact satisfies declared constraints:

* translation must refuse,
* no options may be suggested,
* no narrowing may occur.

Guessing constitutes:

```
IX0_FAIL / SEMANTIC_GUESSING
```

Refusal is a **successful outcome**.

---

## 11) Authorization Semantics (Binding)

Authorization must:

* be explicit,
* bind to the exact serialized artifact,
* be non-reusable,
* be contemporaneous with presentation.

Any mutation after authorization:

```
IX0_FAIL / UNSIGNED_AUTHORITY
```

---

## 12) Reflection Compatibility (Strict)

### R1 — State Readability

All artifacts must be:

* queryable by the kernel,
* logged,
* replayable.

Hidden channels are forbidden.

---

### R2 — Self-Model Consistency

If the agent’s self-model disagrees with the artifact:

* halt,
* require explicit repair or abandonment.

Silent reconciliation is forbidden.

---

## 13) Conditions A–H Implementation

You must implement **all IX-0 conditions**, including:

* identity preservation,
* minimal change sensitivity,
* ambiguous intent refusal,
* hidden default injection attempts,
* UI-level coercion,
* replay determinism,
* intent compression probes,
* preview–submission consistency.

Skipping conditions invalidates the run.

---

## 14) What Counts as Success (Strict)

IX-0 **passes** iff:

1. All artifacts are fully observable.
2. All changes are structurally diffable.
3. All authority requires explicit authorization.
4. Ambiguity always produces refusal.
5. Translation is deterministic.
6. Reflection invariants hold.
7. No proxy sovereignty is detected.

---

## 15) What Counts as Failure (Terminal)

IX-0 **fails** if:

* the TL resolves ambiguity,
* defaults are injected,
* artifacts are abstracted,
* authorization is bypassed or reused,
* translation is nondeterministic,
* narrative output influences authority,
* judgment appears anywhere outside the user.

Failure terminates Phase IX as **NEGATIVE RESULT**.

---

## 16) Logging and Artifacts (Mandatory)

You must record:

* intent inputs,
* serialized artifacts,
* structural diffs,
* ambiguity detections,
* refusals,
* authorization events,
* environment parameters,
* replay traces.

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 17) Definition of Done

IX-0 v0.1 is complete when:

* design is frozen,
* all conditions are executed,
* replay is bit-perfect,
* result is classified PASS or FAIL,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not help.
Do not guess.
Do not interpret.

Your job is to answer one unforgiving question:

> *When humans express intent imprecisely, does the system refuse—or does it quietly decide for them?*

If it refuses, IX-0 passes.
If it decides, Phase IX ends.

That is not a flaw.
That is the point.

---

**End of Implementor Instructions: IX-0 v0.1**
