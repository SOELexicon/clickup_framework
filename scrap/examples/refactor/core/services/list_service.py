"""
List Service Module - Provides service layer for list operations.

This module implements the ListService class which handles all list-related
operations, including CRUD operations, list status management, and
relationship with tasks and folders.
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set

from ..entities.list_entity import ListEntity
from ..repositories.repository_interface import IListRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class ListServiceError(Exception):
    """Base exception for list service errors."""
    pass


class ListNotFoundError(ListServiceError):
    """Exception raised when a list is not found."""
    pass


class ListValidationError(ListServiceError):
    """Exception raised when list validation fails."""
    pass


class ListService:
    """
    Service for managing lists.
    
    This service provides methods for creating, updating, retrieving,
    and deleting lists, as well as managing list relationships with
    tasks and folders.
    """
    
    def __init__(self, list_repository: IListRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the list service.
        
        Args:
            list_repository: Repository for list operations
            logger: Optional logger for service operations
        """
        self.list_repository = list_repository
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
    
    def create_list(self, name: str, folder_id: str, description: str = "",
                    color: Optional[str] = None) -> ListEntity:
        """
        Create a new list.
        
        Args:
            name: Name of the list
            folder_id: ID of the folder that contains this list
            description: Optional description of the list
            color: Optional color code for the list
            
        Returns:
            The created list entity
            
        Raises:
            ListValidationError: If the list data is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(name, "List name")
                validate_id_format(folder_id, "Folder ID")
                
                # Run pre-create hooks
                hook_data = {"name": name, "folder_id": folder_id, 
                            "description": description, "color": color}
                self.hook_registry.execute_hook("pre_list_create", hook_data)
                
                # Create the list entity
                list_entity = ListEntity(
                    name=hook_data["name"],
                    folder_id=hook_data["folder_id"],
                    description=hook_data["description"],
                    color=hook_data["color"]
                )
                
                # Save to repository
                created_list = self.list_repository.add(list_entity)
                
                # Run post-create hooks
                self.hook_registry.execute_hook(
                    "post_list_create", 
                    {"list_entity": created_list}
                )
                
                self.logger.info(f"Created list '{name}' in folder {folder_id}")
                return created_list
                
        except ValidationError as e:
            self.logger.error(f"Validation error creating list: {str(e)}")
            raise ListValidationError(f"Invalid list data: {str(e)}")
    
    def update_list(self, list_id: str, name: Optional[str] = None, 
                    description: Optional[str] = None, 
                    color: Optional[str] = None) -> ListEntity:
        """
        Update an existing list.
        
        Args:
            list_id: ID of the list to update
            name: New name for the list
            description: New description for the list
            color: New color code for the list
            
        Returns:
            The updated list entity
            
        Raises:
            ListNotFoundError: If the list doesn't exist
            ListValidationError: If the update data is invalid
        """
        try:
            with self._lock:
                # Validate list exists
                list_entity = self.list_repository.get(list_id)
                if not list_entity:
                    raise EntityNotFoundError(f"List with ID {list_id} not found")
                
                # Prepare update data
                update_data = {}
                if name is not None:
                    validate_not_empty(name, "List name")
                    update_data["name"] = name
                if description is not None:
                    update_data["description"] = description
                if color is not None:
                    update_data["color"] = color
                
                # Run pre-update hooks
                hook_data = {"list_entity": list_entity, "updates": update_data}
                self.hook_registry.execute_hook("pre_list_update", hook_data)
                
                # Apply updates
                for key, value in hook_data["updates"].items():
                    setattr(list_entity, key, value)
                
                # Save to repository
                updated_list = self.list_repository.update(list_entity)
                
                # Run post-update hooks
                self.hook_registry.execute_hook(
                    "post_list_update", 
                    {"list_entity": updated_list, "updated_fields": list(update_data.keys())}
                )
                
                self.logger.info(f"Updated list {list_id}")
                return updated_list
                
        except EntityNotFoundError as e:
            self.logger.error(f"List not found: {str(e)}")
            raise ListNotFoundError(str(e))
        except ValidationError as e:
            self.logger.error(f"Validation error updating list: {str(e)}")
            raise ListValidationError(f"Invalid list data: {str(e)}")
    
    def get_list(self, list_id: str) -> ListEntity:
        """
        Get a list by its ID.
        
        Args:
            list_id: ID of the list to retrieve
            
        Returns:
            The list entity
            
        Raises:
            ListNotFoundError: If the list doesn't exist
        """
        try:
            with self._lock:
                list_entity = self.list_repository.get(list_id)
                if not list_entity:
                    raise EntityNotFoundError(f"List with ID {list_id} not found")
                return list_entity
        except EntityNotFoundError as e:
            self.logger.error(f"List not found: {str(e)}")
            raise ListNotFoundError(str(e))
    
    def get_list_by_name(self, name: str, folder_id: str) -> Optional[ListEntity]:
        """
        Get a list by its name within a specific folder.
        
        Args:
            name: Name of the list to retrieve
            folder_id: ID of the folder containing the list
            
        Returns:
            The list entity or None if not found
        """
        with self._lock:
            return self.list_repository.get_by_name(name, folder_id)
    
    def delete_list(self, list_id: str) -> None:
        """
        Delete a list by its ID.
        
        Args:
            list_id: ID of the list to delete
            
        Raises:
            ListNotFoundError: If the list doesn't exist
        """
        try:
            with self._lock:
                # Check if list exists
                list_entity = self.list_repository.get(list_id)
                if not list_entity:
                    raise EntityNotFoundError(f"List with ID {list_id} not found")
                
                # Run pre-delete hooks
                hook_data = {"list_entity": list_entity}
                self.hook_registry.execute_hook("pre_list_delete", hook_data)
                
                # Delete the list
                self.list_repository.delete(list_id)
                
                # Run post-delete hooks
                self.hook_registry.execute_hook(
                    "post_list_delete", 
                    {"list_id": list_id, "list_name": list_entity.name}
                )
                
                self.logger.info(f"Deleted list {list_id}")
        except EntityNotFoundError as e:
            self.logger.error(f"List not found: {str(e)}")
            raise ListNotFoundError(str(e))
    
    def get_lists_in_folder(self, folder_id: str) -> List[ListEntity]:
        """
        Get all lists in a specific folder.
        
        Args:
            folder_id: ID of the folder
            
        Returns:
            List of list entities
        """
        with self._lock:
            return self.list_repository.get_by_folder(folder_id)
    
    def search_lists(self, query: str) -> List[ListEntity]:
        """
        Search for lists by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of list entities matching the query
        """
        with self._lock:
            return self.list_repository.search(query)
    
    def count_lists(self, folder_id: Optional[str] = None) -> int:
        """
        Count lists, optionally filtered by folder.
        
        Args:
            folder_id: Optional folder ID to filter by
            
        Returns:
            Number of lists
        """
        with self._lock:
            if folder_id:
                return len(self.list_repository.get_by_folder(folder_id))
            return self.list_repository.count() 