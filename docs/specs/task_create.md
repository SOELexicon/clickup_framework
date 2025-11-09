# task_create - Create New Tasks

## Description

Create a new task in a specified list with comprehensive options for initial configuration.

## Command Signature

```bash
clickup task_create <list_id> "<task_name>" [OPTIONS]
```

## Arguments

### Required
- `list_id` - The ID of the list to create the task in (or "current" if context is set)
- `task_name` - The name/title of the task

### Optional
- `--description TEXT` - Detailed description of the task
- `--status TEXT` - Initial status (must be valid for the list)
- `--priority INT` - Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
- `--tags TAG [TAG ...]` - One or more tags to add to the task
- `--assignees ID [ID ...]` - User IDs to assign to the task
- `--parent ID` - Parent task ID (creates this as a subtask)

## Examples

### Basic Task Creation
```bash
# Create a simple task
clickup task_create 901517404274 "Fix login bug"

# Create with description
clickup task_create 901517404274 "Implement OAuth" \
  --description "Add OAuth 2.0 authentication flow"
```

### Task with Full Options
```bash
clickup task_create 901517404274 "API Endpoint Development" \
  --description "Create RESTful API endpoints for user management" \
  --status "in development" \
  --priority 1 \
  --tags "backend" "api" "urgent" \
  --assignees 12345678
```

### Creating a Subtask
```bash
clickup task_create 901517404274 "Write unit tests" \
  --parent 86c6e0q0a \
  --status "Open" \
  --priority 2
```

### Using Context
```bash
# Set current list
clickup set_current list 901517404274

# Create task in current list
clickup task_create current "New Feature Request"
```

## Output

### Success
```
✓ Task created: API Endpoint Development

Task ID: 86c6e0xyz
URL: https://app.clickup.com/t/86c6e0xyz
```

### Error
```
Error creating task: ClickUp API Error 400: Status does not exist
```

## Implementation Status

✅ **Implemented** - Available in CLI

## Related Commands

- `task_update` - Update existing tasks
- `task_delete` - Delete tasks
- `set_current` - Set current context for list

## API Endpoint

`POST /list/{list_id}/task`

## Notes

- Task name is required and cannot be empty
- Status must exist in the target list's workflow
- Priority values: 1 (Urgent), 2 (High), 3 (Normal), 4 (Low)
- Assignees must be valid user IDs with access to the workspace
- When using `--parent`, the parent task must exist in the same list

## Validation

- ✓ List ID must exist
- ✓ Status must be valid for the list (if provided)
- ✓ Priority must be 1-4 (if provided)
- ✓ Parent task must exist (if provided)
- ✓ Assignee IDs must be valid (if provided)
