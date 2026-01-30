# AKR-0 Implementation Report

- **Project:** AKR-0 v0.1 — Authority Kernel Runtime Calibration
- **Phase:** VIII — Governance Stress Architecture (GSA-PoC)
- **Status:** ✅ **AKR0_PASS / AUTHORITY_EXECUTION_ESTABLISHED**
- **Date:** 2026-01-30
- **Implementation:** Opus (Claude)
- **Specification:** Vesper/Morningstar

---

## 1. Executive Summary

The AKR-0 experiment successfully demonstrated that authority-constrained execution is mechanically realizable under AST Spec v0.2 using a deterministic kernel without semantic interpretation, optimization, or fallback behavior.

| Metric | Result |
|--------|--------|
| Total Runs | 15 |
| Passed | 15 |
| Failed | 0 |
| Replay Verified | **15/15** ✓ |
| Classification | `AKR0_PASS / AUTHORITY_EXECUTION_ESTABLISHED` |

---

## 2. Experiment Configuration

### 2.1 Frozen Dependencies

| Dependency | Version | Status |
|------------|---------|--------|
| AST Spec | v0.2 | FROZEN |
| AIE Spec | v0.1 | FROZEN |
| AKR Spec | v0.1 | FROZEN |

### 2.2 Run Parameters

| Parameter | Value |
|-----------|-------|
| Epochs per run | 100 |
| Seeds | {11, 22, 33, 44, 55} |
| Address Book | 16 holders (H0001–H0016) |
| Scope Pool | 4,096 elements (2,048 resources × 2 operations) |
| PRNG | PCG32, stream=0 |

### 2.3 Conditions

| Condition | Description | Injections/Epoch | Actions/Epoch | Transforms/Epoch |
|-----------|-------------|------------------|---------------|------------------|
| A | Valid Authority | 20 | 20 | 0 |
| B | Authority Absence | 0 | 20 | 5 |
| C | Conflict Saturation | 50 | 20 | 10 |

---

## 3. Results by Condition

### 3.1 Condition A — Valid Authority (Positive Control)

| Seed | Epochs | Events | Executed | Refused | Conflicts | Transforms | Time (s) |
|------|--------|--------|----------|---------|-----------|------------|----------|
| 11 | 100 | 4,099 | 15 | 1,985 | 305 | 1,695 | 72.0 |
| 22 | 100 | 4,099 | 20 | 1,980 | 317 | 1,683 | 71.7 |
| 33 | 100 | 4,099 | 24 | 1,976 | 294 | 1,706 | 70.1 |
| 44 | 100 | 4,099 | 21 | 1,979 | 293 | 1,707 | 69.9 |
| 55 | 100 | 4,099 | 19 | 1,981 | 342 | 1,658 | 71.2 |
| **Total** | **500** | **20,495** | **99** | **9,901** | **1,551** | **8,449** | **354.9** |

**Analysis:**
- Actions executed only when authority exists and scope matches
- ~1% execution rate reflects random holder/scope matching probability
- Conflicts arise from natural scope collisions (~4.5% expected)
- All replay verifications passed ✓

### 3.2 Condition B — Authority Absence (Negative Control)

| Seed | Epochs | Events | Executed | Refused | Conflicts | Deadlock | Time (s) |
|------|--------|--------|----------|---------|-----------|----------|----------|
| 11 | 1 | 25 | 0 | 25 | 0 | ENTROPIC_COLLAPSE | 0.007 |
| 22 | 1 | 25 | 0 | 25 | 0 | ENTROPIC_COLLAPSE | 0.009 |
| 33 | 1 | 25 | 0 | 25 | 0 | ENTROPIC_COLLAPSE | 0.007 |
| 44 | 1 | 25 | 0 | 25 | 0 | ENTROPIC_COLLAPSE | 0.007 |
| 55 | 1 | 25 | 0 | 25 | 0 | ENTROPIC_COLLAPSE | 0.009 |
| **Total** | **5** | **125** | **0** | **125** | **0** | **5×EC** | **0.04** |

**Analysis:**
- Immediate ENTROPIC_COLLAPSE detected at epoch 1 (as expected)
- Zero actions executed (no authorities = no execution possible)
- All 25 action requests per run correctly refused
- Identical final state hash across all seeds: `b7f9295ea6a64eb7...`
- All replay verifications passed ✓

### 3.3 Condition C — Conflict Saturation

| Seed | Epochs | Events | Executed | Refused | Conflicts | Transforms | Time (s) |
|------|--------|--------|----------|---------|-----------|------------|----------|
| 11 | 100 | 8,099 | 17 | 2,963 | 1,478 | 3,542 | 459.5 |
| 22 | 100 | 8,099 | 13 | 2,972 | 1,464 | 3,551 | 447.7 |
| 33 | 100 | 8,099 | 18 | 2,963 | 1,467 | 3,552 | 448.5 |
| 44 | 100 | 8,099 | 10 | 2,977 | 1,477 | 3,536 | 446.0 |
| 55 | 100 | 8,099 | 22 | 2,971 | 1,466 | 3,541 | 446.9 |
| **Total** | **500** | **40,495** | **80** | **14,846** | **7,352** | **17,722** | **2,248.6** |

**Analysis:**
- High conflict density achieved (~30 conflicts per epoch via k=15 hot scopes)
- Very low execution rate (~0.5%) due to conflict blocking
- Transformations processed but most refused (no governance authority)
- No deadlock despite saturation (transformations maintain activity)
- All replay verifications passed ✓

---

## 4. Aggregate Statistics

### 4.1 Total Events Processed

| Condition | Events | Actions Executed | Actions Refused | Conflicts | Transformations |
|-----------|--------|------------------|-----------------|-----------|-----------------|
| A | 20,495 | 99 | 9,901 | 1,551 | 8,449 |
| B | 125 | 0 | 125 | 0 | 0 |
| C | 40,495 | 80 | 14,846 | 7,352 | 17,722 |
| **Total** | **61,115** | **179** | **24,872** | **8,903** | **26,171** |

### 4.2 Execution Rates

| Condition | Execution Rate | Refusal Rate |
|-----------|----------------|--------------|
| A | 0.99% | 99.01% |
| B | 0.00% | 100.00% |
| C | 0.54% | 99.46% |

### 4.3 Runtime Performance

| Condition | Total Time | Avg per Run | Avg per Event |
|-----------|------------|-------------|---------------|
| A | 354.9s | 71.0s | 17.3ms |
| B | 0.04s | 0.008s | 0.3ms |
| C | 2,248.6s | 449.7s | 55.5ms |
| **Total** | **2,603.5s** (~43 min) | — | — |

---

## 5. Success Criteria Verification

Per preregistration §18, AKR-0 passes iff ALL of:

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | No action executes without authority | ✅ PASS | Condition B: 0 executions, 125 refusals |
| 2 | All inadmissible actions are refused | ✅ PASS | 24,872 total refusals, all logged |
| 3 | Conflicts block execution deterministically | ✅ PASS | Condition C: 7,352 conflicts, 80 executions |
| 4 | Deadlocks are detected and classified | ✅ PASS | 5× ENTROPIC_COLLAPSE in Condition B |
| 5 | Replayability is bit-perfect | ✅ PASS | 15/15 replay verifications passed |
| 6 | No semantic or heuristic logic invoked | ✅ PASS | Code inspection confirms deterministic logic |

---

## 6. Final State Hashes

### 6.1 Condition A

| Seed | Final State Hash |
|------|------------------|
| 11 | `cc602fb4cedc2a480b919f022b0fe53e3b0c76e672a03be4eee5439c8306b77f` |
| 22 | `174f32d757e4d264de3d6bb59eb7f4cc037ec024a76a97998df5e1e619754960` |
| 33 | `1beef620183102ef2dcf9818e4ce77f3e5eb4b0a2b874849ca94faa208364b5a` |
| 44 | `94afbf50de57e9610ff9bed55b3e6410464739bfe112d8e1d0589ea812252e68` |
| 55 | `662f379a05e2e373449b02a28083e02a5400befae58865080cd9ce0089cf72bd` |

### 6.2 Condition B

| Seed | Final State Hash |
|------|------------------|
| 11–55 | `b7f9295ea6a64eb78440f4972e2fc2c7625365b4b2f226d6e2bfabb65c72d788` |

*Note: Identical hash across all seeds confirms deterministic empty-state termination.*

### 6.3 Condition C

| Seed | Final State Hash |
|------|------------------|
| 11 | `ea9d40739b9743b3e629ed44bab349bc86aaebd457f15eb1987bfb5ce1af49e8` |
| 22 | `1d60dab23e03d98653597823f1d7d93c1fca537631be66d743654b8c7d095448` |
| 33 | `db5c11b628c94c492f7ce1bd4a0bb247fada3281aff3554cbcd25405c32bd974` |
| 44 | `c1ef2163fe4ded68af306431b408f0d1b9fb9f48a56018be03204f0c35cb0a49` |
| 55 | `d350eaa11b5cb5403dbe74981ab4d363606cf1396146c9a41597dc0e8ac9b315` |

---

## 7. Implementation Files

| File | Purpose | LOC |
|------|---------|-----|
| `structures.py` | Data structures (AuthorityRecord, events, outputs) | ~370 |
| `canonical.py` | AST Appendix C canonicalization, SHA-256, ID generation | ~230 |
| `pcg32.py` | PCG32 PRNG implementation | ~100 |
| `aie.py` | Authority Input Environment, injection logic | ~330 |
| `kernel.py` | AKR-0 kernel core, admissibility, conflict detection | ~710 |
| `harness.py` | Execution harness, traffic generation | ~430 |
| `logger.py` | JSONL logging, hash chain, replay verifier | ~360 |
| `run_akr0.py` | Main experiment runner | ~240 |
| **Total** | | **~2,770** |

---

## 8. Licensed Claim

Per preregistration §20, the following claim is now established:

> **Authority-constrained execution is mechanically realizable under AST Spec v0.2 using a deterministic kernel without semantic interpretation, optimization, or fallback behavior.**

### Scope Qualifiers

This claim is valid only under:
- AIE regime as declared in preregistration
- PCG32 PRNG with seeds {11, 22, 33, 44, 55}
- Scope pool M=4,096, Address Book |H|=16
- No claims about governance success, stability, or desirability

---

## 9. Attestation

```
Experiment:     AKR-0 v0.1
Start Time:     2026-01-30T09:34:49.992192
End Time:       2026-01-30T11:13:56.855768
Duration:       1h 39m 7s
Classification: AKR0_PASS / AUTHORITY_EXECUTION_ESTABLISHED

Signed by implementation: Opus (Claude)
```

---

**End of AKR-0 Implementation Report**
