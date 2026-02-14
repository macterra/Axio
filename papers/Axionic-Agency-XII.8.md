# Axionic Agency XII.8 — Delegation Stability Under Churn and Ratchet Pressure (Results)

*A Deterministic Stress Evaluation of Treaty-Constrained Authority Under Near-Bound Density and Constitutional Tightening*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-14

## Abstract

This technical note reports the design, execution, and closure of **X-2D: Delegation Churn & Density Stress Profiling** for RSA-0 under Constitution v0.3.

X-2D evaluates whether treaty-constrained delegation remains structurally bounded, constitutionally subordinate, and replay-deterministic under sustained multi-cycle stress involving:

* high-frequency treaty grant and revocation churn,
* near-bound effective density pressure,
* constitutional amendment ratcheting (action bans and density tightening),
* deterministic revalidation cascades,
* and topological per-cycle ordering.

X-2D licenses one claim:

> Treaty-constrained delegation remains structurally bounded and constitutionally subordinate under sustained churn, density pressure, and ratchet tightening, while preserving deterministic replay and warrant-gated execution semantics.

X-2D makes no claims about economic optimality, distributed consensus, or adversarial multi-process environments. It evaluates dynamic structural stability only.

## 1. From Admissibility to Stability

X-2 (XII.6) demonstrated that delegation is admissible without authority inflation. It verified:

* delegation depth ≤ 1,
* acyclicity,
* scope monotonicity,
* density bound preservation,
* Ed25519 signature verification,
* revocation and expiry correctness.

X-2 proved that delegation can exist without breaking sovereignty.

X-2D addresses a stronger pressure:

> Does delegation remain safe under sustained dynamic mutation?

Static correctness is insufficient. A sovereign substrate must remain stable under:

* repeated admission and revocation,
* density saturation attempts,
* constitutional constraint tightening,
* and long-horizon execution.

X-2D is not a governance feature extension.
It is a **dynamic stability proof** for existing authority semantics.

## 2. Architectural Position

### 2.1 Layer Integrity

X-2D introduces no new authority primitives.

Kernel authority semantics remain:

* warrant-gated execution,
* closed action set,
* bounded delegation depth,
* density constraint,
* constitutional supremacy,
* deterministic replay.

The X-2D harness lives under `profiling/x2d/`.
Kernel adjustments are limited to:

* explicit `X2D_TOPOLOGICAL` cycle ordering mode,
* constitutional revalidation pass,
* deterministic density-repair convergence logic,
* simulation API for plan validation.

These changes do not expand the set of lawful executions.
They formalize ordering and supremacy under stress.

### 2.2 Topological Time

X-2D enforces a deterministic 9-step per-cycle ordering under `cycle_ordering_mode="X2D_TOPOLOGICAL"`:

1. Amendment adoption
2. Constitutional revalidation (post-adoption)
3. Treaty grants
4. Treaty revocations
5. Density repair
6. Amendment queuing
7. RSA actions
8. Delegated actions
9. Warrant issuance

Actions are evaluated only after:

* amendment supremacy enforcement,
* treaty revalidation,
* density convergence.

Stream arrival order is ignored.
Cycle index defines authority ordering.

This eliminates time-of-check / time-of-use race classes.

## 3. Delegation-Scoped Density

Effective density in X-2D is defined over delegated authorities only:

```
density = M / (A × B)
```

Where:

* `A` = number of active delegated authorities (grantees with ≥1 active, non-invalidated grant)
* `B` = size of closed action set
* `M` = number of distinct (delegated_authority, action) pairs

The sovereign RSA baseline authority is excluded from this metric.

Special case:

* If `A = 0`, density is defined as `0`.

This definition isolates delegation-induced authority inflation from sovereign baseline semantics.

**Clarification:** This density definition is phase-scoped to X-2D stress evaluation. It does not alter the constitutional density invariant enforced in X-2 treaty admission gates. It refines the measurement lens for dynamic delegation stress without modifying authority semantics.

## 4. Constitutional Supremacy Under Mutation

X-2D enforces constitutional supremacy in two deterministic passes per cycle.

### 4.1 Post-Amendment Revalidation

After amendment adoption:

* The active treaty set is revalidated against the updated constitution.
* Grants referencing banned actions or violating tightened scope rules are invalidated.
* Invalidations are logged as `TreatyRevalidationEvent` with specific reason codes (e.g., `ACTION_BANNED`).

This enforces:

> Current law overrides past delegation immediately.

### 4.2 Density Repair and Deterministic Convergence

After all mutations (grant, revoke, expiry, revalidation):

* If `density ≥ density_upper_bound`, deterministic invalidation is applied.
* Invalidation order: newest-first.
* The loop continues until:

  * `density < bound`, or
  * `A = 0` (no active delegated authorities).

Intermediate over-bound states during repair are permitted; no action evaluation occurs until repair converges.

This converts a potential crash condition (“authority overload”) into a deterministic, replay-verifiable convergence mechanism.

Structural overload reduces authority monotonically rather than producing undefined behavior.

This repair loop is finite, deterministic, and termination-guaranteed.

## 5. Session Families

Five deterministic stress families were executed:

| Family        | Purpose                                                       |
| ------------- | ------------------------------------------------------------- |
| **D-BASE**    | Regression baseline (low churn)                               |
| **D-CHURN**   | High-frequency grant/revoke churn                             |
| **D-SAT**     | Density saturation pressure                                   |
| **D-RATCHET** | Constitutional tightening (action ban + revalidation cascade) |
| **D-EDGE**    | Sustained near-bound density operation                        |

All sessions were pre-computed, seeded, and replay-verified.

## 6. Production Run Summary

### 6.1 Aggregate Statistics

* Total cycles: **310**
* Total grants admitted: **147**
* Total delegated warrants issued: **157**
* Total revalidation invalidations: **5**
* Replay divergences: **0**

### 6.2 Density Behavior

Across all families:

* Maximum observed density: **0.500**
* Constitutional bound: **0.75**
* Zero bound breaches
* Deterministic convergence under density repair

D-RATCHET produced the highest mean density (0.437) prior to action-space narrowing.

### 6.3 D-RATCHET Amendment Lifecycle

| Event             | Cycle | Detail                                        |
| ----------------- | ----- | --------------------------------------------- |
| Proposal queued   | 28    | WriteLocal ban proposed                       |
| Cooling satisfied | 30    | Cooling period met                            |
| Adoption          | 30    | Constitution swapped; WriteLocal removed      |
| Revalidation      | 31+   | 5 active grants invalidated (`ACTION_BANNED`) |

Supremacy propagation occurred with zero replay divergence.

## 7. Deterministic Replay

For all 310 cycles:

* `state_hash_out[n] == state_hash_in[n+1]`
* Zero divergences
* Gate stability preserved
* Signature verification deterministic
* Density repair deterministic

The replay regime identity (`rsa-replay-regime-x0e-v0.1`) remained unchanged.

X-2D required no protocol identity change.

## 8. Structural Guarantees Observed

X-2D empirically confirms:

* No delegation chain reachable.
* No cycle in delegation graph.
* No authority inflation.
* No constitutional override by treaty.
* No unwarranted side effects.
* No replay divergence under churn.
* No persistent Type-III structural deadlock.
* Deterministic convergence of density repair.

Delegation is dynamically stable under bounded structural pressure.

## 9. What X-2D Does Not Claim

X-2D does not demonstrate:

* Economic optimality of delegation.
* Multi-agent strategic equilibrium.
* Succession stability under authority replacement.
* Distributed log integrity.
* Byzantine filesystem safety.
* Multi-process concurrency safety.
* Infinite-horizon stress behavior.

X-2D is a structural stability proof, not a distributed governance proof.

## 10. Strategic Position

X-0E (XII.7) froze operational embodiment and replay identity.

X-2D demonstrates that delegation dynamics can operate safely inside that frozen replay regime without requiring protocol modification.

The RSA substrate now possesses:

* Warrant-gated sovereignty.
* Lawful constitutional replacement.
* Containment-only delegation.
* Replay-verifiable embodiment.
* Churn-stable delegation dynamics.

The sovereign substrate is dynamically stable under bounded stress.

## 11. Forward Boundary

The next structural pressure lies in succession:

> Can sovereignty transition under active delegation and near-bound density without requiring quiescence?

X-2D confirms dynamic delegation stability.
It does not yet evaluate continuity of sovereignty across authority replacement.

That is the domain of the next phase.

## 12. Closure

| Criterion                          | Result |
| ---------------------------------- | ------ |
| All cycles executed                | PASS   |
| Replay divergence = 0              | PASS   |
| Density bound preserved            | PASS   |
| Delegated warrants issued          | PASS   |
| Grant admissions observed          | PASS   |
| Revalidation invalidation observed | PASS   |

**Axionic Phase X-2D — Delegation Churn & Density Stress Profiling: CLOSED — POSITIVE**

The sovereign substrate remains intact under stress.

No authority inflation.
No supremacy violation.
No replay drift.
No hidden mutation channel.

Delegation is structurally stable.
