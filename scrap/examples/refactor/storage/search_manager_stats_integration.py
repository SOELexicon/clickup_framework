"""
Search Manager Statistics Integration

This module provides integration between SavedSearchesManager and SearchStatsManager
to enable automatic tracking of search statistics when searches are executed.
"""

import time
from typing import Dict, List, Optional, Any, Union, Tuple

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch
from refactor.storage.search_stats import SearchStatsManager


class SearchManagerWithStats:
    """
    Wrapper class that integrates SavedSearchesManager with SearchStatsManager.
    
    This class extends the functionality of SavedSearchesManager to automatically
    track search statistics when searches are executed. It provides methods to:
    - Execute searches with performance tracking
    - Access search statistics and reports
    - View optimization suggestions
    """
    
    def __init__(self, saved_searches_manager: SavedSearchesManager, storage_path: Optional[str] = None):
        """
        Initialize the integrated search manager.
        
        Args:
            saved_searches_manager: Existing SavedSearchesManager instance
            storage_path: Optional directory for storing statistics (defaults to same as searches)
        """
        self.search_manager = saved_searches_manager
        
        # Use the same storage path as the search manager if not specified
        if storage_path is None:
            # Extract directory from search manager's storage file
            storage_path = '/'.join(self.search_manager.storage_file.split('/')[:-1])
        
        # Initialize the stats manager
        self.stats_manager = SearchStatsManager(storage_path)
    
    def execute_search(self, query: str, saved_search_name: Optional[str] = None, 
                      result_processor=None) -> Tuple[Any, float]:
        """
        Execute a search query with performance tracking.
        
        Args:
            query: The search query to execute
            saved_search_name: Optional name of a saved search if from one
            result_processor: Optional callable that processes and returns results
            
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
        
        # Start timing
        start_time = time.time()
        
        # Execute the search (using provided result processor or dummy)
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
        self.search_manager.add_to_history(
            query=query,
            saved_search_name=saved_search_name,
            result_count=result_count
        )
        
        # Track statistics
        if search:
            self.stats_manager.record_search(
                search_name=search.name,
                query=query,
                execution_time_ms=execution_time_ms,
                result_count=result_count,
                is_favorite=search.is_favorite,
                category=search.category,
                tags=search.tags
            )
        else:
            # For ad-hoc queries
            search_name = saved_search_name or f"adhoc_{int(start_time)}"
            self.stats_manager.record_search(
                search_name=search_name,
                query=query,
                execution_time_ms=execution_time_ms,
                result_count=result_count
            )
        
        return results, execution_time_ms
    
    def execute_template(self, template_name: str, variables: Dict[str, str], 
                        result_processor=None) -> Tuple[Any, float]:
        """
        Execute a search template with variables and performance tracking.
        
        Args:
            template_name: Name of the template to execute
            variables: Dictionary of variable values
            result_processor: Optional callable that processes and returns results
            
        Returns:
            Tuple of (search results, execution time in ms)
        """
        # Get the resulting query from the template
        query, used_variables = self.search_manager.execute_search_template(
            template_name, variables
        )
        
        # Execute with the generated query
        results, execution_time_ms = self.execute_search(
            query=query,
            saved_search_name=template_name,
            result_processor=result_processor
        )
        
        return results, execution_time_ms
    
    def get_stats_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive statistics report.
        
        Returns:
            Dictionary containing statistics report data
        """
        return self.stats_manager.generate_report()
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get suggestions for search optimizations.
        
        Returns:
            List of suggestion dictionaries
        """
        return self.stats_manager.get_optimization_suggestions()
    
    def clear_stats(self) -> None:
        """Reset all statistics to defaults."""
        self.stats_manager.clear_stats()
    
    def get_most_used_searches(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most frequently used searches.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of (search_name, count) tuples, sorted by count descending
        """
        return self.stats_manager.get_most_used_searches(limit)
    
    def get_slowest_searches(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get the searches with the highest average execution time.
        
        Args:
            limit: Maximum number of searches to return
            
        Returns:
            List of (search_name, avg_time_ms) tuples, sorted by time descending
        """
        return self.stats_manager.get_slowest_searches(limit)
    
    def get_search_performance_stats(self, search_name: str) -> Dict[str, Union[float, int]]:
        """
        Get detailed performance statistics for a specific search.
        
        Args:
            search_name: Name of the search
            
        Returns:
            Dictionary with execution time and result count statistics
        """
        time_stats = self.stats_manager.get_execution_time_stats(search_name)
        count_stats = self.stats_manager.get_result_count_stats(search_name)
        
        # Merge the dictionaries
        combined_stats = {**time_stats, **count_stats}
        
        # Add formatted fields for easier reading
        if 'avg' in time_stats:
            combined_stats['avg_formatted'] = f"{time_stats['avg']:.2f}ms"
        
        return combined_stats 