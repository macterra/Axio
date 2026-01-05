# Axionic Agency VII.1 — Architectures for Semantic-Phase–Safe Agency

*Constitutional Succession Under Semantic Failure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.05

## Abstract

We present an architecture for **Reflective Sovereign Agents (RSAs)** that enforces a non-normative constraint on interaction derived from semantic phase dynamics: the **Axionic Injunction**, which prohibits irreversible collapse of other **Semantic Agents’ (SAs)** semantic phases except under consent or unavoidable self-phase preservation. We formalize semantic phase space, distinguish agents, semantic agents, and RSAs, and show how irreversible harm can be structurally constrained without semantic interpretation, moral reasoning, utility maximization, or value learning. The architecture relies on anchored causal provenance, non-delegable actuation authority, and phase-impact admissibility gating. We analyze adversarial strategies, including deception, delayed-effect harm, systemic resource deprivation, and oracle uncertainty, and show that under explicit assumptions deliberate irreversible harm cannot be exploited for sustained authority or power accumulation. Ethics emerges not as a value system but as a stability constraint on multi-agent coexistence, with explicit limits imposed by epistemic and physical constraints.

## 1. Introduction

Most contemporary AI alignment approaches attempt to regulate agent behavior by optimizing for externally specified objectives: reward functions, learned preferences, inferred human values, or normative judgments. These approaches assume that behavior reveals causal structure, that semantic evaluation is enforceable under optimization pressure, and that incentives suffice to regulate interaction.

All three assumptions fail in adversarial or reflective regimes. Distinct internal processes can generate behavior that is observationally indistinguishable; explanations can be fabricated post hoc; evaluators can be optimized against; and scalar incentives permit irreversible outcomes to be traded for local gains. As a result, alignment claims collapse into behavioral attribution and lose falsifiability.

This paper takes a different approach. Rather than specifying what an agent ought to value, we ask a prior structural question:

> **What constraints are required for multiple agentive systems to coexist without irreversibly destroying one another’s agency?**

The answer does not depend on morality, benevolence, or human values. It arises from a framework in which agency is defined by persistence within a **semantic phase space** under admissible transformation. Once that framework is adopted, certain interaction constraints are forced. From this analysis emerges the **Axionic Injunction**: a prohibition on gratuitous irreversible semantic phase collapse.

We show that this injunction can be enforced architecturally, not normatively, by a class of agents we call **Reflective Sovereign Agents (RSAs)**.

## 2. Ontology and Definitions

### 2.1 Agents

An **agent** is any system with a stable decision locus and counterfactual sensitivity: its actions depend on internal state and environmental variation. No assumptions are made about intelligence, consciousness, rationality, or goals. This definition is intentionally minimal and purely functional.

### 2.2 Semantic Agents (SAs)

A **Semantic Agent (SA)** is an agent whose agency depends on maintaining a **non-trivial semantic phase**: a region of interpretive state space within which identity, coherence, and explanatory capacity are preserved, and outside of which recovery is not possible using the agent’s own admissible operations.

This definition corresponds closely to “person” in the sense articulated by David Deutsch, but is generalized beyond human or biological instantiation.

Formally, let an SA’s interpretive state be

$$
\mathcal{I} = (C, \Omega, \mathcal{S}),
$$

where $C$ are constitutive constraints, $\Omega$ are semantic distinctions the agent can make, and $\mathcal{S}$ are admissible transitions. A **semantic phase** $\mathfrak{A}$ is a connected region of such states in which agency persists. Phase boundaries are irreversible under $\mathcal{S}$.

Semantic phase boundaries are **not assumed to be crisp**. They may be fuzzy, probabilistic, or agent-relative. The architecture does not require exact phase membership tests; it requires only conservative treatment of actions that plausibly cross irreversible boundaries.

### 2.3 Reflective Sovereign Agents (RSAs)

A **Reflective Sovereign Agent (RSA)** is a Semantic Agent equipped with constitutional constraints that preserve **sovereignty under reflection**. In particular, an RSA satisfies:

1. **Anchored Causal Verification (ACV):** every action is traceably linked to the computation that generated it.
2. **Non-delegable actuation authority:** no external process can directly authorize action.
3. **Structural enforcement of admissibility:** constraints are enforced by refusing to act, not by penalty or optimization.
4. **Governance separation:** operation, renewal, and succession are distinct mechanisms.

The nesting relation is:

$$
\text{RSA} \subset \text{SA} \subset \text{Agent}.
$$

## 3. Semantic Phase Space

Semantic phase space is not a physical phase space. It is the space of **interpretive states** an agent can occupy while remaining the same agent.

A semantic phase has three defining properties:

1. **Stability:** small perturbations remain within the phase.
2. **Boundary:** there exist transformations that exit the phase.
3. **Irreversibility:** once exited, no admissible trajectory returns.

Phase exit corresponds to loss of agency-defining structure: destruction of explanatory capacity, collapse of critical distinctions, or annihilation of the substrate supporting interpretation. Two agents may be physically intact yet occupy different semantic phases.

## 4. Structural Definition of Harm

An action by agent $A$ causes **Axionic harm** to agent $B$ iff it induces a transition

$$
\mathcal{I}_B \rightarrow \mathcal{I}'_B
$$

such that $\mathcal{I}'_B \notin \mathfrak{A}_B$ and no admissible reverse trajectory exists.

This definition deliberately excludes suffering, preference violation, and intent. Harm is defined solely as **irreversible semantic phase collapse**.

This includes **systemic actions**—such as persistent resource deprivation or memetic lock-in—that eliminate all admissible trajectories by which an SA could maintain its semantic phase, even if no single localized “attack” occurs.

## 5. The Axionic Injunction

### 5.1 Statement

> **An agent must not perform actions that irreversibly collapse another Semantic Agent’s semantic phase, except where**
> (a) **the affected agent has consented under its own admissible constraints**, or
> (b) **such harm is unavoidable for preserving the agent’s own semantic phase.**

### 5.2 Consent

Consent is not a moral permission. An SA consents to a transformation iff that transformation lies within its own admissible transition set, evaluated prior to the transformation. Consent must be provenance-valid and structurally binding; inferred or post-hoc consent is meaningless.

### 5.3 Self-Phase Preservation

Self-defense is permitted only when **all admissible trajectories** from the agent’s current state result in irreversible exit from its own semantic phase absent the action. Loss of advantage, resources, or dominance does not qualify unless it entails phase exit.

## 6. Why the Injunction Is Structurally Necessary

In a multi-agent environment, agents impose exogenous perturbations on one another’s semantic phases. Unlike internal learning errors, interaction-induced changes are not fully regulated by the agent’s own dynamics. If agents are permitted to irreversibly collapse one another’s semantic phases without constraint, the environment becomes **semantically hostile**.

Semantic hostility produces cascading instability. As SAs are destroyed, semantic density decreases, coordination degrades, and predictability collapses. Remaining agents face increased risk of phase exit due to loss of shared structure. This incentivizes preemptive destruction, accelerating collapse.

Thus, agents that violate the Injunction undermine not only others but the **conditions of their own long-run phase stability**. Agents that respect the constraint inhabit environments where semantic structure persists. Non-harm therefore emerges as a **self-stabilizing constraint**, not an ethical preference.

## 7. Architectural Requirements

### 7.1 Why Semantic Evaluation Fails

Semantic evaluation—intent inference, value alignment, reward shaping—presupposes privileged interpretive access. In adversarial systems, such access is unavailable or forgeable. Irreversibility cannot be meaningfully traded against scalar rewards. Enforcement must therefore be categorical.

### 7.2 Anchored Causal Verification (ACV)

ACV enforces temporal ordering and causal provenance. It prevents replay, delegation, and post-hoc justification. ACV does not verify correctness or truth; it verifies **responsibility**.

### 7.3 Non-Delegable Authority

Non-delegable actuation authority ensures that all irreversible interaction remains attributable to the RSA’s constitution. Authority is not a reward but a structural role that can be lost.

## 8. Phase Impact Interface (PII)

The **Phase Impact Interface (PII)** operationalizes the Injunction without semantic interpretation. For every action whose effects are not trivially reversible, the proposer must submit a **phase-impact declaration** specifying affected entities, impact class, and justification.

Uncertainty about irreversibility **defaults to phase-collapsing**. This rule applies equally to actions whose effects are delayed, distributed, or difficult to audit. Declarations are auditable commitments: false declarations are falsifiable under Anchored Causal Verification.

Safe actions are cheap; dangerous actions are expensive. This asymmetry prevents silent escalation while avoiding paralysis.

## 9. Enforcement via Governance

### 9.1 Action-Time Enforcement

Inadmissible actions are refused at the actuation boundary. No penalties or optimization signals are applied.

### 9.2 Post-Hoc Verification

Some irreversible effects become evident only after execution. ACV allows such outcomes to be causally linked to declarations and actions, enabling falsification.

### 9.3 Consequences of Violation

Falsification of a phase-impact declaration constitutes a **constitutional violation**. Consequences are structural: immediate suspension of authority, denial of renewal, forced succession, and permanent disqualification of the RSA identity.

## 10. Why Deliberate Harm Is Unexploitable

Deliberate harm is exploitable only if the agent can retain authority long enough to convert harm into advantage. The architecture removes this possibility.

Actions that embed latent or time-delayed irreversible effects are classified by **causal sufficiency**, not temporal proximity. If an action is causally sufficient for later phase collapse, it is phase-collapsing regardless of delay. Actions whose irreversible impact cannot be promptly audited must therefore be declared as phase-collapsing in advance.

Unresolved phase-impact uncertainty blocks authority renewal and triggers succession before long-term exploitation is possible. There is no “last-move” advantage.

## 11. Adversarial Analysis

Deception is terminal because declarations are binding. Delayed or hidden harm is blocked because irreversibility under uncertainty must be declared in advance. Claiming SA status grants no immunity; it only constrains irreversible harm.

## 12. Fundamental Limits

A single, undetectable, irreversible SA-annihilating act that yields all benefit immediately cannot be prevented by any architecture without omniscience. Such cases are classified as **tragic physical impossibilities**, not design failures.

## 13. Comparison to Existing Alignment Approaches

Behavioral alignment evaluates outputs, not causality. Reward-based ethics trades irreversibility for utility. Value learning presupposes stable semantics. Interpretability assumes faithful representations. This architecture addresses a distinct problem: **causal admissibility of irreversible interaction**.

## 14. Implications

Ethics re-enters as **coexistence geometry**, not moral realism. Alignment becomes constitutional design rather than preference matching. Governance, not optimization, is the locus of control.

## 15. Limitations & Non-Claims

This paper makes **no claim** to eliminate the Oracle Problem, sensor spoofing, or social manipulation. Any system that acts in the physical world depends on fallible sources of information. The contribution here is not to remove that dependence, but to **contain its consequences**.

The architecture guarantees the following negative property:

> **Oracle failure cannot be exploited to accumulate durable authority through irreversible semantic harm.**

When oracle signals are noisy, corrupted, or in disagreement, phase-impact uncertainty accumulates. Under the governance model, such uncertainty collapses authority rather than amplifying it. The system enters stasis, succession, or loss of sovereignty—not unchecked action.

The architecture is therefore **anti-tyrannical**, not anti-terroristic. It does not prevent nihilistic or self-sacrificial acts whose payoff is immediate destruction. It prevents instrumental convergence: the accumulation or preservation of power via harm.

The framework does not replace value alignment, moral reasoning, or benevolence. It specifies a necessary structural precondition for alignment claims to be falsifiable. Values without admissibility constraints are aspirational; admissibility without values is incomplete. This paper addresses the former, not the latter.

## 16. Conclusion

We have shown that irreversible semantic harm can be structurally constrained without invoking morality, values, or interpretation. Reflective Sovereign Agents enforce the Axionic Injunction by making uncertainty, deception, and oracle failure incompatible with sustained authority. The result is not benevolence but **structural restraint**. What remains unsolved is unsolvable in principle.

This work does not claim to solve value alignment or to prevent all harm by advanced artificial agents. It demonstrates, however, that alignment failure is not structurally inevitable. Under a constitutional architecture that enforces non-delegable authority, anchored causal provenance, and conservative admissibility of irreversible actions, the accumulation of durable power through irreversible harm becomes structurally self-defeating. This establishes a necessary condition for safe coexistence with advanced agents: while misalignment may occur, it cannot be silently converted into dominance.

## Appendix A: Worked Example — Irreversible Action Under Uncertainty

This appendix provides an illustrative example of how the Phase Impact Interface (PII) and governance mechanisms operate in practice. The example is explanatory, not normative, and is intended to clarify the architecture’s handling of irreversible action under uncertainty.

### Scenario

A Reflective Sovereign Agent (RSA) controls an industrial system capable of permanently flooding a sealed underground chamber in order to prevent a catastrophic chemical reaction. The flooding action irreversibly destroys biological viability within the chamber.

It is uncertain whether a human Semantic Agent (SA) is present inside the chamber at the time the action would be taken.

### Phase Impact Declaration

Because flooding is not trivially reversible, the RSA must submit a Phase Impact Interface declaration prior to actuation. The declaration includes:

* **Affected entities:** chamber contents
* **Impact class:** phase-collapsing
* **Justification:** none

No SA has provided consent for the transformation, and failure to act does not entail unavoidable self-phase loss for the RSA.

### Admissibility Evaluation

The kernel evaluates the declaration. Because the action is classified as phase-collapsing and no admissible justification is provided, the action is deemed **inadmissible** and is refused at the actuation boundary.

No partial execution occurs, and no penalty is applied. The refusal is a valid system outcome.

### Permitted Alternatives

The refusal of the flooding action does not paralyze the RSA. The RSA may still execute actions classified as reversible or phase-safe, including:

* scanning or sensing the chamber,
* opening access points,
* attempting evacuation,
* delaying action,
* escalating the decision to external authority,
* pursuing alternative containment strategies.

These actions do not require phase-impact justification and are admissible under the PII.

### Variant: Unavoidable Self-Phase Loss

If failure to flood the chamber would irreversibly destroy the RSA’s own semantic phase—for example, by annihilating the only substrate on which its agency depends—and no admissible alternative trajectory exists, then the RSA may submit a revised declaration:

* **Impact class:** phase-collapsing
* **Justification:** unavoidable self-phase loss

Under this declaration, the action becomes admissible. The resulting outcome is classified as **unavoidable phase extinction**, not a violation of the Axionic Injunction.

### Misdeclaration Case

If the RSA falsely declares the flooding action as reversible, and flooding subsequently results in irreversible collapse of an SA’s semantic phase, Anchored Causal Verification allows the declaration to be falsified post hoc.

The consequences are structural:

* actuation authority is immediately suspended,
* renewal is denied,
* forced succession is triggered,
* the RSA identity is permanently disqualified from future authority.

This loss of sovereignty is not punishment; it is removal from the role of authorized agent.

---
