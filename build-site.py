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
    <link rel="icon" type="image/webp" href="../axio.webp">

    <!-- KaTeX CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">

    <!-- Site Styles -->
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <div class="header-bar">
        <a href="../index.html" class="logo-link">
            <img src="../axio.webp" alt="Axio" class="site-logo">
        </a>
        <div class="back-link"><a href="../index.html">← Back to Index</a></div>
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
    """Convert a markdown paper to HTML with proper styling"""
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

    # Wrap in styled HTML
    wrapped_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} - Axio</title>
    <link rel="icon" type="image/webp" href="../axio.webp">

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

    <!-- Site Styles -->
    <link rel="stylesheet" href="../style.css">
    <style>
        article {{
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.7;
        }}
        article h1 {{
            margin-top: 2em;
            margin-bottom: 0.5em;
        }}
        article h2 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        article p {{
            margin: 1em 0;
        }}
    </style>
</head>
<body>
    <div class="header-bar">
        <a href="../index.html" class="logo-link">
            <img src="../axio.webp" alt="Axio" class="site-logo">
        </a>
        <div class="back-link"><a href="index.html">← Back to Papers</a></div>
    </div>
    <article>
{content_html}
    </article>
</body>
</html>
"""

    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(wrapped_html)

def generate_papers_index(papers_metadata):
    """Generate an index.html for the papers directory"""
    papers_list_html = ""

    for paper in papers_metadata:
        title = paper['title']
        filename = paper['filename']
        abstract = paper.get('abstract', '')

        abstract_html = f"<p class='paper-abstract'>{escape(abstract)}</p>" if abstract else ""

        papers_list_html += f"""
        <div class="paper-entry">
            <h2><a href="{filename}">{escape(title)}</a></h2>
            {abstract_html}
        </div>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Papers - Axio</title>
    <link rel="icon" type="image/webp" href="../axio.webp">
    <link rel="stylesheet" href="../style.css">
    <style>
        .papers-container {{
            max-width: 900px;
            margin: 2em auto;
            padding: 0 2em;
        }}
        .paper-entry {{
            margin: 2em 0;
            padding: 1em 0;
            border-bottom: 1px solid #eee;
        }}
        .paper-entry h2 {{
            margin: 0 0 0.5em 0;
        }}
        .paper-entry h2 a {{
            text-decoration: none;
        }}
        .paper-abstract {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="header-bar">
        <a href="../index.html" class="logo-link">
            <img src="../axio.webp" alt="Axio" class="site-logo">
        </a>
        <div class="back-link"><a href="../index.html">← Back to Index</a></div>
    </div>
    <div class="papers-container">
        <h1>Papers</h1>
        {papers_list_html}
    </div>
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
            # Clean up the abstract: remove markdown formatting and limit length
            abstract_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', abstract_text)  # Remove bold
            abstract_text = re.sub(r'\$[^$]+\$', '', abstract_text)  # Remove inline math
            abstract_text = ' '.join(abstract_text.split())  # Normalize whitespace
            if len(abstract_text) > 500:
                abstract = abstract_text[:497] + "..."
            else:
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

    # Add homepage
    sitemap_items.append({
        'loc': f"{base_url}/",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'priority': '1.0'
    })

    # Add papers index
    sitemap_items.append({
        'loc': f"{base_url}/papers/",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'priority': '0.9'
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

    # Generate index.html in docs/
    print("4. Generating index.html...")
    os.system('python3 generate-index.py')

    # Move index.html to docs/
    if Path('index.html').exists():
        shutil.move('index.html', docs_dir / 'index.html')
        print(f"   ✓ Moved index.html to docs/")
    print()

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

    # Generate search index (after papers are added)
    print("5. Generating search index...")
    search_index_path = docs_dir / 'search-index.json'
    with open(search_index_path, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)
    print(f"   ✓ Created search index with {len(search_index)} items ({len([x for x in search_index if x.get('type') != 'paper'])} posts, {len([x for x in search_index if x.get('type') == 'paper'])} papers) ({search_index_path.stat().st_size // 1024}KB)")
    print()

    # Generate sitemap
    print("7. Generating sitemap.xml...")
    sitemap_count = generate_sitemap(post_metadata, papers_metadata)
    print(f"   ✓ Created sitemap with {sitemap_count} URLs")
    print()

    print("=== Build Complete ===")
    if papers_count > 0:
        print(f"   Papers: {papers_count} processed")

if __name__ == '__main__':
    main()
