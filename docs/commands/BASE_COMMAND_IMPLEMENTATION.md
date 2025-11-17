# BaseCommand Implementation Summary

## Overview

A base class (`BaseCommand`) has been created to provide common functionality for all ClickUp Framework CLI commands. This reduces code duplication and ensures consistency across commands.

## Files Created

1. **`clickup_framework/commands/base_command.py`**
   - Main base class implementation
   - Provides common attributes, methods, and utilities

2. **`clickup_framework/commands/example_base_command.py`**
   - Simple example showing basic usage
   - Refactored version of `clear_current` command

3. **`clickup_framework/commands/example_complex_command.py`**
   - Complex example showing advanced features
   - Demonstrates ID resolution, formatting, and error handling

4. **`docs/commands/BASE_COMMAND_GUIDE.md`**
   - Comprehensive usage guide
   - Migration examples
   - Best practices

## Key Features

### Common Attributes
- `args`: Parsed command-line arguments
- `context`: Context manager instance
- `client`: ClickUpClient instance
- `use_color`: Boolean for color output
- `format_options`: FormatOptions instance (auto-created if applicable)
- `command_name`: Command name for error messages
- `command_metadata`: Optional metadata dictionary

### ID Resolution Methods
- `resolve_id(id_type, id_or_current)`: Resolve any ID type from context
- `resolve_container(id_or_current)`: Resolve space/folder/list/task
- `resolve_list(id_or_current)`: Resolve list ID specifically

### Output Methods
- `print()`: Standard print
- `print_color()`: Colorized print
- `print_error()`: Error message to stderr
- `print_success()`: Success message
- `print_warning()`: Warning message
- `error()`: Print error and exit

### Context Utilities
- `get_default_assignee()`: Get default assignee
- `get_workspace_id()`: Get current workspace
- `get_list_id()`: Get current list
- `get_task_id()`: Get current task

## Benefits

1. **Code Reduction**: Eliminates repetitive initialization code
2. **Consistency**: Standardized error handling and output
3. **Maintainability**: Changes to common functionality in one place
4. **Type Safety**: Better IDE support and type checking
5. **Extensibility**: Easy to add new common functionality

## Migration Path

Commands can be migrated gradually:

1. **Phase 1**: New commands use `BaseCommand`
2. **Phase 2**: Refactor simple commands (like `clear_current`)
3. **Phase 3**: Refactor complex commands with formatting
4. **Phase 4**: Complete migration

## Backward Compatibility

The base class maintains backward compatibility:
- Commands can still use function-based approach
- Function wrappers call `BaseCommand.run()`
- Existing command registration works unchanged

## Example: Before vs After

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

**Code Reduction**: ~50% less code, more readable, better error handling

## Next Steps

1. **Review**: Review the base class implementation
2. **Test**: Test with example commands
3. **Migrate**: Start migrating commands one by one
4. **Document**: Update command documentation as needed
5. **Enhance**: Add more common functionality as patterns emerge

## Integration

The base class is already integrated:
- Exported in `clickup_framework/commands/__init__.py`
- Available for import: `from clickup_framework.commands import BaseCommand`
- Examples provided for reference

## Future Enhancements

Potential additions to `BaseCommand`:
- Logging utilities
- Progress indicators
- Batch operation helpers
- Validation decorators
- Command chaining support
- Performance metrics

