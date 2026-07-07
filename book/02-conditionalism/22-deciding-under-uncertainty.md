---
title: 'Deciding Under Uncertainty'
subtitle: 'Tail risks and the unit of rational choice'
status: draft
sources:
  - 163356868.effective-decision-theory
  - 190790460.the-unit-of-rational-choice
---

A stranger stops me on the street and announces that he is a wizard from outside the simulation. If I hand over my wallet, he will conjure $10^{100}$ years of bliss for $10^{100}$ sentient beings; if I refuse, he will inflict the corresponding torment. My Credence that he is telling the truth is minuscule — but it is not zero, and no honest epistemology can make it zero. So the expected-utility calculation runs: a vanishing probability times an astronomical payoff yields an enormous product, and the arithmetic instructs me to hand over the wallet — and, by the same logic, to hand over the next one, to anyone willing to name a bigger number. This is Pascal's Mugging, and any decision theory that pays the mugger has refuted itself.

The mugging is a theatrical version of a problem that is three centuries old. In the St. Petersburg game, a fair coin is flipped until it first lands heads; if that happens on the $n$th flip, the game pays $2^n$ dollars. Half a chance of \$2, a quarter chance of \$4, an eighth chance of \$8 — each term of the expected-value sum contributes a dollar, and there are infinitely many terms. The expected value is infinite, so expected utility theory says a rational agent should stake everything he owns for a single play. No sane person would stake fifty dollars.

Both paradoxes have the same anatomy. Expected utility theory is a superb instrument in the middle of the probability range, where probabilities are well-grounded and payoffs are commensurate with life as lived. It breaks at the tails, where the calculation is dominated by products of two quantities that misbehave together: probabilities too small to estimate and payoffs too large to bound. The output of the multiplication is controlled entirely by the factors we know least about. A theory that lets its most unreliable inputs dominate its verdicts is not a theory of rationality; it is a vulnerability with a formalism attached.

## What Physics Does With Misbehaving Tails

Physics faced the same structural problem and solved it with unusual honesty. Quantum field theories generate absurdities — divergent integrals, infinite corrections — when extrapolated to arbitrarily high energies. The working response is the effective field theory: declare an energy cutoff, model the physics below it faithfully, and systematically ignore whatever happens beyond it. The cutoff is not a claim that high-energy phenomena do not exist. It is the recognition that they have negligible effect at the scales where the theory is used, and that pretending to model them would import spurious precision. An effective field theory does not apologize for its cutoff; the cutoff is what makes it honest. It is a theory that states its own conditions of validity — which, as [all truth is conditional](02-all-truth-is-conditional.md) argues, is the only kind of theory there is; the others merely hide the conditions.

Decision theory should do the same thing, and I call the result **Effective Decision Theory**. The name is modeled on effective field theory; it has nothing to do with *evidential* decision theory, the position usually abbreviated EDT in the decision-theory literature, and to keep the two from blurring I will never abbreviate it. Effective Decision Theory adopts a probability cutoff: below a chosen threshold, probabilities are treated as effectively zero, and the outcomes they attach to are excluded from the expected-utility calculation. The mugger's scenario does not get a tiny weight in the sum. It gets no place in the sum at all.

## Why a Cutoff Is Justified

Ignoring small probabilities sounds like an ad-hoc mutilation of the mathematics, so it matters *why* the cutoff is principled rather than squeamish.

The probabilities at the far tails are not like the probabilities in the middle. When I say a fair coin has a 50% chance of landing heads, I am reporting a Measure — an objective branch weight, in the sense given in [Measure and Credence](11-measure-and-credence.md) — that my model of the situation delivers with high reliability. When I assign the wizard's story a probability of $10^{-50}$, nothing of the kind is happening. That number is not a measured feature of the world; it is an artifact squeezed out of models I trust far less than I would need to in order to take its fiftieth decimal place seriously. Extremely low probabilities come bundled with extreme epistemic uncertainty: modeling ambiguity, unreliable data, hypotheses (like the wizard's) constructed precisely to evade every check the model could run. At the tails, the number feeding the calculation is pure Credence resting on assumptions that have themselves never been tested at anything like that resolution — the neighborhood of what [the varieties of uncertainty](13-varieties-of-uncertainty.md) calls Knightian territory, where no trustworthy model exists to deliver a probability at all. Treating such a number as a precision input to a multiplication by $10^{100}$ is not rigor. It is laundering ignorance into a demand on my wallet.

The cutoff, then, does not deny that tail events are possible. It acknowledges that below a certain probability my estimates are noise, and refuses to let noise steer decisions. This is also where the ledger opened in [Measure and Credence](11-measure-and-credence.md) gets balanced: I claimed there that refusing to be extorted by Pascal's mugger is a rational divergence between the Credence you act on and the best-estimate Measure, and that the justification is decision-theoretic rather than epistemic. Effective Decision Theory is that justification made explicit. The agent is not lying to himself about the probability; he is adopting a policy that excludes unresolvable tail scenarios from the domain in which he optimizes — exactly as the physicist excludes energies beyond the cutoff without asserting that nothing happens there.

Three principles govern the framework:

1. **The cutoff is explicit.** Choose it, state it, document it. A threshold that can be inspected can be criticized; a threshold applied silently is just bias.
2. **The cutoff is contextual.** Like the energy scale of an effective field theory, it varies with what is at stake, how good the available models are, and how much is being risked. A civilization weighing asteroid deflection should set its threshold orders of magnitude lower than an individual weighing a lottery ticket, because its models of the tail are better and its exposure is larger.
3. **Coherence is bought inside the domain.** Within the admitted probability range, all the machinery of expected utility applies with full force. Theoretical completeness is deliberately sacrificed for practical effectiveness — the same trade physics made, for the same reason.

The idea is not new; it formalizes a heuristic as old as the St. Petersburg problem itself. Nicolaus Bernoulli, who posed the game, already suggested that sufficiently small probabilities should simply be neglected — Nicolausian discounting. Effective Decision Theory gives that instinct the shape of a framework rather than an embarrassment. I will not pretend the framework is finished: I have no rigorous rule for selecting the optimal threshold, and an honest agent will adjust it as models improve rather than fix it forever. But an explicit, criticizable cutoff is strictly better than the two alternatives on offer — paying the mugger, or applying a cutoff anyway while denying that you have one. Every actual human decision-maker does the latter. The only question is whether the threshold is chosen or smuggled.

## A Paradox the Cutoff Cannot Touch

The cutoff repairs expected utility where the probabilities are degenerate. But there is a second, deeper failure mode that appears at probabilities as tame as 0.99, and it demands a different repair — not to the probabilities, but to our answer to the question *what is being chosen?*

Newcomb's paradox: a highly reliable predictor has already filled an opaque box with either \$1,000,000 or \$0. If it predicted you would take only the opaque box, it put in the million. If it predicted you would take both boxes, it left the opaque box empty. Beside it sits a transparent box holding \$1,000. You may take the opaque box alone, or both.

The two-boxing argument says: the money is already in the box or it isn't. If it's there, taking both boxes gets you \$1,001,000 instead of \$1,000,000. If it's not, taking both gets you \$1,000 instead of nothing. Either way, two-boxing pays exactly \$1,000 more. Two-boxing dominates.

The argument has a reputation for pitting rationality against itself — causal decision theorists on one side, evidentialists on the other, each claiming the mantle of reason. That framing misses the real issue. Newcomb's paradox is not fundamentally about causation versus correlation. It is about the **unit of choice**. Evaluate an isolated hand motion inside an artificially frozen world, and two-boxing looks compelling. Evaluate the policy that places you into a distribution of futures, and one-boxing is obviously correct. The paradox is manufactured by sliding between those two levels without noticing.

## The Unit of Rational Choice

The dominance argument holds fixed a condition that the problem itself defines as policy-dependent. The contents of the opaque box are not caused by your present hand motion — true. But they are not independent of your decision in the only sense that matters, because they are linked to the *policy you instantiate*. The predictor did not reward a last-second twitch. It rewarded being the kind of agent it predicted would one-box. That is the entire structure of the problem, and once it is stated plainly the paradox is already dying.

The wrong question is: *given fixed box contents, which immediate act pays more?*

The right question is: *from my current vantage, which available policy places the most future Measure into favorable outcomes?*

In the Quantum Branching Universe (QBU) — the branching picture set out in [Measure and Credence](11-measure-and-credence.md) — "the futures" in that question are not a figure of speech. Descending from this moment is a weighted family of branches, and a policy is evaluated by how the Measure of that family distributes over outcomes. Rational choice is not the optimization of an isolated motor output; it is the selection of a policy-pattern, judged by the Measure-distribution of the futures that policy induces.

Run the calculation at that level. Let

$$\pi_1 = \text{one-box}, \qquad \pi_2 = \text{two-box}.$$

If the predictor's reliability is $p$, the payoff distributions the two policies induce are

$$\begin{aligned}
\mu(\$1{,}000{,}000 \mid \pi_1) &= p \\
\mu(\$0 \mid \pi_1) &= 1-p \\
\mu(\$1{,}000 \mid \pi_2) &= p \\
\mu(\$1{,}001{,}000 \mid \pi_2) &= 1-p
\end{aligned}$$

so the expected utilities of the policies are

$$\begin{aligned}
EU(\pi_1) &= p \cdot 1{,}000{,}000 \\
EU(\pi_2) &= p \cdot 1{,}000 + (1-p)\cdot 1{,}001{,}000.
\end{aligned}$$

One-boxing is the better policy whenever

$$p \cdot 1{,}000{,}000 > p \cdot 1{,}000 + (1-p)\cdot 1{,}001{,}000,$$

which simplifies to

$$p > 0.5005.$$

If the predictor is even slightly better than a coin flip, one-boxing wins. At 99% reliability the result is absurdly lopsided: one-boxing expects \$990,000, two-boxing expects \$11,000. Notice that expected utility theory itself delivers this verdict without complaint — no exotic decision rule was needed. All that changed is the unit the expectation ranges over: policies and the branch-weights they induce, not hand motions inside a frozen snapshot.

## No Backward Causation Required

Nothing supernatural is happening here. Your present choice does not reach into the past and rewrite the box's contents. The dependency is structural, not retrocausal: the predictor's earlier action and your later decision covary because both track the same underlying policy-pattern. The predictor succeeds by modeling you, and what it models is not a future twitch but a standing disposition.

This is exactly where the two-boxer goes wrong. He imagines he can keep the favorable consequences of being the kind of agent the predictor rewards, then swap in the local act of a different kind of agent at the last moment. He cannot. That is not a coherent counterfactual — it severs the very dependency the setup is built to expose. He wants to inhabit the branch-family in which the predictor filled the box while acting as the sort of agent for whom the predictor would have left it empty. That is not cleverness. It is incoherence disguised as opportunism. Two-boxing is what happens when local greed masquerades as rationality.

And this is why Newcomb matters far beyond the magic box. It is a stripped-down model of ordinary strategic life in any world containing prediction, reputation, commitment, signaling, or coordination. The two-boxer's mistake reappears whenever someone tries to enjoy the benefits of being trusted, legible, or cooperative while defecting at the final moment and pretending the earlier structure can be held fixed. It cannot. A policy-sensitive world rewards coherent policy, not locally greedy gestures — and every world containing other modelers of you is policy-sensitive.

## Expected Utility, Conditionalized

Assemble the two repairs and a single pattern emerges. Expected utility theory was never wrong; it was stated unconditionally, and unconditional statements conceal the domains where they fail. Make the conditions explicit and both paradoxes dissolve. The theory holds *given* probabilities sound enough to compute with — so adopt an explicit, contextual cutoff and refuse the tails where your numbers are noise. The theory holds *given* the right unit of choice — so apply it to policies and the Measure-distribution of futures they induce, not to isolated acts inside artificially frozen worlds. Pascal's mugger exploits the first hidden condition; Newcomb's predictor exposes the second.

What remains is a picture of rational agency that matches the rest of this volume. Credence tracks Measure as faithfully as the evidence allows — that is the epistemic discipline. And when action deliberately departs from the nominal numbers, the departure is not a lapse but a priced, explicit, decision-theoretic policy: a cutoff declared, a unit of choice enlarged. Rational agency does not optimize isolated acts. It optimizes the future Measure associated with coherent policy.
