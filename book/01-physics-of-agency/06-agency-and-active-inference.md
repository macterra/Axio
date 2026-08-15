---
title: 'Agency and Active Inference'
subtitle: 'The Friston bridge'
summary: >-
  Active inference and the free-energy principle offer a mature vocabulary for systems that maintain themselves by modeling and acting on their environments. That vocabulary has a partial structural correspondence with agency understood as distributional control. Both frameworks describe organized systems whose internal models guide action toward a restricted range of states, and both connect persistence to active correction. The bridge is deliberately limited, however, because variational free energy, prediction error, precision, thermodynamic work, and kybit counts are distinct quantities rather than currencies with a law-by-law conversion. Under an equilibrium-reference realization, minimum-work results may constrain implementation, but they do not establish a universal energetic price per kybit. Convergence between the frameworks is therefore evidence of a shared problem structure, not proof that either formalism derives the other or explains phenomenality. A quantitative bridge would still have to specify the physical realization, the relevant distributions, and the conditions under which the functional analogy becomes informative.
status: review
sources:
  - 163365017.active-inference-and-the-physics
---

There is a standing test for any framework that claims to describe something real rather than something invented: other people, starting from different problems with different tools, should keep running into the same structure. If they never do, the framework is probably an artifact of its own vocabulary. If they do — independently, repeatedly, in detail — that is evidence the framework has hold of a joint in nature.

The physics of agency meets that test in the work of Karl Friston.

Friston's free-energy principle began as a unified theory of the brain and grew into something more ambitious: an account of what any self-maintaining system must do to keep existing. On this picture, every organism — every cell, every brain, every agent — carries an internal model of its world and works ceaselessly to keep that model and the world in registration. It has two moves available. It can update the model to fit the sensory evidence, which is perception. Or it can act on the world until the evidence fits the model, which Friston calls *active inference*. Both moves minimize the same quantity: variational free energy, a measurable bound on how surprised the system is by what its senses report. An agent, in this framework, is a machine for driving prediction error down — and a system that stops doing so stops persisting.

I arrived at [the three laws of agency](04-the-three-laws-of-agency.md) from a different direction entirely: from thermodynamics, from Landauer's principle, from asking what it physically costs to steer a probability distribution over outcomes — with the distributional shift quantified in [kybits](03-the-kybit.md). Nothing in that argument begins from brains, prediction, or variational free energy. Set the two frameworks side by side and a structural correspondence appears, law by law — striking enough to demand an explanation, but short of a derivation or a conversion between their quantities. It is evidence that both frameworks have hold of the same problem.

## The First Law: Control Is Work

The first law says that steering outcomes costs physical work — control is never free. How much work depends on the physics of the implementation: only under an equilibrium-reference realization does the distributional divergence pin the price to a definite floor, below which no such implementation can pay.

Active inference describes a related implementation problem in its own notation. An agent acts to reduce prediction errors between its internal model and sensory data, and those errors are *precision-weighted*: errors treated as reliable count differently from signals treated as noisy. Acting to make observations fit a prediction can change an outcome distribution, while sensing, inference, and actuation consume physical resources. But variational free energy is not a kybit count, precision-weighted error is not KL divergence from an inactive-policy baseline, and neither quantity generally determines the other's energetic cost. The correspondence is functional: both frameworks require an embodied control loop with a physical ledger. A quantitative bridge would need a shared causal model and an explicit thermodynamic realization.

## The Second Law: Agency Decays

The second law says that an isolated agent with finite usable resources cannot renew its total remaining control budget indefinitely. Control capacity is not a possession; it is a process that must be fed.

Active inference explains the mechanism. Minimizing free energy is not something an agent does once; it requires continuous informational and energetic exchange with the environment, because the environment does not hold still. Seal the agent off and its prediction errors begin to accumulate: with no fresh input against which to update and refine its model, the model drifts out of registration with a world that keeps changing without it. The internal structures that carry the agent's predictive capacity degrade, and with them goes its ability to control anything. This is the same lesson that runs through the epistemology of [maps and models](../02-conditionalism/06-maps-models-understanding.md): a model is only as good as the traffic between it and the territory. Cut the traffic and the map goes stale — and an agent steering by a stale map is an agent losing agency, exactly as the second law demands. What thermodynamics states as a decay law, active inference exhibits as a mechanism: isolation starves the model, the starving model mispredicts, and misprediction is the death of control.

## The Third Law: No Perfect Control

The third law says that perfect, frictionless control is physically impossible. There is no agent, actual or constructible, that steers outcomes without residue.

Friston's framework does not promise frictionless control. Variational inference is performed by a finite model through limited observations and actions; real agents face environmental fluctuation, sensory noise, model error, and finite precision. A particular free-energy value need not translate directly into control capacity, and the formal objective alone does not prove the third law. It does exhibit the same bounded architecture: no amount of tuning a model or sharpening a policy buys complete access, perfect prediction, or costless action. The residual mismatch between prediction and world is not an engineering shortfall awaiting a cleverer design — it is constitutive of what a finite, embedded agent is.

## Two Roads, One Structure

Take stock of what just happened. A framework built from the thermodynamics of control — physical implementation costs, divergences between outcome distributions, the constraints on steering — was set beside a framework built from the statistical physics of self-organizing systems and the neuroscience of prediction. Neither was derived from the other. They do not share a vocabulary, a lineage, or a motivating problem. Yet they converge on a bounded picture: control has informational demands and physical costs; sustained organization depends on exchange with an environment; finite embedded systems do not achieve perfect control.

The convergence is evidence, not proof. It could reflect a shared problem, a productive analogy, or a shared hidden error — and it cuts both ways. Active inference offers the three laws a candidate mechanism — where control work goes: into building, running, and correcting predictive models against a world that never stops generating surprises. The three laws hand active inference a set of constraints — that any implementation, whatever its notation, must face physical bookkeeping and boundedness. What they do not yet share is a proof that the two ledgers are one. That is the open problem: to show when predictive control, distributional divergence, variational free energy, and work can be tied into a single causal model. Two roads, cut through different country, reaching a common pass — without yet proving that they end at the same place.

## References

This volume mostly travels without scholarly apparatus, but the free-energy framework is Friston's, and the debt should be paid in the standard coin:

1. Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.
2. Friston, K. J., Parr, T., & de Vries, B. (2017). The graphical brain: Belief propagation and active inference. *Network Neuroscience*, 1(4), 381–414.
3. Friston, K. (2013). Life as we know it. *Journal of the Royal Society Interface*, 10(86), 20130475.
4. Parr, T., & Friston, K. J. (2019). Generalised free energy and active inference. *Biological Cybernetics*, 113(5–6), 495–513.
5. Friston, K. J., Da Costa, L., & Parr, T. (2020). Some interesting observations on the free-energy principle. *Entropy*, 22(12), 1387.
6. Clark, A. (2015). *Surfing Uncertainty: Prediction, Action, and the Embodied Mind*. Oxford University Press.
