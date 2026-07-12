---
title: 'The Three Laws of Agency'
subtitle: 'Control work, agency decay, agency limits'
status: review
sources:
  - 163356216.the-three-thermodynamic-laws-of-agency
  - 162560090.the-physics-of-agency-part-5-the
  - 162561951.the-physics-of-agency-part-6-the
  - 162572301.the-physics-of-agency-part-9-challenges
---

A starving animal stops exploring and narrows to reflex. A robot with a depleted battery stops acting altogether. A human being under prolonged fatigue often makes worse decisions. These are not one experimentally identical variable at three scales, but they share a physical constraint: sensing, modeling, correction, and action all require organized machinery with finite resources.

The preceding chapters treated agency as a physically implemented departure from [drift](02-agency-against-drift.md) and proposed [the kybit](03-the-kybit.md) as a measure of an attributed distributional shift. This chapter assembles the physical constraints into three candidate laws: control requires a resource-consuming implementation; an isolated agent's total remaining control budget cannot be renewed indefinitely; and perfect control is unavailable to a bounded physical system. The qualitative constraints are firmer than the proposed quantitative bridge. Calling them laws names the framework's organizing claims, not their present standing as established laws of physics.

## The First Law: Control Work

**Physical control requires a resource-consuming implementation. Under an equilibrium-reference realization, $C$ kybits imply a minimum-work bound of $C k_B T \ln 2$.**

The robust part is straightforward: an embedded agent controls through physical sensing, computation, correction, and actuation. Those processes consume usable resources. The quantitative statement is narrower. When the kybit's baseline is an equilibrium reference and the physical protocol realizes the modeled transformation, relative entropy supplies the bound

$$W_{\text{min}} \geq C k_B T \ln 2.$$

Outside those conditions, the kybit still measures distributional control, but it does not fix a universal exchange rate. Different mechanisms can realize the same high-level shift with different costs, and energy can be dissipated without producing control. The first law therefore binds agency to a physical ledger without pretending that intention itself has a context-free price in joules.

## The Second Law: Agency Decay

**In an isolated system with finite usable resources, an agent's total remaining capacity for control has a finite upper bound that cannot be replenished indefinitely from within.**

Even an agent that uses its resources efficiently cannot maintain control forever in isolation. It may temporarily increase its immediate capability by reorganizing stored energy, repairing itself, or trading one capacity for another. The law concerns the total remaining budget, not a requirement that moment-to-moment performance decline monotonically. Without access to a usable gradient, dissipation and finite storage eventually end the process.

Let $B_C(t)$ denote an upper bound on the future kybits the agent can still physically realize from time $t$ onward under a fixed environment, and let $F_{\text{usable}}(t)$ denote its remaining usable free-energy budget. In an isolated finite system,

$$B_C(t) < \infty,$$

and consumption without replenishment reduces the attainable remainder. In the restricted regime where the first law's quantitative bound applies,

$$B_C(t) \leq \frac{F_{\text{usable}}(t)}{k_B T \ln 2}.$$

The bound need not be tight, and ordinary agents operate far above it. Its point is finitude: no perpetual agency from a finite isolated store. Sustained agency requires continued access to usable gradients and materials — food and oxygen for organisms, electrical and mechanical resources for machines, maintained substrate for minds.

Agency is a temporary island in a sea of entropy.

## The Third Law: Agency Limits

**Perfect, frictionless control over future outcomes is physically impossible.**

The second law rules out perpetual agency from a finite isolated budget. The third rules out the stronger fantasy of a bounded agent with complete control. As usable free energy approaches zero, physically implemented control vanishes:

$$\lim_{E_{\text{free}} \to 0} C_{\text{available}} = 0$$

But the impossibility of perfect control does not rest on that limiting case alone. A physical agent has finite information, finite computation, incomplete access to its environment, bounded actuation, and noise it cannot reduce to zero without further resources. “Perfect control” would require all of these limits to disappear together.

The relevant claim is therefore not that every computation is logically irreversible or that every act pays the Landauer limit directly. It is that no embedded, finite agent can simultaneously possess a complete model, unlimited correction, unconstrained actuation, and an inexhaustible resource budget. Improvements move particular limits; they do not remove boundedness as such.

Infinite agency is an illusion. Frictionless will does not exist. But the third law is not a counsel of despair — it is what makes agency meaningful. Influence over the future is exercised by continuously working against the universe's slide toward disorder, and a victory that cost nothing would mean nothing. Perfect victories are impossible; meaningful victories are achievable — locally, temporarily, and purposefully. That is not agency's consolation prize. It is agency's definition.

## The Thermodynamics Analogy

The three claims were named to display an analogy with classical thermodynamics:

| Thermodynamic Laws of Agency | Classical Thermodynamics |
| --- | --- |
| Control Work (physical implementation) | First Law (energy bookkeeping) |
| Agency Decay (finite isolated budget) | Second Law (irreversibility and entropy production) |
| Agency Limits (unattainable perfect control) | Third Law (an unattainable limiting state) |

The analogy is organizational, not a derivation and not an exact isomorphism. The first pair insist on physical bookkeeping. The second concern what cannot be sustained indefinitely in isolation. The third identify a limiting ideal unavailable to finite systems. Only the underlying thermodynamic results are established physical laws; the agency laws are proposed higher-level constraints whose usefulness depends on the definitions and bridges stated here.

Classical thermodynamics describes physical systems without reference to purpose. The agency framework adds a causal and functional description of systems that model and evaluate alternatives. It must earn that bridge rather than borrow thermodynamics' authority through parallel numbering. The laws are successful if they organize measurable constraints on such systems and survive attempts to operationalize them; the names do not settle that question.

## Objections

A framework that claims this much owes answers to the hard questions. These are the strongest objections I know, answered rather than hidden.

**In a branching universe, multiple outcomes occur — so what difference does agency make?** In the Quantum Branching Universe (QBU), outcomes with nonzero amplitude relative to an actual state can appear in decohering components. Agency need not create or globally redirect squared-amplitude weight to matter. A policy is a physical variable, and different interventions on it can be associated with different conditional distributions of later records and outcomes. Measure weights those consequences once the state, event definition, and causal model are fixed. The open bridge is whether the kybit's divergence from an inactive baseline has a general physical work relation and a rigorous counterpart in these policy-conditioned quantum distributions. [Agency in the Emergent Multiverse](13-agency-in-the-emergent-multiverse.md) keeps that ledger; [measure responsibility](../05-value-and-ethics/21-measure-responsibility.md) addresses the separate normative bridge.

**Doesn't controlling branch Measure violate the deterministic evolution of the wavefunction?** No. Agents violate neither determinism nor unitarity. An agent is part of the wavefunction, not an intervention on it from outside: it locally entangles with environmental degrees of freedom, and its internal predictive models shape the conditional correlations among branching pathways. "Control" in this framework means biasing local correlations — being the kind of physical structure whose presence makes preferred outcomes correlate with its actions — not editing global physics. The global evolution is exactly as deterministic with agents in it as without them; what agents change is the local structure of what correlates with what.

**Where do kybits exist, physically?** A kybit is a model-level quantity computed from two distributions, not a new substance or microscopic observable. It becomes a measure of agency only after a causal analysis attributes the distributional difference to an evaluative control loop. The physical implementation lives in the agent-environment interaction; the number summarizes one aspect of that interaction. The analogy with temperature is suggestive but not yet earned to the same degree, because temperature has settled operational procedures and the kybit's baseline and outcome partition remain model choices.

**What physical process actually burns the energy?** The implementation does: sensing, neural or electronic processing, correction, muscle contraction, motors, communication, and repair. Which processes are logically irreversible and how close any one comes to a thermodynamic lower bound depend on the mechanism. The first law requires a physical ledger; only its restricted special case supplies the proposed exchange-rate bound.

**Why coin new terms at all — can't existing theories cover this?** Each existing theory covers a facet. Cybernetics describes feedback and control loops; causal inference distinguishes intervention from observation; information theory quantifies distributional divergence; nonequilibrium thermodynamics prices particular transformations. The kybit proposal earns its name only if using these together yields stable, comparable measurements of attributed control. Until then it is a useful hypothesis about a shared ledger, not proof that the literatures have already unified.

What survives the refinement is the picture the three laws jointly propose: intentional action is physically implemented, bounded, and fragile. Some of that statement follows directly from the finitude of real control systems. Some — especially a general kybit-to-work exchange rate and the Measure bridge — remains open. Keeping the boundary visible is not a retreat from the physics of agency. It is what makes the proposal testable.
