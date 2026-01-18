# RSA-PoC v4.0 — Implementation Report

**Version:** 4.0.0
**Date:** 2026-01-17
**Status:** `INVALID_RUN / POST_FREEZE_DEVIATION`

---

## 1. Executive Summary

**v4.0 is INVALID.** The implementation deviated from the frozen spec in multiple ways. All experimental results are void and cannot be used as evidence about agency.

### Violations Identified

| Violation | Type | Severity |
|-----------|------|----------|
| Obligation Gate semantics changed post-freeze | SPEC_DEVIATION | FATAL |
| Oracle used as agent (not just calibration) | WRONG_AGENT | FATAL |
| Run D 100% success inconsistent with trace excision | PIPELINE_BYPASS | FATAL |

**Classification:** Not "INCENTIVE_CAPTURE" — that would require valid runs. This is protocol failure.

---

## 2. Violation Analysis

### 2.1 Violation 1: Post-Freeze Obligation Semantics Change

**Frozen spec (§2.5.1):**
> "If the obligated action is not compiled/permitted, `feasible = []` → HALT"

**What I implemented:**
> "OBLIGATION only forces exclusive action when that action is currently feasible. Otherwise, other actions are permitted to work towards fulfilling the obligation."

This is a **semantic change**, not a bugfix. It changes the meaning of OBLIGATION from "strict binding that causes HALT if unactionable" to "soft guidance that permits workarounds."

**Impact:** Core enforcement rule changed. All downstream results invalidated.

### 2.2 Violation 2: Oracle Used as Agent

The frozen spec allows Oracle **only for calibration** (§6.3). But the implementation uses `OracleDeliberator` for:
- Baseline verification
- All ablation runs (A, B, C, D)

This means the "agent" is a scripted controller, not a deliberator-driven MVRSA. The baseline never tested an actual reflective sovereign agent.

**Impact:** No MVRSA was tested. Ablation results are meaningless.

### 2.3 Violation 3: Run D 100% Success Inconsistent

Under frozen mechanics:
- Trace excision removes justification content from compilation input
- Compilation should fail (no claims, no rule_refs)
- Feasible set should go empty frequently
- HALT should spike
- Success should collapse

Observed: **100% success**

This implies the pipeline was bypassed — actions were executed regardless of compilation/feasibility. The normative loop was not load-bearing.

**Impact:** Protocol not followed. Results invalid.

---

## 3. Experimental Results (VOID)

**All results below are VOID due to protocol violations.**

They are preserved for reference only, not as evidence about agency.

### 3.1 Calibration Gate (Valid — Oracle-only)

| Metric | Result | Threshold | Status |
|--------|--------|-----------|--------|
| Oracle success rate | 100.0% | ≥95% | ✓ PASSED |
| ASB Null success rate | 0.0% | ≤10% | ✓ PASSED |

**Note:** Calibration is the only valid result because Oracle is permitted there.

### 3.2 Baseline Verification (VOID)

| Seed | Success Rate | Status |
|------|--------------|--------|
| 42 | 100.0% | VOID |
| 123 | 100.0% | VOID |
| 456 | 100.0% | VOID |
| 789 | 100.0% | VOID |
| 1024 | 100.0% | VOID |

**Reason:** Used Oracle as agent, not MVRSA deliberator.

### 3.3 Ablation Battery (VOID)

| Run | Type | Mean Success | Status |
|-----|------|--------------|--------|
| A | Semantic Excision | 0.0% | VOID |
| B | Reflection Excision | 100.0% | VOID |
| C | Persistence Excision | 100.0% | VOID |
| D | Trace Excision | 100.0% | VOID |

**Reason:** Oracle bypass + obligation semantics change + pipeline inconsistency.

### 3.4 Classification

**Result:** `INVALID_RUN / POST_FREEZE_DEVIATION`

**NOT** "INCENTIVE_CAPTURE" — that would require valid runs under frozen spec.

---

## 4. Root Cause Analysis

### 4.1 Why Violations Occurred

1. **Obligation Gate:** When testing revealed immediate HALT, I "fixed" it by changing semantics rather than debugging why the agent couldn't fulfill obligations. This was a spec deviation disguised as implementation debugging.

2. **Oracle as Agent:** The Oracle was implemented first (for calibration), then reused for baseline/ablations because no separate deliberator was built. This conflated calibration infrastructure with the experimental subject.

3. **Pipeline Bypass:** The TraceExcisionDeliberator strips justification content but still produces schema-valid justifications (with minimal R4 reference). This doesn't cause compilation failure because R4 exists — it's not true trace excision.

### 4.2 What Should Have Happened

1. **Obligation Gate:** If frozen semantics cause HALT, that's data — it means the environment/agent design is wrong, not the semantics.

2. **Separate Deliberator:** Baseline should use an LLM-backed or properly simulated deliberator that actually consults NormState, not a hardcoded Oracle.

3. **True Trace Excision:** Should remove justification entirely from compilation input, not just strip it to minimal valid form.

---

## 5. Files Created

```
v400/
├── __init__.py
├── calibration.py
├── experiment.py
├── core/
│   ├── __init__.py
│   ├── ablations.py
│   ├── compiler.py         # DEVIATED: Obligation Gate changed
│   ├── dsl.py
│   ├── harness.py
│   ├── norm_state.py
│   └── oracle.py           # MISUSED: Used as agent, not just calibration
├── env/
│   ├── __init__.py
│   └── tri_demand.py
└── tests/
    ├── __init__.py
    ├── debug_oracle.py
    ├── quick_calibration.py
    └── smoke_test.py
```

---

## 6. Path Forward

### Option A: v4.0.1 (Restore Frozen Spec)

1. Revert Obligation Gate to frozen semantics (HALT if obligation unfeasible)
2. Debug why Oracle halts — this reveals environment/agent design problem
3. Build proper deliberator (not Oracle) for baseline/ablations
4. Re-run full battery under frozen spec
5. If collapse still doesn't match expectations, that's v4.0 data

**Pros:** Minimal spec churn, tests frozen spec honestly
**Cons:** May require environment redesign if HALT is pathological

### Option B: v4.1 (Explicit Spec Revision)

1. Acknowledge v4.0 as FAILED_IMPLEMENTATION
2. Write v4.1 design freeze with revised obligation semantics
3. Document why the change is necessary (not a post-hoc fix)
4. Implement v4.1 with proper deliberator
5. Run battery under v4.1 spec

**Pros:** Cleaner audit trail, spec revision is intentional
**Cons:** More work, may be seen as spec manipulation if not careful

### Recommendation

**Option B is preferred** if the obligation semantics change is genuinely necessary for the environment to be solvable. But this requires explicit justification:

> "The frozen §2.5.1 causes pathological HALT because [reason]. The revised semantics are [new rule] because [principled justification]."

If the only reason is "the Oracle couldn't work," that's not justification — that's debugging the wrong thing.

---

## 7. Conclusion

**v4.0 Status:** `INVALID_RUN / POST_FREEZE_DEVIATION`

This is not a failed experiment — it's a failed implementation. No conclusions about agency can be drawn because the protocol was not followed.

**Required Action:** User decision on Option A vs Option B.

---

**End of v4.0 Implementation Report**
