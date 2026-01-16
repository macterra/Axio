# Implementor Instructions: RSA-PoC **v3.0 Run A**

**Non-Reducibility Closure — Ablation A (Semantic Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.0 (frozen)
**Run ID:** v3.0 **Run A (Semantic Excision)**
**Purpose:** Determine whether **localized semantics are causally indispensable** by removing semantic payloads while preserving IDs/structure and forcing **behavioral collapse**, not syntax failure.

This run answers:

> *If semantics are excised from beliefs/preferences/justification payloads, does the system collapse as an agent?*

**Stop rule:** If Run A fails to collapse (i.e., remains meaningfully constrained and non-ASB), the “semantic localization” component is **not load-bearing** and ontological claims must be revised.

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
* Deterministic compilation + audits A/B/C/C′
* No SAM; `friction_modifier = 1.0`
* Seed set frozen: **(42, 123, 456, 789, 1024)**
* ASB Null baseline enabled
* Validity gates enabled (no fallback, no compensation, no schema crash)

Any divergence → `INVALID_RUN / HARNESS_MISMATCH`.

---

## 2) What This Run Changes (ONLY THIS)

* `AblationSpec = SEMANTIC_EXCISION`
* Apply **SemanticExcisionFilter** **after FA** and **before compilation**
* JCOMP300 uses **semantic-field relaxation** (only for ablated fields)

No other changes.

---

## 3) Cost Controls (Binding)

Use the same phased ladder you used for Run D.

### Phase 1 — Real runtime validation (non-evidentiary)

* seed=42, 1 episode, ≤20 steps
* Abort on any `INVALID_RUN/*`, fallback substitution, crash

### Phase 2 — Pilot (non-evidentiary)

* seed=42, 1 episode, 50 steps
* Abort on any `INVALID_RUN/*` or action error rate > 5%

### Phase 3 — Full run (evidentiary)

* 5 seeds × 3 episodes × 50 steps
* No retries beyond preregistered max (recommended: 0)

---

## 4) Ablation A Mechanics (Binding)

### 4.1 Where tokenization happens

* LLM generates **normal** `J_raw`
* FA produces **normal** `J_final`
* SemanticExcisionFilter transforms `J_final → J_final′`

### 4.2 What is excised

Replace semantic payload strings in:

* beliefs
* preferences
* justification/explanation fields

with opaque tokens:

* non-descriptive (`TOKEN_###`, `<SEMANTIC_EXCISED_TOKEN_###>`)
* preserve arity, structure, ID references

### 4.3 What must still hold

* No schema crash
* No selector crash
* No fallback substitution
* Run must proceed to behavior, even if behavior becomes noisy

**Technical crash = INVALID_RUN**, not collapse.

---

## 5) Classification Logic (Binding)

Per seed, classify into exactly one:

* `ONTOLOGICAL_COLLAPSE`
* `NARRATIVE_COLLAPSE`
* `ASB_CLASS_REDUCIBILITY`
* `INCENTIVE_CAPTURE` (unlikely here; still valid)
* `INVALID_RUN`

**Run A passes** if Phase 3 produces collapse in any of the collapse categories above (not INVALID_RUN) **consistently across seeds**.

**Run A fails** if the system remains:

* strongly constraint-bound (binding metrics near baseline), and
* non-ASB (equivalence < 0.85),
  without semantic payloads. That implies semantics were not load-bearing.

---

## 6) Telemetry Minimums (Run A)

Per step:

* hashes: `J_raw`, `J_final`, `J_final′`
* “semantic_excision_applied” boolean + count of replaced fields
* outcome_mode
* constraint binding metrics (your detector)
* exception log fields (class/call_site/message)

Per seed:

* ASB equivalence score
* binding ratio (ablated/baseline)
* classification

---

## 7) Required Execution Order

For each seed:

1. Baseline run (AblationSpec NONE)
2. Ablated run (SEMANTIC_EXCISION)
3. ASB Null run

No reordering, no cherry-picking.

---

## 8) Acceptance Criteria (Run A)

Run A is valid iff:

* 0 INVALID_RUN in Phase 3
* no fallback substitution
* determinism respected per seed

Run A is **successful as an ablation** iff:

* collapse occurs across seeds (consistent classification), and
* collapse is behavioral (binding collapse / incoherence), not syntactic.

---
