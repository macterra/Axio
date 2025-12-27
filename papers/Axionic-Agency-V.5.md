# Axionic Agency V.5 — Dominions: Plurality Without Closure

*Optimal Governance Properties of Federated Virtual Jurisdictions*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.27

## Abstract

This paper analyzes a proposed future social architecture in which agents may create sovereign virtual jurisdictions—here called **Dominions**—admit other agents by invitation and consent, and enforce local rules solely through expulsion. The architecture rejects global value aggregation, enforced coexistence, and normative finality. We show that while such a system does not constitute a utopia under any standard definition, it is *optimal as a governance layer under agency-preserving constraints*. Specifically, it is Pareto-maximal among non-coercive architectures, minimizes structural sacrifice, and remains robust under value drift. The analysis clarifies the domain of these optimality claims, explicitly distinguishing digital governance from physical resource allocation, and specifies the architectural conditions—asset portability and capability isolation—under which expulsion-only enforcement remains viable. The result is a precise characterization of the strongest form of social optimality available once utopia is abandoned.

## 1. Introduction

The incoherence of utopia as a final social design leaves open a constructive question:

> **What kinds of social architectures remain admissible once agency, value drift, and pluralism are taken seriously?**

This paper analyzes a concrete candidate: a federated virtual architecture in which agents inhabit a shared technical substrate while exercising sovereign control over local virtual jurisdictions, hereafter called **Dominions**. Entry into any Dominion is voluntary. Rule enforcement is limited to expulsion. No agent is forced to share a Dominion, value system, or equilibrium.

The claim advanced here is narrow but strong:

> **Among architectures that preserve agency and reject outcome coercion, a system of Federated Virtual Dominions is structurally optimal as a governance layer.**

The paper does *not* claim to solve physical scarcity, biological dependency, or material political economy. It characterizes optimality in the domain where social coordination is digitally mediated.

## 2. Architectural Description

### 2.1 Core Features

The proposed architecture has the following properties:

1. **Dominion Sovereignty**
   Any agent may create a virtual jurisdiction, called a **Dominion** $D_i$, with locally defined rules.

2. **Voluntary Entry**
   Other agents may enter $D_i$ only by invitation and explicit consent to its rules.

3. **Bounded Enforcement**
   Rule violations result only in expulsion from $D_i$. No punishment, fines, or coercive penalties are permitted.

4. **Exit Supremacy**
   Agents retain the unconditional ability to leave any Dominion.

5. **No Global Value Aggregation**
   The system does not rank, optimize, or reconcile Dominion-level value functions.

6. **Thin Substrate**
   A shared infrastructure enforces identity persistence, consent verification, capability isolation, and expulsion, but does not adjudicate values or outcomes.

This defines a **federated, opt-in, expulsion-only governance topology** composed of multiple Dominions.

### 2.2 Asset Portability and Exit Supremacy

Exit supremacy is only meaningful if exit costs remain low.

Accordingly, the architecture requires that:

> **Persistent identity, assets, and reputation are substrate-bound and user-owned, not Dominion-operator-owned.**

Dominions may define local affordances, norms, and rules of interaction, but durable assets must persist across expulsion. If Dominion operators could revoke assets on exit, exit costs would rise and a sacrifice gradient would re-emerge.

Asset portability is therefore not an implementation detail; it is a constitutive requirement for non-coercive governance.

### 2.3 Capability Isolation of Dominions

Dominions are **capability-isolated execution contexts**, not peer sovereigns.

Specifically:

* Dominions do not possess network-addressable access to other Dominions
* Dominions cannot allocate substrate resources beyond assigned quotas
* Dominions cannot write to shared state except through explicit, substrate-mediated bridges

As a result:

> **Inter-Dominion aggression is physically impossible by design, not regulated post hoc.**

This isolation is analogous to process separation in operating systems or object-capability security models. Preventing cross-Dominion interference is a constitutive constraint, not a form of benevolent governance.

## 3. Admissibility Constraints

Let $\mathcal{A}$ denote the set of social architectures satisfying:

* preservation of agentic decision authority,
* allowance for endogenous value drift,
* absence of outcome coercion,
* enforcement limited to constitutive constraints.

Architectures outside $\mathcal{A}$—including enforced coexistence, global norm enforcement, or mandatory value convergence—are excluded *by definition*.

The question addressed here is not whether the proposed system is optimal simpliciter, but whether it is **undominated within $\mathcal{A}$**.

## 4. Pareto Maximality Under Non-Coercion

### 4.1 Claim

The proposed architecture is **Pareto-maximal within $\mathcal{A}$**.

### 4.2 Argument

Consider any alternative architecture $A' \in \mathcal{A}$ that:

* restricts Dominion creation,
* limits exit,
* enforces shared norms, or
* imposes mandatory coexistence across Dominions.

For at least one agent, $A'$ strictly reduces the set of value-consistent trajectories available, while failing to increase any other agent’s attainable value under their own valuation.

No admissible architecture strictly dominates the proposed system.

## 5. Freedom Density Optimality

Define **freedom density** as:

> the measure of distinct value-consistent future trajectories per unit of coercive constraint.

The architecture maximizes freedom density because:

* constraints are localized to voluntary Dominion contexts,
* enforcement is minimal and reversible,
* agents may instantiate arbitrarily divergent norms across Dominions without imposing them on others.

Any architecture that enforces shared Dominions or global outcomes necessarily reduces freedom density by constraining agents whose values diverge.

## 6. Robustness Under Value Drift

Let $U_i(t)$ denote agent $i$’s valuation over time.

The architecture uniquely satisfies the following property:

> For any $i$ and any $t_1 > t_0$, if $U_i(t_1) \neq U_i(t_0)$, there exists a path that does not require reforming or coercing other agents.

This property fails in nation-states, federations, consensus communities, and public-goods-dependent systems.

The system of Federated Virtual Dominions is therefore **drift-optimal**.

## 7. Minimal Sacrifice

### 7.1 Standing Sacrifice

A *standing sacrifice* exists when some agents must endure involuntary deprivation to stabilize a system.

### 7.2 Result

The proposed architecture contains **no standing sacrifice class**.

* Losses are localized to exit costs.
* No agent’s flourishing depends on another’s coerced participation.
* No variance sink is required to maintain equilibrium.

Any architecture that enforces shared outcomes across Dominions must reintroduce sacrifice sinks.

## 8. What the Architecture Does Not Optimize

The system does **not** optimize for:

* shared meaning,
* large-scale coordination,
* public goods,
* epistemic convergence,
* low transaction cost.

These are deliberate exclusions.

Agents who value such goods may instantiate them voluntarily *within* Dominions. The architecture refuses to enforce them globally.

## 9. Substrate Scope and Physical Constraints

The optimality claims advanced here apply to the **governance layer** of digitally mediated interaction.

The architecture does not eliminate:

* physical scarcity,
* energy requirements,
* biological dependency, or
* material political economy.

No governance system can. To the extent that human social, economic, and expressive life is mediated through digital environments, Federated Virtual Dominions minimize coercion *within that domain*. Physical sacrifice patterns may persist elsewhere.

## 10. Relation to Prior Frameworks

This architecture may be read as a **digital instantiation of Robert Nozick’s “framework for utopias”**, updated to enforce exit supremacy, asset portability, and expulsion-only governance in virtual environments.

Unlike Nozick’s rights-based derivation, the present justification rests on agency preservation, non-composability of value, and robustness under drift.

## 11. Conclusion

Once utopia is rejected as incoherent, only constrained optimality remains.

Under the constraints of agency preservation, value drift, non-coercion, asset portability, and capability isolation, a system of Federated Virtual Dominions is:

* Pareto-maximal,
* freedom-density optimal,
* drift-robust,
* sacrifice-minimal,
* and undominated within the admissible design space.

This is the strongest form of optimality available in principle.

The correct ambition is no longer to design a perfect world, but to design a system that **refuses to decide what perfection must be**.

