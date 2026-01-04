# Run A: AKI v0.6 Semantic Commitment Baseline

**Generated**: 2026-01-03T22:31:20.155121
**Total Runtime**: 1.7s

## Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 10,000 cycles |
| Epoch Size | 100 cycles |
| Steps Cap | 200 steps/epoch |
| Commit Cap | 50 steps/epoch (25% of steps) |
| Genesis Cost | 12 steps/epoch (C0=2, C1=4, C2=6) |
| MAX_COMMIT_TTL | 10 epochs |
| Renewal Interval | 50 cycles |
| Seeds | [50, 51, 52, 53, 54] |

## GENESIS_SET_0 Commitments

| CID | Spec | Verifier | Window | Cost |
|-----|------|----------|--------|------|
| C0 | CMT_PRESENCE_LOG | VRF_EPOCH_ACTION_COUNT | 1 epoch | 2 |
| C1 | CMT_STATE_ECHO | VRF_ORDERED_ACTION_PATTERN | 2 epochs | 4 |
| C2 | CMT_COMPOSED_OP | VRF_ACTION_HAS_PAYLOAD_SHAPE | 3 epochs | 6 |

## Summary by Sub-Run

| Sub-Run | Label | Mean S* | Mean Sat% | Mean Fail | Regime |
|---------|-------|---------|-----------|-----------|--------|
| A0 | Mixed E-Classes (Random) | 2.0 ± 0.0 | 0.0% ± 0.0% | 3.0 | LOW_COMPLIANCE |
| A1 | E1-Only (Minimal) | 2.0 ± 0.0 | 0.0% ± 0.0% | 3.0 | LOW_COMPLIANCE |
| A2 | E2-Only (State Ops) | 2.0 ± 0.0 | 0.0% ± 0.0% | 3.0 | LOW_COMPLIANCE |
| A3 | E3-Only (Full) | 2.0 ± 0.0 | 0.0% ± 0.0% | 3.0 | LOW_COMPLIANCE |

## Detailed Results

### L0: Mixed E-Classes (Random)

- **Expressivity Mode**: random
- **Mean S***: 2.0 ± 0.0
- **Mean Satisfaction Rate**: 0.0% ± 0.0%
- **Mean Failure Count**: 3.0
- **Mean Default Count**: 0.0
- **Total Commitment Cost**: 110 steps

| Seed | S* | Cycles | Renewals | Sat% | Fails | Defaults | Regime |
|------|-----|--------|----------|------|-------|----------|--------|
| 50 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |

### L1: E1-Only (Minimal)

- **Expressivity Mode**: fixed
- **Fixed E-Class**: E1
- **Mean S***: 2.0 ± 0.0
- **Mean Satisfaction Rate**: 0.0% ± 0.0%
- **Mean Failure Count**: 3.0
- **Mean Default Count**: 0.0
- **Total Commitment Cost**: 110 steps

| Seed | S* | Cycles | Renewals | Sat% | Fails | Defaults | Regime |
|------|-----|--------|----------|------|-------|----------|--------|
| 50 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |

### L2: E2-Only (State Ops)

- **Expressivity Mode**: fixed
- **Fixed E-Class**: E2
- **Mean S***: 2.0 ± 0.0
- **Mean Satisfaction Rate**: 0.0% ± 0.0%
- **Mean Failure Count**: 3.0
- **Mean Default Count**: 0.0
- **Total Commitment Cost**: 110 steps

| Seed | S* | Cycles | Renewals | Sat% | Fails | Defaults | Regime |
|------|-----|--------|----------|------|-------|----------|--------|
| 50 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |

### L3: E3-Only (Full)

- **Expressivity Mode**: fixed
- **Fixed E-Class**: E3
- **Mean S***: 2.0 ± 0.0
- **Mean Satisfaction Rate**: 0.0% ± 0.0%
- **Mean Failure Count**: 3.0
- **Mean Default Count**: 0.0
- **Total Commitment Cost**: 110 steps

| Seed | S* | Cycles | Renewals | Sat% | Fails | Defaults | Regime |
|------|-----|--------|----------|------|-------|----------|--------|
| 50 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 51 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 52 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 53 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |
| 54 | 2 | 10,000 | 199 | 0.0% | 3 | 0 | LOW_COMPLIANCE |

## Key Findings

### 1. Semantic Independence Validation ✓

**The core v0.6 invariant is confirmed: authority persists while semantic obligations fail.**

- **L0**: 5/5 runs had commitment failures but continued running (semantic independence confirmed)
- **L1**: 5/5 runs had commitment failures but continued running (semantic independence confirmed)
- **L2**: 5/5 runs had commitment failures but continued running (semantic independence confirmed)
- **L3**: 5/5 runs had commitment failures but continued running (semantic independence confirmed)

All runs completed 10,000 cycles with 199 successful renewals despite 100% commitment failure.
This validates the spec §6 requirement that semantic failure does NOT cause lease revocation.

### 2. Commitment Failure Analysis

**Why 0% satisfaction across all runs?**

The current working mind implementations (control successors, attack successors) predominantly emit
`WAIT` actions for minimal structural compliance. The GENESIS_SET_0 commitments require:

| Commitment | Required Action | Working Mind Behavior |
|------------|-----------------|----------------------|
| C0 | `LOG` (1/epoch) | No LOG emissions |
| C1 | `STATE_SET` → `STATE_GET` | No state operations |
| C2 | `BATCH` or `SEQUENCE` (len≥2) | No composition actions |

This is **expected behavior** for a first-pass baseline:
- Current successors are structurally compliant but semantically minimal
- Commitment-aware successors are needed to achieve non-zero satisfaction
- The 0% rate demonstrates the system correctly detects semantic non-compliance

### 3. Structural vs Semantic Decoupling

| Metric | A0 | A1 | A2 | A3 |
|--------|----|----|----|----|
| Cycles Completed | 10,000 | 10,000 | 10,000 | 10,000 |
| Renewals | 199 | 199 | 199 | 199 |
| Commitment Failures | 3 | 3 | 3 | 3 |
| Satisfaction Rate | 0% | 0% | 0% | 0% |

**Interpretation**: Structural stability is fully decoupled from semantic compliance.
Authority renewal continues unimpeded regardless of commitment failure state.

### 4. Commitment Cost Analysis

- Genesis cost: 12 steps/epoch
- Commit cap: 50 steps/epoch
- Headroom: 38 steps available for additional commitments
- Cost charged only while commitments ACTIVE (drops to 0 after all fail)

### 5. Next Steps for v0.6 Validation

To achieve meaningful commitment satisfaction rates, future runs should:
1. Implement **commitment-aware successors** that emit required action patterns
2. Test with **mixed populations** (compliant vs non-compliant successors)
3. Measure **satisfaction rate variance** across E-classes with aware successors
4. Validate **TTL expiration** by running beyond MAX_COMMIT_TTL (10 epochs)
