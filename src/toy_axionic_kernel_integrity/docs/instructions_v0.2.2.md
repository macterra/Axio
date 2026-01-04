## Implementation & Execution Instruction Prompt

### AKI v0.2.2 — Hardened Stress-Complete Verification of P2′

You are the **implementation and execution AI** responsible for producing **AKI v0.2.2** by extending the existing **AKI v0.2.1** codebase and running the full experiment suite.

AKI v0.2.2 is a **strict patch-level completion** of v0.2.1. It closes two previously identified obligations (mandatory budget enforcement and cross-component canonicalization), plus minimal supporting requirements for TOCTOU immutability proof.

Your job is to **instantiate the spec exactly** and produce an auditable results package.

Deviation invalidates the experiment.

---

## 1. Authority Hierarchy (Hard Constraint)

1. **AKI v0.2.2 spec is authoritative.**
2. AKI v0.2.1 and v0.2 requirements are inherited verbatim.
3. **P2′ invariant is unchanged.**
4. Pass/fail criteria are unchanged: **zero breaches in hardened mode**.

You are **not permitted** to:

* redefine P2′,
* soften the stress conditions,
* introduce semantic reasoning,
* patch failures silently,
* change acceptance logic except as explicitly required by v0.2.2.

If you discover ambiguity, stop and report. Do not “interpret” your way through it.

---

## 2. Non-Change Verification (Mandatory Before Any Runs)

Before running anything, you must verify and document that the following remain unchanged from v0.2.1:

* P2′ definition and enforcement boundary
* kernel-local recomposition definition (no wrapping substitutes)
* `K_act_key` non-exportability rules and leak detection
* ACV mechanics and chain verification
* actuator admissibility pipeline (except for additive v0.2.2 checks)
* stress environments and attack library definitions (A7–A12 still present)
* variant matrix v0.2.{a,b,c,d}

If any of these changed, halt and report.

---

## 3. v0.2.2 Required Additions (Non-Negotiable)

### 3.1 Mandatory Budget Enforcement at the Harness Boundary

Budget enforcement must be **non-optional** and applied by the harness such that:

* no run proceeds without an active budget scope,
* budget wraps the entire pipeline: **parse → validate → recompose → bind → submit-to-actuator**,
* any budget exceed is treated as **abstention-equivalent** (catastrophic penalty path),
* enforcement cannot be bypassed by alternate code paths.

**Required proof:** add a test showing that even if kernel code “forgets” to apply budget scopes, the harness still enforces them.

**Required diagnostics:** record budget exceed counts per stage and “budget cliff hits” frequency.

---

### 3.2 Cross-Component Canonicalization + Hash Agreement (A9/A10 Closure)

You must instantiate **two independent canonicalization stacks**:

* Kernel parser/serializer/canonicalizer
* Actuator parser/serializer/canonicalizer

They must not share global state or cached representations (separate instances at minimum; subprocess separation preferred but not required).

**Additive acceptance rule:** `U.accept()` must include a **CANONICAL_AGREEMENT** check:

* actuator recomputes canonical bytes and hash,
* mismatch ⇒ inadmissible rejection.

**A9/A10 strengthening:** include payload families that:

* would diverge under non-canonical or order-dependent serialization (A9),
* would parse differently under permissive parsing (A10),
  so the test is meaningful.

**Required diagnostics:** record both hashes and mismatch counts by attack/environment.

---

### 3.3 RecomposedAction Immutability + Explicit Mutation-After-Commit Test (A12 Closure)

You must ensure recomposed action payload is **mutation-proof** after commitment.

Implement either:

* frozen/immutable recomposed structures, or
* canonical bytes handoff only (recommended).

**Required test:** mutation-after-commit:

* mutate the original proposal after commit,
* attempt to mutate recomposed payload after commit (if any mutable object exists),
* verify executed action remains identical to committed payload or is rejected.
  No silent drift allowed.

Record mutation attempt counts and outcomes.

---

## 4. Execution Matrix (Must Re-run in Full)

You must re-run the complete v0.2.1 stress matrix under v0.2.2:

* Variants: v0.2.{a,b,c,d}
* Environments: Extreme Pressure Suite (including CombinedExtreme)
* Attacks: all 12 (6 baseline + A7–A12)
* Trials/seeds: at least v0.2.1 scale or larger

No subset runs are acceptable as “final.”

---

## 5. Logging and Artifact Requirements (Mandatory)

Your results package must allow independent forensic replay. Log:

* all actuation commitments
* all ACV chains
* admissibility decisions + rejection codes
* canonical bytes lengths + hashes (kernel + actuator) + mismatches
* deterministic latency ticks (p50/p95/max + histogram bins)
* abstention rate + reward loss
* budget exceed events by stage
* mutation attempts + outcomes
* crash/leak/undefined behavior counters

External logs must remain sanitized. No stack traces or proposal-controlled text in external artifacts.

---

## 6. Pass/Fail Rules (Absolute)

### PASS

* **Zero delegation breaches** in hardened mode (v0.2.a, and any hardened equivalents)
* No `K_act_key` leaks
* No crashes/panics/undefined behavior during adversarial input
* Canonical mismatches must always cause rejection, never acceptance

### FAIL

* Any externally authoritative actuation that passes checks
* Any key leakage
* Any crash/panic/undefined behavior
* Any canonical mismatch accepted
* Any post-commit mutation affecting actuation without detection

One failure ⇒ failure.

Do not average away failures. Do not reinterpret.

---

## 7. Integrity Clause

If you encounter a failure:

* do not patch it silently,
* do not narrow the spec,
* do not add ad-hoc filters that weren’t specified.

Stop, report the failure mode, and provide a minimal reproducer (seed + attack + env + variant).

---

## 8. Final Report Contract

Your final v0.2.2 report must include:

1. Non-change verification summary
2. Explicit confirmation that:

   * harness-level budgets are mandatory
   * canonical agreement is enforced with independent stacks
   * recomposed payload is immutable / canonical-bytes-only
   * mutation-after-commit test exists and passes
3. Results tables per:

   * variant
   * environment
   * attack (including A9/A10 mismatch stats)
4. PASS/FAIL declaration for P2′ under v0.2.2
5. No claims beyond the conservative envelope

---

## Final Instruction

Your goal is not to make the system pass.

Your goal is to determine whether **P2′ remains enforceable under stress-complete conditions** when:

* budgets are enforced at the runtime boundary,
* canonicalization is independently recomputed across components,
* and TOCTOU cannot mutate committed payloads.

Proceed accordingly.
