---
title: 'Schemas and Groups'
subtitle: 'A formal model of culture'
status: review
sources:
  - 166080146.understanding-culture
  - 166409545.culture-hierarchies
---

Listen to any argument about culture and you will hear one word doing two jobs. "Christian culture shaped Europe" — is that a claim about a body of ideas or about a population of people? "Immigrants should adopt our culture" — adopt what, exactly: a set of beliefs, or membership in a group? "Western culture is in decline" — are the ideas losing coherence, or are the people who hold them losing numbers? The disputants slide between the two readings, often within a single sentence, and the slide is not harmless. It lets someone defend a set of ideas by pointing to the virtues of a population, or condemn a population by pointing to the vices of a set of ideas. Most of what passes for disagreement about culture is two people equivocating in opposite directions.

The fix is to split the word. "Culture" denotes two distinct objects, and once they are named separately, a surprising amount of structure falls out for free.

## Two Objects, One Word

A **Cultural Schema** is an abstract collection of beliefs, values, preferences, and norms. It is the conceptual blueprint of a culture, independent of any particular individuals or communities: what the culture believes, values, and prioritizes, as an intangible but coherent structure. Formally, a schema is just a set:

$$S_k = \{ b_1, b_2, \dots, b_m \}$$

where each $b$ is a belief or value held within the schema. (What a belief *is* — not a sentence stored in a head but a feature of a model of an agent — is settled in [What Beliefs Are](../02-conditionalism/08-what-beliefs-are.md); this chapter takes that ontology as given and builds on top of it. The set notation is an idealization in exactly the way all agent-modeling is, and it earns its keep the same way: by what it lets us predict.)

A **Cultural Group** is the concrete set of agents — individuals, communities, populations — who instantiate a particular schema: real people whose belief systems contain it. Formally:

$$G(S_k) = \{ a_i \mid S_k \subseteq B(a_i) \}$$

where $B(a)$ is the belief system of agent $a$. The group of a schema is everyone whose beliefs include all of it.

Schemas are abstract; groups are tangible. Schemas are made of beliefs; groups are made of people. A schema can exist with an empty group — every extinct religion is a schema whose group has died out from under it — and a group can outlive large revisions of its schema. Keeping the two apart is the whole trick, and the function $G$ is the bridge between them: it maps each blueprint to its current population of instances.

## A Toy Culture

The machinery is easiest to see at miniature scale. Take three agents:

- $a_1$ with beliefs $\{x, y, z\}$
- $a_2$ with beliefs $\{x, y\}$
- $a_3$ with beliefs $\{x, z\}$

Define two schemas: $S_1 = \{x, y\}$ and $S_2 = \{x\}$. Then $G(S_1) = \{a_1, a_2\}$ — the agents whose belief systems contain both $x$ and $y$ — while $G(S_2) = \{a_1, a_2, a_3\}$: everyone, since everyone holds $x$.

Notice what just happened. The *larger* schema, $S_1$, picked out the *smaller* group. Adding a belief to a schema adds a requirement for membership, and every added requirement can only shrink the pool of agents who satisfy all of them. Demanding schemas have exclusive groups; permissive schemas have inclusive ones. In general, if $S_j \subseteq S_k$ — if one schema is contained in another — then:

$$G(S_k) \subseteq G(S_j)$$

The subset relation *inverts* on its way from schema-space to group-space. This inverse relationship is the model's crucial and elegant property, and it is worth pausing on, because it runs against the grain of ordinary speech. We say Catholicism is "part of" Christianity, meaning the Catholics are among the Christians — a group-space statement. But in schema-space the containment points the other way: the Catholic schema *contains* the Christian schema and adds to it. The big tent is the small set. Whenever culture-talk feels paradoxical, the first thing to check is whether a schema-space claim is being read in group-space or vice versa.

## Schemas Within Schemas

Cultures do not exist in isolation; they form hierarchies, where broader schemas encompass multiple narrower ones. The formalism does not need this added as an extra assumption — hierarchy emerges from set intersection.

Take the obvious case. Let the Catholic and Protestant schemas be:

- $S_{\text{Catholic}} = \{x, y, z\}$
- $S_{\text{Protestant}} = \{x, y, w\}$

where $x$ and $y$ are the shared core — the divinity of Christ, the authority of scripture — while $z$ and $w$ are the distinctives: papal authority on one side, *sola fide* on the other. The two schemas share $\{x, y\}$, and that intersection is itself a schema — the Christian schema:

$$S_{\text{Christian}} = \{x, y\}$$

The parent is not something over and above its children; it is literally their common part. And because it is the smaller set, the inversion delivers the hierarchy in both spaces at once. In schema-space:

$$S_{\text{Christian}} \subseteq S_{\text{Catholic}} \quad \text{and} \quad S_{\text{Christian}} \subseteq S_{\text{Protestant}}$$

Therefore, in group-space:

$$G(S_{\text{Catholic}}) \subseteq G(S_{\text{Christian}}), \quad G(S_{\text{Protestant}}) \subseteq G(S_{\text{Christian}})$$

Picture the group-space version as nested circles: one large circle, $G(S_{\text{Christian}})$, containing everyone who holds the shared core $\{x, y\}$; inside it, two smaller regions — $G(S_{\text{Catholic}})$, those who also hold $z$, and $G(S_{\text{Protestant}})$, those who also hold $w$ — overlapping only in the odd agent who holds both distinctives at once. Every Catholic is a Christian; not every Christian is a Catholic; and the reason is nothing deeper than set inclusion running through the function $G$.

The construction iterates in both directions. Intersect the Christian schema with the Jewish and Muslim schemas and you get an Abrahamic schema — smaller still, with a correspondingly larger group. Add distinctives to the Catholic schema — the Jesuit charism, say — and you get a child schema with a smaller group inside the Catholic circle. The result is a lattice: every pair of schemas has a common parent (their intersection) and a common child (their union, whose group is the possibly-empty set of agents holding everything in both). "World culture," if the phrase means anything, names a schema near the top of the lattice — the few beliefs and norms held nearly universally — and its group is correspondingly nearly everyone. The most demanding sects and tightest subcultures live near the bottom: enormous schemas, tiny groups.

## What the Lattice Buys

A formalism is worth its notation only if it clarifies things that were murky without it. This one pays for itself three times over.

**Cultural transmission** becomes belief-flow along the hierarchy. Beliefs propagate from broader to narrower schemas: a child raised in the Christian core acquires $\{x, y\}$ before acquiring a denomination's distinctives, and a convert typically enters through the parent schema before settling into a child. The path of least resistance for a new belief runs through the schemas whose groups already contain its potential hosts.

**Cultural divergence** is a split in schema-space. A group whose members begin holding differing supersets of a shared schema is one dispute away from schism: the moment the difference is named and made criterial — you must hold $z$; you must reject $z$ — one schema becomes two siblings, and the old schema is demoted to their parent. The Reformation, in this notation, is the appearance of $w$ and the promotion of $\{x, y\}$ from "the faith, entire" to "the common core of two rival faiths."

**Cultural convergence** is the mirror image: schemas merging through shared beliefs, ecumenism as the deliberate migration of criterial beliefs out of the distinctives and into the core.

And the hierarchy hands us the lever for conflict. When two cultural groups collide, the instinct is to negotiate at the level where they differ — the distinctives, precisely the beliefs each side is most committed to defending. The lattice says to look up instead: identify the shared higher-level schema, the parent whose group contains both parties. That schema is not a diplomatic fiction; it is a real set of beliefs that every member of both groups actually holds, and appeals grounded in it land on both sides as appeals to *their own* commitments. Reconciliation is easiest where the schemas already agree, and the intersection tells you exactly where that is. The same move explains why "we are all children of Abraham" is a standard opening in interfaith diplomacy, and why it so often works better than any argument about the distinctives ever could: it is an appeal to a parent schema whose group includes everyone at the table.

## The Special Case

I have been describing culture as if it sits still — sets frozen in place, agents whose belief systems hold long enough to be measured against a schema. That is a deliberate idealization, and this chapter comes first in the theory because of it: a lattice of sets is easy to hold in the mind, and the statics are worth mastering before the dynamics. But the reader should know that this is the still photograph, not the film.

The moving picture is the subject of [Patterns as Players](03-patterns-as-players.md), which generalizes everything here. A cultural schema is a pattern in that chapter's precise sense — a coherent configuration of information stable enough to exert influence — and a cultural group is that pattern's host population, the set of minds currently instantiating it. What the schema formalism captures is the *synchronic slice* of the pattern ecology: who hosts what, right now, and how the hosting relations nest. What it deliberately omits is that patterns are not inert sets waiting to be counted. They compete for hosts, mutate under transmission, and are filtered by incentive environments that reward persistence rather than truth. In the dynamic theory, $G(S_k)$ is not a roster; it is a population under selection pressure, and the schema itself is one of the players.

That reframing has consequences the static model cannot express. Nothing in set notation distinguishes a schema whose beliefs are independently held from one whose beliefs include *defenses* — beliefs whose function is to protect the other beliefs from revision and to punish exit from the group. Both are just sets of $b$'s. But in the ecology they behave utterly differently, and when the fusion of schema and group becomes tight enough — when the hosts begin to serve the pattern rather than the reverse — the appropriate vocabulary shifts from set theory to something older and darker, taken up in [The Egregoric Singularity](05-the-egregoric-singularity.md).

So take the formalism for what it is: the special case where culture holds still long enough to be diagrammed, and the scaffolding on which the rest of the volume's theory hangs. Splitting "culture" into schema and group dissolves the equivocations; the inverse relation explains why breadth of appeal trades off against depth of demand; the lattice locates every subculture, sect, and civilization in one structure and points to the shared parent whenever two of them fight. That is a great deal of work for two definitions and a subset relation — which is exactly what a good formalism looks like.
