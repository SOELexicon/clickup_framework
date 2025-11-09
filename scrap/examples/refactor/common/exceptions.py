"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/exceptions.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses these exceptions for error handling and propagation
    - CommandSystem: Maps exceptions to CLI error messages and exit codes
    - RESTfulAPI: Converts exceptions to appropriate HTTP status codes
    - PluginSystem: Uses exceptions for plugin validation and error isolation
    - ValidationSystem: Raises specific validation exceptions

Purpose:
    Defines the exception hierarchy for the ClickUp JSON Manager.
    Provides a structured approach to error handling with categorized exceptions,
    context preservation, error codes, and user-friendly messages.

Requirements:
    - All exceptions MUST include an appropriate error code
    - Exceptions should support context data for debugging
    - Error messages must be user-friendly and informative
    - CRITICAL: Exception context must not include sensitive information
    - CRITICAL: New exception types must follow the established hierarchy

Common Exceptions Module

This module defines the exception hierarchy for the ClickUp JSON Manager.
It provides a structured approach to error handling with:
- Categorized exceptions
- Context preservation
- Error codes
- User-friendly messages
"""
from typing import Dict, Any, Optional


class ClickUpManagerError(Exception):
    """Base exception for all ClickUp Manager errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Error message
            error_code: Optional error code for identification
            context: Optional dictionary with contextual information
        """
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        
    def add_context(self, key: str, value: Any) -> 'ClickUpManagerError':
        """
        Add additional context to the exception.
        
        Args:
            key: Context key
            value: Context value
            
        Returns:
            Self, for method chaining
        """
        self.context[key] = value
        return self


# Validation Errors (Error codes 1xxx)

class ValidationError(ClickUpManagerError):
    """Raised when validation fails for an input or operation."""
    pass


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing."""
    
    def __init__(self, field_name: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with the name of the missing field.
        
        Args:
            field_name: Name of the missing field
            context: Optional dictionary with contextual information
        """
        message = f"Required field '{field_name}' is missing"
        super().__init__(message, error_code="ERR1001", context=context)
        self.field_name = field_name


class InvalidValueError(ValidationError):
    """Raised when a field value is invalid."""
    
    def __init__(self, field_name: str, value: Any, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the invalid value.
        
        Args:
            field_name: Name of the field with invalid value
            value: The invalid value
            reason: Reason why the value is invalid
            context: Optional dictionary with contextual information
        """
        message = f"Invalid value for field '{field_name}': {reason}"
        super().__init__(message, error_code="ERR1002", context=context)
        self.field_name = field_name
        self.value = value
        self.reason = reason


class InvalidQueryError(ValidationError):
    """Raised when a search query is invalid."""
    
    def __init__(self, query: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the invalid query.
        
        Args:
            query: The invalid query
            reason: Reason why the query is invalid
            context: Optional dictionary with contextual information
        """
        message = f"Invalid query: {reason}"
        super().__init__(message, error_code="ERR1003", context=context)
        self.query = query
        self.reason = reason


# Data Access Errors (Error codes 2xxx)

class DataAccessError(ClickUpManagerError):
    """Raised when data access operations fail."""
    pass


class EntityNotFoundError(DataAccessError):
    """Raised when an entity cannot be found."""
    
    def __init__(self, entity_type: str, identifier: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the missing entity.
        
        Args:
            entity_type: Type of entity (e.g., 'task', 'space')
            identifier: Identifier used to look up the entity
            context: Optional dictionary with contextual information
        """
        message = f"Could not find {entity_type} with identifier '{identifier}'"
        super().__init__(message, error_code="ERR2001", context=context)
        self.entity_type = entity_type
        self.identifier = identifier


class TaskNotFoundError(EntityNotFoundError):
    """Raised when a task cannot be found."""
    
    def __init__(self, identifier: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with the task identifier.
        
        Args:
            identifier: Task identifier (ID or name)
            context: Optional dictionary with contextual information
        """
        super().__init__("task", identifier, context)


class ListNotFoundError(EntityNotFoundError):
    """Raised when a list cannot be found."""
    
    def __init__(self, identifier: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with the list identifier.
        
        Args:
            identifier: List identifier (ID or name)
            context: Optional dictionary with contextual information
        """
        super().__init__("list", identifier, context)


class FolderNotFoundError(EntityNotFoundError):
    """Raised when a folder cannot be found."""
    
    def __init__(self, identifier: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with the folder identifier.
        
        Args:
            identifier: Folder identifier (ID or name)
            context: Optional dictionary with contextual information
        """
        super().__init__("folder", identifier, context)


class SpaceNotFoundError(EntityNotFoundError):
    """Raised when a space cannot be found."""
    
    def __init__(self, identifier: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with the space identifier.
        
        Args:
            identifier: Space identifier (ID or name)
            context: Optional dictionary with contextual information
        """
        super().__init__("space", identifier, context)


class DuplicateEntityError(DataAccessError):
    """Raised when trying to create an entity that already exists."""
    
    def __init__(self, entity_type: str, identifier: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the duplicate entity.
        
        Args:
            entity_type: Type of entity (e.g., 'task', 'space')
            identifier: Identifier for the duplicate entity
            context: Optional dictionary with contextual information
        """
        message = f"{entity_type} with identifier '{identifier}' already exists"
        super().__init__(message, error_code="ERR2002", context=context)
        self.entity_type = entity_type
        self.identifier = identifier


# File Operation Errors (Error codes 3xxx)

class FileOperationError(ClickUpManagerError):
    """Raised when file operations fail."""
    pass


class FileReadError(FileOperationError):
    """Raised when a file cannot be read."""
    
    def __init__(self, file_path: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the file read error.
        
        Args:
            file_path: Path to the file
            reason: Reason for the read failure
            context: Optional dictionary with contextual information
        """
        message = f"Could not read file '{file_path}': {reason}"
        super().__init__(message, error_code="ERR3001", context=context)
        self.file_path = file_path
        self.reason = reason


class FileWriteError(FileOperationError):
    """Raised when a file cannot be written."""
    
    def __init__(self, file_path: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the file write error.
        
        Args:
            file_path: Path to the file
            reason: Reason for the write failure
            context: Optional dictionary with contextual information
        """
        message = f"Could not write to file '{file_path}': {reason}"
        super().__init__(message, error_code="ERR3002", context=context)
        self.file_path = file_path
        self.reason = reason


class JsonParseError(FileOperationError):
    """Raised when JSON parsing fails."""
    
    def __init__(self, file_path: str, error_details: str, line: Optional[int] = None, column: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the JSON parsing error.
        
        Args:
            file_path: Path to the file
            error_details: Details about the parsing error
            line: Line number where the error occurred
            column: Column number where the error occurred
            context: Optional dictionary with contextual information
        """
        location = f" at line {line}, column {column}" if line and column else ""
        message = f"Invalid JSON in file '{file_path}'{location}: {error_details}"
        super().__init__(message, error_code="ERR3003", context=context)
        self.file_path = file_path
        self.error_details = error_details
        self.line = line
        self.column = column


# Relationship Errors (Error codes 4xxx)

class RelationshipError(ClickUpManagerError):
    """Raised when task relationship operations fail."""
    pass


class CircularDependencyError(RelationshipError):
    """Raised when a circular dependency is detected."""
    
    def __init__(self, task_id: str, dependency_chain: list, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the circular dependency.
        
        Args:
            task_id: ID of the task involved in circular dependency
            dependency_chain: List of task IDs in the dependency chain
            context: Optional dictionary with contextual information
        """
        chain_str = " -> ".join(dependency_chain)
        message = f"Circular dependency detected: {chain_str} -> {task_id}"
        super().__init__(message, error_code="ERR4001", context=context)
        self.task_id = task_id
        self.dependency_chain = dependency_chain


class InvalidRelationshipTypeError(RelationshipError):
    """Raised when an invalid relationship type is specified."""
    
    def __init__(self, relationship_type: str, valid_types: list, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the invalid relationship type.
        
        Args:
            relationship_type: The invalid relationship type
            valid_types: List of valid relationship types
            context: Optional dictionary with contextual information
        """
        valid_types_str = ", ".join(valid_types)
        message = f"Invalid relationship type: '{relationship_type}'. Valid types are: {valid_types_str}"
        super().__init__(message, error_code="ERR4002", context=context)
        self.relationship_type = relationship_type
        self.valid_types = valid_types


# Configuration Errors (Error codes 5xxx)

class ConfigurationError(ClickUpManagerError):
    """Raised when configuration operations fail."""
    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration is missing."""
    
    def __init__(self, config_key: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with the missing configuration key.
        
        Args:
            config_key: Key of the missing configuration
            context: Optional dictionary with contextual information
        """
        message = f"Required configuration '{config_key}' is missing"
        super().__init__(message, error_code="ERR5001", context=context)
        self.config_key = config_key


class InvalidConfigurationError(ConfigurationError):
    """Raised when a configuration value is invalid."""
    
    def __init__(self, config_key: str, value: Any, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the invalid configuration.
        
        Args:
            config_key: Key of the invalid configuration
            value: The invalid value
            reason: Reason why the value is invalid
            context: Optional dictionary with contextual information
        """
        message = f"Invalid configuration value for '{config_key}': {reason}"
        super().__init__(message, error_code="ERR5002", context=context)
        self.config_key = config_key
        self.value = value
        self.reason = reason


# For backward compatibility with plugins
ConfigError = InvalidConfigurationError


# Authorization Errors (Error codes 6xxx)

class AuthorizationError(ClickUpManagerError):
    """Raised when an operation is not authorized."""
    
    def __init__(self, operation: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the authorization failure.
        
        Args:
            operation: The operation that was attempted
            reason: Reason why the operation is not authorized
            context: Optional dictionary with contextual information
        """
        message = f"Not authorized to perform operation '{operation}': {reason}"
        super().__init__(message, error_code="ERR6001", context=context)
        self.operation = operation
        self.reason = reason


# Network Errors (Error codes 7xxx)

class NetworkError(ClickUpManagerError):
    """Raised when network operations fail."""
    
    def __init__(self, operation: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the network failure.
        
        Args:
            operation: The network operation that failed
            reason: Reason for the failure
            context: Optional dictionary with contextual information
        """
        message = f"Network operation '{operation}' failed: {reason}"
        super().__init__(message, error_code="ERR7001", context=context)
        self.operation = operation
        self.reason = reason


# Data Integrity Errors (Error codes 8xxx)

class DataCorruptionError(ClickUpManagerError):
    """Raised when data corruption is detected."""
    
    def __init__(self, entity_type: str, identifier: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the data corruption.
        
        Args:
            entity_type: Type of entity with corrupted data
            identifier: Identifier for the entity
            reason: Description of the corruption
            context: Optional dictionary with contextual information
        """
        message = f"Data corruption detected in {entity_type} '{identifier}': {reason}"
        super().__init__(message, error_code="ERR8001", context=context)
        self.entity_type = entity_type
        self.identifier = identifier
        self.reason = reason


# Operation Errors (Error codes 9xxx)

class OperationNotSupportedError(ClickUpManagerError):
    """Raised when an operation is not supported."""
    
    def __init__(self, operation: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the unsupported operation.
        
        Args:
            operation: The unsupported operation
            reason: Reason why the operation is not supported
            context: Optional dictionary with contextual information
        """
        message = f"Operation '{operation}' is not supported: {reason}"
        super().__init__(message, error_code="ERR9001", context=context)
        self.operation = operation
        self.reason = reason


# Plugin Errors (Error codes 10xxx)

class PluginError(ClickUpManagerError):
    """Raised when plugin operations fail."""
    
    def __init__(self, plugin_id: str, operation: str, reason: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize with details about the plugin operation failure.
        
        Args:
            plugin_id: ID of the plugin
            operation: The operation that failed
            reason: Reason for the failure
            context: Optional dictionary with contextual information
        """
        message = f"Plugin operation '{operation}' failed for plugin '{plugin_id}': {reason}"
        super().__init__(message, error_code="ERR10001", context=context)
        self.plugin_id = plugin_id
        self.operation = operation
        self.reason = reason 