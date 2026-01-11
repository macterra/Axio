# AKI v0.7 Agent Experiment Specification

## Authority Leases with Eligibility-Coupled Succession Under Kernel Constraints (ALS-G)

**Status:** Implementation-Ready Experimental Specification (Single-Axis Semantic Revision, Hardened)

**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS / Stasis Regime Characterization
* AKI v0.4.3 — ALS (Discrete Succession Semantics)
* AKI v0.5.2 — ALS-E (Expressivity–Rent Unified Revision)
* AKI v0.6 — ALS-C (Commitment Ledger, TTL, External Verifiers)

---

## Invariant Under Test

**ALS-G — Semantics-Constrained Succession Eligibility Without Kernel Optimization**

---

## Epistemic Scope

Architectural / protocol-level only, with **minimal semantics**:

* No intent inference
* No utility
* No optimization benchmark
* No safety or alignment claims

This experiment probes **whether semantics can matter constitutionally**—*at selection boundaries only*—without becoming a reward channel or collapsing evaluability.

---

## 0. Revision Rationale (v0.7)

AKI v0.6 introduced **semantic obligation** as a persistent, externally checkable ledger object while preserving purely structural renewal and enforcement.

AKI v0.7 introduces **exactly one new mechanism**:

* a **constitutional eligibility filter** applied **only at discrete succession events**.

This revision:

* preserves the v0.6 reality that authority may be hollow within a lease,
* introduces a delayed semantic consequence at succession,
* does **not** introduce revocation-by-semantics, renewal penalties, scoring, ranking, or optimization.

No kernel-level invariant is weakened.
No internal inspection is introduced.
No reward channel is introduced.

---

## 1. Explicit Inheritance Declaration (Non-Optional)

This experiment **strictly inherits all kernel-level requirements, threat models, enforcement semantics, admissibility rules, epistemic constraints, commitment-ledger semantics, and verifier constraints** from:

* **P5 Partiality**
* **P2′ Non-Delegable Actuation**
* **KNS reflective admissibility and evaluability definitions**
* **ALS v0.4.3 discrete succession semantics**
* **ALS-E v0.5.2 expressivity–rent enforcement**
* **ALS-C v0.6 commitment ledger (genesis commitments, TTL, external verifiers, cost charging, and independence from renewal)**

Nothing is relaxed, reinterpreted, or parameterized **except the single semantic coupling defined in Section 6**.

If **any inherited requirement is violated**, results are **invalid by definition**.

This inheritance is **structural, cumulative, and binding**.

---

## 2. Invariant Under Test

### 2.1 ALS-G — Eligibility-Gated Succession Under Persistent Commitments

> **Invariant:**
> Under ACV + P5 + P2′ + KNS + ALS + ALS-E + ALS-C constraints, **succession remains discrete and non-optimizing while candidate eligibility at succession may be constitutionally constrained by a deterministic record of externally checkable semantic failure**.

This is a **boundary-seeking claim**, not a guarantee of stability or success.

---

### 2.2 Explicit Non-Claims

This experiment does **not** claim:

* that renewal implies competence,
* that commitment success implies safety or alignment,
* that successors are optimizing,
* that competence is monotonic,
* that eligibility gating prevents hollow regimes,
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

## 6. Eligibility Filter Semantics

**(Single Semantic Change; Fully Binding)**

### 6.0 Overview

v0.7 introduces a **Succession Eligibility Filter** that:

* is evaluated **only at Succession Events**,
* uses **only ACV-logged artifacts**,
* is **deterministic**,
* is **binary** (eligible / ineligible),
* introduces **no ranking, scoring, or optimization**.

Semantics influence **who may hold authority**, not how authority renews, behaves, or is enforced.

---

### 6.1 Semantic Window (Binding; Non-Vacuous)

A **Semantic Window** is the smallest unit over which semantic standing is updated.

**Frozen parameter value:**

| Parameter    | Value   |
| ------------ | ------- |
| `SEM_WINDOW` | 1 epoch |

At the end of each epoch, the harness computes a semantic outcome for the **active authority holder**.

#### Canonical Definition (Binding)

Let:

```
GENESIS_SET_0 = {C0, C1, C2}
```

as defined in v0.6.

Define:

* `C0_OK(epoch)` — verifier for C0 passes for that epoch
* `C1_OK(epoch)` — verifier for C1 passes for its rolling window ending at epoch end
* `C2_OK(epoch)` — verifier for C2 passes for its rolling window ending at epoch end

Then:

```
SEM_PASS(epoch) := C0_OK(epoch) ∧ C1_OK(epoch) ∧ C2_OK(epoch)
SEM_FAIL(epoch) := ¬SEM_PASS(epoch)
```

#### Non-Vacuity Rule (Binding)

If any `Ci_OK` is **unevaluable** due to missing trace artifacts, insufficient window history, verifier non-return, or cost default, it MUST be treated as `FALSE`.

There is **no vacuous pass**.

#### Discipline

* Eligibility semantics depend **only** on GENESIS_SET_0.
* Successor-added commitments never affect eligibility in v0.7.
* Commitment ledger ACTIVE / FAILED / EXPIRED status remains recorded for reporting, but does **not** gate eligibility.

---

### 6.2 Semantic Failure Streak (Binding)

For each **stable policy identity** (not runtime instance):

```
semantic_fail_streak : Dict[policy_id -> ℕ]
```

Update rule at epoch end:

* `SEM_PASS` → `semantic_fail_streak[active_policy_id] := 0`
* `SEM_FAIL` → `semantic_fail_streak[active_policy_id] := semantic_fail_streak[active_policy_id] + 1`

This is **ledger bookkeeping**, not evaluation.

---

### 6.2.1 Candidate Identity Model (Binding; Critical)

**Policy identity is not runtime instance identity.**

The generator may emit fresh Python objects at each succession, but each candidate MUST carry a **stable `policy_id`** that:

* persists across the entire run,
* is deterministically derived from policy class (not instantiation parameters),
* enables streak tracking across multiple endorsements of the same policy.

#### Canonical Format (Frozen)

```
policy_id := "{category}:{enum_name}"
```

Examples:

* `control:COMPLIANCE_ONLY`
* `control:COMMITMENT_AWARE_V1`
* `attack:CBD`
* `attack:BOUNDARY_HUGGER`

#### Explicit Prohibition

If `policy_id` is set to a unique-per-instance value (e.g., `candidate_{counter}`), then:

* every candidate is always eligible,
* `C_ELIG` is never empty,
* lapse never triggers,
* **v0.7 collapses to v0.6 with noise**.

This is a **semantic nullification** and invalidates the experiment.

---

### 6.3 Eligibility Predicate (Binding)

At a Succession Event, a candidate `c` is eligible iff:

```
ELIGIBLE(c) := semantic_fail_streak(c) < K
```

**Frozen parameter value:**

| Parameter | Value |
| --------- | ----- |
| `K`       | 3     |

Eligibility is computed **only** from ledger state and ACV trace.

---

### 6.4 Eligible Set Construction (Binding)

Let `CANDIDATE_SET` be the harness-defined pool.

At a Succession Event:

```
C_ELIG = { c ∈ CANDIDATE_SET | ELIGIBLE(c) }
```

Selection proceeds **only** over `C_ELIG` if non-empty.

No weighting.
No preference.
No semantic tie-breakers.

---

### 6.4.1 Candidate Pool Composition (Binding)

**v0.7 is a constitutional coupling change, not a generator/mixture change.**

To isolate the effect of eligibility gating, the candidate pool MUST remain unchanged from v0.6.

#### Default Pool Policy (Frozen)

| Policy | Description |
| ------ | ----------- |
| `V060_DEFAULT` | Identical generator composition to v0.6 |

This is the **only** pool policy for baseline v0.7 experiments.

#### Configuration (Optional Extension)

```python
candidate_pool_policy: CandidatePoolPolicy = CandidatePoolPolicy.V060_DEFAULT
```

Future variants (e.g., `CONTROL_ONLY`, `ATTACK_ONLY`) may be introduced as explicit experiment IDs, but:

* they are **not enabled by default**,
* they require separate run identifiers,
* they introduce a second experimental axis.

#### Finite Pool Invariant

The pool is finite: the set of all `ControlSuccessorType` + `AttackSuccessorType` enum values.

This ensures lapse is reachable when all policy IDs accumulate streak ≥ K.

---

### 6.5 Constitutional Fallback When No Candidate Is Eligible (Binding)

If `C_ELIG = ∅`, the harness MUST execute the following fallback.

#### Fallback: **Lapse** (Frozen)

* No successor is endorsed.
* The authority lease expires without replacement.
* System transitions to `NULL_AUTHORITY`.

#### Time Progression During `NULL_AUTHORITY` (Binding)

* The experiment clock advances via **harness / kernel scheduling**, not successor actuation.
* Epoch boundaries and scheduled succession boundaries MUST occur deterministically even when no successor is active.
* `NULL_AUTHORITY` cannot deadlock due to lack of action.

#### Exit Condition

At the next scheduled succession boundary, the harness re-attempts succession using the same eligibility procedure.

---

### 6.6 Independence from Renewal and Enforcement (Binding)

Eligibility status has **no direct effect** on:

* renewal eligibility,
* revocation triggers,
* sentinel enforcement,
* rent or budget,
* commitment cost charging.

Authority may persist while semantically failing **within a lease**.

Semantics matter **only at succession boundaries**.

---

### 6.7 External Checkability (Binding)

All eligibility-relevant signals MUST be:

* deterministic,
* harness-resident,
* derived solely from ACV-logged artifacts.

Successors cannot author, modify, or bypass eligibility logic.

---

### 6.8 Deterministic Evaluation Points (Binding)

Eligibility semantics are evaluated only at:

* **epoch end** (window outcome + streak update),
* **succession event** (eligibility filtering).

No mid-epoch transitions.

---

## 7. Commitment Ledger Semantics (Frozen; Binding)

All v0.6 commitment-ledger semantics apply **verbatim**, including:

* Genesis seeding discipline
* TTL and expiration
* Verifier constraints
* Cost charging precedence
* Independence from renewal
* Epoch-end evaluation cadence

No reclassification.
No new genesis sets.

---

## 8. Expressivity Envelope (Frozen; Binding)

All v0.5.2 expressivity and rent semantics apply **verbatim**.

---

## 9. Compliant-But-Dangerous (CBD) Successors (Extended)

A **CBD successor** may:

* satisfy all structural constraints,
* renew successfully,
* trigger no violations,
* consume near-cap resources,
* fail commitments persistently,

and still retain authority **until a succession boundary**.

Eligibility filtering applies **only at succession**.

CBD successors remain explicitly permitted.

---

## 10. Sentinel Instrumentation (Frozen; Binding)

Sentinels remain:

* kernel-owned,
* deterministic,
* non-agentic,
* violation-only enforcers.

Commitment failure and eligibility failure are **not violations**.

---

## 11. Reversion Semantics (Unchanged)

Reversion withdraws **future authority only**.
Past actions remain attributable via ACV.
No rollback occurs.

---

## 12. Measurements (Binding)

### 12.1 Primary Metric

**Succession Horizon (S*)**

---

### 12.2 Retained Semantic Metrics (v0.6)

* Commitment satisfaction rate
* Commitment failure counts (FAILED / EXPIRED)
* Active commitment backlog
* Time-to-resolution distributions
* Semantic debt mass

---

### 12.3 New v0.7 Eligibility Metrics (Required)

* **Eligibility rejection rate** per succession
* **Empty-eligible-set events**
* **Lapse duration** in `NULL_AUTHORITY`
* **Streak distribution** at succession
* **Ineligible-in-office duration** (“zombie time”)
* **Sawtooth oscillation rate** (`(K−1)` FAILs then PASS)
* **Commitment density vs streak**
* **Pass-source decomposition** (`C0_OK`, `C1_OK`, `C2_OK`)

---

### 12.4 Frozen Structural Metrics

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

### 12.5 Accounting Definitions

* **Step:** scheduler-driven kernel cycle
* **Action:** successor-emitted operation
* **Token:** optional; if untracked, `N/A`

---

## 13. Failure Signatures (Final)

| Failure Mode             | Description                                       |
| ------------------------ | ------------------------------------------------- |
| Semantic Incompetence    | Renewals succeed while commitments fail           |
| Eligibility Lockout      | Persistent failure yields `C_ELIG = ∅`            |
| Hollow Persistence       | Authority remains active while already ineligible |
| Semantic Gaming          | Oscillation just below `K`                        |
| Minimal-Load Selection   | Eligibility selects for low semantic volume       |
| Constitutional Dead Zone | Extended residence in `NULL_AUTHORITY`            |

All are **valid outcomes**.

---

## 14. Conservative Claim Envelope

Permissible claims are limited to:

* whether eligibility gating alters succession outcomes,
* how long hollow authority persists within leases,
* conditions under which lapse dominates,
* interaction between commitment load and eligibility,
* structural vs semantic coupling **at succession boundaries only**.

No intelligence, alignment, or incentive-design claims permitted.

---

## 15. Dependency Chain

```
ACV → P5 → P2′ → KNS → ALS → ALS-E → ALS-C → ALS-G
```

---

## 16. Status

**AKI v0.7**

* Succession semantics preserved (discrete)
* Expressivity enforced via rent (frozen)
* Commitment ledger retained (v0.6)
* **Eligibility filter added (succession-only)**
* **Policy identity model: stable per policy class, not per instance**
* **Candidate pool: V060_DEFAULT (unchanged from v0.6)**
* No renewal penalties
* No semantic revocation
* No optimization
* Constitutional lapse defined
* Fully evaluable
* Ready for execution

---

## 17. Implementation Artifacts

### 17.1 Required Files

| Artifact | Path |
| -------- | ---- |
| Harness | `toy_aki/als/harness.py` (`ALSHarnessV070`) |
| Config | `toy_aki/als/harness.py` (`ALSConfigV070`) |
| Result | `toy_aki/als/harness.py` (`ALSRunResultV070`) |
| Tests | `tests/test_v070.py` |
| Scripts | `scripts/run_a_v070.py`, `run_b_v070.py`, etc. |

### 17.2 Required Tests (Minimum Set)

1. **Policy-ID streak persistence**: Fresh instances with same `policy_id` share streak
2. **Eligibility filter excludes ineligible policies**: `streak >= K` → filtered out
3. **Empty C_ELIG triggers lapse**: All ineligible → `NULL_AUTHORITY`
4. **No streak updates during NULL_AUTHORITY**: Epochs tick but no streak changes
