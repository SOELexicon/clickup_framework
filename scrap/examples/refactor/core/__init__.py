"""
Core Module

This is the central module of the ClickUp JSON Manager that provides the
core functionality for managing tasks, spaces, folders, and lists. It
contains entity definitions, business logic services, repositories, and
exceptions.

The core module is designed to be independent of specific storage mechanisms
and user interfaces, allowing it to be used with different frontends
(CLI, API, GUI) and storage backends (JSON files, databases).

Subpackages:
    - entities: Data model classes
    - services: Business logic services
    - repositories: Data access interfaces
    - exceptions: Error handling classes
"""

from refactor.core.exceptions import (
    ClickUpError,
    ValidationError,
    EntityError,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    TaskCompletionError,
    CircularDependencyError,
    ConfigurationError,
    StorageError,
    FileOperationError,
    SerializationError,
    RepositoryError,
    RepositoryConnectionError,
    RepositoryDataError,
    RepositoryOperationError,
    ServiceError,
    BusinessRuleViolationError,
    ServiceOperationError,
    ServiceDependencyError,
    CommandError,
    PermissionError,
    DependencyError,
    QueryError,
    PluginError,
    # Error context classes
    ErrorSeverity,
    ErrorCode,
    ErrorContext,
    ErrorContextBuilder,
    ErrorCodeRegistry,
    error_code_registry,
    with_error_context,
    # Error code utilities
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
    'get_validation_error_code',
]
