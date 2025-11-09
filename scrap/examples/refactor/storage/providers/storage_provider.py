"""
Storage Module

This module is responsible for data persistence operations, including:
- File I/O with cross-platform compatibility
- JSON data serialization/deserialization
- File integrity verification
- Caching and optimization

Dependencies:
- Common Services: For error handling and logging
"""
from typing import Dict, List, Optional, Any, Union, TextIO
from abc import ABC, abstractmethod
import os
import json


class StorageProvider(ABC):
    """
    Abstract base class defining the storage provider interface.
    
    This interface provides methods for:
    - Reading and writing JSON data
    - Handling file operations with platform compatibility
    - Managing file integrity and backup
    """
    
    @abstractmethod
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be accessed
            JsonDecodeError: If file contains invalid JSON
        """
        pass
    
    @abstractmethod
    def save_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            file_path: Path to the JSON file
            data: Dictionary to serialize and save
            
        Returns:
            True if save succeeded, False otherwise
            
        Raises:
            PermissionError: If file can't be written
            TypeError: If data can't be serialized to JSON
        """
        pass
    
    @abstractmethod
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            PermissionError: If backup can't be created
        """
        pass
    
    @abstractmethod
    def validate_file_integrity(self, file_path: str) -> bool:
        """
        Validate the integrity of a file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False otherwise
            
        Raises:
            PermissionError: If directory can't be created
        """
        pass
    
    @abstractmethod
    def normalize_path(self, file_path: str) -> str:
        """
        Normalize a file path for the current platform.
        
        Args:
            file_path: File path to normalize
            
        Returns:
            Normalized file path
        """
        pass


class JsonFileStorage(StorageProvider):
    """
    Implementation of StorageProvider for JSON file operations.
    
    This class provides:
    - Cross-platform JSON file handling
    - Newline normalization
    - Integrity verification
    - Atomic write operations
    """
    
    def __init__(self, logger=None):
        """
        Initialize the JSON file storage provider.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.logger = logger
        self.newline = self._detect_platform_newline()
        
    def _detect_platform_newline(self) -> str:
        """
        Detect the appropriate newline character for the current platform.
        
        Returns:
            Newline character(s) for the current platform
        """
        return os.linesep
        
    def normalize_newlines(self, content: str) -> str:
        """
        Normalize newlines in a string to the platform-specific format.
        
        Args:
            content: String content to normalize
            
        Returns:
            String with normalized newlines
        """
        # Replace all newlines with platform-specific newline
        return content.replace('\r\n', '\n').replace('\r', '\n').replace('\n', self.newline)
        
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load data from a JSON file with proper newline handling.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be accessed
            JsonDecodeError: If file contains invalid JSON
        """
        normalized_path = self.normalize_path(file_path)
        
        try:
            with open(normalized_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            if self.logger:
                self.logger.error(f"File not found: {normalized_path}")
            raise
        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied: {normalized_path}")
            raise
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f"Invalid JSON in {normalized_path}: {str(e)}")
            raise
        
    def save_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to a JSON file with proper newline handling.
        
        Args:
            file_path: Path to the JSON file
            data: Dictionary to serialize and save
            
        Returns:
            True if save succeeded, False otherwise
            
        Raises:
            PermissionError: If file can't be written
            TypeError: If data can't be serialized to JSON
        """
        normalized_path = self.normalize_path(file_path)
        temp_path = f"{normalized_path}.tmp"
        
        try:
            # Create parent directory if it doesn't exist
            directory = os.path.dirname(normalized_path)
            if directory and not os.path.exists(directory):
                self.ensure_directory_exists(directory)
                
            # Write to temporary file first
            with open(temp_path, 'w', encoding='utf-8') as file:
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                normalized_json = self.normalize_newlines(json_str)
                file.write(normalized_json)
                
            # Create backup of original file if it exists
            if os.path.exists(normalized_path):
                self.backup_file(normalized_path)
                
            # Rename temporary file to target file
            os.replace(temp_path, normalized_path)
            return True
            
        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied: {normalized_path}")
            raise
        except TypeError as e:
            if self.logger:
                self.logger.error(f"Cannot serialize to JSON: {str(e)}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving data to {normalized_path}: {str(e)}")
            # Clean up temporary file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
            
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            PermissionError: If backup can't be created
        """
        normalized_path = self.normalize_path(file_path)
        backup_path = f"{normalized_path}.bak"
        
        try:
            import shutil
            shutil.copy2(normalized_path, backup_path)
            return backup_path
        except FileNotFoundError:
            if self.logger:
                self.logger.error(f"File not found for backup: {normalized_path}")
            raise
        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied for backup: {normalized_path}")
            raise
    
    def validate_file_integrity(self, file_path: str) -> bool:
        """
        Validate the integrity of a JSON file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file contains valid JSON, False otherwise
        """
        normalized_path = self.normalize_path(file_path)
        
        try:
            with open(normalized_path, 'r', encoding='utf-8') as file:
                json.load(file)
            return True
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            return False
    
    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False otherwise
            
        Raises:
            PermissionError: If directory can't be created
        """
        normalized_path = self.normalize_path(directory_path)
        
        try:
            os.makedirs(normalized_path, exist_ok=True)
            return True
        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied: {normalized_path}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating directory {normalized_path}: {str(e)}")
            return False
    
    def normalize_path(self, file_path: str) -> str:
        """
        Normalize a file path for the current platform.
        
        Args:
            file_path: File path to normalize
            
        Returns:
            Normalized file path
        """
        return os.path.normpath(os.path.abspath(file_path)) 