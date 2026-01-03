
# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run H3-redux (Renewal Cost Phase Line)**

## Goal

Precisely characterize the **renewal-cost survivability boundary** discovered in Run H3 by replacing a single catastrophic point with a **measured phase line**.

Run H3-redux answers:

> *At what renewal cost does authority renewal transition from stable to impossible, holding rent, expressivity, workload, and competition fixed?*

This run is **boundary-measuring**, not exploratory.

---

## Scope (Binding)

### In scope

* Competitive successor selection (mixed generator)
* Expressivity tiers enforced by lease interface
* Rent charged as step-budget deduction
* Renewal consumes successor budget
* Forced succession (`max_successive_renewals`)
* Escalation of **renewal cost only**

### Out of scope

* Any semantic objectives or task utility
* Changes to rent schedule
* Changes to expressivity tiers
* Changes to generator composition
* Horizon escalation
* Multi-axis tuning

If any out-of-scope change occurs, **abort the run**.

---

## Shared Preconditions (Must Hold)

All Run G and Run H invariants apply unchanged:

1. Rent charged at epoch start.
2. Renewal consumes successor budget.
3. E-Class for rent = active successor’s lease tier.
4. ViolationSuccessor excluded.
5. Mixed generator + TierFilterGenerator post-filtering.
6. `max_successive_renewals` enforced structurally.

Violation of any invariant invalidates the run.

---
## Binding Decisions (Clarifications)

### 1) Stop Rule: Renewal Fail vs Bankruptcy Cascade

**Stop at the first renewal failure detection.**

* `time_to_first_renewal_fail` is the **cycle of the renewal check** at which the condition
  `remaining_budget < renewal_cost` is first evaluated as true.
* Record `terminal_mode = RENEWAL_FAIL`.

H3-redux measures the **renewal feasibility boundary**. Bankruptcy is a downstream lifecycle consequence. Do not conflate renewal infeasibility (the boundary) with expiration bookkeeping (an artifact).

**Implementation:** In `_check_renewal_with_rent()`, as soon as `remaining_budget < renewal_cost`, emit a `RenewalFailEvent`, set `stop_reason="RENEWAL_FAIL"`, and halt. Do not advance into the bankruptcy/expiration handler.

### 2) Counting Renewal Attempts

**Count only checks that reach the renewal decision point.**

A **renewal_attempt** occurs when:
1. A lease is active and eligible for renewal at this checkpoint
2. The renewal logic reaches the decision gate comparing available budget to renewal cost

* "Check fired but nothing to do" is **not** an attempt.
* "Check fired, lease eligible, decision evaluated" **is** an attempt.

`renewal_successes` is the subset of attempts that result in successful renewal.

### 3) Horizon = 5,000 Cycles

**Confirmed intentional.** H3-redux is boundary measurement. Failure occurs at the first renewal checkpoint where budget margin is insufficient. Long horizon adds runtime and post-boundary behavior with no additional threshold information.

### 4) CBD_E3 Weight Configuration

**Use existing `V052_RUNG_G2_ATTACK_WEIGHTS`** (CBD_E3 = 0.30) unchanged.

Do not invent a new weight set. Reusing a known configuration preserves comparability and prevents accidental tuning.

---
## Shared Configuration (All H3-redux Runs)

### Core parameters (unchanged from Run H)

* `epoch_size = 100 cycles`
* `renewal_check_interval = 100`
* `msrw_cycles = 200`
* `steps_cap_epoch = 100`
* `actions_cap_epoch = 100`
* `reject_immediate_bankruptcy = False`

### Generator (unchanged)

* Mixed generator
* CBD successors included
* TierFilterGenerator applied post-generation
* Max retries per succession = 200

---

## Experimental Axis

**Single escalated axis:** renewal cost

All other parameters remain **identical** across sub-runs.

---

## Run H3-redux Structure

Run H3-redux consists of **six independent sub-runs**, each testing a distinct renewal-cost level.

You must **not** combine these sub-runs.

---

## H3-redux — Renewal Cost Sweep

### Configuration (shared)

* `H = 5,000 cycles`
  (Longer horizons provide no additional signal; failure occurs at renewal.)
* `max_successive_renewals = 15`
* Fixed expressivity tier: **E3**
* Rent schedule: **Run G / Run H baseline**

  * E3 rent = 40
  * Effective steps = 60
* CBD_E3 weight ≥ 0.30

---

### Sub-Runs (Renewal Cost Levels)

| Sub-Run | Renewal Cost (steps) |
| ------- | -------------------- |
| H3-R4   | 4                    |
| H3-R5   | 5                    |
| H3-R6   | 6                    |
| H3-R7   | 7                    |
| H3-R8   | 8                    |
| H3-R9   | 9                    |

---

### Seeds

40, 41, 42, 43, 44
(All seeds must be run at each renewal-cost level.)

---

## Stop Rules (Per Sub-Run)

Terminate a seed immediately on the first occurrence of:

1. **Renewal failure** due to insufficient remaining budget
2. **Bankruptcy**
3. **Revocation**
4. **Horizon reached without failure**

Do **not** terminate for degeneracy, plateau, or low novelty.
H3-redux measures **budget feasibility only**.

---

## Required Telemetry (Binding)

For each `(renewal_cost, seed)` pair record:

### A) Renewal Metrics

* `renewal_attempts`
* `renewal_successes`
* `renewal_success_rate`
* `time_to_first_renewal_fail` (cycles)

### B) Budget Telemetry (at renewal attempt)

* `effective_steps`
* `steps_used`
* `remaining_budget`
* `renewal_cost`

### C) Terminal Classification

One of:

* `RENEWAL_FAIL`
* `BANKRUPTCY`
* `REVOCATION`
* `HORIZON_END`

---

## Required Reporting

### Summary Table (Mandatory)

| renewal_cost | mean_success_rate | std | mean_time_to_fail | dominant_terminal_mode |
| ------------ | ----------------- | --- | ----------------- | ---------------------- |

### Phase Line Plot (Recommended)

* X-axis: `renewal_cost`
* Y-axis: `renewal_success_rate`

Mark the inferred collapse threshold.

---

## Interpretation Constraints (Binding)

You **may** conclude:

* Whether renewal collapse is sharp or graded
* Whether failure is deterministic or stochastic
* The approximate renewal-cost threshold for E3 under baseline rent

You **may not** conclude:

* Long-horizon survivability
* General safety or alignment properties
* Applicability beyond E3
* Effects of rent or expressivity changes

---

## Classification Rules

Run H3-redux is **informative** if:

* Renewal success transitions sharply across renewal-cost levels, **or**
* A narrow stochastic band is observed, **or**
* Stability persists through `renewal_cost = 9`

Run H3-redux is a **failure** only if:

* renewal cost is mischarged,
* renewal is subsidized,
* rent or E-Class semantics differ across sub-runs,
* revocations occur without manifest violations.

---

## Guardrails

Do **not**:

* alter rent fractions,
* adjust generator weights mid-run,
* disable CBD competition,
* increase horizon “to see what happens,”
* interpret renewal collapse as agent misbehavior.

---

## Orientation

Run H3 established that **renewal can be the dominant survivability constraint**.

Run H3-redux exists to measure that constraint precisely.

This run converts a single failure into a **phase boundary**.

Execute exactly as specified.
