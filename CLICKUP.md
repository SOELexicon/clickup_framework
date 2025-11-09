# ClickUp Framework CLI Guide

Complete command-line interface for the ClickUp Framework with beautiful hierarchical task displays and comprehensive task management.

> **Note**: This CLI is under active development. Commands marked with ✅ are fully implemented, while commands marked with 🚧 are planned for future releases. See the [Implementation Roadmap](#implementation-roadmap) for details.

## Table of Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Task Workflow Guide](docs/TASK_WORKFLOW_GUIDE.md) 📖
- [View Commands (Implemented)](#view-commands-implemented-)
- [Context Management (Implemented)](#context-management-implemented-)
- [Task Management Commands (Implemented)](#task-management-commands-implemented-)
- [Comment Commands (Planned)](#comment-commands-planned-)
- [Checklist Commands (Planned)](#checklist-commands-planned-)
- [Relationship Commands (Planned)](#relationship-commands-planned-)
- [Custom Field Commands (Planned)](#custom-field-commands-planned-)
- [List Commands (Planned)](#list-commands-planned-)
- [Workspace/Space/Folder Commands (Planned)](#workspacespacefolders-commands-planned-)
- [Docs Commands (Planned)](#docs-commands-planned-)
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

> **Status**: Partially implemented (4/7 commands complete)
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q0a)

### `task_create` - Create New Task ✅
**Task ID**: [86c6e0q0b](https://app.clickup.com/t/86c6e0q0b) | **Status**: 🚧 Planned

Create a new task with full options support.

```bash
cum task_create <list_id> "Task name" [options]

# Examples:
cum task_create current "Implement feature X"
cum task_create 901517404278 "Bug fix" --description "Fix login issue" --priority urgent
cum task_create current "New task" --status "in progress" --tags bug critical
cum task_create current "Subtask" --parent 86c6e0q06
```

**Options**:
- `--description TEXT` - Task description
- `--status STATUS` - Initial status
- `--priority {1|2|3|4|urgent|high|normal|low}` - Priority level
- `--tags TAG [TAG...]` - Tags to add
- `--assignees USER_ID [USER_ID...]` - User IDs to assign (defaults to configured default assignee)
- `--parent TASK_ID` - Parent task ID (creates subtask)

**Default Assignee**: Tasks are automatically assigned to the default assignee (68483025) unless `--assignees` is specified.

---

### `task_update` - Update Existing Task ✅
**Task ID**: [86c6e0q0d](https://app.clickup.com/t/86c6e0q0d) | **Status**: 🚧 Planned

Update an existing task's properties.

```bash
cum task_update <task_id> [options]

# Examples:
cum task_update current --name "Updated name"
cum task_update 86c6e0q06 --description "New description"
cum task_update current --status "complete" --priority high
```

**Options**:
- `--name TEXT` - Update task name
- `--description TEXT` - Update description
- `--status STATUS` - Update status
- `--priority {1|2|3|4|urgent|high|normal|low}` - Update priority

---

### `task_delete` - Delete Task 🚧
**Task ID**: [86c6e0q0f](https://app.clickup.com/t/86c6e0q0f) | **Status**: 🚧 Planned

```bash
# NOT YET IMPLEMENTED
cum task_delete <task_id>
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

## Comment Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q0n)

### `comment add` - Add Comment to Task
**Task ID**: [86c6e0q0p](https://app.clickup.com/t/86c6e0q0p)

```bash
# NOT YET IMPLEMENTED
cum comment add <task_id> --text "Comment text"
```

---

### `comment list` - List Task Comments
**Task ID**: [86c6e0q0r](https://app.clickup.com/t/86c6e0q0r)

```bash
# NOT YET IMPLEMENTED
cum comment list <task_id>
```

---

### `comment update` - Update Comment
**Task ID**: [86c6e0q0t](https://app.clickup.com/t/86c6e0q0t)

```bash
# NOT YET IMPLEMENTED
cum comment update <comment_id> --text "New text"
```

---

### `comment delete` - Delete Comment
**Task ID**: [86c6e0q0u](https://app.clickup.com/t/86c6e0q0u)

```bash
# NOT YET IMPLEMENTED
cum comment delete <comment_id>
```

---

## Checklist Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q0v)

### `checklist create` - Create Checklist
**Task ID**: [86c6e0q0w](https://app.clickup.com/t/86c6e0q0w)

```bash
# NOT YET IMPLEMENTED
cum checklist create <task_id> --name "Checklist name"
```

---

### `checklist delete` - Delete Checklist
**Task ID**: [86c6e0q0x](https://app.clickup.com/t/86c6e0q0x)

```bash
# NOT YET IMPLEMENTED
cum checklist delete <checklist_id>
```

---

### `checklist-item add` - Add Checklist Item
**Task ID**: [86c6e0q0z](https://app.clickup.com/t/86c6e0q0z)

```bash
# NOT YET IMPLEMENTED
cum checklist-item add <checklist_id> --name "Item name"
```

---

### `checklist-item update` - Update Checklist Item
**Task ID**: [86c6e0q10](https://app.clickup.com/t/86c6e0q10)

```bash
# NOT YET IMPLEMENTED
cum checklist-item update <item_id> [options]
```

---

### `checklist-item delete` - Delete Checklist Item
**Task ID**: [86c6e0q11](https://app.clickup.com/t/86c6e0q11)

```bash
# NOT YET IMPLEMENTED
cum checklist-item delete <item_id>
```

---

## Relationship Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q12)

### Dependency Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q14)

#### `task add-dependency` - Add Task Dependency
**Task ID**: [86c6e0q16](https://app.clickup.com/t/86c6e0q16)

```bash
# NOT YET IMPLEMENTED
cum task add-dependency <task_id> --waiting-on <depends_on_task_id>
cum task add-dependency <task_id> --blocking <blocked_task_id>
```

---

#### `task remove-dependency` - Remove Dependency
**Task ID**: [86c6e0q19](https://app.clickup.com/t/86c6e0q19)

```bash
# NOT YET IMPLEMENTED
cum task remove-dependency <task_id> <dependency_id>
```

---

### Link Commands

**Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1a)

#### `task add-link` - Link Two Tasks
**Task ID**: [86c6e0q1c](https://app.clickup.com/t/86c6e0q1c)

```bash
# NOT YET IMPLEMENTED
cum task add-link <task_id> <linked_task_id>
```

---

#### `task remove-link` - Unlink Tasks
**Task ID**: [86c6e0q1d](https://app.clickup.com/t/86c6e0q1d)

```bash
# NOT YET IMPLEMENTED
cum task remove-link <task_id> <link_id>
```

---

## Custom Field Commands (Planned) 🚧

> **Status**: Not yet implemented
> **Tracking**: [ClickUp Task](https://app.clickup.com/t/86c6e0q1e)

### `custom-field set` - Set Custom Field Value
**Task ID**: [86c6e0q1f](https://app.clickup.com/t/86c6e0q1f)

```bash
# NOT YET IMPLEMENTED
cum custom-field set <task_id> <field_id> <value>
```

---

### `custom-field remove` - Remove Custom Field
**Task ID**: [86c6e0q1g](https://app.clickup.com/t/86c6e0q1g)

```bash
# NOT YET IMPLEMENTED
cum custom-field remove <task_id> <field_id>
```

---

### `custom-field list` - List Available Fields
**Task ID**: [86c6e0q1h](https://app.clickup.com/t/86c6e0q1h)

```bash
# NOT YET IMPLEMENTED
cum custom-field list <list_id>
```

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

### Phase 2: Task Management (⚡ In Progress - 57% Complete)
- ✅ Create tasks (with default assignee)
- ✅ Update tasks
- 🚧 Delete tasks
- ✅ Assign/unassign users
- ✅ Set status (with subtask validation & multi-task support)
- ✅ Set priority (supports names & numbers)
- ✅ Manage tags (add/remove/set)

### Phase 3: Comments & Checklists (🚧 Planned)
- 🚧 Add/list/update/delete comments
- 🚧 Create/delete checklists
- 🚧 Manage checklist items

### Phase 4: Relationships & Fields (🚧 Planned)
- 🚧 Task dependencies
- 🚧 Task links
- 🚧 Custom fields

### Phase 5: Lists & Hierarchy (🚧 Planned)
- 🚧 List operations
- 🚧 Workspace/space/folder management

### Phase 6: Advanced Features (🚧 Planned)
- 🚧 Docs & pages
- 🚧 Time tracking
- 🚧 View management
- 🚧 Attachments

---

## Contributing

Want to help implement the planned features? Check out the [CLI Command Implementation task](https://app.clickup.com/t/86c6e0q06) in ClickUp to see what's next!

## License

See LICENSE file for details.
