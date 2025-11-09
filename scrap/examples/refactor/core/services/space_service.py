"""
Space Service Module - Provides service layer for space operations.

This module implements the SpaceService class which handles all space-related
operations, including CRUD operations and space management.
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set

from ..entities.space_entity import SpaceEntity
from ..repositories.repository_interface import ISpaceRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class SpaceServiceError(Exception):
    """Base exception for space service errors."""
    pass


class SpaceNotFoundError(SpaceServiceError):
    """Exception raised when a space is not found."""
    pass


class SpaceValidationError(SpaceServiceError):
    """Exception raised when space validation fails."""
    pass


class SpaceService:
    """
    Service for managing spaces.
    
    This service provides methods for creating, updating, retrieving,
    and deleting spaces.
    """
    
    def __init__(self, space_repository: ISpaceRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the space service.
        
        Args:
            space_repository: Repository for space operations
            logger: Optional logger for service operations
        """
        self.space_repository = space_repository
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
    
    def create_space(self, name: str, description: str = "",
                    color: Optional[str] = None, private: bool = False) -> SpaceEntity:
        """
        Create a new space.
        
        Args:
            name: Name of the space
            description: Optional description of the space
            color: Optional color code for the space
            private: Whether the space is private
            
        Returns:
            The created space entity
            
        Raises:
            SpaceValidationError: If the space data is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(name, "Space name")
                
                # Run pre-create hooks
                hook_data = {"name": name, "description": description, 
                            "color": color, "private": private}
                self.hook_registry.execute_hook("pre_space_create", hook_data)
                
                # Create the space entity
                space_entity = SpaceEntity(
                    name=hook_data["name"],
                    description=hook_data["description"],
                    color=hook_data["color"],
                    private=hook_data["private"]
                )
                
                # Save to repository
                created_space = self.space_repository.add(space_entity)
                
                # Run post-create hooks
                self.hook_registry.execute_hook(
                    "post_space_create", 
                    {"space_entity": created_space}
                )
                
                self.logger.info(f"Created space '{name}'")
                return created_space
                
        except ValidationError as e:
            self.logger.error(f"Validation error creating space: {str(e)}")
            raise SpaceValidationError(f"Invalid space data: {str(e)}")
    
    def update_space(self, space_id: str, name: Optional[str] = None, 
                    description: Optional[str] = None, 
                    color: Optional[str] = None,
                    private: Optional[bool] = None) -> SpaceEntity:
        """
        Update an existing space.
        
        Args:
            space_id: ID of the space to update
            name: New name for the space
            description: New description for the space
            color: New color code for the space
            private: New private status for the space
            
        Returns:
            The updated space entity
            
        Raises:
            SpaceNotFoundError: If the space doesn't exist
            SpaceValidationError: If the update data is invalid
        """
        try:
            with self._lock:
                # Validate space exists
                space_entity = self.space_repository.get(space_id)
                if not space_entity:
                    raise EntityNotFoundError(f"Space with ID {space_id} not found")
                
                # Prepare update data
                update_data = {}
                if name is not None:
                    validate_not_empty(name, "Space name")
                    update_data["name"] = name
                if description is not None:
                    update_data["description"] = description
                if color is not None:
                    update_data["color"] = color
                if private is not None:
                    update_data["private"] = private
                
                # Run pre-update hooks
                hook_data = {"space_entity": space_entity, "updates": update_data}
                self.hook_registry.execute_hook("pre_space_update", hook_data)
                
                # Apply updates
                for key, value in hook_data["updates"].items():
                    setattr(space_entity, key, value)
                
                # Save to repository
                updated_space = self.space_repository.update(space_entity)
                
                # Run post-update hooks
                self.hook_registry.execute_hook(
                    "post_space_update", 
                    {"space_entity": updated_space, "updated_fields": list(update_data.keys())}
                )
                
                self.logger.info(f"Updated space {space_id}")
                return updated_space
                
        except EntityNotFoundError as e:
            self.logger.error(f"Space not found: {str(e)}")
            raise SpaceNotFoundError(str(e))
        except ValidationError as e:
            self.logger.error(f"Validation error updating space: {str(e)}")
            raise SpaceValidationError(f"Invalid space data: {str(e)}")
    
    def get_space(self, space_id: str) -> SpaceEntity:
        """
        Get a space by its ID.
        
        Args:
            space_id: ID of the space to retrieve
            
        Returns:
            The space entity
            
        Raises:
            SpaceNotFoundError: If the space doesn't exist
        """
        try:
            with self._lock:
                space_entity = self.space_repository.get(space_id)
                if not space_entity:
                    raise EntityNotFoundError(f"Space with ID {space_id} not found")
                return space_entity
        except EntityNotFoundError as e:
            self.logger.error(f"Space not found: {str(e)}")
            raise SpaceNotFoundError(str(e))
    
    def get_space_by_name(self, name: str) -> Optional[SpaceEntity]:
        """
        Get a space by its name.
        
        Args:
            name: Name of the space to retrieve
            
        Returns:
            The space entity or None if not found
        """
        with self._lock:
            return self.space_repository.get_by_name(name)
    
    def delete_space(self, space_id: str) -> None:
        """
        Delete a space by its ID.
        
        Args:
            space_id: ID of the space to delete
            
        Raises:
            SpaceNotFoundError: If the space doesn't exist
        """
        try:
            with self._lock:
                # Check if space exists
                space_entity = self.space_repository.get(space_id)
                if not space_entity:
                    raise EntityNotFoundError(f"Space with ID {space_id} not found")
                
                # Run pre-delete hooks
                hook_data = {"space_entity": space_entity}
                self.hook_registry.execute_hook("pre_space_delete", hook_data)
                
                # Delete the space
                self.space_repository.delete(space_id)
                
                # Run post-delete hooks
                self.hook_registry.execute_hook(
                    "post_space_delete", 
                    {"space_id": space_id, "space_name": space_entity.name}
                )
                
                self.logger.info(f"Deleted space {space_id}")
        except EntityNotFoundError as e:
            self.logger.error(f"Space not found: {str(e)}")
            raise SpaceNotFoundError(str(e))
    
    def list_all_spaces(self) -> List[SpaceEntity]:
        """
        List all spaces.
        
        Returns:
            List of all space entities
        """
        with self._lock:
            return self.space_repository.list_all()
    
    def search_spaces(self, query: str) -> List[SpaceEntity]:
        """
        Search for spaces by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of space entities matching the query
        """
        with self._lock:
            return self.space_repository.search(query)
    
    def count_spaces(self) -> int:
        """
        Count all spaces.
        
        Returns:
            Number of spaces
        """
        with self._lock:
            return self.space_repository.count() 