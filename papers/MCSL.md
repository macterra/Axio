# Measure-Conditioned Self-Location

## A Conditional Axionic Alternative to SSA and SIA

## Abstract

The Self-Sampling Assumption (SSA) and the Self-Indication Assumption (SIA) are the two dominant frameworks for anthropic reasoning, yet both rest on the same flawed primitive: observer-counting. SSA generates pathologies by treating the agent as a random sample from an arbitrary reference class; SIA corrects some of these but introduces its own by granting sheer population size unjustified epistemic force. This paper argues that the correct primitive is not observer-count but objective physical measure, and develops **Measure-Conditioned Self-Location (MCSL)**: a conditional rule under which self-locating credence tracks the total objective measure of admissible coherent realizations of the agent's present evidence state. MCSL requires three nested levels of evidential match — phenomenal, evidential, and admissible coherent — and restricts anthropic weighting to the strongest level, thereby blocking both SSA-style reference-class pathologies and crude SIA-style population favoritism. The framework is applied to five standard test cases: Lazy Adam, Sleeping Beauty, the Doomsday Argument, Presumptuous Philosopher, and Boltzmann brains. MCSL resolves the first-line failures of SSA without importing the excesses of SIA, while isolating the genuinely open problems — particularly the specification of the admissibility relation and the treatment of exact-duplicate presumptuousness — rather than concealing them. The proposal is situated within a broader Axionic ontology in which interpretation is conditional, truth is framework-relative, and coherence under transformation is the criterion for pattern identity.

## 1. Introduction

Anthropic reasoning remains unstable because its dominant formulations begin from the wrong primitive.

The **Self-Sampling Assumption** (SSA) instructs an agent to reason as though it were a random sample from some reference class of observers. That move generates familiar pathologies. In cases like Lazy Adam, a self-locating fact distorts an ordinary physical credence. A fair coin ceases to look fair because the agent treats itself as statistically atypical in the larger world. That is not a minor embarrassment. It is a category mistake.

The **Self-Indication Assumption** (SIA) reacts against this by favoring worlds with more observers. That blocks some SSA failures, including Lazy Adam and the standard Doomsday Argument. But SIA buys relief by granting raw numerosity prior epistemic force. In cases like Presumptuous Philosopher, that becomes pathological. A theory can gain support merely by predicting more observers. Population size starts doing explanatory work it has not earned.

Both views fail for the same underlying reason. Both treat **observer-counting** as basic. SSA samples from observer-slots. SIA rewards worlds that contain more of them. Neither begins from the right ontological currency.

Within an Axionic framework,^1 the correct primitive is **Measure**, not observer-count. Objective probability is physical measure. Credence is epistemic uncertainty. Self-location is uncertainty over where one is within a space of realized vantage-points. Once that is clear, the natural replacement for SSA and SIA is this:

> Under self-locating uncertainty, credence should track the total objective measure of admissible coherent realizations of one’s present evidence state.

That is the core idea of **Measure-Conditioned Self-Location** (MCSL).

This paper develops MCSL as a **conditional rule for self-location within an interpreted physical ontology**. That qualification matters. MCSL is not presented here as a complete first-person anthropic epistemology derivable from bare subjective experience alone. It is a rule for assigning self-locating credence **given** an admissible hypothesis space, a physical measure structure, and a principled account of which realizations count as admissible evidential vantages.

That narrower claim is still substantial. It is enough to show why SSA fails, why SIA overreaches, and why a measure-based alternative is better aligned with branch-structured ontology, conditional interpretation, and coherence-sensitive evidence.

The ambition of this paper is therefore disciplined rather than maximal. I do not claim that MCSL fully solves every anthropic puzzle. I claim something more precise:

1. observer-counting is the wrong primitive;
2. self-locating credence should be measure-weighted rather than count-weighted;
3. admissible evidential realizations must be distinguished from mere phenomenal or local counterfeit matches;
4. once this is done, MCSL appears to dominate SSA and SIA on the standard first-line cases, while isolating the real unresolved problems instead of hiding them.

That is already a significant improvement.

---

## 2. Why SSA and SIA Start in the Wrong Place

SSA begins by imagining a reference class and pretending the agent is uniformly sampled from it. That is not an explanation. It is a placeholder for missing ontology. Why this reference class rather than another? All humans? All observers? All observer-moments? All conscious beings? All exact copies? SSA never produces a principled answer. The arbitrariness is foundational.

This arbitrariness is not cosmetic. It drives the conclusions. In Lazy Adam, SSA says Adam should reason as though he were randomly sampled from all humans in the realized world. Since being Adam is vastly more typical in the tiny-population tails world than in the huge-population heads world, SSA drives credence sharply toward tails. Adam thereby becomes highly confident that a fair coin will almost certainly land tails. Any anthropic principle that yields that result is malformed.

SIA recognizes the failure and attempts to neutralize it by favoring worlds with more observers. That helps in Lazy Adam and in Doomsday-style cases. But it does so by giving global population size prior epistemic force. In Presumptuous Philosopher, this becomes absurd. A theory predicting more observers can swamp an equally well-supported rival merely by being more crowded. Numerosity once again does work it has not earned.

The common defect is deeper than either doctrine. Both presume that “how many observers there are” is the right basic object. It is not. In a branch-structured ontology, the correct object is **measure over realizations**, not count over observer-slots. And in a conditionalist epistemology, the relevant epistemic object is not observerhood in the abstract, but the agent’s present **evidence state** under which hypotheses are being evaluated.

The right question is therefore not:

> From which observer am I sampled?

Nor is it:

> Which world contains more observers?

It is:

> Across the admissible hypotheses, what is the total objective measure of admissible realizations of my present evidential vantage?

That is the shift MCSL makes.

---

## 3. Scope and Status of the Proposal

It is essential to state clearly what kind of theory MCSL is.

MCSL is **not** a universal anthropic solver that begins from bare first-person experience and derives a complete rational prior over all possible worlds. That project faces a severe problem immediately: an agent’s present local evidence does not obviously entitle it to filter candidate realizations by objective third-person coherence structure. If one ignores this, Boltzmann-brain-style objections immediately bite.

Instead, MCSL should be understood as a **conditional self-location rule** inside a prior physical and interpretive framework.

More precisely, MCSL presupposes:

1. an admissible hypothesis space $H$;
2. an objective measure structure $\mu$ defined within each hypothesis;
3. an evidence state $E$;
4. a principled admissibility criterion specifying which realizations count as admissible coherent instances of that evidential vantage.

Given those inputs, MCSL tells us how self-locating credence should be distributed.

This is not a retreat. It is the right level of ambition. In an Axionic setting, interpretation is always conditional. There is no view from nowhere. MCSL is therefore best understood not as an unconditional epistemology but as a rule for rational self-location **given** an interpreted ontology.

That clarification removes a major source of confusion. It also sharpens the Boltzmann-brain issue: the problem is no longer “How can I, from pure subjectivity, prove I am not a Boltzmann brain?” The problem becomes: “Which hypotheses assign admissible coherent measure to my present evidential vantage?” That is a better-posed question.

---

## 4. Formal Setting

Let $H = {H_1, \dots, H_n}$ be an admissible set of hypotheses.

Each hypothesis $H_i$ specifies a physically realized structure $W_i$: a space of histories, branches, world-trajectories, or other ontologically relevant realizations. Each $H_i$ also comes with an objective measure $\mu_i$ defined over the relevant realization space or over the vantage-events derived from it.

Let $E$ denote the agent’s present admissible evidence state. This is not merely a sensation-bitmap. It includes whatever information is admissibly available at the moment of evaluation: present experience, apparent memories, presently available inferential structure, awareness of experimental protocol where applicable, and currently accessible indexical information.

The problem is to assign credence to each $H_i$ conditional on $E$.

The naive temptation is to identify all realizations that “match” $E$ and then weight them by measure. But “match” is ambiguous. Only the strongest notion is adequate. So we first distinguish three nested levels.

---

## 5. Three Nested Levels of Match

### 5.1 Phenomenal Match

A realization $v$ is a **phenomenal match** to $E$ iff it matches the agent’s present experiential content narrowly construed.

Write:

$$
v \in P(E)
$$

This includes current sensations, internal seeming-state, apparent visual field, and any other content taken merely as present phenomenology.

Phenomenal match is too weak. A local counterfeit can satisfy it. A Boltzmann brain can satisfy it. Pure experiential similarity does not ground rational self-location.

### 5.2 Evidential Match

A realization $v$ is an **evidential match** to $E$ iff it matches the full present evidential state available to the agent.

Write:

$$
v \in \mathcal{E}(E)
$$

This is stronger. It includes apparent memories, inferential relations, apparent awareness of protocols, indexical structure, and all presently admissible evidential content.

But this is still not enough. A realization can locally mimic a full evidential state while lacking the structural support that makes that state count as evidence of a world at all.

### 5.3 Admissible Coherent Evidential Match

A realization $v$ is an **admissible coherent evidential match** to $E$ iff:

1. $v$ is an evidential match to $E$, and
2. $v$ instantiates the minimal structural conditions presupposed in treating $E$ as evidence of an ongoing world-model.

Write:

$$
v \in \mathcal{A}(E)
$$

Thus:

$$
\mathcal{A}(E) \subseteq \mathcal{E}(E) \subseteq P(E)
$$

Only $\mathcal{A}(E)$ is adequate for MCSL.

---

## 6. Why Admissibility and Coherence Are Required

Evidence is not a raw local pattern. It is an interpreted structure. A present seeming-state counts as evidence only under background conditions that make memory, persistence, inference, and world-modeling intelligible. This is already implicit in the broader Axionic commitments: interpretation is conditional, truth is framework-relative, and coherence matters.

A one-frame counterfeit can mimic an entire apparent evidence state while lacking the structural conditions that make that state evidentially usable. If anthropic credence treats such a counterfeit as epistemically equivalent to an ordinary embedded vantage, then pathological realizations can swamp the theory.

The solution is not to define away pathology by fiat. The solution is to distinguish between:

1. realizations that merely resemble the local apparent content of an evidence state, and
2. realizations that instantiate the minimal coherence-support conditions presupposed by using that state as evidence at all.

This is not a hidden return to SSA. SSA imposes an arbitrary reference class over which uniform sampling occurs. Admissibility in MCSL plays a different role. It is not a sampling class. It is a criterion for which realizations count as admissible instances of a given evidential vantage in the first place.

That said, the risk of arbitrariness is real. If admissibility is left vague, it can be abused. So MCSL does not escape difficulty by rhetorical relabeling. It must make admissibility explicit and constrained.

---

## 7. Admissibility Conditions

Let $E$ be the present evidence state and $v$ a candidate realization under hypothesis $H_i$.

We say that $v \in \mathcal{A}_i(E)$ iff the following conditions hold.

### 7.1 Evidential Equivalence

$v$ must be indistinguishable from $E$ with respect to all information admissibly available at the moment of evaluation.

Write:

$$
v \sim_E E
$$

This blocks appeals to hidden structure unavailable from the vantage itself.

### 7.2 Interpretive Support

There must exist a non-degenerate interpretive mapping $I$ under which the contents of $E$ function as evidence of a structured world-history in $v$.

This means the apparent content is not merely accidental noise that happens to resemble evidence.

### 7.3 Coherence Support

There must exist a coherence-support relation $K$ sufficient for the apparent diachronic and inferential structure encoded in $E$ to be more than a locally counterfeited pattern.

This does **not** require that the evidence be true, that the agent be non-deceived, or that the realization have a unique ancestry. It requires only that the realization instantiate enough structural support for the evidential state to count as an admissible vantage rather than a degenerate mimic.

Schematically:

$$
\mathcal{A}_i(E) = {v \in W_i : v \sim_E E \wedge I(v,E) \wedge K(v,E)}
$$

This remains schematic. It is not yet a finished theory of admissibility. But it is already more disciplined than either SSA or SIA.

---

## 8. MCSL

We can now state the principle.

> **Measure-Conditioned Self-Location (MCSL).**
> Let $H = {H_1,\dots,H_n}$ be an admissible set of hypotheses. Let each $H_i$ determine a realization structure with objective measure $\mu_i$. Let $E$ be the agent’s present admissible evidence state. Let $\mathcal{A}_i(E)$ be the set of admissible coherent evidential realizations of $E$ under $H_i$. Then the agent’s credence should satisfy
>
> $$
> C(H_i \mid E) = \frac{\mu_i(\mathcal{A}*i(E))}{\sum*{j=1}^{n} \mu_j(\mathcal{A}_j(E))}
> $$

This is the refined form of MCSL.

Not uniform sampling over a reference class.
Not prior weighting by global observer-count.
Not mere local similarity of experience.

The relevant quantity is the **objective measure of admissible coherent realizations of one’s present evidence state**.

One important limitation should already be noted. In its current linear form, this aggregation rule implies that if one hypothesis contains vastly more admissible coherent realizations of my exact present evidential vantage than another, it will be correspondingly favored. So future work may need to refine not only the admissibility relation, but also the **aggregation law over admissible realization-measure**.

---

## 9. Invariants

A viable anthropic principle should satisfy several non-negotiable constraints.

### 9.1 Physical Symmetry Preservation

If two hypotheses differ only by a fair physical chance process, and the present evidence does not discriminate between them, credence must preserve that symmetry.

A fair coin must remain fair unless the evidence genuinely bears on the coin.

### 9.2 Reference-Class Invariance

Credence must not depend on arbitrary population redescriptions such as “all humans,” “all mammals,” or “all observers born before year X,” unless those correspond to genuine evidential differences.

This is the anti-SSA invariant.

### 9.3 Population Non-Presumptuousness

A hypothesis must not gain credence merely by containing more observers *simpliciter*. Only increased admissible coherent measure of the agent’s present evidential vantage may matter.

This is the anti-crude-SIA invariant.

### 9.4 Self-Location / Physics Separation

Self-locating uncertainty may redistribute credence over admissible vantage-realizations, but must not distort ordinary physical uncertainty except via admissible coherent measure.

### 9.5 Everett Compatibility

In a branch-structured ontology, the rule must apply directly in terms of measure. It must not require flattening branching structure into observer-counting.

### 9.6 Admissibility Dependence

All MCSL outputs are conditional on a specified admissibility relation. Anthropics cannot be done without an evidential partition. MCSL makes that explicit rather than hiding it.

---

## 10. Measure in Everettian and Classical Contexts

The notion of objective measure is clearest in Everettian settings, where branch measure has an obvious physical role. But MCSL should not be restricted to Everett alone, and the notion of measure must therefore be handled carefully in classical cases.

In branch-structured theories, $\mu_i$ may be taken directly as branch measure or branch-derived weight over admissible vantage-events.

In classical stochastic cases, $\mu_i$ should be understood as the physically grounded probability measure induced by the relevant chance structure together with the realization structure of admissible vantage-events.

In purely classical duplication scenarios, multiplicity may sometimes collapse into counting as a derived special case. That is not a defect. What matters is that counting is not taken as primitive. It is admissible only when grounded in a prior physical symmetry or stochastic structure that makes the duplicate realizations measure-equal.

This distinction matters. MCSL does **not** claim that measure and count are always different. It claims that when count matters, it matters only as a derivative of physical structure, not as an autonomous anthropic primitive.

That is the key difference from both SSA and SIA.

---

## 11. Epistemic Access vs Ontological Admissibility

This is the most delicate issue in the theory.

An agent’s local evidence does not obviously entitle it to inspect the full ontological support structure of its realization. So one might object that coherence support is unusable: if a Boltzmann brain has the same apparent evidence as an ordinary observer, how can the agent justify privileging the ordinary observer’s realization?

The right response is that MCSL is **not** a rule for proving, from bare subjectivity alone, that one occupies a coherent realization. It is a rule for distributing credence across hypotheses **given** an interpreted hypothesis space in which admissibility is part of what the hypotheses say about the realization structure.

In other words, admissibility is not an extra fact the agent privately inspects from outside the theory. It is part of the interpretation of which realizations count as admissible instances of the evidential vantage under each hypothesis.

This is why MCSL is conditional rather than absolute. It is not a self-grounding epistemology from nowhere. It is a rule for rational self-location within a prior ontological and interpretive framework.

That does not eliminate the hard problem. It merely states it correctly. The unresolved question is not “How do I directly introspect coherence support?” The unresolved question is “What admissibility relation should a rational ontology assign to evidential vantages?” That is a much cleaner target.

---

## 12. Test Case: Lazy Adam

Adam and Eve are the first humans. They will flip a fair coin. If it lands heads, they reproduce and the eventual human population becomes enormous. If it lands tails, they do not reproduce and the total population remains two. Adam knows he is the first male human.

SSA says Adam should reason as though he were randomly sampled from all humans in the realized world. Since being Adam is much more typical in the tails world than in the heads world, SSA drives credence sharply toward tails. Adam thereby predicts that a fair coin will almost certainly land tails. This is absurd.

SIA avoids the absurdity by favoring the large-population world in advance, thereby canceling the anti-heads update. But it does so by population favoritism.

MCSL does better. Adam’s present evidence does not contain new physically discriminating information about the coin. Under a fair coin, the admissible coherent measure of his present evidential vantage is symmetric between heads and tails. Therefore:

$$
C(\text{Heads} \mid E) = C(\text{Tails} \mid E) = \frac{1}{2}
$$

This is the correct result, achieved without arbitrary observer-sampling and without blunt population weighting.

---

## 13. Test Case: Sleeping Beauty

Sleeping Beauty is awakened once if Heads and twice if Tails, with memory erasure between awakenings. Upon awakening, she asks for the probability of Heads.

Under MCSL, this case turns on the specification of the present evidence state. If the present evidence is individuated thinly — “I am now awake in the experiment and do not know the day” — then Tails contributes two admissible coherent realizations while Heads contributes one, and the thirder result follows.

If the admissible evidential partition treats each awakening as a distinct present self-location event, Tails carries twice the admissible measure. If instead the awakenings are treated as components of a single measure-weighted protocol rather than distinct evidential updates, a halfer result may emerge.

This does not yet solve the Sleeping Beauty dispute. It does clarify its real structure. The disagreement is not fundamentally about sampling metaphysics. It is about how the admissible present evidential vantage should be individuated. MCSL forces that choice into the open rather than concealing it.

---

## 14. Test Case: Doomsday

SSA turns low birth rank into evidence that humanity is probably short-lived. The logic is familiar: if I were randomly sampled from all humans, my being relatively early is more typical in a short-lived history than in a long-lived one.

MCSL rejects the sampling premise. The existence of many future humans does not, by itself, dilute the admissible coherent measure of my present evidential vantage. A larger future does not make my current vantage less real or less measure-weighted.

So MCSL does not generate the generic SSA-style doomsday update. It avoids pessimism without invoking SIA’s blunt population favoritism.

---

## 15. Test Case: Presumptuous Philosopher

SIA notoriously favors cosmological theories merely because they predict vastly more observers. MCSL blocks the crude version of this problem. Extra distant observers who do not instantiate my present evidential vantage do no epistemic work.

However, a narrower problem remains. Suppose Theory B predicts vastly more **admissible coherent realizations of my exact present evidence state** than Theory A. In that case, the current MCSL formula will favor B.

So MCSL does **not yet** solve Presumptuous Philosopher in full generality. It solves only the generic-population version. The exact-duplicate version remains open.

That is not a trivial concession. It means MCSL has already improved on SIA, but has not fully escaped all forms of anthropic presumptuousness. It also suggests that the eventual solution, if there is one, may require revising not only the admissibility criterion but the aggregation rule itself.

---

## 16. Test Case: Duplication and Copies

Suppose I am duplicated into two realizations with the same present evidence state. If the duplication is symmetric, the admissible coherent measure splits evenly, and the natural $1/2$ result follows. If the duplication is asymmetric in measure, MCSL yields the corresponding asymmetric credence.

This is a strength. Naive observer-counting cannot distinguish between equal-count duplications with radically unequal physical support. MCSL can.

So duplication cases do not merely fail to damage MCSL. They reveal why observer-counting was the wrong primitive in the first place.

---

## 17. Test Case: Boltzmann Brains

This is the hardest case.

If anthropic credence were assigned over bare phenomenal or even bare evidential matches, Boltzmann-brain-style counterfeits would likely swamp the theory. MCSL survives only because it ranges over **admissible coherent evidential realizations**, not bare local matches.

But the hard problem remains unresolved. The current draft does not yet provide a fully non-question-begging theory of why the admissibility relation should exclude or discount pathological counterfeit realizations. It identifies the locus of the problem and proposes a coherence-based direction. It does not claim a finished proof.

That is the honest status of the matter.

So Boltzmann brains remain an open problem for MCSL, though now in a much better-specified form.

---

## 18. Relation to Axionic Coherence

The refinement becomes clearer when read through the Axionic notion of coherence:

> A pattern is coherent iff there exists at least one non-degenerate mapping under which it can be re-identified as the same pattern across transformation.

An evidential vantage is also a pattern. If it is to count as the same evidential vantage across candidate realizations, there must exist a non-degenerate mapping under which it remains re-identifiable as that evidentially meaningful pattern. A one-frame counterfeit often fails this test. It resembles the pattern locally while lacking the support conditions under which it remains the same structured evidential pattern across relevant transformations.

This does not yet solve the admissibility problem in full. It does show that the proposed refinement is not alien to the broader framework. It is an application of preexisting coherence commitments.

---

## 19. What MCSL Claims, and What It Does Not

MCSL does **not** claim to derive a complete anthropic epistemology from bare first-person experience. It does not yet provide a finished specification of the admissibility relation. It does not fully solve Presumptuous Philosopher in the exact-duplicate case. It does not yet neutralize Boltzmann brains by theorem.

What it does claim is narrower and stronger:

1. observer-counting is the wrong primitive;
2. objective measure is the correct ontic currency;
3. self-location should be conditioned on realizations of present evidence, not arbitrary reference classes;
4. admissible coherent evidential realizations are the right candidates for anthropic weighting;
5. once that is done, the standard first-line failures of SSA are avoided without importing the crudest pathologies of SIA.

That is enough to justify serious development.

---

## 20. Open Problems

Several problems remain open.

The first is the exact content of the coherence-support relation $K(v,E)$. This will determine whether MCSL can block pathological counterfeit realizations without becoming stipulative.

The second is the granularity of the evidence-equivalence relation $\sim_E$. Too coarse, and distinct vantages collapse together illegitimately. Too fine, and anthropic reasoning becomes unusable.

The third is the treatment of exact-duplicate presumptuousness. If a theory predicts vastly more admissible coherent realizations of my exact present evidence state, what constrains the resulting update? This may require revising the linear aggregation rule over admissible realization-measure, not merely sharpening admissibility.

The fourth is the sharpening of measure in classical contexts. The theory needs a cleaner articulation of when multiplicity is a derivative of physical measure and when it is not.

These are real open questions. They are not polish items.

---

## 21. Conclusion

SSA fails because it lets arbitrary observer-sampling distort physical credence. SIA improves on that in some cases, but does so by granting sheer population size unjustified epistemic force. Both begin from the wrong place.

MCSL begins from a better one.

The correct ontic currency is objective measure. The correct epistemic object is the agent’s present evidence state. And the correct realization class is not all observers, nor all local experiential matches, but the set of **admissible coherent realizations** of that evidential vantage.

This does not yet yield a complete anthropic theory. It does something more important at this stage: it identifies the right architecture. It shows why observer-counting is a mistake, why measure must replace it, why evidence must be privileged over reference class, and why admissibility is the real frontier rather than a dispensable gloss.

Whether MCSL is ultimately the final answer remains open. But it already clarifies the landscape substantially. It avoids the clearest failures of SSA, resists the crudest excesses of SIA, and isolates the real unresolved problems instead of concealing them behind sampling rhetoric.

That is a much better starting point than either of the orthodox alternatives.

---

^1 **Axionic framework** here refers to a conditionalist ontology in which evidential and ontological interpretation depends on non-degenerate coherence under transformation rather than on unconditional observer-based primitives.
