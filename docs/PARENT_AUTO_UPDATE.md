# Parent Task Auto-Update Feature

## Overview

The Parent Task Auto-Update feature automatically updates parent task status when a subtask transitions to an active development state. This eliminates the need for manual parent task updates and ensures task hierarchy accurately reflects current work state in real-time.

## How It Works

When you set a subtask status to "in progress" (or similar development status), the system automatically:

1. Detects that the task is a subtask (has a parent)
2. Checks if the new status is a "development" status (e.g., "in progress", "in dev", "active")
3. Checks if the parent task is in an "inactive" status (e.g., "to do", "backlog")
4. Updates the parent task to "in progress"
5. Optionally posts a comment on the parent task documenting the change

## Usage

### Basic Usage

The automation is **enabled by default** and works automatically:

```bash
# Set a subtask to "in progress" - parent task will be auto-updated
clickup task_set_status <subtask_id> "in progress"

# Output:
# ✓ Status updated
#
# Task: Implement Login API [sub123]
# New status: in progress
#
# 🔄 Auto-Update: Parent task updated
#   Task: Authentication System [parent123]
#   Status: to do → in progress
#   Latency: 1847ms
```

### Skipping Automation

Use the `--no-parent-update` flag to skip automation for a specific update:

```bash
clickup task_set_status <subtask_id> "in progress" --no-parent-update
```

### Forcing Automation

Use the `--update-parent` flag to force parent update even if automation is globally disabled:

```bash
clickup task_set_status <subtask_id> "in progress" --update-parent
```

### Custom Parent Comment

Use the `--parent-comment` flag to post a custom comment on the parent task:

```bash
clickup task_set_status <subtask_id> "in progress" --parent-comment "Started API implementation"
```

## Configuration

### Check Current Configuration

```bash
clickup parent_auto_update status
```

Output:
```
Parent Task Auto-Update Configuration
==================================================

Status: ✅ Enabled
Post Comments: ✅ Yes
Update Delay: 2 seconds
Retry on Failure: ✅ Yes (max 3 attempts)

Trigger Statuses (6):
  • in progress
  • in development
  • in dev
  • active
  • working
  • started

Parent Inactive Statuses (7):
  • to do
  • todo
  • backlog
  • not started
  • open
  • ready
  • planned

Target Status for Parent: "in progress"
```

### Enable/Disable Automation

```bash
# Disable automation globally
clickup parent_auto_update disable

# Enable automation globally
clickup parent_auto_update enable
```

### Update Configuration Values

```bash
# Disable comment posting
clickup parent_auto_update config post_comment false

# Change target status for parent
clickup parent_auto_update config parent_target_status "In Development"

# Change max retries
clickup parent_auto_update config max_retries 5
```

### Manage Trigger Statuses

Add or remove statuses that trigger parent updates:

```bash
# Add a custom status to trigger list
clickup parent_auto_update add-trigger "doing"

# Remove a status from trigger list
clickup parent_auto_update remove-trigger "started"

# List all trigger statuses
clickup parent_auto_update list-triggers
```

## Configuration File

Configuration is stored in `~/.clickup/automation_config.json`:

```json
{
  "automation": {
    "parent_update": {
      "enabled": true,
      "post_comment": true,
      "comment_template": "🤖 **Automated Update:** Status changed to '{new_status}' because subtask '{subtask_name}' started development.",
      "trigger_statuses": [
        "in progress",
        "in development",
        "in dev",
        "active",
        "working",
        "started"
      ],
      "parent_inactive_statuses": [
        "to do",
        "todo",
        "backlog",
        "not started",
        "open",
        "ready",
        "planned"
      ],
      "parent_target_status": "in progress",
      "update_delay_seconds": 2,
      "retry_on_failure": true,
      "max_retries": 3,
      "log_automation_events": true,
      "verbose_output": false
    }
  }
}
```

## Behavior Details

### When Automation Triggers

Automation triggers when ALL of these conditions are met:

1. **Automation is enabled** (globally or via `--update-parent` flag)
2. **Task is a subtask** (has a parent task)
3. **New status is in trigger list** (e.g., "in progress")
4. **Parent status is inactive** (e.g., "to do", "backlog")

### When Automation is Skipped

Automation is skipped when:

- Parent task is already in an active state ("in progress", "blocked", etc.)
- Automation is disabled and `--update-parent` flag is not used
- `--no-parent-update` flag is used
- Task has no parent

### Multiple Subtasks

When updating multiple subtasks of the same parent:

```bash
clickup task_set_status sub1 sub2 sub3 "in progress"

# Output:
# ✓ Status updated: Subtask 1
# 🔄 Auto-Update: Parent task updated
#
# ✓ Status updated: Subtask 2
# ℹ️  Parent already updated (skipped for this subtask)
#
# ✓ Status updated: Subtask 3
# ℹ️  Parent already updated (skipped for this subtask)
```

The parent is only updated once, not three times (batching).

### Error Handling

If parent update fails, the subtask update still succeeds:

```bash
# Output:
# ✓ Status updated: Implement Login API [sub123]
# New status: in progress
#
# ⚠️  Warning: Automatic parent update failed
#   Parent task: Authentication System [parent123]
#   Error: ClickUp API Error: Rate limit exceeded (429)
#   → You may need to manually update the parent task
```

Errors are logged but don't block your workflow.

## Examples

### Example 1: Standard Workflow

```bash
# Create a parent task
clickup task_create --list current "Build Authentication System" --status "to do"
# Created: Build Authentication System [parent123]

# Create a subtask
clickup task_create --list current "Implement Login API" --parent parent123 --status "to do"
# Created: Implement Login API [sub456]

# Start work on subtask - parent auto-updates
clickup task_set_status sub456 "in progress"
# ✓ Status updated: Implement Login API
# 🔄 Auto-Update: Parent task updated (to do → in progress)
```

### Example 2: Disable Automation Temporarily

```bash
# Disable automation for this specific update
clickup task_set_status sub456 "in progress" --no-parent-update

# Parent task remains in "to do" state
# You can manually update it later if needed
clickup task_set_status parent123 "in progress"
```

### Example 3: Custom Status Names

If your workspace uses custom status names:

```bash
# Add your custom status to trigger list
clickup parent_auto_update add-trigger "In Development"
clickup parent_auto_update add-trigger "🚀 Active"

# Now these statuses will trigger automation
clickup task_set_status sub456 "In Development"
# 🔄 Auto-Update: Parent task updated
```

## Troubleshooting

### Automation Not Working

1. **Check if automation is enabled:**
   ```bash
   clickup parent_auto_update status
   ```

2. **Verify status is in trigger list:**
   ```bash
   clickup parent_auto_update list-triggers
   ```

3. **Check if parent is already active:**
   - If parent status is already "in progress", automation is skipped

4. **Enable verbose logging:**
   ```bash
   clickup parent_auto_update config log_automation_events true
   ```

### Parent Not Updating

If parent task is not updating:

- Ensure the status you're setting is in the trigger list
- Confirm the parent's current status is in the inactive list
- Check that automation is enabled globally
- Try force update: `--update-parent` flag

### Unwanted Updates

If automation is updating parents when you don't want it to:

- Disable globally: `clickup parent_auto_update disable`
- Use `--no-parent-update` flag on specific commands
- Remove statuses from trigger list

## Best Practices

1. **Use Default Configuration**: The default configuration works for most teams

2. **Customize Trigger Statuses**: Add your workspace's custom status names to the trigger list

3. **Review Parent Comments**: Enable `post_comment` to maintain an audit trail

4. **Handle Errors Gracefully**: If automation fails, manually update the parent task

5. **Batch Multiple Subtasks**: Update multiple subtasks at once to minimize parent updates

6. **Test Configuration**: Use a test list to verify automation behavior before deploying to production

## FAQ

**Q: Does automation work for grandparent tasks?**
A: No, currently only direct parent tasks are updated. Grandparent updates may be added in a future version.

**Q: Can I use different target statuses for different lists?**
A: Not currently. Per-list configuration overrides are planned for a future release.

**Q: What happens if I update a parent task manually?**
A: Manual updates take precedence. Automation will skip updating if the parent is already in an active state.

**Q: Does automation work when updating tasks via the web UI?**
A: No, automation only works when using the CLI `task_set_status` command.

**Q: How do I completely disable automation?**
A: Run `clickup parent_auto_update disable`

**Q: Can I customize the comment template?**
A: Yes, by editing the configuration file at `~/.clickup/automation_config.json`

## Support

For issues or feature requests related to parent task automation:

1. Check the troubleshooting section above
2. Review your configuration with `clickup parent_auto_update status`
3. Open an issue on the GitHub repository with automation logs

## Version History

- **v1.0.0** (2025-11-11): Initial release with core automation features
  - Automatic parent status updates
  - Configurable trigger statuses
  - Optional comment posting
  - Retry logic and error handling
  - Management command for configuration
