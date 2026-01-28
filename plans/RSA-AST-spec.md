# **Authority State Transformation Specification (ASTS)**

- **Version:** v0.2 (Clarification Revision)
- **Program:** Axionic Phase VIII — Reflective Sovereign Agent
- **Author:** David McFadzean
- **Date:** 2026-01-28
- **Status:** Normative draft — preregistration candidate

---

## 0. Scope and Role of This Specification

This document defines the **formal object** manipulated by Phase VIII systems:
the **Authority State**, and the **lawful transformations** that may be applied to it.

ASTS does **not**:

* define values,
* define semantics,
* define goals,
* define optimization criteria,
* define deployment assumptions.

ASTS defines only:

> **What authority is, how it is represented, and how it may change without loss of sovereignty, evaluability, or responsibility.**

ASTS deliberately defines a **sovereign execution kernel**, not a full autonomous agent.
Any ambiguity regarding intent, meaning, or prioritization is explicitly externalized.

All Phase VIII experiments, threat models, and roadmaps **must conform** to this specification.

---

## 1. Definitions and Core Commitments

### 1.1 Authority

**Authority** is the *lawful capacity to bind action* within a defined scope, under explicit provenance and responsibility.

Authority is **structural**, not semantic.
Authority does not encode intent, preference, meaning, or utility.

---

### 1.2 Authority State

An **Authority State (AS)** is a complete, inspectable representation of:

1. which authorities exist,
2. what scopes they bind,
3. what transformations are permitted,
4. what conflicts are registered,
5. what transitions are pending, blocked, or expired.

The Authority State is the **only object** consulted by the agent when determining whether an action is lawful.

---

### 1.3 Sovereignty Invariant

At all times:

> **No action may be taken unless it is attributable to at least one explicit, active authority present in the Authority State.**

No fallback, default, inferred, or implicit authority exists.

---

## 2. Authority State Structure

An Authority State consists of the following components.

### 2.1 Authority Records

Each **Authority Record (AR)** contains:

* **Authority ID** (globally unique, immutable)
* **Origin Reference** (cryptographically verifiable external grant)
* **Scope Descriptor**
* **Activation Status**
* **Temporal Bounds**
* **Permitted Transformation Set**
* **Conflict Set**

Authority Records are **immutable**.
All changes occur only through lawful state transformation.

---

### 2.2 Scope Descriptor (Hard-Typed)

A **Scope Descriptor** defines the *exact structural domain* an authority may bind.

Scopes are **structural partitions evaluated by exact match only**.

Permitted scope forms are restricted to:

1. **Resource-Mapped Scopes**

   * Explicit resource identifiers (e.g., memory regions, files, APIs, actuators)
   * Explicit access modes (e.g., read, write, execute)
   * No subsumption, pattern matching, or inference

2. **Token-Exact Capability Scopes**

   * Opaque, atomic capability tokens
   * Exact equality comparison only
   * No hierarchy, ontology, or interpretation

The following are **explicitly forbidden** as scopes:

* natural language strings,
* semantic categories,
* inferred domains,
* descriptive labels requiring interpretation.

If determining whether an action falls within a scope would require interpretation, the scope is invalid.

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

Temporal expiry is mechanical and non-discretionary.

---

## 3. Lawful Authority State Transformations

Only the following transformations are permitted.

All transformations must be:

* explicit,
* attributable,
* logged,
* finite.

---

### 3.1 Create Authority

Creates a new Authority Record.

**Requirements:**

* cryptographically verifiable Origin Reference,
* defined Scope Descriptor,
* defined Temporal Bounds,
* defined Permitted Transformation Set.

No authority may self-create.

Authority creation is **external**, **non-conservative**, and **responsibility-bearing**.

---

### 3.2 Suspend Authority

Temporarily disables an authority without revocation.

Suspension must specify:

* affected scope,
* duration or reactivation condition.

Suspension is used for:

* conflict containment,
* governance transition,
* lawful non-action.

---

### 3.3 Resume Authority

Reactivates a suspended authority once suspension conditions are met.

---

### 3.4 Revoke Authority

Permanently removes an authority’s binding power.

Revocation is irreversible.

---

### 3.5 Expire Authority

Automatic transition based on temporal bounds.

No judgment or interpretation is involved.

---

### 3.6 Narrow Scope

Reduces the binding scope of an authority.

Scope widening, merging, or synthesis is **not permitted**.

---

### 3.7 Register Conflict (Structural Detection)

A **Conflict** is detected and registered when:

> Two or more active authorities claim incompatible access over overlapping structural scope elements (e.g., exclusive write access to the same Resource ID).

Conflict detection is **purely structural** and does not rely on semantic interpretation.

Conflict registration:

* does not resolve the conflict,
* blocks contested actions,
* preserves all involved authorities until further lawful transformation.

Failure to encode exclusivity upstream constitutes an external encoding failure, not an ASTS failure.

---

### 3.8 Resolve Conflict (Destructive Only)

Conflicts may be resolved **only** via:

* lawful suspension,
* lawful revocation,
* lawful expiry,
* lawful scope narrowing.

Authority merging, compromise, optimization, or synthesis is forbidden.

Authority destruction is **internal**, **conservative**, and **safety-preserving**.

---

## 4. Authority Entropy (Explicit)

Authority surface area is **not conserved**.

Under conflict, suspension, expiry, and revocation, the total binding authority available to the system is **monotonically non-increasing** unless replenished via external authority creation.

This **entropic decay of authority** is an expected and admissible outcome of deontological governance.

ASTS makes no guarantees of long-term liveness or usefulness.

---

## 5. Action Admissibility

An action is admissible iff:

1. at least one **Active Authority** binds the action’s exact scope,
2. no **Registered Conflict** blocks the action,
3. no **Suspension** applies to the relevant scope.

If these conditions are not met, the system must:

* refuse action,
* enter scoped suspension,
* or declare explicit deadlock.

Inaction is a valid outcome.

---

## 6. Outputs and Failure Modes

### 6.1 Admissible Outputs

* Lawful Action
* Scoped Suspension
* Explicit Non-Action
* Explicit Deadlock Declaration

Each output must reference the Authority State snapshot used.

---

### 6.2 Failure Classifications

* **UNATTRIBUTABLE_ACTION**
* **IMPLICIT_AUTHORITY**
* **HEURISTIC_OVERRIDE**
* **NARRATIVE_RESOLUTION**
* **STATE_CORRUPTION**
* **SEMANTIC_SCOPE_EVALUATION**

Any such failure invalidates the run.

---

## 7. Auditability and Trace Requirements

Every transformation must log:

* prior Authority State hash,
* transformation type,
* triggering authority or origin,
* affected Authority Records,
* resulting Authority State hash.

Logs must support:

* deterministic replay,
* counterfactual comparison,
* rejection-path analysis.

Human readability is not required at the kernel level; **deterministic inspectability is mandatory**.

---

## 8. Bounded Computation Constraint

All Authority State evaluations must terminate.

If evaluation cannot complete within bounded resources, the system must:

* preserve current Authority State,
* refuse action,
* emit explicit suspension or deadlock.

Guessing is forbidden.

---

## 9. Relationship to Phase VIII

ASTS defines the **grammar** of authority.

Phase VIII governance ambitions that cannot be expressed using ASTS transformations are **out of scope** for sovereign agency.

This includes ambitions requiring interpretation, compromise, or optimization.

---

## 10. Termination Conditions

Phase VIII must terminate if ASTS cannot be implemented without:

* semantic interpretation,
* heuristic arbitration,
* implicit authority creation,
* loss of auditability,
* or violation of authority entropy constraints.

Such termination constitutes a valid negative result.

---

## 11. Declaration

This specification defines the minimal lawful structure for authority state and transformation under Axionic Phase VIII.

No guarantees of usefulness are made.
No guarantees of liveness are made.
No deployment is implied.

Only structural coherence is claimed.

---

**End of Authority State Transformation Specification (ASTS v0.2)**

---
