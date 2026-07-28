# Reproducibility and source verification

Phase 9 turns the inventory's first ad hoc checks into `verify-book.py`.

## Validator scope

The verifier:

- parses every immediate Markdown source record under the ten book source directories;
- requires non-empty titles, recognized statuses, and list-valued source metadata;
- permits empty source lists only for 12 explicit syntheses: Preface, Introduction, Glossary, eight volume introductions, and the Volume 6 coda;
- enforces the archived source-ID shape;
- requires `posts/<source-id>.html` for every source reference;
- reports shared source IDs with every consuming chapter;
- hashes every file under `docs/book/` and `docs/sitemap.xml`, runs the pinned build, and requires the post-build snapshot to match byte for byte;
- states explicitly that verification changes no status and grants no promotion authority.

`python3 verify-book.py --sources-only` runs the non-generating metadata and provenance checks. The default command includes the in-place rebuild comparison.

## Baseline result

- Python: `3.10.12` (recorded, not enforced)
- PyYAML: `5.4.1` (recorded, not enforced)
- Pandoc: `3.6.4` (pinned and strictly enforced by the build)
- Titled records: 252
- Statuses: 252 `review`
- Records with archived sources: 240
- Explicitly source-free syntheses: 12
- Source references: 586
- Unique archived posts: 581
- Missing or malformed source IDs: 0
- Shared-provenance IDs: 5, matching the inventory dispositions
- Generated files compared: 259 (258 under `docs/book/` plus `docs/sitemap.xml`)
- Byte differences after rebuild: 0

## Toolchain disposition

Pandoc is the output-sensitive renderer and remains exactly pinned. The verifier records Python and PyYAML versions so drift is visible, but does not yet reject other versions: the builder uses Python's standard library for output and PyYAML for plain manifest/front-matter data. The byte-for-byte rebuild comparison is the operative output test. If a Python or PyYAML change alters output, verification fails and the dependency can then be pinned with evidence rather than assumption.

## Limits

This cluster does not test external HTTP availability, paper authority, glossary first-use policy, stale terminology, dated claims, continuous reading, or copyedit approval. Those remain sequenced Phase 9 work.
