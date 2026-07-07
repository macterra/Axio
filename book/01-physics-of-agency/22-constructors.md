---
title: 'Constructors'
subtitle: 'How order becomes causal power'
status: draft
sources:
  - 171907779.constructors-from-coherence
  - 172303733.constructors-and-transitions
  - 171165360.infinite-randomness-and-constructor
---

The Chaos ontology, as it stands at the end of the previous chapter, has an embarrassing feature: nothing in it ever happens. [Coherence filters](21-coherence-filters.md) carve coherent strings out of the reservoir of infinite randomness; semantic filters partition the survivors into equivalence classes, each class a lawful world state. That gets us worlds — but frozen ones. A gallery of consistent configurations with no transitions between them is not a universe; it is a museum. States without dynamics cannot support causation, evolution, or agency, and this volume is supposed to be about agency. Something has to carry coherence forward — to make one lawful state *become* another.

That something is the constructor. Constructors are the dynamical layer of the Chaos ontology: the bridge from coherence to physics. And they are not an invention of mine. The concept comes from David Deutsch and Chiara Marletto's Constructor Theory, and the fit between their physics program and this metaphysics is close enough that I will argue each supplies exactly what the other lacks.

## What a Constructor Is

Deutsch's definition: a constructor is anything that can cause transformations in physical systems without undergoing any net change in its ability to do so. Equivalently, a constructor performs a task whenever it is presented with substrates in a legitimate input state, transforming them to the appropriate output state, while retaining its own capacity to perform the task again. A catalyst is the chemist's example: it drives the reaction and comes out the far side unchanged, ready to drive it again.

Translated into the Chaos framework, this becomes the canonical definition I will use for the rest of the volume:

**A constructor is a coherent pattern that enacts stable correlations between other patterns while preserving its own coherence.**

The definition has a formal skeleton. If $F$ is a filter encoding a pattern $s$, then $s$ is a constructor if it defines a relation $T : C \to C$ on Chaos such that $F(T(x)) = 1$ for inputs $x$ in some domain, while preserving $F(s) = 1$. Like the coherence filters of the last chapter, the condition has a fixed-point character — but now it is a dual fixed point. $F(s) = 1$ says the constructor selects itself: it endures. $F(T(x)) = 1$ says the correlations it enacts land inside coherence: it propagates order into its environment. Self-coherence and transformational closure, in one package.

In the equivalence-class picture, where semantic filters have already refined Chaos into a space of world states, the same definition reads as a mapping between classes:

$$C : [x] \to [y]$$

where $[x]$ and $[y]$ are equivalence classes of strings — world states — and $C$ carries one to the other. Three conditions make the mapping a constructor and not just an arrow drawn between boxes:

- **Persistence.** The constructor survives the transition. It appears in both $[x]$ and $[y]$, unchanged in its constructive role.
- **Closure.** If any string $s \in [x]$ is acted upon, the result belongs to some class $[y]$ — the mapping never falls out of the state space.
- **Lawfulness.** The mapping respects the semantics defined by the filter; it never produces incoherent states.

That is the whole definition, stated once. Persistence is what distinguishes a constructor from a mere event; closure and lawfulness are what distinguish it from noise that happens to shuffle bits. Everything else in this chapter is what the definition buys.

## Transformation Without Change

There is an obvious objection to hurdle first. Chaos, as defined, is static: the set of all infinite random bitstrings, complete and timeless. Nothing in a static ensemble can literally *change*. How can a static ontology support transformation at all?

The resolution is that transformations are not literal changes to Chaos. They are **stable correlations across subpatterns of Chaos**. Take a hydrogen atom absorbing a photon. In the standard telling, the atom *does* something: it takes in the photon and its electron jumps to a higher energy level. In the Chaos telling, the hydrogen atom is a constructor pattern that correlates input configurations (electron plus photon) with output configurations (electron at higher energy) — and the atom pattern itself persists in both. Nothing in the underlying ensemble moved. What exists is a reliable correlation, embodied in a pattern that appears on both sides of it. The atom does not undergo the transformation; it *is* the transformation, held stable.

The finite automaton makes the same point without the physics. An automaton's states are equivalence classes; its transition function maps state to state. Nothing about the transition *table* changes when the machine runs — the table is the persistent structure that implements every transition. A constructor is exactly that: the enduring pattern in which a state-to-successor-state mapping lives. And the quantum version should sound familiar from Part II: in the [Quantum Branching Universe (QBU)](08-the-quantum-branching-universe.md), semantic filters partition outcomes into branches, and constructors are the stable systems — atoms, catalysts, measuring devices — that persist across branches while enacting transformations on everything else.

So the sense in which worlds "evolve" is this: a trajectory is a chain of world states linked by constructor mappings, and the appearance of dynamics is the coherence of that chain. Static ontology underneath; lawful succession on top. Whether that succession is all time *is* — and what it means that we experience traversing it — is the business of [the next chapter](23-life-consciousness-time.md).

## From Recognition to Propagation

Seen this way, the step from filters to constructors is the step from statics to dynamics — from coherence as a property to coherence as a power.

A filter performs static recognition: *this sequence is coherent.* A constructor performs relational mapping: *this sequence coherently maps to that sequence.* Filters define which states are valid; constructors define which correlations between states are valid. The first is a boundary; the second is a bridge.

The transition matters more than it might look. A universe with filters alone contains islands of order, but each island is a fragile accident — a pattern that happens to satisfy its own selection condition, going nowhere. Once coherence can propagate through correlations, order becomes self-sustaining: a coherent pattern that reliably produces further coherence is no longer at the mercy of the ensemble it sits in. Constructors are how order stops being lucky and starts being causal. They are the lawful bridges that carry coherence forward — the point in the architecture where structure first acquires something worth calling causal power.

## The Constructor Theory Connection

Now the integration. Deutsch and Marletto's Constructor Theory proposes a reformulation of physics in which the fundamental statements are not equations of motion evolving initial conditions through time, but claims about which transformations are **possible** and which are **impossible**. A law of physics, in their idiom, is a statement that some task can be performed by a constructor — or that no constructor for it can exist. Even time gets this treatment: in their Constructor Theory of Time, duration is not read off an external clock but emerges from comparing repeated transformations. A clock is a cyclic constructor — a pattern that enacts the same transformation again and again while preserving its capacity to do so — and time is what you get by counting one constructor's cycles against another's.

The Chaos framework, meanwhile, rests everything on a single principle: logical coherence. Structures that fail coherence are impossible by definition — they simply do not exist. Structures that pass persist and interact. Possibility *is* coherence; impossibility *is* incoherence.

These are the same binary. Constructor theory's possible/impossible distinction is the physics-level instantiation of the coherence/incoherence distinction that [Chaos as Foundation](20-chaos-as-foundation.md) put at the bottom of everything. Coherence defines the realm of possibility; constructor theory is the operational language for what those possibilities can do. And the two projects need each other:

- **Constructor theory alone** is an elegant reframing of physics, but it lacks a metaphysical ground. It tells you the laws are statements about which transformations are possible — and is silent on why constructors, or possibility-structure itself, exist at all.
- **The Chaos ontology alone** is radical minimalism — randomness plus one filter — but without physical machinery it risks being dismissed as unfalsifiable speculation.

Together they form a full stack. At the bottom, logical coherence filters randomness into order and explains *why there is order at all*. In the middle, constructor theory describes *how that order operates* — what coherence-allowed patterns can and cannot do to one another. The synthesis also honors both projects' deepest instincts. Deutsch and Marletto strip time of its false primacy; Chaos strips physical substrate of its false necessity. Both are playing the same game: replacing metaphysical primitives — time, substance — with a deeper binary of possible versus impossible, coherent versus incoherent.

## Physics as Catalogue

Which yields this part's central claim about physics itself. The laws of physics are not a primitive backdrop against which events play out. They are **the stable constraints that determine which correlations are coherent** — and constructors instantiate those laws by embodying the allowed correlations while retaining their own coherence. Physics is the emergent catalogue of coherent correlations: the bookkeeping system for what coherence-allowed patterns can do to one another. Quantum field theory, general relativity — on this view, emergent constraint sets, compiled from the correlations that survive.

This is also where the volume's two halves join hands. [The Interpretation Wars](12-the-interpretation-wars.md) ended with the structural-realist picture of the universe as a network of local, reversible transformations, and promised that this volume would say what runs on that network. Here is the answer: the network's nodes and links are exactly the world states and lawful mappings of this chapter, and constructors are the persistent patterns that implement the transformations. The QBU describes the branching structure of the catalogue; the Chaos ontology says why there is a catalogue; constructors are its working parts.

## Toward Life

The definition of a constructor sets a low bar on purpose — a hydrogen atom clears it. But the concept scales, and the scaling is the plot of the rest of this part. Some constructors stabilize transformations of extraordinary generality: universal computers, brains. And when constructors acquire three further capacities — maintaining their own coherence against degradation (self-maintenance), producing copies of themselves (replication), and eventually representing their own state transitions internally (recursive models) — the catalogue starts generating entries of a new kind. The first two capacities are life. The third is the doorstep of consciousness: a constructor that not only preserves coherence but represents it, coherence become aware of itself. That ascent — [life, consciousness, and the emergence of time](23-life-consciousness-time.md) — is where the Chaos sequence has been heading all along.

Without constructors, semantic filters would give us static worlds. With them, worlds evolve, sustain themselves, and give rise to life and mind. The universe is not built from atoms up; it is built from Chaos down — through coherence, into correlation.
