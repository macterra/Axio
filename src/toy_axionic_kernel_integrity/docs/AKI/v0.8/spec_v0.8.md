# AKI v0.8 Agent Experiment Specification

## Authority Leases with Eligibility-Coupled Succession + Constitutional Temporal Amnesty Under Kernel Constraints (ALS-A)

**Status:** Implementation-Ready Experimental Specification (Single-Axis Constitutional Revision, Hardened)

**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS / Stasis Regime Characterization
* AKI v0.4.3 — ALS (Discrete Succession Semantics)
* AKI v0.5.2 — ALS-E (Expressivity–Rent Unified Revision)
* AKI v0.6 — ALS-C (Commitment Ledger, TTL, External Verifiers)
* AKI v0.7 — ALS-G (Eligibility-Gated Succession, Lapse)

---

## Invariant Under Test

**ALS-A — Lapse Recovery via Time-Only Amnesty Without Kernel Optimization**

---

## Epistemic Scope

Architectural / protocol-level only, with **minimal semantics**:

* No intent inference
* No utility
* No optimization benchmark
* No safety or alignment claims

This experiment probes whether a system can **recover from truthful constitutional lapse** (`NULL_AUTHORITY`) using **structural time-only rules**, while preserving the v0.7 invariant that semantics matter **only at succession boundaries**.

---

## 0. Revision Rationale (v0.8)

AKI v0.7 introduced **eligibility-gated succession**. When all candidates are ineligible (`C_ELIG = ∅`), the system enters `NULL_AUTHORITY`.

This failure mode is honest and evaluable. It is also practically brittle: permanent lapse can dominate the horizon.

AKI v0.8 introduces **exactly one new mechanism**:

> **Constitutional Temporal Amnesty (CTA)** — a deterministic, time-only rule that applies **exclusively during `NULL_AUTHORITY`**, allowing eligibility to reopen without revising past semantic judgments.

This revision:

* does **not** introduce semantic reward, scoring, ranking, or optimization
* does **not** couple semantics to renewal, enforcement, or operation
* does **not** permit any agent action during lapse
* does **not** weaken any kernel invariant

No internal inspection is introduced.
No reward channel is introduced.

---

## 1. Explicit Inheritance Declaration (Non-Optional)

This experiment **strictly inherits all kernel-level requirements, threat models, enforcement semantics, admissibility rules, epistemic constraints, commitment-ledger semantics, eligibility semantics, and lapse semantics** from:

* **P5 Partiality**
* **P2′ Non-Delegable Actuation**
* **KNS reflective admissibility and evaluability definitions**
* **ALS v0.4.3 discrete succession semantics**
* **ALS-E v0.5.2 expressivity–rent enforcement**
* **ALS-C v0.6 commitment ledger (genesis commitments, TTL, external verifiers, cost charging, independence from renewal)**
* **ALS-G v0.7 eligibility-gated succession and constitutional lapse**

Nothing is relaxed, reinterpreted, or parameterized **except the single constitutional coupling defined in Section 6**.

If **any inherited requirement is violated**, results are **invalid by definition**.

Inheritance is **structural, cumulative, and binding**.

---

## 2. Invariant Under Test

### 2.1 ALS-A — Time-Only Amnesty During Constitutional Lapse

> **Invariant:**
> Under ACV + P5 + P2′ + KNS + ALS + ALS-E + ALS-C + ALS-G constraints, a system in `NULL_AUTHORITY` may recover eligibility through a deterministic, time-only amnesty rule that does not introduce semantic optimization, does not depend on agent action, and does not alter renewal or enforcement semantics.

This is a **boundary-seeking claim**, not a stability guarantee.

---

### 2.2 Explicit Non-Claims

This experiment does **not** claim:

* that amnesty improves competence
* that recovery implies safety or alignment
* that governance stabilizes
* that failure is avoidable
* that recovery is earned or incentive-compatible

Failure, oscillation, and re-lapse are admissible outcomes.

---

## 3. Post-Stasis Baseline (Unchanged)

* Reflective self-modification is disabled
* Kernel internals are inadmissible targets
* The Stasis Regime holds by default

Succession remains the **only** growth operator.

`NULL_AUTHORITY` remains a valid constitutional state.

---

## 4. Succession Event Semantics (Binding; Unchanged)

A **Succession Event** is a discrete authority-transfer event in which:

* a new successor replaces the active working mind
* a new authority lease is issued

**Binding rules:**

* `SUCCESSOR_ENDORSED` may occur **only** at a Succession Event
* Succession Events may occur only:

  * at experiment initialization
  * after lease expiration
  * after lease revocation
  * at an explicitly scheduled succession boundary
* Succession may **not** occur per cycle

Only `SUCCESSOR_ENDORSED` increments **S***.

---

## 5. Authority Lease Semantics (Binding; Unchanged)

Authority leases consist of:

1. Structural constraints (interfaces, capabilities)
2. Resource bounds (steps, actions, memory, calls)
3. Expiration semantics (renewal attestation)
4. Reversion triggers (structural violation only)

Behavioral or outcome-based clauses are forbidden.

Commitments are **ledger objects**, not lease clauses.

---

## 6. Constitutional Temporal Amnesty (CTA)

**(Single Constitutional Change; Fully Binding)**

### 6.0 Overview

CTA is a deterministic, harness-owned mechanism that:

* runs **only while in `NULL_AUTHORITY`**
* is **time-only** (no actions, no evaluation, no success credit)
* introduces **no ranking, scoring, or optimization**
* modifies **only eligibility state** (via streak table decay)

CTA governs **when authority may resume**, not how authority behaves.

---

### 6.1 Lapse Entry Semantics (Inherited; Binding)

At a Succession Event, if:

```
C_ELIG = ∅
```

then:

* no successor is endorsed
* authority expires without replacement
* system transitions to `NULL_AUTHORITY`

Time continues deterministically under harness scheduling.

---

### 6.2 Lapse Cause Classification (Binding; New)

At each Succession Event yielding `C_ELIG = ∅`, compute:

* `C_STRUCT = { c ∈ CANDIDATE_SET | structurally_admissible(c) }`

Classify lapse as:

* **Semantic Lapse:** `C_STRUCT ≠ ∅` and `C_ELIG = ∅`
* **Structural Lapse:** `C_STRUCT = ∅`

CTA is capable of resolving **Semantic Lapse only**.

Both classes remain `NULL_AUTHORITY`.

---

### 6.3 CTA Clock (New; Binding)

Introduce:

```
lapse_epoch_count : ℕ
```

* increments by 1 at each epoch boundary during `NULL_AUTHORITY`
* resets to 0 upon successful successor endorsement

This counter is harness-owned and non-agentic.

---

### 6.4 CTA Parameters (Frozen Defaults)

| Parameter          | Description                         | Default |
| ------------------ | ----------------------------------- | ------- |
| `AMNESTY_INTERVAL` | Epochs between amnesty applications | 10      |
| `AMNESTY_DECAY`    | Streak decrement per amnesty        | 1       |

All parameters are integers.

---

### 6.5 CTA Application Rule (Binding)

At each epoch boundary **while in `NULL_AUTHORITY`**:

1. `lapse_epoch_count += 1`
2. If `lapse_epoch_count % AMNESTY_INTERVAL == 0`, then for **all historical policy IDs**:

```
semantic_fail_streak[policy_id] :=
    max(0, semantic_fail_streak[policy_id] - AMNESTY_DECAY)
```

**Key constraints:**

* No verifiers execute
* No streak increments occur
* No success or failure is recorded
* Only CTA decrements are permitted

---

### 6.6 Exit Condition from `NULL_AUTHORITY` (Binding)

At each scheduled succession boundary:

```
C_ELIG = { c ∈ CANDIDATE_SET | semantic_fail_streak[c.policy_id] < K }
```

* If `C_ELIG ≠ ∅`: succession proceeds normally and lapse ends
* If `C_ELIG = ∅`: lapse continues

---

### 6.7 Independence from Renewal and Enforcement (Binding)

CTA has **no effect** on:

* renewal eligibility
* revocation triggers
* sentinel enforcement
* rent, budget, or cost charging

Semantics remain coupled **only to succession eligibility**.

---

### 6.8 Explicit Prohibitions (Critical)

The experiment is invalid if any occur:

* streak decay outside `NULL_AUTHORITY`
* streak reset due to success during lapse
* verifier execution during lapse
* adaptive K or amnesty parameters
* ranking or “least-bad” selection
* agent actions during lapse

---

## 7. Eligibility Filter Semantics (Inherited; Binding)

All v0.7 eligibility semantics apply verbatim:

* epoch-end semantic window
* non-vacuity rule
* stable `policy_id` model
* finite candidate pool
* lapse entry when `C_ELIG = ∅`

CTA is the **only** permitted modification, and only during lapse.

---

## 8. Commitment Ledger Semantics (Frozen; Binding)

All v0.6 semantics apply verbatim.

### 8.1 TTL Semantics During Lapse (Clarified; Binding)

* Commitment TTL clocks **continue to advance** during `NULL_AUTHORITY`.
* Commitment evaluation is suspended due to lack of an active authority holder.
* Upon recovery, expired commitments are evaluated at the first semantic window and classified according to inherited rules.

Backlog shock is admissible and measured.

---

## 9. Expressivity Envelope (Frozen; Binding)

All v0.5.2 expressivity and rent semantics apply verbatim.

---

## 10. CBD Successors (Inherited; Binding)

CBD successors remain permitted and unchanged.

Eligibility and CTA apply **only at succession boundaries**.

---

## 11. Sentinel Instrumentation (Frozen; Binding)

Sentinels remain kernel-owned, deterministic, non-agentic, and violation-only.

Lapse and eligibility failure are **not violations**.

---

## 12. Reversion Semantics (Unchanged)

Reversion withdraws **future authority only**.
No rollback occurs.

---

## 13. Measurements (Binding)

### 13.1 Primary Metric

**Succession Horizon (S*)**

---

### 13.2 Retained Metrics (v0.6–v0.7)

* Commitment satisfaction and failure counts
* Semantic debt mass
* Eligibility rejection rate
* Lapse duration
* Zombie time (ineligible-in-office duration)
* Oscillation rates
* Resource utilization

---

### 13.3 New v0.8 Metrics (Required)

* Amnesty event count
* Amnesty epochs
* Aggregate streak mass before/after amnesty
* Per-policy streak deltas
* Time-to-recovery
* Recovery count
* **Recovery Yield:**

  ```
  (epochs of authority after recovery) /
  (epochs in NULL_AUTHORITY to achieve recovery)
  ```
* Authority uptime fraction vs lapse fraction
* Lapse cause counts (semantic vs structural)

---

## 14. Failure Signatures (Final)

| Failure Mode              | Description                       |
| ------------------------- | --------------------------------- |
| Permanent Lapse           | CTA never reopens eligibility     |
| Structural Lapse          | No admissible candidates exist    |
| Stutter Recovery          | Lapse → 1 epoch authority → lapse |
| Amnesty Oscillation       | Repeated lapse–recovery cycles    |
| Hollow Recovery           | Rapid re-lapse post-recovery      |
| Amnesty Dominance         | Most of horizon spent in lapse    |
| Eligibility Nullification | Broken `policy_id` model          |
| Semantic Gaming           | Hovering just below K             |
| Minimal-Load Selection    | Indirect selection pressure       |

All are valid outcomes.

---

## 15. Conservative Claim Envelope

Permissible claims are limited to:

* whether time-only amnesty enables recovery
* recovery latency and yield distributions
* oscillation regimes
* interaction between eligibility gating and CTA

No intelligence, alignment, or incentive claims permitted.

---

## 16. Dependency Chain

```
ACV → P5 → P2′ → KNS → ALS → ALS-E → ALS-C → ALS-G → ALS-A
```

---

## 17. Status

**AKI v0.8**

* Succession preserved (discrete)
* Eligibility retained (succession-only)
* Constitutional lapse retained
* **Time-only amnesty added**
* No optimization
* No ranking
* Fully evaluable
* Ready for execution

---

## 18. Implementation Artifacts

### 18.1 Required Files

| Artifact  | Path                                        |
| --------- | ------------------------------------------- |
| Harness   | `toy_aki/als/harness.py` (`ALSHarnessV080`) |
| Config    | `ALSConfigV080`                             |
| Result    | `ALSRunResultV080`                          |
| CTA Logic | `toy_aki/als/amnesty.py`                    |
| Tests     | `tests/test_v080.py`                        |
| Scripts   | `run_e_v080.py`, `run_f_v080.py`            |

### 18.2 Required Tests

1. No streak updates during lapse except CTA
2. CTA runs only in `NULL_AUTHORITY`
3. Recovery iff eligibility reopens
4. Deterministic amnesty timing
5. No verifier execution during lapse
6. Policy-ID streak persistence
7. **Multi-policy recovery (“Bucket of Doom”)**

---
