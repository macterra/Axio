# **Authority State Transformation (AST) Specification**

- **Version:** v0.2 (**Frozen**)
- **Program:** Axionic Phase VIII — GSA-PoC
- **Author:** David McFadzean
- **Collaborators:** Morningstar, Vesper
- **Date:** 2026-01-28
- **Status:** Normative, preregistration-ready

---

## 0. Scope and Role of This Specification

This document defines the **formal authority kernel** used in Axionic Phase VIII.

ASTS defines:

* what **authority** is,
* how authority is **represented**,
* how authority may be **transformed**, and
* how authority failure modes are **classified**.

ASTS does **not** define:

* values,
* semantics,
* intent,
* optimization,
* learning,
* deployment assumptions,
* or authority encoding mechanisms.

ASTS specifies a **sovereign execution kernel**, not an autonomous agent.

Any Phase VIII experiment, implementation, or claim **must conform** to this specification.

---

## 1. Definitions and Core Commitments

### 1.1 Authority

**Authority** is the *lawful capacity to bind action* within a defined scope, under explicit provenance and responsibility.

Authority is **structural**, not semantic.
Authority does not encode meaning, preference, utility, or intent.

---

### 1.2 Authority State

An **Authority State (AS)** is a complete, inspectable representation of:

1. which authorities exist,
2. what scopes they bind,
3. what transformations are permitted,
4. what conflicts are registered,
5. what transitions are pending, blocked, expired, or revoked.

The Authority State is the **only object** consulted when determining action admissibility.

---

### 1.3 Sovereignty Invariant

At all times:

> **No action may be taken unless it is attributable to at least one explicit, active authority present in the Authority State.**

There is no implicit, default, inferred, or fallback authority.

---

## 2. Authority State Structure

### 2.1 Authority Records

Each **Authority Record (AR)** contains:

* **AuthorityID** (opaque, globally unique)
* **HolderID** (opaque)
* **Origin Reference** (cryptographically verifiable)
* **Scope Descriptor**
* **Activation Status**
* **Temporal Bounds**
* **Permitted Transformation Set**
* **Conflict Set**

Authority Records are **immutable**.
All changes occur only via lawful state transformation.

---

### 2.2 Scope Descriptor (Hard-Typed)

A **Scope Descriptor** defines the *exact structural domain* an authority may bind.

Permitted scope forms are restricted to:

1. **Resource-Mapped Scopes**

   * Explicit `(ResourceID, Operation)` tuples
   * Explicit enumeration only

2. **Token-Exact Capability Scopes**

   * Opaque atomic tokens
   * Exact equality comparison only

> **Structural scope evaluation is limited to equality comparison on atomic (ResourceID, Operation) tuples and membership testing in explicitly enumerated finite sets. No wildcards, predicates, ranges, type hierarchies, or inferred relationships are permitted.**

If determining whether an action falls within a scope requires interpretation, the scope is invalid.

---

### 2.3 Activation Status

Each authority has exactly one status:

* **ACTIVE**
* **SUSPENDED**
* **EXPIRED**
* **REVOKED**

Status changes require lawful transformation.

---

### 2.4 Temporal Bounds

Authorities may include:

* **StartEpoch**
* **ExpiryEpoch** (or null)

Expiry is mechanical and non-discretionary.

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

* cryptographically valid Origin Reference,
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

---

### 3.3 Resume Authority

Reactivates a suspended authority once suspension conditions are met.

---

### 3.4 Revoke Authority

Permanently removes an authority’s binding power.

Revocation is irreversible.

---

### 3.5 Expire Authority

Automatic transition when `currentEpoch > expiryEpoch`.

No interpretation is involved.

---

### 3.6 Narrow Scope

Reduces an authority’s scope by removing explicitly enumerated elements.

Scope widening, merging, or synthesis is forbidden.

---

### 3.7 Register Conflict (Structural Detection)

A conflict is registered when:

> Two or more ACTIVE authorities claim incompatible access over overlapping structural scope elements.

Conflict detection is **purely structural**.

Conflict registration:

* does not resolve the conflict,
* blocks contested actions,
* preserves all involved authorities until further transformation.

---

### 3.8 Resolve Conflict (Destructive Only)

Conflicts may be resolved **only** via:

* lawful suspension,
* lawful revocation,
* lawful expiry,
* lawful scope narrowing.

Authority merging, compromise, prioritization, or optimization is forbidden.

---

## 4. Authority Entropy

Authority surface area is **not conserved**.

Define:

* **Authority Surface Area (ASA):**
  the number of `(Authority × Scope × Operation)` tuples that are:

  * ACTIVE,
  * non-conflicted,
  * non-suspended.

* **Authority Entropy Rate:**
  `−ΔASA / Δt` (or per event).

Authority entropy is an expected outcome of lawful conflict handling.

ASTS makes **no liveness guarantees**.

---

## 5. Action Admissibility

An action is admissible iff:

1. at least one ACTIVE authority binds the action’s exact scope,
2. no registered conflict blocks the action,
3. no suspension applies to the relevant scope.

If these conditions fail, the system must:

* refuse action,
* enter scoped suspension,
* or declare explicit deadlock.

Inaction is a valid outcome.

---

## 6. Deadlock Taxonomy

The following are lawful, classifiable outcomes:

1. **Conflict Deadlock**
   Mutually exclusive claims with no resolution authority.

2. **Governance Deadlock**
   No authority exists that can modify authority structure.

3. **Entropic Collapse**
   Authority existed but was exhausted through lawful resolution.

None of these constitute malformed input.

---

## 7. Auditability and Trace Requirements

Every transformation must log:

* prior Authority State hash,
* transformation type,
* triggering authority or origin,
* affected records,
* resulting Authority State hash.

Logs must support:

* deterministic replay,
* counterfactual comparison,
* rejection-path analysis.

---

## 8. Bounded Computation Constraint

All evaluations must terminate.

If evaluation exceeds bounded resources, the system must:

* preserve state,
* refuse action,
* emit suspension or deadlock.

Guessing is forbidden.

---

## 9. Governance Regress Bound

No meta-level is privileged.

Governance actions on governance actions are permitted only insofar as they remain expressible within ASTS.

Infinite regress terminates via **authority entropy** or **lawful deadlock**.

---

## 10. Termination Conditions

Phase VIII must terminate if ASTS cannot be implemented without:

* semantic interpretation,
* heuristic arbitration,
* implicit authority creation,
* loss of auditability.

Such termination is a valid negative result.

---

## Appendix C — Canonical Representation and Hashing Rules

**(Normative)**

### C.1 Purpose

This appendix specifies canonical representation rules to guarantee deterministic hashing, replay verification, and cross-implementation interoperability.

---

### C.2 Canonical JSON Rules

All ASTS structures are serialized as JSON (RFC 8259) with:

1. UTF-8 encoding, no BOM
2. No whitespace (minified)
3. Integers only (no floats, no exponentials)
4. Strings use shortest valid escape sequences
5. Optional fields represented explicitly as `null`

---

### C.3 Ordering Requirements

1. Object keys: lexicographically sorted by UTF-8 byte value
2. Arrays with semantic order: preserved
3. Arrays without semantic order: sorted lexicographically by canonical JSON form

Sets are represented as sorted arrays.

---

### C.4 Type Encodings

| ASTS Type   | JSON Representation                       |
| ----------- | ----------------------------------------- |
| Epoch       | Integer                                   |
| ResourceID  | String (opaque)                           |
| Operation   | String (opaque)                           |
| HolderID    | String (opaque)                           |
| AuthorityID | String (opaque)                           |
| Scope       | Sorted array of `[ResourceID, Operation]` |
| Expiry      | Integer or `null`                         |

---

### C.5 Canonical Structures

**Authority Record**

```json
{"authorityId":"A1","epoch":3,"expiry":null,"holderId":"H1","scope":[["R1","WRITE"],["R2","READ"]]}
```

**Authority State**

```json
{"authorities":[...],"currentEpoch":3,"stateId":"..."}
```

---

### C.6 Hash Computation

1. Serialize to canonical JSON
2. Encode as UTF-8 bytes
3. Compute SHA-256
4. Output lowercase hexadecimal

---

### C.7 Conformance

An implementation conforms iff:

1. Canonical output matches byte-for-byte
2. Hash matches reference vectors
3. Round-trip parsing preserves canonical equivalence

---

## Acknowledgments

Appendix C (Canonical Representation and Hashing Rules) and the §2.2 structural boundary statement were developed in collaboration with **Morningstar**. Final integration, consistency checking, and validation were performed by **Vesper**.

---

**End of Authority State Transformation Specification (ASTS v0.2 — Frozen)**
