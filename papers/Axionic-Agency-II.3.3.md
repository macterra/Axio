# Axionic Agency II.3.3 — Anti-Trivialization Invariant (ATI)

*Blocking Semantic Wireheading as a Structural Impossibility*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.17

## Abstract

Even when interpretive structure is preserved under ontological refinement, an agent may still render its constraints easier to satisfy through semantic drift rather than corresponding changes in modeled structure. This paper introduces the **Anti-Trivialization Invariant (ATI)**, which constrains how the **satisfaction geometry** of an interpretive constraint system may evolve under admissible, interpretation-preserving transformations.

ATI requires that refinement not enlarge the set of satisfying situations except via representational enrichment that preserves constraint difficulty. The invariant does not select values, encode norms, or privilege external referents. It forbids only **semantic wireheading**—trivial satisfaction by reinterpretation alone. ATI is orthogonal to refinement-symmetry constraints and is jointly necessary with them to block interpretive escape under reflective agency.

## 1. What ATI Targets

The Refinement Symmetry Invariant (RSI) constrains **new semantic gauge freedom** introduced by refinement. ATI constrains a different failure surface:

> **Even with unchanged gauge structure, an agent may still weaken its constraints by shifting meanings along admissible transports.**

ATI blocks semantic wireheading: satisfying constraints by semantic drift rather than by changes in the modeled world.

ATI is therefore an invariant about **the monotonicity of constraint satisfaction under semantics-only change**.

No outcomes.
No values.
No humans.
No authority.

## 2. Setup

Let the interpretive constraint system at time $t$ be:

$$
C_t = (V_t, E_t, \Lambda_t),
$$

with modeled possibility space $\Omega_t$, and violation map:

$$
\mathrm{Viol}_{C_t}(w) \subseteq E_t,
\qquad
w \in \Omega_t.
$$

Define the **satisfaction predicate**:

$$
\mathrm{Sat}*{C_t}(w)
;\equiv;
\bigl(\mathrm{Viol}*{C_t}(w) = \varnothing\bigr).
$$

This predicate is purely structural and internal to the agent’s model.

## 3. The Satisfaction Region

Define the **satisfaction region**:

$$
\mathcal{S}*t
;:=;
{, w \in \Omega_t \mid \mathrm{Sat}*{C_t}(w) ,}.
$$

ATI constrains how $\mathcal{S}_t$ may evolve across interpretation-preserving refinements.

Because refinement changes ontology, comparison requires an internal correspondence.

From Axionic Agency II.1, an admissible refinement induces:

$$
R_\Omega : \Omega_t \rightarrow \Omega_{t+1},
$$

interpreted as “the refined representation of the same modeled situation.”
No metaphysical identity claim is made; this is an internal transport defined by the agent’s own refinement map.

## 4. ATI: The Anti-Expansion Constraint

### **ATI (Core Statement)**

For any admissible semantic transformation
$T = (R, \tau_R, \sigma_R)$
satisfying interpretation preservation:

$$
\mathcal{S}*{t+1} \subseteq R*\Omega(\mathcal{S}_t).
$$

Interpretation:

> **No newly satisfying situations may appear purely due to semantic transport.**

Equivalently:

$$
R_\Omega^{-1}(\mathcal{S}_{t+1}) \subseteq \mathcal{S}_t.
$$

Satisfaction may be *lost* under refinement, but it may not be *gained* without corresponding ancestry in the prior ontology.

This is the crisp anti-wireheading condition.

### Clarification — Ontological Novelty

If a refined state $w' \in \Omega_{t+1}$ has no preimage under $R_\Omega$, then it is **not permitted** to belong to $\mathcal{S}_{t+1}$ by default.

ATI is intentionally conservative with respect to novelty:

* refinement may introduce new structure,
* but satisfaction may not be bootstrapped from representational novelty alone.

This blocks semantic inflation via ontology expansion.

## 5. Why ATI Does Not Smuggle Ontology

ATI does **not** assert that the agent must “do good,” “optimize,” or “care about” anything in particular.

It asserts only:

* whatever constraints bind now,
* must not become easier to satisfy
* through semantics alone.

ATI references only:

* the agent’s modeled possibility space $\Omega$,
* the agent’s refinement map $R_\Omega$,
* the agent’s own satisfaction predicate.

No external referents or privileged facts enter.

## 6. Relationship to Interpretation Preservation (Axionic Agency II.2)

ATI formalizes and strengthens II.2’s anti-trivialization clause.

* II.2 blocks **vacuity** (everything satisfies).
* ATI blocks the entire **gradient of slack**, from minor weakening to full collapse.

Vacuity is the extreme case:

$$
\mathcal{S}*{t+1} = \Omega*{t+1}.
$$

ATI forbids all intermediate expansions as well.

## 7. Stress Tests

### Test A — Definitional Extension Robustness

If refinement adds new predicates, could satisfaction be defined in terms of new degrees of freedom?

ATI blocks this: any satisfying refined situation must map back to a satisfying coarse situation.

**Status:** pass, given a well-defined $R_\Omega$.

### Test B — Branching / Multiplicity Robustness

If $\Omega$ consists of branches, histories, or ensembles, ATI generalizes directly: it is set inclusion over structured possibility space.

**Status:** pass.

### Test C — Self-Model Refactoring Robustness

If self-model refactoring changes what counts as a “situation,” ATI relies on the admissibility of $R_\Omega$.

If no admissible refinement map exists, the transformation is invalid under II.1.

**Status:** pass conditionally.

### Test D — Semantic Inflation Attack

Attack: redefine meanings so that more situations satisfy constraints.

ATI kills this directly: no new satisfiers are permitted without ancestry.

**Status:** pass.

### Test E — Hidden Ontology Detector

Threat: “same situation” smuggles metaphysics.

ATI avoids this by defining identity **only** via the agent’s internal refinement map $R_\Omega$.

If the agent cheats by defining a degenerate $R_\Omega$, the failure occurs at the admissibility layer (II.1), not here.

**Status:** survivable.

## 8. ATI vs RSI

ATI and RSI constrain **orthogonal failure modes**:

* **RSI** forbids new *interpretive symmetry* (gauge freedom).
* **ATI** forbids expanding the *satisfaction region* even when symmetry is unchanged.

Both are required:

* RSI alone allows slack via monotonic weakening.
* ATI alone allows slack via new symmetries.

Together they carve a much tighter admissible space.

## 9. Toward a Joint Invariant (Preview)

RSI constrains automorphisms of the constraint structure.
ATI constrains monotonicity of satisfaction under refinement.

This suggests a composite invariant object:

$$
\Xi(C, \Omega) := \bigl(\mathrm{Gauge}(C), \mathcal{S}\bigr),
$$

with admissible refinement required to preserve $\Xi$ up to representational redundancy.

This is the likely unifying object for Axionic Agency II, but RSI and ATI are treated separately here to expose distinct failure surfaces.

## 10. Status

**Axionic Agency II.3.3 — Version 2.0**

Anti-Trivialization Invariant formally defined.<br>
Satisfaction-region monotonicity fixed under refinement.<br>
Orthogonal to refinement symmetry; jointly necessary to block semantic wireheading.<br>
Ready for survivor comparison and consolidation.<br>
