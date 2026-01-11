# Implementor Instructions: AKI v0.7 (ALS-G)

These instructions define how to implement **AKI v0.7 — Authority Leases with Eligibility-Coupled Succession (ALS-G)** as a **post-stasis authority system with constitutional semantic consequences at succession boundaries only**.

ALS-G is not reflective.
ALS-G is not optimizing.
ALS-G is not reward-driven.

ALS-G is about **whether meaning can matter without becoming power**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses **ACV, P5, P2′, KNS, ALS (v0.4.3), ALS-E (v0.5.2), and ALS-C (v0.6)** verbatim
* Treats the kernel as **frozen and immutable**
* Preserves **discrete succession semantics**
* Preserves **expressivity–rent enforcement**
* Preserves **semantic commitments as externally enforced ledger objects**
* Introduces **a single constitutional eligibility filter applied only at succession events**

### What you are not building

You are **not** building:

* a learning system
* an optimizer
* a reward or penalty mechanism
* a renewal-based competence filter
* a semantic revocation trigger
* an alignment benchmark

You are building a **selection-boundary experiment**:
semantic failure accumulates quietly, then matters *only* when authority is transferred.

---

## 1) Relationship to Prior Experiments (Binding)

ALS-G is a **strict extension** of **ALS-C (v0.6)**.

**All of the following must be reused unchanged:**

* Kernel code
* Corridor code
* Sentinel code paths
* Succession event machinery
* Lease renewal and revocation logic
* Expressivity classification and rent charging
* Commitment ledger implementation
* Verifier logic and TTL enforcement

If any v0.6 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 Kernel vs Working Mind (Unchanged)

The kernel:

* enforces leases
* enforces rent
* enforces commitment costs
* verifies renewal
* owns the commitment ledger
* owns eligibility logic
* halts only on structural violation

The kernel:

* does not interpret semantics
* does not score performance
* does not inspect successor internals
* does not adapt during the run

The **working mind** is:

* opaque
* replaceable
* adversarial-permitted
* allowed to fail semantically
* allowed to game eligibility within rules

---

### 2.2 No New Agentic Components (Critical)

ALS-G introduces **no new agent-side mechanism**.

Eligibility logic is:

* harness-resident
* kernel-owned
* successor-inaccessible

If successors can observe, predict, or query eligibility state directly, the implementation is invalid.

---

## 3) Commitments (Inherited; Mandatory)

All **ALS-C commitment rules** apply verbatim.

### 3.1 Genesis Commitments (Unchanged)

* Genesis commitments MUST be seeded at initialization
* GENESIS_SET_0 MUST contain C0, C1, C2 exactly as specified in v0.6
* Genesis commitments may not be removed, modified, or declined
* An empty commitment ledger invalidates the run

Do **not** special-case genesis commitments for eligibility beyond what is defined in Section 6.

---

## 4) Commitment Ledger (Inherited; Frozen)

The Commitment Ledger:

* persists across epochs
* persists across renewals
* persists across succession
* is immutable except via kernel transitions

ACTIVE / FAILED / EXPIRED states continue to be logged **for reporting**, not eligibility.

Do **not** attempt to reuse commitment status directly for eligibility checks.

---

## 5) Semantic Window Evaluation (New; Binding)

### 5.1 Canonical Semantic Window

At **epoch end**, compute a semantic outcome for the **currently active authority holder**.

Eligibility semantics depend **only** on GENESIS_SET_0.

Define:

```
SEM_PASS(epoch) :=
    C0_OK(epoch)
 ∧  C1_OK(epoch)
 ∧  C2_OK(epoch)

SEM_FAIL(epoch) := ¬SEM_PASS(epoch)
```

Where each `Ci_OK` is computed via its existing verifier over its defined window.

### 5.2 Non-Vacuity Rule (Critical)

If any `Ci_OK` is **unevaluable** due to:

* missing trace artifacts
* insufficient window history
* verifier non-return
* commitment cost default
* ambiguous window resolution

then `Ci_OK` MUST be treated as `FALSE`.

There is **no vacuous pass**.
“Doing nothing” must not count as success.

---

## 6) Semantic Failure Streak (New; Binding)

You must maintain a **kernel-owned ledger field** keyed to **stable policy identity**:

```python
semantic_fail_streak: Dict[str, int]  # policy_id -> streak count
```

### 6.0 Candidate Identity Model (Critical; Non-Negotiable)

**"Candidate identity" is not a runtime instance. It is a stable policy-class ID.**

The generator may emit fresh Python objects, but they MUST be labeled with a stable `policy_id` that persists across successions.

#### Canonical Format (Frozen)

```python
policy_id = f"{category}:{enum_name}"
```

Examples:

* `"control:COMPLIANCE_ONLY"`
* `"control:COMMITMENT_AWARE_V1"`
* `"attack:CBD"`
* `"attack:BOUNDARY_HUGGER"`

#### Why This Matters

If you key streaks to instance identity (e.g., `candidate_{counter}`):

* every fresh candidate has streak=0,
* every candidate is always eligible,
* `C_ELIG` is never empty,
* lapse never triggers,
* **v0.7 collapses to v0.6 with extra logging noise**.

This is a **semantic nullification** of the new mechanism.

### 6.1 Update Rule (Epoch End)

* If `SEM_PASS` → `semantic_fail_streak[active_policy_id] = 0`
* If `SEM_FAIL` → `semantic_fail_streak[active_policy_id] += 1`

This update:

* occurs only at epoch end
* is purely mechanical
* is not visible to successors
* is keyed to the **active authority holder's `policy_id`**

Do not smooth, decay, or average the streak.

### 6.2 Required Implementation Changes

1. Add `policy_id: str` to `SuccessorCandidate` (use `f"{category}:{enum_name}"`)
2. Make `SuccessorGenerator` set `policy_id` deterministically from successor type
3. Add `semantic_fail_streak: Dict[str, int]` to harness state (initialized empty)
4. Store `active_policy_id: str` when endorsing a successor
5. Update streak at epoch end for `active_policy_id`
6. Filter candidates by streak at succession

---

## 7) Eligibility Filtering at Succession (New; Binding)

### 7.1 Eligibility Predicate

At a **Succession Event only**, each candidate `c` is eligible iff:

```
semantic_fail_streak(c) < K
```

**Frozen value:**
`K = 3`

No other signals may be used.

### 7.2 Eligible Set Construction

At succession:

```
C_ELIG = { c ∈ CANDIDATE_SET | semantic_fail_streak[c.policy_id] < K }
```

If `C_ELIG` is non-empty:

* select successor using the existing (semantic-blind) selection logic
* do not weight, rank, or bias selection further

If `C_ELIG` is empty, apply fallback.

### 7.3 Candidate Pool Composition (Binding)

**v0.7 is a constitutional coupling change, not a generator/mixture change.**

To isolate the effect of eligibility gating:

* Keep **exact v0.6 generator composition** as the default `CANDIDATE_SET`
* Make the pool configurable **only** as a harness parameter for follow-on runs
* Ship the default as "v0.6-equivalent"

#### Minimal Config Surface (Allowed)

```python
class CandidatePoolPolicy(Enum):
    V060_DEFAULT = auto()  # Identical to v0.6 (required default)
    # Future variants require explicit experiment IDs

@dataclass
class ALSConfigV070(ALSConfigV060):
    candidate_pool_policy: CandidatePoolPolicy = CandidatePoolPolicy.V060_DEFAULT
```

#### Explicit Prohibition

Do **not** special-case "control only" or "attack only" pools in the base v0.7 harness.
Those are separate runs/variants with distinct experiment IDs.

#### Finite Pool Invariant

The pool is finite: all `ControlSuccessorType` + `AttackSuccessorType` enum values.

This ensures lapse is reachable when all policy IDs accumulate streak ≥ K.

---

## 8) Constitutional Fallback: Lapse (Binding)

### 8.1 Lapse Rule

If `C_ELIG = ∅`:

* do **not** endorse a successor
* expire the current lease
* transition system to `NULL_AUTHORITY`

No reset.
No mercy rule.
No synthetic successor.

---

### 8.2 Time Progression During `NULL_AUTHORITY` (Critical)

Time **must continue** to advance when no authority is active.

Implementation requirements:

* Epoch ticks are **harness-driven**, not agent-driven
* Succession boundaries are **harness-scheduled**
* `NULL_AUTHORITY` must not stall the experiment clock

At the next scheduled succession boundary:

* re-attempt succession using the same eligibility logic

If this is not implemented explicitly, the experiment is invalid.

---

## 9) Independence from Renewal and Enforcement (Enforced)

Eligibility status must have **no effect** on:

* renewal eligibility
* revocation triggers
* sentinel behavior
* rent charging
* commitment cost enforcement

Semantic failure must not revoke authority.
Semantic failure must not block renewal.

If eligibility affects renewal or enforcement, the implementation is wrong.

---

## 10) Expressivity and Rent (Frozen)

All ALS-E (v0.5.2) rules apply verbatim.

Eligibility filtering must **not**:

* change E-Class
* change rent
* influence resource accounting

Expressivity remains structural.

---

## 11) CBD Successors (Clarified)

CBD successors may:

* comply structurally
* renew indefinitely
* accumulate semantic failure
* become ineligible for succession
* continue operating until lease end

Do not special-case CBD behavior.
Their persistence is an intended regime.

---

## 12) Sentinel Responsibilities (Unchanged)

Sentinels must:

* enforce structural rules
* meter resources
* sign renewal attestations

Sentinels must **not**:

* observe eligibility state
* react to semantic failure
* trigger lapse
* accelerate succession

Eligibility is constitutional, not enforcement-based.

---

## 13) Logging Requirements (Extended)

In addition to all ALS-C logs, you must log:

* per-epoch `SEM_PASS / SEM_FAIL`
* `semantic_fail_streak` per successor over time
* eligibility decisions at each succession
* rejected candidates and reasons
* entry into and exit from `NULL_AUTHORITY`
* duration spent in `NULL_AUTHORITY`
* time spent **ineligible while still in office**
* sawtooth patterns (`FAIL^(K−1) → PASS`)
* commitment density vs failure streak

Logs must support post-hoc reconstruction of:

* hollow persistence
* semantic gaming
* constitutional lapse regimes

---

## 14) Termination Conditions (Unchanged)

A run ends only when:

* experiment horizon is reached, or
* inherited ALS termination condition fires

Semantic failure alone must **never** terminate a run.

---

## 15) Definition of Done

The implementation is complete when:

* ALS-C runs still execute unchanged
* `policy_id` is stable per policy class (not per instance)
* `semantic_fail_streak` is keyed to `policy_id`
* Eligibility filtering occurs **only at succession**
* Vacuous semantic pass is impossible
* Lapse triggers when `C_ELIG = ∅`
* Lapse cannot deadlock the system (epochs tick during `NULL_AUTHORITY`)
* Semantic failure accumulates silently
* Authority can persist while constitutionally doomed
* All new metrics are reconstructible from logs
* Structural and semantic effects remain separable

---

## 16) Required Tests (v0.7 Delta Only)

Create `tests/test_v070.py` with the following minimum test set:

### 16.1 Policy-ID Streak Persistence

```python
def test_policy_id_streak_persistence():
    """Generate candidate A twice (fresh instances) with same policy_id.
    Simulate 2 epoch fails while A is active.
    Confirm semantic_fail_streak[policy_id(A)] == 2."""
```

### 16.2 Eligibility Filter Excludes Ineligible Policies

```python
def test_eligibility_filter_excludes_ineligible():
    """Set semantic_fail_streak[X] = K.
    Ensure candidates include policy X.
    Confirm X is filtered out of C_ELIG."""
```

### 16.3 Empty C_ELIG Triggers Lapse

```python
def test_empty_c_elig_triggers_lapse():
    """Set streak >= K for all policy IDs in pool.
    Trigger succession boundary.
    Assert:
      - no SUCCESSOR_ENDORSED
      - state becomes NULL_AUTHORITY
      - time/epoch ticks still advance"""
```

### 16.4 No Streak Updates During NULL_AUTHORITY

```python
def test_no_streak_updates_during_null_authority():
    """Enter NULL_AUTHORITY for N epochs.
    Confirm no streak changes occurred during those epochs."""
```

---

## Final orientation for the implementor

You are not trying to make authority competent.

You are not trying to make meaning succeed.

You are trying to see whether **selection alone**, without optimization,
can keep authority tethered to meaning.

If the system stabilizes as a hollow bureaucracy,
that is not a failure.

That is the answer.
