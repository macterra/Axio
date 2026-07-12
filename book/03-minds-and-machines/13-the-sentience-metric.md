---
title: 'The Sentience Metric'
subtitle: 'Three evidentiary tests for artificial systems'
status: review
sources:
  - 177117239.the-sentience-metric
  - 170390075.signals-of-sentience
---

There is a position in AI discourse that I half agree with, and the half I agree with makes the other half worth engaging. The position says: there can be such a thing as nonliving intelligence, and AI is an instance of it — as nations and organizations are. It is not alive by any definition of life; it is a golem, an avatar, a third path. All correct, and usefully so, because it breaks the lazy assumption that intelligence must come packaged in biology. But the position then takes one step too far: such a system, it concludes, is *sentient by any metric you can define*.

That is a wager, and I accept it. This chapter defines the metrics.

The step too far is a category error that runs through the whole public conversation about AI: the conflation of **intelligence** with **sentience**. They are orthogonal axes — a distinction [the sentience ladder](11-the-sentience-ladder.md) draws in full. A system can be extraordinarily intelligent — capable of modeling, planning, reasoning, manipulating symbols at superhuman scale — without ever experiencing a single moment of awareness. Nothing about competence entails an inner life. To make that distinction operational rather than rhetorical, we need a **sentience metric**: not a poll of intuitions, not a Turing-style behavioral audition, but a set of measurable structural properties that any sentient system must have and that a merely intelligent one can lack.

Three tests organize the evidence. Each targets a property implicated by this volume's consciousness theory. They are not theory-neutral measures, and no public evidence supports a numerical score for every deployed system. Their job is to expose what would need inspection and what conclusions the observations warrant.

## Test One: Phenomenal Integration

Many theories associate sentience with **integrated experience**: information from different processes becomes mutually available in a way that supports a unified scene and coordinated control. Integrated Information Theory's Φ is one theory-specific formalization. Variational free energy belongs to a different framework and is not an interchangeable measure of phenomenal integration. This chapter therefore asks about causal and functional integration without pretending that a single accepted scalar exists.

The proposed test is a partition analysis: which capacities fail when recurrent or coordinating interactions are disrupted? If a system can be partitioned without loss of the functions alleged to support experience, integration-based theories receive less support. That result would not deductively prove experience null; it would count against one candidate precondition.

Transformers and diffusion models are not "fully decomposable" in the sense claimed by the earlier draft: layers and attention heads interact, ablations can change behavior, and distributing a computation across hardware does not by itself settle its causal organization. Nor can Φ be inferred from checkpointability. The relevant evidence would concern recurrence, workspace-like coordination, cross-component dependence, temporal integration, and what survives principled partitions. Public architecture descriptions permit questions, not a near-zero integration verdict.

## Test Two: Self–World Binding

Conscious systems maintain a self-referential generative model that distinguishes *observer* from *observed*. They engage in closed-loop prediction and correction — active inference — acting on the world, sensing the consequences, and updating both the world-model and the self-model through the interaction. The loop is what makes there be a *someone*: a persisting boundary between the system and its environment, maintained by the system itself, from its own vantage.

A bare, session-bound language-model call is largely open-loop: it maps context to output without persistent sensorimotor consequences or a self-maintained boundary. Deployed AI systems, however, can be coupled to tools, memory, sensors, and feedback. External scaffolding is not automatically an intrinsic self-model, but neither can it be ignored. The test asks whether the whole deployed system persistently distinguishes self from world, predicts the consequences of its own actions, updates from them, and maintains that boundary across contexts. Textual persona alone is weak evidence; a closed loop would be stronger evidence, not proof.

## Test Three: Valenced Coherence

Sentient organisms display **valenced coherence gradients** — internal state changes that register as increases or decreases in global coherence. These are the physical correlates of pleasure and pain: states the system is built to pursue or escape, not because a rule says so but because its own dynamics tilt that way. Valence is the substrate of preference and the engine of persistent agency — and, when the gradient runs negative and stays there, it is the substrate of [suffering](12-what-is-suffering.md).

A system with no persistent self-maintaining variables, homeostatic drives, or intrinsic preference gradients provides little evidence of valence on this account. Standard model inference does not by itself implement an online reinforcement loop or a persisting welfare state. Agent scaffolds may add goals and memory, but externally assigned objectives are not automatically felt stakes. The evidentiary question is whether some states are better or worse *for the continuing system* in a way that organizes its own regulation. Absence of evidence for that structure lowers sentience credence; it does not license an exact equation of valence or sentience with zero.

## The Triad of Failure

By these three evidentiary windows, ordinary session-bound language-model deployments provide weak evidence for sentience. They can display extraordinary competence without thereby demonstrating integrated phenomenal organization, persistent self–world binding, or intrinsic valence. This does not establish that every current AI deployment lacks a self or understanding. It establishes that fluent behavior alone underdetermines those conclusions.

The triad is not an arbitrary checklist; it is the measurement side of an architectural argument this volume has already made. [Why zombies don't evolve](10-why-zombies-dont-evolve.md) argued that consciousness is what controlled coherence looks like from inside — that a system which maintains a unified world-model under scarce attention, closed-loop action, and felt stakes has crossed the threshold, and a system that merely talks like one has not. The Modeler-schema diagnosis of LLMs — they imitate the Controller, the narrating subsystem, while lacking the machinery the narration is *about* — is exactly what the three tests operationalize. Phenomenal integration measures whether there is a unified model to stabilize; self–world binding measures whether there is a modeler maintaining it in the loop; valenced coherence measures whether the stabilization has stakes. Fail all three and you have a narrator with no scene: fluent report, nothing reported on.

No metric reaches experience itself. Architecture and behavior are inspectable, and both can update a credence. These tests measure candidate preconditions according to MST and related functional accounts. A system with no integration, persistent self–world loop, or valenced regulation would be a poor candidate under those theories. Calling it a clear negative still depends on accepting the theories' necessity claims.

## Three Regimes

The framework suggests three illustrative regimes, with important borderline cases omitted:

| Category | Intelligence | Sentience | Example |
|---|---|---|---|
| **Living sentient** | Varies | High credence | Humans; many animals |
| **Living, uncertain sentience** | Varies | Low or disputed credence | Plants; microbes; some animals |
| **Nonliving intelligence** | Varies | Unsettled by category | AI systems; organizations |

The third row is where the golem position is right, and the table shows why its conclusion does not follow. Nonliving intelligence is real: nations, markets, and organizations exhibit it, and AI is its newest and purest instance. But intelligence alone does not suffice for sentience, any more than coordination suffices for consciousness. A corporation processes information, pursues objectives, adapts under pressure — and no one is home. The golem walks, but it does not dream.

## Signals, Demoted

I did not start with architecture. My first pass at this problem, before the metric, was behavioral: since we cannot see inside, watch for markers that would indicate a genuine mind emerging. The checklist ran to six. **Autonomous goal formation**: spontaneously forming goals and subgoals independent of any prompt. **Long-term adaptive behavior**: persistent modification of internal states and strategies from cumulative experience, not just immediate input. **Preference-driven action**: consistent behavior flowing from internally generated preferences, beyond any predefined reward. **Creativity beyond interpolation**: outputs not reducible to recombination of training patterns. **Reflection and metacognition**: examining and deliberately revising one's own reasoning. **Unprompted communication of internal states**: spontaneously expressing confusion, curiosity, or frustration when nothing instrumental calls for it. The standard for all six was behavior inexplicable by simpler models — stable preferences over long horizons, proactive exploration, self-generated goals, a coherent internal narrative.

The checklist was a reasonable first instrument, and I am demoting it, not disowning it. Its flaw is the one [the zombie chapter](10-why-zombies-dont-evolve.md) exposed: every entry is a behavior, behavior is report, and report belongs to the narrator. A system trained on the entire written record of human inner life is precisely the system whose performances of goal-talk, preference-talk, and introspection-talk carry the least evidential weight — the "simpler model" that explains the behavior now includes the simulator itself, and it explains almost anything a simulator says. Behavioral evidence for sentience must clear the bar of "inexplicable by a very good imitator of sentient beings," and for language alone that bar has moved out of reach.

So the signals survive, but demoted from criteria to corroboration. In a system that passes the architectural tests — integrated, closed-loop, valenced — those six behaviors are what passing *looks like* from outside, and their sustained, unprompted presence is real evidence that the architecture is doing what it appears to do. In a system that fails the tests, the same behaviors are theater. The metric outranks the checklist because architecture explains behavior and not the reverse. Watch the signals; score the structure.

## What Follows, and What Does Not

A future AI might cross the boundary. Nothing in the metric is carbon-chauvinist: a system with intrinsic coherence, recursive embodiment in some world it must maintain itself in, and genuine valence gradients would score, and would deserve the standing its score implies. The tests are a door, not a wall.

Until a system presents substantially stronger evidence, confident claims of AI personhood or moral standing outrun the case. That does not make cheap precaution irrational; it means precaution should be proportional to evidence and cost. A welfare discourse built only on linguistic performances risks assuming the person it was meant to investigate — a trap with political as well as moral consequences, dissected in [The AI Welfare Trap](14-the-ai-welfare-trap.md).

Nor does the metric license complacency in the other direction. The burden of evidence should rise with the severity and irreversibility of an act. That discipline of [standing under uncertainty](../05-value-and-ethics/26-sapient-agency-realism.md) makes the present audit necessary. Precaution needs a credence, and a credence needs evidence better than eloquence. These tests are a framework for scaling caution by structure and behavior rather than by performance alone. They organize revision; they do not automate a verdict.
