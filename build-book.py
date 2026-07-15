#!/usr/bin/env python3
"""
Build the Axio book from book/ into docs/book/

Reads book/book.yaml for the volume order, discovers chapters from filename
prefixes (01-, 02-, ...) within each volume directory, and renders every
published chapter (status: draft | review | final) to styled HTML with
book/volume/chapter navigation.

Cross-links between chapters are written as relative .md links in the source
and rewritten to .html here. Links to the rest of the site are written
root-relative (/posts/..., /papers/...) and rewritten to relative URLs.
The build FAILS on links whose target file does not exist, and warns on
links to chapters that exist but are not yet published.

Usage:
    python3 build-book.py
"""

import re
import subprocess
import sys
from html import escape
from pathlib import Path

import yaml

BOOK_SRC = Path('book')
BOOK_DEST = Path('docs/book')
DOCS = Path('docs')
BASE_URL = "https://axionic.org"

PUBLISHED_STATUSES = {'draft', 'review', 'final'}
VALID_STATUSES = {'outline'} | PUBLISHED_STATUSES

link_errors = []
link_warnings = []

# ============================================
# SOURCE PARSING
# ============================================

def parse_frontmatter(path):
    """Return (metadata dict, markdown body) for a chapter file."""
    text = path.read_text(encoding='utf-8')
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        print(f"   ✗ Bad frontmatter in {path}: {e}")
        sys.exit(1)
    return meta, text[match.end():]

def convert_markdown_to_html(markdown_content, src_path):
    """Convert markdown to an HTML fragment using pandoc (with math support)."""
    try:
        process = subprocess.run(
            ['pandoc', '--from', 'markdown', '--to', 'html', '--mathjax',
             '--wrap=none'],
            input=markdown_content,
            capture_output=True,
            text=True,
            check=True
        )
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ✗ pandoc failed on {src_path}: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("   ✗ pandoc not found — install pandoc to build the book")
        sys.exit(1)

def load_book():
    """Load the manifest and discover chapters. Returns (manifest, volumes).

    Each volume dict gains:
      number      display number (1-based, front matter excluded)
      intro       {'meta', 'body'} from volume.md, or None
      chapters    [{'src', 'slug', 'meta', 'body', 'published'}] in filename order
      published   True if the volume page should be generated
    """
    manifest_path = BOOK_SRC / 'book.yaml'
    with open(manifest_path, encoding='utf-8') as f:
        manifest = yaml.safe_load(f)

    volumes = []
    number = 0
    for vol in manifest['volumes']:
        vol = dict(vol)
        vol_dir = BOOK_SRC / vol['slug']
        if not vol_dir.is_dir():
            print(f"   ✗ Volume directory missing: {vol_dir}")
            sys.exit(1)

        if not vol.get('front_matter'):
            number += 1
            vol['number'] = number
        else:
            vol['number'] = None

        intro_path = vol_dir / 'volume.md'
        if intro_path.exists():
            meta, body = parse_frontmatter(intro_path)
            vol['intro'] = {'meta': meta, 'body': body}
        else:
            vol['intro'] = None

        chapters = []
        for src in sorted(vol_dir.glob('[0-9]*.md')):
            meta, body = parse_frontmatter(src)
            status = meta.get('status', 'outline')
            if status not in VALID_STATUSES:
                print(f"   ✗ {src}: invalid status '{status}' "
                      f"(expected one of {sorted(VALID_STATUSES)})")
                sys.exit(1)
            chapters.append({
                'src': src,
                'slug': src.stem,
                'meta': meta,
                'body': body,
                'status': status,
                'published': status in PUBLISHED_STATUSES,
            })

        # Optional manifest-defined parts control TOC grouping without
        # changing chapter URLs or filename-based reading order.
        parts = vol.get('parts', [])
        if parts:
            chapter_slugs = [c['slug'] for c in chapters]
            part_slugs = [slug for part in parts
                          for slug in part.get('chapters', [])]
            duplicates = sorted({slug for slug in part_slugs
                                 if part_slugs.count(slug) > 1})
            missing = sorted(set(chapter_slugs) - set(part_slugs))
            unknown = sorted(set(part_slugs) - set(chapter_slugs))
            if duplicates or missing or unknown:
                details = []
                if duplicates:
                    details.append(f'duplicate chapters: {duplicates}')
                if missing:
                    details.append(f'unassigned chapters: {missing}')
                if unknown:
                    details.append(f'unknown chapters: {unknown}')
                print(f"   ✗ {vol['slug']}: invalid parts ({'; '.join(details)})")
                sys.exit(1)
        vol['chapters'] = chapters

        intro_status = (vol['intro']['meta'].get('status', 'outline')
                        if vol['intro'] else 'outline')
        vol['intro_published'] = intro_status in PUBLISHED_STATUSES
        vol['published'] = vol['intro_published'] or any(
            c['published'] for c in chapters)
        volumes.append(vol)

    return manifest, volumes

# ============================================
# LINK RESOLUTION
# ============================================

def build_publish_index(volumes):
    """Map source-relative paths (from book/) to publication status."""
    index = {}
    for vol in volumes:
        if vol['intro'] is not None:
            index[f"{vol['slug']}/volume.md"] = vol['published']
        for ch in vol['chapters']:
            index[f"{vol['slug']}/{ch['slug']}.md"] = ch['published']
    return index

def rewrite_links(html, src_path, prefix, publish_index):
    """Rewrite and validate hrefs in a rendered fragment.

    src_path  source file the fragment came from (for error messages and
              resolving relative .md links)
    prefix    relative path from the output page's directory to docs/ root
    """
    src_dir = src_path.parent

    def fix(match):
        href, inner = match.group(1), match.group(2)
        if re.match(r'^(https?:|mailto:|#)', href):
            return match.group(0)

        target, frag = (href.split('#', 1) + [''])[:2]
        frag = f'#{frag}' if frag else ''

        # Cross-links between book source files
        if target.endswith('.md'):
            resolved = (src_dir / target).resolve()
            try:
                rel = resolved.relative_to(BOOK_SRC.resolve())
            except ValueError:
                link_errors.append(f"{src_path}: link outside book/: {href}")
                return match.group(0)
            if str(rel) not in publish_index:
                link_errors.append(f"{src_path}: broken chapter link: {href}")
                return match.group(0)
            if not publish_index[str(rel)]:
                # Target chapter not yet published: render as plain text so
                # the live site has no dead links. It becomes a link
                # automatically on the rebuild that publishes the target.
                link_warnings.append(
                    f"{src_path}: unlinked (unpublished chapter): {href}")
                return inner
            out = str(rel).replace('volume.md', 'index.html')
            if out.endswith('.md'):
                out = out[:-3] + '.html'
            return f'<a href="{prefix}book/{out}{frag}">{inner}</a>'

        # Root-relative links into the rest of the site
        if target.startswith('/'):
            check = DOCS / (target.lstrip('/') or 'index.html')
            if check.is_dir():
                check = check / 'index.html'
            if not check.exists():
                link_errors.append(f"{src_path}: broken site link: {href}")
                return match.group(0)
            return f'<a href="{prefix}{target.lstrip("/")}{frag}">{inner}</a>'

        return match.group(0)

    return re.sub(r'<a\s[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', fix, html,
                  flags=re.DOTALL)

# ============================================
# HTML GENERATION
# ============================================

def generate_navigation(prefix):
    """Site navigation with the Book tab active (mirrors build-site.py)."""
    nav_items = [
        ('./', 'Home'),
        ('about.html', 'About'),
        ('research.html', 'Research'),
        ('team.html', 'Team'),
        ('publications.html', 'Publications'),
        ('book/', 'Book'),
    ]
    links_html = ''
    for href, label in nav_items:
        active = ' class="active"' if href == 'book/' else ''
        links_html += f'<li><a href="{prefix}{href}"{active}>{label}</a></li>\n'
    return f'''<nav class="site-nav">
        <a href="{prefix}" class="nav-brand">
            <img src="{prefix}images/axionic-logo.png" alt="Axionic">
            <span>Axionic Agency Lab</span>
        </a>
        <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">☰</button>
        <ul class="nav-links">
            {links_html}
        </ul>
    </nav>'''

MATHJAX = '''
    <!-- MathJax for LaTeX rendering -->
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
        MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
        };
    </script>
'''

def wrap_page(title, content, prefix, breadcrumbs=None):
    crumbs_html = ''
    if breadcrumbs:
        parts = []
        for label, href in breadcrumbs:
            if href:
                parts.append(f'<a href="{href}">{escape(label)}</a>')
            else:
                parts.append(f'<span>{escape(label)}</span>')
        crumbs_html = ('<div class="book-breadcrumbs">'
                       + ' <span class="crumb-sep">›</span> '.join(parts)
                       + '</div>')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} - Axio</title>
    <link rel="icon" type="image/png" href="{prefix}images/axionic-logo.png">
{MATHJAX}
    <!-- Site Styles -->
    <link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
    {generate_navigation(prefix)}
    <article class="paper-content book-page">
    {crumbs_html}
{content}
    </article>
    <footer>
        <p>&copy; Axionic Agency Lab</p>
    </footer>
</body>
</html>
'''

def status_badge(status):
    if status == 'final':
        return ''
    return f'<span class="book-status book-status-{status}">{status}</span>'

def status_banner(status):
    if status == 'final':
        return ''
    return (f'<div class="book-banner book-banner-{status}">'
            f'This chapter is a <strong>{status}</strong> — '
            f'it is readable but still changing.</div>')

def chapter_title_block(meta):
    html = f"<h1>{escape(meta.get('title', 'Untitled'))}</h1>\n"
    if meta.get('subtitle'):
        html += f"<p class='paper-subtitle'>{escape(meta['subtitle'])}</p>\n"
    return html

def volume_display_title(vol):
    if vol['number'] is not None:
        return f"Volume {vol['number']} — {vol['title']}"
    return vol['title']

def build_chapter_page(vol, chapter, prev_ch, next_ch, publish_index):
    prefix = '../../'
    dest = BOOK_DEST / vol['slug'] / f"{chapter['slug']}.html"

    fragment = convert_markdown_to_html(chapter['body'], chapter['src'])
    fragment = rewrite_links(fragment, chapter['src'], prefix, publish_index)

    nav_links = []
    if prev_ch:
        nav_links.append(f'<a class="book-prev" href="{prev_ch["slug"]}.html">'
                         f'← {escape(prev_ch["meta"].get("title", ""))}</a>')
    up_href = '../index.html' if vol.get('front_matter') else 'index.html'
    nav_links.append(f'<a class="book-up" href="{up_href}">Contents</a>')
    if next_ch:
        nav_links.append(f'<a class="book-next" href="{next_ch["slug"]}.html">'
                         f'{escape(next_ch["meta"].get("title", ""))} →</a>')
    chapter_nav = f'<nav class="book-chapter-nav">{"".join(nav_links)}</nav>'

    breadcrumbs = [('Axio', '../index.html')]
    if vol['number'] is not None:
        breadcrumbs.append((f"Volume {vol['number']}", 'index.html'))
    breadcrumbs.append((chapter['meta'].get('title', chapter['slug']), None))

    content = (chapter_title_block(chapter['meta'])
               + status_banner(chapter['status'])
               + fragment
               + chapter_nav)
    dest.write_text(
        wrap_page(chapter['meta'].get('title', chapter['slug']),
                  content, prefix, breadcrumbs),
        encoding='utf-8')
    return dest

def build_volume_page(vol, publish_index):
    prefix = '../../'
    dest_dir = BOOK_DEST / vol['slug']
    dest_dir.mkdir(parents=True, exist_ok=True)

    content = f"<h1>{escape(volume_display_title(vol))}</h1>\n"

    if vol['intro'] is not None and vol['intro_published']:
        fragment = convert_markdown_to_html(
            vol['intro']['body'], BOOK_SRC / vol['slug'] / 'volume.md')
        fragment = rewrite_links(
            fragment, BOOK_SRC / vol['slug'] / 'volume.md',
            prefix, publish_index)
        content += fragment

    published = [c for c in vol['chapters'] if c['published']]
    unpublished = [c for c in vol['chapters'] if not c['published']]

    if published:
        content += '<h2>Chapters</h2>\n'
        published_by_slug = {ch['slug']: ch for ch in published}
        if vol.get('parts'):
            # Parts are display groupings only; chapter numbering runs
            # continuously across them via each list's start offset.
            chapter_number = 1
            for part in vol['parts']:
                part_chapters = [published_by_slug[slug]
                                 for slug in part.get('chapters', [])
                                 if slug in published_by_slug]
                if not part_chapters:
                    continue
                content += (f'<h3 class="book-part-title">'
                            f'{escape(part["title"])}</h3>\n'
                            f'<ol class="book-toc" start="{chapter_number}">\n')
                for ch in part_chapters:
                    title = escape(ch['meta'].get('title', ch['slug']))
                    content += (f'<li><a href="{ch["slug"]}.html">{title}</a> '
                                f'{status_badge(ch["status"])}</li>\n')
                content += '</ol>\n'
                chapter_number += len(part_chapters)
        else:
            content += '<ol class="book-toc">\n'
            for ch in published:
                title = escape(ch['meta'].get('title', ch['slug']))
                content += (f'<li><a href="{ch["slug"]}.html">{title}</a> '
                            f'{status_badge(ch["status"])}</li>\n')
            content += '</ol>\n'
    if unpublished:
        content += ('<p class="book-muted">'
                    f'{len(unpublished)} more chapter(s) in preparation.</p>\n')
    if not published and not unpublished:
        content += '<p class="book-muted">This volume is in preparation.</p>\n'

    breadcrumbs = [('Axio', '../index.html'), (volume_display_title(vol), None)]
    dest = dest_dir / 'index.html'
    dest.write_text(
        wrap_page(volume_display_title(vol), content, prefix, breadcrumbs),
        encoding='utf-8')
    return dest

def build_book_index(manifest, volumes, publish_index):
    prefix = '../'
    content = f"<h1>{escape(manifest['title'])}</h1>\n"
    if manifest.get('subtitle'):
        content += f"<p class='paper-subtitle'>{escape(manifest['subtitle'])}</p>\n"

    # Front-matter chapters (e.g. the introduction) listed directly
    for vol in volumes:
        if not vol.get('front_matter'):
            continue
        for ch in vol['chapters']:
            if ch['published']:
                title = escape(ch['meta'].get('title', ch['slug']))
                content += (f'<p class="book-front-link">'
                            f'<a href="{vol["slug"]}/{ch["slug"]}.html">{title}</a> '
                            f'{status_badge(ch["status"])}</p>\n')

    content += '<h2>Volumes</h2>\n<ol class="book-volumes">\n'
    for vol in volumes:
        if vol.get('front_matter'):
            continue
        title = escape(vol['title'])
        if vol['published']:
            n_pub = sum(1 for c in vol['chapters'] if c['published'])
            note = (f'{n_pub} chapter(s)' if n_pub
                    else 'introduction only')
            content += (f'<li><a href="{vol["slug"]}/index.html">{title}</a> '
                        f'<span class="book-muted">— {note}</span></li>\n')
        else:
            content += (f'<li><span class="book-unpublished">{title}</span> '
                        f'<span class="book-muted">— in preparation</span></li>\n')
    content += '</ol>\n'

    dest = BOOK_DEST / 'index.html'
    dest.write_text(wrap_page(manifest['title'], content, prefix), encoding='utf-8')
    return dest

# ============================================
# SITEMAP
# ============================================

def update_sitemap(page_urls):
    """Insert book pages into docs/sitemap.xml (replacing old book entries)."""
    sitemap_path = DOCS / 'sitemap.xml'
    if not sitemap_path.exists():
        return False
    xml = sitemap_path.read_text(encoding='utf-8')

    def drop_book_entry(match):
        block = match.group(0)
        return '' if f'<loc>{BASE_URL}/book/' in block else block

    xml = re.sub(r'  <url>\n.*?  </url>\n', drop_book_entry, xml,
                 flags=re.DOTALL)
    entries = ''
    for url in page_urls:
        entries += ('  <url>\n'
                    f'    <loc>{escape(url)}</loc>\n'
                    '    <priority>0.8</priority>\n'
                    '  </url>\n')
    xml = xml.replace('</urlset>', entries + '</urlset>')
    sitemap_path.write_text(xml, encoding='utf-8')
    return True

# ============================================
# MAIN
# ============================================

def main():
    print("=== Building Axio book ===")
    try:
        from pandoc_version import check as _check_pandoc
        _check_pandoc()  # warns (does not halt) on a pandoc-version mismatch
    except ImportError:
        pass
    if not (BOOK_SRC / 'book.yaml').exists():
        print(f"   ✗ {BOOK_SRC}/book.yaml not found (run from the repo root)")
        sys.exit(1)

    manifest, volumes = load_book()
    publish_index = build_publish_index(volumes)

    # Rebuild output from scratch — docs/book is fully owned by this script
    import shutil
    if BOOK_DEST.exists():
        shutil.rmtree(BOOK_DEST)
    BOOK_DEST.mkdir(parents=True)

    pages = []
    for vol in volumes:
        if not vol['published']:
            continue
        published = [c for c in vol['chapters'] if c['published']]
        if not vol.get('front_matter'):
            pages.append(build_volume_page(vol, publish_index))
        else:
            (BOOK_DEST / vol['slug']).mkdir(parents=True, exist_ok=True)
        for i, ch in enumerate(published):
            prev_ch = published[i - 1] if i > 0 else None
            next_ch = published[i + 1] if i + 1 < len(published) else None
            dest = build_chapter_page(vol, ch, prev_ch, next_ch, publish_index)
            pages.append(dest)
            print(f"   ✓ {ch['src']} → {dest.relative_to(DOCS)} [{ch['status']}]")

    pages.insert(0, build_book_index(manifest, volumes, publish_index))
    print(f"   ✓ Generated book index with "
          f"{sum(1 for v in volumes if v['published'] and not v.get('front_matter'))} "
          f"published volume(s)")

    urls = [f"{BASE_URL}/{p.relative_to(DOCS)}" for p in pages]
    urls = [u.replace('/index.html', '/') for u in urls]
    if update_sitemap(urls):
        print(f"   ✓ Updated sitemap.xml with {len(urls)} book page(s)")

    for w in link_warnings:
        print(f"   ⚠ {w}")
    if link_errors:
        for e in link_errors:
            print(f"   ✗ {e}")
        print(f"=== Book build FAILED: {len(link_errors)} broken link(s) ===")
        sys.exit(1)

    print("=== Book build complete ===")

if __name__ == '__main__':
    main()
