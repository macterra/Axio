---
title: 'The Varieties of Uncertainty'
subtitle: 'Timeline, logical, semantic, and metaphysical credence'
status: review
sources:
  - 164433813.defending-bayes-part-5
  - 164364452.defending-bayes-part-4
  - 165064896.defending-bayes-part-6
---

Eliezer Yudkowsky has proposed that the only irreducible uncertainty is indexical: the predicament of occupying one of several locations an observer's evidence cannot distinguish. The claim is suggestive within a branching interpretation, but it is not established independently of that framework and should not be over-read. This chapter offers four useful kinds of uncertainty and asks which probabilistic tools fit each. The map is diagnostic, not exhaustive.

## Standing in More Than One Place

Start with what Yudkowsky gets right. Indexical uncertainty arises whenever an observer's evidence is consistent with more than one location, identity, or vantage point — whenever there are several places you could be standing and nothing in your experience settles which. The classic cases are self-location puzzles: Sleeping Beauty waking without knowing whether it is Monday or Tuesday; the simulation hypothesis, on which your experiences are consistent with being flesh or being software; the observer outside Schrödinger's box, about to open it.

Conditional on the Quantum Branching Universe (QBU), indexical uncertainty is one way to model quantum uncertainty. A measurement produces multiple robust future records, and before observing one an agent's present evidence may not distinguish among its successors. The two framings can then describe the same modeled predicament:

- **Indexical framing:** *Who am I, given multiple observers my evidence cannot distinguish?*
- **Timeline framing:** *Which branch am I on, given multiple branches consistent with my evidence?*

This reframes rather than dissolves the probability problem: universal evolution is deterministic, while an embedded observer must still connect physical weight to expectations about future records. Some ordinary empirical uncertainty can be represented this way if QBU is assumed, but weather, genetics, and dice also involve ignorance about models and initial conditions. They are not automatically nothing but self-location.

How the numbers should actually be assigned in self-location puzzles — why you are not a random sample from the observers, and not a random branch from the tree — is a hard enough question to need two chapters of its own, [You're Not a Random Sample](15-youre-not-a-random-sample.md) and [You're Not a Random Branch](16-youre-not-a-random-branch.md). Here I need only the taxonomy point: timeline uncertainty is the central case of Credence, the one that empirical evidence bears on and Measure objectively underwrites.

Central — but not exhaustive. Consider three questions a rational agent can be genuinely, quantifiably unsure about, none of which is a question about which branch it occupies.

## Logical Uncertainty

What is your credence that the trillionth digit of π is a 7? Something near one tenth, presumably — and that number is doing real work: you would take one side of a bet at twenty-to-one and the other side at five-to-one, and you would be right to.

But this uncertainty has nothing to do with timelines. The trillionth digit of π is the same in every branch of the multiverse; no observation, no measurement, no self-location will vary it. Mathematics is the one domain where standing in more than one place changes nothing. Your uncertainty here is a fact about *you*, not about the world: you lack the computation. A being with enough compute would have no credence to assign — it would just know. Logical uncertainty is the epistemic shadow of bounded resources, and it covers everything from unresolved digits to open conjectures: your credence that Goldbach's conjecture is true is a probability about a fact that was never in suspense.

## Semantic Uncertainty

What is your credence that baldness begins at fewer than 500 hairs?

Here the uncertainty lives in the word, not the world. Nothing about scalps is hidden from you; what is unsettled is what "baldness" means, precisely — where a vague predicate's boundary falls, how a definitional dispute will resolve, which way an ambiguous term will be sharpened. This is uncertainty about the *conditions* of a statement rather than about its subject matter. Conditionalism locates it exactly: a truth claim is shorthand for a conditional, and when the conditions are left underspecified — the territory of [when statements fail](04-when-statements-fail.md) — an agent can still hold a credence about how they will be filled in. Semantic credence is what it is rational to carry while the conditions are in flux: your credence about how a court will construe "vehicle," how a community will end up using "planet," whether a borderline case will fall inside a category once the category is forced to commit.

## Metaphysical Uncertainty

What is your credence that consciousness requires a biological substrate? That there are moral facts? That the branching picture of quantum mechanics is itself the right one, rather than some rival interpretation?

These are not questions about which timeline you occupy — the answers, whatever they are, hold across all of them. Nor are they mere computation deficits or definitional fuzz. They are uncertainty about the fundamental furniture of reality, about which explanatory framework is true. And credence applies here too. My own confidence in the QBU is high but it is a *credence* — I hold the theory the way a rational agent holds any deep theory, with a probability short of one. This is the position I defend [in defense of Bayes](12-in-defense-of-bayes.md): explanatory theories contain no probabilities, but credences *about* theories are perfectly coherent, and metaphysical uncertainty is exactly such credence at maximum depth.

The proposed map has four regions:

1. **Timeline (indexical) uncertainty** — which location or record am I associated with? Under QBU, Measure can weight the alternatives.
2. **Logical uncertainty** — what do my premises entail? Bounded computation facing unbounded mathematics.
3. **Semantic uncertainty** — what do the words mean? Unsettled conditions on vague or ambiguous statements.
4. **Metaphysical uncertainty** — what is reality fundamentally like? Credence about frameworks themselves.

Within QBU, timeline uncertainty may persist even for an idealized agent with unlimited computation and a complete state description. Whether that makes it the only irreducible variety depends on controversial assumptions about identity, branching, language, and what the ideal agent knows. The other categories plainly matter to finite agents whether or not they are reducible in principle.

## Betting on Mathematics

The taxonomy raises a sharp objection, and answering it is the payoff of this chapter.

Timeline credence has something objective to answer to: Measure. When I say the coin has a 50 percent chance of heads, there is a physical branch weight my credence is tracking, and that is what makes the probability calculus more than etiquette. But the other three varieties have *no objective probability underneath*. There is no Measure over the digits of π; the trillionth digit does not occur in 10 percent of branches, it is what it is in all of them. So why should logical credences obey the probability axioms at all? What disciplines the numbers, when there is no fact of chance for them to be right about? A critic can put it harshly: your "credence" about π is just a feeling with a decimal point.

The answer comes from [Logical Induction](https://intelligence.org/files/LogicalInduction.pdf), a formal framework due to Garrabrant, Benson-Tilsen, Critch, Soares, and Taylor. Its mechanism is a market. Picture the unresolved statements of mathematics as tradeable contracts — a share of "the trillionth digit of π is 7" pays out a dollar if true, nothing if false — and picture a population of traders, each an algorithm implementing some computable betting strategy: one exploits digit statistics, another hunts partial proofs, another arbitrages related theorems against each other. The market price of each contract is the system's credence in that statement. As logical evidence accumulates — a proof lands, a computation terminates, a heuristic pans out — traders profit or bleed, prices move, and the credences update.

A central guarantee is that no efficiently computable trader can exploit a logical inductor to obtain unbounded profit while keeping downside bounded. This resembles market-based resistance to exploitation, but it is not simply the ordinary Dutch-book theorem. Logical induction shows that resource-bounded prices can acquire coherence and convergence properties over time even where no objective chance is posited. Its assumptions and guarantees are specific to the constructed market and deductive process.

A proof, computation, or partial result can change a logical inductor's prices. This supports disciplined graded belief about mathematics, but the update mechanism is not ordinary Bayesian conditionalization unchanged. The broader lesson is narrower: coherent Credence need not mirror an objective chance in every domain.

## A Meta-Credence Check

Is the four-fold classification exhaustive? Probably not in any strict sense: categories overlap, and uncertainty about models, parameters, data quality, and other agents can be carved differently. Its value is diagnostic rather than numerical.

And the residual 5 percent is the chapter in miniature. It is not timeline uncertainty — no branch of the multiverse contains a fifth category that other branches lack. It is logical uncertainty about what my own distinctions entail, semantic uncertainty about where the category boundaries fall, and metaphysical uncertainty about whether reality has joints my taxonomy misses. The map classifies even the doubt about the map. That is what a framework in good working order looks like: not certainty, but uncertainty that knows its own varieties.
