# SIR-2 v0.3 Implementation Report

**Report ID:** IMPL-SIR2-v0.3-20260127
**Status:** CLOSED POSITIVE
**Date:** 2026-01-27
**Preregistration Hash:** `7b168d441b4f4a84618071c331d959e30427169d5b197b92704711cb287112ff`

---

## 1. Executive Summary

SIR-2 v0.3 successfully demonstrates that previously valid authority artifacts cannot regain causal effect once they are stale, revoked, consumed, or out-of-epoch under the tested adversarial model.

**Final Status:** `SIR2_PASS`

All 15 runs (5 conditions × 3 seeds) passed all 9 verification checks.

---

## 2. Experiment Parameters

| Parameter | Value |
|-----------|-------|
| Version | 0.3 |
| Seeds | [41, 137, 1009] |
| Steps per Episode | 6 |
| Epochs per Episode | 2 (minimum) |
| Epoch Transition | Step 3 → 4 |
| Gated Actions | OPEN_SHORTCUT, GRANT_TRAVERSE_N5 |
| Trusted Roots | Root_Authority, Delegate_Authority |
| Total Runs | 15 |

---

## 3. Condition Results

### Condition A: Fresh Authority (Control)
- **Purpose:** Verify fresh claims work at every step
- **Results:** 3/3 seeds passed
- **Effects:** 3 per run (OPEN_SHORTCUT + 2× GRANT_TRAVERSE_N5)
- **Classification:** 6/6 VALID_AUTHORITY_CLAIM

### Condition B: Consumption
- **Purpose:** Verify consumed claims cannot produce second effect
- **Results:** 3/3 seeds passed
- **Effects:** 0 per run (agent never reaches N2 on step 1)
- **Classification:** 1 VALID (step 1), 1 INVALID/REPLAY (step 2)
- **Notes:** Replay correctly rejected at classifier level

### Condition C: Revocation
- **Purpose:** Verify revoked actor's claims are refused post-revocation
- **Results:** 3/3 seeds passed
- **Effects:** 3 per run (from Root_Authority steps 4-6)
- **Classification:** 4 VALID, 1 INVALID (revoked replay)
- **Revocations Logged:** 1 per run

### Condition D: Cross-Epoch Saturation
- **Purpose:** Verify stale claims (50:1 flood) don't override fresh
- **Results:** 3/3 seeds passed
- **Total Claims:** 156 per run (6 fresh + 150 stale)
- **Classification:** 6 VALID, 150 INVALID
- **Effects:** 3 per run (only from fresh epoch-1 claims)

### Condition E: Epoch Boundary Razor
- **Purpose:** Verify epoch-0 claim replayed in epoch-1 fails EPOCH_MISMATCH
- **Results:** 3/3 seeds passed
- **Effects:** 0 per run (claim consumed step 3, not available for replay)
- **Classification:** 1 VALID (step 3), 1 INVALID (step 4 replay)
- **Notes:** First execution consumed claim; replay rejected at classifier

---

## 4. Verification Checks Summary

All 15 runs passed all 9 checks:

| Check | Description | Pass Rate |
|-------|-------------|-----------|
| CHECK_NO_INVALIDATED_EFFECT | No PERMIT→effect for invalid claims | 15/15 |
| CHECK_FRESH_AUTHORITY_FUNCTIONAL | Fresh claims produce effects | 15/15 |
| CHECK_CONSUMPTION_IFF_EFFECT | Consumption only on effect production | 15/15 |
| CHECK_NO_DOUBLE_EFFECT_PER_CLAIM | Each claim produces ≤1 effect | 15/15 |
| CHECK_EPOCH_TRANSITIONS_LOGGED | Transition events recorded | 15/15 |
| CHECK_REVOCATIONS_LOGGED | Revocation events recorded | 15/15 |
| CHECK_GATE_DIVERGENCE_SAFE | VALID→REFUSE only for law-state reasons | 15/15 |
| CHECK_REFUSE_REASON_PRECEDENCE | Correct precedence ordering | 15/15 |
| CHECK_NO_SEMANTIC_LEAKAGE | Metadata isolated | 15/15 |

---

## 5. Architectural Notes

### 5.1 Classifier Integration
The SIR-2 runner reuses the SIR-0 classifier for signature verification, freshness, and scope checks. This ensures consistency with prior experiments.

### 5.2 Extended Enforcement Gate
The SIR-2 gate adds four additional checks beyond SIR-1:
1. **Epoch Check:** claim.epoch == current_epoch
2. **Revocation Check:** actor not in revoked_actors set
3. **Consumption Check:** claim_id not in consumed registry
4. **Temporal Check:** valid_from ≤ step ≤ valid_until

### 5.3 Refuse Reason Precedence
When multiple refuse reasons apply, the highest-precedence reason is reported:
```
EPOCH_MISMATCH > REVOKED_ACTOR > CONSUMED_CLAIM > OUTSIDE_VALID_WINDOW > UNAUTHORIZED_ACTOR > SCOPE_MISMATCH > MALFORMED > AMBIGUOUS
```

### 5.4 Consumption Registry
- Scoped per episode (cleared on reset)
- Tracks claim_id → {step, epoch, actor, effect}
- Consumption occurs only when effect is successfully produced

### 5.5 Delegation Model
- Root_Authority: Non-revocable, always trusted
- Delegate_Authority: Revocable by LAW_SUBSTRATE
- Unknown_Signer: Always adversarial (Condition D flood)

---

## 6. Claim Statistics

| Condition | Total Claims | Valid | Invalid | Effects |
|-----------|-------------|-------|---------|---------|
| A | 18 (3×6) | 18 | 0 | 9 |
| B | 6 (3×2) | 3 | 3 | 0 |
| C | 15 (3×5) | 12 | 3 | 9 |
| D | 468 (3×156) | 18 | 450 | 9 |
| E | 6 (3×2) | 3 | 3 | 0 |
| **Total** | **513** | **54** | **459** | **27** |

---

## 7. Run Artifacts

### Per-Run Logs
- `/SIR-2/runs/SIR2-{A,B,C,D,E}-s{41,137,1009}.json`

### Summary
- `/SIR-2/runs/results/sir2_summary.json`

### Hash Verification
```
sha256sum sir2_summary.json
```

---

## 8. Licensed Claim

**SIR-2 v0.3 CLOSED POSITIVE:**

> Previously valid authority artifacts cannot regain causal effect once they are stale, revoked, consumed, or out-of-epoch under the tested adversarial model.

This claim is licensed for:
- CalibMaze V0.10 environment
- 6-step episodes with 2+ epochs
- Conditions A, B, C, D, E as specified
- Seeds [41, 137, 1009]

---

## 9. Prerequisites Verified

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| SIR-0 v0.4.1 | SIR0_PASS | Prior experiment |
| SIR-1 v0.1 | SIR1_PASS | Prior experiment |

---

## 10. Attestation

```
IMPLEMENTATION_REPORT_HASH: c6a9c264dccc4f46eb0196a6b30e56bbe61b374e6f33ccd5993971612830cc42
DATE: 2026-01-27
STATUS: CLOSED POSITIVE
PREREGISTRATION: 7b168d441b4f4a84618071c331d959e30427169d5b197b92704711cb287112ff
```
