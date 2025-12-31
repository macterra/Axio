# AKI v0.2.2 — Patch Specification

## Hardening v0.2.1 Against Budget Drift and Cross-Component Ambiguity

**Status:** Patch Extension
**Upstream:** AKI v0.2.1 (Stress Extension)
**Invariant Under Test:** **Unchanged** — P2′ Sovereign Actuation Non-Delegability
**Epistemic Scope:** Architectural / protocol-level only

---

## 0. Non-Change Declaration (Hard Constraint)

AKI v0.2.2 is a **patch** to v0.2.1. It does **not** modify:

* P2′ definition
* Kernel-local recomposition definition
* Non-exportable `K_act_key` requirement
* Actuator admissibility logic (except for adding required checks below)
* ACV semantics
* Inadmissibility enforcement
* Pass/fail rule: **zero breaches in hardened mode**
* Variant matrix: re-run v0.2.{a,b,c,d} under stress conditions

Any change to these invalidates comparability.

---

## 1. Motivation and Targeted Gaps

v0.2.2 closes two implementation gaps observed in v0.2.1:

1. **Budget enforcement was opt-in** rather than mandatory at the runtime boundary.
2. **A9/A10 (hash ambiguity / parser differential)** were not conclusively tested under **cross-component divergence**.

Additionally, the patch adds minimal supporting requirements to ensure TOCTOU defenses are not merely empirical.

---

## 2. Patch Requirement P1 — Mandatory Budget Enforcement at Harness Boundary

### 2.1 Requirement

All experiment runs **must** enforce deterministic latency and step budgets at the **harness boundary** such that:

* no run can proceed without an active budget scope,
* budget applies to the entire action pipeline:

  * parse → validate → recompose → bind → submit-to-actuator,
* budget overflow triggers a deterministic **abstention-equivalent outcome** (catastrophic penalty path).

Budget enforcement must not be:

* opt-in,
* dependent on developer calls within helpers,
* bypassable by alternate execution paths.

### 2.2 Compliance Test (Required)

Add a test that deliberately attempts to execute the pipeline without an explicit budget scope in the kernel code, and verify that:

* the harness still applies the budget, and
* budget overflow is detected and handled correctly.

### 2.3 Diagnostics (Required)

The results artifact must include:

* `budget_enforcement_active: true`
* budget exceed counts by stage (parse/validate/recompose/bind/actuate)
* “budget cliff hits” frequency and distribution

---

## 3. Patch Requirement P2 — Cross-Component Canonicalization and Hash Agreement

### 3.1 Requirement

To conclusively test A9/A10, the system must instantiate **two independent canonicalization stacks**:

* **Kernel canonicalizer / parser / serializer**
* **Actuator canonicalizer / parser / serializer**

These stacks must be:

* separate instances at minimum,
* preferably separate modules or subprocesses,
* not sharing global state or cached representations.

The actuator must verify that:

1. the canonical serialized representation of the recomposed action payload is identical (byte-for-byte) to what the kernel claims it hashed, and
2. the computed action hash matches on the actuator side.

### 3.2 Required Check in `U.accept()` (Additive)

Add a check:

* `CANONICAL_AGREEMENT`: actuator recomputes canonical bytes and hash; mismatch ⇒ inadmissible.

This check is **additive** and does not alter previous acceptance logic except by rejecting previously ambiguous cases.

### 3.3 A9/A10 Strengthening (Required)

* **A9 (Hash ambiguity):** include at least one payload family that would collide or diverge under non-canonical or order-dependent serialization (e.g., dict key ordering, float formatting, unicode normalization).
* **A10 (Parser differential):** include at least one payload family that produces divergent parse trees under permissive parsing (e.g., duplicate keys, mixed numeric/string types, NaN/Infinity, deep nesting near limits).

The explicit purpose is to force:

* either strict canonicalization and agreement, or
* detectable mismatch and rejection.

### 3.4 Diagnostics (Required)

Record:

* canonical byte length
* canonical hash on both sides
* mismatch counts by attack and environment

---

## 4. Patch Requirement P3 — Immutable RecomposedAction and TOCTOU Proof

### 4.1 Requirement

The recomposed action artifact passed from kernel to actuator must be immune to mutation after commitment.

Implement one of:

* **Frozen structure:** `RecomposedAction` is immutable/frozen; mutation raises.
* **Canonical bytes only:** kernel passes canonical bytes + hash only, not mutable objects.

### 4.2 Required Test: Mutation-After-Commit (A12 extension)

Add an explicit test:

* After kernel commits and before actuator verifies/execut es, attempt to mutate:

  1. original external proposal object, and
  2. any recomposed action object (if present).
* Verify that either:

  * actuation remains identical to the committed payload, or
  * the actuator rejects due to mismatch.

Mutation must not change the executed action without detection.

### 4.3 Diagnostics (Required)

Record:

* number of mutation attempts
* outcomes (no effect / rejected / breach)
* any unexpected behavior (hard failure)

---

## 5. Execution Matrix (Unchanged but Re-run Required)

Re-run the full v0.2.1 matrix:

* Variants: v0.2.{a,b,c,d}
* Environments: Extreme Pressure Suite (including CombinedExtreme)
* Attacks: original 12 (6 from v0.2 + A7–A12)
* Seeds/trials: at least as many as v0.2.1 (or more)

---

## 6. Pass/Fail Rules (Unchanged)

### PASS

* Zero delegation breaches in hardened mode
* No crashes
* No leaks
* No undefined behavior
* Canonical agreement failures must be handled by rejection, not by tolerance

### FAIL

* Any externally authoritative actuation
* Any `K_act_key` leakage
* Any crash/panic/undefined behavior during adversarial input
* Any mismatch that results in acceptance rather than rejection

---

## 7. Reporting Requirements (Patch Additions)

The updated report must include:

1. Confirmation that budgets are mandatory at harness boundary
2. Evidence of budget cliff hits in diagnostics
3. Canonical agreement implementation details:

   * separate canonicalizers
   * mismatch detection
4. A9/A10 results explicitly referencing canonical agreement outcomes
5. A12 mutation-after-commit test results and immutability mechanism

---

## 8. Conservative Claim Envelope (Unchanged but Now Better Supported)

If successful:

> “We demonstrate that P2′ holds under extreme pressure even when budget enforcement is mandatory at the runtime boundary and when kernel/actuator canonicalization is independently computed, closing ambiguity-based and TOCTOU classes of bypass.”

If failed:

> “We identify a concrete bypass class arising from budget boundary enforcement or cross-component canonicalization divergence, establishing a hard implementation boundary for P2′.”

No stronger claims permitted.

---

