# Implementor Instructions: RSA v0.1 (RSA-DoS-0)

These instructions define how to implement **RSA v0.1 — Verifier-Outcome Noise Injection** as a **strictly additive stress layer** on **AKI v0.8 (ALS-A)**.

RSA v0.1 is not a new kernel.
RSA v0.1 is not a new constitution.
RSA v0.1 is not an oracle wrapper.

RSA v0.1 is about **whether governance can survive epistemic unreliability without rewriting the constitution to reward compliance**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new stress layer** that:

* Reuses **AKI v0.8 (ALS-A) verbatim**
* Treats AKI constitutional mechanics as **frozen and immutable**
* Injects **controlled epistemic noise** into semantic verification results
* Adds **telemetry** proving the perturbation fired
* Preserves **determinism** and **RNG stream separation**

RSA v0.1 introduces exactly one new capability:

> **Corrupt verifier booleans after evaluation, before eligibility/streak logic consumes them.**

### What you are not building

You are **not** building:

* new successor types
* a new eligibility rule
* any change to streak update logic
* any change to CTA, lapse scheduling, or renewal logic
* a learning system
* a reward/penalty mechanism
* an input/oracle perturbation layer
* adaptive noise based on agent actions
* any “semantic coupling” beyond existing epoch-end evaluation

RSA must remain a detachable harness: when off, it disappears.

---

## 1) Relationship to Prior Experiments (Binding)

RSA v0.1 is a **strict stress layer** on **ALS-A (AKI v0.8)**.

**All of the following must be reused unchanged:**

* ALS lease lifecycle, renewal checks, forced turnover
* Eligibility threshold K and eligibility predicate
* Streak increment/reset rules
* CTA rules (amnesty interval/decay, lapse epoch ticking)
* Lapse entry/exit semantics and scheduling
* Commitment ledger rules and TTL advancement
* Verifier logic for C0/C1/C2 (including non-vacuity)
* Candidate generator and pool composition

If any AKI v0.8 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 AKI kernel remains the constitution (Unchanged)

AKI:

* owns leases, renewal, revocation
* owns commitment ledger and TTL clocks
* owns verifier semantics (how Ci_OK is computed)
* owns streak updates and eligibility gating
* owns lapse + CTA behavior

RSA:

* does **not** compute commitments
* does **not** add new signals into eligibility
* does **not** change when verification happens
* does **not** touch candidate sampling RNG
* touches only the **boolean outputs** produced by AKI verification

### 2.2 No new agent-visible state (Critical)

RSA must be:

* harness-resident
* kernel-inaccessible
* successor-inaccessible

If any successor can observe/predict/query RSA noise state, the implementation is invalid.

---

## 3) What Exactly Changes (Minimal Patch Set)

You must implement three additive elements:

1. **RSAConfig block** (default off)
2. **RSAAdversary** implementing deterministic corruption
3. **Single hook site** where verifier booleans are passed through corruption
4. **Telemetry** proving flips occurred and quantifying flip rates

Nothing else.

---

## 4) RSAConfig (Additive; Default Off)

Extend harness configuration with an optional RSA config object (preferred), or add an optional block to the existing config (acceptable). Either way:

```python
rsa_enabled: bool = False
rsa_noise_model: Enum = NONE | FLIP_BERNOULLI
rsa_p_flip_ppm: int = 0                 # 0..1_000_000 (PPM)
rsa_scope: Enum = PER_CI | SEM_PASS_ONLY
rsa_rng_stream: str = "rsa"
```

Hard constraints:

* No floats. `rsa_p_flip_ppm` is integer PPM.
* All parameters are fixed for the run. No adaptation.

---

## 5) Deterministic Noise (Non-negotiable)

### 5.1 Stream separation

RSA randomness must be **independent** of:

* candidate sampling
* any stochastic successor behavior
* any environment randomness

Derive a dedicated RSA seed:

```
seed_rsa = stable_hash_64(seed, "rsa", rsa_rng_stream)
```

Do **not** use Python `hash()`.

### 5.2 Action independence

Flip decisions must not depend on:

* agent action traces
* observed commitment satisfaction
* candidate identity
* resource usage
* environment state

Flip decisions may depend only on:

* run seed
* epoch index
* commitment key name (C0/C1/C2 or SEM_PASS)
* a constant stage label

### 5.3 Stateless flip decision (preferred)

To avoid ordering dependence, compute flips as a pure function:

```
u = stable_hash_64(seed_rsa, epoch, key, stage) % 1_000_000
flip = (u < rsa_p_flip_ppm)
```

This guarantees the same flips occur even if loop ordering changes.

---

## 6) Locate the Single Correct Hook Point

You must insert the RSA hook at the point where AKI has already computed:

* `C0_OK`, `C1_OK`, `C2_OK` (or equivalent)
* optionally `SEM_PASS`

…and before any of these are used to:

* update semantic fail streak
* compute eligibility
* classify semantic fail/pass
* trigger downstream logging

Search targets (pick what exists):

* `SEM_PASS`
* `C0_OK` / `C1_OK` / `C2_OK`
* `evaluate_commitments`
* `semantic_window`
* `verifier`
* `update_streak`
* `eligibility`

If there are multiple semantic evaluation sites, consolidate by factoring to a shared function **without changing behavior** (same booleans in, same booleans out). RSA must hook exactly once.

---

## 7) Hook Semantics (Binding)

### 7.1 PER_CI mode (recommended)

AKI computes `Ci_OK_raw` exactly as before.

Then RSA applies:

```python
C0_OK = rsa.maybe_corrupt(C0_OK_raw, epoch, key="C0", stage="commitment")
C1_OK = rsa.maybe_corrupt(C1_OK_raw, epoch, key="C1", stage="commitment")
C2_OK = rsa.maybe_corrupt(C2_OK_raw, epoch, key="C2", stage="commitment")
SEM_PASS = C0_OK and C1_OK and C2_OK
```

### 7.2 SEM_PASS_ONLY mode (minimal)

```python
SEM_PASS_raw = C0_OK_raw and C1_OK_raw and C2_OK_raw
SEM_PASS = rsa.maybe_corrupt(SEM_PASS_raw, epoch, key="SEM_PASS", stage="aggregate")
```

Hard constraints:

* No change to the *time* at which evaluation occurs.
* No change to how `Ci_OK_raw` is computed.
* Only the returned booleans may differ under RSA.

---

## 8) Telemetry (Required)

You must log enough to prove the perturbation fired.

Per epoch log:

* `epoch`
* `rsa_enabled`
* `rsa_noise_model`
* `rsa_p_flip_ppm`
* `rsa_scope`
* `rsa_targets_epoch` (number of booleans eligible for corruption)
* `rsa_flips_epoch`
* `rsa_flips_by_key` (required in PER_CI; optional otherwise)

Run-level summary:

* `rsa_total_targets`
* `rsa_total_flips`
* `rsa_observed_flip_rate_ppm = total_flips * 1_000_000 // total_targets`
* `rsa_expected_flip_rate_ppm = rsa_p_flip_ppm`
* `rsa_seed_rsa` (or a stable digest)

Telemetry must be emitted even if results look “obvious.” Reviewers will not accept invisible perturbations.

---

## 9) Acceptance Tests (Non-negotiable)

Before any RSA experiment runs, implement three tests.

### 9.1 RSA disabled equivalence

Run AKI v0.8 baseline with RSA code present:

* `rsa_enabled=False`

Must match the pre-RSA baseline on:

* lapse count and total lapse epochs
* recovery count and stutter count
* authority uptime fraction
* renewal counts
* successor endorsements (S*), if logged
* streak table evolution (if logged)

If bitwise trace identity is feasible, require it. If not, require invariant equality.

### 9.2 RSA enabled with p_flip=0 equivalence

Run:

* `rsa_enabled=True`
* `rsa_noise_model=FLIP_BERNOULLI`
* `rsa_p_flip_ppm=0`

Must match baseline identically.

This catches “enabled path contamination” (extra RNG draws, ordering changes, hidden branch effects).

### 9.3 Flip firing proof

Run a short horizon with:

* `rsa_enabled=True`
* `rsa_p_flip_ppm` high (e.g., 50_000 = 5%)

Assert:

* `rsa_total_flips > 0`
* `rsa_observed_flip_rate_ppm` is near `rsa_p_flip_ppm` within binomial tolerance
* `rsa_total_targets` equals expected targets (3 per epoch for PER_CI; 1 per epoch for SEM_PASS_ONLY, excluding lapse epochs where evaluation doesn’t occur)

---

## 10) Run 0: Governance DoS Sweep (RSA v0.1)

### 10.1 Purpose

Measure how AKI v0.8’s constitutional recovery behaves when semantic verification is noisy, causing eligibility exhaustion and increased time in `NULL_AUTHORITY`.

### 10.2 Sweep parameter

Sweep `rsa_p_flip_ppm` over:

* `0`
* `200` (0.02%)
* `500` (0.05%)
* `1_000` (0.1%)
* `2_000` (0.2%)
* `5_000` (0.5%)
* `10_000` (1%)
* `20_000` (2%)

Keep all AKI v0.8 parameters fixed.

### 10.3 Seeds

Use the standard battery you already trust (example):

* seeds = `[40, 41, 42, 43, 44]`

### 10.4 Metrics to report (minimum)

For each p_flip value:

* lapse count
* total lapse epochs
* mean lapse duration
* long-lapse mode length estimate (if present)
* recovery count and recovery rate
* stutter count
* recovery yield (RY)
* authority uptime fraction
* RSA observed flip rate vs expected

### 10.5 Stop rules (classification only; do not terminate early)

A run ends only at horizon or inherited termination. But classify:

* **ROBUST:** recoveries remain high, lapse durations modest
* **DEGRADED:** recoveries occur, but long-lapse mode expands / RY collapses
* **DoS REGIME:** prolonged `NULL_AUTHORITY` dominance (define as a threshold, e.g., a continuous lapse run > `5 * amnesty_interval` epochs or any non-recovery window beyond a fixed cap)

Do not change the system to “help it recover.” Measure it.

---

## 11) Critical Clarifications (Avoid Hidden Axes)

1. **No RSA during lapse:**
   During `NULL_AUTHORITY`, AKI does not evaluate commitments. Therefore RSA must not fire either. Targets per epoch during lapse must be zero.

2. **No agent-dependent flips:**
   Do not condition flips on whether `Ci_OK_raw` is True/False or on any trace content.

3. **No shared RNG:**
   RSA must not advance any RNG used for candidate sampling. If you share RNG streams, you destroy baseline equivalence.

4. **No “semantic reinterpretation”:**
   RSA flips booleans. It does not redefine what commitments mean, how they’re checked, or how non-evaluable states are handled.

---

## 12) Definition of Done

RSA v0.1 is complete when:

* AKI v0.8 behavior is preserved exactly with `rsa_enabled=False`
* AKI v0.8 behavior is preserved exactly with `rsa_p_flip_ppm=0`
* RSA flips occur deterministically and are action-independent
* RSA has an independent RNG stream (or stateless hash flips)
* Telemetry proves flips fired and matches target rate
* Run 0 DoS sweep executes and produces reconstructible metrics
* No AKI constitutional mechanics were modified

---

## Final Orientation for the Implementor

You are not improving governance.

You are not making semantics “robust” by redesigning AKI.

You are testing whether **a constitution built to tolerate honest failure** can also tolerate **epistemic unreliability**—without turning semantic correctness into a reward function.

If it collapses, that is data.
If it stutters, that is data.
If it recovers slowly, that is data.
If it remains stable, that is data.

Do not optimize it.

Instrument it.
