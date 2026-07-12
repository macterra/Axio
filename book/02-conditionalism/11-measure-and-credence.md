---
title: 'Measure and Credence'
subtitle: 'Objective and subjective probability in a branching universe'
status: review
sources:
  - 163921757.defending-bayes
  - 163283969.objective-vs-subjective-probability
  - 165273153.defending-bayes-part-9-interlude
---

Two statements, same grammar. *The probability that tomorrow's coin flip lands heads is 50%.* *The probability that the trillionth digit of π is 7 is 10%.* Both can express an agent's uncertainty. The first may also be supported by an objective physical or statistical model of the coin; the second concerns a fixed mathematical fact the speaker has not computed. The contrast introduces two roles probability can play, though philosophical accounts of objective probability remain contested.

This optional module uses **Measure** for objective weight in the QBU model and **Credence** for an agent's graded uncertainty. The distinction is a modeling discipline, not a claim that every use of probability falls neatly into one box or that adopting it proves QBU.

To say what Measure is objective *about*, I first need to say what kind of universe we live in.

## A Universe That Branches

Between measurements, standard quantum mechanics describes a wavefunction evolving under the Schrödinger equation. Textbook collapse formulations add a measurement rule that selects an outcome. Everettian interpretations instead treat universal unitary evolution as complete. The empirical predictions are shared in ordinary applications; the dispute concerns ontology, probability, and the role of measurement.

On the Everettian reading adopted conditionally here, there is no fundamental collapse. Measurement entangles observer, apparatus, and system; decoherence produces robust records whose later interference is negligible. Calling those emergent record structures *branches* is useful, but they are not uniquely countable fundamental objects.

I call this picture the **Quantum Branching Universe (QBU)**. Reality is the totality of branching timelines: every quantum event is a fork, every fork spawns timelines for each of its outcomes, and all the timelines are equally real — ours enjoys no privileged status beyond being the one we find ourselves in. The structure as a whole does not unfold in time; it is better pictured as a vast static object, a generalization of the block universe in which the block forks. The physics behind this — why decoherence makes branches effectively independent, how events and timelines can be formally identified and counted — belongs to another volume; the formal construction is in [The Quantum Branching Universe](../01-physics-of-agency/08-the-quantum-branching-universe.md). For everything in *this* volume, four commitments suffice:

1. **Branching, not collapse.** Quantum events split timelines; no outcome is annihilated.
2. **All branches are real.** "What will happen?" has many true answers, one per branch.
3. **Record sectors are weighted.** The proposed Measure of a record sector is given by the Born weight, represented by the squared norm or, more generally, a projector expectation.
4. **That weight is Measure.**

The third commitment is the one that matters here. Counting emergent branches is not well defined; the QBU model instead assigns a normalized weight to specified record sectors. That weight is objective relative to the quantum state and chosen event decomposition. Whether it deserves the further interpretation *probability* is the problem taken up in Chapters 14 and 16.

## Probability in the World

**Measure** is the modeled physical weight of the record sectors in which a specified outcome obtains. Given a state $|\psi\rangle$ and projector $P_E$ for an event $E$, the usual expression is $\langle\psi|P_E|\psi\rangle$. It is indifferent to what an observer believes, but its application presupposes a state, an event specification, and the QBU interpretation.

Because macroscopic records emerge from quantum dynamics, the model is not confined to laboratory experiments. A flipped coin can amplify microscopic differences; under an adequately specified symmetric model, the heads record sector may have Measure close to one half. This is not a count or an "actual proportion of tomorrows." It is one half of the normalized Born weight for the stated event.

## Probability in the Head

**Credence** is subjective probability: an agent's rational degree of confidence in a proposition, given the information the agent actually has. In branching terms, the central case is uncertainty about location: which branch am I in, and which branches am I about to be in? A Credence is a fact about an agent's epistemic state, and so it legitimately varies from agent to agent. Your Credence that the coin lands heads might be 0.5; mine, having watched the same coin come up heads eleven times running, might reasonably sit elsewhere. The world has not changed between us — our information has. Credence is the raw material of belief: as I argued in [What Beliefs Are](08-what-beliefs-are.md), to believe a proposition just is to assign it Credence high enough to act on.

And Credence outruns Measure in scope. Measure applies where the world genuinely branches. Credence applies to *anything* an agent can be uncertain about — including matters where the world does not branch at all. The trillionth digit of π is the same in every timeline; there is no branch where arithmetic came out differently. Measure has nothing to spread: it assigns weight 1 to whatever the digit actually is. Yet my Credence is rightly spread evenly across the ten digits, because I have not done the computation. The same goes for uncertainty about scientific theories, about logical conjectures, about which model of a situation is correct: no branching, pure Credence. A probability assignment with no possible grounding in branch weights is the clearest signature that we are talking about the head, not the world.

## One Mathematics, Two Interpretations

Here is the trap. Measure and Credence can both be represented by normalized measures and conditional probabilities. Nothing in bare symbols tells you which interpretation is intended. But they are not thereby governed by identical assignment rules: physical dynamics supplies Measure, while priors, evidence models, and norms of inference govern Credence. Conflating them can turn ignorance into a physical claim or treat a modeled physical weight as though it were a negotiable opinion.

The conflation does its worst damage in the philosophy of science. When I assign a Credence of 0.9 to a scientific theory, I am not asserting that the theory is 90% true, or true in 90% of branches, or possessed of some intrinsic probabilistic essence. Theories are not the kind of thing that has a Measure. The 0.9 quantifies *my* rational uncertainty about whether the theory correctly describes reality — a fact about me, not about the theory. Critics of Bayesian epistemology, David Deutsch and Brett Hall foremost among them, have effectively skewered the confused version of this claim, and their deeper challenge — that explanatory knowledge leaves no legitimate role for credence at all — deserves a full answer, which I give it [in defense of Bayes](12-in-defense-of-bayes.md). For now the point is narrower: the position they rightly attack, probability as a property of theories themselves, is exactly what the Measure/Credence distinction forbids.

Note also what the distinction does *not* say: neither kind of probability is unconditional. A Measure is always the weight of branches descending from a specified event, given a specified branching structure; a Credence is always confidence given evidence and background assumptions. Both are conditional through and through, as [all truth is conditional](02-all-truth-is-conditional.md) — the distinction between them is not conditional versus absolute, but world versus head.

## Bayes Across the Branches

Bayes' theorem updates Credence once priors and likelihoods have been specified. A physical theory can supply likelihoods; in the QBU module, those likelihoods may be calculated from Measure. The connection is conditional on the empirical model and on the epistemic decision to use it.

Take the coin flip, with an observation layered on top. The hypothesis $H$: the coin landed heads. The evidence $E$: I glimpse the coin in bad light and it looks like heads. Both of these pick out sets of branches, and the physics fixes their weights:

- $\text{Measure}(E \mid H)$ — among branches where the coin actually landed heads, the weight of those in which I see heads. Say my glimpse is 90% reliable: 0.9.
- $\text{Measure}(E)$ — the overall weight of branches in which I see heads, however the coin landed. For a fair coin: $0.9 \times 0.5 + 0.1 \times 0.5 = 0.5$.

Suppose my prior $\text{Credence}(H)$ is 0.5 and I accept the physical model as the source of the observation likelihoods. Then:

$$\text{Credence}(H \mid E) = \frac{\text{Credence}(E \mid H)\,\text{Credence}(H)}{\text{Credence}(E)} = \frac{0.9 \times 0.5}{0.5} = 0.9.$$

The prior, likelihood, evidence probability, and posterior in this equation are all Credences. In this special case, the accepted physical model supplies likelihood values numerically equal to ratios of Measure. Keeping the types straight avoids treating a physical weight as though it were already an agent's belief. Bayesian conditionalization is a powerful coherence constraint under its assumptions; other procedures may be needed when evidence is uncertain, the model class changes, or precise priors are unavailable. QBU also raises self-location and selection questions, discussed in [You're Not a Random Branch](16-youre-not-a-random-branch.md), as well as the prior question of why weight should guide probability at all, discussed in [Probability Without Collapse](14-probability-without-collapse.md).

## When Diverging Is Rational

When the relevant physical model is known, its Measure can constrain well-calibrated Credence. In practice, several complications intervene:

- **Computational limits.** An agent may use an approximation rather than calculate the exact physical weight. That makes the Credence imprecise, not deliberately false.
- **Extreme-payoff cases.** Pascal-style problems expose uncertainty about models, utilities, and tail behavior. Robust decision rules or bounded utilities can address them without pretending the estimated probability is different for motivational reasons.
- **Psychological constraints.** Optimism and caution can affect performance. It is clearer to represent those effects in utilities, policies, and models of future behavior than to relabel a useful distortion as accurate belief.
- **Knightian uncertainty.** When no model warrants a precise likelihood, Credence may be interval-valued or qualitative rather than a fabricated point estimate.

These cases motivate a gate between epistemic assessment and action. First represent what is known and how uncertain it is; then combine that representation with utilities, resource limits, and robustness requirements. [Deciding Under Uncertainty](23-deciding-under-uncertainty.md) takes up that second task.

## The Division of Labor

The conditional picture, assembled: Measure describes physical weight in the QBU model; Credence represents an agent's uncertainty. A physical model can inform likelihoods used in Bayesian updating, but it does not erase the assumptions connecting weight, evidence, belief, and choice. Before manipulating a probability, ask what kind of quantity it represents, how it was assigned, and which model makes the assignment meaningful. The rest of this module keeps those questions visible.
