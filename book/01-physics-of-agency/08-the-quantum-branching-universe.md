---
title: 'The Quantum Branching Universe'
subtitle: 'A formal map of parallel timelines'
status: draft
sources:
  - 162844036.the-quantum-branching-universe-qbu
  - 162845671.identifying-branches-in-the-qbu
---

Everett's move is easy to state. Take the Schrödinger equation literally, drop the collapse postulate, and accept what the mathematics has been saying all along: every quantum event splits reality, and every outcome with nonzero amplitude occurs — each in its own branch. The case that this is the right reading of quantum mechanics is the business of [The Interpretation Wars](12-the-interpretation-wars.md). This chapter's business is different: to say precisely what the picture *is*.

Because as usually told, it isn't precise. "Branch," "world," "timeline," "history" get used interchangeably and informally, even by physicists who take branching seriously. That looseness is tolerable for popularization and fatal for everything I want to do with the picture. The questions this volume runs on — what makes one event the cause of another, what a counterfactual claim is true *of*, what an agent is choosing between, whether the you in another timeline is you — are questions about the *structure* of the branching, and structure cannot be interrogated in a vocabulary that never fixes its referents. Probability was a suggestive muddle until Kolmogorov gave it a formal object with defined operations; branching-universe talk is at the same pre-formal stage, and it needs the same treatment. So here is the object. I call it the **Quantum Branching Universe**, or **QBU**, and the rest of this book leans on the definitions in this chapter.

## A Graph of Events

A **Quantum Branching Universe** is a structured representation of all physically possible quantum timelines, organized as a directed acyclic graph — a DAG. In this graph:

- **Nodes** represent quantum events or measurements.
- **Edges** represent branching due to quantum outcomes.
- **Paths** through the DAG represent distinct timelines.

Formally:

$$
\text{QBU} \equiv (V, E)
$$

where $V$ is the set of all quantum events and $E$ is the set of directed edges indicating temporal and causal ordering.

Each piece of the definition is doing work. The graph is *directed* because the edges carry the arrow of causal ordering: an edge runs from an event to the outcomes that follow from it, never back. It is *acyclic* because no timeline revisits an event; a history that looped through the same quantum event twice would not be a history. And the primitive objects are *events*, not worlds: a "world" or "timeline" is a derived notion, a maximal path through the graph, one complete way the universe's quantum events could have resolved from beginning to end. Two timelines that share a path up to some event and diverge afterward are, in the ordinary loose sense, "the same world until the split" — and the DAG makes that loose sense exact.

Ancestry falls out of the path structure. An **ancestor** event $E_a$ precedes another event $E_b$ if all timelines passing through $E_b$ necessarily pass through $E_a$. This is stronger than merely coming earlier: it says that $E_a$ is unavoidable history for anything downstream of $E_b$, part of the fixed past of every version of every observer at $E_b$. Ancestry, so defined, is what causal reasoning in a branching universe hangs on, and nearly everything in this chapter's second half is machinery for establishing it.

## An Ensemble of Block Universes

Before the machinery, the metaphysics — because the word "branching" invites a picture that is exactly wrong.

The classical **block universe** of relativity treats time as a static, four-dimensional structure in which past, present, and future coexist. Nothing flows; the block simply *is*, and what we call the passage of time is a feature of how observers embedded in the block experience their worldlines. The QBU does not reject this picture. It multiplies it. The QBU is an immense static structure composed of an astronomically vast — potentially infinite — number of distinct block universes, each a unique, deterministic timeline, related to one another by the branch structure of the DAG.

So branching is not something that *happens*. The tree does not grow; no fork is ever poised, waiting for an outcome to be decided. Branching is a structural relationship among timelines — the fact that two block universes are identical up to some quantum event and differ after it — in precisely the way that a road's fork is a fact about the map, not an occurrence on it. Every alternative outcome is equally real, a coexisting timeline, and ours enjoys no privileged status beyond being the one we find ourselves in. This is what makes the QBU fit for rigorous work on causality, counterfactual reasoning, and choice: the alternatives that counterfactuals gesture at are not fictions or abstract possibilia but actual, explicitly modeled timelines elsewhere in the structure. What that buys for the semantics of "would have" is the subject of [Causality and Counterfactuals](10-causality-and-counterfactuals.md).

## Pattern Identifiers

A map of every physically possible timeline is useless without a way to point at parts of it. "The timelines where I exist," "the timelines where the coin landed heads," "the timelines descending from my birth" — every interesting claim about the QBU quantifies over some subset of its paths, and the subset had better be well defined.

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
AncestorDescendant(PI_a, PI_b) = \begin{cases} True, & \text{if for all timelines containing } PI_b, \text{ there exists an ancestor timeline containing } PI_a \\ False, & \text{otherwise} \end{cases}
$$

When $AncestorDescendant$ returns $True$, the pattern $PI_a$ is fixed history for every instance of $PI_b$ anywhere in the QBU — the pattern-level analogue of an unavoidable ancestor event. That is a strong guarantee, and not every identifier can deliver it.

## Strong and Weak Identifiers

Pattern Identifiers divide into two kinds, and the division is where most careless reasoning about parallel selves goes wrong.

A **Strong PI** is a pattern whose matching timelines necessarily share a common ancestor event. Select the worlds, and you have selected a family: every one of them descends from a single node in the DAG, and everything downstream of that node inherits it as fixed past. Strong PIs provide strict causal clarity.

The canonical example is a **genotype**. A genotype uniquely identifies an individual at the biological level, and it is the product of a precise sequence of ancestral genetic events. Every timeline containing my exact genotype necessarily contains the event of my genetic formation — that specific fertilization, that specific recombination. It could not be otherwise: the pattern is so informationally particular that independent origination elsewhere in the structure has no purchase. So $SelectWorlds(\text{my genotype})$ returns a set of timelines with a guaranteed common ancestor, and every causal question about "the versions of me" is anchored to a definite node. This is what makes Strong PIs the working currency of rigorous investigation into causality and agency within the QBU. Neural connectomes and specific quantum states earn the same status the same way: by being precise enough that matching entails shared origin.

A **Weak PI** is a pattern that carries no such guarantee. The canonical example is a **name**. A name is a culturally assigned label with no biological or causal constraint behind it; the same name arises independently in completely separate causal histories. $SelectWorlds(\text{"David"})$ returns a sprawl of timelines containing entirely unrelated individuals who happen to share a label — no common ancestor event, no shared causal root, no fact of the matter about "what happened to David across the branches," because the selection never picked out a single lineage in the first place. Weak PIs are not useless — for cultural and historical analysis, patterns like names, labels, and general event-descriptions are exactly the right grain — but they cannot support causal claims, and arguments that quietly treat a Weak PI as if it were Strong are trading on an ambiguity.

There is also a degenerate limit worth marking. Logical invariants — the value of π, the theorems of arithmetic — are patterns that match *every* timeline. They are universally true and therefore trivially differentiating: $SelectWorlds$ returns the whole QBU, which selects nothing. Universality makes an identifier operationally worthless, not maximally reliable. The useful PIs live between the two failure modes: particular enough to entail a shared origin, contingent enough to distinguish some timelines from others.

The payoff of the distinction is discipline. When later chapters analyze a decision — an agent standing at a branch point, weighing futures — the agent is picked out by Strong PIs, so that "the branches where I do X" and "the branches where I do Y" are genuinely branches *of the same trunk*, downstream of a common ancestor, and comparing them is a well-posed causal comparison rather than a survey of strangers.

## The Unweighted Skeleton

What this chapter has built is deliberately austere: a graph, an ancestry relation, and a selection calculus. Nothing yet says that some branches count for more than others. But they do — branches carry an objective weight, fixed by the squared amplitudes of the wavefunction, and that weight is **Measure**, the physical quantity that turns the QBU from a map of what is possible into an account of what is probable. Adding Measure to the skeleton, together with the observer-relative notions of Vantage and Branchcone, is the work of [the next chapter](09-measure-vantage-branchcone.md). And once Measure is in place as a fact about the world, there is a matching question about the head — how an agent's subjective confidence should track objective branch weight — which is the epistemology of [Measure and Credence](../02-conditionalism/11-measure-and-credence.md).

The QBU framework draws on standing work: the many-worlds interpretation of quantum mechanics (Everett, 1957); the block universe reading of relativity (Putnam, 1967); causality and counterfactuals in quantum theory (Pearl, 2000; Deutsch, 1999); the formal structures of quantum mechanics and quantum computation (Nielsen & Chuang, 2010); and quantum causality (Adlam, 2021).
