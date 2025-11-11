# task_create - Create New Tasks

## Description

Create a new task in a specified list with comprehensive options for initial configuration.

## Command Signature

```bash
clickup task_create "<task_name>" [--list LIST_ID] [--parent PARENT_ID] [OPTIONS]
```

## Arguments

### Required
- `task_name` - The name/title of the task

### Optional
- `--list LIST_ID` - The ID of the list to create the task in (or "current" if context is set). **Not required if --parent is provided** - the list will be automatically determined from the parent task.
- `--parent ID` - Parent task ID (creates this as a subtask). When provided, the list ID is automatically fetched from the parent task.
- `--description TEXT` - Detailed description of the task (text)
- `--description-file PATH` - Detailed description of the task (from file - supports markdown!)
- `--status TEXT` - Initial status (must be valid for the list)
- `--priority {1|2|3|4|urgent|high|normal|low}` - Priority level (number or name string)
  - Numbers: 1=Urgent, 2=High, 3=Normal, 4=Low
  - Strings: urgent, high, normal, low (case-insensitive)
- `--tags TAG [TAG ...]` - One or more tags to add to the task
- `--assignees ID [ID ...]` - User IDs to assign to the task
- `--custom-task-ids` - Enable custom task IDs (requires workspace setting)
- `--check-required-custom-fields true|false` - Check required custom fields (default: true)

**Notes**:
- `--description` and `--description-file` are mutually exclusive
- Description files can be markdown (.md) - ClickUp renders markdown in task descriptions
- Priority accepts both numbers (1-4) and names (urgent/high/normal/low)

## Examples

### Basic Task Creation
```bash
# Create a simple task
clickup task_create "Fix login bug" --list 901517404274

# Create with description
clickup task_create "Implement OAuth" --list 901517404274 \
  --description "Add OAuth 2.0 authentication flow"
```

### Task with Full Options
```bash
# Using priority as number
clickup task_create "API Endpoint Development" --list 901517404274 \
  --description "Create RESTful API endpoints for user management" \
  --status "in development" \
  --priority 1 \
  --tags "backend" "api" "urgent" \
  --assignees 12345678

# Using priority as string (more readable!)
clickup task_create "API Endpoint Development" --list 901517404274 \
  --description-file api_spec.md \
  --status "in development" \
  --priority urgent \
  --tags "backend" "api" \
  --assignees 12345678
```

### Creating a Subtask
```bash
# With parent - no list ID needed! List is automatically determined from parent
clickup task_create "Write unit tests" --parent 86c6e0q0a \
  --status "Open" \
  --priority 2

# Can still specify list if you want to be explicit
clickup task_create "Write unit tests" --list 901517404274 --parent 86c6e0q0a \
  --status "Open" \
  --priority 2
```

### Using Context
```bash
# Set current list
clickup set_current list 901517404274

# Create task in current list
clickup task_create "New Feature Request" --list current
```

### Using File Input for Descriptions
```bash
# Create task with description from markdown file
clickup task_create "Feature: OAuth Integration" --list 901517404274 \
  --description-file oauth_spec.md \
  --priority 1 \
  --tags "feature" "security"

# Useful for longer descriptions or specifications
echo "## Requirements
- Implement OAuth 2.0 flow
- Support Google and GitHub providers
- Add token refresh mechanism" > requirements.md

clickup task_create "OAuth Implementation" --list current \
  --description-file requirements.md
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
- Either `--list` or `--parent` must be provided (or both)
- **When using `--parent`:**
  - The parent task must exist
  - The list ID is automatically fetched from the parent task
  - You don't need to specify `--list` (but you can if you want to be explicit)
  - This makes creating subtasks much easier!
- Status must exist in the target list's workflow
- **Priority values:**
  - **Numbers:** 1 (Urgent), 2 (High), 3 (Normal), 4 (Low)
  - **Strings:** urgent, high, normal, low (case-insensitive)
  - Both forms work identically - use whichever is more readable for your use case
- Assignees must be valid user IDs with access to the workspace
- **Description files:**
  - Use `--description-file` to read descriptions from files
  - **Supports markdown** (.md files) - ClickUp renders markdown in task descriptions
  - Supports headers, lists, code blocks, links, bold, italic, etc.
  - File paths can be absolute or relative to current working directory
  - Files must be readable text files (UTF-8 encoding)
- **Custom task IDs:**
  - Use `--custom-task-ids` if your workspace has custom task ID setting enabled
  - This allows tasks to have custom alphanumeric IDs instead of ClickUp's default IDs
- **Required custom fields:**
  - Use `--check-required-custom-fields false` to skip validation of required custom fields
  - Useful when creating tasks programmatically that will be completed later

## Validation

- ✓ List ID must exist
- ✓ Status must be valid for the list (if provided)
- ✓ Priority must be 1-4 or urgent/high/normal/low (if provided)
- ✓ Priority strings are case-insensitive
- ✓ Parent task must exist (if provided)
- ✓ Assignee IDs must be valid (if provided)
- ✓ Description files must exist and be readable (if provided)

## Examples with Priority Strings

```bash
# Create urgent task with markdown description
cum tc "Critical Security Fix" --list current \
  --description-file security-patch.md \
  --priority urgent \
  --tags security critical

# Create high priority feature with parent (no list needed!)
cum tc "Implement OAuth" --parent 86c6ce9gg \
  --priority high \
  --assignees 12345678

# Create normal priority task (default)
cum tc "Update documentation" --list current \
  --priority normal \
  --tags docs

# Case insensitive priority
cum tc "Low priority cleanup" --list current \
  --priority LOW  # Works just like 'low' or 4
```
