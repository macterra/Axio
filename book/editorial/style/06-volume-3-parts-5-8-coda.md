# Phase 10 Batch 6: Volume 3, Parts V–VIII and Coda

Date: 2026-08-02

Status: **Complete; pending author review.**

## Scope

This batch reads Volume 3 Chapters 15–36 continuously. It covers intelligence, machine-understanding evidence, the Dialectic Catalyst, AI risk and power, and the succession coda. Em-dash editing remains deferred.

| Ch. | Page | Words | Lexical leads | Em dashes |
|---:|---|---:|---:|---:|
| 15 | *Intelligence Is a Game We Play* | 1,835 → 1,835 | 5 → 4 | 36 → 36 |
| 16 | *In Defense of IQ* | 1,861 → 1,860 | 12 → 11 | 31 → 31 |
| 17 | *Universality and Generality* | 1,992 → 1,992 | 10 → 10 | 24 → 24 |
| 18 | *Tool Bias* | 1,913 → 1,911 | 7 → 5 | 28 → 28 |
| 19 | *Fallacies of Machine Understanding* | 2,339 → 2,339 | 17 → 17 | 43 → 43 |
| 20 | *Pearl and the Machine* | 2,084 → 2,086 | 8 → 8 | 24 → 24 |
| 21 | *Fluency and Its Limits* | 2,387 → 2,386 | 18 → 17 | 38 → 38 |
| 22 | *The Turing Test and Its Successors* | 1,835 → 1,833 | 6 → 4 | 27 → 27 |
| 23 | *The Agency Criterion* | 2,394 → 2,394 | 19 → 19 | 36 → 36 |
| 24 | *The Dialectic Catalyst* | 1,464 → 1,463 | 6 → 5 | 18 → 18 |
| 25 | *The Discipline of Thinking With AI* | 2,166 → 2,166 | 13 → 13 | 34 → 34 |
| 26 | *Catalysts in the Wild* | 1,831 → 1,831 | 8 → 8 | 24 → 24 |
| 27 | *Artificial Intimacy* | 2,392 → 2,391 | 13 → 12 | 41 → 41 |
| 28 | *Programming After Programming* | 2,944 → 2,944 | 8 → 8 | 5 → 5 |
| 29 | *The AI Fork Is About Agency* | 2,481 → 2,479 | 18 → 16 | 35 → 35 |
| 30 | *Making Sense of P(doom)* | 1,296 → 1,295 | 12 → 11 | 16 → 16 |
| 31 | *The Cassandra and the Blueprint* | 1,516 → 1,516 | 10 → 10 | 11 → 11 |
| 32 | *Steelmanning Doom* | 1,909 → 1,908 | 11 → 10 | 29 → 29 |
| 33 | *The Politics of Safety* | 2,949 → 2,949 | 12 → 12 | 30 → 30 |
| 34 | *Coercion Beats Intelligence* | 2,193 → 2,193 | 13 → 13 | 9 → 9 |
| 35 | *The Extropian Crucible* | 2,439 → 2,439 | 13 → 13 | 45 → 45 |
| 36 | *Passing the Torch* | 1,115 → 1,115 | 8 → 8 | 17 → 17 |
| **Total** | **22 pages** | **45,335 → 45,325** | **247 → 234** | **601 → 601** |

## Dispositions

- **Edited:** chs. 15, 16, 18, 20–22, 24, 27, 29, 30, and 32. The style edits remove expendable intensifiers or replace `what remains` with the result/handoff itself.
- **No style edit:** chs. 17, 19, 23, 25, 26, 28, 31, and 33–36. Their flagged language is quoted, technical, heading-bound, degree-bearing, or part of a controlling rhetorical voice.
- **Factual consistency fix:** ch. 20's `AlphaZero cycles random-sampled moves` was false and contradicted the correction merged in Volume 1 through #108. It now says AlphaZero improves through self-play, search-guided move selection, and reinforcement from outcomes. The variation/selection analogy and open-endedness caveat are unchanged.

## Manual structural review

- Intelligence-as-game, tool, room, fluency/surface, catalyst, mirror, fork, ladder, race, and torch remain locally controlling images.
- Negative contrasts define universality/generality, fluency/understanding, thinking/choosing, catalyst/agent, intimacy/projection, risk/doom, and intelligence/coercion.
- Headings containing `Actually` or `Really` remain untouched for voice and anchor safety.
- The dense flagship chapters received no broad smoothing; their cadence and signature lines remain intact.

## Proposed author exceptions

1. Chs. 17–21 retain voiced `really`, `surely`, and `genuinely` claims where the text stages or answers objections.
2. Chs. 23–27 retain degree- and agency-bearing qualifiers, including `very good at seeming`, `actually mean it`, and `genuinely novel`.
3. Chs. 28, 30, and 35 retain anchor-bearing `Actually`/`Really` headings.
4. Chs. 31–36 retain participant-witness, risk-testing, freedom, provenance, and succession emphasis.
5. Technical `robust`, landscape, leverage, and navigation uses remain throughout.

## Claim guards

- Intelligence remains game-relative; universality and generality remain distinct.
- Fluency, understanding, agency, sentience, and authorship remain separate evidentiary claims.
- Current systems remain assessed under the Agency Criterion rather than categorically denied future agency.
- Catalyst language preserves human verification and whole-system responsibility.
- P(doom) remains time-, event-, model-, and intervention-indexed; high stakes do not create probability.
- Risk arguments remain conditional, non-fatalist, and separate from coercive policy conclusions.
- No em dash was removed or added.

## Verification

Complete:

- continuous read of all 22 chapters and a second read of every edited passage;
- `git diff --check` passes;
- the batch em-dash count is unchanged at 601;
- titles, subtitles, statuses, sources, headings, and Markdown link destinations are unchanged;
- the generated diff is limited to the 11 edited HTML pages and `docs/book-index.json`; and
- `python3 verify-book.py` passes: 259 generated files are byte-for-byte reproducible, 4,835 internal routes and 89 fragments resolve, the glossary is 101/101/101, navigation passes for 243 chapter pages, and all 252 records remain `review`.
