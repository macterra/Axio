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
    body {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        color: #333;
    }
    a {
        color: #2c3e50;
        text-decoration: none;
    }
    a:hover {
        color: #3498db;
        text-decoration: underline;
    }
    .back-link {
        display: inline-block;
        margin-bottom: 20px;
        font-size: 0.9em;
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
