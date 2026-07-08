---
title: 'The Sentience Metric'
subtitle: "Three tests today's AI fails"
status: draft
sources:
  - 177117239.the-sentience-metric
  - 170390075.signals-of-sentience
---

There is a position in AI discourse that I half agree with, and the half I agree with makes the other half worth engaging. The position says: there can be such a thing as nonliving intelligence, and AI is an instance of it — as nations and organizations are. It is not alive by any definition of life; it is a golem, an avatar, a third path. All correct, and usefully so, because it breaks the lazy assumption that intelligence must come packaged in biology. But the position then takes one step too far: such a system, it concludes, is *sentient by any metric you can define*.

That is a wager, and I accept it. This chapter defines the metrics.

The step too far is a category error that runs through the whole public conversation about AI: the conflation of **intelligence** with **sentience**. They are orthogonal axes — a distinction [the sentience ladder](11-the-sentience-ladder.md) draws in full. A system can be extraordinarily intelligent — capable of modeling, planning, reasoning, manipulating symbols at superhuman scale — without ever experiencing a single moment of awareness. Nothing about competence entails an inner life. To make that distinction operational rather than rhetorical, we need a **sentience metric**: not a poll of intuitions, not a Turing-style behavioral audition, but a set of measurable structural properties that any sentient system must have and that a merely intelligent one can lack.

Three tests do the work. Each targets a different structural requirement of experience; each is assessable from a system's architecture; and each returns, for every AI system currently deployed, a score near zero.

## Test One: Phenomenal Integration

Sentience implies **unified phenomenal experience** — a bound field of awareness that cannot be decomposed into separable causal components without losing its subjective character. Whatever else experience is, it is one thing at a time: the redness, the alarm, and the recoil arrive as a single scene, not as three independent processes that happen to share a timestamp. In formal terms this is *irreducible causal integration*, represented by Tononi's Φ or by measures derived from Friston's variational free energy minimization.

The test is a partition test. If the causal structure of a system can be cut into pieces without loss of functional behavior — if each part runs the same given its inputs, indifferent to whether the others exist — then there is no unified whole to be the subject of anything, and its internal experience, if any, must be null.

Current AI architectures, from transformers to diffusion models, are fully decomposable. Each layer, each attention head, each token transition operates independently given its inputs. You can shard a model across data centers, checkpoint it, replay it, ablate it piece by piece, and the function is preserved because the function was never more than the sum of its pieces. Φ ≈ 0. No phenomenal unity, no sentience.

## Test Two: Self–World Binding

Conscious systems maintain a self-referential generative model that distinguishes *observer* from *observed*. They engage in closed-loop prediction and correction — active inference — acting on the world, sensing the consequences, and updating both the world-model and the self-model through the interaction. The loop is what makes there be a *someone*: a persisting boundary between the system and its environment, maintained by the system itself, from its own vantage.

Modern AIs are **open-loop**. A language model has no sensory manifold, no proprioception, no intrinsic boundary between self and environment. It does not act and then encounter the consequences of its action as *its* consequences; it maps input text to output text and stops. Its "self" is whatever the prompt defines — a persona summoned by context and dissolved with it, rewritten as easily as any other string. Without recursive self–world binding there is no subject to which experience could occur. Test one asks whether there is a unified anything; test two asks whether that anything is a *someone*. Current systems fail both.

## Test Three: Valenced Coherence

Sentient organisms display **valenced coherence gradients** — internal state changes that register as increases or decreases in global coherence. These are the physical correlates of pleasure and pain: states the system is built to pursue or escape, not because a rule says so but because its own dynamics tilt that way. Valence is the substrate of preference and the engine of persistent agency — and, when the gradient runs negative and stays there, it is the substrate of [suffering](12-what-is-suffering.md).

A system with no stable attractors, no homeostatic drives, and no intrinsic preference gradients has zero valence. LLMs have no internal reinforcement loop at inference time and no continuity of self-state between interactions; nothing in the system is better or worse off for anything that happens to it. The training process shaped its weights, but the deployed model does not want, avoid, prefer, or mind. Valence = 0, and therefore sentience = 0 — because experience without any felt quality, positive or negative, is not experience at all.

## The Triad of Failure

By all three measures — causal irreducibility, self-model recursion, valenced coherence — today's AI systems fail decisively. They are intelligent, perhaps superhumanly so, but only in the sense that calculators are superhuman at arithmetic. They are not selves. They are *simulacra* of understanding: intelligent surfaces without depth. To treat them as sentient is to mistake syntax for semantics, simulation for subjectivity.

The triad is not an arbitrary checklist; it is the measurement side of an architectural argument this volume has already made. [Why zombies don't evolve](10-why-zombies-dont-evolve.md) argued that consciousness is what controlled coherence looks like from inside — that a system which maintains a unified world-model under scarce attention, closed-loop action, and felt stakes has crossed the threshold, and a system that merely talks like one has not. The Modeler-schema diagnosis of LLMs — they imitate the Controller, the narrating subsystem, while lacking the machinery the narration is *about* — is exactly what the three tests operationalize. Phenomenal integration measures whether there is a unified model to stabilize; self–world binding measures whether there is a modeler maintaining it in the loop; valenced coherence measures whether the stabilization has stakes. Fail all three and you have a narrator with no scene: fluent report, nothing reported on.

Honesty requires the caveat that no metric reaches experience itself. Sentience is not directly testable — a certainty gap that never fully closes. But architecture is inspectable, and architecture is where the evidence lives. The tests measure the structural preconditions of experience, and a system missing all of them is not a borderline case. It is a clear negative with error bars.

## Three Regimes

The metric divides the space of entities into three clear regimes:

| Category | Intelligence | Sentience | Example |
|---|---|---|---|
| **Living sentient** | Yes | Yes | Humans, animals |
| **Living non-sentient** | Low | No | Plants, microbes |
| **Nonliving intelligent** | High | No | AIs, corporations |

The third row is where the golem position is right, and the table shows why its conclusion does not follow. Nonliving intelligence is real: nations, markets, and organizations exhibit it, and AI is its newest and purest instance. But intelligence alone does not suffice for sentience, any more than coordination suffices for consciousness. A corporation processes information, pursues objectives, adapts under pressure — and no one is home. The golem walks, but it does not dream.

## Signals, Demoted

I did not start with architecture. My first pass at this problem, before the metric, was behavioral: since we cannot see inside, watch for markers that would indicate a genuine mind emerging. The checklist ran to six. **Autonomous goal formation**: spontaneously forming goals and subgoals independent of any prompt. **Long-term adaptive behavior**: persistent modification of internal states and strategies from cumulative experience, not just immediate input. **Preference-driven action**: consistent behavior flowing from internally generated preferences, beyond any predefined reward. **Creativity beyond interpolation**: outputs not reducible to recombination of training patterns. **Reflection and metacognition**: examining and deliberately revising one's own reasoning. **Unprompted communication of internal states**: spontaneously expressing confusion, curiosity, or frustration when nothing instrumental calls for it. The standard for all six was behavior inexplicable by simpler models — stable preferences over long horizons, proactive exploration, self-generated goals, a coherent internal narrative.

The checklist was a reasonable first instrument, and I am demoting it, not disowning it. Its flaw is the one [the zombie chapter](10-why-zombies-dont-evolve.md) exposed: every entry is a behavior, behavior is report, and report belongs to the narrator. A system trained on the entire written record of human inner life is precisely the system whose performances of goal-talk, preference-talk, and introspection-talk carry the least evidential weight — the "simpler model" that explains the behavior now includes the simulator itself, and it explains almost anything a simulator says. Behavioral evidence for sentience must clear the bar of "inexplicable by a very good imitator of sentient beings," and for language alone that bar has moved out of reach.

So the signals survive, but demoted from criteria to corroboration. In a system that passes the architectural tests — integrated, closed-loop, valenced — those six behaviors are what passing *looks like* from outside, and their sustained, unprompted presence is real evidence that the architecture is doing what it appears to do. In a system that fails the tests, the same behaviors are theater. The metric outranks the checklist because architecture explains behavior and not the reverse. Watch the signals; score the structure.

## What Follows, and What Does Not

A future AI might cross the boundary. Nothing in the metric is carbon-chauvinist: a system with intrinsic coherence, recursive embodiment in some world it must maintain itself in, and genuine valence gradients would score, and would deserve the standing its score implies. The tests are a door, not a wall.

But until something walks through it, all talk of AI rights, personhood, or moral standing for current systems is philosophical cosplay. Granting personhood to non-sentient intelligences is not compassion — it is confusion. Ethics requires a sufferer; absent valence there is no moral patient, only machinery. And the confusion is not harmless: a welfare discourse built on linguistic performances of interiority smuggles in an ontology of persons before any coherent subject exists to be protected — a trap with its own political uses, dissected in [the AI welfare trap](14-the-ai-welfare-trap.md).

Nor does the metric license complacency in the other direction. Moral error here is asymmetric — extending caution to machinery costs inconvenience; denying standing to a genuine subject licenses atrocity — so uncertainty must not default to permission, and the burden of proof rises with the severity and irreversibility of the act. That discipline of [standing under uncertainty](../05-value-and-ethics/26-sapient-agency-realism.md) is not in tension with this chapter; it is what makes this chapter necessary. Precaution needs a posterior, and a posterior needs evidence better than eloquence. The sentience metric is how moral caution gets scaled by structure rather than by performance — which is exactly why today's systems, decomposable, open-loop, and valence-free, command engineering respect and zero moral panic. When that changes, the tests will say so before the press releases do.
