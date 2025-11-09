"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/utils/validation_utils.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - EntityClasses: Use for property validation
    - CommandSystem: Validates command arguments
    - TaskService: Validates task field values
    - ImportExportSystem: Validates import data integrity
    - PluginManager: Validates plugin configurations

Purpose:
    Provides a comprehensive set of validation utilities for ensuring
    data integrity throughout the application. Includes functions for
    required field validation, type checking, value constraints,
    and custom validation rules.

Requirements:
    - Must raise appropriate exception types with clear error messages
    - Must include context information in exceptions for debugging
    - Must handle edge cases (null values, empty collections, etc.)
    - Must correctly validate complex data types
    - CRITICAL: Must not modify input data during validation
    - CRITICAL: Must fail fast when encountering invalid data
    - CRITICAL: Must provide detailed error messages for end users

Validation Utility Module

This module provides utility functions for data validation.
"""
from typing import Any, Dict, List, Type, TypeVar, Union, Optional, Callable, Pattern
from ..exceptions import RequiredFieldError, InvalidValueError
import re
from enum import Enum

T = TypeVar('T')


def validate_required(data: Dict[str, Any], field_name: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate that a required field is present and not None.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        context: Optional context information for error reporting
        
    Raises:
        RequiredFieldError: If the field is missing or None
    """
    if field_name not in data or data[field_name] is None:
        raise RequiredFieldError(field_name, context)


def validate_type(data: Dict[str, Any], field_name: str, expected_type: Type[T], 
                  context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate that a field has the expected type.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        expected_type: The expected type
        context: Optional context information for error reporting
        
    Raises:
        InvalidValueError: If the field has an incorrect type
    """
    if field_name not in data or data[field_name] is None:
        # Skip validation for missing or None fields
        return
    
    value = data[field_name]
    if not isinstance(value, expected_type):
        raise InvalidValueError(
            field_name, 
            value, 
            f"Expected type {expected_type.__name__}, got {type(value).__name__}",
            context
        )


def validate_enum(data: Dict[str, Any], field_name: str, valid_values: List[Any],
                  case_sensitive: bool = True, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate that a field has one of the valid values.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        valid_values: List of valid values
        case_sensitive: Whether to do case-sensitive comparison for strings
        context: Optional context information for error reporting
        
    Raises:
        InvalidValueError: If the field has an invalid value
    """
    if field_name not in data or data[field_name] is None:
        # Skip validation for missing or None fields
        return
    
    value = data[field_name]
    
    # Case-insensitive comparison for strings
    if isinstance(value, str) and not case_sensitive:
        if value.lower() not in [str(v).lower() for v in valid_values if v is not None]:
            valid_str = ", ".join([str(v) for v in valid_values])
            raise InvalidValueError(
                field_name,
                value,
                f"Value must be one of: {valid_str}",
                context
            )
    else:
        if value not in valid_values:
            valid_str = ", ".join([str(v) for v in valid_values])
            raise InvalidValueError(
                field_name,
                value,
                f"Value must be one of: {valid_str}",
                context
            )


def validate_custom(data: Dict[str, Any], field_name: str, validator: Callable[[Any], bool],
                    error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate a field using a custom validation function.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        validator: A function that takes the value and returns True if valid
        error_message: Error message if validation fails
        context: Optional context information for error reporting
        
    Raises:
        InvalidValueError: If the value fails validation
    """
    if field_name not in data or data[field_name] is None:
        # Skip validation for missing or None fields
        return
    
    value = data[field_name]
    if not validator(value):
        raise InvalidValueError(field_name, value, error_message, context)


def validate_min_length(data: Dict[str, Any], field_name: str, min_length: int,
                        context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate that a string or list field has at least the minimum length.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        min_length: The minimum allowed length
        context: Optional context information for error reporting
        
    Raises:
        InvalidValueError: If the field is too short
    """
    if field_name not in data or data[field_name] is None:
        # Skip validation for missing or None fields
        return
    
    value = data[field_name]
    if not hasattr(value, "__len__"):
        raise InvalidValueError(
            field_name,
            value,
            f"Value must support length checking",
            context
        )
    
    if len(value) < min_length:
        raise InvalidValueError(
            field_name,
            value,
            f"Value must have at least {min_length} items/characters",
            context
        )


def validate_max_length(data: Dict[str, Any], field_name: str, max_length: int,
                        context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate that a string or list field does not exceed the maximum length.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        max_length: The maximum allowed length
        context: Optional context information for error reporting
        
    Raises:
        InvalidValueError: If the field is too long
    """
    if field_name not in data or data[field_name] is None:
        # Skip validation for missing or None fields
        return
    
    value = data[field_name]
    if not hasattr(value, "__len__"):
        raise InvalidValueError(
            field_name,
            value,
            f"Value must support length checking",
            context
        )
    
    if len(value) > max_length:
        raise InvalidValueError(
            field_name,
            value,
            f"Value must have at most {max_length} items/characters",
            context
        )


def validate_regex(data: Dict[str, Any], field_name: str, pattern: str,
                   context: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate that a string field matches a regular expression pattern.
    
    Args:
        data: The data dictionary to validate
        field_name: The field name to check
        pattern: The regular expression pattern to match
        context: Optional context information for error reporting
        
    Raises:
        InvalidValueError: If the field does not match the pattern
    """
    if field_name not in data or data[field_name] is None:
        # Skip validation for missing or None fields
        return
    
    value = data[field_name]
    if not isinstance(value, str):
        raise InvalidValueError(
            field_name,
            value,
            f"Value must be a string for regex validation",
            context
        )
    
    if not re.match(pattern, value):
        raise InvalidValueError(
            field_name,
            value,
            f"Value must match pattern: {pattern}",
            context
        ) 