---
title: 'The Kybit'
subtitle: 'A unit of control'
status: review
sources:
  - 162485677.the-physics-of-agency-part-3-the
  - 162543579.the-physics-of-agency-part-4-the
---

Physics runs on units. Energy is measured in joules, entropy in Boltzmann's constant, information in bits — and each of those quantities became a real subject of science only once it had a unit. Before Shannon, "information" was a loose intuition; after Shannon, it was a measurable quantity with theorems attached. Agency is still stuck on the wrong side of that transition. We say one act shows more deliberate control than another, that a thermostat exercises less agency than a chess engine, that forcing an outcome takes more effort than merely nudging it — and we say all of this without any way to put a number on it.

If agency is physically implemented — an embedded system using a model to change outcomes relative to an uncontrolled baseline, as argued in [Agency Against Drift](02-agency-against-drift.md) — then at least its distributional effect ought to be quantifiable. This chapter proposes a unit. I call it the **kybit**. The kybit measures how far an intervention moves a distribution over outcomes from a specified baseline. Whether that movement is attributable to an agent, and what minimum work its physical implementation requires, are separate questions that the definition alone cannot settle.

## Control as Distance Between Futures

Start with what control actually does. Before an agent intervenes, the world has some probability distribution over outcomes — call it $P_{\text{initial}}$, the distribution drift would deliver on its own. After the agent acts, the outcomes follow a different distribution, $P_{\text{final}}$, reshaped in the agent's favor. The control exerted is precisely the gap between those two futures: how far the agent dragged the probabilities from where they were going to where the agent wanted them.

There is a standard measure of how one probability distribution diverges from another: the **Kullback–Leibler (KL) divergence**. It is not a mathematical distance — it is asymmetric and does not obey the triangle inequality — but its asymmetry fits an intervention evaluated against a baseline. Define the distributional control registered by a shift from $P_{\text{initial}}$ to $P_{\text{final}}$ as

$$
D_{KL}(P_{\text{final}} \parallel P_{\text{initial}}) = \sum_{i} P_{\text{final}}(i)\,\log_2\frac{P_{\text{final}}(i)}{P_{\text{initial}}(i)}
$$

measured in kybits. The logarithm is base 2 for the same reason Shannon's is: it makes the unit binary, and it makes the simplest possible act of control come out to exactly one.

Two properties make this a useful candidate measure. First, it is always non-negative, and it is zero only when the distributions are identical. Second, it measures the information required to distinguish the steered distribution from the baseline. That does not make every divergence an act of agency: a storm, a broken bearing, or an unnoticed confounder can also change an outcome distribution. Attribution requires a causal intervention model, a defensible baseline, and evidence that the change ran through the system's evaluative control loop. The kybit measures the size of an attributed distributional shift after those conditions have been met; it does not meet them by itself.

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

Forcing a previously uncertain 50/50 outcome to complete certainty registers exactly **one kybit** of distributional control. The symmetry with information theory is deliberate: one bit resolves which way a fair coin landed; one kybit records the divergence produced by fixing which way it lands. This is a statement about distributions, not yet a statement that every physical device capable of forcing the coin pays the same energy price.

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

Reshaping the die's future this far from fair registers about **0.585 kybits** — more than half the divergence of the forced coin, but less than forcing the die outright. Notice how the arithmetic distributes the shift: amplified faces contribute positive terms, suppressed faces negative ones, and the total remains non-negative. Partial steering therefore receives a definite number once its baseline, intervention, and outcome partition are fixed. Change any of those choices and the number may change, which is why a kybit comparison is meaningful only when the modeled domains are commensurable.

## From Information to Work

So far the kybit is an information measure applied to interventions. Connecting it to work requires a physical model of the transformation.

Landauer's principle connects logically irreversible information erasure to physics: resetting one bit in an environment at temperature $T$ dissipates at least $k_B T \ln 2$ under the principle's standard assumptions. A related result in nonequilibrium thermodynamics connects relative entropy to excess free energy when a distribution is transformed relative to an equilibrium reference. In the special case where the kybit baseline is that reference and the physical protocol realizes the modeled transformation, the information divergence supplies a lower bound of the same form:

$$
W_{\text{min}} \geq C k_B T \ln 2
$$

where $C$ is measured in kybits. This is the strongest clean bridge presently available, and its conditions matter. An arbitrary $P_{\text{initial}}$ is not automatically an equilibrium distribution; an abstract change in outcome probabilities does not specify the microphysical protocol; and the same high-level divergence may be realized by devices with radically different costs. The universal claim that physical control consumes resources is secure. A universal linear exchange rate between every attributed kybit and work remains a conjecture outside the restricted thermodynamic case.

I therefore state the **Law of Control Work** in two layers:

> **Physical control requires a resource-consuming implementation. Under an equilibrium-reference realization, $C$ kybits imply the lower bound $W_{\text{min}} \geq C k_B T \ln 2$.**

At room temperature $k_B T \ln 2$ is on the order of $3 \times 10^{-21}$ joules. Real control systems usually dissipate many orders of magnitude more because sensing, computation, correction, and actuation are not quasistatic ideal transformations. The bound matters as a limiting case, not as a meter that converts any observed behavioral divergence directly into joules.

## Drift Needs No Agent

The distinction from the previous chapter can now be stated without saying drift is energetically free. Uncontrolled dynamics may release, transfer, or dissipate enormous energy. What they do not require is an agent maintaining a model and paying the additional costs of sensing, correction, and actuation. Drift is the comparison trajectory, the $P_{\text{initial}}$ in the calculation. Control is the causally attributed departure from it.

Consider a drone correcting its flight toward a gap. Its battery powers sensing, computation, and actuation; a causal model compares the resulting position distribution with the wind-and-momentum baseline; the KL divergence records the size of the shift. The energy use and the kybit count describe related aspects of the same intervention, but neither alone determines the other. A more efficient drone can realize the same outcome divergence with less work, while a wasteful controller can burn energy without producing control at all.

The kybit is therefore a proposed unit with a disciplined scope: it measures an attributed distributional shift relative to an explicit baseline. The next chapter asks what physical bounds survive once that definition, its causal prerequisites, and its restricted thermodynamic bridge are kept separate.
