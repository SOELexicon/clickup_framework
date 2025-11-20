# Error Handling in Mermaid Diagram Generators

This document describes the error handling patterns and custom exception classes used in the Mermaid diagram generation system.

## Overview

The Mermaid diagram generators use a comprehensive custom exception hierarchy that provides:

- **Context-rich error messages** with specific details about what went wrong
- **Actionable suggestions** to help users resolve issues
- **Structured error information** for programmatic error handling
- **Consistent error formatting** across all generators

## Exception Hierarchy

All custom exceptions inherit from `MermaidGenerationError`, which itself inherits from Python's base `Exception` class:

```
Exception
└── MermaidGenerationError (base class)
    ├── DataValidationError
    ├── ConfigurationError
    ├── FileOperationError
    ├── DiagramSyntaxError
    └── ResourceLimitError
```

## Exception Classes

### MermaidGenerationError (Base Class)

The base exception class that all other custom exceptions inherit from.

**Attributes:**
- `message`: The error message
- `suggestions`: List of actionable suggestions for resolving the error
- `context`: Dictionary containing contextual information about the error

**Methods:**
- `format_error()`: Returns a formatted error message with context and suggestions

**Example:**
```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import MermaidGenerationError

error = MermaidGenerationError(
    "Something went wrong",
    suggestions=["Try this solution", "Or try this other solution"],
    context={"file": "diagram.md", "line_count": 150}
)

# Print formatted error
print(error.format_error())
```

**Output:**
```
ERROR: Something went wrong

Context:
  file: diagram.md
  line_count: 150

Suggestions:
  • Try this solution
  • Or try this other solution
```

### DataValidationError

Raised when input data fails validation checks.

**Factory Methods:**

#### `missing_required_field(field_name, generator_type, stats_keys=None)`

Creates an error for missing required fields in stats data.

**Parameters:**
- `field_name`: Name of the missing required field
- `generator_type`: Type of generator that requires the field
- `stats_keys`: Optional list of available keys in the stats dictionary

**Example:**
```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError

# In a generator's validate_inputs method
def validate_inputs(self, **kwargs):
    symbols_by_file = self.stats.get('symbols_by_file', {})
    if not symbols_by_file:
        raise DataValidationError.missing_required_field(
            field_name='symbols_by_file',
            generator_type='flowchart',
            stats_keys=list(self.stats.keys())
        )
```

**Generated Error Message:**
```
ERROR: Required field 'symbols_by_file' not found in stats data for flowchart generator

Context:
  generator_type: flowchart
  required_field: symbols_by_file
  available_fields: total_symbols, by_language, files_analyzed

Suggestions:
  • Found fields: by_language, files_analyzed, total_symbols
  • Ensure ctags scan completed successfully and found symbols
  • Check that the codebase contains files matching the language filter
  • Verify tags file (.tags.json) exists and contains 'symbols_by_file' data
  • Try running: cum map --help to see required options
```

#### `empty_data_structure(field_name, generator_type, data_size=0)`

Creates an error for empty data structures.

**Parameters:**
- `field_name`: Name of the empty field
- `generator_type`: Type of generator
- `data_size`: Size of the data structure (0 for empty)

**Example:**
```python
function_calls = self.stats.get('function_calls', {})
if len(function_calls) == 0:
    raise DataValidationError.empty_data_structure(
        field_name='function_calls',
        generator_type='sequence',
        data_size=len(function_calls)
    )
```

### ConfigurationError

Raised when configuration values are invalid.

**Factory Methods:**

#### `invalid_value(config_name, value, valid_values)`

Creates an error for invalid configuration values.

**Parameters:**
- `config_name`: Name of the configuration parameter
- `value`: The invalid value provided
- `valid_values`: List of valid values

**Example:**
```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import ConfigurationError

def __init__(self, default_format: str = 'minimal'):
    if default_format not in self.FORMATS:
        raise ConfigurationError.invalid_value(
            config_name='default_format',
            value=default_format,
            valid_values=list(self.FORMATS.keys())
        )
```

**Generated Error Message:**
```
ERROR: Invalid value 'invalid_theme' for configuration 'theme'

Context:
  config_name: theme
  provided_value: invalid_theme
  valid_values: ['dark', 'light', 'neutral']

Suggestions:
  • Use one of the valid values: dark, light, neutral
  • Check configuration file syntax
```

#### `out_of_range(config_name, value, min_value, max_value)`

Creates an error for out-of-range configuration values.

**Parameters:**
- `config_name`: Name of the configuration parameter
- `value`: The out-of-range value
- `min_value`: Minimum allowed value
- `max_value`: Maximum allowed value

**Example:**
```python
if max_nodes > 1000 or max_nodes < 1:
    raise ConfigurationError.out_of_range(
        config_name='max_nodes',
        value=max_nodes,
        min_value=1,
        max_value=1000
    )
```

### FileOperationError

Raised when file I/O operations fail.

**Factory Methods:**

#### `cannot_write(file_path, reason)`

Creates an error for file write failures.

**Parameters:**
- `file_path`: Path to the file that couldn't be written
- `reason`: Reason for the failure (e.g., "Permission denied")

**Example:**
```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import FileOperationError

try:
    with open(self.output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(self.lines))
except PermissionError as e:
    raise FileOperationError.cannot_write(
        file_path=self.output_file,
        reason="Permission denied"
    ) from e
except OSError as e:
    raise FileOperationError.cannot_write(
        file_path=self.output_file,
        reason=str(e)
    ) from e
```

**Generated Error Message:**
```
ERROR: Cannot write to file '/path/to/output.md': Permission denied

Context:
  file_path: /path/to/output.md
  reason: Permission denied
  operation: write

Suggestions:
  • Check file permissions (chmod/chown on Unix, Properties on Windows)
  • Ensure parent directory exists and is writable
  • Close any programs that may have the file open
  • Try running with elevated privileges if appropriate
```

#### `cannot_read(file_path, reason)`

Creates an error for file read failures.

**Example:**
```python
try:
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError as e:
    raise FileOperationError.cannot_read(
        file_path=config_file,
        reason="File not found"
    ) from e
```

### DiagramSyntaxError

Raised when generated diagram fails validation.

**Factory Methods:**

#### `validation_failed(errors, diagram_type, line_count)`

Creates an error for diagram validation failures.

**Parameters:**
- `errors`: List of validation error messages
- `diagram_type`: Type of diagram (e.g., "flowchart", "sequence")
- `line_count`: Number of lines in the diagram

**Example:**
```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import DiagramSyntaxError

validation_errors = [
    "Invalid node ID: node-1",
    "Malformed edge syntax: A --> B C",
    "Unescaped special character: node[test{value}]"
]

raise DiagramSyntaxError.validation_failed(
    errors=validation_errors,
    diagram_type="flowchart",
    line_count=150
)
```

### ResourceLimitError

Raised when resource limits are exceeded.

**Factory Methods:**

#### `diagram_too_large(node_count, max_nodes, diagram_type)`

Creates an error when diagram exceeds node limit.

**Parameters:**
- `node_count`: Actual number of nodes
- `max_nodes`: Maximum allowed nodes
- `diagram_type`: Type of diagram

**Example:**
```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import ResourceLimitError

if len(collected_symbols) > max_nodes:
    raise ResourceLimitError.diagram_too_large(
        node_count=len(collected_symbols),
        max_nodes=max_nodes,
        diagram_type='code_flow'
    )
```

#### `memory_exceeded(current_mb, peak_mb, threshold_mb)`

Creates an error when memory usage exceeds threshold.

**Example:**
```python
if current_memory_mb > threshold_mb:
    raise ResourceLimitError.memory_exceeded(
        current_mb=current_memory_mb,
        peak_mb=peak_memory_mb,
        threshold_mb=threshold_mb
    )
```

## Usage Patterns

### In Generator validate_inputs()

All generators should validate their required inputs and raise appropriate exceptions:

```python
def validate_inputs(self, **kwargs) -> None:
    """Validate diagram-specific inputs."""
    symbols_by_file = self.stats.get('symbols_by_file', {})
    if not symbols_by_file:
        raise DataValidationError.missing_required_field(
            field_name='symbols_by_file',
            generator_type='flowchart',
            stats_keys=list(self.stats.keys())
        )

    # Validate other required fields...
```

### In Configuration Validation

Validate configuration values with helpful error messages:

```python
def __init__(self, theme: str = 'dark'):
    valid_themes = ['dark', 'light', 'neutral']
    if theme not in valid_themes:
        raise ConfigurationError.invalid_value(
            config_name='theme',
            value=theme,
            valid_values=valid_themes
        )
```

### In File Operations

Handle file I/O errors with context:

```python
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
except PermissionError as e:
    raise FileOperationError.cannot_write(
        file_path=output_file,
        reason="Permission denied"
    ) from e
except OSError as e:
    raise FileOperationError.cannot_write(
        file_path=output_file,
        reason=str(e)
    ) from e
```

### Handling Exceptions

The base generator's `_handle_error()` method automatically formats custom exceptions:

```python
def _handle_error(self, error: Exception) -> None:
    """Log error with helpful context."""
    if isinstance(error, MermaidGenerationError):
        print(error.format_error(), file=sys.stderr)
    else:
        # Fall back to generic error logging
        print(f"[ERROR] Diagram generation failed: {error}", file=sys.stderr)
```

## Best Practices

1. **Always provide context**: Include relevant information in the context dictionary
2. **Provide actionable suggestions**: Give users clear steps to resolve the issue
3. **Use factory methods**: Prefer factory methods over direct instantiation for consistency
4. **Preserve exception chains**: Use `raise ... from e` to maintain the original traceback
5. **Validate early**: Check inputs in `validate_inputs()` before processing
6. **Be specific**: Use the most specific exception class for the error type

## Testing

All exception classes have comprehensive test coverage in `tests/test_exceptions.py`. When adding new error scenarios:

1. Create factory methods for common patterns
2. Add test cases for the new error scenarios
3. Verify error messages are clear and actionable
4. Ensure context and suggestions are populated correctly

## Example: Complete Error Handling Flow

```python
from clickup_framework.commands.map_helpers.mermaid.exceptions import (
    DataValidationError,
    ConfigurationError,
    FileOperationError
)

class MyGenerator(BaseGenerator):
    def validate_inputs(self, **kwargs):
        # Validate required data
        required_data = self.stats.get('required_data', {})
        if not required_data:
            raise DataValidationError.missing_required_field(
                field_name='required_data',
                generator_type='my_generator',
                stats_keys=list(self.stats.keys())
            )

        # Validate configuration
        max_items = kwargs.get('max_items', 100)
        if max_items < 1 or max_items > 1000:
            raise ConfigurationError.out_of_range(
                config_name='max_items',
                value=max_items,
                min_value=1,
                max_value=1000
            )

    def generate_body(self, **kwargs):
        # Generate diagram content...
        pass

# Usage
try:
    generator = MyGenerator(stats, output_file)
    result = generator.generate()
except DataValidationError as e:
    print(e.format_error())
    # Handle missing data
except ConfigurationError as e:
    print(e.format_error())
    # Handle configuration issues
except FileOperationError as e:
    print(e.format_error())
    # Handle file I/O problems
```

## Migration Guide

If you have existing code that raises `ValueError` or generic exceptions:

### Before:
```python
if not data:
    raise ValueError("Missing required data")
```

### After:
```python
if not data:
    raise DataValidationError.missing_required_field(
        field_name='data',
        generator_type='my_generator',
        stats_keys=list(self.stats.keys())
    )
```

The new approach provides:
- Specific exception type for programmatic handling
- Context about what data is available
- Actionable suggestions for users
- Consistent error formatting
