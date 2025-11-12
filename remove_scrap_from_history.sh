#!/bin/bash
# Script to remove scrap/ folder from entire git history
# WARNING: This rewrites git history and requires force push!

set -e

echo "============================================================"
echo "  Remove scrap/ folder from Git History"
echo "============================================================"
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "⚠️  All collaborators will need to re-clone the repository"
echo "⚠️  This operation cannot be easily undone"
echo ""
echo "Recommended steps before running:"
echo "  1. Create a backup: git clone . ../clickup_framework_backup"
echo "  2. Inform all team members"
echo "  3. Ensure you have a backup of any important data"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Checking for git-filter-repo..."

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "git-filter-repo is not installed."
    echo ""
    echo "Installation options:"
    echo "  1. pip install git-filter-repo"
    echo "  2. Download from: https://github.com/newren/git-filter-repo"
    echo ""

    read -p "Would you like to install it via pip now? (yes/no): " install_confirm

    if [ "$install_confirm" = "yes" ]; then
        pip install git-filter-repo
    else
        echo "Please install git-filter-repo and run this script again."
        exit 1
    fi
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
echo "Fetching all branches and tags..."
git fetch --all --tags

echo ""
echo "Removing scrap/ folder from history..."
echo "This may take a few minutes..."
echo ""

# Use git-filter-repo to remove the scrap directory
git filter-repo --path scrap --invert-paths --force

echo ""
echo "✓ scrap/ folder removed from git history"
echo ""
echo "Checking repository size reduction..."

# Show the size difference
du -sh .git

echo ""
echo "Running git garbage collection to reclaim space..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✓ Garbage collection complete"
echo ""
du -sh .git

echo ""
echo "============================================================"
echo "✓ History rewrite complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Verify the changes:"
echo "   git log --all --oneline | head -20"
echo "   git diff main origin/main"
echo ""
echo "2. Add back your remotes (they were removed by filter-repo):"
echo "   git remote add origin https://github.com/SOELexicon/clickup_framework.git"
echo ""
echo "3. Force push to remote (⚠️  WARNING: This will rewrite remote history!):"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "4. Notify all team members to re-clone the repository:"
echo "   git clone https://github.com/SOELexicon/clickup_framework.git"
echo ""
echo "If something went wrong, restore from backup:"
echo "   cd .."
echo "   rm -rf clickup_framework"
echo "   mv clickup_framework_backup clickup_framework"
echo ""
