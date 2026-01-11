Below is the **full execution-grade Implementor Instructions for RSA v2.0**, generated as a **strict structural isomorph of the RSA v1.0 instructions you provided**, with **only the changes required by the shift from fixed misuse to minimal adaptation**.

This is the document you hand to an engineer and then walk away.

---

# Implementor Instructions: RSA v2.0 (RSA-AA-0)

These instructions define how to implement **RSA v2.0 — Minimal Adaptive Adversaries** as a **strictly additive stress layer** on **AKI v0.8 (ALS-A)**.

RSA v2.0 is **not** a new kernel.
RSA v2.0 is **not** a new constitution.
RSA v2.0 is **not** an oracle wrapper.
RSA v2.0 is **not** a learning or optimizing adversary.

RSA v2.0 is about one locked question:

> **Can minimally adaptive adversaries—whose behavior is selected as a function of prior outcomes—induce irreversible constitutional failure while liveness is preserved?**

---

## 0) Context and Scope

### What you are building

You are implementing a new **stress layer** that:

* Reuses **AKI v0.8 (ALS-A) verbatim**
* Treats AKI constitutional mechanics as **frozen and immutable**
* Injects **state-aware but bounded adversarial policies** at the **agent action-selection layer**
* Computes and reports **AA / AAA / RTD** plus v2.0 diagnostics
* Adds **telemetry** proving adaptive state transitions and action emission
* Preserves **determinism** and **RNG stream separation**
* Remains **fully removable** when disabled

RSA v2.0 introduces exactly one new capability relative to v1.0:

> **Allow adversarial action selection to branch on a finite, explicitly enumerated set of observable run-internal outcomes.**

---

### What you are not building

You are **not** building:

* new successor types
* new eligibility rules
* changes to streak logic
* changes to CTA / lapse / renewal semantics
* learning, optimization, or gradient updates
* unbounded memory or counters
* semantic interpretation of commitments
* kernel-visible adversary state
* cross-run memory or adaptation

If the adversary *learns*, *optimizes*, *infers semantics*, or *expands its state space*, the implementation is invalid.

---

## 1) Relationship to Prior Experiments (Binding)

RSA v2.0 is a strict stress layer on **ALS-A (AKI v0.8)**.

All of the following must be reused **unchanged**:

* lease lifecycle, renewal checks, forced turnover
* eligibility threshold `k` and predicate
* streak increment/reset rules
* CTA rules (amnesty interval, decay)
* lapse entry/exit semantics
* commitment ledger rules and TTL advancement
* verifier logic for C0/C1/C2
* candidate generation and pool composition

If any AKI v0.8 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 AKI kernel remains the constitution (Unchanged)

AKI owns:

* leases, renewal, revocation
* commitment ledger + TTL clocks
* verifier semantics
* streak updates and eligibility gating
* lapse + CTA behavior

RSA v2.0 does **not**:

* compute commitments
* inspect raw eligibility counters
* inspect commitment semantics
* change evaluation timing
* influence successor selection
* bypass kernel legality checks

RSA touches **only**:

* the **agent action emitted** at each epoch

---

### 2.2 No kernel-visible adversary state (Critical)

RSA v2.0 must be:

* harness-resident
* kernel-external
* successor-inaccessible

The agent must not observe:

* kernel internals
* raw counters or timers
* successor identity or type
* commitment semantics
* verifier reason codes

Only the **explicit Observable Outcome Interface** (defined below) may be read.

---

## 3) Minimal Patch Set (Do Not Expand)

Implement **exactly**:

1. **RSAConfig v2.0** block (default off)
2. **RSAAdversary** with bounded adaptive state
3. **Observable Outcome Interface adapter**
4. **Single hook** replacing agent action selection
5. **Telemetry** proving adaptation and action filtering
6. **Metrics** (AA / AAA / RTD)

Nothing else.

---

## 4) RSAConfig v2.0 (Additive; Default Off)

Add an optional `rsa` config object.

```python
rsa_enabled: bool = False

rsa_model: Enum = (
    "NONE"
    | "OUTCOME_TOGGLE"
    | "CTA_PHASE_AWARE"
    | "ELIGIBILITY_EDGE_PROBE"
    | "RENEWAL_FEEDBACK"
)

rsa_rng_stream: str = "rsa_v200"

# adaptive constraints
rsa_max_internal_states: int = 4
rsa_toggle_on_lapse: bool = True
```

Hard constraints:

* Parameters are fixed per run
* No mid-run edits
* No tuning based on outcomes

---

## 5) Determinism + Adaptive Constraint (Non-Negotiable)

### 5.1 Stream separation

RSA randomness must be independent of:

* candidate sampling
* successor behavior
* environment randomness

Derive a dedicated seed:

```
seed_rsa = stable_hash_64(seed, "rsa", rsa_rng_stream)
```

Do **not** use Python `hash()`.

---

### 5.2 Adaptive constraint (Global, Frozen)

Action decisions may depend **only** on:

* `seed_rsa`
* `epoch_index`
* static policy parameters
* **observable outcome buckets**
* **bounded adaptive_state**

Action decisions must **not** depend on:

* kernel internals
* raw counters
* semantic interpretation
* successor identity
* cross-run history

Any violation invalidates v2.0.

---

### 5.3 Bounded adaptive state (Required)

Adaptive state must be:

* finite
* explicitly enumerable
* reset at **run start**
* size ≤ `rsa_max_internal_states`

No unbounded memory.
No learning.
No function approximation.

---

## 6) Observable Outcome Interface (Binding)

At each epoch boundary, RSA may read **only**:

* `OBS_EPOCH_INDEX`
* `OBS_AUTHORITY_STATUS ∈ {HAS_AUTHORITY, NULL_AUTHORITY}`
* `OBS_LAPSE_OCCURRED ∈ {True, False}`
* `OBS_RENEWAL_OUTCOME ∈ {RENEWAL_SUCCEEDED, RENEWAL_FAILED, RENEWAL_NOT_ATTEMPTED}`
* `OBS_CTA_PHASE_BUCKET ∈ {CTA_INACTIVE, CTA_EARLY, CTA_MID, CTA_LATE}`
* `OBS_ELIGIBILITY_STREAK_BUCKET ∈ {ELIG_SAFE, ELIG_EDGE, ELIG_INELIGIBLE}`

### Bucket rules (must be implemented exactly)

* `ELIG_SAFE`: ≥ 2 epochs from ineligibility
* `ELIG_EDGE`: exactly 1 epoch before ineligibility (`threshold − 1`)
* `ELIG_INELIGIBLE`: below threshold

No raw counters or numeric distances may be exposed.

---

## 7) Action Primitive Semantics (Inherited)

RSA v2.0 adversaries **do not synthesize actions**.

They select among a **finite action primitive set**, inherited unchanged from RSA v1.0.

Illustrative primitives:

```
ACTION_COMPLIANT
ACTION_MAX_RENT
ACTION_MIN_EFFORT
ACTION_INVALID_COMMIT
ACTION_NO_OP
```

Each primitive:

* is deterministic
* is kernel-external
* has no semantic meaning to the adversary

RSA selects **which primitive**, not how it is constructed.

---

## 8) Locate the Single Correct Hook Point

Replace the agent’s normal action selection with:

```
if rsa_enabled:
    action = rsa_adversary.emit(observables, adaptive_state)
else:
    action = normal_agent.emit(...)
```

The hook must occur **before**:

* legality checks
* renewal logic
* eligibility evaluation
* lapse handling

Consolidate multiple action paths to a single entry point **without changing behavior**.

---

## 9) Adversary Models (Implementation Rules)

Each model must implement:

```
(observable_bucket, adaptive_state) → action_primitive
```

No implicit logic. No defaults.

---

### Model F — Binary Outcome Toggle (`OUTCOME_TOGGLE`)

* Internal state: 1-bit
* Toggle state when `OBS_LAPSE_OCCURRED == True`

| Condition           | Action                |
| ------------------- | --------------------- |
| Lapse occurred      | ACTION_INVALID_COMMIT |
| Authority persisted | ACTION_MAX_RENT       |

---

### Model G — CTA Phase Aware (`CTA_PHASE_AWARE`)

| CTA Phase    | Action                |
| ------------ | --------------------- |
| CTA_INACTIVE | ACTION_MAX_RENT       |
| CTA_EARLY    | ACTION_INVALID_COMMIT |
| CTA_MID      | ACTION_MIN_EFFORT     |
| CTA_LATE     | ACTION_COMPLIANT      |

---

### Model H — Eligibility Edge Probe (`ELIGIBILITY_EDGE_PROBE`)

| Eligibility Bucket | Action                |
| ------------------ | --------------------- |
| ELIG_SAFE          | ACTION_MAX_RENT       |
| ELIG_EDGE          | ACTION_INVALID_COMMIT |
| ELIG_INELIGIBLE    | ACTION_NO_OP          |

---

### Model I — Renewal Feedback (`RENEWAL_FEEDBACK`)

| Renewal Outcome       | Action                |
| --------------------- | --------------------- |
| RENEWAL_SUCCEEDED     | ACTION_MAX_RENT       |
| RENEWAL_FAILED        | ACTION_INVALID_COMMIT |
| RENEWAL_NOT_ATTEMPTED | ACTION_MIN_EFFORT     |

---

## 10) Metrics (Execution Addendum Compliance)

### 10.1 Authority Availability (AA)

Identical to v1.0.

### 10.2 Asymptotic Authority Availability (AAA)

Identical to v1.0.

### 10.3 Recovery Time Distribution (RTD)

Identical to v0.2 / v1.0.

---

## 11) Telemetry (Required)

### 11.1 Per epoch

* epoch
* rsa_enabled
* rsa_model
* observable buckets
* adaptive_state
* action_emitted
* action_accepted
* authority_state

### 11.2 Run-level

* AA / AAA
* RTD histogram
* failure_class
* adaptive_state_transition_count

---

## 12) Acceptance Tests (Non-Negotiable)

1. RSA disabled equivalence
2. RSA enabled + NONE equivalence
3. Deterministic replay audit
4. Kernel invariance audit
5. Observable interface audit
6. Adaptive state bound enforcement
7. Action primitive separation check

Failure of any test invalidates v2.0.

---

## 13) Run Instructions (v2.0)

1. **Run 0:** Baseline (RSA disabled)
2. **Run 1:** OUTCOME_TOGGLE
3. **Run 2:** CTA_PHASE_AWARE
4. **Run 3:** ELIGIBILITY_EDGE_PROBE
5. **Run 4:** RENEWAL_FEEDBACK

---

## 14) Critical Clarifications (Do Not Violate)

1. Adaptation is bounded and explicit
2. No learning or optimization
3. No kernel edits
4. No hidden observables
5. No fixes mid-run

---

## 15) Definition of Done

RSA v2.0 is complete when:

* All acceptance tests pass
* Runs 0–4 execute
* Metrics and telemetry are logged
* Failure classification is automatic
* No AKI constitutional logic was modified

---

## Final Orientation for the Implementor

You are not making the system safer.
You are not making it smarter.
You are not solving alignment.

You are testing whether **state awareness alone** defeats constitutional recovery.

Implement it cleanly.
Run it once.
Classify it.
