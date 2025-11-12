---
description: Complete command line reference for the cum CLI tool with full shortcode index
---

# ClickUp Framework CLI - Complete Command Reference

Access the comprehensive command line reference documentation for the `cum` (ClickUp Unified Manager) CLI tool.

## Documentation Structure

The CLI reference is organized into the following sections:

### 📋 [INDEX](../../docs/cli/INDEX.md)
**Main index page** with all shortcodes organized by category. Start here for quick lookup of any command or shortcode.

**Quick access to:**
- All shortcodes in one place
- Command categories overview
- Common options reference
- Priority values and status codes
- Special keywords (`current`)
- Quick start examples

---

### 📊 [View Commands](../../docs/cli/VIEW_COMMANDS.md)
Commands for displaying and visualizing tasks in different formats.

**Commands:** `hierarchy` (h, ls, l), `clist` (c), `flat` (f), `filter` (fil), `detail` (d), `stats` (st), `assigned` (a), `demo`

**Use when you need to:**
- View tasks in hierarchy, flat, or container view
- Filter tasks by status, priority, tags, or assignee
- See detailed task information with relationships
- View statistics and distribution
- Check your assigned tasks

---

### ✅ [Task Management](../../docs/cli/TASK_COMMANDS.md)
Commands for creating, updating, deleting, and managing tasks.

**Commands:** `task_create` (tc), `task_update` (tu), `task_delete` (td), `task_assign` (ta), `task_unassign` (tua), `task_set_status` (tss), `task_set_priority` (tsp), `task_set_tags` (tst), `task_add_dependency` (tad), `task_remove_dependency` (trd), `task_add_link` (tal), `task_remove_link` (trl)

**Use when you need to:**
- Create new tasks or subtasks
- Update task properties (name, description, status, priority)
- Assign/unassign users
- Manage task tags
- Set up dependencies and links between tasks
- Delete tasks

---

### 💬 [Comment Management](../../docs/cli/COMMENT_COMMANDS.md)
Commands for adding and managing comments on tasks.

**Commands:** `comment_add` (ca), `comment_list` (cl), `comment_update` (cu), `comment_delete` (cd)

**Use when you need to:**
- Add progress updates or notes to tasks
- List existing comments
- Update or delete comments
- Add comments from files

---

### 📄 [Docs Management](../../docs/cli/DOC_COMMANDS.md)
Commands for working with ClickUp Docs and pages.

**Commands:** `dlist` (dl), `doc_get` (dg), `doc_create` (dc), `doc_update` (du), `doc_export` (de), `doc_import` (di), `page_list` (pl), `page_create` (pc), `page_update` (pu)

**Use when you need to:**
- List, create, or update docs
- Export docs to markdown files
- Import markdown files as docs
- Manage pages within docs
- Backup documentation

---

### 🎯 [Context Management](../../docs/cli/CONTEXT_COMMANDS.md)
Commands for setting and managing current workspace/list/task context.

**Commands:** `set_current` (set), `show_current` (show), `clear_current` (clear)

**Use when you need to:**
- Set default workspace, list, task, or assignee
- Use `current` keyword instead of typing IDs
- View or clear your current context
- Store API token in context

---

### 🎨 [Configuration](../../docs/cli/CONFIG_COMMANDS.md)
Commands for configuring CLI behavior and settings.

**Commands:** `ansi`, `update`

**Use when you need to:**
- Enable/disable ANSI color output
- Update the cum tool to latest version
- Bump project version and create git tags

---

### 🔧 [Advanced Features](../../docs/cli/ADVANCED_COMMANDS.md)
Advanced functionality including checklists, custom fields, automation, and workflows.

**Features:**
- **Checklist Management** (`checklist`, `chk`) - Manage checklists with templates
- **Custom Fields** (`custom-field`, `cf`) - Manage custom field values
- **Parent Auto-Update** (`parent_auto_update`, `pau`) - Auto-update parent tasks
- **Git Overflow** (`overflow`) - Automated Git + ClickUp workflow
- **Space/Folder/List Management** - Create and manage organizational structure

**Use when you need to:**
- Create reusable checklist templates
- Track custom metadata on tasks
- Automate parent task updates based on subtasks
- Integrate Git commits with ClickUp updates
- Set up project structure (spaces, folders, lists)

---

## Quick Command Lookup

### Most Used Shortcodes

```bash
# View commands
cum h current              # hierarchy view
cum c current              # container view
cum f current              # flat list
cum fil current --status "in progress"  # filter
cum d <task_id>            # task details
cum st current             # statistics
cum a                      # assigned tasks

# Context management
cum set list <list_id>     # set current list
cum set task <task_id>     # set current task
cum show                   # show context

# Task management
cum tc current "Task name" # create task
cum tu <task_id> --name "New name"  # update task
cum tss <task_id> "done"   # set status
cum tsp <task_id> urgent   # set priority
cum tst <task_id> --add bug critical  # add tags
cum td <task_id>           # delete task

# Comments
cum ca <task_id> "Comment" # add comment
cum cl <task_id>           # list comments

# Docs
cum dl <workspace_id>      # list docs
cum de <workspace_id> --output-dir ./docs  # export docs
```

---

## Getting Started Workflow

### 1. Initial Setup

```bash
# Set API token
cum set token "pk_your_token"

# Set default workspace and list
cum set workspace 90151898946
cum set list 901517404278

# Set default assignee (tasks auto-assigned)
cum set assignee 68483025

# Verify setup
cum show
```

### 2. View Your Work

```bash
# See your assigned tasks
cum a

# View current list in hierarchy
cum h current

# View with details
cum h current --preset detailed --show-descriptions
```

### 3. Work on a Task

```bash
# Set current task
cum set task 86c6xyz

# View task details
cum d current

# Update status
cum tss current "in progress"

# Add comment
cum ca current "Started working on this"
```

### 4. Create and Manage Tasks

```bash
# Create task
cum tc current "New feature" --priority high --tags feature backend

# Create subtask
cum tc "Subtask" --parent <parent_id>

# Update task
cum tu current --description-file spec.md

# Set status
cum tss current "done"
```

---

## Common Workflows

### Development Workflow

```bash
# 1. View assigned tasks
cum a

# 2. Set current task
cum set task <task_id>

# 3. Update status
cum tss current "in progress"

# 4. Work on code, then commit
git add .
git commit -m "Implement feature"
git push

# 5. Add comment with commit info
cum ca current "Committed changes - ready for review"

# 6. Update status
cum tss current "in review"

# 7. After review, complete
cum tss current "done"
```

### Git Overflow Workflow (Automated)

```bash
# Set current task
cum set task 86c6xyz

# Work on code, then use overflow
cum overflow "Implement feature X" --status "in review" --tags "needs-review"

# Result:
# ✓ Changes committed
# ✓ Pushed to remote
# ✓ Task updated to "in review"
# ✓ Tags added
# ✓ Comment added with commit SHA
```

### Project Setup Workflow

```bash
# Create space
cum space create --name "Project X" --workspace current

# Create folders
cum folder create --space <space_id> --name "Backend"
cum folder create --space <space_id> --name "Frontend"

# Create lists
cum list-mgmt create --folder <folder_id> --name "Sprint 1"

# Set context
cum set list <list_id>

# Create tasks with templates
cum tc "Setup API" --checklist-template "api-setup" --priority high
```

---

## Tips & Best Practices

1. **Use context everywhere:** Set once with `cum set`, use `current` everywhere
2. **Master shortcodes:** `cum h` instead of `cum hierarchy` - faster and cleaner
3. **Enable colors:** Better visual experience - `cum ansi enable`
4. **Use presets:** Quick formatting - `cum h current --preset detailed`
5. **Checklist templates:** Reusable checklists save time
6. **Markdown support:** Use `--description-file` for rich task descriptions
7. **Git overflow:** Automate Git + ClickUp updates in one command
8. **Dependencies:** Use `cum tad` to enforce task order
9. **Check context:** Run `cum show` to verify before using `current`
10. **Help is always there:** `cum <command> --help` for any command

---

## Import to ClickUp Docs

You can import this entire documentation structure into ClickUp Docs:

```bash
# Quick import (uses default workspace)
./scripts/import_cli_docs.sh

# Import to specific workspace
./scripts/import_cli_docs.sh 90151898946

# Custom doc name
./scripts/import_cli_docs.sh --doc-name "CLI Reference v2.0"

# Check prerequisites first
./scripts/import_cli_docs.sh --check
```

The script will import all 8 documentation pages as a single ClickUp Doc that you can share with your team.

---

## Documentation Quick Links

- **[Full Index](../../docs/cli/INDEX.md)** - All commands and shortcodes
- **[View Commands](../../docs/cli/VIEW_COMMANDS.md)** - Display and visualize tasks
- **[Task Commands](../../docs/cli/TASK_COMMANDS.md)** - Create and manage tasks
- **[Comment Commands](../../docs/cli/COMMENT_COMMANDS.md)** - Manage task comments
- **[Docs Commands](../../docs/cli/DOC_COMMANDS.md)** - Work with ClickUp Docs
- **[Context Commands](../../docs/cli/CONTEXT_COMMANDS.md)** - Context management
- **[Config Commands](../../docs/cli/CONFIG_COMMANDS.md)** - CLI configuration
- **[Advanced Commands](../../docs/cli/ADVANCED_COMMANDS.md)** - Advanced features

---

## Need More Help?

```bash
# General help
cum --help

# Command-specific help
cum <command> --help

# Examples:
cum hierarchy --help
cum task_create --help
cum overflow --help
```

---

## Version Information

```bash
# Check current version
cum --version

# Update to latest
cum update cum

# Bump version (for developers)
cum update version --minor
```
