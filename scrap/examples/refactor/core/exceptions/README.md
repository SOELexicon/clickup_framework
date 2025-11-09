# Error Handling Guidelines

## Error Context Pattern

The Error Context pattern provides structured error information across the application:

```python
class ErrorContext:
    def __init__(self,
                 code: ErrorCodes,
                 message: str,
                 details: Optional[Dict[str, Any]] = None,
                 inner: Optional[Exception] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.inner = inner
```

### Usage Examples

1. **Validation Errors**
```python
def validate_status(self, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValidationError(ErrorContext(
            code=ErrorCodes.INVALID_STATUS,
            message=f"Invalid status: {status}",
            details={
                "status": status,
                "valid_statuses": list(VALID_STATUSES)
            }
        ))
```

2. **Repository Errors**
```python
def find_by_id(self, id: str) -> TaskEntity:
    try:
        task = self._storage.find_one({"id": id})
        if not task:
            raise TaskNotFoundError(ErrorContext(
                code=ErrorCodes.TASK_NOT_FOUND,
                message=f"Task not found: {id}",
                details={"task_id": id}
            ))
        return task
    except StorageError as e:
        raise RepositoryError(ErrorContext(
            code=ErrorCodes.STORAGE_ERROR,
            message="Failed to retrieve task",
            details={"task_id": id},
            inner=e
        ))
```

3. **Command Errors**
```python
def execute(self, args: Dict[str, Any]) -> CommandResult:
    try:
        # Command logic
        return CommandResult.success(data)
    except ValidationError as e:
        return CommandResult.validation_error(
            message=str(e),
            details=e.details,
            code=e.code
        )
    except TaskNotFoundError as e:
        return CommandResult.error(
            message=str(e),
            code=e.code
        )
    except Exception as e:
        return CommandResult.system_error(
            message="Unexpected error occurred",
            inner=e
        )
```

## Error Code Organization

Error codes are organized by domain and severity:

```python
class ErrorCodes(Enum):
    # Validation Errors (1000-1999)
    INVALID_STATUS = 1001
    INVALID_NAME = 1002
    INVALID_PRIORITY = 1003
    
    # Repository Errors (2000-2999)
    TASK_NOT_FOUND = 2001
    STORAGE_ERROR = 2002
    DUPLICATE_ID = 2003
    
    # Command Errors (3000-3999)
    INVALID_COMMAND = 3001
    MISSING_ARGUMENT = 3002
    
    # System Errors (9000-9999)
    CONFIGURATION_ERROR = 9001
    INITIALIZATION_ERROR = 9002
```

## Exception Hierarchy

```
BaseError
├── ValidationError
├── RepositoryError
│   ├── TaskNotFoundError
│   ├── DuplicateIdError
│   └── StorageError
├── CommandError
│   ├── InvalidCommandError
│   └── MissingArgumentError
└── SystemError
    ├── ConfigurationError
    └── InitializationError
```

## Best Practices

1. **Error Context Creation**
   - Always include an error code
   - Provide descriptive messages
   - Add relevant details for debugging
   - Preserve inner exceptions when wrapping

2. **Error Handling Levels**
   - Handle errors at appropriate levels
   - Transform low-level errors to domain errors
   - Preserve error context when re-throwing
   - Log errors with appropriate severity

3. **Error Response Format**
   - Use consistent error response structure
   - Include all relevant error context
   - Provide actionable error messages
   - Handle errors gracefully in UI/CLI

4. **Testing Error Scenarios**
   - Test error paths explicitly
   - Verify error context details
   - Test error propagation
   - Validate error handling in integration tests

## Example Error Handling Flow

```python
# 1. Low-level error occurs
try:
    with open(file_path, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    # 2. Transform to domain error
    raise StorageError(ErrorContext(
        code=ErrorCodes.STORAGE_ERROR,
        message="Failed to parse JSON data",
        details={"file_path": file_path},
        inner=e
    ))

# 3. Repository layer handles storage error
try:
    data = self._storage.load()
except StorageError as e:
    # 4. Transform to repository error
    raise RepositoryError(ErrorContext(
        code=ErrorCodes.REPOSITORY_ERROR,
        message="Failed to load repository data",
        inner=e
    ))

# 5. Command layer provides user-friendly response
try:
    result = repository.find_by_id(task_id)
except RepositoryError as e:
    # 6. Transform to command result
    return CommandResult.error(
        message="Could not retrieve task",
        code=e.code,
        details=e.details
    )
``` 