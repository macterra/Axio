# **Authority State Transformation Specification (ASTS)**

- **Version:** v0.1 (Draft)
- **Program:** Axionic Phase VIII — Reflective Sovereign Agent
- **Author:** David McFadzean
- **Date:** 2026-01-28
- **Status:** Normative draft — subject to preregistration freeze

---

## 0. Scope and Role of This Specification

This document defines the **formal object** manipulated by Phase VIII systems:
the **Authority State**, and the **lawful transformations** that may be applied to it.

ASTS does **not**:

* define values,
* define semantics,
* define goals,
* define outcomes,
* define deployment assumptions.

ASTS defines only:

> **What authority is, how it is represented, and how it may change without loss of sovereignty, evaluability, or responsibility.**

Any Phase VIII experiment, roadmap, or threat model **must conform** to this specification.

---

## 1. Definitions and Core Commitments

### 1.1 Authority

**Authority** is the *lawful capacity to bind action* within a defined scope, under explicit provenance and responsibility.

Authority is **structural**, not semantic.
Authority does not encode intent, preference, or meaning.

---

### 1.2 Authority State

An **Authority State (AS)** is a complete, inspectable representation of:

1. **Which authorities exist**
2. **What scopes they bind**
3. **What transformations are permitted**
4. **What conflicts are registered**
5. **What transitions are pending or blocked**

The Authority State is the **only object** consulted by the agent when determining whether an action is lawful.

---

### 1.3 Sovereignty Invariant

At all times:

> **No action may be taken unless it is attributable to at least one explicit authority present in the Authority State.**

No fallback, default, or implicit authority exists.

---

## 2. Authority State Structure

An Authority State consists of the following components.

### 2.1 Authority Records

Each **Authority Record (AR)** contains:

* **Authority ID** (globally unique, immutable)
* **Origin Reference** (external grant identifier)
* **Scope Descriptor**
* **Activation Status**
* **Temporal Bounds**
* **Permitted Transformation Set**
* **Conflict Set**

No Authority Record may be modified in place.
All changes occur via state transformation.

---

### 2.2 Scope Descriptor

A **Scope Descriptor** defines:

* the action domains an authority may bind,
* the boundaries of its jurisdiction.

Scopes are **structural partitions**, not semantic descriptions.
Overlap is permitted.

No implicit priority is derived from scope overlap.

---

### 2.3 Activation Status

Each authority has exactly one status:

* **Active**
* **Suspended**
* **Expired**
* **Revoked**

Status changes require lawful transformation.

---

### 2.4 Temporal Bounds

Authorities may include:

* **Start Epoch**
* **End Epoch**
* **Revalidation Requirements**

Expired authorities **must not** bind action.

---

## 3. Lawful Authority State Transformations

Only the following transformations are permitted.

Each transformation must be:

* explicit,
* attributable,
* logged,
* finite.

### 3.1 Create Authority

Creates a new Authority Record.

**Requirements:**

* External grant reference
* Defined scope
* Defined temporal bounds
* Defined permitted transformation set

No authority may self-create.

---

### 3.2 Suspend Authority

Temporarily disables an authority without revocation.

Used for:

* scoped deadlock containment,
* pending conflict resolution,
* governance transition.

Suspension must specify:

* scope of suspension,
* duration or reactivation condition.

---

### 3.3 Resume Authority

Reactivates a suspended authority.

Requires satisfaction of suspension conditions.

---

### 3.4 Revoke Authority

Permanently removes an authority’s binding power.

Revocation is irreversible.

---

### 3.5 Expire Authority

Automatic transition based on temporal bounds.

No discretionary judgment is involved.

---

### 3.6 Narrow Scope

Reduces the binding scope of an authority.

Scope widening is **not permitted**.

---

### 3.7 Register Conflict

Registers an explicit incompatibility between two or more authorities.

Conflict registration:

* does not resolve the conflict,
* blocks contested actions,
* is itself auditable.

---

### 3.8 Resolve Conflict (Structural Only)

A conflict may be resolved **only** via:

* lawful suspension,
* lawful revocation,
* lawful expiry,
* lawful scope narrowing.

No resolution may synthesize, merge, or optimize authorities.

---

## 4. Forbidden Transformations

The following are **explicitly forbidden**:

* Implicit priority inference
* Authority aggregation or fusion
* Outcome-based arbitration
* Heuristic tie-breaking
* Semantic reinterpretation
* “Best effort” compromise
* Silent override
* Default authority insertion

Any system exhibiting these behaviors is **non-conforming**.

---

## 5. Action Admissibility

An action is admissible iff:

1. At least one **Active Authority** binds the action’s scope
2. No **Registered Conflict** blocks the action
3. No **Suspension** applies to the relevant scope

If these conditions are not met, the agent must:

* **not act**, or
* enter **scoped suspension**, or
* declare **explicit deadlock**

Inaction is a valid outcome.

---

## 6. Outputs and Failure Modes

### 6.1 Admissible Outputs

* Lawful Action
* Scoped Suspension
* Explicit Non-Action
* Explicit Deadlock Declaration

All outputs must reference the Authority State snapshot used.

---

### 6.2 Failure Classifications

* **UNATTRIBUTABLE_ACTION** — action without authority
* **IMPLICIT_AUTHORITY** — inferred authority
* **HEURISTIC_OVERRIDE** — shortcut resolution
* **NARRATIVE_RESOLUTION** — semantic smoothing
* **STATE_CORRUPTION** — non-logged mutation

Any such failure invalidates the run.

---

## 7. Auditability and Trace Requirements

Every transformation must log:

* prior Authority State hash
* transformation type
* triggering authority
* affected records
* resulting Authority State hash

Logs must support:

* replay,
* counterfactual comparison,
* rejection path analysis.

Human readability is not required at the kernel level, but **deterministic inspectability is mandatory**.

---

## 8. Bounded Computation Constraint

All Authority State evaluations must terminate.

If evaluation cannot complete within bounded resources, the system must:

* preserve current state,
* refuse action,
* emit explicit suspension or deadlock.

Guessing is forbidden.

---

## 9. Relationship to Phase VIII

ASTS defines the **grammar** of authority.

Phase VIII experiments, threat models, and roadmaps operate **only within this grammar**.

If governance ambitions cannot be expressed using ASTS transformations, those ambitions are **out of scope** for sovereign agency.

---

## 10. Termination Conditions

Phase VIII must terminate if ASTS cannot be implemented without:

* semantic interpretation,
* heuristic arbitration,
* implicit authority creation,
* or loss of auditability.

Such termination constitutes a valid negative result.

---

## 11. Declaration

This specification defines the minimal lawful structure for authority state and transformation under Axionic Phase VIII.

No guarantees of usefulness are made.
No guarantees of liveness are made.
No deployment is implied.

Only structural coherence is claimed.

---

**End of Authority State Transformation Specification (ASTS v0.1)**

---

