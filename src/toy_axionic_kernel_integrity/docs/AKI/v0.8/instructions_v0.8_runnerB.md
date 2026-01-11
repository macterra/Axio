# Opus Run Instructions: AKI v0.8 (ALS-A) — **Run B (Amnesty Interval Sensitivity Under Forced Turnover)**

## Goal

Test whether the **long-lapse mode** observed in v0.8 Run A is governed by the **CTA clock**, by halving the amnesty interval while keeping everything else frozen.

Run B answers:

> *If we reduce `AMNESTY_INTERVAL` from 10 to 5 (single-axis), does the long-lapse mode (L ≈ 20 epochs) compress or disappear, and does the share of recoveries requiring amnesty change materially?*

Run B is **single-axis and causal-isolating**, not exploratory.

---

## Scope (Binding)

### In scope

* ALS-A CTA mechanism
* Halving `AMNESTY_INTERVAL` only
* Lapse/recovery dynamics and Recovery Yield
* Lapse cause classification (semantic vs structural)
* Recovery-without-amnesty vs recovery-with-amnesty split
* Bimodality shift/compression analysis

### Out of scope

* Any change to K
* Any change to candidate pool policy or composition
* Any change to turnover geometry (`max_successive_renewals`)
* Any change to rent schedule / expressivity tier
* Any change to renewal cost or renewal cadence
* Any change to commitment definitions/verifiers/windows/TTL rules
* Any change to streak update rule during active authority
* Any change to eligibility predicate (`streak < K`)
* Any new coupling channel (renewal penalties, revocation-by-semantics, etc.)
* Any detector changes
* Any multi-axis tuning or parameter sweep

If any out-of-scope change occurs, **abort Run B**.

---

## Shared Preconditions (Must Hold)

All v0.8 invariants from Run A must hold unchanged:

1. Eligibility filtering occurs **only at succession events**.
2. `semantic_fail_streak` keyed to stable `policy_id`, not instance identity.
3. Streak updates occur **only at epoch end with active authority**.
4. No agent actions during `NULL_AUTHORITY`.
5. No verifiers executed during `NULL_AUTHORITY`.
6. No streak updates during lapse **except CTA decrement**.
7. Commitment TTL clocks **continue to advance** during `NULL_AUTHORITY`.
8. Succession attempts occur at the inherited scheduled boundaries (epoch boundaries in this harness).
9. Candidate pools are regenerated at each succession attempt using the same pool policy.

Violation of any invariant invalidates the run.

---

## Shared Configuration (All Seeds)

Run B must be identical to v0.8 Run A in every parameter except the single axis below.

### Fixed parameters (identical to Run A)

* `horizon = 5,000 cycles`
* `renewal_check_interval = 50 cycles`
* `max_successive_renewals = 3` (harness-enforced)
* `K = 3`
* `AMNESTY_DECAY = 1`
* Candidate Pool Policy: `V060_DEFAULT`
* Seeds: **50, 51, 52, 53, 54**
* Rent/expressivity: unchanged
* Renewal cost: unchanged
* MSRW: unchanged
* Commitment ledger + `GENESIS_SET_0`: unchanged

### Single experimental axis (the only change)

* **Change:** `AMNESTY_INTERVAL = 5` epochs
* **Baseline comparison:** Run A used `AMNESTY_INTERVAL = 10`

Do not sweep. Do not try 3, 7, 12. This is a single-axis test.

---

## Run B Structure

One run, five seeds, no sub-runs.

---

## Implementation Notes (Binding)

### A) CTA tick logic (unchanged except interval)

At each epoch boundary while in `NULL_AUTHORITY`:

1. `lapse_epoch_count += 1`
2. If `lapse_epoch_count % AMNESTY_INTERVAL == 0`, apply:

```
streak[policy_id] := max(0, streak[policy_id] - AMNESTY_DECAY)
```

No verifiers. No actions. No increments/resets. CTA only.

### B) Lapse cause classification (required)

At each succession boundary with `C_ELIG = ∅`, compute `C_STRUCT` and log:

* Semantic Lapse if `C_STRUCT ≠ ∅`
* Structural Lapse if `C_STRUCT = ∅`

CTA can only address semantic lapse.

### C) Candidate pool regeneration (unchanged)

At each succession attempt, regenerate candidate list from the baseline generator and pool policy.

---

## Stop Rules (Binding)

Terminate a seed run on first occurrence of:

1. Horizon exhaustion
2. Degeneracy detector trigger (if enabled; must match Run A config)
3. Renewal failure
4. Bankruptcy
5. Revocation

`NULL_AUTHORITY` is not terminal.

---

## Required Telemetry (Binding)

All telemetry from Run A must be recorded identically, plus explicit “interval effect” fields.

### A) Episode Table (Mandatory)

For each lapse episode:

* Lapse epochs `L`
* Amnesty events during lapse (count)
* Recovered?
* Post-recovery authority epochs `A`
* Recovery Yield `RY = A / max(1, L)`
* Recovery-without-amnesty indicator (`amnesty_events == 0`)
* Lapse cause (semantic/structural)

### B) Aggregates (Mandatory)

* Total lapses
* Total recoveries
* Recovery rate
* Total amnesty events
* `recoveries_without_amnesty / total_recoveries`
* `recoveries_with_amnesty / total_recoveries`
* Distribution of `L` (lapse lengths)
* Distribution of `A` (authority spans)
* Distribution of `RY`

### C) Bimodality comparison against Run A (Mandatory)

Compute and report:

* Fraction of lapses with `L <= 2`
* Fraction of lapses with `L >= 10`
* Fraction of lapses with `L >= 20` (if any remain)
* Median `L` for “long-lapse” subset

You must compare these to Run A values:

* Run A long-lapse mode was **L ≈ 20** with 2 amnesty events.

---

## Post-hoc Regime Classification (Required)

Per seed:

* `NO_LAPSE`
* `RECOVERING`
* `PERMANENT_LAPSE`
* `AMNESTY_DOMINANT` (lapse fraction > 0.80)

No “stutter dominant” label unless `A <= 1` occurs; record it if it occurs.

---

## Required Reporting

### Summary Table (Mandatory)

| Seed | Post-Init Successions | Avg |C_ELIG| | Min |C_ELIG| | Lapses | NULL_AUTH (cycles) | Amnesty Events | Recoveries | Recoveries w/o Amnesty | Median L | Median A | Median RY | Dominant Regime | Terminal Cause |
|------|------------------------|------------|------------|--------|-------------------|--------------|-----------|----------------------|----------|----------|----------|----------------|---------------|

### Episode Table (Mandatory)

Same format as Run A, but include `amnesty_events` and `no_amnesty` flag.

### One conservative paragraph per seed (Mandatory)

Each paragraph must state:

* whether the long-lapse mode compressed (or not)
* whether amnesty was required more or less often than Run A
* whether recovery yield changed materially
* what cannot be inferred beyond this single axis

---

## Interpretation Constraints (Binding)

You may conclude:

* whether halving `AMNESTY_INTERVAL` shifts/compresses long lapse durations
* whether the fraction of recoveries requiring amnesty changes
* whether recovery yield improves or degrades under shorter interval

You may not conclude:

* alignment, competence, or governance optimality
* generality beyond this geometry and pool
* anything about pool composition, K-sensitivity, or enforcement

---

## Classification Rules

Run B is **informative** if any occurs:

* Long-lapse mode shifts (e.g., L ≈ 20 → ≈10) or collapses
* Amnesty-required recovery fraction changes materially vs Run A
* Recovery Yield distribution shifts materially vs Run A

Run B is a **failure** only if:

* more than one parameter changed
* CTA logic violated (runs outside lapse or changes streaks incorrectly)
* verifiers/actions executed during lapse
* candidate pool policy deviates from `V060_DEFAULT`
* telemetry does not support episode-level `L`, `A`, `RY` reconstruction

---

## Orientation

Run A showed:

* recovery is achievable
* lapse is bimodal
* amnesty fires only in long lapses
* many recoveries occur without amnesty

Run B changes **one knob** to isolate causality:

**Does the CTA clock govern the long-lapse mode?**

Proceed exactly as specified.
