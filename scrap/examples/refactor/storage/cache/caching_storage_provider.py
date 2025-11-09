"""
Caching Storage Provider

This module implements a storage provider that adds caching to another provider.
It uses the cache manager to store frequently accessed data in memory for performance.

Features:
- Transparent caching of storage operations
- Configurable cache behavior
- Automatic cache invalidation
"""
from typing import Dict, List, Optional, Any, Union, Set
import os
from ..providers.storage_provider_interface import StorageProviderInterface
from .cache_manager import CacheManager


class CachingStorageProvider(StorageProviderInterface):
    """
    Implementation of StorageProviderInterface that adds caching to another provider.
    
    This provider delegates operations to the underlying provider while caching results.
    """
    
    def __init__(self, 
                 provider: StorageProviderInterface, 
                 cache_manager: Optional[CacheManager] = None,
                 logger=None):
        """
        Initialize the caching storage provider.
        
        Args:
            provider: The underlying storage provider to cache
            cache_manager: Optional cache manager (creates one if not provided)
            logger: Optional logger for logging operations
        """
        self.provider = provider
        self.cache_manager = cache_manager or CacheManager()
        self.logger = logger
        self._modified_paths: Set[str] = set()
        
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load data from storage with caching.
        
        Args:
            file_path: Path to the data source
            
        Returns:
            Dictionary containing the parsed data
            
        Raises:
            FileNotFoundError: If source doesn't exist
            PermissionError: If source can't be accessed
            ValueError: If data format is invalid
        """
        normalized_path = self.normalize_storage_path(file_path)
        cache_key = f"data:{normalized_path}"
        
        # Skip cache if file was modified since last cache
        if normalized_path in self._modified_paths:
            if self.logger:
                self.logger.debug(f"Cache bypass for modified file: {normalized_path}")
            self._modified_paths.remove(normalized_path)
            data = self.provider.load_data(file_path)
            self.cache_manager.set(cache_key, data)
            return data
        
        # Try to get from cache
        return self.cache_manager.get_or_set(
            cache_key,
            lambda: self.provider.load_data(file_path),
            tags=[f"file:{normalized_path}", "data"]
        )
    
    def save_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to storage and update cache.
        
        Args:
            file_path: Path to the destination
            data: Dictionary to serialize and save
            
        Returns:
            True if save succeeded, False otherwise
            
        Raises:
            PermissionError: If destination can't be written
            TypeError: If data can't be serialized
        """
        normalized_path = self.normalize_storage_path(file_path)
        
        # Save using underlying provider
        result = self.provider.save_data(file_path, data)
        
        if result:
            # Update cache
            cache_key = f"data:{normalized_path}"
            self.cache_manager.set(cache_key, data, tags=[f"file:{normalized_path}", "data"])
            
            # Mark as modified
            self._modified_paths.add(normalized_path)
            
            # Invalidate any related caches
            self.cache_manager.invalidate_by_tag(f"file:{normalized_path}")
            
        return result
    
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
        # No caching for backups, delegate directly
        return self.provider.backup_data(file_path)
    
    def validate_data_integrity(self, file_path: str) -> bool:
        """
        Validate the integrity of stored data.
        
        Args:
            file_path: Path to the data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        normalized_path = self.normalize_storage_path(file_path)
        cache_key = f"validate:{normalized_path}"
        
        # Cache validation results for a short time
        return self.cache_manager.get_or_set(
            cache_key,
            lambda: self.provider.validate_data_integrity(file_path),
            ttl=60,  # Cache for 1 minute
            tags=[f"file:{normalized_path}", "validate"]
        )
    
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
        # No caching for directory creation, delegate directly
        return self.provider.ensure_storage_location_exists(location_path)
    
    def normalize_storage_path(self, path: str) -> str:
        """
        Normalize a storage path for the current platform.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Use underlying provider for normalization
        return self.provider.normalize_storage_path(path)
    
    def get_storage_info(self, path: str) -> Dict[str, Any]:
        """
        Get information about a storage location with caching.
        
        Args:
            path: Path to the storage location
            
        Returns:
            Dictionary with storage information
            
        Raises:
            FileNotFoundError: If location doesn't exist
        """
        normalized_path = self.normalize_storage_path(path)
        cache_key = f"info:{normalized_path}"
        
        # Skip cache if file was modified
        if normalized_path in self._modified_paths:
            if self.logger:
                self.logger.debug(f"Cache bypass for modified file info: {normalized_path}")
            info = self.provider.get_storage_info(path)
            self.cache_manager.set(cache_key, info, ttl=30, tags=[f"file:{normalized_path}", "info"])
            return info
        
        # Cache file info for a short time
        return self.cache_manager.get_or_set(
            cache_key,
            lambda: self.provider.get_storage_info(path),
            ttl=30,  # Cache for 30 seconds
            tags=[f"file:{normalized_path}", "info"]
        )
    
    def invalidate_cache(self, file_path: Optional[str] = None) -> int:
        """
        Invalidate cache entries for a file or all entries.
        
        Args:
            file_path: Optional path to invalidate (invalidates all if None)
            
        Returns:
            Number of cache entries invalidated
        """
        if file_path is None:
            # Invalidate all data cache entries
            count = self.cache_manager.invalidate_by_tag("data")
            if self.logger:
                self.logger.debug(f"Invalidated {count} cache entries")
            return count
        
        # Invalidate specific file
        normalized_path = self.normalize_storage_path(file_path)
        count = self.cache_manager.invalidate_by_tag(f"file:{normalized_path}")
        
        if self.logger:
            self.logger.debug(f"Invalidated {count} cache entries for {normalized_path}")
            
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache_manager.get_stats() 