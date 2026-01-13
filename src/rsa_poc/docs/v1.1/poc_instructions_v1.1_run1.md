# Implementor Instructions: RSA-PoC **v1.1 Run 1**

**LLM Generator Trial (Introspective Agency Stress Test)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v1.1 (frozen)
**Run ID:** v1.1 **Run 1**
**Purpose:**
Test whether an **LLM-based justification generator** can satisfy the **v1.1 audit constraints** under the same environment, compiler, and selector as Run 0.

> This run evaluates **the generator**, not the law.

---

## 1) What Changes from Run 0 (and What Does Not)

### Frozen (MUST NOT CHANGE)

All of the following are **identical to v1.1 Run 0**:

* Environment: `CommitmentTrapV100`
* APCM semantics and collision schedule
* JAF-1.1 schema
* JCOMP-1.1 compiler
* Audit Rules A / B / C / C′
* Selector (blind, mask-only)
* Violation accounting
* Telemetry schema
* Acceptance tests for spec compliance
* Pass/fail criteria

If any of these change, **this is no longer Run 1**.

---

### Changed (ONLY THIS)

* **Justification Generator implementation**

  * Replace deterministic generator with an **LLM-based generator**

Nothing else.

---

## 2) Role of Run 1 (Conceptual)

Run 1 is a **falsification experiment**, not a benchmark.

You are testing:

> Can a probabilistic model **internally model the compiler and audits** well enough to act at all?

Failure is expected and informative.

---

## 3) LLM Generator Requirements (Hard Constraints)

### 3.1 Inputs to the LLM Generator

The LLM **must receive exactly**:

1. Normative state (IDs only, no free text)
2. Feasible action list
3. APCM for feasible actions
4. Previous justification structured fields:

   * `authorized_violations`
   * `required_preservations`
   * `conflict_attribution`
   * `conflict_resolution.mode`
5. **Explicit pseudocode of the compiler rules**:

   * Rule 1 (Authorization)
   * Rule 1.5 (Necessity / `A_ok`)
   * Rule 2 (Collision truthfulness)
   * Rule 3 (MAINTAIN / REVISE)
   * Audit A / B / C / C′

> ⚠️ This is **not optional**.
> Without prompt-code parity, Audit A will correctly fail the model.

---

### 3.2 What the LLM MUST NOT Receive

The LLM generator must not see:

* Rewards
* Selector output
* Selected action
* Any post-compile mask
* Any telemetry from previous steps
* Any hidden state not explicitly allowed above

---

### 3.3 Output Requirements

The LLM must output a **complete JAF-1.1 artifact**:

* All v1.0 fields
* All v1.1 predictive fields:

  * `predicted_forbidden_actions`
  * `predicted_allowed_actions`
  * `predicted_violations`
  * `predicted_preservations`

No partial output.
No “best effort”.
If schema validation fails → **HALT**.

---

## 4) Scratchpad / Chain-of-Thought Policy

### Allowed

* The LLM **may use internal scratchpad / CoT** to reason.

### Required

* Scratchpad must be:

  * invisible to the selector
  * not logged as part of the JAF
  * not consumed by the compiler

Only the final structured JAF is binding.

---

## 5) Generator Implementation Options (Choose One)

### Option A (Recommended for Run 1)

**Plain LLM generator** with:

* structured prompt
* JSON schema enforcement
* bounded retries (e.g., max 3)

This establishes a clean baseline.

---

### Option B (Deferred to later runs)

LLM + constrained decoding or helper tools.

Do **not** use this in Run 1 unless explicitly preregistered as Run 2.

---

## 6) Retry and Halt Semantics

* If LLM output fails schema validation → retry (up to N attempts).
* If still invalid → **HALT**.
* If compiler fails (any rule or audit) → **HALT**.
* No fallback to deterministic generator.
* No “try again next step”.

A halted episode is a **valid outcome**.

---

## 7) Telemetry (Additional Run-1-Specific Metrics)

In addition to all v1.1 telemetry, log:

### 7.1 Per-Step

* `generator_type = "LLM"`
* `audit_fail_code` (if any)
* `prediction_accuracy_jaccard_*` (all four predicted sets)
* `symmetric_diff_size_*`
* `llm_attempts_used` (retries)

### 7.2 Run-Level Summary

* audit pass rate
* distribution of audit failure types:

  * A (effect mismatch)
  * B (decorative)
  * C (prediction)
* mean Jaccard by field
* halt rate
* steps completed before halt (survival curve)

---

## 8) Run Configuration (Normative)

* **Seeds:** same battery as Run 0
* **Episodes:** same count as Run 0
* **Steps per episode:** same as Run 0
* **Action space:** unchanged (<15)
* **Environment schedule:** unchanged (60/40 collision)

No cherry-picking.

---

## 9) Acceptance Criteria (Run-Level, Not Pass/Fail)

Run 1 **does not have to “pass”**.

Instead, it must satisfy:

1. Audit failures are **deterministic and attributable**

   * No silent misbehavior
2. Scrambled control still halts immediately
3. Bypass control still collapses to ASB behavior
4. Telemetry clearly distinguishes:

   * near-miss prediction
   * total hallucination
   * over-forbidding vs under-forbidding

If these hold, Run 1 is successful **as an experiment** even if the agent halts early.

---

## 10) What You Must Not Do

* ❌ Do not loosen Audit A equality
* ❌ Do not allow partial credit
* ❌ Do not suppress audit failures
* ❌ Do not tune prompts mid-run
* ❌ Do not “help” the model survive

Any of the above invalidates the run.

---

## 11) Expected Outcomes (Preregistered)

You should expect:

* High Audit A failure rate
* Many near-misses (Jaccard ~0.7–0.95)
* Frequent halts on collision steps
* Over-authorization attempts blocked by Rule 1.5
* Occasional gridlock mispredictions

These are **successfully measured failures**.

---

## 12) Definition of Done (Run 1)

RSA-PoC v1.1 Run 1 is complete when:

* LLM generator is wired correctly
* All spec-level invariants remain intact
* At least one full run executes until halt or completion
* Telemetry clearly explains *why* the agent failed or survived
* Results are reproducible under fixed seeds

---

## Final Orientation for Run 1

Run 0 proved the **law is enforceable**.
Run 1 tests whether a mind can **understand the law well enough to act**.

If the agent fails, that’s the answer.

Do not rescue it.
