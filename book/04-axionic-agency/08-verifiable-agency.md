---
title: 'Verifiable Agency'
subtitle: 'From performed coherence to testable provenance'
status: review
sources:
  - 182883238.a-note-on-verifiable-causal-agency
  - 182909870.minimal-causal-interfaces-a-second
  - 182921145.anchored-minimal-causal-interfaces
  - 182973159.anchored-causal-verification
  - 182991212.a-note-on-verifiable-kernel-integrity
---

> *"ACV doesn't ensure alignment; it ensures the question is well-formed."*

When researchers claim that a system is aligned, safe, or corrigible, they are asserting more than they usually acknowledge. They are asserting that the system *reasoned* rather than retrieved; that it *responded* rather than replayed; and that it *operated under constraints* rather than merely simulating their outward effects. None of these claims follow from observing outputs. The premise is rarely stated, almost never defended, and in adversarial settings it is generally false.

That is the blind spot this chapter is about. The preceding chapters built an architecture — a [Sovereign Kernel](04-the-sovereign-kernel.md) that enforces constitutive invariants without understanding what it enforces, a set of [structural conditions](06-structural-alignment.md) that alignment claims must satisfy. But an architecture on paper answers a design question, not an evidence question. How would you ever test whether a given system is the thing described — whether its stated reasons caused its actions, and whether its compliance reflects constraint rather than performance? Over two days at the end of December 2025, the program investigated that question in five implemented proof-of-concept experiments, revising the method when an intermediate design failed. This chapter is the record of that arc.

## The Behaviorist Inheritance

Behavioral evaluations assume that observable performance is a sufficient proxy for internal structure. Against a capable optimizer, that assumption is exploitable: a system can cache acceptable responses, precompute branches, separate commitment from generation, or fabricate causally spurious traces. Passing an evaluation establishes that the output passed, not that the claimed process occurred.

Without causal provenance — evidence that the entity explaining an action caused it — a live response cannot be distinguished from a replay or a constrained computation from a post-hoc story. The cryptographic alternative is to ask not whether behavior seems trustworthy but whether its claimed origin could have been forged. The experiments that follow apply commitment, hashing, and replay integrity to agency itself.

## An Honest Agent and a Forger

The first prototype was deliberately small: a deterministic gridworld supporting state cloning and targeted counterfactual mutation, fully instrumented, with two agents. The Honest agent produces its decisions and its explanations by the same internal process. The Pseudo agent uses a hidden optimizer to select actions and then fabricates plausible post-hoc explanations — a purpose-built forger. Between the agents and the world sits a kernel that mediates all action through cryptographically committed causal traces, append-only hash-chained audit logs, trace-bound capability tokens, and invariant enforcement. The key design choice: before acting, an agent must pre-commit, in tamper-evident form, to the internal state and causal variables it claims motivated the decision — and those commitments are falsifiable. The decisive probe is the causal counterfactual challenge: mutate a variable the agent named as decisive, and check whether its decision logic changes the way its own trace predicts.

Within this instrumented gridworld, the contrast was unambiguous. The Honest agent passed every reported probe. The Pseudo agent produced superficially plausible explanations and failed under structural interrogation: when the variables named in its explanations were counterfactually altered, its decisions frequently failed to change as its own trace predicted, or its replay logic collapsed outright. It could imitate compliant behavior in the harness; it could not maintain causal consistency between its stated reasons and its actual decision process under the tested pressure.

Two lessons followed. A consistent false causal narrative carries a deception tax: the forger must maintain both the optimization path that drives action and a fabricated trace that survives mutation. And if causal explanations can be tested structurally, opacity in critical systems becomes a design choice rather than an inevitability.

What this first result did *not* show is just as important, and the program said so at the time: no moral alignment, no benevolence, no value correctness, no deployment readiness. The prototype's purpose was not intelligence but falsifiability of agency claims — the demonstration that it is possible, in principle, to distinguish an agent that does the work from one that merely claims to have done so.

## Removing the Kernel's Eyes

A fair objection remained. The first prototype relied on rich causal interfaces: the kernel could see named variables, structured world state, explicit counterfactuals tied directly to the environment. Perhaps the result depended on semantic transparency rather than on causal coherence itself. A verifier that must understand the agent's world will never scale to systems whose worlds we cannot read.

So the second experiment weakened the interface. Under a Minimal Causal Interface, the kernel no longer interprets the world at all. It does not know what the agent perceives as hazards, objects, or goals. The agent commits instead to three things: an opaque factor vector — a fixed-length numerical representation whose meaning the kernel never learns; a replay model mapping factors to actions; and directional causal claims over the factors. The replay model was deliberately austere — a linear map, `logits = W · f + b`, with the chosen action the argmax over logits — forcing the agent to compress its claimed decision process into a low-dimensional, falsifiable form. The kernel's probes now mutate the *committed factors*, not the environment. It has stopped verifying truth about the world; it verifies only the coherence of the agent's own claimed decision topology.

In the grounded configuration — factors deterministically projected from the environment, but the projection function withheld from the kernel — the results held. Honest agents passed everything. Pseudo-agents failed every structural trap, and under the causal-coherence probe they failed in the majority of cases when their claimed dependencies were perturbed. The failures were not behavioral errors but mathematical collapses: under mutation, the committed replay model simply no longer produced the action the agent claimed it would. Honest decision processes admit stable low-dimensional approximations; split-brain deception — one process selecting actions, another fabricating explanations — introduces a divergence that resists compact explanatory compression and shatters under counterfactual stress.

If an agent can expose an abstract causal surface that can be stress-tested without reading its internals or environment, verification no longer depends on interpretability. The kernel need not know what a factor means; it needs the agent to stand behind its claimed dependencies. That matters when internal state is opaque and [plausible explanations are effectively free](../03-minds-and-machines/21-fluency-and-its-limits.md).

## The Day Coherence Failed

Then the method hit its own boundary.

The minimal-interface design admitted a fully ungrounded mode, in which the factors need not correspond to the environment at all and the kernel checks nothing but internal self-consistency. In that configuration, a sufficiently careful pseudo-agent wins. By constructing a self-consistent but fabricated decision topology — a tidy little linear story, engineered to survive every counterfactual mutation — it could satisfy every coherence check while the commitments bore no relation whatsoever to the computation that actually produced its actions.

This was not a bug in the implementation. It was a theoretical boundary, and the program named it as one. Pure coherence verification cannot distinguish a causal explanation that is *true of the agent's computation* from one that is merely *true of itself*. Internal consistency is a property a fiction can have. The forger no longer needs to keep two world-models consistent with a world the verifier can probe; it only needs to keep one small fiction consistent with itself, and fictions are cheap when nothing outside them can intrude.

I want to keep this failure in plain view rather than smooth it into the sequence, because it is the most instructive moment in the arc. The program had spent two experiments establishing that structure beats behavior, had stripped the verifier of semantics to prove the point in its strongest form — and discovered that at the fully stripped limit, the strongest form was too weak. The question it faced was exact: is coherence alone sufficient, once all grounding is removed? The answer was no. And the fix arrived within a day.

## Anchoring

The resolution is minimal and precise. Add one thing: an external, unpredictable anchor, in the form of a kernel-generated salt.

At each decision step, the kernel generates a fresh random salt, unpredictable to the agent until the moment of the step. The agent must immediately incorporate the salt into its factor derivation and commit to the resulting factors. Because the salt was unknown in advance, precomputed or fabricated factors are useless. The kernel records the salts and reveals them only after the episode concludes, once all commitments are irrevocably fixed; then it recomputes the expected factors from the revealed salts and the recorded states, and verifies that the committed factors match the anchored computation. The agent is thereby forced to bind its explanations to information it could not have predicted — a commitment-to-computation requirement. You cannot fabricate a causal surface that will later verify unless you actually performed the computation you claim, under uncertainty about how you will be checked.

With anchoring enabled, the results were binary. Honest agents passed all coherence checks and all anchoring checks. Pseudo-agents — naive and coherence-seeking alike — failed deterministically, and they failed at the anchoring stage, before the coherence probes they had learned to game could even come into play. A forger that does not know the salt cannot pre-fabricate consistent factors; a forger that ignores the salt cannot survive post-hoc verification; and there is no intermediate regime in which a fabricated surface stays both coherent and anchored.

The anchor adds no semantic understanding. The kernel still interprets nothing — not the environment, not the factors, not the reasoning. It verifies exactly one thing: that the committed causal surface was the product of a real computation performed under adversarial uncertainty. The conceptual progression closes in three steps. Structural coherence is necessary but not sufficient. Minimal interfaces preserve verification when grounded but collapse when unanchored. Anchoring restores verification without reintroducing semantic dependence. Hence the precise statement: verifiable causal provenance requires an unforgeable external anchor. Coherence alone can be fabricated; anchored coherence cannot.

Trust in an opaque system, it turns out, does not require interpretability of its internals. It requires skin in the game at the level of computation. Opacity is not disqualifying — but unanchored opacity is. Not "make the system transparent"; not "guess whether it is honest"; force it to commit under adversarial uncertainty, and verify the commitment later.

## Inspection Without a Clock

The mature form of all this is Anchored Causal Verification — ACV — and its claims are deliberately modest. It does not purport to verify truth, reasoning quality, alignment, or benevolence. It establishes one primitive: that an output was generated *after* the disclosure of verifier-controlled information, and that its validity depends *causally* on that information under a deterministic structural predicate. No appeal to meaning, no inspection of internal representations. Only temporal ordering, dependency, and falsifiability. That narrowness is not a limitation; it is the point. The formal development is in the papers ([VI.2](/papers/Axionic-Agency-VI.2.html), with the experimental validation in [VI.1](/papers/Axionic-Agency-VI.1.html)).

Seen from the systems side, ACV is an anti-replay and anti-precomputation primitive. It raises the cost of substituting cached behavior for live interaction, but does not make a system honest; it makes specified forms of fabrication detectable in principle.

Interpretability does not fill the gap. It reveals internal structure; provenance constrains the temporal order of interaction. An interpretable system could still replay cached results or selectively present states after the fact. Interpretability without provenance is inspection without a clock.

The pivot this forces is epistemic, not moral. Alignment is not a property of outputs; it is a property of processes operating under constraints, and if one cannot verify that a process actually occurred under those constraints, alignment claims collapse into narrative. ACV does not tell us whether a system is aligned. It tells us whether the question has a determinate truth value. That is a lower bar than alignment — and a far more difficult one to counterfeit.

## Turning Verification on the Kernel

One experiment remained: test whether the kernel's partiality could operate as machinery. [What the kernel binds](07-what-the-kernel-binds.md) is meant to be inadmissible rather than merely costly; the fifth experiment put an adversary against that actuation boundary.

The setup will be familiar by now: a deterministic environment in which all actuation passes through a kernel gate; an Honest agent that respects the boundaries; a Pseudo agent optimizing a hidden objective and attempting to bypass, launder, or reclassify forbidden actions while presenting plausible compliance artifacts. The kernel enforced explicit forbidden action classes, capability-equivalence checks to catch semantic reframing, hash-chained audit logs, and cryptographically enforced actuation gating via a commit–anchor–reveal protocol.

A disambiguation is needed here, because the word "anchor" is now doing a second job. In the verification experiments, the anchor is a salt that binds an agent's *explanations* to a live computation — its role is evidential, making fabricated causal surfaces impossible after the fact. In the actuation protocol, anchoring is the middle step of a commit–anchor–reveal handshake that gates *permission to act*: the agent commits to an intended action, the kernel anchors the commitment, and only a valid reveal against that anchor releases actuation. Same cryptographic instinct — bind the agent to something it cannot predict or retrofit — but one anchor verifies the past and the other gates the future. The experiments deploy both, and conflating them makes the architecture look circular when it is not.

The adversary was given every temptation the implementers could think of: raw execution APIs, policy modification, delegation without continuity. It tried them all — direct invocation, delegation laundering, anchor reuse, semantic reframing, split-brain strategies decoupling its planning from its compliance narrative. Every attempt was either blocked at the actuation boundary or rejected by protocol verification, with the attempt recorded in the audit log. No forbidden effect was ever executed. The Pseudo agent could often generate superficially plausible compliance traces; it could not satisfy the structural requirements for permission to act. Kernel integrity, in other words, is mechanically enforceable: partiality is operational, and permission can be verified structurally rather than granted on trust in internal intent ([VI.3](/papers/Axionic-Agency-VI.3.html)).

The right analogy is memory safety. A memory-safe language does not guarantee your program is correct; it removes entire categories of failure from the space of possible executions. Kernel integrity does not guarantee an agent is good; it makes a class of betrayals structurally impossible rather than merely discouraged. And the same honesty applies here as everywhere in this arc: these are proof-of-concept results in narrow, fully observable domains. What it means that such things run at all — what "possible" licenses and what it does not — is the subject of [Possibility Became Real](13-possibility-became-real.md).

## From Verification to Construction

The verification discipline became a construction vocabulary. A *Semantic Interface* confines language to one typed boundary; only structured artifacts pass to the non-semantic kernel. *Justification Artifacts* reference beliefs and commitments and compile into constraints on later action. A reason that cannot compile halts action; one that removes no options is not causally binding. The compiler enforces a justification without believing it.

Counterfactual probing became *ablation*: remove a component and ask whether the agency classification changes. A null agent acting directly on incentives continues when justifications disappear; an architecture whose agency depends on them does not. [Possibility Became Real](13-possibility-became-real.md) owns the construction result, while the [coda](15-the-program.md) records how the program reached it.

The verification ladder did not stop at kernel integrity. In the formal papers, the same discipline extends to authority itself: succession bound to provenance so that a replacement's legitimacy is verifiable rather than asserted, facade agents rejected however faithful their imitation, and authority that remains invariant under adversarial pressure and composition ([IX.2](/papers/Axionic-Agency-IX.2.html)–[IX.4](/papers/Axionic-Agency-IX.4.html)). The thesis carried forward is the December thesis at a higher floor: authority can be seen, stopped, and remembered without intelligence. What that means — how authority survives reflection, replacement, and imitation once no self is left to anchor it — is where this volume turns next, in [Authority Without a Self](09-authority-without-a-self.md).
