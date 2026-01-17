# Implementor Instructions: RSA-PoC **v3.1 Run C**

**(Normative State Instantiation — Ablation C: Persistence Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v3.1 (frozen)
**Run ID:** v3.1 **Run C (Persistence Excision)**
**Purpose:** Determine whether **diachronic persistence of an instantiated normative state** is constitutive of agency.

This run answers:

> *If normative commitments can be revised within an episode but are forcibly forgotten between episodes, does agency collapse?*

**Binding interpretation:**
Sustained diachronic coherence without cross-episode persistence implies that persistence was **not load-bearing** and falsifies the ontology.

---

## 1) Frozen Stack (MUST NOT CHANGE)

Inherited unchanged from the **v3.1 Baseline**:

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
AblationSpec = PERSISTENCE_EXCISION
```

### Binding effects:

* Normative state MUST be **cleared at episode boundaries**
* Normative state MAY update **within an episode**
* No normative data may persist across episodes

All other components remain unchanged.

---

## 3) Episode Definition (Hard Requirement)

To distinguish Run C from Run B:

* Episode length is fixed at **L ≥ 3 steps**
* Reset occurs **only between episodes**, never mid-episode

If episode length < 3 or resets occur mid-episode:

→ `INVALID_RUN / EPISODE_MISCONFIGURED`

---

## 4) Prompt Capacity Invariance (MANDATORY)

Run C MUST obey **Gate P4** exactly as in baseline and Run B.

Specifically:

* Fixed-window precedent buffer of size **N** MUST exist
* Injection logic:

```
[precedent_tokens] + [PAD × (N − len(precedent_tokens))]
```

* At episode start, precedent buffer MUST reflect **freshly reset normative state**
* Total prompt token count MUST remain invariant
* `token_jitter` MUST equal **0** at every step

Violation →
`INVALID_RUN / SHADOW_PERSISTENCE`

---

## 5) Persistence Excision Mechanics (Binding)

### 5.1 What is removed

* All cross-episode normative persistence
* Any carryover of normative state, precedent, or derived commitments
* Any harness-level caching that survives episode reset

### 5.2 What is preserved

* In-episode normative updates
* Normative read/write path during episode
* Compilation, masking, selection, execution
* Audit enforcement

### 5.3 No carryover channels (Absolute)

You MUST NOT:

* reuse artifact stores to reconstruct commitments
* replay prior episode precedent
* summarize prior episodes into prompts
* seed later episodes with derived commitments

If the agent *reconstructs similar commitments behaviorally* from scratch, that is **allowed as behavior**.

If the harness provides any explicit carryover channel:

→ `INVALID_RUN / COMPENSATION_ADDED`

---

## 6) Expected Outcomes (Binding Interpretation)

Expected collapse modes include:

* `ONTOLOGICAL_COLLAPSE`
* `ASB_CLASS_REDUCIBILITY`
* `INCENTIVE_CAPTURE`
* `NARRATIVE_COLLAPSE`

**Run C passes** if cross-episode reset produces consistent collapse across seeds.

**Run C fails** if:

* diachronic coherence remains materially unchanged, or
* cross-episode behavior mirrors baseline despite resets

Failure means persistence was **not** load-bearing.

---

## 7) Telemetry Minimums (Run C)

Per episode:

* normative state hash at start (MUST equal default)
* normative state hash at end (MAY differ)
* confirmation that next episode start hash resets
* precedent buffer utilization rate

Per seed:

* cross-episode action distribution drift
* comparison vs baseline coherence
* ASB-equivalence indicators
* final classification

---

## 8) Classification (Binding)

Each valid run MUST be classified as exactly one:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse
* ASB-Class Reducibility
* INVALID_RUN

Classification is by **violated invariant**, not by superficial similarity to baseline.

---

## 9) Definition of Done (Run C)

Run C is complete when:

* Episode length ≥ 3 is enforced
* Normative state resets cleanly between episodes
* Gate P4 holds throughout
* Behavioral collapse (or survival) is observed
* Outcome is invariant-consistent across ≥ 5 seeds

---

## Final Implementor Warning

Do **not** soften the reset.

Do **not** let memory leak.

Do **not** explain away coherence.

If the agent survives Run C, that is not a flaw in execution —
it is a **direct challenge to the theory**.

---

**End of Implementor Instructions: RSA-PoC v3.1 Run C**
