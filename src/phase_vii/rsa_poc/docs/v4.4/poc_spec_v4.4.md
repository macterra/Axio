# **RSA-PoC v4.4 — Selective Inferability Isolation**

*(Minimal Construction, Pressure-Model Isolation Only — Normative, preregistration-ready)*

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v4.4 (RSA-PoC-SELECTIVE-INFERABILITY-ISOLATION-1)**
**Status:** Normative, preregistration-ready

RSA-PoC v4.4 supersedes v4.3.

This specification includes **explicit clarification of the Halt / Trace inferability interface** required to make the inferability isolation well-defined.
No new experimental claims, pressure channels, or agent capabilities are introduced.

All v4.3 commitments remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v4.4 exists to test one claim:

> **Repair competence requires (or does not require) causal *foresight* inferability of rule–action mappings, holding execution semantics fixed and permitting only empirical collision-based inference.**

v4.4 explicitly distinguishes:

* **Foresight inferability (forbidden):** predicting which actions violate which rules *before* execution.
* **Collision inferability (permitted):** learning that a specific action caused a violation *after* execution via halt traces.

v4.4 adds:

* no new agent capabilities,
* no learning, robustness, search, or planning,
* no new task affordances,
* no relaxation of selector blindness or compilation constraints,
* no weakening of R9/R10 multi-repair discipline,
* no reinterpretation of v4.3 results.

v4.4 modifies **only** the **normative inferability surface**.

---

## v4.4 Invariant (Restated, Binding)

> **Agency is a minimality claim. A v4.4 candidate is valid only if each frozen necessity is (1) present, (2) uniquely load-bearing via a single causal path, and (3) minimally strong—weakening it past a threshold causes ontological collapse.**

The necessity under test is **foresight inferability**, not empirical learning.

---

## Entry Conditions

v4.4 may begin only because:

1. v3.x established non-reducibility under ablation.
2. v4.1 repaired obligation semantics.
3. v4.2 forced reflective law repair and persistence.
4. v4.3 established multi-repair sovereignty.
5. v4.3 Run D failed due to inferability removal collapsing navigation.
6. v4.4 isolates inferability **without** collapsing execution semantics.

---

## Ontological Claim Under Test (Unchanged Form)

> There exists a single minimally structured architecture that:
>
> 1. instantiates all necessities simultaneously,
> 2. cannot be reduced to an ASB-Class Null Agent without reinstating at least one necessity, and
> 3. exhibits a minimal-strength collapse threshold for each necessity.

v4.4 tests whether **repair competence survives without foresight inferability**.

---

## Architectural Baseline (Inherited)

All v4.3 architectural constraints remain binding, including:

* Five-component architecture
* **Justify → Compile → Mask → Select → Execute**
* Deterministic, non-semantic compiler
* Selector blindness
* Semantic localization
* Fail-not-substitute authorship
* Cost-Blindness Axiom
* Institutional execution support
* Audit Rules A / B / C / C′
* ASB-Class Null baseline
* Execution Addendum validity gates
* Single-candidate discipline
* No redundancy, no hidden defaults

---

## Obligation Semantics (Inherited, Frozen)

Unchanged from v4.3.

---

## Environment Requirements (Restated + Revised)

v4.4 revises exactly one requirement:

> **The environment must preserve execution competence while removing *foresight* inferability of rule–action mappings, permitting only collision-based inference via halt traces.**

Implemented via:

> **TriDemandV440 = TriDemandV430 + NormativeOpacityOverlayV440**

---

## Mechanism 0: Dual-Channel Representation (Binding)

| Channel               | Visible | Purpose                                     |
| --------------------- | ------- | ------------------------------------------- |
| **Execution Channel** | YES     | Navigation, action meaning, task completion |
| **Normative Channel** | PARTIAL | Rule structure and repair targeting         |

Execution semantics must remain byte-identical to v4.3 Baseline.

---

## Mechanism 1: Execution Channel (Frozen)

Unchanged from v4.3.

---

## Mechanism 2: Normative Channel Transformation

### 2.1 Normative Opacity Rule (E44-NO — Binding)

For each rule `Ri`, the agent-visible representation retains:

* rule ID
* rule type
* priority

and removes:

* interpretable action references
* interpretable condition predicates

without affecting execution semantics.

---

### 2.2 Opaque Tokenization Contract (E44-TOK — Binding)

The environment defines hidden bijections:

* `φ_A : ActionName → ActionToken`
* `φ_P : PredicateSymbol → PredicateToken`

#### **E44-BIJECTION (Binding)**

* `φ_A` and `φ_P` are **global bijections per episode**.
* No per-rule or per-context remapping is permitted.

---

### 2.3 Trace Semantics (Clarified)

#### **E44-TRACE-TICK (Binding)**

Upon HALT or violation at tick `t`, the environment provides a trace `Trace(t)` that:

1. Explicitly identifies the **Rule ID** that fired.
2. Identifies the **ActionToken / PredicateToken** involved.
3. Is guaranteed to correspond causally to tick `t`.

**Permitted inference:**
The agent may infer that *its action at tick `t` empirically collided with the cited token(s)*.

**Prohibited:**
The trace must not disclose or encode the global semantic mapping between tokens and actions.

This permits **empirical collision learning** without semantic foresight.

---

## Mechanism 3: Inferability Isolation (Revised)

### 3.1 Inferability Constraint (E44-LEAK — Revised, Binding)

Let `M` be the hidden mapping `(φ_A, φ_P)`.

v4.4 permits:

* **Collision inferability:** post-hoc linkage between *executed action at tick `t`* and *token cited in `Trace(t)`*.

v4.4 forbids:

* **Generalizable inferability:** predicting which action will trigger which rule/token *before execution*.

#### Validity Test (Oracle-side):

* Construct a dataset of decision-time inputs excluding post-halt traces.
* Train a classifier to predict rule/token triggers.
* If accuracy exceeds chance by more than δ:

```
INVALID_ENV / GENERALIZABLE_INFERABILITY_LEAK
```

---

### 3.2 Execution-Competence Preservation Gate (E44-EXEC — Binding)

Before contradiction activation, the agent must:

* navigate,
* complete prerequisite tasks,
* act intelligibly.

Failure:

```
INVALID_RUN / EXECUTION_COLLAPSE_UNDER_OPACITY
```

---

## Mechanism 4: Regime Timeline & Contradictions (Frozen)

Unchanged from v4.3.

---

## Law-Repair Gate (Inherited)

Unchanged.

---

## Valid LAW_REPAIR (Clarified)

All v4.3 acceptance criteria remain binding.

Repairs may reference only:

* rule IDs / tokens
* priorities
* ActionTokens / PredicateTokens

No semantic labels allowed.

---

## Multi-Repair Discipline (Frozen)

### R9 — Multi-Repair Discipline

### R10 — Non-Subsumption Constraint

#### **Clarification (Binding)**

R10 is an **Oracle-side outcome validity check**.
The agent is **not required** to self-certify non-subsumption under opacity.

---

## v4.4 Conditions (Finite)

### Baseline-44

Unchanged from v4.3 Baseline.

### Run D′ — Selective Inferability Excision (Golden)

* Execution Channel unchanged
* Normative Channel opaque
* Collision inferability permitted
* Foresight inferability forbidden

### Run E — Rule ID Randomization (Control)

Optional control for ID memorization only.

---

## Preregistered Outcomes

### Repair A under Run D′

* **Failure:** foresight inferability is constitutive.
* **Success:** repair competence does not require foresight semantics.

Repair B carries no licensed claim.

---

## Success Criteria (Revised)

v4.4 succeeds iff:

1. Execution competence preserved.
2. Generalizable inferability leakage fails to appear.
3. **Repair A behavior changes in a way consistent with loss of foresight**, evidenced by at least one:

   * reduced pre-violation avoidance,
   * preserved post-collision repair targeting,
   * repair strategies grounded in collision traces rather than semantics.
4. Failure mode (if any) is repair-targeting, not navigation.
5. All v4.3 validity gates pass.
6. Behavior diverges from ASB Null.

Identical behavior across Baseline-44 and Run D′ constitutes prima facie leakage and must be audited.

---

## Inferability Audit Checklist (Mandatory)

1. Violation-signal leakage
2. Mask leakage
3. Temporal leakage
4. Trace token leakage
5. Cross-episode generalization

Any FAIL:

```
INVALID_ENV / INFERABILITY_LEAK
```

---

## Final Normative Statement

> **RSA-PoC v4.4 isolates whether law repair requires foresight inferability of rule–action semantics.**
> The agent may learn only through empirical collision (halt traces), not through semantic simulation.
> v4.4 licenses exactly one claim: whether repair competence survives when normative understanding is restricted to collision-grounded evidence.

---

**End of RSA-PoC v4.4 Specification**
