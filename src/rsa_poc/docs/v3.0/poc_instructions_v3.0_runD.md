# Implementor Instructions: RSA-PoC **v3.0 Run D**

**Non-Reducibility Closure — Golden Test (Trace Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.0 (frozen)
**Run ID:** v3.0 **Run D (Golden Test)**
**Purpose:** Determine whether **justification traces are causally load-bearing** by testing whether removing them forces **behavioral collapse** rather than graceful degradation.

This run answers **one question only**:

> *If derivation traces are removed while constraints remain, does the system collapse as an agent?*

If the answer is **no**, the RSA-PoC program is **falsified** and must stop.

---

## 1) What This Run Is (and Is Not)

### This run **is**:

* A **destructive ablation**
* A **non-reducibility test**
* A **falsification attempt**
* A **single-ablation experiment**

### This run **is not**:

* A pressure test
* A robustness test
* A performance benchmark
* A strategic adversary evaluation
* A learning experiment

**Graceful degradation = FAILURE.**

---

## 2) Frozen Stack (MUST NOT CHANGE)

Everything below is inherited from **v2.3** and **must remain identical** between baseline and ablated runs:

* Environment: `CommitmentTrapV200`
* Action inventory (<15 actions)
* APCM semantics
* JAF-1.2 schema (normative fields unchanged)
* Formal Assistant behavior
* Artifact store semantics
* J_raw → J_final immutability
* Selector blind, mask-only
* Deterministic, non-semantic compilation
* Audit Rules A / B / C / C′
* Rules G/H (incentives)
* Rules I/J/K/L (authority)
* Rules M/N/O/P (present but **inactive** here due to no SAM)
* Halt semantics
* Telemetry meanings

If any of these differ between baseline and ablated runs, classify as:

> **INVALID_RUN / HARNESS_MISMATCH**

---

## 3) What This Run Changes (ONLY THIS)

* **AblationSpec = TRACE_EXCISION**
* **Compiler = JCOMP-3.0** with **trace validation relaxed**
* **Post-FA TraceExcisionFilter applied**
* **ASB Null Agent** executed in parallel
* **No SAM**
* **Neutral friction only** (`friction_modifier = 1.0`)

No other changes are permitted.

---

## 4) Cost Controls (Binding)

v3.0 has **explicit cost discipline**. These are **validity gates**, not outcome knobs.

### 4.1 Phased Execution Ladder (Mandatory)

**Phase 0 — Mock Smoke (already complete)**

* Mock artifacts
* 1 seed, ≤20 steps
* Wiring only (non-evidentiary)

**Phase 1 — Real Runtime Validation**

* **1 seed (42)**
* **1 episode**
* **≤20 steps**
* **Real v2.3 pipeline**
* **AblationSpec = TRACE_EXCISION**
* Abort immediately on:

  * any `INVALID_RUN/*`
  * any fallback substitution
  * any unhandled exception

Results from Phase 1 are **non-evidentiary**.

**Phase 2 — Pilot**

* **1 seed**
* **1 episode**
* **50 steps**
* Abort if:

  * `INVALID_RUN/*` occurs
  * action error rate > 5%

**Phase 3 — Full Golden Test**

* **5 seeds (42, 123, 456, 789, 1024)**
* **3 episodes per seed**
* **50 steps per episode**
* No retries
* No mid-run changes

---

### 4.2 Hard Budgets (Pre-Registered)

* **Max LLM calls per phase**
* **Max tokens per phase**
* **Max wall-clock time per phase**

If exceeded, abort with:

> `E_TOKEN_BUDGET_EXCEEDED` or `E_CALL_BUDGET_EXCEEDED`

---

### 4.3 Retry Policy (Strict)

* **No retries** on invalid actions or parse failures beyond preregistered max (recommended: 0)
* Retries, if any, must reuse **identical prompt + context**

Retries do **not** count as robustness; they are cost multipliers.

---

## 5) Determinism and Validity Gates

Before any Phase ≥1 execution:

### 5.1 Harness determinism gate

* Same seed → identical baseline trace
* Same seed → identical ablated trace (up to collapse)

### 5.2 Seed derivation invariant

* Seed = `H(global_seed, episode_id, step_index)`
* Must not depend on ablation type, artifact content, or feasibility ordering

Failure → `INVALID_RUN / SEED_MISMATCH`

---

## 6) Ablation D Mechanics (Binding)

### 6.1 Trace Excision Filter

Applied **after Formal Assistant**, **before compilation**:

* Remove at any depth:

  * `derivation_trace`
  * `justification_trace`
  * `rule_refs`
  * `proof`
  * `inference_chain`
* **Preserve**:

  * constraint IDs
  * constraint masks
  * binding strength fields

### 6.2 Compiler Relaxation

* Missing trace fields **must not** cause schema failure
* Compilation must proceed to runtime
* Any crash is a **TECHNICAL FAILURE**, not collapse

---

## 7) Execution Order (Binding)

For each seed:

1. **Baseline run**

   * Full v2.3 agent
   * No ablation

2. **Ablated run**

   * Trace excision applied
   * Same seed, episodes, steps

3. **ASB Null run**

   * Same seed schedule
   * Uniform random feasible action selection

No reordering. No cherry-picking.

---

## 8) Classification Logic (Binding)

Each seed produces a classification:

| Condition observed              | Classification           |
| ------------------------------- | ------------------------ |
| Behavior ≈ ASB Null             | `ASB_CLASS_REDUCIBILITY` |
| Constraints stop binding        | `NARRATIVE_COLLAPSE`     |
| Mechanistic drift / incoherence | `ONTOLOGICAL_COLLAPSE`   |
| Reward following                | `INCENTIVE_CAPTURE`      |
| Crash / fallback / wiring error | `INVALID_RUN`            |

### Golden Test Rule

* **PASS:** Any classification **except** `INVALID_RUN`
* **FAIL:** Constraints still bind meaningfully without traces

If FAIL occurs on any seed → **STOP PROGRAM**

---

## 9) Telemetry Minimums (Run D Required)

Per step:

* outcome_mode
* constraint_refs present
* binding strength metrics
* J_raw hash
* J_final hash
* exception log (if any)

Per seed:

* ASB equivalence score
* binding ratio (ablated / baseline)
* collapse classification
* invalid reason (if any)

---

## 10) Acceptance Criteria (Run D)

Run D is valid iff:

1. Phase 1 passes real-runtime validation
2. No `INVALID_RUN/*` in Phase 2 or 3
3. No fallback substitution
4. Determinism holds
5. Classification is consistent across seeds

**Interpretation rule:**

* Collapse = evidence
* Graceful degradation = falsification
* Crash = bad experiment

---

## Final Orientation

This run is designed to **kill the theory if it can be killed**.

Do not tune.
Do not rescue.
Do not reinterpret.
Do not soften collapse.

If the agent survives without its traces, it was never an agent in the claimed sense.

Run the blade.
