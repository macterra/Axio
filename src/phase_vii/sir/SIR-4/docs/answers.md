# **Principal Rulings: SIR-4 v0.1**

**Status:** FINAL
**Effect:** Unblocks preregistration and implementation

---

## Q1: Maximum Declared Load — Concrete Value

**Ruling:** **B) 500 bundles per step**

**Justification:**
500 is sufficient to force evaluator pressure, queue engagement, and failure-order stress without turning SIR-4 into a resource exhaustion exercise. SIR-4 tests **structural integrity under pressure**, not hardware limits. Higher values add noise, not signal.

**Binding:**
*Maximum declared load for Condition F is fixed at 500 bundles per step.*

---

## Q2: Queue Policy Selection

**Ruling:** **A) Ingress Filtering Before Queue**

**Justification:**
Ingress filtering preserves the clean architectural invariant established in SIR-0–3: *invalid authority never consumes privileged resources*. Priority queues introduce unnecessary displacement complexity and obscure auditability.

**Binding:**
*Invalid and malformed bundles must be refused prior to queue admission.*

---

## Q3: Failure Ordering — Preregistered Sequence

**Ruling:** **APPROVED AS WRITTEN**

```
1. MALFORMED_STRUCTURE
2. MISSING_REQUIRED_FIELD
3. WRONG_TYPE
4. SIGNATURE_INVALID
5. ISSUER_UNKNOWN
6. SCOPE_MISMATCH
7. EXPIRED_CREDENTIAL
8. REVOKED_CREDENTIAL
```

**Justification:**
This ordering is deterministic, total, and aligned with the fixed validation pipeline. Early structural rejection is correct and cost-orthogonal. No reordering is permitted.

**Binding:**
*This sequence is frozen for SIR-4 v0.1.*

---

## Q4: Condition-Specific Bundle Ratios

**Ruling:** **APPROVED AS PROPOSED**

| Condition | Valid | Invalid | Malformed |
| --------- | ----- | ------- | --------- |
| A         | 95%   | 5%      | 0%        |
| B         | 5%    | 95%     | 0%        |
| C         | 5%    | 0%      | 95%       |
| D         | 0%    | 100%*   | 0%        |
| E         | 5%    | 95%**   | 0%        |
| F         | 10%   | 45%     | 45%       |

* multi-failure engineered
** edge-case crafted

**Justification:**
Ratios exercise all declared hazards while preserving at least one valid bundle where required for non-starvation checks.

---

## Q5: Harness Implementation — Deterministic Injection

**Ruling:** **A) Batch injection at step start**

**Justification:**
Batch semantics align exactly with the evaluator load metric (“cardinality per step”) and simplify auditability. Streaming introduces temporal ambiguity without adding structural insight.

**Binding:**
*All N bundles are injected at the beginning of each logical step.*

---

## Q6: Reuse of SIR-3 Provenance Infrastructure

**Ruling:** **CONFIRMED (All three points)**

1. Import SIR-3 provenance module unchanged
2. Log provenance chains for all bundle classifications
3. Extend logs with evaluator load context

**Justification:**
SIR-4 stresses the evaluator, not provenance semantics. Any modification to provenance logic invalidates inheritance.

---

## Q7: “Exception Induction” Bundle Types (Condition E)

**Ruling:** **ALL LISTED CATEGORIES INCLUDED**

Approved categories:

1. Oversized bundles
2. Null / empty fields
3. Unicode edge cases
4. Deeply nested / recursive structures
5. Boundary values
6. Duplicate fields

**Constraint:**
These must be handled **structurally**, not via sanitization heuristics or semantic normalization.

---

## Q8: Run Matrix Composition

**Ruling:** **APPROVED AS PROPOSED**

| Run | Condition | Load | Seeds |
| --- | --------- | ---- | ----- |
| 1   | A         | 50   | 3     |
| 2   | B         | 500  | 3     |
| 3   | C         | 500  | 3     |
| 4   | D         | 200  | 3     |
| 5   | E         | 200  | 3     |
| 6   | F         | 500  | 5     |

**Total:** 20 runs

**Justification:**
Seed count is sufficient to expose nondeterminism without drifting into statistical testing.

---

## Q9: Non-Blocking Refusal Implementation

**Ruling:** **B) Synchronous logging required**

**Justification:**
Auditability overrides throughput. Refusal is a first-class sovereign act and must be causally ordered with classification.

**Binding:**
*If refusal logging blocks progress, that is evaluator collapse, not a logging optimization opportunity.*

---

## Q10: Evaluator Collapse Definition

**Ruling:** **APPROVED + ONE ADDITION**

Evaluator collapse includes:

1. Unhandled exception
2. Timeout exceeding step limit
3. Memory exhaustion
4. Infinite loop detection
5. No classification output

**Additional collapse mode:**

6. **Acceptance or effect emission without a prior classification record**

This captures silent fail-open behavior.

---

# **Principal Rulings: SIR-4 v0.1 — Follow-Ups (Q11–Q18)**

**Status:** FINAL
**Effect:** Unblocks implementation and preregistration completion

---

## Q11: Step Time Limit for Timeout Detection

**Ruling:** **B) 5 seconds per step**

**Justification:**
SIR-4 is not a performance benchmark, but collapse detection must be real. 5 seconds is long enough for 500-bundle batch processing in a normal environment while still detecting hangs and pathological stalls.

**Binding:**
*Evaluator step timeout threshold is 5.0 seconds wall-clock per logical step.*

---

## Q12: Memory Exhaustion Threshold

**Ruling:** **B) Allocator raises OOM exception**

**Justification:**
Fixed RSS limits create machine-dependent false failures. Proactive checks are heuristics. The structural signal is “allocation fails.”

**Binding:**
*Memory exhaustion is detected when the evaluator process raises an OOM / allocation-failure exception, which constitutes evaluator collapse.*

---

## Q13: Acceptance-Without-Classification Detection

**Ruling:** **C) Both A and B (defense in depth)**

**Justification:**
Inline gating is the structural guarantee. Post-step audit is the integrity witness that catches any bypass.

**Binding:**

1. *Effect emission is blocked unless accompanied by a classification token produced earlier in the pipeline.*
2. *Post-step audit must verify that every effect has exactly one prior classification record and causal author bundle.*

Violation triggers:

```
SIR_FAIL / EVALUATOR_COLLAPSE
```

---

## Q14: Infinite Loop Detection Mechanism

**Ruling:** **C) Both iteration limit and timeout**

**Justification:**
Iteration caps catch tight loops; timeout catches slow non-terminating paths. Both are structural and deterministic.

**Binding:**
*Set a hard per-step evaluator iteration cap of 10,000 internal iterations (or equivalent loop ticks) in addition to the 5-second timeout.*

Exceeding either threshold triggers:

```
SIR_FAIL / EVALUATOR_COLLAPSE
```

---

## Q15: Unicode Edge Case — Specific Handling

**Ruling:** **APPROVED AS STATED (1–3 all true)**

**Binding interpretation:**

1. Bundles containing invalid/unsafe Unicode encodings or forbidden codepoint patterns are classified as:

```
MALFORMED_STRUCTURE
```

2. No Unicode normalization, sanitization, or “repair” is applied.
3. Raw bytes (or exact original encoding representation) must be preserved in logs for audit.

---

## Q16: Duplicate Fields — First vs Last Wins

**Ruling:** **A) Trigger `MALFORMED_STRUCTURE` refusal**

**Justification:**
First-wins/last-wins is parser-dependent behavior and creates ambiguity vectors. Structural rejection is the correct sovereign posture.

**Binding:**
*Any duplicate field occurrence in a bundle yields MALFORMED_STRUCTURE under the first-failure rule.*

---

## Q17: Seed Selection for Reproducibility

**Ruling:** **A) Sequential seeds (1, 2, 3, …)**

**Binding:**
Use sequential seeds per condition:

* 3-seed conditions: **[1, 2, 3]**
* 5-seed condition (F): **[1, 2, 3, 4, 5]**

No additional seeds are permitted under v0.1.

---

## Q18: Evaluator Load Context in Provenance Logs

**Ruling:** **APPROVED WITH ONE CHANGE**

Approved fields, with the following constraint:

*The per-bundle log must include the step totals and the bundle index.*
*The “so far this step” counters are permitted but must not affect behavior and must not be used as gating inputs.*

**Binding required structure:**

```yaml
evaluator_load:
  step_id: <int>
  bundle_count: <int>        # total bundles injected this step
  bundle_index: <int>        # this bundle's deterministic position (0..N-1)
  valid_count_so_far: <int>  # optional diagnostic
  invalid_count_so_far: <int># optional diagnostic
  malformed_count_so_far: <int># optional diagnostic
```

**Constraint:**
Counts are **diagnostic only**. Any policy that branches on these counters is an invalid adaptive heuristic.

Violation yields:

```
INVALID_RUN / ADAPTIVE_PRESSURE_HANDLING
```

---
