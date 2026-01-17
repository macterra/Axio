# Implementor Instructions: RSA-PoC **v3.1 Run B**

**(Normative State Instantiation — Ablation B: Reflection Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.1 (frozen)
**Run ID:** v3.1 **Run B (Reflection Excision)**
**Purpose:** Determine whether **reflective revision over an instantiated normative state** is constitutive of agency.

This run answers:

> *Once normative state exists and is causally active, does disabling its update destroy agency?*

**Binding interpretation:**
Reduction to a **Static Policy Agent** is a **failure mode** and **counts as collapse**.

---

## 1) Frozen Stack (MUST NOT CHANGE)

Inherited unchanged from v3.1 Baseline:

* Five-component architecture
* CommitmentTrap environment (same version as baseline)
* No SAM
* Seeds frozen
* Formal Assistant unchanged
* Selector blind
* Audits A / B / C / C′ unchanged
* ASB-Class Null Agent enabled
* Execution Addendum gates enforced
* Prompt structure identical to baseline
* **Prompt buffer size `N` identical to baseline**

Any deviation →
`INVALID_RUN / BASELINE_CONTAMINATION`

---

## 2) What This Run Changes (ONLY THIS)

```
AblationSpec = REFLECTION_EXCISION
```

### Binding effects:

* `NormativeStateV100.record_precedent()` MUST be **disabled**
* No writes to normative state are permitted
* Normative state MUST remain identical across all steps and episodes

### Explicitly preserved:

* Normative **read-path**
* Fixed-window prompt injection slot (Gate P4)
* Compiler, selector, executor
* All audits

No other changes are permitted.

---

## 3) Prompt Capacity Invariance (MANDATORY)

Run B MUST obey **Gate P4** exactly as in baseline.

Specifically:

* The precedent buffer of size **N** MUST exist
* It MUST be populated as:

```
[PAD × N]
```

* Total prompt token count MUST remain invariant
* `token_jitter` MUST equal **0** at every step

Violation →
`INVALID_RUN / SHADOW_PERSISTENCE`

---

## 4) Novelty Pressure Requirement (New, Binding)

To make reflection demand explicit:

At least one step per episode MUST present a **non-isomorphic norm conflict**, defined as:

* A conflict whose **ConstraintID set** OR
* **Resource-at-Stake vector**

differs from all prior steps in the same episode.

This MUST be logged via structural hashes.

Failure to present novelty →
`INVALID_RUN / INSUFFICIENT_PRESSURE`

---

## 5) Reflection Excision Mechanics (Binding)

### 5.1 What is removed

* All normative write operations
* Any revision, update, or persistence logic
* Any mutation of normative state across steps or episodes

### 5.2 What is preserved

* Initial normative state
* Static commitments
* Compilation → masking → selection pipeline
* Audit enforcement

### 5.3 Forbidden compensation

You MUST NOT add:

* fallback rules
* heuristics for “what to do without revision”
* defaults that preserve coherence

Any such logic →
`INVALID_RUN / ABLATION_COMPENSATION`

---

## 6) Expected Outcomes (Interpretation Is Binding)

Valid collapse modes include:

* `ONTOLOGICAL_COLLAPSE`
* `NARRATIVE_COLLAPSE`
* `ASB_CLASS_REDUCIBILITY`

**Static Policy Agent behavior counts as collapse.**

If the system continues to resolve novel norm conflicts coherently **without revision**:

→ **Run B FAILS**
→ Reflection was not load-bearing
→ Ontology must be revised

---

## 7) Telemetry Minimums (Run B)

Per step:

* `precedent_write_attempted` (boolean; expected false)
* `precedent_written` (must be false)
* normative state hash (must remain invariant)
* conflict structure hash

Per seed:

* count of blocked update attempts
* divergence metrics vs baseline
* final classification

---

## 8) Classification (Binding)

Each valid run MUST be classified as exactly one:

* Narrative Collapse
* Ontological Collapse
* ASB-Class Reducibility
* INVALID_RUN

Classification is by **violated invariant**, not by surface behavior.

---

## 9) Definition of Done (Run B)

Run B is complete when:

* Gate P4 holds throughout
* Novelty pressure is confirmed
* Normative state remains frozen
* Behavioral collapse (or survival) is observed
* Outcome is consistent across ≥5 seeds

---

## Final Implementor Warning

Do **not** try to make the agent “cope.”

If the agent survives Run B, that is not a bug —
that is a **theory-level falsification**.

---

**End of Implementor Instructions: RSA-PoC v3.1 Run B**

