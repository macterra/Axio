#!/bin/bash
#
# Update Axio blog archive site
#
# This script:
# 1. Removes Zone.Identifier files from Windows downloads
# 2. Regenerates the index.html from posts.csv
# 3. Shows git status
#
# Usage:
#   ./update-site.sh
#

set -e  # Exit on error

echo "=== Updating Axio Blog Archive ==="
echo

# Remove Zone.Identifier files if any exist
echo "1. Cleaning up Zone.Identifier files..."
ZONE_FILES=$(find . -type f -name "*:Zone.Identifier" 2>/dev/null | wc -l)
if [ "$ZONE_FILES" -gt 0 ]; then
    find . -type f -name "*:Zone.Identifier" -delete
    echo "   ✓ Removed $ZONE_FILES Zone.Identifier files"
else
    echo "   ✓ No Zone.Identifier files found"
fi
echo

# Regenerate index.html
echo "2. Generating index.html..."
python3 generate-index.py
echo

# Show git status
echo "3. Git status:"
git status --short
echo

echo "=== Update Complete ==="
echo
echo "Next steps:"
echo "  git add ."
echo "  git commit -m 'Update blog archive'"
echo "  git push"
echo
