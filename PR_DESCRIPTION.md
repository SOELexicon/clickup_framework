# PR: Centralize config storage to ~/.cum directory (v2)

## Summary

This PR re-introduces centralized configuration storage to the `~/.cum/` directory with improved error handling and additional enhancements.

## Changes

### 1. Centralized Config Storage
- **Location:** `~/.cum/clickup_context.json` (previously `~/.clickup_context.json`)
- **Cross-platform:** Works on Windows, Linux, and macOS
- **Security:** Maintains 0600 file permissions on Unix-like systems

### 2. Robust Error Handling
- **File Conflict Detection:** Detects if `~/.cum` exists as a file (not directory) and provides clear error message
- **Permission Issues:** Catches and reports OSError for directory creation failures
- **Better Diagnostics:** Helps users troubleshoot configuration path issues

### 3. Task Workflow Guide
- **New Documentation:** `docs/TASK_WORKFLOW_GUIDE.md`
- **Comprehensive Coverage:**
  - Starting tasks (when to update status, leave comments)
  - Working on tasks (progress updates, milestone comments)
  - Completing tasks (handling subtasks, completion criteria)
  - Status management best practices
  - Comment guidelines (when to comment vs when not to)
  - Subtask handling (5 common scenarios)
- **Quick Reference:** Command snippets for common workflows
- **Git Integration:** Example workflow combining git + ClickUp

### 4. Bug Fix: `assigned` Command
- **Issue:** Used non-existent `get_workspaces()` method
- **Fix:** Changed to `get_authorized_workspaces()`
- **Impact:** Command now works correctly for workspace selection

## Testing

- ✅ Tested on Linux (Ubuntu)
- ✅ Confirmed directory creation works correctly
- ✅ Verified file permissions (0600)
- ✅ Tested error handling for edge cases
- ✅ Confirmed Windows path compatibility (user verified: `C:\Users\craig\.cum`)

## Why This Version is Better

The previous PR (#28) was reverted due to issues. This version includes:

1. **Better error handling** - Won't crash silently if directory creation fails
2. **Clear error messages** - Users know exactly what went wrong
3. **Additional fixes** - Fixed the `assigned` command bug
4. **Better documentation** - Added comprehensive workflow guide

## Breaking Changes

**Config file location changes:**
- Old: `~/.clickup_context.json`
- New: `~/.cum/clickup_context.json`

Users will need to either:
- Manually move their config file, or
- Re-configure their settings (workspace, assignee, etc.)

## Files Changed

- `clickup_framework/context.py` - Config path + error handling
- `clickup_framework/cli.py` - Fixed `assigned` command
- `README.md` - Updated config path references
- `CLICKUP.md` - Updated config path references
- `docs/TASK_WORKFLOW_GUIDE.md` - New workflow guide (NEW)

## Commits

1. Add comprehensive task workflow guide
2. Fix assigned command: use correct method name
3. Add robust error handling for config directory creation

## Related Issues

- Fixes the issue that caused PR #28 to be reverted
- Resolves `assigned` command error: "'ClickUpClient' object has no attribute 'get_workspaces'"
