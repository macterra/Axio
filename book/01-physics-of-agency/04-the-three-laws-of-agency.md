---
title: 'The Three Laws of Agency'
subtitle: 'Control work, agency decay, agency limits'
status: draft
sources:
  - 163356216.the-three-thermodynamic-laws-of-agency
  - 162560090.the-physics-of-agency-part-5-the
  - 162561951.the-physics-of-agency-part-6-the
  - 162572301.the-physics-of-agency-part-9-challenges
---

A starving animal stops exploring and narrows to reflex. A robot with a depleted battery stops acting altogether. A human being at the end of a punishing day makes visibly worse decisions — "decision fatigue" is not a metaphor but a measurable physical depletion. Three very different systems, one identical failure mode: when the energy runs out, the steering stops.

That convergence is not a coincidence. It is the signature of law. The preceding chapters established that agency is a physical phenomenon — an embedded agent spending energy to bias reality against [drift](02-agency-against-drift.md) — and gave it a unit of account, [the kybit](03-the-kybit.md), with a hard thermodynamic price per unit of control. This chapter assembles those results into three laws that bound every agent that has ever existed or ever will: bacteria, brains, corporations, artificial intelligences. Control requires work. Control capacity decays without external input. Perfect frictionless control is impossible. Each law has a formal statement, and together they stand in a structural parallel to the classical laws of thermodynamics — a parallel I will make exact, and then defend against the strongest objections the framework faces.

## The First Law: Control Work

**Exercising intentional control over outcomes requires physical work proportional to the kybits exerted.**

This is the law derived in [the kybit](03-the-kybit.md): steering the probability distribution over futures is a physical operation with a minimum energy cost, Landauer's principle extended from erasing bits to biasing outcomes. Every kybit of control carries a floor price:

$$W_{\text{min}} = k_B T \ln 2 \quad \text{per kybit}$$

There is no such thing as a thermodynamically free choice. An agent that wants to make a difference must pay for the difference in joules — in neural computation, in muscle contraction, in actuated machinery. The first law fixes the exchange rate between intention and energy; the remaining two laws follow from taking that exchange rate seriously over time and at the limit.

## The Second Law: Agency Decay

**In a closed system without external energy input, the available capacity to exercise agency inevitably decreases over time.**

Even an agent that burns its energy wisely and chooses carefully cannot hold its ground by thrift alone. Entropy is always waiting. Cut off the inflow of fresh energy and the decline is not a risk but a certainty: the agent's internal modeling degrades, its action capabilities diminish, its power to bias futures shrinks. Eventually it stops steering entirely, and random drift reclaims dominance.

Formally: let $C_{\text{available}}(t)$ be the number of kybits an agent can still exert at time $t$, and $E_{\text{free}}(t)$ the free energy available to it. Then

$$\frac{dC_{\text{available}}}{dt} \leq 0 \quad \text{(in a closed system)}$$

which follows directly from the first law's exchange rate: control capacity is purchased from the free-energy budget,

$$C_{\text{available}}(t) \propto \frac{E_{\text{free}}(t)}{k_B T \ln 2}$$

so as free energy dissipates, control capacity decays with it.

The consequences are unforgiving. No perpetual agency. No infinite choosing without cost. No escape from thermodynamic consequences. Sustained agency demands a continual intake of negentropy — ordered energy imported from outside: food for organisms, fuel for machines, computation and knowledge for minds. This is why the opening examples are one phenomenon and not three. The starving organism, the depleted battery, the exhausted decision-maker are all the same curve at different scales: an agent whose free-energy reserve is running down, watching its capacity to steer run down in proportion. Without replenishment, every agent eventually becomes a drifter.

Agency is a temporary island in a sea of entropy.

## The Third Law: Agency Limits

**Perfect, frictionless control over future outcomes is physically impossible.**

The second law says agency runs down; the third law says it can never, even in principle, run perfectly. Just as no physical system can reach absolute zero temperature, no agent can exercise unlimited, cost-free control. As available free energy approaches zero, the capacity for agency vanishes with it:

$$\lim_{E_{\text{free}} \to 0} C_{\text{available}} = 0$$

and there is no clever engineering around the floor price of $k_B T \ln 2$ per kybit. Perfect control — infinite steering at zero thermodynamic cost — would require the price to fall to nothing, and it never does.

Three independent facts each suffice to enforce the limit. Physical systems are never entirely isolated from external disturbance: there is always noise to correct, and correction costs work. Predictive models are inherently imperfect and inherently costly: an agent steers by simulating futures, and simulation is computation, and computation dissipates. And prediction and action alike require irreversible physical processes, which always generate entropy. Even under ideal conditions, an agent must expend a finite amount of energy to steer any outcome at all.

Infinite agency is an illusion. Frictionless will does not exist. But the third law is not a counsel of despair — it is what makes agency meaningful. Influence over the future is exercised by continuously working against the universe's slide toward disorder, and a victory that cost nothing would mean nothing. Perfect victories are impossible; meaningful victories are achievable — locally, temporarily, and purposefully. That is not agency's consolation prize. It is agency's definition.

## The Thermodynamics Parallel

The correspondence with classical thermodynamics is not decoration; it is structural, law by law.

| Thermodynamic Laws of Agency | Classical Thermodynamics |
| --- | --- |
| Control Work (energy required) | First Law (energy conservation) |
| Agency Decay (agency reduction) | Second Law (entropy increase) |
| Agency Limits (control constraints) | Third Law (unattainability of absolute zero) |

The first pair share a conservation logic: energy is neither created nor destroyed, only converted — and control is one of the things it converts into, at a fixed minimum rate. The second pair share a direction of time: entropy increases in isolated systems, and agency, which is purchased from the free energy entropy consumes, declines in step. The third pair share an asymptote: absolute zero and absolute control are the same kind of impossibility, a limit that can be approached at exponentially growing cost but never reached.

The parallel is exact in structure, but the two sets of laws are not the same laws, and the differences matter as much as the correspondence. Classical thermodynamics describes universal physical systems with complete indifference to purpose; the agency laws specifically address intentional action — what it costs a system to have preferences about the future and act on them. Classical thermodynamics quantifies disorder with entropy; the agency framework quantifies intentional control with kybits. And where the classical laws strictly describe physical processes, the agency laws deliberately bridge physics and intentionality — they are the point where thermodynamic constraint meets meaningful choice. The three laws of agency do not compete with thermodynamics. They enrich it, extending its bookkeeping to the one class of physical systems that keeps books of its own.

## Objections

A framework that claims this much owes answers to the hard questions. These are the strongest objections I know, answered rather than hidden.

**In a branching universe, everything happens anyway — so what difference does agency make?** This is the deepest challenge, and I will not soften the claim it targets. In the Quantum Branching Universe (QBU) — the Everettian picture developed in full in [its own chapter](08-the-quantum-branching-universe.md) — all physically possible outcomes occur in some branch. If every future happens, steering can look pointless. The answer is that Measure matters. Each branch carries a Measure — the objective weight determined by the squared quantum amplitude, defined precisely in [Measure, Vantage, Branchcone](09-measure-vantage-branchcone.md) — and my claim, the most contestable claim in this framework, is that agency directs Measure toward preferred branches. An agent does not select which futures exist; it influences which futures flourish — how much weight flows to the branches it prefers, and which versions of itself become more prominent. I state this openly as a commitment of the framework rather than a theorem of it: the thermodynamic accounting in this chapter tells us what steering costs, while the claim that the steering shifts Measure is the bridge between the physics of control and the physics of branching. Whether that bridge can be built from derivation rather than assertion is an honest open problem, and I keep the ledger on it in [Agency in the Emergent Multiverse](13-agency-in-the-emergent-multiverse.md). What I will insist on here is that the claim is not idle: it is what makes the energy expenditure of the first law an investment rather than a ritual, and it is why [measure responsibility](../05-value-and-ethics/21-measure-responsibility.md) can carry ethical weight downstream.

**Doesn't controlling branch Measure violate the deterministic evolution of the wavefunction?** No. Agents violate neither determinism nor unitarity. An agent is part of the wavefunction, not an intervention on it from outside: it locally entangles with environmental degrees of freedom, and its internal predictive models shape the conditional correlations among branching pathways. "Control" in this framework means biasing local correlations — being the kind of physical structure whose presence makes preferred outcomes correlate with its actions — not editing global physics. The global evolution is exactly as deterministic with agents in it as without them; what agents change is the local structure of what correlates with what.

**Where do kybits exist, physically?** At the agent-environment interface. Kybits are emergent, macro-level quantities — like temperature, they do not appear in the microphysical state description, and like temperature, they are no less real for that. They quantify the extent to which an agent shapes branching futures through internal prediction and deliberate action, and they live at the intersection of three processes: prediction, intentional action, and environmental decoherence. Ask where a kybit is located and you have made a category error; ask what physical difference it measures and the answer is exact.

**What physical process actually burns the energy?** Every intentional action runs on dissipative physical machinery: neural processing and computation, muscle contraction and movement, the actuation of sensors and motors. Shaping the future intentionally requires irreversible, entropy-generating physical processes — the same kind of cost Landauer identified for erasing information, extended here to steering outcomes. No act of agency is thermodynamically free, and the first law is just this fact stated as an exchange rate.

**Why coin new terms at all — can't existing theories cover this?** Each existing theory covers a facet. Decoherence explains quantum branching; cybernetics describes feedback and control loops; information theory quantifies uncertainty. None of them integrates these into a single framework in which agent-driven shaping of branching futures is clearly quantified, thermodynamically grounded, and linked explicitly to evolutionary and ethical dynamics. The kybit is not a rebranding of an existing quantity; it is the unit that lets those separate literatures share a ledger.

Criticism does not weaken this framework; it refines it. And what survives the refinement is the picture the three laws jointly paint: intentional action is real, it is costly, and it is fragile — a physical achievement wrested, at a metered price and for a limited time, from a universe whose default is drift. The laws are not the enemies of agency. They are the reason it counts.
