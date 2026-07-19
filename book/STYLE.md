# Axio book — drafting conventions

These rules govern how blog posts become book chapters. They apply to every volume.

## What a chapter is

A chapter is a *rework*, not a compilation: merge the source posts into one continuous argument, in the order that serves the argument rather than the order they were published. Do not invent new philosophical positions; the intellectual content comes from the sources. Structural rewriting, reconciling drifted terminology, and fixes named in the chapter's editorial notes are required.

**The blog is the record of the philosophy's evolution; the book is a coherent statement of its latest version.** When sources drift or a later post supersedes an earlier position, write every chapter from the latest position — do not present the drift as content. The exception is an honestly unresolved problem, which gets named as such (an open-problems section), never papered over. When new posts advance the position, the book updates to match.

## Voice

- First person singular, direct, confident. The author argues; he does not survey.
- Plain declarative prose. No academic throat-clearing ("In this chapter we will..."), no summary-of-what-was-just-said endings.
- Concrete examples carry the argument. Keep the sources' best examples; cut duplicated ones.
- Polemical edges are part of the voice — keep them where the argument earns them, cut them where they are just topical heat.

## Blog-isms to strip

- News pegs, dates, and occasions ("Last week...", "A recent tweet by...", "GPT-5 just..."). If a post was a reply to a named person's public claim, keep the engagement but recast it as a standing position, not an event.
- References to the blog itself, Substack furniture, subscription asks.
- "In a previous post..." — replace with a real cross-link or just make the claim.

## Mechanics

- Frontmatter: `title`, `subtitle`, `status` (set to `draft` when the rework is complete), `sources` (keep the full list).
- Open with the problem or a concrete case, not a definition. Definitions arrive when needed.
- Section headings: `##`, short, title case. Use sections only when length demands them.
- Cross-links between chapters: relative markdown links, e.g. `[when statements fail](04-when-statements-fail.md)`. Link on first natural mention; do not force links.
- Links to blog posts (`/posts/<id>.html`) only for supplementary material not merged into any chapter. Links to papers (`/papers/<name>.html`) for formal treatments.
- Math: inline `$...$`, display `$$...$$` (MathJax). Keep math only where it does real work.
- Terminology: **Measure** (objective branch weight) and **Credence** (subjective probability) are capitalized terms of art. QBU = Quantum Branching Universe, spelled out at first use in each chapter with a cross-link to its home chapter or volume.
- Length: whatever the argument and evidence require, and no more. Short and complete beats long and padded; there is no numeric target or ceiling.

## What not to do

- Do not soften claims the author makes firmly, and do not harden his hedges. Calibration is his, not yours.
- Do not add citations or scholarly apparatus the sources don't have.
- Do not leave editorial-note text, TODOs, or meta-commentary in the chapter body.
