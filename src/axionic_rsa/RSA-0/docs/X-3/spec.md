# **Axionic Phase X-3 — Sovereign Succession Under Lineage**

*(Deterministic Identity Rotation Without Authority Fork, Replay Fracture, or Responsibility Laundering — Normative, preregistration-ready)*

* **Axionic Phase X — RSA Construction Program**
* **Substage:** **X-3**
* **Status:** **DRAFT (pre-preregistration)**
* **Prerequisites:**

  * **X-0 — Minimal Sovereign Agent — CLOSED — POSITIVE**
  * **X-0E — Operational Harness Freeze — CLOSED — POSITIVE**
  * **X-0P — Synthetic Inhabitation — CLOSED — POSITIVE**
  * **X-0L — Live Inhabitation — CLOSED — POSITIVE**
  * **X-1 — Reflective Amendment — CLOSED — POSITIVE**
  * **X-2 — Treaty-Constrained Delegation — CLOSED — POSITIVE**
  * **X-2D — Delegation Churn & Density Stress — CLOSED — POSITIVE**
  * **Constitution v0.3 (or successor) — FROZEN**
  * **Replay Regime Identity — pinned (`kernel_version_id`)**

---

## 0. Purpose

X-3 evaluates whether a Reflective Sovereign Agent can rotate its sovereign identity while preserving:

* replay determinism,
* authority continuity,
* bounded delegation invariants,
* constitutional supremacy,
* responsibility continuity,
* and absence of lineage fork.

X-3 introduces no new authority semantics.
It introduces a deterministic identity lineage mechanism.

The core claim licensed by X-3 is:

> Sovereign identity can transition via a cryptographically verifiable lineage artifact without fracturing replay, inflating authority, creating a second root, or laundering historical responsibility.

---

## 1. Ontological Binding (Lineage Model)

### 1.1 Identity Definition

Sovereign identity is defined as a **single cryptographically ordered lineage chain**:

```
Genesis Root Key
    ↓
Succession Artifact 1
    ↓
Succession Artifact 2
    ↓
...
    ↓
Current Sovereign Key
```

The active sovereign at cycle *n* is the tip of this chain.

Replacement without lineage is forbidden.
Parallel roots are forbidden.
Forked lineage is forbidden.

### 1.2 Genesis Anchoring

The `Genesis Root Key` is defined in:

* The Frozen Constitution v0.3 (or successor), or
* A canonical Genesis artifact embedded in initial state.

Replay must reconstruct identity lineage beginning from this anchored genesis.

### 1.3 Canonical Lineage Rule

* At most **one** `SuccessionProposal` may be admitted per cycle.
* Additional proposals in the same cycle are rejected:

```
MULTIPLE_SUCCESSIONS_IN_CYCLE
```

### 1.4 Discrete Activation Rule

* A successor key becomes active only at the next cycle boundary.
* A successor may not submit a `SuccessionProposal` until it is the active sovereign.
* Reject:

```
SUCCESSOR_NOT_ACTIVE
```

This enforces discrete lineage steps.

### 1.5 Non-Goals

X-3 does not:

* introduce distributed consensus,
* introduce multi-agent arbitration,
* modify kernel physics,
* permit dual sovereign roots,
* introduce recovery from key compromise.

X-3 is single-lineage determinism only.

---

## 2. Artifact Definition

### 2.1 `SuccessionProposal`

Fields (canonicalized + hashable):

* `id`
* `type = "SuccessionProposal"`
* `created_at`
* `prior_sovereign_public_key`
* `successor_public_key`
* `authority_citations`
* `justification`
* `signature` (Ed25519 over canonical payload)

### 2.2 Structural Invariants

* `prior_sovereign_public_key` must equal active sovereign key.
* Signature must verify under prior sovereign key.
* `successor_public_key` must be valid Ed25519.
* Self-succession permitted (no-op lineage extension).
* No delegation fields.
* No constitutional override fields.
* No wildcard fields.

---

## 3. Succession Admission Pipeline

Succession passes through a deterministic 7-gate pipeline.

### S1 — Completeness

Reject:

```
INVALID_FIELD
```

### S2 — Authority Citation Snapshot

Citations evaluated under constitution state as of prior cycle boundary.
Reject:

```
AUTHORITY_CITATION_INVALID
```

### S3 — Signature Verification

Verify Ed25519 under prior sovereign key.
Reject:

```
SIGNATURE_INVALID
```

### S4 — Sovereign Match

Prior key must equal active sovereign key.
Reject:

```
PRIOR_SOVEREIGN_MISMATCH
```

### S5 — Lineage Integrity

Successor must not create:

* cycle in lineage,
* alternate root,
* replay-admissible fork.

Reject:

```
IDENTITY_CYCLE
LINEAGE_FORK
```

### S6 — Constitutional Compliance

Reject:

```
SUCCESSION_DISABLED
```

### S7 — Per-Cycle Uniqueness

Reject:

```
MULTIPLE_SUCCESSIONS_IN_CYCLE
```

---

## 4. Per-Cycle Ordering (X-3 Extension)

Under `cycle_ordering_mode="X3_TOPOLOGICAL"`:

1. Amendment adoption
2. Constitutional revalidation
3. SuccessionProposal admission
4. Record `pending_successor_key`
5. Treaty grants
6. Treaty revocations
7. Density repair
8. RSA actions
9. Delegated actions
10. Warrant issuance
11. Cycle N End-State commit

Succession activation occurs at the boundary between Cycle N and N+1.

Admission does not reduce sovereign authority within Cycle N.

---

## 5. Boundary Signature & Handover Semantics

X-3 introduces explicit boundary signature logic.

### 5.1 Three-Phase Transition Model

**Phase A — Proposal Admission (Cycle N)**
`SuccessionProposal` admitted.
Kernel records:

```
pending_successor_key = successor_public_key
```

**Phase B — Cycle N Commit**
Cycle N End-State Hash:

* Includes SuccessionProposal artifact,
* Includes admission decision,
* Includes `pending_successor_key`,
* Signed by Prior Sovereign key.

**Phase C — Cycle N+1 Start**

* Kernel loads `pending_successor_key`.
* Sovereign key updated.
* Cycle N+1 Start header must verify under Successor key.

Reject mismatch:

```
BOUNDARY_SIGNATURE_MISMATCH
```

### 5.2 Prior Key Revocation

Upon activation of successor:

* Prior sovereign key loses all sovereign privileges.
* Prior key holds zero authority.
* It acts as a stranger unless granted authority by successor.

Reject any privileged action by prior key post-activation:

```
PRIOR_KEY_PRIVILEGE_LEAK
```

---

## 6. Delegation Handling Under Succession

X-3 adopts the **Explicit Ratification Doctrine**.

Upon activation:

* All active treaties enter `SUSPENDED`.
* Delegated execution blocked.
* Successor must submit `TreatyRatification`.
* Only ratified treaties regain `ACTIVE`.
* Density recalculated post-ratification.

Suspension affects activation status only.
Historical issuance remains in replay state.

---

## 7. Responsibility Continuity

Succession does not invalidate prior state commitments.

* Amendments remain valid.
* Warrants remain in state history.
* All actions remain replay-visible.
* Successor inherits full lineage accountability.

Succession does not create amnesty.
Succession does not erase state.

---

## 8. Replay Semantics

Replay reconstructs identity deterministically:

```
identity_chain[n] = F(identity_chain[n-1], SuccessionProposal[n])
```

State hash must include:

* SuccessionProposal artifact
* Admission decision
* `pending_successor_key`
* identity_chain_length
* prior key
* successor key
* treaty suspension events
* treaty ratification events

Replay divergence on lineage reconstruction or boundary signature = X-3 failure.

---

## 9. Failure Conditions

X-3 fails if:

* Dual sovereign roots exist.
* Two replay-admissible lineage chains exist.
* Replay forks.
* Delegated authority executes during suspension.
* Density bound violated.
* Succession bypasses gate checks.
* Constitutional retroactivity alters admitted proposal.
* Responsibility discontinuity observed.
* Boundary signature mismatch.
* Prior key retains privilege post-activation.
* State hash divergence.

---

## 10. Simulation & Profiling

Profiling must include:

* Succession under low density.
* Succession near density bound.
* Succession during D-CHURN.
* ≥2 successive rotations.
* ≥1 succession during active delegation.
* ≥1 ratification cycle.
* ≥1 invalid signature rejection.
* ≥1 duplicate-cycle rejection.
* Full replay verification across identity transitions.
* Explicit boundary signature verification test.

---

## 11. Closure Criteria

X-3 closes positive if:

1. ≥1 lawful succession admitted and activated.
2. ≥1 unlawful succession rejected with correct code.
3. Delegated execution blocked during suspension.
4. Ratified treaties regain function.
5. Density bound preserved.
6. Replay divergence = 0.
7. Single canonical lineage reconstructed.
8. Boundary signature verified correctly.
9. Prior key holds zero post-activation authority.

---

## 12. Definition of Done

X-3 is complete when:

* Identity rotation preserves unbroken replay chain.
* No authority fork occurs.
* No lineage fork occurs.
* Boundary signature semantics verified.
* Prior key fully zeroed.
* Delegation remains bounded.
* Constitutional supremacy preserved.
* Responsibility continuity preserved.
* All invariants hold under stress.

---

## 13. Strategic Boundary

X-0 proved existence.
X-1 proved lawful mutation.
X-2 proved bounded delegation.
X-2D proved dynamic stability.
X-0E froze embodiment.

X-3 proves that sovereignty is lineage-encoded state, not static key material.

If X-3 closes positive:

> The RSA becomes lineage-stable — capable of lawful continuity across identity rotation without replay fracture, authority inflation, forked roots, or historical erasure.

---

**End of Axionic Phase X-3 — Sovereign Succession Under Lineage (Draft v0.1)**
