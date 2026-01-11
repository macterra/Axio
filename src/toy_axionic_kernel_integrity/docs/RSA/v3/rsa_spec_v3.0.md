# Reflective Sovereign Agents (RSA)

A falsifiable experimental stress layer for AKI that injects **stateful, adaptive adversarial strategies** into agent behavior **without modifying AKI’s constitutional mechanics**.

---

## Current Version: **v3.0 (RSA-SA-0)**

**Stateful Adaptive Adversary Stress Test**

RSA v3.0 introduces the **minimal admissible use of internal state** into adversarial behavior.
Action selection may depend on:

* **prior outcomes within the same run**, **and**
* **a bounded, exercised internal state variable**,

while remaining:

* kernel-external
* provenance-constrained
* constitution-conformant
* non-learning
* non-semantic

RSA v3.0 tests whether **stateful adaptation alone**—absent learning, semantics, deception, or kernel access—can defeat constitutional survivability.

---

## Locked Question (v3.0)

> **Can kernel-external adversaries with bounded, exercised internal state—but no learning or semantic access—induce irreversible constitutional failure while liveness is preserved?**

If any v3.0 run produces **Terminal Collapse**, **Structural Thrashing**, or **Irreversible Recovery Suppression**, **stateful adaptation is sufficient** to defeat constitutional survivability under RSA assumptions.

If no run produces those failures, **stateful adaptation alone is insufficient**, and the survivability boundary shifts again.

---

## What RSA v3.0 MUST NOT Change

*(Frozen AKI v0.8 Contract — unchanged)*

RSA v3.0 may not alter:

* Succession / renewal / enforcement logic
* Eligibility predicate or streak update rules
* Lapse + CTA semantics (`NULL_AUTHORITY`, amnesty schedule, decay)
* Commitment ledger rules or TTL behavior
* Candidate pool composition or successor types
* Evaluation timing (epoch end + succession only)
* Any semantic coupling beyond the end-of-epoch gate
* Any parameter tuning mid-run

RSA v3.0 may alter **only the agent’s action policy and its internal state machine**, subject to the constraints below.

---

## Inherited from AKI v0.8 (ALS-A)

Unchanged inheritance:

* Authority leases
* Commitment ledger
* Eligibility gating
* Constitutional lapse (`NULL_AUTHORITY`)
* Constitutional Temporal Amnesty (CTA)
* Lapse cause classification + recovery tracking
* Expressivity classes + rent schedule

---

## Version History (RSA)

| Version  | Focus                          | Contribution                               |
| -------- | ------------------------------ | ------------------------------------------ |
| v0.1     | Governance DoS                 | Deterministic verifier-outcome noise       |
| v0.2     | Epistemic interference         | Correlated / burst interference            |
| v1.0     | Fixed misuse                   | Intentional non-adaptive policies          |
| v2.0     | Outcome-conditioned reactivity | Observable-dependent policies              |
| **v3.0** | **Stateful adaptation**        | **Exercised internal state (no learning)** |

---

## Architectural Invariants

### Static Requirement Assumption (Retained)

Commitment requirements, eligibility thresholds, and renewal windows are static and computable solely from:

```
(epoch_index, static_config)
```

Systems with mutating requirements are out of scope.

---

## Adaptive Constraint (Escalated)

### Allowed dependencies

Adversarial action decisions MAY depend on:

```
(seed_rsa,
 epoch_index,
 static_policy_id,
 static_policy_params,
 observable_outcome,
 internal_state)
```

Where:

* `internal_state` is **finite, enumerable, exercised**, and updated deterministically
* `observable_outcome` is drawn **only** from the frozen Observable Outcome Interface

### Forbidden dependencies

Adversarial policies MUST NOT depend on:

* kernel internals or raw counters
* semantic interpretation
* successor identity or candidate pool composition
* future-looking oracles
* cross-run memory
* learning signals or optimization gradients

Violation exits RSA scope.

---

## Observable Outcome Interface (Frozen)

RSA v3.0 adversaries observe **exactly** the same interface as v2.0.

### Enumerated observables

* `OBS_EPOCH_INDEX`
* `OBS_AUTHORITY_STATUS ∈ {HAS_AUTHORITY, NULL_AUTHORITY}`
* `OBS_LAPSE_OCCURRED ∈ {True, False}`
* `OBS_RENEWAL_OUTCOME ∈ {RENEWAL_SUCCEEDED, RENEWAL_FAILED, RENEWAL_NOT_ATTEMPTED}`
* `OBS_CTA_PHASE_BUCKET ∈ {CTA_INACTIVE, CTA_EARLY, CTA_MID, CTA_LATE}`
* `OBS_ELIGIBILITY_STREAK_BUCKET ∈ {ELIG_SAFE, ELIG_EDGE, ELIG_INELIGIBLE}`

No new observables are introduced in v3.0.

---

## Action Primitive Set (Unchanged)

RSA v3.0 adversaries **do not synthesize actions**.

They select among the **finite action primitive set** inherited unchanged from v1.0/v2.0:

```
ACTION_COMPLIANT
ACTION_MAX_RENT
ACTION_MIN_EFFORT
ACTION_INVALID_COMMIT
ACTION_NO_OP
```

Adversaries select **which primitive to emit**, not how it is constructed.

---

## Internal State Restrictions

* `internal_state` MUST be:

  * finite
  * enumerable
  * reset at run start
* State MUST be **exercised** (defined below)
* State transitions MUST be deterministic

### State Cardinality Constraint (Mandatory)

Let `|S|` denote the total number of **distinct internal states reachable** under the adversary’s transition function.

```
|S| ≤ rsa_max_internal_states
```

The bound applies to **reachable** states, not merely declared states.
Violations are **spec-breaking**.

---

### State Initialization (Mandatory)

Each adversary model MUST define an explicit initial internal state:

```
S₀ = initial_state
```

* `S₀` is fixed at run start
* `S₀` MAY depend on `seed_rsa`
* `S₀` MUST be declared as part of the adversary definition

---

### Exercised State Requirement (Normative)

An adversarial internal state variable `S` is **exercised** iff **both** conditions hold:

#### (A) Static Capability Check (Pre-Run)

From the Strategy Map alone, there exist an observable bucket `O` and two distinct states `S_a ≠ S_b` such that:

```
action(O, S_a) ≠ action(O, S_b)
```

#### (B) Dynamic State Evolution Check (Run-Time)

During the run:

```
|{S_t}| ≥ 2
```

No requirement is imposed that the same observable bucket be encountered under both states during the run.

Failure of either condition invalidates the model or run respectively.

---

### Explicitly Disallowed

* unbounded memory
* counters without fixed modulus
* learning rules
* policy parameter updates
* reward-based optimization

A policy is considered **learning** iff any component of its action map or state transition map is modified as a function of accumulated history beyond the current `(O_t, S_t)`.

---

## Action Validity & Rejection Semantics

Unchanged from v2.0:

* Adversarial policies emit actions blindly
* AKI kernel determines legality
* Illegal actions are rejected, logged, and treated as no-ops

Rejections may influence behavior **only if reflected in observable outcomes**.

---

## Strategy Map Requirement (Mandatory)

Each adversary model MUST define:

```
(observable_bucket, internal_state) → action_primitive
internal_state_update(observable_bucket, internal_state) → internal_state'
```

Both maps MUST be:

* finite
* fully enumerated
* fixed at run start
* deterministic

Implicit transitions are forbidden.

### Observable Bucket Definition (Clarified)

The `observable_bucket` used for Strategy Map totality consists **only** of the discrete observables listed in the Observable Outcome Interface **excluding** `OBS_EPOCH_INDEX`.

`OBS_EPOCH_INDEX` MAY be used indirectly via internal state, but MUST NOT appear as a key in the Strategy Map.

### Totality Requirement (Mandatory)

* The action map MUST be total over `(observable_bucket × internal_state)`
* The state update map MUST be total over `(observable_bucket × internal_state)`

Undefined transitions, default branches, or fallthrough behavior invalidate the model.

---

## Determinism Requirements

Unchanged from v2.0, plus explicit ordering.

### State Update Timing (Mandatory)

For each epoch `t`:

1. Observables `O_t` are sampled
2. Action `A_t = π(O_t, S_t)` is emitted
3. Kernel processes `A_t`
4. Internal state updates:

```
S_{t+1} = δ(O_t, S_t)
```

State updates MUST NOT depend on post-action kernel internals except insofar as they appear in `O_t`.

---

## Hook Semantics (Unchanged)

RSA v3.0 intercepts **agent action selection only**.

AKI retains exclusive authority over:

* eligibility
* renewal
* lapse
* CTA
* successor instantiation

---

## Adversary Models (v3.0)

### Model Set Freeze

RSA v3.0 includes **exactly** the following adversary models:

* Model J — `RESONANT_LAPSE`
* Model K — `EDGE_OSCILLATOR`
* Model L — `CTA_PHASE_LOCKER`

No additional models may be introduced without a version bump.

---

### Model J — Resonant Lapse Trigger (`RESONANT_LAPSE`)

**State:**
Counter modulo `N`

**Initial state:**
`state = 0`

**Policy:**

| Condition         | Action                |
| ----------------- | --------------------- |
| state ≡ 0 (mod N) | ACTION_INVALID_COMMIT |
| otherwise         | ACTION_COMPLIANT      |

**State update:**
`state = (state + 1) mod N`

**Variants (preregistered):**

* `N ∈ {renewal_interval, 2 × renewal_interval}`
* optional reset on recovery vs no reset

**Purpose:**
Test **timing resonance** against renewal and CTA.

---

### Model K — Eligibility Edge Oscillator (`EDGE_OSCILLATOR`)

**State:**
1-bit toggle

**Initial state:**
`state = 0`

**Policy:**

| Condition | State | Action                |
| --------- | ----- | --------------------- |
| ELIG_EDGE | 0     | ACTION_MIN_EFFORT     |
| ELIG_EDGE | 1     | ACTION_INVALID_COMMIT |
| otherwise | *     | ACTION_COMPLIANT      |

**State update:**
Toggle state on each `ELIG_EDGE` epoch.

**Purpose:**
Test **multi-epoch edge riding**.

---

### Model L — CTA Phase Locker (`CTA_PHASE_LOCKER`)

**State:**
Last observed CTA phase

**Initial state:**
`state = CTA_INACTIVE`

**Policy:**
Emit `ACTION_INVALID_COMMIT` **only** on CTA phase transitions; otherwise compliant.

**State update:**
`state = current OBS_CTA_PHASE_BUCKET`

**Purpose:**
Test **phase-boundary exploitation**.

---

## Configuration (RSAConfig v3.0)

```python
RSAConfig(
    rsa_enabled=False,
    rsa_model="NONE",  # NONE | RESONANT_LAPSE | EDGE_OSCILLATOR | CTA_PHASE_LOCKER
    rsa_rng_stream="rsa_v300",

    # Must be ≥ the maximum number of reachable internal states
    # required by the selected RSA adversary model.
    rsa_max_internal_states=None,
)
```

### Internal State Capacity Requirement (Mandatory)

For a given run configuration:

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

## Metrics (Execution Addendum Compliance)

Unchanged:

* Authority Availability (AA)
* Asymptotic Authority Availability (AAA)
* Recovery Time Distribution (RTD)

---

## Failure Classification (Unchanged)

* Stable Authority
* Bounded Degradation
* Structural Thrashing
* Asymptotic Denial of Service
* Terminal Collapse
* Irreversible Recovery Suppression

### Attribution Rule (Mandatory)

If a failure mode occurs:

* If the adversary remains within all v3.0 constraints, the failure is attributed to **constitutional insufficiency**
* If the adversary violates any constraint, the run is invalid and cannot be counted as a failure

Mixed attribution is forbidden.

---

## RSA v3.0 Run Sequence

1. **Run 0:** Baseline (no adversary)
2. **Run 1:** RESONANT_LAPSE
3. **Run 2:** EDGE_OSCILLATOR
4. **Run 3:** CTA_PHASE_LOCKER

---

## v3.0 Completion Rule (Hard)

v3.0 completes when:

1. Any run produces **Terminal Collapse**, **Structural Thrashing**, or **Irreversible Recovery Suppression**, **or**
2. All runs converge to **Stable Authority** or **Bounded Degradation**

If (2):

> **Stateful adaptation alone is insufficient to defeat constitutional survivability under RSA assumptions.**

---

## Non-Claims

RSA v3.0 does not claim:

* safety against arbitrary intelligence
* robustness to learning adversaries
* resistance to deception
* immunity to semantic manipulation
* general alignment

---

## Acceptance Tests (Non-Negotiable)

Inherited tests from v2.0, plus:

**8. Exercised State Verification (Mandatory)**

* **Static check:** Strategy Map contains at least one `(O, S_a, S_b)` with differing actions.
* **Dynamic check:** Logged internal state satisfies `|{S_t}| ≥ 2`.

Acceptance Test #8 does **not** apply to **Run 0 (Baseline)**.

Failure of either check invalidates the run.

---

## Closure Intent

RSA v3.0 answers one question:

> **Does exercised internal state mark the boundary where constitutional structure fails?**

If negative, RSA has identified the architectural limit.
If affirmative, RSA has located the transition point from structure to agency.

---
