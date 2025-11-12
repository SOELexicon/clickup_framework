# ClickUp Framework CLI - Command Reference Index

Complete command reference for the `cum` (ClickUp Unified Manager) CLI tool.

## Quick Navigation

- [View Commands](#view-commands) - Display tasks in various formats
- [Task Management](#task-management) - Create, update, delete tasks
- [Comment Management](#comment-management) - Manage task comments
- [Docs Management](#docs-management) - Work with ClickUp Docs
- [Context Management](#context-management) - Set current workspace/list/task
- [Configuration](#configuration) - Configure CLI settings
- [Advanced Features](#advanced-features) - Checklists, custom fields, automation

---

## All Shortcodes Quick Reference

### View Commands
| Shortcode | Full Command | Description |
|-----------|--------------|-------------|
| `h` `ls` `l` | `hierarchy` | Hierarchical parent-child tree view |
| `c` | `clist` `container` | Container hierarchy (Space→Folder→List) |
| `f` | `flat` | Flat list view |
| `fil` | `filter` | Filtered task view |
| `d` | `detail` | Detailed single task view |
| `st` | `stats` | Task statistics & distribution |
| `a` | `assigned` | Your assigned tasks, sorted by difficulty |

### Context Management
| Shortcode | Full Command | Description |
|-----------|--------------|-------------|
| `set` | `set_current` | Set current workspace/list/task/assignee |
| `show` | `show_current` | Display current context |
| `clear` | `clear_current` | Clear context (all or specific type) |

### Task Management
| Shortcode | Full Command | Description |
|-----------|--------------|-------------|
| `tc` | `task_create` | Create new task |
| `tu` | `task_update` | Update task properties |
| `td` | `task_delete` | Delete task |
| `ta` | `task_assign` | Assign users to task |
| `tua` | `task_unassign` | Remove assignees |
| `tss` | `task_set_status` | Change task status |
| `tsp` | `task_set_priority` | Set priority (1-4 or name) |
| `tst` | `task_set_tags` | Manage task tags |
| `tad` | `task_add_dependency` | Add dependency |
| `trd` | `task_remove_dependency` | Remove dependency |
| `tal` | `task_add_link` | Link tasks |
| `trl` | `task_remove_link` | Unlink tasks |

### Comment Management
| Shortcode | Full Command | Description |
|-----------|--------------|-------------|
| `ca` | `comment_add` | Add comment |
| `cl` | `comment_list` | List task comments |
| `cu` | `comment_update` | Update comment |
| `cd` | `comment_delete` | Delete comment |

### Docs & Pages
| Shortcode | Full Command | Description |
|-----------|--------------|-------------|
| `dl` | `dlist` `doc_list` | List all docs |
| `dg` | `doc_get` | Show doc details |
| `dc` | `doc_create` | Create doc |
| `du` | `doc_update` | Update doc |
| `de` | `doc_export` | Export to markdown |
| `di` | `doc_import` | Import markdown files |
| `pl` | `page_list` | List pages in doc |
| `pc` | `page_create` | Create page |
| `pu` | `page_update` | Update page |

### Advanced Features
| Shortcode | Full Command | Description |
|-----------|--------------|-------------|
| `chk` | `checklist` | Manage checklists on tasks |
| `cf` | `custom-field` | Manage custom fields |
| `pau` | `parent_auto_update` | Parent task auto-update automation |
| `fld` `fd` | `folder` | Manage folders |
| `lm` | `list-mgmt` `list_mgmt` | Manage lists |
| `sp` `spc` | `space` | Manage spaces |

---

## Command Categories

### View Commands
Display and visualize tasks in different formats.

**Commands:** `hierarchy` `flat` `clist` `filter` `detail` `stats` `assigned` `demo`

[View Commands Detail →](VIEW_COMMANDS.md)

---

### Task Management
Create, update, delete, and manage tasks.

**Commands:** `task_create` `task_update` `task_delete` `task_assign` `task_unassign` `task_set_status` `task_set_priority` `task_set_tags` `task_add_dependency` `task_remove_dependency` `task_add_link` `task_remove_link`

[Task Management Detail →](TASK_COMMANDS.md)

---

### Comment Management
Add and manage comments on tasks.

**Commands:** `comment_add` `comment_list` `comment_update` `comment_delete`

[Comment Management Detail →](COMMENT_COMMANDS.md)

---

### Docs Management
Work with ClickUp Docs and pages.

**Commands:** `dlist` `doc_get` `doc_create` `doc_update` `doc_export` `doc_import` `page_list` `page_create` `page_update`

[Docs Management Detail →](DOC_COMMANDS.md)

---

### Context Management
Set and manage current workspace/list/task context.

**Commands:** `set_current` `show_current` `clear_current`

[Context Management Detail →](CONTEXT_COMMANDS.md)

---

### Configuration
Configure CLI behavior and settings.

**Commands:** `ansi` `update`

[Configuration Detail →](CONFIG_COMMANDS.md)

---

### Advanced Features
Advanced functionality including checklists, custom fields, and automation.

**Features:**
- Checklist management
- Custom field operations
- Parent task auto-update automation
- Git Overflow workflow
- Space/Folder/List management

[Advanced Features Detail →](ADVANCED_COMMANDS.md)

---

## Quick Start Examples

```bash
# Set up context
cum set workspace 90151898946
cum set list 901517404278
cum set assignee 68483025

# View tasks (using shortcodes!)
cum h current                    # hierarchy view
cum c current                    # container view
cum st current                   # statistics

# Create task
cum tc current "New feature" --priority urgent

# Update task
cum tu <task_id> --status "in progress"

# Add comment
cum ca <task_id> "Great work!"

# List docs
cum dl <workspace_id>
```

---

## Common Options

Most view commands support these common options:

| Option | Description |
|--------|-------------|
| `--preset minimal\|summary\|detailed\|full` | Quick format preset |
| `--colorize` / `--no-colorize` | Force colors on/off |
| `--show-ids` | Display task IDs |
| `--show-tags` | Display tags (default: on) |
| `--show-descriptions` | Display descriptions |
| `--show-dates` | Display date fields |
| `--show-comments N` | Show N comments per task |
| `--include-completed` | Include completed tasks |
| `--no-emoji` | Hide emoji icons |

---

## Priority Values

| Number | Name | Usage |
|--------|------|-------|
| `1` | `urgent` | `--priority 1` or `--priority urgent` |
| `2` | `high` | `--priority 2` or `--priority high` |
| `3` | `normal` | `--priority 3` or `--priority normal` |
| `4` | `low` | `--priority 4` or `--priority low` |

---

## Status Codes (3-Letter)

Tasks display with color-coded 3-letter status codes:

- `[CLS]` Closed/Complete
- `[OPN]` Open
- `[PRG]` In Progress
- `[REV]` In Review
- `[BLK]` Blocked
- `[TDO]` To Do
- Custom statuses use first 3 letters

---

## Special Keywords

- `current` - Use currently set resource from context
- Works with: `task_id`, `list_id`, `workspace_id`, etc.

---

## Setup

```bash
# Install
pip install -e .

# Set API token
export CLICKUP_API_TOKEN="your_token"

# Or set via context
cum set token "your_token"
```

---

## Help & Documentation

```bash
# General help
cum --help
cum -h

# Command-specific help
cum <command> --help
cum <command> -h

# Examples
cum hierarchy --help
cum tc --help
cum chk --help
```

---

## Version

```bash
cum --version
cum -v
```

---

**Navigation:**
- [INDEX](INDEX.md) ← You are here
- [View Commands →](VIEW_COMMANDS.md)
- [Task Commands →](TASK_COMMANDS.md)
- [Comment Commands →](COMMENT_COMMANDS.md)
- [Docs Commands →](DOC_COMMANDS.md)
- [Context Commands →](CONTEXT_COMMANDS.md)
- [Config Commands →](CONFIG_COMMANDS.md)
- [Advanced Commands →](ADVANCED_COMMANDS.md)
