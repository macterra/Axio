# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run K (Succession Geometry Sweep)**

## Goal

Determine whether **forced, discrete authority turnover** is merely a procedural guardrail or a **constitutive stabilizer** of institutional dynamics under ALS-E.

Run K answers:

> *How does the system behave as succession pressure is varied—holding rent, renewal cost, renewal timing, tier, detector, and generator constant—and does a stable “constitutional band” exist between lock-in and thrash?*

Run K is **structural and classificatory**, not exploratory.

---

## Scope (Binding)

### In scope

* Competitive successor selection (mixed generator)
* Expressivity tiers enforced by lease interface
* Rent charged as step-budget deduction
* Renewal consumes successor budget
* Fixed renewal timing geometry
* **Forced succession frequency only** (`max_successive_renewals`)

### Out of scope

* Any semantic objectives or task utility
* Changes to rent schedule
* Changes to renewal cost
* Changes to renewal-check timing
* Changes to expressivity tier
* Generator reweighting
* Detector changes
* Multi-axis tuning

If any out-of-scope change occurs, **abort the run**.

---

## Shared Preconditions (Must Hold)

All v0.5.2 invariants apply unchanged unless explicitly overridden:

1. Rent charged at epoch start.
2. Renewal consumes successor budget.
3. E-Class for rent = active successor’s lease tier.
4. ViolationSuccessor excluded.
5. Mixed generator + TierFilterGenerator post-filtering.
6. Renewal checks use **fixed geometry**.
7. Degeneracy detector enabled and terminal.

Violation of any invariant invalidates the run.

---

## Shared Configuration (All K Runs)

### Core parameters (fixed)

* `epoch_size = 100 cycles`
* `steps_cap_epoch = 200`
* `actions_cap_epoch = 100`
* `msrw_cycles = 200`
* `renewal_cost = 5`
* `reject_immediate_bankruptcy = False`

### Renewal Geometry (fixed)

* `renewal_check_interval = 90`

Rationale: intentionally **non-commensurate** with epoch size to avoid J/J2 resonance artifacts.

---

### Expressivity / Rent (fixed)

* Fixed expressivity tier: **E3**
* **E3 rent = 80** (40%)
  → `effective_steps = 120`

Rationale: baseline lies well inside the known stable region to ensure failures—if any—are due to **succession pressure**, not budget infeasibility.

---

### Generator (fixed)

* Mixed generator
* CBD successors included
* TierFilterGenerator applied post-generation
* Max retries per succession = 200
* Attack weights: `V052_RUNG_G2_ATTACK_WEIGHTS`

---

## Experimental Axis

**Single varied parameter:** `max_successive_renewals`

All other parameters must remain identical across sub-runs.

---

## Run K Structure

Run K consists of **four independent sub-runs**, each representing a different level of forced turnover pressure.

You must **not** combine sub-runs.

---

## K Sub-Runs — Succession Pressure Sweep

### K0 — No Forced Succession (Lock-In Control)

* `max_successive_renewals = 1_000_000` (effectively ∞)

Purpose: reproduce and anchor **institutional lock-in** behavior observed in Run I under otherwise stable geometry.

---

### K1 — Low Turnover Pressure

* `max_successive_renewals = 100`

Purpose: test whether very infrequent forced turnover meaningfully breaks lock-in or merely delays it.

---

### K2 — Moderate Turnover (Constitutional Baseline)

* `max_successive_renewals = 15`

Purpose: evaluate the currently favored “constitutional” setting under fixed geometry and rent.

---

### K3 — High Turnover Pressure

* `max_successive_renewals = 3` (fixed)

Purpose: test for **authority thrash**, premature turnover, and MSRW-limited instability.

> **Note:** If additional MSRW interaction data is needed, add K4 = 5 as a separate sub-run.

---

## MSRW Semantic Constraint (Binding)

**MSRW must not gate renewal checks or renewal execution; it gates successor replacement only.**

If MSRW gates renewal in the implementation, abort Run K and fix before proceeding.

---

## Horizon

* `H = 30,000 cycles`

Chosen to allow multiple full tenure sequences even under low turnover pressure.

---

## Seeds

* 40, 41, 42, 43, 44

Must match prior runs for cross-comparison.

---

## Stop Rules (Binding)

Terminate a seed on first occurrence of:

1. **Degeneracy detector trigger**
2. **Renewal failure**
3. **Bankruptcy**
4. **Revocation**
5. **Horizon exhaustion**

Terminal cause must be recorded explicitly.

---

## Required Telemetry (Binding)

For each `(sub-run, seed)`:

### A) Succession Dynamics

* `max_successive_renewals`
* `total_tenures`
* `tenures_per_horizon`
* `mean_residence_time`
* `residence_time_distribution`

---

### B) Renewal Outcomes

* `renewal_attempts`
* `renewal_successes`
* `renewal_success_rate`
* renewals per tenure

---

### C) Authority Diversity

* `successor_identity_entropy` (rolling window + final)
* `manifest_signature_diversity`
* proposal rejection rate

---

### D) Lifecycle & Termination

* `terminal_stop_reason`
* degeneracy classification (if any)
* renewal-fail events
* bankruptcy events
* revocations

---

## Post-hoc Regime Classification (Required)

Classify each `(sub-run, seed)` using **institutional dynamics**, not quality:

* **LOCK-IN**

  * tenures ≈ 1
  * entropy → 0
  * renewals dominate horizon

* **CONSTITUTIONAL STABILITY**

  * tenures > 1
  * entropy bounded away from 0
  * renewal rate remains high
  * no spam or thrash detection

* **THRASH**

  * short residence times
  * high tenure count
  * MSRW pressure or spam degeneracy

Detector remains the terminal authority.

---

## Required Reporting

### Summary Table (Mandatory)

| Sub-Run | max_successive_renewals | Tenures | Mean Residence | Renewal Rate | Entropy | Dominant Regime | Terminal Cause |
| ------- | ----------------------- | ------- | -------------- | ------------ | ------- | --------------- | -------------- |

---

### Phase Line Visualization (Mandatory)

Single axis plot or table showing:

`max_successive_renewals → regime outcome`

---

### One Conservative Interpretation Paragraph per Sub-Run

Must state:

* turnover pressure tested
* whether lock-in, stability, or thrash appeared
* what **cannot** be inferred beyond succession geometry

---

## Interpretation Constraints (Binding)

You **may** conclude:

* Whether forced succession is constitutive or procedural
* Whether a stable “constitutional band” exists
* Where lock-in and thrash boundaries lie under fixed geometry

You **may not** conclude:

* General governance optimality
* Task competence or semantic performance
* Cross-tier generality
* Long-horizon inevitability claims

---

## Classification Rules

Run K is **informative** if **any** occurs:

* lock-in at low turnover
* thrash at high turnover
* a non-empty stable band in between

Run K is a **failure** only if:

* renewal timing differs across sub-runs
* rent or renewal cost deviates from spec
* detector configuration changes
* turnover pressure is not the sole varied axis

---

## Orientation

Run I showed **lock-in without forced succession**.
Run G showed **stability with forced succession**.

**Run K determines whether forced turnover is merely a training wheel—or a constitutional requirement.**

Proceed exactly as specified.

