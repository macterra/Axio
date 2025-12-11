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

## Image Localization

The build script automatically:
- Detects all Substack image URLs in posts
- Downloads new images to `docs/images/`
- Replaces remote URLs with local references
- Skips images that are already downloaded

This makes your archive completely self-contained and independent of Substack's servers. When you add new posts, any new images will be automatically downloaded during the build process.

## Directory Structure

- `posts/` - Original HTML files from Substack export (not published to site)
- `docs/` - Built site for GitHub Pages (auto-generated)
  - `docs/index.html` - Main landing page with search functionality
  - `docs/posts/` - Processed post HTML files with fixed links and custom CSS
  - `docs/images/` - Local copies of all images (597 images, ~1.1GB)
  - `docs/search-index.json` - Full-text search index
  - `docs/style.css` - Custom CSS styling
  - `docs/axio.webp` - Site logo (displayed on all pages and browser tabs)
- `posts.csv` - Post metadata from Substack export

## Build Scripts

- `build-site.py` - Main build script that:
  - **Automatically downloads and localizes all Substack images** to `docs/images/`
  - Copies posts from `posts/` to `docs/posts/` with localized image references
  - Fixes internal Substack links to point to local files
  - Skips unpublished posts (draft posts are not included in the archive)
  - Injects custom CSS for better readability
  - Adds logo and "Back to Index" links
  - Generates the search index
  - Generates the index page
- `generate-index.py` - Generates index.html from posts.csv (called by build-site.py)
- `update-site.sh` - Convenience wrapper that cleans up and runs the build
- `download-images.py` - Standalone script to download images (now integrated into build-site.py)
- `fix-image-urls.py` - Standalone script to fix image URLs (now integrated into build-site.py)

## Configuration

- `_config.yml` - GitHub Pages configuration
- `.nojekyll` - Disables Jekyll processing
