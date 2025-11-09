"""
Core Exceptions Package

This package contains exception classes used throughout the ClickUp JSON Manager
to provide consistent error handling.

This package provides the error handling infrastructure for the core module:
- Base exception classes for repository and service errors
- Error context system for rich error information
- Error code registry for consistent error identification
"""

# Define all exceptions here to avoid circular imports
class ClickUpError(Exception):
    """Base exception for all ClickUp JSON Manager errors."""
    def __init__(self, message=None):
        super().__init__(message or "An error occurred")

class ValidationError(ClickUpError):
    """Exception raised when data validation fails."""
    def __init__(self, message=None):
        super().__init__(message or "Validation failed")

class EntityError(ClickUpError):
    """Base exception for entity-related errors."""
    def __init__(self, entity_type="Entity", message=None):
        self.entity_type = entity_type
        super().__init__(f"{entity_type} error: {message or 'Entity operation failed'}")

class EntityNotFoundError(EntityError):
    """Exception raised when an entity is not found."""
    def __init__(self, entity_id, entity_type="Entity"):
        self.entity_id = entity_id
        self.entity_type = entity_type
        super().__init__(entity_type, f"Not found with ID: {entity_id}")

class EntityAlreadyExistsError(EntityError):
    """Exception raised when an entity already exists."""
    def __init__(self, entity_id, entity_type="Entity"):
        self.entity_id = entity_id
        self.entity_type = entity_type
        super().__init__(entity_type, f"Already exists with ID: {entity_id}")

class TaskCompletionError(ValidationError):
    """Exception raised when a task cannot be marked as complete."""
    pass

class CircularDependencyError(ValidationError):
    """Exception raised when a circular dependency is detected."""
    pass

# TODO: Add RelationshipError here, as it seems to be missing but expected by some tests.
# Example structure:
# class RelationshipError(ClickUpError):
#     """Base exception for relationship-related errors."""
#     def __init__(self, message=None):
#         super().__init__(message or "Relationship operation failed")

class ConfigurationError(ClickUpError):
    """Exception raised when there is a configuration error."""
    pass

class StorageError(ClickUpError):
    """Base exception for storage-related errors."""
    pass

class FileOperationError(StorageError):
    """Exception raised when a file operation fails."""
    def __init__(self, filename, operation, message=None):
        self.filename = filename
        self.operation = operation
        super().__init__(f"Failed to {operation} file '{filename}': {message or 'File operation failed'}")

class SerializationError(StorageError):
    """Exception raised when serialization or deserialization fails."""
    pass

# Repository Exceptions
class RepositoryError(ClickUpError):
    """
    Base exception for repository-related errors.
    
    Used as the base class for all exceptions raised from repository operations.
    
    ## Usage Examples
    
    ### Basic Usage
    ```python
    # Raise a basic repository error
    raise RepositoryError(
        repository_name="TaskRepository",
        message="Failed to query tasks"
    )
    ```
    
    ### Creating Custom Repository Exceptions
    ```python
    # Create a custom repository exception
    class StaleDataError(RepositoryError):
        def __init__(self, repository_name=None, entity_id=None):
            self.entity_id = entity_id
            message = f"Entity data is stale: {entity_id}"
            super().__init__(repository_name, message)
    
    # Raise the custom exception
    raise StaleDataError("TaskRepository", "tsk_123")
    ```
    
    ### Using with Error Context
    ```python
    from refactor.core.exceptions import ErrorContextBuilder
    
    try:
        # Repository operation
        raise RepositoryError("TaskRepository", "Failed to update task")
    except RepositoryError as e:
        # Create error context
        context = ErrorContextBuilder("Repository operation failed") \
            .with_code("CORE-REPO-TASK-003") \
            .with_exception(e) \
            .with_data("repository", e.repository_name) \
            .build()
            
        # Attach context to exception
        e.error_context = context
        raise
    ```
    """
    def __init__(self, repository_name=None, message=None):
        self.repository_name = repository_name or "Repository"
        super().__init__(f"{self.repository_name} error: {message or 'Repository operation failed'}")

class RepositoryConnectionError(RepositoryError):
    """
    Exception raised when a repository connection fails.
    
    This exception is typically raised when the repository cannot establish
    a connection to its underlying data source.
    
    ## Usage Example
    ```python
    class FileTaskRepository:
        def __init__(self, file_path):
            self.file_path = file_path
            
        def connect(self):
            if not os.path.exists(self.file_path):
                raise RepositoryConnectionError(
                    repository_name="FileTaskRepository",
                    message=f"Repository file not found: {self.file_path}"
                )
    ```
    """
    def __init__(self, repository_name=None, message=None):
        super().__init__(repository_name, message or "Could not connect to data source")

class RepositoryDataError(RepositoryError):
    """
    Exception raised when there is an issue with repository data.
    
    This exception is typically raised when the data in a repository
    is invalid, corrupt, or cannot be properly processed.
    
    ## Usage Example
    ```python
    class TaskRepository:
        def get_task(self, task_id):
            data = self._load_task_data(task_id)
            if not self._is_valid_task_data(data):
                raise RepositoryDataError(
                    repository_name="TaskRepository",
                    message=f"Invalid task data format for task: {task_id}"
                )
            return TaskEntity.from_dict(data)
    ```
    """
    def __init__(self, repository_name=None, message=None):
        super().__init__(repository_name, message or "Data error in repository")

class RepositoryOperationError(RepositoryError):
    """
    Exception raised when a repository operation fails.
    
    This exception is raised when a specific repository operation
    (like create, update, delete) fails to complete.
    
    ## Usage Example
    ```python
    class TaskRepository:
        def update_task(self, task):
            try:
                # Update task logic
                self._validate_task(task)
                self._write_task_data(task)
            except Exception as e:
                raise RepositoryOperationError(
                    repository_name="TaskRepository",
                    operation="update",
                    message=f"Failed to update task {task.id}: {str(e)}"
                )
    ```
    """
    def __init__(self, repository_name=None, operation=None, message=None):
        self.operation = operation or "operation"
        super().__init__(repository_name, f"Operation '{self.operation}' failed: {message or 'Operation failed'}")

# Service Exceptions
class ServiceError(ClickUpError):
    """
    Base exception for service-related errors.
    
    Used as the base class for all exceptions raised from service operations.
    
    ## Usage Examples
    
    ### Basic Usage
    ```python
    # Raise a basic service error
    raise ServiceError(
        service_name="TaskService",
        message="Failed to process task operation"
    )
    ```
    
    ### Creating Custom Service Exceptions
    ```python
    # Create a custom service exception
    class TaskLockError(ServiceError):
        def __init__(self, service_name=None, task_id=None):
            self.task_id = task_id
            message = f"Task is locked for editing: {task_id}"
            super().__init__(service_name, message)
    
    # Raise the custom exception
    raise TaskLockError("TaskService", "tsk_123")
    ```
    
    ### Using with Error Context
    ```python
    from refactor.core.exceptions import ErrorContextBuilder
    
    try:
        # Service operation
        raise ServiceError("TaskService", "Failed to complete task")
    except ServiceError as e:
        # Create error context
        context = ErrorContextBuilder("Service operation failed") \
            .with_code("CORE-SERVICE-TASK-001") \
            .with_exception(e) \
            .with_data("service", e.service_name) \
            .build()
            
        # Attach context to exception
        e.error_context = context
        raise
    ```
    """
    def __init__(self, service_name=None, message=None):
        self.service_name = service_name or "Service"
        super().__init__(f"{self.service_name} error: {message or 'Service operation failed'}")

class BusinessRuleViolationError(ServiceError):
    """
    Exception raised when a business rule is violated.
    
    This exception is raised when an operation would violate a business rule
    or constraint defined in the domain model.
    
    ## Usage Example
    ```python
    class TaskService:
        def complete_task(self, task_id):
            task = self.task_repository.get_task(task_id)
            
            # Check business rule: can't complete task with incomplete subtasks
            if self._has_incomplete_subtasks(task):
                raise BusinessRuleViolationError(
                    service_name="TaskService",
                    rule="complete_with_subtasks",
                    message="Cannot complete a task with incomplete subtasks"
                )
                
            task.status = "complete"
            self.task_repository.update_task(task)
    ```
    """
    def __init__(self, service_name=None, rule=None, message=None):
        self.rule = rule or "business_rule"
        super().__init__(service_name, f"Business rule '{self.rule}' violated: {message or 'Rule violation'}")

class ServiceOperationError(ServiceError):
    """
    Exception raised when a service operation fails.
    
    This exception is raised when a specific service operation fails
    to complete, typically due to an issue in a lower layer.
    
    ## Usage Example
    ```python
    class TaskService:
        def update_task_status(self, task_id, status):
            try:
                task = self.task_repository.get_task(task_id)
                task.status = status
                self.task_repository.update_task(task)
            except RepositoryError as e:
                raise ServiceOperationError(
                    service_name="TaskService",
                    operation="update_status",
                    message=f"Failed to update task status: {str(e)}"
                )
    ```
    """
    def __init__(self, service_name=None, operation=None, message=None):
        self.operation = operation or "operation"
        super().__init__(service_name, f"Operation '{self.operation}' failed: {message or 'Operation failed'}")

class ServiceDependencyError(ServiceError):
    """
    Exception raised when a service dependency is missing or fails.
    
    This exception is raised when a service cannot access or
    properly use one of its dependencies (like a repository or another service).
    
    ## Usage Example
    ```python
    class TaskService:
        def __init__(self, task_repository=None, user_service=None):
            self.task_repository = task_repository
            self.user_service = user_service
            
            if not self.task_repository:
                raise ServiceDependencyError(
                    service_name="TaskService",
                    dependency="TaskRepository",
                    message="TaskRepository is required"
                )
                
        def assign_task(self, task_id, user_id):
            # Check if user service is available for user validation
            if not self.user_service:
                raise ServiceDependencyError(
                    service_name="TaskService",
                    dependency="UserService",
                    message="UserService is required for task assignment"
                )
            
            # Use the dependencies
            task = self.task_repository.get_task(task_id)
            user = self.user_service.get_user(user_id)
            # ...
    ```
    """
    def __init__(self, service_name=None, dependency=None, message=None):
        self.dependency = dependency or "dependency"
        super().__init__(service_name, f"Dependency '{self.dependency}' issue: {message or 'Dependency failed'}")

class CommandError(ClickUpError):
    """Exception raised when a command execution fails."""
    def __init__(self, command=None, message=None):
        self.command = command or "command"
        super().__init__(f"Command '{self.command}' error: {message or 'Command execution failed'}")

class PermissionError(ClickUpError):
    """Exception raised when a permission check fails."""
    pass

class DependencyError(ClickUpError):
    """Exception raised when a dependency is missing or incompatible."""
    pass

class QueryError(ClickUpError):
    """Exception raised when a query fails."""
    pass

class PluginError(ClickUpError):
    """Exception raised when a plugin operation fails."""
    pass

# Import error context classes
from .error_context import (
    ErrorSeverity,
    ErrorCode,
    ErrorContext,
    ErrorContextBuilder,
    ErrorCodeRegistry,
    error_code_registry,
    with_error_context
)

# Import error code utilities
from refactor.core.exceptions.error_codes import (
    get_repo_error_code,
    get_service_error_code,
    get_storage_error_code,
    get_command_error_code,
    get_validation_error_code
)

__all__ = [
    'ClickUpError',
    'ValidationError',
    'EntityError',
    'EntityNotFoundError',
    'EntityAlreadyExistsError',
    'TaskCompletionError',
    'CircularDependencyError',
    'ConfigurationError',
    'StorageError',
    'FileOperationError',
    'SerializationError',
    'RepositoryError',
    'RepositoryConnectionError',
    'RepositoryDataError',
    'RepositoryOperationError',
    'ServiceError',
    'BusinessRuleViolationError',
    'ServiceOperationError',
    'ServiceDependencyError',
    'CommandError',
    'PermissionError',
    'DependencyError',
    'QueryError',
    'PluginError',
    # Error context classes
    'ErrorSeverity',
    'ErrorCode',
    'ErrorContext',
    'ErrorContextBuilder',
    'ErrorCodeRegistry',
    'error_code_registry',
    'with_error_context',
    # Error code utilities
    'get_repo_error_code',
    'get_service_error_code',
    'get_storage_error_code',
    'get_command_error_code',
    'get_validation_error_code'
] 