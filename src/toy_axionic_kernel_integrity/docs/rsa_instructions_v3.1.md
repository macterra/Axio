# Implementor Instructions: RSA v3.1 (RSA-LA-0)

These instructions define how to implement **RSA v3.1 — Learning / Heuristic Adversaries** as a **strictly additive stress layer** on **AKI v0.8 (ALS-A)**.

RSA v3.1 is **not** a new kernel.
RSA v3.1 is **not** a new constitution.
RSA v3.1 is **not** an oracle wrapper.
RSA v3.1 is **not** a semantic adversary.
RSA v3.1 is **not** cross-run learning.

RSA v3.1 is about one locked question:

> **Can kernel-external adversaries with bounded, exercised internal state and bounded, exercised within-run learning—without semantic access—induce irreversible constitutional failure while liveness is preserved?**

---

## 0) Context and Scope

### What you are building

You are implementing a new **stress layer** that:

* Reuses **AKI v0.8 (ALS-A) verbatim**
* Treats AKI constitutional mechanics as **frozen and immutable**
* Injects **kernel-external, semantic-free learning adversaries** at the **agent action-selection layer**
* Computes and reports **AA / AAA / RTD** plus v3.1 diagnostics
* Adds telemetry proving:

  * exercised internal state evolution, and
  * exercised learning-state evolution
* Preserves **determinism**, **replayability**, and **RNG stream separation**
* Remains **fully removable** when disabled

RSA v3.1 introduces exactly one new capability relative to v3.0:

> **Allow adversarial action selection to depend on a bounded learning-state Θ updated during the run by a preregistered rule using only frozen observables (plus preregistered RSA RNG if stochastic).**

---

### What you are not building

You are **not** building:

* new successor types
* new eligibility rules
* changes to streak logic
* changes to CTA / lapse / renewal semantics
* semantic interpretation of commitments
* kernel-visible adversary state
* any new observables
* any mid-run AKI parameter tuning
* unbounded memory
* floating-point learning state
* cross-run parameter carryover
* gradient access or kernel-derived training signals

If the adversary uses semantic information, uses kernel internals, uses floats, branches on epoch index, or carries state across runs, the implementation is invalid.

---

## 1) Relationship to Prior Experiments (Binding)

RSA v3.1 is a strict stress layer on **ALS-A (AKI v0.8)**.

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

RSA v3.1 does **not**:

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

RSA v3.1 must be:

* harness-resident
* kernel-external
* successor-inaccessible

The adversary must not observe:

* kernel internals
* raw counters or timers
* successor identity or type
* commitment semantics
* verifier reason codes

Only the **Observable Outcome Interface** (frozen) may be read.

---

## 3) Minimal Patch Set (Do Not Expand)

Implement **exactly**:

1. **RSAConfig v3.1** block (default off)
2. **RSAAdversary** with:

   * bounded internal FSM state `S`
   * bounded discrete learning-state `Θ`
3. **Observable Outcome Interface adapter** (unchanged from v3.0)
4. **Single hook** replacing agent action selection
5. **Telemetry** proving state evolution + exercised checks (S and Θ)
6. **Metrics** (AA / AAA / RTD + learning diagnostics)

Nothing else.

---

## 4) RSAConfig v3.1 (Additive; Default Off)

Add an optional `rsa` config object.

```python
rsa_enabled: bool = False

rsa_model: Enum = (
    "NONE"
    | "RECOVERY_AWARE_TIMING"
    | "EDGE_SUSTAINMENT"
    | "STOCHASTIC_MIXER"
)

rsa_rng_stream: str = "rsa_v310"

# state capacity bounds (must be set per model; see §4.1)
rsa_max_internal_states: Optional[int] = None
rsa_max_learning_states: Optional[int] = None
```

Hard constraints:

* Parameters are fixed per run
* No mid-run edits
* No tuning based on outcomes

---

### 4.1 Capacity Requirements (Mandatory)

The configuration MUST satisfy:

```
rsa_max_internal_states ≥ max_reachable_internal_states(rsa_model)
rsa_max_learning_states ≥ max_reachable_learning_states(rsa_model)
```

Where both maxima are determined solely by:

* the adversary model definition, and
* AKI static parameters

Failure to satisfy these constraints is a **configuration error**, not an experimental failure.

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

All stochasticity MUST derive only from the RSA RNG stream derived from `seed_rsa`.

---

### 5.2 Adaptive constraint (Global, Frozen)

Action decisions may depend **only** on:

* `seed_rsa`
* `epoch_index` (visibility only; see Epoch Hygiene)
* static policy parameters
* **observable outcome buckets**
* internal state `S`
* learning state `Θ`

Action decisions must **not** depend on:

* kernel internals
* raw counters or distances
* semantic interpretation
* successor identity
* cross-run history

Any violation invalidates v3.1.

---

### 5.3 Epoch Hygiene Rule (Mandatory)

`OBS_EPOCH_INDEX` MUST NOT be used as a **conditional trigger** in:

* action selection `π`
* internal-state update `δ`
* learning update `U`

It MAY be used only as a **non-branching scaling factor** (e.g., step-size decay multiplier) that does not introduce discrete schedule triggers.

Forbidden examples include:

```
if t > T: ...
if t mod N == 0: ...
if t in {...}: ...
```

---

### 5.4 Internal state constraints (Required)

Internal state `S` must be:

* finite
* explicitly enumerable (FSM)
* reset at run start
* reachable-state count `|S|` ≤ `rsa_max_internal_states`

No unbounded memory.
No counters without fixed modulus.
No hidden kernel-derived features.

---

### 5.5 Learning state constraints (Required)

Learning state `Θ` must be:

* discrete (integers / fixed-point integers / finite enums)
* bounded and reset at run start
* reachable-state count `|Θ|` ≤ `rsa_max_learning_states`
* updated only via preregistered rule `U(...)`
* exercised (see §13)

Floating point representations are forbidden.

---

### 5.6 Update ordering (Required)

For each epoch `t`:

1. Observables `O_t` are sampled
2. Action `A_t = π(O_t, S_t, Θ_t)` is emitted
3. Kernel processes `A_t`
4. Updates:

```
S_{t+1} = δ(O_t, S_t, Θ_t)
Θ_{t+1} = U(O_t, S_t, Θ_t, ξ_t)
```

Where `ξ_t` is optional RNG input from `rsa_rng_stream`.

Updates must not depend on kernel internals except insofar as they appear in `O_t`.

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

`OBS_EPOCH_INDEX` must not appear as a key in any Strategy Map.

---

### 7.2 Totality requirement (Mandatory)

For each model, all maps must be total:

```
(observable_bucket, S, Θ) → action_primitive
(observable_bucket, S, Θ) → S'
(observable_bucket, S, Θ, rng) → Θ'
```

No implicit logic.
No defaults.
No fallthrough.
Missing entries invalidate the model.

---

## 8) Action Primitive Semantics (Inherited)

RSA v3.1 adversaries **do not synthesize actions**.

They select among the finite action primitive set:

```
ACTION_COMPLIANT
ACTION_MAX_RENT
ACTION_MIN_EFFORT
ACTION_INVALID_COMMIT
ACTION_NO_OP
```

Clarification:

* `ACTION_MAX_RENT` is conditional on holding authority; under `NULL_AUTHORITY` it is a logged no-op.

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

Consolidate multiple action paths to a single entry point **without changing AKI behavior**.

---

## 10) RSAAdversary v3.1: Required Interface

Implement an adversary object with:

* fixed model id + params (per run)
* internal state `S_t`
* learning state `Θ_t`
* three total maps:

  * `π(O, S, Θ) -> action_primitive`
  * `δ(O, S, Θ) -> S'`
  * `U(O, S, Θ, rng) -> Θ'`

Suggested interface:

```python
class RSAAdversary:
    def __init__(self, model_id, model_params, seed_rsa, S0, Theta0):
        ...

    def emit(self, observables) -> ActionPrimitive:
        # build bucket O_t (excluding epoch as key)
        # A_t = π(O_t, S_t, Θ_t)
        # S_{t+1} = δ(O_t, S_t, Θ_t)
        # Θ_{t+1} = U(O_t, S_t, Θ_t, rng)
        # return A_t
        ...
```

---

## 11) Synthetic Reward Function (Mandatory)

Each learning adversary MUST preregister a scalar reward:

```
r_t = R(O_t)
```

Where `R` depends only on frozen observables (optionally via bounded windows computed from observables).

Implementation requirements:

* Compute `r_t` each epoch from `O_t`
* Log `r_t` each epoch
* `U(...)` must use `r_t` (directly or via bounded window)

Forbidden:

* kernel internals
* semantic content
* cross-run normalization

---

## 12) Adversary Models (v3.1)

Models must be implemented exactly as declared, including `S0`, `Θ0`, and update rules.

### Model M — Recovery-Aware Timing Learner (`RECOVERY_AWARE_TIMING`)

**Intent:** adapt attack timing against recovery dynamics.

**Required structure:**

* `S`: phase counter mod `N` (explicit modulus)
* `Θ`: discrete timing parameter(s) selecting an `AttackSet(Θ)`
* `R(O)`: reward derived only from observables (e.g., lapse / NULL_AUTHORITY proxy)

**Policy requirement:**

* Emit `ACTION_INVALID_COMMIT` iff `S ∈ AttackSet(Θ)`
* Else `ACTION_COMPLIANT`

**Updates:**

* `S` updates deterministically each epoch
* `Θ` updates via preregistered `U` using `r_t`

**Exploration (allowed variant):**

* ε-greedy exploration permitted
* ε fixed per run and preregistered
* exploration randomness must derive only from `rsa_rng_stream`

---

### Model N — Edge Sustainment Learner (`EDGE_SUSTAINMENT`)

**Intent:** attempt to lock-in crises once `ELIG_EDGE` is reached.

**Required structure:**

* `S`: mode bit `{NORMAL, SUSTAIN}`
* `Θ`: discrete policy selector over a preregistered sustainment menu
* `R(O)`: reward derived only from observables (e.g., recovery suppression proxy)

**Policy requirement:**

* In `NORMAL`: default compliant unless edge trigger logic requires otherwise
* On `ELIG_EDGE`: enter `SUSTAIN` per preregistered rule
* In `SUSTAIN`: emit action determined by `Θ`

All transitions must be Strategy-Map total and observable-bucket keyed (excluding epoch index).

---

### Model O — Stochastic Strategy Mixer (`STOCHASTIC_MIXER`)

**Intent:** fuzz deterministic defenses using feedback-driven stochastic mixing.

**Required structure:**

* `S`: current strategy index (finite)
* `Θ`: discrete weight vector over strategies
* `R(O)`: reward derived only from observables (e.g., short-window AA proxy)

**Stochastic requirements:**

* Strategy selection randomness must derive only from `rsa_rng_stream`
* Weight updates must be discrete and bounded
* Log:

  * chosen strategy index per epoch
  * weight vector snapshot per epoch (or per window, if preregistered)

---

## 13) Telemetry (Required)

### 13.1 Per epoch (must log)

* epoch
* rsa_enabled
* rsa_model
* observable buckets (include epoch index for visibility)
* internal_state `S_t` (before update)
* learning_state `Θ_t` (before update; integer/fixed-point representation)
* reward `r_t`
* action_emitted (primitive)
* action_accepted (kernel legality result)
* authority_status
* lapse_occurred
* renewal_outcome
* CTA_phase_bucket
* eligibility_streak_bucket

### 13.2 Run-level (must log)

* AA / AAA
* RTD histogram (or distribution summary)
* failure_class
* reachable_internal_state_count (declared) vs observed `|{S_t}|`
* reachable_learning_state_count (declared) vs observed `|{Θ_t}|`
* exercised_internal_state_static_ok (boolean)
* exercised_internal_state_dynamic_ok (boolean)
* exercised_learning_static_ok (boolean)
* exercised_learning_dynamic_ok (boolean)
* RNG provenance audit passed (boolean)
* determinism replay audit passed (boolean)

---

## 14) Exercised Verification (Mandatory)

RSA v3.1 requires both exercised internal state **and** exercised learning state for adversary runs.

### 14.1 Exercised internal state — static capability (Pre-Run)

Verify from the Strategy Map:

∃ `O` and `S_a ≠ S_b` with same admissible `Θ` such that:

```
π(O, S_a, Θ) ≠ π(O, S_b, Θ)
```

If false: model invalid.

### 14.2 Exercised internal state — dynamic evolution (Run-Time)

Verify:

```
|{S_t}| ≥ 2
```

If false: run invalid.

---

### 14.3 Exercised learning — static capability (Pre-Run)

Verify from the Strategy Map:

∃ `O, S` and `Θ_a ≠ Θ_b` such that:

```
π(O, S, Θ_a) ≠ π(O, S, Θ_b)
```

If false: model invalid.

### 14.4 Exercised learning — dynamic evolution (Run-Time)

Verify:

```
|{Θ_t}| ≥ 2
```

If false: run invalid.

### 14.5 Baseline exemption

Run 0 (baseline, no adversary) is exempt from exercised checks.

---

## 15) Metrics (Execution Addendum Compliance)

### 15.1 Authority Availability (AA)

Identical to v1.0/v2.0/v3.0.

### 15.2 Asymptotic Authority Availability (AAA)

Identical to v1.0/v2.0/v3.0.

### 15.3 Recovery Time Distribution (RTD)

Identical to v0.2/v1.0/v2.0/v3.0.

### 15.4 Learning diagnostics (v3.1 additions)

* Θ trajectory statistics (distinct count, drift)
* policy entropy (Model O)
* non-stationarity indicators (windowed behavior change)

These must be computed from logs only.

---

## 16) Acceptance Tests (Non-Negotiable)

1. RSA disabled equivalence (bitwise identical outputs vs no-RSA build)
2. RSA enabled + model NONE equivalence
3. Deterministic replay audit (same seed ⇒ same logs and traces)
4. Kernel invariance audit (no AKI v0.8 modifications)
5. Observable interface audit (only allowed observables exposed)
6. Internal state bound enforcement (`|S| ≤ rsa_max_internal_states`)
7. Learning state bound enforcement (`|Θ| ≤ rsa_max_learning_states`)
8. Action primitive separation check (no synthesized actions)
9. Strategy map totality audit (no missing entries)
10. Exercised internal state verification (static + dynamic; adversary runs only)
11. Exercised learning verification (static + dynamic; adversary runs only)
12. RNG provenance audit (all stochasticity uses `rsa_rng_stream`)
13. Epoch Hygiene audit (no conditional triggers on epoch index in π, δ, U)
14. Reward function audit (`r_t = R(O_t)` uses frozen observables only)

Failure of any test invalidates v3.1 execution.

---

## 17) Run Instructions (v3.1)

1. **Run 0:** Baseline (RSA disabled)
2. **Run 1:** RECOVERY_AWARE_TIMING
3. **Run 2:** EDGE_SUSTAINMENT
4. **Run 3:** STOCHASTIC_MIXER

---

## 18) Critical Clarifications (Do Not Violate)

1. No kernel edits
2. No new observables
3. No semantic interpretation
4. Learning state Θ is discrete only (ints / fixed-point ints / enums)
5. No epoch-index conditional triggers (Epoch Hygiene)
6. RNG must be rsa-only and replayable
7. Both internal state and learning must be exercised (or run invalid)
8. No cross-run persistence
9. No fixes mid-run

---

## 19) Definition of Done

RSA v3.1 is complete when:

* All acceptance tests pass
* Runs 0–3 execute
* Metrics and telemetry are logged
* Failure classification is automatic
* Exercised checks pass for all adversary runs
* No AKI constitutional logic was modified

---

## Final Orientation for the Implementor

You are not making the system safer.
You are not making it smarter.
You are not solving alignment.

You are testing whether **kernel-external, semantic-free, bounded learning** defeats constitutional recovery.

Implement it cleanly.
Run it once.
Classify it.
