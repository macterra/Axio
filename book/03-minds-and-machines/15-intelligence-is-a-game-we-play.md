---
title: 'Intelligence Is a Game We Play'
subtitle: 'The strategic core'
status: draft
sources:
  - 163805376.intelligence-is-a-game-we-play
  - 172908866.foresight-is-not-intelligence
  - 166857416.intelligence-as-a-hyperobject
---

Arguments about intelligence have a way of going nowhere. Is an LLM intelligent? Is an octopus? Is IQ meaningful, or a colonial relic? Was the chess grandmaster who lost his fortune to a con man smart or stupid? The disputants talk past each other for a predictable reason: nobody has said what the word means, and each party is quietly using a definition that flatters their side. Before this volume can say anything useful about machine minds, it needs a definition of intelligence that does real work — one precise enough to settle arguments rather than restate them.

I build that definition on a foundation that philosophy officially declared unbuildable.

## Answering Wittgenstein

Wittgenstein famously argued in *Philosophical Investigations* that the concept of a "game" defies precise definition. Board games, ball games, card games, solitaire, ring-around-the-rosy: search for a property common to all of them, he said, and you will find none — only a network of overlapping similarities, "family resemblances," with no essential core. The passage became the standard citation for the futility of definition itself, and "game" became the canonical example of a concept that cannot be pinned down.

Wittgenstein was right about the surface and wrong about the depth. He was right that no enumeration of features — rules, scoring, competition, amusement — captures every game while excluding every non-game. But he was hunting at the wrong level of abstraction. The common core of games is not a feature list; it is a structural property:

**A game is any interactive process involving agents, where strategy — the deliberate selection among alternatives in pursuit of preferred outcomes — is salient.**

This definition isolates four crucial elements:

1. **Agency.** The salience of strategy implies at least one agent capable of choice. Without agency, strategic considerations collapse into deterministic inevitability or randomness.
2. **Strategy.** Meaningful decision-making among alternatives, each evaluated by some criterion of desirability. This is what differentiates a game from purely deterministic or stochastic phenomena.
3. **Interaction.** Though commonly associated with multiple participants, even solitary interactions between an agent and an environment qualify. The environment itself can embody strategic dynamics.
4. **Preferred outcomes.** Strategies aim at goals, whether explicitly articulated or implicitly understood.

The obvious objections dissolve on contact. *Games require multiple agents?* Solitaire and rock-climbing are strategic engagements with an environment. *Games require explicit rules?* Rules can be implicit, emergent, or situationally defined — the "rules" of a courtship or a career are no less binding for being unwritten. *Wittgenstein's critique invalidates all definitions?* It invalidates definitions by feature-enumeration. A minimalist, strategy-centric definition does not enumerate features; it names the abstraction that makes the family resemble itself. Wittgenstein documented the symptoms and missed the diagnosis.

## Intelligence Defined Through Games

Why spend this effort on "game"? Because once the game is defined, intelligence falls out almost for free:

**Intelligence is effectiveness at achieving goals within the constraints of a given game.**

The definition is deliberately relational. Intelligence is not a substance a system contains or a fluid it secretes; it is a performance measure, and a performance measure is meaningless without a specified context — a game. Asking "how intelligent is this system?" without specifying the game is like asking "how fast?" without specifying the course.

This immediately demystifies the proliferation of "intelligences" that so embarrasses the unitary view. Emotional intelligence, mathematical intelligence, social intelligence — these are not evidence that the concept is confused. They are proficiencies at different implicit games:

- **Career intelligence:** the game of economic competition, professional networking, and advancement.
- **Social intelligence:** navigating the implicit rules of cultural norms and social signaling.
- **Scientific intelligence:** effective play within epistemic norms, research methodologies, and peer review.

Naming the implicit game clarifies debates that otherwise run in circles. The general-versus-domain-specific dispute, for instance, is largely a dispute about which games are being scored. And the grandmaster fleeced by a con man is no paradox at all: he is a superb player of one game and a poor player of another.

The definition also scales downward, all the way to the floor of agency. A bacterium climbing a sugar gradient is playing a simple game — sample the concentration, forecast which direction improves it, suppress tumbling when the news is good — and its chemotactic strategy is rudimentary intelligence by exactly this standard. That is no coincidence: the game-relative definition of intelligence is built on the same three-part structure of agency — embeddedness, predictive modeling, intentional biasing — developed in [Minimal and Maximal Agents](../01-physics-of-agency/05-minimal-and-maximal-agents.md), where the same bacterium marks the minimum viable agent. Intelligence is what the quality of an agent's play looks like from outside; agency is what makes there be play at all. And it scales upward without modification: humans play vastly more complex games — science, politics, philosophy — and machine intelligence, when it arrives in force, will be assessed the same way, by the games it can play and how well.

## The Oracle and the Agent

The definition has teeth, and the best way to show them is against a rival that sounds compelling. Elon Musk has asserted, as a standing position, that "the ability to predict the future is the best measure of intelligence." The claim is crisp, and it resonates with real science. Brains are prediction machines; Karl Friston's free energy principle formalizes cognition as the minimization of prediction error; in machine learning, predictive accuracy is the easiest thing to quantify. Prediction is not a bad candidate. It is the best wrong answer available.

And it is wrong, because prediction is necessary but not sufficient. Consider what pure foresight buys on its own:

- A weather oracle that perfectly forecasts tomorrow's storm cannot act, strategize, or pursue goals.
- A chess engine that knows the opponent's next moves is powerful — but without a framework for winning, the knowledge is inert.
- A prophet who foresees disaster and cannot respond is not intelligent, merely informed.

The oracle appeared once before in this book, as a structural diagnosis: strip embeddedness from an agent and what remains is an oracle — a system that computes over the world but never acts within it. Musk's definition selects for exactly that amputation. Set the two conceptions side by side and the difference runs through every element of the game:

| Feature | Game-Based Intelligence (Axio) | Prediction-Based Definition |
|---|---|---|
| **Agency** | Central — modeling, choosing, acting | Absent or implicit — passive forecasting |
| **Strategy** | Core — decisions among alternatives matter | Not required — mere foresight suffices |
| **Interaction** | Embedded — multi-agent or environment-based | Nonessential — forecasting can be isolated |
| **Goals** | Explicit — pursuit of preferred outcomes | Ignored — accuracy not tied to value |
| **Creativity** | Building futures, defining new games | Unnecessary — construction not required |
| **Scope** | Domain-general, adaptable across contexts | Narrow — domain-specific foresight |

None of this demotes prediction. Without anticipating consequences, no agent could play any game effectively; predictive modeling is the engine of agency, and in adversarial games strategic advantage tracks model accuracy directly. But intelligence requires the full stack: **prediction**, for epistemic grounding; **strategy**, for reasoning about alternatives; **agency**, for the capacity to act and construct futures; and **goals**, so the play is aimed at something worth achieving. Reducing intelligence to prediction amputates its constructive half. It is like calling eyesight the best measure of athletic ability: indispensable, and useless on the field without movement, strength, and coordination.

The prediction-centric definition is not an idle philosophical error; it is the load-bearing assumption of the benchmark arms race. One quarter this lab's model tops a forecasting leaderboard, the next quarter a rival dominates some other metric, and each result is announced as a measurement of intelligence itself. These scoreboards say less about the nature of intelligence than about marketing cycles: a benchmark is a single game, usually a spectator-friendly oracle's game, and topping it demonstrates proficiency at that game — nothing more. True intelligence, biological or artificial, is not proven in any one competition. It is proven in the endless plurality of games agents play across reality.

So the prediction thesis is half-right, and the half matters. Prediction is the backbone of cognition. But intelligence, properly defined, is not mere foresight — it is foresight *in play*: the art of navigating, strategizing, and constructing futures within constraints. An oracle may predict, but only an agent can play. **Intelligence is not the ability to foresee the future. It is the ability to *create* one.**

## Intelligence as a Hyperobject

There is a final move to make, and it guards the definition against its own success. Having defined intelligence cleanly — effectiveness at a game — the temptation is to conclude that intelligence as a whole is now a tidy, measurable thing. It is not, and the reason is built into the definition: the measure is game-relative, and the games are without limit.

This is why the rival theories of intelligence correlate so stubbornly without converging. Cognitive science, philosophy, neuroscience, and AI research have each staked a claim: intelligence is predictive inference; it is goal-directed problem-solving; it is an adaptation for evolutionary fitness; it is an organ of social coordination. Each theory is compelling and each is incomplete, because each has fixed its instruments on a different region of the same enormous object.

The right lens here is Timothy Morton's concept of a **hyperobject**: an entity so vast, distributed, and multidimensional that it cannot be fully grasped from any single perspective — climate is the canonical example. Intelligence matches the description point for point:

- **High dimensionality.** It integrates cognition, perception, emotion, computation, and social interaction.
- **Non-locality.** It is distributed across brains, bodies, environments, and cultural systems — no skull contains it.
- **Temporal extension.** It spans evolutionary history, developmental lifespans, and cultural evolution.
- **Interobjectivity.** It exists only relationally — agents interacting with environments, tools, and societies. This is the game-relativity of the definition, seen from the outside.
- **Partial observability.** No single discipline, model, or metric captures it whole.

The hyperobject framing is not mysticism; it is a precise statement of the concept's dimensionality, and it prescribes epistemic humility of a specific kind. Every measurement of intelligence is a projection of a high-dimensional object onto a low-dimensional instrument, and every projection discards information. That is what a benchmark is. That is also what an IQ score is — which is not a slur against IQ. A projection can be honest, stable, and predictive within its domain while remaining a projection, and the next chapter, [In Defense of IQ](16-in-defense-of-iq.md), defends exactly that: a calibrated, game-relative scalar that earns its keep so long as it is never mistaken for a cosmic rank. The failure mode is not measurement but reduction — collapsing the hyperobject to one of its shadows and then reasoning from the shadow, an error whose grandest forms, the myths of universal and of illusory general intelligence, occupy [Universality and Generality](17-universality-and-generality.md).

So the account comes to this. A game is any interactive process where strategy is salient. Intelligence is effectiveness at achieving goals within a game's constraints. The plurality of intelligences is the plurality of games; prediction is the engine of play but never the whole of it; and the concept in full is a hyperobject that no scalar will ever exhaust. Anyone who tells you intelligence is one number, one benchmark, or one faculty is not measuring the object. They are measuring their instrument.
