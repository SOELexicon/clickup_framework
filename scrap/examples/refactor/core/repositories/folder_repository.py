"""
Folder repository implementation.

This module provides the concrete implementation of the folder repository interface.
"""

from typing import Dict, List, Any, Optional, Callable, Set, TypeVar, cast
import json
from pathlib import Path

from refactor.core.repositories.repository_interface import (
    IFolderRepository,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity

# Import ListRepository to access list entities
from refactor.core.repositories.list_repository import ListRepository

class FolderRepository(IFolderRepository):
    """
    Concrete implementation of the folder repository interface.
    
    This repository stores folders in memory and can be initialized from a JSON file.
    """
    
    def __init__(self, json_path: Optional[Path] = None, list_repository: Optional[ListRepository] = None):
        """
        Initialize a new folder repository.
        
        Args:
            json_path: Optional path to a JSON file containing folder data
            list_repository: Optional list repository to use for fetching list entities
        """
        self._folders: Dict[str, FolderEntity] = {}
        self._folders_by_name: Dict[str, str] = {}  # name -> id mapping
        self._lists_by_folder: Dict[str, List[str]] = {}  # folder_id -> [list_id, ...]
        self._list_repository = list_repository
        
        if json_path is not None:
            self._load_from_json(json_path)
        
    def _load_from_json(self, json_path: Path) -> None:
        """
        Load folder data from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            
        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            json.JSONDecodeError: If the JSON file is invalid
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Load folders
            for folder_data in data.get('folders', []):
                folder_entity = FolderEntity.from_dict(folder_data)
                self._folders[folder_entity.id] = folder_entity
                self._folders_by_name[folder_entity.name] = folder_entity.id
                
                # Initialize empty list array for this folder
                self._lists_by_folder[folder_entity.id] = []
                
            # Load lists into folders
            for list_data in data.get('lists', []):
                if 'folder_id' in list_data and list_data['folder_id'] in self._folders:
                    folder_id = list_data['folder_id']
                    list_id = list_data['id']
                    self._lists_by_folder[folder_id].append(list_id)
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"Folder JSON file not found: {json_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in folder file: {json_path}")
    
    def add(self, entity: FolderEntity) -> FolderEntity:
        """
        Add a new folder to the repository.
        
        Args:
            entity: Folder entity to add
            
        Returns:
            The added folder entity
            
        Raises:
            EntityAlreadyExistsError: If a folder with the same ID or name already exists
            ValidationError: If the folder entity fails validation
        """
        # Validate entity ID
        if not entity.id:
            raise ValidationError("Folder ID cannot be empty")
            
        # Validate entity name
        if not entity.name:
            raise ValidationError("Folder name cannot be empty")
            
        # Check for existing ID
        if self.exists(entity.id):
            raise EntityAlreadyExistsError(f"Folder with ID {entity.id} already exists")
            
        # Check for existing name
        if entity.name in self._folders_by_name:
            raise EntityAlreadyExistsError(f"Folder with name '{entity.name}' already exists")
            
        # Add the entity
        self._folders[entity.id] = entity
        self._folders_by_name[entity.name] = entity.id
        self._lists_by_folder[entity.id] = []
        return entity
    
    def update(self, entity: FolderEntity) -> FolderEntity:
        """
        Update an existing folder in the repository.
        
        Args:
            entity: Folder entity with updated data
            
        Returns:
            The updated folder entity
            
        Raises:
            EntityNotFoundError: If the folder doesn't exist
            ValidationError: If the folder entity fails validation
        """
        # Validate entity ID
        if not entity.id:
            raise ValidationError("Folder ID cannot be empty")
            
        # Validate entity name
        if not entity.name:
            raise ValidationError("Folder name cannot be empty")
            
        # Check if entity exists
        if not self.exists(entity.id):
            raise EntityNotFoundError(f"Folder with ID {entity.id} not found")
            
        # Handle name change
        old_folder = self._folders[entity.id]
        if old_folder.name != entity.name:
            if entity.name in self._folders_by_name:
                # Check if the name is already used by another folder
                if self._folders_by_name[entity.name] != entity.id:
                    raise ValidationError(f"Folder name '{entity.name}' is already in use")
            
            # Remove old name mapping and add new one
            del self._folders_by_name[old_folder.name]
            self._folders_by_name[entity.name] = entity.id
            
        # Update the entity
        self._folders[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> FolderEntity:
        """
        Get a folder by its ID.
        
        Args:
            entity_id: ID of the folder to get
            
        Returns:
            The folder entity with the given ID
            
        Raises:
            EntityNotFoundError: If no folder with the given ID exists
            ValidationError: If the entity ID is empty
        """
        # Validate entity ID
        if not entity_id:
            raise ValidationError("Folder ID cannot be empty")
            
        # Check if entity exists
        if not self.exists(entity_id):
            raise EntityNotFoundError(f"Folder with ID {entity_id} not found")
            
        return self._folders[entity_id]
    
    def get_by_name(self, name: str) -> FolderEntity:
        """
        Get a folder by its name.
        
        Args:
            name: Name of the folder to get
            
        Returns:
            The folder entity with the given name
            
        Raises:
            EntityNotFoundError: If no folder with the given name exists
            ValidationError: If the name is empty
        """
        # Validate name
        if not name:
            raise ValidationError("Folder name cannot be empty")
            
        # Check if entity exists by name
        if name not in self._folders_by_name:
            raise EntityNotFoundError(f"Folder with name '{name}' not found")
            
        folder_id = self._folders_by_name[name]
        return self._folders[folder_id]
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if a folder with the given ID exists.
        
        Args:
            entity_id: ID to check
            
        Returns:
            True if a folder with the given ID exists, False otherwise
        """
        return entity_id in self._folders
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete a folder by its ID.
        
        Args:
            entity_id: ID of the folder to delete
            
        Returns:
            True if the folder was deleted, False if it didn't exist
        """
        if not self.exists(entity_id):
            return False
            
        folder_entity = self._folders[entity_id]
        del self._folders_by_name[folder_entity.name]
        del self._folders[entity_id]
        if entity_id in self._lists_by_folder:
            del self._lists_by_folder[entity_id]
        return True
    
    def list_all(self) -> List[FolderEntity]:
        """
        Get all folders in the repository.
        
        Returns:
            List of all folder entities
        """
        return list(self._folders.values())
    
    def count(self) -> int:
        """
        Get the number of folders in the repository.
        
        Returns:
            Number of folder entities
        """
        return len(self._folders)
    
    def find(self, predicate: Callable[[FolderEntity], bool]) -> List[FolderEntity]:
        """
        Find folders that match a predicate.
        
        Args:
            predicate: Function that takes a folder entity and returns True for matches
            
        Returns:
            List of matching folder entities
        """
        return [folder_entity for folder_entity in self._folders.values() if predicate(folder_entity)]
    
    def get_by_space(self, space_id: str) -> List[FolderEntity]:
        """
        Get folders in a specific space.
        
        Args:
            space_id: ID of the space
            
        Returns:
            List of folders in the space
            
        Raises:
            ValidationError: If the space ID is empty
        """
        # Validate space ID
        if not space_id:
            raise ValidationError("Space ID cannot be empty")
            
        return [folder_entity for folder_entity in self._folders.values() 
                if hasattr(folder_entity, 'space_id') and folder_entity.space_id == space_id]
    
    def get_lists(self, folder_id: str) -> List[ListEntity]:
        """
        Get all lists in a folder.
        
        Args:
            folder_id: ID of the folder to get lists for
            
        Returns:
            List of list entities in the folder
            
        Raises:
            EntityNotFoundError: If no folder with the given ID exists
            ValidationError: If the folder ID is empty
        """
        # Validate folder ID
        if not folder_id:
            raise ValidationError("Folder ID cannot be empty")
            
        # Check if folder exists
        if not self.exists(folder_id):
            raise EntityNotFoundError(f"Folder with ID {folder_id} not found")
            
        # Check if there's a list repository available
        if not self._list_repository:
            raise RuntimeError("List repository not available. Cannot fetch list entities.")
            
        # Get list IDs for this folder
        list_ids = self._lists_by_folder.get(folder_id, [])
        
        # Get actual list entities from the list repository
        list_entities = []
        for list_id in list_ids:
            try:
                list_entity = self._list_repository.get(list_id)
                list_entities.append(list_entity)
            except EntityNotFoundError:
                # Skip lists that don't exist in the list repository
                continue
                
        return list_entities 