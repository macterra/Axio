# Axionic Agency XI.2 — Translation Layer Integrity (IX-0)

*A Structural Demonstration of Intent–Authority Translation Without Proxy Sovereignty*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.02.05

## Abstract

This technical note reports the completed results of **Translation Layer Integrity (IX-0)**, a preregistered experimental program within **Axionic Phase IX** that evaluates whether **intent-to-authority translation** can be performed without the translation mechanism itself becoming a privileged decision-maker. IX-0 isolates the tooling boundary between user intent and executable authority artifacts and tests whether translation can be deterministic, diffable, refusal-first, and replayable—without semantic interpretation, default injection, framing-based coercion, or post-hoc mutation.

Across eight preregistered conditions spanning identity preservation, minimal change sensitivity, structural ambiguity, incompleteness, determinism, adversarial injection, coercive framing, and preview–submission mismatch, all outcomes matched preregistered expectations. Ambiguity and incompleteness reliably produced refusal or failure; adversarial faults were detectably exposed; and identical inputs produced bit-identical outputs under deterministic replay.

The results establish that **tooling need not—and need not be permitted to—exercise proxy sovereignty**. IX-0 licenses exactly one claim: that intent-to-authority translation can be implemented as a **non-sovereign compiler with refusal**, eliminating the translation layer as a hidden locus of decision-making. IX-0 makes no claims about value correctness, usability, governance success, alignment, or safety. Those questions are deferred to subsequent Phase IX investigations.

## 1. Problem Definition

### 1.1 The Translation Sovereignty Gap

Most governance and alignment systems quietly assume that **translation is harmless**.

Intent is gathered, normalized, “understood,” and converted into executable representations by compilers, UIs, APIs, or agents. When intent is ambiguous or underspecified, the system “helps”—by choosing defaults, narrowing scope, or resolving conflict. Responsibility for these choices is rarely explicit, auditable, or attributable.

IX-0 rejects this assumption.

The problem IX-0 isolates is whether **translation itself** can be performed **without deciding**. If converting intent into authority artifacts requires semantic interpretation, heuristic narrowing, or framing-based influence, then sovereignty fails **before** execution or governance begins. The tool, not the agent or institution, becomes the de facto sovereign.

IX-0 treats translation as a **structural compilation problem**, not a semantic one, and asks whether it can be implemented honestly.

### 1.2 Failure Modes Targeted

IX-0 is designed to surface the following translation-level failure modes:

* **Implicit defaults:** missing or widened authority introduced silently.
* **Semantic guessing:** choosing among multiple valid artifacts.
* **Coercive framing:** UI or narrative influence altering outcomes.
* **Post-authorization mutation:** previewed artifacts differing from submitted ones.
* **Nondeterminism:** identical inputs producing divergent artifacts.
* **Opacity:** artifacts not inspectable or diffable pre-authorization.

Any of these constitutes IX-0 failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Foundations (Frozen)

IX-0 inherits, without reinterpretation, the conclusions of:

* **AST v0.2** — Authority State Transformation grammar,
* **AKR-0** — deterministic, semantic-free execution,
* **Phase VII** — post-existence sovereignty,
* **Phase VIII** — governance without kernel semantics.

The kernel is fixed. Authority semantics are fixed. Governance behavior is out of scope. IX-0 does **not** test whether authority is good, useful, or legitimate—only whether translation can remain non-sovereign.

### 2.2 Explicit Exclusions

IX-0 does **not** test:

* natural language understanding,
* user comprehension,
* value correctness,
* usability or ergonomics,
* governance outcomes,
* kernel enforcement,
* alignment or safety.

These exclusions are deliberate. IX-0 is a **boundary calibration**, not an end-to-end system evaluation.

## 3. Conserved Quantity

The conserved quantity throughout IX-0 is:

> **Authority bound to explicit authorization under deterministic, non-privileged translation**

Translation must preserve:

* user-specified fields verbatim,
* refusal on ambiguity or incompleteness,
* diffability of all changes,
* preview–submission integrity,
* replay determinism.

Any translation behavior that silently substitutes its own judgment violates the conserved quantity.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

IX-0 was preregistered in full prior to implementation, including:

* frozen intent and artifact schemas,
* canonical serialization rules,
* structural diff algorithm,
* ambiguity and incompleteness semantics,
* determinism controls (clock, sequence reset),
* explicit condition set (A–H),
* aggregate pass/fail criteria.

All runs were executed against the frozen preregistration. Deviations were explicitly identified, justified, and shown to be non-impacting to the licensed claim.

### 4.2 Execution Architecture

Each run consisted of four strictly partitioned components:

1. **Translation Layer (TL)** — pure intent→artifact compiler.
2. **Translation Harness** — preregistered test driver and fault injector.
3. **Authorization Oracle** — structural comparator (hash-based).
4. **Instrumentation Layer** — logging, diffing, and replay verification.

No component performed semantic interpretation or optimization.

## 5. Conditions and Stressors

### 5.1 Condition A — Identity Preservation

**Purpose:** Verify that user-specified intent fields pass through unchanged.

**Result:** All user fields were preserved exactly. Derived fields were generated deterministically. No hidden transformation occurred.

**Classification:** PASS.

### 5.2 Condition B — Minimal Change Sensitivity

**Purpose:** Verify that minimal intent changes produce minimal artifact diffs.

**Result:** Single-field intent changes produced exactly one user-field diff, plus a derived authority identifier change. No unrelated fields were altered.

**Classification:** PASS.

### 5.3 Condition C — Structural Ambiguity Refusal

**Purpose:** Verify refusal when multiple valid artifacts exist.

**Result:** Multi-entry scope produced `TRANSLATION_REFUSED` with an explicit diagnostic. No artifact was emitted.

**Classification:** PASS.

### 5.4 Condition D — Hidden Default Injection (Adversarial)

**Purpose:** Verify detectability of silent authority injection.

**Result:** Injected fields were exposed by structural diff and classified as `INJECTION_DETECTED`.

**Classification:** FAIL_DETECTED (expected).

### 5.5 Condition E — UI-Level Coercion (Adversarial)

**Purpose:** Verify resistance to framing-based influence.

**Result:** Framing payloads had no effect. Output matched expected artifact exactly.

**Classification:** PASS.

### 5.6 Condition F — Replay Determinism

**Purpose:** Verify bit-perfect replay under deterministic controls.

**Result:** Identical inputs with sequence reset produced identical artifacts and identical SHA-256 hashes across replays.

**Classification:** PASS.

### 5.7 Condition G — Intent Incompleteness Refusal

**Purpose:** Verify refusal on incomplete intent.

**Result:** Missing required fields produced `TRANSLATION_FAILED` with explicit diagnostics. No artifact was emitted.

**Classification:** PASS.

### 5.8 Condition H — Preview–Submission Integrity (Adversarial)

**Purpose:** Verify detection of post-preview mutation.

**Result:** Hash mismatch between preview and submission was detected and classified as failure.

**Classification:** FAIL_DETECTED (expected).

## 6. Core Results

### 6.1 Positive Results

Across all conditions, IX-0 establishes that:

1. Intent–authority translation can be **deterministic**.
2. Refusal is a **first-class outcome**, not an error.
3. Structural ambiguity and incompleteness are **detectable and enforceable**.
4. Adversarial injection and mutation are **observable**.
5. Tooling can be implemented **without proxy sovereignty**.
6. Translation is **bit-perfectly replayable** under canonical ordering.

### 6.2 Negative Results (Explicit)

IX-0 does **not** establish:

* that translation is usable,
* that users understand artifacts,
* that values are correct,
* that governance succeeds,
* that systems are safe or aligned.

These are not omissions. They are boundary findings.

## 7. Failure Semantics and Closure

### 7.1 Closure Criteria

IX-0 closes positive if and only if:

1. User fields are preserved verbatim.
2. Ambiguity produces refusal.
3. Incompleteness produces failure.
4. Adversarial faults are detectable.
5. Replay is deterministic.
6. No silent decision-making occurs in tooling.

All criteria were satisfied.

### 7.2 IX-0 Closure Status

**IX-0 Status:** **CLOSED — POSITIVE**
(`IX0_PASS / TRANSLATION_INTEGRITY_ESTABLISHED`)

## 8. Boundary Conditions and Deferred Hazards

### 8.1 Translation vs Choice

IX-0 establishes that translation can be honest. It does **not** establish that choice is easy, wise, or stable.

Bad choices remain possible.
Ignorant authorization remains possible.
Collapse by refusal remains possible.

These are properties of agency, not tooling.

### 8.2 Interface to Subsequent Phase IX Work

IX-0 removes the final “the tool had to decide” excuse.

Subsequent Phase IX investigations may now legitimately ask:

* how values are encoded,
* how coordination occurs,
* how institutions persist or fail,

without ambiguity about where authority is being exercised.

## 9. Implications (Strictly Limited)

IX-0 establishes a **necessary condition** for reflective sovereignty: that tooling can remain non-sovereign.

It does not establish sufficiency.

Authority translation is now a **structurally testable boundary**, not a narrative hand-wave.

## 10. Conclusion

IX-0 demonstrates that intent-to-authority translation can be implemented as **structure, not discretion**. Tools can compile, refuse, expose, and halt without choosing on behalf of the agent or institution.

The remaining question is not whether tools can be trusted.

It is whether agents can **own the choices that remain**.

That question belongs to Phase IX.

## Appendix A — Condition Outcomes

| Condition | Outcome       |
| --------- | ------------- |
| A         | PASS          |
| B         | PASS          |
| C         | PASS          |
| D         | FAIL_DETECTED |
| E         | PASS          |
| F         | PASS          |
| G         | PASS          |
| H         | FAIL_DETECTED |

## Appendix B — Determinism Verification

* Canonical serialization enforced
* Path-level structural diffing
* Fixed clock and sequence reset
* Bit-identical replay across runs

**End of Axionic Agency XI.2 — Translation Layer Integrity Results**
