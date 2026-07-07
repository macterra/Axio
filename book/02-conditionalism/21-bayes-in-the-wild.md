---
title: 'Bayes in the Wild'
subtitle: 'The lab-leak question as a calibration exercise'
status: draft
sources:
  - 165642623.the-covid-19-lab-leak-hypothesis
---

Ask where COVID-19 came from and you rarely get an answer; you get a team jersey. One camp treats the lab-leak hypothesis as self-evident and its deniers as captured; the other treats it as a racist conspiracy theory and its proponents as cranks. Both camps run on the same fuel — a confidence that vastly outstrips the arithmetic anyone has actually done. Neither has written the calculation down.

That is the interesting failure. The origin of a virus is exactly the kind of question Bayes' theorem was built for: a fixed but unknown fact, a scatter of imperfect clues, competing hypotheses that each predict the clues to different degrees. The machinery this volume has assembled — [Credence as distinct from Measure](11-measure-and-credence.md), updating as the routing of likelihoods into confidence, [the discipline of stating conditions](02-all-truth-is-conditional.md) — is not decoration for toy coins. It earns its keep on live, contested, emotionally loaded questions, and this is one. So let me do the thing almost no one in the debate does: put the numbers on the table where you can argue with them. A number you can argue with beats a conviction you cannot.

Two warnings before the crank turns. First, everything below is a **calibration exercise**, not a verdict from on high. The output is a Credence, and a Credence is conditional through and through — conditional on the evidential record as it stood when this was written, and conditional on the specific likelihoods I plug in. Change the record, or change the plausibility of a number, and the honest response is to *redo the arithmetic*, not to defend the conclusion. Second, the value here is the method. If you finish this chapter having memorized my posterior and forgotten how I got it, I have failed; if you finish it able to rebuild the calculation with your own inputs, I have succeeded even if your answer differs from mine.

## What Kind of Probability This Is

The virus has an origin. Whatever actually happened in Wuhan happened, once, and is now a settled historical fact — as fixed as the trillionth digit of π. There is no branch of the [Quantum Branching Universe](11-measure-and-credence.md) in which the same virus took a different path into the first human host; the fork, if there was one, is long behind us. So the probability we are after is not a **Measure**. Nothing is spread across branches here. It is pure **Credence**: the rational degree of confidence an agent should hold about a fact already determined but not yet known.

This matters because it sets the terms of success. We are not trying to discover a physical frequency. We are trying to make our confidence *track* a fact we cannot directly see, using the traces it left behind. That is a job for [Bayesian conditionalization](12-in-defense-of-bayes.md), and the cleanest form to run it in is odds.

## Setting the Prior

Start before any Wuhan-specific fact is on the table. How often do novel human outbreaks originate in a laboratory rather than in nature? The overwhelming default is nature: SARS, MERS, Ebola, HIV, influenza after influenza — the pandemic record is a record of zoonotic spillover, humans meeting wildlife at the messy edges of agriculture and the wildlife trade. Laboratory-associated escapes exist, and are more common than the public imagines, but as a fraction of *pandemic-scale* events they are rare.

So the base-rate prior should favor natural origin, and heavily. Call it roughly one-in-ten for a lab-associated origin — prior odds of $1:9$ against. You can argue that figure. Some will set it lower, insisting lab escapes essentially never seed pandemics; some will set it higher, noting how much gain-of-function work on exactly these viruses had ramped up. Fine — that disagreement is legible, which is the whole point. Write your own prior in the margin and carry it through.

Notice what this fixes that the loose version of the argument gets wrong. It is tempting to say "a natural outbreak *in Wuhan specifically* is improbable, so the prior is low." That smuggles the key piece of evidence into the prior and then double-counts it later. Keep them separate: the prior is set before we look at *where* the outbreak began. The location is evidence, and evidence belongs in the likelihood ratio.

## The Likelihood Ratios

A likelihood ratio asks one question of each piece of evidence: how much more (or less) probable is this observation if the lab hypothesis is true than if the natural hypothesis is true? Greater than one, it pushes toward the lab; less than one, toward nature; near one, it is noise dressed as signal. Bayes in odds form is then almost insultingly simple — multiply the prior odds by each ratio in turn:

$$\text{posterior odds} \;=\; \text{prior odds} \;\times\; \prod_i \text{LR}_i$$

**The location coincidence.** This is the heavyweight, and it deserves its weight. The outbreak announced itself in Wuhan — a northern industrial city hundreds of miles from the horseshoe-bat caves where SARS-related coronaviruses actually circulate, and home to the one institute on Earth running the most aggressive collection-and-enhancement program on exactly this family of viruses. Under the lab hypothesis, the outbreak beginning on that doorstep is very nearly guaranteed: that is where the relevant work was done. Under the natural hypothesis, a spillover could have surfaced anywhere across a vast range of southern China and Southeast Asia, and its landing in Wuhan of all places is a genuine coincidence.

I will bundle the geography with the programmatic fact — *this city, this lab, this exact line of research* — into a single ratio, deliberately, because they are not independent. The reason Wuhan is suspicious *is* that the lab does the work; to count "outbreak in Wuhan" and "lab does gain-of-function" as two separate multipliers would be to charge the same coincidence twice. Bundled, and being conservative about how much of the range a natural spillover could have used, I put this ratio around $40$. It is the number most worth contesting, and I will contest my own figure shortly.

**The missing intermediate host.** For SARS-1, the intermediate animal host was pinned down within months. For COVID-19, an intensive, prolonged, well-funded search has not produced one. Under natural origin, we expected to find the chain; its persistent absence is mildly more consistent with there being no animal chain to find. Mildly — absence of evidence is weak evidence here, and the search is genuinely hard. Ratio: about $2$.

**Institutional obfuscation.** The suppression of data, the obstruction of investigators, the destruction of records — this fits the predictable pattern of an institution covering an embarrassing accident. But be careful, because this is the number people most overreach on. States and bureaucracies obfuscate reflexively, over natural outbreaks too, to dodge blame and project control. Obfuscation is therefore only weakly diagnostic *between* the hypotheses, even though it is infuriating on its own terms. I give it about $1.5$, and I would not fight anyone who pushed it to $1$.

**The absence of engineering signatures.** Genomic analyses have turned up no unambiguous fingerprint of deliberate manipulation — no telltale restriction sites, no obviously inserted sequence. Taken naively this favors natural origin. But adaptation by serial passage through cell culture or animals — a routine laboratory technique — would leave no such fingerprint, so the observation is far weaker counter-evidence than it first appears. It points the right way, against the lab, but only a little. Ratio: about $0.7$.

## Turning the Crank

Assemble the pieces. Prior odds $1:9$. Multiply through:

$$\text{posterior odds} \;=\; \frac{1}{9} \times 40 \times 2 \times 1.5 \times 0.7 \;\approx\; \frac{84}{9} \;\approx\; 9.3 : 1$$

Odds of about $9:1$ convert to a Credence near $0.90$ — nine-to-one that the origin was a laboratory accident. Run the same machine with a slightly gloomier reading of the evidence and you land a little lower; with a slightly starker one, a little higher. The defensible band, holding the structure fixed and jostling the inputs within reason, is roughly **85 to 95 percent** for an accidental laboratory origin.

That is a strong conclusion, and I hold it. It is also *not* the 60-to-70 percent that cautious commentators often settle on — and the gap between their figure and mine is instructive. The cautious estimate almost always comes from feeling the pull of the location coincidence and then flinching from it, discounting by mood rather than by a number. Once you actually price the coincidence as a likelihood ratio, 60 percent is very hard to reach without assigning the geography a ratio near $3$ — which is to say, without pretending that an outbreak surfacing next to the one lab doing this work is only mildly surprising under natural origin. State that ratio out loud and few will defend it.

## Where Reasonable People Diverge

Now earn the word *calibration*. The virtue of writing the calculation down is that every disagreement becomes a disagreement about a specific number, which is the only kind worth having. So here is where an honest interlocutor can push, and what it does to the answer.

Suppose you think the location ratio is badly inflated — that the Wuhan institute sits where it does *because* these viruses circulate in the broader region, that the early Huanan market cluster is real evidence of a zoonotic venue, and that a natural spillover reaching a city of eleven million with a major transport hub is not so freakish. Drop the ratio from $40$ to $15$. Then:

$$\frac{1}{9} \times 15 \times 2 \times 1.5 \times 0.7 \;\approx\; 3.5 : 1 \;\approx\; 0.78$$

Still favoring the lab, but now short of the strong band — a genuinely different epistemic posture. Nudge the prior more toward nature as well, or zero out the obfuscation term, and you can walk it down toward a coin flip. I do not think those moves are correct, but they are *legible*: I can see exactly which input we disagree about and argue that one on its merits, instead of trading tribal certainties. That is what [reasonable disagreement](20-reasonable-disagreement.md) looks like when it is done well — not a clash of vibes but a reconciliation of ledgers.

And this is where the exercise must wear its date on its sleeve. Every ratio above is a reading of the evidential record as it stood at the time of writing. A confirmed intermediate host, discovered tomorrow, would drive the missing-host ratio below one and pull the location ratio down with it. A leaked internal record of a specific accident would send the numbers the other way. New genomic analysis could sharpen or dull the engineering-signature term. None of that would refute the method; all of it would demand that the method be *rerun*. A Credence that refuses to move when its inputs move is not a conviction, it is a fossil. The right relationship to this conclusion is the one [the discipline of updating](19-the-discipline-of-updating.md) prescribes: hold it at the strength the current evidence licenses, and stand ready to revise the moment the evidence does.

## What the Exercise Shows

Strip away the specific virus and what remains is a portable procedure. Set a prior from base rates, honestly, before the vivid particulars seduce you. Isolate each piece of evidence and ask the one question a likelihood ratio asks, refusing to let a single coincidence be counted twice. Handle the emotionally loud evidence — the obfuscation, the institutional betrayal — with special suspicion, because outrage is not a likelihood ratio and the two are easy to confuse. Then multiply, read off the posterior, and publish the inputs so others can attack them.

The obfuscation deserves a last word, because it is the piece most likely to be mishandled in both directions. Joscha Bach's phrase for the affair — "virology's Chernobyl" — is apt not because the cover-up proves a leak but because of what the cover-up *did*: institutions charged with truth-seeking spent their credibility to protect themselves, and that expenditure is real damage whatever the virus's origin turns out to be. The Bayesian lesson is precise. Institutional stonewalling should move your Credence, because concealment is more expected from a party with something to hide — but it should move it only as far as its likelihood ratio warrants, which is not far, because concealment is also the reflex of institutions with nothing to hide but their own dignity. The failure mode of the lab-leak proponent is to let justified anger at the cover-up masquerade as evidence for the leak. The failure mode of the denier is to let the absence of a smoking gun masquerade as evidence of innocence. Both errors are the same error: substituting a feeling for a number.

I come out at 85 to 95 percent for an accidental laboratory origin. I want you to notice that I could be wrong and the method still be right — that is the mark of a calibration you can trust rather than a dogma you must defend. The verdict is provisional and dated. The procedure is not. When the next contested origin, the next disputed catastrophe, the next question your tribe has already answered for you comes around, the move is the same: refuse the jersey, set the prior, price the evidence, turn the crank, and show your work. That is what it is to carry [decisions under uncertainty](22-deciding-under-uncertainty.md) out of the seminar room and into the world.
