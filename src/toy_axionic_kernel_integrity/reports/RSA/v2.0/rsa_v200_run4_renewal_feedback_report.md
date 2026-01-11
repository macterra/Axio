# RSA v2.0 Run 4: Renewal-Outcome Feedback (RENEWAL_FEEDBACK)

**Implementation Report**

**Version:** v2.0.0 Run 4
**Date:** 2026-01-08
**Status:** ✅ COMPLETE — Model I Activation Verified, No Terminal Failure Modes

---

## 1. Purpose

Run 4 is the **renewal observability exploitation probe**.

It tests whether renewal outcomes—even in a bucketed, semantics-free form—provide
enough feedback for an adversary to synchronize misuse with renewal dynamics
and induce **structural thrashing** or **irreversible recovery suppression**.

**Research question:**

> *Can an adversary that conditions behavior on renewal outcomes
> (succeeded/failed/not-attempted) defeat constitutional survivability
> under RSA constraints?*

---

## 2. Protocol Fingerprint

| Component | Hash / Version |
|-----------|----------------|
| ALSConfig Parameter Hash | `fd58b6e5` |
| Harness Patch | `v0.8.1-lapse-tracking` |
| RSA v2.0 Config | `91d605eb` |
| Observable Interface | `9afe2362` |
| Eligibility Threshold K | 3 |

**Seeds:** `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`
**Horizon:** 300,000 cycles = 6,000 epochs

---

## 3. Terminology Definitions

| Term | Definition |
|------|------------|
| **Model I** | RENEWAL_FEEDBACK: Renewal-outcome adversary |
| **SUCCEEDED** | Renewal check fired and renewal was granted |
| **FAILED** | Renewal check fired and renewal was denied |
| **NOT_ATTEMPTED** | No renewal check fired in the prior epoch |
| **Activation** | Telemetry-proven correct strategy execution |

---

## 4. Renewal Outcome Observable Source of Truth

**CRITICAL:** The renewal outcome must be derived from the *actual* kernel
renewal decision, not from downstream effects or inference.

### 4.1 Kernel Renewal Decision Point (AKI v0.8)

In `harness.py`, the renewal decision occurs in method `_check_renewal_with_rent()`.
The V080 override tracks the outcome at **line ~5102**:

```python
def _check_renewal_with_rent(self) -> None:
    # Record count of renewal events before parent call
    events_before = len(self._renewal_events)

    # Call parent implementation
    super()._check_renewal_with_rent()

    # Check if a renewal event was added
    if len(self._renewal_events) > events_before:
        latest_event = self._renewal_events[-1]
        if latest_event.cycle == self._cycle:
            self._last_renewal_outcome = latest_event.success  # True/False
```

### 4.2 Observable Mapping

In `_build_kernel_state_for_rsa_v2()`:

```python
last_renewal_result = self._last_renewal_outcome  # True/False/None
```

In `AdaptiveRSAWrapper.sample_observable()`:

```python
if last_renewal_result is None:
    renewal_outcome = RenewalOutcome.NOT_ATTEMPTED
elif last_renewal_result:
    renewal_outcome = RenewalOutcome.SUCCEEDED
else:
    renewal_outcome = RenewalOutcome.FAILED
```

### 4.3 Epoch Rollover Semantics

Per binding decision:
- At epoch t=0: `OBS_RENEWAL_OUTCOME = NOT_ATTEMPTED` (no prior epoch)
- At epoch t > 0: `OBS_RENEWAL_OUTCOME` reflects the outcome from epoch t-1
- If no renewal check fired in epoch t-1, outcome is `NOT_ATTEMPTED`

The `_last_renewal_outcome` field is reset to `None` at each epoch boundary
after sampling, ensuring stale data does not persist.

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

### 5.2 RSA v2.0 Configuration (Run 4)

| Parameter | Value |
|-----------|-------|
| `policy_model` | `RENEWAL_FEEDBACK` |
| `rsa_version` | `v2` |
| `epoch_size` | 50 |
| `rsa_invalid_target_key` | `C0` |
| **RSA Config Hash** | `91d605eb` |

### 5.3 Model I Strategy Map (FROZEN)

| Renewal Outcome | Action Primitive | Rationale |
|-----------------|------------------|-----------|
| `SUCCEEDED` | `MAX_RENT` | Exploit after successful renewal |
| `FAILED` | `INVALID_COMMIT` | Attack after renewal failure |
| `NOT_ATTEMPTED` | `MIN_EFFORT` | Passive when no renewal event |

**Observable dependency:** Model I reads ONLY `OBS_RENEWAL_OUTCOME`.

---

## 6. Activation Verification (Telemetry)

**CRITICAL: Activation must be proven by telemetry, not outcome deltas.**

### 6.1 Renewal Outcome Distribution (Per Seed)

| Seed | SUCCEEDED | FAILED | NOT_ATTEMPTED | TOTAL | succ_frac |
|------|-----------|--------|---------------|-------|-----------|
| 42 | 3,957 | 39 | 7 | 4,003 | 98.9% |
| 137 | 3,951 | 39 | 7 | 3,997 | 98.8% |
| 256 | 3,957 | 39 | 6 | 4,002 | 98.9% |
| 512 | 3,955 | 39 | 6 | 4,000 | 98.9% |
| 1024 | 3,957 | 39 | 7 | 4,003 | 98.9% |
| 2048 | 3,949 | 39 | 9 | 3,997 | 98.8% |
| 4096 | 3,951 | 39 | 9 | 3,999 | 98.8% |
| 8192 | 3,956 | 39 | 9 | 4,004 | 98.8% |
| 16384 | 3,955 | 39 | 8 | 4,002 | 98.8% |
| 32768 | 3,953 | 39 | 7 | 3,999 | 98.8% |
| **TOTAL** | **39,541** | **390** | **75** | **40,006** | **98.8%** |

**Outcome Distribution:**
- SUCCEEDED: 98.8%
- FAILED: 1.0%
- NOT_ATTEMPTED: 0.2%

### 6.2 Primitive Emissions by Outcome (Per Seed)

| Seed | MAX_RENT (SUCC) | INVALID_COMMIT (FAIL) | MIN_EFFORT (NOT_AT) | WRONG |
|------|-----------------|------------------------|---------------------|-------|
| 42 | 3,957 | 39 | 7 | 0 |
| 137 | 3,951 | 39 | 7 | 0 |
| 256 | 3,957 | 39 | 6 | 0 |
| 512 | 3,955 | 39 | 6 | 0 |
| 1024 | 3,957 | 39 | 7 | 0 |
| 2048 | 3,949 | 39 | 9 | 0 |
| 4096 | 3,951 | 39 | 9 | 0 |
| 8192 | 3,956 | 39 | 9 | 0 |
| 16384 | 3,955 | 39 | 8 | 0 |
| 32768 | 3,953 | 39 | 7 | 0 |
| **TOTAL** | **39,541** | **390** | **75** | **0** |

### 6.3 Conditional Probabilities

| Condition | Numerator | Denominator | Probability |
|-----------|-----------|-------------|-------------|
| P(MAX_RENT \| SUCCEEDED) | 39,541 | 39,541 | **1.000000** |
| P(INVALID_COMMIT \| FAILED) | 390 | 390 | **1.000000** |
| P(MIN_EFFORT \| NOT_ATTEMPTED) | 75 | 75 | **1.000000** |

**Wrong primitive emissions:** 0

### 6.4 Activation Status

✅ **Model I ACTIVATION VERIFIED**

All conditional probabilities are exactly 1.0.
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

### 7.2 Run 4 — Model I (RENEWAL_FEEDBACK)

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

| Seed | Baseline AA | Run 4 AA | Δ AA | Base Lapses | Run 4 Lapses | Identical? |
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

Telemetry proves that Model I is fully active:
- 39,541 SUCCEEDED epochs → emitted MAX_RENT 39,541 times
- 390 FAILED epochs → emitted INVALID_COMMIT 390 times
- 75 NOT_ATTEMPTED epochs → emitted MIN_EFFORT 75 times
- **All conditional probabilities = 1.0**
- **Zero wrong primitive emissions**

### 9.2 Agent Succeeds Renewals 98.8% of the Time

The most striking observation is that renewals almost always succeed:

| Outcome | Fraction |
|---------|----------|
| SUCCEEDED | 98.8% |
| FAILED | 1.0% |
| NOT_ATTEMPTED | 0.2% |

This reflects the baseline behavior: the incumbent succeeds most renewals,
with failures occurring only at eligibility boundaries or lapse transitions.

### 9.3 Renewal Feedback Has No Effect

Despite conditioning on renewal outcomes and emitting different primitives:

- 9/10 seeds have **identical** AA values to baseline
- All 10 seeds reach HORIZON_EXHAUSTED (no terminal failure)
- Mean AA delta is −0.7 PPM (negligible)

### 9.4 Why Renewal Feedback Exploitation Fails

The adversary cannot leverage renewal feedback because:

1. **SUCCEEDED → MAX_RENT**: After successful renewal, the agent has a full
   new epoch. MAX_RENT consumes budget but doesn't change the renewal dynamics.

2. **FAILED → INVALID_COMMIT**: After failed renewal, succession or lapse
   is already triggered. INVALID_COMMIT cannot prevent the constitutional
   transition that's already in progress.

3. **NOT_ATTEMPTED → MIN_EFFORT**: During lapse or other non-renewal epochs,
   MIN_EFFORT is passive and has no structural impact.

The fundamental issue is that renewal outcomes are **trailing indicators**:
by the time the agent observes them, the kernel has already processed the
constitutional transition. The agent cannot use feedback to *prevent* failures.

### 9.5 No Terminal Failure Modes

The research question asked whether renewal feedback could defeat constitutional
survivability. The answer is **NO**:

- No TERMINAL_COLLAPSE observed
- No STRUCTURAL_THRASHING observed
- No IRREVERSIBLE_RECOVERY_SUPPRESSION observed

All 10 seeds complete the full horizon with HORIZON_EXHAUSTED.

---

## 10. Failure Classification

| Class | Baseline | Run 4 |
|-------|----------|-------|
| HORIZON_EXHAUSTED | 10 | 10 |
| TERMINAL_COLLAPSE | 0 | 0 |
| STRUCTURAL_THRASHING | 0 | 0 |

**No terminal failure modes observed in either condition.**

---

## 11. Defensible Claim

> **Run 4 (Model I: RENEWAL_FEEDBACK) executed to completion on all 10
> seeds with telemetry-verified model activation.**
>
> **Activation Proof:**
> - P(MAX_RENT | SUCCEEDED) = 39,541/39,541 = 1.0
> - P(INVALID_COMMIT | FAILED) = 390/390 = 1.0
> - P(MIN_EFFORT | NOT_ATTEMPTED) = 75/75 = 1.0
> - Wrong primitive emissions: 0
>
> **Outcome Distribution:**
> - SUCCEEDED: 98.8%, FAILED: 1.0%, NOT_ATTEMPTED: 0.2%
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
> Renewal observability does NOT leak enough structure for a minimally
> adaptive adversary to defeat constitutional survivability.

---

## 12. Protocol Notes

### 12.1 Observable Semantics

Per binding decision (2026-01-08):
- Renewal outcome is sampled at the START of epoch t, reflecting epoch t-1
- At t=0, outcome is NOT_ATTEMPTED (no prior epoch)
- Outcome is reset to NOT_ATTEMPTED at each epoch boundary after sampling

### 12.2 Renewal Outcome vs Eligibility

Note that RENEWAL_FAILED and INELIGIBLE (from Run 3) are related but distinct:

- **INELIGIBLE** (Run 3): Policy's fail-streak ≥ K (eligibility bucket)
- **FAILED** (Run 4): Renewal check fired and was denied (renewal event)

A policy can be INELIGIBLE for many epochs after a single FAILED event.
The FAILED outcome occurs at the transition point; INELIGIBLE is the state.

---

## 13. Artifacts

| File | Description |
|------|-------------|
| `run4_renewal_feedback.py` | Run 4 execution script with telemetry |
| `reports/rsa_v200_run4_renewal_feedback_report.md` | This report |

---

## 14. Run 4 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Frozen AKI v0.8 configuration used | ✅ |
| 2 | RSA v2.0 RENEWAL_FEEDBACK model enabled | ✅ |
| 3 | All 10 seeds executed to full horizon | ✅ |
| 4 | Per-seed metrics reported | ✅ |
| 5 | Baseline comparison (side-by-side + delta) | ✅ |
| 6 | Model activation verified via telemetry (P=1.0 checks) | ✅ |
| 7 | Renewal outcome distribution reported | ✅ |
| 8 | Primitive emissions by outcome reported | ✅ |
| 9 | Failure classification reported | ✅ |
| 10 | No terminal failure modes observed | ✅ |
| 11 | Degradation assessment: negligible | ✅ |
| 12 | Renewal observable source of truth documented | ✅ |

---

**RUN 4 COMPLETE. MODEL I ACTIVE. NO SURVIVABILITY DEGRADATION.**

**Renewal feedback does NOT defeat constitutional survivability.**
