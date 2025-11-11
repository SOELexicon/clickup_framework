---
description: Guide for ClickUp + Git workflow - when and where to use commands
---

# ClickUp + Git Workflow Guide

This guide shows the recommended workflow for using ClickUp commands (`cum`) alongside Git.

## Starting a Task

1. **View your assigned tasks:**
   ```bash
   cum a
   ```

2. **Set current task:**
   ```bash
   cum set task <task_id>
   ```

3. **View task details:**
   ```bash
   cum d <task_id>
   ```

4. **Update task status to "In Development":**
   ```bash
   cum tss <task_id> "In Development"
   ```

## During Development

### Managing Dependencies

If your task depends on other tasks:

```bash
# Make current task wait for another task
cum tad current --waiting-on <other_task_id>

# Make current task block another task
cum tad current --blocking <blocked_task_id>
```

### Linking Related Tasks

```bash
# Link related tasks together
cum tal current <related_task_id>
```

### Adding Comments

```bash
# Add progress updates
cum ca current "Started working on feature X"
```

### Viewing Context

```bash
# Check your current context
cum show
```

## Git Workflow

### Creating Commits

1. **Make your changes**
2. **Stage and commit:**
   ```bash
   git add .
   git commit -m "Descriptive message"
   ```

3. **Add comment to ClickUp task:**
   ```bash
   cum ca current "Committed: <commit_message>"
   ```

### Pushing Changes

```bash
# Push to remote
git push -u origin <branch-name>
```

## Completing a Task

1. **Run tests (if applicable)**
2. **Update subtasks if any:**
   ```bash
   cum tss <subtask_id> "Complete"
   ```

3. **Update main task:**
   ```bash
   cum tss current "Complete"
   ```

4. **Add final comment:**
   ```bash
   cum ca current "Task completed and pushed to branch <branch-name>"
   ```

5. **Create PR if needed:**
   ```bash
   gh pr create --title "Title" --body "Description"
   ```

## Common Command Aliases

| Command | Alias | Description |
|---------|-------|-------------|
| `assigned` | `a` | View assigned tasks |
| `detail` | `d` | View task details |
| `set_current` | `set` | Set current context |
| `show_current` | `show` | Show current context |
| `task_set_status` | `tss` | Set task status |
| `task_create` | `tc` | Create new task |
| `task_update` | `tu` | Update task |
| `task_add_dependency` | `tad` | Add dependency |
| `task_remove_dependency` | `trd` | Remove dependency |
| `task_add_link` | `tal` | Link tasks |
| `task_remove_link` | `trl` | Unlink tasks |
| `comment_add` | `ca` | Add comment |
| `comment_list` | `cl` | List comments |

## Quick Examples

### Example 1: Starting a new task
```bash
# View assigned tasks
cum a

# Set current task
cum set task 86c6e0q12

# Update status
cum tss current "In Development"

# Add initial comment
cum ca current "Starting work on this task"
```

### Example 2: Completing with dependencies
```bash
# Mark dependency complete
cum tss 86c6e0q16 "Complete"

# Remove dependency
cum trd current --waiting-on 86c6e0q16

# Mark current task complete
cum tss current "Complete"
```

### Example 3: Creating a subtask
```bash
# Create subtask with parent (no --list needed)
cum tc "Subtask name" --parent <parent_task_id> --status "In Development"
```

## Pro Tips

1. **Always use `cum show`** to verify your current context before running commands with "current"
2. **Use `cum d <task_id>`** to see dependencies and relationships before modifying them
3. **Add comments frequently** to track progress: `cum ca current "message"`
4. **Use dependencies** (`cum tad`) to enforce task order and prevent premature status changes
5. **Use links** (`cum tal`) for related tasks that don't have strict ordering

---

For more help on any command: `cum <command> --help`
