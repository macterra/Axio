---
title: 'What Beliefs Are'
subtitle: 'From credence thresholds to models of agents'
status: review
sources:
  - 177433505.the-nature-of-beliefs
  - 165666289.what-counts-as-a-belief
---

A mugger hints that he has something concealed in his jacket. It could be a firearm; it could be a toy. The victim has to evaluate a proposition — *the concealed weapon is real* — and has to do it now, with a wallet in the balance. At what point does the victim's suspicion become a belief? Not at certainty; certainty never arrives, in this alley or anywhere else. The natural answer is: at the point where the assessment starts driving behavior. When the victim's confidence that the weapon is real gets high enough that handing over the wallet becomes the rational move, and the wallet is handed over, something has crossed a line. Whatever we mean by *belief*, that crossing is it.

That answer is nearly right, and I held it for a while in exactly that form. This chapter starts there, follows it until it creaks, and ends somewhere more radical: beliefs are not things agents have at all. They are features of *models* of agents — including the model each agent keeps of itself. Getting from the first picture to the second is not a retraction; it is a refinement, and the first picture survives inside the second as a special case. But the destination changes what kind of thing a belief is, so it is worth making the trip carefully.

## Credence with Teeth

The word *belief* wanders vaguely between opinion and knowledge, and most confusion about it comes from letting it wander. The threshold account pins it down: a belief is an agent's assignment of sufficiently high subjective probability — Credence — to a proposition, robust enough to guide practical decisions, predictions, and actions.

Three features of this definition do real work.

First, belief is quantified by **Credence**, not by objective frequency. In the optional Quantum Branching Universe (QBU) model introduced in [Measure and Credence](11-measure-and-credence.md), Measure is the normalized Born weight of a specified event sector, while Credence represents an agent's uncertainty. Belief lives entirely on the Credence side. It embodies high credence but never absolute certainty, which is as it should be for cognitively limited creatures whose beliefs evolved to guide action under uncertainty, not to mirror the world perfectly.

Second, belief has **dispositional consequences**. A proposition counts as a belief when it shapes, or would shape in a relevant circumstance, an agent's predictions, deliberation, or behavior. This qualification matters: many genuine beliefs remain dormant because no occasion calls on them, and conduct can be masked by fear, incentives, habit, or competing values. Still, a purported belief that constrains no expectation or possible decision is difficult to distinguish from a slogan. If confidence that a bridge will hold never affects any prediction about the bridge, the attribution has lost its explanatory work.

Third, belief is **conditional**. Since [all truth is conditional](02-all-truth-is-conditional.md), every meaningful belief has the implicit form: *given conditions X, proposition Y warrants sufficiently high credence*. The victim's belief that the weapon is real is conditioned on background assumptions about muggers, jackets, and the local price of bluffing. There are no unconditional beliefs for the same reason there are no unconditional truths.

So far, so good. Credence, action, conditions: the account demystifies belief, connects it to decision-making, and dissolves the false demand for certainty. As a working definition it earns its keep. But push on it and two joints start to creak.

## Where the Threshold Creaks

The first creak is that the threshold moves. Whether a given credence is "sufficiently high" to warrant action depends on the stakes, so the same credence crosses the line for one decision and not another. Suppose the victim's credence that the weapon is real is 0.6. For handing over a replaceable wallet, 0.6 is far past any sane threshold: comply. For a decision with a different payoff structure — testifying under oath that the mugger was armed — 0.6 may fall well short. Same agent, same proposition, same credence: belief for one purpose, non-belief for another. The threshold account, followed honestly, concludes that "believes P" is not a stable property of an agent at all. It is a property of an agent *relative to a decision problem*. That is not fatal — it may even be true — but it means belief has already stopped being the simple mental possession we took ourselves to be defining. The definition set out to find belief inside the agent and found something indexed to circumstances outside the agent.

The second creak is deeper. The threshold account can sound as though there were a precise credence *in there* — a number stored in the victim's head, waiting to be compared against a threshold. Neural and computational states can certainly encode probabilistic information, but the proposition, number, and threshold appear only under a functional interpretation of those states. Credence is therefore not a separately locatable mental object. It is a useful level of description that we ascribe to an agent to explain and predict what the agent does.

Take that interpreter seriously and the whole picture reorganizes.

## Beliefs Live in Models

Beliefs are not static propositions stored inside minds. They are models of regularity, evolved and learned to explain and predict behavior — first our own, then that of others. To believe a bridge will hold is to model it as structurally reliable, and thus to walk across. To believe someone is honest is to model their future actions as aligned with truth. Belief is not representational content sitting in a mental filing cabinet; it is **functional compression** — a simplified generative model that guides behavior under uncertainty. In predictive-processing terms, a belief is a prior: a probability distribution over possible world-states, continuously updated by evidence. In Dennett's terms, it is a feature of the *intentional stance*: an attribution that renders an agent's behavior intelligible and predictable. Beliefs belong to the same family as the maps and models examined in [Maps, Models, and Understanding](06-maps-models-understanding.md) — compressions judged by their usefulness — with one twist that changes everything: the thing being modeled is an agent.

Here is the proposed interpretation: belief belongs to **models of agents**, not to a separately identifiable inventory inside them. A physical or computational agent enacts processes — it perceives, reacts, regulates — and some of those processes carry information and support control. Describing their organization as belief is a higher-level interpretation, much as describing a rock's motion with a trajectory equation is a useful representation rather than the discovery of an equation inside the rock. On this account belief appears at the level that relates an agent's representations, expectations, and actions to its environment.

This applies even to the first person. An agent can maintain a **self-model** that depicts itself as an agent — and that self-model can contain beliefs. But the beliefs live in the model, not in the agent as a physical entity. And the rule applies recursively: models of agents can contain models of agents, each level ascribing beliefs to the one beneath.

**On this account, a belief is a model of the world inside a model of an agent. Saying that an agent has beliefs is useful shorthand for that explanatory level.**

## The Interpretation Stack

Lay the levels out and the architecture of the whole thing becomes visible:

- **World.** Causal dynamics, devoid of representation. Nothing here believes anything.
- **Agent.** Processes and control systems — perception, reaction, regulation. Still no beliefs, only mechanism.
- **Model of Agent.** Beliefs appear here, for the first time: in representations of how the agent perceives, values, and predicts.
- **Self-Model.** The agent's internal model of itself *as* an agent — which, being a model of an agent, contains beliefs. This is where "I believe" gets its meaning.
- **Observer.** A model of another agent's self-model, attributing beliefs to explain and predict — the layer at which we read each other's minds.

Beliefs arise only in the modeling relation itself. They are features of how systems represent agents, not of how agents exist in the world. The stack also explains why belief-talk works at all between us: language, imitation, and theory of mind are the machinery by which agents synchronize their models across the top layers of the stack. When you tell me what you believe, you are not exporting an object from your skull; you are helping me tune my model of your self-model.

## The Threshold, Reinterpreted

Now the reconciliation, and it is a reconciliation rather than a replacement. Where does the credence-threshold account live in this stack? At the self-model layer. When the victim deliberates — *how likely is the weapon to be real, and is that likely enough to comply?* — he is running a model of himself as a credence-bearing chooser facing a decision problem. Within that model, the threshold story is exactly correct: there is a credence, there is a stakes-sensitive threshold, and belief is the credence crossing it. The threshold account is the view from *inside* the self-model, and it remains the right account of what deliberation is like and of how belief guides action.

Its creaks are explained rather than merely excused. The threshold moved with the stakes because thresholds are features of decision models, and decision models are indexed to decisions. And the missing credence-object in the skull is no defect if credence is a functional description of organized physical states rather than an additional object. The two accounts describe the phenomenon from different vantage points — from within the self-model, where belief guides action, and from without, where belief explains it. The models-of-agents account is the broader proposal; the threshold account is what it looks like inside a particular decision model.

## Calibration, Not Certainty

One consequence matters more than the rest. If a belief is a predictive model, one central epistemic virtue is **calibration**: how well graded confidence survives contact with reality. Calibration does not replace accuracy, explanatory reach, or relevance, but it makes overconfidence visible. A well-calibrated 0.6 is better than an ill-founded 0.99 when those forecasts can be assessed over comparable cases. Confidence, on this view, includes an expectation about how stable a belief will be under new evidence. And epistemic faith, as defined in [Against Faith](10-against-faith.md), is confidence protected from calibration: a model disconnected from the error signal. Keeping beliefs calibrated is a practice, and [the discipline of updating](19-the-discipline-of-updating.md) is that practice's name.

Beliefs are living hypotheses, not frozen propositions. Their function is to reduce surprise, not to defend identity — and most of what goes wrong in human believing is the second use crowding out the first. A belief held as a badge of belonging has stopped doing its job; it is no longer compressing the world, only signaling allegiance. What makes a belief valuable is not that it is correct full stop — nothing is correct full stop — but that it *reduces error without freezing adaptation*.

To believe is to model. To explain belief is to model a model. That recursive architecture is not a curiosity of philosophy of mind; it underlies cognition, communication, and social inference all the way down. Beliefs are not containers of truth but constructors of coherence, binding perception, action, and interpretation into a single predictive loop. What it takes for such a model to rise to the dignity of *knowledge* is the next question — taken up in [What Knowledge Is](09-what-knowledge-is.md).
