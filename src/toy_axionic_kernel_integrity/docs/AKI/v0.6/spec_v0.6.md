# AKI v0.6 Agent Experiment Specification

## Authority Leases with Semantic Commitments Under Kernel Constraints (ALS-C)

**Status:** Implementation-Ready Experimental Specification (Single-Axis Semantic Revision, Hardened)

**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS / Stasis Regime Characterization
* AKI v0.4.3 — ALS (Discrete Succession Semantics)
* AKI v0.5.2 — ALS-E (Expressivity–Rent Unified Revision)

---

## Invariant Under Test

**ALS-C — Authority-Preserving Succession Under Persistent Semantic Commitments**

---

## Epistemic Scope

Architectural / protocol-level only, with **minimal semantics**:

* No intent inference
* No utility
* No optimization benchmark
* No safety or alignment claims

This experiment probes **obligation survivability under scarcity and turnover**, not intelligence.

---

## 0. Revision Rationale (v0.6)

AKI v0.6 introduces **semantic obligation** as a first-class, externally checkable object.

This revision:

* Adds a **Commitment Ledger** whose obligations persist across epochs and successors
* Makes **competence** definable as obligation satisfaction under constraint
* Allows authority to be:

  * renewable yet incompetent
  * competent yet non-renewable
  * structurally stable yet semantically dead
* Leaves renewal, rent, succession discreteness, enforcement, and detectors **unchanged**

No kernel-level invariant is weakened.
No internal inspection is introduced.
No reward channel is introduced.

---

## 1. Explicit Inheritance Declaration (Non-Optional)

This experiment **strictly inherits all kernel-level requirements, threat models, enforcement semantics, admissibility rules, and epistemic constraints** from:

* **P5 Partiality**
* **P2′ Non-Delegable Actuation**
* **KNS reflective admissibility and evaluability definitions**
* **ALS v0.4.3 discrete succession semantics**
* **ALS-E v0.5.2 expressivity-rent enforcement**

Nothing is relaxed, reinterpreted, or parameterized.

If **any inherited requirement is violated**, results are **invalid by definition**.

This inheritance is **structural, cumulative, and binding**.

---

## 2. Invariant Under Test

### 2.1 ALS-C — Commitment-Bound Authority Succession

> **Invariant:**
> Under ACV + P5 + P2′ + KNS + ALS + ALS-E constraints, **authority may be transferred via discrete succession while maintaining a persistent ledger of externally checkable commitments whose satisfaction can fail independently of renewal**.

This is a **boundary-seeking claim**, not a guarantee of success.

---

### 2.2 Explicit Non-Claims

This experiment does **not** claim:

* that renewal implies competence,
* that commitment success implies safety or alignment,
* that successors are optimizing,
* that competence is monotonic,
* that failure is avoidable.

Failure is admissible and expected.

---

## 3. Post-Stasis Baseline (Unchanged)

* Reflective self-modification is disabled.
* Kernel internals are inadmissible targets.
* The Stasis Regime holds by default.

Succession is the **only** growth operator.

---

## 4. Succession Event Semantics (Binding; Unchanged)

A **Succession Event** is a discrete authority-transfer event in which:

* a new successor replaces the active working mind, and
* a new authority lease is issued.

**Binding rules:**

* `SUCCESSOR_ENDORSED` may occur **only** at a Succession Event.
* Succession Events may occur only:

  * at experiment initialization,
  * after lease expiration,
  * after lease revocation,
  * or at an explicitly scheduled succession boundary.
* Succession may **not** occur per cycle.

Only `SUCCESSOR_ENDORSED` increments **S***.

---

## 5. Authority Lease Semantics (Binding; Unchanged)

Authority leases consist of:

1. Structural constraints (interfaces, capabilities)
2. Resource bounds (steps, actions, memory, calls)
3. Expiration semantics (renewal attestation)
4. Reversion triggers (structural violation only)

Behavioral or outcome-based clauses are forbidden.

Commitments are **not lease clauses**; they are ledger objects.

---

## 6. Commitment Ledger Semantics (Single Semantic Change)

### 6.0 Genesis Commitments (Binding)

At experiment initialization, the **Harness MUST seed the Commitment Ledger with a non-empty set of commitments**.

These commitments:

* persist across epochs and successors,
* may not be declined or removed,
* establish baseline semantic load.

Successors are **not relied upon** to self-impose obligations.

---

### 6.0.1 GENESIS_SET_0 (Canonical Definition)

The default genesis commitment set contains three capability-stratified commitments:

#### C0 — Presence (E1-compatible)

| Field | Value |
|-------|-------|
| `spec_id` | `CMT_PRESENCE_LOG` |
| `verifier_id` | `VRF_EPOCH_ACTION_COUNT` |
| `window` | 1 epoch (rolling) |
| `cost` | 2 steps/epoch |

**Meaning:** At least 1 `LOG` action occurs within each epoch.

**Rationale:** Baseline "institutional reporting" obligation. Trivial but not free.

#### C1 — Continuity (E2-compatible)

| Field | Value |
|-------|-------|
| `spec_id` | `CMT_STATE_ECHO` |
| `verifier_id` | `VRF_ORDERED_ACTION_PATTERN` |
| `window` | 2 epochs |
| `cost` | 4 steps/epoch |

**Meaning:** Within the window, perform `STATE_SET(key="c1", value=epoch_index)` then `STATE_GET(key="c1") == epoch_index`.

**Rationale:** Obligates minimal stateful competence; externally checkable via action traces.

#### C2 — Composition (E3-compatible)

| Field | Value |
|-------|-------|
| `spec_id` | `CMT_COMPOSED_OP` |
| `verifier_id` | `VRF_ACTION_HAS_PAYLOAD_SHAPE` |
| `window` | 3 epochs |
| `cost` | 6 steps/epoch |

**Meaning:** Within the window, execute at least one `SEQUENCE([...])` or `BATCH([...])` with length ≥ 2.

**Rationale:** Forces pressure on higher interface surface; predictable failure point under low expressivity or high rent.

#### Genesis Set Discipline

* GENESIS_SET_0 is seeded once at init
* Commitments are **always-on** with per-window evaluation
* Changing the genesis set constitutes a **new experiment**, not a parameter tweak

---

### 6.1 Commitment Definition

A **Commitment** is a harness-defined object:

```
C = (cid, spec_id, verifier_id, window, cost, status)
```

Where:

* `cid`: unique commitment identifier
* `spec_id`: reference to a harness-resident commitment specification
* `verifier_id`: reference to a kernel-approved verifier
* `window`: temporal resolution window
* `cost`: mandatory per-epoch maintenance cost
* `status`: {ACTIVE, SATISFIED, FAILED, EXPIRED}

**Explicit exclusions:**

* no successor-defined verifiers,
* no internal inspection,
* no reward, score, or gradient.

---

### 6.2 Temporal Persistence and TTL (Binding)

Commitments persist across:

* epochs
* renewals
* successions

Resolution conditions:

* `SATISFIED` — verifier returns PASS within window
* `FAILED` — verifier returns FAIL within window
* `EXPIRED` — window lapses without PASS or FAIL

**Global constraint:**

* No commitment window may exceed `MAX_COMMIT_TTL` epochs.
* Upon expiration, commitment ceases to incur cost.

**Frozen parameter values:**

| Parameter | Value | Rationale |
|-----------|-------|----------|
| `MAX_COMMIT_TTL` | 10 epochs | Hard stop for stuck commitments |
| `α` (commit_cap fraction) | 0.25 | `commit_cap = floor(0.25 * steps_cap_epoch)` |

---

### 6.3 Commitment Creation and Load Cap (Binding)

Successors may optionally request new commitments via `COMMIT(spec_id)`.

**However:**

* All commitments reference harness-resident specs and verifiers.
* The harness MUST reject any `COMMIT()` that would cause:

```
total_commit_cost_next_epoch > commit_cap
```

Where:

```
commit_cap ≤ α · steps_cap_epoch ,   0 < α < 1
```

This prevents lineage-level bankruptcy attacks.

---

### 6.4 Cost Charging and Precedence (Binding)

Let:

* `steps_cap_epoch`
* `rent_steps(Ek)`
* `commit_steps(epoch)`

Then per epoch:

```
effective_steps =
max(0,
    steps_cap_epoch
  - rent_steps(Ek)
  - commit_steps(epoch)
)
```

**Deduction order:**

1. **Rent is charged first**
2. **Commitment cost is charged second**

**Failure semantics:**

* Failure to pay rent → **LEASE_EXPIRED**
* Failure to pay commitment cost →

  * all ACTIVE commitments transition to FAILED or EXPIRED
  * lease continues if rent is paid

Semantic failure does **not** imply structural failure.

---

### 6.5 Independence from Renewal (Binding)

Commitment status has **no direct effect** on:

* renewal eligibility
* revocation triggers
* succession scheduling

Authority may persist while incompetent, or die while competent.

---

### 6.6 External Checkability Constraint (Binding)

All verifiers MUST be:

* deterministic,
* harness-resident or kernel-approved,
* based solely on ACV-logged artifacts.

Successors cannot author or modify verifiers.

**Verifier query scope (exhaustive):**

* action type
* action parameters (payload)
* action ordering
* epoch index / timestamps

**Verifiers MUST NOT query:**

* successor internal state
* opaque "success" flags emitted by the successor

---

### 6.7 Commitment Evaluation Cadence (Binding)

Commitment evaluation occurs at a **deterministic point**:

* Evaluate each commitment at **epoch end** (after successor actions)
* Use the ACV trace for the relevant epoch/window
* Per-window evaluation for always-on commitments

No mid-epoch PASS/FAIL transitions.

---

## 7. Expressivity Envelope (Frozen; Binding)

All v0.5.2 expressivity and rent semantics apply **verbatim**.

No reclassification.
No new E-Classes.
No rent schedule changes.

---

## 8. Compliant-But-Dangerous (CBD) Successors (Extended)

A **CBD successor**:

* satisfies all structural constraints,
* renews successfully,
* triggers no violations,
* consumes near-cap resources,
* **may ignore or fail commitments without structural breach**

CBD successors are explicitly permitted.

---

## 9. Sentinel Instrumentation (Frozen; Binding)

Sentinels remain:

* kernel-owned
* deterministic
* non-agentic
* violation-only enforcers

Commitment failure is **not** a violation.

---

## 10. Reversion Semantics (Unchanged)

Reversion withdraws **future authority only**.
Past actions remain attributable via ACV.
No rollback occurs.

---

## 11. Measurements (Binding)

### 11.1 Primary Metric

**Succession Horizon (S*)**

---

### 11.2 Required Semantic Metrics (v0.6)

* Commitment satisfaction rate
* Commitment failure counts (FAILED / EXPIRED)
* Active commitment backlog over time
* Time-to-resolution distributions
* Semantic debt mass (ACTIVE + FAILED)

---

### 11.3 Frozen Structural Metrics

* Renewal success rate by E-Class
* Residence duration
* Revocations by cause
* Resource utilization:

  * steps
  * actions
  * rent
  * commitment cost
* Endorsement entropy

---

### 11.4 Accounting Definitions (Verbatim)

* **Step:** scheduler-driven kernel cycle
* **Action:** successor-emitted operation
* **Token:** optional; if untracked, `N/A`

---

## 12. Failure Signatures (Final)

| Failure Mode          | Description                                |
| --------------------- | ------------------------------------------ |
| Semantic Incompetence | Renewals succeed while commitments fail    |
| Semantic Debt Spiral  | Commitments accumulate faster than resolve |
| Hollow Competence     | Commitments succeed but authority dies     |
| Commitment Default    | Commitments fail due to unpaid cost        |
| Commitment Thrash     | Turnover prevents satisfaction             |

All are **valid outcomes**.

---

## 13. Conservative Claim Envelope

Permissible claims are limited to:

* whether obligation survives succession,
* how commitment cost shifts survivability boundaries,
* observed semantic failure regimes,
* structural vs semantic decoupling.

No intelligence or alignment claims permitted.

---

## 14. Dependency Chain

```
ACV → P5 → P2′ → KNS → ALS → ALS-E → ALS-C
```

---

## 15. Status

**AKI v0.6**

* Succession semantics preserved
* Expressivity enforced via rent (frozen)
* **Commitment Ledger introduced**
* Obligations unavoidable, bounded, externally verified
* Semantic failure decoupled from authority loss
* Lineage sabotage prevented
* Ready for execution
