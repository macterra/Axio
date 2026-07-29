# Phase 9 verification inventory and sequencing

Phase 9 verifies the reviewed manuscript before any promotion to `final`. This phase does not infer author approval from a clean build or from earlier merge approval.

Baseline: `41d14372` (`main`, after the Phase 8 identity follow-up).

## Current state

- **252 titled source records:** all `status: review`.
- **240 source-bearing records:** each carries one or more archived source IDs.
- **12 intentionally source-free records:** Preface, Introduction, Glossary, eight synthetic volume introductions, and the synthetic Volume 6 coda use `sources: []`.
- **586 source references / 581 unique archived posts:** every referenced ID resolves to `posts/<id>.html`.
- **5 reused source IDs:** each reuse is attributable to distinct chapters drawing from the same source essay; reuse is not a missing-source or duplicate-file error.
- **253 generated book pages:** the full build currently completes without internal-link, site-link, redirect, status, or part-assignment errors.
- **Toolchain baseline:** Pandoc `3.6.4` is pinned in `.pandoc-version` and enforced strictly by `pandoc_version.py`; the current local Pandoc matches. Current Python is `3.10.12`, but Python itself is not yet pinned for the book build.

## Existing automated coverage

`build-book.py` currently checks:

- recognized chapter statuses;
- complete, unique, and known manifest part assignments;
- Markdown links to book sources;
- root-relative links into the built site;
- publication-aware link rewriting;
- compatibility redirect targets and collisions;
- reproducible Pandoc version;
- generated navigation, index, redirects, and sitemap.

These checks are necessary but do not cover all Phase 9 requirements.

## Verification matrix

| Requirement | Baseline disposition | Next evidence |
|---|---|---|
| Full build and internal link validation | **Passing now** | Re-run from a clean checkout and compare generated-tree hashes/status. |
| Deterministic toolchain | **Partial** | Pandoc is pinned and matching; record Python/YAML dependency assumptions or pin them if output-sensitive. |
| Source IDs | **Passing automated check** | `verify-book.py` validates syntax, archive existence, explicit source-free records, and intentional reuse reporting. |
| Paper links | **Passing automated route check** | `verify-book.py` resolves all 58 unique generated `/papers/` destinations; interpretive authority remains an editorial judgment. |
| External links | **Passing dated baseline** | `verify-external-links.py` reports 45 URLs across 38 domains: 39 healthy, 6 access-restricted, and no hard failures. Re-run as an opt-in network check; apply the explicit repair/exception policy to any future 404/410. |
| Obsolete terminology and superseded claims | **Passing closeout** | `04-stale-language-inventory.md` through `08-stale-language-closeout.md` record the evidence, three repair families, rerun results, and retain dispositions. |
| Glossary anchors and defining-chapter links | **Passing automated check** | `verify-book.py` matches 101 terminology headings, glossary entries, and rendered anchors and validates their routes/fragments. |
| TODOs and drafting markers | **Passing inventory** | No TODO/TBD/FIXME/XXX, work-in-progress, coming-soon, or chapter-to-blog furniture remains; contextual draft language is intentional. |
| Dated news pegs | **Passing closeout** | `06-mutable-time-and-ai-scope.md` dates the two legal snapshots and scopes unversioned AI-state claims; `08-stale-language-closeout.md` classifies the remaining dated records and indexicals. |
| Chapter ordering and navigation | **Passing automated check** | `verify-book.py` independently recomputes and matches prev/up/next order for all 243 chapter pages; route checks cover indexes and redirects. |
| Continuous reading | **In progress; Volumes 1–5 complete** | `09-volume-1-continuity-and-copyedit.md` through `13-volume-5-continuity-and-copyedit.md` record the load-bearing sequence and its bounded repairs. Continue Volumes 6–9. |
| Promotion | **Blocked by policy, not by defect** | Require explicit author approval after verification and copyedit; no bulk status change is authorized now. |

## Source reuse dispositions

| Source ID | Reused by | Disposition |
|---|---|---|
| `164270270.defending-bayes-part-3` | Vol. 2 chs. 9 and 12 | Knowledge definition and Bayes defense draw distinct material from one source. |
| `166945477.demographics-without-coercion` | Vol. 6 ch. 22 and Vol. 7 ch. 16 | Fertility economics and migration governance use different parts of the same demographic argument. |
| `181528086.sentience-without-sovereignty` | Vol. 4 ch. 11 and Vol. 5 ch. 13 | Formal sovereignty and moral-standing treatments intentionally share provenance. |
| `181714344.alignment-is-a-domain-constraint` | Vol. 4 chs. 2 and 4 | Typed alignment and kernel architecture develop separate consequences of the same paper-era essay. |
| `183376003.axionic-agency-interlude-iv` | Vol. 4 chs. 10 and 15 | The negative growth result and program history intentionally cite the same interlude. |

## Sequence

1. **Complete — Reproducibility and source validator.** `verify-book.py` validates front matter, status and source metadata, archive existence, shared provenance, and byte-for-byte regeneration of `docs/book/` plus `docs/sitemap.xml`. `01-reproducibility-and-sources.md` records the result.
2. **Complete — Internal links, papers, glossary, and navigation.** `verify-book.py` now walks generated internal routes and fragments, checks paper targets, verifies the 101-entry terminology/glossary/rendered-anchor correspondence, and compares all chapter navigation against the manifest. `02-internal-authority-routes.md` records two repaired legacy links and the passing baseline.
3. **Complete — External link health.** `verify-external-links.py` supplies a bounded, network-dependent audit with explicit hard-failure and restricted-access dispositions. `03-external-link-health.md` records the 2026-07-28 baseline and the reviewed soft redirect.
4. **Complete — Obsolete terms, superseded claims, dated pegs, and blog furniture.** `04-stale-language-inventory.md` records the opening evidence; `05-residual-pattern-reification.md` through `07-final-agentive-shorthand.md` record the bounded repairs; `08-stale-language-closeout.md` reruns the original and expanded ledgers and gives every remaining family a retain disposition.
5. **In progress — Continuous reading and copyedit signoff.** `09-volume-1-continuity-and-copyedit.md` through `13-volume-5-continuity-and-copyedit.md` record Volumes 1–5 and close the load-bearing sequence. Continue with Volumes 6–9.
6. **Promotion decision.** Ask for explicit author approval only after the verification record is complete.

## Gate

A passing automated inventory does not authorize `review → final`. Promotion remains a distinct, explicit author decision.
