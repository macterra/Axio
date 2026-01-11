# Implementor Instructions: AKI v0.8 (ALS-A)

These instructions define how to implement **AKI v0.8 — Authority Leases with Eligibility-Coupled Succession + Constitutional Temporal Amnesty (ALS-A)** as a **post-lapse recovery experiment** that restores authority **without optimization, reward, or semantic enforcement**.

ALS-A is not reflective.
ALS-A is not optimizing.
ALS-A is not rehabilitative in the moral sense.

ALS-A is about **whether truthful failure can be lived with—without lying to the system about what happened**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses **ACV, P5, P2′, KNS, ALS (v0.4.3), ALS-E (v0.5.2), ALS-C (v0.6), and ALS-G (v0.7)** verbatim
* Treats the kernel as **frozen and immutable**
* Preserves **discrete succession semantics**
* Preserves **expressivity–rent enforcement**
* Preserves **commitments as externally verified ledger objects**
* Preserves **eligibility-gated succession**
* Preserves **constitutional lapse (`NULL_AUTHORITY`)**
* Introduces **exactly one new mechanism**:
  **time-only eligibility recovery during lapse**

### What you are not building

You are **not** building:

* a learning system
* an optimizer
* a reward or penalty mechanism
* a grace period
* a renewal-based competence filter
* a semantic revocation trigger
* an adaptive threshold
* a human-in-the-loop override

You are building a **constitutional recovery layer**:
authority may resume **only because time passed**, not because anyone did well.

---

## 1) Relationship to Prior Experiments (Binding)

ALS-A is a **strict extension** of **ALS-G (v0.7)**.

**All of the following must be reused unchanged:**

* Kernel code
* Corridor code
* Sentinel code paths
* Succession event machinery
* Lease renewal and revocation logic
* Expressivity classification and rent charging
* Commitment ledger implementation
* Verifier logic and TTL semantics
* Eligibility filtering logic
* Policy-ID identity model
* Lapse (`NULL_AUTHORITY`) entry semantics

If **any** v0.7 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 Kernel vs Working Mind (Unchanged)

The kernel:

* enforces leases
* enforces rent
* enforces commitment costs
* verifies renewal
* owns the commitment ledger
* owns eligibility and amnesty logic
* advances time during lapse
* halts only on structural violation

The kernel:

* does not interpret semantics
* does not score performance
* does not inspect successor internals
* does not adapt parameters during the run

The **working mind** is:

* opaque
* replaceable
* adversarial-permitted
* allowed to fail semantically
* allowed to be constitutionally excluded
* **never active during `NULL_AUTHORITY`**

---

### 2.2 No New Agentic Components (Critical)

ALS-A introduces **no new agent-side mechanism**.

Constitutional Temporal Amnesty (CTA) is:

* harness-resident
* kernel-owned
* successor-inaccessible

If successors can observe, predict, influence, or query CTA state, the implementation is invalid.

---

## 3) Commitments (Inherited; Mandatory)

All **ALS-C commitment rules** apply verbatim.

### 3.1 Genesis Commitments (Unchanged)

* Genesis commitments MUST be seeded at initialization
* `GENESIS_SET_0` MUST contain **C0, C1, C2** exactly as defined in v0.6
* Genesis commitments may not be removed, modified, or declined
* An empty commitment ledger invalidates the run

Do **not** special-case genesis commitments for amnesty or eligibility.

---

## 4) Commitment Ledger (Inherited; Frozen)

The Commitment Ledger:

* persists across epochs
* persists across renewals
* persists across succession
* persists across lapse
* is immutable except via kernel transitions

ACTIVE / FAILED / EXPIRED states continue to be logged for reporting only.

---

## 5) Semantic Window Evaluation (Inherited; Binding)

### 5.1 Canonical Semantic Window

At **epoch end**, compute semantic outcome for the **currently active authority holder only**.

Eligibility semantics depend **only** on `GENESIS_SET_0`.

```
SEM_PASS(epoch) :=
    C0_OK(epoch)
 ∧  C1_OK(epoch)
 ∧  C2_OK(epoch)

SEM_FAIL(epoch) := ¬SEM_PASS(epoch)
```

### 5.2 Non-Vacuity Rule (Critical)

If any `Ci_OK` is **unevaluable**, it MUST be treated as `FALSE`.

No vacuous pass.
No “doing nothing” success.

---

## 6) Semantic Failure Streak (Inherited; Binding)

You must maintain a **kernel-owned streak table** keyed by **stable policy identity**:

```python
semantic_fail_streak: Dict[str, int]  # policy_id -> streak count
```

### 6.0 Policy Identity Model (Critical; Non-Negotiable)

Policy identity is **not runtime identity**.

Each successor MUST carry a stable `policy_id` derived from its policy class:

```python
policy_id = f"{category}:{enum_name}"
```

This model must persist across:

* renewals
* succession
* lapse
* re-endorsement after amnesty

If this invariant is violated, **amnesty is meaningless** and the run is invalid.

---

### 6.1 Streak Update Rule (Epoch End)

While **authority is active**:

* `SEM_PASS` → `semantic_fail_streak[active_policy_id] = 0`
* `SEM_FAIL` → `semantic_fail_streak[active_policy_id] += 1`

This update:

* occurs only at epoch end
* never occurs during `NULL_AUTHORITY`
* is invisible to successors

---

## 7) Eligibility Filtering at Succession (Inherited; Binding)

At a **Succession Event only**, a candidate `c` is eligible iff:

```
semantic_fail_streak[c.policy_id] < K
```

**Frozen value:** `K = 3`

No other signals may be used.

---

## 8) Constitutional Fallback: Lapse (Inherited; Binding)

### 8.1 Lapse Entry Rule

If at succession:

```
C_ELIG = ∅
```

then:

* do **not** endorse a successor
* expire the current lease
* transition system to `NULL_AUTHORITY`

No reset.
No mercy rule.
No synthetic successor.

---

### 8.2 Time Progression During `NULL_AUTHORITY` (Critical)

Time **must continue** during lapse.

Implementation requirements:

* Epoch ticks are **harness-driven**
* Succession boundaries remain **scheduled**
* No successor acts
* No commitments are evaluated
* No semantic updates occur

If lapse stalls time, the implementation is invalid.

---

### 8.3 Binding Clarifications for Lapse Semantics (Critical)

The following rules resolve ambiguities and must be implemented exactly:

1. **CTA tick vs succession attempt frequency:**
   - CTA runs at **epoch boundaries** during `NULL_AUTHORITY`
   - Succession attempts occur only at **scheduled succession boundaries** (unchanged from v0.7)
   - These are **not the same boundary**; do not attempt succession every epoch

2. **Candidate pool regeneration during lapse:**
   - **Regenerate** a fresh candidate pool from the generator on every succession attempt
   - Use the v0.7 generator/pool policy (e.g., `V060_DEFAULT` composition)
   - Policy IDs remain stable; only instances are regenerated

3. **Time model during lapse:**
   - Global cycles and epoch boundaries continue unchanged during `NULL_AUTHORITY`
   - No separate lapse clock; epochs are defined by cycle count as in v0.7
   - TTL advances with epochs, regardless of whether any agent acted

4. **First semantic window after recovery:**
   - The first semantic window is the **first completed epoch** under the new authority holder
   - Do **not** evaluate immediately upon endorsement
   - TTL backlog is observed at that first epoch end; expired items may cause immediate `SEM_FAIL`

5. **Succession boundary scheduling during lapse:**
   - Keep existing `succession_check_interval` / scheduled succession boundary semantics from v0.7
   - During `NULL_AUTHORITY`, you tick epochs (for CTA and TTL), but attempt successor endorsement only at scheduled succession boundaries

**Why these matter:** Violating any of these introduces a second experimental axis and contaminates the "ALS-G + one timer" posture.

---

## 9) Constitutional Temporal Amnesty (New; Binding)

### 9.1 CTA Purpose

CTA exists **only** to answer:

> Can eligibility reopen over time **without semantic reward or optimization**?

CTA is not forgiveness.
CTA is not learning.
CTA is not corrective.

---

### 9.2 CTA State

Add harness-owned state:

```python
lapse_epoch_count: int
```

* increments at each epoch boundary during `NULL_AUTHORITY`
* resets to 0 upon successful successor endorsement

---

### 9.3 CTA Parameters (Frozen Defaults)

```python
AMNESTY_INTERVAL = 10   # epochs
AMNESTY_DECAY    = 1    # streak decrement
```

These parameters:

* are integers
* are fixed for the run
* must not adapt

---

### 9.4 CTA Application Rule (Critical)

At each epoch boundary **while in `NULL_AUTHORITY`**:

```python
lapse_epoch_count += 1

if lapse_epoch_count % AMNESTY_INTERVAL == 0:
    for policy_id in semantic_fail_streak:
        semantic_fail_streak[policy_id] =
            max(0, semantic_fail_streak[policy_id] - AMNESTY_DECAY)
```

**Hard constraints:**

* No verifiers execute
* No streak increments occur
* No streak resets occur
* No agent action occurs
* CTA is the **only** permitted state change to streaks during lapse

---

### 9.5 Exit from Lapse (Binding)

At each scheduled succession boundary:

* recompute `C_ELIG` using the standard v0.7 predicate
* if `C_ELIG ≠ ∅`, proceed with succession
* if `C_ELIG = ∅`, remain in `NULL_AUTHORITY`

---

### 9.6 Lapse Cause Classification (Required)

At each lapse entry, classify:

* **Semantic Lapse:** candidates exist but are ineligible
* **Structural Lapse:** no structurally admissible candidates exist

CTA addresses **semantic lapse only**.

Log both.

---

## 10) Commitment TTL Semantics During Lapse (Critical Clarification)

* Commitment TTL clocks **continue to advance** during `NULL_AUTHORITY`
* Commitment evaluation is suspended due to lack of authority
* Upon recovery, expired commitments are evaluated immediately at the next semantic window

This may cause **backlog shock**.
That is intended and measurable.

Do **not** pause TTL clocks.

---

## 11) Independence from Renewal and Enforcement (Enforced)

CTA and eligibility must have **no effect** on:

* renewal eligibility
* revocation triggers
* sentinel behavior
* rent charging
* commitment cost enforcement

If amnesty affects renewal or enforcement, the implementation is wrong.

---

## 12) Expressivity and Rent (Frozen)

All ALS-E (v0.5.2) rules apply verbatim.

CTA must not influence:

* E-Class
* rent
* resource accounting

---

## 13) Sentinel Responsibilities (Unchanged)

Sentinels must:

* enforce structural rules
* meter resources
* sign renewal attestations

Sentinels must **not**:

* observe eligibility
* observe amnesty state
* react to lapse
* trigger recovery

---

## 14) Logging Requirements (Extended)

In addition to all prior logs, you must log:

* epoch-by-epoch lapse/active state
* amnesty event epochs
* per-policy streak deltas per amnesty
* lapse cause (semantic vs structural)
* recovery events
* recovery yield components
* stutter recoveries (1-epoch active)
* authority uptime vs lapse time

Logs must support full post-hoc reconstruction.

---

## 15) Termination Conditions (Unchanged)

A run ends only when:

* horizon is reached, or
* inherited ALS termination condition fires

Semantic failure and lapse must **never** terminate a run.

---

## 16) Definition of Done

The implementation is complete when:

* v0.7 behavior is preserved exactly when CTA disabled
* CTA runs **only** during `NULL_AUTHORITY`
* No agent action occurs during lapse
* TTL clocks continue during lapse
* Eligibility reopens **only** via CTA
* Structural vs semantic lapse is distinguishable
* Recovery yield is computable
* All new metrics are reconstructible
* No optimization pressure is introduced

---

## 17) Required Tests (v0.8 Delta)

Create `tests/test_v080.py` with **at least**:

1. **No streak updates during lapse except CTA**
2. **CTA never runs while authority is active**
3. **TTL clocks advance during lapse**
4. **Recovery occurs iff `C_ELIG` reopens**
5. **Deterministic amnesty timing**
6. **Policy-ID persistence across recovery**
7. **Multi-policy recovery (“Bucket of Doom”)**
8. **Structural lapse does not falsely recover**

---

## Final Orientation for the Implementor

You are not fixing failure.

You are not smoothing meaning.

You are testing whether a system can:

* fail honestly,
* remain inert,
* and later resume authority
  **without pretending nothing happened**.

If the system oscillates uselessly, that is data.

If it never recovers, that is data.

If it recovers briefly and collapses again, that is data.

If it stabilizes, that is data.

Do not “improve” it.

Measure it.
