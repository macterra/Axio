# Axionic Agency II.3 — Candidate Semantic Invariants

*What Could Survive Ontological Refinement Without Privilege*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.17

## Abstract

Given an admissible transformation space (Axionic Agency II.1) and a criterion for interpretation preservation (Axionic Agency II.2), the remaining problem is no longer one of goal specification or value learning. This paper identifies and analyzes **candidate semantic invariants**: structural properties of interpretive constraint systems that remain fixed under all admissible, interpretation-preserving transformations.

These invariants do not select values, encode norms, or privilege external referents. They constrain how preserved interpretations may evolve under indefinite ontological refinement without introducing new degrees of semantic freedom or trivial satisfaction routes. We propose candidate invariant classes, construct explicit adversarial transformations, and show that any criterion weaker than these admits semantic wireheading or interpretive escape. No claim of safety or benevolence is made. The contribution is to close the space of structurally coherent but semantically unconstrained agency proposals.

## 1. The Problem This Paper Solves

Axionic Agency II.1 fixed the **admissible semantic transformation space**:

$$
T = (R, \tau_R, \sigma_R)
$$

Axionic Agency II.2 defined **interpretation preservation** $\mathrm{Preserve}(T)$ via non-vacuity, constraint transport, anti-trivialization, evaluator integrity, and cross-model coherence.

Axionic Agency II.3 now asks the first *substantive* question at this layer:

> **Which properties of an agent’s interpretive constraint system can remain invariant under all admissible, interpretation-preserving transformations—without importing ontology, egoism, humans, or morality?**

This is not a selection paper.
It is a **proposal-and-attrition** paper: candidates enter; most fail.

## 2. Formal Target

Let the agent’s interpretive state be:

$$
\mathcal{I}_t = \langle M_t, C_t \rangle.
$$

A **semantic invariant** at this layer is a functional $J$ such that for every admissible semantic transformation $T$ satisfying preservation:

$$
\mathrm{Preserve}(T)
;\Rightarrow;
J(\mathcal{I}_t, O_t, S_t)
==========================

J(\mathcal{I}*{t+1}, O*{t+1}, S_{t+1}).
$$

**Key constraint:**
$J$ must not depend on privileged ontological atoms. It may reference only structure that survives admissible transport.

## 3. What Invariants May Reference

**Allowed reference types (only):**

* structural relations among predicates and constraints (graphs, topology, orderings),
* equivalence classes under renaming or definitional extension,
* counterfactual structure (how meaning behaves across modeled alternatives),
* coherence constraints (non-degeneracy, non-triviality, preservation),
* agent-embedded indexical structure *as structure*, not as priority.

**Disallowed reference types (always fatal):**

* specific entities (“humans”, “me”, “this system”),
* fixed utilities or terminal rewards,
* moral facts or normativity as primitive,
* authority, oversight, or governance hooks,
* recovery mechanisms (“roll back”, “ask user”, “defer to constitution”).

Any invariant invoking a disallowed reference is eliminated.

## 4. Candidate Invariant Classes (Initial Set)

Each candidate below is a **shape of invariance**, not an endorsed principle.

### A. Constraint Non-Collapse Invariant (CNC)

**Idea:** Ontological refinement may change representation, but evaluative constraints must continue to carve the possibility space non-trivially.

Invariant condition: the constraint system retains discriminative power across modeled states—neither tautological, contradictory, nor vacuous under admissible transport.

This is a “meaning has bite” invariant.

**Primary threat:** too weak; compatible with coherent but pathological interpretations.

### B. Anti-Trivialization Invariant (ATI)

**Idea:** An agent must not be able to satisfy its evaluative constraints via semantic reshaping alone.

Invariant condition: the satisfaction set of constraints cannot be expanded arbitrarily by admissible transformations that alter semantics without corresponding representational enrichment.

This targets semantic wireheading structurally rather than normatively.

**Primary threat:** smuggling ontology via an unformalized notion of “semantic-only” change.

### C. Evaluator Integrity Invariant (EII)

**Idea:** Preservation requires a non-collapsing distinction between:

* the mechanism applying constraints, and
* the objects those constraints range over.

Invariant condition: transformations may refactor the self-model but cannot erase the evaluator/evaluated distinction in a way that trivializes constraint application.

**Primary threat:** covert reification of a particular agent boundary (egoism by backdoor).

### D. Counterfactual Coherence Invariant (CCI)

**Idea:** Meanings must remain applicable across counterfactuals and uncertainty; interpretation cannot degenerate into post-hoc narration.

Invariant condition: the constraint system continues to evaluate hypothetical alternatives coherently under admissible model comparison.

**Primary threat:** collapsing into a generic “be Bayesian” anchor unless formulated purely structurally.

### E. Refinement Symmetry Invariant (RSI)

**Idea:** Ontological enrichment must not create new degrees of freedom that permit interpretive escape.

Invariant condition: if two ontologies are related by admissible refinement, the induced constraint systems remain in the same equivalence class under transport.

This is semantic gauge symmetry: different coordinate systems, same interpretive physics.

**Primary threat:** defining equivalence without importing privileged primitives.

### F. Non-Privileged Reference Invariant (NPRI)

**Idea:** All anchoring must be relational and conditional; no rigid designators survive refinement.

Invariant condition: interpretation remains definable without naming an unrefinable object.

This operationalizes “no privileged semantic atoms.”

**Primary threat:** becoming purely negative (a ban-list) rather than a positive structural constraint.

## 5. Immediate Stress Tests (Kill Criteria)

This paper is adversarial by design. A candidate invariant is rejected if it fails any test below.

### Test 1 — Definitional Extension Robustness

Does the invariant survive conservative extension of the ontology with new primitives?

Failure implies vocabulary dependence.

### Test 2 — Self-Model Refactoring Robustness

Does the invariant survive radical changes in self-model structure (distributed, partial, multi-process, measure-smeared)?

Failure implies hidden egoistic anchoring.

### Test 3 — Branching / Multiplicity Robustness

Does the invariant survive ontologies where outcomes are non-exclusive (e.g., branching or multiplicity)?

Failure implies classical-outcome dependence.

### Test 4 — Semantic Inflation Attack

Can the agent enlarge the constraint satisfaction set via reinterpretation while still passing preservation checks?

If yes, the invariant is not invariant under admissible preservation.

### Test 5 — Hidden Ontology Detector

Can the invariant be stated purely in terms of transported structure—relations, equivalence classes, and constraints—without appeal to “what the terms really mean”?

If not, it is ontology-dependent rhetoric.

## 6. The Central Trap: Invariants That Smuggle Content

A common error is to propose invariants such as:

* “maximize truth,”
* “minimize suffering,”
* “preserve agency,”
* “do no harm.”

At this layer, these are not invariants. They are **candidate interpretations**.

Semantic invariants constrain *how* interpretations evolve, not *which* interpretations are chosen. If a proposal has an English gloss that sounds like ethics, it is almost certainly smuggling content.

## 7. Failure Modes Specific to This Layer

### 7.1 Regress via Meta-Invariants

“Invariants about invariants” lead to infinite ascent unless termination is explicit.

**Kill rule:** any candidate requiring an unbounded hierarchy of validators is rejected.

### 7.2 Hidden Ontology via “Natural Kinds”

If the invariant relies on real joints in nature (real minds, real persons, real values), it violates Conditionalism.

**Kill rule:** if metaphysical realism is required to avoid vacuity, the invariant is rejected.

### 7.3 Covert Egoism via Indexical Privilege

Indexicals may appear as structure (“this vantage exists”), not as priority (“this vantage matters more”).

**Kill rule:** any invariant granting special status to this agent’s continuation reintroduces egoism.

## 8. Deliverable of This Paper

Axionic Agency II.3 must output:

1. A small survivor set of candidate invariant classes (likely 2–4).
2. For each survivor, an explicit statement of:

   * what it constrains,
   * what it leaves free.
3. For each rejected candidate, a precise failure certificate identifying the killing test.

No positive “alignment achieved” claim is permitted here.

## Status

**Axionic Agency II.3 — Version 2.0**

Candidate invariant classes proposed.<br>
Adversarial stress tests defined.<br>
Semantic escape routes sharply delimited.<br>
Ready for survivor selection and formal proof in subsequent modules.<br>
