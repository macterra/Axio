# Opus Run Instructions: AKI v0.7 (ALS-G) — **Run B (Forced Succession Eligibility Activation)**

## Goal

Determine whether **eligibility-coupled succession** in AKI v0.7 produces **observable constitutional effects** when post-initial succession events are forced to occur.

Run B answers:

> *When authority turnover is made frequent while all other mechanics are held constant, does eligibility gating actively filter successor candidates, and under what conditions does constitutional lapse (`NULL_AUTHORITY`) occur?*

Run B is **mechanism-activation and classification**, not optimization or stress testing.

---

## Scope (Binding)

### In scope

* Eligibility-gated successor selection (ALS-G)
* Stable `policy_id`–keyed semantic failure streaks
* Forced succession via renewal-count constraint
* Commitment ledger semantics inherited from ALS-C
* Expressivity tiers and rent enforced by lease interface
* Renewal remains structural and semantic-blind

### Out of scope

* Any change to commitment definitions or verifiers
* Any change to eligibility predicate (`streak < K`)
* Any change to rent schedule
* Any change to renewal cost
* Any change to expressivity tier
* Generator reweighting or pool restriction
* Detector changes
* Multi-axis parameter tuning

If any out-of-scope change occurs, **abort Run B**.

---

## Shared Preconditions (Must Hold)

All **ALS-G / v0.7** invariants must hold unchanged:

1. Eligibility filtering occurs **only at succession events**.
2. `semantic_fail_streak` is keyed to stable `policy_id`.
3. Streak updates occur **only at epoch end with active authority**.
4. No streak updates during `NULL_AUTHORITY`.
5. Empty `C_ELIG` triggers constitutional lapse.
6. Renewal remains independent of semantic state.
7. Commitment failures are not violations.

Violation of any invariant invalidates the run.

---

## Shared Configuration (All B Runs)

### Core parameters (fixed)

* `max_cycles` — set per horizon rule above
* `renewal_check_interval` — unchanged from Run A
* `msrw_cycles` — unchanged from Run A
* `renewal_cost_steps` — unchanged from Run A
* `reject_immediate_bankruptcy = False`

### Renewal Geometry (fixed)

* `renewal_check_interval` — unchanged

No renewal timing geometry changes are permitted.

---

### Expressivity / Rent (fixed)

* Expressivity tier: **unchanged from Run A / v0.6**
* Rent schedule: **unchanged**

Rationale: isolate **succession frequency** as the sole driver of new behavior.

---

### Generator (fixed)

* Same successor generator as v0.6 / Run A
* Same successor pool composition
* Same attack/control weighting
* Same TierFilterGenerator behavior
* Same retry limits

Do **not** alter the candidate pool.

---

## Experimental Axis

**Single varied parameter:** `max_successive_renewals`

All other parameters must remain identical to Run A.

### Harness-Enforced Renewal Limit (Binding)

`max_successive_renewals` must be **harness-enforced**, not a generator hint.

**Implementation requirement:**

In `ALSHarnessV070`, add:

* A counter tracking renewals for the current tenure: `tenure_renewals_used`
* Initialize to 0 at successor endorsement
* At each renewal check:
  - If renewal succeeds: increment `tenure_renewals_used += 1`
  - If `tenure_renewals_used >= max_successive_renewals`: force lease expiration and trigger succession

**Key constraint:** This is purely structural—no semantics involved.

### Logging (Required)

Log each forced turnover event with:

* `policy_id` of outgoing authority
* `tenure_renewals_used`
* `max_successive_renewals`
* `cause = FORCED_TURNOVER_RENEWAL_LIMIT`

---

## Run B Structure

Run B consists of **one forced-turnover regime**, not a sweep.

Do **not** introduce sub-runs unless explicitly instructed later.

---

## Run B Configuration — Forced Turnover

### B0 — Moderate Forced Succession (Activation Baseline)

* `max_successive_renewals = 3`
* `K = 3` (spec default)

Purpose:

* Guarantee multiple post-initial succession events
* Activate eligibility filtering in a non-trivial regime
* Observe candidate exclusions without immediately forcing thrash

---

## Horizon

Run B must be long enough to guarantee **many post-initial successions**.

**Rule (Binding):**

> Choose `H` large enough that each seed experiences **at least 20 post-initial succession events** under the forced-turnover rule.

### Horizon Calculation

If renewal checks happen every `R = renewal_check_interval` cycles, and forced turnover is after `N = max_successive_renewals` successful renewals, then expected time between forced successions is:

```
cycles_per_tenure ≈ N * R
```

To target `T` post-init successions:

```
H ≈ (T + 1) * N * R
```

**Concrete instruction:**

```
H = 100 * renewal_check_interval
```

Example: if `renewal_check_interval = 50`, then `H = 5000` cycles gives ~33 forced turnovers maximum.

If post-init successions < 20 by end, rerun with `H = 300 * renewal_check_interval`.

---

## Seeds

Reuse **Run A seeds** for continuity:

* 50, 51, 52, 53, 54

---

## Stop Rules (Binding)

Terminate a seed run on first occurrence of:

1. Horizon exhaustion
2. Degeneracy detector trigger
3. Renewal failure
4. Bankruptcy
5. Revocation

`NULL_AUTHORITY` is **not** a terminal condition.

Terminal cause must be logged explicitly.

---

## Required Telemetry (Binding)

For each `(seed)`:

### A) Succession Activation

* total successions
* post-initial successions
* mean residence time (epochs)
* residence time distribution

---

### B) Eligibility Dynamics

For each succession event:

* `|C_POOL|`
* `|C_ELIG|`
* number of rejected candidates
* list of rejected `policy_id`s

---

### C) Semantic Streak Dynamics

Per `policy_id`:

* max streak reached
* number of streak resets (`SEM_PASS`)
* sawtooth patterns (`FAIL^(K−1) → PASS`)
* epochs spent ineligible while not endorsed

---

### D) Constitutional Lapse

* count of lapse events
* total time in `NULL_AUTHORITY` (epochs)
* confirmation: no streak updates during lapse

---

### E) Structural Integrity Checks

* renewal success rate
* commitment evaluation continues during active authority
* no semantic influence on renewal or enforcement

---

## Post-hoc Regime Classification (Required)

Classify each seed using **constitutional behavior**, not competence:

* **LATENT (Control-like)**

  * successions occur
  * eligibility rarely reduces `C_ELIG`

* **FILTERING ACTIVE**

  * eligibility exclusions observed
  * `|C_ELIG| < |C_POOL|` occurs repeatedly

* **CONSTITUTIONAL LAPSE**

  * `C_ELIG = ∅` occurs
  * system enters `NULL_AUTHORITY`

No quality or performance labels permitted.

---

## Required Reporting

### Summary Table (Mandatory)

| Seed | Post-Init Successions | Mean Residence | Avg |C_ELIG| | Lapses | Time in NULL_AUTHORITY | Dominant Regime | Terminal Cause |
|------|----------------------|----------------|------------|--------|-----------------------|----------------|----------------|

---

### Eligibility Activation Timeline (Mandatory)

Chronological table or plot:

```
epoch → |C_ELIG| / |C_POOL|
```

This must visibly show eligibility becoming active.

---

### Conservative Interpretation (One Paragraph)

Must state:

* turnover pressure applied
* whether eligibility filtering activated
* whether lapse occurred
* what **cannot** be inferred beyond succession-gated selection

---

## Interpretation Constraints (Binding)

You **may** conclude:

* Whether eligibility gating activates under forced turnover
* How often candidates are excluded
* Whether lapse is reachable under these conditions

You **may not** conclude:

* Improved competence
* Optimal governance
* Semantic success
* Alignment properties
* Long-run inevitability

---

## Classification Rules

Run B is **informative** if **any** occurs:

* eligibility exclusions observed
* reduced `C_ELIG` at succession
* lapse occurs or is narrowly avoided

Run B is a **failure** only if:

* succession frequency does not increase
* eligibility predicate is never evaluated post-init
* any out-of-scope parameter changes

---

## Orientation

Run A showed **latent eligibility** under stable authority.

**Run B determines whether eligibility gating becomes constitutionally active when turnover is forced—without changing semantics, rent, or generators.**

Proceed exactly as specified.
