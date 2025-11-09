# task_update - Update Existing Tasks

## Description

Update one or more fields of an existing task. Allows modification of name, description, status, priority, and tags.

## Command Signature

```bash
clickup task_update <task_id> [OPTIONS]
```

## Arguments

### Required
- `task_id` - The ID of the task to update (or "current" if context is set)

### Optional
- `--name TEXT` - New task name
- `--description TEXT` - New task description
- `--status TEXT` - New status (must be valid for the list)
- `--priority INT` - New priority (1-4)
- `--add-tags TAG [TAG ...]` - Tags to add to existing tags
- `--remove-tags TAG [TAG ...]` - Tags to remove from existing tags

## Examples

### Update Task Name
```bash
clickup task_update 86c6e0xyz --name "Updated Task Name"
```

### Update Multiple Fields
```bash
clickup task_update 86c6e0xyz \
  --name "Refactor Authentication" \
  --description "Complete refactor of auth system" \
  --status "in development" \
  --priority 1
```

### Manage Tags
```bash
# Add tags
clickup task_update 86c6e0xyz --add-tags "urgent" "backend"

# Remove tags
clickup task_update 86c6e0xyz --remove-tags "wont fix"

# Add and remove in same command (use separate calls)
clickup task_update 86c6e0xyz --add-tags "reviewed"
clickup task_update 86c6e0xyz --remove-tags "needs-review"
```

### Using Context
```bash
# Set current task
clickup set_current task 86c6e0xyz

# Update current task
clickup task_update current --status "testing"
```

## Output

### Success
```
✓ Task updated: Refactor Authentication

Updated fields:
  name: Refactor Authentication
  description: Complete refactor of auth system
  status: in development
  priority: 1
```

### Error
```
Error updating task: ClickUp API Error 404: Task not found
```

## Implementation Status

✅ **Implemented** - Available in CLI

## Related Commands

- `task_create` - Create new tasks
- `task_set_status` - Quick status updates with validation
- `task_set_priority` - Quick priority updates
- `task_set_tags` - Advanced tag management

## API Endpoint

`PUT /task/{task_id}`

## Notes

- At least one update option must be provided
- Tags operations (add/remove) require fetching current task state first
- Status must exist in the task's list workflow
- Priority values: 1 (Urgent), 2 (High), 3 (Normal), 4 (Low)
- All updates are atomic - either all succeed or none apply

## Validation

- ✓ Task must exist
- ✓ Status must be valid for the list (if provided)
- ✓ Priority must be 1-4 (if provided)
- ✗ No subtask validation (use task_set_status for validated status changes)
