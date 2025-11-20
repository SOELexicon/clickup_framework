#!/bin/bash
# Git worktree helper for avoiding file lock issues

MAIN_DIR="/e/Projects/clickup_framework"
EDIT_DIR="/e/Projects/clickup_framework_edit"

# Function to sync edit branch with master
sync_edit() {
    cd "$EDIT_DIR"
    git fetch origin master:master
    git rebase master
    echo "Edit branch synced with master"
}

# Function to merge changes back to master
merge_to_master() {
    cd "$MAIN_DIR"
    git merge edit --no-ff -m "Merge edits from worktree"
    git push
    echo "Changes merged to master and pushed"
}

# Function to commit in edit worktree
commit_edit() {
    cd "$EDIT_DIR"
    git add -A
    git commit -m "$1"
    echo "Changes committed to edit branch"
}

# Function to show status
status() {
    echo "=== Main (master) ==="
    cd "$MAIN_DIR" && git status -s
    echo ""
    echo "=== Edit worktree ==="
    cd "$EDIT_DIR" && git status -s
}

# Main command dispatcher
case "$1" in
    sync)
        sync_edit
        ;;
    commit)
        commit_edit "$2"
        ;;
    merge)
        merge_to_master
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {sync|commit|merge|status}"
        echo "  sync   - Sync edit branch with master"
        echo "  commit - Commit changes in edit worktree (requires message)"
        echo "  merge  - Merge edit branch back to master"
        echo "  status - Show status of both worktrees"
        exit 1
        ;;
esac
