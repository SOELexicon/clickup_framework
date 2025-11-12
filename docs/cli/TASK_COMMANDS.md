# Task Management Commands

Commands for creating, updating, deleting, and managing tasks.

**[← Back to Index](INDEX.md)**

---

## Commands Overview

| Command | Shortcode | Description |
|---------|-----------|-------------|
| [`task_create`](#task_create) | `tc` | Create new task |
| [`task_update`](#task_update) | `tu` | Update task properties |
| [`task_delete`](#task_delete) | `td` | Delete task |
| [`task_assign`](#task_assign) | `ta` | Assign users to task |
| [`task_unassign`](#task_unassign) | `tua` | Remove assignees from task |
| [`task_set_status`](#task_set_status) | `tss` | Set task status (validates subtasks) |
| [`task_set_priority`](#task_set_priority) | `tsp` | Set task priority |
| [`task_set_tags`](#task_set_tags) | `tst` | Manage task tags |
| [`task_add_dependency`](#task_add_dependency) | `tad` | Add dependency relationship |
| [`task_remove_dependency`](#task_remove_dependency) | `trd` | Remove dependency relationship |
| [`task_add_link`](#task_add_link) | `tal` | Link two tasks together |
| [`task_remove_link`](#task_remove_link) | `trl` | Remove link between tasks |

---

## task_create

**Shortcode:** `tc`

Create a new task in a list or as a subtask.

### Usage

```bash
cum task_create <name> [options]
cum tc <name> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Task name/title |

### Options

| Option | Description |
|--------|-------------|
| `--list LIST_ID\|current` | List ID (required unless --parent is used) |
| `--parent TASK_ID` | Parent task ID (creates subtask) |
| `--description TEXT` | Task description (plain text) |
| `--description-file PATH` | Read description from file (supports markdown) |
| `--status STATUS` | Initial status (with smart mapping) |
| `--priority 1-4\|urgent\|high\|normal\|low` | Task priority |
| `--tags TAG [TAG...]` | Tags to add |
| `--assignees USER_ID [USER_ID...]` | Assign users (defaults to context assignee) |
| `--checklist-template NAME` | Apply checklist template |
| `--clone-checklists-from TASK_ID` | Clone checklists from another task |
| `--custom-task-ids` | Use custom task IDs |
| `--check-required-custom-fields` | Validate required custom fields (default: true) |

**Note:** `--description` and `--description-file` are mutually exclusive.

### Examples

```bash
# Basic task creation
cum tc "New feature" --list current

# With description file (markdown supported!)
cum tc "API Documentation" --list current --description-file spec.md

# Create subtask
cum tc "Implement login" --parent 86c6xyz

# With priority and tags
cum tc "Fix bug" --list current --priority urgent --tags bug critical

# With assignees
cum tc "Code review" --list current --assignees 68483025 68483026

# Auto-assign to default assignee
cum set assignee 68483025
cum tc "Task" --list current  # Auto-assigned

# With status
cum tc "New task" --list current --status "in progress"

# With checklist template
cum tc "Deployment" --list current --checklist-template "deployment-checklist"

# Clone checklists from existing task
cum tc "Similar task" --list current --clone-checklists-from 86c6abc
```

[→ Full task_create command details](commands/task_create.md)

---

## task_update

**Shortcode:** `tu`

Update task properties.

### Usage

```bash
cum task_update <task_id> [options]
cum tu <task_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |

### Options

| Option | Description |
|--------|-------------|
| `--name TEXT` | New task name |
| `--description TEXT` | New description (plain text) |
| `--description-file PATH` | Read description from file |
| `--status STATUS` | New status |
| `--priority 1-4\|urgent\|high\|normal\|low` | New priority |
| `--parent TASK_ID` | New parent task |
| `--add-tags TAG [TAG...]` | Add tags |
| `--remove-tags TAG [TAG...]` | Remove tags |

**Note:** `--description` and `--description-file` are mutually exclusive.

### Examples

```bash
# Update task name
cum tu 86c6xyz --name "Updated task name"

# Update description from file
cum tu current --description-file updated_spec.md

# Update status
cum tu 86c6xyz --status "in progress"

# Update priority
cum tu current --priority urgent

# Change parent (move subtask)
cum tu 86c6xyz --parent 86c6abc

# Add tags
cum tu current --add-tags feature backend

# Remove tags
cum tu 86c6xyz --remove-tags deprecated

# Multiple updates
cum tu current --name "New name" --priority high --add-tags urgent
```

[→ Full task_update command details](commands/task_update.md)

---

## task_delete

**Shortcode:** `td`

Delete a task with confirmation prompt.

### Usage

```bash
cum task_delete <task_id> [options]
cum td <task_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |

### Options

| Option | Description |
|--------|-------------|
| `--force` | Skip confirmation prompt |

### Examples

```bash
# Delete with confirmation
cum td 86c6xyz

# Delete without confirmation
cum task_delete 86c6xyz --force

# Delete current task
cum td current
```

**Warning:** Deletion is permanent and cannot be undone!

[→ Full task_delete command details](commands/task_delete.md)

---

## task_assign

**Shortcode:** `ta`

Assign one or more users to a task.

### Usage

```bash
cum task_assign <task_id> <user_id> [user_id...]
cum ta <task_id> <user_id> [user_id...]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |
| `user_id` | Yes | One or more user IDs to assign |

### Examples

```bash
# Assign single user
cum ta 86c6xyz 68483025

# Assign multiple users
cum task_assign current 68483025 68483026 68483027

# Assign to current task
cum ta current 68483025
```

[→ Full task_assign command details](commands/task_assign.md)

---

## task_unassign

**Shortcode:** `tua`

Remove assignees from a task.

### Usage

```bash
cum task_unassign <task_id> <user_id> [user_id...]
cum tua <task_id> <user_id> [user_id...]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |
| `user_id` | Yes | One or more user IDs to remove |

### Examples

```bash
# Unassign single user
cum tua 86c6xyz 68483025

# Unassign multiple users
cum task_unassign current 68483025 68483026
```

[→ Full task_unassign command details](commands/task_unassign.md)

---

## task_set_status

**Shortcode:** `tss`

Set task status with subtask validation.

### Usage

```bash
cum task_set_status <task_id> [task_id...] <status>
cum tss <task_id> [task_id...] <status>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | One or more task IDs |
| `status` | Yes | Status to set (last argument) |

### Features

- **Subtask validation:** Prevents closing parent tasks with open subtasks
- **Smart status mapping:** Automatically maps common status names
- **Bulk operations:** Update multiple tasks at once

### Examples

```bash
# Set single task status
cum tss 86c6xyz "in progress"

# Set status for multiple tasks
cum task_set_status 86c6xyz 86c6abc 86c6def "done"

# Use current task
cum tss current "in review"

# Smart status mapping
cum tss current done
cum tss current open
cum tss current progress
```

[→ Full task_set_status command details](commands/task_set_status.md)

---

## task_set_priority

**Shortcode:** `tsp`

Set task priority.

### Usage

```bash
cum task_set_priority <task_id> <priority>
cum tsp <task_id> <priority>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |
| `priority` | Yes | Priority value (1-4 or name) |

### Priority Values

| Number | Name | Usage |
|--------|------|-------|
| `1` | `urgent` | Highest priority |
| `2` | `high` | High priority |
| `3` | `normal` | Normal priority |
| `4` | `low` | Low priority |

### Examples

```bash
# Set using number
cum tsp 86c6xyz 1

# Set using name
cum task_set_priority current urgent

# Other priorities
cum tsp 86c6xyz high
cum tsp current normal
cum tsp 86c6xyz low
```

[→ Full task_set_priority command details](commands/task_set_priority.md)

---

## task_set_tags

**Shortcode:** `tst`

Manage task tags (add, remove, or replace).

### Usage

```bash
cum task_set_tags <task_id> <operation> <tag> [tag...]
cum tst <task_id> <operation> <tag> [tag...]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |

### Operations

| Operation | Description |
|-----------|-------------|
| `--add TAG [TAG...]` | Add tags to existing tags |
| `--remove TAG [TAG...]` | Remove specific tags |
| `--set TAG [TAG...]` | Replace all tags |

### Examples

```bash
# Add tags
cum tst 86c6xyz --add bug critical

# Remove tags
cum task_set_tags current --remove deprecated

# Replace all tags
cum tst 86c6xyz --set feature backend api

# Add multiple tags
cum tst current --add urgent needs-review high-priority
```

[→ Full task_set_tags command details](commands/task_set_tags.md)

---

## task_add_dependency

**Shortcode:** `tad`

Add task dependency relationship.

### Usage

```bash
cum task_add_dependency <task_id> <operation> <other_task_id>
cum tad <task_id> <operation> <other_task_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |

### Operations

| Operation | Description |
|-----------|-------------|
| `--waiting-on TASK_ID` | This task waits on another task to complete |
| `--blocking TASK_ID` | This task blocks another task |

### Examples

```bash
# Task 86c6xyz waits on 86c6abc to complete
cum tad 86c6xyz --waiting-on 86c6abc

# Task current blocks 86c6xyz
cum task_add_dependency current --blocking 86c6xyz

# Create dependency chain
cum tad task1 --blocking task2
cum tad task2 --blocking task3
```

**Note:** Dependencies are used by the `assigned` command to sort tasks by difficulty.

[→ Full task_add_dependency command details](commands/task_add_dependency.md)

---

## task_remove_dependency

**Shortcode:** `trd`

Remove task dependency relationship.

### Usage

```bash
cum task_remove_dependency <task_id> <operation> <other_task_id>
cum trd <task_id> <operation> <other_task_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |

### Operations

| Operation | Description |
|-----------|-------------|
| `--waiting-on TASK_ID` | Remove waiting-on relationship |
| `--blocking TASK_ID` | Remove blocking relationship |

### Examples

```bash
# Remove waiting-on dependency
cum trd 86c6xyz --waiting-on 86c6abc

# Remove blocking dependency
cum task_remove_dependency current --blocking 86c6xyz
```

[→ Full task_remove_dependency command details](commands/task_remove_dependency.md)

---

## task_add_link

**Shortcode:** `tal`

Link two tasks together (general relationship, not dependency).

### Usage

```bash
cum task_add_link <task_id> <linked_task_id>
cum tal <task_id> <linked_task_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |
| `linked_task_id` | Yes | Task ID to link to |

### Examples

```bash
# Link two tasks
cum tal 86c6xyz 86c6abc

# Link to current task
cum task_add_link current 86c6xyz
```

**Difference from dependencies:** Links are general relationships, while dependencies indicate blocking/waiting relationships.

[→ Full task_add_link command details](commands/task_add_link.md)

---

## task_remove_link

**Shortcode:** `trl`

Remove link between two tasks.

### Usage

```bash
cum task_remove_link <task_id> <linked_task_id>
cum trl <task_id> <linked_task_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | Task ID or `current` |
| `linked_task_id` | Yes | Task ID to unlink from |

### Examples

```bash
# Remove link
cum trl 86c6xyz 86c6abc

# Remove link from current task
cum task_remove_link current 86c6xyz
```

[→ Full task_remove_link command details](commands/task_remove_link.md)

---

## Common Workflows

### Create and Manage Task

```bash
# Create task with context
cum set list 901517404278
cum set assignee 68483025

# Create task (auto-assigned)
cum tc "Implement feature X" --priority high --tags feature backend

# Update task
cum tu current --description-file spec.md

# Set status
cum tss current "in progress"

# Add dependency
cum tad current --waiting-on 86c6abc

# Complete task
cum tss current "done"
```

### Bulk Task Operations

```bash
# Set status for multiple tasks
cum tss 86c6xyz 86c6abc 86c6def "in review"

# Tag multiple related tasks
for task in task1 task2 task3; do
  cum tst $task --add sprint-5 backend
done
```

### Subtask Creation

```bash
# Create parent task
cum tc "Major Feature" --list current
# Returns: 86c6parent

# Create subtasks
cum tc "Design API" --parent 86c6parent --priority high
cum tc "Implement backend" --parent 86c6parent --priority normal
cum tc "Write tests" --parent 86c6parent --priority normal
cum tc "Documentation" --parent 86c6parent --priority low
```

---

## Tips

1. **Use context:** Set default assignee to auto-assign tasks: `cum set assignee YOUR_USER_ID`
2. **Markdown descriptions:** Use `--description-file` with `.md` files for rich formatting
3. **Checklist templates:** Save time with reusable checklist templates
4. **Dependency tracking:** Use dependencies to help prioritize work with `cum assigned`
5. **Smart status:** Common status names are automatically mapped (e.g., "done" → "closed")

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [← View Commands](VIEW_COMMANDS.md)
- [Comment Commands →](COMMENT_COMMANDS.md)
