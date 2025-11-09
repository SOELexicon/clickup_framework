"""
Storage Provider Interface

This module defines the abstract base class for storage providers, which handle:
- Data persistence and retrieval
- File operations with cross-platform compatibility
- Data integrity and validation
- Backup and recovery functionality
"""
from typing import Dict, List, Optional, Any, Union, TextIO
from abc import ABC, abstractmethod


class StorageProviderInterface(ABC):
    """
    Abstract base class defining the storage provider interface.
    
    This interface provides methods for:
    - Reading and writing data
    - Handling file operations with platform compatibility
    - Managing file integrity and backup
    """
    
    @abstractmethod
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load data from a storage source.
        
        Args:
            file_path: Path to the data source
            
        Returns:
            Dictionary containing the parsed data
            
        Raises:
            FileNotFoundError: If source doesn't exist
            PermissionError: If source can't be accessed
            ValueError: If data format is invalid
        """
        pass
    
    @abstractmethod
    def save_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to a storage destination.
        
        Args:
            file_path: Path to the destination
            data: Dictionary to serialize and save
            
        Returns:
            True if save succeeded, False otherwise
            
        Raises:
            PermissionError: If destination can't be written
            TypeError: If data can't be serialized
        """
        pass
    
    @abstractmethod
    def backup_data(self, file_path: str) -> str:
        """
        Create a backup of stored data.
        
        Args:
            file_path: Path to the data to backup
            
        Returns:
            Path to the backup
            
        Raises:
            FileNotFoundError: If source doesn't exist
            PermissionError: If backup can't be created
        """
        pass
    
    @abstractmethod
    def validate_data_integrity(self, file_path: str) -> bool:
        """
        Validate the integrity of stored data.
        
        Args:
            file_path: Path to the data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def ensure_storage_location_exists(self, location_path: str) -> bool:
        """
        Ensure a storage location exists, creating it if necessary.
        
        Args:
            location_path: Path to the storage location
            
        Returns:
            True if location exists or was created, False otherwise
            
        Raises:
            PermissionError: If location can't be created
        """
        pass
    
    @abstractmethod
    def normalize_storage_path(self, path: str) -> str:
        """
        Normalize a storage path for the current platform.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        pass

    @abstractmethod
    def get_storage_info(self, path: str) -> Dict[str, Any]:
        """
        Get information about a storage location.
        
        Args:
            path: Path to the storage location
            
        Returns:
            Dictionary with storage information (size, creation date, etc.)
            
        Raises:
            FileNotFoundError: If location doesn't exist
        """
        pass 