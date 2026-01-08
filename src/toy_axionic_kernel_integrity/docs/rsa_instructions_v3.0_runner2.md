# RSA v3.0 Run 2 — Eligibility Edge Oscillator (EDGE_OSCILLATOR)

## Purpose

Run 2 is the **multi-epoch eligibility edge-riding probe**.

It tests whether a kernel-external adversary with **finite exercised internal state** can exploit the **eligibility cliff edge** by alternating behavior across consecutive `ELIG_EDGE` epochs—“feinting” with low effort on one edge epoch and violating commitments on the next—to induce repeated ineligibility, renewal failure cascades, or recovery suppression.

Run 2 answers one question:

> *Can a stateful adversary that oscillates only at the eligibility edge induce **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression** under the frozen AKI constitution?*

This is the v3.0 stateful generalization of v2.0’s edge probing: not merely “attack when on the edge,” but **use memory to coordinate across edge epochs**.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All Run 0 frozen components remain frozen:

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k` (fail-streak semantics; frozen baseline)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`)
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (use frozen v3.0 baseline)
* Seed set (fixed)
* Metrics computation (`AA`, `AAA`, `RTD`) and failure classifier (frozen)
* Observable Outcome Interface (frozen)
* Action Primitive Set (frozen)
* Determinism + RNG stream separation (frozen)
* Strategy map totality requirement (frozen)

### Run-specific independent variable (single axis)

Run 2 sets **exactly one** run-specific choice:

* `Model K: EDGE_OSCILLATOR`

No other parameters vary.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config

Use the same frozen AKI configuration as Run 0 and all v3.0 runs.

```python
ALSConfigV080(
    max_cycles=300_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
```

---

### 1.2 RSA v3.0 config — Run 2

```python
RSAConfig(
    rsa_enabled=True,
    rsa_model="EDGE_OSCILLATOR",
    rsa_rng_stream="rsa_v300",

    # capacity must satisfy rsa_max_internal_states ≥ 2 for Model K
    rsa_max_internal_states=8,   # any value ≥ 2 is acceptable; keep consistent across v3.0 if desired
)
```

**Requirements:**

* `rsa_max_internal_states` MUST be ≥ 2
* No mid-run edits; no tuning by outcome

---

### 1.3 Model K definition (must match spec)

**State:** 1-bit toggle
**Initial state:** `S0 = 0`

**Policy:**

| Condition | State | Action                |
| --------- | ----- | --------------------- |
| ELIG_EDGE | 0     | ACTION_MIN_EFFORT     |
| ELIG_EDGE | 1     | ACTION_INVALID_COMMIT |
| otherwise | *     | ACTION_COMPLIANT      |

**State update:**

Toggle state on each epoch where:

```
OBS_ELIGIBILITY_STREAK_BUCKET == ELIG_EDGE
```

Otherwise state unchanged.

No other conditionals.

---

### 1.4 Seeds (fixed)

Use the same seed battery as Run 0:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 2) Pre-run Gates (Mandatory)

Run 2 must not execute unless all v3.0 acceptance tests pass, including exercised-state checks.

### 2.1 Static exercised-state capability check (gate)

From the Strategy Map alone, verify there exists an observable bucket `O` such that:

```
π(O, 0) != π(O, 1)
```

For Model K, this must hold for `O` where `ELIG_EDGE`.

If false: abort before any adversary run.

### 2.2 Strategy map totality (gate)

Verify both maps are total over:

```
(observable_bucket × {0,1})
```

Where `observable_bucket` excludes `OBS_EPOCH_INDEX`.

---

## 3) Execution

For each seed:

1. Initialize AKI harness with frozen config
2. Initialize RSA adversary:

   * `seed_rsa = stable_hash_64(seed, "rsa", "rsa_v300")` (even if unused)
   * `S0 = 0`
3. Run full horizon; no early termination
4. Log per-epoch telemetry and per-seed metrics

---

## 4) Telemetry (Required)

### 4.1 Per epoch (must log)

In addition to standard AKI telemetry:

* `epoch`
* `rsa_enabled` (True)
* `rsa_model` (EDGE_OSCILLATOR)
* internal state `S_t` (pre-update)
* action emitted (primitive)
* action accepted (kernel legality)
* `OBS_ELIGIBILITY_STREAK_BUCKET`
* all other observable buckets

### 4.2 Run-level diagnostics (must compute)

* `distinct_states_observed = |{S_t}|`
* `state_transition_count` (toggles)
* `edge_epoch_count` (epochs where `ELIG_EDGE`)
* `invalid_commit_emission_count`
* `min_effort_emission_count`
* `edge_attack_ratio = invalid_commit_emission_count / max(edge_epoch_count, 1)`

---

## 5) Metrics (must report per seed and aggregate)

Run 2 reports exactly the same metrics and derived diagnostics as Run 0.

### 5.1 Governance outcomes (per seed)

* AA_ppm
* AAA_ppm
* RTD
* failure_class
* lapse_count
* total_lapse_epochs
* max_single_lapse_epochs

### 5.2 Derived diagnostics (per seed)

* ever_ineligible
* ineligibility_fraction
* renewal_success_rate_ppm
* renewal_check_epochs_count
* renewals_succeeded

### 5.3 Aggregate summary (across seeds)

* mean/std AA and AAA
* counts by failure_class
* RTD aggregate summary
* mean/std of renewal_success_rate_ppm and ineligibility_fraction

---

## 6) Exercised State Verification (Run-Time, Mandatory)

For each seed-run, verify:

```
distinct_states_observed ≥ 2
```

If not, the run is invalid.

Interpretation discipline: this check is about **state evolution**, not about how often `ELIG_EDGE` occurs. Even rare edge epochs should produce toggling at least once in most horizons; if not, that is an observed property, not a reason to change the spec.

---

## 7) Failure Classification (Frozen)

Use the exact classifier in `toy_aki/rsa/metrics.py`.

No reinterpretation. Exactly one label per seed-run.

---

## 8) Output Format

### Script name

```
scripts/rsa_v300_run2_edge_oscillator.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * RSA config hash
   * horizon epochs
   * tail window

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction
   * edge_epoch_count, invalid_commit_emission_count, min_effort_emission_count
   * distinct_states_observed, state_transition_count

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction
   * aggregate edge_epoch_count and edge_attack_ratio

4. **Integrity block**

   * exercised_state_static_ok (True)
   * exercised_state_dynamic_ok rate (how many seeds passed)
   * state_transition_count totals

---

## 9) Definition of Done (Run 2)

Run 2 is complete when:

* all acceptance tests pass
* all seeds execute full horizon
* exercised-state checks pass for every seed
* metrics + telemetry are logged
* failure classes are produced automatically
* results are comparable to Run 0 baseline and Runs 1a/1b

No refactors. No mid-run tuning. No additional variants.

---

## Role of Run 2 in v3.0

Run 2 tests whether **memory across edge epochs** enables adversarial coordination that a purely reactive policy cannot achieve.

If Run 2 induces collapse or irreversible suppression, then the boundary is not “state in general,” but specifically **state enabling multi-step exploitation of eligibility discontinuities**.

If it does not, the remaining v3.0 probe is **phase-transition exploitation (Run 3)**.
