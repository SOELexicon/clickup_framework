# ClickUp CLI Command Reference

Quick reference for the ClickUp Framework CLI (`cum` / `clickup`)

## Setup

```bash
export CLICKUP_API_TOKEN="your_token"
pip install -e .
```

## View Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `hierarchy` `h` | `cum h <list_id>` | Hierarchical parent-child tree view |
| `container` `c` | `cum c <list_id>` | Container hierarchy (Space→Folder→List) |
| `flat` `f` | `cum f <list_id>` | Flat list view |
| `filter` | `cum filter <list_id> [--status\|--priority\|--tags\|--assignee]` | Filtered task view |
| `detail` `d` | `cum d <task_id> [list_id]` | Detailed single task view |
| `stats` | `cum stats <list_id>` | Task statistics & distribution |
| `assigned` `a` | `cum a [--user-id UID]` | Your assigned tasks, sorted by difficulty |
| `demo` | `cum demo [--mode MODE]` | Demo mode (no API token required) |

## Context Management

| Command | Usage | Description |
|---------|-------|-------------|
| `set_current` | `cum set_current <type> <id>` | Set current workspace/list/task/assignee |
| `show_current` | `cum show_current` | Display current context |
| `clear_current` | `cum clear_current [type]` | Clear context (all or specific type) |
| `ansi` | `cum ansi <enable\|disable\|status>` | Configure color output |

**Context Types**: `workspace`, `space`, `folder`, `list`, `task`, `assignee`

## Task Management

| Command | Usage | Description |
|---------|-------|-------------|
| `task_create` | `cum task_create <list_id> "name" [options]` | Create new task |
| `task_update` | `cum task_update <task_id> [options]` | Update task properties |
| `task_assign` | `cum task_assign <task_id> <user_id> [...]` | Assign users to task |
| `task_unassign` | `cum task_unassign <task_id> <user_id> [...]` | Remove assignees |
| `task_set_status` | `cum task_set_status <task_id> [...] <status>` | Change task status (validates subtasks) |
| `task_set_priority` | `cum task_set_priority <task_id> <priority>` | Set priority (1-4 or name) |
| `task_set_tags` | `cum task_set_tags <task_id> <--add\|--remove\|--set> <tags...>` | Manage task tags |
| `task_add_dependency` | `cum task_add_dependency <task_id> <depends_on_id>` | Add dependency |
| `task_remove_dependency` | `cum task_remove_dependency <task_id> <dependency_id>` | Remove dependency |
| `task_add_link` | `cum task_add_link <task_id> <linked_task_id>` | Link tasks |
| `task_remove_link` | `cum task_remove_link <task_id> <link_id>` | Unlink tasks |

### Task Create Options

```bash
--description TEXT          # Task description (text)
--description-file PATH     # Task description (from file)
--status STATUS            # Initial status
--priority {1|2|3|4|urgent|high|normal|low}
--tags TAG [...]           # Tags to add
--assignees USER_ID [...]  # Assign users (defaults to context assignee)
--parent TASK_ID           # Create as subtask
```

**Note**: `--description` and `--description-file` are mutually exclusive.

### Task Update Options

```bash
--name TEXT                # Update name
--description TEXT         # Update description (text)
--description-file PATH    # Update description (from file)
--status STATUS           # Update status
--priority PRIORITY       # Update priority
```

**Note**: `--description` and `--description-file` are mutually exclusive.

## Comment Management

| Command | Usage | Description |
|---------|-------|-------------|
| `comment_add` | `cum comment_add <task_id> "text" \| --comment-file FILE` | Add comment |
| `comment_list` | `cum comment_list <task_id>` | List task comments |
| `comment_update` | `cum comment_update <comment_id> "text" \| --comment-file FILE` | Update comment |
| `comment_delete` | `cum comment_delete <comment_id>` | Delete comment |

### Comment Options

```bash
# Add/Update comments with text or file
comment_text               # Direct text input
--comment-file PATH        # Read comment text from file
```

**Note**: Comment text and `--comment-file` are mutually exclusive.

## Docs & Pages

| Command | Usage | Description |
|---------|-------|-------------|
| `dlist` `dl` | `cum dl <workspace_id>` | List all docs |
| `doc_get` `dg` | `cum dg <workspace_id> <doc_id>` | Show doc details |
| `doc_create` `dc` | `cum dc <workspace_id> "name" [--pages "name:content" ...]` | Create doc |
| `doc_update` | `cum doc_update <workspace_id> <doc_id> [options]` | Update doc |
| `doc_export` | `cum doc_export <workspace_id> [--doc-id ID] --output-dir ./out` | Export to markdown |
| `doc_import` | `cum doc_import <workspace_id> ./input_dir [--nested]` | Import markdown files |
| `page_list` `pl` | `cum pl <workspace_id> <doc_id>` | List pages in doc |
| `page_create` `pc` | `cum pc <workspace_id> <doc_id> --name "name" [--content "..."]` | Create page |
| `page_update` `pu` | `cum pu <workspace_id> <doc_id> <page_id> [--name\|--content]` | Update page |

## Global Format Options

| Option | Description |
|--------|-------------|
| `--preset {minimal\|summary\|detailed\|full}` | Quick format preset |
| `--colorize` / `--no-colorize` | Force colors on/off |
| `--show-ids` | Display task IDs |
| `--show-tags` | Display tags (default: on) |
| `--show-descriptions` | Display descriptions |
| `--show-dates` | Display date fields |
| `--show-comments N` | Show N comments per task |
| `--include-completed` | Include completed tasks |
| `--no-emoji` | Hide emoji icons |

## Presets

| Preset | Shows | Hides |
|--------|-------|-------|
| `minimal` | IDs, status, priority | Tags, descriptions, dates, emojis |
| `summary` | Status, priority, tags | IDs, descriptions, dates |
| `detailed` | Status, priority, tags, descriptions, dates | IDs |
| `full` | Everything + 5 comments | Nothing |

## Priority Values

| Value | Alias |
|-------|-------|
| `1` | `urgent` |
| `2` | `high` |
| `3` | `normal` |
| `4` | `low` |

## Status Codes (3-Letter)

Tasks display with color-coded 3-letter status codes:

- `[CLS]` Closed/Complete
- `[OPN]` Open
- `[PRG]` In Progress
- `[REV]` In Review
- `[BLK]` Blocked
- `[TDO]` To Do
- Custom statuses use first 3 letters

## Special Keywords

- `current` - Use currently set resource from context
- Works with: task_id, list_id, workspace_id, etc.

## Common Workflows

```bash
# Set up context
cum set_current workspace 90151898946
cum set_current list 901517404278
cum set_current assignee 68483025

# Quick task view
cum h current                                    # Hierarchy view
cum a                                            # Your assigned tasks

# Create and manage tasks
cum task_create current "New feature"            # Auto-assigned to default assignee
cum task_create current "Feature" --description-file spec.md  # With description from file
cum task_update current --description-file updated_spec.md    # Update from file
cum task_set_status current "in progress"
cum task_set_tags current --add bug critical

# Add comments from files
cum comment_add current --comment-file notes.txt              # Comment from file

# Filter tasks
cum filter current --status "in progress"
cum filter current --priority urgent --view-mode flat

# Work with docs
cum dl 90151898946                               # List docs
cum dc 90151898946 "API Docs"                    # Create doc
cum pc 90151898946 <doc_id> --name "Overview"    # Add page
```

## Configuration

Settings stored in `~/.clickup_context.json`:
- Current workspace/list/task/assignee
- ANSI color preference
- Last updated timestamp

## Tips

- Use short aliases: `cum h` instead of `cum hierarchy`
- Set context once, use `current` everywhere
- Default assignee auto-assigns new tasks
- `assigned` command sorts by dependency difficulty
- `demo` mode works without API token
- Use `--description-file` and `--comment-file` for longer content
- Most commands support `--help` for details

## Tab Completion

Enable tab completion for bash/zsh (if argcomplete installed):
```bash
eval "$(register-python-argcomplete cum)"
```
