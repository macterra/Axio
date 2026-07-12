---
title: 'The Quantum Branching Universe'
subtitle: 'A formal map of parallel timelines'
status: review
sources:
  - 162844036.the-quantum-branching-universe-qbu
  - 162845671.identifying-branches-in-the-qbu
---

Everett's move is easy to state. Take unitary quantum evolution seriously and do not add a collapse process the dynamics does not contain. Decoherence then produces effectively autonomous records that can be described as branches. The branches are emergent and approximate: the universal state does not come labeled with a unique set of worlds, and not every microscopic interaction defines one exact split. The case that this is the right reading of quantum mechanics is the business of [The Interpretation Wars](12-the-interpretation-wars.md). This chapter's business is to construct the coarse-grained representation the rest of this book uses.

“Branch,” “world,” “timeline,” and “history” are often used at several grains, even by physicists who take Everett seriously. The questions this volume runs on — causation, counterfactuals, choice, identity — require a declared grain. The **Quantum Branching Universe**, or **QBU**, is my modeling layer for that purpose. It is not a replacement for Hilbert-space quantum mechanics and not a claim that one exact graph is written into nature. It is a representation of decoherent histories at whatever coarse-graining makes the records relevant to the question stable. The rest of the book leans on that conditional object.

## A Graph of Events

A **Quantum Branching Universe** is a coarse-grained representation of decoherent quantum histories, organized as a directed acyclic graph — a DAG. Relative to a specified decomposition:

- **Nodes** represent stable event records at the chosen grain.
- **Edges** represent decoherent continuation between records.
- **Paths** represent histories distinguished by those records.

Formally:

$$
\text{QBU} \equiv (V, E)
$$

where $V$ is the selected set of event records and $E$ is the selected continuation relation. A complete physical model would also carry amplitudes, quantum states, and a decoherence functional; the bare graph is the book's causal skeleton.

The graph is *directed* because its edges encode record succession at this grain. It is *acyclic* because the same record occurrence does not become its own ancestor. The primitive objects are selected events, not worlds: a “world” or “timeline” is a derived path through the representation. Two paths may share records and later diverge. This makes the loose branching picture explicit once a coarse-graining has been fixed; it does not make the choice of coarse-graining unique.

Ancestry falls out of the path structure. An **ancestor** event $E_a$ precedes another event $E_b$ in a specified QBU if every represented history through $E_b$ also passes through $E_a$. This is stronger than merely coming earlier within the model. Whether the relation captures physical causation rather than record ancestry is a further argument taken up later.

## An Ensemble of Block Universes

Before the machinery, the metaphysics — because the word "branching" invites a picture that is exactly wrong.

The classical **block universe** reading of relativity treats time as a static, four-dimensional structure in which past, present, and future coexist. The QBU combines that picture with an Everettian state containing decoherent histories. It can be visualized as a static family of block-like paths related by the DAG. The visualization is useful, but the paths remain emergent descriptions of one quantum state, not a fundamental census of separately packaged classical universes.

On this static reading, branching is a structural relationship among histories rather than a tree growing into an external future. The records represented by different paths are components of the universal state; none is selected by collapse, and ours has no privileged dynamical status. This makes the QBU useful for causality, counterfactual reasoning, and choice while leaving open how much semantic work physical co-realization can carry. That question is the subject of [Causality and Counterfactuals](10-causality-and-counterfactuals.md).

## Pattern Identifiers

A map of represented histories is useless without a way to point at parts of it. “The histories where I exist,” “the histories where the coin landed heads,” “the histories descending from my birth” — every interesting claim about the QBU selects some subset of its paths, and the selection rule had better be explicit.

The pointing device is the **Pattern Identifier (PI)**: a precise, reproducible pattern or state used to identify and select subsets of timelines within the QBU. A genotype is a PI. A neural connectome is a PI. A specific quantum state is a PI. So, more loosely, is a name — and the difference between those examples is the crux of this chapter, but first the operations, which are common to all of them.

The primitive is the **Match** operation, which asks of a single timeline whether it contains the pattern:

$$
Match(PI, W) \rightarrow \{True, False\}
$$

From Match, selection over the whole structure is immediate. The **SelectWorlds** operation returns every timeline in which the pattern occurs:

$$
SelectWorlds(PI) = \{W \in QBU \mid Match(PI, W)\}
$$

This is the formal content of phrases like "the worlds where X": a pattern, and the set of paths that match it.

The third operation lifts ancestry from events to patterns. Given two PIs, it asks whether one is causally upstream of the other everywhere:

$$
AncestorDescendant(PI_a, PI_b) = \begin{cases} True, & \text{if every path matching } PI_b \text{ contains an earlier match of } PI_a \\ False, & \text{otherwise} \end{cases}
$$

When $AncestorDescendant$ returns $True$, $PI_a$ is represented as prior history for every selected instance of $PI_b$ in this QBU. That is a strong model-relative guarantee, and not every identifier can deliver it.

## Strong and Weak Identifiers

Pattern Identifiers divide into two kinds, and the division is where most careless reasoning about parallel selves goes wrong.

A **Strong PI** combines state constraints with provenance constraints strong enough that every match descends from a specified ancestor event. Select the histories, and you have selected a family by construction. A **Weak PI** matches descriptive features without guaranteeing that provenance. Precision alone does not create shared ancestry: two independent processes can instantiate the same description, however improbable the coincidence.

A genotype by itself is therefore not canonical proof of identity: identical twins already show that a sequence need not pick out one individual, and independent re-instantiation is conceptually possible. A strong identifier would instead specify something like *this genotype descending from this fertilization event*, or a later physical state together with a cryptographically or causally traceable history. Neural connectomes and quantum states face the same rule. Their descriptive detail may make accidental duplication negligible for practical work, but only provenance makes ancestry part of the identifier rather than a probabilistic inference.

A **Weak PI** carries no provenance guarantee. A name is the obvious example: $SelectWorlds(\text{"David"})$ returns unrelated individuals who share a label. Weak PIs are not useless — names, roles, genotypes, and general event descriptions can be the right grain for many questions — but they cannot support lineage claims without an added causal condition.

There is also a degenerate limit worth marking. Logical invariants — the value of π, the theorems of arithmetic — match every history under the relevant interpretation. $SelectWorlds$ then returns the whole represented QBU and distinguishes nothing. Useful PIs must state both what equivalence they track and, when identity or responsibility is at issue, what provenance they require.

The payoff is discipline. When later chapters analyze a decision, “the branches where I do X” and “the branches where I do Y” must be selected by an identifier anchored to the same pre-decision agent-state. The shared trunk comes from that declared provenance, not from resemblance alone.

## The Unweighted Skeleton

What this chapter has built is deliberately austere: a graph, an ancestry relation, and a selection calculus, all relative to a coarse-graining. Nothing yet says how much quantum weight belongs to the histories selected by a pattern. That weight is **Measure**, obtained from squared amplitudes over the relevant decoherent components. Adding Measure to the skeleton, together with Vantage and Branchcone, is the work of [the next chapter](09-measure-vantage-branchcone.md). The matching epistemic question — how an agent's subjective confidence should track objective quantum weight — belongs to [Measure and Credence](../02-conditionalism/11-measure-and-credence.md).

The QBU framework draws on standing work: the many-worlds interpretation of quantum mechanics (Everett, 1957); the block universe reading of relativity (Putnam, 1967); causality and counterfactuals in quantum theory (Pearl, 2000; Deutsch, 1999); the formal structures of quantum mechanics and quantum computation (Nielsen & Chuang, 2010); and quantum causality (Adlam, 2021).
