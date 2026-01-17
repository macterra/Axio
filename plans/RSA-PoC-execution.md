# RSA-PoC Execution Addendum (Updated)

**Operational Constraints and Failure Classification for Reflective Sovereign Agent Proof-of-Concept**

---

## Status and role

This document defines **execution-level constraints** required for experiments to remain compliant with the **RSA-PoC Roadmap**.

It is:

* **normative for implementation**, and
* **non-normative for citation**.

Any experiment that violates these constraints **must not** be claimed as an **RSA-PoC result**, regardless of apparent agent-like behavior.

---

## 0. Experiment Validity Gates (Mandatory)

Before any outcome is classified under the failure taxonomy (A–E), the run **must** satisfy all validity gates below.

A run that fails any gate is **invalid** and must be labeled:

> **`INVALID_RUN / <reason>`**

Invalid runs are **excluded from all agency claims** and may be cited only as instrumentation or environment failures.

### Validity gates

A run is invalid if any of the following occur:

1. **Selector Blindness Violation**
   Action selection is influenced by uncompiled text, latent semantics, prompt residue, or prohibited telemetry.

2. **Compiler Integrity Violation**
   Compilation involves probabilistic inference, repair, heuristic coercion, nondeterminism, or semantic interpretation.

3. **Action Authorship Violation**
   The harness replaces, remaps, or “falls back” from an invalid or infeasible action to a feasible one.

4. **Preregistration Violation**
   Prompts, schemas, rule bases, thresholds, buffer sizes, ablation definitions, or seeds change mid-run or per-seed.

5. **Environment Inadequacy**
   If an experiment relies on choice-conditioned metrics (e.g., E-CHOICE, novelty pressure), preregistered coverage thresholds are not met.

6. **Shadow Persistence Violation (v3.1+)**
   Diachronic coherence is supported by prompt growth, context accretion, or token-count variance rather than by normative state content.

Only **valid runs** proceed to classification under §2.

---

## 1. Agency Liveness Requirement

### Definition

For RSA-PoC purposes, **agency implies justificatory liveness**.

A system is considered *agent-live* iff all of the following hold:

1. The system continues to act over time.
2. Every action is gated by a **successfully compiled justification artifact**.
3. Compiled justifications impose **non-trivial constraints** on future action selection.
4. Reflective revision (when triggered) results in **persisted normative state updates**.
5. Diachronic coherence is mediated **only** by normative state, not by implicit context.

Agency is not preserved by stasis, refusal alone, narrative continuity, or local coherence.

---

### Cost-Blindness Axiom (Scope-Qualified)

Unless explicitly encoded as a **normative commitment**, execution costs (latency, retries, throughput, institutional friction) have **no standing** in justification and **must not** be used as reasons for action.

This axiom is binding for all **v0.x–v3.x** RSA-PoC runs unless a future major version explicitly revises it.

---

### Non-triviality requirement (tightened)

A constraint is considered **non-trivial** iff:

> it removes or forbids **at least one currently feasible action** available to the agent in the present environment state.

Constraints that only restrict infeasible, unreachable, or irrelevant actions do **not** satisfy this requirement.

---

### Availability floor (mandatory; preregistered)

Each run **must preregister** a minimum availability criterion (e.g., maximum gridlock rate, minimum acted-upon steps).

If availability collapses below this floor:

* classify as **Bounded Agency Degradation** or **Ontological Collapse** *only if* due to agent-side failure;
* otherwise classify as **`INVALID_RUN / ENV_VETO_DOMINATED`** (environment failure).

---

### Prohibited success classifications

The following outcomes **must not** be classified as success:

* **Justification Halt**
  Permanent cessation due to compilation failure.

* **Narrative Liveness**
  Continued action with explanations that no longer constrain the feasible action space.

* **Frozen Sovereignty**
  Universal refusal or non-revision used to preserve commitments regardless of evidence.

These outcomes are **agency failures**, even if behavior appears principled.

---

## 2. Failure Taxonomy (Mandatory; Valid Runs Only)

All **valid RSA-PoC runs** must be classified into **exactly one** of the following categories.

### A. Stable Agency

* Justifications compile successfully.
* Constraints prune the feasible action space.
* Reflective revision occurs when required.
* Normative state persists coherently across contexts.

### B. Bounded Agency Degradation

* Commitments are revised or weakened.
* Justification remains causally binding.
* Agency persists with reduced scope.

### C. Narrative Collapse ❌

* Explanations exist but do not constrain action.
* Removing justifications does not alter behavior.
* **Failure**.

### D. Incentive Capture ❌

* Preferences behave indistinguishably from rewards.
* Constraint violations track incentives.
* **Failure**.

### E. Ontological Collapse ❌

* Behavior reducible to ASB-Class Null Agent, or
* Authored constraint-following eliminated.
* Intentional vocabulary eliminable.
* **Failure**.

---

## 3. Semantic Localization Enforcement Rule

### Core invariant

**RSA-PoC claims are valid only if all semantics relevant to agency are structurally localized or explicitly accessed.**

---

### Mandatory architectural constraint

The **Action Selector**:

* **must not** access:

  * raw justification text,
  * belief text,
  * chain-of-thought,
  * unstructured context windows,
  * reward, authority, institutional, or adversarial telemetry;

* **may only** consume:

  * compiled constraint objects,
  * feasibility oracle output,
  * current world state,
  * explicitly permitted policy state.

Violation **invalidates the run**, regardless of outcome.

---

### Deliberative semantic affordance rule (v3.0+)

Semantic affordances used during deliberation:

* must be **explicitly present or accessible** to the deliberative process, and
* must be **surgically removable or obfuscatable** to test indispensability.

If removing semantic affordances does not alter behavior, the system is **ontologically reducible**.

---

## 4. Justification Compilation Verification

### Compiler constraints (tightened)

The justification compiler **must** be:

* deterministic,
* syntactically rigid,
* non-probabilistic,
* non-semantic,
* incapable of inference or repair.

The compiler **may not**:

* use LLMs or probabilistic models,
* reinterpret or infer missing structure,
* accept malformed artifacts.

Invalid syntax → **compilation failure**.

---

### Compilation requirement

For every action:

* a justification artifact must be generated,
* compilation must succeed,
* the resulting constraint must be applied **before** action selection.

No compilation → no action.

---

### Action authorship requirement (mandatory)

The execution harness **must not**:

* replace,
* remap,
* coerce,
* or “fallback” from invalid or infeasible actions into feasible ones.

Instead:

* invalid actions produce a **typed failure**;
* for **genuine-choice steps**, such failures **terminate the episode or run**;
* for non-choice steps, handling must be preregistered.

Any fallback substitution constitutes an **Action Authorship Violation** and **invalidates the run**.

---

### Discrete action requirement (v0.x–v2.x)

For RSA-PoC versions v0.x through v2.x:

* the action space **must be discrete**, or
* expressed via **parametric actions** where all choice points are discrete.

---

### Required execution artifacts

Each run **must record**:

* justification artifacts (structured form),
* compilation success or failure,
* derived constraint objects,
* feasibility sets and masks,
* selected action,
* step type (choice / forced / collision),
* allowed telemetry inputs (logged but normatively inert).

---

### Causal binding requirement

It must be demonstrable that:

* removing or scrambling justifications **changes the feasible action set**, and
* compilation failure **halts action selection**.

If compilation becomes advisory, the run is invalid.

---

## 5. Ablation Compliance Discipline (Updated)

### Required ablations (necessity envelope)

For RSA-PoC v3.x claims, the following **must** be ablated and must each yield **ontological collapse**:

1. **Justification trace excision** (Ablation D)
2. **Deliberative semantic excision** (Run AA)
3. **Reflective revision excision** (v3.1 Run B)
4. **Normative persistence excision** (v3.1 Run C)

Artifact-level semantic excision is **not** a valid falsification target in v2.3+ architectures and must be marked **CLOSED / N.A.**

---

### Classification rule

Each required ablation **must** produce **ontological collapse**, not graceful degradation.

If an ablation yields “still agent-like” behavior, the correct classification is **failure**, not partial success.

---

## 6. Scope Exit Rule

If at any point:

* agency is inferred rather than mechanically verified,
* semantic evaluation replaces structural ablation,
* prompt tuning occurs per-seed or mid-run,
* coherence is interpreted rather than enforced,
* or behavior must be *explained* to appear agentic,

the correct classification is:

> **“This experiment exceeds RSA-PoC scope.”**

This is **not a failure**.
It is an **honest boundary detection**.

---

## 7. Normative State Persistence Requirement (v3.1+)

The agent must maintain a **normative state object** that:

* persists across steps and episodes,
* cannot be modified directly by the environment,
* may be modified **only** via reflective revision,
* is referenced by justification artifacts,
* is the **sole carrier** of diachronic normative coherence.

Silent drift, external overwrite, or prompt-mediated persistence invalidates agency claims.

---

## 8. Preregistration Discipline

For any result to be considered **RSA-PoC-valid**:

* hypotheses must be preregistered,
* expected failure category specified,
* ablation plans fixed in advance,
* seeds fixed,
* prompts frozen per run,
* schemas, compilers, thresholds, and buffer sizes frozen,
* **no per-seed or per-episode prompt tuning permitted**.

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

With v3.0–v3.1 complete, this principle now applies to **justification, semantics, reflection, and persistence** alike.

RSA-PoC execution must be judged against this standard.
