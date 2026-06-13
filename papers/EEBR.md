# Crossing the Threshold: Everettian Emergence and the Born Rule

## Abstract

Lela (2026) proves a conditional uniqueness theorem: on robust record
sectors, the quadratic assignment is the only non-negative
refinement-stable induced weight, given two structural conditions —
internal equivalence of refinement profiles, and admissible binary
saturation — with additivity carried by disjoint continuation bundles
rather than the projector lattice. Lela leaves open whether physical
systems meet the saturation threshold, and offers no epistemic reading of
the weight. We show that Everettian quantum mechanics crosses the
threshold. Saturation is established constructively: decoherence-stabilized
record sectors in the universal Hilbert space admit non-demolition refining
processes realizing every norm-compatible profile (Theorem 1), answering
Lela's open question. We then argue that the theorem's remaining condition
is not a posit but a consequence of Everettian emergence: decoherence
constitutes the dynamical autonomy of record structure, and a weak
epistemic principle — rational self-locating weight cannot track features
screened from all possible evidence — converts autonomy into
profile-supervenience. The relocated non-contextuality that a modal reading
of saturation requires is faced openly and discharged by an
Everett-exclusive argument: choices among refining contexts can be
delegated to branching processes, rendering every context actual in a
sibling decision-branch, so cross-context consistency is diachronic
coherence among actualities. The result closes the loop on Everett's
original 1956 derivation of the squared-amplitude measure, supplying the
justifications he stipulated. A final ledger itemizes what is still
assumed: strictly weaker posits than those of our companion analysis, with
the exponent now purchased by theorem.

---

## 1. Introduction

In 1956 Everett derived the squared-amplitude measure from two
stipulations: that the measure of a branch at one time equal the sum of the
measures of its successors, and that the measure be a function of branch
amplitude alone. The derivation was sound; the stipulations were the
problem, and seventy years of criticism — from DeWitt's reviewers to
Barrett's reconstruction — has consisted largely of observing that they
were stipulations. The decision-theoretic program of Deutsch and Wallace,
the envariance argument of Zurek, and the self-location argument of Sebens
and Carroll are best read as attempts to earn what Everett assumed, and the
critical literature — Albert, Kent, Baker, Dawid and Thébault, Dawid and
Friederich — as demonstrations that each attempt buys the conclusion with
premises of comparable strength differently disguised.

In a companion paper (BMSL) one of us argued that the honest position is a
conditional reduction: the Born rule in Everett rests on exactly two
posits — a physical-measure claim (squared norm is the weight) and an
epistemic bridge (rational self-locating credence tracks the weight) — and
that the literature's derivations relocate rather than discharge them. The
present paper reports a development that changes the bookkeeping. Lela
(2026) has proven a structural uniqueness theorem whose form is, in
retrospect, a rigorization of Everett's original argument: on robust record
sectors, with additivity carried by disjoint continuation bundles, the
quadratic assignment is the unique non-negative refinement-stable induced
weight — conditional on two explicitly stated structural conditions. The
theorem is interpretation-neutral and deliberately silent on whether
physical systems satisfy its conditions and on why anyone's credence should
care about its weight.

Our thesis is that Everettian quantum mechanics, and perhaps only
Everettian quantum mechanics, crosses Lela's threshold — and that crossing
it converts BMSL's first posit from an assumption into a theorem-mediated
consequence of emergence, while shrinking the second to its minimal core.
The argument has a technical half and a philosophical half. The technical
half (Sections 3–4) establishes admissible binary saturation for
decoherence-stabilized record sectors in the universal Hilbert space, by a
construction whose physics is deliberately familiar — the tunable quantum
coin of the Everettian literature — and whose contribution is the
clause-by-clause verification against Lela's functional definitions,
answering the question he explicitly leaves open. The philosophical half
(Sections 5–8) begins with a confession: the saturation theorem has force
only under a modal reading of "admissible," and the modal reading relocates
Gleason's contested non-contextuality premise rather than eliminating it.
We decompose the relocated debt, show that two of its three components are
respectively classical-grade and theorem-grade, and devote the crux of the
paper to the third: arguing that internal equivalence — the claim that
weight sees only internally accessible refinement structure — follows from
what Everettian emergence is, given one weak and independently motivated
epistemic principle, and that the final cross-context residue admits an
argument unavailable to any one-world theory, because in Everett the
contexts are all actual.

Throughout, we hold ourselves to the accounting standard of the companion
paper. Every premise is named when introduced and collected in a closing
ledger (Section 12). The conclusion is conditional, and the conditions are
individually attackable; we think this is a virtue, and we have tried to
make each condition fail interestingly rather than vaguely. The reader who
rejects the conclusion should, by the end, be able to say exactly which
line item she declines to pay.

## 2. The threshold theorem

We restate Lela's result in the form we need; definition numbers are his.

A *robust record sector* is a closed subspace $R$ of a Hilbert layer $H$
satisfying three functional conditions (his Definition 1): internal
discriminability ($R$ represents record content internally readable and
distinguishable from admissible alternatives), short-horizon persistence
(the content survives micro-recodings and one-step admissible evolution),
and refinement closure (next-step alternatives are representable by
admissible orthogonal refinements). For a global state $|\Psi\rangle$, each
sector carries a state-relative *continuation bundle* $C_\Psi(R)$ — the
admissible forward developments in which $R$'s content is realized — and a
non-negative, finitely additive valuation $\mu$ on disjoint bundles induces
the weight $W_\Psi(R) := \mu(C_\Psi(R))$. An *admissible orthogonal
refinement* $R = R_1 \oplus R_2$ (his Definition 3) requires the $R_i$ to
be robust sectors representing mutually exclusive readable alternatives,
and — clause (iii), on which much will turn — that every continuation in
$C_\Psi(R)$ fall under exactly one $R_i$. His Continuation Partition Lemma
then makes $W$ automatically additive over admissible refinements:
refinement-stability is inherited, not postulated.

The theorem: if, further, (Condition 1, *internal equivalence*) sectors
with identical admissible binary refinement profiles carry identical
weight, and (Condition 2, *admissible binary saturation*) every pair
$(r_1, r_2)$ with $r_1^2 + r_2^2 = \lVert \Pi_R|\Psi\rangle\rVert^2$ is
realized by some admissible refinement, then
$W_\Psi(R) = c\,\lVert \Pi_R|\Psi\rangle\rVert^2$ for a constant
$c \geq 0$; normalization yields the Born form. The proof is a profile reduction followed by the
Pythagorean functional equation and a Cauchy-type lemma; the exponent $2$
is contributed entirely by the Pythagorean relation among orthogonal
components. A supplementary proposition weakens exact saturation to dense
saturation plus continuity of the profile function.

Three features matter for what follows. First, the additive carrier:
additivity lives on disjoint sets of continuations, motivated by the same
exclusivity that grounds classical probability on mutually exclusive
events — no lattice structure, no betting behaviour, no symmetry postulate.
The philosophically contested content of Gleason-type routes has not
vanished, but it has migrated into Conditions 1 and 2, which is precisely
where this paper operates. Second, Lela's own flags: whether physically
relevant systems in dimension greater than two satisfy saturation is, he
writes, an open structural question, with decoherence-stabilized pointer
sectors the natural candidates; and the theorem performs no ontological or
epistemic interpretation of its weight. Third, the genealogy. Everett's
1956 derivation demanded that the measure of a trajectory equal the sum of
the measures of its branches and that it depend on branch amplitude alone;
diachronic additivity over continuations plus amplitude-dependence is, in
modern dress, bundle-additivity plus internal equivalence. Lela's theorem
rigorizes the uniqueness half of Everett's argument. What was never
supplied — by Everett or, we will argue, by his successors except at
equivalent cost elsewhere — is the justification of the premises. Supplying
it is this paper's business.

## 3. The Everettian record layer and one structural assumption

We now specialize: the record layer is the universal Hilbert space $H$,
the state $|\Psi\rangle$ the universal state, and record sectors are
macroscopic — $R$ is spanned by all microstates compatible with some
definite,
decoherence-stabilized record content: a pointer reading, a memory
configuration, an environmental imprint.

Two consequences of the specialization do real work. There is no
enlargement problem: the textbook realization of a generalized measurement
adjoins an ancilla and dilates to a larger space, and under an operational
reading of Lela's framework this obstructs saturation — a refinement
obtained by dilation refines a lifted sector in
$H \otimes H_{\mathrm{anc}}$, not the sector $R$ that Condition 2
quantifies over. In the universal layer the obstruction dissolves, because
every ancilla, apparatus, and environmental degree of freedom is already
inside $H$: the dilation space is not adjoined but
occupied, and what follows is not an embedding argument but a description
of physically available internal processes. This advantage is exclusive to
readings on which $H$ is universal; no operational construal of the theorem
can claim it. And macroscopic sectors are never too thin to refine: record
content constrains a coarse macrovariable and leaves essentially everything
else free.

The little the construction needs beyond this we package as a named
premise.

**Ancilla Availability (AA).** Every decoherence-stabilized record sector
$R$ contains an ancilla: a subsystem $A$ with orthogonal pointer states
$|a_0\rangle, |a_1\rangle$ such that (i) the record content defining $R$ is
insensitive to $A$'s pointer value — $\Pi_R$ commutes with every operator
on $A$; (ii) in the component $|\varphi_R\rangle := \Pi_R|\Psi\rangle$, $A$
stands in the ready state $|a_0\rangle$, uncorrelated with the remaining
degrees of freedom; (iii) $A$'s pointer basis is environmentally monitored,
so pointer superpositions decohere on timescales short relative to the
record's persistence horizon, with redundant imprinting.

AA is a substantive premise and is priced as one (Section 12), but it is
mild in the way a premise about macroscopic physics should be: it says that
inside any macroscopic record there is room for one more stable bit the
record does not yet constrain. A world where AA failed would be one in
which some record sector had exhausted the universe's capacity for further
stable differentiation — no spin to flip, no mode to populate, no register
to write — which is not our world and not any world in which experimental
physics is possible. One honest qualification: clause (ii) is
state-relative — a claim about the actual universal state restricted to
$R$, not about all states — and it can fail for contrived $|\Psi\rangle$.
Our results are
stated for sectors satisfying AA; Section 10 notes that the credence
application only ever invokes observer-containing sectors, for which AA is
uncontentious.

## 4. The Saturation Theorem

Lela's Condition 2 demands that every norm-compatible binary profile be
realized by an admissible refinement, and he is explicit that whether
physical systems meet this threshold above dimension two is open, with
decoherence-stabilized sectors the natural candidates. This section answers
the question affirmatively for the Everettian layer. The construction is
deliberately humble — the tunable quantum coin that appears in Deutsch's
equal-amplitude decompositions, Zurek's fine-grainings, and Sebens and
Carroll's branch-splittings. The contribution is not the device but the
verification, clause by clause, that its output satisfies Lela's
definitions: that verification converts a familiar Everettian manoeuvre
into the discharge of a published theorem's premise, and clause (iii) of
his Definition 3 will exact a philosophical price (Section 5) that casual
uses of the device have never had to pay.

**Lemma 1 (Tunable non-demolition refinement).** Let $R$ satisfy AA with
$|\varphi_R\rangle \neq 0$. For every $\theta \in [0, \pi/2]$ there exist a
unitary $U_\theta$ and subspaces $R_1(\theta), R_2(\theta) \subseteq R$
such that: (i) $U_\theta$ acts only on $A$, hence $[U_\theta, \Pi_R] = 0$
and $U_\theta$ preserves every record sector whose content is
$A$-insensitive; (ii) writing $|\Psi'\rangle = U_\theta|\Psi\rangle$, we
have $R = R_1(\theta) \oplus R_2(\theta)$ with $R_i(\theta)$ the sub-sector
of $R$ carrying $A$-pointer value $a_{i-1}$, and
$\lVert \Pi_{R_1(\theta)}|\Psi'\rangle\rVert = \cos\theta \cdot \lVert\varphi_R\rVert$,
$\lVert \Pi_{R_2(\theta)}|\Psi'\rangle\rVert = \sin\theta \cdot \lVert\varphi_R\rVert$;
(iii) after the monitoring of AA(iii), the pointer alternatives within $R$
are decoherent: interference between the two components of $|\Psi'\rangle$
has no record-functional effect over the persistence horizon.

*Proof.* By AA(ii), $|\varphi_R\rangle = |a_0\rangle \otimes |\chi\rangle$
for some $|\chi\rangle$ in the complementary factors of $R$'s support. Let
$U_\theta$ rotate $A$:
$U_\theta|a_0\rangle = \cos\theta|a_0\rangle + \sin\theta|a_1\rangle$
(identity elsewhere). Then
$U_\theta|\varphi_R\rangle = (\cos\theta|a_0\rangle + \sin\theta|a_1\rangle) \otimes |\chi\rangle$.
Set $R_i(\theta) := (\text{pointer eigenspace of } a_{i-1}) \cap R$; these
are orthogonal and their direct sum exhausts $R$ restricted to the pointer
span, which suffices since the construction iterates within either summand.
Claim (i): $U_\theta$ is local to $A$, and $\Pi_R$ commutes with
$A$-operators by AA(i); in particular
$\Pi_R|\Psi'\rangle = U_\theta \Pi_R|\Psi\rangle$, so
$\lVert\Pi_R|\Psi'\rangle\rVert = \lVert\varphi_R\rVert$ — the refinement is
non-demolition with respect to the coarse record. Claim (ii) is read off
the rotated component. Claim (iii) is AA(iii). ∎

The map
$\theta \mapsto (\cos\theta, \sin\theta)\cdot\lVert\varphi_R\rVert$ is a
continuous surjection onto the full profile set, so every norm-compatible
profile is realized exactly; should implementability of every $\theta$ in
the continuum be doubted, Lela's
dense-saturation-plus-continuity variant stands ready, and continuity here
is barely an additional assumption — realized norms vary continuously with
a continuously tunable coupling.

**Lemma 2 (Admissibility).** Under AA, the decomposition
$R = R_1(\theta) \oplus R_2(\theta)$, taken after the monitoring of
AA(iii), is an admissible orthogonal refinement of $R$ relative to
$|\Psi'\rangle$, and each $R_i(\theta)$ is a robust record sector.

*Proof.* Definition 1(i), internal discriminability: the pointer states are
orthogonal and, by AA(iii), redundantly imprinted in the environment.
Redundancy is the operative point. Lela glosses his conditions as
functional rather than microscopic: what is required is that the record be
internally *readable*, not actually read. Quantum Darwinism supplies
exactly this — the pointer value is recoverable from many disjoint
environmental fragments, so the discrimination is available to internal
processes generically and cheaply. A strict reading on which readability
demands actual access would disqualify Lela's own paradigm cases
(unobserved pointer sectors); we take the functional reading as intended.
Definition 1(ii), persistence: pointer decoherence with environmental
redundancy is the textbook mechanism of record stabilization; the
identifying content of $R_i(\theta)$ survives micro-recodings because the
environment continuously re-records it. Definition 1(iii), closure: each
$R_i(\theta)$ itself satisfies AA — macroscopic sectors contain many
ancillas, and consuming one leaves the supply intact — so refinement
iterates. For Definition 3: clauses (i)–(ii) are immediate. Clause (iii) —
every continuation of $C_{\Psi'}(R)$ falls under exactly one $R_i(\theta)$,
none outside — holds because the pointer basis is complete on its span and
decoherent: every forward development of the $R$-component carries a
definite stable
pointer record; exclusivity by orthogonality plus suppression of
re-interference, exhaustiveness by completeness. ∎

**Theorem 1 (Everettian binary saturation).** Every decoherence-stabilized
record sector satisfying AA admits, for every $(r_1, r_2)$ with
$r_1^2 + r_2^2 = \lVert\varphi_R\rVert^2$, an admissible orthogonal
refinement realizing that profile. Hence the Everettian universal layer
satisfies admissible binary saturation on such sectors, and — granting
Condition 1, to which Sections 6–8 are devoted — Lela's theorem applies:
$W_\Psi(R) = c\,\lVert\Pi_R|\Psi\rangle\rVert^2$.

*Proof.* Set $\theta = \arccos(r_1/\lVert\varphi_R\rVert)$; apply Lemmas
1–2. ∎

**Corollary.** Lela's open question — physical instances of the saturation
threshold above dimension two — has an affirmative answer in the Everettian
universal layer, witnessed by ordinary system–ancilla–environment dynamics.

The reader will have noticed what the proof of Theorem 1 quietly did: it
*chose* a $\theta$. For a different profile it would have chosen a
different $\theta$, and the processes $U_\theta$ for distinct $\theta$ are
mutually incompatible — at most one of them is what actually happens.
Saturation, as just established, is a claim about what the dynamics can do,
not about what it does do.
Everything in this paper that is philosophically expensive is contained in
that observation, and we now stop deferring it.

## 5. What saturation costs: the modal reading

Suppose admissibility quantified only over refinements the actual forward
dynamics of $|\Psi\rangle$ enacts. Then the admissible class for a given
sector contains at most one non-trivial binary profile — whichever process
occurs — and Lela's own Remark 7 shows what follows: a sparse refinement
class supports only fragmentary instances of the functional equation, which
do not force the quadratic form. His counterexample is explicit — for an
equal-split-only class, every weight of the form
$g(s) = s^2(1 + \varepsilon \sin(4\pi \log_2 s))$ is refinement-stable —
and it transfers verbatim. On the actualist reading, Theorem 1 is true but
useless: it
exhibits, for each profile, a possible process, while the actualist's class
collects only enacted ones. Uniqueness fails; anti-Born weights survive.

So the theorem has force only under a modal reading: a refinement is
admissible if some available physical process would realize it, where
"available" means implementable by unitary dynamics acting within the
sector compatibly with its record structure — the precise content of
Lemmas 1–2. The functional equation is then instantiated across
counterfactual contexts: its two sides are evaluated in incompatible
would-be histories, and it constrains a single weight function across all
of them at once.

We state plainly what this is: non-contextuality, in modal dress. The
demand that one fixed $W$ satisfy the partition law for every
counterfactual refinement simultaneously is the bundle-formulation analogue
of demanding
that a frame function assign a projector the same value in every orthogonal
decomposition containing it. The route through continuation bundles did not
eliminate Gleason's contested premise; it relocated it, one level down,
from a lattice axiom to a cross-context identity claim. A paper in the
tradition of pricing its assumptions must say so before its referees do.

Saying so prepares an exact bill, for the modal reading decomposes the
theorem's premises into three items of sharply different standing. *Bundle
additivity* is innocent: within any one context, the continuations
realizing $R_1(\theta)$ and $R_2(\theta)$ are disjoint sets, and the weight
of a disjoint union is the sum of the weights — classical-grade
exclusivity, no lattice,
no betting, no symmetry. *Modal richness* — that the counterfactual
contexts exist in sufficient supply — is no longer a posit but Theorem 1: a
physical fact about what unitaries, ancillas, and monitoring can jointly do
inside a macroscopic sector. It could have failed: were non-demolition
refinement dynamically impossible, the route would end here; that the
physics cooperates is a discovery about the theory, not a stipulation
within it. *Cross-context identity* — that it is one and the same weight
function across the contexts — is where the entire relocated debt
concentrates, and within Lela's framework it is precisely the work of his
Condition 1. Strip that condition away and the modal reading collapses back
into the actualist one, pathologies and all.

The bookkeeping consequence shapes the rest of the paper: of three
premises, one is classical-grade, one is now a theorem, and one carries
everything. Sections 6–8 are therefore not one front among several but the
crux of the climb. Everett, in 1956, derived the squared-amplitude measure
from diachronic additivity over continuations together with the bare
stipulation that the measure depend on branch structure alone; his critics
have observed ever since that the stipulation is what needed earning. This
section has located that old debt with new precision. The next three
attempt to pay it.

## 6. Dynamical autonomy without probability

The foundation must be a version of branch autonomy that owes nothing to
probability — otherwise the circularity charges of Baker and of Dawid and
Thébault end the argument at its first step, and we state their objection
at full strength. Baker: proofs of decoherence proceed via reduced density
matrices and expectation values whose physical interpretation presupposes
the Born rule. Dawid and Thébault: discarding interference terms because
they are small presupposes that small amplitude means small significance —
an implicitly probabilistic judgment — so decoherence-defined branching
cannot non-circularly ground a probability derivation.

The claim we need is deliberately limited. Call it autonomy:

**(AUT)** After decoherence, the record-functional evolution of a sector
factorizes — which discriminations are internally available, which records
persist, which continuation structure obtains within $R$ develops as it
would were the companion components of $|\Psi\rangle$, and the choice among
available external contexts, absent or otherwise.

AUT concerns record-functional structure only; exact microstates are not
autonomous, interference terms being small rather than zero. The claim is
that their record-functional effect is null over the persistence horizon —
which is all that Section 7 will need.

Following Franklin's reply to Dawid and Thébault, AUT can be evidenced
without probabilistic premises. The effects that establish emergence are
dynamical: the stability of quasiclassical patterns, the persistence of
records, the suppression of re-interference as a feature of the flow on
Hilbert space. None of these requires expectation values to state; where
textbook derivations deploy density-matrix methods, these are calculational
conveniences, and the underlying claims can be cast as perturbation bounds
on vectors. One premise, however, hides in "suppression" and "small," and
the honesty this paper aspires to requires dragging it into the light:

**(NG)** Dynamical relevance is norm-graded: norm-small perturbations have
proportionally small record-functional effects.

Is NG the circular premise renamed? We argue not, on the ground that the
norm topology is the dynamics' own. Unitary evolution is an isometry of the
norm; its continuity, its perturbation theory, and the stability results of
decoherent-histories theory are all stated in it; no rival functional has
any dynamical standing — there is no alternative topology in which the
theory's stability theory can so much as be formulated. Privileging the
norm as the gauge of dynamical relevance is not an interpretive choice
calibrated against statistics; it is reading the Schrödinger equation's
native modulus of continuity off the equation. We note with pleasure that
the sharpest statement of this point in the literature belongs to a rival
program: Saunders's continuity-in-norm requirement, in his rehabilitation
of branch counting, derives, as he says, from the norm on Hilbert space —
we repurpose the observation and acknowledge its source.

Two clarifications complete the section. First, what is not claimed: no
dynamical office is asserted for the *square* of the amplitude. NG concerns
the norm as a grading; the exponent $2$ enters this paper exactly once, in
the Pythagorean relation inside Lela's functional equation. The circularity
that threatens dynamical defenses of $|a|^2$ — that the square's dynamical
credentials are established through Born-presupposing statistics — is
therefore not inherited here but dissolved: the squaring is done by
geometry, not by physics. Second, the residual exposure: a determined
critic may insist that grading record-relevance by norm is still a
significance judgment. Our reply — that NG is a structural claim checkable
as perturbation bounds within the formalism, whereas the circular premise
is an interpretive claim about importance — is an argument, not a theorem,
and the critic's strongest rejoinder (that record-functional effect does
not matter absent probability) would equally undercut every rival program.
NG is logged in the ledger as challenge-shaped: the challenge being to
exhibit any rival grading with dynamical standing.

## 7. Evidential internalism and the derivation of internal equivalence

The epistemic principle we need is weak, and its weakness is the point.

**(EI)** The weight that rational self-locating credence tracks cannot
depend on features from which the agent's total possible evidence is
dynamically screened.

Here "total possible evidence" means the full record-functional structure
internally accessible within the sector over its horizon, and the modality
of "possible" is the same modality introduced in Section 5 and certified in
Section 4: implementable by internal dynamics. The paper runs on one modal
notion throughout; a reader who has accepted the modal reading of
saturation has already accepted the modality EI quantifies over.

EI is best located by contrast with Elga's indifference principle, of which
it is the weak sibling. Elga: evidence-identical centered predicaments
receive equal credence — a principle independently endorsed in formal
epistemology, which in Everett yields branch-counting and perishes under
refinement, as both the companion paper and Sebens and Carroll's diagnosis
agree. EI demands far less: not equal credence, but no weight difference
without an evidence-structural difference. Indifference legislates the
values of credence and perishes by them; supervenience legislates only the
dependency base and lets a uniqueness theorem dictate the values. We are
asking for less than the literature already grants elsewhere, and letting
Lela's theorem do the work indifference was too strong to survive doing.

The derivation of Lela's Condition 1 is now a short chain. By AUT, the
record-functional future of a sector is screened from companions and
contexts. By Theorem 1, the admissible binary refinement profile of a
sector is exactly the inventory of its possible internal evidence: every
profile element is realizable as an actual record by an internal process —
this is where the technical half pays epistemic rent. Hence two situations
with identical profiles have identical record-functional futures: the same
discriminations available, the same continuation structure, the same
possible evidence trajectories. By EI, weight cannot differ between them.
That is Condition 1, no longer posited: what Lela stipulates as internal
equivalence, autonomy plus evidential internalism derive as
profile-supervenience. A weight that distinguished profile-identical
situations would track what Lela calls representational surplus —
differences that make no difference to any record, hence to any possible
evidence, hence to anything credence could answer to.

Two objections, faced now and revisited in Section 11. The externalist asks
why weight should not track evidence-transcendent features, as objective
chance is sometimes held to do. In Everett there is nothing for the
transcendent feature to be: by AUT, differences beyond the profile are
surplus, and a weight sensitive to surplus could never be evidentially
vindicated or refuted — adopting it severs credence from confirmation
entirely, gutting the confirmation structure that any empiricist account of
quantum theory's success requires. This is a strong argument and not a
theorem; it is ledger item (a). The gerrymander objection asks how profiles
are individuated; we inherit Lela's individuation and note that Theorem 1
shows it maximally fine for Everettian sectors — every norm-compatible
profile is realized — so nothing finer is internally accessible and
anything coarser ignores accessible structure. And the reader who suspects
that profile-supervenience is epistemic separability in new clothing is
half right; the difference, developed in Section 11, is that it arrives
here with a derivation where ESS arrived as a posit, and with its carrier
fixed by a theorem where ESS's carrier was fixed by calibration.

## 8. Cross-context identity: every context is somebody's actual

Section 7 delivers that weight is a function of the profile alone. The
modal residue of Section 5 remains: why one and the same function across
the counterfactual refining contexts $\theta$ — the cross-context identity
that makes the functional equation bind globally rather than context by
context?

The first argument is an application of what we already have. By Lemma
1(i), contexts differing in which $U_\theta$ would be applied differ in
nothing
with record-functional footprint on the parent sector: the coarse record,
its profile, its continuation structure are point-identical across
contexts — that is what non-demolition means. A weight varying with context
would vary without any profile difference, in direct violation of
profile-supervenience. A reader who balks only here is balking at EI, and
should be routed back to Section 7.

The second argument is the one no one-world theory can make. In Everett the
agent and her choosing are physical systems, and a choice among refining
contexts $\{\theta_i\}$ can always be delegated to a quantum randomizer —
an
ancilla-driven branching process, available whenever AA holds, i.e. always.
Under delegation the choice event is itself a branching event, and every
context is enacted in some sibling decision-branch: the "counterfactual"
contexts are all actual. The demand for one weight function across contexts
then becomes the demand that a pre-decision agent's weight for the parent
record not depend on which of her sibling successors enacts which
refinement — diachronic coherence under one's own branching, a consistency
constraint among actualities rather than a stipulation about possibilia.

**Lemma 3 (Decision-branch consistency).** Let a pre-decision agent face a
delegated branching choice among contexts $\{\theta_i\}$, each satisfying
Lemma 1. Then profile-supervenience together with the commutation clause of
Lemma 1(i) entail that the induced weight of the parent sector $R$ is
identical in every sibling decision-branch.

*Proof.* In each sibling branch the parent profile is preserved: by
$[U_{\theta_i}, \Pi_R] = 0$, the parent norm and its admissible refinement
structure are untouched by the enacted refinement. The profiles are
therefore
identical across siblings, and by Condition 1 — as derived in Section 7 —
the weights are identical. ∎

Note what the proof does not use: at no point are the *measures* of the
sibling decision-branches invoked — only their existence and their record
structure. The argument is measure-free by construction, which is worth a
deliberate sentence because it is where a circularity hunter will look
first: a justification of the Born rule that needed Born weights over the
randomizer's outcomes would be the old circle; Lemma 3 needs only that the
outcomes are there.

The bridge from delegated to deliberate choices is one more application of
EI. An agent whose parent-sector weight depended on whether she chose
$\theta$ herself or let a quantum coin choose would treat the provenance of
the
context — an evidentially idle fact, leaving no trace in any parent-sector
record — as weight-relevant. Provenance-sensitivity violates
profile-supervenience exactly as context-sensitivity did. This move is kin
to Wallace's branching-indifference arguments, and the kinship should be
acknowledged with the difference stated: his indifference is a rationality
axiom within a decision theory; ours is a consequence of a principle
already in play, purchased once in Section 7 and merely spent here.

Three scope guards. What has been earned is non-contextuality of weight
assignments over record sectors, not of value assignments;
Kochen–Specker contextuality of hidden values is untouched and irrelevant,
Everett having no hidden values. The argument needs branching choices to be
available, not universal: delegation suffices, and AA keeps a randomizer
always in stock. And the staked ground should be credited precisely: Bub
and Pitowsky observed that the Deutsch–Wallace rationality constraints are
justifiable only on the Everett interpretation, where all outcomes occur
relative to branches — the germ of the present argument, grown in
decision-theoretic soil; and it has been noted that in Everettian terms
noncontextuality amounts to branch-dependence, an assumption flagged in
that literature as exactly what the objectors reject. Neither develops the
choice-as-branching-event argument; Wallace's noncontextual-inference
theorem reaches a cousin of our conclusion with rationality axioms this
route does not need. Gleason had to posit non-contextuality, and
hidden-variable theorists may always reject it by denying counterfactual
definiteness. In Everett it is a coherence constraint among actualities:
every context is somebody's actual.

## 9. Assembly

**Theorem 2 (Born weight at the emergence threshold).** Grant: (i)
non-probabilistic emergence of decoherent branching — AUT, supported by NG
(Section 6); (ii) evidential internalism — EI (Section 7); (iii) that the
agent's self-locating credence over admissible record alternatives exists
and is finitely additive over exclusive alternatives. Then for every
decoherence-stabilized, AA-satisfying record sector $R$, rational
self-locating credence is

$$
C(R) = \frac{\lVert\Pi_R|\Psi\rangle\rVert^2}{\lVert\Psi\rVert^2}.
$$

*Proof.* Sections 6–8 derive Lela's Condition 1 from (i) and (ii), with
Lemma 3 discharging the cross-context identity that the modal reading of
Condition 2 requires; Theorem 1 establishes Condition 2 for AA-sectors.
Premise (iii) makes credence a non-negative finitely additive valuation on
disjoint admissible continuation bundles — an extensive bundle valuation in
Lela's sense — whose induced sector weight, satisfying Conditions 1 and 2,
is by his theorem $c\,\lVert\Pi_R|\Psi\rangle\rVert^2$. Normalizing over a
complete admissible decomposition fixes $c = \lVert\Psi\rVert^{-2}$. ∎

The logical form deserves emphasis: conditional, with conditions
individually motivated and individually attackable — the methodology of the
companion paper, retained. What has changed is what the conditions are.

## 10. The slimmed bridge

The companion paper's epistemic bridge, MCSL, asked the agent to align
credence with *the* objective measure — which obliged the companion paper
to defend squared norm's claim to be the measure, the burden its Section
3.6 carried uneasily. The present route asks for less, and the difference
is the paper's payoff. The bridge now consists of premise (iii) of Theorem
2 alone: self-locating credence exists, and is additive over exclusive
admissible alternatives. Nothing in the bridge selects the quadratic form;
selection is performed by the uniqueness theorem, operating on conditions
that Sections 4 and 6–8 derived from the physics and one weak epistemic
principle. The companion paper's Section 14.2 objection — why this measure
rather than another? — thereby receives a structural answer: there is no
other for credence to be, once credence supervenes on what evidence could
ever show and the dynamics supplies refinements in every proportion.

Two inheritances are recorded rather than re-litigated. The question
whether self-locating credence in a branching universe is well-posed at
all — whether there is a coherent epistemic predicament between branching
and observation for credence to address — is the companion paper's Section
14.6, defended there via the distinction between indexical and prospective
registers; it enters here as premise (iii) and is priced in the ledger as
item (c). And the restriction to AA-satisfying sectors costs the credence
application nothing: an agent's predicament always concerns
observer-containing sectors — sectors compatible with her own records
existing — and such sectors satisfy AA on any non-contrived universal
state, containing as they do the most record-saturated macroscopic
structure there is.

## 11. Stress tests

**11.1 The Dawid–Friederich transfer.** Their case against Sebens and
Carroll has a precise anatomy: a plausible general principle (epistemic
separability), a specialization to quantum mechanics requiring a choice of
formal carrier for the local epistemic situation, and the demonstration
that the chosen carrier — the reduced density matrix — has no motivation
independent of the empirical success of Born-rule physics. Calibration, not
derivation. Run against the present route, the transfer fails at the
specialization step, and it is worth saying exactly why. Our general
principle, EI, is independently motivated, non-quantum, and strictly weaker
than a principle (Elga's) the formal-epistemology literature already
endorses. Our specialization — record-functional structure is the
admissible refinement profile, and the realizable profiles are exactly the
norm-compatible ones — is mediated by Theorem 1, a result proven from
unitarity, Hilbert geometry, and AA, not read off statistically vindicated
practice. The reduced density matrix wears Born weights on its diagonal;
the profile set wears only what unitary couplings can do. The hostile
reading — epistemic separability in new clothing — is therefore half right,
and the half matters: this is separability with a derivation, where ESS was
separability as posit; the clothing is a theorem.

**11.2 The circularity charges.** Handled in Section 6; the residue is
restated honestly. Against Baker: no reduced density matrices or
expectation values appear in AUT's support; against Dawid and Thébault: NG
is a structural claim about perturbation bounds, not a significance
judgment. The standing exposure is the challenge to exhibit a rival grading
of dynamical relevance with any dynamical standing; until one is produced,
NG stands as the only candidate the theory itself offers, and the ledger
records it as challenge-shaped.

**11.3 Saunders's rehabilitated branch-counting.** The most serious rival
route, and partly a creditor: his counting rule achieves convention-freedom
by a continuity-in-norm requirement, and we have repurposed his observation
that this requirement derives from the Hilbert norm itself. The difference
is bookkeeping. His route lets the measure enter through the topology that
individuates the branches to be counted, implicitly; ours names the
norm-gradedness premise, prices it, and lets the quadratic form be earned
by theorem rather than by count. Whether his implicit dependence is lighter
or heavier than our explicit one is a fair question for a referee; we
contend that an itemized bill beats an unitemized one at equal cost.

**11.4 The ad-hocness probe.** The suspicion that the package was
reverse-engineered to yield Born is answered by its exposure to failure. If
refining couplings necessarily disturbed parent records, Theorem 1 fails;
if decoherence did not screen contexts, Section 8's first argument fails;
if dynamical relevance were not norm-graded, Section 6 fails; if
self-locating credence is ill-posed, premise (iii) fails. Each component
can lose on structural or physical grounds, and none is tunable to save the
conclusion. Calibrated arguments do not take risks; this one takes four.

## 12. The ledger

The companion paper closed by pricing two posits. This paper closes by
showing the revised bill — all of it, including the small print.

| # | Premise | Where | Status |
|---|---------|-------|--------|
| a | Evidential internalism (EI) | §7 | Open posit. Rejection severs credence from confirmation (§7) — strong reply, not theorem. |
| b | Norm-gradedness (NG) | §6 | Open posit, challenge-shaped: no rival grading has dynamical standing. |
| c | Well-posed additive self-locating credence | §9(iii), §10 | Inherited from companion §14.6; untouched here. |
| d | Ancilla Availability (AA) | §3 | Local; mild for macroscopic sectors; state-relativity priced, defused for observer-containing sectors (§10). |
| e | Functional reading of "readable" | §4, Lemma 2 | Interpretive; strict reading would disqualify Lela's own paradigm cases. |
| f | Delegation-availability | §8 | Follows from AA; listed for completeness. |

Items d–f are local and, we have argued, defused where they arise; a
referee is nevertheless entitled to the full count, and the count is six,
not two. The headline comparison is with the companion paper's two posits:
*squared norm is the objective measure* and *credence tracks the measure*.
These are replaced by (a) and (c) — credence answers to possible evidence,
and credence exists and adds — which are strictly weaker, individually
motivated, and jointly silent on any exponent. The exponent 2 is purchased
nowhere in the ledger; it is purchased by the Pythagorean relation inside a
uniqueness theorem, which is to say by geometry. Everett stipulated in 1956
that the measure of a trajectory be the sum of the measures of its branches
and a function of their amplitudes alone, and was told for seventy years
that the stipulations were the problem. The stipulations were the problem.
We have tried to show that, in the one interpretation where every outcome
is somebody's actual, they were also payable.

---

## References (TO VERIFY — flagged items especially)

- Lela, M. (2026). The Born Rule as the Unique Refinement-Stable Induced
  Weight on Robust Record Sectors. arXiv:2603.24619.
- Everett, H. (1957). "Relative State" Formulation of Quantum Mechanics.
  Rev. Mod. Phys. 29, 454–462. [Also the 1956 long thesis for the
  additivity derivation — cite the DeWitt–Graham volume or Barrett–Byrne
  edition; VERIFY page numbers for the trajectory-measure passage.]
- Barrett, J. (2020?). Typical Worlds. arXiv:1912.05312. [VERIFY journal:
  Studies in HPS B?]
- Wallace, D. (2012). The Emergent Multiverse. OUP.
- Saunders, S. (2021). Branch-counting in the Everett interpretation.
  Proc. R. Soc. A 477: 20210600.
- Sebens, C. & Carroll, S. (2018). Self-locating Uncertainty and the Origin
  of Probability in Everettian Quantum Mechanics. BJPS 69(1), 25–74.
- Dawid, R. & Friederich, S. (2022). Epistemic Separability and Everettian
  Branches. BJPS 73(3). [axaa002]
- Dawid, R. & Thébault, K. (2015). Many Worlds: Decoherent or Incoherent?
  [VERIFY venue: Synthese 192?]
- Baker, D. (2007). Measurement Outcomes and Probability in Everettian
  Quantum Mechanics. Studies in HPS B 38, 153–169.
- Franklin, A. (2023/24?). Incoherent? No, Just Decoherent: How Quantum
  Many Worlds Emerge. Philosophy of Science. [VERIFY author first name,
  year, volume — arXiv:2501.16020.]
- Bub, J. & Pitowsky, I. (2010). Two Dogmas About Quantum Mechanics. In
  Saunders et al. (eds.), Many Worlds? OUP.
- Elga, A. (2004). Defeating Dr. Evil with Self-Locating Belief. PPR 69(2).
- Zurek, W. (2009). Quantum Darwinism. Nature Physics 5, 181–188.
- Busch, P. (2003). Quantum States and Generalized Observables: A Simple
  Proof of Gleason's Theorem. PRL 91, 120403. [Comparison only.]
- Gleason, A. (1957). Measures on the Closed Subspaces of a Hilbert Space.
  J. Math. Mech. 6, 885–893.
- [Author TBD] (2016). Quantum Probability as an Application of Data
  Compression Principles. arXiv:1606.06802. [VERIFY author.]
- [Author TBD] (2026). Summing to Uncertainty: On the Necessity of
  Additivity in Deriving the Born Rule. arXiv:2603.06211. [VERIFY authors.]
- Brown, H. & Ben-Porath, G. (2020). Everettian Probabilities, the
  Deutsch–Wallace Theorem and the Principal Principle. arXiv:2010.11591.
  [VERIFY published venue.]
- BMSL and the MCSL companion paper — cite per your own bibliography.
