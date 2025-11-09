"""
Space JSON Repository

This module implements a JSON repository specifically for space entities.
It extends the JsonRepository with space-specific operations.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Type, Union

from refactor.core.entities.space_entity import SpaceEntity
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity
from refactor.core.repositories.json_repository import JsonRepository
from refactor.core.repositories.repository_interface import ISpaceRepository
from refactor.core.repositories.list_json_repository import ListJsonRepository
from refactor.core.repositories.folder_json_repository import FolderJsonRepository
from refactor.core.exceptions import EntityNotFoundError, ValidationError


class SpaceJsonRepository(JsonRepository[SpaceEntity], ISpaceRepository):
    """
    JSON repository implementation for space entities.
    
    This repository extends the generic JsonRepository with space-specific
    operations and implements the ISpaceRepository interface.
    """
    
    def __init__(self, 
                json_path: Path, 
                folder_repository: Optional[FolderJsonRepository] = None,
                list_repository: Optional[ListJsonRepository] = None,
                **kwargs):
        """
        Initialize a new space JSON repository.
        
        Args:
            json_path: Path to the JSON file for space persistence
            folder_repository: Optional folder repository for retrieving folder entities
            list_repository: Optional list repository for retrieving list entities
            **kwargs: Additional arguments to pass to JsonRepository constructor
        """
        super().__init__(SpaceEntity, json_path, **kwargs)
        self._folder_repository = folder_repository
        self._list_repository = list_repository
        
        # Initialize additional mappings
        self._folders_by_space: Dict[str, List[str]] = {}  # space_id -> [folder_id, ...]
        self._lists_by_space: Dict[str, List[str]] = {}  # space_id -> [list_id, ...]
        
        # Build mappings from the loaded entities
        self._build_mappings()
    
    def _build_mappings(self) -> None:
        """
        Build mappings for folders and lists based on loaded entities.
        """
        # Clear existing mappings
        self._folders_by_space = {}
        self._lists_by_space = {}
        
        # Initialize empty arrays for each space
        for space_entity in self.get_all():
            space_id = self._get_entity_id(space_entity)
            self._folders_by_space[space_id] = []
            self._lists_by_space[space_id] = []
        
        # Map folders to spaces if folder repository is available
        if self._folder_repository:
            for folder in self._folder_repository.get_all():
                if hasattr(folder, 'space_id') and folder.space_id:
                    space_id = folder.space_id
                    if space_id in self._folders_by_space:
                        self._folders_by_space[space_id].append(folder.id)
        
        # Map lists to spaces if list repository is available
        if self._list_repository:
            for list_entity in self._list_repository.get_all():
                if hasattr(list_entity, 'space_id') and list_entity.space_id:
                    space_id = list_entity.space_id
                    if space_id in self._lists_by_space:
                        self._lists_by_space[space_id].append(list_entity.id)
    
    def add(self, entity: SpaceEntity) -> SpaceEntity:
        """
        Add a new space entity to the repository.
        
        Args:
            entity: The space entity to add
            
        Returns:
            The added space entity
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
            ValidationError: If the entity is invalid
        """
        # Perform basic validation before passing to parent
        if not entity.name:
            raise ValidationError("Space name cannot be empty")
        
        # Add the entity using parent method
        added_entity = super().add(entity)
        
        # Initialize mappings for the new space
        space_id = self._get_entity_id(added_entity)
        self._folders_by_space[space_id] = []
        self._lists_by_space[space_id] = []
        
        return added_entity
    
    def delete(self, entity_id: str) -> None:
        """
        Delete a space entity by its ID.
        
        Args:
            entity_id: The ID of the space entity to delete
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
            ValidationError: If the space has folders or lists
        """
        # Verify entity exists
        if not self.exists(entity_id):
            raise EntityNotFoundError(entity_id, "Space")
        
        # Check if space has folders
        if entity_id in self._folders_by_space and self._folders_by_space[entity_id]:
            raise ValidationError(f"Cannot delete space with {len(self._folders_by_space[entity_id])} folders. "
                                 "Delete folders first.")
        
        # Check if space has lists
        if entity_id in self._lists_by_space and self._lists_by_space[entity_id]:
            raise ValidationError(f"Cannot delete space with {len(self._lists_by_space[entity_id])} lists. "
                                 "Delete lists first.")
        
        # Remove mappings
        if entity_id in self._folders_by_space:
            del self._folders_by_space[entity_id]
        if entity_id in self._lists_by_space:
            del self._lists_by_space[entity_id]
        
        # Delete the entity using parent method
        super().delete(entity_id)
    
    def get_folders(self, space_id: str) -> List[FolderEntity]:
        """
        Get all folders in a specific space.
        
        Args:
            space_id: ID of the space to get folders for
            
        Returns:
            List of folder entities in the space
            
        Raises:
            EntityNotFoundError: If no space with the given ID exists
        """
        # Verify space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(space_id, "Space")
        
        # Check if folder repository is available
        if not self._folder_repository:
            return []
        
        # Get folder IDs for this space
        folder_ids = self._folders_by_space.get(space_id, [])
        
        # Get folder entities
        folders = []
        for folder_id in folder_ids:
            try:
                folder = self._folder_repository.get(folder_id)
                folders.append(folder)
            except EntityNotFoundError:
                # Skip folders that don't exist
                continue
        
        return folders
    
    def get_lists(self, space_id: str) -> List[ListEntity]:
        """
        Get all lists in a specific space.
        
        Args:
            space_id: ID of the space to get lists for
            
        Returns:
            List of list entities in the space
            
        Raises:
            EntityNotFoundError: If no space with the given ID exists
        """
        # Verify space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(space_id, "Space")
        
        # Check if list repository is available
        if not self._list_repository:
            return []
        
        # Get list IDs for this space
        list_ids = self._lists_by_space.get(space_id, [])
        
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
    
    def add_folder_to_space(self, space_id: str, folder_id: str) -> None:
        """
        Add a folder to a space.
        
        Args:
            space_id: ID of the space
            folder_id: ID of the folder to add
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
        """
        # Verify space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(space_id, "Space")
        
        # Verify folder exists if folder repository is available
        if self._folder_repository and not self._folder_repository.exists(folder_id):
            raise EntityNotFoundError(folder_id, "Folder")
        
        # Initialize folder list if needed
        if space_id not in self._folders_by_space:
            self._folders_by_space[space_id] = []
        
        # Add folder ID to space if not already there
        if folder_id not in self._folders_by_space[space_id]:
            self._folders_by_space[space_id].append(folder_id)
    
    def add_list_to_space(self, space_id: str, list_id: str) -> None:
        """
        Add a list to a space.
        
        Args:
            space_id: ID of the space
            list_id: ID of the list to add
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
        """
        # Verify space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(space_id, "Space")
        
        # Verify list exists if list repository is available
        if self._list_repository and not self._list_repository.exists(list_id):
            raise EntityNotFoundError(list_id, "List")
        
        # Initialize list array if needed
        if space_id not in self._lists_by_space:
            self._lists_by_space[space_id] = []
        
        # Add list ID to space if not already there
        if list_id not in self._lists_by_space[space_id]:
            self._lists_by_space[space_id].append(list_id)
    
    def remove_folder_from_space(self, space_id: str, folder_id: str) -> None:
        """
        Remove a folder from a space.
        
        Args:
            space_id: ID of the space
            folder_id: ID of the folder to remove
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
        """
        # Verify space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(space_id, "Space")
        
        # Remove folder ID from space if present
        if space_id in self._folders_by_space and folder_id in self._folders_by_space[space_id]:
            self._folders_by_space[space_id].remove(folder_id)
    
    def remove_list_from_space(self, space_id: str, list_id: str) -> None:
        """
        Remove a list from a space.
        
        Args:
            space_id: ID of the space
            list_id: ID of the list to remove
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
        """
        # Verify space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(space_id, "Space")
        
        # Remove list ID from space if present
        if space_id in self._lists_by_space and list_id in self._lists_by_space[space_id]:
            self._lists_by_space[space_id].remove(list_id)
    
    def search(self, query: str) -> List[SpaceEntity]:
        """
        Search for spaces matching a query.
        
        Args:
            query: Text to search for in space name and description
            
        Returns:
            List of matching space entities
        """
        # Start with all spaces
        results = self.get_all()
        
        # Filter by text query
        if query:
            query = query.lower()
            results = [space_entity for space_entity in results 
                      if query in space_entity.name.lower() or 
                         (hasattr(space_entity, 'description') and 
                          space_entity.description and 
                          query in space_entity.description.lower())]
        
        return results 