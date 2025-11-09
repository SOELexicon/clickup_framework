"""
Storage Module

This module provides data persistence operations for the ClickUp JSON Manager.
It handles file I/O, data serialization, and cross-platform compatibility.

Features:
- Cross-platform file handling
- Data serialization and deserialization
- Caching for performance optimization
- Backup and recovery
"""
# Storage provider interfaces
from .providers.storage_provider_interface import StorageProviderInterface

# Storage provider implementations
from .providers.json_storage_provider import JsonStorageProvider
from .providers.memory_storage_provider import MemoryStorageProvider

# Platform abstraction
from .providers.platform_abstraction import (
    PlatformInfo,
    PlatformHandler,
    WindowsPlatformHandler,
    UnixPlatformHandler,
    LinuxPlatformHandler,
    MacOSPlatformHandler,
    PlatformAbstraction
)

# Serialization components
from .serialization.serializer_interface import SerializerInterface, EntitySerializerInterface
from .serialization.json_serializer import JsonSerializer
from .serialization.entity_serializer import EntitySerializer

# Saved searches components
from .saved_searches import SavedSearch, SavedSearchesManager, SearchHistoryEntry

# Full-text search components
from .full_text_search import FullTextSearchIndex, FullTextSearchManager

# Caching components
from .cache.cache_manager import CacheManager, CacheEntry
from .cache.caching_storage_provider import CachingStorageProvider

# Factory functions for easy instantiation
def create_json_storage_provider(logger=None):
    """
    Create a JSON storage provider with platform-specific optimizations.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        JsonStorageProvider instance
    """
    return JsonStorageProvider(logger)
    
def create_memory_storage_provider(logger=None):
    """
    Create an in-memory storage provider for testing or caching.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        MemoryStorageProvider instance
    """
    return MemoryStorageProvider(logger)
    
def create_cached_storage_provider(provider=None, cache_size=1000, default_ttl=300, logger=None):
    """
    Create a cached storage provider that wraps another provider.
    
    Args:
        provider: Underlying storage provider (defaults to JsonStorageProvider)
        cache_size: Maximum number of entries in the cache
        default_ttl: Default time-to-live in seconds
        logger: Optional logger instance
        
    Returns:
        CachingStorageProvider instance
    """
    if provider is None:
        provider = create_json_storage_provider(logger)
        
    cache_manager = CacheManager(max_size=cache_size, default_ttl=default_ttl)
    return CachingStorageProvider(provider, cache_manager, logger)

# Default provider instance
default_provider = create_json_storage_provider()
