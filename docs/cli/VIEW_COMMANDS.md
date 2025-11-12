# View Commands

Commands for displaying and visualizing tasks in different formats.

**[← Back to Index](INDEX.md)**

---

## Commands Overview

| Command | Shortcodes | Description |
|---------|------------|-------------|
| [`hierarchy`](#hierarchy) | `h` `list` `ls` `l` | Hierarchical parent-child tree view |
| [`clist`](#clist) | `c` `container` | Container hierarchy (Space→Folder→List) |
| [`flat`](#flat) | `f` | Flat list view |
| [`filter`](#filter) | `fil` | Filtered task view |
| [`detail`](#detail) | `d` | Detailed single task view |
| [`stats`](#stats) | `st` | Task statistics & distribution |
| [`assigned`](#assigned) | `a` | Your assigned tasks, sorted by difficulty |
| [`demo`](#demo) | - | Demo mode (no API required) |

---

## hierarchy

**Shortcodes:** `h` `list` `ls` `l`

Display tasks in hierarchical parent-child tree view.

### Usage

```bash
cum hierarchy [list_id] [options]
cum h [list_id] [options]
cum ls [list_id] [options]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `list_id` | ClickUp space, folder, list, or task ID (optional if `--all` is used) |

### Options

| Option | Description |
|--------|-------------|
| `--all` | Show all tasks from entire workspace |
| `--header TEXT` | Custom header text |
| `--depth N` | Limit hierarchy display to N levels deep |
| `--preset minimal\|summary\|detailed\|full` | Use preset format configuration |
| `--colorize` / `--no-colorize` | Enable/disable color output |
| `--show-ids` | Show task IDs |
| `--show-tags` | Show task tags (default: true) |
| `--show-descriptions` | Show task descriptions |
| `-d` / `--full-descriptions` | Show full descriptions without truncation |
| `--show-dates` | Show task dates |
| `--show-comments N` | Show N most recent comments per task |
| `--include-completed` | Include completed tasks |
| `-sc` / `--show-closed` | Show ONLY closed tasks |
| `--no-emoji` | Hide task type emojis |

### Examples

```bash
# View current list in hierarchy
cum h current

# View all workspace tasks
cum hierarchy --all

# View with custom options
cum h current --show-ids --show-descriptions

# View detailed preset
cum ls current --preset detailed

# Limit depth
cum h current --depth 2

# Show only closed tasks
cum h current --show-closed
```

[→ Full hierarchy command details](commands/hierarchy.md)

---

## clist

**Shortcodes:** `c` `container`

Display tasks by container hierarchy (Space → Folder → List).

### Usage

```bash
cum clist <list_id> [options]
cum c <list_id> [options]
cum container <list_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `list_id` | Yes | ClickUp list ID or task ID |

### Options

Same format options as `hierarchy` command.

### Examples

```bash
# View container hierarchy
cum c current

# With IDs and descriptions
cum clist current --show-ids --show-descriptions
```

[→ Full clist command details](commands/clist.md)

---

## flat

**Shortcode:** `f`

Display tasks in flat list format (no hierarchy).

### Usage

```bash
cum flat <list_id> [options]
cum f <list_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `list_id` | Yes | ClickUp list ID or task ID |

### Options

Same format options as `hierarchy` command.

### Examples

```bash
# View flat list
cum f current

# With custom header
cum flat current --header "My Tasks"

# Minimal preset
cum f current --preset minimal
```

[→ Full flat command details](commands/flat.md)

---

## filter

**Shortcode:** `fil`

Display filtered tasks by status, priority, tags, or assignee.

### Usage

```bash
cum filter <list_id> [filter_options] [format_options]
cum fil <list_id> [filter_options] [format_options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `list_id` | Yes | ClickUp list ID or task ID |

### Filter Options

| Option | Description |
|--------|-------------|
| `--status STATUS` | Filter by status |
| `--priority NUMBER` | Filter by priority (1-4) |
| `--tags TAG [TAG...]` | Filter by tags |
| `--assignee USER_ID` | Filter by assignee |
| `--view-mode hierarchy\|container\|flat` | Display mode (default: hierarchy) |

### Format Options

Same format options as `hierarchy` command.

### Examples

```bash
# Filter by status
cum fil current --status "in progress"

# Filter by priority
cum filter current --priority 1

# Filter by multiple criteria
cum fil current --status "open" --priority urgent --view-mode flat

# Filter by tags
cum fil current --tags bug critical

# Filter by assignee
cum filter current --assignee 68483025
```

[→ Full filter command details](commands/filter.md)

---

## detail

**Shortcode:** `d`

Show comprehensive task details with relationships, subtasks, dependencies, and links.

### Usage

```bash
cum detail <task_id> [list_id] [options]
cum d <task_id> [list_id] [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_id` | Yes | ClickUp task ID |
| `list_id` | No | List ID for relationship context |

### Options

Same format options as `hierarchy` command.

### Examples

```bash
# Show task details
cum d 86c6xyz

# With list context
cum detail 86c6xyz 901517404278

# With full descriptions
cum d current --full-descriptions

# Show with comments
cum d current --show-comments 10
```

[→ Full detail command details](commands/detail.md)

---

## stats

**Shortcode:** `st`

Display aggregate statistics for tasks in a list.

### Usage

```bash
cum stats <list_id> [options]
cum st <list_id> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `list_id` | Yes | ClickUp list ID |

### Options

Same format options as `hierarchy` command.

### Statistics Displayed

- Total task count
- Status distribution
- Priority distribution
- Assignee distribution
- Tag distribution
- Completion percentage
- Date statistics

### Examples

```bash
# Show stats for current list
cum st current

# With colorized output
cum stats current --colorize

# Include completed tasks in stats
cum st current --include-completed
```

[→ Full stats command details](commands/stats.md)

---

## assigned

**Shortcode:** `a`

Show tasks assigned to user, sorted by dependency difficulty.

### Usage

```bash
cum assigned [options]
cum a [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--user-id USER_ID` | User ID (defaults to configured default assignee) |
| `--team-id TEAM_ID` | Team/workspace ID (defaults to current workspace) |
| `--include-completed` | Include completed tasks |
| `--show-closed-only` | Show ONLY closed tasks |

### Examples

```bash
# Show your assigned tasks
cum a

# Show specific user's assigned tasks
cum assigned --user-id 68483025

# Include completed tasks
cum a --include-completed

# Show only closed tasks
cum a --show-closed-only
```

**Note:** Tasks are sorted by dependency difficulty, helping you prioritize work based on blocking relationships.

[→ Full assigned command details](commands/assigned.md)

---

## demo

View demo output with sample data (no API token required).

### Usage

```bash
cum demo [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--mode hierarchy\|container\|flat\|stats\|detail` | View mode (default: hierarchy) |

### Examples

```bash
# Demo hierarchy view
cum demo

# Demo container view
cum demo --mode container

# Demo stats view
cum demo --mode stats

# Demo detail view
cum demo --mode detail
```

**Use case:** Testing the CLI without needing API access or real data.

[→ Full demo command details](commands/demo.md)

---

## Common Options Reference

All view commands support these common options:

### Presets

| Preset | Shows | Hides |
|--------|-------|-------|
| `minimal` | IDs, status, priority | Tags, descriptions, dates, emojis |
| `summary` | Status, priority, tags | IDs, descriptions, dates |
| `detailed` | Status, priority, tags, descriptions, dates | IDs |
| `full` | Everything + 5 comments | Nothing |

### Display Control

| Option | Effect |
|--------|--------|
| `--show-ids` | Display task IDs |
| `--show-tags` | Display tags (default: on) |
| `--show-descriptions` | Display task descriptions |
| `--full-descriptions` `-d` | Show full descriptions without truncation |
| `--show-dates` | Display date fields (created, updated, due) |
| `--show-comments N` | Show N most recent comments per task |
| `--no-emoji` | Hide task type emojis |
| `--include-completed` | Include completed tasks in output |
| `--show-closed` `-sc` | Show ONLY closed/completed tasks |

### Color Control

| Option | Effect |
|--------|--------|
| `--colorize` | Force enable color output |
| `--no-colorize` | Force disable color output |
| *(default)* | Use configured ANSI setting |

---

## Tips

1. **Use shortcodes** for faster typing: `cum h` instead of `cum hierarchy`
2. **Set context** once, use `current` everywhere: `cum set list 123 && cum h current`
3. **Combine filters** for precise views: `cum fil current --status "in progress" --priority 1`
4. **Save presets** for common views: `cum h current --preset detailed`
5. **Use depth limiting** for large hierarchies: `cum h current --depth 3`

---

**Navigation:**
- [← Back to Index](INDEX.md)
- [Task Commands →](TASK_COMMANDS.md)
