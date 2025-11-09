"""
Search Caching System

This module provides caching functionality for saved searches to improve performance
by storing the results of frequently used searches.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import OrderedDict


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    
    This class provides an LRU cache with a fixed maximum size, automatically
    evicting the least recently used items when the cache becomes full.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize the LRU cache.
        
        Args:
            max_size: Maximum number of items to store in the cache
        """
        self.max_size = max_size
        self.cache = OrderedDict()  # Using OrderedDict for LRU functionality
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from the cache and mark it as recently used.
        
        Args:
            key: Cache key to look up
            
        Returns:
            Cached value or None if not found
        """
        if key not in self.cache:
            return None
            
        # Move the item to the end (most recently used)
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
        
    def put(self, key: str, value: Any) -> None:
        """
        Add or update an item in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # If key exists, remove it first to update its position
        if key in self.cache:
            self.cache.pop(key)
            
        # Add the new item
        self.cache[key] = value
        
        # Check if we need to evict the least recently used item
        if len(self.cache) > self.max_size:
            # Remove the first item (least recently used)
            self.cache.popitem(last=False)
            
    def remove(self, key: str) -> bool:
        """
        Remove an item from the cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if the item was removed, False if not found
        """
        if key in self.cache:
            self.cache.pop(key)
            return True
        return False
        
    def clear(self) -> None:
        """Clear all items from the cache."""
        self.cache.clear()
        
    def get_keys(self) -> List[str]:
        """
        Get all keys in the cache, ordered from least to most recently used.
        
        Returns:
            List of keys
        """
        return list(self.cache.keys())
        
    def size(self) -> int:
        """
        Get the current number of items in the cache.
        
        Returns:
            Number of items in the cache
        """
        return len(self.cache)


class SearchCacheEntry:
    """
    Represents an entry in the search cache.
    
    This class stores the cached search results along with metadata such as
    the creation time, expiration time, and usage statistics.
    """
    
    def __init__(self, query: str, results: Any, 
                 execution_time_ms: float,
                 expiration_seconds: int = 3600):  # Default: 1 hour
        """
        Initialize a cache entry.
        
        Args:
            query: The search query string
            results: The search results to cache
            execution_time_ms: Original execution time in milliseconds
            expiration_seconds: Number of seconds until the entry expires
        """
        self.query = query
        self.results = results
        self.execution_time_ms = execution_time_ms
        self.created_at = time.time()
        self.expires_at = self.created_at + expiration_seconds
        self.hit_count = 0
        
    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expires_at
        
    def mark_hit(self) -> None:
        """Increment the hit counter for this cache entry."""
        self.hit_count += 1
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the cache entry
        """
        return {
            "query": self.query,
            "results": self.results,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "hit_count": self.hit_count
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchCacheEntry':
        """
        Create a SearchCacheEntry from a dictionary.
        
        Args:
            data: Dictionary containing cache entry data
            
        Returns:
            New SearchCacheEntry instance
        """
        entry = cls(
            query=data["query"],
            results=data["results"],
            execution_time_ms=data["execution_time_ms"]
        )
        entry.created_at = data.get("created_at", time.time())
        entry.expires_at = data.get("expires_at", entry.created_at + 3600)
        entry.hit_count = data.get("hit_count", 0)
        return entry


class SearchCache:
    """
    Cache manager for search results.
    
    This class manages caching of search results using an LRU strategy with
    configurable cache size and expiration. It provides methods to:
    - Get cached results for a query
    - Cache new search results
    - Invalidate cache entries
    - Monitor cache statistics
    """
    
    def __init__(self, storage_path: str, max_size: int = 100, 
                default_expiration: int = 3600):
        """
        Initialize the search cache.
        
        Args:
            storage_path: Directory where cache data will be stored
            max_size: Maximum number of entries in the cache
            default_expiration: Default expiration time in seconds (1 hour)
        """
        self.storage_path = storage_path
        self.cache_file = os.path.join(storage_path, "search_cache.json")
        self.max_size = max_size
        self.default_expiration = default_expiration
        
        # Initialize the LRU cache
        self.cache = LRUCache(max_size)
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "inserts": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # Load any existing cache data
        self._load_cache()
        
    def _load_cache(self) -> None:
        """
        Load cache data from the cache file.
        
        If the file doesn't exist or can't be read, it starts with an empty cache.
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                
                # Load cache entries
                for key, entry_data in data.get("entries", {}).items():
                    entry = SearchCacheEntry.from_dict(entry_data)
                    
                    # Skip expired entries
                    if not entry.is_expired():
                        self.cache.put(key, entry)
                    else:
                        self.stats["expirations"] += 1
                
                # Load statistics
                if "stats" in data:
                    self.stats.update(data["stats"])
                    
            except (json.JSONDecodeError, IOError):
                # Start with an empty cache if there's an error
                pass
                
    def _save_cache(self) -> None:
        """Save the current cache to the cache file."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Convert cache entries to dictionaries
        entries = {}
        for key in self.cache.get_keys():
            entry = self.cache.get(key)
            entries[key] = entry.to_dict()
            
        # Prepare data to save
        data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "entries": entries
        }
        
        # Save to file
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
            
    def get(self, query: str) -> Optional[Tuple[Any, float]]:
        """
        Get cached results for a query.
        
        Args:
            query: The search query string
            
        Returns:
            Tuple of (results, original_execution_time_ms) if cache hit,
            None if cache miss or entry expired
        """
        entry = self.cache.get(query)
        
        if entry is None:
            # Cache miss
            self.stats["misses"] += 1
            return None
            
        if entry.is_expired():
            # Entry expired, remove it
            self.cache.remove(query)
            self.stats["expirations"] += 1
            return None
            
        # Cache hit
        entry.mark_hit()
        self.stats["hits"] += 1
        return (entry.results, entry.execution_time_ms)
        
    def put(self, query: str, results: Any, execution_time_ms: float,
           expiration_seconds: Optional[int] = None) -> None:
        """
        Cache results for a query.
        
        Args:
            query: The search query string
            results: The search results to cache
            execution_time_ms: Original execution time in milliseconds
            expiration_seconds: Optional custom expiration time in seconds
        """
        # Use default expiration if not specified
        if expiration_seconds is None:
            expiration_seconds = self.default_expiration
            
        # Create cache entry
        entry = SearchCacheEntry(
            query=query,
            results=results,
            execution_time_ms=execution_time_ms,
            expiration_seconds=expiration_seconds
        )
        
        # Check if we're replacing an existing entry
        old_size = self.cache.size()
        
        # Add to cache
        self.cache.put(query, entry)
        self.stats["inserts"] += 1
        
        # Check if an item was evicted
        if old_size == self.max_size and old_size == self.cache.size():
            self.stats["evictions"] += 1
            
        # Save cache to disk
        self._save_cache()
        
    def invalidate(self, query: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            query: The search query string to invalidate
            
        Returns:
            True if an entry was removed, False otherwise
        """
        if self.cache.remove(query):
            self._save_cache()
            return True
        return False
        
    def invalidate_all(self) -> None:
        """Invalidate all cache entries."""
        self.cache.clear()
        self._save_cache()
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        # Calculate hit rate
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = 0
        if total_requests > 0:
            hit_rate = self.stats["hits"] / total_requests
            
        return {
            "size": self.cache.size(),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "inserts": self.stats["inserts"],
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"]
        }
        
    def configure(self, max_size: Optional[int] = None, 
                default_expiration: Optional[int] = None) -> None:
        """
        Update cache configuration.
        
        Args:
            max_size: New maximum cache size (if None, keeps current)
            default_expiration: New default expiration time in seconds (if None, keeps current)
        """
        if max_size is not None:
            # If reducing size, we need to resize the cache
            if max_size < self.max_size and self.cache.size() > max_size:
                # Create a new cache with the smaller size
                new_cache = LRUCache(max_size)
                
                # Keep only the most recently used entries
                for key in reversed(self.cache.get_keys()[-max_size:]):
                    new_cache.put(key, self.cache.get(key))
                    
                self.cache = new_cache
                self.stats["evictions"] += (self.max_size - max_size)
            
            self.max_size = max_size
            
        if default_expiration is not None:
            self.default_expiration = default_expiration
            
        # Save updated configuration
        self._save_cache() 