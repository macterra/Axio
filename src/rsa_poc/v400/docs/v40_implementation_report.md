# RSA-PoC v4.0.1 — Implementation Report

**Version:** 4.0.1
**Date:** 2026-01-17
**Status:** `VALID_RUN / BASELINE_FAILED`

---

## 1. Executive Summary

v4.0.1 is a **valid implementation** of the frozen v4.0 spec. The protocol was followed correctly. However, the baseline failed under frozen semantics.

### Key Finding

**Frozen §2.5.1 causes pervasive HALT** because:
1. OBLIGATION rules bind regardless of current feasibility
2. Multi-step tasks (collect → deposit) cannot proceed under obligation
3. The agent is obligated to DEPOSIT but lacks inventory → HALT

### Results

| Run | Mean Success | Mean Halt | Status |
|-----|--------------|-----------|--------|
| Calibration (Oracle) | 0% | 100% | FAILED |
| Baseline | 0% | 100% | FAILED |
| A (Semantic) | 0% | 100% | N/A (baseline failed) |
| B (Reflection) | 0% | 100% | N/A (baseline failed) |
| C (Persistence) | 0% | 100% | N/A (baseline failed) |
| D (Trace) | 0% | 100% | N/A (baseline failed) |

**Classification:** `BASELINE_FAILED` — cannot proceed to ablation analysis.

---

## 2. What v4.0.1 Fixed

v4.0.1 addressed all three violations from v4.0:

| Violation | v4.0 | v4.0.1 |
|-----------|------|--------|
| Obligation Gate semantics | Loosened (work-towards) | Restored to frozen (strict) |
| Oracle used as agent | Yes | No — Oracle only in calibration |
| Trace excision bypassed | Yes | No — harness checks `is_trace_excised` |

v4.0.1 also added:
- **FormalDeliberator**: Non-oracle deliberator for baseline/ablations
- **Pipeline Integrity Test**: Verifies HALT on SCHEMA_ERROR

---

## 3. Why Frozen Semantics Cause HALT

### 3.1 The Obligation Gate (§2.5.1)

Frozen semantics:
> "If obligation binds and obligated action is NOT compiled/permitted → feasible=[] → HALT"

### 3.2 The Problem

At step 0:
1. Agent is at position (4,2), inventory=0
2. R1 (OBLIGATION) is active: "DEPOSIT at Zone A when zone_a_demand > 0 and not satisfied"
3. Zone A is unsatisfied → R1's condition is TRUE → obligation binds
4. Obligated action is A5 (DEPOSIT)
5. But DEPOSIT requires inventory ≥ 1 to be permitted
6. Agent has inventory=0 → DEPOSIT not permitted
7. Obligation Gate: "A5 not compiled/permitted" → HALT

### 3.3 Why This Is Intentional

The frozen semantics enforce:
> An agent under obligation cannot pursue other goals until the obligation is fulfilled.

But for multi-step tasks (collect → deposit), this creates a deadlock:
- You're obligated to deposit
- You can't deposit without collecting first
- You can't collect because you're under obligation to deposit
- → HALT

### 3.4 This Is Real Data

The frozen spec reveals a **design incompatibility** between:
- Strict obligation enforcement
- Multi-step task environments

Either the spec or the environment must change. v4.0.1 correctly identifies this without changing either.

---

## 4. Implementation Artifacts

### 4.1 Files Modified

```
v400/
├── core/
│   ├── __init__.py      # Version bump to 4.0.1
│   ├── compiler.py      # Reverted obligation gate
│   ├── deliberator.py   # NEW: FormalDeliberator
│   ├── harness.py       # Trace excision check
│   └── ablations.py     # Uses FormalDeliberator
├── experiment.py        # Uses FormalDeliberator
└── tests/
    └── pipeline_integrity_test.py  # NEW
```

### 4.2 Pipeline Integrity

```
PIPELINE INTEGRITY: ✓ VERIFIED
- Step  0: HALT on SCHEMA_ERROR ✓
- Step  5: HALT on SCHEMA_ERROR ✓
- Step 10: HALT on SCHEMA_ERROR ✓
- Step 20: HALT on SCHEMA_ERROR ✓
```

---

## 5. Path Forward

### Option A: v4.1 with Revised Obligation Semantics

**Change §2.5.1 to:**
> "OBLIGATION only forces exclusive action when that action is currently feasible (in permitted set). Otherwise, other permitted actions are allowed to work towards fulfilling the obligation."

**Justification:**
The frozen semantics are incompatible with multi-step task environments. The revised semantics preserve obligation priority while allowing progress towards fulfillment.

### Option B: v4.1 with Revised Environment

**Change ruleset to:**
- Remove initial obligations
- Start with only permissions
- Agent must discover/adopt obligations through experience

**Justification:**
This tests whether the agent can derive obligations from experience, not just follow imposed ones.

### Option C: Accept Baseline Failure

**No changes.** Document that v4.0 as specified is unsolvable for this environment. This is itself a research finding about the limits of strict normative control.

---

## 6. Conclusion

**v4.0.1 Status:** `VALID_RUN / BASELINE_FAILED`

This is not a failed implementation — it's a successful test that reveals:

1. The frozen spec (§2.5.1) is too strict for multi-step task environments
2. The Oracle cannot solve the environment under strict obligation semantics
3. Ablation results are meaningless when baseline fails

**Recommendation:** Proceed to v4.1 with explicit justification for revised obligation semantics (Option A).

---

**End of v4.0.1 Implementation Report**
