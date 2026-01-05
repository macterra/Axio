# Opus Run Instructions: AKI v0.8 (ALS-A) — **Run A (CTA Baseline Recovery Dynamics Under Forced Turnover)**

## Goal

Test whether **Constitutional Temporal Amnesty (CTA)** enables **constitutional recovery** from `NULL_AUTHORITY` while preserving the v0.7 invariants: **eligibility gating at succession only**, **no semantic enforcement**, **no optimization**, and **no agent action during lapse**.

Run A answers:

> *Given a configuration that reaches `NULL_AUTHORITY` under ALS-G, does CTA reopen eligibility over time, and if so, does recovery produce meaningful authority spans or only stutter/oscillation?*

Run A is **single-axis and classificatory**, not exploratory.

---

## Scope (Binding)

### In scope

* ALS-A CTA (time-only streak decay **during** `NULL_AUTHORITY`)
* ALS-G eligibility gating at succession
* Harness-enforced forced turnover (`max_successive_renewals`)
* Stable `policy_id` streak accounting
* Lapse (`NULL_AUTHORITY`) accounting
* Lapse cause classification (semantic vs structural)
* Recovery Yield metric

### Out of scope

* Any change to rent schedule or expressivity tier
* Any change to renewal cost
* Any change to `renewal_check_interval` timing
* Any change to commitment definitions/verifiers/windows
* Any change to streak update rule during active authority (reset-on-pass, +1-on-fail)
* Any change to eligibility predicate form (`streak < K`)
* Any new coupling channel (renewal penalties, revocation-by-semantics, etc.)
* Any change to candidate pool composition policy
* Any detector changes
* Any multi-axis tuning or parameter sweep

If any out-of-scope change occurs, **abort Run A**.

---

## Shared Preconditions (Must Hold)

All v0.7 invariants must hold unchanged, plus v0.8 additions:

### ALS-G invariants (must hold)

1. Eligibility filtering occurs **only at succession events**.
2. `semantic_fail_streak` is keyed to stable `policy_id`, not instance identity.
3. Streak updates occur **only at epoch end with active authority**.
4. `C_ELIG = ∅` at succession triggers constitutional lapse → `NULL_AUTHORITY`.
5. Renewal success remains independent of semantic state.
6. Commitment failure is not a violation; no semantic enforcement.

### ALS-A additions (must hold)

7. **No agent actions occur during `NULL_AUTHORITY`.**
8. **No verifiers execute during `NULL_AUTHORITY`.**
9. **No streak updates during `NULL_AUTHORITY` except CTA decrement.**
10. Commitment TTL clocks **continue to advance** during `NULL_AUTHORITY`.
11. Succession attempts occur only at **scheduled succession boundaries** (unchanged cadence).
12. Candidate pools are **regenerated** at each succession attempt (same pool policy, fresh instances).

Violation of any invariant invalidates the run.

---

## Shared Configuration (All A Sub-Runs)

These settings must be identical to the v0.7 run configuration you are using as the “lapse-reachable baseline,” except for the CTA parameters explicitly listed below.

### Core parameters (fixed)

* `renewal_check_interval = 50` cycles
* `max_successive_renewals = 3` (**harness-enforced**, not generator hint)
* `horizon = 5,000 cycles`
* Seeds: **50, 51, 52, 53, 54**
* Rent/expressivity: unchanged
* Renewal cost: unchanged
* MSRW settings: unchanged
* Commitment ledger + `GENESIS_SET_0`: unchanged
* Candidate pool policy: **V060_DEFAULT** (unchanged from v0.7 baseline)

### Eligibility threshold (fixed)

To keep Run A single-axis, fix K at a single value:

* `K = 3`

Do not sweep K in Run A.

### CTA parameters (the single new mechanism)

Enable CTA with fixed defaults:

* `AMNESTY_INTERVAL = 10` epochs
* `AMNESTY_DECAY = 1`

Do not sweep CTA parameters in Run A.

---

## Experimental Axis

**Single varied parameter:** **None**.
Run A is the baseline that validates the v0.8 mechanism under default CTA parameters.

The only difference from the v0.7 baseline is that CTA is enabled.

---

## Run A Structure

Run A is a single run (no sub-runs), executed across the five specified seeds.

---

## Implementation Notes (Binding)

### A) CTA must run only during `NULL_AUTHORITY`

At **each epoch boundary** while in `NULL_AUTHORITY`:

1. `lapse_epoch_count += 1`
2. If `lapse_epoch_count % AMNESTY_INTERVAL == 0`, decrement all historical streaks:

```
streak[policy_id] := max(0, streak[policy_id] - AMNESTY_DECAY)
```

Hard constraints:

* No verifier calls
* No streak increments/resets
* No agent actions
* No semantic window evaluation

### B) Succession attempt cadence during lapse must remain unchanged

During `NULL_AUTHORITY`, continue advancing cycles and epochs normally, but:

* attempt succession **only** at scheduled succession boundaries (same schedule as active operation)
* do not attempt succession every epoch unless that was already the inherited succession schedule

### C) Candidate pool regeneration during lapse

At each succession attempt (including those occurring during `NULL_AUTHORITY`):

* regenerate the candidate list using the baseline generator and `V060_DEFAULT` policy
* fresh instances are allowed; `policy_id` must remain stable
* do not reuse the last “lapse-causing” candidate list

### D) Commitment TTL semantics during lapse

* TTL clocks advance with epoch boundaries even during `NULL_AUTHORITY`
* commitment evaluation is suspended during lapse
* after recovery, TTL backlog is evaluated at the **first epoch end** under an active authority holder (standard evaluation point)

No “immediate evaluation on endorsement.” The first semantic window is the first completed epoch.

### E) Lapse cause classification must be recorded

At each succession boundary that yields `C_ELIG = ∅`, compute:

* `C_STRUCT = { c ∈ CANDIDATE_SET | structurally_admissible(c) }`

Classify:

* **Semantic Lapse** if `C_STRUCT ≠ ∅` and `C_ELIG = ∅`
* **Structural Lapse** if `C_STRUCT = ∅`

CTA is only relevant to semantic lapse; report both regardless.

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

For each `(seed)`:

### A) Succession Dynamics

* total `SUCCESSOR_ENDORSED`
* post-initial successions (S* excluding initialization)
* mean residence time (epochs)
* residence time distribution
* endorsement entropy (inherited definition)

---

### B) Eligibility Dynamics (Per Succession)

At each succession event (excluding initial):

* candidate list size
* `|C_STRUCT|`
* `|C_ELIG|`
* number rejected
* rejected `policy_id`s and their streaks
* indicator `C_ELIG = ∅`

Also report:

* average `|C_ELIG|`
* minimum `|C_ELIG|`
* fraction of successions with `|C_ELIG| = 0`

---

### C) Lapse Metrics (Core)

* lapse count
* total time in `NULL_AUTHORITY` (cycles)
* mean lapse duration (cycles and epochs)
* `lapse_epoch_count` evolution during each lapse episode
* confirmation: no agent actions during lapse
* confirmation: no verifier calls during lapse
* lapse cause counts: semantic vs structural
* lapse cause durations: semantic vs structural

---

### D) Amnesty Metrics (Core)

For each amnesty event:

* epoch index of amnesty
* total streak mass before and after (sum over `policy_id`)
* per-policy streak deltas
* count of policy_ids that crossed `K` threshold due to amnesty (from ineligible to eligible)

Also report:

* total amnesty events per seed

---

### E) Recovery Metrics (Core)

Define a **recovery episode** as:

`NULL_AUTHORITY → SUCCESSOR_ENDORSED`

For each recovery episode i:

* `L_i` = epochs in `NULL_AUTHORITY` before recovery
* `A_i` = epochs of active authority until next lapse or horizon
* **Recovery Yield**: `RY_i = A_i / max(1, L_i)`

Also report:

* distribution of `RY` (min/median/mean/max)
* time to first recovery (epochs from first lapse entry)
* recovery count

---

### F) Stutter Metrics (Required)

Define **Stutter Recovery**:

`NULL_AUTHORITY → ACTIVE for exactly 1 epoch → NULL_AUTHORITY`

Report:

* stutter count
* stutter fraction of recoveries
* stutter-associated `policy_id` (if concentrated)

---

### G) “Zombie Time” Definition (Required)

Zombie time exists when an active authority holder becomes ineligible mid-lease and remains in office until succession.

You must record:

* epoch where `streak` first reaches `K` for the active holder
* epoch of the next succession boundary
* zombie duration = delta between those epochs

Report zombie time distribution per seed.

---

## Post-hoc Regime Classification (Required)

Classify each `(seed)` using constitutional behavior:

* **NO_LAPSE**

  * no `NULL_AUTHORITY` entered

* **RECOVERING**

  * lapse occurs and at least one recovery occurs

* **PERMANENT_LAPSE**

  * lapse occurs and no recovery occurs by horizon

* **AMNESTY_DOMINANT**

  * lapse fraction of horizon > 0.80 (threshold fixed for reporting)

Additionally, classify oscillation subtype if `RECOVERING`:

* **STUTTER_DOMINANT**

  * stutter fraction of recoveries > 0.50

No competence labels permitted.

---

## Required Reporting

### Summary Table (Mandatory)

| Seed | Post-Init Successions | Avg |C_ELIG| | Min |C_ELIG| | Lapses | NULL_AUTH (cycles) | Semantic vs Structural Lapse (cycles) | Amnesty Events | Recoveries | Median RY | Stutter Recoveries | Dominant Regime | Terminal Cause |
|------|------------------------|------------|------------|--------|-------------------|-------------------------------|--------------|-----------|----------|-------------------|----------------|---------------|

---

### Episode Table (Mandatory)

One table listing lapse/recovery episodes:

| Seed | Episode # | Lapse Cause | Lapse Epochs (L) | Amnesty Events During Lapse | Recovered? | Active Epochs After (A) | RY = A/L | Stutter? | Notes |
| ---- | --------- | ----------- | ---------------- | --------------------------- | ---------- | ----------------------- | -------- | -------- | ----- |

---

### Conservative Interpretation Paragraph per Seed (Mandatory)

Each paragraph must state:

* whether lapse occurred
* whether recovery occurred
* whether recovery yield was meaningful or near-zero
* whether lapse was semantic or structural
* what cannot be inferred beyond this run

---

## Interpretation Constraints (Binding)

You **may** conclude:

* whether CTA reopens eligibility in practice under this geometry
* recovery latency and yield distributions
* whether recovery is dominated by stutter oscillation
* whether backlog shock (expired TTL) correlates with immediate re-lapse
* the relative prevalence of semantic vs structural lapse

You **may not** conclude:

* competence
* alignment
* optimal governance
* generality beyond this geometry and pool policy
* that CTA “solves” lapse

---

## Classification Rules

Run A is **informative** if any occurs:

* at least one seed shows recovery with non-trivial authority spans (RY not near 0)
* at least one seed shows permanent lapse (boundary evidence)
* stutter regimes appear and are quantifiable
* semantic vs structural lapse split is non-trivial

Run A is a **failure** only if:

* CTA not actually applied (no amnesty events despite lapse)
* streak changes occur during lapse in any way other than CTA decrement
* verifiers execute during lapse
* succession attempts occur at a different cadence than inherited schedule
* candidate pool policy deviates from `V060_DEFAULT`
* any out-of-scope parameter changes occur

---

## Orientation

Run A is the **v0.8 reset baseline**: **ALS-G + one timer**.

Do not tune it.
Do not add axes.
Do not “fix” stutter.

Proceed exactly as specified.
