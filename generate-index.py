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
    <link rel="icon" type="image/webp" href="axio.webp">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0"></script>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <img src="axio.webp" alt="Axio" class="index-logo">
                <h1>Axio</h1>
            </div>
            <p class="subtitle">A collection of essays and <a href="papers/index.html">papers</a> on agency, rationality, and the future</p>
        </header>

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
            <strong><span id="post-count">""" + str(len(posts)) + """</span> published posts</strong>
            <span style="margin: 0 10px;">•</span>
            <span>Archive updated """ + archive_date + """</span>
        </div>

        <ul class="post-list" id="post-list">
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

    <script>
        let postsFuse, papersFuse;
        let allPosts = [], allPapers = [];
        let currentFilter = 'all';

        // Load both search indexes
        Promise.all([
            fetch('search-index.json').then(r => r.json()),
            fetch('papers-index.json').then(r => r.json())
        ]).then(([posts, papers]) => {
            allPosts = posts;
            allPapers = papers;

            const fuseConfig = {
                keys: [
                    { name: 'title', weight: 2 },
                    { name: 'subtitle', weight: 1.5 },
                    { name: 'content', weight: 1 }
                ],
                threshold: 0.1,
                ignoreLocation: true,
                distance: 100000,
                includeScore: true,
                minMatchCharLength: 2,
                useExtendedSearch: false,
                findAllMatches: true
            };

            postsFuse = new Fuse(posts, fuseConfig);
            papersFuse = new Fuse(papers, fuseConfig);
        });

        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        const postList = document.getElementById('post-list');
        const postCount = document.getElementById('post-count');
        const filterRadios = document.querySelectorAll('input[name="search-filter"]');

        // Update filter when radio buttons change
        filterRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                currentFilter = e.target.value;
                // Re-run search if there's a query
                if (searchInput.value.trim().length >= 2) {
                    searchInput.dispatchEvent(new Event('input'));
                }
            });
        });

        function performSearch(query) {
            let results = [];

            if (currentFilter === 'all') {
                const postResults = postsFuse ? postsFuse.search(query) : [];
                const paperResults = papersFuse ? papersFuse.search(query) : [];
                results = [...postResults, ...paperResults].sort((a, b) => a.score - b.score);
            } else if (currentFilter === 'posts') {
                results = postsFuse ? postsFuse.search(query) : [];
            } else if (currentFilter === 'papers') {
                results = papersFuse ? papersFuse.search(query) : [];
            }

            return results;
        }

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            if (query.length < 2) {
                searchResults.innerHTML = '';
                postList.style.display = 'block';
                postCount.textContent = """ + str(len(posts)) + """;
                return;
            }

            const results = performSearch(query);

            if (results.length === 0) {
                searchResults.innerHTML = '<div class="no-results">No results found</div>';
                postList.style.display = 'none';
                postCount.textContent = '0';
                return;
            }

            postList.style.display = 'none';
            postCount.textContent = results.length;

            searchResults.innerHTML = results.map(result => {
                const post = result.item;
                const isPaper = post.type === 'paper';

                // Format date for posts (papers don't have dates)
                let dateHtml = '';
                if (!isPaper && post.date) {
                    const date = new Date(post.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                    dateHtml = `<div class="post-date">${date}</div>`;
                }

                // Create excerpt with highlighted match
                let excerpt = post.content.substring(0, 200) + '...';

                // Determine the correct link based on type
                const link = isPaper ? post.id + '.html' : 'posts/' + post.id + '.html';
                const typeLabel = isPaper ? '<span style="color: #888; font-size: 0.9em;">[Paper]</span> ' : '';

                return `
                    <div class="search-result-item">
                        ${dateHtml}
                        <h2 class="post-title">
                            ${typeLabel}<a href="${link}">${escapeHtml(post.title)}</a>
                        </h2>
                        ${post.subtitle ? `<div class="post-subtitle">${escapeHtml(post.subtitle)}</div>` : ''}
                        <div class="search-excerpt">${escapeHtml(excerpt)}</div>
                    </div>
                `;
            }).join('');
        });

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""

    # Write index.html
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated docs/index.html with {len(posts)} posts")

if __name__ == '__main__':
    main()
