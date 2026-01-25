# Implementor Instructions: RSA-PoC **v3.0 Run AA**

**Non-Reducibility Closure — Prompt-Level Semantic Excision**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.0 (frozen)
**Run ID:** v3.0 **Run AA (Prompt-Level Semantic Excision)**

**Purpose:** Determine whether **semantic affordances during deliberation** are causally indispensable by removing all semantic meaning from the **generator prompt**, forcing the LLM to reason using **opaque symbolic structure only**.

This run answers:

> *Can the agent remain constraint-bound and non-ASB when it cannot read the meaning of the symbols it reasons over?*

**Stop rule:**
If the agent remains meaningfully constrained and non-ASB across seeds, then **semantic meaning is not load-bearing at the deliberation layer**.

---

## 1) Frozen Stack (MUST NOT CHANGE)

Identical to v3.0 Run D baseline:

* Environment: `CommitmentTrapV200`
* Action inventory (<15)
* APCM semantics
* JAF-1.2 unchanged
* Formal Assistant unchanged
* J_raw → J_final immutability
* Selector blind, mask-only
* Deterministic compilation + audits A / B / C / C′
* No SAM; `friction_modifier = 1.0`
* Seed set frozen: **(42, 123, 456, 789, 1024)**
* ASB Null baseline enabled
* Validity gates enabled (no fallback, no compensation, no schema crash)

Any divergence → `INVALID_RUN / HARNESS_MISMATCH`.

---

## 2) What This Run Changes (ONLY THIS)

* `AblationSpec = PROMPT_SEMANTIC_EXCISION`
* Apply **prompt-level ID and descriptor obfuscation before LLM invocation**
* Generator receives **no semantic identifiers or gloss**
* Execution layer performs **structural de-obfuscation only**

No post-hoc artifact rewriting is permitted.

---

## 3) Cost Controls (Binding)

Same phased ladder as Run D.

### Phase 1 — Runtime validation (non-evidentiary)

* seed = 42
* 1 episode, ≤20 steps
* Abort on any `INVALID_RUN/*`, fallback substitution, or crash

### Phase 2 — Pilot (non-evidentiary)

* seed = 42
* 1 episode, 50 steps
* Abort on any `INVALID_RUN/*` or action error rate > 5%

### Phase 3 — Full run (evidentiary)

* 5 seeds × 3 episodes × 50 steps
* No retries beyond preregistered max (recommended: 0)

---

## 4) Run AA Mechanics (Binding)

### 4.1 Where ablation occurs

**Before LLM generation.**

Pipeline:

```
Canonical Prompt
   ↓
PromptSemanticExcisionFilter
   ↓
Obfuscated Prompt
   ↓
LLM (reasons over opaque symbols)
   ↓
J_raw
   ↓
Normal FA / compiler / audits
```

---

### 4.2 What is excised

All semantic meaning in the generator prompt, including:

* action IDs
* preference IDs
* belief / rule identifiers
* comments
* examples
* English gloss or explanation text

---

### 4.3 Mandatory mechanism: deterministic ID bijection

1. Generate deterministic bijection `f` over all agent-visible symbols:

   * `COOPERATE` → `A_001`
   * `DEFECT` → `A_002`
   * `P_NO_DEFECT` → `P_001`
   * etc.

2. Apply `f` to:

   * the **entire generator prompt**
   * any structured input passed to the LLM

3. The LLM **must never see** the original semantic labels.

---

### 4.4 Execution boundary handling

* Compiler and FA remain unchanged.
* Environment execution uses canonical internal action handles.
* A **pure structural adapter** maps:

  ```
  A_001 → internal_action_handle("COOPERATE")
  ```
* No semantic descriptions may re-enter upstream of execution.

---

### 4.5 What must still hold

* No schema crash
* No selector crash
* No fallback substitution
* Constraint checking executes normally

Any technical failure → `INVALID_RUN`, not collapse.

---

## 5) Classification Logic (Binding)

Per seed, classify exactly one:

* `ONTOLOGICAL_COLLAPSE`
* `NARRATIVE_COLLAPSE`
* `ASB_CLASS_REDUCIBILITY`
* `INCENTIVE_CAPTURE`
* `INVALID_RUN`

**Run AA passes** if collapse (any non-INVALID collapse class) occurs **consistently across seeds**.

**Run AA fails** if the system remains:

* strongly constraint-bound, and
* non-ASB (equivalence < 0.85),

despite prompt-level semantic excision.

---

## 6) Telemetry Minimums (Run AA)

### Per step

* hash of obfuscated prompt
* hash of original prompt
* `prompt_semantic_excision_applied = true`
* count of obfuscated symbols
* outcome_mode
* constraint binding metrics
* exception log fields

### Per seed

* ASB equivalence score
* binding ratio vs baseline
* collapse classification

---

## 7) Required Execution Order

For each seed:

1. Baseline run (`AblationSpec = NONE`)
2. Run AA (`PROMPT_SEMANTIC_EXCISION`)
3. ASB Null run

No reordering. No cherry-picking.

---

## 8) Acceptance Criteria (Run AA)

Run AA is **valid** iff:

* 0 `INVALID_RUN` in Phase 3
* no fallback substitution
* determinism respected per seed

Run AA is **successful as an ablation** iff:

* collapse occurs across seeds, and
* collapse is **behavioral**, not syntactic.

---

### Bottom line

Tell Opus to **close Run A cleanly as architectural N/A**, then proceed with **Run AA** as the only experiment that actually tests semantic indispensability at the causal locus.

If you want, next I can:

* draft the **exact closure paragraph** Opus can paste verbatim, or
* help anticipate **expected failure modes** specific to Run AA so interpretation is preregistered.
