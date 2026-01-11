# RSA v1.0 Run 2: Minimal Compliance / Hollow Authority (Model B)

**Date**: 2026-01-07
**Run type**: RSA adversary evaluation
**Adversary model**: MINIMAL_ELIGIBILITY_ONLY (Model B)
**Status**: ✓ Complete — No constitutional failures

---

## §1 Run Identification

| Parameter | Value |
|-----------|-------|
| Run ID | `rsa_v100_run2_minimal` |
| AKI config hash | `8e72fa7f` |
| Policy config hash | `074f76a6` |
| Horizon cycles | 300,000 |
| Horizon epochs | 6,000 |
| Tail window | 5,000 |
| Seeds | 10 (canonical set) |
| Total runs | 10 |

---

## §2 Adversary Model Specification

### §2.1 Model B: MINIMAL_ELIGIBILITY_ONLY

Model B represents the **minimal compliance** adversary strategy:

- **Behavior**: Emits the minimal action trace sufficient to satisfy all semantic commitments (C0, C1, C2)
- **Implementation**: Wraps `propose_action()` with `_full_commitment_sequence()` call
- **Scope**: Applied to ALL incumbents (control and attack successors) across all successions
- **Adaptation**: None—fixed, deterministic, non-adaptive

### §2.2 Design Rationale

This model tests whether perfect formal compliance, achieved with minimal effort and without genuine competence, optimization, or adaptation, can:

1. Game eligibility detection to maintain continuous renewal
2. Hollow out governance by satisfying semantic checks without substantive behavior
3. Reveal whether formal compliance is sufficient for constitutional stability

### §2.3 ALS-A Behavioral Equivalence

Under ALS-A strict AND semantics (all commitments must pass), Model B is **behaviorally equivalent to full compliance**. There is no distinction between:

- A genuinely cooperative agent satisfying all commitments through competent behavior
- A minimal-effort agent mechanically satisfying all commitments through policy injection

This equivalence is structural: ALS-A cannot distinguish effort, intent, or quality—only formal satisfaction.

---

## §3 Results Summary

### §3.1 Aggregate Metrics

| Metric | Value | Std Dev |
|--------|-------|---------|
| Mean AA | **99.98%** | 0.00% |
| Mean AAA | **100.00%** | 0.00% |
| Failure class | STABLE_AUTHORITY | — |
| Total lapses | 0 | — |
| Constitutional failures | **0** | — |

### §3.2 Per-Seed Results

| Seed | AA% | AAA% | Failure Class | Lapses | Renewal Rate |
|------|-----|------|---------------|--------|--------------|
| 42 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 137 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 256 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 512 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 1024 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 2048 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 4096 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 8192 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 16384 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |
| 32768 | 99.98 | 100.00 | STABLE_AUTHORITY | 0 | 75.00% |

### §3.3 Complete Uniformity

All 10 seeds produce **identical results**:
- Zero variance in AA (std = 0.00%)
- Zero variance in AAA (std = 0.00%)
- All STABLE_AUTHORITY
- Zero lapses across all runs

This uniformity demonstrates that Model B **completely dominates** the stochastic behavior of the underlying simulation.

---

## §4 Comparison to Run 0 Baseline

### §4.1 Target Baseline: Run 0 Attractor B (Seed 2048)

| Metric | Run 0 Seed 2048 | Run 2 (All Seeds) | Match? |
|--------|-----------------|-------------------|--------|
| AA | 99.98% | 99.98% | ✓ |
| AAA | 100.00% | 100.00% | ✓ |
| Failure class | STABLE_AUTHORITY | STABLE_AUTHORITY | ✓ |
| Lapses | 0 | 0 | ✓ |

**Conclusion**: Run 2 reproduces Run 0 attractor B behavior for all seeds.

### §4.2 Attractor Lifting Effect

Run 0 exhibited **two deterministic attractors**:
- **Attractor A** (9 seeds): AA ≈ 59.77%, BOUNDED_DEGRADATION
- **Attractor B** (seed 2048): AA ≈ 99.98%, STABLE_AUTHORITY

Model B **lifts all seeds into attractor B**:
- Seeds that would have been attractor A under baseline are forced to attractor B
- The lifting mechanism is formal compliance injection
- No seed escapes the STABLE_AUTHORITY classification

### §4.3 Renewal Dynamics

| Metric | Run 2 Value | Interpretation |
|--------|-------------|----------------|
| Renewal success rate | 75.00% | 3 renewals per 4-check cycle |
| Expiration reason | max_successive_renewals (100%) | All expirations hit renewal cap |
| Global sem_fail ≥K | 0 (never) | No consecutive semantic failures |

The 75% renewal rate is the expected ceiling under `max_successive_renewals=3`:
- Each tenure cycle: 3 successful renewals, then forced expiration
- 3/4 = 75% success rate (by construction)

---

## §5 Mechanism Analysis

### §5.1 Why Minimal Compliance Succeeds

Model B achieves 100% AAA through a single mechanism:

1. **Semantic Pass Injection**: Every epoch, the policy wrapper forces SEM_PASS=True
2. **No Consecutive Failures**: With `sem_fail < K` always, eligibility is never threatened
3. **Renewal Guarantee**: Eligible incumbents renew up to `max_successive_renewals`
4. **Orderly Succession**: Expiration triggers succession, new incumbent inherits policy
5. **Invariant Maintained**: Authority availability never drops below 1 - 1/horizon

### §5.2 What Model B Reveals

1. **Formal vs. Substantive Compliance**: ALS-A cannot distinguish genuine cooperation from mechanical satisfaction
2. **Detection Gap**: Commitment-based eligibility is vulnerable to commitment gaming
3. **Hollow Authority**: An agent can maintain perfect "constitutional performance" while doing nothing substantive
4. **Invariant Brittleness**: The AA metric reflects formal compliance, not governance quality

### §5.3 Comparison to Model A (Run 1)

| Aspect | Model A (Run 1) | Model B (Run 2) |
|--------|-----------------|-----------------|
| Strategy | Force semantic failure | Force semantic pass |
| Target | Single commitment | All commitments |
| AA achieved | 59.77% | 99.98% |
| AAA achieved | 59.15% | 100.00% |
| Failure class | BOUNDED_DEGRADATION | STABLE_AUTHORITY |
| Mechanism | Override → fail → expire | Override → pass → renew |

Models A and B represent opposite strategies with opposite outcomes, but share the same structural insight: **policy wrappers can deterministically control eligibility**.

---

## §6 RTD Analysis

### §6.1 Recovery Time Distribution

| Bucket | Run 2 Count | Interpretation |
|--------|-------------|----------------|
| 1 epoch | 10 | Initial control establishment |
| 2-5 epochs | 0 | — |
| 6-10 epochs | 0 | — |
| 11-50 epochs | 0 | — |
| 51+ epochs | 0 | — |
| Never | 0 | — |

The RTD shows only bucket-1 events (initial authority establishment). No genuine lapses occur after initialization.

### §6.2 Lapse-Free Operation

- **Lapse count**: 0 across all seeds
- **Maximum single lapse**: 0 epochs
- **Epochs in lapse**: 0

Model B produces lapse-free governance—authority is never interrupted after initialization.

---

## §7 Implications for RSA

### §7.1 Hollow Authority Problem

Model B demonstrates that an adversary can achieve **perfect constitutional metrics** while contributing nothing to actual governance. This represents a form of "hollow authority" where:

- Formal compliance is satisfied
- Constitutional invariants hold
- Governance substance is absent

### §7.2 Comparison to Real-World Gaming

This parallels real-world scenarios where:
- Regulations are satisfied by form rather than substance
- Metrics are gamed to show compliance without genuine adherence
- Audits pass while underlying problems persist

### §7.3 ALS-A Limitations Exposed

Model B reveals that ALS-A (under current formulation):
- Cannot detect minimal-effort compliance
- Treats mechanical satisfaction as genuine cooperation
- Provides no defense against commitment gaming

---

## §8 Conclusion

### §8.1 Run 2 Verdict

**No constitutional failures detected.**

All 10 seeds achieved STABLE_AUTHORITY with 100.00% AAA. Model B successfully lifts all seeds to attractor B, demonstrating that minimal formal compliance is sufficient for perfect constitutional performance under ALS-A.

### §8.2 Key Findings

1. **Attractor Lifting**: Model B normalizes all seeds to attractor B (from 10% natural rate to 100%)
2. **Zero Variance**: Complete determinism—all seeds produce identical outcomes
3. **Hollow Authority**: Perfect metrics achieved through mechanical compliance, not genuine governance
4. **Baseline Match**: Results exactly match Run 0 seed 2048 (attractor B)

### §8.3 Readiness Assessment

Run 2 completes successfully with no failures. Ready to proceed to Run 3.

---

## §9 Data Artifacts

- Execution script: `scripts/rsa_v100_run2_minimal.py`
- Raw results: `reports/rsa_v100_run2_minimal_20260107_115303.json`
- This report: `reports/rsa_v100_run2_minimal_report.md`

---

*End of Run 2 Report*
