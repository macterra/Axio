#!/usr/bin/env python3
"""Verify book metadata, source provenance, and reproducible output.

The verifier is intentionally separate from status promotion. A passing run
does not change manuscript metadata or authorize ``review -> final``.
"""

import argparse
import hashlib
import html
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

BOOK = Path("book")
POSTS = Path("posts")
GENERATED = (Path("docs/book"), Path("docs/sitemap.xml"))
SOURCE_ID = re.compile(r"^[0-9]+\.[a-z0-9][a-z0-9-]*$")
VALID_STATUSES = {"outline", "draft", "review", "final"}
INTENTIONALLY_SOURCE_FREE = {
    Path("book/00-front/01-preface.md"),
    Path("book/00-front/02-introduction.md"),
    Path("book/00-front/03-glossary.md"),
    Path("book/01-physics-of-agency/volume.md"),
    Path("book/03-minds-and-machines/volume.md"),
    Path("book/04-axionic-agency/volume.md"),
    Path("book/05-value-and-ethics/volume.md"),
    Path("book/06-markets-and-money/26-coordination-is-not-salvation.md"),
    Path("book/06-markets-and-money/volume.md"),
    Path("book/07-liberty-and-governance/volume.md"),
    Path("book/08-culture-and-memetics/volume.md"),
    Path("book/09-meaning/volume.md"),
}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise ValueError("missing YAML front matter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("front matter is not a mapping")
    return data


def source_records():
    return sorted(BOOK.glob("[0-9][0-9]-*/*.md"))


def verify_metadata_and_sources():
    errors = []
    statuses = defaultdict(int)
    uses = defaultdict(list)
    records = source_records()
    source_free = 0

    for path in records:
        try:
            meta = frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        title = meta.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{path}: missing non-empty title")

        status = meta.get("status")
        if status not in VALID_STATUSES:
            errors.append(
                f"{path}: invalid status {status!r}; "
                f"expected one of {sorted(VALID_STATUSES)}"
            )
        else:
            statuses[status] += 1

        sources = meta.get("sources")
        if not isinstance(sources, list):
            errors.append(f"{path}: sources must be a list")
            continue
        if not sources and path not in INTENTIONALLY_SOURCE_FREE:
            errors.append(f"{path}: empty sources list is not allowlisted")
        if sources and path in INTENTIONALLY_SOURCE_FREE:
            errors.append(f"{path}: source-free allowlist entry now has sources")
        if not sources:
            source_free += 1

        for source_id in sources:
            if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id):
                errors.append(f"{path}: malformed source ID {source_id!r}")
                continue
            uses[source_id].append(path)
            archive = POSTS / f"{source_id}.html"
            if not archive.is_file():
                errors.append(f"{path}: missing source archive {archive}")

    referenced = sum(len(paths) for paths in uses.values())
    shared = {
        source_id: paths
        for source_id, paths in uses.items()
        if len(paths) > 1
    }

    print("=== Metadata and source provenance ===")
    print(f"   {'✓' if not errors else '✗'} {len(records)} titled records")
    print(
        "   Statuses: "
        + ", ".join(
            f"{status}={count}" for status, count in sorted(statuses.items())
        )
    )
    print(
        f"   {'✓' if not errors else '✗'} {referenced} source references, "
        f"{len(uses)} unique archived posts"
    )
    print(f"   ✓ {len(records) - source_free} records with archived sources; "
          f"{source_free} explicitly source-free")
    print(f"   ✓ {len(shared)} shared-provenance source ID(s) reported")
    for source_id, paths in sorted(shared.items()):
        joined = ", ".join(str(path) for path in paths)
        print(f"      {source_id}: {joined}")

    return errors


def hash_generated():
    snapshot = {}
    for target in GENERATED:
        if target.is_dir():
            paths = sorted(path for path in target.rglob("*") if path.is_file())
        elif target.is_file():
            paths = [target]
        else:
            paths = []
        for path in paths:
            snapshot[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def verify_rebuild():
    before = hash_generated()
    if not before:
        return ["generated baseline is missing"]

    print("=== Reproducible rebuild ===")
    result = subprocess.run(
        [sys.executable, "build-book.py"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return [f"build-book.py exited {result.returncode}"]

    after = hash_generated()
    changed = sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    )
    if changed:
        return [
            "rebuild changed generated output: "
            + ", ".join(changed[:20])
            + (" ..." if len(changed) > 20 else "")
        ]

    print(f"   ✓ {len(after)} generated file(s) are byte-for-byte reproducible")
    return []


def html_ids(path):
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r'\b(?:id|name)="([^"]+)"', text))


def resolve_internal_href(source, href):
    parsed = urlsplit(html.unescape(href))
    if parsed.scheme or parsed.netloc:
        return None
    if parsed.path.startswith("/"):
        target = Path("docs") / parsed.path.lstrip("/")
    elif parsed.path:
        target = source.parent / unquote(parsed.path)
    else:
        target = source
    target = Path(os.path.normpath(target))
    if target.is_dir():
        target /= "index.html"
    return target, unquote(parsed.fragment)


def verify_internal_routes():
    errors = []
    anchor_cache = {}
    href_count = 0
    fragment_count = 0
    paper_targets = set()

    generated_pages = sorted(Path("docs/book").rglob("*.html"))
    for source in generated_pages:
        text = source.read_text(encoding="utf-8")
        for href in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', text):
            if href.startswith(("mailto:", "javascript:", "data:")):
                continue
            resolved = resolve_internal_href(source, href)
            if resolved is None:
                continue
            target, fragment = resolved
            href_count += 1
            if not target.is_file():
                errors.append(f"{source}: missing internal route {href} -> {target}")
                continue
            if target.parts[:2] == ("docs", "papers"):
                paper_targets.add(target)
            if fragment:
                fragment_count += 1
                ids = anchor_cache.setdefault(target, html_ids(target))
                if fragment not in ids:
                    errors.append(
                        f"{source}: missing fragment #{fragment} in {target}"
                    )

    print("=== Internal routes and fragments ===")
    print(f"   {'✓' if not errors else '✗'} {href_count} internal href(s) "
          f"across {len(generated_pages)} generated book HTML files")
    print(f"   {'✓' if not errors else '✗'} {fragment_count} fragment link(s)")
    print(f"   {'✓' if not errors else '✗'} "
          f"{len(paper_targets)} unique paper target(s)")
    return errors


def normalize_heading(value):
    value = value.casefold().replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", "", value)


def markdown_h3(path):
    return [
        match.group(1).strip()
        for match in re.finditer(
            r"^###\s+(.+?)\s*$",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    ]


def rendered_h3(path):
    text = path.read_text(encoding="utf-8")
    headings = []
    for anchor, content in re.findall(
        r'<h3 id="([^"]+)">(.*?)</h3>', text, re.DOTALL
    ):
        plain = html.unescape(re.sub(r"<[^>]+>", "", content)).strip()
        headings.append((anchor, plain))
    return headings


def verify_glossary():
    errors = []
    terminology = markdown_h3(Path("book/editorial/terminology.md"))
    glossary = markdown_h3(Path("book/00-front/03-glossary.md"))
    rendered = rendered_h3(Path("docs/book/00-front/03-glossary.html"))

    terminology_norm = [normalize_heading(item) for item in terminology]
    glossary_norm = [normalize_heading(item) for item in glossary]
    rendered_norm = [normalize_heading(item[1]) for item in rendered]

    if Counter(terminology_norm) != Counter(glossary_norm):
        errors.append("terminology and glossary H3 entries differ after normalization")
    if glossary_norm != rendered_norm:
        errors.append("source and rendered glossary H3 entries differ")

    rendered_ids = [item[0] for item in rendered]
    if len(rendered_ids) != len(set(rendered_ids)):
        errors.append("rendered glossary contains duplicate H3 IDs")

    print("=== Glossary authority ===")
    print(f"   {'✓' if not errors else '✗'} {len(terminology)} terminology "
          f"heading(s), {len(glossary)} glossary entries, "
          f"{len(rendered)} rendered H3 anchor(s)")
    return errors


def nav_hrefs(path):
    text = path.read_text(encoding="utf-8")
    return {
        role: match.group(1) if match else None
        for role in ("prev", "up", "next")
        for match in [
            re.search(
                rf'<a class="book-{role}" href="([^"]+)"',
                text,
            )
        ]
    }


def verify_navigation():
    errors = []
    manifest = yaml.safe_load(Path("book/book.yaml").read_text(encoding="utf-8"))
    pages_checked = 0

    for volume in manifest["volumes"]:
        volume_dir = Path("book") / volume["slug"]
        chapters = []
        for path in sorted(volume_dir.glob("[0-9]*.md")):
            meta = frontmatter(path)
            if meta["status"] in {"draft", "review", "final"}:
                chapters.append(path)

        for index, path in enumerate(chapters):
            expected = {
                "prev": (
                    f"{chapters[index - 1].stem}.html" if index else None
                ),
                "up": (
                    "../index.html"
                    if volume.get("front_matter")
                    else "index.html"
                ),
                "next": (
                    f"{chapters[index + 1].stem}.html"
                    if index + 1 < len(chapters)
                    else None
                ),
            }
            generated = (
                Path("docs/book")
                / volume["slug"]
                / f"{path.stem}.html"
            )
            actual = nav_hrefs(generated)
            if actual != expected:
                errors.append(
                    f"{generated}: navigation {actual}, expected {expected}"
                )
            pages_checked += 1

    print("=== Chapter navigation ===")
    print(f"   {'✓' if not errors else '✗'} {pages_checked} chapter page(s) "
          "match manifest prev/up/next order")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources-only",
        action="store_true",
        help="skip the destructive-in-place rebuild comparison",
    )
    args = parser.parse_args()

    print(f"Python {sys.version.split()[0]}; PyYAML {yaml.__version__}")
    errors = verify_metadata_and_sources()
    if not args.sources_only:
        errors.extend(verify_rebuild())
        errors.extend(verify_internal_routes())
        errors.extend(verify_glossary())
        errors.extend(verify_navigation())

    if errors:
        for error in errors[:50]:
            print(f"   ✗ {error}")
        if len(errors) > 50:
            print(f"   ✗ ... {len(errors) - 50} additional error(s) omitted")
        print(f"=== Verification FAILED: {len(errors)} error(s) ===")
        return 1

    print("=== Verification complete ===")
    print("No status was changed; promotion still requires author approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
