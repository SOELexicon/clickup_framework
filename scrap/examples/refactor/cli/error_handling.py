"""
Error handling utilities for CLI commands.

This module provides error handling functions and classes for CLI commands,
ensuring consistent error reporting and appropriate exit codes.
"""

from typing import Optional, Tuple, Dict, Type
import inspect
import json
import os
from enum import Enum
from refactor.core.exceptions import (
    ErrorCode as CoreErrorCode,
    error_code_registry,
    get_storage_error_code,
    get_command_error_code,
    get_repo_error_code,
    get_validation_error_code,
    get_service_error_code,
    ErrorContext,
    ErrorContextBuilder,
    ValidationError
)

# Define error code enum for unit tests
class ErrorCode(Enum):
    """
    Error code enum for CLI exit codes.
    Used for integration testing.
    """
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENT = 2
    FILE_NOT_FOUND = 3
    INVALID_JSON = 4
    TASK_NOT_FOUND = 5
    PERMISSION_DENIED = 6
    VALIDATION_ERROR = 7
    DEPENDENCY_ERROR = 8

# Register CLI-specific error codes if not already registered
def register_cli_error_codes():
    """Register CLI-specific error codes if they haven't been registered yet."""
    # Use tuples of (code, description) to avoid hashing issues
    codes_to_register = [
        (get_command_error_code("EXEC", "001"), "General command execution error"),
        (get_command_error_code("ARGS", "001"), "Invalid command arguments"),
        (get_command_error_code("ABORT", "001"), "Command execution aborted"),
        (get_command_error_code("GENERAL", "000"), "Unknown CLI error")
    ]
    
    for code, description in codes_to_register:
        if not error_code_registry.is_registered(str(code)):
            error_code_registry.register(code, description)

# Register CLI error codes
register_cli_error_codes()

# System error mapping
SYSTEM_ERROR_MAPPING: Dict[Type[Exception], CoreErrorCode] = {
    FileNotFoundError: get_storage_error_code("FILE", "001"),  # STORAGE-FILE-ERROR-001
    PermissionError: get_storage_error_code("FILE", "002"),    # STORAGE-FILE-ERROR-002
    json.JSONDecodeError: get_storage_error_code("JSON", "001") # STORAGE-JSON-ERROR-001
}

class CLIError(Exception):
    """Exception class for CLI errors with structured error codes and context."""
    
    def __init__(self, message: str, code: CoreErrorCode = get_command_error_code("EXEC", "001"), context_data: Optional[dict] = None):
        """
        Initialize a new CLI error.
        
        Args:
            message: Error message
            code: Error code (defaults to general command execution error)
            context_data: Optional dictionary of context data
        """
        self.message = message
        self.code = code
        self.error_context = ErrorContextBuilder(message) \
            .with_code(str(code)) \
            .with_data("cli_command", inspect.stack()[1].function) \
            .with_data_dict(context_data or {}) \
            .build()
        super().__init__(message)


def map_exception_to_error_code(exception: Exception) -> CoreErrorCode:
    """
    Map an exception to an appropriate error code.
    
    Args:
        exception: Exception to map
        
    Returns:
        Mapped error code
    """
    # Check for CLIError first (it already has a code)
    if isinstance(exception, CLIError):
        return exception.code
        
    # Map system errors using predefined mapping
    for error_type, error_code in SYSTEM_ERROR_MAPPING.items():
        if isinstance(exception, error_type):
            return error_code
        
    # Map core module errors by name
    exception_name = exception.__class__.__name__
    
    # Entity related errors - using helper functions for consistent codes
    if exception_name == 'EntityNotFoundError':
        return get_repo_error_code("ENTITY", "001")  # CORE-REPO-ENTITY-001
    if exception_name == 'TaskNotFoundError':
        return get_repo_error_code("TASK", "001")    # CORE-REPO-TASK-001
    if exception_name == 'ListNotFoundError':
        return get_repo_error_code("LIST", "001")    # CORE-REPO-LIST-001
    if exception_name == 'FolderNotFoundError':
        return get_repo_error_code("FOLDER", "001")  # CORE-REPO-FOLDER-001
    if exception_name == 'SpaceNotFoundError':
        return get_repo_error_code("SPACE", "001")   # CORE-REPO-SPACE-001
    if exception_name == 'EntityAlreadyExistsError':
        return get_repo_error_code("ENTITY", "002")  # CORE-REPO-ENTITY-002
        
    # Map validation errors to CORE-VALID-GENERAL-001
    if isinstance(exception, ValidationError):
        return get_validation_error_code("001")  # CORE-VALID-GENERAL-001
        
    # Validation errors - using helper functions
    if exception_name == 'InvalidArgumentError':
        return get_command_error_code("ARGS", "001") # CLI-COMMAND-ARGS-001
        
    # Relationship errors - using helper functions
    if exception_name == 'RelationshipError':
        return get_service_error_code("TASK", "004") # CORE-SERVICE-TASK-004
    if exception_name == 'CircularDependencyError':
        return get_service_error_code("TASK", "004") # CORE-SERVICE-TASK-004
    if exception_name == 'DependencyError':
        return get_service_error_code("TASK", "004") # CORE-SERVICE-TASK-004
        
    # Default to general error with proper structure
    return get_command_error_code("GENERAL", "000")  # CLI-COMMAND-GENERAL-000


def validate_args(args, required_args):
    """
    Validate that required arguments are present.
    
    Args:
        args: Namespace object containing arguments
        required_args: List of required argument names
        
    Returns:
        Tuple of (valid: bool, error_message: Optional[str])
    """
    for arg_name in required_args:
        if not hasattr(args, arg_name) or getattr(args, arg_name) is None:
            return False, f"Missing required argument: {arg_name}"
    return True, None


def validate_file_exists(file_path):
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (valid: bool, error_message: Optional[str])
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    if not os.path.isfile(file_path):
        return False, f"Not a file: {file_path}"
    return True, None


def validate_json_file(file_path):
    """
    Validate that a file exists and is valid JSON.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (valid: bool, error_message: Optional[str], data: Optional[dict])
    """
    valid, error = validate_file_exists(file_path)
    if not valid:
        return valid, error, None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, None, data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON file: {str(e)}", None
    except Exception as e:
        return False, f"Error reading file: {str(e)}", None


def handle_cli_error(func):
    """
    Decorator for handling CLI errors with structured error codes and context.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that returns integer exit codes (0 for success, non-zero for failure)
    """
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, str):
                if result:  # Non-empty string indicates error
                    error_code = result
                    print(f"Error [{error_code}]: Command failed")
                    return 1  # Return error exit code
                else:  # Empty string indicates success
                    return 0  # Return success exit code
            if isinstance(result, int):  # Integer indicates explicit exit code
                return result
            return 0  # Return success exit code for any other type
        except CLIError as e:
            print(f"Error [{e.code}]: {e.message}")
            if hasattr(e, 'error_context'):
                print(f"Context: {e.error_context.to_json()}")
            return 1  # Return error exit code
        except Exception as e:
            # Map the exception to an appropriate error code
            error_code = map_exception_to_error_code(e)
            error_context = ErrorContextBuilder(str(e)) \
                .with_code(str(error_code)) \
                .with_data("cli_command", func.__name__) \
                .build()
            print(f"Error [{error_code}]: {str(e)}")
            print(f"Context: {error_context.to_json()}")
            return 1  # Return error exit code
    return wrapper 