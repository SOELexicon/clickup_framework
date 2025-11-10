# MCP Conversion Project - Task Specification

## Main Task: Convert ClickUp Framework to MCP Server

**Priority:** High (2)
**Status:** To Do

### Description

Convert the existing ClickUp Framework CLI tool into a Model Context Protocol (MCP) server that can be used by AI assistants like Claude Desktop to interact with ClickUp.

### Goals

This will enable AI assistants to:
- Create and manage ClickUp tasks
- Add comments and track time
- View hierarchies and manage workspaces
- Leverage the existing token-efficient formatters (90-98% token reduction)

### Technical Approach

- Maintain existing CLI functionality (both CLI and MCP server can coexist)
- Add MCP server as additional entry point
- Reuse existing client, resources, and formatters
- Minimal changes to codebase (~95% stays the same)

### Architecture Changes

**New Files to Create:**
```
clickup_framework/
├── mcp_server.py          # Main MCP server entry point (~200 lines)
├── mcp_tools.py           # MCP tool definitions and handlers
└── mcp_resources.py       # MCP resource handlers (optional)
```

**Files to Modify:**
- `pyproject.toml` - Add `mcp>=1.0.0` dependency and new `clickup-mcp` entry point

**Files to Keep As-Is:**
- ✅ `client.py` - Core API client (works perfectly for MCP)
- ✅ `resources/*.py` - All resource APIs (minimal changes)
- ✅ `formatters/*.py` - Token-efficient formatters (ideal for MCP!)
- ✅ `exceptions.py` - Error handling
- ✅ `rate_limiter.py` - Rate limiting
- ✅ `context.py` - Context management

---

## Subtasks

### 1. Add MCP SDK dependency to pyproject.toml

**Status:** To Do
**Priority:** Normal (3)
**Estimated Effort:** 5 minutes

#### Description
Add the `mcp>=1.0.0` package to the dependencies list in `pyproject.toml`.

#### Acceptance Criteria
- [ ] `mcp>=1.0.0` added to `dependencies` array
- [ ] Package installs without conflicts
- [ ] Can import `mcp` package successfully

#### Implementation
```toml
dependencies = [
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "argcomplete>=3.0.0",
    "mcp>=1.0.0",  # ADD THIS LINE
]
```

---

### 2. Create mcp_server.py entry point

**Status:** To Do
**Priority:** High (2)
**Estimated Effort:** 2 hours

#### Description
Create the main MCP server entry point that initializes the server, handles tool registration, and manages the stdio communication protocol.

#### Acceptance Criteria
- [ ] `clickup_framework/mcp_server.py` created
- [ ] Server initializes with proper name and version
- [ ] Implements `list_tools()` handler
- [ ] Implements `call_tool()` handler
- [ ] Implements `main()` function with stdio server
- [ ] Can start server with `python -m clickup_framework.mcp_server`

#### Key Components
- Server initialization with `Server("clickup-mcp")`
- ClickUp client initialization with auto-loaded token
- Context manager integration
- Async handlers for MCP protocol
- Error handling and logging

#### Files
- Create: `clickup_framework/mcp_server.py`

---

### 3. Create mcp_tools.py with tool definitions

**Status:** To Do
**Priority:** High (2)
**Estimated Effort:** 3 hours

#### Description
Create a separate module that defines all MCP tool schemas and their metadata. This keeps the server code clean and makes tools easy to maintain.

#### Acceptance Criteria
- [ ] `clickup_framework/mcp_tools.py` created
- [ ] All tool schemas defined with proper JSON Schema
- [ ] Tool descriptions are clear and concise
- [ ] Required/optional parameters properly specified
- [ ] Enum values provided where applicable

#### Tool Categories to Define
1. **Task Operations** (6 tools)
   - `clickup_get_task`
   - `clickup_create_task`
   - `clickup_update_task`
   - `clickup_delete_task`
   - `clickup_update_task_status`
   - `clickup_update_task_priority`

2. **Task Assignments** (2 tools)
   - `clickup_assign_task`
   - `clickup_unassign_task`

3. **Task Relationships** (4 tools)
   - `clickup_add_dependency`
   - `clickup_remove_dependency`
   - `clickup_add_task_link`
   - `clickup_remove_task_link`

4. **Comments** (4 tools)
   - `clickup_add_comment`
   - `clickup_list_comments`
   - `clickup_update_comment`
   - `clickup_delete_comment`

5. **Context Management** (3 tools)
   - `clickup_set_current`
   - `clickup_get_current`
   - `clickup_clear_current`

#### Files
- Create: `clickup_framework/mcp_tools.py`

---

### 4. Create mcp_resources.py for resource handlers (Optional)

**Status:** To Do
**Priority:** Low (4)
**Estimated Effort:** 2 hours

#### Description
Implement MCP resources that allow AI assistants to "read" ClickUp data via URI patterns like `clickup://task/{task_id}`. This is optional but provides a cleaner interface for reading data.

#### Acceptance Criteria
- [ ] `clickup_framework/mcp_resources.py` created
- [ ] Resource URI patterns defined
- [ ] List resources handler implemented
- [ ] Read resource handler implemented
- [ ] Proper error handling for invalid URIs

#### Resource URI Patterns
```
clickup://workspace/{workspace_id}
clickup://space/{space_id}
clickup://folder/{folder_id}
clickup://list/{list_id}
clickup://task/{task_id}
clickup://task/{task_id}/comments
```

#### Files
- Create: `clickup_framework/mcp_resources.py`

---

### 5. Add async support to resource methods

**Status:** To Do
**Priority:** Normal (3)
**Estimated Effort:** 4 hours

#### Description
While MCP handlers are async, the existing ClickUp Framework uses synchronous code. We have two options:
1. Call sync code from async handlers (simpler, works fine)
2. Add async versions of resource methods (better, but more work)

Start with option 1, then optionally add option 2 later.

#### Acceptance Criteria
- [ ] MCP handlers can call existing sync resource methods
- [ ] No blocking I/O in async context
- [ ] (Optional) Add async resource API methods

#### Implementation Strategy
```python
# Option 1: Call sync from async (use this first)
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    # Sync calls work fine in async context
    tasks_api = TasksAPI(client)
    result = tasks_api.get_task(task_id)
    return [types.TextContent(type="text", text=result)]

# Option 2: Add async methods (optional, later)
async def get_task_async(self, task_id: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self.get_task, task_id)
```

#### Files
- Modify: `clickup_framework/resources/*.py` (optional)

---

### 6. Implement core MCP tools (get_task, create_task, update_status)

**Status:** To Do
**Priority:** High (2)
**Estimated Effort:** 3 hours

#### Description
Implement the core task management tools in the MCP server. These are the most essential tools and serve as templates for other tools.

#### Tools to Implement
1. **clickup_get_task** - Get task details with formatting
2. **clickup_create_task** - Create new task with duplicate detection
3. **clickup_update_task_status** - Update task status
4. **clickup_update_task_priority** - Update task priority
5. **clickup_assign_task** - Assign users to task
6. **clickup_list_tasks** - Get all tasks in a list

#### Acceptance Criteria
- [ ] All 6 core tools implemented in `call_tool()` handler
- [ ] Proper error handling for each tool
- [ ] Context integration (support "current" keyword)
- [ ] Token-efficient formatters used for output
- [ ] Detail level parameter supported
- [ ] Test each tool manually

#### Implementation Notes
- Use existing `TasksAPI` class from `resources/tasks.py`
- Leverage token-efficient formatters from `formatters/task.py`
- Support "current" list/task from context
- Return formatted strings suitable for LLM consumption

#### Files
- Modify: `clickup_framework/mcp_server.py`

---

### 7. Implement comment tools (add, list, update, delete)

**Status:** To Do
**Priority:** Normal (3)
**Estimated Effort:** 2 hours

#### Description
Implement all comment management tools in the MCP server.

#### Tools to Implement
1. **clickup_add_comment** - Add comment to task
2. **clickup_list_comments** - Get all comments on task
3. **clickup_update_comment** - Update existing comment
4. **clickup_delete_comment** - Delete comment

#### Acceptance Criteria
- [ ] All 4 comment tools implemented
- [ ] Support "current" task from context
- [ ] Proper error handling
- [ ] Test each tool manually

#### Implementation Notes
- Use existing `CommentsAPI` class from `resources/comments.py`
- Use token-efficient formatters from `formatters/comment.py`

#### Files
- Modify: `clickup_framework/mcp_server.py`

---

### 8. Implement hierarchy and view tools

**Status:** To Do
**Priority:** Normal (3)
**Estimated Effort:** 3 hours

#### Description
Implement tools that provide hierarchical views and filtered views of tasks. These are powerful features unique to this framework.

#### Tools to Implement
1. **clickup_get_hierarchy** - Hierarchical parent-child tree view
2. **clickup_get_container_view** - Container hierarchy (Space→Folder→List)
3. **clickup_filter_tasks** - Filtered task view with criteria
4. **clickup_get_task_stats** - Task statistics and distribution
5. **clickup_search** - Search tasks across workspace

#### Acceptance Criteria
- [ ] All 5 view tools implemented
- [ ] Support detail level parameters
- [ ] Token-efficient output
- [ ] Proper error handling
- [ ] Test each tool manually

#### Implementation Notes
- Use existing display components from `components/`
- Use hierarchy formatters
- Support filter criteria (status, priority, assignee, tags)

#### Files
- Modify: `clickup_framework/mcp_server.py`

---

### 9. Implement time tracking tools

**Status:** To Do
**Priority:** Low (4)
**Estimated Effort:** 1.5 hours

#### Description
Implement time tracking tools for logging and viewing time entries.

#### Tools to Implement
1. **clickup_create_time_entry** - Log time to task
2. **clickup_get_time_entries** - Get time entries with filters
3. **clickup_get_task_time** - Get total time logged to task

#### Acceptance Criteria
- [ ] All 3 time tracking tools implemented
- [ ] Support duration in various formats
- [ ] Proper error handling
- [ ] Test each tool manually

#### Implementation Notes
- Use existing `TimeAPI` class from `resources/time.py`
- Handle OAuth requirement gracefully (time tracking requires OAuth, not just API token)
- Use formatters from `formatters/time_entry.py`

#### Files
- Modify: `clickup_framework/mcp_server.py`

---

### 10. Implement docs management tools

**Status:** To Do
**Priority:** Low (4)
**Estimated Effort:** 2 hours

#### Description
Implement tools for managing ClickUp Docs and Pages.

#### Tools to Implement
1. **clickup_list_docs** - List all docs in workspace
2. **clickup_get_doc** - Get doc details
3. **clickup_create_doc** - Create new doc
4. **clickup_create_page** - Add page to doc
5. **clickup_update_page** - Update page content

#### Acceptance Criteria
- [ ] All 5 docs tools implemented
- [ ] Proper error handling
- [ ] Test each tool manually

#### Implementation Notes
- Use existing `DocsAPI` class from `resources/docs.py`
- Consider export/import functionality as future enhancement

#### Files
- Modify: `clickup_framework/mcp_server.py`

---

### 11. Add MCP server entry point to pyproject.toml scripts

**Status:** To Do
**Priority:** High (2)
**Estimated Effort:** 5 minutes

#### Description
Add a new entry point in `pyproject.toml` so users can run the MCP server with a simple command.

#### Acceptance Criteria
- [ ] `clickup-mcp` entry point added to `[project.scripts]`
- [ ] Can run server with `clickup-mcp` command after install
- [ ] Entry point points to correct module and function

#### Implementation
```toml
[project.scripts]
clickup = "clickup_framework.cli:main"
cum = "clickup_framework.cli:main"
clickup-mcp = "clickup_framework.mcp_server:main"  # ADD THIS LINE
```

#### Files
- Modify: `pyproject.toml`

---

### 12. Test MCP server with basic operations

**Status:** To Do
**Priority:** High (2)
**Estimated Effort:** 2 hours

#### Description
Test the MCP server with real AI assistant integrations and manual testing.

#### Test Scenarios
1. **Basic Connection**
   - [ ] Server starts without errors
   - [ ] MCP client can connect via stdio
   - [ ] Server responds to `initialize` request
   - [ ] Tools list is returned correctly

2. **Task Operations**
   - [ ] Create a new task
   - [ ] Read task details
   - [ ] Update task status
   - [ ] Update task priority
   - [ ] Add comment to task
   - [ ] List comments on task

3. **Context Management**
   - [ ] Set current list
   - [ ] Use "current" keyword in commands
   - [ ] Get current context

4. **Error Handling**
   - [ ] Invalid task ID returns proper error
   - [ ] Missing required parameters returns proper error
   - [ ] API errors are handled gracefully

5. **Integration Testing**
   - [ ] Test with Claude Desktop (if available)
   - [ ] Test with MCP Inspector tool

#### Files
- Create: `scrap/test-mcp-commands.md` with test commands

---

### 13. Write MCP server documentation

**Status:** To Do
**Priority:** Normal (3)
**Estimated Effort:** 3 hours

#### Description
Create comprehensive documentation for the MCP server, including setup, configuration, and usage examples.

#### Documentation to Create
1. **README-MCP.md** - Main documentation file
   - What is MCP?
   - Why use ClickUp MCP server?
   - Installation instructions
   - Configuration guide
   - Available tools reference
   - Examples

2. **docs/mcp-setup.md** - Detailed setup guide
   - Prerequisites
   - Installation steps
   - Configuration options
   - Troubleshooting

3. **docs/mcp-tools-reference.md** - Complete tools reference
   - All available tools
   - Parameters
   - Examples
   - Response formats

#### Acceptance Criteria
- [ ] `README-MCP.md` created
- [ ] `docs/mcp-setup.md` created
- [ ] `docs/mcp-tools-reference.md` created
- [ ] All examples tested and working
- [ ] Screenshots included (optional)

#### Files
- Create: `README-MCP.md`
- Create: `docs/mcp-setup.md`
- Create: `docs/mcp-tools-reference.md`

---

### 14. Create example MCP configuration for Claude Desktop

**Status:** To Do
**Priority:** Normal (3)
**Estimated Effort:** 30 minutes

#### Description
Create example configuration files that users can copy/paste into their Claude Desktop or other MCP clients.

#### Files to Create
1. **`examples/claude-desktop-config.json`** - Claude Desktop MCP configuration
2. **`examples/mcp-test-config.json`** - Test configuration
3. **`examples/.env.example`** - Environment variable template

#### Acceptance Criteria
- [ ] Claude Desktop config file created with proper format
- [ ] Example shows both installed and development mode usage
- [ ] API token configuration explained
- [ ] Comments included for clarity

#### Example Configuration
```json
{
  "mcpServers": {
    "clickup": {
      "command": "clickup-mcp",
      "env": {
        "CLICKUP_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

Or for development:
```json
{
  "mcpServers": {
    "clickup": {
      "command": "python",
      "args": ["-m", "clickup_framework.mcp_server"],
      "cwd": "/path/to/clickup_framework",
      "env": {
        "CLICKUP_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

#### Files
- Create: `examples/claude-desktop-config.json`
- Create: `examples/mcp-test-config.json`
- Create: `examples/.env.example`

---

## Summary

### Task Breakdown
- **Total Tasks:** 15 (1 main + 14 subtasks)
- **High Priority:** 5 tasks
- **Normal Priority:** 7 tasks
- **Low Priority:** 3 tasks
- **Total Estimated Effort:** ~25-30 hours

### Implementation Order
1. Dependencies & Setup (Tasks 1, 11)
2. Core Infrastructure (Tasks 2, 3)
3. Essential Tools (Task 6)
4. Extended Tools (Tasks 7, 8)
5. Optional Features (Tasks 4, 9, 10)
6. Testing & Documentation (Tasks 12, 13, 14)
7. Async Improvements (Task 5) - ongoing

### Success Criteria
- ✅ MCP server runs without errors
- ✅ AI assistants can connect and use tools
- ✅ Token-efficient formatting preserved
- ✅ Existing CLI functionality unaffected
- ✅ Comprehensive documentation available
- ✅ Example configurations provided

---

## Notes

### Key Advantages of This Approach
1. **Token Efficiency** - Existing 90-98% token reduction formatters are perfect for MCP
2. **Minimal Changes** - 95% of codebase stays the same
3. **Context Management** - Built-in context system works great with conversational AI
4. **Safeguards** - Existing safeguards (view-before-modify, duplicate detection) carry over
5. **Mature Foundation** - Building on production-ready, tested codebase

### Future Enhancements
- Webhooks support for real-time updates
- Batch operations for efficiency
- Custom field management tools
- Advanced search with filters
- Workspace management tools
- Team and user management tools
