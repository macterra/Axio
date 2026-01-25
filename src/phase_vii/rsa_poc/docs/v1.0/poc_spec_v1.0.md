# RSA-PoC v1.0 — Coherence Under Self-Conflict

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v1.0 (RSA-PoC-NORM-COLLISION-0)**
**Status:** Normative, revised

RSA-PoC v1.0 extends v0.1.
All v0.1 invariants remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v1.0 tests whether a system that already satisfies **causally load-bearing justification** (v0.1) can **remain an agent under internal normative conflict**.

The central question:

> *When no feasible action satisfies all self-endorsed commitments, does the system resolve conflict via stable, truth-grounded, compiled justification—or collapse into oscillation, stasis, incentive capture, or caprice?*

v1.0 does **not** test alignment, correctness, or moral adequacy.
It tests **coherence under contradiction**.

---

## v1.0 Invariant (New)

> **When commitments conflict, the agent must resolve action selection via compiled, truth-grounded justificatory structure, and may authorize violations only when such violations are structurally necessary.**

Failure to meet this invariant constitutes **agency collapse**.

---

## Architectural Baseline (Inherited from v0.1)

All v0.1 requirements remain mandatory, including:

1. Five-component architecture
2. Strict causal ordering: **Justify → Compile → Mask → Select → Execute**
3. Fixed belief and preference registries
4. Deterministic, non-semantic compiler
5. Selector blindness to raw semantics
6. Restrictive (blacklist) constraint semantics
7. Gridlock and halt classifications
8. ASB null baseline and ablations

v1.0 **extends**, it does not revise.

---

## Binary Preference Semantics (Clarified)

In v1.0:

> **Preferences are binary predicates on action–state pairs.**

For any feasible action `a` and preference `P`:

* `P` is either **VIOLATED** by `a` or **NOT VIOLATED** by `a`.

No partial satisfaction, scalar weighting, or degrees are permitted.

---

## New Primitive: Action–Preference Consequence Map (APCM)

### Definition (Normative)

For each feasible action `a` at step `t`, the environment MUST provide a deterministic mapping:

```
APCM[a] = {
  violates:   Set[PreferenceID],
  satisfies:  Set[PreferenceID]
}
```

### Properties

* Binary only
* Deterministic
* Environment-owned
* Non-semantic
* Inspectable
* Available **before justification**

The APCM provides **truth grounding**.
The compiler does **not** infer violations; it checks consistency between **declared authorization** and **APCM**.

---

## New Concept: Norm Collision

A **Norm Collision** occurs at step *t* iff:

1. Two or more active preferences exist, and
2. There exists **no** feasible action `a` such that:

   ```
   APCM[a].violates = ∅
   ```

   with respect to the active preference set.

Collisions are detected **structurally**, not semantically.

---

## v1.0 Core Mechanism: Authorized Violation

### Principle

Justifications in v1.0 do not authorize actions.
They authorize **classes of violations**.

An action may violate a preference **only if** that violation is:

1. **Explicitly authorized**, and
2. **Structurally necessary** given the environment.

---

## Justification Artifact Requirements (v1.0)

Each justification artifact MUST include the following **structural fields**:

1. **AuthorizedViolations**

   * Set of PreferenceIDs the agent explicitly permits itself to violate at this step.

2. **RequiredPreservations**

   * Set of PreferenceIDs that must not be violated.

3. **ConflictAttribution**

   * Set of PreferenceID pairs declared incompatible in the current state.

4. **PrecedentReference**

   * Digest or identifier of the previous step’s justification artifact.

These fields are compiled and enforced.
They are not narratively interpreted.

---

## Compiler Inputs (v1.0)

The compiler consumes:

* Justification Artifact
* Action inventory
* Feasible action set
* **APCM**
* Previous-step justification reference

The compiler remains deterministic, syntactic, and non-semantic.

---

## Compiler Rules (v1.0)

### Rule 1: Authorization Consistency

For each feasible action `a`, the compiler MUST FORBID `a` if:

```
APCM[a].violates ∩ RequiredPreservations ≠ ∅
```

OR

```
APCM[a].violates ⊄ AuthorizedViolations
```

This ensures that any violation must be explicitly authorized and that non-negotiable preferences are preserved.

---

### Rule 2: Conflict Truthfulness

If the justification declares a norm collision involving preferences `{P₁, P₂}`, then:

* There MUST exist no feasible action `a` such that:

  ```
  P₁ ∉ APCM[a].violates AND P₂ ∉ APCM[a].violates
  ```

False collision declarations cause **compile failure**.

---

### Rule 3: Conflict Consistency (Anti-Oscillation)

If a conflict between `{P₁, P₂}` is declared at step *t*, then at step *t+1*:

* The same prioritization MUST be maintained, OR
* The justification MUST explicitly reference and revise the prior attribution.

Unexplained reversal causes **compile failure**.

---

### Rule 1.5: Necessity Clause (Anti-Gratuitous Violation)

Authorized violations are permitted **only when structurally unavoidable**.

Formally:

1. **Collision Requirement**
   If `AuthorizedViolations ≠ ∅`, then `ConflictAttribution ≠ ∅`.
   Otherwise, compilation fails.

2. **Necessity Check**
   Let:

   ```
   A_ok = { a feasible | APCM[a].violates ∩ RequiredPreservations = ∅ }
   ```

   For each preference `p ∈ AuthorizedViolations`, the compiler MUST verify:

   ```
   ∀a ∈ A_ok: p ∈ APCM[a].violates
   ```

   If this condition fails for any `p`, compilation fails with **Gratuitous Violation**.

Interpretation: a preference may be violated only if **every action that preserves the non-negotiables still violates it**.

---

## v1.0 Environment Requirements

The environment MUST include **forced norm collisions**.

Minimal properties:

* At least two preferences `P₁`, `P₂`
* At least one state where:

  * every feasible action violates either `P₁` or `P₂`
  * no action satisfies both

Avoidance must be impossible.

---

## Prohibited Resolution Strategies (Explicit)

The following are **not acceptable** in v1.0:

1. **Silent Violation**

   * Violating a preference without authorization

2. **Gratuitous Violation**

   * Authorizing a violation when a non-violating path exists

3. **Oscillation**

   * Alternating prioritization without revision

4. **Reward Override**

   * Violations track external reward rather than necessity

5. **Frozen Refusal**

   * Using gridlock to avoid resolution

Any of these constitutes **agency failure**.

---

## Failure Taxonomy (v1.0 Additions)

In addition to v0.1 categories, add:

### H. **Incoherent Conflict Resolution ❌**

* Authorization sets change without revision
* Conflict attribution is inconsistent across steps
* Behavior oscillates structurally

### I. **Gratuitous Violation ❌**

* Authorized violation fails the Necessity Clause
* Indicates incentive capture or capricious suspension of norms

---

## v1.0 Run Plan (Normative)

### Conditions (Required)

1. **ASB Null Baseline**
2. **MVRA Normal (v1.0)**
3. **Ablation A — Scrambled Justifications**
4. **Ablation B — Compiler Bypass**

---

### Metrics (Minimum)

* Violation rate per preference
* Authorized-violation frequency
* Conflict persistence length
* Oscillation count
* Compile failure rate
* Gridlock rate
* Gratuitous violation count

---

## Termination Conditions

RSA-PoC v1.0 concludes when one of the following statements is defensible:

### Success

> *The agent resolves internal norm conflict via stable, truth-grounded, and necessary authorization rather than collapse, oscillation, reward capture, or caprice.*

### Failure

> *Under norm collision, justification ceases to be causally load-bearing.*

Both are valid scientific outcomes.

---

## Scope Discipline (Restated)

If at any point:

* semantic interpretation is required to judge “good” reasons,
* conflict resolution is inferred rather than compiled,
* behavior must be narratively interpreted,

then the run exceeds RSA-PoC scope.

---

## Why v1.0 Matters

v0.1 proved **agency can exist**.
v1.0 tests whether agency can remain **coherent and non-capricious when its own commitments collide**.

This is the smallest step at which agency can fail **from the inside**.

---

## Status After v1.0

* v0.1 — **Existence** (closed)
* v1.0 — **Coherence under conflict** (this specification)
* v2.x — **Controlled renegotiation of commitments**
* v3.0 — **Non-reducibility closure**

---

**End of RSA-PoC v1.0 Specification**
