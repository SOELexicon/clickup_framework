#!/bin/bash
# Alternative script using git filter-branch (no additional tools required)
# WARNING: This rewrites git history and requires force push!

set -e

echo "============================================================"
echo "  Remove scrap/ folder from Git History (filter-branch)"
echo "============================================================"
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "⚠️  All collaborators will need to re-clone the repository"
echo "⚠️  This operation cannot be easily undone"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Creating backup of current repository..."
if [ ! -d "../clickup_framework_backup" ]; then
    git clone . ../clickup_framework_backup
    echo "✓ Backup created at ../clickup_framework_backup"
else
    echo "ℹ️  Backup already exists at ../clickup_framework_backup"
fi

echo ""
echo "Removing scrap/ folder from history using filter-branch..."
echo "This may take several minutes..."
echo ""

# Use git filter-branch to remove the scrap directory
git filter-branch --force --index-filter \
    'git rm -rf --cached --ignore-unmatch scrap/' \
    --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✓ scrap/ folder removed from git history"
echo ""

# Clean up the backup refs
echo "Cleaning up backup references..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "============================================================"
echo "✓ History rewrite complete!"
echo "============================================================"
echo ""
echo "Repository size after cleanup:"
du -sh .git
echo ""
echo "Next steps:"
echo ""
echo "1. Verify the changes:"
echo "   git log --all --oneline -- scrap/"
echo "   (Should show no results)"
echo ""
echo "2. Force push to remote (⚠️  WARNING: This rewrites remote history!):"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "3. Notify all team members to re-clone or reset:"
echo "   # Option A: Re-clone (recommended)"
echo "   git clone https://github.com/SOELexicon/clickup_framework.git"
echo ""
echo "   # Option B: Reset existing clone"
echo "   git fetch origin"
echo "   git reset --hard origin/main  # or master"
echo "   git clean -fdx"
echo ""
