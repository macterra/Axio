---
title: "You're Not a Random Sample"
subtitle: 'Anthropics without observer-counting'
status: review
sources:
  - 193379647.youre-not-a-random-sample
---

Imagine you are Adam — literally the first human. You are about to flip a perfectly fair coin. Heads: humanity flourishes and billions of people eventually exist. Tails: it is just you and Eve, forever.

Before you flip, how confident should you be that the coin will land heads?

If you said 50/50, you have identified the intuition the Lazy Adam case is designed to defend. Under one application of the Self-Sampling Assumption (SSA), Adam's indexical evidence can instead favor *tails*. SSA is influential, but neither it nor the relevant reference class is uniquely dominant.

The reasoning goes like this: if you should think of yourself as a random sample from all humans who will ever live, then being literally the first human is wildly unlikely in a world with billions of people but perfectly normal in a world with only two. So the coin is probably going to land tails.

That verdict is counterintuitive because the physical coin mechanism is unchanged. Defenders of anthropic updating will answer that the evidence is not only about the mechanism but about Adam's location. The example therefore exposes a disagreement about what belongs in the likelihood rather than ending it by ridicule.

## The Two Orthodox Answers

Philosophy has two main frameworks for reasoning about your own location in the universe.

**The Self-Sampling Assumption (SSA)** says: reason as if you were randomly picked from some group of observers. This is the view that makes Adam confident in tails. It also generates the infamous **Doomsday Argument** — the claim that your birth rank (roughly, how many humans have lived before you) is evidence that humanity will end relatively soon, because being born early is more "typical" in a short-lived civilization.

The problem with SSA is not just that it gives weird answers. It is that the whole setup is arbitrary. Randomly sampled from *which* group? All humans? All mammals? All conscious beings? All observers born on Tuesdays? SSA never gives a principled answer, and the conclusions change depending on which group you pick.

**The Self-Indication Assumption (SIA)** tries to fix this by saying: worlds with more observers are more likely, because there are more "slots" you could be occupying. This neatly cancels out the Doomsday Argument and fixes the Adam case. But it creates its own monster.

In the **Presumptuous Philosopher** scenario, two cosmological theories are equally well-supported by evidence. Theory A says the universe contains a trillion observers. Theory B says it contains a trillion trillion. SIA says you should be virtually certain that Theory B is correct — not because of any physical evidence, but simply because there are more observers in it. The sheer headcount of a theory becomes a trump card over actual scientific evidence.

Both frameworks share the same deep flaw: they treat **counting observers** as the fundamental operation. SSA samples from a count. SIA rewards a bigger count. The disagreement is about *how* to count, but neither questions whether counting is the right thing to do at all.

## Stop Counting Heads

I propose a framework called Measure-Conditioned Self-Location (MCSL) — the formal treatment is in [the MCSL paper](/papers/MCSL.html) — and its central move is deceptively simple: replace observer-counting with [Measure](11-measure-and-credence.md).

What is Measure? In the optional QBU model, it is the Born weight assigned to a specified record sector—not a quantity of reality or a claim that one branch is less real than another. Classical stochastic models can also supply objective probabilities, but there is no theory-neutral measure over arbitrary observers or cosmologies.

The crucial difference: if you duplicate someone, SSA and SIA just see "two observers now" and start counting. MCSL asks: what is the physical weight behind each copy? Two copies created by a symmetric process share Measure equally — you get the intuitive 50/50 answer. But two "copies" with very different physical grounding can have very different weights. Counting cannot see that distinction. Measure can.

## The Right Question

MCSL says the question is not "From which observer was I randomly sampled?" or "Which world has the most observers?" Instead, the right question is:

**Across the theories I am considering, how much objective physical weight stands behind situations that match my current evidence?**

Three words in that sentence are doing heavy lifting: *objective*, *physical*, and *evidence*.

**Objective and physical** means the weights must come from a stated physical model rather than an arbitrary sampling rule. Comparing theories still requires priors, likelihoods, and a common account of evidence; MCSL does not obtain those for free.

**Evidence** means we are not just looking for situations that *feel* the same from the inside. We need situations that genuinely support the full structure of what we currently know. This matters because of what might be the hardest problem in this whole area.

## The Counterfeit Problem

Imagine a freak fluctuation in empty space momentarily assembles a brain — complete with all your memories, all your current sensations, your sense of sitting here reading this page. One instant later, it dissolves. This is a **Boltzmann brain**, and it is not just a thought experiment — some cosmological theories predict they should be overwhelmingly common.

If you naively count all situations that match your current experience, these cosmic counterfeits swamp everything else. Any theory that predicts more empty space predicts more random brain-fluctuations, and suddenly you should believe you are a momentary hallucination floating in the void.

MCSL's answer is to distinguish between three levels of "matching":

1. **Phenomenal match**: it feels the same right now. (Too weak — counterfeits pass this test.)
2. **Evidential match**: the full structure of memories, knowledge, and context matches. (Better, but still not enough — a sufficiently detailed counterfeit passes this too.)
3. **Admissible coherent match**: it not only matches your evidence but actually *supports* the structures that make your evidence count as evidence in the first place. Your memories are not just present as a pattern — they connect to a real history. Your inferences are not just locally mimicked — they are grounded in genuine structure.

MCSL proposes that only the third level is admissible. But calling a causally ordinary observer "genuine" and a Boltzmann brain "counterfeit" risks assuming the conclusion unless the relevance of causal history is independently defended.

This is the hardest part of the framework. I do not claim to have a complete theory of exactly where to draw the line. The proposal's promise depends on whether admissibility can be specified without building the preferred conclusion into the rule.

## The Famous Puzzles

**Lazy Adam**: given symmetric physical weights and an evidential specification that does not reweight by future observer count, MCSL returns 50/50.

**The Doomsday Argument**: The existence of many future humans does not dilute the physical weight of your current situation. A bigger future does not make your present less real. So your birth rank is not evidence of impending doom — at least not through this route.

**Presumptuous Philosopher**: Extra distant observers who share none of your specific evidence do not count. A theory is not favored just because it has more people in it. Only situations that match *your actual evidence* matter.

**Sleeping Beauty**: This famous puzzle asks: if you are woken up once on heads and twice on tails (with memory erasure between wakings), what is the probability of heads when you wake up? MCSL does not magically resolve the debate, but it clarifies what the debate is actually about. The disagreement is not about sampling — it is about how to carve up your evidence. Should each waking be treated as a separate evidence-state, or are they components of one protocol? That is the real question, and MCSL forces it into the open.

## What This Doesn't Solve

I want to be forthright about the limits:

- MCSL does not yet have a complete theory of admissibility — the exact line between genuine and counterfeit realizations.
- It does not fully solve the Presumptuous Philosopher when a theory predicts many exact copies of *you specifically* (as opposed to just many generic observers).
- It does not prove from first principles that Boltzmann brains should be excluded.
- It presupposes a physical framework rather than building everything from scratch out of pure subjective experience.

But these are honest open problems, not hidden failures. Identifying the *right* open problems is more valuable than pretending to have solved the wrong ones.

## From Counting to Weighing

This might seem like an abstract philosophical exercise, but the stakes are surprisingly concrete. If you are trying to reason about the multiverse, the far future of humanity, the simulation hypothesis, or the foundations of quantum mechanics, you need a theory of self-location. And if that theory is fundamentally broken — if it tells you fair coins are biased or that headcount trumps evidence — then every conclusion built on it is suspect.

MCSL is a research proposal. It asks how much model-grounded weight supports situations matching the evidence, replacing simple observer counts with physical structure. It still owes a general account of cross-theory weights, priors, likelihoods, and admissibility.

The same shift has a twin. Self-location asks where you are among observers; the QBU poses the mirror-image question of where you are among branches — and there, too, the orthodox instinct is to count when it should weigh. Why your Credence should track Measure at all, and why the amplitude-squared weight is the only self-consistent way to do the weighing, is the subject of the companion chapter, [You're Not a Random Branch](16-youre-not-a-random-branch.md).
