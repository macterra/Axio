---
title: 'Constructors'
subtitle: 'How order becomes causal power'
status: review
sources:
  - 171907779.constructors-from-coherence
  - 172303733.constructors-and-transitions
  - 171165360.infinite-randomness-and-constructor
---

The formalism at the end of the previous chapter describes sets and maps, not a physical process. Calling equivalence classes “worlds” does not yet supply dynamics, causation, or realization. This chapter proposes constructors as the next modeling layer: persistent systems that implement repeatable physical transformations. It does not derive those systems from the mere existence of encoded maps.

The concept comes from David Deutsch and Chiara Marletto's Constructor Theory. I borrow it as a proposed bridge between the Chaos representation and physics. Constructor theory itself does not entail the Chaos ontology, and the analogy should not be mistaken for an integration already established by either framework.

## What a Constructor Is

Deutsch's definition: a constructor is anything that can cause transformations in physical systems without undergoing any net change in its ability to do so. Equivalently, a constructor performs a task whenever it is presented with substrates in a legitimate input state, transforming them to the appropriate output state, while retaining its own capacity to perform the task again. A catalyst is the chemist's example: it drives the reaction and comes out the far side unchanged, ready to drive it again.

Translated into the Chaos framework, this becomes the canonical definition I will use for the rest of the volume:

**A constructor is a coherent pattern that enacts stable correlations between other patterns while preserving its own coherence.**

The definition can be represented schematically. If $F$ classifies modeled states and $T$ maps inputs to outputs, then $F(T(x)) = 1$ says the output remains in the accepted domain. A separate condition must identify a subsystem whose ability to perform the task is retained. The earlier condition $F(s)=1$ says only that $s$ passes a predicate; it does not by itself establish endurance or construction.

In the equivalence-class picture, where semantic filters have already refined Chaos into a space of world states, the same definition reads as a mapping between classes:

$$C : [x] \to [y]$$

where $[x]$ and $[y]$ are equivalence classes of strings — world states — and $C$ carries one to the other. Three conditions make the mapping a constructor and not just an arrow drawn between boxes:

- **Persistence.** The constructor survives the transition. It appears in both $[x]$ and $[y]$, unchanged in its constructive role.
- **Closure.** If any string $s \in [x]$ is acted upon, the result belongs to some class $[y]$ — the mapping never falls out of the state space.
- **Lawfulness.** The mapping respects the semantics defined by the filter; it never produces incoherent states.

That is the whole definition, stated once. Persistence is what distinguishes a constructor from a mere event; closure and lawfulness are what distinguish it from noise that happens to shuffle bits. Everything else in this chapter is what the definition buys.

## Transformation Without Change

There is an obvious objection to hurdle first. Chaos, as defined, is static: the set of all infinite random bitstrings, complete and timeless. Nothing in a static ensemble can literally *change*. How can a static ontology support transformation at all?

The proposed resolution is to represent transformations as **stable correlations across modeled states**. A hydrogen atom absorbing a photon can be described by correlated input and output configurations under quantum dynamics. That block-style representation can encode change without treating the possibility space itself as changing. It remains an interpretation of the dynamics, not a derivation of them from static correlation.

The finite automaton makes the same point without the physics. An automaton's states are equivalence classes; its transition function maps state to state. Nothing about the transition *table* changes when the machine runs — the table is the persistent structure that implements every transition. A constructor is exactly that: the enduring pattern in which a state-to-successor-state mapping lives. And the quantum version should sound familiar from Part II: in the [Quantum Branching Universe (QBU)](08-the-quantum-branching-universe.md), semantic filters partition outcomes into branches, and constructors are the stable systems — atoms, catalysts, measuring devices — that persist across branches while enacting transformations on everything else.

So the sense in which worlds "evolve" is this: a trajectory is a chain of world states linked by constructor mappings, and the appearance of dynamics is the coherence of that chain. Static ontology underneath; lawful succession on top. Whether that succession is all time *is* — and what it means that we experience traversing it — is the business of [the next chapter](23-life-consciousness-time.md).

## From Recognition to Propagation

Seen this way, the step from filters to constructors is the step from statics to dynamics — from coherence as a property to coherence as a power.

A filter performs static recognition: *this sequence is coherent.* A constructor performs relational mapping: *this sequence coherently maps to that sequence.* Filters define which states are valid; constructors define which correlations between states are valid. The first is a boundary; the second is a bridge.

The transition matters more than it might look. A universe with filters alone contains islands of order, but each island is a fragile accident — a pattern that happens to satisfy its own selection condition, going nowhere. Once coherence can propagate through correlations, order becomes self-sustaining: a coherent pattern that reliably produces further coherence is no longer at the mercy of the ensemble it sits in. Constructors are how order stops being lucky and starts being causal. They are the lawful bridges that carry coherence forward — the point in the architecture where structure first acquires something worth calling causal power.

## The Constructor Theory Connection

Now the integration. Deutsch and Marletto's Constructor Theory proposes a reformulation of physics in which the fundamental statements are not equations of motion evolving initial conditions through time, but claims about which transformations are **possible** and which are **impossible**. A law of physics, in their idiom, is a statement that some task can be performed by a constructor — or that no constructor for it can exist. Even time gets this treatment: in their Constructor Theory of Time, duration is not read off an external clock but emerges from comparing repeated transformations. A clock is a cyclic constructor — a pattern that enacts the same transformation again and again while preserving its capacity to do so — and time is what you get by counting one constructor's cycles against another's.

The Chaos proposal, meanwhile, tries to represent physical possibility using coherence conditions. Logical consistency is not sufficient for physical possibility, and a predicate's acceptance does not make a structure persist or interact. Any synthesis must add the actual physical task constraints that constructor theory studies.

The two binaries are analogous but not identical. Constructor theory's possible/impossible distinction is constrained by physical law; logical coherence alone permits many worlds that are not physically possible under our laws. The proposed synthesis treats physical task constraints as a specialized coherence relation:

- **Constructor theory alone** is an elegant reframing of physics, but it lacks a metaphysical ground. It tells you the laws are statements about which transformations are possible — and is silent on why constructors, or possibility-structure itself, exist at all.
- **The Chaos ontology alone** is radical minimalism — randomness plus one filter — but without physical machinery it risks being dismissed as unfalsifiable speculation.

Together they sketch a possible stack: a possibility-space representation at the bottom and physically constrained tasks in the middle. It remains incomplete until it explains why one measure, law set, and realization relation are privileged. The result is a research proposal, not a completed foundation for constructor theory.

## Physics as Catalogue

Which yields this part's central claim about physics itself. The laws of physics are not a primitive backdrop against which events play out. They are **the stable constraints that determine which correlations are coherent** — and constructors instantiate those laws by embodying the allowed correlations while retaining their own coherence. Physics is the emergent catalogue of coherent correlations: the bookkeeping system for what coherence-allowed patterns can do to one another. Quantum field theory, general relativity — on this view, emergent constraint sets, compiled from the correlations that survive.

This is also where the volume's two halves join hands. [The Interpretation Wars](12-the-interpretation-wars.md) ended with the structural-realist picture of the universe as a network of local, reversible transformations, and promised that this volume would say what runs on that network. Here is the answer: the network's nodes and links are exactly the world states and lawful mappings of this chapter, and constructors are the persistent patterns that implement the transformations. The QBU describes the branching structure of the catalogue; the Chaos ontology says why there is a catalogue; constructors are its working parts.

## Toward Life

The definition of a constructor sets a low bar on purpose — a hydrogen atom clears it. But the concept scales, and the scaling is the plot of the rest of this part. Some constructors stabilize transformations of extraordinary generality: universal computers, brains. And when constructors acquire three further capacities — maintaining their own coherence against degradation (self-maintenance), producing copies of themselves (replication), and eventually representing their own state transitions internally (recursive models) — the catalogue starts generating entries of a new kind. The first two capacities are life. The third is the doorstep of consciousness: a constructor that not only preserves coherence but represents it, coherence become aware of itself. That ascent — [life, consciousness, and the emergence of time](23-life-consciousness-time.md) — is where the Chaos sequence has been heading all along.

Constructors supply useful language for repeatable transformations within a physical theory. Whether they also complete a derivation from Chaos to evolving worlds, life, and mind is the open conjecture this sequence has made visible.
