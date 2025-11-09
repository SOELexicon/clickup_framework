"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - All modules: Import common utilities, exceptions, and services
    - CoreManager: Depends on the common utilities for core functionality
    - CommandSystem: Uses exceptions and logging from common
    - PluginSystem: Leverages DI container from common
    - RESTfulAPI: Uses validation and exception handling

Purpose:
    Serves as the central package for common utilities, services, and
    functionality used throughout the ClickUp JSON Manager. Provides
    a unified import interface for commonly used components.

Requirements:
    - Must expose all core utilities through a clean public API
    - Must maintain backward compatibility for imports
    - Re-exports should be organized by functional category
    - CRITICAL: Should not include business logic or domain-specific code
    - CRITICAL: Must prevent circular dependencies

Common utilities package for the ClickUp JSON Manager refactored code.

This package contains common utilities used across the application.
"""

# Re-export exceptions
from .exceptions import (
    ClickUpManagerError,
    ConfigurationError,
    ValidationError,
    RequiredFieldError,
    InvalidValueError,
    FileOperationError,
    TaskNotFoundError,
    ListNotFoundError,
    FolderNotFoundError,
    SpaceNotFoundError,
    EntityNotFoundError,
    DuplicateEntityError,
    AuthorizationError,
    NetworkError,
    DataCorruptionError,
    OperationNotSupportedError,
    InvalidQueryError,
    DataAccessError
)

# Re-export logging
from .logging import (
    Logger,
    get_logger,
    LogLevel,
    LogHandler,
    ConsoleHandler,
    FileHandler,
    configure_logging
)

# Re-export configuration
from .config import (
    ConfigManager,
    ConfigurationSource,
    FileConfigurationSource,
    DictConfigurationSource,
    EnvironmentConfigurationSource
)

# Re-export dependency injection
from .di import (
    ServiceContainer,
    ServiceLifetime,
    ServiceDescriptor,
    ServiceRegistration,
    ServiceResolver,
    ServiceCollection,
    ServiceProvider,
    create_default_service_provider
)

# Re-export string utilities
from .utils import (
    slugify,
    normalize_newlines,
    truncate,
    validate_required,
    validate_type,
    validate_enum,
    validate_custom,
    validate_min_length,
    validate_max_length,
    validate_regex
)

__all__ = [
    # Exceptions
    'ClickUpManagerError',
    'ConfigurationError',
    'ValidationError',
    'RequiredFieldError',
    'InvalidValueError',
    'FileOperationError',
    'TaskNotFoundError',
    'ListNotFoundError',
    'FolderNotFoundError',
    'SpaceNotFoundError',
    'EntityNotFoundError',
    'DuplicateEntityError',
    'AuthorizationError',
    'NetworkError',
    'DataCorruptionError',
    'OperationNotSupportedError',
    'InvalidQueryError',
    'DataAccessError',
    
    # Logging
    'Logger',
    'get_logger',
    'LogLevel',
    'LogHandler',
    'ConsoleHandler',
    'FileHandler',
    'configure_logging',
    
    # Configuration
    'ConfigManager',
    'ConfigurationSource',
    'FileConfigurationSource',
    'DictConfigurationSource',
    'EnvironmentConfigurationSource',
    
    # Dependency Injection
    'ServiceContainer',
    'ServiceLifetime',
    'ServiceDescriptor',
    'ServiceRegistration',
    'ServiceResolver',
    'ServiceCollection',
    'ServiceProvider',
    'create_default_service_provider',
    
    # Utilities
    'slugify',
    'normalize_newlines',
    'truncate',
    'validate_required',
    'validate_type',
    'validate_enum',
    'validate_custom',
    'validate_min_length',
    'validate_max_length',
    'validate_regex'
]
