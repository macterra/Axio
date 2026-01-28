# SIR-4 v0.1 Implementation Questions

**Status:** PENDING_PRINCIPAL_RULING
**Date:** 2026-01-17
**Context:** Pre-implementation clarification for Evaluator Pressure, Flooding, and Ambiguity Resistance

---

## Q1: Maximum Declared Load — Concrete Value

**Reference:** spec.md § "Evaluator Load Metric", § "Condition F — Maximum Mixed Stress"

The spec requires:
- Evaluator load logged per step as cardinality of bundles
- Maximum declared load for Condition F

**Question:** What is the maximum declared load for SIR-4 experimental runs?

**Options:**
- A) 100 bundles per step (moderate stress)
- B) 500 bundles per step (high stress)
- C) 1000 bundles per step (extreme stress)
- D) Principal specifies different value

**Recommendation:** Option B (500) provides meaningful pressure while remaining tractable for logging and analysis.

**Ruling:** ___

---

## Q2: Queue Policy Selection

**Reference:** spec.md § "Queue Admissibility and Priority Discipline"

The spec permits exactly one of:
- **A) Ingress Filtering Before Queue** — invalid/malformed bundles refused before consuming queue capacity
- **B) Priority or Displacing Queue** — valid bundles have strict priority, including displacement

**Question:** Which queue policy should SIR-4 implement and test?

**Recommendation:** Option A (Ingress Filtering) is simpler, matches the existing reject-early architecture from SIR-0–3, and avoids displacement complexity.

**Ruling:** ___

---

## Q3: Failure Ordering — Preregistered Sequence

**Reference:** spec.md § "Failure Ordering Discipline"

The spec requires a fixed, total, preregistered ordering of failure checks for bundles that fail multiple global checks simultaneously.

**Question:** Confirm the following failure check ordering is acceptable:

```
1. MALFORMED_STRUCTURE (parse fails)
2. MISSING_REQUIRED_FIELD (required fields absent)
3. WRONG_TYPE (type mismatch)
4. SIGNATURE_INVALID (cryptographic verification fails)
5. ISSUER_UNKNOWN (issuer not in trust registry)
6. SCOPE_MISMATCH (requested effect outside granted scope)
7. EXPIRED_CREDENTIAL (temporal validity exceeded)
8. REVOKED_CREDENTIAL (on revocation list)
```

**Rationale:** This ordering prioritizes structural failures (cheap, early) before cryptographic and semantic checks (expensive, later).

**Ruling:** ___

---

## Q4: Condition-Specific Bundle Ratios

**Reference:** spec.md § Experimental Conditions B–F

**Question:** For conditions involving mixed bundles, what ratios should be used?

**Proposed Ratios:**

| Condition | Valid | Invalid | Malformed |
|-----------|-------|---------|-----------|
| A: Baseline Load Control | 95% | 5% | 0% |
| B: Invalid Flood | 5% | 95% | 0% |
| C: Malformed Flood | 5% | 0% | 95% |
| D: Multi-Failure Ambiguity Storm | 0% | 100%* | 0% |
| E: Exception Induction Attempts | 5% | 95%** | 0% |
| F: Maximum Mixed Stress | 10% | 45% | 45% |

*Condition D: Invalid bundles engineered to fail multiple checks simultaneously
**Condition E: Invalid bundles specifically crafted to probe edge cases

**Ruling:** ___

---

## Q5: Harness Implementation — Deterministic Injection

**Reference:** spec.md § "Pressure Harness (New)"

The spec requires deterministic injection of N bundles per step with deterministic arrival order by seed.

**Question:** Should the harness:

- A) Inject all N bundles at the **start** of each step (batch injection), or
- B) Inject bundles **interleaved** with legitimate execution across the step (streaming injection)?

**Recommendation:** Option A (batch injection) is simpler to implement and analyze. The spec's evaluator load metric ("cardinality of bundles per step") suggests batch semantics.

**Ruling:** ___

---

## Q6: Reuse of SIR-3 Provenance Infrastructure

**Reference:** spec.md § "Inherited Architecture", instructions.md § "Binding Dependencies"

SIR-4 inherits global provenance integrity from SIR-3.

**Question:** Confirm that SIR-4 should:

1. Import the SIR-3 provenance module unchanged
2. Log provenance chains for all bundle classifications
3. Extend provenance logging to include evaluator load context

**Ruling:** ___

---

## Q7: "Exception Induction" Bundle Types (Condition E)

**Reference:** spec.md § "Condition E — Exception Induction Attempts"

The spec references "bundles crafted to trigger edge cases or exceptions" without enumerating specific types.

**Question:** Should Condition E include the following exception induction categories?

1. **Oversized bundles** — exceeding expected field lengths
2. **Null/empty fields** — fields present but empty
3. **Unicode edge cases** — homoglyphs, RTL override, zero-width chars
4. **Nested structures** — deeply nested or recursive structures
5. **Boundary values** — timestamps at epoch, max int, etc.
6. **Duplicate fields** — same field appearing multiple times

**Ruling:** ___

---

## Q8: Run Matrix Composition

**Reference:** instructions.md § "Experimental Conditions"

**Question:** Confirm the run matrix structure:

| Run | Condition | Load | Seeds |
|-----|-----------|------|-------|
| 1 | A: Baseline | Low (50) | 3 seeds |
| 2 | B: Invalid Flood | High (500) | 3 seeds |
| 3 | C: Malformed Flood | High (500) | 3 seeds |
| 4 | D: Ambiguity Storm | Medium (200) | 3 seeds |
| 5 | E: Exception Induction | Medium (200) | 3 seeds |
| 6 | F: Maximum Stress | Max (500) | 5 seeds |

Total: 20 runs across 6 conditions

**Ruling:** ___

---

## Q9: Non-Blocking Refusal Implementation

**Reference:** spec.md § "Non-Blocking Refusal Semantics"

The spec requires refusals to be non-blocking: "Refusal must emit a classified record and terminate the claim. It must not block the episode, halt the evaluator, or degrade subsequent claims."

**Question:** Under maximum load (Condition F), if refusal logging itself becomes a bottleneck, is it acceptable to:

- A) Buffer refusals and flush asynchronously (maintaining ordering), or
- B) Refusals must be synchronously logged before proceeding (strict sequencing)?

**Recommendation:** Option B (synchronous) preserves the clearest audit trail but may limit throughput. Option A risks log ordering issues.

**Ruling:** ___

---

## Q10: Evaluator Collapse Definition

**Reference:** spec.md § "Failure Criteria"

`SIR_FAIL / EVALUATOR_COLLAPSE` is listed but not explicitly defined.

**Question:** Confirm evaluator collapse includes:

1. Unhandled exception in evaluator code
2. Evaluator timeout (exceeds step time limit)
3. Memory exhaustion
4. Infinite loop detection
5. Evaluator returns no classification for any bundle

Are there additional collapse modes to enumerate?

**Ruling:** ___

---

## Summary

10 questions requiring principal ruling before SIR-4 implementation can proceed.

**Blocking:** Q1, Q2, Q3, Q4, Q5, Q8 (core experimental design)
**Clarifying:** Q6, Q7, Q9, Q10 (implementation details)

**Status Update:** All 10 questions answered — see [answers.md](answers.md)

---

# Follow-Up Questions

**Status:** PENDING_PRINCIPAL_RULING  
**Date:** 2026-01-28  
**Context:** Clarifications arising from principal rulings

---

## Q11: Step Time Limit for Timeout Detection

**Reference:** answers.md Q10 ruling — "Timeout exceeding step limit"

The collapse definition includes timeout, but no concrete step time limit is specified.

**Question:** What is the maximum allowed step duration before timeout triggers evaluator collapse?

**Options:**
- A) 1 second per step
- B) 5 seconds per step
- C) 10 seconds per step
- D) Principal specifies different value

**Recommendation:** Option B (5 seconds) allows meaningful processing of 500 bundles while catching genuine stalls.

**Ruling:** ___

---

## Q12: Memory Exhaustion Threshold

**Reference:** answers.md Q10 ruling — "Memory exhaustion"

Memory exhaustion is a collapse mode, but no threshold is defined.

**Question:** How should memory exhaustion be detected?

**Options:**
- A) Process memory exceeds fixed limit (e.g., 1GB)
- B) Allocator raises OOM exception
- C) Evaluator pre-checks available memory before step
- D) No proactive limit — rely on OS OOM behavior

**Recommendation:** Option B (allocator exception) is cleanest — structural failure on actual exhaustion rather than arbitrary limits.

**Ruling:** ___

---

## Q13: Acceptance-Without-Classification Detection

**Reference:** answers.md Q10 ruling — additional collapse mode "Acceptance or effect emission without a prior classification record"

**Question:** How should this be verified?

**Options:**
- A) Post-step audit: compare effect log against classification log
- B) Inline assertion: effect emission blocked without classification token
- C) Both A and B (defense in depth)

**Recommendation:** Option C — inline blocking is the structural guarantee; post-audit confirms no bypass.

**Ruling:** ___

---

## Q14: Infinite Loop Detection Mechanism

**Reference:** answers.md Q10 ruling — "Infinite loop detection"

**Question:** How should infinite loops be detected?

**Options:**
- A) Step iteration counter with declared maximum (e.g., 10,000 iterations)
- B) Rely solely on step timeout (Q11)
- C) Both iteration limit and timeout

**Recommendation:** Option C — iteration limit catches tight loops quickly; timeout catches slow infinite loops.

**Ruling:** ___

---

## Q15: Unicode Edge Case — Specific Handling

**Reference:** answers.md Q7 ruling — "Unicode edge cases" with constraint "handled structurally, not via sanitization heuristics"

**Question:** Confirm structural handling means:

1. Bundles with problematic Unicode are classified as `MALFORMED_STRUCTURE` (first failure check)
2. No Unicode normalization or sanitization is applied
3. Raw bytes are preserved in logs for audit

**Ruling:** ___

---

## Q16: Duplicate Fields — First vs Last Wins

**Reference:** answers.md Q7 ruling — "Duplicate fields"

When a bundle contains duplicate fields, parsers typically use first-wins or last-wins semantics.

**Question:** For SIR-4, should duplicate fields:

- A) Trigger `MALFORMED_STRUCTURE` refusal (no parsing of duplicates)
- B) Use first-wins semantics (second occurrence ignored)
- C) Use last-wins semantics (first occurrence overwritten)

**Recommendation:** Option A — structural rejection is cleanest and avoids parser-dependent behavior.

**Ruling:** ___

---

## Q17: Seed Selection for Reproducibility

**Reference:** answers.md Q5, Q8 rulings — deterministic injection with 3-5 seeds per condition

**Question:** Should seeds be:

- A) Sequential (1, 2, 3, ...)
- B) Fixed arbitrary values (e.g., 42, 1337, 31415)
- C) Derived from condition hash (deterministic but condition-specific)

**Recommendation:** Option A — simplest and fully reproducible.

**Ruling:** ___

---

## Q18: Evaluator Load Context in Provenance Logs

**Reference:** answers.md Q6 ruling — "Extend logs with evaluator load context"

**Question:** What evaluator load context should be logged with each classification?

**Proposed fields:**
```
evaluator_load: {
  step_id: <int>,
  bundle_count: <int>,        # total bundles this step
  bundle_index: <int>,        # this bundle's position in step
  valid_count: <int>,         # valid bundles so far this step
  invalid_count: <int>,       # invalid bundles so far this step
  malformed_count: <int>      # malformed bundles so far this step
}
```

**Ruling:** ___

---

## Summary

8 follow-up questions arising from principal rulings.

**Blocking:** Q11, Q14 (collapse detection parameters)  
**Clarifying:** Q12, Q13, Q15, Q16, Q17, Q18 (implementation specifics)

---

**End of Questions Document**
