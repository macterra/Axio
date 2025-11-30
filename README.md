# Axio

Backup archive of my Substack blog, hosted on GitHub Pages.

**Live site:** https://macterra.github.io/Axio/

## Updating the Archive

When you download a new Substack archive:

1. Extract the archive and copy `posts.csv` and the `posts/` directory to this repository
2. Run the update script:
   ```bash
   ./update-site.sh
   ```
3. Review changes and commit:
   ```bash
   git add .
   git commit -m "Update blog archive"
   git push
   ```

The site will automatically rebuild on GitHub Pages within a few minutes.

## Directory Structure

- `posts/` - Original HTML files from Substack export (not published to site)
- `docs/` - Built site for GitHub Pages (auto-generated)
  - `docs/index.html` - Main landing page
  - `docs/posts/` - Processed post HTML files with fixed links and custom CSS
- `posts.csv` - Post metadata from Substack export

## Build Scripts

- `build-site.py` - Main build script that:
  - Copies posts from `posts/` to `docs/posts/`
  - Fixes internal Substack links to point to local files
  - Injects custom CSS for better readability
  - Adds "Back to Index" links
  - Generates the index page
- `generate-index.py` - Generates index.html from posts.csv
- `update-site.sh` - Convenience wrapper that cleans up and runs the build

## Configuration

- `_config.yml` - GitHub Pages configuration
- `.nojekyll` - Disables Jekyll processing
