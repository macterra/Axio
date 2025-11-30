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

## Files

- `index.html` - Main landing page (auto-generated)
- `posts/` - Individual post HTML files from Substack export
- `posts.csv` - Post metadata from Substack export
- `generate-index.py` - Script to generate index.html from posts.csv
- `update-site.sh` - Convenience script to update the site
- `_config.yml` - GitHub Pages configuration
- `.nojekyll` - Disables Jekyll processing
