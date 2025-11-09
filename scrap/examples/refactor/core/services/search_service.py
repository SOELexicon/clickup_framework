"""
Search Service Module - Provides service layer for task searching and filtering.

This module implements the SearchService class which handles all search-related
operations, including complex queries, text search, and result filtering.
"""

import logging
import threading
import re
import time
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Tuple, Callable, Union
from datetime import datetime, timedelta

from ..entities.task_entity import TaskEntity, TaskStatus, TaskPriority
from ..repositories.repository_interface import ITaskRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class SearchServiceError(Exception):
    """Base exception for search service errors."""
    pass


class QueryParseError(SearchServiceError):
    """Exception raised when a query cannot be parsed."""
    pass


class InvalidFilterError(SearchServiceError):
    """Exception raised when a filter is invalid."""
    pass


class SortOrder(Enum):
    """Sort order for search results."""
    ASCENDING = "asc"
    DESCENDING = "desc"


class SearchResult:
    """Container for search results with pagination information."""
    
    def __init__(self, tasks: List[TaskEntity], total_count: int, 
                page: int, page_size: int, query: str):
        """
        Initialize a search result.
        
        Args:
            tasks: List of task entities matching the search
            total_count: Total number of tasks matching the search (before pagination)
            page: Current page number (1-based)
            page_size: Number of items per page
            query: The search query that produced these results
        """
        self.tasks = tasks
        self.total_count = total_count
        self.page = page
        self.page_size = page_size
        self.query = query
        
    @property
    def total_pages(self) -> int:
        """Get the total number of pages."""
        if self.page_size <= 0:
            return 1
        return (self.total_count + self.page_size - 1) // self.page_size
    
    @property
    def has_next_page(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous_page(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
    
    def __repr__(self) -> str:
        return (f"SearchResult(tasks_count={len(self.tasks)}, total_count={self.total_count}, "
                f"page={self.page}/{self.total_pages}, page_size={self.page_size})")


class FilterOperator:
    """Filter operators for query expressions."""
    
    # Comparison operators
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUALS = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUALS = "<="
    
    # String operators
    CONTAINS = "contains"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    
    # Collection operators
    IN = "in"
    NOT_IN = "not in"
    
    # Logical operators
    AND = "and"
    OR = "or"
    NOT = "not"


class SearchService:
    """
    Service for searching and filtering tasks.
    
    This service provides methods for executing complex queries against tasks,
    filtering results, and paginating them.
    """
    
    def __init__(self, task_repository: ITaskRepository, logger: Optional[logging.Logger] = None,
                cache_ttl: int = 300, max_cache_size: int = 100):
        """
        Initialize the search service.
        
        Args:
            task_repository: Repository for task operations
            logger: Optional logger for service operations
            cache_ttl: Time-to-live for cached results in seconds
            max_cache_size: Maximum number of queries to cache
        """
        self.task_repository = task_repository
        self.logger = logger or logging.getLogger(__name__)
        self.engine = SearchEngine(task_repository, self.logger)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self._cache = {}  # Query string -> (timestamp, result)
    
    def search(self, query: str, page: int = 1, page_size: int = 20,
              sort_by: Optional[str] = None, sort_order: SortOrder = SortOrder.ASCENDING,
              use_cache: bool = True) -> SearchResult:
        """
        Search for tasks using a query expression.
        
        Args:
            query: Query expression (e.g., "status == 'in_progress' and priority < 3")
            page: Page number (1-based)
            page_size: Number of items per page
            sort_by: Field to sort by (e.g., "created_at", "name")
            sort_order: Sort order (ascending or descending)
            use_cache: Whether to use cached results
            
        Returns:
            SearchResult containing the matching tasks and pagination info
            
        Raises:
            QueryParseError: If the query cannot be parsed
        """
        try:
            with self._lock:
                # Normalize query for cache
                normalized_query = query.strip().lower()
                cache_key = f"{normalized_query}|{sort_by}|{sort_order.value}|{page}|{page_size}"
                
                # Check cache first
                if use_cache and cache_key in self._cache:
                    timestamp, result = self._cache[cache_key]
                    if time.time() - timestamp <= self.cache_ttl:
                        return result
                    # Remove stale cache entry
                    del self._cache[cache_key]
                
                # Run pre-search hooks
                hook_data = {
                    "query": query,
                    "page": page,
                    "page_size": page_size,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                }
                self.hook_registry.execute_hook("pre_search", hook_data)
                
                # Parse the query into a filter function
                try:
                    filter_func = self._parse_query(hook_data["query"])
                except Exception as e:
                    raise QueryParseError(f"Failed to parse query: {str(e)}")
                
                # Fetch all tasks (we'll filter and paginate in memory)
                all_tasks = self.task_repository.list_all()
                
                # Apply the filter
                filtered_tasks = [task for task in all_tasks if filter_func(task)]
                
                # Sort the results
                if hook_data["sort_by"]:
                    try:
                        filtered_tasks = self._sort_tasks(
                            filtered_tasks, 
                            hook_data["sort_by"], 
                            hook_data["sort_order"]
                        )
                    except Exception as e:
                        self.logger.warning(f"Error sorting tasks: {str(e)}")
                
                # Calculate pagination
                total_count = len(filtered_tasks)
                start_idx = (hook_data["page"] - 1) * hook_data["page_size"]
                end_idx = start_idx + hook_data["page_size"]
                paged_tasks = filtered_tasks[start_idx:end_idx]
                
                # Create result
                result = SearchResult(
                    tasks=paged_tasks,
                    total_count=total_count,
                    page=hook_data["page"],
                    page_size=hook_data["page_size"],
                    query=hook_data["query"]
                )
                
                # Run post-search hooks
                hook_response = {
                    "result": result
                }
                self.hook_registry.execute_hook("post_search", hook_response)
                
                # Cache the result
                if use_cache and normalized_query:
                    # Manage cache size (LRU policy)
                    if len(self._cache) >= self.max_cache_size:
                        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                        del self._cache[oldest_key]
                    
                    self._cache[cache_key] = (time.time(), hook_response["result"])
                
                return hook_response["result"]
                
        except Exception as e:
            self.logger.error(f"Error searching tasks: {str(e)}")
            if isinstance(e, (QueryParseError, InvalidFilterError)):
                raise
            raise SearchServiceError(f"Search failed: {str(e)}")
    
    def text_search(self, text: str, fields: List[str] = None, 
                   page: int = 1, page_size: int = 20) -> SearchResult:
        """
        Search for tasks containing specific text in their fields.
        
        Args:
            text: Text to search for
            fields: Fields to search in (defaults to name and description)
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            SearchResult containing the matching tasks and pagination info
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(text, "Search text")
                
                # Default fields
                if not fields:
                    fields = ["name", "description"]
                
                # Run pre-text-search hooks
                hook_data = {
                    "text": text,
                    "fields": fields,
                    "page": page,
                    "page_size": page_size
                }
                self.hook_registry.execute_hook("pre_text_search", hook_data)
                
                # Build a query for the text search
                field_conditions = []
                for field in hook_data["fields"]:
                    field_conditions.append(f"{field} contains '{hook_data['text']}'")
                
                query = " or ".join(field_conditions)
                
                # Execute the search
                return self.search(
                    query=query,
                    page=hook_data["page"],
                    page_size=hook_data["page_size"],
                    sort_by="relevance",
                    use_cache=True
                )
                
        except Exception as e:
            self.logger.error(f"Error performing text search: {str(e)}")
            raise SearchServiceError(f"Text search failed: {str(e)}")
    
    def find_by_status(self, status: TaskStatus, page: int = 1, page_size: int = 20) -> SearchResult:
        """
        Find tasks by status.
        
        Args:
            status: Status to filter by
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            SearchResult containing the matching tasks and pagination info
        """
        query = f"status == '{status.value}'"
        return self.search(query, page, page_size, sort_by="created_at", sort_order=SortOrder.DESCENDING)
    
    def find_by_priority(self, priority: TaskPriority, page: int = 1, page_size: int = 20) -> SearchResult:
        """
        Find tasks by priority.
        
        Args:
            priority: Priority to filter by
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            SearchResult containing the matching tasks and pagination info
        """
        query = f"priority == {priority.value}"
        return self.search(query, page, page_size, sort_by="created_at", sort_order=SortOrder.DESCENDING)
    
    def find_by_tag(self, tag: str, page: int = 1, page_size: int = 20) -> SearchResult:
        """
        Find tasks with a specific tag.
        
        Args:
            tag: Tag to filter by
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            SearchResult containing the matching tasks and pagination info
        """
        query = f"'{tag}' in tags"
        return self.search(query, page, page_size, sort_by="created_at", sort_order=SortOrder.DESCENDING)
    
    def find_related_to(self, task_id: str, page: int = 1, page_size: int = 20) -> SearchResult:
        """
        Find tasks related to a specific task.
        
        Args:
            task_id: ID of the task to find related tasks for
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            SearchResult containing the matching tasks and pagination info
            
        Raises:
            EntityNotFoundError: If the task doesn't exist
        """
        try:
            with self._lock:
                # Validate inputs
                validate_id_format(task_id, "Task ID")
                
                # Get the task
                task = self.task_repository.get(task_id)
                if not task:
                    raise EntityNotFoundError(f"Task with ID {task_id} not found")
                
                # Custom implementation for related tasks
                # This won't use the query parser because we need to check actual task relationships
                all_tasks = self.task_repository.list_all()
                related_tasks = []
                
                for t in all_tasks:
                    if t.id == task_id:
                        continue  # Skip the task itself
                    
                    # Check all relationship types
                    if (t.has_relationship_with(task_id) or 
                        task.has_relationship_with(t.id) or
                        (t.parent_id and t.parent_id == task.parent_id and task.parent_id)):
                        related_tasks.append(t)
                
                # Sort by name
                related_tasks.sort(key=lambda t: t.name)
                
                # Calculate pagination
                total_count = len(related_tasks)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paged_tasks = related_tasks[start_idx:end_idx]
                
                # Create result
                result = SearchResult(
                    tasks=paged_tasks,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    query=f"related_to:{task_id}"
                )
                
                return result
                
        except EntityNotFoundError as e:
            self.logger.error(f"Error finding related tasks: {str(e)}")
            raise
    
    def clear_cache(self) -> None:
        """Clear the search result cache."""
        with self._lock:
            self._cache.clear()
            self.logger.info("Search cache cleared")
    
    def _parse_query(self, query: str) -> Callable[[TaskEntity], bool]:
        """
        Parse a query string into a filter function.
        
        Args:
            query: Query expression
            
        Returns:
            Function that takes a TaskEntity and returns True if it matches the query
            
        Raises:
            QueryParseError: If the query cannot be parsed
        """
        # Special case: empty query matches everything
        query = query.strip()
        if not query:
            return lambda _: True
        
        # Basic parsing for demonstration; in a real implementation,
        # you would use a proper parser for complex queries
        
        # Handle AND/OR operators
        if " and " in query.lower():
            parts = query.lower().split(" and ", 1)
            left = self._parse_query(parts[0])
            right = self._parse_query(parts[1])
            return lambda task: left(task) and right(task)
        
        if " or " in query.lower():
            parts = query.lower().split(" or ", 1)
            left = self._parse_query(parts[0])
            right = self._parse_query(parts[1])
            return lambda task: left(task) or right(task)
        
        # Handle NOT operator
        if query.lower().startswith("not "):
            inner = self._parse_query(query[4:])
            return lambda task: not inner(task)
        
        # Handle comparisons
        for op in [
            FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
            FilterOperator.GREATER_THAN, FilterOperator.GREATER_THAN_OR_EQUALS,
            FilterOperator.LESS_THAN, FilterOperator.LESS_THAN_OR_EQUALS
        ]:
            if f" {op} " in query:
                field, value = query.split(f" {op} ", 1)
                field = field.strip()
                value = value.strip()
                
                # Handle string literals
                if value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Convert numeric values
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") <= 1:
                    value = float(value)
                
                # Convert boolean values
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                
                return self._create_comparison_filter(field, op, value)
        
        # Handle string operations
        if " contains " in query.lower():
            field, value = query.lower().split(" contains ", 1)
            field = field.strip()
            value = value.strip()
            
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            return lambda task: self._get_field_value(task, field) is not None and value in str(self._get_field_value(task, field)).lower()
        
        if " startswith " in query.lower():
            field, value = query.lower().split(" startswith ", 1)
            field = field.strip()
            value = value.strip()
            
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            return lambda task: self._get_field_value(task, field) is not None and str(self._get_field_value(task, field)).lower().startswith(value)
        
        if " endswith " in query.lower():
            field, value = query.lower().split(" endswith ", 1)
            field = field.strip()
            value = value.strip()
            
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            return lambda task: self._get_field_value(task, field) is not None and str(self._get_field_value(task, field)).lower().endswith(value)
        
        # Handle collection operations
        if " in " in query and not " not in " in query:
            value, field = query.split(" in ", 1)
            value = value.strip()
            field = field.strip()
            
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            return lambda task: self._get_field_value(task, field) is not None and value in self._get_field_value(task, field)
        
        if " not in " in query:
            value, field = query.split(" not in ", 1)
            value = value.strip()
            field = field.strip()
            
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            return lambda task: self._get_field_value(task, field) is not None and value not in self._get_field_value(task, field)
        
        # If we get here, the query couldn't be parsed
        raise QueryParseError(f"Could not parse query: {query}")
    
    def _create_comparison_filter(self, field: str, operator: str, value: Any) -> Callable[[TaskEntity], bool]:
        """
        Create a filter function for a comparison operation.
        
        Args:
            field: Field to compare
            operator: Comparison operator
            value: Value to compare against
            
        Returns:
            Function that takes a TaskEntity and returns True if it matches the comparison
        """
        if operator == FilterOperator.EQUALS:
            return lambda task: self._get_field_value(task, field) == value
        
        elif operator == FilterOperator.NOT_EQUALS:
            return lambda task: self._get_field_value(task, field) != value
        
        elif operator == FilterOperator.GREATER_THAN:
            return lambda task: self._get_field_value(task, field) > value
        
        elif operator == FilterOperator.GREATER_THAN_OR_EQUALS:
            return lambda task: self._get_field_value(task, field) >= value
        
        elif operator == FilterOperator.LESS_THAN:
            return lambda task: self._get_field_value(task, field) < value
        
        elif operator == FilterOperator.LESS_THAN_OR_EQUALS:
            return lambda task: self._get_field_value(task, field) <= value
        
        else:
            raise InvalidFilterError(f"Unknown operator: {operator}")
    
    def _get_field_value(self, task: TaskEntity, field: str) -> Any:
        """
        Get the value of a field from a task entity.
        
        Args:
            task: Task entity
            field: Field name or attribute path
            
        Returns:
            Value of the field, or None if the field doesn't exist
        """
        try:
            # Handle nested fields with dot notation
            if "." in field:
                parts = field.split(".")
                value = task
                for part in parts:
                    value = getattr(value, part, None)
                    if value is None:
                        return None
                return value
            
            # Handle simple fields
            return getattr(task, field, None)
        except Exception:
            return None
    
    def _sort_tasks(self, tasks: List[TaskEntity], sort_by: str, 
                   sort_order: SortOrder = SortOrder.ASCENDING) -> List[TaskEntity]:
        """
        Sort a list of tasks by a field.
        
        Args:
            tasks: List of tasks to sort
            sort_by: Field to sort by
            sort_order: Sort order
            
        Returns:
            Sorted list of tasks
            
        Raises:
            InvalidFilterError: If the sort field is invalid
        """
        # Special case for relevance (used in text search)
        if sort_by == "relevance":
            # For now, just return as-is (text search already sorted by relevance)
            return tasks
        
        try:
            reverse = sort_order == SortOrder.DESCENDING
            
            # Get a key function for the sort field
            def key_func(task: TaskEntity) -> Any:
                value = self._get_field_value(task, sort_by)
                # Handle None values for stable sorting
                if value is None:
                    # Sort None values at the end
                    return (1, None) if reverse else (1, None)
                return (0, value)
            
            # Sort the tasks
            return sorted(tasks, key=key_func, reverse=reverse)
        except Exception as e:
            raise InvalidFilterError(f"Invalid sort field: {sort_by}. Error: {str(e)}") 