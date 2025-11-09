#!/usr/bin/env python3
"""
Simple test for error handling in the repository interfaces.

This is a standalone test that can be run without the full application context.
"""
import unittest
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable, List, Dict, Optional
from unittest.mock import MagicMock

# Define a simple entity type
class BaseEntity:
    """Base entity class for testing."""
    
    def __init__(self, entity_id: str, name: str):
        """Initialize a test entity."""
        self._id = entity_id
        self._name = name
    
    @property
    def id(self) -> str:
        """Get entity ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get entity name."""
        return self._name
    
    @name.setter
    def name(self, value: str):
        """Set entity name."""
        self._name = value

# Define repository errors
class RepositoryError(Exception):
    """Base exception class for repository-related errors."""
    pass

class EntityNotFoundError(RepositoryError):
    """Error raised when trying to access a non-existent entity."""
    pass

class EntityAlreadyExistsError(RepositoryError):
    """Error raised when trying to add an entity with a duplicate ID."""
    pass

class ValidationError(RepositoryError):
    """Error raised when entity validation fails."""
    pass

# Entity type for generics
T = TypeVar('T', bound=BaseEntity)

# Define repository interface
class IRepository(Generic[T], ABC):
    """Generic interface for entity repositories."""
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity to the repository."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity in the repository."""
        pass
    
    @abstractmethod
    def get(self, entity_id: str) -> T:
        """Get an entity by its ID."""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> T:
        """Get an entity by its name."""
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if an entity with the given ID exists."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by its ID."""
        pass

# Simple repository implementation for testing
class BaseRepository:
    """Simple in-memory repository implementation for testing error handling."""
    
    def __init__(self):
        self._entities = {}
        self._name_index = {}  # For looking up entities by name
    
    def add(self, entity):
        """Add an entity to the repository."""
        # Validate the entity
        self._validate_entity(entity)
        
        # Check if entity already exists
        if entity.id in self._entities:
            raise EntityAlreadyExistsError(f"Entity with ID '{entity.id}' already exists.")
        
        # Check if name is already used
        if entity.name in self._name_index:
            raise EntityAlreadyExistsError(f"Entity with name '{entity.name}' already exists.")
        
        # Store the entity
        self._entities[entity.id] = entity
        self._name_index[entity.name] = entity.id
        
        return entity
    
    def get(self, entity_id):
        """Get an entity by ID."""
        # Validate ID
        self._validate_id(entity_id)
        
        # Check if entity exists
        if entity_id not in self._entities:
            raise EntityNotFoundError(f"Entity with ID '{entity_id}' not found.")
        
        return self._entities[entity_id]
    
    def get_by_name(self, name):
        """Get an entity by name."""
        # Validate name
        self._validate_name(name)
        
        # Check if entity exists
        if name not in self._name_index:
            raise EntityNotFoundError(f"Entity with name '{name}' not found.")
        
        entity_id = self._name_index[name]
        return self._entities[entity_id]
    
    def update(self, entity):
        """Update an entity in the repository."""
        # Validate the entity
        self._validate_entity(entity)
        
        # Check if entity exists
        if entity.id not in self._entities:
            raise EntityNotFoundError(f"Entity with ID '{entity.id}' not found.")
        
        old_entity = self._entities[entity.id]
        
        # If name has changed, check if new name is already used by a different entity
        if old_entity.name != entity.name and entity.name in self._name_index:
            existing_id = self._name_index[entity.name]
            if existing_id != entity.id:  # Make sure it's not the same entity
                raise ValidationError(f"Entity with name '{entity.name}' already exists.")
        
        # Update name index if name has changed
        if old_entity.name != entity.name:
            del self._name_index[old_entity.name]
            self._name_index[entity.name] = entity.id
        
        # Update entity
        self._entities[entity.id] = entity
        
        return entity
    
    def delete(self, entity_id):
        """Delete an entity from the repository."""
        # If entity doesn't exist, return False
        if entity_id not in self._entities:
            return False
        
        # Get entity
        entity = self._entities[entity_id]
        
        # Remove from name index
        del self._name_index[entity.name]
        
        # Remove from entities
        del self._entities[entity_id]
        
        return True
    
    def exists(self, entity_id):
        """Check if an entity exists by ID."""
        return entity_id in self._entities
    
    def exists_by_name(self, name):
        """Check if an entity exists by name."""
        return name in self._name_index
    
    def _validate_entity(self, entity):
        """Validate an entity."""
        self._validate_id(entity.id)
        self._validate_name(entity.name)
    
    def _validate_id(self, entity_id):
        """Validate an entity ID."""
        if not entity_id:
            raise ValidationError("Entity ID cannot be empty.")
    
    def _validate_name(self, name):
        """Validate an entity name."""
        if not name:
            raise ValidationError("Entity name cannot be empty.")

# Test cases
class ErrorHandlingTests(unittest.TestCase):
    """Test cases for repository error handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.repository = BaseRepository()
        
        # Add a test entity
        self.test_entity = BaseEntity("test_id_1", "Test Entity 1")
        self.repository.add(self.test_entity)
    
    def test_not_found_error(self):
        """Test EntityNotFoundError is raised correctly."""
        # Test get by non-existent ID
        with self.assertRaises(EntityNotFoundError) as context:
            self.repository.get("non_existent_id")
        
        # Verify error message
        self.assertIn("not found", str(context.exception).lower())
        
        # Test get by non-existent name
        with self.assertRaises(EntityNotFoundError) as context:
            self.repository.get_by_name("Non-Existent Entity")
        
        # Verify error message
        self.assertIn("not found", str(context.exception).lower())
    
    def test_already_exists_error(self):
        """Test EntityAlreadyExistsError is raised correctly."""
        # Test add with duplicate ID
        duplicate_id_entity = BaseEntity("test_id_1", "Test Entity 2")
        with self.assertRaises(EntityAlreadyExistsError) as context:
            self.repository.add(duplicate_id_entity)
        
        # Verify error message
        self.assertIn("already exists", str(context.exception).lower())
        
        # Test add with duplicate name
        duplicate_name_entity = BaseEntity("test_id_2", "Test Entity 1")
        with self.assertRaises(EntityAlreadyExistsError) as context:
            self.repository.add(duplicate_name_entity)
        
        # Verify error message
        self.assertIn("already exists", str(context.exception).lower())
    
    def test_validation_error(self):
        """Test ValidationError is raised for invalid updates."""
        # Add a second entity with a unique name
        entity2 = BaseEntity("test_id_2", "Test Entity 2")
        self.repository.add(entity2)
        
        # Add a third entity with a unique name
        entity3 = BaseEntity("test_id_3", "Test Entity 3")
        self.repository.add(entity3)
        
        # Verify all entities exist with correct names
        self.assertEqual(self.repository.get("test_id_1").name, "Test Entity 1")
        self.assertEqual(self.repository.get("test_id_2").name, "Test Entity 2")
        self.assertEqual(self.repository.get("test_id_3").name, "Test Entity 3")
        
        # Now try to update entity3 to have the same name as entity1
        entity3_update = BaseEntity("test_id_3", "Test Entity 1")
        
        # This should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            self.repository.update(entity3_update)
        
        # Verify error message mentions the name collision
        self.assertIn("already exists", str(context.exception).lower())
    
    def test_error_inheritance(self):
        """Test error inheritance hierarchy."""
        # Verify specific errors inherit from RepositoryError
        self.assertTrue(issubclass(EntityNotFoundError, RepositoryError))
        self.assertTrue(issubclass(EntityAlreadyExistsError, RepositoryError))
        self.assertTrue(issubclass(ValidationError, RepositoryError))
        
        # Verify catching base error works for specific errors
        not_found_caught = False
        try:
            raise EntityNotFoundError("Test error")
        except RepositoryError:
            not_found_caught = True
        self.assertTrue(not_found_caught)
        
        already_exists_caught = False
        try:
            raise EntityAlreadyExistsError("Test error")
        except RepositoryError:
            already_exists_caught = True
        self.assertTrue(already_exists_caught)
        
        validation_caught = False
        try:
            raise ValidationError("Test error")
        except RepositoryError:
            validation_caught = True
        self.assertTrue(validation_caught)
    
    def test_error_propagation(self):
        """Test errors propagate correctly through method calls."""
        # Create a mock repository that raises an error
        mock_repo = MagicMock(spec=IRepository)
        mock_repo.get.side_effect = EntityNotFoundError("Entity not found")
        
        # Function that uses the repository
        def get_entity_name(repo, entity_id):
            """Get an entity's name by its ID."""
            entity = repo.get(entity_id)
            return entity.name
        
        # Test error propagation
        with self.assertRaises(EntityNotFoundError) as context:
            get_entity_name(mock_repo, "test_id")
        
        # Verify error message is preserved
        self.assertIn("not found", str(context.exception).lower())

    def test_update_nonexistent_entity(self):
        """Test that updating a non-existent entity raises EntityNotFoundError."""
        # Create an entity that doesn't exist in the repository
        nonexistent_entity = BaseEntity("nonexistent_id", "Nonexistent Entity")
        
        # Attempt to update the non-existent entity
        with self.assertRaises(EntityNotFoundError) as context:
            self.repository.update(nonexistent_entity)
            
        # Verify the error message contains useful information
        self.assertIn("not found", str(context.exception).lower())
        self.assertIn("nonexistent_id", str(context.exception))
    
    def test_delete_nonexistent_entity(self):
        """Test that deleting a non-existent entity returns False."""
        # Attempt to delete a non-existent entity
        result = self.repository.delete("nonexistent_id")
        
        # Verify the result is False (entity not deleted)
        self.assertFalse(result)
    
    def test_null_and_empty_values(self):
        """Test handling of null and empty values."""
        # Test get with empty ID
        with self.assertRaises((EntityNotFoundError, ValidationError)) as context:
            self.repository.get("")
        
        # Test get_by_name with empty name
        with self.assertRaises((EntityNotFoundError, ValidationError)) as context:
            self.repository.get_by_name("")
            
        # Test adding entity with empty ID
        with self.assertRaises(ValidationError) as context:
            empty_id_entity = BaseEntity("", "Empty ID Entity")
            self.repository.add(empty_id_entity)
            
        # Test adding entity with empty name
        with self.assertRaises(ValidationError) as context:
            empty_name_entity = BaseEntity("empty_name_id", "")
            self.repository.add(empty_name_entity)
    
    def test_special_characters(self):
        """Test handling of special characters in IDs and names."""
        # Create an entity with special characters
        special_entity = BaseEntity("special!@#$%^&*()_id", "Special !@#$%^&*() Name")
        
        # Add the entity
        self.repository.add(special_entity)
        
        # Verify we can retrieve it by ID
        retrieved_entity = self.repository.get("special!@#$%^&*()_id")
        self.assertEqual(retrieved_entity.id, "special!@#$%^&*()_id")
        self.assertEqual(retrieved_entity.name, "Special !@#$%^&*() Name")
        
        # Verify we can retrieve it by name
        retrieved_entity = self.repository.get_by_name("Special !@#$%^&*() Name")
        self.assertEqual(retrieved_entity.id, "special!@#$%^&*()_id")
    
    def test_unicode_characters(self):
        """Test handling of Unicode characters in entity IDs and names."""
        # Create an entity with Unicode characters
        unicode_entity = BaseEntity("unicode_☺_id", "Unicode 你好世界 Name")
        
        # Add the entity
        self.repository.add(unicode_entity)
        
        # Verify we can retrieve it by ID
        retrieved_entity = self.repository.get("unicode_☺_id")
        self.assertEqual(retrieved_entity.id, "unicode_☺_id")
        self.assertEqual(retrieved_entity.name, "Unicode 你好世界 Name")
        
        # Verify we can retrieve it by name
        retrieved_entity = self.repository.get_by_name("Unicode 你好世界 Name")
        self.assertEqual(retrieved_entity.id, "unicode_☺_id")
    
    def test_multiple_operations_after_error(self):
        """Test that repository remains usable after an error."""
        # Create an entity with duplicate ID (should fail)
        duplicate_entity = BaseEntity("test_id_1", "Duplicate Entity")
        
        # This operation should fail
        with self.assertRaises(EntityAlreadyExistsError):
            self.repository.add(duplicate_entity)
            
        # Repository should still be usable
        # Try to add a valid entity
        valid_entity = BaseEntity("valid_id", "Valid Entity")
        
        # This should succeed
        self.repository.add(valid_entity)
        
        # Verify entity was added
        self.assertTrue(self.repository.exists("valid_id"))
        
        # Try to get the original entity (should still work)
        entity = self.repository.get("test_id_1")
        self.assertEqual(entity.id, "test_id_1")
    
    def test_add_update_delete_sequence(self):
        """Test a complex sequence of operations to ensure state consistency."""
        # Create entities with unique names
        entity1 = BaseEntity("complex_1", "Complex Entity 1")
        entity2 = BaseEntity("complex_2", "Complex Entity 2")
        entity3 = BaseEntity("complex_3", "Complex Entity 3")
        
        # Add entities to repository
        self.repository.add(entity1)
        self.repository.add(entity2)
        self.repository.add(entity3)
        
        # Verify entities were added with correct names
        self.assertEqual(self.repository.get("complex_1").name, "Complex Entity 1")
        self.assertEqual(self.repository.get("complex_2").name, "Complex Entity 2")
        self.assertEqual(self.repository.get("complex_3").name, "Complex Entity 3")
        
        # Delete entity1
        self.repository.delete("complex_1")
        
        # Try to update entity1 (should fail)
        entity1_update = BaseEntity("complex_1", "Updated Complex Entity 1")
        with self.assertRaises(EntityNotFoundError):
            self.repository.update(entity1_update)
        
        # Add a new entity with the same ID as entity1
        new_entity1 = BaseEntity("complex_1", "New Complex Entity 1")
        self.repository.add(new_entity1)
        
        # Try to update entity2 to have the same name as entity3
        entity2_update = BaseEntity("complex_2", "Complex Entity 3")
        with self.assertRaises(ValidationError):
            self.repository.update(entity2_update)
            
        # Verify entity2 name was not changed
        self.assertEqual(self.repository.get("complex_2").name, "Complex Entity 2")
        
        # Verify final state of all entities
        self.assertEqual(self.repository.get("complex_1").name, "New Complex Entity 1")
        self.assertEqual(self.repository.get("complex_2").name, "Complex Entity 2")
        self.assertEqual(self.repository.get("complex_3").name, "Complex Entity 3")

class SimpleTaskRepository(BaseRepository):
    """Task-specific repository implementation for testing."""
    pass


class TestRepositoryInterface(unittest.TestCase):
    """Test the repository interface."""
    
    def test_error_inheritance(self):
        """Test that repository errors inherit from RepositoryError."""
        self.assertTrue(issubclass(EntityNotFoundError, RepositoryError))
        self.assertTrue(issubclass(EntityAlreadyExistsError, RepositoryError))
        self.assertTrue(issubclass(ValidationError, RepositoryError))

if __name__ == '__main__':
    unittest.main() 