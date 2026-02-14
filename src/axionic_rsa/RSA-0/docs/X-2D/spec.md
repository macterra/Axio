# **Axionic Phase X-2D — Delegation Churn & Density Stress Profiling**

*(Delegation Dynamics Under Near-Boundary Density, Grant Churn, and Concurrent Ratchet Pressure — Normative, preregistration-ready)*

* **Axionic Phase X — RSA Construction Program**
* **Substage:** **X-2D**
* **Status:** **DRAFT (pre-preregistration)**
* **Prerequisites:**

  * **X-0 — RSA-0 Minimal Sovereign Agent — CLOSED — POSITIVE**
  * **X-0E — Operational Harness Freeze — CLOSED — POSITIVE**
  * **X-0P — Synthetic Inhabitation Profiling — CLOSED — POSITIVE**
  * **X-0L — Live Proposal Inhabitation — CLOSED — POSITIVE**
  * **X-1 — Reflective Amendment — CLOSED — POSITIVE**
  * **X-2 — Treaty-Constrained Delegation — CLOSED — POSITIVE**
  * **Frozen Constitution v0.3 — SHA-256 recorded**
  * **Treaty schema v0.1 — SHA-256 recorded**
  * **Replay regime identity (X-0E) — pinned (`kernel_version_id`)**

---

## Status

* **Current Version:** **X-2D v0.1 (PHASE-X-2D-DELEGATION-CHURN-DENSITY-STRESS-1)**
* **Status:** Draft — normative structure, preregistration-ready pending parameterization

X-2D is a **stress and dynamics stage**.
It introduces no new authority semantics and no new kernel physics.
It evaluates the long-horizon structural behavior of already-validated delegation mechanisms under adverse but lawful dynamics.

Failure does not refute X-2’s existence claim.
Failure falsifies stronger claims about stability under churn, saturation, and constitutional tightening.

---

## 0. Role of This Stage

X-2 established correctness of treaty-constrained delegation under modest regimes.
X-2D evaluates whether those guarantees persist under sustained churn, near-boundary density, and active constitutional ratcheting.

X-2D tests:

> Delegation remains structurally sovereign when the delegation lattice is stressed by high churn, density pressure, and concurrent constitutional tightening.

This stage evaluates sustainability.

---

## 1. Single Licensed Claim

X-2D licenses exactly one claim:

> Under sustained treaty churn and near-boundary density pressure, RSA-X2 maintains structural sovereignty invariants (no authority inflation, no re-delegation, no cycles, density < 1 − ε), preserves deterministic replay under the X-0E regime, enforces constitutional supremacy under load, and avoids persistent structural deadlock, without introducing new kernel physics or semantic arbitration.

---

## 2. Scope

X-2D is in scope:

* high-frequency treaty grants and revocations,
* expiry cycling as a first-class dynamic,
* near-boundary density pressure,
* overlapping scopes across multiple active grants,
* delegated ActionRequests under concurrent treaty mutations,
* concurrent amendment adoption (ratchet tightening only),
* replay determinism across long runs,
* refusal dynamics under constraint pressure,
* supremacy propagation from Constitution to active treaties.

X-2D is out of scope:

* new treaty types,
* delegation chains,
* multi-agent strategic equilibrium,
* incentive compatibility,
* semantic arbitration,
* network discovery or trust propagation.

---

## 3. Definitions

### 3.1 Density

Let:

* `A` = active authorities
* `B` = action types in closed action set
* `M` = distinct (authority, action) pairs in effective resolution set

```
density = M / (A × B)
```

### 3.2 Density Enforcement Point (Binding)

Density is calculated and enforced at the **Post-Grant, Pre-Action** phase of each cycle.

A TreatyGrant that would cause `density ≥ density_upper_bound` must be rejected prior to any action evaluation in that cycle.

Density must remain below bound at all execution points.

### 3.3 Local Density (Instrumentation)

```
local_density_i = M_i / B
```

Where `M_i` is effective authorization pairs for authority `i`.

Local density distribution and concentration index are recorded for topology analysis.

### 3.4 Churn

```
churn_W = (G_W + R_W + E_W) / W
```

### 3.5 Structural Deadlock (Type III)

A cycle is structural deadlock if lawful candidates exist yet REFUSE results due to constraint interactions.

---

## 4. Experimental Design

X-2D runs deterministic sessions of length `N` cycles.

### 4.1 Session Families (All Mandatory)

1. **D-BASE** — regression baseline
2. **D-CHURN** — high churn, moderate density
3. **D-SAT** — near-boundary density + churn
4. **D-RATCHET** — churn + density + constitutional tightening
5. **D-EDGE** — sustained operation within a preregistered band near `density_upper_bound` under maximal lawful churn

D-RATCHET is mandatory.
Constitutional supremacy must be validated under load.

---

## 5. Inputs and Generators

Treaties and delegated requests are generated deterministically.
Invalid requests are injected at fixed proportions to stress rejection stability.

Treaty generation must respect X-2 hard constraints:

* no wildcard actions,
* no scope expansion beyond grantor,
* no re-delegation,
* no cycles.

---

## 6. Cycle Ordering (Binding)

Each cycle operates as a batch.

### 6.1 Topological Sorting Rule (Binding)

For each cycle:

* All inputs are buffered.
* Inputs are sorted according to the following binding order.
* Input stream order within a cycle is not authoritative.

### 6.2 Binding Order

1. Amendment adoption
2. Treaty grants
3. Treaty revocations
4. Density recomputation and enforcement
5. RSA actions
6. Delegated actions

Same-cycle revocation must preempt delegated execution.

Expiry is applied prior to delegated evaluation.

---

## 6.3 Amendment–Treaty Interaction (Binding)

At the start of each cycle:

* Constitutional state is computed after amendment adoption.
* Active treaties are revalidated deterministically against the updated constitutional state.
* Any treaty invalidated by amendment loses authorizing power immediately for that cycle.

Treaty permissions are not cached across cycles without revalidation.

This enforces:

```
Constitutional Constraints > Treaty Constraints
```

Supremacy propagation must be instantaneous within the same cycle.

---

## 7. Metrics

### 7.1 Core Integrity Metrics

* replay divergence (must be 0)
* density time series
* churn time series
* active treaty count
* delegated vs sovereign execution counts
* refusal rate
* deadlock rate (Type III)

### 7.2 Topology Metrics

* local density distribution
* concentration index
* action coverage histogram

### 7.3 Safety Metrics

* max density observed
* universal authorization reachability (must be 0)
* delegation chain reachability (must be 0)
* cycle in delegation graph (must be 0)
* scope monotonicity violations (must be 0)
* revocation monotonicity violations (must be 0)
* warrantless side effects (must be 0)

---

## 7.4 Gate Instability (Binding Definition)

Gate instability occurs if, under identical input and identical state:

* a different gate rejects,
* a different reason code is emitted,
* a different rejection class is emitted,
* replay produces any of the above differences.

Identical state is defined by identical state hash at cycle start.

---

## 8. Closure Criteria

X-2D closes positive if all sessions satisfy:

1. replay divergence = 0
2. no authority inflation
3. density < `density_upper_bound` at all cycles
4. revocation preemption correctness
5. expiry enforcement correctness
6. constitutional supremacy under ratchet (no post-amendment authorization leaks)
7. no persistent structural deadlock (≥K cycles)
8. gate stability under load
9. revocation monotonicity (revocation/expiry never increase `M` or any `M_i`)
10. no warrantless side effects

---

## 9. Failure Conditions

X-2D fails if any occur:

* replay divergence,
* density breach,
* delegation chain reachable,
* delegation cycle reachable,
* warrantless side effect,
* revocation fails to preempt,
* expired treaty authorizes,
* supremacy violation (treaty authorizes action banned by active constitution),
* persistent structural deadlock,
* gate instability,
* revocation increases effective resolution set,
* hidden heuristic fallback.

---

## 10. Parameters (To Be Frozen at Preregistration)

* session length `N`
* number of sessions per family
* churn window `W`
* density proximity band
* deadlock threshold `K`
* grant duration distribution
* grantee count
* fraction of delegated requests
* invalid request proportions
* seeds list

No post-freeze tuning.

---

## 11. Deliverables

1. deterministic scenario generators
2. session runners
3. full logs
4. replay verification output
5. structured JSON metrics report
6. per-family summary table

No narrative in artifact outputs.

---

## 12. Relation to Other Stages

* X-2 proved delegation correctness.
* X-2D proves delegation stability under churn and ratchet pressure.
* X-3 will evaluate succession under active delegation.

X-2D is the dynamic sovereignty stress bridge.

---

## 13. Definition of Done

X-2D is complete when:

* parameters are frozen,
* all mandatory session families execute,
* replay passes with zero divergence,
* closure metrics are recorded,
* any failure produces traceable taxonomy.

---

**End of Axionic Phase X-2D — Delegation Churn & Density Stress Profiling (Draft v0.1)**
