"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/utils/validation.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)
    - tsk_4fd89a12 - Enhance Input Validation (related)

Used By:
    - Entity Classes: For validating field values
    - Services: For validating input parameters
    - Repositories: For validating entities before storage
    - CLI Commands: For validating user input

Purpose:
    Provides centralized validation utilities used across the application
    to ensure data consistency, enforce business rules, and present clear
    error messages when validation fails.

Requirements:
    - Must provide consistent validation across all application layers
    - Must return clear error messages suitable for end users
    - Must handle common validation patterns (emptiness, ranges, types)
    - CRITICAL: Must not throw exceptions, but return error messages
    - CRITICAL: Must be performant for frequent validation operations

Changes:
    - v1: Initial implementation with basic validators
    - v2: Added type validation
    - v3: Enhanced ID format validation with regex
    - v4: Improved error message clarity

Lessons Learned:
    - Centralized validation functions improve consistency
    - Error messages should be user-friendly for UI display
    - Return Optional[str] pattern works well for validation pipelines
    - Common validation patterns emerge across different entity types
"""

import re
from typing import Union, Optional, Any


def validate_not_empty(value: str, field_name: str = "field") -> Optional[str]:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/utils/validation.py
    dohcount: 1
    
    Used By:
        - Entity Validation: For required string fields
        - Service Layer: For validating input parameters
        - CLI Commands: For validating required arguments
    
    Purpose:
        Validates that a string value is not empty (null or zero-length),
        providing a standardized way to check for required string fields
        across all components of the application.
    
    Requirements:
        - Must handle both None and empty string as failures
        - Must return clear, user-friendly error message
        - Must include field name in error message
        - CRITICAL: Must not throw exceptions
    
    Args:
        value: The string value to validate
        field_name: Name of the field for the error message
            
    Returns:
        Error message string if validation fails, None if validation passes
        
    Example Usage:
        ```python
        # Validating a task name
        error = validate_not_empty(task.name, "Task name")
        if error:
            raise ValidationError(error)
            
        # In a validation pipeline
        errors = []
        if error := validate_not_empty(user_input, "Username"):
            errors.append(error)
        ```
    """
    if not value:
        return f"{field_name} cannot be empty"
    return None


def validate_id_format(value: str, field_name: str = "ID") -> Optional[str]:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/utils/validation.py
    dohcount: 1
    
    Used By:
        - Entity Validation: For ID fields across all entities
        - Services: For validating ID parameters
        - Repository Layer: For ensuring ID integrity
        - Import/Export: For validating external IDs
    
    Purpose:
        Validates that an ID follows the required format convention
        (three lowercase letters followed by underscore and alphanumeric
        identifier), ensuring consistency in ID formatting across the system.
    
    Requirements:
        - Must check for empty values
        - Must enforce standard ID pattern
        - Must be performant for frequent ID checks
        - CRITICAL: Pattern must match the established ID convention
    
    Args:
        value: The ID string to validate
        field_name: Name of the ID field for the error message
            
    Returns:
        Error message string if validation fails, None if validation passes
        
    Example Usage:
        ```python
        # Validating a task ID
        error = validate_id_format(task_id, "Task ID")
        if error:
            raise ValidationError(error)
            
        # Common entity ID patterns:
        # - tsk_XXXXXXXX: Task ID
        # - stk_XXXXXXXX: Subtask ID
        # - chk_XXXXXXXX: Checklist ID
        # - spc_XXXXXXXX: Space ID
        # - fld_XXXXXXXX: Folder ID
        # - lst_XXXXXXXX: List ID
        ```
    """
    if not value:
        return f"{field_name} cannot be empty"
        
    # Check format: typically three lowercase letters followed by underscore and alphanumeric
    if not re.match(r'^[a-z]{3}_[a-zA-Z0-9]+$', value):
        return f"{field_name} must follow the format 'xxx_identifier'"
        
    return None


def validate_in_range(value: Union[int, float], 
                     min_val: Union[int, float], 
                     max_val: Union[int, float],
                     field_name: str = "value") -> Optional[str]:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/utils/validation.py
    dohcount: 1
    
    Used By:
        - Entity Validation: For numeric fields with constraints
        - Services: For validating numeric parameters
        - CLI Commands: For validating numeric user input
        - Scoring System: For validating score values
    
    Purpose:
        Validates that a numeric value falls within a specified inclusive range,
        providing a standardized way to enforce numeric boundaries for fields
        like priorities, scores, and other constrained numeric values.
    
    Requirements:
        - Must handle both integer and floating-point values
        - Must check both lower and upper bounds (inclusive)
        - Must include value range in error message
        - CRITICAL: Must use inclusive comparison (>=, <=)
    
    Args:
        value: The numeric value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        field_name: Name of the field for the error message
            
    Returns:
        Error message string if validation fails, None if validation passes
        
    Example Usage:
        ```python
        # Validating task priority (1-5)
        error = validate_in_range(task.priority, 1, 5, "Priority")
        if error:
            raise ValidationError(error)
            
        # Validating a percentage
        error = validate_in_range(score, 0.0, 1.0, "Score percentage")
        if error:
            raise ValidationError(error)
        ```
    """
    if value < min_val or value > max_val:
        return f"{field_name} must be between {min_val} and {max_val}"
    return None


def validate_type(value: Any, expected_type: type, field_name: str = "value") -> Optional[str]:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/utils/validation.py
    dohcount: 1
    
    Used By:
        - Entity Validation: For type checking fields
        - Services: For validating parameter types
        - CLI Commands: For type checking arguments
        - Repository Layer: For verifying entity types
    
    Purpose:
        Validates that a value is of the expected type, providing a standardized
        way to perform type checking across the application to catch type errors
        early and provide clear error messages.
    
    Requirements:
        - Must handle any value and type combination
        - Must include expected type name in error message
        - CRITICAL: Must use isinstance for proper inheritance handling
        - CRITICAL: Should handle built-in types and custom classes
    
    Args:
        value: The value to validate
        expected_type: The expected type to check against
        field_name: Name of the field for the error message
            
    Returns:
        Error message string if validation fails, None if validation passes
        
    Example Usage:
        ```python
        # Validate parameter types
        error = validate_type(task_id, str, "Task ID")
        if error:
            raise ValidationError(error)
            
        # Validate entity types
        error = validate_type(entity, TaskEntity, "Entity")
        if error:
            raise ValidationError(error)
        ```
    """
    if not isinstance(value, expected_type):
        return f"{field_name} must be of type {expected_type.__name__}"
    return None 