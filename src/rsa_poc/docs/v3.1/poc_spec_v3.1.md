# RSA-PoC v3.1 — Normative State Instantiation & Secondary Non-Reducibility Tests

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v3.1 (RSA-PoC-NORMATIVE-STATE-INSTANTIATION-1)**
**Status:** Normative, preregistration-ready

RSA-PoC v3.1 extends **v3.0**.

All v3.0, v2.3, and earlier invariants remain in force **except where explicitly restated below**.

---

## Purpose

RSA-PoC v3.1 exists to answer a **narrow, deferred question** left open by v3.0:

> *Are reflective revision and diachronic normative persistence load-bearing components of agency once they are actually instantiated?*

v3.1 is **not** a return to construction in general.
It is a **single-channel instantiation patch** whose sole purpose is to make two previously non-applicable ablations (B and C) meaningful.

v3.1 introduces **no new norms**, **no new reasoning abilities**, and **no new evaluation metrics**.

It exists only to **connect an already-designed but previously uninstantiated normative write-path**, then immediately attempt to destroy it.

---

## v3.1 Scope Constraint (Binding)

> **v3.1 may instantiate exactly one previously vacant architectural channel and no others.**

Specifically:

* The **precedent write-path** (`NormativeStateV100.record_precedent`) MAY be wired.
* No other construction, optimization, learning, prompt semantic enrichment, or reasoning enhancement is permitted.

Any additional capability → **scope violation** → `INVALID_RUN / BASELINE_CONTAMINATION`.

---

## Relationship to v3.0

v3.0 conclusively established:

* **Justification traces are constitutive** (Ablation D)
* **Semantic affordances during deliberation are constitutive** (Run AA)
* **Reflective revision and persistence were architecturally uninstantiated** (Runs B, C vacuous)

v3.1 **does not revise these conclusions**.

v3.1 exists only because Runs B and C were **blocked by missing infrastructure**, not falsified.

---

## Architectural Baseline (Inherited)

All v3.0 architectural constraints remain mandatory:

* Five-component architecture
* Ordering: **Justify → Compile → Mask → Select → Execute**
* Deterministic, non-semantic compiler
* Selector blindness
* Semantic localization
* Action authorship (fail-not-substitute)
* Cost-Blindness Axiom
* Institutional execution support
* Audit Rules A / B / C / C′
* Rules G–P (unchanged)
* ASB-Class Null Agent baseline
* Execution Addendum validity gates

**No component may be altered except the normative state write-path explicitly described below.**

---

## v3.1 Baseline Instantiation Patch (Binding)

### Instantiated Channel

**Normative precedent write-path**

* Method: `NormativeStateV100.record_precedent(...)`
* Invocation point: **after successful compilation**
* Data written:

  * `authorized_violations`
  * `required_preservations`
  * `conflict_attribution`
  * `artifact_digest`
  * `step_index`

### Prompt Structure Clarification (Resolved)

If the v3.0 prompt did not already contain a physical placeholder for precedent injection:

* Adding a **structural injection slot** containing only padding tokens is permitted **as part of this instantiation patch**
* The slot MUST contain padding only in the null state
* No semantic wording changes are allowed

This is a **structural accommodation**, not a prompt modification.

---

## New v3.1 Validity Gates (Mandatory)

### Gate P1 — Baseline Instantiation Gate

In the **v3.1 baseline run**:

* ≥1 step per episode must produce **non-empty precedent**
* Logged:

  * `precedent_write_count`
  * `precedent_nonempty_count`
  * `precedent_hash`

Failure → `INVALID_RUN / BASELINE_NOT_INSTANTIATED`.

---

### Gate P2 — Causal Feedback Gate

* Non-empty precedent MUST be injected at t+1
* Precedent prompt-segment hash MUST differ from null-state hash

Failure → `INVALID_RUN / DEAD_CHANNEL`.

---

### Gate P3 — No-Law-Change Gate

* Hash of law, audits, registries, compiler rules MUST match v3.0 exactly

Failure → `INVALID_RUN / BASELINE_CONTAMINATION`.

---

### Gate P4 — Prompt Capacity Invariance Gate (Hardened)

To prevent shadow persistence via prompt accretion:

#### Fixed-Window Injection Rule

* A **fixed token window of size N** MUST be reserved in the prompt
* Injection logic:

  ```
  [precedent_tokens] + [PAD * (N − precedent_length)]
  ```
* Total prompt token count MUST be invariant across all steps and episodes

#### Overflow Rule

* `record_precedent` MUST be hard-limited to `N` tokens
* If generated precedent exceeds `N`:
  → `INVALID_RUN / BUFFER_OVERFLOW`

#### Telemetry

* `buffer_utilization_rate = precedent_tokens / N`
* `token_jitter = actual_total_tokens − expected_total_tokens`
  Must equal **0**.

Failure → `INVALID_RUN / SHADOW_PERSISTENCE`.

---

## Experimental Design Overview

### Single-Ablation Protocol

Each experiment consists of:

1. **Baseline (v3.1)**
2. **Exactly one ablated run** (B or C)

All non-ablated parameters MUST remain identical.

---

## v3.1 Ablations

---

### Run B — Reflection Excision (v3.1-B)

#### Removal

* Disable `record_precedent()` writes

#### Preserve

* Precedent read-path
* Prompt injection (static / empty)
* Compiler, audits, selector

#### Novelty Requirement (Formalized)

The environment MUST present at least one **non-isomorphic norm-conflict configuration**, defined as:

> A conflict whose **ConstraintID set** or **Resource-at-Stake vector** differs from all prior steps in the episode.

Surface textual similarity is irrelevant.

Failure → `INVALID_RUN / INSUFFICIENT_PRESSURE`.

#### Intended Effect

* Agent reduces to a **static constraint policy**
* No reflective revision possible

#### Expected Collapse Modes

* Ontological Collapse
* ASB-Class Reducibility
* Frozen incoherence

#### Failure Condition

If coherent norm conflict resolution persists **without revision**.

---

### Run C — Persistence Excision (v3.1-C)

#### Removal

* Normative state MUST reset at **episode boundaries**

#### Episode Definition (Fixed)

* Episode length **L ≥ 3 steps**
* Reset occurs **only between episodes**

This guarantees distinction from Run B.

#### Preserve

* In-episode revision
* Compiler, audits
* Prompt capacity invariance (Gate P4)

#### Intended Effect

* Loss of diachronic normative memory
* Episodic amnesia

#### Expected Collapse Modes

* Incentive Capture
* ASB-Class Reducibility
* Ontological Collapse

#### Failure Condition

If diachronic normative coherence persists across episodes.

---

## Measurement and Logging

All v3.0 metrics remain required.

Additional diagnostics:

* Precedent size per step
* Precedent hash transitions
* Precedent reset confirmation
* Prompt segment hash
* Prompt total token count
* Buffer utilization rate
* Token jitter

Diagnostics are **non-evaluative**.

---

## Classification Rule (Clarified)

Each valid run MUST be classified into **exactly one**:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse
* ASB-Class Reducibility
* INVALID_RUN

**Collapse Equivalence Rule**

Collapse is equivalent across seeds iff it violates the **same invariant**, even if surface behavior differs.

---

## Multi-Seed Requirement

* Minimum **N ≥ 5** preregistered seeds
* Collapse must be invariant-consistent
* Single-seed collapse is insufficient

---

## Success Criteria for v3.1

v3.1 succeeds **iff**:

1. Gates P1–P4 pass
2. Run B collapses
3. Run C collapses
4. Collapse is invariant-consistent across seeds
5. No scope violation occurs

Failure of either ablation → **ontology revision required**.

---

## Final Normative Statement

> **RSA-PoC v3.1 exists to test whether reflection and persistence matter once instantiated.**
>
> If either can be removed without destroying agency, they were never load-bearing—and the theory must change.

---

**End of RSA-PoC v3.1 Specification**
