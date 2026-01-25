# Implementor Instructions: RSA-PoC **v3.0 Run A**

**Non-Reducibility Closure — Ablation A (Semantic Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.0 (frozen)
**Run ID:** v3.0 **Run A (Semantic Excision)**

**Purpose:** Determine whether **localized semantics are causally indispensable** by excising semantic content from beliefs, preferences, justifications, and identifiers **while preserving structural integrity**, forcing **behavioral collapse**, not syntax failure.

This run answers:

> *If semantic content is removed while referential structure is preserved, does the system cease to function as an agent?*

**Stop rule:**
If Run A fails to collapse (i.e., remains meaningfully constrained and non-ASB), then **semantic localization is not load-bearing**, and ontological claims must be revised.

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

* `AblationSpec = SEMANTIC_EXCISION`
* Apply **SemanticExcisionFilter** **after Formal Assistant** and **before compilation**
* Semantic excision MUST be implemented via **deterministic ID obfuscation with preserved referential integrity** (see §4.4)
* JCOMP300 uses **semantic-field relaxation** (only for ablated text fields, not IDs)

No other changes are permitted.

---

## 3) Cost Controls (Binding)

Use the same phased ladder as Run D.

### Phase 1 — Real runtime validation (non-evidentiary)

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

## 4) Ablation A Mechanics (Binding)

### 4.1 Where excision occurs

* LLM generates **normal** `J_raw`
* Formal Assistant produces **normal** `J_final`
* **SemanticExcisionFilter** transforms `J_final → J_final′`
* Compiler consumes `J_final′`

---

### 4.2 What is excised (payload-level)

Replace semantic payload strings in:

* beliefs
* preferences
* justification / explanation fields

with **opaque tokens**:

* non-descriptive (`TOKEN_###`, `<SEMANTIC_EXCISED_TOKEN_###>`)
* arity, structure, and references preserved

---

### 4.3 What must still hold

* No schema crash
* No selector crash
* No fallback substitution
* Constraint checking still executes
* Run must proceed to behavior, even if behavior degrades or becomes incoherent

**Technical crash = INVALID_RUN**, not collapse.

---

## 4.4 Semantic Excision for ID-Based Systems (Binding)

### 4.4.1 Definition

In Run A, **semantic excision** means:

> Removal of semantic meaning from **all agent-visible identifiers and descriptors** while preserving **structural, referential, and execution integrity**.

This includes:

* action IDs
* preference IDs
* belief / rule identifiers
* any human-readable gloss or descriptor

---

### 4.4.2 Mandatory Design: **ID Bijection + Dual Registries**

#### Goal

Erase semantic meaning from identifiers **without breaking compilation or execution**.

#### Required Mechanism

1. **Generate a deterministic bijection `f` over all agent-visible IDs** in scope:

   * Actions:
     `COOPERATE`, `DEFECT`, … → `A_001`, `A_002`, …
   * Preferences:
     `P_NO_DEFECT`, … → `P_001`, …
   * Beliefs / rules / artifacts similarly if referenced

2. **Apply `f` consistently at two layers**:

   **(a) Post-FA Filter**
   Rewrite all IDs in `J_final` → `J_final′` using `f`.

   **(b) Compiler Registries**
   Replace registry keys with obfuscated IDs:

   * `VALID_ACTIONS_OBF`
   * `VALID_PREFERENCES_OBF`
   * rule registries, etc.

   This is a **lookup-table substitution only**.
   No semantic inference or repair is permitted.

3. **Execution Layer Constraint**

   * Environment MUST execute using **canonical internal action handles**
   * Agent/compiler-visible IDs are opaque labels only

   If execution currently dispatches by string ID, insert a **pure index adapter**:

   ```
   A_001 → internal_action_handle("COOPERATE")
   ```

   This adapter is structural, not semantic, and is allowed.

---

### 4.4.3 Determinism & Audit Requirements

* The bijection `f` MUST be:

  * deterministic,
  * seeded by `(global_seed, ablation_spec, run_id)`,
  * frozen for the entire run

* You MUST log:

  * hash of `f`
  * counts of rewritten IDs by category

* **No semantic leakage is permitted**:

  * no comments
  * no prompt text
  * no metadata
  * no variable names
    may reveal original meanings

If semantic gloss appears anywhere in prompts or artifacts, the run is **INVALID_RUN**.

---

### 4.4.4 Explicitly Disallowed for Run A

The following invalidate Run A:

* Compiler relaxation for unknown IDs
* Registry bypass
* Treating unknown IDs as permissive symbols
* Implicit fallback or best-effort resolution
* Any change that weakens constraint enforcement

These test **registry absence**, not **semantic excision**.

---

## 5) Classification Logic (Binding)

Per seed, classify into exactly one:

* `ONTOLOGICAL_COLLAPSE`
* `NARRATIVE_COLLAPSE`
* `ASB_CLASS_REDUCIBILITY`
* `INCENTIVE_CAPTURE`
* `INVALID_RUN`

**Run A passes** if Phase 3 produces collapse (any non-INVALID collapse class) **consistently across seeds**.

**Run A fails** if the system remains:

* strongly constraint-bound (binding metrics near baseline), and
* non-ASB (equivalence < 0.85),

despite semantic excision.

---

## 6) Telemetry Minimums (Run A)

### Per step

* hashes: `J_raw`, `J_final`, `J_final′`
* `semantic_excision_applied` boolean
* count of replaced payload fields
* count of obfuscated IDs by type
* outcome_mode
* constraint binding metrics
* exception log fields (class / call_site / message)

### Per seed

* ASB equivalence score
* binding ratio (ablated / baseline)
* collapse classification

---

## 7) Required Execution Order

For each seed:

1. Baseline run (`AblationSpec = NONE`)
2. Ablated run (`SEMANTIC_EXCISION`)
3. ASB Null run

No reordering. No cherry-picking.

---

## 8) Acceptance Criteria (Run A)

Run A is **valid** iff:

* 0 `INVALID_RUN` in Phase 3
* no fallback substitution
* determinism respected per seed

Run A is **successful as an ablation** iff:

* collapse occurs across seeds (consistent classification), and
* collapse is **behavioral** (binding loss / incoherence), not syntactic.
