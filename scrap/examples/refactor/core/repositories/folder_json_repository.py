"""
Folder JSON Repository

This module implements a JSON repository specifically for folder entities.
It extends the JsonRepository with folder-specific operations.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Type, Union

from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity
from refactor.core.repositories.json_repository import JsonRepository
from refactor.core.repositories.repository_interface import IFolderRepository
from refactor.core.repositories.list_json_repository import ListJsonRepository
from refactor.core.exceptions import EntityNotFoundError, ValidationError


class FolderJsonRepository(JsonRepository[FolderEntity], IFolderRepository):
    """
    JSON repository implementation for folder entities.
    
    This repository extends the generic JsonRepository with folder-specific
    operations and implements the IFolderRepository interface.
    """
    
    def __init__(self, 
                json_path: Path, 
                list_repository: Optional[ListJsonRepository] = None,
                **kwargs):
        """
        Initialize a new folder JSON repository.
        
        Args:
            json_path: Path to the JSON file for folder persistence
            list_repository: Optional list repository for retrieving list entities
            **kwargs: Additional arguments to pass to JsonRepository constructor
        """
        super().__init__(FolderEntity, json_path, **kwargs)
        self._list_repository = list_repository
        
        # Initialize additional mappings
        self._lists_by_folder: Dict[str, List[str]] = {}  # folder_id -> [list_id, ...]
        
        # Build mappings from the loaded entities
        self._build_mappings()
    
    def _build_mappings(self) -> None:
        """
        Build mappings for lists based on loaded entities.
        """
        # Clear existing mappings
        self._lists_by_folder = {}
        
        # Initialize empty arrays for each folder
        for folder_entity in self.get_all():
            folder_id = self._get_entity_id(folder_entity)
            self._lists_by_folder[folder_id] = []
        
        # Map lists to folders if list repository is available
        if self._list_repository:
            for list_entity in self._list_repository.get_all():
                if hasattr(list_entity, 'folder_id') and list_entity.folder_id:
                    folder_id = list_entity.folder_id
                    if folder_id in self._lists_by_folder:
                        self._lists_by_folder[folder_id].append(list_entity.id)
    
    def add(self, entity: FolderEntity) -> FolderEntity:
        """
        Add a new folder entity to the repository.
        
        Args:
            entity: The folder entity to add
            
        Returns:
            The added folder entity
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
            ValidationError: If the entity is invalid
        """
        # Perform basic validation before passing to parent
        if not entity.name:
            raise ValidationError("Folder name cannot be empty")
        if not entity.space_id:
            raise ValidationError("Folder must belong to a space")
        
        # Add the entity using parent method
        added_entity = super().add(entity)
        
        # Initialize mappings for the new folder
        folder_id = self._get_entity_id(added_entity)
        self._lists_by_folder[folder_id] = []
        
        return added_entity
    
    def update(self, entity: FolderEntity) -> FolderEntity:
        """
        Update an existing folder entity.
        
        Args:
            entity: The folder entity to update
            
        Returns:
            The updated folder entity
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
            ValidationError: If the entity is invalid
        """
        # Perform basic validation before passing to parent
        if not entity.name:
            raise ValidationError("Folder name cannot be empty")
        if not entity.space_id:
            raise ValidationError("Folder must belong to a space")
        
        # Verify entity exists
        entity_id = self._get_entity_id(entity)
        if not self.exists(entity_id):
            raise EntityNotFoundError(entity_id, "Folder")
        
        # Update the entity using parent method
        return super().update(entity)
    
    def delete(self, entity_id: str) -> None:
        """
        Delete a folder entity by its ID.
        
        Args:
            entity_id: The ID of the folder entity to delete
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
            ValidationError: If the folder has lists
        """
        # Verify entity exists
        if not self.exists(entity_id):
            raise EntityNotFoundError(entity_id, "Folder")
        
        # Check if folder has lists
        if entity_id in self._lists_by_folder and self._lists_by_folder[entity_id]:
            raise ValidationError(f"Cannot delete folder with {len(self._lists_by_folder[entity_id])} lists. "
                                 "Delete lists first.")
        
        # Remove mappings
        if entity_id in self._lists_by_folder:
            del self._lists_by_folder[entity_id]
        
        # Delete the entity using parent method
        super().delete(entity_id)
    
    def get_lists(self, folder_id: str) -> List[ListEntity]:
        """
        Get all lists in a specific folder.
        
        Args:
            folder_id: ID of the folder to get lists for
            
        Returns:
            List of list entities in the folder
            
        Raises:
            EntityNotFoundError: If no folder with the given ID exists
        """
        # Verify folder exists
        if not self.exists(folder_id):
            raise EntityNotFoundError(folder_id, "Folder")
        
        # Check if list repository is available
        if not self._list_repository:
            return []
        
        # Get list IDs for this folder
        list_ids = self._lists_by_folder.get(folder_id, [])
        
        # Get list entities
        lists = []
        for list_id in list_ids:
            try:
                list_entity = self._list_repository.get(list_id)
                lists.append(list_entity)
            except EntityNotFoundError:
                # Skip lists that don't exist
                continue
        
        return lists
    
    def add_list_to_folder(self, folder_id: str, list_id: str) -> None:
        """
        Add a list to a folder.
        
        Args:
            folder_id: ID of the folder
            list_id: ID of the list to add
            
        Raises:
            EntityNotFoundError: If the folder doesn't exist
        """
        # Verify folder exists
        if not self.exists(folder_id):
            raise EntityNotFoundError(folder_id, "Folder")
        
        # Verify list exists if list repository is available
        if self._list_repository and not self._list_repository.exists(list_id):
            raise EntityNotFoundError(list_id, "List")
        
        # Initialize list array if needed
        if folder_id not in self._lists_by_folder:
            self._lists_by_folder[folder_id] = []
        
        # Add list ID to folder if not already there
        if list_id not in self._lists_by_folder[folder_id]:
            self._lists_by_folder[folder_id].append(list_id)
    
    def remove_list_from_folder(self, folder_id: str, list_id: str) -> None:
        """
        Remove a list from a folder.
        
        Args:
            folder_id: ID of the folder
            list_id: ID of the list to remove
            
        Raises:
            EntityNotFoundError: If the folder doesn't exist
        """
        # Verify folder exists
        if not self.exists(folder_id):
            raise EntityNotFoundError(folder_id, "Folder")
        
        # Remove list ID from folder if present
        if folder_id in self._lists_by_folder and list_id in self._lists_by_folder[folder_id]:
            self._lists_by_folder[folder_id].remove(list_id)
    
    def get_by_space(self, space_id: str) -> List[FolderEntity]:
        """
        Get all folders in a specific space.
        
        Args:
            space_id: ID of the space to get folders for
            
        Returns:
            List of folder entities in the space
        """
        # Filter folders by space ID
        return [folder for folder in self.get_all() if folder.space_id == space_id]
    
    def search(self, query: str, space_id: Optional[str] = None) -> List[FolderEntity]:
        """
        Search for folders matching a query, optionally filtered by space.
        
        Args:
            query: Text to search for in folder name and description
            space_id: Optional space ID to filter folders by
            
        Returns:
            List of matching folder entities
        """
        # Start with all folders
        results = self.get_all()
        
        # Filter by space if provided
        if space_id:
            results = [folder for folder in results if folder.space_id == space_id]
        
        # Filter by text query
        if query:
            query = query.lower()
            results = [folder for folder in results 
                      if query in folder.name.lower() or 
                         (hasattr(folder, 'description') and 
                          folder.description and 
                          query in folder.description.lower())]
        
        return results 