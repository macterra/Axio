---
title: 'Bayes in the Wild'
subtitle: 'A dated ledger, audited as a calibration exercise'
status: review
sources:
  - 165642623.the-covid-19-lab-leak-hypothesis
---

The origin of SARS-CoV-2 remains scientifically and politically contested. Public discussion often turns uncertainty into team identity, while the evidential record contains major gaps. This makes the case useful for studying calibration—but dangerous as a stage for false precision.

Bayesian structure is relevant because the origin is a fixed but unknown historical fact and different hypotheses make evidence more or less expected. Yet a ledger is only as good as its hypothesis definitions, dependence assumptions, and likelihoods. The calculation below is preserved as a reconstruction of an earlier assessment so that its weaknesses can be inspected. It is not a current posterior endorsed by the book.

Two warnings govern the exercise. First, the numerical inputs were subjective judgments made against an earlier evidential record. Second, publishing inputs makes disagreement inspectable but does not make every input calibrated. If likelihoods are guessed, correlated, or selected after seeing the outcome, multiplication can amplify confidence without adding information.

## What Kind of Probability This Is

The virus has an origin. Whatever actually happened in Wuhan happened, once, and is now a settled historical fact — as fixed as the trillionth digit of π. There is no branch of the [Quantum Branching Universe](11-measure-and-credence.md) in which the same virus took a different path into the first human host; the fork, if there was one, is long behind us. So the probability we are after is not a **Measure**. Nothing is spread across branches here. It is pure **Credence**: the rational degree of confidence an agent should hold about a fact already determined but not yet known.

This matters because it sets the terms of success. We are not trying to discover a physical frequency. We are trying to make our confidence *track* a fact we cannot directly see, using the traces it left behind. That is a job for [Bayesian conditionalization](12-in-defense-of-bayes.md), and the cleanest form to run it in is odds.

## The Current Evidential Baseline

The World Health Organization's Scientific Advisory Group for the Origins of Novel Pathogens reported in June 2025 that all major hypotheses remained on the table because essential data had not been provided. It judged that the weight of available scientific evidence suggested zoonotic spillover, while emphasizing that the animal source and transmission chain had not been established. Environmental sampling linked susceptible animal material and viral material at the Huanan market, but did not prove that an infected animal introduced the virus. Intelligence agencies and political bodies have published differing assessments of laboratory-associated scenarios; those assessments should be distinguished from the scientific evidential record and evaluated according to their disclosed evidence. See the [WHO summary and SAGO report](https://www.who.int/news/item/27-06-2025-who-scientific-advisory-group-issues-report-on-origins-of-covid-19).

The responsible current conclusion is therefore not a fresh decimal. It is a structured state of uncertainty: zoonotic spillover is favored by the available scientific evidence; a laboratory-associated incident has not been excluded; missing records materially limit confidence. The historical ledger below is useful precisely because it shows how a different conclusion was produced.

## Reconstructing the Earlier Prior

Start before any Wuhan-specific fact is on the table. How often do novel human outbreaks originate in a laboratory rather than in nature? The overwhelming default is nature: SARS, MERS, Ebola, HIV, influenza after influenza — the pandemic record is a record of zoonotic spillover, humans meeting wildlife at the messy edges of agriculture and the wildlife trade. Laboratory-associated escapes exist, and are more common than the public imagines, but as a fraction of *pandemic-scale* events they are rare.

The earlier calculation assigned a one-in-ten prior to laboratory association—odds of $1:9$ against. That was an illustrative judgment, not a measured base rate: the reference class of "pandemic-scale events" is small, heterogeneous, and sensitive to how laboratory association is defined. A sensitivity analysis should vary the prior rather than present one figure as neutral.

Notice what this fixes that the loose version of the argument gets wrong. It is tempting to say "a natural outbreak *in Wuhan specifically* is improbable, so the prior is low." That smuggles the key piece of evidence into the prior and then double-counts it later. Keep them separate: the prior is set before we look at *where* the outbreak began. The location is evidence, and evidence belongs in the likelihood ratio.

## Reconstructing the Earlier Likelihood Ratios

A likelihood ratio asks one question of each piece of evidence: how much more (or less) probable is this observation if the lab hypothesis is true than if the natural hypothesis is true? Greater than one, it pushes toward the lab; less than one, toward nature; near one, it is noise dressed as signal. Bayes in odds form is then almost insultingly simple — multiply the prior odds by each ratio in turn:

$$\text{posterior odds} = \text{prior odds} \times \prod_i \text{LR}_i$$

**The location and research-program bundle.** The earlier ledger treated Wuhan's research institutions and the outbreak's location as its strongest evidence. That observation is relevant, but "very nearly guaranteed" under laboratory association and highly surprising under zoonosis were both unsupported simplifications. A valid likelihood must model multiple possible facilities and pathways, the geography and transport network of wildlife trade, outbreak detection, and the early concentration of cases around the Huanan market.

Bundling avoids one obvious double count, but the assigned ratio of $40$ is still especially fragile. It requires a denominator over plausible natural emergence locations and a numerator over laboratory-associated scenarios, neither of which was estimated from a validated model. The value should be read as the assumption driving the historical result, not as an empirical measurement.

**The unidentified intermediate host.** The earlier ledger assigned a ratio of $2$ toward laboratory association. That comparison was too simple: failure to identify an animal source can favor laboratory scenarios only relative to an explicit model of search effort, access, and expected discovery time. The market evidence and missing upstream data must be modeled jointly rather than selected asymmetrically.

**Institutional opacity.** Restricted access and missing data matter because different scenarios may predict different records and disclosure behavior. But political incentives to conceal embarrassment, uncertainty, or regulatory failure exist under multiple origins. The earlier ratio of $1.5$ was weak and subjective, and allegations about specific suppression or destruction require source-level verification.

**The absence of engineering signatures.** Genomic analyses have turned up no unambiguous fingerprint of deliberate manipulation — no telltale restriction sites, no obviously inserted sequence. Taken naively this favors natural origin. But adaptation by serial passage through cell culture or animals — a routine laboratory technique — would leave no such fingerprint, so the observation is far weaker counter-evidence than it first appears. It points the right way, against the lab, but only a little. Ratio: about $0.7$.

## Turning the Crank

Assemble the pieces. Prior odds $1:9$. Multiply through:

$$\text{posterior odds} = \frac{1}{9} \times 40 \times 2 \times 1.5 \times 0.7 \approx \frac{84}{9} \approx 9.3 : 1$$

The arithmetic converts those inputs to a Credence near $0.90$. It does not show that the inputs were calibrated. The factor of $40$ dominates, the evidence terms are not demonstrably independent, and the narrow **85-to-95-percent** band merely held the model structure fixed. It was an output of the earlier ledger, not a defensible current interval.

That was a strong conclusion, and this audit retracts it as the book's present verdict. The calculation treated alternative estimates as failures of nerve when they could instead reflect different causal models and greater attention to market and animal evidence. Numerical explicitness improves an argument only when its inputs are better grounded than the qualitative judgments it replaces.

## Where Reasonable People Diverge

Now earn the word *calibration*. Writing the calculation down makes assumptions visible, but disagreement about definitions, causal structure, data quality, and dependence can be more important than disagreement about a specific number.

Suppose you think the location ratio is badly inflated — that the Wuhan institute sits where it does *because* these viruses circulate in the broader region, that the early Huanan market cluster is real evidence of a zoonotic venue, and that a natural spillover reaching a city of eleven million with a major transport hub is not so freakish. Drop the ratio from $40$ to $15$. Then:

$$\frac{1}{9} \times 15 \times 2 \times 1.5 \times 0.7 \approx 3.5 : 1 \approx 0.78$$

Still favoring laboratory association, but already outside the claimed band. Varying the prior, reducing the opacity term, incorporating market evidence, or modeling dependence can move the result much further. The point is not that one altered ledger wins; it is that the posterior is structurally sensitive and should not be advertised without those alternatives.

The exercise must wear its date on its sleeve. Every ratio above records an earlier reading of the evidence and should not be carried forward unchanged. New animal-source evidence, verified laboratory records, or stronger genomic analysis would alter the comparison. Updating requires more than rerunning the same spreadsheet: sometimes the hypotheses, dependence structure, and event definitions must change as well.

## What the Exercise Shows

Strip away the specific virus and what remains is a portable procedure. Set a prior from base rates, honestly, before the vivid particulars seduce you. Isolate each piece of evidence and ask the one question a likelihood ratio asks, refusing to let a single coincidence be counted twice. Handle the emotionally loud evidence — the obfuscation, the institutional betrayal — with special suspicion, because outrage is not a likelihood ratio and the two are easy to confuse. Then multiply, read off the posterior, and publish the inputs so others can attack them.

The obfuscation deserves a last word, because it is the piece most likely to be mishandled in both directions. Joscha Bach's phrase for the affair — "virology's Chernobyl" — is apt not because the cover-up proves a leak but because of what the cover-up *did*: institutions charged with truth-seeking spent their credibility to protect themselves, and that expenditure is real damage whatever the virus's origin turns out to be. The Bayesian lesson is precise. Institutional stonewalling should move your Credence, because concealment is more expected from a party with something to hide — but it should move it only as far as its likelihood ratio warrants, which is not far, because concealment is also the reflex of institutions with nothing to hide but their own dignity. The failure mode of the lab-leak proponent is to let justified anger at the cover-up masquerade as evidence for the leak. The failure mode of the denier is to let the absence of a smoking gun masquerade as evidence of innocence. Both errors are the same error: substituting a feeling for a number.

I do not assign a replacement point estimate here. The current scientific record favors zoonotic spillover while leaving laboratory association unresolved because essential evidence is missing. The durable lesson is methodological: define hypotheses, separate evidence from priors, model dependence, test sensitivity, disclose sources, and distinguish an illustrative ledger from a calibrated conclusion. That is the epistemic work required before [decisions under uncertainty](23-deciding-under-uncertainty.md) begin.
