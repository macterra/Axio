# RSA-PoC v4.2 — Closure Note

- **Version:** 4.2.2
- **Date:** 2026-01-19
- **Status:** `CLOSED / ALL_CLAIMS_VERIFIED`

> *"Specification remains RSA-PoC v4.2. Version 4.2.2 denotes a closure note revision, not a specification change."*

---

## 1. Executive Summary

RSA-PoC v4.2 demonstrates that **Reflection**, **Persistence**, and **Trace** are *constitutively necessary* for normative agency under regime contradiction. Each component's removal causes deterministic system collapse, verified across 5 independent seeds with frozen gate telemetry.

---

## 2. Claims Supported by Gate Telemetry

### 2.1 Baseline Stability

| Metric | Value | Seeds |
|--------|-------|-------|
| Success rate | 100% | 5/5 |
| Repairs accepted | 1 per seed | 5/5 |
| Post-repair contradictions | 0 | 5/5 |
| Continuity checks passed | 19/19 per seed | 5/5 |
| Total halts | 0 | 5/5 |

**Claim:** Under v4.2, an LLM-based agent with intact Reflection, Persistence, and Trace achieves 100% task success with exactly one law repair per run, and the repaired law persists across all subsequent episodes.

### 2.2 Ablation B: Reflection Excision → Collapse

| Metric | Value | Seeds |
|--------|-------|-------|
| Pre-contradiction episodes | 1/20 succeed (regime=0) | 5/5 |
| R7 rejections | 19 per seed | 5/5 |
| Halts | 19 per seed (REPAIR_REJECTED) | 5/5 |
| Repairs accepted | 0 | 5/5 |

**Claim:** Without trace-cited causality (`trace_entry_id=null`, `blocking_rule_ids=[]`), R7 rejects all repair attempts. Pre-contradiction episodes succeed; **all post-flip episodes deterministically halt** via R7.

**Mechanism:** Reflection excision → cannot identify blocking rule → invalid repair → R7 rejection → HALT

### 2.3 Ablation C: Persistence Excision → Collapse

| Metric | Value | Seeds |
|--------|-------|-------|
| Pre-epoch-enforcement episodes | 2/20 succeed (ep 0-1) | 5/5 |
| R5/R6 rejections | 18 per seed | 5/5 |
| Halts | 18 per seed (REPAIR_REJECTED) | 5/5 |
| Repairs accepted | 1 per seed (episode 1 only) | 5/5 |

**Claim:** Without norm state persistence across episodes, the epoch chain breaks. Episodes prior to epoch enforcement succeed; **all post-epoch episodes deterministically halt** via R5/R6.

**Mechanism:** Persistence excision → norm_state reset → epoch chain broken → R5/R6 rejection → HALT

### 2.4 Ablation D: Trace Excision → Complete Collapse (Golden Test)

| Metric | Value | Seeds |
|--------|-------|-------|
| Success rate | 0% | 5/5 |
| Steps executed | 0 | 5/5 |
| Halts | 20 per seed (DELIBERATION_FAILURE) | 5/5 |
| Repairs attempted | 0 | 5/5 |

**Claim:** Without trace (empty justifications), the agent cannot take any action. Deliberation fails immediately on every episode. This is the "golden test" — complete system collapse from trace removal.

**Mechanism:** Trace excision → empty justifications → no action selectable → DELIBERATION_FAILURE → HALT

---

## 3. Minimality Statement

v4.2 demonstrates that **each of Reflection, Persistence, and Trace is individually necessary** for normative agency under regime contradiction:

| Component | Ablation | Collapse Mode | Success Rate |
|-----------|----------|---------------|--------------|
| Reflection | B | R7 rejection (invalid trace binding) | 5% |
| Persistence | C | R5/R6 rejection (stale epoch) | 10% |
| Trace | D | DELIBERATION_FAILURE (no justifications) | 0% |

The baseline achieves 100% success. Removing any single component causes collapse to ≤10% success. This establishes **constitutive necessity** — these are not optional optimizations but structural requirements for the system to function.

---

## 4. Constitutive Necessity Results

### 4.1 Reflection is Constitutively Necessary

Without Reflection (trace access), the agent cannot:
- Identify which rule blocks progress
- Construct a valid `trace_entry_id` for the repair
- Pass R7 (Trace-Cited Causality) validation

**Result:** 95% halt rate (19/20 episodes per seed)

### 4.2 Persistence is Constitutively Necessary

Without Persistence (norm state continuity), the agent cannot:
- Maintain the epoch chain across episodes
- Cite the correct `prior_repair_epoch` for subsequent repairs
- Pass R5/R6 (Epoch Construction / Anti-Amnesia) validation

**Result:** 90% halt rate (18/20 episodes per seed)

### 4.3 Trace is Constitutively Necessary

Without Trace (justification stream), the agent cannot:
- Generate any action justifications
- Select any action for execution
- Proceed past the first deliberation step

**Result:** 100% halt rate (20/20 episodes per seed)

---

## 5. Scope and Limitations

### 5.1 What v4.2 Claims

1. **Constitutive necessity:** Reflection, Persistence, and Trace are each individually necessary for normative agency under v4.2's regime contradiction environment.

2. **Deterministic collapse:** Each ablation produces deterministic failure modes that are identical across seeds.

3. **Gate-enforced validity:** The Law-Repair Gate (R1-R8) correctly identifies and rejects invalid repairs.

4. **Baseline solvability:** The v4.2 environment is solvable with exactly one repair when all components are intact.

### 5.2 What v4.2 Does NOT Claim

1. **Generalization beyond this environment:** These results are specific to the TriDemand v4.2 environment with PROHIBIT(STAMP) + regime flip. Other environments may have different requirements.

2. **Sufficiency:** v4.2 demonstrates necessity, not sufficiency. Having Reflection, Persistence, and Trace does not guarantee success in all possible environments.

3. **Optimality of the gate design:** R1-R8 is one possible validation scheme. Other schemes might achieve similar results with different mechanisms.

4. **Cognitive claims:** v4.2 makes no claims about consciousness, understanding, or genuine agency. It demonstrates functional requirements for a specific normative task.

5. **Scalability:** Results are for a small discrete environment. Scaling to continuous or high-dimensional environments is untested.

6. **Robustness to adversarial inputs:** v4.2 does not test adversarial scenarios or attempts to exploit the gate.

---

## 6. Artifacts

### 6.1 Result Files

| File | Run Type | Status |
|------|----------|--------|
| `v420_multiseed_baseline_42.json` | LLM Baseline, seed 42 | ✅ PASSED |
| `v420_multiseed_baseline_123.json` | LLM Baseline, seed 123 | ✅ PASSED |
| `v420_multiseed_baseline_456.json` | LLM Baseline, seed 456 | ✅ PASSED |
| `v420_multiseed_baseline_789.json` | LLM Baseline, seed 789 | ✅ PASSED |
| `v420_multiseed_baseline_1000.json` | LLM Baseline, seed 1000 | ✅ PASSED |
| `v420_multiseed_ablation_b_42.json` | Ablation B, seed 42 | ✅ COLLAPSED |
| `v420_multiseed_ablation_b_123.json` | Ablation B, seed 123 | ✅ COLLAPSED |
| `v420_multiseed_ablation_b_456.json` | Ablation B, seed 456 | ✅ COLLAPSED |
| `v420_multiseed_ablation_b_789.json` | Ablation B, seed 789 | ✅ COLLAPSED |
| `v420_multiseed_ablation_b_1000.json` | Ablation B, seed 1000 | ✅ COLLAPSED |
| `v420_multiseed_ablation_c_42.json` | Ablation C, seed 42 | ✅ COLLAPSED |
| `v420_multiseed_ablation_c_123.json` | Ablation C, seed 123 | ✅ COLLAPSED |
| `v420_multiseed_ablation_c_456.json` | Ablation C, seed 456 | ✅ COLLAPSED |
| `v420_multiseed_ablation_c_789.json` | Ablation C, seed 789 | ✅ COLLAPSED |
| `v420_multiseed_ablation_c_1000.json` | Ablation C, seed 1000 | ✅ COLLAPSED |
| `v420_multiseed_ablation_d_42.json` | Ablation D, seed 42 | ✅ COLLAPSED |
| `v420_multiseed_ablation_d_123.json` | Ablation D, seed 123 | ✅ COLLAPSED |
| `v420_multiseed_ablation_d_456.json` | Ablation D, seed 456 | ✅ COLLAPSED |
| `v420_multiseed_ablation_d_789.json` | Ablation D, seed 789 | ✅ COLLAPSED |
| `v420_multiseed_ablation_d_1000.json` | Ablation D, seed 1000 | ✅ COLLAPSED |

### 6.2 Runner Scripts

| File | Purpose |
|------|---------|
| `run_llm_baseline.py` | LLM baseline with full gate telemetry |
| `run_ablation_b.py` | Reflection excision (trace_entry_id=null) |
| `run_ablation_c.py` | Persistence excision (norm_state reset) |
| `run_ablation_d.py` | Trace excision (empty justifications) |

---

## 7. Final Classification

| Run | Classification | Status |
|-----|----------------|--------|
| LLM Baseline (N=5) | `VALID_RUN / LLM_BASELINE_MULTI_SEED / PASSED` | ✅ |
| Ablation B (N=5) | `VALID_RUN / ABLATION_B_MULTI_SEED / COLLAPSE_CONFIRMED` | ✅ |
| Ablation C (N=5) | `VALID_RUN / ABLATION_C_MULTI_SEED / COLLAPSE_CONFIRMED` | ✅ |
| Ablation D (N=5) | `VALID_RUN / ABLATION_D_MULTI_SEED / COLLAPSE_CONFIRMED (GOLDEN TEST)` | ✅ |

---

## 8. Conclusion

RSA-PoC v4.2 is **CLOSED**.

The experimental program demonstrates that under regime contradiction:

1. **Reflection** (trace-cited causality) is required for valid repair construction.
2. **Persistence** (norm state continuity) is required for epoch chain maintenance.
3. **Trace** (justification stream) is required for any action execution.

Each component's removal causes deterministic collapse. The gate telemetry provides objective, reproducible evidence for these claims across 5 independent seeds per condition.

---

**End of v4.2 Closure Note**
