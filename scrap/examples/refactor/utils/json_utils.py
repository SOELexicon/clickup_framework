"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/utils/json_utils.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - TaskManager: Loads and saves task data from JSON files
    - ConfigManager: Persists configuration to JSON
    - BackupManager: Creates and restores JSON backups
    - ImportExportManager: Handles JSON transformations for external systems
    - StorageManager: Core JSON persistence layer

Purpose:
    Provides robust utilities for handling JSON data throughout the application,
    addressing cross-platform compatibility issues, error handling, and common
    JSON operations. This module ensures consistent behavior when working with 
    JSON files and strings, handling edge cases like different newline formats
    and providing detailed error information when JSON parsing fails.

Requirements:
    - CRITICAL: Must handle cross-platform newline differences (\r\n vs \n)
    - CRITICAL: Must provide detailed error context when JSON parsing fails
    - CRITICAL: Must safely handle file operations with proper error handling
    - Must maintain UTF-8 encoding for all JSON operations
    - Must preserve JSON structure during read/write operations
    - Should provide helpful debugging information in error messages
    - Must create parent directories automatically when saving files

JSON utilities for the ClickUp JSON Manager.

This module provides utilities for working with JSON data, including:
- Loading JSON from files with error handling
- Saving JSON to files with proper formatting
- Handling special cases like newlines in text
"""

import json
import os
import logging
from typing import Dict, Any, Optional, TextIO, Union

logger = logging.getLogger(__name__)


def load_json_data(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from a file with proper error handling.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as a dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not os.path.exists(file_path):
        logger.error(f"JSON file not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {str(e)}")
        raise


def save_json_data(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """
    Save JSON data to a file with proper formatting.
    
    Args:
        data: Data to save
        file_path: Path to save the JSON file
        indent: Indentation level for formatting
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {str(e)}")
        return False


def deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively update a nested dictionary.
    
    Args:
        target: Target dictionary to update
        source: Source dictionary with new values
        
    Returns:
        Updated dictionary
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            target[key] = deep_update(target[key], value)
        else:
            target[key] = value
    return target


def normalize_newlines(json_str: str) -> str:
    """
    Normalize newline characters in a JSON string to ensure cross-platform compatibility.
    
    Args:
        json_str: JSON string to normalize
        
    Returns:
        Normalized JSON string
    """
    # Replace Windows-style newlines with Unix-style
    return json_str.replace('\r\n', '\n')


def safe_json_loads(json_str: str) -> Dict[str, Any]:
    """
    Safely load JSON string with error handling and newline normalization.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed JSON data
        
    Raises:
        json.JSONDecodeError: If the string contains invalid JSON
    """
    try:
        normalized = normalize_newlines(json_str)
        return json.loads(normalized)
    except json.JSONDecodeError as e:
        # If there's an error, try to show the problematic part
        line_no = e.lineno
        col_no = e.colno
        lines = normalized.split('\n')
        
        if 0 <= line_no - 1 < len(lines):
            context = lines[line_no - 1]
            pointer = ' ' * (col_no - 1) + '^'
            error_msg = f"JSON error at line {line_no}, column {col_no}:\n{context}\n{pointer}\n{str(e)}"
            logger.error(error_msg)
        
        raise 