# Context Management Commands

Commands for setting and managing current workspace/list/task context.

**[← Back to Index](INDEX.md)**

---

## What is Context?

Context allows you to set default values for workspace, list, task, assignee, etc., so you can use the keyword `current` instead of typing IDs repeatedly.

**Benefits:**
- Faster command execution
- Less typing
- Fewer errors
- Cleaner command syntax

**Context is stored in:** `~/.clickup_context.json`

---

## Commands Overview

| Command | Shortcode | Description |
|---------|-----------|-------------|
| [`set_current`](#set_current) | `set` | Set current resource context |
| [`show_current`](#show_current) | `show` | Display current context |
| [`clear_current`](#clear_current) | `clear` | Clear context (all or specific type) |

---

## set_current

**Shortcode:** `set`

Set current resource context.

### Usage

```bash
cum set_current <resource_type> <resource_id>
cum set <resource_type> <resource_id>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `resource_type` | Yes | Type of resource (see below) |
| `resource_id` | Yes | ID or value of resource |

### Resource Types

| Type | Description | Example |
|------|-------------|---------|
| `workspace` | ClickUp workspace ID | `90151898946` |
| `team` | Team ID (same as workspace) | `90151898946` |
| `space` | Space ID | `90151234567` |
| `folder` | Folder ID | `90151234567` |
| `list` | List ID | `901517404278` |
| `task` | Task ID | `86c6xyz` |
| `assignee` | Default assignee user ID | `68483025` |
| `token` | API token | `pk_your_token` |

### Examples

```bash
# Set workspace
cum set workspace 90151898946

# Set list
cum set list 901517404278

# Set default assignee
cum set assignee 68483025

# Set current task
cum set task 86c6xyz

# Set API token
cum set token "pk_123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Chain multiple sets
cum set workspace 90151898946
cum set list 901517404278
cum set assignee 68483025
```

### Using Context

Once set, use `current` in place of the ID:

```bash
# Without context
cum hierarchy 901517404278
cum task_create 901517404278 "New task"

# With context
cum set list 901517404278
cum hierarchy current
cum task_create current "New task"
```

[→ Full set_current command details](commands/set_current.md)

---

## show_current

**Shortcode:** `show`

Display current context with animated box.

### Usage

```bash
cum show_current
cum show
```

### Output

Displays:
- Workspace ID
- Space ID
- Folder ID
- List ID
- Task ID
- Default assignee ID
- API token (masked)
- Last updated timestamp

### Examples

```bash
# Show current context
cum show

# Sample output:
# ╭─────────────────────────────────────╮
# │     Current ClickUp Context        │
# ├─────────────────────────────────────┤
# │ Workspace: 90151898946              │
# │ List:      901517404278             │
# │ Task:      86c6xyz                  │
# │ Assignee:  68483025                 │
# │ Token:     pk_*******************   │
# │ Updated:   2024-01-15 10:30:45      │
# ╰─────────────────────────────────────╯

# Check context before operations
cum show
cum hierarchy current
```

[→ Full show_current command details](commands/show_current.md)

---

## clear_current

**Shortcode:** `clear`

Clear context resources.

### Usage

```bash
cum clear_current [resource_type]
cum clear [resource_type]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `resource_type` | No | Type to clear (omit to clear all) |

### Resource Types

Same types as `set_current`:
- `workspace` / `team`
- `space`
- `folder`
- `list`
- `task`
- `assignee`
- `token`

### Examples

```bash
# Clear all context
cum clear

# Clear specific resource
cum clear task

# Clear list and task
cum clear list
cum clear task

# Clear and reset
cum clear
cum set workspace 90151898946
cum set list 901517404278
```

**Use case:** Clear context when switching between projects or workspaces.

[→ Full clear_current command details](commands/clear_current.md)

---

## Common Workflows

### Initial Setup

```bash
# Set up your default context
cum set token "pk_your_token_here"
cum set workspace 90151898946
cum set assignee 68483025
cum set list 901517404278

# Verify
cum show
```

### Working on a Project

```bash
# Set project context
cum set list 901517404278

# Work with current context
cum h current
cum tc current "New task" --priority high
cum a  # Show your assigned tasks
```

### Switching Projects

```bash
# Show current context
cum show

# Switch to new project
cum set list 901517404279

# Or clear and set fresh
cum clear
cum set workspace 90151898946
cum set list 901517404279
cum set assignee 68483025
```

### Working on Specific Task

```bash
# Set task as current
cum set task 86c6xyz

# Work on current task
cum d current
cum tu current --status "in progress"
cum ca current "Started working on this"
cum tss current "done"
```

### Multiple Workspace Workflow

```bash
# Create workspace aliases
alias work_workspace='cum set workspace 90151898946 && cum set assignee 68483025'
alias personal_workspace='cum set workspace 90151898947 && cum set assignee 68483026'

# Switch easily
work_workspace
cum h current --all

personal_workspace
cum h current --all
```

### Context-Based Scripts

```bash
#!/bin/bash
# daily_standup.sh

# Set context
cum set list "$DAILY_STANDUP_LIST"

# Show assigned tasks
echo "=== Your Tasks ==="
cum a

# Show stats
echo "=== List Stats ==="
cum st current

# Create daily standup note
cum ca "$STANDUP_TASK" "$(date +%Y-%m-%d) Standup:
- Yesterday: ...
- Today: ...
- Blockers: ..."
```

---

## Context Hierarchy

Resources have a natural hierarchy. Setting a child resource doesn't automatically set parent resources:

```
Workspace (Team)
└── Space
    └── Folder
        └── List
            └── Task
```

**Example:**
```bash
# Setting list doesn't set workspace
cum set list 901517404278

# Need to set workspace separately if required
cum set workspace 90151898946
```

**Best practice:** Set from top-down (workspace → list → task).

---

## Tips

1. **Set workspace first:** Always start with `cum set workspace`
2. **Use assignee context:** Auto-assign new tasks with `cum set assignee`
3. **Check before clearing:** Run `cum show` before `cum clear` to save IDs
4. **Create aliases:** Make workspace switching easier with shell aliases
5. **Context in scripts:** Use context to make scripts more maintainable
6. **Token in context:** Store token in context to avoid environment variables

---

## Context File Location

**File:** `~/.clickup_context.json`

**Structure:**
```json
{
  "workspace_id": "90151898946",
  "list_id": "901517404278",
  "task_id": "86c6xyz",
  "assignee_id": "68483025",
  "api_token": "pk_...",
  "space_id": null,
  "folder_id": null,
  "last_updated": "2024-01-15T10:30:45.123456"
}
```

**Manual editing:** You can edit this file directly if needed, but use `cum set` for safety.

---

## Security Note

The context file stores your API token in plain text. Ensure proper file permissions:

```bash
chmod 600 ~/.clickup_context.json
```

Alternatively, use environment variable:
```bash
export CLICKUP_API_TOKEN="pk_your_token"
```

The CLI checks environment variable first, then context file.

---

## Troubleshooting

### Context not working

```bash
# Check context
cum show

# Clear and reset
cum clear
cum set workspace YOUR_WORKSPACE_ID
cum set list YOUR_LIST_ID
```

### "Resource not found" errors

```bash
# Verify IDs are correct
cum show

# Test without context
cum hierarchy 901517404278

# If works, update context
cum set list 901517404278
```

### Token issues

```bash
# Check token
cum show

# Set new token
cum set token "pk_new_token"

# Or use environment variable
export CLICKUP_API_TOKEN="pk_new_token"
```

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [← Docs Commands](DOC_COMMANDS.md)
- [Config Commands →](CONFIG_COMMANDS.md)
