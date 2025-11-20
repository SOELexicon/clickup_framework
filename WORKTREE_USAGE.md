# Git Worktree Setup for File Editing

## Problem
When editing files in the main directory, VSCode or other tools may lock files, preventing the Edit tool from working.

## Solution
Use a git worktree for all file editing operations.

## Setup
```bash
# Create the edit worktree (already done)
git worktree add -b edit ../clickup_framework_edit

# View worktrees
git worktree list
```

## File Editing Workflow

### For Claude Code (automated)
1. Read files from: `E:/Projects/clickup_framework_edit/...`
2. Edit files in: `E:/Projects/clickup_framework_edit/...`
3. Commit in edit worktree
4. Merge back to master

### Using Helper Script
```bash
# Check status of both worktrees
./worktree_helper.sh status

# Sync edit branch with latest master
./worktree_helper.sh sync

# Commit changes in edit worktree
./worktree_helper.sh commit "Your commit message"

# Merge edit changes back to master
./worktree_helper.sh merge
```

## Manual Workflow
```bash
# Work in edit directory
cd ../clickup_framework_edit

# Make changes, commit
git add -A
git commit -m "Your changes"

# Switch to main directory
cd ../clickup_framework

# Merge changes
git merge edit
git push
```

## Cleanup
```bash
# When done with worktree
git worktree remove ../clickup_framework_edit
git branch -d edit
```

## Benefits
- No file lock conflicts with IDEs
- Separate working directory for edits
- Can commit/test in isolation
- Easy to merge back to master
