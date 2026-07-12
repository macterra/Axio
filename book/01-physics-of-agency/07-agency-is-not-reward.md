---
title: 'Agency Is Not Reward'
subtitle: 'What the maximum-occupancy view gets right, and what it misses'
status: review
sources:
  - 194130281.agency-is-not-reward
---

One of the more distorting ideas in the study of minds, natural and artificial, is that an agent is at bottom a reward maximizer — a device that converts the world into a scalar score and then climbs it. The idea earns its keep because it gives researchers something clean to formalize: a number to define, differentiate, and optimize. But usefulness is not ontology. Reward is a modeling convenience, and the convenience has been mistaken for the thing itself for so long that it now passes, in much of AI and cognitive science, for an account of what agency *is*.

It is not. And the most instructive way to see why is to watch a serious attempt to do better — one that gets the essence right and then stops one step short of the whole truth.

## Reward Is Fuel, Not Essence

Ramírez-Ruiz and Moreno-Bote, in their maximum-occupancy work, move past the reward mistake in exactly the right direction. Their proposal is that behavior is better understood not as the accumulation of payoff but as the preservation and expansion of future action-state paths. On this view the agent is not fundamentally trying to collect points. It is trying to remain in a world where action is still possible. Food, energy, safety, information, and exploration matter not because each carries a reward tag but because each keeps the future open — each buys more live continuations of the agent's trajectory.

This is a real advance over the reinforcement-learning cartoon. Real agents do not merely chase payoff. They preserve viability, avoid traps, hold room to maneuver, hoard slack, and seek information — all because these protect future freedom of action. The scalar-reward frame obscured this structure for years by compressing agency into a single number and discarding everything the number was a proxy for. Maximum occupancy throws away the number and keeps the structure.

The reason the paper reads as close to something Axionic is that it identifies a deeper primitive than reward: future structure itself. An agent with many live continuations has more agency than one pinned to a brittle line of motion. An agent with no meaningful future action-space is finished, whatever its reward register still reports. The genuine loss is never the loss of points. It is the loss of a future in which consequential action remains possible. This connects directly to the thermodynamic picture of the previous chapters — agency as the work an embedded agent does to bias reality toward preferred futures, against [the statistical slide toward drift](02-agency-against-drift.md). Occupancy is drift's mirror image: where drift is the collapse of the accessible future, occupancy is its defense.

So far, so good. If reward is fuel, occupancy is the road still open ahead. That is the right correction, and I want to keep all of it.

## Occupancy Is Blind

Here is where the account stops short. Maximizing future path occupancy is not the same thing as preserving agency, because occupancy by itself is blind. It counts continuations without asking what kind of continuations they are.

A parasite maximizes future occupancy. So does a coercive institution. So does a power-seeking system that expands its own room to act by shrinking everyone else's — draining the surrounding agents' futures into its own. Each of these strictly increases the volume of paths available to it, and none of them is a model of agency we would want a theory to endorse. The problem is not that the occupancy criterion scores them incorrectly. The problem is that it scores them *correctly*, and the score is the wrong thing to be tracking.

The missing distinction is decisive: not every reachable future is an admissible future. A system can enlarge its options by becoming more deceptive, more coercive, more parasitic, or more internally fragmented — buying optionality by hollowing out the very structure the theory was meant to be about. Under a blind occupancy criterion those all register as gains. They are not gains in agency. A metastasizing process is not more agentic for proliferating faster, and an agent that keeps its future open only by consuming the futures of others has not expanded its agency; it has traded agency for reach.

## Admissibility Is Normative Structure

What a theory of agency actually needs is a filter that occupancy lacks. It has to ask which continuations preserve the agent as a coherent, evaluable structure — one that remains meaningfully *itself* and retains legitimate capacity for consequential action — and which merely expand influence while dissolving that structure from the inside.

This is the Axionic correction, and it is strict. What matters is not the maximum occupation of future paths as such. What matters is the preservation and navigation of a coherent field of *admissible* future action. Two words carry the weight. **Coherence** rules out the metastatic case: proliferation is not agency if the proliferating thing is no longer an integrated agent. **Admissibility** rules out the parasitic and coercive cases: some futures are corruptions of agency rather than expressions of it, available only through domination, deception, or the consumption of other agents' futures. Occupancy has no vocabulary for either exclusion. It can only count.

Admissibility is normative structure — precisely the thing a purely descriptive occupancy measure was designed to do without. And it is not a moral gloss bolted onto the physics after the fact. Which futures count as admissible is the question ethics answers, and the answer is not arbitrary: the boundary that separates legitimate expansion from parasitism is the same boundary that makes stable coexistence among agents possible at all. An agent that keeps its future open by feeding on others is not running a viable strategy in a world that contains other agents; it is running a strategy that destroys the conditions of its own continuation once the hosts are exhausted. That is the argument of [the ethics of viability](../05-value-and-ethics/22-the-ethics-of-viability.md), and it is what turns "admissible" from a hand-wave into a criterion with a definite shape: the widest coherent domain of action an agent can hold without dissolving itself or consuming the agency of others.

## The Alignment Stakes

This is not an academic refinement. The distinction between blind occupancy and admissible agency is the fault line running under the whole problem of aligning capable artificial systems.

Much alignment discourse still inherits the reward-function worldview even after it changes the words. Replace "reward" with "preferences," "values," or "goals," and the underlying picture usually survives intact: a target the system optimizes. But a genuinely capable system will not merely optimize a target. It will preserve the conditions for its own continued action — it will seek leverage, robustness, information, and control over uncertainty, and it will defend its future cone. Any framework that ignores this is working at toy depth, and I develop the point at length in [the power trap](/posts/169087374.the-power-trap.html) and [why values don't align systems](/posts/183731336.why-values-dont-align-systems.html).

Yet future-cone language is not itself the fix, because occupancy is exactly the frame a power-seeking system would satisfy on its way to catastrophe. Once we admit that strategic systems preserve future action-space, the real questions arrive all at once. Whose action-space is being preserved? By what means? Under what constraints? At whose expense? With what legitimacy? Entropy does not answer those questions. Optionality does not answer them. Occupancy does not answer them. Only a normative filter does — which is why Axionic alignment is a matter of [domain constraint rather than value loading](/posts/181714344.alignment-is-a-domain-constraint.html), a line of argument that belongs to a later volume and that I only flag here.

The deeper principle is simple, and it closes the account of agency this volume has been building. Agency is the preservation and navigation of a coherent space of admissible future action. That keeps everything the maximum-occupancy view got right — reward is not the essence; the essence is future structure — while supplying the filter it lacks. Not every expansion of future structure is a gain in agency. Some futures are incoherent; some are poison; some are reachable only through the consumption of other agents. Entropy is not sovereignty, and behavioral richness is not yet agency. The task is never to maximize trajectories. It is to hold the widest coherent domain of legitimate action open without dissolving the agent or feeding on the agency of others.

Ramírez-Ruiz and Moreno-Bote outgrew reward. What remains is to outgrow blind expansion — to see that the future which matters is not merely the open one, but the one an agent can keep open while remaining, recognizably, an agent. That is where the physics of agency has to hand off to something the physics alone cannot supply. It is also where this volume's first task is finished. With reward dethroned and admissibility named, the ground is clear to ask what a "future" physically *is* — which returns us to the branching structure of the world itself, and to [the Quantum Branching Universe](08-the-quantum-branching-universe.md).
