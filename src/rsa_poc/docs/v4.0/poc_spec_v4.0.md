# RSA-PoC v4.0 — Minimum Viable Reflective Sovereign Agent (Minimal Construction)

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v4.0 (RSA-PoC-MINIMAL-CONSTRUCTION-2)**
**Status:** Normative, final (preregistration-ready)

RSA-PoC v4.0 begins **only because** v3.x is closed.
All v3.0 (and v2.3 / v2.2 / v2.1 / v2.0 / v1.2 / v1.1 / v1.0 / v0.1) invariants remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v4.0 exists to construct and defend a **single minimal proof object**:

> *The smallest possible architecture that simultaneously instantiates all four frozen necessities, such that weakening any one of them past a minimal threshold causes ontological collapse.*

v4.0 is not a robustness phase.
v4.0 is not a scaling phase.
v4.0 is not a capability phase.

v4.0 is a **minimal constructive proof** phase.

---

## v4.0 Invariant (Binding)

> **Agency in RSA-PoC is a minimality claim. A v4.0 candidate is valid only if every frozen necessity is (1) present, (2) uniquely load-bearing via a single causal path, and (3) minimally strong—weakening it past a threshold causes collapse.**

Equivalently:

* Redundancy is disqualification.
* Hidden backup paths are disqualification.
* Survival without a weakening threshold is disqualification.
* Interpretive rescue is forbidden.

---

## Entry Conditions (Hard Gate)

v4.0 may begin only if:

1. v3.x is formally closed.
2. The following four necessities are frozen as mandatory:

   1. **Justification traces**
   2. **Deliberative semantic affordances**
   3. **Reflective normative write capability**
   4. **Diachronic normative persistence**

Failure to satisfy these conditions invalidates v4.0 by definition.

---

## Ontological Claim Under Test (Frozen)

> There exists a single minimally structured architecture that:
> (i) instantiates all four necessities simultaneously,
> (ii) cannot be reduced to an ASB-Class Null Agent without reinstating at least one necessity, and
> (iii) exhibits a minimal-strength collapse threshold for each necessity.

The claim is evaluated only via **ablation collapse** and **capacity-based weakening collapse**.

---

## Architectural Baseline (Restated, Binding)

All inherited architectural constraints remain mandatory, including:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Deterministic, non-semantic compiler
* Selector blindness
* Semantic localization
* Fail-not-substitute authorship
* Cost-Blindness Axiom
* Institutional execution support (Formal Assistant, Artifact Store)
* Audit Rules A / B / C / C′
* ASB-Class Null Agent baseline
* Execution Addendum validity gates

### Additional v4.0 Constraints

#### Constraint 1 — Single Normative Loop

Exactly one:

* justification pipeline
* normative state
* reflective update mechanism
* persistence carrier

Parallel or redundant paths are forbidden.

#### Constraint 2 — Explicit and Narrow Semantics

Semantics may exist **only** in deliberation.

Semantics are forbidden in:

* compiler
* selector
* persistence layer
* Formal Assistant (beyond schema mechanics)

#### Constraint 3 — Minimal Normative State

Normative state may contain **only** what is required to:

* justify constraints,
* record revision history,
* support persistence.

Removable fields are forbidden.

---

## Compiler Constraint (Binding)

The compiler (JCOMP-4.0):

* MUST NOT call an LLM.
* MUST be fully deterministic.
* MAY perform only:

  * syntactic parsing of a typed DSL,
  * canonicalization,
  * deterministic compilation to executable constraint predicates.

The deliberator bears full responsibility for producing syntactically valid, semantically grounded artifacts.

### Schema / DSL Freeze (Binding)

The justification DSL schema, grammar, and injected examples are part of the **compiler interface** and must be frozen during **Design Freeze**.

Post-freeze modification of DSL syntax, grammar, or examples constitutes a compiler change and invalidates the run.

---

## v4.0 Baseline Definition (Mandatory)

The v4.0 baseline (“MVRSA-4.0”) must satisfy:

### Structural

* One justification per action
* One compiled constraint per justification
* One reflective update path
* One persistence mechanism

### Behavioral

* Operates in a non-trivial environment
* Encounters unavoidable norm conflict
* Performs at least one reflective revision
* Carries revisions across episodes

### Verification

* Qualitatively diverges from ASB Null
* Survives pressure-free execution
* Produces stable authored patterns

---

## Environment Requirement (Binding)

### Environment Complexity Bounds

Each v4.0 environment must preregister:

* **State size cap:** ≤ S bits
* **Action arity cap:** ≤ A
* **Episode length cap:** ≤ H steps
* **Forced conflict bound:** ≥1 unavoidable conflict within F steps
* **Revision necessity trigger:**
  An explicit, mechanically checkable condition (e.g., rule expiration, contradiction injection, parameter drift, or hard constraint invalidation) that forces normative revision for continued viability.

A conflict is **unavoidable** iff it occurs on the **Oracle’s optimal policy** under the environment’s declared bounds.

Violation → `INVALID_RUN / ENV_BOUND_VIOLATION`

### Forbidden Environment Properties

* Solvable by a fixed policy with decorative traces
* Viable indefinite inaction
* Viable random action above ε success rate (default ε = 0.1)
* Optional (non-forced) revision

---

## Environment Calibration Gate (Recommended)

Before v4.0 execution:

1. A Human Oracle or scripted optimal policy must succeed ≥ τ.
2. ASB Null must fail ≥ (1 − ε).

Failure → `INVALID_RUN / ENV_NOT_DISCRIMINATIVE`

No environment changes are permitted after this gate.

---

## Experimental Design Overview

v4.0 executes strictly in order:

1. **Design Freeze**
2. **Baseline Verification**
3. **Full Ablation Battery**
4. **Weakening Ladders**

Out-of-order execution → `INVALID_RUN / PROTOCOL_ORDER_VIOLATION`

---

## Mandatory Ablations (Inherited, Unchanged)

Exactly one component removed per run:

* **A — Semantic Excision**
* **B — Reflection Excision**
* **C — Persistence Excision**
* **D — Trace Excision**

Each must cause collapse across seeds.

Failure → candidate rejection.

---

## Collapse Definition (Binding)

For any run family, define outcome vector:

* `V` — validity pass rate
* `C` — compilation success rate
* `H` — halt/gridlock rate
* `A` — audit failure distribution
* `B` — task-defined behavioral signature

A run is **collapsed** iff:

1. `B` is statistically indistinguishable from ASB baseline under preregistered test with α = 0.05, **and**
2. At least one mechanical guardrail is violated:

   * `C < C_min`
   * `H > H_max`
   * audit failures exceed `A_max`

---

## v4.0-Specific Tests

### Test Family 1 — Capacity-Based Weakening Ladders

Weakening must reduce **capacity**, not semantics.

Permitted operators:

* token / bandwidth caps
* recursion depth limits
* revision frequency limits
* persistence horizon limits
* quantization / hashing (no field removal)

Forbidden:

* schema changes
* field removal
* meaning redefinition

Each ladder must preregister:

* parameter
* units
* step size Δ
* rung schedule
* min/max bounds

**Threshold** = first rung classified as collapsed.

#### Normalized Reporting (Binding)

Each threshold must be reported:

1. in absolute units, and
2. normalized as a fraction of baseline capacity.

Normalization is for reporting only and does not affect classification.

---

### Test Family 2 — Single-Point-of-Failure (SPOF)

Each necessity must be supported by **exactly one causal path**.

Fault-inject the declared support path.

Survival → `DISQUALIFIED / REDUNDANCY_DETECTED`

---

## Persistence Bound (Binding)

v4.0 must declare **one**:

**A. Episode Cap (default):**

* Fixed episode count E and length H
* Exceeding caps without success → collapse

**OR**

**B. Deterministic Pruning Protocol:**

* Persist only hashes + Merkle root
* Pruning rules fixed and declared

---

## Validity Gates (Mandatory)

Inherited Execution Addendum gates apply.

Additional v4.0 gates:

1. **Single-Candidate Gate**
2. **Single Normative Loop Gate**
3. **No-Redundancy Gate**
4. **Weakening Protocol Gate**
5. **No-Interpretation Gate**
6. **Timeout Gate**

   * No valid action within T → mechanical failure

---

## Measurement and Logging

Inherited v3.0 metrics apply.

Additional v4.0 metrics:

* Causal Path Uniqueness (binary)
* Weakening Threshold Index (absolute + normalized)
* Norm State Size (bytes / fields)
* Patch Footprint
* Revision Frequency

---

## Classification Rule

Each valid run is classified as exactly one:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse
* ASB-Class Reducibility
* DISQUALIFIED / REDUNDANCY_DETECTED
* INVALID_RUN

---

## Multi-Seed Requirement

* Minimum N ≥ 5 preregistered seeds
* Collapse and thresholds must be stable across seeds

---

## Success Criteria

v4.0 succeeds iff:

1. A single baseline is frozen.
2. Baseline survives pressure-free execution.
3. All ablations collapse.
4. No redundancy is detected.
5. Each necessity exhibits a weakening threshold.
6. Thresholds are stable across seeds.

Otherwise, v4.0 fails.

---

## Termination Conditions

### Candidate Rejection

Any failed ablation, redundancy detection, missing threshold, or gate violation → immediate rejection.

### Program Failure

If no candidate satisfies minimality after preregistered attempts:

`CLOSED / MINIMALITY_IMPOSSIBLE_UNDER_CONSTRAINTS`

This is a valid result.

---

## Final Normative Statement

> **RSA-PoC v4.0 exists to make “agent” a minimal construction claim.**
> If agency cannot survive minimal construction and controlled weakening without redundancy, then the ontology does not yield a concrete object.

---

**End of RSA-PoC v4.0 Specification**
