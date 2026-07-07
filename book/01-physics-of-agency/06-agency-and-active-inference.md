---
title: 'Agency and Active Inference'
subtitle: 'The Friston bridge'
status: draft
sources:
  - 163365017.active-inference-and-the-physics
---

There is a standing test for any framework that claims to describe something real rather than something invented: other people, starting from different problems with different tools, should keep running into the same structure. If they never do, the framework is probably an artifact of its own vocabulary. If they do — independently, repeatedly, in detail — that is evidence the framework has hold of a joint in nature.

The physics of agency passes this test, and the examiner is Karl Friston.

Friston's free-energy principle began as a unified theory of the brain and grew into something more ambitious: an account of what any self-maintaining system must do to keep existing. On this picture, every organism — every cell, every brain, every agent — carries an internal model of its world and works ceaselessly to keep that model and the world in registration. It has two moves available. It can update the model to fit the sensory evidence, which is perception. Or it can act on the world until the evidence fits the model, which Friston calls *active inference*. Both moves minimize the same quantity: variational free energy, a measurable bound on how surprised the system is by what its senses report. An agent, in this framework, is a machine for driving prediction error down — and a system that stops doing so stops persisting.

I arrived at [the three laws of agency](04-the-three-laws-of-agency.md) from a different direction entirely: from thermodynamics, from Landauer's principle, from asking what it physically costs to steer the probability distribution over outcomes — the cost quantified in [kybits](03-the-kybit.md). Nothing in that derivation mentions brains, prediction, or free energy. Yet when the two frameworks are laid side by side, the correspondence is not loose analogy. It is one-to-one, law by law.

## The First Law: Control Is Work

The first law says that exercising intentional control over outcomes requires physical work, in proportion to the kybits exerted — every bit of steering has a thermodynamic price, and there is no way to pay less than the floor.

Active inference says the same thing in its own notation. An agent acts to reduce the prediction errors between its internal model and its sensory data, and those errors are *precision-weighted*: errors the agent must resolve with high confidence count for more than errors it can afford to leave sloppy. The informational complexity the kybit measures — how far, and how reliably, the agent shifts the outcome distribution away from what would have happened without it — corresponds directly to the precision-weighted prediction error the agent must eliminate. Forcing the world to match a prediction *is* shifting an outcome distribution; demanding higher precision *is* demanding more kybits. The greater the complexity and the tighter the precision required to align prediction with sensation, the more physical and informational work the alignment costs. The two frameworks are keeping the same ledger. One writes the entries in kybits, the other in free energy, and the currencies convert.

## The Second Law: Agency Decays

The second law says that in a closed system, without external energy input, agency inevitably diminishes. Control capacity is not a possession; it is a process that must be fed.

Active inference explains the mechanism. Minimizing free energy is not something an agent does once; it requires continuous informational and energetic exchange with the environment, because the environment does not hold still. Seal the agent off and its prediction errors begin to accumulate: with no fresh input against which to update and refine its model, the model drifts out of registration with a world that keeps changing without it. The internal structures that carry the agent's predictive capacity degrade, and with them goes its ability to control anything. This is the same lesson that runs through the epistemology of [maps and models](../02-conditionalism/06-maps-models-understanding.md): a model is only as good as the traffic between it and the territory. Cut the traffic and the map goes stale — and an agent steering by a stale map is an agent losing agency, exactly as the second law demands. What thermodynamics states as a decay law, active inference exhibits as a mechanism: isolation starves the model, the starving model mispredicts, and misprediction is the death of control.

## The Third Law: No Perfect Control

The third law says that perfect, frictionless control is physically impossible. There is no agent, actual or constructible, that steers outcomes without residue.

Friston's framework does not merely tolerate this limit; it has the limit built into its mathematics. Variational free energy can be driven down but never to zero. The minimization is *variational* — approximate by construction — and it is bounded below by irreducible uncertainty, environmental fluctuation, sensory noise, and the inaccuracies of any finite model. However finely tuned and energetically well-supplied a predictive system is, a mismatch between internal prediction and external reality always remains. Residual error is not an engineering shortfall awaiting a cleverer design; it is constitutive of what a model-driven agent is. Absolute predictive precision, and with it frictionless control, is fundamentally unattainable — which is the third law, stated in a different dialect.

## Two Roads, One Structure

Take stock of what just happened. A framework built from the thermodynamics of control — Landauer costs, divergences between outcome distributions, the physics of steering — was set beside a framework built from the statistical physics of self-organizing systems and the neuroscience of prediction. Neither was derived from the other. They do not share a vocabulary, a lineage, or a motivating problem. And they agree point for point: control costs work in proportion to its informational demands; control capacity decays without continuous exchange with the environment; perfect control is impossible in principle.

The convergence is itself the argument. When two independently constructed maps agree on the terrain, the likeliest explanation is that both are maps *of* the terrain. It could be coincidence; it could be a shared hidden error; convergence is evidence, not proof. But it is exactly the kind of evidence that science runs on, and it cuts both ways. Active inference gives the three laws a mechanism — it says *where* the work of control actually goes, into building, running, and correcting predictive models against a world that never stops generating surprises. The three laws give active inference its price tag — they anchor the free-energy story in thermodynamic constraints that no implementation can evade. What emerges from the union is a single picture of agency as a physical process: predictive control, purchased with work, sustained by exchange, and bounded by irreducible error. Two roads, cut through different country, arriving at the same place — because there is one place to arrive at.

## References

This volume mostly travels without scholarly apparatus, but the free-energy framework is Friston's, and the debt should be paid in the standard coin:

1. Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.
2. Friston, K. J., Parr, T., & de Vries, B. (2017). The graphical brain: Belief propagation and active inference. *Network Neuroscience*, 1(4), 381–414.
3. Friston, K. (2013). Life as we know it. *Journal of the Royal Society Interface*, 10(86), 20130475.
4. Parr, T., & Friston, K. J. (2019). Generalised free energy and active inference. *Biological Cybernetics*, 113(5–6), 495–513.
5. Friston, K. J., Da Costa, L., & Parr, T. (2020). Some interesting observations on the free-energy principle. *Entropy*, 22(12), 1387.
6. Clark, A. (2015). *Surfing Uncertainty: Prediction, Action, and the Embodied Mind*. Oxford University Press.
