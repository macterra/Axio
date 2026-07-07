---
title: 'Causality and Counterfactuals'
subtitle: 'Cause as branch structure'
status: draft
sources:
  - 163348907.a-rigorous-definition-of-causality
  - 164572808.do-ideas-move-atoms
  - 165063201.yes-we-can-assign-probabilities-to
---

Alice flips a switch, and a moment later the lamp turns on. Everyone agrees the flip caused the light. Almost no one can say what that claim means.

The oldest answer, Hume's, is regularity: flips of this kind are constantly conjoined with lightings of that kind. But regularity is too weak — night regularly follows day without causing it — and every attempt to patch it smuggles in the very notion it was supposed to explain. The modern answer, due mainly to David Lewis, is counterfactual: the flip caused the light because *if Alice had not flipped the switch, the lamp would not have turned on*. That gets the logic right. Causal claims really are claims about what would have happened otherwise; that is why we test drugs against control groups and assign blame by asking what the defendant could have done differently.

The trouble is what the counterfactual is supposed to be *about*. Lewis evaluated "if a had occurred, b would have occurred" by consulting the nearest possible worlds in which a occurs and checking whether b occurs there too. Nearest by what metric? Among worlds that exist in what sense? Possible-world semantics runs on a similarity ordering nobody can define and an ontology nobody believes in. The counterfactual analysis of causation is a correct theory with its foundations missing: right about the logic, embarrassed about the metaphysics.

The [Quantum Branching Universe](08-the-quantum-branching-universe.md) (QBU) supplies the missing foundations, because it already contains, as physical fact, exactly the structure Lewis had to invent. Reality is a branching set of quantum timelines, diverging at discrete quantum events. Each branching event is a node from which timelines split according to different outcomes; each timeline is a sequence of causally linked events; and timelines share common ancestors, which means "the closest alternative timelines" is not a metaphor in search of a metric but a definite region of a real structure. The nearest worlds in which Alice does not flip the switch are the branches that split off from ours at the last event where both futures were still open. They are not philosophers' fictions. They are out there, running.

## The Definition

Given two events, a and b, find their nearest common ancestor event $E_0$ in the branching structure — the latest event from which both a-containing and a-lacking timelines descend. Counterfactual implication is then defined as

$$
(a \,\square\!\!\to\, b) \quad \text{iff} \quad \forall\,T:\,(E_0 \prec T \wedge a \in T) \rightarrow b \in T
$$

where $E_0 \prec T$ means that $E_0$ is an ancestor event of timeline $T$, and $a \in T$ means that event a happens within timeline $T$. In plain terms:

> Starting from the common ancestor event $E_0$, every descendant timeline containing event a also contains event b.

That is the sufficiency half of causation: given the shared past, a is enough to guarantee b. Full causation adds a dependence half — remove a from the ancestor timeline and b vanishes from every descendant branch. So **a causes b** if and only if two conditions hold:

1. **Ancestor–descendant relationship.** All timelines containing b descend from a common ancestor containing a.
2. **Counterfactual dependence.** Removing a from that ancestor removes b from all the timelines branching from it.

Together they say: with a, always b; without a, no b — quantified over actual branches rather than imagined worlds.

The events themselves are picked out by Strong Pattern Identifiers — the reproducible quantum, atomic, or neural configurations that, as [The Quantum Branching Universe](08-the-quantum-branching-universe.md) establishes, guarantee a common causal ancestor for every timeline containing them. That guarantee is what makes the definition well-posed: a Strong PI ensures that $E_0$ exists and that "the same event" across branches means something.

Run the lamp through it. Event a is "Alice flips the switch at time t"; event b is "the lamp turns on at $t + \Delta t$." All descendant timelines from $E_0$ in which Alice flips the switch also contain the lamp turning on, and the timelines branching from $E_0$ in which she does not flip it do not. Both conditions hold, so

$$
(\text{Alice flips switch}) \,\square\!\!\to\, (\text{Lamp turns on})
$$

and the everyday causal claim is cashed out, without remainder, as a fact about branch structure.

Notice what the definition buys. The asymmetry of causation — a causes b, never the reverse — falls out of the geometry rather than being stipulated: the quantification runs forward from $E_0$ down the descendant branches, and the branching structure is a directed graph in which ancestors precede descendants. Lewis's similarity metric is replaced by ancestry, which is objective. And the modal mystery evaporates: "would have" is quantification over branches that exist.

A definition earns its keep by what it settles. Here are two questions it settles immediately.

## Do Ideas Move Atoms?

In our brains, do ideas push around atoms, or do the atoms push the ideas? The question sounds like a koan, and centuries of dualist and epiphenomenalist hand-wringing have treated it as one: surely only physical things can cause physical things, so either ideas are causally inert passengers or something spooky is going on.

Apply the definition instead. Ideas are neural activation patterns — Strong Pattern Identifiers at the neural level — and neural activation patterns correspond precisely to atomic configurations and quantum states. So take Idea A and Idea B as events and run the two conditions. Ancestor–descendant relationship: the atomic patterns constituting Idea B cannot arise unless the ancestor atomic and neural patterns of Idea A are present. Counterfactual dependence: remove the neural — and therefore atomic — pattern of Idea A from the ancestor timeline, and the atomic patterns of Idea B fail to occur in every descendant branch. Both conditions hold. By exactly the standard that certifies the switch causing the lamp:

> Ideas, as neural patterns, cause atomic events.

There is nothing spooky in this, and the software analogy shows why. Nobody blinks at the claim that software controls hardware — that a program moves electrons through circuits — even though the program is "just" a higher-level description of what the electrons are doing. Software is a pattern implemented in physics that satisfies the causal conditions with respect to physical outcomes. Ideas stand to brains as software stands to circuits: a higher-level semantic process implemented in neural states. If software can move electrons, ideas can move atoms.

The residual puzzle — how can there be two causes for one event? — dissolves once you see that the two descriptions run in parallel rather than in competition. Physically, atoms push atoms. Semantically, ideas push ideas. Brains are remarkable precisely because evolution has aligned the two causal ledgers, so that the atomic story and the semantic story track the same branch structure. When you say an idea caused your action, you are not speaking loosely or metaphorically pending a real atomic explanation; you are stating a causal fact that holds as rigorously at the semantic level as the atomic facts hold at theirs. Mental causation is not an exception the theory must apologize for. It is an instance.

## Probabilities for Things That Don't Happen

The second question is a standing objection to the whole counterfactual program: if causation is predicated on counterfactuals, it cannot be probabilistic, because we cannot assign probabilities to things that don't happen. A probability of an event that never occurs, the objection runs, is a number about nothing.

The objection is exactly right — given its premise. If the counterfactual branches are non-real, mere imaginings, then there is nothing for the probability to be a property *of*, and probabilistic causation inherits all the groundlessness of the possible worlds it quantifies over. This is the same foundations problem as before, resurfacing in probabilistic dress.

And it has the same resolution. In the QBU, the counterfactuals are not hypothetical imaginings; they are actualized, concrete branches of an objectively real universal wavefunction. What "doesn't happen" from our vantage does happen elsewhere in the branching structure. And each branch carries an objective weight — its [Measure](09-measure-vantage-branchcone.md) — which is a physical quantity, not a degree of belief. So assigning a probability to a counterfactual is not putting a number on nothing; it is reporting the Measure of a real set of branches. "Had Alice not flipped the switch, the lamp would probably still have been off at midnight" is a claim about the Measure-weighted proportion of no-flip branches in which the lamp stays dark — as objective as any other physical magnitude.

Causation, then, is a relationship between branches, actual and counterfactual alike, and probability is the objective Measure of those relationships across the multiverse. Deterministic causation is the special case where the descendant branches are unanimous; probabilistic causation is the general case where a shifts the Measure of b without fixing it. One framework, no discontinuity — and the objection, far from being fatal, turns out to mark exactly the fork in the road: whether you can have both counterfactual causation and probability depends on whether the counterfactual branches are real. Grant the branching structure and you get both. Deny it and you must give one up.

That is also where causation joins prediction. [Knowledge, on my account](../02-conditionalism/09-what-knowledge-is.md), is pattern-encoded structure that reliably reduces an agent's entropy about future events across branching timelines — and causal knowledge is the strongest form it takes, because knowing that a causes b is knowing the branch structure itself: which futures contain b given a, and with what Measure. A correlation lets you predict from where you happen to stand; a causal relation tells you what every branch downstream of an intervention looks like, which is why it survives the move from observing to acting. Agents care about causation because agents are in the steering business, and steering — spending work to shift Measure toward preferred branches — presupposes exactly the counterfactual facts this definition supplies. What an agent buys with its kybits is a difference between branches; causality is the structure that makes there be a difference to buy.
