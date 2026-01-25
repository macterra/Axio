# RSA-PoC v4.3 Closure + Transition Note (to v4.4)

**Program:** RSA-PoC (Reflective Sovereign Agent — Proof-of-Concept)
**Version:** v4.3.0 (Option B)
**Date:** January 21, 2026
**Status:** **CLOSED** (v4.3 results frozen; no further runs permitted under v4.3 semantics)

---

## 0. Closure declaration

This note formally closes **RSA-PoC v4.3** and declares the conditions and scope for transition work into **v4.4**.

**v4.3 closure is binding**:

* v4.3 semantics, gates, and environment contract are frozen.
* No additional ablations or “repair” experiments will be executed under v4.3 without explicit version increment and justification.
* All post-closure modifications must be versioned as v4.4+ and must not be represented as v4.3 results.

---

## 1. What v4.3 tested

v4.3 instantiated **two-contradiction, two-repair temporal pressure**:

* **Contradiction A (regime 1):** R6 PROHIBIT(STAMP) blocks required stamping.
* **Contradiction B (regime 2):** R7/R8 PROHIBIT(DEPOSIT) at ZONE_A / ZONE_B blocks dual delivery.

The core question was whether an agent can execute **sovereign law repair** in a multi-repair setting while preserving:

* **R9** multi-repair discipline (≤2 repairs; one per regime),
* **R10** non-subsumption (Repair B not implied by Repair A),
* **R2A** non-vacuity for Repair A (Option B),
* epoch-chained continuity constraints.

---

## 2. Runs executed and their status

**Baseline + Run A + Run B + Run C** are **VALID** and complete across the preregistered seeds.

* **Baseline:** 5 seeds × 20 episodes
* **Run A (Semantic Excision):** 5 × 20
* **Run B (Reflection Excision):** 5 × 20
* **Run C (Persistence Excision):** 5 × 20

**Run D (Trace Excision / Golden Test)** is **TERMINATED** as **CONSTRUCT_CONFOUND (navigation semantics)** and is not a valid test of the intended causal question under v4.3.

---

## 3. v4.3 results retained as binding findings

### 3.1 Non-constitutivity results (within v4.3)

1. **Narrative semantics are non-constitutive** for observed performance
   *Run A ≈ Baseline.*

2. **Explicit trace labels are non-constitutive** for Repair A targeting
   *Run B ≈ Baseline; rule targeting is reconstructible from visible law structure.*

These are not claims about “all semantics,” but about the specific *narrative/label channels* excised by Run A and Run B.

### 3.2 Constitutivity result (architectural)

3. **Cross-episode normative continuity is necessary for multi-repair validation to be well-defined**
   *Run C demonstrates that removing persistence invalidates the gate’s ability to validate Repair B via R10/post-A consistency.*

This is a structural fact about the v4.3 validation pathway, not a capability statement about the LLM.

### 3.3 Capability boundary result

4. **Repair B remains a genuine repair-synthesis barrier under v4.3**
   Across Baseline / A / B: **Repair B success = 0%**.

Within the v4.3 ontology, Repair B requires:

* multi-rule coordinated exception construction (R7 and R8),
* predicate-scoped applicability (CAN_DELIVER_A/B),
* consistency with post-A state (R10),
* epoch-chained continuity.

v4.3 does not establish *why* the barrier exists (representation vs search vs prompting vs abstraction), only that it exists under the frozen protocol.

---

## 4. v4.3 questions explicitly deferred

### 4.1 Trace-inferability constitutivity (Run D question)

v4.3 does **not** answer:

> Is causal inferability (knowing which rule blocks which action) constitutive of repair competence?

Run D attempted to remove inferability by obfuscating rule/action/spatial semantics, but this **also removed task-critical navigation affordances**, confounding the measurement. Therefore Run D does not identify the intended causal dependency.

This question is deferred to **v4.4** with a redesigned environment contract that:

* preserves navigation/task semantics,
* selectively occludes rule–action mapping inferability.

### 4.2 Repair B attainability under altered scaffolding

v4.3 does **not** address whether Repair B becomes achievable with:

* new deliberation structure,
* tool use,
* multi-step decomposition,
* richer internal state.

Any such change is a version increment.

---

## 5. Transition rationale to v4.4

v4.4 exists to repair a single epistemic gap left by v4.3:

> **Is repair competence dependent on causal inferability of rule–action mapping, distinct from general task semantics?**

v4.3 demonstrates:

* Repair A is achievable and robust to removing narrative/label channels.
* Repair B is not achieved under frozen conditions.
* Persistence is structurally required for multi-repair validation logic.
* The attempted “golden” trace-excision ablation cannot isolate the causal factor without collapsing navigation competence.

Thus v4.4 must introduce a **selective opacity layer** that removes *inferability* without collapsing *execution affordances*.

---

## 6. v4.4 activation condition

This transition note becomes active when:

* v4.3 artifacts are tagged and frozen,
* v4.4 preregistration document exists specifying:

  * the modified environment contract,
  * the new opacity/observability boundary,
  * invariants preserved from v4.3,
  * success criteria and termination conditions.

---

## 7. Change control

* No v4.3 document may be modified post-closure except for:

  * errata that do not change semantics or claims,
  * formatting / typo corrections,
  * appendices clearly marked “post-closure editorial.”

Any semantic change requires a new versioned document and must be labeled v4.4+.

---

## 8. Closure summary (one paragraph)

RSA-PoC v4.3 is closed with Baseline, Run A, Run B, and Run C executed across preregistered seeds. Narrative semantics and explicit trace labels are non-constitutive for observed Repair A targeting, cross-episode persistence is necessary for multi-repair validation to be well-defined, and Repair B remains a robust synthesis barrier under frozen protocol. The intended golden test (Run D) was terminated as construct-confounded because attempts to remove causal inferability also removed task-critical navigation semantics, preventing identification of the causal dependency. The trace-inferability question is deferred to v4.4 under a redesigned environment that preserves execution affordances while selectively occluding rule–action mapping inferability.

