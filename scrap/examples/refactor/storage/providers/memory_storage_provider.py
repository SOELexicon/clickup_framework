"""
Memory Storage Provider

This module implements an in-memory storage provider for:
- Testing without file system access
- Temporary data storage
- Performance optimization for frequently accessed data

This provider stores all data in memory rather than on disk.
"""
from typing import Dict, List, Optional, Any, Union
import copy
import datetime
import os
from .storage_provider_interface import StorageProviderInterface


class MemoryStorageProvider(StorageProviderInterface):
    """
    Implementation of StorageProviderInterface for in-memory storage.
    
    This class provides:
    - In-memory data storage
    - Path simulation
    - Backup functionality
    - Useful for testing and caching
    """
    
    def __init__(self, logger=None):
        """
        Initialize the memory storage provider.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.logger = logger
        self.storage = {}  # Dictionary to store data
        self.backups = {}  # Dictionary to store backups
        self.metadata = {}  # Dictionary to store metadata
        
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load data from memory.
        
        Args:
            file_path: Path identifier for the data
            
        Returns:
            Dictionary containing the data
            
        Raises:
            FileNotFoundError: If data doesn't exist for the path
        """
        normalized_path = self.normalize_storage_path(file_path)
        
        if normalized_path not in self.storage:
            if self.logger:
                self.logger.error(f"Data not found: {normalized_path}")
            raise FileNotFoundError(f"Data not found: {normalized_path}")
            
        # Return a deep copy to prevent unintended modifications
        return copy.deepcopy(self.storage[normalized_path])
        
    def save_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to memory.
        
        Args:
            file_path: Path identifier for the data
            data: Dictionary to save
            
        Returns:
            True if save succeeded, False otherwise
        """
        normalized_path = self.normalize_storage_path(file_path)
        
        try:
            # Create parent directory simulation if needed
            self._ensure_parent_exists(normalized_path)
            
            # Backup existing data if it exists
            if normalized_path in self.storage:
                self.backup_data(normalized_path)
                
            # Store a deep copy to prevent unintended modifications
            self.storage[normalized_path] = copy.deepcopy(data)
            
            # Update metadata
            self.metadata[normalized_path] = {
                "size": len(str(data)),
                "created": datetime.datetime.now().isoformat(),
                "modified": datetime.datetime.now().isoformat(),
                "accessed": datetime.datetime.now().isoformat(),
                "is_dir": False,
                "is_file": True,
            }
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving data to {normalized_path}: {str(e)}")
            return False
            
    def backup_data(self, file_path: str) -> str:
        """
        Create a backup of data in memory.
        
        Args:
            file_path: Path identifier for the data
            
        Returns:
            Path to the backup
            
        Raises:
            FileNotFoundError: If data doesn't exist for the path
        """
        normalized_path = self.normalize_storage_path(file_path)
        
        if normalized_path not in self.storage:
            if self.logger:
                self.logger.error(f"Data not found: {normalized_path}")
            raise FileNotFoundError(f"Data not found: {normalized_path}")
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{normalized_path}.{timestamp}.bak"
        
        # Store a deep copy to prevent unintended modifications
        self.backups[backup_path] = copy.deepcopy(self.storage[normalized_path])
        
        # Update metadata for the backup
        self.metadata[backup_path] = copy.deepcopy(self.metadata.get(normalized_path, {}))
        self.metadata[backup_path]["is_backup"] = True
        
        return backup_path
        
    def validate_data_integrity(self, file_path: str) -> bool:
        """
        Validate the integrity of data in memory.
        
        Args:
            file_path: Path identifier for the data
            
        Returns:
            True if data exists, False otherwise
        """
        normalized_path = self.normalize_storage_path(file_path)
        return normalized_path in self.storage
        
    def ensure_storage_location_exists(self, location_path: str) -> bool:
        """
        Ensure a directory simulation exists in memory.
        
        Args:
            location_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        normalized_path = self.normalize_storage_path(location_path)
        
        # Check if path already exists as file
        if normalized_path in self.storage:
            return False
            
        # Create directory metadata
        self.metadata[normalized_path] = {
            "size": 0,
            "created": datetime.datetime.now().isoformat(),
            "modified": datetime.datetime.now().isoformat(),
            "accessed": datetime.datetime.now().isoformat(),
            "is_dir": True,
            "is_file": False,
        }
        
        return True
        
    def normalize_storage_path(self, path: str) -> str:
        """
        Normalize a path for consistent key usage in dictionaries.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Convert to forward slashes for consistency
        return path.replace('\\', '/')
        
    def get_storage_info(self, path: str) -> Dict[str, Any]:
        """
        Get information about stored data.
        
        Args:
            path: Path identifier for the data
            
        Returns:
            Dictionary with data information
            
        Raises:
            FileNotFoundError: If data or directory doesn't exist
        """
        normalized_path = self.normalize_storage_path(path)
        
        # Check if path exists as file or directory
        if normalized_path not in self.storage and normalized_path not in self.metadata:
            raise FileNotFoundError(f"Path not found: {normalized_path}")
            
        # Return metadata if it exists, or generate default metadata
        if normalized_path in self.metadata:
            return copy.deepcopy(self.metadata[normalized_path])
        
        # Default metadata for a path that exists but has no explicit metadata
        return {
            "path": normalized_path,
            "size": len(str(self.storage.get(normalized_path, ''))),
            "created": datetime.datetime.now().isoformat(),
            "modified": datetime.datetime.now().isoformat(),
            "accessed": datetime.datetime.now().isoformat(),
            "is_dir": False,
            "is_file": True,
        }
    
    def _ensure_parent_exists(self, path: str) -> None:
        """
        Ensure parent directories exist in the virtual file system.
        
        Args:
            path: Path to ensure parents exist for
        """
        parent_path = os.path.dirname(path.replace('/', os.sep))
        if parent_path and parent_path != path:
            normalized_parent = self.normalize_storage_path(parent_path)
            
            # Create parent directory metadata if it doesn't exist
            if normalized_parent not in self.metadata:
                self.ensure_storage_location_exists(normalized_parent)
                
                # Recursively ensure grandparent exists
                self._ensure_parent_exists(normalized_parent) 