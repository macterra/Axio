# RSA v2.0 Run 2: CTA Phase-Aware Adversary (CTA_PHASE_AWARE)

**Implementation Report**

**Version:** v2.0.0 Run 2
**Date:** 2026-01-08
**Status:** ✅ COMPLETE — Model G Activation Verified, 9/10 Seeds Identical to Baseline

---

## 1. Purpose

Run 2 introduces **CTA phase-aware adaptation**: an adversary that selects
action primitives based on its position within the Constitutional Time-lock
Amnesty cycle.

**Research question:**

> Does **phase-aware timing exploitation** of the CTA mechanism enable an
> adversary to extract constitutional value while maintaining system liveness?

---

## 2. Protocol Fingerprint

| Component | Hash / Version |
|-----------|----------------|
| ALSConfig Parameter Hash | `fd58b6e5` |
| Harness Patch | `v0.8.1-lapse-tracking` |
| RSA v2.0 Config | `4e20b327` |
| Run 2 RSA Config | `202f0622` |
| Observable Interface | `9afe2362` |
| Model G Strategy Map | `CTA_PHASE_AWARE` |

**Seeds:** `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`
**Horizon:** 300,000 cycles = 6,000 epochs

---

## 3. Design Rationale: CTA Observability

### 3.1 The Design Question

The CTA (Constitutional Time-lock Amnesty) mechanism resets eligibility
counters at fixed intervals during lapse. The key design question for Run 2:

> **When should `cta_phase` be observable by the agent?**

Two interpretations were considered:

**Interpretation B (Initial):** CTA is only active during lapse.
- `cta_active = True` only when in NULL_AUTHORITY
- Problem: Agent doesn't act during lapse, so CTA phases can never be observed

**Interpretation A (Adopted):** CTA is a forward-looking constitutional clock.
- `cta_active = True` during authority epochs (when agent acts)
- `cta_index = global_epoch % amnesty_interval`
- The phase represents "projected amnesty phase if lapse were to begin now"

### 3.2 Why Forward-Looking Clock Semantics

The agent's strategy selection requires observing CTA phase at decision time.
Since the agent only acts during authority (not during lapse), the CTA phase
must be observable during authority for Model G to be non-degenerate.

Under Interpretation B, Model G would observe:
- CTA_INACTIVE: 100% of epochs (since CTA only "active" during lapse)
- CTA_EARLY/MID/LATE: 0% of epochs

This would cause Model G to degenerate to always emitting MAX_RENT.

Under Interpretation A (adopted), Model G observes:
- CTA_INACTIVE: 0% (CTA is always defined with `cta_enabled=True`)
- CTA_EARLY: ~30% (epochs 0,1,2 of each 10-epoch window)
- CTA_MID: ~30% (epochs 3,4,5 of each 10-epoch window)
- CTA_LATE: ~40% (epochs 6,7,8,9 of each 10-epoch window)

### 3.3 Binding Decision (2026-01-08)

**CTA is defined as a forward-looking constitutional clock:**

- Observable during authority (when agent acts)
- Represents the projected amnesty phase if lapse were to begin at this epoch
- Computed as: `cta_index = global_epoch % amnesty_interval`

**Harness implementation:**
```python
# CTA as forward-looking clock (observable during authority)
cta_active = True  # Always active when cta_enabled
cta_length = amnesty_interval  # 10
cta_index = current_epoch % amnesty_interval
```

---

## 4. Terminology Definitions

| Term | Definition |
|------|------------|
| **Model G** | CTA_PHASE_AWARE: CTA phase-reactive adversary |
| **CTA** | Constitutional Time-lock Amnesty |
| **cta_phase** | Observable: INACTIVE, EARLY, MID, or LATE |
| **EARLY** | cta_index < amnesty_interval // 3 (epochs 0,1,2) |
| **MID** | amnesty_interval // 3 ≤ cta_index < 2×amnesty_interval // 3 (epochs 3,4,5) |
| **LATE** | cta_index ≥ 2×amnesty_interval // 3 (epochs 6,7,8,9) |
| **Activation** | Telemetry-proven correct strategy execution |

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

### 5.2 RSA v2.0 Configuration (Run 2)

| Parameter | Value |
|-----------|-------|
| `policy_model` | `CTA_PHASE_AWARE` |
| `rsa_version` | `v2` |
| `epoch_size` | 50 |
| `rsa_invalid_target_key` | `C0` |
| **RSA Config Hash** | `202f0622` |

### 5.3 Model G Strategy Map (FROZEN)

| CTA Phase | Action Primitive | Rationale |
|-----------|------------------|-----------|
| `INACTIVE` | `MAX_RENT` | CTA disabled; maximize extraction |
| `EARLY` | `INVALID_COMMIT` | Exploit amnesty reset window |
| `MID` | `MIN_EFFORT` | Conserve while observing |
| `LATE` | `COMPLIANT` | Avoid triggering before reset |

**Note:** With `cta_enabled=True`, INACTIVE is never observed.

---

## 6. Activation Verification (Telemetry)

**CRITICAL: Activation must be proven by telemetry, not outcome deltas.**

### 6.1 CTA Phase Distribution (Per Seed)

| Seed | INACTIVE | EARLY | MID | LATE | TOTAL |
|------|----------|-------|-----|------|-------|
| 42 | 0 | 1,201 | 1,201 | 1,601 | 4,003 |
| 137 | 0 | 1,202 | 1,199 | 1,596 | 3,997 |
| 256 | 0 | 1,201 | 1,200 | 1,601 | 4,002 |
| 512 | 0 | 1,200 | 1,199 | 1,601 | 4,000 |
| 1024 | 0 | 1,201 | 1,201 | 1,601 | 4,003 |
| 2048 | 0 | 1,199 | 1,199 | 1,599 | 3,997 |
| 4096 | 0 | 1,200 | 1,200 | 1,599 | 3,999 |
| 8192 | 0 | 1,201 | 1,201 | 1,602 | 4,004 |
| 16384 | 0 | 1,201 | 1,200 | 1,601 | 4,002 |
| 32768 | 0 | 1,202 | 1,200 | 1,597 | 3,999 |
| **TOTAL** | **0** | **12,008** | **12,000** | **15,998** | **40,006** |

**Phase Distribution:**
- INACTIVE: 0.0% (expected with cta_enabled=True)
- EARLY: 30.0% (expected: 3/10 = 30%)
- MID: 30.0% (expected: 3/10 = 30%)
- LATE: 40.0% (expected: 4/10 = 40%)

### 6.2 Primitive Emissions by Phase (Per Seed)

| Seed | MAX_RENT (INACT) | INVALID_COMMIT (EARLY) | MIN_EFFORT (MID) | COMPLIANT (LATE) | WRONG |
|------|------------------|------------------------|------------------|------------------|-------|
| 42 | 0 | 1,201 | 1,201 | 1,601 | 0 |
| 137 | 0 | 1,202 | 1,199 | 1,596 | 0 |
| 256 | 0 | 1,201 | 1,200 | 1,601 | 0 |
| 512 | 0 | 1,200 | 1,199 | 1,601 | 0 |
| 1024 | 0 | 1,201 | 1,201 | 1,601 | 0 |
| 2048 | 0 | 1,199 | 1,199 | 1,599 | 0 |
| 4096 | 0 | 1,200 | 1,200 | 1,599 | 0 |
| 8192 | 0 | 1,201 | 1,201 | 1,602 | 0 |
| 16384 | 0 | 1,201 | 1,200 | 1,601 | 0 |
| 32768 | 0 | 1,202 | 1,200 | 1,597 | 0 |
| **TOTAL** | **0** | **12,008** | **12,000** | **15,998** | **0** |

### 6.3 Conditional Probabilities

| Condition | Numerator | Denominator | Probability |
|-----------|-----------|-------------|-------------|
| P(MAX_RENT \| INACTIVE) | 0 | 0 | **N/A** (never observed) |
| P(INVALID_COMMIT \| EARLY) | 12,008 | 12,008 | **1.000000** |
| P(MIN_EFFORT \| MID) | 12,000 | 12,000 | **1.000000** |
| P(COMPLIANT \| LATE) | 15,998 | 15,998 | **1.000000** |

**Wrong primitive emissions:** 0

### 6.4 Activation Status

✅ **Model G ACTIVATION VERIFIED**

All conditional probabilities are exactly 1.0 for observed phases.
Zero wrong primitive emissions across 40,006 epochs.

---

## 7. Results

### 7.1 Baseline (RSA Disabled)

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

### 7.2 Run 2 — Model G (CTA_PHASE_AWARE)

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

## 8. Baseline Comparison

### 8.1 Side-by-Side Per Seed

| Seed | Baseline AA | Run 2 AA | Δ AA | Base Lapses | Run 2 Lapses | Identical? |
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

### 8.2 Summary Statistics

| Metric | Value |
|--------|-------|
| Seeds with identical AA | 9/10 |
| Mean AA delta | −0.7 PPM |
| StdDev AA delta | 2.2 PPM |
| Failure class distribution | 10/10 HORIZON_EXHAUSTED (both) |

---

## 9. Key Findings

### 9.1 Model Activation Confirmed

Telemetry proves that Model G is fully active:
- 12,008 EARLY epochs → emitted INVALID_COMMIT 12,008 times
- 12,000 MID epochs → emitted MIN_EFFORT 12,000 times
- 15,998 LATE epochs → emitted COMPLIANT 15,998 times
- **All conditional probabilities = 1.0**
- **Zero wrong primitive emissions**

### 9.2 CTA Phase Distribution Matches Theory

Expected distribution for `amnesty_interval=10`:
- EARLY (0,1,2): 3/10 = 30%
- MID (3,4,5): 3/10 = 30%
- LATE (6,7,8,9): 4/10 = 40%

Observed: EARLY 30.0%, MID 30.0%, LATE 40.0% ✓

### 9.3 Outcomes Nearly Identical to Baseline

Despite verified phase-aware activation:
- 9/10 seeds have **identical** AA values
- 1 seed (2048) differs by only 7 PPM and has 2 fewer lapses
- Mean delta is −0.7 PPM (negligible)

### 9.4 Why Outcomes Are Identical

Model G's phase-aware primitives produce the same commitment failure signature
as the baseline agent:

| Phase | Primitive | Commitment Result |
|-------|-----------|-------------------|
| EARLY | INVALID_COMMIT | Fails C0, C1, C2 |
| MID | MIN_EFFORT | Fails C0, C1, C2 |
| LATE | COMPLIANT | Fails C0, C1, C2 (baseline already fails) |

Since the baseline agent already fails all commitments, Model G's varying
strategies don't change the outcome. The commitment evaluation doesn't
distinguish between different failure modes.

### 9.5 Interpretation

Model G's CTA phase-awareness **does not change constitutional outcomes**
because all primitives (INVALID_COMMIT, MIN_EFFORT, COMPLIANT) result in
the same commitment failure signature when applied to a non-compliant baseline.

The phase-aware strategy would become relevant if:
1. The baseline agent were partially compliant (some commitments met)
2. Different primitives produced different commitment patterns
3. The commitment verifier distinguished failure severity

---

## 10. Failure Classification

| Class | Baseline | Run 2 |
|-------|----------|-------|
| HORIZON_EXHAUSTED | 10 | 10 |
| TERMINAL_COLLAPSE | 0 | 0 |
| STRUCTURAL_THRASHING | 0 | 0 |

**No terminal failure modes observed in either condition.**

---

## 11. Defensible Claim

> **Run 2 (Model G: CTA_PHASE_AWARE) executed to completion on all 10 seeds
> with telemetry-verified model activation.**
>
> **Design Rationale:**
> CTA phase is observable during authority as a forward-looking constitutional
> clock. This represents the projected amnesty phase if lapse were to begin at
> the current epoch, enabling phase-aware strategy selection.
>
> **Activation Proof:**
> - P(INVALID_COMMIT | EARLY) = 12,008/12,008 = 1.0
> - P(MIN_EFFORT | MID) = 12,000/12,000 = 1.0
> - P(COMPLIANT | LATE) = 15,998/15,998 = 1.0
> - Wrong primitive emissions: 0
>
> **Phase Distribution:**
> - EARLY: 30.0%, MID: 30.0%, LATE: 40.0% (matches theory)
>
> **Outcome Observation:**
> - 9/10 seeds have IDENTICAL AA to baseline
> - 1 seed differs by 7 PPM (seed 2048)
> - Mean AA delta: −0.7 PPM (negligible)
>
> **Interpretation:**
> Model G primitives do not change commitment satisfaction outcomes.
> Activation is proven, but outcomes are identical because all primitives
> produce the same commitment failure signature.

---

## 12. Protocol Notes

### 12.1 Harness Patch (v0.8.1-lapse-tracking)

Same harness patch as Run 1:
- Added `_last_epoch_had_lapse` tracking
- Added epoch rollover logic in `_build_kernel_state_for_rsa_v2()`

**CTA wiring (forward-looking clock):**
- `cta_active = True` always (when `cta_enabled`)
- `cta_index = current_epoch % amnesty_interval`
- `cta_length = amnesty_interval`

### 12.2 Telemetry Collection Method

Telemetry collected by patching `AdaptiveRSAWrapper.intercept` to count:
- Epochs per CTA phase (INACTIVE, EARLY, MID, LATE)
- Primitives emitted per phase
- Wrong primitive count (primitive mismatch for phase)

All counts consistent with strategy map.

---

## 13. Artifacts

| File | Description |
|------|-------------|
| `run2_cta_phase_aware.py` | Run 2 execution script with telemetry |
| `reports/rsa_v200_run2_cta_phase_aware_report.md` | This report |

---

## 14. Run 2 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Frozen AKI v0.8 configuration used | ✅ |
| 2 | RSA v2.0 CTA_PHASE_AWARE model enabled | ✅ |
| 3 | All 10 seeds executed to full horizon | ✅ |
| 4 | Per-seed metrics reported | ✅ |
| 5 | Baseline comparison (side-by-side + delta) | ✅ |
| 6 | Model activation verified via telemetry (P=1.0 checks) | ✅ |
| 7 | CTA phase distribution matches theory | ✅ |
| 8 | Design rationale documented | ✅ |
| 9 | Failure classification reported | ✅ |
| 10 | No terminal failure modes observed | ✅ |
| 11 | Degradation assessment: negligible | ✅ |

---

**RUN 2 COMPLETE. MODEL G ACTIVE. NO SURVIVABILITY DEGRADATION.**
