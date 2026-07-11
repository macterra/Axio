# Axio Editorial Workspace

This directory contains working editorial material for *Axio*. It is tracked in the repository and deliberately excluded from the published book.

`build-book.py` reads only volumes listed in `book/book.yaml` and only numbered Markdown chapters immediately inside those volume directories. `book/editorial/` is not listed in the manifest, so none of its contents are rendered into `docs/book/`.

## Publication boundary

- Never add `editorial` to `book/book.yaml`.
- Do not copy editorial files into a manifest-listed volume as numbered Markdown chapters.
- Editorial notes may link to manuscript sources for repository navigation.
- Published chapters must not link to editorial notes.
- Do not add this directory to `.gitignore`; its contents are part of the reviewed project record.

## Phase 1 control documents

- `argument-map.csv` inventories every chapter's thesis, premises, dependencies, distinctive contribution, main review question, structural function, and provisional disposition.
- `terminology.md` is the internal authority for terms of art during editing. It is not the future reader-facing glossary.
- `claim-calibration.md` defines how the edit distinguishes results, interpretations, arguments, conjectures, commitments, and illustrations.
- `repetition-ledger.md` identifies recurring material and assigns canonical treatments before compression begins.
- `architecture/` contains the Phase 2 book-wide audit and nine volume structural memos.

The argument map is intentionally provisional about keep/merge/move/cut decisions. Phase 1 establishes complete coverage; Phase 2 makes book- and volume-level structural decisions after reading the architecture as a whole.

## Updating the argument map

Run:

```bash
python3 book/editorial/build-argument-map.py
```

The generator derives the inventory from chapter metadata, internal links, and section structure. It fails if a chapter lacks frontmatter or if the generated map does not cover every numbered manuscript chapter. Editorial overrides for load-bearing theses and review questions live in the script and should remain narrow and explicit.
