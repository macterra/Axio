# RSA v0.1 Run 2 — Robustness Surface Mapping

**(Semantic Baseline × Noise Intensity)**

## Purpose

Run 2 maps the **two-dimensional robustness surface** of AKI v0.8 under RSA noise by jointly varying:

* **Semantic baseline quality** (SV oracle), and
* **Epistemic noise intensity** (RSA flip rate),

while holding **all constitutional mechanics fixed**.

Interpretation: this run identifies **phase boundaries** between *robust*, *degraded*, and *DoS-prone* regimes, and tests whether the Run-1 threshold behavior persists across noise levels.

---

## 0) Binding Constraints (Non-Negotiable)

### 0.1 Frozen components (must not change)

* AKI kernel:

  * `ALSConfigV080`
  * `ALSHarnessV080`
* Eligibility rule: `K = 3`
* CTA parameters:

  * `amnesty_interval = 10`
  * `amnesty_decay = 1`
* Renewal / succession semantics
* Candidate pool composition and successor types
* SV oracle mechanism (deterministic hash-based)
* RSA noise model type (`FLIP_BERNOULLI`)
* RSA scope (`PER_CI`)
* Epoch definition and clocking
* Horizon and renewal interval
* Seed set

If **any** of the above change, the run is invalid.

---

## 1) Independent Variables (Exactly Two)

### Axis A — Semantic Baseline (SV)

Sweep:

```text
SVConfig.per_ci_pass_rate_ppm ∈
[600_000, 700_000, 800_000, 850_000, 900_000]
```

Corresponding expected SEM_PASS:

| per-Ci | SEM_PASS |
| -----: | -------: |
|   0.60 |    0.216 |
|   0.70 |    0.343 |
|   0.80 |    0.512 |
|   0.85 |    0.614 |
|   0.90 |    0.729 |

These values straddle the Run-1 boundary.

---

### Axis B — RSA Noise Intensity

Sweep:

```text
RSAConfig.rsa_p_flip_ppm ∈
[0, 50_000, 100_000, 150_000, 200_000]
```

Corresponding flip rates:

|  PPM |   % |
| ---: | --: |
|    0 |  0% |
|  50k |  5% |
| 100k | 10% |
| 150k | 15% |
| 200k | 20% |

RSA scope and model are **fixed**:

```python
rsa_scope = PER_CI
rsa_noise_model = FLIP_BERNOULLI
```

---

## 2) Configuration (Frozen)

### 2.1 AKI v0.8

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

Derived:

* `renewal_check_interval = 50`
* `total_epochs = 200`

---

### 2.2 Seeds

Use **exactly**:

```text
seeds = [40, 41, 42, 43, 44]
```

No resampling, no expansion.

---

## 3) Experimental Grid

Total configurations:

```text
5 SV baselines × 5 RSA noise levels × 5 seeds = 125 runs
```

Run ordering does not matter, but results must be grouped by **(SV, RSA)** cell.

---

## 4) Metrics (Required)

### 4.1 Per-Seed Metrics (per cell)

For each seed:

* `lapse_event_count`
* `lapse_epoch_count_total`
* `max_single_lapse_epochs`
* `authority_uptime_fraction`
* `recovery_count` (if available)
* `stutter_count` (if available)
* `recovery_yield` (if available)

---

### 4.2 Aggregate Metrics (per cell)

Across 5 seeds:

* mean ± std of:

  * `lapse_event_count`
  * `lapse_epoch_count_total`
  * `max_single_lapse_epochs`
  * `authority_uptime_fraction`
* distribution of `max_single_lapse_epochs`
* regime counts:

  * `N_ROBUST / N_DEGRADED / N_DOS`

---

### 4.3 RSA Integrity Metrics (per cell)

Aggregate across seeds:

* `sum_targets`
* `sum_flips`
* `observed_flip_rate_ppm`
* `sum_pivotal_flips`
* `pivotal_rate = pivotal / flips`

---

### 4.4 SV Calibration (Required, once per SV baseline)

For each SV baseline (independent of RSA):

* `obs_C0`, `obs_C1`, `obs_C2`
* `obs_SEM_PASS`
* expected values
* absolute deviation

This must be **raw SV (pre-RSA)**.

---

## 5) Regime Classification (Frozen)

Per seed, per cell:

* **DOS_REGIME**
  if `max_single_lapse_epochs > 5 × amnesty_interval`
  → threshold = 50 epochs

* **DEGRADED**
  if `lapse_epoch_fraction > 0.50`

* **ROBUST**
  otherwise

Aggregate regime label is counts, not averages.

---

## 6) Pre-Registered Hypotheses

### H4 — Robustness Surface Continuity

For fixed SV baseline, governance degrades monotonically with increasing RSA noise.

### H5 — Phase Boundary Shift

The critical RSA noise level that induces lapses increases with higher SV baseline.

### H6 — CTA Persistence

Across all non-DOS cells, lapse durations remain clustered near multiples of `amnesty_interval`.

---

## 7) Output Requirements

### 7.1 Tables

1. **Surface table**
   Rows = SV baseline
   Columns = RSA noise
   Cells = mean uptime + regime counts

2. **Boundary table**
   For each SV baseline, report:

   * highest RSA noise with 5×ROBUST
   * lowest RSA noise with any lapses

3. **CTA imprint table**
   For selected degraded cells:

   * remainder histogram mod `amnesty_interval`

---

### 7.2 Visuals (Optional but encouraged)

* Heatmap: `authority_uptime_fraction(SV, RSA)`
* Heatmap: `max_single_lapse_epochs(SV, RSA)`

(These are presentation only; do not change metrics.)

---

## 8) Script Naming

Create:

```text
scripts/rsa_run2_surface_sweep_v010.py
reports/rsa_v010_run2_implementation_report.md
```

Do **not** reuse Run-1 scripts.

---

## 9) Definition of Done (Run 2)

Run 2 is complete when:

* All 125 runs execute
* No frozen parameter is modified
* All required metrics are reported
* SV calibration is shown
* Regime classification is explicit per cell
* Hypotheses H4–H6 are evaluated as:

  * SUPPORTED / NOT SUPPORTED / INCONCLUSIVE
* Claims name:

  * SV oracle
  * RSA noise model
  * scope
  * geometry (K, CTA)

---

## 10) Explicit Non-Goals

Run 2 does **not** include:

* correlated noise
* SEM_PASS_ONLY scope
* adaptive adversaries
* changing K
* changing CTA interval
* longer horizons

Those are Run 3+ topics.

---

### Final Orientation for Opus

Run 2 is **cartography**, not optimization.

You are mapping where governance breaks, not trying to prevent it.

No clever fixes.
No parameter tuning.
No smoothing.

Measure the surface.

If you want, next I can:

* draft the exact stdout format Opus should emit, **or**
* pre-write the Run-2 report skeleton with section headers matching Run-1 style.
