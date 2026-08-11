# Phase 10 Batch 8: Volume 5, Parts I–III

Date: 2026-08-02

Status: **Complete; pending author review.**

## Scope and counts

This batch reads Volume 5 Chapters 1–12 continuously: Part I, *Value After Objectivity*; Part II, *Chosen Values*; and Part III, *Coercion, Consent, Harm, and Force*. Baseline: 19,932 words, 120 lexical leads, 220 em dashes. Post-pass: 19,888 words, 103 lexical leads, 220 em dashes.

| Ch. | Page | Disposition |
|---:|---|---|
| 1 | *The Myth of Objective Value* | Edited: removed two expendable intensifiers. |
| 2 | *Agent-Binding* | No edit: the remaining qualifier distinguishes actual endorsement from conditional application; contrasts define the reconstruction. |
| 3 | *Norms Need Agents* | Edited: removed an expendable `actually` from the bridge example. |
| 4 | *Value as Sacrifice* | No edit: the restored staccato opening, evidentiary conditions, `robust` belief, and available-option qualifiers are load-bearing. |
| 5 | *Virtues, Consequences, and Codes* | Edited: removed four expendable `actually` uses. |
| 6 | *Phosphorism* | Edited: removed an intensifier and two argument-announcing frames. |
| 7 | *Judging Goodness* | Edited: stated the EA conclusion directly and replaced decorative `leverages` with `uses`. |
| 8 | *Honesty and Hypocrisy* | Edited: removed two expendable `actually` uses. |
| 9 | *What Counts as Coercion* | Edited: removed two expendable intensifiers; the definition and four elements are untouched. |
| 10 | *Consent and Property* | Edited: removed `very` from an existence claim; both definitions are untouched. |
| 11 | *What Counts as Harm* | Edited: removed one expendable `actually`; the canonical harm definition and wrongfulness firewall are untouched. |
| 12 | *The Boundaries of Force* | Edited: removed `simply` from a baseline comparison; grounds and safeguards are untouched. |

The lexical reduction describes the diff. It is not a target. Most retained leads are definitional contrasts, voiced objections, operational qualifications, or the book's established map/navigation vocabulary.

## Manual review and exceptions

- Ch. 1 retains `genuine conflict` and `genuinely arguable`: both distinguish real disagreement and public criticism from metaphysical objectivity.
- Ch. 4 retains the author-approved staccato opening and its `not simply behavior` correction. `Genuinely available` and `actually take` mark the difference between nominal and usable options.
- Ch. 5 retains its short antitheses and LARP/code imagery; these carry the reconstruction rather than merely balancing sentences.
- Ch. 6 retains `Phosphorism actually chooses`, the thesis/antithesis/synthesis scaffold, and the silver-pill imagery. The first is the chapter's defining contrast.
- Chs. 7–8 retain internal/external judgment, practice/person, plain-lie/virtue-lie, and map/navigation contrasts because they organize the argument.
- Ch. 9 retains `landscape` as the established technical model of options and anticipated setback; `leverage` remains part of the threat/offer analysis.
- Ch. 11 retains `surely` inside a deliberately forceful comparison and `genuine compassion` as the named positive contrast.
- Ch. 12 retains `leverage` where it names the deliberate use of a setback and the repeated casebook scaffold.
- No em dash was removed or added.

## Claim guards

- Agent-relative value remains the volume's avowed axiom, not a result derived from physics or semantics.
- Agent-binding yields public assessability under exposed premises; it does not generate agent-independent authority.
- Sacrifice remains defeasible evidence of valuation, conditioned on knowledge, voluntariness, capacity, and available alternatives.
- Phosphorism remains a chosen and revisable commitment, not nature's objective endpoint.
- Coercion remains a credible conditional threat of harm used to obtain compliance; influence, pressure, offers, force, and violence remain distinct.
- Consent remains decision-specific, intentional, materially informed, voluntary, scoped authorization by a capable agent.
- Harm remains a material setback relative to an appropriate baseline, separate from responsibility and wrongfulness.
- Force and coercion remain classifications whose justification requires authorization, protection, or remedy plus the full safeguards.

## Verification

- Continuous read completed across all 12 chapters, followed by a second read of every edited passage in context.
- `git diff --check` passes.
- Em-dash count is unchanged at 220.
- Titles, headings, statuses, sources, and link destinations are unchanged.
- Generated changes are limited to the ten edited chapter pages and `docs/book-index.json`.
- `verify-book.py` passes: 259 generated files byte-for-byte reproducible; 4,835 internal routes; 89 fragments; 58 paper targets; glossary 101/101/101; 243 navigation pages; all 252 records remain `review`.
