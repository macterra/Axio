# Born Measure from Self-Location

## An MCSL Account of Probability in Everettian Quantum Mechanics

### Abstract

Everettian quantum mechanics removes collapse from the physical ontology. The universal state evolves unitarily, and measurement produces decohered outcome branches rather than a single selected result. This creates a familiar problem: if all outcomes occur, in what sense should an observer assign probabilities to them, and why should those probabilities obey the Born rule?

This paper offers not a derivation of probability from probability-free premises but a *conditional reduction*: the Born rule follows once two substantive and conceptually distinct posits are granted. The first is physical: the natural measure over decohered quantum alternatives is squared Hilbert-space norm. The second is epistemic: under self-locating uncertainty, rational credence should track the total objective measure of admissible coherent realizations of one’s evidence state. The second principle is Measure-Conditioned Self-Location, or MCSL. Neither posit is forced by the unitary formalism alone, and the paper is explicit about what each one costs.

On this account, Everettian probability is neither ignorance about which outcome becomes real nor indifference over counted branches. It is measure-conditioned self-location within the universal wavefunction. Branch-counting fails because branches are emergent, non-canonically individuated, and indefinitely refinable. Squared Hilbert-space norm supplies the objective measure. MCSL supplies the bridge from objective measure to first-person credence.

Applied to decohered measurement outcomes, MCSL assigns credence proportional to the squared norm of the observer-supporting component associated with each outcome. For an exhaustive normalized measurement, this is exactly the Born rule. The account does not dissolve the two residual difficulties it inherits — why squared norm rather than another function of amplitude, and whether self-locating uncertainty is even coherent when every outcome occurs — but it isolates them, so that each can be argued on its own terms.

## 1. The Everettian Probability Problem

Everettian quantum mechanics keeps the unitary dynamics of quantum theory and rejects physical collapse. The universal wavefunction evolves according to the Schrödinger equation. Measurement interactions entangle observer, system, apparatus, and environment. Decoherence then suppresses interference between macroscopic outcome components, yielding effectively autonomous branches.

For a simple measurement,

$$
|\psi\rangle = a|0\rangle + b|1\rangle ,
$$

an observer measuring in the $\{|0\rangle, |1\rangle\}$ basis becomes entangled with the system:

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

The second claim is MCSL. The first claim is often treated as belonging to the structure of quantum theory, but as §3 and §11 make clear, the constraints usually cited do not by themselves single out the squared norm among competing functions of amplitude; that selection is itself a substantive step. The result of the paper is therefore a conditional reduction — *given* both claims, Born-rule credence follows — not a derivation of probability from non-probabilistic premises.

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

Two cautions should be registered now and discharged later, so that the positive account is not read as a free lunch. First, the measure that replaces counting must still be applied to *some* partition of the state into alternatives; measure-weighting does not by itself supply that partition (§6). Second, calling squared norm “the” measure presupposes that one power of amplitude is privileged over the others (§3.6). Branch-counting fails for the reasons given, but the account that replaces it incurs these two debts.

## 3. Hilbert-Space Norm as Physical Measure

Quantum states live in Hilbert space. The geometry of Hilbert space supplies a natural measure over orthogonal components of the state.

Let $|\Psi\rangle$ be the universal quantum state. Let $P_i$ be a projector onto the subspace corresponding to outcome $i$. The component of the universal state associated with outcome $i$ is:

$$
P_i|\Psi\rangle .
$$

Its squared norm is:

$$
\mu(i)=\lVert P_i|\Psi\rangle\rVert^2 .
$$

For an exhaustive set of orthogonal outcomes,

$$
\sum_i P_i = I,
$$

and for a normalized state,

$$
\sum_i \lVert P_i|\Psi\rangle\rVert^2 = 1 .
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

Squared norm has this property. For orthogonal $A$ and $B$, $\lVert v_A + v_B\rVert^2 = \lVert v_A\rVert^2 + \lVert v_B\rVert^2$ by the Pythagorean theorem. The sharpest way to see why it is the *square* that matters, and not the norm itself, is that the squared norm of a projected component is *linear in the projector*:

$$
\lVert P_i|\Psi\rangle\rVert^2 = \langle\Psi|P_i|\Psi\rangle,
$$

so additivity over orthogonal projectors holds identically, $\langle\Psi|(P_A + P_B)|\Psi\rangle = \langle\Psi|P_A|\Psi\rangle + \langle\Psi|P_B|\Psi\rangle$. Projection alone does not deliver this number. It delivers the component *vector* $P_i|\Psi\rangle$, whose norm is $|a|$ in the qubit case, and the squaring is a further step. What forces that step is the demand for additivity: among the powers $|a|^p$, only $p = 2$ is additive over orthogonal alternatives, because only the square is linear in the projector; the plain norm ($p = 1$) and the higher powers fail. Raw signed or complex amplitude is not even a candidate, since it fails non-negativity. A non-negative assignment that is additive over orthogonal direct sums and depends only on the subspace is thereby driven toward the squared-norm form, which is the content of Gleason's theorem (§11). Whether that additivity constraint can be imposed *non-circularly* in a branching setting — where additivity over exclusive alternatives is also the probability axiom — is taken up in §3.6 and §11.

### 3.3 Invariance Under Redescription

The measure assigned to a physical alternative should not depend on an arbitrary choice of basis or notation. If two descriptions represent the same subspace, they should receive the same measure. Squared Hilbert norm is invariant under unitary changes of basis.

### 3.4 Conservation Under Unitary Evolution

Unitary evolution preserves the total Hilbert-space norm:

$$
\lVert\Psi(t)\rVert^2 = \lVert\Psi(0)\rVert^2.
$$

This is a conserved global quantity, which is part of what makes squared norm a natural candidate measure. A caveat is needed, however. Global conservation does *not* entail that the measure of any particular branch is conserved. While components remain coherent, interference and recoherence redistribute weight between them, and a branch's squared norm is only approximately stable *after* decoherence has suppressed the relevant interference terms. The stability the account actually relies on is therefore a FAPP, post-decoherence stability of branch weights, not an exact conservation law for individual branches.

### 3.5 Locality to the Relevant Subspace

The measure assigned to an outcome should depend on the component of the state realizing that outcome, rather than on arbitrary labeling or external bookkeeping. Projectors let us isolate the physically relevant component:

$$
\mu(E)=\lVert P_E|\Psi\rangle\rVert^2.
$$

Here $E$ may be an outcome, an evidence state, or a larger observer-supporting condition.

These properties do not yet prove that squared norm is subjective probability. They identify squared norm as the canonical physical measure over decohered alternatives.

### 3.6 Why Squared Norm Rather Than Another Power?

The properties above are necessary conditions, not a uniqueness proof. Non-negativity is shared by every $|a|^p$. Redescription-invariance and the global conservation law constrain but do not fix the exponent. The one property that genuinely discriminates is additivity over orthogonal alternatives, and it discriminates only through a theorem — Gleason's (§11) — whose premise is that the assignment to subspaces is a *non-contextual additive* one. That premise is already close to assuming that the quantity in question behaves like a probability. Appealing to Gleason to certify the physical measure therefore risks importing, as a premise about physical structure, the very additivity that is contested when the structure is reinterpreted as credence.

Two non-circular routes remain, and the account leans on them rather than on the bare property-list.

The first is *dynamical*. Squared amplitude is not an arbitrary label on a branch; it is the quantity that governs interference, the rate and structure of decoherence, transition rates, and the recombination of histories. A function such as $|a|^4$ has no comparable dynamical office. The exponent $p=2$ is the one written into the equations of motion, not merely into the bookkeeping. This is a substantive physical claim about *which* feature of a component does causal work, and it is what the paper means in calling squared norm "the objective measure."

The second is *symmetry* (§12). Envariance-style arguments fix equal weights for equal-amplitude components from the structure of entanglement, and reach unequal amplitudes by fine-graining into equal-amplitude sub-structures. Where they succeed, they pin the exponent without first assuming an additive credence.

Neither route is uncontested. The honest position is that the privileging of $p=2$ is a load-bearing physical posit, defended dynamically and by symmetry, and *not* a free consequence of the abstract notion of "a measure." The split between the physical-measure claim and the epistemic bridge does not make the first claim cheap; it locates it precisely, so that it can be argued for rather than assumed.

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
\frac{\lVert P_{A_i(E)}|\Psi\rangle\rVert^2}
{\sum_j \lVert P_{A_j(E)}|\Psi\rangle\rVert^2}.
$$

For an ideal decohered measurement, each outcome subspace corresponds to one admissible class of observer-realizations. The measure of each class is the squared norm of the corresponding projected component.

A concession is owed here. The projectors $P_{A_i(E)}$ presuppose a determinate partition of the universal state into observer-supporting subspaces — exactly the kind of individuation that §2 found to be emergent and non-canonical. MCSL does not escape this. What MCSL avoids is the *counting* of branches within a partition, which is refinement-dependent; the squared-norm measure is refinement-invariant, so finer or coarser admissible decompositions of the same outcome subspace return the same total measure. But the coarse partition into outcomes $\{A_i(E)\}$ is itself supplied, approximately and FAPP, by decoherence — the same resource every Everettian account draws on. The advantage of measure over counting is therefore real but narrower than it can first appear: it is invariance under refinement, not independence from the preferred basis.

For a normalized exhaustive measurement,

$$
\sum_j \lVert P_{A_j(E)}|\Psi\rangle\rVert^2 = 1,
$$

so:

$$
C(H_i\mid E)=\lVert P_{A_i(E)}|\Psi\rangle\rVert^2.
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

In a single-outcome theory, probability can be interpreted as uncertainty about which outcome will become actual. In Everett, all outcomes become actual as decohered components of the universal state. Probability must therefore be reconstructed as self-locating credence. That this reconstruction is even available is itself contested: the objection that branching leaves *no* uncertainty for a credence to attach to is the most serious challenge to the entire program, and it is met directly in §14.6.

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

Branches with frequencies far from $p$ exist, but their total *measure* becomes small. MCSL says rational credence tracks that total measure, so an observer should expect to see Born-typical frequencies.

It is essential to be clear about the logical status of this result. The concentration is a fact about the squared-norm measure, and it holds *because* the records are weighted by that measure rather than counted. If one instead counted maverick records, the conclusion would reverse. For $p \neq \tfrac{1}{2}$ the sequences with near-equal frequencies are exponentially the most numerous — there are about $\binom{N}{N/2} \sim 2^N/\sqrt{N}$ of them — even though each carries exponentially small squared norm. Branch-*count* is dominated by anti-Born frequencies; branch-*measure* is dominated by Born frequencies. The law of large numbers delivers Born statistics only once the squared-norm weighting is already in force.

This section therefore does not provide independent confirmation of the Born rule. It is an internal consistency check: it shows that MCSL together with the squared-norm measure is empirically adequate — that it predicts the frequencies we observe and does not contradict itself across repeated trials. The weighting it assumes is exactly the bridge the paper is arguing for. The result is that the bridge, once granted, reproduces standard quantum statistics without collapse and without treating branch-count as fundamental.

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

It is worth being candid about what is and is not new here. MCSL's two ingredients each have close precursors: the objective measure is essentially Vaidman's measure of existence, and the self-locating manoeuvre is essentially the Sebens–Carroll use of post-branching, pre-observation uncertainty together with an epistemic-separability constraint. What MCSL contributes is not a new mechanism but a *factorization* — the explicit separation of ontology, objective measure, and self-location rule into three independently assessable claims — together with a generalization of the third claim beyond Everett. That generalization is double-edged. A fully general "track the objective measure" principle says nothing, by itself, about *which* measure is objective in a given ontology; in cosmology that question is open, and even in Everett it is the substantive content of §3.6. The generality of MCSL should not be mistaken for added explanatory power on the hard question. The general principle organizes the problem; the Everett-specific physical-measure claim does the work.

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
\mu(i)=\lVert P_i|\Psi\rangle\rVert^2.
$$

That claim is not MCSL itself. But it should not be waved through as "mere mathematics" either. As §3.6 argued, the usual Hilbert-space constraints — non-negativity, unitary invariance, norm conservation — do not by themselves single out the squared norm; only additivity over orthogonal subspaces does, and that route runs through Gleason's theorem, whose non-contextual-additivity premise is itself close to a probabilistic assumption. The physical-measure claim is defended instead on dynamical and symmetry grounds (§3.6, §12). The point for the present objection is narrower: even granting that the privileging of squared norm is substantive, it is a claim about *physical* structure — about which feature of a component governs the dynamics — and not yet a claim that this structure is subjective probability.

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

This is the sense in which the paper's result is a conditional reduction rather than a proof. MCSL is offered as a primitive norm of self-locating rationality, on a par with the principle that, absent other information, one's credence should track objective chance. It is defended as the best — arguably the only stable — weighting rule available in a many-realization ontology, not deduced from the dynamics. A reader who rejects it owes an alternative; but a reader is not *compelled* to it by the formalism alone.

### 14.3 “What About Low-Measure Observers?”

Low-measure observers exist. MCSL does not deny them.

An observer in an anti-Born branch can record anti-Born frequencies. That observer’s evidence is real from within that branch. MCSL says such observer-realizations carry low total measure. Therefore a pre-measurement observer should assign low credence to becoming such an observer, and a post-measurement observer should treat a long anti-Born record as evidence against the theory, because that record had low expected measure under the theory.

This is the same structure used in ordinary probabilistic reasoning. Low-probability events can occur. Their occurrence is evidence, especially when repeated or extreme.

The analogy to ordinary low-probability events is imperfect, however, and the disanalogy is the residual metaphysical cost of the view. In a single-world theory a low-probability outcome *usually does not happen*; here the anti-Born branch definitely happens, and the observer in it is fully real, with experience no less vivid than ours. MCSL does not soften this by making low-measure observers "partly real" or "faint." It says only that their measure is low, and that low measure is what credence and confirmation track. Whether a fully real observer should regard their own branch's low measure as a reason to discount their situation is precisely the force of the bridge principle (§14.2); the account does not pretend this is obvious. It claims that the alternative — granting equal standing to every realization regardless of measure — is worse, because it renders the observed statistical regularities of quantum mechanics inexplicable.

### 14.4 “Does This Reduce Probability to Typicality?”

It reduces Everettian probability to measure-conditioned typicality over observer-realizations. That is the right reduction.

In Everett, probability cannot be exclusive actuality selection. The universal state contains every decohered outcome. Probability must instead describe where observers should expect to find themselves within the measure-structured ontology.

This is typicality, but not vague typicality. It is conditionalized typicality over admissible coherent evidence-bearing vantages:

$$
C(H\mid E)=\frac{\mu(A(H,E))}{\mu(A(E))}.
$$

Two caveats keep this from being a verbal victory. First, "typical = high measure" is itself a posit: nothing in the bare measure compels a rational agent to *expect* the typical rather than merely to *label* it so. This is the standing complaint against typicality accounts generally, and it recurs in the Boltzmannian and Bohmian literatures. MCSL's answer is the bridge principle of §14.2; the reduction to typicality does not avoid that commitment, it relocates it. Second, the reduction is only as good as the admissibility criterion that fixes $A(E)$, discussed next.

### 14.5 “What Counts as an Admissible Coherent Realization?”

An admissible coherent realization must support the evidence state in the right way. It must be a physically coherent observer-vantage, not a superficial pattern match. The realization must preserve the functional, causal, and evidential structure that makes the observer’s evidence genuinely present.

This matters because self-location theories can be distorted by gerrymandered observer descriptions, Boltzmann-brain-like fluctuations, and accidental information-pattern matches. MCSL requires an admissibility criterion to exclude pseudo-realizations that do not instantiate the relevant evidence-bearing perspective.

In Everettian laboratory measurements, this problem is usually mild. Decohered observer records produced by ordinary measurement interactions are admissible coherent realizations. The harder cases arise in cosmology, simulation, duplication, and disordered thermal fluctuation scenarios.

### 14.6 “There Is No Uncertainty to Be Uncertain About”

The deepest objection, pressed by Albert and by Kent, is prior to all of the above: it denies that there is any genuine uncertainty in Everett for a credence to be the credence *of*. Before the measurement, the agent knows the full deterministic future — every outcome occurs, each with a successor who records it. After the measurement, each successor knows their own result. The decision-theoretic and self-locating programs both try to exploit a sliver of time, after branching but before the agent reads the outcome, in which the agent supposedly "knows the universal state but not which branch they are in." Critics argue that this sliver is illusory: with realistic decoherence there is no determinate moment at which the agent has split but not yet self-located, and in any case there is no single subject who is uncertain — there are several subjects, each with a settled outcome. "No probability without uncertainty," on this view, is a constraint Everett cannot meet.

MCSL does not refute this objection so much as decline its framing, and the cost of doing so should be stated plainly. MCSL does not require a temporal window of ignorance. Its "uncertainty" is indexical rather than dynamical: even with full knowledge of the universal state and of the deterministic dynamics, the question "which of the admissible observer-realizations of my present evidence am I about to be continuous with?" has no answer fixed by that knowledge, because the evidence does not discriminate among them. This is self-location in the sense of the standard Sleeping-Beauty and personal-duplication cases, where uncertainty survives complete knowledge of the third-person facts. If indexical self-location is a coherent locus for credence in those cases — and the burden is on the critic to explain why it would not be — then it is coherent here, and MCSL says how to apportion it.

What the objection does establish is that the Everettian cannot interpret probability as *uncertainty about which outcome will occur*; that reading is simply false in a branching world (§7). The defender's claim is the weaker one, that *indexical* credence remains well-posed. Whether indexical credence under full physical knowledge counts as genuine "probability" or as a distinct propositional attitude wearing probability's mathematics is, at this point, partly terminological — but the terminological question does not touch the empirical adequacy established in §8 or the confirmation structure of §15. The account stands or falls with the legitimacy of self-locating credence in general, not with any special infirmity of quantum branching.

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
C(H_i\mid E)=\lVert P_i|\Psi\rangle\rVert^2.
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

What is offered, then, is a conditional reduction, and its conditions should be kept in view. It assumes that squared norm — and not another function of amplitude — is the physically privileged measure, a claim defended on dynamical and symmetry grounds rather than read off the abstract notion of measure (§3.6). It assumes that indexical self-locating credence is a coherent attitude in a deterministic branching world, against a serious objection that it is not (§14.6). And it inherits, undissolved, the metaphysical discomfort of fully real low-measure observers (§14.3). Granting these, the Born rule is not a further postulate but a consequence; withholding any of them, the derivation lapses. The contribution is to have separated these commitments cleanly enough that each can be accepted, rejected, or improved on its own.

## References

Albert, David Z. “Probability in the Everett Picture.” In Saunders, Barrett, Kent, and Wallace (eds.), *Many Worlds? Everett, Quantum Theory, and Reality*. Oxford University Press, 2010.

Busch, Paul. “Quantum States and Generalized Observables: A Simple Proof of Gleason’s Theorem.” Physical Review Letters 91, 120403, 2003.

Carroll, Sean M., and Charles T. Sebens. “Many Worlds, the Born Rule, and Self-Locating Uncertainty.” arXiv:1405.7907.

Deutsch, David. “Quantum Theory of Probability and Decisions.” Proceedings of the Royal Society A 455, 1999.

Everett, Hugh. “‘Relative State’ Formulation of Quantum Mechanics.” Reviews of Modern Physics 29, 1957.

Gleason, Andrew M. “Measures on the Closed Subspaces of a Hilbert Space.” Journal of Mathematics and Mechanics 6, 1957.

Greaves, Hilary. “Understanding Deutsch’s Probability in a Deterministic Multiverse.” Studies in History and Philosophy of Modern Physics 35, 2004.

Hanson, Robin. “Mangled Worlds.” 2003.

Kent, Adrian. “Against Many-Worlds Interpretations.” International Journal of Modern Physics A 5, 1990.

Kent, Adrian. “One World Versus Many: The Inadequacy of Everettian Accounts of Evolution, Probability, and Scientific Confirmation.” In Saunders, Barrett, Kent, and Wallace (eds.), *Many Worlds?* Oxford University Press, 2010.

Saunders, Simon, Jonathan Barrett, Adrian Kent, and David Wallace, eds. *Many Worlds? Everett, Quantum Theory, and Reality*. Oxford University Press, 2010.

Sebens, Charles T., and Sean M. Carroll. “Self-Locating Uncertainty and the Origin of Probability in Everettian Quantum Mechanics.” British Journal for the Philosophy of Science / arXiv:1405.7577.

Vaidman, Lev. “Probability in the Many-Worlds Interpretation of Quantum Mechanics.” In Ben-Menahem and Hemmo (eds.), *Probability in Physics*. Springer, 2012.

Wallace, David. *The Emergent Multiverse: Quantum Theory According to the Everett Interpretation*. Oxford University Press, 2012.

Wallace, David. “A Formal Proof of the Born Rule from Decision-Theoretic Assumptions.” arXiv:0906.2718.

Zurek, Wojciech H. “Environment-Assisted Invariance, Entanglement, and Probabilities in Quantum Physics.” Physical Review Letters 90, 2003.
