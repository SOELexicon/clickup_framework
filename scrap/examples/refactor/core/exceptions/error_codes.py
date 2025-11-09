"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/exceptions/error_codes.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_65df3554 - Update TaskType Enum (sibling)

Used By:
    - Exception Classes: For standardized error code generation
    - Services: For proper exception categorization
    - Error Handlers: For consistent error reporting
    - Logging System: For structured error logging

Purpose:
    Defines the standard error codes used throughout the ClickUp JSON Manager,
    providing utilities for registering error codes and retrieving their descriptions
    through a centralized registry system.

Requirements:
    - Must maintain consistent error code format across the application
    - Must provide helper functions for common error code categories
    - Must document all standard error codes with clear descriptions
    - CRITICAL: Never change existing error code meanings as they may be used in error handling
    - CRITICAL: Error codes must follow the established format pattern for proper categorization

Error Code Format: <component>-<category>-<subcategory>-<code>
Example: CORE-REPO-TASK-001 (Core module, Repository component, Task entity, code 001)

Components:
    - CORE: Core module
    - CLI: Command-line interface
    - STORAGE: Storage module
    - DASH: Dashboard module
    - PLUGIN: Plugin system

Categories:
    - REPO: Repository layer
    - SERVICE: Service layer
    - ENTITY: Entity layer
    - COMMAND: Command handler
    - CONFIG: Configuration
    - STORAGE: Storage operations
    - VALID: Validation
    - AUTH: Authentication/Authorization

Subcategories typically represent entity types or specific components:
    - TASK: Task entity
    - SPACE: Space entity
    - FOLDER: Folder entity
    - LIST: List entity
    - JSON: JSON operations
    - FILE: File operations
    - API: API operations

Changes:
    - v1: Initial implementation with basic error code registry
    - v2: Added helper functions for common error code types
    - v3: Expanded error codes to cover new entity types and operations
    - v4: Added documentation and usage examples

Lessons Learned:
    - Structured error codes significantly improve error traceability
    - Helper functions reduce error code duplication and inconsistency
    - Centralized registry ensures error code consistency across the application
    - Detailed documentation of error codes helps with debugging and maintenance

## Usage Examples

### Using Standard Error Codes

```python
from refactor.core.exceptions import ErrorCode, error_code_registry
from refactor.core.exceptions.error_codes import get_repo_error_code

# Get a standard repository error code for "task not found"
task_not_found = get_repo_error_code("TASK", "001")
print(str(task_not_found))  # "CORE-REPO-TASK-001"

# Get the description for this error code
description = error_code_registry.get_description(task_not_found)
print(description)  # "Task not found with the specified ID"

# Use in exception handling
try:
    # Operation that might fail
    raise TaskNotFoundError("tsk_123")
except Exception as e:
    # Create error context with the standard code
    error_context = ErrorContext(
        message=f"Failed to find task: {str(e)}",
        error_code=task_not_found,
        context_data={"task_id": "tsk_123"}
    )
```

### Using Helper Functions for Common Errors

```python
from refactor.core.exceptions.error_codes import (
    get_repo_error_code,
    get_service_error_code,
    get_storage_error_code,
    get_command_error_code,
    get_validation_error_code
)

# Repository errors
task_not_found = get_repo_error_code("TASK", "001")
task_already_exists = get_repo_error_code("TASK", "002")
space_not_found = get_repo_error_code("SPACE", "001")

# Service errors
task_validation_failed = get_service_error_code("TASK", "001")
incomplete_subtasks = get_service_error_code("TASK", "003")

# Storage errors
read_failed = get_storage_error_code("JSON", "001")
invalid_json = get_storage_error_code("JSON", "003")

# Command errors
invalid_args = get_command_error_code("ARGS", "001")
command_failed = get_command_error_code("EXEC", "001")

# Validation errors
required_field = get_validation_error_code("001")
invalid_value = get_validation_error_code("002")
```

### Using with Error Context System

```python
from refactor.core.exceptions import (
    ErrorContext,
    with_error_context,
    RepositoryError
)
from refactor.core.exceptions.error_codes import get_repo_error_code

# Use with decorator
@with_error_context(
    error_message="Failed to process task",
    error_code=get_repo_error_code("TASK", "001")
)
def get_task_by_id(task_id):
    # Implementation
    pass

# Use with error context builder
from refactor.core.exceptions import ErrorContextBuilder

context = ErrorContextBuilder("Failed to find task") \
    .with_code(get_repo_error_code("TASK", "001")) \
    .with_data("task_id", "tsk_123") \
    .build()

# Throw exception with specific error code
def find_task(task_id):
    if not task_exists(task_id):
        error_code = get_repo_error_code("TASK", "001")
        raise RepositoryError(
            repository_name="TaskRepository",
            message=f"Task not found: {task_id}"
        )
```

### Registering Custom Error Codes

```python
from refactor.core.exceptions import ErrorCode, error_code_registry

# Register a custom error code
custom_code = ErrorCode("PLUGIN", "AUTH", "TOKEN", "001")
error_code_registry.register(
    custom_code,
    "Invalid authentication token for plugin"
)

# Use the custom code
try:
    # Authentication code
    pass
except AuthenticationError as e:
    context = ErrorContext(
        message="Plugin authentication failed",
        error_code=custom_code,
        exception=e
    )
```
"""

from refactor.core.exceptions.error_context import ErrorCode, error_code_registry

# Core Repository Error Codes
error_code_registry.register(
    ErrorCode("CORE", "REPO", "TASK", "001"),
    "Task not found with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "TASK", "002"),
    "Task already exists with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "TASK", "003"),
    "Invalid task data provided"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "TASK", "004"),
    "Failed to delete task"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "SPACE", "001"),
    "Space not found with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "SPACE", "002"),
    "Space already exists with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "FOLDER", "001"),
    "Folder not found with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "FOLDER", "002"),
    "Folder already exists with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "LIST", "001"),
    "List not found with the specified ID"
)

error_code_registry.register(
    ErrorCode("CORE", "REPO", "LIST", "002"),
    "List already exists with the specified ID"
)

# Core Service Error Codes
error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "TASK", "001"),
    "Task operation failed due to validation error"
)

error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "TASK", "002"),
    "Cannot delete task with subtasks (use cascade=True)"
)

error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "TASK", "003"),
    "Cannot complete task with incomplete subtasks"
)

error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "TASK", "004"),
    "Circular dependency detected in task relationships"
)

error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "SPACE", "001"),
    "Space operation failed due to validation error"
)

error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "FOLDER", "001"),
    "Folder operation failed due to validation error"
)

error_code_registry.register(
    ErrorCode("CORE", "SERVICE", "LIST", "001"),
    "List operation failed due to validation error"
)

# Storage Error Codes
error_code_registry.register(
    ErrorCode("STORAGE", "FILE", "JSON", "001"),
    "Failed to read JSON file"
)

error_code_registry.register(
    ErrorCode("STORAGE", "FILE", "JSON", "002"),
    "Failed to write JSON file"
)

error_code_registry.register(
    ErrorCode("STORAGE", "FILE", "JSON", "003"),
    "Invalid JSON format"
)

error_code_registry.register(
    ErrorCode("STORAGE", "FILE", "JSON", "004"),
    "File not found"
)

error_code_registry.register(
    ErrorCode("STORAGE", "FILE", "JSON", "005"),
    "Permission denied"
)

# CLI Error Codes
error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "GENERAL", "000"),
    "General command error"
)

error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "ARGS", "001"),
    "Invalid command arguments"
)

error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "EXEC", "001"),
    "Command execution failed"
)

error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "TASK", "001"),
    "Task command failed"
)

error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "SPACE", "001"),
    "Space command failed"
)

error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "FOLDER", "001"),
    "Folder command failed"
)

error_code_registry.register(
    ErrorCode("CLI", "COMMAND", "LIST", "001"),
    "List command failed"
)

# Configuration Error Codes
error_code_registry.register(
    ErrorCode("CORE", "CONFIG", "GENERAL", "001"),
    "Missing configuration setting"
)

error_code_registry.register(
    ErrorCode("CORE", "CONFIG", "GENERAL", "002"),
    "Invalid configuration value"
)

error_code_registry.register(
    ErrorCode("CORE", "CONFIG", "GENERAL", "003"),
    "Failed to load configuration file"
)

# Validation Error Codes
error_code_registry.register(
    ErrorCode("CORE", "VALID", "ENTITY", "001"),
    "Invalid entity data"
)

error_code_registry.register(
    ErrorCode("CORE", "VALID", "TASK", "001"),
    "Invalid task data"
)

error_code_registry.register(
    ErrorCode("CORE", "VALID", "TASK", "002"),
    "Invalid task status"
)

error_code_registry.register(
    ErrorCode("CORE", "VALID", "TASK", "003"),
    "Invalid task priority"
)

# General Error Codes
error_code_registry.register(
    ErrorCode("CORE", "GENERAL", "UNKNOWN", "000"),
    "Unknown error"
)

error_code_registry.register(
    ErrorCode("CORE", "GENERAL", "SYSTEM", "001"),
    "System error"
)

error_code_registry.register(
    ErrorCode("CORE", "GENERAL", "UNEXPECTED", "001"),
    "Unexpected error condition"
)

# Function to get standard error codes by area
def get_repo_error_code(entity_type, code_type):
    """
    Get a standard repository error code.
    
    Args:
        entity_type: Entity type (TASK, SPACE, FOLDER, LIST)
        code_type: Type of error (001=not_found, 002=already_exists, etc.)
        
    Returns:
        ErrorCode instance
    """
    return ErrorCode("CORE", "REPO", entity_type, code_type)

def get_service_error_code(entity_type, code_type):
    """
    Get a standard service error code.
    
    Args:
        entity_type: Entity type (TASK, SPACE, FOLDER, LIST)
        code_type: Type of error (001=validation, etc.)
        
    Returns:
        ErrorCode instance
    """
    return ErrorCode("CORE", "SERVICE", entity_type, code_type)

def get_storage_error_code(operation_type, code_type):
    """
    Get a standard storage error code.
    
    Args:
        operation_type: Operation type (JSON, FILE)
        code_type: Type of error (001=read_error, etc.)
        
    Returns:
        ErrorCode instance
    """
    return ErrorCode("STORAGE", "FILE", operation_type, code_type)

def get_command_error_code(command_type, code_type):
    """
    Get a standard command error code.
    
    Args:
        command_type: Command type (TASK, SPACE, FOLDER, LIST, ARGS, EXEC)
        code_type: Type of error (001=general_failure, etc.)
        
    Returns:
        ErrorCode instance
    """
    return ErrorCode("CLI", "COMMAND", command_type, code_type)

def get_validation_error_code(code_type):
    """
    Get a standard validation error code.
    
    Args:
        code_type: Type of error (001=missing_field, etc.)
        
    Returns:
        ErrorCode instance
    """
    return ErrorCode("CORE", "VALID", "ENTITY", code_type) 