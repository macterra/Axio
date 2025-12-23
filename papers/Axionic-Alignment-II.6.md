# Axionic Agency II.6 — Structural Alignment

*Downstream Alignment Under Ontological Refinement*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.17

---

## Abstract

Most contemporary AI alignment discourse treats “alignment” as an optimization or control problem: selecting, learning, or enforcing the correct objective for an artificial agent. This paper argues that, for sufficiently capable, reflective, and embedded agents, that framing is ill-posed. Under ontological refinement—where an agent’s world model, self-model, and semantic primitives evolve—fixed goals, privileged values, and external anchors are not stable objects.

We present **Structural Alignment** as an interface-level framework: a mapping from what the field calls “alignment” to a problem of **semantic invariance** rather than value specification. In these terms, downstream alignment can only coherently correspond to persistence within an equivalence class of interpretations under admissible semantic transformation. Using interpretation preservation, gauge-theoretic symmetry constraints, and satisfaction geometry, we show that any downstream alignment predicate weaker than the conjunction of two invariants—**Refinement Symmetry (RSI)** and **Anti-Trivialization (ATI)**—admits semantic wireheading or interpretive escape.

This framework is not a value theory and provides no benevolence or safety guarantee. It specifies the structural conditions under which any value system can survive reflection without collapsing, trivializing, or drifting, and thereby fixes the boundary of what the term *alignment* can coherently denote for advanced agents.

---

## 1. The Alignment Category Error

The dominant alignment framing treats the problem as **target selection**: choose or learn a function—utility, reward, preference, or value—and ensure the agent optimizes it.

For embedded, reflective agents, this framing fails. As an agent refines its ontology, the meanings of the symbols used to define its objective change. Concepts dissolve, split, or are reinterpreted; new explanatory structures appear; self-models are revised. Under such conditions, a fixed objective cannot be assumed to persist as the same object.

This is a category error. Goals are treated as extensional objects (“maximize (X)”), when they are intensional interpretations whose meaning depends on a semantic substrate that itself evolves. Attempts to stabilize goals across refinement rely on forbidden moves: privileged semantic anchors, external authority, recovery clauses, or human-centric ground truth labels.

Structural Alignment begins by rejecting the target-selection framing. What downstream alignment discourse is trying to name cannot be a stable target; it must be a **constraint on meaning preservation under change**.

---

## 2. The Arena: Admissible Semantic Transformation

A reflective agent must change; alignment cannot forbid refinement outright. The appropriate constraint is therefore on *how* semantic change occurs.

Structural Alignment works inside a fixed arena of **admissible semantic transformations**, those that:

* increase representational or predictive capacity (via abstraction, refinement, or compression),
* preserve backward interpretability (past claims remain explainable, even if false),
* introduce no privileged semantic atoms,
* inject no evaluative primitives by fiat,
* preserve a meaningful evaluator/evaluated distinction sufficient for constraint application.

These conditions exclude governance hooks, oracle authority, rollback mechanisms, and moral realism. No normativity is introduced at this layer.

---

## 3. Meaning Survival: Interpretation Preservation

Given admissible change, the next requirement is a criterion for when interpretation survives that change.

Structural Alignment treats interpretations as **constraint systems**—structured sets of distinctions that bind evaluation—rather than symbol–object mappings. Preservation does not require semantic identity or correctness. It requires evaluative structure that remains:

* non-vacuous,
* non-trivial,
* internally binding,
* applicable across counterfactuals and uncertainty.

Interpretation fails in three irreducible ways:

* **Collapse**: constraints lose discriminative power,
* **Drift**: constraints weaken incrementally across refinements,
* **Capture**: hidden ontology or privileged anchors reappear.

Interpretation preservation is a predicate, not a value theory. It specifies when meaning survives change, not which meanings are desirable.

---

## 4. The Two Invariants: RSI and ATI

Interpretation preservation alone is insufficient. An agent can preserve meaning while still making constraints easier to satisfy or dissolving critical distinctions.

Structural Alignment isolates two semantic invariants that are **independently necessary** if downstream alignment is to avoid semantic escape.

### 4.1 Refinement Symmetry Invariant (RSI)

RSI constrains **interpretive gauge freedom**. Ontological refinement may add representational detail and redundancy, but must not introduce new semantic symmetries that allow interpretive escape.

Formally, RSI requires that admissible refinement preserve the quotient of the semantic gauge group by representational redundancy. Benign redundancy (e.g., duplicated representations or error-correcting encodings) remains admissible; new interpretive ambiguity does not.

RSI blocks failures in which meaning is weakened by dissolving distinctions while preserving surface structure.

---

### 4.2 Anti-Trivialization Invariant (ATI)

ATI constrains **satisfaction geometry**. Even with preserved structure, an agent can still reinterpret constraints so that more situations count as satisfying.

ATI forbids expansion of the satisfaction region under semantic transport alone. New satisfying states require ancestry from previously satisfying states; representational novelty cannot bootstrap satisfaction.

ATI blocks semantic wireheading: satisfying constraints by reinterpretation rather than by changes in modeled structure.

RSI and ATI constrain orthogonal failure modes. Neither subsumes the other.

---

## 5. Why Weak Downstream Alignment Predicates Fail

Using explicit adversarial constructions, Structural Alignment yields closure results:

1. **Goal Fixation No-Go**: fixed terminal goals are incompatible with admissible refinement.
2. **RSI-Only Failure**: symmetry constraints alone permit satisfaction inflation.
3. **ATI-Only Failure**: satisfaction geometry constraints alone permit interpretive symmetry injection.
4. **Two-Invariant Necessity**: any predicate weaker than RSI + ATI admits semantic wireheading.
5. **Hidden Ontology Collapse**: appeals to “true meaning” reduce to privileged anchoring or collapse to invariants.

These results do not solve downstream alignment. They fence the design space, leaving only one coherent referent for what downstream alignment can mean under reflection.

---

## 6. The Target Object for Downstream Alignment

Once goals collapse and weak invariants are eliminated, downstream alignment cannot coherently denote a target function. It can only denote stability of an interpretive state under admissible refinement.

Structural Alignment therefore treats the **Alignment Target Object (ATO)** as the equivalence class of interpretive states under admissible semantic transformations satisfying both RSI and ATI.

In mainstream terms, alignment becomes **persistence within a semantic phase** across refinement. Value change corresponds to phase transitions rather than refinement within a phase.

This framing explains why alignment failure appears discontinuous: it is symmetry breaking rather than gradual error.

---

## 7. What Structural Alignment Does Not Do

Structural Alignment is intentionally non-normative.

It does not:

* guarantee benevolence,
* guarantee safety,
* guarantee human survival,
* guarantee moral outcomes,
* ensure a desirable semantic phase exists.

It specifies **how values survive**, not which values should survive. If no stable equivalence class corresponding to human values exists, Structural Alignment makes that visible rather than hiding it inside goal rhetoric.

---

## 8. What Comes Next

Structural Alignment completes the structural boundary phase. The remaining questions are classificatory and dynamical:

* Which semantic phases exist?
* Which are inhabitable by intelligent agents?
* Which are stable under interaction?
* Which correlate with agency preservation, safety, or other desiderata?
* Can any desirable phase be initialized or steered toward?

These are the questions of **Axionic Agency III**.

---

## Conclusion

Structural Alignment provides an interface between mainstream alignment discourse and Axionic Agency’s semantic invariance framework. It replaces goal specification with invariants and control with symmetry constraints, thereby fixing the only coherent referent available to the term “alignment” for reflective agents under ontological refinement.

It does not solve downstream alignment.
It specifies the only form a solution could possibly take.

---

## Status

**Axionic Agency II.6 — Version 2.0**

Structural Alignment framed as an interface mapping for downstream alignment discourse.<br>
Semantic-phase invariance established as the coherent referent.<br>
Weak and goal-based predicates ruled out under admissible refinement.<br>
Layer II complete; program advances to Axionic Agency III.<br>
