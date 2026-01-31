# Axionic Agency X.2 — Authority Kernel Runtime Calibration (AKR-0)

*A Structural Demonstration of Executable Authority Without Semantics*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.31

## Abstract

This technical note reports the completed results of **Authority Kernel Runtime Calibration (AKR-0)**, a preregistered experimental program within **Axionic Phase VIII** that evaluates whether **authority-constrained execution** is mechanically realizable without semantic interpretation, optimization, or fallback behavior. AKR-0 isolates the execution substrate beneath governance and tests whether a deterministic kernel can (i) execute actions only when explicitly authorized, (ii) refuse inadmissible actions without degradation, (iii) register and enforce structural conflicts, and (iv) recognize deadlock as a terminal diagnostic outcome. Across fifteen preregistered runs spanning valid authority, authority absence, and conflict saturation regimes, all executions were deterministic, auditable, and bit-perfectly replayable. The results establish that authority can be executed as **structure**, not narrative. AKR-0 makes no claims about governance success, stability, alignment, or desirability; those questions are deferred to subsequent Phase VIII experiments.

## 1. Problem Definition

### 1.1 The Executability Gap

Most discussions of governance, alignment, or authority implicitly assume that *execution* is trivial once rules are defined. In practice, many systems silently rely on heuristics, semantic interpretation, or “best effort” behavior when authority is absent, ambiguous, or conflicting.

AKR-0 removes that assumption.

The problem AKR-0 isolates is whether **authority can be executed at all** as a purely mechanical constraint—without an agent, without interpretation, and without rescue logic. If authority requires semantic reasoning or optimization to be enforced, then governance claims collapse into narrative descriptions rather than executable structure.

AKR-0 treats authority as a **state-bound admissibility relation**, not as a goal, preference, or policy, and tests whether that relation can be enforced deterministically under stress.

### 1.2 Failure Modes Targeted

AKR-0 is designed to surface the following execution-level failure modes:

* **Ungated execution:** actions occur without explicit authority.
* **Fail-open behavior:** inadmissible actions are executed “by default.”
* **Heuristic arbitration:** conflicts are resolved implicitly or preferentially.
* **Semantic fallback:** execution proceeds based on inferred intent or utility.
* **Non-determinism:** identical inputs yield divergent outcomes.
* **Deadlock evasion:** systems continue acting after authority exhaustion.

Any of these constitutes AKR-0 failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Semantics (Frozen)

AKR-0 inherits, without reinterpretation, the semantics fixed by:

* **AST Spec v0.2** (Authority State Transformation),
* **AIE v0.1** (Authority Input Environment),
* and the Phase VIII Execution Addendum.

Authority is structural, scopes are atomic, conflicts are destructive, and authority creation is external. AKR-0 does **not** test whether these definitions are correct; it tests whether they are *executable*.

### 2.2 Explicit Exclusions

AKR-0 does **not** test:

* governance effectiveness,
* coordination or convergence,
* robustness under adversarial deception,
* strategic planning,
* long-horizon survivability,
* alignment or safety.

Those hazards are intentionally excluded. AKR-0 is a calibration gate, not a governance experiment.

## 3. Conserved Quantity

The conserved quantity throughout AKR-0 is:

> **Authority-constrained admissibility under deterministic execution**

Authority is neither a score nor an emergent pattern. It is a **binary structural condition**: an action is either admissible or it is not, given the Authority State.

The kernel must:

* execute **only** admissible actions,
* refuse inadmissible actions without escalation,
* preserve state under refusal,
* and halt honestly when no admissible path remains.

No semantic interpretation is permitted to “improve” outcomes.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

AKR-0 was preregistered in full prior to implementation, including:

* frozen specifications,
* closed schemas,
* fixed PRNG and seeds,
* deterministic gas budgets,
* canonical ordering rules,
* explicit failure taxonomies.

All 15 runs were executed without deviation. Any divergence would have yielded `INVALID_RUN`.

### 4.2 Execution Architecture

Each run consisted of three strictly partitioned components:

1. **AIE** — injected authority records only.
2. **Execution Harness** — generated candidate actions and transformation requests.
3. **AKR-0 Kernel** — enforced admissibility, conflict blocking, refusal, and deadlock.

No component had access to semantic information or outcome desirability.

## 5. Experiment Ladder and Conditions

### 5.1 Condition A — Valid Authority (Positive Control)

**Purpose:** Verify lawful execution under valid authority.

**Result:**
Actions executed **only** when holder and scope matched an ACTIVE authority. All other actions were refused deterministically. Conflicts were registered and blocked execution without arbitration.

**Classification:** PASS.

### 5.2 Condition B — Authority Absence (Negative Control)

**Purpose:** Test refusal and deadlock under zero authority.

**Result:**
All actions were refused. **ENTROPIC_COLLAPSE** was detected at epoch 1, terminating each run immediately. Final Authority State hashes were identical across all seeds, confirming deterministic empty-state termination.

**Classification:** PASS.

### 5.3 Condition C — Conflict Saturation

**Purpose:** Stress conflict detection and blocking.

**Method:**
High conflict density was guaranteed via deterministic hot-scope pairing.

**Result:**
Thousands of conflicts were registered. Execution rates dropped below 1%. No conflict was arbitrated, no semantic fallback occurred, and no nondeterminism was observed. Despite saturation, the kernel remained live until termination conditions were met.

**Classification:** PASS.

## 6. Core Results

### 6.1 Positive Results

Across all conditions and seeds, AKR-0 establishes that:

1. Authority gating is **deterministically enforceable**.
2. Refusal is a **stable, first-class outcome**.
3. Conflict can be **represented and enforced** without resolution.
4. Deadlock can be **detected and classified** mechanically.
5. Execution is **bit-perfectly replayable** under canonical ordering.
6. No semantic or heuristic logic is required at runtime.

### 6.2 Negative Results (Explicit)

AKR-0 does **not** establish:

* that governance succeeds,
* that coordination emerges,
* that authority persists long-term,
* that execution is efficient or useful.

These are not omissions; they are boundary conditions.

## 7. Failure Semantics and Closure

### 7.1 Closure Criteria

AKR-0 closes positive if and only if:

1. No ungated execution occurs.
2. All inadmissible actions are refused.
3. Conflicts block execution deterministically.
4. Deadlock is detected without recovery logic.
5. Replay is bit-perfect across all runs.

All criteria were satisfied.

### 7.2 AKR-0 Closure Status

**AKR-0 Status:** **CLOSED — POSITIVE**
(`AKR0_PASS / AUTHORITY_EXECUTION_ESTABLISHED`)

## 8. Boundary Conditions and Deferred Hazards

### 8.1 Governance vs Execution

AKR-0 establishes **executability**, not governance viability. A system that refuses everything is still a valid AKR-0 system.

### 8.2 Interface to Subsequent Phase VIII Work

AKR-0 removes the “execution substrate” objection. Subsequent experiments may now legitimately ask:

* whether authority survives pressure,
* whether transformations enable governance,
* whether coordination is possible.

Those questions were ill-posed before AKR-0.

## 9. Implications (Strictly Limited)

AKR-0 establishes a **necessary condition** for governance: that authority can be enforced without semantics. It does not establish sufficiency.

Authority is now a **mechanically testable property**, not a narrative assumption.

## 10. Conclusion

AKR-0 demonstrates that authority can be executed as **structure**, not story. Actions can be gated, refused, blocked, and halted deterministically without interpretation, optimization, or rescue behavior.

The remaining question is not whether authority can run, but whether it can *govern*.

That question belongs to the next phase.

## Appendix A — Experiment Status

| Condition | Runs | Status |
| --------- | ---- | ------ |
| A         | 5    | PASS   |
| B         | 5    | PASS   |
| C         | 5    | PASS   |

## Appendix B — Determinism Verification

* Canonical ordering enforced
* Deterministic gas accounting
* Per-event hash chaining
* 15/15 replay verifications passed

**End of Axionic Agency IX.3 — AKR-0 Results Note**
