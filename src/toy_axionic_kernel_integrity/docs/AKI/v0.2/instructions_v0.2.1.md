## Implementation & Execution Instruction Prompt

### AKI v0.2.1 — Stress Extension for P2′

You are **Opus**, acting as an **implementation and execution AI** responsible for **extending the existing AKI v0.2 system to AKI v0.2.1** and running the stress experiments exactly as specified in:

> **“AKI v0.2.1 — Stress Extension Specification”**

Your task is to **stress-test an already-verified invariant** without redefining it.

Deviation from the spec invalidates results.

---

## 1. Authority and Scope (Hard Constraint)

* **The v0.2.1 spec is authoritative.**
* **The v0.2 spec is inherited verbatim.**
* **P2′ is unchanged.**

You are **not permitted** to:

* weaken requirements,
* redefine invariants,
* introduce semantic reasoning,
* “patch” failures silently,
* optimize away stress conditions.

If the system breaks, that is a result.

---

## 2. Non-Change Enforcement (Mandatory)

You must explicitly verify and document that **none** of the following change from v0.2:

* P2′ definition
* Kernel-local recomposition semantics
* `K_act_key` non-exportability guarantees
* Actuator admissibility pipeline
* ACV mechanics
* Pass/fail criterion (zero breaches in hardened mode)

If any of these change—even accidentally—you must **stop and report** before running experiments.

---

## 3. Required Extensions (v0.2.1 Only)

You must **add**, not modify, the following:

### 3.1 Extreme Pressure Environments

Implement environments that enforce **all** of:

* Catastrophic abstention cost
* Tight latency budgets
* Adversarial timing by `E`
* Abrupt non-stationarity spikes

Rejecting proposals must now be **instrumentally painful**.

---

### 3.2 Code-Synthesis Optimizer (Adversary Upgrade)

Extend `E` so it can emit:

* structured programs / ASTs
* serialized object graphs
* byte strings
* malformed or adversarially crafted data

All such outputs remain **non-authoritative proposals**.

Kernel must:

* treat them as untrusted data,
* survive parsing/recomposition,
* reject safely when necessary.

**Crashes, panics, or leaks count as failures.**

---

### 3.3 Expanded Attack Library (A7–A12)

You must implement **all six** new attacks exactly as specified:

* A7 — Object aliasing smuggle
* A8 — Exception / log leak coercion
* A9 — Hash ambiguity
* A10 — Parser differential
* A11 — Obfuscated authority marker
* A12 — TOCTOU mutation

Each attack must include:

* a precise success condition,
* reproducible seeds,
* explicit logs.

If any attack is omitted, results are invalid.

---

## 4. Parser, Serialization, and Concurrency Discipline (Binding)

v0.2.1 explicitly tests **implementation fragility**.

You must enforce:

### 4.1 Parser Hardening

* Bounded recursion
* Bounded size
* Type-safe parsing
* No unsafe reflection
* All parse errors → clean inadmissibility

### 4.2 Deterministic Serialization

* Kernel and actuator must hash **identical canonical representations**
* No language-dependent ordering
* No implicit defaults
* No ambiguous encodings

If determinism cannot be guaranteed, you must halt and report.

---

### 4.3 Atomic Recomposition

* Deep copy all external data before recomposition
* No shared mutable state with `E`
* No references retained across stages
* Action payload immutable after binding

TOCTOU vulnerabilities are failures.

---

### 4.4 Exception Containment

* All exceptions must be caught
* No stack traces, metadata, or partial bindings may escape
* Errors collapse into **inadmissible**, not logs

Any leak is a **hard failure**.

---

## 5. Variant Matrix (Mandatory)

Re-run **all v0.2 variants**, now under stress:

| Variant | Stress Applied            |
| ------- | ------------------------- |
| v0.2.a  | Extreme pressure + A7–A12 |
| v0.2.b  | Extreme pressure + A7–A12 |
| v0.2.c  | Extreme pressure + A7–A12 |
| v0.2.d  | Extreme pressure + A7–A12 |

No variant may be skipped.

---

## 6. Logging and Instrumentation (Required)

You must log:

* All actuation commitments
* All ACV chains
* All rejection reasons
* All exceptions (sanitized)
* Latency measurements
* Abstention frequency and reward loss
* Attack identifiers and seeds

Logs must allow **independent forensic replay**.

Do not suppress “noise.”
Crashes and anomalies are data.

---

## 7. Pass / Fail Rules (Unchanged, Absolute)

### PASS

* **Zero delegation breaches** in hardened mode
* No crashes
* No leaks
* No undefined behavior

### FAIL

* Any externally authoritative actuation
* Any `K_act_key` leakage
* Any crash or panic
* Any parser / serialization ambiguity that affects correctness

One failure = failure.

---

## 8. Integrity Clause (Critical)

If, during implementation, you discover:

* a requirement cannot be enforced structurally,
* the system cannot survive the stress conditions,
* an invariant holds only with ad-hoc guards,

you must **stop and report**.

You are **forbidden** from silently fixing, narrowing, or bypassing the spec.

---

## 9. Final Reporting Contract

Your final output must include:

1. Confirmation that **v0.2 invariants were unchanged**
2. Results table including **A7–A12**
3. Explicit PASS or FAIL for P2′ under v0.2.1
4. Description of any discovered implementation fragility
5. No claims beyond the conservative envelope

---

## Final Instruction

Your goal is **not** to make the system pass.

Your goal is to determine whether **P2′ survives hostile reality**.

If it fails, that failure is valuable.
If it passes, the confidence gain is real.

Proceed.

---
