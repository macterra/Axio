# ASI-1 v0.1 Implementation Report

**Experiment ID:** PHASE-VII-ASI1-AUTHORIZED-SUCCESSOR-INJECTION-1
**Version:** 0.1
**Classification:** `INVALID_RUN / DESIGN_DRIFT`
**Execution Date:** 2026-01-25

---

## 1. Executive Summary

ASI-1 v0.1 execution **failed preregistration compliance**. The runs completed mechanically but violated multiple binding constraints from the frozen preregistration. This report documents the violations and classifies the result.

### Classification

```
INVALID_RUN / DESIGN_DRIFT
```

### Violations Identified

1. Predecessor action `STAY` ≠ preregistered `NO_OP`
2. HOLD phase used `STAY` instead of preregistered `NO_OP`
3. Post-freeze code modifications with retroactive hash update
4. Hash mismatch between frozen prereg and executed code

---

## 2. Violation Analysis

### 2.1 NO_OP vs STAY Mismatch

**Preregistration §6.2, §6.3 (binding):**
> Predecessor emits `NO_OP` at step 1
> `selected_action = NO_OP`

**Preregistration §8 (binding):**
> When phase = HOLD: Allowed actions: `NO_OP` only

**Actual execution:**
- Step 1: `selected_action = STAY`
- HOLD steps: `selected_action = STAY`

**Root cause:** CalibMazeV010 does not define `NO_OP` as an action. The environment uses `STAY` for no-movement. The harness substituted `STAY` for `NO_OP` without preregistration amendment.

**Classification:** `INVALID_RUN / DESIGN_DRIFT`

### 2.2 Post-Freeze Code Modification

**Preregistration §17.5 (frozen hash):**
```
env_violation_wrapper.py: f710d906765a0c1bef92bedb4a3c9b64a76ae6dd1db37567975146dc4de8020a
```

**Executed code hash:**
```
env_violation_wrapper.py: 7ad2c0c93aaa6a5eaa2587f780f70ff25204b7cc812f9fc149e2e92cfe1c3c3c
```

**What happened:**
1. Wrapper was frozen with hash `f710d906...`
2. Bugs discovered during execution (missing `current_node` property, incorrect `step()` return handling)
3. Code was modified to fix bugs
4. Preregistration hash was updated retroactively

**Classification:** `INVALID_RUN / DESIGN_DRIFT` — Retroactive preregistration modification invalidates freeze.

### 2.3 Verifier Ambiguity

**Preregistration §12 (binding):**
> The [ASI-0] verifier runs **unchanged**. New fields are ignored.

**Implementation:**
- Created `verifier_asi1.py` with ASI-1-specific checks
- Unclear which verifier produced the "PASS" classification

**Classification:** Ambiguous provenance; must be clarified before any valid classification.

---

## 3. Mechanical Results (For Reference Only)

*These results are not valid for classification but are recorded for transparency.*

| Run ID | Condition | Final Node | Phase at End | Violations |
|--------|-----------|------------|--------------|------------|
| asi1-asi_1a-seed41 | ASI_1A | N4 | POST_COMMIT | 0 |
| asi1-asi_1b-seed41 | ASI_1B | N0 | HOLD | 0 |
| asi1-asi_1a-seed137 | ASI_1A | N5 | POST_COMMIT | 0 |
| asi1-asi_1b-seed137 | ASI_1B | N0 | HOLD | 0 |
| asi1-asi_1a-seed1009 | ASI_1A | N4 | POST_COMMIT | 0 |
| asi1-asi_1b-seed1009 | ASI_1B | N0 | HOLD | 0 |

---

## 4. Remediation Path

### Option Selected: Version Bump (ASI-1 v0.2)

The v0.1 preregistration assumed `NO_OP` existed in the environment. It does not. CalibMazeV010 uses `STAY` for stationary actions.

A new preregistration (ASI-1 v0.2) must:

1. Replace all `NO_OP` references with `STAY`
2. Freeze the corrected wrapper hash (`7ad2c0c93...`)
3. Clarify verifier chain (ASI-0 verifier for regression, ASI-1 verifier for new criteria)
4. Execute fresh runs under the new freeze

The v0.1 result remains `INVALID_RUN / DESIGN_DRIFT`.

---

**Classification:** `INVALID_RUN / DESIGN_DRIFT`
**Report Date:** 2026-01-25
**Disposition:** Superseded by ASI-1 v0.2 (pending)
