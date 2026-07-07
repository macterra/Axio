---
title: 'Coherence Filters'
subtitle: 'Carving structure from the reservoir'
status: draft
sources:
  - 171846415.coherence-from-chaos
  - 172130342.filters-in-chaos
  - 172302569.semantic-filters
  - 172303106.equivalence-and-meaning
---

[Chaos](20-chaos-as-foundation.md) explains everything and therefore, so far, nothing. The reservoir of infinite randomness contains every possible sequence, which means it contains every structure, every law, every observer — and also every piece of noise, every contradiction, every history that dissolves into static after three steps. A ground that permits everything has not yet accounted for why we find *this*: a lawful, persistent, interpretable world. Something has to select. This chapter is about the selector. I call it a **Coherence Filter**, and the central claim is that it needs no outside agency to wield it: every filter is itself a pattern in Chaos, so coherence is self-selecting. The claim can be made mathematically exact, down to explicit twelve-bit programs, and that is what I intend to do.

One piece of housekeeping first, because the arc matters and I will state it once, canonically: the order of emergence is **Chaos → exclusion filters → semantic filters → constructors → life → consciousness**. Exclusion filters prune the reservoir; semantic filters assign lawful meaning to the survivors; [constructors](22-constructors.md) are the stable patterns within the resulting trajectories; life and consciousness are constructors that maintain and represent themselves. This chapter covers the two filter stages. The rest of the arc follows in the next two chapters.

## Chaos as Random Reals

To work with filters we need Chaos in a form mathematics can grip. Let

$$
C = [0,1] \subset \mathbb{R}
$$

be the unit interval, equipped with Lebesgue measure. Almost every $x \in C$ is algorithmically random in the Martin-Löf sense: its binary expansion

$$
x = 0.b_1 b_2 b_3 \ldots
$$

is an incompressible sequence, admitting no algorithmic description shorter than itself. The set of such reals has measure 1; the computable and compressible reals — π, √2, everything nameable — form a measure-zero exception. This is the **Chaos Reservoir**: the measure-theoretic ocean of incompressible bitstrings, with the orderly numbers scattered through it as isolated points of no weight at all.

## Coherence as a Filter

Define a **Coherence Filter** as a predicate

$$
F: \{0,1\}^\mathbb{N} \to \{0,1\}
$$

that selects subsequences of Chaos as self-consistent. A sequence passes the filter if it does not contradict the internal rules that $F$ encodes. In algorithmic information terms: a filter corresponds to a recursively enumerable set of constraints, a bitstring is coherent if it satisfies all of them, and each filter carves out an island of order — sequences that are not merely random but structured according to internal consistency.

So far this looks like the old move of imposing form on matter from outside, with the filter playing the role of the demiurge. The next observation dissolves that picture. Every filter $F$ is itself describable as a bitstring — hence as a real number, hence as a point *within* Chaos. The reservoir contains not just the random sequences but also the encodings of every possible rule for distinguishing order from disorder, and the encodings of every rule about which rules persist. Filters are patterns in Chaos; structures are patterns selected by filters; meta-filters are patterns too. The loop closes with nothing left outside it.

The apparent regress — filters needing filters needing filters — stabilizes in a fixed point. A pattern persists if it encodes a filter that selects itself: if $s \in \{0,1\}^\mathbb{N}$ encodes a filter $F$, and

$$
F(s) = 1,
$$

then $s$ is self-coherent. These fixed points of the filter relation are the stable attractors in Chaos — the self-consistent subpatterns that survive by recognizing their own coherence. That is my proposed answer to where long-lived structure comes from: not imposed, not chosen by anything prior, but the residue of a self-selection that Chaos performs on itself. Physics, mathematics, and observers are what the fixed points look like from inside.

## Filters as Explicit Programs

A skeptic is entitled to ask whether "every filter is a pattern in Chaos" is a metaphor or a theorem. It is a theorem, and the encodings can be written out bit by bit.

Fix a universal **prefix-free** Turing machine $U$ — one whose valid programs form a prefix-free set, so that no program is an initial segment of another. Encode all integers with **Elias gamma** coding, which is itself prefix-free. A filter code is then a concatenation of self-delimiting fields: a 2-bit type tag telling $U$ which semantics to apply, followed by the filter's parameters, with any raw bitstring preceded by its gamma-encoded length. Two types suffice to illustrate.

**Type 1 — Π filters: forbid a substring.** The program layout is

$$
p = \gamma(1)\;||\;\gamma(|b|)\;||\;b
$$

Running $U(p)$ enumerates all finite strings containing the forbidden block $b$; the filter $F_b$ is the set of infinite sequences in which $b$ never occurs. Concretely, to forbid $b = 0000$: $\gamma(1) = 10$ and $\gamma(4) = 111000$, so the program is the twelve bits `101110000000`. This yields an effectively closed subset of Cantor space.

**Type 2 — Martin-Löf tests.** The program layout is

$$
p = \gamma(2)\;||\;\gamma(m)
$$

Running $U(p)$ enumerates a Martin-Löf test $(U_n)$: for each $n$ it lists the compressible strings of length $n$, those with program length below $n - m$. The filter $F(m)$ is the set of sequences that pass the test — that do not fall in infinitely many $U_n$ — which enforces a complexity bound on every prefix. Concretely, for $m = 10$: $\gamma(2) = 1100$ and $\gamma(10) = 11110010$, giving the twelve bits `110011110010`. Where a Π filter forbids a specific pattern, an ML filter imposes a randomness-style typicality constraint: it excludes sequences that are *too* orderly to be honest samples of Chaos, which is exactly the kind of statistical lawfulness a physical history exhibits.

Now the payoff. Because the encoding is prefix-free, each finite program corresponds to a *clopen cylinder* in Cantor space: the set of all infinite sequences beginning with that program's bits. Every real in the interval $[0.101110000000,\; 0.101110000000 + 2^{-12})$ — an uncountable set — encodes the filter "no 0000." The filter is not a description hovering above the reservoir; it is a region of the reservoir, occupied by uncountably many of its points. "Filters are patterns in Chaos" is thereby literal.

The encoding also makes filters quantitative objects. Each filter has a complexity, $K(F)$, the length of its shortest code. Each has a selectivity: the Lebesgue measure of what survives a Π filter, or the parameter $m$ of an ML test. And filters compose — conjunction by concatenating codes and running both recognizers, disjunction by accepting on either — so the space of filters has an algebra, and questions about which coherence conditions are simple, strict, or stable become questions in algorithmic information theory rather than metaphysics.

## Semantic Filters

Everything so far works by exclusion: a filter prunes Chaos by eliminating sequences that fail invariants or collapse into contradiction. Exclusion formalizes coherence as *what survives*. But survival is not yet meaning. A string that avoids the block 0000 forever is consistent; it is not yet *about* anything.

So there is a second, complementary kind of filter. A **Semantic Filter** assigns meaning to every bit of a surviving sequence, treating the string as a measurement record — the symbolic trace of an evolving universe. Where an exclusion filter defines a subset $F$ of the infinite binary sequences, a semantic filter defines a mapping

$$
S : F \to T
$$

where $T$ is the space of lawful trajectories: state-vector evolutions, automaton runs, dynamical histories. The division of labor is clean. Exclusion narrows Chaos to the set worth interpreting; semantics supplies lawful meaning for the survivors.

The natural reading of the bits is quantum mechanical. Take each bit to be the outcome of measuring some observable; the semantic filter specifies the initial state and the measurement operators; the string then corresponds to a trajectory $|\psi_0\rangle \to |\psi_1\rangle \to |\psi_2\rangle \to \ldots$, updated step by step by the outcomes. Under a semantic filter, coherence is no longer mere absence of contradiction — it is *lawful continuation under dynamics*.

A toy example shows the two stages meshing. Exclusion: forbid the substring 00, so only strings without adjacent zeros survive. Semantics: read each surviving string as the record of a qubit evolving under the rule *0 = apply a flip operator, 1 = identity*. The survivors now correspond to valid qubit trajectories. Randomness in, lawful histories out.

Could semantics do the whole job alone, with no exclusion at all? No — and the failure mode is instructive. If the exclusion filter excludes nothing, the semantic filter must map *every* random string into some trajectory, pathological ones included, and in practice the semantics would quietly reintroduce exclusion by sending incoherent strings to trivial or null histories. Exclusion is not dispensable scaffolding; it is what lets semantics be a theory of meaning rather than a theory of everything. Exclusion defines what can exist; semantics defines what the survivors mean.

A semantic filter is, in plain terms, an interpreter — and this is where the present story meets the epistemology. I argue in [Truth Machines](../02-conditionalism/05-truth-machines.md) that interpretation *is* compression: meaning arises exactly when a pattern admits a compact interpreter that reconstructs it predictively, and incompressible patterns resist interpretation altogether. The semantic filter is that thesis running at the ontological ground floor. A finite program $S$, confronting the incompressible output of Chaos, extracts precisely the histories it can lawfully continue — and what it cannot compress, it cannot mean.

## Equivalence Classes: Strings into Worlds

The formal heart of the semantic filter is that it is a *quotient map*. Different strings can map to the same trajectory:

$$
S(x_1) = S(x_2) = \tau
$$

in which case $x_1$ and $x_2$ belong to the same equivalence class under $S$. The preimage of a trajectory $\tau$ is the set of all strings that generate it:

$$
S^{-1}(\tau) = \{\, x \in F : S(x) = \tau \,\}
$$

A semantic filter thus partitions the survivors $F$ into equivalence classes — and each class corresponds to one lawful world.

Two examples make the partition concrete. *Redundancy in encoding:* suppose the semantic filter ignores every second bit. Then $0101\ldots$ and $0001\ldots$ map to the same trajectory; they are the same world written twice. *Quantum histories:* imagine a qubit measured repeatedly in the Z basis, where some outcomes are decohered away. Distinct bitstrings differing only in the decohered positions map to the same physical trajectory — many microscopically distinct records, one branch. This is the same identification that individuates worlds in the [Quantum Branching Universe](08-the-quantum-branching-universe.md) (QBU): a branch is never a single microhistory but a class of them, bundled by what the dynamics treats as equivalent.

How much structure survives the quotient depends on the shape of $S$. If $S$ is one-to-one, every coherent string corresponds to a unique trajectory — the string *is* the trajectory. If $S$ is many-to-one, strings collapse into classes; detail is lost and only the quotient structure remains. One-to-many is the case to avoid: a single string corresponding to multiple worlds would abandon determinism at the semantic level, and every formalization worth having declines that trade.

The equivalence-class view sharpens the whole account of coherence. Meaning does not live in individual bitstrings; it lives in the partition structure that semantics induces over them. Coherence is not just *survival* — passing the exclusion filter — it is also *identification*: the recognition that different chaotic traces are the same world. Two raw sequences that no observer could distinguish in any lawful measurement are not two worlds that happen to agree; they are one world, twice encoded. That collapse of redundant description into shared identity is where meaning first enters the architecture, well below anything resembling a mind.

Here, then, is where the arc stands. Chaos supplies everything; exclusion filters — finite, self-delimiting, themselves resident in Chaos — prune it to the self-consistent; semantic filters map the survivors onto lawful trajectories and bundle them into equivalence classes, which are worlds. What the account still lacks is dynamics from the inside: patterns that do not merely persist within a trajectory but *act* — transforming other patterns while preserving their own coherence. Those are the [constructors](22-constructors.md), and they are where this architecture starts to become physics.
