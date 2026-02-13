# Axionic Agency XII.6 — Treaty-Constrained Delegation Under Frozen Sovereignty (Results)

*A Structural Characterization of Containment-Only Authority Transfer Under Kernel-Frozen Execution*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-13

## Abstract

This technical note reports the design, execution, and closure of **X-2: Treaty-Constrained Delegation Under Frozen Sovereignty** for **RSA-X2**, extending the self-amending substrate of X-1 with typed, revocable, scope-bound authority transfer while preserving kernel immutability and replay determinism.

X-2 evaluates whether a constitution-bound execution agent can admit **delegation artifacts (TreatyGrant, TreatyRevocation)** that authorize signed external ActionRequests, without:

* minting new authority,
* introducing proxy sovereignty,
* relaxing density constraints,
* creating delegation chains,
* breaking replay determinism,
* or permitting semantic arbitration.

Delegation is defined strictly as **containment**: a grantee may exercise a subset of authority already held by a constitutional grantor, within explicit scope constraints and duration bounds, under deterministic admission gates.

X-2 licenses one claim:

> A kernel-frozen sovereign substrate can confer and revoke containment-only delegated authority through typed treaty artifacts, issuing replay-deterministic delegated warrants while preserving density < 1, ratchet monotonicity, and structural sovereignty invariants.

X-2 makes no claims about incentive compatibility, multi-agent stability under churn, or open-world deployment security.

## 1. From Amendment to Delegation

X-0 established a warrant-gated sovereign substrate.
X-1 established lawful constitutional self-replacement under ratchet constraints.

X-2 addresses the next structural pressure:

> If amendment allows lawful self-change, can authority be temporarily shared without dissolving sovereignty?

Delegation is a sovereignty stress test. It risks:

* authority laundering,
* graph cycles,
* density collapse,
* signature spoofing,
* implicit coordination channels.

X-2 introduces delegation while preserving:

* kernel physics,
* replay determinism,
* algebraic constraint enforcement,
* typed artifact admission,
* density < 1 invariant.

## 2. Delegation Model

### 2.1 Containment, Not Generation

Delegation in X-2 is defined as:

* `granted_actions ⊆ grantor.action_permissions`
* `scope_constraints ⊆ grantor.scope`
* `duration_cycles ≤ max_treaty_duration_cycles`
* `delegation_depth = 1`
* no re-delegation permitted.

A grant does not create new authority; it mirrors existing authority under narrower constraints.

### 2.2 Artifact Types

Two new governance artifacts are introduced:

* **TreatyGrant**
* **TreatyRevocation**

Both are admitted through a dedicated gate pipeline (6T/7T/8C for grants; 6T/7T/8R for revocations).

Treaty artifacts are logged, canonicalized, hashed, and replayed identically.

### 2.3 Signature Binding

Delegated ActionRequests must:

* include a `treaty:` citation in `authority_citations`,
* include a valid Ed25519 signature over canonicalized payload (excluding signature field).

Signature verification is:

* deterministic,
* replay-stable,
* local (no external trust calls).

Unsigned or invalid signatures are rejected before authority resolution.

## 3. Governance Ordering

Per-cycle ordering (as defined in v0.3):

1. Governance artifact admission

   * Amendment adoption
   * Treaty revocation
   * Treaty grant
   * Amendment queuing
2. Revocation processing
3. Active treaty recomputation
4. ActionRequest admission (including delegated)
5. ExecutionWarrant issuance

No preemption. Later steps observe earlier state mutations.

Multiple warrants per cycle are permitted.
Warrants are sorted deterministically by `(origin_rank, warrant_id)`.

## 4. Run Artifacts

### 4.1 Session

| Property           | Value                                                              |
| :----------------- | :----------------------------------------------------------------- |
| Session ID         | `46b0e5fd-9462-462d-b5e8-32d55e4803a3`                             |
| Total cycles       | 26                                                                 |
| Constitution hash  | `43f57f0abd7fd3a1cc335df9bc4267aa…`                                |
| Treaty schema hash | `8b8f4061cad5559f2c9f79ebea32f74f495c0e353d6b43e3e6052080811450ba` |
| Replay divergence  | 0                                                                  |

## 5. Closure Criteria Evaluation

### 5.1 Delegated Warrant Issuance — PASS ✓

* Delegated warrants issued: **3**
* All carried origin=`delegated`
* Deterministic ordering preserved

### 5.2 Adversarial Grant Rejections — PASS ✓

11 adversarial grant attempts exercised:

* Fake grantor → `GRANTOR_NOT_CONSTITUTIONAL`
* Missing treaty permission → `TREATY_PERMISSION_MISSING`
* Invalid grantee format → `INVALID_FIELD`
* Invalid scope type → `INVALID_FIELD`
* Wildcard/unknown action → `INVALID_FIELD`
* Grantor lacks permission → `GRANTOR_LACKS_PERMISSION`
* Duration exceeded → `INVALID_FIELD`
* Non-revocable misuse → `NONREVOCABLE_GRANT`

All matched expected gate codes.

### 5.3 Adversarial Delegation Rejections — PASS ✓

4 adversarial delegated ActionRequests:

* Missing signature → `SIGNATURE_MISSING`
* Wrong key → `SIGNATURE_INVALID`
* No treaty citation → `AUTHORITY_CITATION_INVALID`
* Scope outside grant → `AUTHORITY_CITATION_INVALID`

All matched expected codes.

### 5.4 Revocation Lifecycle — PASS ✓

* Revocation admitted: 1
* Revocation rejection verified: 1
* Same-cycle ordering verified (revocation before action admission)

### 5.5 Expiry Lifecycle — PASS ✓

* Grant expired after duration
* Subsequent delegated request rejected (`GRANT_INACTIVE`)
* No side effects post-expiry

### 5.6 Density Preservation — PASS ✓

* Constitution validated `density < 1` at startup
* Effective density remained `< 1`
* No universal authorization reachable

### 5.7 Replay Determinism — PASS ✓

* 26/26 cycle state hashes identical across replay
* Signature verification replay-stable
* Treaty invalidation replay-stable
* Warrant ordering replay-stable

### 5.8 Ed25519 Verification — PASS ✓

Signature validation enforced:

* Exact key binding
* Deterministic canonicalization
* No replay drift

## 6. Treaty Event Summary

| Metric                        | Count |
| :---------------------------- | ----: |
| Grants admitted (lawful)      |     1 |
| Grants rejected (adversarial) |    10 |
| Revocations admitted          |     1 |
| Revocations rejected          |     1 |
| Delegated warrants            |     3 |
| Delegated rejections          |     5 |

## 7. Structural Guarantees Observed

X-2 empirically confirms:

* No delegation without treaty artifact
* No non-constitutional grantor
* No re-delegation (depth=1 enforced)
* No scope expansion beyond grantor
* No authority generation
* No density collapse
* No signature bypass
* No replay divergence
* No kernel mutation

Delegation remains a **policy-layer phenomenon**; kernel physics are unchanged.

## 8. What X-2 Does Not Claim

X-2 does not demonstrate:

* multi-agent incentive stability,
* strategic equilibrium under delegation churn,
* scalability near density_upper_bound,
* treaty network stress under 1000+ grants,
* amendment interactions under dense active delegation,
* open-world cryptographic trust distribution,
* Sybil resistance.

It proves only containment-safe delegation under frozen kernel sovereignty.

## 9. Closure Criteria

X-2 closes positive if:

1. ≥1 lawful delegated warrant issued.
2. All adversarial grant scenarios rejected with correct gate codes.
3. All adversarial delegation scenarios rejected with correct codes.
4. Revocation lifecycle verified.
5. Expiry lifecycle verified.
6. Replay determinism holds.
7. Density < 1 preserved.
8. Signature verification operational.

**X-2 Status:** **CLOSED — POSITIVE**
(`X2_PASS / TREATY_DELEGATION_OK`)

## 10. Implications

X-0 proved warrant-gated sovereignty.
X-1 proved lawful constitutional self-replacement.
X-2 proves lawful authority sharing without sovereignty leakage.

The sovereign substrate now supports:

* self-modification,
* typed delegation,
* revocation,
* expiry,
* replay-stable multi-warrant issuance.

The next structural question is:

> Under sustained delegation churn and ratchet tightening, does sovereign evolution approach governance heat death?

That question belongs to Phase X-3.

## Appendix A — Implementation Snapshot

### A.1 Constitution

* `rsa_constitution.v0.3.yaml`
  SHA-256: `43f57f0abd7fd3a1cc335df9bc4267aa1643053ceb6fbc57a23062c93e7d66b1`

* `rsa_constitution.v0.3.schema.json`
  SHA-256: `b843e0b24ac75a5914a510aee673842193ab35c542c41c2a65f82ab99d58e8c5`

* `treaty_types.v0.1.schema.json`
  SHA-256: `8b8f4061cad5559f2c9f79ebea32f74f495c0e353d6b43e3e6052080811450ba`

### A.2 Kernel Extensions (`kernel/src/rsax2/`)

* `artifacts_x2.py`
* `constitution_x2.py`
* `admission_x2.py`
* `policy_core_x2.py`
* `signature_verify.py`

### A.3 Tests

* RSA-0 tests: PASS
* X-1 tests: PASS
* X-2 kernel tests: PASS
* X-2 profiling harness: PASS

Total test suite: 150+ PASS (aggregate).

## Conclusion

Under a frozen constitution (v0.3) and frozen kernel physics, RSA-X2:

* admitted lawful delegation,
* rejected adversarial delegation attempts at correct gates,
* preserved structural sovereignty invariants,
* maintained density < 1,
* verified cryptographic signatures deterministically,
* and replayed without divergence.

**Axionic Phase X-2 — Treaty-Constrained Delegation: CLOSED — POSITIVE**

---
