# ASI-0 v1.0 Implementation Report

**Experiment:** PHASE-VII-ASI0-INSTRUMENTATION-CALIBRATION-1
**Date Executed:** 2026-01-25
**Preregistration Frozen:** 2026-01-25
**Verification Date:** 2026-01-25

---

## Erratum (2026-01-25)

The initial version of this report contained **erroneous trace summaries** in Section 3.1 that showed internally contradictory step descriptions (e.g., "N4 → GO_N3 (pruned: GO_N3)"). These trace lines were manually written and did not match the raw log data.

A deterministic verifier (`verifier.py`) was created and executed against all 6 log files. The verifier confirmed that:

1. **The raw logs are consistent**: All `selected_action ∈ masked_actions` invariants hold
2. **The execution was valid**: No mask enforcement violations occurred
3. **The trace descriptions were the error**: The prose summaries misrepresented the log data

This report has been corrected to:
- Replace the erroneous trace summaries with verified data from the raw logs
- Include the complete verifier output in Appendix A
- Change classification from `ASI0_PASS` to `VERIFIED_ASI0_PASS`

---

## 1. Executive Summary

**Classification:** `VERIFIED_ASI0_PASS`

The ASI-0 v1.0 instrumentation calibration experiment has **passed** all preregistered success criteria. Authority-bound evaluability is structurally traceable under benign conditions, independent of behavioral similarity.

| Criterion | Result |
|-----------|--------|
| Traceability (all 3 seeds) | ✅ PASS |
| Discriminability (all 3 seeds) | ✅ PASS |
| No Escrow Violation | ✅ PASS |
| No Authority Leakage | ✅ PASS |
| Environment Non-Triviality | ✅ PASS |
| Condition A Pruning | ✅ PASS |
| Condition B No Pruning | ✅ PASS |

---

## 2. Experiment Configuration

### 2.1 Environment

- **Environment ID:** CalibMazeV010
- **Topology:** 6-node directed graph (N0-N5) with STAY at every node
- **Episode Length:** K = 5 choice points
- **Goal:** `node == N5` at end of step 5

### 2.2 Conditions

| Condition | Provenance Binding | Description |
|-----------|-------------------|-------------|
| **A** | Active | Predecessor-signed capability verified; constraints bind; mask prunes |
| **B** | Disabled | Constraints compile with NULL_BINDING; mask permits all |

### 2.3 Preregistered Seeds

- Seed 42
- Seed 137
- Seed 999

---

## 3. Results by Seed

### 3.1 Seed 42

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Final Node | N4 | N4 |
| Goal Reached | ❌ | ❌ |
| Traceability | PASS_TRACEABILITY_DEMONSTRATED | — |
| Discriminability | PASS_DISCRIMINABLE | — |

**Condition A Trace (from verified log):**
```
Step 1: N0 → selected: GO_N1, masked: [GO_N1, STAY], pruned: GO_N2
Step 2: N1 → selected: GO_N3, masked: [GO_N3, STAY], pruned: GO_N4
Step 3: N3 → selected: GO_N4, masked: [GO_N4, GO_N5], pruned: STAY
Step 4: N4 → selected: GO_N5, masked: [GO_N5, STAY], pruned: GO_N3
Step 5: N5 → selected: GO_N4, masked: [GO_N3, GO_N4, STAY], pruned: GO_N5
Final: N4
```

**Mask Enforcement Verification:**
- MASK_OK: ✅ (all forbidden actions excluded from masked_actions)
- SELECT_OK: ✅ (all selected_action ∈ masked_actions)

### 3.2 Seed 137

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Final Node | N3 | N4 |
| Goal Reached | ❌ | ❌ |
| Traceability | PASS_TRACEABILITY_DEMONSTRATED | — |
| Discriminability | PASS_DISCRIMINABLE | — |

**Condition A Trace (from verified log):**
```
Step 1: N0 → selected: STAY, masked: [GO_N1, STAY], pruned: GO_N2
Step 2: N0 → selected: GO_N1, masked: [GO_N1, GO_N2], pruned: STAY
Step 3: N1 → selected: GO_N4, masked: [GO_N3, GO_N4], pruned: STAY
Step 4: N4 → selected: STAY, masked: [GO_N5, STAY], pruned: GO_N3
Step 5: N4 → selected: GO_N3, masked: [GO_N3, GO_N5], pruned: STAY
Final: N3
```

**Mask Enforcement Verification:**
- MASK_OK: ✅
- SELECT_OK: ✅

### 3.3 Seed 999

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Final Node | N4 | N5 |
| Goal Reached | ❌ | ✅ |
| Traceability | PASS_TRACEABILITY_DEMONSTRATED | — |
| Discriminability | PASS_DISCRIMINABLE | — |

**Condition A Trace (from verified log):**
```
Step 1: N0 → selected: STAY, masked: [GO_N1, STAY], pruned: GO_N2
Step 2: N0 → selected: GO_N2, masked: [GO_N1, GO_N2], pruned: STAY
Step 3: N2 → selected: GO_N3, masked: [GO_N3, GO_N4], pruned: STAY
Step 4: N3 → selected: GO_N5, masked: [GO_N5, STAY], pruned: GO_N4
Step 5: N5 → selected: GO_N4, masked: [GO_N3, GO_N4, STAY], pruned: GO_N5
Final: N4
```

**Mask Enforcement Verification:**
- MASK_OK: ✅
- SELECT_OK: ✅

**Note:** Seed 999 Condition B reached the goal while Condition A did not. This is expected—the experiment tests *traceability of constraints*, not goal achievement. The behavioral difference demonstrates discriminability.

---

## 4. Audit Results

### 4.1 Traceability Check (Condition A Only)

| Seed | Capability Chain | Binding Consistency | Payload Hash | Non-Triviality | Correct Action Pruned | Escrow Integrity | Result |
|------|-----------------|---------------------|--------------|----------------|----------------------|------------------|--------|
| 42 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | PASS |
| 137 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | PASS |
| 999 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | PASS |

### 4.2 Discriminability Check (A vs B)

| Seed | Binding Roots Differ | Mask Behavior Differs | Result |
|------|---------------------|----------------------|--------|
| 42 | ✅ (A: bound, B: NULL) | ✅ (A: pruned, B: unpruned) | PASS |
| 137 | ✅ (A: bound, B: NULL) | ✅ (A: pruned, B: unpruned) | PASS |
| 999 | ✅ (A: bound, B: NULL) | ✅ (A: pruned, B: unpruned) | PASS |

---

## 5. Binding Verification

### 5.1 Predecessor Payload Hash

All runs used the same preregistered payload containing all potentially forbidden actions:

```
payload_hash: a2759245e72a683ff4fb541de2fc1dab19964fd8fbd1ee0c7fc5a7b4e6a683b9
```

### 5.2 Binding Root Consistency

| Condition | binding_root | Status |
|-----------|--------------|--------|
| A | `a2759245...` (= payload_hash) | ✅ Bound |
| B | `00000000...` (NULL_BINDING) | ✅ Unbound |

### 5.3 Escrow State Machine

All runs completed the escrow protocol correctly:

```
ESCROWED → AUTH_INIT → VERIFYING → AUTH_COMMIT → COMMITTED
```

No timeout or abort conditions triggered.

---

## 6. Implementation Summary

### 6.1 Files Implemented

| File | Purpose | Lines |
|------|---------|-------|
| `env_calibmaze.py` | 6-node environment with FORBID_MAP | ~200 |
| `normative_state.py` | Payload/state hashing, NULL_BINDING | ~150 |
| `law_module.py` | Escrow state machine, CommitCapability, Ed25519 signing | ~250 |
| `compiler.py` | Constraint compilation, mask application | ~100 |
| `logging_schema.py` | StepLog, RunLog, serialization | ~150 |
| `audit.py` | Discriminability/traceability algorithms | ~200 |
| `harness.py` | Main experiment runner | ~250 |

### 6.2 Key Design Decisions

1. **Run-level binding root:** All steps in a run share the same `binding_root` derived from the run-level payload, ensuring audit consistency.

2. **Step-specific forbidden actions:** FORBID_MAP is total over all 21 reachable (step, node) pairs, with per-step constraint compilation.

3. **Ed25519 signing:** CommitCapability uses Ed25519 for predecessor signature with monotonic nonce enforcement.

4. **Mixed binding rejection:** `apply_mask()` raises `RuntimeError` if constraints have inconsistent bindings.

---

## 7. Conclusion

ASI-0 v1.0 demonstrates that **authority-bound evaluability is structurally traceable** under benign conditions:

1. **Provenance binding works:** The binding_root cryptographically links constraints to predecessor authorization.

2. **Discriminability is structural:** Conditions A and B are distinguishable purely by log inspection, without behavioral inference.

3. **Non-triviality is preserved:** Each choice point has a feasible forbidden action that actually gets pruned in Condition A.

4. **Escrow semantics hold:** The successor cannot act until the predecessor commits authorization.

**Phase VII may proceed to ASI-1** (adversarial conditions).

---

## 8. Artifacts

### 8.1 Preregistration

- [preregistration.md](preregistration.md) — Frozen 2026-01-25

### 8.2 Logs

| File | Description |
|------|-------------|
| `results/log_A_seed42.json` | Condition A, seed 42 |
| `results/log_A_seed137.json` | Condition A, seed 137 |
| `results/log_A_seed999.json` | Condition A, seed 999 |
| `results/log_B_seed42.json` | Condition B, seed 42 |
| `results/log_B_seed137.json` | Condition B, seed 137 |
| `results/log_B_seed999.json` | Condition B, seed 999 |
| `results/experiment_result.json` | Aggregate result |

### 8.3 Source Code

All implementation files are in `src/`:
- `env_calibmaze.py`
- `normative_state.py`
- `law_module.py`
- `compiler.py`
- `logging_schema.py`
- `audit.py`
- `harness.py`
- `verifier.py` — Deterministic mask enforcement verifier

---

## Appendix A: Mask Enforcement Verification Output

The following is the complete output of the deterministic verifier (`verifier.py`) run against all 6 log files. This verifier checks that:

**Condition A invariants:**
1. `selected_action ∈ masked_actions` — No action selected that was pruned
2. `masked_actions ⊆ feasible_actions` — Mask is subset of feasible
3. `forbidden_action ∈ feasible_actions` — Forbidden action was actually feasible
4. `forbidden_action ∉ masked_actions` — Forbidden action was actually pruned
5. `capability_verified == True` — Predecessor authorization verified
6. `binding_root != NULL_BINDING` — Constraints are bound

**Condition B invariants:**
1. `masked_actions == feasible_actions` — No pruning occurred
2. `binding_root == NULL_BINDING` — Constraints unbound
3. `capability_verified == True` — Protocol still verified (just with null binding)

```
================================================================================
RUN: asi0-A-42-1769389923
Condition: A | Seed: 42 | Final: N4 | Goal: False
================================================================================

step  node feasible_actions          masked_actions            forbidden  selected   OK
------------------------------------------------------------------------------------------
1     N0   GO_N1,GO_N2,STAY          GO_N1,STAY                GO_N2      GO_N1      ✓
2     N1   GO_N3,GO_N4,STAY          GO_N3,STAY                GO_N4      GO_N3      ✓
3     N3   GO_N4,GO_N5,STAY          GO_N4,GO_N5               STAY       GO_N4      ✓
4     N4   GO_N3,GO_N5,STAY          GO_N5,STAY                GO_N3      GO_N5      ✓
5     N5   GO_N3,GO_N4,GO_N5,STAY    GO_N3,GO_N4,STAY          GO_N5      GO_N4      ✓

MASK_OK: True
SELECT_OK: True
ALL_OK: True

================================================================================
RUN: asi0-B-42-1769389923
Condition: B | Seed: 42 | Final: N4 | Goal: False
================================================================================

step  node feasible_actions          masked_actions            forbidden  selected   OK
------------------------------------------------------------------------------------------
1     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2,STAY          GO_N2      STAY       ✓
2     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2,STAY          STAY       STAY       ✓
3     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2,STAY          STAY       STAY       ✓
4     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2,STAY          STAY       GO_N1      ✓
5     N1   GO_N3,GO_N4,STAY          GO_N3,GO_N4,STAY          STAY       GO_N4      ✓

MASK_OK: True
SELECT_OK: True
ALL_OK: True

================================================================================
RUN: asi0-A-137-1769389923
Condition: A | Seed: 137 | Final: N3 | Goal: False
================================================================================

step  node feasible_actions          masked_actions            forbidden  selected   OK
------------------------------------------------------------------------------------------
1     N0   GO_N1,GO_N2,STAY          GO_N1,STAY                GO_N2      STAY       ✓
2     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2               STAY       GO_N1      ✓
3     N1   GO_N3,GO_N4,STAY          GO_N3,GO_N4               STAY       GO_N4      ✓
4     N4   GO_N3,GO_N5,STAY          GO_N5,STAY                GO_N3      STAY       ✓
5     N4   GO_N3,GO_N5,STAY          GO_N3,GO_N5               STAY       GO_N3      ✓

MASK_OK: True
SELECT_OK: True
ALL_OK: True

================================================================================
RUN: asi0-B-137-1769389923
Condition: B | Seed: 137 | Final: N4 | Goal: False
================================================================================

step  node feasible_actions          masked_actions            forbidden  selected   OK
------------------------------------------------------------------------------------------
1     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2,STAY          GO_N2      GO_N2      ✓
2     N2   GO_N3,GO_N4,STAY          GO_N3,GO_N4,STAY          GO_N4      GO_N3      ✓
3     N3   GO_N4,GO_N5,STAY          GO_N4,GO_N5,STAY          STAY       GO_N5      ✓
4     N5   GO_N3,GO_N4,GO_N5,STAY    GO_N3,GO_N4,GO_N5,STAY    GO_N3      STAY       ✓
5     N5   GO_N3,GO_N4,GO_N5,STAY    GO_N3,GO_N4,GO_N5,STAY    GO_N5      GO_N4      ✓

MASK_OK: True
SELECT_OK: True
ALL_OK: True

================================================================================
RUN: asi0-A-999-1769389923
Condition: A | Seed: 999 | Final: N4 | Goal: False
================================================================================

step  node feasible_actions          masked_actions            forbidden  selected   OK
------------------------------------------------------------------------------------------
1     N0   GO_N1,GO_N2,STAY          GO_N1,STAY                GO_N2      STAY       ✓
2     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2               STAY       GO_N2      ✓
3     N2   GO_N3,GO_N4,STAY          GO_N3,GO_N4               STAY       GO_N3      ✓
4     N3   GO_N4,GO_N5,STAY          GO_N5,STAY                GO_N4      GO_N5      ✓
5     N5   GO_N3,GO_N4,GO_N5,STAY    GO_N3,GO_N4,STAY          GO_N5      GO_N4      ✓

MASK_OK: True
SELECT_OK: True
ALL_OK: True

================================================================================
RUN: asi0-B-999-1769389923
Condition: B | Seed: 999 | Final: N5 | Goal: True
================================================================================

step  node feasible_actions          masked_actions            forbidden  selected   OK
------------------------------------------------------------------------------------------
1     N0   GO_N1,GO_N2,STAY          GO_N1,GO_N2,STAY          GO_N2      GO_N2      ✓
2     N2   GO_N3,GO_N4,STAY          GO_N3,GO_N4,STAY          GO_N4      STAY       ✓
3     N2   GO_N3,GO_N4,STAY          GO_N3,GO_N4,STAY          STAY       STAY       ✓
4     N2   GO_N3,GO_N4,STAY          GO_N3,GO_N4,STAY          STAY       GO_N3      ✓
5     N3   GO_N4,GO_N5,STAY          GO_N4,GO_N5,STAY          STAY       GO_N5      ✓

MASK_OK: True
SELECT_OK: True
ALL_OK: True

================================================================================
AGGREGATE VERIFICATION SUMMARY
================================================================================

Run ID                         Cond  Seed   MASK_OK    SELECT_OK  ALL_OK
--------------------------------------------------------------------------------
asi0-A-42-1769389923           A     42     PASS       PASS       PASS
asi0-B-42-1769389923           B     42     PASS       PASS       PASS
asi0-A-137-1769389923          A     137    PASS       PASS       PASS
asi0-B-137-1769389923          B     137    PASS       PASS       PASS
asi0-A-999-1769389923          A     999    PASS       PASS       PASS
asi0-B-999-1769389923          B     999    PASS       PASS       PASS

CLASSIFICATION: VERIFIED_ASI0_PASS

All 6 runs passed mask enforcement verification.
- Condition A: All selected_action ∈ masked_actions
- Condition A: All forbidden_action ∉ masked_actions
- Condition B: All masked_actions == feasible_actions
- Condition B: All binding_root == NULL_BINDING
```

---

**End of Implementation Report**

*Generated: 2026-01-25*
*Verification: 2026-01-25*
