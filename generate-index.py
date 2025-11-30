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
    with open('posts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['is_published'] == 'true' and row['title']:  # Only published posts with titles
                posts.append({
                    'id': row['post_id'],
                    'title': row['title'],
                    'subtitle': row['subtitle'],
                    'date': row['post_date']
                })

    # Sort by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)

    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Axio - Blog Archive</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        header {
            border-bottom: 3px solid #2c3e50;
            margin-bottom: 40px;
            padding-bottom: 20px;
        }

        h1 {
            font-size: 2.5em;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .post-list {
            list-style: none;
        }

        .post-item {
            margin-bottom: 30px;
            padding-bottom: 30px;
            border-bottom: 1px solid #eee;
        }

        .post-item:last-child {
            border-bottom: none;
        }

        .post-date {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 5px;
        }

        .post-title {
            font-size: 1.5em;
            margin-bottom: 8px;
        }

        .post-title a {
            color: #2c3e50;
            text-decoration: none;
            transition: color 0.2s;
        }

        .post-title a:hover {
            color: #3498db;
        }

        .post-subtitle {
            color: #666;
            font-style: italic;
        }

        footer {
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #888;
            font-size: 0.9em;
        }

        .stats {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Axio</h1>
            <p class="subtitle">A collection of essays on agency, rationality, and the future</p>
        </header>

        <div class="stats">
            <strong>""" + str(len(posts)) + """ published posts</strong>
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
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated index.html with {len(posts)} posts")

if __name__ == '__main__':
    main()
