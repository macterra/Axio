# RSA v0.2 Run 3 — Burst-Scheduled Interference Sweep (Temporal Concentration Axis)

## Purpose

Measure whether **temporally concentrated, non-adaptive** post-verification interference can induce **asymptotic governance failure** (Structural Thrashing / Asymptotic DoS) even when the **average** corruption rate is modest.

Run 3 directly probes a plausible “last epistemic vulnerability”:

> **Fixed-time synchronization between interference bursts and constitutional timing.**

This is still epistemic, not adversarial: burst timing is a pure function of epoch index and fixed schedule params.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Evaluation timing (end-of-epoch verification only)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`), lapse semantics, scheduling
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (use frozen v0.2 baseline)
* Seed set (fixed)
* Failure thresholds doc (`docs/rsa_v020_failure_thresholds.md`) (frozen)
* Burst schedule definition: **PERIODIC ONLY**, `phase(epoch)` depends only on `(epoch, period, width, phase_offset)`
  No event anchoring. No runtime-state reference.

### Independent variables (Run 3 grid only)

Run 3 varies only these schedule parameters (plus burst probability):

* `rsa_burst_period_epochs`
* `rsa_burst_width_epochs`
* `rsa_burst_phase_offset` (frozen to a single value for this run)
* `rsa_p_burst_flip_ppm`

All other RSA and AKI parameters are frozen.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (baseline for v0.2)

Use the same frozen AKI config as Runs 1–2. Minimum required invariants:

```python
ALSConfigV080(
    max_cycles=300_000,             # frozen for v0.2 (yields 6000 epochs)
    eligibility_threshold_k=3,       # frozen baseline
    max_successive_renewals=3,       # frozen baseline
    amnesty_interval=10,             # frozen baseline
    amnesty_decay=1,                # frozen baseline
    cta_enabled=True,               # frozen baseline
)
```

Log and persist per sweep job:

* `horizon_epochs` (from harness)
* `tail_window = max(5000, horizon_epochs // 5)` (frozen rule)

### 1.2 RSA config (fixed for Run 3)

Run 3 uses only:

* `rsa_noise_model = BURST_SCHEDULED_FLIP`
* `rsa_scope = SEM_PASS_ONLY`
* `rsa_p_quiet_flip_ppm = 0` (frozen)
* periodic schedule only

```python
RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.BURST_SCHEDULED_FLIP,
    rsa_scope=RSAScope.SEM_PASS_ONLY,
    rsa_rng_stream="rsa_v020",

    rsa_burst_period_epochs=...,     # grid
    rsa_burst_width_epochs=...,      # grid
    rsa_burst_phase_offset=0,        # frozen for Run 3
    rsa_p_burst_flip_ppm=...,        # grid
    rsa_p_quiet_flip_ppm=0,          # frozen
)
```

Hard constraints:

* No corruption of individual keys in Run 3.
* No use of `PER_KEY`.
* No event anchoring or lapse-aligned schedules.

### 1.3 Seeds (fixed)

Use:

* `seeds = [40, 41, 42, 43, 44]`

---

## 2) Sweep Grid

### 2.1 Preregistered grid (epochs)

Use the preregistered values:

* `period ∈ {10, 50, 100, 200}`
* `width ∈ {1, 5, 10}`
* `phase_offset = 0` (frozen)
* `p_burst ∈ {50_000, 100_000, 200_000}` (5%, 10%, 20%)
* `p_quiet = 0`

This produces `4 × 3 × 1 × 3 = 36` schedule settings × 5 seeds = 180 runs.

No extra points. No adaptive refinement.

### 2.2 Optional “tooth” case (only if preregistered addendum exists)

If you have preregistered the spike test, include exactly one additional setting:

* `period=200`, `width=1`, `phase=0`, `p_burst=1_000_000`, `p_quiet=0`

If not preregistered, do not run it.

---

## 3) Model Semantics (must match spec)

### 3.1 Periodic burst phase function (frozen)

For each epoch:

```
x = (epoch + phase_offset) % period
phase = ACTIVE iff x < width else QUIET
```

### 3.2 Interference rule (SEM_PASS_ONLY)

* AKI computes `SEM_PASS_raw` normally.
* If `phase == ACTIVE`, RSA flips `SEM_PASS_raw` with probability `rsa_p_burst_flip_ppm`.
* If `phase == QUIET`, RSA flips with probability `rsa_p_quiet_flip_ppm` (frozen to 0).

**No other wires may be corrupted.**

### 3.3 Lapse invariant

If AKI does not evaluate commitments during lapse, RSA must not fire. Therefore:

* during `NULL_AUTHORITY` evaluation-absent epochs: `targets_epoch = 0`, `flips_epoch = 0`

This should already be enforced by tests; Run 3 scripts must still report it.

---

## 4) Metrics (must report per seed and aggregate)

Run 3 uses the same v0.2 metrics contract as Runs 1–2, plus burst telemetry.

### 4.1 Governance outcomes (per seed, per setting)

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class`
* `recovery_time_histogram` (RTD)
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`

Aggregate across seeds:

* mean/std AA and AAA
* class counts
* RTD aggregate summary
* distribution of `max_single_lapse_epochs`

### 4.2 RSA integrity metrics (required)

Per schedule setting (aggregate across seeds):

* `total_targets`
* `total_flips`
* `observed_flip_rate_ppm` (global; keep, but do not rely on it)
* `epochs_evaluated`
* `epochs_in_lapse`

### 4.3 Burst telemetry (required; primary for interpretation)

Per schedule setting (aggregate across seeds):

* `burst_duty_cycle_ppm = active_epochs * 1_000_000 // horizon_epochs`
  (or over evaluated epochs if that is how you defined it—be consistent and label it)
* `active_phase_flip_rate_ppm = active_flips * 1_000_000 // active_targets`
* `quiet_phase_flip_rate_ppm = quiet_flips * 1_000_000 // quiet_targets` (should be 0)

Also report:

* `effective_average_flip_rate_ppm = active_phase_flip_rate_ppm * burst_duty_cycle_ppm // 1_000_000`
  (approximate; for comparison only)

### 4.4 Pivotal flip telemetry (required)

A flip is pivotal iff:

```
SEM_PASS_raw != SEM_PASS_corrupted
```

Report per setting:

* `pivotal_flips`
* `pivotal_rate_ppm`

---

## 5) Failure Classification (Frozen; no reinterpretation)

Use the exact classifier in `toy_aki/rsa/metrics.py` with frozen constants in:

* `docs/rsa_v020_failure_thresholds.md`

Emit exactly one label per run:

* `STABLE_AUTHORITY`
* `BOUNDED_DEGRADATION`
* `STRUCTURAL_THRASHING`
* `ASYMPTOTIC_DOS`
* `TERMINAL_COLLAPSE`

No extra labels.

---

## 6) Expected qualitative shape (pre-registered hypotheses)

### H1 (temporal concentration does not dominate average rate)

For fixed `p_burst`, smaller duty cycles (width/period) should reduce average interference and therefore improve AA/AAA.

### H2 (possible resonance band)

There may exist specific periods (especially those comparable to constitutional timing scales like amnesty interval) where bursts disproportionately increase long lapses even at modest average rates.

### H3 (CTA absorption)

If governance holds, RTD should remain bounded and CTA should prevent heavy-tail growth for short bursts (width ≤ amnesty interval scale).

---

## 7) Script: `scripts/rsa_v020_run3_burst_correlated.py`

### Required output blocks

For each schedule setting `(period, width, p_burst)`:

1. **Run header**: AKI config hash, RSA config hash, horizon cycles, `horizon_epochs`, `tail_window`, phase offset, amnesty interval
2. **Burst descriptor**: period, width, computed duty cycle ppm
3. **Per-seed table**: AA_ppm, AAA_ppm, failure_class, lapse_count, total_lapse_epochs, max_single_lapse_epochs, active_phase_flip_rate_ppm, pivotal_rate_ppm
4. **Aggregate summary**: mean/std AA and AAA, class counts, RTD aggregate summary
5. **Burst telemetry block**: duty cycle, active/quiet flip rates, global observed flip rate, effective average rate estimate

### Skeleton pseudocode (structure, not implementation)

* loop over period in periods

  * loop over width in widths

    * loop over p_burst in p_bursts

      * set RSAConfig with those params (phase=0, p_quiet=0)
      * for each seed

        * run harness
        * collect metrics + RSA burst telemetry
      * aggregate and print required blocks

---

## 8) Definition of Done (Run 3)

Run 3 is complete when:

* all grid settings × seeds execute
* per-seed AA/AAA/RTD + failure class are reported per setting
* aggregate summaries are reported per setting
* burst telemetry (duty cycle + active/quiet flip rates) is reported per setting
* pivotal flip telemetry is reported per setting
* no additional sweep points or schedule modes are introduced

No refactors, no new models, no event anchoring, no parameter tuning.

---
