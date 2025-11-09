"""
Query Service Module - Provides service layer for query operations.

This module implements the QueryService class which handles complex queries
against entities in the system, including filtering, sorting, and pagination.
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set, Tuple, Callable, TypeVar, Generic

from .base_service import BaseService
from ..repositories.repository_interface import IRepository, EntityNotFoundError
from ..entities.base_entity import BaseEntity

T = TypeVar('T', bound=BaseEntity)


class QueryServiceError(Exception):
    """Base exception for query service errors."""
    pass


class QueryService(BaseService, Generic[T]):
    """
    Service for performing queries against a repository.
    
    This service provides methods for filtering, sorting, and paginating
    entities in a repository based on various criteria.
    """
    
    def __init__(self, repository: IRepository[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the query service.
        
        Args:
            repository: Repository to query against
            logger: Optional logger for service operations
        """
        super().__init__(logger)
        self.repository = repository
    
    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Filter entities based on a predicate function.
        
        Args:
            predicate: Function that takes an entity and returns True to include it
            
        Returns:
            List of entities that match the predicate
        """
        with self._lock:
            # Run pre-filter hooks
            hook_data = {"predicate": predicate}
            self._execute_hook("pre_query_filter", hook_data)
            
            # Get filtered entities
            entities = self.repository.find(hook_data["predicate"])
            
            # Run post-filter hooks
            filtered_entities = self._execute_hook_filter("post_query_filter", entities, predicate)
            
            return filtered_entities
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            Entity if found, None otherwise
        """
        with self._lock:
            try:
                # Run pre-get hooks
                hook_data = {"entity_id": entity_id}
                self._execute_hook("pre_query_get", hook_data)
                
                # Get the entity
                entity = self.repository.get(hook_data["entity_id"])
                
                # Run post-get hooks if entity was found
                if entity:
                    entity = self._execute_hook_filter("post_query_get", entity)
                
                return entity
            except EntityNotFoundError:
                return None
    
    def get_all(self) -> List[T]:
        """
        Get all entities in the repository.
        
        Returns:
            List of all entities
        """
        with self._lock:
            # Run pre-get-all hooks
            self._execute_hook("pre_query_get_all", {})
            
            # Get all entities
            entities = self.repository.list_all()
            
            # Run post-get-all hooks
            entities = self._execute_hook_filter("post_query_get_all", entities)
            
            return entities
    
    def paginate(self, 
                 page: int = 1, 
                 page_size: int = 20, 
                 predicate: Optional[Callable[[T], bool]] = None) -> Tuple[List[T], int, int]:
        """
        Get a paginated list of entities.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            predicate: Optional filter predicate
            
        Returns:
            Tuple of (entities, total_count, total_pages)
        """
        with self._lock:
            # Validate page and page_size
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            
            # Run pre-paginate hooks
            hook_data = {"page": page, "page_size": page_size, "predicate": predicate}
            self._execute_hook("pre_query_paginate", hook_data)
            
            # Get all entities that match the predicate
            if hook_data["predicate"]:
                entities = self.repository.find(hook_data["predicate"])
            else:
                entities = self.repository.list_all()
            
            # Calculate total count and pages
            total_count = len(entities)
            total_pages = (total_count + hook_data["page_size"] - 1) // hook_data["page_size"]
            
            # Apply pagination
            start_idx = (hook_data["page"] - 1) * hook_data["page_size"]
            end_idx = start_idx + hook_data["page_size"]
            paginated_entities = entities[start_idx:end_idx]
            
            # Run post-paginate hooks
            result = {
                "entities": paginated_entities,
                "total_count": total_count,
                "total_pages": total_pages
            }
            result = self._execute_hook_filter("post_query_paginate", result)
            
            return result["entities"], result["total_count"], result["total_pages"] 