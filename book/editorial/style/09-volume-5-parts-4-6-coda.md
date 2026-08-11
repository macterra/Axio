# Phase 10 Batch 9: Volume 5, Parts IV–VI and Coda

Date: 2026-08-02

Status: **Complete; pending author review.**

## Scope and counts

This batch reads Volume 5 Chapters 13–27 continuously: Part IV, *Moral Standing*; Part V, *Rival Frameworks and Boundary Cases*; Part VI, *The Ethics of Viability*; and the coda, *The Price of Agency*. Baseline: 31,040 words, 176 lexical leads, 338 em dashes. Post-pass: 31,015 words, 156 lexical leads, 338 em dashes.

| Ch. | Page | Disposition |
|---:|---|---|
| 13 | *Sapientism* | Edited: removed two expendable `actually` uses and replaced generic praise with `formidable`. |
| 14 | *Against Utilitarianism* | No edit: degree qualifiers, vantage conditions, and the framework contrast carry substantive scope. |
| 15 | *Against Moral Extortion* | Edited: stated the unresolved choice directly and removed two expendable intensifiers. |
| 16 | *The Near Misses* | No edit: `really` belongs to quotation or a granted hypothetical; `actually` distinguishes modeled functions and real-system application. |
| 17 | *The Ethics of Existence* | Edited: replaced a significance-announcer with the stated task. |
| 18 | *The Ultimate Metagame* | Edited: removed two expendable `actually` uses; the analytic-game disclaimer is intact. |
| 19 | *The Viability Criterion* | Edited: removed four expendable intensifiers while preserving the descriptive/normative boundary. |
| 20 | *When Risk Is Harm* | No edit: the retained `not simply never` form states an essential exception to the prospective-risk rule. |
| 21 | *Measure Responsibility* | No edit: `very probably` belongs to the modeled rescue case; Measure remains descriptive. |
| 22 | *The Ethics of Viability* | No edit: the short invariant statement and structural/interior contrast are signature formulation. |
| 23 | *The Coexistence Protocol* | Edited: removed an expendable `actually` and stated Domain Exit's asymmetry directly. |
| 24 | *Viability Under Fire* | Edited: removed a significance-announcer and corrected sacrifice from a measurement of value to evidence of value. |
| 25 | *Innocence and Moral Debt* | Edited: removed two expendable `actually` uses; the contradiction remains explicit and unresolved. |
| 26 | *Sapient Agency Realism* | No edit: actual endorsement, genuine uncertainty, and the uncaring-reasoner hypothetical are claim-bearing. |
| 27 | *The Price of Agency* | Edited: removed one expendable `actually`; the signature close is untouched. |

The lexical reduction is descriptive. Most retained hits are named contrasts, voiced objections, explicit scope conditions, or technical robustness/navigation language.

## Bundled correctness fix

Chapter 24 previously said value is “measured by what you will give up.” That contradicted Chapter 4's bounded account: sacrifice is defeasible evidence of valuation, not its constitution or an infallible measurement. The sentence now says value is “evidenced by what you will give up.” The surrounding trolley argument is unchanged.

## Manual review and exceptions

- The Sapientism sentience/sovereignty distinction and animal-case challenge remain forceful; `genuinely suffer` is retained as a claim about real welfare, not generic emphasis.
- Singer's pond, Parfit's four-tell drumbeat, the Burning Hospital, Red/Blue Button, and innocent-shield contradiction retain their controlling images and payoff lines.
- `Surely` remains voiced by the critic in Chapter 15. `Really` remains quoted or voiced in Chapters 16 and 18.
- Metagame vocabulary remains analytic and mechanism-bound; no process is promoted to a hidden chooser.
- Robustness and navigation terms remain technical throughout the viability sequence.
- No em dash was removed or added.

## Claim guards

- Sapient standing remains substrate-neutral and distinct from sentience, benevolence, capability, and species membership.
- Utilitarianism is rejected under the book's chosen agency premise; no objective moral verdict is smuggled in.
- Moral pressure remains distinct from coercion unless a credible conditional threat of harm is controlled and threatened.
- Persistence and viability remain descriptive constraints, not objective value, teleology, or a duty to survive.
- Prospective harm remains material and attributable relative to an explicit baseline; wrongfulness requires separate justification.
- Measure weights modeled consequences but supplies no values, causal responsibility, or complete decision rule by itself.
- The Coexistence Protocol remains a fallible adjudication process, not an oracle or epistemic operating system.
- Chapter 25's innocent-shield conflict remains open; Chapter 24 is not falsely listed as resolving it.
- The coda retains the full authorization, evidence, necessity, proportionality, minimally harmful means, review, and restitution safeguards.

## Verification

- Continuous read completed across all 15 chapters, followed by a second read of every edited passage in context.
- `git diff --check` passes.
- Em-dash count is unchanged at 338.
- Titles, headings, statuses, sources, and link destinations are unchanged.
- Generated changes are limited to the nine edited chapter pages and `docs/book-index.json`.
- `verify-book.py` passes: 259 generated files byte-for-byte reproducible; 4,835 internal routes; 89 fragments; 58 paper targets; glossary 101/101/101; 243 navigation pages; all 252 records remain `review`.
