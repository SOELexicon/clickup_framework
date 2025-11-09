"""
Mock Repository

This module provides an in-memory repository implementation for testing purposes.
It implements the Repository interface while storing entities in memory.
"""
from typing import Generic, TypeVar, List, Optional, Any, Dict, Callable, Type
import copy

from refactor.core.repositories.repository import Repository
from refactor.core.exceptions import EntityNotFoundError, EntityAlreadyExistsError, ValidationError

T = TypeVar('T')


class InMemoryRepository(Generic[T], Repository[T]):
    """
    In-memory repository implementation for testing.
    
    This repository stores entities in memory and provides the standard repository
    interface methods for tests that need to interact with a repository.
    """
    
    def __init__(self, entity_class: Type[T]):
        """
        Initialize the repository.
        
        Args:
            entity_class: The class of entities this repository will store
        """
        self._entity_class = entity_class
        self._entities: Dict[str, T] = {}
        self._filters: List[Callable[[T], bool]] = []
    
    def add(self, entity: T) -> T:
        """
        Add an entity to the repository.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
        """
        entity_id = entity.id
        if entity_id in self._entities:
            raise EntityAlreadyExistsError(entity_id, self._entity_class.__name__)
        
        # Store a deep copy to ensure isolation
        self._entities[entity_id] = copy.deepcopy(entity)
        return entity
    
    def get(self, entity_id: str) -> T:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The ID of the entity to get
            
        Returns:
            The entity
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
        """
        if entity_id not in self._entities:
            raise EntityNotFoundError(entity_id, self._entity_class.__name__)
        
        # Return a deep copy to ensure isolation
        return copy.deepcopy(self._entities[entity_id])
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: The ID of the entity to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        return entity_id in self._entities
    
    def update(self, entity: T) -> T:
        """
        Update an entity.
        
        Args:
            entity: The entity with updated values
            
        Returns:
            The updated entity
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
        """
        entity_id = entity.id
        if entity_id not in self._entities:
            raise EntityNotFoundError(entity_id, self._entity_class.__name__)
        
        # Store a deep copy to ensure isolation
        self._entities[entity_id] = copy.deepcopy(entity)
        return entity
    
    def delete(self, entity_id: str) -> None:
        """
        Delete an entity.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
        """
        if entity_id not in self._entities:
            raise EntityNotFoundError(entity_id, self._entity_class.__name__)
        
        del self._entities[entity_id]
    
    def get_all(self) -> List[T]:
        """
        Get all entities.
        
        Returns:
            List of all entities
        """
        # Apply any registered filters
        entities = list(self._entities.values())
        
        for filter_func in self._filters:
            entities = [entity for entity in entities if filter_func(entity)]
        
        # Return deep copies to ensure isolation
        return [copy.deepcopy(entity) for entity in entities]
    
    def find_by_property(self, property_name: str, property_value: Any) -> List[T]:
        """
        Find entities by a property value.
        
        Args:
            property_name: The name of the property to filter by
            property_value: The value to filter for
            
        Returns:
            List of entities matching the property value
        """
        results = []
        for entity in self._entities.values():
            try:
                if hasattr(entity, property_name) and getattr(entity, property_name) == property_value:
                    results.append(copy.deepcopy(entity))
            except Exception:
                # Ignore any errors (e.g., property doesn't exist)
                pass
        
        return results
    
    def find_by_name(self, name: str) -> Optional[T]:
        """
        Find an entity by name.
        
        Args:
            name: The name to search for
            
        Returns:
            The entity with the given name, or None if not found
        """
        for entity in self._entities.values():
            try:
                if hasattr(entity, 'name') and entity.name == name:
                    return copy.deepcopy(entity)
            except Exception:
                # Ignore any errors
                pass
        
        return None
    
    def count(self) -> int:
        """
        Count the number of entities.
        
        Returns:
            The number of entities
        """
        return len(self._entities)
    
    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Filter entities by a predicate.
        
        Args:
            predicate: The predicate to filter by
            
        Returns:
            List of entities matching the predicate
        """
        return [copy.deepcopy(entity) for entity in self._entities.values() if predicate(entity)]
    
    def register_filter(self, filter_func: Callable[[T], bool]) -> None:
        """
        Register a filter function to be applied on get_all operations.
        
        Args:
            filter_func: Function that takes an entity and returns a boolean
        """
        self._filters.append(filter_func)
        
    def clear_filters(self) -> None:
        """
        Clear all registered filters.
        """
        self._filters.clear()
    
    def clear(self) -> None:
        """
        Clear all entities from the repository.
        """
        self._entities.clear()


class MockRepositoryFactory:
    """Factory for creating mock repositories for different entity types."""
    
    @staticmethod
    def create_task_repository() -> InMemoryRepository:
        """
        Create a mock task repository.
        
        Returns:
            InMemoryRepository for TaskEntity
        """
        from refactor.core.entities.task_entity import TaskEntity
        return InMemoryRepository(TaskEntity)
    
    @staticmethod
    def create_space_repository() -> InMemoryRepository:
        """
        Create a mock space repository.
        
        Returns:
            InMemoryRepository for SpaceEntity
        """
        from refactor.core.entities.space_entity import SpaceEntity
        return InMemoryRepository(SpaceEntity)
    
    @staticmethod
    def create_folder_repository() -> InMemoryRepository:
        """
        Create a mock folder repository.
        
        Returns:
            InMemoryRepository for FolderEntity
        """
        from refactor.core.entities.folder_entity import FolderEntity
        return InMemoryRepository(FolderEntity)
    
    @staticmethod
    def create_list_repository() -> InMemoryRepository:
        """
        Create a mock list repository.
        
        Returns:
            InMemoryRepository for ListEntity
        """
        from refactor.core.entities.list_entity import ListEntity
        return InMemoryRepository(ListEntity)
    
    @staticmethod
    def create_all_repositories() -> Dict[str, InMemoryRepository]:
        """
        Create mock repositories for all entity types.
        
        Returns:
            Dictionary of repository instances keyed by entity type
        """
        return {
            "task": MockRepositoryFactory.create_task_repository(),
            "space": MockRepositoryFactory.create_space_repository(),
            "folder": MockRepositoryFactory.create_folder_repository(),
            "list": MockRepositoryFactory.create_list_repository()
        } 