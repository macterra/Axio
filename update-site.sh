#!/bin/bash
#
# Update Axio blog archive site
#
# This script:
# 1. Extracts any Substack archive ZIP files
# 2. Removes Zone.Identifier files from Windows downloads
# 3. Builds the docs/ directory with fixed links and custom CSS
# 4. Shows git status
#
# Usage:
#   ./update-site.sh
#

set -e  # Exit on error

echo "=== Updating Axio Blog Archive ==="
echo

# Extract any zip files in the root directory
echo "1. Checking for Substack archive ZIP files..."
ZIP_COUNT=$(find . -maxdepth 1 -type f -name "*.zip" 2>/dev/null | wc -l)
if [ "$ZIP_COUNT" -gt 0 ]; then
    for zipfile in *.zip; do
        if [ -f "$zipfile" ]; then
            echo "   Extracting $zipfile..."
            unzip -o "$zipfile"
            echo "   ✓ Extracted $zipfile"
        fi
    done
else
    echo "   ✓ No ZIP files found"
fi
echo

# Remove Zone.Identifier files if any exist
echo "2. Cleaning up Zone.Identifier files..."
ZONE_FILES=$(find . -type f -name "*:Zone.Identifier" 2>/dev/null | wc -l)
if [ "$ZONE_FILES" -gt 0 ]; then
    find . -type f -name "*:Zone.Identifier" -delete
    echo "   ✓ Removed $ZONE_FILES Zone.Identifier files"
else
    echo "   ✓ No Zone.Identifier files found"
fi
echo

# Build the docs site
echo "3. Building docs/ site..."
python3 build-site.py
echo

# Show git status
echo "4. Git status:"
git status --short
echo

echo "=== Update Complete ==="
echo
echo "Next steps:"
echo "  git add ."
echo "  git commit -m 'Update blog archive'"
echo "  git push"
echo
