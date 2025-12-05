"""
Axio Bootstrap Utilities
------------------------

Paste this cell into a fresh ChatGPT Python environment after uploading
your latest `search-index.json`. Then run it once.

Assumptions:
- The uploaded file is available as: /mnt/data/search-index.json
  (If the path or name differ, change AXIO_INDEX_PATH below.)

Provides:
- Navigation & browsing over the Axio corpus
- Simple TUI-like viewer
- Search and analysis helpers
- Sequence and Index generators
- A consolidated help() menu
"""

import json
import math
import re
from pathlib import Path
from typing import List, Dict, Optional

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

AXIO_INDEX_PATH = Path("/mnt/data/search-index.json")

# Global cache of the corpus and pagination state
_AXIO_DATA: Optional[List[Dict]] = None
_PAGINATION = {
    "page": 1,        # 1-based current page
    "page_size": 20,  # posts per page
}


# ---------------------------------------------------------------------
# Internal loading
# ---------------------------------------------------------------------

def _load_axio_data() -> List[Dict]:
    """
    Internal: load and cache the Axio JSON corpus from AXIO_INDEX_PATH.
    The JSON must be a list of dicts with at least:
      - id
      - title
      - subtitle (optional)
      - date
      - content
    """
    global _AXIO_DATA
    if _AXIO_DATA is None:
        if not AXIO_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"Axio index not found at {AXIO_INDEX_PATH}. "
                f"Upload `search-index.json` and/or adjust AXIO_INDEX_PATH."
            )
        with AXIO_INDEX_PATH.open("r", encoding="utf-8") as f:
            _AXIO_DATA = json.load(f)
    return _AXIO_DATA


# Initialize corpus and total count
_AXIO_DATA = _load_axio_data()
TOTAL_POSTS = len(_AXIO_DATA)


# ---------------------------------------------------------------------
# Core browsing: list_posts
# ---------------------------------------------------------------------

def list_posts(
    limit: Optional[int] = 20,
    contains: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 20,
) -> List[Dict]:
    """
    List basic metadata for posts (date, id, title).

    Args:
        limit (int or None):
            Max number of posts to show (ignored if `page` is set).
            Use None to show all (non-paginated mode).
        contains (str or None):
            Case-insensitive substring filter applied to title OR subtitle.
        page (int or None):
            1-based page index for pagination mode.
            If provided, `limit` is ignored and `page_size` is used.
        page_size (int):
            Number of posts per page (default: 20).

    Returns:
        List[Dict] with keys: date, id, title.
    """
    data = _load_axio_data()
    # Sort newest first by ISO timestamp
    sorted_data = sorted(data, key=lambda d: d.get("date", ""))[::-1]

    # Optional text filter on title/subtitle
    if contains:
        needle = contains.lower()
        sorted_data = [
            d for d in sorted_data
            if needle in (d.get("title") or "").lower()
            or needle in (d.get("subtitle") or "").lower()
        ]

    # Pagination mode overrides limit
    if page is not None:
        if page < 1:
            page = 1
        start = (page - 1) * page_size
        end = start + page_size
        sliced = sorted_data[start:end]
        _PAGINATION["page"] = page
        _PAGINATION["page_size"] = page_size
    else:
        if limit is None:
            sliced = sorted_data
        else:
            sliced = sorted_data[:limit]

    out = []
    for d in sliced:
        record = {
            "date": d.get("date"),
            "id": d.get("id"),
            "title": d.get("title"),
        }
        out.append(record)
        print(f"{record['date']}  |  {record['id']}  |  {record['title']}")

    return out


# ---------------------------------------------------------------------
# Pagination helpers: next, prev, home, end, status, goto
# ---------------------------------------------------------------------

def next() -> List[Dict]:  # noqa: A001 - intentionally named next()
    """
    Move forward one page using the current pagination state.

    Returns:
        List[Dict] of the newly displayed posts (same format as list_posts).
    """
    data = _load_axio_data()
    total = len(data)
    ps = _PAGINATION["page_size"]
    p = _PAGINATION["page"]
    max_page = math.ceil(total / ps) if ps > 0 else 0

    if p >= max_page:
        print("Already at last page.")
        return []
    return list_posts(page=p + 1, page_size=ps)


def prev() -> List[Dict]:
    """
    Move back one page using the current pagination state.

    Returns:
        List[Dict] of the newly displayed posts (same format as list_posts).
    """
    ps = _PAGINATION["page_size"]
    p = _PAGINATION["page"]
    if p <= 1:
        print("Already at first page.")
        return []
    return list_posts(page=p - 1, page_size=ps)


def home() -> List[Dict]:
    """
    Jump to the first page (newest posts) using current page_size.

    Returns:
        List[Dict] of the displayed posts.
    """
    ps = _PAGINATION["page_size"]
    return list_posts(page=1, page_size=ps)


def end() -> List[Dict]:
    """
    Jump to the last page (oldest posts) using current page_size.

    Returns:
        List[Dict] of the displayed posts.
    """
    ps = _PAGINATION["page_size"]
    total = len(_load_axio_data())
    max_page = math.ceil(total / ps) if ps > 0 else 0
    return list_posts(page=max_page, page_size=ps)


def status() -> Dict:
    """
    Show current pagination status.

    Returns:
        Dict with:
            - page
            - page_size
            - total_posts
            - total_pages
    """
    total = len(_load_axio_data())
    ps = _PAGINATION["page_size"]
    p = _PAGINATION["page"]
    total_pages = math.ceil(total / ps) if ps > 0 else 0

    info = {
        "page": p,
        "page_size": ps,
        "total_posts": total,
        "total_pages": total_pages,
    }
    print(f"Current page: {p}")
    print(f"Page size: {ps}")
    print(f"Total posts: {total}")
    print(f"Total pages: {total_pages}")
    return info


def goto(page: int) -> List[Dict]:
    """
    Jump directly to a specific page number using the current page_size.

    Args:
        page (int): 1-based page number.

    Returns:
        List[Dict] of the displayed posts.
    """
    total = len(_load_axio_data())
    ps = _PAGINATION["page_size"]
    total_pages = math.ceil(total / ps) if ps > 0 else 0

    if page < 1 or page > total_pages:
        print(f"Page {page} out of range (1..{total_pages}).")
        return []
    return list_posts(page=page, page_size=ps)


# ---------------------------------------------------------------------
# TUI-like viewer
# ---------------------------------------------------------------------

def view(page: Optional[int] = None) -> None:
    """
    TUI-like viewer for the Axio corpus.

    - Shows current page (or given page) with a header and navigation hints.
    - Uses existing pagination state.
    - Use next(), prev(), home(), end(), goto(), status() to navigate.

    Args:
        page (int or None): page to show; if None, uses current pagination page.
    """
    data = _load_axio_data()
    total = len(data)

    if page is None:
        page = _PAGINATION["page"]

    ps = _PAGINATION["page_size"]
    total_pages = math.ceil(total / ps) if ps > 0 else 0

    print("=" * 80)
    print(f" Axio Browser  |  Page {page}/{total_pages}  |  Page size: {ps}  |  Total posts: {total}")
    print("=" * 80)
    print("Commands: home()  end()  next()  prev()  goto(n)  status()")
    print("-" * 80)
    list_posts(page=page, page_size=ps)
    print("=" * 80)


# ---------------------------------------------------------------------
# Post access
# ---------------------------------------------------------------------

def get_post(post_id: str, show_content: bool = False) -> Optional[Dict]:
    """
    Retrieve a single post by its ID.

    Args:
        post_id (str):
            Full ID string from the JSON index, e.g.:
            "162560090.the-physics-of-agency-part-5-the"
        show_content (bool):
            If True, prints the full content to stdout.

    Returns:
        Dict with keys: id, title, subtitle, date, content; or None if not found.
    """
    data = _load_axio_data()
    for d in data:
        if d.get("id") == post_id:
            if show_content:
                print(f"# {d.get('title')}\n")
                if d.get("subtitle"):
                    print(f"## {d.get('subtitle')}\n")
                print(d.get("content") or "")
            return d
    print(f"Post not found: {post_id}")
    return None


# ---------------------------------------------------------------------
# Search utilities
# ---------------------------------------------------------------------

def find_posts(pattern: str, field: str = "all", limit: int = 50) -> List[Dict]:
    """
    Search posts by case-insensitive pattern (substring or regex).

    Args:
        pattern (str):
            Substring or regex to search.
        field (str):
            'title', 'subtitle', 'content', or 'all' (default).
        limit (int):
            Maximum number of matches to return.

    Returns:
        List[Dict] with keys: id, title, subtitle, date, snippet.
    """
    data = _load_axio_data()
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []

    def match_text(text: Optional[str]) -> bool:
        return bool(text and regex.search(text))

    for d in data:
        title = d.get("title") or ""
        subtitle = d.get("subtitle") or ""
        content = d.get("content") or ""

        if field == "title":
            found = match_text(title)
        elif field == "subtitle":
            found = match_text(subtitle)
        elif field == "content":
            found = match_text(content)
        else:  # all
            found = match_text(title) or match_text(subtitle) or match_text(content)

        if found:
            snippet = ""
            if content:
                m = regex.search(content)
                if m:
                    start = max(m.start() - 40, 0)
                    end = min(m.end() + 40, len(content))
                    snippet = content[start:end].replace("\n", " ")
            matches.append(
                {
                    "id": d.get("id"),
                    "date": d.get("date"),
                    "title": title,
                    "subtitle": subtitle,
                    "snippet": snippet,
                }
            )
            if len(matches) >= limit:
                break

    print(f"Found {len(matches)} result(s) matching /{pattern}/ in field='{field}':\n")
    for m in matches:
        date = (m["date"] or "")[:19]
        print(f"- {date}  {m['id']}")
        print(f"  {m['title']}")
        if m["snippet"]:
            print(f"  ...{m['snippet']}...")
        print()

    return matches


# ---------------------------------------------------------------------
# Sequence & index helpers
# ---------------------------------------------------------------------

def _id_to_slug(post_id: str) -> str:
    """
    Convert an Axio post ID like:
        '162560090.the-physics-of-agency-part-5-the'
    into a slug:
        'the-physics-of-agency-part-5-the'
    """
    if "." in post_id:
        return post_id.split(".", 1)[1]
    return post_id


def generate_sequence(name: str, ids: List[str], as_markdown: bool = True) -> str:
    """
    Generate a markdown (or plain text) block for an Axio sequence.

    Args:
        name (str): sequence name (human-readable).
        ids (list[str]): list of post IDs in desired order.
        as_markdown (bool):
            If True, output markdown with links: https://axio.fyi/p/<slug>.

    Returns:
        str – sequence listing.
    """
    data = _load_axio_data()
    by_id = {d.get("id"): d for d in data}

    lines = []
    if as_markdown:
        lines.append(f"# {name}\n")

    for pid in ids:
        post = by_id.get(pid)
        if not post:
            continue
        title = post.get("title") or pid
        slug = _id_to_slug(pid)
        url = f"https://axio.fyi/p/{slug}"
        date = (post.get("date") or "")[:10]

        if as_markdown:
            lines.append(f"- **{title}** ({date})  \n  {url}")
        else:
            lines.append(f"- {title} ({date}) :: {url}")

    result = "\n".join(lines)
    print(result)
    return result


def update_axio_index(as_markdown: bool = True) -> str:
    """
    Generate a simple Axio Index of all posts, sorted by date (ascending).

    Args:
        as_markdown (bool):
            If True, returns markdown; else plain text.

    Returns:
        str – index listing.
    """
    data = _load_axio_data()
    sorted_data = sorted(data, key=lambda d: d.get("date", ""))

    lines = []
    if as_markdown:
        lines.append("# Axio Index (auto-generated)\n")

    for d in sorted_data:
        pid = d.get("id")
        title = d.get("title") or pid
        date = (d.get("date") or "")[:10]
        slug = _id_to_slug(pid)
        url = f"https://axio.fyi/p/{slug}"

        if as_markdown:
            lines.append(f"- **{title}** ({date})  \n  {url}")
        else:
            lines.append(f"- {title} ({date}) :: {url}")

    result = "\n".join(lines)
    # Preview first chunk for sanity
    print(result[:2000] + ("\n...\n" if len(result) > 2000 else ""))
    return result


# ---------------------------------------------------------------------
# Definition & concept helpers
# ---------------------------------------------------------------------

def extract_definitions() -> List[Dict]:
    """
    Scan the corpus for lines starting with 'Definition:' (case-insensitive).

    Returns:
        List[Dict]: each with 'id', 'title', 'definition'.
    """
    data = _load_axio_data()
    results = []
    pattern = re.compile(r"^\s*definition\s*:", re.IGNORECASE)

    for d in data:
        content = d.get("content") or ""
        lines = content.splitlines()
        for line in lines:
            if pattern.match(line):
                results.append(
                    {
                        "id": d.get("id"),
                        "title": d.get("title"),
                        "definition": line.strip(),
                    }
                )

    print(f"Found {len(results)} definition line(s).")
    return results


def map_concepts(terms: List[str], top_k: int = 20) -> Dict[str, List[Dict]]:
    """
    Build a simple concept-to-post mapping.

    Args:
        terms (list[str]):
            Concept strings to track (case-insensitive).
        top_k (int):
            Maximum posts per term.

    Returns:
        Dict: { term: [ { 'id', 'title', 'count' }, ... ] }
    """
    data = _load_axio_data()
    results: Dict[str, List[Dict]] = {}
    lowered_terms = [t.lower() for t in terms]

    for term in lowered_terms:
        counts = []
        term_regex = re.compile(re.escape(term), re.IGNORECASE)
        for d in data:
            content = d.get("content") or ""
            count = len(term_regex.findall(content))
            if count > 0:
                counts.append(
                    {"id": d.get("id"), "title": d.get("title"), "count": count}
                )
        counts.sort(key=lambda x: x["count"], reverse=True)
        results[term] = counts[:top_k]

        print(f"Concept '{term}' appears in {len(counts)} post(s) (top {top_k}):")
        for p in counts[:5]:
            print(f"  - {p['id']} ({p['count']} hits): {p['title']}")
        print()

    return results


# ---------------------------------------------------------------------
# Consolidated help()
# ---------------------------------------------------------------------

def help():
    """
Axio utilities – available functions:

CORE:
- help()
    Show this help message.

BROWSING & NAVIGATION:
- list_posts(limit=20, contains=None, page=None, page_size=20)
    List basic metadata for posts (date, id, title).
    Args:
        limit (int or None): max number of posts (ignored if page is set).
        contains (str or None): case-insensitive substring filter on title or subtitle.
        page (int or None): 1-based page index for pagination.
        page_size (int): posts per page (default 20).

- next()
    Move forward one page using the current pagination state.

- prev()
    Move back one page using the current pagination state.

- home()
    Jump to the first page (newest posts) using current page_size.

- end()
    Jump to the last page (oldest posts) using current page_size.

- status()
    Show current pagination status: page, page_size, total_pages, total_posts.

- goto(page)
    Jump directly to a page number using current page_size.

- view(page=None)
    TUI-like browser for the corpus. Shows a framed page with navigation hints.
    If page is None, uses the current page from the pagination state.

POST ACCESS:
- get_post(post_id, show_content=False)
    Retrieve a single post by its ID.
    Args:
        post_id (str): e.g. "162560090.the-physics-of-agency-part-5-the"
        show_content (bool): if True, prints the full content.
    Returns:
        dict with keys: id, title, subtitle, date, content.

SEARCH & ANALYSIS:
- find_posts(pattern, field='all', limit=50)
    Search posts by case-insensitive pattern.
    Args:
        pattern (str): substring or regex to search for.
        field (str): 'title', 'subtitle', 'content', or 'all' (default).
        limit (int): maximum number of matches to return.

- extract_definitions()
    Scan all posts for lines starting with 'Definition:' (case-insensitive).
    Returns:
        list of dicts: { 'id', 'title', 'definition' }.

- map_concepts(terms, top_k=20)
    Build a simple concept-to-post mapping for given terms.
    Args:
        terms (list[str]): list of concept strings to track (case-insensitive).
        top_k (int): max posts per term.
    Returns:
        dict: { term: [ { 'id', 'title', 'count' }, ... ] }.

SEQUENCES & INDEX:
- generate_sequence(name, ids, as_markdown=True)
    Generate a markdown (or plain text) block for an Axio sequence.
    Args:
        name (str): human-readable sequence name.
        ids (list[str]): list of post IDs in desired order.
        as_markdown (bool): if True, returns markdown with links.
    Returns:
        str – sequence listing suitable for Axio.

- update_axio_index(as_markdown=True)
    Generate a simple Axio Index of all posts, sorted by date.
    Args:
        as_markdown (bool): if True, returns markdown; otherwise plain text.
    Returns:
        str – index listing (markdown or plain text).
"""
    print(help.__doc__)


print(f"Axio bootstrap loaded. Total posts: {TOTAL_POSTS}. Use view(), list_posts(), help(), etc.")
