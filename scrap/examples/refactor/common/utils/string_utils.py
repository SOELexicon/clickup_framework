"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/utils/string_utils.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - FileManager: Uses for file path normalization and slugification
    - ImportExportSystem: Uses for slug generation and text normalization
    - TaskManager: Uses to ensure consistent text formatting
    - RESTfulAPI: Uses for URL slug generation
    - TemplateParser: Uses for consistent newline handling

Purpose:
    Provides utility functions for string manipulation, including
    conversion to URL-friendly slugs, newline normalization across
    platforms, and text truncation with proper suffixes.

Requirements:
    - Must handle Unicode characters correctly
    - Must provide consistent behavior across platforms
    - Must preserve text meaning during transformations
    - CRITICAL: Newline normalization must maintain content integrity
    - CRITICAL: String operations must be stable across Python versions

String Utility Module

This module provides utility functions for string manipulation.
"""
import re
import os
import sys
from typing import Optional


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text: The text to convert
        
    Returns:
        A slug version of the text
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading and trailing hyphens
    slug = slug.strip('-')
    
    return slug


def normalize_newlines(text: str, target_newline: Optional[str] = None) -> str:
    """
    Normalize newlines in a string to a consistent format.
    
    Args:
        text: The text to normalize
        target_newline: The target newline character sequence (default: platform-specific)
        
    Returns:
        Text with normalized newlines
    """
    if target_newline is None:
        target_newline = os.linesep
    
    # First convert all newlines to '\n'
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Then convert to the target newline format
    if target_newline != '\n':
        normalized = normalized.replace('\n', target_newline)
        
    return normalized


def truncate(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate text to a maximum length with a suffix.
    
    Args:
        text: The text to truncate
        max_length: Maximum length of the truncated text
        suffix: Suffix to append if truncated (default: '...')
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncated_length = max_length - len(suffix)
    if truncated_length <= 0:
        # If max_length is too small, just return the suffix truncated
        return suffix[:max_length]
    
    return text[:truncated_length] + suffix


def get_platform_newline() -> str:
    """
    Get the platform-specific newline character.
    
    Returns:
        The platform-specific newline character sequence
    """
    return os.linesep


def is_windows() -> bool:
    """
    Check if the current platform is Windows.
    
    Returns:
        True if the platform is Windows, False otherwise
    """
    return sys.platform.startswith('win') 