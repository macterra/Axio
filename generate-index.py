#!/usr/bin/env python3
"""
Generate index.html for Axio blog archive from posts.csv

This script reads the Substack posts.csv export and creates a static
index page listing all published posts with links to their HTML files.

Usage:
    python3 generate-index.py
"""

import csv
from datetime import datetime
from html import escape

def main():
    # Read posts from CSV
    posts = []
    latest_date = None

    with open('posts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['is_published'] == 'true' and row['title']:  # Only published posts with titles
                post_date = row['post_date']
                posts.append({
                    'id': row['post_id'],
                    'title': row['title'],
                    'subtitle': row['subtitle'],
                    'date': post_date
                })

                # Track the most recent post date
                if post_date and (not latest_date or post_date > latest_date):
                    latest_date = post_date

    # Sort by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)

    # Format archive date
    archive_date = "Unknown"
    if latest_date:
        try:
            date_obj = datetime.fromisoformat(latest_date.replace('Z', '+00:00'))
            archive_date = date_obj.strftime('%B %d, %Y')
        except:
            archive_date = latest_date[:10]

    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Axio - Blog Archive</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Axio</h1>
            <p class="subtitle">A collection of essays on agency, rationality, and the future</p>
        </header>

        <div class="stats">
            <strong>""" + str(len(posts)) + """ published posts</strong>
            <span style="margin: 0 10px;">•</span>
            <span>Archive updated """ + archive_date + """</span>
        </div>

        <ul class="post-list">
"""

    for post in posts:
        # Format date
        try:
            date_obj = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = post['date'][:10]

        # Build the post HTML filename
        post_file = f"posts/{post['id']}.html"

        html += f"""            <li class="post-item">
                <div class="post-date">{escape(formatted_date)}</div>
                <h2 class="post-title">
                    <a href="{escape(post_file)}">{escape(post['title'])}</a>
                </h2>
"""
        if post['subtitle']:
            html += f"""                <div class="post-subtitle">{escape(post['subtitle'])}</div>
"""
        html += """            </li>
"""

    html += """        </ul>

        <footer>
            <p>Backup of Substack blog &middot; Hosted on GitHub Pages</p>
        </footer>
    </div>
</body>
</html>
"""

    # Write index.html
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated docs/index.html with {len(posts)} posts")

if __name__ == '__main__':
    main()
