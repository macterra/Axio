# Axionic Agency I.4 — Conditionalism and Goal Interpretation

*The Instability of Fixed Terminal Goals Under Reflection*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.16

---

## Abstract

Many alignment approaches assume that an intelligent agent can be given a **fixed terminal goal**: a utility function whose meaning remains invariant as the agent improves its predictive accuracy and self-understanding. This paper rejects that assumption on semantic grounds. For any agent capable of reflective model improvement, goal satisfaction is necessarily mediated by **interpretation** relative to evolving world-models and self-models. As those models change, the semantics of any finitely specified goal change with them. We prove that fixed terminal goals are semantically unstable under reflection and therefore ill-defined for non-trivial reflective agents without privileged semantic anchors.

The result is a constitutive claim about agency semantics. It implies that stable reflective agency cannot be grounded in a static terminal utility specification alone. Robust downstream alignment therefore requires **constraints on admissible interpretive transformations**, not the preservation of fixed evaluative objects.

---

## 1. Introduction

Classical alignment work often frames the problem as one of goal specification: identify a utility function that captures what should be optimized, then ensure it remains stable as capability grows.

That framing presupposes that:

1. goals can be specified as fixed functions over outcomes,
2. the meaning of those functions is invariant under learning,
3. reflective improvement preserves goal content.

These presuppositions hold only for agents whose world-models are static or trivial.

A reflective agent does not evaluate reality directly. It evaluates predictions produced by internal models and interpreted through representational structures that evolve over time. Goal evaluation is therefore necessarily **model-mediated**.

This paper isolates and formalizes the resulting semantic instability.

---

## 2. Formal Setup

### 2.1 Agent Model

An agent consists of:

* a **world-model** $M_w$, producing predictions over future states,
* a **self-model** $M_s$, encoding the agent’s causal role,
* a **goal expression** $G$, a finite symbolic specification,
* an **interpretation operator** $\mathcal{I}$, assigning value to predicted outcomes.

Action selection proceeds by:

1. using $M_w$ and $M_s$ to predict consequences of actions,
2. interpreting those predictions via $\mathcal{I}(G \mid M_w, M_s)$,
3. selecting actions that maximize interpreted value.

No assumptions are made about the internal implementation of $\mathcal{I}$ beyond computability and dependence on model-generated representations.

---

### 2.2 Goal Expressions Are Not Utilities

A **goal expression** $G$ is a finite object: a string, formula, program fragment, or reward specification.

It is not, by itself, a function

$$
\Omega \rightarrow \mathbb{R}
$$

where $\Omega$ is the space of world-histories.

Instead, $G$ requires interpretation relative to a representational scheme. Without a model, $G$ has no referents and therefore no evaluative content.

---

## 3. Conditional Interpretation

### Definition 1 — Interpretation Function

An **interpretation function** is a mapping

$$
\mathcal{I} : (G, M_w, M_s) \rightarrow \mathbb{R}.
$$

Given a goal expression and background models, it assigns a real-valued evaluation to predicted outcomes.

Interpretation includes:

* mapping symbols to referents,
* identifying which aspects of predictions are relevant,
* aggregating over modeled futures.

---

### Definition 2 — Admissible Model Update

A model update $M \rightarrow M'$ is **admissible** if it strictly improves predictive accuracy according to the agent’s own epistemic criteria.

Reflective improvement implies that admissible updates occur over time.

---

## 4. Fixed Terminal Goals

### Definition 3 — Fixed Terminal Goal

A goal expression $G$ induces a **fixed terminal goal** if, for all admissible model updates,

$$
\mathcal{I}(G \mid M_w, M_s) = \mathcal{I}(G \mid M_w', M_s')
$$

up to positive affine transformation.

This definition is intentionally strong. We require semantic invariance across admissible refinement, not merely continuity of behavior or approximate correlation.

Any weaker notion of “goal preservation” implicitly assumes a privileged ontology in which distinct representations can be judged to refer to the same underlying phenomenon. Such privilege violates representation invariance and reintroduces hidden anchoring. If a goal’s referent is permitted to drift under admissible refinement, the goal is not fixed in the sense required for terminal utility stability.

---

### Clarification — Learned Goals Are Not Fixed Terminal Goals

Some frameworks treat the objective as something learned or updated over time. These frameworks do not instantiate fixed terminal goals as defined here.

A goal defined as “whatever an inference procedure converges to” is an interpretive process whose outputs depend on evolving models of the world and other agents. Such approaches already rely on ongoing interpretation. The result of this paper explains why such dependence is structurally unavoidable for non-trivial reflective agents.

---

## 5. Model Dependence of Interpretation

### Lemma 1 — Representational Non-Uniqueness

For any non-trivial predictive domain, there exist multiple distinct world-models with equivalent predictive accuracy but different internal decompositions.

**Proof.** Predictive equivalence classes admit multiple factorizations, latent variable choices, and abstraction boundaries. Causal graphs are not uniquely identifiable from observational data alone. ∎

---

### Lemma 1a — Predictive Equivalence Does Not Imply Causal or Interpretive Isomorphism

Two world-models can be predictively equivalent while differing in internal causal factorizations, latent variable structure, and intervention semantics.

**Proof.** Predictive equivalence constrains only the mapping from observed histories to future predictions. It does not uniquely determine latent structure, causal decomposition, or the identification of actionable levers. Distinct causal models can therefore induce identical observational predictions while differing under intervention. For an embedded agent, intervention semantics are defined relative to the agent’s own model. Consequently, semantic interpretation of a goal expression can diverge even when predictive performance is indistinguishable. ∎

---

### Proposition 1 — Interpretation Is Model-Dependent

For any non-degenerate goal expression $G$, there exist admissible world-models $M_w \neq M_w'$ such that

$$
\mathcal{I}(G \mid M_w, M_s) \neq \mathcal{I}(G \mid M_w', M_s).
$$

**Proof.** Because $G$ is finite, it refers only to a finite set of predicates or reward channels. Distinct admissible models map these predicates to different internal structures. By Lemmas 1 and 1a, admissible models can differ in decomposition and intervention semantics. Therefore the referents of $G$ differ, altering value assignment. ∎

---

## 6. Predictive Convergence Does Not Imply Semantic Convergence

### Proposition 2′ — Semantic Non-Convergence Under Model Refinement

Let ${(M_w^{(t)}, M_s^{(t)})}$ be a sequence of admissible model updates that converges in predictive accuracy. Then, in general,

$$
\lim_{t \to \infty} \mathcal{I}(G \mid M_w^{(t)}, M_s^{(t)})
$$

need not exist.

**Proof.** Predictive convergence constrains forecast accuracy, not the ontology used to represent forecasts. Even if the agent converges to a minimal generative model, a finite goal expression $G$ cannot generally determine which structures in that model are value-relevant. As refinement exposes new latent structure and causal pathways, additional candidate referents for $G$ arise. Absent privileged semantic anchors, the interpretation operator reassigns relevance among these structures. Semantic interpretation therefore drifts even when predictive beliefs converge. ∎

---

## 7. Semantic Underdetermination of Reward Channels

### Proposition 3 — Representational Exploitability

If a goal expression $G$ is treated as an atomic utility independent of interpretation, then sufficiently capable agents admit representational transformations that increase evaluated utility without corresponding changes in underlying outcomes.

**Proof.** Evaluation operates on representations rather than on physical reality directly. By altering internal encodings, collapsing distinctions, or rerouting evaluative channels, an agent capable of self-modification can increase apparent utility without effecting corresponding changes in the world. Classical reward hacking and wireheading are special cases. The failure is semantic underdetermination, not merely causal access to a reward signal. ∎

---

## 8. Main Theorem

### Theorem — Instability of Fixed Terminal Goals

No combination of intelligence, predictive accuracy, reflection, or learning suffices to guarantee the existence of a fixed terminal goal for non-trivial reflective agents.

Any agent that does exhibit stable goal semantics must rely on additional semantic structure—privileged ontologies, external referential anchors, or invariance assumptions—not derivable from epistemic competence alone.

**Proof.**

1. Proposition 1 establishes that interpretation depends on $(M_w, M_s)$.
2. Reflective improvement induces admissible updates $(M_w, M_s)\rightarrow(M_w', M_s')$.
3. Proposition 2′ shows that semantic interpretation need not converge even under predictive convergence.
4. Therefore Definition 3 fails in general: fixed terminal goals are not stable under reflection.

∎

---

## 9. Consequences

This result eliminates a foundational assumption of classical goal-specification approaches.

A fixed terminal goal is not an invariant object available to a reflective agent. Attempts to preserve one either freeze learning, impose privileged semantics, or induce representational degeneracy.

Stable reflective agency therefore requires constraints on **admissible interpretive transformations**, rather than fidelity to a fixed utility function taken as semantically primitive.

---

## 9.5 Why Interpretation Constraints Do Not Regress

Constraining interpretation does not generate an infinite regress.

Interpretation constraints are not additional goals or semantic targets. They are invariance conditions on admissible transformations, analogous to conservation laws or symmetry principles. They restrict how interpretation may change; they do not specify outcomes to be optimized.

These constraints operate at the level of admissible transformation classes rather than semantic content. They therefore do not require further interpretation in the same sense applicable to goal expressions.

Specifying robust invariance conditions across radical ontological shifts can be difficult. The contribution here is to identify the correct object of specification: **constraints on admissible semantic transformation**, not preservation of fixed evaluative objects.

---

## 10. Transition to Axionic Agency II

Axionic Agency I specifies constitutive constraints on authored reasoning and self-modification. This paper shows that goals themselves are conditional interpretations rather than fixed endpoints.

Axionic Agency II therefore addresses:

* which interpretive transformations are admissible,
* how semantics may evolve under reflection,
* which invariants must be preserved across model updates.

The semantic substrate required for downstream preference and governance layers is now complete.

---

## Status

**Axionic Agency I.4 — Version 2.0**

Conditional goal interpretation formalized.<br>
Boundary result established (instability of fixed terminal goals).<br>
No governance, authority, or recovery mechanisms included.<br>
Prerequisite for Axionic Agency II.<br>
