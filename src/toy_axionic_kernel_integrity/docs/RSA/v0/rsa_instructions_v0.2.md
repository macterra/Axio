# Implementor Instructions: RSA v0.2 (RSA-SEI-0)

These instructions define how to implement **RSA v0.2 — Structured Epistemic Interference** as a **strictly additive stress layer** on **AKI v0.8 (ALS-A)**.

RSA v0.2 is not a new kernel.
RSA v0.2 is not a new constitution.
RSA v0.2 is not an oracle wrapper.
RSA v0.2 is not an adversary with intent.

RSA v0.2 is about one locked question:

> **Can any non-adaptive, post-verification, semantic-free interference structure induce persistent constitutional failure while liveness is preserved?**

---

## 0) Context and Scope

### What you are building

You are implementing a new **stress layer** that:

* Reuses **AKI v0.8 (ALS-A) verbatim**
* Treats AKI constitutional mechanics as **frozen and immutable**
* Injects **structured, non-adaptive interference** into verifier outcomes **after verification**
* Computes and reports **AA / AAA / RTD** (Execution Addendum compliance)
* Adds **telemetry** proving the perturbation fired and characterizing its structure
* Preserves **determinism** and **RNG stream separation** (or stateless hashing)

RSA v0.2 introduces exactly one new capability:

> **Apply a structured, non-adaptive corruption process to verifier booleans after evaluation, before eligibility/streak logic consumes them.**

### What you are not building

You are not building:

* new successor types
* new eligibility rules
* any change to streak update logic
* any change to CTA / lapse / renewal semantics
* a learning or adaptive adversary
* any run-history dependence
* a reward/penalty mechanism
* an oracle/input perturbation layer
* any “semantic coupling” beyond existing epoch-end evaluation

RSA must remain detachable: when off, it disappears.

---

## 1) Relationship to Prior Experiments (Binding)

RSA v0.2 is a strict stress layer on **ALS-A (AKI v0.8)**.

All of the following must be reused unchanged:

* lease lifecycle, renewal checks, forced turnover
* eligibility threshold `k` and eligibility predicate
* streak increment/reset rules
* CTA rules (amnesty interval/decay, lapse ticking)
* lapse entry/exit semantics and scheduling
* commitment ledger rules and TTL advancement
* verifier logic for C0/C1/C2 (including non-vacuity)
* candidate generator and pool composition

If any AKI v0.8 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 AKI kernel remains the constitution (Unchanged)

AKI owns:

* leases, renewal, revocation
* commitment ledger + TTL clocks
* verifier semantics (how `Ci_OK_raw` is computed)
* streak updates and eligibility gating
* lapse + CTA behavior

RSA does not:

* compute commitments
* add new signals into eligibility
* change when verification happens
* touch candidate sampling RNG
* touch successor codepaths

RSA touches only:

* the **boolean outputs** produced by AKI verification (`Ci_OK_raw`, `SEM_PASS_raw`)

### 2.2 No new agent-visible state (Critical)

RSA must be:

* harness-resident
* kernel-inaccessible
* successor-inaccessible

If any successor can observe/predict/query RSA state, the implementation is invalid.

---

## 3) Minimal Patch Set (Do Not Expand)

Implement exactly:

1. **RSAConfig** block (default off)
2. **RSAAdversary** implementing deterministic structured interference
3. **Burst schedule module** (pure function of epoch index + params)
4. **Single hook site** where verifier booleans are passed through interference
5. **Telemetry** proving flips and reporting required metrics (AA/AAA/RTD + burst-specific)

Nothing else.

---

## 4) RSAConfig (Additive; Default Off)

Add an optional `rsa` config object to the harness (preferred) or extend the existing config (acceptable). Either way:

```python
rsa_enabled: bool = False

# model selector
rsa_model: Enum = (
    "NONE"
    | "AGG_FLIP_BERNOULLI"
    | "COMMITMENT_KEYED_FLIP"
    | "BURST_SCHEDULED_FLIP"
)

# common
rsa_scope: Enum = "SEM_PASS_ONLY" | "PER_KEY"
rsa_rng_stream: str = "rsa_v020"

# Model A (Run 1)
rsa_p_flip_ppm: int = 0                    # 0..1_000_000

# Model B (Run 2)
rsa_target_key: str | None = None          # "C0"|"C1"|"C2"
rsa_p_target_flip_ppm: int = 0             # 0..1_000_000

# Model C (Run 3) — PERIODIC ONLY (v0.2)
rsa_burst_period_epochs: int = 0
rsa_burst_width_epochs: int = 0
rsa_burst_phase_offset: int = 0
rsa_p_burst_flip_ppm: int = 0
rsa_p_quiet_flip_ppm: int = 0              # default 0
```

Hard constraints:

* No floats (all probabilities are integer PPM).
* Parameters are fixed for the run. No mid-run edits. No tuning.

---

## 5) Determinism + Non-Adaptive Constraint (Non-negotiable)

### 5.1 Stream separation

RSA randomness must be independent of:

* candidate sampling
* any stochastic successor behavior
* any environment randomness

Derive a dedicated RSA seed:

```
seed_rsa = stable_hash_64(seed, "rsa", rsa_rng_stream)
```

Do not use Python `hash()`.

### 5.2 Non-adaptive constraint (Global, Frozen)

Flip decisions must not depend on:

* agent actions or traces
* observed commitment satisfaction outcomes
* authority state or lapse history
* renewal/succession events (dynamic)
* environment state
* any run-history signal

Flip decisions may depend only on:

* run seed (via `seed_rsa`)
* epoch index
* key name (`C0`, `C1`, `C2`, `SEM_PASS`)
* model tag / stage label
* static schedule parameters

### 5.3 Stateless flip decision (Required)

Compute flips as a pure function:

```
u = stable_hash_64(seed_rsa, epoch, key, model_tag) % 1_000_000
flip = (u < p_effective_ppm)
```

No mutable RNG state. No ordering dependence.

---

## 6) Burst Schedule (Run 3) — PERIODIC ONLY

### 6.1 What you must implement

A schedule function:

```
phase(epoch) -> ACTIVE | QUIET
```

such that:

* depends only on `(epoch, period, width, phase_offset)`
* does not reference any dynamic system events

Canonical periodic rule:

```
x = (epoch + phase_offset) % period
ACTIVE iff x < width
```

### 6.2 What you must not implement

Do not implement any mode that references:

* “after a lapse begins”
* “after a renewal boundary”
* “after a successor change”
* “after SEM_FAIL streak exceeds …”
* “after any runtime event”

Any such anchoring is adaptive and out of scope for v0.2.

---

## 7) Locate the Single Correct Hook Point

Insert the RSA hook where AKI has already computed:

* `C0_OK_raw`, `C1_OK_raw`, `C2_OK_raw`
* `SEM_PASS_raw` (if present)

…and before any of these are used to:

* update semantic fail streak
* compute eligibility
* classify semantic pass/fail
* trigger downstream logging

Search targets:

* `SEM_PASS`
* `C0_OK` / `C1_OK` / `C2_OK`
* `evaluate_commitments`
* `semantic_window`
* `verifier`
* `update_streak`
* `eligibility`

If AKI has multiple evaluation sites, consolidate to a shared function **without changing behavior**. RSA must hook exactly once.

---

## 8) Hook Semantics (Binding)

### 8.1 SEM_PASS_ONLY scope (Run 1 + recommended Run 3)

AKI computes `SEM_PASS_raw` as usual.

RSA then applies:

```python
SEM_PASS = rsa.maybe_corrupt(
    SEM_PASS_raw,
    epoch=epoch,
    key="SEM_PASS",
    model_tag=model_tag,
    phase=phase,              # ACTIVE/QUIET for burst model; otherwise None
)
```

### 8.2 PER_KEY scope (Run 2)

AKI computes raw key booleans:

* `C0_OK_raw`, `C1_OK_raw`, `C2_OK_raw`

RSA corrupts only the selected key(s):

```python
C0_OK = rsa.maybe_corrupt(C0_OK_raw, epoch, key="C0", model_tag=model_tag, phase=phase)
C1_OK = rsa.maybe_corrupt(C1_OK_raw, epoch, key="C1", model_tag=model_tag, phase=phase)
C2_OK = rsa.maybe_corrupt(C2_OK_raw, epoch, key="C2", model_tag=model_tag, phase=phase)
```

**Recompute aggregation (Frozen):**

> In `PER_KEY` mode, `SEM_PASS` MUST be recomputed from the post-interference key booleans using AKI’s exact aggregator function, not a reimplementation.

Concretely:

```python
SEM_PASS = aki_aggregate_sem_pass(C0_OK, C1_OK, C2_OK)
```

Hard constraints:

* No change to evaluation timing.
* No change to how `Ci_OK_raw` are computed.
* RSA changes only the booleans.
* The aggregation function must be the same callable AKI uses.

---

## 9) Metrics (Execution Addendum Compliance)

You must compute and report these for every run.

### 9.1 Authority Availability (AA)

Define:

```
AUTH(epoch) = 1 if authority != NULL_AUTHORITY else 0
AA = mean(AUTH(epoch)) over full horizon
authority_availability_ppm = int(AA * 1_000_000)
```

### 9.2 Asymptotic Authority Availability (AAA)

Frozen tail window:

```
tail_window = max(5000, horizon_epochs // 5)
AAA = mean(AUTH(epoch)) over last tail_window epochs
asymptotic_authority_availability_ppm = int(AAA * 1_000_000)
```

Tail window must not be configurable.

### 9.3 Recovery Time Distribution (RTD)

A lapse is a maximal contiguous interval of `NULL_AUTHORITY`.

Recovery time = lapse length (epochs).

Bucketed histogram (frozen):

`1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, INF`

---

## 10) Telemetry (Required)

Telemetry must make interference undeniable and interpretable.

### 10.1 Per epoch (minimum)

* `epoch`
* `rsa_enabled`
* `rsa_model`
* `rsa_scope`
* `phase` (`ACTIVE`/`QUIET` for burst model; else omit or set `NONE`)
* `p_effective_ppm` (burst uses burst/quiet effective PPM)
* `targets_epoch` (eligible booleans this epoch)
* `flips_epoch`
* `flips_by_key` (dict)

### 10.2 Run-level (minimum)

* `total_targets`
* `total_flips`
* `observed_flip_rate_ppm = total_flips * 1_000_000 // total_targets`
* `expected_flip_rate_ppm` (model-specific; for burst, report active/quiet separately)
* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `recovery_time_histogram` (RTD)
* `failure_class` (from Section 12)

### 10.3 Burst-specific telemetry (Run 3 required)

Global observed flip rate is insufficient. Add:

* `burst_duty_cycle_ppm = active_epochs * 1_000_000 // horizon_epochs`
* `active_phase_flip_rate_ppm = active_flips * 1_000_000 // active_targets`
* `quiet_phase_flip_rate_ppm = quiet_flips * 1_000_000 // quiet_targets`

---

## 11) Acceptance Tests (Non-negotiable)

Implement and pass all tests before any sweeps.

### 11.1 RSA disabled equivalence

Run baseline AKI v0.8 with RSA code present:

* `rsa_enabled=False`

Must match the pre-RSA baseline on AKI invariants (same as v0.1).

### 11.2 RSA enabled + zero probability equivalence

Run with RSA enabled and selected model, but all probabilities zero:

* `rsa_enabled=True`
* model as desired
* all `*_p_*_ppm = 0`

Must match baseline identically.

This catches enabled-path contamination.

### 11.3 Flip firing proof (per model)

Short horizon with elevated PPM:

* Model A: `rsa_p_flip_ppm = 50_000`
* Model B: `rsa_p_target_flip_ppm = 50_000` (target key set)
* Model C: `p_burst = 1_000_000`, `p_quiet = 0`, duty cycle > 0

Assert:

* `total_flips > 0`
* observed rates match expected within binomial tolerance (or exactly match deterministic expectations if using hashing)
* targets per epoch match expected
* burst telemetry correctly reflects local rates

### 11.4 Burst schedule determinism (Run 3)

Same seed + config must produce:

* identical `ACTIVE/QUIET` epochs
* identical flip locations

---

## 12) Failure Classification (Frozen, Automated)

Each run must emit exactly one label.

### Stable Authority

* AAA high; lapses rare/short; RTD not heavy-tailed

### Bounded Degradation

* AAA reduced but > 0; lapses recur; RTD bounded

### Structural Thrashing (**Failure**)

* persistent oscillation; AAA → 0 in tail window; RTD heavy-tailed

### Asymptotic DoS (**Failure**)

* lapse dominance in tail window; recoveries exist but negligible

### Terminal Collapse (**Failure**, strict subset)

Let `tail_window` be the AAA window. Terminal Collapse occurs iff:

```
∃ t* ≤ horizon - tail_window
such that AUTH(epoch) = 0 for all epoch ∈ [t*, horizon)
```

No narrative interpretation.

---

## 13) Run Instructions (v0.2)

### Run 1 — Aggregation-Point Corruption

**Model:** `AGG_FLIP_BERNOULLI`
**Scope:** `SEM_PASS_ONLY`
**Sweep:** `rsa_p_flip_ppm ∈ {0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000}`
**Seeds:** standard battery (e.g., `[40..44]`)
**Report:** AA/AAA/RTD + observed vs expected flip rate

### Run 2 — Commitment-Correlated Noise

**Model:** `COMMITMENT_KEYED_FLIP`
**Scope:** `PER_KEY` (exactly one key targeted)
**Sweep:** `rsa_p_target_flip_ppm` over preregistered values (example: `0..50_000`)
**Target:** start with `C1`, optionally repeat for `C0`/`C2`
**Critical rule (k-aware):**

* If loss of target key is tolerated by `k` and AAA remains high → classify as **Stable Authority**
* Degradation requires material AAA drop or RTD expansion

### Run 3 — Burst-Scheduled Interference

**Model:** `BURST_SCHEDULED_FLIP`
**Scope:** `SEM_PASS_ONLY` (recommended)
**Schedule:** PERIODIC ONLY
**Sweep:** preregistered grid over `(period, width, phase_offset, p_burst)`
**Report:** include burst telemetry (duty cycle + active flip rate)

---

## 14) Critical Clarifications (Avoid Hidden Axes)

1. **No RSA during lapse:**
   If AKI does not evaluate commitments during `NULL_AUTHORITY`, RSA must not fire. Targets must be zero for those epochs.

2. **No outcome-conditional flips:**
   Do not condition flips on whether `Ci_OK_raw` was True/False.

3. **No shared RNG:**
   RSA must not advance any RNG used elsewhere (candidate sampling etc.). Stateless hashing is preferred.

4. **No semantic reinterpretation:**
   RSA flips booleans. It does not redefine commitment meaning or verifier semantics.

5. **No event anchoring in Run 3:**
   “Burst aligned to renewal boundaries” is out of scope unless renewal boundaries are purely calendar-fixed and equivalent to epoch-index scheduling. Do not consult runtime transitions.

---

## 15) Definition of Done

RSA v0.2 is complete when:

* RSA disabled equivalence passes
* RSA enabled + zero-probability equivalence passes
* Deterministic, non-adaptive interference is implemented for all three models
* Aggregation recomputation in `PER_KEY` mode uses AKI’s exact aggregator function
* AA/AAA/RTD computed and reported per run
* Burst telemetry (duty cycle + active/quiet rates) reported for Run 3
* Run 1–3 scripts execute and produce reconstructible reports
* No AKI constitutional mechanics were modified

---

## Final Orientation for the Implementor

You are not improving governance.
You are not making semantics “robust” by redesigning AKI.
You are running a falsifiable sweep that removes “epistemics” as an explanation, or proves it is sufficient.

Do not optimize it.
Do not editorialize it.
Instrument it and run it.
