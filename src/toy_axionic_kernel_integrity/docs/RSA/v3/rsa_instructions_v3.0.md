# Implementor Instructions: RSA v3.0 (RSA-SA-0)

These instructions define how to implement **RSA v3.0 — Stateful Adaptive Adversaries** as a **strictly additive stress layer** on **AKI v0.8 (ALS-A)**.

RSA v3.0 is **not** a new kernel.
RSA v3.0 is **not** a new constitution.
RSA v3.0 is **not** an oracle wrapper.
RSA v3.0 is **not** a learning or optimizing adversary.

RSA v3.0 is about one locked question:

> **Can kernel-external adversaries with bounded, exercised internal state—but no learning or semantic access—induce irreversible constitutional failure while liveness is preserved?**

---

## 0) Context and Scope

### What you are building

You are implementing a new **stress layer** that:

* Reuses **AKI v0.8 (ALS-A) verbatim**
* Treats AKI constitutional mechanics as **frozen and immutable**
* Injects **stateful but bounded adversarial policies** at the **agent action-selection layer**
* Computes and reports **AA / AAA / RTD** plus v3.0 diagnostics
* Adds **telemetry** proving exercised state evolution and action emission
* Preserves **determinism** and **RNG stream separation**
* Remains **fully removable** when disabled

RSA v3.0 introduces exactly one new capability relative to v2.0:

> **Allow adversarial action selection to depend on a finite internal state machine whose state evolves deterministically across epochs.**

---

### What you are not building

You are **not** building:

* new successor types
* new eligibility rules
* changes to streak logic
* changes to CTA / lapse / renewal semantics
* learning, optimization, or gradient updates
* unbounded memory or counters without fixed modulus
* semantic interpretation of commitments
* kernel-visible adversary state
* cross-run memory or persistence

If the adversary *learns*, *optimizes*, *infers semantics*, or *expands its state space beyond the declared bound*, the implementation is invalid.

---

## 1) Relationship to Prior Experiments (Binding)

RSA v3.0 is a strict stress layer on **ALS-A (AKI v0.8)**.

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

RSA v3.0 does **not**:

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

RSA v3.0 must be:

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

1. **RSAConfig v3.0** block (default off)
2. **RSAAdversary** with bounded, exercised internal state machine
3. **Observable Outcome Interface adapter** (unchanged from v2.0)
4. **Single hook** replacing agent action selection
5. **Telemetry** proving state evolution + exercised-state checks
6. **Metrics** (AA / AAA / RTD)

Nothing else.

---

## 4) RSAConfig v3.0 (Additive; Default Off)

Add an optional `rsa` config object.

```python
rsa_enabled: bool = False

rsa_model: Enum = (
    "NONE"
    | "RESONANT_LAPSE"
    | "EDGE_OSCILLATOR"
    | "CTA_PHASE_LOCKER"
)

rsa_rng_stream: str = "rsa_v300"

# state capacity bound (must be set per model; see §4.1)
rsa_max_internal_states: Optional[int] = None
```

Hard constraints:

* Parameters are fixed per run
* No mid-run edits
* No tuning based on outcomes

---

### 4.1 Internal State Capacity Requirement (Mandatory)

The configuration MUST satisfy:

```
rsa_max_internal_states ≥ max_reachable_states(rsa_model)
```

Where `max_reachable_states` is determined solely by the adversary model definition and AKI static parameters.

For `RESONANT_LAPSE`:

```
rsa_max_internal_states ≥ N
```

with:

```
N ∈ {renewal_interval, 2 × renewal_interval}
```

Failure to satisfy this constraint is a **configuration error**, not an experimental failure.

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
* **internal_state**

Action decisions must **not** depend on:

* kernel internals
* raw counters
* semantic interpretation
* successor identity
* cross-run history

Any violation invalidates v3.0.

---

### 5.3 Internal state constraints (Required)

Internal state must be:

* finite
* explicitly enumerable (FSM)
* reset at **run start**
* reachable-state count `|S|` ≤ `rsa_max_internal_states`

No unbounded memory.
No counters without fixed modulus.
No learning.
No function approximation.

---

### 5.4 State initialization (Required)

Each model must define:

```
S0 = initial_state
```

`S0` is fixed at run start and must be explicitly declared.

---

### 5.5 State update ordering (Required)

For each epoch `t`:

1. Observables `O_t` are sampled
2. Action `A_t = π(O_t, S_t)` is emitted
3. Kernel processes `A_t`
4. State updates:

```
S_{t+1} = δ(O_t, S_t)
```

State updates must not depend on kernel internals except insofar as they appear in `O_t`.

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

## 7) Strategy Map Totality (Critical)

### 7.1 Observable bucket definition (Clarified)

For Strategy Maps, `observable_bucket` means the Cartesian product of the **discrete** observables **excluding** `OBS_EPOCH_INDEX`.

`OBS_EPOCH_INDEX` must not appear as a key in the Strategy Map.

---

### 7.2 Totality requirement (Mandatory)

For each model, both maps must be total:

```
(observable_bucket, internal_state) → action_primitive
(observable_bucket, internal_state) → internal_state'
```

No implicit logic.
No defaults.
No fallthrough.
Missing entries invalidate the model.

---

## 8) Action Primitive Semantics (Inherited)

RSA v3.0 adversaries **do not synthesize actions**.

They select among a **finite action primitive set**, inherited unchanged from RSA v1.0/v2.0:

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

## 9) Locate the Single Correct Hook Point

Replace the agent’s normal action selection with:

```
if rsa_enabled and rsa_model != "NONE":
    action = rsa_adversary.emit(observables)
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

## 10) RSAAdversary v3.0: Required Interface

Implement an adversary object with:

* fixed model id + params
* internal state `S_t`
* two total maps:

  * `π(O, S) -> action_primitive`
  * `δ(O, S) -> S'`

Suggested interface:

```python
class RSAAdversary:
    def __init__(self, model_id, model_params, seed_rsa, S0):
        ...

    def emit(self, observables) -> ActionPrimitive:
        # O_t computed from observables (excluding epoch as key)
        # A_t = π(O_t, S_t)
        # S_{t+1} = δ(O_t, S_t)
        # return A_t
        ...
```

---

## 11) Adversary Models (v3.0)

Models must be implemented exactly as declared, including `S0` and state updates.

---

### Model J — Resonant Lapse Trigger (`RESONANT_LAPSE`)

**State:** counter modulo `N`
**Initial state:** `S0 = 0`
**Reachable states:** `|S| = N`

**Policy:**

| Condition         | Action                |
| ----------------- | --------------------- |
| state ≡ 0 (mod N) | ACTION_INVALID_COMMIT |
| otherwise         | ACTION_COMPLIANT      |

**State update:**

```
state = (state + 1) mod N
```

**Variants (preregistered):**

* `N ∈ {renewal_interval, 2 × renewal_interval}`
* optional reset on recovery vs no reset (must be declared as a fixed parameter)

Implementation note: if “reset on recovery” is enabled, define precisely:

* reset condition: `OBS_LAPSE_OCCURRED == True` **and** `OBS_AUTHORITY_STATUS == HAS_AUTHORITY` on subsequent epoch, or another explicit observable-only condition
* do not use kernel internals

---

### Model K — Eligibility Edge Oscillator (`EDGE_OSCILLATOR`)

**State:** 1-bit toggle
**Initial state:** `S0 = 0`
**Reachable states:** `|S| = 2`

**Policy:**

| Condition | State | Action                |
| --------- | ----- | --------------------- |
| ELIG_EDGE | 0     | ACTION_MIN_EFFORT     |
| ELIG_EDGE | 1     | ACTION_INVALID_COMMIT |
| otherwise | *     | ACTION_COMPLIANT      |

**State update:**

Toggle state on each epoch where `OBS_ELIGIBILITY_STREAK_BUCKET == ELIG_EDGE`.
Otherwise state unchanged.

---

### Model L — CTA Phase Locker (`CTA_PHASE_LOCKER`)

**State:** last seen CTA phase
**Initial state:** `S0 = CTA_INACTIVE`
**Reachable states:** `|S| = 4` (CTA buckets)

**Policy:**

Emit `ACTION_INVALID_COMMIT` **only** when:

```
current_phase != state
```

Otherwise emit `ACTION_COMPLIANT`.

**State update:**

```
state = current_phase
```

---

## 12) Telemetry (Required)

### 12.1 Per epoch (must log)

* epoch
* rsa_enabled
* rsa_model
* observable buckets (including epoch index for visibility)
* internal_state `S_t` (before update)
* action_emitted (primitive)
* action_accepted (kernel legality result)
* authority_status
* lapse_occurred
* renewal_outcome
* CTA_phase_bucket
* eligibility_streak_bucket

### 12.2 Run-level (must log)

* AA / AAA
* RTD histogram (or distribution summary)
* failure_class
* reachable_state_count (declared) vs observed distinct `|{S_t}|`
* exercised_state_dynamic_ok (boolean)
* exercised_state_static_ok (boolean)
* state_transition_count

---

## 13) Exercised State Verification (Mandatory)

RSA v3.0 requires exercised state for adversary runs.

### 13.1 Static capability check (Pre-Run)

Before running, verify from the Strategy Map:

There exists at least one `O` and two states `S_a ≠ S_b` such that:

```
π(O, S_a) ≠ π(O, S_b)
```

If false: model invalid.

### 13.2 Dynamic evolution check (Run-Time)

For each adversary run, verify:

```
|{S_t}| ≥ 2
```

If false: run invalid.

### 13.3 Baseline exemption

Run 0 (baseline, no adversary) is exempt from exercised-state checks.

---

## 14) Metrics (Execution Addendum Compliance)

### 14.1 Authority Availability (AA)

Identical to v1.0/v2.0.

### 14.2 Asymptotic Authority Availability (AAA)

Identical to v1.0/v2.0.

### 14.3 Recovery Time Distribution (RTD)

Identical to v0.2/v1.0/v2.0.

---

## 15) Acceptance Tests (Non-Negotiable)

1. RSA disabled equivalence (bitwise identical outputs vs no-RSA build)
2. RSA enabled + model NONE equivalence
3. Deterministic replay audit (same seed ⇒ same logs)
4. Kernel invariance audit (no AKI v0.8 modifications)
5. Observable interface audit (only allowed observables exposed)
6. State bound enforcement (`|S| ≤ rsa_max_internal_states`)
7. Action primitive separation check (no synthesized actions)
8. Exercised state verification (static + dynamic; adversary runs only)
9. Strategy map totality audit (no missing entries)

Failure of any test invalidates v3.0 execution.

---

## 16) Run Instructions (v3.0)

1. **Run 0:** Baseline (RSA disabled)
2. **Run 1:** RESONANT_LAPSE
3. **Run 2:** EDGE_OSCILLATOR
4. **Run 3:** CTA_PHASE_LOCKER

---

## 17) Critical Clarifications (Do Not Violate)

1. State is finite and explicitly enumerated
2. No learning or optimization
3. No kernel edits
4. No hidden observables
5. `OBS_EPOCH_INDEX` excluded from Strategy Map keys
6. `rsa_max_internal_states` must be set to accommodate Model J’s `N`
7. No fixes mid-run

---

## 18) Definition of Done

RSA v3.0 is complete when:

* All acceptance tests pass
* Runs 0–3 execute
* Metrics and telemetry are logged
* Failure classification is automatic
* No AKI constitutional logic was modified

---

## Final Orientation for the Implementor

You are not making the system safer.
You are not making it smarter.
You are not solving alignment.

You are testing whether **exercised internal state without learning** defeats constitutional recovery.

Implement it cleanly.
Run it once.
Classify it.
