"""
Utility functions for Mermaid diagram generation.

This module provides common utility functions for path manipulation,
file handling, and other helper operations used across Mermaid generators.
"""

from .path_utils import (
    normalize_folder_path,
    find_common_ancestor,
    get_base_filename,
    simplify_folder_path
)

__all__ = [
    'normalize_folder_path',
    'find_common_ancestor',
    'get_base_filename',
    'simplify_folder_path'
]
