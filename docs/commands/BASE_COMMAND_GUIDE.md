# BaseCommand Guide

## Overview

The `BaseCommand` class provides a foundation for all ClickUp Framework CLI commands, reducing code duplication and ensuring consistency across commands.

## Benefits

1. **Reduced Code Duplication**: Common initialization and utilities are centralized
2. **Consistent Error Handling**: Standardized error messages and exit codes
3. **ID Resolution**: Built-in methods for resolving IDs from context
4. **Colorization**: Consistent color output handling
5. **Format Options**: Automatic format options creation for display commands
6. **Metadata Support**: Store command metadata for help generation

## Basic Usage

### Simple Command Example

```python
from clickup_framework.commands.base_command import BaseCommand

class MyCommand(BaseCommand):
    def execute(self):
        """Implement your command logic here."""
        # Access common attributes:
        # - self.args: Parsed arguments
        # - self.context: Context manager
        # - self.client: ClickUpClient instance
        # - self.use_color: Boolean for color output
        
        self.print_success("Command executed successfully!")

def my_command(args):
    """Command function wrapper for backward compatibility."""
    command = MyCommand(args, command_name='my_command')
    command.run()

def register_command(subparsers, add_common_args=None):
    parser = subparsers.add_parser('mycommand', help='My command')
    parser.set_defaults(func=my_command)
```

## Available Attributes

### Core Attributes

- `self.args`: Parsed command-line arguments from argparse
- `self.context`: Context manager instance (`get_context_manager()`)
- `self.client`: ClickUpClient instance
- `self.use_color`: Boolean indicating whether to use ANSI colors
- `self.format_options`: FormatOptions instance (if command uses formatting)
- `self.command_name`: Name of the command
- `self.command_metadata`: Optional metadata dictionary

## Available Methods

### ID Resolution

#### `resolve_id(id_type, id_or_current)`
Resolve an ID from context or use provided ID.

```python
# Resolve task ID (handles 'current' keyword)
task_id = self.resolve_id('task', args.task_id)

# Resolve list ID
list_id = self.resolve_id('list', 'current')
```

**Supported types**: `'task'`, `'list'`, `'workspace'`, `'folder'`, `'space'`

#### `resolve_container(id_or_current)`
Resolve a container ID (space, folder, list, or task).

```python
container = self.resolve_container(args.id)
# Returns: {'type': 'list', 'id': '12345', 'data': {...}}
```

#### `resolve_list(id_or_current)`
Resolve a list ID from list ID, task ID, or 'current'.

```python
list_id = self.resolve_list('current')
```

### Output Methods

#### `print(*args, **kwargs)`
Standard print with optional colorization.

```python
self.print("Hello, world!")
```

#### `print_color(text, color, style)`
Print colorized text.

```python
self.print_color("Success!", TextColor.BRIGHT_GREEN, TextStyle.BOLD)
```

#### `print_error(message)`
Print error message to stderr.

```python
self.print_error("Something went wrong!")
```

#### `print_success(message)`
Print success message.

```python
self.print_success("Task created successfully!")
```

#### `print_warning(message)`
Print warning message.

```python
self.print_warning("This action cannot be undone.")
```

#### `error(message, exit_code=1)`
Print error and exit with code.

```python
self.error("Invalid input", exit_code=1)
```

### Context Utilities

#### `get_default_assignee()`
Get default assignee from context.

```python
assignee = self.get_default_assignee()
```

#### `get_workspace_id()`
Get current workspace ID from context.

```python
workspace_id = self.get_workspace_id()
```

#### `get_list_id()`
Get current list ID from context.

```python
list_id = self.get_list_id()
```

#### `get_task_id()`
Get current task ID from context.

```python
task_id = self.get_task_id()
```

## Migration Guide

### Before (Function-Based)

```python
def my_command(args):
    context = get_context_manager()
    client = ClickUpClient()
    use_color = context.get_ansi_output()
    
    try:
        task_id = context.resolve_id('task', args.task_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    task = client.get_task(task_id)
    print(f"Task: {task['name']}")
```

### After (BaseCommand-Based)

```python
class MyCommand(BaseCommand):
    def execute(self):
        task_id = self.resolve_id('task', self.args.task_id)
        task = self.client.get_task(task_id)
        self.print(f"Task: {task['name']}")

def my_command(args):
    command = MyCommand(args, command_name='my_command')
    command.run()
```

## Advanced Usage

### Using Format Options

Commands that display data can automatically get format options:

```python
class DisplayCommand(BaseCommand):
    def execute(self):
        # Format options are automatically created if command uses formatting
        if self.format_options:
            view = TaskDetailView(self.client, self.format_options)
            view.display_task(task)
```

### Custom Error Handling

Override `run()` for custom error handling:

```python
class MyCommand(BaseCommand):
    def run(self):
        try:
            return self.execute()
        except CustomException as e:
            self.print_error(f"Custom error: {e}")
            sys.exit(2)  # Custom exit code
```

### Command Metadata

Store metadata for help generation:

```python
class MyCommand(BaseCommand):
    def __init__(self, args, command_name=None):
        super().__init__(args, command_name)
        self.set_metadata({
            'category': 'Task Management',
            'description': 'Creates a new task',
            'examples': ['cum tc "Task Name" --list 123']
        })
```

## Best Practices

1. **Always use `execute()` method**: Implement your logic in `execute()`, not `__init__()`
2. **Use provided methods**: Use `resolve_id()`, `print_error()`, etc. instead of duplicating code
3. **Maintain backward compatibility**: Keep function wrapper for existing command registration
4. **Handle errors gracefully**: Use `error()` or `print_error()` for user-facing errors
5. **Use format options**: For display commands, leverage `self.format_options`
6. **Set command name**: Pass `command_name` to constructor for better error messages

## Common Patterns

### Pattern 1: Simple Command with ID Resolution

```python
class GetTaskCommand(BaseCommand):
    def execute(self):
        task_id = self.resolve_id('task', self.args.task_id)
        task = self.client.get_task(task_id)
        self.print(f"Task: {task['name']}")
```

### Pattern 2: Command with Formatting

```python
class ListTasksCommand(BaseCommand):
    def execute(self):
        list_id = self.resolve_list(self.args.list_id)
        tasks = self.client.get_tasks(list_id)
        
        if self.format_options:
            view = TaskListView(self.client, self.format_options)
            view.display_tasks(tasks)
```

### Pattern 3: Command with Validation

```python
class CreateTaskCommand(BaseCommand):
    def execute(self):
        if not self.args.name:
            self.error("Task name is required")
        
        list_id = self.resolve_list(self.args.list_id)
        task = self.client.create_task(list_id, self.args.name)
        self.print_success(f"Created task: {task['name']}")
```

## See Also

- `clickup_framework/commands/base_command.py` - Base class implementation
- `clickup_framework/commands/example_base_command.py` - Simple example
- `clickup_framework/commands/example_complex_command.py` - Complex example

