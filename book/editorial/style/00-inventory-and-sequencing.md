# Phase 10 Style Inventory and Sequencing

Date: 2026-08-02

Status: **Baseline complete; manuscript batches pending.**

## Scope

Phase 10 applies `book/editorial/STYLE_GUIDE.md` to all 252 manuscript pages: three front-matter pages, nine volume introductions, and 240 chapters. The pass precedes author approval for `review → final`.

`book/editorial/style-audit.py` scans the prose body of each record and writes `00-baseline.csv`. It removes YAML front matter, fenced code, inline code, displayed math, inline math, HTML tags, and link destinations before counting. The CSV records page title, word count, em-dash count, lexical leads, total leads, and lead density.

Counts produce review leads. Human reading decides each disposition. The scanner deliberately over-selects negative parallelism and intensifiers. One passage can trigger more than one category. Several categories require manual review:

- reflexive tricolons;
- false-balance endings;
- repeated sentence scaffolds;
- competing or decorative metaphors;
- deletable opening and closing sentences; and
- abstract nouns that conceal a concrete claim.

Locations and dispositions will be recorded in each manuscript batch. The baseline establishes scope and order.

## Baseline

The scanner found 482,671 prose words.

| Mechanical lead | Count |
|---|---:|
| Negative-parallelism candidates | 1,731 |
| Structural lampshading | 6 |
| Empty openers | 0 |
| Hedge stacks | 0 |
| Restatement closers | 12 |
| Tapestry diction | 200 |
| Significance announcers | 36 |
| Intensifiers | 674 |
| Pre-answer flattery | 3 |
| `surely` | 11 |
| Em dashes | 5,302 |

The lexical patterns produced 2,673 leads. Em dashes produced 5,302. Their scale makes punctuation the largest mechanical task in the phase. Each retained dash must carry an interruption or sharp reversal that earns it.

| Section | Pages | Words | Lexical leads | Em dashes | Total leads per 1,000 words |
|---|---:|---:|---:|---:|---:|
| Front Matter | 3 | 6,289 | 21 | 15 | 5.72 |
| Volume 1 | 29 | 44,464 | 225 | 474 | 15.72 |
| Volume 2 | 26 | 47,919 | 256 | 558 | 16.99 |
| Volume 3 | 37 | 70,575 | 377 | 807 | 16.78 |
| Volume 4 | 16 | 41,113 | 235 | 510 | 18.12 |
| Volume 5 | 28 | 51,400 | 298 | 565 | 16.79 |
| Volume 6 | 27 | 49,104 | 252 | 504 | 15.40 |
| Volume 7 | 37 | 69,832 | 340 | 669 | 14.45 |
| Volume 8 | 28 | 60,154 | 360 | 729 | 18.10 |
| Volume 9 | 21 | 41,821 | 309 | 471 | 18.65 |

The highest-density pages identify pressure tests for the method. They occur across all nine volumes, so density cannot determine sequence. Reading order governs.

| Page | Leads | Leads per 1,000 words |
|---|---:|---:|
| Volume 8, *Echoes of Freud* | 85 | 32.88 |
| Volume 9, *Beyond Clown World* | 59 | 28.42 |
| Volume 7, *The Conversion of Coercion* | 62 | 25.77 |
| Volume 3, *Fallacies of Machine Understanding* | 60 | 25.65 |
| Volume 8, *The Wound and the Weapon* | 74 | 25.58 |
| Volume 5, *Phosphorism* | 51 | 25.55 |
| Volume 9, *Growing Up* | 47 | 25.12 |
| Volume 9, *What Stoicism Gets Right and Wrong* | 57 | 23.85 |
| Volume 3, *The Extropian Crucible* | 58 | 23.78 |
| Volume 1, *Creativity as Virtual Evolution* | 43 | 23.78 |

## Review sequence

The manuscript pass uses seventeen bounded PRs after this inventory. Manifest part boundaries keep each diff readable and preserve continuous local context.

1. Front matter and Volume 1 Parts I–II.
2. Volume 1 Parts III–V.
3. Volume 2 Parts I–IV.
4. Volume 2 Parts V–VI and coda.
5. Volume 3 Parts I–IV.
6. Volume 3 Parts V–VIII and coda.
7. Volume 4, including its coda.
8. Volume 5 Parts I–III.
9. Volume 5 Parts IV–VI and coda.
10. Volume 6 Parts I–IV.
11. Volume 6 Parts V–VII and coda.
12. Volume 7 Parts I–IV.
13. Volume 7 Parts V–VII and fictional coda.
14. Volume 8 Parts I–III.
15. Volume 8 Parts IV–V.
16. Volume 9 Parts I–II.
17. Volume 9 Parts III–IV and double envoi.

## Batch record

Every manuscript PR will include:

- the pages read and their baseline counts;
- line-level dispositions for lexical leads and manually found tics;
- retained hard-stop constructions awaiting or carrying author approval;
- word-count and em-dash-count changes;
- checks against the canonical claim boundaries affected by the prose;
- a continuous-read result for the edited sequence;
- `git diff --check` and `verify-book.py` results; and
- regenerated book output.

Claude reviews each draft PR. David decides contested voice exceptions and merges. Codex continues with the next batch after merge.

## Exit test

The phase closes when all 252 CSV rows have manuscript dispositions, every accepted edit is merged, every surviving hard-stop construction has an author-recorded reason, all affected sequences have been read continuously, and the deterministic verifier passes on the complete book.
