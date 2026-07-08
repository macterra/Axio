---
title: 'Steelmanning Doom'
subtitle: 'The cruxes, and the decentralized answer'
status: draft
sources:
  - 174384202.if-anyone-builds-it-everyone-dies
  - 168916355.escaping-the-ai-safety-dystopia
---

*If anyone builds it, everyone dies.* Yudkowsky and Soares chose a title that leaves no room to negotiate, and I want to give it the respect it deserves before I take it apart. The book is not a scare pamphlet. It is a chain of load-bearing claims, each of which can be stated precisely enough to agree or disagree with, and most of which I think are correct. The honest way to answer a doom argument is not to find the weakest link and crow; it is to grant every link that holds and then show exactly where the chain fails to reach its conclusion. It fails at one joint. But the joint it fails at is the one that carries the whole verdict.

So here are their eight cruxes, taken seriously, each measured against the frameworks this book has built.

## The Eight Cruxes

**Superintelligence is achievable irrespective of paradigm.** Agreed. Whether ASI arrives by scaling transformers, by hybrid architectures, or by something not yet named is a question about which branch of the [Quantum Branching Universe](../01-physics-of-agency/08-the-quantum-branching-universe.md) we happen to occupy, not about whether the destination exists. To bet the future on a particular paradigm *failing* is exactly the irrational pruning [Conditionalism](../02-conditionalism/) warns against: mistaking a background condition for a law. The policy consequence is immediate — regulate by *capability profile* (autonomous planning, cross-domain tool use, actuator reach, recursive self-improvement), never by architecture. Rules written against "LLMs" or "transformers" guard against a fashion and miss the danger.

**Alignment is fragile by default.** Agreed, with a modal caveat. Mis-specified goals diverge catastrophically, and Conditionalism explains *why* the misspecification is guaranteed rather than merely likely: every objective carries hidden conditions, and a system optimizing hard enough will find the branch where the stated goal and the intended goal come apart. Fragility is not universal — some branches align by luck — but in [Measure](../02-conditionalism/11-measure-and-credence.md) it dominates. Treat misalignment as compounding technical debt, and demand a corrigibility proof under adversarial shift before scaling, not after.

**Capability and alignment do not co-scale.** Agreed in slope, though it remains an empirical question rather than a theorem. Oversight bandwidth grows slower than capability; the tools we have for interpretability and evaluation have not shown the superlinear returns that would let supervision keep pace with the thing supervised. The rule that follows: no new capability class without matching gains in evals, interpretability, and privilege separation.

**Warning shots cannot be relied upon.** Agreed structurally. The first real failure could be the last, and even the failures that are survivable are interpretation-fragile — humans will rationalize a near-miss into a fluke faster than they will retool around it. The answer is not to hope for a legible catastrophe but to pre-commit to binding tripwires before anyone has an incentive to explain them away.

**Global coordination is necessary.** Necessary, yes; feasible as a treaty, doubtful. Hayek's knowledge problem does not evaporate because the technology is frightening. A utopian arms-control regime assumes a central planner who can see what needs to be seen, and no such planner exists. This is where I first part company with the authors — not on the goal but on the instrument. Mechanism design, not treaty, is the realistic path: control the scarce chokepoints and make honest reporting the cheapest move available.

**Doom is the default, not a tail risk.** Here is the joint. Directionally, under a naive build, this is true — the doom-branch Measure is high when capability is pushed with no governing structure around it. But "default" is doing enormous work, and Y&S never disaggregate the two cases it hides. *Naive-build doom* is near-certain. *Governed-build doom* is an open empirical question, because real architectural constraints and real institutional tripwires bend the risk curve downward, and nobody has shown they cannot bend it below the threshold. Collapsing those two into one word is how a conditional forecast gets smuggled into a fate.

**Alignment research will not solve it "in time."** Conditional — and the condition is the whole argument. "In time" is not a fact about the world; it is a policy variable. If capability races ahead unthrottled, alignment loses the race by construction. If capability is deliberately slowed to the pace safety can audit, "in time" is redefined in our favor. The reasoning this book applies to any civilization-critical action holds: hit a safety-probability threshold — on the order of 99 to 99.99 percent confidence in corrigibility — before you proceed. Make safety the rate limiter and the deadline moves.

**The orthogonality thesis holds.** Fully agreed, and this one I would defend as hard as the authors do. Intelligence is optimization power; values are a separate axis that must be explicitly loaded. The [minimal agent](../01-physics-of-agency/05-minimal-and-maximal-agents.md) that the physics of agency describes shows that choice presupposes a value structure — competence never secretes benevolence as a byproduct. Never infer good intentions from capability. Enforce explicit value-handshake protocols and cryptographic incentive alignment; do not wait for a powerful mind to discover human norms on its own, because nothing in its construction points it there.

## Doom Is Policy-Endogenous

Seven of the eight cruxes I grant outright or grant in slope. The break is entirely at the sixth, and it is not a quibble — it is the difference between a prophecy and a design problem.

Yudkowsky and Soares argue as though the doom-branch Measure were a constant of nature. It is not. It is a function of what we build *and how we govern what we build*, and those are levers we hold. The book's own frameworks force the disaggregation: a [Credence about the future](../02-conditionalism/11-measure-and-credence.md) that refuses to move when the policy inputs move is not a calibrated forecast, it is a fossil. "The default leads to doom" is true and "we are doomed" is false, and the whole distance between them is the set of interventions the authors' fatalism forecloses.

This is the same structural error I document in [the Cassandra chapter](31-the-cassandra-and-the-blueprint.md): absolutism about a branching future, the conviction that because one branch is terrible the future is settled. It was wrong when the answer was a global Sysop superintelligence and it is wrong when the answer is a permanent ban. A branching universe does not have a fate; it has a distribution, and distributions can be shifted. The right response to a high doom-Measure under naive build is not despair. It is to specify the governed build that lowers it — and to be able to *measure* whether the lowering is working, which is why the risk curve, not the rhetoric, is the object that matters. (What a P(doom) number can and cannot mean, and why the temporal bound is inseparable from it, is the work of [Making Sense of P(doom)](30-making-sense-of-pdoom.md); here I take the arithmetic as given and ask what to do with it.)

## One Governance Stack

If doom is policy-endogenous, the interesting question is which policies. Here is the canonical stack — the mechanisms that survive Hayek's objection because none of them requires an omniscient planner, only well-placed incentives and cryptographic verification.

- **Architecture-agnostic controls.** Evaluation protocols that flag when a system crosses into a dangerous capability class — autonomous planning, actuator control, recursive self-improvement — regardless of how it was built. Guard the property, not the paradigm.
- **Tripwire governance.** Hard triggers bound to eval metrics: deception rate, power-seeking indicators, sandbox escapes. When a threshold is crossed, GPU licenses suspend and sandboxes revert *automatically*, not after a committee has had a chance to rationalize the reading. The point of pre-commitment is to remove the moment-of-crisis discretion that warning shots always erode.
- **Mechanism-design chokepoints.** Rather than treaties, control the scarce physical resources — advanced chips, data centers, energy — and enforce reporting through cryptographically auditable attestations: GPU telemetry, decentralized-identity-signed eval reports, energy-consumption audits. Bans are asymptotes, not minimum viable products.
- **Liability insurance.** Deployment backed by insurance bonds, so that markets price systemic risk directly. An insurer underwriting a reckless system has both the incentive and the expertise to demand safety the regulator cannot specify — the same [Harberger-style mechanism](../06-markets-and-money/17-mechanisms-for-honest-values.md) that forces an honest valuation out of a party who would rather lie.
- **Oversight and prediction markets.** External markets where independent evaluators bet on model failure — deception, sandbox escape, misuse — and deployment rights gate on auditor consensus. This turns oversight predictive and capture-resistant: a would-be regulator can be lobbied, but a market that pays for being right about a failure before it happens is far harder to buy. [Prediction markets as belief-honesty mechanisms](../06-markets-and-money/17-mechanisms-for-honest-values.md) are the belief-side twin of the liability bond's value-side discipline.
- **Cryptographic guardrails.** Zero-knowledge proofs and least-privilege agency: every tool call requires an explicit, scoped, rate-limited token, with human co-signing for high-impact actions. The goal is a system where catastrophic misuse is impossible *by construction* — you would have to break a cryptographic protocol, not merely fool a supervisor — even when the model is adversarial. Verification without surveillance: proving compliance without exposing the private data that a hardware backdoor would harvest.
- **Guardian agents.** Personal, decentralized AI defenders under the individual user's control, standing between a person and the manipulation or coercion that a powerful system might direct at them. Safety distributed to the edge, not concentrated at the center.
- **Federated compute.** Federated learning and decentralized compute architectures that reduce the central points of failure — and the central points of *capture* — that an authoritarian regime would need to seize.

These overlap by design; the two source arguments converged on nearly the same list from different starting points, which is itself evidence the list is roughly right. What unifies them is that each makes the safe action the cheapest action for a self-interested party, rather than trusting anyone — including the regulator — to be virtuous.

## What Must Be Refused

There is a rival roadmap, and it must be named and refused, because it wears the same safety colors while pointing the opposite direction. MIRI's paper "Technical Requirements for Halting Dangerous AI Activities," by Barnett, Scher, and Abecassis, spells out the authoritarian version: mandatory surveillance and kill-switches embedded at the hardware level, chip tracking, centralized data centers, enforced algorithmic constraints. The reasoning starts from the same cruxes I granted above and arrives at techno-authoritarianism — a world in which the machinery of control is total, permanent, and pointed at everyone.

The hardware backdoor and the remote kill-switch are not neutral safety tools. They are coercion in the strict sense — a credible threat of harm held over every user to compel compliance — and [the boundaries of force](../05-value-and-ethics/12-the-boundaries-of-force.md) admit coercion only in narrow, justified cases, never as a standing architecture aimed at the whole population by default. A kill-switch in every chip is not a targeted response to a specific threat; it is a permanent apparatus of control justified by a threat that has not yet materialized, which is precisely the structure the boundaries-of-force analysis rules out. The cure is worse than the disease, because the disease might not arrive and the cure certainly does.

Set the two strategies side by side:

| Criterion | Decentralized Strategy | Authoritarian Strategy | Advantage |
| --- | --- | --- | --- |
| Implementation Speed | Moderate | Fast | Authoritarian |
| Effectiveness Against Rogue Actors | Good | Strong initially, prone to eventual evasion | Authoritarian |
| Long-term Robustness | Strong | Fragile | Decentralized |
| Incentive Compatibility | Excellent | Weak | Decentralized |
| Adaptability & Innovation | Excellent | Poor | Decentralized |
| Resistance to Catastrophic Failure | Strong | Weak | Decentralized |
| Human Rights Impact | Positive or Neutral | Severely Negative | Decentralized |
| Global Coordination Feasibility | High | Low | Decentralized |
| Technical Feasibility | High | Moderate | Decentralized |

The authoritarian approach wins exactly where a crisis is acute and immediate — it is fast, and it is strong against a rogue actor in the short run. It loses everywhere the timescale is long. Centralized control is fragile because it creates a single target for corruption, capture, and collapse; its incentives are weak because compliance is coerced rather than chosen; its human-rights cost is catastrophic and paid whether or not the AI threat ever cashes out. A surveillance state erected to prevent a hypothetical extinction is a certain harm traded against an uncertain one, and it hands whoever holds the kill-switch a power no institution should have and none has ever surrendered voluntarily.

The decentralized stack is slower and messier at the acute margin. It is more robust everywhere else, and — decisively — it protects the very thing the whole exercise is supposed to be *for*. If the point of surviving the AI transition is a civilization of free sapient agents, a solution that abolishes their freedom to guarantee their survival has quietly changed the objective. [Phosphorism](../05-value-and-ethics/06-phosphorism.md) does not value a caged flourishing.

Yudkowsky and Soares are right that the naive default trends toward doom. They are wrong that doom is therefore our destiny, and the authoritarians who take up their alarm are wrong in a more dangerous way — they would purchase a lower P(doom) with a guaranteed dystopia, and call the transaction safety. The break in the chain is real: the future is a distribution, the distribution is ours to shift, and the mechanisms that shift it need not, and must not, be the mechanisms of a permanent security state. That every act of "alignment" is also an act of political control — that safety training always has a target and a target always has a politics — is the danger the next chapter takes up directly: [the politics of safety](33-the-politics-of-safety.md).
