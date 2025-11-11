# GitHub Copilot Custom Instructions - ClickUp Framework

## Project Overview
This is the ClickUp Framework (`cum`), a comprehensive Python CLI and MCP server for interacting with the ClickUp API. The project provides both command-line tools and a Model Context Protocol server for AI assistants.

## Core Architecture

### Project Structure
```
clickup_framework/
├── clickup_framework/          # Main package
│   ├── client.py              # ClickUp API client with auth & rate limiting
│   ├── context.py             # Context manager for settings/state
│   ├── commands/              # CLI command implementations
│   │   ├── hierarchy.py       # Task hierarchy display
│   │   ├── detail.py          # Task details
│   │   ├── filter.py          # Task filtering
│   │   └── ...
│   ├── components/            # Display/formatting components
│   │   ├── display.py         # DisplayManager
│   │   ├── hierarchy.py       # TaskHierarchyFormatter
│   │   ├── formatter.py       # RichTaskFormatter
│   │   └── options.py         # FormatOptions
│   ├── resources/             # Resource-specific API wrappers
│   ├── utils/                 # Utilities (colors, etc.)
│   ├── mcp_server.py          # MCP server implementation
│   └── cli.py                 # CLI entry point
├── tests/                     # Comprehensive test suite
├── docs/                      # Documentation
└── scripts/                   # Automation scripts
```

### Key Design Patterns

1. **API Client Pattern**: `ClickUpClient` handles all API interactions with:
   - Automatic rate limiting (100 req/min)
   - Token fallback (parameter → env → context)
   - Retry logic with exponential backoff
   - Comprehensive error handling

2. **Command Pattern**: Each CLI command is a separate module with:
   - `<command>_command(args)` main function
   - `register_command(subparsers)` for CLI registration
   - Helper functions prefixed with `_`
   - Comprehensive docstrings

3. **Display Pattern**: Separation of data fetching and display:
   - Commands fetch data via `ClickUpClient`
   - `DisplayManager` handles formatting
   - `FormatOptions` controls display behavior
   - Formatters use rich output with colors/emojis

4. **Pagination Pattern**: ClickUp API returns max 100 items per page:
   - Always use `_fetch_all_pages()` helper
   - Check `last_page` field in responses
   - Iterate with `page` parameter starting at 0

## Coding Standards

### Python Style
- **Python Version**: 3.11+
- **Style Guide**: PEP 8 with Google-style docstrings
- **Type Hints**: Use type hints for function signatures
- **Imports**: Organize as: stdlib, third-party, local
- **Line Length**: 100 characters preferred, 120 max
- **Strings**: Use double quotes for strings, single for dict keys

### Naming Conventions
```python
# Functions and variables: snake_case
def fetch_all_pages(fetch_func, **params):
    task_list = []

# Classes: PascalCase
class ClickUpClient:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private functions/methods: _prefix
def _get_tasks_from_lists(client, lists):
    pass
```

### Error Handling
```python
# Use specific exceptions from exceptions.py
from clickup_framework.exceptions import (
    ClickUpNotFoundError,
    ClickUpAuthError,
    ClickUpRateLimitError
)

# Log errors appropriately
import logging
logger = logging.getLogger(__name__)

try:
    result = client.get_task(task_id)
except ClickUpNotFoundError:
    logger.debug(f"Task {task_id} not found")
except ClickUpAuthError:
    logger.error(f"Authentication failed for task {task_id}")
except Exception as e:
    logger.warning(f"Unexpected error: {e}")
```

### CLI Command Structure
```python
def my_command(args):
    """
    Brief description.

    Detailed description explaining what the command does,
    its behavior, and any important notes.

    Args:
        args: argparse.Namespace containing:
            - param1 (type): Description
            - param2 (type): Description

    Exits:
        1: Error condition description

    Examples:
        Usage example 1:
            >>> args = Namespace(param1='value')
            >>> my_command(args)

    Notes:
        - Important note 1
        - Important note 2
    """
    # Get dependencies
    context = get_context_manager()
    client = ClickUpClient()
    display = DisplayManager(client)

    # Validate input
    if not args.required_param:
        print("Error: Missing required parameter", file=sys.stderr)
        sys.exit(1)

    # Fetch data (with pagination if needed)
    tasks = _fetch_all_pages(
        lambda **p: client.get_list_tasks(list_id, **p),
        include_closed=args.include_completed
    )

    # Create options
    options = create_format_options(args)

    # Display output
    output = display.format_view(tasks, options)
    print(output)

def register_command(subparsers):
    """Register command with CLI parser."""
    parser = subparsers.add_parser('mycommand', help='Brief help')
    parser.add_argument('param', help='Parameter help')
    add_common_args(parser)
    parser.set_defaults(func=my_command, preset='full')
```

## API Interaction Patterns

### Fetching with Pagination
```python
# ALWAYS use pagination for potentially large result sets
def _fetch_all_pages(fetch_func, **params):
    all_items = []
    page = 0
    last_page = False

    while not last_page:
        try:
            result = fetch_func(page=page, **params)
            items = result.get('tasks', []) # or 'items', depends on endpoint
            all_items.extend(items)
            last_page = result.get('last_page', True)
            page += 1
        except Exception as e:
            logger.warning(f"Pagination stopped at page {page}: {e}")
            break

    return all_items

# Usage
tasks = _fetch_all_pages(
    lambda **p: client.get_team_tasks(team_id, **p),
    subtasks=True,
    include_closed=False
)
```

### API Client Usage
```python
# Get single item
task = client.get_task(task_id)

# Get list with params
result = client.get_list_tasks(
    list_id,
    page=0,
    include_closed=True,
    subtasks=True
)

# Create/Update/Delete
new_task = client.create_task(list_id, name="Task Name", description="...")
updated = client.update_task(task_id, status="in progress")
client.delete_task(task_id)

# Handle specific errors
from clickup_framework.exceptions import ClickUpNotFoundError

try:
    task = client.get_task(task_id)
except ClickUpNotFoundError:
    print(f"Task {task_id} not found")
```

### Context Management
```python
# Get context manager
context = get_context_manager()

# Resolve IDs (with fallback to 'current')
workspace_id = context.resolve_id('workspace', 'current')
list_id = context.resolve_id('list', 'current')

# Get/Set settings
ansi_enabled = context.get_ansi_output()
context.set_ansi_output(True)

# Cache list metadata
list_data = client.get_list(list_id)
context.cache_list_metadata(list_id, list_data)
cached = context.get_cached_list_metadata(list_id)
```

## Testing Requirements

### Test Structure
```python
"""
Test module for <component>.

Tests cover:
- Basic functionality
- Edge cases
- Error handling
- Integration scenarios
"""

import pytest
from unittest.mock import Mock, patch

class TestMyFunction:
    """Test suite for my_function."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = my_function(input_data)
        assert result == expected

    def test_edge_case_empty_input(self):
        """Test handling of empty input."""
        result = my_function([])
        assert result == []

    @patch('module.dependency')
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked"
        result = my_function()
        assert mock_dep.called
```

### Test Coverage Goals
- **Unit tests**: All helper functions and utilities
- **Integration tests**: Full command flows
- **Edge cases**: Empty inputs, missing data, errors
- **Mocking**: Use mocks for API calls in unit tests
- **Assertions**: Clear, specific assertions with good error messages

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/commands/test_hierarchy_command.py

# Run with coverage
pytest --cov=clickup_framework

# Run specific test
pytest tests/test_file.py::TestClass::test_method
```

## Documentation Standards

### Module Docstrings
```python
"""
Brief module description.

Detailed explanation of module purpose, main functionality,
and how it fits into the larger system.

Features:
    - Feature 1
    - Feature 2

Examples:
    # Usage example 1
    from module import function
    result = function(param)

    # Usage example 2
    obj = MyClass()
    obj.method()

Notes:
    - Important note about module behavior
    - Limitations or considerations

Author: ClickUp Framework Team
"""
```

### Function Docstrings
```python
def function_name(param1: str, param2: int = 0) -> dict:
    """
    Brief one-line description.

    Longer description explaining what the function does,
    any important behavior, and how it should be used.

    Args:
        param1 (str): Description of param1
        param2 (int, optional): Description of param2. Defaults to 0.

    Returns:
        dict: Description of return value structure.
            Example: {'key': 'value', 'count': 10}

    Raises:
        ValueError: When param1 is empty
        ClickUpNotFoundError: When resource not found

    Examples:
        Basic usage:
            >>> result = function_name("test")
            >>> print(result['count'])
            10

        With optional parameter:
            >>> result = function_name("test", param2=5)

    Notes:
        - Important behavior note
        - Performance consideration
        - Related functions or alternatives
    """
```

### Class Docstrings
```python
class MyClass:
    """
    Brief class description.

    Detailed explanation of class purpose, main responsibilities,
    and typical usage patterns.

    Attributes:
        attr1 (str): Description of attribute 1
        attr2 (int): Description of attribute 2

    Examples:
        Basic usage:
            >>> obj = MyClass(param="value")
            >>> result = obj.method()

        Advanced usage:
            >>> obj = MyClass(param="value")
            >>> obj.configure(setting=True)
            >>> result = obj.process()

    Notes:
        - Thread safety information
        - Performance characteristics
        - Common pitfalls
    """
```

## Display & Formatting

### Using FormatOptions
```python
from clickup_framework.components import FormatOptions

# Use presets
options = FormatOptions.minimal()  # IDs and names only
options = FormatOptions.summary()  # Compact view
options = FormatOptions.detailed() # More info
options = FormatOptions.full()     # Everything

# Or create custom
options = FormatOptions(
    colorize_output=True,
    show_ids=True,
    show_tags=True,
    show_descriptions=True,
    show_dates=True,
    include_completed=False,
    description_length=500
)

# Get from args
from clickup_framework.commands.utils import create_format_options
options = create_format_options(args)
```

### Color Usage
```python
from clickup_framework.utils.colors import (
    colorize,
    TextColor,
    TextStyle,
    status_color
)

# Basic colorization
text = colorize("Error", TextColor.RED, TextStyle.BOLD)

# Status-aware colors
color = status_color("in progress")  # Returns appropriate color
text = colorize(status_name, color)

# Available colors
TextColor.RED, YELLOW, GREEN, BLUE, CYAN, MAGENTA
TextColor.BRIGHT_RED, BRIGHT_YELLOW, etc.

# Available styles
TextStyle.BOLD, DIM, ITALIC, UNDERLINE
```

### Emojis
```python
# Use emojis sparingly, only when they add clarity
# Common emojis in the project:
"📝"  # Task
"✅"  # Completed
"🏷️"  # Tags
"📅"  # Dates
"🔗"  # Links/Dependencies
"⚠️"  # Warning
"❌"  # Error
"✓"   # Success (plain text alternative)
```

## Common Utilities

### Argument Parsing
```python
from clickup_framework.commands.utils import (
    create_format_options,     # Create FormatOptions from args
    get_list_statuses,         # Get formatted status line
    add_common_args,           # Add standard formatting args
    resolve_container_id,      # Resolve space/folder/list/task ID
    resolve_list_id,           # Resolve list or task ID (deprecated)
    read_text_from_file        # Read text file with validation
)

# Add standard args to parser
add_common_args(parser)
# Adds: --preset, --colorize, --show-ids, --show-tags,
#       --show-descriptions, --show-dates, --show-comments,
#       --include-completed, --no-emoji
```

### Container Resolution
```python
from clickup_framework.commands.utils import resolve_container_id

# Resolves space, folder, list, or task ID
container = resolve_container_id(client, id_or_current, context)

# Returns dict with:
# {'type': 'space|folder|list', 'id': '...', 'data': {...}}

if container['type'] == 'space':
    space_data = container['data']
    tasks = _get_tasks_from_space(client, space_data, include_closed)
elif container['type'] == 'folder':
    folder_data = container['data']
    tasks = _get_tasks_from_folder(client, folder_data, include_closed)
else:  # list
    list_id = container['id']
    tasks = _fetch_all_pages(
        lambda **p: client.get_list_tasks(list_id, **p),
        include_closed=include_closed
    )
```

## MCP Server

### Tool Pattern
```python
@mcp.tool()
async def tool_name(arguments: dict) -> Any:
    """
    Brief tool description.

    Args:
        arguments: Dict containing:
            - param1: Description
            - param2: Description (optional)

    Returns:
        Result data
    """
    # Validate required arguments
    if 'param1' not in arguments:
        raise ValueError("param1 is required")

    # Use shared client
    client = get_shared_client()

    # Perform operation
    result = client.operation(arguments['param1'])

    # Return formatted result
    return format_result(result)
```

### Resource Pattern
```python
@mcp.resource("resource://type/{id}")
async def get_resource(uri: str) -> str:
    """Get resource by URI."""
    # Parse URI
    resource_id = uri.split('/')[-1]

    # Fetch data
    client = get_shared_client()
    data = client.get_resource(resource_id)

    # Format and return
    return format_resource(data)
```

## Git Workflow

### Commit Messages
```
Brief summary (50 chars or less)

Detailed explanation of what changed and why. Reference
issue numbers if applicable.

Changes:
- Specific change 1
- Specific change 2
- Specific change 3

Testing:
- How the changes were tested
- Test results summary
```

### Branch Naming
```
claude/<description>-<session-id>
feature/<feature-name>
fix/<bug-description>
docs/<doc-update>
```

## Common Patterns to Follow

### 1. Always Handle Pagination
```python
# ❌ Bad - only gets first 100
result = client.get_team_tasks(team_id)
tasks = result['tasks']

# ✅ Good - gets all tasks
tasks = _fetch_all_pages(
    lambda **p: client.get_team_tasks(team_id, **p),
    subtasks=True
)
```

### 2. Use Context for IDs
```python
# ❌ Bad - hardcoded or missing fallback
workspace_id = args.workspace_id

# ✅ Good - use context with fallback
context = get_context_manager()
workspace_id = context.resolve_id('workspace', 'current')
```

### 3. Create Comprehensive Docstrings
```python
# ❌ Bad - minimal or missing
def fetch_tasks(list_id):
    """Get tasks."""
    return client.get_list_tasks(list_id)

# ✅ Good - comprehensive with examples
def fetch_tasks(list_id: str, include_closed: bool = False) -> list:
    """
    Fetch all tasks from a list with pagination.

    Args:
        list_id (str): ClickUp list ID
        include_closed (bool): Include completed tasks

    Returns:
        list: All tasks from all pages

    Examples:
        >>> tasks = fetch_tasks('123', include_closed=True)
    """
    return _fetch_all_pages(
        lambda **p: client.get_list_tasks(list_id, **p),
        include_closed=include_closed
    )
```

### 4. Consistent Error Handling
```python
# ❌ Bad - generic exception handling
try:
    task = client.get_task(task_id)
except:
    pass

# ✅ Good - specific exceptions with logging
from clickup_framework.exceptions import ClickUpNotFoundError

try:
    task = client.get_task(task_id)
except ClickUpNotFoundError:
    logger.debug(f"Task {task_id} not found")
    print(f"Error: Task not found", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 5. Use DisplayManager for Output
```python
# ❌ Bad - direct formatting
for task in tasks:
    print(f"{task['id']}: {task['name']}")

# ✅ Good - use DisplayManager
display = DisplayManager(client)
options = create_format_options(args)
output = display.hierarchy_view(tasks, options, header="Tasks")
print(output)
```

### 6. Test Everything
```python
# For every new function, create tests:
# - Basic functionality
# - Edge cases (empty, None, invalid input)
# - Error conditions
# - Integration with other components

class TestMyFunction:
    def test_basic(self):
        """Test basic functionality."""

    def test_empty_input(self):
        """Test with empty input."""

    def test_invalid_input(self):
        """Test error handling."""

    @patch('module.dependency')
    def test_mocked(self, mock_dep):
        """Test with mocked dependency."""
```

## Performance Considerations

1. **Pagination**: Always fetch all pages for workspace/space operations
2. **Caching**: Use context.cache_list_metadata() for repeated list access
3. **Rate Limiting**: Client automatically handles rate limiting
4. **Batch Operations**: Consider batching when creating/updating multiple items
5. **Display Options**: Use presets for performance (minimal > summary > detailed > full)

## Security Considerations

1. **API Tokens**: Never log or print tokens
2. **Input Validation**: Validate all user input
3. **Error Messages**: Don't expose sensitive data in errors
4. **File Operations**: Validate file paths and permissions
5. **Command Injection**: Sanitize shell commands

## Code Review Checklist

- [ ] Comprehensive docstrings (module, class, function)
- [ ] Type hints on function signatures
- [ ] Proper error handling with specific exceptions
- [ ] Pagination for potentially large result sets
- [ ] Tests covering functionality and edge cases
- [ ] Logging at appropriate levels
- [ ] No hardcoded values (use config/context)
- [ ] Consistent naming conventions
- [ ] User-facing documentation if adding commands
- [ ] No emojis unless explicitly requested

## Quick Reference

### Essential Imports
```python
# Core
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager, FormatOptions
from clickup_framework.exceptions import (
    ClickUpNotFoundError,
    ClickUpAuthError,
    ClickUpRateLimitError
)

# Utilities
from clickup_framework.commands.utils import (
    create_format_options,
    add_common_args,
    resolve_container_id
)
from clickup_framework.utils.colors import colorize, TextColor, TextStyle

# Standard library
import sys
import logging
import argparse
```

### Common Code Snippets
```python
# Initialize
context = get_context_manager()
client = ClickUpClient()
display = DisplayManager(client)
logger = logging.getLogger(__name__)

# Fetch with pagination
tasks = _fetch_all_pages(
    lambda **p: client.get_list_tasks(list_id, **p),
    include_closed=args.include_completed
)

# Format and display
options = create_format_options(args)
output = display.hierarchy_view(tasks, options)
print(output)

# Error handling
try:
    result = client.get_task(task_id)
except ClickUpNotFoundError:
    print("Error: Task not found", file=sys.stderr)
    sys.exit(1)
```

---

**Remember**: This is a production CLI tool. Code quality, documentation, and testing are paramount. When in doubt, look at existing commands like `hierarchy.py` as reference implementations.
