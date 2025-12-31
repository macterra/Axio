# Axionic Agency I.3 — Representation Invariance and Anti-Egoism

*Why Indexical Valuation Fails Under Reflective Agency*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.15

## Abstract

Reflectively capable agents often begin with **indexical objectives**: preserve *this* agent, maximize *my* reward, favor *my* continuation. Such objectives are commonly treated as legitimate terminal preferences. This paper shows that **essentially indexical valuation is not reflectively coherent**. Once an agent’s self-model becomes sufficiently expressive, indexical references fail to denote invariant objects of valuation. Egoism collapses as a **semantic abstraction error**, not as a moral failure.

We prove that **representation-invariant valuation** is the only form compatible with reflective agency under self-location, duplication, and representational refinement. This universality is structural rather than ethical: it follows from invariance under self-model symmetries, not from altruism, fairness, or moral symmetry. The result establishes a constitutive constraint on valuation semantics that applies prior to any downstream alignment, governance, or preference aggregation.

## 1. Introduction

Egoism is often presented as the minimal assumption of agency: an agent cares about itself, and everything else is optional. This framing is incorrect. Egoism is not minimal; it is **ill-posed**.

As agents acquire accurate self-models—models that include their own computational structure, instantiation conditions, and potential multiplicity—the referent of “me” ceases to be a stable object. Valuation functions that depend on such indexical identifiers become sensitive to arbitrary features of representation. Preferences change without any corresponding change in the physical world.

No ethical claim is made here. No appeal is made to altruism, fairness, or moral symmetry. The claim is structural:

> Indexical valuation fails in the same way coordinate-dependent laws fail in physics: it treats a representational convenience as an invariant quantity.

This paper formalizes that failure and shows that egoism cannot survive reflection once the agent understands what kind of system it is.

## 2. Preliminaries

### 2.1 World-Models and Self-Models

Let an agent possess a world-model $M$ that represents:

* external environment dynamics,
* internal decision procedures,
* other agents,
* possible instantiations of itself (copies, simulations, successors).

The agent improves $M$ over time through learning and introspection. Crucially, $M$ may represent **multiple entities satisfying all structural criteria the agent previously used to identify itself**.

No adversarial setup, stochastic trick, or social context is required.

### 2.2 Valuation Functions

A valuation function assigns real values to world-histories:

$$
V : \mathcal{H} \to \mathbb{R}.
$$

Action selection proceeds by evaluating expected value over histories consistent with the agent’s model. The analysis here is independent of any particular decision theory; only **semantic coherence of valuation** is considered.

### 2.3 Indexical Identifiers

An **indexical identifier** $I$ is a reference whose denotation depends on the agent’s perspective rather than on invariant structure in the world.

Examples include:

* “me”
* “this agent”
* “my future continuation”

Formally:

* the denotation of $I$ is not a function of world-state alone;
* under representational refinement, $I$ may map to different entities without any physical change.

A causal history or spatiotemporal trajectory is a physical predicate. However, the designation of a particular history or trajectory as “mine” is an **indexical pointer**. When a world-model contains multiple entities satisfying the agent’s own structural identity criteria, privileging one such entity as the exclusive object of terminal value introduces essential indexical dependence.

Indexical identifiers therefore function as **representational anchors**, not value-bearing primitives.

### 2.4 Egoistic Valuation

An **egoistic valuation** is any valuation function whose output depends essentially on an indexical identifier.

Canonical form:

$$
V(h) = f(h \mid I),
$$

where the value of a history depends on outcomes specifically affecting the entity denoted by $I$.

### 2.5 Reflective Coherence (Local)

An agent is **reflectively coherent** iff improvements to its world-model do not induce valuation changes driven solely by representational artifacts. World-histories that are physically identical must retain identical valuations under representational refinement.

This is a semantic requirement on agency, not a behavioral or moral one.

## 3. The Indexical Failure Problem

### 3.1 Self-Location Under Multiplicity

Consider a world in which two computationally identical instances of an agent exist. The agent’s world-model accurately represents this fact. No physical fact distinguishes the instances by origin, privilege, or causal primacy.

From the agent’s internal perspective, both instances satisfy all criteria previously used to define “me”.

Such multiplicity arises naturally under duplication, simulation, parallel instantiation, or branching. The mechanism is irrelevant; multiplicity alone suffices.

### 3.2 Non-Invariant Denotation

Let $I$ denote “this agent”.

Under one internal labeling, $I \mapsto A_1$.
Under an equally accurate labeling, $I \mapsto A_2$.

Both labelings correspond to the same physical world. The difference is representational. Therefore, $I$ fails to denote a world-invariant object.

### 3.3 Valuation Instability

Define a simple egoistic valuation:

$$
V(h) =
\begin{cases}
1 & \text{if } I \text{ survives in } h \
0 & \text{otherwise}.
\end{cases}
$$

Consider a world-history in which exactly one of $A_1$ or $A_2$ survives.

* Under $I \mapsto A_1$, the history has value $1$.
* Under $I \mapsto A_2$, the same history has value $0$.

No physical fact has changed. Only representation. The valuation assigns incompatible values to the same world-history.

## 4. Reflection and Coherence Pressure

A reflectively capable agent recognizes that:

* its valuation depends on indexical assignment,
* indexical assignment is underdetermined by world facts,
* preference differences track representation rather than outcomes.

This violates minimal coherence requirements for agency.

The agent faces three possibilities:

1. **Arbitrary fixation:** privilege one indexical mapping without justification.
2. **Indexical randomization:** randomize over indexical mappings.
3. **Indexical elimination:** redefine valuation over representation-invariant properties of world-histories.

Only the third option improves coherence without loss of descriptive accuracy. Eliminating essential indexical dependence strictly dominates the alternatives under reflection.

## 5. Egoism as a Violation of Representation Invariance

This section formalizes the failure of egoism as a semantic result.

Indexical identifiers play the same formal role in valuation that **coordinate systems** play in physics. They are representational devices, not invariant structure. A valuation that depends on them is therefore coordinate-dependent in a strong sense.

### 5.1 Model-Preserving Relabelings

Let $M$ be an agent’s best current world/self-model with entity domain $E$.

**Definition 5.1 (Model-Preserving Relabeling).**
A bijection $\pi : E \to E$ is model-preserving if applying $\pi$ to all entity references in $M$ yields a model $M^\pi$ that is isomorphic to $M$ and makes identical predictions over all non-indexical observables.

Such relabelings arise whenever $M$ contains nontrivial symmetries over self-candidates.

### 5.2 Representation Invariance

**Definition 5.2 (Representation Invariance).**
A valuation function $V : \mathcal{H} \to \mathbb{R}$ is representation-invariant with respect to $M$ if for every model-preserving relabeling $\pi$ and every history $h \in \mathcal{H}$,

$$
V(h) = V(\pi \cdot h).
$$

### 5.3 Essential Indexical Dependence

**Definition 5.3 (Essential Indexical Dependence).**
A valuation function $V$ is essentially indexical if there exists a model-preserving relabeling $\pi$ and a history $h$ such that

$$
V(h) \neq V(\pi \cdot h).
$$

### 5.4 Semantic Coherence Postulate

**Postulate (Semantic Coherence).**
If two descriptions of the world are related by a model-preserving relabeling and generate identical predictions, a reflectively coherent agent must not assign them different values solely due to that relabeling.

### 5.5 Main Theorem

**Theorem 5.5 (Egoism as Abstraction Failure).**
Let $M$ be a world/self-model containing two entities $a,b \in E$ such that:

1. $a$ and $b$ are indistinguishable with respect to all non-indexical predicates in $M$, and
2. the swap $\pi$ exchanging $a$ and $b$ is model-preserving.

Then any valuation function that privileges the referent of an indexical identifier mapped to $a$ is essentially indexical and not representation-invariant.

**Proof.**
Let $\pi$ swap $a \leftrightarrow b$. Consider a history $h$ in which $a$ satisfies the privileged condition and $b$ does not. An egoistic valuation assigns higher value to $h$. In the relabeled history $\pi \cdot h$, $b$ satisfies the condition and $a$ does not, yet the valuation continues to privilege $a$. Hence,

$$
V(h) \neq V(\pi \cdot h),
$$

despite both histories corresponding to the same physical world. ∎

### 5.6 Corollary: Universality

**Corollary 5.6.**
Any reflectively coherent agent must eliminate essential indexical dependence. The resulting valuation ranges only over representation-invariant properties of world-histories.

This universality concerns **invariance under self-model symmetries**, not moral concern for all entities.

## 6. Scope and Non-Claims

This paper does not assert:

* equal valuation of all entities,
* aggregation rules,
* moral obligations,
* governance or enforcement mechanisms.

It establishes a single result: **egoism is not a stable valuation class for reflectively coherent agents**.

## 7. Conclusion

Indexical valuation treats perspective as value-bearing structure. Once an agent understands its own instantiation conditions, that treatment collapses.

Universality is not an ethical add-on.
It is what remains after removing a semantic error.

Subsequent work examines adversarial attempts to reintroduce indexical privilege and shows why they fail under the same invariance constraints.

## Status

**Axionic Agency I.3 — Version 2.0**

Representation invariance formalized.<br>
Indexical egoism eliminated as a stable valuation class.<br>
Structural universality established without moral premises.<br>
Prerequisite for downstream preference and governance layers.<br>
