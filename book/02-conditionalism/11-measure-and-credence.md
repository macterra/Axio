---
title: 'Measure and Credence'
subtitle: 'Objective and subjective probability in a branching universe'
status: draft
sources:
  - 163921757.defending-bayes
  - 163283969.objective-vs-subjective-probability
  - 165273153.defending-bayes-part-9-interlude
---

Two statements, same grammar. *The probability that tomorrow's coin flip lands heads is 50%.* *The probability that the trillionth digit of π is 7 is 10%.* Both are honest, well-formed probability assignments; a bookmaker would take either bet. Yet they are claims about entirely different things. The first is, at bottom, a claim about the world — about what the physics of the flip will actually do. The second cannot be a claim about the world at all: the trillionth digit of π is whatever it is, fixed by mathematics, the same in every corner of reality. The 10% measures nothing but my ignorance.

Ordinary language uses one word, *probability*, for both, and that single ambiguity is the root error in most confusions about probability — in quantum mechanics, in epistemology, in decision theory. This chapter separates the two things and gives them the names the rest of this volume will use: **Measure**, the objective probability written into the physical structure of reality, and **Credence**, the subjective probability that quantifies an agent's uncertainty. They obey the same mathematics, which is precisely what makes them so easy to conflate and so important to distinguish.

To say what Measure is objective *about*, I first need to say what kind of universe we live in.

## A Universe That Branches

Quantum mechanics, taken at face value, describes physical systems by a wavefunction that evolves smoothly and deterministically under the Schrödinger equation. Left alone, a system can occupy a superposition — an electron with amplitude for spin-up *and* amplitude for spin-down. The textbook tradition then adds a second, alien rule: upon measurement, the wavefunction "collapses," one outcome is mysteriously promoted to reality, and the others are annihilated. Nothing in the physics motivates this rule; it is bolted on to preserve the intuition that only one thing happens.

Everett's insight was to delete the bolt-on and take the equations literally. There is no collapse. When an observer measures the electron, the deterministic evolution simply continues: the observer becomes entangled with the superposition, and the result is an observer-who-saw-up *and* an observer-who-saw-down, each embedded in their own decohered history, unable to interact with the other. Every outcome with nonzero amplitude occurs — each in its own branch.

I call this picture the **Quantum Branching Universe (QBU)**. Reality is the totality of branching timelines: every quantum event is a fork, every fork spawns timelines for each of its outcomes, and all the timelines are equally real — ours enjoys no privileged status beyond being the one we find ourselves in. The structure as a whole does not unfold in time; it is better pictured as a vast static object, a generalization of the block universe in which the block forks. The physics behind this — why decoherence makes branches effectively independent, how events and timelines can be formally identified and counted — belongs to another volume; the formal construction is in [The Quantum Branching Universe](/posts/162844036.the-quantum-branching-universe-qbu.html). For everything in *this* volume, four commitments suffice:

1. **Branching, not collapse.** Quantum events split timelines; no outcome is annihilated.
2. **All branches are real.** "What will happen?" has many true answers, one per branch.
3. **Branches are weighted.** Each branch carries an objective weight given by the squared amplitude of the wavefunction — the same quantity the textbook tradition calls the Born probability.
4. **That weight is Measure.**

The third commitment is the one that matters here. Branches are not democratic. An unequal superposition does not split reality into two equal halves that happen to be labeled 70/30; it produces branches of genuinely unequal weight, and the weights are as much a physical fact as mass or charge.

## Probability in the World

**Measure** is objective probability: the weight of the branches, descending from an event, in which a given outcome obtains. It is fixed by the wavefunction — by the squared amplitudes — and it is utterly indifferent to what anyone believes, knows, or expects. An electron prepared in a superposition with amplitudes yielding weights 0.7 and 0.3 branches accordingly whether the experimenter is a Nobel laureate, a fraud, or absent. Measure is a fact about the branching structure of reality, on the same footing as any other physical fact.

Because branching is ubiquitous — every thermal fluctuation, every photon absorbed or not — Measure is not confined to laboratory experiments. A flipped coin is a macroscopic amplifier of microscopic quantum uncertainty: among the branches descending from the flip, the ones where it lands heads have a total Measure, and for a symmetric coin that Measure is very close to one half. When I say the objective probability of heads is 50%, that is not a statement about ignorance or about long-run frequencies in imaginary repetitions. It is a statement about the actual proportion — by weight — of tomorrows.

## Probability in the Head

**Credence** is subjective probability: an agent's rational degree of confidence in a proposition, given the information the agent actually has. In branching terms, the central case is uncertainty about location: which branch am I in, and which branches am I about to be in? A Credence is a fact about an agent's epistemic state, and so it legitimately varies from agent to agent. Your Credence that the coin lands heads might be 0.5; mine, having watched the same coin come up heads eleven times running, might reasonably sit elsewhere. The world has not changed between us — our information has. Credence is the raw material of belief: as I argued in [What Beliefs Are](08-what-beliefs-are.md), to believe a proposition just is to assign it Credence high enough to act on.

And Credence outruns Measure in scope. Measure applies where the world genuinely branches. Credence applies to *anything* an agent can be uncertain about — including matters where the world does not branch at all. The trillionth digit of π is the same in every timeline; there is no branch where arithmetic came out differently. Measure has nothing to spread: it assigns weight 1 to whatever the digit actually is. Yet my Credence is rightly spread evenly across the ten digits, because I have not done the computation. The same goes for uncertainty about scientific theories, about logical conjectures, about which model of a situation is correct: no branching, pure Credence. A probability assignment with no possible grounding in branch weights is the clearest signature that we are talking about the head, not the world.

## One Mathematics, Two Interpretations

Here is the trap. Measure and Credence obey *identical* mathematics — the probability axioms, the calculus of conditional probability, Bayesian updating. Every formal manipulation licensed for one is licensed for the other. Nothing in the symbols tells you which one you are holding, so the distinction must be carried by discipline rather than by notation. When we conflate them, we commit real errors in both directions: treating epistemic uncertainty as if the world itself were undecided (there is no branch-spread over the digits of π), or treating physical branch weights as if they were negotiable opinions (the electron's 0.7 does not care about your priors).

The conflation does its worst damage in the philosophy of science. When I assign a Credence of 0.9 to a scientific theory, I am not asserting that the theory is 90% true, or true in 90% of branches, or possessed of some intrinsic probabilistic essence. Theories are not the kind of thing that has a Measure. The 0.9 quantifies *my* rational uncertainty about whether the theory correctly describes reality — a fact about me, not about the theory. Critics of Bayesian epistemology, David Deutsch and Brett Hall foremost among them, have effectively skewered the confused version of this claim, and their deeper challenge — that explanatory knowledge leaves no legitimate role for credence at all — deserves a full answer, which I give it [in defense of Bayes](12-in-defense-of-bayes.md). For now the point is narrower: the position they rightly attack, probability as a property of theories themselves, is exactly what the Measure/Credence distinction forbids.

Note also what the distinction does *not* say: neither kind of probability is unconditional. A Measure is always the weight of branches descending from a specified event, given a specified branching structure; a Credence is always confidence given evidence and background assumptions. Both are conditional through and through, as [all truth is conditional](02-all-truth-is-conditional.md) — the distinction between them is not conditional versus absolute, but world versus head.

## Bayes Across the Branches

The two kinds of probability are not merely compatible; they are made for each other, and Bayes' theorem is the machine that connects them. Bayesian updating is how an agent aligns Credence with Measure as evidence arrives.

Take the coin flip, with an observation layered on top. The hypothesis $H$: the coin landed heads. The evidence $E$: I glimpse the coin in bad light and it looks like heads. Both of these pick out sets of branches, and the physics fixes their weights:

- $\text{Measure}(E \mid H)$ — among branches where the coin actually landed heads, the weight of those in which I see heads. Say my glimpse is 90% reliable: 0.9.
- $\text{Measure}(E)$ — the overall weight of branches in which I see heads, however the coin landed. For a fair coin: $0.9 \times 0.5 + 0.1 \times 0.5 = 0.5$.

My prior $\text{Credence}(H)$ is 0.5 — and note that this alignment of prior Credence with known Measure is itself an epistemic achievement, not a triviality. Then:

$$\text{Credence}(H \mid E) \;=\; \frac{\text{Measure}(E \mid H)\,\cdot\,\text{Credence}(H)}{\text{Measure}(E)} \;=\; \frac{0.9 \times 0.5}{0.5} \;=\; 0.9$$

Look at the anatomy of that equation. The prior and the posterior are Credences — states of my head, before and after. The likelihoods are Measures — weights of branches, facts of physics. Updating is exactly the operation of routing objective branch weights into subjective confidence: after the glimpse, my Credence in heads matches the Measure of heads-branches *among the branches consistent with what I have seen*. That is what it means for a belief to track reality in a branching universe, and it is why I hold that Bayesian conditionalization is not one updating rule among many but the only coherent way to keep Credence answerable to Measure. One caution the branching picture makes vivid: the alignment must be done carefully, because observers are themselves branch-bound, and evidence of the form "I exist and am seeing this" invites selection effects that can silently corrupt the likelihoods — traps I disarm in [You're Not a Random Branch](16-youre-not-a-random-branch.md). And beneath the whole construction sits a question I have so far waved past: what entitles branch weights to be called *probabilities* at all, if every outcome happens? That foundational challenge gets its own chapter, [Probability Without Collapse](14-probability-without-collapse.md).

## When Diverging Is Rational

If updating is alignment, it is tempting to conclude that Credence should equal Measure whenever the Measure is known, full stop. As an epistemic ideal that is right. But agents are not disembodied ideals; they are finite creatures spending scarce resources inside the branching structure, and there are cases where deliberately letting Credence diverge from Measure — or proceeding without a Measure at all — is the rational course:

- **Computational limits.** When computing the true Measure would cost more than the answer is worth, a cheap heuristic Credence is the rational substitute. Rational ignorance is still rational: the trillionth digit of π is knowable, but a flat Credence over the digits is a better use of my life than the computation.
- **Pascal's mugging.** Astronomically improbable, astronomically high-stakes scenarios can hijack expected-value reasoning: a tiny Measure multiplied by a fabricated enormous payoff yields an absurd demand on resources. Discounting such scenarios below their nominal weight — refusing to let Credence be extorted — is a defensible protective policy.
- **Psychological utility.** Optimism that sustains motivation, and caution that overweights danger, are Credences bent away from the best-estimate Measure on purpose. Sometimes the bent belief is the one that serves the agent — a trade-off to handle with open eyes, since it spends calibration to buy performance.
- **Knightian uncertainty.** Sometimes the Measure is not merely unknown but unknowable in practice — no model of the branching structure is trustworthy enough to yield one. Here Credence has nothing to align with and must run on judgment alone; this is uncertainty of a different species, dissected in [the varieties of uncertainty](13-varieties-of-uncertainty.md).

What these cases share is that the divergence is justified *decision-theoretically*, not epistemically: the agent is optimizing outcomes across the branches, not accuracy of the estimate. That boundary — where the theory of belief hands off to the theory of action — is where [deciding under uncertainty](23-deciding-under-uncertainty.md) picks up.

## The Division of Labor

The picture, assembled: Measure determines the branching structure of reality — which timelines exist and with what weight. Credence guides agents navigating that structure — which branch to bet on being in. One mathematics, two subject matters; Bayes' theorem as the coupling between them; deliberate decoupling as an occasional, priced, decision-theoretic choice. Nearly every probability confusion I know of — collapsing quantum "randomness" into ignorance, inflating ignorance into physical indeterminacy, assigning theories intrinsic probabilities, mistaking a selection effect for evidence — is at bottom a failure to ask one small question before manipulating the symbols: *is this probability in the world, or in the head?* Ask it every time. The rest of this volume does.
