# Hierarchy Command Documentation

Display ClickUp tasks in a hierarchical tree structure showing parent-child relationships, dependencies, and links.

## Synopsis

```bash
cum hierarchy [<container_id>] [options]
cum h [<container_id>] [options]          # Short alias
cum list [<container_id>] [options]       # Alternative name
cum ls [<container_id>] [options]         # Unix-style
cum l [<container_id>] [options]          # Shortest alias
```

## Description

The `hierarchy` command (and its aliases) displays ClickUp tasks in a visual tree structure, showing:

- **Parent-child relationships**: Tasks and their subtasks
- **Dependencies**: Tasks that are waiting on or blocking other tasks
- **Links**: Related tasks that are linked together
- **Task metadata**: Status, priority, tags, dates, descriptions, and more

**Key Features:**
- ✅ **Full pagination support**: Automatically fetches all tasks (handles 1000+ task workspaces)
- ✅ **Flexible containers**: Works with workspaces, spaces, folders, lists, or individual tasks
- ✅ **Rich filtering**: Show/hide completed tasks, customize display options
- ✅ **Visual tree**: Unicode box-drawing characters for clear hierarchy
- ✅ **Relationship display**: Shows task dependencies and links

## Options

### Container Selection

| Option | Description |
|--------|-------------|
| `<container_id>` | ClickUp space, folder, list, or task ID (optional if `--all` is used) |
| `--all` | Show all tasks from the entire workspace (mutually exclusive with container_id) |

### Filtering

| Option | Description |
|--------|-------------|
| `--include-completed` | Include completed/closed tasks in the output |

### Display Options

| Option | Description |
|--------|-------------|
| `--header <text>` | Custom header text for the output |
| `--preset <mode>` | Use a preset format configuration:<br>• `minimal`: Bare minimum (IDs and names)<br>• `summary`: Compact view<br>• `detailed`: More information<br>• `full`: Everything (default) |
| `--show-ids` | Show task IDs |
| `--show-tags` | Show task tags (default: true) |
| `--show-descriptions` | Show task descriptions (truncated) |
| `-d, --full-descriptions` | Show full descriptions without truncation |
| `--show-dates` | Show task creation and update dates |
| `--show-comments <N>` | Show N comments per task |
| `--no-emoji` | Hide task type emojis |

### Colorization

| Option | Description |
|--------|-------------|
| `--colorize` | Enable color output (uses ANSI colors) |
| `--no-colorize` | Disable color output (plain text) |

*Note: Color output can also be controlled via the `cum set ansi_output` command.*

## Examples

### Basic Usage

Show all workspace tasks (with pagination):
```bash
cum h --all
```

Show tasks from a specific list:
```bash
cum h <list_id>
```

Show tasks from a space (includes all folders/lists):
```bash
cum h <space_id>
```

Show tasks from a folder (includes all lists):
```bash
cum h <folder_id>
```

### With Filtering

Show all tasks including completed ones:
```bash
cum h --all --include-completed
```

Show completed tasks from a specific list:
```bash
cum h <list_id> --include-completed
```

### With Custom Display

Use minimal preset (IDs and names only):
```bash
cum h --all --preset minimal
```

Show full descriptions and dates:
```bash
cum h <list_id> --full-descriptions --show-dates
```

Show with custom header:
```bash
cum h --all --header "My Active Tasks"
```

Show task IDs and 3 comments per task:
```bash
cum h <list_id> --show-ids --show-comments 3
```

### Using Aliases

All of these are equivalent:
```bash
cum hierarchy --all
cum h --all
cum list --all
cum ls --all
cum l --all
```

## Output Format

The command displays tasks in a tree structure with Unicode box-drawing characters:

```
All Workspace Tasks

├─[abc123] 📝 [OPN] Parent Task (P2)
│   🏷️  Tags: feature, important
│   📝 Description: This is a parent task
│   📅 Created: 2024-01-01 | Updated: 2024-01-15
│   🔗 Depends on: 2 task(s)
│   ├─[def456] 📝 [PRG] Child Task 1 (P1)
│   │   🏷️  Tags: frontend
│   │   🔗 Linked: 1 task(s)
│   └─[ghi789] 📝 [OPN] Child Task 2 (P2)
│       🏷️  Tags: backend
├─[jkl012] 📝 [CMP] Completed Task (P3)
│   ✅ Status: Complete
└─[mno345] 📝 [OPN] Another Task (P4)
```

### Legend

**Tree Characters:**
- `├─` : Branch (more items follow)
- `└─` : Last branch (no more items)
- `│` : Vertical continuation
- `[taskid]` : Task ID (when `--show-ids` is used or ID format is short)

**Emojis:**
- 📝 : Standard task
- ✅ : Completed task
- 🏷️ : Tags
- 📝 : Description
- 📅 : Dates
- 🔗 : Dependencies or links
- ⏰ : Due date
- 📎 : Attachments

**Status Abbreviations:**
- `[OPN]` : Open
- `[PRG]` : In Progress
- `[CMP]` : Complete
- `[BLK]` : Blocked
- (and custom statuses)

**Priority:**
- `(P1)` : Urgent
- `(P2)` : High
- `(P3)` : Normal
- `(P4)` : Low

## Task Relationships

The hierarchy command displays several types of task relationships:

### Parent-Child Relationships

Tasks are automatically organized in a tree showing subtasks under their parent tasks:

```
├─[parent] Parent Task
│   ├─[child1] Child Task 1
│   │   └─[grandchild] Grandchild Task
│   └─[child2] Child Task 2
```

### Dependencies

When tasks have dependencies, they're shown with a dependencies count:

```
├─[task1] Task with Dependencies
│   🔗 Depends on: 3 task(s)
│   🔗 Blocking: 2 task(s)
```

To see the actual dependency relationships:
```bash
# Show a specific task's dependencies
cum detail <task_id>
```

### Linked Tasks

Related tasks that are linked together show a link count:

```
├─[task1] Linked Task
│   🔗 Linked: 2 task(s)
```

## Pagination

The hierarchy command **automatically handles pagination** for large workspaces:

- ClickUp API returns max 100 tasks per page
- The command fetches all pages automatically
- Works transparently for 1000+ task workspaces
- No special flags needed - it just works!

Example: If your workspace has 1,500 tasks, the command will automatically fetch:
- Page 0: 100 tasks
- Page 1: 100 tasks
- ...
- Page 14: 100 tasks
- Total: 1,500 tasks displayed

## Performance Considerations

For large workspaces or complex hierarchies:

1. **Use filters**: `--include-completed` adds more tasks (slower)
2. **Use presets**: `--preset minimal` is fastest, `--preset full` shows everything
3. **Scope appropriately**: List-level is faster than workspace-level (`--all`)
4. **Network matters**: API calls can take time for large datasets

Typical performance:
- Small list (< 50 tasks): < 1 second
- Medium workspace (100-500 tasks): 2-5 seconds
- Large workspace (1000+ tasks): 5-15 seconds

## Container Types

The command intelligently handles different container types:

| Container Type | What It Shows |
|---------------|---------------|
| **Workspace** (`--all`) | All tasks from all spaces, folders, and lists |
| **Space** | All tasks from all folders and folderless lists in the space |
| **Folder** | All tasks from all lists in the folder |
| **List** | All tasks from the single list (shows status line) |
| **Task** | All subtasks of the specified task |

## Error Handling

The command handles various error conditions gracefully:

### No Container Specified
```bash
cum h
# Error: Either provide a container ID or use --all to show all workspace tasks
```

### Both Container and --all
```bash
cum h <list_id> --all
# Error: Cannot use both container ID and --all flag together
```

### No Workspace Set (when using --all)
```bash
cum h --all
# Error: No workspace ID set. Use 'cum set workspace <team_id>' first.
```

### Invalid Container ID
```bash
cum h invalid_id
# Error: Invalid ID 'invalid_id'. Please provide a valid space, folder, list, or task ID.
```

### Permission Errors
If you don't have permission to access a list within a space/folder, the command:
- Logs a debug message
- Continues fetching from other lists
- Shows all accessible tasks

## Integration with Other Commands

The hierarchy command works well with other `cum` commands:

### Set Context
```bash
# Set workspace first
cum set workspace <workspace_id>

# Then use --all without specifying workspace
cum h --all
```

### Filter and Detail
```bash
# See hierarchy overview
cum h <list_id>

# Get detailed info on a specific task
cum detail <task_id>
```

### Dependencies
```bash
# Add dependency
cum task_add_dependency <task_id> --waiting-on <blocking_task_id>

# View updated hierarchy (shows dependency count)
cum h <list_id>
```

### Links
```bash
# Add link
cum task_add_link <task_id> <related_task_id>

# View updated hierarchy (shows link count)
cum h <list_id>
```

## Configuration

The command respects configuration settings:

### ANSI Output
```bash
# Enable color output by default
cum set ansi_output true

# Commands will now use colors by default
cum h --all
```

### Workspace Context
```bash
# Set default workspace
cum set workspace <workspace_id>

# Now --all works without workspace ID
cum h --all
```

## Advanced Examples

### Workspace Audit
```bash
# See everything in workspace
cum h --all --include-completed --full-descriptions --show-dates --show-ids
```

### Sprint Planning
```bash
# See all active tasks with details
cum h <list_id> --preset detailed --show-comments 1
```

### Status Report
```bash
# Minimal view for quick overview
cum h --all --preset minimal --header "Sprint 23 - Active Tasks"
```

### Task Review
```bash
# Full details with relationships
cum h <list_id> --full-descriptions --show-ids --show-dates --show-comments 3
```

## Troubleshooting

### No Tasks Displayed

Check if:
1. You're using the correct container ID
2. The container has tasks (try `--include-completed`)
3. You have permission to view the container
4. Workspace is set correctly (`cum show` to verify)

### Pagination Issues

The command handles pagination automatically. If you suspect pagination issues:
1. Check the last tasks displayed - are they cut off mid-stream?
2. Look for warning messages in output
3. Try with a smaller scope (single list instead of workspace)

### Performance Issues

If the command is slow:
1. Use `--preset minimal` for faster rendering
2. Scope to a specific list instead of `--all`
3. Remove `--include-completed` if not needed
4. Check network connection to ClickUp API

### Display Issues

If the output looks wrong:
1. Check terminal supports Unicode (for tree characters)
2. Try `--no-colorize` if colors are wrong
3. Verify terminal width is sufficient (80+ columns recommended)
4. Use `--preset minimal` to reduce visual complexity

## See Also

- `cum detail` - Get detailed information about a specific task
- `cum filter` - Filter tasks by various criteria
- `cum container` - View workspace container hierarchy
- `cum set` - Set context and configuration
- `cum show` - Show current context

## API Reference

The hierarchy command uses these ClickUp API endpoints:

- `GET /team/{team_id}/task` - Fetch workspace tasks (with `--all`)
- `GET /list/{list_id}/task` - Fetch list tasks
- `GET /space/{space_id}` - Get space metadata
- `GET /folder/{folder_id}` - Get folder metadata

All endpoints support pagination via `?page=N` parameter.

## Version History

- **v2.0** - Added pagination support for large workspaces
- **v2.0** - Fixed `--include-completed` flag to work properly
- **v1.5** - Added space and folder container support
- **v1.0** - Initial release with list-level hierarchy

## Contributing

Found a bug or have a feature request? Please report it at:
https://github.com/SOELexicon/clickup_framework/issues
