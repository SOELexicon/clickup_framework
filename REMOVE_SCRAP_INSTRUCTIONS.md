# Instructions: Remove scrap/ Folder from Git History

This guide provides multiple methods to completely remove the `scrap/` folder from your git history and reclaim disk space.

## ⚠️ Important Warnings

- **This rewrites git history** - all commit SHAs will change
- **Requires force push** - will overwrite remote repository
- **Team coordination required** - all collaborators must re-clone or reset
- **Cannot be easily undone** - make backups first!

## Prerequisites

1. **Create a backup:**
   ```bash
   git clone . ../clickup_framework_backup
   ```

2. **Ensure clean working directory:**
   ```bash
   git status  # Should show "nothing to commit, working tree clean"
   ```

3. **Notify team members** - they will need to re-clone after you push

## Method 1: Using git-filter-repo (Recommended)

`git-filter-repo` is the modern, faster, and safer tool for rewriting history.

### Installation

```bash
# Option 1: Via pip
pip install git-filter-repo

# Option 2: Download directly
# Visit: https://github.com/newren/git-filter-repo
```

### Run the automated script

```bash
chmod +x remove_scrap_from_history.sh
./remove_scrap_from_history.sh
```

### Or run commands manually

```bash
# 1. Remove scrap/ from history
git filter-repo --path scrap --invert-paths --force

# 2. Re-add your remote (filter-repo removes it for safety)
git remote add origin https://github.com/SOELexicon/clickup_framework.git

# 3. Force push
git push origin --force --all
git push origin --force --tags
```

## Method 2: Using git filter-branch (Built-in, Slower)

If you can't install git-filter-repo, use the built-in `git filter-branch`.

### Run the automated script

```bash
chmod +x remove_scrap_from_history_filter_branch.sh
./remove_scrap_from_history_filter_branch.sh
```

### Or run commands manually

```bash
# 1. Remove scrap/ from history
git filter-branch --force --index-filter \
    'git rm -rf --cached --ignore-unmatch scrap/' \
    --prune-empty --tag-name-filter cat -- --all

# 2. Clean up backup refs
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 3. Force push
git push origin --force --all
git push origin --force --tags
```

## Method 3: Using BFG Repo-Cleaner (Fastest)

BFG is the fastest tool for removing large files/folders.

### Installation

```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Or via Homebrew (Mac/Linux)
brew install bfg
```

### Usage

```bash
# 1. Clone a fresh mirror
git clone --mirror https://github.com/SOELexicon/clickup_framework.git

# 2. Run BFG
java -jar bfg-1.14.0.jar --delete-folders scrap clickup_framework.git
# Or if installed via brew: bfg --delete-folders scrap clickup_framework.git

# 3. Clean up
cd clickup_framework.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. Push
git push --force
```

## After Rewriting History

### Verify the changes

```bash
# Check that scrap/ is gone from history
git log --all --oneline -- scrap/
# Should return no results

# Check repository size reduction
du -sh .git
```

### For team members

Everyone who has cloned the repository needs to either:

**Option A: Re-clone (Recommended)**
```bash
cd ..
rm -rf clickup_framework
git clone https://github.com/SOELexicon/clickup_framework.git
cd clickup_framework
```

**Option B: Reset existing repository**
```bash
# ⚠️ WARNING: This will delete any uncommitted work!
git fetch origin
git reset --hard origin/main  # or origin/master
git clean -fdx
git pull --rebase
```

## Troubleshooting

### "refusing to update checked out branch"

You're trying to push while on that branch. Solution:
```bash
git checkout -b temp-branch
git push origin --force --all
```

### "remote: error: denying non-fast-forward"

You need to force push:
```bash
git push origin --force --all
```

### "cannot lock ref 'refs/remotes/origin/...'"

Delete the problematic remote branches:
```bash
git remote prune origin
git fetch origin
```

## Rollback (If something goes wrong)

```bash
# Stop everything and restore from backup
cd ..
rm -rf clickup_framework
mv clickup_framework_backup clickup_framework
cd clickup_framework
```

## Expected Results

- **Before:** `scrap/` folder exists in git history (all commits)
- **After:** `scrap/` folder completely removed from history
- **Space saved:** Approximately 100-200 MB (depending on the size of scrap/)
- **Commit SHAs:** All commits will have new SHA hashes
- **Tags:** All tags remain but point to new commit SHAs

## Size Comparison

Check before and after:

```bash
# Before
du -sh .git
# Example: 450M

# After
du -sh .git
# Example: 250M (saved ~200M)
```

## Additional Resources

- [git-filter-repo documentation](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [Git filter-branch manual](https://git-scm.com/docs/git-filter-branch)
