# Phase 10 Batch 5: Volume 3, Parts I–IV

Date: 2026-08-02

Status: **Complete; pending author review.**

## Scope

This batch reads Volume 3 Chapters 1–14 continuously, from cybernetic foundations through sentience, suffering, and machine welfare. Scanner matches are leads, not targets. Em-dash editing remains deferred.

| Ch. | Page | Words | Lexical leads | Em dashes |
|---:|---|---:|---:|---:|
| 1 | *A Cybernetic Lineage* | 1,842 → 1,839 | 16 → 13 | 27 → 27 |
| 2 | *What Is a Model?* | 1,982 → 1,980 | 9 → 7 | 19 → 19 |
| 3 | *Control Requires Models* | 1,433 → 1,431 | 6 → 4 | 14 → 14 |
| 4 | *Minds and Agents* | 1,184 → 1,183 | 4 → 3 | 14 → 14 |
| 5 | *The Origin of Meaning* | 1,559 → 1,557 | 8 → 6 | 13 → 13 |
| 6 | *The Geometry of Inner Speech* | 1,525 → 1,524 | 7 → 6 | 13 → 13 |
| 7 | *A Candidate Architecture of Consciousness* | 1,484 → 1,484 | 7 → 7 | 17 → 17 |
| 8 | *Beyond Dennett* | 1,778 → 1,777 | 10 → 9 | 12 → 12 |
| 9 | *Mirrors of the Mind* | 1,968 → 1,967 | 13 → 12 | 13 → 13 |
| 10 | *Why Zombies Don't Evolve* | 2,315 → 2,312 | 11 → 8 | 6 → 6 |
| 11 | *The Sentience Ladder* | 1,925 → 1,925 | 17 → 17 | 14 → 14 |
| 12 | *What Is Suffering?* | 1,823 → 1,821 | 6 → 4 | 25 → 25 |
| 13 | *Tests for Sentience* | 1,792 → 1,792 | 5 → 5 | 10 → 10 |
| 14 | *The AI Welfare Trap* | 2,273 → 2,273 | 8 → 8 | 8 → 8 |
| **Total** | **14 pages** | **24,883 → 24,865** | **127 → 109** | **205 → 205** |

## Dispositions

- **Chs. 1–6 — edited.** Removed expendable `simply`, `very`, `actually`, and `really` where the surrounding definitions already did the work. Retained ch1's `genuinely do` distinction for machine cognition; ch2's journey language as the Tube-map example; ch3's voiced `surely`; ch4's `genuinely hard question`; and ch6's `really are about words`, `very good`, and `genuinely verbal` where degree or task type matters.
- **Ch. 7 — no edit.** `Robust agency` is technical, and the remaining contrasts delimit the Modeler-Schema Theory as a candidate architecture rather than a proof of phenomenality.
- **Chs. 8–10 — edited.** Removed expendable intensifiers and replaced `The real question is` with the question itself. Retained ch8's `genuinely be a subject`, ch9's voiced `computation really happens` and soul-comparison `simply`, and ch10's navigation vocabulary. The zombie argument remains explicitly functionalist and does not claim evolutionary proof of phenomenality.
- **Ch. 11 — no edit.** Its `genuinely new situation` marks the deliberative/affective distinction; negative contrasts build the sentience ladder rather than decorate it.
- **Ch. 12 — edited.** Removed `very` and `actually`; the three-lever suffering definition and its candidate status remain intact.
- **Ch. 13 — no edit.** `Very good imitator` denotes the evidentiary bar created by high-quality simulation; the behavioral/architectural contrasts are the chapter's test design.
- **Ch. 14 — no edit.** `Genuinely qualifies` is part of the agency evidence threshold, and `robust` names embodied continuity rather than generic praise.

## Manual structural review

- The model, vehicle/driver, projection, mirror, zombie, ladder, and welfare-trap images remain locally controlled.
- Repeated contrasts separate constitutive from interpretive models, agent from mind, report from experience, behavior from architecture, sentience from sapience, and welfare from sovereignty.
- No reflexive tricolon, false-balance close, or deletable opening/closing was found.
- Ch. 10's significance announcement was the only structural lead recast; other explicit scaffolds organize actual definitions or objection sequences.

## Proposed author exceptions

1. Ch. 1 retains `genuinely do` for the modeling/experience/authorship distinction.
2. Ch. 3 retains the critic's `surely`; ch. 4 retains `genuinely hard question`.
3. Ch. 6 retains task- and degree-bearing verbal/imitator language and its signature shadow/interface lines.
4. Chs. 8–10 retain voiced or disputed `genuinely`, `really`, and `simply` phrases.
5. Chs. 11, 13, and 14 retain sentience/novelty/evidence qualifiers that affect the claims.
6. Technical `robust` and conceptual navigation language are retained throughout.

## Claim guards

- Constitutive models remain physically instantiated; interpretive models remain descriptions used by observers.
- Mind remains a proposed recursive self-model coupled to an agent, not a synonym for agency or proof of portability.
- Modeler-Schema Theory remains a candidate functional architecture and does not claim to derive phenomenality.
- Zombie arguments expose a functionalist dispute; they do not settle it by biology alone.
- Suffering retains three independent levers: world condition, representation, and preference.
- Sentience evidence remains distinct from sapient agency, authorship, sovereignty, and moral status.
- No em dash was removed or added.

## Verification

Complete:

- continuous read of all 14 chapters and a second read of every edited passage;
- `git diff --check` passes;
- the batch em-dash count is unchanged at 205;
- titles, subtitles, statuses, sources, headings, and Markdown link destinations are unchanged;
- the generated diff is limited to the 10 edited HTML pages and `docs/book-index.json`; and
- `python3 verify-book.py` passes: 259 generated files are byte-for-byte reproducible, 4,835 internal routes and 89 fragments resolve, the glossary is 101/101/101, navigation passes for 243 chapter pages, and all 252 records remain `review`.
