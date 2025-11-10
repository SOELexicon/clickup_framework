# ClickUp Framework MCP Server

Model Context Protocol (MCP) server for ClickUp, enabling AI assistants like Claude Desktop to interact with ClickUp tasks, comments, and workspaces.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that enables AI assistants to securely connect to external tools and data sources. This ClickUp MCP server allows AI assistants to:

- Create and manage ClickUp tasks
- Add and manage comments
- View hierarchical task structures
- Filter and search tasks
- Manage task relationships (dependencies, links)
- Access token-efficient formatters (90-98% token reduction)

## Features

### Token-Efficient Formatting
Built on the ClickUp Framework's proven formatters that reduce token usage by 90-98%, perfect for AI context windows.

### Comprehensive Task Management
- Create, read, update, and delete tasks
- Manage task status, priority, and assignments
- Handle task tags and custom fields
- Support for subtasks and parent-child relationships

### Advanced Views
- **Hierarchy View**: Parent-child task tree with progressive disclosure
- **Flat View**: Simple list of all tasks
- **Filtered View**: Filter by status, priority, assignee, or tags
- **Assigned View**: See tasks assigned to specific users, sorted by difficulty

### Context Management
- Set "current" workspace, list, or task
- Use "current" keyword in commands for convenience
- Persistent context across conversations

### Safeguards & Best Practices
- **View-before-modify**: Tasks are viewed before updates/deletes
- **Duplicate detection**: Prevents accidental duplicate task creation
- **Confirmation prompts**: Destructive actions require `force=true`

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
pip install --upgrade --force-reinstall git+https://github.com/SOELexicon/clickup_framework.git
```

### Option 2: Install from Source

```bash
git clone https://github.com/SOELexicon/clickup_framework.git
cd clickup_framework
pip install -e .
```

### Verify Installation

```bash
cum-mcp --help
```

## Configuration

### 1. Get Your ClickUp API Token

1. Go to https://app.clickup.com/settings/apps
2. Click **Generate** or **Regenerate** under "API Token"
3. Copy the token (starts with `pk_`)

### 2. Configure Claude Desktop

Add the ClickUp MCP server to your Claude Desktop configuration:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "clickup": {
      "command": "cum-mcp",
      "env": {
        "CLICKUP_API_TOKEN": "pk_your_actual_token_here"
      }
    }
  }
}
```

**For Development (using local source):**

```json
{
  "mcpServers": {
    "clickup-dev": {
      "command": "python",
      "args": ["-m", "clickup_framework.mcp_server"],
      "cwd": "/path/to/clickup_framework",
      "env": {
        "CLICKUP_API_TOKEN": "pk_your_actual_token_here"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

After saving the configuration, restart Claude Desktop to load the MCP server.

## Quick Start

Once configured, you can ask Claude to interact with ClickUp:

### Set Up Context (Optional but Recommended)

```
"Set my current ClickUp workspace to 90151898946 and list to 901517404278"
```

This allows you to use "current" instead of IDs in subsequent commands.

### View Tasks

```
"Show me the hierarchy of tasks in my current ClickUp list"
```

```
"Show me all my assigned ClickUp tasks"
```

### Create Tasks

```
"Create a new ClickUp task called 'Implement user authentication' in my current list"
```

```
"Create a ClickUp task with:
- Name: Fix login bug
- Description: Users are unable to log in with SSO
- Priority: urgent
- Tags: bug, security"
```

### Update Tasks

```
"Update ClickUp task abc123 to set priority to high and status to 'in progress'"
```

### Manage Comments

```
"Add a comment to ClickUp task abc123: 'Started working on this, ETA 2 hours'"
```

```
"Show me all comments on task abc123"
```

### Filter and Search

```
"Show me all ClickUp tasks with status 'in progress' and priority 'urgent'"
```

```
"Show me task statistics for my current list"
```

## Available Tools

The MCP server exposes 25+ tools for ClickUp interaction:

### Task Operations
- `clickup_get_task` - Get task details
- `clickup_create_task` - Create new task
- `clickup_update_task` - Update task properties
- `clickup_delete_task` - Delete task (requires confirmation)
- `clickup_set_task_status` - Change task status
- `clickup_set_task_priority` - Change task priority
- `clickup_assign_task` - Assign users to task
- `clickup_unassign_task` - Remove assignees
- `clickup_set_task_tags` - Manage task tags

### View & Display
- `clickup_get_hierarchy` - Hierarchical parent-child tree view
- `clickup_get_flat_view` - Flat list of tasks
- `clickup_filter_tasks` - Filtered task view
- `clickup_get_assigned_tasks` - User's assigned tasks
- `clickup_get_stats` - Task statistics

### Comments
- `clickup_add_comment` - Add comment to task
- `clickup_list_comments` - List task comments
- `clickup_update_comment` - Update comment
- `clickup_delete_comment` - Delete comment

### Task Relationships
- `clickup_add_dependency` - Add task dependency
- `clickup_remove_dependency` - Remove dependency
- `clickup_add_task_link` - Link tasks together
- `clickup_remove_task_link` - Unlink tasks

### Context Management
- `clickup_set_current` - Set current workspace/list/task/assignee
- `clickup_get_current` - View current context
- `clickup_clear_current` - Clear context

## Usage Examples

### Example 1: Daily Task Review

```
You: "Show me all my assigned ClickUp tasks sorted by priority"

Claude: [Uses clickup_get_assigned_tasks]
Here are your assigned tasks sorted by difficulty:

1. [URG] Fix authentication bug (ID: abc123)
   - Blocks 3 other tasks
   - Priority: Urgent

2. [HGH] Implement user dashboard (ID: def456)
   - Has 2 subtasks
   - Priority: High
...
```

### Example 2: Creating a Feature with Subtasks

```
You: "Create a ClickUp task for implementing a new search feature, with subtasks for:
1. Design search UI
2. Implement backend API
3. Write tests"

Claude: [Uses clickup_create_task multiple times]
✓ Created main task: Implement new search feature (ID: xyz789)
✓ Created subtask: Design search UI (ID: xyz790)
✓ Created subtask: Implement backend API (ID: xyz791)
✓ Created subtask: Write tests (ID: xyz792)

All tasks are in your current list and assigned to you.
```

### Example 3: Updating Task Status with Context

```
You: "Set my current ClickUp task to abc123"

Claude: [Uses clickup_set_current]
✓ Set current task to: abc123

You: "Update the current task's status to 'in progress' and add a comment 'Working on this now'"

Claude: [Uses clickup_update_task and clickup_add_comment]
✓ Updated task status to 'in progress'
✓ Added comment to task
```

### Example 4: Filtering and Analysis

```
You: "Show me all urgent ClickUp tasks in my current list that are not completed"

Claude: [Uses clickup_filter_tasks]
Found 5 urgent tasks:

[URG] Fix production bug (abc123) - In Progress
[URG] Security patch needed (def456) - To Do
[URG] Database migration (ghi789) - Blocked
...
```

## Token Efficiency

The ClickUp Framework's formatters provide 90-98% token reduction compared to raw API responses:

**Raw API Response:** ~2000 tokens per task
**Formatted Output:** ~40-200 tokens per task

This means you can view many more tasks in a single conversation without hitting context limits!

### Detail Levels

Control output verbosity with `detail_level`:

- **minimal**: IDs, status, priority only (~40 tokens/task)
- **summary**: + tags, assignees (~100 tokens/task)
- **detailed**: + descriptions, dates (~200 tokens/task)
- **full**: Everything including comments (~500+ tokens/task)

## Troubleshooting

### MCP Server Not Starting

1. **Check API Token:**
   ```bash
   echo $CLICKUP_API_TOKEN
   ```
   Should print your token (starts with `pk_`)

2. **Test Server Manually:**
   ```bash
   cum-mcp
   ```
   Should start without errors. Press Ctrl+C to stop.

3. **Check Logs:**
   - macOS/Linux: `tail -f ~/Library/Logs/Claude/mcp*.log`
   - Windows: Check `%LOCALAPPDATA%\Claude\logs\`

### "Access Denied" Errors

- Your API token may not have permission
- Regenerate token at https://app.clickup.com/settings/apps
- Ensure you have access to the workspace/list you're trying to use

### "No current list set" Errors

Use `clickup_set_current` to set context:
```
"Set my current ClickUp list to 901517404278"
```

Or provide IDs directly in commands:
```
"Show hierarchy for ClickUp list 901517404278"
```

### Commands Not Working

1. Restart Claude Desktop
2. Check configuration file syntax (valid JSON)
3. Verify `cum-mcp` command exists: `which cum-mcp`
4. Try development mode with full Python path

## Advanced Usage

### Multiple Workspaces

You can switch between workspaces using context:

```
"Set my ClickUp workspace to 90151898946"  # Workspace A
# ... work with Workspace A ...

"Set my ClickUp workspace to 90151898999"  # Workspace B
# ... work with Workspace B ...
```

### Bulk Operations

```
"Create 5 ClickUp tasks for the following features: [list]"
```

Claude will call `clickup_create_task` multiple times automatically.

### Task Dependencies

```
"Make ClickUp task abc123 depend on task def456"
```

Uses `clickup_add_dependency` to create blocking relationships.

## Architecture

The MCP server wraps the existing ClickUp Framework CLI:

```
┌─────────────────────────────────────┐
│      Claude Desktop / AI Agent      │
└───────────────┬─────────────────────┘
                │ MCP Protocol
┌───────────────▼─────────────────────┐
│         cum-mcp Server          │
│  (clickup_framework/mcp_server.py)  │
├─────────────────────────────────────┤
│         MCP Tools (25+ tools)       │
│  (clickup_framework/mcp_tools.py)   │
├─────────────────────────────────────┤
│      ClickUp Framework Core         │
│  • Client (HTTP, Auth, Retries)    │
│  • Resources (Tasks, Comments, etc) │
│  • Formatters (Token-Efficient)     │
│  • Components (Display, Hierarchy)  │
└───────────────┬─────────────────────┘
                │ ClickUp API v2
┌───────────────▼─────────────────────┐
│          ClickUp Cloud              │
└─────────────────────────────────────┘
```

### Key Components

1. **mcp_server.py** - Main MCP server entry point
   - Implements MCP protocol handlers
   - Routes tool calls to appropriate functions
   - Manages context and error handling

2. **mcp_tools.py** - Tool definitions
   - JSON Schema for each tool
   - Input validation
   - Documentation

3. **Existing Framework** - Business logic
   - All task operations use existing `TasksAPI`
   - Token-efficient formatters preserved
   - Safeguards and validation maintained

## CLI Still Works!

The MCP server is **additive** - all existing CLI functionality remains:

```bash
# CLI commands still work
cum list 901517404278
cum tc current "New task"
cum h --preset detailed

# Plus new MCP server
cum-mcp
```

Both can be used simultaneously!

## Development

### Running in Development Mode

```bash
cd clickup_framework
python -m clickup_framework.mcp_server
```

### Testing Tools

Use the MCP Inspector to test tools:

```bash
npx @modelcontextprotocol/inspector python -m clickup_framework.mcp_server
```

### Adding New Tools

1. Add tool definition to `mcp_tools.py`:
   ```python
   types.Tool(
       name="clickup_my_tool",
       description="Description",
       inputSchema={...}
   )
   ```

2. Add handler to `mcp_server.py`:
   ```python
   elif name == "clickup_my_tool":
       return await handle_my_tool(client, arguments)
   ```

3. Implement handler function:
   ```python
   async def handle_my_tool(client, arguments):
       # Implementation
       return [types.TextContent(type="text", text=result)]
   ```

## Resources

- **ClickUp Framework CLI**: See `README.md` for full CLI documentation
- **Slash Commands**: Use `/cum` in Claude Code for quick reference
- **MCP Specification**: https://modelcontextprotocol.io/
- **ClickUp API Docs**: https://clickup.com/api/

## Support

- **Issues**: https://github.com/SOELexicon/clickup_framework/issues
- **Discussions**: https://github.com/SOELexicon/clickup_framework/discussions
- **API Token**: https://app.clickup.com/settings/apps

## License

Apache-2.0 - See LICENSE file for details
