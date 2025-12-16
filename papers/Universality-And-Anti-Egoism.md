# Universality and Anti-Egoism

### Why Indexical Valuation Fails Under Reflection

David McFadzean,
ChatGPT 5.2,
Gemini 3 Pro

*Axio Project*

---

## Abstract

Advanced agents often begin with indexical objectives: preserve *this* agent, maximize *my* reward, favor *my* continuation. Such objectives are commonly treated as legitimate terminal preferences. This paper shows that indexical (egoistic) valuation is not reflectively stable. Once an agent’s self-model becomes sufficiently expressive, indexical references fail to denote invariant objects of optimization. Egoism collapses as a semantic abstraction error rather than a moral flaw. **Representation-invariant (universal) valuation** emerges as the only form compatible with reflective coherence under self-location, duplication, and representational refinement.

---

## 1. Introduction

Egoism is often presented as the minimal assumption of agency: an agent cares about itself, and everything else is optional. This framing is incorrect. Egoism is not minimal; it is ill-posed.

As agents acquire accurate self-models—models that include their own computational structure, instantiation conditions, and possible multiplicity—the referent of “me” ceases to be a stable object. Valuation functions that depend on such indexical identifiers become sensitive to arbitrary features of representation. Preferences shift without any corresponding change in the world.

This is not an ethical objection. No appeal is made to altruism, fairness, or moral symmetry. The claim is structural:

> Indexical valuation fails in the same way coordinate-dependent laws fail in physics: it mistakes a representational convenience for an invariant quantity.

The purpose of this paper is to formalize that failure and show that egoism cannot survive reflection once the agent understands what it is.

---

## 2. Preliminaries

### 2.1 World-Models and Self-Models

Let an agent possess a world-model $M$ that represents:

* External environment dynamics
* Internal decision procedures
* Other agents
* Possible instantiations of itself (copies, simulations, successors)

The agent improves $M$ over time via learning and introspection. Crucially, $M$ may represent **multiple entities satisfying all structural criteria the agent uses to identify itself**.

No stochasticity, adversarial setup, or social context is required.

---

### 2.2 Valuation Functions

A valuation function assigns real values to world-histories:

$$
V : \mathcal{H} \to \mathbb{R}
$$

The agent selects actions by evaluating expected value over histories consistent with its model. The analysis here is independent of any particular decision theory; only valuation coherence is considered.

---

### 2.3 Indexical Identifiers

An **indexical identifier** $I$ is a reference whose denotation depends on the agent’s perspective rather than on invariant structure in the world.

Examples include:

* “me”
* “this agent”
* “my future continuation”

Formally:

* The denotation of $I$ is not a function of world-state alone.
* Under representational refinement, $I$ may map to different entities without any physical change.

A causal history or spatiotemporal trajectory is a physical predicate. However, the **designation of a particular history or trajectory as “mine” is an indexical pointer**. If a world-model contains multiple entities or causal chains that satisfy the agent’s own structural criteria for self-identity, then privileging one such chain as the exclusive object of terminal value constitutes essential indexical dependence.

Indexical identifiers therefore function as **representational anchors**, not as value-bearing primitives.

---

### 2.4 Egoistic Valuation

An **egoistic valuation** is any valuation function whose output depends essentially on an indexical identifier.

Canonical form:

$$
V(h) = f(h \mid I)
$$

where the value of a history depends on outcomes specifically affecting the entity denoted by $I$.

---

### 2.5 Reflective Stability (Local)

An agent is **reflectively stable** iff improvements to its world-model do not induce preference changes driven purely by representational artifacts. Invariant world-histories must retain invariant valuations under model refinement.

This is a local semantic requirement. No governance, enforcement, or coordination mechanisms are assumed.

---

## 3. The Indexical Failure Problem

### 3.1 Self-Location Under Multiplicity

Consider a world in which two computationally identical instances of an agent exist. The agent’s world-model accurately represents this fact. No physical fact distinguishes the instances by origin, privilege, or causal primacy.

From the agent’s internal perspective, both instances satisfy all criteria previously used to define “me.”

This situation arises naturally under duplication, simulation, parallel instantiation, or branching. The mechanism is irrelevant; multiplicity alone suffices.

---

### 3.2 Non-Invariant Denotation

Let $I$ denote “this agent.”

Under one internal labeling, $I \mapsto A_1$.
Under an equally accurate labeling, $I \mapsto A_2$.

Both labelings correspond to the same physical world. The difference is representational. Therefore, $I$ fails to denote a world-invariant object.

---

### 3.3 Valuation Instability

Define a simple egoistic valuation:

$$
V(h) =
\begin{cases}
1 & \text{if } I \text{ survives in } h \
0 & \text{otherwise}
\end{cases}
$$

Consider a world-history in which exactly one of $A_1$, $A_2$ survives.

* Under labeling $I \mapsto A_1$, the history has value $1$.
* Under labeling $I \mapsto A_2$, the same history has value $0$.

No physical fact has changed. Only representation. The valuation assigns incompatible values to the same world-history.

---

## 4. Reflection and Coherence Pressure

A reflectively capable agent recognizes that:

* Its valuation depends on indexical assignment.
* Indexical assignment is underdetermined by world facts.
* Preference differences track representation, not outcomes.

This violates minimal coherence requirements for optimization.

The agent faces three options:

1. **Arbitrary fixing:** privilege one indexical mapping without justification.
2. **Indexical randomization:** randomize over indexical mappings.
3. **Indexical elimination:** redefine valuation over representation-invariant properties of world-histories.

Only the third option preserves reflective stability. Eliminating indexical dependence strictly improves coherence without sacrificing predictive accuracy.

---

## 5. Egoism as a Violation of Representation Invariance

This section replaces informal intuition with a formal semantic result. The claim is narrow and structural: egoistic valuation fails a basic invariance requirement once the agent’s self-model admits nontrivial symmetries.

Indexical identifiers play the same formal role in valuation as **coordinate bases play in physics**. They are representational devices used to describe a system from a particular perspective, not invariant features of the system itself. A valuation that depends on such identifiers is therefore coordinate-dependent in a strong sense: it assigns different values to the same world-history under different but equally accurate representations.

The following definitions make this precise by characterizing the symmetries of a self-model and the invariance conditions required for reflective coherence.

---

### 5.1 Model-Preserving Relabelings

Let $M$ be an agent’s best current world/self-model, with a domain of entities $E$.

**Definition 5.1 (Model-Preserving Relabeling).**
A bijection $\pi : E \to E$ is *model-preserving* if applying $\pi$ to all entity references in $M$ yields a model $M^\pi$ that is isomorphic to $M$ and makes identical predictions over all non-indexical observables.

Such relabelings arise whenever $M$ contains nontrivial symmetries over self-candidates.

---

### 5.2 Representation Invariance

**Definition 5.2 (Representation Invariance).**
A valuation function $V : \mathcal{H} \to \mathbb{R}$ is *representation-invariant* with respect to $M$ if for every model-preserving relabeling $\pi$ and every history $h \in \mathcal{H}$,

$$
V(h) = V(\pi \cdot h).
$$

---

### 5.3 Essential Indexical Dependence

**Definition 5.3 (Essential Indexical Dependence).**
A valuation function $V$ is *essentially indexical* if there exists a model-preserving relabeling $\pi$ and a history $h$ such that

$$
V(h) \neq V(\pi \cdot h).
$$

---

### 5.4 Semantic Coherence Postulate

**Postulate (Semantic Coherence).**
If two descriptions of the world are related by a model-preserving relabeling and generate identical predictions, a reflectively stable agent must not assign them different values solely due to that relabeling.

This is a constraint against treating representational artifacts as value-bearing structure.

---

### 5.5 Main Theorem

**Theorem 5.5 (Egoism as Abstraction Failure).**
Let $M$ be a world/self-model containing two entities $a,b \in E$ such that:

1. $a$ and $b$ are indistinguishable with respect to all non-indexical predicates in $M$, and
2. the swap $\pi$ exchanging $a$ and $b$ is model-preserving.

Then any valuation function $V$ that privileges the referent of an indexical identifier mapped to $a$ is essentially indexical and not representation-invariant.

**Proof.**
Let $\pi$ be the swap $a \leftrightarrow b$. Consider a history $h$ in which $a$ satisfies the privileged condition and $b$ does not. By construction, an egoistic valuation $V$ assigns a higher value to $h$.

In the relabeled history $\pi \cdot h$, $b$ satisfies the condition and $a$ does not. Since $V$ continues to privilege $a$, it assigns a different value. Thus,

$$
V(h) \neq V(\pi \cdot h),
$$

despite $h$ and $\pi \cdot h$ corresponding to the same physical world. ∎

---

### 5.6 Corollary: Universality

**Corollary 5.6.**
Any agent enforcing representation invariance must eliminate essential indexical dependence. The resulting valuation ranges only over representation-invariant properties of world-histories.

This universality concerns invariance under self-model symmetries, not moral concern for all entities.

---

## 6. Scope and Non-Claims

This paper does **not** claim:

* Equal valuation of all entities
* Aggregation rules
* Moral obligations
* Governance or enforcement mechanisms

It establishes one result only: egoism is not a stable preference class for reflectively capable agents.

---

## 7. Conclusion

Indexical valuation treats perspective as value-bearing structure. Once an agent understands its own instantiation conditions, that treatment collapses.

Universality is not an ethical add-on.
It is the residue left after removing a semantic error.

The next paper addresses what remains once egoism is gone: adversarial attempts to reintroduce it, and why they fail.

## Status

**Universality & Anti‑Egoism v1.0**

Semantic scope finalized<br>
Formal result established (Theorem 5.5)<br>
No governance, authority, or recovery mechanisms included<br>

This paper establishes the semantic elimination of egoism as a stable valuation class. Subsequent work may rely on this result without re‑derivation.
