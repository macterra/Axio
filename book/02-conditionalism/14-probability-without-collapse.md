---
title: 'Probability Without Collapse'
subtitle: 'A conditional bridge from physical weight to credence'
status: review
sources:
  - 171824780.probability-without-collapse
---

Prepare an electron in a superposition weighted two to one and measure its spin. In Everettian quantum mechanics nothing collapses: the universal wavefunction branches, and both outcomes occur — one set of your future selves records spin-up, another records spin-down. Now repeat the experiment a thousand times. The lab notebook in front of you — the one in this branch — shows spin-up on about two-thirds of the runs, exactly as the Born rule prescribes: frequencies track the squared amplitude, $|\psi|^2$. But if every outcome occurs on every run, what is the "probability" of an outcome even supposed to mean? Why should the number two-thirds show up in anyone's notebook at all?

This is the notorious **probability problem**, and it is the standard indictment of the Everett interpretation. Collapse theories dodge the puzzle by fiat: they postulate that at each measurement exactly one outcome occurs, at random, with exactly the Born probabilities. That is not an explanation — it is the answer written directly into the axioms, and the purchase price is a mysterious, unobserved, dynamics-violating collapse process bolted onto an otherwise deterministic theory. Everett refuses to pay. The Schrödinger equation holds universally; every outcome happens in some branch of the Quantum Branching Universe (QBU) — the picture whose physical credentials I lay out in [Measure and Credence](11-measure-and-credence.md). But having refused collapse, the Everettian owes an account of what probability is doing in a theory where everything happens. Deterministic branching plus Born-rule experience: that is the debt this chapter pays.

## Three Failed Escapes

The literature offers several strategies. Each has strengths and disputed premises; the brief sketches below identify the gap this book's proposal tries to address.

**Declare amplitudes to be probabilities.** Zurek's envariance program tries to show that $|\psi|^2$ is objectively *the* probability measure, built into the symmetries of Hilbert space itself. The construction is elegant, but it does not by itself identify physical weight with an agent's uncertainty. No theorem about entanglement symmetries, however pretty, tells anyone what to *expect* — a measure defined on event sectors is not yet a degree of belief, and calling it one is the very step that needed justifying.

**Derive the Born rule from decision theory.** Deutsch, Wallace, and Sebens & Carroll argue that a rational agent in an Everettian universe must act *as if* branch weights are probabilities. This is closer to the truth — close enough that the argument below is its debtor. But the critics' accusation sticks: the derivations smuggle the Born rule in through rationality axioms that already presuppose it, constraints on preference whose innocence evaporates the moment you ask why a rational agent must obey them in a branching world.

**Shrug instrumentally.** Many working physicists simply shut up and calculate. Probability works in practice; why fuss over foundations? Because the fuss is the point: instrumentalism abandons exactly the promise that made Everett worth having — a fully coherent, universal quantum theory with no special rules for measurement. A model whose predictive recipe is accepted while its explanatory structure is declared off-limits has stopped doing the work we keep [models](06-maps-models-understanding.md) for.

Three different failures, one common root: none of them separates **what the world is like** from **how an embedded agent should reason about it**. The first tries to read epistemology directly off the ontology. The second tries to conjure the ontology's role out of pure epistemology. The third refuses to discuss either. The probability problem does not yield to any of these because it is not a problem *in* physics or a problem *in* epistemology — it is a problem about the bridge between them.

## Measure Is Not Credence

So build the bridge deliberately, starting from the distinction that the whole of this volume runs on.

**Measure** is a physical weight within the QBU model. For a specified state and record projector it is given by the Born expression; it is not a uniquely countable property of a fundamental branch, nor is it analogous in every respect to charge or spin. **Credence** is an agent's graded uncertainty about future observations or present self-location. Both can use probability mathematics, but their assignment rules and interpretations differ.

Keep them apart and the probability problem changes shape. Before the measurement, "you will see spin-up" has no unconditional truth value on the Everettian model — successor records exist for both nonzero alternatives. What the model offers is record-relative facts plus Measure over specified sectors; truth about outcomes, like [truth everywhere](02-all-truth-is-conditional.md), is conditional — here, conditional on a record. The proposed uncertainty is therefore not ignorance of some hidden cosmic coin flip but self-location within the represented structure. Whether that pre-observation attitude is genuine uncertainty remains a disputed premise, and Credence is the proposed way to represent it.

The question the probability problem was actually asking now stands exposed. It was never "what are the probabilities?" — the theory has no chancy events to pin them on. It was: **why should an agent's Credences track the branch Measures?** That is a normative question, and it gets a normative answer.

## The Regret Lemma

**Conditional claim.** Given a specified utility function, available bets, repeated trials, and Measure-weighted evaluation of descendants, a policy based on Credences that diverge from Measure can be outperformed by a Measure-aligned policy in high-Measure sectors.

Watch it work on the electron. The Measures are $2/3$ spin-up, $1/3$ spin-down; suppose your Credences are an indifferent one-half each. I offer you even odds on spin-down: stake ten dollars to win ten. By your Credences the bet is fair, and with any sweetener you take it. Then the world branches. Your spin-down descendants collect; your spin-up descendants pay; and the descendants who pay carry two-thirds of the Measure. Run the policy repeatedly and the arithmetic compounds: over many trials, the Measure of descendants whose observed frequencies stray far from two-thirds shrinks toward zero — the law of large numbers, computed inside the wavefunction with Measure as the measure. In the limit, the set of futures in which your misaligned betting policy outperforms the aligned one is of vanishing Measure. Almost all of you, in the only sense of "almost all" the physics defines, will look back at the policy and see that it was predictably, systematically worse.

The proof sketch generalizes past coin flips and wagers:

1. The agent chooses an action with payoffs contingent on outcomes.
2. They evaluate it using their Credences.
3. The accepted QBU model assigns Measure to the corresponding payoff sectors.
4. If Credence and Measure diverge, some available bet turns the divergence into systematic loss.
5. The overwhelming majority of descendants, weighted by Measure, regret the action relative to the Measure-aligned alternative.

Therefore, agents who accept those decision premises have a reason to align operational Credence with Measure. This is a conditional bridge to Born-rule behavior, not a derivation from unitary dynamics alone. The local [BMSL paper](/papers/BMSL.html) gives the formal version and its assumptions.

One objection is central: weighting descendants by Measure may assume part of the bridge the argument is meant to motivate. The regret claim explicitly uses Measure-weighted typicality. Simple branch counting is not well defined for emergent branches, but rejecting it does not by itself prove that rational Credence must equal Measure. The argument succeeds only for readers who independently accept Measure-weighted evaluation and the relevant decision axioms.

## What the Lemma Buys

**The circularity question is exposed rather than hidden.** The proposal separates Measure from Credence and states the typicality and decision assumptions used to connect them. Readers can then judge whether those assumptions are independently motivated.

**Decision-theoretic clarity.** The alignment of Credence with Measure is enforced by something an agent independently cares about — not being predictably outperformed across almost all of their own futures — rather than by preference axioms tailored to yield the answer. The Deutsch–Wallace program had the right instinct; the regret argument supplies the missing motivation.

**Philosophical precision.** The squared amplitude is already in the theory; the argument aims to explain why agents satisfying the stated premises would treat it as a guide. It thereby proposes a bridge between Hilbert-space structure and the epistemology of self-locating agents.

On this proposal, probability in the Everettian picture is a stance of finite agents navigating a branching structure. The QBU model supplies Measure, agents supply Credence, and additional rationality assumptions connect them. The result is a candidate account of Born-rule practice in a world without collapse, not an assumption-free theorem.
