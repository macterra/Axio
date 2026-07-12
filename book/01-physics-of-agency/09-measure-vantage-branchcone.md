---
title: 'Measure, Vantage, Branchcone'
subtitle: 'The toolkit of objective probability'
status: review
sources:
  - 163778685.measure-vantage-branchcone-and-counterfactuals
  - 164425191.heads-or-tails
  - 163285659.how-quantum-measurement-shapes-cosmic
---

Half a second before a coin flip, the flipper sets the coin heads-up on her thumb. Nobody's beliefs change — the spectators still call it fifty-fifty, and they are right to. But something about the world has already changed. Empirically, a flipped coin lands the same side up it started slightly more often than not — about 51% of the time — so the objective probability of heads just moved from 0.500 to roughly 0.51 while every rational observer's confidence stayed put at 0.5.

Moved *relative to what?* That is the question this chapter answers. "The probability of heads" is not a free-floating number attached to the coin. It is a quantity anchored at a point — this coin, this thumb, this instant, these initial conditions — and computed over a definite set of futures flowing out of that point. Most confusion about probability, and nearly all confusion about counterfactuals, comes from leaving the anchor and the set implicit. The [Quantum Branching Universe (QBU)](08-the-quantum-branching-universe.md) lets us make both explicit. This chapter defines the three pieces of machinery — **Measure**, **Vantage**, **Branchcone** — and then puts them to work on counterfactuals, on the coin, and on a photon that has been in flight for billions of years.

## Measure

In the QBU, a specified coarse-graining represents decoherent histories and assigns quantum weight without counting them. The **Measure** of an event $E$, conditioned on a reference record $V$, is the normalized squared-amplitude weight of the components satisfying $E$. Schematically, for a conditioned state $|\psi_V\rangle$ and an event projector $\Pi_E$,

$$
\mu_V(E) = \frac{\langle\psi_V|\Pi_E|\psi_V\rangle}{\langle\psi_V|\psi_V\rangle}.
$$

Measure is fixed by the quantum state, the event definition, and the conditioning record, not by anyone's opinion. It is objective given those inputs, though the decomposition into macroscopic histories is emergent rather than unique. When I say the Measure of heads is 51%, I am not reporting that 51 of every 100 countable worlds contain heads. I am reporting the Born weight of the event subspace selected by “heads,” conditional on $V$.

Notice that the definition will not run without the subscript. Measure is always Measure *from somewhere*.

## Vantage

That somewhere is the **Vantage**: the conditioning record used as the anchor for “here and now.” In a QBU representation it may be drawn as a node, but it need not encode the universe's exact microstate. It contains the physical and historical conditions the model treats as fixed for the question.

Two things follow. First, every Measure statement is indexed: $\mu_V(E)$ gives the weight of $E$ conditional on the record represented by $V$. Second, conditioning on a later physical record can change that value even when a distant observer has not received the record. This is conditionalization on a changed physical state, not a claim that global amplitude has been created or destroyed.

## Branchcone

The Vantage anchors the calculation; the **Branchcone** names its modeled future domain. A Branchcone is the set of represented decoherent histories extending from a Vantage through a specified duration:

$$
\mathcal{B}(V, T) = \{\text{QBU histories extending } V \text{ through horizon } T\}.
$$

The name is an analogy to a light cone, not another object in relativity. A Branchcone makes the conditioning record and time horizon explicit. “The probability my headache is gone” is incomplete; “the Measure of headache-gone within one hour, conditional on this Vantage and model” has a declared domain.

$$
\mu_V(E;T) = \frac{\langle\psi_V|\Pi_{E,T}|\psi_V\rangle}{\langle\psi_V|\psi_V\rangle}.
$$

This is the same conditional Measure with its horizon stated explicitly. The result is objective relative to a quantum state, event projector, conditioning record, and coarse-graining; leaving those implicit is often harmless in practice and dangerous in foundational arguments.

## Counterfactuals Without Ghosts

The machinery pays for itself immediately on the most notoriously slippery constructions in language: counterfactuals. "If I had taken aspirin, my headache would be gone." What could make such a claim true? I didn't take the aspirin. The classical options are unattractive: treat the claim as meaningless, or follow David Lewis and evaluate it at the "nearest possible world" where I did — leaving *possible world* and *nearest* as primitives floating free of physics.

The QBU supplies physically represented alternatives, but it does not by itself choose a similarity metric or intervention. Evaluating a counterfactual still requires a causal model:

- Identify the actual Vantage and the variables held fixed.
- Specify an intervention that sets the antecedent while preserving the chosen background conditions.
- Compute the conditional Measure of the consequent under that intervention.

Writing $do(X)$ for the modeled intervention:

$$
X \square\!\!\rightarrow Y \quad\Longleftrightarrow\quad \mu_V(Y\mid do(X)) \approx 1.
$$

If the Measure of headache resolution under the aspirin intervention is near one, the flat counterfactual is supported; if it is 0.6, only the probabilistic version is. Everettian branches give the alternatives physical realization and Measure, but the intervention and background conditions still do semantic work. The QBU can ground part of counterfactual evaluation; it does not eliminate causal modeling. [Causality and Counterfactuals](10-causality-and-counterfactuals.md) develops the proposal and its limits.

## Worked Case: Heads or Tails

Now run the coin flip through the full toolkit, tracking two quantities side by side: Measure, defined above, and **Credence** — the subjective probability an observer assigns given the information they actually have. Measure belongs to this volume; Credence and the discipline of updating it belong to [Measure and Credence](../02-conditionalism/11-measure-and-credence.md). The coin flip is the cleanest demonstration of why they must not be conflated: over a two-second interval the two quantities, which started equal, come apart completely and then reconverge.

**Before $-0.5$ s.** A fair coin, no side chosen. The situation is symmetric, and both quantities sit at 0.5 — Measure because the branches forward of this Vantage split evenly by weight, Credence because the observer has no information that favors either side.

**At $-0.5$ s.** The flipper sets the coin heads-up. Symmetry breaks: from the new Vantage, the same-side bias puts the heads branches at weight $\approx 0.51$. Measure steps from 0.500 to 0.51. The spectators, who cannot see which side is up — or don't know the bias exists — hold their Credence at 0.5, and are rationally correct to.

**During the flip, $0$ to $0.5$ s.** The coin's state evolves, and later physical records may constrain its eventual landing more strongly than the earlier setup did. If each advancing Vantage conditions on those records, the conditional Measure of heads can move toward zero or one before a spectator sees the result. The path need not be smooth or universal; it depends on the physical model and on which records the Vantage includes. The spectator's Credence can meanwhile remain at 0.5 because none of those records has reached her.

**After $0.5$ s.** The coin lands and is observed. Conditional on the landing record, the Measure of heads is one on a heads record and zero on a tails record. The spectator's Credence updates when that record reaches her.

The example follows one heads-landing trajectory under a progressively enriched physical Vantage; it is not a universal law of coin dynamics. Its point is the possible separation between conditioning on the world's physical record and conditioning on the observer's information:

| Phase | Measure of heads | Credence in heads |
|---|---|---|
| Before side chosen (< $-0.5$ s) | 0.5 | 0.5 |
| Side set heads-up ($-0.5$ s) | steps to ~0.51 | 0.5 |
| Coin in flight ($0$ to $0.5$ s) | model-dependent as physical records accumulate | 0.5 |
| Landed and observed (> $0.5$ s) | 1.0 | updates rapidly to 1.0 |

Two different quantities, two different conditioning relations. Measure changes when the physical state or conditioning record changes. Credence changes when the agent receives evidence. They often agree at the start and after observation, which is why everyday language gets away with one word for both; the interval between physical determination and observer access is where the distinction matters.

## Worked Case: Wheeler's Cosmic Delayed Choice

The same machinery scales from half a second to half the age of the universe. John Wheeler's delayed-choice experiment, in its cosmic version: a photon emitted billions of years ago by a distant quasar passes an intervening galaxy whose gravity lenses it, splitting its path into multiple coherent routes around the lens. The photon travels all of them in superposition. Billions of years later it arrives at Earth, where an experimenter chooses — tonight — whether to measure interference between the paths (wave-like behavior) or which path it took (particle-like behavior).

The result seems paranormal: a decision made tonight appears to determine what the photon was doing billions of years ago. If measurement collapsed the wavefunction, you would be forced into retrocausality — today's choice reaching back to edit cosmic history.

The QBU dissolves the retrocausal reading with the Vantage. There is no collapse and nothing edits the past. Provided environmental decoherence has not already destroyed the relevant coherence, the state does not contain one measurement-independent classical path fact waiting to be revealed. Tonight's apparatus determines which observable becomes recorded, and the resulting decoherent records support different classical descriptions. From the Vantage of the choice, outcome Measures are fixed by the incoming state and the selected interaction.

So the delayed choice does not alter history; it determines which compatible classical record the present interaction establishes. The underlying quantum history need not contain the determinate classical property the later record expresses. What looks like the present reaching backward is a demand for a measurement-independent classical narrative that the formalism does not supply.
