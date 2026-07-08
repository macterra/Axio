# Book Project Roadmap

*A multi-volume web book built from the Axio blog corpus, published at `docs/book/` on the existing GitHub Pages site.*

Status: **Volumes 1, 2, 5, and 6 fully drafted** — 105 chapters, ~218k words, live in draft status awaiting author review → review/final promotion. Remaining: Vols 3, 4, 7, 8, 9 (Vols 3/7 largest; author decided: no splits). · Created 2026-07-07 · Book title: **Axio**

## Vision

Transform the blog archive (593 published posts, 2022–2026) into a coherent multi-volume book. The book is web-native: one site, many volumes, with free hyperlinking between chapters, sections, and pages — and outward links to the blog archive (`docs/posts/`) and papers (`docs/papers/`) where the full technical record lives.

Posts are **raw material, not chapters**. Related posts get merged, arguments get rewritten for book flow, and each volume gets connective tissue: an introduction, transitions, and a conclusion. The blog is the lab notebook; the book is the considered statement.

## Proposed volume structure

Nine volumes, from a full thematic clustering of all 593 posts (every post assigned to exactly one primary volume; 21 excluded as housekeeping/navigational/one-offs). Working titles and counts:

| # | Volume (working title) | Posts | Scope |
|---|---|---|---|
| 1 | The Physics of Agency and the Branching Universe | ~74 | Thermodynamics of agency, QBU, Everettian probability, measure vs. credence, the Chaos sequence, "why is there something" |
| 2 | Conditionalism — Truth, Bayes, and Rationality | ~43 | Conditionalism, Defending Bayes, theories of truth, pancritical rationalism, anthropics, applied rationality |
| 3 | Minds and Machines — Consciousness, Intelligence, and AI | ~92 | Modeler-Schema consciousness, sentience/sapience, Turing tests, LLM cognition, AI risk discourse |
| 4 | Axionic Agency — The Alignment Program | ~71 | Sovereign kernel, reflective stability, structural alignment, the Phase I–IX program narrative and retrospectives |
| 5 | Value and Agency-Centered Ethics | ~64 | Subjectivism vs. moral realism, Valorism/Phosphorism, the "What Counts As" essays, Viability Ethics, anti-utilitarianism |
| 6 | Markets, Money, and Prosperity | ~47 | Subjective value, money/capital, defenses of markets, Bitcoin, incentives, prosperity and demographics |
| 7 | Liberty, Coercion, and Governance | ~92 | State-as-coercion, rights, justice, free speech, anarchism/archism, Axiocracy and post-democratic governance |
| 8 | Culture, Memetics, and Ideology | ~54 | Culture as schemas, egregores/mind viruses, ideological capture, narrative warfare, discourse pathologies |
| 9 | Meaning, Spirituality, and the Secular Sacred | ~35 | Credo essays, secular sacredness, Stoicism, conditional divinity, naturalistic meaning |

Notes on the structure:

- **Reading order is roughly foundational → applied**: physics/epistemology (1–2) ground mind/agency (3–4), which grounds ethics (5), which grounds economics/politics/culture (6–8), ending in meaning (9). Volumes remain independently readable; cross-links carry the dependencies.
- **Volumes 3 and 7 are oversized (~92 each)** — author decision (2026-07-08): NO split; the book is online-only, so volume length is not a binding constraint.
- **Straddle posts** (Viability Ethics as the on-ramp from Vol 5 to Vol 4, the Metagame series, free-speech posts split across 7/8, anthropics pair across 1/2) get resolved per-chapter during outlining; the catalog (Phase 1) records both primary and secondary volume assignments.
- **The 13 sequence-index posts** (Chaos, Defending Bayes, Physics of Agency, Conditionalism, Metagame, Axiocracy, AI, Axionic Agency, …) are excluded as chapters but are **pre-made chapter orderings** — each is an author-curated reading path. Mine them first when outlining volumes.

## Repository layout

Follows the existing pattern (`papers/` → `docs/papers/`): editable source at the top level, built HTML in `docs/`.

```
book/
  book.yaml                  # manifest: book title, volume order (chapter order comes from filename prefixes; status lives in chapter frontmatter)
  catalog.csv                # post_id → volume, secondary volume for straddles, notes
  00-front/                  # book-level front matter: introduction, how-to-read-this
  01-physics-of-agency/
    volume.md                # volume introduction (written, not compiled)
    01-<chapter-slug>.md
    02-<chapter-slug>.md
    ...
  02-conditionalism/
  ...
  09-secular-sacred/
docs/book/                   # build output — never hand-edited
  index.html                 # book landing page: volumes with status badges
  01-physics-of-agency/index.html + chapter pages
  ...
```

Chapter file conventions:

- Markdown with YAML frontmatter: `title`, `subtitle`, `status` (outline | draft | review | final), `sources` (list of post slugs the chapter reworks).
- Cross-links written as relative markdown links between source files (`[reflective stability](../04-axionic-agency/03-reflective-stability.md#kernel)`); the build rewrites them to site URLs and **fails the build on broken targets**.
- Links to blog posts and papers use site-root-relative URLs (`/posts/...`, `/papers/...` — the site serves from the domain root at axionic.org); the build validates these exist and rewrites them to relative URLs.

## Build pipeline

New script `build-book.py` (invoked by `update-site.sh` after `build-site.py`; standalone runnable for fast iteration):

1. Read `book.yaml`; render each chapter markdown → HTML with the site's existing styling (reuse the CSS-injection and markdown pipeline patterns from `build-site.py`'s papers processing).
2. Generate navigation: book index page, per-volume TOC pages, prev/next links within a volume, breadcrumbs (Book → Volume → Chapter), and a per-page section TOC from headings.
3. Resolve and validate all cross-links; give every heading a stable anchor id so sections are linkable.
4. Emit unfinished chapters only when `status` ≥ draft, with a visible status badge — the book publishes **incrementally**, volume by volume, chapter by chapter.
5. Add the book to `docs/sitemap.xml` and (optionally, later) to the site search index.

Safety check (verified): `build-site.py` only deletes `docs/posts/` on rebuild — `docs/book/` is safe. `build-book.py` owns and fully regenerates `docs/book/`.

## Phases

### Phase 0 — Infrastructure
Create `book/` skeleton, `book.yaml`, `build-book.py` with one stub chapter end-to-end; wire into `update-site.sh`; add a "Book" link to the site nav. *Exit: a stub chapter renders on the live site with working nav.*

### Phase 1 — Catalog
Materialize the thematic clustering into `book/catalog.csv`: every published post → primary volume (+ secondary where it straddles), with the 21 exclusions marked. This is the editorial source of truth; correct it by hand as understanding improves. *Exit: catalog reviewed by author.*

### Phase 2 — Volume outlines (one volume at a time)
For the active volume: read the assigned posts (start from the sequence-index posts where they exist), design a chapter list — each chapter names its source posts, its thesis, and what must be merged/cut/rewritten — and identify gaps needing genuinely new writing. Record in `volume.md` + `book.yaml`. *Exit: author-approved outline.*

### Phase 3 — Drafting (per volume)
Rework posts into chapters per the outline: merge sources, strip blog-isms (datedness, "last week I wrote…", Substack furniture), unify terminology against the glossary, add cross-links, write the volume introduction and conclusion. Chapters move outline → draft → review → final in `book.yaml`; drafts publish to the site as they land. *Exit: all chapters final; volume announced.*

### Phase 4 — Iterate
Repeat Phases 2–3 per volume. After the first two volumes, revisit book-level front matter, the volume ordering, and whether Vols 3 and 7 should split.

**Suggested starting volume: 5 (Value and Agency-Centered Ethics)** — it is the conceptual hub the applied volumes (6–8) hang off, mid-sized (~64 posts), and its Viability Ethics seam with Vol 4 is where the freshest thinking is. Alternative: start with 2 (Conditionalism, ~43 posts, already sequence-organized) as a smaller pipeline shakedown.

## Open decisions

- [x] Overall book title: **Axio**
- [ ] Which volume to draft first (recommendation above)
- [ ] Split Vols 3 and/or 7 into two volumes each (decide at their Phase 2)
- [ ] Author byline/collaboration credit convention for reworked chapters
- [ ] Whether book pages join the site-wide search index (defer until a volume is live)
