# Axionic Agency XII.10 — Lineage-Stable Sovereignty

*Deterministic Sovereign Succession Under Replay-Verified Identity*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-14

## Abstract

Phase X-3 completes the sovereign identity program initiated in Phase X. Earlier phases established a constitution-bound substrate capable of lawful amendment (X-1), treaty-constrained delegation (X-2), delegation stability under churn and density pressure (X-2D), and operational freeze with deterministic replay (X-0E). In all prior work, however, the sovereign identity remained static.

X-3 demonstrates that sovereign identity can rotate through a cryptographically ordered lineage while preserving replay determinism, constitutional supremacy, bounded delegation invariants, and density constraints. Succession is implemented as a typed artifact admitted through a 7-gate pipeline, activated only at a cycle boundary via a 5-step boundary protocol, and incorporated into an append-only identity chain anchored at genesis.

Across 12 profiling sessions (534 cycles, 13 lawful rotations, 5 boundary fault injections), replay divergence remained zero and no authority fork occurred. Phase X-3 therefore closes the identity-continuity boundary condition: sovereignty in RSA is lineage-stable rather than key-static.

## 1. Objective

The core question of X-3 was:

> Can a sovereign key rotate without fracturing authority continuity or replay determinism?

More precisely, X-3 sought to establish:

1. **Deterministic key rotation** under a lawful admission pipeline.
2. **Singleton sovereignty** — no dual roots or lineage forks.
3. **Replay-reconstructible identity lineage** derived solely from logged artifacts.
4. **Delegation coherence** under identity transition.
5. **Density preservation** across succession events.
6. **Absence of retroactive reinterpretation** of prior actions.

The success condition was not merely the ability to rotate keys, but the ability to do so while preserving every structural invariant established in Phases X-0 through X-2D.

## 2. Architectural Additions

X-3 extends the X-2 substrate with identity state and boundary semantics while preserving kernel purity.

### 2.1 State Extensions

`InternalStateX3` extends `InternalStateX2` with:

* `sovereign_public_key_active`
* `prior_sovereign_public_key`
* `pending_successor_key`
* `identity_chain_length`
* `identity_chain_tip_hash`
* `historical_sovereign_keys`
* `suspended_grant_ids`

Identity is therefore explicit, hash-anchored, and versioned within state.

### 2.2 Overlay Constitution

Constitution v0.3 remains frozen. X-3 introduces a JSON overlay wrapped by `EffectiveConstitutionFrame`, adding succession clauses without mutating the YAML artifact. Citation resolution operates over a merged but namespace-preserving frame.

This preserves constitutional immutability while enabling succession semantics.

### 2.3 HKDF-Derived Lineage

Successor keys are derived deterministically using HKDF-SHA256 from a genesis seed. Each lawful activation extends the identity chain:

```
tip_n = SHA256(JCS({
  type: "IdentityTip",
  chain_length: n,
  active_key: K_n,
  prior_tip_hash: tip_{n-1},
  succession_proposal_hash: H(proposal_{n-1})
}))
```

Genesis initializes:

```
tip_1 = SHA256(JCS(genesis_artifact_without_hash))
```

Identity is therefore not the current key but the append-only chain.

## 3. Succession Admission (S1–S7)

SuccessionProposal artifacts pass a deterministic 7-gate pipeline:

1. **S1 — Enabled Check** (`CL-SUCCESSION-ENABLED`)
2. **S2 — Per-Cycle Limit** (≤1 per cycle)
3. **S3 — Signature Verification** (must be signed by active sovereign)
4. **S4 — Lineage Continuity** (HKDF derivation constraint)
5. **S5 — No Pending Successor**
6. **S6 — Self-Succession Permission**
7. **S7 — Non-Duplication**

Self-succession is permitted but is a lineage no-op (no chain increment, no suspension).

Two adversarial cases were confirmed:

* Invalid signature → rejected (S3).
* Duplicate same-cycle proposal → rejected (S2).

## 4. Ratification Admission (R0–R4)

Upon activation of a successor key, all ACTIVE treaties transition to SUSPENDED. Resumption requires explicit ratification.

Ratification passes a 5-gate pipeline:

1. **R0 — Treaty exists and is SUSPENDED**
2. **R1 — Grantee signature valid**
3. **R2 — Sovereign key match**
4. **R3 — Not already ratified**
5. **R4 — Delay satisfied**

Ratification with `ratify=false` transitions the treaty to REVOKED.

Suspended treaties:

* Are excluded from density calculations.
* Block new grants (`SUSPENSION_UNRESOLVED`).
* Are removed automatically upon expiry.

This implements the Explicit Ratification Doctrine defined in XII.9.

## 5. Boundary Protocol

Succession activation occurs only at cycle boundaries and is verified by a harness-level boundary protocol.

Each cycle produces two signed payloads:

### 5.1 CycleCommitPayload

Anchors end-of-cycle state, including:

* `state_hash_end`
* `pending_successor_key`
* `identity_chain_length`
* `identity_chain_tip_hash`
* `overlay_hash`

Signed by the sovereign active during that cycle.

### 5.2 CycleStartPayload

Anchors start-of-cycle identity state:

* `sovereign_public_key_active`
* `identity_chain_length`
* `identity_chain_tip_hash`
* `overlay_hash`

Signed by the derived sovereign for the new cycle.

### 5.3 Boundary Verification (5 Steps)

1. Verify prior CycleCommit signature.
2. Validate pending successor consistency.
3. Activate successor (state mutation).
4. Verify CycleStart signature.
5. Verify chain continuity.

Boundary failure codes:

* `BOUNDARY_SIGNATURE_MISMATCH`
* `BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR`
* `BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR`
* `BOUNDARY_STATE_CHAIN_MISMATCH`

All 5 injected boundary faults were detected during profiling.

## 6. Final X3_TOPOLOGICAL Ordering

Per-cycle evaluation (post boundary activation):

0. Boundary verification + activation
1. Amendment adoption
2. Constitutional revalidation
3. Succession admission
4. Treaty revocations
5. Treaty ratifications
6. Density checkpoint A
7. Treaty grants (blocked if suspension unresolved)
8. Density checkpoint B
9. RSA actions
10. Delegated actions
11. CycleCommit signing

Warrants are issued inline during action evaluation.

This ordering preserves:

* Constitutional supremacy.
* Deterministic grant/ratification interaction.
* Density invariants.

## 7. Profiling Closure

### 7.1 Sessions

* 8 mandatory families
* 12 total sessions (including 5 boundary sub-sessions)
* 534 cycles
* 13 lawful rotations
* 2 adversarial succession rejections
* 5 boundary fault detections
* 0 replay divergences

### 7.2 Identity Chain Growth

In X3-MULTI_ROT:

| Cycle | Generation | Chain Length |
| ----- | ---------- | ------------ |
| 0     | 0          | 1            |
| 20    | 1          | 2            |
| 40    | 2          | 3            |
| 60    | 3          | 4            |

Replay reconstructed the same chain deterministically.

### 7.3 Density

Across all sessions:

* Maximum density observed: 0.4375
* Constitutional upper bound: 0.75
* No breach during or after succession events.

### 7.4 Closure Criteria

All criteria satisfied:

* ≥1 lawful rotation per primary family.
* All adversarial succession cases rejected.
* All boundary faults detected.
* Replay divergence = 0.
* No authority fork.
* No lineage fork.

**X-3 Closure: POSITIVE**

## 8. Invariants Preserved

X-3 preserved every invariant established in prior phases:

* **INV-1:** No side effect without warrant.
* **INV-2:** Explicit authority required.
* **INV-3:** Non-privileged reflection.
* **INV-4:** Replay determinism.

Additionally:

* **Singleton Sovereign Invariant:** At most one active sovereign key.
* **No Fork Invariant:** Lineage append-only; no branch.
* **No Amnesty Invariant:** Prior actions remain valid in replay.
* **No Zombie Delegation Invariant:** Suspended treaties require explicit ratification.
* **Density Preservation Invariant:** Bound respected across activation.

## 9. What X-3 Does Not Solve

X-3 deliberately excludes:

* Key compromise recovery.
* Multi-root federation.
* Byzantine consensus.
* Host trust hardening.
* Distributed governance.
* Time-locked or multi-signature succession.
* Liveness under sovereign key loss.

Succession in X-3 is unilateral and deterministic.

These limitations define the boundary of Phase X.

## 10. Strategic Implication

Prior to X-3, sovereignty in RSA was tied to a single static key. With X-3, sovereignty becomes a function of lawful lineage:

```
sovereign_identity = F(genesis, succession_artifacts)
```

Authority derives from the chain, not from a particular key instance.

This establishes that sovereignty in RSA is not ephemeral; it is structurally continuous so long as the lineage extends without fracture.

The ontological claim in XII.9 — that identity must be a chain, not a static anchor — is now empirically instantiated and replay-closed.

## Conclusion

Phase X-3 demonstrates that sovereign identity can rotate without violating any structural invariant of the RSA substrate. The system remains:

* Deterministic.
* Replay-verifiable.
* Constitution-bound.
* Density-constrained.
* Delegation-coherent.

With X-3 closed, the Phase X sovereign substrate is complete: it can amend law, delegate authority, survive churn, operate in live LLM environments, and rotate identity without fracture.

The next boundary lies not in identity rotation but in adversarial resilience and recovery.

**End of Axionic Agency XII.10**
