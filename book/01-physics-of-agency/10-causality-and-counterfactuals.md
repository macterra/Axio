---
title: 'Causality and Counterfactuals'
subtitle: 'Cause as branch structure'
status: review
sources:
  - 163348907.a-rigorous-definition-of-causality
  - 164572808.do-ideas-move-atoms
  - 165063201.yes-we-can-assign-probabilities-to
---

Alice flips a switch, and a moment later the lamp turns on. Everyone agrees the flip caused the light. Almost no one can say what that claim means.

The oldest answer, Hume's, is regularity: flips of this kind are constantly conjoined with lightings of that kind. But regularity is too weak — night regularly follows day without causing it — and every attempt to patch it smuggles in the very notion it was supposed to explain. The modern answer, due mainly to David Lewis, is counterfactual: the flip caused the light because *if Alice had not flipped the switch, the lamp would not have turned on*. That gets the logic right. Causal claims really are claims about what would have happened otherwise; that is why we test drugs against control groups and assign blame by asking what the defendant could have done differently.

The trouble is what the counterfactual is supposed to be *about*. Lewis evaluated “if a had occurred, b would have occurred” using nearby possible worlds, which requires a similarity ordering. Modern causal models instead represent interventions explicitly, but they still require judgments about variables, structural equations, and which background conditions remain fixed. Counterfactual analysis gets the logic right; no ontology eliminates the modeling choices.

The [Quantum Branching Universe](08-the-quantum-branching-universe.md) (QBU) adds a physical interpretation of alternative outcomes and their weights. It does not automatically identify the correct intervention or nearest comparison history. The graph supplies ancestry and Measure once a coarse-graining is specified; a causal model must still say what counts as Alice's action, what is held fixed, and which differences are irrelevant.

## The Definition

Given a Vantage $V$, a causal model $M$, an intervention on $a$, and an outcome $b$, compare the conditional Measure of $b$ under the intervention with its Measure under an appropriate contrast intervention:

$$
\Delta_a b = \mu_V(b\mid do(a),M) - \mu_V(b\mid do(\neg a),M).
$$

Then:

> **Event $a$ is a cause of $b$, relative to $V$ and $M$, when intervening on $a$ changes the Measure of $b$ relative to the specified contrast, with the causal path respecting the QBU's ancestry relation.**

The deterministic case is the limit in which $\mu_V(b\mid do(a),M)=1$ and $\mu_V(b\mid do(\neg a),M)=0$. Most causes are not like that. They raise or lower an outcome's Measure without guaranteeing it. The definition therefore has three explicit dependencies:

1. **Representation.** The events and histories have been defined at a relevant coarse-graining.
2. **Intervention model.** The contrast specifies what is changed and what is held fixed.
3. **Measure difference.** The intervention changes the outcome's conditional weight.

Ancestry rules out backward paths within the QBU representation; it does not by itself establish dependence. The intervention comparison does that work.

The events are picked out by Pattern Identifiers. When identity across histories matters, a Strong PI must include provenance from a declared ancestor; descriptive precision alone does not guarantee a common origin.

Run an ideal lamp through it. Event $a$ is “Alice flips the switch at time $t$”; event $b$ is “the lamp turns on at $t+\Delta t$.” In a model that holds the power supply, bulb, and wiring fixed, suppose the flip makes the Measure of illumination nearly one while the no-flip intervention leaves it near zero. Then $\Delta_a b$ is large and positive, so

$$
(\text{Alice flips switch}) \,\square\!\!\to\, (\text{Lamp turns on})
$$

and the everyday causal claim is represented as a model-relative intervention fact with physical weights.

The QBU contributes temporal ancestry and an Everettian interpretation of the weighted alternatives. The causal model contributes the intervention and comparison class. Neither can replace the other. Overdetermination, preemption, feedback, and coarse-graining remain hard cases; the definition is a framework for stating them, not a claim that ancestry alone has settled them.

A definition earns its keep by what it settles. Here are two questions it settles immediately.

## Do Ideas Move Atoms?

In our brains, do ideas push around atoms, or do the atoms push the ideas? The question sounds like a koan, and centuries of dualist and epiphenomenalist hand-wringing have treated it as one: surely only physical things can cause physical things, so either ideas are causally inert passengers or something spooky is going on.

Apply the definition at the right grain. Ideas are higher-level patterns implemented by neural activity. If interventions that preserve the relevant background while changing whether pattern A is instantiated systematically change the Measure of later neural or behavioral outcome B, then A is causally relevant at that level. The intervention may be experimental, computational, or counterfactual; what matters is that the macrovariable supports stable difference-making rather than merely redescribing the outcome after the fact.

> Ideas, as neural patterns, cause atomic events.

There is nothing spooky in this, and the software analogy shows why. A program is a higher-level description implemented by physical states, yet changing the program while holding hardware conditions appropriately fixed changes the machine's behavior. Ideas can be causally explanatory in the same intervention-supporting sense.

The atomic and semantic descriptions need not compete for one causal slot. They track the same process at different grains and answer different interventions. The higher-level claim is rigorous only where its variables remain stable under the comparison; not every story a mind tells about its motive will pass that test.

## Probabilities for Things That Don't Happen

The second question is a standing objection to the whole counterfactual program: if causation is predicated on counterfactuals, it cannot be probabilistic, because we cannot assign probabilities to things that don't happen. A probability of an event that never occurs, the objection runs, is a number about nothing.

The objection confuses non-actual with measureless. Standard causal models assign probabilities under interventions without requiring that every alternative be a concrete world. The QBU offers a stronger ontological reading: alternative decoherent outcomes are components of the quantum state and carry Born Measure. On that reading, “Had Alice not flipped the switch, the lamp would probably still have been off” reports $\mu_V(\text{off}\mid do(\neg\text{flip}),M)$.

Deterministic causation is the limiting case where the intervention drives the relevant Measure to zero or one; probabilistic causation changes it without fixing it. Everettian ontology is one way to interpret those weights physically, not a prerequisite for probabilistic causal reasoning.

That is where causation joins prediction. [Knowledge, on my account](../02-conditionalism/09-what-knowledge-is.md), is pattern-encoded structure that reliably reduces an agent's uncertainty about relevant futures. A correlation predicts under observation; a causal model predicts under intervention. Agents need the latter because control is evaluated against alternative policies. The kybit can summarize the resulting distributional difference only after this causal structure has supplied the baseline.
