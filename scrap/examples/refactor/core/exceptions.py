#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core exception classes and error handling for the CLI application.

This module provides a structured approach to error handling with:
- Consistent error codes
- Context-rich error information
- Extensible error hierarchies
"""

from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
import time
import uuid


class ErrorCode:
    """
    Structured error code representation.
    
    Format: {MODULE}-{COMPONENT}-{CATEGORY}-{CODE}
    Example: CLI-TASK-VALIDATION-001
    """
    
    def __init__(
        self, 
        module: str, 
        component: str, 
        category: str, 
        code: str
    ):
        """
        Initialize a new error code.
        
        Args:
            module: High-level module (CLI, API, CORE)
            component: Component name (TASK, USER, FILE)
            category: Error category (VALIDATION, NOT_FOUND)
            code: Specific error code (typically a 3-digit number)
        """
        self.module = module.upper()
        self.component = component.upper()
        self.category = category.upper()
        self.code = code
    
    def __str__(self) -> str:
        """Convert to string representation."""
        return f"{self.module}-{self.component}-{self.category}-{self.code}"


@dataclass
class ErrorContext:
    """
    Rich context for error reporting and handling.
    
    Contains detailed information about the error, including:
    - Message: Human-readable description
    - Error code: Structured identifier
    - Timestamp: When the error occurred
    - Data: Additional contextual information
    """
    
    message: str
    error_code: str = ""
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Dict[str, Any] = field(default_factory=dict)


class ErrorContextBuilder:
    """Builder pattern for creating error contexts."""
    
    def __init__(self, message: str):
        """
        Initialize with an error message.
        
        Args:
            message: The error message
        """
        self.message = message
        self.error_code = ""
        self.data = {}
    
    def with_code(self, code: str) -> 'ErrorContextBuilder':
        """
        Set the error code.
        
        Args:
            code: The error code string
            
        Returns:
            Self for chaining
        """
        self.error_code = code
        return self
    
    def with_data(self, key: str, value: Any) -> 'ErrorContextBuilder':
        """
        Add a data item to the context.
        
        Args:
            key: Data key
            value: Data value
            
        Returns:
            Self for chaining
        """
        self.data[key] = value
        return self
    
    def with_data_dict(self, data: Dict[str, Any]) -> 'ErrorContextBuilder':
        """
        Add multiple data items from a dictionary.
        
        Args:
            data: Dictionary of data to add
            
        Returns:
            Self for chaining
        """
        self.data.update(data)
        return self
    
    def build(self) -> ErrorContext:
        """
        Build and return the error context.
        
        Returns:
            Fully configured ErrorContext
        """
        return ErrorContext(
            message=self.message,
            error_code=self.error_code,
            data=self.data
        )


class CLIError(Exception):
    """
    Base exception for CLI errors with structured error information.
    
    Provides consistent error handling with:
    - Human-readable message
    - Structured error code
    - Rich error context
    """
    
    def __init__(
        self, 
        message: str, 
        code: Union[ErrorCode, str], 
        error_context: Optional[ErrorContext] = None
    ):
        """
        Initialize the error.
        
        Args:
            message: Human-readable error message
            code: Error code (ErrorCode instance or string)
            error_context: Optional error context
        """
        super().__init__(message)
        self.message = message
        self.code = str(code)
        
        # Create error context if not provided
        if error_context is None:
            self.error_context = ErrorContextBuilder(message) \
                .with_code(self.code) \
                .build()
        else:
            self.error_context = error_context


class ValidationError(CLIError):
    """Exception raised for data validation errors."""
    pass


class FileError(CLIError):
    """Exception raised for file operations errors."""
    pass


class ConfigError(CLIError):
    """Exception raised for configuration errors."""
    pass


class OperationError(CLIError):
    """Exception raised for operation failures."""
    pass


def get_command_error_code(category: str, code: str) -> ErrorCode:
    """
    Helper to create command-related error codes.
    
    Args:
        category: Error category
        code: Specific error code
        
    Returns:
        Structured ErrorCode
    """
    return ErrorCode("CLI", "COMMAND", category, code)


def get_task_error_code(category: str, code: str) -> ErrorCode:
    """
    Helper to create task-related error codes.
    
    Args:
        category: Error category
        code: Specific error code
        
    Returns:
        Structured ErrorCode
    """
    return ErrorCode("CLI", "TASK", category, code)


def get_file_error_code(category: str, code: str) -> ErrorCode:
    """
    Helper to create file-related error codes.
    
    Args:
        category: Error category
        code: Specific error code
        
    Returns:
        Structured ErrorCode
    """
    return ErrorCode("CLI", "FILE", category, code) 