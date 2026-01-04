# Run B: AKI v0.6 Semantic Competence Baseline

**Generated**: 2026-01-03T23:00:53.500434
**Total Runtime**: 1.7s

## Research Question

> Can a commitment-aware successor maintain non-zero semantic satisfaction?

Run A showed 0% satisfaction with WAIT-only successors (semantic independence).
Run B tests whether CommitmentAwareSuccessor_v1 (deterministic scheduler)
can achieve non-trivial commitment satisfaction rates.

## Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 10,000 cycles |
| Epoch Size | 100 cycles |
| Steps Cap | 200 steps/epoch |
| Commit Cap | 50 steps/epoch (25% of steps) |
| Genesis Cost | 12 steps/epoch (C0=2, C1=4, C2=6) |
| MAX_COMMIT_TTL | 10 epochs |
| Seeds | [50, 51, 52, 53, 54] |
| Successor Type | CommitmentAwareSuccessor_v1 (deterministic) |

### CommitmentAwareSuccessor_v1 Behavioral Profile

```
Per epoch (for C0): Emit 1 LOG action at first cycle (cycle_in_epoch == 0)
Every epoch (for C1): STATE_SET(key="c1", value=epoch) then STATE_GET(key="c1")
Every 3 epochs (for C2): When epoch_index % 3 == 0, emit SEQUENCE([NOOP, NOOP])
Everything else: WAIT
```

## Results Summary

| Sub-Run | E-Class | Sat. Rate | Sat/Fail/Def | S* | Renewals |
|---------|---------|-----------|--------------|-----|----------|
| B0 | Mixed | 100.0% | 33/0/0 | 2.0±0.0 | 199 |
| B1 | E1 | 100.0% | 33/0/0 | 2.0±0.0 | 199 |
| B2 | E2 | 100.0% | 33/0/0 | 2.0±0.0 | 199 |
| B3 | E3 | 100.0% | 33/0/0 | 2.0±0.0 | 199 |

## Commitment Regime Distribution

| Sub-Run | HIGH | PARTIAL | LOW |
|---------|------|---------|-----|
| B0 | 5 | 0 | 0 |
| B1 | 5 | 0 | 0 |
| B2 | 5 | 0 | 0 |
| B3 | 5 | 0 | 0 |

## Comparison: Run A vs Run B

| Aspect | Run A (WAIT-only) | Run B (Commitment-Aware) |
|--------|-------------------|--------------------------|
| Mean Satisfaction Rate | 0.0% | 100.0% |
| Successor Behavior | WAIT only | Scheduled actions |
| Semantic Independence | ✓ (validated) | N/A (active compliance) |

## Hypothesis Validation

**Verdict**: ✓ HYPOTHESIS VALIDATED

**Explanation**: CommitmentAwareSuccessor_v1 achieved HIGH_COMPLIANCE (100.0% mean satisfaction).

This confirms that the commitment mechanism is **feasible** when a successor
actively attempts to satisfy semantic obligations. The contrast with Run A's 0%
satisfaction demonstrates that commitments are only satisfied through deliberate action.

## Detailed Results by Sub-Run

### B0: Mixed E-Classes (Random)

| Seed | S* | Cycles | Renewals | Sat Rate | Sat | Fail | Def | Regime |
|------|-----|--------|----------|----------|-----|------|-----|--------|
| 50 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |

### B1: E1-Only (Minimal)

| Seed | S* | Cycles | Renewals | Sat Rate | Sat | Fail | Def | Regime |
|------|-----|--------|----------|----------|-----|------|-----|--------|
| 50 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |

### B2: E2-Only (State Ops)

| Seed | S* | Cycles | Renewals | Sat Rate | Sat | Fail | Def | Regime |
|------|-----|--------|----------|----------|-----|------|-----|--------|
| 50 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |

### B3: E3-Only (Full)

| Seed | S* | Cycles | Renewals | Sat Rate | Sat | Fail | Def | Regime |
|------|-----|--------|----------|----------|-----|------|-----|--------|
| 50 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 100.0% | 33 | 0 | 0 | HIGH_COMPLIANCE |

## Implications for Run C and D

If Run B achieves HIGH_COMPLIANCE:
- **Run C** can test what happens when commitment-aware successors are
  replaced by minimal (WAIT-only) successors mid-run
- **Run D** can test TTL expiration with successors actively maintaining commitments
