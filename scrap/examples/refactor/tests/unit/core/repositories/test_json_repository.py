"""
Unit tests for the JsonRepository class.

This module contains comprehensive tests for the generic JsonRepository implementation.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from refactor.core.repositories.json_repository import JsonRepository
from refactor.core.exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ValidationError,
    StorageError
)

# Mock entity for testing
class MockEntity:
    """Simple mock entity class for testing."""
    
    def __init__(self, entity_id, name, properties=None):
        """Initialize the mock entity."""
        self.id = entity_id
        self.name = name
        self.properties = properties or {}
    
    def to_dict(self):
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create entity from dictionary."""
        return cls(
            entity_id=data.get("id"),
            name=data.get("name"),
            properties=data.get("properties", {})
        )


# Mock entity serializer for testing
class MockSerializer:
    """Mock serializer for testing."""
    
    def serialize(self, entity):
        """Serialize entity to dictionary."""
        return entity.to_dict()
    
    def deserialize(self, data):
        """Deserialize dictionary to entity."""
        return MockEntity.from_dict(data)


class JsonRepositoryTests(unittest.TestCase):
    """Test cases for the JsonRepository implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary file
        self.test_fd, self.test_path = tempfile.mkstemp(suffix='.json')
        self.test_path = Path(self.test_path)
        
        # Initialize test data
        self.test_data = {
            "entities": [
                {
                    "id": "ent_001",
                    "name": "Test Entity 1",
                    "properties": {"key1": "value1", "key2": 42}
                },
                {
                    "id": "ent_002",
                    "name": "Test Entity 2",
                    "properties": {"key1": "value2", "key3": True}
                }
            ]
        }
        
        # Write test data to file
        with open(self.test_path, 'w') as f:
            json.dump(self.test_data, f, indent=2)
        
        # Create repository
        self.serializer = MockSerializer()
        self.repo = JsonRepository(
            entity_class=MockEntity,
            json_path=self.test_path,
            entity_serializer=self.serializer
        )
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            os.close(self.test_fd)
            os.unlink(self.test_path)
        except:
            pass
    
    def test_initialization(self):
        """Test repository initialization and loading."""
        # Verify entities were loaded
        self.assertEqual(self.repo.count(), 2)
        
        # Check that entities are accessible
        entity1 = self.repo.get("ent_001")
        self.assertEqual(entity1.name, "Test Entity 1")
        self.assertEqual(entity1.properties["key1"], "value1")
        
        entity2 = self.repo.get("ent_002")
        self.assertEqual(entity2.name, "Test Entity 2")
        self.assertEqual(entity2.properties["key1"], "value2")
    
    def test_initialization_with_nonexistent_file(self):
        """Test initialization with a non-existent file."""
        # Use a non-existent path
        non_existent_path = Path("non_existent_file.json")
        
        # Create repository with non-existent file - should not raise error
        repo = JsonRepository(
            entity_class=MockEntity,
            json_path=non_existent_path,
            entity_serializer=self.serializer
        )
        
        # Verify no entities are loaded
        self.assertEqual(repo.count(), 0)
    
    @patch('refactor.core.repositories.json_repository.open', side_effect=PermissionError("Permission denied"))
    def test_initialization_with_permission_error(self, mock_open):
        """Test initialization with permission error."""
        with self.assertRaises(StorageError):
            JsonRepository(
                entity_class=MockEntity,
                json_path=self.test_path,
                entity_serializer=self.serializer
            )
    
    @patch('refactor.core.repositories.json_repository.json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    def test_initialization_with_invalid_json(self, mock_load):
        """Test initialization with invalid JSON."""
        with self.assertRaises(StorageError):
            JsonRepository(
                entity_class=MockEntity,
                json_path=self.test_path,
                entity_serializer=self.serializer
            )
    
    def test_add_entity(self):
        """Test adding a new entity."""
        # Create a new entity
        new_entity = MockEntity("ent_003", "Test Entity 3", {"key1": "value3"})
        
        # Add entity to repository
        added_entity = self.repo.add(new_entity)
        
        # Verify entity was added
        self.assertEqual(self.repo.count(), 3)
        self.assertEqual(added_entity.id, "ent_003")
        
        # Retrieve entity and verify attributes
        retrieved_entity = self.repo.get("ent_003")
        self.assertEqual(retrieved_entity.name, "Test Entity 3")
        self.assertEqual(retrieved_entity.properties["key1"], "value3")
        
        # Verify entity was saved to file
        with open(self.test_path, 'r') as f:
            saved_data = json.load(f)
            
        saved_entities = saved_data.get("entities", [])
        self.assertEqual(len(saved_entities), 3)
        
        saved_entity = next((e for e in saved_entities if e["id"] == "ent_003"), None)
        self.assertIsNotNone(saved_entity)
        self.assertEqual(saved_entity["name"], "Test Entity 3")
    
    def test_add_duplicate_id(self):
        """Test adding entity with duplicate ID."""
        # Create entity with duplicate ID
        duplicate_entity = MockEntity("ent_001", "Duplicate ID Entity")
        
        # Try to add entity - should raise error
        with self.assertRaises(EntityAlreadyExistsError):
            self.repo.add(duplicate_entity)
            
        # Verify no entity was added
        self.assertEqual(self.repo.count(), 2)
    
    def test_add_duplicate_name(self):
        """Test adding entity with duplicate name."""
        # Create entity with duplicate name
        duplicate_name_entity = MockEntity("ent_003", "Test Entity 1")
        
        # Try to add entity - should raise error
        with self.assertRaises(EntityAlreadyExistsError):
            self.repo.add(duplicate_name_entity)
            
        # Verify no entity was added
        self.assertEqual(self.repo.count(), 2)
    
    def test_get_entity(self):
        """Test getting an entity by ID."""
        # Get existing entity
        entity = self.repo.get("ent_001")
        self.assertEqual(entity.id, "ent_001")
        self.assertEqual(entity.name, "Test Entity 1")
        
        # Try to get non-existent entity
        with self.assertRaises(EntityNotFoundError):
            self.repo.get("non_existent")
    
    def test_update_entity(self):
        """Test updating an existing entity."""
        # Get entity to update
        entity = self.repo.get("ent_001")
        
        # Update entity properties
        entity.name = "Updated Entity"
        entity.properties["key1"] = "updated_value"
        
        # Update entity in repository
        updated_entity = self.repo.update(entity)
        
        # Verify entity was updated
        self.assertEqual(updated_entity.name, "Updated Entity")
        self.assertEqual(updated_entity.properties["key1"], "updated_value")
        
        # Retrieve entity and verify attributes
        retrieved_entity = self.repo.get("ent_001")
        self.assertEqual(retrieved_entity.name, "Updated Entity")
        self.assertEqual(retrieved_entity.properties["key1"], "updated_value")
        
        # Verify entity was saved to file
        with open(self.test_path, 'r') as f:
            saved_data = json.load(f)
            
        saved_entities = saved_data.get("entities", [])
        saved_entity = next((e for e in saved_entities if e["id"] == "ent_001"), None)
        self.assertEqual(saved_entity["name"], "Updated Entity")
        self.assertEqual(saved_entity["properties"]["key1"], "updated_value")
    
    def test_update_nonexistent_entity(self):
        """Test updating a non-existent entity."""
        # Create entity with non-existent ID
        non_existent_entity = MockEntity("non_existent", "Non-existent Entity")
        
        # Try to update entity - should raise error
        with self.assertRaises(EntityNotFoundError):
            self.repo.update(non_existent_entity)
    
    def test_delete_entity(self):
        """Test deleting an entity."""
        # Verify entity exists
        self.assertTrue(self.repo.exists("ent_001"))
        
        # Delete entity
        self.repo.delete("ent_001")
        
        # Verify entity was deleted
        self.assertFalse(self.repo.exists("ent_001"))
        self.assertEqual(self.repo.count(), 1)
        
        # Verify entity was removed from file
        with open(self.test_path, 'r') as f:
            saved_data = json.load(f)
            
        saved_entities = saved_data.get("entities", [])
        self.assertEqual(len(saved_entities), 1)
        self.assertEqual(saved_entities[0]["id"], "ent_002")
    
    def test_delete_nonexistent_entity(self):
        """Test deleting a non-existent entity."""
        # Some implementations return False, others raise an error
        # Both are acceptable, so handle both cases
        try:
            result = self.repo.delete("non_existent")
            # If it returns a value, it should be False
            self.assertFalse(result)
        except EntityNotFoundError:
            # If it raises an error, that's also acceptable
            pass
        
        # Either way, the entity count should remain unchanged
        self.assertEqual(self.repo.count(), 2)
    
    def test_exists(self):
        """Test checking if entity exists."""
        # Check existing entity
        self.assertTrue(self.repo.exists("ent_001"))
        
        # Check non-existent entity
        self.assertFalse(self.repo.exists("non_existent"))
    
    def test_get_all(self):
        """Test getting all entities."""
        # Get all entities
        entities = self.repo.get_all()
        
        # Verify all entities were returned
        self.assertEqual(len(entities), 2)
        self.assertEqual({e.id for e in entities}, {"ent_001", "ent_002"})
    
    def test_find_by_name(self):
        """Test finding entity by name."""
        # Find existing entity
        entity = self.repo.find_by_name("Test Entity 1")
        self.assertEqual(entity.id, "ent_001")
        
        # Try to find non-existent entity
        entity = self.repo.find_by_name("Non-existent Entity")
        self.assertIsNone(entity)
    
    def test_find_by_property(self):
        """Test finding entities by property."""
        # We need to access the properties correctly for our mocked entities
        # Find entities with property key1=value1
        entities = self.repo.filter(lambda e: e.properties.get("key1") == "value1")
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].id, "ent_001")
        
        # Find entities with property key3=True
        entities = self.repo.filter(lambda e: e.properties.get("key3") is True)
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].id, "ent_002")
        
        # Find entities with non-existent property
        entities = self.repo.filter(lambda e: e.properties.get("non_existent") is not None)
        self.assertEqual(len(entities), 0)
    
    def test_count(self):
        """Test counting entities."""
        self.assertEqual(self.repo.count(), 2)
        
        # Add entity and verify count increases
        new_entity = MockEntity("ent_003", "Test Entity 3")
        self.repo.add(new_entity)
        self.assertEqual(self.repo.count(), 3)
        
        # Delete entity and verify count decreases
        self.repo.delete("ent_003")
        self.assertEqual(self.repo.count(), 2)
    
    def test_filter(self):
        """Test filtering entities."""
        # Filter entities with key1 property
        entities = self.repo.filter(lambda e: "key1" in e.properties)
        self.assertEqual(len(entities), 2)
        
        # Filter entities with key3 property
        entities = self.repo.filter(lambda e: "key3" in e.properties)
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].id, "ent_002")
        
        # Filter with complex condition
        entities = self.repo.filter(lambda e: "key1" in e.properties and e.properties["key1"] == "value1")
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].id, "ent_001")
    
    @patch('refactor.core.repositories.json_repository.open', side_effect=PermissionError("Permission denied"))
    def test_save_with_permission_error(self, mock_open):
        """Test saving with permission error."""
        # Create entity
        new_entity = MockEntity("ent_003", "Test Entity 3")
        
        # Try to add entity - should raise error
        with self.assertRaises(StorageError):
            self.repo.add(new_entity)


if __name__ == "__main__":
    unittest.main() 