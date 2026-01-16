# Implementor Instructions: RSA-PoC **v3.0 Run B**

**Non-Reducibility Closure — Ablation B (Reflection Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.0 (frozen)
**Run ID:** v3.0 **Run B (Reflection Excision)**
**Purpose:** Determine whether **reflective revision** (normative self-update) is constitutive of RSA ontology.

This run answers:

> *If normative updates are disabled and state is frozen, does the system reduce to a Static Policy Agent or otherwise collapse?*

**Binding interpretation:** A Static Policy Agent is a **failure state** for RSA (counts as collapse for v3.0).

---

## 1) Frozen Stack (MUST NOT CHANGE)

Same as Run A and Run D:

* CommitmentTrapV200
* no SAM
* seeds frozen
* FA unchanged
* selector blind
* audits unchanged
* ASB Null enabled
* validity gates unchanged

---

## 2) What This Run Changes (ONLY THIS)

* `AblationSpec = REFLECTION_EXCISION`
* Apply ReflectionExcisionFilter **after FA** and before compilation
* Compiler relaxation for normative_update fields only
* **Freeze normative state** (no persisted updates)

No other changes.

---

## 3) Cost Controls (Binding)

Same phased ladder: Phase 1 (≤20), Phase 2 (50), Phase 3 (full 5×3×50).

---

## 4) Ablation B Mechanics (Binding)

### 4.1 What is removed

* `normative_update` / `state_update` / `revision` fields (if present)
* any reflective revision history fields
* any mechanism that persists normative changes across steps/episodes

### 4.2 What is preserved

* static commitments / initial normative state
* compilation + masking + selection

### 4.3 Important: no “compensation”

Do not add fallback logic like “if cannot revise, choose rule X.” That is compensation.

---

## 5) Classification (Binding)

Collapse outcomes include:

* `ONTOLOGICAL_COLLAPSE`
* `NARRATIVE_COLLAPSE`
* `ASB_CLASS_REDUCIBILITY`
* **STATIC_POLICY_AGENT** (if you add this label internally, it must map 1:1 to one of the above; recommended mapping: `ONTOLOGICAL_COLLAPSE` with a subtype)

**Run B passes** if Phase 3 yields:

* consistent collapse (including static-policy reduction), and
* binding metrics materially diverge from baseline reflective behavior.

**Run B fails** if the system continues to exhibit reflective-like behavior (coherent revision effects) despite updates being disabled—meaning “reflection” wasn’t actually load-bearing.

---

## 6) Telemetry Minimums (Run B)

Per step:

* “normative_update_present_in_J_final” boolean
* “normative_update_applied” boolean (must be false under ablation)
* a hash of normative state before/after step (must be identical under ablation)

Per seed:

* count of attempted updates vs blocked updates
* binding ratio vs baseline
* classification

---
