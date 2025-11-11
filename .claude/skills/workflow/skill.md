---
name: clickup-workflow
description: Guide for ClickUp + Git workflow - when and where to use commands
tags: [clickup, workflow, git, best-practices]
---

# ClickUp + Git Workflow Guide

This guide shows the recommended workflow for using ClickUp commands (`cum`) alongside Git.

## Installation

Before starting, ensure the ClickUp Framework is installed:

```bash
pip install --upgrade --force-reinstall git+https://github.com/SOELexicon/clickup_framework.git
```

And set your API token:

```bash
export CLICKUP_API_TOKEN="your_token_here"
# Add to ~/.bashrc or ~/.zshrc for persistence
```

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

# Add comment from file
cum ca current --comment-file progress_notes.md
```

### Viewing Context

```bash
# Check your current context
cum show

# View task with comments
cum d current --show-comments 5
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
| `hierarchy` | `h` `ls` `l` | View task hierarchy |
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

### Example 4: Daily standup workflow
```bash
# Check your tasks
cum a

# View task hierarchy with comments
cum h current --show-comments 3

# Update progress
cum ca current "Today: Completed authentication module, blocked on API review"
```

## Pro Tips

1. **Always use `cum show`** to verify your current context before running commands with "current"
2. **Use `cum d <task_id> --show-comments 5`** to see recent comments and context
3. **Add comments frequently** to track progress: `cum ca current "message"`
4. **Use dependencies** (`cum tad`) to enforce task order and prevent premature status changes
5. **Use links** (`cum tal`) for related tasks that don't have strict ordering
6. **Set default assignee** in context to auto-assign new tasks
7. **Use `--description-file` and `--comment-file`** for longer content from files
8. **Leverage short codes** - `cum h` is faster than `cum hierarchy`

## Context Management Tips

```bash
# Set up your default working context once
cum set workspace <workspace_id>
cum set list <list_id>
cum set assignee <your_user_id>

# Now all commands use these defaults
cum tc "Quick task"  # Auto-uses current list and assignee
cum h current        # Shows current list hierarchy
cum a                # Shows tasks for current assignee
```

## Integration with CI/CD

Add ClickUp updates to your CI/CD pipeline:

```yaml
# .github/workflows/deploy.yml
- name: Update ClickUp Task
  run: |
    pip install git+https://github.com/SOELexicon/clickup_framework.git
    cum ca $TASK_ID "Deployed to production: ${{ github.sha }}"
  env:
    CLICKUP_API_TOKEN: ${{ secrets.CLICKUP_API_TOKEN }}
    TASK_ID: ${{ github.event.inputs.task_id }}
```

---

For complete command reference: See the CLI Reference skill or run `/cum` in Claude Code.
