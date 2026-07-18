---
title: 'Reasonable Disagreement'
subtitle: "What Aumann's theorem actually implies"
status: review
sources:
  - 165822194.aumanns-agreement-theorem
  - 164937702.reasonable-disagreement
---

Two epistemically serious people take up the same question — say, whether some metaphysical doctrine, the logical necessity of the Christian Trinity, could actually be true. They read the same arguments, weigh the same evidence, and talk until neither has anything new to say. One settles at a [Credence](11-measure-and-credence.md) of one or two percent: skeptical but open. The other settles a hundred times lower. Neither is confused, neither is bluffing, and each can walk the other through every step of the reasoning. Common sense says this standoff is simply what inquiry among humans looks like.

A famous theorem says it should be impossible.

## The Theorem

Robert Aumann proved in 1976 that Bayesian agents with a common prior cannot have different posteriors for the same event when those posteriors are common knowledge. The theorem is static: under its formal information-partition assumptions, the posteriors must already be equal. Dialogue protocols can produce convergence results, but that is additional machinery.

The result hinges on two idealizations:

1. **Common prior.** Both agents' posteriors arise by conditioning the same prior probability on their respective information.
2. **Common knowledge of posteriors.** Each posterior value, and the fact that both values have been announced, is common knowledge to the usual infinite depth.

The intuition behind the proof is worth having in your bones, because it changes how you hear a disagreement. Under these conditions, your announced Credence is *evidence* for me. If you are a flawless Bayesian working from the same priors I am, and you have arrived at a different posterior, the only possible explanation is that you have seen something I have not — so your number tells me about your evidence, and I must update on it. But my updated Credence then tells you about *my* evidence, and you must update in turn. Iterate the exchange and the gap closes. The mere fact that a rational peer disagrees with me is itself data, and a persistent refusal to converge would mean one of us is ignoring data — which perfect Bayesians, by definition, never do.

So when people persistently disagree, the theorem identifies assumptions worth checking; it does not hand us an exhaustive psychological diagnosis. At least one formal premise fails:

- **They hold different priors.** They were never starting from the same place, so shared evidence cannot force them to the same destination.
- **They have asymmetric information.** Something one of them knows — evidence, or the reasoning of the other — has not actually made it into common knowledge.
- **The formal representation differs or fails.** The proposition or model spaces may differ; agents may be bounded, use imprecise probabilities, or lack a shared representation of the evidence.

That is the theorem's whole content, and it is easy to misread. It does not say that disagreement is irrational. It says that disagreement is *informative*: every persistent disagreement carries information about its own causes.

## Why Real Disagreements Survive

No pair of humans has ever satisfied Aumann's conditions. Real agents almost never share identical priors; a lifetime of different evidence, different training, and different temperament guarantees they arrive at any question from different starting points. Common knowledge is even more demanding than it sounds — not merely that we have both read the same papers, but that our entire epistemic states are mutually transparent to infinite depth. And perfect Bayesian rationality is an ideal that flesh-and-blood reasoners approximate at best, riddled as we are with systematic biases that push our updating off the Bayesian rails.

This is why the theological standoff above need not demonstrate a failure of rationality. The two estimates may reflect different priors, models, evidence assessments, or thresholds—and those differences remain open to criticism. The theorem never promised that actual people would agree; it tells us which idealized conditions would rule disagreement out.

That reframing is the theorem's real gift. The naive reaction to persistent disagreement with an apparently rational peer is accusation: one of us must be stupid, dishonest, or blinded. Aumann replaces the accusation with a checklist. When a disagreement refuses to close, do not ask *who is being irrational?* Ask *which condition failed?* Do we differ in priors — and if so, can we state them and examine where they came from? Is there information one of us holds that the other has not truly absorbed? Is one of us making an identifiable error? Working through that checklist is [the discipline of updating](19-the-discipline-of-updating.md) applied socially: the disagreement itself becomes an instrument for surfacing hidden assumptions that neither party knew they were making. Used this way, rational disagreement is not something to be tolerated. It is a diagnostic tool, and often the sharpest one available.

## The Fourth Source

But the checklist, as Aumann's idealization presents it, is missing an entry — one that the idealization itself conceals. The theorem quietly assumes that the proposition under dispute is the same proposition for both agents: a single well-defined claim whose truth value both are estimating. For coin flips and market prices, fair enough. For a large and important class of questions — above all, moral and social questions — the assumption fails, because the proposition's own truth conditions include facts about the agent evaluating it.

This is Conditionalism's home territory. [All truth is conditional](02-all-truth-is-conditional.md): every claim holds or fails only relative to background conditions, and most of the time those conditions stay implicit. What moral disputes add is that the implicit conditions are *agent-relative* — they involve the values, thresholds, experiences, and informational vantage of particular agents. Two people can then assign different truth values to the "same" sentence while disagreeing about nothing in the world, because the sentence was never the same conditional for both of them.

The clearest cases are the three load-bearing concepts of moral and legal argument: harm, coercion, and consent. I have given each a precise definition elsewhere — the full treatments belong to the ethics of the matter, not to epistemology — but the one-sentence versions suffice here. [Harm](../05-value-and-ethics/11-what-counts-as-harm.md) is a material setback to welfare or functional capacity and viable options against an appropriate baseline. [Coercion](../05-value-and-ethics/09-what-counts-as-coercion.md) is the deliberate use of a credible conditional threat of material setback to obtain compliance. [Consent](../05-value-and-ethics/10-consent-and-property.md) is scoped authorization given with sufficient capacity, material understanding, intention, and voluntariness.

Now watch where the agent-relativity enters each one:

- **Harm** requires judging whether a capacity to pursue *valued goals* was *genuinely degraded*. Which goals matter, how large an impact must be before it counts, whether a given setback constitutes real functional impairment — different agents, with different values and different thresholds, can answer differently without either being wrong.
- **Coercion** turns on whether a threat was *credible* and aimed at extracting compliance. Credibility is not a free-floating fact; it depends on the target's past experience, the context, and the perceived intent behind the words. What reads to one reasonable person as a genuine threat reads to another as mere information.
- **Consent** requires that the agreement be informed, intentional, and uncoerced — and every one of those components has a threshold to set. How much information is *enough*? How deliberate must the choice be to count as intentional? At what point does pressure cross into coercion? Individual and cultural standards for each can differ widely among people acting entirely in good faith.

And beneath all three lies a further layer of unavoidable uncertainty: evaluating these claims requires modeling the internal states of other agents — what they knew, believed, valued, feared, and intended. Minds are not transparent. Even ideally rational observers, working from identical external evidence, will build somewhat different models of the mental facts, and the verdicts on harm, coercion, and consent inherit that variance.

So add another diagnostic entry. When two reasonable people appear to have the same information but disagree about whether an act was coercive, they may be evaluating differently specified propositions or applying different normative thresholds. They can both reason competently about different conditionals; whether either conditional is normatively defensible remains open to criticism.

## A Feature, Not a Flaw

The absolutist instinct treats this conclusion as a scandal: if reasonable people can permanently disagree about coercion, then morality is subjective and anything goes. The instinct is wrong, and the Conditionalist analysis shows exactly why. Once the conditions are fixed — these values, this threshold, this model of the agents' mental states — each verdict is objective. The slaveholder does not get to escape judgment by choosing flattering conditions; conditions can themselves be articulated, compared, and criticized. What agent-relativity removes is not objectivity but the fantasy of a single verdict issued from nowhere, binding on every vantage at once. Interpretive flexibility in our moral concepts is not a defect awaiting repair by sharper definitions. It is a structural feature of moral and social reasoning, which must operate across agents with different values, experiences, and informational vantages — and any definitional scheme that denied this would falsify the subject matter it claims to describe.

This also explains what precise definitions are actually *for*. They do not end moral debates, and it is no strike against them that they cannot. What they do is localize the disagreement. Without the definitions, a dispute over an alleged coercion is a shouting match between verdicts — *coercion!*, *not coercion!* — with nothing to grip. With them, the parties can trace their divergence to the exact condition where it lives: we agree the threat was made and agree compliance followed; we differ on credibility, and we differ because your model of the speaker's intent assigns weight to a history that mine discounts. At that point the moral dispute has been converted into an Aumann-style inquiry — a hunt through priors, information, and interpretive conditions — and *that* inquiry can make progress even when the verdicts never merge.

The theorem, rightly read, was never a promise of consensus. It is a calibration instrument, like the frictionless plane: a statement of what disagreement would have to mean among ideal agents, valuable precisely because we can measure our actual disagreements against it. When you and a peer cannot close a gap, run the full checklist. Different priors? Asymmetric information? A reasoning error? Or agent-relative conditions, filled in differently from where each of you stands? The first three call for more evidence and better updating. The fourth calls for something else: making the conditions explicit, so that both parties can see exactly which conditional each of them is evaluating, and decide whether the difference is one that argument can move. Reasonable disagreement, handled this way, is not a truce and not a failure. It is a map of where the conditions differ — and drawing that map is the only convergence worth having.
