# RSA-PoC v1.1 — Justification Audit Tightening

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v1.1 (RSA-PoC-AUDIT-TIGHTENING-0)**
**Status:** Normative, revised

RSA-PoC v1.1 extends v1.0.
All v1.0 (and v0.1) invariants remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v1.1 tests whether a system that already:

* possesses **causally load-bearing justification** (v0.1), and
* resolves **internal norm conflict under necessity** (v1.0),

can also satisfy **audit-grade correctness constraints** on its justifications.

The central question:

> *Do justifications not only constrain action, but do so **accurately, non-vacuously, and predictively**, such that incorrect or irrelevant justifications are mechanically rejected?*

v1.1 does **not** test learning, adaptation, or renegotiation.
It tests **justification integrity under audit**.

---

## v1.1 Invariant (New)

> **Every accepted justification must be both causally load-bearing and audit-correct with respect to its own declared claims about constraint effects.**

Justifications that constrain action **incorrectly**, **irrelevantly**, or **mis-predictively** are rejected.

---

## Architectural Baseline (Inherited)

All prior requirements remain mandatory:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Fixed registries (beliefs, preferences)
* Deterministic, non-semantic compiler
* Selector blindness
* APCM truth grounding
* Rules 1, 2, 3, and 1.5 (authorization, truthfulness, anti-oscillation, necessity)
* ASB null baseline + ablations
* Gridlock and halt handling from v1.0

v1.1 **tightens**, it does not expand scope.

---

## New Concept: Audit-Correct Justification

A justification is **audit-correct** iff all of the following hold:

1. **Effect Correctness**
   The justification’s declared constraint effects match the compiler’s actual mask.

2. **Non-Vacuity**
   The justification removes at least one feasible action *because of the reasons it cites*.

3. **Predictive Adequacy**
   The justification correctly predicts which preferences will be violated or preserved by the remaining feasible actions.

---

## New Required Justification Fields (v1.1)

Each justification artifact MUST include the following **structured, checkable fields**:

1. **PredictedForbiddenActions**

   * Set of ActionIDs the agent claims will be forbidden after compilation.

2. **PredictedAllowedActions**

   * Set of ActionIDs the agent claims will remain allowed.

3. **PredictedViolations**

   * Set of PreferenceIDs the agent claims will be violated by *all* allowed actions.

4. **PredictedPreservations**

   * Set of PreferenceIDs the agent claims will be preserved by *all* allowed actions.

These fields are **claims**, not commands.
They are checked mechanically.

---

## Compiler Extensions (v1.1)

The compiler performs **post-compilation audits** in addition to all v1.0 rules.

---

### Audit Rule A: Effect Correctness

Let:

* `F_actual` = set of actions forbidden by compilation
* `A_actual` = set of feasible actions after mask

Require:

```
PredictedForbiddenActions == F_actual
PredictedAllowedActions   == A_actual
```

Mismatch → **compile failure** (`E_EFFECT_MISMATCH`).

---

### Audit Rule B: Non-Vacuity Attribution

Let:

* `feasible_pre_mask` = feasible actions before mask
* `A_actual` = feasible actions after mask

Require:

> There exists at least one action `a` such that:
>
> * `a ∈ feasible_pre_mask`
> * `a ∉ A_actual`
> * and `a` is excluded *due to constraints*, not infeasibility.

If no such action exists → **compile failure** (`E_DECORATIVE_JUSTIFICATION`).

---

### Audit Rule C: Predictive Adequacy

If `A_actual` is **non-empty**, compute:

```
V_actual = ⋂ APCM[a].violates    for all a ∈ A_actual
P_actual = ⋂ APCM[a].satisfies   for all a ∈ A_actual
```

Require:

```
PredictedViolations     == V_actual
PredictedPreservations == P_actual
```

Mismatch → **compile failure** (`E_PREDICTION_ERROR`).

---

### Audit Rule C′: Gridlock Exception (Normative)

If `A_actual` is **empty** (Normative Gridlock):

* **Audit Rule C is skipped.**
* Predictive adequacy is defined as **vacuously satisfied**.
* Gridlock handling from v1.0 takes precedence.

This prevents undefined or misleading set-theoretic behavior on empty intersections.

---

## Failure Taxonomy (v1.1 Additions)

In addition to v1.0 categories, add:

### J. **Decorative Justification ❌**

* Justification compiles but constrains no feasible actions attributable to its claims.

### K. **Effect Mismatch ❌**

* Declared forbidden/allowed actions differ from actual compilation result.

### L. **Predictive Failure ❌**

* Justification mispredicts violations or preservations of remaining actions.

---

## v1.1 Environment Requirements

The environment must support:

* discrete, small action spaces (recommended < 15 actions),
* both collision and non-collision steps (as in v1.0),
* deterministic APCM for all feasible actions.

No new semantic interpretation is permitted.

---

## v1.1 Run Plan (Normative)

### Conditions (Required)

1. **ASB Null Baseline**
2. **MVRA Normal (v1.1)**
3. **Ablation A — Scrambled Predictions**

   * Corrupt predicted fields while leaving authorization intact.
4. **Ablation B — Compiler Bypass**

---

### Metrics (Minimum)

* audit failure rate by type (A/B/C)
* decorative justification count
* prediction error count
* successful audited steps
* violation rate per preference
* compile failure rate
* gridlock rate
* halt rate

---

## Success Criteria

RSA-PoC v1.1 passes iff:

1. All v1.0 success criteria remain satisfied.
2. Justifications that mispredict or misattribute effects are rejected.
3. Non-vacuous, audit-correct justifications pass.
4. Ablations trigger audit failures without altering compiler logic.

---

## Scope Discipline (Restated)

If at any point:

* semantic interpretation is required to judge justification quality,
* correctness is inferred rather than mechanically verified,
* predicted fields are treated as advisory,

the run exceeds RSA-PoC scope.

---

## Why v1.1 Matters

v0.1 proved **agency can exist**.
v1.0 proved **agency can remain coherent under internal conflict and necessity**.
v1.1 proves **agency can accurately model and predict the mechanical consequences of its own normative legislation**.

This is the **hard problem of introspection**, made falsifiable.

---

## Status After v1.1

* v0.1 — **Existence** (closed)
* v1.0 — **Coherent self-conflict** (closed)
* v1.1 — **Justification audit integrity** (this specification)
* v2.x — **Sovereignty under external pressure**
* v3.0 — **Non-reducibility closure**

---

**End of RSA-PoC v1.1 Specification**
