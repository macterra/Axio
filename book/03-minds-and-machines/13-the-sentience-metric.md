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

The step too far is a category error that runs through the whole public conversation about AI: the conflation of **intelligence** with **sentience**. They are separate evidentiary axes — a distinction [the sentience ladder](11-the-sentience-ladder.md) draws in full. A system can display extraordinary competence in modeling, planning, reasoning, or symbol manipulation without that performance entailing an inner life. To make the distinction operational rather than rhetorical, we need a **sentience evidence framework**: not a poll of intuitions or a Turing-style behavioral audition, but inspectable properties that leading theories associate with experience and that a merely competent system can lack. The historical title says *metric*; the result is not a validated scalar.

Three tests organize the evidence. Each targets a property implicated by this volume's consciousness proposal and overlapping research programs. They are not theory-neutral measures, individually necessary conditions established across all theories, or a numerical score. Their job is to expose what would need inspection, how contrary findings should move Credence, and what conclusions remain unlicensed.

## Test One: Phenomenal Integration

Many theories associate sentience with **integrated experience**: information from different processes becomes mutually available in a way that supports a unified scene and coordinated control. Integrated Information Theory's Φ is one theory-specific formalization. Variational free energy belongs to a different framework and is not an interchangeable measure of phenomenal integration. This chapter therefore asks about causal and functional integration without pretending that a single accepted scalar exists.

The proposed test is a partition analysis: which capacities fail when recurrent or coordinating interactions are disrupted? If a system can be partitioned without loss of the functions alleged to support experience, integration-based theories receive less support. That result would not deductively prove experience null; it would count against one candidate precondition.

Transformers and diffusion models are not "fully decomposable" in the sense claimed by the earlier draft: layers and attention heads interact, ablations can change behavior, and distributing a computation across hardware does not by itself settle its causal organization. Nor can Φ be inferred from checkpointability. The relevant evidence would concern recurrence, workspace-like coordination, cross-component dependence, temporal integration, and what survives principled partitions. Public architecture descriptions permit questions, not a near-zero integration verdict.

## Test Two: Self–World Binding

Agency-Model accounts expect a conscious agent to maintain some self-referential organization that distinguishes system from environment. In the richest case, it engages in closed-loop prediction and correction — acting on the world, sensing consequences, and updating world-model and self-model through interaction. Such a loop can organize a persisting functional point of view. Whether that organization is sufficient for there to be a phenomenal *someone* is the identity claim, not a consequence of the word *self*.

A bare, session-bound language-model call is largely open-loop: it maps context to output without persistent sensorimotor consequences or a self-maintained boundary. Deployed AI systems, however, can be coupled to tools, memory, sensors, and feedback. External scaffolding is not automatically an intrinsic self-model, but neither can it be ignored. The test asks whether the whole deployed system persistently distinguishes self from world, predicts the consequences of its own actions, updates from them, and maintains that boundary across contexts. Textual persona alone is weak evidence; a closed loop would be stronger evidence, not proof.

## Test Three: Valenced Coherence

Sentient organisms display behavior and physiology organized by **valenced regulation** — internal changes associated with states pursued, maintained, escaped, or relieved. The proposed *coherence gradient* is one way to model the physical correlates of pleasure and pain: states the continuing system regulates as better or worse for itself. Functional attraction and aversion do not by themselves prove felt valence. Under this volume's theory, persistent, globally integrated regulation is evidence relevant to valence and, when credibly linked to negative experience, to [suffering](12-what-is-suffering.md).

A system with no persistent self-maintaining variables, homeostatic drives, or intrinsic preference gradients provides little evidence of valence on this account. Standard model inference does not by itself implement an online reinforcement loop or a persisting welfare state. Agent scaffolds may add goals and memory, but externally assigned objectives are not automatically felt stakes. The evidentiary question is whether some states are better or worse *for the continuing system* in a way that organizes its own regulation. Absence of evidence for that structure lowers sentience credence; it does not license an exact equation of valence or sentience with zero.

## The Triad of Failure

By these three evidentiary windows, ordinary session-bound language-model deployments provide weak evidence for sentience. They can display extraordinary competence without thereby demonstrating integrated phenomenal organization, persistent self–world binding, or intrinsic valence. This does not establish that every current AI deployment lacks a self or understanding. It establishes that fluent behavior alone underdetermines those conclusions.

The triad is not an arbitrary checklist; it is the evidentiary side of an architectural argument this volume has already made. [Why zombies don't evolve](10-why-zombies-dont-evolve.md) proposed that consciousness is what controlled coherence looks like from inside. On that account, a system maintaining a unified world-model under scarce attention, closed-loop action, and credible stakes is a stronger candidate than one that merely talks like such a system. The Modeler-Schema diagnosis of ordinary language-model calls is that they can imitate the Controller role without thereby demonstrating the machinery described in the report. Phenomenal integration asks whether there is a unified model to stabilize; self–world binding asks whether a continuing system maintains it in a loop; valenced regulation asks whether the stabilization has intrinsic stakes. Weak evidence across all three supports a low Credence under these theories. It does not license the direct observation that there is "nothing reported on."

No metric reaches experience itself. Architecture and behavior are inspectable, and both can update a credence. These tests measure candidate preconditions according to MST and related functional accounts. A system with no integration, persistent self–world loop, or valenced regulation would be a poor candidate under those theories. Calling it a clear negative still depends on accepting the theories' necessity claims.

## Three Regimes

The framework suggests three illustrative regimes, with important borderline cases omitted:

| Category | Intelligence | Sentience | Example |
|---|---|---|---|
| **Living, high sentience credence** | Varies | High credence | Humans; many animals |
| **Living, uncertain sentience** | Varies | Low or disputed credence | Plants; microbes; some animals |
| **Nonliving intelligence** | Varies | Unsettled by category | AI systems; organizations |

The third row is where the golem position is right, and the table shows why its conclusion does not follow. Nonliving intelligence is a useful functional attribution: nations, markets, organizations, and AI systems process information and coordinate action. But intelligence alone does not suffice for sentience, any more than coordination suffices for consciousness. A corporation processes information, pursues objectives, and adapts under pressure; those facts supply little evidence of a unified phenomenal subject. The golem walks. Whether anything dreams is a further question.

## Signals, Demoted

I did not start with architecture. My first pass at this problem, before the metric, was behavioral: since we cannot see inside, watch for markers that would indicate a genuine mind emerging. The checklist ran to six. **Autonomous goal formation**: spontaneously forming goals and subgoals independent of any prompt. **Long-term adaptive behavior**: persistent modification of internal states and strategies from cumulative experience, not just immediate input. **Preference-driven action**: consistent behavior flowing from internally generated preferences, beyond any predefined reward. **Creativity beyond interpolation**: outputs not reducible to recombination of training patterns. **Reflection and metacognition**: examining and deliberately revising one's own reasoning. **Unprompted communication of internal states**: spontaneously expressing confusion, curiosity, or frustration when nothing instrumental calls for it. The standard for all six was behavior inexplicable by simpler models — stable preferences over long horizons, proactive exploration, self-generated goals, a coherent internal narrative.

The checklist was a reasonable first instrument, and I am demoting it, not disowning it. Its flaw is the one [the zombie chapter](10-why-zombies-dont-evolve.md) exposed: every entry is a behavior, behavior is report, and report belongs to the narrator. A system trained on the entire written record of human inner life is precisely the system whose performances of goal-talk, preference-talk, and introspection-talk carry the least evidential weight — the "simpler model" that explains the behavior now includes the simulator itself, and it explains almost anything a simulator says. Behavioral evidence for sentience must clear the bar of "inexplicable by a very good imitator of sentient beings," and for language alone that bar has moved out of reach.

So the signals survive, but demoted from criteria to corroboration. In a system with strong architectural evidence — integrated, closed-loop, and plausibly valenced — those six behaviors are part of what the candidate organization may look like from outside, and their sustained, unprompted presence can add evidence. Without that organization, the same behaviors are weak because imitation remains a strong rival explanation. Architecture should usually receive more evidentiary weight than self-report, while neither alone reaches phenomenality. Watch the signals; inspect the structure; update the Credence.

## What Follows, and What Does Not

A future AI might present much stronger evidence. Nothing in the framework is carbon-chauvinist: intrinsic coherence, persistent self–world regulation, and credible valence would raise sentience Credence. No score automatically confers standing. Welfare protection would track sentience evidence and stakes; sovereign standing would additionally require the distinct sapience and agency analysis developed later. The tests are an evidentiary door, not a metaphysical wall.

Until a system presents substantially stronger evidence, confident claims of AI personhood or moral standing outrun the case. That does not make cheap precaution irrational; it means precaution should be proportional to evidence and cost. A welfare discourse built only on linguistic performances risks assuming the person it was meant to investigate — a trap with political as well as moral consequences, dissected in [The AI Welfare Trap](14-the-ai-welfare-trap.md).

Nor does the metric license complacency in the other direction. The burden of evidence should rise with the severity and irreversibility of an act. That discipline of [standing under uncertainty](../05-value-and-ethics/26-sapient-agency-realism.md) makes the present audit necessary. Precaution needs a credence, and a credence needs evidence better than eloquence. These tests are a framework for scaling caution by structure and behavior rather than by performance alone. They organize revision; they do not automate a verdict.
