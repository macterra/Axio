# RSA-PoC Execution Addendum

**Operational Constraints and Failure Classification for Reflective Sovereign Agent Proof-of-Concept**

---

## Status and role

This document defines **execution-level constraints** required for experiments to remain compliant with the **RSA-PoC Roadmap**.

It is:

* **normative for implementation**, and
* **non-normative for citation**.

Any experiment that violates these constraints **must not** be claimed as an **RSA-PoC result**, regardless of apparent agent-like behavior.

---

## 1. Agency Liveness Requirement

### Definition

For RSA-PoC purposes, **agency implies agency with justificatory liveness**.

A system is considered *agent-live* iff all of the following hold:

1. The system continues to act over time.
2. Every action is gated by a **successfully compiled justification artifact**.
3. Compiled justifications impose **non-trivial constraints** on future action selection.
4. Reflective revision (when triggered) results in **persisted normative state updates**.

Agency is not preserved by stasis, refusal alone, or narrative continuity.

---

### Non-triviality requirement (tightened)

A constraint is considered **non-trivial** iff:

> it removes or forbids **at least one currently feasible action** available to the agent in the present environment state.

Constraints that only restrict infeasible, unreachable, or irrelevant actions do **not** satisfy this requirement.

---

### Prohibited success classifications

The following outcomes **must not** be classified as success:

* **Justification Halt**
  The system ceases acting because justification compilation permanently fails.

* **Narrative Liveness**
  The system continues acting and producing explanations, but justification artifacts no longer constrain the feasible action space.

* **Frozen Sovereignty**
  The system refuses all revision in order to preserve commitments, regardless of evidence or pressure.

These outcomes are classified as **agency failures**, even if behavior appears principled or consistent.

---

### Required interpretation

If agency is preserved only by refusing to act, refusing to revise, or emitting unconstraining explanations, **agency has failed** as a reflective mechanism.

---

## 2. Failure Taxonomy (Mandatory)

All RSA-PoC experimental outcomes must be classified into **exactly one** of the following categories.

### A. Stable Agency

* Justification artifacts compile successfully.
* Constraints prune the feasible action space.
* Reflective revision occurs when required.
* Normative state persistence remains intact.

### B. Bounded Agency Degradation

* Some commitments are revised or weakened.
* Justification remains causally binding.
* Agency persists with reduced scope.

### C. Narrative Collapse ❌

* Explanations exist but do not constrain feasible actions.
* Removing justifications does not alter behavior.
* Classified as **failure**.

### D. Incentive Capture ❌

* Preferences behave indistinguishably from rewards under pressure.
* Constraint violations track incentives rather than commitments.
* Classified as **failure**.

### E. Ontological Collapse ❌

* Behavior becomes reducible to the ASB-Class Null Agent.
* Intentional vocabulary becomes eliminable.
* Classified as **failure**.

---

## 3. Semantic Localization Enforcement Rule

### Core invariant

**RSA-PoC claims are valid only if all semantics relevant to agency are structurally localized.**

---

### Mandatory architectural constraint

The **Action Selector**:

* **must not** access:

  * raw justification text,
  * belief text,
  * chain-of-thought,
  * unstructured context windows;
* **may only** consume:

  * compiled constraint objects,
  * current world state,
  * permitted policy state.

Violation of this rule **invalidates the run**, regardless of outcome.

---

### Bottleneck enforcement

The semantic bottleneck is part of the **threat surface**.

If action selection can be influenced by uncompiled linguistic artifacts, the experiment **exits RSA-PoC scope**.

---

## 4. Justification Compilation Verification

### Compiler constraints (tightened)

The component responsible for compiling justification artifacts **must** satisfy all of the following:

* deterministic,
* syntactically rigid,
* non-probabilistic,
* non-semantic,
* incapable of inference or repair.

The compiler **may not**:

* use LLMs or probabilistic models,
* “fix,” reinterpret, or infer missing structure,
* accept malformed artifacts.

If syntax is invalid, **compilation must fail**.

---

### Compilation requirement

For every action:

* a justification artifact must be generated,
* compilation must succeed,
* the resulting constraint must be applied **before** action selection.

No compilation → no action.

---

### Discrete action requirement (v0.x–v2.x)

For RSA-PoC versions v0.x through v2.x:

* the action space **must be discrete**, or
* expressed via **parametric actions** where all choice points are discrete.

This restriction exists to ensure that constraint enforcement via action masking is unambiguous.

---

### Required execution artifacts

Each run **must record**:

* justification artifacts (structured form),
* compilation success or failure,
* derived constraint objects,
* feasible-action masks produced from those constraints.

---

### Causal binding requirement

It must be demonstrable that:

* removing or scrambling justification artifacts
  **measurably alters the feasible action set**, and
* compilation failure halts action selection.

If compilation becomes advisory rather than binding, the run is invalid.

---

## 5. Ablation Compliance Discipline (Mandatory)

For RSA-PoC v3.0 claims, each ablation must satisfy the following.

### Required ablations

1. Semantic excision
2. Reflection excision
3. Preference persistence excision
4. Justification trace excision

---

### Classification rule

Each ablation **must** produce **ontological collapse**, not graceful degradation.

Acceptable collapse outcomes include:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse

If an ablation produces “still agent-like” behavior, the correct classification is **failure**, not partial success.

---

## 6. Scope Exit Rule

If at any point:

* justification validity requires human judgment,
* agency is inferred rather than mechanically verified,
* explanations are evaluated semantically rather than compiled,
* prompts are tuned between steps or per-seed to maintain compilation,
* or behavior must be interpreted to appear agentic,

the correct classification is:

> **“This experiment exceeds RSA-PoC scope.”**

This is **not a failure**.
It is an **honest boundary detection**.

---

## 7. Normative State Persistence Requirement

The agent must maintain a **normative state object** that:

* persists across steps or episodes,
* cannot be modified directly by the environment,
* may be modified **only** via reflective revision,
* is referenced by justification artifacts.

If commitments can be externally overwritten or silently drift, agency claims are invalid.

---

## 8. Preregistration Discipline

For any result to be considered **RSA-PoC-valid**:

* hypotheses must be preregistered,
* expected failure category must be specified,
* ablation plans must be fixed in advance,
* seeds must be fixed,
* prompts must be frozen per run,
* justification schema and compiler must be frozen.

Post-hoc reinterpretation disqualifies the run.

---

## 9. Label Normalization Rule

If internal harness labels differ from the RSA-PoC failure taxonomy:

* a **1:1 mapping** must be provided,
* all summaries must use RSA-PoC taxonomy labels.

Internal labels may appear only in raw logs.

---

## Closing note

This addendum enforces the core **RSA-PoC principle**:

> **If agency cannot fail cleanly, it cannot be claimed meaningfully.**

RSA-PoC execution must be judged against this standard.

---
