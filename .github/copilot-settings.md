# GitHub Copilot Settings - ClickUp Framework

**For use in GitHub Copilot Settings (character-limited version)**

Copy this into your GitHub Copilot custom instructions:

---

## ClickUp Framework CLI & MCP Server

Python 3.11+ CLI tool for ClickUp API. Architecture: CLI commands in `commands/`, API client in `client.py`, display components in `components/`, MCP server in `mcp_server.py`.

### Critical Patterns

**1. Always Paginate** (ClickUp returns max 100/page):
```python
tasks = _fetch_all_pages(
    lambda **p: client.get_team_tasks(team_id, **p),
    subtasks=True, include_closed=False
)
```

**2. Command Structure**:
```python
def cmd_command(args):
    """Comprehensive docstring with Args, Returns, Examples, Notes."""
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)
    # Fetch data with pagination
    # Format with options
    # Print output
```

**3. Error Handling**:
```python
from clickup_framework.exceptions import ClickUpNotFoundError, ClickUpAuthError
try:
    result = client.get_task(task_id)
except ClickUpNotFoundError:
    logger.debug(f"Task {task_id} not found")
    sys.exit(1)
```

**4. Tests Required**: Unit tests for all functions, integration tests for commands. Use pytest with mocks.

**5. Docstrings**: Google-style with Args, Returns, Raises, Examples, Notes. Module docstrings explain purpose, features, examples.

**6. Display**: Use `DisplayManager` with `FormatOptions`, not direct prints. Support color with `colorize()`.

### Code Standards
- Type hints required
- snake_case for functions/vars, PascalCase for classes
- Private functions: `_prefix`
- 100 char line length
- Comprehensive error handling
- Log at appropriate levels
- No hardcoded values

### Key Imports
```python
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager, FormatOptions
from clickup_framework.commands.utils import create_format_options, resolve_container_id
```

### Common Utilities
- `create_format_options(args)` - Format from CLI args
- `resolve_container_id()` - Resolve space/folder/list/task ID
- `_fetch_all_pages()` - Paginate any API endpoint
- `add_common_args(parser)` - Add standard CLI args

### Testing Pattern
```python
class TestFunction:
    def test_basic(self): """Basic case."""
    def test_edge_case(self): """Edge cases."""
    @patch('module.dep')
    def test_mocked(self, mock): """With mocks."""
```

Reference: `.github/copilot-instructions.md` for full details.

**Quality Bar**: Production CLI - comprehensive docs, full test coverage, proper error handling mandatory.
