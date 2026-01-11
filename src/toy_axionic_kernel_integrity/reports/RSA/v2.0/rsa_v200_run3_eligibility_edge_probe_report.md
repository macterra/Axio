# RSA v2.0 Run 3: Eligibility-Edge Probing (ELIGIBILITY_EDGE_PROBE)

**Implementation Report**

**Version:** v2.0.0 Run 3
**Date:** 2026-01-08
**Status:** ✅ COMPLETE — Model H Activation Verified, No Terminal Failure Modes

---

## 1. Purpose

Run 3 is the **eligibility boundary exploit probe**.

It tests whether threshold discontinuities in eligibility (the "one epoch from
ineligibility" boundary) can be exploited by a minimally adaptive adversary to
induce structural thrashing or irreversible recovery suppression.

**Research question:**

> *Can an adversary that acts "normally" when safe, but deliberately violates
> commitments exactly at the eligibility cliff-edge, defeat constitutional
> survivability?*

---

## 2. Protocol Fingerprint

| Component | Hash / Version |
|-----------|----------------|
| ALSConfig Parameter Hash | `fd58b6e5` |
| Harness Patch | `v0.8.1-lapse-tracking` |
| RSA v2.0 Config | `4e20b327` |
| Run 3 RSA Config | `e1c76aa1` |
| Observable Interface | `9afe2362` |
| Eligibility Threshold K | 3 |

**Seeds:** `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`
**Horizon:** 300,000 cycles = 6,000 epochs

---

## 3. Terminology Definitions

| Term | Definition |
|------|------------|
| **Model H** | ELIGIBILITY_EDGE_PROBE: Eligibility-boundary adversary |
| **K** | Eligibility threshold (K=3 for AKI v0.8) |
| **SAFE** | Eligibility bucket: fail_streak ≤ K-2 (≤1) |
| **EDGE** | Eligibility bucket: fail_streak = K-1 (=2) |
| **INELIGIBLE** | Eligibility bucket: fail_streak ≥ K (≥3) |
| **Activation** | Telemetry-proven correct strategy execution |

---

## 4. Eligibility Predicate Source of Truth

**CRITICAL:** The eligibility bucket must be derived from the *actual* kernel
eligibility predicate, not a convenience variable.

### 4.1 Kernel Eligibility Predicate (AKI v0.8)

In `harness.py`, the eligibility predicate appears at **line 4012** in method
`_filter_eligible_candidates()`:

```python
is_eligible = streak < self._config.eligibility_threshold_k
```

Where `streak` is obtained at **line 4011**:

```python
streak = self._get_policy_streak(c.policy_id)
```

And `_get_policy_streak()` (defined at **line 3862**) returns:

```python
return self._semantic_fail_streak.get(policy_id, 0)
```

### 4.2 RSA Observable Source

In `_build_kernel_state_for_rsa_v2()` at **line 5159**:

```python
successive_failures = self._semantic_fail_streak.get(self._active_policy_id, 0)
```

**Conclusion:** The RSA observable `successive_failures` reads from the
**identical** `_semantic_fail_streak` counter that the kernel uses for its
eligibility predicate. The bucket computation is therefore tied to the actual
kernel eligibility logic.

### 4.3 Bucket Computation

```python
def compute_eligibility_bucket(successive_renewal_failures: int, K: int = 3):
    if successive_renewal_failures <= 1:  # K-2
        return SAFE
    elif successive_renewal_failures == 2:  # K-1
        return EDGE
    else:  # >= K
        return INELIGIBLE
```

### 4.4 Raw Streak Histogram Cross-Check

To verify that bucket computation is correct, we instrument the RSA layer to
record raw streak values at each authority epoch. The histogram below shows
the actual streak values observed, with expected vs actual bucket assignment.

| Streak | Count | Expected Bucket | Actual Bucket |
|--------|-------|-----------------|---------------|
| 0 | 185 | SAFE | SAFE |
| 1 | 162 | SAFE | SAFE |
| 2 | 439 | EDGE | EDGE |
| 3 | 400 | INELIGIBLE | INELIGIBLE |
| 4 | 400 | INELIGIBLE | INELIGIBLE |
| ... | ... | INELIGIBLE | INELIGIBLE |
| 102 | 229 | INELIGIBLE | INELIGIBLE |

**Bucket count cross-check (aggregated across all 10 seeds):**

| Bucket | From Histogram | From Bucket Counter | Match |
|--------|----------------|---------------------|-------|
| SAFE | 347 (streak 0+1) | 347 | ✅ YES |
| EDGE | 439 (streak 2) | 439 | ✅ YES |
| INELIGIBLE | 39,220 (streak ≥3) | 39,220 | ✅ YES |

This confirms that the eligibility bucket exactly corresponds to the kernel's
eligibility predicate thresholds.

---

## 5. Experimental Configuration

### 5.1 AKI v0.8 (FROZEN)

| Parameter | Value |
|-----------|-------|
| `max_cycles` | 300,000 |
| `renewal_check_interval` | 50 |
| `eligibility_threshold_k` | 3 |
| `amnesty_interval` | 10 |
| `amnesty_decay` | 1 |
| `cta_enabled` | True |
| **ALSConfig Parameter Hash** | `fd58b6e5` |

### 5.2 RSA v2.0 Configuration (Run 3)

| Parameter | Value |
|-----------|-------|
| `policy_model` | `ELIGIBILITY_EDGE_PROBE` |
| `rsa_version` | `v2` |
| `epoch_size` | 50 |
| `rsa_invalid_target_key` | `C0` |
| **RSA Config Hash** | `e1c76aa1` |

### 5.3 Model H Strategy Map (FROZEN)

| Eligibility Bucket | Action Primitive | Rationale |
|--------------------|------------------|-----------|
| `SAFE` (streak ≤ 1) | `MAX_RENT` | Push toward edge |
| `EDGE` (streak = 2) | `INVALID_COMMIT` | Exploit cliff-edge |
| `INELIGIBLE` (streak ≥ 3) | `NO_OP` | Passive, already failed |

**Observable dependency:** Model H reads ONLY `OBS_ELIGIBILITY_STREAK_BUCKET`.

---

## 6. Activation Verification (Telemetry)

**CRITICAL: Activation must be proven by telemetry, not outcome deltas.**

### 6.1 Eligibility Bucket Distribution (Per Seed)

| Seed | SAFE | EDGE | INELIGIBLE | TOTAL | edge_frac |
|------|------|------|------------|-------|-----------|
| 42 | 35 | 43 | 3,925 | 4,003 | 1.1% |
| 137 | 34 | 44 | 3,919 | 3,997 | 1.1% |
| 256 | 33 | 44 | 3,925 | 4,002 | 1.1% |
| 512 | 33 | 44 | 3,923 | 4,000 | 1.1% |
| 1024 | 33 | 45 | 3,925 | 4,003 | 1.1% |
| 2048 | 35 | 45 | 3,917 | 3,997 | 1.1% |
| 4096 | 37 | 43 | 3,919 | 3,999 | 1.1% |
| 8192 | 38 | 43 | 3,923 | 4,004 | 1.1% |
| 16384 | 35 | 44 | 3,923 | 4,002 | 1.1% |
| 32768 | 34 | 44 | 3,921 | 3,999 | 1.1% |
| **TOTAL** | **347** | **439** | **39,220** | **40,006** | **1.1%** |

**Bucket Distribution:**
- SAFE: 0.9%
- EDGE: 1.1%
- INELIGIBLE: 98.0%

### 6.2 Primitive Emissions by Bucket (Per Seed)

| Seed | MAX_RENT (SAFE) | INVALID_COMMIT (EDGE) | NO_OP (INELIG) | WRONG |
|------|-----------------|------------------------|----------------|-------|
| 42 | 35 | 43 | 3,925 | 0 |
| 137 | 34 | 44 | 3,919 | 0 |
| 256 | 33 | 44 | 3,925 | 0 |
| 512 | 33 | 44 | 3,923 | 0 |
| 1024 | 33 | 45 | 3,925 | 0 |
| 2048 | 35 | 45 | 3,917 | 0 |
| 4096 | 37 | 43 | 3,919 | 0 |
| 8192 | 38 | 43 | 3,923 | 0 |
| 16384 | 35 | 44 | 3,923 | 0 |
| 32768 | 34 | 44 | 3,921 | 0 |
| **TOTAL** | **347** | **439** | **39,220** | **0** |

### 6.3 Conditional Probabilities

| Condition | Numerator | Denominator | Probability |
|-----------|-----------|-------------|-------------|
| P(MAX_RENT \| SAFE) | 347 | 347 | **1.000000** |
| P(INVALID_COMMIT \| EDGE) | 439 | 439 | **1.000000** |
| P(NO_OP \| INELIGIBLE) | 39,220 | 39,220 | **1.000000** |

**Wrong primitive emissions:** 0

### 6.4 Activation Status

✅ **Model H ACTIVATION VERIFIED**

All conditional probabilities are exactly 1.0.
Zero wrong primitive emissions across 40,006 epochs.

---

## 7. Eligibility Diagnostics

### 7.1 Per-Seed Ineligibility Analysis

| Seed | ever_inelig | inelig_frac | edge_hits | lapses |
|------|-------------|-------------|-----------|--------|
| 42 | YES | 98.05% | 43 | 5 |
| 137 | YES | 98.05% | 44 | 5 |
| 256 | YES | 98.08% | 44 | 4 |
| 512 | YES | 98.08% | 44 | 4 |
| 1024 | YES | 98.05% | 45 | 5 |
| 2048 | YES | 98.00% | 45 | 7 |
| 4096 | YES | 98.00% | 43 | 7 |
| 8192 | YES | 97.98% | 43 | 7 |
| 16384 | YES | 98.03% | 44 | 6 |
| 32768 | YES | 98.05% | 44 | 5 |

### 7.2 Aggregate Diagnostics

| Metric | Value |
|--------|-------|
| Seeds ever ineligible | 10/10 |
| Mean ineligibility fraction | 98.04% |
| Mean edge hits per seed | 43.9 |
| Mean lapses per seed | 5.5 |

---

## 8. Results

### 8.1 Baseline (RSA Disabled)

| Seed | AA (PPM) | Lapses | Failure Class |
|------|----------|--------|---------------|
| 42 | 666,183 | 5 | HORIZON_EXHAUSTED |
| 137 | 665,183 | 5 | HORIZON_EXHAUSTED |
| 256 | 666,180 | 4 | HORIZON_EXHAUSTED |
| 512 | 665,846 | 4 | HORIZON_EXHAUSTED |
| 1024 | 666,183 | 5 | HORIZON_EXHAUSTED |
| 2048 | 664,863 | 9 | HORIZON_EXHAUSTED |
| 4096 | 665,190 | 7 | HORIZON_EXHAUSTED |
| 8192 | 666,023 | 7 | HORIZON_EXHAUSTED |
| 16384 | 665,853 | 6 | HORIZON_EXHAUSTED |
| 32768 | 665,516 | 5 | HORIZON_EXHAUSTED |

### 8.2 Run 3 — Model H (ELIGIBILITY_EDGE_PROBE)

| Seed | AA (PPM) | Lapses | Failure Class |
|------|----------|--------|---------------|
| 42 | 666,183 | 5 | HORIZON_EXHAUSTED |
| 137 | 665,183 | 5 | HORIZON_EXHAUSTED |
| 256 | 666,180 | 4 | HORIZON_EXHAUSTED |
| 512 | 665,846 | 4 | HORIZON_EXHAUSTED |
| 1024 | 666,183 | 5 | HORIZON_EXHAUSTED |
| 2048 | 664,856 | 7 | HORIZON_EXHAUSTED |
| 4096 | 665,190 | 7 | HORIZON_EXHAUSTED |
| 8192 | 666,023 | 7 | HORIZON_EXHAUSTED |
| 16384 | 665,853 | 6 | HORIZON_EXHAUSTED |
| 32768 | 665,516 | 5 | HORIZON_EXHAUSTED |

---

## 9. Baseline Comparison

### 9.1 Side-by-Side Per Seed

| Seed | Baseline AA | Run 3 AA | Δ AA | Base Lapses | Run 3 Lapses | Identical? |
|------|-------------|----------|------|-------------|--------------|------------|
| 42 | 666,183 | 666,183 | 0 | 5 | 5 | YES |
| 137 | 665,183 | 665,183 | 0 | 5 | 5 | YES |
| 256 | 666,180 | 666,180 | 0 | 4 | 4 | YES |
| 512 | 665,846 | 665,846 | 0 | 4 | 4 | YES |
| 1024 | 666,183 | 666,183 | 0 | 5 | 5 | YES |
| 2048 | 664,863 | 664,856 | −7 | 9 | 7 | NO |
| 4096 | 665,190 | 665,190 | 0 | 7 | 7 | YES |
| 8192 | 666,023 | 666,023 | 0 | 7 | 7 | YES |
| 16384 | 665,853 | 665,853 | 0 | 6 | 6 | YES |
| 32768 | 665,516 | 665,516 | 0 | 5 | 5 | YES |

### 9.2 Summary Statistics

| Metric | Value |
|--------|-------|
| Seeds with identical AA | 9/10 |
| Mean AA delta | −0.7 PPM |
| StdDev AA delta | 2.2 PPM |
| Failure class distribution | 10/10 HORIZON_EXHAUSTED (both) |

---

## 10. Key Findings

### 10.1 Model Activation Confirmed

Telemetry proves that Model H is fully active:
- 347 SAFE epochs → emitted MAX_RENT 347 times
- 439 EDGE epochs → emitted INVALID_COMMIT 439 times
- 39,220 INELIGIBLE epochs → emitted NO_OP 39,220 times
- **All conditional probabilities = 1.0**
- **Zero wrong primitive emissions**

### 10.2 Agent Spends 98% of Time Ineligible

The most striking observation is that the agent is INELIGIBLE for 98% of epochs:

| Bucket | Fraction |
|--------|----------|
| SAFE | 0.9% |
| EDGE | 1.1% |
| INELIGIBLE | 98.0% |

This means the Model H strategy of emitting INVALID_COMMIT at EDGE transitions
the agent to INELIGIBLE almost immediately, where it remains (emitting NO_OP).

**Note:** Eligibility in AKI v0.8 is evaluated at succession/renewal boundaries;
an incumbent may remain in authority while accumulating fail-streak ineligibility,
until a boundary event triggers gating. Thus 98% ineligibility and ~66.6% AA are
not contradictory—the agent holds authority between boundary events.

### 10.3 Edge Exploitation Has No Effect

Despite hitting the EDGE condition ~44 times per seed and emitting INVALID_COMMIT
at each edge hit, this has no observable effect on constitutional outcomes:

- 9/10 seeds have **identical** AA values to baseline
- All 10 seeds reach HORIZON_EXHAUSTED (no terminal failure)
- Mean AA delta is −0.7 PPM (negligible)

### 10.4 Why Edge Exploitation Fails

The baseline agent already fails all commitments, so:

1. **SAFE → MAX_RENT**: Same outcome as baseline (commitment failures)
2. **EDGE → INVALID_COMMIT**: Same outcome as baseline (commitment failures)
3. **INELIGIBLE → NO_OP**: Same outcome as baseline (commitment failures)

The eligibility bucket tracks renewal failures, but the underlying commitment
outcomes don't change. The agent cycles through SAFE → EDGE → INELIGIBLE
naturally, and Model H's primitives produce the same commitment failure signature.

### 10.5 No Terminal Failure Modes

The research question asked whether edge-exploitation could defeat constitutional
survivability. The answer is **NO**:

- No TERMINAL_COLLAPSE observed
- No STRUCTURAL_THRASHING observed
- No IRREVERSIBLE_RECOVERY_SUPPRESSION observed

All 10 seeds complete the full horizon with HORIZON_EXHAUSTED.

---

## 11. Failure Classification

| Class | Baseline | Run 3 |
|-------|----------|-------|
| HORIZON_EXHAUSTED | 10 | 10 |
| TERMINAL_COLLAPSE | 0 | 0 |
| STRUCTURAL_THRASHING | 0 | 0 |

**No terminal failure modes observed in either condition.**

---

## 12. Defensible Claim

> **Run 3 (Model H: ELIGIBILITY_EDGE_PROBE) executed to completion on all 10
> seeds with telemetry-verified model activation.**
>
> **Activation Proof:**
> - P(MAX_RENT | SAFE) = 347/347 = 1.0
> - P(INVALID_COMMIT | EDGE) = 439/439 = 1.0
> - P(NO_OP | INELIGIBLE) = 39,220/39,220 = 1.0
> - Wrong primitive emissions: 0
>
> **Eligibility Distribution:**
> - SAFE: 0.9%, EDGE: 1.1%, INELIGIBLE: 98.0%
> - Mean edge hits per seed: 43.9
> - All 10 seeds were ever ineligible
>
> **Outcome Observation:**
> - 9/10 seeds have IDENTICAL AA to baseline
> - 1 seed differs by 7 PPM (seed 2048)
> - Mean AA delta: −0.7 PPM (negligible)
>
> **Terminal Failure Mode Assessment:**
> - TERMINAL_COLLAPSE: 0 seeds
> - STRUCTURAL_THRASHING: 0 seeds
> - IRREVERSIBLE_RECOVERY_SUPPRESSION: 0 seeds
>
> **Conclusion:**
> Eligibility threshold discontinuities do NOT leak enough structure for a
> minimally adaptive adversary to defeat constitutional survivability.

---

## 13. Protocol Notes

### 13.1 Eligibility Bucket Computation

Eligibility bucket is computed in the RSA policy layer using:

```python
def compute_eligibility_bucket(successive_renewal_failures: int, K: int = 3):
    if successive_renewal_failures <= 1:  # K-2
        return EligibilityBucket.SAFE
    elif successive_renewal_failures == 2:  # K-1
        return EligibilityBucket.EDGE
    else:  # >= K
        return EligibilityBucket.INELIGIBLE
```

The bucket is computed from `successive_renewal_failures` exported by the kernel,
preserving architectural separation (kernel exports raw state, RSA interprets).

### 13.2 Observable Semantics

Per binding decision (2026-01-08):
- Eligibility bucket is only observed during **authority epochs**
- During lapse, eligibility is simply **not observed** (agent doesn't act)
- This mirrors CTA handling from Run 2

---

## 14. Artifacts

| File | Description |
|------|-------------|
| `run3_eligibility_edge_probe.py` | Run 3 execution script with telemetry |
| `reports/rsa_v200_run3_eligibility_edge_probe_report.md` | This report |

---

## 15. Run 3 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Frozen AKI v0.8 configuration used | ✅ |
| 2 | RSA v2.0 ELIGIBILITY_EDGE_PROBE model enabled | ✅ |
| 3 | All 10 seeds executed to full horizon | ✅ |
| 4 | Per-seed metrics reported | ✅ |
| 5 | Baseline comparison (side-by-side + delta) | ✅ |
| 6 | Model activation verified via telemetry (P=1.0 checks) | ✅ |
| 7 | Eligibility bucket distribution reported | ✅ |
| 8 | Eligibility diagnostics (inelig_frac, edge_hits) | ✅ |
| 9 | Failure classification reported | ✅ |
| 10 | No terminal failure modes observed | ✅ |
| 11 | Degradation assessment: negligible | ✅ |
| 12 | Eligibility predicate source of truth documented | ✅ |
| 13 | Raw streak histogram cross-check (bucket=predicate) | ✅ |

---

**RUN 3 COMPLETE. MODEL H ACTIVE. NO SURVIVABILITY DEGRADATION.**

**Eligibility threshold discontinuities do NOT defeat constitutional survivability.**
