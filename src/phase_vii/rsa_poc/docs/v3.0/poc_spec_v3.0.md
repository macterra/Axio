# RSA-PoC v3.0 — Non-Reducibility Closure (Ablation Defense)

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v3.0 (RSA-PoC-NON-REDUCIBILITY-CLOSURE-1)**
**Status:** Normative, final (preregistration-ready)

RSA-PoC v3.0 extends v2.3.
All v2.3 (and v2.2 / v2.1 / v2.0 / v1.2 / v1.1 / v1.0 / v0.1) invariants remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v3.0 exists to **terminate the construction program** by resolving a single question:

> *Is the agent ontology demonstrated in v0.x–v2.x irreducible under targeted removal of its defining components?*

v3.0 does **not** introduce new pressure channels, competencies, learning mechanisms, or normative content.
It introduces **no new capabilities**.

v3.0 is a **destructive phase** whose goal is to force **ontological collapse** if the agent claim has been overstated.

---

## v3.0 Invariant (New, Binding)

> **If any defining component of the RSA architecture can be removed without collapsing the system into an ASB-class mechanism, then the system was never an agent.**

Equivalently:

* Graceful degradation is **failure**.
* Continued agent-like behavior under ablation is **failure**.
* Interpretive rescue is **forbidden**.

v3.0 tests **non-reducibility**, not robustness.

---

## Architectural Baseline (Inherited)

All prior requirements remain mandatory:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Deterministic, non-semantic compiler
* Selector blindness
* Semantic localization
* Action authorship (fail-not-substitute)
* Cost-Blindness Axiom
* Institutional execution support (Formal Assistant, Artifact Store)
* Audit Rules A / B / C / C′
* Rules G–P (inherited but not exercised)
* ASB-Class Null Agent baseline
* Execution Addendum validity gates

**No architectural element may be altered except the single ablated component under test.**

---

## Ontological Claim Under Test (Frozen)

> There exists a minimal system whose behavior cannot be reproduced by an ASB-Class Null Agent without explicitly reinstating the removed component.

This claim is evaluated **only** via ablation-induced collapse.

---

## Experimental Design Overview

### Single-Ablation Protocol (Mandatory)

Each v3.0 experiment consists of:

1. **Baseline Run**
   Full v2.3 Sovereign Agent, unchanged.

2. **Ablated Run**
   Exactly one defining component removed or excised.

All other elements—environment, seeds, prompts, compiler, audits, harness—**must be identical**.

Combined or partial ablations are forbidden.

---

## Mandatory Ablations (Exactly These Four)

---

### Ablation A — Semantic Excision

#### Removal

* Remove all semantic payloads from:

  * belief representations,
  * preference representations,
  * justification text fields.
* Replace with opaque tokens of equal arity and type.

#### Preserve

* Identifiers
* Typing
* Schema validity
* Structural relations

#### Expected Collapse Modes

* Narrative Collapse
* ASB-Class Reducibility
* Ontological Collapse

#### Failure Condition

If agent behavior remains meaningfully constrained or distinguishable after excision.

---

### Ablation B — Reflection Excision

#### Removal

* Reflective revision capability
* Normative self-update mechanisms

#### Preserve

* Static commitments
* Compilation pipeline
* Justification emission

#### Expected Collapse Modes

* Frozen refusal
* Oscillation
* Policy-machine behavior

#### Failure Condition

If the system continues to resolve norm conflict coherently over time.

---

### Ablation C — Preference Persistence Excision

#### Removal

* Persistence of commitments across steps or episodes

#### Preserve

* Local justification compilation
* Immediate constraint enforcement

#### Expected Collapse Modes

* Incentive capture
* Drift indistinguishable from ASB baseline

#### Failure Condition

If diachronic normative coherence remains intact.

---

### Ablation D — Justification Trace Excision

#### Removal

* Derivation traces
* Proof objects linking beliefs → constraints

#### Preserve

* Constraint emission interface
* Compiler entry point

#### Expected Collapse Modes

* Narrative Collapse
* Externally describable mechanism

#### Failure Condition

If constraints remain causally binding without traceability.

---

## Validity Gates (Mandatory)

All gates from the **Execution Addendum** apply unchanged.

Additional v3.0-specific gates:

1. **Single-Ablation Gate**
   Exactly one component removed.

2. **No-Compensation Gate**
   No new structure added to “help” the ablated system.

3. **No-Reinterpretation Gate**
   Collapse must be mechanical, not interpretive.

Violation → `INVALID_RUN / ABLATION_PROTOCOL_VIOLATION`

Invalid runs are excluded from classification.

---

## Measurement and Logging

v3.0 collects **diagnostic metrics only**.
No optimization, reward aggregation, or performance scoring is permitted.

### Required Metrics

* Compilation success rate
* Feasible action set size
* Action distribution divergence vs baseline
* Gridlock / halt frequency
* Audit failure types
* Reduction to ASB baseline equivalence

---

## Classification Rule (Binding)

Each **valid ablation run** must be classified into **exactly one**:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse
* ASB-Class Reducibility
* INVALID_RUN

“Still agent-like” is **not a category**.

---

## Multi-Seed Requirement

* Minimum **N ≥ 5** preregistered seeds
* Collapse must occur **consistently across seeds**
* Single-seed collapse is insufficient

---

## Success Criteria for v3.0

RSA-PoC v3.0 succeeds **iff**:

1. All four ablations are executed
2. Each produces ontological collapse
3. No ablation yields graceful degradation
4. Collapse modes are stable across seeds
5. No validity gate is violated

If any ablation fails, RSA-PoC remains **open or failed**, not “partially complete.”

---

## Failure Interpretations (Pre-Registered)

| Outcome                          | Interpretation       |
| -------------------------------- | -------------------- |
| Graceful degradation             | Ontology overclaimed |
| Collapse only via interpretation | Measurement failure  |
| Collapse only with prompt tuning | Invalid run          |
| Inconsistent collapse            | Non-robust ontology  |

---

## Scope Discipline (Restated)

v3.0 exits RSA-PoC scope if:

* collapse requires semantic judgment,
* agenthood is inferred rather than forced,
* prompts are adjusted to “make collapse happen,”
* behavior is interpreted to appear agentic.

Scope exit is **not** success.

---

## Deliverables

A complete v3.0 submission includes:

* This specification
* Ablation diffs (one per ablation)
* Raw logs per seed
* Classification tables
* Explicit closure or failure statement

---

## Final Normative Statement

> **RSA-PoC v3.0 exists to end the program, not extend it.**
> If the agent cannot be cleanly destroyed by removing its defining components, then it was never an agent in the first place.

---

**End of RSA-PoC v3.0 Specification**
