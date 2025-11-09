"""
Folder Service Module - Provides service layer for folder operations.

This module implements the FolderService class which handles all folder-related
operations, including CRUD operations, folder management, and
relationship with lists and spaces.
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Set

from ..entities.folder_entity import FolderEntity
from ..repositories.repository_interface import IFolderRepository, EntityNotFoundError, ValidationError
from ..utils.validation import validate_not_empty, validate_id_format
from ...plugins.hooks.hook_system import global_hook_registry


class FolderServiceError(Exception):
    """Base exception for folder service errors."""
    pass


class FolderNotFoundError(FolderServiceError):
    """Exception raised when a folder is not found."""
    pass


class FolderValidationError(FolderServiceError):
    """Exception raised when folder validation fails."""
    pass


class FolderService:
    """
    Service for managing folders.
    
    This service provides methods for creating, updating, retrieving,
    and deleting folders, as well as managing folder relationships with
    lists and spaces.
    """
    
    def __init__(self, folder_repository: IFolderRepository, logger: Optional[logging.Logger] = None):
        """
        Initialize the folder service.
        
        Args:
            folder_repository: Repository for folder operations
            logger: Optional logger for service operations
        """
        self.folder_repository = folder_repository
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
    
    def create_folder(self, name: str, space_id: str, description: str = "",
                      hidden: bool = False) -> FolderEntity:
        """
        Create a new folder.
        
        Args:
            name: Name of the folder
            space_id: ID of the space that contains this folder
            description: Optional description of the folder
            hidden: Whether the folder should be hidden
            
        Returns:
            The created folder entity
            
        Raises:
            FolderValidationError: If the folder data is invalid
        """
        try:
            with self._lock:
                # Validate inputs
                validate_not_empty(name, "Folder name")
                validate_id_format(space_id, "Space ID")
                
                # Run pre-create hooks
                hook_data = {"name": name, "space_id": space_id, 
                            "description": description, "hidden": hidden}
                self.hook_registry.execute_hook("pre_folder_create", hook_data)
                
                # Create the folder entity
                folder_entity = FolderEntity(
                    name=hook_data["name"],
                    space_id=hook_data["space_id"],
                    description=hook_data["description"],
                    hidden=hook_data["hidden"]
                )
                
                # Save to repository
                created_folder = self.folder_repository.add(folder_entity)
                
                # Run post-create hooks
                self.hook_registry.execute_hook(
                    "post_folder_create", 
                    {"folder_entity": created_folder}
                )
                
                self.logger.info(f"Created folder '{name}' in space {space_id}")
                return created_folder
                
        except ValidationError as e:
            self.logger.error(f"Validation error creating folder: {str(e)}")
            raise FolderValidationError(f"Invalid folder data: {str(e)}")
    
    def update_folder(self, folder_id: str, name: Optional[str] = None, 
                     description: Optional[str] = None, 
                     hidden: Optional[bool] = None) -> FolderEntity:
        """
        Update an existing folder.
        
        Args:
            folder_id: ID of the folder to update
            name: New name for the folder
            description: New description for the folder
            hidden: New hidden status for the folder
            
        Returns:
            The updated folder entity
            
        Raises:
            FolderNotFoundError: If the folder doesn't exist
            FolderValidationError: If the update data is invalid
        """
        try:
            with self._lock:
                # Validate folder exists
                folder_entity = self.folder_repository.get(folder_id)
                if not folder_entity:
                    raise EntityNotFoundError(f"Folder with ID {folder_id} not found")
                
                # Prepare update data
                update_data = {}
                if name is not None:
                    validate_not_empty(name, "Folder name")
                    update_data["name"] = name
                if description is not None:
                    update_data["description"] = description
                if hidden is not None:
                    update_data["hidden"] = hidden
                
                # Run pre-update hooks
                hook_data = {"folder_entity": folder_entity, "updates": update_data}
                self.hook_registry.execute_hook("pre_folder_update", hook_data)
                
                # Apply updates
                for key, value in hook_data["updates"].items():
                    setattr(folder_entity, key, value)
                
                # Save to repository
                updated_folder = self.folder_repository.update(folder_entity)
                
                # Run post-update hooks
                self.hook_registry.execute_hook(
                    "post_folder_update", 
                    {"folder_entity": updated_folder, "updated_fields": list(update_data.keys())}
                )
                
                self.logger.info(f"Updated folder {folder_id}")
                return updated_folder
                
        except EntityNotFoundError as e:
            self.logger.error(f"Folder not found: {str(e)}")
            raise FolderNotFoundError(str(e))
        except ValidationError as e:
            self.logger.error(f"Validation error updating folder: {str(e)}")
            raise FolderValidationError(f"Invalid folder data: {str(e)}")
    
    def get_folder(self, folder_id: str) -> FolderEntity:
        """
        Get a folder by its ID.
        
        Args:
            folder_id: ID of the folder to retrieve
            
        Returns:
            The folder entity
            
        Raises:
            FolderNotFoundError: If the folder doesn't exist
        """
        try:
            with self._lock:
                folder_entity = self.folder_repository.get(folder_id)
                if not folder_entity:
                    raise EntityNotFoundError(f"Folder with ID {folder_id} not found")
                return folder_entity
        except EntityNotFoundError as e:
            self.logger.error(f"Folder not found: {str(e)}")
            raise FolderNotFoundError(str(e))
    
    def get_folder_by_name(self, name: str, space_id: str) -> Optional[FolderEntity]:
        """
        Get a folder by its name within a specific space.
        
        Args:
            name: Name of the folder to retrieve
            space_id: ID of the space containing the folder
            
        Returns:
            The folder entity or None if not found
        """
        with self._lock:
            return self.folder_repository.get_by_name(name, space_id)
    
    def delete_folder(self, folder_id: str) -> None:
        """
        Delete a folder by its ID.
        
        Args:
            folder_id: ID of the folder to delete
            
        Raises:
            FolderNotFoundError: If the folder doesn't exist
        """
        try:
            with self._lock:
                # Check if folder exists
                folder_entity = self.folder_repository.get(folder_id)
                if not folder_entity:
                    raise EntityNotFoundError(f"Folder with ID {folder_id} not found")
                
                # Run pre-delete hooks
                hook_data = {"folder_entity": folder_entity}
                self.hook_registry.execute_hook("pre_folder_delete", hook_data)
                
                # Delete the folder
                self.folder_repository.delete(folder_id)
                
                # Run post-delete hooks
                self.hook_registry.execute_hook(
                    "post_folder_delete", 
                    {"folder_id": folder_id, "folder_name": folder_entity.name}
                )
                
                self.logger.info(f"Deleted folder {folder_id}")
        except EntityNotFoundError as e:
            self.logger.error(f"Folder not found: {str(e)}")
            raise FolderNotFoundError(str(e))
    
    def get_folders_in_space(self, space_id: str) -> List[FolderEntity]:
        """
        Get all folders in a specific space.
        
        Args:
            space_id: ID of the space
            
        Returns:
            List of folder entities
        """
        with self._lock:
            return self.folder_repository.get_by_space(space_id)
    
    def search_folders(self, query: str) -> List[FolderEntity]:
        """
        Search for folders by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of folder entities matching the query
        """
        with self._lock:
            return self.folder_repository.search(query)
    
    def count_folders(self, space_id: Optional[str] = None) -> int:
        """
        Count folders, optionally filtered by space.
        
        Args:
            space_id: Optional space ID to filter by
            
        Returns:
            Number of folders
        """
        with self._lock:
            if space_id:
                return len(self.folder_repository.get_by_space(space_id))
            return self.folder_repository.count() 