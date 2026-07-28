# Internal authority routes, glossary, and navigation

Phase 9 extends `verify-book.py` from provenance and reproducibility into the reader's internal authority routes.

## Automated scope

After the reproducible rebuild, the verifier now:

- walks every generated book HTML file and resolves every internal `<a href>`;
- treats directory routes as their `index.html` targets;
- requires every internal target file to exist;
- requires every fragment to match an actual `id` or named anchor in its target;
- reports unique paper targets separately;
- compares the canonical terminology sheet and reader glossary as normalized one-to-one multisets;
- requires the source glossary order to match all rendered `<h3>` entries;
- rejects duplicate rendered glossary H3 IDs;
- reconstructs expected previous/up/next navigation from the manifest, source order, and publication statuses, then compares every chapter page.

## Baseline result

- Generated book HTML files walked: 258
- Internal hrefs resolved: 4,834
- Fragment links resolved: 89
- Unique generated paper targets: 58
- Canonical terminology headings: 101
- Reader glossary entries: 101
- Rendered glossary H3 anchors: 101
- Chapter navigation pages checked: 243
- Route, fragment, glossary, or navigation failures after repair: 0

The 58 paper targets comprise 57 distinct paper documents referenced by the manuscript plus the papers index used by site navigation. The manuscript contains 80 paper references across 21 source files. File existence is mechanically verified; the framing authority remains explicit: chapters govern the considered synthesis, while papers govern formal definitions, proofs, protocols, and run details.

## Defects found and repaired

Volume 1 chapter 18 contained two old bare HTML links:

- `163805376.intelligence-is-a-game-we-play.html`
- `200030842.the-ai-fork-is-about-agency.html`

In generated output they resolved relative to the Volume 1 directory and were broken. They now point to the current Volume 3 Markdown sources; the builder rewrites them to the correct generated chapter routes.

## Glossary and first-use disposition

The earlier glossary audit remains valid:

- all 101 canonical terminology entries have one reader-facing glossary entry after normalization;
- topical ordering in the internal terminology sheet and alphabetical ordering in the reader glossary are intentionally different;
- all 101 rendered glossary entry anchors exist and are unique;
- the nine selected front-matter first-use links—agency in the Preface and eight central terms in the Introduction—resolve to their glossary entries;
- each glossary definition routes to its governing chapter or chapter sequence, and the internal link walk validates those destinations and fragments.

This check establishes route integrity. It does not replace editorial judgment about whether a paper proves what a chapter says, or whether every later use of a term should link again.
