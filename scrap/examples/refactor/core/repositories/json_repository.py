"""
JSON Repository Implementation

This module implements a generic JSON repository that leverages the storage module
to persist entities to JSON files. It implements the Repository interface and can
be used for any entity type.
"""
import json
import os
from pathlib import Path
from typing import Generic, TypeVar, List, Dict, Any, Optional, Callable, Type, Set

from refactor.core.repositories.repository import Repository
from refactor.core.exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError,
    StorageError
)
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.entity_serializer import EntitySerializer

T = TypeVar('T')

class JsonRepository(Generic[T], Repository[T]):
    """
    JSON implementation of the Repository interface.
    
    This repository stores entities in a JSON file, using the storage module for
    file operations and serialization.
    """
    
    def __init__(self, 
                 entity_class: Type[T], 
                 json_path: Path,
                 storage_provider: Optional[JsonStorageProvider] = None,
                 entity_serializer: Optional[EntitySerializer] = None):
        """
        Initialize a new JSON repository.
        
        Args:
            entity_class: The entity class this repository manages
            json_path: Path to the JSON file for persistence
            storage_provider: Optional storage provider for file operations
            entity_serializer: Optional serializer for entity conversion
            
        Raises:
            StorageError: If there's an issue accessing the JSON file
        """
        self._entity_class = entity_class
        self._json_path = json_path
        self._storage_provider = storage_provider or JsonStorageProvider()
        self._entity_serializer = entity_serializer or EntitySerializer(entity_class)
        
        # In-memory storage for entities
        self._entities: Dict[str, T] = {}
        self._entities_by_name: Dict[str, str] = {}  # name -> id mapping
        
        # Load entities from file if it exists
        self._load_entities()
    
    def _load_entities(self) -> None:
        """
        Load entities from the JSON file.
        
        Raises:
            StorageError: If there's an issue accessing or parsing the JSON file
        """
        try:
            if not os.path.exists(self._json_path):
                # Initialize with empty data if file doesn't exist
                self._data = {"entities": []}
                return
                
            # Load data from file
            with open(self._json_path, 'r') as f:
                self._data = json.load(f)
                
            # Process entities
            for entity_data in self._data.get("entities", []):
                entity = self._entity_serializer.deserialize(entity_data)
                self._entities[self._get_entity_id(entity)] = entity
                
                # Map by name if entity has a name
                if hasattr(entity, 'name'):
                    self._entities_by_name[entity.name] = self._get_entity_id(entity)
                    
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            raise StorageError(f"Failed to load entities from {self._json_path}: {str(e)}")
    
    def _save_entities(self) -> None:
        """
        Save entities to the JSON file.
        
        Raises:
            StorageError: If there's an issue writing to the JSON file
        """
        try:
            # Serialize entities
            entity_data = [self._entity_serializer.serialize(entity) for entity in self._entities.values()]
            
            # Update data and save to file
            self._data["entities"] = entity_data
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self._json_path), exist_ok=True)
            
            # Save data to file
            with open(self._json_path, 'w') as f:
                json.dump(self._data, f, indent=2)
                
        except (PermissionError, OSError) as e:
            raise StorageError(f"Failed to save entities to {self._json_path}: {str(e)}")
    
    def _get_entity_id(self, entity: T) -> str:
        """
        Get the ID of an entity.
        
        Args:
            entity: The entity to get the ID for
            
        Returns:
            The entity ID
            
        Raises:
            ValidationError: If the entity doesn't have an ID
        """
        if not hasattr(entity, 'id'):
            raise ValidationError(f"Entity of type {type(entity).__name__} doesn't have an 'id' attribute")
        
        return getattr(entity, 'id')
    
    def add(self, entity: T) -> T:
        """
        Add a new entity to the repository.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
            ValidationError: If the entity is invalid
        """
        entity_id = self._get_entity_id(entity)
        
        # Check if entity with same ID already exists
        if entity_id in self._entities:
            raise EntityAlreadyExistsError(entity_id, self._entity_class.__name__)
        
        # Check if entity with same name already exists (if applicable)
        if hasattr(entity, 'name') and entity.name in self._entities_by_name:
            raise EntityAlreadyExistsError(f"Entity with name '{entity.name}' already exists")
        
        # Add entity to in-memory storage
        self._entities[entity_id] = entity
        
        # Add name mapping if applicable
        if hasattr(entity, 'name'):
            self._entities_by_name[entity.name] = entity_id
        
        # Save changes to file
        self._save_entities()
        
        return entity
    
    def get(self, entity_id: str) -> T:
        """
        Get an entity by its ID.
        
        Args:
            entity_id: The ID of the entity to retrieve
            
        Returns:
            The entity with the specified ID
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
        """
        if entity_id not in self._entities:
            raise EntityNotFoundError(entity_id, self._entity_class.__name__)
        
        return self._entities[entity_id]
    
    def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity with updated values
            
        Returns:
            The updated entity
            
        Raises:
            EntityNotFoundError: If the entity does not exist
            ValidationError: If the updated entity is invalid
        """
        entity_id = self._get_entity_id(entity)
        
        # Check if entity exists
        if entity_id not in self._entities:
            raise EntityNotFoundError(entity_id, self._entity_class.__name__)
        
        # Handle name changes if applicable
        if hasattr(entity, 'name'):
            old_entity = self._entities[entity_id]
            old_name = getattr(old_entity, 'name', None)
            new_name = getattr(entity, 'name', None)
            
            if old_name != new_name:
                # Check if new name is already in use by another entity
                if new_name in self._entities_by_name and self._entities_by_name[new_name] != entity_id:
                    raise ValidationError(f"Entity name '{new_name}' is already in use")
                
                # Update name mapping
                if old_name in self._entities_by_name:
                    del self._entities_by_name[old_name]
                
                if new_name:
                    self._entities_by_name[new_name] = entity_id
        
        # Update entity in memory
        self._entities[entity_id] = entity
        
        # Save changes to file
        self._save_entities()
        
        return entity
    
    def delete(self, entity_id: str) -> None:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
        """
        if entity_id not in self._entities:
            raise EntityNotFoundError(entity_id, self._entity_class.__name__)
        
        # Remove name mapping if applicable
        entity = self._entities[entity_id]
        if hasattr(entity, 'name') and entity.name in self._entities_by_name:
            del self._entities_by_name[entity.name]
        
        # Remove entity from memory
        del self._entities[entity_id]
        
        # Save changes to file
        self._save_entities()
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            entity_id: The ID to check
            
        Returns:
            True if an entity with the given ID exists, False otherwise
        """
        return entity_id in self._entities
    
    def get_all(self) -> List[T]:
        """
        Get all entities in the repository.
        
        Returns:
            A list of all entities
        """
        return list(self._entities.values())
    
    def find_by_name(self, name: str) -> Optional[T]:
        """
        Find an entity by its name.
        
        Args:
            name: The name to search for
            
        Returns:
            The entity with the given name, or None if not found
        """
        if name not in self._entities_by_name:
            return None
        
        entity_id = self._entities_by_name[name]
        return self._entities[entity_id]
    
    def find_by_property(self, property_name: str, property_value: Any) -> List[T]:
        """
        Find entities by a property value.
        
        Args:
            property_name: The name of the property to filter by
            property_value: The value to filter for
            
        Returns:
            A list of entities where the specified property matches the value
        """
        results = []
        
        for entity in self._entities.values():
            if hasattr(entity, property_name):
                entity_value = getattr(entity, property_name)
                
                # Handle lists and sets
                if isinstance(entity_value, (list, set)) and property_value in entity_value:
                    results.append(entity)
                # Handle direct comparison
                elif entity_value == property_value:
                    results.append(entity)
        
        return results
    
    def count(self) -> int:
        """
        Get the number of entities in the repository.
        
        Returns:
            The number of entities
        """
        return len(self._entities)
    
    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Filter entities by a predicate.
        
        Args:
            predicate: A function that takes an entity and returns a boolean
            
        Returns:
            A list of entities for which the predicate returns True
        """
        return [entity for entity in self._entities.values() if predicate(entity)] 