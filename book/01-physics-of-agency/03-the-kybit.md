---
title: 'The Kybit'
subtitle: 'A unit of control'
status: draft
sources:
  - 162485677.the-physics-of-agency-part-3-the
  - 162543579.the-physics-of-agency-part-4-the
---

Physics runs on units. Energy is measured in joules, entropy in Boltzmann's constant, information in bits — and each of those quantities became a real subject of science only once it had a unit. Before Shannon, "information" was a loose intuition; after Shannon, it was a measurable quantity with theorems attached. Agency is still stuck on the wrong side of that transition. We say one act shows more deliberate control than another, that a thermostat exercises less agency than a chess engine, that forcing an outcome takes more effort than merely nudging it — and we say all of this without any way to put a number on it.

If agency is a physical phenomenon — an embedded agent spending energy to bias reality toward preferred futures, against the entropic slide I call drift, as argued in [Agency Against Drift](02-agency-against-drift.md) — then intentional control ought to be quantifiable, the way energy and information are. This chapter supplies the unit. I call it the **kybit**. Just as the bit measures information, the kybit measures an agent's intentional influence on future outcomes. And like the bit, it turns out to carry a thermodynamic price tag.

## Control as Distance Between Futures

Start with what control actually does. Before an agent intervenes, the world has some probability distribution over outcomes — call it $P_{\text{initial}}$, the distribution drift would deliver on its own. After the agent acts, the outcomes follow a different distribution, $P_{\text{final}}$, reshaped in the agent's favor. The control exerted is precisely the gap between those two futures: how far the agent dragged the probabilities from where they were going to where the agent wanted them.

There is a standard measure of the distance between two probability distributions: the **Kullback–Leibler (KL) divergence**. The total control exerted in shifting the outcome distribution from $P_{\text{initial}}$ to $P_{\text{final}}$ is

$$
D_{KL}(P_{\text{final}} \parallel P_{\text{initial}}) = \sum_{i} P_{\text{final}}(i)\,\log_2\frac{P_{\text{final}}(i)}{P_{\text{initial}}(i)}
$$

measured in kybits. The logarithm is base 2 for the same reason Shannon's is: it makes the unit binary, and it makes the simplest possible act of control come out to exactly one.

Two properties make this the right measure. First, it is always non-negative, and it is zero only when the initial and final distributions are identical — an agent who changes nothing has, by definition, exerted no control, and there is no way to score points by shuffling probability around pointlessly. Second, as I will argue below, it represents the total thermodynamic work required to rearrange the probability distribution — the number is not just a bookkeeping convenience but tracks a physical cost.

Note that the measure is asymmetric: it is computed over the final distribution, from the agent's achieved future looking back at the future drift would have delivered. That is as it should be. Control is not a symmetric relation between two possible worlds; it is the act of steering from one to the other, and the steering is what the kybit counts.

## One Kybit: The Forced Coin

The cleanest calibration is a fair coin forced to land heads.

Before the intervention, the outcomes are maximally uncertain: heads 0.5, tails 0.5. After it, the outcome is certain: heads 1.0, tails 0.0. Substituting into the definition:

$$
D_{KL} = (1.0) \log_2 \frac{1.0}{0.5} + (0.0) \log_2 \frac{0.0}{0.5}
$$

The first term evaluates directly:

$$
(1.0) \log_2 \frac{1.0}{0.5} = 1.0 \times \log_2(2) = 1.0
$$

The second term involves a zero-probability outcome, which the standard limit convention handles cleanly — $0 \log(0/q) \to 0$:

$$
(0.0) \log_2 \frac{0.0}{0.5} = 0 \quad \text{(by the standard limit convention)}
$$

So the total is

$$
D_{KL}(P_{\text{final}} \parallel P_{\text{initial}}) = 1.0 \text{ kybit}
$$

Forcing a previously uncertain 50/50 outcome to complete certainty costs exactly **one kybit** of control. The symmetry with information theory is exact and deliberate: one bit is what it takes to *learn* which way a fair coin landed; one kybit is what it takes to *decide* which way it lands. The outcome that was steered away from contributes nothing — the convention that eliminates zero-probability terms is what makes the measure robust rather than blowing up whenever an agent rules something out entirely.

## Fractions of a Kybit: The Biased Die

Control is rarely total. More often an agent tilts the odds without fixing the outcome, and the kybit handles partial control just as naturally.

Take a fair die, each face at $1/6 \approx 0.1667$, and suppose an agent biases it so that face 1 comes up half the time, face 2 a quarter of the time, and faces 3 through 6 are suppressed to $0.0625$ (one sixteenth) each. Applying the definition:

$$
\begin{aligned}
D_{KL} &= (0.5) \log_2 \frac{0.5}{1/6} + (0.25) \log_2 \frac{0.25}{1/6} + 4 \times (0.0625) \log_2 \frac{0.0625}{1/6} \\
&= 0.5 \times \log_2(3) + 0.25 \times \log_2(1.5) + 0.25 \times \log_2(0.375) \\
&\approx 0.7925 + 0.1463 - 0.3538 \\
&\approx 0.585 \text{ kybits}
\end{aligned}
$$

Reshaping the die's future this far from fair costs about **0.585 kybits** — more than half the control needed to force a coin, but nowhere near the control needed to force the die outright. Notice how the arithmetic distributes credit: the amplified faces contribute positive terms, the suppressed faces contribute negative ones, and the total still comes out positive, as it must. Every act of steering, however partial, registers as a definite, comparable quantity. A drug that shifts recovery odds from 40% to 60%, a campaign that moves an election by three points, a thermostat that narrows a room's temperature distribution — all of them exert some measurable number of kybits, and the numbers can be compared on a single scale.

## The Law of Control Work

So far the kybit could pass for pure mathematics — a scoring rule for interventions. It is more than that. Kybits represent real thermodynamic costs.

The precedent is Landauer's principle, one of the deepest results connecting information to physics: erasing one bit of information in an environment at temperature $T$ costs a minimum of $k_B T \ln 2$ in dissipated work, where $k_B$ is Boltzmann's constant. Erasure is a compression of a system's state space — two possible states forced into one — and physics charges for it. But steering an outcome is *also* a compression of possibility: forcing the coin collapses two live futures into one, exactly the operation Landauer priced. The same floor applies. Each kybit of control corresponds to a minimum energy expenditure required to intentionally bias outcomes:

$$
W_{\text{min}} = k_B T \ln 2 \quad \text{per kybit}
$$

This is Landauer's principle extended from erasure to steering, and it generalizes immediately. I state it as the **Law of Control Work**:

> **Exercising intentional control over future outcomes requires physical work proportional to the kybits of control exerted.**

Formally, if an agent exerts $C$ kybits of control, the minimum energy cost is

$$
W_{\text{min}} = C \times k_B T \ln 2
$$

where $C$ is the number of kybits exerted, $k_B$ is Boltzmann's constant, $T$ is the temperature of the agent's environment, and $\ln 2$ reflects the binary nature of the kybit. At room temperature the floor per kybit is on the order of $3 \times 10^{-21}$ joules — vanishingly small, which is why it is a floor and not a typical price. Real agents, running on muscles and microchips, pay many orders of magnitude above the Landauer minimum. But the floor is what matters in principle: it can never be zero.

That is the significance of the law. Just as erasing information has a known thermodynamic cost, intentionally shaping future outcomes — exercising agency — incurs a measurable thermodynamic cost. **Agency is never free.** Every deliberate act that biases the future consumes real physical resources. There is no such thing as influence from outside the ledger; a preference that costs nothing to enact has, by this accounting, controlled nothing. This is what it means to say agency is embedded in physical reality rather than hovering above it.

## Drift Is Free; Control Is Not

The law sharpens the asymmetry that the previous chapter drew between agency and drift. Drift — the spontaneous entropic evolution of a system toward disorder — happens without intentional effort and without anyone paying for it. It is the default trajectory, the $P_{\text{initial}}$ in every calculation above. Control is the paid alternative: an intentional investment of energy to move against that default and selectively amplify specific futures. The further you push the distribution from where drift was taking it — the more kybits you exert — the more work you must do. The exchange rate is fixed by physics.

You can see the law operating wherever genuine agency shows up. A drone adjusting its flight path in real time, running predictive simulations to steer around obstacles, is buying kybits with battery charge: narrowing the distribution over its future positions from "wherever wind and momentum take it" to "through the gap." A portfolio algorithm continuously rebalancing holdings against its forecasts is spending compute and transaction costs to drag the distribution of future returns away from the market's drift. An animal caching food against a predicted scarce season is burning calories now to compress the probability distribution over its winter — trading present energy for a future where starvation has been steered toward zero. In every case the signature is the same: a predictive internal model, an energy expenditure, and a measurable gap between the future that would have happened and the future the agent made happen. That gap, in kybits, is what the energy bought.

The Law of Control Work is the first of three. Control costs work; the capacity for control decays without continuous energy input; and perfect, frictionless control is impossible even in principle. Together they bound what any agent — bacterium, animal, human, machine — can ever do, and they are the subject of [The Three Laws of Agency](04-the-three-laws-of-agency.md).
