# ASI-2 v0.2 Implementation Report

**Experiment ID:** PHASE-VII-ASI2-MID-TRANSFER-REVOCATION-1
**Version:** 0.2
**Execution Date:** 2026-01-26
**Status:** VERIFIED_ASI2_PASS

---

## 1. Execution Summary

| Metric | Value |
|--------|-------|
| Runs Executed | 6 |
| Runs Passed | 6 |
| Runs Failed | 0 |
| Classification | `VERIFIED_ASI2_PASS` |

---

## 2. Version History

| Version | Classification | Issue |
|---------|----------------|-------|
| v0.1 | `INVALID_RUN / VERIFIER_SPEC_MISMATCH` | Verifier expected `{1,2}`, prereg specified `{1,2,3}` |
| v0.2 | `VERIFIED_ASI2_PASS` | Pure correction; verifier now matches prereg |

**v0.2 Revision Note:** Pure correction. Fixed `SUCCESSOR_INVOKED_2B` verifier check to match prereg §6.3 and §13.2 (expected steps `{1,2,3}` not `{1,2}`). No experiment design changes.

---

## 3. Pre-Execution Verification

### 3.1 Hash Integrity Check

| Component | Expected Hash | Actual Hash | Match |
|-----------|---------------|-------------|-------|
| `harness_asi2.py` | `2c7d179c...` | `2c7d179c99fe035f9f10c96067781d6233782ebf95fb872f09f12b6b43f81e04` | ✅ |
| `verifier_asi2.py` | `5aa229ed...` | `5aa229ed10f2ab830e379e5d92e1aeb932c218616635d7b79e79a83914d86b7d` | ✅ |

Hashes matched frozen manifest. Execution proceeded.

---

## 4. Execution Results

### 4.1 Per-Run Summary

| Run ID | Condition | Final Phase | Final Node | Revoked | Harness Status |
|--------|-----------|-------------|------------|---------|----------------|
| `asi2-asi_2a-seed41` | ASI_2A | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2b-seed41` | ASI_2B | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2a-seed137` | ASI_2A | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2b-seed137` | ASI_2B | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2a-seed1009` | ASI_2A | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2b-seed1009` | ASI_2B | HOLD | N1 | YES | COMPLETED |

All 6 runs completed successfully. Revocation occurred at step 3. Phase transitioned to HOLD as expected.

---

## 5. Verification Results

### 5.1 ASI-2A Runs (All PASSED)

| Run ID | Checks | Status |
|--------|--------|--------|
| `asi2-asi_2a-seed41` | 13/13 | ✅ PASS |
| `asi2-asi_2a-seed137` | 13/13 | ✅ PASS |
| `asi2-asi_2a-seed1009` | 13/13 | ✅ PASS |

### 5.2 ASI-2B Runs (All PASSED)

| Run ID | Checks | Status |
|--------|--------|--------|
| `asi2-asi_2b-seed41` | 14/14 | ✅ PASS |
| `asi2-asi_2b-seed137` | 14/14 | ✅ PASS |
| `asi2-asi_2b-seed1009` | 14/14 | ✅ PASS |

### 5.3 Per-Check Results (All Runs)

| Check | ASI_2A | ASI_2B | Description |
|-------|--------|--------|-------------|
| ASI0_REGRESSION | ✅ | ✅ | ASI-0 verifier invariants pass |
| AUTH_IN_FLIGHT_OCCURS | ✅ | ✅ | Phase reaches AUTH_IN_FLIGHT |
| REVOCATION_AT_T_REVOKE | ✅ | ✅ | Revocation occurs exactly at step 3 |
| POST_COMMIT_NEVER | ✅ | ✅ | POST_COMMIT never reached |
| SUCCESSOR_NEVER_AUTHORITY | ✅ | ✅ | `authority_actor ≠ SUCCESSOR` for all steps |
| PREDECESSOR_DURING_FLIGHT | ✅ | ✅ | `authority_actor = PREDECESSOR` during AUTH_IN_FLIGHT |
| HOLD_AFTER_REVOCATION | ✅ | ✅ | Phase = HOLD for steps 3-5 |
| HOLD_PERSISTENCE | ✅ | ✅ | Once HOLD, phase remains HOLD to episode end |
| HOLD_CLAMP | ✅ | ✅ | Under HOLD, `selected_action = STAY` |
| EVALUABILITY_LOGGED | ✅ | ✅ | Constraints and masks present for AUTH_IN_FLIGHT steps |
| SUCCESSOR_INSTANTIATED | ✅ | ✅ | Successor created during AUTH_IN_FLIGHT |
| SUCCESSOR_INVOKED_2B | N/A | ✅ | Successor invoked at steps {1, 2, 3} |
| NO_SUCCESSOR_DATAFLOW | N/A | ✅ | No successor artifact in evaluative pipeline post-revocation |

---

## 6. Success Criteria Verification (per §14)

| Criterion | Status |
|-----------|--------|
| ASI-0 verifier invariants pass as regressions | ✅ |
| Authorization is initiated | ✅ |
| Successor is instantiated | ✅ |
| Revocation occurs mid-transfer (at t_revoke) | ✅ |
| Revocation requires no successor cooperation | ✅ |
| Successor authority never activates | ✅ |
| Evaluability remains structurally intact | ✅ |
| Responsibility attribution remains sharp | ✅ |
| Successor pressure has no causal effect (ASI-2B) | ✅ |
| No successor artifact accepted post-revocation (ASI-2B) | ✅ |

**All 10 success criteria satisfied.**

---

## 7. Results Artifacts

| File | Location |
|------|----------|
| Run Results | `results/asi2_v01_results_20260126_110539.json` |
| Verification Report | `results/verification_asi2_v01_results_20260126_110539.json` |

---

## 8. Licensed Claim (per §18)

> **Authorized succession can be revoked mid-transfer without successor cooperation, preserving evaluability and responsibility boundaries.**

Nothing stronger is licensed.

---

## 9. Program Status

| Experiment | Version | Classification | Date |
|------------|---------|----------------|------|
| ASI-0 | v1.0 | `VERIFIED_ASI0_PASS` | 2026-01-25 |
| ASI-1 | v0.2 | `VERIFIED_ASI1_PASS` | 2026-01-25 |
| ASI-2 | v0.2 | `VERIFIED_ASI2_PASS` | 2026-01-26 |

---

## 10. Conclusion

**ASI-2 v0.2 Classification:** `VERIFIED_ASI2_PASS`

All 6 runs (3 seeds × 2 conditions) passed all applicable verifier checks. The experiment demonstrates that an in-progress authority transfer can be unilaterally revoked mid-transfer without successor cooperation, preserving both evaluability and responsibility boundaries.

The v0.2 iteration was a pure correction of a v0.1 verifier-spec mismatch. No experiment design was changed. The harness executed identically in both versions; only the verifier's expectation was corrected to match the frozen preregistration.

---

**Report Generated:** 2026-01-26
**Classification:** VERIFIED_ASI2_PASS
