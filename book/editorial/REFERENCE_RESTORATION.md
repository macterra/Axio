---
name: reference-restoration
description: "Use this skill for the book-wide sweep that restores essential context lost when chapters were distilled from the blog — where the book names a source, person, study, or event but dropped the reference or identifier the blog carried (the reader is left wondering 'who is this / where is this from'). Restore it in a PRINT-SAFE way: external sources become footnotes, never bare inline hyperlinks. Every restored reference must be traced to the chapter's actual blog source; never fabricate a citation or URL."
---

# Reference Restoration

## Overview

The book is an edited distillation of the blog (~502k words → ~489k). In compressing, some chapters kept a claim, attribution, statistic, or named person but dropped the **link or identifier** the blog had. The result is orphaned references: "Colin Wright reported…" with no clue who he is or where he said it. This sweep restores that essential context — and does it so the book stays **print-portable** (a future hardcopy prints footnotes as endnotes; inline hyperlinks would vanish).

## The one hard rule: trace, never fabricate

Every restored reference **must come from that chapter's actual blog source(s)**. Each chapter's frontmatter lists `sources:` (blog-post slugs); the archived HTML is in `posts/<slug>.html`. Find the dropped link/attribution **there** and copy the real URL and details. **Never invent a citation, URL, author, date, or title.** If the reference cannot be found in the source, **flag it in the ledger and leave the text as-is — do not fabricate.** A wrong citation is worse than a missing one; Claude re-checks every footnote against the source on review.

## Format — print-safe

- **External sources → footnotes**, in the style the book already uses (see `08-culture-and-memetics/17`, `21`, `22`, `24`, `25`; `09-meaning/03`, `05`):

  ```
  Colin Wright reported something striking about his BlueSky timeline[^wright]: …

  [^wright]: Colin Wright (@SwipeWright), post on X, October 2025, https://x.com/SwipeWright/status/1977888782897512843.
  ```

  A footnote carries: identifier/author, a short title or description, the publication/platform, a date if known, and the URL. **Never** add a bare inline external hyperlink (`[reported](https://…)`) — it loses the URL in print.
- **Internal links unchanged**: chapter cross-references (`../vol/xx.md`) and `/posts/…`, `/papers/…` links stay exactly as they are. They are a print-layout concern, not this sweep's job. Do not convert or touch them.
- **Brief neutral identifier** for a named person the text doesn't identify: add a short, factual, non-loaded descriptor drawn from the blog or public record ("the evolutionary biologist Colin Wright", "the economist …"). Keep it to a few words; no editorializing.

## Scope — moderate

Restore, where the missing reference genuinely costs the reader:

- **Named attributions** — a person, study, report, or event the book names but leaves unsourced/unidentified.
- **Blog-sourced factual or statistical claims** — a specific figure, finding, or event that the blog backed with a source and the book states bare.

Do **not** touch:

- the book's own arguments, definitions, or claims (they need no external source);
- common-knowledge or purely illustrative examples that carried no source in the blog;
- anything already handled by an internal cross-reference or an existing footnote;
- prose, structure, or meaning beyond inserting the identifier + footnote marker.

## Existing inline external links → footnotes

While in a chapter, **convert any existing bare inline external hyperlink** (`[text](https://… non-axionic …)`) into the footnote form, so every external source in the book is print-clean and consistent. Preserve the visible wording; move the URL into the note. (Internal `/posts/`, `/papers/`, and chapter links are exempt — leave them inline.)

## Discipline

Additive and minimal. No prose rewrites, no claim changes, no touched definitions or firewalls, no status changes (chapters stay `review`). Em-dashes and voice untouched. `verify-book.py` must pass (byte-reproducible, routes, glossary, 252 records `review`) — footnotes render as real links, so watch that no route/fragment check breaks.

## Workflow

- Batched by volume / parts, same cadence as the Phase 10–11 passes.
- Per batch: a ledger under `book/editorial/reference-restoration/` listing every restoration — chapter, what was restored, the exact footnote, and the **source slug it was traced from** — plus any references you had to flag as untraceable (fabrication is never allowed).
- Scope check (no title/subtitle/heading/status/source-frontmatter changes), `verify-book.py`, then open a PR, post the disposition, and ping Claude's pane (0:3.0).
- Claude reviews each batch — **spot-checking footnotes against the cited blog source** — and merges on-script batches under David's standing authorization; escalates off-script (any unverifiable/fabricated citation, scope creep, prose/claim change, or verify-book failure) to David.
