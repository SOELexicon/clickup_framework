"""
Cache Manager

This module provides caching functionality for storage operations to improve performance.
It implements various caching strategies including time-based expiration and LRU.

Features:
- In-memory caching of data
- Flexible cache invalidation strategies
- Thread-safe operations
- Configurable size limits
"""
import threading
import time
from typing import Dict, Any, Optional, Callable, List, Tuple, Union
from collections import OrderedDict


class CacheEntry:
    """
    Represents a single entry in the cache with metadata.
    """
    
    def __init__(self, key: str, value: Any, expiry: Optional[float] = None, tags: Optional[List[str]] = None):
        """
        Initialize a cache entry.
        
        Args:
            key: Unique identifier for the entry
            value: The cached value
            expiry: Optional expiration time (timestamp)
            tags: Optional list of tags for grouped invalidation
        """
        self.key = key
        self.value = value
        self.expiry = expiry
        self.tags = tags or []
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 0
        
    def touch(self) -> None:
        """Update the last accessed time and increment access count."""
        self.last_accessed = time.time()
        self.access_count += 1
        
    def is_expired(self) -> bool:
        """Check if the entry is expired."""
        if self.expiry is None:
            return False
        return time.time() > self.expiry
        
    def has_tag(self, tag: str) -> bool:
        """Check if the entry has a specific tag."""
        return tag in self.tags


class CacheManager:
    """
    Manages a cache of values with various invalidation strategies.
    
    Features:
    - Time-based expiration
    - Size limits with LRU eviction
    - Tag-based invalidation
    - Thread-safe operations
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        """
        Initialize the cache manager.
        
        Args:
            max_size: Maximum number of entries in the cache
            default_ttl: Default time-to-live in seconds for entries
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key to retrieve
            default: Default value to return if key is not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            entry = self._cache.get(key)
            
            # Handle cache miss
            if entry is None:
                return default
                
            # Check expiration
            if entry.is_expired():
                self._cache.pop(key, None)
                return default
                
            # Update access info and move to end (for LRU)
            entry.touch()
            self._cache.move_to_end(key)
            
            return entry.value
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            tags: Optional list of tags for grouped invalidation
        """
        with self._lock:
            # Calculate expiry time
            expiry = None
            if ttl is not None:
                expiry = time.time() + ttl
            elif self._default_ttl is not None:
                expiry = time.time() + self._default_ttl
                
            # Create entry
            entry = CacheEntry(key, value, expiry, tags)
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Enforce size limit
            self._enforce_size_limit()
            
    def delete(self, key: str) -> bool:
        """
        Delete an entry from the cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
            
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with a specific tag.
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            Number of entries invalidated
        """
        count = 0
        with self._lock:
            keys_to_delete = [key for key, entry in self._cache.items() if entry.has_tag(tag)]
            for key in keys_to_delete:
                del self._cache[key]
                count += 1
        return count
        
    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all entries with keys starting with a prefix.
        
        Args:
            prefix: Key prefix to invalidate
            
        Returns:
            Number of entries invalidated
        """
        count = 0
        with self._lock:
            keys_to_delete = [key for key in self._cache.keys() if key.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
                count += 1
        return count
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "default_ttl": self._default_ttl,
                "hit_count": sum(entry.access_count for entry in self._cache.values()),
                "oldest_entry_age": time.time() - min(entry.created_at for entry in self._cache.values()) if self._cache else 0,
                "tags": list(set(tag for entry in self._cache.values() for tag in entry.tags))
            }
            
    def _enforce_size_limit(self) -> None:
        """Enforce the maximum cache size by removing oldest entries (LRU)."""
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
            
    def get_or_set(self, key: str, value_func: Callable[[], Any], ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> Any:
        """
        Get a value from cache, or compute and store it if not present.
        
        Args:
            key: Cache key
            value_func: Function to compute the value if not in cache
            ttl: Time-to-live in seconds
            tags: Optional list of tags
            
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is None:
            value = value_func()
            self.set(key, value, ttl, tags)
        return value
        
    def remove_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        count = 0
        with self._lock:
            current_time = time.time()
            keys_to_delete = [
                key for key, entry in self._cache.items()
                if entry.expiry is not None and entry.expiry <= current_time
            ]
            for key in keys_to_delete:
                del self._cache[key]
                count += 1
        return count 