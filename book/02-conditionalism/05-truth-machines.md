---
title: 'Truth Machines'
subtitle: 'From Leibniz to Tarski, Gödel, and Turing'
status: review
sources:
  - 177760320.truth-machines
  - 174125219.entangled-truths
---

Consider two statements: *2+2=4* and *it rained in Paris yesterday*. They feel like different kinds of thing. Deny the first and you seem to lapse into incoherence; deny the second and you are merely, perhaps, mistaken. The first appears to hold in every possible world; the second could easily have been otherwise. Nearly all of Western philosophy has treated this felt difference as a deep fact about reality — a fault line running between two domains of truth.

Leibniz drew the line most cleanly:

> "There are two kinds of truths: those of reasoning and those of fact. The truths of reasoning are necessary and their opposite is impossible; the truths of fact are contingent and their opposites are possible."

I want to use twentieth-century logic to qualify that line. Tarski, Gödel, Turing, and Chaitin did not jointly prove Conditionalism or abolish the distinction between necessary and contingent truth. Their results show, in different ways, that formal consequence, semantic truth, proof, computation, and resource-bounded knowability must be distinguished. Conditionalism is my philosophical interpretation of those distinctions.

## Leibniz's Two Kinds of Truth

Leibniz's taxonomy divided the intelligible world in two. **Truths of reasoning** are necessary: mathematical and logical truths whose negations entail contradiction. **Truths of fact** are contingent: empirical statements about the world whose negations are logically possible. Behind each kind stood a governing principle. The Principle of Non-Contradiction grounds necessity — no necessary truth can be denied without incoherence. The Principle of Sufficient Reason grounds contingency — every fact has an explanation, yet things might have been otherwise.

The scheme was enormously productive. It gave early modern philosophy a map for the boundary between mathematics and empirical science, and its descendants — Hume's relations of ideas versus matters of fact, Kant's analytic versus synthetic — organized epistemology for two hundred years. But the sharpness of the divide is an illusion born of categorical rigidity, and it takes only the Conditionalist recasting to see why.

## Necessity Is Framework-Relative

Conditionalism holds that truth evaluations require an interpretation and domain. Apply this to Leibniz's paradigm cases without confusing contextual dependence with material implication.

The inscription *2+2=4* requires conventions fixing its symbols. The corresponding arithmetic proposition follows in standard arithmetic and many weaker systems; it does not owe its truth to Indo-Arabic notation or uniquely to Peano's axioms. The law $\neg(P \wedge \neg P)$ is valid in classical logic, while paraconsistent systems revise what follows from contradiction. Framework-relative evaluation does not make a theorem historically contingent inside a fixed structure.

Our expressions and choices of formal framework have historical contingencies. Notation is invented, definitions fix structures, and inference rules differ across logics. Necessity survives as validity across the models or derivations fixed by a framework. Conditionalism explains the evaluation context; it does not reduce mathematical necessity to the sociology of choosing notation.

## Contingency Is Coherence-Dependent

Now run the recasting in the other direction. *It rained in Paris yesterday* becomes: *if* these meteorological and historical conditions obtained, *then* it rained in Paris yesterday. So far, so Leibnizian. But the fact itself is not free-floating. Without a logical-linguistic system supplying syntax and semantics, the statement collapses into noise. A consistency filter is already operating: self-contradictory claims cannot be admitted as facts at all. And the empirical claim gains its force only through its inferential role — by [cohering](03-the-three-levels-of-truth.md) with networks of other claims about weather stations, calendars, and the city of Paris.

Contingency, then, is *coherence-dependent* contingency. Leibniz's two domains turn out to lean on each other for their very intelligibility. Reasoning rests on an empirical substrate: notations, definitions, and rules emerge historically and are stabilized socially. Fact rests on a logical substrate: empirical claims require logical form to be intelligible and testable. Leibniz saw a boundary; there is actually a braid.

Alongside the modal distinction between necessity and contingency, there is a **continuum of epistemic and model stability**. Mathematical conclusions can be stable across many representations; weather claims depend on volatile conditions; scientific laws have domains and idealizations. That continuum is a difference of degree. The formal distinction between truth in all relevant models and truth in some remains a difference of kind.

That is the philosophical argument. The remarkable thing is that when logic was finally made rigorous enough to test Leibniz's picture from the inside, it delivered the same verdict.

## Syntax Without Meaning

Turing showed that a computation is a finite mechanical process operating on symbols according to formal rules. Crucially, those symbols are *syntactic tokens* — they have structure but no intrinsic semantics. A Turing machine manipulates "0011" and "⊢P→Q" identically, because from the machine's standpoint both are mere patterns in a tape alphabet. This is the original schism of modern logic: computation explains *form*, not *meaning*. If Leibniz's truths of reasoning were self-grounding, the machine grinding through their proofs would somehow contain their meaning. It doesn't. The meaning has to come from somewhere else.

## Tarski's Bridge

Tarski supplied the somewhere else. His formal definition of truth reads:

> A statement 'P' is true under an interpretation I if and only if P holds in the model I.

That semantic schema illustrates one premise Conditionalism emphasizes: truth in a formal language is defined relative to an interpretation or model. Even Tarski's “snow is white” schema distinguishes the mentioned sentence in one language from the condition stated in a metalanguage. Formally, the model-relative idea can be written:

$$\mathrm{Truth}(P \mid I)$$

For decidable fragments and supplied representations, a machine may evaluate the condition. Tarski's semantic account does not make truth mechanically decidable in general. Its lesson here is narrower: object language, metalanguage, and interpretation must not be silently conflated.

## Gödel's Limit, Chaitin's Boundary

Gödel proved that any consistent, effectively axiomatized formal system sufficiently expressive for arithmetic is incomplete: there are sentences for which it proves neither the sentence nor its negation. Calling a Gödel sentence “true” invokes an intended interpretation outside the proof system. This is a precise separation between provability and semantic truth, not a general theorem that semantics always escapes systems.

Chaitin later established incompleteness results using algorithmic information: a fixed formal system can determine only finitely much irreducible algorithmic information beyond a bound tied to the system. This connects provability and description complexity without making their boundaries simply identical.

## Computation as Interpretation

Now observe a possible implementation. A computation can implement an interpretation when a user or system supplies semantics for its inputs, program, and outputs. Given data $P$ and program $I$, the machine produces $O=I(P)$; what $P$, $I$, and $O$ mean is not fixed by that syntax alone.

This renders one part of Conditionalism operational: evaluation is a mapping under a specified interpreter. The trivial fact that some contrived interpreter can label a pattern “true” does not make the pattern true about a target. Interpretations remain answerable to reference, evidence, and use. An uninterpreted string is not yet a truth claim. ([When Statements Fail](04-when-statements-fail.md) examines that boundary.)

Shannon's theory deliberately excludes semantics: entropy measures uncertainty under a distribution, not meaning. Compact predictive reconstruction can support interpretation, but compression is neither necessary nor sufficient for meaning. Reference, causal use, and the practices of an interpreting system also matter. Truth should not be redefined as compression performance.

## No Ultimate Vantage

The natural objection is to ask for a master interpreter. Reasoning relies on rules and interpretations that can themselves be examined. Gödel and Turing establish specific limits on proof and computation; they do not prove the metaphysical claim that no ultimate vantage exists or that no system can model any aspect of itself. They motivate a narrower fallibilism: sufficiently rich formal and computational procedures cannot be assumed complete merely because they are internally specified.

When philosophers speak of "unconditional truth," they are implicitly assuming exactly such a vantage — a hidden universal interpreter, a divine Tarski model in which every statement gets its absolute verdict. Leibniz had a candidate for the position; his necessary truths were true in the mind of God. Conditionalism simply removes that ghost. What is left is not chaos but recursion without closure: truth, like computation, is locally consistent and globally ungrounded.

So the pieces assemble into one picture. Computation gives us syntax; Tarski gives us semantics; Gödel and Chaitin reveal the boundaries of both. And Leibniz's chasm between reasoning and fact turns out to be a Möbius strip — reasoning and fact twisting into one another, each supplying the other's substrate, conditional all the way down. One rule unifies the whole edifice:

> Truth is not a property of statements, but of evaluations. To compute is to interpret, and to interpret is to condition.

Every expressed truth claim requires interpretation. The target structures an interpretation is about need not depend on an interpreter for their existence. Formal logic supplies constraints on this relation; Conditionalism supplies the philosophical reading defended here.
