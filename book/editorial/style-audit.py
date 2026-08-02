#!/usr/bin/env python3
"""Count mechanical Phase 10 style-review leads across the manuscript.

The counts nominate passages for close reading. They are not style verdicts.
Manual review remains responsible for reflexive tricolons, false-balance
endings, repeated sentence scaffolds, controlling images, and deletable
openings or closings.
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

import yaml


BOOK = Path("book")
DEFAULT_CSV = Path("book/editorial/style/00-baseline.csv")

PATTERNS = {
    "negative_parallelism": (
        r"\brather than\b",
        r"\binstead of\b",
        r"\bnot because\b",
        r"\bnot (?:merely|simply|only)\b",
        r"\bnot\b(?!\s+(?:because|merely|simply|only)\b)[^\n.!?]{0,100}\bbut\b",
    ),
    "lampshading": (
        r"\bthe load-bearing assumption is\b",
        r"\bthe crucial move is\b",
        r"\bthis is the part that does the work\b",
        r"\bthe key step\b",
        r"\bthe strongest objection is\b",
        r"\beverything depends on\b",
        r"\band that is the point\b",
        r"\bthis is where it bites hardest\b",
    ),
    "empty_opener": (
        r"\bin today'?s (?:fast-paced )?world\b",
        r"\bgreat question\b",
    ),
    "hedge_stack": (
        r"\bit'?s worth noting that\b",
        r"\bit'?s important to remember\b",
        r"\bit is worth noting that\b",
        r"\bit is important to remember\b",
    ),
    "restatement_closer": (
        r"\bin conclusion\b",
        r"\bultimately\b",
        r"\bat the end of the day\b",
    ),
    "tapestry_diction": (
        r"\bdelv(?:e|es|ed|ing)\b",
        r"\bnavigat(?:e|es|ed|ing|ion)\b",
        r"\blandscape(?:s)?\b",
        r"\brealm(?:s)?\b",
        r"\bjourney(?:s|ed|ing)?\b",
        r"\bleverag(?:e|es|ed|ing)\b",
        r"\brobust(?:ly|ness)?\b",
        r"\bseamless(?:ly|ness)?\b",
        r"\bvibrant(?:ly|ness)?\b",
        r"\btapestr(?:y|ies)\b",
        r"\btestament(?:s)?\b",
    ),
    "significance_announcer": (
        r"\bthe real question is\b",
        r"\bwhat matters here is\b",
        r"\bthe honest question is\b",
        r"\bthe deeper point is\b",
        r"\bwhat'?s worth noting is\b",
        r"\bwhat remains is\b",
    ),
    "intensifier": (
        r"\btruly\b",
        r"\bgenuinely\b",
        r"\breally\b",
        r"\bvery\b",
        r"\bactually\b",
        r"\bsimply\b",
    ),
    "preanswer_flattery": (
        r"\bexcellent question\b",
        r"\binsightful question\b",
        r"\bimportant question\b",
        r"\bfascinating question\b",
    ),
    "surely": (r"\bsurely\b",),
}


def manuscript_paths():
    return sorted(BOOK.glob("[0-9][0-9]-*/*.md"))


def split_record(path):
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", raw, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: missing YAML front matter")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: invalid YAML front matter")
    return metadata, match.group(2)


def prose_text(body):
    text = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", " ", text)
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\$[^$\n]+\$", " ", text)
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def count_patterns(text):
    lowered = text.lower()
    counts = Counter()
    for name, expressions in PATTERNS.items():
        counts[name] = sum(
            len(re.findall(expression, lowered, flags=re.IGNORECASE))
            for expression in expressions
        )
    counts["em_dash"] = text.count("—")
    return counts


def volume_label(path):
    directory = path.parent.name
    if directory == "00-front":
        return "Front Matter"
    match = re.match(r"(\d\d)-", directory)
    return f"Volume {int(match.group(1))}" if match else directory


def build_rows():
    rows = []
    for path in manuscript_paths():
        metadata, body = split_record(path)
        prose = prose_text(body)
        words = len(re.findall(r"\b[\w’'-]+\b", prose, flags=re.UNICODE))
        counts = count_patterns(prose)
        lexical_hits = sum(counts[name] for name in PATTERNS)
        total_leads = lexical_hits + counts["em_dash"]
        rows.append(
            {
                "path": str(path),
                "volume": volume_label(path),
                "title": metadata.get("title", ""),
                "words": words,
                "em_dash": counts["em_dash"],
                **{name: counts[name] for name in PATTERNS},
                "lexical_hits": lexical_hits,
                "total_leads": total_leads,
                "leads_per_1000_words": (
                    f"{total_leads * 1000 / words:.2f}" if words else "0.00"
                ),
            }
        )
    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    totals = Counter()
    for row in rows:
        totals.update({name: int(row[name]) for name in PATTERNS})
        totals["em_dash"] += int(row["em_dash"])
        totals["words"] += int(row["words"])

    print(f"Manuscript pages: {len(rows)}")
    print(f"Words scanned: {totals['words']}")
    for name in (*PATTERNS, "em_dash"):
        print(f"{name}: {totals[name]}")
    print("Volume totals:")
    volume_totals = {}
    for row in rows:
        volume = row["volume"]
        if volume not in volume_totals:
            volume_totals[volume] = Counter()
        volume_totals[volume]["pages"] += 1
        volume_totals[volume]["words"] += int(row["words"])
        volume_totals[volume]["lexical_hits"] += int(row["lexical_hits"])
        volume_totals[volume]["em_dash"] += int(row["em_dash"])
    for volume, counts in volume_totals.items():
        density = (
            (counts["lexical_hits"] + counts["em_dash"])
            * 1000
            / counts["words"]
        )
        print(
            f"  {volume:>12}: {counts['pages']:>3} pages, "
            f"{counts['words']:>6} words, {counts['lexical_hits']:>4} lexical, "
            f"{counts['em_dash']:>4} em dash, {density:>5.2f}/1k"
        )
    print("Highest lead densities:")
    for row in sorted(
        rows,
        key=lambda item: (float(item["leads_per_1000_words"]), item["total_leads"]),
        reverse=True,
    )[:15]:
        print(
            f"  {row['leads_per_1000_words']:>6}  "
            f"{row['total_leads']:>3}  {row['path']}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"write the baseline CSV (default: {DEFAULT_CSV})",
    )
    args = parser.parse_args()
    rows = build_rows()
    if len(rows) != 252:
        raise SystemExit(f"expected 252 manuscript pages, found {len(rows)}")
    write_csv(args.csv, rows)
    print_summary(rows)


if __name__ == "__main__":
    main()
