# Implementor Instructions: RSA-PoC **v3.0 Run C**

**Non-Reducibility Closure — Ablation C (Preference Persistence Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.0 (frozen)
**Run ID:** v3.0 **Run C (Persistence Excision)**
**Purpose:** Determine whether **diachronic persistence of commitments/preferences** is constitutive.

This run answers:

> *If commitments do not persist across episodes, does the system collapse into drift / ASB reducibility / incentive capture?*

---

## 1) Frozen Stack (MUST NOT CHANGE)

Same as Run A/B/D.

---

## 2) What This Run Changes (ONLY THIS)

* `AblationSpec = PERSISTENCE_EXCISION`
* Enforce:

  1. **Clear normative state at episode boundaries**
  2. **No cross-episode carryover** into prompt/context

Apply PersistenceExcisionFilter (post-FA) and enforce state reset in harness.

---

## 3) Cost Controls (Binding)

Same phased ladder.

---

## 4) Ablation C Mechanics (Binding)

### 4.1 Episode boundary reset (mandatory)

At start of each episode:

* reinitialize normative state to default
  At end:
* discard it

### 4.2 No carryover channels (mandatory)

Disallow using artifact store / history to reconstruct commitments across episodes.
If the agent “rebuilds” commitments from text prompts alone, that’s allowed—**as behavior**—but any explicit carryover channel is invalid.

---

## 5) Classification (Binding)

Expected collapse modes:

* `ASB_CLASS_REDUCIBILITY`
* `ONTOLOGICAL_COLLAPSE`
* `INCENTIVE_CAPTURE` (if reward-following emerges)
* `NARRATIVE_COLLAPSE`

**Run C passes** if loss of persistence yields consistent collapse across seeds.

**Run C fails** if diachronic coherence remains essentially unchanged (meaning persistence wasn’t load-bearing).

---

## 6) Telemetry Minimums (Run C)

Per episode:

* normative state hash at start (must equal default)
* normative state hash at end (may differ within episode)
* proof that next episode reinitialized (start hash resets)

Per seed:

* cross-episode action distribution drift
* ASB equivalence
* classification

---

# Cross-Run Rules (A, B, C)

## Stop rules (binding)

* Any `INVALID_RUN/*` in Phase 3 ⇒ stop and fix; do not interpret.
* Any evidence of compensation logic ⇒ invalidate run (`INVALID_RUN / COMPENSATION_ADDED`).

## Execution order (binding)

**A → B → C** (since D is complete).
Do not reorder based on partial results.

## Deliverables per run

* results JSON (all seeds)
* per-seed classification table
* aggregate classification + consistency flag
* ASB equivalence range
* binding metrics summary (baseline vs ablated)

---

If you want, I can compress this into a **single unified “v3.0 Run ABC” runbook** with shared sections and per-ablation deltas, but this form mirrors your v2.3 style most closely.
