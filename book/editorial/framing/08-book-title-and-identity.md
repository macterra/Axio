# Phase 8 Framing Audit: Book Title and Identity

## Finding

The published book had no title distinct from the repository and framework name. The manifest title, index heading, browser-title suffix, breadcrumbs, README, and build output all called it *Axio*. That name remains useful inside the work, but it does not tell a reader what the nine-volume argument is about.

Agency is the manuscript's actual spine:

- Volume 1 proposes its physical basis.
- Volume 2 asks how bounded agents can know and decide.
- Volume 3 separates minds, sentience, intelligence, and agency.
- Volume 4 studies reflective and sovereign agency.
- Volume 5 states a chosen ethics of protecting authorship.
- Volumes 6–8 examine coordination, power, and culture through their effects on agents.
- Volume 9 asks how finite agents inherit, revise, and make meaning.

## Decision

The reader-facing title is:

> **The Architecture of Agency**
>
> *A Naturalistic Philosophy of Minds, Values, Power, and Meaning*

“Architecture” fits the book's method: it distinguishes layers, boundaries, mechanisms, evidentiary registers, and failure modes rather than reducing agency to one substance or slogan. The subtitle names the main human-facing arc without promising that every topic is derived from one theorem.

## Identity boundary

The rename does not erase *Axio*:

- **The Architecture of Agency** is the book.
- **Axio** is the philosophical framework developed within it and the historical blog/repository identity.
- **Axionic Agency Lab** remains the publishing institution and site brand.

The repository path, public URLs, volume slugs, chapter filenames, and internal Axio terminology therefore remain unchanged.

## Implementation

The manifest owns the title and subtitle. The book builder now reads the manifest title for browser-title suffixes, book breadcrumbs, and build output instead of hard-coding *Axio*. The generated book index displays the new bibliographic identity, while the site navigation continues to display Axionic Agency Lab.

## Next cluster

Audit chapter titles and subtitles for claims stronger than their bodies and obsolete terminology, with URL and heading-anchor safety checked before any rename.
