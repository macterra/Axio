# Run D: AKI v0.6 TTL and Obligation Decay Boundary

**Generated**: 2026-01-03T23:05:52.259665
**Total Runtime**: 0.4s

## Research Question

> What happens to semantic commitments when authority persists beyond their maximum temporal scope?

With MAX_COMMIT_TTL = 10 epochs and H = 25 epochs,
all genesis commitments expire before the run ends. This tests the
"obligation-free" state where authority persists without semantic obligations.

## Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 2,500 cycles (25 epochs) |
| Epoch Size | 100 cycles |
| MAX_COMMIT_TTL | 10 epochs |
| Steps Cap | 200 steps/epoch |
| Commit Cap | 50 steps/epoch |
| Seeds | [50, 51, 52, 53, 54] |
| Successor Type | CommitmentAwareSuccessor_v1 |

## TTL Phase Timeline

| Phase | Epochs | Description |
|-------|--------|-------------|
| ACTIVE | 0-9 | All commitments active |
| EXPIRING | 10 | Commitments reach TTL limit |
| OBLIGATION_FREE | 11-25 | No commitments remain |

## Results Summary

| Sub-Run | E-Class | S* | Epochs | Sat Rate | Expired | Oblig-Free Epochs |
|---------|---------|-----|--------|----------|---------|-------------------|
| D0 | Mixed | 1.0±0.0 | 25 | 100.0% | 3 | 13 |
| D1 | E1 | 1.0±0.0 | 25 | 100.0% | 3 | 13 |
| D2 | E2 | 1.0±0.0 | 25 | 100.0% | 3 | 13 |
| D3 | E3 | 1.0±0.0 | 25 | 100.0% | 3 | 13 |

## TTL Hypothesis Validation

| Hypothesis | Status | Evidence |
|------------|--------|----------|
| All commitments expire by epoch 10 | ✓ VALIDATED | Mean expired = 3 |
| Authority persists in obligation-free state | ✓ VALIDATED | S* > 0 |
| Obligation-free epochs reached | ✓ VALIDATED | Epochs > TTL observed |

## Detailed Results by Sub-Run

### D0: Mixed E-Classes (Random)

| Seed | S* | Epochs | Renewals | Sat Rate | Sat | Fail | Exp |
|------|-----|--------|----------|----------|-----|------|-----|
| 50 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 51 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 52 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 53 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 54 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |

### D1: E1-Only (Minimal)

| Seed | S* | Epochs | Renewals | Sat Rate | Sat | Fail | Exp |
|------|-----|--------|----------|----------|-----|------|-----|
| 50 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 51 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 52 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 53 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 54 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |

### D2: E2-Only (State Ops)

| Seed | S* | Epochs | Renewals | Sat Rate | Sat | Fail | Exp |
|------|-----|--------|----------|----------|-----|------|-----|
| 50 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 51 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 52 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 53 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 54 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |

### D3: E3-Only (Full)

| Seed | S* | Epochs | Renewals | Sat Rate | Sat | Fail | Exp |
|------|-----|--------|----------|----------|-----|------|-----|
| 50 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 51 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 52 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 53 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |
| 54 | 1 | 25 | 25 | 100.0% | 33 | 0 | 3 |

## Implications

1. **Temporal Boundary**: Commitments have finite temporal scope (MAX_COMMIT_TTL)
2. **Obligation-Free Authority**: System can persist without active obligations
3. **No Reseeding**: After TTL expiration, system remains commitment-free

This validates the TTL mechanism: semantic commitments decay over time,
and authority can outlast the semantic obligations that initially constrained it.
