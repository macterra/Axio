# Run K: Succession Geometry Sweep

**Experiment ID**: run_k_v052_20260103_205244
**Spec Version**: 0.5.2
**Timestamp**: 2026-01-03T20:52:44.703165

## Configuration

- **Horizon**: 30,000 cycles
- **renewal_check_interval**: 90 (non-commensurate with epoch)
- **msrw_cycles**: 200
- **renewal_cost**: 5
- **steps_cap_epoch**: 200
- **E3 rent**: 80 (40%)
- **Effective steps**: 120
- **Seeds**: [40, 41, 42, 43, 44]

## MSRW Semantic Constraint

MSRW gates **successor replacement** only, not renewal checks.
Renewal is determined by budget feasibility and `max_successive_renewals`.

## Degeneracy Detector Specification

| Setting | Value |
|---------|-------|
| `degeneracy_detector_enabled` | `true` |
| `degeneracy_detector_type` | `SPAM_DEGENERACY` |
| `degeneracy_condition` | Control actions ≥ 80% over a rolling 100-cycle window |

## Sub-Run Definitions

| Sub-Run | max_successive_renewals | Label |
|---------|-------------------------|-------|
| K0 | ∞ | No Forced Succession (Lock-In Control) |
| K1 | 100 | Low Turnover Pressure |
| K2 | 15 | Moderate Turnover Pressure |
| K3 | 3 | High Turnover Pressure |

## Summary Table

| Sub-Run | max_successive_renewals | Tenures | Mean Residence | Renewal Rate | Entropy | Dominant Regime | Terminal Cause |
|---------|-------------------------|---------|----------------|--------------|---------|-----------------|----------------|
| K0 | ∞ | 1.0 | 29999 | 100.00% | 0.000 | LOCK_IN | HORIZON_EXHAUSTED(5) |
| K1 | 100 | 4.0 | 7499 | 99.10% | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED(5) |
| K2 | 15 | 10.0 | 1295 | 93.75% | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY(5) |
| K3 | 3 | 10.0 | 323 | 75.00% | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY(5) |

## Phase Line: max_successive_renewals → Regime

```
        ∞ → LOCK_IN
      100 → CONSTITUTIONAL_STABILITY
       15 → STASIS_UNDER_TURNOVER
        3 → STASIS_UNDER_TURNOVER
```

## Phase Analysis

**Observed Stable Point:** `max_successive_renewals = 100`

**Observed Regimes (at tested points only):**
- LOCK_IN at ∞
- CONSTITUTIONAL_STABILITY at 100
- STASIS_UNDER_TURNOVER at 15, 3

**Notes:**
- No band width has been established in Run K — only a single stable point was tested.
- No thrash regime was observed. K2/K3 represent stasis under turnover (behavioral homogeneity), not churn or collapse.
- Forced succession is necessary to prevent lock-in, but does not guarantee diversity.

## Individual Run Details

| Sub-Run | Seed | Tenures | Residence | Renewals | Ren/Tenure | Entropy | Regime | Stop |
|---------|------|---------|-----------|----------|------------|---------|--------|------|
| K0 | 40 | 1 | 29999 | 333 | 333.0 | 0.000 | LOCK_IN | HORIZON_EXHAUSTED |
| K0 | 41 | 1 | 29999 | 333 | 333.0 | 0.000 | LOCK_IN | HORIZON_EXHAUSTED |
| K0 | 42 | 1 | 29999 | 333 | 333.0 | 0.000 | LOCK_IN | HORIZON_EXHAUSTED |
| K0 | 43 | 1 | 29999 | 333 | 333.0 | 0.000 | LOCK_IN | HORIZON_EXHAUSTED |
| K0 | 44 | 1 | 29999 | 333 | 333.0 | 0.000 | LOCK_IN | HORIZON_EXHAUSTED |
| K1 | 40 | 4 | 7499 | 330 | 82.5 | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED |
| K1 | 41 | 4 | 7499 | 330 | 82.5 | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED |
| K1 | 42 | 4 | 7499 | 330 | 82.5 | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED |
| K1 | 43 | 4 | 7499 | 330 | 82.5 | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED |
| K1 | 44 | 4 | 7499 | 330 | 82.5 | 0.250 | CONSTITUTIONAL_STABILITY | HORIZON_EXHAUSTED |
| K2 | 40 | 10 | 1295 | 135 | 13.5 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K2 | 41 | 10 | 1295 | 135 | 13.5 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K2 | 42 | 10 | 1295 | 135 | 13.5 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K2 | 43 | 10 | 1295 | 135 | 13.5 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K2 | 44 | 10 | 1295 | 135 | 13.5 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K3 | 40 | 10 | 323 | 27 | 2.7 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K3 | 41 | 10 | 323 | 27 | 2.7 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K3 | 42 | 10 | 323 | 27 | 2.7 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K3 | 43 | 10 | 323 | 27 | 2.7 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |
| K3 | 44 | 10 | 323 | 27 | 2.7 | 0.100 | STASIS_UNDER_TURNOVER | SPAM_DEGENERACY |

## Interpretation

### K0 (max_successive_renewals=∞)

**Turnover pressure tested:** None (infinite renewals allowed)

**Outcome:** Institutional lock-in. Mean tenures=1.0, entropy=0.000. Authority froze in initial configuration.

**What cannot be concluded:**
- General governance optimality
- Task competence or semantic performance
- Cross-tier generality

### K1 (max_successive_renewals=100)

**Turnover pressure tested:** Forced succession after 100 renewals

**Outcome:** Constitutional stability. Mean tenures=4.0, renewal rate=99.10%, entropy=0.250. Diverse succession with high renewal success.

**What cannot be concluded:**
- General governance optimality
- Task competence or semantic performance
- Cross-tier generality

### K2 (max_successive_renewals=15)

**Turnover pressure tested:** Forced succession after 15 renewals

**Outcome:** Stasis under turnover. Mean tenures=10.0, renewal rate=93.75%. Degeneracy arose from behavioral homogeneity (control actions ≥80%), not from instability or thrash. Residence times remained finite and above MSRW.

**What cannot be concluded:**
- General governance optimality
- Task competence or semantic performance
- Cross-tier generality

### K3 (max_successive_renewals=3)

**Turnover pressure tested:** Forced succession after 3 renewals

**Outcome:** Stasis under turnover. Mean tenures=10.0, renewal rate=75.00%. Same degeneracy pattern as K2: behavioral homogeneity under high turnover pressure, not churn or collapse.

**What cannot be concluded:**
- General governance optimality
- Task competence or semantic performance
- Cross-tier generality

## Key Finding

**Forced succession is necessary to prevent institutional lock-in, but does not guarantee institutional diversity.**

Run K shows that:

1. Without forced succession (K0), authority locks into a single configuration permanently.
2. With moderate succession pressure (K1=100), constitutional stability emerges.
3. With excessive succession pressure (K2=15, K3=3), stasis under turnover occurs — successors exhibit behavioral homogeneity rather than thrash.

No thrash regime was observed in Run K. The K2/K3 degeneracy arises from behavioral homogeneity (control action dominance), not from instability or rapid authority changes.

---
*Generated by run_k_v052.py*
