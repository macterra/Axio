#!/usr/bin/env python3
"""
Build the docs/ directory from posts/ with fixed links and custom CSS

This script:
1. Copies posts/ to docs/posts/
2. Fixes internal Substack links to point to local files
3. Injects custom CSS for better readability
4. Generates index.html

Usage:
    python3 build-site.py
"""

import os
import re
import csv
import shutil
from pathlib import Path

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

CUSTOM_CSS = """
<style>
    /* RESET & BASE */
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    body {
        background-color: #03050e;
        color: #e6e6e6;
        font-family: 'Georgia', 'Times New Roman', serif;
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
        padding: 40px 20px;
    }

    /* LAYOUT CONTAINER */
    article {
        max-width: 680px;
        margin: 0 auto;
    }

    /* BACK LINK */
    .back-link {
        display: inline-block;
        margin-bottom: 24px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 0.85rem;
        color: #94a3b8;
        text-decoration: none;
        transition: color 0.2s;
    }

    .back-link:hover {
        color: #fff;
    }

    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Georgia', serif;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
        line-height: 1.2;
    }

    h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    h2 {
        font-size: 2rem;
        margin-top: 2rem;
    }

    h3 {
        font-size: 1.5rem;
        margin-top: 1.5rem;
    }

    /* PARAGRAPHS & CONTENT */
    p {
        font-size: 1.125rem;
        line-height: 1.7;
        color: #e2e8f0;
        margin-bottom: 1.5em;
    }

    /* LINKS */
    a {
        color: #60a5fa;
        text-decoration: none;
        transition: color 0.2s;
    }

    a:hover {
        color: #93c5fd;
        text-decoration: underline;
    }

    /* LISTS */
    ul, ol {
        margin-bottom: 1.5em;
        padding-left: 2em;
        color: #e2e8f0;
    }

    li {
        margin-bottom: 0.5em;
        line-height: 1.7;
    }

    /* BLOCKQUOTES */
    blockquote {
        border-left: 3px solid #334155;
        padding-left: 1.5em;
        margin: 1.5em 0;
        color: #94a3b8;
        font-style: italic;
    }

    /* CODE */
    code {
        background-color: #1e293b;
        color: #e2e8f0;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-size: 0.9em;
        font-family: 'Consolas', 'Monaco', monospace;
    }

    pre {
        background-color: #1e293b;
        padding: 1em;
        border-radius: 5px;
        overflow-x: auto;
        margin-bottom: 1.5em;
    }

    pre code {
        background: none;
        padding: 0;
    }

    /* IMAGES */
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 2em 0;
    }

    figure {
        margin: 2em 0;
    }

    /* DIVIDERS */
    hr {
        border: none;
        border-top: 1px solid #1e293b;
        margin: 2em 0;
    }

    /* TABLES */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 2em 0;
        color: #e2e8f0;
    }

    th, td {
        padding: 0.75em;
        text-align: left;
        border-bottom: 1px solid #1e293b;
    }

    th {
        font-weight: 700;
        color: #ffffff;
        background-color: #0f172a;
    }

    /* STRONG/BOLD */
    strong {
        color: #ffffff;
        font-weight: 700;
    }

    /* EMPHASIS */
    em {
        color: #cbd5e1;
    }
</style>
"""

def process_post_file(src_path, dest_path, slug_to_id):
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

    # Wrap content in proper HTML structure with CSS
    wrapped_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Axio - Post</title>
{CUSTOM_CSS}
</head>
<body>
    <div class="back-link"><a href="../index.html">← Back to Index</a></div>
    <article>
{content}
    </article>
</body>
</html>
"""

    # Write processed content
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(wrapped_content)

    return changes

def main():
    print("=== Building Docs Site ===")
    print()

    # Load post mapping
    print("1. Loading post mapping from posts.csv...")
    slug_to_id = load_post_mapping()
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

    for src_file in html_files:
        dest_file = docs_posts_dir / src_file.name
        changes = process_post_file(src_file, dest_file, slug_to_id)
        total_changes += changes
        files_processed += 1

    print(f"   ✓ Processed {files_processed} files, fixed {total_changes} links")
    print()

    # Generate index.html in docs/
    print("4. Generating index.html...")
    os.system('python3 generate-index.py')

    # Move index.html to docs/
    if Path('index.html').exists():
        shutil.move('index.html', docs_dir / 'index.html')
        print(f"   ✓ Moved index.html to docs/")
    print()

    print("=== Build Complete ===")

if __name__ == '__main__':
    main()
