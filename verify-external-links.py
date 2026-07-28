#!/usr/bin/env python3
"""Audit external HTTP(S) links in the book manuscript.

This network-dependent check is intentionally separate from ``verify-book.py``.
HTTP 404/410 responses and malformed URLs fail the audit. Access restrictions,
rate limits, server errors, and transport failures are reported for review but
do not masquerade as proof that a citation is dead.
"""

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BOOK_GLOB = "[0-9][0-9]-*/*.md"
URL = re.compile(r"https?://[^\s<>\"']+")
HARD_FAILURES = {404, 410}
RESTRICTED = {401, 403, 405, 406, 418, 425, 429, 451}
USER_AGENT = (
    "Mozilla/5.0 (compatible; ArchitectureOfAgency-LinkVerifier/1.0; "
    "+https://axionic.org/book/)"
)


def clean_url(value):
    return value.rstrip(".,;:!?)]}")


def manuscript_urls():
    uses = {}
    for path in sorted(Path("book").glob(BOOK_GLOB)):
        for match in URL.finditer(path.read_text(encoding="utf-8")):
            url = clean_url(match.group(0))
            uses.setdefault(url, set()).add(str(path))
    return uses


def result_for_status(url, status, final_url):
    if status in HARD_FAILURES:
        category = "hard-failure"
    elif status in RESTRICTED:
        category = "restricted"
    elif 200 <= status < 400:
        category = "healthy"
    elif 400 <= status < 500:
        category = "other-client-error"
    else:
        category = "server-error"
    return {
        "url": url,
        "category": category,
        "status": status,
        "final_url": final_url,
    }


def check_url(url, timeout):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "Range": "bytes=0-4095",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return result_for_status(url, response.status, response.geturl())
    except HTTPError as exc:
        return result_for_status(url, exc.code, exc.geturl())
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "url": url,
            "category": "transport-error",
            "error": f"{type(exc).__name__}: {exc}",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--json",
        type=Path,
        help="write the complete result set to this path",
    )
    args = parser.parse_args()

    uses = manuscript_urls()
    malformed = [
        url for url in uses
        if urlsplit(url).scheme not in {"http", "https"}
        or not urlsplit(url).netloc
    ]

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(check_url, url, args.timeout): url
            for url in uses
            if url not in malformed
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["url"])

    counts = Counter(item["category"] for item in results)
    domains = {urlsplit(url).netloc.casefold() for url in uses}
    print("=== External link health ===")
    print(f"   {len(uses)} unique URL(s) across {len(domains)} domain(s)")
    for category in (
        "healthy",
        "restricted",
        "other-client-error",
        "server-error",
        "transport-error",
        "hard-failure",
    ):
        print(f"   {category}: {counts[category]}")

    review_categories = {
        "restricted",
        "other-client-error",
        "server-error",
        "transport-error",
        "hard-failure",
    }
    for item in results:
        if item["category"] not in review_categories:
            continue
        detail = item.get("status", item.get("error", "unknown"))
        print(f"   {item['category']}: {detail} {item['url']}")

    if args.json:
        payload = {
            "summary": {
                "urls": len(uses),
                "domains": len(domains),
                **dict(sorted(counts.items())),
            },
            "malformed": malformed,
            "results": [
                {**item, "sources": sorted(uses[item["url"]])}
                for item in results
            ],
        }
        args.json.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    failures = malformed + [
        item["url"]
        for item in results
        if item["category"] == "hard-failure"
    ]
    if failures:
        for url in malformed:
            print(f"   malformed: {url}")
        print(f"=== External link audit FAILED: {len(failures)} hard failure(s) ===")
        return 1

    print("=== External link audit complete ===")
    print("Restricted/transient results require review; they are not dead-link verdicts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
