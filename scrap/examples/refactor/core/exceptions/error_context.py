"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/exceptions/error_context.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_65df3554 - Update TaskType Enum (sibling)
    - tsk_0fa698f3 - Update Core Module Comments (current)

Used By:
    - Core Exception Classes: For detailed error context and traceability
    - Service Layer: For consistent error handling and propagation
    - CLI Layer: For translating errors into user-friendly messages
    - Logging System: For structured error logging with context

Purpose:
    Provides a comprehensive error context system for tracking, propagating, and 
    debugging errors throughout the application. This system enhances error 
    handling by capturing contextual information, maintaining error hierarchies,
    and ensuring consistent error reporting.

Requirements:
    - Must support attaching contextual data to exceptions
    - Must maintain parent-child relationships between errors
    - Must support error severity levels and categorization
    - Must provide serialization for logging and reporting
    - CRITICAL: Must ensure error context is properly propagated through call stack
    - CRITICAL: Must maintain backward compatibility for error handling code

Changes:
    - v1: Initial implementation with basic error context
    - v2: Added builder pattern for easier construction
    - v3: Added decorator for automatic context application
    - v4: Enhanced with parent-child relationships for nested errors
    - v5: Added JSON serialization for reporting and logging

Lessons Learned:
    - Contextual error information greatly reduces debugging time
    - Structured error codes enable systematic error handling and reporting
    - Builder pattern simplifies complex object construction for users
    - Decorator approach reduces boilerplate error handling code
    - Maintaining parent-child relationships helps trace root causes

## Usage Examples

### Basic Error Context Creation
```python
from refactor.core.exceptions import ErrorContext, ErrorCode, ErrorSeverity

# Create a simple error context
context = ErrorContext(
    message="Failed to find task",
    error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
    severity=ErrorSeverity.ERROR,
    context_data={"task_id": "tsk_123"}
)

# Or use a string error code
context = ErrorContext(
    message="Failed to find task",
    error_code="CORE-REPO-TASK-001",
    context_data={"task_id": "tsk_123"}
)
```

### Using the Builder Pattern
```python
from refactor.core.exceptions import ErrorContextBuilder, ErrorSeverity

# Create context with a fluent builder interface
context = ErrorContextBuilder("Failed to find task") \
    .with_code("CORE-REPO-TASK-001") \
    .with_severity(ErrorSeverity.ERROR) \
    .with_data("task_id", "tsk_123") \
    .with_data("operation", "find_by_id") \
    .build()
```

### Adding Context to Exceptions
```python
try:
    # Some operation that might fail
    raise ValueError("Missing required field")
except ValueError as e:
    # Create context with the exception
    context = ErrorContext(
        message="Validation failed",
        error_code="CORE-VALID-ENTITY-001",
        exception=e,
        context_data={"field": "name"}
    )
    
    # Attach context to exception
    e.error_context = context
    raise
```

### Using the Decorator
```python
from refactor.core.exceptions import with_error_context, ErrorCode

# Add context automatically to any exceptions raised in the function
@with_error_context(
    error_message="Failed to process task",
    error_code=ErrorCode("CORE", "SERVICE", "TASK", "001")
)
def process_task(task_id, status):
    # Function implementation
    # Any exceptions will get error context automatically
    pass
```

### Handling Errors with Context
```python
try:
    result = process_task("tsk_123", "complete")
except Exception as e:
    if hasattr(e, 'error_context'):
        # Access the error context
        context = e.error_context
        
        # Log detailed error information
        logger.error(
            f"Error: {context.message}",
            extra={
                "error_code": str(context.error_code),
                "severity": context.severity.name,
                "context_data": context._context_data
            }
        )
        
        # Generate JSON for error reporting
        error_json = context.to_json()
    else:
        # Handle regular exceptions
        logger.error(f"Unhandled error: {str(e)}")
```

This error context system is designed to work with the ClickUp JSON Manager's exception 
hierarchy to provide consistent, detailed error information for debugging and error reporting.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Set, Tuple, Union, Callable, TypeVar, cast
import json
import datetime
import traceback
import uuid
from dataclasses import dataclass, field
import functools
import inspect


class ErrorSeverity(Enum):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/exceptions/error_context.py
    dohcount: 1
    
    Used By:
        - ErrorContext: For classifying error severity
        - Logging System: For determining log levels
        - Error Handlers: For priority-based error handling
    
    Purpose:
        Defines standardized severity levels for errors, enabling
        consistent classification and appropriate handling based on 
        the error's impact and urgency.
    
    Requirements:
        - Must provide granular levels for different error severities
        - Levels must be ordered by increasing severity
        - Must be compatible with common logging levels
    """
    DEBUG = 0     # Informational, for debugging purposes only
    INFO = 1      # Informational, but potentially useful for users
    WARNING = 2   # Issues that don't prevent operation but require attention
    ERROR = 3     # Errors that prevent a specific operation but not the whole application
    CRITICAL = 4  # Severe errors that may prevent the application from functioning


@dataclass
class ErrorCode:
    """
    Structured error code for categorizing and identifying errors.
    
    Format: <component>-<category>-<subcategory>-<code>
    Example: CORE-REPO-TASK-001 (Core module, Repository component, Task entity, error code 001)
    
    ## Usage Examples
    
    ### Creating Error Codes
    ```python
    # Create an error code for a task not found error
    task_not_found = ErrorCode("CORE", "REPO", "TASK", "001")
    
    # Create an error code for a validation error
    validation_error = ErrorCode("CORE", "VALID", "ENTITY", "001")
    
    # Convert to string for logging or display
    error_str = str(task_not_found)  # "CORE-REPO-TASK-001"
    ```
    
    ### Parsing from String
    ```python
    # Parse an error code from its string representation
    code = ErrorCode.from_string("CORE-REPO-TASK-001")
    
    # Access components
    component = code.component  # "CORE"
    category = code.category    # "REPO"
    subcategory = code.subcategory  # "TASK"
    code_num = code.code  # "001"
    ```
    
    ### Using with the Registry
    ```python
    from refactor.core.exceptions import error_code_registry
    
    # Register a new error code
    new_code = ErrorCode("CORE", "SERVICE", "TASK", "999")
    error_code_registry.register(new_code, "Custom task processing error")
    
    # Get the description
    description = error_code_registry.get_description(new_code)
    
    # Check if registered
    is_registered = error_code_registry.is_registered(new_code)
    ```
    
    ### Using Helper Functions
    ```python
    from refactor.core.exceptions import get_repo_error_code
    
    # Get standard error codes using helpers
    task_not_found = get_repo_error_code("TASK", "001")
    space_not_found = get_repo_error_code("SPACE", "001")
    ```
    """
    component: str
    category: str
    subcategory: str
    code: str
    
    def __str__(self) -> str:
        """Return the string representation of the error code."""
        return f"{self.component}-{self.category}-{self.subcategory}-{self.code}"
    
    @classmethod
    def from_string(cls, code_string: str) -> 'ErrorCode':
        """
        Create an ErrorCode from its string representation.
        
        Args:
            code_string: String representation of an error code
            
        Returns:
            ErrorCode instance
            
        Raises:
            ValueError: If the code string format is invalid
        """
        parts = code_string.split('-')
        if len(parts) != 4:
            raise ValueError(f"Invalid error code format: {code_string}. Expected format: COMP-CAT-SUB-CODE")
        
        return cls(component=parts[0], category=parts[1], subcategory=parts[2], code=parts[3])


class ErrorContext:
    """
    Container for error contextual information.
    
    This class captures and maintains detailed context about an error,
    including the error code, message, timestamp, severity, and any
    additional contextual data that might be helpful for debugging.
    
    ## Usage Examples
    
    ### Basic Usage
    ```python
    # Create a simple error context
    context = ErrorContext(
        message="Failed to find task",
        error_code=ErrorCode("CORE", "REPO", "TASK", "001"),
        severity=ErrorSeverity.ERROR,
        context_data={"task_id": "tsk_123"}
    )
    
    # Add more context data
    context.add_context_data("operation", "find_by_id")
    context.add_context_data("user_id", "usr_456")
    
    # Get context data
    task_id = context.get_context_data("task_id")  # "tsk_123"
    ```
    
    ### Working with Exceptions
    ```python
    try:
        # Some operation that might fail
        raise ValueError("Invalid data")
    except ValueError as e:
        # Create context with the exception
        context = ErrorContext(
            message="Data validation failed",
            error_code="CORE-VALID-ENTITY-001",
            exception=e
        )
        
        # The stack trace is automatically captured
        stack_trace = context.stack_trace
    ```
    
    ### Error Chains - Parent/Child Relationships
    ```python
    # Create a parent context for a high-level operation
    parent_context = ErrorContext(
        message="Task update operation failed",
        error_code="CORE-SERVICE-TASK-001"
    )
    
    # Create a child context for the specific error
    child_context = ErrorContext(
        message="Failed to save task to repository",
        error_code="CORE-REPO-TASK-003"
    )
    
    # Link the contexts
    child_context.with_parent(parent_context)
    
    # Later, when handling the error
    if child_context.parent_context:
        print(f"Operation: {child_context.parent_context.message}")
        print(f"Specific error: {child_context.message}")
    ```
    
    ### Error Chains - Cause/Effect Relationships
    ```python
    # Create contexts for cause and effect
    cause_context = ErrorContext(
        message="Database connection failed",
        error_code="STORAGE-DB-CONN-001"
    )
    
    effect_context = ErrorContext(
        message="Failed to read task data",
        error_code="CORE-REPO-TASK-001"
    )
    
    # Link cause to effect
    effect_context.add_cause(cause_context)
    
    # Later, when analyzing the error
    for cause in effect_context.cause_contexts:
        print(f"Caused by: {cause.message}")
    ```
    
    ### Serialization for Logging and Reporting
    ```python
    # Convert to dictionary for structured logging
    context_dict = context.to_dict(include_stack_trace=False)
    
    # Convert to JSON for API responses or storage
    json_str = context.to_json(indent=2)
    
    # Format message for display
    formatted = context.format_message(include_error_code=True)
    # "[CORE-REPO-TASK-001] Failed to find task"
    ```
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[Union[ErrorCode, str]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        exception: Optional[Exception] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the error context.
        
        Args:
            message: Error message describing what went wrong
            error_code: Error code categorizing the error
            severity: Error severity level
            exception: Original exception if applicable
            context_data: Additional contextual data
        """
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()
        self.message = message
        
        # Convert string error code to ErrorCode instance
        if isinstance(error_code, str):
            try:
                self.error_code = ErrorCode.from_string(error_code)
            except ValueError:
                # Use generic error code if the format is invalid
                self.error_code = ErrorCode("CORE", "GENERAL", "UNKNOWN", "000")
        else:
            self.error_code = error_code
            
        self.severity = severity
        self.exception = exception
        self._context_data = context_data or {}
        
        # Capture stack trace if there's an exception
        self.stack_trace = None
        if exception:
            self.stack_trace = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__))
        
        # Store parent and cause error contexts
        self.parent_context = None
        self.cause_contexts = []
    
    def with_parent(self, parent_context: 'ErrorContext') -> 'ErrorContext':
        """
        Set the parent error context.
        
        Args:
            parent_context: Parent error context
            
        Returns:
            Self for method chaining
        """
        self.parent_context = parent_context
        return self
    
    def add_cause(self, cause_context: 'ErrorContext') -> 'ErrorContext':
        """
        Add a cause error context.
        
        Args:
            cause_context: Error context representing the cause of this error
            
        Returns:
            Self for method chaining
        """
        self.cause_contexts.append(cause_context)
        return self
    
    def add_context_data(self, key: str, value: Any) -> 'ErrorContext':
        """
        Add additional contextual data.
        
        Args:
            key: Context data key
            value: Context data value
            
        Returns:
            Self for method chaining
        """
        self._context_data[key] = value
        return self
    
    def merge_context_data(self, context_data: Dict[str, Any]) -> 'ErrorContext':
        """
        Merge additional contextual data.
        
        Args:
            context_data: Context data dictionary to merge
            
        Returns:
            Self for method chaining
        """
        self._context_data.update(context_data)
        return self
    
    def get_context_data(self, key: str, default: Any = None) -> Any:
        """
        Get contextual data for a key.
        
        Args:
            key: Context data key
            default: Default value if key is not found
            
        Returns:
            Contextual data value or default
        """
        return self._context_data.get(key, default)
    
    def to_dict(self, include_stack_trace: bool = True) -> Dict[str, Any]:
        """
        Convert the error context to a dictionary.
        
        Args:
            include_stack_trace: Whether to include the stack trace
            
        Returns:
            Dictionary representation of the error context
        """
        result = {
            'id': self.id,
            'timestamp': self.timestamp,
            'message': self.message,
            'error_code': str(self.error_code) if self.error_code else None,
            'severity': self.severity.name,
            'context_data': self._context_data,
        }
        
        if include_stack_trace and self.stack_trace:
            result['stack_trace'] = self.stack_trace
            
        if self.parent_context:
            result['parent_context'] = {
                'id': self.parent_context.id,
                'error_code': str(self.parent_context.error_code) if self.parent_context.error_code else None,
                'message': self.parent_context.message
            }
            
        if self.cause_contexts:
            result['cause_contexts'] = [
                {
                    'id': cause.id,
                    'error_code': str(cause.error_code) if cause.error_code else None,
                    'message': cause.message
                }
                for cause in self.cause_contexts
            ]
            
        return result
    
    def to_json(self, include_stack_trace: bool = True, indent: int = 2) -> str:
        """
        Convert the error context to a JSON string.
        
        Args:
            include_stack_trace: Whether to include the stack trace
            indent: JSON indentation level
            
        Returns:
            JSON string representation of the error context
        """
        return json.dumps(self.to_dict(include_stack_trace), indent=indent)
    
    def format_message(self, include_error_code: bool = True) -> str:
        """
        Format the error message with additional context.
        
        Args:
            include_error_code: Whether to include the error code
            
        Returns:
            Formatted error message
        """
        message = self.message
        if include_error_code and self.error_code:
            message = f"[{self.error_code}] {message}"
            
        if self.severity in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL):
            message = f"{self.severity.name}: {message}"
            
        return message
    
    def __str__(self) -> str:
        """Return the string representation of the error context."""
        return self.format_message()


class ErrorContextBuilder:
    """
    Builder for creating error contexts with fluent interface.
    
    This builder makes it easy to create detailed error contexts
    with a chainable API.
    
    ## Usage Examples
    
    ### Basic Builder Usage
    ```python
    # Create a simple error context with the builder
    context = ErrorContextBuilder("Failed to find task") \
        .with_code("CORE-REPO-TASK-001") \
        .with_severity(ErrorSeverity.ERROR) \
        .build()
    ```
    
    ### Adding Context Data
    ```python
    # Add individual context data items
    context = ErrorContextBuilder("Failed to update task") \
        .with_code("CORE-SERVICE-TASK-002") \
        .with_data("task_id", "tsk_123") \
        .with_data("field", "status") \
        .with_data("value", "invalid_status") \
        .build()
        
    # Add a dictionary of context data
    context_data = {
        "task_id": "tsk_123",
        "user_id": "usr_456",
        "timestamp": "2023-04-01T12:34:56"
    }
    
    context = ErrorContextBuilder("Permission denied") \
        .with_code("CORE-AUTH-PERM-001") \
        .with_data_dict(context_data) \
        .build()
    ```
    
    ### Working with Exceptions
    ```python
    try:
        # Some operation that might fail
        result = process_task("tsk_123")
    except Exception as e:
        # Create context with the builder
        context = ErrorContextBuilder("Task processing failed") \
            .with_code("CORE-SERVICE-TASK-001") \
            .with_exception(e) \
            .with_data("task_id", "tsk_123") \
            .build()
            
        # Attach to the exception
        e.error_context = context
        raise
    ```
    
    ### Building Complex Error Chains
    ```python
    # Create parent context
    parent_context = ErrorContextBuilder("User operation failed") \
        .with_code("CORE-SERVICE-USER-001") \
        .with_data("user_id", "usr_456") \
        .build()
        
    # Create cause context
    cause_context = ErrorContextBuilder("Network timeout") \
        .with_code("CORE-NET-CONN-001") \
        .with_severity(ErrorSeverity.WARNING) \
        .build()
        
    # Create main error context with parent and cause
    context = ErrorContextBuilder("Failed to update user task list") \
        .with_code("CORE-SERVICE-TASK-003") \
        .with_severity(ErrorSeverity.ERROR) \
        .with_data("user_id", "usr_456") \
        .with_data("task_count", 42) \
        .with_parent(parent_context) \
        .with_cause(cause_context) \
        .build()
    ```
    """
    
    def __init__(self, message: str):
        """
        Initialize the error context builder.
        
        Args:
            message: Base error message
        """
        self._message = message
        self._error_code = None
        self._severity = ErrorSeverity.ERROR
        self._exception = None
        self._context_data = {}
        self._parent_context = None
        self._cause_contexts = []
    
    def with_code(self, error_code: Union[ErrorCode, str]) -> 'ErrorContextBuilder':
        """
        Set the error code.
        
        Args:
            error_code: Error code categorizing the error
            
        Returns:
            Self for method chaining
        """
        self._error_code = error_code
        return self
    
    def with_severity(self, severity: ErrorSeverity) -> 'ErrorContextBuilder':
        """
        Set the error severity.
        
        Args:
            severity: Error severity level
            
        Returns:
            Self for method chaining
        """
        self._severity = severity
        return self
    
    def with_exception(self, exception: Exception) -> 'ErrorContextBuilder':
        """
        Set the original exception.
        
        Args:
            exception: Original exception
            
        Returns:
            Self for method chaining
        """
        self._exception = exception
        return self
    
    def with_data(self, key: str, value: Any) -> 'ErrorContextBuilder':
        """
        Add contextual data.
        
        Args:
            key: Context data key
            value: Context data value
            
        Returns:
            Self for method chaining
        """
        self._context_data[key] = value
        return self
    
    def with_data_dict(self, context_dict: Dict[str, Any]) -> 'ErrorContextBuilder':
        """
        Add multiple contextual data items.
        
        Args:
            context_dict: Dictionary of context data
            
        Returns:
            Self for method chaining
        """
        self._context_data.update(context_dict)
        return self
    
    def with_parent(self, parent_context: ErrorContext) -> 'ErrorContextBuilder':
        """
        Set the parent error context.
        
        Args:
            parent_context: Parent error context
            
        Returns:
            Self for method chaining
        """
        self._parent_context = parent_context
        return self
    
    def with_cause(self, cause_context: ErrorContext) -> 'ErrorContextBuilder':
        """
        Add a cause error context.
        
        Args:
            cause_context: Error context representing the cause of this error
            
        Returns:
            Self for method chaining
        """
        self._cause_contexts.append(cause_context)
        return self
    
    def build(self) -> ErrorContext:
        """
        Build the error context.
        
        Returns:
            Constructed ErrorContext instance
        """
        context = ErrorContext(
            message=self._message,
            error_code=self._error_code,
            severity=self._severity,
            exception=self._exception,
            context_data=self._context_data
        )
        
        if self._parent_context:
            context.with_parent(self._parent_context)
            
        for cause in self._cause_contexts:
            context.add_cause(cause)
            
        return context


class ErrorCodeRegistry:
    """
    Registry for error codes to ensure uniqueness and provide descriptions.
    
    This registry maintains a mapping of error codes to their descriptions
    and ensures that all error codes are unique.
    """
    
    def __init__(self):
        """Initialize the error code registry."""
        self._registry: Dict[str, str] = {}
    
    def register(self, error_code: Union[ErrorCode, str], description: str) -> None:
        """
        Register an error code with its description.
        
        Args:
            error_code: Error code to register
            description: Description of what the error code represents
            
        Raises:
            ValueError: If the error code is already registered
        """
        code_str = str(error_code)
        if code_str in self._registry:
            raise ValueError(f"Error code '{code_str}' is already registered")
        
        self._registry[code_str] = description
    
    def get_description(self, error_code: Union[ErrorCode, str]) -> Optional[str]:
        """
        Get the description for an error code.
        
        Args:
            error_code: Error code to look up
            
        Returns:
            Description of the error code or None if not found
        """
        return self._registry.get(str(error_code))
    
    def is_registered(self, error_code: Union[ErrorCode, str]) -> bool:
        """
        Check if an error code is registered.
        
        Args:
            error_code: Error code to check
            
        Returns:
            True if the error code is registered, False otherwise
        """
        return str(error_code) in self._registry
    
    def list_codes(self, component: Optional[str] = None, 
                  category: Optional[str] = None,
                  subcategory: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        List registered error codes and their descriptions.
        
        Args:
            component: Filter by component
            category: Filter by category
            subcategory: Filter by subcategory
            
        Returns:
            List of (error_code, description) tuples
        """
        result = []
        
        for code_str, description in self._registry.items():
            try:
                error_code = ErrorCode.from_string(code_str)
                
                # Apply filters
                if component and error_code.component != component:
                    continue
                if category and error_code.category != category:
                    continue
                if subcategory and error_code.subcategory != subcategory:
                    continue
                    
                result.append((code_str, description))
            except ValueError:
                # Skip invalid code strings
                continue
                
        return result


# Create a global error code registry
error_code_registry = ErrorCodeRegistry()


F = TypeVar('F', bound=Callable[..., Any])

def with_error_context(
    error_message: Optional[str] = None,
    error_code: Optional[Union[ErrorCode, str]] = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR
) -> Callable[[F], F]:
    """
    Decorator that adds error context to exceptions raised within a function.
    
    Args:
        error_message: Error message template
        error_code: Error code
        severity: Error severity
        
    Returns:
        Decorator function
        
    ## Usage Examples
    
    ### Basic Usage
    ```python
    from refactor.core.exceptions import with_error_context, ErrorCode
    
    # Add context to any exceptions raised in the function
    @with_error_context(
        error_message="Failed to process task",
        error_code=ErrorCode("CORE", "SERVICE", "TASK", "001")
    )
    def process_task(task_id, status):
        # Function implementation
        # Any exceptions will get error context automatically
        pass
    ```
    
    ### Using without Arguments
    ```python
    # Can be used without arguments for simple cases
    # Will use function name and exception message
    @with_error_context
    def update_task_status(task_id, status):
        # The decorator will create a generic message:
        # f"Error in update_task_status: {exception_message}"
        pass
    ```
    
    ### Using with String Error Code
    ```python
    @with_error_context(
        error_message="Task validation failed",
        error_code="CORE-VALID-TASK-001",
        severity=ErrorSeverity.WARNING
    )
    def validate_task(task):
        if not task.has_required_fields():
            raise ValidationError("Missing required fields")
    ```
    
    ### Handling Decorated Function Errors
    ```python
    try:
        # Call the decorated function
        result = process_task("tsk_123", "complete")
    except Exception as e:
        # Check if the exception has error context
        if hasattr(e, 'error_context'):
            # Access the error context
            context = e.error_context
            
            # Log with structured context
            logger.error(
                f"Error: {context.message}",
                extra={
                    "error_code": str(context.error_code),
                    "severity": context.severity.name,
                    "task_id": context.get_context_data("task_id"),
                    "status": context.get_context_data("status")
                }
            )
            
            # The context will include function arguments automatically
            # (except sensitive ones like 'password', 'secret', etc.)
        else:
            # Handle regular exceptions
            logger.error(f"Unhandled error: {str(e)}")
    ```
    
    ### Using with Helper Functions
    ```python
    from refactor.core.exceptions import with_error_context, get_service_error_code
    
    # Use with helper functions for standard error codes
    @with_error_context(
        error_message="Failed to complete task",
        error_code=get_service_error_code("TASK", "003")
    )
    def complete_task(task_id):
        # Implementation
        pass
    ```
    
    ### Class Method Decoration
    ```python
    class TaskService:
        @with_error_context(
            error_message="Failed to update task in service",
            error_code="CORE-SERVICE-TASK-002"
        )
        def update_task(self, task_id, data):
            # Implementation
            pass
    ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Don't rewrap if it already has context
                if hasattr(e, 'error_context'):
                    raise
                
                # Generate a message if none was provided
                message = error_message
                if message is None:
                    message = f"Error in {func.__name__}: {str(e)}"
                
                # Create context
                context_builder = ErrorContextBuilder(message) \
                    .with_exception(e) \
                    .with_severity(severity)
                    
                if error_code:
                    context_builder.with_code(error_code)
                
                # Add function arguments as context data
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                
                # Add safe, non-sensitive arguments to context
                context_args = {}
                for name, value in bound.arguments.items():
                    # Skip 'self' and 'cls' arguments
                    if name in ('self', 'cls'):
                        continue
                    
                    # Skip password and sensitive arguments
                    if any(sensitive in name.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                        context_args[name] = '[REDACTED]'
                    else:
                        # Try to convert to string safely
                        try:
                            str_value = str(value)
                            # Truncate long values
                            if len(str_value) > 100:
                                str_value = str_value[:100] + '...'
                            context_args[name] = str_value
                        except Exception:
                            context_args[name] = f"<{type(value).__name__}>"
                
                context_builder.with_data_dict(context_args)
                
                # Attach the context to the exception
                e.error_context = context_builder.build()  # type: ignore
                
                # Re-raise the exception with context
                raise
                
        return cast(F, wrapper)
    
    # Handle the case where the decorator is used without arguments
    if callable(error_message) and error_code is None and severity == ErrorSeverity.ERROR:
        func_to_wrap = error_message
        error_message = None
        return decorator(func_to_wrap)  # type: ignore 