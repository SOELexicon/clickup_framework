# ClickUp Framework

A modular, token-efficient framework for ClickUp API interactions achieving **90-95% token reduction** through intelligent formatting and progressive disclosure.
[![ClickUp Framework Tests](https://github.com/SOELexicon/clickup_framework/actions/workflows/test.yml/badge.svg)](https://github.com/SOELexicon/clickup_framework/actions/workflows/test.yml)

## Status

**Version:** 1.0.0-alpha
**Phase:** 3 (Resource APIs) - Complete ✅
[![Test and Generate Display Screenshots](https://github.com/SOELexicon/clickup_framework/actions/workflows/test-and-screenshot.yml/badge.svg)](https://github.com/SOELexicon/clickup_framework/actions/workflows/test-and-screenshot.yml)
### Implementation Progress


- [x] **Phase 1:** Core Client Library (Week 1) - COMPLETE ✅
  - [x] Core client class with authentication
  - [x] Rate limiting (token bucket algorithm)
  - [x] Error handling and retries
  - [x] All ClickUp API endpoints
  - [x] Tested with real API

- [x] **Phase 2:** Formatters Library (Week 2) - COMPLETE ✅
  - [x] Task formatter with 4 detail levels
  - [x] Comment formatter with 4 detail levels
  - [x] Time entry formatter with 4 detail levels
  - [x] Utility functions (datetime, text)
  - [x] Benchmarked: **98% token reduction achieved**
  - [x] Tested with real API responses
  - [ ] List formatter (future)
  - [ ] Workspace formatter (future)

- [x] **Phase 3:** Resource APIs (Week 3) - COMPLETE ✅
  - [x] **TasksAPI:** Task CRUD, comments, checklists, custom fields, relationships
    - [x] Implementing GET/retrieve operations (get, get_list_tasks, get_team_tasks)
    - [x] Implementing CREATE operations (create)
    - [x] Implementing UPDATE operations (update, update_status, update_priority)
    - [x] Implementing DELETE operations (delete)
    - [ ] Adding filtering and search capabilities (advanced filters)
    - [x] Integrating automatic formatting with detail levels (minimal, summary, detailed, full)
    - [x] Adding convenience methods (assign, unassign, status updates)
    - [x] Adding comment operations (add_comment, get_comments)
    - [x] Adding checklist operations (add_checklist, add_checklist_item)
    - [x] Adding custom field operations (set_custom_field, remove_custom_field)
    - [x] Adding dependency operations (add_dependency_waiting_on, add_dependency_blocking, remove_dependency)
    - [x] Adding link operations (add_link, remove_link)
    - [x] Adding custom relationship operations (set_relationship_field)
    - [x] Testing with real API data
    - [x] Error handling and edge cases
    - [x] View-before-modify safeguards for update/delete
    - [x] Duplicate detection for create operations

  - [x] **ListsAPI:** List management and task queries
    - [x] Implementing GET/retrieve operations (get, get_tasks)
    - [x] Implementing CREATE operations (create)
    - [x] Implementing UPDATE operations (update)
    - [ ] Implementing DELETE operations (delete)
    - [x] Adding filtering capabilities (archived, include_closed)
    - [ ] Integrating automatic formatting with detail levels
    - [x] Adding convenience methods (get_custom_fields)
    - [x] Testing with real API data
    - [x] Error handling and edge cases

  - [x] **WorkspacesAPI:** Workspace, space, folder, search operations
    - [x] Implementing GET/retrieve operations (get_hierarchy, get_space, get_spaces, get_folder, get_tags)
    - [x] Implementing CREATE operations (create_space, create_folder, create_tag)
    - [x] Implementing UPDATE operations (update_space, update_folder)
    - [x] Implementing DELETE operations (delete_space)
    - [x] Adding search capabilities (search)
    - [ ] Integrating automatic formatting with detail levels
    - [x] Adding convenience methods for hierarchy navigation
    - [x] Testing with real API data
    - [x] Error handling and edge cases

  - [x] **TimeAPI:** Time tracking with automatic formatting
    - [x] Implementing GET/retrieve operations (get_entries, get_task_time, get_user_time)
    - [x] Implementing CREATE operations (create_entry)
    - [ ] Implementing UPDATE operations (update_entry)
    - [ ] Implementing DELETE operations (delete_entry)
    - [x] Adding filtering capabilities (by date, assignee, task)
    - [x] Integrating automatic formatting with detail levels (minimal, summary, detailed, full)
    - [x] Adding convenience methods (get_task_time, get_user_time)
    - [x] Testing with real API data
    - [x] Error handling and edge cases

  - [x] **DocsAPI:** Document and page management
    - [x] Implementing GET/retrieve operations (get_workspace_docs, get_doc, get_doc_pages, get_page)
    - [x] Implementing CREATE operations (create_doc, create_page)
    - [x] Implementing UPDATE operations (update_page)
    - [ ] Implementing DELETE operations (delete_doc, delete_page)
    - [ ] Adding search capabilities for docs
    - [ ] Integrating automatic formatting with detail levels
    - [x] Adding convenience methods (create_doc_with_pages)
    - [x] Testing with real API data
    - [x] Error handling and edge cases

- [ ] **Phase 4:** Skill Integration (Week 4)
  - [x] **Context Management System**
    - [x] Implement persistent JSON context storage (~/.clickup_context.json)
    - [x] Add set_current functionality for tasks, lists, spaces
    - [x] Add CLI commands for context management (set_current, clear_current, show_current)
    - [x] Integrate context resolution in existing CLI commands
    - [x] Add "current" keyword support for task/list/space IDs
    - [x] Error handling for missing context
    - [x] Security considerations (no API tokens in context file)
    - [x] Unit tests for context loading/saving
    - [x] Documentation and examples

  - [ ] **Skill-Based Task Automation**
    - [ ] Define skill interface for task operations
    - [ ] Implement task creation workflows
    - [ ] Implement task update workflows
    - [ ] Implement task search and filtering workflows
    - [ ] Add intelligent task suggestions
    - [ ] Integration with LLM for natural language commands
    - [ ] Error recovery and rollback mechanisms

  - [ ] **Advanced Display Features**
    - [ ] Gantt chart visualization
    - [ ] Dependency graph visualization
    - [ ] Burndown charts and progress tracking
    - [ ] Custom view templates
    - [ ] Export to various formats (PDF, HTML, Markdown)

  - [ ] **Workflow Automation**
    - [ ] Task templates and presets
    - [ ] Bulk operations (batch create, update, delete)
    - [ ] Automated task assignments
    - [ ] Status transition rules
    - [ ] Custom field automation
    - [ ] Integration with webhooks

- [ ] **Phase 5:** Documentation & Release (Week 5)
  - [ ] Complete API documentation
  - [ ] Tutorial and getting started guide
  - [ ] Best practices and patterns
  - [ ] Migration guide from ClickupCLI
  - [ ] Performance benchmarks and optimization guide
  - [ ] Security and authentication guide
  - [ ] Example projects and use cases
  - [ ] Release preparation (versioning, changelog, PyPI)

## Installation

```bash
# Install the package
pip install -e .

# Or add framework to Python path
export PYTHONPATH="/home/user/Skills:$PYTHONPATH"
```

### Tab Autocomplete (Optional)

Enable tab completion for `cum` and `clickup` commands to get command suggestions and argument completion:

**What you get:**
- Tab completion for all commands: `cum <TAB>` shows all available commands
- Prefix matching: `cum task_<TAB>` shows all task commands
- Argument completion: `cum hierarchy <TAB>` shows available options

#### Linux / macOS / WSL

```bash
# Run the setup script (bash or zsh)
./enable-completion.sh

# Reload your shell configuration
source ~/.bashrc  # for bash
source ~/.zshrc   # for zsh

# Or restart your terminal
```

**Manual setup for bash** (`~/.bashrc`):
```bash
eval "$(register-python-argcomplete cum)"
eval "$(register-python-argcomplete clickup)"
```

**Manual setup for zsh** (`~/.zshrc`):
```bash
autoload -U bashcompinit
bashcompinit
eval "$(register-python-argcomplete cum)"
eval "$(register-python-argcomplete clickup)"
```

#### Windows

**PowerShell** (recommended):
```powershell
# Run the setup script
.\enable-completion.ps1

# Reload your profile
. $PROFILE

# Or restart PowerShell
```

**Git Bash on Windows**:
```bash
# Use the bash setup script
./enable-completion.sh

# Reload configuration
source ~/.bashrc
```

### Shell Aliases (Optional)

Set up convenient shell aliases for frequently used commands:

**What you get:**
- `cud` - Quick shortcut for `cum detail` (shorter than `cum d`)
- `cumd` - Alternative for `cum detail`
- `cum task` - Another alias for `cum detail` (available by default)

#### Linux / macOS / WSL

```bash
# Run the alias setup script (bash or zsh)
./enable-aliases.sh

# Reload your shell configuration
source ~/.bashrc  # for bash
source ~/.zshrc   # for zsh

# Or restart your terminal
```

**Manual setup for bash** (`~/.bashrc`):
```bash
alias cud='cum detail'
alias cumd='cum detail'
```

**Manual setup for zsh** (`~/.zshrc`):
```bash
alias cud='cum detail'
alias cumd='cum detail'
```

**Usage examples:**
```bash
cud 86c6j1vr6        # View task details (short form)
cumd current         # View current task details
cum task 86c6j1vr6   # Use built-in 'task' alias
```

## Quick Start

### Command-Line Interface (NEW! ✨)

The framework includes a powerful CLI for all display operations:

```bash
# View available commands
./clickup --help
python -m clickup_framework --help

# Try demo mode (no API key required)
./clickup demo --mode hierarchy
./clickup demo --mode detail --preset detailed

# Fetch and display tasks from ClickUp
cum h <list_id>              # hierarchy view (short code)
cum c <list_id>              # container view (short code)
cum d <task_id> <list_id>    # detail view (short code)

# Filter tasks
cum fil <list_id> --status "in progress"
cum fil <list_id> --priority 1 --tags backend api

# Task management
cum tc "New Task" --list <list_id>  # create task (name comes first!)
cum tss <task_id> "in progress"     # set status
cum ca <task_id> "Great work!"      # add comment

# Customize output
cum h <list_id> --show-ids --show-descriptions --preset detailed
cum c <list_id> --no-colorize --include-completed

# View statistics
cum st <list_id>
```

**CLI Commands:**

*Display Commands:*
- `hierarchy` / `h` / `list` / `ls` / `l` - Display tasks in hierarchical parent-child view
- `clist` / `c` / `container` - Display tasks by workspace → space → folder → list
- `flat` / `f` - Display tasks in simple flat list
- `filter` / `fil` - Display filtered tasks with custom criteria
- `detail` / `d` - Show comprehensive single-task view with relationships
- `stats` / `st` - Display task statistics and counts
- `assigned` / `a` - Show assigned tasks sorted by difficulty
- `demo` - Show examples with sample data (no API required)

*Context Management:*
- `set_current` / `set` - Set current resource (task, list, space, folder, workspace, assignee)
- `show_current` / `show` - Display current context
- `clear_current` / `clear` - Clear current context (specific resource or all)
- `ansi` - Enable/disable ANSI color output

*Task Management:*
- `task_create` / `tc` - Create new task
- `task_update` / `tu` - Update task properties
- `task_delete` / `td` - Delete task
- `task_assign` / `ta` - Assign users to task
- `task_unassign` / `tua` - Remove assignees
- `task_set_status` / `tss` - Change task status (validates subtasks)
- `task_set_priority` / `tsp` - Set task priority
- `task_set_tags` / `tst` - Manage task tags

*Relationships:*
- `task_add_dependency` / `tad` - Add task dependency
- `task_remove_dependency` / `trd` - Remove dependency
- `task_add_link` / `tal` - Link tasks
- `task_remove_link` / `trl` - Unlink tasks

*Comments:*
- `comment_add` / `ca` - Add comment
- `comment_list` / `cl` - List comments
- `comment_update` / `cu` - Update comment
- `comment_delete` / `cd` - Delete comment

*Checklists:*
- `checklist` / `chk` - Manage checklists and checklist items

*Custom Fields:*
- `custom-field` / `cf` - Manage custom field values

*Docs & Pages:*
- `dlist` / `dl` / `doc_list` - List docs
- `doc_get` / `dg` - Get doc details
- `doc_create` / `dc` - Create doc
- `doc_update` / `du` - Update doc
- `doc_export` / `de` - Export docs to markdown
- `doc_import` / `di` - Import markdown files
- `page_list` / `pl` - List pages
- `page_create` / `pc` - Create page
- `page_update` / `pu` - Update page

**Common Options:**
- `--preset <level>` - Use preset format: minimal, summary, detailed, full
- `--show-ids` - Display task IDs
- `--show-descriptions` - Include task descriptions
- `--show-dates` - Show created/due dates
- `--show-comments N` - Show N comments per task
- `--include-completed` - Include completed tasks
- `--no-colorize` - Disable color output
- `--no-emoji` - Hide task type emojis

See `./clickup <command> --help` for command-specific options.

### Documentation & Guides

- **[Task Workflow Guide](docs/TASK_WORKFLOW_GUIDE.md)** - Comprehensive guide on managing tasks from start to finish, including when to update statuses, leave comments, and handle subtasks
- **[API Command Reference](CLICKUP.md)** - Complete CLI command reference with examples

## Quick Start

### Basic Usage (Phase 1 - Client)

```python
from clickup_framework import ClickUpClient

# Initialize client (uses CLICKUP_API_TOKEN env var)
client = ClickUpClient()

# Get a task
task = client.get_task("task_id")
print(task['name'])  # Raw JSON

# Get all tasks in a list
result = client.get_list_tasks("list_id")
for task in result['tasks']:
    print(task['name'])

# Create and update tasks
new_task = client.create_task(
    list_id="list_id",
    name="New Task",
    description="Task description",
    priority=1  # 1=Urgent, 2=High, 3=Normal, 4=Low
)
client.update_task(task_id="task_id", status="in progress")
```

### Token-Efficient Formatting (Phase 2 - NEW!)

```python
from clickup_framework import ClickUpClient
from clickup_framework.formatters import (
    format_task, format_task_list,
    format_comment, format_comment_list,
    format_time_entry, format_time_entry_list
)

client = ClickUpClient()

# Format tasks with different detail levels
task = client.get_task("task_id")
print(format_task(task, detail_level="minimal"))
# Output: Task: abc123 - "Implement feature"

print(format_task(task, detail_level="summary"))
# Output:
# Task: abc123 - "Implement feature"
# Status: in progress
# Assigned: John Doe, Jane Smith
# Due: 2024-01-15

# Format comments
comments = client.get_task_comments("task_id")
formatted_comments = format_comment_list(comments['comments'], detail_level="summary")
print(formatted_comments)
# Output: Clean, numbered list of all comments with timestamps

# Format time entries
time_entries = client.get_time_entries(team_id="team_id", task_id="task_id")
formatted_time = format_time_entry_list(time_entries['data'], detail_level="summary")
print(formatted_time)
# Output: Clean, numbered list of time entries with durations

# Token Savings: 90-98% reduction vs raw JSON!
```

### High-Level Resource APIs (Phase 3 - NEW!)

```python
from clickup_framework import ClickUpClient
from clickup_framework.resources import TasksAPI, ListsAPI, WorkspacesAPI, TimeAPI

client = ClickUpClient()

# Initialize Resource APIs
tasks = TasksAPI(client)
lists = ListsAPI(client)
workspaces = WorkspacesAPI(client)
time = TimeAPI(client)

# TasksAPI - Get formatted task directly
task_summary = tasks.get("task_id", detail_level="summary")
print(task_summary)
# Output:
# Task: task_id - "Implement feature"
# Status: in progress
# Assigned: John Doe

# TasksAPI - Convenience methods
new_task = tasks.create(
    list_id="list_id",
    name="My Task",
    description="Task description",
    priority=2  # High priority
)
tasks.update_status(new_task['id'], "in progress")
tasks.assign(new_task['id'], [user_id])

# TasksAPI - Comments and checklists
tasks.add_comment(task_id, "Status update")
comments = tasks.get_comments(task_id, detail_level="summary")

# TasksAPI - Task Relationships (Dependencies, Links, Custom Relationships)
# 1. Dependencies: Create "blocking" and "waiting on" relationships
tasks.add_dependency_waiting_on("task_b", "task_a")  # Task B waits for Task A
tasks.add_dependency_blocking("task_a", "task_b")     # Task A blocks Task B
tasks.remove_dependency("task_b", depends_on="task_a")

# 2. Simple Task Links: Connect related tasks
tasks.add_link("task_1", "task_2")  # Bidirectional link
tasks.remove_link("task_1", "task_2")

# 3. Custom Relationships: Link tasks across lists (e.g., Projects -> Clients)
tasks.set_relationship_field(
    "project_task_id",
    "client_field_id",
    add_task_ids=["client_task_123"]  # Link project to client
)

# ListsAPI - List management
list_data = lists.get("list_id")
new_list = lists.create(folder_id="folder_id", name="My List")
list_tasks = lists.get_tasks("list_id", include_closed=False)

# WorkspacesAPI - Workspace hierarchy and search
hierarchy = workspaces.get_hierarchy(team_id="team_id")
spaces = workspaces.get_spaces(team_id="team_id")
results = workspaces.search(team_id="team_id", query="bug")

# TimeAPI - Time tracking with formatting
time_summary = time.get_entries(
    team_id="team_id",
    task_id="task_id",
    detail_level="summary"
)
time.create_entry(
    team_id="team_id",
    duration=3600000,  # 1 hour in ms
    description="Development work",
    task_id="task_id"
)

# All APIs support both raw and formatted responses
raw_task = tasks.get("task_id")  # Returns dict
formatted_task = tasks.get("task_id", detail_level="summary")  # Returns formatted string
```

### Display Components - Hierarchical Tree Views (Phase 3.5 - NEW! ✨)

Beautiful, CLI-ready hierarchical tree displays similar to [ClickupCLI](https://github.com/SOELexicon/ClickupCLI) output:

```python
from clickup_framework import ClickUpClient
from clickup_framework.components import DisplayManager, FormatOptions

client = ClickUpClient()
display = DisplayManager(client)

# Display tasks in hierarchical tree view
tasks = client.get_list_tasks("list_id")
output = display.hierarchy_view(tasks)
print(output)

# Example output:
# ├─Feature Development (0/7)
# │ └─UI Improvements (0/7)
# │   └─Hierarchy View (0/7)
# │     └─📝 Enhance Task List Hierarchy View [in progress] (2)
# │       │ 📝 Description:
# │       │   Update the list command to provide a hierarchical tree view...
# │       └─
# │       ├─📝 Add Comprehensive Tests (3)
# │       │ │ 📝 Description:
# │       │ │   Create comprehensive test suite...
# │       │ └─

# Display with container hierarchy (workspace → space → folder → list)
container_output = display.container_view(tasks)
print(container_output)

# Custom formatting options
options = FormatOptions(
    colorize_output=True,
    show_ids=True,
    show_tags=True,
    show_descriptions=True,
    show_dates=True,
    show_comments=2
)
detailed_output = display.hierarchy_view(tasks, options)

# Use preset detail levels
minimal = display.hierarchy_view(tasks, FormatOptions.minimal())
summary = display.hierarchy_view(tasks, FormatOptions.summary())
detailed = display.hierarchy_view(tasks, FormatOptions.detailed())
full = display.hierarchy_view(tasks, FormatOptions.full())

# Filter and display
filtered = display.filtered_view(
    tasks,
    status="in progress",
    priority=1,
    view_mode='hierarchy'
)

# Get statistics
stats = display.summary_stats(tasks)
print(stats)
# Output:
# Task Summary:
#   Total: 22
#   Completed: 5
#   In Progress: 8
#   Blocked: 1
#   To Do: 8

# Detail View - Show task with full relationship context
task = client.get_task("task_id")
all_tasks = client.get_list_tasks("list_id")
detail_output = display.detail_view(task, all_tasks, FormatOptions.detailed())
print(detail_output)

# Example output shows:
# - Parent chain (grandparent > parent)
# - Current task (highlighted with full details)
# - Sibling tasks (same parent)
# - Child tasks/subtasks (in tree view)
# - Dependencies
# - Full task details (description, tags, dates, assignees, etc.)
```

**Display Components:**
- **DisplayManager**: High-level interface for all display operations
- **FormatOptions**: Dataclass for managing display settings (with presets: minimal, summary, detailed, full)
- **RichTaskFormatter**: Enhanced task formatting with emojis, colors, and detailed information
- **TaskHierarchyFormatter**: Organize tasks by parent-child relationships
- **ContainerHierarchyFormatter**: Organize tasks by workspace/space/folder/list containers
- **TaskDetailFormatter**: Comprehensive single-task view with relationship tree
- **TreeFormatter**: Low-level tree rendering with box-drawing characters (├─, └─, │)
- **TaskFilter**: Filter tasks by status, priority, tags, assignee, dates, and custom criteria

**View Modes:**
- `hierarchy_view`: Parent-child task relationships
- `container_view`: Organized by workspace → space → folder → list
- `flat_view`: Simple list display
- `filtered_view`: Apply filters and display in any view mode
- `detail_view`: Comprehensive single task with relationship context

**Features:**
- Beautiful tree structures with Unicode box-drawing characters
- ANSI color support for status, priority, and container types
- Task type emojis (📝 task, 🐛 bug, 🚀 feature, etc.)
- Completion statistics with color coding
- Multi-line description and comment support
- Relationship indicators (dependencies, links)
- Orphaned task detection and display
- Fully customizable formatting options

See `examples/display_components_example.py` for complete usage examples.

### Screenshots

Visual examples of the display components in action:

#### Summary View - Task Hierarchy
![Summary View](screenshots/02_summary_view.jpg)
*Hierarchical task display with IDs, emojis, tags, and dates*

#### Container Hierarchy View
![Container Hierarchy](screenshots/04_container_hierarchy.jpg)
*Tasks organized by workspace → space → folder → list structure*

#### Detailed View with Descriptions
![Detailed View](screenshots/03_detailed_view.jpg)
*Comprehensive task information including descriptions and relationships*

#### Task Detail View with Relationship Tree (NEW! ✨)

The detail view shows a single task with its complete hierarchical context:

![Detail View - Child Task](screenshots/09_detail_view_child.jpg)
*Child task showing parent chain, siblings, and subtasks with full details*

**What's shown in detail view:**
- 📊 **Parent Chain**: Full ancestry from root to current task
- 👉 **Current Task**: Highlighted with complete details (description, tags, dates, assignees)
- 👥 **Siblings**: Other tasks with the same parent
- 📂 **Subtasks**: Child tasks in recursive tree view (up to 3 levels deep)
- 🔗 **Dependencies**: Blocking/waiting tasks
- ☑️ **Checklists**: With completion status
- 💬 **Comments**: User discussions
- 📎 **Attachments**: Files and links
- ⏱️ **Time Tracking**: Estimates and actual time spent

| Deep Hierarchy | Parent View |
|----------------|-------------|
| ![Grandchild](screenshots/10_detail_view_grandchild.jpg) | ![Parent](screenshots/11_detail_view_parent.jpg) |
| Task deep in hierarchy showing full context | Parent task with all children displayed |

#### Other View Modes

| Minimal View | Filtered View | Statistics |
|--------------|---------------|------------|
| ![Minimal](screenshots/01_minimal_view.jpg) | ![Filtered](screenshots/05_filtered_in_progress.jpg) | ![Stats](screenshots/07_statistics.jpg) |
| Simple task list | Active tasks only | Project metrics |

**To generate screenshots locally:**
```bash
# Generate display examples
FORCE_COLOR=1 python scripts/generate_display_examples.py

# Create screenshots (requires aha and wkhtmltopdf)
./scripts/generate_screenshots.sh
```

See `screenshots/README.md` for details on all available screenshots.

### Context Management (NEW! ✨)

Persistent context storage allows you to work with "current" items without repeatedly specifying IDs:

```python
from clickup_framework import ContextManager

# Initialize context manager
context = ContextManager()

# Set current task, list, space, etc.
context.set_current_task("task_123")
context.set_current_list("list_456")
context.set_current_space("space_789")

# Get current IDs
task_id = context.get_current_task()  # Returns "task_123"

# Resolve "current" keyword to actual ID
actual_id = context.resolve_id("task", "current")  # Returns "task_123"
```

**CLI Commands:**

```bash
# Set current resources
./clickup set_current task task_123
./clickup set_current list list_456
./clickup set_current space space_789

# View current context
./clickup show_current
# Output:
# Current Context:
# ==================================================
#   Task         task_123
#   List         list_456
#   Space        space_789
#
# Last Updated: 2025-11-09T12:34:56.789012

# Clear specific context
./clickup clear_current task

# Clear all context
./clickup clear_current

# Use "current" in commands
./clickup detail current           # Uses current task
./clickup hierarchy current        # Uses current list
```

**Integration with Existing Commands:**

All CLI commands now support the `current` keyword:

```bash
# Set current list once
./clickup set_current list 90151234

# Use "current" in subsequent commands
./clickup hierarchy current
./clickup stats current
./clickup filter current --status "in progress"
```

**Context Storage:**
- Context is stored in `~/.clickup_context.json`
- File permissions are set to user-only (0600 on Unix systems)
- Does NOT store API tokens or sensitive credentials
- Only stores resource IDs for convenience

### Task Operation Safeguards (NEW! ✨)

The TasksAPI now includes safeguards to prevent accidental modifications and duplicate creation:

#### View-Before-Modify Requirement

Update and delete operations now require you to fetch the task first:

```python
from clickup_framework.resources import TasksAPI

tasks = TasksAPI(client)

# ✅ CORRECT - View task before modifying
task = tasks.get("task_id")
tasks.update(task, status="in progress")
tasks.delete(task)

# ❌ WRONG - Will raise ValueError
tasks.update("task_id", status="done")  # Error!
tasks.delete("task_id")                 # Error!
```

**Why this matters:**
- Ensures you're aware of the current state before making changes
- Prevents blind edits that might conflict with recent updates
- Reduces risk of accidental deletions
- Encourages intentional, informed modifications

**Convenience methods also require task object:**

```python
task = tasks.get("task_id")

# All these require the task object
tasks.update_status(task, "in progress")
tasks.update_priority(task, 1)
tasks.assign(task, [user_id])
tasks.unassign(task, [user_id])
```

#### Duplicate Detection

Task creation now automatically checks for duplicates using fuzzy matching:

```python
# Create a task
new_task = tasks.create(
    list_id="list_123",
    name="Implement login feature",
    description="Add OAuth2 authentication"
)

# Try to create a similar task
try:
    tasks.create(
        list_id="list_123",
        name="Implement login feature",
        description="Add OAuth2 authentication"
    )
except ValueError as e:
    # Raises: "Task already exists with similar name, description, and parent.
    #          Please review existing task [task_123]: 'Implement login feature'.
    #          Use skip_duplicate_check=True to force creation."
    print(e)
```

**Features:**
- Uses fuzzy string matching (default 95% similarity threshold)
- Checks both task name AND description
- Considers parent task for subtasks (duplicates must have same parent)
- Configurable similarity threshold

**Force creation if needed:**

```python
# Skip duplicate check (use with caution)
tasks.create(
    list_id="list_123",
    name="Implement login feature",
    skip_duplicate_check=True
)
```

**Customize similarity threshold:**

```python
# Require 98% similarity for duplicate detection
tasks = TasksAPI(client, duplicate_threshold=0.98)

# Or more lenient (90% similarity)
tasks = TasksAPI(client, duplicate_threshold=0.90)
```

## Features

### Phase 2: Token-Efficient Formatters ✨

Transform verbose JSON responses into human-readable text with **90-98% token reduction**!

**Task Formatter:**
- 4 detail levels: `minimal`, `summary`, `detailed`, `full`
- Intelligent field selection based on context
- Clean, readable output format
- Tested and benchmarked with real API data

**Comment Formatter:**
- 4 detail levels: `minimal`, `summary`, `detailed`, `full`
- User and timestamp formatting
- Assignee and resolution status tracking
- Reaction and reply count display

**Time Entry Formatter:**
- 4 detail levels: `minimal`, `summary`, `detailed`, `full`
- Duration formatting (ms → "2h 30m")
- Running timer detection (⏱️)
- Billable status and tag support
- Task association display

**Detail Levels (All Formatters):**
- **Minimal** (95-98% reduction): Core identifier only
- **Summary** (90-97% reduction): Key metadata
- **Detailed** (85-92% reduction): Extended information
- **Full** (80-89% reduction): Complete data

**Utility Functions:**
- Date/time formatting (timestamps → readable dates)
- Duration formatting (milliseconds → "2h 30m")
- Text utilities (truncate, clean HTML, format lists)
- User list formatting

See [BENCHMARKS.md](./BENCHMARKS.md) for detailed performance data.

### Phase 3: High-Level Resource APIs 🚀

Convenient, high-level interfaces for ClickUp operations with automatic formatting support.

**TasksAPI:**
- Task CRUD operations (get, create, update, delete)
- Status and priority updates (convenience methods)
- Assignment management (assign, unassign)
- Comments (add_comment, get_comments with formatting)
- Checklists (add_checklist, add_checklist_item)
- Custom fields (set_custom_field, remove_custom_field)
- **Task Relationships:**
  - Dependencies (add_dependency_waiting_on, add_dependency_blocking, remove_dependency)
  - Simple Links (add_link, remove_link)
  - Custom Relationships (set_relationship_field)
- Automatic formatting via `detail_level` parameter

**ListsAPI:**
- List management (get, create, update)
- Task queries (get_tasks with filters)
- Custom field queries (get_custom_fields)

**WorkspacesAPI:**
- Workspace hierarchy (get_hierarchy)
- Space operations (get_space, get_spaces, create_space, update_space, delete_space)
- Folder operations (get_folder, create_folder, update_folder)
- Tag management (get_tags, create_tag)
- Search functionality (search)

**TimeAPI:**
- Time entry queries (get_entries with formatting)
- Time entry creation (create_entry)
- Task-specific time tracking (get_task_time)
- User-specific time tracking (get_user_time)
- Automatic duration formatting

**DocsAPI:**
- Placeholder structure for future implementation
- Requires Docs API endpoints in ClickUpClient

**Key Benefits:**
- Automatic response formatting via `detail_level` parameter
- Convenience methods for common operations
- Type hints for better IDE support
- Comprehensive docstrings
- Consistent API patterns across all resources

### Phase 1: Core API Client

### Authentication
- Automatic token handling from environment
- Session management with connection pooling
- Clear error messages for auth failures

### Rate Limiting
- Token bucket algorithm
- Configurable requests per minute (default: 100)
- Automatic throttling
- Thread-safe

### Error Handling
- Custom exception hierarchy
- Automatic retries with exponential backoff
- Timeout handling
- Detailed error messages

### Supported Endpoints

**Tasks (via TasksAPI - with safeguards):**
- `get(task_id, detail_level=None)` - Get task by ID (optionally formatted)
- `get_list_tasks(list_id, detail_level=None)` - Get all tasks in list
- `get_team_tasks(team_id, detail_level=None)` - Get all tasks in workspace
- `create(list_id, name, skip_duplicate_check=False, **data)` - Create new task with duplicate detection
- `update(task, **updates)` - Update task (requires task object)
- `delete(task)` - Delete task (requires task object)
- `update_status(task, status)` - Update task status (requires task object)
- `update_priority(task, priority)` - Update task priority (requires task object)
- `assign(task, user_ids)` - Assign users to task (requires task object)
- `unassign(task, user_ids)` - Unassign users from task (requires task object)

**Tasks (via ClickUpClient - direct API):**
- `get_task(task_id)` - Get task by ID
- `get_list_tasks(list_id)` - Get all tasks in list
- `get_team_tasks(team_id)` - Get all tasks in workspace
- `create_task(list_id, **data)` - Create new task (no safeguards)
- `update_task(task_id, **updates)` - Update task (no safeguards)
- `delete_task(task_id)` - Delete task (no safeguards)

**Lists:**
- `get_list(list_id)` - Get list by ID
- `create_list(folder_id, name, **data)` - Create new list
- `update_list(list_id, **updates)` - Update list

**Folders:**
- `get_folder(folder_id)` - Get folder by ID
- `create_folder(space_id, name)` - Create new folder
- `update_folder(folder_id, **updates)` - Update folder

**Spaces:**
- `get_space(space_id)` - Get space by ID
- `get_team_spaces(team_id)` - Get all spaces

**Workspace:**
- `get_workspace_hierarchy(team_id)` - Get complete hierarchy

**Comments:**
- `create_task_comment(task_id, comment_text)` - Add comment
- `get_task_comments(task_id)` - Get all comments

**Search:**
- `search(team_id, query, **filters)` - Search workspace

**Time Tracking:**
- `get_time_entries(team_id, **params)` - Get time entries
- `create_time_entry(team_id, **data)` - Create time entry

## Configuration

```python
client = ClickUpClient(
    api_token="your_token",      # Or use CLICKUP_API_TOKEN env var
    rate_limit=100,              # Requests per minute
    timeout=30,                  # Request timeout (seconds)
    max_retries=3                # Maximum retry attempts
)
```

## Error Handling

```python
from clickup_framework import ClickUpClient
from clickup_framework.exceptions import (
    ClickUpAuthError,
    ClickUpNotFoundError,
    ClickUpRateLimitError,
    ClickUpAPIError
)

try:
    client = ClickUpClient()
    task = client.get_task("invalid_id")
except ClickUpAuthError:
    print("Authentication failed - check your API token")
except ClickUpNotFoundError as e:
    print(f"Task not found: {e}")
except ClickUpRateLimitError as e:
    print(f"Rate limit exceeded, retry after {e.retry_after}s")
except ClickUpAPIError as e:
    print(f"API error: {e}")
```

## Context Manager Support

```python
with ClickUpClient() as client:
    task = client.get_task("task_id")
    # Session automatically closed on exit
```

## Architecture

```
┌─────────────────────────────────────────────┐
│   Layer 3: Skill Interface                  │
│   (Coming in Phase 4)                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   Layer 2: Formatters                       │
│   (Coming in Phase 2)                       │
│   - 90-95% token reduction                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   Layer 1: Core Client ✅                   │
│   - Authentication                          │
│   - Rate limiting                           │
│   - Error handling                          │
│   - HTTP operations                         │
└─────────────────────────────────────────────┘
```

## Next Steps

### Phase 2: Formatters (Next)
- Task formatter: Transform verbose JSON to readable text
- Multiple detail levels: minimal, summary, detailed, full
- Achieve 90-95% token reduction
- Benchmark token savings

See `/docs/token-efficient-skill-framework.md` for complete plan.

## Related

- **Documentation:** `/docs/token-efficient-skill-framework.md`
- **ClickUp Task:** [86c6ce9gg](https://app.clickup.com/t/86c6ce9gg)
- **Related Tasks:**
  - API Client Framework: [86c6ce3ag](https://app.clickup.com/t/86c6ce3ag)
  - Task Management: [86c6brp8b](https://app.clickup.com/t/86c6brp8b)
  - ClickUp Suite: [86c6brnrq](https://app.clickup.com/t/86c6brnrq)

## Testing

```bash
# Run basic tests
python3 -c "
import sys
sys.path.insert(0, '/home/user/Skills')
from clickup_framework import ClickUpClient

client = ClickUpClient()
task = client.get_task('86c6ce9gg')
print(f\"✓ Task: {task['name']}\")
"
```

## License

Part of the Skills Repository - Apache 2.0 License
