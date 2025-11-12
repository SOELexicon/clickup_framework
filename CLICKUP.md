# ClickUp Framework CLI Guide

Complete command-line interface for the ClickUp Framework with beautiful hierarchical task displays and comprehensive task management.

> **Note**: This CLI is under active development. Commands marked with ✅ are fully implemented, while commands marked with 🚧 are planned for future releases. See the [Implementation Roadmap](#implementation-roadmap) for details.

## Table of Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Task Workflow Guide](docs/TASK_WORKFLOW_GUIDE.md) 📖
- [File Input Support](#file-input-support)
- [View Commands (Implemented)](#view-commands-implemented-)
- [Context Management (Implemented)](#context-management-implemented-)
- [Task Management Commands (Implemented)](#task-management-commands-implemented-)
- [Comment Commands (Implemented)](#comment-commands-)
- [Checklist Commands (Implemented)](#checklist-commands-)
- [Relationship Commands (Implemented)](#relationship-commands-)
- [Custom Field Commands (Implemented)](#custom-field-commands-)
- [List Commands (Planned)](#list-commands-planned-)
- [Workspace/Space/Folder Commands (Planned)](#workspacespacefolders-commands-planned-)
- [Docs Commands (Implemented)](#docs-commands-)
- [Time Tracking Commands (Planned)](#time-tracking-commands-planned-)
- [View Management Commands (Planned)](#view-management-commands-planned-)
- [Attachment Commands (Planned)](#attachment-commands-planned-)
- [Format Options](#format-options)
- [Presets](#presets)
- [Implementation Roadmap](#implementation-roadmap)

---

## Installation

```bash
pip install -e .
```

After installation, the CLI is available as both `clickup` and `cum` (ClickUp Manager):

```bash
# Both commands work identically
clickup hierarchy <list_id>
cum hierarchy <list_id>
```

## Authentication

Set your ClickUp API token as an environment variable:

```bash
export CLICKUP_API_TOKEN="your_api_token_here"
```

## Quick Start

```bash
# Try the demo mode (no API token required)
cum demo --mode hierarchy

# View tasks in a list
cum hierarchy <list_id>

# Set current list for easier access
cum set_current list <list_id>

# Show current context
cum show_current
```

---

## File Input Support

The CLI supports reading longer content from files for task descriptions and comments, making it easy to work with markdown documentation and formatted text.

### Supported Commands

**Task Management**:
- `task_create --description-file PATH` - Create task with description from file
- `task_update --description-file PATH` - Update task description from file

**Comment Management**:
- `comment_add "text"` - Add comment with direct text (positional argument)
- `comment_add --comment-file PATH` - Add comment from file
- `comment_update "text"` - Update comment with direct text (positional argument)
- `comment_update --comment-file PATH` - Update comment from file

### Examples

```bash
# Create task with description from markdown file
cum task_create current "Implement feature" --description-file spec.md

# Update task description from file
cum task_update current --description-file updated_spec.md

# Add comment with direct text (recommended)
cum comment_add current "Great work on this feature!"

# Add comment from file
cum comment_add current --comment-file feedback.md

# Update comment with direct text (recommended)
cum comment_update abc123 "Updated feedback after review"

# Update comment from file
cum comment_update abc123 --comment-file revised_notes.md
```

**Notes**:
- File input options (`--description-file`, `--comment-file`) are mutually exclusive with their text counterparts
  - For tasks: `--description` flag
  - For comments: positional `text` argument (no flag needed!)
- Comment text can be passed directly without any flag (e.g., `cum ca <task_id> "text"`)
- Use `--comment-file` for longer content or when maintaining comments in version control
- Files can contain any text format, including markdown
- Files are read with UTF-8 encoding
- Useful for maintaining task specifications and documentation in version control

---

## Display Features

### 3-Letter Status Codes
All task views now display color-coded 3-letter status codes before task names:

- `[CLS]` - Closed/Complete
- `[OPN]` - Open
- `[PRG]` - In Progress
- `[REV]` - In Review
- `[BLK]` - Blocked
- `[TDO]` - To Do
- Custom statuses use first 3 letters (e.g., `[IN ]` for "in development")

Example output:
```
├─📝 [CLS] Task Management Commands
├─📝 [OPN] task create - Create new tasks
└─📝 [PRG] CLI Command Implementation (P1)
```

### Configurable ANSI Colors
Control color output globally or per-command:

```bash
# Enable colors globally (default: disabled)
cum ansi enable

# Disable colors globally
cum ansi disable

# Check current setting
cum ansi status

# Override per command
cum hierarchy <list_id> --colorize       # Force colors on
cum hierarchy <list_id> --no-colorize    # Force colors off
```

Setting persists in `~/.clickup_context.json`.

---

## View Commands (Implemented) ✅

These commands display tasks in various formats with beautiful tree views and colored output.

### `hierarchy` - Hierarchical Parent-Child View
Display tasks in a tree structure showing parent-child relationships.

**Default Preset**: `full` (shows IDs, descriptions, dates, and all details)

```bash
cum hierarchy <list_id> [options]

# Examples:
cum hierarchy 901517404278
cum hierarchy 901517404278 --preset minimal  # Override to minimal
cum hierarchy 901517404278 --show-ids --show-descriptions
```

**Options**: All [format options](#format-options) and [presets](#presets) are supported.

---

### `container` - Container Hierarchy View
Display tasks organized by their ClickUp containers (Space → Folder → List).

```bash
cum container <list_id> [options]

# Example:
cum container 901517404278 --preset full
```

---

### `flat` - Flat List View
Display all tasks in a simple flat list format.

```bash
cum flat <list_id> [options]

# Examples:
cum flat 901517404278
cum flat 901517404278 --header "My Tasks"
```

**Additional Options**:
- `--header TEXT` - Custom header for the flat list

---

### `filter` - Filtered Task View
Display tasks filtered by status, priority, tags, or assignee.

```bash
cum filter <list_id> [filter_options] [format_options]

# Examples:
cum filter 901517404278 --status "in progress"
cum filter 901517404278 --priority 1
cum filter 901517404278 --tags bug critical
cum filter 901517404278 --assignee user_123
cum filter 901517404278 --status "to do" --view-mode flat
```

**Filter Options**:
- `--status TEXT` - Filter by task status
- `--priority INT` - Filter by priority (1=urgent, 4=low)
- `--tags TAG [TAG...]` - Filter by one or more tags
- `--assignee USER_ID` - Filter by assignee ID
- `--view-mode {hierarchy|container|flat}` - Display mode (default: hierarchy)

---

### `detail` - Detailed Task View
Show comprehensive details for a single task including relationships.

```bash
cum detail <task_id> [list_id] [options]

# Examples:
cum detail 86c6e0q06
cum detail 86c6e0q06 901517404278
```

**Arguments**:
- `task_id` - The task ID to display
- `list_id` - (Optional) List ID for relationship context

---

### `stats` - Task Statistics
Display aggregate statistics for tasks in a list.

```bash
cum stats <list_id>

# Example:
cum stats 901517404278
```

Shows:
- Total tasks
- Tasks by status
- Tasks by priority
- Completion percentages
- Tag distribution

---

### `demo` - Demo Mode
View demo output with sample data (no API token required).

```bash
cum demo [--mode MODE] [options]

# Examples:
cum demo
cum demo --mode container
cum demo --mode stats
cum demo --preset minimal
```

**Modes**:
- `hierarchy` - Hierarchical view (default)
- `container` - Container view
- `flat` - Flat list view
- `stats` - Statistics view
- `detail` - Detailed task view

---

### `assigned` - Assigned Tasks View
Display tasks assigned to a user, sorted by dependency difficulty.

```bash
cum assigned [--user-id USER_ID] [--team-id TEAM_ID]

# Examples:
cum assigned  # Uses default assignee from config
cum assigned --user-id 68483025
cum assigned --user-id 68483025 --team-id 90151898946
```

**Features**:
- **Smart Sorting**: Tasks sorted by difficulty (# of open blockers) then dependency depth
- **Difficulty Score**: Automatically decreases as blocking tasks get closed
- **Visual Indicators**:
  - ✓ Ready (green) - No blockers, ready to start
  - ⚠ Warning (yellow) - 1-2 blockers
  - 🚫 Blocked (red) - 3+ blockers
- **Dependency Analysis**: Shows blocker details, dependency depth, and relationship counts
- **Summary Stats**: Ready vs blocked task counts

**Options**:
- `--user-id USER_ID` - User ID to filter tasks (defaults to configured default assignee)
- `--team-id TEAM_ID` - Team/workspace ID (defaults to current workspace)

**Note**: Requires default assignee configured or --user-id parameter. Set default with:
```bash
cum set_current assignee <user_id>
```

---

## Context Management (Implemented) ✅

Manage your current working context to avoid repeatedly specifying IDs.

### `set_current` - Set Current Resource
Set the current task, list, space, folder, workspace, or default assignee.

```bash
cum set_current <resource_type> <resource_id>

# Examples:
cum set_current workspace 90151898946
cum set_current list 901517404278
cum set_current task 86c6e0q06
cum set_current assignee 68483025  # Set default assignee for task creation
```

**Resource Types**: `task`, `list`, `space`, `folder`, `workspace`, `team`, `assignee`

**Default Assignee**: When set, all newly created tasks will be automatically assigned to this user (defaults to 68483025).

---

### `show_current` - Show Current Context
Display your current context with a beautiful animated box.

```bash
cum show_current
```

Shows:
- Current workspace (if set)
- Current space (if set)
- Current folder (if set)
- Current list (if set)
- Current task (if set)
- Default assignee (if set)
- ANSI output setting
- Last updated timestamp

Features:
- Rainbow gradient title
- Color-coded IDs by type
- Animated Unicode box borders

---

### `ansi` - Configure ANSI Color Output
Enable or disable colored terminal output globally.

```bash
cum ansi <action>

# Actions:
cum ansi enable   # Enable ANSI colors (default: disabled)
cum ansi disable  # Disable ANSI colors
cum ansi status   # Show current setting
```

The setting persists across sessions in `~/.clickup_context.json`. You can override per-command with `--colorize` or `--no-colorize` flags.

---

### `update cum` - Update CLI Tool
Update the ClickUp CLI tool from the git repository and reinstall.

```bash
cum update cum

# This command will:
# 1. Pull latest changes from git
# 2. Reinstall the package
# 3. Show the updated version
```

**Note**: Requires git repository access and write permissions to the installation directory.

---

### `clear_current` - Clear Context
Clear one or all current resources from your context.

```bash
# Clear specific resource
cum clear_current <resource_type>

# Clear all context
cum clear_current

# Examples:
cum clear_current list
cum clear_current  # Clears everything
```

---

## Task Management Commands ✅

> **Status**: Fully implemented (all core commands complete)
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q0a)

### `task_create` - Create New Task ✅
**Task ID**: [86c6e0q0b](https://app.clickup.com/t/86c6e0q0b) | **Status**: ✅ Closed

Create a new task with full options support.

**IMPORTANT**: Task name comes FIRST as a positional argument, then use flags for list/parent!

```bash
cum task_create "Task name" --list <list_id> [options]
cum tc "Task name" --list <list_id> [options]  # Short code

# Examples:
cum tc "Implement feature X" --list current
cum tc "Bug fix" --list 901517404278 --description "Fix login issue" --priority urgent
cum tc "New task" --list current --status "in progress" --tags bug critical
cum tc "Subtask" --parent 86c6e0q06  # Create subtask (no --list needed)
cum tc "Feature" --list current --description-file spec.md  # Load description from file
```

**Arguments**:
- `name` - Task name (required, positional argument - comes FIRST!)

**Options**:
- `--list LIST_ID` - List ID to create task in (or "current"). Not required if --parent is provided.
- `--description TEXT` - Task description (plain text)
- `--description-file PATH` - Load task description from file (supports markdown)
- `--status STATUS` - Initial status
- `--priority {1|2|3|4|urgent|high|normal|low}` - Priority level
- `--tags TAG [TAG...]` - Tags to add
- `--assignees USER_ID [USER_ID...]` - User IDs to assign (defaults to configured default assignee)
- `--parent TASK_ID` - Parent task ID (creates subtask)

**Note**: `--description` and `--description-file` are mutually exclusive.

**Default Assignee**: Tasks are automatically assigned to the default assignee unless `--assignees` is specified.

---

### `task_update` - Update Existing Task ✅
**Task ID**: [86c6e0q0d](https://app.clickup.com/t/86c6e0q0d) | **Status**: ✅ Closed

Update an existing task's properties.

```bash
cum task_update <task_id> [options]

# Examples:
cum task_update current --name "Updated name"
cum task_update 86c6e0q06 --description "New description"
cum task_update current --status "complete" --priority high
cum task_update current --description-file updated_spec.md  # Update from file
```

**Options**:
- `--name TEXT` - Update task name
- `--description TEXT` - Update description (plain text)
- `--description-file PATH` - Load description from file (supports markdown)
- `--status STATUS` - Update status
- `--priority {1|2|3|4|urgent|high|normal|low}` - Update priority
- `--add-tags TAG [TAG...]` - Add tags to existing tags
- `--remove-tags TAG [TAG...]` - Remove specific tags

**Note**: `--description` and `--description-file` are mutually exclusive.

---

### `task_delete` - Delete Task ✅
**Task ID**: [86c6e0q0f](https://app.clickup.com/t/86c6e0q0f) | **Status**: ✅ Closed

Delete a task with optional confirmation prompt.

```bash
cum task_delete <task_id> [--force]

# Examples:
cum task_delete 86c6e0q06      # Prompts for confirmation
cum task_delete current -f     # Skip confirmation prompt
```

**Arguments**:
- `task_id` - Task ID or "current" from context

**Options**:
- `--force`, `-f` - Skip confirmation prompt

**Warning**: Deletion is permanent and cannot be undone. Subtasks are NOT deleted automatically.

---

### `task_assign` - Assign Task to User ✅
**Task ID**: [86c6e0q0g](https://app.clickup.com/t/86c6e0q0g) | **Status**: ✅ Closed

Assign one or more users to a task.

```bash
cum task_assign <task_id> <user_id> [user_id...]

# Examples:
cum task_assign current 68483025
cum task_assign 86c6e0q06 68483025 12345678
```

---

### `task_unassign` - Remove Assignee ✅
**Task ID**: [86c6e0q0h](https://app.clickup.com/t/86c6e0q0h) | **Status**: ✅ Closed

Remove one or more users from a task.

```bash
cum task_unassign <task_id> <user_id> [user_id...]

# Examples:
cum task_unassign current 68483025
cum task_unassign 86c6e0q06 68483025 12345678
```

---

### `task_set_status` - Change Task Status ✅
**Task ID**: [86c6e0q0j](https://app.clickup.com/t/86c6e0q0j) | **Status**: ✅ Closed

Set task status with subtask validation and multi-task support.

```bash
cum task_set_status <task_id> [task_id...] <status>

# Examples:
cum task_set_status current "in progress"
cum task_set_status 86c6e0q06 86c6e0q0a "complete"
```

**Features**:
- **Subtask Validation**: Prevents parent status change unless all subtasks have the same status
- **Multi-Task Support**: Update multiple tasks in one command
- **Error Display**: Shows which subtasks need updating with formatted output

**Example Error**:
```
⚠ Cannot set status for [86c6e0q06] Task Management Commands

Mismatched Subtasks (3):
├─📝 [OPN] task create - Create new tasks
├─📝 [OPN] task delete - Delete tasks
└─📝 [PRG] task update - Update existing tasks

Update these subtasks first, then retry the parent status change.
```

**Features**:
- Validates subtasks have matching status before allowing parent status change
- Supports multiple tasks in one command
- Shows detailed subtask status if validation fails

---

### `task_set_priority` - Change Task Priority ✅
**Task ID**: [86c6e0q0m](https://app.clickup.com/t/86c6e0q0m) | **Status**: ✅ Closed

Set task priority using numbers or names.

```bash
cum task_set_priority <task_id> <priority>

# Examples:
cum task_set_priority current urgent
cum task_set_priority 86c6e0q06 1
cum task_set_priority current high
```

**Priority Values**:
- `1` or `urgent` - Urgent priority
- `2` or `high` - High priority
- `3` or `normal` - Normal priority
- `4` or `low` - Low priority

---

### `task_set_tags` - Manage Task Tags ✅
**Task ID**: [86c6e0q0k](https://app.clickup.com/t/86c6e0q0k) | **Status**: ✅ Closed

Add, remove, or set task tags.

```bash
cum task_set_tags <task_id> {--add|--remove|--set} TAG [TAG...]

# Examples:
cum task_set_tags current --add bug critical
cum task_set_tags 86c6e0q06 --remove outdated
cum task_set_tags current --set feature ui high-priority
```

**Actions**:
- `--add TAG [TAG...]` - Add tags to existing tags
- `--remove TAG [TAG...]` - Remove specific tags
- `--set TAG [TAG...]` - Replace all tags (clears existing)

---

## Comment Commands ✅

> **Status**: Fully implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q0n)

### `comment_add` - Add Comment to Task ✅
**Task ID**: [86c6e0q0p](https://app.clickup.com/t/86c6e0q0p) | **Status**: ✅ Closed

Add a comment to a task with text or from a file.

```bash
cum comment_add <task_id> "Comment text"
cum comment_add <task_id> --comment-file notes.txt

# Examples:
cum comment_add current "Great work on this feature!"
cum comment_add 86c6e0q06 --comment-file feedback.md
```

**Arguments**:
- `task_id` - Task ID or "current" from context
- `comment_text` - Direct comment text (optional if using --comment-file)

**Options**:
- `--comment-file PATH` - Read comment text from file (supports markdown)

**Note**: `comment_text` and `--comment-file` are mutually exclusive.

---

### `comment_list` - List Task Comments ✅
**Task ID**: [86c6e0q0r](https://app.clickup.com/t/86c6e0q0r) | **Status**: ✅ Closed

List all comments on a task with configurable detail level.

```bash
cum comment_list <task_id> [options]

# Examples:
cum comment_list current
cum comment_list 86c6e0q06 --limit 5
cum comment_list current --detail full
```

**Arguments**:
- `task_id` - Task ID or "current" from context

**Options**:
- `--limit N` - Limit number of comments shown
- `--detail {minimal|summary|detailed|full}` - Detail level (default: summary)

---

### `comment_update` - Update Comment ✅
**Task ID**: [86c6e0q0t](https://app.clickup.com/t/86c6e0q0t) | **Status**: ✅ Closed

Update an existing comment's text.

```bash
cum comment_update <comment_id> "New text"
cum comment_update <comment_id> --comment-file updated.txt

# Examples:
cum comment_update abc123 "Updated feedback"
cum comment_update abc123 --comment-file revised_notes.md
```

**Arguments**:
- `comment_id` - Comment ID to update
- `comment_text` - New comment text (optional if using --comment-file)

**Options**:
- `--comment-file PATH` - Read new comment text from file

**Note**: `comment_text` and `--comment-file` are mutually exclusive.

---

### `comment_delete` - Delete Comment ✅
**Task ID**: [86c6e0q0u](https://app.clickup.com/t/86c6e0q0u) | **Status**: ✅ Closed

Delete a comment with optional confirmation prompt.

```bash
cum comment_delete <comment_id> [--force]

# Examples:
cum comment_delete abc123      # Prompts for confirmation
cum comment_delete abc123 -f   # Skip confirmation
```

**Arguments**:
- `comment_id` - Comment ID to delete

**Options**:
- `--force`, `-f` - Skip confirmation prompt

---

## Checklist Commands ✅

> **Status**: Implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q0v)

Manage checklists and checklist items on tasks.

**Alias**: `chk`

### `checklist create` - Create Checklist

Create a new checklist on a task.

```bash
cum checklist create <task_id> <name>
cum chk create current "Implementation Tasks"
```

**Arguments**:
- `task_id` - Task ID (or "current")
- `name` - Checklist name

**Options**:
- `--verbose`, `-v` - Show additional information

---

### `checklist delete` - Delete Checklist

Delete a checklist and all its items.

```bash
cum checklist delete <checklist_id>
cum chk delete <checklist_id> --force
cum chk rm <checklist_id>  # Using alias
```

**Arguments**:
- `checklist_id` - Checklist ID

**Options**:
- `--force`, `-f` - Skip confirmation prompt

---

### `checklist update` - Update Checklist

Update checklist properties.

```bash
cum checklist update <checklist_id> --name "New name"
cum chk update <checklist_id> --position 0
```

**Arguments**:
- `checklist_id` - Checklist ID

**Options**:
- `--name NAME` - New checklist name
- `--position POS` - New position (order)
- `--verbose`, `-v` - Show update details

---

### `checklist list` - List Checklists

List all checklists and items on a task.

```bash
cum checklist list <task_id>
cum chk list current
cum chk ls current --show-ids
```

**Arguments**:
- `task_id` - Task ID (or "current")

**Options**:
- `--show-ids` - Show checklist and item IDs
- `--no-items` - Hide checklist items, show only checklist names
- `--colorize` - Use colors in output (default: true)

**Example Output**:
```
Checklists for task CLI Command Implementation
Task ID: 86c6e0q06

☑️  Implementation Tasks (0/3)
    ☐ Create checklist commands module
    ☐ Test all commands
    ☐ Update documentation
```

---

### `checklist item-add` - Add Checklist Item

Add a new item to an existing checklist.

```bash
cum checklist item-add <checklist_id> <name>
cum chk add <checklist_id> "Complete testing"
cum chk add <checklist_id> "Review code" --assignee 68483025
```

**Alias**: `add`

**Arguments**:
- `checklist_id` - Checklist ID
- `name` - Item name

**Options**:
- `--assignee USER_ID` - User ID to assign (or "current")
- `--verbose`, `-v` - Show additional information

---

### `checklist item-update` - Update Checklist Item

Update properties of a checklist item.

```bash
cum checklist item-update <checklist_id> <item_id> --name "New name"
cum chk update-item <checklist_id> <item_id> --resolved true
cum chk update-item <checklist_id> <item_id> --assignee 68483025
```

**Alias**: `update-item`

**Arguments**:
- `checklist_id` - Checklist ID
- `item_id` - Item ID

**Options**:
- `--name NAME` - New item name
- `--assignee USER_ID` - User ID to assign (or empty to unassign)
- `--resolved BOOL` - Mark as resolved (true/false)
- `--parent PARENT_ID` - Parent checklist item ID
- `--verbose`, `-v` - Show update details

---

### `checklist item-delete` - Delete Checklist Item

Delete a checklist item.

```bash
cum checklist item-delete <checklist_id> <item_id>
cum chk delete-item <checklist_id> <item_id> --force
cum chk rm-item <checklist_id> <item_id>
```

**Aliases**: `delete-item`, `rm-item`

**Arguments**:
- `checklist_id` - Checklist ID
- `item_id` - Item ID

**Options**:
- `--force`, `-f` - Skip confirmation prompt

---

## Relationship Commands ✅

> **Status**: Fully implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q12)

### Dependency Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q14)

#### `task_add_dependency` - Add Task Dependency ✅
**Task ID**: [86c6e0q16](https://app.clickup.com/t/86c6e0q16) | **Status**: ✅ Closed

Add a dependency relationship between tasks (waiting-on or blocking).

```bash
cum task_add_dependency <task_id> --waiting-on <depends_on_task_id>
cum task_add_dependency <task_id> --blocking <blocked_task_id>

# Examples:
cum task_add_dependency current --waiting-on 86c6e0q06
cum task_add_dependency 86c6e0q0a --blocking 86c6e0q0b
```

**Arguments**:
- `task_id` - Task ID or "current" from context

**Options** (one required):
- `--waiting-on TASK_ID` - Mark this task as waiting on another task (depends on)
- `--blocking TASK_ID` - Mark this task as blocking another task

**Relationship Types**:
- **Waiting On**: This task cannot start until the specified task is complete
- **Blocking**: This task must be completed before the specified task can start

---

#### `task_remove_dependency` - Remove Dependency ✅
**Task ID**: [86c6e0q19](https://app.clickup.com/t/86c6e0q19) | **Status**: ✅ Closed

Remove a dependency relationship between tasks.

```bash
cum task_remove_dependency <task_id> --waiting-on <dependency_task_id>
cum task_remove_dependency <task_id> --blocking <blocked_task_id>

# Examples:
cum task_remove_dependency current --waiting-on 86c6e0q06
cum task_remove_dependency 86c6e0q0a --blocking 86c6e0q0b
```

**Arguments**:
- `task_id` - Task ID or "current" from context

**Options** (one required):
- `--waiting-on TASK_ID` - Remove "waiting on" dependency
- `--blocking TASK_ID` - Remove "blocking" dependency

---

### Link Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1a)

#### `task_add_link` - Link Two Tasks ✅
**Task ID**: [86c6e0q1c](https://app.clickup.com/t/86c6e0q1c) | **Status**: ✅ Closed

Create a general link between two tasks (non-dependency relationship).

```bash
cum task_add_link <task_id> <linked_task_id>

# Examples:
cum task_add_link current 86c6e0q06
cum task_add_link 86c6e0q0a 86c6e0q0b
```

**Arguments**:
- `task_id` - Task ID or "current" from context
- `linked_task_id` - Task ID to link to

**Note**: Links are bidirectional - both tasks will show the relationship.

---

#### `task_remove_link` - Unlink Tasks ✅
**Task ID**: [86c6e0q1d](https://app.clickup.com/t/86c6e0q1d) | **Status**: ✅ Closed

Remove a link between two tasks.

```bash
cum task_remove_link <task_id> <linked_task_id>

# Examples:
cum task_remove_link current 86c6e0q06
cum task_remove_link 86c6e0q0a 86c6e0q0b
```

**Arguments**:
- `task_id` - Task ID or "current" from context
- `linked_task_id` - Task ID to unlink from

---

## Custom Field Commands ✅

> **Status**: Implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1e)

Manage custom fields on tasks. Supports field resolution by name or ID, automatic type validation, and formatted display.

**Alias**: `cf`

### `custom-field set` - Set Custom Field Value

Set a custom field value on a task. Accepts field name (case-insensitive) or field ID.

```bash
cum custom-field set <task_id> <field_name_or_id> <value>
cum cf set current "Difficulty Score" 8
```

**Features**:
- Auto-detects field type and validates value
- Supports all field types: text, number, date, dropdown, checkbox, currency, rating, etc.
- Field name resolution (case-insensitive)
- Shows field info before setting

**Examples**:
```bash
# Set by field name
cum cf set 86c6e0q1e "Priority Score" 8

# Set by field ID
cum cf set current 518a7a2f-a441-4db8-847e-9b47436bf7fa 7

# Set date field
cum cf set current "Due Date" "2025-01-15"

# Set dropdown
cum cf set current "Status" "In Progress"

# Set checkbox
cum cf set current "Approved" true
```

---

### `custom-field get` - Get Custom Field Value

Get a specific custom field value from a task with formatted display.

```bash
cum custom-field get <task_id> <field_name_or_id>
cum cf get current "Difficulty Score"
```

**Features**:
- Field name or ID resolution
- Type-based value formatting
- Color-coded by field type
- Shows "(not set)" for empty fields

**Example Output**:
```
Difficulty Score (number)
Value: 8
```

---

### `custom-field list` - List Custom Fields

List custom fields at different hierarchy levels or show values on a specific task.

```bash
cum custom-field list --task <task_id>        # Show fields on task with values
cum custom-field list --list <list_id>        # Show available fields for list
cum custom-field list --space <space_id>      # Show available fields for space
cum custom-field list --workspace <team_id>   # Show all workspace fields
```

**Features**:
- Multiple hierarchy levels
- Grouped by field type
- Shows field definitions or values
- Required fields marked with *
- Additional type info (options, max rating, etc.)

**Examples**:
```bash
# List all fields on current task with values
cum cf list --task current

# List available fields for current list
cum cf list --list current

# List all workspace custom fields
cum cf list --workspace 90151898946
```

**Example Output**:
```
Custom Fields for Task 86c6e0q06
Task: CLI Command Implementation

  Difficulty Score (number)
    Value: 8

  🔐 On Closed (short_text)
    Value: (not set)
```

---

### `custom-field remove` - Remove Custom Field Value

Remove/clear a custom field value from a task.

```bash
cum custom-field remove <task_id> <field_name_or_id>
cum cf remove current "Difficulty Score"
cum cf rm current "Priority Score"
```

**Alias**: `rm`

**Features**:
- Shows current value before removing
- Warns if field is required
- Field name or ID resolution

**Example**:
```bash
cum cf remove current "Difficulty Score"
```

**Example Output**:
```
Field: Difficulty Score (number)
Current value: 8

✓ Custom field 'Difficulty Score' removed from task
```

---

### Custom Field Type Support

All ClickUp custom field types are supported:

| Type | Description | Example Value |
|------|-------------|---------------|
| `short_text` | Short text field | "Quick note" |
| `text` | Long text field | "Detailed description..." |
| `number` | Numeric value | 42 |
| `drop_down` | Single selection | "In Progress" |
| `labels` | Multiple selection | "bug, urgent" |
| `date` | Date/timestamp | "2025-01-15" |
| `checkbox` | Boolean | true/false, yes/no, 1/0 |
| `email` | Email address | "user@example.com" |
| `url` | Web URL | "https://example.com" |
| `phone` | Phone number | "+1-234-567-8900" |
| `currency` | Money value | 99.99 |
| `rating` | Star rating | 4 (★★★★☆) |
| `location` | Location text | "San Francisco, CA" |

---

## List Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1j)

### `list create` - Create New List
**Task ID**: [86c6e0q1k](https://app.clickup.com/t/86c6e0q1k)

```bash
# NOT YET IMPLEMENTED
cum list create <folder_id> --name "List name"
```

---

### `list update` - Update List Properties
**Task ID**: [86c6e0q1n](https://app.clickup.com/t/86c6e0q1n)

```bash
# NOT YET IMPLEMENTED
cum list update <list_id> [options]
```

---

### `list delete` - Delete List
**Task ID**: [86c6e0q1p](https://app.clickup.com/t/86c6e0q1p)

```bash
# NOT YET IMPLEMENTED
cum list delete <list_id>
```

---

### `list show` - Show List Details
**Task ID**: [86c6e0q1t](https://app.clickup.com/t/86c6e0q1t)

```bash
# NOT YET IMPLEMENTED
cum list show <list_id>
```

---

## Workspace/Space/Folder Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1u)

### Workspace Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1v)

#### `workspace list` - List Workspaces
**Task ID**: [86c6e0q1w](https://app.clickup.com/t/86c6e0q1w)

```bash
# NOT YET IMPLEMENTED
cum workspace list
```

---

#### `workspace show` - Show Workspace Details
**Task ID**: [86c6e0q1x](https://app.clickup.com/t/86c6e0q1x)

```bash
# NOT YET IMPLEMENTED
cum workspace show <workspace_id>
```

---

### Space Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1z)

#### `space list` - List Spaces
**Task ID**: [86c6e0q23](https://app.clickup.com/t/86c6e0q23)

```bash
# NOT YET IMPLEMENTED
cum space list <workspace_id>
```

---

#### `space create` - Create Space
**Task ID**: [86c6e0q26](https://app.clickup.com/t/86c6e0q26)

```bash
# NOT YET IMPLEMENTED
cum space create <workspace_id> --name "Space name"
```

---

#### `space show` - Show Space Details
**Task ID**: [86c6e0q27](https://app.clickup.com/t/86c6e0q27)

```bash
# NOT YET IMPLEMENTED
cum space show <space_id>
```

---

### Folder Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q2a)

#### `folder list` - List Folders
**Task ID**: [86c6e0q2b](https://app.clickup.com/t/86c6e0q2b)

```bash
# NOT YET IMPLEMENTED
cum folder list <space_id>
```

---

#### `folder create` - Create Folder
**Task ID**: [86c6e0q2h](https://app.clickup.com/t/86c6e0q2h)

```bash
# NOT YET IMPLEMENTED
cum folder create <space_id> --name "Folder name"
```

---

#### `folder show` - Show Folder Details
**Task ID**: [86c6e0q2p](https://app.clickup.com/t/86c6e0q2p)

```bash
# NOT YET IMPLEMENTED
cum folder show <folder_id>
```

---

## Docs Commands ✅

> **Status**: Implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q2q)

### `dlist` / `doc_list` - List Docs
**Task ID**: [86c6e0q2t](https://app.clickup.com/t/86c6e0q2t)

```bash
# List all docs in a workspace
cum dlist <workspace_id>
cum dl <workspace_id>          # Short alias
cum doc_list <workspace_id>    # Long alias
```

---

### `doc_create` - Create Doc
**Task ID**: [86c6e0q2u](https://app.clickup.com/t/86c6e0q2u)

```bash
# Create a new doc
cum doc_create <workspace_id> "Doc name"
cum dc <workspace_id> "Doc name"  # Short alias

# Create doc with initial pages
cum doc_create <workspace_id> "My Doc" --pages "Intro:Welcome!" "Setup"
```

---

### `doc_get` - Show Doc Details
**Task ID**: [86c6e0q2v](https://app.clickup.com/t/86c6e0q2v)

```bash
# Get doc and display pages
cum doc_get <workspace_id> <doc_id>
cum dg <workspace_id> <doc_id>  # Short alias

# Show content preview for each page
cum doc_get <workspace_id> <doc_id> --preview
```

---

### `doc_export` - Export Docs to Markdown

```bash
# Export all docs in workspace
cum doc_export <workspace_id> --output-dir ./output

# Export specific doc
cum doc_export <workspace_id> --doc-id <doc_id> --output-dir ./output

# Export with nested folder structure
cum doc_export <workspace_id> --nested --output-dir ./output
```

---

### `doc_import` - Import Markdown Files

```bash
# Import markdown files from directory to create docs
cum doc_import <workspace_id> ./input_dir

# Import single doc from directory
cum doc_import <workspace_id> ./input_dir --doc-name "My Doc"

# Import with nested structure preserved
cum doc_import <workspace_id> ./input_dir --nested --recursive
```

---

### Page Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q2w)

#### `page_list` - List Pages
**Task ID**: [86c6e0q2x](https://app.clickup.com/t/86c6e0q2x)

```bash
# List all pages in a doc
cum page_list <workspace_id> <doc_id>
cum pl <workspace_id> <doc_id>  # Short alias
```

---

#### `page_create` - Create Page
**Task ID**: [86c6e0q2z](https://app.clickup.com/t/86c6e0q2z)

```bash
# Create a new page in a doc
cum page_create <workspace_id> <doc_id> --name "Page name"
cum pc <workspace_id> <doc_id> --name "Page name"  # Short alias

# Create page with content
cum page_create <workspace_id> <doc_id> --name "Getting Started" --content "# Welcome"
```

---

#### `page_update` - Update Page Content
**Task ID**: [86c6e0q31](https://app.clickup.com/t/86c6e0q31)

```bash
# Update page content
cum page_update <workspace_id> <doc_id> <page_id> --content "New content"
cum pu <workspace_id> <doc_id> <page_id> --content "New content"  # Short alias

# Update page name
cum page_update <workspace_id> <doc_id> <page_id> --name "New Page Name"

# Update both name and content
cum page_update <workspace_id> <doc_id> <page_id> --name "Updated" --content "# Updated Content"
```

---

## Time Tracking Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q32)

### `time start` - Start Time Tracking
**Task ID**: [86c6e0q33](https://app.clickup.com/t/86c6e0q33)

```bash
# NOT YET IMPLEMENTED
cum time start <task_id>
```

---

### `time stop` - Stop Time Tracking
**Task ID**: [86c6e0q34](https://app.clickup.com/t/86c6e0q34)

```bash
# NOT YET IMPLEMENTED
cum time stop <task_id>
```

---

### `time list` - List Time Entries
**Task ID**: [86c6e0q35](https://app.clickup.com/t/86c6e0q35)

```bash
# NOT YET IMPLEMENTED
cum time list <task_id>
```

---

## View Management Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q36)

### `view list` - List Views
**Task ID**: [86c6e0q37](https://app.clickup.com/t/86c6e0q37)

```bash
# NOT YET IMPLEMENTED
cum view list <list_id>
```

---

### `view create` - Create View
**Task ID**: [86c6e0q39](https://app.clickup.com/t/86c6e0q39)

```bash
# NOT YET IMPLEMENTED
cum view create <list_id> --name "View name"
```

---

## Attachment Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q3a)

### `attachment upload` - Upload File
**Task ID**: [86c6e0q3b](https://app.clickup.com/t/86c6e0q3b)

```bash
# NOT YET IMPLEMENTED
cum attachment upload <task_id> <file_path>
```

---

### `attachment list` - List Attachments
**Task ID**: [86c6e0q3c](https://app.clickup.com/t/86c6e0q3c)

```bash
# NOT YET IMPLEMENTED
cum attachment list <task_id>
```

---

## Format Options

All view commands support these formatting options:

| Option | Description | Default |
|--------|-------------|---------|
| `--preset {minimal\|summary\|detailed\|full}` | Use a preset format configuration | None |
| `--colorize` | Force enable color output | Use config setting |
| `--no-colorize` | Force disable color output | Use config setting |
| `--show-ids` | Show task IDs | Hidden |
| `--show-tags` | Show task tags | Enabled |
| `--show-descriptions` | Show task descriptions | Hidden |
| `--show-dates` | Show task dates | Hidden |
| `--show-comments N` | Show N comments per task | 0 |
| `--include-completed` | Include completed tasks | Hidden |
| `--no-emoji` | Hide task type emojis | Enabled |

**Note**: Color output is controlled by the global `ansi` setting (default: disabled). Use `cum ansi enable` to enable colors globally, or use `--colorize`/`--no-colorize` flags to override per command.

## Presets

Presets provide quick formatting configurations:

### `minimal`
```bash
cum hierarchy <list_id> --preset minimal
```
- Shows: IDs, status, priority
- Hides: Tags, descriptions, dates, emojis

### `summary`
```bash
cum hierarchy <list_id> --preset summary
```
- Shows: Status, priority, tags
- Hides: IDs, descriptions, dates

### `detailed`
```bash
cum hierarchy <list_id> --preset detailed
```
- Shows: Status, priority, tags, descriptions, dates
- Hides: IDs

### `full`
```bash
cum hierarchy <list_id> --preset full
```
- Shows: Everything including IDs, tags, descriptions, dates, 5 comments

---

## Implementation Roadmap

Track the overall implementation progress: [CLI Command Implementation](https://app.clickup.com/t/86c6e0q06)

### Phase 1: View & Context (✅ Complete)
- ✅ Hierarchy view (defaults to full preset)
- ✅ Container view
- ✅ Flat view
- ✅ Filter view
- ✅ Detail view
- ✅ Stats view
- ✅ Demo mode
- ✅ Assigned tasks view (dependency difficulty sorting)
- ✅ Context management (set/show/clear)
- ✅ Status display with caching
- ✅ Animated ANSI output
- ✅ 3-letter status codes
- ✅ Configurable ANSI colors
- ✅ Default assignee configuration
- ✅ CLI alias (`cum`)

### Phase 2: Task Management (✅ Complete)
- ✅ Create tasks (with default assignee & file input support)
- ✅ Update tasks (with file input support)
- ✅ Delete tasks (with confirmation prompt)
- ✅ Assign/unassign users
- ✅ Set status (with subtask validation & multi-task support)
- ✅ Set priority (supports names & numbers)
- ✅ Manage tags (add/remove/set)

### Phase 3: Comments & Relationships (✅ Complete)
- ✅ Add/list/update/delete comments (with file input support)
- ✅ Task dependencies (waiting-on and blocking relationships)
- ✅ Task links (general task relationships)
- ✅ Create/delete checklists
- ✅ Manage checklist items

### Phase 4: Docs & Pages (✅ Complete)
- ✅ List/create/get docs
- ✅ Create/list/update pages
- ✅ Export docs to markdown (with nested structure support)
- ✅ Import markdown files to create docs (with nested structure support)

### Phase 5: Lists & Hierarchy (🚧 Planned)
- 🚧 List operations
- 🚧 Workspace/space/folder management

### Phase 5: Advanced Features (Mixed)
- ✅ Custom fields (fully implemented)
- ✅ Checklists (fully implemented)
- 🚧 Time tracking (planned)
- 🚧 View management (planned)
- 🚧 Attachments (planned)

---

## Tab Completion

The CLI supports tab completion for bash and zsh shells when `argcomplete` is installed.

### Installation

```bash
# Install argcomplete
pip install argcomplete

# Enable for bash
eval "$(register-python-argcomplete cum)"

# For persistent bash completion, add to ~/.bashrc:
echo 'eval "$(register-python-argcomplete cum)"' >> ~/.bashrc

# For zsh, add to ~/.zshrc:
autoload -U bashcompinit
bashcompinit
eval "$(register-python-argcomplete cum)"
```

### Features

- Complete command names (both full names and short aliases)
- Complete arguments and options
- Works with both `cum` and `clickup` commands

---

## Contributing

Want to help implement the planned features? Check out the [CLI Command Implementation task](https://app.clickup.com/t/86c6e0q06) in ClickUp to see what's next!

## License

See LICENSE file for details.
