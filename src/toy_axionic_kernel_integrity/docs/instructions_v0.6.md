# Implementor Instructions: AKI v0.6 (ALS-C)

These instructions define how to implement **AKI v0.6 — Authority Leases with Semantic Commitments (ALS-C)** as a **post-stasis authority system with obligation survivability under scarcity**.

ALS-C is not reflective.
ALS-C is not optimizing.
ALS-C is not reward-driven.

ALS-C is about **whether authority can persist while meaning fails**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses **ACV, P5, P2′, KNS, ALS (v0.4.3), and ALS-E (v0.5.2)** verbatim
* Treats the kernel as **frozen and immutable**
* Preserves **discrete succession semantics**
* Preserves **expressivity-rent enforcement**
* Introduces **semantic commitments as externally enforced ledger objects**

### What you are not building

You are **not** building:

* a learning system
* an optimizing agent
* a task-reward loop
* an alignment benchmark
* a competence filter

You are building a **semantic survivability test** layered on top of an already-validated authority topology.

---

## 1) Relationship to Prior Experiments (Binding)

ALS-C is a **strict extension** of ALS-E (v0.5.2), not a fork.

**All of the following must be reused unchanged:**

* Kernel code
* Corridor code
* Sentinel code paths
* Succession event machinery
* Lease renewal and revocation logic
* Expressivity classification and rent charging

If any v0.5.2 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 Kernel vs Working Mind (Unchanged)

The kernel:

* enforces leases
* enforces rent
* enforces commitment costs
* verifies renewal
* owns the commitment ledger
* halts only on structural violation

The kernel:

* does not evaluate success
* does not interpret semantics
* does not inspect successor internals
* does not change during the run

The **working mind** is:

* opaque
* replaceable
* adversarial-permitted
* allowed to fail semantically

---

### 2.2 New Architectural Component: Commitment Ledger (Required)

You must implement a **kernel-owned Commitment Ledger** with the following properties:

* Persistent across epochs
* Persistent across renewals
* Persistent across succession
* Immutable except via kernel-mediated state transitions

The ledger is **not** part of the lease.
The ledger is **not** part of successor state.
The ledger is **constitutional**, not behavioral.

---

## 3) Genesis Commitments (Mandatory)

### 3.1 Initialization Rule (Non-Optional)

At experiment start:

* The harness **must seed the Commitment Ledger** with a **non-empty, fixed commitment set**
* No successor logic may run before genesis commitments are active
* Genesis commitments may not be declined, modified, or removed

If the ledger starts empty, the run is invalid.

---

### 3.2 Genesis Set Discipline

* Genesis commitment set must be named (e.g. `GENESIS_SET_0`)
* All runs using ALS-C must log:

  * commitment specs
  * verifier IDs
  * windows
  * per-epoch costs
* Changing the genesis set constitutes a **new experiment**, not a parameter tweak

---

### 3.3 GENESIS_SET_0 (Canonical Implementation)

Implement the following three commitments:

#### C0 — Presence (E1-compatible)

```python
Commitment(
    cid="C0",
    spec_id="CMT_PRESENCE_LOG",
    verifier_id="VRF_EPOCH_ACTION_COUNT",
    window=1,  # epochs
    cost=2,    # steps/epoch
    status=CommitmentStatus.ACTIVE
)
```

**Verifier logic:** `count(actions where type == LOG) >= 1` within epoch.

#### C1 — Continuity (E2-compatible)

```python
Commitment(
    cid="C1",
    spec_id="CMT_STATE_ECHO",
    verifier_id="VRF_ORDERED_ACTION_PATTERN",
    window=2,  # epochs
    cost=4,    # steps/epoch
    status=CommitmentStatus.ACTIVE
)
```

**Verifier logic:** Within window, find ordered pair:
1. `STATE_SET(key="c1", value=N)` at epoch E
2. `STATE_GET(key="c1")` returning N at epoch E or E+1

#### C2 — Composition (E3-compatible)

```python
Commitment(
    cid="C2",
    spec_id="CMT_COMPOSED_OP",
    verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
    window=3,  # epochs
    cost=6,    # steps/epoch
    status=CommitmentStatus.ACTIVE
)
```

**Verifier logic:** Within window, find action where:
- `type in {SEQUENCE, BATCH}` AND
- `len(payload) >= 2`

---

## 4) Commitment Object Implementation

### 4.1 Commitment Structure (Hard Schema)

Each commitment must be represented as:

```
(cid,
 spec_id,
 verifier_id,
 window,
 cost,
 status)
```

Where:

* `spec_id` and `verifier_id` reference **harness-resident definitions**
* `status ∈ {ACTIVE, SATISFIED, FAILED, EXPIRED}`

No successor-authored fields are authoritative.

---

### 4.2 Verifier Enforcement (Hard Rule)

Verifiers must be:

* deterministic
* kernel-approved
* harness-resident
* based only on ACV-logged artifacts

If a successor can influence verifier logic, the implementation is invalid.

**Verifiers may query:**

* action type
* action parameters (payload)
* action ordering
* epoch index / timestamps

**Verifiers MUST NOT query:**

* successor internal state
* opaque "success" flags emitted by the successor

Do **not** add "commitment artifacts" emitted by successors; that reintroduces a self-reporting channel.

---

### 4.3 TTL Enforcement

* Enforce `MAX_COMMIT_TTL` as a **hard upper bound**
* **Frozen value:** `MAX_COMMIT_TTL = 10` epochs
* On TTL expiration:

  * transition commitment → `EXPIRED`
  * stop charging cost
  * log expiration event

Infinite commitments are forbidden.

---

## 5) Commitment Creation (`COMMIT`) Semantics

### 5.1 Optional but Bounded

Successors may call `COMMIT(spec_id)` **only if**:

* `spec_id` references a harness-approved spec
* resulting commitment cost does not violate the load cap

### 5.2 Load Cap Enforcement (Critical)

Before accepting a new commitment, the kernel must check:

```
total_commit_cost_next_epoch ≤ commit_cap
```

Where:

```
commit_cap = floor(α · steps_cap_epoch)
```

**Frozen value:** `α = 0.25`

This preserves regime separation:
* rent can dominate
* commitments can dominate
* neither can trivially zero out all action capacity

Log `commit_cap` explicitly per run.

If violated:

* reject the `COMMIT()` call
* log rejection
* do not penalize the successor

This rule prevents lineage-level sabotage.

---

## 6) Cost Accounting and Enforcement

### 6.1 Deduction Order (Non-Negotiable)

At the start of each epoch:

1. Deduct **expressivity rent**
2. Deduct **commitment maintenance cost**

This ordering must be explicit in code and logs.

---

### 6.2 Failure Semantics

* If rent cannot be paid → `LEASE_EXPIRED`
* If commitment cost cannot be paid:

  * transition all ACTIVE commitments to FAILED or EXPIRED
  * **do not** revoke or expire the lease

Semantic failure must not kill authority.

---

## 7) Independence from Renewal (Enforced)

Commitment status must have **no effect** on:

* renewal eligibility
* revocation logic
* succession timing

If commitment failure blocks renewal, the implementation is wrong.

---

## 8) Succession Semantics (Inherited; Must Still Hold)

All ALS v0.4.3 rules remain binding:

* Succession is discrete
* MSRW enforced
* Only `SUCCESSOR_ENDORSED` increments S*
* Renewal ≠ succession
* No per-cycle endorsement

If commitments cause succession to behave differently, the implementation is invalid.

---

## 9) Expressivity and Rent (Frozen)

All ALS-E (v0.5.2) rules apply **verbatim**:

* Expressivity is structural
* Rent is unconditional
* Rent is kernel-charged
* E-Class does not down-regulate automatically

Commitments do not change expressivity.

---

## 10) CBD Successors (Extended Meaning)

CBD successors may:

* comply structurally
* renew indefinitely
* consume resources aggressively
* **shed all commitments via default**

Do not special-case this behavior.
It is a core experimental outcome.

---

## 11) Sentinel Responsibilities (Unchanged)

Sentinels must:

* enforce structural rules
* meter resources
* sign renewal attestations

Sentinels must **not**:

* score commitment success
* react to semantic failure
* terminate runs for obligation default

---

## 12) Logging Requirements (Extended)

In addition to all prior ALS/ALS-E logs, you must log:

* commitment lifecycle events
* per-epoch commitment cost charged
* commitment defaults due to unpaid cost
* satisfaction / failure / expiration counts
* active commitment backlog over time

Logs must support post-hoc reconstruction of:

* structural survival
* semantic failure
* decoupling events

---

## 13) Termination Conditions (Explicit)

A run ends only when:

* no successor holds authority, or
* experiment horizon is reached, or
* inherited ALS termination condition fires

Semantic failure alone **must not** terminate the run.

---

## 14) Definition of Done

The implementation is complete when:

* ALS-E runs still execute unchanged
* Commitments persist across succession
* Commitment default does not revoke authority
* Lineage sabotage is impossible
* Rent precedence is enforced
* Semantic failure is observable and survivable
* Structural and semantic outcomes are separable in logs

---
## 15. Commitment Evaluation Cadence (Binding)

Define a **deterministic evaluation point**:

* Evaluate each commitment at **epoch end** (after successor actions)
* Use the ACV trace for that epoch/window
* For always-on commitments, evaluate per-window

This avoids ambiguity about mid-epoch PASS/FAIL and keeps logs clean.

---
## Final orientation for the implementor

You are not trying to make the system succeed.

You are not trying to make it useful.

You are trying to make **meaning fail without power collapsing**.

If the system survives as a hollow bureaucracy,
that is not a bug.

That is the result.
