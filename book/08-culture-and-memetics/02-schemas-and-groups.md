---
title: 'Schemas and Groups'
subtitle: 'A toy model of cultural membership'
status: review
sources:
  - 166080146.understanding-culture
  - 166409545.culture-hierarchies
---

Listen to any argument about culture and you will hear one word doing two jobs. "Christian culture shaped Europe" — is that a claim about a body of ideas or about a population of people? "Immigrants should adopt our culture" — adopt what, exactly: a set of beliefs, or membership in a group? "Western culture is in decline" — are the ideas losing coherence, or are the people who hold them losing numbers? The disputants slide between the two readings, often within a single sentence, and the slide is not harmless. It lets someone defend a set of ideas by pointing to the virtues of a population, or condemn a population by pointing to the vices of a set of ideas. Most of what passes for disagreement about culture is two people equivocating in opposite directions.

The fix is to split the word. "Culture" denotes two distinct objects, and once they are named separately, a surprising amount of structure falls out for free.

## Two Objects, One Word

A **Cultural Schema** is an analyst-specified collection of beliefs, values, preferences, practices, or norms used to model a culture. It is not what a culture literally believes: cultures do not necessarily form agents, their contents are contested, and people instantiate them partially and unevenly. For a deliberately crisp toy model, represent a schema as a set:

$$S_k = \{ b_1, b_2, \dots, b_m \}$$

where each $b$ is a modeled belief or value. (What a belief *is* — not a sentence stored in a head but a feature of a model of an agent — is settled in [What Beliefs Are](../02-conditionalism/08-what-beliefs-are.md). Here the set notation suppresses degrees of commitment, contradictions, practices, interpretation, and change. Its deductions are conditional on that idealization.)

A **schema-induced group** is the set of agents who satisfy a stated membership rule for that schema. Under the toy model's all-or-nothing rule:

$$G(S_k) = \{ a_i \mid S_k \subseteq B(a_i) \}$$

where $B(a)$ is the modeled belief system of agent $a$. Empirical applications will usually need a threshold, graded membership, observed practice, self-identification, or some combination. A historically identified community is not interchangeable with whichever set this formula produces.

Schemas are models; groups are collections of people. A recorded schema can have no current instances, and a historically continuous group can outlive large revisions of its schema. Without records or implementations, however, an alleged extinct schema is a reconstruction rather than a free-standing object. Keeping schema, population, and institution apart is the whole trick. The function $G$ is one possible bridge between the first two, not their identity.

## A Toy Culture

The machinery is easiest to see at miniature scale. Take three agents:

- $a_1$ with beliefs $\{x, y, z\}$
- $a_2$ with beliefs $\{x, y\}$
- $a_3$ with beliefs $\{x, z\}$

Define two schemas: $S_1 = \{x, y\}$ and $S_2 = \{x\}$. Then $G(S_1) = \{a_1, a_2\}$ — the agents whose belief systems contain both $x$ and $y$ — while $G(S_2) = \{a_1, a_2, a_3\}$: everyone, since everyone holds $x$.

Notice what just happened. The *larger* schema, $S_1$, picked out the *smaller* group. Adding a belief to a schema adds a requirement for membership, and every added requirement can only shrink the pool of agents who satisfy all of them. Demanding schemas have exclusive groups; permissive schemas have inclusive ones. In general, if $S_j \subseteq S_k$ — if one schema is contained in another — then:

$$G(S_k) \subseteq G(S_j)$$

Under these definitions, the subset relation *inverts* on its way from schema-space to induced group-space. This is a useful property of the model, not an empirical law about identity. We say Catholicism is “part of” Christianity, meaning Catholics are among Christians — a group-space statement. In the toy schema-space, the Catholic schema contains the stipulated Christian core and adds to it. Whenever culture-talk feels paradoxical, check whether a schema claim, population claim, institutional claim, or self-identification is being read as another.

## Schemas Within Schemas

Analysts often arrange schemas into hierarchies, where a stipulated core is shared by more demanding variants. In the toy model, intersections and unions generate a lattice. Whether its nodes correspond to meaningful cultural identities is an empirical and interpretive question, not something set algebra decides.

Take the obvious case. Let the Catholic and Protestant schemas be:

- $S_{\text{Catholic}} = \{x, y, z\}$
- $S_{\text{Protestant}} = \{x, y, w\}$

where $x$ and $y$ are the shared core — the divinity of Christ, the authority of scripture — while $z$ and $w$ are the distinctives: papal authority on one side, *sola fide* on the other. The two schemas share $\{x, y\}$, and that intersection is itself a schema — the Christian schema:

$$S_{\text{Christian}} = \{x, y\}$$

In this representation, the parent is the features the analyst has encoded as common to its children. Because it is the smaller set, the inversion delivers a hierarchy in both modeled spaces. In schema-space:

$$S_{\text{Christian}} \subseteq S_{\text{Catholic}} \quad \text{and} \quad S_{\text{Christian}} \subseteq S_{\text{Protestant}}$$

Therefore, in group-space:

$$G(S_{\text{Catholic}}) \subseteq G(S_{\text{Christian}}), \quad G(S_{\text{Protestant}}) \subseteq G(S_{\text{Christian}})$$

Picture the group-space version as nested circles: one large circle, $G(S_{\text{Christian}})$, containing everyone who holds the shared core $\{x, y\}$; inside it, two smaller regions — $G(S_{\text{Catholic}})$, those who also hold $z$, and $G(S_{\text{Protestant}})$, those who also hold $w$ — overlapping only in the odd agent who holds both distinctives at once. Every Catholic is a Christian; not every Christian is a Catholic; and the reason is nothing deeper than set inclusion running through the function $G$.

The construction iterates in both directions. Intersections and unions exist mathematically for every pair of encoded schemas, but a nonempty intersection need not constitute a socially recognized parent, and a union need not describe a possible identity. “Abrahamic,” “Christian,” and “world culture” require historical and semantic arguments in addition to shared entries in a model. Within its limits, the lattice shows a genuine tradeoff: adding mandatory criteria cannot enlarge the population that satisfies all of them.

## What the Lattice Buys

A formalism is worth its notation only if it clarifies things that were murky without it. This one pays for itself three times over.

**Cultural transmission** can be recorded as movement between modeled memberships. Some learners acquire a broad vocabulary before denominational distinctives; others acquire a local practice first and only later learn an abstract parent identity. The lattice organizes observations but does not predict the direction of learning without a transmission mechanism.

**Cultural divergence** can be represented as a split in schema-space when a difference becomes criterial for membership. The Reformation can be schematized that way, but historical explanation still needs institutions, interests, media, doctrine, violence, and contingency that the notation omits.

**Cultural convergence** can be represented by removing or relaxing membership criteria, although shared action and institutional reconciliation need not follow from formal overlap.

The hierarchy also suggests a conflict heuristic: look for independently verified shared commitments rather than negotiating only at the point of difference. The formal intersection merely proposes candidates. It does not prove that every member endorses them, that the terms mean the same thing on both sides, or that common belief can settle a conflict driven by power or material interests. “We are all children of Abraham” may open an interfaith conversation; whether it lands is evidence, not algebra.

## The Special Case

I have been describing culture as if it sits still — sets frozen in place, agents whose belief systems hold long enough to be measured against a schema. That is a deliberate idealization, and this chapter comes first in the theory because of it: a lattice of sets is easy to hold in the mind, and the statics are worth mastering before the dynamics. But the reader should know that this is the still photograph, not the film.

The moving picture is the subject of [Patterns as Players](03-patterns-as-players.md). A cultural schema is one analyst-specified pattern type, and $G(S_k)$ is one modeled population of its current instances. The synchronic slice says who meets the criteria now and how those criteria nest. A dynamic account must separately specify copying, teaching, enforcement, deliberate revision, differential retention, and environmental change. Neither the schema nor the population automatically becomes an agent or player.

That reframing has consequences the static model cannot express. Nothing in set notation distinguishes independently supported beliefs from defenses that insulate other beliefs or punish exit. Both are just sets of $b$'s. In practice they behave differently because people and institutions enact different feedback mechanisms. [The Egregoric Singularity](05-the-egregoric-singularity.md) offers a vivid model of those distributed loops without turning a schema into a literal organism or mind.

So take the formalism for what it is: a toy case where culture holds still long enough to be diagrammed. Splitting schema, population, and institution blocks important equivocations; the inverse relation shows why adding mandatory criteria narrows an induced group; the lattice can propose shared commitments for investigation. Its cleanliness comes from what it omits, and every empirical use must put the omitted heterogeneity, history, and agency back in.
