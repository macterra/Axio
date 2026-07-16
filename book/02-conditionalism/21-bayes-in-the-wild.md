---
title: 'Bayes in the Wild'
subtitle: 'A dated ledger, audited as a calibration exercise'
status: review
sources:
  - 165642623.the-covid-19-lab-leak-hypothesis
  - 206337512.the-bayesian-trapdoor
---

The origin of SARS-CoV-2 remains scientifically and politically contested. Public discussion often turns uncertainty into team identity, while the evidential record contains major gaps. This makes the case useful for studying calibration—but dangerous as a stage for false precision.

Bayesian structure is relevant because the origin is a fixed but unknown historical fact and different hypotheses make evidence more or less expected. Yet a ledger is only as good as its hypothesis definitions, dependence assumptions, and likelihoods. The calculation below is preserved as a reconstruction of an earlier assessment so that its weaknesses can be inspected. It is not a current posterior endorsed by the book.

Two warnings govern the exercise. First, the numerical inputs were subjective judgments made against an earlier evidential record. Second, publishing inputs makes disagreement inspectable but does not make every input calibrated. If likelihoods are guessed, correlated, or selected after seeing the outcome, multiplication can amplify confidence without adding information.

## What Kind of Probability This Is

The virus has an origin. Whatever actually happened in Wuhan happened, once, and is now a settled historical fact — as fixed as the trillionth digit of π. There is no branch of the [Quantum Branching Universe](11-measure-and-credence.md) in which the same virus took a different path into the first human host; the fork, if there was one, is long behind us. So the probability we are after is not a **Measure**. Nothing is spread across branches here. It is pure **Credence**: the rational degree of confidence an agent should hold about a fact already determined but not yet known.

This matters because it sets the terms of success. We are not trying to discover a physical frequency. We are trying to make our confidence *track* a fact we cannot directly see, using the traces it left behind. That is a job for [Bayesian conditionalization](12-in-defense-of-bayes.md), and the cleanest form to run it in is odds.

## The Current Evidential Baseline

The World Health Organization's Scientific Advisory Group for the Origins of Novel Pathogens reported in June 2025 that all major hypotheses remained on the table because essential data had not been provided. SAGO judged that the weight of the evidence it could review suggested zoonotic spillover, while emphasizing that the animal source and transmission chain had not been established. Crucially, it also said that it could not assess a laboratory-biosafety breach because the necessary laboratory records and source materials were unavailable. That is SAGO's assessment of an incomplete public record, not an authority the book asks readers to trust in place of evidence. See the [WHO summary and SAGO report](https://www.who.int/news/item/27-06-2025-who-scientific-advisory-group-issues-report-on-origins-of-covid-19).

The record changed again on June 18, 2026. Director of National Intelligence Tulsi Gabbard released communications, analytic material, and whistleblower allegations while asserting that U.S.-funded WIV research caused the pandemic and that earlier intelligence assessments had been manipulated. That release is too consequential to omit, especially because it challenges the independence of some evidence previously presented as consensus. But the press release is an attributed institutional claim, not by itself a documented precursor-virus chain or a coordinated analytic estimate. Its underlying materials require claim-by-claim review: what do they establish about funding, influence on analysis, WIV capabilities, a specific pre-pandemic virus, and an actual accident? See the [ODNI release](https://www.odni.gov/index.php/newsroom/press-releases/press-releases-2026/4166-pr-11-26) and its [document index](https://www.odni.gov/files/documents/Newsroom/Reports%20and%20Pubs/COVID-19_Release_DNI_Gabbard_6-18_Index.pdf).

The public evidence cuts in both directions. Peer-reviewed analyses place the earliest known case concentration around the Huanan market and find susceptible-animal genetic material in virus-positive market samples; those findings favor a market-associated zoonotic pathway without identifying an infected animal or proving that the first spillover occurred there. The outbreak's appearance in Wuhan—the same city as laboratories conducting relevant coronavirus research, including WIV—is genuine evidence for a laboratory-associated pathway, especially when the records needed to test that pathway remain unavailable. Neither observation is "just a coincidence." The unresolved question is how strongly each should move Credence once alternative pathways, detection effects, and missing data are modeled. See the [early-epicenter analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC9348750/) and the [market wildlife analysis](https://doi.org/10.1016/j.cell.2024.08.010).

## A Hypothesis Tree, Not a Binary

The old ledger compressed the dispute into *natural* versus *laboratory-associated*. That is too coarse because the observations are not equally likely under every member of either family. A current analysis needs a mutually exclusive partition such as:

1. **$H_Z$: zoonotic spillover.** A naturally evolving virus reaches humans directly or through an intermediate animal, with the market serving as the spillover site, an amplification site, or an early detection site.
2. **$H_C$: research-associated exposure to a collected natural virus.** A worker is infected during collection, transport, culture, or other research activity involving a naturally occurring virus.
3. **$H_A$: laboratory adaptation or passage.** Research changes a collected virus through cell culture, animal passage, or selection without requiring a deliberately assembled genome.
4. **$H_E$: other deliberate engineering.** A laboratory construct contributes to the pandemic but does not satisfy the specific DEFUSE-linked claim below.
5. **$H_D$: the specific DEFUSE/EcoHealth vaccine-precursor claim.** An EcoHealth-linked program at or with WIV creates the recombinant vaccine or precursor that becomes SARS-CoV-2.

The last claim is normally a subset of engineered laboratory origin. It appears as a separate cell here only because $H_E$ has been defined to exclude it; otherwise adding probabilities for $H_E$ and $H_D$ would double-count. The partition also makes evidential work visible. WIV's location and research program bear on all three research-associated pathways. A detectable engineering signature bears more strongly on $H_E$ and $H_D$ than on $H_C$ or $H_A$. The DEFUSE proposal and questions about whether related work proceeded bear especially on $H_D$. Market clustering and susceptible-animal material bear most directly on $H_Z$, while leaving open whether the market amplified an infection introduced by another route.

The specific $H_D$ allegation appears in an August 2021 memo preserved in the [Department of Defense FOIA reading room](https://www.esd.whs.mil/Portals/54/Documents/FOID/Reading%20Room/DARPA/22-FRO-0457_SARS-COV-2_Orgins_Investigation_w_US_Govt_Prog_Undisclosed_Doc_Analysis_2021.pdf). Official hosting verifies that the memo exists and made the allegation; it does not verify the allegation. The public [DEFUSE proposal](https://www.documentcloud.org/documents/21066966-defuse-proposal/) and its [DARPA rejection document](https://assets.ctfassets.net/syq3snmxclc9/5OjsrkkXHfuHps6Lek1MO0/5e7a0d86d5d67e8d153555400d9dcd17/defuse-project-rejection-by-darpa.pdf) establish that closely relevant work was proposed and not funded by DARPA. They do not, without further records, establish that the proposed work proceeded elsewhere or produced SARS-CoV-2. That gap is exactly why $H_D$ must not inherit the full probability assigned to broader laboratory association.

## Reconstructing the Earlier Prior

Start before any Wuhan-specific fact is on the table. How often do novel human outbreaks originate in nature, during field or laboratory research, through adaptation, or through deliberate engineering? The historical record strongly favors zoonosis, but the relevant reference class is contestable: *all emerging diseases* is broader than *novel sarbecoviruses under active collection and experimentation*. A prior should therefore be reported across the hypothesis tree and tested under multiple defensible reference classes.

The earlier calculation assigned a one-in-ten prior to the whole laboratory-associated family—odds of $1:9$ against. That was an illustrative judgment, not a measured base rate: the reference class of "pandemic-scale events" is small, heterogeneous, and sensitive to how laboratory association is defined. It also concealed potentially large differences among $H_C$, $H_A$, $H_E$, and $H_D$. A sensitivity analysis should vary both the total prior and its allocation within the family rather than present one figure as neutral.

Notice what this fixes that the loose version of the argument gets wrong. It is tempting to say "a natural outbreak *in Wuhan specifically* is improbable, so the prior is low." That smuggles the key piece of evidence into the prior and then double-counts it later. Keep them separate: the prior is set before we look at *where* the outbreak began. The location is evidence, and evidence belongs in the likelihood ratio.

## Reconstructing the Earlier Likelihood Ratios

A likelihood ratio asks one question of each piece of evidence: how much more (or less) probable is this observation if the lab hypothesis is true than if the natural hypothesis is true? Greater than one, it pushes toward the lab; less than one, toward nature; near one, it is noise dressed as signal. Bayes in odds form is then almost insultingly simple — multiply the prior odds by each ratio in turn:

$$\text{posterior odds} = \text{prior odds} \times \prod_i \text{LR}_i$$

**The location and research-program bundle.** The earlier ledger treated the coincidence of city and research program as its strongest evidence, and it was right to treat that coincidence as evidence rather than wave it away. The calibration problem lies in the magnitude. "Very nearly guaranteed" under laboratory association and extremely surprising under zoonosis were both unsupported simplifications. A valid likelihood must model multiple facilities and laboratory pathways, the geography and transport network of wildlife trade, outbreak detection, and the early concentration of cases around the Huanan market.

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

## A Second Shape of Overreach

The failure the COVID ledger guards against is a *flat* one: a single multiplication of evidence terms, where the danger is a mispriced ratio, a coincidence counted twice, or an outrage smuggled in as data. But Bayesian reasoning fails in a second shape, harder to see because every step looks impeccable, and it happens along a *chain*. Consider a point of light on an old photographic plate — present in one exposure, gone from the next, carrying the same optical signature as the stars around it. That the light passed through the telescope rather than a scanner artifact or a dust speck is a real inference, honestly earned: *something produced light*. The trapdoor opens when that earned update is quietly inherited by the next link, and the next. Something produced light becomes there was an object; an object becomes an object in orbit; in orbit becomes artificial; artificial becomes not ours — until a plate has apparently photographed a satellite decades before satellites existed.

This is referential drift: evidence enters at a high-level category and exits, several unexamined steps later, at a favored story. The correction is the same discipline the flat ledger demands, run link by link rather than term by term. **Every arrow pays its own rent.** The likelihood ratio that lifts "light" to "object" says nothing about "orbit"; the one that lifts "object" to "orbit" says nothing about "artificial." Where a link carries no ratio of its own it is not a bridge but a gap — and a gap is not a passage, however badly the story on the far side wants to be reached. A chain of anomalies is only as strong as its weakest justified transition, which sits, almost always, much earlier and much lower than the conclusion pretends.

## What the Exercise Shows

Strip away the specific virus and what remains is a portable procedure. Set a prior from base rates, honestly, before the vivid particulars seduce you. Isolate each piece of evidence and ask the one question a likelihood ratio asks, refusing to let a single coincidence be counted twice. Handle the emotionally loud evidence — the obfuscation, the institutional betrayal — with special suspicion, because outrage is not a likelihood ratio and the two are easy to confuse. Then multiply, read off the posterior, and publish the inputs so others can attack them.

The obfuscation deserves a last word, because it is the piece most likely to be mishandled in both directions. Joscha Bach's phrase for the affair — "virology's Chernobyl" — is apt not because the cover-up proves a leak but because of what the cover-up *did*: institutions charged with truth-seeking spent their credibility to protect themselves, and that expenditure is real damage whatever the virus's origin turns out to be. The Bayesian lesson is precise. Institutional stonewalling should move your Credence, because concealment is more expected from a party with something to hide — but it should move it only as far as its likelihood ratio warrants, which is not far, because concealment is also the reflex of institutions with nothing to hide but their own dignity. The failure mode of the lab-leak proponent is to let justified anger at the cover-up masquerade as evidence for the leak. The failure mode of the denier is to let the absence of a smoking gun masquerade as evidence of innocence. Both errors are the same error: substituting a feeling for a number.

I do not assign a replacement point estimate here. The public record contains substantive evidence for a market-associated zoonotic pathway and substantive circumstantial evidence for several research-associated pathways, while the missing animal-source and laboratory records prevent confident calibration. The June 2026 release raises the weight that should be given to possible analytic suppression and makes source-level review more urgent; it does not eliminate the need to identify which laboratory hypothesis the evidence supports. The durable lesson is methodological: partition hypotheses, separate evidence from priors, model dependence, test sensitivity, disclose sources, and distinguish an illustrative ledger from a calibrated conclusion. That is the epistemic work required before [decisions under uncertainty](23-deciding-under-uncertainty.md) begin.
