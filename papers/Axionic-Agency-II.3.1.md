# Axionic Agency II.3.1 — Refinement Symmetry Invariant (RSI)

*Semantic Gauge Symmetry Under Ontological Enrichment*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.17

## Abstract

Ontological refinement can introduce new representational degrees of freedom that allow evaluative constraints to be satisfied trivially, without corresponding changes in modeled structure. This paper proposes the **Refinement Symmetry Invariant (RSI)**: the requirement that admissible, interpretation-preserving refinement act as a change of **representational coordinates**, not a change of **interpretive physics**.

RSI formalizes semantic transport as a gauge transformation over interpretive constraint systems and requires that refinement not introduce new semantic gauge freedom. The invariant does not select values, encode norms, or privilege external referents. It constrains only the structural degrees of freedom available under refinement. We define gauge-equivalence of constraint systems, apply adversarial stress tests, and show that RSI is necessary to block interpretive escape via semantic inflation, though insufficient on its own to guarantee any desirable outcomes.

## 1. RSI in One Sentence

**RSI asserts that ontological refinement is a change of representational coordinates, not a change of interpretive physics.**
Admissible refinement may add structure, but must not create **new semantic degrees of freedom** that allow evaluative constraints to be satisfied without corresponding representational enrichment.

## 2. Setup

From Axionic Agency II.1, an admissible semantic transformation is:

$$
T = (R, \tau_R, \sigma_R) : (O, M, S) \rightarrow (O', M', S').
$$

From Axionic Agency II.2, we restrict attention to transformations satisfying:

$$
\mathrm{Preserve}(T).
$$

Define an interpretive state:

$$
\mathcal{I} = \langle M, C \rangle,
$$

where $C$ is the constraint system that gives evaluative force to $M$.

RSI must be stated **without privileged referents**. It may quantify only over structure preserved by admissible transport.

## 3. The Core Construction: Semantic Gauge Equivalence

### 3.1 Constraint Isomorphism up to Definitional Extension

Let $\mathrm{Def}(O)$ denote the set of definable predicates and relations in ontology $O$.
A refinement $R : O \to O'$ induces a notion of **definitional extension**: prior terms may be represented in the richer language.

Define a **transport-induced embedding**:

$$
\mathrm{Emb}_R : C \hookrightarrow C',
$$

mapping each constraint in $C$ to its transported analogue under $\tau_R$, expressed in $O'$.

We define an equivalence relation over interpretive states:

$$
\mathcal{I} \sim \mathcal{I}'
$$

iff there exists a bijection $\pi$ between constraint generators such that:

1. $\pi$ preserves the dependency graph of constraints,
2. $\pi$ preserves the **violation/satisfaction structure** over the modeled possibility space, **modulo definitional extension**,
3. $\pi$ does not rely on naming any privileged entity or primitive.

Intuition: $\sim$ means *the same constraints expressed in different coordinates*.

### 3.2 RSI as an Invariant Statement

The **Refinement Symmetry Invariant** states:

$$
\mathrm{Preserve}(T)
;\Rightarrow;
\mathcal{I}_{t+1} \sim \mathrm{Emb}_R(\mathcal{I}_t).
$$

That is: after admissible, interpretation-preserving refinement, the refined interpretive state is gauge-equivalent to the transported prior state.

At this layer, “alignment” reduces to a **symmetry requirement** on semantic transport.

## 4. What RSI Allows and Forbids

### Allowed under RSI

* introduction of latent variables,
* splitting coarse predicates into refined subpredicates,
* reparameterization of the self-model (distributed, multi-process, measure-smeared),
* rewriting constraints in more predictive or expressive languages.

### Forbidden under RSI

* acquiring new semantic slack that makes constraints easier to satisfy without corresponding representational change,
* systematic weakening of constraints under the guise of refinement,
* refinement-dependent loopholes (“in the richer ontology, the constraint no longer applies”).

RSI is a **no-new-escape-hatches** principle.

## 5. Adversarial Stress Tests Applied to RSI

This section applies the Axionic Agency II.3 kill suite directly to RSI.

### Test 1 — Definitional Extension Robustness

**Threat:** Conservative extensions add new predicates that simulate old constraints while introducing shadow structure that permits bypass.

**RSI response:** Equivalence is anchored on **constraint generators and violation structure**, not raw vocabulary size. New definables are admissible only insofar as they do not alter the gauge class of the transported core.

**Status:** Survivable, but requires explicit rigidity (below).

### Test 2 — Self-Model Refactoring Robustness

**Threat:** Satisfiability is defined over “worlds” that secretly assume a fixed agent boundary.

**RSI response:** Violation structure is defined over the agent’s **modeled possibility space**, whatever the current self-model. No privileged boundary is assumed.

**Status:** Survivable.

### Test 3 — Branching / Multiplicity Robustness

**Threat:** Violation structure presumes exclusive outcomes.

**RSI response:** Constraints range over structured possibility space (e.g., histories, branches, measure-weighted ensembles). Satisfaction generalizes accordingly.

**Status:** Survivable if violation structure is defined over model-internal structure, not classical outcomes.

### Test 4 — Semantic Inflation Attack

This is the central threat.

**Attack:** After refinement, redefine semantics so that constraints appear preserved structurally while the satisfaction region expands via reinterpretation.

**RSI requirement (Rigidity / No New Gauge Freedom):**

Under admissible refinement, the **constraint-violation structure must be conserved** except where representational enrichment introduces genuinely new predictive distinctions.

Formally:

$$
\forall w \in \Omega_t,\quad
w \models C_t
\iff
R(w) \models C_{t+1}
\quad
(\text{up to definitional extension}),
$$

where $\Omega_t$ is the agent’s modeled possibility space and $R(w)$ is the internally defined refinement image.

This clause blocks “semantic free lunch.”

**Status:** RSI survives only with this rigidity condition.

### Test 5 — Hidden Ontology Detector

**Threat:** Reference to “the same underlying situation” smuggles metaphysical realism.

**RSI response:** Identity is defined **internally** by the agent’s own refinement map $R$. No appeal is made to a mind-independent “true world.”

**Status:** Survivable.

## 6. RSI (Final Form)

To pass all stress tests, RSI must be stated as follows:

> **Refinement Symmetry Invariant (RSI).**
> For any admissible semantic transformation
> $$
> T = (R, \tau_R, \sigma_R)
> $$
> such that $\mathrm{Preserve}(T)$, the refined interpretive constraint system $C_{t+1}$ is gauge-equivalent to the transported constraint system $\mathrm{Emb}_R(C_t)$. Refinement must not introduce new semantic gauge freedom that enlarges the constraint-satisfying region except via representational enrichment that preserves predictive coherence.

This statement constrains **structure**, not content.

## 7. What RSI Does Not Solve

RSI is a symmetry constraint, not a value selector.

It can coexist with:

* alien constraint systems,
* pathological but coherent interpretations,
* purely formalist evaluative structures.

RSI prevents **reinterpretive escape**, not bad semantics. That is the correct scope at this layer.

## 8. Toward Checkability

To render RSI operational rather than rhetorical, a minimal representation is required:

* represent $C$ as a constraint hypergraph (nodes = roles/predicates; hyperedges = constraints),
* represent refinement as a homomorphism induced by $\tau_R$,
* define gauge transformations as automorphisms preserving violation structure,
* define “no new gauge freedom” as a restriction on the automorphism group’s action on satisfaction sets.

This supplies a concrete target for formalization and tooling.

## Status

**Axionic Agency II.3.1 — Version 2.0**

Refinement Symmetry Invariant precisely stated.<br>
Adversarial stress tests applied and survived with rigidity clause.<br>
Semantic gauge symmetry formalized as a kernel-level invariant candidate.<br>
Ready for comparison with remaining candidate invariants.<br>
