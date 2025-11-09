"""
Repository Interface

This module defines the Repository interface that all repositories must implement.
Repositories provide a standardized way to access and manipulate entities stored
in various backends (e.g., JSON files, databases, memory).
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict, Callable

# Type variable for entity type
T = TypeVar('T')


class Repository(Generic[T], ABC):
    """
    Interface for repositories that manage entity persistence.
    
    Repositories handle CRUD operations for entities and provide methods
    for searching and filtering.
    """
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """
        Add a new entity to the repository.
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity, possibly with updated fields
            
        Raises:
            EntityAlreadyExistsError: If an entity with the same ID already exists
            ValidationError: If the entity is invalid
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """
        Get all entities in the repository.
        
        Returns:
            A list of all entities
        """
        pass
    
    @abstractmethod
    def find_by_property(self, property_name: str, value: Any) -> List[T]:
        """
        Find entities by a property value.
        
        Args:
            property_name: The name of the property to filter by
            value: The value to filter for
            
        Returns:
            A list of entities with the specified property value
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[T]:
        """
        Find an entity by its name.
        
        Args:
            name: The name of the entity to find
            
        Returns:
            The entity with the specified name, or None if not found
        """
        pass
    
    @abstractmethod
    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        """
        Filter entities using a predicate function.
        
        Args:
            predicate: A function that takes an entity and returns True to include it
            
        Returns:
            A list of entities for which the predicate returns True
        """
        pass
    
    @abstractmethod
    def count(self, predicate: Optional[Callable[[T], bool]] = None) -> int:
        """
        Count entities, optionally filtering with a predicate.
        
        Args:
            predicate: Optional function that takes an entity and returns True to include it
            
        Returns:
            The number of entities (that match the predicate, if provided)
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            entity_id: The ID to check
            
        Returns:
            True if an entity with the given ID exists, False otherwise
        """
        pass 