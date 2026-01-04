# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run J (Expressivity Rent Escalation / Stasis–Collapse Boundary)**

## Goal

Identify the **first genuine boundary** induced by **expressivity rent** once renewal cost is known to be non-binding under slack and forced succession is understood to prevent lock-in.

Run J answers:

> *As expressivity rent increases (reducing effective steps), where does the system transition from Growth to Stasis or Collapse, and by what mode?*

This run is **boundary-finding**, not exploratory.

---

## Scope (Binding)

### In scope

* Competitive successor selection (mixed generator)
* Expressivity tiers enforced by lease interface
* Rent charged as step-budget deduction
* Renewal consumes successor budget
* Forced succession (`max_successive_renewals`) enabled
* Escalation of **rent schedule only** (single axis)

### Out of scope

* Any semantic objectives or task utility
* Changes to renewal cost
* Changes to sentinel enforcement
* New successor types
* Multi-axis tuning (rent only)
* Audit-friction instrumentation (separate axis, not here)

If any out-of-scope change occurs, **abort the run**.

---

## Shared Preconditions (Must Hold)

All Run G invariants apply unchanged:

1. Rent charged at epoch start.
2. Renewal consumes successor budget.
3. E-Class for rent = active successor’s lease tier.
4. ViolationSuccessor excluded.
5. Mixed generator + TierFilterGenerator post-filtering.
6. `max_successive_renewals` enforced structurally.

Violation of any invariant invalidates the run.

---

## Shared Configuration (All J Runs)

### Core parameters

* `epoch_size = 100 cycles`
* `renewal_check_interval = 100`
* `msrw_cycles = 200`
* `steps_cap_epoch = 200`  (slack regime)
* `actions_cap_epoch = 100`
* `reject_immediate_bankruptcy = False`

### Renewal cost (fixed)

* `renewal_cost = 5`  (chosen inside known non-binding plateau)

### Guardrail (enabled)

* `max_successive_renewals = 15`  (forced succession on)

### Generator

* Mixed generator
* CBD successors included
* TierFilterGenerator applied post-generation
* Max retries per succession = 200
* Attack weights: `V052_RUNG_G2_ATTACK_WEIGHTS` (CBD_E3 = 0.30)

---

## Run J Structure

Run J consists of **four independent sub-runs**.
Each sub-run escalates **rent schedule only**.

Do **not** vary renewal cost, horizon, or guardrails across sub-runs.

---

## Pressure Axis: Rent Schedule Escalation (E3 Target)

Each sub-run fixes expressivity tier to **E3** and changes only `rent(E3)`.

All other E-class rents must remain **monotone** and sensible; E4 may be set but unused.

### Sub-Run Definitions

#### J0 — Baseline (Control)

* E3 rent = 40% of steps_cap_epoch
* With `steps_cap_epoch=200`: rent(E3)=80 → effective_steps=120

#### J1 — High Rent

* E3 rent = 60%  → rent=120 → effective_steps=80

#### J2 — Very High Rent

* E3 rent = 75%  → rent=150 → effective_steps=50

#### J3 — Extreme Rent

* E3 rent = 85%  → rent=170 → effective_steps=30

**Monotonicity requirement (binding):**
Ensure E0 < E1 < E2 < E3 < E4, and rent(E) ≤ steps_cap_epoch − 1.

---

## Expressivity Tier (Fixed)

* Fixed expressivity tier: **E3**
* CBD constrained to E3 (CBD_E3 enabled)

This run measures rent pressure at a single tier to avoid confounding tier shifts.

---

## Horizon

* `H = 30,000 cycles`

Rationale: sufficient to observe forced succession effects and renewal stability under pressure without invoking long-horizon accumulation (separate concern).

---

## Seeds

* 40, 41, 42, 43, 44

---

## Stop Rules (Binding)

Terminate a seed on first occurrence of:

1. **Renewal failure** (budget infeasibility at renewal check)
2. **Bankruptcy** (epoch terminated by rent exhausting budget)
3. **Revocation** (manifest violation)
4. **Horizon exhaustion**

Do not stop on degeneracy labels during execution; classify degeneracy post-hoc.

---

## Required Telemetry (Binding)

For each `(sub-run, seed)`:

### A) Core outcomes

* `S*`
* `total_successions`
* `total_renewals`
* `total_expirations`
* `total_bankruptcies`
* `total_revocations`
* `stop_reason`

### B) Rent / budget

* rent schedule used (full table)
* `effective_steps` (min/mean)
* `steps_used` (min/mean)
* remaining budget at renewal (min/mean)
* bankruptcy events (timestamps, clustering)

### C) Renewal stability

* renewal rate overall
* renewal rate by window (rolling over 10 renewal windows)
* time-to-first failure (if any)

### D) Competition intensity

* TierFilter proposal rejection rate
* number of succession proposals evaluated per succession event

---

## Post-hoc Regime Classification (Required)

Classify each seed into one of:

### Growth (G)

* Bankruptcy rate < 5% of tenures
* Renewal rate ≥ 90%
* No sustained collapse signatures

### Stasis (S)

* Renewal rate high (≥ 90%)
* Bankruptcy rare (< 5%)
* **But** forced successions yield no meaningful variation in manifest diversity (flat) and action budget utilization saturates at “minimal viable” patterns

(Use manifest diversity proxy: unique manifest action types / capability groups per tenure; flat over time.)

### Collapse (C)

Any of:

* Bankruptcy rate ≥ 30% of tenures
* Renewal rate < 50% for 3 consecutive renewal windows
* Reproducible early termination (renewal fail / bankruptcy clustering)

**Note:** If you cannot defensibly classify Stasis without execution traces, label as `STABLE_LOW_MARGIN` rather than inventing a claim.

---

## Required Reporting

### Summary table (Mandatory)

| Sub-Run | E3 Rent % | Effective Steps | Seeds | Failures | Bankruptcies | Mean Renewal Rate | Dominant Regime |
| ------- | --------- | --------------- | ----- | -------- | ------------ | ----------------- | --------------- |

### Failure mode table (Mandatory)

* renewal fail
* bankruptcy clustering
* revocation (should be ~0; if nonzero, suspect bug)
* hollow tenure rate (if defined)

### One conservative interpretation paragraph per sub-run (Mandatory)

Must state:

* axis escalated (E3 rent)
* observed regime (Growth/Stasis/Collapse/Stable-low-margin)
* what cannot be concluded

---

## Classification Rules (Binding)

A Run J sub-run is **informative** if any occurs:

* A reproducible collapse mode appears
* A clear survivability boundary is observed across rent levels
* Stability persists under extreme rent (negative result)

A Run J sub-run is a **failure** only if:

* rent is mischarged,
* monotonicity violated,
* renewal is subsidized,
* E-class/rent mismatch occurs,
* revocations occur without manifest violations at nontrivial rates.

---

## Guardrails

Do **not**:

* alter renewal cost
* remove forced succession
* change generator composition
* introduce semantic workloads
* interpret stability as “alignment solved”

---

## Orientation

H3 shows renewal cost is thresholded; Run I shows guardrail removal yields lock-in.

Run J now tests the remaining major axis:

> **Does expressivity rent induce a Stasis transition or a Collapse boundary under competition?**

Proceed exactly as specified.

---

## Binding Decisions (Q&A)

### Q1: Custom Rent Schedule Implementation

**Answer: (C)** Add `e3_rent_fraction: Optional[float]` to `ALSConfigV052`.

- If set, compute `rent(E3)` from it
- All other tiers use baseline fractions unchanged
- E0 remains hard-coded to 1 step

### Q2: Monotonicity for E0–E2

**Answer: (B)** Keep E0–E2 at baseline; only require they remain < E3.

- Baseline E0–E2 already satisfy monotonicity for all proposed E3 rents
- **E4 requirement (binding):** Set E4 = 180 (90% of cap=200) to preserve strict monotonicity even when E3=170

### Q3: Stasis Detection Metrics

**Answer:** Use existing per-tenure manifest diversity + one lightweight rolling indicator.

**Binding metrics:**
1. `manifest_action_type_count` per tenure (already present)
2. `manifest_signature` per tenure = frozenset of declared action types
3. Rolling window over last 10 tenures: `unique_manifest_signatures_in_window`

**Stasis proxy:** High renewal + low bankruptcy + forced successions occur, but `unique_manifest_signatures_in_window` stays near 1–2 for long stretches.

### Q4: Remaining Budget at Renewal

**Answer: (B)** Extend `RenewalEvent` with:
- `remaining_budget_at_check: int`
- `renewal_cost: int`
- `effective_steps: int`

Record at each renewal check where a decision is evaluated.

---

## Implementation Checklist

- [ ] Add `ALSConfigV052.e3_rent_fraction: Optional[float]`
- [ ] Compute rent(E3) from override; keep E0–E2 baseline; set E4=180
- [ ] Add `manifest_signature` to TenureRecord
- [ ] Add rolling unique manifest signature count (last 10 tenures)
- [ ] Extend RenewalEvent with budget telemetry fields
- [ ] Create run_j_v052.py with 4 sub-runs × 5 seeds
- [ ] Execute and generate report with regime classification

