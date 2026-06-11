# Born Measure from Self-Location

## An MCSL Account of Probability in Everettian Quantum Mechanics

### Abstract

Everettian quantum mechanics removes collapse from the physical ontology. The universal state evolves unitarily, and measurement produces decohered outcome branches rather than a single selected result. This creates a familiar problem: if all outcomes occur, in what sense should an observer assign probabilities to them, and why should those probabilities obey the Born rule?

This paper argues that the Born rule follows from two components that should be kept conceptually distinct. The first is physical: the natural measure over decohered quantum alternatives is squared Hilbert-space norm. The second is epistemic: under self-locating uncertainty, rational credence should track the total objective measure of admissible coherent realizations of one’s evidence state. The second principle is Measure-Conditioned Self-Location, or MCSL.

On this account, Everettian probability is neither ignorance about which outcome becomes real nor indifference over counted branches. It is measure-conditioned self-location within the universal wavefunction. Branch-counting fails because branches are emergent, non-canonically individuated, and indefinitely refinable. Squared Hilbert-space norm supplies the objective measure. MCSL supplies the bridge from objective measure to first-person credence.

Applied to decohered measurement outcomes, MCSL assigns credence proportional to the squared norm of the observer-supporting component associated with each outcome. For an exhaustive normalized measurement, this is exactly the Born rule.

## 1. The Everettian Probability Problem

Everettian quantum mechanics keeps the unitary dynamics of quantum theory and rejects physical collapse. The universal wavefunction evolves according to the Schrödinger equation. Measurement interactions entangle observer, system, apparatus, and environment. Decoherence then suppresses interference between macroscopic outcome components, yielding effectively autonomous branches.

For a simple measurement,

$$
|\psi\rangle = a|0\rangle + b|1\rangle ,
$$

an observer measuring in the ${|0\rangle, |1\rangle}$ basis becomes entangled with the system:

$$
(a|0\rangle + b|1\rangle)|O_{\mathrm{ready}}\rangle
\rightarrow
a|0\rangle|O_0\rangle + b|1\rangle|O_1\rangle .
$$

Under collapse theories, one result becomes actual and the other does not. Under Everett, both decohered components remain in the universal state. Each contains an observer with a definite record. The observer seeing outcome $0$ records $0$. The observer seeing outcome $1$ records $1$.

The Born rule says:

$$
P(0)=|a|^2,\qquad P(1)=|b|^2 .
$$

The difficulty is direct. If both outcomes occur, what does $P(0)$ mean? It cannot mean that outcome $0$ alone will become real. It cannot mean ordinary ignorance about which outcome exists. Both outcome records exist after branching.

The Everettian must therefore explain probability as a feature of observer-location, expectation, rational credence, or empirical typicality inside a branching ontology. The problem is not merely to find a number between 0 and 1. Squared Hilbert-space norm already gives such a number. The problem is to explain why an embedded observer should treat that number as credence.

This paper defends the following thesis:

> In Everettian quantum mechanics, the Born rule follows when squared Hilbert-space norm is used as the objective physical measure and MCSL is used as the self-location rule connecting objective measure to observer credence.

The thesis has two separable claims:

1. **Physical measure claim:** decohered quantum alternatives carry objective measure equal to squared Hilbert-space norm.
2. **Epistemic bridge claim:** rational self-locating credence tracks the total objective measure of admissible coherent realizations of one’s evidence state.

The first claim belongs to the structure of quantum theory. The second is MCSL.

## 2. Why Branch-Counting Fails

A tempting approach says that probabilities in Everett should be obtained by counting branches. If a measurement has two branches, perhaps each branch should receive probability $1/2$. If many branches result, perhaps probability should be the fraction of branches with a given outcome.

This approach fails for several reasons.

### 2.1 Branches Are Emergent, Not Fundamental Atoms

Branches are not fundamental objects in the formalism. The fundamental object is the quantum state. Branches are emergent quasi-classical patterns stabilized by decoherence. Their boundaries depend on coarse-graining, environmental records, macroscopic description, temporal resolution, and tolerance for residual interference.

There is no unique fact of the matter about the exact number of branches produced by a measurement. One can describe the environment at high resolution or low resolution. One can coarse-grain over irrelevant microscopic degrees of freedom or split them into more detailed alternatives. These choices alter the branch count without altering the physical content relevant to the observer’s record.

A probability rule that depends on arbitrary branch individuation cannot be fundamental.

### 2.2 Infinite Branch Ontology Makes Counting Worse

In an infinite-branch ontology, raw counting becomes unusable. If every outcome type is realized by infinitely many fine-grained branches, then branch ratios take the form:

$$
\frac{\infty}{\infty}.
$$

Cardinality alone does not define probability. Countably infinite sets can be rearranged to produce different apparent frequencies. Uncountable sets require a measure before relative size becomes meaningful. The mathematical problem is familiar from continuous probability theory: one cannot assign probabilities over the real line by counting points. Every interval contains the same cardinality of points. Probability requires a measure.

The same applies to Everettian branches. If branches form an indefinitely refinable or continuous structure, counting branches is the wrong operation. The relevant question is not “how many branches have this outcome?” The relevant question is “what measure does the observer-supporting region associated with this outcome carry?”

### 2.3 Branch-Counting Conflicts with Quantum Structure

Branch-counting also ignores the physical role of amplitude. Consider:

$$
|\psi\rangle = \sqrt{0.99}|0\rangle + \sqrt{0.01}|1\rangle .
$$

A naïve two-branch count assigns $1/2$ to each outcome. The quantum state assigns measures $0.99$ and $0.01$. The branch-counting answer is insensitive to the amplitudes that control interference, decoherence, repeated-measurement statistics, and the geometry of state space.

One might try to repair branch-counting by splitting the large-amplitude component into many equal-amplitude subbranches. But that move already appeals to amplitude-weighted structure. It is no longer primitive branch-counting. It has smuggled in the measure it was supposed to replace.

Branch-counting fails because branches are not countable physical atoms, because infinite branch structures require measure, and because amplitude is part of the physical structure of the theory.

## 3. Hilbert-Space Norm as Physical Measure

Quantum states live in Hilbert space. The geometry of Hilbert space supplies a natural measure over orthogonal components of the state.

Let $|\Psi\rangle$ be the universal quantum state. Let $P_i$ be a projector onto the subspace corresponding to outcome $i$. The component of the universal state associated with outcome $i$ is:

$$
P_i|\Psi\rangle .
$$

Its squared norm is:

$$
\mu(i)=|P_i|\Psi\rangle|^2 .
$$

For an exhaustive set of orthogonal outcomes,

$$
\sum_i P_i = I,
$$

and for a normalized state,

$$
\sum_i |P_i|\Psi\rangle|^2 = 1 .
$$

This is the familiar mathematical form of the Born rule. At this stage, however, it should be called objective quantum measure, not yet probability. The move from measure to credence still needs justification.

The squared-norm measure has several properties required of any physically serious quantum measure.

### 3.1 Non-Negativity

A measure assigned to an outcome must be non-negative. Quantum amplitudes can be negative or complex. Squared norm converts complex amplitude into a non-negative real quantity:

$$
|a|^2 = a^*a .
$$

### 3.2 Additivity Over Orthogonal Alternatives

Decohered alternatives correspond, approximately, to orthogonal subspaces. If two alternatives are mutually exclusive and orthogonal, the measure of their union should be the sum of their measures:

$$
\mu(A \oplus B)=\mu(A)+\mu(B).
$$

Squared Hilbert norm has this property. Raw amplitude does not.

### 3.3 Invariance Under Redescription

The measure assigned to a physical alternative should not depend on an arbitrary choice of basis or notation. If two descriptions represent the same subspace, they should receive the same measure. Squared Hilbert norm is invariant under unitary changes of basis.

### 3.4 Conservation Under Unitary Evolution

Unitary evolution preserves Hilbert-space norm. If the universal state evolves unitarily, total measure is conserved:

$$
|\Psi(t)|^2 = |\Psi(0)|^2.
$$

This makes squared norm structurally suited to play the role of conserved quantum measure.

### 3.5 Locality to the Relevant Subspace

The measure assigned to an outcome should depend on the component of the state realizing that outcome, rather than on arbitrary labeling or external bookkeeping. Projectors let us isolate the physically relevant component:

$$
\mu(E)=|P_E|\Psi\rangle|^2.
$$

Here $E$ may be an outcome, an evidence state, or a larger observer-supporting condition.

These properties do not yet prove that squared norm is subjective probability. They identify squared norm as the canonical physical measure over decohered alternatives.

## 4. The Missing Bridge

The Everettian probability problem persists because objective measure and subjective credence are different concepts.

A physical theory can tell us that one region of state space has greater measure than another. It does not automatically follow that an embedded observer’s first-person expectation should be proportional to that measure. This is the gap.

Different Everettian programs try to bridge it differently.

Decision-theoretic approaches argue that rational agents making bets in a branching universe should weight outcomes by Born measure. Symmetry approaches try to derive equiprobability for equal-amplitude components and extend that result to unequal amplitudes. Self-location approaches argue that after branching but before observation, an observer can know the universal state while remaining uncertain which branch they occupy.

Each approach identifies a real feature of the problem. The decision-theoretic approach captures practical rationality. Symmetry arguments capture structural invariance. Self-location captures the first-person epistemic situation of an observer inside the wavefunction.

MCSL belongs in the third family, with a sharper general principle.

## 5. Measure-Conditioned Self-Location

Measure-Conditioned Self-Location says:

> Under self-locating uncertainty, credence should track the total objective measure of admissible coherent realizations of one’s present evidence state.

This rule is conditional. It requires:

1. an interpreted physical ontology;
2. an admissible hypothesis space;
3. an objective measure structure;
4. an account of which realizations count as coherent evidence-bearing vantages.

MCSL does not derive a measure from bare first-person experience. It tells an embedded observer how to use the objective measure supplied by a physical theory when assigning self-locating credence.

In abstract form:

$$
C(H\mid E)=\frac{\mu(A(H,E))}{\mu(A(E))}.
$$

Where:

* $C(H\mid E)$ is the observer’s credence in hypothesis $H$, conditional on evidence $E$;
* $A(E)$ is the class of admissible coherent realizations of the observer’s evidence state;
* $A(H,E)$ is the subclass satisfying both $H$ and $E$;
* $\mu$ is the objective measure over admissible realizations.

The key point is that MCSL does not count observer-copies. It weighs admissible observer-realizations by the measure assigned by the underlying physical ontology.

In a classical duplication case, the relevant measure may reduce to copy-counting if all copies are physically equivalent and equally weighted. In cosmology, the measure problem becomes harder because the physical measure may be contested. In Everettian quantum mechanics, the candidate measure is unusually clear: squared Hilbert-space norm.

This makes Everett the cleanest case for MCSL.

## 6. Everettian Specialization of MCSL

Apply MCSL to an Everettian measurement.

Let $|\Psi\rangle$ be the universal state before observation. Let $E$ be the observer’s current evidence state prior to learning the measurement result. Let $H_i$ be the hypothesis:

$$
H_i = \text{“I am located in, or will be continuous with, the outcome-}i\text{ observer-state.”}
$$

Let $P_{A_i(E)}$ be the projector onto the subspace containing admissible coherent observer-realizations satisfying both $E$ and $H_i$. Then MCSL gives:

$$
C(H_i\mid E)
=
\frac{|P_{A_i(E)}|\Psi\rangle|^2}
{\sum_j |P_{A_j(E)}|\Psi\rangle|^2}.
$$

For an ideal decohered measurement, each outcome subspace corresponds to one admissible class of observer-realizations. The measure of each class is the squared norm of the corresponding projected component.

For a normalized exhaustive measurement,

$$
\sum_j |P_{A_j(E)}|\Psi\rangle|^2 = 1,
$$

so:

$$
C(H_i\mid E)=|P_{A_i(E)}|\Psi\rangle|^2.
$$

This is the Born rule, interpreted as measure-conditioned self-location.

For the simple qubit case:

$$
|\psi\rangle = a|0\rangle + b|1\rangle,
$$

measurement yields:

$$
a|0\rangle|O_0\rangle + b|1\rangle|O_1\rangle.
$$

The relevant observer-outcome projectors isolate the two decohered observer-states:

$$
P_0|\Psi\rangle = a|0\rangle|O_0\rangle,
$$

$$
P_1|\Psi\rangle = b|1\rangle|O_1\rangle.
$$

Their measures are:

$$
\mu(O_0)=|a|^2,
$$

$$
\mu(O_1)=|b|^2.
$$

MCSL therefore gives:

$$
C(O_0)=|a|^2,\qquad C(O_1)=|b|^2.
$$

The Born rule is obtained by applying MCSL to the Hilbert-space measure over admissible observer-realizations.

## 7. Why This Is Probability

The remaining question is why this should count as probability.

In a single-outcome theory, probability can be interpreted as uncertainty about which outcome will become actual. In Everett, all outcomes become actual as decohered components of the universal state. Probability must therefore be reconstructed as self-locating credence.

Before observation, the agent knows the following:

1. the universal state will contain observer-states recording each decohered outcome;
2. each future observer-state is continuous with the pre-measurement observer;
3. the observer has no further evidence selecting one future record over another;
4. the future observer-states carry different objective measures.

The rational question is:

> How should the present observer distribute expectation across future admissible observer-realizations?

MCSL answers:

> In proportion to their objective measure.

This is the same conceptual structure used in other measure-based theories. In statistical mechanics, atypical entropy-decreasing microstates are physically allowed, but rational expectation tracks phase-space measure. In continuous probability, individual points may all have measure zero, yet intervals have different probabilities. In cosmology, bare existence of observers does not determine anthropic expectation; one needs a reference measure.

Everettian quantum mechanics is a measure theory over observer-realizing subspaces. Existence alone gives no usable credence rule. Branch-counting gives no invariant rule. Squared Hilbert-space measure gives the physical weighting. MCSL gives the epistemic bridge.

## 8. Repeated Measurements and Born-Typical Records

The Born rule is empirically tested through repeated measurements. MCSL must therefore recover Born-typical observed frequencies.

Consider $N$ repetitions of a two-outcome measurement with state:

$$
\sqrt{p}|0\rangle + \sqrt{1-p}|1\rangle .
$$

After $N$ measurements, the universal state contains decohered components corresponding to all binary sequences of length $N$. A sequence with $k$ zeroes and $N-k$ ones has amplitude magnitude:

$$
p^{k/2}(1-p)^{(N-k)/2}.
$$

Its squared measure is:

$$
p^k(1-p)^{N-k}.
$$

There are:

$$
\binom{N}{k}
$$

such sequences. The total measure of observer-records with exactly $k$ zeroes is:

$$
\binom{N}{k}p^k(1-p)^{N-k}.
$$

This is the binomial distribution. As $N$ grows, the total measure concentrates around:

$$
k \approx pN.
$$

Branches with frequencies far from $p$ exist, but their total measure becomes small. MCSL says rational credence tracks that total measure. Therefore an observer should expect to see Born-typical frequencies.

This recovers the empirical content of quantum probability without collapse and without treating branch-count as fundamental.

## 9. Relation to Decision-Theoretic Everettian Probability

Deutsch-Wallace decision theory argues that rational agents in Everettian branching scenarios should act as though outcome weights are given by the Born rule. This is an important result because probability is tightly connected to rational action. If an agent’s betting behavior violates Born weights, that agent violates constraints on coherent preference under branching.

MCSL differs in emphasis.

Decision theory asks:

> How should a rational Everettian agent value branching games?

MCSL asks:

> How should an embedded Everettian observer assign self-locating credence over admissible observer-realizations?

These questions are related, but they are not identical. Betting behavior is downstream of credence plus utility. MCSL addresses the credence assignment directly.

A decision-theoretic Everettian can accept MCSL as explaining why the rational betting weights have first-person epistemic meaning. An MCSL Everettian can accept decision theory as showing that agents who use MCSL-guided credences will make coherent decisions under branching.

The approaches are compatible. MCSL is more directly aimed at the observer-location problem.

## 10. Relation to Sebens-Carroll Self-Location

Sebens and Carroll argue that self-locating uncertainty after branching can ground the Born rule in Everettian quantum mechanics. Their approach identifies the period after measurement but before observation as one in which the observer knows the universal state but does not know which branch they occupy. They introduce an epistemic separability principle to block irrelevant environmental facts from altering branch probabilities.

MCSL is close in spirit but broader in structure.

The Sebens-Carroll approach is specialized to Everettian branching. MCSL is a general principle for self-location in any interpreted ontology with an objective measure over admissible observer-realizations. Applied to Everett, it yields the same broad kind of result: self-location credence should be amplitude-weighted rather than branch-counted.

The advantage of MCSL is that it separates three issues that are often run together:

1. what the physical ontology contains;
2. what objective measure the ontology supplies;
3. how first-person credence should use that measure.

Everett supplies the ontology. Hilbert-space geometry supplies the measure. MCSL supplies the self-location rule.

## 11. Relation to Gleason-Type Results

Gleason’s theorem and related results show that, given certain assumptions about assigning probabilities to projection operators, the Born form is forced by the structure of Hilbert space. These results are powerful because they show that the squared-norm rule is not an arbitrary choice among many equally natural alternatives.

However, Gleason-style results have a limitation for Everettian purposes. They assume that probabilities are being assigned to quantum events. They constrain the form such assignments must take. They do not, by themselves, explain why an observer inside a branching universal wavefunction should interpret squared norm as self-locating credence.

MCSL supplies that missing interpretive step.

Gleason-type arguments support the physical measure claim. MCSL supplies the epistemic bridge claim.

Together, the structure is:

1. If quantum events receive a non-contextual additive measure over projectors, the measure has Born form.
2. Everettian observer-realizations are represented by decohered subspaces/projectors.
3. MCSL says self-locating credence tracks the objective measure of admissible observer-realizations.
4. Therefore Everettian credence tracks Born measure.

This gives each argument the right job. Gleason-style reasoning constrains measure. MCSL interprets measure as self-location credence.

## 12. Relation to Envariance and Symmetry Arguments

Envariance arguments attempt to derive the Born rule from symmetries of entangled quantum states. Equal-amplitude alternatives are treated symmetrically; unequal amplitudes are handled by decomposing them into equal-amplitude structures.

MCSL can accept these arguments as support for the objectivity of squared Hilbert-space measure. The self-location bridge remains distinct. Symmetry may help explain why a measure should assign equal weights to equal-amplitude alternatives. MCSL explains why an observer’s credence should track the resulting measure.

This distinction prevents a common ambiguity. A symmetry argument may show that two alternatives deserve equal measure. It does not automatically explain why subjective expectation should follow measure in a universe where all alternatives are realized. MCSL handles that second step.

## 13. Why Mangled Worlds Are Unnecessary Here

Mangled-worlds approaches attempt to recover Born statistics by arguing that low-measure branches are dynamically damaged, overwritten, or rendered observationally unavailable by interaction with higher-measure branches. If only unmangled branches support coherent observers, and if the mangling threshold has the right structure, then observed frequencies may approximate the Born rule.

This approach tries to make branch survival do the work of probability.

MCSL does not need that machinery. Low-measure branches do not have to be destroyed, damaged, or made incoherent. They may exist as admissible observer-realizations. Their contribution to rational credence is small because their measure is small.

The empirical claim becomes:

> Anti-Born observer records exist with low measure.

It need not become:

> Anti-Born observer records must be physically eliminated.

This is a cleaner Everettian position. It preserves unitary dynamics and avoids adding a quasi-collapse selection mechanism.

## 14. Objections

### 14.1 “MCSL Assumes the Born Rule”

MCSL does not assume the Born rule as a probability rule. It assumes that a physical ontology supplies an objective measure. In Everettian quantum mechanics, the candidate measure is squared Hilbert-space norm.

The argument does require the physical measure claim:

$$
\mu(i)=|P_i|\Psi\rangle|^2.
$$

That claim is not MCSL itself. It is supplied by the structure of quantum theory and supported by the usual Hilbert-space constraints: additivity over orthogonal subspaces, unitary invariance, non-negativity, and norm conservation.

MCSL then says that self-locating credence should track that measure.

So the derivation is conditional:

> Given Everettian ontology and squared Hilbert-space physical measure, MCSL yields Born-rule credence.

This is not circular unless “squared Hilbert-space measure” is already interpreted as subjective probability. The paper explicitly avoids that conflation. Measure is physical structure. Credence is epistemic attitude. MCSL connects them.

### 14.2 “Why Should Credence Track Measure?”

This is the central objection.

The answer is that self-location in a many-realization ontology requires a weighting rule. Bare existence gives no usable expectation. Branch-counting is not invariant. Subjective indifference over arbitrarily individuated branches produces contradictions under refinement.

The rational weighting rule should track the objective measure supplied by the ontology. In Everett, that measure is squared Hilbert-space norm.

This is a bridge principle. It cannot be derived from unitary dynamics alone, because unitary dynamics is third-person physics. Credence is a first-person epistemic norm. Every account of Everettian probability requires some bridge from physics to expectation. MCSL makes the bridge explicit.

The bridge principle is modest:

> When an observer knows that multiple admissible coherent realizations of their evidence state exist, and those realizations carry unequal objective measure, their self-locating credence should be proportional to that measure.

Rejecting this principle leaves no stable alternative. Equal weighting over branches depends on arbitrary branch individuation. Equal weighting over outcomes ignores refinement. Equal weighting over observer-descriptions ignores physical measure. Refusal to assign credence makes empirical confirmation unintelligible in Everett.

### 14.3 “What About Low-Measure Observers?”

Low-measure observers exist. MCSL does not deny them.

An observer in an anti-Born branch can record anti-Born frequencies. That observer’s evidence is real from within that branch. MCSL says such observer-realizations carry low total measure. Therefore a pre-measurement observer should assign low credence to becoming such an observer, and a post-measurement observer should treat a long anti-Born record as evidence against the theory, because that record had low expected measure under the theory.

This is the same structure used in ordinary probabilistic reasoning. Low-probability events can occur. Their occurrence is evidence, especially when repeated or extreme.

### 14.4 “Does This Reduce Probability to Typicality?”

It reduces Everettian probability to measure-conditioned typicality over observer-realizations. That is the right reduction.

In Everett, probability cannot be exclusive actuality selection. The universal state contains every decohered outcome. Probability must instead describe where observers should expect to find themselves within the measure-structured ontology.

This is typicality, but not vague typicality. It is conditionalized typicality over admissible coherent evidence-bearing vantages:

$$
C(H\mid E)=\frac{\mu(A(H,E))}{\mu(A(E))}.
$$

### 14.5 “What Counts as an Admissible Coherent Realization?”

An admissible coherent realization must support the evidence state in the right way. It must be a physically coherent observer-vantage, not a superficial pattern match. The realization must preserve the functional, causal, and evidential structure that makes the observer’s evidence genuinely present.

This matters because self-location theories can be distorted by gerrymandered observer descriptions, Boltzmann-brain-like fluctuations, and accidental information-pattern matches. MCSL requires an admissibility criterion to exclude pseudo-realizations that do not instantiate the relevant evidence-bearing perspective.

In Everettian laboratory measurements, this problem is usually mild. Decohered observer records produced by ordinary measurement interactions are admissible coherent realizations. The harder cases arise in cosmology, simulation, duplication, and disordered thermal fluctuation scenarios.

## 15. Confirmation in Everett

A theory is empirically confirmed when observations that it assigns high credence occur and observations it assigns low credence fail to occur. In Everett, all physically possible records may occur somewhere, so confirmation must be measure-sensitive.

Suppose theory $T_1$ assigns high measure to Born-typical records and low measure to anti-Born records. Suppose theory $T_2$ assigns high measure to a different pattern. An observer who records Born-typical frequencies should update toward $T_1$, because their evidence has higher measure conditional on $T_1$:

$$
C(T_1\mid E)\propto C(E\mid T_1)C(T_1).
$$

MCSL interprets $C(E\mid T_1)$ as the measure of admissible observer-realizations with evidence $E$ under $T_1$.

This preserves empirical confirmation in Everett. The fact that disconfirming records exist somewhere does not defeat confirmation, because confirmation was never based on bare existence. It is based on measure-conditioned likelihood.

## 16. The Full Argument

The argument can now be stated compactly.

1. Everettian quantum mechanics contains all decohered measurement outcomes.
2. Therefore probability cannot mean uncertainty about which outcome uniquely becomes real.
3. Branch-counting cannot ground probability because branches are emergent, non-canonically individuated, and indefinitely refinable.
4. Infinite branch ontology requires a measure rather than cardinality.
5. Quantum theory supplies a natural objective measure over decohered subspaces: squared Hilbert-space norm.
6. Observers inside Everettian quantum mechanics face self-locating uncertainty over admissible coherent observer-realizations.
7. MCSL says self-locating credence should track the total objective measure of admissible coherent realizations of one’s evidence state.
8. Therefore Everettian observer credence should be proportional to squared Hilbert-space measure.
9. For exhaustive normalized measurements, this yields:

$$
C(H_i\mid E)=|P_i|\Psi\rangle|^2.
$$

10. This is the Born rule.

## 17. Conclusion

The Born rule in Everettian quantum mechanics requires both a measure and a bridge from measure to credence. Squared Hilbert-space norm supplies the measure. MCSL supplies the bridge.

The account does not claim that subjective probability falls out of linear algebra alone. That would obscure the real structure of the problem. Linear algebra identifies the natural physical measure over decohered alternatives. MCSL explains why an embedded observer’s self-locating credence should track that measure.

This gives a clean Everettian interpretation of quantum probability:

$$
\text{Born probability} = \text{squared-amplitude measure-conditioned self-location}.
$$

All outcomes occur. Observers should not count outcomes, branches, or copies. They should conditionalize over admissible coherent observer-realizations using the objective measure supplied by the universal quantum state.

## References

Carroll, Sean M. “Many Worlds, the Born Rule, and Self-Locating Uncertainty.” arXiv:1405.7907.

Deutsch, David. “Quantum Theory of Probability and Decisions.” Proceedings of the Royal Society A, 1999.

Everett, Hugh. “‘Relative State’ Formulation of Quantum Mechanics.” Reviews of Modern Physics, 1957.

Gleason, Andrew M. “Measures on the Closed Subspaces of a Hilbert Space.” Journal of Mathematics and Mechanics, 1957.

Hanson, Robin. “Mangled Worlds.” 2003.

Sebens, Charles T., and Sean M. Carroll. “Self-Locating Uncertainty and the Origin of Probability in Everettian Quantum Mechanics.” arXiv:1405.7577.

Vaidman, Lev. “Probability in the Many-Worlds Interpretation of Quantum Mechanics.” Various versions.

Wallace, David. “A Formal Proof of the Born Rule from Decision-Theoretic Assumptions.” arXiv:0906.2718.

Zurek, Wojciech H. “Environment-Assisted Invariance, Entanglement, and Probabilities in Quantum Physics.” Physical Review Letters, 2003.
