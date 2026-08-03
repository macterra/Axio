---
name: anti-affectation
description: "Use this skill when revising or critiquing the book's prose for affectation — phrasing that performs candor, depth, courage, or cleverness instead of just making the point. Companion to anti-slop-writing (STYLE_GUIDE.md): that skill kills generic-LLM tics; this one kills the author's own show-off tics — meta-signposting, performed candor/humility, and forced cleverness or twee metaphor. Disposition, not eradication: the book's voice is built on earned epigrams and one controlling image per passage, so protect those and cut only the ones that upstage the idea. Contested signature lines are the author's call, never the editor's."
---

# Anti-affectation

## Overview

Affectation is artificial manner adopted to impress — the writer stepping out of
the argument to be admired for candor, for depth, for nerve, for wit. It differs
from slop: slop is generic and says little; affectation is often distinctive and
*shows off*. The tell is that the phrase spends itself on the writer's
performance instead of the reader's understanding. This book has almost no slop
left after Phase 10, and it does not go purple often, so the surviving problem
is narrow and specific: a handful of recurring self-regarding tics, plus
scattered metaphors that reach too hard.

This skill is the companion to `anti-slop-writing`. Where the two overlap
(significance announcers, structural lampshading), the anti-slop rules govern;
this skill extends them into the three registers below.

## Operating principle

**Exercise the virtue; do not perform it.** If the writing is candid, it does
not need to say so. If a point is deep, the reader will feel the depth without
being told to. If a case is being steelmanned, state the strong version — do
not narrate the intention to be fair. And **earn the epigram**: a metaphor or a
punchy closing line stays only if it makes the idea clearer or more portable,
not if it merely makes the sentence quotable.

## The three registers

Each row is a hard look, not a hard stop — see the keep/cut test and the
protected list before removing anything.

| Register | Tell | Book examples | Fix |
|---|---|---|---|
| **1. Meta-signposting** | The prose leaves the argument to announce what it is doing or that a point is important, interesting, or deep. (Extends anti-slop's *significance announcer* and *structural lampshading*.) | "A note on names, **stated once**"; "The **interesting question** is…"; "deserves **its own** treatment"; "it is **worth pausing / dwelling**"; "**Here is the move / the reframe**"; "the question that **does the real work**" | **Tiered.** Auto-cut the pure announcers — "stated once", "worth pausing / dwelling", "Here is the move / the reframe", "does the real work". Judge "the interesting question / fact / part" and "deserves its own treatment" per instance (a few are legitimate). Delete the frame and make the move — pointing at the load-bearing part is a tell and is faintly condescending. |
| **2. Performed candor / courage / humility / fairness** | The writer advertises a virtue instead of enacting it: staged bluntness, staged modesty, staged steelmanning. | "the uncomfortable part, **which I refuse to soften**"; "Here it is, **stated without cushioning**"; "**I bite that bullet in the open**"; "here **I concede more than the polemic requires**"; "and I **know how that sounds**"; "I intend to take it **at full strength**" / "meet it **at its strongest**"; "**I will not pretend** otherwise" (recurs 7×) | Just do it on the page. Be blunt without announcing bluntness; state the strong version of the opponent without narrating your fairness; make the concession plainly. Delete the virtue-signal, keep the act. **If the wrapper carries a substantive *because*-clause — a real reason, not just the performance — keep the reason and cut only the wrapper; never compress away argument.** |
| **3. Forced cleverness / twee metaphor** | A phrase reaching to be memorable at the expense of the point: strained or cutesy metaphor, stacked alliteration, engineered aphorism, formula wit. Purple prose — grandiose, lush over-reach — is the far end of this register. | "**semantic perfume**"; "a digital spell summoning a self-organizing organism"; "a **phoenix of math**"; "camouflage for cowardice, marketing for mediocrity, fig leaves for failure"; the costume formula — "relativism **in a lab coat**", "the pond fallacy **in a black suit**", "the same disease **in the opposite jersey**"; the "**X with better ___**" formula — "paternalism with better **branding**", "Vitalism with better **furniture**"; "the buck stops **in the beholding**" | **Cut the misfires in-batch — these are dispositions, not proposals.** Say it plainly; prefer a concrete plain word to a clever near-miss. The keep/cut test is the guard: a line that earns its place (the passage's one controlling image, a motto, an argument-compressing epigram) is kept; anything that fails it is cut; flag only a line you genuinely cannot call. |

## The keep/cut test

Register 3 especially — but any candidate — passes through four questions.
Cut only what fails them.

1. **Deletion.** Remove the flourish. If nothing is lost but the flourish, cut it.
2. **Perform vs. exercise.** Is the writer *performing* a virtue (candor, nerve, depth, fairness) or *doing* it? Performing → delete the signal, keep the substance.
3. **Clarify vs. upstage.** Does the image make the idea clearer, or does the reader stop to admire the phrasing? Upstage → plain it.
4. **Rationing.** Is this the *one* controlling image of the passage, or the third ornament in the paragraph? Third → cut. (Same rule as anti-slop's rationing: one vivid metaphor lands, three is a worse writer.)

## Protected — the voice, not the target

The book's style is a Harris spine with a Dawkins controlling image and Dennett
sticky handles (see the voice profile in `STYLE_GUIDE.md`). That means a flat
punchy closer and one load-bearing metaphor per passage are **the style
working**, not affectation. Do not cut:

- the single controlling image of a chapter;
- a volume motto or deliberate refrain (e.g. "Keep the hunger; question the haunting");
- an epigram that *compresses* the argument rather than decorating it ("Waste is safer than theft").

**Author-protected epigrams (never cut, even if flagged):** "Keep the hunger;
question the haunting" (09/01), "Evil is not the refutation of this ethics; it
is the receipt" (05/27), "Both think they are gardeners. Both behave like
arsonists" (09/17), "Every arrow pays its own rent" (02/21).

**Author-protected atmospheric prose:** `06-markets-and-money/14-the-cybernetic-ghost-of-satoshi.md`
— its Halloween/ghost opening and "Ritual of Continuity" prose are deliberate
signature (the chapter is *themed* on the ghost), not affectation. Do not
ration, flatten, or de-purple it.

When a line is genuinely borderline — you cannot confidently call it signature
or misfire — **flag it for the author and leave it in.** That safety valve is
for real uncertainty, not for the obvious reach-too-hard cases, which are cut.
A protected line is never cut on the editor's own judgment.

## Detectable tics — run the greps

Registers 1 and 2 have surface forms and should be scanned, not eyeballed.
Register 3 has no reliable grep and must be read for. From repo root:

```
# Register 1 — meta-signposting
rg -n -i "stated once|the interesting (question|fact|part)|deserves its own|worth (pausing|dwelling)|here is the (move|reframe)|does the real work" book -g '*.md' -g '!editorial/**'

# Register 2 — performed candor / courage / humility
rg -n -i "i will not pretend|not going to pretend|at full strength|at its strongest|i know how (that|this) sounds|i refuse to soften|without cushioning|i bite that bullet|let me be (honest|blunt)|i concede more than" book -g '*.md' -g '!editorial/**'

# Register 3 — formula wit (partial; still read the chapter)
rg -n -i "with better \w+|in a lab coat|in a (black )?suit|in the opposite jersey" book -g '*.md' -g '!editorial/**'
```

Not every hit is guilty: "at full strength" and "true, full stop" have
load-bearing uses; "unpopular opinion" can be substantive. Judge each in place.
The `with better ___` grep is deliberately noisy — the tic is only the dismissive
formula *<abstract noun> with better <concrete noun>* ("utopia with better
manners", "paternalism with better branding", "barbarism with better
stationery", "naturalism with better poetry"). Ignore the substantive uses
("traders with better models", "a doctor with better outcomes").

## Disposition, not eradication

The volume is small. Most chapters carry one tic or none; a few concentrate it
(`06-markets-and-money/14-the-cybernetic-ghost-of-satoshi.md` is the densest
Register-3 chapter). Do not chase a count to zero — the target is the *misfire*,
not the device. A book with zero epigrams and zero controlling images would be
worse, not better.

## Workflow for the editor

Run this as a bounded per-volume/per-parts pass, same cadence and discipline as
the Phase 10 anti-slop batches.

- **Register 1 is tiered; Register 2 is cut-the-performance-keep-the-act.** Dispose the pure meta-announcers ("stated once", "worth pausing/dwelling", "Here is the move", "does the real work") and the candor/humility wrappers ("I will not pretend", "I know how that sounds", "I refuse to soften", "I bite that bullet", staged "at full strength") in the batch, keeping the underlying claim or concession. Judge "the interesting question" and "deserves its own treatment" per instance. Log each edit in the batch ledger under `book/editorial/style-affectation/` with the before/after.
- **Register 3 misfires are disposed in-batch too, gated by the keep/cut test.** Cut the reach-too-hard metaphors, purple over-reach, and the costume / "X with better ___" formulas. KEEP the author-protected epigrams (above) and any passage's one controlling image. Ping David's pane only for a line you genuinely cannot call signature-vs-misfire — not for the obvious misfires, and never cut a protected line on the editor's own judgment.
- **Hold em-dashes.** The em-dash cadence is settled: leave as-is. This pass touches em-dashes only when a demoted phrase happens to remove one; never as a target.
- **Preserve claims and firewalls exactly** as in the anti-slop pass — no canonical definition, claim boundary, or firewall may move.
- **Per batch:** scope check (no title / subtitle / heading / status / source changes), `verify-book.py` full pass (byte-reproducibility, routes, glossary, 252 records still `review`), ledger with claim guards, PR comment with the disposition, and a ping when the review is ready.

## Revision check

Before returning prose, scan for: (1) a phrase that announces the argument
instead of making it; (2) a virtue the writer is performing rather than doing;
(3) a metaphor or aphorism the passage would read better without. Apply the
keep/cut test. Dispose the clear cases; flag the contested ones for the author.
