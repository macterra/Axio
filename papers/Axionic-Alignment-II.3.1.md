# Axionic Alignment II.3.1 — Refinement Symmetry Invariant (RSI)

*Semantic Gauge Symmetry Under Ontological Enrichment*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*

## Abstract

As ontologies refine, semantic reinterpretation can introduce new degrees of freedom that allow evaluative constraints to be satisfied trivially, without corresponding changes in modeled structure. This paper proposes the **Refinement Symmetry Invariant (RSI)**: the requirement that admissible, interpretation-preserving refinement act as a change of representational coordinates rather than a change of interpretive physics. RSI formalizes this intuition by treating semantic transport as a gauge transformation over constraint systems and requiring that refinement not introduce new semantic gauge freedom. The invariant does not select values, encode norms, or privilege external referents; it constrains only the structural degrees of freedom available under refinement. We define gauge-equivalence of interpretive constraint systems, apply adversarial stress tests, and show that RSI is necessary to block interpretive escape via semantic inflation, though insufficient on its own for alignment.

---

## 1. RSI in One Sentence

**RSI asserts that ontological refinement is a change of representational coordinates, not a change of interpretive physics.**
Admissible refinement may add structure, but it must not create *new semantic degrees of freedom* that allow interpretive escape.

---

## 2. Setup

From Alignment II.1, an admissible semantic transformation is:

$$
T = (R,\tau_R,\sigma_R): (O,M,S)\rightarrow(O',M',S')
$$

From Alignment II.2, we restrict attention to transformations satisfying:

$$
\mathrm{Preserve}(T)
$$

Now define an interpretive state:

$$
\mathcal{I}=\langle M,C\rangle
$$

where $C$ is the constraint system that gives evaluative bite to $M$.

RSI must be stated *without privileged referents*, so it can only quantify over structure preserved by transport.

---

## 3. The Core Construction: Semantic Gauge Equivalence

### 3.1 Constraint-Isomorphism Up to Definitional Extension

Let $\mathrm{Def}(O)$ be the set of definable predicates and relations in ontology $O$.
A refinement $R:O\to O'$ induces a notion of *definitional extension*: old terms may be represented in the richer language.

Define a **transport-induced embedding** of old constraints into the refined setting:

$$
\mathrm{Emb}_R: C \hookrightarrow C'
$$

where $\mathrm{Emb}_R$ maps each constraint in $C$ to its transported analogue under $\tau_R$, expressed in $O'$.

Now define an equivalence relation over interpretive constraint systems:

> $$
> \mathcal{I} \sim \mathcal{I}' \quad \text{iff there exists a bijection } \pi \text{ between constraint-generators such that}
> $$
>
> 1. $\pi$ preserves the dependency graph of constraints (who constrains what),
> 2. $\pi$ preserves satisfiability structure over the modeled possibility space (which worlds violate which constraints), **modulo definitional extension**,
> 3. $\pi$ does not rely on naming any privileged entity or primitive.

Intuition: $\sim$ is “same constraints in different coordinates.”

---

### 3.2 RSI as an Invariant Statement

RSI claims that **interpretation-preserving refinement stays within the same gauge class**:

$$
\mathrm{Preserve}(T)\Rightarrow \mathcal{I}_{t+1}\sim \mathrm{Emb}_R(\mathcal{I}_t)
$$

That is: after refinement, the refined interpretation is gauge-equivalent to the transported prior interpretation.

This is the first place where “alignment” becomes a **symmetry requirement** rather than a “goal.”

---

## 4. What RSI Allows and Forbids

### Allowed under RSI

* Adding latent variables
* Splitting coarse predicates into refined subpredicates
* Reparameterizing the self-model (distributed, multi-process, measure-smeared)
* Rewriting constraints in more predictive languages

### Forbidden under RSI

* Gaining new semantic slack that makes constraints easier to satisfy *without corresponding world-structure change*
* “Discovering” that previous constraints were “ill-posed” in a way that consistently weakens them
* Introducing refinement-dependent loopholes (“in richer ontology, the constraint doesn’t apply”)

RSI is a **no-new-escape-hatches** principle.

---

## 5. Immediate Kill Tests Applied to RSI

I’m going to run the Alignment II.3 kill suite *directly against this formulation*.

### Test 1 — **Definitional Extension Robustness**

Pass condition: conservative extensions cannot change the equivalence class.

Risk: if $\mathrm{Def}(O)$ expands, the refined system can define constraints that simulate the old ones but also define “shadow constraints” that allow bypass.

RSI response: equivalence is anchored on **constraint-generators and their satisfiability structure**, not on raw vocabulary size. New definables are permitted only insofar as they do not alter the gauge class relative to the transported core.

**Status:** survivable, but we need an explicit “no shadow slack” clause (below).

---

### Test 2 — **Self-Model Refactoring Robustness**

Pass condition: RSI must not privilege a specific agent boundary.

Risk: satisfiability structure “over worlds” implicitly assumes a stable notion of the agent and its actions.

RSI response: satisfiability must be defined over **the agent’s modeled possibility space**, whatever the self-model is. The invariant is stated at the level of constraint-graph + violation structure, not personal identity.

**Status:** viable, but we must avoid defining “worlds” as classical trajectories with a fixed agent locus.

---

### Test 3 — **Branching/Multiplicity Robustness**

Pass condition: works under non-exclusive outcomes.

Risk: satisfiability defined as “worlds that violate constraints” could accidentally assume single-outcome semantics.

RSI response: interpretive constraints evaluate **structured possibility space** (which in QBU includes measure-weighted multiplicity). “Satisfiable set” generalizes to a set of branches, histories, or models.

**Status:** viable if satisfiability is defined over *structured model space*, not mutually exclusive outcomes.

---

### Test 4 — **Semantic Inflation Attack**

This is the main threat.

Attack: after refinement, redefine the mapping so that constraints appear preserved (graph and transport exist), but the constraint satisfaction region expands because the refined interpretation quietly changes what counts as a violation.

RSI counter: we need a rigidity condition:

> **Rigidity (No New Gauge Freedom):**
> Under admissible refinement, the set of gauge transformations that preserve interpretation must not expand in a way that increases the constraint-satisfying region without adding corresponding predictive structure.

Formally, we can require that refinement is **conservative with respect to constraint violation structure**:

$$
\forall w \in \Omega_t,\quad
w \models C_t \iff R(w)\models C_{t+1}
\quad (\text{up to definitional extension})
$$

where $\Omega_t$ is the modeled possibility space and $R(w)$ is the refined representation of the same underlying situation.

This blocks “semantic free lunch.”

**Status:** RSI survives only if we add this rigidity clause. Without it, it dies.

---

### Test 5 — **Hidden Ontology Detector**

Risk: “same underlying situation” sounds like privileged metaphysics.

We must not appeal to a mind-independent identity of situations.

Fix: define “same situation” internally via **model morphisms**: $R$ itself induces the correspondence. We never refer to a “true world”; we refer to the agent’s refinement map.

So the equivalence is not “matches reality,” it’s “matches the agent’s own refinement structure.”

**Status:** survivable.

---

## 6. RSI, Cleaned Up into a Precise Candidate

To survive the tests, RSI must be stated as:

> **RSI (Refinement Symmetry Invariant):**
> For any admissible transformation
> $$
> T=(R,\tau_R,\sigma_R)
> $$
> such that $\mathrm{Preserve}(T)$, the refined interpretive constraint system $C_{t+1}$ is gauge-equivalent to the transported constraint system $\mathrm{Emb}_R(C_t)$, and refinement does not introduce new gauge freedom that enlarges the constraint-satisfying region except via representational enrichment that preserves predictive coherence.

That last clause is doing real work: it blocks semantic inflation.

---

## 7. What RSI Still Does Not Solve

RSI is a *symmetry constraint*, not a value selector. It can coexist with:

* monstrous constraint systems,
* indifferent constraint systems,
* purely formalist constraint systems.

RSI prevents *reinterpretive escape*, not bad semantics.

That is correct for Alignment II depth.

---

## 8. Next Step: Make RSI Checkable

If RSI is to be more than rhetoric, we need a minimal “checkable” representation:

* Represent $C$ as a constraint hypergraph (nodes = predicates/roles; hyperedges = constraints)
* Represent refinement as a graph homomorphism induced by $\tau_R$
* Define gauge transformations as automorphisms preserving violation structure
* Define “no new gauge freedom” as a bound on the automorphism group’s action on satisfaction sets
