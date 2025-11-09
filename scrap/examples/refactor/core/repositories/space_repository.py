"""
Space repository implementation.

This module provides the concrete implementation of the space repository interface.
"""

from typing import Dict, List, Any, Optional, Callable, Set, TypeVar, cast
import json
from pathlib import Path

from refactor.core.repositories.repository_interface import (
    ISpaceRepository,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError
)
from refactor.core.entities.space_entity import SpaceEntity
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity

# Import repositories for accessing related entities
from refactor.core.repositories.folder_repository import FolderRepository
from refactor.core.repositories.list_repository import ListRepository

class SpaceRepository(ISpaceRepository):
    """
    Concrete implementation of the space repository interface.
    
    This repository stores spaces in memory and can be initialized from a JSON file.
    """
    
    def __init__(self, json_path: Optional[Path] = None, 
                 folder_repository: Optional[FolderRepository] = None,
                 list_repository: Optional[ListRepository] = None):
        """
        Initialize a new space repository.
        
        Args:
            json_path: Optional path to a JSON file containing space data
            folder_repository: Optional folder repository to use for fetching folder entities
            list_repository: Optional list repository to use for fetching list entities
        """
        self._spaces: Dict[str, SpaceEntity] = {}
        self._spaces_by_name: Dict[str, str] = {}  # name -> id mapping
        self._folders_by_space: Dict[str, List[str]] = {}  # space_id -> [folder_id, ...]
        self._lists_by_space: Dict[str, List[str]] = {}  # space_id -> [list_id, ...]
        self._folder_repository = folder_repository
        self._list_repository = list_repository
        
        if json_path is not None:
            self._load_from_json(json_path)
        
    def _load_from_json(self, json_path: Path) -> None:
        """
        Load space data from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            
        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            json.JSONDecodeError: If the JSON file is invalid
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Load spaces
            for space_data in data.get('spaces', []):
                space_entity = SpaceEntity.from_dict(space_data)
                self._spaces[space_entity.id] = space_entity
                self._spaces_by_name[space_entity.name] = space_entity.id
                
                # Initialize empty folder and list arrays for this space
                self._folders_by_space[space_entity.id] = []
                self._lists_by_space[space_entity.id] = []
                
            # Map folders to spaces
            for folder_data in data.get('folders', []):
                if 'space_id' in folder_data and folder_data['space_id'] in self._spaces:
                    space_id = folder_data['space_id']
                    folder_id = folder_data['id']
                    self._folders_by_space[space_id].append(folder_id)
            
            # Map lists to spaces
            for list_data in data.get('lists', []):
                if 'space_id' in list_data and list_data['space_id'] in self._spaces:
                    space_id = list_data['space_id']
                    list_id = list_data['id']
                    self._lists_by_space[space_id].append(list_id)
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"Space JSON file not found: {json_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in space file: {json_path}")
    
    def add(self, entity: SpaceEntity) -> SpaceEntity:
        """
        Add a new space to the repository.
        
        Args:
            entity: Space entity to add
            
        Returns:
            The added space entity
            
        Raises:
            EntityAlreadyExistsError: If a space with the same ID or name already exists
            ValidationError: If the space entity fails validation
        """
        # Validate entity ID
        if not entity.id:
            raise ValidationError("Space ID cannot be empty")
            
        # Validate entity name
        if not entity.name:
            raise ValidationError("Space name cannot be empty")
            
        # Check for existing ID
        if self.exists(entity.id):
            raise EntityAlreadyExistsError(f"Space with ID {entity.id} already exists")
            
        # Check for existing name
        if entity.name in self._spaces_by_name:
            raise EntityAlreadyExistsError(f"Space with name '{entity.name}' already exists")
            
        # Add the entity
        self._spaces[entity.id] = entity
        self._spaces_by_name[entity.name] = entity.id
        self._folders_by_space[entity.id] = []
        self._lists_by_space[entity.id] = []
        return entity
    
    def update(self, entity: SpaceEntity) -> SpaceEntity:
        """
        Update an existing space in the repository.
        
        Args:
            entity: Space entity with updated data
            
        Returns:
            The updated space entity
            
        Raises:
            EntityNotFoundError: If the space doesn't exist
            ValidationError: If the space entity fails validation
        """
        # Validate entity ID
        if not entity.id:
            raise ValidationError("Space ID cannot be empty")
            
        # Validate entity name
        if not entity.name:
            raise ValidationError("Space name cannot be empty")
            
        # Check if entity exists
        if not self.exists(entity.id):
            raise EntityNotFoundError(f"Space with ID {entity.id} not found")
            
        # Handle name change
        old_space = self._spaces[entity.id]
        if old_space.name != entity.name:
            if entity.name in self._spaces_by_name:
                # Check if the name is already used by another space
                if self._spaces_by_name[entity.name] != entity.id:
                    raise ValidationError(f"Space name '{entity.name}' is already in use")
            
            # Remove old name mapping and add new one
            del self._spaces_by_name[old_space.name]
            self._spaces_by_name[entity.name] = entity.id
            
        # Update the entity
        self._spaces[entity.id] = entity
        return entity
    
    def get(self, entity_id: str) -> SpaceEntity:
        """
        Get a space by its ID.
        
        Args:
            entity_id: ID of the space to get
            
        Returns:
            The space entity with the given ID
            
        Raises:
            EntityNotFoundError: If no space with the given ID exists
            ValidationError: If the entity ID is empty
        """
        # Validate entity ID
        if not entity_id:
            raise ValidationError("Space ID cannot be empty")
            
        # Check if entity exists
        if not self.exists(entity_id):
            raise EntityNotFoundError(f"Space with ID {entity_id} not found")
            
        return self._spaces[entity_id]
    
    def get_by_name(self, name: str) -> SpaceEntity:
        """
        Get a space by its name.
        
        Args:
            name: Name of the space to get
            
        Returns:
            The space entity with the given name
            
        Raises:
            EntityNotFoundError: If no space with the given name exists
            ValidationError: If the name is empty
        """
        # Validate name
        if not name:
            raise ValidationError("Space name cannot be empty")
            
        # Check if entity exists by name
        if name not in self._spaces_by_name:
            raise EntityNotFoundError(f"Space with name '{name}' not found")
            
        space_id = self._spaces_by_name[name]
        return self._spaces[space_id]
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if a space with the given ID exists.
        
        Args:
            entity_id: ID to check
            
        Returns:
            True if a space with the given ID exists, False otherwise
        """
        return entity_id in self._spaces
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete a space by its ID.
        
        Args:
            entity_id: ID of the space to delete
            
        Returns:
            True if the space was deleted, False if it didn't exist
        """
        if not self.exists(entity_id):
            return False
            
        space_entity = self._spaces[entity_id]
        del self._spaces_by_name[space_entity.name]
        del self._spaces[entity_id]
        
        # Clean up the folder and list mappings
        if entity_id in self._folders_by_space:
            del self._folders_by_space[entity_id]
        if entity_id in self._lists_by_space:
            del self._lists_by_space[entity_id]
            
        return True
    
    def list_all(self) -> List[SpaceEntity]:
        """
        Get all spaces in the repository.
        
        Returns:
            List of all space entities
        """
        return list(self._spaces.values())
    
    def count(self) -> int:
        """
        Get the number of spaces in the repository.
        
        Returns:
            Number of spaces
        """
        return len(self._spaces)
    
    def find(self, predicate: Callable[[SpaceEntity], bool]) -> List[SpaceEntity]:
        """
        Find spaces that match a predicate.
        
        Args:
            predicate: Function that takes a space entity and returns True for matches
            
        Returns:
            List of matching space entities
        """
        return [space for space in self._spaces.values() if predicate(space)]
    
    def get_folders(self, space_id: str) -> List[FolderEntity]:
        """
        Get all folders in a space.
        
        Args:
            space_id: ID of the space to get folders for
            
        Returns:
            List of folder entities in the space
            
        Raises:
            EntityNotFoundError: If no space with the given ID exists
            ValidationError: If the space ID is empty
        """
        # Validate space ID
        if not space_id:
            raise ValidationError("Space ID cannot be empty")
            
        # Check if space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(f"Space with ID {space_id} not found")
            
        # Check if there's a folder repository available
        if not self._folder_repository:
            raise RuntimeError("Folder repository not available. Cannot fetch folder entities.")
            
        # Get folder IDs for this space
        folder_ids = self._folders_by_space.get(space_id, [])
        
        # Get actual folder entities from the folder repository
        folder_entities = []
        for folder_id in folder_ids:
            try:
                folder_entity = self._folder_repository.get(folder_id)
                folder_entities.append(folder_entity)
            except EntityNotFoundError:
                # Skip folders that don't exist in the folder repository
                continue
                
        return folder_entities
    
    def get_lists(self, space_id: str) -> List[ListEntity]:
        """
        Get all lists in a space.
        
        Args:
            space_id: ID of the space to get lists for
            
        Returns:
            List of list entities in the space
            
        Raises:
            EntityNotFoundError: If no space with the given ID exists
            ValidationError: If the space ID is empty
        """
        # Validate space ID
        if not space_id:
            raise ValidationError("Space ID cannot be empty")
            
        # Check if space exists
        if not self.exists(space_id):
            raise EntityNotFoundError(f"Space with ID {space_id} not found")
            
        # Check if there's a list repository available
        if not self._list_repository:
            raise RuntimeError("List repository not available. Cannot fetch list entities.")
            
        # Get list IDs for this space
        list_ids = self._lists_by_space.get(space_id, [])
        
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