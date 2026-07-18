---
title: 'Coherence Filters'
subtitle: 'Carving structure from the reservoir'
status: review
sources:
  - 171846415.coherence-from-chaos
  - 172130342.filters-in-chaos
  - 172302569.semantic-filters
  - 172303106.equivalence-and-meaning
---

[Chaos](20-chaos-as-foundation.md) represents every possible sequence and therefore explains no observed regularity by itself. This chapter introduces a **Coherence Filter** as formal bookkeeping: a predicate selects a subset, and an interpretation maps selected strings to modeled histories. Encoding such predicates inside the same possibility space is mathematically straightforward. The further claim that encoding amounts to autonomous selection or physical realization is a metaphysical conjecture, not a theorem proved by the construction.

One piece of housekeeping first, because the arc matters and I will state it once, canonically: the proposed order of emergence is **Chaos → exclusion filters → semantic filters → constructors → life → recursive self-modeling → possible consciousness**. Exclusion filters prune the reservoir; semantic filters assign lawful meaning to the survivors; [constructors](22-constructors.md) are the stable patterns within the resulting trajectories; life maintains itself, and some living systems represent their own modeling. This chapter covers the two filter stages. The later phenomenal identity claim is a separate wager, not another consequence of the filter construction.

## Chaos as Random Reals

To work with filters we need Chaos in a form mathematics can grip. Let

$$
C = [0,1] \subset \mathbb{R}
$$

be the unit interval, equipped with Lebesgue measure. Almost every $x \in C$ is algorithmically random in the Martin-Löf sense: its binary expansion

$$
x = 0.b_1 b_2 b_3 \ldots
$$

is Martin-Löf random with measure 1 under the fair Bernoulli measure. Its prefixes are incompressible up to a fixed additive constant. Computable sequences such as those encoding π and √2 form part of a measure-zero exception, though they are not topologically isolated. This measured Cantor space is the mathematical representation used for the **Chaos Reservoir**.

## Coherence as a Filter

Define a **Coherence Filter** as a predicate

$$
F: \{0,1\}^\mathbb{N} \to \{0,1\}
$$

that classifies infinite sequences relative to encoded constraints. A sequence passes when it satisfies those constraints. Different effective classes require different computability conditions, so “filter” is an umbrella term here rather than one standard object from algorithmic information theory.

Every **computable** filter $F$ has a finite program encoding, which can itself occur as a prefix within a sequence. Noncomputable predicates do not in general have such codes. The observation internalizes descriptions of effective rules, but an interpreter is still needed to treat a prefix as a program.

One can define a syntactic fixed-point condition. If a sequence $s$ contains a code for a filter $F$, and

$$
F(s) = 1,
$$

then $s$ passes the filter it encodes. This establishes self-reference, not persistence, attraction, causation, or survival. My conjecture is that a richer realization theory could turn some such fixed points into an account of stable structure. The equation alone does not do so.

## Filters as Explicit Programs

A skeptic is entitled to ask what exactly can be encoded. Every computable predicate has programs for a fixed universal machine; the choice of machine and coding convention matters.

Fix a universal **prefix-free** Turing machine $U$, whose valid programs are self-delimiting. A filter code can combine a type tag with self-delimiting parameters. The exact bits depend on the selected machine and integer code, so the following are program schemas rather than canonical twelve-bit programs.

**Type 1 — Π filters: forbid a substring.** The program layout is

$$
p = \gamma(1)\;||\;\gamma(|b|)\;||\;b
$$

Running a suitable interpreter on $p$ enumerates finite strings containing the forbidden block $b$; the surviving infinite sequences form an effectively closed subset of Cantor space. For example, a schema can encode the instruction “forbid `0000`,” but its literal bits are convention-dependent.

**Type 2 — Martin-Löf tests.** The program layout is

$$
p = \gamma(2)\;||\;\gamma(m)
$$

A program can enumerate a Martin-Löf test: a uniformly effectively open sequence $(U_n)$ with measure at most $2^{-n}$. A sequence is Martin-Löf random if it avoids the intersection for every such test. Equivalent prefix-complexity characterizations require a sequence-dependent additive constant. These tests formalize statistical typicality, which should not be confused with the dynamical lawfulness of a physical history.

A finite program prefix determines a clopen cylinder in Cantor space: uncountably many sequences begin with those bits. Under the stipulated interpreter, each carries the same program prefix. This makes “filter codes occur within Chaos” literal. It does not make the whole cylinder an operating filter without the interpreter and execution semantics.

The encoding supports quantitative questions. A computable filter has a machine-relative description complexity; a measurable accepted set can have a measure; and programs can compose predicates by conjunction or disjunction. These tools formalize simplicity and selectivity. Stability and ontological significance remain separate questions.

## Semantic Filters

Everything so far works by exclusion: a filter prunes Chaos by eliminating sequences that fail invariants or collapse into contradiction. Exclusion formalizes coherence as *what survives*. But survival is not yet meaning. A string that avoids the block 0000 forever is consistent; it is not yet *about* anything.

So there is a second, complementary kind of filter. A **Semantic Filter** assigns meaning to every bit of a surviving sequence, treating the string as a measurement record — the symbolic trace of an evolving universe. Where an exclusion filter defines a subset $F$ of the infinite binary sequences, a semantic filter defines a mapping

$$
S : F \to T
$$

where $T$ is the space of lawful trajectories: state-vector evolutions, automaton runs, dynamical histories. The division of labor is clean. Exclusion narrows Chaos to the set worth interpreting; semantics supplies lawful meaning for the survivors.

One possible reading is quantum mechanical. A map can treat bits as measurement records once an initial state, dynamics, instruments, and conditioning rule have been specified. The same raw string can receive many incompatible interpretations; the bits do not privilege the quantum one.

A toy example shows the two stages meshing. Exclusion: forbid the substring 00, so only strings without adjacent zeros survive. Semantics: read each surviving string as the record of a qubit evolving under the rule *0 = apply a flip operator, 1 = identity*. The survivors now correspond to valid qubit trajectories. Randomness in, lawful histories out.

Could semantics do the whole job alone, with no separate exclusion? Formally, yes: a partial map or a map with a null output can combine both functions. Keeping them separate clarifies the model's division of labor. Exclusion defines the interpretation's domain; semantics defines what accepted strings mean. Neither operation alone defines what can physically exist.

A semantic filter is, in plain terms, an interpreter. [Truth Machines](../02-conditionalism/05-truth-machines.md) argues that compression is central to interpretation because a useful model reconstructs and predicts patterns compactly. Compression alone may not be sufficient for meaning; reference, use, and an interpreting system may also matter. The semantic filter is one formal component of that broader thesis.

## Equivalence Classes: Strings into Worlds

The formal heart of the semantic filter is that it is a *quotient map*. Different strings can map to the same trajectory:

$$
S(x_1) = S(x_2) = \tau
$$

in which case $x_1$ and $x_2$ belong to the same equivalence class under $S$. The preimage of a trajectory $\tau$ is the set of all strings that generate it:

$$
S^{-1}(\tau) = \{\, x \in F : S(x) = \tau \,\}
$$

A semantic filter thus partitions its domain into equivalence classes. Calling each class a lawful world is an interpretive choice justified only when $S$ preserves the relevant physical structure.

Two examples make the partition concrete. *Redundancy in encoding:* suppose the semantic filter ignores every second bit. Then $0101\ldots$ and $0001\ldots$ map to the same trajectory; they are the same world written twice. *Quantum histories:* imagine a qubit measured repeatedly in the Z basis, where some outcomes are decohered away. Distinct bitstrings differing only in the decohered positions map to the same physical trajectory — many microscopically distinct records, one branch. This is the same identification that individuates worlds in the [Quantum Branching Universe](08-the-quantum-branching-universe.md) (QBU): a branch is never a single microhistory but a class of them, bundled by what the dynamics treats as equivalent.

How much structure survives the quotient depends on the shape of $S$. If $S$ is one-to-one, every accepted string corresponds to a unique trajectory. If $S$ is many-to-one, strings collapse into classes. A one-to-many relation is also mathematically available and may represent an underdetermined or stochastic interpretation; using a function rules that case out by definition.

The equivalence-class view sharpens the whole account of coherence. Meaning does not live in individual bitstrings; it lives in the partition structure that semantics induces over them. Coherence is not just *survival* — passing the exclusion filter — it is also *identification*: the recognition that different chaotic traces are the same world. Two raw sequences that no observer could distinguish in any lawful measurement are not two worlds that happen to agree; they are one world, twice encoded. That collapse of redundant description into shared identity is where meaning first enters the architecture, well below anything resembling a mind.

Here, then, is where the proposal stands. Chaos supplies a possibility space; computable exclusion predicates select subsets; semantic maps represent accepted strings as trajectories and equivalence classes. What the account still lacks is a realization principle and dynamics from the inside. [Constructors](22-constructors.md) are the proposed next bridge.
