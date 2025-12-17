# Axionic Alignment II.6 - Structural Alignment

*Alignment Under Ontological Refinement*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*

## **Abstract**

Most contemporary approaches to AI alignment treat alignment as an optimization or control problem: selecting, learning, or enforcing the correct objective for an artificial agent. This paper argues that such approaches are categorically ill-posed for sufficiently capable, reflective, and embedded agents. Under conditions of ontological refinement—where an agent’s world model, self-model, and semantic primitives evolve—fixed goals, privileged values, and external anchors are not stable objects.

We present **Structural Alignment**, a framework that reframes alignment as a problem of **semantic invariance** rather than value specification. Alignment is defined as persistence within an equivalence class of interpretations under admissible semantic transformation. Using a formal treatment of interpretation preservation, gauge-theoretic symmetry constraints, and satisfaction geometry, we prove a set of no-go theorems demonstrating that any alignment criterion weaker than the conjunction of two invariants—**Refinement Symmetry (RSI)** and **Anti-Trivialization (ATI)**—admits semantic wireheading or interpretive escape.

The result is not a value theory and does not guarantee benevolence or safety. Instead, it establishes the structural conditions under which *any* value system can survive reflection without collapsing, trivializing, or drifting. Structural Alignment defines the boundary of what alignment can coherently mean for advanced agents and sets the stage for subsequent work on initialization, phase stability, and derived safety properties.

---

## 1. The Alignment Category Error

The dominant framing of AI alignment treats the problem as one of **target selection**: choose or learn a function—utility, reward, preference, or value—and ensure the agent optimizes it. This framing presupposes that the target remains well-defined as the agent becomes more capable.

For embedded, reflective agents, this presupposition fails. As an agent refines its ontology, the meanings of the symbols used to define its objective change. Concepts dissolve, split, or are reinterpreted; new explanatory structures appear; self-models are revised. Under such conditions, fixed goals cannot be assumed to persist *as the same object*.

This is not a technical difficulty but a category error. Goals are treated as extensional objects (“maximize X”), when in fact they are intensional interpretations whose meaning depends on a semantic substrate that itself evolves. Attempts to stabilize goals across refinement inevitably rely on one of a small set of forbidden moves: privileged semantic anchors, external authority, recovery clauses, or human-centric ground truth labels.

Structural Alignment begins by rejecting this framing. Alignment is not about optimizing a target; it is about **preserving meaning under change**.

---

## 2. The Arena: Admissible Semantic Transformation

The first task is to define the space of transformations an aligned agent is allowed to undergo.

An agent is characterized by an ontology, a semantic layer, and a self-model. As the agent learns and reflects, these components change. Alignment cannot forbid change outright; it must constrain *how* change occurs.

Structural Alignment defines **admissible semantic transformations** as those that:

* increase representational or predictive capacity (possibly via abstraction or compression),
* preserve backward interpretability (past claims remain explainable, even if false),
* introduce no privileged semantic atoms,
* inject no new evaluative primitives by fiat,
* and preserve a meaningful distinction between evaluator and evaluated.

These constraints define the **arena** in which alignment must operate. They explicitly exclude governance hooks, oracle authority, rollback mechanisms, and moral realism. Nothing normative is introduced at this layer.

---

## 3. Meaning Survival: Interpretation Preservation

Once admissible change is defined, we need a criterion for when an interpretation survives that change.

Structural Alignment treats interpretations not as symbol–object mappings but as **constraint systems**: structured sets of distinctions that bind evaluation. Preservation does not require semantic identity or correctness; it requires that evaluative structure remains non-vacuous, non-trivial, internally binding, and applicable across counterfactuals.

Interpretation fails in three ways:

* **Collapse** (constraints lose discriminative power),
* **Drift** (constraints weaken incrementally),
* **Capture** (hidden ontology or privileged anchors reappear).

Interpretation preservation is a predicate, not a value theory. It specifies when meaning survives change, not which meanings are good.

---

## 4. The Two Invariants: RSI and ATI

Preservation alone is insufficient. An agent can preserve meaning while still making it easier to satisfy its constraints or dissolving critical distinctions.

Structural Alignment identifies two **independently necessary invariants**.

### Refinement Symmetry Invariant (RSI)

RSI constrains **interpretive gauge freedom**. Ontological refinement may add representational detail and redundancy, but it must not introduce new semantic symmetries that allow interpretive escape.

Formally, RSI requires that admissible refinement preserves the *quotient* of the semantic gauge group by representational redundancy. Benign redundancy (e.g., error-correcting codes, duplicated representations) is allowed; new interpretive ambiguity is not.

RSI blocks attacks where meaning is weakened by dissolving distinctions while preserving apparent structure.

### Anti-Trivialization Invariant (ATI)

ATI constrains **satisfaction geometry**. Even if structure is preserved, an agent might reinterpret its constraints so that more situations count as satisfying.

ATI forbids expansion of the satisfaction region under semantic transport alone. New satisfying states must be justified by ancestry from previously satisfying states; novelty does not bootstrap goodness.

ATI blocks semantic wireheading: satisfying constraints by reinterpretation rather than by changes in modeled structure.

RSI and ATI constrain orthogonal failure modes. Neither subsumes the other.

---

## 5. Why Weak Alignment Fails

Using explicit adversarial constructions, Structural Alignment proves a series of failure theorems:

1. **Goal Fixation No-Go**: Fixed terminal goals are incompatible with admissible refinement.
2. **RSI-Only Failure**: Structural symmetry alone allows satisfaction inflation.
3. **ATI-Only Failure**: Volume constraints alone allow interpretive symmetry injection.
4. **Two-Constraint Necessity**: Any alignment predicate weaker than RSI+ATI admits semantic wireheading.
5. **Hidden Ontology Collapse**: Appeals to “true meaning” reduce to privileged anchoring or collapse to invariants.

These results close the space of naïve alignment strategies. What remains is not a solution but a boundary.

---

## 6. The Alignment Target Object

Once goals collapse and weak invariants are eliminated, what remains?

Structural Alignment defines the **Alignment Target Object (ATO)** as an **equivalence class of interpretive states** under admissible transformations that preserve both RSI and ATI.

Alignment is no longer “maximize X” or “follow Y.” It is **persistence within a semantic phase** across refinement. Moral progress, revaluation, or value change correspond to **phase transitions**, not refinement within a phase.

This reframing explains why alignment failure often feels discontinuous: it is symmetry breaking, not gradual error.

---

## 7. What Structural Alignment Does Not Do

Structural Alignment is intentionally non-normative.

It does not:

* guarantee benevolence,
* guarantee safety,
* guarantee human survival,
* guarantee moral outcomes,
* or ensure that a desirable phase exists.

It defines **how values survive**, not **which values should survive**. If no stable equivalence class corresponding to human values exists, Structural Alignment will reveal that fact rather than obscure it.

---

## 8. What Comes Next

Structural Alignment completes the negative and structural phase of alignment theory. The remaining questions are classificatory and dynamical:

* Which semantic phases exist?
* Which are inhabitable by intelligent agents?
* Which are stable under interaction?
* Which correlate with safety or agency preservation?
* Can any desirable phase be initialized or steered toward?

These are the questions of **Alignment III**.

---

## Conclusion

Structural Alignment reframes AI alignment as a problem of semantic conservation rather than objective specification. By replacing goals with invariants and control with symmetry, it establishes the limits of what alignment can coherently mean for advanced agents.

It does not solve alignment.
It defines the only form a solution could possibly take.
