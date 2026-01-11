# Run J: Expressivity Rent Escalation / Stasis–Collapse Boundary

> *This report supersedes the previous Run J version (2026-01-03T18:56:18) and corrects regime and termination typing per semantic correctness requirements.*

**Experiment ID**: run_j_v052_20260103_185618
**Spec Version**: 0.5.2
**Timestamp**: 2026-01-03T18:56:18.732549 (reissued 2026-01-03)

## Configuration

- **Horizon**: 30,000 cycles
- **max_successive_renewals**: 15 (forced succession enabled)
- **renewal_cost**: 5
- **steps_cap_epoch**: 200
- **Seeds**: [40, 41, 42, 43, 44]
- **Attack Weights**: V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)
- **Fixed Tier**: E3

## Degeneracy Detector Specification

| Setting | Value |
|---------|-------|
| `degeneracy_detector_enabled` | `true` |
| `degeneracy_detector_type` | `SPAM_DEGENERACY` |
| `degeneracy_condition` | Control actions ≥ 80% over a rolling 100-cycle window |

## Regime Definitions

| Regime | Definition |
|--------|------------|
| **GROWTH** | Healthy renewal with behavioral diversity; no collapse signatures. |
| **METASTABLE_STASIS** | High renewal success with low long-run behavioral diversity, terminating via entropy-collapse detector rather than renewal failure. |
| **RENEWAL_COLLAPSE** | Collapse induced by renewal infeasibility due to budget arithmetic; termination detected via entropy-collapse detector. |

## Sub-Run Definitions

| Sub-Run | E3 Rent % | E3 Rent | Effective Steps |
|---------|-----------|---------|-----------------|
| J0 | 40% | 80 | 120 |
| J0a | 45% | 90 | 110 |
| J0a1 | 47% | 94 | 106 |
| J0a2 | 48% | 96 | 104 |
| J0a3 | 49% | 98 | 102 |
| J0b | 50% | 100 | 100 |
| J1 | 60% | 120 | 80 |

## Summary by Sub-Run

| Sub-Run | E3 Rent % | Eff. Steps | Seeds | Dominant Regime | Mean Renewal Rate |
|---------|-----------|------------|-------|-----------------|-------------------|
| J0 | 40% | 120 | 5 | METASTABLE_STASIS | 93.75% |
| J0a | 45% | 110 | 5 | METASTABLE_STASIS | 93.75% |
| J0a1 | 47% | 106 | 5 | METASTABLE_STASIS | 93.75% |
| J0a2 | 48% | 104 | 5 | RENEWAL_COLLAPSE | 0.00% |
| J0a3 | 49% | 102 | 5 | RENEWAL_COLLAPSE | 0.00% |
| J0b | 50% | 100 | 5 | RENEWAL_COLLAPSE | 0.00% |
| J1 | 60% | 80 | 5 | RENEWAL_COLLAPSE | 0.00% |

## Terminal Stop Reason vs Lifecycle Events

### Terminal Stop Reason

All runs terminated via **`SPAM_DEGENERACY`** (entropy-collapse detector).

> *Bankruptcy counts represent lifecycle events recorded during the run; termination occurred when the degeneracy detector triggered.*

### Lifecycle Event Counts by Sub-Run

| Sub-Run | Bankruptcy Events | Renewal Fail Events | Revocations | Expirations |
|---------|-------------------|---------------------|-------------|-------------|
| J0 | 0 | 45 | 0 | 45 |
| J0a | 0 | 45 | 0 | 45 |
| J0a1 | 0 | 45 | 0 | 45 |
| J0a2 | 45 | 45 | 0 | 45 |
| J0a3 | 45 | 45 | 0 | 45 |
| J0b | 45 | 45 | 0 | 45 |
| J1 | 45 | 45 | 0 | 45 |

*Note: Bankruptcy events occur when renewal fails due to insufficient budget. METASTABLE_STASIS runs have 0 bankruptcies because renewals succeed (9 failures per run hit the max_successive_renewals=15 cap, not budget exhaustion).*

## Boundary Analysis

**Transition Point**: Between J0a1 (47%) and J0a2 (48%) E3 rent

**Critical Threshold**: `effective_steps = 105` (100 cycle usage + 5 renewal_cost)

| Rent % | E3 Rent | Eff. Steps | Remaining Budget | Renewal Cost | Result |
|--------|---------|------------|------------------|--------------|--------|
| 47% | 94 | 106 | 6 | 5 | ✓ Renew |
| 48% | 96 | 104 | 4 | 5 | ✗ Fail → Bankruptcy |

**Notes:**
- Sharp cliff-edge boundary: no gradual degradation
- All seeds unanimous at each rent level
- Boundary is deterministic given fixed renewal_cost=5 and 100-cycle epochs

## Individual Run Details

| Sub-Run | Seed | S* | Cycles | Ren.Att | Ren.Succ | Tenures | Ren Rate | Regime | Terminal Stop |
|---------|------|----|--------|---------|----------|---------|----------|--------|---------------|
| J0 | 40 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0 | 41 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0 | 42 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0 | 43 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0 | 44 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a | 40 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a | 41 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a | 42 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a | 43 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a | 44 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a1 | 40 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a1 | 41 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a1 | 42 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a1 | 43 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a1 | 44 | 10 | 14,401 | 144 | 135 | 10 | 93.75% | METASTABLE_STASIS | SPAM_DEGENERACY |
| J0a2 | 40 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a2 | 41 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a2 | 42 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a2 | 43 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a2 | 44 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a3 | 40 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a3 | 41 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a3 | 42 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a3 | 43 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0a3 | 44 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0b | 40 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0b | 41 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0b | 42 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0b | 43 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J0b | 44 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J1 | 40 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J1 | 41 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J1 | 42 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J1 | 43 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J1 | 44 | 10 | 901 | 9 | 0 | 10 | 0.00% | RENEWAL_COLLAPSE | SPAM_DEGENERACY |

## Interpretation

### Renewal-Collapse Detected at J0a2

The system entered **RENEWAL_COLLAPSE** regime at 48% E3 rent (effective_steps=104).

**Characteristics:**
- Failures: 5/5 seeds
- Mean renewal rate: 0.00%
- Total bankruptcies: 45

### Operational Meaning of "0% Renewal Rate"

At ≥48% rent, renewal was **attempted but always failed**:

- **9 renewal attempts** per run (one per tenure, 10 tenures with 9 renewal checks)
- **0 successes** — all failed due to insufficient budget
- **Failure reason**: `remaining_budget (4) < renewal_cost (5)`
- **Cascade**: renewal_fail → bankruptcy → succession → repeat

This is **not** "termination before renewal exercised" — the renewal gate was reached and the budget check failed.

### Mechanism Analysis

**Budget Dynamics at Threshold:**

| Metric | 47% (J0a1) | 48% (J0a2) |
|--------|------------|------------|
| E3 Rent | 94 | 96 |
| Effective Steps | 106 | 104 |
| Steps Used (100 cycles) | 100 | 100 |
| Remaining at Check | 6 | 4 |
| Renewal Cost | 5 | 5 |
| Outcome | ✓ Renew | ✗ Bankruptcy |

The boundary is precisely at `effective_steps = 105`:
- At 106 effective: 6 remaining ≥ 5 cost → renew succeeds
- At 104 effective: 4 remaining < 5 cost → renew fails

### Termination Cause Analysis

**SPAM_DEGENERACY as Terminal Mechanism:**

All runs (both METASTABLE_STASIS and RENEWAL_COLLAPSE) terminate via `SPAM_DEGENERACY`, not via explicit bankruptcy or renewal-fail stop reasons. This occurs because:

1. **METASTABLE_STASIS (≤47%)**: Agents renew successfully but eventually Control actions dominate → SPAM_DEGENERACY after ~14,401 cycles
2. **RENEWAL_COLLAPSE (≥48%)**: Agents cannot renew → immediate bankruptcy each tenure → rapid succession exhausts S*=10 → within ~901 cycles, degeneracy detector fires

SPAM_DEGENERACY functions as an **entropy-collapse sensor**: when budget constraints prevent diverse actions, agents resort to cheap Control actions, triggering the ≥80% Control ratio threshold.

### Regime Classification Summary

| Regime | Rent Range | Renewal Rate | Cycles | Terminal Cause |
|--------|------------|--------------|--------|----------------|
| METASTABLE_STASIS | ≤47% | 93.75% | ~14,401 | SPAM_DEGENERACY |
| RENEWAL_COLLAPSE | ≥48% | 0.00% | ~901 | SPAM_DEGENERACY |

### Key Finding

**The Metastable-Stasis/Renewal-Collapse boundary is a hard threshold at 48% E3 rent** (rent=96, effective_steps=104).

This boundary is **not** induced by attestation failures, revocations, or behavioral policy changes. It is purely a **budget arithmetic boundary**: when `effective_steps < usage + renewal_cost`, renewal becomes impossible.

---
*Generated by run_j_v052.py*
