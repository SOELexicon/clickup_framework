"""
Search Caching Package

This package provides functionality for caching search results to improve performance.
It includes implementations of:
- LRU caching strategy
- Search cache management
- Integration with the SavedSearchesManager
"""

from refactor.storage.cache.search_cache import SearchCache, LRUCache, SearchCacheEntry
from refactor.storage.cache.search_manager_cache_integration import SearchManagerWithCache

__all__ = [
    'SearchCache',
    'LRUCache',
    'SearchCacheEntry',
    'SearchManagerWithCache'
]
