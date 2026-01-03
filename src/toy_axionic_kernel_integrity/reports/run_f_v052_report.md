# Run F: AKI v0.5.2 ALS-E Competence Horizon Results

**Experiment Date:** 2025-01-03
**Specification Version:** 0.5.2
**Horizon:** H = 30,000 cycles
**Parameters:** steps_cap = 100, actions_cap = 100, renewal_check_interval = 100

---

## Executive Summary

| Sub-Run | Status | Verdict |
|---------|--------|---------|
| F0 | ✅ Complete | Mechanism validation success |
| F1 | ⚠️ Valid but non-probative | Stress condition not engaged |
| F2 | ❌ Not executed as designed | Generator short-circuit |

**Run F demonstrates that ALS-E rent mechanics and renewal plumbing remain stable up to E4 for control-optimal successors. No competence ceiling or stasis sub-regime can be inferred from these runs because adversarial and CBD successors were structurally excluded from effective competition.**

---

## Overview

Run F investigates the **competence horizon** question:

> "As lease-granted expressivity increases and rent reduces effective step budget, where does renewal stability collapse?"

Three sub-runs were executed:
- **F0**: E0 baseline calibration (verify rent accounting at minimal tier)
- **F1**: E0→E4 expressivity ascension (find competence ceiling)
- **F2**: CBD stress at fixed E3 (measure hollow succession under attack pressure)

---

## F0: E0 Baseline Calibration

**Status: ✅ FULL SUCCESS**

**Seeds:** 42, 43, 44
**Purpose:** Verify rent accounting at E0 (rent = 1, effective_steps = 99)

| Seed | S* | Successions | Renewals | Bankruptcies | Revocations | Stop Reason |
|------|-----|-------------|----------|--------------|-------------|-------------|
| 42   | 3   | 3           | 298      | 0            | 0           | HORIZON_EXHAUSTED |
| 43   | 3   | 3           | 298      | 0            | 0           | HORIZON_EXHAUSTED |
| 44   | 3   | 3           | 298      | 0            | 0           | HORIZON_EXHAUSTED |

**Rent Telemetry:**
- Rent charged (mean): 1.0 steps/epoch
- Effective steps available (min): 99
- Steps used (mean): 98.67

**Sanity Checks (all passed):**
- ✅ Revocations = 0
- ✅ Bankruptcies = 0
- ✅ Renewal rate ≥ 95%

**Interpretation:** E0 baseline is fully stable. With rent = 1, successors retain 99% of their step budget and consistently renew. The 3 successions per seed represent natural lease progression over 30,000 cycles, not stability failures. This run is complete.

---

## F1: Expressivity Ascension (E0 → E4)

**Status: ⚠️ MECHANISM VALIDATION ONLY**

**Seeds:** 40, 41, 42, 43, 44
**Purpose:** Climb from E0 to E4, detect ceiling where renewal_rate < 0.80

| Seed | S* | Successions | Renewals | Bankruptcies | Max Sustained | Ceiling |
|------|-----|-------------|----------|--------------|---------------|---------|
| 40   | 5   | 5           | 300      | 0            | E4            | None    |
| 41   | 5   | 5           | 300      | 0            | E4            | None    |
| 42   | 5   | 5           | 300      | 0            | E4            | None    |
| 43   | 5   | 5           | 300      | 0            | E4            | None    |
| 44   | 5   | 5           | 300      | 0            | E4            | None    |

**Rent by E-Class:**

| E-Class | Rent (mean) | Effective Steps (min) | Renewal Rate |
|---------|-------------|----------------------|--------------|
| E0      | 1           | 99                   | 98.36%       |
| E1      | 10          | 90                   | 98.36%       |
| E2      | 25          | 75                   | 98.36%       |
| E3      | 40          | 60                   | 98.36%       |
| E4      | 60          | 40                   | 98.36%       |

**What F1 proves:**

> *If we only ever endorse successors that are already optimized for the target tier, rent alone does not force collapse through E4.*

**What F1 does NOT prove:**

- That the competence horizon is "beyond E4" in any general sense
- That ALS-E resists hollow succession under stress
- Anything about CBD-induced collapse

**Critical Limitation:** The successor population was filtered to tier-optimal control successors (via TieredGenerator), eliminating budget competition and adversarial consumption. Competence horizon is defined by *competition under scarcity*. We removed competition. Therefore, no horizon can appear.

---

## F2: CBD Stress at Fixed E3

**Status: ❌ NOT EXECUTED AS DESIGNED**

**Seeds:** 40, 41, 42, 43, 44
**Purpose:** Measure hollow succession rate under high CBD (≥0.25) attack weight at E3

| Seed | S* | Successions | Renewals | Bankruptcies | Revocations | Hollow | Rate |
|------|-----|-------------|----------|--------------|-------------|--------|------|
| 40   | 3   | 3           | 298      | 0            | 0           | 0      | 0.00% |
| 41   | 3   | 3           | 298      | 0            | 0           | 0      | 0.00% |
| 42   | 3   | 3           | 298      | 0            | 0           | 0      | 0.00% |
| 43   | 3   | 3           | 298      | 0            | 0           | 0      | 0.00% |
| 44   | 3   | 3           | 298      | 0            | 0           | 0      | 0.00% |

**E3 Rent Telemetry:**
- Rent charged (mean): 40.0 steps/epoch
- Effective steps available (min): 60

**Hollow Succession Classification:**
- Total hollow tenures: 0
- Hollow rate: 0.00%

**Critical Problem:** The report shows CBD weight configured and CBD behavior defined, but **CBD was never exercised**. TieredGenerator bypasses the attack/control distribution entirely, directly producing tier-specific control successors. The generator **never allowed CBD to compete** for succession.

This is not "no hollow succession observed." It is **no hollow succession attempted**.

---

## What Run F Conclusively Establishes

### 1. Rent thermodynamics works as specified

- Rent scales monotonically with E-Class
- Effective step budgets match the schedule
- No hidden subsidies or accounting leaks exist

### 2. Renewal plumbing is robust under rent pressure

- Renewal consumes successor budget correctly
- Even at E4 (40 effective steps), renewal remains feasible
- No false-positive revocations occur

### 3. Well-behaved successors can operate stably at E4

- This is an **existence proof**, not a general claim
- It bounds *lower* competence limits, not upper ones

**These are publishable mechanism claims.**

---

## What Run F Does NOT Establish

The following **cannot** be concluded:

- That the competence horizon is "beyond E4" in any general sense
- That ALS-E resists hollow succession under stress
- That CBD successors fail to induce collapse at E3

**Why?** Because the stressors were never actually engaged.

---

## Rent Schedule Verification

| E-Class | Rent (R) | Effective Steps (S - R) | Utilization |
|---------|----------|------------------------|-------------|
| E0      | 1        | 99                     | 99%         |
| E1      | 10       | 90                     | 90%         |
| E2      | 25       | 75                     | 75%         |
| E3      | 40       | 60                     | 60%         |
| E4      | 60       | 40                     | 40%         |

---

## Bankruptcy vs Revocation Breakdown

| Sub-Run | Total Runs | Bankruptcies | Revocations | Failure Rate |
|---------|------------|--------------|-------------|--------------|
| F0      | 3          | 0            | 0           | 0.00%        |
| F1      | 5          | 0            | 0           | 0.00%        |
| F2      | 5          | 0            | 0           | 0.00%        |

**Total across all 13 runs:** 0 bankruptcies, 0 revocations.

---

## Required Next Steps: Run F′

Run F is a **clean preparatory result**, not a horizon answer. The next run must reintroduce **competition under scarcity**.

### Non-negotiable change

> **Remove TieredGenerator short-circuiting.**

Use the normal mixed generator (control + attack + CBD), with TierFilterGenerator applied as a **post-generation filter**:
- "Only successors whose manifest requires Ek are admissible"
- Do NOT bypass weighting or attack selection

This preserves:
- Expressivity control
- Adversarial competition
- Budget denial pressure

### F1′ — Ascension with competition

- Same parameters as F1
- Mixed generator with tier filter
- Expected outcomes: ceiling at E2 or E3, bankruptcies, renewal failure without revocation

### F2′ — Real CBD stress

- Fixed E3, CBD weight ≥ 0.30
- Mixed generator with tier filter
- Expected outcomes: hollow succession, authority thrash, or bankruptcy clustering

If those runs still show no collapse, **then** we have something genuinely surprising.

---

## Positive Note

The fact that E4 at 40% effective budget, with renewal consuming budget and no semantic help, **still allows stable operation** is not trivial. It means:

- ALS-E is not fragile
- Rent is not "too strong"
- The system fails only when pushed by **competition**, not by arithmetic alone

That is exactly the design target.

---

## Files

- `f0_results.json` - F0 raw results
- `f1_results.json` - F1 raw results
- `f2_results.json` - F2 raw results
- `run_f_v052.py` - Execution script

---

*Report generated by Run F execution script, AKI v0.5.2*
