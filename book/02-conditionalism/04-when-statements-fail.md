---
title: 'When Statements Fail'
subtitle: 'Binding, nonsense, and crooked questions'
status: review
sources:
  - 178181286.truth-as-a-function-of-binding
  - 164272915.nonsense
  - 173394932.straight-answers-crooked-questions
  - 167462936.the-minimal-complete-dictionary
---

"It's raining." Is that true?

In ordinary conversation you often can say, because speaker, place, and time are pragmatically supplied. Written on an undated card with no context, however, the sentence is incomplete. Bind the variables—“It's raining in Montreal at 9 a.m. on 12 July 2026”—and it becomes directly evaluable. Conditionalism concerns when the pragmatic binding is insufficient, not a demand that speakers verbalize what their context already fixes.

This chapter is about the sentences that fail this way. [All truth is conditional](02-all-truth-is-conditional.md), and most of the time the conditions are bound tacitly and nobody notices. But a large class of well-formed, grammatical, confident-sounding sentences are neither true nor false, because the conditions that would make them evaluable have never been fixed. These failures are not moral or preferential claims awaiting an agent; they collapse for a simpler reason. They are **underdetermined**. Ambiguity involves multiple possible meanings; underdetermination involves *no fixed meaning at all* until certain background variables are bound. Diagnosing exactly how a statement fails tells you exactly what it would take to repair it — and reveals, in the cases where no repair is possible, a principled definition of nonsense.

## Six Ways a Statement Can Fail

I count six failure modes.

**The indexical gap.** "It's raining" is the canonical case. Indexicals — *here, now, today, she, they* — are invisible placeholders for context. Bound to a place, a time, a referent, they do honest work. Unbound, they yield vacuous propositions that merely feel factual.

**The referential void.** “The present King of France is bald” is Russell's classic. On Russell's analysis it is a determinate and false existential claim, not semantically empty; other semantic theories treat the failed presupposition differently. The example therefore marks a diagnostic question: does a missing referent make an utterance false, truth-valueless, or pragmatically defective under the chosen semantics?

**The quantifier abyss.** "Everyone is online." "Nothing is certain." Everyone where? Certainty about what? Claims like these depend on an unstated quantifier domain, and until the quantifier is bound to a scope, the truth value floats. Formal logic solves this with explicit domains of discourse; natural language routinely leaves them implicit and lets the reader supply whichever domain flatters the claim.

**The conditional mirage.** "She would have succeeded." "That would be impossible." These masquerade as declaratives while hiding an invisible antecedent. The missing clause — *if the funding had arrived*, *under current laws* — is the difference between logical emptiness and a testable counterfactual. Supply the antecedent and you have a claim worth arguing about; withhold it and you have a mood.

**The standardless evaluation.** "The system is secure." "This is fair." "That's efficient." Many technical and normative claims collapse for lack of a defined metric. Without a threat model, an ethical standard, or an optimization criterion, they cannot be falsified. These are not opinions; they are evaluations awaiting a standard — and until the standard arrives, agreeing or disagreeing with them is equally empty.

**The category violation.** Sentences like “the color green is angry” or “truth is heavy” resist a literal interpretation because their predicates ordinarily apply to different categories. Context can still repair them as metaphor, synesthesia, or technical stipulation. A category error is relative to an interpretation, not proof that no possible interpretation exists.

## Binding as Resolution

The first five failures share a cure. When the hidden variables of context, reference, scope, antecedent, or standard are made explicit, a statement transitions from pseudo-propositional noise into an empirical or logical claim. I call this **condition-binding**. Agent-binding handles moral claims; condition-binding generalizes the principle to every domain of discourse. Binding transforms language from gesture to knowledge.

This is the Conditionalist diagnosis of why unconditional truth is impossible. Every meaningful claim presupposes background conditions: a vantage, a referent, a time, a standard, a model of the world. Each unbound statement is a potential mapping from syntax to world — an as-yet undefined correspondence awaiting the specification of its coordinates. Meaning exists only when those coordinates are fixed. Truth is not an inherent property of sentences but a relation between a statement and the conditions that make it interpretable.

## Nonsense, Properly Defined

“Nonsense” is thrown about casually as abuse. It can be made locally technical. Relative to an interpretation family $\mathcal I$ declared relevant to the conversation, an utterance $P$ is **uninterpretable** if

$$\nexists\, I \in \mathcal I : I(P) \in \{T, F\}.$$

The restriction to $\mathcal I$ matters. With enough invention, almost any string can be assigned a meaning. The useful verdict is that no contextually licensed, charitable interpretation yields truth conditions—not that interpretation is impossible in every conceivable language.

The charity clause is what gives the definition teeth, and what distinguishes nonsense from the milder failures above. An underdetermined statement is nonsense-so-far: it lacks a truth value *as uttered*, but there exists a binding that would repair it, and a charitable listener often supplies one automatically. Nonsense proper is the limiting case where the repair cannot succeed — where every candidate interpretation fails. And note what nonsense is *not*: it is not falsehood. "The Earth is six thousand years old" is bound, evaluable, and false. A false claim has done the honest work of exposing itself to refutation. Nonsense never gets that far.

The definition applies to utterances under declared interpretive constraints, not to whole disciplines by insult. It must also be kept separate from empirical failure. Two familiar cases show why.

Homeopathy's claims about “water memory” and therapeutic effects are interpretable enough to test. The absence of a credible mechanism and failure to outperform controls count against them; they make the claims unsupported or false under ordinary scientific interpretations, not meaningless by definition.

Astrological predictions are likewise often vague but interpretable: they propose correlations or causal influence between astronomical configurations and human outcomes. The scientific objection is that the mechanism and predictive record are inadequate. Calling the claims category errors would evade rather than perform that empirical evaluation.

Contrast the claims that clearly pass. "Water boils at 100 degrees Celsius at standard atmospheric pressure" binds every condition — substance, threshold, standard — and stands ready for evaluation. So does a claim like "within the Quantum Branching Universe (QBU), branches are weighted by [Measure](11-measure-and-credence.md)": exotic subject matter, but coherent truth conditions and determinate reference throughout. Nonsense is not a verdict on how strange a claim sounds. It is a verdict on whether there is anything there to evaluate.

## Fixing Meaning Before Truth

Binding fixes a statement's conditions. But there is a prior layer: before a sentence's conditions can be bound, its words must be bound to senses. A thought experiment shows what that lower layer looks like when made fully explicit.

A regular dictionary lists words with definitions, each definition carrying multiple senses — and it never tells you which sense of each defining word is intended. Imagine instead a *complete* dictionary: every word in every definition hyperlinked to the exact sense meant. The word "set" has over 430 senses in the Oxford English Dictionary; in a complete dictionary, each occurrence of "set" would point to precisely one of them. Now compress: the **Minimal Complete Dictionary** is the smallest set of words sufficient to define every word within it — the semantic kernel of a language, a minimal core whose meanings collectively fix each other.

Notice what the construction concedes. Even the kernel is circular: words define other words, and no dictionary can step outside language to bolt its meanings onto the world directly. Meaning is fixed the way the kernel fixes it — by a network of mutual constraints, not by contact with semantic bedrock. That is the same shape as the Conditionalist account of truth, one level down: just as no statement is true unconditionally, no word means anything atomically. Sense-binding precedes condition-binding, and both are relational through and through — a lesson the [formal truth machines](05-truth-machines.md) teach from the other direction. When binding fails at the sense level, you get nonsense; when it fails at the condition level, you get underdetermination; only when both levels are fixed does truth apply at all.

## Crooked Questions

All of this cashes out in how you answer questions. There is a standing position among some rationalists that prizes blunt binary answers to loaded questions as the mark of intellectual honesty — an eval for epistemic courage. Is God real? *No.* Does superintelligent AI pose a major extinction risk to humanity? *Yes.* Does blockchain have a use case a regular database couldn't serve better? *No.* On this view, the right answers are the ones that resist social conformity: religion pressures you to hedge on the first, complacency on the second, hype on the third, and refusing to hedge is the whole test.

The courage is real and I do not want to dismiss it. But run the three questions through the taxonomy and each turns out to be crooked — a straight answer to any of them smuggles in a binding the question never made.

*Is God real?* If "God" names a supernatural being who intervenes in history: no. If it is a metaphor for coherence or sacredness: yes, those referents exist. And some formulations are ill-posed outright — the term is doing standardless, reference-shifting work that no single binding captures. The question looks binary because the indexical machinery is hidden.

*Does superintelligent AI pose a major extinction risk?* The answer depends on what capabilities, deployment conditions, horizon, probability threshold, and comparison class “major” denotes. This is an ordinary Credence and modeling problem; it does not require the QBU's Measure unless that optional ontology has already been adopted.

*Blockchain?* As an efficiency play against databases: no. For trustless coordination without a central authority: yes — a real but rare use case. "Rare but real" is not a hedge; it is the shape of the truth, and the blunt "No" erases exactly the conditional structure that makes the answer informative.

So there are two virtues in tension. **Epistemic courage** cuts through noise with decisive statements and refuses to let social pressure dictate the answer. **Epistemic rigor** refuses to collapse complexity into false binaries and insists on exposing hidden dependencies. Courage without rigor risks dogmatism: confident answers to questions that were never well-posed. Rigor without courage risks paralysis: an endless unpacking of conditions that never ventures a claim. The discipline is to integrate both — answer as clearly as the question's structure permits, and always reveal the conditions that make the answer true. Not "yes" or "no," but *if X, then Y*, said without flinching.

That dialectic is not a flaw in Conditionalism; it is the method working as intended. A statement earns a truth value by having its conditions bound. A question earns a straight answer the same way. When either arrives unbound, the honest response is not courage or silence — it is to do the binding out loud.
