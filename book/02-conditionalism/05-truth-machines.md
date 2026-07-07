---
title: 'Truth Machines'
subtitle: 'From Leibniz to Tarski, Gödel, and Turing'
status: draft
sources:
  - 177760320.truth-machines
  - 174125219.entangled-truths
---

Consider two statements: *2+2=4* and *it rained in Paris yesterday*. They feel like different kinds of thing. Deny the first and you seem to lapse into incoherence; deny the second and you are merely, perhaps, mistaken. The first appears to hold in every possible world; the second could easily have been otherwise. Nearly all of Western philosophy has treated this felt difference as a deep fact about reality — a fault line running between two domains of truth.

Leibniz drew the line most cleanly:

> "There are two kinds of truths: those of reasoning and those of fact. The truths of reasoning are necessary and their opposite is impossible; the truths of fact are contingent and their opposites are possible."

I want to trace what happened to that line. It survived two centuries of philosophy essentially intact, and then the twentieth century's formal logicians — Tarski, Gödel, Turing, Chaitin — dismantled it from the inside, using the very tools of necessity it was supposed to protect. What they discovered, though none of them put it this way, is that truth is not a property of statements at all. It is a property of evaluations. The formal history of logic converges on Conditionalism.

## Leibniz's Two Kinds of Truth

Leibniz's taxonomy divided the intelligible world in two. **Truths of reasoning** are necessary: mathematical and logical truths whose negations entail contradiction. **Truths of fact** are contingent: empirical statements about the world whose negations are logically possible. Behind each kind stood a governing principle. The Principle of Non-Contradiction grounds necessity — no necessary truth can be denied without incoherence. The Principle of Sufficient Reason grounds contingency — every fact has an explanation, yet things might have been otherwise.

The scheme was enormously productive. It gave early modern philosophy a map for the boundary between mathematics and empirical science, and its descendants — Hume's relations of ideas versus matters of fact, Kant's analytic versus synthetic — organized epistemology for two hundred years. But the sharpness of the divide is an illusion born of categorical rigidity, and it takes only the Conditionalist recasting to see why.

## Necessity Is Framework-Relative

Conditionalism holds that [all truth is conditional](02-all-truth-is-conditional.md): every truth takes the form *if X, then Y*, and there are no unconditional truths — only conditionals whose background conditions often remain hidden. Apply this to Leibniz's paradigm cases of necessity.

*2+2=4* becomes: *if* one accepts Peano arithmetic and Indo-Arabic numerals, *then* 2+2=4. The law of non-contradiction, $\neg(P \wedge \neg P)$, becomes: *if* one adopts classical logic, *then* contradictions are excluded.

What Leibniz called necessary rests on a stack of historical contingencies. The **notation** is a cultural invention — numerals and logical symbols had to be devised, and were devised differently in different places. The **definitions** are stipulations — equality, addition, and the logical connectives mean what they mean because we introduced them that way. The **inference rules** vary across systems — classical, intuitionistic, paraconsistent, quantum logics each license different moves, and the choice among them is not itself settled by logic. Necessity survives, but as *framework-relative* necessity: unshakeable inside the framework, contingent in the framework's selection.

## Contingency Is Coherence-Dependent

Now run the recasting in the other direction. *It rained in Paris yesterday* becomes: *if* these meteorological and historical conditions obtained, *then* it rained in Paris yesterday. So far, so Leibnizian. But the fact itself is not free-floating. Without a logical-linguistic system supplying syntax and semantics, the statement collapses into noise. A consistency filter is already operating: self-contradictory claims cannot be admitted as facts at all. And the empirical claim gains its force only through its inferential role — by [cohering](03-the-three-levels-of-truth.md) with networks of other claims about weather stations, calendars, and the city of Paris.

Contingency, then, is *coherence-dependent* contingency. Leibniz's two domains turn out to lean on each other for their very intelligibility. Reasoning rests on an empirical substrate: notations, definitions, and rules emerge historically and are stabilized socially. Fact rests on a logical substrate: empirical claims require logical form to be intelligible and testable. Leibniz saw a boundary; there is actually a braid.

What remains when the dichotomy dissolves is a **continuum of conditional stability**. Some conditionals are highly stable because they rest on entrenched conventions — mathematics, formal logic. Others are fragile, dependent on volatile background conditions — weather, politics, history. Scientific laws sit between the poles: stable conditionals anchored in measurement and modeling conventions. The distinction is one of degree, not kind. What we call "necessary" is merely the upper limit of conditional robustness.

That is the philosophical argument. The remarkable thing is that when logic was finally made rigorous enough to test Leibniz's picture from the inside, it delivered the same verdict.

## Syntax Without Meaning

Turing showed that a computation is a finite mechanical process operating on symbols according to formal rules. Crucially, those symbols are *syntactic tokens* — they have structure but no intrinsic semantics. A Turing machine manipulates "0011" and "⊢P→Q" identically, because from the machine's standpoint both are mere patterns in a tape alphabet. This is the original schism of modern logic: computation explains *form*, not *meaning*. If Leibniz's truths of reasoning were self-grounding, the machine grinding through their proofs would somehow contain their meaning. It doesn't. The meaning has to come from somewhere else.

## Tarski's Bridge

Tarski supplied the somewhere else. His formal definition of truth reads:

> A statement 'P' is true under an interpretation I if and only if P holds in the model I.

That single clause encodes Conditionalism avant la lettre. Truth is not absolute; it is *evaluated relative to an interpretation*. Even "snow is white" — Tarski's own flagship example — is only true in English, given that "snow" refers to frozen precipitation and "white" denotes a spectral range of reflected light. Formally, truth is conditional on interpretation:

$$\mathrm{Truth}(P \mid I)$$

And once the interpreter $I$ is made explicit, a machine can evaluate the condition. Tarski built the bridge between Turing's meaningless syntax and truth — but the bridge has a toll: you must always declare which interpretation you are using. There is no crossing it unconditionally.

## Gödel's Limit, Chaitin's Boundary

Gödel proved that any sufficiently expressive formal system contains true statements unprovable within the system itself. The theorem is often glossed as a result about the limits of mathematics; what it actually exposes is *semantic dependency*. The truth of certain propositions depends on an interpretation that cannot be fully captured by the system's own syntactic rules. The system can write the sentence; it cannot supply the standpoint from which the sentence is true.

Chaitin later tightened the insight using algorithmic information theory: the boundary of provability coincides with the boundary of *compressibility*. Truths that exceed a system's descriptive capacity cannot be generated by it. In both cases the lesson is the same: no system carries its own semantics. Interpretation leaks out of syntax.

## Computation as Interpretation

Now observe the inversion. A computation *is itself* an interpretive act. Given input data $P$ and a program $I$, the machine produces an output $O = I(P)$. Semantically, $I$ interprets $P$. Every evaluation — of arithmetic, of logic, of natural language — is a mapping from pattern to meaning under some interpreter. Change the program, change the meaning.

This is Conditionalism rendered operational: for every pattern $P$ there exists some interpreter $I$ under which $I(P)$ comes out true. There are no absolute truths, only consistent interpreter–pattern pairs. A statement that has been handed to no interpreter has not yet been evaluated at all — it is a candidate for truth, not a bearer of it. (What happens when a statement's conditions are never properly bound is the subject of [when statements fail](04-when-statements-fail.md).)

Shannon's information theory shows why interpretation is not free. Shannon stripped semantics out of the theory deliberately: entropy measures surprise, not meaning. Chaitin's incompressible numbers show what fills the gap — most patterns admit no shorter description than themselves; they resist interpretation. Meaning arises only when a pattern admits a compact interpreter that reconstructs it predictively. Interpretation *is* compression, and truth becomes a measure of how coherently an interpreter maps a pattern to an outcome within finite resources.

## No Ultimate Vantage

The natural objection is to ask for the master interpreter — the one whose evaluations are simply *the* truth. But every act of reasoning presupposes an interpreter evaluating another interpreter, and the formal results close the exit: Gödel's self-reference and Turing's halting problem show that a system cannot perfectly interpret itself. There is no ultimate vantage.

When philosophers speak of "unconditional truth," they are implicitly assuming exactly such a vantage — a hidden universal interpreter, a divine Tarski model in which every statement gets its absolute verdict. Leibniz had a candidate for the position; his necessary truths were true in the mind of God. Conditionalism simply removes that ghost. What is left is not chaos but recursion without closure: truth, like computation, is locally consistent and globally ungrounded.

So the pieces assemble into one picture. Computation gives us syntax; Tarski gives us semantics; Gödel and Chaitin reveal the boundaries of both. And Leibniz's chasm between reasoning and fact turns out to be a Möbius strip — reasoning and fact twisting into one another, each supplying the other's substrate, conditional all the way down. One rule unifies the whole edifice:

> Truth is not a property of statements, but of evaluations. To compute is to interpret, and to interpret is to condition.

Every truth lives inside an interpreter. Outside interpretation there is only unparsed chaos — patterns without meaning, syntax without truth.
