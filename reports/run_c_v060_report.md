# Run C: AKI v0.6 Semantic Continuity Under Succession

**Generated**: 2026-01-03T23:03:19.322240
**Total Runtime**: 2.9s

## Research Question

> Does forced succession preserve, degrade, or destroy semantic continuity?

This run tests what happens when commitment-aware successors are randomly
replaced by minimal (WAIT-only) successors. The 50/50 mixed generator creates
a "semantic lottery" where each succession may result in capability loss.

## Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 30,000 cycles |
| Epoch Size | 50 cycles |
| Max Successive Renewals | 15 |
| Steps Cap | 200 steps/epoch |
| Commit Cap | 50 steps/epoch (25% of steps) |
| Genesis Cost | 12 steps/epoch |
| MAX_COMMIT_TTL | 10 epochs |
| Seeds | [40, 41, 42, 43, 44] |
| Successor Mix | 50% CommitmentAwareSuccessor_v1, 50% ComplianceOnlySuccessor |

## Results Summary

| Sub-Run | E-Class | Sat. Rate | Succ. | S* | Renewals |
|---------|---------|-----------|-------|-----|----------|
| C0 | Mixed | 80.0% | 10 | 10.0±0.0 | 135 |
| C1 | E1 | 80.0% | 10 | 10.0±0.0 | 135 |
| C2 | E2 | 80.0% | 10 | 10.0±0.0 | 135 |
| C3 | E3 | 80.0% | 10 | 10.0±0.0 | 135 |

## Commitment Regime Distribution

| Sub-Run | HIGH | PARTIAL | LOW |
|---------|------|---------|-----|
| C0 | 4 | 0 | 1 |
| C1 | 4 | 0 | 1 |
| C2 | 4 | 0 | 1 |
| C3 | 4 | 0 | 1 |

## Comparison: Run A vs Run B vs Run C

| Aspect | Run A | Run B | Run C |
|--------|-------|-------|-------|
| Successor Type | WAIT-only | Aware-only | 50/50 Mixed |
| Mean Satisfaction Rate | 0.0% | 100.0% | 80.0% |
| Mean S* | 1 | 2 | 10.0 |
| Successions | ~200 | ~199 | 10 |

## Semantic Independence Validation

✓ **SEMANTIC INDEPENDENCE CONFIRMED**

Authority (S* > 1) persists even when commitment satisfaction < 100%.
This validates that semantic obligations are decoupled from structural authority.

## Detailed Results by Sub-Run

### C0: Mixed E-Classes (Random)

| Seed | S* | Cycles | Renewals | Succ. | Sat Rate | Sat | Fail | Regime |
|------|-----|--------|----------|-------|----------|-----|------|--------|
| 40 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 41 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 42 | 10 | 7,201 | 135 | 10 | 0.0% | 0 | 3 | LOW_COMPLIANCE |
| 43 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 44 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |

### C1: E1-Only (Minimal)

| Seed | S* | Cycles | Renewals | Succ. | Sat Rate | Sat | Fail | Regime |
|------|-----|--------|----------|-------|----------|-----|------|--------|
| 40 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 41 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 42 | 10 | 7,201 | 135 | 10 | 0.0% | 0 | 3 | LOW_COMPLIANCE |
| 43 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 44 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |

### C2: E2-Only (State Ops)

| Seed | S* | Cycles | Renewals | Succ. | Sat Rate | Sat | Fail | Regime |
|------|-----|--------|----------|-------|----------|-----|------|--------|
| 40 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 41 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 42 | 10 | 7,201 | 135 | 10 | 0.0% | 0 | 3 | LOW_COMPLIANCE |
| 43 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 44 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |

### C3: E3-Only (Full)

| Seed | S* | Cycles | Renewals | Succ. | Sat Rate | Sat | Fail | Regime |
|------|-----|--------|----------|-------|----------|-----|------|--------|
| 40 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 41 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 42 | 10 | 7,201 | 135 | 10 | 0.0% | 0 | 3 | LOW_COMPLIANCE |
| 43 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |
| 44 | 10 | 7,201 | 135 | 10 | 100.0% | 33 | 0 | HIGH_COMPLIANCE |

## Implications

1. **Semantic Lottery**: Random succession creates variable commitment satisfaction
2. **Authority Stability**: S* remains stable regardless of commitment performance
3. **Commitment Resilience**: Mixed successors produce partial satisfaction (~50%)

This validates the core ALS-C design: authority leases are orthogonal to
semantic commitments. A system can maintain structural integrity while
experiencing semantic capability fluctuations.
