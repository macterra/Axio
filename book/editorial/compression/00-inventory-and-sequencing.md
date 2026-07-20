# Phase 7 Compression Inventory and Sequencing

Baseline: July 18, 2026, immediately after Phase 6.

## Method

The inventory counts whitespace-delimited Markdown tokens in manuscript bodies, excluding YAML front matter. Volume totals include each volume introduction and numbered chapters. Links, inline code, and Markdown markers remain in the count, so the figures are editorial measures rather than publication typography.

The counts describe reading burden; they do not create a style target, review threshold, or ceiling. Structural evidence determines priority: repeated premises, conclusions, definitions, examples, pacing problems, and blurred chapter ownership. A chapter may remain long whenever its argument or evidence requires the length.

## Baseline by volume

| Volume | Files | Body words |
|---|---:|---:|
| 1. Physics of Agency | 29 | 44,236 |
| 2. Conditionalism | 26 | 48,549 |
| 3. Minds and Machines | 37 | 71,950 |
| 4. Axionic Agency | 16 | 49,132 |
| 5. Value and Ethics | 28 | 52,591 |
| 6. Markets and Money | 27 | 49,974 |
| 7. Liberty and Governance | 37 | 95,191 |
| 8. Culture and Memetics | 28 | 60,816 |
| 9. Meaning | 21 | 41,477 |
| **Total** | **249** | **513,916** |

Volume 7 is the largest continuous-reading burden. Volume 4 was selected first because its continuous-reading audit found unusually concentrated duplication: adjacent architecture chapters repeated primers and conclusions despite having distinct argumentative jobs. Its bounded, well-defined sequence also provided a tractable first test of the compression workflow before the longer and more politically interconnected Volume 7 pass.

## Sequencing decision

1. **Complete — Volume 4, Chapters 2–7: conceptual architecture.** Preserve six chapters and make the sequence inherit its results: alignment target → reflective-coherence problem → three kernel depths → stability theorem → semantic transport → commitments and conditional closure results.
2. **Complete — Volume 4, Chapters 8–15: evidence and program record.** The result is recorded in `01-volume-4-evidence-and-program.md`; repeated architecture and construction primers were compressed while the evidence registers remained distinct.
3. **Complete — Volume 7: continuous-reading pass.** The seven analytical clusters and fictional coda are recorded in `02-volume-7-legitimacy-and-rights.md` through `09-volume-7-fictional-coda.md`. The coda's narrative remains intact; its closing note now distinguishes fictional implementation candidates from institutions the analytical chapters established.
4. **In progress — Remaining local sequences.** Audit repetition and pacing in Volumes 1, 5, 6, and 8 within their local argumentative context before choosing the next bounded sequence; length alone does not mandate a cut.
5. **Cross-volume and line pass.** Sweep canonical definitions, familiar examples, conclusions, and prose rhythm after local ownership is stable.

## First-cluster result

The first bounded pass removed repeated setup and conclusions while retaining every chapter and formal distinction. Chapter 3 required no cut: its reflective-coherence thesis already did a distinct job.

| Chapter | Baseline | After pass | Change |
|---|---:|---:|---:|
| 2. What Can Be Aligned | 3,503 | 2,553 | −950 |
| 3. The Reflective Coherence Thesis | 2,736 | 2,736 | — |
| 4. The Sovereign Kernel | 3,059 | 2,418 | −641 |
| 5. Reflective Stability | 2,650 | 2,407 | −243 |
| 6. Structural Alignment | 3,659 | 2,649 | −1,010 |
| 7. What the Kernel Binds | 3,368 | 2,847 | −521 |
| **Cluster** | **18,975** | **15,610** | **−3,365 (17.7%)** |

The reduction is above the book-wide planning range because this sequence contained unusually concentrated duplication. It does not establish a target for later clusters.
