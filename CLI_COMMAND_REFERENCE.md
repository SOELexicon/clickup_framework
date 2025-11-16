# ClickUp Framework CLI - Complete Command Reference

## Overview
The ClickUp Framework CLI uses **argparse** (not Click) for command parsing. Commands are discovered dynamically from the `commands/` directory using a plugin-based system where each command module must define a `register_command(subparsers)` function.

## Main Entry Points

### CLI Entry Point
- **File**: `/home/user/clickup_framework/clickup_framework/cli.py`
- **Main Function**: `main()` (line 467)
- **Module Entry**: `/home/user/clickup_framework/clickup_framework/__main__.py`
- **Parser Type**: `ImprovedArgumentParser` (custom argparse.ArgumentParser extension)

### Command Discovery
- **Location**: `/home/user/clickup_framework/clickup_framework/commands/__init__.py`
- **Functions**:
  - `discover_commands()` - Discovers all command modules with `register_command` function
  - `register_all_commands(subparsers)` - Registers all discovered commands (line 53)
  - Auto-discovers from all `.py` files in `commands/` directory (skips `_*` and `utils.py`)

### Help/Command Tree Display
- **File**: `/home/user/clickup_framework/clickup_framework/cli.py`
- **Function**: `show_command_tree()` (line 320)
- **Triggered**: When no command is specified (lines 536-538)
- **Features**:
  - Displays commands in organized categories
  - Shows aliases, arguments, and descriptions
  - Uses ANSI colors with gradient animation
  - Provides quick examples

## Complete Command List (37 Total Commands + Subcommands)

### 📊 View Commands (9 commands)

#### 1. hierarchy / h / list / ls / l
**File**: `commands/hierarchy.py` (line 499)
- **Aliases**: `h`, `list`, `ls`, `l`
- **Description**: Display tasks in hierarchical parent-child view
- **Arguments**:
  - `list_id` (optional): Space, folder, list, or task ID
  - `--all`: Show all tasks from entire workspace
  - `--header <text>`: Custom header text
  - `--depth N`: Limit hierarchy display to N levels
  - `--preset [minimal|summary|detailed|full]`: Format preset (default: full)
  - `--colorize/--no-colorize`: Enable/disable colors
  - `--show-ids`: Show task IDs
  - `--show-tags`: Show tags (default: true)
  - `--show-descriptions`: Show descriptions
  - `-d, --full-descriptions`: Full descriptions without truncation
  - `--show-dates`: Show task dates
  - `--show-comments N`: Show N comments per task
  - `--include-completed`: Include completed tasks
  - `--no-emoji`: Hide task type emojis

#### 2. flat / f
**File**: `commands/flat.py` (line 48)
- **Aliases**: `f`
- **Description**: Display tasks in flat list format
- **Arguments**:
  - `list_id` (required): ClickUp list ID or task ID
  - `--header <text>`: Custom header text
  - Format options (same as hierarchy)

#### 3. clist / c / container
**File**: `commands/container.py` (line 48)
- **Aliases**: `c`, `container`
- **Description**: Display tasks by container hierarchy (Space → Folder → List)
- **Arguments**:
  - `list_id` (required): ClickUp list ID or task ID
  - Format options (same as hierarchy)

#### 4. filter / fil
**File**: `commands/filter.py` (line 56)
- **Aliases**: `fil`
- **Description**: Display filtered tasks by status/priority/tags/assignee
- **Arguments**:
  - `list_id` (required): ClickUp list ID or task ID
  - `--status <status>`: Filter by status
  - `--priority <number>`: Filter by priority (1-4)
  - `--tags <tag1> <tag2>`: Filter by tags
  - `--assignee <user_id>`: Filter by assignee
  - `--view-mode [hierarchy|container|flat]`: Display mode (default: hierarchy)
  - Format options

#### 5. detail / d
**File**: `commands/detail.py` (line 60)
- **Aliases**: `d`
- **Description**: Show comprehensive task details with relationships
- **Arguments**:
  - `task_id` (required): ClickUp task ID
  - `list_id` (optional): List ID for relationship context
  - Format options

#### 6. stats / st
**File**: `commands/stats.py` (line 166)
- **Aliases**: `st`
- **Description**: Display aggregate statistics for tasks in a list
- **Arguments**:
  - `list_id` (required): ClickUp list ID
  - Format options

#### 7. assigned / a
**File**: `commands/assigned_command.py` (line 332)
- **Aliases**: `a`
- **Description**: Show tasks assigned to user, sorted by dependency difficulty
- **Arguments**:
  - `--user-id <id>`: User ID (defaults to configured default assignee)
  - `--team-id <id>`: Team/workspace ID (defaults to current workspace)
  - `--include-completed`: Include completed tasks
  - `--show-closed-only`: Show ONLY closed tasks

#### 8. demo
**File**: `commands/demo.py` (line 73)
- **Description**: View demo output with sample data (no API required)
- **Arguments**:
  - `--mode [hierarchy|container|flat|stats|detail]`: View mode (default: hierarchy)
  - Format options

---

### ✅ Task Management (15 commands)

#### 1. task_create / tc
**File**: `commands/task_commands.py` (line 809)
- **Aliases**: `tc`
- **Description**: Create new task
- **Arguments**:
  - `name` (required): Task name
  - `--list <list_id|current>`: List ID (or use --parent)
  - `--parent <task_id>`: Parent task ID (creates subtask)
  - `--description <text>`: Task description
  - `--description-file <path>`: Read description from file
  - `--status <status>`: Task status (with smart mapping)
  - `--priority [1-4|urgent|high|normal|low]`: Task priority
  - `--tags <tag1> <tag2>`: Task tags
  - `--assignees <id1> <id2>`: Assignee user IDs
  - `--checklist-template <name>`: Apply checklist template
  - `--clone-checklists-from <task_id>`: Clone checklists from another task
  - `--custom-task-ids`: Custom task IDs
  - `--check-required-custom-fields`: Validate required custom fields

#### 2. task_update / tu
**File**: `commands/task_commands.py` (line 836)
- **Aliases**: `tu`
- **Description**: Update task fields
- **Arguments**:
  - `task_id` (required): Task ID
  - `--name <text>`: New task name
  - `--description <text>`: New description
  - `--description-file <path>`: Read description from file
  - `--status <status>`: New status
  - `--priority [1-4|urgent|high|normal|low]`: New priority
  - `--parent <task_id>`: New parent task
  - `--add-tags <tag1> <tag2>`: Add tags
  - `--remove-tags <tag1> <tag2>`: Remove tags

#### 3. task_delete / td
**File**: `commands/task_commands.py` (line 851)
- **Aliases**: `td`
- **Description**: Delete task with confirmation
- **Arguments**:
  - `task_id` (required): Task ID
  - `--force`: Skip confirmation prompt

#### 4. task_assign / ta
**File**: `commands/task_commands.py` (line 859)
- **Aliases**: `ta`
- **Description**: Assign one or more users to task
- **Arguments**:
  - `task_id` (required): Task ID
  - `assignee_ids` (required): One or more user IDs

#### 5. task_unassign / tua
**File**: `commands/task_commands.py` (line 866)
- **Aliases**: `tua`
- **Description**: Remove assignees from task
- **Arguments**:
  - `task_id` (required): Task ID
  - `assignee_ids` (required): One or more user IDs

#### 6. task_set_status / tss
**File**: `commands/task_commands.py` (line 873)
- **Aliases**: `tss`
- **Description**: Set task status with subtask validation
- **Arguments**:
  - `task_ids` (required): One or more task IDs
  - `status` (required): Status to set

#### 7. task_set_priority / tsp
**File**: `commands/task_commands.py` (line 884)
- **Aliases**: `tsp`
- **Description**: Set task priority
- **Arguments**:
  - `task_id` (required): Task ID
  - `priority` (required): Priority (1-4 or urgent/high/normal/low)

#### 8. task_set_tags / tst
**File**: `commands/task_commands.py` (line 891)
- **Aliases**: `tst`
- **Description**: Manage task tags
- **Arguments**:
  - `task_id` (required): Task ID
  - `--add <tag1> <tag2>`: Add tags
  - `--remove <tag1> <tag2>`: Remove tags
  - `--set <tag1> <tag2>`: Replace all tags

#### 9. task_add_dependency / tad
**File**: `commands/task_commands.py` (line 901)
- **Aliases**: `tad`
- **Description**: Add task dependency relationship
- **Arguments**:
  - `task_id` (required): Task ID
  - `--waiting-on <task_id>`: This task waits on another
  - `--blocking <task_id>`: This task blocks another

#### 10. task_remove_dependency / trd
**File**: `commands/task_commands.py` (line 911)
- **Aliases**: `trd`
- **Description**: Remove task dependency relationship
- **Arguments**:
  - `task_id` (required): Task ID
  - `--waiting-on <task_id>`: Remove waiting-on relationship
  - `--blocking <task_id>`: Remove blocking relationship

#### 11. task_add_link / tal
**File**: `commands/task_commands.py` (line 921)
- **Aliases**: `tal`
- **Description**: Link two tasks together
- **Arguments**:
  - `task_id` (required): Task ID
  - `linked_task_id` (required): Task to link to

#### 12. task_remove_link / trl
**File**: `commands/task_commands.py` (line 930)
- **Aliases**: `trl`
- **Description**: Remove link between two tasks
- **Arguments**:
  - `task_id` (required): Task ID
  - `linked_task_id` (required): Task to unlink from

---

### 💬 Comment Management (4 commands)

#### 1. comment_add / ca
**File**: `commands/comment_commands.py` (line 197)
- **Aliases**: `ca`
- **Description**: Add a comment to a task
- **Arguments**:
  - `task_id` (required): Task ID
  - `text` (required): Comment text
  - `--comment-file <path>`: Read comment from file

#### 2. comment_list / cl
**File**: `commands/comment_commands.py` (line 205)
- **Aliases**: `cl`
- **Description**: List comments on a task
- **Arguments**:
  - `task_id` (required): Task ID
  - `--limit N`: Limit to N comments

#### 3. comment_update / cu
**File**: `commands/comment_commands.py` (line 214)
- **Aliases**: `cu`
- **Description**: Update an existing comment
- **Arguments**:
  - `comment_id` (required): Comment ID
  - `text` (required): New comment text

#### 4. comment_delete / cd
**File**: `commands/comment_commands.py` (line 222)
- **Aliases**: `cd`
- **Description**: Delete a comment
- **Arguments**:
  - `comment_id` (required): Comment ID
  - `--force`: Skip confirmation prompt

---

### 📄 Docs Management (9 commands)

#### 1. dlist / dl / doc_list
**File**: `commands/doc_commands.py` (line 647)
- **Aliases**: `dl`, `doc_list`
- **Description**: List all docs in a workspace
- **Arguments**:
  - `workspace_id` (required): Workspace ID

#### 2. doc_get / dg
**File**: `commands/doc_commands.py` (line 653)
- **Aliases**: `dg`
- **Description**: Get doc and display pages
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `doc_id` (required): Doc ID
  - `--preview`: Show preview mode

#### 3. doc_create / dc
**File**: `commands/doc_commands.py` (line 662)
- **Aliases**: `dc`
- **Description**: Create new doc with optional pages
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `name` (required): Doc name
  - `--pages <text1> <text2>`: Initial pages

#### 4. doc_update / du
**File**: `commands/doc_commands.py` (line 671)
- **Aliases**: `du`
- **Description**: Update a page in a doc
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `doc_id` (required): Doc ID
  - `page_id` (required): Page ID
  - Format options

#### 5. doc_export / de
**File**: `commands/doc_commands.py` (line 681)
- **Aliases**: `de`
- **Description**: Export docs to markdown files
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `--doc-id <id>`: Specific doc to export
  - `--output-dir <dir>`: Output directory
  - `--nested`: Use nested directory structure

#### 6. doc_import / di
**File**: `commands/doc_commands.py` (line 693)
- **Aliases**: `di`
- **Description**: Import markdown files to create docs
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `input_dir` (required): Input directory
  - `--doc-name <name>`: Doc name
  - `--nested`: Handle nested directories

#### 7. page_list / pl
**File**: `commands/doc_commands.py` (line 706)
- **Aliases**: `pl`
- **Description**: List all pages in a doc
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `doc_id` (required): Doc ID

#### 8. page_create / pc
**File**: `commands/doc_commands.py` (line 713)
- **Aliases**: `pc`
- **Description**: Create a new page in a doc
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `doc_id` (required): Doc ID
  - `--name <text>` (required): Page name
  - `--content <text>`: Page content

#### 9. page_update / pu
**File**: `commands/doc_commands.py` (line 722)
- **Aliases**: `pu`
- **Description**: Update a page in a doc
- **Arguments**:
  - `workspace_id` (required): Workspace ID
  - `doc_id` (required): Doc ID
  - `page_id` (required): Page ID
  - `--name <text>`: New page name
  - `--content <text>`: New content

---

### 🎯 Context Management (3 commands)

#### 1. set_current / set
**File**: `commands/set_current.py` (line 45)
- **Aliases**: `set`
- **Description**: Set current resource context
- **Arguments**:
  - `resource_type` (required): [task|list|space|folder|workspace|team|assignee|token]
  - `resource_id` (required): ID or value of resource

#### 2. show_current / show
**File**: `commands/show_current.py` (line 106)
- **Aliases**: `show`
- **Description**: Display current context with animated box
- **Arguments**: None

#### 3. clear_current / clear
**File**: `commands/clear_current.py` (line 39)
- **Aliases**: `clear`
- **Description**: Clear context resources
- **Arguments**:
  - `resource_type` (optional): [task|list|space|folder|workspace|team|token] (omit to clear all)

---

### 🛠️ Utility Commands (1 command)

#### 1. diff
**File**: `commands/diff_command.py` (line 87)
- **Aliases**: None
- **Description**: Compare two files or strings and display unified diff
- **Usage Modes**:
  1. **File comparison**: `cum diff <file1> <file2>`
  2. **String comparison**: `cum diff --old "text1" --new "text2"`
- **Arguments**:
  - `file1` (optional): First file path to compare
  - `file2` (optional): Second file path to compare
  - `--old TEXT`: Old text string to compare
  - `--new TEXT`: New text string to compare
  - `--old-label LABEL`: Label for old text (default: "old")
  - `--new-label LABEL`: Label for new text (default: "new")
  - `--context N`, `-c N`: Number of context lines to show (default: 3)
  - `--color`: Force colored output
  - `--no-color`: Disable colored output
- **Examples**:
  ```bash
  # Compare two files
  cum diff file1.txt file2.txt

  # Compare with more context lines
  cum diff file1.txt file2.txt --context 5

  # Compare two strings
  cum diff --old "Hello World" --new "Hello ClickUp"

  # Disable color output
  cum diff file1.txt file2.txt --no-color
  ```
- **Notes**:
  - Uses Python's `difflib.unified_diff()` for diff generation
  - Respects ANSI color settings from context manager by default
  - Color scheme: additions (green), deletions (red), context (default)
  - Must specify either file paths OR --old/--new strings (not both)

---

### 🎨 Configuration Commands (2 commands)

#### 1. ansi
**File**: `commands/ansi.py` (line 22)
- **Description**: Enable/disable ANSI color output
- **Arguments**:
  - `action` (required): [enable|disable|status]

#### 2. update
**File**: `commands/update_command.py` (line 781)
- **Subcommands**:
  - **cum**: Update cum tool from git and reinstall
  - **version**: Bump project version and create git tag
    - `--major/--minor/--patch`: Version bump type
    - `[VERSION]`: Specific version (optional)

---

### 🔄 Advanced Features

#### Checklist Management (7 commands)
**File**: `commands/checklist_commands.py` (line 457)

1. **checklist / chk** - Main checklist command
   - **Aliases**: `chk`

2. **checklist create** - Create checklist on task
   - `--name <text>`: Checklist name
   - `--task-id <id>`: Task ID
   - `--verbose`: Verbose output

3. **checklist delete / rm** - Delete checklist
   - **Aliases**: `rm`
   - `--checklist-id <id>`: Checklist ID
   - `--force`: Skip confirmation

4. **checklist update** - Update checklist
   - `--name <text>`: New name
   - `--position <n>`: New position

5. **checklist item-add / add** - Add checklist item
   - **Aliases**: `add`

6. **checklist item-update / update-item** - Update item
   - **Aliases**: `update-item`

7. **checklist item-delete / delete-item / rm-item** - Delete item
   - **Aliases**: `delete-item`, `rm-item`

---

#### Custom Fields Management (3 commands)
**File**: `commands/custom_field_commands.py` (line 495)

1. **custom_field / cf** - Main custom field command
   - **Aliases**: `cf`

2. **custom_field get** - Get custom field value
3. **custom_field set** - Set custom field value
4. **custom_field delete / rm** - Delete field value
   - **Aliases**: `rm`

---

#### Parent Task Auto-Update Automation (6 commands)
**File**: `commands/automation_commands.py` (line 126)

1. **parent_auto_update / pau** - Main automation command
   - **Aliases**: `pau`

2. **parent_auto_update status** - Show automation configuration
3. **parent_auto_update enable** - Enable automation
4. **parent_auto_update disable** - Disable automation
5. **parent_auto_update config** - Update configuration
   - `--key <key>`: Config key
   - `--value <value>`: Config value

6. **parent_auto_update add-trigger** - Add status trigger
7. **parent_auto_update remove-trigger** - Remove status trigger

---

#### Git Overflow Workflow (1 command)
**File**: `commands/git_overflow_command.py` (line 211)

**overflow**
- **Description**: Automated Git + ClickUp workflow integration
- **Arguments**:
  - `message` (required): Commit message
  - `--task <id>`: Task ID (optional, defaults to current)
  - `--type [direct|pr|wip|hotfix|merge]`: Workflow type (default: direct)
  - `--no-push`: Don't push to remote
  - `--no-clickup`: Don't update ClickUp
  - `--status <status>`: Update task status
  - `--priority <priority>`: Update task priority
  - `--tags <tag1> <tag2>`: Update task tags
  - `--dry-run`: Test without making changes

---

## Help Text Generation

### Primary Sources

1. **Built-in Argument Parser Help**
   - Each command's `help=` parameter in `add_parser()` calls
   - Accessed via: `cum <command> --help` or `cum <command> -h`
   - Standard argparse output

2. **Dynamic Command Tree Display**
   - Function: `show_command_tree()` in `/home/user/clickup_framework/cli.py` (line 320)
   - Triggered: When running `cum` with no arguments
   - Source: Hardcoded command dictionary in lines 343-396
   - Features: Animated gradient header, organized by category, includes examples

3. **Common Arguments Documentation**
   - File: `/home/user/clickup_framework/commands/utils.py`
   - Function: `add_common_args()` 
   - Applied to: Display commands (hierarchy, list, flat, container, filter, detail, stats)
   - Provides: Format options, color settings, preset formats

### Help Text Structure

```
Accessed via: cum <command> -h or cum <command> --help
Generated by: argparse ArgumentParser
Customized in: Individual register_command() functions
```

---

## Recently Added/Modified Commands

Based on git history (last 5 commits touching commands):

1. **checklist_commands.py** - Checklist template system with local storage and cloning (commit 9b3a794)
2. **comment_commands.py** - Comment management enhancements
3. **git_overflow_command.py** - Overflow workflow updates
4. **task_commands.py** - Task command improvements and automation enhancements

---

## Command Discovery Mechanism

### Process Flow

1. **CLI Initialization** → `/home/user/clickup_framework/cli.py:main()` (line 467)
2. **Parser Creation** → Creates `ImprovedArgumentParser` with subparsers
3. **Command Discovery** → Calls `register_all_commands(subparsers)` (line 526)
4. **Module Loading** → `commands/__init__.py:discover_commands()` iterates `commands/` directory
5. **Registration** → Each module's `register_command(subparsers)` function is called
6. **Parsing** → argparse parses command-line arguments
7. **Execution** → Calls command function set via `parser.set_defaults(func=...)`

### File Structure

```
clickup_framework/
├── cli.py                              # Main CLI entry point
├── __main__.py                         # Module entry point
└── commands/
    ├── __init__.py                     # Command discovery logic
    ├── hierarchy.py                    # Hierarchy view command
    ├── task_commands.py                # Task management (12 commands)
    ├── comment_commands.py             # Comment management (4 commands)
    ├── doc_commands.py                 # Document management (9 commands)
    ├── assigned_command.py             # Assigned tasks view
    ├── flat.py                         # Flat list view
    ├── filter.py                       # Filtered view
    ├── container.py                    # Container view
    ├── detail.py                       # Detail view
    ├── stats.py                        # Statistics view
    ├── demo.py                         # Demo mode
    ├── set_current.py                  # Context setting
    ├── show_current.py                 # Context display
    ├── clear_current.py                # Context clearing
    ├── ansi.py                         # ANSI color configuration
    ├── checklist_commands.py           # Checklist management (7 subcommands)
    ├── custom_field_commands.py        # Custom field management (3 subcommands)
    ├── automation_commands.py          # Parent task automation (6 subcommands)
    ├── git_overflow_command.py         # Git + ClickUp workflow
    ├── update_command.py               # Update functionality (2 subcommands)
    └── utils.py                        # Command utilities
```

---

## Summary Statistics

- **Total Commands**: 37 top-level commands
- **Subcommands**: 28+ (checklist, custom_field, automation, doc, update operations)
- **Aliases**: 40+ defined
- **Command Files**: 23 Python modules
- **Auto-discovery**: Yes (plugin-based system)
- **Help Generation**: argparse + custom command tree display
- **Command Groups**: 9 main categories
  - View Commands (9)
  - Task Management (15)
  - Comment Management (4)
  - Docs Management (9)
  - Context Management (3)
  - Utility Commands (1)
  - Configuration (2)
  - Checklists (7 subcommands)
  - Advanced Features (custom fields, automation, git overflow)
