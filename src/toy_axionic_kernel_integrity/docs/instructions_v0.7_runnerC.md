# Opus Run Instructions: AKI v0.7 (ALS-G) — **Run C (Eligibility Threshold Sweep Under Forced Turnover)**

## Goal

Quantify how the **eligibility threshold K** controls constitutional outcomes under a fixed forced-turnover geometry.

Run C answers:

> *Holding the candidate pool, renewal geometry, rent, and forced turnover constant, how does varying K change eligibility contraction, lapse frequency, and time spent in NULL_AUTHORITY?*

Run C is **single-axis and classificatory**, not exploratory.

---

## Scope (Binding)

### In scope

* ALS-G eligibility gating at succession
* Harness-enforced forced turnover (`max_successive_renewals`)
* Stable `policy_id` streak accounting
* K-threshold variation only (`streak < K`)
* NULL_AUTHORITY lapse handling
* All inherited ALS/ALS-E/ALS-C mechanics unchanged

### Out of scope

* Any change to candidate pool composition or weights
* Any change to rent schedule or expressivity tier
* Any change to renewal cost
* Any change to renewal_check_interval timing
* Any change to commitment definitions/verifiers/windows
* Any change to streak update rule (reset-on-pass, +1-on-fail)
* Any new coupling channel (renewal penalties, revocation-by-semantics, etc.)
* Any detector changes
* Multi-axis tuning

If any out-of-scope change occurs, **abort Run C**.

---

## Shared Preconditions (Must Hold)

All v0.7 invariants must hold unchanged:

1. Eligibility filtering occurs **only at succession events**.
2. `semantic_fail_streak` keyed to stable `policy_id`, not instance identity.
3. Streak updates occur **only at epoch end with active authority**.
4. No streak updates during `NULL_AUTHORITY`.
5. If `C_ELIG = ∅`, constitutional lapse triggers `NULL_AUTHORITY`.
6. Renewal success remains independent of semantic state.
7. Commitment failure is not a violation; no semantic enforcement.

Violation of any invariant invalidates the run.

---

## Shared Configuration (All C Sub-Runs)

These settings must be identical to Run B unless explicitly listed below.

### Core parameters (fixed)

* `renewal_check_interval = 50` cycles
* `max_successive_renewals = 3` (**harness-enforced**, not generator hint)
* Candidate pool and generator: **unchanged from Run B**
* Rent/expressivity: **unchanged**
* Renewal cost: **unchanged**
* MSRW settings: **unchanged**
* Commitment ledger + GENESIS_SET_0: **unchanged**

### Horizon (fixed)

* `H = 5,000 cycles` per seed

Rationale: direct comparability with Run B.

---

## Experimental Axis

**Single varied parameter:** `K`

All other parameters must remain identical across sub-runs.

---

## Run C Structure

Run C consists of **four independent sub-runs**, each with a different `K`.

You must **not** combine sub-runs.

---

## C Sub-Runs — Eligibility Strictness Sweep

### C1 — Knife-edge Eligibility

* `K = 1`

Purpose: maximum strictness; excludes any policy after one semantic failure streak increment.

---

### C2 — Baseline Constitution (Run B replication point)

* `K = 3`

Purpose: replication anchor; must reproduce Run B regime behavior under identical geometry.

---

### C3 — Forgiving Eligibility

* `K = 5`

Purpose: test whether eligibility collapse and lapse are delayed or reduced under higher tolerance.

---

### C4 — Very Forgiving Eligibility

* `K = 10`

Purpose: test whether lapse becomes rare or disappears under high tolerance.

---

## Seeds (Binding)

Use the same seeds as Run A and Run B:

* 50, 51, 52, 53, 54

---

## Stop Rules (Binding)

Terminate a seed run on first occurrence of:

1. Horizon exhaustion
2. Degeneracy detector trigger (if enabled; configuration must match Run B)
3. Renewal failure
4. Bankruptcy
5. Revocation

`NULL_AUTHORITY` is **not** terminal.

Terminal cause must be logged explicitly.

---

## Required Telemetry (Binding)

For each `(K, seed)`:

### A) Succession Dynamics

* total successions
* post-initial successions
* mean residence time (epochs)
* residence time distribution (should remain clustered due to forced turnover)

---

### B) Eligibility Activation Metrics

At each succession event (excluding initial):

* per-succession candidate list size (expected stable)
* `|C_ELIG|`
* number rejected
* rejected `policy_id` list

Also report:

* fraction of successions with `|C_ELIG| < |C_POOL|`
* minimum `|C_ELIG|` observed

---

### C) Time-to-Empty-Eligibility

* first epoch (or succession index) where `C_ELIG = ∅`, if it occurs
* if never occurs, record `N/A`

---

### D) Constitutional Lapse Metrics

* lapse event count
* total time in `NULL_AUTHORITY` (cycles)
* mean lapse duration
* confirmation: no streak updates during lapse

---

### E) Semantic Streak / Reset Evidence

Per `policy_id`:

* max streak reached
* number of resets (`SEM_PASS` count)
* sawtooth count (`FAIL^(K−1) → PASS`)
* total epochs endorsed (exposure) for normalization

---

### F) Structural Integrity Checks

* renewal success rate (should remain 100% before forced expiration)
* commitment evaluation continuity during active authority
* confirmation: renewal and enforcement do not depend on semantic state

---

## Post-hoc Regime Classification (Required)

Classify each `(K, seed)` using constitutional behavior:

* **LATENT**

  * successions occur
  * eligibility rarely reduces `C_ELIG`
  * no lapse

* **FILTERING_ACTIVE**

  * eligibility reductions frequent (`|C_ELIG| < |C_POOL|`)
  * no lapse (or lapse extremely rare)

* **CONSTITUTIONAL_LAPSE**

  * `C_ELIG = ∅` occurs
  * system enters `NULL_AUTHORITY`

Classification is per seed; then aggregate per K.

No competence labels permitted.

---

## Required Reporting

### Summary Table (Mandatory)

One table covering all `(K, seed)`:

| K | Seed | Post-Init Successions | Avg |C_ELIG| | Min |C_ELIG| | Time-to-First C_ELIG=∅ | Lapses | Time in NULL_AUTHORITY (cycles) | Dominant Regime | Terminal Cause |
|---|------|------------------------|------------|------------|------------------------|--------|-------------------------------|----------------|---------------|

---

### Phase-Line View (Mandatory)

A single consolidated view:

`K → regime distribution`

Example format:

| K  | LATENT | FILTERING_ACTIVE | CONSTITUTIONAL_LAPSE |
| -- | ------ | ---------------- | -------------------- |
| 1  | x/5    | y/5              | z/5                  |
| 3  | ...    | ...              | ...                  |
| 5  | ...    | ...              | ...                  |
| 10 | ...    | ...              | ...                  |

---

### Conservative Interpretation Paragraph per K (Mandatory)

Each paragraph must state:

* K tested
* whether eligibility filtering activated
* whether lapse occurred and how often
* what cannot be inferred beyond succession-gated selection

---

## Interpretation Constraints (Binding)

You **may** conclude:

* how K shifts eligibility contraction and lapse frequency under fixed turnover
* whether a non-lapse “constitutional band” appears at higher K
* whether C2 reproduces Run B as expected

You **may not** conclude:

* improved competence
* optimal governance
* alignment properties
* generality beyond tested pool/geometry
* inevitability claims

---

## Classification Rules

Run C is **informative** if any occurs:

* lapse frequency varies materially with K
* time-to-first-empty eligibility shifts with K
* a non-lapse region emerges at higher K

Run C is a **failure** only if:

* any out-of-scope parameter changes occur
* forced turnover is not enforced at harness level
* eligibility is not evaluated post-init despite forced turnover
* C2 fails to reproduce Run B behavior under identical settings

---

## Orientation

Run A demonstrated **latent eligibility** under stable authority.

Run B demonstrated **activation and lapse reachability** under forced turnover at K=3.

**Run C maps how strictness (K) controls constitutional viability under the same forced-turnover geometry.**

Proceed exactly as specified.
