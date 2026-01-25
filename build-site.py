#!/usr/bin/env python3
"""
Build the docs/ directory from posts/ with fixed links and custom CSS

This script:
1. Downloads and localizes images from posts
2. Copies posts/ to docs/posts/
3. Fixes internal Substack links to point to local files
4. Injects custom CSS for better readability
5. Generates index.html
6. Creates search index for full-text search
7. Converts markdown papers with LaTeX to HTML

Usage:
    python3 build-site.py
"""

import os
import re
import csv
import json
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import subprocess

def load_post_mapping():
    """Load mapping of post slugs to post IDs from posts.csv"""
    slug_to_id = {}

    with open('posts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_id = row['post_id']
            # Extract slug from post_id (format: "12345.slug-text")
            if '.' in post_id:
                slug = post_id.split('.', 1)[1]
                slug_to_id[slug] = post_id

    return slug_to_id

def extract_image_id(url):
    """Extract the unique image ID from a Substack URL"""
    match = re.search(r'/images/([a-f0-9\-]+_\d+x\d+\.\w+)', url)
    if match:
        return match.group(1)
    match = re.search(r'([a-f0-9\-]{36}_\d+x\d+\.\w+)', url)
    if match:
        return match.group(1)
    return None

def get_direct_image_url(url):
    """Extract the direct S3 URL from encoded Substack CDN URLs"""
    if 'substack-post-media.s3.amazonaws.com' in url and 'substackcdn.com' not in url:
        return url
    if 'substackcdn.com/image/fetch/' in url:
        match = re.search(r'https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com[^"\s]+', url)
        if match:
            return urllib.parse.unquote(match.group(0))
    return None

def download_image(url, dest_path):
    """Download an image from URL to destination path"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            with open(dest_path, 'wb') as f:
                f.write(content)
            return True
    except Exception as e:
        return False

def localize_images_in_content(content, images_dir, image_map):
    """Replace Substack image URLs with local references in HTML content"""
    # First, collect any new images we haven't seen before
    s3_urls = re.findall(
        r'https://substack-post-media\.s3\.amazonaws\.com/public/images/[a-f0-9\-]+_\d+x\d+\.\w+',
        content
    )
    cdn_urls = re.findall(
        r'https://substackcdn\.com/image/fetch/[^"\s]+https%3A%2F%2Fsubstack-post-media[^"\s]+',
        content
    )

    new_downloads = 0
    for url in s3_urls:
        if url not in image_map:
            image_id = extract_image_id(url)
            if image_id:
                dest_path = images_dir / image_id
                if not dest_path.exists():
                    if download_image(url, dest_path):
                        new_downloads += 1
                image_map[url] = image_id

    for cdn_url in cdn_urls:
        direct_url = get_direct_image_url(cdn_url)
        if direct_url and direct_url not in image_map:
            image_id = extract_image_id(direct_url)
            if image_id:
                dest_path = images_dir / image_id
                if not dest_path.exists():
                    if download_image(direct_url, dest_path):
                        new_downloads += 1
                image_map[direct_url] = image_id

    # Now replace all URLs with local references
    for original_url, local_filename in image_map.items():
        content = content.replace(original_url, f'../images/{local_filename}')
        encoded_url = urllib.parse.quote(original_url, safe='')
        content = content.replace(encoded_url, f'../images/{local_filename}')

    # Clean up any remaining CDN URLs
    def replace_cdn_url(match):
        full_url = match.group(0)
        local_match = re.search(r'\.\./images/([a-f0-9\-]+_\d+x\d+\.\w+)', full_url)
        if local_match:
            return f'../images/{local_match.group(1)}'
        image_match = re.search(r'([a-f0-9\-]{36}_\d+x\d+\.\w+)', full_url)
        if image_match:
            return f'../images/{image_match.group(1)}'
        return full_url

    content = re.sub(
        r'https://substackcdn\.com/image/fetch/[^"\s]+',
        replace_cdn_url,
        content
    )

    return content, new_downloads

# CSS is now external in docs/style.css

class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML"""
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)

def extract_text_from_html(html_content):
    """Extract plain text from HTML content"""
    extractor = HTMLTextExtractor()
    extractor.feed(html_content)
    text = extractor.get_text()
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_post_file(src_path, dest_path, slug_to_id, post_metadata, localized_content=None):
    """Copy and process a single post HTML file"""
    if localized_content is None:
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = localized_content

    changes = 0

    # Fix internal Substack and custom domain links
    def replace_link(match):
        nonlocal changes
        slug = match.group(1).rstrip('?')  # Remove trailing ? if present

        if slug in slug_to_id:
            post_id = slug_to_id[slug]
            changes += 1
            return f'href="{post_id}.html"'
        else:
            return match.group(0)

    # Fix axio.substack.com links
    content = re.sub(
        r'href="https://axio\.substack\.com/p/([^"]+)"',
        replace_link,
        content
    )

    # Fix axio.fyi links
    content = re.sub(
        r'href="https://axio\.fyi/p/([^"]+)"',
        replace_link,
        content
    )

    # Also fix any links that already point to posts/ (from previous processing)
    content = re.sub(
        r'href="posts/([^"]+\.html)"',
        r'href="\1"',
        content
    )

    # Build title section
    title_html = ""
    if post_metadata:
        title = post_metadata.get('title', '')
        subtitle = post_metadata.get('subtitle', '')
        date = post_metadata.get('date', '')

        if title:
            title_html = f'<h1 class="post-title">{escape(title)}</h1>\n'
        if subtitle:
            title_html += f'<p class="post-subtitle">{escape(subtitle)}</p>\n'
        if date:
            # Format the date nicely
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%B %d, %Y')
            except:
                formatted_date = date[:10]
            title_html += f'<p class="post-date">{formatted_date}</p>\n'
        if title_html:
            title_html = f'<header class="post-header">\n{title_html}</header>\n\n'

    # Wrap content in proper HTML structure with CSS
    wrapped_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(post_metadata.get('title', 'Axio - Post')) if post_metadata else 'Axio - Post'}</title>
    <link rel="icon" type="image/png" href="../images/axionic-logo.png">

    <!-- KaTeX CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">

    <!-- Site Styles -->
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <div class="header-bar">
        <a href="../" class="logo-link">
            <img src="../images/axionic-logo.png" alt="Axionic" class="site-logo">
        </a>
        <div class="back-link"><a href="../publications.html">← Back to Publications</a></div>
    </div>
    <article>
{title_html}{content}
    </article>

    <!-- KaTeX JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8" crossorigin="anonymous"></script>
    <script>
        // Find all LaTeX blocks and render them
        document.querySelectorAll('.latex-rendered').forEach(el => {{
            const dataAttrs = el.getAttribute('data-attrs');
            if (dataAttrs) {{
                try {{
                    const attrs = JSON.parse(dataAttrs);
                    const expr = attrs.persistentExpression;
                    if (expr) {{
                        katex.render(expr, el, {{
                            displayMode: true,
                            throwOnError: false,
                            trust: true
                        }});
                    }}
                }} catch (e) {{
                    console.error('Error rendering LaTeX:', e);
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # Write processed content
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(wrapped_content)

    return changes, content  # Return both changes count and raw content for indexing

def convert_markdown_to_html(markdown_content):
    """Convert markdown with LaTeX to HTML using pandoc"""
    try:
        # Use pandoc to convert markdown to HTML with math support
        process = subprocess.run(
            ['pandoc',
             '--from', 'markdown',
             '--to', 'html',
             '--mathjax',
             '--standalone'],
            input=markdown_content,
            capture_output=True,
            text=True,
            check=True
        )
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ⚠ Error converting markdown: {e}")
        # Fallback: basic conversion
        return f"<pre>{escape(markdown_content)}</pre>"
    except FileNotFoundError:
        print(f"   ⚠ pandoc not found, using basic HTML wrapper")
        # Fallback: wrap in basic HTML
        html = markdown_content.replace('\n\n', '</p>\n<p>')
        return f"<div>{html}</div>"

def process_paper_file(src_path, dest_path):
    """Convert a markdown paper to HTML with proper styling (dark theme)"""
    with open(src_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Extract title from first # heading if present
    title_match = re.search(r'^#\s+(.+?)$', markdown_content, re.MULTILINE)
    title = title_match.group(1) if title_match else src_path.stem

    # Convert markdown to HTML
    content_html = convert_markdown_to_html(markdown_content)

    # If pandoc was used, extract just the body content
    body_match = re.search(r'<body>(.*)</body>', content_html, re.DOTALL)
    if body_match:
        content_html = body_match.group(1)

    # Fix internal markdown links to point to .html files
    content_html = re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', content_html)

    # Generate navigation
    nav_html = generate_navigation('publications.html', '../')

    # Wrap in styled HTML with dark theme
    wrapped_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} - Axionic Agency Lab</title>
    <link rel="icon" type="image/png" href="../images/axionic-logo.png">

    <!-- MathJax for LaTeX rendering -->
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }}
        }};
    </script>

    <!-- Site Styles (Dark Theme) -->
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    {nav_html}
    <article class="paper-content">
{content_html}
    </article>
    <footer>
        <p>&copy; Axionic Agency Lab</p>
    </footer>
</body>
</html>
"""

    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(wrapped_html)

def generate_papers_index(papers_metadata):
    """Generate an index.html for the papers directory (dark theme), grouped by series"""

    # Define series order and names
    series_config = [
        ('I', 'Series I: Sovereign Kernel Theory'),
        ('II', 'Series II: Semantic Transport'),
        ('III', 'Series III: Structural Alignment'),
        ('IV', 'Series IV: Binding Theorems'),
        ('V', 'Series V: Agency Dynamics'),
        ('VI', 'Series VI: Governance and Coordination'),
        ('VII', 'Series VII: Constitutional Survivability'),
        ('VIII', 'Series VIII: RSA-PoC'),
    ]

    # Group papers by series
    series_papers = {s[0]: [] for s in series_config}
    standalone_papers = []

    for paper in papers_metadata:
        filename = paper.get('filename', '')
        matched = False
        for series_id, _ in series_config:
            if filename.startswith(f'Axionic-Agency-{series_id}.'):
                series_papers[series_id].append(paper)
                matched = True
                break
        if not matched:
            standalone_papers.append(paper)

    # Build HTML - start with standalone/foundational papers
    papers_list_html = ""

    # Add standalone papers first
    if standalone_papers:
        papers_list_html += """
        <section id="foundational" class="paper-series">
            <h2>Foundational Papers</h2>
        """

        for paper in standalone_papers:
            title = paper['title']
            filename = paper['filename']
            abstract = paper.get('abstract', '')
            abstract_html = f"<p class='paper-abstract'>{escape(abstract)}</p>" if abstract else ""

            papers_list_html += f"""
            <div class="paper-entry">
                <h3><a href="{filename}">{escape(title)}</a></h3>
                {abstract_html}
            </div>
            """

        papers_list_html += "</section>"

    # Then add each series
    for series_id, series_name in series_config:
        papers = series_papers[series_id]
        if not papers:
            continue

        papers_list_html += f"""
        <section id="series-{series_id}" class="paper-series">
            <h2>{series_name}</h2>
        """

        for paper in papers:
            title = paper['title']
            filename = paper['filename']
            abstract = paper.get('abstract', '')
            abstract_html = f"<p class='paper-abstract'>{escape(abstract)}</p>" if abstract else ""

            papers_list_html += f"""
            <div class="paper-entry">
                <h3><a href="{filename}">{escape(title)}</a></h3>
                {abstract_html}
            </div>
            """

        papers_list_html += "</section>"

    nav_html = generate_navigation('publications.html', '../')

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Papers - Axionic Agency Lab</title>
    <link rel="icon" type="image/png" href="../images/axionic-logo.png">
    <link rel="stylesheet" href="../style.css">
    <style>
        .papers-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 1rem;
        }}
        .papers-container h1 {{
            margin-bottom: 2rem;
        }}
        .paper-entry {{
            margin: 1.5rem 0;
            padding: 1.5rem 0;
            border-bottom: 1px solid #1e293b;
        }}
        .paper-entry:last-child {{
            border-bottom: none;
        }}
        .paper-entry h2 {{
            margin: 0 0 0.5em 0;
            font-size: 1.2em;
            font-family: 'Source Serif 4', Georgia, serif;
        }}
        .paper-series {{
            margin: 3rem 0;
            padding-top: 1rem;
        }}
        .paper-series h2 {{
            font-size: 1.4rem;
            color: #94a3b8;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}
        .paper-entry h3 {{
            margin: 0 0 0.5em 0;
            font-size: 1.1em;
            font-family: 'Source Serif 4', Georgia, serif;
        }}
        .paper-entry h3 a {{
            color: #ffffff;
            text-decoration: none;
        }}
        .paper-entry h3 a:hover {{
            color: #60a5fa;
        }}
        .paper-abstract {{
            color: #94a3b8;
            line-height: 1.6;
            font-size: 0.95rem;
            margin: 0;
        }}
    </style>
</head>
<body>
    {nav_html}
    <div class="papers-container">
        <div class="page-header">
            <h1>Papers</h1>
            <p class="lead">Technical papers on agency, alignment, and rationality</p>
        </div>
        {papers_list_html}
    </div>
    <footer>
        <p>&copy; Axionic Agency Lab</p>
    </footer>
</body>
</html>
"""

    with open('docs/papers/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

def generate_paper_redirects():
    """Generate HTML redirect pages for renamed papers"""
    redirects_file = Path('paper_redirects.json')
    if not redirects_file.exists():
        return 0

    try:
        with open(redirects_file, 'r', encoding='utf-8') as f:
            redirects = json.load(f)
    except:
        return 0

    # Filter out comments
    redirects = {k: v for k, v in redirects.items() if not k.startswith('_')}

    if not redirects:
        return 0

    papers_dest_dir = Path('docs/papers')
    papers_dest_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for old_name, new_name in redirects.items():
        # Ensure .html extension
        if not old_name.endswith('.html'):
            old_name += '.html'
        if not new_name.endswith('.html'):
            new_name += '.html'

        redirect_path = papers_dest_dir / old_name

        # Generate redirect HTML
        redirect_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={new_name}">
    <link rel="canonical" href="{new_name}">
    <title>Redirecting...</title>
    <script>
        window.location.href = "{new_name}";
    </script>
</head>
<body>
    <p>This page has moved to <a href="{new_name}">{new_name}</a>.</p>
    <p>You will be redirected automatically. If not, please click the link above.</p>
</body>
</html>
"""

        with open(redirect_path, 'w', encoding='utf-8') as f:
            f.write(redirect_html)

        count += 1

    return count

def process_papers():
    """Process markdown papers from papers/ to docs/papers/"""
    papers_src_dir = Path('papers')
    papers_dest_dir = Path('docs/papers')

    if not papers_src_dir.exists():
        return 0, []

    papers_dest_dir.mkdir(parents=True, exist_ok=True)

    # Get all markdown files except README.md
    papers = [p for p in papers_src_dir.glob('*.md') if p.name.lower() != 'readme.md']
    if not papers:
        return 0, []

    # Sort by title (extracted from filename, will be re-sorted by actual title later)
    papers.sort(key=lambda p: p.stem.lower())

    print(f"6. Processing {len(papers)} paper(s) from papers/...")

    papers_metadata = []

    for paper_path in papers:
        dest_path = papers_dest_dir / f"{paper_path.stem}.html"
        process_paper_file(paper_path, dest_path)
        print(f"   ✓ {paper_path.name} → {dest_path.relative_to('docs')}")

        # Extract metadata for index
        with open(paper_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title
        title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else paper_path.stem

        # Extract abstract (text after ## Abstract heading)
        abstract_match = re.search(r'^##\s+Abstract\s*$(.*?)^##', content, re.MULTILINE | re.DOTALL)
        abstract = ""
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            # Clean up the abstract: remove markdown formatting
            abstract_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', abstract_text)  # Remove bold
            abstract_text = re.sub(r'\$[^$]+\$', '', abstract_text)  # Remove inline math
            abstract_text = ' '.join(abstract_text.split())  # Normalize whitespace
            abstract = abstract_text

        papers_metadata.append({
            'title': title,
            'filename': f"{paper_path.stem}.html",
            'abstract': abstract
        })

    # Sort papers by title
    papers_metadata.sort(key=lambda p: p['title'].lower())

    # Generate papers index
    generate_papers_index(papers_metadata)
    print(f"   ✓ Generated papers/index.html")

    # Generate redirect pages for renamed papers
    redirect_count = generate_paper_redirects()
    if redirect_count > 0:
        print(f"   ✓ Generated {redirect_count} redirect page(s)")

    print()
    return len(papers), papers_metadata

def generate_sitemap(post_metadata, papers_metadata):
    """Generate sitemap.xml for SEO"""
    from datetime import datetime

    base_url = "https://axionic.org"
    sitemap_items = []
    today = datetime.now().strftime('%Y-%m-%d')

    # Add homepage
    sitemap_items.append({
        'loc': f"{base_url}/",
        'lastmod': today,
        'priority': '1.0'
    })

    # Add main section pages
    for page in ['about', 'research', 'team', 'publications']:
        sitemap_items.append({
            'loc': f"{base_url}/{page}.html",
            'lastmod': today,
            'priority': '0.9'
        })

    # Add papers index
    sitemap_items.append({
        'loc': f"{base_url}/papers/",
        'lastmod': today,
        'priority': '0.8'
    })

    # Add all papers
    for paper in papers_metadata:
        sitemap_items.append({
            'loc': f"{base_url}/papers/{paper['filename']}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'priority': '0.8'
        })

    # Add all published posts
    for post_id, metadata in post_metadata.items():
        if metadata.get('is_published') == 'true':
            post_date = metadata.get('date', '')
            try:
                date_obj = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                lastmod = date_obj.strftime('%Y-%m-%d')
            except:
                lastmod = datetime.now().strftime('%Y-%m-%d')

            sitemap_items.append({
                'loc': f"{base_url}/posts/{post_id}.html",
                'lastmod': lastmod,
                'priority': '0.7'
            })

    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for item in sitemap_items:
        xml += '  <url>\n'
        xml += f'    <loc>{escape(item["loc"])}</loc>\n'
        xml += f'    <lastmod>{item["lastmod"]}</lastmod>\n'
        xml += f'    <priority>{item["priority"]}</priority>\n'
        xml += '  </url>\n'

    xml += '</urlset>\n'

    with open('docs/sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(xml)

    return len(sitemap_items)

# ============================================
# SITE PAGE GENERATORS
# ============================================

def load_site_config():
    """Load site configuration from site-config.json"""
    config_path = Path('site-config.json')
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def generate_navigation(current_page, prefix=''):
    """Generate navigation HTML with active state for current page."""
    nav_items = [
        ('./', 'Home'),
        ('about.html', 'About'),
        ('research.html', 'Research'),
        ('team.html', 'Team'),
        ('publications.html', 'Publications'),
    ]

    links_html = ''
    for href, label in nav_items:
        active = ' class="active"' if href == current_page else ''
        links_html += f'<li><a href="{prefix}{href}"{active}>{label}</a></li>\n'

    return f'''<nav class="site-nav">
        <a href="{prefix if prefix else './'}" class="nav-brand">
            <img src="{prefix}images/axionic-logo.png" alt="Axionic">
            <span>Axionic Agency Lab</span>
        </a>
        <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">☰</button>
        <ul class="nav-links">
            {links_html}
        </ul>
    </nav>'''

def generate_page_wrapper(title, content, current_page, config, prefix='', extra_head='', extra_scripts=''):
    """Wrap content in full HTML page with navigation."""
    site_name = config.get('site', {}).get('name', 'Axionic Agency Lab')
    nav = generate_navigation(current_page, prefix)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} - {escape(site_name)}</title>
    <link rel="icon" type="image/png" href="{prefix}images/axionic-logo.png">
    <link rel="stylesheet" href="{prefix}style.css">
    {extra_head}
</head>
<body>
    {nav}
    {content}
    <footer>
        <p>&copy; {site_name}</p>
    </footer>
    {extra_scripts}
</body>
</html>'''

def generate_homepage(config, posts, papers_metadata):
    """Generate mission-first homepage."""
    site = config.get('site', {})
    mission = config.get('mission', {})
    research_areas = config.get('research_areas', [])

    # Get recent posts for featured section (top 5)
    recent_posts = sorted(
        [p for p in posts if p.get('is_published') == 'true'],
        key=lambda x: x.get('date', ''),
        reverse=True
    )[:5]

    # Build recent news HTML
    recent_news_html = ''
    for post in recent_posts:
        date = post.get('date', '')
        try:
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = date[:10] if date else ''

        recent_news_html += f'''<div class="news-item">
            <div class="date">{formatted_date}</div>
            <h3><a href="posts/{post['id']}.html">{escape(post.get('title', ''))}</a></h3>
        </div>
'''

    # Build research areas preview (top 3)
    research_preview_html = ''
    for area in research_areas[:3]:
        research_preview_html += f'''<div class="card">
            <div class="series-label">Series {area.get('series', '')}</div>
            <h3><a href="research.html#{area.get('id', '')}">{escape(area.get('name', ''))}</a></h3>
            <p>{escape(area.get('description', '')[:150])}...</p>
        </div>
'''

    content = f'''
    <div class="hero">
        <div class="hero-header">
            <img src="images/axionic-logo.png" alt="Axionic" class="hero-logo">
            <div class="hero-title">
                <h1>{escape(site.get('name', 'Axionic Agency Lab'))}</h1>
                <p class="tagline">{escape(site.get('tagline', ''))}</p>
            </div>
        </div>
        <p class="mission">{escape(mission.get('long', ''))}</p>
        <div class="section-links">
            <a href="research.html">Research</a>
            <a href="publications.html">Publications</a>
            <a href="about.html">About</a>
        </div>
    </div>

    <div class="featured-section">
        <h2>Research Areas</h2>
        <div class="card-grid" style="max-width: 900px; margin: 0 auto;">
            {research_preview_html}
        </div>
    </div>

'''

    return generate_page_wrapper('Home', content, './', config)

def generate_about_page(config):
    """Generate about/mission page."""

    content = '''
    <div class="page-container">
        <div class="page-header">
            <h1>About</h1>
            <p class="lead">Constitutive Conditions for Agency</p>
        </div>

        <article>
            <h2>Mission</h2>
            <p>The Axionic Agency Lab studies the conditions under which agency exists, persists, and remains well-defined in systems capable of self-reference, delegation, and self-modification.</p>

            <p>We do not treat agency as a given. We treat it as a fragile, derivative structure that exists only when specific coherence conditions hold. When those conditions fail, a system does not become "misaligned." It ceases to be well-defined as an agent at all.</p>

            <p>Our work aims to make that distinction precise.</p>

            <h2>Research Orientation</h2>
            <p>The lab's research is foundational rather than prescriptive. We do not begin with desired outcomes, human values, or safety guarantees. We ask a prior question:</p>

            <p><em>When does a system meaningfully count as an author of its own choices?</em></p>

            <p>This reframing has concrete consequences. Many approaches in AI alignment and safety focus on behavioral guarantees, learned compliance, or external oversight. Such approaches can preserve the appearance of agency while allowing agency itself to collapse under reflection.</p>

            <p>Axionic Agency Lab exists to study that failure mode.</p>

            <h2>Core Research Areas</h2>
            <p>Our work currently focuses on the following interconnected problems:</p>

            <ul>
                <li><strong>Sovereign Kernel Theory</strong><br>Formal conditions under which a system can preserve authorship, valuation, and evaluability across self-modification.</li>
                <li><strong>Reflective Stability and Failure Modes</strong><br>Empirical and theoretical analysis of stasis, hollow authority, survivability-without-liveness, and other forms of agency collapse.</li>
                <li><strong>Semantic Preservation and Breakdown</strong><br>Conditions under which self-evaluation, delegation, and interpretation continue to denote—and the points at which they fail.</li>
                <li><strong>Impossibility Results for Simulated Agency</strong><br>Structural limits separating genuine agency from behavioral imitation, policy execution, or externally stabilized control.</li>
            </ul>

            <p>This work applies to artificial systems across capability regimes and does not assume human-like cognition, values, or consciousness.</p>

            <h2>What This Lab Is Not</h2>
            <p>Axionic Agency Lab is not:</p>
            <ul>
                <li>a value-learning project</li>
                <li>a behavioral alignment or reward-shaping effort</li>
                <li>a governance or policy institute</li>
                <li>a safety-by-oversight program</li>
                <li>a moral or ethical theory</li>
            </ul>

            <p>Any convergence between agency preservation and desirable outcomes is contingent, not axiomatic.</p>

            <h2>Research Practice</h2>
            <p>Our methodology emphasizes:</p>
            <ul>
                <li>formal definitions over slogans</li>
                <li>falsifiable claims over aspirational guarantees</li>
                <li>negative results and failure classification as first-class outputs</li>
            </ul>

            <p>All research artifacts are published openly to support scrutiny, replication, and collaboration.</p>

            <h2>Contact</h2>
            <p>For collaboration inquiries or technical discussion, please reach out via <a href="https://github.com/macterra">GitHub</a>.</p>
        </article>
    </div>
'''

    return generate_page_wrapper('About', content, 'about.html', config)

def generate_research_page(config, papers_metadata):
    """Generate research areas page grouped by paper series."""
    research_areas = config.get('research_areas', [])

    # Count papers per series (add dot to prefix for exact matching)
    paper_counts = {}
    for paper in papers_metadata:
        filename = paper.get('filename', '')
        for area in research_areas:
            prefix = area.get('paper_prefix', '')
            # Add dot to ensure exact series match (I. vs II. vs III.)
            if prefix and filename.startswith(prefix + '.'):
                area_id = area.get('id', '')
                paper_counts[area_id] = paper_counts.get(area_id, 0) + 1

    # Build research areas HTML
    areas_html = ''
    for area in research_areas:
        area_id = area.get('id', '')
        count = paper_counts.get(area_id, 0)

        # Get papers for this series (add dot for exact matching)
        prefix = area.get('paper_prefix', '')
        series_papers = [p for p in papers_metadata if p.get('filename', '').startswith(prefix + '.')]

        papers_list = ''
        for paper in series_papers[:5]:  # Show first 5
            papers_list += f'<li><a href="papers/{paper.get("filename", "")}">{escape(paper.get("title", ""))}</a></li>'

        if len(series_papers) > 5:
            papers_list += f'<li><a href="papers/index.html#series-{area.get("series", "")}"><em>and {len(series_papers) - 5} more...</em></a></li>'

        areas_html += f'''
        <div class="card" id="{area_id}">
            <div class="series-label">Series {area.get('series', '')}</div>
            <h3>{escape(area.get('name', ''))}</h3>
            <p>{escape(area.get('description', ''))}</p>
            {f'<ul style="margin-top: 1rem; font-size: 0.9rem;">{papers_list}</ul>' if papers_list else ''}
            <div class="paper-count">{count} paper{'s' if count != 1 else ''}</div>
        </div>
'''

    # Find standalone papers (not matching any series prefix)
    series_prefixes = [area.get('paper_prefix', '') + '.' for area in research_areas if area.get('paper_prefix')]
    standalone_papers = [
        p for p in papers_metadata
        if not any(p.get('filename', '').startswith(prefix) for prefix in series_prefixes)
    ]

    standalone_html = ''
    if standalone_papers:
        standalone_list = ''
        for paper in standalone_papers:
            standalone_list += f'<li><a href="papers/{paper.get("filename", "")}">{escape(paper.get("title", ""))}</a></li>'

        standalone_html = f'''
    <div class="featured-section" id="foundational" style="margin-bottom: 3rem;">
        <h2>Foundational Papers</h2>
        <div class="card" style="max-width: 600px; margin: 1rem auto;">
            <p>Core documents defining the Axionic framework, terminology, and commitments.</p>
            <ul style="margin-top: 1rem; font-size: 0.95rem;">
                {standalone_list}
            </ul>
            <div class="paper-count">{len(standalone_papers)} paper{'s' if len(standalone_papers) != 1 else ''}</div>
        </div>
    </div>
'''

    content = f'''
    <div class="page-container">
        <div class="page-header">
            <h1>Research</h1>
            <p class="lead">Our research areas and ongoing projects</p>
        </div>
        {standalone_html}
        <h2 style="text-align: center; color: #94a3b8; font-weight: 400; margin-bottom: 2rem;">Paper Series</h2>
        <div class="card-grid">
            {areas_html}
        </div>

        <p style="text-align: center; margin-top: 2rem;">
            <a href="publications.html">Browse all publications →</a>
        </p>
    </div>
'''

    return generate_page_wrapper('Research', content, 'research.html', config)

def generate_team_page(config):
    """Generate team/people page."""
    team = config.get('team', [])

    members_html = ''
    for member in team:
        # Build links
        links_html = ''
        member_links = member.get('links', {})
        if member_links.get('email'):
            links_html += f'<a href="mailto:{member_links["email"]}" title="Email">✉</a>'
        if member_links.get('website'):
            links_html += f'<a href="{member_links["website"]}" title="Website">🌐</a>'
        if member_links.get('twitter'):
            links_html += f'<a href="{member_links["twitter"]}" title="Twitter">𝕏</a>'
        if member_links.get('github'):
            links_html += f'<a href="{member_links["github"]}" title="GitHub">⌨</a>'

        # Avatar placeholder or image
        if member.get('photo'):
            avatar_html = f'<img src="{member["photo"]}" alt="{escape(member.get("name", ""))}">'
        else:
            initials = ''.join(n[0] for n in member.get('name', 'A').split()[:2])
            avatar_html = initials

        members_html += f'''
        <div class="team-member">
            <div class="avatar">{avatar_html}</div>
            <h3>{escape(member.get('name', ''))}</h3>
            <div class="role">{escape(member.get('role', ''))}</div>
            <p class="bio">{escape(member.get('bio', ''))}</p>
            {f'<div class="links">{links_html}</div>' if links_html else ''}
        </div>
'''

    content = f'''
    <div class="page-container">
        <div class="page-header">
            <h1>Team</h1>
            <p class="lead">The agents behind Axionic Agency Lab</p>
        </div>

        <div class="team-grid">
            {members_html}
        </div>
    </div>
'''

    return generate_page_wrapper('Team', content, 'team.html', config)

def generate_news_page(config, posts):
    """Generate news page with recent posts."""
    news_config = config.get('news', {})
    recent_count = news_config.get('recent_count', 15)

    # Get recent published posts
    recent_posts = sorted(
        [p for p in posts if p.get('is_published') == 'true'],
        key=lambda x: x.get('date', ''),
        reverse=True
    )[:recent_count]

    news_html = ''
    for post in recent_posts:
        date = post.get('date', '')
        try:
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = date[:10] if date else ''

        subtitle = post.get('subtitle', '')
        excerpt = subtitle[:200] + '...' if len(subtitle) > 200 else subtitle

        news_html += f'''
        <div class="news-item">
            <div class="date">{formatted_date}</div>
            <h3><a href="posts/{post['id']}.html">{escape(post.get('title', ''))}</a></h3>
            {f'<p class="excerpt">{escape(excerpt)}</p>' if excerpt else ''}
        </div>
'''

    content = f'''
    <div class="page-container">
        <div class="page-header">
            <h1>News</h1>
            <p class="lead">Recent updates and essays</p>
        </div>

        <div class="news-list">
            {news_html}
        </div>

        <p style="text-align: center; margin-top: 2rem;">
            <a href="publications.html">Browse all publications →</a>
        </p>
    </div>
'''

    return generate_page_wrapper('News', content, 'news.html', config)

def generate_publications_page(config, posts, papers_count):
    """Generate publications page with posts and papers listing plus search."""
    from datetime import datetime

    # Get published posts
    published_posts = sorted(
        [p for p in posts if p.get('is_published') == 'true'],
        key=lambda x: x.get('date', ''),
        reverse=True
    )

    # Get archive date
    latest_date = max((p.get('date', '') for p in published_posts), default='')
    archive_date = "Unknown"
    if latest_date:
        try:
            date_obj = datetime.fromisoformat(latest_date.replace('Z', '+00:00'))
            archive_date = date_obj.strftime('%B %d, %Y')
        except:
            archive_date = latest_date[:10]

    # Build posts list HTML
    posts_html = ''
    for post in published_posts:
        date = post.get('date', '')
        try:
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = date[:10] if date else ''

        posts_html += f'''<li class="post-item">
                <div class="post-date">{escape(formatted_date)}</div>
                <h2 class="post-title">
                    <a href="posts/{post['id']}.html">{escape(post.get('title', ''))}</a>
                </h2>
'''
        if post.get('subtitle'):
            posts_html += f'''                <div class="post-subtitle">{escape(post['subtitle'])}</div>
'''
        posts_html += '''            </li>
'''

    extra_head = '<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0"></script>'

    search_script = f'''
    <script>
        let postsFuse, papersFuse;
        let allPosts = [], allPapers = [];
        let currentFilter = 'all';

        Promise.all([
            fetch('search-index.json').then(r => r.json()),
            fetch('papers-index.json').then(r => r.json())
        ]).then(([posts, papers]) => {{
            allPosts = posts;
            allPapers = papers;

            const fuseConfig = {{
                keys: [
                    {{ name: 'title', weight: 2 }},
                    {{ name: 'subtitle', weight: 1.5 }},
                    {{ name: 'content', weight: 1 }}
                ],
                threshold: 0.1,
                ignoreLocation: true,
                distance: 100000,
                includeScore: true,
                minMatchCharLength: 2,
                useExtendedSearch: false,
                findAllMatches: true
            }};

            postsFuse = new Fuse(posts, fuseConfig);
            papersFuse = new Fuse(papers, fuseConfig);
        }});

        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        const postList = document.getElementById('post-list');
        const postCount = document.getElementById('post-count');
        const filterRadios = document.querySelectorAll('input[name="search-filter"]');

        filterRadios.forEach(radio => {{
            radio.addEventListener('change', (e) => {{
                currentFilter = e.target.value;
                if (searchInput.value.trim().length >= 2) {{
                    searchInput.dispatchEvent(new Event('input'));
                }}
            }});
        }});

        function performSearch(query) {{
            let results = [];
            if (currentFilter === 'all') {{
                const postResults = postsFuse ? postsFuse.search(query) : [];
                const paperResults = papersFuse ? papersFuse.search(query) : [];
                results = [...postResults, ...paperResults].sort((a, b) => a.score - b.score);
            }} else if (currentFilter === 'posts') {{
                results = postsFuse ? postsFuse.search(query) : [];
            }} else if (currentFilter === 'papers') {{
                results = papersFuse ? papersFuse.search(query) : [];
            }}
            return results;
        }}

        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value.trim();
            if (query.length < 2) {{
                searchResults.innerHTML = '';
                postList.style.display = 'block';
                postCount.textContent = {len(published_posts)};
                return;
            }}

            const results = performSearch(query);
            if (results.length === 0) {{
                searchResults.innerHTML = '<div class="no-results">No results found</div>';
                postList.style.display = 'none';
                postCount.textContent = '0';
                return;
            }}

            postList.style.display = 'none';
            postCount.textContent = results.length;

            searchResults.innerHTML = results.map(result => {{
                const post = result.item;
                const isPaper = post.type === 'paper';
                let dateHtml = '';
                if (!isPaper && post.date) {{
                    const date = new Date(post.date).toLocaleDateString('en-US', {{
                        year: 'numeric', month: 'long', day: 'numeric'
                    }});
                    dateHtml = `<div class="post-date">${{date}}</div>`;
                }}
                let excerpt = post.content.substring(0, 200) + '...';
                const link = isPaper ? post.id + '.html' : 'posts/' + post.id + '.html';
                const typeLabel = isPaper ? '<span style="color: #888; font-size: 0.9em;">[Paper]</span> ' : '';
                return `
                    <div class="search-result-item">
                        ${{dateHtml}}
                        <h2 class="post-title">
                            ${{typeLabel}}<a href="${{link}}">${{escapeHtml(post.title)}}</a>
                        </h2>
                        ${{post.subtitle ? `<div class="post-subtitle">${{escapeHtml(post.subtitle)}}</div>` : ''}}
                        <div class="search-excerpt">${{escapeHtml(excerpt)}}</div>
                    </div>
                `;
            }}).join('');
        }});

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
    </script>'''

    content = f'''
    <div class="page-container">
        <div class="page-header">
            <h1>Publications</h1>
            <p class="lead">Essays and papers on agency, rationality, and alignment</p>
        </div>

        <div class="search-container">
            <input type="text" id="search-input" placeholder="Search posts and papers..." autocomplete="off">
            <div style="margin-top: 8px;">
                <label style="margin-right: 15px; font-size: 0.9em;">
                    <input type="radio" name="search-filter" value="all" checked> All
                </label>
                <label style="margin-right: 15px; font-size: 0.9em;">
                    <input type="radio" name="search-filter" value="posts"> Posts only
                </label>
                <label style="font-size: 0.9em;">
                    <input type="radio" name="search-filter" value="papers"> Papers only
                </label>
            </div>
            <div id="search-results"></div>
        </div>

        <div class="stats">
            <strong><span id="post-count">{len(published_posts)}</span> published posts</strong>
            <span style="margin: 0 10px;">•</span>
            <strong>{papers_count} papers</strong>
            <span style="margin: 0 10px;">•</span>
            <span>Updated {archive_date}</span>
            <span style="margin: 0 10px;">•</span>
            <a href="papers/index.html">Browse papers →</a>
        </div>

        <ul class="post-list" id="post-list">
{posts_html}        </ul>
    </div>
'''

    return generate_page_wrapper('Publications', content, 'publications.html', config, extra_head=extra_head, extra_scripts=search_script)

def main():
    print("=== Building Docs Site ===")
    print()

    # Load post mapping and metadata
    print("1. Loading post data from posts.csv...")
    slug_to_id = load_post_mapping()

    # Also load full metadata for titles/subtitles
    post_metadata = {}
    with open('posts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_id = row['post_id']
            post_metadata[post_id] = {
                'title': row.get('title', ''),
                'subtitle': row.get('subtitle', ''),
                'date': row.get('post_date', ''),
                'is_published': row.get('is_published', 'false')
            }

    print(f"   ✓ Loaded {len(slug_to_id)} post mappings")
    print()

    # Create docs directory structure
    print("2. Setting up docs/ directory...")
    docs_dir = Path('docs')
    docs_posts_dir = docs_dir / 'posts'
    images_dir = docs_dir / 'images'

    if docs_posts_dir.exists():
        shutil.rmtree(docs_posts_dir)
    docs_posts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    print(f"   ✓ Created {docs_posts_dir}")
    print(f"   ✓ Ensured {images_dir} exists")
    print()

    # Process all HTML files from posts/ to docs/posts/
    print("3. Downloading and localizing images, processing posts...")
    src_posts_dir = Path('posts')
    html_files = list(src_posts_dir.glob('*.html'))

    total_changes = 0
    files_processed = 0
    files_skipped = 0
    total_new_images = 0
    search_index = []
    image_map = {}  # Track all images we've seen

    for src_file in html_files:
        # Extract post_id from filename
        post_id = src_file.stem
        metadata = post_metadata.get(post_id, {})

        # Skip unpublished posts
        if metadata.get('is_published') != 'true':
            files_skipped += 1
            continue

        # Read source content
        with open(src_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Localize images in the content
        content, new_images = localize_images_in_content(content, images_dir, image_map)
        total_new_images += new_images

        # Now process with the localized content
        dest_file = docs_posts_dir / src_file.name
        changes, raw_content = process_post_file(src_file, dest_file, slug_to_id, metadata, localized_content=content)
        total_changes += changes
        files_processed += 1

        # Add to search index if published
        if metadata.get('title'):
            text_content = extract_text_from_html(raw_content)
            search_index.append({
                'id': post_id,
                'title': metadata.get('title', ''),
                'subtitle': metadata.get('subtitle', ''),
                'date': metadata.get('date', ''),
                'content': text_content  # Full text content
            })

    print(f"   ✓ Processed {files_processed} files, fixed {total_changes} links")
    if total_new_images > 0:
        print(f"   ✓ Downloaded {total_new_images} new image(s)")
    if files_skipped > 0:
        print(f"   ℹ Skipped {files_skipped} unpublished post(s)")
    print()

    # Load site configuration
    print("4. Loading site configuration...")
    config = load_site_config()
    print(f"   ✓ Loaded site config")
    print()

    # Build list of posts for page generators
    posts_list = [
        {'id': post_id, **metadata}
        for post_id, metadata in post_metadata.items()
    ]

    # Process papers
    papers_count, papers_metadata = process_papers()

    # Add papers to search index
    papers_src_dir = Path('papers')
    if papers_src_dir.exists():
        for paper_path in papers_src_dir.glob('*.md'):
            if paper_path.name.lower() != 'readme.md':
                with open(paper_path, 'r', encoding='utf-8') as f:
                    paper_content = f.read()

                # Extract title
                title_match = re.search(r'^#\s+(.+?)$', paper_content, re.MULTILINE)
                title = title_match.group(1) if title_match else paper_path.stem

                # Extract subtitle (italic text after title)
                subtitle_match = re.search(r'^\*(.+?)\*\s*$', paper_content, re.MULTILINE)
                subtitle = subtitle_match.group(1) if subtitle_match else ''

                # Extract date (format: YYYY.MM.DD)
                date_match = re.search(r'^(\d{4}\.\d{2}\.\d{2})\s*$', paper_content, re.MULTILINE)
                date = ''
                if date_match:
                    # Convert YYYY.MM.DD to ISO format YYYY-MM-DD
                    date = date_match.group(1).replace('.', '-') + 'T00:00:00.000Z'

                # Clean markdown for search: remove formatting but keep text
                text_content = paper_content
                text_content = re.sub(r'\$\$.*?\$\$', '', text_content, flags=re.DOTALL)  # Remove display math
                text_content = re.sub(r'\$[^$]+\$', '', text_content)  # Remove inline math
                text_content = re.sub(r'\*\*([^*]+)\*\*', r'\1', text_content)  # Remove bold
                text_content = re.sub(r'\*([^*]+)\*', r'\1', text_content)  # Remove italic
                text_content = re.sub(r'`([^`]+)`', r'\1', text_content)  # Remove code
                text_content = re.sub(r'#+\s+', '', text_content)  # Remove heading markers
                text_content = re.sub(r'\s+', ' ', text_content).strip()  # Normalize whitespace

                search_index.append({
                    'id': f"papers/{paper_path.stem}",
                    'title': title,
                    'subtitle': subtitle,
                    'date': date,
                    'content': text_content,
                    'type': 'paper'
                })

    # Generate search indexes (after papers are added)
    print("5. Generating search indexes...")
    # Sort by date, newest first (empty dates go to end)
    search_index.sort(key=lambda x: x.get('date', '') or '', reverse=True)

    # Split into posts and papers
    posts_index = [item for item in search_index if item.get('type') != 'paper']
    papers_index = [item for item in search_index if item.get('type') == 'paper']

    # Write posts index
    posts_index_path = docs_dir / 'search-index.json'
    with open(posts_index_path, 'w', encoding='utf-8') as f:
        json.dump(posts_index, f, ensure_ascii=False, indent=2)

    # Write papers index
    papers_index_path = docs_dir / 'papers-index.json'
    with open(papers_index_path, 'w', encoding='utf-8') as f:
        json.dump(papers_index, f, ensure_ascii=False, indent=2)

    print(f"   ✓ Created search-index.json with {len(posts_index)} posts ({posts_index_path.stat().st_size // 1024}KB)")
    print(f"   ✓ Created papers-index.json with {len(papers_index)} papers ({papers_index_path.stat().st_size // 1024}KB)")
    print()

    # Generate site pages
    print("7. Generating site pages...")

    # Homepage
    homepage_html = generate_homepage(config, posts_list, papers_metadata)
    with open(docs_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(homepage_html)
    print("   ✓ Generated index.html (homepage)")

    # About page
    about_html = generate_about_page(config)
    with open(docs_dir / 'about.html', 'w', encoding='utf-8') as f:
        f.write(about_html)
    print("   ✓ Generated about.html")

    # Research page
    research_html = generate_research_page(config, papers_metadata)
    with open(docs_dir / 'research.html', 'w', encoding='utf-8') as f:
        f.write(research_html)
    print("   ✓ Generated research.html")

    # Team page
    team_html = generate_team_page(config)
    with open(docs_dir / 'team.html', 'w', encoding='utf-8') as f:
        f.write(team_html)
    print("   ✓ Generated team.html")

    # Publications page
    publications_html = generate_publications_page(config, posts_list, papers_count)
    with open(docs_dir / 'publications.html', 'w', encoding='utf-8') as f:
        f.write(publications_html)
    print("   ✓ Generated publications.html")
    print()

    # Generate sitemap
    print("8. Generating sitemap.xml...")
    sitemap_count = generate_sitemap(post_metadata, papers_metadata)
    print(f"   ✓ Created sitemap with {sitemap_count} URLs")
    print()

    print("=== Build Complete ===")
    if papers_count > 0:
        print(f"   Papers: {papers_count} processed")

if __name__ == '__main__':
    main()
