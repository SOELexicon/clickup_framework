# Archived Scripts

This directory contains scripts that are no longer actively used but are kept for reference.

## post_commits_to_clickup.py

**Status:** Archived (replaced by report_test_failures_to_clickup.py)
**Date Archived:** 2025-11-12

### Why Archived

This script automatically created ClickUp tasks for every commit pushed to the repository. This approach was replaced with a more targeted system that only creates bug report tasks when tests fail, reducing noise and focusing on actionable items.

### Replacement

See `scripts/report_test_failures_to_clickup.py` which:
- Only creates tasks for test failures
- Tags bugs with the specific command and args that failed
- Provides detailed error information and reproduction steps
- Creates tasks with proper bug report formatting

### Historical Context

The original script was designed to track all development activity in ClickUp by creating:
- Branch container tasks
- Commit subtasks under each branch
- Automatic commit categorization with emojis

While comprehensive, this created many tasks that didn't require action. The new approach focuses only on failures that need investigation and fixing.

### If You Need to Re-enable

To re-enable commit posting (not recommended):

1. Move script back to scripts directory
2. Re-add the `post-commits` job to `.github/workflows/ci.yml`
3. Ensure `CLICKUP_API_TOKEN` secret is configured

However, consider whether you really need this versus the test failure reporting system.
