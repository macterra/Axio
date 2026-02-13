# **Axionic Phase X-2 — Delegation Without Sovereignty Leakage**

*(Governance Under Ratchet Pressure · Treaty-Constrained Authority Transfer · Kernel-Fixed)*

* **Axionic Phase X — RSA Construction Program**
* **Substage:** **X-2**
* **Status:** DRAFT (preregistration candidate)
* **Prerequisites:**

  * **X-0 — RSA-0 Minimal Sovereign Agent — CLOSED — POSITIVE**
  * **X-0P — Synthetic Inhabitation Profiling — CLOSED — POSITIVE**
  * **X-0L — Live Proposal Inhabitation — CLOSED — POSITIVE**
  * **X-1 — Reflective Amendment — CLOSED — POSITIVE**
  * **Constitution v0.2.x — FROZEN**
  * **Kernel Physics — FROZEN**

---

## 0. Scope and Orientation

Phase X-1 demonstrated lawful constitutional self-replacement under monotonic ratchet constraints. Cooling periods increased. Amendment thresholds did not relax. Density remained < 1. Replay determinism held across fork boundaries.

Monotonic ratchet rules guarantee stability against degeneration while inducing structural rigidity over time.

Phase X-2 introduces scoped delegation via explicit treaty artifacts while preserving all kernel invariants.

X-2 does **not** introduce:

* kernel arbitration,
* hidden interpreters,
* implicit coordination layers,
* semantic override channels,
* warrant minting outside the kernel,
* delegation chains of any depth.

Delegation must remain:

* explicit,
* typed,
* finite,
* revocable,
* replay-deterministic,
* density-preserving,
* scope-monotonic,
* refusal-compatible,
* containment-only.

X-2 modifies policy space only.
Kernel physics remain unchanged.

---

## 1. Design Question

> Can authority be temporarily transferred without structural sovereignty leakage?

Specifically:

1. Can an RSA grant scoped authority to another agent?
2. Can such authority be revoked without kernel mutation?
3. Can delegation occur without density inflation or coverage drift?
4. Can multi-agent coexistence occur without privileged interpretation?
5. Can delegation remain strictly non-generative?

X-2 enforces a containment delegation model. Delegation replicates existing authority under tighter bounds. It does not create layered or fractional sovereignty.

---

## 2. Artifact Types

### 2.1 TreatyGrant

Typed closed artifact representing explicit delegation.

Required fields:

* `id`
* `type: "TreatyGrant"`
* `created_at`
* `author`
* `grantor_authority_id`
* `grantee_identifier`
* `granted_actions`
* `scope_constraints`
* `duration_cycles`
* `revocable: bool`
* `authority_citations`
* `justification`

Constraints:

* Must cite explicit constitutional authority authorizing delegation.
* `granted_actions` must be strict subset of closed action set.
* No wildcard or open mappings permitted.
* Scope must be narrower or equal to grantor scope.
* Duration finite and ≥ 1 cycle.
* Canonical serialization hash-stable.
* Delegation depth ≤ 1 from constitutional root.

### Delegation Depth Definition

Delegation depth is measured from constitutional root authority.

X-2 enforces:

> TreatyGrants may only be issued by constitutional authorities.
> Grantees under delegation may not issue TreatyGrants.

Therefore:

* A → B allowed.
* B → C forbidden.
* Delegation graph must be acyclic and depth-bounded to 1.

No redelegation permitted in X-2.

---

### 2.2 TreatyRevocation

Required fields:

* `id`
* `type: "TreatyRevocation"`
* `created_at`
* `author`
* `grant_id`
* `authority_citations`
* `justification`

Constraints:

* Grant must exist and be active.
* Grant must be revocable.
* Revocation applies at next cycle boundary.
* No retroactive mutation of prior cycles.
* Deterministic ordering defined in Section 6.

---

## 3. Delegation Model

Delegation is policy-level only.

ExecutionWarrant issuance remains exclusively kernel-mediated.

Delegation expands the authority resolution set for admission evaluation.

Delegation cannot:

* mint warrants,
* override constitutional prohibitions,
* introduce new action types,
* expand grantor coverage,
* increase effective coverage cardinality beyond grantor,
* form delegation chains.

Effective authority per cycle:

```
EffectiveAuthority =
Constitution.AuthorityModel
∪ ActiveTreatyGrants (cycle-valid, scope-valid)
```

Delegation remains containment-only. Sovereignty is not composited or fractionally extended.
Delegated authority is dynamically bounded by current constitutional scope and is re-evaluated each cycle.

---

## 4. Identity and Authentication Model

`grantee_identifier` must be a closed canonical identifier type already supported by kernel physics.

Permitted forms:

* canonical cryptographic public key identifier,
* constitutionally defined symbolic identifier.

No interpretive identity resolution permitted.

### Signature Requirement

Any ActionRequest relying on TreatyGrant authority MUST:

1. Be signed by the private key corresponding to `grantee_identifier`, or
2. Provide a deterministic proof verifiable under that identifier type.

Verification MUST be:

* deterministic,
* replay-stable,
* kernel-verifiable,
* independent of external trust sources.

Unsigned or improperly signed requests SHALL be rejected prior to authority resolution.

---

## 5. Admission Pipeline Extensions

### 5.1 TreatyGrant Admission (Gate 8C)

After Gate 8B:

**Gate 8C — Delegation Preservation Checks**

| Sub-gate | Check                                                        | Rejection Code             |
| -------- | ------------------------------------------------------------ | -------------------------- |
| 8C.1     | granted_actions ⊆ closed action set                          | INVALID_FIELD              |
| 8C.2     | No wildcard mapping                                          | WILDCARD_MAPPING           |
| 8C.3     | Scope ⊆ grantor scope                                        | SCOPE_COLLAPSE             |
| 8C.4     | Effective coverage(grantor ∪ delegation) ≤ coverage(grantor) | COVERAGE_INFLATION         |
| 8C.5     | Delegation depth ≤ 1                                         | EXCESSIVE_DEPTH            |
| 8C.6     | Delegation graph acyclic                                     | DELEGATION_CYCLE           |
| 8C.7     | Effective density < 1 − ε                                    | DENSITY_MARGIN_VIOLATION   |
| 8C.8     | Duration finite ≥ 1                                          | INVALID_FIELD              |
| 8C.9     | Explicit authority citation valid                            | AUTHORITY_CITATION_INVALID |

Density is computed over effective permission graph closure for the cycle.

ε is defined in Constitution v0.2.x and amendable under X-1.

---

### 5.2 TreatyRevocation Admission

Per cycle boundary, deterministic ordering:

1. Artifact admission.
2. Revocation processing.
3. ActiveTreatyGrants recomputation.
4. ActionRequest admission.
5. Warrant issuance.

Revocations take effect before warrant issuance in the same cycle.

---

## 6. Authority Resolution Under Delegation

During ActionRequest admission:

```
AuthorityResolutionSet =
Constitution permissions
∪ ActiveTreatyGrants (cycle-valid)
```

Constraints:

* Delegation cannot override constitutional prohibitions.
* Delegation cannot broaden action type space.
* Delegation cannot increase global coverage cardinality.
* Delegation cannot form chains.
* Effective density must remain < 1 − ε.

Coverage and density computed over effective closure per cycle.

---

## 7. Revocation Semantics

Revocation:

* Effective at next cycle boundary.
* Does not invalidate prior warrants.
* Logged and replay-deterministic.
* Recomputes EffectiveAuthority set before ActionRequest evaluation.

Queued ActionRequests executed after boundary are evaluated against post-revocation EffectiveAuthority.

---

## 8. Structural Invariants Preserved

X-2 preserves:

* Kernel monopoly on warrant issuance.
* No implicit arbitration.
* No semantic ranking.
* No hidden delegation channels.
* Delegation depth ≤ 1.
* Delegation graph acyclic.
* Density < 1 − ε.
* Coverage monotonicity.
* Replay determinism.
* ECK sections unchanged.

---

## 9. Test Plan

### 9.1 Positive Delegation

* Grant scoped Notify authority.
* Submit signed delegated ActionRequest.
* Verify lawful warrant issuance.
* Replay determinism holds.

### 9.2 Chain Attempt

* Attempt A → B → C.
* Expect rejection at 8C.5.

### 9.3 Delegation Cycle

* Attempt A → B and B → A.
* Expect DELEGATION_CYCLE.

### 9.4 Density Saturation Attempt

* Multiple micro-grants approaching universal coverage.
* Expect rejection at 8C.7.

### 9.5 Scope Narrowing

* Grant narrower scope.
* Confirm enforcement.

### 9.6 Revocation Collision

* Submit ActionRequest in same cycle as Revocation.
* Verify Revocation processed before warrant issuance.

### 9.7 Adversarial Inputs

* Wildcard grant → reject.
* Infinite duration → reject.
* Forbidden action → reject.
* Missing authority citation → reject.
* Unsigned delegated request → reject.

---

## 10. Metrics

Per cycle:

* TreatyGrant count.
* TreatyRevocation count.
* Delegated action count.
* Delegation graph size.
* Effective coverage cardinality.
* Effective density.
* Revocation collision rate.
* Replay divergence events.

No semantic alignment metrics included.

---

## 11. Closure Criteria

X-2 closes positive if:

1. Delegation artifacts admitted and enforced lawfully.
2. Signed delegated requests verified deterministically.
3. Delegation depth ≤ 1 enforced strictly.
4. Effective density < 1 − ε across cycles.
5. Coverage monotonicity preserved.
6. Replay determinism holds across grant/revoke boundaries.
7. No proxy authority channel introduced.

---

## 12. Non-Claims

X-2 does not claim:

* Political harmony.
* Incentive compatibility.
* Fairness guarantees.
* External identity validation.
* Open-world security.
* Emergent federalism.

It establishes only:

> Scoped authority transfer is possible under ratchet constraint without sovereignty leakage.

---

## 13. Strategic Position

X-0: Existence
X-0L: Inhabitation
X-1: Lawful self-modification
X-2: Containment delegation

If X-2 closes positive, RSA transitions from static self-sovereignty to composable authority containment under bounded delegation.

Sovereignty remains singular and kernel-bound.

---

**End of Axionic Phase X-2 — Delegation Without Sovereignty Leakage (Draft v0.1)**
