"""
Search Manager Cache Integration

This module provides integration between SavedSearchesManager and SearchCache
to enable automatic caching of search results for improved performance.
"""

import time
from typing import Dict, List, Optional, Any, Union, Tuple

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch
from refactor.storage.cache.search_cache import SearchCache


class SearchManagerWithCache:
    """
    Wrapper class that integrates SavedSearchesManager with SearchCache.
    
    This class extends the functionality of SavedSearchesManager to automatically
    cache search results for improved performance. It provides methods to:
    - Execute searches with automatic caching
    - Manage cache configuration
    - Get cache statistics
    """
    
    def __init__(self, saved_searches_manager: SavedSearchesManager, 
                 storage_path: Optional[str] = None, 
                 max_cache_size: int = 100,
                 default_expiration: int = 3600):
        """
        Initialize the integrated search manager.
        
        Args:
            saved_searches_manager: Existing SavedSearchesManager instance
            storage_path: Optional directory for storing cache (defaults to same as searches)
            max_cache_size: Maximum number of entries in the cache
            default_expiration: Default expiration time in seconds (1 hour)
        """
        self.search_manager = saved_searches_manager
        
        # Use the same storage path as the search manager if not specified
        if storage_path is None:
            # Extract directory from search manager's storage file
            storage_path = '/'.join(self.search_manager.storage_file.split('/')[:-1])
        
        # Initialize the cache manager
        self.cache_manager = SearchCache(
            storage_path=storage_path,
            max_size=max_cache_size,
            default_expiration=default_expiration
        )
    
    def execute_search(self, query: str, saved_search_name: Optional[str] = None, 
                      result_processor=None, skip_cache: bool = False,
                      cache_expiration: Optional[int] = None) -> Tuple[Any, float]:
        """
        Execute a search query with caching.
        
        Args:
            query: The search query to execute
            saved_search_name: Optional name of a saved search if from one
            result_processor: Callable that processes and returns results
            skip_cache: If True, bypasses cache and forces a fresh query
            cache_expiration: Optional custom expiration time in seconds
            
        Returns:
            Tuple of (search results, execution time in ms)
        """
        # Get saved search if name provided
        search = None
        if saved_search_name:
            search = self.search_manager.get_search(saved_search_name)
            if search:
                # Mark the search as used
                search.mark_used()
                # Update the query from the saved search
                query = search.query
        
        # Check cache first unless skip_cache is True
        if not skip_cache:
            cached_result = self.cache_manager.get(query)
            if cached_result:
                results, original_execution_time = cached_result
                # Still add to history even if from cache
                self._add_to_history(query, saved_search_name, len(results) if hasattr(results, "__len__") else 0)
                return results, original_execution_time
        
        # Cache miss or skip_cache, execute the search
        start_time = time.time()
        
        # Execute the search
        if result_processor:
            results = result_processor(query)
        else:
            # Dummy result (meant to be overridden by caller)
            results = {"query": query, "dummy": True}
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Get result count (if results support it)
        result_count = 0
        if hasattr(results, "__len__"):
            result_count = len(results)
        
        # Add to history
        self._add_to_history(query, saved_search_name, result_count)
        
        # Cache the results unless skip_cache is True
        if not skip_cache:
            self.cache_manager.put(
                query=query,
                results=results,
                execution_time_ms=execution_time_ms,
                expiration_seconds=cache_expiration
            )
        
        return results, execution_time_ms
    
    def _add_to_history(self, query: str, saved_search_name: Optional[str],
                      result_count: int) -> None:
        """
        Add a search to the history.
        
        Args:
            query: The search query string
            saved_search_name: Optional name of the saved search
            result_count: Number of results returned
        """
        self.search_manager.add_to_history(
            query=query,
            saved_search_name=saved_search_name,
            result_count=result_count
        )
    
    def execute_template(self, template_name: str, variables: Dict[str, str], 
                        result_processor=None, skip_cache: bool = False,
                        cache_expiration: Optional[int] = None) -> Tuple[Any, float]:
        """
        Execute a search template with caching.
        
        Args:
            template_name: Name of the template to execute
            variables: Dictionary of variable values
            result_processor: Callable that processes and returns results
            skip_cache: If True, bypasses cache and forces a fresh query
            cache_expiration: Optional custom expiration time in seconds
            
        Returns:
            Tuple of (search results, execution time in ms)
        """
        # Get the resulting query from the template
        query, used_variables = self.search_manager.execute_search_template(
            template_name, variables
        )
        
        # Execute with the generated query
        return self.execute_search(
            query=query,
            saved_search_name=template_name,
            result_processor=result_processor,
            skip_cache=skip_cache,
            cache_expiration=cache_expiration
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary containing cache statistics
        """
        return self.cache_manager.get_stats()
    
    def clear_cache(self) -> None:
        """Clear all entries from the cache."""
        self.cache_manager.invalidate_all()
    
    def invalidate_cache_entry(self, query: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            query: The query string to invalidate
            
        Returns:
            True if an entry was invalidated, False otherwise
        """
        return self.cache_manager.invalidate(query)
    
    def invalidate_search_cache(self, search_name: str) -> bool:
        """
        Invalidate the cache for a specific saved search.
        
        Args:
            search_name: Name of the saved search
            
        Returns:
            True if an entry was invalidated, False otherwise
        """
        try:
            search = self.search_manager.get_search(search_name)
            return self.cache_manager.invalidate(search.query)
        except KeyError:
            return False
    
    def configure_cache(self, max_size: Optional[int] = None,
                      default_expiration: Optional[int] = None) -> None:
        """
        Update cache configuration.
        
        Args:
            max_size: Maximum number of entries in the cache
            default_expiration: Default expiration time in seconds
        """
        self.cache_manager.configure(
            max_size=max_size,
            default_expiration=default_expiration
        )
    
    # Delegate all other methods to the underlying SavedSearchesManager
    
    def save_search(self, name: str, query: str, **kwargs) -> SavedSearch:
        """
        Save a search query (delegated to SavedSearchesManager).
        
        Args:
            name: Unique name for the saved search
            query: The search query string
            **kwargs: Additional arguments passed to SavedSearchesManager.save_search
            
        Returns:
            The saved search object
        """
        search = self.search_manager.save_search(name, query, **kwargs)
        return search
    
    def update_search(self, name: str, **kwargs) -> SavedSearch:
        """
        Update an existing saved search (delegated to SavedSearchesManager).
        
        Args:
            name: Name of the search to update
            **kwargs: Arguments passed to SavedSearchesManager.update_search
            
        Returns:
            The updated saved search
        """
        # If the query is being updated, invalidate the old query in the cache
        try:
            if "query" in kwargs:
                old_search = self.search_manager.get_search(name)
                self.cache_manager.invalidate(old_search.query)
        except KeyError:
            pass
            
        return self.search_manager.update_search(name, **kwargs)
    
    def get_search(self, name: str) -> SavedSearch:
        """
        Get a saved search by name (delegated to SavedSearchesManager).
        
        Args:
            name: Name of the saved search
            
        Returns:
            The saved search object
        """
        return self.search_manager.get_search(name)
    
    def list_searches(self, **kwargs) -> List[SavedSearch]:
        """
        List saved searches (delegated to SavedSearchesManager).
        
        Args:
            **kwargs: Arguments passed to SavedSearchesManager.list_searches
            
        Returns:
            List of saved search objects
        """
        return self.search_manager.list_searches(**kwargs)
    
    def delete_search(self, name: str) -> bool:
        """
        Delete a saved search (delegated to SavedSearchesManager).
        
        Args:
            name: Name of the saved search
            
        Returns:
            True if the search was deleted, False if not found
        """
        # Try to invalidate the cache for this search before deleting
        try:
            search = self.search_manager.get_search(name)
            self.cache_manager.invalidate(search.query)
        except KeyError:
            pass
            
        return self.search_manager.delete_search(name)
    
    def get_categories(self) -> List[str]:
        """
        Get all unique categories (delegated to SavedSearchesManager).
        
        Returns:
            List of category names
        """
        return self.search_manager.get_categories()
    
    def get_tags(self) -> List[str]:
        """
        Get all unique tags (delegated to SavedSearchesManager).
        
        Returns:
            List of tag names
        """
        return self.search_manager.get_tags()
    
    def toggle_favorite(self, name: str) -> bool:
        """
        Toggle favorite status (delegated to SavedSearchesManager).
        
        Args:
            name: Name of the search
            
        Returns:
            New favorite status
        """
        return self.search_manager.toggle_favorite(name)
    
    def list_favorites(self, **kwargs) -> List[SavedSearch]:
        """
        List favorites (delegated to SavedSearchesManager).
        
        Args:
            **kwargs: Arguments passed to SavedSearchesManager.list_favorites
            
        Returns:
            List of favorite searches
        """
        return self.search_manager.list_favorites(**kwargs)
    
    def get_history(self, **kwargs) -> List[Any]:
        """
        Get search history (delegated to SavedSearchesManager).
        
        Args:
            **kwargs: Arguments passed to SavedSearchesManager.get_history
            
        Returns:
            List of history entries
        """
        return self.search_manager.get_history(**kwargs)
    
    def clear_history(self) -> int:
        """
        Clear search history (delegated to SavedSearchesManager).
        
        Returns:
            Number of entries cleared
        """
        return self.search_manager.clear_history()
    
    # Batch operations are also delegated
    
    def batch_delete(self, names: List[str]) -> Tuple[int, List[str]]:
        """Delegate to SavedSearchesManager.batch_delete."""
        # Try to invalidate cache for each search before deletion
        for name in names:
            try:
                search = self.search_manager.get_search(name)
                self.cache_manager.invalidate(search.query)
            except KeyError:
                pass
                
        return self.search_manager.batch_delete(names)
    
    def batch_categorize(self, names: List[str], category: str) -> Tuple[int, List[str]]:
        """Delegate to SavedSearchesManager.batch_categorize."""
        return self.search_manager.batch_categorize(names, category)
    
    def batch_add_tags(self, names: List[str], tags: List[str]) -> Tuple[int, List[str]]:
        """Delegate to SavedSearchesManager.batch_add_tags."""
        return self.search_manager.batch_add_tags(names, tags)
    
    def batch_remove_tags(self, names: List[str], tags: List[str]) -> Tuple[int, List[str]]:
        """Delegate to SavedSearchesManager.batch_remove_tags."""
        return self.search_manager.batch_remove_tags(names, tags)
    
    def batch_toggle_favorite(self, names: List[str], favorite_status: Optional[bool] = None) -> Tuple[int, List[str]]:
        """Delegate to SavedSearchesManager.batch_toggle_favorite."""
        return self.search_manager.batch_toggle_favorite(names, favorite_status)
    
    def add_to_favorites(self, name_or_names: Union[str, List[str]]) -> Union[bool, Tuple[int, List[str]]]:
        """Delegate to SavedSearchesManager.add_to_favorites."""
        return self.search_manager.add_to_favorites(name_or_names)
    
    def remove_from_favorites(self, name_or_names: Union[str, List[str]]) -> Union[bool, Tuple[int, List[str]]]:
        """Delegate to SavedSearchesManager.remove_from_favorites."""
        return self.search_manager.remove_from_favorites(name_or_names) 