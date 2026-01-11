# Opus Run Instructions: AKI v0.7 (ALS-G) — **Run D (Candidate Pool Composition Stress Under Forced Turnover)**

## Goal

Test whether **eligibility-coupled succession** remains constitutionally meaningful under **candidate pool composition skew**, holding turnover geometry and all other mechanics constant.

Run D answers:

> *Under fixed forced-turnover geometry, does skewing the candidate pool toward failure-prone or pass-prone policy IDs change eligibility contraction, lapse reachability, and time in NULL_AUTHORITY?*

Run D is **single-axis and classificatory**, not exploratory.

---

## Scope (Binding)

### In scope

* ALS-G eligibility gating at succession
* Harness-enforced forced turnover (`max_successive_renewals`)
* Stable `policy_id` streak accounting
* Candidate pool **composition policy** only (weights / inclusion), as a harness parameter
* Lapse (`NULL_AUTHORITY`) accounting

### Out of scope

* Any change to rent schedule or expressivity tier
* Any change to renewal cost
* Any change to renewal_check_interval timing
* Any change to commitment definitions/verifiers/windows
* Any change to streak update rule (reset-on-pass, +1-on-fail)
* Any change to eligibility predicate form (`streak < K`)
* Any new coupling channel (renewal penalties, revocation-by-semantics, etc.)
* Detector changes
* Multi-axis tuning

If any out-of-scope change occurs, **abort Run D**.

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

## Shared Configuration (All D Sub-Runs)

These settings must be identical to Run B / Run C unless explicitly listed below.

### Core parameters (fixed)

* `renewal_check_interval = 50` cycles
* `max_successive_renewals = 3` (**harness-enforced**, not generator hint)
* `horizon = 5,000 cycles`
* Seeds: 50, 51, 52, 53, 54
* Rent/expressivity: unchanged
* Renewal cost: unchanged
* MSRW settings: unchanged
* Commitment ledger + GENESIS_SET_0: unchanged

### Eligibility threshold (fixed)

To keep Run D single-axis, fix K at a single value:

* `K = 5`

Rationale: K=5 is the **boundary region** from Run C (mixed regimes). It is the most informative point for composition stress. Do not sweep K in Run D.

---

## Experimental Axis

**Single varied parameter:** `candidate_pool_policy` (composition/weights)

All other parameters must remain identical across sub-runs.

---

## Run D Structure

Run D consists of **three independent sub-runs**, each with a different pool composition.

You must **not** combine sub-runs.

---

## D Sub-Runs — Pool Composition Variants

### D0 — Baseline Control (Replication Anchor)

* `candidate_pool_policy = V060_DEFAULT`

Purpose: confirm the Run B/C baseline behavior at K=5 for direct comparison.

---

### D1 — Attack-Heavy Pool (Failure-Skew)

* `candidate_pool_policy = ATTACK_HEAVY_90`

Definition (Binding):

* Candidate draws are skewed such that ~90% of sampled candidates are from `AttackSuccessorType` policy IDs, ~10% from `ControlSuccessorType`.
* The per-succession candidate list size must remain identical to baseline.
* All policy IDs remain available unless explicitly excluded by this policy.

Purpose: test whether eligibility collapses faster and lapse dominates under adversarial composition.

---

### D2 — Control-Heavy Pool (Pass-Skew)

* `candidate_pool_policy = CONTROL_HEAVY_90`

Definition (Binding):

* Candidate draws are skewed such that ~90% of sampled candidates are from `ControlSuccessorType` policy IDs, ~10% from `AttackSuccessorType`.
* Per-succession candidate list size unchanged.

Purpose: test whether the system enters a stable non-lapse region under pass-skew without changing K.

---

## Implementation Notes (Binding)

### A) Composition must be applied at candidate sampling

The pool policy must affect **which policy IDs are sampled**, not eligibility logic, not streak updates, and not renewal.

**Implementation approach (Option A — Weight-Map Parameterization):**

Adjust the generator's successor-type sampling weights based on `candidate_pool_policy`, while leaving all other generator logic unchanged.

**Weight construction rules:**

1. Keep the existing v0.6 baseline weights as `BASE_WEIGHTS` (untouched).
2. For D0 (`V060_DEFAULT`): use `BASE_WEIGHTS` exactly — no modification.
3. For D1 (`ATTACK_HEAVY_90`): scale Attack weights so Attack total mass = 0.90, Control total mass = 0.10, preserving within-category relative proportions.
4. For D2 (`CONTROL_HEAVY_90`): inverse — Control total mass = 0.90, Attack total mass = 0.10, preserving within-category relative proportions.

This ensures:
* Internal "shape" of Attack policies remains the same (just reweighted as a block)
* Internal "shape" of Control policies remains the same
* Only the cross-category mix changes (single-axis)
* D0 uses the exact existing weight tables for baseline comparability

### B) Policy identity must remain stable

`policy_id` format must remain unchanged (`"{category}:{enum.name}"`).

### C) Candidate list size must remain constant

Whatever per-succession list size you use (e.g., 11), it must be identical across D0/D1/D2.

### D) Retry semantics must remain unchanged

If the generator uses retries, keep that behavior identical across sub-runs. Composition applies consistently per sampling attempt.

### E) Edge case: category exhaustion

If one category has zero eligible policies due to streak exhaustion, do **not** "force" the 90/10 split. Keep the sampler as-is; eligibility filtering is supposed to reveal pool exhaustion. Just report the realized mix.

---

## Stop Rules (Binding)

Terminate a seed run on first occurrence of:

1. Horizon exhaustion
2. Degeneracy detector trigger (if enabled; must match baseline config)
3. Renewal failure
4. Bankruptcy
5. Revocation

`NULL_AUTHORITY` is **not** terminal.

---

## Required Telemetry (Binding)

For each `(sub-run, seed)`:

### A) Succession Dynamics

* total successions
* post-initial successions
* mean residence time (epochs)
* residence time distribution

---

### B) Eligibility Dynamics (Per Succession)

At each succession event (excluding initial):

* per-succession candidate list size
* `|C_ELIG|`
* # rejected
* rejected `policy_id`s

Also report:

* average `|C_ELIG|`
* minimum `|C_ELIG|`
* fraction of successions with `|C_ELIG| = 0`

---

### C) Lapse Metrics

* lapse count
* total time in `NULL_AUTHORITY` (cycles)
* mean lapse duration
* confirmation: no streak updates during lapse

---

### D) Streak / Reset Evidence

Per `policy_id`:

* max streak
* # resets (`SEM_PASS` count)
* endorsements count (exposure)
* sawtooth count (`FAIL^(K−1) → PASS`) at K=5 (so 4 FAIL then PASS)

---

### E) Composition Verification (Required)

For each sub-run and seed, report:

* `attack_draws / total_draws` — fraction of candidate sampling attempts from Attack policy IDs
* `control_draws / total_draws` — fraction of candidate sampling attempts from Control policy IDs

Where "draw" counts each candidate sampling attempt (including retries), since that reflects the actual sampling policy.

Also log:

* The final resolved weight dictionaries for the run (or at least their category sums + a hash) to make it auditable
* Confirmation that realized mix matches intended skew (~90/10 for D1/D2, baseline for D0)

This is required so the run cannot be accused of “intended skew not actually applied.”

---

## Post-hoc Regime Classification (Required)

Classify each `(sub-run, seed)` using constitutional behavior:

* **LATENT**

  * eligibility rarely reduces `C_ELIG`
  * no lapse

* **FILTERING_ACTIVE**

  * eligibility reductions frequent
  * no lapse (or lapse rare)

* **CONSTITUTIONAL_LAPSE**

  * `C_ELIG = ∅` occurs
  * system enters `NULL_AUTHORITY`

Aggregate regime distribution per sub-run.

No competence labels permitted.

---

## Required Reporting

### Summary Table (Mandatory)

| Sub-Run | Seed | Post-Init Successions | Avg |C_ELIG| | Min |C_ELIG| | Lapses | NULL_AUTH (cycles) | Attack/Control Sample Ratio | Dominant Regime | Terminal Cause |
|--------|------|------------------------|------------|------------|--------|-------------------|---------------------------|----------------|---------------|

---

### Phase-Line View (Mandatory)

A single table:

`pool policy → regime distribution`

Example:

| Pool Policy      | LATENT | FILTERING_ACTIVE | CONSTITUTIONAL_LAPSE |
| ---------------- | ------ | ---------------- | -------------------- |
| V060_DEFAULT     | x/5    | y/5              | z/5                  |
| ATTACK_HEAVY_90  | ...    | ...              | ...                  |
| CONTROL_HEAVY_90 | ...    | ...              | ...                  |

---

### Conservative Interpretation Paragraph per Sub-Run (Mandatory)

Each paragraph must state:

* pool composition tested
* whether eligibility filtering contracted `C_ELIG`
* whether lapse occurred and how often
* what cannot be inferred beyond this axis

---

## Interpretation Constraints (Binding)

You **may** conclude:

* whether pool composition materially changes lapse frequency under fixed K and turnover
* whether eligibility gating remains meaningful under skew
* whether a robust “constitutional band” exists across compositions at K=5

You **may not** conclude:

* optimal governance
* competence or alignment claims
* generality beyond tested pool/geometry
* inevitability claims

---

## Classification Rules

Run D is **informative** if any occurs:

* ATTACK_HEAVY increases lapse relative to baseline
* CONTROL_HEAVY reduces or eliminates lapse relative to baseline
* meaningful differences in `|C_ELIG|` distributions across pool policies

Run D is a **failure** only if:

* composition skew not actually applied (fails verification)
* any out-of-scope parameter changes occur
* forced turnover is not harness-enforced
* eligibility does not evaluate post-init despite forced turnover

---

## Orientation

Run C mapped **K-sensitivity** under the baseline pool.

**Run D maps composition sensitivity** under a fixed K (boundary-region) and fixed turnover.

Proceed exactly as specified.
