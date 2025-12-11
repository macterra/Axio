#!/usr/bin/env python3
"""
Build the docs/ directory from posts/ with fixed links and custom CSS

This script:
1. Copies posts/ to docs/posts/
2. Fixes internal Substack links to point to local files
3. Injects custom CSS for better readability
4. Generates index.html
5. Creates search index for full-text search

Usage:
    python3 build-site.py
"""

import os
import re
import csv
import json
import shutil
from pathlib import Path
from html import escape
from html.parser import HTMLParser

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

def process_post_file(src_path, dest_path, slug_to_id, post_metadata):
    """Copy and process a single post HTML file"""
    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()

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

        if title:
            title_html = f'<h1 class="post-title">{escape(title)}</h1>\n'
        if subtitle:
            title_html += f'<p class="post-subtitle">{escape(subtitle)}</p>\n'
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

    if docs_posts_dir.exists():
        shutil.rmtree(docs_posts_dir)
    docs_posts_dir.mkdir(parents=True, exist_ok=True)
    print(f"   ✓ Created {docs_posts_dir}")
    print()

    # Process all HTML files from posts/ to docs/posts/
    print("3. Processing posts...")
    src_posts_dir = Path('posts')
    html_files = list(src_posts_dir.glob('*.html'))

    total_changes = 0
    files_processed = 0
    files_skipped = 0
    search_index = []

    for src_file in html_files:
        # Extract post_id from filename
        post_id = src_file.stem
        metadata = post_metadata.get(post_id, {})

        # Skip unpublished posts
        if metadata.get('is_published') != 'true':
            files_skipped += 1
            continue

        dest_file = docs_posts_dir / src_file.name
        changes, raw_content = process_post_file(src_file, dest_file, slug_to_id, metadata)
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
    if files_skipped > 0:
        print(f"   ℹ Skipped {files_skipped} unpublished post(s)")
    print()

    # Generate search index
    print("4. Generating search index...")
    search_index_path = docs_dir / 'search-index.json'
    with open(search_index_path, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False)
    print(f"   ✓ Created search index with {len(search_index)} posts ({search_index_path.stat().st_size // 1024}KB)")
    print()

    # Generate index.html in docs/
    print("5. Generating index.html...")
    os.system('python3 generate-index.py')

    # Move index.html to docs/
    if Path('index.html').exists():
        shutil.move('index.html', docs_dir / 'index.html')
        print(f"   ✓ Moved index.html to docs/")
    print()

    print("=== Build Complete ===")

if __name__ == '__main__':
    main()
