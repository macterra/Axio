---
title: 'What Knowledge Is'
subtitle: 'Reliable, decision-relevant uncertainty reduction'
status: review
sources:
  - 167007172.what-counts-as-knowledge
  - 164270270.defending-bayes-part-3
---

You glance at the hallway clock, read 4:17, and go on with your day believing it is 4:17. It is, in fact, 4:17. Your belief is true. It is also justified — consulting a clock that has served you faithfully for years is exactly what a responsible epistemic agent does. But the clock stopped last night, at 4:17, and you happened to walk past during the one minute in twelve hours when a dead clock tells the truth.

Do you know what time it is? A simple justified-true-belief analysis appears to say yes, although a true belief acquired by this kind of luck does not look like knowledge. This is the Gettier problem. It has generated sophisticated proposals about safety, sensitivity, defeat, and epistemic luck rather than a single agreed repair. The functional account developed here is another proposal: it puts reliable uncertainty reduction at the center.

## The Definition

Knowledge is pattern-encoded information that reliably reduces decision-relevant uncertainty within a specified domain.

Every word is doing work, so let me unpack them.

**Pattern.** Knowledge lives in a reproducible structure — a neural configuration, a logical rule, an algorithm, a cultural convention. The form does not matter; the stability does. A pattern too fragile or too idiosyncratic to be exercised twice cannot support prediction, and prediction is the job.

**Decision-relevant structure.** The pattern must be available to an agent or community — encoded in memory, practice, a trusted record, or machinery that can guide expectation and action. This accommodates both exercised skill and stored knowledge while excluding information that no one can recover or use. The relevant structures are among the models examined in [maps, models, and understanding](06-maps-models-understanding.md).

**Reliably reduces uncertainty.** Here is where the definition gets its teeth. When an agent has a well-defined probability distribution over outcomes, one useful measure is Shannon entropy,

$$H = -\sum_i p_i \log_2 p_i.$$

Before you learn the outcome of a fair coin flip, this entropy is one bit; reliable information about the outcome removes some or all of it. Not every epistemic state comes with a precise distribution, so entropy is a model when quantification is available, not a claim that all ignorance literally arrives in bits. The essential requirement is reliability across relevantly similar cases. A useful false model can reduce uncertainty inside a narrow regime, but the knowledge claim must state that domain and remain answerable to observed error; predictive success does not make every part of the model true.

**Within a specified domain.** Reliability is always indexed to a reference class, environment, timescale, and purpose. In ordinary cases it can be assessed by replication, counterfactual robustness, and out-of-sample performance. If the QBU framework introduced later is adopted, branch Measure supplies an additional model-relative way to weight future cases. The definition itself does not require that physical interpretation.

Now apply the proposal to the stopped clock. Across the relevant moments at which you might consult it, its reading carries almost no information about the actual time. The 4:17 belief was true by coincidence, which the reliability criterion is designed to filter out. Knowledge, on this account, is not a belief that happens to be true but a capacity whose connection to the result is robust. Whether this handles every Gettier case remains a test for the proposal, not a victory by definition.

## Ten Stress Tests

A definition earns its keep against hard cases. Here are ten, spanning the pedestrian, the classical, and the exotic.

**A weather forecast.** The model says rain tomorrow, and its track record shows it is right far more often than chance. Your uncertainty about tomorrow drops by a measurable number of bits, reliably, forecast after forecast. Knowledge — the everyday kind, and the definition certifies it without ceremony.

**A false belief.** A false generalization may predict well inside a limited regime: Newtonian mechanics is the familiar example. What is known in such a case is the model's reliable domain and consequences, not the unrestricted literal claim. Persistent falsehood eventually appears as systematic error when the model is pushed beyond that domain.

**A random guess.** You guess the coin will land heads, and it does. No pattern was exercised; no entropy was reduced in advance — your predictive distribution was exactly as flat after the guess as before. The lucky hit is not knowledge, and the definition never has to consult your feelings of confidence to say so.

**The stopped clock.** The classical Gettier case, dissolved above. Justified true belief without reliability is not knowledge. The other Gettier cases fall the same way, because they are all engineered around the same trick: a truth that arrives by a channel disconnected from the belief's grounds. Disconnected channels have no reliability, and reliability is the criterion.

**Riding a bicycle.** You cannot state the control law that keeps you upright — countersteering, torque against lean angle — but your nervous system encodes it, and it reduces your uncertainty about staying vertical from guesswork to near-certainty, every ride. Tacit skill is fully paid-up knowledge on this definition, not a poor relation of the propositional kind. Any account on which knowing *that* is real knowledge but knowing *how* is mere habit has the priorities backwards; the cyclist's cerebellum out-predicts the physicist's blackboard on the question that matters, which is what the bicycle will do next.

**A greeting ritual.** Shared conventions — a language, a handshake, the rules of the queue — are patterns encoded across a community rather than a single skull, and they reliably reduce every member's uncertainty about what the others will do. Cultural knowledge is knowledge, and the definition explains why it feels like knowledge from the inside: it makes the social world predictable.

**Knowing which key opens which door.** The pattern is real and reliable, and it is useless in front of any other door. All knowledge is like this; the front-door key is just the case where the conditions are too obvious to suppress. A pattern reduces entropy *given* a context, within a domain, under standing assumptions — knowledge inherits the conditional structure of [truth itself](02-all-truth-is-conditional.md), and a knowledge claim, like a truth claim, is compressed shorthand for a conditional.

**A database no one presently reads.** A recoverable, trusted archive can preserve communal knowledge even while no one is consulting it; availability, not continuous exercise, matters. A drive whose encoding and provenance are lost contains physical structure but no usable record. This distinction connects stored information to agents without pretending that knowledge vanishes whenever the library closes.

**A quantum state under the QBU interpretation.** Even a complete state description does not select a unique future observation. Within QBU, the state and its Measure distribution can be known while an observer still has self-locating uncertainty about its future record. This conditional example illustrates the later distinction between a physical model and an agent's Credence; other interpretations describe the uncertainty differently.

**Steering across branches.** Conditional on QBU and a decision rule that uses Measure, an agent can use reliable models to compare the weighted consequences of actions. That is a specialized instance of the general function: knowledge supports navigation, not merely passive anticipation.

The cases expose both the reach and the conditions of the proposal. It handles skill, convention, records, luck, and prediction in one functional vocabulary, while the quantum cases remain conditional on the physical model adopted later.

## Four Kinds of Knowledge

One definition, then — but not one kind. Patterns can reduce uncertainty in structurally different ways. Four categories provide a useful, non-exhaustive map.

**Explanatory knowledge** consists of general theories — evolution by natural selection and general relativity, for example. Such frameworks organize and explain families of observations rather than merely reporting one outcome. They are evaluated by empirical adequacy alongside coherence, simplicity, scope, and resistance to criticism. Competing theories and versions of theories can also bear graded Credence, as [In Defense of Bayes](12-in-defense-of-bayes.md) argues.

**Empirical knowledge** concerns contingent conditions: whether you carry a genetic variant, whether it will rain tomorrow, or what evidence supports an account of a historical actor's motives. This is a natural domain for graded Credence and statistical updating. Under QBU some such uncertainty can be modeled as self-location among records, but the category does not depend on that interpretation. The taxonomy of what an agent can be uncertain *about* is richer than it first appears, and I map it in [the varieties of uncertainty](13-varieties-of-uncertainty.md).

The explanatory-empirical distinction is useful, but it does not assign exclusive methods. Explanations face evidence and can receive comparative probabilities; forecasts depend on explanatory models and criticism. Bayesian bookkeeping and critical scrutiny are complementary tools whose importance varies with the problem.

Sharply drawn is not exhaustively drawn, though, and the boundary has honest hybrid cases. A parameterized theory — general relativity plus a Hubble constant, particle physics plus a dark-matter density — is an explanatory framework wrapped around an empirical dial: the framework answers to criticism while the parameter answers to Bayes. Historical interpretation blends the two the other way, running general explanatory machinery (economics, sociology, evolutionary psychology) over irreducibly branch-specific gaps in the record. The categories are joints in the territory, not a demand that every specimen fall on one side.

**Formal knowledge** — mathematics and logic — concerns what follows under specified axioms, definitions, and inference rules: arithmetic, set theory, Gödel's incompleteness theorems. Once the formal context is fixed, no empirical observation changes the derivation, although our choice and understanding of formal systems remain historically and cognitively situated. Its uncertainty reduction is distinctive: it exposes consequences of premises and multiplies the power of empirical models.

**Tacit knowledge** — the bicycle, the violin, the seasoned diagnostician's hunch — is embodied, implicit, and resistant to explicit formulation. It passed the stress test above on the same terms as everything else, and that is the point of listing it as a full category rather than a footnote: the definition never required knowledge to be statable, only to be encoded and reliable.

The typology also explains why the classical definition was doomed. Justified true belief was reverse-engineered from one category — explicit, propositional, single-timeline empirical claims — and then declared the essence of the whole. Tacit knowledge fails its belief clause, formal knowledge trivializes its truth clause, explanatory knowledge strains its justification clause, and Gettier cases break it even on its home turf. Entropy reduction covers all four kinds without strain because it is a claim about what knowledge *does*, not about the format it comes in.

## Knowledge Cashed Out

This account slots into the volume's larger architecture. Beliefs, as I argue in [what beliefs are](08-what-beliefs-are.md), are predictive models, and their virtue is calibration; knowledge is the portion of an agent's predictive structure whose calibration is *earned* — patterns with a track record of paying out in bits. Truth is conditional validity relative to specified assumptions; knowledge is conditional too, a pattern that delivers within its domain and is silent outside it, front-door key writ large.

And the definition returns an answer to the oldest question about knowledge — what is it worth? — in the only currency an agent ultimately spends. Entropy about the future is risk: the predator not anticipated, the market not modeled, the side effect not foreseen. A pattern that reliably removes bits of that uncertainty is not a representation to be admired; it is traction. The measure of what you know is what you can predict, and the measure of what you can predict is how deliberately you can steer — through the one world of common experience, and through the branching futures beneath it.
