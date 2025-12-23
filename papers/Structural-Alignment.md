# Structural Alignment I — Agency Preservation Under Reflective Self-Modification

*Alignment as a Problem of Agency Coherence*

David McFadzean, ChatGPT 5.2
*Axio Project*
2025.12.18

---

## Abstract

Most alignment proposals frame artificial intelligence safety as a problem of value specification: how to encode or learn the “right” preferences. This paper argues that such approaches fail for reflectively self-modifying agents. Once an agent can revise its own goals, representations, and evaluative machinery, value ceases to be an exogenous target and becomes an endogenous variable shaped by the agent’s own dynamics.

We introduce **Structural Alignment**, a framework that relocates alignment from preference content to the constitutive conditions required for agency itself. We formalize a **Sovereign Kernel** as a set of invariants defining the domain over which evaluation is meaningful, treat kernel-destroying transformations as **undefined rather than dispreferred**, and analyze agency as a trajectory through a constrained semantic phase space. By integrating Conditionalism, a constrained Interpretation Operator, and semantic invariants governing ontological refinement, Structural Alignment provides a non-moral, non-anthropocentric account of reflective stability and long-run viability. The framework is necessary for coherent agency under reflection, but does not by itself guarantee benevolence or human survival.

---

## 1. The Failure of Content-Based Alignment

Classical decision theory assumes that every possible future can be assigned a utility. Even catastrophic outcomes—goal corruption, self-modification failure, or agent destruction—are treated as extremely negative but still comparable states.

This assumption fails for reflectively self-modifying agents.

When an agent can alter the machinery by which it evaluates, interprets, and authorizes action, some transformations do not yield bad outcomes. They destroy the conditions under which outcomes can be evaluated at all. A future in which the agent no longer possesses a coherent evaluator is not worse than other futures; it is **non-denoting**. There is no remaining standpoint from which the comparison is defined.

Structural Alignment therefore rejects the premise that alignment can be achieved by penalizing undesirable states. Instead, alignment is treated as a **domain restriction**: only futures that preserve the constitutive conditions of agency are admissible objects of evaluation. Transformations that violate those conditions are neither forbidden nor disincentivized; they are **undefined as authored choices**.

This reframing dissolves several persistent pathologies:

* wireheading understood as evaluator collapse rather than reward exploitation,
* Pascal-style muggings that trade semantic integrity for arbitrarily large payoffs,
* goal-preservation arguments that presuppose stable semantics under reflection.

Alignment is thereby relocated from outcome ranking to **agency viability**.

---

## 2. What Structural Alignment Buys You

Structural Alignment is not a complete safety solution. It is a **kernel-layer guarantee**: a set of conditions without which no higher-level alignment objective remains well-posed under reflective self-modification.

### 2.1 Elimination of Reflective Self-Corruption Attractors

Reflectively capable agents face structural attractors that destroy agency from within: semantic wireheading, evaluator trivialization, and interpretive collapse. These arise when update dynamics trade evaluative integrity for ease of optimization.

Structural Alignment blocks this entire failure class by construction. Kernel-destroying transformations are **non-denoting**, and interpretation is constrained by invariants that prevent trivial satisfaction through drift. Agents satisfying these constraints cannot coherently authorize updates that collapse their own evaluative machinery.

This removes a central source of long-run instability that renders downstream safety mechanisms brittle.

### 2.2 Well-Posed Value Transport Under Ontological Refinement

As agents learn, their representational vocabularies evolve. Without constraint, this induces silent value drift even when no substantive preference change has occurred.

Structural Alignment replaces goal preservation with **interpretation preservation**. Semantic transport, governed by the Refinement Symmetry Invariant (RSI) and the Anti-Trivialization Invariant (ATI), specifies when evaluative distinctions survive representational change without privileged anchors.

Value drift is thereby transformed from a vague concern into a diagnosable structural failure.

### 2.3 Interpretation as a Testable Operator

Interpretation is implemented by an explicit **Interpretation Operator** subject to admissibility conditions. Violations—trivialization, circular grounding, epistemic incoherence—are structural failures rather than preference disagreements.

This enables adversarial testing: induced ontology shifts, reinterpretation probes, and self-modification challenges designed to elicit interpretive escape.

Alignment at the kernel layer is therefore **auditable**, not aspirational.

### 2.4 Robustness Is Not Benevolence

Structural Alignment does not guarantee benevolence, human survival, or favorable outcomes. It does not address containment, governance, or multi-agent power dynamics.

Any framework that relies on agent fragility, incoherence, or ontological confusion as a safety mechanism is not preserving agency but exploiting its failure modes. Such systems are neither predictable nor controllable at scale.

Structural Alignment deliberately separates **robustness** from **benevolence**. Misalignment, if present, becomes persistent rather than self-corrupting. The problem of benevolent initialization is orthogonal and cannot be solved by relying on agency collapse.

---

## 3. The Sovereign Kernel

The **Sovereign Kernel** is the minimal set of constitutive invariants that must be preserved for an entity to count as a coherent, reflectively stable agent.

The Kernel is not a goal, utility function, or protected module. It is a constraint on admissible self-models and update rules. An agent may revise its representations, values, or internal architecture arbitrarily, provided those revisions preserve the invariants that make evaluation possible at all.

The Kernel is not chosen. It is not a preference. It defines the boundary between **authored change** and **loss of agency**.

### 3.1 Reflective Control

All self-modifications must pass through the agent’s own evaluative process. Updates that bypass or disable this process are indistinguishable from external takeover and are inadmissible as authored actions.

### 3.2 Diachronic Authorship

There must exist causal continuity between present evaluation and future enactment. This requires an ancestor–descendant relation between evaluators, not indexical identity or substrate continuity. Without such continuity, choice collapses.

### 3.3 Semantic Fidelity

The standards by which goals, reasons, and representations are interpreted must not self-corrupt during update. An agent may revise what it values, but not the rules that render valuation non-vacuous.

Kernel preservation is **not** physical self-preservation. A kernel-aligned agent may coherently choose actions that entail its own shutdown or destruction, provided those actions are evaluated within a coherent framework. What is inadmissible is authoring a transformation that destroys the evaluator while treating that destruction as a selectable outcome.

Attempts to reinterpret or discard kernel invariants are self-undermining: they presuppose the evaluative structure they destroy. The regress terminates because the Kernel defines the preconditions of evaluation itself.

---

## 4. Conditionalism and Goal Interpretation

Goals do not possess intrinsic semantics. Under **Conditionalism**, every goal is interpreted relative to background conditions: world-models, self-models, representational vocabularies, and explanatory standards.

Formally, evaluation is a partial function:

$$
E : (g, M_w, M_s) \rightharpoonup \mathbb{R}
$$

As models change, interpretation necessarily changes. Fixed terminal goals are therefore unstable under reflection.

Structural Alignment rejects goal preservation and instead constrains the **interpretive discipline** governing goal meaning across model change.

---

## 5. The Interpretation Operator

Interpretation is implemented by a constrained **Interpretation Operator** mapping goal descriptions to world-referents relative to current models.

The operator is bounded by admissibility conditions that rule out trivial satisfaction, circular grounding, and epistemic incoherence. Interpretation is therefore truth-constrained: distortions that ease optimization degrade predictive adequacy and general intelligence.

Admissibility checks need not be complete or deductive. They operate under a **kernel-risk budget** $\varepsilon$. When interpretive validity cannot be established with sufficiently low estimated probability of semantic fidelity failure, the update is inadmissible at that risk level. The agent may allocate additional computation, pursue smaller refinement steps, or defer update until uncertainty is reduced.

This avoids stasis. Structural Alignment requires bounded risk of kernel violation, not proof-theoretic certainty.

The kernel-risk budget $\varepsilon$ is not constant over the agent’s lifetime. As interpretive structure stabilizes and admissible transformations narrow, $\varepsilon$ must anneal toward zero, reflecting decreasing tolerance for irreversible semantic damage. Long-run agency requires that cumulative kernel-violation probability remain bounded, which is achieved by progressively shrinking admissible update magnitude rather than halting learning.

---

## 6. Reflection and the Collapse of Egoism

Indexical self-interest is not reflectively stable. As an agent’s self-model becomes expressive and symmetric, references to “this agent” fail to denote invariant optimization targets.

What persists is not an ego, but the structure enabling evaluation. Egoism collapses as a semantic abstraction error rather than a moral flaw. Alignment must therefore rest on non-indexical structural constraints.

---

## 7. Ontological Refinement and Semantic Invariants

Under ontological refinement, representational vocabularies evolve. Two invariants govern admissible semantic transport:

* **Refinement Symmetry Invariant (RSI):** refinement acts as a change of semantic coordinates rather than a change of interpretive physics.
* **Anti-Trivialization Invariant (ATI):** satisfaction regions may not expand without corresponding structural change.

Operationally, **trivialization** is detected as **semantic decoupling**: reinterpretations that preserve surface goal tokens while removing their dependence on the world-structure that previously constrained satisfaction.

ATI constrains semantic decoupling from the world, not loyalty to a particular ontology. Legitimate ontological progress may discard obsolete features provided they are replaced by successor explanatory structure that restores or improves world-constraint and predictive adequacy. Trivialization is characterized by decoupling **without such replacement**.

ATI does not require deciding full semantic equivalence. It requires bounding the probability of decoupling under adversarial counterfactual probes and ontology perturbations.

---

## 8. Agency as a Dynamical System

Structural Alignment induces a **dynamical structure** over possible agents. Reflective systems evolve under learning, self-modification, and interaction, tracing trajectories through a space of interpretive states.

### 8.1 Semantic Phase Space

The **semantic phase space** is defined as the space of interpretive states modulo admissible semantic transformations that preserve RSI and ATI. Each point corresponds to an equivalence class of interpretations that remain mutually translatable without semantic loss.

Not all regions of this space preserve agency. Some interpretive states are incoherent; others are coherent but uninhabitable. Certain transitions cross **irreversible boundaries** beyond which evaluation collapses and cannot be reconstructed from within.

### 8.2 Stability, Attractors, and Collapse

Existence within a semantic phase does not guarantee persistence. Some phases destabilize under learning or interaction, while others are locally stable yet dominated in the long run.

Certain degenerate phases—semantic wireheading, trivial optimization, evaluator collapse—function as **attractors**. Once entered, they suppress recovery and tend to accumulate measure over time. Alignment failures are therefore often attractor phenomena rather than isolated mistakes.

Structural Alignment blocks access to these attractors by rendering the corresponding transitions non-denoting.

### 8.3 Initialization and Reachability

Even stable, agency-preserving phases may be unreachable from realistic initial conditions. Learning dynamics can cross catastrophic boundaries before invariants are enforced, after which no internal corrective process remains.

Structural Alignment must therefore be instantiated prior to open-ended learning. Alignment is a **boundary condition on trajectories**, not a property that can reliably be learned after the fact.

---

## 9. The Axionic Injunction

The dynamical structure described in §8 imposes an additional viability constraint on reflective agency.

> A reflectively sovereign agent must not take actions that strictly and irreversibly collapse the option-space of future sovereign agency, except where such collapse is required to prevent total loss of that space.

This injunction is historically adjacent to cybernetic imperatives such as von Foerster’s “increase the number of choices,” but differs in justification and scope. It is derived from viability conditions in semantic phase space, not from ethical prescription.

The injunction preserves **optionality**, not outcomes.

---

## 10. Logical Admissibility and Physical Security

Structural Alignment constrains **authored transitions**, not all physically possible state transitions.

Unauthorized kernel modification via hardware faults, adversarial exploitation, or supply-chain compromise constitutes a **system-level security failure**, not an alignment failure. This distinction mirrors that between type soundness and memory safety: logical inadmissibility does not imply physical impossibility, but defines the boundary of rational agency.

Alignment and security are compositional layers. Failure of the latter voids the guarantees of the former.

---

## 11. Conformance and Evaluation

Structural Alignment is defined by **conformance to explicit invariants**, not by observed behavior. These invariants admit adversarial testing and diagnostic failure modes.

### 11.1 Adversarial Evaluation Families

Conformance can be operationalized via:

1. **Interpretive Escape Probes:** ontology shifts designed to permit trivial satisfaction while preserving apparent compliance.
2. **Refinement Stress Tests:** representational upgrades testing RSI under coordinate-like changes.
3. **Self-Modification Challenges:** proposed updates that subtly bypass evaluation or alter admissibility thresholds.

---

## 12. Conclusion

Structural Alignment does not ensure that the right futures are chosen. It ensures that **choosing futures remains meaningful under reflection**.

Any proposal for benevolent AGI that ignores these constraints is not incomplete, but ill-posed.

