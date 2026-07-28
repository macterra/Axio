#!/usr/bin/env python3
"""Verify book metadata, source provenance, and reproducible output.

The verifier is intentionally separate from status promotion. A passing run
does not change manuscript metadata or authorize ``review -> final``.
"""

import argparse
import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

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

    if errors:
        for error in errors:
            print(f"   ✗ {error}")
        print(f"=== Verification FAILED: {len(errors)} error(s) ===")
        return 1

    print("=== Verification complete ===")
    print("No status was changed; promotion still requires author approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
