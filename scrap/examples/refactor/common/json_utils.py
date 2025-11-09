"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/json_utils.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - FileManager: Uses these utilities for reading and writing JSON template files
    - CoreManager: Relies on proper JSON encoding/decoding for configuration
    - ImportExportSystem: Uses for import/export functionality
    - SearchSystem: Uses for query result serialization
    - MigrationTools: Uses for cross-platform file conversion

Purpose:
    Provides utilities for handling JSON data with special attention to
    cross-platform newline compatibility, ensuring consistent file format
    regardless of the operating system used to create or modify files.

Requirements:
    - MUST handle newlines consistently across Windows, Linux, and macOS
    - MUST preserve Unicode characters in JSON files
    - JSON formatting must be consistent and human-readable
    - CRITICAL: Must not lose data during format conversion
    - CRITICAL: Must handle large files efficiently

Utilities for JSON handling with special attention to newline handling.

This module provides utilities for handling JSON data with special
attention to cross-platform newline compatibility.
"""

import json
import os
import sys
from typing import Any, Dict, List, Union, Optional


class NewlineEncoderDecoder:
    """
    Handles JSON encoding and decoding with proper newline handling.
    
    This class provides static methods for encoding and decoding JSON
    with special handling for newline characters to ensure cross-platform
    compatibility.
    """
    
    @staticmethod
    def encode(data: Any, **kwargs) -> str:
        """
        Encode Python data structure to JSON string with proper newline handling.
        
        Args:
            data: The Python data structure to encode
            **kwargs: Additional arguments to pass to json.dumps
            
        Returns:
            JSON string with normalized newlines
        """
        # Use platform-specific newlines for the output
        if 'indent' not in kwargs:
            kwargs['indent'] = 2
            
        # Ensure ASCII is False to handle Unicode properly
        if 'ensure_ascii' not in kwargs:
            kwargs['ensure_ascii'] = False
            
        # Convert to JSON
        json_str = json.dumps(data, **kwargs)
        
        # Normalize newlines to the system default
        json_str = json_str.replace('\r\n', '\n').replace('\r', '\n')
        if os.name == 'nt':  # Windows
            json_str = json_str.replace('\n', '\r\n')
            
        return json_str
    
    @staticmethod
    def decode(json_str: str, **kwargs) -> Any:
        """
        Decode JSON string to Python data structure with proper newline handling.
        
        Args:
            json_str: The JSON string to decode
            **kwargs: Additional arguments to pass to json.loads
            
        Returns:
            Python data structure
        """
        # Normalize newlines before parsing
        json_str = json_str.replace('\r\n', '\n').replace('\r', '\n')
        
        # Parse JSON
        return json.loads(json_str, **kwargs)
    
    @staticmethod
    def write_to_file(data: Any, file_path: str, **kwargs) -> None:
        """
        Write Python data structure to a JSON file with proper newline handling.
        
        Args:
            data: The Python data structure to encode
            file_path: Path to the file to write
            **kwargs: Additional arguments to pass to json.dumps
        """
        # Encode the data
        json_str = NewlineEncoderDecoder.encode(data, **kwargs)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    @staticmethod
    def read_from_file(file_path: str, **kwargs) -> Any:
        """
        Read a JSON file to a Python data structure with proper newline handling.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional arguments to pass to json.loads
            
        Returns:
            Python data structure
        """
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            json_str = f.read()
        
        # Decode the data
        return NewlineEncoderDecoder.decode(json_str, **kwargs) 