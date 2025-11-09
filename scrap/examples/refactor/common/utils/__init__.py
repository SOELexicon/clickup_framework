"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/utils/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses validation utilities for data integrity
    - FileManager: Uses string utilities for file operations
    - CommandSystem: Uses validation for command argument parsing
    - StorageManager: Uses string utilities for content normalization
    - EntityClasses: Use validation utilities for property validation

Purpose:
    Provides common utility functions for string manipulation, validation,
    and other general-purpose operations used throughout the application.
    Centralizes frequently used functions to ensure consistency and reusability.

Requirements:
    - Utilities must be pure functions with no side effects
    - String utilities must handle Unicode properly
    - Validation utilities must provide clear error messages
    - Functions must be well-tested for edge cases
    - CRITICAL: Validation must not modify input data
    - CRITICAL: String operations must preserve content meaning

Utilities Package

This package provides common utility functions for the ClickUp JSON Manager.
"""

from .string_utils import slugify, normalize_newlines, truncate
from .validation_utils import (
    validate_required, 
    validate_type, 
    validate_enum,
    validate_custom,
    validate_min_length,
    validate_max_length,
    validate_regex
)

__all__ = [
    # String utilities
    'slugify',
    'normalize_newlines',
    'truncate',
    
    # Validation utilities
    'validate_required',
    'validate_type',
    'validate_enum',
    'validate_custom',
    'validate_min_length',
    'validate_max_length',
    'validate_regex'
]
