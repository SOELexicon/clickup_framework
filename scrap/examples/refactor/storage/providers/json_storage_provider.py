"""
JSON Storage Provider

This module implements the storage provider interface for JSON file operations:
- JSON file reading/writing with proper encoding
- Cross-platform newline handling
- File integrity verification
- Atomic operations and backups

Dependencies:
- Common Services: For error handling and logging
"""
from typing import Dict, List, Optional, Any, Union, TextIO
import os
import json
import datetime
import shutil
from .storage_provider_interface import StorageProviderInterface


class JsonStorageProvider(StorageProviderInterface):
    """
    Implementation of StorageProviderInterface for JSON file operations.
    
    This class provides:
    - Cross-platform JSON file handling
    - Newline normalization
    - Integrity verification
    - Atomic write operations
    """
    
    def __init__(self, logger=None):
        """
        Initialize the JSON storage provider.
        
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
            ValueError: If file contains invalid JSON
        """
        normalized_path = self.normalize_storage_path(file_path)
        
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
            raise ValueError(f"Invalid JSON in {normalized_path}: {str(e)}")
        
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
        normalized_path = self.normalize_storage_path(file_path)
        temp_path = f"{normalized_path}.tmp"
        
        try:
            # Create parent directory if it doesn't exist
            directory = os.path.dirname(normalized_path)
            if directory and not os.path.exists(directory):
                self.ensure_storage_location_exists(directory)
                
            # Write to temporary file first
            with open(temp_path, 'w', encoding='utf-8') as file:
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                normalized_json = self.normalize_newlines(json_str)
                file.write(normalized_json)
                
            # Create backup of original file if it exists
            if os.path.exists(normalized_path):
                self.backup_data(normalized_path)
                
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
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False
            
    def backup_data(self, file_path: str) -> str:
        """
        Create a backup of a JSON file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            PermissionError: If backup can't be created
        """
        normalized_path = self.normalize_storage_path(file_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{normalized_path}.{timestamp}.bak"
        
        try:
            if not os.path.exists(normalized_path):
                raise FileNotFoundError(f"File not found: {normalized_path}")
                
            shutil.copy2(normalized_path, backup_path)
            return backup_path
            
        except FileNotFoundError:
            if self.logger:
                self.logger.error(f"File not found: {normalized_path}")
            raise
        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied: {backup_path}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating backup of {normalized_path}: {str(e)}")
            raise
        
    def validate_data_integrity(self, file_path: str) -> bool:
        """
        Validate the integrity of a JSON file by attempting to parse it.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid JSON, False otherwise
        """
        normalized_path = self.normalize_storage_path(file_path)
        
        try:
            if not os.path.exists(normalized_path):
                return False
                
            with open(normalized_path, 'r', encoding='utf-8') as file:
                json.load(file)
                return True
                
        except (json.JSONDecodeError, UnicodeDecodeError):
            if self.logger:
                self.logger.warning(f"File {normalized_path} contains invalid JSON")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error validating {normalized_path}: {str(e)}")
            return False
        
    def ensure_storage_location_exists(self, location_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            location_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False otherwise
            
        Raises:
            PermissionError: If directory can't be created
        """
        normalized_path = self.normalize_storage_path(location_path)
        
        try:
            # Check if directory already exists
            if os.path.exists(normalized_path):
                if os.path.isdir(normalized_path):
                    return True
                else:
                    if self.logger:
                        self.logger.error(f"Path exists but is not a directory: {normalized_path}")
                    return False
                    
            # Create directory and any necessary parent directories
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
        
    def normalize_storage_path(self, path: str) -> str:
        """
        Normalize a file path for the current platform.
        
        Args:
            path: File path to normalize
            
        Returns:
            Normalized file path
        """
        # Convert to absolute path if not already
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # Normalize separators for the current platform
        return os.path.normpath(path)
        
    def get_storage_info(self, path: str) -> Dict[str, Any]:
        """
        Get information about a storage file.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with file information (size, modification date, etc.)
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        normalized_path = self.normalize_storage_path(path)
        
        if not os.path.exists(normalized_path):
            raise FileNotFoundError(f"File not found: {normalized_path}")
            
        stat_info = os.stat(normalized_path)
        
        return {
            "path": normalized_path,
            "size": stat_info.st_size,
            "created": datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "is_dir": os.path.isdir(normalized_path),
            "is_file": os.path.isfile(normalized_path),
        } 