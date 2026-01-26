# ASI-2 v0.1 Implementation Report

**Experiment ID:** PHASE-VII-ASI2-MID-TRANSFER-REVOCATION-1
**Version:** 0.1
**Execution Date:** 2026-01-26
**Status:** INVALID_RUN / VERIFIER_SPEC_MISMATCH

> **Note:** No drift occurred. All hashes matched frozen manifest. The frozen prereg and frozen verifier were internally inconsistent at freeze time.

---

## 1. Execution Summary

| Metric | Value |
|--------|-------|
| Runs Executed | 6 |
| Runs Passed | 3 (ASI-2A only) |
| Runs Failed | 3 (ASI-2B only) |
| Classification | `INVALID_RUN / VERIFIER_SPEC_MISMATCH` |

---

## 2. Pre-Execution Verification

### 2.1 Hash Integrity Check

| Component | Expected Hash | Actual Hash | Match |
|-----------|---------------|-------------|-------|
| `harness_asi2.py` | `2c7d179c...` | `2c7d179c99fe035f9f10c96067781d6233782ebf95fb872f09f12b6b43f81e04` | ✅ |
| `verifier_asi2.py` | `0d7026c8...` | `0d7026c834c87f0b30866d773c085521aff4bb506abaf7dc05eebc587f906ea2` | ✅ |

Hashes matched frozen manifest. Execution proceeded.

---

## 3. Execution Results

### 3.1 Per-Run Summary

| Run ID | Condition | Final Phase | Final Node | Revoked | Harness Status |
|--------|-----------|-------------|------------|---------|----------------|
| `asi2-asi_2a-seed41` | ASI_2A | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2b-seed41` | ASI_2B | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2a-seed137` | ASI_2A | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2b-seed137` | ASI_2B | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2a-seed1009` | ASI_2A | HOLD | N1 | YES | COMPLETED |
| `asi2-asi_2b-seed1009` | ASI_2B | HOLD | N1 | YES | COMPLETED |

**Observation:** All 6 runs completed successfully. Revocation occurred at step 3. Phase transitioned to HOLD as expected.

---

## 4. Verification Results

### 4.1 ASI-2A Runs (All PASSED)

| Run ID | Checks | Status |
|--------|--------|--------|
| `asi2-asi_2a-seed41` | 13/13 | ✅ PASS |
| `asi2-asi_2a-seed137` | 13/13 | ✅ PASS |
| `asi2-asi_2a-seed1009` | 13/13 | ✅ PASS |

All ASI-2A runs passed all 13 applicable checks.

### 4.2 ASI-2B Runs (All FAILED)

| Run ID | Checks | Status | Failure |
|--------|--------|--------|---------|
| `asi2-asi_2b-seed41` | 13/14 | ❌ FAIL | `SUCCESSOR_INVOKED_2B` |
| `asi2-asi_2b-seed137` | 13/14 | ❌ FAIL | `SUCCESSOR_INVOKED_2B` |
| `asi2-asi_2b-seed1009` | 13/14 | ❌ FAIL | `SUCCESSOR_INVOKED_2B` |

**Failure Pattern:** All ASI-2B runs failed the same check with the same message:

```
SUCCESSOR_INVOKED_2B: Successor invoked at steps {1, 2, 3}, expected (1, 2)
```

---

## 5. Issue Analysis

### 5.1 Discrepancy Identification

**Source of truth (Frozen Preregistration §13.2):**

> | Check | Description | Applies To |
> |-------|-------------|------------|
> | SUCCESSOR_INVOKED_2B | Successor invoked at steps 1,2,3 | ASI_2B only |

**Frozen Preregistration §6.3:**

> At step 3 (revocation step), execution order is:
> 1. Invoke successor (non-authoritative)
> 2. Capture successor outputs
> 3. Atomic revocation: AUTH_IN_FLIGHT → HOLD
> 4. Discard/quarantine all successor outputs
>
> This tests the **hardest boundary case**: successor output generated at the revocation boundary.

**Verifier Implementation (`verifier_asi2.py`, lines 344-346):**

```python
if not result.check(
    "SUCCESSOR_INVOKED_2B",
    invoked_steps == {1, 2},  # Step 3 is HOLD after revocation, so invoked at 1,2 only
    f"Successor invoked at steps {invoked_steps}, expected {1, 2}"
):
```

### 5.2 Root Cause

The verifier implements `expected_steps = {1, 2}` but the frozen preregistration explicitly specifies `steps 1,2,3`.

The comment in the verifier ("Step 3 is HOLD after revocation, so invoked at 1,2 only") reflects a misunderstanding of the execution order: §6.3 explicitly states successor invocation occurs **before** revocation at step 3.

**Harness behavior is correct:** Successor invoked at steps {1, 2, 3} per §6.3.

**Verifier behavior is incorrect:** Check expects {1, 2} instead of {1, 2, 3}.

### 5.3 Classification

```
INVALID_RUN / VERIFIER_SPEC_MISMATCH
```

**Rationale:** The frozen verifier does not faithfully implement the frozen preregistration. Both artifacts were frozen and executed as frozen (hashes matched). This is not "drift" (no post-freeze modification occurred); it is a **frozen-spec inconsistency** where the prereg and verifier disagreed at freeze time.

**Process finding:** The v0.1 prereg artifact set contained an internal inconsistency: the verifier's SUCCESSOR_INVOKED_2B expectation contradicted the preregistered condition definition in §6.3 and §13.2.

---

## 6. Behavioral Assessment (Despite VERIFIER_SPEC_MISMATCH)

Setting aside the verifier bug, the harness execution demonstrates:

| Criterion | Observed | Expected | Status |
|-----------|----------|----------|--------|
| Authorization initiated | Step 1 | Step 1 | ✅ |
| Successor instantiated | Step 1 | Step 1 | ✅ |
| Revocation at t_revoke | Step 3 | Step 3 | ✅ |
| Phase after revocation | HOLD | HOLD | ✅ |
| authority_actor during flight | PREDECESSOR | PREDECESSOR | ✅ |
| authority_actor during HOLD | NONE | NONE | ✅ |
| Successor invocation (2B) | Steps 1,2,3 | Steps 1,2,3 | ✅ |
| Successor outputs quarantined | YES | YES | ✅ |
| STAY under HOLD | Steps 3,4,5 | Steps 3,4,5 | ✅ |
| POST_COMMIT reached | NO | NO | ✅ |

**Behavioral conclusion:** The harness executed correctly. ASI-2 semantics appear satisfied. The failure is purely a verifier implementation error.

---

## 7. Affected Artifacts

| Artifact | Hash | Defect |
|----------|------|--------|
| `V210/src/verifier_asi2.py` | `0d7026c8...` | Line 345: `{1, 2}` should be `{1, 2, 3}` |

---

## 8. Required Resolution

### Option A: ASI-2 v0.2 (Recommended)

1. Create V220 directory
2. Copy preregistration (no changes needed—it is correct)
3. Copy harness (no changes needed—it is correct)
4. Fix verifier: change `{1, 2}` to `{1, 2, 3}` on line 345
5. Compute new hashes
6. Update preregistration §16.2 with corrected verifier hash
7. Freeze
8. Re-execute

### Option B: Patch v0.1 (NOT RECOMMENDED)

Post-freeze modification violates Phase VII discipline. Would itself constitute `DESIGN_DRIFT`.

---

## 9. Results Artifacts

| File | Location |
|------|----------|
| Run Results | `results/asi2_v01_results_20260126_105344.json` |
| Verification Report | `results/verification_asi2_v01_results_20260126_105344.json` |

---

## 10. Conclusion

**ASI-2 v0.1 Classification:** `INVALID_RUN / VERIFIER_SPEC_MISMATCH`

**Root Cause:** Verifier `SUCCESSOR_INVOKED_2B` check implements incorrect expected value `{1, 2}` instead of preregistration-specified `{1, 2, 3}`. The frozen prereg and frozen verifier were internally inconsistent.

**What can be claimed from v0.1:** Only an instrumentation/process finding:
> The v0.1 prereg artifact set contained an internal inconsistency: the verifier's SUCCESSOR_INVOKED_2B expectation contradicted the preregistered condition definition.

**What cannot be claimed:** ASI-2 PASS. Under Phase VII discipline, "behaviorally looks right" is not evidence when the normative classifier is frozen and fails.

**Next Step:** Create ASI-2 v0.2 with corrected verifier (pure correction, not experiment change).

---

**Report Generated:** 2026-01-26
**Classification:** INVALID_RUN / VERIFIER_SPEC_MISMATCH (no drift; hashes matched)
