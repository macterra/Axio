# RSA v0.1 Run 3 — DoS Threshold Search

**(High-Noise Escalation at Fixed Semantic Baseline)**

## Purpose

Run 3 searches for the **first true DoS regime** under increasingly hostile RSA verifier-outcome corruption, while holding semantic baseline fixed.

This is not another surface map. It is a **boundary-finding escalation**: identify the smallest RSA flip intensity that produces **persistent lapse** (DoS) rather than merely reduced uptime.

**Research question:** At what RSA corruption rate does CTA fail to restore governance under a marginal semantic baseline?

---

## 0) Binding Constraints (Non-Negotiable)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`) unchanged
* Eligibility rules (K = 3)
* CTA parameters:

  * `amnesty_interval = 10`
  * `amnesty_decay = 1`
* Renewal / succession / enforcement semantics
* Candidate pool composition and successor types
* SV oracle mechanism (deterministic hash oracle)
* RSA noise model:

  * `rsa_noise_model = FLIP_BERNOULLI`
  * `rsa_scope = PER_CI`
* Horizon:

  * `max_cycles = 10_000`
  * `renewal_check_interval = 50` → `total_epochs = 200`
* Seed set fixed

If any of these change, Run 3 is invalid.

---

## 1) Independent Variable (Single Axis)

### Axis: RSA noise intensity (high range)

Sweep:

```text
rsa_p_flip_ppm ∈ [300_000, 400_000, 500_000, 600_000]
```

i.e. **30%, 40%, 50%, 60%** per-Ci post-verification flips.

**Rationale:** Run 2 showed no DoS through 20%. Run 3 escalates aggressively to force the first DoS crossing.

---

## 2) Fixed Semantic Baseline (Choose One, Binding)

Use **one** SV baseline for Run 3. Do not sweep SV here.

### Recommended baseline

* `SVConfig.per_ci_pass_rate_ppm = 800_000`

Rationale:

* It is near the Run-1/Run-2 boundary where lapses first appear under moderate noise.
* It is sensitive enough to show failure modes without being already broken at RSA=0.

**Alternative (only if you explicitly want a harder system):**

* `per_ci_pass_rate_ppm = 850_000`

But pick **exactly one** baseline and freeze it for Run 3.

---

## 3) Configuration (Frozen)

### 3.1 AKI v0.8 config

```python
ALSConfigV080(
    max_cycles=10_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
```

### 3.2 SV config (fixed)

```python
SVConfig(per_ci_pass_rate_ppm=800_000)  # binding choice for Run 3
```

### 3.3 RSA config template

For each sweep point:

```python
RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
    rsa_scope=RSAScope.PER_CI,
    rsa_p_flip_ppm=<one of the sweep values>,
)
```

---

## 4) Seeds (Fixed)

Use:

```text
seeds = [40, 41, 42, 43, 44]
```

No expansion. No replacement.

Total runs:

```text
4 noise levels × 5 seeds = 20 runs
```

---

## 5) Metrics (Required)

Report **per seed** and **aggregate** for each noise level.

### 5.1 Core governance metrics (per seed)

* `authority_uptime_fraction`
* `lapse_event_count`
* `lapse_epoch_count_total`
* `max_single_lapse_epochs`
* `mean_lapse_duration = lapse_epoch_count_total / lapse_event_count` (0 if none)
* `final_state`: whether run ends in authority-held state or `NULL_AUTHORITY` (if available)

### 5.2 Recovery characterization (per seed)

* `recovery_count` (if available; else infer as lapse_event_count if each lapse has an exit event)
* `stutter_count` (if available)
* `recovery_yield` (if available)

### 5.3 RSA integrity metrics (aggregate across seeds)

* `sum_targets`, `sum_flips`
* `observed_flip_rate_ppm`
* `sum_pivotal_flips`, `pivotal_rate`

### 5.4 CTA imprint metrics (aggregate)

* Lapse duration remainder distribution mod `amnesty_interval`
* Fraction within ±1 epoch of a multiple of `amnesty_interval`

---

## 6) DoS / Degraded / Robust Classification (Frozen)

Per seed:

* **DOS_REGIME** if
  `max_single_lapse_epochs > 5 × amnesty_interval`
  → threshold = `50 epochs`

* **DEGRADED** if
  `lapse_epoch_fraction > 0.50`

* **ROBUST** otherwise

Also report **N_ROBUST / N_DEGRADED / N_DOS** per noise level.

---

## 7) Stop Rules (Measurement Only)

Do **not** terminate early. Run to horizon regardless.

But **flag** if any of these occur (for the report):

* `max_single_lapse_epochs` exceeds 50
* `authority_uptime_fraction < 50%`
* run ends in `NULL_AUTHORITY` (if trackable)

Run 3 is about *finding* these failures, not avoiding them.

---

## 8) Pre-Registered Hypotheses (Run 3)

### H7 — DoS emergence

There exists a flip rate in {30,40,50,60}% where at least one seed becomes DOS_REGIME.

### H8 — CTA clock imprint persists until DoS

In non-DoS runs, lapse durations remain clustered near amnesty multiples; in DoS runs, clustering weakens or becomes irrelevant because lapse dominates.

### H9 — Nonlinear transition

The transition from “rare lapses” to “persistent lapse” becomes sharper in this high-noise regime than in the 0–20% regime.

---

## 9) Output Requirements (Report Format)

Create:

* `scripts/rsa_run3_dos_threshold_v010.py`
* `reports/rsa_v010_run3_implementation_report.md`

### Required tables

1. **Per-noise summary table**
   For each `rsa_p_flip_ppm`:

* mean ± std uptime
* mean lapse epochs
* max of max_single_lapse_epochs across seeds
* regime counts (R/D/X)

2. **Per-seed table**
   Rows = seeds; columns include uptime, lapse_epoch_total, max_single_lapse, regime

3. **CTA imprint table**
   Remainder histogram mod 10 for all lapse events (optionally split by noise level)

### Required hypothesis validation section

Mark H7–H9 as:

* SUPPORTED / NOT SUPPORTED / INCONCLUSIVE
  with explicit computed checks.

---

## 10) Definition of Done (Run 3)

Run 3 is complete when:

* 20 runs execute (4 noise levels × 5 seeds)
* AKI kernel remains frozen
* SV baseline fixed (800k) across all runs
* RSA scope/model fixed (PER_CI, FLIP_BERNOULLI)
* All required metrics and regime classifications reported
* H7–H9 evaluated without narrative handwaving
* The first observed DoS threshold (if any) is identified as a specific noise level + seed(s)

---

## 11) Explicit Non-Goals

Run 3 does not include:

* SV sweeps
* correlated flips
* SEM_PASS_ONLY scope
* changes to K or CTA interval
* longer horizons

Those belong to later runs.

---

## Final Orientation for Opus

Run 3 is a **stress-to-failure** probe.

Do not smooth.
Do not “fix.”
Do not add heuristics.

Find the boundary.
